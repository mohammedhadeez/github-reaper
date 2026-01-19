"""Repository cloning functionality."""

import subprocess
import time
from pathlib import Path
from typing import List, Optional, Set, Tuple
from tqdm import tqdm

from models import Repository


class RepositoryCloner:
    """Handles cloning of GitHub repositories."""
    
    def __init__(self, clone_dir: Optional[Path] = None):
        """
        Initialize repository cloner.
        
        Args:
            clone_dir: Directory to clone repositories into (default: current directory)
        """
        self.clone_dir = clone_dir or Path.cwd()
        self.clone_dir.mkdir(parents=True, exist_ok=True)
    
    def clone_repositories(
        self, 
        repositories: List[Repository],
        indices: Optional[Set[int]] = None
    ) -> Tuple[List[str], List[str]]:
        """
        Clone selected repositories.
        
        Args:
            repositories: List of repositories to clone
            indices: Set of indices to clone (1-based), None for all
            
        Returns:
            Tuple of (successful_clones, failed_clones)
        """
        if indices:
            # Convert to 0-based indices and filter
            repos_to_clone = [
                repo for i, repo in enumerate(repositories) 
                if (i + 1) in indices
            ]
        else:
            repos_to_clone = repositories
        
        if not repos_to_clone:
            print("No repositories selected for cloning.")
            return [], []
        
        successful = []
        failed = []
        
        print(f"\nCloning {len(repos_to_clone)} repositories...")
        
        for repo in tqdm(repos_to_clone, desc="Cloning"):
            success = self._clone_single_repository(repo)
            if success:
                successful.append(repo.full_name)
            else:
                failed.append(repo.full_name)
            
        
        return successful, failed
    
    def _clone_single_repository(self, repo: Repository) -> bool:
        """
        Clone a single repository.
        
        Args:
            repo: Repository to clone
            
        Returns:
            True if successful, False otherwise
        """
        repo_path = self.clone_dir / repo.name
        
        # Skip if already exists
        if repo_path.exists():
            print(f"\nSkipping {repo.name}: already exists")
            return True
        
        try:
            result = subprocess.run(
                ["git", "clone", repo.html_url, str(repo_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                return True
            else:
                print(f"\nError cloning {repo.name}: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"\nTimeout cloning {repo.name}")
            return False
        except Exception as e:
            print(f"\nUnexpected error cloning {repo.name}: {e}")
            return False


def parse_ranges(range_string: str, max_value: int) -> Set[int]:
    """
    Parse range string into set of indices.
    
    Args:
        range_string: String like "1-5,10,15-20"
        max_value: Maximum valid index
        
    Returns:
        Set of indices (1-based)
        
    Example:
        >>> parse_ranges("1-3,5", 10)
        {1, 2, 3, 5}
    """
    indices = set()
    
    for part in range_string.split(","):
        part = part.strip()
        if not part:
            continue
        
        if "-" in part:
            try:
                start, end = map(int, part.split("-", 1))
                # Ensure valid range
                start = max(1, min(start, max_value))
                end = max(1, min(end, max_value))
                if start <= end:
                    indices.update(range(start, end + 1))
            except ValueError:
                print(f"Invalid range: {part}")
        else:
            try:
                idx = int(part)
                if 1 <= idx <= max_value:
                    indices.add(idx)
            except ValueError:
                print(f"Invalid index: {part}")
    
    return indices
