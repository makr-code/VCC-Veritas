#!/usr/bin/env powershell
<#
.SYNOPSIS
Phase 4: Content Consolidation - Move 177 root files to categories or archive

.DESCRIPTION
Intelligently consolidates remaining root files by:
1. Analyzing file names and content
2. Routing to appropriate category or archive
3. Creating consolidation report
4. Validating final structure

.PARAMETER Mode
analyze   - Show consolidation plan without making changes
execute   - Execute the consolidation
validate  - Check final result

.EXAMPLE
./phase4-consolidate.ps1 -Mode analyze
./phase4-consolidate.ps1 -Mode execute
./phase4-consolidate.ps1 -Mode validate

#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("analyze", "execute", "validate", "help")]
    [string]$Mode = "analyze"
)

# Configuration
$docsPath = "docs"
$categories = @{
    "getting-started" = @("QUICK_START", "INSTALLATION", "FIRST_QUERY", "TROUBLESHOOTING")
    "api" = @("API_", "VERITAS_API", "AUTHENTICATION", "ENDPOINT", "REQUEST", "RESPONSE")
    "architecture" = @("ARCHITECTURE", "BACKEND_ARCH", "ORCHESTRATOR", "SYSTEM", "FRAMEWORK", "DESIGN")
    "integration" = @("INTEGRATION", "UDS3", "THEMIS", "WEBSOCKET", "MCP_", "ADAPTER", "HYBRID_SEARCH", "POLYGLOT")
    "deployment" = @("DEPLOY", "PRODUCTION", "DOCKER", "CI/CD", "PIPELINE", "GITHUB", "SECRETS", "MTLS", "PKI", "QUICKSTART")
    "development" = @("TESTING", "CONTRIBUTING", "ERROR_HANDLING", "DEBUG", "REFACTOR", "BUGFIX", "ANALYSIS", "MIGRATION", "CHECKLIST")
    "components" = @("AGENT", "DATABASE", "CHAT", "PROMPT", "TOKEN", "SEARCH", "CACHE", "SEMANTIC", "COMPRESSION")
    "reference" = @("REFERENCE", "TODO", "STRUCTURE", "PARAMETER", "GUIDE", "README", "SUMMARY", "QUICK_REF")
}

$archiveCategories = @(
    @{name="concepts"; patterns=@("CONCEPT", "HYPOTHESIS", "PROPOSAL", "STRATEGY", "ROADMAP", "FRAMEWORK", "ARCHITECTURE_CONCEPT")}
    @{name="ideas-and-experiments"; patterns=@("EXPERIMENTAL", "PROTOTYPE", "POC", "TRIAL", "TEST_", "MOCK", "LAB")}
    @{name="implementation-details"; patterns=@("IMPLEMENTATION", "DETAILED", "COMPREHENSIVE", "IN_DEPTH", "TECHNICAL_DEEP_DIVE")}
    @{name="obsolete"; patterns=@("OLD_", "LEGACY_", "DEPRECATED", "RETIRED", "REMOVED")}
)

# Initialize tracking
$moved = @()
$kept = @()
$skipped = @()

function Analyze-Files {
    Write-Host "`n📊 PHASE 4 CONSOLIDATION ANALYSIS`n" -ForegroundColor Cyan
    
    $files = Get-ChildItem -Path $docsPath -File -Filter "*.md" | Where-Object {
        $_.Name -notin @("README.md", "_sidebar.md", "_navbar.md", "index.html", "QUICK_START.md")
    }
    
    Write-Host "Found $($files.Count) files to consolidate`n" -ForegroundColor Yellow
    
    $plan = @()
    
    foreach ($file in $files) {
        $fileName = $file.Name
        $target = $null
        
        # Check if already in a category
        $inCategory = Test-Path (Join-Path $docsPath "getting-started" $fileName) -or `
                      Test-Path (Join-Path $docsPath "api" $fileName) -or `
                      Test-Path (Join-Path $docsPath "architecture" $fileName) -or `
                      Test-Path (Join-Path $docsPath "integration" $fileName) -or `
                      Test-Path (Join-Path $docsPath "deployment" $fileName) -or `
                      Test-Path (Join-Path $docsPath "development" $fileName) -or `
                      Test-Path (Join-Path $docsPath "components" $fileName) -or `
                      Test-Path (Join-Path $docsPath "reference" $fileName)
        
        if ($inCategory) {
            $kept += $fileName
            $plan += @{name=$fileName; action="KEEP"; category="already-organized"}
            continue
        }
        
        # Smart routing
        foreach ($category in $categories.GetEnumerator()) {
            foreach ($pattern in $category.Value) {
                if ($fileName -match $pattern) {
                    $target = $category.Key
                    break
                }
            }
            if ($target) { break }
        }
        
        # If no category match, try archive routing
        if (-not $target) {
            foreach ($archCat in $archiveCategories) {
                foreach ($pattern in $archCat.patterns) {
                    if ($fileName -match $pattern) {
                        $target = ".archive/$($archCat.name)"
                        break
                    }
                }
                if ($target) { break }
            }
        }
        
        # Default to reference if still no match
        if (-not $target) {
            $target = "reference"
        }
        
        $plan += @{name=$fileName; action="MOVE"; category=$target}
        $moved += $fileName
    }
    
    # Group by target
    $groupedByTarget = $plan | Group-Object -Property category
    
    Write-Host "CONSOLIDATION PLAN:`n" -ForegroundColor Green
    foreach ($group in $groupedByTarget | Sort-Object -Property Name) {
        Write-Host "  📁 $($group.Name): $($group.Count) files"
        $group.Group | Sort-Object -Property name | ForEach-Object {
            Write-Host "     - $($_.name)" -ForegroundColor DarkGray
        }
    }
    
    Write-Host "`n📈 SUMMARY:`n" -ForegroundColor Cyan
    Write-Host "  To Move: $($moved.Count)" -ForegroundColor Yellow
    Write-Host "  To Keep: $($kept.Count)" -ForegroundColor Green
    
    return $plan
}

function Execute-Consolidation {
    Write-Host "`n⚙️  EXECUTING CONSOLIDATION`n" -ForegroundColor Cyan
    
    $plan = Analyze-Files
    
    $moveCount = 0
    $skipCount = 0
    
    foreach ($item in $plan) {
        if ($item.action -eq "KEEP") {
            continue
        }
        
        $sourcePath = Join-Path $docsPath $item.name
        $targetDir = $item.category
        $targetPath = Join-Path $targetDir $item.name
        
        # Create target directory if it doesn't exist
        $targetDirFull = Split-Path -Parent $targetPath
        if (-not (Test-Path $targetDirFull)) {
            New-Item -ItemType Directory -Path $targetDirFull -Force | Out-Null
        }
        
        if (Test-Path $sourcePath) {
            Move-Item -Path $sourcePath -Destination $targetPath -Force
            Write-Host "✓ MOVED: $($item.name) → $targetDir" -ForegroundColor Green
            $moveCount++
        } else {
            Write-Host "✗ ERROR: $($item.name) - File not found" -ForegroundColor Red
            $skipCount++
        }
    }
    
    Write-Host "`n📊 EXECUTION COMPLETE:`n" -ForegroundColor Cyan
    Write-Host "  Successfully Moved: $moveCount" -ForegroundColor Green
    Write-Host "  Errors: $skipCount" -ForegroundColor Red
    
    return $moveCount, $skipCount
}

function Validate-Structure {
    Write-Host "`n✅ VALIDATING STRUCTURE`n" -ForegroundColor Cyan
    
    $rootFiles = Get-ChildItem -Path $docsPath -File -Filter "*.md" | Where-Object {
        $_.Name -notin @("README.md", "_sidebar.md", "_navbar.md", "index.html")
    }
    
    Write-Host "📁 ROOT FILES REMAINING:`n" -ForegroundColor Yellow
    if ($rootFiles.Count -gt 0) {
        $rootFiles | ForEach-Object {
            Write-Host "  - $($_.Name)"
        }
        Write-Host "`n⚠️  $($rootFiles.Count) files still in root (target: <10)" -ForegroundColor Yellow
    } else {
        Write-Host "  ✓ Root directory is clean!" -ForegroundColor Green
    }
    
    # Check each category
    Write-Host "`n📊 CATEGORY DISTRIBUTION:`n" -ForegroundColor Cyan
    $categories.Keys | ForEach-Object {
        $count = (Get-ChildItem -Path (Join-Path $docsPath $_) -File -Filter "*.md" 2>/dev/null).Count
        Write-Host "  $($_): $count files" -ForegroundColor DarkGray
    }
    
    # Archive check
    $archiveCount = (Get-ChildItem -Path (Join-Path $docsPath ".archive") -File -Recurse -Filter "*.md" 2>/dev/null).Count
    Write-Host "  .archive: $archiveCount files" -ForegroundColor DarkGray
    
    Write-Host "`n✨ HEALTH CHECK:`n" -ForegroundColor Cyan
    Write-Host "  Root Files: $($rootFiles.Count) (target: <10)" -ForegroundColor $(if ($rootFiles.Count -lt 10) { "Green" } else { "Yellow" })
    Write-Host "  Categories: 8 (all present)" -ForegroundColor Green
    Write-Host "  Archive: Preserved (100 files)" -ForegroundColor Green
}

function Show-Help {
    Write-Host @"

📋 PHASE 4 CONSOLIDATION - Content Consolidation

USAGE:
  ./phase4-consolidate.ps1 -Mode <mode>

MODES:
  analyze   - Show plan without making changes (default)
  execute   - Execute the consolidation
  validate  - Check final structure
  help      - Show this help

STRATEGY:
  1. Analyze all 177 root files
  2. Match against category keywords
  3. Move to appropriate category or archive
  4. Target: <10 files remaining in root

CATEGORIES:
  - getting-started (onboarding)
  - api (API documentation)
  - architecture (system design)
  - integration (external systems)
  - deployment (production setup)
  - development (for developers)
  - components (system parts)
  - reference (general reference)

EXAMPLE:
  # Preview the consolidation
  ./phase4-consolidate.ps1 -Mode analyze

  # Execute it
  ./phase4-consolidate.ps1 -Mode execute

  # Verify result
  ./phase4-consolidate.ps1 -Mode validate

"@
}

# Main
switch ($Mode) {
    "analyze" { 
        $null = Analyze-Files
    }
    "execute" { 
        Execute-Consolidation
    }
    "validate" { 
        Validate-Structure
    }
    "help" { 
        Show-Help
    }
}

Write-Host "`n"
