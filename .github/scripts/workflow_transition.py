#!/usr/bin/env python3
"""
Simple workflow transition script for GitHub Actions.

This script provides a simple interface for workflow state transitions
that can be easily called from GitHub Actions workflows.
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Optional


class SimpleWorkflowTransition:
    """Simple workflow transition handler using GitHub API directly."""
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repository = os.getenv("GITHUB_REPOSITORY")
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        if not self.repository:
            raise ValueError("GITHUB_REPOSITORY environment variable is required")
        
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "workflow-orchestrator"
        }
        self.base_url = f"https://api.github.com/repos/{self.repository}"
    
    def get_issue(self, issue_number: int) -> dict:
        """Get issue details from GitHub API."""
        url = f"{self.base_url}/issues/{issue_number}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get issue #{issue_number}: {response.status_code} - {response.text}")
    
    def add_issue_comment(self, issue_number: int, comment: str) -> None:
        """Add comment to issue."""
        url = f"{self.base_url}/issues/{issue_number}/comments"
        data = {"body": comment}
        
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code != 201:
            raise Exception(f"Failed to add comment to issue #{issue_number}: {response.status_code} - {response.text}")
    
    def set_issue_labels(self, issue_number: int, labels: list) -> None:
        """Set labels on issue (replaces existing labels)."""
        url = f"{self.base_url}/issues/{issue_number}/labels"
        data = {"labels": labels}
        
        response = requests.put(url, headers=self.headers, json=data)
        
        if response.status_code != 200:
            raise Exception(f"Failed to set labels on issue #{issue_number}: {response.status_code} - {response.text}")
    
    def remove_label_from_issue(self, issue_number: int, label: str) -> None:
        """Remove specific label from issue."""
        url = f"{self.base_url}/issues/{issue_number}/labels/{label}"
        response = requests.delete(url, headers=self.headers)
        
        # 200 = removed, 404 = label wasn't there (both OK)
        if response.status_code not in [200, 404]:
            raise Exception(f"Failed to remove label {label} from issue #{issue_number}: {response.status_code} - {response.text}")
    
    def add_label_to_issue(self, issue_number: int, labels: list) -> None:
        """Add labels to issue (keeps existing labels)."""
        url = f"{self.base_url}/issues/{issue_number}/labels"
        data = {"labels": labels}
        
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code != 200:
            raise Exception(f"Failed to add labels to issue #{issue_number}: {response.status_code} - {response.text}")
    
    def extract_trace_id(self, issue_body: str) -> Optional[str]:
        """Extract Trace_ID from issue body."""
        import re
        
        # Look for Trace_ID pattern: **Trace_ID**: `trace-...`
        trace_pattern = r'\*\*Trace_ID\*\*:\s*`([^`]+)`'
        match = re.search(trace_pattern, issue_body)
        
        if match:
            return match.group(1)
        
        # Fallback: look for any trace- pattern
        fallback_pattern = r'trace-[a-zA-Z0-9\-_]+'
        match = re.search(fallback_pattern, issue_body)
        
        if match:
            return match.group(0)
        
        return None
    
    def transition_stage(self, issue_number: int, from_stage: str, to_stage: str, workflow_name: str) -> bool:
        """
        Transition issue from one stage to another.
        
        Args:
            issue_number: GitHub issue number
            from_stage: Current stage label (e.g., "stage:triage")
            to_stage: Target stage label (e.g., "stage:plan")
            workflow_name: Name of the workflow performing the transition
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current issue
            issue = self.get_issue(issue_number)
            current_labels = [label["name"] for label in issue["labels"]]
            trace_id = self.extract_trace_id(issue["body"] or "")
            
            # Verify current stage
            if from_stage not in current_labels:
                print(f"Warning: Issue #{issue_number} is not in expected stage {from_stage}")
                print(f"Current labels: {current_labels}")
            
            # Remove old stage label first (if present)
            if from_stage in current_labels:
                self.remove_label_from_issue(issue_number, from_stage)
                print(f"Removed label: {from_stage}")
            
            # Add new stage label (this triggers the 'labeled' event)
            self.add_label_to_issue(issue_number, [to_stage])
            print(f"Added label: {to_stage}")
            
            # Add transition comment
            workflow_run_id = os.getenv("GITHUB_RUN_ID", "unknown")
            workflow_run_url = os.getenv("GITHUB_SERVER_URL", "")
            repository = os.getenv("GITHUB_REPOSITORY", "")
            
            comment_lines = [
                f"🔄 **State Transition**: {from_stage} → {to_stage}",
                "",
                f"**Workflow**: {workflow_name}",
                f"**Timestamp**: {datetime.utcnow().isoformat()}Z"
            ]
            
            if trace_id:
                comment_lines.append(f"**Trace_ID**: `{trace_id}`")
            
            if workflow_run_url and repository and workflow_run_id != "unknown":
                run_url = f"{workflow_run_url}/{repository}/actions/runs/{workflow_run_id}"
                comment_lines.append(f"**Workflow Run**: [{workflow_run_id}]({run_url})")
            
            comment = "\n".join(comment_lines)
            self.add_issue_comment(issue_number, comment)
            
            print(f"✅ Successfully transitioned issue #{issue_number} from {from_stage} to {to_stage}")
            return True
            
        except Exception as e:
            print(f"❌ Error transitioning issue #{issue_number}: {e}")
            
            # Try to add error comment
            try:
                error_comment = f"❌ **Workflow Error**\n\n**Workflow**: {workflow_name}\n**Error**: Failed to transition from {from_stage} to {to_stage}\n**Details**: {str(e)}\n**Timestamp**: {datetime.utcnow().isoformat()}Z"
                self.add_issue_comment(issue_number, error_comment)
            except:
                pass  # Don't fail if we can't add error comment
            
            return False
    
    def add_progress_comment(self, issue_number: int, workflow_name: str, status: str, details: str = "") -> bool:
        """
        Add workflow progress comment to issue.
        
        Args:
            issue_number: GitHub issue number
            workflow_name: Name of the workflow
            status: Status (started, completed, failed, blocked)
            details: Additional details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get trace_id from issue
            issue = self.get_issue(issue_number)
            trace_id = self.extract_trace_id(issue["body"] or "")
            
            # Status emojis
            status_emojis = {
                "started": "🚀",
                "completed": "✅", 
                "failed": "❌",
                "blocked": "🚫"
            }
            emoji = status_emojis.get(status, "ℹ️")
            
            # Build comment
            comment_lines = [
                f"{emoji} **{workflow_name.title()} Workflow {status.title()}**",
                "",
                f"**Status**: {status}",
                f"**Timestamp**: {datetime.utcnow().isoformat()}Z"
            ]
            
            if trace_id:
                comment_lines.append(f"**Trace_ID**: `{trace_id}`")
            
            if details:
                comment_lines.extend(["", "**Details**:", details])
            
            # Add workflow run info
            workflow_run_id = os.getenv("GITHUB_RUN_ID")
            workflow_run_url = os.getenv("GITHUB_SERVER_URL")
            repository = os.getenv("GITHUB_REPOSITORY")
            
            if workflow_run_id and workflow_run_url and repository:
                run_url = f"{workflow_run_url}/{repository}/actions/runs/{workflow_run_id}"
                comment_lines.append(f"**Workflow Run**: [{workflow_run_id}]({run_url})")
            
            comment = "\n".join(comment_lines)
            self.add_issue_comment(issue_number, comment)
            
            print(f"✅ Added progress comment to issue #{issue_number}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding progress comment to issue #{issue_number}: {e}")
            return False


def main():
    """Main entry point for simple workflow transition script."""
    if len(sys.argv) < 2:
        print("Usage: python workflow_transition.py <command> [args...]")
        print("Commands:")
        print("  transition <issue_id> <from_stage> <to_stage> <workflow_name>")
        print("  progress <issue_id> <workflow_name> <status> [details]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        transition = SimpleWorkflowTransition()
        
        if command == "transition":
            if len(sys.argv) < 6:
                print("Usage: transition <issue_id> <from_stage> <to_stage> <workflow_name>")
                sys.exit(1)
            
            issue_id = int(sys.argv[2])
            from_stage = sys.argv[3]
            to_stage = sys.argv[4]
            workflow_name = sys.argv[5]
            
            success = transition.transition_stage(issue_id, from_stage, to_stage, workflow_name)
            sys.exit(0 if success else 1)
        
        elif command == "progress":
            if len(sys.argv) < 5:
                print("Usage: progress <issue_id> <workflow_name> <status> [details]")
                sys.exit(1)
            
            issue_id = int(sys.argv[2])
            workflow_name = sys.argv[3]
            status = sys.argv[4]
            details = sys.argv[5] if len(sys.argv) > 5 else ""
            
            success = transition.add_progress_comment(issue_id, workflow_name, status, details)
            sys.exit(0 if success else 1)
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()