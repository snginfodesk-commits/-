"""
Generate a standalone HTML report with all dashboard tables and charts.
No server needed — just open the output file in a browser.

Usage:
    python generate_report.py
    # Opens fb_ads_report.html in your default browser
"""

import webbrowser
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.io import to_html

from analysis import apply_health_checks, get_best_audiences, get_pause_recommendations
from demo_data import generate_demo_data, generate_demo_data_aggregated

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DAYS = 7
LEVEL = "adset"
TARGET_CPL = 50.0
OUTPUT_FILE = "fb_ads_report.html"

# ---------------------------------------------------------------------------
# Generate data
# ---------------------------------------------------------------------------
daily_df = generate_demo_data(DAYS, LEVEL)
agg_df = generate_demo_data_aggregated(DAYS, LEVEL)
health_df = apply_health_checks(agg_df, TARGET_CPL)
pause_df = get_pause_recommendations(agg_df, top_n=3)
best_df = get_best_audiences(agg_df, top_n=5)

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
total_spend = agg_df["spend"].sum()
total_impressions = agg_df["impressions"].sum()
total_clicks = agg_df["link_clicks"].sum()
total_leads = agg_df["leads"].sum()
avg_cpl = total_spend / total_leads if total_leads > 0 else 0

# ---------------------------------------------------------------------------
# Health check table — color coded
# ---------------------------------------------------------------------------

def health_color(val):
    if "Fatigue" in val:
        return "#ffcccc"
    if "Page Load" in val or "Bounce" in val:
        return "#fff3cd"
    if "Mismatch" in val:
        return "#ffd6cc"
    if "Scale" in val:
        return "#ccffcc"
    return "#ffffff"


health_display_cols = [
    "campaign_name", "adset_name", "spend", "impressions", "link_ctr",
    "cpm", "frequency", "link_clicks", "landing_page_views", "leads",
    "cpl", "conversion_rate", "lp_view_rate", "health_status",
]
health_table = health_df[health_display_cols].copy()
health_table.columns = [
    "Campaign", "Ad Set", "Spend", "Impressions", "CTR %",
    "CPM", "Frequency", "Link Clicks", "LP Views", "Leads",
    "CPL", "Conv Rate %", "LP View Rate %", "Health Status",
]

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

# 1) CPL vs Spend trend
trend_df = daily_df.groupby("date", as_index=False).agg(
    spend=("spend", "sum"),
    leads=("leads", "sum"),
)
trend_df["cpl"] = trend_df.apply(lambda r: r["spend"] / r["leads"] if r["leads"] > 0 else None, axis=1)
trend_df = trend_df.dropna(subset=["cpl"]).sort_values("date")

fig_trend = go.Figure()
fig_trend.add_trace(go.Bar(
    x=trend_df["date"], y=trend_df["spend"],
    name="Daily Spend ($)", marker_color="#636EFA", opacity=0.6, yaxis="y",
))
fig_trend.add_trace(go.Scatter(
    x=trend_df["date"], y=trend_df["cpl"],
    name="CPL ($)", mode="lines+markers",
    line=dict(color="#EF553B", width=3), yaxis="y2",
))
fig_trend.add_hline(y=TARGET_CPL, line_dash="dash", line_color="green",
                    annotation_text=f"Target CPL ${TARGET_CPL:.0f}", yref="y2")
fig_trend.update_layout(
    yaxis=dict(title="Daily Spend ($)", side="left"),
    yaxis2=dict(title="CPL ($)", side="right", overlaying="y"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=400, margin=dict(t=40),
)
trend_html = to_html(fig_trend, full_html=False, include_plotlyjs=False)

# 2) Spend by campaign
spend_by = agg_df.groupby("campaign_name", as_index=False)["spend"].sum().sort_values("spend", ascending=True)
fig_spend = px.bar(spend_by, x="spend", y="campaign_name", orientation="h",
                   labels={"spend": "Spend ($)", "campaign_name": ""})
fig_spend.update_layout(height=350, margin=dict(t=10))
spend_html = to_html(fig_spend, full_html=False, include_plotlyjs=False)

# 3) CTR vs Frequency
fig_scatter = px.scatter(agg_df, x="frequency", y="link_ctr", size="spend",
                         color="campaign_name",
                         labels={"frequency": "Frequency", "link_ctr": "CTR %", "campaign_name": "Campaign"},
                         hover_data=["adset_name", "cpl"])
fig_scatter.update_layout(height=350, margin=dict(t=10))
scatter_html = to_html(fig_scatter, full_html=False, include_plotlyjs=False)


# ---------------------------------------------------------------------------
# Build HTML
# ---------------------------------------------------------------------------

def df_to_html_table(df, fmt=None):
    """Convert a DataFrame to a styled HTML table string."""
    fmt = fmt or {}
    rows_html = []
    # Header
    header = "".join(f"<th>{c}</th>" for c in df.columns)
    rows_html.append(f"<tr>{header}</tr>")
    # Body
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            val = row[col]
            if col in fmt:
                display = fmt[col](val)
            else:
                display = str(val)
            style = ""
            if col == "Health Status":
                style = f' style="background-color:{health_color(str(val))};font-weight:600"'
            cells.append(f"<td{style}>{display}</td>")
        rows_html.append(f"<tr>{''.join(cells)}</tr>")
    return "\n".join(rows_html)


health_fmt = {
    "Spend": lambda v: f"${v:,.2f}",
    "Impressions": lambda v: f"{v:,.0f}",
    "CTR %": lambda v: f"{v:.2f}%",
    "CPM": lambda v: f"${v:.2f}",
    "Frequency": lambda v: f"{v:.2f}",
    "Link Clicks": lambda v: f"{v:,.0f}",
    "LP Views": lambda v: f"{v:,.0f}",
    "Leads": lambda v: f"{v:,.0f}",
    "CPL": lambda v: f"${v:.2f}",
    "Conv Rate %": lambda v: f"{v:.2f}%",
    "LP View Rate %": lambda v: f"{v:.1f}%",
}
health_rows = df_to_html_table(health_table, health_fmt)

# Pause table
pause_display = pause_df.copy()
if not pause_display.empty:
    pause_display.columns = ["Campaign", "Ad Set", "Spend", "CPL", "CPL vs Avg %", "Leads"]
    pause_fmt = {
        "Spend": lambda v: f"${v:,.2f}",
        "CPL": lambda v: f"${v:.2f}",
        "CPL vs Avg %": lambda v: f"{v:+.1f}%",
        "Leads": lambda v: f"{v:,.0f}",
    }
    pause_rows = df_to_html_table(pause_display, pause_fmt)
else:
    pause_rows = "<tr><td colspan='6'>Not enough data</td></tr>"

# Best audiences table
best_display = best_df.copy()
if not best_display.empty:
    best_display.columns = ["Campaign", "Ad Set", "Spend", "Leads", "CPL", "Conv Rate %"]
    best_fmt = {
        "Spend": lambda v: f"${v:,.2f}",
        "Leads": lambda v: f"{v:,.0f}",
        "CPL": lambda v: f"${v:.2f}",
        "Conv Rate %": lambda v: f"{v:.2f}%",
    }
    best_rows = df_to_html_table(best_display, best_fmt)
else:
    best_rows = "<tr><td colspan='6'>Not enough data</td></tr>"


html = f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Facebook Ads Optimization Report</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
  :root {{
    --bg: #0f1117;
    --card: #1a1c23;
    --border: #2d2f36;
    --text: #e6e6e6;
    --muted: #9ca3af;
    --accent: #636EFA;
    --red: #EF553B;
    --green: #00CC96;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 24px;
    line-height: 1.5;
  }}
  h1 {{ font-size: 28px; margin-bottom: 8px; }}
  h2 {{ font-size: 20px; margin: 32px 0 16px; color: var(--accent); }}
  h3 {{ font-size: 16px; margin: 0 0 8px; }}
  .subtitle {{ color: var(--muted); margin-bottom: 24px; }}
  .kpi-row {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
  }}
  .kpi {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    text-align: center;
  }}
  .kpi .label {{ color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .kpi .value {{ font-size: 26px; font-weight: 700; margin-top: 4px; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  @media (max-width: 900px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--card);
    border-radius: 8px;
    overflow: hidden;
    font-size: 13px;
    margin-bottom: 16px;
  }}
  th {{
    background: #22242b;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    white-space: nowrap;
    border-bottom: 2px solid var(--border);
  }}
  td {{
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }}
  tr:hover td {{ background: rgba(99,110,250,0.07); }}
  .table-wrap {{ overflow-x: auto; border-radius: 8px; }}
  .chart-box {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 24px;
  }}
  .legend-box {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    margin-top: 12px;
    font-size: 13px;
  }}
  .legend-box span {{
    display: inline-block;
    width: 14px;
    height: 14px;
    border-radius: 3px;
    margin-right: 6px;
    vertical-align: middle;
  }}
  .legend-item {{ margin: 4px 16px 4px 0; display: inline-block; }}
</style>
</head>
<body>

<h1>Facebook Ads Optimization Report</h1>
<p class="subtitle">Last {DAYS} days &middot; Breakdown: {LEVEL.title()} &middot; Target CPL: ${TARGET_CPL:.0f} &middot; Demo Data</p>

<!-- KPIs -->
<div class="kpi-row">
  <div class="kpi"><div class="label">Total Spend</div><div class="value">${total_spend:,.2f}</div></div>
  <div class="kpi"><div class="label">Impressions</div><div class="value">{total_impressions:,.0f}</div></div>
  <div class="kpi"><div class="label">Link Clicks</div><div class="value">{total_clicks:,.0f}</div></div>
  <div class="kpi"><div class="label">Total Leads</div><div class="value">{total_leads:,.0f}</div></div>
  <div class="kpi"><div class="label">Avg CPL</div><div class="value">${avg_cpl:,.2f}</div></div>
</div>

<!-- Health Check Table -->
<h2>Smart Analysis Table</h2>
<div class="table-wrap">
<table>{health_rows}</table>
</div>
<div class="legend-box">
  <strong>Health Status Legend:</strong><br>
  <span class="legend-item"><span style="background:#ffcccc"></span>High Fatigue - Refresh Creative</span>
  <span class="legend-item"><span style="background:#fff3cd"></span>Page Load Issue / High Bounce</span>
  <span class="legend-item"><span style="background:#ffd6cc"></span>Landing Page / Offer Mismatch</span>
  <span class="legend-item"><span style="background:#ccffcc"></span>Ready to Scale</span>
</div>

<!-- Recommendations -->
<h2>Manager Insights</h2>
<div class="two-col">
  <div>
    <h3>Pause Immediately (Top 3 worst CPL vs average)</h3>
    <div class="table-wrap"><table>{pause_rows}</table></div>
  </div>
  <div>
    <h3>Best Performing Audiences (by CPL)</h3>
    <div class="table-wrap"><table>{best_rows}</table></div>
  </div>
</div>

<!-- CPL vs Spend Trend -->
<h2>CPL vs. Spend Over Time</h2>
<div class="chart-box">{trend_html}</div>

<!-- Additional Charts -->
<h2>Performance Breakdown</h2>
<div class="two-col">
  <div class="chart-box">
    <h3>Spend by Campaign</h3>
    {spend_html}
  </div>
  <div class="chart-box">
    <h3>CTR vs Frequency</h3>
    {scatter_html}
  </div>
</div>

</body>
</html>"""

output_path = Path(OUTPUT_FILE)
output_path.write_text(html, encoding="utf-8")
print(f"Report saved to: {output_path.resolve()}")

# Try to open in browser
try:
    webbrowser.open(str(output_path.resolve()))
except Exception:
    pass
