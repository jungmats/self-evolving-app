"""GitHub API client wrapper for the Self-Evolving Web Application."""

import os
import time
from typing import Optional, List, Dict, Any
from github import Github, GithubException
from github.Issue import Issue
from github.Repository import Repository
import logging

logger = logging.getLogger(__name__)


class GitHubClientError(Exception):
    """Custom exception for GitHub client errors."""
    pass


class GitHubClient:
    """
    Authenticated GitHub client with error handling and timeout management.
    
    Provides methods for Issue creation, label management, and state transitions
    with proper error handling and rate limiting.
    """
    
    def __init__(self, token: Optional[str] = None, repository: Optional[str] = None, timeout: int = 30):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub Personal Access Token (defaults to GITHUB_TOKEN env var)
            repository: Repository name in format "owner/repo" (defaults to GITHUB_REPOSITORY env var)
            timeout: Request timeout in seconds
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repository_name = repository or os.getenv("GITHUB_REPOSITORY")
        self.timeout = timeout
        
        if not self.token:
            raise GitHubClientError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        if not self.repository_name:
            raise GitHubClientError("Repository name is required. Set GITHUB_REPOSITORY environment variable.")
        
        try:
            self.github = Github(self.token, timeout=self.timeout)
            self.repository = self.github.get_repo(self.repository_name)
            
            # Validate permissions by attempting to read repository info
            _ = self.repository.name
            
        except GithubException as e:
            if e.status == 401:
                raise GitHubClientError("GitHub authentication failed. Check your token permissions.")
            elif e.status == 404:
                raise GitHubClientError(f"Repository '{self.repository_name}' not found or not accessible.")
            else:
                raise GitHubClientError(f"GitHub API error: {e.data.get('message', str(e))}")
        except Exception as e:
            raise GitHubClientError(f"Failed to initialize GitHub client: {str(e)}")
    
    def create_issue(
        self,
        title: str,
        body: str,
        labels: List[str],
        trace_id: str
    ) -> Issue:
        """
        Create a GitHub Issue with proper labeling and Trace_ID embedding.
        
        Args:
            title: Issue title
            body: Issue body content
            labels: List of label names to apply
            trace_id: Unique Trace_ID for linking
            
        Returns:
            Created GitHub Issue object
            
        Raises:
            GitHubClientError: If issue creation fails
        """
        try:
            # Embed Trace_ID in issue body
            enhanced_body = f"{body}\n\n---\n**Trace_ID**: `{trace_id}`"
            
            # Create the issue
            issue = self.repository.create_issue(
                title=title,
                body=enhanced_body,
                labels=labels
            )
            
            logger.info(f"Created GitHub Issue #{issue.number} with Trace_ID: {trace_id}")
            return issue
            
        except GithubException as e:
            error_msg = f"Failed to create GitHub Issue: {e.data.get('message', str(e))}"
            logger.error(f"{error_msg} (Trace_ID: {trace_id})")
            raise GitHubClientError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error creating GitHub Issue: {str(e)}"
            logger.error(f"{error_msg} (Trace_ID: {trace_id})")
            raise GitHubClientError(error_msg)
    
    def get_issue(self, issue_number: int) -> Issue:
        """
        Get a GitHub Issue by number.
        
        Args:
            issue_number: Issue number
            
        Returns:
            GitHub Issue object
            
        Raises:
            GitHubClientError: If issue retrieval fails
        """
        try:
            return self.repository.get_issue(issue_number)
        except GithubException as e:
            if e.status == 404:
                raise GitHubClientError(f"Issue #{issue_number} not found")
            else:
                raise GitHubClientError(f"Failed to get issue #{issue_number}: {e.data.get('message', str(e))}")
        except Exception as e:
            raise GitHubClientError(f"Unexpected error getting issue #{issue_number}: {str(e)}")
    
    def add_labels_to_issue(self, issue_number: int, labels: List[str]) -> None:
        """
        Add labels to an existing Issue.
        
        Args:
            issue_number: Issue number
            labels: List of label names to add
            
        Raises:
            GitHubClientError: If label addition fails
        """
        try:
            issue = self.get_issue(issue_number)
            issue.add_to_labels(*labels)
            logger.info(f"Added labels {labels} to Issue #{issue_number}")
        except GitHubClientError:
            raise
        except Exception as e:
            raise GitHubClientError(f"Failed to add labels to Issue #{issue_number}: {str(e)}")
    
    def set_issue_labels(self, issue_number: int, labels: List[str]) -> None:
        """
        Set labels on an Issue (replaces existing labels).
        
        Args:
            issue_number: Issue number
            labels: List of label names to set
            
        Raises:
            GitHubClientError: If label setting fails
        """
        try:
            issue = self.get_issue(issue_number)
            issue.set_labels(*labels)
            logger.info(f"Set labels {labels} on Issue #{issue_number}")
        except GitHubClientError:
            raise
        except Exception as e:
            raise GitHubClientError(f"Failed to set labels on Issue #{issue_number}: {str(e)}")
    
    def add_issue_comment(self, issue_number: int, comment: str) -> None:
        """
        Add a comment to an Issue for audit trail.
        
        Args:
            issue_number: Issue number
            comment: Comment text
            
        Raises:
            GitHubClientError: If comment addition fails
        """
        try:
            issue = self.get_issue(issue_number)
            issue.create_comment(comment)
            logger.info(f"Added comment to Issue #{issue_number}")
        except GitHubClientError:
            raise
        except Exception as e:
            raise GitHubClientError(f"Failed to add comment to Issue #{issue_number}: {str(e)}")
    
    def get_issue_comments(self, issue_number: int) -> List[Any]:
        """
        Get all comments for an Issue.
        
        Args:
            issue_number: Issue number
            
        Returns:
            List of comment objects
            
        Raises:
            GitHubClientError: If comment retrieval fails
        """
        try:
            issue = self.get_issue(issue_number)
            comments = list(issue.get_comments())
            logger.info(f"Retrieved {len(comments)} comments from Issue #{issue_number}")
            return comments
        except GitHubClientError:
            raise
        except Exception as e:
            raise GitHubClientError(f"Failed to get comments for Issue #{issue_number}: {str(e)}")
    
    def ensure_labels_exist(self, labels: List[Dict[str, str]]) -> None:
        """
        Ensure required labels exist in the repository.
        
        Args:
            labels: List of label dictionaries with 'name', 'color', and 'description'
            
        Raises:
            GitHubClientError: If label creation fails
        """
        try:
            existing_labels = {label.name for label in self.repository.get_labels()}
            
            for label_info in labels:
                if label_info['name'] not in existing_labels:
                    self.repository.create_label(
                        name=label_info['name'],
                        color=label_info['color'],
                        description=label_info.get('description', '')
                    )
                    logger.info(f"Created label: {label_info['name']}")
                    
        except GithubException as e:
            raise GitHubClientError(f"Failed to ensure labels exist: {e.data.get('message', str(e))}")
        except Exception as e:
            raise GitHubClientError(f"Unexpected error ensuring labels exist: {str(e)}")
    
    def validate_permissions(self) -> bool:
        """
        Validate that the client has necessary permissions.
        
        Returns:
            True if permissions are valid
            
        Raises:
            GitHubClientError: If permissions are insufficient
        """
        try:
            # Test repository access
            _ = self.repository.name
            
            # Test issue creation permissions by checking repository permissions
            permissions = self.repository.get_collaborator_permission(self.github.get_user().login)
            if permissions not in ['admin', 'write']:
                raise GitHubClientError("Insufficient permissions. Need 'write' or 'admin' access to create issues.")
            
            return True
            
        except GithubException as e:
            if e.status == 401:
                raise GitHubClientError("Authentication failed. Check your GitHub token.")
            elif e.status == 403:
                raise GitHubClientError("Insufficient permissions to access repository.")
            else:
                raise GitHubClientError(f"Permission validation failed: {e.data.get('message', str(e))}")
        except Exception as e:
            raise GitHubClientError(f"Unexpected error validating permissions: {str(e)}")


    def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        labels: Optional[List[str]] = None
    ) -> Any:
        """
        Create a Pull Request.
        
        Args:
            title: PR title
            body: PR body content
            head: Branch name to merge from
            base: Branch name to merge into (default: "main")
            labels: Optional list of label names to apply
            
        Returns:
            Created Pull Request object
            
        Raises:
            GitHubClientError: If PR creation fails
        """
        try:
            # Create the pull request
            pr = self.repository.create_pull(
                title=title,
                body=body,
                head=head,
                base=base
            )
            
            # Add labels if provided
            if labels:
                pr.add_to_labels(*labels)
            
            logger.info(f"Created Pull Request #{pr.number}: {title}")
            return pr
            
        except GithubException as e:
            error_msg = f"Failed to create Pull Request: {e.data.get('message', str(e))}"
            logger.error(error_msg)
            raise GitHubClientError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error creating Pull Request: {str(e)}"
            logger.error(error_msg)
            raise GitHubClientError(error_msg)
    
    def get_pull_request(self, pr_number: int) -> Any:
        """
        Get a Pull Request by number.
        
        Args:
            pr_number: Pull Request number
            
        Returns:
            Pull Request object
            
        Raises:
            GitHubClientError: If PR retrieval fails
        """
        try:
            return self.repository.get_pull(pr_number)
        except GithubException as e:
            if e.status == 404:
                raise GitHubClientError(f"Pull Request #{pr_number} not found")
            else:
                raise GitHubClientError(f"Failed to get PR #{pr_number}: {e.data.get('message', str(e))}")
        except Exception as e:
            raise GitHubClientError(f"Unexpected error getting PR #{pr_number}: {str(e)}")
    
    def add_labels_to_pull_request(self, pr_number: int, labels: List[str]) -> None:
        """
        Add labels to an existing Pull Request.
        
        Args:
            pr_number: Pull Request number
            labels: List of label names to add
            
        Raises:
            GitHubClientError: If label addition fails
        """
        try:
            pr = self.get_pull_request(pr_number)
            issue = self.repository.get_issue(pr_number)  # PRs are also issues
            issue.add_to_labels(*labels)
            logger.info(f"Added labels {labels} to PR #{pr_number}")
        except GitHubClientError:
            raise
        except Exception as e:
            raise GitHubClientError(f"Failed to add labels to PR #{pr_number}: {str(e)}")
    
    def is_pull_request_merged(self, pr_number: int) -> bool:
        """
        Check if a Pull Request has been merged.
        
        Args:
            pr_number: Pull Request number
            
        Returns:
            True if PR is merged, False otherwise
            
        Raises:
            GitHubClientError: If PR status check fails
        """
        try:
            pr = self.get_pull_request(pr_number)
            return pr.merged
        except GitHubClientError:
            raise
        except Exception as e:
            raise GitHubClientError(f"Failed to check PR merge status #{pr_number}: {str(e)}")
    
    def get_linked_issue_from_pr(self, pr_number: int) -> Optional[int]:
        """
        Extract linked issue number from PR body.
        
        Args:
            pr_number: Pull Request number
            
        Returns:
            Issue number if found, None otherwise
            
        Raises:
            GitHubClientError: If PR retrieval fails
        """
        try:
            import re
            
            pr = self.get_pull_request(pr_number)
            pr_body = pr.body or ""
            
            # Look for "Fixes #123" or "Refs #123" pattern
            pattern = r'(Fixes|Refs)\s+#(\d+)'
            match = re.search(pattern, pr_body, re.IGNORECASE)
            
            if match:
                issue_number = int(match.group(2))
                logger.info(f"Found linked issue #{issue_number} in PR #{pr_number}")
                return issue_number
            
            return None
        except GitHubClientError:
            raise
        except Exception as e:
            raise GitHubClientError(f"Failed to extract linked issue from PR #{pr_number}: {str(e)}")


def get_github_client() -> GitHubClient:
    """
    Factory function to create a configured GitHub client.
    
    Returns:
        Configured GitHubClient instance
        
    Raises:
        GitHubClientError: If client creation fails
    """
    return GitHubClient()