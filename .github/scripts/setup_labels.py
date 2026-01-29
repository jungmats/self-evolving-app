#!/usr/bin/env python3
"""
GitHub Labels Setup Script

This script ensures all required labels exist in the repository for the self-evolving app workflow.
Labels are organized by category: stage, request, source, priority, and agent.
"""

import os
import sys
import json
from typing import List, Dict, Any
import requests

# Required labels for the self-evolving app workflow
REQUIRED_LABELS = [
    # Stage labels - workflow state machine
    {"name": "stage:triage", "color": "0052cc", "description": "Issue is in triage stage"},
    {"name": "stage:plan", "color": "1d76db", "description": "Issue is in planning stage"},
    {"name": "stage:prioritize", "color": "5319e7", "description": "Issue is in prioritization stage"},
    {"name": "stage:awaiting-implementation-approval", "color": "fbca04", "description": "Issue awaits implementation approval"},
    {"name": "stage:implement", "color": "0e8a16", "description": "Issue is in implementation stage"},
    {"name": "stage:pr-opened", "color": "28a745", "description": "Pull request has been opened"},
    {"name": "stage:awaiting-deploy-approval", "color": "f9d0c4", "description": "Issue awaits deployment approval"},
    {"name": "stage:blocked", "color": "d93f0b", "description": "Issue is blocked and requires intervention"},
    {"name": "stage:done", "color": "6f42c1", "description": "Issue is completed"},
    
    # Request type labels
    {"name": "request:bug", "color": "d73a4a", "description": "Bug report submission"},
    {"name": "request:feature", "color": "a2eeef", "description": "Feature request submission"},
    {"name": "request:investigate", "color": "fef2c0", "description": "Investigation request from monitoring"},
    
    # Source labels - origin of the request
    {"name": "source:user", "color": "c2e0c6", "description": "Request originated from user submission"},
    {"name": "source:monitor", "color": "f9c513", "description": "Request originated from automated monitoring"},
    
    # Priority labels
    {"name": "priority:p0", "color": "b60205", "description": "Critical priority - immediate attention required"},
    {"name": "priority:p1", "color": "d93f0b", "description": "High priority - should be addressed soon"},
    {"name": "priority:p2", "color": "fbca04", "description": "Normal priority - can be scheduled"},
    
    # Agent labels - identifies automated actions
    {"name": "agent:claude", "color": "e99695", "description": "Created or modified by Claude workflows"},
]

class GitHubLabelsManager:
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "self-evolving-app-setup"
        }
        self.base_url = f"https://api.github.com/repos/{repo}"
    
    def get_existing_labels(self) -> List[Dict[str, Any]]:
        """Fetch all existing labels from the repository."""
        url = f"{self.base_url}/labels"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching labels: {response.status_code} - {response.text}")
            return []
    
    def create_label(self, label: Dict[str, str]) -> bool:
        """Create a new label in the repository."""
        url = f"{self.base_url}/labels"
        response = requests.post(url, headers=self.headers, json=label)
        
        if response.status_code == 201:
            print(f"✓ Created label: {label['name']}")
            return True
        elif response.status_code == 422:
            # Label already exists, try to update it
            return self.update_label(label)
        else:
            print(f"✗ Error creating label {label['name']}: {response.status_code} - {response.text}")
            return False
    
    def update_label(self, label: Dict[str, str]) -> bool:
        """Update an existing label in the repository."""
        url = f"{self.base_url}/labels/{label['name']}"
        response = requests.patch(url, headers=self.headers, json=label)
        
        if response.status_code == 200:
            print(f"✓ Updated label: {label['name']}")
            return True
        else:
            print(f"✗ Error updating label {label['name']}: {response.status_code} - {response.text}")
            return False
    
    def setup_all_labels(self) -> bool:
        """Ensure all required labels exist in the repository."""
        print(f"Setting up labels for repository: {self.repo}")
        
        existing_labels = self.get_existing_labels()
        existing_names = {label['name'] for label in existing_labels}
        
        success = True
        for label in REQUIRED_LABELS:
            if label['name'] not in existing_names:
                if not self.create_label(label):
                    success = False
            else:
                print(f"• Label already exists: {label['name']}")
        
        return success

def main():
    # Get GitHub token and repository from environment
    token = os.getenv('GITHUB_TOKEN')
    repo = os.getenv('GITHUB_REPOSITORY')
    
    if not token:
        print("Error: GITHUB_TOKEN environment variable is required")
        sys.exit(1)
    
    if not repo:
        print("Error: GITHUB_REPOSITORY environment variable is required")
        print("Format: owner/repository-name")
        sys.exit(1)
    
    manager = GitHubLabelsManager(token, repo)
    
    if manager.setup_all_labels():
        print("\n✓ All labels configured successfully!")
        sys.exit(0)
    else:
        print("\n✗ Some labels failed to configure")
        sys.exit(1)

if __name__ == "__main__":
    main()