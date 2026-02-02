"""Contract tests for Claude workflow outputs with golden file validation."""

import pytest
import json
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch
from app.claude_client import ClaudeClient, ClaudeResponse, ClaudeClientError, ClaudeResponseValidationError
from datetime import datetime


class TestClaudeWorkflowOutputsContract:
    """Contract tests for Claude workflow output schemas with golden files."""

    @pytest.fixture
    def golden_file_path(self):
        """Path to the golden file containing expected Claude workflow output schemas."""
        return Path(__file__).parent / "golden_files" / "claude_workflow_outputs.json"

    @pytest.fixture
    def expected_output_schemas(self, golden_file_path):
        """Load expected Claude output schemas from golden file."""
        if not golden_file_path.exists():
            # Create golden file if it doesn't exist
            golden_file_path.parent.mkdir(exist_ok=True)
            golden_data = self._generate_golden_output_schemas()
            with open(golden_file_path, 'w') as f:
                json.dump(golden_data, f, indent=2)
        
        with open(golden_file_path, 'r') as f:
            return json.load(f)

    def _generate_golden_output_schemas(self) -> Dict[str, Any]:
        """Generate the expected golden file content for Claude workflow outputs."""
        return {
            "description": "Expected Claude workflow output schemas and validation rules",
            "version": "1.0",
            "triage_output_schema": {
                "required_sections": [
                    "Problem Summary",
                    "Suspected Cause",
                    "Clarifying Questions", 
                    "Recommendation"
                ],
                "validation_rules": {
                    "recommendation_must_contain": ["proceed", "block"],
                    "min_content_per_section": 10,
                    "max_total_length": 2000
                },
                "example_output": {
                    "problem_summary": "Application crashes when users click the main button during startup sequence",
                    "suspected_cause": "Null pointer exception in button event handler due to uninitialized component state",
                    "clarifying_questions": "What browser and version? Does this happen on all devices? Are there any console errors?",
                    "recommendation": "This issue should proceed to planning stage as it affects core functionality"
                }
            },
            "planning_output_schema": {
                "required_sections": [
                    "Proposed Approach",
                    "Affected Files",
                    "Acceptance Criteria",
                    "Unit Test Plan",
                    "Risks and Considerations",
                    "Effort Estimate"
                ],
                "validation_rules": {
                    "affected_files_min_length": 10,
                    "must_include_test_strategy": True,
                    "max_total_length": 3000
                },
                "example_output": {
                    "proposed_approach": "Add null checks and proper initialization order in the button component",
                    "affected_files": "frontend/src/components/MainButton.tsx, frontend/src/App.tsx",
                    "acceptance_criteria": "Button clicks work without crashes, proper error handling displays user-friendly messages",
                    "unit_test_plan": "Test button initialization, test click handlers, test error scenarios",
                    "risks_and_considerations": "Changes may affect other components that depend on button state",
                    "effort_estimate": "2-3 hours development, 1 hour testing"
                }
            },
            "prioritization_output_schema": {
                "required_sections": [
                    "Expected User Value",
                    "Implementation Effort",
                    "Risk Assessment", 
                    "Priority Recommendation",
                    "Justification"
                ],
                "validation_rules": {
                    "priority_must_contain": ["p0", "p1", "p2"],
                    "must_assess_user_impact": True,
                    "max_total_length": 1500
                },
                "example_output": {
                    "expected_user_value": "High - fixes critical functionality that prevents users from using the application",
                    "implementation_effort": "Medium - requires component changes and testing but no architectural changes",
                    "risk_assessment": "Low risk - isolated change with good test coverage",
                    "priority_recommendation": "p1 - high priority due to user impact",
                    "justification": "Critical bug affecting core functionality warrants high priority despite medium effort"
                }
            },
            "implementation_output_schema": {
                "required_elements": [
                    "code_blocks",
                    "test_coverage",
                    "error_handling"
                ],
                "validation_rules": {
                    "min_content_length": 100,
                    "must_contain_code": True,
                    "must_include_tests": True
                },
                "code_indicators": ["```", "def ", "class ", "function ", "const "],
                "test_indicators": ["test_", "describe(", "it(", "expect(", "assert"]
            },
            "response_metadata_schema": {
                "required_fields": [
                    "trace_id",
                    "model", 
                    "usage",
                    "timestamp",
                    "workflow_stage"
                ],
                "usage_fields": ["input_tokens", "output_tokens"],
                "timestamp_format": "ISO 8601"
            },
            "error_handling_requirements": {
                "api_errors": {
                    "timeout_handling": True,
                    "rate_limit_handling": True,
                    "authentication_error_handling": True
                },
                "validation_errors": {
                    "missing_sections": "ClaudeResponseValidationError",
                    "invalid_format": "ClaudeResponseValidationError",
                    "content_too_short": "ClaudeResponseValidationError"
                },
                "retry_behavior": {
                    "max_retries": 0,
                    "exponential_backoff": False
                }
            }
        }

    @pytest.fixture
    def mock_claude_response(self):
        """Create mock Claude CLI response for testing."""
        return {
            "content": [
                {
                    "type": "text",
                    "text": "- Problem Summary: Test problem summary\n- Suspected Cause: Test suspected cause\n- Clarifying Questions: Test questions\n- Recommendation: This should proceed to planning"
                }
            ],
            "model": "claude-3-sonnet-20240229",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50
            }
        }

    def create_claude_client(self):
        """Create a ClaudeClient instance for testing (deprecated)."""
        # This will raise an error since Claude API client is deprecated
        # Tests should use Claude CLI client instead
        try:
            return ClaudeClient()
        except ClaudeClientError:
            # Expected - Claude API client is deprecated
            return None

    def test_triage_output_schema_matches_golden_file(self, expected_output_schemas, mock_claude_response):
        """
        Contract Test: Claude Workflow Outputs
        
        Test that triage analysis output matches the expected schema.
        **Validates: Requirements 4.3, 5.2, 6.2**
        """
        # Setup
        expected_schema = expected_output_schemas["triage_output_schema"]
        required_sections = expected_schema["required_sections"]
        
        # Create valid triage response content
        triage_content = "\n".join([
            f"- {section}: Test content for {section.lower()} section with sufficient detail"
            for section in required_sections
        ])
        triage_content += "\n- Recommendation: This issue should proceed to planning stage"
        
        mock_claude_response["content"][0]["text"] = triage_content
        
        # Mock the API call
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_claude_response
            
            claude_client = self.create_claude_client()
            result = claude_client.triage_analysis("test prompt", "trace-test123")
            
            # Verify all required sections are present
            for section in required_sections:
                section_key = section.lower().replace(" ", "_")
                assert section_key in result, f"Missing required section: {section}"
                assert len(result[section_key]) >= expected_schema["validation_rules"]["min_content_per_section"]
            
            # Verify recommendation validation
            recommendation = result["recommendation"].lower()
            recommendation_keywords = expected_schema["validation_rules"]["recommendation_must_contain"]
            assert any(keyword in recommendation for keyword in recommendation_keywords), \
                f"Recommendation must contain one of: {recommendation_keywords}"
            
            # Verify metadata is present
            assert "_metadata" in result
            metadata = result["_metadata"]
            assert metadata["trace_id"] == "trace-test123"
            assert metadata["workflow_stage"] == "triage"

    def test_planning_output_schema_matches_golden_file(self, expected_output_schemas, mock_claude_response):
        """
        Contract Test: Claude Workflow Outputs
        
        Test that planning analysis output matches the expected schema.
        **Validates: Requirements 4.3, 5.2, 6.2**
        """
        # Setup
        expected_schema = expected_output_schemas["planning_output_schema"]
        required_sections = expected_schema["required_sections"]
        
        # Create valid planning response content
        planning_content = "\n".join([
            f"- {section}: Test content for {section.lower()} section with detailed information"
            for section in required_sections
        ])
        planning_content += "\n- Affected Files: app/main.py, tests/test_main.py, frontend/src/App.tsx"
        
        mock_claude_response["content"][0]["text"] = planning_content
        
        # Mock the API call
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_claude_response
            
            claude_client = self.create_claude_client()
            result = claude_client.planning_analysis("test prompt", "trace-test456")
            
            # Verify all required sections are present
            for section in required_sections:
                section_key = section.lower().replace(" ", "_")
                assert section_key in result, f"Missing required section: {section}"
            
            # Verify affected files validation
            affected_files = result["affected_files"]
            min_length = expected_schema["validation_rules"]["affected_files_min_length"]
            assert len(affected_files) >= min_length, \
                f"Affected files section too short (min {min_length} chars)"
            
            # Verify metadata is present
            assert "_metadata" in result
            metadata = result["_metadata"]
            assert metadata["trace_id"] == "trace-test456"
            assert metadata["workflow_stage"] == "planning"

    def test_prioritization_output_schema_matches_golden_file(self, expected_output_schemas, mock_claude_response):
        """
        Contract Test: Claude Workflow Outputs
        
        Test that prioritization analysis output matches the expected schema.
        **Validates: Requirements 4.3, 5.2, 6.2**
        """
        # Setup
        expected_schema = expected_output_schemas["prioritization_output_schema"]
        required_sections = expected_schema["required_sections"]
        
        # Create valid prioritization response content
        prioritization_content = "\n".join([
            f"- {section}: Test content for {section.lower()} section"
            for section in required_sections
        ])
        prioritization_content += "\n- Priority Recommendation: p1 - high priority based on analysis"
        
        mock_claude_response["content"][0]["text"] = prioritization_content
        
        # Mock the API call
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_claude_response
            
            claude_client = self.create_claude_client()
            result = claude_client.prioritization_analysis("test prompt", "trace-test789")
            
            # Verify all required sections are present
            for section in required_sections:
                section_key = section.lower().replace(" ", "_")
                assert section_key in result, f"Missing required section: {section}"
            
            # Verify priority recommendation validation
            priority_rec = result["priority_recommendation"].lower()
            valid_priorities = expected_schema["validation_rules"]["priority_must_contain"]
            assert any(priority in priority_rec for priority in valid_priorities), \
                f"Priority recommendation must contain one of: {valid_priorities}"
            
            # Verify metadata is present
            assert "_metadata" in result
            metadata = result["_metadata"]
            assert metadata["trace_id"] == "trace-test789"
            assert metadata["workflow_stage"] == "prioritization"

    def test_implementation_output_schema_matches_golden_file(self, expected_output_schemas, mock_claude_response):
        """
        Contract Test: Claude Workflow Outputs
        
        Test that implementation generation output matches the expected schema.
        **Validates: Requirements 4.3, 5.2, 6.2**
        """
        # Setup
        expected_schema = expected_output_schemas["implementation_output_schema"]
        
        # Create valid implementation response content with code
        implementation_content = """
        Here is the implementation:
        
        ```python
        def fix_button_issue():
            if button is not None:
                button.initialize()
                return True
            return False
        ```
        
        And the corresponding test:
        
        ```python
        def test_fix_button_issue():
            result = fix_button_issue()
            assert result is True
        ```
        """
        
        mock_claude_response["content"][0]["text"] = implementation_content
        
        # Mock the API call
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_claude_response
            
            claude_client = self.create_claude_client()
            result = claude_client.implementation_generation("test prompt", "trace-test101112")
            
            # Verify minimum content length
            content = result["implementation_content"]
            min_length = expected_schema["validation_rules"]["min_content_length"]
            assert len(content) >= min_length, f"Implementation content too short (min {min_length} chars)"
            
            # Verify code indicators are present
            code_indicators = expected_schema["code_indicators"]
            assert any(indicator in content for indicator in code_indicators), \
                f"Implementation must contain code indicators: {code_indicators}"
            
            # Verify test indicators are present (for comprehensive testing)
            test_indicators = expected_schema["test_indicators"]
            assert any(indicator in content for indicator in test_indicators), \
                f"Implementation should include test indicators: {test_indicators}"
            
            # Verify metadata is present
            assert "_metadata" in result
            metadata = result["_metadata"]
            assert metadata["trace_id"] == "trace-test101112"
            assert metadata["workflow_stage"] == "implementation"

    def test_response_metadata_schema_matches_golden_file(self, expected_output_schemas, mock_claude_response):
        """
        Contract Test: Claude Workflow Outputs
        
        Test that response metadata matches the expected schema.
        **Validates: Requirements 4.3, 5.2, 6.2**
        """
        # Setup
        expected_metadata = expected_output_schemas["response_metadata_schema"]
        required_fields = expected_metadata["required_fields"]
        
        # Create valid response content
        mock_claude_response["content"][0]["text"] = "- Problem Summary: Test\n- Suspected Cause: Test\n- Clarifying Questions: Test\n- Recommendation: proceed"
        
        # Mock the API call
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_claude_response
            
            claude_client = self.create_claude_client()
            result = claude_client.triage_analysis("test prompt", "trace-metadata-test")
            
            # Verify metadata structure
            assert "_metadata" in result
            metadata = result["_metadata"]
            
            # Verify all required fields are present
            for field in required_fields:
                assert field in metadata, f"Missing required metadata field: {field}"
            
            # Verify usage fields
            usage = metadata["usage"]
            usage_fields = expected_metadata["usage_fields"]
            for field in usage_fields:
                assert field in usage, f"Missing usage field: {field}"
            
            # Verify timestamp format (ISO 8601)
            timestamp = metadata["timestamp"]
            assert isinstance(timestamp, str), "Timestamp should be string"
            assert "T" in timestamp and ":" in timestamp, "Timestamp should be ISO 8601 format"

    def test_error_handling_matches_golden_file_requirements(self, expected_output_schemas):
        """
        Contract Test: Claude Workflow Outputs
        
        Test that error handling matches the golden file requirements.
        **Validates: Requirements 4.3, 5.2, 6.2**
        """
        # Setup
        expected_errors = expected_output_schemas["error_handling_requirements"]
        claude_client = self.create_claude_client()
        
        # Test API timeout error
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Request timeout")
            
            with pytest.raises(ClaudeClientError) as exc_info:
                claude_client.triage_analysis("test prompt", "trace-error-test")
            
            assert "timeout" in str(exc_info.value).lower() or "error" in str(exc_info.value).lower()
        
        # Test validation error for missing sections
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "content": [{"type": "text", "text": "Incomplete response"}],
                "model": "claude-3-sonnet-20240229",
                "usage": {"input_tokens": 10, "output_tokens": 5}
            }
            
            with pytest.raises(ClaudeResponseValidationError) as exc_info:
                claude_client.triage_analysis("test prompt", "trace-validation-test")
            
            expected_error_type = expected_errors["validation_errors"]["missing_sections"]
            assert exc_info.type.__name__ == expected_error_type
        
        # Test validation error for content too short
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "content": [{"type": "text", "text": "Short"}],
                "model": "claude-3-sonnet-20240229", 
                "usage": {"input_tokens": 10, "output_tokens": 5}
            }
            
            with pytest.raises(ClaudeResponseValidationError) as exc_info:
                claude_client.implementation_generation("test prompt", "trace-short-test")
            
            expected_error_type = expected_errors["validation_errors"]["content_too_short"]
            assert exc_info.type.__name__ == expected_error_type

    def test_claude_response_parsing_consistency(self, expected_output_schemas, mock_claude_response):
        """
        Contract Test: Claude Workflow Outputs
        
        Test that Claude response parsing is consistent across all workflow types.
        **Validates: Requirements 4.3, 5.2, 6.2**
        """
        claude_client = self.create_claude_client()
        
        # Test different response formats
        test_cases = [
            {
                "name": "array_content_format",
                "response": {
                    "content": [{"type": "text", "text": "- Problem Summary: Test\n- Suspected Cause: Test\n- Clarifying Questions: Test\n- Recommendation: proceed"}],
                    "model": "claude-3-sonnet-20240229",
                    "usage": {"input_tokens": 100, "output_tokens": 50}
                }
            },
            {
                "name": "string_content_format", 
                "response": {
                    "content": "- Problem Summary: Test\n- Suspected Cause: Test\n- Clarifying Questions: Test\n- Recommendation: proceed",
                    "model": "claude-3-sonnet-20240229",
                    "usage": {"input_tokens": 100, "output_tokens": 50}
                }
            }
        ]
        
        for test_case in test_cases:
            with patch('requests.post') as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = test_case["response"]
                
                # Test that both formats work
                result = claude_client.triage_analysis("test prompt", f"trace-{test_case['name']}")
                
                # Verify consistent structure
                assert "_metadata" in result
                assert "problem_summary" in result
                assert "suspected_cause" in result
                assert "clarifying_questions" in result
                assert "recommendation" in result
                
                # Verify metadata consistency
                metadata = result["_metadata"]
                assert metadata["model"] == test_case["response"]["model"]
                assert metadata["usage"] == test_case["response"]["usage"]

    def test_golden_file_version_compatibility(self, expected_output_schemas):
        """
        Contract Test: Claude Workflow Outputs
        
        Test that the golden file version is compatible with the current implementation.
        **Validates: Requirements 4.3, 5.2, 6.2**
        """
        # Verify golden file has required structure
        required_keys = [
            "description", "version", "triage_output_schema", "planning_output_schema",
            "prioritization_output_schema", "implementation_output_schema", 
            "response_metadata_schema", "error_handling_requirements"
        ]
        
        for key in required_keys:
            assert key in expected_output_schemas, f"Golden file missing required key: {key}"
        
        # Verify version format
        version = expected_output_schemas["version"]
        assert isinstance(version, str), "Version should be a string"
        assert "." in version, "Version should follow semantic versioning (e.g., '1.0')"
        
        # Verify each workflow schema has required structure
        workflow_schemas = [
            "triage_output_schema", "planning_output_schema", 
            "prioritization_output_schema", "implementation_output_schema"
        ]
        
        for schema_name in workflow_schemas:
            schema = expected_output_schemas[schema_name]
            assert isinstance(schema, dict), f"{schema_name} should be a dictionary"
            
            if schema_name != "implementation_output_schema":
                assert "required_sections" in schema, f"{schema_name} missing required_sections"
                assert isinstance(schema["required_sections"], list), f"{schema_name} required_sections should be a list"
            
            assert "validation_rules" in schema, f"{schema_name} missing validation_rules"
            assert isinstance(schema["validation_rules"], dict), f"{schema_name} validation_rules should be a dictionary"