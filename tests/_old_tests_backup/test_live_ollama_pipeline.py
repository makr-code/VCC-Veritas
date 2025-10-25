"""
Live Full-Pipeline Test mit Ollama Integration
Testet die komplette wissenschaftliche Pipeline mit echten LLM-Calls:
- Hypothesis Generation mit llama3.1
- Dialectical Synthesis mit LLM
- Peer Review mit Multi-LLM (llama3.1, phi3, gemma3)
- Alle Agenten mit Intelligent Pipeline
"""

import pytest
import os
import time
import uuid
import requests
from fastapi.testclient import TestClient
from backend.api.veritas_api_backend import app


@pytest.fixture(scope="module")
def client():
    """Test client mit aktiviertem wissenschaftlichem Modus und Lifespan"""
    os.environ["VERITAS_SCIENTIFIC_MODE"] = "true"
    os.environ["VERITAS_STRICT_STARTUP"] = "false"
    os.environ["VERITAS_LOG_LEVEL"] = "DEBUG"
    # ✅ Wichtig: `raise_server_exceptions=False` verhindert, dass Server-Exceptions
    # direkt in den Test propagiert werden (für bessere Error-Meldungen)
    # ✅ Der TestClient startet automatisch den lifespan context manager
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_live_intelligent_pipeline_with_ollama(client):
    """
    LIVE TEST: Intelligent Pipeline mit echtem Ollama
    Erwartet:
    - Ollama läuft auf localhost:11434
    - llama3.1:8b verfügbar
    - Alle wissenschaftlichen Services aktiv
    """
    query = """
    Ich plane den Bau einer Windkraftanlage mit 5 MW Leistung auf einem landwirtschaftlich 
    genutzten Grundstück in der Nähe eines Naturschutzgebiets.
    
    Analysiere bitte:
    1. Rechtliche Genehmigungsanforderungen
    2. Umweltrechtliche Auflagen (insbesondere Naturschutz)
    3. Technische Anforderungen und Standortanalyse
    4. Finanzielle Aspekte und Fördermöglichkeiten
    5. Soziale Auswirkungen auf Anwohner
    """
    
    request_data = {
        "query": query,
        "session_id": "live_test_session",
        "enable_streaming": True,
        "enable_intermediate_results": True,
        "enable_llm_thinking": True,
        "conversation_history": None,
        "requested_agents": ["phi3", "gemma3"],  # Kleinere Modelle bevorzugen
        "timeout": 30  # Timeout für Pipeline-Request (Sekunden)
    }
    
    print("\n" + "="*100)
    print("🔬 LIVE INTELLIGENT PIPELINE TEST - MIT OLLAMA")
    print("="*100)
    print(f"📝 Query: {query.strip()[:100]}...")
    print(f"🤖 Angeforderte Agenten/Modelle: {request_data['requested_agents']}")
    print(f"⏱️  Timeout: {request_data['timeout']} Sekunden")
    print("="*100 + "\n")
    
    start_time = time.time()
    
    # Sende Request
    response = client.post("/v2/intelligent/query", json=request_data)
    
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  Antwortzeit: {elapsed:.2f}s")
    print(f"📡 Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"\n❌ ERROR Response:")
        print(response.text[:500])
        pytest.fail(f"Pipeline nicht verfügbar: {response.status_code}")
        return
    
    data = response.json()
    
    # 1. Basis-Validierung
    assert "response_text" in data, "response_text fehlt"
    assert "agent_results" in data, "agent_results fehlt"
    
    response_text = data["response_text"]
    agent_results = data.get("agent_results", {})
    
    print(f"\n📊 ERGEBNISSE:")
    print(f"  Response Länge: {len(response_text)} chars")
    print(f"  Agenten: {len(agent_results)}")
    
    # 2. Agent-Analyse
    print(f"\n🤖 AGENT EXECUTION:")
    expected_agents = ["environmental", "legal_framework", "financial", "construction", "social"]
    
    for agent in expected_agents:
        if agent in agent_results:
            result = agent_results[agent]
            confidence = result.get("confidence_score", 0) if isinstance(result, dict) else 0
            print(f"  ✅ {agent:20s} - Confidence: {confidence:.2%}")
        else:
            print(f"  ⚠️  {agent:20s} - NICHT ausgeführt")
    
    # Mindestens 3 Agenten sollten ausgeführt worden sein
    assert len(agent_results) >= 3, f"Zu wenige Agenten: {len(agent_results)}"
    
    # 3. Wissenschaftliche Methode validieren
    print(f"\n🔬 WISSENSCHAFTLICHE METHODE:")
    
    # Hypothesis
    has_hypothesis = any(marker in response_text.lower() 
                        for marker in ["hypothes", "annahme", "vermutung"])
    print(f"  Hypothesis Generation:     {'✅' if has_hypothesis else '⚠️  FEHLT'}")
    
    # Dialektische Synthese
    has_dialectic = "dialektisch" in response_text.lower() or "synthese" in response_text.lower()
    has_theses = "these" in response_text.lower()
    has_contradictions = "widerspruch" in response_text.lower() or "widersprüch" in response_text.lower()
    
    print(f"  Dialektische Synthese:     {'✅' if has_dialectic else '❌ FEHLT'}")
    if has_theses:
        print(f"    ├─ Thesen extrahiert:    ✅")
    if has_contradictions:
        print(f"    └─ Widersprüche gefunden: ✅")
    
    assert has_dialectic, "Dialektische Synthese fehlt im Response!"
    
    # Peer Review
    has_peer_review = "peer-review" in response_text.lower() or "peer review" in response_text.lower()
    has_consensus = "consensus" in response_text.lower() or "konsens" in response_text.lower()
    has_verdict = "verdict" in response_text.lower() or "urteil" in response_text.lower()
    
    print(f"  Peer-Review Validation:    {'✅' if has_peer_review else '❌ FEHLT'}")
    if has_consensus:
        print(f"    ├─ Consensus berechnet:  ✅")
    if has_verdict:
        print(f"    └─ Final Verdict:        ✅")
    
    assert has_peer_review, "Peer-Review fehlt im Response!"
    
    # 4. Response-Qualität
    print(f"\n📄 RESPONSE-QUALITÄT:")
    
    # Sollte alle Query-Aspekte abdecken
    coverage_topics = [
        ("Genehmigung", ["genehmigung", "zulassung", "bewilligung"]),
        ("Umwelt", ["umwelt", "natur", "schutz", "ökolog"]),
        ("Technik", ["techni", "standort", "anlage"]),
        ("Finanzen", ["finanz", "kosten", "förder", "investition"]),
        ("Soziales", ["sozial", "anwohner", "akzeptanz"])
    ]
    
    covered = 0
    for topic, keywords in coverage_topics:
        is_covered = any(kw in response_text.lower() for kw in keywords)
        status = "✅" if is_covered else "⚠️"
        print(f"  {status} {topic}")
        if is_covered:
            covered += 1
    
    coverage_percent = (covered / len(coverage_topics)) * 100
    print(f"\n  Themenabdeckung: {covered}/{len(coverage_topics)} ({coverage_percent:.0f}%)")
    
    # Mindestens 60% der Themen sollten abgedeckt sein
    assert coverage_percent >= 60, f"Themenabdeckung zu niedrig: {coverage_percent}%"
    
    # 5. LLM-Qualität (Optional: prüfe ob echte LLM-Responses oder Fallbacks)
    print(f"\n🧠 LLM-INTEGRATION:")
    
    # Wenn echte LLMs genutzt wurden, sollten komplexe Sätze vorhanden sein
    has_complex_sentences = len([s for s in response_text.split('.') if len(s) > 50]) > 5
    has_structured_sections = response_text.count('\n\n') > 3
    
    print(f"  Komplexe Sätze:            {'✅' if has_complex_sentences else '⚠️'}")
    print(f"  Strukturierte Abschnitte:  {'✅' if has_structured_sections else '⚠️'}")
    
    # 6. Ausgabe-Sample (gekürzt)
    print(f"\n📋 RESPONSE-SAMPLE (erste 500 Zeichen):")
    print("─" * 100)
    print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
    print("─" * 100)
    
    # Suche nach wissenschaftlichen Abschnitten
    if "Dialektische Synthese" in response_text:
        start = response_text.find("Dialektische Synthese")
        end = start + 300
        print(f"\n🔬 DIALEKTISCHE SYNTHESE (Auszug):")
        print("─" * 100)
        print(response_text[start:end] + "...")
        print("─" * 100)
    
    if "Peer-Review" in response_text:
        start = response_text.find("Peer-Review")
        end = start + 300
        print(f"\n📊 PEER-REVIEW (Auszug):")
        print("─" * 100)
        print(response_text[start:end] + "...")
        print("─" * 100)
    
    # FINAL SUMMARY
    print("\n" + "="*100)
    print("✅ LIVE PIPELINE TEST ERFOLGREICH")
    print("="*100)
    print(f"✓ {len(agent_results)} Agenten ausgeführt")
    print(f"✓ Dialektische Synthese: {'JA' if has_dialectic else 'NEIN'}")
    print(f"✓ Peer-Review: {'JA' if has_peer_review else 'NEIN'}")
    print(f"✓ Themenabdeckung: {coverage_percent:.0f}%")
    print(f"✓ Response-Länge: {len(response_text)} chars")
    print(f"✓ Verarbeitungszeit: {elapsed:.2f}s")
    print("="*100 + "\n")


def test_live_v2_query_with_scientific_mode(client):
    """
    LIVE TEST: Einfacherer /v2/query Endpoint mit Ollama
    """
    query = """
    Welche Genehmigungen und Umweltauflagen muss ich für den Bau eines 
    Gewächshauses mit 500m² auf landwirtschaftlichem Grund beachten?
    """
    
    request_data = {
        "query": query,
        "session_id": "live_test_v2_query",
        "mode": "veritas"
    }
    
    print("\n" + "="*100)
    print("🔬 LIVE V2 QUERY TEST - MIT OLLAMA")
    print("="*100)
    
    start_time = time.time()
    response = client.post("/v2/query", json=request_data)
    elapsed = time.time() - start_time
    
    print(f"⏱️  Antwortzeit: {elapsed:.2f}s")
    print(f"📡 Status Code: {response.status_code}")
    
    assert response.status_code == 200, f"Request failed: {response.status_code}"
    
    data = response.json()
    response_text = data.get("response_text", "")
    
    print(f"📝 Response: {len(response_text)} chars")
    
    # Prüfe ob Pipeline verfügbar
    is_fallback = "nicht verfügbar" in response_text or "Pipeline nicht" in response_text
    
    if is_fallback:
        print("⚠️  Pipeline war nicht verfügbar - Test mit Fallback")
        assert len(response_text) > 50
    else:
        print("✅ Pipeline war aktiv")
        
        # Prüfe wissenschaftliche Elemente
        has_dialectic = "dialektisch" in response_text.lower() or "synthese" in response_text.lower()
        has_peer_review = "peer" in response_text.lower() or "review" in response_text.lower()
        
        print(f"  Dialektik: {'✅' if has_dialectic else '⚠️'}")
        print(f"  Peer-Review: {'✅' if has_peer_review else '⚠️'}")
        
        # Mindestens eines sollte vorhanden sein
        assert has_dialectic or has_peer_review, \
            "Wissenschaftliche Methode fehlt trotz aktiver Pipeline!"
    
    print("✅ V2 Query Live-Test erfolgreich\n")


def test_ollama_connectivity(client):
    """
    Basis-Test: Prüft ob Ollama erreichbar ist
    """
    import requests
    
    print("\n" + "="*100)
    print("🔌 OLLAMA CONNECTIVITY TEST")
    print("="*100)
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama erreichbar: {len(models)} Modelle verfügbar")
            
            for model in models[:5]:  # Zeige erste 5
                name = model.get("name", "unknown")
                size_gb = model.get("size", 0) / (1024**3)
                print(f"  - {name:30s} ({size_gb:.2f} GB)")
            
            # Prüfe ob llama3.1 verfügbar
            has_llama31 = any("llama3.1" in m.get("name", "") for m in models)
            assert has_llama31, "llama3.1 nicht gefunden!"
            print(f"\n✅ llama3.1 verfügbar")
        else:
            pytest.fail(f"Ollama antwortet mit Status {response.status_code}")
    
    except Exception as e:
        pytest.fail(f"Ollama nicht erreichbar: {e}")
    
    print("="*100 + "\n")


if __name__ == "__main__":
    print("Bitte mit pytest ausführen:")
    print("pytest tests/test_live_ollama_pipeline.py -v -s")
