"""
Web Link Scraper GUI Application

This module provides a GUI interface for the web link scraper tool.
It allows users to:
- Enter a URL to scrape
- Set the maximum number of links to scrape
- Extract text content from web pages
- Save the results to files
- View the results in a scrollable list
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import os
import re
from urllib.parse import urlparse
import logging
from scraper import Scraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GUI')

class ScraperGUI:
    """GUI application for web link scraping."""
    
    def __init__(self, root):
        """
        Initialize the GUI application.
        
        Args:
            root: The tkinter root window
        """
        self.root = root
        self.root.title("Web Link Scraper")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Create a queue for thread-safe communication
        self.queue = queue.Queue()
        
        # Set styles for a modern look
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#4CAF50")
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=('Helvetica', 10))
        self.style.configure("Header.TLabel", font=('Helvetica', 14, 'bold'))
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the input frame
        self.create_input_frame()
        
        # Create the results frame
        self.create_results_frame()
        
        # Create the status bar
        self.create_status_bar()
        
        # Start the queue processing
        self.process_queue()
        
        # Scraper instance
        self.scraper = None
        
        # Scraping thread
        self.scrape_thread = None
        
        # Text content
        self.text_content = {}
    
    def create_input_frame(self):
        """Create the input frame with URL entry and scrape button."""
        input_frame = ttk.Frame(self.main_frame, padding="5")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # URL Label
        url_label = ttk.Label(input_frame, text="URL:", style="Header.TLabel")
        url_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # URL Entry
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(input_frame, textvariable=self.url_var, width=60)
        self.url_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        self.url_entry.insert(0, "https://")
        
        # Max Links Label and Spinbox
        max_links_label = ttk.Label(input_frame, text="Max Links:")
        max_links_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.max_links_var = tk.IntVar(value=10)
        self.max_links_spinbox = ttk.Spinbox(
            input_frame, 
            from_=1, 
            to=100, 
            textvariable=self.max_links_var, 
            width=10
        )
        self.max_links_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Depth Label and Spinbox
        depth_label = ttk.Label(input_frame, text="Max Depth:")
        depth_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.max_depth_var = tk.IntVar(value=2)
        self.max_depth_spinbox = ttk.Spinbox(
            input_frame, 
            from_=1, 
            to=5, 
            textvariable=self.max_depth_var, 
            width=10
        )
        self.max_depth_spinbox.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Extract Text Checkbox
        self.extract_text_var = tk.BooleanVar(value=True)
        self.extract_text_checkbox = ttk.Checkbutton(
            input_frame,
            text="Extract Text Content",
            variable=self.extract_text_var
        )
        self.extract_text_checkbox.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Scrape Button
        self.scrape_button = ttk.Button(
            input_frame, 
            text="Scrape Links", 
            command=self.start_scraping
        )
        self.scrape_button.grid(row=4, column=0, pady=10)
        
        # Save Content Button
        self.save_button = ttk.Button(
            input_frame, 
            text="Save Content", 
            command=self.save_content,
            state=tk.DISABLED
        )
        self.save_button.grid(row=4, column=1, pady=10)
        
        # Configure grid
        input_frame.columnconfigure(1, weight=1)
    
    def create_results_frame(self):
        """Create the results frame with scrollable text area."""
        results_frame = ttk.Frame(self.main_frame, padding="5")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab Control
        self.tab_control = ttk.Notebook(results_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Links Tab
        self.links_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.links_tab, text="Links")
        
        # Content Tab
        self.content_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.content_tab, text="Content Preview")
        
        # Links Text Area
        self.links_text = scrolledtext.ScrolledText(
            self.links_tab, 
            wrap=tk.WORD, 
            width=80, 
            height=20
        )
        self.links_text.pack(fill=tk.BOTH, expand=True)
        self.links_text.config(state=tk.DISABLED)
        
        # Content Text Area
        self.content_text = scrolledtext.ScrolledText(
            self.content_tab, 
            wrap=tk.WORD, 
            width=80, 
            height=20
        )
        self.content_text.pack(fill=tk.BOTH, expand=True)
        self.content_text.config(state=tk.DISABLED)
    
    def create_status_bar(self):
        """Create the status bar at the bottom of the window."""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def validate_url(self, url):
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
    
    def start_scraping(self):
        """Start the scraping process in a separate thread."""
        url = self.url_var.get().strip()
        
        if not self.validate_url(url):
            messagebox.showerror("Invalid URL", "Please enter a valid URL, including http:// or https://")
            return
        
        max_links = self.max_links_var.get()
        max_depth = self.max_depth_var.get()
        extract_text = self.extract_text_var.get()
        
        # Clear previous results
        self.links_text.config(state=tk.NORMAL)
        self.links_text.delete(1.0, tk.END)
        self.links_text.config(state=tk.DISABLED)
        
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        self.content_text.config(state=tk.DISABLED)
        
        # Update status
        self.status_var.set(f"Scraping {url}...")
        
        # Disable the scrape button while scraping
        self.scrape_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        
        # Create scraper instance
        self.scraper = Scraper(max_links=max_links)
        
        # Start scraping in a separate thread
        self.scrape_thread = threading.Thread(
            target=self.scrape_worker,
            args=(url, max_depth, extract_text)
        )
        self.scrape_thread.daemon = True
        self.scrape_thread.start()
    
    def scrape_worker(self, url, max_depth, extract_text):
        """
        Worker function for scraping in a separate thread.
        
        Args:
            url: The URL to scrape
            max_depth: The maximum depth of recursion
            extract_text: Whether to extract text content
        """
        try:
            # Run the scraper
            links, self.text_content = self.scraper.scrape(url, max_depth=max_depth)
            
            if links:
                links_output = f"Found {len(links)} links:\n\n"
                for i, link in enumerate(links):
                    links_output += f"{i+1}. {link}\n"
                
                # Update the links display
                self.queue.put(("links", links_output))
                
                # Update the content display if text was extracted
                if extract_text and self.text_content:
                    content_preview = f"Text content extracted from {len(self.text_content)} pages.\n"
                    content_preview += "Preview of the first page:\n\n"
                    
                    if self.text_content:
                        first_url = list(self.text_content.keys())[0]
                        first_content = self.text_content[first_url]
                        
                        # Limit preview length
                        if len(first_content) > 2000:
                            content_preview += first_content[:2000] + "...\n\n(Content truncated for preview)"
                        else:
                            content_preview += first_content
                    
                    self.queue.put(("content", content_preview))
                    
                    # Enable the save button
                    self.queue.put(("enable_save", None))
                
                self.queue.put(("status", f"Scraping completed: Found {len(links)} links"))
            else:
                self.queue.put(("status", "No links found"))
                self.queue.put(("links", "No links found"))
        
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            self.queue.put(("status", f"Error: {e}"))
        
        finally:
            # Re-enable the scrape button
            self.queue.put(("enable_scrape", None))
    
    def save_content(self):
        """Save the compiled content to a file."""
        if not self.text_content:
            messagebox.showerror("Error", "No content to save")
            return
        
        # Ask for directory
        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return
        
        try:
            # Create the output directory if it doesn't exist
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Default filename based on the first URL
            first_url = list(self.text_content.keys())[0]
            domain = urlparse(first_url).netloc
            default_filename = f"{domain}_content.txt"
            
            # Full path
            output_path = os.path.join(output_dir, default_filename)
            
            # Save the content
            saved_file = self.scraper.save_text_content(output_path)
            
            # Also save links to a separate file
            links_file = os.path.join(output_dir, "links.txt")
            with open(links_file, "w", encoding="utf-8") as f:
                links_text = self.links_text.get(1.0, tk.END)
                f.write(links_text)
            
            messagebox.showinfo("Success", f"Content saved to {saved_file}\nLinks saved to {links_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving content: {e}")
    
    def process_queue(self):
        """Process messages from the worker thread."""
        try:
            while True:
                message = self.queue.get_nowait()
                message_type, data = message
                
                if message_type == "links":
                    self.links_text.config(state=tk.NORMAL)
                    self.links_text.delete(1.0, tk.END)
                    self.links_text.insert(tk.END, data)
                    self.links_text.config(state=tk.DISABLED)
                    
                elif message_type == "content":
                    self.content_text.config(state=tk.NORMAL)
                    self.content_text.delete(1.0, tk.END)
                    self.content_text.insert(tk.END, data)
                    self.content_text.config(state=tk.DISABLED)
                    
                elif message_type == "status":
                    self.status_var.set(data)
                    
                elif message_type == "enable_scrape":
                    self.scrape_button.config(state=tk.NORMAL)
                    
                elif message_type == "enable_save":
                    self.save_button.config(state=tk.NORMAL)
                
                self.queue.task_done()
                
        except queue.Empty:
            pass
        
        # Schedule to run again
        self.root.after(100, self.process_queue)


def main():
    """Main function to start the GUI application."""
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    main()
