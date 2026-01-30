"""Property-based tests for Trace_ID functionality."""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.orm import Session
from app.database import Submission, generate_trace_id, Base
from tests.conftest import TestingSessionLocal, engine


class TestTraceIdProperties:
    """Property tests for Trace_ID generation and uniqueness."""

    def test_trace_id_generation_format(self):
        """
        Feature: self-evolving-app, Property 12: Traceability and Audit Trail
        
        Test that generated Trace_IDs follow the expected format.
        """
        trace_id = generate_trace_id()
        
        # Should start with "trace-" prefix
        assert trace_id.startswith("trace-")
        
        # Should have exactly 12 hex characters after prefix
        hex_part = trace_id[6:]  # Remove "trace-" prefix
        assert len(hex_part) == 12
        assert all(c in "0123456789abcdef" for c in hex_part)

    @given(st.integers(min_value=1, max_value=100))
    def test_trace_id_uniqueness_generation(self, num_ids):
        """
        Feature: self-evolving-app, Property 12: Traceability and Audit Trail
        
        For any number of generated Trace_IDs, each should be unique.
        **Validates: Requirements 12.1, 12.2**
        """
        generated_ids = set()
        
        for _ in range(num_ids):
            trace_id = generate_trace_id()
            assert trace_id not in generated_ids, f"Duplicate Trace_ID generated: {trace_id}"
            generated_ids.add(trace_id)
        
        # All IDs should be unique
        assert len(generated_ids) == num_ids

    @given(
        request_type=st.sampled_from(['bug', 'feature']),
        title=st.text(min_size=1, max_size=100),
        description=st.text(min_size=1, max_size=1000)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_submission_trace_id_uniqueness_database(self, request_type, title, description, test_db):
        """
        Feature: self-evolving-app, Property 12: Traceability and Audit Trail
        
        For any valid submission data, each submission should get a unique Trace_ID
        that is enforced at the database level.
        **Validates: Requirements 12.1, 12.2**
        """
        # Create test database session
        db = TestingSessionLocal()
        
        try:
            # Create first submission
            submission1 = Submission(
                trace_id=generate_trace_id(),
                request_type=request_type,
                title=title,
                description=description
            )
            db.add(submission1)
            db.commit()
            db.refresh(submission1)
            
            # Create second submission with different trace_id
            submission2 = Submission(
                trace_id=generate_trace_id(),
                request_type=request_type,
                title=title + " (second)",
                description=description + " (second)"
            )
            db.add(submission2)
            db.commit()
            db.refresh(submission2)
            
            # Verify both submissions have different trace_ids
            assert submission1.trace_id != submission2.trace_id
            
            # Verify both trace_ids are properly formatted
            assert submission1.trace_id.startswith("trace-")
            assert submission2.trace_id.startswith("trace-")
            
        finally:
            db.close()

    def test_trace_id_database_uniqueness_constraint(self, test_db):
        """
        Feature: self-evolving-app, Property 12: Traceability and Audit Trail
        
        Test that database enforces Trace_ID uniqueness constraint.
        **Validates: Requirements 12.1, 12.2**
        """
        db = TestingSessionLocal()
        
        try:
            # Create first submission
            trace_id = generate_trace_id()
            submission1 = Submission(
                trace_id=trace_id,
                request_type="bug",
                title="First submission",
                description="First description"
            )
            db.add(submission1)
            db.commit()
            
            # Try to create second submission with same trace_id
            submission2 = Submission(
                trace_id=trace_id,  # Same trace_id
                request_type="feature",
                title="Second submission",
                description="Second description"
            )
            db.add(submission2)
            
            # Should raise integrity error due to unique constraint
            with pytest.raises(Exception):
                db.commit()
                
        finally:
            db.close()