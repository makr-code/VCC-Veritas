"""
Test: UDS3 Integration - Echte Daten statt Mocks
=================================================

Testet ob die Mock-Funktionen erfolgreich durch echte UDS3 Queries ersetzt wurden.

Erwartetes Verhalten:
- Agent-Ergebnisse enthalten 'uds3_used': True
- Sources stammen aus UDS3 Datenbank (nicht mehr hardcoded)
- Details zeigen echte Dokument-Inhalte
- Confidence-Scores basieren auf Similarity-Scores
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.agents.veritas_intelligent_pipeline import (
    IntelligentMultiAgentPipeline,
    IntelligentPipelineRequest
)


async def test_uds3_integration():
    """Testet UDS3 Integration mit echter Query"""
    
    print("=" * 70)
    print("🧪 TEST: UDS3 INTEGRATION - ECHTE DATEN STATT MOCKS")
    print("=" * 70)
    
    # Pipeline initialisieren
    print("\n📦 Initialisiere Intelligent Multi-Agent Pipeline...")
    pipeline = IntelligentMultiAgentPipeline()
    success = await pipeline.initialize()
    
    if not success:
        print("❌ Pipeline-Initialisierung fehlgeschlagen!")
        return False
    
    print("✅ Pipeline erfolgreich initialisiert")
    
    # UDS3 Status prüfen
    if pipeline.uds3_strategy:
        print("✅ UDS3 Strategy ist verfügbar")
    else:
        print("⚠️ UDS3 Strategy NICHT verfügbar - Test wird Fallback-Modus verwenden")
    
    # Test Query
    query = "Welche Umweltauflagen gelten für Bauvorhaben in Stuttgart?"
    print(f"\n🔍 Test Query: {query}")
    
    # Pipeline Request erstellen
    request = IntelligentPipelineRequest(
        query_id="test_uds3_integration",
        query_text=query,
        session_id="test_session",
        enable_llm_commentary=False,
        enable_real_time_updates=False,
        max_parallel_agents=3,
        timeout=30
    )
    
    print("\n⏳ Führe Pipeline aus (max 30s)...")
    print("-" * 70)
    
    # Pipeline ausführen
    try:
        response = await pipeline.process_intelligent_query(request)
        
        print("\n✅ Pipeline-Execution erfolgreich!")
        print("=" * 70)
        
        # Analysiere Agent-Ergebnisse
        print("\n📊 AGENT-ERGEBNISSE ANALYSE:")
        print("=" * 70)
        
        uds3_agents = 0
        mock_agents = 0
        
        for agent_type, result in response.agent_results.items():
            if isinstance(result, dict):
                is_uds3 = result.get('uds3_used', False)
                confidence = result.get('confidence_score', 0)
                sources = result.get('sources', [])
                summary = result.get('summary', '')[:100]
                
                status_icon = "🟢" if is_uds3 else "🔴"
                print(f"\n{status_icon} Agent: {agent_type}")
                print(f"   - UDS3 genutzt: {is_uds3}")
                print(f"   - Confidence: {confidence:.2f}")
                print(f"   - Sources: {sources}")
                print(f"   - Summary: {summary}...")
                
                if is_uds3:
                    uds3_agents += 1
                else:
                    mock_agents += 1
        
        # Zusammenfassung
        print("\n" + "=" * 70)
        print("📈 ZUSAMMENFASSUNG:")
        print("=" * 70)
        print(f"✅ Agents mit UDS3-Daten: {uds3_agents}")
        print(f"🔴 Agents mit Mock-Daten: {mock_agents}")
        print(f"📝 Gesamt-Agents: {len(response.agent_results)}")
        print(f"⏱️ Processing Time: {response.processing_metadata.get('total_time', 0):.2f}s")
        
        # Finale Antwort
        print("\n" + "=" * 70)
        print("💬 FINALE ANTWORT:")
        print("=" * 70)
        print(response.response_text[:500])
        print("..." if len(response.response_text) > 500 else "")
        
        # Bewertung
        print("\n" + "=" * 70)
        if uds3_agents > 0:
            print("✅ ERFOLG: UDS3 Integration funktioniert!")
            print(f"   {uds3_agents} Agent(s) nutzen echte Datenbank-Daten")
        else:
            print("⚠️ WARNUNG: Keine UDS3-Daten gefunden")
            print("   Alle Agents nutzen Fallback Mock-Daten")
            print("   Mögliche Gründe:")
            print("   - UDS3 Datenbank ist leer")
            print("   - UDS3 nicht korrekt konfiguriert")
            print("   - Keine passenden Dokumente für Query")
        print("=" * 70)
        
        return uds3_agents > 0
        
    except Exception as e:
        print(f"\n❌ Pipeline-Execution fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_uds3_integration())
    sys.exit(0 if success else 1)
