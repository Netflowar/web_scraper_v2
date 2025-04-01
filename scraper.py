"""
Web Link Scraper Module

This module contains the Scraper class that handles the web link scraping logic.
It provides functionality to:
- Scrape links from a specific URL
- Recursively follow and scrape links from subsequent pages
- Extract text content from web pages
- Save compiled content to a text file
- Limit the number of links scraped
"""

import re
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List, Optional, Dict, Tuple
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('WebScraper')

class Scraper:
    """A class that handles recursive web link scraping."""
    
    def __init__(self, max_links: int = 10):
        """
        Initialize the Scraper with a maximum number of links to scrape.
        
        Args:
            max_links: Maximum number of links to scrape, defaults to 10
        """
        self.max_links = max_links
        self.visited_urls: Set[str] = set()
        self.all_links: List[str] = []
        self.text_content: Dict[str, str] = {}  # Store URL -> content mapping
        self.session = requests.Session()
        # Set a user agent to avoid being blocked by some websites
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid.
        
        Args:
            url: The URL to check
            
        Returns:
            bool: True if the URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception as e:
            logger.error(f"Error validating URL {url}: {e}")
            return False
    
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch the HTML content of a page.
        
        Args:
            url: The URL to fetch
            
        Returns:
            Optional[str]: The HTML content of the page, or None if an error occurred
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_links(self, url: str, html_content: str) -> List[str]:
        """
        Extract links from HTML content.
        
        Args:
            url: The base URL for resolving relative links
            html_content: The HTML content to parse
            
        Returns:
            List[str]: A list of links found in the HTML content
        """
        links = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                # Resolve relative URLs
                absolute_url = urljoin(url, href)
                # Check if it's a valid URL and not an anchor link
                if self.is_valid_url(absolute_url) and not absolute_url.endswith('#'):
                    # Get the base URL without query parameters
                    base_url = re.sub(r'\?.*$', '', absolute_url)
                    if base_url not in links:
                        links.append(base_url)
        except Exception as e:
            logger.error(f"Error extracting links from {url}: {e}")
        
        return links
    
    def extract_text_content(self, url: str, html_content: str) -> str:
        """
        Extract meaningful text content from HTML.
        
        Args:
            url: The URL being parsed
            html_content: The HTML content to parse
            
        Returns:
            str: Extracted text content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav']):
                script_or_style.extract()
                
            # Extract the page title
            title = soup.title.text.strip() if soup.title else url
            
            # Get text content
            text = soup.get_text(separator="\n", strip=True)
            
            # Clean up text: remove excessive whitespace and empty lines
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            
            # Format the content with title and URL
            formatted_content = f"{'='*80}\n"
            formatted_content += f"URL: {url}\n"
            formatted_content += f"TITLE: {title}\n"
            formatted_content += f"{'='*80}\n\n"
            formatted_content += "\n".join(lines)
            formatted_content += "\n\n"
            
            return formatted_content
            
        except Exception as e:
            logger.error(f"Error extracting text from {url}: {e}")
            return f"Error extracting text from {url}: {e}\n"
    
    def scrape(self, start_url: str, current_depth: int = 0, max_depth: int = 1) -> Tuple[List[str], Dict[str, str]]:
        """
        Recursively scrape links and text content from a URL up to a specified depth.
        
        Args:
            start_url: The URL to start scraping from
            current_depth: The current depth of recursion
            max_depth: The maximum depth of recursion
            
        Returns:
            Tuple[List[str], Dict[str, str]]: A tuple containing a list of all links found and a dictionary of text content
        """
        if not self.is_valid_url(start_url):
            logger.error(f"Invalid URL: {start_url}")
            return self.all_links, self.text_content
        
        if start_url in self.visited_urls:
            return self.all_links, self.text_content
        
        if len(self.all_links) >= self.max_links:
            return self.all_links, self.text_content
        
        logger.info(f"Scraping {start_url} (depth: {current_depth})")
        self.visited_urls.add(start_url)
        
        html_content = self.fetch_page(start_url)
        if not html_content:
            return self.all_links, self.text_content
        
        # Extract text content
        self.text_content[start_url] = self.extract_text_content(start_url, html_content)
        logger.info(f"Extracted text content from {start_url}")
        
        # Add this URL to our list of links
        if start_url not in self.all_links:
            self.all_links.append(start_url)
            logger.info(f"Added link: {start_url}")
        
        # If we've reached the maximum number of links, return early
        if len(self.all_links) >= self.max_links:
            return self.all_links, self.text_content
        
        # Extract links from the current page
        links = self.extract_links(start_url, html_content)
        
        # Recursively scrape links if we haven't reached the maximum depth
        if current_depth < max_depth:
            # Create a copy of links to avoid modifying during iteration
            links_to_visit = links.copy()
            for link in links_to_visit:
                # Skip if we've already visited this URL
                if link in self.visited_urls:
                    continue
                
                # Skip if we've reached the maximum number of links
                if len(self.all_links) >= self.max_links:
                    break
                
                # Add this link to our list if it's not already there
                if link not in self.all_links:
                    self.all_links.append(link)
                    logger.info(f"Found link: {link}")
                
                # Recursively scrape this link
                self.scrape(link, current_depth + 1, max_depth)
        
        return self.all_links, self.text_content
    
    def save_text_content(self, output_file: str = "scraped_content.txt") -> str:
        """
        Save the compiled text content to a file.
        
        Args:
            output_file: The file path to save the content to
            
        Returns:
            str: The path to the saved file
        """
        # Create the output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"SCRAPED CONTENT FROM {len(self.text_content)} PAGES\n")
            f.write(f"{'='*80}\n\n")
            
            for url, content in self.text_content.items():
                f.write(content)
                f.write("\n")
                
        logger.info(f"Saved compiled content to {output_file}")
        return output_file
    
    def reset(self):
        """Reset the scraper's state."""
        self.visited_urls = set()
        self.all_links = []
        self.text_content = {}
