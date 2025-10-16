"""
Test: Chat-Verlauf Integration
================================
Testet ob Chat-Verlauf korrekt an Backend übergeben und in der Antwort berücksichtigt wird

EXPECTED:
- Backend empfängt conversation_history
- Finale Antwort enthält Gesprächskontext
- LLM nutzt Kontext für bessere Antworten
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_conversation_history():
    print("=" * 80)
    print("🧪 TEST: Chat-Verlauf Integration")
    print("=" * 80)
    
    # 1. Health Check
    print("\n1️⃣ Backend Health Check...")
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5).json()
        print(f"✅ Backend: {health.get('status')}")
    except Exception as e:
        print(f"❌ Backend nicht erreichbar: {e}")
        return
    
    # 2. Simuliere Chat-Verlauf
    conversation_history = [
        {
            "role": "user",
            "content": "Wie funktioniert das Baugenehmigungsverfahren in München?"
        },
        {
            "role": "assistant",
            "content": "Das Baugenehmigungsverfahren in München umfasst mehrere Schritte: 1. Bauantrag stellen, 2. Prüfung durch Bauaufsicht, 3. Genehmigung erteilen."
        },
        {
            "role": "user",
            "content": "Welche Unterlagen benötige ich dafür?"
        }
    ]
    
    print(f"\n2️⃣ Sende Query mit {len(conversation_history)} Nachrichten Kontext...")
    
    # 3. Sende Streaming Query mit conversation_history
    query = "Welche Unterlagen benötige ich dafür?"
    
    response = requests.post(
        f"{BASE_URL}/v2/query/stream",
        json={
            "query": query,
            "session_id": f"test_conv_{int(time.time())}",
            "enable_streaming": True,
            "enable_intermediate_results": True,
            "enable_llm_thinking": True,
            "conversation_history": conversation_history  # 🆕 Chat-Verlauf
        },
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Query fehlgeschlagen: {response.status_code}")
        print(response.text)
        return
    
    stream_info = response.json()
    stream_session_id = stream_info["session_id"]
    
    print(f"✅ Stream gestartet: {stream_session_id}")
    
    # 4. Listen to Stream
    print("\n3️⃣ Warte auf finale Antwort...")
    
    stream_response = requests.get(
        f"{BASE_URL}/progress/{stream_session_id}",
        stream=True,
        headers={'Accept': 'text/event-stream'},
        timeout=120
    )
    
    final_result = None
    
    for line in stream_response.iter_lines(decode_unicode=True):
        if line.startswith('data: '):
            try:
                event_data = json.loads(line[6:])
                event_type = event_data.get('type', '')
                stage = event_data.get('stage', '')
                
                if event_type == 'stage_complete' and stage == 'completed':
                    final_result = event_data.get('details', {})
                    break
                    
            except json.JSONDecodeError:
                continue
    
    # 5. Analysiere Antwort
    if final_result:
        response_text = final_result.get('response_text', '')
        
        print("\n" + "=" * 80)
        print("📄 FINALE ANTWORT:")
        print("=" * 80)
        print(response_text[:500])  # Erste 500 Zeichen
        print("...")
        
        # 6. Prüfe ob Kontext berücksichtigt wurde
        print("\n" + "=" * 80)
        print("🔍 KONTEXT-ANALYSE:")
        print("=" * 80)
        
        has_conversation_context = "**Gesprächskontext**" in response_text
        
        print(f"   Gesprächskontext-Abschnitt: {'✅ Vorhanden' if has_conversation_context else '❌ Fehlt'}")
        
        if has_conversation_context:
            # Extrahiere Kontext-Abschnitt
            start = response_text.find("**Gesprächskontext**")
            end = response_text.find("**Zusammenfassung", start)
            context_section = response_text[start:end] if end > start else response_text[start:start+300]
            
            print("\n   📚 Kontext-Abschnitt:")
            print("   " + "-" * 76)
            for line in context_section.split('\n')[:10]:  # Erste 10 Zeilen
                print(f"   {line}")
            print("   " + "-" * 76)
        
        # Prüfe ob frühere Frage erwähnt wird
        mentions_previous = any(keyword in response_text.lower() for keyword in [
            'baugenehmigung',
            'münchen',
            'vorherige frage',
            'gesprächskontext'
        ])
        
        print(f"\n   Bezug zu vorherigen Nachrichten: {'✅ Ja' if mentions_previous else '⚠️ Unklar'}")
        
        # Zusammenfassung
        print("\n" + "=" * 80)
        if has_conversation_context and mentions_previous:
            print("✅ TEST ERFOLGREICH!")
            print("   - Chat-Verlauf wurde korrekt übermittelt")
            print("   - Kontext wird in Antwort angezeigt")
            print("   - Bezug zu vorherigen Nachrichten erkennbar")
        elif has_conversation_context:
            print("⚠️ TEST TEILWEISE ERFOLGREICH")
            print("   - Kontext-Abschnitt vorhanden")
            print("   - Aber Bezug zu Kontext unklar")
        else:
            print("❌ TEST FEHLGESCHLAGEN")
            print("   - Kontext-Abschnitt fehlt in Antwort")
        print("=" * 80)
    else:
        print("\n❌ Keine finale Antwort erhalten")

if __name__ == "__main__":
    print("🚀 Starte Chat-Verlauf Integration Test...\n")
    print("⚠️  Stelle sicher, dass Backend läuft")
    print("")
    
    test_conversation_history()
