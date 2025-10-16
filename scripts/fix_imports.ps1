# VERITAS Import-Fix Script
# Repariert alle Import-Pfade nach Projekt-Reorganisation
# Datum: 14. Oktober 2025

param(
    [switch]$DryRun,
    [switch]$NoBackup,
    [switch]$Verbose
)

# Farben für Output
function Write-Header($text) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " $text" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Step($text) {
    Write-Host "→ $text" -ForegroundColor Yellow
}

function Write-Success($text) {
    Write-Host "  ✅ $text" -ForegroundColor Green
}

function Write-Warning2($text) {
    Write-Host "  ⚠️  $text" -ForegroundColor Yellow
}

function Write-Error2($text) {
    Write-Host "  ❌ $text" -ForegroundColor Red
}

function Write-Info($text) {
    Write-Host "  ℹ️  $text" -ForegroundColor Blue
}

# Banner
Write-Header "VERITAS Import-Fix Script"
Write-Host "Projekt-Reorganisation: Import-Pfade reparieren`n" -ForegroundColor White

if ($DryRun) {
    Write-Warning2 "DRY RUN MODE - Keine Änderungen werden gespeichert!"
}

# Import-Mapping (Alt → Neu)
$importMappings = @{
    # Shared/Core Imports
    'from veritas_core import' = 'from shared.core.veritas_core import'
    'from veritas_core\s+import' = 'from shared.core.veritas_core import'
    'import veritas_core' = 'import shared.core.veritas_core as veritas_core'
    
    # Frontend UI Imports
    'from veritas_ui_components import' = 'from frontend.ui.veritas_ui_components import'
    'from veritas_ui_components\s+import' = 'from frontend.ui.veritas_ui_components import'
    'from veritas_ui_feedback_system import' = 'from frontend.ui.veritas_ui_feedback_system import'
    'from veritas_ui_toolbar import' = 'from frontend.ui.veritas_ui_toolbar import'
    'from veritas_ui_statusbar import' = 'from frontend.ui.veritas_ui_statusbar import'
    'from veritas_ui_markdown import' = 'from frontend.ui.veritas_ui_markdown import'
    
    # Frontend Theme Imports
    'from veritas_forest_theme import' = 'from frontend.themes.veritas_forest_theme import'
    
    # Frontend Streaming Imports
    'from veritas_frontend_streaming import' = 'from frontend.streaming.veritas_frontend_streaming import'
    
    # Backend API Imports
    'from veritas_api_backend import' = 'from backend.api.veritas_api_backend import'
    'from veritas_api_backend_fixed import' = 'from backend.api.veritas_api_backend_fixed import'
    'from veritas_api_backend_streaming import' = 'from backend.api.veritas_api_backend_streaming import'
    
    # Backend Services Imports
    'from veritas_streaming_service import' = 'from backend.services.veritas_streaming_service import'
    'from veritas_streaming_progress import' = 'from shared.pipelines.veritas_streaming_progress import'
    
    # Backend Agents Imports
    'from veritas_api_agent_orchestrator import' = 'from backend.agents.veritas_api_agent_orchestrator import'
    'from veritas_api_agent_registry import' = 'from backend.agents.veritas_api_agent_registry import'
    'from veritas_api_agent_pipeline_manager import' = 'from backend.agents.veritas_api_agent_pipeline_manager import'
    'from veritas_api_agent_core_components import' = 'from backend.agents.veritas_api_agent_core_components import'
    'from veritas_api_agent_environmental import' = 'from backend.agents.veritas_api_agent_environmental import'
    'from veritas_api_agent_financial import' = 'from backend.agents.veritas_api_agent_financial import'
    'from veritas_api_agent_social import' = 'from backend.agents.veritas_api_agent_social import'
    'from veritas_api_agent_traffic import' = 'from backend.agents.veritas_api_agent_traffic import'
    'from veritas_ollama_client import' = 'from backend.agents.veritas_ollama_client import'
    'from veritas_agent_template import' = 'from backend.agents.veritas_agent_template import'
    
    # Shared Pipelines Imports
    'from veritas_export_pipeline_final import' = 'from shared.pipelines.veritas_export_pipeline_final import'
    'from veritas_standard_pipeline_orchestrator import' = 'from shared.pipelines.veritas_standard_pipeline_orchestrator import'
    
    # Frontend App Self-Reference (für UI-Module)
    'from veritas_app import' = 'from frontend.veritas_app import'
}

# WICHTIG: UDS3 und Database Imports NICHT ändern!
$excludedPatterns = @(
    'from uds3',
    'import uds3',
    'from database',
    'import database'
)

# Backup erstellen
if (-not $NoBackup -and -not $DryRun) {
    Write-Step "Erstelle Backup..."
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = "backups\import-fix-$timestamp"
    
    if (-not (Test-Path "backups")) {
        New-Item -ItemType Directory -Path "backups" | Out-Null
    }
    
    New-Item -ItemType Directory -Path $backupDir | Out-Null
    
    # Backup aller Python-Dateien
    Get-ChildItem -Recurse -Include *.py | ForEach-Object {
        $relativePath = $_.FullName.Replace((Get-Location).Path, "").TrimStart("\")
        $backupPath = Join-Path $backupDir $relativePath
        $backupFolder = Split-Path $backupPath -Parent
        
        if (-not (Test-Path $backupFolder)) {
            New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null
        }
        
        Copy-Item $_.FullName $backupPath -Force
    }
    
    Write-Success "Backup erstellt: $backupDir"
}

# Statistiken
$stats = @{
    FilesScanned = 0
    FilesModified = 0
    ReplacementsMade = 0
    ErrorsEncountered = 0
}

# Python-Dateien finden und bearbeiten
Write-Step "Scanne Python-Dateien..."

$pythonFiles = Get-ChildItem -Recurse -Include *.py -Exclude "*__pycache__*","*backup*","*test_*"

Write-Info "Gefunden: $($pythonFiles.Count) Python-Dateien"

foreach ($file in $pythonFiles) {
    $stats.FilesScanned++
    
    if ($Verbose) {
        Write-Host "  Prüfe: $($file.Name)" -ForegroundColor Gray
    }
    
    try {
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        $originalContent = $content
        $replacementsInFile = 0
        
        # Prüfe ob Datei ausgeschlossene Imports hat (UDS3, Database)
        $hasExcludedImports = $false
        foreach ($pattern in $excludedPatterns) {
            if ($content -match $pattern) {
                $hasExcludedImports = $true
                break
            }
        }
        
        # Import-Replacements durchführen
        foreach ($oldImport in $importMappings.Keys) {
            $newImport = $importMappings[$oldImport]
            
            # Regex-basierte Ersetzung
            $pattern = $oldImport
            if ($content -match $pattern) {
                $content = $content -replace $pattern, $newImport
                $replacementsInFile++
                $stats.ReplacementsMade++
                
                if ($Verbose) {
                    Write-Host "    → $oldImport" -ForegroundColor DarkYellow
                    Write-Host "      $newImport" -ForegroundColor DarkGreen
                }
            }
        }
        
        # Änderungen speichern
        if ($content -ne $originalContent) {
            $stats.FilesModified++
            
            if (-not $DryRun) {
                Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
                Write-Success "$($file.Name) - $replacementsInFile Replacements"
            } else {
                Write-Info "$($file.Name) - $replacementsInFile Replacements (DRY RUN)"
            }
            
            if ($hasExcludedImports) {
                Write-Warning2 "$($file.Name) hat UDS3/Database Imports (nicht geändert)"
            }
        }
        
    } catch {
        $stats.ErrorsEncountered++
        Write-Error2 "Fehler bei $($file.Name): $($_.Exception.Message)"
    }
}

# Statistiken ausgeben
Write-Header "Import-Fix Abgeschlossen"

Write-Host "📊 Statistiken:" -ForegroundColor Cyan
Write-Host "  Dateien gescannt:    $($stats.FilesScanned)" -ForegroundColor White
Write-Host "  Dateien geändert:    $($stats.FilesModified)" -ForegroundColor Green
Write-Host "  Replacements:        $($stats.ReplacementsMade)" -ForegroundColor Green
Write-Host "  Fehler:              $($stats.ErrorsEncountered)" -ForegroundColor $(if ($stats.ErrorsEncountered -gt 0) { 'Red' } else { 'Green' })

if ($DryRun) {
    Write-Host "`n⚠️  DRY RUN - Keine Änderungen gespeichert!" -ForegroundColor Yellow
    Write-Host "Führe Script ohne -DryRun aus, um Änderungen anzuwenden.`n" -ForegroundColor Yellow
}

if ($stats.FilesModified -gt 0 -and -not $DryRun) {
    Write-Host "`n✅ Import-Fixes erfolgreich angewendet!" -ForegroundColor Green
    Write-Host "Nächster Schritt: Syntax-Check ausführen`n" -ForegroundColor Cyan
    Write-Host "  python -m py_compile frontend/**/*.py backend/**/*.py shared/**/*.py`n" -ForegroundColor White
}

# Syntax-Check anbieten
if ($stats.FilesModified -gt 0 -and -not $DryRun) {
    Write-Host "Syntax-Check jetzt ausführen? (j/n): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host
    
    if ($response -eq 'j' -or $response -eq 'y') {
        Write-Step "Führe Syntax-Check aus..."
        
        # Alle Python-Dateien kompilieren
        $errorFiles = @()
        
        Get-ChildItem -Recurse -Include *.py -Exclude "*__pycache__*","*backup*" | ForEach-Object {
            $result = python -m py_compile $_.FullName 2>&1
            if ($LASTEXITCODE -ne 0) {
                $errorFiles += $_.FullName
                Write-Error2 $_.Name
                Write-Host "    $result" -ForegroundColor Red
            }
        }
        
        if ($errorFiles.Count -eq 0) {
            Write-Success "Alle Dateien kompilieren erfolgreich!"
        } else {
            Write-Error2 "$($errorFiles.Count) Dateien mit Syntax-Fehlern:"
            $errorFiles | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
        }
    }
}

Write-Host "`n✅ Import-Fix Script abgeschlossen!`n" -ForegroundColor Green
