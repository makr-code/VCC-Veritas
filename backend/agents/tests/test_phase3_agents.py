"""
VERITAS Phase 3 Agent Tests - Standalone Version

Umfassende Test-Suite für alle 10 Phase 3 Agents (ohne Registry-Dependencies).

Test Coverage:
✅ Agent initialization (basic)
✅ Query processing
✅ Knowledge base searches
✅ Legacy compatibility
✅ Error handling

Author: VERITAS Test Suite
Date: 2025-12-04
Version: 2.0
"""

import os
import sys

import pytest

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)


# =============================================================================
# SOCIAL AGENT TESTS (5 tests)
# =============================================================================


class TestSocialAgent:
    """Test suite for SocialAgent"""

    def test_social_agent_initialization(self):
        """Test 1: Agent initializes correctly"""
        from backend.agents.domain.social.social_agent_v2_framework import SocialAgent

        agent = SocialAgent()
        assert agent.AGENT_TYPE == "social"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 6

    def test_social_agent_kindergeld_query(self):
        """Test 2: Kindergeld query"""
        from backend.agents.domain.social.social_agent_v2_framework import SocialAgent

        agent = SocialAgent()
        result = agent.query("Ich habe 2 Kinder, bekomme ich Kindergeld?")
        assert result["success"] is True
        assert len(result["benefits"]) > 0
        assert result["confidence"] >= 0.6

    def test_social_agent_buergergeld_query(self):
        """Test 3: Bürgergeld query"""
        from backend.agents.domain.social.social_agent_v2_framework import SocialAgent

        agent = SocialAgent()
        result = agent.query("Ich bin arbeitslos, brauche Bürgergeld")
        assert result["success"] is True
        assert any("bürgergeld" in str(b).lower() for b in result["benefits"])

    def test_social_agent_wohngeld_query(self):
        """Test 4: Wohngeld query"""
        from backend.agents.domain.social.social_agent_v2_framework import SocialAgent

        agent = SocialAgent()
        result = agent.query("Kann ich Wohngeld beantragen?")
        assert result["success"] is True
        assert result["confidence"] >= 0.5

    def test_social_agent_get_info(self):
        """Test 5: Get agent info"""
        from backend.agents.domain.social.social_agent_v2_framework import SocialAgent

        agent = SocialAgent()
        info = agent.get_info()
        assert info["name"] == "SocialAgent"
        assert info["domain"] == "SOCIAL_SERVICES"
        assert info["version"] == "2.0"


# =============================================================================
# FINANCIAL AGENT TESTS (5 tests)
# =============================================================================


class TestFinancialAgent:
    """Test suite for FinancialAgent"""

    def test_financial_agent_initialization(self):
        """Test 6: Agent initializes correctly"""
        from backend.agents.domain.financial.financial_agent_v2_framework import FinancialAgent

        agent = FinancialAgent()
        assert agent.AGENT_TYPE == "financial"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 5

    def test_financial_agent_grundsteuer_query(self):
        """Test 7: Grundsteuer query"""
        from backend.agents.domain.financial.financial_agent_v2_framework import FinancialAgent

        agent = FinancialAgent()
        result = agent.query("Was ist die Grundsteuer in München?")
        assert result["success"] is True
        assert len(result["taxes"]) > 0

    def test_financial_agent_einkommensteuer_query(self):
        """Test 8: Einkommensteuer query"""
        from backend.agents.domain.financial.financial_agent_v2_framework import FinancialAgent

        agent = FinancialAgent()
        result = agent.query("Wie hoch ist die Einkommensteuer?")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_financial_agent_gewerbesteuer_query(self):
        """Test 9: Gewerbesteuer query"""
        from backend.agents.domain.financial.financial_agent_v2_framework import FinancialAgent

        agent = FinancialAgent()
        result = agent.query("Gewerbesteuer für Unternehmen in Berlin")
        assert result["success"] is True

    def test_financial_agent_get_info(self):
        """Test 10: Get agent info"""
        from backend.agents.domain.financial.financial_agent_v2_framework import FinancialAgent

        agent = FinancialAgent()
        info = agent.get_info()
        assert info["name"] == "FinancialAgent"
        assert info["domain"] == "FINANCIAL"


# =============================================================================
# TECHNICAL STANDARDS AGENT TESTS (5 tests)
# =============================================================================


class TestTechnicalStandardsAgent:
    """Test suite for TechnicalStandardsAgent"""

    def test_standards_agent_initialization(self):
        """Test 11: Agent initializes correctly"""
        from backend.agents.domain.standards.technical_standards_agent_v2_framework import TechnicalStandardsAgent

        agent = TechnicalStandardsAgent()
        assert agent.AGENT_TYPE == "technical_standards"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 4

    def test_standards_agent_iso_9001_query(self):
        """Test 12: ISO 9001 query"""
        from backend.agents.domain.standards.technical_standards_agent_v2_framework import TechnicalStandardsAgent

        agent = TechnicalStandardsAgent()
        result = agent.query("Was ist ISO 9001?")
        assert result["success"] is True
        assert len(result["results"]) > 0

    def test_standards_agent_din_18040_query(self):
        """Test 13: DIN 18040 query"""
        from backend.agents.domain.standards.technical_standards_agent_v2_framework import TechnicalStandardsAgent

        agent = TechnicalStandardsAgent()
        result = agent.query("DIN 18040 Barrierefreiheit")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_standards_agent_vde_0100_query(self):
        """Test 14: VDE 0100 query"""
        from backend.agents.domain.standards.technical_standards_agent_v2_framework import TechnicalStandardsAgent

        agent = TechnicalStandardsAgent()
        result = agent.query("VDE 0100 Elektroinstallation")
        assert result["success"] is True

    def test_standards_agent_get_info(self):
        """Test 15: Get agent info"""
        from backend.agents.domain.standards.technical_standards_agent_v2_framework import TechnicalStandardsAgent

        agent = TechnicalStandardsAgent()
        info = agent.get_info()
        assert info["name"] == "TechnicalStandardsAgent"
        assert info["standards_count"] >= 10


# =============================================================================
# CHEMICAL DATA AGENT TESTS (5 tests)
# =============================================================================


class TestChemicalDataAgent:
    """Test suite for ChemicalDataAgent"""

    def test_chemical_agent_initialization(self):
        """Test 16: Agent initializes correctly"""
        from backend.agents.domain.chemical.chemical_data_agent_v2_framework import ChemicalDataAgent

        agent = ChemicalDataAgent()
        assert agent.AGENT_TYPE == "chemical_data"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 5

    def test_chemical_agent_ethanol_query(self):
        """Test 17: Ethanol query"""
        from backend.agents.domain.chemical.chemical_data_agent_v2_framework import ChemicalDataAgent

        agent = ChemicalDataAgent()
        result = agent.query("Was ist Ethanol?")
        assert result["success"] is True
        assert result["substance"] is not None

    def test_chemical_agent_cas_number_query(self):
        """Test 18: CAS number query"""
        from backend.agents.domain.chemical.chemical_data_agent_v2_framework import ChemicalDataAgent

        agent = ChemicalDataAgent()
        result = agent.query("64-17-5")  # Ethanol CAS
        assert result["success"] is True
        assert result["identifier"]["type"] == "cas_number"

    def test_chemical_agent_benzol_query(self):
        """Test 19: Benzol query"""
        from backend.agents.domain.chemical.chemical_data_agent_v2_framework import ChemicalDataAgent

        agent = ChemicalDataAgent()
        result = agent.query("Benzol Sicherheitsdatenblatt")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_chemical_agent_get_info(self):
        """Test 20: Get agent info"""
        from backend.agents.domain.chemical.chemical_data_agent_v2_framework import ChemicalDataAgent

        agent = ChemicalDataAgent()
        info = agent.get_info()
        assert info["name"] == "ChemicalDataAgent"
        assert info["substances_count"] >= 5


# =============================================================================
# WIKIPEDIA AGENT TESTS (5 tests)
# =============================================================================


class TestWikipediaAgent:
    """Test suite for WikipediaAgent"""

    def test_wikipedia_agent_initialization(self):
        """Test 21: Agent initializes correctly"""
        from backend.agents.domain.wikipedia.wikipedia_agent_v2_framework import WikipediaAgent

        agent = WikipediaAgent()
        assert agent.AGENT_TYPE == "wikipedia"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 6

    def test_wikipedia_agent_deutschland_query(self):
        """Test 22: Deutschland query"""
        from backend.agents.domain.wikipedia.wikipedia_agent_v2_framework import WikipediaAgent

        agent = WikipediaAgent()
        result = agent.query("Deutschland")
        assert result["success"] is True
        assert len(result["articles"]) > 0

    def test_wikipedia_agent_ki_query(self):
        """Test 23: KI query"""
        from backend.agents.domain.wikipedia.wikipedia_agent_v2_framework import WikipediaAgent

        agent = WikipediaAgent()
        result = agent.query("Künstliche Intelligenz")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_wikipedia_agent_english_query(self):
        """Test 24: English query"""
        from backend.agents.domain.wikipedia.wikipedia_agent_v2_framework import WikipediaAgent

        agent = WikipediaAgent()
        result = agent.query("Climate Change", {"language": "en"})
        assert result["success"] is True
        assert result["language"] == "en"

    def test_wikipedia_agent_get_info(self):
        """Test 25: Get agent info"""
        from backend.agents.domain.wikipedia.wikipedia_agent_v2_framework import WikipediaAgent

        agent = WikipediaAgent()
        info = agent.get_info()
        assert info["name"] == "WikipediaAgent"
        assert "de" in info["supported_languages"]


# =============================================================================
# TRAFFIC AGENT TESTS (5 tests)
# =============================================================================


class TestTrafficAgent:
    """Test suite for TrafficAgent"""

    def test_traffic_agent_initialization(self):
        """Test 26: Agent initializes correctly"""
        from backend.agents.domain.traffic.traffic_agent_v2_framework import TrafficAgent

        agent = TrafficAgent()
        assert agent.AGENT_TYPE == "traffic"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 3

    def test_traffic_agent_muenchen_query(self):
        """Test 27: München traffic query"""
        from backend.agents.domain.traffic.traffic_agent_v2_framework import TrafficAgent

        agent = TrafficAgent()
        result = agent.query("Verkehr in München")
        assert result["success"] is True
        assert result["location"]["name"] == "München"

    def test_traffic_agent_berlin_query(self):
        """Test 28: Berlin traffic query"""
        from backend.agents.domain.traffic.traffic_agent_v2_framework import TrafficAgent

        agent = TrafficAgent()
        result = agent.query("Verkehrslage Berlin")
        assert result["success"] is True
        assert result["traffic_data"] is not None

    def test_traffic_agent_hamburg_query(self):
        """Test 29: Hamburg traffic query"""
        from backend.agents.domain.traffic.traffic_agent_v2_framework import TrafficAgent

        agent = TrafficAgent()
        result = agent.query("ÖPNV Hamburg")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_traffic_agent_get_info(self):
        """Test 30: Get agent info"""
        from backend.agents.domain.traffic.traffic_agent_v2_framework import TrafficAgent

        agent = TrafficAgent()
        info = agent.get_info()
        assert info["name"] == "TrafficAgent"
        assert info["domain"] == "TRANSPORT"


# =============================================================================
# DATABASE AGENT TESTS (5 tests)
# =============================================================================


class TestDatabaseAgent:
    """Test suite for DatabaseAgent"""

    def test_database_agent_initialization(self):
        """Test 31: Agent initializes correctly"""
        from backend.agents.domain.database.database_agent_v2_framework import DatabaseAgent

        agent = DatabaseAgent()
        assert agent.AGENT_TYPE == "database"
        assert agent.AGENT_VERSION == "2.0"
        assert agent.max_results == 1000

    def test_database_agent_select_query(self):
        """Test 32: SELECT query"""
        from backend.agents.domain.database.database_agent_v2_framework import DatabaseAgent

        agent = DatabaseAgent()
        result = agent.query("SELECT * FROM users")
        assert result["success"] is True
        assert result["operation"] == "select"

    def test_database_agent_blocked_insert(self):
        """Test 33: INSERT blocked"""
        from backend.agents.domain.database.database_agent_v2_framework import DatabaseAgent

        agent = DatabaseAgent()
        result = agent.query("INSERT INTO users VALUES (1, 'test')")
        assert result["success"] is False
        assert result.get("blocked") is True

    def test_database_agent_blocked_update(self):
        """Test 34: UPDATE blocked"""
        from backend.agents.domain.database.database_agent_v2_framework import DatabaseAgent

        agent = DatabaseAgent()
        result = agent.query("UPDATE users SET name='test'")
        assert result["success"] is False
        assert "Blocked operation" in result.get("reason", "")

    def test_database_agent_get_info(self):
        """Test 35: Get agent info"""
        from backend.agents.domain.database.database_agent_v2_framework import DatabaseAgent

        agent = DatabaseAgent()
        info = agent.get_info()
        assert info["name"] == "DatabaseAgent"
        assert "Read-Only" in info["security"]


# =============================================================================
# VERWALTUNGSRECHT AGENT TESTS (5 tests)
# =============================================================================


class TestVerwaltungsrechtAgent:
    """Test suite for VerwaltungsrechtAgent"""

    def test_verwaltungsrecht_agent_initialization(self):
        """Test 36: Agent initializes correctly"""
        from backend.agents.domain.social.verwaltungsrecht_agent_v2_framework import VerwaltungsrechtAgent

        agent = VerwaltungsrechtAgent()
        assert agent.AGENT_TYPE == "verwaltungsrecht"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 3

    def test_verwaltungsrecht_agent_baugb_query(self):
        """Test 37: BauGB query"""
        from backend.agents.domain.social.verwaltungsrecht_agent_v2_framework import VerwaltungsrechtAgent

        agent = VerwaltungsrechtAgent()
        result = agent.query("Was regelt das BauGB?")
        assert result["success"] is True
        assert len(result["provisions"]) > 0

    def test_verwaltungsrecht_agent_baugenehmigung_query(self):
        """Test 38: Baugenehmigung query"""
        from backend.agents.domain.social.verwaltungsrecht_agent_v2_framework import VerwaltungsrechtAgent

        agent = VerwaltungsrechtAgent()
        result = agent.query("Baugenehmigung beantragen")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_verwaltungsrecht_agent_vwvfg_query(self):
        """Test 39: VwVfG query"""
        from backend.agents.domain.social.verwaltungsrecht_agent_v2_framework import VerwaltungsrechtAgent

        agent = VerwaltungsrechtAgent()
        result = agent.query("Verwaltungsverfahrensgesetz")
        assert result["success"] is True

    def test_verwaltungsrecht_agent_get_info(self):
        """Test 40: Get agent info"""
        from backend.agents.domain.social.verwaltungsrecht_agent_v2_framework import VerwaltungsrechtAgent

        agent = VerwaltungsrechtAgent()
        info = agent.get_info()
        assert info["name"] == "VerwaltungsrechtAgent"
        assert info["domain"] == "LEGAL"


# =============================================================================
# RECHTSRECHERCHE AGENT TESTS (5 tests)
# =============================================================================


class TestRechtsrechercheAgent:
    """Test suite for RechtsrechercheAgent"""

    def test_rechtsrecherche_agent_initialization(self):
        """Test 41: Agent initializes correctly"""
        from backend.agents.domain.social.rechtsrecherche_agent_v2_framework import RechtsrechercheAgent

        agent = RechtsrechercheAgent()
        assert agent.AGENT_TYPE == "rechtsrecherche"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 3

    def test_rechtsrecherche_agent_bgb_query(self):
        """Test 42: BGB query"""
        from backend.agents.domain.social.rechtsrecherche_agent_v2_framework import RechtsrechercheAgent

        agent = RechtsrechercheAgent()
        result = agent.query("BGB Zivilrecht")
        assert result["success"] is True
        assert len(result["laws"]) > 0

    def test_rechtsrecherche_agent_stgb_query(self):
        """Test 43: StGB query"""
        from backend.agents.domain.social.rechtsrecherche_agent_v2_framework import RechtsrechercheAgent

        agent = RechtsrechercheAgent()
        result = agent.query("Strafgesetzbuch")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_rechtsrecherche_agent_gg_query(self):
        """Test 44: GG query"""
        from backend.agents.domain.social.rechtsrecherche_agent_v2_framework import RechtsrechercheAgent

        agent = RechtsrechercheAgent()
        result = agent.query("Grundgesetz Grundrechte")
        assert result["success"] is True

    def test_rechtsrecherche_agent_get_info(self):
        """Test 45: Get agent info"""
        from backend.agents.domain.social.rechtsrecherche_agent_v2_framework import RechtsrechercheAgent

        agent = RechtsrechercheAgent()
        info = agent.get_info()
        assert info["name"] == "RechtsrechercheAgent"
        assert info["laws_count"] >= 3


# =============================================================================
# VERWALTUNGSPROZESS AGENT TESTS (5 tests)
# =============================================================================


class TestVerwaltungsprozessAgent:
    """Test suite for VerwaltungsprozessAgent"""

    def test_verwaltungsprozess_agent_initialization(self):
        """Test 46: Agent initializes correctly"""
        from backend.agents.domain.social.verwaltungsprozess_agent_v2_framework import VerwaltungsprozessAgent

        agent = VerwaltungsprozessAgent()
        assert agent.AGENT_TYPE == "verwaltungsprozess"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 4

    def test_verwaltungsprozess_agent_klagefrist_query(self):
        """Test 47: Klagefrist query"""
        from backend.agents.domain.social.verwaltungsprozess_agent_v2_framework import VerwaltungsprozessAgent

        agent = VerwaltungsprozessAgent()
        result = agent.query("Wie lange ist die Klagefrist?")
        assert result["success"] is True
        assert len(result["provisions"]) > 0

    def test_verwaltungsprozess_agent_widerspruch_query(self):
        """Test 48: Widerspruch query"""
        from backend.agents.domain.social.verwaltungsprozess_agent_v2_framework import VerwaltungsprozessAgent

        agent = VerwaltungsprozessAgent()
        result = agent.query("Widerspruchsfrist VwGO")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_verwaltungsprozess_agent_einstweilig_query(self):
        """Test 49: Einstweiliger Rechtsschutz query"""
        from backend.agents.domain.social.verwaltungsprozess_agent_v2_framework import VerwaltungsprozessAgent

        agent = VerwaltungsprozessAgent()
        result = agent.query("Einstweiliger Rechtsschutz")
        assert result["success"] is True

    def test_verwaltungsprozess_agent_get_info(self):
        """Test 50: Get agent info"""
        from backend.agents.domain.social.verwaltungsprozess_agent_v2_framework import VerwaltungsprozessAgent

        agent = VerwaltungsprozessAgent()
        info = agent.get_info()
        assert info["name"] == "VerwaltungsprozessAgent"
        assert info["provisions_count"] >= 4


# =============================================================================
# TEST EXECUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


# =============================================================================
# SOCIAL AGENT TESTS (5 tests)
# =============================================================================


class TestSocialAgent:
    """Test suite for SocialAgent"""

    def test_social_agent_initialization(self):
        """Test 1: Agent initializes correctly"""
        agent = SocialAgent()
        assert agent.AGENT_TYPE == "social"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 6

    def test_social_agent_kindergeld_query(self):
        """Test 2: Kindergeld query"""
        agent = SocialAgent()
        result = agent.query("Ich habe 2 Kinder, bekomme ich Kindergeld?")
        assert result["success"] is True
        assert len(result["benefits"]) > 0
        assert result["confidence"] >= 0.6

    def test_social_agent_buergergeld_query(self):
        """Test 3: Bürgergeld query"""
        agent = SocialAgent()
        result = agent.query("Ich bin arbeitslos, brauche Bürgergeld")
        assert result["success"] is True
        assert any("bürgergeld" in str(b).lower() for b in result["benefits"])

    def test_social_agent_wohngeld_query(self):
        """Test 4: Wohngeld query"""
        agent = SocialAgent()
        result = agent.query("Kann ich Wohngeld beantragen?")
        assert result["success"] is True
        assert result["confidence"] >= 0.5

    def test_social_agent_get_info(self):
        """Test 5: Get agent info"""
        agent = SocialAgent()
        info = agent.get_info()
        assert info["name"] == "SocialAgent"
        assert info["domain"] == "SOCIAL_SERVICES"
        assert info["version"] == "2.0"


# =============================================================================
# FINANCIAL AGENT TESTS (5 tests)
# =============================================================================


class TestFinancialAgent:
    """Test suite for FinancialAgent"""

    def test_financial_agent_initialization(self):
        """Test 6: Agent initializes correctly"""
        agent = FinancialAgent()
        assert agent.AGENT_TYPE == "financial"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 5

    def test_financial_agent_grundsteuer_query(self):
        """Test 7: Grundsteuer query"""
        agent = FinancialAgent()
        result = agent.query("Was ist die Grundsteuer in München?")
        assert result["success"] is True
        assert len(result["taxes"]) > 0

    def test_financial_agent_einkommensteuer_query(self):
        """Test 8: Einkommensteuer query"""
        agent = FinancialAgent()
        result = agent.query("Wie hoch ist die Einkommensteuer?")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_financial_agent_gewerbesteuer_query(self):
        """Test 9: Gewerbesteuer query"""
        agent = FinancialAgent()
        result = agent.query("Gewerbesteuer für Unternehmen in Berlin")
        assert result["success"] is True

    def test_financial_agent_get_info(self):
        """Test 10: Get agent info"""
        agent = FinancialAgent()
        info = agent.get_info()
        assert info["name"] == "FinancialAgent"
        assert info["domain"] == "FINANCIAL"


# =============================================================================
# TECHNICAL STANDARDS AGENT TESTS (5 tests)
# =============================================================================


class TestTechnicalStandardsAgent:
    """Test suite for TechnicalStandardsAgent"""

    def test_standards_agent_initialization(self):
        """Test 11: Agent initializes correctly"""
        agent = TechnicalStandardsAgent()
        assert agent.AGENT_TYPE == "technical_standards"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 4

    def test_standards_agent_iso_9001_query(self):
        """Test 12: ISO 9001 query"""
        agent = TechnicalStandardsAgent()
        result = agent.query("Was ist ISO 9001?")
        assert result["success"] is True
        assert len(result["results"]) > 0

    def test_standards_agent_din_18040_query(self):
        """Test 13: DIN 18040 query"""
        agent = TechnicalStandardsAgent()
        result = agent.query("DIN 18040 Barrierefreiheit")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_standards_agent_vde_0100_query(self):
        """Test 14: VDE 0100 query"""
        agent = TechnicalStandardsAgent()
        result = agent.query("VDE 0100 Elektroinstallation")
        assert result["success"] is True

    def test_standards_agent_get_info(self):
        """Test 15: Get agent info"""
        agent = TechnicalStandardsAgent()
        info = agent.get_info()
        assert info["name"] == "TechnicalStandardsAgent"
        assert info["standards_count"] >= 10


# =============================================================================
# CHEMICAL DATA AGENT TESTS (5 tests)
# =============================================================================


class TestChemicalDataAgent:
    """Test suite for ChemicalDataAgent"""

    def test_chemical_agent_initialization(self):
        """Test 16: Agent initializes correctly"""
        agent = ChemicalDataAgent()
        assert agent.AGENT_TYPE == "chemical_data"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 5

    def test_chemical_agent_ethanol_query(self):
        """Test 17: Ethanol query"""
        agent = ChemicalDataAgent()
        result = agent.query("Was ist Ethanol?")
        assert result["success"] is True
        assert result["substance"] is not None

    def test_chemical_agent_cas_number_query(self):
        """Test 18: CAS number query"""
        agent = ChemicalDataAgent()
        result = agent.query("64-17-5")  # Ethanol CAS
        assert result["success"] is True
        assert result["identifier"]["type"] == "cas_number"

    def test_chemical_agent_benzol_query(self):
        """Test 19: Benzol query"""
        agent = ChemicalDataAgent()
        result = agent.query("Benzol Sicherheitsdatenblatt")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_chemical_agent_get_info(self):
        """Test 20: Get agent info"""
        agent = ChemicalDataAgent()
        info = agent.get_info()
        assert info["name"] == "ChemicalDataAgent"
        assert info["substances_count"] >= 5


# =============================================================================
# WIKIPEDIA AGENT TESTS (5 tests)
# =============================================================================


class TestWikipediaAgent:
    """Test suite for WikipediaAgent"""

    def test_wikipedia_agent_initialization(self):
        """Test 21: Agent initializes correctly"""
        agent = WikipediaAgent()
        assert agent.AGENT_TYPE == "wikipedia"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 6

    def test_wikipedia_agent_deutschland_query(self):
        """Test 22: Deutschland query"""
        agent = WikipediaAgent()
        result = agent.query("Deutschland")
        assert result["success"] is True
        assert len(result["articles"]) > 0

    def test_wikipedia_agent_ki_query(self):
        """Test 23: KI query"""
        agent = WikipediaAgent()
        result = agent.query("Künstliche Intelligenz")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_wikipedia_agent_english_query(self):
        """Test 24: English query"""
        agent = WikipediaAgent()
        result = agent.query("Climate Change", {"language": "en"})
        assert result["success"] is True
        assert result["language"] == "en"

    def test_wikipedia_agent_get_info(self):
        """Test 25: Get agent info"""
        agent = WikipediaAgent()
        info = agent.get_info()
        assert info["name"] == "WikipediaAgent"
        assert "de" in info["supported_languages"]


# =============================================================================
# TRAFFIC AGENT TESTS (5 tests)
# =============================================================================


class TestTrafficAgent:
    """Test suite for TrafficAgent"""

    def test_traffic_agent_initialization(self):
        """Test 26: Agent initializes correctly"""
        agent = TrafficAgent()
        assert agent.AGENT_TYPE == "traffic"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 3

    def test_traffic_agent_muenchen_query(self):
        """Test 27: München traffic query"""
        agent = TrafficAgent()
        result = agent.query("Verkehr in München")
        assert result["success"] is True
        assert result["location"]["name"] == "München"

    def test_traffic_agent_berlin_query(self):
        """Test 28: Berlin traffic query"""
        agent = TrafficAgent()
        result = agent.query("Verkehrslage Berlin")
        assert result["success"] is True
        assert result["traffic_data"] is not None

    def test_traffic_agent_hamburg_query(self):
        """Test 29: Hamburg traffic query"""
        agent = TrafficAgent()
        result = agent.query("ÖPNV Hamburg")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_traffic_agent_get_info(self):
        """Test 30: Get agent info"""
        agent = TrafficAgent()
        info = agent.get_info()
        assert info["name"] == "TrafficAgent"
        assert info["domain"] == "TRANSPORT"


# =============================================================================
# DATABASE AGENT TESTS (5 tests)
# =============================================================================


class TestDatabaseAgent:
    """Test suite for DatabaseAgent"""

    def test_database_agent_initialization(self):
        """Test 31: Agent initializes correctly"""
        agent = DatabaseAgent()
        assert agent.AGENT_TYPE == "database"
        assert agent.AGENT_VERSION == "2.0"
        assert agent.max_results == 1000

    def test_database_agent_select_query(self):
        """Test 32: SELECT query"""
        agent = DatabaseAgent()
        result = agent.query("SELECT * FROM users")
        assert result["success"] is True
        assert result["operation"] == "select"

    def test_database_agent_blocked_insert(self):
        """Test 33: INSERT blocked"""
        agent = DatabaseAgent()
        result = agent.query("INSERT INTO users VALUES (1, 'test')")
        assert result["success"] is False
        assert result.get("blocked") is True

    def test_database_agent_blocked_update(self):
        """Test 34: UPDATE blocked"""
        agent = DatabaseAgent()
        result = agent.query("UPDATE users SET name='test'")
        assert result["success"] is False
        assert "Blocked operation" in result.get("reason", "")

    def test_database_agent_get_info(self):
        """Test 35: Get agent info"""
        agent = DatabaseAgent()
        info = agent.get_info()
        assert info["name"] == "DatabaseAgent"
        assert "Read-Only" in info["security"]


# =============================================================================
# VERWALTUNGSRECHT AGENT TESTS (5 tests)
# =============================================================================


class TestVerwaltungsrechtAgent:
    """Test suite for VerwaltungsrechtAgent"""

    def test_verwaltungsrecht_agent_initialization(self):
        """Test 36: Agent initializes correctly"""
        agent = VerwaltungsrechtAgent()
        assert agent.AGENT_TYPE == "verwaltungsrecht"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 3

    def test_verwaltungsrecht_agent_baugb_query(self):
        """Test 37: BauGB query"""
        agent = VerwaltungsrechtAgent()
        result = agent.query("Was regelt das BauGB?")
        assert result["success"] is True
        assert len(result["provisions"]) > 0

    def test_verwaltungsrecht_agent_baugenehmigung_query(self):
        """Test 38: Baugenehmigung query"""
        agent = VerwaltungsrechtAgent()
        result = agent.query("Baugenehmigung beantragen")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_verwaltungsrecht_agent_vwvfg_query(self):
        """Test 39: VwVfG query"""
        agent = VerwaltungsrechtAgent()
        result = agent.query("Verwaltungsverfahrensgesetz")
        assert result["success"] is True

    def test_verwaltungsrecht_agent_get_info(self):
        """Test 40: Get agent info"""
        agent = VerwaltungsrechtAgent()
        info = agent.get_info()
        assert info["name"] == "VerwaltungsrechtAgent"
        assert info["domain"] == "LEGAL"


# =============================================================================
# RECHTSRECHERCHE AGENT TESTS (5 tests)
# =============================================================================


class TestRechtsrechercheAgent:
    """Test suite for RechtsrechercheAgent"""

    def test_rechtsrecherche_agent_initialization(self):
        """Test 41: Agent initializes correctly"""
        agent = RechtsrechercheAgent()
        assert agent.AGENT_TYPE == "rechtsrecherche"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 3

    def test_rechtsrecherche_agent_bgb_query(self):
        """Test 42: BGB query"""
        agent = RechtsrechercheAgent()
        result = agent.query("BGB Zivilrecht")
        assert result["success"] is True
        assert len(result["laws"]) > 0

    def test_rechtsrecherche_agent_stgb_query(self):
        """Test 43: StGB query"""
        agent = RechtsrechercheAgent()
        result = agent.query("Strafgesetzbuch")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_rechtsrecherche_agent_gg_query(self):
        """Test 44: GG query"""
        agent = RechtsrechercheAgent()
        result = agent.query("Grundgesetz Grundrechte")
        assert result["success"] is True

    def test_rechtsrecherche_agent_get_info(self):
        """Test 45: Get agent info"""
        agent = RechtsrechercheAgent()
        info = agent.get_info()
        assert info["name"] == "RechtsrechercheAgent"
        assert info["laws_count"] >= 3


# =============================================================================
# VERWALTUNGSPROZESS AGENT TESTS (5 tests)
# =============================================================================


class TestVerwaltungsprozessAgent:
    """Test suite for VerwaltungsprozessAgent"""

    def test_verwaltungsprozess_agent_initialization(self):
        """Test 46: Agent initializes correctly"""
        agent = VerwaltungsprozessAgent()
        assert agent.AGENT_TYPE == "verwaltungsprozess"
        assert agent.AGENT_VERSION == "2.0"
        assert len(agent.knowledge_base) >= 4

    def test_verwaltungsprozess_agent_klagefrist_query(self):
        """Test 47: Klagefrist query"""
        agent = VerwaltungsprozessAgent()
        result = agent.query("Wie lange ist die Klagefrist?")
        assert result["success"] is True
        assert len(result["provisions"]) > 0

    def test_verwaltungsprozess_agent_widerspruch_query(self):
        """Test 48: Widerspruch query"""
        agent = VerwaltungsprozessAgent()
        result = agent.query("Widerspruchsfrist VwGO")
        assert result["success"] is True
        assert result["confidence"] >= 0.6

    def test_verwaltungsprozess_agent_einstweilig_query(self):
        """Test 49: Einstweiliger Rechtsschutz query"""
        agent = VerwaltungsprozessAgent()
        result = agent.query("Einstweiliger Rechtsschutz")
        assert result["success"] is True

    def test_verwaltungsprozess_agent_get_info(self):
        """Test 50: Get agent info"""
        agent = VerwaltungsprozessAgent()
        info = agent.get_info()
        assert info["name"] == "VerwaltungsprozessAgent"
        assert info["provisions_count"] >= 4


# =============================================================================
# TEST EXECUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
