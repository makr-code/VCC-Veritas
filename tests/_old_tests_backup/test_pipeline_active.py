#!/usr/bin/env python3
"""
Test: Ist die Intelligent Pipeline wirklich aktiv im Streaming-Endpoint?
"""
import json
import time

import requests

print("=" * 80)
print("TEST: Intelligent Pipeline im Streaming-Endpoint")
print("=" * 80)

# 1. Backend Status prüfen
print("\n1. Prüfe Backend-Status...")
try:
    response = requests.get("http://localhost:5000/health")
    status = response.json()
    print(f"✓ Backend läuft: {response.status_code}")
    print(f"✓ Intelligent Pipeline verfügbar: {status.get('intelligent_pipeline_available')}")
    print(f"✓ Ollama verfügbar: {status.get('ollama_available')}")
except Exception as e:
    print(f"✗ Backend nicht erreichbar: {e}")
    exit(1)

# 2. Streaming-Query starten
print("\n2. Sende Streaming-Query...")
query_data = {
    "query": "Welche Baugenehmigung brauche ich für ein Einfamilienhaus in München?",
    "enable_intermediate_results": True,
    "enable_reflection": True,
}

try:
    response = requests.post("http://localhost:5000/v2/query/stream", json=query_data, timeout=5)

    if response.status_code != 200:
        print(f"✗ HTTP {response.status_code}: {response.text}")
        exit(1)

    result = response.json()
    session_id = result.get("session_id")

    if not session_id:
        print(f"✗ Keine Session ID in Response: {result}")
        exit(1)

    print(f"✓ Query gestartet: Session ID = {session_id}")

    # 3. Progress überwachen
    print("\n3. Überwache Progress...")
    print("-" * 80)

    agent_count = 0
    last_stage = None

    for i in range(120):  # Max 120 Sekunden (2 Minuten)
        try:
            progress_response = requests.get(
                f"http://localhost:5000/progress/{session_id}", headers={"Accept": "text/event-stream"}, stream=True, timeout=2
            )

            for line in progress_response.iter_lines():
                if line:
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]  # Skip 'data: '
                        try:
                            event = json.loads(data_str)
                            event_type = event.get("type")

                            # Stage Changes
                            if event_type == "stage_start":
                                stage = event.get("stage")
                                if stage != last_stage:
                                    print(f"\n>>> STAGE: {stage}")
                                    last_stage = stage

                            # Agent Events
                            elif event_type == "AGENT_START":
                                agent_name = event.get("agent_name", "unknown")
                                print(f"  → Agent startet: {agent_name}")

                            elif event_type == "AGENT_COMPLETE":
                                agent_name = event.get("agent_name", "unknown")
                                agent_count += 1
                                confidence = event.get("result", {}).get("confidence_score", 0)
                                print(f"  ✓ Agent fertig: {agent_name} (Confidence: {confidence:.2f})")

                            # Stream Complete
                            elif event_type == "STREAM_COMPLETE":
                                print(f"\n{'='*80}")
                                print(f"✓ STREAM COMPLETE")
                                print(f"  Total Agents: {agent_count}")

                                answer = event.get("answer", "")
                                print(f"\n📝 Antwort ({len(answer)} Zeichen):")
                                print(f"  {answer[:200]}...")

                                # Prüfe ob Pipeline-Agents
                                if agent_count >= 8:
                                    print(f"\n✅ ERFOLG: Pipeline läuft (8+ Agents)")
                                else:
                                    print(f"\n⚠️ WARNUNG: Nur {agent_count} Agents (erwartet: 8+)")

                                break  # Exit loop

                        except json.JSONDecodeError:
                            pass

                time.sleep(0.1)

        except requests.exceptions.RequestException:
            # Warte auf Events
            time.sleep(1)

    print("\n⏱️ Timeout nach 120 Sekunden")

except Exception as e:
    print(f"\n✗ Fehler: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
