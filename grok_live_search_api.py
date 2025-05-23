"""
Grok Live Search API Integration Module
This module handles the API requests and response parsing for the Grok Live Search GUI tool.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

class GrokLiveSearchAPI:
    """
    A class to handle interactions with the Xai Grok Live Search API.
    """
    
    API_URL = "https://api.x.ai/v1/chat/completions"
    
    def __init__(self, api_key: str = None):
        """
        Initialize the API handler with an optional API key.
        
        Args:
            api_key (str, optional): The Xai API key. Defaults to None.
        """
        self.api_key = api_key
        
    def set_api_key(self, api_key: str) -> None:
        """
        Set or update the API key.
        
        Args:
            api_key (str): The Xai API key.
        """
        self.api_key = api_key
        
    def validate_api_key(self) -> bool:
        """
        Check if the API key is set and valid.
        
        Returns:
            bool: True if the API key is set, False otherwise.
        """
        return bool(self.api_key) and len(self.api_key.strip()) > 0
    
    def build_search_parameters(self, 
                               mode: str = "auto",
                               sources: List[Dict[str, Any]] = None,
                               from_date: str = None,
                               to_date: str = None,
                               max_search_results: int = 20,
                               return_citations: bool = True) -> Dict[str, Any]:
        """
        Build the search_parameters dictionary for the API request.
        
        Args:
            mode (str, optional): Search mode ("auto", "on", or "off"). Defaults to "auto".
            sources (List[Dict[str, Any]], optional): List of source configurations. Defaults to None.
            from_date (str, optional): Start date in ISO8601 format (YYYY-MM-DD). Defaults to None.
            to_date (str, optional): End date in ISO8601 format (YYYY-MM-DD). Defaults to None.
            max_search_results (int, optional): Maximum number of search results. Defaults to 20.
            return_citations (bool, optional): Whether to return citations. Defaults to True.
            
        Returns:
            Dict[str, Any]: The search_parameters dictionary.
        """
        search_params = {"mode": mode}
        
        # Add sources if provided
        if sources:
            search_params["sources"] = sources
            
        # Add date range if provided
        if from_date:
            search_params["from_date"] = from_date
        if to_date:
            search_params["to_date"] = to_date
            
        # Add max search results
        search_params["max_search_results"] = max_search_results
        
        # Add return citations
        search_params["return_citations"] = return_citations
        
        return search_params
    
    def build_source_config(self, 
                           source_type: str, 
                           country: str = None,
                           excluded_websites: List[str] = None,
                           safe_search: bool = None,
                           x_handles: List[str] = None,
                           links: List[str] = None) -> Dict[str, Any]:
        """
        Build a source configuration dictionary.
        
        Args:
            source_type (str): The type of source ("web", "x", "news", or "rss").
            country (str, optional): Country code for web/news sources. Defaults to None.
            excluded_websites (List[str], optional): List of websites to exclude. Defaults to None.
            safe_search (bool, optional): Whether to enable safe search. Defaults to None.
            x_handles (List[str], optional): List of X handles for "x" source. Defaults to None.
            links (List[str], optional): List of RSS links for "rss" source. Defaults to None.
            
        Returns:
            Dict[str, Any]: The source configuration dictionary.
        """
        source_config = {"type": source_type}
        
        # Add source-specific parameters
        if source_type in ["web", "news"]:
            if country:
                source_config["country"] = country
            if excluded_websites:
                source_config["excluded_websites"] = excluded_websites
            if safe_search is not None:
                source_config["safe_search"] = safe_search
        elif source_type == "x":
            if x_handles:
                source_config["x_handles"] = x_handles
        elif source_type == "rss":
            if links:
                source_config["links"] = links
                
        return source_config
    
    def execute_search(self, 
                      query: str,
                      model: str = "grok-3-latest",
                      search_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a search using the Grok Live Search API.
        
        Args:
            query (str): The user query.
            model (str, optional): The model to use. Defaults to "grok-3-latest".
            search_parameters (Dict[str, Any], optional): Search parameters. Defaults to None.
            
        Returns:
            Dict[str, Any]: The API response.
            
        Raises:
            ValueError: If the API key is not set.
            requests.RequestException: If the API request fails.
        """
        if not self.validate_api_key():
            raise ValueError("API key is not set or is invalid")
        
        # Set default search parameters if not provided
        if search_parameters is None:
            search_parameters = self.build_search_parameters()
        
        # Build the request payload
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "search_parameters": search_parameters,
            "model": model
        }
        
        # Set up headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Execute the request
        try:
            response = requests.post(self.API_URL, headers=headers, json=payload)
            response.raise_for_status()  # Raise exception for HTTP errors
            return response.json()
        except requests.RequestException as e:
            # Re-raise with more context
            raise requests.RequestException(f"API request failed: {str(e)}")
    
    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the API response into a more usable format.
        
        Args:
            response (Dict[str, Any]): The raw API response.
            
        Returns:
            Dict[str, Any]: The parsed response with extracted content and citations.
        """
        parsed = {
            "content": "",
            "citations": [],
            "raw": response
        }
        
        # Extract the content from the response
        if "choices" in response and response["choices"]:
            choice = response["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                parsed["content"] = choice["message"]["content"]
            
            # Extract citations if available
            if "citations" in choice:
                parsed["citations"] = choice["citations"]
        
        return parsed

# Example usage
if __name__ == "__main__":
    # This is just for demonstration, not executed when imported
    api = GrokLiveSearchAPI("your_api_key_here")
    
    # Build source configurations
    web_source = api.build_source_config("web", safe_search=True)
    x_source = api.build_source_config("x", x_handles=["elonmusk"])
    
    # Build search parameters
    search_params = api.build_search_parameters(
        mode="on",
        sources=[web_source, x_source],
        from_date="2025-01-01",
        max_search_results=10
    )
    
    try:
        # Execute search
        response = api.execute_search(
            query="What are the latest developments in AI?",
            search_parameters=search_params
        )
        
        # Parse response
        parsed = api.parse_response(response)
        
        print("Content:", parsed["content"])
        print("\nCitations:")
        for citation in parsed["citations"]:
            print(f"- {citation}")
    except Exception as e:
        print(f"Error: {str(e)}")
