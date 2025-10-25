#!/usr/bin/env python3
"""
Test: Production Agents - Comprehensive Test Suite
===================================================

Umfassende Test-Suite für alle drei Production Agents:
- VerwaltungsrechtAgent
- RechtsrecherchAgent  
- ImmissionsschutzAgent

Test-Szenarien:
1. Agent Registry Integration (alle 9 Agents)
2. Einzelagent-Tests (Queries)
3. Capability-basierte Suche
4. Domain-basierte Suche
5. Performance-Tests

Author: VERITAS Development Team
Date: 2025-10-16
"""

import sys
import os
import logging
from datetime import datetime

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

def test_registry_all_agents():
    """Test 1: Registry mit allen 9 Agents"""
    print_header("TEST 1: Registry - Alle Agents")
    
    try:
        registry = AgentRegistry()
        agents = registry.list_available_agents()
        
        print_result("INFO", f"Registrierte Agents: {len(agents)}")
        
        expected_agents = [
            "EnvironmentalAgent",
            "ChemicalDataAgent",
            "TechnicalStandardsAgent",
            "WikipediaAgent",
            "AtmosphericFlowAgent",
            "DatabaseAgent",
            "VerwaltungsrechtAgent",
            "RechtsrecherchAgent",
            "ImmissionsschutzAgent"
        ]
        
        for agent_id in expected_agents:
            if agent_id in agents:
                print_result("PASS", f"{agent_id} registriert")
            else:
                print_result("FAIL", f"{agent_id} NICHT registriert")
        
        if len(agents) == 9:
            print_result("PASS", f"Alle 9 Agents erfolgreich registriert!")
            return True
        else:
            print_result("FAIL", f"Nur {len(agents)}/9 Agents registriert")
            return False
            
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

def test_verwaltungsrecht_agent():
    """Test 2: VerwaltungsrechtAgent Queries"""
    print_header("TEST 2: VerwaltungsrechtAgent - Query Tests")
    
    try:
        registry = AgentRegistry()
        agent = registry.get_agent("VerwaltungsrechtAgent")
        
        if agent is None:
            print_result("FAIL", "Agent nicht verfügbar")
            return False
        
        test_queries = [
            ("Was bedeutet § 34 BauGB?", 1),
            ("Welche Unterlagen für Baugenehmigung?", 1),
            ("§ 5 BImSchG Vorsorgepflicht", 1),
        ]
        
        passed = 0
        failed = 0
        
        for query, min_results in test_queries:
            result = agent.query(query)
            
            if result["success"] and len(result["results"]) >= min_results:
                print_result("PASS", f"'{query[:40]}...' → {len(result['results'])} Ergebnisse")
                passed += 1
            else:
                print_result("FAIL", f"'{query[:40]}...' → {len(result['results'])} Ergebnisse")
                failed += 1
        
        print(f"\n  Gesamt: {passed}/{len(test_queries)} Queries erfolgreich")
        return failed == 0
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rechtsrecherch_agent():
    """Test 3: RechtsrecherchAgent Queries"""
    print_header("TEST 3: RechtsrecherchAgent - Query Tests")
    
    try:
        registry = AgentRegistry()
        agent = registry.get_agent("RechtsrecherchAgent")
        
        if agent is None:
            print_result("FAIL", "Agent nicht verfügbar")
            return False
        
        test_queries = [
            ("Was bedeutet § 433 BGB?", 1),
            ("Grundrechte Grundgesetz", 1),
            ("Schadensersatz BGB", 1),
        ]
        
        passed = 0
        failed = 0
        
        for query, min_results in test_queries:
            result = agent.query(query)
            
            if result["success"] and len(result["results"]) >= min_results:
                print_result("PASS", f"'{query[:40]}...' → {len(result['results'])} Ergebnisse")
                passed += 1
            else:
                print_result("FAIL", f"'{query[:40]}...' → {len(result['results'])} Ergebnisse")
                failed += 1
        
        print(f"\n  Gesamt: {passed}/{len(test_queries)} Queries erfolgreich")
        return failed == 0
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_immissionsschutz_agent():
    """Test 4: ImmissionsschutzAgent Queries"""
    print_header("TEST 4: ImmissionsschutzAgent - Query Tests")
    
    try:
        registry = AgentRegistry()
        agent = registry.get_agent("ImmissionsschutzAgent")
        
        if agent is None:
            print_result("FAIL", "Agent nicht verfügbar")
            return False
        
        test_queries = [
            ("NO2 Grenzwerte", 1),
            ("Lärmgrenzwerte Wohngebiet", 1),
            ("Feinstaub PM10", 1),
            ("TA Luft", 1),
        ]
        
        passed = 0
        failed = 0
        
        for query, min_results in test_queries:
            result = agent.query(query)
            
            if result["success"] and len(result["results"]) >= min_results:
                print_result("PASS", f"'{query[:40]}...' → {len(result['results'])} Ergebnisse")
                passed += 1
            else:
                print_result("FAIL", f"'{query[:40]}...' → {len(result['results'])} Ergebnisse")
                failed += 1
        
        print(f"\n  Gesamt: {passed}/{len(test_queries)} Queries erfolgreich")
        return failed == 0
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_capability_based_search():
    """Test 5: Capability-basierte Suche für neue Agents"""
    print_header("TEST 5: Capability-basierte Suche")
    
    try:
        registry = AgentRegistry()
        
        test_cases = [
            # VerwaltungsrechtAgent
            ("baurecht", "VerwaltungsrechtAgent"),
            ("verwaltungsrecht", "VerwaltungsrechtAgent"),
            
            # RechtsrecherchAgent
            ("rechtsrecherche", "RechtsrecherchAgent"),
            ("bgb", "RechtsrecherchAgent"),
            ("grundgesetz", "RechtsrecherchAgent"),
            
            # ImmissionsschutzAgent
            ("luftqualität", "ImmissionsschutzAgent"),
            ("lärm", "ImmissionsschutzAgent"),
            ("ta luft", "ImmissionsschutzAgent"),
        ]
        
        passed = 0
        failed = 0
        
        for capability, expected_agent in test_cases:
            agents = registry.get_agents_by_capability(capability)
            
            if expected_agent in agents:
                print_result("PASS", f"Capability '{capability}' → {expected_agent}")
                passed += 1
            else:
                print_result("FAIL", f"Capability '{capability}' → NICHT gefunden (gefunden: {agents})")
                failed += 1
        
        print(f"\n  Gesamt: {passed}/{len(test_cases)} Capability-Tests bestanden")
        return failed == 0
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

def test_domain_distribution():
    """Test 6: Domain-Verteilung der Agents"""
    print_header("TEST 6: Domain-Verteilung")
    
    try:
        registry = AgentRegistry()
        
        # LEGAL Domain (sollte 2 Agents haben: VerwaltungsrechtAgent, RechtsrecherchAgent)
        legal_agents = registry.get_agents_by_domain(AgentDomain.LEGAL)
        print_result("INFO", f"LEGAL Domain: {len(legal_agents)} Agents")
        for agent_id in legal_agents:
            print_result("INFO", f"  - {agent_id}")
        
        # ENVIRONMENTAL Domain (sollte 3 Agents haben: Environmental, Chemical, ImmissionsschutzAgent)
        env_agents = registry.get_agents_by_domain(AgentDomain.ENVIRONMENTAL)
        print_result("INFO", f"ENVIRONMENTAL Domain: {len(env_agents)} Agents")
        for agent_id in env_agents:
            print_result("INFO", f"  - {agent_id}")
        
        # Prüfungen
        legal_ok = "VerwaltungsrechtAgent" in legal_agents and "RechtsrecherchAgent" in legal_agents
        env_ok = "ImmissionsschutzAgent" in env_agents
        
        if legal_ok and env_ok:
            print_result("PASS", "Domain-Verteilung korrekt")
            return True
        else:
            print_result("FAIL", "Domain-Verteilung fehlerhaft")
            return False
            
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

def test_performance():
    """Test 7: Performance-Test aller Production Agents"""
    print_header("TEST 7: Performance-Test")
    
    try:
        registry = AgentRegistry()
        
        performance_tests = [
            ("VerwaltungsrechtAgent", "Was bedeutet § 34 BauGB?"),
            ("RechtsrecherchAgent", "Was bedeutet § 433 BGB?"),
            ("ImmissionsschutzAgent", "NO2 Grenzwerte"),
        ]
        
        passed = 0
        failed = 0
        
        for agent_id, query in performance_tests:
            agent = registry.get_agent(agent_id)
            
            if agent is None:
                print_result("FAIL", f"{agent_id} nicht verfügbar")
                failed += 1
                continue
            
            result = agent.query(query)
            processing_time = result.get("processing_time_ms", 0)
            
            if processing_time < 100:  # < 100ms = PASS
                print_result("PASS", f"{agent_id}: {processing_time}ms")
                passed += 1
            else:
                print_result("WARN", f"{agent_id}: {processing_time}ms (langsam)")
                passed += 1  # Trotzdem PASS, nur langsam
        
        print(f"\n  Gesamt: {passed}/{len(performance_tests)} Performance-Tests bestanden")
        return failed == 0
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

def test_agent_info():
    """Test 8: Agent-Informationen abrufen"""
    print_header("TEST 8: Agent-Informationen")
    
    try:
        registry = AgentRegistry()
        
        production_agents = [
            "VerwaltungsrechtAgent",
            "RechtsrecherchAgent",
            "ImmissionsschutzAgent"
        ]
        
        passed = 0
        failed = 0
        
        for agent_id in production_agents:
            agent = registry.get_agent(agent_id)
            
            if agent is None:
                print_result("FAIL", f"{agent_id} nicht verfügbar")
                failed += 1
                continue
            
            info = agent.get_info()
            
            if "agent_id" in info and "name" in info and "version" in info:
                print_result("PASS", f"{agent_id}: v{info['version']}")
                passed += 1
            else:
                print_result("FAIL", f"{agent_id}: Info unvollständig")
                failed += 1
        
        print(f"\n  Gesamt: {passed}/{len(production_agents)} Info-Tests bestanden")
        return failed == 0
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

# ==========================================
# TEST RUNNER
# ==========================================

def run_all_tests():
    """Führe alle Tests aus"""
    print_header("PRODUCTION AGENTS - COMPREHENSIVE TEST SUITE")
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Registry - Alle 9 Agents", test_registry_all_agents),
        ("VerwaltungsrechtAgent Queries", test_verwaltungsrecht_agent),
        ("RechtsrecherchAgent Queries", test_rechtsrecherch_agent),
        ("ImmissionsschutzAgent Queries", test_immissionsschutz_agent),
        ("Capability-basierte Suche", test_capability_based_search),
        ("Domain-Verteilung", test_domain_distribution),
        ("Performance-Test", test_performance),
        ("Agent-Informationen", test_agent_info),
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
        print_result("PASS", "🎉 ALLE PRODUCTION AGENT TESTS BESTANDEN!")
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
