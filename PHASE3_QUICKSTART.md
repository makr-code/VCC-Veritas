# Phase 3 Quick Start Guide

**Nächster Schritt:** Dokumentation migrieren & Links validieren  
**Geschätzter Aufwand:** 7-10 Tage  
**Zielgruppe:** Documentation Team, DevOps

---

## 🎯 Phase 3 Ziele

1. **Existierende Docs migrieren** in neue Struktur
2. **Links validieren** und Broken Links beheben
3. **Duplikate löschen** und archivieren
4. **Content migrieren** in entsprechende Kategorien

---

## ✅ Phase 3 Checkliste

### Schritt 1: Existierende Docs bewerten (1 Tag)

```powershell
# Analyse durchführen
./scripts/cleanup-docs.ps1 -Mode analyze | Out-File analysis.log

# Report generieren
Get-Content analysis.log | Select-String "duplicate|old|archive" > cleanup_candidates.txt
```

**Output:** Liste von Dateien für Archivierung/Löschung

### Schritt 2: Wichtige Docs migrieren (3 Tage)

**Migration-Strategie:**

| Quell-Datei | Ziel-Verzeichnis | Aktion |
|-------------|-----------------|--------|
| `QUICK_START_V7_REAL.md` | `getting-started/` | Kopieren + aktualisieren |
| `BACKEND_ARCHITECTURE_ANALYSIS.md` | `architecture/` | Kopieren |
| `VERITAS_API_BACKEND_DOCUMENTATION.md` | `api/` | Konsolidieren |
| `DEPLOYMENT_GUIDE.md` | `deployment/` | Prüfen + aktualisieren |
| `TESTING.md` | `development/` | Kopieren |
| `UDS3_INTEGRATION_GUIDE.md` | `integration/` | Kopieren |
| `HYBRID_SEARCH_RRF_RERANKING_REPORT.md` | `components/` | Konsolidieren |

**Prozess pro Datei:**
```bash
# 1. Kopieren
cp src_file docs/target_dir/

# 2. Aktualisieren (Links, Referenzen)
# 3. Testen (Links validieren)
# 4. Commit
git add docs/target_dir/file.md
git commit -m "docs: migrate file to new structure"
```

### Schritt 3: Duplikate & Veraltetes archivieren (2 Tage)

```powershell
# Dry-Run durchführen
./scripts/cleanup-docs.ps1 -Mode archive -DryRun | Tee-Object archive_preview.log

# Bei Zufriedenheit: echte Archivierung
./scripts/cleanup-docs.ps1 -Mode archive
```

**Kandidaten für Archivierung:**
- `DOCUMENTATION_*.md` (alte Dokumentations-Indizes)
- `PHASE*.md` (alle Phase-Reports)
- `SESSION_SUMMARY.md` (alte Sessions)
- `MONITORING_LOG*.md` (alte Logs)

### Schritt 4: Links validieren (2 Tage)

```powershell
# Alle Links prüfen
./scripts/cleanup-docs.ps1 -Mode validate > link_report.txt

# Broken Links finden
Get-Content link_report.txt | Select-String "BROKEN|ERROR" > broken_links.txt
```

**Broken Links beheben:**
```bash
# 1. Broken Link identifizieren
# 2. Korrekte Target-Datei finden
# 3. Link aktualisieren
# 4. Testen

git add docs/
git commit -m "docs: fix broken links"
```

### Schritt 5: Final Validation (1-2 Tage)

```powershell
# Full validation durchführen
./scripts/cleanup-docs.ps1 -Mode validate

# Lokal testen
cd docs
docsify serve .

# Browser: http://localhost:3000
```

---

## 📋 Dokumentations-Migration Matrix

### Getting Started
```
FROM: QUICK_START_V7_REAL.md, QUICK_START.md, INSTALLATION.md
TO:   getting-started/
      ├── QUICK_START.md (konsolidiert)
      ├── INSTALLATION.md (neu/aktualisiert)
      ├── FIRST_QUERY.md (neu)
      └── TROUBLESHOOTING.md (migration hints)
```

### Architecture
```
FROM: BACKEND_ARCHITECTURE_ANALYSIS.md, 
      VERITAS_System_Overview.md,
      PROCESS_TREE_ARCHITECTURE.md
TO:   architecture/
      ├── OVERVIEW.md (Hub)
      ├── BACKEND_ARCHITECTURE.md (konsolidiert)
      ├── DATA_FLOW.md (neu)
      ├── RAG_PIPELINE.md (PHASE4_RAG_INTEGRATION.md)
      └── AGENTS.md (AGENT_FRAMEWORK_QUICKSTART.md)
```

### API
```
FROM: API_REFERENCE.md,
      VERITAS_API_BACKEND_DOCUMENTATION.md,
      API_V3_*.md (5 Dateien)
TO:   api/
      ├── API_REFERENCE.md (konsolidiert)
      ├── ENDPOINTS.md (neu)
      ├── AUTHENTICATION.md (neu)
      └── v3/OVERVIEW.md (API v3 details)
```

### Integration
```
FROM: UDS3_INTEGRATION_GUIDE.md,
      THEMIS_ADAPTER_QUICKSTART.md,
      WEBSOCKET_QUICKSTART.md
TO:   integration/
      ├── UDS3_INTEGRATION.md (kopieren)
      ├── THEMIS_INTEGRATION.md (kopieren)
      ├── OLLAMA_INTEGRATION.md (neu/hints)
      ├── OFFICE_ADDON.md (neu/hints)
      └── MCP_SERVER.md (neu/hints)
```

### Deployment
```
FROM: DEPLOYMENT_GUIDE.md,
      PRODUCTION_DEPLOYMENT_PLAN.md,
      DOCKER*,
      KUBERNETES.md
TO:   deployment/
      ├── DEPLOYMENT_GUIDE.md (konsolidiert)
      ├── DOCKER.md (aktualisiert)
      ├── KUBERNETES.md (kopieren)
      ├── CONFIGURATION.md (neu)
      ├── MONITORING.md (neu)
      └── TROUBLESHOOTING.md (neu)
```

### Development
```
FROM: TESTING.md,
      DEVELOPMENT.md,
      CONTRIBUTING.md
TO:   development/
      ├── DEVELOPMENT.md (kopieren)
      ├── TESTING_GUIDE.md (neu/hints)
      ├── CONTRIBUTING.md (kopieren)
      ├── CODE_STYLE.md (neu)
      └── DEBUGGING.md (neu)
```

### Components
```
FROM: DATABASE_AGENT_QUICKSTART.md,
      HYBRID_SEARCH_RRF_RERANKING_REPORT.md,
      PHASE5_HYPOTHESIS_GENERATION.md
TO:   components/
      ├── DATABASE_AGENT.md (kopieren)
      ├── RAG_SERVICE.md (neu/hints)
      ├── RERANKING.md (konsolidiert)
      ├── HYPOTHESIS_AGENT.md (PHASE5_*.md)
      └── CHAT_PERSISTENCE.md (TODO_CHAT_PERSISTENCE.md)
```

### Reference
```
FROM: ROADMAP.md,
      CHANGELOG.md,
      README.md (misc)
TO:   reference/
      ├── GLOSSAR.md (neu)
      ├── CHANGELOG.md (kopieren)
      ├── ROADMAP.md (kopieren)
      ├── KNOWN_ISSUES.md (neu)
      └── FAQ.md (neu)
```

---

## 🚨 Wichtige Hinweise

### Link-Konventionen
```markdown
# NACH MIGRATION - Richtige Link-Syntax:

## Interne Links (Docsify):
[Quickstart](getting-started/QUICK_START.md)
[API Referenz](api/API_REFERENCE.md)
[Archive](../.archive/README.md)

## Nicht mehr verwenden:
[[File]]  ← GitBook Syntax (veraltet)
./DOCUMENT.md ← Relative Pfade ohne Kategorie
```

### Kategorisierung
- **Wenn unsicher:** In `reference/` ablegen oder unter Archiv-Überlegung
- **Wenn doppelt:** Konsolidieren, nicht duplizieren
- **Wenn alt:** Archivieren, nicht löschen

### Timing
- Täglich committen (kleinere Änderungen)
- Daily-Standup mit Team (Fortschritt)
- Weekly-Review (Blocker, Fragen)

---

## 🔧 Nützliche Commands

```powershell
# Alle .md Dateien zählen
Get-ChildItem -Path . -Filter "*.md" -Recurse | Measure-Object

# Links in Datei finden
Select-String -Path docs/**/*.md -Pattern '\[.*\]\(.*\)' | Select Line

# Duplicate Dateinamen finden
Get-ChildItem -Path docs -Filter "*.md" -Recurse | Group-Object -Property Name | Where Count -GT 1

# Archive-Ready Dateien (älter als 90 Tage)
Get-ChildItem -Path . -Filter "*.md" -Recurse | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-90)}
```

---

## 📊 Progress Tracking

**Empfohlen:** Daily Update in GitHub Issues oder Slack

```
Phase 3: Dokumentation Migration

Tag 1-2: Analyse & Planning
- [ ] Audit durchführen
- [ ] Migration-Plan erstellen
- [ ] Team kickoff

Tag 3-5: Migration
- [ ] Getting Started migriert
- [ ] Architecture migriert
- [ ] API migriert
- [ ] Integration migriert

Tag 6-7: Archivierung & Cleanup
- [ ] Alte Docs archiviert
- [ ] Duplikate gelöscht
- [ ] Root-Level aufgeräumt

Tag 8-9: Link Validation
- [ ] Alle Links geprüft
- [ ] Broken Links behoben
- [ ] Final Review

Tag 10: Release
- [ ] Production Deploy
- [ ] Team Announcement
```

---

## 🎯 Success Criteria

- ✅ Alle wichtigen Docs migriert
- ✅ Keine Broken Links
- ✅ 0 Duplicate Dateien
- ✅ Navigation funktioniert
- ✅ Alle Kategorien gefüllt
- ✅ Team kann navigieren

---

## 📚 Referenzen

- **[Phase 1-2 Plan](DOCUMENTATION_CLEANUP_PLAN.md)**
- **[Cleanup Script](scripts/cleanup-docs.ps1)**
- **[New Navigation](docs/README.md)**

---

**Bereit zu starten?** → Beginne mit Schritt 1 (Analyse) 🚀

