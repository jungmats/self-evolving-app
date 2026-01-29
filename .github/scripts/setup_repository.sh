#!/bin/bash

# GitHub Repository Setup Script for Self-Evolving Web Application
# This script sets up all required GitHub configuration for the workflow system

set -e

echo "🚀 Setting up GitHub repository for Self-Evolving Web Application"
echo "================================================================"

# Check required environment variables
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Error: GITHUB_TOKEN environment variable is required"
    echo "Please set your GitHub Personal Access Token:"
    echo "export GITHUB_TOKEN=your_token_here"
    exit 1
fi

if [ -z "$GITHUB_REPOSITORY" ]; then
    echo "❌ Error: GITHUB_REPOSITORY environment variable is required"
    echo "Please set your repository in format owner/repo:"
    echo "export GITHUB_REPOSITORY=owner/repository-name"
    exit 1
fi

echo "📋 Repository: $GITHUB_REPOSITORY"
echo "🔑 Token: ${GITHUB_TOKEN:0:8}..."
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed"
    exit 1
fi

# Install required Python packages
echo "📦 Installing required Python packages..."
pip3 install requests --quiet

# Setup GitHub labels
echo "🏷️  Setting up GitHub labels..."
python3 .github/scripts/setup_labels.py
if [ $? -eq 0 ]; then
    echo "✅ Labels configured successfully"
else
    echo "❌ Failed to configure labels"
    exit 1
fi

# Setup GitHub environment
echo "🌍 Setting up GitHub environment..."
python3 .github/scripts/setup_environment.py
if [ $? -eq 0 ]; then
    echo "✅ Environment configured successfully"
else
    echo "❌ Failed to configure environment"
    exit 1
fi

# Validate workflow files
echo "🔍 Validating workflow files..."
WORKFLOW_FILES=(
    ".github/workflows/triage.yml"
    ".github/workflows/planning.yml"
    ".github/workflows/prioritization.yml"
    ".github/workflows/implementation.yml"
    ".github/workflows/deployment.yml"
)

for workflow in "${WORKFLOW_FILES[@]}"; do
    if [ -f "$workflow" ]; then
        echo "✅ $workflow exists"
    else
        echo "❌ $workflow is missing"
        exit 1
    fi
done

# Validate issue templates
echo "📝 Validating issue templates..."
TEMPLATE_FILES=(
    ".github/ISSUE_TEMPLATE/bug_report.yml"
    ".github/ISSUE_TEMPLATE/feature_request.yml"
    ".github/ISSUE_TEMPLATE/investigation.yml"
    ".github/ISSUE_TEMPLATE/config.yml"
)

for template in "${TEMPLATE_FILES[@]}"; do
    if [ -f "$template" ]; then
        echo "✅ $template exists"
    else
        echo "❌ $template is missing"
        exit 1
    fi
done

echo
echo "🎉 Repository setup completed successfully!"
echo
echo "📋 Summary of configured components:"
echo "   • GitHub labels (stage, request, source, priority, agent)"
echo "   • Issue templates (bug report, feature request, investigation)"
echo "   • Workflow files (triage, planning, prioritization, implementation, deployment)"
echo "   • Production environment (without required reviewers)"
echo
echo "🔧 Next steps:"
echo "   1. Configure required secrets in repository settings:"
echo "      - CLAUDE_API_KEY (for Claude Code integration)"
echo "      - DEPLOYMENT_SECRET (for deployment authentication)"
echo "   2. Set up branch protection rules for 'main' branch"
echo "   3. Test the system by creating an issue with labels"
echo
echo "📚 For more information, see: docs/self-evolving-app.md"