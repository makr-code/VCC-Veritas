# Phase 3: Aggressive Documentation Cleanup
# ==========================================
# Archiviert 350+ veraltete Dateien in .archive/
# Behält nur 70-80 essenzielle Dateien
# 
# Usage:
#   .\phase3-cleanup.ps1 -Mode analyze   # Nur zeigen
#   .\phase3-cleanup.ps1 -Mode dryrun    # Dry-run Archivierung
#   .\phase3-cleanup.ps1 -Mode execute   # Echte Archivierung
#   .\phase3-cleanup.ps1 -Mode validate  # Nach Links suchen

param(
    [ValidateSet('analyze', 'dryrun', 'execute', 'validate', 'help')]
    [string]$Mode = 'help'
)

# ==================== CONFIG ====================
$docsRoot = 'C:\VCC\veritas\docs'
$archiveRoot = 'C:\VCC\veritas\.archive'
$logFile = "C:\VCC\veritas\cleanup_phase3_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Patterns für Archivierung
$archivePatterns = @{
    'phase-reports' = @(
        'PHASE*.md',           # PHASE_1_SUCCESS_REPORT.md, PHASE5_*.md, etc.
        'SESSION*.md',         # SESSION_SUMMARY_*.md, SESSION_PERSISTENCE_*.md
        'PHASE_*.md',
        '*_COMPLETE*.md',      # PRODUCTION_DEPLOYMENT_COMPLETE.md
        '*_FINAL*.md'          # PHASE_*_FINAL*.md, TEST_SESSION_*.md
    )
    'old-versions' = @(
        'API_V*.md',           # API_V3_COMPLETE.md, API_V3_PHASE*.md
        'V[0-9]*.md',          # V4_VS_V5_COMPARISON.md
        'RELEASE*.md',         # RELEASE_NOTES*.md (nur ältere)
        '*_V[0-9]*.md'         # Dateien mit Versionsnummern
    )
    'concepts' = @(
        'KONZEPT*.md',         # KONZEPTE, DESIGN
        '*_DESIGN*.md',        # *_DESIGN.md
        '*_PROPOSAL*.md',
        '*_PLANNING*.md',
        '*ARCHITECTURE*.md'    # ARCHITECTURE-Dateien (alte Varianten)
    )
    'deployment-logs' = @(
        'MONITORING*.md',      # MONITORING_*.md, etc.
        'DEPLOYMENT_LOG*.md',  # DEPLOYMENT_LOG*.md
        '*_AUDIT*.md',         # SECURITY_OPERATIONS_AUDIT_*.md
        '*_LOG*.md'            # Generische LOG-Dateien
    )
    'session-summaries' = @(
        'TEST*.md',            # TEST_*.md (außer TESTING.md und TESTING_GUIDE.md)
        '*_TEST*.md',          # *_TEST.md
        '*_EVALUATION*.md',
        '*_REPORT*.md',
        '*_STATUS*.md',
        'STATUS*.md'
    )
    'obsolete-guides' = @(
        'LEGACY*.md',
        'DEPRECATED*.md',
        '*_OLD*.md',
        '*_OBSOLETE*.md',
        'CHROMADB_*.md',       # Alte ChromaDB Dokumentation
        '*_VLLM*.md',
        'CLARA_*.md',
        'REFACTORING*.md'
    )
}

# Patterns FÜR BEIBEHALTUNG (prioritär)
$keepPatterns = @(
    'README.md',
    '_sidebar.md',
    '_navbar.md',
    'QUICK_START.md',           # NUR die aktuelle, nicht _V7_REAL
    'CONTRIBUTING.md',
    'TESTING.md',               # Aktueller Test-Guide
    'TESTING_GUIDE.md',
    'TESTING_CHECKLIST*.md',
    'AUTHENTICATION.md',
    'AUTHENTICATION_GUIDE.md',
    'ERROR_HANDLING_GUIDE.md',
    'DEPLOYMENT_GUIDE.md',
    'DEPLOYMENT_QUICKSTART.md',
    'DEPLOYMENT_READINESS*.md',
    'VERITAS_System_Overview.md',
    'VERITAS_API_BACKEND_DOCUMENTATION.md',
    'BACKEND_ARCHITECTURE_ANALYSIS.md',
    'ORCHESTRATOR.md',
    'PROJECT_STRUCTURE.md',
    'QUICK_REFERENCE.md',
    'UDS3_INTEGRATION_GUIDE.md',    # Nur beste Version
    'THEMIS_ADAPTER_QUICKSTART.md',
    'WEBSOCKET_*.md',
    'DATABASE_AGENT_QUICKSTART.md',
    'ROADMAP.md',
    'TODO.md',
    'DEVELOPMENT.md'
)

# Blacklist: Nie archivieren (zu neu, sehr wichtig)
$neverArchive = @(
    'POLYGLOT_EXECUTION_PLAN_ANALYSIS.md',  # 2025-12-04
    'CHART_BUILDER_INTEGRATION.md',          # 2025-12-04
    'VERITAS_RAG_WORKFLOW_ANALYSIS.md',      # 2025-12-04
    'VECTOR_CHART_AGENT*.md'                 # 2025-12-04
)

# ==================== FUNCTIONS ====================

function Write-Log {
    param($Message, $Level = 'INFO')
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logMsg = "[$timestamp] [$Level] $Message"
    Write-Host $logMsg
    Add-Content -Path $logFile -Value $logMsg
}

function Get-ArchiveCategory {
    param($FileName)
    
    foreach ($category in $archivePatterns.Keys) {
        foreach ($pattern in $archivePatterns[$category]) {
            if ($FileName -like $pattern) {
                return $category
            }
        }
    }
    return $null
}

function Should-ArchiveFile {
    param($FileName)
    
    # Check Blacklist
    foreach ($blackPattern in $neverArchive) {
        if ($FileName -like $blackPattern) {
            return $false
        }
    }
    
    # Check Keep List
    foreach ($keepPattern in $keepPatterns) {
        if ($FileName -like $keepPattern) {
            return $false
        }
    }
    
    # Check Archive Patterns
    if (Get-ArchiveCategory $FileName) {
        return $true
    }
    
    return $false
}

# ==================== MODE: ANALYZE ====================

function Mode-Analyze {
    Write-Log "===== PHASE 3 ANALYSIS ====="
    
    $files = Get-ChildItem -Path $docsRoot -Filter "*.md" -File -Recurse | 
             Where-Object { $_.DirectoryName -eq $docsRoot }
    
    Write-Log "Total Markdown files in docs/ root: $($files.Count)"
    Write-Log "  "
    
    # Analyze by category
    $stats = @{
        'keep' = @()
        'archive' = @{}
        'orphaned' = @()
    }
    
    foreach ($archiveCategory in $archivePatterns.Keys) {
        $stats.archive[$archiveCategory] = @()
    }
    
    foreach ($file in $files) {
        if (Should-ArchiveFile $file.Name) {
            $category = Get-ArchiveCategory $file.Name
            if ($category) {
                $stats.archive[$category] += $file.Name
            } else {
                $stats.orphaned += $file.Name
            }
        } else {
            $stats.keep += $file.Name
        }
    }
    
    # Report
    Write-Log "  "
    Write-Log "KEEP: $($stats.keep.Count) files"
    Write-Log "  $(($stats.keep | Select-Object -First 10) -join ', ')..."
    Write-Log "  "
    
    Write-Log "ARCHIVE (by category):"
    foreach ($category in $archivePatterns.Keys) {
        $count = $stats.archive[$category].Count
        if ($count -gt 0) {
            Write-Log "  [$category] $count files"
            # Show first 3 examples
            $examples = $stats.archive[$category] | Select-Object -First 3
            foreach ($example in $examples) {
                Write-Log "    - $example"
            }
            if ($count -gt 3) {
                Write-Log "    - ... and $($count - 3) more"
            }
        }
    }
    Write-Log "  "
    
    Write-Log "ORPHANED (not matched): $($stats.orphaned.Count) files"
    foreach ($orphan in $stats.orphaned | Select-Object -First 10) {
        Write-Log "  - $orphan"
    }
    
    # Summary
    $totalArchive = ($stats.archive.Values | ForEach-Object { $_.Count } | Measure-Object -Sum).Sum
    Write-Log "  "
    Write-Log "=== SUMMARY ==="
    Write-Log "Files to KEEP:      $($stats.keep.Count)"
    Write-Log "Files to ARCHIVE:   $totalArchive"
    Write-Log "Unmatched:          $($stats.orphaned.Count)"
    Write-Log "Total:              $($files.Count)"
    Write-Log "Reduction:          -$(($totalArchive / $files.Count * 100).ToString('F1'))%"
}

# ==================== MODE: DRY-RUN ====================

function Mode-DryRun {
    Write-Log "===== PHASE 3 DRY-RUN ====="
    Write-Log "(No files will be moved, just preview)"
    Write-Log "  "
    
    $files = Get-ChildItem -Path $docsRoot -Filter "*.md" -File -Recurse | 
             Where-Object { $_.DirectoryName -eq $docsRoot }
    
    $archiveCount = 0
    
    foreach ($category in $archivePatterns.Keys) {
        $categoryFiles = @()
        
        foreach ($file in $files) {
            if (Should-ArchiveFile $file.Name) {
                $fileCategory = Get-ArchiveCategory $file.Name
                if ($fileCategory -eq $category) {
                    $categoryFiles += $file.Name
                    $archiveCount++
                }
            }
        }
        
        if ($categoryFiles.Count -gt 0) {
            Write-Log "Would move to .archive/$category/ ($($categoryFiles.Count) files):"
            foreach ($f in $categoryFiles | Select-Object -First 5) {
                Write-Log "  - $f"
            }
            if ($categoryFiles.Count -gt 5) {
                Write-Log "  - ... and $($categoryFiles.Count - 5) more"
            }
            Write-Log "  "
        }
    }
    
    Write-Log "Total files to archive: $archiveCount"
}

# ==================== MODE: EXECUTE ====================

function Mode-Execute {
    Write-Log "===== PHASE 3 EXECUTE ====="
    Write-Log "WARNING: Archiving files now..."
    Write-Log "  "
    
    # Ensure archive dirs exist
    foreach ($category in $archivePatterns.Keys) {
        $archiveDir = Join-Path $archiveRoot $category
        if (!(Test-Path $archiveDir)) {
            New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
            Write-Log "Created: $archiveDir"
        }
    }
    
    $files = Get-ChildItem -Path $docsRoot -Filter "*.md" -File -Recurse | 
             Where-Object { $_.DirectoryName -eq $docsRoot }
    
    $movedCount = 0
    
    foreach ($file in $files) {
        if (Should-ArchiveFile $file.Name) {
            $category = Get-ArchiveCategory $file.Name
            if ($category) {
                $targetDir = Join-Path $archiveRoot $category
                $targetPath = Join-Path $targetDir $file.Name
                
                Move-Item -Path $file.FullName -Destination $targetPath -Force
                Write-Log "Moved: $($file.Name) → .archive/$category/"
                $movedCount++
            }
        }
    }
    
    Write-Log "  "
    Write-Log "=== EXECUTION COMPLETE ==="
    Write-Log "Files moved: $movedCount"
    
    # Verify
    $remaining = (Get-ChildItem -Path $docsRoot -Filter "*.md" -File -Recurse | 
                  Where-Object { $_.DirectoryName -eq $docsRoot } | Measure-Object).Count
    Write-Log "Files remaining in docs/: $remaining"
}

# ==================== MODE: VALIDATE ====================

function Mode-Validate {
    Write-Log "===== PHASE 3 VALIDATE ====="
    Write-Log "Checking for broken internal links..."
    Write-Log "  "
    
    $files = Get-ChildItem -Path $docsRoot -Filter "*.md" -File -Recurse
    $brokenLinks = @()
    
    foreach ($file in $files) {
        # Find all markdown links: [text](path)
        $content = Get-Content -Path $file.FullName -Raw
        $linkPattern = '\[([^\]]*)\]\(([^\)]+)\)'
        $matches = [regex]::Matches($content, $linkPattern)
        
        foreach ($match in $matches) {
            $linkPath = $match.Groups[2].Value
            
            # Skip external links
            if ($linkPath -like 'http*' -or $linkPath -like '#*') {
                continue
            }
            
            # Resolve relative path
            $resolvedPath = Join-Path (Split-Path $file.FullName) $linkPath
            $resolvedPath = [System.IO.Path]::GetFullPath($resolvedPath)
            
            if (!(Test-Path $resolvedPath)) {
                $brokenLinks += @{
                    File = $file.FullName
                    Link = $linkPath
                    ResolvedPath = $resolvedPath
                }
            }
        }
    }
    
    if ($brokenLinks.Count -eq 0) {
        Write-Log "✓ No broken links found!"
    } else {
        Write-Log "✗ Found $($brokenLinks.Count) broken links:"
        Write-Log "  "
        foreach ($link in $brokenLinks | Select-Object -First 20) {
            Write-Log "  In: $(Split-Path $link.File -Leaf)"
            Write-Log "    Link: $($link.Link)"
            Write-Log "    Resolved: $($link.ResolvedPath)"
            Write-Log "  "
        }
        if ($brokenLinks.Count -gt 20) {
            Write-Log "  ... and $($brokenLinks.Count - 20) more"
        }
    }
}

# ==================== MAIN ====================

# Create log file
New-Item -Path $logFile -ItemType File -Force | Out-Null
Write-Log "Phase 3 Cleanup Script Started"
Write-Log "Mode: $Mode"
Write-Log "  "

switch ($Mode) {
    'analyze'  { Mode-Analyze }
    'dryrun'   { Mode-DryRun }
    'execute'  { Mode-Execute }
    'validate' { Mode-Validate }
    'help' {
        Write-Host "Phase 3 Documentation Cleanup"
        Write-Host "============================="
        Write-Host ""
        Write-Host "USAGE:"
        Write-Host "  .\phase3-cleanup.ps1 -Mode <mode>"
        Write-Host ""
        Write-Host "MODES:"
        Write-Host "  analyze    Show what WOULD be archived (preview)"
        Write-Host "  dryrun     Full dry-run with exact targets"
        Write-Host "  execute    Actually archive files (irreversible!)"
        Write-Host "  validate   Check for broken internal links"
        Write-Host "  help       Show this message"
        Write-Host ""
        Write-Host "EXAMPLES:"
        Write-Host "  .\phase3-cleanup.ps1 -Mode analyze"
        Write-Host "  .\phase3-cleanup.ps1 -Mode dryrun"
        Write-Host "  .\phase3-cleanup.ps1 -Mode validate"
        Write-Host "  .\phase3-cleanup.ps1 -Mode execute"
        Write-Host ""
        Write-Host "WARNING: Use 'analyze' and 'dryrun' first before 'execute'!"
        Write-Host ""
        Write-Host "Log file: $logFile"
    }
}

Write-Log ""
Write-Log "Log written to: $logFile"
