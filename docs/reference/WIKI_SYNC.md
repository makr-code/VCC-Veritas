# Wiki Synchronization

## Übersicht

Das `sync-wiki.ps1` Skript synchronisiert die Dokumentation aus dem `docs/` Verzeichnis mit dem GitHub Wiki.

## Voraussetzungen

1. Git muss installiert und im PATH sein
2. Das Wiki muss auf GitHub initialisiert sein (mindestens eine Seite erstellen)
3. Du must Push-Rechte auf das Wiki haben

## Verwendung

### Dry-Run (Testmodus)

Zeigt, was synchronisiert würde, ohne tatsächlich zu pushen:

```powershell
.\sync-wiki.ps1 -DryRun
```

### Wiki synchronisieren

Synchronisiert und pusht Änderungen zum GitHub Wiki:

```powershell
.\sync-wiki.ps1
```

## Was wird synchronisiert?

Das Skript kopiert folgende Dokumentationsdateien:

- **Backend**: ENV_VARS, Agent-Guides, Evaluation Framework
- **Frontend**: UI Modules, Visual Query Builder
- **Testing**: Testing Guide, Scientific Pipeline Tests
- **Scripts**: Backend Management, Service Management
- **Configuration**: Hybrid Config, Helm Deployment
- **Tools**: PGBouncer Setup
- **Reference**: Documentation Overview, Consolidation Plan
- **Integration**: ThemisDB AQL Prompt Engineering

## Wiki-Struktur

Das Skript erstellt automatisch:

- `Home.md` - Hauptseite (aus docs/README.md)
- `_Sidebar.md` - Navigation im Wiki
- `Archive.md` - Verweis auf historische Dokumentation
- Alle konsolidierten Dokumentationsseiten mit Wiki-freundlichen Namen

## Automatisierung

Um das Wiki regelmäßig zu synchronisieren, kannst du:

1. **Manuell nach größeren Änderungen**: `.\sync-wiki.ps1`
2. **GitHub Action** (empfohlen): Erstelle `.github/workflows/sync-wiki.yml`
3. **Pre-Commit Hook**: Synchronisiere vor jedem Commit

### GitHub Action Beispiel

```yaml
name: Sync Wiki
on:
  push:
    branches: [main]
    paths:
      - 'docs/**'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Sync Wiki
        run: |
          chmod +x sync-wiki.ps1
          pwsh ./sync-wiki.ps1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Troubleshooting

### "Wiki repository not found"

Initialisiere das Wiki auf GitHub:
1. Gehe zu https://github.com/makr-code/VCC-Veritas/wiki
2. Erstelle die erste Seite
3. Führe das Skript erneut aus

### "Failed to push"

Überprüfe deine Git-Credentials:
```powershell
git config --global user.name
git config --global user.email
```

### Änderungen werden nicht angezeigt

Das Wiki wird geclont in `.wiki/`. Lösche diesen Ordner und führe das Skript erneut aus:
```powershell
Remove-Item -Recurse -Force .wiki
.\sync-wiki.ps1
```

## Hinweise

- Das Wiki wird in `.wiki/` geclont (ist in `.gitignore`)
- Relative Links in Markdown-Dateien werden automatisch für das Wiki angepasst
- Das Skript fügt automatisch einen Footer mit Sync-Timestamp hinzu
- Archive-Dateien werden nicht einzeln ins Wiki kopiert, sondern nur verlinkt

## Wiki-Link-Struktur

Im Wiki werden Markdown-Dateien ohne `.md`-Endung verlinkt:

- `[Link](../path/file.md)` → `[Link](file)`
- `[Link](./file.md)` → `[Link](file)`
- `[Link](file.md)` → `[Link](file)`

Dies ermöglicht eine saubere Wiki-Navigation.
