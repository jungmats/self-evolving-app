# Implementation Plan: Self-Evolving Web Application

## Overview

This implementation plan breaks down the self-evolving web application into discrete, testable steps that build incrementally toward user-visible milestones. The approach prioritizes core functionality first, with comprehensive testing at each stage. Each task builds on previous work and includes validation through automated tests.

The implementation follows test-driven development principles, with small, reversible changes that maintain system integrity throughout development.

## Tasks

- [-] 1. Web Server Foundation - Local Deployment
  - Set up Python FastAPI project structure with SQLAlchemy ORM
  - Configure development environment with testing framework (pytest + Hypothesis)
  - Create basic FastAPI server with health endpoint
  - Set up basic SQLite database (no migrations yet)
  - _Requirements: 0.1, 14.1, 15.1_
  - **Test: Server runs locally and responds to health checks**

- [ ] 2. Repository Bootstrap and GitHub Plumbing
  - Ensure GitHub labels exist (stage:*, request:*, source:*, priority:*, agent:*)
  - Add .github/ISSUE_TEMPLATE/* for structured issue creation
  - Configure workflow permissions and secrets placeholders
  - Configure GitHub Environment 'production' (without required reviewers)
  - _Requirements: 3.1, 15.1_
  - **Test: Repository has all required labels and templates configured**

- [ ] 3. User Request Submission Interface
  - [ ] 3.1 Implement core web application data models (Submission only)
    - Create SQLAlchemy Submission model for outbox-style tracking
    - Store minimal trace_id ↔ issue_id mapping and submission status
    - Implement Trace_ID generation and uniqueness constraints
    - _Requirements: 1.4, 12.1, 14.3_

  - [ ] 3.2 Write property test for Trace_ID uniqueness
    - **Property 12: Traceability and Audit Trail**
    - **Validates: Requirements 12.1, 12.2**

  - [ ] 3.3 Create FastAPI endpoints for request submission
    - Implement bug report submission endpoint with validation
    - Implement feature request submission endpoint with validation
    - Add input validation with fail-fast error handling
    - _Requirements: 1.1, 1.2, 1.3, 0.3_

  - [ ] 3.4 Create basic React frontend with submission forms
    - Set up React + TypeScript project structure
    - Create bug report and feature request forms
    - Connect forms to FastAPI backend
    - _Requirements: 1.1_
    - **Test: Users can submit requests via web interface, data appears in local database**

- [ ] 4. GitHub Integration - Issues Creation
  - [ ] 4.1 Implement GitHub API client wrapper
    - Create authenticated GitHub client with error handling
    - Implement Issue creation with proper labeling
    - Add GitHub API timeout handling
    - _Requirements: 15.3, 1.2, 1.3_

  - [ ] 4.2 Implement Issue state management
    - Create functions for label management and state transitions
    - Implement Trace_ID embedding in Issue bodies
    - Add comment creation for audit trail
    - _Requirements: 3.4, 12.2, 12.4_

  - [ ] 4.3 Write property test for state machine integrity
    - **Property 5: State Machine Integrity**
    - **Validates: Requirements 3.2, 3.3, 3.4, 3.5**

  - [ ] 4.4 Connect request submission to GitHub Issue creation
    - Integrate GitHub client with request submission endpoints
    - Add proper error handling and user feedback
    - Store minimal trace_id ↔ issue_id mapping locally
    - _Requirements: 1.2, 1.3, 1.5_

  - [ ] 4.5 Write contract test for GitHub Issue creation
    - **Contract Test: GitHub Issue Creation**
    - Test Issue creation with specific inputs and expected labels
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
    - **Test: Feature/bug submissions create GitHub Issues with correct labels**

- [ ] 5. Workflow State Machine - Empty Workflows
  - [ ] 5.1 Create GitHub Actions workflow shells
    - Write YAML workflow files for triage, planning, prioritization (empty implementations)
    - Add workflow triggering based on Issue label changes
    - Implement basic state transitions without Claude integration
    - _Requirements: 4.1, 5.1, 6.1_

  - [ ] 5.2 Write contract test for GitHub label transitions
    - **Contract Test: State Machine Transitions**
    - Test valid label transition rules with golden file
    - **Validates: Requirements 3.2, 3.3**

  - [ ] 5.3 Implement basic workflow orchestration scripts
    - Create Python scripts that handle state transitions
    - Add Issue comment creation for workflow progress
    - Implement workflow run correlation with Trace_ID
    - _Requirements: 12.4, 3.2_
    - **Test: State machine works (triage→plan→prioritize→stage:awaiting-implementation-approval) without real outcomes**

- [ ] 6. Policy & Gate Component - Request Blocking
  - [ ] 6.1 Implement Policy & Gate Component data model
    - Create PolicyDecision model for audit trail
    - Add policy decision recording with timestamps
    - _Requirements: 16.12_

  - [ ] 6.2 Implement Policy & Gate Component core logic
    - Create PolicyGateComponent class with decision evaluation
    - Implement stage context analysis and constraint checking
    - Add deterministic prompt construction with scope constraints
    - _Requirements: 16.1, 16.4, 16.5, 16.6, 16.7_

  - [ ] 6.3 Write property test for policy decision determinism
    - **Property 17: Policy Decision Determinism**
    - **Validates: Requirements 16.4, 16.6, 16.7**

  - [ ] 6.4 Write contract test for policy component I/O
    - **Contract Test: Policy Component Interface**
    - Test input/output schema with golden files
    - **Validates: Requirements 16.2, 16.4**

  - [ ] 6.5 Integrate Policy & Gate with workflow shells
    - Connect policy evaluation to workflow triggers
    - Add policy decision blocking for inappropriate requests
    - _Requirements: 16.3_
    - **Test: Unjustified/unrelated submissions are blocked by policy checks**

- [ ] 7. Functional Workflows - Real Outcomes
  - [ ] 7.1 Implement Claude API integration
    - Create Claude client with constrained prompt handling
    - Add workflow-specific prompt templates
    - Implement response parsing and validation
    - _Requirements: 4.2, 5.2, 6.2_

  - [ ] 7.2 Write contract test for Claude output structure
    - **Contract Test: Claude Workflow Outputs**
    - Test triage, planning, prioritization output schemas
    - **Validates: Requirements 4.3, 5.2, 6.2**

  - [ ] 7.3 Implement functional workflow logic
    - Add real triage analysis with problem assessment
    - Create planning workflow with implementation plans
    - Implement prioritization with value/effort analysis
    - _Requirements: 4.2, 4.3, 5.2, 6.2, 6.3_
    - **Test: Workflows produce real outcomes (triage reports, plans, prioritization)**

- [ ] 8. Implementation Workflow - Code Generation
  - [ ] 8.1 Implement code generation workflow
    - Create implementation workflow that generates code changes
    - Add unit test generation for all new/modified code
    - Implement test execution and validation
    - _Requirements: 8.2, 8.3, 8.4_

  - [ ] 8.2 Write property test for implementation test requirements
    - **Property 9: Implementation Workflow Test Requirements**
    - **Validates: Requirements 8.3, 8.4**

  - [ ] 8.3 Implement Pull Request creation and management
    - Add PR creation with proper Trace_ID and Issue linking
    - Implement agent labeling for workflow-created PRs
    - Add PR merge detection and Issue state transition
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ] 8.4 Add human approval gate for implementation
    - Implement approval requirement before implementation workflow
    - Add approval state tracking via GitHub labels only
    - _Requirements: 7.1, 7.3_
    - **Test: Implementation workflow creates PRs when approved, ready for merge**

- [ ] 9. Admin Operations Dashboard
  - [ ] 9.1 Implement Issue display and grouping
    - Create components for Issue listing by stage and type
    - Implement GitHub API integration for real-time data
    - Add Pull Request display for agent-created PRs
    - _Requirements: 10.1, 10.2, 10.5_

  - [ ] 9.2 Implement approval controls
    - Create approval buttons for implementation
    - Add approval workflow via GitHub label mutations only
    - Implement approval state tracking and display
    - _Requirements: 7.2, 7.3_

  - [ ] 9.3 Write property test for state machine invariants
    - **Property 5: State Machine Integrity** (admin view)
    - **Validates: Requirements 3.4, 10.1**
    - **Test: Admin dashboard displays all Issues/PRs grouped correctly with functional approval controls**

- [ ] 10. Code-Only Deployment Pipeline
  - [ ] 10.1 Implement basic deployment component
    - Create versioned release directory management
    - Implement atomic symlink switching with rollback
    - Add health checks and deployment validation (no DB migrations)
    - _Requirements: 11.3, 11.4, 11.5_

  - [ ] 10.2 Write property test for deployment atomicity
    - **Property 11: Deployment Atomicity and Rollback**
    - **Validates: Requirements 11.3, 11.4, 11.5**

  - [ ] 10.3 Create deployment GitHub Actions workflow
    - Implement automatic deployment trigger on PR merge to main
    - Add deployment execution with proper error handling
    - Create rollback mechanism for failed deployments
    - _Requirements: 11.1_
    - **Test: PR merge to main automatically triggers deployment**

- [ ] 11. Migrations-Aware Deployment
  - [ ] 11.1 Introduce Alembic for database migrations
    - Set up Alembic configuration and initial migration
    - Create migration generation for schema changes
    - Add migration validation (fail fast on errors)
    - _Requirements: 14.1, 14.2_

  - [ ] 11.2 Integrate migrations into deployment pipeline
    - Add migration execution to deployment workflow
    - Implement migration validation against production data copies
    - Add deployment failure handling (manual rollback required)
    - _Requirements: 14.2_
    - **Test: Deployment handles database schema changes correctly**

- [ ] 12. Monitoring Component - Error Detection
  - [ ] 12.1 Implement monitoring data model
    - Create MonitoringSignature model for deduplication
    - Add signature hash storage and cooldown tracking
    - _Requirements: 2.5, 14.3_

  - [ ] 12.2 Implement log scanning and error detection
    - Create background task for periodic log inspection
    - Implement error signature computation and hashing
    - Add cooldown period tracking with database storage
    - _Requirements: 2.1, 2.2, 2.5_

  - [ ] 12.3 Write property test for monitoring deduplication
    - **Property 4: Monitoring Error Detection and Deduplication**
    - **Validates: Requirements 2.2, 2.3, 2.4, 2.5**

  - [ ] 12.4 Integrate monitoring with GitHub Issue creation
    - Connect error detection to Issue creation workflow
    - Implement proper labeling for monitoring Issues
    - Add error details and timestamp inclusion
    - _Requirements: 2.3, 2.4_
    - **Test: Provoke error in logs, monitoring component discovers and creates GitHub Issue**

- [ ] 13. Error Handling and System Resilience
  - [ ] 13.1 Implement comprehensive error handling
    - Add error recording for all workflow failures
    - Implement retry mechanisms with Trace_ID preservation
    - Create error recovery workflows and manual intervention points
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [ ] 13.2 Write property test for error handling
    - **Property 13: Error Handling and Recovery**
    - **Validates: Requirements 13.1, 13.2, 13.3, 13.4**

  - [ ] 13.3 Implement security configuration and logging
    - Add secure configuration management with environment variables
    - Implement security event logging for audit purposes
    - Add GitHub API timeout handling and circuit breaker
    - _Requirements: 15.2, 15.5, 13.5_

  - [ ] 13.4 Write property test for input validation
    - **Property 1: Input Validation and Fail-Fast Behavior**
    - **Validates: Requirements 0.3**
    - **Test: System handles all error conditions gracefully with proper logging and recovery**

- [ ] 14. Final Integration and System Validation
  - [ ] 14.1 Create end-to-end integration tests
    - Test complete request-to-deployment flow
    - Validate state machine transitions across all stages
    - Test approval gates and human intervention points
    - _Requirements: All requirements integration_

  - [ ] 14.2 Implement system monitoring and health checks
    - Add application health endpoints
    - Create system status dashboard
    - Implement alerting for critical system failures
    - _Requirements: System reliability_
    - **Test: Complete end-to-end flow from user request to deployed change**

## Notes

- All testing tasks are required for comprehensive validation
- Each major task includes a "Test:" description for visible progress validation
- Tasks are structured to align with user-visible testing milestones
- Property tests focus on meaningful invariants: Trace_ID uniqueness, state machine integrity, monitoring deduplication, policy determinism
- Contract tests validate schemas and interfaces: Claude outputs, policy I/O, GitHub label transitions
- SQLite scope: Local web application state and operational caches only; GitHub is authoritative for workflow artifacts
- Submission model: Outbox-style tracking with minimal trace_id ↔ issue_id mapping and submission status
- Approval mechanics: Admin Ops page UX triggers GitHub label mutations exclusively
- Deployment trigger: Automatic on PR merge to main (merge constitutes deployment approval)
- Data models are introduced only when needed: Submission (Task 3), PolicyDecision (Task 6), MonitoringSignature (Task 12)
- Alembic migrations introduced only in migrations-aware deployment (Task 11)
- Database migrations: Fail fast on errors, manual rollback required
- GitHub Actions workflows tested through extracted Python modules and integration tests