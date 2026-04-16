# Facebook Ads Optimization Dashboard

An interactive Streamlit dashboard that connects to the Facebook Marketing API to pull campaign data, run automated health checks, and provide optimization recommendations.

## Features

- **Data Integration**: Fetches campaign and ad set metrics from the Facebook Marketing API for 7, 14, or 30-day windows
- **Smart Analysis Table**: Automated health checks flag creative fatigue, funnel leaks, conversion issues, and scaling opportunities
- **Manager Insights**: Identifies ads to pause, best-performing audiences, and CPL vs. spend trends
- **Export**: Download health check and daily data as CSV
- **Demo Mode**: Explore the dashboard with realistic sample data before connecting your ad account

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Facebook API credentials:

| Variable | Description |
|----------|-------------|
| `FB_ACCESS_TOKEN` | User or system access token with `ads_read` permission |
| `FB_AD_ACCOUNT_ID` | Your ad account ID (format: `act_XXXXXXXXXX`) |
| `FB_APP_SECRET` | Your Facebook app secret |
| `TARGET_CPL` | Target cost per lead for scaling analysis (default: 50.0) |

#### How to get your credentials

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create or select an app
3. In the [Graph API Explorer](https://developers.facebook.com/tools/explorer/), generate a User Access Token with `ads_read` permission
4. Your Ad Account ID is visible in [Ads Manager](https://www.facebook.com/adsmanager/) (format: `act_XXXXXXXXXX`)
5. The App Secret is in your app's Settings > Basic page

### 3. Run the Dashboard

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`. Enable "Use demo data" in the sidebar to explore without API credentials.

## Project Structure

```
.
├── app.py              # Main Streamlit dashboard
├── fb_api.py           # Facebook Marketing API integration
├── analysis.py         # Health checks and recommendation engine
├── demo_data.py        # Realistic demo data generator
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── .gitignore          # Git ignore rules
```

## Health Check Flags

| Flag | Condition | Action |
|------|-----------|--------|
| **High Fatigue - Refresh Creative** | Frequency > 2.5 and CTR below average | Swap creatives, test new angles |
| **Page Load Issue/High Bounce** | LP View Rate < 60% of clicks | Check page speed, mobile experience |
| **Landing Page/Offer Mismatch** | CTR > 1.2% but Conv. Rate < 5% | Align landing page with ad messaging |
| **Ready to Scale** | CPL 20%+ below target, Frequency < 1.5 | Increase budget incrementally |

## Metrics Tracked

- Campaign Name, Ad Set Name
- Spend, Impressions, CPM
- Link CTR, Frequency
- Link Clicks, Landing Page Views
- Leads, CPL (Cost Per Lead)
- Conversion Rate, LP View Rate
