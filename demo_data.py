"""
Generate realistic demo data for the dashboard when no Facebook API credentials
are configured. This allows users to explore the dashboard UI before connecting
their ad account.
"""

import random
from datetime import datetime, timedelta

import pandas as pd

CAMPAIGNS = [
    "Brand Awareness - US",
    "Lead Gen - Webinar Q1",
    "Retargeting - Cart Abandoners",
    "Lookalike - Top Customers",
    "Broad - Interest Tech",
    "Lead Gen - Ebook Download",
]

ADSETS = {
    "Brand Awareness - US": ["18-34 Males", "35-54 Females", "Broad US"],
    "Lead Gen - Webinar Q1": ["Lookalike 1%", "Lookalike 3%", "Interest - Marketing"],
    "Retargeting - Cart Abandoners": ["7-day visitors", "30-day visitors", "Email list"],
    "Lookalike - Top Customers": ["LAL 1% - US", "LAL 2% - US", "LAL 1% - CA"],
    "Broad - Interest Tech": ["Tech Enthusiasts", "SaaS Buyers", "Startup Founders"],
    "Lead Gen - Ebook Download": ["Content Marketers", "CMOs", "Digital Agencies"],
}

# Profiles per campaign to create realistic variation
CAMPAIGN_PROFILES = {
    "Brand Awareness - US": {"cpm_range": (8, 15), "ctr_range": (0.4, 1.0), "lead_rate": 0.01},
    "Lead Gen - Webinar Q1": {"cpm_range": (12, 22), "ctr_range": (1.0, 2.5), "lead_rate": 0.08},
    "Retargeting - Cart Abandoners": {"cpm_range": (18, 35), "ctr_range": (1.5, 3.5), "lead_rate": 0.12},
    "Lookalike - Top Customers": {"cpm_range": (10, 18), "ctr_range": (0.8, 2.0), "lead_rate": 0.06},
    "Broad - Interest Tech": {"cpm_range": (6, 12), "ctr_range": (0.3, 0.9), "lead_rate": 0.02},
    "Lead Gen - Ebook Download": {"cpm_range": (10, 20), "ctr_range": (1.2, 2.8), "lead_rate": 0.10},
}


def generate_demo_data(days: int, level: str = "campaign") -> pd.DataFrame:
    """Generate realistic demo campaign data."""
    random.seed(42 + days)
    rows = []
    end_date = datetime.now()

    for campaign in CAMPAIGNS:
        profile = CAMPAIGN_PROFILES[campaign]
        adsets = ADSETS[campaign] if level == "adset" else ["All Ad Sets"]

        for adset in adsets:
            for day_offset in range(days):
                date = (end_date - timedelta(days=day_offset)).strftime("%Y-%m-%d")

                # Add day-over-day variation and trends
                trend_factor = 1 + (day_offset / days) * random.uniform(-0.15, 0.15)
                daily_noise = random.uniform(0.8, 1.2)

                spend = random.uniform(20, 150) * daily_noise
                cpm = random.uniform(*profile["cpm_range"]) * trend_factor
                impressions = int(spend / cpm * 1000)
                ctr = random.uniform(*profile["ctr_range"]) * daily_noise
                link_clicks = max(1, int(impressions * ctr / 100))
                frequency = random.uniform(0.8, 3.5) * trend_factor

                # Funnel metrics
                lp_view_pct = random.uniform(0.40, 0.95)
                landing_page_views = max(0, int(link_clicks * lp_view_pct))
                lead_rate = profile["lead_rate"] * daily_noise
                leads = max(0, int(landing_page_views * lead_rate))
                cpl = spend / leads if leads > 0 else 0
                conversion_rate = (leads / landing_page_views * 100) if landing_page_views > 0 else 0
                lp_view_rate = (landing_page_views / link_clicks * 100) if link_clicks > 0 else 0

                rows.append(
                    {
                        "date": date,
                        "campaign_name": campaign,
                        "adset_name": adset if level == "adset" else "N/A",
                        "spend": round(spend, 2),
                        "impressions": impressions,
                        "cpm": round(cpm, 2),
                        "frequency": round(frequency, 2),
                        "link_clicks": link_clicks,
                        "link_ctr": round(ctr, 2),
                        "landing_page_views": landing_page_views,
                        "leads": leads,
                        "cpl": round(cpl, 2),
                        "conversion_rate": round(conversion_rate, 2),
                        "lp_view_rate": round(lp_view_rate, 2),
                    }
                )

    return pd.DataFrame(rows)


def generate_demo_data_aggregated(days: int, level: str = "campaign") -> pd.DataFrame:
    """Generate aggregated (non-daily) demo data for the health-check table."""
    daily = generate_demo_data(days, level)

    group_cols = ["campaign_name"]
    if level == "adset":
        group_cols.append("adset_name")

    agg = daily.groupby(group_cols, as_index=False).agg(
        spend=("spend", "sum"),
        impressions=("impressions", "sum"),
        link_clicks=("link_clicks", "sum"),
        landing_page_views=("landing_page_views", "sum"),
        leads=("leads", "sum"),
    )

    # Recalculate derived metrics from aggregated totals
    agg["cpm"] = (agg["spend"] / agg["impressions"] * 1000).round(2).where(agg["impressions"] > 0, 0)
    agg["frequency"] = (agg["impressions"] / (agg["impressions"] / daily.groupby(group_cols)["frequency"].mean().values).clip(1)).round(2)
    # Simpler frequency: use mean of daily values
    freq_means = daily.groupby(group_cols, as_index=False)["frequency"].mean()
    agg = agg.drop(columns=["frequency"]).merge(freq_means, on=group_cols)

    agg["link_ctr"] = (agg["link_clicks"] / agg["impressions"] * 100).round(2).where(agg["impressions"] > 0, 0)
    agg["cpl"] = agg.apply(lambda r: round(r["spend"] / r["leads"], 2) if r["leads"] > 0 else 0, axis=1)
    agg["conversion_rate"] = agg.apply(
        lambda r: round(r["leads"] / r["landing_page_views"] * 100, 2) if r["landing_page_views"] > 0 else 0, axis=1
    )
    agg["lp_view_rate"] = agg.apply(
        lambda r: round(r["landing_page_views"] / r["link_clicks"] * 100, 2) if r["link_clicks"] > 0 else 0, axis=1
    )

    agg["spend"] = agg["spend"].round(2)

    if level != "adset":
        agg["adset_name"] = "N/A"

    return agg
