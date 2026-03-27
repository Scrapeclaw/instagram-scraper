# 📸 Instagram Profile Scraper

> Part of **[ScrapeClaw](https://www.scrapeclaw.cc/)** — a suite of production-ready, agentic social media scrapers for Instagram, YouTube, X/Twitter, and Facebook. Built with Python & Playwright. No API keys required.

[![ScrapeClaw](https://img.shields.io/badge/ScrapeClaw-Visit%20Site-blue?style=flat-square)](https://www.scrapeclaw.cc/)
[![ClawHub](https://img.shields.io/badge/ClawHub-View%20Skill-green?style=flat-square)](https://clawhub.ai/ArulmozhiV/instagram-scraper)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-PayPal-yellow?style=flat-square&logo=paypal)](https://www.paypal.com/paypalme/arulmozhivelu)

---

## What Is This?

A browser-based Instagram scraper that discovers and extracts structured data from **public Instagram profiles** — without any official API. It uses Playwright for full browser automation with built-in anti-detection, fingerprinting, and human behavior simulation to scrape at scale reliably.

Two-phase workflow:
1. **Discovery** — Find Instagram profiles by location and category via Google Custom Search
2. **Scraping** — Extract full profile data, stats, posts, and media using a real browser session

---

## Features

| Feature | Description |
|---------|-------------|
| 🔍 **Discovery** | Find profiles by city and category automatically |
| 🌐 **Browser Simulation** | Full Playwright browser — renders JavaScript, handles logins |
| 🛡️ **Anti-Detection** | Browser fingerprinting, stealth scripts, human behavior simulation |
| 📊 **Rich Data** | Profile info, follower counts, bios, posts, engagement stats |
| 🖼️ **Media Download** | Profile pics and content thumbnails saved locally |
| 💾 **Flexible Export** | JSON and CSV output formats |
| 🔄 **Resume Support** | Checkpoint-based resume for interrupted sessions |
| ⚡ **Smart Filtering** | Auto-skip private accounts, low-follower profiles, empty accounts |
| 🔁 **Session Reuse** | Saves login state to skip re-login on subsequent runs |
| 🌍 **Residential Proxy** | Built-in proxy manager supporting 4 major providers |

---

## Installation

```bash
# Clone the repository
git clone https://github.com/Scrapeclaw/instagram-scraper.git
cd instagram-scraper

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Environment Setup

Create a `.env` file in the project root:

```env
# Instagram credentials (required)
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password

# Google Custom Search API (optional, for discovery)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id

# Residential proxy (optional — see Proxy section below)
PROXY_ENABLED=false
PROXY_PROVIDER=brightdata
PROXY_USERNAME=your_proxy_user
PROXY_PASSWORD=your_proxy_pass
PROXY_COUNTRY=us
PROXY_STICKY=true
```

---

## Usage

### Discover Profiles

```bash
# Discover fashion influencers in Miami
python main.py discover --location "Miami" --category "fashion"

# Discover fitness influencers in New York
python main.py discover --location "New York" --category "fitness"

# Return JSON output (for agent integration)
python main.py discover --location "Miami" --category "fitness" --output json
```

### Scrape

```bash
# Scrape a single profile by username
python main.py scrape --username influencer123

# Scrape from a discovery queue file
python main.py scrape data/queue/Miami_fashion_20260220.json

# Run headless
python main.py scrape --username influencer123 --headless
```

### Manage & Export

```bash
# List available queue files
python main.py list

# Export all scraped data to JSON + CSV
python main.py export --format both
```

---

## Output Data

Each scraped profile is saved to `data/output/{username}.json`:

```json
{
  "username": "example_user",
  "full_name": "Example User",
  "bio": "Fashion blogger | NYC",
  "followers": 125000,
  "following": 1500,
  "posts_count": 450,
  "is_verified": false,
  "is_private": false,
  "influencer_tier": "mid",
  "category": "fashion",
  "location": "New York",
  "profile_pic_local": "thumbnails/example_user/profile_abc123.jpg",
  "content_thumbnails": [
    "thumbnails/example_user/content_1_def456.jpg",
    "thumbnails/example_user/content_2_ghi789.jpg"
  ],
  "post_engagement": [
    {"post_url": "https://instagram.com/p/ABC123/", "likes": 5420, "comments": 89}
  ],
  "scrape_timestamp": "2026-02-20T14:30:00"
}
```

### Influencer Tiers

| Tier | Followers |
|------|-----------|
| nano | < 1,000 |
| micro | 1,000 – 10,000 |
| mid | 10,000 – 100,000 |
| macro | 100,000 – 1M |
| mega | > 1,000,000 |

---

## Configuration Reference

Edit `config/scraper_config.json` to customise behaviour:

```json
{
  "proxy": {
    "enabled": false,
    "provider": "brightdata",
    "country": "",
    "sticky": true,
    "sticky_ttl_minutes": 10
  },
  "google_search": {
    "enabled": true,
    "api_key": "",
    "search_engine_id": "",
    "queries_per_location": 3
  },
  "scraper": {
    "headless": false,
    "min_followers": 1000,
    "download_thumbnails": true,
    "max_thumbnails": 6,
    "delay_between_profiles": [5, 10],
    "timeout": 60000
  }
}
```

---

## Project Structure

```
instagram-scraper/
├── main.py               # CLI entry point
├── scraper.py            # Playwright browser scraper
├── discovery.py          # Google-based profile discovery
├── anti_detection.py     # Fingerprinting & stealth
├── proxy_manager.py      # Residential proxy integration
├── config/
│   └── scraper_config.json
├── data/
│   ├── output/           # Scraped JSON files
│   ├── queue/            # Discovery queue files
│   └── browser_fingerprints.json
└── thumbnails/           # Downloaded profile & content images
```

---

## Part of ScrapeClaw

This scraper is one of several tools in the **[ScrapeClaw](https://www.scrapeclaw.cc/)** collection:

| Scraper | Description | Links |
|---------|-------------|-------|
| 📸 **Instagram** | Profiles, posts, media & follower counts | [GitHub](https://github.com/Scrapeclaw/instagram-scraper) · [ClawHub](https://clawhub.ai/ArulmozhiV/instagram-scraper) |
| 📘 **Facebook** | Pages, groups, posts & engagement data | [GitHub](https://github.com/Scrapeclaw/facebook-scraper) · [ClawHub](https://clawhub.ai/ArulmozhiV/facebook-scraper) |
| 🎥 **YouTube** | Channels, subscribers & video metadata | [GitHub](https://github.com/Scrapeclaw/youtube-scrapper) · [ClawHub](https://clawhub.ai/ArulmozhiV/youtube-scrapper) |
| 🐦 **X / Twitter** | Tweets, profiles & engagement metrics | [GitHub](https://github.com/Scrapeclaw/twitter-scraper) · [ClawHub](https://clawhub.ai/ArulmozhiV/x-twitter-scraper) |

All scrapers share the same anti-detection foundation, proxy support, and JSON/CSV export pipeline.

---

## 🚀 ScrapeClaw Customised Solutions

> **We build, you own.** No per-credit fees. Stop renting data — own your entire scraping infrastructure.

ScrapeClaw offers two commercial offerings for teams and businesses that need more than open-source:

### 📦 Tailored Datasets

Get pre-scraped or on-demand datasets built around your exact industry, platform, or niche — delivered ready for analysis.

- Industry-specific social media datasets on demand
- Custom extraction logic ("Skills") for your use case
- One-time delivery or recurring data feeds
- Output in CSV, JSON, or direct database delivery

👉 [**Request a Dataset →**](https://www.scrapeclaw.cc/)

### 🏗️ Private Infrastructure Setup ★ High Value

We deploy a turnkey ScrapeClaw system on your own servers — you own 100% of the infrastructure and the data.

- 🔒 **Privacy & Compliance** — data never leaves your network, ideal for FinTech & Health
- 🤖 **Self-Healing Agents** — AI-powered scrapers that adapt when sites change
- 💸 **Slash API Costs** — stop paying $1–5 per 1K requests; scrape 1M rows at flat infra cost
- Includes **1 month of managed maintenance & support**

👉 [**Book a Strategy Call →**](https://www.scrapeclaw.cc/)

---

## ☕ Support This Project

If this tool saves you time or helps your workflow, consider buying me a coffee — it keeps the project maintained and new scrapers coming!

[![Buy Me a Coffee via PayPal](https://img.shields.io/badge/☕%20Buy%20Me%20a%20Coffee-PayPal-blue?style=for-the-badge&logo=paypal)](https://www.paypal.com/paypalme/arulmozhivelu)

👉 **[paypal.me/arulmozhivelu](https://www.paypal.com/paypalme/arulmozhivelu)**

---

## Disclaimer

This tool is intended for scraping **publicly available** data only. Always comply with Instagram's Terms of Service and your local data privacy regulations. The author is not responsible for any misuse.

---

*Built by [ScrapeClaw](https://www.scrapeclaw.cc/) · [View all scrapers](https://www.scrapeclaw.cc/#scrapers)*
