#!/usr/bin/env python3
"""
GitHub Environment Setup Script

This script configures the 'production' environment in the GitHub repository
without required reviewers, as specified in the requirements.
"""

import os
import sys
import json
import requests

class GitHubEnvironmentManager:
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "self-evolving-app-setup"
        }
        self.base_url = f"https://api.github.com/repos/{repo}"
    
    def get_environments(self):
        """Get all environments for the repository."""
        url = f"{self.base_url}/environments"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching environments: {response.status_code} - {response.text}")
            return None
    
    def create_production_environment(self):
        """Create or update the production environment."""
        url = f"{self.base_url}/environments/production"
        
        # Environment configuration without required reviewers
        environment_config = {
            "wait_timer": 0,
            "reviewers": [],
            "deployment_branch_policy": {
                "protected_branches": True,
                "custom_branch_policies": False
            }
        }
        
        response = requests.put(url, headers=self.headers, json=environment_config)
        
        if response.status_code in [200, 201]:
            print("✓ Production environment configured successfully")
            return True
        else:
            print(f"✗ Error configuring production environment: {response.status_code} - {response.text}")
            return False
    
    def setup_environment_secrets_placeholders(self):
        """Document required secrets for the production environment."""
        secrets_info = {
            "required_secrets": [
                {
                    "name": "GITHUB_TOKEN",
                    "description": "GitHub Personal Access Token for API access",
                    "required_for": ["all workflows"]
                },
                {
                    "name": "DEPLOYMENT_SECRET",
                    "description": "Secret for deployment authentication",
                    "required_for": ["deployment"]
                }
            ],
            "repository_secrets": [
                {
                    "name": "GITHUB_TOKEN",
                    "description": "Automatically provided by GitHub Actions",
                    "note": "No manual configuration required"
                }
            ]
        }
        
        print("\n📋 Required Secrets Configuration:")
        print("=" * 50)
        
        for secret in secrets_info["required_secrets"]:
            print(f"Secret: {secret['name']}")
            print(f"  Description: {secret['description']}")
            print(f"  Required for: {', '.join(secret['required_for'])}")
            print()
        
        print("Repository Secrets (automatic):")
        for secret in secrets_info["repository_secrets"]:
            print(f"Secret: {secret['name']}")
            print(f"  Description: {secret['description']}")
            if "note" in secret:
                print(f"  Note: {secret['note']}")
            print()
        
        return True

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
    
    manager = GitHubEnvironmentManager(token, repo)
    
    print(f"Setting up GitHub environment for repository: {repo}")
    
    success = True
    
    # Create production environment
    if not manager.create_production_environment():
        success = False
    
    # Document required secrets
    if not manager.setup_environment_secrets_placeholders():
        success = False
    
    if success:
        print("\n✓ GitHub environment setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure the required secrets in your repository settings")
        print("2. Ensure your repository has a 'main' branch protection rule")
        print("3. Test the workflows by creating an issue with appropriate labels")
        sys.exit(0)
    else:
        print("\n✗ Some environment setup steps failed")
        sys.exit(1)

if __name__ == "__main__":
    main()