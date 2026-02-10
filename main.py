#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Profile Scraper - Main Entry Point
ClawHub Skill for OpenClaw Agent Integration

Commands:
    discover  - Discover Instagram profiles via Google Search API
    scrape    - Scrape Instagram profiles using browser automation
    list      - List available queue files
    export    - Export scraped data to JSON/CSV
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog='instagram-scraper',
        description='Instagram Profile Discovery and Scraping Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s discover --location "New York" --category "fashion"
  %(prog)s scrape data/queue/NewYork_fashion_20250209.json
  %(prog)s scrape --username influencer123
  %(prog)s list
  %(prog)s export --format json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover Instagram profiles via Google API')
    discover_parser.add_argument('--location', '-l', type=str, help='Location/city to search')
    discover_parser.add_argument('--category', '-c', type=str, help='Category to search')
    discover_parser.add_argument('--count', '-n', type=int, default=10, help='Number of profiles to discover')
    discover_parser.add_argument('--batch', '-b', action='store_true', help='Batch mode for multiple locations')
    discover_parser.add_argument('--output', '-o', type=str, choices=['json', 'text'], default='text')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape Instagram profiles')
    scrape_parser.add_argument('queue_file', nargs='?', help='Queue file to scrape')
    scrape_parser.add_argument('--username', '-u', type=str, help='Single username to scrape')
    scrape_parser.add_argument('--resume', '-r', action='store_true', default=True, help='Resume from checkpoint')
    scrape_parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    scrape_parser.add_argument('--output', '-o', type=str, choices=['json', 'text'], default='text')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available queue files')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export scraped data')
    export_parser.add_argument('--format', '-f', type=str, choices=['json', 'csv', 'both'], default='both')
    
    args = parser.parse_args()
    
    if args.command == 'discover':
        from discovery import discover_command, interactive_discovery, batch_discovery
        
        if args.batch:
            batch_discovery()
        elif args.location and args.category:
            result = discover_command(
                args.location, 
                args.category, 
                args.count, 
                args.output == 'json'
            )
            if args.output == 'json' and result:
                print(json.dumps(result, indent=2))
        else:
            interactive_discovery()
    
    elif args.command == 'scrape':
        from scraper import scrape_from_queue, scrape_single, list_queue_files
        
        if args.username:
            result = asyncio.run(scrape_single(args.username, args.output == 'json'))
            if args.output == 'json' and result:
                print(json.dumps(result, indent=2))
        elif args.queue_file:
            asyncio.run(scrape_from_queue(args.queue_file, args.resume))
        else:
            # Interactive queue selection
            list_queue_files()
            print("\nUsage: python main.py scrape <queue_file>")
    
    elif args.command == 'list':
        from scraper import list_queue_files
        list_queue_files()
    
    elif args.command == 'export':
        from scraper import export_data
        export_data(args.format)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
