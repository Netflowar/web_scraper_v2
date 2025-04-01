# Web Link Scraper

A versatile web scraping tool that allows you to extract links and content from websites.

## Features

- Scrape links from a starting URL with configurable depth
- Extract and save text content from web pages
- Filter links by domain (stay on same website)
- Highlight specific keywords in the extracted content
- Rate limiting to avoid overwhelming servers
- Respect robots.txt rules
- Progress tracking with visual feedback
- Both GUI and command-line interfaces

## Installation

### Requirements
- Python 3.8+
- Required Python packages: beautifulsoup4, requests, python-dotenv, tqdm, colorama, validators

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/web-link-scraper.git
   cd web-link-scraper
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### GUI Interface

To use the graphical user interface:

```
python run_scraper_ui.py
```

The GUI provides the following options:
- Enter the URL to scrape
- Set the maximum number of links to scrape
- Set the crawling depth
- Configure rate limiting between requests
- Add keywords to highlight in content
- Toggle same-domain filtering
- Enable/disable robots.txt compliance
- Extract and save content

### Command-Line Interface

To use the command-line interface:

```
python cli.py [URL] [options]
```

Options:
- `-o, --output FILE`: Output file (default: scraped_content.txt)
- `-m, --max-links N`: Maximum number of links to scrape (default: 10)
- `-d, --max-depth N`: Maximum depth of recursion (default: 1)
- `-r, --rate-limit N`: Minimum time between requests in seconds (default: 1.0)
- `-s, --same-domain`: Only follow links from the same domain
- `-k, --keywords LIST`: Comma-separated list of keywords to highlight in content
- `--no-robots`: Disable robots.txt compliance
- `-v, --verbose`: Enable verbose output

Example:
```
python cli.py https://example.com -m 20 -d 2 -s -k "example,test,demo"
```

## Library Usage

You can also use the scraper as a library in your own Python code:

```python
from scraper import Scraper

# Create a scraper instance
scraper = Scraper(
    max_links=20,
    rate_limit=1.0,
    respect_robots=True
)

# Define a progress callback function (optional)
def update_progress(current, total):
    print(f"Progress: {current}/{total}")

# Run the scraper
links, content = scraper.scrape(
    "https://example.com",
    max_depth=2,
    filter_same_domain=True,
    keywords=["example", "test"],
    progress_callback=update_progress
)

# Save the content to a file
scraper.save_text_content("output.txt")
```

## Considerations

- Be respectful of websites you scrape. Check the site's terms of service before scraping.
- Use rate limiting to avoid overloading servers.
- Respect robots.txt rules when possible.
- Some websites may block scraping attempts.

## Examples

### Basic Usage

To scrape a website with default settings:

```python
from scraper import Scraper

scraper = Scraper()
links, content = scraper.scrape("https://example.com")
scraper.save_text_content("example_content.txt")
```

### Advanced Usage

To scrape with custom settings:

```python
from scraper import Scraper

scraper = Scraper(max_links=50, rate_limit=2.0)
links, content = scraper.scrape(
    "https://example.com",
    max_depth=3,
    filter_same_domain=True,
    keywords=["important", "keyword"]
)
scraper.save_text_content("example_content.txt")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
