"""
Test UDS3 Multi-Database Integration
====================================

Tests all 4 UDS3 databases:
1. ChromaDB - Vector search
2. Neo4j - Knowledge graph
3. CouchDB - Document store
4. PostgreSQL - Relational queries

Usage:
    python tools\test_uds3_integration.py
"""
import os
import sys
from pathlib import Path
import logging

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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

from backend.database.uds3_integration import get_uds3_client, get_status, vector_search, graph_query, hybrid_search


def test_connection_status():
    """Test 1: Check connection status of all databases."""
    print("\n" + "=" * 80)
    print("TEST 1: Database Connection Status")
    print("=" * 80)
    
    print("\n→ Initializing UDS3 client...")
    uds3 = get_uds3_client()
    
    print("\n→ Checking database connections...")
    status = get_status()
    
    print("\n→ Connection Status:")
    for db_name, is_connected in status.items():
        status_icon = "✅" if is_connected else "❌"
        print(f"   {status_icon} {db_name}: {is_connected}")
    
    is_healthy = any(status.values())
    print(f"\n→ Health Check: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
    
    return uds3, status


def test_vector_search(uds3):
    """Test 2: ChromaDB vector search."""
    print("\n" + "=" * 80)
    print("TEST 2: Vector Search (ChromaDB)")
    print("=" * 80)
    
    status = get_status()
    if not status["chromadb"]:
        print("⏭️  Skipping: ChromaDB not available")
        return
    
    print("\n→ Searching for: 'air quality Munich'")
    
    try:
        results = vector_search("air quality Munich", top_k=5)
        
        print(f"\n✅ Found {len(results)} results")
        
        for i, result in enumerate(results[:3], 1):
            print(f"\n   Result {i}:")
            print(f"   - ID: {result.get('id', 'N/A')}")
            print(f"   - Score: {result.get('score', 0.0):.4f}")
            if result.get('content'):
                content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                print(f"   - Content: {content_preview}")
            if result.get('metadata'):
                print(f"   - Metadata: {result['metadata']}")
        
        return results
    
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_graph_query(uds3):
    """Test 3: Neo4j graph query."""
    print("\n" + "=" * 80)
    print("TEST 3: Knowledge Graph Query (Neo4j)")
    print("=" * 80)
    
    status = get_status()
    if not status["neo4j"]:
        print("⏭️  Skipping: Neo4j not available")
        return
    
    print("\n→ Querying graph: MATCH (n) RETURN count(n) as total")
    
    try:
        # Count total nodes
        results = graph_query("MATCH (n) RETURN count(n) as total")
        
        if results:
            print(f"\n✅ Total nodes in graph: {results[0].get('total', 0)}")
        
        # Get sample documents
        print("\n→ Fetching sample documents...")
        doc_results = graph_query("""
            MATCH (d:Document)
            RETURN d.id AS id, d.title AS title, d.domain AS domain
            LIMIT 5
        """)
        
        if doc_results:
            print(f"\n✅ Found {len(doc_results)} documents:")
            for i, doc in enumerate(doc_results, 1):
                print(f"   {i}. {doc.get('title', 'N/A')} (Domain: {doc.get('domain', 'N/A')})")
        else:
            print("⚠️  No documents found in graph")
        
        return doc_results
    
    except Exception as e:
        print(f"❌ Graph query failed: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_document_retrieval(uds3):
    """Test 4: CouchDB document retrieval."""
    print("\n" + "=" * 80)
    print("TEST 4: Document Store (CouchDB)")
    print("=" * 80)
    
    if not uds3.get_status()["couchdb"]:
        print("⏭️  Skipping: CouchDB not available")
        return
    
    print("\n→ Searching documents with selector...")
    
    try:
        # Search for environmental documents
        results = uds3.search_documents(
            selector={"domain": {"$exists": True}},
            fields=["_id", "title", "domain", "date"],
            limit=5
        )
        
        if results:
            print(f"\n✅ Found {len(results)} documents:")
            for i, doc in enumerate(results, 1):
                print(f"   {i}. {doc.get('title', 'N/A')} (Domain: {doc.get('domain', 'N/A')})")
        else:
            print("⚠️  No documents found")
        
        # Try to retrieve first document
        if results:
            doc_id = results[0].get('_id')
            print(f"\n→ Retrieving full document: {doc_id}")
            
            full_doc = uds3.get_document(doc_id)
            if full_doc:
                print(f"✅ Document retrieved successfully")
                print(f"   Keys: {list(full_doc.keys())[:10]}")  # Show first 10 keys
        
        return results
    
    except Exception as e:
        print(f"❌ Document retrieval failed: {e}")
        return []


def test_sql_query(uds3):
    """Test 5: PostgreSQL relational query."""
    print("\n" + "=" * 80)
    print("TEST 5: Relational Database (PostgreSQL)")
    print("=" * 80)
    
    if not uds3.get_status()["postgresql"]:
        print("⏭️  Skipping: PostgreSQL not available")
        return
    
    print("\n→ Querying research plans...")
    
    try:
        # Query research plans
        results = uds3.sql_query("""
            SELECT plan_id, research_question, status, progress_percentage
            FROM research_plans
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if results:
            print(f"\n✅ Found {len(results)} plans:")
            for i, plan in enumerate(results, 1):
                print(f"   {i}. {plan['plan_id']}")
                print(f"      Question: {plan['research_question'][:60]}...")
                print(f"      Status: {plan['status']} ({plan['progress_percentage']}%)")
        else:
            print("⚠️  No research plans found")
        
        # Count steps
        print("\n→ Counting plan steps...")
        step_count = uds3.sql_query("SELECT COUNT(*) as total FROM research_plan_steps")
        if step_count:
            print(f"✅ Total steps: {step_count[0]['total']}")
        
        return results
    
    except Exception as e:
        print(f"❌ SQL query failed: {e}")
        return []


def test_hybrid_search(uds3):
    """Test 6: Multi-database hybrid search."""
    print("\n" + "=" * 80)
    print("TEST 6: Hybrid Search (Multi-Database)")
    print("=" * 80)
    
    status = get_status()
    available_dbs = [db for db, connected in status.items() if connected]
    
    if not available_dbs:
        print("⏭️  Skipping: No databases available")
        return
    
    print(f"\n→ Available databases: {', '.join(available_dbs)}")
    print("→ Performing hybrid search for: 'environmental regulations'")
    
    try:
        results = hybrid_search(
            query="environmental regulations",
            top_k=5,
            domains=["environmental"]
        )
        
        print(f"\n✅ Hybrid search complete:")
        print(f"   - Type: {type(results)}")
        print(f"   - Keys: {list(results.keys()) if isinstance(results, dict) else 'Not a dict'}")
        
        if isinstance(results, dict):
            if 'results' in results:
                print(f"   - Results count: {len(results['results'])}")
            if 'metadata' in results:
                print(f"   - Metadata: {results['metadata']}")
        
        return results
    
    except Exception as e:
        print(f"❌ Hybrid search failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all UDS3 integration tests."""
    print("=" * 80)
    print("VERITAS UDS3 Multi-Database Integration Test")
    print("=" * 80)
    
    # Test 1: Connection status
    uds3, status = test_connection_status()
    
    if not uds3.is_healthy():
        print("\n❌ ERROR: No databases available! Please check configuration.")
        return
    
    # Test 2: Vector search
    test_vector_search(uds3)
    
    # Test 3: Graph query
    test_graph_query(uds3)
    
    # Test 4: Document retrieval
    test_document_retrieval(uds3)
    
    # Test 5: SQL query
    test_sql_query(uds3)
    
    # Test 6: Hybrid search
    test_hybrid_search(uds3)
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    connected_count = sum(1 for connected in status.values() if connected)
    total_count = len(status)
    
    print(f"\n✅ Connected databases: {connected_count}/{total_count}")
    for db_name, is_connected in status.items():
        status_icon = "✅" if is_connected else "❌"
        print(f"   {status_icon} {db_name}")
    
    print("\n" + "=" * 80)
    print("✅ UDS3 Integration Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
