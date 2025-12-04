"""
VERITAS Phase 3 Agent Direct Tests - Ohne Registry

Tests prüfen die direkten Agent-Implementierungen ohne Registry-Dependencies.
Dies validiert die BaseAgent v2.0 Migration unabhängig von Registry-Komplexität.

Author: VERITAS Test Suite
Date: 2025-12-04
Version: 2.0 (Direct Tests)
"""

import asyncio
import os
import sys

import pytest

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestSocialAgentDirect:
    """Direct tests for SocialAgent v2.0"""

    def test_social_agent_import(self):
        """Test SocialAgent can be imported"""
        from backend.agents.domain.social.social_agent_v2_framework import SocialAgent

        assert SocialAgent is not None
        assert hasattr(SocialAgent, "AGENT_TYPE")

    def test_social_agent_initialization(self):
        """Test SocialAgent initialization"""
        from backend.agents.domain.social.social_agent_v2_framework import SocialAgent

        agent = SocialAgent()
        assert agent.AGENT_TYPE == "social"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) > 0

    @pytest.mark.asyncio
    async def test_social_agent_async_query(self):
        """Test SocialAgent async query"""
        from backend.agents.domain.social.social_agent_v2_framework import SocialAgent

        agent = SocialAgent()
        result = await agent.process_query("Kindergeld Bedingungen")
        assert result is not None
        assert isinstance(result, dict)


class TestFinancialAgentDirect:
    """Direct tests for FinancialAgent v2.0"""

    def test_financial_agent_import(self):
        """Test FinancialAgent can be imported"""
        from backend.agents.domain.financial.financial_agent_v2_framework import FinancialAgent

        assert FinancialAgent is not None

    def test_financial_agent_initialization(self):
        """Test FinancialAgent initialization"""
        from backend.agents.domain.financial.financial_agent_v2_framework import FinancialAgent

        agent = FinancialAgent()
        assert agent.AGENT_TYPE == "financial"
        assert len(agent.knowledge_base) > 0

    @pytest.mark.asyncio
    async def test_financial_agent_async_query(self):
        """Test FinancialAgent async query"""
        from backend.agents.domain.financial.financial_agent_v2_framework import FinancialAgent

        agent = FinancialAgent()
        result = await agent.process_query("Grundsteuer Berlin")
        assert result is not None


class TestTechnicalStandardsAgentDirect:
    """Direct tests for TechnicalStandardsAgent v2.0"""

    def test_technical_standards_agent_import(self):
        """Test TechnicalStandardsAgent can be imported"""
        from backend.agents.domain.standards.technical_standards_agent_v2_framework import TechnicalStandardsAgent

        assert TechnicalStandardsAgent is not None

    def test_technical_standards_agent_initialization(self):
        """Test TechnicalStandardsAgent initialization"""
        from backend.agents.domain.standards.technical_standards_agent_v2_framework import TechnicalStandardsAgent

        agent = TechnicalStandardsAgent()
        assert agent.AGENT_TYPE == "technical_standards"
        assert len(agent.knowledge_base) > 0


class TestChemicalDataAgentDirect:
    """Direct tests for ChemicalDataAgent v2.0"""

    def test_chemical_data_agent_import(self):
        """Test ChemicalDataAgent can be imported"""
        from backend.agents.domain.chemical.chemical_data_agent_v2_framework import ChemicalDataAgent

        assert ChemicalDataAgent is not None

    def test_chemical_data_agent_initialization(self):
        """Test ChemicalDataAgent initialization"""
        from backend.agents.domain.chemical.chemical_data_agent_v2_framework import ChemicalDataAgent

        agent = ChemicalDataAgent()
        assert agent.AGENT_TYPE == "chemical_data"
        assert len(agent.knowledge_base) >= 5  # 5 chemicals


class TestWikipediaAgentDirect:
    """Direct tests for WikipediaAgent v2.0"""

    def test_wikipedia_agent_import(self):
        """Test WikipediaAgent can be imported"""
        from backend.agents.domain.wikipedia.wikipedia_agent_v2_framework import WikipediaAgent

        assert WikipediaAgent is not None

    def test_wikipedia_agent_initialization(self):
        """Test WikipediaAgent initialization"""
        from backend.agents.domain.wikipedia.wikipedia_agent_v2_framework import WikipediaAgent

        agent = WikipediaAgent()
        assert agent.AGENT_TYPE == "wikipedia"
        assert len(agent.knowledge_base) >= 6  # 6 articles


class TestTrafficAgentDirect:
    """Direct tests for TrafficAgent v2.0"""

    def test_traffic_agent_import(self):
        """Test TrafficAgent can be imported"""
        from backend.agents.domain.traffic.traffic_agent_v2_framework import TrafficAgent

        assert TrafficAgent is not None

    def test_traffic_agent_initialization(self):
        """Test TrafficAgent initialization"""
        from backend.agents.domain.traffic.traffic_agent_v2_framework import TrafficAgent

        agent = TrafficAgent()
        assert agent.AGENT_TYPE == "traffic"
        assert len(agent.knowledge_base) >= 3  # München, Berlin, Hamburg


class TestDatabaseAgentDirect:
    """Direct tests for DatabaseAgent v2.0"""

    def test_database_agent_import(self):
        """Test DatabaseAgent can be imported"""
        from backend.agents.domain.database.database_agent_v2_framework import DatabaseAgent

        assert DatabaseAgent is not None

    def test_database_agent_initialization(self):
        """Test DatabaseAgent initialization"""
        from backend.agents.domain.database.database_agent_v2_framework import DatabaseAgent

        agent = DatabaseAgent()
        assert agent.AGENT_TYPE == "database"
        assert agent.AGENT_VERSION == "2.0"


class TestVerwaltungsrechtAgentDirect:
    """Direct tests for VerwaltungsrechtAgent v2.0"""

    def test_verwaltungsrecht_agent_import(self):
        """Test VerwaltungsrechtAgent can be imported"""
        from backend.agents.domain.social.verwaltungsrecht_agent_v2_framework import VerwaltungsrechtAgent

        assert VerwaltungsrechtAgent is not None

    def test_verwaltungsrecht_agent_initialization(self):
        """Test VerwaltungsrechtAgent initialization"""
        from backend.agents.domain.social.verwaltungsrecht_agent_v2_framework import VerwaltungsrechtAgent

        agent = VerwaltungsrechtAgent()
        assert agent.AGENT_TYPE == "verwaltungsrecht"


class TestRechtsrechercheAgentDirect:
    """Direct tests for RechtsrechercheAgent v2.0"""

    def test_rechtsrecherche_agent_import(self):
        """Test RechtsrechercheAgent can be imported"""
        from backend.agents.domain.social.rechtsrecherche_agent_v2_framework import RechtsrechercheAgent

        assert RechtsrechercheAgent is not None

    def test_rechtsrecherche_agent_initialization(self):
        """Test RechtsrechercheAgent initialization"""
        from backend.agents.domain.social.rechtsrecherche_agent_v2_framework import RechtsrechercheAgent

        agent = RechtsrechercheAgent()
        assert agent.AGENT_TYPE == "rechtsrecherche"


class TestVerwaltungsprozessAgentDirect:
    """Direct tests for VerwaltungsprozessAgent v2.0"""

    def test_verwaltungsprozess_agent_import(self):
        """Test VerwaltungsprozessAgent can be imported"""
        from backend.agents.domain.social.verwaltungsprozess_agent_v2_framework import VerwaltungsprozessAgent

        assert VerwaltungsprozessAgent is not None

    def test_verwaltungsprozess_agent_initialization(self):
        """Test VerwaltungsprozessAgent initialization"""
        from backend.agents.domain.social.verwaltungsprozess_agent_v2_framework import VerwaltungsprozessAgent

        agent = VerwaltungsprozessAgent()
        assert agent.AGENT_TYPE == "verwaltungsprozess"


def test_all_agents_have_base_methods():
    """Verify all Phase 3 agents have BaseAgent methods"""
    from backend.agents.domain.chemical.chemical_data_agent_v2_framework import ChemicalDataAgent
    from backend.agents.domain.database.database_agent_v2_framework import DatabaseAgent
    from backend.agents.domain.financial.financial_agent_v2_framework import FinancialAgent
    from backend.agents.domain.social.rechtsrecherche_agent_v2_framework import RechtsrechercheAgent
    from backend.agents.domain.social.social_agent_v2_framework import SocialAgent
    from backend.agents.domain.social.verwaltungsprozess_agent_v2_framework import VerwaltungsprozessAgent
    from backend.agents.domain.social.verwaltungsrecht_agent_v2_framework import VerwaltungsrechtAgent
    from backend.agents.domain.standards.technical_standards_agent_v2_framework import TechnicalStandardsAgent
    from backend.agents.domain.traffic.traffic_agent_v2_framework import TrafficAgent
    from backend.agents.domain.wikipedia.wikipedia_agent_v2_framework import WikipediaAgent

    agents = [
        SocialAgent(),
        FinancialAgent(),
        TechnicalStandardsAgent(),
        ChemicalDataAgent(),
        WikipediaAgent(),
        TrafficAgent(),
        DatabaseAgent(),
        VerwaltungsrechtAgent(),
        RechtsrechercheAgent(),
        VerwaltungsprozessAgent(),
    ]

    required_methods = ["execute_step", "get_agent_type", "get_capabilities", "process_query", "query"]

    for agent in agents:
        for method in required_methods:
            assert hasattr(agent, method), f"{agent.__class__.__name__} missing {method}"

    print(f"✅ All 10 agents have required BaseAgent methods!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
