"""Main FastAPI application for the Self-Evolving Web Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import create_tables, get_db
import uvicorn


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


@app.get("/")
def read_root():
    """Root endpoint."""
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


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)