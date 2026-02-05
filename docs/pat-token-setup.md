# Personal Access Token (PAT) Setup for Workflow Transitions

## Problem

GitHub Actions workflows using `GITHUB_TOKEN` cannot trigger other workflows. This is a security feature to prevent recursive workflow loops.

From [GitHub's documentation](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow#triggering-a-workflow-from-a-workflow):

> "When you use the repository's GITHUB_TOKEN to perform tasks, events triggered by the GITHUB_TOKEN will not create a new workflow run."

This means when a workflow adds a label like `stage:plan` using `GITHUB_TOKEN`, the planning workflow won't trigger.

## Solution

Use a Personal Access Token (PAT) instead of `GITHUB_TOKEN` for operations that need to trigger other workflows.

## Setup Instructions

### 1. Create a Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Configure the token:
   - **Name**: `Self-Evolving App Workflow Token`
   - **Expiration**: Choose appropriate duration (90 days recommended)
   - **Repository access**: Select "Only select repositories" → Choose your repository
   - **Permissions**:
     - Repository permissions:
       - **Issues**: Read and write
       - **Contents**: Read-only and write
       - **Pull Requests**: Read-only and write
       - **Workflows**: Read-only and write
       - **Metadata**: Read-only (automatically included)

4. Click "Generate token"
5. **IMPORTANT**: Copy the token immediately - you won't be able to see it again!

### 2. Add Token to Repository Secrets

1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Configure:
   - **Name**: `PAT_TOKEN`
   - **Value**: Paste the token you copied
4. Click "Add secret"

### 3. Update Workflow Files

Replace `GITHUB_TOKEN` with `PAT_TOKEN` in workflow files where label transitions occur.

**Files to update:**
- `.github/workflows/triage.yml`
- `.github/workflows/planning.yml`
- `.github/workflows/prioritization.yml`
- `.github/workflows/implementation.yml`
- `.github/workflows/approval.yml`
- `.github/workflows/deployment.yml`

**Change this:**
```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**To this:**
```yaml
env:
  GITHUB_TOKEN: ${{ secrets.PAT_TOKEN }}
```

### 4. Verify the Fix

1. Create a test issue with the `stage:triage` label
2. Watch the workflow run complete
3. Verify that the `stage:plan` label is automatically added
4. Confirm that the planning workflow triggers automatically

## Security Considerations

- **Token Scope**: Use fine-grained tokens with minimal permissions
- **Expiration**: Set reasonable expiration dates and rotate tokens regularly
- **Access**: Limit repository access to only the repositories that need it
- **Audit**: Regularly review token usage in GitHub's audit logs

## Troubleshooting

### Workflows still not triggering?

1. **Check token permissions**: Ensure the PAT has "Issues: Read and write" permission
2. **Verify secret name**: Confirm the secret is named `PAT_TOKEN` (case-sensitive)
3. **Token expiration**: Check if the token has expired
4. **Workflow conditions**: Verify the workflow's `if` conditions are met
5. **Label name**: Ensure label names match exactly (e.g., `stage:plan` not `stage: plan`)

### How to test without creating real issues?

Use the GitHub CLI to test label operations:

```bash
# Add a label (should trigger workflow)
gh issue edit <issue-number> --add-label "stage:plan"

# Check workflow runs
gh run list --workflow=planning.yml
```

## Alternative: GitHub App

For production systems, consider using a GitHub App instead of a PAT:
- More granular permissions
- Better audit trail
- Doesn't count against user rate limits
- Can be installed per-repository

See [GitHub's documentation](https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps) for details.
