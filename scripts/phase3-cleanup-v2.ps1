#!/usr/bin/env powershell
# Phase 3 Documentation Cleanup - Simple & Robust Version

param(
    [ValidateSet('analyze', 'dryrun', 'execute', 'validate')]
    [string]$Mode = 'analyze'
)

$docsRoot = 'C:\VCC\veritas\docs'
$archiveRoot = 'C:\VCC\veritas\.archive'
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$logFile = "C:\VCC\veritas\cleanup_phase3_$timestamp.log"

# Archive category patterns
$archiveRules = @{
    'phase-reports' = @(
        'PHASE*',
        'SESSION*',
        '*_COMPLETE*',
        '*_FINAL*'
    )
    'old-versions' = @(
        'API_V*',
        'V[0-9]*',
        'RELEASE*'
    )
    'concepts' = @(
        'KONZEPT*',
        '*_DESIGN*',
        '*_PROPOSAL*'
    )
    'deployment-logs' = @(
        'MONITORING*',
        'DEPLOYMENT_LOG*',
        '*_AUDIT*'
    )
    'session-summaries' = @(
        '*_TEST*',
        '*_EVALUATION*',
        '*_REPORT*',
        '*_STATUS*',
        'STATUS*'
    )
    'obsolete-guides' = @(
        'LEGACY*',
        'DEPRECATED*',
        'CHROMADB*',
        '*_VLLM*'
    )
}

$keepFiles = @(
    'README*',
    '_sidebar*',
    '_navbar*',
    'QUICK_START.md',
    'CONTRIBUTING*',
    'TESTING*',
    'AUTHENTICATION*',
    'ERROR_HANDLING*',
    'DEPLOYMENT_GUIDE*',
    'VERITAS_System_Overview*',
    'VERITAS_API_BACKEND*',
    'BACKEND_ARCHITECTURE*',
    'ORCHESTRATOR*',
    'PROJECT_STRUCTURE*',
    'UDS3_INTEGRATION_GUIDE*',
    'THEMIS_ADAPTER_QUICKSTART*',
    'WEBSOCKET*',
    'DATABASE_AGENT_QUICKSTART*',
    'ROADMAP*',
    'DEVELOPMENT*',
    'POLYGLOT*',
    'CHART_BUILDER*',
    'VECTOR_CHART*'
)

function Log-Msg {
    param([string]$Msg, [string]$Type = 'INFO')
    $timestamp = Get-Date -Format 'HH:mm:ss'
    $line = "[$timestamp] [$Type] $Msg"
    Write-Host $line
    Add-Content -Path $logFile -Value $line 2>$null
}

function Should-ArchiveFile {
    param([string]$FileName)

    # Check keep list first
    foreach ($pattern in $keepFiles) {
        if ($FileName -like $pattern) {
            return $false
        }
    }

    # Check archive patterns
    foreach ($category in $archiveRules.Keys) {
        foreach ($pattern in $archiveRules[$category]) {
            if ($FileName -like "$pattern.md") {
                return $true
            }
        }
    }

    return $false
}

function Get-ArchiveCategory {
    param([string]$FileName)

    foreach ($category in $archiveRules.Keys) {
        foreach ($pattern in $archiveRules[$category]) {
            if ($FileName -like "$pattern.md") {
                return $category
            }
        }
    }
    return $null
}

function Mode-Analyze {
    Log-Msg "===== PHASE 3 ANALYSIS ====="

    $files = @(Get-ChildItem -Path $docsRoot -Filter "*.md" -File -Recurse |
               Where-Object { $_.DirectoryName -eq $docsRoot })

    Log-Msg "Total Markdown files in docs/ root: $($files.Count)"
    Log-Msg ""

    $keepCount = 0
    $archiveCount = 0
    $archiveByCategory = @{}

    foreach ($category in $archiveRules.Keys) {
        $archiveByCategory[$category] = @()
    }

    foreach ($file in $files) {
        if (Should-ArchiveFile $file.Name) {
            $cat = Get-ArchiveCategory $file.Name
            if ($cat) {
                $archiveByCategory[$cat] += $file.Name
                $archiveCount++
            }
        } else {
            $keepCount++
        }
    }

    Log-Msg ""
    Log-Msg "FILES TO KEEP: $keepCount"
    foreach ($f in ($keepFiles | ForEach-Object {Get-ChildItem -Path $docsRoot -Filter $_ -ErrorAction SilentlyContinue -File}).Name | Select-Object -First 10) {
        Log-Msg "  * $f"
    }
    Log-Msg ""

    Log-Msg "FILES TO ARCHIVE: $archiveCount (by category)"
    foreach ($cat in $archiveRules.Keys) {
        $count = $archiveByCategory[$cat].Count
        if ($count -gt 0) {
            Log-Msg "  [$cat] $count files"
            foreach ($f in ($archiveByCategory[$cat] | Select-Object -First 3)) {
                Log-Msg "    - $f"
            }
            if ($count -gt 3) {
                Log-Msg "    - ... and $($count - 3) more"
            }
        }
    }

    Log-Msg ""
    Log-Msg "SUMMARY: Keep=$keepCount, Archive=$archiveCount, Total=$($files.Count)"
    Log-Msg "Reduction: -$(([math]::Round($archiveCount / $files.Count * 100)))%"
}

function Mode-DryRun {
    Log-Msg "===== PHASE 3 DRY-RUN (Preview) ====="

    $files = @(Get-ChildItem -Path $docsRoot -Filter "*.md" -File -Recurse |
               Where-Object { $_.DirectoryName -eq $docsRoot })

    $toArchive = @()
    foreach ($file in $files) {
        if (Should-ArchiveFile $file.Name) {
            $toArchive += $file
        }
    }

    Log-Msg "Would archive $($toArchive.Count) files:"
    Log-Msg ""

    foreach ($category in $archiveRules.Keys) {
        $catFiles = $toArchive | Where-Object { (Get-ArchiveCategory $_.Name) -eq $category }
        if ($catFiles.Count -gt 0) {
            Log-Msg "  .archive/$category/ ($($catFiles.Count) files)"
            foreach ($f in $catFiles | Select-Object -First 3) {
                Log-Msg "    - $($f.Name)"
            }
            if ($catFiles.Count -gt 3) {
                Log-Msg "    - ... and $($catFiles.Count - 3) more"
            }
            Log-Msg ""
        }
    }
}

function Mode-Execute {
    Log-Msg "===== PHASE 3 EXECUTE ====="
    Log-Msg "WARNING: Archiving files now..."
    Log-Msg ""

    # Create archive structure
    foreach ($category in $archiveRules.Keys) {
        $dir = Join-Path $archiveRoot $category
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Log-Msg "Created directory: $dir"
        }
    }

    $files = @(Get-ChildItem -Path $docsRoot -Filter "*.md" -File -Recurse |
               Where-Object { $_.DirectoryName -eq $docsRoot })

    $movedCount = 0

    foreach ($file in $files) {
        if (Should-ArchiveFile $file.Name) {
            $category = Get-ArchiveCategory $file.Name
            if ($category) {
                $targetDir = Join-Path $archiveRoot $category
                $targetPath = Join-Path $targetDir $file.Name

                Move-Item -Path $file.FullName -Destination $targetPath -Force -ErrorAction SilentlyContinue
                Log-Msg "Moved: $($file.Name) -> .archive/$category/"
                $movedCount++
            }
        }
    }

    Log-Msg ""
    Log-Msg "EXECUTION COMPLETE: $movedCount files moved"
}

function Mode-Validate {
    Log-Msg "===== PHASE 3 VALIDATE (Check Links) ====="
    Log-Msg "Scanning for broken internal links..."
    Log-Msg ""

    $files = @(Get-ChildItem -Path $docsRoot -Filter "*.md" -File -Recurse)
    $brokenCount = 0

    foreach ($file in $files) {
        $content = Get-Content -Path $file.FullName -Raw -ErrorAction SilentlyContinue

        # Find markdown links
        $pattern = '\[([^\]]*)\]\(([^\)]+)\)'
        $matches = [regex]::Matches($content, $pattern)

        foreach ($match in $matches) {
            $linkPath = $match.Groups[2].Value

            # Skip external/anchor links
            if ($linkPath -like 'http*' -or $linkPath -like '#*') {
                continue
            }

            # Resolve path
            $resolvedPath = Join-Path (Split-Path $file.FullName) $linkPath
            $resolvedPath = [System.IO.Path]::GetFullPath($resolvedPath)

            if (!(Test-Path $resolvedPath)) {
                Log-Msg "BROKEN: $($file.Name) -> $linkPath"
                $brokenCount++
            }
        }
    }

    Log-Msg ""
    if ($brokenCount -eq 0) {
        Log-Msg "RESULT: No broken links found! (OK)"
    } else {
        Log-Msg "RESULT: $brokenCount broken links found"
    }
}

# ===== MAIN =====

New-Item -Path $logFile -ItemType File -Force | Out-Null

Log-Msg "Phase 3 Cleanup Script"
Log-Msg "Mode: $Mode"
Log-Msg ""

switch ($Mode) {
    'analyze'  { Mode-Analyze }
    'dryrun'   { Mode-DryRun }
    'execute'  { Mode-Execute }
    'validate' { Mode-Validate }
}

Log-Msg ""
Log-Msg "Log: $logFile"
