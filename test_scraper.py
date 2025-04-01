"""
Test script for the scraper module.

This script provides a simple test case for the Scraper class.
"""

import sys
from scraper import Scraper


def test_scraper():
    """Run a simple test of the Scraper class."""
    print("Testing the Scraper class...")
    
    # Create a scraper with a maximum of 5 links
    scraper = Scraper(max_links=5)
    
    # Specify a test URL
    test_url = "https://example.com"
    
    print(f"Scraping {test_url} with a limit of 5 links...")
    
    # Run the scraper
    links = scraper.scrape(test_url, max_depth=1)
    
    # Print the results
    if links:
        print(f"\nFound {len(links)} links:")
        for i, link in enumerate(links):
            print(f"{i+1}. {link}")
    else:
        print("No links found.")
    
    print("\nTest completed.")


if __name__ == "__main__":
    test_scraper()
