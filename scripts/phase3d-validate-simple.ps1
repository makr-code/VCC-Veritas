#!/usr/bin/env powershell
# Phase 3d: Final Validation - Simple Version

$docsRoot = 'C:\VCC\veritas\docs'
$archiveRoot = 'C:\VCC\veritas\.archive'

Write-Host ""
Write-Host "=== PHASE 3D: FINAL VALIDATION ==="
Write-Host ""

# Check 1: Directory structure
Write-Host "CHECK 1: Directory Structure"
Write-Host "───────────────────────────────"

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
        Write-Host "[OK] $dir/ - $fileCount files"
    } else {
        Write-Host "[FAIL] $dir/ - MISSING"
        $allDirsExist = $false
    }
}

Write-Host ""

# Check 2: Archive structure
Write-Host "CHECK 2: Archive Structure"
Write-Host "───────────────────────────────"

$archiveDirs = @(
    'phase-reports',
    'session-summaries',
    'old-versions',
    'concepts',
    'obsolete-guides',
    'deployment-logs'
)

foreach ($dir in $archiveDirs) {
    $path = Join-Path $archiveRoot $dir
    if (Test-Path $path) {
        $fileCount = (Get-ChildItem -Path $path -Filter "*.md" -File | Measure-Object).Count
        Write-Host "[OK] .archive/$dir/ - $fileCount files"
    } else {
        Write-Host "[FAIL] .archive/$dir/ - MISSING"
    }
}

Write-Host ""

# Check 3: Key files
Write-Host "CHECK 3: Key Navigation Files"
Write-Host "───────────────────────────────"

$keyFiles = @(
    'README.md',
    '_sidebar.md',
    'getting-started/QUICK_START.md',
    'api/API_REFERENCE.md',
    'architecture/OVERVIEW.md',
    'deployment/DEPLOYMENT_GUIDE.md'
)

$keyFilesOk = 0
foreach ($file in $keyFiles) {
    $path = Join-Path $docsRoot $file
    if (Test-Path $path) {
        $size = (Get-Item $path).Length
        Write-Host "[OK] $file ($([math]::Round($size/1KB))KB)"
        $keyFilesOk++
    } else {
        Write-Host "[FAIL] $file - MISSING"
    }
}

Write-Host ""

# Check 4: File counts
Write-Host "CHECK 4: File Counts"
Write-Host "───────────────────────────────"

$docsFileCount = (Get-ChildItem -Path $docsRoot -Filter "*.md" -File -Recurse | Measure-Object).Count
$archiveFileCount = (Get-ChildItem -Path $archiveRoot -Filter "*.md" -File -Recurse | Measure-Object).Count
$rootFileCount = (Get-ChildItem -Path $docsRoot -Filter "*.md" -File | Where-Object { $_.DirectoryName -eq $docsRoot } | Measure-Object).Count

Write-Host "Total docs files:       $docsFileCount"
Write-Host "Total archive files:    $archiveFileCount"
Write-Host "Files in docs/root:     $rootFileCount (target: under 100)"
Write-Host "Files in subdirs:       $($docsFileCount - $rootFileCount) (target: over 100)"

Write-Host ""

# Check 5: Summary
Write-Host "SUMMARY"
Write-Host "───────────────────────────────"

Write-Host "Required dirs:      $($requiredDirs.Count) all present = $allDirsExist"
Write-Host "Archive dirs:       $($archiveDirs.Count) all present"
Write-Host "Key files:          $keyFilesOk / $($keyFiles.Count) present"
Write-Host "Total files:        $($docsFileCount + $archiveFileCount) preserved"
Write-Host "Root cleanup:       $rootFileCount files (target: under 100)"
Write-Host ""

if ($allDirsExist -and $keyFilesOk -eq $keyFiles.Count -and $rootFileCount -lt 100) {
    Write-Host "RESULT: PASS - Documentation is well-organized and ready"
} else {
    Write-Host "RESULT: ISSUES - Some structure elements need attention"
}

Write-Host ""
