#!/usr/bin/env powershell
# Phase 4: Content Consolidation - Move 177 root files to categories

param([string]$Mode = "analyze")

$docsPath = "docs"

# Define routing patterns
$routingRules = @{
    "getting-started" = @("QUICK_START", "INSTALLATION", "FIRST_", "TROUBLESHOOTING")
    "api" = @("API_", "_API", "VERITAS_API", "AUTHENTICATION")
    "architecture" = @("ARCHITECT", "BACKEND_ARCH", "ORCHESTRATOR", "SYSTEM_OVERVIEW", "FRAMEWORK", "ENGINE", "LAYER")
    "integration" = @("INTEGRATION", "UDS3", "THEMIS", "WEBSOCKET", "MCP_", "ADAPTER", "HYBRID", "POLYGLOT")
    "deployment" = @("DEPLOY", "PRODUCTION", "DOCKER", "CI/CD", "PIPELINE", "GITHUB", "SECRETS", "MTLS", "PKI")
    "development" = @("TEST", "DEBUG", "CONTRIBUTING", "ERROR_", "REFACTOR", "BUGFIX", "ANALYSIS", "MIGRATION")
    "components" = @("AGENT", "DATABASE", "CHAT", "PROMPT", "TOKEN", "SEARCH", "CACHE", "SEMANTIC", "EXECUTOR")
    "reference" = @("REFERENCE", "TODO", "STRUCTURE", "PARAMETER", "QUICK_REF", "SUMMARY", "OVERVIEW", "README")
}

function Route-File {
    param($fileName)

    foreach ($cat in $routingRules.GetEnumerator()) {
        foreach ($pattern in $cat.Value) {
            if ($fileName -match $pattern) {
                return $cat.Name
            }
        }
    }

    # Special cases
    if ($fileName -match "EXPERIMENT|CONCEPT|FRAMEWORK|ROADMAP|STRATEGY|HYPOTHESIS") {
        return ".archive/concepts"
    }
    if ($fileName -match "SESSION|REPORT|STATUS") {
        return ".archive/session-summaries"
    }
    if ($fileName -match "LEGACY_|DEPRECATED|OLD_|V1|V2|V3_") {
        return ".archive/old-versions"
    }

    return "reference"
}

function Analyze-Files {
    Write-Host "`n📊 PHASE 4 CONSOLIDATION ANALYSIS`n" -ForegroundColor Cyan

    $files = Get-ChildItem -Path $docsPath -File -Filter "*.md" -ErrorAction SilentlyContinue
    $files = $files | Where-Object {
        $_.Name -notin @("README.md", "_sidebar.md", "_navbar.md", "index.html", "QUICK_START.md", "SUMMARY.md")
    }

    Write-Host "Found $($files.Count) files to consolidate`n" -ForegroundColor Yellow

    $distribution = @{}

    foreach ($file in $files | Sort-Object Name) {
        $target = Route-File $file.Name

        if (-not $distribution.ContainsKey($target)) {
            $distribution[$target] = @()
        }

        $distribution[$target] += $file.Name
    }

    # Display plan
    Write-Host "CONSOLIDATION PLAN:`n" -ForegroundColor Green
    $distribution.GetEnumerator() | Sort-Object -Property Key | ForEach-Object {
        $category = $_.Key
        $fileCount = $_.Value.Count
        Write-Host "  📁 $category`: $fileCount files" -ForegroundColor Cyan

        $_.Value | Sort-Object | ForEach-Object {
            Write-Host "     - $_" -ForegroundColor DarkGray
        }
    }

    $totalToMove = ($files | Measure-Object).Count
    Write-Host "`n📈 SUMMARY:`n" -ForegroundColor Green
    Write-Host "  Total Files: $totalToMove" -ForegroundColor Yellow
    Write-Host "  Target Categories: $($distribution.Count)" -ForegroundColor Yellow
}

function Execute-Consolidation {
    Write-Host "`n⚙️  EXECUTING CONSOLIDATION`n" -ForegroundColor Cyan

    $files = Get-ChildItem -Path $docsPath -File -Filter "*.md" -ErrorAction SilentlyContinue
    $files = $files | Where-Object {
        $_.Name -notin @("README.md", "_sidebar.md", "_navbar.md", "index.html", "QUICK_START.md", "SUMMARY.md")
    }

    $moveCount = 0
    $errorCount = 0

    foreach ($file in $files | Sort-Object Name) {
        $target = Route-File $file.Name
        $targetDir = Join-Path $docsPath $target

        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force -ErrorAction SilentlyContinue | Out-Null
        }

        $targetPath = Join-Path $targetDir $file.Name
        $sourcePath = $file.FullName

        $moveSuccess = Move-Item -Path $sourcePath -Destination $targetPath -Force -ErrorAction SilentlyContinue -PassThru

        if ($moveSuccess) {
            Write-Host "✓ $($file.Name) → $target" -ForegroundColor Green
            $moveCount++
        } else {
            Write-Host "✗ ERROR: $($file.Name)" -ForegroundColor Red
            $errorCount++
        }
    }

    Write-Host "`n📊 EXECUTION COMPLETE:`n" -ForegroundColor Cyan
    Write-Host "  Moved: $moveCount" -ForegroundColor Green
    Write-Host "  Errors: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
}

function Validate-Structure {
    Write-Host "`n✅ VALIDATING STRUCTURE`n" -ForegroundColor Cyan

    $rootFiles = Get-ChildItem -Path $docsPath -File -Filter "*.md" -ErrorAction SilentlyContinue
    $rootFiles = $rootFiles | Where-Object {
        $_.Name -notin @("README.md", "_sidebar.md", "_navbar.md", "index.html")
    }

    if ($rootFiles.Count -gt 0) {
        Write-Host "⚠️  $($rootFiles.Count) files remain in root:" -ForegroundColor Yellow
        $rootFiles | ForEach-Object { Write-Host "     - $($_.Name)" }
    } else {
        Write-Host "✅ Root directory is clean!" -ForegroundColor Green
    }

    Write-Host "`n📁 CATEGORY DISTRIBUTION:`n" -ForegroundColor Cyan
    $categories = Get-ChildItem -Path $docsPath -Directory -ErrorAction SilentlyContinue
    foreach ($cat in $categories | Sort-Object Name) {
        $count = (Get-ChildItem -Path $cat.FullName -File -Filter "*.md" -ErrorAction SilentlyContinue | Measure-Object).Count
        Write-Host "  $($cat.Name): $count files" -ForegroundColor DarkGray
    }

    $totalMd = (Get-ChildItem -Path $docsPath -File -Filter "*.md" -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host "`n  TOTAL: $totalMd Markdown files" -ForegroundColor Cyan
}

# Main
switch ($Mode) {
    "analyze" {
        Analyze-Files
    }
    "execute" {
        Execute-Consolidation
    }
    "validate" {
        Validate-Structure
    }
    default {
        Write-Host @"

PHASE 4: CONTENT CONSOLIDATION

USAGE: .\phase4-consolidate-v2.ps1 -Mode <mode>

MODES:
  analyze   - Show consolidation plan (default)
  execute   - Execute the consolidation
  validate  - Check results

EXAMPLE:
  .\phase4-consolidate-v2.ps1 -Mode analyze
  .\phase4-consolidate-v2.ps1 -Mode execute
  .\phase4-consolidate-v2.ps1 -Mode validate

"@
    }
}

Write-Host "`n"
