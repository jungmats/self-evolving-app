"""Contract tests for GitHub label transitions with golden file validation."""

import pytest
import json
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock
from app.state_management import IssueStateManager, Stage, StateTransitionError
from app.github_client import GitHubClient


class TestStateMachineTransitionsContract:
    """Contract tests for state machine transitions with golden file validation."""

    @pytest.fixture
    def golden_file_path(self):
        """Path to the golden file containing expected transition rules."""
        return Path(__file__).parent / "golden_files" / "state_machine_transitions.json"

    @pytest.fixture
    def expected_transitions(self, golden_file_path):
        """Load expected transitions from golden file."""
        if not golden_file_path.exists():
            # Create golden file if it doesn't exist
            golden_file_path.parent.mkdir(exist_ok=True)
            golden_data = self._generate_golden_transitions()
            with open(golden_file_path, 'w') as f:
                json.dump(golden_data, f, indent=2)
        
        with open(golden_file_path, 'r') as f:
            return json.load(f)

    def _generate_golden_transitions(self) -> Dict[str, Any]:
        """Generate the expected golden file content for state transitions."""
        return {
            "description": "Valid state machine transitions for the self-evolving app workflow",
            "version": "1.0",
            "transitions": {
                "stage:triage": ["stage:plan", "stage:blocked"],
                "stage:plan": ["stage:prioritize", "stage:blocked"],
                "stage:prioritize": ["stage:awaiting-implementation-approval"],
                "stage:awaiting-implementation-approval": ["stage:implement", "stage:blocked"],
                "stage:implement": ["stage:pr-opened", "stage:blocked"],
                "stage:pr-opened": ["stage:awaiting-deploy-approval"],
                "stage:awaiting-deploy-approval": ["stage:done", "stage:blocked"],
                "stage:blocked": ["stage:triage"],
                "stage:done": []
            },
            "initial_stage": "stage:triage",
            "terminal_stages": ["stage:done"],
            "recovery_stages": ["stage:blocked"],
            "approval_gates": [
                "stage:awaiting-implementation-approval",
                "stage:awaiting-deploy-approval"
            ]
        }

    def create_mock_github_client(self):
        """Create a mock GitHub client for testing."""
        mock_client = Mock(spec=GitHubClient)
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.labels = []
        mock_client.get_issue.return_value = mock_issue
        mock_client.set_issue_labels.return_value = None
        mock_client.add_issue_comment.return_value = None
        return mock_client

    def create_mock_issue_with_stage(self, stage_name: str):
        """Create a mock issue with a specific stage label."""
        mock_issue = Mock()
        mock_issue.number = 123
        mock_label = Mock()
        mock_label.name = stage_name
        mock_issue.labels = [mock_label]
        return mock_issue

    def test_state_machine_transitions_match_golden_file(self, expected_transitions):
        """
        Contract Test: State Machine Transitions
        
        Test that the implemented state machine transitions match the golden file specification.
        **Validates: Requirements 3.2, 3.3**
        """
        # Setup
        mock_client = self.create_mock_github_client()
        state_manager = IssueStateManager(mock_client)
        
        # Get actual transitions from the state manager
        actual_transitions = {}
        for stage in Stage:
            valid_transitions = state_manager.VALID_TRANSITIONS.get(stage, [])
            actual_transitions[stage.value] = [t.value for t in valid_transitions]
        
        # Compare with golden file
        expected_transition_rules = expected_transitions["transitions"]
        
        for stage_name, expected_targets in expected_transition_rules.items():
            assert stage_name in actual_transitions, f"Stage {stage_name} not found in implementation"
            
            actual_targets = actual_transitions[stage_name]
            assert set(actual_targets) == set(expected_targets), \
                f"Transition mismatch for {stage_name}: expected {expected_targets}, got {actual_targets}"

    def test_initial_stage_matches_golden_file(self, expected_transitions):
        """
        Contract Test: State Machine Transitions
        
        Test that the initial stage matches the golden file specification.
        **Validates: Requirements 3.2, 3.3**
        """
        expected_initial = expected_transitions["initial_stage"]
        
        # Verify that issues are created with the expected initial stage
        mock_client = self.create_mock_github_client()
        state_manager = IssueStateManager(mock_client)
        
        # The initial stage should be TRIAGE according to the golden file
        assert Stage.TRIAGE.value == expected_initial
        
        # Verify this is used in issue creation (tested indirectly through existing tests)
        # The create_issue_with_initial_state method should use Stage.TRIAGE

    def test_terminal_stages_match_golden_file(self, expected_transitions):
        """
        Contract Test: State Machine Transitions
        
        Test that terminal stages (no outgoing transitions) match the golden file.
        **Validates: Requirements 3.2, 3.3**
        """
        expected_terminal = expected_transitions["terminal_stages"]
        
        # Setup
        mock_client = self.create_mock_github_client()
        state_manager = IssueStateManager(mock_client)
        
        # Find actual terminal stages (stages with no valid transitions)
        actual_terminal = []
        for stage in Stage:
            valid_transitions = state_manager.VALID_TRANSITIONS.get(stage, [])
            if not valid_transitions:
                actual_terminal.append(stage.value)
        
        assert set(actual_terminal) == set(expected_terminal), \
            f"Terminal stages mismatch: expected {expected_terminal}, got {actual_terminal}"

    def test_recovery_stages_match_golden_file(self, expected_transitions):
        """
        Contract Test: State Machine Transitions
        
        Test that recovery stages (for manual intervention) match the golden file.
        **Validates: Requirements 3.2, 3.3**
        """
        expected_recovery = expected_transitions["recovery_stages"]
        
        # Setup
        mock_client = self.create_mock_github_client()
        state_manager = IssueStateManager(mock_client)
        
        # Verify that blocked stage can transition back to triage (recovery mechanism)
        blocked_transitions = state_manager.VALID_TRANSITIONS.get(Stage.BLOCKED, [])
        blocked_transition_values = [t.value for t in blocked_transitions]
        
        # Recovery stages should be able to restart the workflow
        for recovery_stage in expected_recovery:
            if recovery_stage == "stage:blocked":
                # Blocked stage should be able to transition back to triage
                assert Stage.TRIAGE.value in blocked_transition_values, \
                    "Blocked stage should allow transition back to triage for recovery"

    def test_approval_gates_match_golden_file(self, expected_transitions):
        """
        Contract Test: State Machine Transitions
        
        Test that approval gate stages match the golden file specification.
        **Validates: Requirements 3.2, 3.3**
        """
        expected_approval_gates = expected_transitions["approval_gates"]
        
        # These stages should exist in the state machine
        for gate_stage in expected_approval_gates:
            stage_enum = None
            for stage in Stage:
                if stage.value == gate_stage:
                    stage_enum = stage
                    break
            
            assert stage_enum is not None, f"Approval gate stage {gate_stage} not found in Stage enum"

    def test_all_valid_transitions_succeed(self, expected_transitions):
        """
        Contract Test: State Machine Transitions
        
        Test that all transitions defined in the golden file are valid in the implementation.
        **Validates: Requirements 3.2, 3.3**
        """
        # Setup
        mock_client = self.create_mock_github_client()
        state_manager = IssueStateManager(mock_client)
        
        expected_transition_rules = expected_transitions["transitions"]
        
        for from_stage_name, to_stage_names in expected_transition_rules.items():
            # Find the corresponding Stage enum
            from_stage = None
            for stage in Stage:
                if stage.value == from_stage_name:
                    from_stage = stage
                    break
            
            assert from_stage is not None, f"Stage {from_stage_name} not found in Stage enum"
            
            # Test each valid transition
            for to_stage_name in to_stage_names:
                to_stage = None
                for stage in Stage:
                    if stage.value == to_stage_name:
                        to_stage = stage
                        break
                
                assert to_stage is not None, f"Stage {to_stage_name} not found in Stage enum"
                
                # Mock the current issue state
                mock_client.get_issue.return_value = self.create_mock_issue_with_stage(from_stage_name)
                
                # This transition should succeed without raising StateTransitionError
                try:
                    state_manager.transition_issue_state(
                        issue_number=123,
                        new_stage=to_stage,
                        reason=f"Test transition from {from_stage_name} to {to_stage_name}",
                        trace_id="test-trace-123"
                    )
                except StateTransitionError as e:
                    pytest.fail(f"Valid transition {from_stage_name} -> {to_stage_name} failed: {e}")

    def test_invalid_transitions_are_rejected(self, expected_transitions):
        """
        Contract Test: State Machine Transitions
        
        Test that transitions not defined in the golden file are properly rejected.
        **Validates: Requirements 3.2, 3.3**
        """
        # Setup
        mock_client = self.create_mock_github_client()
        state_manager = IssueStateManager(mock_client)
        
        expected_transition_rules = expected_transitions["transitions"]
        
        # Test some known invalid transitions
        invalid_transitions = [
            ("stage:triage", "stage:implement"),  # Skip planning and prioritization
            ("stage:plan", "stage:implement"),    # Skip prioritization
            ("stage:done", "stage:triage"),       # Can't restart from done
            ("stage:pr-opened", "stage:plan"),    # Can't go backwards
        ]
        
        for from_stage_name, to_stage_name in invalid_transitions:
            # Verify this transition is not in the golden file
            expected_targets = expected_transition_rules.get(from_stage_name, [])
            if to_stage_name in expected_targets:
                continue  # Skip if it's actually valid according to golden file
            
            # Find the corresponding Stage enums
            from_stage = None
            to_stage = None
            for stage in Stage:
                if stage.value == from_stage_name:
                    from_stage = stage
                if stage.value == to_stage_name:
                    to_stage = stage
            
            if from_stage is None or to_stage is None:
                continue  # Skip if stages don't exist
            
            # Mock the current issue state
            mock_client.get_issue.return_value = self.create_mock_issue_with_stage(from_stage_name)
            
            # This transition should raise StateTransitionError
            with pytest.raises(StateTransitionError):
                state_manager.transition_issue_state(
                    issue_number=123,
                    new_stage=to_stage,
                    reason=f"Invalid test transition from {from_stage_name} to {to_stage_name}",
                    trace_id="test-trace-123"
                )

    def test_golden_file_version_compatibility(self, expected_transitions):
        """
        Contract Test: State Machine Transitions
        
        Test that the golden file version is compatible with the current implementation.
        **Validates: Requirements 3.2, 3.3**
        """
        # Verify golden file has required structure
        required_keys = ["description", "version", "transitions", "initial_stage", "terminal_stages"]
        for key in required_keys:
            assert key in expected_transitions, f"Golden file missing required key: {key}"
        
        # Verify version format
        version = expected_transitions["version"]
        assert isinstance(version, str), "Version should be a string"
        assert "." in version, "Version should follow semantic versioning (e.g., '1.0')"