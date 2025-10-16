"""
Einfacher direkter Test des Streaming-Endpoints
"""

import requests
import json

def test_streaming():
    """Teste Streaming-Endpoint"""
    
    print("🧪 Test Streaming-Endpoint")
    print("=" * 60)
    
    url = "http://localhost:5000/v2/query/stream"
    payload = {
        "query": "Baugenehmigung München",
        "session_id": "test_simple"
    }
    
    print(f"📝 Query: {payload['query']}")
    print(f"🌐 URL: {url}")
    print(f"\n⏳ Sende Request...")
    
    try:
        # Schritt 1: Starte Streaming Query
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"✅ HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return
        
        result = response.json()
        session_id = result.get('session_id')
        stream_url = result.get('stream_url')
        
        print(f"✅ Session ID: {session_id}")
        print(f"✅ Stream URL: {stream_url}")
        
        # Schritt 2: Verbinde mit Progress Stream
        full_stream_url = f"http://localhost:5000{stream_url}"
        print(f"\n⏳ Verbinde mit Stream: {full_stream_url}")
        
        stream_response = requests.get(full_stream_url, stream=True, timeout=60)
        
        if stream_response.status_code != 200:
            print(f"❌ Stream Error: HTTP {stream_response.status_code}")
            return
        
        print(f"\n📡 Streaming Events:\n")
        
        event_count = 0
        agents = []
        
        for line in stream_response.iter_lines():
            if line:
                try:
                    text = line.decode('utf-8')
                    
                    if text.startswith('data: '):
                        data = json.loads(text[6:])
                        event = data.get('event')
                        event_count += 1
                        
                        # DEBUG: Print first 3 data objects
                        if event_count <= 3:
                            print(f"\n  🔍 DEBUG Event #{event_count}:")
                            print(f"     Data Keys: {list(data.keys())}")
                            print(f"     Event: {event}")
                            if len(data) < 10:
                                print(f"     Full Data: {data}")
                        
                        if event == 'AGENT_COMPLETE':
                            agent = data.get('agent')
                            result = data.get('result', {})
                            is_sim = result.get('is_simulation', False)
                            conf = result.get('confidence_score', 0.0)
                            
                            status = "🔴 MOCK" if is_sim else "✅ REAL"
                            print(f"  {agent:20s}: {status} (Conf: {conf:.2f})")
                            agents.append(agent)
                        
                        elif event == 'STAGE_UPDATE':
                            stage = data.get('stage')
                            print(f"  📍 Stage: {stage}")
                        
                        elif event == 'STREAM_COMPLETE':
                            print(f"\n✅ Stream Complete!")
                            break
                        
                        else:
                            # Print all other events for debugging
                            print(f"  🔍 Event: {event}")
                
                except Exception as e:
                    pass
        
        print(f"\n📊 Total Events: {event_count}")
        print(f"📊 Agents Executed: {len(agents)}")
        print(f"📊 Agents: {', '.join(agents)}")
        
        if len(agents) >= 8:
            print("\n🎉 ERFOLGREICH - 8+ Agenten (Intelligent Pipeline!)")
        elif len(agents) >= 5:
            print("\n✅ GUT - 5+ Agenten")
        else:
            print(f"\n⚠️ NUR {len(agents)} Agenten")
        
    except requests.exceptions.ConnectionError:
        print("❌ Backend nicht erreichbar!")
        print("➡️ Starte Backend: python start_backend.py")
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_streaming()
