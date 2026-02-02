#!/usr/bin/env python3
"""
Functional workflow executor for GitHub Actions.

This script integrates the WorkflowEngine with GitHub Actions to execute
real Claude-powered workflows for triage, planning, and prioritization.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from workflow_engine import WorkflowEngine, WorkflowEngineError, get_workflow_engine
from github_client import GitHubClient, GitHubClientError


class FunctionalWorkflowExecutor:
    """
    Executor for functional workflows in GitHub Actions environment.
    
    Integrates WorkflowEngine with GitHub Actions to execute real Claude-powered
    workflows while maintaining proper error handling and state transitions.
    """
    
    def __init__(self):
        """Initialize the functional workflow executor."""
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repository = os.getenv("GITHUB_REPOSITORY")
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        if not self.repository:
            raise ValueError("GITHUB_REPOSITORY environment variable is required")
        if not self.claude_api_key:
            raise ValueError("CLAUDE_API_KEY environment variable is required")
        
        try:
            self.workflow_engine = get_workflow_engine()
            self.github_client = GitHubClient(
                token=self.github_token,
                repository=self.repository
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize workflow executor: {str(e)}")
    
    def execute_triage_workflow(self, issue_id: int) -> Dict[str, Any]:
        """
        Execute triage workflow for the given issue.
        
        Args:
            issue_id: GitHub Issue ID
            
        Returns:
            Workflow execution results
            
        Raises:
            WorkflowEngineError: If workflow execution fails
        """
        try:
            print(f"🔍 Starting triage workflow for issue #{issue_id}")
            
            # Get issue details from GitHub
            issue = self.github_client.get_issue(issue_id)
            
            # Extract issue information
            issue_content = issue.body or ""
            title = issue.title
            
            # Extract trace_id from issue body
            trace_id = self._extract_trace_id_from_issue(issue_content)
            if not trace_id:
                trace_id = f"workflow-triage-{issue_id}-{int(datetime.utcnow().timestamp())}"
                print(f"⚠️ No trace_id found in issue, generated: {trace_id}")
            
            # Determine request type and source from labels
            labels = [label.name for label in issue.labels]
            request_type = self._extract_request_type_from_labels(labels)
            source = self._extract_source_from_labels(labels)
            severity = self._extract_severity_from_issue(issue_content, title)
            
            # Execute triage workflow
            result = self.workflow_engine.execute_triage_workflow(
                issue_id=issue_id,
                trace_id=trace_id,
                issue_content=f"Title: {title}\n\nDescription: {issue_content}",
                request_type=request_type,
                source=source,
                severity=severity
            )
            
            if result["success"]:
                print(f"✅ Triage workflow completed successfully for issue #{issue_id}")
                print(f"📋 Next stage: {result['next_stage']}")
                return {
                    "success": True,
                    "next_stage": result["next_stage"],
                    "trace_id": trace_id,
                    "analysis_completed": True
                }
            else:
                reason = result.get("reason", "Unknown reason")
                if result.get("blocked"):
                    print(f"🚫 Triage workflow blocked: {reason}")
                    return {
                        "success": False,
                        "blocked": True,
                        "reason": reason,
                        "trace_id": trace_id
                    }
                elif result.get("review_required"):
                    print(f"👥 Triage workflow requires human review: {reason}")
                    return {
                        "success": False,
                        "review_required": True,
                        "reason": reason,
                        "trace_id": trace_id
                    }
                else:
                    print(f"❌ Triage workflow failed: {reason}")
                    return {
                        "success": False,
                        "reason": reason,
                        "trace_id": trace_id
                    }
            
        except WorkflowEngineError as e:
            print(f"❌ Workflow engine error: {str(e)}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error in triage workflow: {str(e)}")
            raise WorkflowEngineError(f"Triage workflow failed: {str(e)}")
    
    def execute_planning_workflow(self, issue_id: int) -> Dict[str, Any]:
        """
        Execute planning workflow for the given issue.
        
        Args:
            issue_id: GitHub Issue ID
            
        Returns:
            Workflow execution results
            
        Raises:
            WorkflowEngineError: If workflow execution fails
        """
        try:
            print(f"📋 Starting planning workflow for issue #{issue_id}")
            
            # Get issue details from GitHub
            issue = self.github_client.get_issue(issue_id)
            
            # Extract issue information
            issue_content = issue.body or ""
            title = issue.title
            
            # Extract trace_id from issue body
            trace_id = self._extract_trace_id_from_issue(issue_content)
            if not trace_id:
                trace_id = f"workflow-planning-{issue_id}-{int(datetime.utcnow().timestamp())}"
                print(f"⚠️ No trace_id found in issue, generated: {trace_id}")
            
            # Determine request type and source from labels
            labels = [label.name for label in issue.labels]
            request_type = self._extract_request_type_from_labels(labels)
            source = self._extract_source_from_labels(labels)
            priority = self._extract_priority_from_labels(labels)
            severity = self._extract_severity_from_issue(issue_content, title)
            
            # Get triage artifacts from issue comments
            triage_artifacts = self._extract_workflow_artifacts(issue_id, "triage")
            
            # Execute planning workflow
            result = self.workflow_engine.execute_planning_workflow(
                issue_id=issue_id,
                trace_id=trace_id,
                issue_content=f"Title: {title}\n\nDescription: {issue_content}",
                request_type=request_type,
                source=source,
                triage_artifacts=triage_artifacts,
                priority=priority,
                severity=severity
            )
            
            if result["success"]:
                print(f"✅ Planning workflow completed successfully for issue #{issue_id}")
                print(f"📋 Next stage: {result['next_stage']}")
                return {
                    "success": True,
                    "next_stage": result["next_stage"],
                    "trace_id": trace_id,
                    "analysis_completed": True
                }
            else:
                reason = result.get("reason", "Unknown reason")
                if result.get("blocked"):
                    print(f"🚫 Planning workflow blocked: {reason}")
                    return {
                        "success": False,
                        "blocked": True,
                        "reason": reason,
                        "trace_id": trace_id
                    }
                elif result.get("review_required"):
                    print(f"👥 Planning workflow requires human review: {reason}")
                    return {
                        "success": False,
                        "review_required": True,
                        "reason": reason,
                        "trace_id": trace_id
                    }
                else:
                    print(f"❌ Planning workflow failed: {reason}")
                    return {
                        "success": False,
                        "reason": reason,
                        "trace_id": trace_id
                    }
            
        except WorkflowEngineError as e:
            print(f"❌ Workflow engine error: {str(e)}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error in planning workflow: {str(e)}")
            raise WorkflowEngineError(f"Planning workflow failed: {str(e)}")
    
    def execute_prioritization_workflow(self, issue_id: int) -> Dict[str, Any]:
        """
        Execute prioritization workflow for the given issue.
        
        Args:
            issue_id: GitHub Issue ID
            
        Returns:
            Workflow execution results including recommended priority label
            
        Raises:
            WorkflowEngineError: If workflow execution fails
        """
        try:
            print(f"⚖️ Starting prioritization workflow for issue #{issue_id}")
            
            # Get issue details from GitHub
            issue = self.github_client.get_issue(issue_id)
            
            # Extract issue information
            issue_content = issue.body or ""
            title = issue.title
            
            # Extract trace_id from issue body
            trace_id = self._extract_trace_id_from_issue(issue_content)
            if not trace_id:
                trace_id = f"workflow-prioritization-{issue_id}-{int(datetime.utcnow().timestamp())}"
                print(f"⚠️ No trace_id found in issue, generated: {trace_id}")
            
            # Determine request type and source from labels
            labels = [label.name for label in issue.labels]
            request_type = self._extract_request_type_from_labels(labels)
            source = self._extract_source_from_labels(labels)
            priority = self._extract_priority_from_labels(labels)
            severity = self._extract_severity_from_issue(issue_content, title)
            
            # Get workflow artifacts from issue comments
            workflow_artifacts = self._extract_workflow_artifacts(issue_id, "all")
            
            # Execute prioritization workflow
            result = self.workflow_engine.execute_prioritization_workflow(
                issue_id=issue_id,
                trace_id=trace_id,
                issue_content=f"Title: {title}\n\nDescription: {issue_content}",
                request_type=request_type,
                source=source,
                workflow_artifacts=workflow_artifacts,
                priority=priority,
                severity=severity
            )
            
            if result["success"]:
                print(f"✅ Prioritization workflow completed successfully for issue #{issue_id}")
                print(f"📋 Next stage: {result['next_stage']}")
                print(f"🏷️ Recommended priority: {result['recommended_priority_label']}")
                return {
                    "success": True,
                    "next_stage": result["next_stage"],
                    "recommended_priority_label": result["recommended_priority_label"],
                    "trace_id": trace_id,
                    "analysis_completed": True
                }
            else:
                reason = result.get("reason", "Unknown reason")
                if result.get("blocked"):
                    print(f"🚫 Prioritization workflow blocked: {reason}")
                    return {
                        "success": False,
                        "blocked": True,
                        "reason": reason,
                        "trace_id": trace_id
                    }
                elif result.get("review_required"):
                    print(f"👥 Prioritization workflow requires human review: {reason}")
                    return {
                        "success": False,
                        "review_required": True,
                        "reason": reason,
                        "trace_id": trace_id
                    }
                else:
                    print(f"❌ Prioritization workflow failed: {reason}")
                    return {
                        "success": False,
                        "reason": reason,
                        "trace_id": trace_id
                    }
            
        except WorkflowEngineError as e:
            print(f"❌ Workflow engine error: {str(e)}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error in prioritization workflow: {str(e)}")
            raise WorkflowEngineError(f"Prioritization workflow failed: {str(e)}")
    
    def _extract_trace_id_from_issue(self, issue_body: str) -> Optional[str]:
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
    
    def _extract_request_type_from_labels(self, labels: list) -> str:
        """Extract request type from issue labels."""
        for label in labels:
            if label.startswith("request:"):
                return label.split(":", 1)[1]
        return "bug"  # Default fallback
    
    def _extract_source_from_labels(self, labels: list) -> str:
        """Extract source from issue labels."""
        for label in labels:
            if label.startswith("source:"):
                return label.split(":", 1)[1]
        return "user"  # Default fallback
    
    def _extract_priority_from_labels(self, labels: list) -> Optional[str]:
        """Extract priority from issue labels."""
        for label in labels:
            if label.startswith("priority:"):
                return label.split(":", 1)[1]
        return None
    
    def _extract_severity_from_issue(self, issue_content: str, title: str) -> Optional[str]:
        """Extract severity from issue content or title."""
        content = f"{title} {issue_content}".lower()
        
        if "critical" in content or "severe" in content:
            return "critical"
        elif "high" in content:
            return "high"
        elif "medium" in content:
            return "medium"
        elif "low" in content:
            return "low"
        
        return None
    
    def _extract_workflow_artifacts(self, issue_id: int, stage: str) -> list:
        """Extract workflow artifacts from issue comments."""
        # For now, return a simple list indicating which stages have been completed
        # In a full implementation, this would parse comments to extract actual artifacts
        artifacts = []
        
        if stage in ["all", "triage"]:
            artifacts.append("triage_report")
        
        if stage in ["all", "planning"]:
            artifacts.append("implementation_plan")
        
        return artifacts


def main():
    """Main entry point for functional workflow executor."""
    parser = argparse.ArgumentParser(description="Functional Workflow Executor")
    parser.add_argument("workflow", choices=["triage", "planning", "prioritization"],
                       help="Workflow type to execute")
    parser.add_argument("--issue-id", type=int, required=True,
                       help="GitHub Issue ID")
    
    args = parser.parse_args()
    
    try:
        executor = FunctionalWorkflowExecutor()
        
        if args.workflow == "triage":
            result = executor.execute_triage_workflow(args.issue_id)
        elif args.workflow == "planning":
            result = executor.execute_planning_workflow(args.issue_id)
        elif args.workflow == "prioritization":
            result = executor.execute_prioritization_workflow(args.issue_id)
        else:
            print(f"Unknown workflow: {args.workflow}")
            sys.exit(1)
        
        # Output result as JSON for GitHub Actions
        print(f"\n📊 WORKFLOW_RESULT={json.dumps(result)}")
        
        # Set GitHub Actions outputs
        if "GITHUB_OUTPUT" in os.environ:
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"success={str(result.get('success', False)).lower()}\n")
                f.write(f"trace_id={result.get('trace_id', '')}\n")
                
                if result.get("success"):
                    f.write(f"next_stage={result.get('next_stage', '')}\n")
                    if "recommended_priority_label" in result:
                        f.write(f"recommended_priority={result['recommended_priority_label']}\n")
                else:
                    f.write(f"blocked={str(result.get('blocked', False)).lower()}\n")
                    f.write(f"review_required={str(result.get('review_required', False)).lower()}\n")
                    f.write(f"reason={result.get('reason', '')}\n")
        
        sys.exit(0 if result.get("success", False) else 1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()