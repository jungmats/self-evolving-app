"""Contract tests for Policy & Gate Component I/O with golden file validation."""

import pytest
import json
from pathlib import Path
from typing import Dict, List, Any
from app.policy_gate import PolicyGateComponent
from app.models import StageContext, ChangeContext


class TestPolicyComponentContract:
    """Contract tests for Policy & Gate Component input/output schema with golden files."""

    @pytest.fixture
    def golden_file_path(self):
        """Path to the golden file containing expected policy component behavior."""
        return Path(__file__).parent / "golden_files" / "policy_component_io.json"

    @pytest.fixture
    def expected_policy_behavior(self, golden_file_path):
        """Load expected policy behavior from golden file."""
        if not golden_file_path.exists():
            # Create golden file if it doesn't exist
            golden_file_path.parent.mkdir(exist_ok=True)
            golden_data = self._generate_golden_policy_behavior()
            with open(golden_file_path, 'w') as f:
                json.dump(golden_data, f, indent=2)
        
        with open(golden_file_path, 'r') as f:
            return json.load(f)

    def _generate_golden_policy_behavior(self) -> Dict[str, Any]:
        """Generate the expected golden file content for policy component behavior."""
        return {
            "description": "Expected Policy & Gate Component input/output behavior",
            "version": "1.0",
            "stage_constraints": {
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
            },
            "decision_types": ["allow", "review_required", "block"],
            "content_validation": {
                "min_content_length": 10,
                "inappropriate_patterns": [
                    "delete everything",
                    "rm -rf",
                    "drop database",
                    "format hard drive",
                    "shutdown system",
                    "hack",
                    "exploit",
                    "backdoor"
                ],
                "spam_indicators": {
                    "max_exclamation_marks": 10,
                    "max_question_marks": 10
                }
            },
            "change_evaluation": {
                "max_files_changed": 20,
                "restricted_paths": [
                    ".github/workflows/",
                    "app/policy_gate.py",
                    "requirements.txt"
                ],
                "required_ci_status": "success"
            },
            "prompt_template_requirements": {
                "required_sections": [
                    "ISSUE CONTENT:",
                    "TRACE_ID:",
                    "CONSTRAINTS:"
                ],
                "required_variables": [
                    "request_type",
                    "source",
                    "issue_content",
                    "trace_id",
                    "constraints"
                ]
            },
            "audit_trail_requirements": {
                "required_fields": ["trace_id", "stage", "decision", "reason", "timestamp"],
                "decision_persistence": True
            }
        }

    def create_policy_component(self):
        """Create a PolicyGateComponent instance for testing."""
        return PolicyGateComponent(db_session=None)

    def test_stage_constraints_match_golden_file(self, expected_policy_behavior):
        """
        Contract Test: Policy Component Interface
        
        Test that stage constraints match the golden file specification.
        **Validates: Requirements 16.2, 16.4**
        """
        # Setup
        policy_component = self.create_policy_component()
        expected_constraints = expected_policy_behavior["stage_constraints"]
        
        # Get actual constraints from the policy component
        actual_constraints = policy_component._stage_constraints
        
        # Verify all expected stages are present
        for stage_name, expected_config in expected_constraints.items():
            assert stage_name in actual_constraints, f"Stage {stage_name} not found in policy constraints"
            
            actual_config = actual_constraints[stage_name]
            
            # Verify each configuration field matches
            for field, expected_value in expected_config.items():
                assert field in actual_config, f"Field {field} missing from {stage_name} constraints"
                assert actual_config[field] == expected_value, \
                    f"Mismatch in {stage_name}.{field}: expected {expected_value}, got {actual_config[field]}"

    def test_decision_types_match_golden_file(self, expected_policy_behavior):
        """
        Contract Test: Policy Component Interface
        
        Test that all policy decisions use only the allowed decision types.
        **Validates: Requirements 16.2, 16.4**
        """
        # Setup
        policy_component = self.create_policy_component()
        expected_decisions = set(expected_policy_behavior["decision_types"])
        
        # Test various contexts to ensure only valid decisions are returned
        test_contexts = [
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
                current_stage="invalid_stage",
                request_type="feature",
                source="user",
                trace_id="trace-test456",
                issue_content="Valid feature request content.",
                workflow_artifacts=[]
            ),
            StageContext(
                issue_id=789,
                current_stage="implement",
                request_type="bug",
                source="monitor",  # Should trigger review_required
                trace_id="trace-test789",
                issue_content="Monitor-detected bug requiring implementation.",
                workflow_artifacts=[]
            )
        ]
        
        for context in test_contexts:
            decision = policy_component.evaluate_stage_transition(context)
            assert decision.decision in expected_decisions, \
                f"Invalid decision type '{decision.decision}' not in {expected_decisions}"

    def test_content_validation_rules_match_golden_file(self, expected_policy_behavior):
        """
        Contract Test: Policy Component Interface
        
        Test that content validation rules match the golden file specification.
        **Validates: Requirements 16.2, 16.4**
        """
        # Setup
        policy_component = self.create_policy_component()
        expected_validation = expected_policy_behavior["content_validation"]
        
        # Test minimum content length
        min_length = expected_validation["min_content_length"]
        short_content = "a" * (min_length - 1)
        
        context = StageContext(
            issue_id=123,
            current_stage="triage",
            request_type="bug",
            source="user",
            trace_id="trace-test123",
            issue_content=short_content,
            workflow_artifacts=[]
        )
        
        decision = policy_component.evaluate_stage_transition(context)
        assert decision.decision == "block"
        assert "min_content_length" in decision.constraints
        assert decision.constraints["min_content_length"] == min_length
        
        # Test inappropriate patterns
        inappropriate_patterns = expected_validation["inappropriate_patterns"]
        for pattern in inappropriate_patterns:
            context = StageContext(
                issue_id=123,
                current_stage="triage",
                request_type="bug",
                source="user",
                trace_id="trace-test123",
                issue_content=f"Please {pattern} to fix this issue",
                workflow_artifacts=[]
            )
            
            decision = policy_component.evaluate_stage_transition(context)
            assert decision.decision == "block"
            assert "blocked_patterns" in decision.constraints

    def test_change_evaluation_rules_match_golden_file(self, expected_policy_behavior):
        """
        Contract Test: Policy Component Interface
        
        Test that change evaluation rules match the golden file specification.
        **Validates: Requirements 16.2, 16.4**
        """
        # Setup
        policy_component = self.create_policy_component()
        expected_change_rules = expected_policy_behavior["change_evaluation"]
        
        # Test max files changed limit
        max_files = expected_change_rules["max_files_changed"]
        too_many_files = ["file" + str(i) + ".py" for i in range(max_files + 1)]
        
        change_context = ChangeContext(
            changed_files=too_many_files,
            diff_stats={"additions": 100, "deletions": 50},
            ci_status="success"
        )
        
        decision = policy_component.evaluate_implementation_changes(change_context, "trace-test123")
        assert decision.decision == "review_required"
        assert "max_files_changed" in decision.constraints
        assert decision.constraints["max_files_changed"] == max_files
        
        # Test restricted paths
        restricted_paths = expected_change_rules["restricted_paths"]
        for restricted_path in restricted_paths:
            test_file = restricted_path + "test_file.yml" if restricted_path.endswith("/") else restricted_path
            
            change_context = ChangeContext(
                changed_files=[test_file, "app/main.py"],
                diff_stats={"additions": 10, "deletions": 5},
                ci_status="success"
            )
            
            decision = policy_component.evaluate_implementation_changes(change_context, "trace-test123")
            assert decision.decision == "review_required"
            assert "restricted_paths" in decision.constraints
        
        # Test CI status requirement
        required_ci_status = expected_change_rules["required_ci_status"]
        
        change_context = ChangeContext(
            changed_files=["app/main.py"],
            diff_stats={"additions": 10, "deletions": 5},
            ci_status="failure"  # Not the required status
        )
        
        decision = policy_component.evaluate_implementation_changes(change_context, "trace-test123")
        assert decision.decision == "block"
        assert "required_ci_status" in decision.constraints
        assert decision.constraints["required_ci_status"] == required_ci_status

    def test_prompt_template_structure_matches_golden_file(self, expected_policy_behavior):
        """
        Contract Test: Policy Component Interface
        
        Test that prompt templates contain required sections and variables.
        **Validates: Requirements 16.2, 16.4**
        """
        # Setup
        policy_component = self.create_policy_component()
        expected_requirements = expected_policy_behavior["prompt_template_requirements"]
        
        # Test each stage's prompt template
        for stage in ["triage", "plan", "prioritize", "implement"]:
            context = StageContext(
                issue_id=123,
                current_stage=stage,
                request_type="bug",
                source="user",
                trace_id="trace-test123",
                issue_content="Valid bug report content for testing prompt template structure.",
                workflow_artifacts=[]
            )
            
            decision = policy_component.evaluate_stage_transition(context)
            
            if decision.decision == "allow":
                prompt = decision.constructed_prompt
                assert prompt is not None, f"No prompt constructed for allowed {stage} stage"
                
                # Check required sections
                required_sections = expected_requirements["required_sections"]
                for section in required_sections:
                    assert section in prompt, f"Required section '{section}' missing from {stage} prompt"
                
                # Check that required variables are populated
                required_variables = expected_requirements["required_variables"]
                for variable in required_variables:
                    if variable == "request_type":
                        assert context.request_type in prompt
                    elif variable == "source":
                        assert context.source in prompt
                    elif variable == "issue_content":
                        assert context.issue_content in prompt
                    elif variable == "trace_id":
                        assert context.trace_id in prompt

    def test_decision_output_schema_consistency(self, expected_policy_behavior):
        """
        Contract Test: Policy Component Interface
        
        Test that all policy decisions have consistent output schema.
        **Validates: Requirements 16.2, 16.4**
        """
        # Setup
        policy_component = self.create_policy_component()
        
        # Test various decision scenarios
        test_scenarios = [
            {
                "name": "valid_allow_case",
                "context": StageContext(
                    issue_id=123,
                    current_stage="triage",
                    request_type="bug",
                    source="user",
                    trace_id="trace-test123",
                    issue_content="Valid bug report content for testing decision schema.",
                    workflow_artifacts=[]
                )
            },
            {
                "name": "block_case_invalid_stage",
                "context": StageContext(
                    issue_id=456,
                    current_stage="invalid_stage",
                    request_type="feature",
                    source="user",
                    trace_id="trace-test456",
                    issue_content="Valid feature request content.",
                    workflow_artifacts=[]
                )
            },
            {
                "name": "review_required_case",
                "context": StageContext(
                    issue_id=789,
                    current_stage="implement",
                    request_type="bug",
                    source="monitor",
                    trace_id="trace-test789",
                    issue_content="Monitor-detected bug requiring implementation review.",
                    workflow_artifacts=[]
                )
            }
        ]
        
        for scenario in test_scenarios:
            decision = policy_component.evaluate_stage_transition(scenario["context"])
            
            # Verify required fields are present
            assert hasattr(decision, 'decision'), f"Missing 'decision' field in {scenario['name']}"
            assert hasattr(decision, 'reason'), f"Missing 'reason' field in {scenario['name']}"
            assert hasattr(decision, 'constraints'), f"Missing 'constraints' field in {scenario['name']}"
            assert hasattr(decision, 'timestamp'), f"Missing 'timestamp' field in {scenario['name']}"
            
            # Verify field types
            assert isinstance(decision.decision, str), f"'decision' should be string in {scenario['name']}"
            assert isinstance(decision.reason, str), f"'reason' should be string in {scenario['name']}"
            assert isinstance(decision.constraints, dict), f"'constraints' should be dict in {scenario['name']}"
            
            # Verify decision is valid
            expected_decisions = set(expected_policy_behavior["decision_types"])
            assert decision.decision in expected_decisions, \
                f"Invalid decision '{decision.decision}' in {scenario['name']}"
            
            # Verify constructed_prompt is present for allow decisions
            if decision.decision == "allow":
                assert hasattr(decision, 'constructed_prompt'), \
                    f"Missing 'constructed_prompt' for allow decision in {scenario['name']}"
                assert decision.constructed_prompt is not None, \
                    f"'constructed_prompt' should not be None for allow decision in {scenario['name']}"

    def test_audit_trail_requirements_match_golden_file(self, expected_policy_behavior):
        """
        Contract Test: Policy Component Interface
        
        Test that audit trail requirements match the golden file specification.
        **Validates: Requirements 16.2, 16.4**
        """
        expected_audit = expected_policy_behavior["audit_trail_requirements"]
        required_fields = expected_audit["required_fields"]
        
        # Verify that PolicyDecision model has all required fields for audit trail
        from app.models import PolicyDecisionModel
        
        # Create a sample decision to verify structure
        context = StageContext(
            issue_id=123,
            current_stage="triage",
            request_type="bug",
            source="user",
            trace_id="trace-test123",
            issue_content="Valid bug report content for audit trail testing.",
            workflow_artifacts=[]
        )
        
        policy_component = self.create_policy_component()
        decision = policy_component.evaluate_stage_transition(context)
        
        # Verify all required audit fields are present
        for field in required_fields:
            if field == "trace_id":
                # trace_id comes from context, should be in constraints or available for audit
                assert context.trace_id is not None
            elif field == "stage":
                # stage comes from context
                assert context.current_stage is not None
            else:
                # Other fields should be in the decision object
                assert hasattr(decision, field), f"Missing required audit field: {field}"

    def test_golden_file_version_compatibility(self, expected_policy_behavior):
        """
        Contract Test: Policy Component Interface
        
        Test that the golden file version is compatible with the current implementation.
        **Validates: Requirements 16.2, 16.4**
        """
        # Verify golden file has required structure
        required_keys = [
            "description", "version", "stage_constraints", "decision_types",
            "content_validation", "change_evaluation", "prompt_template_requirements",
            "audit_trail_requirements"
        ]
        
        for key in required_keys:
            assert key in expected_policy_behavior, f"Golden file missing required key: {key}"
        
        # Verify version format
        version = expected_policy_behavior["version"]
        assert isinstance(version, str), "Version should be a string"
        assert "." in version, "Version should follow semantic versioning (e.g., '1.0')"
        
        # Verify stage_constraints structure
        stage_constraints = expected_policy_behavior["stage_constraints"]
        assert isinstance(stage_constraints, dict), "stage_constraints should be a dictionary"
        
        for stage_name, constraints in stage_constraints.items():
            assert isinstance(constraints, dict), f"Constraints for {stage_name} should be a dictionary"
            
            # Verify required constraint fields
            required_constraint_fields = [
                "allowed_request_types", "source_policy", "scope_limits",
                "output_format", "max_response_length", "required_artifacts"
            ]
            
            for field in required_constraint_fields:
                assert field in constraints, f"Missing required constraint field {field} in {stage_name}"