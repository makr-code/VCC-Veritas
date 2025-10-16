# Phase 1 Monitoring - Quick Command Reference

**Monitoring Period:** 12.10.2025 - 26.10.2025  
**Deployment:** Phase 1 Conservative (supervisor_enabled=false)  
**Daily Time Required:** 5 minutes

---

## Daily Health Check (2 minutes)

### 1. Check Backend Status

```powershell
# Check if backend process is running
Get-Process python | Where-Object {$_.MainWindowTitle -like "*veritas*"} | Format-Table Id,ProcessName,StartTime

# Expected: Process running since 12.10.2025
```

### 2. Check Logs for Errors

```powershell
# Check last 50 lines for errors
Get-Content data\veritas_auto_server.log -Tail 50 | Select-String "ERROR"

# Expected: Only ChromaDB warnings (expected, not critical)
```

### 3. Test Backend Availability

```powershell
# Simple health check
curl http://localhost:5000/health

# Expected: HTTP 200 OK or JSON response
```

---

## Weekly Test Query (3 minutes)

### Standard Test Query

```powershell
# Test with standard administrative query
$query = @{
    query = "Welche Abstandsflächen gelten in Baden-Württemberg nach § 50 LBO BW?"
    use_rag = $true
} | ConvertTo-Json

# Send query and measure time
Measure-Command {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/v7/query" `
        -Method Post `
        -ContentType "application/json" `
        -Body $query
}

# Record response details
$response | ConvertTo-Json -Depth 10 | Out-File "monitoring_results_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
```

### Extract Key Metrics

```powershell
# Parse response (adjust path as needed)
$result = Get-Content "monitoring_results_*.json" -Raw | ConvertFrom-Json

# Execution time (from Measure-Command above)
# Confidence score
$result.confidence

# Phases executed
$result.phases_executed

# Final answer
$result.final_answer
```

### Record in Log

```
Date: ___
Query: § 50 LBO BW Abstandsflächen
Execution Time: ___ seconds (Target: 34-52s)
Confidence: ___ (Target: >0.7)
Phases: ___ (Expected: 6)
Errors: Yes/No
Notes: ___
```

---

## Quick Troubleshooting

### Backend Not Running

```powershell
# Check if process exists
Get-Process python -ErrorAction SilentlyContinue

# If not running, restart
cd C:\VCC\veritas
python start_backend.py

# Wait 10 seconds, then test
Start-Sleep -Seconds 10
curl http://localhost:5000/health
```

### Port Already in Use

```powershell
# Find process using port 5000
Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | 
    Select-Object OwningProcess | 
    ForEach-Object {Get-Process -Id $_.OwningProcess}

# Kill process if needed (use with caution!)
# Stop-Process -Id <PROCESS_ID> -Force
```

### High Response Time (>60s)

```powershell
# Check system resources
Get-Process python | Format-List ProcessName,CPU,WorkingSet,StartTime

# Check for high CPU usage
# If CPU > 90% consistently, investigate

# Check logs for bottlenecks
Get-Content data\veritas_auto_server.log -Tail 100 | 
    Select-String "slow|timeout|bottleneck"
```

### Low Confidence (<0.6)

```
Action Items:
1. Check if RAG context is relevant
2. Verify ChromaDB is available (warnings OK, errors not)
3. Test with different query
4. Review Phase 3 (Analysis) output for issues
```

### Incomplete Phases (<6)

```powershell
# Check logs for phase failures
Get-Content data\veritas_auto_server.log -Tail 200 | 
    Select-String "Phase.*failed|Phase.*error"

# Common causes:
# - Ollama timeout (increase timeout)
# - UDS3 connection issue (check databases)
# - Memory issue (check RAM usage)
```

---

## Weekly Summary Commands

### Calculate Weekly Averages

```powershell
# Aggregate all test results from week
$results = Get-ChildItem "monitoring_results_*.json" | 
    ForEach-Object {Get-Content $_.FullName | ConvertFrom-Json}

# Average execution time (manual calculation)
# Average confidence
$avgConfidence = ($results | Measure-Object -Property confidence -Average).Average

# Count errors
$errorCount = ($results | Where-Object {$_.error -ne $null}).Count
$errorRate = ($errorCount / $results.Count) * 100

Write-Host "Week Summary:"
Write-Host "  Total Queries: $($results.Count)"
Write-Host "  Avg Confidence: $avgConfidence"
Write-Host "  Error Rate: $errorRate%"
```

---

## Phase 2 Transition Commands

### When Ready to Enable Supervisor

```powershell
# 1. Backup current config
Copy-Item config\scientific_methods\default_method.json `
    config\scientific_methods\default_method_phase1_backup.json

# 2. Verify backup
Test-Path config\scientific_methods\default_method_phase1_backup.json
# Expected: True

# 3. Edit config (manual step)
notepad config\scientific_methods\default_method.json
# Change: "supervisor_enabled": false → true

# 4. Verify change
python -c "import json; c=json.load(open('config/scientific_methods/default_method.json')); print('Supervisor Enabled:', c.get('supervisor_enabled'))"
# Expected: Supervisor Enabled: True

# 5. Restart backend (stop current, start new)
# Press Ctrl+C in backend terminal, then:
python start_backend.py

# 6. Test Phase 2
python tests\test_progressive_deployment.py
# Expected: 9 phases execute (6 + 3 supervisor)
```

---

## Useful Aliases (Optional)

```powershell
# Add to PowerShell profile for quick access
# File: $PROFILE (usually C:\Users\<USER>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1)

function Check-VeritasBackend {
    Get-Process python | Where-Object {$_.MainWindowTitle -like "*veritas*"}
}

function Check-VeritasLogs {
    Get-Content C:\VCC\veritas\data\veritas_auto_server.log -Tail 50 | Select-String "ERROR"
}

function Test-VeritasHealth {
    curl http://localhost:5000/health
}

function Restart-VeritasBackend {
    Set-Location C:\VCC\veritas
    python start_backend.py
}

# Usage:
# Check-VeritasBackend
# Check-VeritasLogs
# Test-VeritasHealth
# Restart-VeritasBackend
```

---

## Monitoring Checklist (Daily)

**Morning (5 min):**
- [ ] Check backend status (running?)
- [ ] Check logs (errors?)
- [ ] Test health endpoint (responding?)

**Evening (Optional):**
- [ ] Review any user-reported issues
- [ ] Check resource usage (CPU/Memory)

**Weekly (15 min):**
- [ ] Run test query
- [ ] Calculate averages (exec time, confidence)
- [ ] Update monitoring log
- [ ] Review for Phase 2 readiness

---

## Emergency Contacts

**System Owner:** ___  
**Technical Contact:** ___  
**Escalation:** ___

---

## Quick Reference Card

```
Backend URL:     http://localhost:5000
Health Check:    curl http://localhost:5000/health
Logs:            data\veritas_auto_server.log
Config:          config\scientific_methods\default_method.json
Backup:          config\scientific_methods\default_method_v2.0.0_backup_*.json

Current Status:  Phase 1 Conservative
Supervisor:      DISABLED (false)
Phases:          6 active, 3 ready
Expected Time:   34-52s
Expected Conf:   >0.7

Rollback Time:   1-5 minutes
Phase 2 Ready:   After 2 weeks monitoring
```

---

**Last Updated:** 12. Oktober 2025  
**Next Review:** 26. Oktober 2025
