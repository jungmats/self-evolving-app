#!/usr/bin/env python3
"""
Workflow Orchestration Scripts

This module provides Python scripts that handle state transitions, Issue comment creation
for workflow progress, and workflow run correlation with Trace_ID.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from github_client import GitHubClient, GitHubClientError
from state_management import IssueStateManager, Stage, StateTransitionError


class WorkflowOrchestrator:
    """
    Orchestrates workflow state transitions and progress tracking.
    
    Handles state transitions, audit trail creation, and workflow run correlation
    with Trace_ID for the self-evolving app workflow system.
    """
    
    def __init__(self, github_token: Optional[str] = None, repository: Optional[str] = None):
        """
        Initialize workflow orchestrator.
        
        Args:
            github_token: GitHub Personal Access Token
            repository: Repository name in format "owner/repo"
        """
        self.github_client = GitHubClient(
            token=github_token or os.getenv("GITHUB_TOKEN"),
            repository=repository or os.getenv("GITHUB_REPOSITORY")
        )
        self.state_manager = IssueStateManager(self.github_client)
    
    def extract_trace_id_from_issue(self, issue_number: int) -> Optional[str]:
        """
        Extract Trace_ID from Issue body.
        
        Args:
            issue_number: GitHub Issue number
            
        Returns:
            Trace_ID if found, None otherwise
        """
        try:
            issue = self.github_client.get_issue(issue_number)
            body = issue.body or ""
            
            # Look for Trace_ID pattern: **Trace_ID**: `trace-...`
            import re
            trace_pattern = r'\*\*Trace_ID\*\*:\s*`([^`]+)`'
            match = re.search(trace_pattern, body)
            
            if match:
                return match.group(1)
            
            # Fallback: look for any trace- pattern
            fallback_pattern = r'trace-[a-zA-Z0-9\-_]+'
            match = re.search(fallback_pattern, body)
            
            if match:
                return match.group(0)
            
            return None
            
        except GitHubClientError as e:
            print(f"Error extracting Trace_ID from Issue #{issue_number}: {e}")
            return None
    
    def add_workflow_progress_comment(
        self,
        issue_number: int,
        workflow_name: str,
        status: str,
        details: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> None:
        """
        Add workflow progress comment to Issue for audit trail.
        
        Args:
            issue_number: GitHub Issue number
            workflow_name: Name of the workflow (triage, plan, prioritize, etc.)
            status: Workflow status (started, completed, failed, blocked)
            details: Additional details about the workflow execution
            trace_id: Trace_ID for correlation
        """
        # Extract trace_id from issue if not provided
        if not trace_id:
            trace_id = self.extract_trace_id_from_issue(issue_number)
        
        # Build status emoji
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
        
        # Add workflow run correlation if available
        workflow_run_id = os.getenv("GITHUB_RUN_ID")
        workflow_run_url = os.getenv("GITHUB_SERVER_URL")
        repository = os.getenv("GITHUB_REPOSITORY")
        
        if workflow_run_id and workflow_run_url and repository:
            run_url = f"{workflow_run_url}/{repository}/actions/runs/{workflow_run_id}"
            comment_lines.extend([
                "",
                f"**Workflow Run**: [{workflow_run_id}]({run_url})"
            ])
        
        comment = "\n".join(comment_lines)
        
        try:
            self.github_client.add_issue_comment(issue_number, comment)
            print(f"Added workflow progress comment to Issue #{issue_number}")
        except GitHubClientError as e:
            print(f"Error adding workflow progress comment: {e}")
            raise
    
    def transition_issue_stage(
        self,
        issue_number: int,
        target_stage: str,
        reason: str,
        workflow_name: Optional[str] = None
    ) -> bool:
        """
        Transition Issue to a new stage with proper validation and audit trail.
        
        Args:
            issue_number: GitHub Issue number
            target_stage: Target stage name (e.g., "stage:plan")
            reason: Reason for the transition
            workflow_name: Name of the workflow triggering the transition
            
        Returns:
            True if transition succeeded, False otherwise
        """
        try:
            # Extract trace_id from issue
            trace_id = self.extract_trace_id_from_issue(issue_number)
            if not trace_id:
                print(f"Warning: Could not extract Trace_ID from Issue #{issue_number}")
                trace_id = f"workflow-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            # Convert stage string to Stage enum
            target_stage_enum = None
            for stage in Stage:
                if stage.value == target_stage:
                    target_stage_enum = stage
                    break
            
            if not target_stage_enum:
                raise ValueError(f"Invalid stage: {target_stage}")
            
            # Perform the transition
            self.state_manager.transition_issue_state(
                issue_number=issue_number,
                new_stage=target_stage_enum,
                reason=reason,
                trace_id=trace_id
            )
            
            # Add workflow progress comment if workflow name provided
            if workflow_name:
                self.add_workflow_progress_comment(
                    issue_number=issue_number,
                    workflow_name=workflow_name,
                    status="completed",
                    details=f"Transitioned to {target_stage}",
                    trace_id=trace_id
                )
            
            print(f"Successfully transitioned Issue #{issue_number} to {target_stage}")
            return True
            
        except (StateTransitionError, ValueError, GitHubClientError) as e:
            print(f"Error transitioning Issue #{issue_number} to {target_stage}: {e}")
            
            # Add failure comment if workflow name provided
            if workflow_name:
                try:
                    trace_id = self.extract_trace_id_from_issue(issue_number) or "unknown"
                    self.add_workflow_progress_comment(
                        issue_number=issue_number,
                        workflow_name=workflow_name,
                        status="failed",
                        details=f"Failed to transition to {target_stage}: {str(e)}",
                        trace_id=trace_id
                    )
                except Exception:
                    pass  # Don't fail if we can't add the comment
            
            return False
    
    def handle_workflow_completion(
        self,
        issue_number: int,
        workflow_name: str,
        success: bool,
        next_stage: Optional[str] = None,
        details: Optional[str] = None
    ) -> bool:
        """
        Handle workflow completion with appropriate state transition.
        
        Args:
            issue_number: GitHub Issue number
            workflow_name: Name of the completed workflow
            success: Whether the workflow completed successfully
            next_stage: Next stage to transition to if successful
            details: Additional details about the workflow execution
            
        Returns:
            True if handling succeeded, False otherwise
        """
        try:
            trace_id = self.extract_trace_id_from_issue(issue_number)
            
            if success and next_stage:
                # Successful completion - transition to next stage
                reason = f"{workflow_name.title()} workflow completed successfully"
                if details:
                    reason += f": {details}"
                
                return self.transition_issue_stage(
                    issue_number=issue_number,
                    target_stage=next_stage,
                    reason=reason,
                    workflow_name=workflow_name
                )
            
            elif not success:
                # Failed workflow - transition to blocked
                reason = f"{workflow_name.title()} workflow failed"
                if details:
                    reason += f": {details}"
                
                return self.transition_issue_stage(
                    issue_number=issue_number,
                    target_stage="stage:blocked",
                    reason=reason,
                    workflow_name=workflow_name
                )
            
            else:
                # Just add progress comment without transition
                status = "completed" if success else "failed"
                self.add_workflow_progress_comment(
                    issue_number=issue_number,
                    workflow_name=workflow_name,
                    status=status,
                    details=details,
                    trace_id=trace_id
                )
                return True
                
        except Exception as e:
            print(f"Error handling workflow completion: {e}")
            return False


def main():
    """Main entry point for workflow orchestration script."""
    parser = argparse.ArgumentParser(description="Workflow Orchestration Script")
    parser.add_argument("command", choices=["transition", "progress", "complete"], 
                       help="Command to execute")
    parser.add_argument("--issue-id", type=int, required=True,
                       help="GitHub Issue number")
    parser.add_argument("--workflow", required=True,
                       help="Workflow name (triage, plan, prioritize, implement)")
    parser.add_argument("--stage", 
                       help="Target stage for transition command")
    parser.add_argument("--status", choices=["started", "completed", "failed", "blocked"],
                       help="Status for progress command")
    parser.add_argument("--success", action="store_true",
                       help="Whether workflow completed successfully (for complete command)")
    parser.add_argument("--next-stage",
                       help="Next stage to transition to on successful completion")
    parser.add_argument("--reason",
                       help="Reason for the transition")
    parser.add_argument("--details",
                       help="Additional details about the workflow execution")
    
    args = parser.parse_args()
    
    try:
        orchestrator = WorkflowOrchestrator()
        
        if args.command == "transition":
            if not args.stage or not args.reason:
                print("Error: --stage and --reason are required for transition command")
                sys.exit(1)
            
            success = orchestrator.transition_issue_stage(
                issue_number=args.issue_id,
                target_stage=args.stage,
                reason=args.reason,
                workflow_name=args.workflow
            )
            
            sys.exit(0 if success else 1)
        
        elif args.command == "progress":
            if not args.status:
                print("Error: --status is required for progress command")
                sys.exit(1)
            
            orchestrator.add_workflow_progress_comment(
                issue_number=args.issue_id,
                workflow_name=args.workflow,
                status=args.status,
                details=args.details
            )
            
            sys.exit(0)
        
        elif args.command == "complete":
            success = orchestrator.handle_workflow_completion(
                issue_number=args.issue_id,
                workflow_name=args.workflow,
                success=args.success,
                next_stage=args.next_stage,
                details=args.details
            )
            
            sys.exit(0 if success else 1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()