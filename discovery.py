#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Profile Discovery Script
Discovers Instagram profiles using Google Custom Search API
Outputs queue files for the Instagram browser scraper
"""

import sys
import io
import json
import logging
import re
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import requests

# Force UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base directory for the skill
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / 'config' / 'scraper_config.json'
QUEUE_DIR = BASE_DIR / 'data' / 'queue'


def load_config(config_path: Path = None) -> Dict:
    """Load configuration from JSON file"""
    if config_path is None:
        config_path = CONFIG_PATH
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load config: {e}. Using defaults.")
        return {
            'cities': ['New York', 'Los Angeles', 'Miami'],
            'categories': ['fashion', 'beauty', 'fitness', 'food', 'travel', 'tech'],
            'google_search': {
                'enabled': True,
                'api_key': '',
                'search_engine_id': '',
                'queries_per_location': 3
            }
        }


def discover_profiles_google(
    location: str, 
    category: str, 
    num_results: int = 10, 
    config: Dict = None
) -> List[str]:
    """
    Discover Instagram profiles using Google Custom Search API
    
    Args:
        location: Location/city to search (e.g., 'New York', 'Miami')
        category: Category to search (e.g., 'fashion', 'beauty', 'fitness')
        num_results: Number of results to fetch per query (max 10)
        config: Configuration dictionary (optional)
    
    Returns:
        List of Instagram usernames
    """
    try:
        if config is None:
            config = load_config()
        
        google_config = config.get('google_search', {})
        if not google_config.get('enabled', False):
            logger.warning("Google Search API is disabled in config")
            return []
        
        api_key = google_config.get('api_key')
        cx = google_config.get('search_engine_id')
        queries_per_location = google_config.get('queries_per_location', 3)
        
        if not api_key or not cx:
            logger.warning("Google API key or Search Engine ID not configured. Using DuckDuckGo fallback.")
            return discover_profiles_duckduckgo(location, category, num_results)
        
        # Generate multiple search queries for better coverage
        search_queries = [
            f'site:instagram.com "{location}" "{category}" influencer',
            f'site:instagram.com "{location}" {category} blogger',
            f'site:instagram.com {category} "{location}"',
        ][:queries_per_location]
        
        all_usernames = []
        
        for query in search_queries:
            try:
                logger.info(f"Searching Google: '{query}'")
                
                # Make API request
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': api_key,
                    'cx': cx,
                    'q': query,
                    'num': min(num_results, 10)  # Google API max is 10
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    total_results = data.get('searchInformation', {}).get('totalResults', 0)
                    logger.info(f"  Found {total_results} total results")
                    
                    # Extract Instagram usernames from URLs
                    for item in data.get('items', []):
                        link = item.get('link', '')
                        match = re.search(r'instagram\.com/([a-zA-Z0-9._]+)/?', link)
                        if match:
                            username = match.group(1)
                            # Filter out common non-profile pages
                            if username not in ['p', 'reel', 'reels', 'explore', 'accounts', 'stories', 'direct', 'tv']:
                                all_usernames.append(username)
                                logger.info(f"  Found: @{username}")
                    
                elif response.status_code == 429:
                    logger.warning("Google API rate limit reached")
                    break
                else:
                    logger.warning(f"Google API error {response.status_code} for query: {query}")
                
                # Small delay between queries
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                continue
        
        # Remove duplicates and return
        unique_usernames = list(set(all_usernames))
        logger.info(f"✅ Discovered {len(unique_usernames)} unique profiles from Google")
        return unique_usernames
            
    except Exception as e:
        logger.error(f"Error in Google profile discovery: {e}")
        return []


def discover_profiles_duckduckgo(
    location: str, 
    category: str, 
    num_results: int = 10
) -> List[str]:
    """
    Discover Instagram profiles using DuckDuckGo HTML search (No API key required)
    
    Args:
        location: Location/city to search
        category: Category to search
        num_results: Number of results to fetch
    
    Returns:
        List of Instagram usernames
    """
    try:
        logger.info(f"Falling back to DuckDuckGo search (no API key required)")
        
        # Construct search query
        query = f'site:instagram.com "{location}" "{category}"'
        url = "https://html.duckduckgo.com/html/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://html.duckduckgo.com/'
        }
        
        params = {'q': query}
        
        logger.info(f"Searching DuckDuckGo: '{query}'")
        response = requests.post(url, data=params, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"DuckDuckGo search failed with status {response.status_code}")
            return []
            
        # Extract usernames using regex
        html_content = response.text
        usernames = []
        
        # Look for instagram.com/username patterns in result links
        # DuckDuckGo HTML format typically puts result links in <a> tags
        # We look for result__a class or similar structure, but regex is more robust to layout changes if careful
        
        # Improved regex to capture usernames from result URLs
        matches = re.findall(r'instagram\.com/([a-zA-Z0-9._]+)/?', html_content)
        
        blacklisted = ['p', 'reel', 'reels', 'explore', 'accounts', 'stories', 'direct', 'tv', 'signin', 'legal']
        
        for username in matches:
            username = username.strip()
            if username and username not in blacklisted and len(username) > 3:
                usernames.append(username)
        
        unique_usernames = list(set(usernames))[:num_results]
        logger.info(f"✅ Discovered {len(unique_usernames)} unique profiles from DuckDuckGo")
        
        return unique_usernames

    except Exception as e:
        logger.error(f"Error in DuckDuckGo discovery: {e}")
        return []


def create_queue_file(
    location: str, 
    category: str, 
    usernames: List[str],
    output_dir: Path = None
) -> str:
    """
    Create a queue file for the scraper
    
    Args:
        location: Location name
        category: Category name
        usernames: List of discovered usernames
        output_dir: Output directory for queue file
    
    Returns:
        Path to created queue file
    """
    if output_dir is None:
        output_dir = QUEUE_DIR
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_location = re.sub(r'[^\w\-]', '_', location)
    filename = f"{safe_location}_{category}_{timestamp}.json"
    filepath = output_dir / filename
    
    queue_data = {
        'location': location,
        'category': category,
        'total': len(usernames),
        'usernames': usernames,
        'completed': [],
        'failed': {},
        'current_index': 0,
        'created_at': datetime.now().isoformat(),
        'source': 'google_api'
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(queue_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📁 Created queue file: {filepath}")
    return str(filepath)


def interactive_discovery():
    """Interactive mode - prompts for single location/category"""
    config = load_config()
    
    print("\n" + "="*50)
    print("🔍 Instagram Profile Discovery")
    print("="*50)
    
    # Get location
    cities = config.get('cities', [])
    print("\nAvailable cities:")
    for i, city in enumerate(cities, 1):
        print(f"  {i}. {city}")
    print(f"  {len(cities)+1}. Enter custom location")
    
    while True:
        try:
            choice = input("\nSelect city (number) or enter custom: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(cities):
                    location = cities[idx]
                    break
                elif idx == len(cities):
                    location = input("Enter custom location: ").strip()
                    break
            else:
                location = choice
                break
        except:
            print("Invalid input. Try again.")
    
    # Get category
    categories = config.get('categories', [])
    print("\nAvailable categories:")
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat}")
    print(f"  {len(categories)+1}. Enter custom category")
    
    while True:
        try:
            choice = input("\nSelect category (number) or enter custom: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    category = categories[idx]
                    break
                elif idx == len(categories):
                    category = input("Enter custom category: ").strip()
                    break
            else:
                category = choice
                break
        except:
            print("Invalid input. Try again.")
    
    # Get count
    while True:
        try:
            count = int(input("\nNumber of profiles to discover (default 10): ").strip() or "10")
            if count > 0:
                break
        except:
            print("Please enter a valid number.")
    
    print(f"\n🔎 Discovering {category} influencers in {location}...")
    
    # Discover profiles
    usernames = discover_profiles_google(location, category, count, config)
    
    if usernames:
        queue_file = create_queue_file(location, category, usernames)
        print(f"\n✅ Successfully discovered {len(usernames)} profiles!")
        print(f"📁 Queue file: {queue_file}")
        print(f"\n🚀 Next step: Run the scraper with:")
        print(f"   python main.py scrape {queue_file}")
    else:
        print("\n❌ No profiles discovered. Check your API credentials.")


def batch_discovery():
    """Batch mode - discover for multiple locations/categories"""
    config = load_config()
    
    print("\n" + "="*50)
    print("🔍 Batch Profile Discovery")
    print("="*50)
    
    cities = config.get('cities', [])
    categories = config.get('categories', [])
    
    # Select cities
    print("\nAvailable cities:")
    for i, city in enumerate(cities, 1):
        print(f"  {i}. {city}")
    
    city_input = input("\nSelect cities (comma-separated numbers or 'all'): ").strip()
    if city_input.lower() == 'all':
        selected_cities = cities
    else:
        indices = [int(x.strip())-1 for x in city_input.split(',') if x.strip().isdigit()]
        selected_cities = [cities[i] for i in indices if 0 <= i < len(cities)]
    
    # Select categories
    print("\nAvailable categories:")
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat}")
    
    cat_input = input("\nSelect categories (comma-separated numbers or 'all'): ").strip()
    if cat_input.lower() == 'all':
        selected_categories = categories
    else:
        indices = [int(x.strip())-1 for x in cat_input.split(',') if x.strip().isdigit()]
        selected_categories = [categories[i] for i in indices if 0 <= i < len(categories)]
    
    # Get count
    count = int(input("\nProfiles per combination (default 10): ").strip() or "10")
    
    print(f"\n📊 Processing {len(selected_cities)} cities × {len(selected_categories)} categories")
    print(f"   = {len(selected_cities) * len(selected_categories)} total combinations")
    
    created_files = []
    
    for city in selected_cities:
        for category in selected_categories:
            print(f"\n🔎 {city} - {category}...")
            usernames = discover_profiles_google(city, category, count, config)
            
            if usernames:
                queue_file = create_queue_file(city, category, usernames)
                created_files.append(queue_file)
            
            # Rate limit protection
            time.sleep(1)
    
    print(f"\n" + "="*50)
    print(f"✅ Batch discovery complete!")
    print(f"📁 Created {len(created_files)} queue files")


def discover_command(
    location: str = None,
    category: str = None,
    count: int = 10,
    output_json: bool = False
) -> Optional[Dict]:
    """
    Command-line discover function for agent integration
    
    Returns JSON-compatible dict if output_json=True
    """
    if not location or not category:
        if output_json:
            return {"error": "location and category are required"}
        interactive_discovery()
        return None
    
    config = load_config()
    usernames = discover_profiles_google(location, category, count, config)
    
    if usernames:
        queue_file = create_queue_file(location, category, usernames)
        result = {
            "success": True,
            "location": location,
            "category": category,
            "profiles_found": len(usernames),
            "usernames": usernames,
            "queue_file": queue_file
        }
    else:
        result = {
            "success": False,
            "error": "No profiles discovered",
            "location": location,
            "category": category
        }
    
    if output_json:
        return result
    else:
        if result["success"]:
            print(f"\n✅ Discovered {len(usernames)} profiles")
            print(f"📁 Queue file: {queue_file}")
        else:
            print("\n❌ No profiles discovered")
        return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Discover Instagram profiles via Google Search API')
    parser.add_argument('--location', '-l', type=str, help='Location/city to search')
    parser.add_argument('--category', '-c', type=str, help='Category to search')
    parser.add_argument('--count', '-n', type=int, default=10, help='Number of profiles to discover')
    parser.add_argument('--batch', '-b', action='store_true', help='Batch mode for multiple locations/categories')
    parser.add_argument('--output', '-o', type=str, choices=['json', 'text'], default='text', help='Output format')
    
    args = parser.parse_args()
    
    if args.batch:
        batch_discovery()
    elif args.location and args.category:
        result = discover_command(args.location, args.category, args.count, args.output == 'json')
        if args.output == 'json' and result:
            print(json.dumps(result, indent=2))
    else:
        interactive_discovery()
