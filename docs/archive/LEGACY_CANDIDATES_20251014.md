# Kandidaten für Archivierung — 14. Oktober 2025

Datum: 14.10.2025

Kontext
-------
Diese Liste fasst Dateien und Bereiche im `veritas`-Teil des Repositories zusammen, die als "legacy"/"deprecated"/"obsolete" eingestuft wurden oder deutlich als Archiv-/TODO-Material markiert sind. PKI-bezogene Inhalte liegen außerhalb des Auftrags (siehe Nutzeranweisung) und wurden daher hier nicht verschoben — sie werden als Hinweise gelistet, aber nicht automatisiert archiviert.

Auswahlkriterien
-----------------
- Dateiname enthält typische Marker: `legacy`, `deprecated`, `DEPRECATED`, `TODO_`, `*_OLD`, `*_bak`.
- Dokumente mit klarer Kennzeichnung "Deprecated", "Legacy" oder Hinweise auf Migration/Archiv.
- Codedateien mit `_DEPRECATED` oder `DEPRECATED` im Header.
- Skripte, die Legacy-Files verschieben oder referenzieren (mögliche Pflegepunkte).

Kurzstatistik (aus Suche)
-------------------------
- Gesamt-Treffer (pattern-suche): viele, fokussiert auf `docs/`, `uds3/` und einige `shared/`-Module.
- PKI-spezifische Legacy-Audit-Dateien existieren, wurden aber nicht verändert (siehe `C:\VCC\PKI`).

Kandidaten (veritas-scope)
--------------------------
Hinweis: Pfade relativ zum Repo-Root `c:\VCC\veritas`.

1) Dokumentation / Docs
  - `docs/archive/legacy/TODO_PKI_INTEGRATION_LEGACY.md` — bereits archiviert. (Informativ)
  - `docs/README.md` — Index zeigt deprecated/legacy-Sektionen; prüfen, ob weitere Einträge ergänzt werden müssen.
  - `docs/archive/README.md` — Archiv-Index; ggf. Kategorien anpassen (legacy / old-implementations / deprecated-features).
  - `docs/OFFENE_IMPLEMENTIERUNGEN_REPORT.md` — enthält Erwähnungen zu PKI-Tests (`test_pki_integration.py`); prüfen, ob Verweise aktualisiert werden müssen.
  - `docs/archive/old-implementations/PKI_MIGRATION_COMPLETE.md` — Archivdokument mit PKI-Referenzen (informativ).
  - `docs/archive/old-implementations/PKI_INTEGRATION.md` — verweist auf `docs/PKI_INTEGRATION.md` (ggf. konsolidieren).
  - Diverse `docs/TODO_*` in der Repo-Top-Ebene (z. B. `TODO_REMOVE_MOCKS_AND_SIMULATIONS.md`, `TODO_PKI_INTEGRATION.md` Verweise) — Kandidaten für Archivierung oder Konsolidierung.

2) UDS3-Bereich (große Legacy-Gruppe)
  - `uds3/uds3_security_DEPRECATED.py` und `uds3_quality_DEPRECATED.py` (inkl. `.bak`-Backups): bereits als deprecated markiert — verschieben nach `uds3/deprecated/` oder `docs/archive/` je nach Policy.
  - `uds3/UDS3_LEGACY_ANALYSIS.md`, `docs/TODO_*` unter `uds3/docs/` — Migrationsdokumente und ToDos, gut als Archivkategorie geeignet.
  - `uds3/*_ORIGINAL.py.bak` und `*_DEPRECATED.py` — Binaries/Backups prüfen und ggf. in `uds3/archive/` verschieben.

3) Code mit Legacy-Aliases / Fallbacks
  - `shared/universal_json_payload.py` — enthält Legacy-Aliase; falls Kompatibilität noch benötigt, belassen, sonst in `shared/deprecated/` verschieben oder kommentieren.
  - `shared/utilities/veritas_production_manager.py` — importiert `legacy_scrapers.scraper_bverwg_adapter` (prüfen, ob der Adapter noch benötigt wird).

4) Scripts / Automatisierungspunkte
  - `scripts/pki_cleanup.ps1` — Script enthält Move-Operationen für `TODO_PKI_INTEGRATION.md` → `docs\legacy\TODO_PKI_INTEGRATION_LEGACY.md`; das Script sollte aktualisiert, dokumentiert oder in eine `maintenance/` Sammlung verschoben werden.

5) Sonstige (low-priority / informational)
  - `reports/PHASE_*` und `reports/*MIGRATION*` — haben Hinweise auf preserved legacy code; diese können bleiben, sind aber als historisch gekennzeichnet.

Empfehlungen & Priorisierung
----------------------------
1) Kurzfristig (niedriger Aufwand)
  - Aktualisieren: `scripts/pki_cleanup.ps1` — Pfad-Referenzen auf die neue Archivstruktur prüfen/aktualisieren (nur Docs, kein PKI-Touch).
  - Link-Check der `docs/`-Tree (Markdown-Link-Checker) — findet relative Link-Broken nach weiteren Verschiebungen.

2) Mittelfristig (entscheidungsbedarf)
  - Konsolidieren: `uds3/` deprecated/backup-Dateien in `uds3/deprecated/` verschieben; Update der `uds3/README.md` mit Migration-Shim und Hinweis auf Backups.
  - Review: `shared/universal_json_payload.py` und `shared/utilities/veritas_production_manager.py` auf aktive Abhängigkeiten prüfen; falls nicht mehr gebraucht, in `shared/deprecated/` verschieben.

3) Langfristig (ggf. Team-Entscheidung)
  - PKI-Aufräumaktion: ist außerhalb dieses Tasks, aber verzeichnet in `C:\VVC\PKI\LEGACY_FILES_AUDIT.md` — erfordert Eigentümer-Freigabe.

Vorgehensvorschlag für die nächsten Schritte
-------------------------------------------
1. Review-Meeting: kurze Abstimmung (15–30min) mit Maintainer-Team, um Prioritäten festzulegen.
2. Testlauf: Führe einen Markdown-Link-Checker über `docs/` aus (optional kann ich das automatisiert ausführen).
3. Kleinere Moves: Aktualisiere Skripte (`scripts/pki_cleanup.ps1`) und verschiebe wenige, klar-entkoppelte Dateien (z. B. backups, `.bak`) nach `*_deprecated/` oder `archive/` — immer mit Git-Commit.

Anmerkung zu PKI
-----------------
PKI-Repository/Audit-Dateien existieren (`C:\VVC\PKI\LEGACY_FILES_AUDIT.md`). Diese wurden nicht verändert. Wenn Sie möchten, kann ich eine separate, nicht-destruktive Kandidatenliste für PKI vorbereiten, aber nur nach Ihrer ausdrücklichen Freigabe.

Datei erstellt: `docs/archive/LEGACY_CANDIDATES_20251014.md`
