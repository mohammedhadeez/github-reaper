"""Tests for GitHub Reaper application."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from config import Config
from models import Repository, SearchResult
from github_client import GitHubClient
from repository_cloner import RepositoryCloner, parse_ranges


@pytest.fixture
def config():
    """Create test configuration."""
    return Config(github_token="test_token")


@pytest.fixture
def sample_repository():
    """Create sample repository."""
    return Repository(
        id=1,
        name="test-repo",
        full_name="user/test-repo",
        html_url="https://github.com/user/test-repo",
        description="Test repository",
        language="Python",
        stargazers_count=42
    )


class TestConfig:
    """Test configuration management."""
    
    def test_config_from_env_missing_token(self):
        """Test config creation fails without token."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GITHUB_TOKEN not found"):
                Config.from_env()
    
    def test_config_headers(self, config):
        """Test header generation."""
        headers = config.headers
        assert headers["Authorization"] == "token test_token"
        assert headers["Accept"] == "application/vnd.github.v3+json"


class TestModels:
    """Test data models."""
    
    def test_repository_from_api_response(self):
        """Test creating repository from API response."""
        api_data = {
            "id": 123,
            "name": "awesome-project",
            "full_name": "user/awesome-project",
            "html_url": "https://github.com/user/awesome-project",
            "description": "An awesome project",
            "language": "Python",
            "stargazers_count": 1000
        }
        
        repo = Repository.from_api_response(api_data)
        assert repo.id == 123
        assert repo.name == "awesome-project"
        assert repo.stargazers_count == 1000


class TestGitHubClient:
    """Test GitHub API client."""
    
    def test_search_repositories_empty_query(self, config):
        """Test search with empty query raises error."""
        client = GitHubClient(config)
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            client.search_repositories("")
    
    @patch('requests.Session.get')
    def test_search_repositories_success(self, mock_get, config):
        """Test successful repository search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total_count": 2,
            "items": [
                {
                    "id": 1,
                    "name": "repo1",
                    "full_name": "user/repo1",
                    "html_url": "https://github.com/user/repo1",
                    "stargazers_count": 10
                },
                {
                    "id": 2,
                    "name": "repo2",
                    "full_name": "user/repo2",
                    "html_url": "https://github.com/user/repo2",
                    "stargazers_count": 20
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = GitHubClient(config)
        result = client.search_repositories("test")
        
        assert result.total_count == 2
        assert len(result.repositories) == 2
        assert result.repositories[0].name == "repo1"
        assert result.repositories[1].name == "repo2"


class TestRepositoryCloner:
    """Test repository cloning functionality."""
    
    def test_parse_ranges(self):
        """Test range parsing."""
        assert parse_ranges("1-3", 10) == {1, 2, 3}
        assert parse_ranges("1,5,10", 10) == {1, 5, 10}
        assert parse_ranges("1-3,5,7-9", 10) == {1, 2, 3, 5, 7, 8, 9}
        assert parse_ranges("15-20", 10) == set()  # Out of range
        assert parse_ranges("", 10) == set()
    
    @patch('subprocess.run')
    def test_clone_single_repository_success(self, mock_run, sample_repository):
        """Test successful repository cloning."""
        mock_run.return_value = Mock(returncode=0)
        
        cloner = RepositoryCloner(Path("/tmp/test"))
        success = cloner._clone_single_repository(sample_repository)
        
        assert success is True
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_clone_single_repository_failure(self, mock_run, sample_repository):
        """Test failed repository cloning."""
        mock_run.return_value = Mock(
            returncode=1,
            stderr="Error: repository not found"
        )
        
        cloner = RepositoryCloner(Path("/tmp/test"))
        success = cloner._clone_single_repository(sample_repository)
        
        assert success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
