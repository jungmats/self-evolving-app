"""Tests for database configuration and models."""

import pytest
from sqlalchemy.orm import Session
from app.database import Request, get_db, create_tables
from datetime import datetime


def test_request_model_creation(test_db, client):
    """Test Request model can be created and saved."""
    from tests.conftest import TestingSessionLocal
    
    db = TestingSessionLocal()
    
    # Create a test request
    request = Request(
        trace_id="test-trace-123",
        request_type="bug",
        source="user",
        title="Test Bug Report",
        description="This is a test bug report"
    )
    
    db.add(request)
    db.commit()
    db.refresh(request)
    
    # Verify the request was saved
    assert request.id is not None
    assert request.trace_id == "test-trace-123"
    assert request.request_type == "bug"
    assert request.source == "user"
    assert request.title == "Test Bug Report"
    assert request.description == "This is a test bug report"
    assert request.created_at is not None
    assert request.updated_at is not None
    
    db.close()


def test_request_model_unique_trace_id(test_db, client):
    """Test Request model enforces unique trace_id constraint."""
    from tests.conftest import TestingSessionLocal
    
    db = TestingSessionLocal()
    
    # Create first request
    request1 = Request(
        trace_id="duplicate-trace",
        request_type="bug",
        source="user",
        title="First Request",
        description="First description"
    )
    db.add(request1)
    db.commit()
    
    # Try to create second request with same trace_id
    request2 = Request(
        trace_id="duplicate-trace",
        request_type="feature",
        source="user",
        title="Second Request",
        description="Second description"
    )
    db.add(request2)
    
    # Should raise integrity error
    with pytest.raises(Exception):
        db.commit()
    
    db.close()


def test_database_connection(client):
    """Test database connection through health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["database"] == "connected"