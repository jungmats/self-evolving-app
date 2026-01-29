"""Database configuration and models for the Self-Evolving Web Application."""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


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