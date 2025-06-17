"""Data models for GitHub Reaper."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Repository:
    """Represents a GitHub repository."""
    
    id: int
    name: str
    full_name: str
    html_url: str
    description: Optional[str]
    language: Optional[str]
    stargazers_count: int
    
    @classmethod
    def from_api_response(cls, data: dict) -> "Repository":
        """Create Repository instance from GitHub API response."""
        return cls(
            id=data["id"],
            name=data["name"],
            full_name=data["full_name"],
            html_url=data["html_url"],
            description=data.get("description"),
            language=data.get("language"),
            stargazers_count=data.get("stargazers_count", 0)
        )


@dataclass
class SearchResult:
    """Represents GitHub search results."""
    
    total_count: int
    repositories: List[Repository]
    incomplete_results: bool = False
