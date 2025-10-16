#!/usr/bin/env python3
"""
Test UDS3 Database Connections (PostgreSQL, Neo4j, ChromaDB)
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_uds3_connections():
    """Test all UDS3 database connections"""
    print("=" * 80)
    print("UDS3 DATABASE CONNECTIONS TEST")
    print("=" * 80)
    print()
    
    try:
        from uds3.uds3_core import get_optimized_unified_strategy
        
        print("🔄 Initialisiere UDS3 Strategy...")
        uds3 = get_optimized_unified_strategy()
        print(f"✅ UDS3 Strategy erstellt: {uds3.__class__.__name__}")
        print()
        
        # Test 1: Check Database Manager
        if hasattr(uds3, 'db_manager'):
            print("📊 Database Manager Status:")
            print(f"   - DB Manager: {uds3.db_manager.__class__.__name__}")
            
            # Check backends
            backends = {
                'vector': uds3.db_manager.vector_backend,
                'graph': uds3.db_manager.graph_backend,
                'relational': uds3.db_manager.relational_backend
            }
            
            for name, backend in backends.items():
                if backend:
                    print(f"   - {name.upper()}: ✅ {backend.__class__.__name__}")
                else:
                    print(f"   - {name.upper()}: ❌ Nicht verfügbar")
            print()
        
        # Test 2: Try a simple query
        print("🔍 Teste UDS3 Query...")
        try:
            # First, create an embedding for the query
            query_text = "Taschengeldparagraph BGB § 110"
            
            # Try to get embedding from UDS3 (if available)
            embedding = None
            if hasattr(uds3, 'db_manager') and hasattr(uds3.db_manager, 'vector_backend'):
                try:
                    # Simple query without embedding first
                    print("   Teste Relational Query...")
                    result = uds3.query_across_databases(
                        relational_params={
                            "table": "documents",
                            "limit": 5
                        },
                        execution_mode="sequential"
                    )
                    
                    if result and hasattr(result, 'success') and result.success:
                        print(f"✅ Relational Query erfolgreich!")
                        print(f"   - Dokumente: {result.joined_count if hasattr(result, 'joined_count') else 0}")
                    else:
                        print(f"⚠️  Query lieferte keine Ergebnisse")
                        
                except Exception as rel_e:
                    print(f"❌ Relational Query fehlgeschlagen: {rel_e}")
            else:
                print("⚠️  Vector Backend nicht verfügbar - überspringe Query-Test")
            
        except Exception as query_e:
            print(f"❌ Query fehlgeschlagen: {query_e}")
            import traceback
            traceback.print_exc()
        
        print()
        print("=" * 80)
        print("TEST ABGESCHLOSSEN")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_uds3_connections())
