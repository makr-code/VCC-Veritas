#!/usr/bin/env python3
"""
Test: EmissionenMonitoringAgent
================================

Testet die wichtigsten Funktionen des neuen Agents:
- Initialisierung
- Query-Tests für alle Capabilities
- Fallback-Suche
- get_info()
- search_emissionen()
- search_bericht()

Author: VERITAS Development Team
Date: 2025-10-16
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agents.veritas_api_agent_emissionen_monitoring import EmissionenMonitoringAgent

def print_result(result_type, message):
    symbols = {"PASS": "✅", "FAIL": "❌", "INFO": "ℹ️", "WARN": "⚠️"}
    print(f"  {symbols.get(result_type, '•')} {message}")

def test_initialization():
    print("\n=== Test: Initialisierung ===")
    try:
        agent = EmissionenMonitoringAgent()
        info = agent.get_info()
        
        assert info["agent_id"] == "EmissionenMonitoringAgent"
        assert info["version"] == "v1.0"
        assert len(info["capabilities"]) > 0
        
        print_result("PASS", f"Agent initialisiert: {info['agent_id']} {info['version']}")
        print_result("INFO", f"Capabilities: {info['capabilities']}")
        print_result("INFO", f"Wissensbasis-Einträge: {len(info['knowledge_base'])}")
        return True
    except Exception as e:
        print_result("FAIL", f"Initialisierung fehlgeschlagen: {e}")
        return False

def test_query_capabilities():
    print("\n=== Test: Query für Capabilities ===")
    agent = EmissionenMonitoringAgent()
    success_count = 0
    total_count = 0
    
    for cap in agent.capabilities:
        total_count += 1
        result = agent.query(cap)
        if any(cap in r.get("capability", "") for r in result):
            confidence = result[0].get("confidence", 0) if result else 0
            print_result("PASS", f"'{cap}' → {len(result)} Ergebnisse (Konfidenz: {confidence})")
            success_count += 1
        else:
            print_result("FAIL", f"'{cap}' → Keine Ergebnisse")
    
    print_result("INFO", f"Gesamt: {success_count}/{total_count} Capabilities erfolgreich")
    return success_count == total_count

def test_fallback_query():
    print("\n=== Test: Fallback-Query ===")
    agent = EmissionenMonitoringAgent()
    
    result = agent.query("TA Luft")
    if result and len(result) > 0:
        print_result("PASS", f"Fallback-Query 'TA Luft' → {len(result)} Ergebnisse (Konfidenz: {result[0].get('confidence', 0)})")
        return True
    else:
        print_result("FAIL", "Fallback-Query lieferte keine Ergebnisse")
        return False

def test_get_info():
    print("\n=== Test: get_info() ===")
    agent = EmissionenMonitoringAgent()
    info = agent.get_info()
    
    if info["agent_id"] == "EmissionenMonitoringAgent" and len(info["capabilities"]) > 0:
        print_result("PASS", "get_info() liefert korrekte Metadaten")
        return True
    else:
        print_result("FAIL", "get_info() lieferte unvollständige Daten")
        return False

def test_search_methods():
    print("\n=== Test: Spezifische Suchmethoden ===")
    agent = EmissionenMonitoringAgent()
    results = []
    
    try:
        emissionen_result = agent.search_emissionen("NO2 Grenzwertüberschreitung")
        if "NO2 Grenzwertüberschreitung" in emissionen_result:
            print_result("PASS", f"search_emissionen() funktioniert")
            results.append(True)
        else:
            print_result("FAIL", "search_emissionen() fehlgeschlagen")
            results.append(False)
    except Exception as e:
        print_result("FAIL", f"search_emissionen() Fehler: {e}")
        results.append(False)
    
    try:
        bericht_result = agent.search_bericht("Jahresbericht 2024")
        if "Jahresbericht 2024" in bericht_result:
            print_result("PASS", f"search_bericht() funktioniert")
            results.append(True)
        else:
            print_result("FAIL", "search_bericht() fehlgeschlagen")
            results.append(False)
    except Exception as e:
        print_result("FAIL", f"search_bericht() Fehler: {e}")
        results.append(False)
    
    return all(results)

def main():
    print("=" * 30)
    print("EmissionenMonitoringAgent - Test Suite")
    print("=" * 30)
    
    tests = [
        test_initialization,
        test_query_capabilities,
        test_fallback_query,
        test_get_info,
        test_search_methods
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 30)
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Gesamt: {passed}/{total} Tests bestanden ({percentage:.1f}%)")
    
    if passed == total:
        print_result("PASS", "ALLE TESTS BESTANDEN!")
    else:
        print_result("FAIL", f"{total - passed} Test(s) fehlgeschlagen")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

