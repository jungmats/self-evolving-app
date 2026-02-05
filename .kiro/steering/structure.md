# Project Structure

## Repository Layout

```
├── app/                          # Backend application (FastAPI)
│   ├── main.py                   # FastAPI app with endpoints
│   ├── database.py               # SQLAlchemy models and DB setup
│   ├── models.py                 # Pydantic models for API
│   ├── workflow_engine.py        # Workflow orchestration with Claude
│   ├── policy_gate.py            # Policy evaluation and constraints
│   ├── state_management.py       # GitHub label-based state machine
│   ├── github_client.py          # GitHub API integration
│   ├── claude_client.py          # Claude API client
│   ├── claude_cli_client.py      # Claude CLI client
│   └── claude_client_factory.py  # Client factory with fallback
│
├── frontend/                     # Public UI (React + TypeScript)
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── BugReportForm.tsx
│   │   │   ├── FeatureRequestForm.tsx
│   │   │   └── Modal.tsx
│   │   ├── App.tsx               # Main app component
│   │   ├── api.ts                # Backend API client
│   │   └── types.ts              # TypeScript types
│   └── public/
│
├── admin-dashboard/              # Admin operations dashboard
│   ├── src/
│   │   ├── api/                  # GitHub API client
│   │   │   └── GitHubAPIClient.ts
│   │   ├── components/           # Dashboard components
│   │   │   ├── Tabs.tsx
│   │   │   ├── IssuesByStageTab.tsx
│   │   │   ├── PullRequestsTab.tsx
│   │   │   ├── ApprovalsRequiredTab.tsx
│   │   │   └── WorkflowRunsTab.tsx
│   │   ├── context/              # React context
│   │   ├── types/                # TypeScript types
│   │   └── utils/                # Utility functions
│   └── scripts/
│       └── deploy.sh             # Deployment script
│
├── tests/                        # Test suite
│   ├── conftest.py               # Pytest fixtures
│   ├── golden_files/             # Contract test golden files
│   │   ├── claude_workflow_outputs.json
│   │   ├── policy_component_io.json
│   │   └── state_machine_transitions.json
│   ├── test_main.py              # API endpoint tests
│   ├── test_database.py          # Database tests
│   ├── test_workflow_orchestration.py
│   ├── test_policy_decision_properties.py
│   ├── test_state_machine_properties.py
│   └── test_*_contract.py        # Contract tests
│
├── templates/                    # Prompt templates
│   └── prompts/
│       ├── triage.txt
│       ├── plan.txt
│       ├── prioritize.txt
│       └── implement.txt
│
├── scripts/                      # Operational scripts
│   ├── bootstrap_github.py       # GitHub repository setup
│   ├── setup-runner.sh           # Self-hosted runner setup
│   └── validate-claude-cli-integration.py
│
├── docs/                         # Documentation
│   ├── self-evolving-app.md      # System specification
│   ├── setup_new_self_evolving_app.md
│   ├── pat-token-setup.md
│   └── policy-extension-guide.md
│
├── .github/                      # GitHub configuration
│   ├── workflows/                # GitHub Actions workflows
│   │   └── implementation.yml
│   └── ISSUE_TEMPLATE/           # Issue templates
│
├── .kiro/                        # Kiro configuration
│   ├── specs/                    # Feature specifications
│   └── steering/                 # AI assistant steering rules
│
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Test configuration
└── run_server.py                 # Development server entry point
```

## Key Architectural Patterns

### Backend Architecture

- **Layered Design**: API → Business Logic → Data Access
- **Dependency Injection**: FastAPI's `Depends()` for DB sessions and clients
- **Factory Pattern**: Client factories with fallback mechanisms
- **Policy-Constrained Automation**: All workflows evaluated by `PolicyGateComponent`
- **State Machine**: GitHub labels represent canonical workflow state

### Frontend Architecture

- **Component-Based**: Reusable React components
- **Type Safety**: TypeScript throughout
- **Separation of Concerns**: 
  - Public UI: User-facing request submission
  - Admin Dashboard: Independent operations monitoring

### Testing Architecture

- **Unit Tests**: Component and function-level tests
- **Property-Based Tests**: Hypothesis for invariant testing
- **Contract Tests**: Golden file validation for component interfaces
- **Integration Tests**: End-to-end workflow testing

## File Naming Conventions

- **Python**: `snake_case.py`
- **TypeScript/React**: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- **Tests**: `test_*.py` pattern
- **Configuration**: lowercase with extensions (`.env`, `pytest.ini`)

## Import Conventions

### Python
```python
# Standard library
import os
from typing import Dict, Any

# Third-party
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# Local application
from app.database import get_db
from app.models import BugReportRequest
```

### TypeScript
```typescript
// React and libraries
import React from 'react';
import { useState } from 'react';

// Local components
import { GitHubAPIClient } from './api/GitHubAPIClient';
import { Tabs } from './components/Tabs';
```

## Database Schema

- **Submission**: Local tracking of requests
  - `trace_id`: Unique identifier (UUID format)
  - `request_type`: bug, feature, investigate
  - `source`: user, monitor
  - `github_issue_id`: Link to GitHub Issue
  - `status`: pending, submitted, failed

## GitHub Artifacts

- **Issues**: Requests and events with labels
- **Pull Requests**: Implementation outputs
- **Labels**: State machine representation
- **Comments**: Workflow outputs and approvals
- **Workflow Runs**: Execution instances

## Configuration Files

- `.env`: Backend environment variables
- `admin-dashboard/.env`: Admin dashboard configuration
- `pytest.ini`: Test runner configuration
- `requirements.txt`: Python dependencies
- `package.json`: Node.js dependencies (per frontend)
