#!/usr/bin/env powershell
# Phase 3d: Final Validation - Check documentation structure

$docsRoot = 'C:\VCC\veritas\docs'
$archiveRoot = 'C:\VCC\veritas\.archive'

Write-Host ""
Write-Host "=== Phase 3d: FINAL VALIDATION ==="
Write-Host ""

# Check 1: Directory structure
Write-Host "📁 CHECK 1: Directory Structure"
Write-Host "────────────────────────────────"

$requiredDirs = @(
    'getting-started',
    'architecture',
    'api',
    'integration',
    'deployment',
    'development',
    'components',
    'reference'
)

$allDirsExist = $true
foreach ($dir in $requiredDirs) {
    $path = Join-Path $docsRoot $dir
    if (Test-Path $path) {
        $fileCount = (Get-ChildItem -Path $path -Filter "*.md" -File | Measure-Object).Count
        Write-Host "✅ $dir/ - $fileCount files"
    } else {
        Write-Host "❌ $dir/ - MISSING"
        $allDirsExist = $false
    }
}

Write-Host ""

# Check 2: Archive structure
Write-Host "📦 CHECK 2: Archive Structure"
Write-Host "────────────────────────────────"

$archiveDirs = @(
    'phase-reports',
    'session-summaries',
    'old-versions',
    'concepts',
    'obsolete-guides',
    'deployment-logs'
)

$allArchiveDirsExist = $true
foreach ($dir in $archiveDirs) {
    $path = Join-Path $archiveRoot $dir
    if (Test-Path $path) {
        $fileCount = (Get-ChildItem -Path $path -Filter "*.md" -File | Measure-Object).Count
        Write-Host "✅ $dir/ - $fileCount files"
    } else {
        Write-Host "❌ $dir/ - MISSING"
        $allArchiveDirsExist = $false
    }
}

Write-Host ""

# Check 3: Key files exist
Write-Host "📄 CHECK 3: Key Navigation Files"
Write-Host "────────────────────────────────"

$keyFiles = @(
    'README.md',
    '_sidebar.md',
    'getting-started/QUICK_START.md',
    'api/API_REFERENCE.md',
    'architecture/OVERVIEW.md',
    'deployment/DEPLOYMENT_GUIDE.md'
)

$allKeyFilesExist = $true
foreach ($file in $keyFiles) {
    $path = Join-Path $docsRoot $file
    if (Test-Path $path) {
        $size = (Get-Item $path).Length
        Write-Host "✅ $file ($([math]::Round($size/1KB))KB)"
    } else {
        Write-Host "❌ $file - MISSING"
        $allKeyFilesExist = $false
    }
}

Write-Host ""

# Check 4: File counts
Write-Host "📊 CHECK 4: File Counts"
Write-Host "────────────────────────────────"

$docsFileCount = (Get-ChildItem -Path $docsRoot -Filter "*.md" -File -Recurse | Measure-Object).Count
$archiveFileCount = (Get-ChildItem -Path $archiveRoot -Filter "*.md" -File -Recurse | Measure-Object).Count
$rootFileCount = (Get-ChildItem -Path $docsRoot -Filter "*.md" -File | Where-Object { $_.DirectoryName -eq $docsRoot } | Measure-Object).Count

Write-Host "Total docs files:       $docsFileCount"
Write-Host "Total archive files:    $archiveFileCount"
Write-Host "Files in docs/root:     $rootFileCount (target: less than 100)"
Write-Host "Files in subdirs:       $($docsFileCount - $rootFileCount) (target: more than 100)"

if ($rootFileCount -lt 100) {
    Write-Host "OK - Root file count is acceptable (under 100)"
} else {
    Write-Host "WARNING - Root file count is high ($rootFileCount)"
}

if ($docsFileCount + $archiveFileCount -gt 400) {
    Write-Host "✅ Total file preservation OK"
} else {
    Write-Host "❌ Missing files!"
}

Write-Host ""

# Check 5: README and _sidebar links
Write-Host "🔗 CHECK 5: Navigation Links"
Write-Host "────────────────────────────────"

$readmePath = Join-Path $docsRoot 'README.md'
$sidebarPath = Join-Path $docsRoot '_sidebar.md'

if (Test-Path $readmePath) {
    $readmeContent = Get-Content $readmePath -Raw

    # Check for category section links
    $categories = @('getting-started', 'architecture', 'api', 'integration', 'deployment', 'development', 'components', 'reference')
    $missingCategories = @()

    foreach ($cat in $categories) {
        if (-not ($readmeContent -match $cat)) {
            $missingCategories += $cat
        }
    }

    if ($missingCategories.Count -eq 0) {
        Write-Host "✅ README.md - All categories referenced"
    } else {
        Write-Host "⚠️  README.md - Missing categories: $($missingCategories -join ', ')"
    }
}

if (Test-Path $sidebarPath) {
    $sidebarContent = Get-Content $sidebarPath -Raw

    # Check for archive link
    if ($sidebarContent -match '\.archive') {
        Write-Host "✅ _sidebar.md - Archive section present"
    } else {
        Write-Host "⚠️  _sidebar.md - Archive section missing"
    }

    # Count links
    $linkCount = ([regex]::Matches($sidebarContent, '\[.*?\]\(.*?\)')).Count
    Write-Host "✅ _sidebar.md - $linkCount links found"
}

Write-Host ""

# Check 6: Overall health
Write-Host "✨ CHECK 6: Overall Health"
Write-Host "────────────────────────────────"

$healthScore = 0

if ($allDirsExist) { $healthScore += 20 }
if ($allArchiveDirsExist) { $healthScore += 20 }
if ($allKeyFilesExist) { $healthScore += 20 }
if ($rootFileCount -lt 100 -and $rootFileCount -gt 0) { $healthScore += 20 }
if ($missingCategories.Count -eq 0) { $healthScore += 20 }

Write-Host "Health Score: $healthScore/100"

if ($healthScore -ge 90) {
    Write-Host "✅ EXCELLENT - Ready for production!"
} elseif ($healthScore -ge 80) {
    Write-Host "⚠️  GOOD - Minor issues to address"
} elseif ($healthScore -ge 70) {
    Write-Host "⚠️  FAIR - Some cleanup needed"
} else {
    Write-Host "❌ POOR - Needs significant work"
}

Write-Host ""
Write-Host "=== Validation Complete ==="
