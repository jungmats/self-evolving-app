"""Tests for main FastAPI application."""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns correct message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Self-Evolving Web Application"}


def test_health_check_endpoint(client: TestClient):
    """Test health check endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["service"] == "self-evolving-app"
    assert "error" not in data


def test_health_check_structure(client: TestClient):
    """Test health check response has required fields."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    required_fields = ["status", "database", "service"]
    for field in required_fields:
        assert field in data