"""
UDS3 Data Check - Prüft ob UDS3 Daten enthält
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def check_uds3_data():
    """Prüft UDS3 Daten-Status"""
    print("=" * 80)
    print("UDS3 DATA CHECK")
    print("=" * 80)
    print()

    try:
        from uds3.uds3_core import get_optimized_unified_strategy

        print("🔄 Initialisiere UDS3 Strategy...")
        uds3 = get_optimized_unified_strategy()
        print(f"✅ UDS3 Strategy: {uds3.__class__.__name__}")
        print()

        # Test Vector Search
        print("📊 Test 1: Vector Search")
        try:
            # Try a simple query
            if hasattr(uds3, "vector_search"):
                results = await uds3.vector_search(query_text="BGB Vertragsrecht", top_k=5)
                print(f"   ✅ Vector Search funktioniert")
                print(f"   📄 Gefunden: {len(results)} Dokumente")
                if results:
                    print(f"   🔍 Erstes Ergebnis: {results[0].get('doc_id', 'N/A')}")
                else:
                    print(f"   ⚠️ KEINE DOKUMENTE INDEXIERT")
            else:
                print(f"   ❌ vector_search Methode nicht gefunden")
                # Try query_across_databases
                if hasattr(uds3, "query_across_databases"):
                    print(f"   🔄 Versuche query_across_databases...")
                    result = uds3.query_across_databases(
                        vector_params={"query_text": "test", "top_k": 5}, graph_params=None, relational_params=None
                    )
                    docs = result.get("documents", [])
                    print(f"   📄 Gefunden: {len(docs)} Dokumente")
                    if docs:
                        print(f"   ✅ UDS3 enthält Daten!")
                    else:
                        print(f"   ⚠️ UDS3 ist LEER - Keine Dokumente gefunden")
        except Exception as e:
            print(f"   ❌ Vector Search Error: {e}")

        print()

        # Test Database Manager
        print("📊 Test 2: Database Manager")
        if hasattr(uds3, "db_manager"):
            dm = uds3.db_manager
            print(f"   ✅ DB Manager verfügbar: {dm.__class__.__name__}")

            # Check backends
            if hasattr(dm, "vector_backend") and dm.vector_backend:
                print(f"   ✅ Vector Backend: {dm.vector_backend.__class__.__name__}")
                # Try to get collection info
                if hasattr(dm.vector_backend, "collection") and dm.vector_backend.collection:
                    try:
                        count = dm.vector_backend.collection.count()
                        print(f"   📄 Vector DB Dokumente: {count}")
                    except Exception as e:
                        print(f"   ⚠️ Kann Dokumenten-Anzahl nicht abrufen: {e}")
            else:
                print(f"   ❌ Vector Backend nicht initialisiert")

            if hasattr(dm, "graph_backend") and dm.graph_backend:
                print(f"   ✅ Graph Backend: {dm.graph_backend.__class__.__name__}")
            else:
                print(f"   ⚠️ Graph Backend nicht verfügbar")

            if hasattr(dm, "relational_backend") and dm.relational_backend:
                print(f"   ✅ Relational Backend: {dm.relational_backend.__class__.__name__}")
            else:
                print(f"   ⚠️ Relational Backend nicht verfügbar")
        else:
            print(f"   ❌ DB Manager nicht verfügbar")

        print()
        print("=" * 80)
        print("ZUSAMMENFASSUNG:")
        print("=" * 80)

        # Check if we found any data
        has_data = False
        try:
            if hasattr(uds3, "db_manager") and uds3.db_manager.vector_backend:
                if hasattr(uds3.db_manager.vector_backend, "collection"):
                    count = uds3.db_manager.vector_backend.collection.count()
                    has_data = count > 0
                    print(f"📊 Vector DB Status: {count} Dokumente")
        except:
            pass

        if has_data:
            print("✅ UDS3 ist BEREIT - Daten vorhanden!")
            print("➡️ Sie können direkt mit Staging Phase 1 starten")
            return True
        else:
            print("⚠️ UDS3 ist LEER - Keine Dokumente indexiert")
            print("➡️ Sie müssen zuerst Dokumente indexieren")
            print()
            print("Optionen:")
            print("  A) Demo-Corpus erstellen und indexieren (schnell)")
            print("  B) Produktiv-Daten indexieren (empfohlen)")
            return False

    except ImportError as e:
        print(f"❌ UDS3 Import-Fehler: {e}")
        print("➡️ UDS3 muss installiert werden")
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(check_uds3_data())
    sys.exit(0 if result else 1)
