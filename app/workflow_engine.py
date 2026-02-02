"""Functional workflow engine for the Self-Evolving Web Application.

This module implements the functional workflow logic that integrates Claude API
with the Policy & Gate Component to produce real outcomes for triage, planning,
and prioritization workflows.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.claude_client import ClaudeClient, ClaudeClientError, get_claude_client
from app.policy_gate import PolicyGateComponent, get_policy_gate_component
from app.github_client import GitHubClient, get_github_client
from app.models import StageContext

logger = logging.getLogger(__name__)


class WorkflowEngineError(Exception):
    """Custom exception for workflow engine errors."""
    pass


class WorkflowEngine:
    """
    Functional workflow engine that orchestrates Claude analysis with policy constraints.
    
    This engine integrates the Policy & Gate Component with Claude API to produce
    real workflow outcomes while ensuring all automated actions stay within
    defined policy bounds.
    """
    
    def __init__(
        self,
        claude_client: Optional[ClaudeClient] = None,
        policy_component: Optional[PolicyGateComponent] = None,
        github_client: Optional[GitHubClient] = None,
        db_session: Optional[Session] = None
    ):
        """
        Initialize workflow engine.
        
        Args:
            claude_client: Claude API client
            policy_component: Policy & Gate Component
            github_client: GitHub API client
            db_session: Database session for audit trail
        """
        self.claude_client = claude_client or get_claude_client()
        self.policy_component = policy_component or get_policy_gate_component(db_session)
        self.github_client = github_client or get_github_client()
        self.db_session = db_session
    
    def execute_triage_workflow(
        self,
        issue_id: int,
        trace_id: str,
        issue_content: str,
        request_type: str,
        source: str,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute triage workflow with real Claude analysis.
        
        Args:
            issue_id: GitHub Issue ID
            trace_id: Trace ID for correlation
            issue_content: Issue content to analyze
            request_type: Type of request (bug, feature, investigate)
            source: Source of request (user, monitor)
            severity: Severity level for bugs
            
        Returns:
            Triage analysis results with recommendation
            
        Raises:
            WorkflowEngineError: If workflow execution fails
        """
        try:
            logger.info(f"Starting triage workflow for issue #{issue_id}, trace_id: {trace_id}")
            
            # Create stage context
            context = StageContext(
                issue_id=issue_id,
                current_stage="triage",
                request_type=request_type,
                source=source,
                trace_id=trace_id,
                issue_content=issue_content,
                severity=severity,
                workflow_artifacts=[]
            )
            
            # Policy gate evaluation
            policy_decision = self.policy_component.evaluate_stage_transition(context)
            
            if policy_decision.decision == "block":
                logger.warning(f"Triage workflow blocked by policy: {policy_decision.reason}")
                return {
                    "success": False,
                    "blocked": True,
                    "reason": policy_decision.reason,
                    "constraints": policy_decision.constraints,
                    "trace_id": trace_id
                }
            
            if policy_decision.decision == "review_required":
                logger.info(f"Triage workflow requires human review: {policy_decision.reason}")
                return {
                    "success": False,
                    "review_required": True,
                    "reason": policy_decision.reason,
                    "constraints": policy_decision.constraints,
                    "trace_id": trace_id
                }
            
            # Execute Claude triage analysis
            constrained_prompt = policy_decision.constructed_prompt
            triage_result = self.claude_client.triage_analysis(constrained_prompt, trace_id)
            
            # Add workflow execution metadata
            triage_result["workflow_execution"] = {
                "issue_id": issue_id,
                "stage": "triage",
                "policy_decision": policy_decision.decision,
                "policy_constraints": policy_decision.constraints,
                "execution_timestamp": datetime.utcnow().isoformat()
            }
            
            # Add GitHub Issue comment with triage results
            self._add_workflow_comment(
                issue_id=issue_id,
                workflow_stage="triage",
                results=triage_result,
                trace_id=trace_id
            )
            
            logger.info(f"Completed triage workflow for issue #{issue_id}, trace_id: {trace_id}")
            
            return {
                "success": True,
                "triage_analysis": triage_result,
                "next_stage": self._determine_next_stage_from_triage(triage_result),
                "trace_id": trace_id
            }
            
        except ClaudeClientError as e:
            logger.error(f"Claude API error in triage workflow: {str(e)}")
            raise WorkflowEngineError(f"Triage analysis failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in triage workflow: {str(e)}")
            raise WorkflowEngineError(f"Triage workflow failed: {str(e)}")
    
    def execute_planning_workflow(
        self,
        issue_id: int,
        trace_id: str,
        issue_content: str,
        request_type: str,
        source: str,
        triage_artifacts: List[str],
        priority: Optional[str] = None,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute planning workflow with real Claude analysis.
        
        Args:
            issue_id: GitHub Issue ID
            trace_id: Trace ID for correlation
            issue_content: Issue content to analyze
            request_type: Type of request (bug, feature)
            source: Source of request (user, monitor)
            triage_artifacts: Artifacts from triage stage
            priority: Priority level for features
            severity: Severity level for bugs
            
        Returns:
            Planning analysis results with implementation plan
            
        Raises:
            WorkflowEngineError: If workflow execution fails
        """
        try:
            logger.info(f"Starting planning workflow for issue #{issue_id}, trace_id: {trace_id}")
            
            # Create stage context
            context = StageContext(
                issue_id=issue_id,
                current_stage="plan",
                request_type=request_type,
                source=source,
                trace_id=trace_id,
                issue_content=issue_content,
                priority=priority,
                severity=severity,
                workflow_artifacts=triage_artifacts
            )
            
            # Policy gate evaluation
            policy_decision = self.policy_component.evaluate_stage_transition(context)
            
            if policy_decision.decision == "block":
                logger.warning(f"Planning workflow blocked by policy: {policy_decision.reason}")
                return {
                    "success": False,
                    "blocked": True,
                    "reason": policy_decision.reason,
                    "constraints": policy_decision.constraints,
                    "trace_id": trace_id
                }
            
            if policy_decision.decision == "review_required":
                logger.info(f"Planning workflow requires human review: {policy_decision.reason}")
                return {
                    "success": False,
                    "review_required": True,
                    "reason": policy_decision.reason,
                    "constraints": policy_decision.constraints,
                    "trace_id": trace_id
                }
            
            # Execute Claude planning analysis
            constrained_prompt = policy_decision.constructed_prompt
            planning_result = self.claude_client.planning_analysis(constrained_prompt, trace_id)
            
            # Add workflow execution metadata
            planning_result["workflow_execution"] = {
                "issue_id": issue_id,
                "stage": "planning",
                "policy_decision": policy_decision.decision,
                "policy_constraints": policy_decision.constraints,
                "execution_timestamp": datetime.utcnow().isoformat()
            }
            
            # Add GitHub Issue comment with planning results
            self._add_workflow_comment(
                issue_id=issue_id,
                workflow_stage="planning",
                results=planning_result,
                trace_id=trace_id
            )
            
            logger.info(f"Completed planning workflow for issue #{issue_id}, trace_id: {trace_id}")
            
            return {
                "success": True,
                "planning_analysis": planning_result,
                "next_stage": "prioritize",
                "trace_id": trace_id
            }
            
        except ClaudeClientError as e:
            logger.error(f"Claude API error in planning workflow: {str(e)}")
            raise WorkflowEngineError(f"Planning analysis failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in planning workflow: {str(e)}")
            raise WorkflowEngineError(f"Planning workflow failed: {str(e)}")
    
    def execute_prioritization_workflow(
        self,
        issue_id: int,
        trace_id: str,
        issue_content: str,
        request_type: str,
        source: str,
        workflow_artifacts: List[str],
        priority: Optional[str] = None,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute prioritization workflow with real Claude analysis.
        
        Args:
            issue_id: GitHub Issue ID
            trace_id: Trace ID for correlation
            issue_content: Issue content to analyze
            request_type: Type of request (bug, feature)
            source: Source of request (user, monitor)
            workflow_artifacts: Artifacts from previous stages
            priority: Priority level for features
            severity: Severity level for bugs
            
        Returns:
            Prioritization analysis results with priority recommendation
            
        Raises:
            WorkflowEngineError: If workflow execution fails
        """
        try:
            logger.info(f"Starting prioritization workflow for issue #{issue_id}, trace_id: {trace_id}")
            
            # Create stage context
            context = StageContext(
                issue_id=issue_id,
                current_stage="prioritize",
                request_type=request_type,
                source=source,
                trace_id=trace_id,
                issue_content=issue_content,
                priority=priority,
                severity=severity,
                workflow_artifacts=workflow_artifacts
            )
            
            # Policy gate evaluation
            policy_decision = self.policy_component.evaluate_stage_transition(context)
            
            if policy_decision.decision == "block":
                logger.warning(f"Prioritization workflow blocked by policy: {policy_decision.reason}")
                return {
                    "success": False,
                    "blocked": True,
                    "reason": policy_decision.reason,
                    "constraints": policy_decision.constraints,
                    "trace_id": trace_id
                }
            
            if policy_decision.decision == "review_required":
                logger.info(f"Prioritization workflow requires human review: {policy_decision.reason}")
                return {
                    "success": False,
                    "review_required": True,
                    "reason": policy_decision.reason,
                    "constraints": policy_decision.constraints,
                    "trace_id": trace_id
                }
            
            # Execute Claude prioritization analysis
            constrained_prompt = policy_decision.constructed_prompt
            prioritization_result = self.claude_client.prioritization_analysis(constrained_prompt, trace_id)
            
            # Add workflow execution metadata
            prioritization_result["workflow_execution"] = {
                "issue_id": issue_id,
                "stage": "prioritization",
                "policy_decision": policy_decision.decision,
                "policy_constraints": policy_decision.constraints,
                "execution_timestamp": datetime.utcnow().isoformat()
            }
            
            # Extract priority recommendation for label application
            priority_label = self._extract_priority_label(prioritization_result)
            
            # Add GitHub Issue comment with prioritization results
            self._add_workflow_comment(
                issue_id=issue_id,
                workflow_stage="prioritization",
                results=prioritization_result,
                trace_id=trace_id
            )
            
            logger.info(f"Completed prioritization workflow for issue #{issue_id}, trace_id: {trace_id}")
            
            return {
                "success": True,
                "prioritization_analysis": prioritization_result,
                "recommended_priority_label": priority_label,
                "next_stage": "awaiting-implementation-approval",
                "trace_id": trace_id
            }
            
        except ClaudeClientError as e:
            logger.error(f"Claude API error in prioritization workflow: {str(e)}")
            raise WorkflowEngineError(f"Prioritization analysis failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in prioritization workflow: {str(e)}")
            raise WorkflowEngineError(f"Prioritization workflow failed: {str(e)}")
    
    def _determine_next_stage_from_triage(self, triage_result: Dict[str, Any]) -> str:
        """Determine next stage based on triage recommendation."""
        recommendation = triage_result.get("recommendation", "").lower()
        
        if "proceed" in recommendation:
            return "plan"
        elif "block" in recommendation:
            return "blocked"
        else:
            # Default to planning if recommendation is unclear
            logger.warning("Unclear triage recommendation, defaulting to planning stage")
            return "plan"
    
    def _extract_priority_label(self, prioritization_result: Dict[str, Any]) -> str:
        """Extract priority label from prioritization analysis."""
        priority_rec = prioritization_result.get("priority_recommendation", "").lower()
        
        if "p0" in priority_rec:
            return "priority:p0"
        elif "p1" in priority_rec:
            return "priority:p1"
        elif "p2" in priority_rec:
            return "priority:p2"
        else:
            # Default to p2 if unclear
            logger.warning("Unclear priority recommendation, defaulting to p2")
            return "priority:p2"
    
    def _add_workflow_comment(
        self,
        issue_id: int,
        workflow_stage: str,
        results: Dict[str, Any],
        trace_id: str
    ) -> None:
        """Add workflow results as GitHub Issue comment."""
        try:
            # Build comment content based on workflow stage
            if workflow_stage == "triage":
                comment = self._build_triage_comment(results, trace_id)
            elif workflow_stage == "planning":
                comment = self._build_planning_comment(results, trace_id)
            elif workflow_stage == "prioritization":
                comment = self._build_prioritization_comment(results, trace_id)
            else:
                comment = f"**{workflow_stage.title()} Analysis Completed**\n\n**Trace_ID**: `{trace_id}`\n\nResults available in workflow execution metadata."
            
            self.github_client.add_issue_comment(issue_id, comment)
            logger.info(f"Added {workflow_stage} workflow comment to issue #{issue_id}")
            
        except Exception as e:
            logger.error(f"Failed to add workflow comment to issue #{issue_id}: {str(e)}")
            # Don't raise exception - comment failure shouldn't fail the workflow
    
    def _build_triage_comment(self, results: Dict[str, Any], trace_id: str) -> str:
        """Build triage analysis comment."""
        return f"""🔍 **Triage Analysis Completed** ✅

**Problem Summary**
{results.get('problem_summary', 'Not available')}

**Suspected Cause**
{results.get('suspected_cause', 'Not available')}

**Clarifying Questions**
{results.get('clarifying_questions', 'Not available')}

**Recommendation**
{results.get('recommendation', 'Not available')}

---
**Trace_ID**: `{trace_id}`
**Analysis Timestamp**: {results.get('_metadata', {}).get('timestamp', 'Unknown')}
**Model**: {results.get('_metadata', {}).get('model', 'Unknown')}
**Token Usage**: {results.get('_metadata', {}).get('usage', {})}
"""
    
    def _build_planning_comment(self, results: Dict[str, Any], trace_id: str) -> str:
        """Build planning analysis comment."""
        return f"""📋 **Implementation Plan Completed** ✅

**Proposed Approach**
{results.get('proposed_approach', 'Not available')}

**Affected Files**
{results.get('affected_files', 'Not available')}

**Acceptance Criteria**
{results.get('acceptance_criteria', 'Not available')}

**Unit Test Plan**
{results.get('unit_test_plan', 'Not available')}

**Risks and Considerations**
{results.get('risks_and_considerations', 'Not available')}

**Effort Estimate**
{results.get('effort_estimate', 'Not available')}

---
**Trace_ID**: `{trace_id}`
**Analysis Timestamp**: {results.get('_metadata', {}).get('timestamp', 'Unknown')}
**Model**: {results.get('_metadata', {}).get('model', 'Unknown')}
**Token Usage**: {results.get('_metadata', {}).get('usage', {})}
"""
    
    def _build_prioritization_comment(self, results: Dict[str, Any], trace_id: str) -> str:
        """Build prioritization analysis comment."""
        return f"""⚖️ **Priority Assessment Completed** ✅

**Expected User Value**
{results.get('expected_user_value', 'Not available')}

**Implementation Effort**
{results.get('implementation_effort', 'Not available')}

**Risk Assessment**
{results.get('risk_assessment', 'Not available')}

**Priority Recommendation**
{results.get('priority_recommendation', 'Not available')}

**Justification**
{results.get('justification', 'Not available')}

---
**Trace_ID**: `{trace_id}`
**Analysis Timestamp**: {results.get('_metadata', {}).get('timestamp', 'Unknown')}
**Model**: {results.get('_metadata', {}).get('model', 'Unknown')}
**Token Usage**: {results.get('_metadata', {}).get('usage', {})}
"""


def get_workflow_engine(db_session: Optional[Session] = None) -> WorkflowEngine:
    """
    Factory function to create a configured WorkflowEngine instance.
    
    Args:
        db_session: Database session for audit trail
        
    Returns:
        Configured WorkflowEngine instance
        
    Raises:
        WorkflowEngineError: If engine creation fails
    """
    try:
        return WorkflowEngine(db_session=db_session)
    except Exception as e:
        raise WorkflowEngineError(f"Failed to create workflow engine: {str(e)}")