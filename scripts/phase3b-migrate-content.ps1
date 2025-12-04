#!/usr/bin/env powershell
# Phase 3b: Content Migration - Move essential files to new categories

$docsRoot = 'C:\VCC\veritas\docs'

# Define migrations (source -> destination)
$migrations = @(
    # API Documentation
    @{ src = 'VERITAS_API_BACKEND_DOCUMENTATION.md'; dst = 'api/'; dstName = 'VERITAS_API.md' }
    @{ src = 'API_REFERENCE_HYBRID_SEARCH.md'; dst = 'api/'; dstName = 'HYBRID_SEARCH.md' }
    @{ src = 'AUTHENTICATION_GUIDE.md'; dst = 'api/'; dstName = 'AUTHENTICATION.md' }

    # Architecture Documentation
    @{ src = 'BACKEND_ARCHITECTURE_ANALYSIS.md'; dst = 'architecture/'; dstName = 'BACKEND_ARCH.md' }
    @{ src = 'ORCHESTRATOR.md'; dst = 'architecture/'; dstName = 'ORCHESTRATOR_ARCH.md' }
    @{ src = 'ORCHESTRATOR_INTEGRATION_ARCHITECTURE.md'; dst = 'architecture/'; dstName = 'ORCHESTRATOR_INTEGRATION.md' }
    @{ src = 'VERITAS_System_Overview.md'; dst = 'architecture/'; dstName = 'SYSTEM_OVERVIEW.md' }
    @{ src = 'MICROSERVICES_ARCHITECTURE.md'; dst = 'architecture/'; dstName = 'MICROSERVICES.md' }
    @{ src = 'PROCESS_TREE_ARCHITECTURE.md'; dst = 'architecture/'; dstName = 'PROCESS_TREE.md' }

    # Integration Documentation
    @{ src = 'UDS3_INTEGRATION_GUIDE.md'; dst = 'integration/'; dstName = 'UDS3_INTEGRATION.md' }
    @{ src = 'UDS3_SEARCH_API_PRODUCTION_GUIDE.md'; dst = 'integration/'; dstName = 'UDS3_PRODUCTION.md' }
    @{ src = 'THEMIS_ADAPTER_QUICKSTART.md'; dst = 'integration/'; dstName = 'THEMIS_ADAPTER.md' }
    @{ src = 'THEMIS_ADVANCED_FEATURES.md'; dst = 'integration/'; dstName = 'THEMIS_FEATURES.md' }
    @{ src = 'WEBSOCKET_QUICKSTART.md'; dst = 'integration/'; dstName = 'WEBSOCKET.md' }
    @{ src = 'WEBSOCKET_PROTOCOL.md'; dst = 'integration/'; dstName = 'WEBSOCKET_PROTOCOL.md' }
    @{ src = 'MCP_QUICK_START.md'; dst = 'integration/'; dstName = 'MCP_SERVER.md' }

    # Deployment Documentation
    @{ src = 'DEPLOYMENT_QUICKSTART.md'; dst = 'deployment/'; dstName = 'QUICKSTART.md' }

    # Development Documentation
    @{ src = 'DEVELOPMENT.md'; dst = 'development/'; dstName = 'DEVELOPMENT.md' }
    @{ src = 'TESTING.md'; dst = 'development/'; dstName = 'TESTING.md' }
    @{ src = 'TESTING_GUIDE.md'; dst = 'development/'; dstName = 'TESTING_GUIDE.md' }
    @{ src = 'CONTRIBUTING.md'; dst = 'development/'; dstName = 'CONTRIBUTING.md' }
    @{ src = 'ERROR_HANDLING_GUIDE.md'; dst = 'development/'; dstName = 'ERROR_HANDLING.md' }

    # Components Documentation
    @{ src = 'DATABASE_AGENT_QUICKSTART.md'; dst = 'components/'; dstName = 'DATABASE_AGENT.md' }
    @{ src = 'DATABASE_AGENT_EXTENSION.md'; dst = 'components/'; dstName = 'DATABASE_AGENT_EXT.md' }
    @{ src = 'HYBRID_SEARCH_DEVELOPER_GUIDE.md'; dst = 'components/'; dstName = 'HYBRID_SEARCH.md' }

    # Reference Documentation
    @{ src = 'ROADMAP.md'; dst = 'reference/'; dstName = 'ROADMAP.md' }
    @{ src = 'QUICK_REFERENCE.md'; dst = 'reference/'; dstName = 'QUICK_REFERENCE.md' }
    @{ src = 'TODO.md'; dst = 'reference/'; dstName = 'TODO.md' }
    @{ src = 'PROJECT_STRUCTURE.md'; dst = 'reference/'; dstName = 'PROJECT_STRUCTURE.md' }
    @{ src = 'LLM_PARAMETERS.md'; dst = 'reference/'; dstName = 'LLM_PARAMETERS.md' }
)

function Migrate-File {
    param($Migration)

    $srcPath = Join-Path $docsRoot $Migration.src
    $dstDir = Join-Path $docsRoot $Migration.dst
    $dstPath = Join-Path $dstDir $Migration.dstName

    if (Test-Path $srcPath) {
        # Check if destination exists
        if ((Test-Path $dstPath) -and ($srcPath -ne $dstPath)) {
            Write-Host "SKIP: $($Migration.src) -> $($Migration.dst)$($Migration.dstName) (destination exists)"
            return $false
        }

        # Create destination directory if needed
        if (!(Test-Path $dstDir)) {
            New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
        }

        # Move/rename file
        if ($srcPath -ne $dstPath) {
            Move-Item -Path $srcPath -Destination $dstPath -Force
            Write-Host "MOVED: $($Migration.src) -> $($Migration.dst)$($Migration.dstName)"
        } else {
            Write-Host "SKIP: $($Migration.src) (already in place)"
        }
        return $true
    } else {
        Write-Host "NOTFOUND: $($Migration.src)"
        return $false
    }
}

# Execute migrations
Write-Host ""
Write-Host "=== Phase 3b: Content Migration ===" 
Write-Host ""

$moved = 0
$skipped = 0
$notfound = 0

foreach ($migration in $migrations) {
    $result = Migrate-File $migration
    if ($result) {
        $moved++
    } else {
        if ((Test-Path (Join-Path $docsRoot $migration.src))) {
            $skipped++
        } else {
            $notfound++
        }
    }
}

Write-Host ""
Write-Host "=== Summary ===" 
Write-Host "Moved:    $moved"
Write-Host "Skipped:  $skipped"
Write-Host "Not Found: $notfound"
Write-Host "Total:    $($moved + $skipped + $notfound)"
