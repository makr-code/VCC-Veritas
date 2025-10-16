"""
UDS3 Database Check
===================
Prüft ob UDS3 konfiguriert ist und Datenbanken hat
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def check_uds3():
    """Prüfe UDS3 Verfügbarkeit und Konfiguration"""
    
    print("=" * 80)
    print("🔍 UDS3 DATABASE CHECK")
    print("=" * 80)
    
    # 1. Import UDS3
    print("\n1️⃣ Import UDS3...")
    try:
        from uds3.uds3_core import OptimizedUnifiedDatabaseStrategy, get_optimized_unified_strategy
        print("✅ UDS3 Core importiert")
    except ImportError as e:
        print(f"❌ UDS3 Import fehlgeschlagen: {e}")
        return
    
    # 2. Initialisiere UDS3
    print("\n2️⃣ Initialisiere UDS3...")
    try:
        uds3 = get_optimized_unified_strategy()
        if uds3:
            print("✅ UDS3 Strategy initialisiert")
        else:
            print("❌ UDS3 Strategy ist None")
            return
    except Exception as e:
        print(f"❌ UDS3 Initialisierung fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Prüfe verfügbare Datenbanken
    print("\n3️⃣ Prüfe verfügbare Datenbanken...")
    
    try:
        # Check if uds3 has databases configured
        has_vector = hasattr(uds3, 'vector_db') and uds3.vector_db is not None
        has_graph = hasattr(uds3, 'graph_db') and uds3.graph_db is not None
        has_relational = hasattr(uds3, 'relational_db') and uds3.relational_db is not None
        
        print(f"   Vector DB: {'✅ Konfiguriert' if has_vector else '❌ Nicht konfiguriert'}")
        print(f"   Graph DB: {'✅ Konfiguriert' if has_graph else '❌ Nicht konfiguriert'}")
        print(f"   Relational DB: {'✅ Konfiguriert' if has_relational else '❌ Nicht konfiguriert'}")
        
        if not (has_vector or has_graph or has_relational):
            print("\n⚠️ WARNUNG: Keine Datenbanken konfiguriert!")
            print("   UDS3 kann keine Queries ausführen ohne DB-Verbindungen")
            print("\n   Benötigt:")
            print("   - Vector DB (z.B. ChromaDB, Qdrant)")
            print("   - Graph DB (z.B. Neo4j) [optional]")
            print("   - Relational DB (z.B. SQLite, PostgreSQL) [optional]")
            return
    except Exception as e:
        print(f"⚠️ Fehler beim Prüfen der DBs: {e}")
    
    # 4. Test-Query
    print("\n4️⃣ Test-Query ausführen...")
    try:
        result = uds3.query_across_databases(
            vector_params={
                "query_text": "Bauvorschriften München",
                "top_k": 3,
                "threshold": 0.5
            },
            graph_params=None,
            relational_params=None,
            join_strategy="union"
        )
        
        print(f"✅ Query ausgeführt")
        print(f"   Success: {result.success if hasattr(result, 'success') else 'N/A'}")
        
        if hasattr(result, 'joined_results'):
            print(f"   Ergebnisse: {len(result.joined_results) if result.joined_results else 0}")
            
            if result.joined_results:
                print("\n   📄 Erste Ergebnisse:")
                for i, doc in enumerate(result.joined_results[:3], 1):
                    if isinstance(doc, dict):
                        content = doc.get('content', doc.get('text', ''))[:80]
                        score = doc.get('score', doc.get('similarity', 0))
                        print(f"      {i}. Score: {score:.2f} | {content}...")
            else:
                print("   ⚠️ Keine Ergebnisse gefunden")
                print("   Mögliche Gründe:")
                print("   - Vector DB ist leer")
                print("   - Keine passenden Dokumente")
                print("   - Threshold zu hoch")
        
        if hasattr(result, 'error'):
            print(f"   Error: {result.error}")
            
    except Exception as e:
        print(f"❌ Query fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
    
    # Zusammenfassung
    print("\n" + "=" * 80)
    print("📋 ZUSAMMENFASSUNG:")
    print("=" * 80)
    
    if has_vector or has_graph or has_relational:
        print("✅ UDS3 ist einsatzbereit")
        print("   - Queries können ausgeführt werden")
        print("   - Agents können echte Daten nutzen")
        
        if not (has_vector and has_graph and has_relational):
            print("\n💡 EMPFEHLUNG:")
            print("   Für optimale Ergebnisse alle 3 DB-Typen konfigurieren")
    else:
        print("❌ UDS3 ist NICHT einsatzbereit")
        print("   - Keine Datenbanken konfiguriert")
        print("   - Agents werden Fallback auf Mock-Daten nutzen")
        print("\n📚 Setup-Anleitung:")
        print("   1. Vector DB konfigurieren (ChromaDB/Qdrant)")
        print("   2. Optional: Graph DB (Neo4j)")
        print("   3. Optional: Relational DB (SQLite/PostgreSQL)")
    print("=" * 80)

if __name__ == "__main__":
    check_uds3()
