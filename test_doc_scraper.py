"""
Test script for the documentation scraper.

This script tests the DocScraper class with various programming documentation websites.
"""

import unittest
import os
from doc_scraper import DocScraper

class TestDocScraper(unittest.TestCase):
    """Test cases for the DocScraper class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a scraper with modest limits to avoid overwhelming servers
        self.scraper = DocScraper(
            max_links=5,
            rate_limit=2.0,
            respect_robots=True
        )
        
        # Sample documentation URLs to test
        self.doc_urls = [
            "https://docs.python.org/3/tutorial/index.html",
            "https://pyaci.readthedocs.io/en/latest/",
            "https://flask.palletsprojects.com/en/2.3.x/",
            "https://requests.readthedocs.io/en/latest/"
        ]
        
        # Ensure output directory exists
        os.makedirs("test_output", exist_ok=True)
    
    def test_single_page_scrape(self):
        """Test scraping a single page."""
        url = self.doc_urls[0]  # Python docs
        
        # Scrape the page
        result = self.scraper.scrape_single_page(url)
        
        # Check the result
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 0)
        self.assertIn("title", result)
        self.assertIn("content", result)
        self.assertIn("headings", result)
        
        # Check that the title is present and meaningful
        self.assertTrue(len(result["title"]) > 5)
        
        # Check that content has reasonable length
        self.assertTrue(len(result["content"]) > 1000)
    
    def test_multiple_pages_scrape(self):
        """Test scraping multiple pages from a documentation site."""
        url = self.doc_urls[0]  # Python docs
        
        # Scrape multiple pages
        results = self.scraper.scrape(url, max_depth=1, filter_same_domain=True)
        
        # Check we got some results
        self.assertTrue(len(results) > 0)
        
        # Check output file was created
        output_file = self.scraper.save_text_content("test_output/python_docs.txt")
        self.assertTrue(os.path.exists(output_file))
        self.assertTrue(os.path.getsize(output_file) > 1000)
    
    def test_all_doc_sites(self):
        """Test scraping from all documentation sites."""
        for idx, url in enumerate(self.doc_urls):
            # Reset the scraper
            self.scraper.reset()
            
            # Extract domain for the output filename
            domain = url.split("//")[1].split("/")[0]
            
            # Scrape the site
            results = self.scraper.scrape(
                url, 
                max_depth=1, 
                filter_same_domain=True,
                max_links=3  # Keep it limited for testing
            )
            
            # Save the output
            output_file = self.scraper.save_text_content(f"test_output/{domain}_content.txt")
            
            # Verify results
            self.assertTrue(len(results) > 0)
            self.assertTrue(os.path.exists(output_file))
            self.assertTrue(os.path.getsize(output_file) > 0)
            
            # Print basic stats
            print(f"Site {idx+1}: {domain}")
            print(f"  - Pages scraped: {len(self.scraper.visited_urls)}")
            print(f"  - Content size: {os.path.getsize(output_file)} bytes\n")

    def test_content_structure(self):
        """Test that the scraped content is properly structured."""
        url = self.doc_urls[1]  # PyACI docs
        
        # Scrape a page
        result = self.scraper.scrape_single_page(url)
        
        # Check structure
        self.assertIn("title", result)
        self.assertIn("content", result)
        self.assertIn("headings", result)
        self.assertIn("code_blocks", result)
        
        # Check heading structure
        if len(result["headings"]) > 0:
            self.assertTrue(isinstance(result["headings"][0], dict))
            self.assertIn("level", result["headings"][0])
            self.assertIn("text", result["headings"][0])

if __name__ == "__main__":
    unittest.main() 