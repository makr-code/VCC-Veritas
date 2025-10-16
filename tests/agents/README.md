# 🧪 Veritas Agent Tests

**Generated:** 2025-10-08 16:26:13

This directory contains pytest test suites for all Veritas agents.

## 📊 Test Coverage Status

**Current Coverage:** 0.0%
**Agents with Tests:** 0/14

## 📁 Structure

```
tests/agents/
├── conftest.py              # Shared fixtures
├── README.md                # This file
├── test_<agent_name>.py     # Agent-specific tests
└── ...
```

## 🚀 Running Tests

### Run All Tests

```bash
pytest tests/agents/
```

### Run Specific Agent Tests

```bash
pytest tests/agents/test_financial.py
```

### Run with Coverage

```bash
pytest tests/agents/ --cov=backend/agents --cov-report=html
```

### Run Only Unit Tests (skip integration)

```bash
pytest tests/agents/ -m "not integration"
```

### Run Only Integration Tests

```bash
pytest tests/agents/ -m integration
```

### Run Migration Tests

```bash
pytest tests/agents/ -m migration
```

## 🏷️ Test Markers

- `@pytest.mark.integration` - Integration tests (slower, require services)
- `@pytest.mark.migration` - Framework migration compatibility tests
- `@pytest.mark.asyncio` - Async tests

## 📝 Test Template Structure

Each agent test file follows this structure:

1. **Initialization Tests** - Agent can be created
2. **Method Tests** - Public methods work correctly
3. **Tool Integration Tests** - External tools/APIs work
4. **Domain-Specific Tests** - Domain logic is correct
5. **Error Handling Tests** - Graceful error handling
6. **Performance Tests** - Response time acceptable
7. **Integration Tests** - End-to-end workflows
8. **Migration Tests** - Framework compatibility

## 🔧 Implementing Tests

### Step 1: Review Generated Template

Each test file has `pytest.skip("Test not implemented yet")` placeholders.

### Step 2: Implement Test Logic

Replace `pytest.skip()` with actual test logic:

```python
@pytest.mark.asyncio
async def test_query_processing(self, agent_instance, sample_query):
    """Test query processing."""
    result = await agent_instance.process_query(sample_query)
    
    assert result is not None
    assert "data" in result
    assert len(result["data"]) > 0
```

### Step 3: Add Domain-Specific Assertions

```python
@pytest.mark.asyncio
async def test_financial_query(self, agent_instance):
    """Test financial domain query."""
    result = await agent_instance.query_financial_data("cost of construction")
    
    assert "cost" in result or "price" in result
    assert result["currency"] == "EUR"
```

### Step 4: Mock External Dependencies

```python
@pytest.mark.asyncio
async def test_api_integration(self, agent_instance):
    """Test external API."""
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"data": "test"}
        
        result = await agent_instance.fetch_external_data()
        
        assert result["data"] == "test"
        mock_get.assert_called_once()
```

## 🎯 Migration Testing Checklist

Before migrating an agent to the new framework:

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Test coverage >80%
- [ ] Error handling tested
- [ ] Performance benchmarks established
- [ ] Framework compatibility verified

## 📊 Test Agents by Priority

### 🔴 HIGH Priority (10 agents)

Must have tests before migration:

- `atmospheric_flow` - environmental (1241 LOC)
- `chemical_data` - environmental (1232 LOC)
- `construction` - construction (891 LOC)
- `core_components` - financial (884 LOC)
- `dwd_weather` - environmental (896 LOC)
- `orchestrator` - financial (1105 LOC)
- `pipeline_manager` - environmental (620 LOC)
- `registry` - financial (675 LOC)
- `technical_standards` - technical (1252 LOC)
- `wikipedia` - general (1039 LOC)


### 🟡 MEDIUM Priority (3 agents)

- `financial` - financial (1050 LOC)
- `social` - social (1300 LOC)
- `traffic` - traffic (949 LOC)


### 🟢 LOW Priority (1 agents)

- `environmental` - environmental (573 LOC)


## 🛠️ Useful Commands

### Find Skipped Tests

```bash
pytest tests/agents/ -v | grep SKIPPED
```

### Run Only Implemented Tests

```bash
pytest tests/agents/ -k "not skip"
```

### Generate Coverage Report

```bash
pytest tests/agents/ --cov=backend/agents --cov-report=term-missing
```

### Run Tests in Parallel (faster)

```bash
pip install pytest-xdist
pytest tests/agents/ -n auto
```

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Gap Analysis Report](../../reports/AGENT_GAP_ANALYSIS.md)

## 🤝 Contributing

1. Pick an agent from the priority list
2. Implement tests following the template
3. Ensure all tests pass
4. Update this README with progress
5. Submit for review

---

**Last Updated:** 2025-10-08 16:26:13
