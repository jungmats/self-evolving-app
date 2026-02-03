"""
Unit tests for Pull Request creation and management.

Validates Requirements 9.1, 9.2, 9.3, 9.4, 9.5
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from app.github_client import GitHubClient, GitHubClientError


class TestPullRequestCreation:
    """Tests for Pull Request creation functionality."""
    
    def test_create_pull_request_with_trace_id(self):
        """
        Test that PR creation includes Trace_ID in body.
        
        Validates: Requirement 9.2
        """
        # Mock GitHub client
        with patch('app.github_client.Github') as mock_github:
            mock_repo = MagicMock()
            mock_pr = MagicMock()
            mock_pr.number = 42
            mock_pr.html_url = "https://github.com/owner/repo/pull/42"
            
            mock_repo.create_pull.return_value = mock_pr
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Create client
            client = GitHubClient(token="test_token", repository="owner/repo")
            
            # Create PR with Trace_ID in body
            trace_id = "trace-test-123"
            pr_body = f"Fixes #10\n\n**Trace_ID**: `{trace_id}`"
            
            pr = client.create_pull_request(
                title="Test PR",
                body=pr_body,
                head="feature-branch",
                base="main",
                labels=["agent:claude"]
            )
            
            # Verify PR was created with correct parameters
            mock_repo.create_pull.assert_called_once()
            call_args = mock_repo.create_pull.call_args
            
            assert call_args[1]["title"] == "Test PR"
            assert trace_id in call_args[1]["body"]
            assert call_args[1]["head"] == "feature-branch"
            assert call_args[1]["base"] == "main"
    
    def test_create_pull_request_with_issue_reference(self):
        """
        Test that PR body includes proper Issue reference.
        
        Validates: Requirement 9.3
        """
        # Mock GitHub client
        with patch('app.github_client.Github') as mock_github:
            mock_repo = MagicMock()
            mock_pr = MagicMock()
            mock_pr.number = 42
            
            mock_repo.create_pull.return_value = mock_pr
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Create client
            client = GitHubClient(token="test_token", repository="owner/repo")
            
            # Create PR with Issue reference
            issue_number = 10
            pr_body = f"Fixes #{issue_number}\n\nImplementation details..."
            
            pr = client.create_pull_request(
                title="Test PR",
                body=pr_body,
                head="feature-branch",
                base="main"
            )
            
            # Verify Issue reference is in body
            call_args = mock_repo.create_pull.call_args
            assert f"Fixes #{issue_number}" in call_args[1]["body"]
    
    def test_create_pull_request_with_agent_label(self):
        """
        Test that PR is labeled with agent:claude.
        
        Validates: Requirement 9.4
        """
        # Mock GitHub client
        with patch('app.github_client.Github') as mock_github:
            mock_repo = MagicMock()
            mock_pr = MagicMock()
            mock_pr.number = 42
            
            mock_repo.create_pull.return_value = mock_pr
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Create client
            client = GitHubClient(token="test_token", repository="owner/repo")
            
            # Create PR with agent label
            pr = client.create_pull_request(
                title="Test PR",
                body="Test body",
                head="feature-branch",
                base="main",
                labels=["agent:claude"]
            )
            
            # Verify agent label was added
            mock_pr.add_to_labels.assert_called_once_with("agent:claude")
    
    def test_get_linked_issue_from_pr_with_fixes(self):
        """
        Test extracting linked issue from PR body using Fixes keyword.
        
        Validates: Requirement 9.3
        """
        # Mock GitHub client
        with patch('app.github_client.Github') as mock_github:
            mock_repo = MagicMock()
            mock_pr = MagicMock()
            mock_pr.number = 42
            mock_pr.body = "Fixes #123\n\nImplementation details..."
            
            mock_repo.get_pull.return_value = mock_pr
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Create client
            client = GitHubClient(token="test_token", repository="owner/repo")
            
            # Extract linked issue
            issue_number = client.get_linked_issue_from_pr(42)
            
            assert issue_number == 123
    
    def test_get_linked_issue_from_pr_with_refs(self):
        """
        Test extracting linked issue from PR body using Refs keyword.
        
        Validates: Requirement 9.3
        """
        # Mock GitHub client
        with patch('app.github_client.Github') as mock_github:
            mock_repo = MagicMock()
            mock_pr = MagicMock()
            mock_pr.number = 42
            mock_pr.body = "Refs #456\n\nRelated changes..."
            
            mock_repo.get_pull.return_value = mock_pr
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Create client
            client = GitHubClient(token="test_token", repository="owner/repo")
            
            # Extract linked issue
            issue_number = client.get_linked_issue_from_pr(42)
            
            assert issue_number == 456
    
    def test_get_linked_issue_from_pr_no_reference(self):
        """
        Test that None is returned when no issue reference exists.
        """
        # Mock GitHub client
        with patch('app.github_client.Github') as mock_github:
            mock_repo = MagicMock()
            mock_pr = MagicMock()
            mock_pr.number = 42
            mock_pr.body = "No issue reference here"
            
            mock_repo.get_pull.return_value = mock_pr
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Create client
            client = GitHubClient(token="test_token", repository="owner/repo")
            
            # Extract linked issue
            issue_number = client.get_linked_issue_from_pr(42)
            
            assert issue_number is None
    
    def test_is_pull_request_merged(self):
        """
        Test checking if a PR has been merged.
        
        Validates: Requirement 9.5
        """
        # Mock GitHub client
        with patch('app.github_client.Github') as mock_github:
            mock_repo = MagicMock()
            mock_pr = MagicMock()
            mock_pr.number = 42
            mock_pr.merged = True
            
            mock_repo.get_pull.return_value = mock_pr
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Create client
            client = GitHubClient(token="test_token", repository="owner/repo")
            
            # Check merge status
            is_merged = client.is_pull_request_merged(42)
            
            assert is_merged is True
    
    def test_is_pull_request_not_merged(self):
        """
        Test checking if a PR has not been merged.
        """
        # Mock GitHub client
        with patch('app.github_client.Github') as mock_github:
            mock_repo = MagicMock()
            mock_pr = MagicMock()
            mock_pr.number = 42
            mock_pr.merged = False
            
            mock_repo.get_pull.return_value = mock_pr
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Create client
            client = GitHubClient(token="test_token", repository="owner/repo")
            
            # Check merge status
            is_merged = client.is_pull_request_merged(42)
            
            assert is_merged is False


class TestPullRequestManagement:
    """Tests for Pull Request management functionality."""
    
    def test_add_labels_to_pull_request(self):
        """
        Test adding labels to an existing PR.
        """
        # Mock GitHub client
        with patch('app.github_client.Github') as mock_github:
            mock_repo = MagicMock()
            mock_pr = MagicMock()
            mock_issue = MagicMock()
            
            mock_repo.get_pull.return_value = mock_pr
            mock_repo.get_issue.return_value = mock_issue
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Create client
            client = GitHubClient(token="test_token", repository="owner/repo")
            
            # Add labels
            client.add_labels_to_pull_request(42, ["agent:claude", "priority:p1"])
            
            # Verify labels were added
            mock_issue.add_to_labels.assert_called_once_with("agent:claude", "priority:p1")
    
    def test_get_pull_request(self):
        """
        Test retrieving a PR by number.
        """
        # Mock GitHub client
        with patch('app.github_client.Github') as mock_github:
            mock_repo = MagicMock()
            mock_pr = MagicMock()
            mock_pr.number = 42
            mock_pr.title = "Test PR"
            
            mock_repo.get_pull.return_value = mock_pr
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Create client
            client = GitHubClient(token="test_token", repository="owner/repo")
            
            # Get PR
            pr = client.get_pull_request(42)
            
            assert pr.number == 42
            assert pr.title == "Test PR"
    
    def test_get_pull_request_not_found(self):
        """
        Test error handling when PR is not found.
        """
        # Mock GitHub client
        with patch('app.github_client.Github') as mock_github:
            from github import GithubException
            
            mock_repo = MagicMock()
            # GithubException requires status, data, and headers
            mock_repo.get_pull.side_effect = GithubException(404, {"message": "Not Found"}, {})
            mock_github.return_value.get_repo.return_value = mock_repo
            
            # Create client
            client = GitHubClient(token="test_token", repository="owner/repo")
            
            # Attempt to get non-existent PR
            with pytest.raises(GitHubClientError, match="Pull Request #999 not found"):
                client.get_pull_request(999)
