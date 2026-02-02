# Self-Hosted GitHub Runner Setup Guide

## Overview

This guide covers setting up a self-hosted GitHub Actions runner for the Self-Evolving Web Application. The runner provides Claude CLI integration with full repository context for enhanced AI-powered workflows.

## Prerequisites

- Local machine or dedicated server with internet access
- GitHub repository admin access
- Python 3.11+
- Git
- jq (JSON processor)
- Claude CLI access

## Security Requirements

- Repository-scoped runner (never organization-wide)
- Specific runner labels: `[self-hosted, solops-local]`
- No fork execution
- Trusted code only
- Network isolation beyond GitHub and Claude CLI

## Installation Steps

### 1. Download and Configure Runner

```bash
# Create runner directory
mkdir -p ~/actions-runner && cd ~/actions-runner

# Download the latest runner package (replace with current version)
curl -o actions-runner-osx-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-osx-x64-2.311.0.tar.gz

# Extract the installer
tar xzf ./actions-runner-osx-x64-2.311.0.tar.gz

# Configure the runner (you'll need a registration token from GitHub)
./config.sh --url https://github.com/YOUR_ORG/YOUR_REPO --token YOUR_REGISTRATION_TOKEN --labels self-hosted,solops-local --name solops-runner
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Verify Claude CLI is available
claude --version

# Verify jq is available
jq --version

# Verify Git is available
git --version
```

### 3. Configure Environment

Create a `.env` file in the runner directory:

```bash
# Runner environment configuration
PYTHONPATH=/path/to/your/self-evolving-app/app:/path/to/your/self-evolving-app
REPO_ROOT=/path/to/your/self-evolving-app
# GITHUB_TOKEN=your_github_token  # Only if not in shell environment
```

### 4. Start Runner

```bash
# Start the runner
./run.sh
```

### 5. Configure as Service (Optional)

For production deployment, configure the runner as a system service:

```bash
# Install as service
sudo ./svc.sh install

# Start service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

## Security Configuration

### Runner Configuration

The runner MUST be configured with these security settings:

1. **Repository Scope**: Never organization-wide
2. **Specific Labels**: `[self-hosted, solops-local]`
3. **Trusted Code Only**: No fork execution
4. **Network Isolation**: Minimal network access

### Workflow Security Controls

Workflows include these security controls:

```yaml
jobs:
  workflow-job:
    runs-on: [self-hosted, solops-local]  # Specific runner targeting
    if: |
      github.event.label.name == 'stage:triage' && 
      github.event.action == 'labeled' &&
      github.event.issue.user.type != 'Bot'  # No bot-created issues
```

### Risk Mitigation

- Workflows execute only on repository owner's issues and trusted collaborators
- No execution on forked repository pull requests
- Repository checkout uses trusted main branch code for workflow scripts
- Claude CLI access limited to repository context only

## Testing Runner Setup

### Basic Connectivity Test

1. Create a test issue in your repository
2. Add the `stage:triage` label
3. Verify the workflow triggers on the self-hosted runner
4. Check runner logs for successful execution

### Dependency Verification

```bash
# Test Python environment
python3 -c "import sys; print(sys.version)"

# Test Claude CLI
claude --print "Hello, this is a test"

# Test jq
echo '{"test": "value"}' | jq '.test'

# Test Git
git status
```

## Troubleshooting

### Common Issues

1. **Runner Not Connecting**
   - Check internet connectivity
   - Verify registration token is valid
   - Ensure firewall allows GitHub connections

2. **Workflow Not Triggering**
   - Verify runner labels match workflow requirements
   - Check workflow conditions and filters
   - Review runner logs for errors

3. **Claude CLI Issues**
   - Verify Claude CLI authentication
   - Test Claude CLI outside of workflows

4. **Permission Errors**
   - Verify GitHub token has required permissions
   - Check repository access settings
   - Ensure runner user has file system permissions

### Log Locations

- Runner logs: `~/actions-runner/_diag/`
- Workflow logs: Available in GitHub Actions UI
- System logs: `/var/log/` (if running as service)

## Maintenance

### Regular Tasks

1. **Update Runner**: Download and install latest runner version
2. **Update Dependencies**: Keep Python packages and Claude CLI current
3. **Monitor Logs**: Regular review of runner and workflow logs
4. **Security Review**: Periodic review of access permissions and configurations

### Backup and Recovery

1. **Configuration Backup**: Save runner configuration and environment files
2. **Recovery Process**: Document steps to recreate runner on new machine
3. **Monitoring**: Set up alerts for runner downtime or failures