"""GitHub API client for repository operations."""

import time
from typing import List, Optional
import requests
from requests.exceptions import RequestException

from config import Config
from models import Repository, SearchResult


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    def __init__(self, config: Config):
        """Initialize GitHub client with configuration."""
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.headers)
    
    def search_repositories(
        self, 
        query: str, 
        max_results: Optional[int] = None
    ) -> SearchResult:
        """
        Search for repositories on GitHub.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to fetch (default: config.max_results)
            
        Returns:
            SearchResult containing repositories and metadata
            
        Raises:
            RequestException: If API request fails
        """
        if not query:
            raise ValueError("Search query cannot be empty")
        
        max_results = min(
            max_results or self.config.max_results,
            self.config.max_results
        )
        
        repositories = []
        page = 1
        total_count = 0
        
        while len(repositories) < max_results:
            params = {
                "q": query,
                "per_page": self.config.per_page,
                "page": page
            }
            
            try:
                response = self._make_request(params)
                data = response.json()
                
                total_count = data.get("total_count", 0)
                items = data.get("items", [])
                
                if not items:
                    break
                
                for item in items:
                    if len(repositories) >= max_results:
                        break
                    repositories.append(Repository.from_api_response(item))
                
                page += 1
                
                # Respect rate limiting
                time.sleep(self.config.request_delay)
                
            except RequestException as e:
                print(f"Error fetching page {page}: {e}")
                break
        
        return SearchResult(
            total_count=total_count,
            repositories=repositories,
            incomplete_results=len(repositories) < min(total_count, max_results)
        )
    
    def _make_request(self, params: dict) -> requests.Response:
        """
        Make API request with error handling.
        
        Args:
            params: Query parameters for the request
            
        Returns:
            Response object
            
        Raises:
            RequestException: If request fails
        """
        response = self.session.get(
            self.config.base_url,
            params=params,
            timeout=30
        )
        
        if response.status_code == 403:
            # Check for rate limit
            if "X-RateLimit-Remaining" in response.headers:
                remaining = int(response.headers["X-RateLimit-Remaining"])
                if remaining == 0:
                    reset_time = int(response.headers["X-RateLimit-Reset"])
                    wait_time = reset_time - int(time.time())
                    raise RequestException(
                        f"Rate limit exceeded. Try again in {wait_time} seconds."
                    )
        
        response.raise_for_status()
        return response
