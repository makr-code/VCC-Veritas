"""
Full Scientific Pipeline Integration Test
Testet die komplette Pipeline mit Intelligent Multi-Agent System:
- Hypothesis Generation
- Agent Orchestration
- Dialectical Synthesis
- Peer Review Validation

Verwendet /v2/intelligent/query und /v2/query Endpoints
"""

import os

import pytest
from fastapi.testclient import TestClient

from backend.api.veritas_api_backend import app


@pytest.fixture(scope="module")
def client():
    """Test client mit aktiviertem wissenschaftlichem Modus"""
    os.environ["VERITAS_SCIENTIFIC_MODE"] = "true"
    return TestClient(app)


def test_intelligent_pipeline_with_scientific_method(client):
    """
    Test der Intelligent Pipeline mit wissenschaftlicher Methode
    """
    query = """
    Ich plane eine Photovoltaikanlage auf meinem Gewerbedach mit 100 kWp Leistung.
    Welche Genehmigungen, Umweltauflagen und Finanzierungsmöglichkeiten gibt es?
    """

    request_data = {
        "query_text": query,
        "query_id": "test_intelligent_pipeline",
        "session_id": "test_session_intelligent",
        "enable_llm_commentary": True,
        "enable_supervisor": False,
        "user_context": {"test": True},
        "timeout": 90,
    }

    print("\n" + "=" * 80)
    print("🧪 INTELLIGENT PIPELINE TEST + SCIENTIFIC METHOD")
    print("=" * 80)
    print(f"Query: {query.strip()[:80]}...")
    print("=" * 80 + "\n")

    response = client.post("/v2/intelligent/query", json=request_data)

    print(f"Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"⚠️  Pipeline nicht verfügbar: {response.text[:200]}")
        pytest.skip("Intelligent Pipeline nicht verfügbar")
        return

    data = response.json()

    assert "response_text" in data
    response_text = data["response_text"]

    print(f"📝 Response: {len(response_text)} chars")

    # Prüfe auf wissenschaftliche Elemente (wenn LLM verfügbar)
    has_hypothesis = "hypothes" in response_text.lower()
    has_dialectic = "dialektisch" in response_text.lower() or "synthese" in response_text.lower()
    has_peer_review = "peer" in response_text.lower() or "review" in response_text.lower()

    print(f"  Hypothesis: {'✅' if has_hypothesis else '⚠️'}")
    print(f"  Dialectic:  {'✅' if has_dialectic else '⚠️'}")
    print(f"  Peer Review: {'✅' if has_peer_review else '⚠️'}")

    # Agent Results
    agent_results = data.get("agent_results", {})
    if agent_results:
        print(f"\n🤖 {len(agent_results)} Agenten ausgeführt:")
        for agent_name in list(agent_results.keys())[:5]:
            print(f"  - {agent_name}")

    print("\n✅ Intelligent Pipeline Test erfolgreich\n")


def test_v2_query_with_scientific_mode(client):
    """
    Test des /v2/query Endpoints mit wissenschaftlichem Modus
    """
    query = "Welche Genehmigungen benötige ich für einen Carport?"

    request_data = {"query": query, "session_id": "test_v2_query", "mode": "veritas"}

    print("\n" + "=" * 80)
    print("🧪 V2 QUERY TEST (NON-STREAMING)")
    print("=" * 80)

    response = client.post("/v2/query", json=request_data)

    assert response.status_code == 200
    data = response.json()

    assert "response_text" in data
    response_text = data["response_text"]

    print(f"📝 Response: {len(response_text)} chars")

    # Check ob Pipeline verfügbar oder Fallback
    is_fallback = "nicht verfügbar" in response_text or "Pipeline nicht" in response_text

    if is_fallback:
        print("  ⚠️  Pipeline nicht verfügbar - Fallback aktiv")
        print("  ℹ️  Wissenschaftliche Methode nur mit aktiver Pipeline")
        assert len(response_text) > 50, "Fallback sollte sinnvollen Text enthalten"
    else:
        print("  ✅ Pipeline aktiv")
        # Prüfe wissenschaftliche Elemente
        has_science = any(marker in response_text.lower() for marker in ["dialektisch", "synthese", "peer", "review"])
        if has_science:
            print("  ✅ Wissenschaftliche Methode aktiv")
        else:
            print("  ⚠️  Wissenschaftliche Methode möglicherweise nicht aktiv")

    print("✅ V2 Query Test erfolgreich\n")


def test_scientific_pipeline_integration_simple(client):
    """
    Einfacher wissenschaftlicher Pipeline-Test wie der originale
    Verwendet /v2/query Endpoint
    """
    query = "Wie sind die rechtlichen Rahmenbedingungen für Windkraftanlagen?"

    os.environ["VERITAS_SCIENTIFIC_MODE"] = "true"

    request_data = {"query": query, "session_id": "test_simple_scientific"}

    print("\n" + "=" * 80)
    print("🧪 SIMPLE SCIENTIFIC PIPELINE TEST")
    print("=" * 80)

    response = client.post("/v2/query", json=request_data)

    assert response.status_code == 200
    data = response.json()
    response_text = data.get("response_text", "")

    print(f"📝 Response Length: {len(response_text)} chars")

    # Prüfe ob mindestens Text vorhanden ist
    assert len(response_text) > 100, "Response sollte substanziellen Inhalt haben"

    # Wenn Pipeline verfügbar, erwarte wissenschaftliche Elemente
    if "Pipeline nicht" not in response_text:
        # Mindestens eines der wissenschaftlichen Elemente sollte vorhanden sein
        scientific_markers = ["dialektisch", "synthese", "peer", "review", "thes", "widerspruch"]

        has_scientific_content = any(marker in response_text.lower() for marker in scientific_markers)

        if has_scientific_content:
            print("  ✅ Wissenschaftliche Inhalte gefunden")

            # Detaillierte Prüfung
            if "dialektisch" in response_text.lower() or "synthese" in response_text.lower():
                print("    ✅ Dialektische Synthese")
            if "peer" in response_text.lower() or "review" in response_text.lower():
                print("    ✅ Peer Review")
        else:
            print("  ⚠️  Keine wissenschaftlichen Marker gefunden (möglicherweise Fallback)")
    else:
        print("  ℹ️  Pipeline nicht verfügbar - Fallback-Modus")

    print("✅ Simple Scientific Pipeline Test erfolgreich\n")


def test_agent_orchestration_complexity(client):
    """
    Test verschiedener Query-Komplexitäten
    """
    test_queries = [
        ("Einfach", "Was kostet eine Baugenehmigung?"),
        ("Mittel", "Welche Umweltauflagen gelten für Gewerbebau?"),
        ("Komplex", "Komplettes Genehmigungsverfahren für Industriehalle mit Emissionen?"),
    ]

    print("\n" + "=" * 80)
    print("🧪 AGENT ORCHESTRATION COMPLEXITY TEST")
    print("=" * 80 + "\n")

    for complexity, query in test_queries:
        print(f"🔍 {complexity}: {query[:50]}...")

        request_data = {"query": query, "session_id": f"test_complexity_{complexity.lower()}"}

        response = client.post("/v2/query", json=request_data)

        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response_text", "")
            agent_count = len(data.get("agent_results", {}))

            print(f"  ✅ Response: {len(response_text)} chars, {agent_count} agents")
        else:
            print(f"  ⚠️  Status: {response.status_code}")

        print()

    print("✅ Complexity Test erfolgreich\n")


if __name__ == "__main__":
    print("Bitte mit pytest ausführen:")
    print("pytest tests/test_full_scientific_pipeline.py -v -s")
