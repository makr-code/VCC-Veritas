<<<<<<< Updated upstream
﻿# Dokumentations- und Wiki-RichtlinienDiese Richtlinien helfen, die VERITAS-Dokumentation konsistent zu pflegen und die Inhalte ins GitHub Wiki zu ver├Âffentlichen.## Struktur und Ziele- Prim├ñrquelle: `docs/` im Repo. Hier liegen alle Markdown-Dateien.- Website-Vorschau: Docsify mit `docs/index.html`, Navigation ├╝ber `_sidebar.md` und `_navbar.md`.- GitHub Wiki: Spiegelung ausgew├ñhlter/aller Markdown-Dateien. Startseite ist `Home.md`, Navigation ├╝ber `_Sidebar.md`.## Lokale Vorschau (Docsify)```powershellnpx docsify serve docs# Browser: http://localhost:3000```## Publizieren & Sidebar-Aktualisierung (GitHub Wiki)Das kombinierte Skript aktualisiert zuerst optional die Sidebars und publiziert anschlie├ƒend.1. GitHub Token mit Scope `repo` setzen:   ```powershell   $env:GITHUB_TOKEN = "<gh_personal_access_token>"   ```2. Publizieren (mit Sidebar-Generierung):   ```powershell   powershell -ExecutionPolicy Bypass -File .\scripts\publish-wiki.ps1   ```3. Nur Publish (ohne Sidebar-Neugenerierung):   ```powershell   powershell -ExecutionPolicy Bypass -File .\scripts\publish-wiki.ps1 -SkipSidebarGeneration   ```### Mapping-Regeln- `docs/README.md` ÔåÆ `Home.md` (Wiki-Startseite)- `docs/_Sidebar.md` (falls vorhanden) ÔåÆ `_Sidebar.md` (bevorzugt)- Fallback: `docs/_sidebar.md` ÔåÆ `_Sidebar.md`- Es werden `*.md` sowie Ordner `assets,img,images,media` kopiert (falls vorhanden).### Link-Konventionen- Docsify (im Repo): Normale Links wie `[Titel](DATEI.md)` funktionieren.- GitHub Wiki: In `_Sidebar.md` am besten Wiki-Links nutzen: `[[SEITENNAME]]` (ohne `.md`).- Inhaltliche Seiten k├Ânnen weiterhin regul├ñre Markdown-Links enthalten; GitHub Wiki rendert `.md` Links nicht immer zuverl├ñssig. Empfehlung: Navigation im Wiki vor allem ├╝ber `_Sidebar.md` sicherstellen.## Benennung & Organisation- Bestehende Dateinamen beibehalten (meist UPPERCASE mit `_`).- Optional mittelfristig Kapitel-Indexseiten anlegen (z. B. `architecture/README.md`) und in `_sidebar.md` verlinken.- Gro├ƒe Umbauten bitte ├╝ber PR mit kurzer Begr├╝ndung (Aufr├ñumen, Kapitelbildung, Archivierung).## Qualit├ñtssicherung- Pr├╝fe nach gr├Â├ƒeren ├änderungen: `README.md` (Inhalt & Links), `_sidebar.md` (Docsify), `_Sidebar.md` (Wiki).- Nach Wiki-Publish kurz validieren: Home, 3ÔÇô5 Hauptseiten, Navigation.## N├ñchste Verbesserungen (optional)- Skript um Asset-/Bildkopie erweitern (z. B. `docs/assets/` ÔåÆ `assets/`).- Automatisches Link-Rewriting f├╝r Wiki (`.md` ÔåÆ Wiki-Links) per Preprocessing.- CI-Job f├╝r automatisches Publishen (z. B. manuell triggerbar via Workflow-Dispatch).
=======
# Dokumentations- und Wiki-Richtlinien

Diese Richtlinien helfen, die VERITAS-Dokumentation konsistent zu pflegen und die Inhalte ins GitHub Wiki zu veröffentlichen.

## Struktur und Ziele

- Primärquelle: `docs/` im Repo. Hier liegen alle Markdown-Dateien.
- Website-Vorschau: Docsify mit `docs/index.html`, Navigation über `_sidebar.md` und `_navbar.md`.
- GitHub Wiki: Spiegelung ausgewählter/aller Markdown-Dateien. Startseite ist `Home.md`, Navigation über `_Sidebar.md`.

## Lokale Vorschau (Docsify)

```powershell
npx docsify serve docs
# Browser: http://localhost:3000
```

## Publizieren & Sidebar-Aktualisierung (GitHub Wiki)

Das kombinierte Skript aktualisiert zuerst optional die Sidebars und publiziert anschließend.

1. GitHub Token mit Scope `repo` setzen:
   ```powershell
   $env:GITHUB_TOKEN = "<gh_personal_access_token>"
   ```
2. Publizieren (mit Sidebar-Generierung):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\publish-wiki.ps1
   ```
3. Nur Publish (ohne Sidebar-Neugenerierung):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\publish-wiki.ps1 -SkipSidebarGeneration
   ```

### Mapping-Regeln

- `docs/README.md` → `Home.md` (Wiki-Startseite)
- `docs/_Sidebar.md` (falls vorhanden) → `_Sidebar.md` (bevorzugt)
- Fallback: `docs/_sidebar.md` → `_Sidebar.md`
- Es werden `*.md` sowie Ordner `assets,img,images,media` kopiert (falls vorhanden).

### Link-Konventionen

- Docsify (im Repo): Normale Links wie `[Titel](DATEI.md)` funktionieren.
- GitHub Wiki: In `_Sidebar.md` am besten Wiki-Links nutzen: `[[SEITENNAME]]` (ohne `.md`).
- Inhaltliche Seiten können weiterhin reguläre Markdown-Links enthalten; GitHub Wiki rendert `.md` Links nicht immer zuverlässig. Empfehlung: Navigation im Wiki vor allem über `_Sidebar.md` sicherstellen.

## Benennung & Organisation

- Bestehende Dateinamen beibehalten (meist UPPERCASE mit `_`).
- Optional mittelfristig Kapitel-Indexseiten anlegen (z. B. `architecture/README.md`) und in `_sidebar.md` verlinken.
- Große Umbauten bitte über PR mit kurzer Begründung (Aufräumen, Kapitelbildung, Archivierung).

## Qualitätssicherung

- Prüfe nach größeren Änderungen: `README.md` (Inhalt & Links), `_sidebar.md` (Docsify), `_Sidebar.md` (Wiki).
- Nach Wiki-Publish kurz validieren: Home, 3–5 Hauptseiten, Navigation.

## Nächste Verbesserungen (optional)

- Skript um Asset-/Bildkopie erweitern (z. B. `docs/assets/` → `assets/`).
- Automatisches Link-Rewriting für Wiki (`.md` → Wiki-Links) per Preprocessing.
- CI-Job für automatisches Publishen (z. B. manuell triggerbar via Workflow-Dispatch).
>>>>>>> Stashed changes
