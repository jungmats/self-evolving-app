"""Contract tests for GitHub Issue creation."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import get_db, Submission
from app.github_client import GitHubClient
from app.state_management import IssueStateManager, Stage, RequestType, Source
from tests.conftest import TestingSessionLocal, override_get_db


class TestGitHubIssueCreationContract:
    """Contract tests for GitHub Issue creation with specific inputs and expected labels."""

    @pytest.fixture
    def mock_github_client(self):
        """Create mock GitHub client for testing."""
        mock_client = Mock(spec=GitHubClient)
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.labels = []
        mock_client.create_issue.return_value = mock_issue
        mock_client.get_issue.return_value = mock_issue
        mock_client.set_issue_labels.return_value = None
        mock_client.add_issue_comment.return_value = None
        mock_client.ensure_labels_exist.return_value = None
        return mock_client

    @pytest.fixture
    def mock_state_manager(self, mock_github_client):
        """Create mock state manager for testing."""
        mock_manager = Mock(spec=IssueStateManager)
        mock_manager.ensure_repository_labels.return_value = None
        mock_manager.create_issue_with_initial_state.return_value = 123
        return mock_manager

    def test_bug_report_creates_github_issue_with_correct_labels(self, client, mock_github_client, mock_state_manager):
        """
        Contract Test: GitHub Issue Creation
        
        Test that bug report submission creates GitHub Issue with correct labels.
        **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
        """
        # Test data
        bug_report_data = {
            "title": "Application crashes on startup",
            "description": "The application fails to start when clicking the main button",
            "severity": "high"
        }
        
        # Mock the GitHub client and state manager
        with patch('app.main.get_github_client', return_value=mock_github_client), \
             patch('app.main.get_state_manager', return_value=mock_state_manager):
            
            # Submit bug report
            response = client.post("/api/submit/bug", json=bug_report_data)
            
            # Verify response
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["github_issue_id"] == 123
            assert "trace-" in response_data["trace_id"]
            assert "GitHub Issue created" in response_data["message"]
            
            # Verify GitHub Issue creation was called with correct parameters
            mock_state_manager.create_issue_with_initial_state.assert_called_once()
            call_args = mock_state_manager.create_issue_with_initial_state.call_args
            
            # Verify issue creation parameters
            assert call_args.kwargs['title'] == bug_report_data['title']
            assert call_args.kwargs['description'] == bug_report_data['description']
            assert call_args.kwargs['request_type'] == RequestType.BUG
            assert call_args.kwargs['source'] == Source.USER
            assert call_args.kwargs['severity'] == bug_report_data['severity']
            assert call_args.kwargs['trace_id'].startswith('trace-')
            
            # Verify repository labels were ensured
            mock_state_manager.ensure_repository_labels.assert_called_once()

    def test_feature_request_creates_github_issue_with_correct_labels(self, client, mock_github_client, mock_state_manager):
        """
        Contract Test: GitHub Issue Creation
        
        Test that feature request submission creates GitHub Issue with correct labels.
        **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
        """
        # Test data
        feature_request_data = {
            "title": "Add dark mode support",
            "description": "Users want a dark theme option for better usability",
            "priority": "medium"
        }
        
        # Mock the GitHub client and state manager
        with patch('app.main.get_github_client', return_value=mock_github_client), \
             patch('app.main.get_state_manager', return_value=mock_state_manager):
            
            # Submit feature request
            response = client.post("/api/submit/feature", json=feature_request_data)
            
            # Verify response
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["github_issue_id"] == 123
            assert "trace-" in response_data["trace_id"]
            assert "GitHub Issue created" in response_data["message"]
            
            # Verify GitHub Issue creation was called with correct parameters
            mock_state_manager.create_issue_with_initial_state.assert_called_once()
            call_args = mock_state_manager.create_issue_with_initial_state.call_args
            
            # Verify issue creation parameters
            assert call_args.kwargs['title'] == feature_request_data['title']
            assert call_args.kwargs['description'] == feature_request_data['description']
            assert call_args.kwargs['request_type'] == RequestType.FEATURE
            assert call_args.kwargs['source'] == Source.USER
            assert call_args.kwargs['priority'] == feature_request_data['priority']
            assert call_args.kwargs['trace_id'].startswith('trace-')
            
            # Verify repository labels were ensured
            mock_state_manager.ensure_repository_labels.assert_called_once()

    def test_github_issue_creation_with_trace_id_embedding(self, mock_github_client):
        """
        Contract Test: GitHub Issue Creation
        
        Test that Trace_ID is properly embedded in GitHub Issue body.
        **Validates: Requirements 1.4, 12.2**
        """
        # Setup
        state_manager = IssueStateManager(mock_github_client)
        test_trace_id = "trace-abc123def456"
        
        # Execute
        issue_number = state_manager.create_issue_with_initial_state(
            title="Test Issue",
            description="Test description",
            request_type=RequestType.BUG,
            source=Source.USER,
            trace_id=test_trace_id,
            severity="medium"
        )
        
        # Verify GitHub client was called correctly
        mock_github_client.create_issue.assert_called_once()
        call_args = mock_github_client.create_issue.call_args
        
        # Verify the enhanced description was passed (with severity)
        issue_body = call_args.kwargs['body']
        assert "**Severity**: medium" in issue_body
        assert "Test description" in issue_body
        
        # Verify Trace_ID was passed to create_issue (GitHub client will embed it)
        assert call_args.kwargs['trace_id'] == test_trace_id
        
        # Verify correct labels are applied
        labels = call_args.kwargs['labels']
        expected_labels = [
            RequestType.BUG.value,
            Source.USER.value,
            Stage.TRIAGE.value
        ]
        for expected_label in expected_labels:
            assert expected_label in labels

    def test_github_issue_creation_failure_handling(self, client, mock_github_client, mock_state_manager):
        """
        Contract Test: GitHub Issue Creation
        
        Test proper error handling when GitHub Issue creation fails.
        **Validates: Requirements 1.2, 1.3, 1.5**
        """
        from app.github_client import GitHubClientError
        
        # Test data
        bug_report_data = {
            "title": "Test bug report",
            "description": "Test description",
            "severity": "low"
        }
        
        # Mock GitHub client to raise error
        mock_state_manager.create_issue_with_initial_state.side_effect = GitHubClientError("GitHub API error")
        
        with patch('app.main.get_github_client', return_value=mock_github_client), \
             patch('app.main.get_state_manager', return_value=mock_state_manager):
            
            # Submit bug report
            response = client.post("/api/submit/bug", json=bug_report_data)
            
            # Verify response indicates failure but local submission succeeded
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is False
            assert response_data["github_issue_id"] is None
            assert "GitHub Issue creation failed" in response_data["message"]
            assert "trace-" in response_data["trace_id"]
            
            # Verify local submission was still created
            db = TestingSessionLocal()
            try:
                submission = db.query(Submission).filter(
                    Submission.trace_id == response_data["trace_id"]
                ).first()
                assert submission is not None
                assert submission.status == "failed"
                assert submission.github_issue_id is None
            finally:
                db.close()

    def test_database_stores_trace_id_issue_id_mapping(self, client, mock_github_client, mock_state_manager):
        """
        Contract Test: GitHub Issue Creation
        
        Test that database stores minimal trace_id ↔ issue_id mapping.
        **Validates: Requirements 1.4, 1.5, 12.1**
        """
        # Test data
        feature_request_data = {
            "title": "Test feature",
            "description": "Test description",
            "priority": "high"
        }
        
        # Mock successful GitHub Issue creation
        mock_state_manager.create_issue_with_initial_state.return_value = 456
        
        with patch('app.main.get_github_client', return_value=mock_github_client), \
             patch('app.main.get_state_manager', return_value=mock_state_manager):
            
            # Submit feature request
            response = client.post("/api/submit/feature", json=feature_request_data)
            
            # Verify response
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["github_issue_id"] == 456
            
            # Verify database mapping
            db = TestingSessionLocal()
            try:
                submission = db.query(Submission).filter(
                    Submission.trace_id == response_data["trace_id"]
                ).first()
                assert submission is not None
                assert submission.github_issue_id == 456
                assert submission.status == "submitted"
                assert submission.request_type == "feature"
                assert submission.source == "user"
            finally:
                db.close()

    def test_issue_creation_with_initial_triage_stage(self, mock_github_client):
        """
        Contract Test: GitHub Issue Creation
        
        Test that all created Issues start with stage:triage label.
        **Validates: Requirements 1.5, 3.2**
        """
        # Setup
        state_manager = IssueStateManager(mock_github_client)
        
        # Test both bug and feature request types
        test_cases = [
            (RequestType.BUG, Source.USER, "bug", "high"),
            (RequestType.FEATURE, Source.USER, "feature", "medium"),
            (RequestType.INVESTIGATE, Source.MONITOR, "investigate", None)
        ]
        
        for request_type, source, title_prefix, extra_param in test_cases:
            # Reset mock
            mock_github_client.reset_mock()
            
            # Execute
            kwargs = {
                'title': f"{title_prefix} issue",
                'description': f"Test {title_prefix} description",
                'request_type': request_type,
                'source': source,
                'trace_id': f"trace-{title_prefix}-123"
            }
            
            if extra_param and request_type == RequestType.BUG:
                kwargs['severity'] = extra_param
            elif extra_param and request_type == RequestType.FEATURE:
                kwargs['priority'] = extra_param
            
            state_manager.create_issue_with_initial_state(**kwargs)
            
            # Verify labels include initial triage stage
            call_args = mock_github_client.create_issue.call_args
            labels = call_args.kwargs['labels']
            
            assert Stage.TRIAGE.value in labels
            assert request_type.value in labels
            assert source.value in labels
            
            # Verify exactly one stage label
            stage_labels = [label for label in labels if label.startswith("stage:")]
            assert len(stage_labels) == 1
            assert stage_labels[0] == Stage.TRIAGE.value