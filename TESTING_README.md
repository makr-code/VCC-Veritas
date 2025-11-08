# ThemisDB Adapter Test Suite - README

[![Tests](https://github.com/makr-code/VCC-AAT/workflows/ThemisDB%20Adapter%20Test%20Suite/badge.svg)](https://github.com/makr-code/VCC-AAT/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](https://codecov.io)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Umfassende Test-Suite für ThemisDB/UDS3 Adapter mit CI/CD-Integration.

---

## Quick Start

```bash
# Installation
pip install -r requirements.txt -r requirements-dev.txt

# Alle Tests
make test

# Nur Unit Tests
make test-unit

# Mit Coverage
make coverage

# Linting
make lint

# Code formatieren
make format
```

---

## Test-Kategorien

| Kategorie | Command | Dauer | Beschreibung |
|-----------|---------|-------|--------------|
| **Unit** | `make test-unit` | ~30s | Schnelle Mock-basierte Tests |
| **Integration** | `make test-integration` | ~2min | Tests mit Redis/PostgreSQL |
| **API** | `make test-api` | ~1min | REST Endpoint Tests |
| **WebSocket** | `make test-websocket` | ~30s | Real-time Communication Tests |
| **Load** | `make load-test` | ~1min | Performance Tests (Locust) |
| **Alle** | `make test` | ~5min | Komplette Test-Suite |

---

## CI/CD Pipeline

### GitHub Actions

**Workflow:** `.github/workflows/test-suite.yml`

**Jobs:**
1. ✅ Lint & Code Quality
2. ✅ Unit Tests (Python 3.10, 3.11, 3.12)
3. ✅ Integration Tests
4. ✅ API Tests
5. ✅ WebSocket Tests
6. ✅ Security Scan
7. ✅ Test Summary

**Trigger:**
- Push zu `main`, `develop`
- Pull Requests
- Manual Workflow Dispatch

---

## Code Quality

### Tools

- **Black** - Code Formatter
- **isort** - Import Sorter
- **Flake8** - Linting
- **Pylint** - Static Analysis
- **mypy** - Type Checking
- **Bandit** - Security Linter

### Pre-commit Hooks

```bash
# Installation
pre-commit install

# Manuelle Ausführung
pre-commit run --all-files
```

---

## Coverage

**Ziele:**
- Gesamt: > 80%
- Backend Core: > 90%
- Adapters: > 85%

**Report generieren:**
```bash
make coverage
# Öffnet: htmlcov/index.html
```

---

## Load Testing

```bash
# Locust mit Web UI
locust -f tests/load/locustfile.py --host http://localhost:8000

# Headless (CI/CD)
locust -f tests/load/locustfile.py \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 60s \
    --host http://localhost:8000
```

**Targets:**
- Vector Search: 1000+ RPS
- WebSocket: 100+ concurrent connections

---

## Dokumentation

- **[Testing Guide](docs/TESTING_GUIDE.md)** - Detaillierte Anleitung
- **[WebSocket Quickstart](docs/WEBSOCKET_QUICKSTART.md)** - WebSocket Tests
- **[API Reference](docs/THEMIS_ENDPOINTS_QUICKREF.md)** - Endpoint Übersicht

---

## Struktur

```
veritas/
├── .github/
│   └── workflows/
│       └── test-suite.yml          # GitHub Actions Workflow
├── backend/
│   ├── adapters/                   # Adapter Implementierungen
│   ├── api/v3/                     # API Routers
│   └── services/                   # Services
├── tests/
│   ├── test_themisdb_adapter.py    # Adapter Tests
│   ├── test_themis_router.py       # ThemisDB API Tests
│   ├── test_adapter_router.py      # Adapter Management Tests
│   ├── test_websocket_router.py    # WebSocket Tests
│   └── load/
│       └── locustfile.py           # Load Tests
├── scripts/
│   ├── run_tests.ps1               # PowerShell Test Runner
│   └── run_tests.sh                # Bash Test Runner
├── pytest.ini                      # Pytest Config
├── .flake8                         # Flake8 Config
├── pyproject.toml                  # Tool Config
├── .pre-commit-config.yaml         # Pre-commit Hooks
├── Makefile                        # Make Targets
├── requirements.txt                # Production Dependencies
└── requirements-dev.txt            # Development Dependencies
```

---

## Commands Übersicht

### Lokale Ausführung

**PowerShell:**
```powershell
.\scripts\run_tests.ps1 -TestType all -Coverage
```

**Bash:**
```bash
bash scripts/run_tests.sh --type all --coverage
```

**Make:**
```bash
make test              # Alle Tests
make test-unit         # Unit Tests
make coverage          # Mit Coverage
make lint              # Code Quality
make format            # Code formatieren
make clean             # Cleanup
```

### CI/CD

```yaml
# .github/workflows/test-suite.yml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

---

## Troubleshooting

### Tests schlagen fehl

```bash
# Verbose Output
pytest tests/ -v --tb=short

# Einzelner Test
pytest tests/test_themis_router.py::test_vector_search -v

# Mit Debugger
pytest tests/ --pdb
```

### Import Errors

```bash
# PYTHONPATH setzen
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Langsame Tests

```bash
# Parallel Execution
pytest tests/ -n 4

# Nur schnelle Tests
pytest tests/ -m "not slow"
```

---

## Contributing

1. Fork Repository
2. Feature Branch erstellen (`git checkout -b feature/amazing`)
3. Tests schreiben & ausführen (`make test`)
4. Code formatieren (`make format`)
5. Commit (`git commit -m "Add amazing feature"`)
6. Push (`git push origin feature/amazing`)
7. Pull Request erstellen

**Requirements:**
- Alle Tests müssen grün sein
- Coverage darf nicht sinken
- Code muss formatiert sein (Black, isort)
- Keine Linting-Fehler (Flake8)
- Keine Security-Issues (Bandit)

---

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

---

## Support

**Issues:** [GitHub Issues](https://github.com/makr-code/VCC-AAT/issues)  
**Docs:** [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)  
**Contact:** development@vcc.ai
