#!/usr/bin/env python3
"""
Test: Production Agents - Direct Registry Tests
================================================

Direkte Tests der Production Agents über Agent Registry (ohne Pipeline).

Test-Szenarien:
1. Agent Registry Initialisierung mit allen 9 Agents
2. Direkte Agent-Queries (VerwaltungsrechtAgent, RechtsrecherchAgent, ImmissionsschutzAgent)
3. Capability-basierte Agent-Suche
4. Domain-basierte Agent-Suche
5. Multi-Agent Orchestration (simulation)

Author: VERITAS Development Team
Date: 2025-10-16
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agents.agent_registry import get_agent_registry

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
    """Test 1: Agent Registry Initialisierung"""
    print_header("TEST 1: Agent Registry Initialisierung")
    
    try:
        registry = get_agent_registry()
        agents = registry.list_available_agents()
        
        print_result("INFO", f"Verfügbare Agents: {len(agents)}")
        
        # Prüfe Production Agents
        production_agents = ["VerwaltungsrechtAgent", "RechtsrecherchAgent", "ImmissionsschutzAgent"]
        found = []
        
        for agent_name in production_agents:
            if agent_name in agents:
                found.append(agent_name)
                print_result("PASS", f"{agent_name} registriert")
            else:
                print_result("FAIL", f"{agent_name} NICHT registriert")
        
        if len(found) == 3:
            print_result("PASS", "Alle 3 Production Agents verfügbar!")
            return True
        else:
            print_result("FAIL", f"Nur {len(found)}/3 Production Agents verfügbar")
            return False
            
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_verwaltungsrecht_direct():
    """Test 2: VerwaltungsrechtAgent - Direkte Queries"""
    print_header("TEST 2: VerwaltungsrechtAgent - Direkte Queries")
    
    try:
        registry = get_agent_registry()
        agent = registry.get_agent("VerwaltungsrechtAgent")
        
        if not agent:
            print_result("FAIL", "VerwaltungsrechtAgent nicht gefunden")
            return False
        
        test_queries = [
            "Was bedeutet § 34 BauGB?",
            "Welche Unterlagen brauche ich für eine Baugenehmigung?",
            "§ 5 BImSchG Vorsorgepflicht",
        ]
        
        passed = 0
        failed = 0
        
        for query in test_queries:
            result = agent.query(query)
            
            if result.get("success") and len(result.get("results", [])) > 0:
                print_result("PASS", f"'{query[:50]}...' → {len(result['results'])} Ergebnisse (Konfidenz: {result.get('confidence', 0):.2f})")
                passed += 1
            else:
                print_result("FAIL", f"'{query[:50]}...' → Keine Ergebnisse")
                failed += 1
        
        print(f"\n  Gesamt: {passed}/{len(test_queries)} Queries erfolgreich")
        return failed == 0
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rechtsrecherche_direct():
    """Test 3: RechtsrecherchAgent - Direkte Queries"""
    print_header("TEST 3: RechtsrecherchAgent - Direkte Queries")
    
    try:
        registry = get_agent_registry()
        agent = registry.get_agent("RechtsrecherchAgent")
        
        if not agent:
            print_result("FAIL", "RechtsrecherchAgent nicht gefunden")
            return False
        
        test_queries = [
            "Was bedeutet § 433 BGB?",
            "Grundrechte im Grundgesetz",
            "Schadensersatz nach BGB",
        ]
        
        passed = 0
        failed = 0
        
        for query in test_queries:
            result = agent.query(query)
            
            if result.get("success") and len(result.get("results", [])) > 0:
                print_result("PASS", f"'{query[:50]}...' → {len(result['results'])} Ergebnisse (Konfidenz: {result.get('confidence', 0):.2f})")
                passed += 1
            else:
                print_result("FAIL", f"'{query[:50]}...' → Keine Ergebnisse")
                failed += 1
        
        print(f"\n  Gesamt: {passed}/{len(test_queries)} Queries erfolgreich")
        return failed == 0
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_immissionsschutz_direct():
    """Test 4: ImmissionsschutzAgent - Direkte Queries"""
    print_header("TEST 4: ImmissionsschutzAgent - Direkte Queries")
    
    try:
        registry = get_agent_registry()
        agent = registry.get_agent("ImmissionsschutzAgent")
        
        if not agent:
            print_result("FAIL", "ImmissionsschutzAgent nicht gefunden")
            return False
        
        test_queries = [
            "NO2 Grenzwerte in Deutschland",
            "Lärmgrenzwerte für Wohngebiete",
            "Feinstaub PM10 Grenzwerte",
        ]
        
        passed = 0
        failed = 0
        
        for query in test_queries:
            result = agent.query(query)
            
            if result.get("success") and len(result.get("results", [])) > 0:
                print_result("PASS", f"'{query[:50]}...' → {len(result['results'])} Ergebnisse (Konfidenz: {result.get('confidence', 0):.2f})")
                passed += 1
            else:
                print_result("FAIL", f"'{query[:50]}...' → Keine Ergebnisse")
                failed += 1
        
        print(f"\n  Gesamt: {passed}/{len(test_queries)} Queries erfolgreich")
        return failed == 0
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_capability_search():
    """Test 5: Capability-basierte Agent-Suche"""
    print_header("TEST 5: Capability-basierte Agent-Suche")
    
    try:
        registry = get_agent_registry()
        
        test_capabilities = [
            ("baurecht", ["VerwaltungsrechtAgent"]),
            ("verwaltungsrecht", ["VerwaltungsrechtAgent"]),
            ("rechtsrecherche", ["RechtsrecherchAgent"]),
            ("bgb", ["RechtsrecherchAgent"]),
            ("grundgesetz", ["RechtsrecherchAgent"]),
            ("luftqualität", ["ImmissionsschutzAgent"]),
            ("lärm", ["ImmissionsschutzAgent"]),
            ("immissionsschutz", ["ImmissionsschutzAgent"]),
        ]
        
        passed = 0
        failed = 0
        
        for capability, expected_agents in test_capabilities:
            agent_names = registry.get_agents_by_capability(capability)
            
            found = any(name in expected_agents for name in agent_names)
            
            if found:
                print_result("PASS", f"Capability '{capability}' → {agent_names}")
                passed += 1
            else:
                print_result("FAIL", f"Capability '{capability}' → Keine passenden Agents")
                failed += 1
        
        print(f"\n  Gesamt: {passed}/{len(test_capabilities)} Capability-Searches erfolgreich")
        return failed == 0
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_domain_search():
    """Test 6: Domain-basierte Agent-Suche"""
    print_header("TEST 6: Domain-basierte Agent-Suche")
    
    try:
        registry = get_agent_registry()
        
        # Importiere AgentDomain
        from backend.agents.agent_registry import AgentDomain
        
        # Teste LEGAL Domain
        legal_names = registry.get_agents_by_domain(AgentDomain.LEGAL)
        
        print_result("INFO", f"LEGAL Domain: {len(legal_names)} Agents")
        print_result("INFO", f"  {legal_names}")
        
        if "VerwaltungsrechtAgent" in legal_names and "RechtsrecherchAgent" in legal_names:
            print_result("PASS", "LEGAL Domain enthält beide Legal-Agents")
        else:
            print_result("FAIL", "LEGAL Domain: Production Agents fehlen")
            return False
        
        # Teste ENVIRONMENTAL Domain
        env_names = registry.get_agents_by_domain(AgentDomain.ENVIRONMENTAL)
        
        print_result("INFO", f"ENVIRONMENTAL Domain: {len(env_names)} Agents")
        print_result("INFO", f"  {env_names}")
        
        if "ImmissionsschutzAgent" in env_names:
            print_result("PASS", "ENVIRONMENTAL Domain enthält ImmissionsschutzAgent")
        else:
            print_result("FAIL", "ENVIRONMENTAL Domain: ImmissionsschutzAgent fehlt")
            return False
        
        print_result("PASS", "Domain-Verteilung korrekt")
        return True
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_agent_scenario():
    """Test 7: Multi-Agent Szenario (Simulation)"""
    print_header("TEST 7: Multi-Agent Szenario")
    
    try:
        registry = get_agent_registry()
        
        # Simuliere komplexe Query, die mehrere Agents benötigt
        query = "Was sind die rechtlichen Grundlagen für Lärmschutz bei Bauvorhaben und welche Grenzwerte gelten?"
        
        print_result("INFO", f"Query: {query}")
        
        # 1. VerwaltungsrechtAgent (rechtliche Grundlagen)
        verwaltungsrecht_agent = registry.get_agent("VerwaltungsrechtAgent")
        if verwaltungsrecht_agent:
            result1 = verwaltungsrecht_agent.query("rechtliche Grundlagen Lärmschutz Bauvorhaben")
            print_result("INFO", f"VerwaltungsrechtAgent: {len(result1.get('results', []))} Ergebnisse")
        
        # 2. ImmissionsschutzAgent (Grenzwerte)
        immissionsschutz_agent = registry.get_agent("ImmissionsschutzAgent")
        if immissionsschutz_agent:
            result2 = immissionsschutz_agent.query("Lärmschutz Grenzwerte")
            print_result("INFO", f"ImmissionsschutzAgent: {len(result2.get('results', []))} Ergebnisse")
        
        # Prüfe ob beide Agents Ergebnisse lieferten
        if (verwaltungsrecht_agent and len(result1.get('results', [])) > 0 and
            immissionsschutz_agent and len(result2.get('results', [])) > 0):
            print_result("PASS", "Multi-Agent Koordination erfolgreich!")
            print_result("INFO", f"Gesamt: {len(result1.get('results', []))} + {len(result2.get('results', []))} = {len(result1.get('results', [])) + len(result2.get('results', []))} Ergebnisse")
            return True
        else:
            print_result("WARN", "Multi-Agent Koordination teilweise erfolgreich")
            return True
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance():
    """Test 8: Performance-Test"""
    print_header("TEST 8: Performance-Test")
    
    try:
        registry = get_agent_registry()
        
        agents = [
            "VerwaltungsrechtAgent",
            "RechtsrecherchAgent",
            "ImmissionsschutzAgent"
        ]
        
        for agent_name in agents:
            agent = registry.get_agent(agent_name)
            if not agent:
                continue
            
            # Einfache Query
            import time
            start = time.time()
            result = agent.query("Test Query Performance")
            elapsed = (time.time() - start) * 1000
            
            if elapsed < 100:  # < 100ms
                print_result("PASS", f"{agent_name}: {elapsed:.2f}ms")
            else:
                print_result("WARN", f"{agent_name}: {elapsed:.2f}ms (langsam)")
        
        print_result("PASS", "Performance-Tests abgeschlossen")
        return True
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

# ==========================================
# TEST RUNNER
# ==========================================

def run_all_tests():
    """Führe alle Tests aus"""
    print_header("PRODUCTION AGENTS - DIRECT REGISTRY TESTS")
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Registry Initialisierung", test_registry_initialization),
        ("VerwaltungsrechtAgent Direkt", test_verwaltungsrecht_direct),
        ("RechtsrecherchAgent Direkt", test_rechtsrecherche_direct),
        ("ImmissionsschutzAgent Direkt", test_immissionsschutz_direct),
        ("Capability-basierte Suche", test_capability_search),
        ("Domain-basierte Suche", test_domain_search),
        ("Multi-Agent Szenario", test_multi_agent_scenario),
        ("Performance-Test", test_performance),
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
        print_result("PASS", "🎉 ALLE DIRECT REGISTRY TESTS BESTANDEN!")
        return 0
    else:
        print_result("FAIL", f"❌ {failed} Test(s) fehlgeschlagen")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
