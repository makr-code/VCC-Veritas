"""
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
