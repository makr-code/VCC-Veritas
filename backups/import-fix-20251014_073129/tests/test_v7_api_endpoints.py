"""
Test Suite für v7 API Endpoints

Testet:
- /api/v7/query (Scientific Method Query)
- /api/v7/capabilities (System Capabilities)

Author: VERITAS v7.0
Date: 12. Oktober 2025
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient


def test_v7_capabilities_endpoint():
    """
    Test: /api/v7/capabilities Endpoint
    
    Prüft:
    - Response Status 200
    - Korrekte JSON-Struktur
    - Version = 7.0.0
    - Alle erforderlichen Felder vorhanden
    """
    from backend.api.veritas_api_backend_streaming import app
    
    client = TestClient(app)
    
    # Request
    response = client.get("/api/v7/capabilities")
    
    # Assertions
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    
    # Required fields
    assert "version" in data
    assert "supervisor_enabled" in data
    assert "supervisor_available" in data
    assert "phases" in data
    assert "features" in data
    assert "uds3_available" in data
    assert "agent_orchestrator_available" in data
    assert "streaming_enabled" in data
    assert "method_id" in data
    assert "config_version" in data
    
    # Version check
    assert data["version"] == "7.0.0"
    
    # Phases check
    assert isinstance(data["phases"], list)
    assert len(data["phases"]) > 0, "Phases list should not be empty"
    
    # Features check
    assert isinstance(data["features"], dict)
    required_features = [
        "scientific_method",
        "supervisor",
        "agent_coordination",
        "uds3_search",
        "streaming",
        "rag_semantic",
        "rag_graph",
        "llm_reasoning"
    ]
    
    for feature in required_features:
        assert feature in data["features"], f"Feature '{feature}' missing"
    
    print("✅ v7 Capabilities Endpoint Test PASSED")
    print(f"   Version: {data['version']}")
    print(f"   Supervisor Enabled: {data['supervisor_enabled']}")
    print(f"   Phases: {len(data['phases'])}")
    print(f"   Method ID: {data['method_id']}")
    print(f"   Config Version: {data['config_version']}")
    
    return data


def test_v7_query_endpoint():
    """
    Test: /api/v7/query Endpoint
    
    Prüft:
    - Response Status 200
    - Korrekte JSON-Struktur
    - Answer vorhanden
    - Confidence zwischen 0-1
    - Scientific Process vorhanden
    """
    from backend.api.veritas_api_backend_streaming import app
    
    client = TestClient(app)
    
    # Request
    request_data = {
        "query": "Brauche ich eine Baugenehmigung für einen Carport?",
        "user_id": "test_user_123",
        "context": {"test": True},
        "enable_streaming": False
    }
    
    response = client.post("/api/v7/query", json=request_data)
    
    # Assertions
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    
    # Required fields
    assert "answer" in data
    assert "confidence" in data
    assert "scientific_process" in data
    assert "execution_time_ms" in data
    assert "metadata" in data
    
    # Answer check
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0, "Answer should not be empty"
    
    # Confidence check
    assert isinstance(data["confidence"], (int, float))
    assert 0.0 <= data["confidence"] <= 1.0, "Confidence must be between 0 and 1"
    
    # Scientific Process check
    assert isinstance(data["scientific_process"], dict)
    
    # Metadata check
    assert isinstance(data["metadata"], dict)
    assert "query_count" in data["metadata"]
    assert "method_id" in data["metadata"]
    
    print("✅ v7 Query Endpoint Test PASSED")
    print(f"   Answer Length: {len(data['answer'])} chars")
    print(f"   Confidence: {data['confidence']:.2f}")
    print(f"   Execution Time: {data['execution_time_ms']:.0f}ms")
    print(f"   Query Count: {data['metadata']['query_count']}")
    
    return data


def test_v7_streaming_not_implemented():
    """
    Test: /api/v7/query mit Streaming (sollte 501 zurückgeben)
    """
    from backend.api.veritas_api_backend_streaming import app
    
    client = TestClient(app)
    
    # Request with streaming enabled
    request_data = {
        "query": "Test query",
        "enable_streaming": True
    }
    
    response = client.post("/api/v7/query", json=request_data)
    
    # Should return 501 Not Implemented
    assert response.status_code == 501, f"Expected 501, got {response.status_code}"
    
    print("✅ v7 Streaming Not Implemented Test PASSED")


def test_v7_capabilities_phase_structure():
    """
    Test: Phase-Struktur in Capabilities
    
    Prüft, dass jede Phase die erforderlichen Felder hat
    """
    from backend.api.veritas_api_backend_streaming import app
    
    client = TestClient(app)
    response = client.get("/api/v7/capabilities")
    
    assert response.status_code == 200
    data = response.json()
    
    for phase in data["phases"]:
        # Required phase fields
        assert "id" in phase, "Phase must have 'id'"
        assert "name" in phase, "Phase must have 'name'"
        assert "type" in phase, "Phase must have 'type'"
        assert "optional" in phase, "Phase must have 'optional'"
        
        # Type check
        assert isinstance(phase["id"], str)
        assert isinstance(phase["name"], str)
        assert isinstance(phase["type"], str)
        assert isinstance(phase["optional"], bool)
        
        # Type should be one of: llm, supervisor, agent_coordination, agent_coordinator
        valid_types = ["llm", "supervisor", "agent_coordination", "agent_coordinator"]
        assert phase["type"] in valid_types, \
            f"Invalid phase type: {phase['type']} (expected one of {valid_types})"
    
    print(f"✅ v7 Phase Structure Test PASSED ({len(data['phases'])} phases validated)")


def test_v7_error_handling():
    """
    Test: Error Handling bei fehlerhaften Requests
    """
    from backend.api.veritas_api_backend_streaming import app
    
    client = TestClient(app)
    
    # Test 1: Missing query field
    response = client.post("/api/v7/query", json={})
    assert response.status_code == 422, "Should return 422 for missing fields"
    
    # Test 2: Invalid query type
    response = client.post("/api/v7/query", json={"query": 123})
    assert response.status_code == 422, "Should return 422 for invalid types"
    
    print("✅ v7 Error Handling Test PASSED")


# ===== INTEGRATION TEST =====

async def integration_test_full_workflow():
    """
    Integration Test: Vollständiger v7 API Workflow
    
    1. Capabilities abrufen
    2. Query senden
    3. Response validieren
    """
    from backend.api.veritas_api_backend_streaming import app
    
    client = TestClient(app)
    
    print("\n" + "="*70)
    print("v7 API INTEGRATION TEST - Full Workflow")
    print("="*70)
    
    # Step 1: Get Capabilities
    print("\n[1/3] Abrufen der v7 Capabilities...")
    capabilities_response = client.get("/api/v7/capabilities")
    assert capabilities_response.status_code == 200
    
    capabilities = capabilities_response.json()
    print(f"      ✅ Version: {capabilities['version']}")
    print(f"      ✅ Supervisor: {capabilities['supervisor_enabled']}")
    print(f"      ✅ Phasen: {len(capabilities['phases'])}")
    print(f"      ✅ Features: {sum(1 for v in capabilities['features'].values() if v)}/{len(capabilities['features'])}")
    
    # Step 2: Send Query
    print("\n[2/3] Senden einer Test-Query...")
    query_request = {
        "query": "Wie funktioniert der Baugenehmigungsprozess in Baden-Württemberg?",
        "user_id": "integration_test_user",
        "context": {"test_mode": True}
    }
    
    query_response = client.post("/api/v7/query", json=query_request)
    assert query_response.status_code == 200
    
    result = query_response.json()
    print(f"      ✅ Antwort erhalten: {len(result['answer'])} Zeichen")
    print(f"      ✅ Confidence: {result['confidence']:.2%}")
    print(f"      ✅ Execution Time: {result['execution_time_ms']:.0f}ms")
    
    # Step 3: Validate Response
    print("\n[3/3] Validierung der Response...")
    
    # Check scientific process
    scientific_process = result["scientific_process"]
    phase_count = len(scientific_process)
    print(f"      ✅ Scientific Process Phasen: {phase_count}")
    
    # Check metadata
    metadata = result["metadata"]
    print(f"      ✅ Method ID: {metadata['method_id']}")
    print(f"      ✅ Query Count: {metadata['query_count']}")
    
    print("\n" + "="*70)
    print("✅ INTEGRATION TEST COMPLETE - ALL CHECKS PASSED")
    print("="*70 + "\n")
    
    return {
        "capabilities": capabilities,
        "query_result": result
    }


# ===== MAIN TEST RUNNER =====

if __name__ == "__main__":
    print("\n" + "="*70)
    print("VERITAS v7 API ENDPOINT TEST SUITE")
    print("="*70 + "\n")
    
    # Run unit tests
    try:
        print("[TEST 1/6] v7 Capabilities Endpoint...")
        test_v7_capabilities_endpoint()
        print()
        
        print("[TEST 2/6] v7 Query Endpoint...")
        test_v7_query_endpoint()
        print()
        
        print("[TEST 3/6] v7 Streaming Not Implemented...")
        test_v7_streaming_not_implemented()
        print()
        
        print("[TEST 4/6] v7 Capabilities Phase Structure...")
        test_v7_capabilities_phase_structure()
        print()
        
        print("[TEST 5/6] v7 Error Handling...")
        test_v7_error_handling()
        print()
        
        print("[TEST 6/6] v7 Integration Test (Full Workflow)...")
        asyncio.run(integration_test_full_workflow())
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED - v7 API IS READY")
        print("="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
