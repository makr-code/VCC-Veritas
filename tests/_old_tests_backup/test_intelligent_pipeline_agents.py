"""
Test der Intelligent Pipeline mit echten Agent-Aufrufen
Prüft ob Pipeline _execute_real_agent() korrekt funktioniert
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_intelligent_pipeline():
    """Teste IntelligentPipeline direkt"""

    print("=" * 60)
    print("🧠 Intelligent Pipeline Test")
    print("=" * 60)

    try:
        from backend.agents.veritas_intelligent_pipeline import IntelligentMultiAgentPipeline

        print("✅ Import erfolgreich: IntelligentMultiAgentPipeline")
    except ImportError as e:
        print(f"❌ Import fehlgeschlagen: {e}")
        import traceback

        traceback.print_exc()
        return False

    try:
        pipeline = IntelligentMultiAgentPipeline(max_workers=3)
        print("✅ Pipeline-Instanz erstellt")
    except Exception as e:
        print(f"❌ Pipeline-Instanziierung fehlgeschlagen: {e}")
        import traceback

        traceback.print_exc()
        return False

    try:
        print("\n⏳ Initialisiere Pipeline...")
        await pipeline.initialize()
        print("✅ Pipeline initialisiert")
    except Exception as e:
        print(f"⚠️  Pipeline-Initialisierung fehlgeschlagen: {e}")
        # Continue trotzdem - viele Features sind optional

    # Test _execute_real_agent direkt
    print("\n" + "=" * 60)
    print("📝 Test: _execute_real_agent()")
    print("=" * 60)

    test_agents = [
        ("construction", "Baugenehmigung für Anbau in München"),
        ("environmental", "Luftqualität in Berlin"),
        ("geo_context", "Geografische Informationen zu Hamburg"),
    ]

    results = []

    for agent_type, query in test_agents:
        print(f"\n🔍 Test Agent: {agent_type}")
        print(f"   Query: {query}")

        try:
            result = pipeline._execute_real_agent(agent_type=agent_type, query=query, rag_context={})

            if result:
                is_mock = result.get("is_simulation", False)
                is_specialized = result.get("specialized_agent_used", False)
                is_uds3 = result.get("uds3_used", False)

                if is_specialized:
                    status = "✅ SPEZIALIZED"
                elif is_uds3:
                    status = "✅ UDS3"
                elif is_mock:
                    status = "🔴 MOCK"
                else:
                    status = "⚠️  UNKNOWN"

                print(f"   Status: {status}")
                print(f"   Summary: {result.get('summary', 'N/A')[:80]}...")
                print(f"   Confidence: {result.get('confidence_score', 0.0):.2f}")
                print(f"   Sources: {len(result.get('sources', []))}")

                results.append((agent_type, status, not is_mock))
            else:
                print(f"   ❌ Keine Ergebnisse")
                results.append((agent_type, "❌ NO RESULT", False))

        except Exception as e:
            print(f"   ❌ Fehler: {e}")
            import traceback

            traceback.print_exc()
            results.append((agent_type, "❌ ERROR", False))

    # Summary
    print("\n\n" + "=" * 60)
    print("📊 ZUSAMMENFASSUNG")
    print("=" * 60)

    for agent, status, is_real in results:
        print(f"{agent:20s}: {status}")

    real_count = sum(1 for _, _, is_real in results if is_real)
    total_count = len(results)

    print(f"\n📈 Echte Agenten: {real_count}/{total_count}")
    print(f"📈 Mock-Agenten: {total_count - real_count}/{total_count}")

    if real_count > 0:
        print("\n🎉 Mindestens ein echter Agent funktioniert!")
        print("➡️  Spezialisierte Agenten sind verfügbar")
        return True
    else:
        print("\n⚠️  Nur Mock-Daten - UDS3 und spezialisierte Agenten nicht verfügbar")
        print("➡️  Integration der spezialisierten Agenten erforderlich")
        return False


async def test_full_pipeline():
    """Teste komplette Pipeline mit Query"""

    print("\n\n" + "=" * 60)
    print("🚀 Kompletter Pipeline-Test")
    print("=" * 60)

    try:
        from backend.agents.veritas_intelligent_pipeline import IntelligentMultiAgentPipeline, IntelligentPipelineRequest
    except ImportError as e:
        print(f"❌ Import fehlgeschlagen: {e}")
        return False

    pipeline = IntelligentMultiAgentPipeline(max_workers=3)

    try:
        await pipeline.initialize()
    except:
        pass

    # Test Query
    query = "Welche Unterlagen benötige ich für eine Baugenehmigung in München?"
    print(f"\n📝 Query: '{query}'")

    import uuid

    request = IntelligentPipelineRequest(
        query_id=str(uuid.uuid4()),
        query_text=query,
        session_id="test_session",
        enable_llm_commentary=False,  # Für schnelleren Test
        enable_supervisor=False,
        timeout=30,
    )

    try:
        print("\n⏳ Führe Pipeline aus...")
        response = await pipeline.process_intelligent_query(request)

        print("\n✅ Pipeline erfolgreich!")
        print(f"\nResponse Text (erste 300 Zeichen):")
        print(response.response_text[:300] + "...")

        print(f"\nAgent Results:")
        for agent, result in response.agent_results.items():
            is_mock = result.get("is_simulation", False)
            status = "🔴 MOCK" if is_mock else "✅ REAL"
            print(f"  {agent}: {status}")

        print(f"\nConfidence: {response.confidence_score:.2f}")
        print(f"Processing Time: {response.total_processing_time:.2f}s")

        return True

    except Exception as e:
        print(f"\n❌ Pipeline-Execution fehlgeschlagen: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Hauptfunktion"""

    print("\n🧪 VERITAS Intelligent Pipeline - Agent Integration Test")
    print("=" * 60)

    # Test 1: Direkte Agent-Execution
    result1 = await test_intelligent_pipeline()

    # Test 2: Komplette Pipeline
    result2 = await test_full_pipeline()

    print("\n\n" + "=" * 60)
    print("🎯 GESAMT-ERGEBNIS")
    print("=" * 60)

    if result1:
        print("✅ Direkte Agent-Execution funktioniert")
    else:
        print("❌ Direkte Agent-Execution nur mit Mock")

    if result2:
        print("✅ Komplette Pipeline funktioniert")
    else:
        print("❌ Komplette Pipeline hat Probleme")

    if result1 or result2:
        print("\n🎉 Pipeline ist einsatzbereit!")
        print("➡️  Nächster Schritt: Integration in Backend API")
    else:
        print("\n⚠️  Pipeline benötigt weitere Konfiguration")

    return result1 or result2


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
