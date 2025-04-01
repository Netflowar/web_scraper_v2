"""
Documentation Scraper Module

This module extends the base Scraper class with specialized functionality
for scraping programming documentation websites. It adds features like:
- Improved content extraction for documentation pages
- Heading structure preservation
- Code block detection and formatting
- Better handling of documentation-specific content
- Structured output format
"""

import re
import os
import time
import json
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any, Tuple, Set
import logging
from scraper import Scraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DocScraper')

class DocScraper(Scraper):
    """A specialized scraper for programming documentation websites."""
    
    def __init__(self, max_links: int = 20, rate_limit: float = 1.0, respect_robots: bool = True):
        """
        Initialize the DocScraper.
        
        Args:
            max_links: Maximum number of links to scrape, defaults to 20
            rate_limit: Minimum time between requests in seconds, defaults to 1.0
            respect_robots: Whether to respect robots.txt rules, defaults to True
        """
        super().__init__(max_links, rate_limit, respect_robots)
        
        # Additional attributes for documentation specific content
        self.page_structures: Dict[str, Dict] = {}  # Store structured content for each page
        
        # Common documentation site domains for better handling
        self.doc_domains = [
            'docs.python.org',
            'readthedocs.io',
            'docs.djangoproject.com',
            'flask.palletsprojects.com',
            'nodejs.org',
            'developer.mozilla.org',
            'docs.oracle.com',
            'docs.microsoft.com',
            'docs.aws.amazon.com',
        ]
    
    def is_doc_site(self, url: str) -> bool:
        """
        Check if the URL is likely a documentation site.
        
        Args:
            url: The URL to check
            
        Returns:
            bool: True if it appears to be a documentation site
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Check against known documentation domains
        for doc_domain in self.doc_domains:
            if doc_domain in domain:
                return True
        
        # Check for common documentation URL patterns
        doc_patterns = [
            '/docs/', '/doc/', '/documentation/', '/api/', 
            '/reference/', '/manual/', '/guide/', '/tutorial/'
        ]
        for pattern in doc_patterns:
            if pattern in parsed_url.path:
                return True
        
        return False
    
    def extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract heading structure from the page.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List[Dict]: List of headings with their level and text
        """
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(tag.name[1])
            
            # Get the text, removing any excess whitespace
            text = tag.get_text(strip=True)
            
            # Skip empty headings
            if not text:
                continue
            
            # Get the heading ID if available
            heading_id = tag.get('id', '')
            
            headings.append({
                'level': level,
                'text': text,
                'id': heading_id
            })
        
        return headings
    
    def extract_code_blocks(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract code blocks from the page.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List[Dict]: List of code blocks with their content and language
        """
        code_blocks = []
        
        # Find all <pre><code> combinations (common in many doc sites)
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                # Try to determine the language from class
                language = "unknown"
                if code.get('class'):
                    classes = code.get('class')
                    for cls in classes:
                        if cls.startswith(('language-', 'lang-')):
                            language = cls.split('-')[1]
                
                code_content = code.get_text(strip=True)
                
                # Skip empty blocks
                if not code_content:
                    continue
                
                code_blocks.append({
                    'language': language,
                    'content': code_content
                })
            else:
                # Some sites just use <pre> without <code>
                code_content = pre.get_text(strip=True)
                
                # Skip empty blocks
                if not code_content:
                    continue
                
                code_blocks.append({
                    'language': "unknown",
                    'content': code_content
                })
        
        # Some sites use <div class="highlight">
        for highlight in soup.find_all('div', class_='highlight'):
            code_content = highlight.get_text(strip=True)
            
            # Skip empty blocks
            if not code_content:
                continue
            
            # Try to determine the language
            language = "unknown"
            if highlight.get('class'):
                classes = highlight.get('class')
                for cls in classes:
                    if cls.startswith(('language-', 'lang-', 'highlight-')):
                        parts = cls.split('-')
                        if len(parts) > 1:
                            language = parts[1]
            
            code_blocks.append({
                'language': language,
                'content': code_content
            })
        
        return code_blocks
    
    def extract_toc(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract table of contents if present.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List[Dict]: Table of contents structure
        """
        toc = []
        
        # Common TOC container classes
        toc_containers = [
            soup.find('div', class_='toc'),
            soup.find('nav', class_='toc'),
            soup.find('div', id='table-of-contents'),
            soup.find('nav', id='contents'),
            soup.find('div', class_='contents'),
            soup.find('ul', class_='toctree-wrapper')
        ]
        
        # Use the first TOC container found
        toc_container = next((container for container in toc_containers if container), None)
        
        if toc_container:
            # Extract links from the TOC
            for link in toc_container.find_all('a'):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if href and text:
                    toc.append({
                        'text': text,
                        'href': href
                    })
        
        return toc
    
    def extract_article_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the main article content from the page.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            str: Extracted article content
        """
        # Common content container selectors in documentation sites
        content_selectors = [
            ('div', 'class', 'content'),
            ('div', 'class', 'document'),
            ('article', None, None),
            ('main', None, None),
            ('div', 'class', 'body'),
            ('div', 'id', 'content'),
            ('div', 'class', 'documentation'),
            ('div', 'class', 'section'),
            ('div', 'class', 'container'),
        ]
        
        # Try to find the content container
        content_container = None
        for tag, attr, value in content_selectors:
            if attr and value:
                content_container = soup.find(tag, {attr: value})
            else:
                content_container = soup.find(tag)
            
            if content_container:
                break
        
        # If no container found, use the body as fallback
        if not content_container:
            content_container = soup.body
        
        # Extract text from the content container
        if content_container:
            # Remove navigation, header, footer, etc.
            for element in content_container.find_all(['nav', 'header', 'footer', 'script', 'style', 'aside']):
                element.extract()
            
            # Get text with better spacing for paragraph breaks
            paragraphs = []
            for p in content_container.find_all(['p', 'div', 'section']):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)
            
            content = '\n\n'.join(paragraphs)
        else:
            # Fallback to basic text extraction
            content = soup.get_text(separator='\n\n', strip=True)
        
        return content
    
    def scrape_single_page(self, url: str) -> Dict[str, Any]:
        """
        Scrape a single documentation page and return structured content.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dict: Structured content of the page
        """
        # Fetch the page
        html_content = self.fetch_page(url)
        if not html_content:
            return {}
        
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract page title
            title = soup.title.text.strip() if soup.title else url
            
            # Extract headings, code blocks, TOC
            headings = self.extract_headings(soup)
            code_blocks = self.extract_code_blocks(soup)
            toc = self.extract_toc(soup)
            
            # Extract main content
            content = self.extract_article_content(soup)
            
            # Store structured page data
            page_data = {
                'url': url,
                'title': title,
                'headings': headings,
                'code_blocks': code_blocks,
                'toc': toc,
                'content': content
            }
            
            # Store in the page structures dictionary
            self.page_structures[url] = page_data
            
            return page_data
            
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return {}
    
    def scrape(self, start_url: str, current_depth: int = 0, max_depth: int = 1, 
              filter_same_domain: bool = True, keywords: List[str] = None, 
              progress_callback: Any = None) -> List[str]:
        """
        Scrape documentation pages starting from the given URL.
        
        Args:
            start_url: The URL to start scraping from
            current_depth: Current depth level, defaults to 0 (internal use)
            max_depth: Maximum depth to scrape, defaults to 1
            filter_same_domain: Whether to only follow links to the same domain, defaults to True
            keywords: Optional list of keywords to filter content, defaults to None
            progress_callback: Optional callback function for progress updates, defaults to None
            
        Returns:
            List[str]: List of scraped URLs
        """
        # If we've reached the maximum number of links, stop
        if len(self.visited_urls) >= self.max_links:
            return list(self.visited_urls)
        
        # If we've already visited this URL, skip
        if start_url in self.visited_urls:
            return list(self.visited_urls)
        
        # Validate URL
        if not self.is_valid_url(start_url):
            logger.warning(f"Invalid URL: {start_url}")
            return list(self.visited_urls)
        
        # Fetch the page
        html_content = self.fetch_page(start_url)
        if not html_content:
            return list(self.visited_urls)
        
        # Process the page - extract structured content
        page_data = self.scrape_single_page(start_url)
        
        # Mark as visited
        self.visited_urls.add(start_url)
        
        # Store text content
        if html_content:
            # Format the content for text output
            formatted_content = self.format_page_content(page_data)
            self.text_content[start_url] = formatted_content
        
        # If we've reached the maximum depth, stop
        if current_depth >= max_depth:
            return list(self.visited_urls)
        
        # Extract links
        if html_content:
            links = self.extract_links(start_url, html_content, filter_same_domain)
            
            # Filter to focus on documentation pages
            doc_links = []
            for link in links:
                # Skip already visited links
                if link in self.visited_urls:
                    continue
                
                # Prioritize documentation links
                if self.is_doc_site(link):
                    doc_links.append(link)
            
            # Sort documentation links first, then remaining links
            sorted_links = doc_links + [link for link in links if link not in doc_links]
            
            # Recursively scrape links
            for link in sorted_links:
                # Check if we've reached the maximum links
                if len(self.visited_urls) >= self.max_links:
                    break
                
                # Update progress if callback provided
                if progress_callback:
                    progress_callback(len(self.visited_urls), self.max_links)
                
                # Scrape the link
                self.scrape(link, current_depth + 1, max_depth, filter_same_domain, keywords, progress_callback)
        
        return list(self.visited_urls)
    
    def format_page_content(self, page_data: Dict[str, Any]) -> str:
        """
        Format page data into a nicely formatted text representation.
        
        Args:
            page_data: Structured page data
            
        Returns:
            str: Formatted text content
        """
        if not page_data:
            return ""
        
        # Start with header
        output = f"{'═' * 80}\n"
        output += f"URL: {page_data['url']}\n"
        output += f"TITLE: {page_data['title']}\n"
        output += f"{'═' * 80}\n\n"
        
        # Add table of contents if available
        if page_data.get('toc', []):
            output += "TABLE OF CONTENTS\n"
            output += "----------------\n"
            for item in page_data['toc']:
                output += f"- {item['text']}\n"
            output += "\n"
        
        # Add main content
        output += page_data.get('content', '')
        output += "\n\n"
        
        # Add code blocks if available
        if page_data.get('code_blocks', []):
            output += "CODE EXAMPLES\n"
            output += "-------------\n\n"
            for i, block in enumerate(page_data['code_blocks']):
                output += f"Example {i+1} ({block['language']}):\n"
                output += f"```\n{block['content']}\n```\n\n"
        
        return output
    
    def save_text_content(self, output_file: str = "scraped_content.txt") -> str:
        """
        Save compiled text content to a file with improved formatting.
        
        Args:
            output_file: Path to the output file, defaults to 'scraped_content.txt'
            
        Returns:
            str: Path to the saved file
        """
        if not self.text_content:
            logger.warning("No content to save.")
            return output_file
        
        try:
            # Create summary information
            summary = f"╔{'═' * 78}╗\n"
            summary += f"║{' SCRAPED CONTENT FROM ' + str(len(self.visited_urls)) + ' PAGES':^78}║\n"
            summary += f"╚{'═' * 78}╝\n\n"
            
            summary += f"┌{' SUMMARY ':─^76}┐\n"
            summary += f"│ Total URLs visited:    {len(self.visited_urls):<50}│\n"
            summary += f"│ Successful fetches:    {self.success_count:<50}│\n"
            summary += f"│ Failed fetches:    {self.failure_count:<50}│\n"
            summary += f"│ Content extracted from:    {len(self.text_content)} pages{' ' * 38}│\n"
            summary += f"└{'─' * 76}┘\n\n"
            
            summary += f"{'═' * 80}\n\n"
            
            # Open the file and write the content
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write the summary
                f.write(summary)
                
                # Write the content of each page
                for url, content in self.text_content.items():
                    f.write(content)
                    f.write("\n\n" + "═" * 80 + "\n\n")
            
            logger.info(f"Saved compiled content to {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Error saving content to {output_file}: {e}")
            return output_file
    
    def save_structured_data(self, output_file: str = "structured_content.json") -> str:
        """
        Save structured page data to a JSON file.
        
        Args:
            output_file: Path to the output JSON file, defaults to 'structured_content.json'
            
        Returns:
            str: Path to the saved file
        """
        if not self.page_structures:
            logger.warning("No structured data to save.")
            return output_file
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.page_structures, f, indent=2)
            
            logger.info(f"Saved structured data to {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Error saving structured data to {output_file}: {e}")
            return output_file
    
    def reset(self):
        """Reset the scraper for a new scraping session."""
        super().reset()
        self.page_structures = {} 