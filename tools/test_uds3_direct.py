"""
Test Direct UDS3 Integration
============================

Verwendet die zentrale UDS3 UnifiedDatabaseStrategy direkt
ohne zusätzliche Wrapper.

Usage:
    python tools\test_uds3_direct.py
"""
import os
import sys
from pathlib import Path
import logging

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add UDS3 to path
uds3_path = project_root.parent / "uds3"
if str(uds3_path) not in sys.path:
    sys.path.insert(0, str(uds3_path))

# Configure environment
os.environ.setdefault("POSTGRES_HOST", "192.168.178.94")
os.environ.setdefault("POSTGRES_DATABASE", "veritas")
os.environ.setdefault("CHROMA_HOST", "192.168.178.94")
os.environ.setdefault("NEO4J_URI", "bolt://192.168.178.94:7687")
os.environ.setdefault("COUCHDB_HOST", "192.168.178.94")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test direct UDS3 usage."""
    print("=" * 80)
    print("VERITAS Direct UDS3 Integration Test")
    print("=" * 80)
    
    # Import UDS3
    print("\n→ Importing UDS3 core...")
    try:
        from uds3_core import UnifiedDatabaseStrategy
        print("✅ UDS3 core imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import UDS3: {e}")
        print("\nTrying alternative import...")
        try:
            from uds3.uds3_core import UnifiedDatabaseStrategy
            print("✅ UDS3 core imported successfully (alternative path)")
        except ImportError as e2:
            print(f"❌ Failed to import UDS3 (alternative): {e2}")
            return
    
    # Initialize UDS3
    print("\n→ Initializing UDS3 with default config...")
    try:
        uds3 = UnifiedDatabaseStrategy()
        print("✅ UDS3 initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize UDS3: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 1: Check available databases
    print("\n" + "=" * 80)
    print("TEST 1: Available Databases")
    print("=" * 80)
    
    print("\n→ Checking database availability...")
    
    # ChromaDB
    if hasattr(uds3, 'chromadb') and uds3.chromadb:
        print("✅ ChromaDB: Available")
    else:
        print("❌ ChromaDB: Not available")
    
    # Neo4j
    if hasattr(uds3, 'neo4j') and uds3.neo4j:
        print("✅ Neo4j: Available")
    else:
        print("❌ Neo4j: Not available")
    
    # PostgreSQL
    if hasattr(uds3, 'relational') and uds3.relational:
        print("✅ PostgreSQL: Available")
    else:
        print("❌ PostgreSQL: Not available")
    
    # CouchDB
    if hasattr(uds3, 'file_storage') and uds3.file_storage:
        print("✅ CouchDB/File Storage: Available")
    else:
        print("❌ CouchDB/File Storage: Not available")
    
    # Test 2: Vector Search (if available)
    print("\n" + "=" * 80)
    print("TEST 2: Vector Search")
    print("=" * 80)
    
    if hasattr(uds3, 'chromadb') and uds3.chromadb:
        print("\n→ Performing vector search...")
        try:
            # Check if query method exists
            if hasattr(uds3.chromadb, 'query_vectors'):
                results = uds3.chromadb.query_vectors(
                    query_texts=["air quality Munich"],
                    n_results=5
                )
                print(f"✅ Vector search returned {len(results)} results")
                if results:
                    print(f"   First result ID: {results[0].get('id', 'N/A')}")
            elif hasattr(uds3.chromadb, 'search'):
                results = uds3.chromadb.search(
                    query="air quality Munich",
                    top_k=5
                )
                print(f"✅ Vector search returned {len(results)} results")
            else:
                print("⚠️  ChromaDB has no known query method")
                print(f"   Available methods: {[m for m in dir(uds3.chromadb) if not m.startswith('_')][:10]}")
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
    else:
        print("⏭️  Skipping: ChromaDB not available")
    
    # Test 3: Graph Query (if available)
    print("\n" + "=" * 80)
    print("TEST 3: Knowledge Graph")
    print("=" * 80)
    
    if hasattr(uds3, 'neo4j') and uds3.neo4j:
        print("\n→ Querying Neo4j graph...")
        try:
            # Check available methods
            if hasattr(uds3.neo4j, 'execute_cypher'):
                results = uds3.neo4j.execute_cypher("MATCH (n) RETURN count(n) as total")
                print(f"✅ Graph query successful")
                if results:
                    print(f"   Total nodes: {results[0].get('total', 'N/A')}")
            elif hasattr(uds3.neo4j, 'query'):
                results = uds3.neo4j.query("MATCH (n) RETURN count(n) as total")
                print(f"✅ Graph query successful")
            else:
                print("⚠️  Neo4j has no known query method")
                print(f"   Available methods: {[m for m in dir(uds3.neo4j) if not m.startswith('_')][:10]}")
        except Exception as e:
            print(f"❌ Graph query failed: {e}")
    else:
        print("⏭️  Skipping: Neo4j not available")
    
    # Test 4: Relational Query (if available)
    print("\n" + "=" * 80)
    print("TEST 4: Relational Database")
    print("=" * 80)
    
    if hasattr(uds3, 'relational') and uds3.relational:
        print("\n→ Querying PostgreSQL...")
        try:
            # Check available methods
            if hasattr(uds3.relational, 'execute_query'):
                results = uds3.relational.execute_query(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5"
                )
                print(f"✅ SQL query successful")
                if results:
                    print(f"   Found {len(results)} tables")
                    for row in results[:3]:
                        print(f"   - {row.get('table_name', 'N/A')}")
            elif hasattr(uds3.relational, 'query'):
                results = uds3.relational.query(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5"
                )
                print(f"✅ SQL query successful")
            else:
                print("⚠️  PostgreSQL has no known query method")
                print(f"   Available methods: {[m for m in dir(uds3.relational) if not m.startswith('_')][:10]}")
        except Exception as e:
            print(f"❌ SQL query failed: {e}")
    else:
        print("⏭️  Skipping: PostgreSQL not available")
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    print("\n✅ Direct UDS3 integration test complete!")
    print(f"   UDS3 instance: {type(uds3).__name__}")
    print(f"   Available attributes: {len([a for a in dir(uds3) if not a.startswith('_')])}")
    
    print("\n→ Key UDS3 components:")
    for attr in ['chromadb', 'neo4j', 'relational', 'file_storage', 'saga', 'crud']:
        if hasattr(uds3, attr):
            value = getattr(uds3, attr)
            status = "✅" if value else "❌"
            print(f"   {status} {attr}: {type(value).__name__ if value else 'None'}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
