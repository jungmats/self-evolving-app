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


## Admin Operations Dashboard

The Admin Operations Dashboard is a **pure frontend application** for monitoring and managing system operations.

### Key Features
- **Independent Architecture**: Completely separate from the Web Server component
- **Direct GitHub API Integration**: No backend dependencies
- **Tab-Based Interface**: Organized views for Issues, PRs, Approvals, and Workflows
- **Real-Time Monitoring**: Live data from GitHub API
- **Approval Controls**: Approve or deny implementation and deployment requests

### Quick Start

1. Navigate to admin dashboard:
   ```bash
   cd admin-dashboard
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your GitHub credentials:
   # - VITE_GITHUB_TOKEN: Personal Access Token with repo and workflow scopes
   # - VITE_GITHUB_OWNER: GitHub username or organization
   # - VITE_GITHUB_REPO: Repository name
   ```

4. Run development server:
   ```bash
   npm run dev
   ```

5. Access at: `http://localhost:3001`

### Deployment

The admin dashboard can be deployed in multiple ways:

1. **Co-located with Web Server** (recommended for development)
2. **Netlify** (static hosting)
3. **Vercel** (static hosting)
4. **AWS S3 + CloudFront** (static hosting)

See [Admin Dashboard Deployment Guide](admin-dashboard/DEPLOYMENT.md) for detailed instructions.

### Testing

Run admin dashboard tests:
```bash
cd admin-dashboard
npm test
```

### Documentation

- [Admin Dashboard README](admin-dashboard/README.md)
- [Deployment Guide](admin-dashboard/DEPLOYMENT.md)
