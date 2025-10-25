#!/usr/bin/env python3
"""
Test: VerwaltungsrechtAgent Registry Integration
=================================================

Test der Integration des VerwaltungsrechtAgent im AgentRegistry.

Test-Szenarien:
1. Agent-Registrierung im Registry
2. Agent-Abruf über Registry
3. Query über Registry
4. Capability-basierte Suche

Author: VERITAS Development Team
Date: 2025-10-16
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agents.agent_registry import AgentRegistry, AgentDomain

logger = logging.getLogger(__name__)

# ==========================================
# TEST UTILITIES
# ==========================================

def print_header(title: str):
    """Print formatted test header"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def print_result(result_type: str, message: str):
    """Print formatted test result"""
    symbols = {
        "PASS": "✅",
        "FAIL": "❌",
        "INFO": "ℹ️",
        "WARN": "⚠️"
    }
    symbol = symbols.get(result_type, "•")
    print(f"  {symbol} {message}")

# ==========================================
# TESTS
# ==========================================

def test_registry_initialization():
    """Test 1: Registry-Initialisierung"""
    print_header("TEST 1: Registry-Initialisierung")
    
    try:
        registry = AgentRegistry()
        
        # Prüfe, dass VerwaltungsrechtAgent registriert ist
        agents = registry.list_available_agents()
        
        print_result("INFO", f"Registrierte Agents: {len(agents)}")
        for agent_id in agents:
            print_result("INFO", f"  - {agent_id}")
        
        if "VerwaltungsrechtAgent" in agents:
            print_result("PASS", "VerwaltungsrechtAgent erfolgreich registriert")
            return True
        else:
            print_result("FAIL", "VerwaltungsrechtAgent nicht im Registry gefunden")
            return False
            
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

def test_agent_retrieval():
    """Test 2: Agent-Abruf über Registry"""
    print_header("TEST 2: Agent-Abruf über Registry")
    
    try:
        registry = AgentRegistry()
        
        # Hole VerwaltungsrechtAgent
        agent = registry.get_agent("VerwaltungsrechtAgent")
        
        if agent is None:
            print_result("FAIL", "Agent konnte nicht abgerufen werden")
            return False
        
        print_result("PASS", f"Agent abgerufen: {type(agent).__name__}")
        
        # Prüfe Agent-Eigenschaften
        if hasattr(agent, "name"):
            print_result("INFO", f"Agent Name: {agent.name}")
        if hasattr(agent, "version"):
            print_result("INFO", f"Agent Version: {agent.version}")
        
        return True
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

def test_query_via_registry():
    """Test 3: Query über Registry"""
    print_header("TEST 3: Query über Registry")
    
    try:
        registry = AgentRegistry()
        agent = registry.get_agent("VerwaltungsrechtAgent")
        
        if agent is None:
            print_result("FAIL", "Agent nicht verfügbar")
            return False
        
        # Teste Query
        query_text = "Was bedeutet § 34 BauGB?"
        result = agent.query(query_text)
        
        print_result("INFO", f"Query: {query_text}")
        
        if result.get("success"):
            print_result("PASS", f"Query erfolgreich: {len(result.get('results', []))} Ergebnisse")
            print_result("INFO", f"Confidence: {result.get('confidence', 0):.2f}")
            print_result("INFO", f"Processing Time: {result.get('processing_time_ms', 0)}ms")
            
            # Zeige erste Ergebnisse
            results = result.get("results", [])
            if results:
                top_result = results[0]
                print_result("INFO", f"Top Result: {top_result.get('paragraph', 'N/A')}")
            
            return True
        else:
            print_result("FAIL", f"Query fehlgeschlagen: {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_capability_search():
    """Test 4: Capability-basierte Suche"""
    print_header("TEST 4: Capability-basierte Suche")
    
    try:
        registry = AgentRegistry()
        
        # Test verschiedene Capabilities
        test_cases = [
            ("verwaltungsrecht", "VerwaltungsrechtAgent"),
            ("baurecht", "VerwaltungsrechtAgent"),
            ("baugenehmigung", "VerwaltungsrechtAgent"),
        ]
        
        passed = 0
        failed = 0
        
        for capability, expected_agent in test_cases:
            agents = registry.get_agents_by_capability(capability)
            
            if expected_agent in agents:
                print_result("PASS", f"Capability '{capability}' → {expected_agent} gefunden")
                passed += 1
            else:
                print_result("FAIL", f"Capability '{capability}' → {expected_agent} nicht gefunden (gefunden: {agents})")
                failed += 1
        
        print(f"\n  Gesamt: {passed}/{len(test_cases)} Capability-Tests bestanden")
        return failed == 0
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

def test_domain_search():
    """Test 5: Domain-basierte Suche"""
    print_header("TEST 5: Domain-basierte Suche")
    
    try:
        registry = AgentRegistry()
        
        # Suche LEGAL-Domain Agents
        legal_agents = registry.get_agents_by_domain(AgentDomain.LEGAL)
        
        print_result("INFO", f"LEGAL-Domain Agents: {len(legal_agents)}")
        for agent_id in legal_agents:
            print_result("INFO", f"  - {agent_id}")
        
        if "VerwaltungsrechtAgent" in legal_agents:
            print_result("PASS", "VerwaltungsrechtAgent in LEGAL-Domain gefunden")
            return True
        else:
            print_result("FAIL", "VerwaltungsrechtAgent nicht in LEGAL-Domain")
            return False
            
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

def test_agent_info():
    """Test 6: Agent-Info über Registry"""
    print_header("TEST 6: Agent-Info über Registry")
    
    try:
        registry = AgentRegistry()
        
        # Hole Agent-Info
        info = registry.get_agent_info("VerwaltungsrechtAgent")
        
        if info is None:
            print_result("FAIL", "Agent-Info nicht verfügbar")
            return False
        
        print_result("PASS", "Agent-Info erfolgreich abgerufen")
        print_result("INFO", f"Agent ID: {info.agent_id}")
        print_result("INFO", f"Domain: {info.domain.value}")
        print_result("INFO", f"Capabilities: {len(info.capabilities)}")
        print_result("INFO", f"Description: {info.description}")
        print_result("INFO", f"Initialized: {info.initialized}")
        
        return True
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

def test_multiple_queries():
    """Test 7: Multiple Queries"""
    print_header("TEST 7: Multiple Queries")
    
    try:
        registry = AgentRegistry()
        agent = registry.get_agent("VerwaltungsrechtAgent")
        
        if agent is None:
            print_result("FAIL", "Agent nicht verfügbar")
            return False
        
        # Verschiedene Test-Queries
        queries = [
            "Welche Unterlagen brauche ich für eine Baugenehmigung?",
            "Was bedeutet § 35 BauGB?",
            "Vorsorgepflicht nach § 5 BImSchG",
        ]
        
        passed = 0
        failed = 0
        
        for i, query in enumerate(queries, 1):
            print(f"\n  Query {i}: {query}")
            result = agent.query(query)
            
            if result.get("success") and len(result.get("results", [])) > 0:
                print_result("PASS", f"{len(result['results'])} Ergebnisse")
                passed += 1
            else:
                print_result("FAIL", "Keine Ergebnisse")
                failed += 1
        
        print(f"\n  Gesamt: {passed}/{len(queries)} Queries erfolgreich")
        return failed == 0
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

# ==========================================
# TEST RUNNER
# ==========================================

def run_all_tests():
    """Führe alle Tests aus"""
    print_header("VERWALTUNGSRECHT AGENT - REGISTRY INTEGRATION TESTS")
    
    tests = [
        ("Registry-Initialisierung", test_registry_initialization),
        ("Agent-Abruf", test_agent_retrieval),
        ("Query über Registry", test_query_via_registry),
        ("Capability-Suche", test_capability_search),
        ("Domain-Suche", test_domain_search),
        ("Agent-Info", test_agent_info),
        ("Multiple Queries", test_multiple_queries),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print_result("FAIL", f"Test '{test_name}' abgebrochen: {e}")
            results.append((test_name, False))
    
    # Zusammenfassung
    print_header("TEST ZUSAMMENFASSUNG")
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print_result(status, test_name)
    
    print(f"\n  Gesamt: {passed}/{len(results)} Tests bestanden ({passed/len(results)*100:.1f}%)")
    
    if failed == 0:
        print_result("PASS", "🎉 ALLE REGISTRY-INTEGRATION TESTS BESTANDEN!")
        return 0
    else:
        print_result("FAIL", f"❌ {failed} Test(s) fehlgeschlagen")
        return 1

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    exit_code = run_all_tests()
    sys.exit(exit_code)
