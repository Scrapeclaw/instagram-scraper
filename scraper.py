#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Scraper with Playwright Browser Automation
Handles authentication and anti-bot detection
"""

import asyncio
import json
import os
import sys
import logging
import time
import csv
import re
from typing import List, Dict, Optional
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser
from datetime import datetime
import random
from dotenv import load_dotenv
import aiohttp
import hashlib
from PIL import Image
import io

# Set UTF-8 encoding for stdout
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base directory for the skill
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = DATA_DIR / 'output'
QUEUE_DIR = DATA_DIR / 'queue'
THUMBNAILS_DIR = BASE_DIR / 'thumbnails'
CONFIG_PATH = BASE_DIR / 'config' / 'scraper_config.json'


class ProfileSkippedException(Exception):
    """Exception raised when a profile should be skipped"""
    pass


class ProfileNotFoundException(Exception):
    """Exception raised when a profile doesn't exist"""
    pass


class RateLimitException(Exception):
    """Exception raised when Instagram rate limits the request"""
    pass


class DailyLimitException(Exception):
    """Exception raised when Instagram daily limit is reached"""
    pass


class InstagramScraper:
    """Instagram scraper using Playwright for browser automation"""

    def __init__(self, config_path: Path = None):
        self.config = self._load_config(config_path or CONFIG_PATH)
        self.browser = None
        self.context = None
        self.page = None
        self.logged_in = False
        self.playwright = None

        # Credentials from environment
        self.username = os.getenv('INSTAGRAM_USERNAME', '')
        self.password = os.getenv('INSTAGRAM_PASSWORD', '')

        # Setup directories
        self.thumbnails_dir = THUMBNAILS_DIR
        self.output_dir = OUTPUT_DIR
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize anti-detection
        from anti_detection import AntiDetectionManager
        self.anti_detection_mgr = AntiDetectionManager(DATA_DIR)

    def _load_config(self, config_path: Path) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load config: {e}. Using defaults.")
            return {
                'scraper': {
                    'headless': False,
                    'min_followers': 1000,
                    'download_thumbnails': True,
                    'max_thumbnails': 6
                }
            }

    async def start_browser(self, headless: bool = None):
        """Start Playwright browser with anti-detection"""
        if headless is None:
            headless = self.config.get('scraper', {}).get('headless', False)
        
        logger.info("Starting browser with anti-detection...")
        from anti_detection import BrowserFingerprint
        
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )

        # Apply fingerprint
        fingerprint_mgr = BrowserFingerprint(DATA_DIR)
        fingerprint = fingerprint_mgr.get_random_fingerprint(self.username)
        context_options = fingerprint_mgr.get_context_options(fingerprint)
        self.context = await self.browser.new_context(**context_options)

        self.page = await self.context.new_page()

        # Inject stealth scripts
        stealth_js = fingerprint_mgr.get_stealth_scripts(fingerprint)
        await self.page.add_init_script(stealth_js)

        logger.info("Browser started with anti-detection")

    async def login(self) -> bool:
        """Login to Instagram"""
        if not self.username or not self.password:
            logger.error("Instagram credentials not set. Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD.")
            return False

        try:
            logger.info(f"Logging into Instagram as {self.username}...")
            await asyncio.sleep(2)
            
            # Load login page
            await self.page.goto('https://www.instagram.com/', timeout=30000)
            await asyncio.sleep(4)

            # Find username input
            username_input = None
            username_selectors = [
                'input[name="username"]',
                'input[aria-label*="username" i]',
                'input[type="text"]',
            ]

            for selector in username_selectors:
                try:
                    username_input = await self.page.wait_for_selector(selector, timeout=5000, state='visible')
                    if username_input:
                        break
                except:
                    continue

            if not username_input:
                logger.error("Could not find username input")
                return False

            await username_input.fill(self.username)
            await asyncio.sleep(1)

            # Find password input
            password_input = None
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
            ]

            for selector in password_selectors:
                try:
                    password_input = await self.page.wait_for_selector(selector, timeout=3000, state='visible')
                    if password_input:
                        break
                except:
                    continue

            if not password_input:
                logger.error("Could not find password input")
                return False

            await password_input.fill(self.password)
            await asyncio.sleep(1)

            # Click login button
            login_selectors = [
                'button[type="submit"]',
                'button:has-text("Log in")',
            ]

            for selector in login_selectors:
                try:
                    login_button = await self.page.wait_for_selector(selector, timeout=3000, state='visible')
                    if login_button:
                        await login_button.click()
                        break
                except:
                    continue

            await asyncio.sleep(5)

            # Handle verification if needed
            current_url = self.page.url
            page_content = await self.page.content()

            if 'challenge' in current_url or 'two_factor' in current_url:
                print("\n⚠️  VERIFICATION REQUIRED")
                print("Please complete verification in the browser window...")
                print("Waiting 180 seconds...")
                await asyncio.sleep(180)

            # Handle popups
            try:
                not_now = await self.page.wait_for_selector('button:has-text("Not Now")', timeout=5000)
                if not_now:
                    await not_now.click()
                    await asyncio.sleep(1)
            except:
                pass

            # Verify login
            await asyncio.sleep(2)
            if 'instagram.com' in self.page.url and 'login' not in self.page.url:
                self.logged_in = True
                logger.info("✅ Login successful!")
                return True
            else:
                logger.error("❌ Login failed")
                return False

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    async def download_image(self, url: str, username: str, image_type: str, index: int = 0) -> Optional[str]:
        """Download and resize image to ~150KB"""
        try:
            user_dir = self.thumbnails_dir / username
            user_dir.mkdir(parents=True, exist_ok=True)

            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{image_type}_{index}_{url_hash}.jpg" if image_type != 'profile' else f"profile_{url_hash}.jpg"
            filepath = user_dir / filename

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()

                        img = Image.open(io.BytesIO(content))

                        # Convert to RGB
                        if img.mode in ('RGBA', 'LA', 'P'):
                            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                            img = rgb_img

                        # Resize to max 1000px
                        max_dimension = 1000
                        if max(img.size) > max_dimension:
                            ratio = max_dimension / max(img.size)
                            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                            img = img.resize(new_size, Image.Resampling.LANCZOS)

                        # Save with compression
                        quality = 85
                        output = io.BytesIO()
                        img.save(output, format='JPEG', quality=quality, optimize=True)

                        # Adjust quality to meet ~150KB target
                        while output.tell() > 150 * 1024 and quality > 50:
                            output = io.BytesIO()
                            quality -= 5
                            img.save(output, format='JPEG', quality=quality, optimize=True)

                        with open(filepath, 'wb') as f:
                            f.write(output.getvalue())

                        logger.info(f"Downloaded: {filename} ({output.tell()/1024:.1f}KB)")
                        return str(filepath)

            return None
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None

    async def scrape_profile(self, username: str, category: str = '', location: str = '') -> Optional[Dict]:
        """Scrape a single Instagram profile"""
        if not self.logged_in:
            logger.error("Not logged in. Call login() first.")
            return None

        try:
            from anti_detection import HumanBehaviorSimulator, NetworkPatternRandomizer
            behavior_sim = HumanBehaviorSimulator()
            network_sim = NetworkPatternRandomizer()
            
            url = f'https://www.instagram.com/{username}/'
            logger.info(f"Scraping profile: {username}")

            await network_sim.randomize_network(self.page)
            await behavior_sim.simulate_pre_navigation(self.page)
            response = await self.page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await behavior_sim.simulate_post_navigation(self.page)

            try:
                await self.page.wait_for_selector('header, h2, main', timeout=10000)
            except:
                pass

            await behavior_sim.simulate_content_render(self.page)

            # Check HTTP status
            if response and response.status >= 400:
                if response.status == 404:
                    raise ProfileNotFoundException(f"Profile {username} not found")
                elif response.status == 429:
                    raise RateLimitException("Rate limited")

            # Scroll to load posts
            await behavior_sim.simulate_scroll(self.page)

            try:
                await self.page.wait_for_selector('article img, main img', timeout=8000)
            except:
                pass

            # Check page content
            page_content = await self.page.content()
            page_content_lower = page_content.lower()

            # Check for daily limit
            if 'reached your daily limit' in page_content_lower:
                raise DailyLimitException("Daily limit reached")

            # Check for rate limiting
            if 'http error 429' in page_content_lower:
                raise RateLimitException("Rate limited")

            # Check for not found
            not_found_indicators = [
                "sorry, this page isn't available",
                'page not found',
                'user not found',
            ]
            for indicator in not_found_indicators:
                if indicator in page_content_lower:
                    raise ProfileNotFoundException(f"Profile {username} not found")

            # Check for private
            if 'this account is private' in page_content_lower:
                raise ProfileSkippedException(f"Profile {username} is private")

            await behavior_sim.simulate_final_wait(self.page)

            # Extract data
            profile_data = await self.page.evaluate(r'''() => {
                const data = {};
                data.username = window.location.pathname.split('/').filter(x => x)[0];

                let nameElement = document.querySelector('header section h2') ||
                                 document.querySelector('header h1');
                data.full_name = nameElement ? nameElement.innerText.trim() : data.username;

                const statsText = document.body.innerText;

                const postsMatch = statsText.match(/([\d,KkMm.]+)\s+post/i);
                const followersMatch = statsText.match(/([\d,KkMm.]+)\s+follower/i);
                const followingMatch = statsText.match(/([\d,KkMm.]+)\s+following/i);

                function parseCount(text) {
                    if (!text) return 0;
                    text = text.toUpperCase().replace(/,/g, '');
                    if (text.includes('K')) return Math.floor(parseFloat(text) * 1000);
                    if (text.includes('M')) return Math.floor(parseFloat(text) * 1000000);
                    return parseInt(text) || 0;
                }

                data.posts_count = postsMatch ? parseCount(postsMatch[1]) : 0;
                data.followers = followersMatch ? parseCount(followersMatch[1]) : 0;
                data.following = followingMatch ? parseCount(followingMatch[1]) : 0;

                // Get bio
                const bioSelectors = ['header section div span', '._aa_c'];
                for (const selector of bioSelectors) {
                    const el = document.querySelector(selector);
                    if (el && el.innerText && el.innerText.length > 5) {
                        data.bio = el.innerText.trim();
                        break;
                    }
                }
                if (!data.bio) data.bio = '';

                // Profile pic
                const profilePic = document.querySelector('header img');
                data.profile_pic_url = profilePic ? profilePic.src : '';

                // Verified
                data.is_verified = !!document.querySelector('svg[aria-label="Verified"]');

                // Private
                data.is_private = statsText.toLowerCase().includes('this account is private');

                // Content thumbnails
                data.content_thumbnails = [];
                const images = document.querySelectorAll('article a img, a[href*="/p/"] img');
                for (const img of images) {
                    if (data.content_thumbnails.length >= 6) break;
                    const src = img.src;
                    if (src && src.startsWith('http') && !src.includes('profile')) {
                        data.content_thumbnails.push(src);
                    }
                }

                return data;
            }''')

            # Validate data
            if not profile_data.get('username'):
                return None

            if profile_data.get('is_private'):
                logger.warning(f"Skipping private account: {username}")
                return None

            # Check minimum followers
            min_followers = self.config.get('scraper', {}).get('min_followers', 1000)
            if profile_data.get('followers', 0) < min_followers:
                logger.warning(f"Skipping {username}: {profile_data.get('followers', 0)} followers < {min_followers}")
                return None

            # Classify tier
            followers = profile_data.get('followers', 0)
            if followers < 1000:
                tier = 'nano'
            elif followers < 10000:
                tier = 'micro'
            elif followers < 100000:
                tier = 'mid'
            elif followers < 1000000:
                tier = 'macro'
            else:
                tier = 'mega'

            profile_data['influencer_tier'] = tier

            # Download profile picture
            if profile_data.get('profile_pic_url'):
                profile_pic_local = await self.download_image(
                    profile_data['profile_pic_url'],
                    username,
                    'profile'
                )
                profile_data['profile_pic_local'] = profile_pic_local

            # Download content thumbnails
            content_thumbnails_local = []
            if profile_data.get('content_thumbnails'):
                max_thumbnails = self.config.get('scraper', {}).get('max_thumbnails', 6)
                for idx, thumb_url in enumerate(profile_data['content_thumbnails'][:max_thumbnails], 1):
                    local_path = await self.download_image(thumb_url, username, 'content', idx)
                    if local_path:
                        content_thumbnails_local.append(local_path)
                profile_data['content_thumbnails_local'] = content_thumbnails_local

            # Add metadata
            profile_data['category'] = category
            profile_data['location'] = location
            profile_data['scrape_timestamp'] = datetime.now().isoformat()

            logger.info(f"✅ Scraped: {username} ({followers:,} followers, {tier})")
            return profile_data

        except (ProfileNotFoundException, ProfileSkippedException, RateLimitException, DailyLimitException):
            raise
        except Exception as e:
            logger.error(f"Error scraping {username}: {e}")
            return None

    def save_profile(self, profile: Dict):
        """Save profile to JSON file"""
        username = profile.get('username', 'unknown')
        filepath = self.output_dir / f"{username}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved: {filepath}")

    async def cleanup(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")


def load_queue_file(filepath: str) -> Dict:
    """Load queue file with checkpoint data"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'completed' not in data:
        data['completed'] = []
    if 'current_index' not in data:
        data['current_index'] = 0
    if 'failed' not in data:
        data['failed'] = {}

    return data


def save_queue_file(filepath: str, data: Dict):
    """Save queue file with checkpoint"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def scrape_from_queue(queue_file: str, resume: bool = True) -> List[Dict]:
    """Scrape profiles from a queue file"""
    queue_data = load_queue_file(queue_file)
    
    usernames = queue_data.get('usernames', [])
    completed = set(queue_data.get('completed', []))
    location = queue_data.get('location', '')
    category = queue_data.get('category', '')
    
    # Filter remaining usernames
    remaining = [u for u in usernames if u not in completed]
    
    print(f"\n{'='*50}")
    print(f"📋 Queue: {Path(queue_file).name}")
    print(f"   Location: {location}")
    print(f"   Category: {category}")
    print(f"   Total: {len(usernames)} | Completed: {len(completed)} | Remaining: {len(remaining)}")
    print(f"{'='*50}\n")
    
    if not remaining:
        print("✅ All profiles already scraped!")
        return []
    
    scraper = InstagramScraper()
    results = []
    
    try:
        await scraper.start_browser()
        
        if not await scraper.login():
            logger.error("Failed to login")
            return []
        
        for i, username in enumerate(remaining, 1):
            print(f"\n[{i}/{len(remaining)}] Scraping: @{username}")
            
            try:
                profile = await scraper.scrape_profile(username, category, location)
                
                if profile:
                    results.append(profile)
                    scraper.save_profile(profile)
                    queue_data['completed'].append(username)
                else:
                    queue_data['failed'][username] = 'no_data'
                
            except ProfileNotFoundException:
                queue_data['failed'][username] = 'not_found'
                logger.warning(f"Profile not found: {username}")
            except ProfileSkippedException:
                queue_data['failed'][username] = 'skipped'
            except RateLimitException:
                logger.error("Rate limited! Waiting 60 seconds...")
                await asyncio.sleep(60)
            except DailyLimitException:
                logger.error("Daily limit reached! Stopping.")
                break
            except Exception as e:
                queue_data['failed'][username] = str(e)
                logger.error(f"Error: {e}")
            
            # Save checkpoint
            save_queue_file(queue_file, queue_data)
            
            # Delay between profiles
            delay = random.uniform(3, 6)
            logger.info(f"Waiting {delay:.1f}s...")
            await asyncio.sleep(delay)
        
    finally:
        await scraper.cleanup()
    
    return results


async def scrape_single(username: str, output_json: bool = False) -> Optional[Dict]:
    """Scrape a single profile"""
    scraper = InstagramScraper()
    
    try:
        await scraper.start_browser()
        
        if not await scraper.login():
            if output_json:
                return {"error": "Login failed"}
            return None
        
        profile = await scraper.scrape_profile(username)
        
        if profile:
            scraper.save_profile(profile)
            if output_json:
                return profile
            print(f"\n✅ Scraped: @{username}")
            print(f"   Followers: {profile.get('followers', 0):,}")
            print(f"   Tier: {profile.get('influencer_tier', 'unknown')}")
            return profile
        else:
            if output_json:
                return {"error": "Could not scrape profile"}
            print(f"\n❌ Could not scrape: @{username}")
            return None
        
    finally:
        await scraper.cleanup()


def export_data(output_format: str = 'both'):
    """Export all scraped data to JSON and/or CSV"""
    output_files = list(OUTPUT_DIR.glob('*.json'))
    
    if not output_files:
        print("No data to export")
        return
    
    profiles = []
    for f in output_files:
        with open(f, 'r', encoding='utf-8') as file:
            profiles.append(json.load(file))
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if output_format in ('json', 'both'):
        json_path = DATA_DIR / f"export_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
        print(f"📁 JSON export: {json_path}")
    
    if output_format in ('csv', 'both'):
        csv_path = DATA_DIR / f"export_{timestamp}.csv"
        if profiles:
            keys = ['username', 'full_name', 'followers', 'following', 'posts_count', 
                   'is_verified', 'bio', 'influencer_tier', 'category', 'location']
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(profiles)
        print(f"📁 CSV export: {csv_path}")


def list_queue_files():
    """List all queue files"""
    queue_files = sorted(QUEUE_DIR.glob('*.json'))
    
    if not queue_files:
        print("No queue files found")
        return
    
    print(f"\n{'='*60}")
    print("📋 Available Queue Files")
    print(f"{'='*60}")
    
    for i, qf in enumerate(queue_files, 1):
        try:
            with open(qf, 'r') as f:
                data = json.load(f)
            total = len(data.get('usernames', []))
            completed = len(data.get('completed', []))
            pct = int(completed/total*100) if total > 0 else 0
            print(f"{i}. {qf.name}")
            print(f"   Location: {data.get('location', 'N/A')} | Category: {data.get('category', 'N/A')}")
            print(f"   Progress: {completed}/{total} ({pct}%)")
        except:
            print(f"{i}. {qf.name} (error reading)")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Instagram Profile Scraper')
    parser.add_argument('queue_file', nargs='?', help='Queue file to scrape')
    parser.add_argument('--username', '-u', type=str, help='Single username to scrape')
    parser.add_argument('--list', '-l', action='store_true', help='List queue files')
    parser.add_argument('--resume', '-r', action='store_true', default=True, help='Resume from checkpoint')
    parser.add_argument('--export', '-e', type=str, choices=['json', 'csv', 'both'], help='Export data')
    parser.add_argument('--output', '-o', type=str, choices=['json', 'text'], default='text', help='Output format')
    
    args = parser.parse_args()
    
    if args.list:
        list_queue_files()
    elif args.export:
        export_data(args.export)
    elif args.username:
        result = asyncio.run(scrape_single(args.username, args.output == 'json'))
        if args.output == 'json' and result:
            print(json.dumps(result, indent=2))
    elif args.queue_file:
        asyncio.run(scrape_from_queue(args.queue_file, args.resume))
    else:
        parser.print_help()
