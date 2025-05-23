"""
Grok Live Search GUI Tool
A Python GUI application for interacting with Xai's grok live search API.
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkinter import filedialog
from datetime import datetime
import configparser
import webbrowser
from typing import Dict, List, Any, Optional, Union
import threading

# Import the API integration module
from grok_live_search_api import GrokLiveSearchAPI

class BubbleChatFrame(ttk.Frame):
    """
    A frame that displays chat messages in a bubble style similar to QQ.
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Create a canvas with scrollbar for the chat bubbles
        self.canvas = tk.Canvas(self, bg="#f0f0f0")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create a frame inside the canvas to hold the bubbles
        self.bubble_frame = ttk.Frame(self.canvas)
        self.bubble_frame_id = self.canvas.create_window((0, 0), window=self.bubble_frame, anchor="nw")
        
        # Pack the widgets
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Configure the canvas to resize with the frame
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.bubble_frame.bind("<Configure>", self._on_bubble_frame_configure)
        
        # Initialize message counter
        self.message_count = 0
        
    def _on_canvas_configure(self, event):
        """Handle canvas resize event."""
        self.canvas.itemconfig(self.bubble_frame_id, width=event.width)
    
    def _on_bubble_frame_configure(self, event):
        """Update the scrollregion when the bubble frame changes size."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def add_user_message(self, message: str):
        """
        Add a user message bubble (right-aligned).
        
        Args:
            message (str): The message text.
        """
        # Create a frame for this message
        msg_frame = ttk.Frame(self.bubble_frame)
        msg_frame.pack(fill="x", padx=10, pady=5)
        
        # Add spacer on the left to push bubble to the right
        spacer = ttk.Frame(msg_frame)
        spacer.pack(side="left", fill="x", expand=True)
        
        # Create the bubble with text
        bubble = ttk.Frame(msg_frame)
        bubble.pack(side="right", padx=5)
        
        # Add the text inside the bubble
        text = tk.Text(bubble, wrap="word", width=40, height=4, bg="#95ec69", 
                      borderwidth=0, highlightthickness=0)
        text.insert("1.0", message)
        text.config(state="disabled")  # Make it read-only
        text.pack(padx=10, pady=10)
        
        # Increment message counter
        self.message_count += 1
        
        # Scroll to the bottom
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
        
    def add_bot_message(self, message: str, citations: List[str] = None):
        """
        Add a bot message bubble (left-aligned).
        
        Args:
            message (str): The message text.
            citations (List[str], optional): List of citation URLs.
        """
        # Create a frame for this message
        msg_frame = ttk.Frame(self.bubble_frame)
        msg_frame.pack(fill="x", padx=10, pady=5)
        
        # Create the bubble with text
        bubble = ttk.Frame(msg_frame)
        bubble.pack(side="left", padx=5)
        
        # Add the text inside the bubble
        text = tk.Text(bubble, wrap="word", width=40, height=4, bg="white", 
                      borderwidth=0, highlightthickness=0)
        text.insert("1.0", message)
        text.config(state="disabled")  # Make it read-only
        text.pack(padx=10, pady=10)
        
        # Add citations if provided
        if citations:
            citation_frame = ttk.Frame(msg_frame)
            citation_frame.pack(side="left", fill="y", padx=5)
            
            citation_label = ttk.Label(citation_frame, text="Citations:")
            citation_label.pack(anchor="w", padx=5, pady=(5, 0))
            
            for i, url in enumerate(citations):
                link = ttk.Label(citation_frame, text=f"[{i+1}] {url[:30]}...", 
                                cursor="hand2", foreground="blue")
                link.pack(anchor="w", padx=5)
                link.bind("<Button-1>", lambda e, url=url: webbrowser.open(url))
        
        # Add spacer on the right
        spacer = ttk.Frame(msg_frame)
        spacer.pack(side="right", fill="x", expand=True)
        
        # Increment message counter
        self.message_count += 1
        
        # Scroll to the bottom
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
        
    def clear(self):
        """Clear all messages from the chat."""
        for widget in self.bubble_frame.winfo_children():
            widget.destroy()
        self.message_count = 0


class APIKeyFrame(ttk.LabelFrame):
    """
    A frame for API key input and management.
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, text="API Key", **kwargs)
        
        # Create widgets
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(self, textvariable=self.api_key_var, width=40, show="*")
        self.show_key_var = tk.BooleanVar(value=False)
        self.show_key_check = ttk.Checkbutton(self, text="Show Key", variable=self.show_key_var,
                                             command=self._toggle_key_visibility)
        self.save_key_button = ttk.Button(self, text="Save Key", command=self._save_key)
        self.load_key_button = ttk.Button(self, text="Load Key", command=self._load_key)
        
        # Layout widgets
        ttk.Label(self, text="Enter API Key:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.show_key_check.grid(row=0, column=2, padx=5, pady=5)
        self.save_key_button.grid(row=0, column=3, padx=5, pady=5)
        self.load_key_button.grid(row=0, column=4, padx=5, pady=5)
        
        # Configure grid
        self.columnconfigure(1, weight=1)
        
    def _toggle_key_visibility(self):
        """Toggle API key visibility."""
        if self.show_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
            
    def _save_key(self):
        """Save API key to a configuration file."""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key first.")
            return
        
        # Create a simple config file
        config = configparser.ConfigParser()
        config["API"] = {"key": api_key}
        
        # Ask user where to save the file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".ini",
            filetypes=[("Configuration files", "*.ini"), ("All files", "*.*")],
            title="Save API Key Configuration"
        )
        
        if file_path:
            try:
                with open(file_path, "w") as f:
                    config.write(f)
                messagebox.showinfo("Success", "API key saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save API key: {str(e)}")
    
    def _load_key(self):
        """Load API key from a configuration file."""
        # Ask user to select the file
        file_path = filedialog.askopenfilename(
            defaultextension=".ini",
            filetypes=[("Configuration files", "*.ini"), ("All files", "*.*")],
            title="Load API Key Configuration"
        )
        
        if file_path:
            try:
                config = configparser.ConfigParser()
                config.read(file_path)
                api_key = config["API"]["key"]
                self.api_key_var.set(api_key)
                messagebox.showinfo("Success", "API key loaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load API key: {str(e)}")
    
    def get_api_key(self) -> str:
        """
        Get the current API key.
        
        Returns:
            str: The API key.
        """
        return self.api_key_var.get().strip()


class SourcesFrame(ttk.LabelFrame):
    """
    A frame for configuring data sources.
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, text="Data Sources", **kwargs)
        
        # Create source checkboxes
        self.web_var = tk.BooleanVar(value=True)
        self.x_var = tk.BooleanVar(value=True)
        self.news_var = tk.BooleanVar(value=False)
        self.rss_var = tk.BooleanVar(value=False)
        
        self.web_check = ttk.Checkbutton(self, text="Web", variable=self.web_var,
                                        command=self._update_source_frames)
        self.x_check = ttk.Checkbutton(self, text="X", variable=self.x_var,
                                      command=self._update_source_frames)
        self.news_check = ttk.Checkbutton(self, text="News", variable=self.news_var,
                                         command=self._update_source_frames)
        self.rss_check = ttk.Checkbutton(self, text="RSS", variable=self.rss_var,
                                        command=self._update_source_frames)
        
        # Layout source checkboxes
        self.web_check.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.x_check.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.news_check.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.rss_check.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        
        # Create source-specific parameter frames
        self.web_frame = WebSourceFrame(self)
        self.x_frame = XSourceFrame(self)
        self.news_frame = NewsSourceFrame(self)
        self.rss_frame = RSSSourceFrame(self)
        
        # Layout source frames
        self.web_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        self.x_frame.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        self.news_frame.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        self.rss_frame.grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        
        # Configure grid
        self.columnconfigure((0, 1, 2, 3), weight=1)
        
        # Update source frames visibility
        self._update_source_frames()
        
    def _update_source_frames(self):
        """Update the visibility of source-specific parameter frames."""
        if self.web_var.get():
            self.web_frame.grid()
        else:
            self.web_frame.grid_remove()
            
        if self.x_var.get():
            self.x_frame.grid()
        else:
            self.x_frame.grid_remove()
            
        if self.news_var.get():
            self.news_frame.grid()
        else:
            self.news_frame.grid_remove()
            
        if self.rss_var.get():
            self.rss_frame.grid()
        else:
            self.rss_frame.grid_remove()
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """
        Get the configured sources.
        
        Returns:
            List[Dict[str, Any]]: List of source configurations.
        """
        sources = []
        
        if self.web_var.get():
            sources.append(self.web_frame.get_config())
            
        if self.x_var.get():
            sources.append(self.x_frame.get_config())
            
        if self.news_var.get():
            sources.append(self.news_frame.get_config())
            
        if self.rss_var.get():
            sources.append(self.rss_frame.get_config())
            
        return sources


class WebSourceFrame(ttk.Frame):
    """
    A frame for configuring web source parameters.
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Create a border
        self.config(relief="groove", borderwidth=1)
        
        # Create widgets
        ttk.Label(self, text="Web Parameters", font=("TkDefaultFont", 10, "bold")).grid(
            row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        ttk.Label(self, text="Country:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.country_var = tk.StringVar()
        self.country_combo = ttk.Combobox(self, textvariable=self.country_var, width=10)
        self.country_combo["values"] = ["", "US", "GB", "CA", "AU", "IN", "DE", "FR", "JP", "CN"]
        self.country_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(self, text="Excluded Websites:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.excluded_var = tk.StringVar()
        self.excluded_entry = ttk.Entry(self, textvariable=self.excluded_var, width=40)
        self.excluded_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(self, text="(comma-separated)").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        self.safe_search_var = tk.BooleanVar(value=True)
        self.safe_search_check = ttk.Checkbutton(self, text="Safe Search", 
                                               variable=self.safe_search_var)
        self.safe_search_check.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Configure grid
        self.columnconfigure(1, weight=1)
        
    def get_config(self) -> Dict[str, Any]:
        """
        Get the web source configuration.
        
        Returns:
            Dict[str, Any]: The web source configuration.
        """
        config = {"type": "web"}
        
        country = self.country_var.get().strip()
        if country:
            config["country"] = country
            
        excluded = self.excluded_var.get().strip()
        if excluded:
            excluded_list = [site.strip() for site in excluded.split(",") if site.strip()]
            if excluded_list:
                config["excluded_websites"] = excluded_list
                
        config["safe_search"] = self.safe_search_var.get()
        
        return config


class XSourceFrame(ttk.Frame):
    """
    A frame for configuring X source parameters.
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Create a border
        self.config(relief="groove", borderwidth=1)
        
        # Create widgets
        ttk.Label(self, text="X Parameters", font=("TkDefaultFont", 10, "bold")).grid(
            row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        ttk.Label(self, text="X Handles:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.handles_var = tk.StringVar()
        self.handles_entry = ttk.Entry(self, textvariable=self.handles_var, width=40)
        self.handles_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(self, text="(comma-separated, without @)").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # Configure grid
        self.columnconfigure(1, weight=1)
        
    def get_config(self) -> Dict[str, Any]:
        """
        Get the X source configuration.
        
        Returns:
            Dict[str, Any]: The X source configuration.
        """
        config = {"type": "x"}
        
        handles = self.handles_var.get().strip()
        if handles:
            handles_list = [handle.strip() for handle in handles.split(",") if handle.strip()]
            if handles_list:
                config["x_handles"] = handles_list
                
        return config


class NewsSourceFrame(ttk.Frame):
    """
    A frame for configuring news source parameters.
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Create a border
        self.config(relief="groove", borderwidth=1)
        
        # Create widgets
        ttk.Label(self, text="News Parameters", font=("TkDefaultFont", 10, "bold")).grid(
            row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        ttk.Label(self, text="Country:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.country_var = tk.StringVar()
        self.country_combo = ttk.Combobox(self, textvariable=self.country_var, width=10)
        self.country_combo["values"] = ["", "US", "GB", "CA", "AU", "IN", "DE", "FR", "JP", "CN"]
        self.country_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(self, text="Excluded Websites:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.excluded_var = tk.StringVar()
        self.excluded_entry = ttk.Entry(self, textvariable=self.excluded_var, width=40)
        self.excluded_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(self, text="(comma-separated)").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        self.safe_search_var = tk.BooleanVar(value=True)
        self.safe_search_check = ttk.Checkbutton(self, text="Safe Search", 
                                               variable=self.safe_search_var)
        self.safe_search_check.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Configure grid
        self.columnconfigure(1, weight=1)
        
    def get_config(self) -> Dict[str, Any]:
        """
        Get the news source configuration.
        
        Returns:
            Dict[str, Any]: The news source configuration.
        """
        config = {"type": "news"}
        
        country = self.country_var.get().strip()
        if country:
            config["country"] = country
            
        excluded = self.excluded_var.get().strip()
        if excluded:
            excluded_list = [site.strip() for site in excluded.split(",") if site.strip()]
            if excluded_list:
                config["excluded_websites"] = excluded_list
                
        config["safe_search"] = self.safe_search_var.get()
        
        return config


class RSSSourceFrame(ttk.Frame):
    """
    A frame for configuring RSS source parameters.
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Create a border
        self.config(relief="groove", borderwidth=1)
        
        # Create widgets
        ttk.Label(self, text="RSS Parameters", font=("TkDefaultFont", 10, "bold")).grid(
            row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        ttk.Label(self, text="RSS Links:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.links_var = tk.StringVar()
        self.links_entry = ttk.Entry(self, textvariable=self.links_var, width=40)
        self.links_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(self, text="(comma-separated)").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # Configure grid
        self.columnconfigure(1, weight=1)
        
    def get_config(self) -> Dict[str, Any]:
        """
        Get the RSS source configuration.
        
        Returns:
            Dict[str, Any]: The RSS source configuration.
        """
        config = {"type": "rss"}
        
        links = self.links_var.get().strip()
        if links:
            links_list = [link.strip() for link in links.split(",") if link.strip()]
            if links_list:
                config["links"] = links_list
                
        return config


class SearchParametersFrame(ttk.LabelFrame):
    """
    A frame for configuring search parameters.
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, text="Search Parameters", **kwargs)

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, height=260)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Create content frame
        self.inner_frame = ttk.Frame(self.canvas)
        self.inner_frame_id = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        # Bind frame size change, update canvas scroll region
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.inner_frame_id, width=e.width))

        # Mouse wheel support (only works when hovering over the Search Parameters area)
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        def _bind_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _unbind_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        self.canvas.bind("<Enter>", _bind_mousewheel)
        self.canvas.bind("<Leave>", _unbind_mousewheel)
        self.inner_frame.bind("<Enter>", _bind_mousewheel)
        self.inner_frame.bind("<Leave>", _unbind_mousewheel)

        # All controls are added to self.inner_frame
        ttk.Label(self.inner_frame, text="Mode:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.mode_var = tk.StringVar(value="auto")
        self.auto_radio = ttk.Radiobutton(self.inner_frame, text="Auto", variable=self.mode_var, value="auto")
        self.on_radio = ttk.Radiobutton(self.inner_frame, text="On", variable=self.mode_var, value="on")
        self.off_radio = ttk.Radiobutton(self.inner_frame, text="Off", variable=self.mode_var, value="off")

        self.auto_radio.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.on_radio.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.off_radio.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        self.sources_frame = SourcesFrame(self.inner_frame)
        self.sources_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="ew")

        ttk.Label(self.inner_frame, text="Date Range:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(self.inner_frame, text="From:").grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.from_date = DateEntry(self.inner_frame, width=12, background='darkblue',
                                   foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.from_date.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.from_date.delete(0, "end")

        ttk.Label(self.inner_frame, text="To:").grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.to_date = DateEntry(self.inner_frame, width=12, background='darkblue',
                                 foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.to_date.grid(row=3, column=2, padx=5, pady=5, sticky="w")
        self.to_date.delete(0, "end")

        ttk.Label(self.inner_frame, text="Max Results:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.max_results_var = tk.IntVar(value=20)
        self.max_results_spinbox = ttk.Spinbox(self.inner_frame, from_=1, to=50, textvariable=self.max_results_var, width=5)
        self.max_results_spinbox.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        self.return_citations_var = tk.BooleanVar(value=True)
        self.return_citations_check = ttk.Checkbutton(self.inner_frame, text="Return Citations",
                                                      variable=self.return_citations_var)
        self.return_citations_check.grid(row=4, column=2, columnspan=2, padx=5, pady=5, sticky="w")

        self.inner_frame.columnconfigure((0, 1, 2, 3), weight=1)
        
    def get_search_parameters(self) -> Dict[str, Any]:
        """
        Get the search parameters.
        
        Returns:
            Dict[str, Any]: The search parameters.
        """
        params = {
            "mode": self.mode_var.get(),
            "sources": self.sources_frame.get_sources(),
            "max_search_results": self.max_results_var.get(),
            "return_citations": self.return_citations_var.get()
        }
        
        from_date = self.from_date.get()
        if from_date:
            params["from_date"] = from_date
            
        to_date = self.to_date.get()
        if to_date:
            params["to_date"] = to_date
            
        return params


class QueryFrame(ttk.LabelFrame):
    """
    A frame for entering and submitting queries.
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, text="Query", **kwargs)
        
        # Create query text area
        self.query_text = tk.Text(self, wrap=tk.WORD, width=40, height=5)
        self.query_text.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        
        # Add scrollbar to query text area
        query_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.query_text.yview)
        query_scrollbar.grid(row=0, column=3, pady=5, sticky="ns")
        self.query_text.configure(yscrollcommand=query_scrollbar.set)
        
        # Create character count label
        self.char_count_var = tk.StringVar(value="Characters: 0/1000")
        self.char_count_label = ttk.Label(self, textvariable=self.char_count_var)
        self.char_count_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # Create model selection
        ttk.Label(self, text="Model:").grid(row=1, column=1, padx=5, pady=5, sticky="e")
        self.model_var = tk.StringVar(value="grok-3-latest")
        self.model_combo = ttk.Combobox(self, textvariable=self.model_var, width=15)
        self.model_combo["values"] = ["grok-3-latest", "grok-2", "grok-1.5-mini"]
        self.model_combo.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # Create submit button
        self.submit_button = ttk.Button(self, text="Execute Search")
        self.submit_button.grid(row=2, column=0, columnspan=3, padx=5, pady=5)
        
        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Bind events
        self.query_text.bind("<KeyRelease>", self._update_char_count)
        
    def _update_char_count(self, event=None):
        """Update the character count label."""
        count = len(self.query_text.get("1.0", "end-1c"))
        self.char_count_var.set(f"Characters: {count}/1000")
        
    def get_query(self) -> str:
        """
        Get the query text.
        
        Returns:
            str: The query text.
        """
        return self.query_text.get("1.0", "end-1c").strip()
    
    def get_model(self) -> str:
        """
        Get the selected model.
        
        Returns:
            str: The model name.
        """
        return self.model_var.get()
    
    def set_submit_callback(self, callback):
        """
        Set the callback function for the submit button.
        
        Args:
            callback: The callback function.
        """
        self.submit_button.config(command=callback)


class GrokLiveSearchGUI:
    """
    Main GUI application for Grok Live Search.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Grok Live Search Tool")
        self.root.geometry("800x800")
        self.root.minsize(800, 800)
        
        # Try to apply a theme if ttkthemes is available
        try:
            import ttkthemes
            self.style = ttkthemes.ThemedStyle(self.root)
            self.style.set_theme("arc")
        except ImportError:
            self.style = ttk.Style()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create paned window for top and bottom sections
        self.paned_window = ttk.PanedWindow(self.main_frame, orient="vertical")
        self.paned_window.pack(fill="both", expand=True)
        
        # Create top frame for parameters
        self.top_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.top_frame, weight=1)
        
        # Create bottom frame for chat display
        self.bottom_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.bottom_frame, weight=2)
        
        # Create API key frame
        self.api_key_frame = APIKeyFrame(self.top_frame)
        self.api_key_frame.pack(fill="x", padx=5, pady=5)
        
        # Create search parameters frame
        self.search_params_frame = SearchParametersFrame(self.top_frame)
        self.search_params_frame.pack(fill="x", padx=5, pady=5)
        
        # Create query frame
        self.query_frame = QueryFrame(self.top_frame)
        self.query_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create chat display frame
        self.chat_frame = ttk.LabelFrame(self.bottom_frame, text="Chat")
        self.chat_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create bubble chat frame
        self.bubble_chat = BubbleChatFrame(self.chat_frame)
        self.bubble_chat.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create clear chat button
        self.clear_button = ttk.Button(self.chat_frame, text="Clear Chat", 
                                     command=self.bubble_chat.clear)
        self.clear_button.pack(padx=5, pady=5)
        
        # Create API handler
        self.api = GrokLiveSearchAPI()
        
        # Set up event handlers
        self.query_frame.set_submit_callback(self._on_submit)
        
        # Add welcome message
        self.bubble_chat.add_bot_message(
            "Welcome to the Grok Live Search Tool!\n\n"
            "Enter your API key above, configure search parameters, "
            "and type your query to get started."
        )
        
    def _show_result_popup(self, content: str, citations: list = None):
        popup = tk.Toplevel(self.root)
        popup.title("Result")
        popup.geometry("800x600")
        popup.transient(self.root)
        popup.grab_set()
        
        # 使用ScrolledText显示内容
        text_area = scrolledtext.ScrolledText(popup, wrap=tk.WORD, font=("Arial", 12))
        text_area.pack(fill="both", expand=True, padx=10, pady=10)
        text_area.insert("1.0", content)
        if citations:
            text_area.insert("end", "\n\n引用：\n")
            for i, url in enumerate(citations):
                text_area.insert("end", f"[{i+1}] {url}\n")
        text_area.config(state="disabled")
        
        # 关闭按钮
        close_btn = ttk.Button(popup, text="关闭", command=popup.destroy)
        close_btn.pack(pady=10)
        
    def _on_submit(self):
        # 获取参数（这些可以在主线程做）
        api_key = self.api_key_frame.get_api_key()
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key.")
            return

        query = self.query_frame.get_query()
        if not query:
            messagebox.showerror("Error", "Please enter a query.")
            return

        model = self.query_frame.get_model()
        search_params = self.search_params_frame.get_search_parameters()
        self.api.set_api_key(api_key)
        self.bubble_chat.add_user_message(query)
        self.root.config(cursor="watch")
        self.query_frame.submit_button.config(state="disabled", text="Searching...")
        self.root.update()

        # 启动后台线程
        threading.Thread(
            target=self._background_search,
            args=(query, model, search_params),
            daemon=True
        ).start()

    def _background_search(self, query, model, search_params):
        try:
            response = self.api.execute_search(
                query=query,
                model=model,
                search_parameters=search_params
            )
            parsed = self.api.parse_response(response)
            # UI更新必须用after
            self.root.after(0, self._on_search_success, parsed)
        except Exception as e:
            self.root.after(0, self._on_search_error, str(e))

    def _on_search_success(self, parsed):
        self.bubble_chat.add_bot_message(
            parsed["content"],
            citations=parsed.get("citations", [])
        )
        self._show_result_popup(parsed["content"], citations=parsed.get("citations", []))
        self.root.config(cursor="")
        self.query_frame.submit_button.config(state="normal", text="Execute Search")

    def _on_search_error(self, error_msg):
        messagebox.showerror("Error", f"Search failed: {error_msg}")
        self.bubble_chat.add_bot_message(f"Error: {error_msg}")
        self.root.config(cursor="")
        self.query_frame.submit_button.config(state="normal", text="Execute Search")


def main():
    # Check if tkcalendar is installed, if not, install it
    try:
        from tkcalendar import DateEntry
    except ImportError:
        import subprocess
        import sys
        
        print("Installing required package: tkcalendar...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tkcalendar"])
        
        # Now import it
        from tkcalendar import DateEntry
    
    # Create the root window
    root = tk.Tk()
    
    # Create the application
    app = GrokLiveSearchGUI(root)
    
    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    # Import DateEntry here to make it available for the class definition
    try:
        from tkcalendar import DateEntry
    except ImportError:
        print("tkcalendar package is required. Please install it with: pip install tkcalendar")
        sys.exit(1)
        
    main()
