"""
Setup script for the Web Link Scraper.
"""

from setuptools import setup, find_packages

setup(
    name="web_link_scraper",
    version="1.0.0",
    description="A GUI tool for scraping web links recursively",
    author="User",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "requests>=2.22.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "web_link_scraper_gui=main:main",
            "web_link_scraper=cli:main",
        ],
    },
)
