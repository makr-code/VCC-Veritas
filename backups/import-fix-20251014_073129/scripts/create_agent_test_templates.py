#!/usr/bin/env python3
"""
Test Template Generator for Veritas Agents
==========================================

Generates pytest test templates for all Veritas agents based on
the gap analysis results.

Usage:
    python scripts/create_agent_test_templates.py

Output:
    - tests/agents/test_<agent_name>.py for each agent
    - tests/agents/conftest.py with shared fixtures
    - tests/agents/README.md with testing guide
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class TestTemplateGenerator:
    """Generate pytest test templates for agents."""
    
    def __init__(self, gap_analysis_path: Path, output_dir: Path):
        self.gap_analysis_path = gap_analysis_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load gap analysis
        with open(gap_analysis_path, 'r', encoding='utf-8') as f:
            self.gap_data = json.load(f)
    
    def generate_all(self):
        """Generate all test templates."""
        print("📝 Generating test templates...")
        print()
        
        agents = self.gap_data['agents']
        
        # Generate conftest.py
        print("1. Creating conftest.py with shared fixtures...")
        self._generate_conftest()
        print(f"   ✅ Created: {self.output_dir / 'conftest.py'}")
        print()
        
        # Generate test files for each agent
        print(f"2. Creating test files for {len(agents)} agents...")
        for i, agent in enumerate(agents, 1):
            test_file = self._generate_test_file(agent)
            print(f"   {i:2d}. ✅ {test_file.name}")
        print()
        
        # Generate README
        print("3. Creating README.md with testing guide...")
        self._generate_readme()
        print(f"   ✅ Created: {self.output_dir / 'README.md'}")
        print()
        
        print("✅ All test templates generated!")
        print()
        print(f"📁 Output directory: {self.output_dir}")
        print()
        print("Next steps:")
        print("  1. Review generated tests")
        print("  2. Implement actual test logic")
        print("  3. Run: pytest tests/agents/")
        print()
    
    def _generate_conftest(self):
        """Generate conftest.py with shared fixtures."""
        content = '''"""
Shared pytest fixtures for agent tests.

This file contains common fixtures used across all agent tests:
- Mock UDS3 manager
- Mock database connections
- Sample test data
- Agent instances
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from pathlib import Path
import json


# ===== MOCK DATA FIXTURES =====

@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return "Was sind die Bauvorschriften für nachhaltiges Bauen?"


@pytest.fixture
def sample_documents():
    """Sample document corpus for testing."""
    return [
        {
            "doc_id": "doc_0",
            "content": "§110 BGB Taschengeldparagraph...",
            "metadata": {"source": "legal", "type": "bgb"}
        },
        {
            "doc_id": "doc_1",
            "content": "§433 BGB Kaufvertrag...",
            "metadata": {"source": "legal", "type": "bgb"}
        },
    ]


@pytest.fixture
def sample_context():
    """Sample context for agent execution."""
    return {
        "user_id": "test_user",
        "session_id": "test_session_123",
        "query": "test query",
        "parameters": {}
    }


# ===== MOCK UDS3 FIXTURES =====

@pytest.fixture
def mock_uds3_manager():
    """Mock UDS3 database manager."""
    mock = MagicMock()
    
    # Mock query methods
    mock.query = AsyncMock(return_value=[
        {"id": "1", "content": "Test result 1"},
        {"id": "2", "content": "Test result 2"},
    ])
    
    mock.query_across_databases = AsyncMock(return_value={
        "chroma": [{"id": "c1", "content": "Chroma result"}],
        "neo4j": [{"id": "n1", "content": "Neo4j result"}],
    })
    
    # Mock index methods
    mock.index_documents = AsyncMock(return_value={"indexed": 2})
    
    # Mock stats
    mock.get_stats = Mock(return_value={
        "total_queries": 100,
        "avg_latency_ms": 50.0,
    })
    
    return mock


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama LLM client."""
    mock = MagicMock()
    
    mock.chat = AsyncMock(return_value={
        "message": {
            "content": "This is a mock LLM response."
        }
    })
    
    mock.embed = AsyncMock(return_value={
        "embedding": [0.1] * 384  # Mock 384-dim embedding
    })
    
    return mock


@pytest.fixture
def mock_database():
    """Mock database connection."""
    mock = MagicMock()
    
    mock.execute = AsyncMock(return_value=[
        {"id": 1, "value": "data1"},
        {"id": 2, "value": "data2"},
    ])
    
    mock.fetch_one = AsyncMock(return_value={"id": 1, "value": "data1"})
    mock.fetch_all = AsyncMock(return_value=[{"id": 1}, {"id": 2}])
    
    return mock


# ===== AGENT REGISTRY FIXTURES =====

@pytest.fixture
def mock_agent_registry():
    """Mock agent registry."""
    registry = MagicMock()
    
    registry.register = Mock()
    registry.get = Mock(return_value=MagicMock())
    registry.list_agents = Mock(return_value=["agent1", "agent2"])
    
    return registry


# ===== TOOL FIXTURES =====

@pytest.fixture
def mock_tool_registry():
    """Mock tool registry."""
    registry = MagicMock()
    
    registry.get_tool = Mock(return_value={
        "name": "test_tool",
        "description": "A test tool",
        "parameters": {}
    })
    
    registry.list_tools = Mock(return_value=["tool1", "tool2"])
    
    return registry


# ===== FILE SYSTEM FIXTURES =====

@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary directory for test data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_json_file(temp_data_dir):
    """Sample JSON file for testing."""
    file_path = temp_data_dir / "sample.json"
    data = {"key": "value", "items": [1, 2, 3]}
    
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    return file_path


# ===== PHASE 5 FIXTURES =====

@pytest.fixture
def mock_hybrid_retriever():
    """Mock Phase 5 Hybrid Retriever."""
    mock = MagicMock()
    
    mock.retrieve = AsyncMock(return_value=[
        {
            "doc_id": "doc_0",
            "content": "Test content",
            "score": 0.95,
            "dense_score": 0.8,
            "sparse_score": 0.15,
        }
    ])
    
    mock.get_stats = Mock(return_value={
        "total_queries": 10,
        "avg_latency_ms": 3.5,
    })
    
    return mock


@pytest.fixture
def mock_bm25_retriever():
    """Mock BM25 Retriever."""
    mock = MagicMock()
    
    mock.search = Mock(return_value=[
        {"doc_id": "doc_0", "score": 0.85},
        {"doc_id": "doc_1", "score": 0.75},
    ])
    
    return mock


# ===== ASYNC HELPERS =====

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ===== ENVIRONMENT FIXTURES =====

@pytest.fixture
def test_env_vars(monkeypatch):
    """Set test environment variables."""
    monkeypatch.setenv("VERITAS_DEPLOYMENT_STAGE", "test")
    monkeypatch.setenv("VERITAS_ENABLE_HYBRID_SEARCH", "true")
    monkeypatch.setenv("VERITAS_ENABLE_QUERY_EXPANSION", "false")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
'''
        
        output_path = self.output_dir / "conftest.py"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_test_file(self, agent: Dict[str, Any]) -> Path:
        """Generate test file for a single agent."""
        agent_name = agent['name']
        class_name = agent.get('class_name', 'UnknownAgent')
        file_path = agent['file_path']
        domain = agent.get('domain', 'general')
        tools_used = agent.get('tools_used', [])
        methods = agent.get('methods', [])
        
        #  Fix import path for Windows/Linux
        import_path = file_path.replace("\\", ".").replace("/", ".").replace(".py", "")
        
        # Generate test content
        content = f'''"""
Tests for {agent_name} Agent

Agent: {class_name}
File: {file_path}
Domain: {domain}
Tools: {', '.join(tools_used) if tools_used else 'None'}

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

# Import agent
try:
    from {import_path} import {class_name or "Agent"}
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="Agent not importable yet")


class Test{class_name or "Agent"}:
    """Test suite for {class_name or agent_name}."""
    
    # ===== SETUP & TEARDOWN =====
    
    @pytest.fixture
    def agent_instance(self, mock_uds3_manager, mock_database):
        """Create agent instance for testing."""
        if not AGENT_AVAILABLE:
            pytest.skip("Agent not available")
        
        # TODO: Adjust constructor parameters based on actual agent
        agent = {class_name or "Agent"}(
            db_manager=mock_database,
            # Add other required parameters
        )
        return agent
    
    # ===== INITIALIZATION TESTS =====
    
    def test_agent_initialization(self, agent_instance):
        """Test agent can be initialized."""
        assert agent_instance is not None
        # TODO: Add specific initialization checks
    
    def test_agent_has_required_attributes(self, agent_instance):
        """Test agent has required attributes."""
        # TODO: Add attribute checks based on agent requirements
        pass
'''

        # Add method tests
        if methods:
            content += f'''
    
    # ===== METHOD TESTS =====
'''
            for method in methods[:5]:  # First 5 methods
                content += f'''
    
    @pytest.mark.asyncio
    async def test_{method}(self, agent_instance, sample_query, sample_context):
        """Test {method} method."""
        # TODO: Implement test for {method}
        
        # Example async call:
        # result = await agent_instance.{method}(sample_query, context=sample_context)
        # assert result is not None
        
        pytest.skip("Test not implemented yet")
'''
        
        # Add tool-specific tests
        if tools_used:
            content += f'''
    
    # ===== TOOL INTEGRATION TESTS =====
'''
            
            if "uds3" in tools_used:
                content += '''
    
    @pytest.mark.asyncio
    async def test_uds3_integration(self, agent_instance, mock_uds3_manager):
        """Test UDS3 database integration."""
        # TODO: Test UDS3 queries
        pytest.skip("Test not implemented yet")
'''
            
            if "database" in tools_used:
                content += '''
    
    @pytest.mark.asyncio
    async def test_database_queries(self, agent_instance, mock_database):
        """Test database query execution."""
        # TODO: Test database interactions
        pytest.skip("Test not implemented yet")
'''
            
            if "api_call" in tools_used:
                content += '''
    
    @pytest.mark.asyncio
    async def test_api_calls(self, agent_instance):
        """Test external API calls."""
        # TODO: Test API interactions (with mocking)
        pytest.skip("Test not implemented yet")
'''
            
            if "ollama" in tools_used or "llm" in tools_used:
                content += '''
    
    @pytest.mark.asyncio
    async def test_llm_integration(self, agent_instance, mock_ollama_client):
        """Test LLM integration."""
        # TODO: Test LLM calls
        pytest.skip("Test not implemented yet")
'''
        
        # Add domain-specific tests
        content += f'''
    
    # ===== DOMAIN-SPECIFIC TESTS ({domain.upper()}) =====
    
    @pytest.mark.asyncio
    async def test_{domain}_query(self, agent_instance):
        """Test {domain}-specific query processing."""
        # TODO: Add {domain} domain test
        pytest.skip("Test not implemented yet")
'''
        
        # Add error handling tests
        content += f'''
    
    # ===== ERROR HANDLING TESTS =====
    
    @pytest.mark.asyncio
    async def test_handles_empty_input(self, agent_instance):
        """Test agent handles empty input gracefully."""
        # TODO: Test error handling
        pytest.skip("Test not implemented yet")
    
    @pytest.mark.asyncio
    async def test_handles_invalid_parameters(self, agent_instance):
        """Test agent handles invalid parameters."""
        # TODO: Test error handling
        pytest.skip("Test not implemented yet")
    
    # ===== PERFORMANCE TESTS =====
    
    @pytest.mark.asyncio
    async def test_response_time(self, agent_instance, sample_query):
        """Test agent response time is acceptable."""
        # TODO: Add performance test
        pytest.skip("Test not implemented yet")


# ===== INTEGRATION TESTS =====

@pytest.mark.integration
class Test{class_name or "Agent"}Integration:
    """Integration tests for {class_name or agent_name}."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow from query to result."""
        # TODO: Implement end-to-end test
        pytest.skip("Test not implemented yet")


# ===== MIGRATION TESTS =====

@pytest.mark.migration
class Test{class_name or "Agent"}Migration:
    """Tests for framework migration."""
    
    def test_compatible_with_base_agent_interface(self):
        """Test agent is compatible with new BaseAgent interface."""
        # TODO: Test framework compatibility
        pytest.skip("Test not implemented yet")
    
    def test_tools_registered_in_registry(self):
        """Test agent tools are properly registered."""
        # TODO: Test tool registry integration
        pytest.skip("Test not implemented yet")
'''
        
        # Write file
        output_path = self.output_dir / f"test_{agent_name}.py"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path
    
    def _generate_readme(self):
        """Generate README with testing guide."""
        content = f'''# 🧪 Veritas Agent Tests

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This directory contains pytest test suites for all Veritas agents.

## 📊 Test Coverage Status

**Current Coverage:** {self.gap_data['summary']['test_coverage']['percentage']}%
**Agents with Tests:** {self.gap_data['summary']['test_coverage']['agents_with_tests']}/{self.gap_data['summary']['total_agents']}

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
        mock_get.return_value.json.return_value = {{"data": "test"}}
        
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

### 🔴 HIGH Priority ({len([a for a in self.gap_data['agents'] if a['migration_priority'] == 'HIGH'])} agents)

Must have tests before migration:

{self._generate_agent_list('HIGH')}

### 🟡 MEDIUM Priority ({len([a for a in self.gap_data['agents'] if a['migration_priority'] == 'MEDIUM'])} agents)

{self._generate_agent_list('MEDIUM')}

### 🟢 LOW Priority ({len([a for a in self.gap_data['agents'] if a['migration_priority'] == 'LOW'])} agents)

{self._generate_agent_list('LOW')}

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

**Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
'''
        
        output_path = self.output_dir / "README.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_agent_list(self, priority: str) -> str:
        """Generate markdown list of agents by priority."""
        agents = [a for a in self.gap_data['agents'] if a['migration_priority'] == priority]
        
        if not agents:
            return "- None\n"
        
        lines = []
        for agent in agents:
            lines.append(f"- `{agent['name']}` - {agent.get('domain', 'general')} ({agent['line_count']} LOC)")
        
        return "\n".join(lines) + "\n"


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    veritas_root = script_dir.parent
    
    gap_analysis_path = veritas_root / "reports" / "agent_gap_analysis.json"
    output_dir = veritas_root / "tests" / "agents"
    
    if not gap_analysis_path.exists():
        print(f"❌ Gap analysis not found: {gap_analysis_path}")
        print("Run: python scripts/analyze_agent_gap.py first")
        return
    
    print("🚀 Veritas Agent Test Template Generator")
    print(f"📁 Input: {gap_analysis_path}")
    print(f"📁 Output: {output_dir}")
    print()
    
    generator = TestTemplateGenerator(gap_analysis_path, output_dir)
    generator.generate_all()


if __name__ == "__main__":
    main()
