#!/usr/bin/env pwsh
<#
.SYNOPSIS
    PKI Cleanup Script - Entfernt redundante lokale PKI-Implementierung

.DESCRIPTION
    Entfernt lokale PKI-Packages und Storage, da externer PKI-Service
    unter C:\VCC\PKI verwendet wird.
    
    Erstellt vorher sichere Backups (ca_storage wird verschlüsselt!).

.EXAMPLE
    .\scripts\pki_cleanup.ps1

.NOTES
    Author: VCC Development Team
    Date: 2025-10-14
    WICHTIG: Erstellt verschlüsseltes Backup von Private Keys!
#>

# Strict Mode
$ErrorActionPreference = "Stop"

# Colors
function Write-Header($text) {
    Write-Host "`n$("=" * 80)" -ForegroundColor Cyan
    Write-Host $text -ForegroundColor Cyan
    Write-Host $("=" * 80)`n -ForegroundColor Cyan
}

function Write-Step($number, $total, $text) {
    Write-Host "[STEP $number/$total] $text" -ForegroundColor Yellow
}

function Write-Success($text) {
    Write-Host "  ✅ $text" -ForegroundColor Green
}

function Write-Warning($text) {
    Write-Host "  ⚠️  $text" -ForegroundColor Yellow
}

function Write-Error2($text) {
    Write-Host "  ❌ $text" -ForegroundColor Red
}

function Write-Info($text) {
    Write-Host "  ℹ️  $text" -ForegroundColor Cyan
}

# Start
Write-Header "PKI CLEANUP SCRIPT"
Write-Host "This script will remove redundant PKI implementations" -ForegroundColor White
Write-Host "and create secure backups before deletion.`n" -ForegroundColor White

# Confirm
Write-Warning "This will DELETE the following:"
Write-Host "  - pki/ (root PKI package)" -ForegroundColor Gray
Write-Host "  - backend/pki/ (backend PKI package)" -ForegroundColor Gray
Write-Host "  - ca_storage/ (CA certificates & private keys)" -ForegroundColor Gray
Write-Host "  - pki_storage/ (PKI storage)" -ForegroundColor Gray
Write-Host "  - tests/test_pki/ (PKI tests)" -ForegroundColor Gray
Write-Host ""

$confirmation = Read-Host "Continue? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Warning "Cleanup cancelled by user"
    exit 0
}

# Timestamp
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupRoot = "backups\pki-cleanup-$timestamp"

Write-Host ""

# ========================================
# STEP 1: Create Backup Directory
# ========================================
Write-Step 1 6 "Creating backup directory..."

try {
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    Write-Success "Backup directory created: $backupRoot"
}
catch {
    Write-Error2 "Failed to create backup directory: $_"
    exit 1
}

# ========================================
# STEP 2: Encrypted Backup of ca_storage
# ========================================
Write-Step 2 6 "Creating encrypted backup of ca_storage..."

if (Test-Path "ca_storage") {
    Write-Info "ca_storage contains PRIVATE KEYS - creating encrypted backup"
    
    # Check if 7z is available
    $has7z = Get-Command "7z" -ErrorAction SilentlyContinue
    
    if ($has7z) {
        $archivePath = "$backupRoot\ca_storage-ENCRYPTED.7z"
        Write-Info "Using 7-Zip for encryption..."
        Write-Host "  Enter password for encrypted archive:" -ForegroundColor Yellow
        
        try {
            # 7z with password prompt and AES-256 encryption
            & 7z a -p -mhe=on -t7z $archivePath ca_storage\ | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                $size = (Get-Item $archivePath).Length / 1MB
                Write-Success "Encrypted backup created: $archivePath ($([math]::Round($size, 2)) MB)"
            }
            else {
                Write-Warning "7z encryption may have failed (exit code: $LASTEXITCODE)"
            }
        }
        catch {
            Write-Warning "Encrypted backup failed: $_"
            Write-Info "Falling back to unencrypted backup..."
        }
    }
    else {
        Write-Warning "7-Zip not found - creating unencrypted backup"
        Write-Info "Install 7-Zip for encrypted backups: https://www.7-zip.org/"
    }
    
    # Fallback: Standard ZIP (unencrypted)
    if (-not (Test-Path "$backupRoot\ca_storage-ENCRYPTED.7z")) {
        try {
            Compress-Archive -Path "ca_storage\*" -DestinationPath "$backupRoot\ca_storage-UNENCRYPTED.zip" -Force
            Write-Warning "Created UNENCRYPTED backup: $backupRoot\ca_storage-UNENCRYPTED.zip"
            Write-Warning "⚠️  This contains private keys! Secure this file!"
        }
        catch {
            Write-Error2 "Backup failed: $_"
            exit 1
        }
    }
}
else {
    Write-Info "ca_storage not found - skipping"
}

# ========================================
# STEP 3: Backup other PKI components
# ========================================
Write-Step 3 6 "Backing up PKI packages..."

$componentsToBackup = @(
    @{Path = "pki"; Name = "pki-root"},
    @{Path = "backend\pki"; Name = "pki-backend"},
    @{Path = "pki_storage"; Name = "pki_storage"},
    @{Path = "tests\test_pki"; Name = "test_pki"}
)

foreach ($component in $componentsToBackup) {
    $sourcePath = $component.Path
    $destName = $component.Name
    
    if (Test-Path $sourcePath) {
        try {
            $destPath = "$backupRoot\$destName"
            Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
            
            # Count files
            $fileCount = (Get-ChildItem -Path $destPath -Recurse -File).Count
            Write-Success "Backed up: $sourcePath → $destName ($fileCount files)"
        }
        catch {
            Write-Warning "Backup failed for $sourcePath : $_"
        }
    }
    else {
        Write-Info "Not found: $sourcePath - skipping"
    }
}

# ========================================
# STEP 4: Delete PKI components
# ========================================
Write-Step 4 6 "Deleting redundant PKI components..."

$componentsToDelete = @(
    "pki",
    "backend\pki",
    "ca_storage",
    "pki_storage",
    "tests\test_pki"
)

foreach ($component in $componentsToDelete) {
    if (Test-Path $component) {
        try {
            Remove-Item -Path $component -Recurse -Force
            Write-Success "Deleted: $component"
        }
        catch {
            Write-Error2 "Failed to delete $component : $_"
        }
    }
    else {
        Write-Info "Not found: $component - skipping"
    }
}

# ========================================
# STEP 5: Update .gitignore
# ========================================
Write-Step 5 6 "Updating .gitignore..."

$gitignoreAdditions = @"

# ========================================
# PKI Storage (removed - using external C:\VCC\PKI service)
# Added: $timestamp
# ========================================
ca_storage/
pki_storage/
temp_ca.pem
backups/pki-cleanup-*/
"@

try {
    Add-Content -Path ".gitignore" -Value $gitignoreAdditions
    Write-Success ".gitignore updated"
}
catch {
    Write-Warning "Failed to update .gitignore: $_"
}

# ========================================
# STEP 6: Archive TODO document
# ========================================
Write-Step 6 6 "Archiving TODO_PKI_INTEGRATION.md..."

if (Test-Path "TODO_PKI_INTEGRATION.md") {
    try {
        # Create legacy docs folder
        New-Item -ItemType Directory -Path "docs\legacy" -Force | Out-Null
        
        # Move TODO to legacy
        Move-Item -Path "TODO_PKI_INTEGRATION.md" -Destination "docs\legacy\TODO_PKI_INTEGRATION_LEGACY.md" -Force
        Write-Success "Archived: TODO_PKI_INTEGRATION.md → docs\legacy\"
    }
    catch {
        Write-Warning "Failed to archive TODO document: $_"
    }
}
else {
    Write-Info "TODO_PKI_INTEGRATION.md not found - skipping"
}

# ========================================
# SUMMARY
# ========================================
Write-Header "CLEANUP COMPLETE"

Write-Host "✅ Redundant PKI components removed" -ForegroundColor Green
Write-Host ""

Write-Host "📦 Backups created:" -ForegroundColor Cyan
Write-Host "  Location: $backupRoot" -ForegroundColor White
if (Test-Path "$backupRoot\ca_storage-ENCRYPTED.7z") {
    Write-Host "  ✅ ca_storage: ENCRYPTED (7z with password)" -ForegroundColor Green
}
elseif (Test-Path "$backupRoot\ca_storage-UNENCRYPTED.zip") {
    Write-Host "  ⚠️  ca_storage: UNENCRYPTED (ZIP) - SECURE THIS FILE!" -ForegroundColor Yellow
}

$backupSize = (Get-ChildItem -Path $backupRoot -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "  Total size: $([math]::Round($backupSize, 2)) MB" -ForegroundColor White
Write-Host ""

Write-Host "🔄 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Create PKI client: backend/services/pki_client.py" -ForegroundColor White
Write-Host "  2. Update imports to use external PKI service" -ForegroundColor White
Write-Host "  3. Run integration tests" -ForegroundColor White
Write-Host "  4. Commit changes" -ForegroundColor White
Write-Host ""

Write-Host "📄 Documentation:" -ForegroundColor Cyan
Write-Host "  - See PKI_CLEANUP_REPORT.md for details" -ForegroundColor White
Write-Host "  - Migration guide: docs/PKI_MIGRATION_COMPLETE.md" -ForegroundColor White
Write-Host ""

Write-Host "🔙 Rollback:" -ForegroundColor Cyan
Write-Host "  If needed, restore from: $backupRoot" -ForegroundColor White
Write-Host ""

Write-Success "PKI Cleanup completed successfully!"
