"""Pydantic models for API request/response validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
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


class StageContext(BaseModel):
    """Context information for policy evaluation."""
    issue_id: int
    current_stage: str
    request_type: str
    source: str
    priority: Optional[str] = None
    severity: Optional[str] = None
    trace_id: str
    issue_content: str
    workflow_artifacts: list[str] = Field(default_factory=list)


class ChangeContext(BaseModel):
    """Context information for implementation change evaluation."""
    changed_files: list[str]
    diff_stats: Dict[str, Any]
    ci_status: str
    test_results: Optional[Dict[str, Any]] = None


class PolicyDecisionModel(BaseModel):
    """Policy decision response model."""
    decision: str = Field(..., description="Policy decision: allow, review_required, or block")
    reason: str = Field(..., description="Explanation for the decision")
    constructed_prompt: Optional[str] = Field(None, description="Constrained prompt for Claude if decision is allow")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Applied constraints")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('decision')
    @classmethod
    def validate_decision(cls, v):
        allowed_decisions = ['allow', 'review_required', 'block']
        if v not in allowed_decisions:
            raise ValueError(f'Decision must be one of: {", ".join(allowed_decisions)}')
        return v