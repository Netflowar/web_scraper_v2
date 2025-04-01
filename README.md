# Documentation Web Scraper

A specialized web scraper for extracting structured content from programming documentation websites. This tool focuses on preserving the structure of documentation, including headings, code blocks, and table of contents.

## Features

- **Documentation-specific scraping**: Optimized for extracting content from programming documentation sites
- **Structure preservation**: Maintains heading hierarchy, code blocks, and table of contents
- **Code block detection**: Identifies and extracts code examples with language detection
- **Prioritized crawling**: Focuses on documentation-relevant pages first
- **Structured output format**: Saves content in both readable text and structured JSON formats
- **Content analysis**: Provides basic analysis of the scraped content

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/doc-scraper.git
cd doc-scraper
```

2. Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

The documentation scraper can be run from the command line using the `run_doc_scraper.py` script:

```bash
python run_doc_scraper.py https://docs.python.org/3/tutorial/index.html
```

#### Command Line Options

```
usage: run_doc_scraper.py [-h] [-o OUTPUT] [-j JSON_OUTPUT] [-m MAX_LINKS]
                        [-d MAX_DEPTH] [-r RATE_LIMIT] [-s] [--no-robots]
                        [-k KEYWORDS] [--analyze] [--output-dir OUTPUT_DIR]
                        url

Scrape programming documentation websites

positional arguments:
  url                   The URL to start scraping from

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path to the output text file (default: scraped_content.txt)
  -j JSON_OUTPUT, --json-output JSON_OUTPUT
                        Path to the output JSON file (default: structured_content.json)
  -m MAX_LINKS, --max-links MAX_LINKS
                        Maximum number of links to scrape (default: 20)
  -d MAX_DEPTH, --max-depth MAX_DEPTH
                        Maximum depth to scrape (default: 2)
  -r RATE_LIMIT, --rate-limit RATE_LIMIT
                        Rate limit in seconds between requests (default: 1.0)
  -s, --same-domain     Only follow links to the same domain
  --no-robots           Ignore robots.txt rules
  -k KEYWORDS, --keywords KEYWORDS
                        Comma-separated list of keywords to filter content
  --analyze             Show basic analysis of the scraped content
  --output-dir OUTPUT_DIR
                        Directory to save output files (default: doc_output)
```

### Examples

#### Scrape Python documentation:

```bash
python run_doc_scraper.py https://docs.python.org/3/tutorial/index.html -s -m 15 -o python_docs.txt --analyze
```

#### Scrape Flask documentation with keyword filtering:

```bash
python run_doc_scraper.py https://flask.palletsprojects.com/en/2.3.x/ -k "route,template,request,app" -m 10 -d 1
```

#### Scrape a ReadTheDocs site:

```bash
python run_doc_scraper.py https://requests.readthedocs.io/en/latest/ -s --output-dir requests_docs
```

## Python API

You can also use the scraper as a Python library:

```python
from doc_scraper import DocScraper

# Initialize the scraper
scraper = DocScraper(max_links=20, rate_limit=1.0)

# Scrape multiple pages
results = scraper.scrape(
    start_url="https://docs.python.org/3/tutorial/index.html",
    max_depth=2,
    filter_same_domain=True
)

# Save the results
text_file = scraper.save_text_content("python_docs.txt")
json_file = scraper.save_structured_data("python_docs.json")

# Access structured data
for url, page_data in scraper.page_structures.items():
    print(f"Page: {page_data['title']}")
    print(f"Headings: {len(page_data['headings'])}")
    print(f"Code blocks: {len(page_data['code_blocks'])}")
```

## Testing

Run the tests to verify functionality:

```bash
python -m unittest test_doc_scraper.py
```

## Structure

- `doc_scraper.py`: The main DocScraper class extending the base Scraper
- `run_doc_scraper.py`: Command-line interface for the documentation scraper
- `test_doc_scraper.py`: Unit tests for the documentation scraper

## Output Formats

### Text Output

The text output is a human-readable format with the following structure:

- URL and title headers
- Table of contents (if available)
- Main content with preserved paragraph structure
- Code examples section with language identification

### JSON Output

The JSON output contains the structured data of each page:

```json
{
  "url": "https://docs.python.org/3/tutorial/index.html",
  "title": "The Python Tutorial",
  "headings": [
    {"level": 1, "text": "The Python Tutorial", "id": "the-python-tutorial"},
    {"level": 2, "text": "Getting Started", "id": "getting-started"}
  ],
  "code_blocks": [
    {"language": "python", "content": "print('Hello, world!')"}
  ],
  "toc": [
    {"text": "Getting Started", "href": "#getting-started"}
  ],
  "content": "This is the main content..."
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
