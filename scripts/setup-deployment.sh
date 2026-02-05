#!/bin/bash
"""
Setup script for deployment directory configuration.

This script helps configure the deployment environment for the self-evolving app.
"""

set -e

# Default deployment directory
DEFAULT_DEPLOYMENT_DIR="/Users/$(whoami)/deployments"

echo "🚀 Self-Evolving App Deployment Setup"
echo "======================================"
echo

# Get deployment directory from user
read -p "Enter deployment directory path (default: $DEFAULT_DEPLOYMENT_DIR): " DEPLOYMENT_DIR
DEPLOYMENT_DIR=${DEPLOYMENT_DIR:-$DEFAULT_DEPLOYMENT_DIR}

echo
echo "📁 Deployment directory: $DEPLOYMENT_DIR"

# Create deployment directory
if [ ! -d "$DEPLOYMENT_DIR" ]; then
    echo "📦 Creating deployment directory..."
    mkdir -p "$DEPLOYMENT_DIR"
    echo "✅ Directory created: $DEPLOYMENT_DIR"
else
    echo "✅ Directory already exists: $DEPLOYMENT_DIR"
fi

# Check permissions
if [ ! -w "$DEPLOYMENT_DIR" ]; then
    echo "❌ No write permission to deployment directory"
    echo "   Please fix permissions: chmod 755 $DEPLOYMENT_DIR"
    exit 1
fi

echo "✅ Write permissions verified"

# Set up GitHub repository variable
echo
echo "🔧 GitHub Repository Configuration"
echo "=================================="
echo
echo "To complete the setup, you need to configure the DEPLOYMENT_BASE_PATH"
echo "repository variable in GitHub:"
echo
echo "1. Go to your GitHub repository"
echo "2. Navigate to Settings → Secrets and variables → Actions"
echo "3. Click on the 'Variables' tab"
echo "4. Click 'New repository variable'"
echo "5. Name: DEPLOYMENT_BASE_PATH"
echo "6. Value: $DEPLOYMENT_DIR"
echo "7. Click 'Add variable'"
echo
echo "Alternatively, you can set it via GitHub CLI:"
echo "gh variable set DEPLOYMENT_BASE_PATH --body \"$DEPLOYMENT_DIR\""
echo

# Test deployment script
echo "🧪 Testing deployment script..."
echo "==============================="
echo

# Test health check
if python3 .github/scripts/deployment_executor.py health-check --base-path "$DEPLOYMENT_DIR" > /dev/null 2>&1; then
    echo "✅ Deployment script test passed"
else
    echo "❌ Deployment script test failed"
    echo "   Make sure you're running this from the repository root"
    echo "   and that Python dependencies are installed"
fi

echo
echo "🎉 Setup complete!"
echo
echo "Next steps:"
echo "1. Configure DEPLOYMENT_BASE_PATH in GitHub repository variables"
echo "2. Ensure your self-hosted runner is running"
echo "3. Test the deployment by merging a PR with 'agent:claude' label"
echo
echo "Deployment directory structure will be:"
echo "$DEPLOYMENT_DIR/"
echo "├── releases/"
echo "│   └── {git-sha}/"
echo "└── current -> releases/{git-sha}"
echo