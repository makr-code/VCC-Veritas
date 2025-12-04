#!/usr/bin/env pwsh
# VERITAS Wiki Sync Tool
# Synchronizes docs/ directory to GitHub Wiki

param([switch]$DryRun)

$ErrorActionPreference = "Stop"

# Config
$REPO = "makr-code/VCC-Veritas"
$WIKI_URL = "https://github.com/$REPO.wiki.git"
$DOCS = "$PSScriptRoot\docs"
$WIKI = "$PSScriptRoot\.wiki"

Write-Host "`n=== VERITAS Wiki Sync ===" -ForegroundColor Cyan

# Check docs exist
if (-not (Test-Path $DOCS)) {
    Write-Host "ERROR: docs/ not found" -ForegroundColor Red
    exit 1
}

# Clone/update wiki
if (Test-Path $WIKI) {
    Write-Host "Updating wiki..." -ForegroundColor Cyan
    cd $WIKI
    git fetch origin
    git reset --hard origin/master
    cd ..
} else {
    Write-Host "Cloning wiki..." -ForegroundColor Cyan
    git clone $WIKI_URL $WIKI
}

# Copy main documentation files
Write-Host "Syncing files..." -ForegroundColor Cyan

$files = @{
    "$DOCS\README.md" = "$WIKI\Home.md"
    "$DOCS\backend\ENV_VARS.md" = "$WIKI\Backend-Environment-Variables.md"
    "$DOCS\backend\agents\AGENT_TEMPLATE_GUIDE.md" = "$WIKI\Agent-Template-Guide.md"
    "$DOCS\backend\agents\INTEGRATION_README.md" = "$WIKI\Agent-Integration.md"
    "$DOCS\backend\evaluation\README.md" = "$WIKI\Evaluation-Framework.md"
    "$DOCS\frontend\ui\README_UI_MODULES.md" = "$WIKI\Frontend-UI-Modules.md"
    "$DOCS\frontend\vqb\README.md" = "$WIKI\Visual-Query-Builder.md"
    "$DOCS\testing\TESTING_README.md" = "$WIKI\Testing-Guide.md"
    "$DOCS\testing\SCIENTIFIC_PIPELINE_TESTS.md" = "$WIKI\Scientific-Pipeline-Tests.md"
    "$DOCS\scripts\QUICK_REFERENCE.md" = "$WIKI\Scripts-Quick-Reference.md"
    "$DOCS\scripts\README_BACKEND_MANAGEMENT.md" = "$WIKI\Backend-Management-Scripts.md"
    "$DOCS\scripts\README_BACKEND_V4.md" = "$WIKI\Backend-V4-Guide.md"
    "$DOCS\scripts\README_SERVICE_MANAGEMENT.md" = "$WIKI\Service-Management-Scripts.md"
    "$DOCS\config\README_HYBRID_CONFIG.md" = "$WIKI\Hybrid-Configuration.md"
    "$DOCS\deployment\helm\README.md" = "$WIKI\Helm-Deployment.md"
    "$DOCS\tools\pgbouncer\README.md" = "$WIKI\PGBouncer-Setup.md"
    "$DOCS\reference\MARKDOWN_FILES_OVERVIEW.md" = "$WIKI\Documentation-Overview.md"
    "$DOCS\reference\DOCS_CONSOLIDATION_PLAN.md" = "$WIKI\Documentation-Consolidation-Plan.md"
    "$DOCS\integration\themisdb\aql_prompt_engineering.md" = "$WIKI\ThemisDB-AQL-Prompt-Engineering.md"
}

$copied = 0
foreach ($entry in $files.GetEnumerator()) {
    if (Test-Path $entry.Key) {
        Copy-Item -Path $entry.Key -Destination $entry.Value -Force
        Write-Host "  ✓ $(Split-Path $entry.Value -Leaf)" -ForegroundColor Green
        $copied++
    } else {
        Write-Host "  ✗ $(Split-Path $entry.Key -Leaf) not found" -ForegroundColor Yellow
    }
}

# Create sidebar
Write-Host "Creating sidebar..." -ForegroundColor Cyan
$sidebar = @"
# VERITAS Documentation

## 📚 Getting Started
* [Home](Home)
* [Documentation Overview](Documentation-Overview)

## 🔧 Backend
* [Environment Variables](Backend-Environment-Variables)
* [Agent Template Guide](Agent-Template-Guide)
* [Agent Integration](Agent-Integration)
* [Evaluation Framework](Evaluation-Framework)

## 🎨 Frontend
* [UI Modules](Frontend-UI-Modules)
* [Visual Query Builder](Visual-Query-Builder)

## 🧪 Testing
* [Testing Guide](Testing-Guide)
* [Scientific Pipeline Tests](Scientific-Pipeline-Tests)

## 📜 Scripts
* [Quick Reference](Scripts-Quick-Reference)
* [Backend Management](Backend-Management-Scripts)
* [Backend V4 Guide](Backend-V4-Guide)
* [Service Management](Service-Management-Scripts)

## ⚙️ Configuration & Deployment
* [Hybrid Configuration](Hybrid-Configuration)
* [Helm Deployment](Helm-Deployment)
* [PGBouncer Setup](PGBouncer-Setup)

## 🔌 Integration
* [ThemisDB AQL](ThemisDB-AQL-Prompt-Engineering)

## 📖 Reference
* [Consolidation Plan](Documentation-Consolidation-Plan)
* [Archive](Archive)
"@

$sidebarPath = Join-Path $WIKI "_Sidebar.md"
Set-Content $sidebarPath -Value $sidebar -Encoding UTF8

# Create archive page
$archive = @"
# Archive

Historical documentation for reference.

## 📦 Phase Reports
See [archive/phase-reports](https://github.com/$REPO/tree/main/docs/archive/phase-reports)

## 📝 Session Summaries
See [archive/session-summaries](https://github.com/$REPO/tree/main/docs/archive/session-summaries)

## 💡 Concepts
See [archive/concepts](https://github.com/$REPO/tree/main/docs/archive/concepts)

## 📚 Legacy
See [archive/legacy](https://github.com/$REPO/tree/main/docs/archive/legacy)
"@

$archivePath = Join-Path $WIKI "Archive.md"
Set-Content $archivePath -Value $archive -Encoding UTF8

# Commit and push
Write-Host "Committing changes..." -ForegroundColor Cyan
cd $WIKI
git add -A

$hasChanges = git status --porcelain
if (-not $hasChanges) {
    Write-Host "No changes to commit" -ForegroundColor Yellow
    cd ..
    exit 0
}

$commitMsg = "docs: Sync from main repo ($copied files)"
git commit -m $commitMsg

if ($DryRun) {
    Write-Host ""
    Write-Host "DRY RUN - Not pushing to GitHub" -ForegroundColor Yellow
    Write-Host "Run without -DryRun to push changes" -ForegroundColor Yellow
} else {
    Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
    git push origin master
    Write-Host ""
    Write-Host "✅ Wiki synced successfully!" -ForegroundColor Green
    $wikiUrl = "https://github.com/$REPO/wiki"
    Write-Host "View at: $wikiUrl" -ForegroundColor Cyan
}

cd ..
