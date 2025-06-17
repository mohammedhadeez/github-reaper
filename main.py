#!/usr/bin/env python3
"""
GitHub Reaper - Clone multiple GitHub repositories based on search criteria.

This tool searches GitHub for repositories matching a query and allows
batch cloning of selected repositories.
"""

import sys
from pathlib import Path
from typing import Optional

from config import Config
from github_client import GitHubClient
from repository_cloner import RepositoryCloner, parse_ranges
from models import Repository


class GitHubReaper:
    """Main application class for GitHub Reaper."""
    
    def __init__(self, config: Config):
        """Initialize GitHub Reaper with configuration."""
        self.config = config
        self.client = GitHubClient(config)
        self.cloner = RepositoryCloner()
    
    def run(self):
        """Run the main application flow."""
        try:
            # Get search query
            query = self._get_search_query()
            if not query:
                return
            
            # Search repositories
            print(f"\nSearching for repositories matching: '{query}'")
            result = self.client.search_repositories(query)
            
            if not result.repositories:
                print("No repositories found.")
                return
            
            print(f"\nFound {len(result.repositories)} repositories "
                  f"(out of {result.total_count} total)")
            
            # Display repositories
            self._display_repositories(result.repositories)
            
            # Get user selection
            indices = self._get_user_selection(len(result.repositories))
            
            # Clone repositories
            successful, failed = self.cloner.clone_repositories(
                result.repositories, 
                indices
            )
            
            # Display results
            self._display_results(successful, failed)
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}")
            sys.exit(1)
    
    def _get_search_query(self) -> Optional[str]:
        """Get search query from user."""
        query = input("Enter your search query (or 'quit' to exit): ").strip()
        return None if query.lower() == 'quit' else query
    
    def _display_repositories(self, repositories: list[Repository]):
        """Display found repositories."""
        print("\n" + "=" * 80)
        print("Repository URLs Found:")
        print("=" * 80)
        
        for i, repo in enumerate(repositories, 1):
            stars = f"⭐ {repo.stargazers_count}" if repo.stargazers_count else ""
            lang = f"[{repo.language}]" if repo.language else ""
            print(f"{i:3d}. {repo.html_url} {lang} {stars}")
            if repo.description:
                print(f"     {repo.description[:70]}...")
        
        print("=" * 80)
    
    def _get_user_selection(self, total_repos: int) -> Optional[set[int]]:
        """Get user selection for repositories to clone."""
        print(f"\nEnter the repositories to clone:")
        print("  - Single numbers: 1, 5, 10")
        print("  - Ranges: 1-5, 10-15")
        print("  - Combined: 1-5,10,15-20")
        print("  - Press Enter to clone all")
        print("  - Type 'none' to exit without cloning")
        
        selection = input("\nYour selection: ").strip()
        
        if selection.lower() == 'none':
            return set()
        elif not selection:
            return None  # Clone all
        else:
            return parse_ranges(selection, total_repos)
    
    def _display_results(self, successful: list[str], failed: list[str]):
        """Display cloning results."""
        print("\n" + "=" * 80)
        print("Cloning Results:")
        print("=" * 80)
        
        if successful:
            print(f"\n✅ Successfully cloned {len(successful)} repositories:")
            for repo in successful:
                print(f"   - {repo}")
        
        if failed:
            print(f"\n❌ Failed to clone {len(failed)} repositories:")
            for repo in failed:
                print(f"   - {repo}")
        
        print(f"\nTotal: {len(successful)} successful, {len(failed)} failed")


def main():
    """Entry point for the application."""
    try:
        config = Config.from_env()
        app = GitHubReaper(config)
        app.run()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
