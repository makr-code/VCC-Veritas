# VERITAS Comprehensive Test Plan & Specification

**Version:** 1.0
**Datum:** 2025-12-03
**Status:** Spezifikation für separaten PR
**Geschätzter Aufwand:** 3-5 Tage (vollständige Implementierung)

---

## Executive Summary

Dieses Dokument definiert eine umfassende Test-Strategie für alle VERITAS-Komponenten außerhalb der bereits implementierten AI-Agenten (Vector Chart, Presentation Canvas, Geo Sub-Agent, AI Image Generator). Die Test-Suite wird **~250-350 automatisierte Tests** mit Performance-Benchmarks und E2E-Tests umfassen.

---

## Zielsetzung

### Primäre Ziele

1. **Vollständige Test-Abdeckung** für alle VERITAS-Kernkomponenten
2. **Performance-Benchmarks** für kritische Operationen
3. **Integration Tests** für API-Endpunkte und Service-Interaktionen
4. **E2E Tests** für komplette Workflows
5. **CI/CD Integration** mit automatisierten Test-Pipelines
6. **Dokumentation** aller Test-Strategien und Best Practices

### Qualitätsmetriken

- **Code Coverage:** Minimum 80% für alle Komponenten
- **Branch Coverage:** Minimum 75%
- **Test Execution Time:** < 10 Minuten für vollständige Suite
- **Performance Regression:** < 5% Toleranz

---

## Komponenten-Übersicht

### Backend-Komponenten (zu testen)

#### 1. Services (`backend/services/`) - 23 Services

| Service | Priorität | Geschätzte Tests |
|---------|-----------|------------------|
| `rag_service.py` | **Hoch** | 25 |
| `query_service.py` | **Hoch** | 20 |
| `hypothesis_service.py` | **Hoch** | 18 |
| `agent_executor.py` | **Hoch** | 15 |
| `process_executor.py` | **Hoch** | 15 |
| `chat_persistence_service.py` | Mittel | 12 |
| `reranker_service.py` | Mittel | 10 |
| `pki_client.py` | Mittel | 10 |
| `context_window_manager.py` | Mittel | 10 |
| `token_budget_calculator.py` | Mittel | 8 |
| `token_overflow_handler.py` | Mittel | 8 |
| `veritas_streaming_service.py` | Mittel | 12 |
| `websocket_progress_bridge.py` | Mittel | 8 |
| `nlp_service.py` | Niedrig | 8 |
| `intent_classifier.py` | Niedrig | 8 |
| `office_parsers.py` | Niedrig | 10 |
| `process_builder.py` | Niedrig | 8 |
| `peer_review_service.py` | Niedrig | 8 |
| `stage_reflection_service.py` | Niedrig | 8 |
| `dialectical_synthesis_service.py` | Niedrig | 8 |
| `scientific_phase_executor.py` | Niedrig | 8 |
| `prompt_improvement_engine.py` | Niedrig | 6 |
| Weitere Services | Niedrig | 10 |

**Gesamt Services:** ~235 Unit Tests

#### 2. API-Endpunkte (`backend/api/`) - 45+ Endpunkte

##### V3 API Router

| Router | Endpunkte | Geschätzte Tests |
|--------|-----------|------------------|
| `database_router.py` | 8 | 16 |
| `query_router.py` | 6 | 12 |
| `agent_router.py` | 5 | 10 |
| `themis_router.py` | 5 | 10 |
| `covina_router.py` | 4 | 8 |
| `immi_router.py` | 4 | 8 |
| `pki_router.py` | 4 | 8 |
| `user_router.py` | 4 | 8 |
| `system_router.py` | 3 | 6 |
| `compliance_router.py` | 3 | 6 |
| `governance_router.py` | 3 | 6 |
| `adapter_router.py` | 2 | 4 |
| `websocket_router.py` | 2 | 4 |
| `vpb_router.py` | 2 | 4 |
| `saga_router.py` | 2 | 4 |
| `uds3_router.py` | 2 | 4 |

##### Legacy API

| Modul | Endpunkte | Geschätzte Tests |
|-------|-----------|------------------|
| `veritas_api_backend.py` | 6 | 12 |
| `streaming_api.py` | 3 | 6 |
| `auth_endpoints.py` | 4 | 8 |
| `feedback_routes.py` | 2 | 4 |
| `mcp_http_endpoints.py` | 2 | 4 |
| `sse_endpoints.py` | 2 | 4 |

**Gesamt API:** ~136 Integration Tests

#### 3. Orchestration (`backend/orchestration/`)

| Komponente | Geschätzte Tests |
|------------|------------------|
| `unified_orchestrator_v7.py` | 20 |
| Agent Coordination | 15 |
| Process Workflows | 15 |

**Gesamt Orchestration:** ~50 Tests

#### 4. Database (`backend/database/`)

| Komponente | Geschätzte Tests |
|------------|------------------|
| Connection Manager | 12 |
| Query Builder | 15 |
| Migration Scripts | 8 |
| Database Adapters | 10 |

**Gesamt Database:** ~45 Tests

#### 5. Frontend (`vqb_frontend/`)

| Komponente | Geschätzte Tests |
|------------|------------------|
| UI-Komponenten | 20 |
| Controller | 15 |
| State Management | 10 |
| Event Handlers | 10 |

**Gesamt Frontend:** ~55 Tests (optional, separate Test-Strategie)

---

## Test-Kategorien

### 1. Unit Tests (~235 Tests)

**Umfang:** Isolierte Funktionen, Methoden, Klassen

**Beispiel-Struktur:**
```
tests/
├── services/
│   ├── test_rag_service.py
│   ├── test_query_service.py
│   ├── test_hypothesis_service.py
│   ├── test_agent_executor.py
│   ├── test_process_executor.py
│   ├── test_chat_persistence_service.py
│   ├── test_reranker_service.py
│   ├── test_pki_client.py
│   ├── test_context_window_manager.py
│   ├── test_token_budget_calculator.py
│   ├── test_nlp_service.py
│   ├── test_intent_classifier.py
│   └── ... (weitere Services)
├── orchestration/
│   ├── test_unified_orchestrator.py
│   ├── test_agent_coordination.py
│   └── test_process_workflows.py
└── database/
    ├── test_connection_manager.py
    ├── test_query_builder.py
    └── test_adapters.py
```

**Test-Template:**
```python
import pytest
from backend.services.rag_service import RAGService

@pytest.mark.unit
class TestRAGService:
    """Unit tests for RAG Service"""

    @pytest.fixture
    def rag_service(self):
        return RAGService()

    def test_initialization(self, rag_service):
        """Test RAG service initialization"""
        assert rag_service is not None
        assert hasattr(rag_service, 'retrieve')

    @pytest.mark.asyncio
    async def test_retrieve_documents(self, rag_service):
        """Test document retrieval"""
        query = "BImSchG Genehmigung"
        results = await rag_service.retrieve(query, top_k=5)
        assert isinstance(results, list)
        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_retrieve_with_filters(self, rag_service):
        """Test retrieval with metadata filters"""
        query = "Windenergie"
        filters = {"category": "1.1"}
        results = await rag_service.retrieve(
            query,
            top_k=10,
            filters=filters
        )
        assert all(doc['metadata']['category'] == '1.1' for doc in results)

    def test_invalid_query(self, rag_service):
        """Test handling of invalid queries"""
        with pytest.raises(ValueError):
            rag_service.retrieve("")
```

### 2. Integration Tests (~136 Tests)

**Umfang:** API-Endpunkte, Service-Interaktionen, Datenbankzugriff

**Beispiel-Struktur:**
```
tests/
└── integration/
    ├── test_api_v3_routers.py
    ├── test_database_api.py
    ├── test_query_api.py
    ├── test_agent_api.py
    ├── test_themis_api.py
    ├── test_covina_api.py
    ├── test_immi_api.py
    ├── test_pki_api.py
    ├── test_streaming_api.py
    ├── test_websocket_api.py
    └── test_service_interactions.py
```

**Test-Template:**
```python
import pytest
from httpx import AsyncClient
from backend.app import app

@pytest.mark.integration
class TestDatabaseAPI:
    """Integration tests for Database API endpoints"""

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_query_endpoint(self, client):
        """Test database query endpoint"""
        response = await client.post(
            "/api/v3/database/query",
            json={
                "query": "SELECT * FROM bimschg_anlagen LIMIT 5",
                "database": "uds3"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) <= 5

    @pytest.mark.asyncio
    async def test_statistics_endpoint(self, client):
        """Test database statistics endpoint"""
        response = await client.get("/api/v3/database/statistics")
        assert response.status_code == 200
        stats = response.json()
        assert "total_records" in stats
        assert "tables" in stats

    @pytest.mark.asyncio
    async def test_invalid_query(self, client):
        """Test handling of invalid SQL queries"""
        response = await client.post(
            "/api/v3/database/query",
            json={"query": "INVALID SQL", "database": "uds3"}
        )
        assert response.status_code in [400, 422]
        assert "error" in response.json()
```

### 3. Performance Benchmarks (~30 Benchmarks)

**Umfang:** Kritische Operationen, Durchsatz, Latenz, Speichernutzung

**Beispiel-Struktur:**
```
tests/
└── benchmarks/
    ├── test_service_benchmarks.py
    ├── test_api_benchmarks.py
    ├── test_database_benchmarks.py
    └── test_orchestration_benchmarks.py
```

**Benchmark-Template:**
```python
import pytest
import time
import psutil
import os

@pytest.mark.benchmark
class TestRAGServiceBenchmarks:
    """Performance benchmarks for RAG Service"""

    @pytest.mark.asyncio
    async def test_rag_retrieval_throughput(self):
        """Benchmark: RAG retrieval throughput"""
        from backend.services.rag_service import RAGService

        service = RAGService()
        queries = [f"Query {i}" for i in range(100)]

        # Memory before
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # Benchmark execution
        start = time.time()
        results = []
        for query in queries:
            result = await service.retrieve(query, top_k=5)
            results.append(result)
        duration = time.time() - start

        # Memory after
        mem_after = process.memory_info().rss / 1024 / 1024  # MB

        # Metrics
        throughput = len(queries) / duration
        avg_latency = (duration / len(queries)) * 1000  # ms
        memory_delta = mem_after - mem_before

        print(f"\n=== RAG Retrieval Benchmark ===")
        print(f"Queries: {len(queries)}")
        print(f"Duration: {duration:.2f}s")
        print(f"Throughput: {throughput:.2f} queries/s")
        print(f"Avg Latency: {avg_latency:.2f}ms")
        print(f"Memory Delta: {memory_delta:.2f} MB")

        # Assertions
        assert throughput > 5.0, "RAG throughput should be > 5 queries/s"
        assert avg_latency < 200, "RAG latency should be < 200ms"
        assert memory_delta < 100, "Memory delta should be < 100 MB"
```

### 4. End-to-End Tests (~20 Tests)

**Umfang:** Komplette Workflows, Multi-Service-Interaktionen

**Beispiel-Struktur:**
```
tests/
└── e2e/
    ├── test_complete_query_workflow.py
    ├── test_document_ingestion_workflow.py
    ├── test_hypothesis_generation_workflow.py
    └── test_agent_execution_workflow.py
```

**E2E-Test-Template:**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.e2e
class TestCompleteQueryWorkflow:
    """End-to-end tests for complete query workflows"""

    @pytest.mark.asyncio
    async def test_bimschg_query_to_result(self):
        """E2E: BImSchG query → RAG → Hypothesis → Result"""
        async with AsyncClient(base_url="http://test") as client:
            # Step 1: Submit query
            query_response = await client.post(
                "/api/v3/query/execute",
                json={
                    "query": "Wie viele BImSchG-Anlagen sind in Brandenburg?",
                    "context": "statistical"
                }
            )
            assert query_response.status_code == 200
            query_id = query_response.json()["query_id"]

            # Step 2: Wait for RAG retrieval
            import asyncio
            await asyncio.sleep(2)

            # Step 3: Check hypothesis generation
            hypothesis_response = await client.get(
                f"/api/v3/query/{query_id}/hypothesis"
            )
            assert hypothesis_response.status_code == 200
            hypothesis = hypothesis_response.json()
            assert "hypothesis" in hypothesis

            # Step 4: Get final result
            result_response = await client.get(
                f"/api/v3/query/{query_id}/result"
            )
            assert result_response.status_code == 200
            result = result_response.json()
            assert "answer" in result
            assert "sources" in result
```

---

## Test-Infrastruktur

### Ordnerstruktur

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures & configuration
├── services/                   # Service unit tests
│   ├── __init__.py
│   ├── test_rag_service.py
│   ├── test_query_service.py
│   └── ...
├── integration/                # API integration tests
│   ├── __init__.py
│   ├── test_api_v3_routers.py
│   └── ...
├── benchmarks/                 # Performance benchmarks
│   ├── __init__.py
│   ├── test_service_benchmarks.py
│   └── ...
├── e2e/                       # End-to-end tests
│   ├── __init__.py
│   ├── test_complete_query_workflow.py
│   └── ...
├── orchestration/             # Orchestration tests
│   ├── __init__.py
│   ├── test_unified_orchestrator.py
│   └── ...
├── database/                  # Database tests
│   ├── __init__.py
│   ├── test_connection_manager.py
│   └── ...
└── fixtures/                  # Test data & fixtures
    ├── __init__.py
    ├── sample_queries.json
    ├── sample_documents.json
    └── mock_responses.json
```

### conftest.py (Shared Fixtures)

```python
"""
Shared test fixtures and configuration for VERITAS test suite
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from backend.app import app

# Pytest configuration
pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for API tests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_queries():
    """Sample query data for tests"""
    return [
        {
            "query": "Wie viele BImSchG-Anlagen gibt es?",
            "context": "statistical"
        },
        {
            "query": "Welche Genehmigungen wurden 2023 erteilt?",
            "context": "temporal"
        }
    ]

@pytest.fixture
def mock_rag_response():
    """Mock RAG service response"""
    return {
        "documents": [
            {
                "content": "BImSchG-Anlage XYZ",
                "metadata": {"category": "1.1", "year": 2023},
                "score": 0.95
            }
        ],
        "total": 1
    }

@pytest.fixture(scope="session")
def database_url():
    """Test database URL"""
    return "postgresql://test:test@localhost:5432/veritas_test"

@pytest.fixture
async def db_session():
    """Database session for tests"""
    # Setup test database
    # Yield session
    # Cleanup
    pass
```

### pytest.ini (Enhanced Configuration)

```ini
[pytest]
# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Test markers
markers =
    unit: Unit tests for isolated components
    integration: Integration tests for API endpoints and service interactions
    benchmark: Performance benchmarks for critical operations
    e2e: End-to-end tests for complete workflows
    slow: Tests that take longer than 5 seconds
    requires_database: Tests requiring database connection
    requires_llm: Tests requiring LLM service
    requires_chromadb: Tests requiring ChromaDB

# Asyncio configuration
asyncio_mode = auto

# Coverage configuration
addopts =
    --verbose
    --strict-markers
    --tb=short
    --cov=backend
    --cov-report=html:reports/coverage_html
    --cov-report=xml:reports/coverage.xml
    --cov-report=term-missing
    --junitxml=reports/junit.xml
    --maxfail=5
    -p no:warnings

# Timeout
timeout = 300
timeout_method = thread

# Test paths
testpaths = tests

# Minimum coverage
;--cov-fail-under=80
```

---

## Test-Ausführung

### Lokale Ausführung

```bash
# Alle Tests
pytest

# Nur Unit Tests
pytest -v -m unit

# Nur Integration Tests
pytest -v -m integration

# Nur Benchmarks
pytest -v -m benchmark

# Nur E2E Tests
pytest -v -m e2e

# Spezifischer Test
pytest tests/services/test_rag_service.py -v

# Mit Coverage
pytest --cov=backend/services --cov-report=html

# Parallele Ausführung (schneller)
pytest -n auto

# Nur fehlgeschlagene Tests wiederholen
pytest --lf

# Verbose mit stdout
pytest -v -s
```

### CI/CD Integration

#### GitHub Actions Workflow

```yaml
name: VERITAS Test Suite

on:
  push:
    branches: [ main, develop, copilot/* ]
  pull_request:
    branches: [ main, develop ]

jobs:
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run unit tests
        run: pytest -v -m unit --cov=backend --junitxml=junit.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: veritas_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run integration tests
        run: pytest -v -m integration --junitxml=junit-integration.xml
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/veritas_test

  benchmarks:
    name: Performance Benchmarks
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run benchmarks
        run: pytest -v -m benchmark --benchmark-json=benchmark-results.json

      - name: Upload benchmark results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: benchmark-results.json
```

---

## Komponenten-Details

### 1. RAG Service Tests

**Datei:** `tests/services/test_rag_service.py`

**Test-Kategorien:**
- Initialisierung und Konfiguration
- Dokument-Retrieval (Top-K, Filters)
- Embedding-Generierung
- Vektor-Suche (ChromaDB Integration)
- Re-Ranking
- Fehlerbehandlung
- Performance (Latenz, Durchsatz)

**Geschätzte Tests:** 25

### 2. Query Service Tests

**Datei:** `tests/services/test_query_service.py`

**Test-Kategorien:**
- Query-Ausführung
- Parameter-Validierung
- Cache-Mechanismus
- Error Handling
- Streaming-Responses
- Query-Transformation
- Result-Aggregation

**Geschätzte Tests:** 20

### 3. Hypothesis Service Tests

**Datei:** `tests/services/test_hypothesis_service.py`

**Test-Kategorien:**
- Hypothesis-Generierung
- LLM-Integration
- Prompt-Templates
- Context-Window-Management
- Dialectical Synthesis
- Scientific Phase Execution
- Peer Review

**Geschätzte Tests:** 18

### 4. Agent Executor Tests

**Datei:** `tests/services/test_agent_executor.py`

**Test-Kategorien:**
- Agent-Initialisierung
- Task-Execution
- Error Recovery
- Parallel Execution
- Resource Management
- Logging & Monitoring

**Geschätzte Tests:** 15

### 5. Process Executor Tests

**Datei:** `tests/services/test_process_executor.py`

**Test-Kategorien:**
- Process Orchestration
- Workflow Execution
- Stage Management
- Error Handling
- Progress Tracking

**Geschätzte Tests:** 15

### 6. Database API Tests

**Datei:** `tests/integration/test_database_api.py`

**Test-Kategorien:**
- Query Execution
- Statistics Endpoints
- Schema Endpoints
- Connection Management
- Error Handling
- Security & Auth

**Geschätzte Tests:** 16

### 7. Unified Orchestrator Tests

**Datei:** `tests/orchestration/test_unified_orchestrator.py`

**Test-Kategorien:**
- Multi-Agent Coordination
- Workflow Execution
- Resource Allocation
- Error Propagation
- Performance Optimization

**Geschätzte Tests:** 20

---

## Performance-Benchmarks

### Kritische Operationen

| Operation | Ziel-Metrik | Priorität |
|-----------|-------------|-----------|
| RAG Retrieval (5 docs) | < 200ms | Hoch |
| Query Execution | < 2s | Hoch |
| Hypothesis Generation | < 5s | Hoch |
| Database Query | < 100ms | Hoch |
| Agent Task Execution | < 10s | Mittel |
| Document Embedding | < 500ms | Mittel |
| Re-Ranking (20 docs) | < 300ms | Mittel |
| WebSocket Message | < 50ms | Niedrig |

### Benchmark-Suite

```python
# tests/benchmarks/test_critical_operations.py

@pytest.mark.benchmark
class TestCriticalOperationsBenchmarks:
    """Benchmarks for critical VERITAS operations"""

    @pytest.mark.asyncio
    async def test_rag_retrieval_latency(self):
        """Benchmark: RAG retrieval latency (5 docs)"""
        # Target: < 200ms
        pass

    @pytest.mark.asyncio
    async def test_query_execution_latency(self):
        """Benchmark: Complete query execution"""
        # Target: < 2s
        pass

    @pytest.mark.asyncio
    async def test_hypothesis_generation_latency(self):
        """Benchmark: Hypothesis generation"""
        # Target: < 5s
        pass

    @pytest.mark.asyncio
    async def test_database_query_latency(self):
        """Benchmark: Database query latency"""
        # Target: < 100ms
        pass
```

---

## Dokumentation

### Test-Dokumentation erstellen

Für jede Test-Datei:

1. **Modul-Docstring:** Beschreibung, Umfang, Abhängigkeiten
2. **Klassen-Docstring:** Test-Kategorie, Setup-Requirements
3. **Methoden-Docstring:** Was wird getestet, erwartetes Ergebnis
4. **Inline-Kommentare:** Komplexe Test-Logik erklären

**Beispiel:**
```python
"""
Unit tests for RAG Service

Tests cover:
- Document retrieval with various filters
- Embedding generation
- Vector search operations
- Re-ranking functionality
- Error handling and edge cases

Dependencies:
- ChromaDB (in-memory for tests)
- Mock LLM responses
- Sample document fixtures

Author: VERITAS Team
Date: 2025-12-03
"""

class TestRAGService:
    """
    Unit tests for RAG Service core functionality

    Setup:
    - In-memory ChromaDB instance
    - Mock embedding model
    - Sample document fixtures

    Cleanup:
    - Clear ChromaDB collections
    - Reset mock responses
    """

    @pytest.fixture
    def rag_service(self):
        """
        Create RAG service instance with test configuration

        Returns:
            RAGService: Configured service instance
        """
        # Implementation
        pass

    @pytest.mark.asyncio
    async def test_retrieve_with_filters(self, rag_service):
        """
        Test document retrieval with metadata filters

        Scenario:
        1. Query for "Windenergie" with category filter
        2. Verify all results match filter criteria
        3. Verify result count <= top_k

        Expected:
        - Returns list of documents
        - All documents have category='1.1'
        - Result count <= top_k
        """
        # Test implementation
        pass
```

---

## Zeitplan & Priorisierung

### Phase 1: Foundations (Tag 1)

**Ziel:** Test-Infrastruktur und kritische Services

- [ ] Test-Ordnerstruktur erstellen
- [ ] `conftest.py` mit Shared Fixtures
- [ ] `pytest.ini` konfigurieren
- [ ] CI/CD Workflow (GitHub Actions)
- [ ] **RAG Service Tests** (25 Tests) ✅
- [ ] **Query Service Tests** (20 Tests) ✅
- [ ] **Hypothesis Service Tests** (18 Tests) ✅

**Deliverable:** ~63 Tests, CI/CD funktioniert

### Phase 2: Core Services (Tag 2)

**Ziel:** Weitere kritische Services

- [ ] **Agent Executor Tests** (15 Tests)
- [ ] **Process Executor Tests** (15 Tests)
- [ ] **Chat Persistence Tests** (12 Tests)
- [ ] **Reranker Service Tests** (10 Tests)
- [ ] **PKI Client Tests** (10 Tests)
- [ ] **Context Window Manager Tests** (10 Tests)

**Deliverable:** +72 Tests (Total: ~135)

### Phase 3: Integration & API (Tag 3)

**Ziel:** API-Endpunkte und Integrationen

- [ ] **Database API Tests** (16 Tests)
- [ ] **Query API Tests** (12 Tests)
- [ ] **Agent API Tests** (10 Tests)
- [ ] **Themis API Tests** (10 Tests)
- [ ] **Covina API Tests** (8 Tests)
- [ ] **IMMI API Tests** (8 Tests)
- [ ] **PKI API Tests** (8 Tests)
- [ ] **Weitere Router Tests** (30 Tests)

**Deliverable:** +102 Tests (Total: ~237)

### Phase 4: Orchestration & Database (Tag 4)

**Ziel:** Orchestration und Database Layer

- [ ] **Unified Orchestrator Tests** (20 Tests)
- [ ] **Agent Coordination Tests** (15 Tests)
- [ ] **Process Workflows Tests** (15 Tests)
- [ ] **Connection Manager Tests** (12 Tests)
- [ ] **Query Builder Tests** (15 Tests)
- [ ] **Database Adapters Tests** (10 Tests)

**Deliverable:** +87 Tests (Total: ~324)

### Phase 5: Benchmarks & E2E (Tag 5)

**Ziel:** Performance und End-to-End

- [ ] **Service Benchmarks** (12 Benchmarks)
- [ ] **API Benchmarks** (8 Benchmarks)
- [ ] **Database Benchmarks** (6 Benchmarks)
- [ ] **Orchestration Benchmarks** (4 Benchmarks)
- [ ] **E2E Query Workflow** (5 Tests)
- [ ] **E2E Document Ingestion** (5 Tests)
- [ ] **E2E Hypothesis Generation** (5 Tests)
- [ ] **E2E Agent Execution** (5 Tests)

**Deliverable:** +50 Tests/Benchmarks (Total: ~374)

### Finale Aufgaben

- [ ] Code Coverage Report (Ziel: >80%)
- [ ] Performance Baseline dokumentieren
- [ ] Test-Dokumentation finalisieren
- [ ] PR-Review und Merge

---

## Dependencies

### Zusätzliche Test-Dependencies

```txt
# requirements-dev.txt (erweitert)

# Testing frameworks
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-xdist>=3.3.0          # Parallel execution
pytest-timeout>=2.1.0        # Test timeouts
pytest-benchmark>=4.0.0      # Benchmarking

# HTTP testing
httpx>=0.24.0
respx>=0.20.0                # HTTP mocking

# Database testing
pytest-postgresql>=5.0.0     # PostgreSQL fixtures
pytest-docker>=2.0.0         # Docker containers for tests

# Performance monitoring
psutil>=5.9.0
memory-profiler>=0.61.0

# Code quality
mypy>=1.5.0
black>=23.7.0
flake8>=6.1.0
isort>=5.12.0

# Mocking & fixtures
faker>=19.3.0                # Fake data generation
factory-boy>=3.3.0           # Test fixtures
freezegun>=1.2.2             # Time mocking
responses>=0.23.0            # HTTP response mocking
```

---

## Metriken & Reporting

### Code Coverage

**Ziel-Metriken:**
- **Line Coverage:** > 80%
- **Branch Coverage:** > 75%
- **Function Coverage:** > 85%

**Tools:**
- `pytest-cov` für Coverage-Generierung
- Codecov für CI/CD Integration
- HTML Reports für lokale Analyse

### Performance Monitoring

**Metriken:**
- Ausführungszeit pro Test
- Durchsatz (Operationen/Sekunde)
- Latenz (ms pro Operation)
- Speichernutzung (MB Delta)
- CPU-Auslastung

**Tools:**
- `pytest-benchmark` für Benchmarks
- `psutil` für System-Metriken
- Custom Performance Reporter

### Test Reports

**Generierte Reports:**
1. **JUnit XML** - CI/CD Integration
2. **HTML Coverage Report** - Visueller Coverage-Überblick
3. **Benchmark JSON** - Performance-Metriken
4. **Test Summary** - Aggregierte Statistiken

---

## Best Practices

### Test-Design

1. **Isolation:** Jeder Test unabhängig
2. **Determinismus:** Gleiche Eingabe → Gleiche Ausgabe
3. **Schnelligkeit:** Unit Tests < 1s, Integration Tests < 5s
4. **Lesbarkeit:** Klare Test-Namen, gute Dokumentation
5. **Wartbarkeit:** DRY-Prinzip, Shared Fixtures

### Fixture-Management

```python
# Gutes Beispiel: Wiederverwendbare Fixtures
@pytest.fixture
def sample_query():
    return {
        "query": "BImSchG Genehmigungen",
        "context": "statistical"
    }

@pytest.fixture
def rag_service(mock_chromadb):
    return RAGService(chromadb=mock_chromadb)

# Test verwendet Fixtures
def test_query_execution(rag_service, sample_query):
    result = rag_service.execute(sample_query)
    assert result is not None
```

### Mocking-Strategien

```python
# Mock externe Services
@pytest.fixture
def mock_llm_service(monkeypatch):
    async def mock_generate(prompt):
        return {"response": "Mocked LLM response"}

    monkeypatch.setattr(
        "backend.services.llm_service.generate",
        mock_generate
    )

# Mock Datenbank
@pytest.fixture
def mock_database(monkeypatch):
    mock_results = [{"id": 1, "name": "Test"}]

    async def mock_query(sql):
        return mock_results

    monkeypatch.setattr(
        "backend.database.connection.execute",
        mock_query
    )
```

### Fehlerbehandlung testen

```python
def test_invalid_input_handling(rag_service):
    """Test proper error handling for invalid input"""
    with pytest.raises(ValueError, match="Query cannot be empty"):
        rag_service.retrieve("")

    with pytest.raises(TypeError, match="top_k must be integer"):
        rag_service.retrieve("test", top_k="invalid")
```

---

## Risiken & Mitigation

### Identifizierte Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Test-Daten veraltet | Mittel | Mittel | Automatische Fixture-Generierung |
| Flaky Tests | Mittel | Hoch | Retry-Mechanismus, bessere Isolation |
| Lange Ausführungszeit | Hoch | Mittel | Parallele Ausführung, Test-Optimierung |
| Mock vs. Real Service | Mittel | Hoch | Integration Tests mit echten Services |
| Dependency-Konflikte | Niedrig | Hoch | Strikte Dependency-Pinning |

### Mitigation-Strategien

1. **Flaky Tests:** Retry-Mechanismus mit `pytest-rerunfailures`
2. **Performance:** Parallele Ausführung mit `pytest-xdist`
3. **Dependencies:** Docker-Container für Integration Tests
4. **Maintenance:** Automatische Test-Updates bei API-Änderungen

---

## Success Criteria

### Definition of Done

Ein Test-Modul ist "Done" wenn:

- [ ] Alle geplanten Tests implementiert
- [ ] Code Coverage > 80% für getestete Komponente
- [ ] Alle Tests bestehen (lokal + CI/CD)
- [ ] Dokumentation vollständig
- [ ] Performance-Benchmarks definiert
- [ ] PR-Review abgeschlossen

### Gesamt-Projekt Success Criteria

- [ ] **~250-350 Tests** implementiert
- [ ] **Code Coverage** > 80% gesamt
- [ ] **CI/CD Pipeline** funktioniert
- [ ] **Performance Baselines** dokumentiert
- [ ] **Test-Dokumentation** vollständig
- [ ] **Alle kritischen Services** getestet

---

## Nächste Schritte

### Für neuen PR

1. **Issue erstellen** mit diesem Dokument als Spezifikation
2. **Branch erstellen:** `feature/veritas-comprehensive-tests`
3. **Phase 1 starten:** Foundations + kritische Services
4. **Iterativ entwickeln:** Daily Progress Reports
5. **Review & Merge:** Nach jeder Phase

### Immediate Actions

```bash
# 1. Neuen Branch erstellen
git checkout -b feature/veritas-comprehensive-tests

# 2. Test-Struktur anlegen
mkdir -p tests/{services,integration,benchmarks,e2e,orchestration,database,fixtures}
touch tests/__init__.py tests/conftest.py

# 3. pytest.ini aktualisieren
# (siehe Konfiguration oben)

# 4. Erste Tests schreiben
# tests/services/test_rag_service.py
```

---

## Anhang

### Verwandte Dokumente

- `docs/AI_AGENT_TESTING.md` - Test-Suite für AI-Agenten
- `docs/TEST_SUITE_SUMMARY.md` - Zusammenfassung AI-Agent Tests
- `TESTING_README.md` - Allgemeine Testing-Richtlinien
- `DEVELOPMENT.md` - Entwicklungs-Richtlinien

### Referenzen

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Codecov](https://about.codecov.io/)

### Kontakt

- **Team:** VERITAS Development Team
- **Maintainer:** @makr-code
- **Created:** 2025-12-03
- **Version:** 1.0

---

**Ende der Spezifikation**

Dieses Dokument dient als Basis für einen separaten PR zur Implementierung der umfassenden Test-Suite für alle VERITAS-Komponenten.
