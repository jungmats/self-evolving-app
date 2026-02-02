# GitHub Runner Security Configuration

## Overview

This document outlines the security configuration requirements for the self-hosted GitHub Actions runner used in the Self-Evolving Web Application.

## Security Principles

1. **Principle of Least Privilege**: Runner has minimal permissions required for operation
2. **Repository Scope**: Runner is scoped to a single repository, never organization-wide
3. **Trusted Code Only**: No execution of untrusted or fork-originated code
4. **Network Isolation**: Minimal network access beyond GitHub and Claude CLI
5. **Audit Trail**: All runner activities are logged and traceable

## Runner Configuration Security

### Required Configuration

```bash
# Runner must be configured with these exact parameters
./config.sh \
    --url https://github.com/YOUR_ORG/YOUR_REPO \
    --token YOUR_REGISTRATION_TOKEN \
    --labels "self-hosted,solops-local" \
    --name "solops-runner" \
    --work "_work" \
    --replace
```

### Security Labels

- `self-hosted`: Identifies as self-hosted runner
- `solops-local`: Specific label for this application's workflows

### Prohibited Configurations

❌ **NEVER configure as organization-wide runner**
❌ **NEVER use generic labels like `linux` or `ubuntu`**
❌ **NEVER allow public repository access**
❌ **NEVER run without specific workflow targeting**

## Workflow Security Controls

### Required Workflow Conditions

All workflows MUST include these security conditions:

```yaml
jobs:
  secure-job:
    runs-on: [self-hosted, solops-local]  # Specific runner targeting
    if: |
      github.event.label.name == 'stage:triage' && 
      github.event.action == 'labeled' &&
      github.event.issue.user.type != 'Bot' &&
      github.repository_owner == 'YOUR_ORG'  # Repository owner check
```

### Security Filters

1. **Event Filtering**: Only specific label events trigger workflows
2. **Bot Detection**: Exclude bot-created issues from processing
3. **Repository Validation**: Verify repository ownership
4. **User Validation**: Only trusted users can trigger workflows

### Prohibited Workflow Triggers

❌ **NEVER trigger on `pull_request` events from forks**
❌ **NEVER trigger on `push` events from untrusted branches**
❌ **NEVER allow `workflow_dispatch` without authentication**
❌ **NEVER process untrusted user input directly**

## Network Security

### Allowed Connections

✅ **GitHub API**: `api.github.com`, `github.com`
✅ **Package Registries**: `pypi.org`, `registry.npmjs.org` (if needed)

### Blocked Connections

❌ **Arbitrary Internet Access**: Block all other outbound connections
❌ **Internal Networks**: No access to internal/private networks
❌ **File Sharing Services**: No access to external file services
❌ **Social Media APIs**: No access to social platforms

### Firewall Configuration

```bash
# Example iptables rules (adapt for your system)
# Allow GitHub
iptables -A OUTPUT -d github.com -j ACCEPT
iptables -A OUTPUT -d api.github.com -j ACCEPT

# Allow DNS
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT

# Block everything else
iptables -A OUTPUT -j DROP
```

## File System Security

### Runner Directory Permissions

```bash
# Set restrictive permissions on runner directory
chmod 750 ~/actions-runner
chown runner:runner ~/actions-runner

# Protect configuration files
chmod 600 ~/actions-runner/.runner
chmod 600 ~/actions-runner/.env
```

### Work Directory Isolation

```bash
# Ensure work directory is isolated
mkdir -p ~/actions-runner/_work
chmod 750 ~/actions-runner/_work
```

### Log File Security

```bash
# Secure log files
chmod 640 ~/actions-runner/_diag/*.log
```

## Environment Security

### Required Environment Variables

```bash
# Minimal required environment
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx  # Repository-scoped token (if not in shell)
PYTHONPATH=/path/to/repo/app:/path/to/repo
REPO_ROOT=/path/to/repo
```

### Prohibited Environment Variables

❌ **Personal Access Tokens with broad scope**
❌ **Organization secrets**
❌ **Database credentials**
❌ **Third-party API keys**

### Secret Management

1. **GitHub Secrets**: Use repository secrets for sensitive data
2. **Environment Files**: Protect `.env` files with restrictive permissions
3. **Token Rotation**: Regularly rotate GitHub tokens
4. **Audit Access**: Monitor token usage and access patterns

## Process Security

### User Isolation

```bash
# Create dedicated user for runner
sudo useradd -m -s /bin/bash runner
sudo usermod -aG docker runner  # Only if Docker is needed

# Run runner as dedicated user
sudo -u runner ./run.sh
```

### Process Monitoring

```bash
# Monitor runner processes
ps aux | grep runner
netstat -tulpn | grep runner
```

### Resource Limits

```bash
# Set resource limits in systemd service
[Service]
LimitNOFILE=1024
LimitNPROC=512
MemoryLimit=2G
CPUQuota=50%
```

## Monitoring and Alerting

### Security Events to Monitor

1. **Unauthorized Access Attempts**
2. **Unusual Network Connections**
3. **Failed Authentication Events**
4. **Workflow Execution Anomalies**
5. **File System Access Violations**

### Log Analysis

```bash
# Monitor runner logs for security events
tail -f ~/actions-runner/_diag/Runner_*.log | grep -i "error\|fail\|unauthorized"

# Monitor system logs
sudo tail -f /var/log/auth.log | grep runner
```

### Alerting Configuration

Set up alerts for:
- Runner offline/disconnected
- Failed workflow executions
- Unusual resource usage
- Security policy violations

## Incident Response

### Security Incident Procedures

1. **Immediate Response**
   - Stop the runner service
   - Isolate the runner machine
   - Revoke GitHub tokens
   - Document the incident

2. **Investigation**
   - Analyze runner logs
   - Review workflow execution history
   - Check for unauthorized changes
   - Assess impact scope

3. **Recovery**
   - Rebuild runner from clean state
   - Rotate all credentials
   - Update security configurations
   - Resume operations with enhanced monitoring

### Emergency Contacts

- **Repository Owner**: [Contact Information]
- **Security Team**: [Contact Information]
- **GitHub Support**: [Support Channel]

## Compliance and Auditing

### Audit Requirements

1. **Access Logs**: Maintain logs of all runner access and activities
2. **Configuration Changes**: Track all configuration modifications
3. **Workflow Executions**: Log all workflow runs and outcomes
4. **Security Events**: Record all security-related events

### Compliance Checklist

- [ ] Runner configured with repository scope only
- [ ] Specific security labels applied
- [ ] Network access restricted to required services
- [ ] File system permissions properly configured
- [ ] Environment variables secured
- [ ] Monitoring and alerting configured
- [ ] Incident response procedures documented
- [ ] Regular security reviews scheduled

## Regular Security Reviews

### Monthly Reviews

- Review runner access logs
- Verify configuration compliance
- Update security policies
- Test incident response procedures

### Quarterly Reviews

- Rotate GitHub tokens
- Update runner software
- Review network security rules
- Conduct security assessment

### Annual Reviews

- Complete security audit
- Update security documentation
- Review and update procedures
- Security training for operators