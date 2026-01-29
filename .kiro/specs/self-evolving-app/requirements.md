# Requirements Document

## Introduction

The Self-Evolving Web Application is a controlled automation system that enables continuous improvement through structured workflows. Users and automated monitors submit bug reports or feature requests via a web interface, which triggers a multi-stage GitHub Actions pipeline using Claude Code for triage, planning, prioritization, and implementation. The system requires explicit human approval before implementation and deployment, ensuring controlled evolution while maintaining system integrity.

## Coding Principles (Order of Importance)

All design and implementation SHALL adhere to these principles:

1. **Test-Driven Development**: Write or update tests first. Do not claim completion unless tests run and pass, or explicitly state why they could not be run.

2. **Small, Reversible, Observable Changes**: Prefer small diffs and scoped changes. Implement user testable and visible changes before backend changes wherever feasible. Keep changes reversible where possible. Maintain separation of concerns; avoid mixing orchestration, domain logic, and IO unless trivial.

3. **Fail Fast, No Silent Fallbacks**: Validate inputs at boundaries. Surface errors early and explicitly. Assume dependencies may fail. No silent fallbacks or hidden degradation. Any fallback must be explicit, tested, and observable.

4. **Minimize Complexity (YAGNI, No Premature Optimization)**: Implement the simplest solution that meets current requirements and tests. Do not design for speculative future use cases. Optimize only with evidence.

5. **Deliberate Trade-offs: Reusability vs. Fit (DRY with Restraint)**: Apply DRY only to real, stable duplication. Avoid abstractions that increase cognitive load without clear benefit. Prefer fit-for-purpose code unless a second use case is concrete.

6. **Don't Assume—Ask for Clarification**: If requirements are ambiguous or multiple interpretations exist, ask. If proceeding is necessary, state assumptions explicitly and keep changes localized and reversible.

7. **Confidence-Gated Autonomy**: Proceed end-to-end only when confidence is high. Narrow scope and increase checks when confidence is medium. Stop and ask when confidence is low.

8. **Security-by-Default**: Treat all external input as untrusted. Use safe defaults and least privilege. Do not weaken auth, authz, crypto, or injection defenses without explicit instruction. Never introduce secrets into code.

9. **Don't Break Contracts**: Preserve existing public APIs, schemas, and behavioral contracts unless explicitly instructed otherwise. If breaking changes are required, provide migration steps and compatibility tests.

10. **Risk-Scaled Rigor (Lightweight)**: Scale rigor with impact: 1) Low risk: unit tests, lint/format. 2) Medium risk: integration tests, edge cases, rollback awareness. 3) High risk (security, auth, money, data loss, core flows): explicit approval before destructive actions, targeted tests, minimal refactoring.

## Glossary

- **System**: The complete Self-Evolving Web Application
- **Web_Server**: FastAPI backend with React frontend for user interactions
- **Monitoring_Component**: Automated log/metric inspection service
- **Workflow_Component**: GitHub Actions workflows with Claude Code integration
- **Admin_Ops_Page**: Administrative dashboard for approval and monitoring
- **Deployment_Component**: GitHub-triggered deployment pipeline
- **GitHub_API**: GitHub REST API for issue and repository management
- **Request**: User-submitted bug report or feature request
- **Issue**: GitHub Issue representing a work item
- **Workflow_Run**: Execution instance of a GitHub Actions workflow
- **Stage**: Current state in the workflow state machine
- **Trace_ID**: Unique identifier linking related artifacts
- **Human_Approver**: Authorized user who can approve implementation and deployment

## Requirements

### Requirement 0: Development Methodology Compliance

**User Story:** As a development team, I want all system design and implementation to follow established coding principles, so that the codebase remains maintainable, secure, and reliable.

#### Acceptance Criteria

1. THE System SHALL be developed using test-driven development methodology with tests written before implementation
2. WHEN implementing any feature, THE System SHALL prioritize small, reversible, and observable changes
3. THE System SHALL validate all inputs at system boundaries and fail fast without silent fallbacks
4. THE System SHALL implement the simplest solution that meets current requirements without premature optimization
5. THE System SHALL apply DRY principles only to real, stable duplication and avoid unnecessary abstractions
6. WHEN requirements are ambiguous, THE development process SHALL seek clarification before proceeding
7. THE System SHALL implement confidence-gated autonomy with appropriate checks based on confidence levels
8. THE System SHALL treat all external input as untrusted and use security-by-default practices
9. THE System SHALL preserve existing public APIs and behavioral contracts unless explicitly instructed otherwise
10. THE System SHALL scale development rigor based on risk impact levels

### Requirement 1: Request Submission

**User Story:** As a user, I want to submit bug reports and feature requests through a web interface, so that I can communicate issues and improvement ideas to the system.

#### Acceptance Criteria

1. WHEN a user accesses the web application, THE Web_Server SHALL display a form interface for submitting requests
2. WHEN a user submits a bug report with required fields, THE System SHALL create a GitHub Issue with `request:bug` and `source:user` labels
3. WHEN a user submits a feature request with required fields, THE System SHALL create a GitHub Issue with `request:feature` and `source:user` labels
4. WHEN a request is submitted, THE System SHALL assign a unique Trace_ID to the Issue
5. WHEN an Issue is created, THE System SHALL apply the `stage:triage` label to initiate workflow processing

### Requirement 2: Automated Monitoring

**User Story:** As a system administrator, I want automated monitoring to detect and report critical errors, so that system issues are identified and addressed proactively.

#### Acceptance Criteria

1. THE Monitoring_Component SHALL periodically inspect application logs for critical error signatures
2. WHEN a critical error is detected, THE Monitoring_Component SHALL compute a signature hash for deduplication
3. IF an error signature has not been reported within the cooldown window, THEN THE System SHALL create a GitHub Issue with `request:investigate` and `source:monitor` labels
4. WHEN creating a monitoring Issue, THE System SHALL include error details and occurrence timestamp
5. THE Monitoring_Component SHALL store the last occurrence timestamp and Issue reference for each error signature

### Requirement 3: Workflow State Management

**User Story:** As a system architect, I want a clear state machine for tracking request progress, so that all work items follow a consistent and auditable process.

#### Acceptance Criteria

1. WHEN an Issue is created, THE System SHALL apply the `stage:triage` label as the initial state
2. WHEN a workflow completes successfully, THE System SHALL transition the Issue to the next stage according to the state machine
3. IF a workflow encounters blocking conditions, THEN THE System SHALL apply the `stage:blocked` label
4. THE System SHALL maintain exactly one `stage:*` label per Issue at any time
5. WHEN a stage transition occurs, THE System SHALL record the transition in Issue comments with timestamp

### Requirement 4: Triage Workflow

**User Story:** As a development team, I want automated triage of incoming requests, so that problems are understood and scoped before planning begins.

#### Acceptance Criteria

1. WHEN an Issue receives the `stage:triage` label, THE Workflow_Component SHALL trigger the triage workflow
2. THE triage workflow SHALL analyze the Issue content and produce a triage report
3. THE triage report SHALL include problem summary, suspected cause, clarifying questions, and recommendation
4. WHEN triage completes successfully, THE System SHALL transition the Issue to `stage:plan`
5. IF triage determines the Issue should not proceed, THEN THE System SHALL transition to `stage:blocked`

### Requirement 5: Planning Workflow

**User Story:** As a development team, I want detailed implementation plans for approved requests, so that development work can proceed with clear guidance.

#### Acceptance Criteria

1. WHEN an Issue receives the `stage:plan` label, THE Workflow_Component SHALL trigger the planning workflow
2. THE planning workflow SHALL produce an implementation plan including proposed approach, affected files, acceptance criteria, unit test plan, risks, and effort estimate
3. THE implementation plan SHALL be recorded as an Issue comment with the assigned Trace_ID
4. WHEN planning completes successfully, THE System SHALL transition the Issue to `stage:prioritize`
5. IF planning identifies blocking conditions, THEN THE System SHALL transition to `stage:blocked`

### Requirement 6: Prioritization Workflow

**User Story:** As a product manager, I want automated prioritization recommendations, so that development resources are allocated effectively.

#### Acceptance Criteria

1. WHEN an Issue receives the `stage:prioritize` label, THE Workflow_Component SHALL trigger the prioritization workflow
2. THE prioritization workflow SHALL assess expected user value, effort, and risk
3. THE prioritization workflow SHALL recommend a priority level (`priority:p0`, `priority:p1`, or `priority:p2`)
4. WHEN prioritization completes, THE System SHALL apply the recommended priority label
5. WHEN prioritization completes, THE System SHALL transition the Issue to `stage:awaiting-implementation-approval`

### Requirement 7: Human Approval Gates

**User Story:** As a system administrator, I want explicit approval control over implementation and deployment, so that automated changes are reviewed before execution.

#### Acceptance Criteria

1. WHEN an Issue reaches `stage:awaiting-implementation-approval`, THE System SHALL require Human_Approver action before proceeding
2. THE Admin_Ops_Page SHALL display Issues awaiting implementation approval with approval controls
3. WHEN a Human_Approver grants implementation approval, THE System SHALL transition the Issue to `stage:implement`
4. WHEN an Issue reaches `stage:awaiting-deploy-approval`, THE System SHALL require Human_Approver action before deployment
5. THE System SHALL NOT execute implementation or deployment workflows without explicit Human_Approver approval

### Requirement 8: Implementation Workflow

**User Story:** As a development team, I want automated implementation of approved changes, so that planned work is executed consistently with proper testing.

#### Acceptance Criteria

1. WHEN an Issue receives the `stage:implement` label with approval, THE Workflow_Component SHALL trigger the implementation workflow
2. THE implementation workflow SHALL create code changes based on the approved implementation plan
3. THE implementation workflow SHALL include unit tests for all new or modified code
4. THE implementation workflow SHALL execute all tests and verify they pass
5. WHEN implementation completes successfully, THE System SHALL create a Pull Request and transition the Issue to `stage:pr-opened`

### Requirement 9: Pull Request Management

**User Story:** As a development team, I want all changes to go through Pull Requests, so that code changes are reviewable and traceable.

#### Acceptance Criteria

1. THE implementation workflow SHALL create Pull Requests rather than direct commits to main branch
2. WHEN creating a Pull Request, THE System SHALL include the Trace_ID in the PR body
3. THE Pull Request body SHALL reference the originating Issue using `Fixes #<issue>` or `Refs #<issue>` format
4. THE System SHALL apply the `agent:claude` label to Pull Requests created by workflows
5. WHEN a Pull Request is merged, THE System SHALL transition the linked Issue to `stage:awaiting-deploy-approval`

### Requirement 10: Admin Operations Dashboard

**User Story:** As a system administrator, I want visibility into all requests and their current status, so that I can monitor system operation and provide approvals.

#### Acceptance Criteria

1. THE Admin_Ops_Page SHALL display Issues grouped by stage and request type
2. THE Admin_Ops_Page SHALL display Pull Requests labeled `agent:claude`
3. THE Admin_Ops_Page SHALL display recent Workflow_Runs with their status
4. THE Admin_Ops_Page SHALL provide approval controls for implementation and deployment
5. THE Admin_Ops_Page SHALL retrieve all data via GitHub_API queries

### Requirement 11: Deployment Pipeline

**User Story:** As a system administrator, I want controlled deployment of approved changes, so that the running system is updated safely with rollback capability.

#### Acceptance Criteria

1. WHEN a Pull Request is merged to main branch, THE Deployment_Component SHALL be available for triggering
2. THE deployment process SHALL require Human_Approver approval before execution
3. THE deployment SHALL create a versioned release directory using the git SHA
4. THE deployment SHALL atomically switch the current symlink to the new release
5. IF deployment fails, THEN THE System SHALL automatically rollback to the previous release

### Requirement 12: Traceability and Linking

**User Story:** As a system auditor, I want complete traceability between requests, plans, implementations, and deployments, so that all changes can be tracked to their origin.

#### Acceptance Criteria

1. WHEN creating any artifact, THE System SHALL include the Trace_ID for linking related items
2. THE Trace_ID SHALL appear in Issue bodies, Pull Request bodies, and workflow comments
3. THE System SHALL maintain references between Issues and their resulting Pull Requests
4. THE System SHALL record all stage transitions with timestamps in Issue comments
5. THE GitHub_API SHALL serve as the authoritative system of record for all workflow artifacts

### Requirement 13: Error Handling and Recovery

**User Story:** As a system administrator, I want robust error handling in workflows, so that temporary failures don't prevent system operation.

#### Acceptance Criteria

1. WHEN a workflow encounters an error, THE System SHALL record the error details in Issue comments
2. IF a workflow fails, THEN THE System SHALL transition the Issue to `stage:blocked`
3. THE System SHALL provide mechanisms for Human_Approvers to retry failed workflows
4. WHEN retrying a workflow, THE System SHALL preserve the original Trace_ID
5. THE System SHALL implement appropriate timeouts for all GitHub_API operations

### Requirement 14: Data Persistence and Storage

**User Story:** As a system architect, I want reliable data storage for application state, so that the system maintains consistency across restarts.

#### Acceptance Criteria

1. THE Web_Server SHALL use SQLite database for local application data storage
2. THE database schema SHALL be designed for future PostgreSQL migration compatibility
3. THE System SHALL store monitoring signatures and cooldown timestamps in the database
4. THE System SHALL use GitHub as the authoritative system of record for workflow artifacts
5. THE database SHALL maintain referential integrity between local data and GitHub artifact IDs

### Requirement 16: Policy & Gate Component

**User Story:** As a system owner, I want a deterministic Policy & Gate Component that evaluates each workflow step and generates policy-constrained prompts, so that automation is bounded, auditable, and cannot proceed outside defined constraints.

#### Acceptance Criteria

1. THE System SHALL include a Policy & Gate Component that is invoked by GitHub Actions workflows at defined points in the state machine
2. THE Policy & Gate Component SHALL produce machine-readable outputs used to enforce stage transitions and execution eligibility
3. THE Workflow_Component SHALL invoke the Policy & Gate Component before invoking Claude for any workflow stage (triage, plan, prioritize, implement)
4. THE Policy & Gate Component SHALL accept inputs including stage context, artifact context, operational context, and change context
5. THE Policy & Gate Component SHALL output a decision that MUST be one of: allow, review_required, block
6. THE Policy & Gate Component SHALL provide a deterministic reason explaining which constraints applied
7. THE Policy & Gate Component SHALL generate a constructed_prompt containing stage-specific instructions and scope constraints for Claude
8. WHEN decision=allow, THE workflow SHALL use constructed_prompt as the sole prompt basis for Claude invocation
9. WHEN decision=review_required, THE System SHALL NOT proceed with the guarded action and SHALL route the Issue into an approval state
10. WHEN decision=block, THE System SHALL transition the Issue to stage:blocked and record the decision
11. THE System SHALL re-evaluate policy using change context before advancing beyond the implementation stage
12. THE System SHALL record each policy decision as an auditable artifact linked to the Issue/PR with Trace_ID and timestamp
13. WHEN policy definitions or the Policy & Gate Component are modified, THE System SHALL require explicit Human_Approver approval before taking effect

### Requirement 17: Configuration and Security

**User Story:** As a system administrator, I want secure configuration management, so that API credentials and system settings are protected.

#### Acceptance Criteria

1. THE System SHALL use GitHub Personal Access Token for API authentication
2. THE System SHALL store sensitive configuration in environment variables or secure configuration files
3. THE System SHALL validate GitHub_API permissions before executing workflows
4. THE System SHALL implement rate limiting for GitHub_API requests
5. THE System SHALL log security-relevant events for audit purposes