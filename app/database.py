"""Database configuration and models for the Self-Evolving Web Application."""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
import uuid

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Submission(Base):
    """Submission model for outbox-style tracking of user requests."""
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, unique=True, nullable=False, index=True)
    github_issue_id = Column(Integer, unique=True, nullable=True)
    request_type = Column(String, nullable=False)  # bug, feature
    source = Column(String, nullable=False, default="user")  # user, monitor
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, submitted, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Request(Base):
    """Request model for tracking user submissions and monitoring alerts."""
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, unique=True, nullable=False, index=True)
    github_issue_id = Column(Integer, unique=True, nullable=True)
    request_type = Column(String, nullable=False)  # bug, feature, investigate
    source = Column(String, nullable=False)  # user, monitor
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PolicyDecision(Base):
    """Policy decision model for audit trail of Policy & Gate Component decisions."""
    __tablename__ = "policy_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, nullable=False, index=True)
    stage = Column(String, nullable=False)  # triage, plan, prioritize, implement
    decision = Column(String, nullable=False)  # allow, review_required, block
    reason = Column(Text, nullable=False)
    constraints = Column(Text, nullable=True)  # JSON blob for constraint details
    created_at = Column(DateTime, default=datetime.utcnow)


class Deployment(Base):
    """Deployment model for tracking deployment history and status."""
    __tablename__ = "deployments"
    
    id = Column(Integer, primary_key=True, index=True)
    git_sha = Column(String, nullable=False, index=True)
    release_path = Column(String, nullable=False)
    status = Column(String, nullable=False)  # pending, success, failed, rolled_back
    deployment_time = Column(Integer, nullable=True)  # Duration in seconds
    health_check_result = Column(Text, nullable=True)  # JSON blob for health check details
    created_at = Column(DateTime, default=datetime.utcnow)


def generate_trace_id() -> str:
    """Generate a unique Trace_ID for tracking requests."""
    return f"trace-{uuid.uuid4().hex[:12]}"


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()