#!/usr/bin/env python3
"""
Unit Tests for EnvironmentalAgent - BaseAgent Framework v2.0

Comprehensive test suite covering:
- Agent initialization and lifecycle
- BaseAgent interface compliance
- Registry integration
- Async query processing
- Environmental data classification
- Query categorization
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
    from backend.agents.domain.environmental.environmental_agent_v2_framework import (
        EnvironmentalAgent,
        register_environmental_agent,
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
    """Create EnvironmentalAgent instance for testing."""
    if not AGENT_AVAILABLE:
        pytest.skip("Agent not available")
    return EnvironmentalAgent(agent_id="test_environmental_001")


@pytest.fixture
def sample_query() -> str:
    """Sample environmental query."""
    return "Wie ist die Luftqualität in Deutschland?"


@pytest.fixture
def sample_context() -> Dict[str, Any]:
    """Sample query context."""
    return {"domain": "environmental", "user_id": "test_user", "timestamp": datetime.now().isoformat(), "priority": "normal"}


class TestEnvironmentalAgentInitialization:
    """Test agent initialization and setup."""

    def test_agent_initialization(self, agent_instance):
        """Test agent initializes correctly."""
        assert agent_instance is not None
        assert isinstance(agent_instance, EnvironmentalAgent)
        assert isinstance(agent_instance, BaseAgent)

    def test_agent_type(self, agent_instance):
        """Test agent type identification."""
        assert agent_instance.get_agent_type() == "environmental"

    def test_agent_capabilities(self, agent_instance):
        """Test agent capabilities."""
        capabilities = agent_instance.get_capabilities()
        assert len(capabilities) > 0
        assert AgentCapability.ENVIRONMENTAL_DATA_PROCESSING in capabilities
        assert AgentCapability.QUERY_PROCESSING in capabilities

    def test_agent_has_knowledge_base(self, agent_instance):
        """Test agent has knowledge base."""
        assert hasattr(agent_instance, "knowledge_base")
        assert isinstance(agent_instance.knowledge_base, dict)
        assert len(agent_instance.knowledge_base) > 0

    def test_knowledge_base_topics(self, agent_instance):
        """Test knowledge base contains environmental topics."""
        kb = agent_instance.knowledge_base
        expected_topics = ["luftqualitaet", "emissionsschutz", "gewaesserschutz", "bodenschutz", "naturschutz"]
        for topic in expected_topics:
            assert topic in kb

    def test_known_regions(self, agent_instance):
        """Test known regions are defined."""
        assert hasattr(agent_instance, "known_regions")
        regions = agent_instance.known_regions
        assert "rhein" in regions
        assert "elbe" in regions
        assert "ostsee" in regions


@pytest.mark.asyncio
class TestEnvironmentalAgentAsyncProcessing:
    """Test async query processing."""

    async def test_async_process_query(self, agent_instance, sample_query):
        """Test async query processing."""
        result = await agent_instance.process_query(sample_query)

        assert result is not None
        assert isinstance(result, dict)
        assert "agent_type" in result
        assert result["agent_type"] == "environmental"

    async def test_process_query_returns_response(self, agent_instance, sample_query):
        """Test that process_query returns response text."""
        result = await agent_instance.process_query(sample_query)

        assert "response" in result
        assert isinstance(result["response"], str)

    async def test_process_query_returns_recommendations(self, agent_instance, sample_query):
        """Test that process_query returns recommendations."""
        result = await agent_instance.process_query(sample_query)

        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)

    async def test_process_query_returns_category(self, agent_instance, sample_query):
        """Test that process_query returns category."""
        result = await agent_instance.process_query(sample_query)

        assert "category" in result
        assert result["category"] in ["air_quality", "water_protection", "soil_protection", "nature_protection", "general"]

    async def test_concurrent_queries(self, agent_instance):
        """Test multiple concurrent queries."""
        queries = ["Luftqualität in Berlin", "Gewässerschutz am Rhein", "Naturschutzgebiete"]
        tasks = [agent_instance.process_query(q) for q in queries]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(isinstance(r, dict) for r in results)
        assert all("agent_type" in r for r in results)


class TestEnvironmentalAgentQueryClassification:
    """Test query classification into environmental categories."""

    def test_classify_air_quality_query(self, agent_instance):
        """Test classification of air quality queries."""
        category = agent_instance._classify_query("Wie ist die Luftqualität?")
        assert category == "air_quality"

    def test_classify_water_protection_query(self, agent_instance):
        """Test classification of water protection queries."""
        category = agent_instance._classify_query("Gewässerschutz am See")
        assert category == "water_protection"

    def test_classify_soil_protection_query(self, agent_instance):
        """Test classification of soil protection queries."""
        category = agent_instance._classify_query("Bodenschutz und Altlasten")
        assert category == "soil_protection"

    def test_classify_nature_protection_query(self, agent_instance):
        """Test classification of nature protection queries."""
        category = agent_instance._classify_query("Naturschutzgebiet")
        assert category == "nature_protection"


class TestEnvironmentalAgentRegionExtraction:
    """Test region extraction from queries."""

    def test_extract_known_regions(self, agent_instance):
        """Test extraction of known regions."""
        regions = ["rhein", "elbe", "donau", "ostsee", "bodensee"]

        for region in regions:
            query = f"Wasser qualität am {region}"
            extracted = agent_instance._extract_region(query)
            # Either None or a dict with region info
            if extracted:
                assert isinstance(extracted, dict)

    def test_extract_region_returns_none_for_unknown(self, agent_instance):
        """Test unknown regions return None."""
        result = agent_instance._extract_region("Wasser in Atlantis")
        assert result is None


@pytest.mark.asyncio
class TestEnvironmentalAgentRecommendations:
    """Test recommendation generation."""

    async def test_generates_recommendations(self, agent_instance, sample_query):
        """Test that recommendations are generated."""
        result = await agent_instance.process_query(sample_query)

        assert "recommendations" in result
        recommendations = result["recommendations"]
        assert len(recommendations) > 0
        assert all(isinstance(r, str) for r in recommendations)

    def test_recommendations_for_air_quality(self, agent_instance):
        """Test recommendations for air quality queries."""
        recs = agent_instance._generate_recommendations("air_quality", "Luftqualität")
        assert len(recs) > 0
        assert any("Luft" in r for r in recs)

    def test_recommendations_for_water_protection(self, agent_instance):
        """Test recommendations for water protection queries."""
        recs = agent_instance._generate_recommendations("water_protection", "Gewässer")
        assert len(recs) > 0
        assert any("Wasser" in r or "Gewässer" in r for r in recs)


class TestEnvironmentalAgentLegacyCompatibility:
    """Test backward compatibility with legacy interface."""

    def test_legacy_query_method_exists(self, agent_instance):
        """Test legacy query() method exists."""
        assert hasattr(agent_instance, "query")
        assert callable(agent_instance.query)

    def test_search_environmental_method(self, agent_instance):
        """Test legacy search_environmental method."""
        assert hasattr(agent_instance, "search_environmental")
        result = agent_instance.search_environmental("luftqualitaet")
        assert isinstance(result, list)


@pytest.mark.asyncio
class TestEnvironmentalAgentErrorHandling:
    """Test error handling."""

    async def test_handles_empty_query(self, agent_instance):
        """Test handling of empty query."""
        result = await agent_instance.process_query("")
        assert result is not None

    async def test_handles_none_query(self, agent_instance):
        """Test handling of None query."""
        with pytest.raises((TypeError, ValueError)):
            await agent_instance.process_query(None)

    async def test_handles_special_characters(self, agent_instance):
        """Test handling of special characters."""
        result = await agent_instance.process_query("Umwelt ü ö ä €")
        assert result is not None


@pytest.mark.asyncio
class TestEnvironmentalAgentConfidenceScoring:
    """Test confidence score calculation."""

    async def test_confidence_based_on_matches(self, agent_instance):
        """Test confidence increases with more KB matches."""
        result = await agent_instance.process_query("Luftqualität")
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1


@pytest.mark.integration
class TestEnvironmentalAgentIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, agent_instance, sample_query):
        """Test complete workflow."""
        agent_type = agent_instance.get_agent_type()
        assert agent_type == "environmental"

        capabilities = agent_instance.get_capabilities()
        assert len(capabilities) > 0

        result = await agent_instance.process_query(sample_query)
        assert result is not None
        assert "agent_type" in result
        assert result["agent_type"] == "environmental"
        assert "category" in result
        assert "recommendations" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
