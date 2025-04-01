#!/usr/bin/env python3
"""
Web Link Scraper CLI

This module provides a command-line interface for the web link scraper tool.
"""

import argparse
import sys
import os
import logging
import validators
from typing import List, Optional
from tqdm import tqdm
from colorama import Fore, Style, init
from scraper import Scraper

# Initialize colorama for colored terminal output
init()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CLI')


def progress_callback(current: int, total: int):
    """Update the progress bar"""
    # This function will be called by the scraper to update progress
    # but we're using tqdm in the main function, so this is a no-op
    pass


def validate_url(url: str) -> bool:
    """
    Validate a URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        bool: True if the URL is valid, False otherwise
    """
    return validators.url(url) is True


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Web Link Scraper CLI')
    
    parser.add_argument(
        'url',
        help='URL to start scraping from'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file to save content to',
        default='scraped_content.txt'
    )
    
    parser.add_argument(
        '-m', '--max-links',
        help='Maximum number of links to scrape',
        type=int,
        default=10
    )
    
    parser.add_argument(
        '-d', '--max-depth',
        help='Maximum depth of recursion',
        type=int,
        default=1
    )
    
    parser.add_argument(
        '-r', '--rate-limit',
        help='Minimum time between requests in seconds',
        type=float,
        default=1.0
    )
    
    parser.add_argument(
        '-s', '--same-domain',
        help='Only follow links from the same domain',
        action='store_true'
    )
    
    parser.add_argument(
        '-k', '--keywords',
        help='Comma-separated list of keywords to highlight in content',
        default=''
    )
    
    parser.add_argument(
        '--no-robots',
        help='Disable robots.txt compliance',
        action='store_true'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        help='Enable verbose output',
        action='store_true'
    )
    
    return parser.parse_args()


def main():
    """Main function for the CLI."""
    # Parse arguments
    args = parse_args()
    
    # Validate URL
    if not validate_url(args.url):
        print(f"{Fore.RED}Error: Invalid URL{Style.RESET_ALL}")
        return 1
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Parse keywords
    keywords = None
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(',')]
    
    # Create scraper
    scraper = Scraper(
        max_links=args.max_links,
        rate_limit=args.rate_limit,
        respect_robots=not args.no_robots
    )
    
    print(f"{Fore.GREEN}Starting scraper with the following settings:{Style.RESET_ALL}")
    print(f"  URL: {args.url}")
    print(f"  Max links: {args.max_links}")
    print(f"  Max depth: {args.max_depth}")
    print(f"  Same domain only: {'Yes' if args.same_domain else 'No'}")
    print(f"  Respect robots.txt: {'No' if args.no_robots else 'Yes'}")
    print(f"  Rate limit: {args.rate_limit} seconds")
    print(f"  Keywords: {', '.join(keywords) if keywords else 'None'}")
    print(f"  Output file: {args.output}")
    print()
    
    # Use tqdm to show a progress bar
    with tqdm(total=args.max_links, desc="Scraping", unit="links") as pbar:
        
        def update_progress(current, total):
            pbar.n = current
            pbar.refresh()
        
        # Run the scraper
        try:
            links, text_content = scraper.scrape(
                args.url,
                max_depth=args.max_depth,
                filter_same_domain=args.same_domain,
                keywords=keywords,
                progress_callback=update_progress
            )
            
            # Save the content
            if text_content:
                output_file = scraper.save_text_content(args.output)
                print(f"\n{Fore.GREEN}Content saved to {output_file}{Style.RESET_ALL}")
                
                # Print summary
                print(f"\n{Fore.BLUE}Summary:{Style.RESET_ALL}")
                print(f"  Total URLs visited: {len(scraper.visited_urls)}")
                print(f"  Successful fetches: {scraper.success_count}")
                print(f"  Failed fetches: {scraper.failure_count}")
                print(f"  Content extracted from: {len(text_content)} pages")
            else:
                print(f"\n{Fore.YELLOW}No content was extracted{Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Scraping interrupted by user{Style.RESET_ALL}")
            
            # Try to save any content collected so far
            if hasattr(scraper, 'text_content') and scraper.text_content:
                output_file = scraper.save_text_content(args.output)
                print(f"{Fore.GREEN}Partial content saved to {output_file}{Style.RESET_ALL}")
            
            return 1
            
        except Exception as e:
            print(f"\n{Fore.RED}Error during scraping: {e}{Style.RESET_ALL}")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
