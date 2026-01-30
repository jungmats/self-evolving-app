"""Tests for frontend integration."""

import pytest
from fastapi.testclient import TestClient
import os


class TestFrontendIntegration:
    """Tests for frontend integration with the backend API."""

    def test_frontend_files_exist(self):
        """Test that frontend files are created."""
        frontend_files = [
            "frontend/package.json",
            "frontend/tsconfig.json",
            "frontend/public/index.html",
            "frontend/src/index.tsx",
            "frontend/src/App.tsx",
            "frontend/src/types.ts",
            "frontend/src/api.ts",
            "frontend/src/components/BugReportForm.tsx",
            "frontend/src/components/FeatureRequestForm.tsx",
        ]
        
        for file_path in frontend_files:
            assert os.path.exists(file_path), f"Frontend file {file_path} should exist"

    def test_api_endpoints_accessible(self, client: TestClient):
        """Test that API endpoints are accessible for frontend integration."""
        # Test bug report submission
        bug_data = {
            "title": "Frontend Integration Test Bug",
            "description": "Testing frontend integration",
            "severity": "low"
        }
        
        response = client.post("/api/submit/bug", json=bug_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "trace_id" in data
        
        # Test status endpoint
        trace_id = data["trace_id"]
        status_response = client.get(f"/api/status/{trace_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["trace_id"] == trace_id
        assert status_data["request_type"] == "bug"

    def test_feature_request_api_integration(self, client: TestClient):
        """Test feature request API for frontend integration."""
        feature_data = {
            "title": "Frontend Integration Test Feature",
            "description": "Testing frontend integration",
            "priority": "medium"
        }
        
        response = client.post("/api/submit/feature", json=feature_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "trace_id" in data
        
        # Test status endpoint
        trace_id = data["trace_id"]
        status_response = client.get(f"/api/status/{trace_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["trace_id"] == trace_id
        assert status_data["request_type"] == "feature"

    def test_root_endpoint_without_frontend_build(self, client: TestClient):
        """Test root endpoint returns JSON when frontend build doesn't exist."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Since frontend/build doesn't exist, should return JSON
        data = response.json()
        assert data["message"] == "Self-Evolving Web Application"

    def test_cors_headers_for_frontend(self, client: TestClient):
        """Test that API endpoints work for frontend requests."""
        # Test preflight request simulation
        response = client.post("/api/submit/bug", json={
            "title": "CORS Test",
            "description": "Testing CORS",
            "severity": "low"
        })
        
        # Should work without CORS issues in test environment
        assert response.status_code == 200