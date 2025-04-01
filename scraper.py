"""
Web Link Scraper Module

This module contains the Scraper class that handles the web link scraping logic.
It provides functionality to:
- Scrape links from a specific URL
- Recursively follow and scrape links from subsequent pages
- Extract text content from web pages
- Save compiled content to a text file
- Limit the number of links scraped
- Respect robots.txt rules
- Use rate limiting to avoid overwhelming servers
- Filter content by keywords
"""

import re
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List, Optional, Dict, Tuple, Any
import logging
import validators
from urllib.robotparser import RobotFileParser
from tqdm import tqdm
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('WebScraper')

class Scraper:
    """A class that handles recursive web link scraping."""
    
    def __init__(self, max_links: int = 10, rate_limit: float = 1.0, respect_robots: bool = True):
        """
        Initialize the Scraper with a maximum number of links to scrape.
        
        Args:
            max_links: Maximum number of links to scrape, defaults to 10
            rate_limit: Minimum time between requests in seconds, defaults to 1.0
            respect_robots: Whether to respect robots.txt rules, defaults to True
        """
        self.max_links = max_links
        self.rate_limit = rate_limit
        self.respect_robots = respect_robots
        self.visited_urls: Set[str] = set()
        self.all_links: List[str] = []
        self.text_content: Dict[str, str] = {}  # Store URL -> content mapping
        self.robot_parsers: Dict[str, RobotFileParser] = {}  # Cache robot parsers
        self.last_request_time = 0
        self.session = requests.Session()
        # Set a user agent to avoid being blocked by some websites
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.session.headers.update({
            'User-Agent': self.user_agent
        })
        # Success and failure counters
        self.success_count = 0
        self.failure_count = 0
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid using the validators library.
        
        Args:
            url: The URL to check
            
        Returns:
            bool: True if the URL is valid, False otherwise
        """
        try:
            return validators.url(url)
        except Exception as e:
            logger.error(f"Error validating URL {url}: {e}")
            return False
    
    def _get_robot_parser(self, url: str) -> Optional[RobotFileParser]:
        """
        Get or create a robot parser for the given URL's domain.
        
        Args:
            url: The URL to get a robot parser for
            
        Returns:
            Optional[RobotFileParser]: A robot parser for the domain, or None if an error occurred
        """
        if not self.respect_robots:
            return None
            
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            if base_url in self.robot_parsers:
                return self.robot_parsers[base_url]
            
            rp = RobotFileParser()
            rp.set_url(f"{base_url}/robots.txt")
            rp.read()
            self.robot_parsers[base_url] = rp
            return rp
        except Exception as e:
            logger.warning(f"Error reading robots.txt for {url}: {e}")
            return None
    
    def can_fetch(self, url: str) -> bool:
        """
        Check if a URL can be fetched according to robots.txt rules.
        
        Args:
            url: The URL to check
            
        Returns:
            bool: True if the URL can be fetched, False otherwise
        """
        if not self.respect_robots:
            return True
            
        rp = self._get_robot_parser(url)
        if rp is None:
            return True
            
        return rp.can_fetch(self.user_agent, url)
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch the HTML content of a page with rate limiting and robots.txt compliance.
        
        Args:
            url: The URL to fetch
            
        Returns:
            Optional[str]: The HTML content of the page, or None if an error occurred
        """
        if not self.can_fetch(url):
            logger.warning(f"Skipping {url} due to robots.txt rules")
            self.failure_count += 1
            return None
            
        # Apply rate limiting
        self._rate_limit()
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            self.success_count += 1
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            self.failure_count += 1
            return None
    
    def extract_links(self, url: str, html_content: str, filter_same_domain: bool = False) -> List[str]:
        """
        Extract links from HTML content with domain filtering option.
        
        Args:
            url: The base URL for resolving relative links
            html_content: The HTML content to parse
            filter_same_domain: Whether to only include links from the same domain
            
        Returns:
            List[str]: A list of links found in the HTML content
        """
        links = []
        try:
            base_domain = urlparse(url).netloc
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                # Resolve relative URLs
                absolute_url = urljoin(url, href)
                
                # Filter by domain if requested
                if filter_same_domain:
                    link_domain = urlparse(absolute_url).netloc
                    if link_domain != base_domain:
                        continue
                
                # Check if it's a valid URL and not an anchor link
                if self.is_valid_url(absolute_url) and not absolute_url.endswith('#'):
                    # Get the base URL without query parameters
                    base_url = re.sub(r'\?.*$', '', absolute_url)
                    if base_url not in links:
                        links.append(base_url)
        except Exception as e:
            logger.error(f"Error extracting links from {url}: {e}")
        
        return links
    
    def extract_text_content(self, url: str, html_content: str, keywords: List[str] = None) -> str:
        """
        Extract meaningful text content from HTML with optional keyword filtering.
        
        Args:
            url: The URL being parsed
            html_content: The HTML content to parse
            keywords: Optional list of keywords to highlight in the content
            
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
            formatted_content = f"{'═' * 80}\n"  # Pretty separator
            formatted_content += f"URL: {url}\n"
            formatted_content += f"TITLE: {title}\n"
            formatted_content += f"{'═' * 80}\n\n"
            
            # Create sections for better readability
            current_section = ""
            section_lines = []
            formatted_lines = []
            
            # Process lines and create sections
            for line in lines:
                # Potential section header (short lines with no punctuation)
                if len(line) < 50 and not any(c in line for c in ",.;:?!()") and line.strip():
                    # If we have a previous section, add it to formatted lines
                    if section_lines:
                        if current_section:
                            formatted_lines.append(f"\n## {current_section} ##\n")
                        formatted_lines.extend(section_lines)
                        formatted_lines.append("")  # Add spacing between sections
                    
                    # Start a new section
                    current_section = line
                    section_lines = []
                else:
                    section_lines.append(line)
            
            # Add the last section
            if section_lines:
                if current_section:
                    formatted_lines.append(f"\n## {current_section} ##\n")
                formatted_lines.extend(section_lines)
            
            # Highlight keywords if provided
            if keywords and len(keywords) > 0:
                highlighted_lines = []
                for line in formatted_lines:
                    highlighted_line = line
                    for keyword in keywords:
                        if keyword.lower() in line.lower():
                            # Add the line with keyword highlighted
                            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                            highlighted_line = pattern.sub(f"**{keyword}**", highlighted_line)
                    highlighted_lines.append(highlighted_line)
                formatted_content += "\n".join(highlighted_lines)
            else:
                formatted_content += "\n".join(formatted_lines)
                
            formatted_content += "\n\n"
            
            return formatted_content
            
        except Exception as e:
            logger.error(f"Error extracting text from {url}: {e}")
            return f"Error extracting text from {url}: {e}\n"
    
    def scrape(self, start_url: str, current_depth: int = 0, max_depth: int = 1, 
              filter_same_domain: bool = False, keywords: List[str] = None, 
              progress_callback: Any = None) -> Tuple[List[str], Dict[str, str]]:
        """
        Recursively scrape links and text content from a URL up to a specified depth.
        
        Args:
            start_url: The URL to start scraping from
            current_depth: The current depth of recursion
            max_depth: The maximum depth of recursion
            filter_same_domain: Whether to only follow links from the same domain
            keywords: Optional list of keywords to highlight in the content
            progress_callback: Optional callback function to report progress
            
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
        
        logger.info(f"{Fore.GREEN}Scraping{Style.RESET_ALL} {start_url} (depth: {current_depth})")
        self.visited_urls.add(start_url)
        
        html_content = self.fetch_page(start_url)
        if not html_content:
            return self.all_links, self.text_content
        
        # Extract text content
        self.text_content[start_url] = self.extract_text_content(start_url, html_content, keywords)
        logger.info(f"Extracted text content from {start_url}")
        
        # Add this URL to our list of links
        if start_url not in self.all_links:
            self.all_links.append(start_url)
            logger.info(f"Added link: {start_url}")
            
            # Report progress if callback is provided
            if progress_callback:
                progress_callback(len(self.all_links), self.max_links)
        
        # If we've reached the maximum number of links, return early
        if len(self.all_links) >= self.max_links:
            return self.all_links, self.text_content
        
        # Extract links from the current page
        links = self.extract_links(start_url, html_content, filter_same_domain)
        
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
                    
                    # Report progress if callback is provided
                    if progress_callback:
                        progress_callback(len(self.all_links), self.max_links)
                
                # Recursively scrape this link
                self.scrape(link, current_depth + 1, max_depth, filter_same_domain, keywords, progress_callback)
        
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
            # Title with pretty formatting
            f.write(f"{'╔' + '═' * 78 + '╗'}\n")
            f.write(f"║{' SCRAPED CONTENT FROM ' + str(len(self.text_content)) + ' PAGES':^78}║\n")
            f.write(f"{'╚' + '═' * 78 + '╝'}\n\n")
            
            # Add summary statistics with pretty formatting
            f.write(f"{'┌' + '─' * 30 + ' SUMMARY ' + '─' * 30 + '┐'}\n")
            f.write(f"│ Total URLs visited: {len(self.visited_urls):4} {' ' * 45}│\n")
            f.write(f"│ Successful fetches: {self.success_count:4} {' ' * 45}│\n")
            f.write(f"│ Failed fetches: {self.failure_count:4} {' ' * 47}│\n")
            f.write(f"│ Content extracted from: {len(self.text_content):4} pages {' ' * 37}│\n")
            f.write(f"{'└' + '─' * 78 + '┘'}\n\n")
            
            # Divider before content
            f.write(f"{'═' * 80}\n\n")
            
            # Write actual content
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
        self.success_count = 0
        self.failure_count = 0
        self.robot_parsers = {}
        self.last_request_time = 0
