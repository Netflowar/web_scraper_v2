#!/usr/bin/env python3
"""
Launcher script for the Web Link Scraper.

This script allows users to choose between the GUI and CLI versions.
"""

import sys
import argparse


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Web Link Scraper Launcher")
    
    parser.add_argument(
        "--cli", 
        action="store_true",
        help="Run the command-line interface version"
    )
    
    # Pass remaining arguments to the CLI if needed
    parser.add_argument(
        "remaining", 
        nargs=argparse.REMAINDER,
        help=argparse.SUPPRESS
    )
    
    return parser.parse_args()


def main():
    """Main function to launch the appropriate interface."""
    args = parse_args()
    
    if args.cli:
        # Import and run the CLI
        from cli import main as cli_main
        
        # If there are remaining arguments, pass them to the CLI
        if args.remaining:
            sys.argv = [sys.argv[0]] + args.remaining
        
        return cli_main()
    else:
        try:
            # Try to import and run the GUI
            from main import main as gui_main
            return gui_main()
        except ImportError as e:
            if "_tkinter" in str(e):
                print("Error: Tkinter is not installed or configured properly.")
                print("You can:")
                print("1. Install Tkinter and try again, or")
                print("2. Use the command-line interface with: python run.py --cli [URL] [options]")
                return 1
            else:
                # Some other import error
                print(f"Error: {e}")
                return 1


if __name__ == "__main__":
    sys.exit(main())
