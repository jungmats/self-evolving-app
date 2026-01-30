"""Main FastAPI application for the Self-Evolving Web Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import create_tables, get_db, Submission, generate_trace_id
from app.models import BugReportRequest, FeatureRequestRequest, RequestResponse, StatusResponse
import uvicorn
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    create_tables()
    yield
    # Shutdown (if needed)


# Create FastAPI application
app = FastAPI(
    title="Self-Evolving Web Application",
    description="A controlled automation system for continuous improvement",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if frontend build exists
frontend_build_path = "frontend/build"
if os.path.exists(frontend_build_path):
    app.mount("/static", StaticFiles(directory=f"{frontend_build_path}/static"), name="static")


@app.get("/")
def read_root():
    """Root endpoint - serve React app if available, otherwise return JSON."""
    frontend_index = "frontend/build/index.html"
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    return {"message": "Self-Evolving Web Application"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint that verifies database connectivity."""
    try:
        # Test database connection by executing a simple query
        result = db.execute(text("SELECT 1")).fetchone()
        if result:
            return {
                "status": "healthy",
                "database": "connected",
                "service": "self-evolving-app"
            }
        else:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "service": "self-evolving-app",
                "error": "Database query returned no result"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "service": "self-evolving-app",
            "error": str(e)
        }


@app.post("/api/submit/bug", response_model=RequestResponse)
def submit_bug_report(bug_report: BugReportRequest, db: Session = Depends(get_db)):
    """Submit a bug report."""
    try:
        # Generate unique trace ID
        trace_id = generate_trace_id()
        
        # Create submission record
        submission = Submission(
            trace_id=trace_id,
            request_type="bug",
            source="user",
            title=bug_report.title,
            description=f"Severity: {bug_report.severity}\n\n{bug_report.description}",
            status="pending"
        )
        
        db.add(submission)
        db.commit()
        db.refresh(submission)
        
        return RequestResponse(
            success=True,
            trace_id=trace_id,
            message="Bug report submitted successfully",
            github_issue_id=None  # Will be set when GitHub issue is created
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit bug report: {str(e)}")


@app.post("/api/submit/feature", response_model=RequestResponse)
def submit_feature_request(feature_request: FeatureRequestRequest, db: Session = Depends(get_db)):
    """Submit a feature request."""
    try:
        # Generate unique trace ID
        trace_id = generate_trace_id()
        
        # Create submission record
        submission = Submission(
            trace_id=trace_id,
            request_type="feature",
            source="user",
            title=feature_request.title,
            description=f"Priority: {feature_request.priority}\n\n{feature_request.description}",
            status="pending"
        )
        
        db.add(submission)
        db.commit()
        db.refresh(submission)
        
        return RequestResponse(
            success=True,
            trace_id=trace_id,
            message="Feature request submitted successfully",
            github_issue_id=None  # Will be set when GitHub issue is created
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit feature request: {str(e)}")


@app.get("/api/status/{trace_id}", response_model=StatusResponse)
def get_request_status(trace_id: str, db: Session = Depends(get_db)):
    """Get the status of a submitted request by trace ID."""
    submission = db.query(Submission).filter(Submission.trace_id == trace_id).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return StatusResponse(
        trace_id=submission.trace_id,
        status=submission.status,
        request_type=submission.request_type,
        title=submission.title,
        github_issue_id=submission.github_issue_id,
        created_at=submission.created_at,
        updated_at=submission.updated_at
    )


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)