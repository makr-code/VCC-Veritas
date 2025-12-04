# Cleanup-Automation Script für VCC-Veritas Dokumentation
# Dieses Script kategorisiert und archiviert alte Dokumentationsdateien

param(
    [ValidateSet('analyze', 'archive', 'cleanup', 'validate', 'full')]
    [string]$Mode = 'analyze',
    [switch]$DryRun = $false,
    [string]$LogFile = "./docs_cleanup_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
)

$ErrorActionPreference = 'Stop'
$WarningPreference = 'Continue'

# Logging-Funktionen
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('INFO', 'WARN', 'ERROR', 'SUCCESS')]
        [string]$Level = 'INFO'
    )

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] [$Level] $Message"

    Write-Host $logEntry -ForegroundColor @{
        'INFO'    = 'Cyan'
        'WARN'    = 'Yellow'
        'ERROR'   = 'Red'
        'SUCCESS' = 'Green'
    }[$Level]

    Add-Content -Path $LogFile -Value $logEntry
}

# ============================================================================
# PHASE 1: ANALYSE
# ============================================================================

function Analyze-Documentation {
    Write-Log "🔍 Starte Dokumentation-Analyse..." "INFO"

    $docs = Get-ChildItem -Path '.' -Filter '*.md' -Recurse

    $categories = @{
        'phase_reports'     = @()
        'deployment_logs'   = @()
        'session_summaries' = @()
        'concepts'          = @()
        'current_active'    = @()
        'duplicates'        = @()
    }

    $filesByName = @{}

    foreach ($file in $docs) {
        $name = $file.Name.ToLower()
        $fullPath = $file.FullName
        $age = (Get-Date) - $file.LastWriteTime
        $ageDays = [int]$age.TotalDays

        # Kategorisierung
        if ($name -match '^phase\d+_|^phase_a\d+_') {
            $categories['phase_reports'] += @{
                Path   = $fullPath
                Name   = $file.Name
                Age    = $ageDays
                Size   = $file.Length
            }
        }
        elseif ($name -match 'deployment_|monitoring_log') {
            $categories['deployment_logs'] += @{
                Path   = $fullPath
                Name   = $file.Name
                Age    = $ageDays
                Size   = $file.Length
            }
        }
        elseif ($name -match 'session_summary|_complete\.md|_final_|_ready\.md') {
            $categories['session_summaries'] += @{
                Path   = $fullPath
                Name   = $file.Name
                Age    = $ageDays
                Size   = $file.Length
            }
        }
        elseif ($name -match '^konzept_') {
            $categories['concepts'] += @{
                Path   = $fullPath
                Name   = $file.Name
                Age    = $ageDays
                Size   = $file.Length
            }
        }
        else {
            # Prüfe auf Duplikate
            $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
            if (-not $filesByName.ContainsKey($baseName)) {
                $filesByName[$baseName] = @()
            }
            $filesByName[$baseName] += $file

            $categories['current_active'] += @{
                Path   = $fullPath
                Name   = $file.Name
                Age    = $ageDays
                Size   = $file.Length
            }
        }
    }

    # Duplikate finden
    foreach ($baseName in $filesByName.Keys) {
        if ($filesByName[$baseName].Count -gt 1) {
            Write-Log "⚠️  Duplikate gefunden: $baseName" "WARN"
            foreach ($file in $filesByName[$baseName]) {
                $categories['duplicates'] += @{
                    Path   = $file.FullName
                    Name   = $file.Name
                    Age    = ([int]((Get-Date) - $file.LastWriteTime).TotalDays)
                    Size   = $file.Length
                }
            }
        }
    }

    # Report
    Write-Log "📊 Analyse abgeschlossen:" "SUCCESS"
    Write-Log "  Phase Reports: $($categories['phase_reports'].Count)" "INFO"
    Write-Log "  Deployment Logs: $($categories['deployment_logs'].Count)" "INFO"
    Write-Log "  Session Summaries: $($categories['session_summaries'].Count)" "INFO"
    Write-Log "  Konzepte: $($categories['concepts'].Count)" "INFO"
    Write-Log "  Aktive Docs: $($categories['current_active'].Count)" "INFO"
    Write-Log "  Duplikate: $($categories['duplicates'].Count)" "INFO"

    return $categories
}

# ============================================================================
# PHASE 2: ARCHIVIERUNG
# ============================================================================

function Create-ArchiveStructure {
    Write-Log "📦 Erstelle Archive-Struktur..." "INFO"

    $archiveRoot = '.\.archive'
    $subDirs = @(
        'phase-reports',
        'deployment-logs',
        'session-summaries',
        'concepts',
        'obsolete-guides',
        'old-versions'
    )

    if (-not (Test-Path $archiveRoot)) {
        if (-not $DryRun) {
            New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null
            Write-Log "✅ Archive-Root erstellt: $archiveRoot" "SUCCESS"
        } else {
            Write-Log "🔄 [DRY-RUN] Würde Archive-Root erstellen: $archiveRoot" "INFO"
        }
    }

    foreach ($subDir in $subDirs) {
        $path = Join-Path $archiveRoot $subDir
        if (-not (Test-Path $path)) {
            if (-not $DryRun) {
                New-Item -ItemType Directory -Path $path -Force | Out-Null
                Write-Log "✅ Unterverzeichnis erstellt: $subDir" "SUCCESS"
            } else {
                Write-Log "🔄 [DRY-RUN] Würde Unterverzeichnis erstellen: $subDir" "INFO"
            }
        }
    }

    return $archiveRoot
}

function Archive-Files {
    param(
        [hashtable]$Categories,
        [string]$ArchiveRoot
    )

    Write-Log "🗂️  Starte Archivierung..." "INFO"

    $archiveMappings = @{
        'phase_reports'     = 'phase-reports'
        'deployment_logs'   = 'deployment-logs'
        'session_summaries' = 'session-summaries'
        'concepts'          = 'concepts'
    }

    foreach ($category in $archiveMappings.Keys) {
        $files = $Categories[$category]
        $targetDir = Join-Path $ArchiveRoot $archiveMappings[$category]

        Write-Log "  Archiviere $($files.Count) Dateien aus '$category'..." "INFO"

        foreach ($file in $files) {
            $sourcePath = $file.Path
            $fileName = $file.Name
            $targetPath = Join-Path $targetDir $fileName

            if (-not $DryRun) {
                Move-Item -Path $sourcePath -Destination $targetPath -Force
                Write-Log "    ✅ Archiviert: $fileName" "SUCCESS"
            } else {
                Write-Log "    🔄 [DRY-RUN] Würde archivieren: $fileName" "INFO"
            }
        }
    }

    Write-Log "✅ Archivierung abgeschlossen" "SUCCESS"
}

# ============================================================================
# PHASE 3: CLEANUP
# ============================================================================

function Remove-Obsolete {
    Write-Log "🗑️  Starte Bereinigung..." "INFO"

    $toRemove = @(
        'DOCUMENTATION_*.md',  # Alte Dokumentations-Index
        'README_OLD.md',
        '*_TEMP.md',
        'TODO_REMOVE_*.md'
    )

    foreach ($pattern in $toRemove) {
        $matches = Get-ChildItem -Path '.' -Filter $pattern -ErrorAction SilentlyContinue

        foreach ($file in $matches) {
            Write-Log "  Kandidat zur Löschung: $($file.Name)" "WARN"

            if (-not $DryRun) {
                Remove-Item -Path $file.FullName -Force
                Write-Log "    ✅ Gelöscht: $($file.Name)" "SUCCESS"
            } else {
                Write-Log "    🔄 [DRY-RUN] Würde löschen: $($file.Name)" "INFO"
            }
        }
    }

    Write-Log "✅ Bereinigung abgeschlossen" "SUCCESS"
}

# ============================================================================
# PHASE 4: VALIDIERUNG
# ============================================================================

function Validate-Documentation {
    Write-Log "🔗 Validiere Dokumentation..." "INFO"

    $docs = Get-ChildItem -Path 'docs' -Filter '*.md' -Recurse
    $brokenLinks = @()
    $missingFiles = @()

    foreach ($doc in $docs) {
        # Regex für Markdown-Links
        $content = Get-Content -Path $doc.FullName -Raw
        $linkPattern = '\[([^\]]+)\]\(([^)]+)\)'
        $matches = [regex]::Matches($content, $linkPattern)

        foreach ($match in $matches) {
            $linkText = $match.Groups[1].Value
            $linkPath = $match.Groups[2].Value

            # Nur lokale Links prüfen
            if (-not ($linkPath.StartsWith('http'))) {
                $resolvedPath = Join-Path (Split-Path $doc.FullName) $linkPath
                $resolvedPath = [IO.Path]::GetFullPath($resolvedPath)

                if (-not (Test-Path $resolvedPath)) {
                    $brokenLinks += @{
                        File = $doc.Name
                        Text = $linkText
                        Link = $linkPath
                    }
                }
            }
        }
    }

    if ($brokenLinks.Count -gt 0) {
        Write-Log "⚠️  $($brokenLinks.Count) defekte Links gefunden:" "WARN"
        foreach ($link in $brokenLinks) {
            Write-Log "  In: $($link.File) - Link: $($link.Link)" "WARN"
        }
    } else {
        Write-Log "✅ Alle Links sind gültig" "SUCCESS"
    }

    return $brokenLinks
}

# ============================================================================
# ARCHIVE-INDEX GENERIEREN
# ============================================================================

function Generate-ArchiveIndex {
    param([string]$ArchiveRoot)

    Write-Log "📝 Generiere Archive-Index..." "INFO"

    $indexContent = @"
# Dokumentations-Archiv

Dieses Verzeichnis enthält archivierte Dokumentation die nicht mehr aktiv gepflegt wird.

**Archivierungsdatum:** $(Get-Date -Format 'dd.MM.yyyy')

## Verzeichnisse

### 📋 phase-reports/
Alte Phase-Reports und Completion-Berichte (Phase 1-5, Phase A-A5)
- Zeitraum: meist 6+ Monate alt
- Grund: Historische Information, Roadmap ist in ROADMAP.md

### 📊 deployment-logs/
Deployment-Logs und Monitoring-Reports
- Zeitraum: Production Deployments >3 Monate alt
- Grund: Archiviert für Audit/Referenz

### 🔄 session-summaries/
Session-Summaries, Test-Reports und Completion-Meldungen
- Zeitraum: einzelne Entwicklungs-Sessions
- Grund: Historische Information

### 💡 concepts/
Alte Konzepte und Designvorschläge
- Grund: Teilweise implementiert, teilweise verworfen
- Status: Für Kontext siehe aktuelle Guides

### 🚫 obsolete-guides/
Veraltete API-Versionen, alte Integration-Guides
- Grund: Code wurde refaktoriert oder deprecated

### 📦 old-versions/
Ältere Releases und Versionsinformation
- Status: Nur für Referenz

## Wie findet man Informationen?

1. **Aktuelle Dokumentation:** siehe `docs/` im Root
2. **Historische Informationen:** in diesem Archiv
3. **Aktuelle Roadmap:** `docs/reference/ROADMAP.md`
4. **Changelog:** `docs/reference/CHANGELOG.md`

## Wann archiviert?

Dateien werden archiviert wenn:
- Sie älter als 3 Monate sind UND
- Keine aktive Referenzen mehr existieren UND
- Ein neueres Äquivalent vorhanden ist

## Kontakt

Fragen zur Archivierung?
→ Siehe `docs/CONTRIBUTING.md` für Kontakt-Informationen

**Letzte Aktualisierung:** $(Get-Date -Format 'dd.MM.yyyy HH:mm:ss')
"@

    $indexPath = Join-Path $ArchiveRoot 'README.md'

    if (-not $DryRun) {
        Set-Content -Path $indexPath -Value $indexContent
        Write-Log "✅ Archive-Index erstellt: README.md" "SUCCESS"
    } else {
        Write-Log "🔄 [DRY-RUN] Würde Archive-Index erstellen" "INFO"
    }
}

# ============================================================================
# MAIN
# ============================================================================

function Main {
    Write-Log "╔════════════════════════════════════════════════════════════╗" "INFO"
    Write-Log "║    VCC-Veritas Dokumentation Cleanup Tool                 ║" "INFO"
    Write-Log "║    Mode: $($Mode.PadRight(48))║" "INFO"
    Write-Log "║    Dry-Run: $($DryRun.ToString().PadRight(45))║" "INFO"
    Write-Log "╚════════════════════════════════════════════════════════════╝" "INFO"

    if ($DryRun) {
        Write-Log "🔄 DRY-RUN MODE: Keine Änderungen werden durchgeführt" "WARN"
    }

    try {
        switch ($Mode) {
            'analyze' {
                $categories = Analyze-Documentation
                Write-Log "📄 Details in Logfile: $LogFile" "INFO"
            }

            'archive' {
                $categories = Analyze-Documentation
                $archiveRoot = Create-ArchiveStructure
                Archive-Files -Categories $categories -ArchiveRoot $archiveRoot
                Generate-ArchiveIndex -ArchiveRoot $archiveRoot
                Write-Log "✅ Archivierung abgeschlossen" "SUCCESS"
            }

            'cleanup' {
                Remove-Obsolete
                Write-Log "✅ Cleanup abgeschlossen" "SUCCESS"
            }

            'validate' {
                $brokenLinks = Validate-Documentation
                Write-Log "✅ Validierung abgeschlossen" "SUCCESS"
            }

            'full' {
                Write-Log "🚀 Starte vollständiges Cleanup..." "INFO"
                $categories = Analyze-Documentation
                $archiveRoot = Create-ArchiveStructure
                Archive-Files -Categories $categories -ArchiveRoot $archiveRoot
                Generate-ArchiveIndex -ArchiveRoot $archiveRoot
                Remove-Obsolete
                $brokenLinks = Validate-Documentation
                Write-Log "✅✅✅ Vollständiges Cleanup abgeschlossen" "SUCCESS"
            }
        }

        Write-Log "📄 Detaillierter Log: $LogFile" "INFO"
    }
    catch {
        Write-Log "❌ Fehler: $_" "ERROR"
        Write-Log $_.ScriptStackTrace "ERROR"
        exit 1
    }
}

Main
