#!/usr/bin/env python3
"""
Test: GenehmigungsAgent
=======================

Testet die wichtigsten Funktionen des neuen Agents:
- Initialisierung
- Query-Tests für alle Capabilities
- Fallback-Suche
- get_info()

Author: VERITAS Development Team
Date: 2025-10-16
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agents.veritas_api_agent_genehmigung import GenehmigungsAgent

def print_result(result_type, message):
    symbols = {"PASS": "✅", "FAIL": "❌", "INFO": "ℹ️", "WARN": "⚠️"}
    print(f"  {symbols.get(result_type, '•')} {message}")

def test_initialization():
    print("\n=== Test: Initialisierung ===")
    try:
        agent = GenehmigungsAgent()
        info = agent.get_info()
        print_result("PASS", f"Agent initialisiert: {info['name']} v{info['version']}")
        print_result("INFO", f"Capabilities: {info['capabilities']}")
        print_result("INFO", f"Wissensbasis-Einträge: {info['knowledge_base_size']}")
        return True
    except Exception as e:
        print_result("FAIL", f"Fehler: {e}")
        return False

def test_query_capabilities():
    print("\n=== Test: Query für Capabilities ===")
    agent = GenehmigungsAgent()
    passed = 0
    failed = 0
    for cap in agent.capabilities:
        result = agent.query(cap)
        if result["success"] and len(result["results"]) > 0:
            print_result("PASS", f"'{cap}' → {len(result['results'])} Ergebnisse (Konfidenz: {result['confidence']})")
            passed += 1
        else:
            print_result("FAIL", f"'{cap}' → Keine Ergebnisse")
            failed += 1
    print(f"  Gesamt: {passed}/{len(agent.capabilities)} Capabilities erfolgreich")
    return failed == 0

def test_fallback_query():
    print("\n=== Test: Fallback-Query ===")
    agent = GenehmigungsAgent()
    query = "VwVfG Fristen"
    result = agent.query(query)
    if result["success"] and len(result["results"]) > 0:
        print_result("PASS", f"Fallback-Query '{query}' → {len(result['results'])} Ergebnisse (Konfidenz: {result['confidence']})")
        return True
    else:
        print_result("FAIL", f"Fallback-Query '{query}' → Keine Ergebnisse")
        return False

def test_get_info():
    print("\n=== Test: get_info() ===")
    agent = GenehmigungsAgent()
    info = agent.get_info()
    if info["name"] == "GenehmigungsAgent" and info["domain"] == "LEGAL":
        print_result("PASS", "get_info() liefert korrekte Metadaten")
        return True
    else:
        print_result("FAIL", "get_info() liefert falsche Daten")
        return False

def run_all_tests():
    print("\n==============================")
    print("GenehmigungsAgent - Test Suite")
    print("==============================")
    tests = [
        ("Initialisierung", test_initialization),
        ("Query Capabilities", test_query_capabilities),
        ("Fallback Query", test_fallback_query),
        ("get_info()", test_get_info),
    ]
    passed = 0
    failed = 0
    for name, func in tests:
        try:
            if func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_result("FAIL", f"Test '{name}' abgebrochen: {e}")
            failed += 1
    print("\n==============================")
    print(f"Gesamt: {passed}/{len(tests)} Tests bestanden ({passed/len(tests)*100:.1f}%)")
    if failed == 0:
        print_result("PASS", "ALLE TESTS BESTANDEN!")
    else:
        print_result("FAIL", f"{failed} Test(s) fehlgeschlagen")

if __name__ == "__main__":
    run_all_tests()
