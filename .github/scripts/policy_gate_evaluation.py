#!/usr/bin/env python3
"""
Policy Gate Evaluation Script for GitHub Actions Workflows

This script provides policy evaluation functionality that can be called from
GitHub Actions workflows to determine whether workflow stages should proceed.
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

from policy_gate import PolicyGateComponent
from models import StageContext, ChangeContext
from github_client import GitHubClient, GitHubClientError
from database import SessionLocal


class PolicyGateEvaluator:
    """
    Policy Gate Evaluator for GitHub Actions integration.
    
    Provides policy evaluation functionality that can be called from GitHub Actions
    workflows to determine whether workflow stages should proceed.
    """
    
    def __init__(self, github_token: Optional[str] = None, repository: Optional[str] = None):
        """
        Initialize policy gate evaluator.
        
        Args:
            github_token: GitHub Personal Access Token
            repository: Repository name in format "owner/repo"
        """
        self.github_client = GitHubClient(
            token=github_token or os.getenv("GITHUB_TOKEN"),
            repository=repository or os.getenv("GITHUB_REPOSITORY")
        )
        
        # Create database session for policy component
        self.db_session = SessionLocal()
        self.policy_component = PolicyGateComponent(self.db_session)
    
    def __del__(self):
        """Clean up database session."""
        if hasattr(self, 'db_session'):
            self.db_session.close()
    
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
    
    def extract_request_info_from_issue(self, issue_number: int) -> Dict[str, Any]:
        """
        Extract request information from GitHub Issue.
        
        Args:
            issue_number: GitHub Issue number
            
        Returns:
            Dictionary with request information
        """
        try:
            issue = self.github_client.get_issue(issue_number)
            
            # Determine request type from labels
            request_type = "bug"  # default
            source = "user"  # default
            priority = None
            severity = None
            
            for label in issue.labels:
                label_name = label.name
                if label_name.startswith("request:"):
                    request_type = label_name.split(":", 1)[1]
                elif label_name.startswith("source:"):
                    source = label_name.split(":", 1)[1]
                elif label_name.startswith("priority:"):
                    priority = label_name.split(":", 1)[1]
                elif label_name.startswith("severity:"):
                    severity = label_name.split(":", 1)[1]
            
            # Extract workflow artifacts from comments
            workflow_artifacts = []
            try:
                comments = self.github_client.get_issue_comments(issue_number)
                for comment in comments:
                    comment_body = comment.body or ""
                    if "Triage Workflow Completed" in comment_body:
                        workflow_artifacts.append("triage_report")
                    elif "Planning Workflow Completed" in comment_body:
                        workflow_artifacts.append("implementation_plan")
                    elif "Prioritization Workflow Completed" in comment_body:
                        workflow_artifacts.append("priority_assessment")
                    elif "Implementation approved" in comment_body.lower():
                        workflow_artifacts.append("human_approval")
            except Exception:
                pass  # Don't fail if we can't get comments
            
            return {
                "request_type": request_type,
                "source": source,
                "priority": priority,
                "severity": severity,
                "title": issue.title,
                "content": issue.body or "",
                "workflow_artifacts": workflow_artifacts
            }
            
        except GitHubClientError as e:
            print(f"Error extracting request info from Issue #{issue_number}: {e}")
            raise
    
    def evaluate_stage_policy(self, issue_number: int, stage: str) -> Dict[str, Any]:
        """
        Evaluate policy for a workflow stage.
        
        Args:
            issue_number: GitHub Issue number
            stage: Workflow stage (triage, plan, prioritize, implement)
            
        Returns:
            Dictionary with policy decision and details
        """
        try:
            # Extract trace_id and request info
            trace_id = self.extract_trace_id_from_issue(issue_number)
            if not trace_id:
                trace_id = f"policy-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{issue_number}"
            
            request_info = self.extract_request_info_from_issue(issue_number)
            
            # Create stage context
            context = StageContext(
                issue_id=issue_number,
                current_stage=stage,
                request_type=request_info["request_type"],
                source=request_info["source"],
                priority=request_info["priority"],
                severity=request_info["severity"],
                trace_id=trace_id,
                issue_content=request_info["content"],
                workflow_artifacts=request_info["workflow_artifacts"]
            )
            
            # Evaluate policy
            decision = self.policy_component.evaluate_stage_transition(context)
            
            # Return result in format expected by GitHub Actions
            result = {
                "decision": decision.decision,
                "reason": decision.reason,
                "constraints": decision.constraints,
                "trace_id": trace_id,
                "timestamp": decision.timestamp.isoformat()
            }
            
            if decision.constructed_prompt:
                result["constructed_prompt"] = decision.constructed_prompt
            
            return result
            
        except Exception as e:
            print(f"Error evaluating stage policy: {e}")
            return {
                "decision": "block",
                "reason": f"Policy evaluation error: {str(e)}",
                "constraints": {"error": "policy_evaluation_failed"},
                "trace_id": trace_id if 'trace_id' in locals() else "unknown",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def evaluate_change_policy(self, changed_files: list, ci_status: str, trace_id: str) -> Dict[str, Any]:
        """
        Evaluate policy for implementation changes.
        
        Args:
            changed_files: List of changed file paths
            ci_status: CI/CD status (success, failure, pending)
            trace_id: Trace ID for audit trail
            
        Returns:
            Dictionary with policy decision and details
        """
        try:
            # Create change context
            context = ChangeContext(
                changed_files=changed_files,
                diff_stats={"additions": len(changed_files) * 10, "deletions": len(changed_files) * 5},  # Estimate
                ci_status=ci_status
            )
            
            # Evaluate policy
            decision = self.policy_component.evaluate_implementation_changes(context, trace_id)
            
            # Return result in format expected by GitHub Actions
            return {
                "decision": decision.decision,
                "reason": decision.reason,
                "constraints": decision.constraints,
                "trace_id": trace_id,
                "timestamp": decision.timestamp.isoformat()
            }
            
        except Exception as e:
            print(f"Error evaluating change policy: {e}")
            return {
                "decision": "block",
                "reason": f"Change policy evaluation error: {str(e)}",
                "constraints": {"error": "change_evaluation_failed"},
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def add_policy_decision_comment(self, issue_number: int, decision_result: Dict[str, Any], stage: str) -> None:
        """
        Add policy decision comment to Issue for audit trail.
        
        Args:
            issue_number: GitHub Issue number
            decision_result: Policy decision result
            stage: Workflow stage
        """
        try:
            # Build decision emoji
            decision_emojis = {
                "allow": "✅",
                "review_required": "⚠️",
                "block": "🚫"
            }
            emoji = decision_emojis.get(decision_result["decision"], "ℹ️")
            
            # Build comment
            comment_lines = [
                f"{emoji} **Policy Gate Decision: {decision_result['decision'].upper()}**",
                "",
                f"**Stage**: {stage}",
                f"**Decision**: {decision_result['decision']}",
                f"**Reason**: {decision_result['reason']}",
                f"**Timestamp**: {decision_result['timestamp']}",
                f"**Trace_ID**: `{decision_result['trace_id']}`"
            ]
            
            # Add constraints if present
            if decision_result.get("constraints"):
                constraints = decision_result["constraints"]
                comment_lines.extend(["", "**Applied Constraints**:"])
                for key, value in constraints.items():
                    if isinstance(value, list):
                        comment_lines.append(f"- {key}: {', '.join(map(str, value))}")
                    else:
                        comment_lines.append(f"- {key}: {value}")
            
            # Add workflow run correlation
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
            self.github_client.add_issue_comment(issue_number, comment)
            
            print(f"Added policy decision comment to Issue #{issue_number}")
            
        except Exception as e:
            print(f"Error adding policy decision comment: {e}")
            # Don't fail the workflow if we can't add the comment


def main():
    """Main entry point for policy gate evaluation script."""
    parser = argparse.ArgumentParser(description="Policy Gate Evaluation Script")
    parser.add_argument("command", choices=["evaluate-stage", "evaluate-change"], 
                       help="Command to execute")
    parser.add_argument("--issue-id", type=int,
                       help="GitHub Issue number (required for evaluate-stage)")
    parser.add_argument("--stage", 
                       help="Workflow stage (required for evaluate-stage)")
    parser.add_argument("--changed-files", nargs="*",
                       help="List of changed files (required for evaluate-change)")
    parser.add_argument("--ci-status", default="success",
                       help="CI status (for evaluate-change)")
    parser.add_argument("--trace-id",
                       help="Trace ID (for evaluate-change)")
    parser.add_argument("--output-format", choices=["json", "github-actions"], default="github-actions",
                       help="Output format")
    parser.add_argument("--add-comment", action="store_true",
                       help="Add policy decision comment to Issue")
    
    args = parser.parse_args()
    
    try:
        evaluator = PolicyGateEvaluator()
        
        if args.command == "evaluate-stage":
            if not args.issue_id or not args.stage:
                print("Error: --issue-id and --stage are required for evaluate-stage command")
                sys.exit(1)
            
            result = evaluator.evaluate_stage_policy(args.issue_id, args.stage)
            
            # Add comment if requested
            if args.add_comment:
                evaluator.add_policy_decision_comment(args.issue_id, result, args.stage)
            
            # Output result
            if args.output_format == "json":
                print(json.dumps(result, indent=2))
            else:
                # GitHub Actions output format
                print(f"decision={result['decision']}")
                print(f"reason={result['reason']}")
                print(f"trace_id={result['trace_id']}")
                if result.get("constructed_prompt"):
                    # Save prompt to file for GitHub Actions to use
                    with open("policy_prompt.txt", "w") as f:
                        f.write(result["constructed_prompt"])
                    print("constructed_prompt_file=policy_prompt.txt")
            
            # Exit with appropriate code
            sys.exit(0 if result["decision"] == "allow" else 1)
        
        elif args.command == "evaluate-change":
            if not args.changed_files or not args.trace_id:
                print("Error: --changed-files and --trace-id are required for evaluate-change command")
                sys.exit(1)
            
            result = evaluator.evaluate_change_policy(args.changed_files, args.ci_status, args.trace_id)
            
            # Output result
            if args.output_format == "json":
                print(json.dumps(result, indent=2))
            else:
                # GitHub Actions output format
                print(f"decision={result['decision']}")
                print(f"reason={result['reason']}")
                print(f"trace_id={result['trace_id']}")
            
            # Exit with appropriate code
            sys.exit(0 if result["decision"] == "allow" else 1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()