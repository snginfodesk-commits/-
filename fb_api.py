"""
Facebook Marketing API data fetching module.

Handles authentication and data retrieval from the Facebook Ads API.
Uses the facebook-business SDK to fetch campaign and ad set level metrics.
"""

import os
from datetime import datetime, timedelta

import pandas as pd
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.api import FacebookAdsApi


def initialize_api(access_token: str, app_secret: str, app_id: str = "0"):
    """Initialize the Facebook Marketing API connection."""
    FacebookAdsApi.init(app_id, app_secret, access_token)


def _date_range(days: int) -> dict:
    """Return a time_range dict for the Facebook API."""
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return {"since": start, "until": end}


FIELDS = [
    AdsInsights.Field.campaign_name,
    AdsInsights.Field.adset_name,
    AdsInsights.Field.spend,
    AdsInsights.Field.impressions,
    AdsInsights.Field.cpm,
    AdsInsights.Field.frequency,
    AdsInsights.Field.inline_link_clicks,
    AdsInsights.Field.inline_link_click_ctr,
    AdsInsights.Field.actions,
    AdsInsights.Field.cost_per_action_type,
    AdsInsights.Field.date_start,
    AdsInsights.Field.date_stop,
]


def _extract_action_value(actions: list | None, action_type: str) -> float:
    """Extract a specific action value from the actions list."""
    if not actions:
        return 0.0
    for action in actions:
        if action.get("action_type") == action_type:
            return float(action.get("value", 0))
    return 0.0


def _extract_cost_per_action(cost_per_actions: list | None, action_type: str) -> float:
    """Extract cost per action for a specific action type."""
    if not cost_per_actions:
        return 0.0
    for entry in cost_per_actions:
        if entry.get("action_type") == action_type:
            return float(entry.get("value", 0))
    return 0.0


def fetch_insights(
    ad_account_id: str, days: int, level: str = "campaign"
) -> pd.DataFrame:
    """
    Fetch insights from the Facebook Marketing API.

    Args:
        ad_account_id: The ad account ID (format: act_XXXXXXXXXX).
        days: Number of days to look back (7, 14, or 30).
        level: Breakdown level - 'campaign' or 'adset'.

    Returns:
        DataFrame with processed metrics.
    """
    account = AdAccount(ad_account_id)
    params = {
        "time_range": _date_range(days),
        "level": level,
        "filtering": [],
        "time_increment": 1,  # daily breakdown for trend analysis
    }

    insights = account.get_insights(fields=FIELDS, params=params)

    rows = []
    for row in insights:
        actions = row.get("actions", [])
        cost_per_actions = row.get("cost_per_action_type", [])

        landing_page_views = _extract_action_value(actions, "landing_page_view")
        leads = _extract_action_value(actions, "lead")
        link_clicks = float(row.get("inline_link_clicks", 0))
        spend = float(row.get("spend", 0))

        cpl = _extract_cost_per_action(cost_per_actions, "lead")
        if cpl == 0 and leads > 0:
            cpl = spend / leads

        conversion_rate = (leads / landing_page_views * 100) if landing_page_views > 0 else 0.0
        lp_view_rate = (landing_page_views / link_clicks * 100) if link_clicks > 0 else 0.0

        rows.append(
            {
                "date": row.get("date_start", ""),
                "campaign_name": row.get("campaign_name", "N/A"),
                "adset_name": row.get("adset_name", "N/A"),
                "spend": spend,
                "impressions": int(row.get("impressions", 0)),
                "cpm": float(row.get("cpm", 0)),
                "frequency": float(row.get("frequency", 0)),
                "link_clicks": link_clicks,
                "link_ctr": float(row.get("inline_link_click_ctr", 0)),
                "landing_page_views": landing_page_views,
                "leads": leads,
                "cpl": cpl,
                "conversion_rate": conversion_rate,
                "lp_view_rate": lp_view_rate,
            }
        )

    return pd.DataFrame(rows)


def fetch_insights_aggregated(
    ad_account_id: str, days: int, level: str = "campaign"
) -> pd.DataFrame:
    """
    Fetch insights aggregated over the full period (no daily breakdown).
    Used for the summary health-check table.
    """
    account = AdAccount(ad_account_id)
    params = {
        "time_range": _date_range(days),
        "level": level,
        "filtering": [],
    }

    insights = account.get_insights(fields=FIELDS, params=params)

    rows = []
    for row in insights:
        actions = row.get("actions", [])
        cost_per_actions = row.get("cost_per_action_type", [])

        landing_page_views = _extract_action_value(actions, "landing_page_view")
        leads = _extract_action_value(actions, "lead")
        link_clicks = float(row.get("inline_link_clicks", 0))
        spend = float(row.get("spend", 0))

        cpl = _extract_cost_per_action(cost_per_actions, "lead")
        if cpl == 0 and leads > 0:
            cpl = spend / leads

        conversion_rate = (leads / landing_page_views * 100) if landing_page_views > 0 else 0.0
        lp_view_rate = (landing_page_views / link_clicks * 100) if link_clicks > 0 else 0.0

        rows.append(
            {
                "campaign_name": row.get("campaign_name", "N/A"),
                "adset_name": row.get("adset_name", "N/A"),
                "spend": spend,
                "impressions": int(row.get("impressions", 0)),
                "cpm": float(row.get("cpm", 0)),
                "frequency": float(row.get("frequency", 0)),
                "link_clicks": link_clicks,
                "link_ctr": float(row.get("inline_link_click_ctr", 0)),
                "landing_page_views": landing_page_views,
                "leads": leads,
                "cpl": cpl,
                "conversion_rate": conversion_rate,
                "lp_view_rate": lp_view_rate,
            }
        )

    return pd.DataFrame(rows)
