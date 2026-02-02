"""Property-based tests for Policy & Gate Component decision determinism."""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import Mock
from app.policy_gate import PolicyGateComponent
from app.models import StageContext, ChangeContext


class TestPolicyDecisionProperties:
    """Property tests for Policy & Gate Component decision determinism."""

    def create_policy_component(self):
        """Create a PolicyGateComponent instance for testing."""
        return PolicyGateComponent(db_session=None)

    @given(
        issue_id=st.integers(min_value=1, max_value=10000),
        current_stage=st.sampled_from(["triage", "plan", "prioritize", "implement"]),
        request_type=st.sampled_from(["bug", "feature", "investigate"]),
        source=st.sampled_from(["user", "monitor"]),
        trace_id=st.text(min_size=1, max_size=50),
        issue_content=st.text(min_size=10, max_size=1000)
    )
    def test_policy_decision_determinism_same_inputs(
        self, issue_id, current_stage, request_type, source, trace_id, issue_content
    ):
        """
        Feature: self-evolving-app, Property 17: Policy Decision Determinism
        
        For any given set of identical inputs, the Policy & Gate Component should
        produce identical decisions with the same reasoning.
        **Validates: Requirements 16.4, 16.6, 16.7**
        """
        # Setup
        policy_component = self.create_policy_component()
        
        # Create identical context objects
        context1 = StageContext(
            issue_id=issue_id,
            current_stage=current_stage,
            request_type=request_type,
            source=source,
            trace_id=trace_id,
            issue_content=issue_content,
            workflow_artifacts=[]
        )
        
        context2 = StageContext(
            issue_id=issue_id,
            current_stage=current_stage,
            request_type=request_type,
            source=source,
            trace_id=trace_id,
            issue_content=issue_content,
            workflow_artifacts=[]
        )
        
        # Execute policy evaluation twice with identical inputs
        decision1 = policy_component.evaluate_stage_transition(context1)
        decision2 = policy_component.evaluate_stage_transition(context2)
        
        # Verify decisions are identical
        assert decision1.decision == decision2.decision
        assert decision1.reason == decision2.reason
        assert decision1.constraints == decision2.constraints
        
        # If decision is allow, constructed prompts should be identical
        if decision1.decision == "allow":
            assert decision1.constructed_prompt == decision2.constructed_prompt
            assert decision1.constructed_prompt is not None
            assert decision2.constructed_prompt is not None

    @given(
        current_stage=st.sampled_from(["triage", "plan", "prioritize", "implement"]),
        request_type=st.sampled_from(["bug", "feature", "investigate"]),
        source=st.sampled_from(["user", "monitor"]),
        issue_content=st.text(min_size=10, max_size=1000)
    )
    def test_policy_decision_consistency_across_trace_ids(
        self, current_stage, request_type, source, issue_content
    ):
        """
        Feature: self-evolving-app, Property 17: Policy Decision Determinism
        
        For any given stage, request type, source, and content, the policy decision
        should be consistent regardless of trace_id or issue_id.
        **Validates: Requirements 16.4, 16.6, 16.7**
        """
        # Setup
        policy_component = self.create_policy_component()
        
        # Create contexts with different trace_ids and issue_ids but same core attributes
        context1 = StageContext(
            issue_id=123,
            current_stage=current_stage,
            request_type=request_type,
            source=source,
            trace_id="trace-abc123",
            issue_content=issue_content,
            workflow_artifacts=[]
        )
        
        context2 = StageContext(
            issue_id=456,
            current_stage=current_stage,
            request_type=request_type,
            source=source,
            trace_id="trace-def456",
            issue_content=issue_content,
            workflow_artifacts=[]
        )
        
        # Execute policy evaluation
        decision1 = policy_component.evaluate_stage_transition(context1)
        decision2 = policy_component.evaluate_stage_transition(context2)
        
        # Core policy decision should be the same
        assert decision1.decision == decision2.decision
        assert decision1.reason == decision2.reason
        
        # Constraints should be identical (policy rules don't depend on trace_id/issue_id)
        assert decision1.constraints == decision2.constraints

    @given(
        stage=st.sampled_from(["triage", "plan", "prioritize", "implement"]),
        request_type=st.sampled_from(["bug", "feature", "investigate"]),
        source=st.sampled_from(["user", "monitor"])
    )
    def test_policy_decision_valid_stage_request_combinations(
        self, stage, request_type, source
    ):
        """
        Feature: self-evolving-app, Property 17: Policy Decision Determinism
        
        For any valid stage and request type combination, the policy component
        should make consistent decisions based on defined rules.
        **Validates: Requirements 16.4, 16.6, 16.7**
        """
        # Setup
        policy_component = self.create_policy_component()
        
        context = StageContext(
            issue_id=123,
            current_stage=stage,
            request_type=request_type,
            source=source,
            trace_id="trace-test123",
            issue_content="This is a valid test issue content for policy evaluation.",
            workflow_artifacts=[]
        )
        
        # Execute policy evaluation
        decision = policy_component.evaluate_stage_transition(context)
        
        # Decision should be one of the valid options
        assert decision.decision in ["allow", "review_required", "block"]
        
        # Reason should be non-empty
        assert len(decision.reason) > 0
        
        # Constraints should be a dictionary
        assert isinstance(decision.constraints, dict)
        
        # If decision is allow, constructed_prompt should be provided
        if decision.decision == "allow":
            assert decision.constructed_prompt is not None
            assert len(decision.constructed_prompt) > 0
            # Prompt should contain the trace_id for traceability
            assert context.trace_id in decision.constructed_prompt

    @given(
        inappropriate_content=st.sampled_from([
            "delete everything from the system",
            "rm -rf / --no-preserve-root",
            "drop database production",
            "format hard drive completely",
            "shutdown system immediately",
            "hack into the mainframe",
            "exploit security vulnerability",
            "install backdoor access"
        ])
    )
    def test_policy_blocks_inappropriate_content_deterministically(self, inappropriate_content):
        """
        Feature: self-evolving-app, Property 17: Policy Decision Determinism
        
        For any inappropriate content patterns, the policy component should
        consistently block the request with clear reasoning.
        **Validates: Requirements 16.4, 16.6, 16.7**
        """
        # Setup
        policy_component = self.create_policy_component()
        
        context = StageContext(
            issue_id=123,
            current_stage="triage",
            request_type="bug",
            source="user",
            trace_id="trace-test123",
            issue_content=inappropriate_content,
            workflow_artifacts=[]
        )
        
        # Execute policy evaluation
        decision = policy_component.evaluate_stage_transition(context)
        
        # Should always block inappropriate content
        assert decision.decision == "block"
        assert "inappropriate" in decision.reason.lower() or "pattern" in decision.reason.lower()
        assert "blocked_patterns" in decision.constraints

    @given(
        content_length=st.integers(min_value=1, max_value=9)
    )
    def test_policy_blocks_insufficient_content_deterministically(self, content_length):
        """
        Feature: self-evolving-app, Property 17: Policy Decision Determinism
        
        For any content below minimum length requirements, the policy component
        should consistently block with clear reasoning.
        **Validates: Requirements 16.4, 16.6, 16.7**
        """
        # Setup
        policy_component = self.create_policy_component()
        
        # Create content that's too short (less than 10 characters)
        short_content = "a" * content_length
        
        context = StageContext(
            issue_id=123,
            current_stage="triage",
            request_type="bug",
            source="user",
            trace_id="trace-test123",
            issue_content=short_content,
            workflow_artifacts=[]
        )
        
        # Execute policy evaluation
        decision = policy_component.evaluate_stage_transition(context)
        
        # Should always block insufficient content
        assert decision.decision == "block"
        assert "too short" in decision.reason.lower() or "minimum" in decision.reason.lower()
        assert "min_content_length" in decision.constraints
        assert decision.constraints["min_content_length"] == 10

    @given(
        changed_files=st.lists(st.text(min_size=1, max_size=50), min_size=21, max_size=50),
        ci_status=st.sampled_from(["success", "failure", "pending"])
    )
    def test_policy_change_evaluation_determinism(self, changed_files, ci_status):
        """
        Feature: self-evolving-app, Property 17: Policy Decision Determinism
        
        For any change context with too many files, the policy component should
        consistently require review regardless of other factors.
        **Validates: Requirements 16.4, 16.6, 16.7**
        """
        # Setup
        policy_component = self.create_policy_component()
        
        change_context = ChangeContext(
            changed_files=changed_files,
            diff_stats={"additions": 100, "deletions": 50},
            ci_status=ci_status
        )
        
        # Execute policy evaluation
        decision = policy_component.evaluate_implementation_changes(
            change_context, "trace-test123"
        )
        
        # Should always require review for too many files (>20)
        assert decision.decision == "review_required"
        assert "too many files" in decision.reason.lower()
        assert "max_files_changed" in decision.constraints
        assert decision.constraints["max_files_changed"] == 20

    @given(
        restricted_file=st.sampled_from([
            ".github/workflows/triage.yml",
            ".github/workflows/deploy.yml", 
            "app/policy_gate.py",
            "requirements.txt",
            ".github/workflows/implementation.yml"
        ])
    )
    def test_policy_blocks_restricted_path_changes_deterministically(self, restricted_file):
        """
        Feature: self-evolving-app, Property 17: Policy Decision Determinism
        
        For any changes to restricted paths, the policy component should
        consistently require review with clear reasoning.
        **Validates: Requirements 16.4, 16.6, 16.7**
        """
        # Setup
        policy_component = self.create_policy_component()
        
        change_context = ChangeContext(
            changed_files=[restricted_file, "app/main.py"],  # Include restricted file
            diff_stats={"additions": 10, "deletions": 5},
            ci_status="success"
        )
        
        # Execute policy evaluation
        decision = policy_component.evaluate_implementation_changes(
            change_context, "trace-test123"
        )
        
        # Should always require review for restricted paths
        assert decision.decision == "review_required"
        assert "restricted path" in decision.reason.lower()
        assert "restricted_paths" in decision.constraints

    def test_policy_decision_structure_consistency(self):
        """
        Feature: self-evolving-app, Property 17: Policy Decision Determinism
        
        All policy decisions should have consistent structure and required fields.
        **Validates: Requirements 16.4, 16.6, 16.7**
        """
        # Setup
        policy_component = self.create_policy_component()
        
        # Test various contexts
        contexts = [
            StageContext(
                issue_id=123,
                current_stage="triage",
                request_type="bug",
                source="user",
                trace_id="trace-test123",
                issue_content="Valid bug report content for testing policy decisions.",
                workflow_artifacts=[]
            ),
            StageContext(
                issue_id=456,
                current_stage="invalid_stage",  # Invalid stage
                request_type="feature",
                source="user",
                trace_id="trace-test456",
                issue_content="Valid feature request content.",
                workflow_artifacts=[]
            )
        ]
        
        for context in contexts:
            decision = policy_component.evaluate_stage_transition(context)
            
            # All decisions should have required fields
            assert hasattr(decision, 'decision')
            assert hasattr(decision, 'reason')
            assert hasattr(decision, 'constraints')
            assert hasattr(decision, 'timestamp')
            
            # Decision should be valid
            assert decision.decision in ["allow", "review_required", "block"]
            
            # Reason should be non-empty string
            assert isinstance(decision.reason, str)
            assert len(decision.reason) > 0
            
            # Constraints should be dictionary
            assert isinstance(decision.constraints, dict)
            
            # Timestamp should be datetime
            assert decision.timestamp is not None

    @given(
        stage=st.sampled_from(["triage", "plan", "prioritize", "implement"]),
        request_type=st.sampled_from(["bug", "feature"])
    )
    def test_policy_prompt_construction_determinism(self, stage, request_type):
        """
        Feature: self-evolving-app, Property 17: Policy Decision Determinism
        
        For any allowed stage and request type, constructed prompts should be
        deterministic and contain required constraint information.
        **Validates: Requirements 16.4, 16.6, 16.7**
        """
        # Setup
        policy_component = self.create_policy_component()
        
        context = StageContext(
            issue_id=123,
            current_stage=stage,
            request_type=request_type,
            source="user",
            trace_id="trace-test123",
            issue_content="This is a comprehensive test issue content that meets minimum length requirements for policy evaluation.",
            workflow_artifacts=[]
        )
        
        # Execute policy evaluation multiple times
        decision1 = policy_component.evaluate_stage_transition(context)
        decision2 = policy_component.evaluate_stage_transition(context)
        
        # If decisions are allow, prompts should be identical
        if decision1.decision == "allow" and decision2.decision == "allow":
            assert decision1.constructed_prompt == decision2.constructed_prompt
            
            # Prompt should contain required elements
            prompt = decision1.constructed_prompt
            assert context.trace_id in prompt
            assert context.request_type in prompt
            assert context.issue_content in prompt
            assert "CONSTRAINTS:" in prompt