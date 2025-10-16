"""
Test für Streaming Display Fix
Testet ob die finale Antwort korrekt angezeigt wird
"""
import asyncio
import requests
import json
import time

BACKEND_URL = "http://localhost:5000"

async def test_streaming_display():
    """Teste Streaming mit Stuttgart Query"""
    
    print("🧪 Test: Streaming Display Fix")
    print("=" * 60)
    
    # 1. Health Check
    print("\n1️⃣ Backend Health Check...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        health = response.json()
        print(f"✅ Backend: {health.get('status')}")
        print(f"   Streaming: {health.get('streaming_available')}")
        print(f"   UDS3: {health.get('uds3_available')}")
        print(f"   Ollama: {health.get('ollama_available')}")
    except Exception as e:
        print(f"❌ Backend nicht erreichbar: {e}")
        return
    
    # 2. Streaming Query
    print("\n2️⃣ Sende Streaming Query...")
    query_data = {
        "query": "Was sind die wichtigsten Bauvorschriften in Stuttgart?",
        "session_id": f"test_stream_{int(time.time())}",
        "enable_streaming": True,
        "enable_intermediate_results": True,
        "enable_llm_thinking": True
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/v2/query/stream",
            json=query_data,
            timeout=10
        )
        result = response.json()
        
        print(f"✅ Query gestartet")
        print(f"   Query ID: {result.get('query_id')}")
        print(f"   Stream Session: {result.get('stream_session_id')}")
        stream_session_id = result.get('stream_session_id')
        session_id = result.get('session_id')
        
    except Exception as e:
        print(f"❌ Query-Start fehlgeschlagen: {e}")
        return
    
    # 3. Progress Stream verfolgen
    print("\n3️⃣ Verfolge Progress Stream...")
    progress_url = f"{BACKEND_URL}/progress/{session_id}"
    
    final_result_found = False
    response_text_found = False
    response_text_content = None
    
    try:
        # SSE Stream lesen
        response = requests.get(progress_url, stream=True, timeout=120)
        
        event_count = 0
        for line in response.iter_lines():
            if not line:
                continue
            
            line = line.decode('utf-8')
            
            if line.startswith('data: '):
                event_data = line[6:]  # Remove 'data: '
                
                try:
                    event = json.loads(event_data)
                    event_type = event.get('type', 'unknown')
                    
                    event_count += 1
                    
                    # Log wichtige Events
                    if event_type == 'stage_update':
                        stage = event.get('stage', 'unknown')
                        message = event.get('message', '')
                        print(f"   📍 Stage: {stage} - {message}")
                    
                    elif event_type == 'stage_reflection':
                        reflection = event.get('details', {})
                        stage = reflection.get('stage', 'unknown')
                        status = reflection.get('fulfillment_status', 'unknown')
                        percent = reflection.get('completion_percent', 0)
                        print(f"   🔍 Reflection: {stage} - {status} ({percent}%)")
                    
                    elif event_type == 'stage_complete':
                        print(f"   ✅ STAGE_COMPLETE Event empfangen!")
                        details = event.get('details', {})
                        print(f"      Details Keys: {list(details.keys())}")
                        
                        if 'response_text' in details:
                            response_text_content = details['response_text']
                            response_text_found = True
                            print(f"      ✅ response_text gefunden: {len(response_text_content)} Zeichen")
                            print(f"      Preview: {response_text_content[:200]}...")
                        else:
                            print(f"      ❌ KEIN response_text in details!")
                        
                        final_result_found = True
                        break
                
                except json.JSONDecodeError:
                    pass
        
        print(f"\n📊 Statistik:")
        print(f"   Events empfangen: {event_count}")
        print(f"   Final Result Event: {'✅ Ja' if final_result_found else '❌ Nein'}")
        print(f"   response_text gefunden: {'✅ Ja' if response_text_found else '❌ Nein'}")
        
        if response_text_found:
            print(f"\n✅ TEST ERFOLGREICH!")
            print(f"   Response Text Länge: {len(response_text_content)} Zeichen")
            print(f"   Erste 500 Zeichen:\n{response_text_content[:500]}")
        else:
            print(f"\n❌ TEST FEHLGESCHLAGEN!")
            print(f"   Keine response_text im final_result gefunden!")
    
    except Exception as e:
        print(f"❌ Stream-Fehler: {e}")

if __name__ == "__main__":
    asyncio.run(test_streaming_display())
