"""
Test für BuildingPermitWorker - Proof of Concept
Testet ob spezialisierte Agenten standalone funktionieren
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_building_permit():
    """Teste BuildingPermitWorker direkt"""
    
    print("=" * 60)
    print("🏗️  BuildingPermitWorker Standalone Test")
    print("=" * 60)
    
    try:
        from backend.agents.veritas_api_agent_construction import BuildingPermitWorker
        print("✅ Import erfolgreich: BuildingPermitWorker")
    except ImportError as e:
        print(f"❌ Import fehlgeschlagen: {e}")
        return False
    
    try:
        agent = BuildingPermitWorker()
        print("✅ Agent-Instanz erstellt")
    except Exception as e:
        print(f"❌ Instanziierung fehlgeschlagen: {e}")
        return False
    
    # Test Query
    query = "Baugenehmigung für Anbau in München"
    print(f"\n📝 Query: '{query}'")
    
    metadata = {
        'query': query,
        'location': 'München',
        'project_type': 'Anbau'
    }
    
    try:
        print("\n⏳ Führe Agent aus...")
        
        # Check if method is async
        if asyncio.iscoroutinefunction(agent._process_internal):
            result = await agent._process_internal(metadata)
        else:
            result = agent._process_internal(metadata)
        
        print("\n✅ Agent erfolgreich ausgeführt!")
        print("\n" + "=" * 60)
        print("📊 ERGEBNIS")
        print("=" * 60)
        
        if isinstance(result, dict):
            print(f"Status: {result.get('status', 'N/A')}")
            print(f"Confidence: {result.get('confidence_score', 0.0):.2f}")
            print(f"\nSummary:\n{result.get('summary', 'N/A')}")
            print(f"\nDetails:\n{result.get('details', 'N/A')}")
            print(f"\nSources: {result.get('sources', [])}")
            print(f"\nProcessing Time: {result.get('processing_time', 0.0)} sec")
            
            # Check if it's mock data
            is_mock = result.get('is_simulation', False)
            if is_mock:
                print("\n⚠️  WARNUNG: Agent gibt Mock-Daten zurück!")
                print(f"Grund: {result.get('simulation_reason', 'Unbekannt')}")
            else:
                print("\n✅ ECHTER AGENT - Keine Mock-Daten!")
            
            return True
        else:
            print(f"⚠️  Unerwartetes Result-Format: {type(result)}")
            print(result)
            return True  # Agent funktioniert, aber Format anders
            
    except Exception as e:
        print(f"\n❌ Agent-Execution fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_environmental():
    """Teste EnvironmentalAgent direkt"""
    
    print("\n\n" + "=" * 60)
    print("🌍 EnvironmentalAgent Standalone Test")
    print("=" * 60)
    
    try:
        from backend.agents.veritas_api_agent_environmental import EnvironmentalAgent
        print("✅ Import erfolgreich: EnvironmentalAgent")
    except ImportError as e:
        print(f"❌ Import fehlgeschlagen: {e}")
        return False
    
    try:
        agent = EnvironmentalAgent()
        print("✅ Agent-Instanz erstellt")
    except Exception as e:
        print(f"❌ Instanziierung fehlgeschlagen: {e}")
        return False
    
    query = "Luftqualität und Umweltbelastung in Berlin"
    print(f"\n📝 Query: '{query}'")
    
    try:
        print("\n⏳ Führe Agent aus...")
        
        # Check which method to use
        if hasattr(agent, 'process_query'):
            if asyncio.iscoroutinefunction(agent.process_query):
                result = await agent.process_query(query)
            else:
                result = agent.process_query(query)
        elif hasattr(agent, '_process_internal'):
            metadata = {'query': query}
            if asyncio.iscoroutinefunction(agent._process_internal):
                result = await agent._process_internal(metadata)
            else:
                result = agent._process_internal(metadata)
        else:
            print("⚠️  Keine bekannte Process-Methode gefunden")
            return False
        
        print("\n✅ Agent erfolgreich ausgeführt!")
        print("\n" + "=" * 60)
        print("📊 ERGEBNIS")
        print("=" * 60)
        
        if isinstance(result, dict):
            print(f"Status: {result.get('status', 'N/A')}")
            print(f"Confidence: {result.get('confidence_score', 0.0):.2f}")
            print(f"\nSummary:\n{result.get('summary', 'N/A')[:200]}...")
            print(f"\nSources: {len(result.get('sources', []))} Quellen")
            
            is_mock = result.get('is_simulation', False)
            if is_mock:
                print("\n⚠️  WARNUNG: Agent gibt Mock-Daten zurück!")
            else:
                print("\n✅ ECHTER AGENT - Keine Mock-Daten!")
            
            return True
        else:
            print(f"⚠️  Unerwartetes Result-Format: {type(result)}")
            return True
            
    except Exception as e:
        print(f"\n❌ Agent-Execution fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Hauptfunktion"""
    
    print("\n🚀 VERITAS Spezialisierte Agenten - Proof of Concept")
    print("=" * 60)
    
    results = []
    
    # Test BuildingPermitWorker
    result1 = await test_building_permit()
    results.append(("BuildingPermitWorker", result1))
    
    # Test EnvironmentalAgent
    result2 = await test_environmental()
    results.append(("EnvironmentalAgent", result2))
    
    # Summary
    print("\n\n" + "=" * 60)
    print("📊 ZUSAMMENFASSUNG")
    print("=" * 60)
    
    for agent_name, success in results:
        status = "✅ ERFOLGREICH" if success else "❌ FEHLGESCHLAGEN"
        print(f"{agent_name}: {status}")
    
    all_success = all(result for _, result in results)
    
    if all_success:
        print("\n🎉 Alle Agenten funktionieren!")
        print("➡️  Nächster Schritt: Integration in Intelligent Pipeline")
    else:
        print("\n⚠️  Einige Agenten haben Probleme")
        print("➡️  Bitte Fehler beheben bevor Integration")
    
    return all_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
