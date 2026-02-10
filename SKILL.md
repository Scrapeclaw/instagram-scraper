# Instagram Profile Scraper

A browser-based Instagram profile discovery and scraping tool.

```yaml
---
name: instagram-browser-scraper
description: Discover and scrape Instagram profiles from your browser.
emoji: 📸
version: 1.0.2
author: influenza
tags:
  - instagram
  - scraping
  - social-media
  - influencer-discovery
metadata:
  clawdbot:
    requires:
      bins:
        - python3
        - chromium
      env:
        - GOOGLE_API_KEY
        - GOOGLE_SEARCH_ENGINE_ID
        - INSTAGRAM_USERNAME
        - INSTAGRAM_PASSWORD
    config:
      stateDirs:
        - data/output
        - data/queue
        - thumbnails
      outputFormats:
        - json
        - csv
---
```

## Overview

This skill provides a two-phase Instagram scraping system:

1. **Profile Discovery**  
2. **Browser Scraping** 

## Features

- 🔍  - Discover Instagram profiles by location and category
- 🌐  - Full browser simulation for accurate scraping
- 🛡️  - Browser fingerprinting, human behavior simulation, and stealth scripts
- 📊  - Profile info, stats, images, and engagement data
- 💾  - JSON/CSV export with downloaded thumbnails
- 🔄  - Resume interrupted scraping sessions
- ⚡  - Auto-skip private accounts, low followers, empty profiles

## Installation

### 1. Install Python Dependencies

```bash
cd instagram-scraper
pip install -r requirements.txt
```

### 2. Install Playwright Browser

```bash
python -m playwright install chromium
```

### 3. Configure Environment

Create a `.env` file or set environment variables:

```env
# Google Custom Search API (for discovery - optional)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id

# Instagram Credentials (for scraping)
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
```

#### Getting Google API Credentials (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Custom Search API"
4. Create API credentials → API Key
5. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
6. Create a search engine with `instagram.com` as the site to search
7. Copy the Search Engine ID

## Usage

### CLI Commands

#### Discover Profiles

```bash
# Interactive mode - prompts for location/category
python main.py discover

# With arguments
python main.py discover --location "New York" --category "fashion" --count 20

# Batch mode - multiple locations/categories
python main.py discover --batch
```

#### Scrape Profiles

```bash
# Scrape from queue file
python main.py scrape data/queue/NewYork_fashion_20250209.json

# Scrape specific username
python main.py scrape --username fashionblogger123

# Scrape with engagement extraction (slower)
python main.py scrape data/queue/file.json --extract-engagement

# Resume interrupted session
python main.py scrape data/queue/file.json --resume
```

#### List Queue Files

```bash
python main.py list
```

### Agent Tool Interface

For OpenClaw agent integration, the skill provides JSON output:

```bash
# Discover profiles (returns JSON)
python main.py discover --location "Miami" --category "fitness" --output json

# Scrape single profile (returns JSON)
python main.py scrape --username influencer123 --output json
```

## Output Data

### Profile Data Structure

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
  "scrape_timestamp": "2025-02-09T14:30:00"
}
```

### Influencer Tiers

| Tier  | Follower Range    |
|-------|-------------------|
| nano  | < 1,000           |
| micro | 1,000 - 10,000    |
| mid   | 10,000 - 100,000  |
| macro | 100,000 - 1M      |
| mega  | > 1,000,000       |

### File Outputs

- **Queue files**: `data/queue/{location}_{category}_{timestamp}.json`
- **Scraped data**: `data/output/{username}.json`
- **Thumbnails**: `thumbnails/{username}/profile_*.jpg`, `thumbnails/{username}/content_*.jpg`
- **Export files**: `data/export_{timestamp}.json`, `data/export_{timestamp}.csv`

## Configuration

Edit `config/scraper_config.json`:

```json
{
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
    "max_thumbnails": 6
  },
  "cities": ["New York", "Los Angeles", "Miami", "Chicago"],
  "categories": ["fashion", "beauty", "fitness", "food", "travel", "tech"]
}
```



## Filters Applied

The scraper automatically filters out:

- ❌ Private accounts
- ❌ Accounts with < 1,000 followers (configurable)
- ❌ Accounts with no posts
- ❌ Non-existent/removed accounts
- ❌ Already scraped accounts (deduplication)

## Troubleshooting

### Login Issues

- Ensure credentials are correct
- Handle verification codes when prompted
- Wait if rate limited (the script will auto-retry)

### No Profiles Discovered

- Check Google API key and quota
- Verify Search Engine ID is configured for instagram.com
- Try different location/category combinations

### Rate Limiting

- Reduce scraping speed (increase delays)
- Use multiple Instagram accounts
- Run during off-peak hours


