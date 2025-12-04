# Scripts - Utility & Automation Tools

## Overview

The `scripts/` directory contains utility scripts and automation tools for managing the VERITAS system, including deployment, testing, monitoring, and maintenance tasks.

## Available Scripts

### Deployment & Infrastructure

#### `manage_backend.ps1`
**Purpose:** Start, stop, and manage backend services

```bash
# Start backend in background
powershell .\scripts\manage_backend.ps1 start

# Stop backend
powershell .\scripts\manage_backend.ps1 stop

# Restart backend
powershell .\scripts\manage_backend.ps1 restart

# Get backend status
powershell .\scripts\manage_backend.ps1 status

# View backend logs
powershell .\scripts\manage_backend.ps1 logs
```

**Features:**
- Background process management
- PID file tracking
- Log file monitoring
- Health checks
- Graceful shutdown

#### `quick_test.ps1`
**Purpose:** Quick test runner for fast validation

```bash
# Run quick smoke tests
powershell .\scripts\quick_test.ps1

# Run specific category
powershell .\scripts\quick_test.ps1 -category "api"

# Verbose output
powershell .\scripts\quick_test.ps1 -verbose
```

**Features:**
- Fast subset of tests
- Quick health checks
- Smoke test validation
- Progress reporting

### Testing & Benchmarking

#### `demo_compliance.py`
**Purpose:** Demonstrate compliance with administrative law requirements

```bash
python scripts/demo_compliance.py
```

**Tests:**
- BImSchG (Federal Immission Control Act) compliance
- Environmental procedure knowledge
- Legal reference accuracy
- Regulatory requirement coverage

#### `test_semantic_cache.ps1`
**Purpose:** Test semantic caching performance

```bash
powershell .\scripts\test_semantic_cache.ps1

# Compare with non-cached version
powershell .\scripts\test_semantic_cache.ps1 -compare

# Benchmark latency
powershell .\scripts\test_semantic_cache.ps1 -benchmark
```

**Output:**
- Cache hit rates
- Latency comparisons
- Memory usage
- Performance gains

#### `test_compression_metrics.ps1`
**Purpose:** Test compression and metrics collection

```bash
powershell .\scripts\test_compression_metrics.ps1

# Test specific compression algorithm
powershell .\scripts\test_compression_metrics.ps1 -algorithm gzip

# Generate detailed metrics
powershell .\scripts\test_compression_metrics.ps1 -metrics detailed
```

**Metrics:**
- Compression ratio
- Processing time
- Memory efficiency
- Performance impact

### Integration Testing

#### `test_audit_api_integration.ps1`
**Purpose:** Test audit logging API integration

```bash
powershell .\scripts\test_audit_api_integration.ps1

# Test with specific audit level
powershell .\scripts\test_audit_api_integration.ps1 -level "detailed"

# Load test
powershell .\scripts\test_audit_api_integration.ps1 -load-test
```

**Tests:**
- Audit event creation
- Event tracking
- Log persistence
- Query capabilities
- Performance under load

#### `test_saga_api_integration.ps1`
**Purpose:** Test SAGA pattern API integration for distributed transactions

```bash
powershell .\scripts\test_saga_api_integration.ps1

# Test specific saga type
powershell .\scripts\test_saga_api_integration.ps1 -saga "process-execution"

# Test compensation
powershell .\scripts\test_saga_api_integration.ps1 -test-compensation
```

**Tests:**
- Saga orchestration
- Step execution
- Rollback/compensation
- Failure recovery
- Idempotency

#### `test_rebuild_metrics.ps1`
**Purpose:** Test system rebuild and metrics collection

```bash
powershell .\scripts\test_rebuild_metrics.ps1

# Simulate rebuild
powershell .\scripts\test_rebuild_metrics.ps1 -simulate

# Collect detailed metrics
powershell .\scripts\test_rebuild_metrics.ps1 -detailed
```

**Metrics:**
- Rebuild time
- Memory usage
- Index size
- Query performance
- Recovery validation

### API & Configuration

#### `setup.ps1` / `setup.sh`
**Purpose:** Initial system setup and configuration

```bash
# Windows
powershell .\scripts\setup.ps1

# Linux/Mac
bash scripts/setup.sh
```

**Setup Tasks:**
- Environment validation
- Dependency installation
- Configuration initialization
- Database setup
- Index creation

#### `apply_api_changes.ps1`
**Purpose:** Apply API changes and regenerate clients

```bash
powershell .\scripts\apply_api_changes.ps1

# Dry run
powershell .\scripts\apply_api_changes.ps1 -dry-run

# Force update
powershell .\scripts\apply_api_changes.ps1 -force
```

**Changes:**
- OpenAPI spec updates
- Client generation
- Schema validation
- Documentation updates
- Breaking change detection

### Analysis & Reporting

#### `analyze_bimschv_connection.py`
**Purpose:** Analyze BImSchV (Environmental Impact Assessment Act) connections

```bash
python scripts/analyze_bimschv_connection.py

# Generate report
python scripts/analyze_bimschv_connection.py --report

# Detailed analysis
python scripts/analyze_bimschv_connection.py --detailed
```

**Analysis:**
- Regulation mapping
- Requirement coverage
- Gap identification
- Compliance status

#### `debug_ollama_integration.py`
**Purpose:** Debug and diagnose Ollama LLM integration

```bash
python scripts/debug_ollama_integration.py

# Test connectivity
python scripts/debug_ollama_integration.py --test-connection

# Performance diagnostics
python scripts/debug_ollama_integration.py --diagnostics

# Verbose logging
python scripts/debug_ollama_integration.py --verbose
```

**Diagnostics:**
- Connection status
- Model availability
- Response times
- Error identification
- Performance metrics

#### `native_ollama_integration.py`
**Purpose:** Test native Ollama integration without wrappers

```bash
python scripts/native_ollama_integration.py

# Benchmark
python scripts/native_ollama_integration.py --benchmark

# Custom model
python scripts/native_ollama_integration.py --model "custom-model"
```

**Tests:**
- Direct API connectivity
- Model loading
- Inference speed
- Response quality
- Error handling

#### `debug_frontend.py`
**Purpose:** Debug frontend issues and connectivity

```bash
python scripts/debug_frontend.py

# Check API connectivity
python scripts/debug_frontend.py --api-check

# Performance analysis
python scripts/debug_frontend.py --performance

# Detailed logs
python scripts/debug_frontend.py --verbose
```

**Debugging:**
- API endpoint testing
- Performance analysis
- Network diagnostics
- Error tracing
- Log collection

### Monitoring & Logging

#### `monitor_token_budgets.py`
**Purpose:** Monitor token usage across system

```bash
python scripts/monitor_token_budgets.py

# Generate report
python scripts/monitor_token_budgets.py --report

# Real-time monitoring
python scripts/monitor_token_budgets.py --realtime

# Historical analysis
python scripts/monitor_token_budgets.py --history
```

**Monitoring:**
- Token consumption tracking
- Budget utilization
- Cost analysis
- Alerts and warnings
- Trend analysis

#### `dashboard_token_budgets.py`
**Purpose:** Generate dashboard for token budget visualization

```bash
python scripts/dashboard_token_budgets.py

# Generate HTML dashboard
python scripts/dashboard_token_budgets.py --html

# JSON export
python scripts/dashboard_token_budgets.py --json
```

**Dashboard:**
- Token usage charts
- Budget status
- Cost breakdown
- Alerts
- Forecasting

### Maintenance & Fixes

#### `fix_quotes.py`
**Purpose:** Fix quote formatting issues in documentation

```bash
python scripts/fix_quotes.py

# Process specific directory
python scripts/fix_quotes.py --directory docs/

# Dry run
python scripts/fix_quotes.py --dry-run
```

**Fixes:**
- Smart quote conversion
- Consistency validation
- Encoding preservation
- Backup creation

### Build & Compilation

#### `build.ps1` / `build.sh`
**Purpose:** Build VERITAS system

```bash
# Windows
powershell .\scripts\build.ps1

# Linux/Mac
bash scripts/build.sh

# Release build
powershell .\scripts\build.ps1 -Configuration Release

# Clean build
powershell .\scripts\build.ps1 -Clean
```

**Build Tasks:**
- Dependency compilation
- Test execution
- Documentation generation
- Package creation

### Docker & Deployment

#### `publish-all.ps1`
**Purpose:** Publish all Docker images

```bash
powershell .\scripts\publish-all.ps1

# Tag version
powershell .\scripts\publish-all.ps1 -version "1.0.0"

# Dry run
powershell .\scripts\publish-all.ps1 -dry-run
```

**Publish Tasks:**
- Build Docker images
- Tag images
- Push to registry
- Verify deployment

#### `security-scan.ps1`
**Purpose:** Run security scanning tools

```bash
powershell .\scripts\security-scan.ps1

# Full scan
powershell .\scripts\security-scan.ps1 -full

# Generate report
powershell .\scripts\security-scan.ps1 -report
```

**Scanning:**
- Dependency vulnerabilities
- Code security issues
- Configuration security
- Container scanning

## Script Categories

### Infrastructure Management
- `manage_backend.ps1`
- `setup.ps1` / `setup.sh`
- `build.ps1` / `build.sh`
- `publish-all.ps1`

### Testing & Validation
- `quick_test.ps1`
- `test_semantic_cache.ps1`
- `test_compression_metrics.ps1`
- `test_audit_api_integration.ps1`
- `test_saga_api_integration.ps1`
- `test_rebuild_metrics.ps1`
- `demo_compliance.py`

### Debugging & Diagnostics
- `debug_ollama_integration.py`
- `debug_frontend.py`
- `analyze_bimschv_connection.py`
- `native_ollama_integration.py`

### Monitoring & Reporting
- `monitor_token_budgets.py`
- `dashboard_token_budgets.py`

### API & Configuration
- `apply_api_changes.ps1`

### Security & Maintenance
- `security-scan.ps1`
- `fix_quotes.py`

## Best Practices

### Running Scripts Safely

1. **Always Review First**
   ```bash
   # View script before running
   cat scripts/script_name.ps1
   ```

2. **Use Dry-Run Mode**
   ```bash
   # Test without making changes
   powershell .\scripts\script_name.ps1 -dry-run
   ```

3. **Check Prerequisites**
   ```bash
   # Verify dependencies
   powershell .\scripts\script_name.ps1 -check-deps
   ```

4. **Monitor Execution**
   ```bash
   # Verbose output
   powershell .\scripts\script_name.ps1 -verbose
   ```

### Error Handling

Scripts include comprehensive error handling:
- Input validation
- Dependency checking
- Error reporting
- Rollback capabilities
- Logging

### Logging

All scripts log to:
- Console (stdout/stderr)
- Log files in `logs/` directory
- System event logs (where applicable)

## Common Use Cases

### Daily Development Workflow
```bash
# 1. Setup environment
powershell .\scripts\setup.ps1

# 2. Build system
powershell .\scripts\build.ps1

# 3. Run quick tests
powershell .\scripts\quick_test.ps1

# 4. Start backend
powershell .\scripts\manage_backend.ps1 start
```

### Pre-Commit Checklist
```bash
# Run tests
pytest tests/

# Scan security
powershell .\scripts\security-scan.ps1

# Check code quality
pylint backend/
```

### Deployment Pipeline
```bash
# 1. Full build and test
powershell .\scripts\build.ps1 -Configuration Release

# 2. Security verification
powershell .\scripts\security-scan.ps1 -full

# 3. Publish containers
powershell .\scripts\publish-all.ps1 -version "x.y.z"
```

### Troubleshooting
```bash
# 1. Debug frontend
python scripts/debug_frontend.py --verbose

# 2. Check Ollama
python scripts/debug_ollama_integration.py --diagnostics

# 3. Monitor tokens
python scripts/monitor_token_budgets.py --realtime
```

## Contributing Scripts

### Adding New Scripts

1. **Create script in `scripts/` directory**
2. **Add comprehensive help/docstring**
3. **Implement error handling**
4. **Add dry-run capability**
5. **Update this README.md**
6. **Test thoroughly**

### Script Template

```powershell
# PSvirtualenv
<#
.SYNOPSIS
    Brief description

.DESCRIPTION
    Detailed description

.EXAMPLE
    ./script_name.ps1

.NOTES
    Author: VERITAS Team
    Date: YYYY-MM-DD
#>

param(
    [switch]$DryRun,
    [switch]$Verbose
)

# Implementation
```

## Related Documentation

- See `docs/` for system documentation
- See `DEVELOPMENT.md` for development workflow
- See `Makefile` for automation targets
- See `backend/README.md` for backend details

---

**Last Updated:** December 4, 2025
**Status:** Production Ready ✅
**Script Count:** 20+
**Coverage:** Infrastructure, Testing, Debugging, Monitoring
