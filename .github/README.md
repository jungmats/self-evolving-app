# GitHub Configuration for Self-Evolving Web Application

This directory contains all GitHub-specific configuration for the self-evolving web application workflow system.

## Overview

The self-evolving web application uses GitHub as the central system of record for all workflow state, artifacts, and decisions. This configuration includes:

- **Labels**: Structured labeling system for workflow state management
- **Issue Templates**: Standardized forms for bug reports, feature requests, and investigations
- **Workflows**: GitHub Actions workflows for automated processing
- **Environment**: Production environment configuration for deployments
- **Scripts**: Setup and maintenance utilities

## Directory Structure

```
.github/
├── ISSUE_TEMPLATE/           # Issue templates for structured submissions
│   ├── bug_report.yml        # Bug report template
│   ├── feature_request.yml   # Feature request template
│   ├── investigation.yml     # Investigation request template
│   └── config.yml           # Issue template configuration
├── workflows/               # GitHub Actions workflows
│   ├── triage.yml          # Triage workflow (stage:triage)
│   ├── planning.yml        # Planning workflow (stage:plan)
│   ├── prioritization.yml  # Prioritization workflow (stage:prioritize)
│   ├── implementation.yml  # Implementation workflow (stage:implement)
│   └── deployment.yml      # Deployment workflow (PR merge)
├── scripts/                # Setup and maintenance scripts
│   ├── setup_repository.sh # Complete repository setup
│   ├── setup_labels.py     # GitHub labels configuration
│   └── setup_environment.py # Environment configuration
└── README.md              # This documentation
```

## Label System

The workflow uses a structured labeling system organized by category:

### Stage Labels (Workflow State Machine)
- `stage:triage` - Issue is in triage stage
- `stage:plan` - Issue is in planning stage  
- `stage:prioritize` - Issue is in prioritization stage
- `stage:awaiting-implementation-approval` - Issue awaits implementation approval
- `stage:implement` - Issue is in implementation stage
- `stage:pr-opened` - Pull request has been opened
- `stage:awaiting-deploy-approval` - Issue awaits deployment approval
- `stage:blocked` - Issue is blocked and requires intervention
- `stage:done` - Issue is completed

### Request Type Labels
- `request:bug` - Bug report submission
- `request:feature` - Feature request submission
- `request:investigate` - Investigation request from monitoring

### Source Labels
- `source:user` - Request originated from user submission
- `source:monitor` - Request originated from automated monitoring

### Priority Labels
- `priority:p0` - Critical priority - immediate attention required
- `priority:p1` - High priority - should be addressed soon
- `priority:p2` - Normal priority - can be scheduled

### Agent Labels
- `agent:claude` - Created or modified by Claude workflows

## Workflow System

The GitHub Actions workflows implement a multi-stage processing pipeline:

1. **Triage** (`triage.yml`) - Triggered by `stage:triage` label
   - Analyzes issue content and produces triage report
   - Transitions to `stage:plan` on success

2. **Planning** (`planning.yml`) - Triggered by `stage:plan` label
   - Creates detailed implementation plan
   - Transitions to `stage:prioritize` on success

3. **Prioritization** (`prioritization.yml`) - Triggered by `stage:prioritize` label
   - Assesses value, effort, and risk
   - Applies priority label and transitions to `stage:awaiting-implementation-approval`

4. **Implementation** (`implementation.yml`) - Triggered by `stage:implement` label
   - Generates code changes and tests
   - Creates Pull Request and transitions to `stage:pr-opened`

5. **Deployment** (`deployment.yml`) - Triggered by PR merge to main
   - Deploys approved changes to production
   - Transitions linked issue to `stage:done`

## Issue Templates

Structured issue templates ensure consistent information collection:

- **Bug Report** (`bug_report.yml`) - For reporting system issues
- **Feature Request** (`feature_request.yml`) - For requesting new functionality  
- **Investigation** (`investigation.yml`) - For investigation requests (typically from monitoring)

Each template automatically applies appropriate labels and guides users through providing necessary information.

## Environment Configuration

The `production` environment is configured for deployment workflows:
- No required reviewers (as specified in requirements)
- Protected branches policy enabled
- Deployment branch policy configured

## Setup Instructions

### Prerequisites
- GitHub repository with admin access
- GitHub Personal Access Token with appropriate permissions
- Python 3.x installed locally

### Required Token Permissions
Your GitHub token needs the following scopes:
- `repo` (full repository access)
- `workflow` (update GitHub Actions workflows)
- `admin:repo_hook` (manage repository webhooks)

### Quick Setup
1. Set environment variables:
   ```bash
   export GITHUB_TOKEN=your_token_here
   export GITHUB_REPOSITORY=owner/repository-name
   ```

2. Run the setup script:
   ```bash
   ./.github/scripts/setup_repository.sh
   ```

### Manual Setup
If you prefer to set up components individually:

1. **Setup Labels**:
   ```bash
   python3 .github/scripts/setup_labels.py
   ```

2. **Setup Environment**:
   ```bash
   python3 .github/scripts/setup_environment.py
   ```

### Required Secrets
Configure these secrets in your repository settings:

- `CLAUDE_API_KEY` - API key for Claude Code integration
- `DEPLOYMENT_SECRET` - Secret for deployment authentication
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

## Testing the Setup

After setup, test the system by:

1. Creating a new issue using one of the templates
2. Verifying the issue receives appropriate labels
3. Checking that workflows trigger correctly
4. Monitoring workflow execution in the Actions tab

## Troubleshooting

### Common Issues

**Labels not created**: Check token permissions and repository access
**Workflows not triggering**: Verify label names match exactly (case-sensitive)
**Environment setup fails**: Ensure token has admin:repo_hook permission
**Secrets not available**: Check repository settings > Secrets and variables > Actions

### Validation Commands

Check if all components are properly configured:

```bash
# Verify workflow files exist
ls -la .github/workflows/

# Verify issue templates exist  
ls -la .github/ISSUE_TEMPLATE/

# Test label setup (requires GITHUB_TOKEN)
python3 .github/scripts/setup_labels.py
```

## Maintenance

### Updating Labels
Modify `REQUIRED_LABELS` in `setup_labels.py` and re-run the script.

### Updating Workflows
Edit workflow files in `.github/workflows/` and commit changes.

### Updating Templates
Modify template files in `.github/ISSUE_TEMPLATE/` and commit changes.

## Security Considerations

- Store sensitive configuration in GitHub Secrets, never in code
- Use least privilege principle for token permissions
- Regularly rotate API keys and tokens
- Monitor workflow execution logs for security events

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Issue Templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments)
- [Self-Evolving App Design Document](../docs/self-evolving-app.md)