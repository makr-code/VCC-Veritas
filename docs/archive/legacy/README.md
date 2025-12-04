# Dokumentations-Archiv

**Erstellt:** 4. Dezember 2025

Dieses Verzeichnis enthält archivierte Dokumentation, die nicht mehr aktiv gepflegt wird.

---

## 📂 Verzeichnisse

### 📋 `phase-reports/`
Alte Phase-Reports und Completion-Berichte (Phase 1-5, Phase A-A5)

- **Zeitraum:** Phase 1 (Aug 2024) bis Phase 5 (Jul 2025)
- **Inhalt:** Implementierungs-Reports, Completion-Berichte, Roadmaps pro Phase
- **Grund:** Historische Information, aktuelle Roadmap ist in `../reference/ROADMAP.md`
- **Wann archiviert:** Dezember 2025

### 📊 `deployment-logs/`
Deployment-Logs und Monitoring-Reports

- **Inhalt:** Production Deployments >3 Monate alt, Monitoring-Berichte
- **Grund:** Archiviert für Audit-Trail und Referenz
- **Wann archiviert:** Dezember 2025

### 🔄 `session-summaries/`
Session-Summaries, Test-Reports und Completion-Meldungen

- **Inhalt:** Einzelne Entwicklungs-Sessions, Test-Reports, Validation-Berichte
- **Grund:** Historische Information für spezifische Sessions
- **Wann archiviert:** Dezember 2025

### 💡 `concepts/`
Alte Konzepte und Designvorschläge

- **Inhalt:** KONZEPT_*.md Dateien, alte VQB-Designs, Legacy-Architektur-Vorschläge
- **Grund:** Teilweise implementiert, teilweise verworfen
- **Status:** Für zusätzlichen Kontext siehe aktuelle Guides in `../architecture/`
- **Wann archiviert:** Dezember 2025

### 🚫 `obsolete-guides/`
Veraltete API-Versionen, alte Integration-Guides

- **Inhalt:** API v1/v2 Dokumentation, alte VERITAS-Versionen (v1.x, v2.x)
- **Grund:** Code wurde refaktoriert oder deprecated
- **Aktuell:** Siehe `../api/v3/` für aktuelle API-Dokumentation
- **Wann archiviert:** Dezember 2025

### 📦 `old-versions/`
Ältere Releases und Versionsinformation

- **Inhalt:** Release Notes für v1.x, v2.x, v3.x
- **Status:** Nur für Referenz
- **Aktuell:** Siehe `../reference/CHANGELOG.md` für aktuelle Version
- **Wann archiviert:** Dezember 2025

---

## 🔍 Wie findet man Informationen?

### Aktuelle Dokumentation
→ Siehe `../README.md` und Hauptkategorien in `../`

### Historische Informationen
→ Suche im entsprechenden Archiv-Verzeichnis oben

### Aktuelle Roadmap
→ `../reference/ROADMAP.md`

### Aktuelle API-Dokumentation
→ `../api/` und `../api/v3/`

### Performance-Metriken & Deployments
→ `../deployment/MONITORING.md` für aktuelle Daten

---

## 📋 Archiv-Policy

### Wann werden Dateien archiviert?

Dateien werden archiviert wenn:
1. Sie älter als 3 Monate sind UND
2. Keine aktiven Referenzen mehr existieren UND
3. Ein neueres Äquivalent vorhanden ist

### Kann ich Dateien aus dem Archiv verwenden?

**Ja!** Archivierte Dateien sind noch lesbar und nützlich für:
- Historischen Kontext verstehen
- Legacy-Code nachvollziehen
- Performance-Vergleiche
- Frühere Designs verstehen

### Wie kann ich etwas aus dem Archiv wiederherstellen?

Kontaktiere den Documentation Lead oder öffne einen GitHub Issue.

---

## 📚 Wichtige Dokumente im Archiv

### Phase-Reports
```
phase-reports/
├── PHASE1_DEPLOYMENT_SUCCESS.md      (Aug 2024)
├── PHASE2_DEPLOYMENT_SUCCESS.md      (Sep 2024)
├── PHASE3_*.md                       (Oct 2024)
├── PHASE4_*.md                       (May 2025)
├── PHASE5_*.md                       (Jul 2025)
└── PHASE_A*.md                       (Jun-Jul 2025)
```

### Session-Summaries
```
session-summaries/
├── SESSION_SUMMARY_*.md
├── REFACTORING_COMPLETE.md
├── RELEASE_v3.19.0_COMPLETE.md
└── [Individuelle Sessions]
```

### Veraltete Konzepte
```
concepts/
├── KONZEPT_VISUAL_QUERY_BUILDER.md
├── KONZEPT_VQB_*.md
├── CONCEPT_NEO4J_GRAPH.md
└── [Andere Konzepte]
```

---

## 🔗 Referenzen

- **Cleanup-Plan:** `../DOCUMENTATION_CLEANUP_PLAN.md`
- **Implementation Guide:** `../DOCUMENTATION_CLEANUP_IMPLEMENTATION.md`
- **Aktuelle Docs:** `../README.md`

---

## 📞 Kontakt

Fragen zur Archivierung oder Anfragen zum Zugriff auf archivierte Dateien?

→ Siehe `../development/CONTRIBUTING.md` für Kontakt-Informationen

---

**Status:** ✅ Archive aktiv
**Letzte Aktualisierung:** 4. Dezember 2025
**Maintenance:** Monatliche Review nach diesem Datum
