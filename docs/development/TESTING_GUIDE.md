# ThemisDB Adapter - Test Suite Guide

**Erstellt:** 7. November 2025
**Version:** 1.0
**Status:** ✅ Production-Ready

---

## Übersicht

Umfassende Test-Suite für ThemisDB/UDS3 Adapter mit:

- ✅ **Unit Tests** (Mock-basiert, schnell)
- ✅ **Integration Tests** (mit Redis/PostgreSQL)
- ✅ **API Tests** (REST Endpoints)
- ✅ **WebSocket Tests** (Real-time Kommunikation)
- ✅ **Load Tests** (Locust)
- ✅ **Code Quality** (Black, Flake8, Pylint, mypy)
- ✅ **Security Checks** (Bandit, pip-audit)
- ✅ **CI/CD Integration** (GitHub Actions)

---

## Quick Start

### Lokale Ausführung

**PowerShell (Windows):**
```powershell
# Alle Tests
.\scripts\run_tests.ps1 -TestType all -Coverage

# Nur Unit Tests
.\scripts\run_tests.ps1 -TestType unit -Verbose

# API Tests
.\scripts\run_tests.ps1 -TestType api

# WebSocket Tests
.\scripts\run_tests.ps1 -TestType websocket

# Linting
.\scripts\run_tests.ps1 -TestType lint

# Parallel Execution (schneller)
.\scripts\run_tests.ps1 -TestType unit -Parallel -Workers 4
```

**Bash (Linux/Mac):**
```bash
# Alle Tests
bash scripts/run_tests.sh --type all --coverage

# Unit Tests
bash scripts/run_tests.sh --type unit --verbose

# Parallel
bash scripts/run_tests.sh --type all --parallel --workers 4
```

**Makefile:**
```bash
# Alle verfügbaren Commands anzeigen
make help

# Tests ausführen
make test              # Alle Tests
make test-unit         # Unit Tests
make test-integration  # Integration Tests
make test-api          # API Tests
make test-websocket    # WebSocket Tests

# Code Quality
make lint              # Linting Checks
make format            # Code formatieren
make security          # Security Scan (Bandit + pip-audit)

# Coverage
make coverage          # Tests mit Coverage Report

# Load Testing
make load-test         # Locust Load Tests

# Cleanup
make clean             # Temporäre Dateien löschen
```

---

## Installation

### Dependencies installieren

```bash
# Production Dependencies
pip install -r requirements.txt

# Development Dependencies
pip install -r requirements-dev.txt

# Pre-commit Hooks
pre-commit install
```

### Virtual Environment (empfohlen)

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

---

## Test-Kategorien

### 1. Unit Tests

**Marker:** `@pytest.mark.unit`

```bash
pytest tests/ -m "unit"
```

**Eigenschaften:**
- Schnell (< 1 Sekunde pro Test)
- Keine externen Dependencies
- Mock-basiert
- Hohe Coverage

**Beispiel:**
```python
@pytest.mark.unit
def test_themisdb_adapter_config():
    config = ThemisDBConfig.from_env()
    assert config.host == "localhost"
    assert config.port == 8765
```

### 2. Integration Tests

**Marker:** `@pytest.mark.integration`

```bash
pytest tests/ -m "integration"
```

**Eigenschaften:**
- Benötigt Services (Redis, PostgreSQL)
- Langsamer als Unit Tests
- Testet Interaktion zwischen Komponenten

**Beispiel:**
```python
@pytest.mark.integration
async def test_adapter_with_redis():
    # Test mit echtem Redis
    pass
```

### 3. API Tests

**Marker:** `@pytest.mark.api`

```bash
pytest tests/test_themis_router.py tests/test_adapter_router.py -v
```

**Eigenschaften:**
- Testet REST Endpoints
- FastAPI TestClient
- Response Validation

### 4. WebSocket Tests

**Marker:** `@pytest.mark.websocket`

```bash
pytest tests/test_websocket_router.py -v
```

**Eigenschaften:**
- Real-time Kommunikation
- Connection Management
- Message Streaming

### 5. End-to-End Tests

**Marker:** `@pytest.mark.e2e`

```bash
pytest tests/ -m "e2e"
```

**Eigenschaften:**
- Kompletter System-Test
- Alle Services müssen laufen
- Langsam aber realistisch

---

## Code Quality Checks

### Black (Code Formatter)

```bash
# Check
black --check backend/ tests/

# Format
black backend/ tests/
```

### isort (Import Sorter)

```bash
# Check
isort --check-only backend/ tests/

# Format
isort backend/ tests/
```

### Flake8 (Linting)

```bash
flake8 backend/ tests/ --count --statistics
```

### Pylint

```bash
pylint backend/ --exit-zero
```

### mypy (Type Checking)

```bash
mypy backend/ --ignore-missing-imports
```

### Bandit (Security)

```bash
bandit -r backend/ -ll
```

---

## Coverage

### Lokale Coverage

```bash
# Mit HTML Report
pytest tests/ --cov=backend --cov-report=html

# Terminal Output
pytest tests/ --cov=backend --cov-report=term-missing

# XML für CI/CD
pytest tests/ --cov=backend --cov-report=xml
```

### Coverage öffnen

```bash
# Windows
start htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# Mac
open htmlcov/index.html
```

### Coverage Ziele

- **Gesamt:** > 80%
- **Backend Core:** > 90%
- **Adapters:** > 85%
- **Routers:** > 75%

---

## Load Testing

### Locust

**Starten:**
```bash
# Mit Web UI
locust -f tests/load/locustfile.py --host http://localhost:8000

# Headless
locust -f tests/load/locustfile.py \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 60s \
    --host http://localhost:8000 \
    --html locust-report.html
```

**Web UI:** `http://localhost:8089`

**Targets:**
- **Vector Search:** 1000+ RPS
- **Adapter Status:** 500+ RPS
- **WebSocket:** 100+ concurrent connections

---

## CI/CD (GitHub Actions)

### Workflow-Datei

`.github/workflows/test-suite.yml`

### Trigger

- **Push:** `main`, `develop` branches
- **Pull Request:** `main`, `develop` branches
- **Manual:** Workflow Dispatch

### Jobs

1. **Lint** - Code Quality Checks
2. **Unit Tests** - Python 3.10, 3.11, 3.12
3. **Integration Tests** - Mit Redis/PostgreSQL
4. **API Tests** - REST Endpoints
5. **WebSocket Tests** - Real-time Tests
6. **Load Tests** - Nur auf `main` branch
7. **Security Scan** - Trivy, Bandit, pip-audit
8. **Test Summary** - Aggregierte Ergebnisse

### Status Badge

```markdown
[![Tests](https://github.com/makr-code/VCC-AAT/workflows/ThemisDB%20Adapter%20Test%20Suite/badge.svg)](https://github.com/makr-code/VCC-AAT/actions)
```

### Artifacts

- Pytest Reports (XML)
- Coverage Reports (HTML)
- Bandit Security Reports
- Load Test Results
- Logs

---

## Pre-commit Hooks

### Installation

```bash
pre-commit install
```

### Ausführen

```bash
# Alle Dateien
pre-commit run --all-files

# Nur staged files (automatisch bei git commit)
git commit -m "Your message"
```

### Hooks

1. **Black** - Code Formatting
2. **isort** - Import Sorting
3. **Flake8** - Linting
4. **Bandit** - Security
5. **mypy** - Type Checking
6. **YAML Lint** - YAML Validation
7. **Markdown Lint** - Markdown Validation
8. **Trailing Whitespace** - Cleanup
9. **End of File Fixer** - Newline am Ende

---

## Pytest Konfiguration

### pytest.ini

**Test Discovery:**
- `test_*.py`
- `*_test.py`

**Markers:**
```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.websocket
@pytest.mark.slow
@pytest.mark.api
@pytest.mark.adapter
```

**Coverage:**
- Source: `backend/`
- Exclude: `tests/`, `*/venv/*`, `*/migrations/*`

### Fixtures

**Beispiel:**
```python
@pytest.fixture
def test_client():
    """FastAPI Test Client"""
    return TestClient(app)

@pytest.fixture
async def themis_adapter():
    """Mock ThemisDB Adapter"""
    adapter = AsyncMock()
    adapter.vector_search = AsyncMock(return_value=[...])
    return adapter
```

---

## Troubleshooting

### Problem: Tests schlagen fehl

```bash
# Verbose Output
pytest tests/ -v --tb=short

# Stop on first failure
pytest tests/ -x

# Show print statements
pytest tests/ -s
```

### Problem: Import Errors

```bash
# PYTHONPATH setzen
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Oder in pytest.ini
pythonpath = .
```

### Problem: Coverage zu niedrig

```bash
# Zeige nicht gecoverten Code
pytest tests/ --cov=backend --cov-report=term-missing

# Nur spezifische Module
pytest tests/ --cov=backend.adapters --cov-report=term
```

### Problem: Langsame Tests

```bash
# Parallel Execution
pytest tests/ -n 4

# Nur schnelle Tests
pytest tests/ -m "not slow"

# Zeige langsamste Tests
pytest tests/ --durations=10
```

---

## Best Practices

### 1. Test-Namenskonvention

```python
# ✓ Gut
def test_vector_search_returns_results()
def test_adapter_handles_connection_error()

# ✗ Schlecht
def test1()
def test_function()
```

### 2. Arrange-Act-Assert Pattern

```python
def test_vector_search():
    # Arrange
    adapter = ThemisDBAdapter()
    query = "test query"

    # Act
    results = await adapter.vector_search(query, top_k=5)

    # Assert
    assert len(results) == 5
    assert all("score" in r for r in results)
```

### 3. Mocking

```python
@patch('backend.adapters.adapter_factory.get_database_adapter')
def test_with_mock(mock_adapter):
    mock_adapter.return_value = AsyncMock()
    mock_adapter.return_value.vector_search = AsyncMock(return_value=[...])
    # Test logic
```

### 4. Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### 5. Parametrized Tests

```python
@pytest.mark.parametrize("query,expected", [
    ("test", 5),
    ("another", 3),
    ("third", 0)
])
def test_multiple_cases(query, expected):
    result = search(query)
    assert len(result) == expected
```

---

## Continuous Improvement

### Coverage-Trend

```bash
# Coverage über Zeit tracken
pytest tests/ --cov=backend --cov-report=json
# JSON zu Metrics-System exportieren
```

### Performance-Monitoring

```bash
# Test-Dauer tracken
pytest tests/ --durations=0 --json-report --json-report-file=report.json
```

### Code Complexity

```bash
# Radon für Complexity Metrics
radon cc backend/ -a
radon mi backend/
```

---

## FAQ

**Q: Wie lange dauern die Tests?**
A: Unit Tests: ~30s, Integration: ~2min, Alle: ~5min (parallel)

**Q: Welche Python-Versionen werden unterstützt?**
A: Python 3.10, 3.11, 3.12

**Q: Muss ich alle Services lokal laufen haben?**
A: Nein, Unit Tests funktionieren ohne. Integration Tests benötigen Redis/PostgreSQL.

**Q: Wie erhöhe ich Coverage?**
A: 1) Fehlende Tests schreiben, 2) Edge Cases testen, 3) Error Paths testen

**Q: Was ist der Unterschied zwischen Unit und Integration Tests?**
A: Unit Tests sind isoliert und schnell (Mocks), Integration Tests nutzen echte Services.

**Q: Wie kann ich einzelne Tests überspringen?**
A: `@pytest.mark.skip(reason="...")` oder `@pytest.mark.skipif(condition)`

**Q: Wie debugge ich Tests?**
A: 1) `pytest --pdb` für Debugger, 2) `pytest -s` für print(), 3) `pytest -v --tb=long`

---

## Ressourcen

**Dokumentation:**
- [Pytest Docs](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Locust Docs](https://docs.locust.io/)
- [GitHub Actions](https://docs.github.com/en/actions)

**Tools:**
- [Codecov](https://codecov.io/) - Coverage Tracking
- [SonarQube](https://www.sonarqube.org/) - Code Quality
- [Dependabot](https://github.com/dependabot) - Dependency Updates

---

**Status:** ✅ Production-Ready
**Maintainer:** VCC Development Team
**Last Updated:** 7. November 2025
