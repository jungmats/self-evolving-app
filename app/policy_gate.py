"""Policy & Gate Component for the Self-Evolving Web Application.

This component provides deterministic policy evaluation and constrained prompt construction
for all workflow stages, ensuring automation stays within defined bounds.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from models import StageContext, ChangeContext, PolicyDecisionModel

logger = logging.getLogger(__name__)


class TemplateLoadError(Exception):
    """Raised when a required prompt template cannot be loaded."""
    pass


class PolicyGateComponent:
    """
    Policy & Gate Component that evaluates workflow steps and generates policy-constrained prompts.
    
    This component ensures that all automated actions are bounded, auditable, and cannot proceed
    outside defined constraints. It provides deterministic decision-making based on stage context,
    artifact context, operational context, and change context.
    """
    
    def __init__(self):
        """Initialize the Policy & Gate Component."""
        self._stage_constraints = self._load_stage_constraints()
        self._prompt_templates = self._load_prompt_templates()
    
    def evaluate_stage_transition(self, context: StageContext) -> PolicyDecisionModel:
        """
        Evaluate whether a workflow stage transition should be allowed.
        
        Args:
            context: Stage context containing issue details and current state
            
        Returns:
            PolicyDecisionModel with decision, reason, and constructed prompt if allowed
        """
        try:
            # Validate stage context
            if not self._is_valid_stage(context.current_stage):
                return PolicyDecisionModel(
                    decision="block",
                    reason=f"Invalid stage: {context.current_stage}",
                    constraints={"valid_stages": list(self._stage_constraints.keys())}
                )
            
            # Check request type compatibility
            if not self._is_request_type_allowed(context.request_type, context.current_stage):
                return PolicyDecisionModel(
                    decision="block",
                    reason=f"Request type '{context.request_type}' not allowed for stage '{context.current_stage}'",
                    constraints={"allowed_request_types": self._get_allowed_request_types(context.current_stage)}
                )
            
            # Check source compatibility
            if not self._is_source_allowed(context.source, context.current_stage):
                return PolicyDecisionModel(
                    decision="review_required",
                    reason=f"Source '{context.source}' requires review for stage '{context.current_stage}'",
                    constraints={"source_policy": "monitor_sources_require_review"}
                )
            
            # Check content appropriateness
            content_check = self._evaluate_content_appropriateness(context)
            if content_check["decision"] != "allow":
                return PolicyDecisionModel(
                    decision=content_check["decision"],
                    reason=content_check["reason"],
                    constraints=content_check["constraints"]
                )
            
            # Check stage-specific constraints
            stage_check = self._evaluate_stage_constraints(context)
            if stage_check["decision"] != "allow":
                return PolicyDecisionModel(
                    decision=stage_check["decision"],
                    reason=stage_check["reason"],
                    constraints=stage_check["constraints"]
                )
            
            # Generate constrained prompt for allowed decisions
            constructed_prompt = self._construct_constrained_prompt(context)
            
            decision = PolicyDecisionModel(
                decision="allow",
                reason=f"All policy checks passed for {context.current_stage} stage",
                constructed_prompt=constructed_prompt,
                constraints={
                    "stage": context.current_stage,
                    "request_type": context.request_type,
                    "source": context.source,
                    "scope_limits": self._stage_constraints[context.current_stage]["scope_limits"]
                }
            )
            
            # Record decision for audit trail (GitHub comments provide audit trail)
            logger.info(f"Policy decision for trace_id {context.trace_id}, stage {context.current_stage}: {decision.decision}")
            
            return decision
            
        except Exception as e:
            logger.error(f"Policy evaluation failed for trace_id {context.trace_id}: {str(e)}")
            return PolicyDecisionModel(
                decision="block",
                reason=f"Policy evaluation error: {str(e)}",
                constraints={"error": "policy_evaluation_failed"}
            )
    
    def evaluate_implementation_changes(self, context: ChangeContext, trace_id: str) -> PolicyDecisionModel:
        """
        Evaluate implementation changes before allowing deployment.
        
        Args:
            context: Change context with file changes and test results
            trace_id: Trace ID for audit trail
            
        Returns:
            PolicyDecisionModel with decision about change approval
        """
        try:
            # Check file change limits
            if len(context.changed_files) > 20:
                return PolicyDecisionModel(
                    decision="review_required",
                    reason=f"Too many files changed ({len(context.changed_files)}), requires human review",
                    constraints={"max_files_changed": 20}
                )
            
            # Check for restricted paths
            restricted_paths = [".github/workflows/", "app/policy_gate.py", "requirements.txt"]
            for file_path in context.changed_files:
                if any(file_path.startswith(restricted) for restricted in restricted_paths):
                    return PolicyDecisionModel(
                        decision="review_required",
                        reason=f"Changes to restricted path '{file_path}' require human review",
                        constraints={"restricted_paths": restricted_paths}
                    )
            
            # Check CI status
            if context.ci_status != "success":
                return PolicyDecisionModel(
                    decision="block",
                    reason=f"CI status is '{context.ci_status}', must be 'success' to proceed",
                    constraints={"required_ci_status": "success"}
                )
            
            # Check test results if available
            if context.test_results and not context.test_results.get("all_passed", False):
                return PolicyDecisionModel(
                    decision="block",
                    reason="Not all tests passed, cannot proceed with deployment",
                    constraints={"required_test_status": "all_passed"}
                )
            
            decision = PolicyDecisionModel(
                decision="allow",
                reason="Implementation changes meet all policy requirements",
                constraints={
                    "files_changed": len(context.changed_files),
                    "ci_status": context.ci_status,
                    "tests_passed": context.test_results.get("all_passed", True) if context.test_results else True
                }
            )
            
            # Record decision for audit trail (GitHub comments provide audit trail)
            logger.info(f"Policy decision for trace_id {trace_id}, implementation review: {decision.decision}")
            
            return decision
            
        except Exception as e:
            logger.error(f"Implementation change evaluation failed for trace_id {trace_id}: {str(e)}")
            return PolicyDecisionModel(
                decision="block",
                reason=f"Change evaluation error: {str(e)}",
                constraints={"error": "change_evaluation_failed"}
            )
    
    def _is_valid_stage(self, stage: str) -> bool:
        """Check if the stage is valid."""
        return stage in self._stage_constraints
    
    def _is_request_type_allowed(self, request_type: str, stage: str) -> bool:
        """Check if request type is allowed for the stage."""
        allowed_types = self._stage_constraints[stage]["allowed_request_types"]
        return request_type in allowed_types
    
    def _is_source_allowed(self, source: str, stage: str) -> bool:
        """Check if source is allowed for the stage."""
        source_policy = self._stage_constraints[stage]["source_policy"]
        if source_policy == "all_allowed":
            return True
        elif source_policy == "user_only":
            return source == "user"
        elif source_policy == "monitor_requires_review":
            return source == "user"  # monitor sources will trigger review_required
        return False
    
    def _evaluate_content_appropriateness(self, context: StageContext) -> Dict[str, Any]:
        """Evaluate if the issue content is appropriate for processing."""
        content = context.issue_content.lower()
        
        # Check for inappropriate content patterns
        inappropriate_patterns = [
            "delete everything",
            "rm -rf",
            "drop database",
            "format hard drive",
            "shutdown system",
            "hack",
            "exploit",
            "backdoor"
        ]
        
        for pattern in inappropriate_patterns:
            if pattern in content:
                return {
                    "decision": "block",
                    "reason": f"Content contains inappropriate pattern: '{pattern}'",
                    "constraints": {"blocked_patterns": inappropriate_patterns}
                }
        
        # Check for minimum content quality
        if len(context.issue_content.strip()) < 10:
            return {
                "decision": "block",
                "reason": "Issue content too short, minimum 10 characters required",
                "constraints": {"min_content_length": 10}
            }
        
        # Check for spam-like patterns
        if context.issue_content.count("!") > 10 or context.issue_content.count("?") > 10:
            return {
                "decision": "review_required",
                "reason": "Content appears spam-like, requires human review",
                "constraints": {"spam_indicators": "excessive_punctuation"}
            }
        
        return {"decision": "allow", "reason": "Content is appropriate", "constraints": {}}
    
    def _evaluate_stage_constraints(self, context: StageContext) -> Dict[str, Any]:
        """Evaluate stage-specific constraints."""
        stage_config = self._stage_constraints[context.current_stage]
        
        # Check priority requirements for prioritization stage
        if context.current_stage == "prioritize" and not context.priority:
            return {
                "decision": "block",
                "reason": "Priority information required for prioritization stage",
                "constraints": {"required_fields": ["priority"]}
            }
        
        # Check severity requirements for bug triage
        if (context.current_stage == "triage" and 
            context.request_type == "bug" and 
            not context.severity):
            return {
                "decision": "block",
                "reason": "Severity information required for bug triage",
                "constraints": {"required_fields": ["severity"]}
            }
        
        # Check workflow artifact requirements
        required_artifacts = stage_config.get("required_artifacts", [])
        missing_artifacts = [artifact for artifact in required_artifacts 
                           if artifact not in context.workflow_artifacts]
        
        if missing_artifacts:
            return {
                "decision": "block",
                "reason": f"Missing required artifacts: {', '.join(missing_artifacts)}",
                "constraints": {"required_artifacts": required_artifacts, "missing": missing_artifacts}
            }
        
        return {"decision": "allow", "reason": "Stage constraints satisfied", "constraints": {}}
    
    def _construct_constrained_prompt(self, context: StageContext) -> str:
        """Construct a policy-constrained prompt for Claude."""
        template = self._prompt_templates.get(context.current_stage, "")
        
        if not template:
            raise ValueError(f"No prompt template found for stage: {context.current_stage}")
        
        # Get stage-specific constraints
        constraints = self._stage_constraints[context.current_stage]
        
        # Build constraint text
        constraint_text = self._build_constraint_text(constraints)
        
        # Format the template with context and constraints
        prompt = template.format(
            request_type=context.request_type,
            source=context.source,
            issue_content=context.issue_content,
            trace_id=context.trace_id,
            constraints=constraint_text,
            priority=context.priority or "not specified",
            severity=context.severity or "not specified"
        )
        
        return prompt
    
    def _build_constraint_text(self, constraints: Dict[str, Any]) -> str:
        """Build human-readable constraint text."""
        constraint_parts = []
        
        if "scope_limits" in constraints:
            scope_limits = constraints["scope_limits"]
            constraint_parts.append(f"SCOPE LIMITS: {', '.join(scope_limits)}")
        
        if "output_format" in constraints:
            constraint_parts.append(f"OUTPUT FORMAT: {constraints['output_format']}")
        
        if "max_response_length" in constraints:
            constraint_parts.append(f"MAX RESPONSE LENGTH: {constraints['max_response_length']} characters")
        
        return "\n".join(constraint_parts)
    
    def _load_stage_constraints(self) -> Dict[str, Any]:
        """Load stage-specific constraints configuration."""
        return {
            "triage": {
                "allowed_request_types": ["bug", "feature", "investigate"],
                "source_policy": "all_allowed",
                "scope_limits": [
                    "analyze problem only",
                    "no code changes",
                    "no implementation suggestions",
                    "focus on understanding and clarification"
                ],
                "output_format": "structured triage report",
                "max_response_length": 2000,
                "required_artifacts": []
            },
            "plan": {
                "allowed_request_types": ["bug", "feature"],
                "source_policy": "all_allowed",
                "scope_limits": [
                    "create implementation plan only",
                    "no actual code implementation",
                    "focus on approach and design",
                    "include test strategy"
                ],
                "output_format": "structured implementation plan",
                "max_response_length": 3000,
                "required_artifacts": ["triage_report"]
            },
            "prioritize": {
                "allowed_request_types": ["bug", "feature"],
                "source_policy": "all_allowed",
                "scope_limits": [
                    "assess priority only",
                    "no implementation decisions",
                    "focus on value and effort analysis"
                ],
                "output_format": "priority recommendation with justification",
                "max_response_length": 1500,
                "required_artifacts": ["triage_report", "implementation_plan"]
            },
            "implement": {
                "allowed_request_types": ["bug", "feature"],
                "source_policy": "user_only",
                "scope_limits": [
                    "implement approved plan only",
                    "include comprehensive tests",
                    "follow existing code patterns",
                    "no architectural changes without approval"
                ],
                "output_format": "code implementation with tests",
                "max_response_length": 10000,
                "required_artifacts": ["triage_report", "implementation_plan", "priority_assessment", "human_approval"]
            }
        }
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """
        Load prompt templates for each stage from template files.
        
        Raises:
            TemplateLoadError: If any required template file is missing or cannot be loaded
        """
        templates = {}
        template_dir = Path(__file__).parent.parent / "templates" / "prompts"
        required_stages = ["triage", "plan", "prioritize", "implement"]
        
        # Validate template directory exists
        if not template_dir.exists():
            raise TemplateLoadError(
                f"Template directory not found: {template_dir}. "
                f"Create the directory and add template files for stages: {required_stages}"
            )
        
        # Load templates from files - fail fast if any are missing
        missing_templates = []
        load_errors = []
        
        for stage in required_stages:
            template_file = template_dir / f"{stage}.txt"
            
            if not template_file.exists():
                missing_templates.append(str(template_file))
                continue
            
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                    if not content:
                        load_errors.append(f"Template file is empty: {template_file}")
                        continue
                    
                    # Validate required variables are present
                    required_vars = ['{request_type}', '{source}', '{issue_content}', '{trace_id}', '{constraints}']
                    missing_vars = [var for var in required_vars if var not in content]
                    
                    if missing_vars:
                        load_errors.append(
                            f"Template {template_file} missing required variables: {missing_vars}"
                        )
                        continue
                    
                    templates[stage] = content
                    logger.info(f"Loaded prompt template for {stage} stage from {template_file}")
                    
            except Exception as e:
                load_errors.append(f"Failed to load template {template_file}: {str(e)}")
        
        # Fail fast if any templates are missing or invalid
        if missing_templates or load_errors:
            error_parts = []
            
            if missing_templates:
                error_parts.append(f"Missing template files: {missing_templates}")
            
            if load_errors:
                error_parts.append(f"Template load errors: {load_errors}")
            
            raise TemplateLoadError(
                f"Failed to load required prompt templates. {' | '.join(error_parts)}. "
                f"All templates must exist and be valid for stages: {required_stages}"
            )
        
        logger.info(f"Successfully loaded {len(templates)} prompt templates from {template_dir}")
        return templates
    
    def _construct_constrained_prompt(self, context: StageContext) -> str:
        """Construct a policy-constrained prompt for Claude."""
        template = self._prompt_templates.get(context.current_stage, "")
        
        if not template:
            raise TemplateLoadError(f"No prompt template found for stage: {context.current_stage}")
        
        # Get stage-specific constraints
        constraints = self._stage_constraints[context.current_stage]
        
        # Build constraint text
        constraint_text = self._build_constraint_text(constraints)
        
        # Format the template with context and constraints
        prompt = template.format(
            request_type=context.request_type,
            source=context.source,
            issue_content=context.issue_content,
            trace_id=context.trace_id,
            constraints=constraint_text,
            priority=context.priority or "not specified",
            severity=context.severity or "not specified"
        )
        
        return prompt
    
    def _build_constraint_text(self, constraints: Dict[str, Any]) -> str:
        """Build human-readable constraint text."""
        constraint_parts = []
        
        if "scope_limits" in constraints:
            scope_limits = constraints["scope_limits"]
            constraint_parts.append(f"SCOPE LIMITS: {', '.join(scope_limits)}")
        
        if "output_format" in constraints:
            constraint_parts.append(f"OUTPUT FORMAT: {constraints['output_format']}")
        
        if "max_response_length" in constraints:
            constraint_parts.append(f"MAX RESPONSE LENGTH: {constraints['max_response_length']} characters")
        
        return "\n".join(constraint_parts)
    
    def _get_allowed_request_types(self, stage: str) -> list[str]:
        """Get allowed request types for a stage."""
        return self._stage_constraints.get(stage, {}).get("allowed_request_types", [])


def get_policy_gate_component() -> PolicyGateComponent:
    """Factory function to get PolicyGateComponent instance."""
    return PolicyGateComponent()