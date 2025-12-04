# Phase 3 Execution Plan: Aggressive Documentation Cleanup

**Status:** Phase 3a Complete - Ready für Cleanup
**Daten-Punkte:** 406 Markdown-Dateien in docs/ (massiver Bloat!)
**Strategie:** Archiviere 350+ Dateien, behalte nur essenzielle

---

## 🚨 **Problem: 406 Markdown-Dateien in docs/**

Das Problem ist größer als erwartet:
- ✅ Neue Struktur erstellt (8 Kategorien)
- ❌ **ABER:** 406 alte Dateien liegen im Root von docs/
- ❌ Mit neuer Struktur = Chaos

### Lösung: Aggressive Archivierung

**Strategie:**
1. Behalte nur **Top 50-100 essenzielle Dateien** im Root oder neue Struktur
2. Archiviere **350+ alte Dateien** in `.archive/`
3. Nutze cleanup-docs.ps1 für Automation

---

## 📊 Dateien-Kategorisierung (Nach Name-Patterns)

### ✅ **BEHALTEN** (Essenzielle Dokumentation)

#### Navigation & Index (10 Dateien)
- `README.md`
- `_sidebar.md`
- `_navbar.md`
- `QUICK_START*.md` (2-3 Varianten, beste behalten)
- `PROJECT_STRUCTURE.md`
- `VERITAS_System_Overview.md` → zu `architecture/OVERVIEW.md`

#### Kerndokumentation (20 Dateien)
- `VERITAS_API_BACKEND_DOCUMENTATION.md` → zu `api/`
- `BACKEND_ARCHITECTURE_ANALYSIS.md` → zu `architecture/`
- `DEPLOYMENT_GUIDE.md` → zu `deployment/`
- `TESTING*.md` → zu `development/`
- `CONTRIBUTING.md` → behalten
- `AUTHENTICATION*.md` → zu `api/`
- `ERROR_HANDLING_GUIDE.md` → zu `development/`
- `ORCHESTRATOR*.md` → zu `architecture/`

#### Integration (15 Dateien)
- `UDS3_*.md` (nur neueste) → zu `integration/UDS3_INTEGRATION.md`
- `THEMIS_*.md` (nur neueste) → zu `integration/THEMIS_INTEGRATION.md`
- `WEBSOCKET*.md` → zu `integration/WEBSOCKET.md`

#### Reference (10 Dateien)
- `ROADMAP.md` → zu `reference/`
- `QUICK_REFERENCE.md` → zu `reference/`
- `CHANGELOG.md` + `RELEASE_NOTES*.md` (newest) → zu `reference/`

**Total: ~70 essenzielle Dateien**

### 🗑️ **ARCHIVIEREN** (336 Dateien)

#### Phase-Reports & Session-Summaries (80+ Dateien)
```
PHASE*.md
PHASE_*.md
PHASE_A*.md
SESSION_*.md
*_COMPLETE*.md
*_FINAL*.md
*_SUCCESS*.md
```
→ Ziel: `.archive/phase-reports/`

#### Veraltete APIs & Versionen (60+ Dateien)
```
API_V*.md
V*.md (Version-Dateien)
VERITAS_API_*.md (ältere Varianten)
```
→ Ziel: `.archive/old-versions/`

#### Konzepte & Designs (40+ Dateien)
```
KONZEPT_*.md
*_DESIGN*.md
*_PROPOSAL.md
*_PLANNING.md
```
→ Ziel: `.archive/concepts/`

#### Tests & Evaluierung (40+ Dateien)
```
*TEST*.md
*_TESTING*.md
*_EVALUATION*.md
*_REPORT*.md
```
→ Ziel: `.archive/session-summaries/`

#### Monitoring & Logs (30+ Dateien)
```
MONITORING*.md
*_LOG*.md
DEPLOYMENT_LOG*.md
*_AUDIT*.md
```
→ Ziel: `.archive/deployment-logs/`

#### Veraltete Features & Legacy (80+ Dateien)
```
LEGACY*.md
DEPRECATED*.md
*_OLD*.md
*_OBSOLETE*.md
[In archive/ subfolder: old-implementations/, deprecated-features/, etc.]
```
→ Ziel: `.archive/obsolete-guides/`

#### Duplikate & Redundantes (6+ Dateien)
```
README.md (mehrfach)
API_REFERENCE.md (mehrfach)
QUICK_START.md (mehrfach)
```
→ Ziel: Nur beste Version behalten, andere archivieren

---

## 🔧 Automatisiertes Cleanup Script

Erstelle `scripts/phase3-aggressive-cleanup.ps1`:

```powershell
# Phase 3: Aggressive Cleanup für 406 Dateien

param(
    [switch]$DryRun = $true,
    [switch]$Execute = $false
)

$archivePatterns = @{
    'phase-reports' = @(
        'PHASE*.md',
        'SESSION*.md',
        '*_COMPLETE*.md',
        '*_FINAL*.md'
    )
    'old-versions' = @(
        'API_V*.md',
        'V[0-9]*.md',
        'RELEASE_*.md'
    )
    'concepts' = @(
        'KONZEPT*.md',
        '*_DESIGN*.md',
        '*_PROPOSAL*.md'
    )
    'deployment-logs' = @(
        'MONITORING*.md',
        'DEPLOYMENT_LOG*.md',
        '*_AUDIT*.md'
    )
    'session-summaries' = @(
        '*TEST*.md',
        '*_EVALUATION*.md',
        '*_REPORT*.md'
    )
}

# Implementierung würde hier folgen...
```

---

## 📋 Cleanup Execution Plan

### Step 1: Dry-Run (1 Stunde)
```powershell
# Nur anzeigen, nicht ändern
./scripts/cleanup-docs.ps1 -Mode analyze
```

**Output:**
- Zeige Archivierungs-Kandidaten
- Zeige Duplikate
- Zeige fehlerhafte Links

### Step 2: Backup erstellen (1 Stunde)
```bash
git tag backup-before-phase3-$(date +%Y%m%d_%H%M%S)
git push origin --tags
```

### Step 3: Automated Archiving (2-3 Stunden)
```powershell
# Echte Archivierung mit Automation
./scripts/phase3-aggressive-cleanup.ps1 -Execute

# Oder manuell in Batches:
Move-Item docs/PHASE*.md .archive/phase-reports/
Move-Item docs/API_V*.md .archive/old-versions/
# usw.
```

### Step 4: Verify & Commit (1 Stunde)
```bash
# Prüfe wie viele Dateien noch im docs/ Root
ls docs/*.md | wc -l  # sollte < 100 sein

# Commit
git add docs/ .archive/
git commit -m "docs: phase 3 - aggressive cleanup of 350+ old files

- Archiviert 350+ veraltete Dateien in .archive/
- Behalte nur 70 essenzielle Dateien
- Neue Struktur ist nun sauber
- Ready für Phase 3b: Content Migration"
```

### Step 5: Link Validation (2-3 Stunden)
```powershell
./scripts/cleanup-docs.ps1 -Mode validate

# Behebe Broken Links
# (werden automatisch geloggt)
```

---

## 📊 Expected Results nach Phase 3

| Metrik | Vorher | Nachher | Reduktion |
|--------|--------|---------|-----------|
| **Dateien in docs/** | 406 | ~80 | -80% |
| **Archivierte Dateien** | 0 | 326 | +100% |
| **Root-Level Chaos** | Hoch | Niedrig | ✅ |
| **Navigation** | Schlecht | Gut | ✅ |

---

## ⚡ Quick Wins (Diese Woche)

1. **2 Stunden:** Analyze durchführen → `analysis.txt`
2. **2 Stunden:** Kategorisierung durchführen
3. **3 Stunden:** Archivierung durchführen
4. **2 Stunden:** Links validieren
5. **1 Stunde:** Commit & Test

**Total: 10 Stunden → 2 Tage intensive Arbeit**

---

## 🎯 Danach (Phase 3b): Content Migration

Nachdem 350+ Dateien archiviert sind, migriere essenzielle Dateien:

```
docs/getting-started/
├── QUICK_START.md
├── INSTALLATION.md
├── FIRST_QUERY.md
└── TROUBLESHOOTING.md

docs/architecture/
├── OVERVIEW.md (from VERITAS_System_Overview.md)
├── BACKEND_ARCHITECTURE.md (from BACKEND_ARCHITECTURE_ANALYSIS.md)
├── ORCHESTRATOR.md
└── ...

docs/api/
├── API_REFERENCE.md (from VERITAS_API_BACKEND_DOCUMENTATION.md)
├── ENDPOINTS.md
└── AUTHENTICATION.md

docs/integration/
├── UDS3_INTEGRATION.md
├── THEMIS_INTEGRATION.md
├── WEBSOCKET.md
└── ...

docs/deployment/
├── DEPLOYMENT_GUIDE.md
├── DOCKER.md
├── KUBERNETES.md
└── ...

docs/development/
├── DEVELOPMENT.md
├── TESTING.md
├── CONTRIBUTING.md
└── ...

docs/components/
├── ORCHESTRATOR.md
├── RAG_SERVICE.md
├── RERANKING.md
└── ...

docs/reference/
├── ROADMAP.md
├── QUICK_REFERENCE.md
├── CHANGELOG.md
└── GLOSSAR.md
```

---

## 🚨 Wichtige Hinweise

### Duplikate
- **Problem:** Mehrere Versionen (QUICK_START.md, QUICK_START_V7_REAL.md, QUICK_START_DUAL_PROMPT.md)
- **Lösung:** Nur beste Version behalten, Rest archivieren

### Broken Links nach Archivierung
- **Problem:** Andere Dateien verweisen auf archivierte Docs
- **Lösung:** cleanup-docs.ps1 -Mode validate
- **Behebung:** Links aktualisieren oder zu Archiv-Version linken

### Test nach Archivierung
```bash
# Lokal mit Docsify testen
docsify serve docs/

# Sollte keine 404er zeigen
```

---

## 📞 Decision Points

1. **Behalte alle Phase-Reports?** → Nein, archivieren (historisch, aber nicht relevant)
2. **Behalte API v1/v2?** → Nein, nur aktuelle API (v3) behalten
3. **Behalte alte Konzepte?** → Ja, aber archiviert für Kontext

---

## ✅ Success Criteria Phase 3

- [ ] Alle 406 Dateien kategorisiert
- [ ] 350+ archiviert (in .archive/)
- [ ] 70-80 essenzielle Dateien behalten
- [ ] Keine Broken Links
- [ ] docs/ Navigation funktioniert lokal
- [ ] Team kann navigieren
- [ ] Git Commit erfolgreich

---

**Bereit zur Ausführung?** → Starte mit `analyze` Dry-Run
