"""Pydantic models for API request/response validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class BugReportRequest(BaseModel):
    """Request model for bug report submission."""
    title: str = Field(..., min_length=1, max_length=200, description="Bug report title")
    description: str = Field(..., min_length=1, max_length=2000, description="Bug report description")
    severity: str = Field(..., description="Bug severity level")
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        allowed_severities = ['low', 'medium', 'high', 'critical']
        if v.lower() not in allowed_severities:
            raise ValueError(f'Severity must be one of: {", ".join(allowed_severities)}')
        return v.lower()


class FeatureRequestRequest(BaseModel):
    """Request model for feature request submission."""
    title: str = Field(..., min_length=1, max_length=200, description="Feature request title")
    description: str = Field(..., min_length=1, max_length=2000, description="Feature request description")
    priority: str = Field(..., description="Feature priority level")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        allowed_priorities = ['low', 'medium', 'high']
        if v.lower() not in allowed_priorities:
            raise ValueError(f'Priority must be one of: {", ".join(allowed_priorities)}')
        return v.lower()


class RequestResponse(BaseModel):
    """Response model for request submission."""
    success: bool
    trace_id: str
    message: str
    github_issue_id: Optional[int] = None


class StatusResponse(BaseModel):
    """Response model for request status."""
    trace_id: str
    status: str
    request_type: str
    title: str
    github_issue_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime