#!/usr/bin/env python3
"""
Frontend-Backend UDS3-Integrations-Test
Testet die Kommunikation zwischen Veritas Frontend und Backend mit UDS3
"""

import json
import os
import sys

# Setup Python-Pfade wie im Frontend
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "frontend"))
sys.path.insert(0, os.path.join(project_root, "backend"))
sys.path.insert(0, os.path.join(project_root, "shared"))
sys.path.insert(0, os.path.join(project_root, "uds3"))

# Backend URL
BACKEND_URL = "http://localhost:5000"


def test_frontend_uds3_imports():
    """Testet UDS3-Imports im Frontend"""
    print("🔍 Teste Frontend UDS3-Imports...")

    try:
        # UDS3 Core Imports (korrigiert)
        from uds3.uds3_core import UnifiedDatabaseStrategy, get_optimized_unified_strategy
        from uds3.uds3_security_quality import SecurityLevel

        print("✅ UDS3 Core Imports erfolgreich")

        # Teste Strategy-Instanziierung
        strategy = get_optimized_unified_strategy()
        print("✅ UDS3 Strategy-Instanziierung erfolgreich")

        # Teste create_secure_document_light direkt
        from uds3 import create_secure_document_light

        result = create_secure_document_light(
            {"file_path": "frontend_test.txt", "content": "Frontend UDS3-Test Content", "chunks": ["Frontend", "UDS3", "Test"]}
        )

        print(f"✅ UDS3 Direct Call erfolgreich: {result.get('success', False)}")

        return True, strategy

    except ImportError as e:
        print(f"❌ Frontend UDS3-Import Fehler: {e}")
        return False, None
    except Exception as e:
        print(f"⚠️ Frontend UDS3-Test Fehler: {e}")
        return False, None


def test_backend_communication():
    """Testet Backend-Kommunikation"""
    print("\n🔍 Teste Backend-Kommunikation...")

    try:
        import requests

        # Teste Root Endpoint
        response = requests.get(f"{BACKEND_URL}/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend erreichbar")
            print(f"   UDS3 verfügbar: {data.get('uds3_available', False)}")
            return True
        else:
            print(f"❌ Backend nicht erreichbar: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Backend-Kommunikation Fehler: {e}")
        return False


def simulate_frontend_backend_flow():
    """Simuliert Frontend-Backend UDS3-Flow"""
    print("\n🔍 Simuliere Frontend-Backend UDS3-Flow...")

    try:
        import requests

        # Simuliere Frontend-Request
        frontend_data = {"query": "UDS3 Integration Test vom Frontend", "mode": "UDS3", "security_level": "INTERNAL"}

        # 1. Teste UDS3 Query Endpoint
        query_data = {
            "query": frontend_data["query"],
            "query_type": "light",
            "filters": {"mode": frontend_data["mode"]},
            "security_context": frontend_data["security_level"],
        }

        response = requests.post(f"{BACKEND_URL}/uds3/query", json=query_data)

        if response.status_code == 200:
            result = response.json()
            print("✅ Frontend-Backend UDS3 Flow erfolgreich")
            print(f"   Success: {result.get('success', False)}")
            print(f"   Results: {len(result.get('results', []))}")
            return True
        else:
            print(f"❌ Frontend-Backend Flow Fehler: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Frontend-Backend Flow Exception: {e}")
        return False


def main():
    """Hauptfunktion"""
    print("🧪 VERITAS Frontend-Backend UDS3-Integration Test")
    print("=" * 60)

    # Test 1: Frontend UDS3-Imports
    frontend_success, strategy = test_frontend_uds3_imports()

    # Test 2: Backend-Kommunikation
    backend_success = test_backend_communication()

    # Test 3: Frontend-Backend Flow
    if frontend_success and backend_success:
        flow_success = simulate_frontend_backend_flow()
    else:
        flow_success = False
        print("\n⚠️ Überspringe Frontend-Backend Flow wegen vorherigen Fehlern")

    # Zusammenfassung
    print(f"\n{'='*60}")
    print("📊 INTEGRATION-TEST ZUSAMMENFASSUNG")
    print(f"{'='*60}")

    tests = [
        ("Frontend UDS3-Imports", frontend_success),
        ("Backend-Kommunikation", backend_success),
        ("Frontend-Backend Flow", flow_success),
    ]

    successful = sum(success for _, success in tests)
    total = len(tests)

    for test_name, success in tests:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")

    print(f"\nErfolgreiche Tests: {successful}/{total}")

    if successful == total:
        print("🎉 VOLLSTÄNDIGE INTEGRATION ERFOLGREICH!")
        print("✅ Frontend und Backend kommunizieren korrekt über UDS3")
    elif successful >= 2:
        print("⚠️ GRUNDLEGENDE INTEGRATION FUNKTIONIERT")
        print("🔧 Einige erweiterte Features benötigen noch Feintuning")
    else:
        print("❌ INTEGRATION PROBLEMATISCH")
        print("🛠️ Überprüfung der Konfiguration erforderlich")

    # UDS3-Empfehlungen
    print(f"\n📋 UDS3-EMPFEHLUNGEN:")
    if frontend_success:
        print("✅ Frontend UDS3-Integration ist bereit")
    else:
        print("🔧 Frontend: UDS3-Imports überprüfen")

    if backend_success:
        print("✅ Backend UDS3-API ist verfügbar")
    else:
        print("🔧 Backend: UDS3-Service starten")

    if flow_success:
        print("✅ End-to-End UDS3-Kommunikation funktioniert")
    else:
        print("🔧 Flow: API-Endpoints und Datenformate überprüfen")


if __name__ == "__main__":
    main()
