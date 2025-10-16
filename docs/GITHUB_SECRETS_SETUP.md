# GitHub Secrets Configuration Guide

This guide explains how to configure all required secrets for the VERITAS CI/CD pipeline.

## Table of Contents
1. [Required Secrets](#required-secrets)
2. [How to Add Secrets](#how-to-add-secrets)
3. [Secret Configuration Details](#secret-configuration-details)
4. [Security Best Practices](#security-best-practices)

---

## Required Secrets

### Essential Secrets (Always Required)
✅ `GITHUB_TOKEN` - Automatically provided by GitHub Actions (no configuration needed)

### Deployment Secrets

#### Staging Environment
- `KUBECONFIG_STAGING` - Kubernetes configuration for staging cluster (base64 encoded)
- `STAGING_SSH_KEY` - SSH private key for staging server
- `STAGING_USER` - SSH username for staging server
- `STAGING_HOST` - Staging server hostname or IP address

#### Production Environment
- `KUBECONFIG_PRODUCTION` - Kubernetes configuration for production cluster (base64 encoded)
- `PRODUCTION_SSH_KEY` - SSH private key for production server
- `PRODUCTION_USER` - SSH username for production server
- `PRODUCTION_HOST` - Production server hostname or IP address

### Publishing Secrets
- `PYPI_API_TOKEN` - PyPI API token for publishing Python packages (optional)
- `CODECOV_TOKEN` - Codecov API token for code coverage reports (optional)
- `SLACK_WEBHOOK` - Slack webhook URL for notifications (optional)

---

## How to Add Secrets

### Method 1: Via GitHub Web UI

1. Navigate to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Enter the secret name (e.g., `PRODUCTION_SSH_KEY`)
5. Paste the secret value
6. Click **Add secret**

### Method 2: Via GitHub CLI

```bash
# Install GitHub CLI if not already installed
# https://cli.github.com/

# Authenticate
gh auth login

# Add a secret
gh secret set SECRET_NAME --body "secret_value"

# Add a secret from a file
gh secret set SECRET_NAME < path/to/file

# List all secrets
gh secret list
```

---

## Secret Configuration Details

### 1. KUBECONFIG_STAGING

**Purpose**: Allows GitHub Actions to deploy to staging Kubernetes cluster

**How to obtain**:
```bash
# On your local machine with kubectl configured for staging
cat ~/.kube/config | base64 -w 0

# On macOS
cat ~/.kube/config | base64

# Copy the output
```

**How to add**:
```bash
# Option 1: Via file
cat ~/.kube/config | base64 | gh secret set KUBECONFIG_STAGING

# Option 2: Via GitHub UI
# Paste the base64-encoded string
```

**Testing**:
```bash
# Decode and verify
echo "YOUR_BASE64_STRING" | base64 -d
```

---

### 2. KUBECONFIG_PRODUCTION

**Purpose**: Allows GitHub Actions to deploy to production Kubernetes cluster

**Configuration**: Same as `KUBECONFIG_STAGING` but for production cluster

**⚠️ Important**: 
- Use a separate kubeconfig for production
- Limit permissions to specific namespace (e.g., `veritas-production`)
- Consider using a service account token instead of admin credentials

**Minimal Service Account Example**:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: github-deployer
  namespace: veritas-production
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer-role
  namespace: veritas-production
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "update", "patch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: deployer-binding
  namespace: veritas-production
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: deployer-role
subjects:
- kind: ServiceAccount
  name: github-deployer
  namespace: veritas-production
```

---

### 3. STAGING_SSH_KEY / PRODUCTION_SSH_KEY

**Purpose**: SSH access to deployment servers (for Docker Compose deployments)

**How to generate**:
```bash
# Generate a new SSH key pair (do NOT use your personal key)
ssh-keygen -t ed25519 -C "github-actions-staging" -f github_staging_key
# or
ssh-keygen -t rsa -b 4096 -C "github-actions-production" -f github_production_key

# This creates two files:
# - github_staging_key (private key - add to GitHub Secrets)
# - github_staging_key.pub (public key - add to server)
```

**Add public key to server**:
```bash
# Copy public key to server
ssh-copy-id -i github_staging_key.pub user@staging-server

# OR manually add to ~/.ssh/authorized_keys
cat github_staging_key.pub | ssh user@staging-server "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

**Add private key to GitHub Secrets**:
```bash
# Read the private key (NOT the .pub file)
cat github_staging_key | gh secret set STAGING_SSH_KEY

# Verify the key format (should start with "-----BEGIN OPENSSH PRIVATE KEY-----")
cat github_staging_key
```

**Test SSH access**:
```bash
ssh -i github_staging_key user@staging-server "echo 'SSH works!'"
```

---

### 4. STAGING_USER / PRODUCTION_USER

**Purpose**: SSH username for deployment servers

**Example**:
```bash
gh secret set STAGING_USER --body "deploy"
gh secret set PRODUCTION_USER --body "deploy"
```

**Best Practice**: 
- Create a dedicated deployment user (e.g., `deploy`, `github-deployer`)
- Grant only necessary permissions
- Use `sudo` for privileged operations with NOPASSWD for specific commands

**Server Setup**:
```bash
# Create deployment user
sudo useradd -m -s /bin/bash deploy

# Add to docker group (if using Docker)
sudo usermod -aG docker deploy

# Configure sudo for specific commands (optional)
sudo visudo
# Add: deploy ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose
```

---

### 5. STAGING_HOST / PRODUCTION_HOST

**Purpose**: Server hostname or IP address

**Examples**:
```bash
# Using hostname
gh secret set STAGING_HOST --body "staging.veritas.example.com"

# Using IP address
gh secret set PRODUCTION_HOST --body "192.168.1.100"
```

**Recommendation**: Use hostname with DNS for flexibility

---

### 6. PYPI_API_TOKEN

**Purpose**: Publish Python packages to PyPI

**How to obtain**:
1. Create PyPI account: https://pypi.org/account/register/
2. Verify email address
3. Enable two-factor authentication (recommended)
4. Go to Account Settings → API tokens
5. Click **Add API token**
6. Name: "VERITAS GitHub Actions"
7. Scope: "Entire account" or specific project
8. Copy the token (starts with `pypi-`)

**Add to GitHub**:
```bash
gh secret set PYPI_API_TOKEN --body "pypi-AgE..."
```

**⚠️ Important**: 
- Token is shown only once - save it securely
- Rotate token every 90 days
- Use scoped tokens when possible

---

### 7. CODECOV_TOKEN

**Purpose**: Upload code coverage reports to Codecov

**How to obtain**:
1. Sign up at https://codecov.io/
2. Link your GitHub repository
3. Go to repository settings
4. Copy the upload token

**Add to GitHub**:
```bash
gh secret set CODECOV_TOKEN --body "your-codecov-token"
```

**Note**: Optional - CI will continue without this token

---

### 8. SLACK_WEBHOOK

**Purpose**: Send release notifications to Slack

**How to obtain**:
1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Enable **Incoming Webhooks**
4. Add New Webhook to Workspace
5. Select channel (e.g., #releases)
6. Copy the webhook URL

**Add to GitHub**:
```bash
gh secret set SLACK_WEBHOOK --body "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
```

**Test webhook**:
```bash
curl -X POST $SLACK_WEBHOOK \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message from VERITAS CI/CD"}'
```

---

## Security Best Practices

### 1. Secret Rotation
- Rotate all secrets every 90 days
- Immediately rotate if:
  - Secret may have been exposed
  - Team member with access leaves
  - Suspicious activity detected

### 2. Least Privilege
- Grant minimum permissions necessary
- Use scoped tokens when available
- Separate staging and production credentials
- Use service accounts instead of personal accounts

### 3. Access Control
- Limit who can view/edit repository secrets
- Use environment-specific secrets for sensitive deployments
- Enable branch protection rules
- Require reviews for production deployments

### 4. Audit Trail
- Review GitHub Actions logs regularly
- Monitor secret usage
- Set up alerts for failed deployments
- Track who adds/modifies secrets

### 5. Backup & Recovery
- Document all secrets and where they're used
- Store backup copies in secure password manager
- Have rollback plan if secrets are compromised
- Test secret rotation process

### 6. Encryption
- All secrets in GitHub are encrypted at rest
- Use base64 encoding for kubeconfigs (then encrypted by GitHub)
- Never log secrets in workflow outputs
- Use `::add-mask::` in workflows if needed

---

## Verification Checklist

After adding all secrets, verify your configuration:

### Staging Deployment
- [ ] `KUBECONFIG_STAGING` is set and valid (if using Kubernetes)
- [ ] `STAGING_SSH_KEY` is set and can connect (if using SSH)
- [ ] `STAGING_USER` is set
- [ ] `STAGING_HOST` is set
- [ ] SSH connection works: `ssh -i key user@host "echo OK"`
- [ ] Kubernetes connection works: `kubectl --kubeconfig=config get nodes`

### Production Deployment
- [ ] `KUBECONFIG_PRODUCTION` is set and valid (if using Kubernetes)
- [ ] `PRODUCTION_SSH_KEY` is set and can connect (if using SSH)
- [ ] `PRODUCTION_USER` is set
- [ ] `PRODUCTION_HOST` is set
- [ ] SSH connection works
- [ ] Kubernetes connection works

### Publishing
- [ ] `PYPI_API_TOKEN` is set (if publishing to PyPI)
- [ ] `CODECOV_TOKEN` is set (if using Codecov)
- [ ] `SLACK_WEBHOOK` is set (if using Slack notifications)

### Testing
- [ ] Trigger CI workflow and verify it passes
- [ ] Trigger CD workflow to staging and verify deployment
- [ ] Test rollback workflow
- [ ] Verify release workflow creates releases correctly

---

## Common Issues

### Issue: "Permission denied (publickey)"
**Cause**: SSH key not properly configured

**Solution**:
1. Verify private key is in GitHub Secrets
2. Verify public key is in `~/.ssh/authorized_keys` on server
3. Check key permissions on server: `chmod 600 ~/.ssh/authorized_keys`
4. Test manually: `ssh -i private_key user@host`

---

### Issue: "kubectl: command not found" or "Unable to connect to cluster"
**Cause**: Invalid kubeconfig or cluster unreachable

**Solution**:
1. Verify kubeconfig is base64 encoded correctly
2. Decode and check kubeconfig format
3. Ensure cluster is accessible from GitHub Actions runners
4. Check if cluster requires VPN or IP whitelist

---

### Issue: "Authentication failed" for PyPI
**Cause**: Invalid or expired token

**Solution**:
1. Generate new token from PyPI
2. Update `PYPI_API_TOKEN` secret
3. Ensure token starts with `pypi-`
4. Check token scope includes your package

---

### Issue: Slack webhook returns 404
**Cause**: Invalid webhook URL

**Solution**:
1. Regenerate webhook in Slack app settings
2. Update `SLACK_WEBHOOK` secret
3. Test with curl before adding to GitHub
4. Ensure webhook is enabled

---

## Support

For additional help:
1. Check GitHub Actions logs for specific error messages
2. Review workflow YAML syntax
3. Test secrets manually before adding to GitHub
4. Contact your DevOps team

---

## Appendix: Complete Setup Script

```bash
#!/bin/bash
# setup_github_secrets.sh - Configure all GitHub secrets

echo "VERITAS CI/CD Secrets Setup"
echo "==========================="

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    echo "Install from: https://cli.github.com/"
    exit 1
fi

# Authenticate
gh auth status || gh auth login

# Staging secrets
echo "Configuring staging secrets..."
if [ -f ~/.kube/staging-config ]; then
    cat ~/.kube/staging-config | base64 -w 0 | gh secret set KUBECONFIG_STAGING
fi

if [ -f github_staging_key ]; then
    cat github_staging_key | gh secret set STAGING_SSH_KEY
fi

read -p "Staging user (e.g., deploy): " STAGING_USER
gh secret set STAGING_USER --body "$STAGING_USER"

read -p "Staging host (e.g., staging.example.com): " STAGING_HOST
gh secret set STAGING_HOST --body "$STAGING_HOST"

# Production secrets
echo "Configuring production secrets..."
if [ -f ~/.kube/production-config ]; then
    cat ~/.kube/production-config | base64 -w 0 | gh secret set KUBECONFIG_PRODUCTION
fi

if [ -f github_production_key ]; then
    cat github_production_key | gh secret set PRODUCTION_SSH_KEY
fi

read -p "Production user (e.g., deploy): " PRODUCTION_USER
gh secret set PRODUCTION_USER --body "$PRODUCTION_USER"

read -p "Production host (e.g., veritas.example.com): " PRODUCTION_HOST
gh secret set PRODUCTION_HOST --body "$PRODUCTION_HOST"

# Optional secrets
read -p "PyPI API token (or press Enter to skip): " PYPI_TOKEN
if [ -n "$PYPI_TOKEN" ]; then
    gh secret set PYPI_API_TOKEN --body "$PYPI_TOKEN"
fi

read -p "Codecov token (or press Enter to skip): " CODECOV_TOKEN
if [ -n "$CODECOV_TOKEN" ]; then
    gh secret set CODECOV_TOKEN --body "$CODECOV_TOKEN"
fi

read -p "Slack webhook URL (or press Enter to skip): " SLACK_WEBHOOK
if [ -n "$SLACK_WEBHOOK" ]; then
    gh secret set SLACK_WEBHOOK --body "$SLACK_WEBHOOK"
fi

echo "✅ Secrets configuration complete!"
echo "Run 'gh secret list' to verify"
```

**Usage**:
```bash
chmod +x setup_github_secrets.sh
./setup_github_secrets.sh
```

---

**Last Updated**: 2025-10-08  
**Version**: 1.0.0
