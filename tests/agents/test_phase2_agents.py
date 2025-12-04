"""
Unit Tests for Phase 2 Agents - BaseAgent v2.0 Framework

Tests:
1. NaturschutzAgent
2. BodenGewaesserschutzAgent
3. EmissionenMonitoringAgent
4. ImmissionsschutzAgent
5. BrightSkyWeatherAgent

Author: VERITAS Framework Migration v2.0
Date: 2025-12-04
"""

import asyncio
from datetime import datetime

import pytest

from backend.agents.domain.environmental.boden_gewaesserschutz_agent_v2_framework import BodenGewaesserschutzAgent
from backend.agents.domain.environmental.emissionen_monitoring_agent_v2_framework import EmissionenMonitoringAgent

# Phase 2 Agents
from backend.agents.domain.environmental.naturschutz_agent_v2_framework import NaturschutzAgent
from backend.agents.domain.immissionsschutz.immissionsschutz_agent_v2_framework import ImmissionsschutzAgent
from backend.agents.domain.weather.brightsky_weather_agent_v2_framework import BrightSkyWeatherAgent

# Framework
from backend.agents.registry.api_agent_registry import AgentCapability

# =========================================================================
# 1. NaturschutzAgent Tests
# =========================================================================


class TestNaturschutzAgent:
    """Tests for NaturschutzAgent v2.0"""

    def test_initialization(self):
        """Test agent initialization"""
        agent = NaturschutzAgent()
        assert agent.AGENT_TYPE == "naturschutz"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.get_capabilities()) > 0

    def test_get_agent_type(self):
        """Test get_agent_type method"""
        agent = NaturschutzAgent()
        assert agent.get_agent_type() == "naturschutz"

    def test_get_capabilities(self):
        """Test get_capabilities method"""
        agent = NaturschutzAgent()
        caps = agent.get_capabilities()
        assert AgentCapability.QUERY_PROCESSING in caps
        assert AgentCapability.ENVIRONMENTAL_DATA_PROCESSING in caps

    @pytest.mark.asyncio
    async def test_process_query_naturschutz(self):
        """Test naturschutz query"""
        agent = NaturschutzAgent()
        result = await agent.process_query("naturschutz")
        assert result["success"] is True
        assert result["confidence"] > 0.5
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_process_query_artenschutz(self):
        """Test artenschutz query"""
        agent = NaturschutzAgent()
        result = await agent.process_query("artenschutz")
        assert result["success"] is True
        assert "results" in result

    def test_legacy_query_method(self):
        """Test legacy query() method compatibility"""
        agent = NaturschutzAgent()
        result = agent.query("FFH Richtlinie")
        assert result["success"] is True

    def test_get_info(self):
        """Test get_info method"""
        agent = NaturschutzAgent()
        info = agent.get_info()
        assert info["name"] == "NaturschutzAgent"
        assert info["version"] == "2.0"


# =========================================================================
# 2. BodenGewaesserschutzAgent Tests
# =========================================================================


class TestBodenGewaesserschutzAgent:
    """Tests for BodenGewaesserschutzAgent v2.0"""

    def test_initialization(self):
        """Test agent initialization"""
        agent = BodenGewaesserschutzAgent()
        assert agent.AGENT_TYPE == "boden_gewaesserschutz"
        assert agent.AGENT_VERSION == "2.0"

    @pytest.mark.asyncio
    async def test_process_query_bodenschutz(self):
        """Test bodenschutz query"""
        agent = BodenGewaesserschutzAgent()
        result = await agent.process_query("bodenschutz")
        assert result["success"] is True
        assert result["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_process_query_grundwasser(self):
        """Test grundwasser query"""
        agent = BodenGewaesserschutzAgent()
        result = await agent.process_query("grundwasser")
        assert result["success"] is True

    def test_get_capabilities(self):
        """Test get_capabilities method"""
        agent = BodenGewaesserschutzAgent()
        caps = agent.get_capabilities()
        assert AgentCapability.ENVIRONMENTAL_DATA_PROCESSING in caps

    def test_legacy_methods(self):
        """Test legacy compatibility methods"""
        agent = BodenGewaesserschutzAgent()
        result = agent.search_bodenschutz("BBodSchG")
        assert isinstance(result, list)


# =========================================================================
# 3. EmissionenMonitoringAgent Tests
# =========================================================================


class TestEmissionenMonitoringAgent:
    """Tests for EmissionenMonitoringAgent v2.0"""

    def test_initialization(self):
        """Test agent initialization"""
        agent = EmissionenMonitoringAgent()
        assert agent.AGENT_TYPE == "emissionen_monitoring"
        assert agent.AGENT_VERSION == "2.0"

    @pytest.mark.asyncio
    async def test_process_query_emissionsmessung(self):
        """Test emissionsmessung query"""
        agent = EmissionenMonitoringAgent()
        result = await agent.process_query("emissionsmessung")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_process_query_grenzwert(self):
        """Test grenzwertüberschreitung query"""
        agent = EmissionenMonitoringAgent()
        result = await agent.process_query("grenzwertüberschreitung")
        assert result["success"] is True

    def test_get_capabilities(self):
        """Test get_capabilities method"""
        agent = EmissionenMonitoringAgent()
        caps = agent.get_capabilities()
        assert AgentCapability.REAL_TIME_PROCESSING in caps


# =========================================================================
# 4. ImmissionsschutzAgent Tests
# =========================================================================


class TestImmissionsschutzAgent:
    """Tests for ImmissionsschutzAgent v2.0"""

    def test_initialization(self):
        """Test agent initialization"""
        agent = ImmissionsschutzAgent()
        assert agent.AGENT_TYPE == "immissionsschutz"
        assert agent.AGENT_VERSION == "2.0"

    @pytest.mark.asyncio
    async def test_process_query_no2(self):
        """Test NO2 query"""
        agent = ImmissionsschutzAgent()
        result = await agent.process_query("NO2 Grenzwerte")
        assert result["success"] is True
        assert result["confidence"] > 0.8

    @pytest.mark.asyncio
    async def test_process_query_laerm(self):
        """Test Lärmschutz query"""
        agent = ImmissionsschutzAgent()
        result = await agent.process_query("Lärmgrenzwerte Wohngebiet")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_process_query_ta_luft(self):
        """Test TA Luft query"""
        agent = ImmissionsschutzAgent()
        result = await agent.process_query("TA Luft")
        assert result["success"] is True
        assert result["confidence"] > 0.8

    def test_get_luftqualitaet_grenzwerte(self):
        """Test get_luftqualitaet_grenzwerte method"""
        agent = ImmissionsschutzAgent()
        grenzwerte = agent.get_luftqualitaet_grenzwerte("NO2")
        assert "jahresgrenzwert" in grenzwerte
        assert "40 µg/m³" in grenzwerte["jahresgrenzwert"]

    def test_get_laermschutz_grenzwerte(self):
        """Test get_laermschutz_grenzwerte method"""
        agent = ImmissionsschutzAgent()
        grenzwerte = agent.get_laermschutz_grenzwerte("Wohngebiet")
        assert "tag" in grenzwerte
        assert "55 dB(A)" in grenzwerte["tag"]


# =========================================================================
# 5. BrightSkyWeatherAgent Tests
# =========================================================================


class TestBrightSkyWeatherAgent:
    """Tests for BrightSkyWeatherAgent v2.0"""

    def test_initialization(self):
        """Test agent initialization"""
        agent = BrightSkyWeatherAgent()
        assert agent.AGENT_TYPE == "brightsky_weather"
        assert agent.AGENT_VERSION == "2.0"

    def test_get_capabilities(self):
        """Test get_capabilities method"""
        agent = BrightSkyWeatherAgent()
        caps = agent.get_capabilities()
        assert AgentCapability.WEATHER_DATA in caps
        assert AgentCapability.EXTERNAL_API in caps

    @pytest.mark.asyncio
    async def test_process_query(self):
        """Test weather query processing"""
        agent = BrightSkyWeatherAgent()
        result = await agent.process_query("Wetter München")
        # Note: May fail if API unavailable
        assert "success" in result
        assert "confidence" in result

    def test_get_current_weather(self):
        """Test get_current_weather method"""
        agent = BrightSkyWeatherAgent()
        result = agent.get_current_weather(48.1351, 11.5820)
        # Note: May fail if API unavailable
        assert "success" in result

    def test_get_info(self):
        """Test get_info method"""
        agent = BrightSkyWeatherAgent()
        info = agent.get_info()
        assert info["name"] == "BrightSkyWeatherAgent"
        assert info["version"] == "2.0"
        assert "api_available" in info


# =========================================================================
# Integration Tests
# =========================================================================


class TestPhase2Integration:
    """Integration tests for all Phase 2 agents"""

    def test_all_agents_initialize(self):
        """Test that all agents can be initialized"""
        agents = [
            NaturschutzAgent(),
            BodenGewaesserschutzAgent(),
            EmissionenMonitoringAgent(),
            ImmissionsschutzAgent(),
            BrightSkyWeatherAgent(),
        ]
        assert len(agents) == 5
        for agent in agents:
            assert agent.AGENT_VERSION == "2.0"

    def test_all_agents_have_capabilities(self):
        """Test that all agents have capabilities defined"""
        agents = [
            NaturschutzAgent(),
            BodenGewaesserschutzAgent(),
            EmissionenMonitoringAgent(),
            ImmissionsschutzAgent(),
            BrightSkyWeatherAgent(),
        ]
        for agent in agents:
            caps = agent.get_capabilities()
            assert len(caps) > 0
            assert AgentCapability.QUERY_PROCESSING in caps

    @pytest.mark.asyncio
    async def test_all_agents_process_query(self):
        """Test that all agents can process queries"""
        test_queries = {
            "naturschutz": NaturschutzAgent(),
            "bodenschutz": BodenGewaesserschutzAgent(),
            "emissionen": EmissionenMonitoringAgent(),
            "NO2": ImmissionsschutzAgent(),
            "wetter": BrightSkyWeatherAgent(),
        }

        for query, agent in test_queries.items():
            result = await agent.process_query(query)
            assert "success" in result
            assert "confidence" in result
            assert "agent" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
