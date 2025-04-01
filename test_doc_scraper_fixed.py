"""
Test script for the documentation scraper.

This script tests the DocScraper class with various programming documentation websites.
"""

import unittest
import os
import sys
import logging
from doc_scraper import DocScraper

# Set up logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TestDocScraper')

class TestDocScraper(unittest.TestCase):
    """Test cases for the DocScraper class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a scraper with modest limits to avoid overwhelming servers
        self.scraper = DocScraper(
            max_links=3,  # Keep it small for testing
            rate_limit=1.0,
            respect_robots=True
        )
        
        # Sample documentation URLs to test - using just one for basic tests
        self.doc_urls = [
            "https://docs.python.org/3/tutorial/index.html",
        ]
        
        # Ensure output directory exists
        os.makedirs("test_output", exist_ok=True)
    
    def test_initialization(self):
        """Test that the scraper initializes correctly."""
        self.assertIsNotNone(self.scraper)
        self.assertEqual(self.scraper.max_links, 3)
        self.assertEqual(self.scraper.rate_limit, 1.0)
        self.assertTrue(self.scraper.respect_robots)
        
        # Check that page structures dictionary is initialized
        self.assertIsNotNone(self.scraper.page_structures)
        self.assertEqual(len(self.scraper.page_structures), 0)
    
    def test_is_doc_site(self):
        """Test the is_doc_site method."""
        # These should be recognized as documentation sites
        doc_sites = [
            "https://docs.python.org/3/tutorial/index.html",
            "https://flask.palletsprojects.com/en/2.3.x/",
            "https://requests.readthedocs.io/en/latest/",
            "https://example.com/docs/api/",
            "https://example.com/documentation/guide.html"
        ]
        
        # These should not be recognized as documentation sites
        non_doc_sites = [
            "https://example.com",
            "https://news.ycombinator.com",
            "https://github.com",
            "https://www.python.org"  # Main site, not docs
        ]
        
        for url in doc_sites:
            self.assertTrue(
                self.scraper.is_doc_site(url), 
                f"Failed to recognize documentation site: {url}"
            )
        
        for url in non_doc_sites:
            self.assertFalse(
                self.scraper.is_doc_site(url),
                f"Incorrectly identified as documentation site: {url}"
            )
    
    def test_single_page_scrape(self):
        """Test scraping a single page with proper error handling."""
        if not self._internet_on():
            self.skipTest("Internet connection required for this test")
        
        url = self.doc_urls[0]  # Python docs
        
        try:
            # Scrape the page
            result = self.scraper.scrape_single_page(url)
            
            # Basic validation
            self.assertIsNotNone(result)
            self.assertIn('url', result)
            self.assertIn('title', result)
            
            # Optional validations that might fail sometimes
            if 'headings' in result:
                self.assertIsInstance(result['headings'], list)
            
            if 'content' in result:
                self.assertIsInstance(result['content'], str)
                self.assertTrue(len(result['content']) > 100)
            
            # Check that the page was added to page structures
            self.assertIn(url, self.scraper.page_structures)
            
        except Exception as e:
            self.fail(f"scrape_single_page raised exception: {e}")
    
    def test_save_content(self):
        """Test saving content to files."""
        # Create a dummy page structure for testing
        dummy_url = "https://example.com/docs"
        dummy_title = "Example Documentation"
        dummy_content = "This is some example documentation content."
        
        # Create a dummy page data structure
        dummy_page = {
            'url': dummy_url,
            'title': dummy_title,
            'headings': [{'level': 1, 'text': 'Example', 'id': 'example'}],
            'code_blocks': [{'language': 'python', 'content': 'print("Hello")'}],
            'toc': [{'text': 'Introduction', 'href': '#intro'}],
            'content': dummy_content
        }
        
        # Add to scraper structures
        self.scraper.page_structures[dummy_url] = dummy_page
        
        # Format and add to text content
        formatted_content = self.scraper.format_page_content(dummy_page)
        self.scraper.text_content[dummy_url] = formatted_content
        
        # Test saving text content
        text_file = self.scraper.save_text_content("test_output/test_content.txt")
        self.assertTrue(os.path.exists(text_file))
        self.assertTrue(os.path.getsize(text_file) > 0)
        
        # Test saving structured data
        json_file = self.scraper.save_structured_data("test_output/test_data.json")
        self.assertTrue(os.path.exists(json_file))
        self.assertTrue(os.path.getsize(json_file) > 0)
    
    def _internet_on(self):
        """Check if internet connection is available."""
        import socket
        try:
            # Try to connect to Google's DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

if __name__ == "__main__":
    unittest.main() 