#!/usr/bin/env python3
"""
Test-Skript für UDS3-Integration im VERITAS Backend
Testet die neue UDS3-API und Frontend-Backend-Kommunikation
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Backend URL
BACKEND_URL = "http://localhost:5000"

def test_api_endpoint(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Testet einen API-Endpoint"""
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        return {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "data": response.json() if response.status_code == 200 else response.text,
            "url": url
        }
    except requests.exceptions.ConnectionError:
        return {"error": "Backend nicht erreichbar", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}

def print_test_result(test_name: str, result: Dict[str, Any]):
    """Druckt Testergebnis"""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"{'='*60}")
    
    if "error" in result:
        print(f"❌ FEHLER: {result['error']}")
        return False
    
    success = result.get("success", False)
    status = "✅ ERFOLGREICH" if success else f"❌ FEHLER (Status: {result['status_code']})"
    print(f"Status: {status}")
    print(f"URL: {result['url']}")
    
    if success and "data" in result:
        print(f"Response:")
        print(json.dumps(result["data"], indent=2, ensure_ascii=False))
    elif not success:
        print(f"Fehler-Response: {result.get('data', 'Keine Details')}")
    
    return success

def main():
    """Hauptfunktion für UDS3-Integration Tests"""
    print("🧪 VERITAS UDS3-Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Backend Status
    print("\n🔍 Teste Backend-Verfügbarkeit...")
    root_result = test_api_endpoint("/")
    if not print_test_result("Backend Root Endpoint", root_result):
        print("\n❌ Backend nicht verfügbar - Tests abgebrochen")
        sys.exit(1)
    
    # Test 2: UDS3 Status
    print("\n🔍 Teste UDS3-Status...")
    uds3_status_result = test_api_endpoint("/uds3/status")
    print_test_result("UDS3 Status Endpoint", uds3_status_result)
    
    # Test 3: Health Check
    print("\n🔍 Teste Health Check...")
    health_result = test_api_endpoint("/health")
    print_test_result("Health Check Endpoint", health_result)
    
    # Test 4: UDS3 Document Creation (Light)
    print("\n🔍 Teste UDS3 Dokument-Erstellung...")
    test_doc_data = {
        "file_path": "test_legal_document.txt",
        "content": "Testkontent für rechtliches Dokument mit UDS3 Integration. Dieses Dokument testet die sichere Dokumentenerstellung.",
        "chunks": [
            "Testkontent für rechtliches Dokument",
            "UDS3 Integration wird getestet",
            "Sichere Dokumentenerstellung funktioniert"
        ],
        "security_level": "INTERNAL",
        "metadata": {
            "title": "UDS3 Test Dokument",
            "author": "Integration Test",
            "rechtsgebiet": "Test",
            "keywords": ["UDS3", "Test", "Integration"]
        }
    }
    
    create_doc_result = test_api_endpoint("/uds3/documents", "POST", test_doc_data)
    doc_success = print_test_result("UDS3 Dokument-Erstellung", create_doc_result)
    
    # Test 5: UDS3 Query
    print("\n🔍 Teste UDS3 Query...")
    test_query_data = {
        "query": "Teste UDS3 Query-Funktionalität",
        "query_type": "light",
        "filters": {"test": True},
        "security_context": "INTERNAL"
    }
    
    query_result = test_api_endpoint("/uds3/query", "POST", test_query_data)
    query_success = print_test_result("UDS3 Query", query_result)
    
    # Ergebnis-Zusammenfassung
    print(f"\n{'='*60}")
    print("📊 TEST-ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    
    total_tests = 5
    successful_tests = sum([
        root_result.get("success", False),
        uds3_status_result.get("success", False),
        health_result.get("success", False),
        doc_success,
        query_success
    ])
    
    print(f"Erfolgreiche Tests: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("🎉 ALLE TESTS ERFOLGREICH!")
        print("✅ UDS3-Integration funktioniert korrekt")
    elif successful_tests >= 3:
        print("⚠️ GRUNDFUNKTIONEN VERFÜGBAR")
        print("🔧 Einige erweiterte Features benötigen noch Konfiguration")
    else:
        print("❌ INTEGRATION UNVOLLSTÄNDIG")
        print("🛠️ Backend-Konfiguration überprüfen")
    
    # UDS3-spezifische Informationen
    if uds3_status_result.get("success") and "data" in uds3_status_result:
        uds3_data = uds3_status_result["data"]
        print(f"\n📋 UDS3-Details:")
        print(f"   - UDS3 verfügbar: {uds3_data.get('uds3_available', 'Unknown')}")
        print(f"   - Strategy initialisiert: {uds3_data.get('strategy_initialized', 'Unknown')}")
        print(f"   - Multi-DB Distribution: {uds3_data.get('multi_db_distribution', 'Unknown')}")

if __name__ == "__main__":
    main()