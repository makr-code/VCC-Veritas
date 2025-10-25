#!/usr/bin/env python3
"""
Test ob Pipeline wirklich genutzt wird - Check Backend Logs
"""
import requests
import time

query = "Test: Nutzt das System die Intelligent Pipeline?"

print("="*80)
print("PIPELINE USAGE TEST")
print("="*80)

# 1. Query starten
print("\n1. Starte Test-Query...")
resp = requests.post(
    "http://localhost:5000/v2/query/stream",
    json={"query": query}
).json()

session_id = resp["session_id"]
print(f"   Session ID: {session_id}")

# 2. Warte auf Verarbeitung
print("\n2. Warte auf Verarbeitung (5 Sekunden)...")
time.sleep(5)

# 3. Hole Session-Status über API
print("\n3. Prüfe Session-Status...")
try:
    # Versuche Session-Details zu holen (falls endpoint existiert)
    status_resp = requests.get(f"http://localhost:5000/api/sessions/{session_id}")
    if status_resp.status_code == 200:
        status = status_resp.json()
        print(f"   Status: {status}")
except:
    print("   (Kein Session-Status-Endpoint)")

# 4. Die WICHTIGSTE Frage: Schauen wir ob DEBUG-Logs existieren würden
print("\n4. KRITISCHER TEST:")
print("   Wenn die Pipeline läuft, sollten im Backend folgende Logs erscheinen:")
print("   - 'DEBUG: INTELLIGENT_PIPELINE_AVAILABLE=True'")
print("   - 'DEBUG: intelligent_pipeline=True'")
print("   - 'Nutze Intelligent Pipeline fur Agent-Execution'")
print("")
print("   Da wir die Logs hier nicht sehen konnen, testen wir indirekt:")

# 5. Indirekter Test: Schaue auf Timing und Stages
print("\n5. Indirekte Verifikation uber Event-Sequenz...")
import json

try:
    r = requests.get(
        f"http://localhost:5000/progress/{session_id}",
        headers={"Accept": "text/event-stream"},
        stream=True,
        timeout=30
    )
    
    stages = []
    for line in r.iter_lines():
        if line and line.startswith(b'data: '):
            try:
                event = json.loads(line.decode('utf-8')[6:])
                if event.get('type') == 'stage_start':
                    stages.append(event.get('stage'))
                    print(f"   Stage: {event.get('stage')}")
                elif event.get('type') == 'stage_complete' and event.get('stage') == 'completed':
                    break
            except:
                pass
    
    print(f"\n   Stages gesehen: {stages}")
    
    # Analyse
    print("\n6. ANALYSE:")
    
    # Wenn Pipeline läuft: gathering_context, llm_reasoning
    # Wenn Mock läuft: Nur synthesizing
    
    has_gathering = 'gathering_context' in stages
    has_llm = 'llm_reasoning' in stages
    
    if has_gathering and has_llm:
        print("   [OK] 'gathering_context' + 'llm_reasoning' gefunden")
        print("   [OK] Das deutet auf INTELLIGENT PIPELINE hin!")
        print("\n   ==> VERIFIKATION: Pipeline wird wahrscheinlich genutzt")
        exit(0)
    else:
        print("   [FAIL] Erwartete Stages fehlen")
        print("   [FAIL] System nutzt vermutlich MOCK/Fallback")
        exit(1)

except Exception as e:
    print(f"   Error: {e}")
    exit(1)
