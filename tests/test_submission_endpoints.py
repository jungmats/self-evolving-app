"""Tests for request submission endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.database import Submission
from tests.conftest import TestingSessionLocal


class TestSubmissionEndpoints:
    """Tests for bug report and feature request submission endpoints."""

    def test_submit_bug_report_success(self, client: TestClient):
        """Test successful bug report submission."""
        bug_data = {
            "title": "Test Bug Report",
            "description": "This is a test bug description",
            "severity": "medium"
        }
        
        response = client.post("/api/submit/bug", json=bug_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["trace_id"].startswith("trace-")
        assert data["message"] == "Bug report submitted successfully"
        assert data["github_issue_id"] is None
        
        # Verify submission was saved to database
        db = TestingSessionLocal()
        submission = db.query(Submission).filter(Submission.trace_id == data["trace_id"]).first()
        assert submission is not None
        assert submission.request_type == "bug"
        assert submission.source == "user"
        assert submission.title == "Test Bug Report"
        assert "Severity: medium" in submission.description
        assert submission.status == "pending"
        db.close()

    def test_submit_feature_request_success(self, client: TestClient):
        """Test successful feature request submission."""
        feature_data = {
            "title": "Test Feature Request",
            "description": "This is a test feature description",
            "priority": "high"
        }
        
        response = client.post("/api/submit/feature", json=feature_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["trace_id"].startswith("trace-")
        assert data["message"] == "Feature request submitted successfully"
        assert data["github_issue_id"] is None
        
        # Verify submission was saved to database
        db = TestingSessionLocal()
        submission = db.query(Submission).filter(Submission.trace_id == data["trace_id"]).first()
        assert submission is not None
        assert submission.request_type == "feature"
        assert submission.source == "user"
        assert submission.title == "Test Feature Request"
        assert "Priority: high" in submission.description
        assert submission.status == "pending"
        db.close()

    def test_submit_bug_report_validation_errors(self, client: TestClient):
        """Test bug report submission with validation errors."""
        # Test empty title
        bug_data = {
            "title": "",
            "description": "Valid description",
            "severity": "medium"
        }
        response = client.post("/api/submit/bug", json=bug_data)
        assert response.status_code == 422
        
        # Test invalid severity
        bug_data = {
            "title": "Valid title",
            "description": "Valid description",
            "severity": "invalid"
        }
        response = client.post("/api/submit/bug", json=bug_data)
        assert response.status_code == 422
        
        # Test missing required fields
        bug_data = {
            "title": "Valid title"
            # Missing description and severity
        }
        response = client.post("/api/submit/bug", json=bug_data)
        assert response.status_code == 422

    def test_submit_feature_request_validation_errors(self, client: TestClient):
        """Test feature request submission with validation errors."""
        # Test empty title
        feature_data = {
            "title": "",
            "description": "Valid description",
            "priority": "medium"
        }
        response = client.post("/api/submit/feature", json=feature_data)
        assert response.status_code == 422
        
        # Test invalid priority
        feature_data = {
            "title": "Valid title",
            "description": "Valid description",
            "priority": "invalid"
        }
        response = client.post("/api/submit/feature", json=feature_data)
        assert response.status_code == 422

    def test_get_request_status_success(self, client: TestClient):
        """Test successful request status retrieval."""
        # First submit a bug report
        bug_data = {
            "title": "Test Bug for Status",
            "description": "Test description",
            "severity": "low"
        }
        
        submit_response = client.post("/api/submit/bug", json=bug_data)
        trace_id = submit_response.json()["trace_id"]
        
        # Get status
        status_response = client.get(f"/api/status/{trace_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["trace_id"] == trace_id
        assert status_data["status"] == "pending"
        assert status_data["request_type"] == "bug"
        assert status_data["title"] == "Test Bug for Status"
        assert status_data["github_issue_id"] is None
        assert "created_at" in status_data
        assert "updated_at" in status_data

    def test_get_request_status_not_found(self, client: TestClient):
        """Test request status retrieval for non-existent trace ID."""
        response = client.get("/api/status/trace-nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"] == "Request not found"

    def test_severity_case_insensitive(self, client: TestClient):
        """Test that severity validation is case insensitive."""
        bug_data = {
            "title": "Test Bug",
            "description": "Test description",
            "severity": "HIGH"  # Uppercase
        }
        
        response = client.post("/api/submit/bug", json=bug_data)
        assert response.status_code == 200
        
        # Verify it was stored as lowercase
        db = TestingSessionLocal()
        trace_id = response.json()["trace_id"]
        submission = db.query(Submission).filter(Submission.trace_id == trace_id).first()
        assert "Severity: high" in submission.description
        db.close()

    def test_priority_case_insensitive(self, client: TestClient):
        """Test that priority validation is case insensitive."""
        feature_data = {
            "title": "Test Feature",
            "description": "Test description",
            "priority": "LOW"  # Uppercase
        }
        
        response = client.post("/api/submit/feature", json=feature_data)
        assert response.status_code == 200
        
        # Verify it was stored as lowercase
        db = TestingSessionLocal()
        trace_id = response.json()["trace_id"]
        submission = db.query(Submission).filter(Submission.trace_id == trace_id).first()
        assert "Priority: low" in submission.description
        db.close()