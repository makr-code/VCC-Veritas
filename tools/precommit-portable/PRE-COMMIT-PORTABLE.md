PRE-COMMIT PORTABLE TEMPLATE
=============================

Zweck
-----
Dieses Verzeichnis enthält eine transportable Vorlage für `pre-commit`-Hooks,
inkl. einer Beispiel-Config und einem einfachen PowerShell-Setupskript.
Die Vorlage ist so gestaltet, dass sie leicht in andere Python-Projekte
kopiert und dort angepasst werden kann.

Enthaltene Dateien
------------------
- PRE-COMMIT-TEMPLATE.yaml  - die vorgefertigte .pre-commit-config.yaml-Vorlage
- setup-precommit.ps1        - PowerShell-Skript: installiert pre-commit, setzt es
                               up und führt initial alle Hooks aus (empfohlen)

Hinzugefügt / empfohlene Hooks
-------------------------------
Die Vorlage enthält Standard-Hooks wie `black`, `isort`, `flake8`, `mypy` und
`bandit`. Zusätzlich habe ich die folgenden Hooks als Empfehlung ergänzt:

- `ruff`  – eine schnelle All-in-One Linter/Formatter/Auto-fix-Option; kann
  Flake8-Checks ersetzen oder ergänzen, ist deutlich schneller in großen
  Repositories.
- `safety` – führt Sicherheitsprüfungen gegen bekannte Python-Paketlücken aus
  (liefert einen Report über vulnerable dependencies).

Wenn Du ruff statt flake8 einsetzen willst, entferne den flake8-Block oder
scope ihn nur dort, wo Du legacy-Regeln benötigst.

Kurzanleitung: Verwendung in einem anderen Projekt
-------------------------------------------------
1) Kopieren der Vorlage
   Kopiere die Datei `PRE-COMMIT-TEMPLATE.yaml` in das Zielprojekt und
   benenne sie um:

   # PowerShell
   Copy-Item .\tools\precommit-portable\PRE-COMMIT-TEMPLATE.yaml .\.pre-commit-config.yaml

2) Pinne die Hook-Versionen
   Ersetze alle `<rev-placeholder>`-Werte in `.pre-commit-config.yaml` mit
   konkreten Versionstags oder SHAs. Beispiele findest Du auf den jeweiligen
   GitHub-Repositories (z. B. `https://github.com/psf/black`).

   Warum pinnen? Eine feste Version sorgt dafür, dass lokale Entwickler und CI
   die exakt gleichen Hook-Versionen verwenden.

3) Anpassungen (empfohlen)
   - mypy/bandit: Scope diese Hooks auf relevante Ordner (z. B. `backend/` und
     `shared/`) mit dem `files:`-Attribut, um Laufzeit in großen Repos zu
     vermeiden.
   - flake8/black/isort: Passe `args:` an (z. B. `--max-line-length`) oder
     ergänze eine projektweite `pyproject.toml`/`setup.cfg`.
   - Lokale Hooks: Falls nötig, füge einen `repo: local`-Block für projekt-
     spezifische Checks hinzu.

4) Installation (PowerShell)
   Falls Python & pip vorhanden sind, führe im Projekt-Root das Setup-Skript
   aus oder die zwei Befehle manuell:

   # PowerShell
   & 'C:\Program Files\Python313\python.exe' -m pip install --user pre-commit
   & 'C:\Program Files\Python313\python.exe' -m pre_commit install
   & 'C:\Program Files\Python313\python.exe' -m pre_commit run --all-files

   Alternativ (wenn Du das mitgelieferte Skript nutzen willst):

   # PowerShell
   .\tools\precommit-portable\setup-precommit.ps1

5) CI-Integration (Beispiel GitHub Actions)
   Füge einen Job hinzu, der `pre-commit` installiert und `pre-commit run --all-files` ausführt.

   Beispiel (Auszug):

   jobs:
     lint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         - name: Install pre-commit
           run: python -m pip install pre-commit
         - name: Run pre-commit
           run: python -m pre-commit run --all-files

Tipps zur Fehlersuche
---------------------
- Wenn `mypy` oder `bandit` zu viele Ergebnisse liefern, scope die Checks
  auf relevante Unterordner mittels `files:` in `.pre-commit-config.yaml`.
- Nutze projektweite Konfigurationsdateien (`mypy.ini`, `pyproject.toml`,
  `.flake8`) um Hook-Optionen konsistent zu halten.

State-of-the-art Best-Practices
--------------------------------
1) Zentrale Konfiguration in `pyproject.toml`
   - Lege Formatter/Linter-Optionen (black, isort, ruff) in `pyproject.toml`
     ab. So verhindern Devs unterschiedliche lokale Flags.

2) Scope teure Hooks
   - Schränke mypy/semgrep/bandit auf die relevanten Module ein (z. B. `^src/` oder
     `^backend/|^shared/`) mit dem `files:`-Feld. Das reduziert Laufzeit in Monorepos.

3) CI & Caching
   - Nutze einen CI-Job, der `python -m pre-commit run --all-files` ausführt.
   - Aktiviere Actions- oder Runner-Caching für ~/.cache/pre-commit und venvs,
     um Hook-Installationszeit zu reduzieren.

4) Automatische Hook-Updates
   - Planmäßiges `pre-commit autoupdate` (z. B. wöchentlich via cron or GitHub Actions)
     sorgt für Sicherheits- und Bugfix-Updates. Teste updates in einer separaten Branch.

5) Pre-commit.ci
   - Für Open-Source-Repos: erwäge `pre-commit.ci` (kostenfrei für öffentliche Repos).
     Das übernimmt das Hook-Running in der Cloud und liefert PR-Checks.

6) Geheimnisscan & Geheimnisschutz
   - `detect-secrets` hilft, versehentliche Credential-Commits zu verhindern.
   - Zusätzlich empfiehlt sich ein pre-commit-Policy, vertrauliche Keys über Secrets-Scanning
     in CI zu prüfen (z. B. GitHub Advanced Security).

7) Semgrep für Security-Checks
   - Semgrep liefert präzise, regelbasierte Security-Checks (und ist besser
     wartbar als Bandit allein). Verwende semgrep-Regelnets (p/ci) und eigene Regeln
     für organisation-spezifische Policies.

8) Spell-/Style-Checks
   - `codespell` hilft, häufige Tippfehler in Prosa und Code zu finden.
   - Für Markdown/Docs empfiehlt sich zusätzlich ein markdown-linting-Job (z. B.
     remark-lint in CI) falls viele Dokumente gepflegt werden.

9) Commit-Message-Checks
   - Nutze `gitlint` oder commit-msg-Hooks, um Conventional-Commits oder andere
     Commit-Standards zu erzwingen. Das erleichtert Release-Automation.

10) Monorepo-Strategie
    - Für große Repos: verwende pro-Package `pyproject.toml` oder gezielte pre-commit
      Configs per Subdir. Setze teure Hooks nur für geänderte Unterprojekte.

11) Umgang mit False-Positives
    - Vermeide globale `# nosec`-Kommentare. Stattdessen dokumentiere Ausnahmen und
      begründe sie in PR-Descriptions.

Suggested CI snippet (mit cache) — GitHub Actions

```yaml
name: pre-commit
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Cache pre-commit
        uses: actions/cache@v4
        with:
          path: |
            ~/.cache/pre-commit
          key: ${{ runner.os }}-pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}
      - name: Install pre-commit
        run: python -m pip install pre-commit
      - name: Run pre-commit
        run: python -m pre-commit run --all-files
```

Unterstützte Plattformen
------------------------
- Das Setup-Skript ist in PowerShell geschrieben und funktioniert auf
  Windows/PowerShell. Für macOS/Linux kannst Du dieselben `python -m pip ...`
  Befehle manuell verwenden oder ein kurzes Bash-Skript ableiten.

Lizenz & Haftung
-----------------
Dieses Template ist rein informativ. Prüfe Hook-Konfigurationen und Versionen
vor dem Einsatz in produktiven Repositories.
