# Self-Evolving Web Application

A controlled automation system that enables continuous improvement through structured workflows.

## Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation
```bash
pip install -r requirements.txt
```

### Running the Server
```bash
python3 run_server.py
```

The server will be available at:
- Main application: http://localhost:8000
- Health check: http://localhost:8000/health
- API documentation: http://localhost:8000/docs

### Running Tests
```bash
python3 -m pytest tests/ -v
```

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   └── database.py      # Database models and configuration
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # Test configuration
│   ├── test_main.py     # API endpoint tests
│   └── test_database.py # Database model tests
├── requirements.txt     # Python dependencies
├── pytest.ini         # Test configuration
└── run_server.py       # Development server script
```

## Features Implemented

- ✅ FastAPI web server with health endpoint
- ✅ SQLAlchemy ORM with SQLite database
- ✅ Basic Request model for tracking submissions
- ✅ Comprehensive test suite with pytest + Hypothesis
- ✅ Development environment setup

## Health Check

The `/health` endpoint provides system status:

```json
{
    "status": "healthy",
    "database": "connected", 
    "service": "self-evolving-app"
}
```

## Next Steps

This foundation supports the implementation of:
- User request submission interface
- GitHub integration for issue creation
- Automated monitoring components
- Workflow orchestration
- Policy & gate components
- Deployment pipeline