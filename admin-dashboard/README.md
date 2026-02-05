# Admin Operations Dashboard

A pure frontend application for monitoring and managing the Self-Evolving Web Application system.

## Overview

The Admin Operations Dashboard is a completely independent React + TypeScript application that provides visibility into all requests, their current status, and approval controls. It communicates directly with the GitHub API without any backend dependencies.

## Architecture

- **Pure Frontend**: No backend server or database dependencies
- **Direct GitHub API Integration**: All data retrieved client-side from GitHub REST API
- **Independent Deployment**: Can be deployed separately or co-located with the Web Server
- **No Shared Code**: Completely separate from the Web Server component

## Features

- **Issues by Stage**: View issues grouped by workflow stage
- **Issues by Request Type**: View issues grouped by bug/feature/investigate
- **Pull Requests**: Monitor agent-created PRs with CI status
- **Approvals Required**: Approve or deny implementation and deployment requests
- **Workflow Runs**: Track recent workflow executions and their status

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your GitHub credentials
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Build for production:
   ```bash
   npm run build
   ```

## Environment Variables

- `VITE_GITHUB_TOKEN`: GitHub Personal Access Token with `repo` and `workflow` scopes
- `VITE_GITHUB_OWNER`: GitHub repository owner/organization
- `VITE_GITHUB_REPO`: GitHub repository name
- `VITE_GITHUB_API_BASE_URL`: GitHub API base URL (default: https://api.github.com)

## Deployment Options

### Option 1: Co-located with Web Server
Build the dashboard and serve static files from the Web Server:
```bash
npm run build
# Copy dist/ contents to Web Server static directory
```

### Option 2: Independent Deployment
Deploy to static hosting services (Netlify, Vercel, S3+CloudFront):
```bash
npm run build
# Deploy dist/ directory to hosting service
```

## Security

- GitHub token stored in environment variables (never in code)
- Token requires `repo` and `workflow` scopes
- Client-side token handling with secure storage
- CORS configuration for GitHub API requests
- Rate limiting awareness and handling

## Technology Stack

- React 18
- TypeScript
- Vite (build tool)
- Direct GitHub REST API integration
