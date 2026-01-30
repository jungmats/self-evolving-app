"""Property-based tests for state machine integrity."""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from unittest.mock import Mock, MagicMock
from app.state_management import (
    IssueStateManager, Stage, RequestType, Source, Priority,
    StateTransitionError
)
from app.github_client import GitHubClient


class TestStateMachineProperties:
    """Property tests for state machine integrity and transitions."""

    def create_mock_github_client(self):
        """Create a mock GitHub client for testing."""
        mock_client = Mock(spec=GitHubClient)
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.labels = []
        mock_client.create_issue.return_value = mock_issue
        mock_client.get_issue.return_value = mock_issue
        mock_client.set_issue_labels.return_value = None
        mock_client.add_issue_comment.return_value = None
        return mock_client

    def create_mock_issue_with_stage(self, stage: Stage):
        """Create a mock issue with a specific stage label."""
        mock_issue = Mock()
        mock_issue.number = 123
        mock_label = Mock()
        mock_label.name = stage.value
        mock_issue.labels = [mock_label]
        return mock_issue

    @given(
        request_type=st.sampled_from([RequestType.BUG, RequestType.FEATURE, RequestType.INVESTIGATE]),
        source=st.sampled_from([Source.USER, Source.MONITOR]),
        title=st.text(min_size=1, max_size=100),
        description=st.text(min_size=1, max_size=1000),
        trace_id=st.text(min_size=1, max_size=50)
    )
    def test_issue_creation_always_starts_with_triage_stage(
        self, request_type, source, title, description, trace_id
    ):
        """
        Feature: self-evolving-app, Property 5: State Machine Integrity
        
        For any valid issue creation parameters, the issue should always be created
        with the initial stage:triage label.
        **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
        """
        # Setup
        mock_client = self.create_mock_github_client()
        state_manager = IssueStateManager(mock_client)
        
        # Execute
        issue_number = state_manager.create_issue_with_initial_state(
            title=title,
            description=description,
            request_type=request_type,
            source=source,
            trace_id=trace_id
        )
        
        # Verify issue was created with correct initial labels
        mock_client.create_issue.assert_called_once()
        call_args = mock_client.create_issue.call_args
        
        # Check that initial labels include triage stage
        labels = call_args.kwargs['labels']
        assert Stage.TRIAGE.value in labels
        assert request_type.value in labels
        assert source.value in labels
        
        # Verify exactly one stage label is present
        stage_labels = [label for label in labels if label.startswith("stage:")]
        assert len(stage_labels) == 1
        assert stage_labels[0] == Stage.TRIAGE.value

    @given(
        current_stage=st.sampled_from(list(Stage)),
        target_stage=st.sampled_from(list(Stage))
    )
    def test_state_transitions_follow_valid_rules(self, current_stage, target_stage):
        """
        Feature: self-evolving-app, Property 5: State Machine Integrity
        
        For any state transition attempt, only valid transitions defined in the
        state machine should be allowed.
        **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
        """
        # Setup
        mock_client = self.create_mock_github_client()
        mock_client.get_issue.return_value = self.create_mock_issue_with_stage(current_stage)
        state_manager = IssueStateManager(mock_client)
        
        # Check if transition is valid according to state machine rules
        valid_transitions = state_manager.VALID_TRANSITIONS.get(current_stage, [])
        is_valid_transition = target_stage in valid_transitions
        
        # Execute and verify
        if is_valid_transition:
            # Valid transition should succeed
            try:
                state_manager.transition_issue_state(
                    issue_number=123,
                    new_stage=target_stage,
                    reason="Test transition",
                    trace_id="test-trace-123"
                )
                # Should not raise exception
                mock_client.set_issue_labels.assert_called_once()
            except StateTransitionError:
                pytest.fail(f"Valid transition {current_stage.value} -> {target_stage.value} was rejected")
        else:
            # Invalid transition should raise StateTransitionError
            with pytest.raises(StateTransitionError):
                state_manager.transition_issue_state(
                    issue_number=123,
                    new_stage=target_stage,
                    reason="Test transition",
                    trace_id="test-trace-123"
                )

    @given(
        stages=st.lists(
            st.sampled_from(list(Stage)),
            min_size=1,
            max_size=10
        )
    )
    def test_issue_maintains_exactly_one_stage_label(self, stages):
        """
        Feature: self-evolving-app, Property 5: State Machine Integrity
        
        For any sequence of valid state transitions, an issue should maintain
        exactly one stage:* label at all times.
        **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
        """
        # Setup
        mock_client = self.create_mock_github_client()
        state_manager = IssueStateManager(mock_client)
        
        # Start with triage stage
        current_stage = Stage.TRIAGE
        mock_client.get_issue.return_value = self.create_mock_issue_with_stage(current_stage)
        
        # Track label updates to verify exactly one stage label
        label_updates = []
        
        def capture_set_labels(issue_number, labels):
            label_updates.append(labels)
            # Update mock to reflect new labels
            mock_issue = self.create_mock_issue_with_stage(current_stage)
            # Add non-stage labels
            non_stage_labels = [Mock() for label in labels if not label.startswith("stage:")]
            stage_labels = [Mock() for label in labels if label.startswith("stage:")]
            for i, label in enumerate(stage_labels):
                stage_labels[i].name = label
            mock_issue.labels = non_stage_labels + stage_labels
            mock_client.get_issue.return_value = mock_issue
        
        mock_client.set_issue_labels.side_effect = capture_set_labels
        
        # Attempt transitions through the provided stages
        for target_stage in stages:
            valid_transitions = state_manager.VALID_TRANSITIONS.get(current_stage, [])
            
            if target_stage in valid_transitions:
                try:
                    state_manager.transition_issue_state(
                        issue_number=123,
                        new_stage=target_stage,
                        reason=f"Transition to {target_stage.value}",
                        trace_id="test-trace-123"
                    )
                    current_stage = target_stage
                except StateTransitionError:
                    # Skip invalid transitions
                    continue
        
        # Verify each label update maintains exactly one stage label
        for labels in label_updates:
            stage_labels = [label for label in labels if label.startswith("stage:")]
            assert len(stage_labels) == 1, f"Expected exactly 1 stage label, got {len(stage_labels)}: {stage_labels}"

    @given(
        priority=st.sampled_from([Priority.P0, Priority.P1, Priority.P2]),
        trace_id=st.text(min_size=1, max_size=50)
    )
    def test_priority_label_management_maintains_single_priority(self, priority, trace_id):
        """
        Feature: self-evolving-app, Property 5: State Machine Integrity
        
        For any priority assignment, an issue should maintain exactly one
        priority:* label at all times.
        **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
        """
        # Setup
        mock_client = self.create_mock_github_client()
        state_manager = IssueStateManager(mock_client)
        
        # Create mock issue with existing priority label
        mock_issue = Mock()
        mock_issue.number = 123
        existing_priority_label = Mock()
        existing_priority_label.name = "priority:p1"
        stage_label = Mock()
        stage_label.name = "stage:triage"
        mock_issue.labels = [existing_priority_label, stage_label]
        mock_client.get_issue.return_value = mock_issue
        
        # Track label updates
        updated_labels = []
        
        def capture_labels(issue_number, labels):
            updated_labels.extend(labels)
        
        mock_client.set_issue_labels.side_effect = capture_labels
        
        # Execute
        state_manager.add_priority_label(123, priority, trace_id)
        
        # Verify exactly one priority label is set
        priority_labels = [label for label in updated_labels if label.startswith("priority:")]
        assert len(priority_labels) == 1
        assert priority_labels[0] == priority.value

    def test_state_machine_transition_rules_completeness(self):
        """
        Feature: self-evolving-app, Property 5: State Machine Integrity
        
        Verify that the state machine transition rules are complete and consistent.
        **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
        """
        state_manager = IssueStateManager(Mock())
        
        # Every stage except DONE should have at least one valid transition
        for stage in Stage:
            if stage != Stage.DONE:
                valid_transitions = state_manager.VALID_TRANSITIONS.get(stage, [])
                assert len(valid_transitions) > 0, f"Stage {stage.value} has no valid transitions"
        
        # BLOCKED stage should be able to transition back to TRIAGE for manual intervention
        blocked_transitions = state_manager.VALID_TRANSITIONS.get(Stage.BLOCKED, [])
        assert Stage.TRIAGE in blocked_transitions, "BLOCKED stage should allow transition back to TRIAGE"
        
        # TRIAGE should be the entry point (can be reached from BLOCKED)
        assert Stage.TRIAGE in state_manager.VALID_TRANSITIONS.get(Stage.BLOCKED, [])

    @given(
        trace_id=st.text(min_size=1, max_size=50),
        reason=st.text(min_size=1, max_size=200)
    )
    def test_state_transitions_always_create_audit_trail(self, trace_id, reason):
        """
        Feature: self-evolving-app, Property 5: State Machine Integrity
        
        For any valid state transition, an audit trail comment should be created
        with timestamp and Trace_ID.
        **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
        """
        # Setup
        mock_client = self.create_mock_github_client()
        mock_client.get_issue.return_value = self.create_mock_issue_with_stage(Stage.TRIAGE)
        state_manager = IssueStateManager(mock_client)
        
        # Execute valid transition
        state_manager.transition_issue_state(
            issue_number=123,
            new_stage=Stage.PLAN,  # Valid transition from TRIAGE
            reason=reason,
            trace_id=trace_id
        )
        
        # Verify audit comment was created
        mock_client.add_issue_comment.assert_called_once()
        comment_call = mock_client.add_issue_comment.call_args
        comment_text = comment_call.args[1]
        
        # Verify comment contains required audit information
        assert "State Transition" in comment_text
        assert trace_id in comment_text
        assert reason in comment_text
        assert "Timestamp" in comment_text
        assert Stage.TRIAGE.value in comment_text
        assert Stage.PLAN.value in comment_text