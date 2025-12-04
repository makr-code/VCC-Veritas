"""
Test: UDS3 Real Agent Integration
==================================
Testet, ob echte UDS3 Hybrid Search Daten geliefert werden

ZIEL:
- Prüfe ob UDS3 funktioniert
- Prüfe ob Agents echte Daten zurückgeben
- Vergleiche Mock vs. Real Data
"""

import asyncio
import json
import time

import requests

BASE_URL = "http://localhost:5000"


def test_uds3_integration():
    """Testet UDS3 Integration End-to-End"""

    print("=" * 80)
    print("🧪 TEST: UDS3 Real Agent Integration")
    print("=" * 80)

    # 1. Health Check
    print("\n1️⃣ Backend Health Check...")
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5).json()
        print(f"✅ Backend Status: {health.get('status')}")
        print(f"   UDS3: {'✅ Verfügbar' if health.get('uds3_available') else '❌ Nicht verfügbar'}")
        print(f"   Ollama: {'✅ Verfügbar' if health.get('ollama_available') else '❌ Nicht verfügbar'}")
        print(f"   Streaming: {'✅ Verfügbar' if health.get('streaming_available') else '❌ Nicht verfügbar'}")

        if not health.get("uds3_available"):
            print("\n⚠️ UDS3 nicht verfügbar - Test wird Mock-Daten nutzen")
    except Exception as e:
        print(f"❌ Backend nicht erreichbar: {e}")
        return

    # 2. Sende Test-Query
    print("\n2️⃣ Sende Test-Query mit Streaming...")

    query = "Welche Umweltauflagen gelten für Industriebauten in München?"

    response = requests.post(
        f"{BASE_URL}/v2/query/stream",
        json={
            "query": query,
            "session_id": f"test_uds3_{int(time.time())}",
            "enable_streaming": True,
            "enable_intermediate_results": True,
            "enable_llm_thinking": True,
        },
        timeout=10,
    )

    if response.status_code != 200:
        print(f"❌ Query fehlgeschlagen: {response.status_code}")
        return

    stream_info = response.json()
    stream_session_id = stream_info["session_id"]

    print(f"✅ Stream gestartet: {stream_session_id}")

    # 3. Listen to Stream
    print("\n3️⃣ Warte auf Agent-Ergebnisse...")

    stream_response = requests.get(
        f"{BASE_URL}/progress/{stream_session_id}", stream=True, headers={"Accept": "text/event-stream"}, timeout=120
    )

    agent_results = {}
    uds3_used_count = 0
    mock_used_count = 0

    for line in stream_response.iter_lines(decode_unicode=True):
        if line.startswith("data: "):
            try:
                event_data = json.loads(line[6:])
                event_type = event_data.get("type", "")
                stage = event_data.get("stage", "")

                # Stage Complete mit final_result
                if event_type == "stage_complete" and stage == "completed":
                    final_result = event_data.get("details", {})
                    agent_results = final_result.get("agent_results", {})

                    print(f"\n✅ Finale Ergebnisse erhalten!")
                    print(f"   Agent-Results: {len(agent_results)}")

                    # Analysiere Agent-Results
                    print("\n" + "=" * 80)
                    print("📊 AGENT-RESULTS ANALYSE:")
                    print("=" * 80)

                    for agent_type, result in agent_results.items():
                        uds3_used = result.get("uds3_used", False)
                        sources = result.get("sources", [])
                        confidence = result.get("confidence_score", 0)
                        summary = result.get("summary", "")[:80]

                        if uds3_used:
                            uds3_used_count += 1
                            marker = "🟢 UDS3"
                        else:
                            mock_used_count += 1
                            marker = "🔴 MOCK"

                        print(f"\n{marker} {agent_type}:")
                        print(f"   Summary: {summary}")
                        print(f"   Sources: {sources}")
                        print(f"   Confidence: {confidence:.2%}")

                    # Gesamt-Statistik
                    print("\n" + "=" * 80)
                    print("📈 STATISTIK:")
                    print("=" * 80)
                    print(f"   Gesamt Agents: {len(agent_results)}")
                    print(f"   🟢 UDS3 genutzt: {uds3_used_count}")
                    print(f"   🔴 Mock genutzt: {mock_used_count}")

                    # Bewertung
                    print("\n" + "=" * 80)
                    if uds3_used_count > 0:
                        print("✅ TEST ERFOLGREICH!")
                        print(f"   {uds3_used_count} Agent(s) nutzen echte UDS3 Daten")
                        print("   Hybrid Search funktioniert!")
                    else:
                        print("⚠️ TEST TEILWEISE ERFOLGREICH")
                        print("   Alle Agents nutzen Mock-Daten")
                        print("   Mögliche Gründe:")
                        print("   - UDS3 Datenbank leer")
                        print("   - Keine passenden Dokumente gefunden")
                        print("   - UDS3 nicht korrekt initialisiert")
                    print("=" * 80)

                    break

            except json.JSONDecodeError:
                continue

    # 4. Prüfe Quellen-Unterschiede
    if agent_results:
        print("\n4️⃣ Quellen-Analyse:")
        all_sources = []
        for result in agent_results.values():
            all_sources.extend(result.get("sources", []))

        unique_sources = list(set(all_sources))
        print(f"   Einzigartige Quellen: {len(unique_sources)}")
        print(f"   Quellen-Liste: {unique_sources[:5]}")  # Erste 5

        # Prüfe ob hardcoded
        hardcoded_sources = ["OpenStreetMap", "Gemeinde-DB", "BauGB", "VwVfG"]
        has_hardcoded = any(src in unique_sources for src in hardcoded_sources)
        has_uds3 = any("UDS3" in str(src) or "uds3" in str(src).lower() for src in unique_sources)

        print(f"\n   Hardcoded-Quellen: {'✅ Ja' if has_hardcoded else '❌ Nein'}")
        print(f"   UDS3-Quellen: {'✅ Ja' if has_uds3 else '❌ Nein'}")


if __name__ == "__main__":
    print("🚀 Starte UDS3 Integration Test...\n")
    print("⚠️  Stelle sicher, dass Backend läuft")
    print("")

    test_uds3_integration()
