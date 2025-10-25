#!/usr/bin/env python3
"""
Test-Script für Hypothesis-Integration in Streaming-Pipeline
Führt eine Query aus und zeigt alle SSE-Events an
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_hypothesis_streaming():
    """Teste Hypothesis-Events in Streaming-Pipeline"""
    
    print("=" * 60)
    print("HYPOTHESIS STREAMING TEST")
    print("=" * 60)
    
    # 1. Starte Streaming Query
    print("\n1️⃣  Starte Streaming Query...")
    query_request = {
        "query": "Welche Genehmigungen brauche ich für einen Neubau in Stuttgart?",
        "enable_llm_thinking": False  # Ohne Reflection für schnelleren Test
    }
    
    response = requests.post(
        f"{BASE_URL}/v2/query/stream",
        json=query_request
    )
    
    if response.status_code != 200:
        print(f"❌ Fehler beim Starten: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    session_id = data["session_id"]
    query_id = data["query_id"]
    
    print(f"   ✅ Session gestartet: {session_id}")
    print(f"   📝 Query ID: {query_id}")
    print(f"   🔗 Stream URL: {data['stream_url']}")
    
    # 2. Verbinde mit Progress-Stream (Nach kurzer Wartezeit für Hypothesis-Generation)
    print("\n2️⃣  Verbinde mit SSE-Stream...")
    print("   ⏱️  Warte 1.5s für Hypothesis-Generation (LLM braucht Zeit)...")
    time.sleep(1.5)  # LLM-Call für Hypothesis braucht ~1-2 Sekunden
    print("   🔗 Connecting jetzt...\n")
    
    # Nutze die stream_url aus der Response (ohne /v2/query prefix)
    stream_url = f"{BASE_URL}{data['stream_url']}"
    print(f"   🔗 Connecting to: {stream_url}")
    
    hypothesis_found = False
    event_count = 0
    all_events = []  # Speichere alle Events für Analyse
    
    try:
        # WICHTIG: Timeout erhöhen für LLM-Calls (Hypothesis-Generierung kann 5-10s dauern)
        with requests.get(stream_url, stream=True, timeout=60) as stream_response:
            if stream_response.status_code != 200:
                print(f"❌ Stream-Verbindung fehlgeschlagen: {stream_response.status_code}")
                return
            
            for line in stream_response.iter_lines():
                if not line:
                    continue
                
                line_str = line.decode('utf-8')
                
                # Parse SSE-Events
                if line_str.startswith('data: '):
                    event_count += 1
                    event_json = line_str[6:]  # Remove 'data: ' prefix
                    
                    try:
                        event = json.loads(event_json)
                        event_type = event.get('type', 'unknown')
                        stage = event.get('stage', 'unknown')
                        message = event.get('message', '')
                        
                        # Speichere Event für spätere Analyse
                        all_events.append(event)
                        
                        # Anzeige
                        print(f"📡 Event #{event_count}: {event_type} | {stage}")
                        print(f"   💬 {message}")
                        
                        # HYPOTHESIS EVENT DETECTION
                        if event_type == 'hypothesis':
                            hypothesis_found = True
                            print("\n" + "=" * 60)
                            print("🔬 HYPOTHESIS EVENT GEFUNDEN!")
                            print("=" * 60)
                            
                            hypothesis_data = event.get('hypothesis_data', {})
                            print(f"   Question Type: {hypothesis_data.get('question_type', 'N/A')}")
                            print(f"   Confidence: {hypothesis_data.get('confidence', 'N/A')}")
                            print(f"   Primary Intent: {hypothesis_data.get('primary_intent', 'N/A')}")
                            
                            # Information Gaps
                            gaps = hypothesis_data.get('information_gaps', [])
                            print(f"\n   📊 Information Gaps: {len(gaps)}")
                            for i, gap in enumerate(gaps, 1):
                                print(f"      {i}. {gap.get('gap_type')} ({gap.get('severity')}) - {gap.get('suggested_query')}")
                            
                            # Clarification Questions
                            clarifications = hypothesis_data.get('clarification_questions', [])
                            print(f"\n   ❓ Clarification Questions: {len(clarifications)}")
                            for i, question in enumerate(clarifications, 1):
                                print(f"      {i}. {question}")
                            
                            print("=" * 60 + "\n")
                        
                        # STAGE_COMPLETE = Pipeline fertig
                        if event_type == 'stage_complete' and stage == 'completed':
                            print("\n✅ Pipeline abgeschlossen!\n")
                            break
                        
                        # ERROR
                        if event_type == 'error':
                            print(f"\n❌ Fehler: {event.get('details', {})}\n")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON Parse Error: {e}")
                        print(f"   Raw: {event_json[:100]}")
    
    except requests.exceptions.Timeout:
        print("\n⏱️  Timeout nach 30 Sekunden")
    except KeyboardInterrupt:
        print("\n⏸️  Test abgebrochen")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"Events empfangen: {event_count}")
    print(f"Hypothesis Event: {'✅ GEFUNDEN' if hypothesis_found else '❌ NICHT GEFUNDEN'}")
    
    # Zeige alle Event-Types
    print(f"\n📊 Event-Types empfangen:")
    event_types = {}
    for evt in all_events:
        evt_type = evt.get('type', 'unknown')
        event_types[evt_type] = event_types.get(evt_type, 0) + 1
    for evt_type, count in event_types.items():
        print(f"   • {evt_type}: {count}x")
    
    if not hypothesis_found:
        print("\n⚠️  HYPOTHESIS EVENT FEHLT!")
        print("Mögliche Ursachen:")
        print("  1. Processing zu schnell → Events vor Stream-Verbindung")
        print("  2. HypothesisService nicht initialisiert")
        print("  3. Ollama-Client nicht verfügbar")
        print("  4. Import-Fehler in _process_streaming_query()")
        print("\nÜberprüfe Backend-Logs:")
        print("  Get-Content logs/backend_uvicorn.err.log -Tail 50")


if __name__ == "__main__":
    test_hypothesis_streaming()
