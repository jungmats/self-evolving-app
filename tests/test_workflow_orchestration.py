"""Tests for workflow orchestration scripts."""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the .github/scripts directory to the Python path for testing
scripts_path = Path(__file__).parent.parent / ".github" / "scripts"
sys.path.insert(0, str(scripts_path))

from workflow_transition import SimpleWorkflowTransition


class TestWorkflowOrchestration:
    """Test workflow orchestration functionality."""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test-token',
            'GITHUB_REPOSITORY': 'test-owner/test-repo',
            'GITHUB_RUN_ID': '12345',
            'GITHUB_SERVER_URL': 'https://github.com'
        }):
            yield

    @pytest.fixture
    def mock_requests(self):
        """Mock requests module for API calls."""
        with patch('workflow_transition.requests') as mock_requests:
            yield mock_requests

    def test_simple_workflow_transition_initialization(self, mock_env_vars):
        """Test that SimpleWorkflowTransition initializes correctly with environment variables."""
        transition = SimpleWorkflowTransition()
        
        assert transition.token == 'test-token'
        assert transition.repository == 'test-owner/test-repo'
        assert 'Authorization' in transition.headers
        assert transition.headers['Authorization'] == 'token test-token'

    def test_extract_trace_id_from_issue_body(self, mock_env_vars):
        """Test Trace_ID extraction from issue body."""
        transition = SimpleWorkflowTransition()
        
        # Test with proper Trace_ID format
        body_with_trace = "Issue description\n\n---\n**Trace_ID**: `trace-abc123def456`"
        trace_id = transition.extract_trace_id(body_with_trace)
        assert trace_id == "trace-abc123def456"
        
        # Test with fallback pattern
        body_with_fallback = "Issue description with trace-xyz789 in text"
        trace_id = transition.extract_trace_id(body_with_fallback)
        assert trace_id == "trace-xyz789"
        
        # Test with no Trace_ID
        body_without_trace = "Issue description without trace ID"
        trace_id = transition.extract_trace_id(body_without_trace)
        assert trace_id is None

    def test_successful_stage_transition(self, mock_env_vars, mock_requests):
        """Test successful stage transition with proper API calls."""
        # Setup mocks
        mock_issue_response = Mock()
        mock_issue_response.status_code = 200
        mock_issue_response.json.return_value = {
            'labels': [
                {'name': 'stage:triage'},
                {'name': 'request:bug'},
                {'name': 'source:user'}
            ],
            'body': '**Trace_ID**: `trace-test123`'
        }
        
        mock_labels_response = Mock()
        mock_labels_response.status_code = 200
        
        mock_comment_response = Mock()
        mock_comment_response.status_code = 201
        
        mock_requests.get.return_value = mock_issue_response
        mock_requests.put.return_value = mock_labels_response
        mock_requests.post.return_value = mock_comment_response
        
        # Execute
        transition = SimpleWorkflowTransition()
        success = transition.transition_stage(123, "stage:triage", "stage:plan", "triage")
        
        # Verify
        assert success is True
        
        # Verify API calls
        mock_requests.get.assert_called_once()
        mock_requests.put.assert_called_once()
        mock_requests.post.assert_called_once()
        
        # Verify labels were updated correctly
        labels_call = mock_requests.put.call_args
        updated_labels = labels_call.kwargs['json']['labels']
        assert 'stage:plan' in updated_labels
        assert 'stage:triage' not in updated_labels
        assert 'request:bug' in updated_labels  # Non-stage labels preserved
        assert 'source:user' in updated_labels

    def test_failed_stage_transition_handling(self, mock_env_vars, mock_requests):
        """Test handling of failed stage transitions."""
        # Setup mocks - simulate API failure
        mock_issue_response = Mock()
        mock_issue_response.status_code = 200
        mock_issue_response.json.return_value = {
            'labels': [{'name': 'stage:triage'}],
            'body': '**Trace_ID**: `trace-test123`'
        }
        
        mock_labels_response = Mock()
        mock_labels_response.status_code = 500
        mock_labels_response.text = "Internal Server Error"
        
        mock_requests.get.return_value = mock_issue_response
        mock_requests.put.return_value = mock_labels_response
        
        # Execute
        transition = SimpleWorkflowTransition()
        success = transition.transition_stage(123, "stage:triage", "stage:plan", "triage")
        
        # Verify
        assert success is False

    def test_add_progress_comment(self, mock_env_vars, mock_requests):
        """Test adding workflow progress comments."""
        # Setup mocks
        mock_issue_response = Mock()
        mock_issue_response.status_code = 200
        mock_issue_response.json.return_value = {
            'body': '**Trace_ID**: `trace-test123`'
        }
        
        mock_comment_response = Mock()
        mock_comment_response.status_code = 201
        
        mock_requests.get.return_value = mock_issue_response
        mock_requests.post.return_value = mock_comment_response
        
        # Execute
        transition = SimpleWorkflowTransition()
        success = transition.add_progress_comment(123, "triage", "started", "Beginning analysis")
        
        # Verify
        assert success is True
        
        # Verify comment was posted
        mock_requests.post.assert_called_once()
        comment_call = mock_requests.post.call_args
        comment_body = comment_call.kwargs['json']['body']
        
        assert "🚀 **Triage Workflow Started**" in comment_body
        assert "trace-test123" in comment_body
        assert "Beginning analysis" in comment_body
        assert "12345" in comment_body  # Workflow run ID

    def test_workflow_run_correlation(self, mock_env_vars, mock_requests):
        """Test that workflow run information is included in comments."""
        # Setup mocks
        mock_issue_response = Mock()
        mock_issue_response.status_code = 200
        mock_issue_response.json.return_value = {
            'labels': [{'name': 'stage:triage'}],
            'body': '**Trace_ID**: `trace-test123`'
        }
        
        mock_labels_response = Mock()
        mock_labels_response.status_code = 200
        
        mock_comment_response = Mock()
        mock_comment_response.status_code = 201
        
        mock_requests.get.return_value = mock_issue_response
        mock_requests.put.return_value = mock_labels_response
        mock_requests.post.return_value = mock_comment_response
        
        # Execute
        transition = SimpleWorkflowTransition()
        success = transition.transition_stage(123, "stage:triage", "stage:plan", "triage")
        
        # Verify
        assert success is True
        
        # Check that workflow run information is included
        comment_call = mock_requests.post.call_args
        comment_body = comment_call.kwargs['json']['body']
        
        assert "**Workflow Run**: [12345](https://github.com/test-owner/test-repo/actions/runs/12345)" in comment_body

    def test_state_machine_workflow_progression(self, mock_env_vars, mock_requests):
        """
        Test that the state machine works through the progression:
        triage → plan → prioritize → stage:awaiting-implementation-approval
        **Validates: Requirements 12.4, 3.2**
        """
        # Setup successful API responses
        def mock_get_issue(url, **kwargs):
            issue_id = url.split('/')[-1]
            if 'comments' in url:
                # Comment creation endpoint
                response = Mock()
                response.status_code = 201
                return response
            else:
                # Issue retrieval endpoint
                response = Mock()
                response.status_code = 200
                # Return different stage based on test progression
                if hasattr(mock_get_issue, 'call_count'):
                    mock_get_issue.call_count += 1
                else:
                    mock_get_issue.call_count = 1
                
                stages = ['stage:triage', 'stage:plan', 'stage:prioritize']
                current_stage = stages[min(mock_get_issue.call_count - 1, len(stages) - 1)]
                
                response.json.return_value = {
                    'labels': [{'name': current_stage}, {'name': 'request:bug'}],
                    'body': '**Trace_ID**: `trace-workflow-test`'
                }
                return response
        
        def mock_put_labels(url, **kwargs):
            response = Mock()
            response.status_code = 200
            return response
        
        def mock_post_comment(url, **kwargs):
            response = Mock()
            response.status_code = 201
            return response
        
        mock_requests.get.side_effect = mock_get_issue
        mock_requests.put.side_effect = mock_put_labels
        mock_requests.post.side_effect = mock_post_comment
        
        # Execute workflow progression
        transition = SimpleWorkflowTransition()
        
        # Step 1: Triage → Plan
        success1 = transition.transition_stage(123, "stage:triage", "stage:plan", "triage")
        assert success1 is True
        
        # Step 2: Plan → Prioritize  
        success2 = transition.transition_stage(123, "stage:plan", "stage:prioritize", "planning")
        assert success2 is True
        
        # Step 3: Prioritize → Awaiting Implementation Approval
        success3 = transition.transition_stage(123, "stage:prioritize", "stage:awaiting-implementation-approval", "prioritization")
        assert success3 is True
        
        # Verify all transitions succeeded
        assert all([success1, success2, success3])
        
        # Verify correct number of API calls were made
        # Each transition: 1 GET (issue) + 1 PUT (labels) + 1 POST (comment) = 3 calls each
        assert mock_requests.get.call_count == 3  # One GET per transition
        assert mock_requests.put.call_count == 3  # One PUT per transition  
        assert mock_requests.post.call_count == 3  # One POST per transition

    def test_trace_id_correlation_in_comments(self, mock_env_vars, mock_requests):
        """
        Test that Trace_ID is properly correlated in workflow comments.
        **Validates: Requirements 12.4**
        """
        test_trace_id = "trace-correlation-test-456"
        
        # Setup mocks
        mock_issue_response = Mock()
        mock_issue_response.status_code = 200
        mock_issue_response.json.return_value = {
            'body': f'Issue description\n\n**Trace_ID**: `{test_trace_id}`'
        }
        
        mock_comment_response = Mock()
        mock_comment_response.status_code = 201
        
        mock_requests.get.return_value = mock_issue_response
        mock_requests.post.return_value = mock_comment_response
        
        # Execute
        transition = SimpleWorkflowTransition()
        success = transition.add_progress_comment(123, "triage", "completed", "Analysis finished")
        
        # Verify
        assert success is True
        
        # Verify Trace_ID is included in comment
        comment_call = mock_requests.post.call_args
        comment_body = comment_call.kwargs['json']['body']
        
        assert f"**Trace_ID**: `{test_trace_id}`" in comment_body

    def test_error_handling_with_invalid_environment(self):
        """Test error handling when required environment variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GITHUB_TOKEN environment variable is required"):
                SimpleWorkflowTransition()
        
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'test-token'}, clear=True):
            with pytest.raises(ValueError, match="GITHUB_REPOSITORY environment variable is required"):
                SimpleWorkflowTransition()