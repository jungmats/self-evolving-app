# Technology Stack

## Backend

- **Framework**: FastAPI (Python 3.9+)
- **ASGI Server**: 
  - Development: uvicorn
  - Production: gunicorn with uvicorn workers
- **Database**: SQLite with SQLAlchemy ORM (designed for future PostgreSQL migration)
- **Testing**: pytest + Hypothesis (property-based testing)
- **Environment**: python-dotenv for configuration

## Frontend

### Public UI
- **Framework**: React 18 + TypeScript
- **Build Tool**: react-scripts (Create React App)
- **Dev Server**: Port 3000

### Admin Dashboard
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Dev Server**: Port 3001
- **Architecture**: Pure frontend with direct GitHub API integration (no backend dependency)

## GitHub Integration

- **API Client**: PyGithub
- **Authentication**: Personal Access Token (fine-grained)
- **Workflows**: GitHub Actions with Claude Code integration
- **State Management**: Label-based state machine

## Key Dependencies

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pytest==7.4.3
hypothesis==6.92.1
httpx==0.25.2
pytest-asyncio==0.21.1
PyGithub==1.59.1
python-dotenv==1.0.0
pydantic==2.5.0
```

## Common Commands

### Backend Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python3 run_server.py

# Run tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_main.py -v

# Run with coverage
python3 -m pytest tests/ -v --cov=app
```

### Frontend Development

```bash
# Public UI
cd frontend
npm install
npm start  # Runs on port 3000

# Admin Dashboard
cd admin-dashboard
npm install
npm run dev  # Runs on port 3001
npm test     # Run tests
npm run build  # Production build
```

## Environment Configuration

Required environment variables (`.env` file):

```bash
# GitHub Integration
GITHUB_TOKEN=<personal_access_token>
GITHUB_REPOSITORY=<owner/repo>

# Admin Dashboard (separate .env in admin-dashboard/)
VITE_GITHUB_TOKEN=<personal_access_token>
VITE_GITHUB_OWNER=<username_or_org>
VITE_GITHUB_REPO=<repository_name>
```

## Testing Configuration

- **Test Framework**: pytest with asyncio support
- **Property-Based Testing**: Hypothesis for generating test cases
- **Test Location**: `tests/` directory
- **Test Pattern**: `test_*.py` files
- **Configuration**: `pytest.ini` with verbose output and short tracebacks
- **Golden Files**: Contract tests use golden files in `tests/golden_files/`

## API Documentation

When server is running:
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health
