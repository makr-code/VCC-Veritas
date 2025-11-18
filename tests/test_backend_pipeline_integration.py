"""
Test Backend API mit Intelligent Pipeline Integration
Verifiziert dass /v2/query/stream die Pipeline nutzt
"""

import asyncio
import json
import sys

import aiohttp


async def test_streaming_with_pipeline():
    """Teste /v2/query/stream mit Intelligent Pipeline"""

    print("=" * 70)
    print("🚀 Test: Streaming mit Intelligent Pipeline Integration")
    print("=" * 70)

    query = "Welche Unterlagen benötige ich für eine Baugenehmigung in München?"

    print(f"\n📝 Query: '{query}'")
    print(f"\n⏳ Sende Request an Backend...")

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "query": query,
                "session_id": "test_pipeline_integration",
                "enable_llm_thinking": False,  # Für schnelleren Test
                "enable_intermediate_results": True,
            }

            async with session.post(
                "http://localhost:5000/v2/query/stream", json=payload, headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    print(f"❌ Request fehlgeschlagen: HTTP {response.status}")
                    text = await response.text()
                    print(f"Response: {text}")
                    return False

                print(f"✅ Connection established (HTTP {response.status})")
                print(f"\n📡 Streaming Events:\n")

                agent_results = {}
                final_result = None
                event_count = 0

                async for line in response.content:
                    if line:
                        try:
                            event = line.decode("utf-8").strip()

                            if event.startswith("data: "):
                                data = json.loads(event[6:])
                                event_type = data.get("event")
                                event_count += 1

                                # Print Event
                                if event_type == "AGENT_COMPLETE":
                                    agent_name = data.get("agent")
                                    result = data.get("result", {})
                                    is_sim = result.get("is_simulation", False)
                                    conf = result.get("confidence_score", 0.0)

                                    status = "🔴 MOCK" if is_sim else "✅ PIPELINE"
                                    print(f"  {agent_name:20s}: {status} (Conf: {conf:.2f})")

                                    agent_results[agent_name] = result

                                elif event_type == "STREAM_COMPLETE":
                                    final_result = data.get("final_result", {})
                                    print(f"\n✅ Stream Complete!")

                                elif event_type == "STAGE_UPDATE":
                                    stage = data.get("stage")
                                    print(f"  Stage: {stage}")

                        except json.JSONDecodeError:
                            pass
                        except Exception as e:
                            print(f"⚠️ Event-Parse-Fehler: {e}")

                # Analyse Results
                print("\n" + "=" * 70)
                print("📊 ANALYSE")
                print("=" * 70)

                print(f"\nTotal Events: {event_count}")
                print(f"Agents Executed: {len(agent_results)}")

                # Check if Pipeline was used
                pipeline_used = False
                mock_used = False

                for agent, result in agent_results.items():
                    if result.get("is_simulation"):
                        mock_used = True
                    else:
                        pipeline_used = True

                print(f"\n🎯 Integration Status:")
                if pipeline_used and not mock_used:
                    print("  ✅ INTELLIGENT PIPELINE wird genutzt!")
                    print("  ✅ Alle Agenten nutzen Pipeline-Execution")
                elif pipeline_used and mock_used:
                    print("  ⚠️ HYBRID - Pipeline + Mock")
                    print("  ⚠️ Einige Agenten nutzen Pipeline, andere Mock")
                elif mock_used:
                    print("  🔴 NUR MOCK - Pipeline nicht genutzt!")
                    print("  ❌ Backend nutzt alte Mock-Funktion")

                # Print Final Response
                if final_result:
                    worker_results = final_result.get("worker_results", {})
                    main_response = final_result.get("main_response", "")

                    print(f"\n📝 Final Response (erste 300 Zeichen):")
                    print(main_response[:300] + "...")

                    # Check Simulation Warning
                    has_warning = "⚠️  **DEMO-MODUS**" in main_response
                    print(f"\n⚠️ Simulation Warning vorhanden: {'Ja' if has_warning else 'Nein'}")

                return pipeline_used

    except aiohttp.ClientConnectorError:
        print("❌ Kann nicht zu Backend verbinden!")
        print("➡️ Bitte starte Backend: python start_backend.py")
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_compare_agents():
    """Vergleiche Agent-Count: Vorher vs. Nachher"""

    print("\n\n" + "=" * 70)
    print("🔍 Vergleich: Agent-Count")
    print("=" * 70)

    query = "Baugenehmigung München"

    try:
        async with aiohttp.ClientSession() as session:
            payload = {"query": query, "session_id": "test_compare"}

            async with session.post("http://localhost:5000/v2/query/stream", json=payload) as response:
                agent_count = 0

                async for line in response.content:
                    if line:
                        try:
                            event = line.decode("utf-8").strip()
                            if event.startswith("data: "):
                                data = json.loads(event[6:])
                                if data.get("event") == "AGENT_COMPLETE":
                                    agent_count += 1
                        except:
                            pass

                print(f"\n📊 Anzahl ausgeführter Agenten: {agent_count}")

                if agent_count >= 8:
                    print("✅ EXCELLENT - 8+ Agenten (Intelligent Pipeline!)")
                elif agent_count >= 5:
                    print("✅ GUT - 5+ Agenten")
                else:
                    print("⚠️ NUR - {agent_count} Agenten (erwartet 8+)")

                return agent_count

    except Exception as e:
        print(f"❌ Fehler: {e}")
        return 0


async def main():
    """Hauptfunktion"""

    print("\n🧪 BACKEND API - INTELLIGENT PIPELINE INTEGRATION TEST")
    print("=" * 70)

    # Test 1: Integration Check
    result1 = await test_streaming_with_pipeline()

    # Test 2: Agent Count
    agent_count = await test_compare_agents()

    # Summary
    print("\n\n" + "=" * 70)
    print("🎯 GESAMT-ERGEBNIS")
    print("=" * 70)

    if result1:
        print("✅ Intelligent Pipeline wird genutzt")
    else:
        print("❌ Pipeline-Integration fehlgeschlagen")

    if agent_count >= 8:
        print("✅ Agent-Count optimal (8+)")
    elif agent_count >= 5:
        print("⚠️ Agent-Count OK (5+)")
    else:
        print("❌ Agent-Count zu niedrig")

    if result1 and agent_count >= 8:
        print("\n🎉 PHASE 2 ERFOLGREICH!")
        print("➡️ Backend nutzt Intelligent Pipeline")
        print("➡️ 8+ Agenten werden ausgeführt")
        print("➡️ Ready für Frontend-Test!")
    elif result1:
        print("\n⚠️ TEILWEISE ERFOLGREICH")
        print("➡️ Pipeline wird genutzt, aber weniger Agenten als erwartet")
    else:
        print("\n❌ FEHLGESCHLAGEN")
        print("➡️ Backend nutzt noch alte Mock-Funktion")
        print("➡️ Check Backend-Logs für Fehler")

    return result1


if __name__ == "__main__":
    print("\n⚠️ WICHTIG: Backend muss laufen!")
    print("Starte Backend mit: python start_backend.py\n")

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
