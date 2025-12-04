#!/usr/bin/env powershell
# Phase 3c: Fix Broken Links - Create missing stubs

$docsRoot = 'C:\VCC\veritas\docs'

# Define stub files to create
$stubs = @(
    # getting-started/
    @{ path = 'getting-started/INSTALLATION.md'; title = 'Installation Guide' }
    @{ path = 'getting-started/FIRST_QUERY.md'; title = 'First Query Guide' }
    @{ path = 'getting-started/TROUBLESHOOTING.md'; title = 'Troubleshooting Guide' }

    # architecture/
    @{ path = 'architecture/BACKEND_ARCHITECTURE.md'; title = 'Backend Architecture' }
    @{ path = 'architecture/FRONTEND_ARCHITECTURE.md'; title = 'Frontend Architecture' }
    @{ path = 'architecture/DATA_FLOW.md'; title = 'Data Flow' }
    @{ path = 'architecture/RAG_PIPELINE.md'; title = 'RAG Pipeline' }
    @{ path = 'architecture/AGENTS.md'; title = 'Agent Framework' }

    # api/
    @{ path = 'api/ENDPOINTS.md'; title = 'API Endpoints' }

    # integration/
    @{ path = 'integration/OLLAMA_INTEGRATION.md'; title = 'Ollama LLM Integration' }
    @{ path = 'integration/OFFICE_ADDON.md'; title = 'Office Add-In Integration' }

    # deployment/
    @{ path = 'deployment/DOCKER.md'; title = 'Docker Deployment' }
    @{ path = 'deployment/KUBERNETES.md'; title = 'Kubernetes Deployment' }
    @{ path = 'deployment/CONFIGURATION.md'; title = 'Configuration Guide' }
    @{ path = 'deployment/MONITORING.md'; title = 'Monitoring & Observability' }
    @{ path = 'deployment/TROUBLESHOOTING.md'; title = 'Deployment Troubleshooting' }

    # development/
    @{ path = 'development/CODE_STYLE.md'; title = 'Code Style Guide' }
    @{ path = 'development/DEBUGGING.md'; title = 'Debugging Guide' }

    # components/
    @{ path = 'components/RAG_SERVICE.md'; title = 'RAG Service' }
    @{ path = 'components/RERANKING.md'; title = 'Re-Ranking System' }
    @{ path = 'components/HYPOTHESIS_AGENT.md'; title = 'Hypothesis Agent' }
    @{ path = 'components/CHAT_PERSISTENCE.md'; title = 'Chat Persistence' }

    # reference/
    @{ path = 'reference/GLOSSAR.md'; title = 'Glossary' }
    @{ path = 'reference/CHANGELOG.md'; title = 'Changelog' }
    @{ path = 'reference/FAQ.md'; title = 'Frequently Asked Questions' }
    @{ path = 'reference/KNOWN_ISSUES.md'; title = 'Known Issues' }
)

function Create-StubFile {
    param($Stub)

    $fullPath = Join-Path $docsRoot $Stub.path
    $dir = Split-Path $fullPath

    # Create directory if needed
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    # Check if file already exists
    if (Test-Path $fullPath) {
        Write-Host "SKIP: $($Stub.path) (already exists)"
        return $false
    }

    # Create stub content
    $content = @"
# $($Stub.title)

**Status:** ⏳ Under Construction
**Last Updated:** 4. Dezember 2025

---

## Overview

This document is currently under construction. Content coming soon.

---

## Quick Links

- [Back to Documentation](../README.md)
- [Getting Started](../getting-started/QUICK_START.md)

"@

    # Write file
    Set-Content -Path $fullPath -Value $content -Encoding UTF8
    Write-Host "CREATE: $($Stub.path)"
    return $true
}

# Main execution
Write-Host ""
Write-Host "=== Phase 3c: Creating Missing Stub Files ==="
Write-Host ""

$created = 0
$skipped = 0

foreach ($stub in $stubs) {
    if (Create-StubFile $stub) {
        $created++
    } else {
        $skipped++
    }
}

Write-Host ""
Write-Host "=== Summary ==="
Write-Host "Created: $created"
Write-Host "Skipped: $skipped"
Write-Host "Total:   $($created + $skipped)"
