#!/usr/bin/env python3
"""
Test: VerwaltungsrechtAgent
===========================

Test-Suite für den VerwaltungsrechtAgent.

Test-Szenarien:
1. Baurecht-Anfragen (§ 34 BauGB, § 35 BauGB, etc.)
2. Immissionsschutzrecht-Anfragen (§ 5 BImSchG, etc.)
3. Genehmigungsverfahren
4. Kategorisierung verschiedener Anfragen
5. Wissensbasis-Suche

Author: VERITAS Development Team
Date: 2025-10-16
"""

import sys
import os
import logging
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agents.veritas_api_agent_verwaltungsrecht import (
    VerwaltungsrechtAgent,
    VerwaltungsrechtAgentConfig,
    VerwaltungsrechtQueryRequest,
    VerwaltungsrechtCategory
)

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
# TEST CASES
# ==========================================

def test_agent_initialization():
    """Test 1: Agent-Initialisierung"""
    print_header("TEST 1: Agent-Initialisierung")
    
    try:
        agent = VerwaltungsrechtAgent()
        assert agent is not None, "Agent sollte nicht None sein"
        assert agent.name == "verwaltungsrecht_agent", f"Agent-Name falsch: {agent.name}"
        assert agent.version == "1.0", f"Version falsch: {agent.version}"
        
        # Prüfe Wissensbasis
        assert len(agent.baurecht_knowledge) > 0, "Baurecht-Wissensbasis leer"
        assert len(agent.immissionsschutzrecht_knowledge) > 0, "Immissionsschutz-Wissensbasis leer"
        assert len(agent.genehmigungsverfahren_knowledge) > 0, "Genehmigungsverfahren-Wissensbasis leer"
        
        print_result("PASS", "Agent erfolgreich initialisiert")
        print_result("INFO", f"Baurecht-Einträge: {len(agent.baurecht_knowledge)}")
        print_result("INFO", f"Immissionsschutz-Einträge: {len(agent.immissionsschutzrecht_knowledge)}")
        print_result("INFO", f"Genehmigungsverfahren-Einträge: {len(agent.genehmigungsverfahren_knowledge)}")
        return True
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

def test_baurecht_queries():
    """Test 2: Baurecht-Anfragen"""
    print_header("TEST 2: Baurecht-Anfragen")
    
    agent = VerwaltungsrechtAgent()
    
    test_cases = [
        {
            "query": "Was bedeutet § 34 BauGB?",
            "expected_category": VerwaltungsrechtCategory.BAURECHT,
            "expected_min_results": 1,
            "description": "§ 34 BauGB Suche"
        },
        {
            "query": "Welche Regelungen gibt es für Bauen im Außenbereich?",
            "expected_category": VerwaltungsrechtCategory.BAURECHT,
            "expected_min_results": 1,
            "description": "Außenbereich-Suche"
        },
        {
            "query": "Zulässigkeit von Vorhaben innerhalb der im Zusammenhang bebauten Ortsteile",
            "expected_category": VerwaltungsrechtCategory.BAURECHT,
            "expected_min_results": 1,
            "description": "Bebauung-Suche"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  Test Case {i}: {test_case['description']}")
        print(f"  Query: {test_case['query']}")
        
        request = VerwaltungsrechtQueryRequest(
            query_id=f"test_baurecht_{i}",
            query_text=test_case['query']
        )
        
        response = agent.process_query(request)
        
        # Prüfungen
        category_ok = response.category == test_case['expected_category']
        results_ok = len(response.results) >= test_case['expected_min_results']
        success_ok = response.success
        
        if category_ok and results_ok and success_ok:
            print_result("PASS", f"Kategorie: {response.category.value}, Ergebnisse: {len(response.results)}")
            passed += 1
        else:
            print_result("FAIL", f"Kategorie: {response.category.value} (erwartet: {test_case['expected_category'].value}), Ergebnisse: {len(response.results)}")
            failed += 1
        
        # Zeige Top-Ergebnis
        if response.results:
            top_result = response.results[0]
            print_result("INFO", f"Top-Result: {top_result.get('paragraph', top_result.get('verfahren', 'N/A'))}")
    
    print(f"\n  Gesamt: {passed}/{len(test_cases)} Tests bestanden")
    return failed == 0

def test_immissionsschutzrecht_queries():
    """Test 3: Immissionsschutzrecht-Anfragen"""
    print_header("TEST 3: Immissionsschutzrecht-Anfragen")
    
    agent = VerwaltungsrechtAgent()
    
    test_cases = [
        {
            "query": "Welche Pflichten haben Betreiber nach § 5 BImSchG?",
            "expected_category": VerwaltungsrechtCategory.IMMISSIONSSCHUTZRECHT,
            "expected_min_results": 1,
            "description": "§ 5 BImSchG Suche"
        },
        {
            "query": "Was bedeutet Vorsorgepflicht im Immissionsschutzrecht?",
            "expected_category": VerwaltungsrechtCategory.IMMISSIONSSCHUTZRECHT,
            "expected_min_results": 1,
            "description": "Vorsorgepflicht-Suche"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  Test Case {i}: {test_case['description']}")
        print(f"  Query: {test_case['query']}")
        
        request = VerwaltungsrechtQueryRequest(
            query_id=f"test_imsch_{i}",
            query_text=test_case['query']
        )
        
        response = agent.process_query(request)
        
        # Prüfungen
        category_ok = response.category == test_case['expected_category']
        results_ok = len(response.results) >= test_case['expected_min_results']
        success_ok = response.success
        
        if category_ok and results_ok and success_ok:
            print_result("PASS", f"Kategorie: {response.category.value}, Ergebnisse: {len(response.results)}")
            passed += 1
        else:
            print_result("FAIL", f"Kategorie: {response.category.value}, Ergebnisse: {len(response.results)}")
            failed += 1
        
        # Zeige Top-Ergebnis
        if response.results:
            top_result = response.results[0]
            print_result("INFO", f"Top-Result: {top_result.get('paragraph', 'N/A')}")
    
    print(f"\n  Gesamt: {passed}/{len(test_cases)} Tests bestanden")
    return failed == 0

def test_genehmigungsverfahren_queries():
    """Test 4: Genehmigungsverfahren-Anfragen"""
    print_header("TEST 4: Genehmigungsverfahren-Anfragen")
    
    agent = VerwaltungsrechtAgent()
    
    test_cases = [
        {
            "query": "Welche Unterlagen brauche ich für eine Baugenehmigung?",
            "expected_category": VerwaltungsrechtCategory.GENEHMIGUNGSRECHT,
            "expected_min_results": 1,
            "description": "Baugenehmigung-Unterlagen"
        },
        {
            "query": "Was ist eine immissionsschutzrechtliche Genehmigung?",
            "expected_category": VerwaltungsrechtCategory.GENEHMIGUNGSRECHT,
            "expected_min_results": 1,
            "description": "Immissionsschutzrechtliche Genehmigung"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  Test Case {i}: {test_case['description']}")
        print(f"  Query: {test_case['query']}")
        
        request = VerwaltungsrechtQueryRequest(
            query_id=f"test_genehmigung_{i}",
            query_text=test_case['query']
        )
        
        response = agent.process_query(request)
        
        # Prüfungen (Genehmigungsrecht kann auch zu anderen Kategorien passen)
        results_ok = len(response.results) >= test_case['expected_min_results']
        success_ok = response.success
        
        if results_ok and success_ok:
            print_result("PASS", f"Kategorie: {response.category.value}, Ergebnisse: {len(response.results)}")
            passed += 1
        else:
            print_result("FAIL", f"Ergebnisse: {len(response.results)} (erwartet: >= {test_case['expected_min_results']})")
            failed += 1
        
        # Zeige Top-Ergebnis
        if response.results:
            top_result = response.results[0]
            print_result("INFO", f"Top-Result: {top_result.get('verfahren', top_result.get('paragraph', 'N/A'))}")
    
    print(f"\n  Gesamt: {passed}/{len(test_cases)} Tests bestanden")
    return failed == 0

def test_category_detection():
    """Test 5: Kategorie-Erkennung"""
    print_header("TEST 5: Kategorie-Erkennung")
    
    agent = VerwaltungsrechtAgent()
    
    test_cases = [
        ("Baurecht und Baugenehmigung", VerwaltungsrechtCategory.BAURECHT),
        ("Immissionsschutzrecht BImSchG", VerwaltungsrechtCategory.IMMISSIONSSCHUTZRECHT),
        ("Bebauungsplan und Flächennutzungsplan", VerwaltungsrechtCategory.PLANUNGSRECHT),
        ("Verwaltungsakt und Widerspruch", VerwaltungsrechtCategory.VERWALTUNGSVERFAHREN),
        ("Genehmigungsverfahren und Antrag", VerwaltungsrechtCategory.GENEHMIGUNGSRECHT),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_category in test_cases:
        detected = agent._detect_category(query)
        
        if detected == expected_category:
            print_result("PASS", f"{query} → {detected.value}")
            passed += 1
        else:
            print_result("FAIL", f"{query} → {detected.value} (erwartet: {expected_category.value})")
            failed += 1
    
    print(f"\n  Gesamt: {passed}/{len(test_cases)} Tests bestanden")
    return failed == 0

def test_simplified_query_method():
    """Test 6: Vereinfachte query() Methode"""
    print_header("TEST 6: Vereinfachte query() Methode (Registry-Kompatibilität)")
    
    agent = VerwaltungsrechtAgent()
    
    try:
        # Test einfache query() Methode
        result = agent.query("Was bedeutet § 34 BauGB?")
        
        assert "success" in result, "Result sollte 'success' enthalten"
        assert "results" in result, "Result sollte 'results' enthalten"
        assert result["success"] == True, "Query sollte erfolgreich sein"
        assert len(result["results"]) > 0, "Query sollte Ergebnisse liefern"
        
        print_result("PASS", "query() Methode funktioniert")
        print_result("INFO", f"Ergebnisse: {len(result['results'])}")
        print_result("INFO", f"Confidence: {result.get('confidence', 0):.2f}")
        print_result("INFO", f"Processing Time: {result.get('processing_time_ms', 0)}ms")
        
        return True
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

def test_agent_info():
    """Test 7: Agent-Info abrufen"""
    print_header("TEST 7: Agent-Info abrufen")
    
    agent = VerwaltungsrechtAgent()
    
    try:
        info = agent.get_info()
        
        assert "agent_id" in info, "Info sollte 'agent_id' enthalten"
        assert "name" in info, "Info sollte 'name' enthalten"
        assert "version" in info, "Info sollte 'version' enthalten"
        assert "domain" in info, "Info sollte 'domain' enthalten"
        assert "capabilities" in info, "Info sollte 'capabilities' enthalten"
        
        print_result("PASS", "get_info() funktioniert")
        print_result("INFO", f"Agent: {info['name']} v{info['version']}")
        print_result("INFO", f"Domain: {info['domain']}")
        print_result("INFO", f"Capabilities: {len(info['capabilities'])}")
        
        return True
        
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

# ==========================================
# TEST RUNNER
# ==========================================

def run_all_tests():
    """Führe alle Tests aus"""
    print_header("VERITAS VERWALTUNGSRECHT AGENT - TEST SUITE")
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Agent-Initialisierung", test_agent_initialization),
        ("Baurecht-Anfragen", test_baurecht_queries),
        ("Immissionsschutzrecht-Anfragen", test_immissionsschutzrecht_queries),
        ("Genehmigungsverfahren-Anfragen", test_genehmigungsverfahren_queries),
        ("Kategorie-Erkennung", test_category_detection),
        ("Vereinfachte query() Methode", test_simplified_query_method),
        ("Agent-Info", test_agent_info),
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
        print_result("PASS", "🎉 ALLE TESTS BESTANDEN!")
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
