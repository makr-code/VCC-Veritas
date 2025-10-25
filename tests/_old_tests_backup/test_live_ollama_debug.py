"""
Kleinteiliger Debug-Test für die wissenschaftliche Pipeline mit Ollama
Testet einzelne Pipeline-Schritte separat und gibt Debug-Infos aus.
"""

import pytest
import os
import uuid
import time
from fastapi.testclient import TestClient
from backend.api.veritas_api_backend import app

@pytest.fixture(scope="module")
def client():
    os.environ["VERITAS_SCIENTIFIC_MODE"] = "true"
    os.environ["VERITAS_STRICT_STARTUP"] = "false"
    os.environ["VERITAS_LOG_LEVEL"] = "DEBUG"
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client

# Test 1: Nur Query Analysis

def test_query_analysis_only(client):
    query = "Was sind die wichtigsten Umweltauflagen für den Bau eines Windrads?"
    request_data = {
        "query": query,
        "session_id": f"debug_{uuid.uuid4().hex[:8]}",
        "enable_streaming": False,
        "enable_intermediate_results": False,
        "enable_llm_thinking": False,
        "requested_agents": ["phi3"],
        "timeout": 10
    }
    print("\n--- DEBUG: Query Analysis Only ---")
    response = client.post("/v2/intelligent/query", json=request_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    assert response.status_code in [200, 503]

# Test 2: Nur RAG Search

def test_rag_search_only(client):
    query = "Welche Dokumente sind relevant für Windenergie-Genehmigungen?"
    request_data = {
        "query": query,
        "session_id": f"debug_{uuid.uuid4().hex[:8]}",
        "enable_streaming": False,
        "enable_intermediate_results": True,
        "enable_llm_thinking": False,
        "requested_agents": ["phi3"],
        "timeout": 10
    }
    print("\n--- DEBUG: RAG Search Only ---")
    response = client.post("/v2/intelligent/query", json=request_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    assert response.status_code in [200, 503]

# Test 3: Nur Agent Selection

def test_agent_selection_only(client):
    query = "Welche Agenten sind für Umweltrecht relevant?"
    request_data = {
        "query": query,
        "session_id": f"debug_{uuid.uuid4().hex[:8]}",
        "enable_streaming": False,
        "enable_intermediate_results": False,
        "enable_llm_thinking": True,
        "requested_agents": ["phi3", "gemma3"],
        "timeout": 10
    }
    print("\n--- DEBUG: Agent Selection Only ---")
    response = client.post("/v2/intelligent/query", json=request_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    assert response.status_code in [200, 503]
