# VERITAS GitHub Wiki - Export Guide

**Ziel:** Dokumentation ins GitHub Wiki exportieren
**Datum:** 4. Dezember 2025

---

## Wiki-Struktur

### Haupt-Seiten

**1. Home** (`Home.md`)
```markdown
Quelle: docs/CURRENT_STATUS.md
Titel: VERITAS System Status & Übersicht
Beschreibung: Vollständiger System-Status, 20 Agents, 22 Capabilities
```

**2. Agent-System** (`Agent-System.md`)
```markdown
Quelle: docs/architecture/AGENTS.md
Titel: Agent-System (20 Agents, 22 Capabilities)
Beschreibung: Detaillierte Agent-Dokumentation, Framework, Orchestrator
```

**3. Dokumentations-Index** (`Documentation-Index.md`)
```markdown
Quelle: docs/README.md
Titel: Dokumentation & Navigation
Beschreibung: Übersicht aller Dokumentations-Kategorien
```

**4. Schnellstart** (`Quick-Start.md`)
```markdown
Quelle: docs/getting-started/QUICK_START.md
Titel: 30-Minuten Quickstart
Beschreibung: Setup und erste Abfrage
```

**5. API-Referenz** (`API-Reference.md`)
```markdown
Quelle: docs/api/API_REFERENCE.md
Titel: API-Dokumentation
Beschreibung: Alle Endpoints, Authentication, Integration
```

### Archiv-Seiten

**6. Phase 1 Migration** (`archive/Phase-1-Migration.md`)
```markdown
Quelle: docs/archive/phases/PHASE1_MIGRATION_COMPLETE.md
Titel: Phase 1 - Weather Agents Migration
```

**7. Phase 2 Migration** (`archive/Phase-2-Migration.md`)
```markdown
Quelle: docs/archive/phases/PHASE2_MIGRATION_COMPLETE.md
Titel: Phase 2 - Environmental Agents Migration
```

**8. Phase 3 Migration** (`archive/Phase-3-Migration.md`)
```markdown
Quelle: docs/archive/phases/PHASE3_MIGRATION_COMPLETE.md
Titel: Phase 3 - Domain v2.0 Migration (10 Agents)
```

**9. Phase 4 Visualization** (`archive/Phase-4-Visualization.md`)
```markdown
Quelle: docs/archive/phases/PHASE4_COMPLETION_REPORT.md
Titel: Phase 4 - Visualization & Generation Agents
```

---

## Export-Prozess

### Schritt 1: Wiki klonen

```bash
# Wiki-Repository klonen
git clone https://github.com/makr-code/VCC-Veritas.wiki.git

cd VCC-Veritas.wiki
```

### Schritt 2: Dateien kopieren

```bash
# Haupt-Seiten
cp ../docs/CURRENT_STATUS.md Home.md
cp ../docs/architecture/AGENTS.md Agent-System.md
cp ../docs/README.md Documentation-Index.md
cp ../docs/getting-started/QUICK_START.md Quick-Start.md
cp ../docs/api/API_REFERENCE.md API-Reference.md

# Archiv-Verzeichnis erstellen
mkdir -p archive

# Archiv-Seiten
cp ../docs/archive/phases/PHASE1_MIGRATION_COMPLETE.md archive/Phase-1-Migration.md
cp ../docs/archive/phases/PHASE2_MIGRATION_COMPLETE.md archive/Phase-2-Migration.md
cp ../docs/archive/phases/PHASE3_MIGRATION_COMPLETE.md archive/Phase-3-Migration.md
cp ../docs/archive/phases/PHASE4_COMPLETION_REPORT.md archive/Phase-4-Visualization.md
```

### Schritt 3: Links anpassen

Wiki-interne Links anpassen (relativer Pfad → Wiki-Link):

**Beispiel:**
```markdown
# Vorher
[Agent-System](architecture/AGENTS.md)

# Nachher
[Agent-System](Agent-System)
```

**Automatisierte Anpassung (PowerShell):**
```powershell
# In jedem Wiki-File
Get-ChildItem *.md | ForEach-Object {
    $content = Get-Content $_.FullName -Raw

    # Relative Pfade → Wiki-Links
    $content = $content -replace '\(docs/([^\)]+)\.md\)', '($1)'
    $content = $content -replace '\(architecture/([^\)]+)\.md\)', '($1)'
    $content = $content -replace '\(getting-started/([^\)]+)\.md\)', '($1)'
    $content = $content -replace '\(api/([^\)]+)\.md\)', '($1)'

    # Speichern
    Set-Content $_.FullName -Value $content -NoNewline
}
```

### Schritt 4: Commit & Push

```bash
# Status prüfen
git status

# Alle Änderungen hinzufügen
git add .

# Commit
git commit -m "docs: Wiki-Update v3.20.0 - System Status & Agent-Dokumentation

- Home: CURRENT_STATUS.md (20 Agents, 22 Capabilities)
- Agent-System: Vollständige Agent-Dokumentation
- Documentation-Index: README.md
- Quick-Start: 30-Min Setup
- API-Reference: API-Dokumentation
- Archiv: Phase 1-4 Migration Reports

Status: PRODUKTIONSBEREIT"

# Push
git push origin master
```

---

## Wiki-Sidebar

### `_Sidebar.md`

```markdown
# VERITAS Wiki

## Übersicht
- [Home](Home)
- [System Status](Home#system-status-snapshot)

## Getting Started
- [Quickstart](Quick-Start)
- [Installation](Installation)
- [Erste Abfrage](First-Query)

## Architektur
- [Agent-System](Agent-System)
- [Backend-Architektur](Backend-Architecture)
- [RAG-Pipeline](RAG-Pipeline)

## API
- [API-Referenz](API-Reference)
- [Endpoints](Endpoints)
- [Authentication](Authentication)

## Archiv
- [Phase 1 Migration](archive/Phase-1-Migration)
- [Phase 2 Migration](archive/Phase-2-Migration)
- [Phase 3 Migration](archive/Phase-3-Migration)
- [Phase 4 Visualization](archive/Phase-4-Visualization)

## Entwicklung
- [Contributing](Contributing)
- [Testing](Testing)
- [Debugging](Debugging)

---

**Version:** 3.20.0
**Status:** ✅ PRODUKTIONSBEREIT
```

---

## Wiki-Footer

### `_Footer.md`

```markdown
---

**VERITAS** | Version 3.20.0 | © 2025 VCC Team
[GitHub](https://github.com/makr-code/VCC-Veritas) | [Issues](https://github.com/makr-code/VCC-Veritas/issues) | [Releases](https://github.com/makr-code/VCC-Veritas/releases)

**Status:** ✅ PRODUKTIONSBEREIT | 20 Agents | 22 Capabilities
```

---

## Automatisierung (PowerShell-Script)

### `export-to-wiki.ps1`

```powershell
# VERITAS Wiki Export Script
# Exportiert Dokumentation ins GitHub Wiki

param(
    [string]$WikiPath = "..\VCC-Veritas.wiki",
    [string]$DocsPath = ".\docs"
)

Write-Host "VERITAS Wiki Export" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host ""

# Prüfen ob Wiki-Repo existiert
if (-not (Test-Path $WikiPath)) {
    Write-Host "ERROR: Wiki-Repository nicht gefunden: $WikiPath" -ForegroundColor Red
    Write-Host "Bitte zuerst klonen: git clone https://github.com/makr-code/VCC-Veritas.wiki.git" -ForegroundColor Yellow
    exit 1
}

# Haupt-Seiten kopieren
Write-Host "Kopiere Haupt-Seiten..." -ForegroundColor Cyan

Copy-Item "$DocsPath\CURRENT_STATUS.md" "$WikiPath\Home.md" -Force
Copy-Item "$DocsPath\architecture\AGENTS.md" "$WikiPath\Agent-System.md" -Force
Copy-Item "$DocsPath\README.md" "$WikiPath\Documentation-Index.md" -Force
Copy-Item "$DocsPath\getting-started\QUICK_START.md" "$WikiPath\Quick-Start.md" -Force
Copy-Item "$DocsPath\api\API_REFERENCE.md" "$WikiPath\API-Reference.md" -Force

Write-Host "  ✓ 5 Haupt-Seiten kopiert" -ForegroundColor Green

# Archiv-Verzeichnis
if (-not (Test-Path "$WikiPath\archive")) {
    New-Item "$WikiPath\archive" -ItemType Directory | Out-Null
}

Write-Host "Kopiere Archiv-Seiten..." -ForegroundColor Cyan

Copy-Item "$DocsPath\archive\phases\PHASE1_MIGRATION_COMPLETE.md" "$WikiPath\archive\Phase-1-Migration.md" -Force
Copy-Item "$DocsPath\archive\phases\PHASE2_MIGRATION_COMPLETE.md" "$WikiPath\archive\Phase-2-Migration.md" -Force
Copy-Item "$DocsPath\archive\phases\PHASE3_MIGRATION_COMPLETE.md" "$WikiPath\archive\Phase-3-Migration.md" -Force
Copy-Item "$DocsPath\archive\phases\PHASE4_COMPLETION_REPORT.md" "$WikiPath\archive\Phase-4-Visualization.md" -Force

Write-Host "  ✓ 4 Archiv-Seiten kopiert" -ForegroundColor Green

# Links anpassen
Write-Host "Passe Wiki-Links an..." -ForegroundColor Cyan

Get-ChildItem "$WikiPath\*.md" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw

    # Relative Pfade → Wiki-Links
    $content = $content -replace '\(docs/([^\)]+)\.md\)', '($1)'
    $content = $content -replace '\(architecture/([^\)]+)\.md\)', '($1)'
    $content = $content -replace '\(getting-started/([^\)]+)\.md\)', '($1)'
    $content = $content -replace '\(api/([^\)]+)\.md\)', '($1)'
    $content = $content -replace '\(\.\./([^\)]+)\.md\)', '($1)'

    Set-Content $_.FullName -Value $content -NoNewline
}

Write-Host "  ✓ Links angepasst" -ForegroundColor Green

# Sidebar & Footer erstellen
Write-Host "Erstelle Sidebar & Footer..." -ForegroundColor Cyan

@"
# VERITAS Wiki

## Übersicht
- [Home](Home)
- [System Status](Home#system-status-snapshot)

## Getting Started
- [Quickstart](Quick-Start)

## Architektur
- [Agent-System](Agent-System)

## API
- [API-Referenz](API-Reference)

## Archiv
- [Phase 1 Migration](archive/Phase-1-Migration)
- [Phase 2 Migration](archive/Phase-2-Migration)
- [Phase 3 Migration](archive/Phase-3-Migration)
- [Phase 4 Visualization](archive/Phase-4-Visualization)

---

**Version:** 3.20.0
**Status:** ✅ PRODUKTIONSBEREIT
"@ | Set-Content "$WikiPath\_Sidebar.md" -NoNewline

@"
---

**VERITAS** | Version 3.20.0 | © 2025 VCC Team
[GitHub](https://github.com/makr-code/VCC-Veritas) | [Issues](https://github.com/makr-code/VCC-Veritas/issues)

**Status:** ✅ PRODUKTIONSBEREIT | 20 Agents | 22 Capabilities
"@ | Set-Content "$WikiPath\_Footer.md" -NoNewline

Write-Host "  ✓ Sidebar & Footer erstellt" -ForegroundColor Green

Write-Host ""
Write-Host "Export abgeschlossen!" -ForegroundColor Green
Write-Host ""
Write-Host "Nächste Schritte:" -ForegroundColor Yellow
Write-Host "  1. cd $WikiPath" -ForegroundColor White
Write-Host "  2. git add ." -ForegroundColor White
Write-Host "  3. git commit -m 'docs: Wiki-Update v3.20.0'" -ForegroundColor White
Write-Host "  4. git push origin master" -ForegroundColor White
```

**Verwendung:**
```powershell
# Standard (Wiki im Parent-Verzeichnis)
.\export-to-wiki.ps1

# Custom Path
.\export-to-wiki.ps1 -WikiPath "C:\Git\VCC-Veritas.wiki" -DocsPath ".\docs"
```

---

## Checklist

### Vor Export

- [x] Dokumentation vollständig
- [x] CURRENT_STATUS.md erstellt
- [x] AGENTS.md aktualisiert
- [x] Phase-Docs archiviert
- [x] README.md aktualisiert

### Export

- [ ] Wiki-Repository klonen
- [ ] export-to-wiki.ps1 erstellen
- [ ] Script ausführen
- [ ] Links manuell prüfen
- [ ] Sidebar & Footer prüfen

### Nach Export

- [ ] Git commit & push
- [ ] Wiki im Browser prüfen
- [ ] Links testen
- [ ] Navigation prüfen

---

**Erstellt:** 4. Dezember 2025, 14:00 Uhr
**Status:** ✅ Bereit für Export
