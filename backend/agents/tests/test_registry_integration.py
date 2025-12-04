"""
VERITAS Registry Integration Tests - Phase 3 Agents

Tests die Registry-Integration der Phase 3 Agents.
Prüft Registrierung, Capability-Matching und Lifecycle.

Author: VERITAS Test Suite
Date: 2025-12-04
"""

import os
import sys

import pytest

# Add project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_registry_phase3_registration():
    """Test Phase 3 agent registration in registry"""
    from backend.agents.registry.domain_agent_registration import register_phase3_agents

    results = register_phase3_agents()

    # Verify all 10 agents were attempted
    assert len(results) == 10, f"Expected 10 agents, got {len(results)}"

    # Check which agents registered successfully
    passed = [k for k, v in results.items() if v]
    failed = [k for k, v in results.items() if not v]

    print(f"\n✅ Registered: {len(passed)}/10")
    if passed:
        for agent in passed:
            print(f"   ✅ {agent}")

    if failed:
        print(f"\n❌ Failed: {len(failed)}/10")
        for agent in failed:
            print(f"   ❌ {agent}")

    # At least check that registration was attempted
    expected_agents = [
        "SocialAgent",
        "VerwaltungsrechtAgent",
        "RechtsrechercheAgent",
        "VerwaltungsprozessAgent",
        "FinancialAgent",
        "TechnicalStandardsAgent",
        "ChemicalDataAgent",
        "WikipediaAgent",
        "TrafficAgent",
        "DatabaseAgent",
    ]

    for agent in expected_agents:
        assert agent in results, f"Agent {agent} not in results"


def test_registry_all_phases():
    """Test registration of all phases"""
    from backend.agents.registry.domain_agent_registration import register_all_domain_agents

    results = register_all_domain_agents(phase="all")

    print(f"\n📊 Total Registrations: {len(results)}")
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    assert len(results) > 0, "No agents registered"


def test_registry_get_instance():
    """Test getting agent instance from registry"""
    from backend.agents.registry.api_agent_registry import get_agent_registry

    registry = get_agent_registry()

    # Test registry is accessible
    assert registry is not None
    assert hasattr(registry, "register_agent")
    assert hasattr(registry, "get_agent")

    print("\n✅ Registry accessible")


def test_phase3_agent_capabilities():
    """Test that Phase 3 agents have correct capabilities"""
    # Import all Phase 3 agents
    from backend.agents.domain.financial.financial_agent_v2_framework import FinancialAgent
    from backend.agents.domain.social.social_agent_v2_framework import SocialAgent
    from backend.agents.domain.standards.technical_standards_agent_v2_framework import TechnicalStandardsAgent

    agents = [
        (SocialAgent(), "social", ["social_benefits", "child_care"]),
        (FinancialAgent(), "financial", ["tax_assessment", "property_tax"]),
        (TechnicalStandardsAgent(), "technical_standards", ["iso_standards", "din_standards"]),
    ]

    for agent, expected_type, expected_capabilities in agents:
        # Check type
        assert agent.AGENT_TYPE == expected_type, f"Wrong type: {agent.AGENT_TYPE}"

        # Check capabilities method exists
        capabilities = agent.get_capabilities()
        assert isinstance(capabilities, list), f"Capabilities should be list, got {type(capabilities)}"

        # Check at least some expected capabilities exist
        for cap in expected_capabilities:
            assert cap in capabilities, f"{expected_type} missing capability: {cap}"

        print(f"✅ {expected_type}: {len(capabilities)} capabilities")


def test_agent_info_structure():
    """Test that all Phase 3 agents return proper info structure"""
    from backend.agents.domain.database.database_agent_v2_framework import DatabaseAgent
    from backend.agents.domain.social.social_agent_v2_framework import SocialAgent

    agents = [SocialAgent(), DatabaseAgent()]

    for agent in agents:
        info = agent.get_info()

        # Check required keys
        assert "type" in info, f"{agent.AGENT_TYPE} missing 'type' in info"
        assert "version" in info, f"{agent.AGENT_TYPE} missing 'version' in info"
        assert "capabilities" in info, f"{agent.AGENT_TYPE} missing 'capabilities' in info"

        # Check values
        assert info["version"] == "2.0", f"Wrong version: {info['version']}"
        assert isinstance(info["capabilities"], list), "Capabilities should be list"

        print(f"✅ {agent.AGENT_TYPE}: Valid info structure")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
