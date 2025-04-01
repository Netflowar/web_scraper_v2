#!/usr/bin/env python3
"""
Documentation Scraper CLI

This script provides a command-line interface for the specialized 
documentation scraper. It allows users to easily scrape programming
documentation from various websites.
"""

import argparse
import os
import sys
import logging
from doc_scraper import DocScraper
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DocScraperCLI')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Scrape programming documentation websites'
    )
    
    parser.add_argument(
        'url',
        type=str,
        help='The URL to start scraping from'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='scraped_content.txt',
        help='Path to the output text file (default: scraped_content.txt)'
    )
    
    parser.add_argument(
        '-j', '--json-output',
        type=str,
        default='structured_content.json',
        help='Path to the output JSON file (default: structured_content.json)'
    )
    
    parser.add_argument(
        '-m', '--max-links',
        type=int,
        default=20,
        help='Maximum number of links to scrape (default: 20)'
    )
    
    parser.add_argument(
        '-d', '--max-depth',
        type=int,
        default=2,
        help='Maximum depth to scrape (default: 2)'
    )
    
    parser.add_argument(
        '-r', '--rate-limit',
        type=float,
        default=1.0,
        help='Rate limit in seconds between requests (default: 1.0)'
    )
    
    parser.add_argument(
        '-s', '--same-domain',
        action='store_true',
        help='Only follow links to the same domain'
    )
    
    parser.add_argument(
        '--no-robots',
        action='store_true',
        help='Ignore robots.txt rules'
    )
    
    parser.add_argument(
        '-k', '--keywords',
        type=str,
        help='Comma-separated list of keywords to filter content'
    )
    
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Show basic analysis of the scraped content'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='doc_output',
        help='Directory to save output files (default: doc_output)'
    )
    
    return parser.parse_args()

def progress_callback(current, total):
    """Callback for progress updates."""
    tqdm.write(f"Scraped {current}/{total} pages")

def main():
    """Main entry point for the script."""
    # Parse arguments
    args = parse_args()
    
    # Extract keywords if provided
    keywords = None
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(',')]
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Full paths for output files
    text_output = os.path.join(args.output_dir, args.output)
    json_output = os.path.join(args.output_dir, args.json_output)
    
    # Initialize the scraper
    scraper = DocScraper(
        max_links=args.max_links,
        rate_limit=args.rate_limit,
        respect_robots=not args.no_robots
    )
    
    print(f"Starting to scrape {args.url}")
    print(f"Max links: {args.max_links}, Max depth: {args.max_depth}")
    if args.same_domain:
        print("Staying on the same domain")
    if keywords:
        print(f"Filtering for keywords: {', '.join(keywords)}")
    
    # Set up progress bar
    with tqdm(total=args.max_links, desc="Scraping", unit="page") as pbar:
        def update_progress(current, total):
            pbar.update(1)
        
        # Start scraping
        results = scraper.scrape(
            args.url,
            max_depth=args.max_depth,
            filter_same_domain=args.same_domain,
            keywords=keywords,
            progress_callback=update_progress
        )
    
    # Save the results
    text_file = scraper.save_text_content(text_output)
    json_file = scraper.save_structured_data(json_output)
    
    # Print summary
    print("\nScraping completed!")
    print(f"Pages scraped: {len(scraper.visited_urls)}")
    print(f"Successful fetches: {scraper.success_count}")
    print(f"Failed fetches: {scraper.failure_count}")
    print(f"\nOutput files:")
    print(f"  - Text content: {text_file}")
    print(f"  - Structured data: {json_file}")
    
    # Show analysis if requested
    if args.analyze:
        print("\nBasic Analysis:")
        
        # Count pages with code blocks
        code_pages = sum(1 for data in scraper.page_structures.values() 
                         if data.get('code_blocks', []))
        print(f"Pages with code examples: {code_pages}")
        
        # Count total code blocks
        total_blocks = sum(len(data.get('code_blocks', [])) 
                           for data in scraper.page_structures.values())
        print(f"Total code blocks: {total_blocks}")
        
        # Count languages
        languages = {}
        for data in scraper.page_structures.values():
            for block in data.get('code_blocks', []):
                lang = block.get('language', 'unknown')
                languages[lang] = languages.get(lang, 0) + 1
        
        if languages:
            print("Code languages:")
            for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {lang}: {count}")
        
        # Count average headings per page
        total_headings = sum(len(data.get('headings', [])) 
                            for data in scraper.page_structures.values())
        if scraper.page_structures:
            avg_headings = total_headings / len(scraper.page_structures)
            print(f"Average headings per page: {avg_headings:.2f}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 