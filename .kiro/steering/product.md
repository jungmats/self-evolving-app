# Product Overview

## Self-Evolving Web Application

A controlled automation system that enables continuous improvement through structured workflows. The system allows users and automated monitors to submit bug reports and feature requests, which are then processed through a multi-stage workflow with human approval gates.

## Core Capabilities

- **Request Submission**: Web interface for users to submit bug reports and feature requests
- **Automated Triage**: Claude-powered analysis to understand problems and scope
- **Planning & Prioritization**: Automated generation of implementation plans and priority assessments
- **Controlled Implementation**: Human-approved code changes via GitHub Pull Requests
- **Admin Dashboard**: Operational visibility and approval controls for administrators
- **Monitoring**: Automated detection of critical errors with deduplication

## Key Principles

- **Human-in-the-Loop**: All implementation and deployment require explicit human approval
- **GitHub as System of Record**: Issues, PRs, labels, and comments provide full traceability
- **Staged Workflows**: Triage → Plan → Prioritize → Implement → Deploy
- **Policy-Constrained Automation**: All automated actions bounded by deterministic policy evaluation
- **Trace ID Correlation**: Every request tracked end-to-end with unique trace identifiers
