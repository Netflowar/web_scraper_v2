"""
Command-line interface for the Web Link Scraper.

This module provides a command-line alternative to the GUI application.
"""

import argparse
import sys
import os
from urllib.parse import urlparse
from scraper import Scraper

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Web Link Scraper - CLI Version")
    
    parser.add_argument(
        "url", 
        type=str, 
        help="The URL to start scraping from (include http:// or https://)"
    )
    
    parser.add_argument(
        "-m", 
        "--max-links", 
        type=int, 
        default=10, 
        help="Maximum number of links to scrape (default: 10)"
    )
    
    parser.add_argument(
        "-d", 
        "--max-depth", 
        type=int, 
        default=2, 
        help="Maximum depth of recursion (default: 2)"
    )
    
    parser.add_argument(
        "-o", 
        "--output", 
        type=str, 
        default="scraped_content.txt",
        help="Output file to save the content (default: scraped_content.txt)"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="scraped_data",
        help="Directory to save the output files (default: scraped_data)"
    )
    
    parser.add_argument(
        "--links-only", 
        action="store_true",
        help="Only scrape links, don't extract text content"
    )
    
    return parser.parse_args()


def validate_url(url):
    """
    Validate the URL format.
    
    Args:
        url: The URL to validate
        
    Returns:
        bool: True if the URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def main():
    """Main function for the CLI application."""
    args = parse_args()
    
    # Validate URL
    if not validate_url(args.url):
        print(f"Error: Invalid URL - {args.url}")
        print("Please include http:// or https:// in the URL")
        return 1
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Set output path
    output_path = os.path.join(args.output_dir, args.output)
    
    print(f"Scraping {args.url} with a limit of {args.max_links} links and max depth of {args.max_depth}...")
    
    # Create scraper instance
    scraper = Scraper(max_links=args.max_links)
    
    try:
        # Run the scraper
        links, text_content = scraper.scrape(args.url, max_depth=args.max_depth)
        
        if links:
            # Format the links output
            links_output = f"Found {len(links)} links:\n\n"
            for i, link in enumerate(links):
                links_output += f"{i+1}. {link}\n"
            
            # Save links to a separate file
            links_file = os.path.join(args.output_dir, "links.txt")
            with open(links_file, "w") as f:
                f.write(links_output)
            print(f"Links saved to {links_file}")
            
            # Print links to console
            print(links_output)
            
            # Save text content if not links-only mode
            if not args.links_only:
                if text_content:
                    saved_file = scraper.save_text_content(output_path)
                    print(f"Text content from {len(text_content)} pages saved to {saved_file}")
                else:
                    print("No text content was extracted.")
            
            return 0
        else:
            print("No links found.")
            return 0
    
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
        return 130
    
    except Exception as e:
        print(f"Error during scraping: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
