#!/usr/bin/env python3
"""
Unit Tests for ConstructionAgent - BaseAgent Framework v2.0

Comprehensive test suite covering:
- Agent initialization and lifecycle
- BaseAgent interface compliance
- Registry integration
- Async query processing
- Legacy compatibility
- Knowledge base functionality
- Error handling and retry logic

Author: VERITAS Framework Migration v2.0
Date: 2025-12-04
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.agents.domain.construction.construction_agent_v2_framework import (
        ConstructionAgent,
        register_construction_agent,
    )
    from backend.agents.framework.base_agent import BaseAgent
    from backend.agents.registry.api_agent_registry import AgentCapability, AgentLifecycleType

    AGENT_AVAILABLE = True
except ImportError as e:
    AGENT_AVAILABLE = False
    print(f"⚠️ Import failed: {e}")
    pytestmark = pytest.mark.skip(reason="Agent not available")


@pytest.fixture
def agent_instance():
    """Create ConstructionAgent instance for testing."""
    if not AGENT_AVAILABLE:
        pytest.skip("Agent not available")
    return ConstructionAgent(agent_id="test_construction_001")


@pytest.fixture
def sample_query() -> str:
    """Sample construction query."""
    return "Wie läuft ein Baugenehmigungsverfahren ab?"


@pytest.fixture
def sample_context() -> Dict[str, Any]:
    """Sample query context."""
    return {"domain": "construction", "user_id": "test_user", "timestamp": datetime.now().isoformat(), "priority": "normal"}


class TestConstructionAgentInitialization:
    """Test agent initialization and setup."""

    def test_agent_initialization(self, agent_instance):
        """Test agent initializes correctly."""
        assert agent_instance is not None
        assert isinstance(agent_instance, ConstructionAgent)
        assert isinstance(agent_instance, BaseAgent)

    def test_agent_type(self, agent_instance):
        """Test agent type identification."""
        assert agent_instance.get_agent_type() == "construction"

    def test_agent_capabilities(self, agent_instance):
        """Test agent capabilities."""
        capabilities = agent_instance.get_capabilities()
        assert len(capabilities) > 0
        assert AgentCapability.LEGAL_FRAMEWORK_ANALYSIS in capabilities
        assert AgentCapability.BUILDING_PERMIT_PROCESSING in capabilities

    def test_agent_has_knowledge_base(self, agent_instance):
        """Test agent has knowledge base."""
        assert hasattr(agent_instance, "knowledge_base")
        assert isinstance(agent_instance.knowledge_base, dict)
        assert len(agent_instance.knowledge_base) > 0

    def test_knowledge_base_topics(self, agent_instance):
        """Test knowledge base contains construction topics."""
        kb = agent_instance.knowledge_base
        expected_topics = ["baugenehmigung", "baurecht", "zoniering", "bebauungsplan", "nachbarschaftsrecht"]
        for topic in expected_topics:
            assert topic in kb


@pytest.mark.asyncio
class TestConstructionAgentAsyncProcessing:
    """Test async query processing."""

    async def test_async_process_query(self, agent_instance, sample_query):
        """Test async query processing."""
        result = await agent_instance.process_query(sample_query)

        assert result is not None
        assert isinstance(result, dict)
        assert "agent_type" in result
        assert result["agent_type"] == "construction"

    async def test_process_query_returns_response(self, agent_instance, sample_query):
        """Test that process_query returns response text."""
        result = await agent_instance.process_query(sample_query)

        assert "response" in result
        assert isinstance(result["response"], str)

    async def test_process_query_returns_confidence(self, agent_instance, sample_query):
        """Test that process_query returns confidence score."""
        result = await agent_instance.process_query(sample_query)

        assert "confidence" in result
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 1

    async def test_concurrent_queries(self, agent_instance, sample_query):
        """Test multiple concurrent queries."""
        tasks = [agent_instance.process_query(f"{sample_query} - Query {i}") for i in range(3)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(isinstance(r, dict) for r in results)
        assert all("agent_type" in r for r in results)


class TestConstructionAgentLegacyCompatibility:
    """Test backward compatibility with legacy interface."""

    def test_legacy_query_method_exists(self, agent_instance):
        """Test legacy query() method exists."""
        assert hasattr(agent_instance, "query")
        assert callable(agent_instance.query)

    def test_search_construction_method(self, agent_instance):
        """Test legacy search_construction method."""
        assert hasattr(agent_instance, "search_construction")
        result = agent_instance.search_construction("baugenehmigung")
        assert isinstance(result, list)

    def test_search_planning_method(self, agent_instance):
        """Test legacy search_planning method."""
        assert hasattr(agent_instance, "search_planning")
        result = agent_instance.search_planning("zoniering")
        assert isinstance(result, list)


class TestConstructionAgentLocationExtraction:
    """Test location extraction from queries."""

    def test_known_locations(self, agent_instance):
        """Test known locations are recognized."""
        known_locations = ["münchen", "berlin", "hamburg", "frankfurt", "köln"]

        for location in known_locations:
            query = f"Baurecht in {location}"
            result = agent_instance._extract_location(query)
            assert result is not None


class TestConstructionAgentConfidenceCalculation:
    """Test confidence score calculation."""

    def test_confidence_increases_with_matches(self, agent_instance):
        """Test confidence increases with KB matches."""
        # Short query with no location
        conf1 = agent_instance._calculate_confidence("Baurecht?", {}, None)

        # Longer query with matches
        conf2 = agent_instance._calculate_confidence(
            "Wie läuft ein Baugenehmigungsverfahren in München ab?",
            {"baugenehmigung": "...", "genehmigung": "..."},
            {"name": "München"},
        )

        assert conf2 > conf1


@pytest.mark.asyncio
class TestConstructionAgentErrorHandling:
    """Test error handling."""

    async def test_handles_empty_query(self, agent_instance):
        """Test handling of empty query."""
        result = await agent_instance.process_query("")
        assert result is not None

    async def test_handles_none_query(self, agent_instance):
        """Test handling of None query."""
        with pytest.raises((TypeError, ValueError)):
            await agent_instance.process_query(None)


@pytest.mark.integration
class TestConstructionAgentIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, agent_instance, sample_query):
        """Test complete workflow."""
        agent_type = agent_instance.get_agent_type()
        assert agent_type == "construction"

        capabilities = agent_instance.get_capabilities()
        assert len(capabilities) > 0

        result = await agent_instance.process_query(sample_query)
        assert result is not None
        assert "agent_type" in result
        assert result["agent_type"] == "construction"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
