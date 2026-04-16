"""
Analysis engine for Facebook Ads health checks and optimization recommendations.
"""

import pandas as pd


def apply_health_checks(df: pd.DataFrame, target_cpl: float) -> pd.DataFrame:
    """
    Apply health-check flags to each row.

    Flags:
    - Creative Fatigue: Frequency > 2.5 and CTR < period average
    - Funnel Leak: Landing Page View rate < 60% of link clicks
    - Conversion Issue: CTR > 1.2% but Conversion Rate < 5%
    - Scaling Opportunity: CPL 20%+ below target and Frequency < 1.5

    Returns a copy of the DataFrame with a 'health_status' column.
    """
    df = df.copy()
    avg_ctr = df["link_ctr"].mean() if len(df) > 0 else 0

    statuses = []
    for _, row in df.iterrows():
        flags = []

        # Creative Fatigue
        if row["frequency"] > 2.5 and row["link_ctr"] < avg_ctr:
            flags.append("High Fatigue - Refresh Creative")

        # Funnel Leak
        if row["lp_view_rate"] < 60 and row["link_clicks"] > 0:
            flags.append("Page Load Issue/High Bounce")

        # Conversion Issue
        if row["link_ctr"] > 1.2 and row["conversion_rate"] < 5:
            flags.append("Landing Page/Offer Mismatch")

        # Scaling Opportunity
        cpl_threshold = target_cpl * 0.80
        if row["cpl"] > 0 and row["cpl"] < cpl_threshold and row["frequency"] < 1.5:
            flags.append("Ready to Scale")

        statuses.append(" | ".join(flags) if flags else "Healthy")

    df["health_status"] = statuses
    return df


def get_pause_recommendations(df: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    """
    Identify the top N ads/campaigns that should be paused immediately
    based on CPL being highest relative to the average.

    Only considers rows that actually have leads (CPL > 0).
    """
    with_leads = df[df["cpl"] > 0].copy()
    if with_leads.empty:
        return pd.DataFrame()

    avg_cpl = with_leads["cpl"].mean()
    with_leads["cpl_vs_avg"] = ((with_leads["cpl"] - avg_cpl) / avg_cpl * 100).round(1)
    worst = with_leads.nlargest(top_n, "cpl")
    return worst[["campaign_name", "adset_name", "spend", "cpl", "cpl_vs_avg", "leads"]]


def get_best_audiences(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """
    Rank audiences (ad sets) by CPL efficiency.
    Lower CPL = better performing audience.
    """
    with_leads = df[df["cpl"] > 0].copy()
    if with_leads.empty:
        return pd.DataFrame()

    best = with_leads.nsmallest(top_n, "cpl")
    return best[
        ["campaign_name", "adset_name", "spend", "leads", "cpl", "conversion_rate"]
    ]
