"""Configuration management for GitHub Reaper."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration."""
    
    github_token: str
    base_url: str = "https://api.github.com/search/repositories"
    per_page: int = 100
    max_results: int = 1000
    request_delay: float = 1.0  # Delay between API requests in seconds
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        load_dotenv()
        
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError(
                "GITHUB_TOKEN not found in environment variables. "
                "Please create a .env file with your GitHub token."
            )
        
        return cls(github_token=token)
    
    @property
    def headers(self) -> dict[str, str]:
        """Get HTTP headers for GitHub API requests."""
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
