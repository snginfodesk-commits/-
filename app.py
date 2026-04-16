"""
Facebook Ads Optimization Dashboard
====================================
Interactive Streamlit dashboard that connects to the Facebook Marketing API,
displays campaign health checks, and provides optimization recommendations.

Run with: streamlit run app.py
"""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from analysis import apply_health_checks, get_best_audiences, get_pause_recommendations
from demo_data import generate_demo_data, generate_demo_data_aggregated

load_dotenv()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Facebook Ads Optimization Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Facebook Ads Optimization Dashboard")

# ---------------------------------------------------------------------------
# Sidebar – credentials & controls
# ---------------------------------------------------------------------------
st.sidebar.header("Configuration")

use_demo = st.sidebar.checkbox("Use demo data (no API needed)", value=True)

access_token = st.sidebar.text_input(
    "FB Access Token",
    value=os.getenv("FB_ACCESS_TOKEN", ""),
    type="password",
    disabled=use_demo,
)
ad_account_id = st.sidebar.text_input(
    "Ad Account ID",
    value=os.getenv("FB_AD_ACCOUNT_ID", ""),
    placeholder="act_XXXXXXXXXX",
    disabled=use_demo,
)
app_secret = st.sidebar.text_input(
    "App Secret",
    value=os.getenv("FB_APP_SECRET", ""),
    type="password",
    disabled=use_demo,
)

st.sidebar.divider()

date_range = st.sidebar.selectbox("Date Range", [7, 14, 30], index=0, format_func=lambda d: f"Last {d} days")
level = st.sidebar.radio("Breakdown Level", ["campaign", "adset"], format_func=lambda l: l.replace("adset", "Ad Set").title())
target_cpl = st.sidebar.number_input("Target CPL ($)", min_value=1.0, value=float(os.getenv("TARGET_CPL", "50.0")), step=5.0)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300, show_spinner="Fetching data...")
def load_data(token, account_id, secret, days, lvl, demo):
    if demo:
        daily = generate_demo_data(days, lvl)
        aggregated = generate_demo_data_aggregated(days, lvl)
        return daily, aggregated

    from fb_api import fetch_insights, fetch_insights_aggregated, initialize_api

    initialize_api(token, secret)
    daily = fetch_insights(account_id, days, lvl)
    aggregated = fetch_insights_aggregated(account_id, days, lvl)
    return daily, aggregated


# Validate credentials when not using demo data
if not use_demo and not all([access_token, ad_account_id, app_secret]):
    st.warning("Please fill in all Facebook API credentials in the sidebar, or enable demo mode.")
    st.stop()

daily_df, agg_df = load_data(access_token, ad_account_id, app_secret, date_range, level, use_demo)

if daily_df.empty:
    st.info("No data returned for the selected date range and breakdown level.")
    st.stop()

if use_demo:
    st.info("Showing **demo data**. Uncheck 'Use demo data' and enter your API credentials to see real results.")

# ---------------------------------------------------------------------------
# KPI summary row
# ---------------------------------------------------------------------------
st.header("Key Metrics Overview")
col1, col2, col3, col4, col5 = st.columns(5)

total_spend = agg_df["spend"].sum()
total_impressions = agg_df["impressions"].sum()
total_clicks = agg_df["link_clicks"].sum()
total_leads = agg_df["leads"].sum()
avg_cpl = total_spend / total_leads if total_leads > 0 else 0

col1.metric("Total Spend", f"${total_spend:,.2f}")
col2.metric("Impressions", f"{total_impressions:,.0f}")
col3.metric("Link Clicks", f"{total_clicks:,.0f}")
col4.metric("Total Leads", f"{total_leads:,.0f}")
col5.metric("Avg CPL", f"${avg_cpl:,.2f}")

# ---------------------------------------------------------------------------
# Part 2 – Smart Analysis / Health Check Table
# ---------------------------------------------------------------------------
st.header("Smart Analysis Table")

health_df = apply_health_checks(agg_df, target_cpl)

# Color-code health status
def style_health(val):
    if "Fatigue" in val:
        return "background-color: #ffcccc"
    if "Page Load" in val or "Bounce" in val:
        return "background-color: #fff3cd"
    if "Mismatch" in val:
        return "background-color: #ffd6cc"
    if "Scale" in val:
        return "background-color: #ccffcc"
    return ""


display_cols = ["campaign_name"]
if level == "adset":
    display_cols.append("adset_name")
display_cols += [
    "spend", "impressions", "link_ctr", "cpm", "frequency",
    "link_clicks", "landing_page_views", "leads", "cpl",
    "conversion_rate", "lp_view_rate", "health_status",
]

styled = (
    health_df[display_cols]
    .style
    .format(
        {
            "spend": "${:,.2f}",
            "impressions": "{:,.0f}",
            "link_ctr": "{:.2f}%",
            "cpm": "${:.2f}",
            "frequency": "{:.2f}",
            "link_clicks": "{:,.0f}",
            "landing_page_views": "{:,.0f}",
            "leads": "{:,.0f}",
            "cpl": "${:.2f}",
            "conversion_rate": "{:.2f}%",
            "lp_view_rate": "{:.1f}%",
        }
    )
    .map(style_health, subset=["health_status"])
)

st.dataframe(styled, use_container_width=True, hide_index=True)

# Legend
with st.expander("Health Status Legend"):
    st.markdown(
        """
| Status | Condition | Meaning |
|--------|-----------|---------|
| **High Fatigue - Refresh Creative** | Frequency > 2.5 & CTR below average | Audience seeing ads too often, performance dropping |
| **Page Load Issue/High Bounce** | LP View Rate < 60% | Users clicking but not reaching the landing page |
| **Landing Page/Offer Mismatch** | CTR > 1.2% but Conv. Rate < 5% | Ad messaging doesn't match landing page experience |
| **Ready to Scale** | CPL 20%+ below target & Frequency < 1.5 | Strong performer with room to increase budget |
| **Healthy** | None of the above | Performing within normal parameters |
"""
    )

# ---------------------------------------------------------------------------
# Part 3 – Optimization Recommendations
# ---------------------------------------------------------------------------
st.header("Manager Insights & Recommendations")

rec_col1, rec_col2 = st.columns(2)

# 3a – Pause recommendations
with rec_col1:
    st.subheader("Pause Immediately")
    st.caption("Top 3 worst performers by CPL vs. average")
    pause_df = get_pause_recommendations(agg_df, top_n=3)
    if pause_df.empty:
        st.info("Not enough lead data to make pause recommendations.")
    else:
        st.dataframe(
            pause_df.style.format(
                {
                    "spend": "${:,.2f}",
                    "cpl": "${:.2f}",
                    "cpl_vs_avg": "{:+.1f}%",
                    "leads": "{:,.0f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

# 3b – Best audiences
with rec_col2:
    st.subheader("Best Performing Audiences")
    st.caption("Ranked by lowest CPL")
    best_df = get_best_audiences(agg_df, top_n=5)
    if best_df.empty:
        st.info("Not enough lead data to rank audiences.")
    else:
        st.dataframe(
            best_df.style.format(
                {
                    "spend": "${:,.2f}",
                    "cpl": "${:.2f}",
                    "leads": "{:,.0f}",
                    "conversion_rate": "{:.2f}%",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

# 3c – CPL vs Spend trend line
st.subheader("CPL vs. Spend Over Time")

# Aggregate daily data per date for trend chart
trend_df = daily_df.groupby("date", as_index=False).agg(
    spend=("spend", "sum"),
    leads=("leads", "sum"),
)
trend_df["cpl"] = trend_df.apply(lambda r: r["spend"] / r["leads"] if r["leads"] > 0 else None, axis=1)
trend_df = trend_df.dropna(subset=["cpl"]).sort_values("date")

if trend_df.empty:
    st.info("Not enough daily lead data to plot trends.")
else:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=trend_df["date"],
            y=trend_df["spend"],
            name="Daily Spend ($)",
            marker_color="#636EFA",
            opacity=0.6,
            yaxis="y",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=trend_df["date"],
            y=trend_df["cpl"],
            name="CPL ($)",
            mode="lines+markers",
            line=dict(color="#EF553B", width=3),
            yaxis="y2",
        )
    )
    # Target CPL reference line
    fig.add_hline(
        y=target_cpl,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Target CPL ${target_cpl:.0f}",
        yref="y2",
    )
    fig.update_layout(
        yaxis=dict(title="Daily Spend ($)", side="left"),
        yaxis2=dict(title="CPL ($)", side="right", overlaying="y"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
        margin=dict(t=40),
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Additional Charts
# ---------------------------------------------------------------------------
st.header("Performance Breakdown")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Spend by Campaign")
    spend_by_campaign = agg_df.groupby("campaign_name", as_index=False)["spend"].sum().sort_values("spend", ascending=True)
    fig_spend = px.bar(
        spend_by_campaign,
        x="spend",
        y="campaign_name",
        orientation="h",
        labels={"spend": "Spend ($)", "campaign_name": ""},
    )
    fig_spend.update_layout(height=350, margin=dict(t=10))
    st.plotly_chart(fig_spend, use_container_width=True)

with chart_col2:
    st.subheader("CTR vs Frequency")
    fig_scatter = px.scatter(
        agg_df,
        x="frequency",
        y="link_ctr",
        size="spend",
        color="campaign_name",
        labels={"frequency": "Frequency", "link_ctr": "Link CTR (%)", "campaign_name": "Campaign"},
        hover_data=["adset_name", "cpl"],
    )
    fig_scatter.update_layout(height=350, margin=dict(t=10))
    st.plotly_chart(fig_scatter, use_container_width=True)

# ---------------------------------------------------------------------------
# Export to CSV
# ---------------------------------------------------------------------------
st.divider()

csv_col1, csv_col2 = st.columns(2)

with csv_col1:
    csv_health = health_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Export Health Check Table to CSV",
        data=csv_health,
        file_name="fb_ads_health_check.csv",
        mime="text/csv",
    )

with csv_col2:
    csv_daily = daily_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Export Daily Data to CSV",
        data=csv_daily,
        file_name="fb_ads_daily_data.csv",
        mime="text/csv",
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Built with Streamlit, Plotly, and the Facebook Marketing API. "
    "Data refreshes every 5 minutes when using live API."
)
