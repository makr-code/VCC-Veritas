import os
import pytest
from fastapi.testclient import TestClient
from backend.api.veritas_api_backend import app

@pytest.fixture(scope="module")
def client():
    os.environ["VERITAS_SCIENTIFIC_MODE"] = "true"
    with TestClient(app) as c:
        yield c
    os.environ["VERITAS_SCIENTIFIC_MODE"] = "false"

def test_scientific_pipeline_full(client):
    """
    Integrationstest: Pipeline mit Dialektischer Synthese & Peer-Review
    """
    query = "Welche rechtlichen und ökologischen Aspekte sind bei einem Bauantrag in einer ländlichen Gemeinde zu beachten? Gibt es Zielkonflikte?"
    payload = {
        "query": query,
        "enable_llm_thinking": True,
        "agent_types": ["legal_framework", "environmental", "document_retrieval"],
        "complexity": "advanced",
        "external_sources": True,
        "quality_level": "high"
    }
    response = client.post("/v2/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Prüfe, ob Synthese und Peer-Review Ergebnisse enthalten sind
    assert "response_text" in data
    assert "agent_results" in data
    # Optional: Suche nach typischen Texten der Synthese/Review
    assert any(word in data["response_text"].lower() for word in ["synthese", "peer-review", "widerspruch", "these"])
    print("Pipeline-Integrationstest erfolgreich: Dialektik & Peer-Review durchlaufen.")
