
# Self-Evolving Web Application – Specification (MVP)

## 1. Purpose and Goal

### Goal
Build an exploratory prototype that demonstrates a **controlled self-evolving application loop**:

1. Users and automated monitors submit bug reports or feature requests via a web application.
2. The application creates structured work items in GitHub (Issues with labels).
3. GitHub Actions workflows using Claude Code perform **triage → planning → prioritization → implementation** in staged steps.
4. Human approval is required **before implementation** and **before deployment**.
5. Merged changes are deployed via a GitHub-triggered, non-container deployment pipeline to a single server.

### Non-goals (MVP)
- No microservices or distributed event infrastructure.
- No separate event/audit database (GitHub is the system of record).
- No autonomous implementation or deployment without explicit human approval.
- No container-based deployment.

---

## 2. Expected Components

The system consists of the following components:

1. **Web Server (Backend + Public UI)**
   - Accepts bug reports and feature requests.
   - Hosts a minimal public UI.
   - Runs a periodic monitoring job.
   - Integrates with the GitHub API.

2. **Monitoring Component**
   - Periodically inspects logs/metrics for critical errors.
   - Deduplicates recurring incidents.
   - Creates GitHub Issues for detected problems.

3. **Workflow Component (GitHub Configuration)**
   - GitHub Actions workflows implementing the multi-stage pipeline.
   - Claude Code integration.
   - Issue templates and label taxonomy.

4. **Admin Ops Page (Level 0)**
   - Displays requests, stages, PRs, and workflow runs by querying GitHub APIs.
   - Provides human approval actions.

5. **Deployment Component**
   - GitHub-triggered deployment to a single server.
   - Versioned releases with atomic symlink switch.
   - Rollback support.

---

## 3. Technology Stack

### Backend
- Python + FastAPI
- ASGI:
  - Development: uvicorn
  - Production: gunicorn with uvicorn workers

### Database
- SQLite (MVP)
- ORM: SQLAlchemy or SQLModel
- Schema designed for future PostgreSQL migration

### Frontend
- React + TypeScript
- Minimal UI (public request forms + admin ops dashboard)

### GitHub Integration
- MVP: fine-grained Personal Access Token
- Recommended later: GitHub App with installation tokens

---

## 4. Repository Structure

Suggested layout:

- `backend/` – FastAPI backend service
- `frontend/` – React + TypeScript frontend
- `ops/` or `scripts/` – deployment and operational scripts
- `.github/workflows/` – GitHub Actions workflows
- `.github/ISSUE_TEMPLATE/` – issue templates
- `CLAUDE.md` – repository conventions and constraints for Claude Code

---

## 5. GitHub Artifact Model (System of Record)

### Core Artifacts
- **Issue**: request/event (bug, feature, investigation)
- **Pull Request**: implementation output
- **Workflow Run**: execution instance
- **Comment**: plans, prioritization, approvals, outcomes
- **Labels**: workflow state machine

### Label Taxonomy

#### Request Type
- `request:bug`
- `request:feature`
- `request:investigate`

#### Source
- `source:user`
- `source:monitor`

#### Severity / Priority
- `severity:critical`
- `severity:high`
- `severity:normal`
- `priority:p0`
- `priority:p1`
- `priority:p2`

#### Stages (State Machine)
- `stage:triage`
- `stage:plan`
- `stage:prioritize`
- `stage:awaiting-implementation-approval`
- `stage:implement`
- `stage:pr-opened`
- `stage:awaiting-deploy-approval`
- `stage:done`
- `stage:blocked`

#### Agent
- `agent:claude`

### Linking and Traceability
- PR body must reference the issue (`Fixes #<issue>` or `Refs #<issue>`).
- A `trace_id` must appear in the issue body, PR body, and workflow comments.

---

## 6. Multi-Stage Workflow Design

### Overview
Workflows are triggered by GitHub events and label transitions. Labels represent the canonical state machine.

Stages:
1. Triage
2. Planning
3. Prioritization
4. Implementation (human-approved)
5. Deployment (human-approved)

---

### Workflow A: TRIAGE

**Trigger**
- Issue opened with `request:*` label.

**Purpose**
- Understand the problem and scope.
- Decide whether to proceed.

**Claude Output**
- Triage report:
  - Problem summary
  - Suspected cause/area
  - Clarifying questions
  - Recommendation

**Result**
- Label transition to:
  - `stage:plan` or
  - `stage:blocked`

---

### Workflow B: PLAN

**Trigger**
- Issue labeled `stage:plan`.

**Purpose**
- Produce a concrete implementation plan.

**Claude Output**
- Implementation plan including:
  - Proposed approach
  - Files/modules affected
  - Acceptance criteria (user-visible, testable)
  - Unit test plan
  - Risk/unknowns
  - Rough effort estimate (S/M/L)

**Result**
- Label transition to:
  - `stage:prioritize` or
  - `stage:blocked`

---

### Workflow C: PRIORITIZE

**Trigger**
- Issue labeled `stage:prioritize`.

**Purpose**
- Assess value vs. effort and recommend priority.

**Claude Output**
- Prioritization memo:
  - Expected user/business value
  - Expected effort
  - Risk assessment
  - Recommended priority (`p0`/`p1`/`p2`)

**Result**
- Apply `priority:*` label.
- Transition to `stage:awaiting-implementation-approval`.

---

### Human Gate 1: Implementation Approval

**Mechanism**
- Admin applies approval label or directly sets `stage:implement`.

**Requirement**
- No implementation workflow may run without explicit approval.

---

### Workflow D: IMPLEMENT

**Trigger**
- Issue labeled `stage:implement` and approved.

**Purpose**
- Implement change and open a PR.

**Policy Constraints**
- PR-only changes (no direct push to main).
- Unit tests required for new/changed code.
- Tests must be executed.
- PR must not be marked ready if tests fail.

**Claude Output**
- Pull Request:
  - Code changes
  - Unit tests
  - Summary and test evidence

**Result**
- PR labeled `agent:claude`.
- Issue updated to `stage:pr-opened`.

---

## 7. Admin Ops Page (Level 0)

### Purpose
Provide operational visibility and approval controls using GitHub as the data source.

### Data Displayed
- Issues grouped by stage and type.
- PRs labeled `agent:claude`.
- Recent workflow runs.
- Links to GitHub for drill-down.

### Admin Actions
- Approve implementation.
- Approve deployment.

---

## 8. Deployment (Non-Container)

### Deployment Model
- Versioned release directories:
  - `/srv/app/releases/<git_sha>/`
  - `/srv/app/current -> releases/<git_sha>/`
- systemd service runs from `/srv/app/current`.

### Trigger
- GitHub Actions on:
  - push to `main`, or
  - push of tag `v*`.

### Approval
- Use GitHub Actions Environments with required reviewers.

### Steps
1. Checkout code.
2. SSH to server.
3. Create new release directory.
4. Install dependencies.
5. Run smoke checks.
6. Atomically switch symlink.
7. Restart service.
8. Rollback on failure.

---

## 9. Monitoring

### Function
- Periodic inspection of logs or metrics.
- Detect critical error signatures.

### Deduplication
- Compute signature hash.
- Store last occurrence and issue reference.
- Suppress repeated issue creation within cooldown window.

---

## 10. Testing Requirements

### Mandatory
- New functionality must include unit tests.
- CI must execute tests.
- Failed tests block completion and deployment.

### Acceptance Criteria
- Each implementation plan must define user-visible, testable acceptance criteria.
- Examples:
  - Service responds on health endpoint.
  - Submitted feature request appears in admin ops page.
  - Approved deployment updates running version.

---

## 11. Label / State Transition Table

| Current State | Trigger / Action | Next State |
|---------------|-----------------|------------|
| (new issue) | issue opened | stage:triage |
| stage:triage | triage workflow success | stage:plan |
| stage:triage | triage rejects | stage:blocked |
| stage:plan | plan workflow success | stage:prioritize |
| stage:plan | plan blocked | stage:blocked |
| stage:prioritize | prioritization complete | stage:awaiting-implementation-approval |
| stage:awaiting-implementation-approval | human approval | stage:implement |
| stage:implement | implementation workflow success | stage:pr-opened |
| stage:pr-opened | PR merged | stage:awaiting-deploy-approval |
| stage:awaiting-deploy-approval | human approval | stage:done |
| any | human intervention | stage:blocked |

---

## 12. MVP Acceptance Criteria

- Requests submitted via UI create labeled GitHub issues.
- Triage, plan, and prioritize workflows execute automatically.
- Human approval is required before implementation and deployment.
- Implementation workflow produces PRs with passing tests.
- Deployment is GitHub-triggered, approved, and reversible.
