# VERITAS Framework - CI/CD Pipeline Documentation

## Overview

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the VERITAS Framework. The pipeline is implemented using GitHub Actions and consists of three main workflows:

1. **CI (Continuous Integration)** - `.github/workflows/ci.yml`
2. **CD (Continuous Deployment)** - `.github/workflows/deploy.yml`
3. **Release Management** - `.github/workflows/release.yml`

---

## 1. CI Workflow (ci.yml)

### Triggers
- Push to `main`, `develop`, or `feature/**` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

### Jobs

#### 1.1 Code Quality & Linting
**Purpose**: Ensure code quality and style consistency

**Tools**:
- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting and syntax checking
- **Pylint**: Advanced static analysis

**Runs on**: Python 3.11, Ubuntu latest

**Pass Criteria**: No syntax errors (E9, F63, F7, F82), warnings are allowed

---

#### 1.2 Backend Tests
**Purpose**: Run comprehensive backend test suite

**Strategy**: Matrix testing across Python 3.10, 3.11, 3.12

**Test Types**:
1. Unit tests (`tests/`)
2. Integration tests (`backend/api/test_security_integration.py`)
3. Agent tests (excluding load performance tests)

**Dependencies**:
- pytest, pytest-cov, pytest-asyncio, pytest-timeout, pytest-xdist
- PyJWT, psutil
- All requirements.txt packages

**Timeouts**:
- Unit tests: 10 minutes
- Integration tests: 5 minutes
- Agent tests: 10 minutes

**Pass Criteria**: All tests pass on all Python versions

---

#### 1.3 Frontend Tests
**Purpose**: Test frontend application

**Strategy**: Matrix testing across Node.js 18, 20

**Test Types**:
1. Linting (ESLint/TSLint)
2. Unit/Integration tests
3. Build verification

**Timeouts**:
- Tests: 5 minutes
- Build: 10 minutes

**Pass Criteria**: All tests pass and build succeeds

---

#### 1.4 Code Coverage
**Purpose**: Track code coverage and generate reports

**Runs on**: Python 3.11, Ubuntu latest

**Coverage Targets**:
- `backend/` module
- `shared/` module

**Excludes**: Load performance tests

**Outputs**:
1. XML coverage report (Codecov)
2. HTML coverage report (artifact)
3. Coverage badge (SVG)

**Artifacts**: Retained for 30 days

**Integration**: Uploads to Codecov (if configured)

---

#### 1.5 Performance Tests
**Purpose**: Run load and performance tests

**Test**: `backend/agents/test_load_performance_simple.py`

**Timeout**: 15 minutes

**Outputs**: Performance results JSON files

**Artifacts**: Retained for 90 days (historical analysis)

**Dependencies**: All production dependencies

---

#### 1.6 Security Scanning
**Purpose**: Identify security vulnerabilities

**Tools**:
1. **Bandit**: Python security linter
   - Scans `backend/`, `shared/`
   - Outputs JSON report
   - Low-level warnings only (non-blocking)

2. **Safety**: Dependency vulnerability scanner
   - Checks all installed packages
   - Reports known CVEs
   - Non-blocking (warnings only)

**Outputs**: Security reports (JSON)

**Artifacts**: Retained for 30 days

**Pass Criteria**: Information only, doesn't block CI

---

#### 1.7 Build Docker Images
**Purpose**: Build and test Docker images

**Images Built**:
1. Backend image (`ghcr.io/[repo]/backend`)
2. Frontend image (`ghcr.io/[repo]/frontend`)

**Registry**: GitHub Container Registry (ghcr.io)

**Tag Strategy**:
- Branch name (e.g., `main`, `develop`)
- PR number (e.g., `pr-123`)
- Semantic version (e.g., `1.2.3`, `1.2`)
- Git SHA with branch prefix (e.g., `main-abc1234`)
- `latest` (only on default branch)

**Caching**: GitHub Actions cache (type=gha)

**Push Behavior**: 
- Push on branch commits
- Don't push on pull requests (build only)

**Dependencies**: All backend and frontend tests must pass

---

#### 1.8 CI Success Check
**Purpose**: Aggregate all job results

**Checks**:
1. Linting status (warning if failed)
2. Backend tests (fail if failed)
3. Frontend tests (fail if failed)
4. Docker build (fail if failed)
5. Coverage (informational)
6. Security (informational)

**Outputs**:
- Console summary
- PR comment (on pull requests)

**Pass Criteria**: All critical jobs (tests, build) must succeed

---

### CI Pipeline Flow

```
Push/PR Trigger
    │
    ├─→ Lint (parallel)
    ├─→ Backend Tests (parallel, matrix)
    ├─→ Frontend Tests (parallel, matrix)
    │
    ↓ (after tests pass)
    │
    ├─→ Coverage (depends: backend tests)
    ├─→ Performance (depends: backend tests)
    ├─→ Security (parallel)
    │
    ↓ (after tests + coverage)
    │
    ├─→ Build Docker (depends: backend + frontend tests)
    │
    ↓ (always runs)
    │
    └─→ CI Success Check (aggregates all results)
```

---

## 2. CD Workflow (deploy.yml)

### Triggers
- Push to `main` branch
- Push tags matching `v*.*.*` (e.g., v1.2.3)
- Published releases
- Manual workflow dispatch (with environment selection)

### Environments
- **Staging**: For testing before production
- **Production**: Live deployment

---

### Jobs

#### 2.1 Setup Deployment
**Purpose**: Determine deployment environment and version

**Logic**:
- Manual dispatch → Use input environment
- Release/Tag → Production
- Main branch → Staging

**Version Detection**:
- Manual dispatch → Use input version
- Tag → Extract from tag name
- Default → `latest`

**Deploy Check**: Only deploy on `main` branch or tags

**Outputs**:
- `environment`: Target environment
- `version`: Version to deploy
- `deploy`: Boolean (should deploy)

---

#### 2.2 Build Docker Images
**Purpose**: Build production-ready images

**Runs**: Only if `deploy=true`

**Permissions**:
- `contents: read` - Read repository
- `packages: write` - Push to ghcr.io

**Build Args**:
- `VERSION`: Release version
- `BUILD_DATE`: Commit timestamp
- `VCS_REF`: Git commit SHA

**Images**:
1. Backend: `ghcr.io/[repo]/backend:[version]`
2. Frontend: `ghcr.io/[repo]/frontend:[version]`

**Caching**: GitHub Actions cache (optimized)

**Tags**: See CI workflow tag strategy

---

#### 2.3 Deploy to Staging
**Purpose**: Deploy to staging environment

**Runs**: Only if environment is `staging`

**Environment**: 
- Name: `staging`
- URL: `https://staging.veritas.example.com`

**Deployment Methods**:

1. **Kubernetes** (preferred):
   - Requires: `KUBECONFIG_STAGING` secret
   - Namespace: `veritas-staging`
   - Updates image tags in manifests
   - Applies manifests with `kubectl apply`
   - Waits for rollout completion (5 min timeout)

2. **Docker Compose** (fallback):
   - Requires: `STAGING_SSH_KEY`, `STAGING_USER`, `STAGING_HOST` secrets
   - SSH to staging server
   - Run `docker-compose -f docker-compose.staging.yml up -d`

**Smoke Tests**:
- Wait 30 seconds for startup
- Check `/health` endpoint
- Check `/api/health` endpoint
- Non-blocking (continue on error)

---

#### 2.4 Deploy to Production
**Purpose**: Deploy to production environment

**Runs**: Only if environment is `production`

**Environment**: 
- Name: `production`
- URL: `https://veritas.example.com`

**Pre-Deployment**:
1. **Deployment Notification**: GitHub deployment event
2. **Database Backup**:
   - SSH to production server
   - Dump PostgreSQL database
   - Compress backup with gzip
   - Store with timestamp
   - Non-blocking (continue on error)

**Deployment Methods**:

1. **Kubernetes** (preferred):
   - Requires: `KUBECONFIG_PRODUCTION` secret
   - Namespace: `veritas-production`
   - Updates image tags in manifests
   - Applies manifests with `kubectl apply`
   - Waits for rollout completion (10 min timeout)
   - Verifies with `kubectl get pods`

2. **Docker Compose** (fallback):
   - Requires: `PRODUCTION_SSH_KEY`, `PRODUCTION_USER`, `PRODUCTION_HOST` secrets
   - SSH to production server
   - **Zero-downtime deployment**:
     1. Pull new images
     2. Scale backend to 2 instances
     3. Wait 10 seconds
     4. Scale backend back to 1 instance
     5. Update frontend
   - Show deployment status

**Smoke Tests**:
- Wait 60 seconds for startup
- Check `/health` endpoint
- Check `/api/health` endpoint
- Test `/api/version` endpoint
- Parse and display response
- **Blocking** (fail if tests fail)

**Post-Deployment**:
- Update GitHub deployment status (success/failure)
- Set environment URL

---

#### 2.5 Post-Deployment Tasks
**Purpose**: Cleanup and notifications

**Runs**: Only if staging or production deployment succeeded

**Tasks**:
1. **Notify Success**: GitHub commit comment
2. **Create Release Notes** (only for tags):
   - Generate release on GitHub
   - Include version, changes, deployment info
3. **Cleanup**: Remove old Docker images (placeholder)

---

#### 2.6 Rollback (Manual Only)
**Purpose**: Emergency rollback capability

**Trigger**: Manual workflow dispatch only

**Requires**: Environment input (staging or production)

**Process**:
1. Configure kubectl for target environment
2. Run `kubectl rollout undo` for backend
3. Run `kubectl rollout undo` for frontend
4. Wait for rollout completion (5 min timeout)
5. Verify rollback success

**Use Case**: When production deployment fails or has critical issues

---

### CD Pipeline Flow

```
Trigger (main push, tag, release)
    │
    ↓
Setup Deployment
    │ (determines environment & version)
    │
    ↓
Build Docker Images
    │ (production-ready images)
    │
    ├─→ Deploy to Staging (if staging)
    │       │
    │       ├─→ Kubernetes deployment
    │       ├─→ Docker Compose (fallback)
    │       └─→ Smoke tests
    │
    ├─→ Deploy to Production (if production)
    │       │
    │       ├─→ Create deployment notification
    │       ├─→ Backup database
    │       ├─→ Kubernetes deployment
    │       ├─→ Docker Compose (fallback)
    │       ├─→ Smoke tests (blocking)
    │       └─→ Update deployment status
    │
    ↓
Post-Deployment Tasks
    │
    ├─→ Notify success
    ├─→ Create release notes
    └─→ Cleanup old images

Rollback (manual only)
    │
    └─→ kubectl rollout undo
```

---

## 3. Release Workflow (release.yml)

### Triggers
- Push tags matching `v*.*.*`
- Manual workflow dispatch (with version input)

### Permissions
- `contents: write` - Create releases
- `packages: write` - Publish packages

---

### Jobs

#### 3.1 Create Release
**Purpose**: Generate GitHub release with changelog

**Steps**:
1. **Checkout**: Full history (`fetch-depth: 0`)
2. **Determine Version**: From tag or input
3. **Generate Changelog**:
   - Find previous tag
   - Generate commit log since previous tag
   - Format as markdown
4. **Create Release**:
   - Title: `VERITAS Framework v1.2.3`
   - Body: Release highlights + changelog
   - Include installation instructions
   - Include upgrade guide
   - Include documentation links
   - Generate release notes automatically

**Outputs**:
- `version`: Release version
- `upload_url`: URL for uploading assets

**Pre-release**: Optional (workflow input)

---

#### 3.2 Build Artifacts
**Purpose**: Build release packages for multiple platforms

**Strategy**: Matrix build
- OS: Ubuntu, Windows, macOS
- Python: 3.11

**Build Process**:
1. Install build tools (`build`, `wheel`, `setuptools`)
2. Build Python package (`python -m build`)
3. Create distribution archive:
   - Linux/macOS: `.tar.gz` (gzip)
   - Windows: `.zip`
4. Upload as release asset

**Artifacts**:
- `veritas-v1.2.3-ubuntu-latest.tar.gz`
- `veritas-v1.2.3-windows-latest.zip`
- `veritas-v1.2.3-macos-latest.tar.gz`

---

#### 3.3 Publish to PyPI
**Purpose**: Publish package to Python Package Index

**Runs**: Only if `PYPI_API_TOKEN` secret is configured

**Process**:
1. Build package (`python -m build`)
2. Upload to PyPI using Twine
   - Username: `__token__`
   - Password: `PYPI_API_TOKEN` secret

**Non-blocking**: Continue on error (manual verification)

**Package Name**: `veritas-framework`

---

#### 3.4 Update Documentation
**Purpose**: Auto-update version in documentation

**Updates**:
1. **README.md**:
   - Replace version string (e.g., "Version: v1.2.3")
2. **CHANGELOG.md**:
   - Add new entry with version and date
   - Link to GitHub release
   - Prepend to existing changelog

**Commit**:
- Author: `github-actions[bot]`
- Message: `docs: Update documentation for v1.2.3`
- Push to `main` branch

**Non-blocking**: Continue on error

---

#### 3.5 Notify Release
**Purpose**: Announce release to team

**Notifications**:

1. **GitHub Commit Comment**:
   - Emoji banner
   - Version number
   - Download links
   - Docker pull command
   - Thank you message

2. **Slack** (if configured):
   - Requires: `SLACK_WEBHOOK` secret
   - Posts formatted message
   - Includes download link
   - Non-blocking (continue on error)

**Use Case**: Keep team and users informed of new releases

---

### Release Pipeline Flow

```
Tag Push (v1.2.3) or Manual Trigger
    │
    ↓
Create Release
    │ (generate changelog, create GitHub release)
    │
    ├─→ Build Artifacts (parallel)
    │       │ (Ubuntu, Windows, macOS)
    │       └─→ Upload release assets
    │
    ├─→ Publish to PyPI
    │       └─→ Upload to Python Package Index
    │
    ├─→ Update Documentation
    │       │ (README.md, CHANGELOG.md)
    │       └─→ Commit and push
    │
    ↓
Notify Release
    │
    ├─→ GitHub commit comment
    └─→ Slack notification (if configured)
```

---

## Required Secrets

### General
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

### Deployment (Staging)
- `KUBECONFIG_STAGING` - Kubernetes config (base64 encoded)
- `STAGING_SSH_KEY` - SSH private key for staging server
- `STAGING_USER` - SSH username for staging
- `STAGING_HOST` - Staging server hostname/IP

### Deployment (Production)
- `KUBECONFIG_PRODUCTION` - Kubernetes config (base64 encoded)
- `PRODUCTION_SSH_KEY` - SSH private key for production server
- `PRODUCTION_USER` - SSH username for production
- `PRODUCTION_HOST` - Production server hostname/IP

### Publishing
- `PYPI_API_TOKEN` - PyPI API token for publishing packages
- `SLACK_WEBHOOK` - Slack webhook URL for notifications (optional)

### Code Coverage
- `CODECOV_TOKEN` - Codecov API token (optional)

---

## Configuration Files Required

### Docker
- `Dockerfile` - Backend Docker image
- `frontend/Dockerfile` - Frontend Docker image
- `docker-compose.staging.yml` - Staging deployment
- `docker-compose.production.yml` - Production deployment

### Kubernetes
- `k8s/staging/*.yaml` - Staging manifests
- `k8s/production/*.yaml` - Production manifests

### Python
- `requirements.txt` - Python dependencies
- `setup.py` or `pyproject.toml` - Package configuration

### Frontend
- `frontend/package.json` - Node.js dependencies
- `frontend/package-lock.json` - Lock file

---

## Workflow Execution Examples

### Example 1: Feature Branch Push

```
1. Developer pushes to feature/new-feature
2. CI workflow triggers:
   - Lint ✅
   - Backend tests (3.10, 3.11, 3.12) ✅
   - Frontend tests (18, 20) ✅
   - Coverage ✅
   - Security scan ✅
   - Docker build (no push) ✅
   - CI success ✅
3. Result: CI badge shows passing
```

---

### Example 2: Pull Request to Main

```
1. Developer creates PR to main
2. CI workflow triggers:
   - All CI jobs run
   - Docker images built (not pushed)
   - CI success posts comment to PR
3. Reviewer approves
4. PR merged to main
5. CD workflow triggers:
   - Build Docker images (pushed)
   - Deploy to staging
   - Smoke tests ✅
6. Result: Staging updated with latest code
```

---

### Example 3: Production Release

```
1. Maintainer creates tag: git tag v1.2.3
2. Maintainer pushes tag: git push origin v1.2.3
3. Release workflow triggers:
   - Create GitHub release ✅
   - Build artifacts (Linux, Windows, macOS) ✅
   - Publish to PyPI ✅
   - Update documentation ✅
   - Notify team ✅
4. CD workflow triggers:
   - Build production images ✅
   - Backup database ✅
   - Deploy to production ✅
   - Smoke tests ✅
   - Update deployment status ✅
5. Result: v1.2.3 live in production
```

---

### Example 4: Emergency Rollback

```
1. Production deployment has critical issue
2. Maintainer triggers rollback workflow:
   - Workflow dispatch → deploy.yml
   - Environment: production
3. Rollback executes:
   - kubectl rollout undo backend ✅
   - kubectl rollout undo frontend ✅
   - Wait for rollout ✅
4. Result: Previous version restored in ~5 minutes
```

---

## Best Practices

### 1. Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature development
- `hotfix/*` - Emergency fixes

### 2. Versioning
- Use semantic versioning: `MAJOR.MINOR.PATCH`
- Tag format: `v1.2.3`
- Increment MAJOR for breaking changes
- Increment MINOR for new features
- Increment PATCH for bug fixes

### 3. Testing
- All tests must pass before merge
- Maintain >80% code coverage
- Run performance tests regularly
- Security scans on every commit

### 4. Deployment
- Always deploy to staging first
- Run smoke tests after deployment
- Backup database before production deployment
- Monitor for 24 hours after production deploy

### 5. Secrets Management
- Rotate secrets regularly (every 90 days)
- Use base64 encoding for kubeconfigs
- Never commit secrets to repository
- Limit secret access to necessary workflows

### 6. Monitoring
- Check CI/CD workflow status daily
- Review security scan reports weekly
- Monitor deployment success rates
- Track performance test trends

---

## Troubleshooting

### CI Workflow Fails

**Problem**: Tests fail on specific Python version
**Solution**: 
1. Check Python version compatibility
2. Update dependencies in requirements.txt
3. Test locally with specific Python version

**Problem**: Docker build fails
**Solution**:
1. Check Dockerfile syntax
2. Verify all COPY paths exist
3. Check base image availability

### CD Workflow Fails

**Problem**: Kubernetes deployment fails
**Solution**:
1. Verify KUBECONFIG secret is valid
2. Check cluster connectivity
3. Review manifest syntax
4. Check namespace exists

**Problem**: Smoke tests fail
**Solution**:
1. Check application logs
2. Verify endpoints are correct
3. Increase wait time before tests
4. Check network connectivity

### Release Workflow Fails

**Problem**: PyPI publish fails
**Solution**:
1. Verify PYPI_API_TOKEN is valid
2. Check package name is available
3. Ensure version number is unique
4. Review package metadata

**Problem**: Changelog generation fails
**Solution**:
1. Ensure full git history exists
2. Check previous tag exists
3. Verify git log format

---

## Performance Metrics

### CI Pipeline
- **Duration**: ~15-25 minutes (full suite)
- **Parallel Jobs**: 6-8 concurrent jobs
- **Success Rate**: Target >95%

### CD Pipeline
- **Staging Deploy**: ~5-10 minutes
- **Production Deploy**: ~10-15 minutes
- **Rollback**: ~3-5 minutes

### Release Pipeline
- **Duration**: ~10-15 minutes
- **Artifact Size**: ~50-200 MB per platform

---

## Future Enhancements

1. **Automated Performance Regression Detection**
   - Compare against baseline
   - Fail if performance degrades >10%

2. **Canary Deployments**
   - Deploy to subset of production pods
   - Monitor metrics
   - Gradually roll out

3. **Blue-Green Deployment**
   - Maintain two production environments
   - Switch traffic with zero downtime

4. **Automated Rollback**
   - Monitor error rates
   - Auto-rollback if errors spike

5. **Multi-Region Deployment**
   - Deploy to multiple regions
   - Geographic load balancing

6. **Enhanced Security**
   - SAST (Static Application Security Testing)
   - DAST (Dynamic Application Security Testing)
   - Container image scanning

---

## Support

For issues with the CI/CD pipeline:
1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Contact DevOps team
4. Create issue in repository

---

**Last Updated**: 2025-10-08  
**Version**: 1.0.0  
**Status**: Production Ready ✅
