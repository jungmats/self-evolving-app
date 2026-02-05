# Deployment Configuration Guide

This guide explains how to configure the deployment environment for the Self-Evolving Web Application.

## Environment Variable Configuration

The deployment system uses the `DEPLOYMENT_BASE_PATH` environment variable to specify where deployments should be created.

### Setting Up DEPLOYMENT_BASE_PATH

#### Option 1: GitHub Repository Variable (Recommended)

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click on the **Variables** tab
4. Click **New repository variable**
5. Set:
   - **Name**: `DEPLOYMENT_BASE_PATH`
   - **Value**: `/path/to/your/deployment/directory`
6. Click **Add variable**

#### Option 2: GitHub CLI

```bash
gh variable set DEPLOYMENT_BASE_PATH --body "/path/to/your/deployment/directory"
```

#### Option 3: Local Testing

For local testing, you can set the environment variable directly:

```bash
export DEPLOYMENT_BASE_PATH="/Users/$(whoami)/deployments"
```

## Directory Requirements

### Prerequisites

1. **Directory must exist**: The deployment directory must be created before deployment
2. **Write permissions**: The runner must have write access to the directory
3. **Sufficient space**: Ensure adequate disk space for multiple releases

### Directory Structure

The deployment system creates the following structure:

```
$DEPLOYMENT_BASE_PATH/
├── releases/                    # All release versions
│   ├── abc123def/              # Release by git SHA
│   │   ├── app/                # Application code
│   │   ├── requirements.txt    # Dependencies
│   │   └── run_server.py       # Server entry point
│   └── def456ghi/              # Another release
└── current -> releases/abc123def  # Symlink to current release
```

## Setup Script

Use the provided setup script to configure your deployment environment:

```bash
./scripts/setup-deployment.sh
```

This script will:
- Create the deployment directory
- Verify permissions
- Test the deployment script
- Provide GitHub configuration instructions

## Deployment Process

### Automatic Deployment

When a PR with the `agent:claude` label is merged to main:

1. **GitHub Actions triggers** the deployment workflow
2. **Environment validation** checks `DEPLOYMENT_BASE_PATH`
3. **Directory validation** ensures the path exists and is writable
4. **Release creation** creates a new versioned directory
5. **Atomic deployment** switches the symlink to the new release
6. **Health checks** verify the deployment
7. **Rollback** occurs automatically if deployment fails

### Manual Testing

You can test the deployment system manually:

```bash
# Health check
DEPLOYMENT_BASE_PATH=/your/path python3 .github/scripts/deployment_executor.py health-check

# Deploy a specific commit
DEPLOYMENT_BASE_PATH=/your/path python3 .github/scripts/deployment_executor.py deploy --git-sha abc123

# Rollback to previous release
DEPLOYMENT_BASE_PATH=/your/path python3 .github/scripts/deployment_executor.py rollback --previous-release /your/path/releases/def456
```

## Logging and Monitoring

### Log Format

The deployment system provides comprehensive logging with emojis for easy scanning:

- 🚀 **Action start**: Beginning of deployment operations
- 📁 **Directory info**: Path and validation information
- ✅ **Success**: Successful operations
- ❌ **Error**: Failed operations with details
- ⚠️ **Warning**: Non-critical issues
- 🔄 **Process**: Ongoing operations
- 📦 **Release**: Release creation and management
- 🏥 **Health**: Health check operations
- 🎯 **Target**: Deployment targets and paths
- ⏱️ **Timing**: Performance metrics

### Example Log Output

```
2026-02-05 10:52:29,122 - INFO - 🚀 Starting deployment action: deploy
2026-02-05 10:52:29,122 - INFO - 📁 Target deployment directory: /Users/majung/deployments
2026-02-05 10:52:29,123 - INFO - ✅ Deployment directory validated: /Users/majung/deployments
2026-02-05 10:52:29,123 - INFO - ✅ DeploymentComponent initialized successfully
2026-02-05 10:52:29,125 - INFO - 📦 Creating release directory...
2026-02-05 10:52:29,130 - INFO - ✅ Release created successfully
2026-02-05 10:52:29,130 - INFO -    📁 Release path: /Users/majung/deployments/releases/abc123def
2026-02-05 10:52:29,130 - INFO -    📋 Artifacts: app, requirements.txt, run_server.py
2026-02-05 10:52:29,135 - INFO - 🔄 Deploying release...
2026-02-05 10:52:29,140 - INFO - ✅ Deployment successful!
2026-02-05 10:52:29,140 - INFO -    🎯 Deployed to: /Users/majung/deployments/releases/abc123def
2026-02-05 10:52:29,140 - INFO -    ⏱️  Deployment time: 0.05 seconds
2026-02-05 10:52:29,140 - INFO -    🔗 Current symlink updated
```

## Error Handling

### Common Errors

#### 1. Missing Environment Variable
```
❌ DEPLOYMENT_BASE_PATH environment variable not set and --base-path not provided
   Set DEPLOYMENT_BASE_PATH environment variable or use --base-path argument
```

**Solution**: Configure the `DEPLOYMENT_BASE_PATH` variable as described above.

#### 2. Directory Does Not Exist
```
❌ Deployment base directory does not exist: /path/to/deployment
   Please create the directory first: mkdir -p /path/to/deployment
```

**Solution**: Create the directory with appropriate permissions.

#### 3. Permission Denied
```
❌ No write permission to deployment directory: /path/to/deployment
   Check directory permissions: ls -la /path/to/deployment
```

**Solution**: Fix directory permissions or choose a different directory.

### Fail-Fast Behavior

The deployment system follows fail-fast principles:

- **Pre-flight checks**: Validates environment before starting
- **Directory validation**: Ensures target directory exists and is writable
- **Health checks**: Verifies deployment integrity before switching
- **Automatic rollback**: Restores previous state on failure

## Security Considerations

1. **Directory permissions**: Use restrictive permissions (755 or 750)
2. **Path validation**: Only use trusted deployment paths
3. **Runner isolation**: Ensure self-hosted runner security
4. **Backup strategy**: Maintain backups of critical deployments

## Troubleshooting

### Debug Mode

For detailed debugging, you can examine the deployment result JSON:

```bash
DEPLOYMENT_BASE_PATH=/your/path python3 .github/scripts/deployment_executor.py deploy \
  --git-sha abc123 \
  --output-file deployment_result.json

cat deployment_result.json
```

### Manual Cleanup

If needed, you can manually clean up failed deployments:

```bash
# Remove failed release
rm -rf $DEPLOYMENT_BASE_PATH/releases/failed-sha

# Reset symlink to previous working release
ln -sfn $DEPLOYMENT_BASE_PATH/releases/working-sha $DEPLOYMENT_BASE_PATH/current
```

### Health Check Validation

Regular health checks help ensure deployment integrity:

```bash
# Check current deployment health
DEPLOYMENT_BASE_PATH=/your/path python3 .github/scripts/deployment_executor.py health-check
```