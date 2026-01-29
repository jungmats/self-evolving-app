#!/usr/bin/env python3
"""Development server startup script."""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("Starting Self-Evolving Web Application...")
    print("Server will be available at: http://localhost:8000")
    print("Health check endpoint: http://localhost:8000/health")
    print("API documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )