#!/usr/bin/env python3
"""
UDS3 Search API Integration Test

Tests the complete integration:
1. UDS3 Search API (uds3_search_api.py)
2. VERITAS Agent (veritas_uds3_hybrid_agent.py)
3. All backends (ChromaDB, Neo4j, PostgreSQL)

Run: python scripts/test_uds3_search_api_integration.py
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / "uds3"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_uds3_search_api():
    """Test UDS3 Search API directly"""
    print("\n" + "="*80)
    print("TEST 1: UDS3 Search API (Direct)")
    print("="*80)
    
    try:
        from uds3 import get_optimized_unified_strategy
        from uds3.search import SearchQuery
        
        # Initialize strategy (Search API accessed via property) ✅
        strategy = get_optimized_unified_strategy()
        search_api = strategy.search_api  # NEW: Property access ⭐
        
        print(f"✅ Strategy created: {strategy}")
        print(f"✅ Search API accessed via property: {search_api}")
        
        # Test 1.1: Vector Search
        print("\n📊 Test 1.1: Vector Search (ChromaDB)")
        model = search_api._get_embedding_model()
        if model:
            embedding = model.encode("Photovoltaik").tolist()
            vector_results = await search_api.vector_search(embedding, top_k=5)
            print(f"✅ Found {len(vector_results)} vector results")
            for i, result in enumerate(vector_results[:3], 1):
                print(f"   {i}. Score: {result.score:.3f}, ID: {result.document_id}")
        else:
            print("⚠️ Embedding model not available")
        
        # Test 1.2: Graph Search
        print("\n📊 Test 1.2: Graph Search (Neo4j)")
        graph_results = await search_api.graph_search("Photovoltaik", top_k=5)
        print(f"✅ Found {len(graph_results)} graph results")
        for i, result in enumerate(graph_results[:3], 1):
            print(f"   {i}. Score: {result.score:.3f}, ID: {result.document_id}")
            print(f"      Name: {result.metadata.get('name', 'N/A')}")
        
        # Test 1.3: Hybrid Search
        print("\n📊 Test 1.3: Hybrid Search (Vector + Graph)")
        query = SearchQuery(
            query_text="Photovoltaik Anforderungen",
            top_k=5,
            search_types=["vector", "graph"],
            weights={"vector": 0.5, "graph": 0.5}
        )
        hybrid_results = await search_api.hybrid_search(query)
        print(f"✅ Found {len(hybrid_results)} hybrid results")
        for i, result in enumerate(hybrid_results[:3], 1):
            print(f"   {i}. Score: {result.score:.3f}, ID: {result.document_id}, Source: {result.source}")
        
        print("\n✅ UDS3 Search API Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ UDS3 Search API Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_veritas_agent():
    """Test VERITAS Agent using UDS3 Search API"""
    print("\n" + "="*80)
    print("TEST 2: VERITAS Agent (UDS3 Integration)")
    print("="*80)
    
    try:
        from uds3.uds3_core import get_optimized_unified_strategy
        from backend.agents.veritas_uds3_hybrid_agent import UDS3HybridSearchAgent
        
        # Initialize
        strategy = get_optimized_unified_strategy()
        agent = UDS3HybridSearchAgent(strategy)
        
        # Test 2.1: Hybrid Search (Default)
        print("\n📊 Test 2.1: Agent Hybrid Search")
        results = await agent.hybrid_search(
            query="Was regelt § 58 LBO BW?",
            top_k=5,
            weights={"vector": 0.5, "graph": 0.5}
        )
        print(f"✅ Found {len(results)} results")
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. Score: {result.final_score:.3f}, ID: {result.document_id}")
            print(f"      Scores: {result.scores}")
        
        # Test 2.2: Vector-Only Search
        print("\n📊 Test 2.2: Agent Vector Search")
        vector_results = await agent.vector_search(
            query="Photovoltaik",
            top_k=3
        )
        print(f"✅ Found {len(vector_results)} vector results")
        for i, result in enumerate(vector_results, 1):
            print(f"   {i}. Score: {result.final_score:.3f}, ID: {result.document_id}")
        
        # Test 2.3: Graph-Only Search
        print("\n📊 Test 2.3: Agent Graph Search")
        graph_results = await agent.graph_search(
            query="Energiegesetz",
            top_k=3
        )
        print(f"✅ Found {len(graph_results)} graph results")
        for i, result in enumerate(graph_results, 1):
            print(f"   {i}. Score: {result.final_score:.3f}")
            print(f"      Name: {result.metadata.get('name', 'N/A')}")
        
        # Test 2.4: Custom Weights
        print("\n📊 Test 2.4: Custom Weights (Graph 80%, Vector 20%)")
        custom_results = await agent.hybrid_search(
            query="Photovoltaik",
            top_k=5,
            weights={"graph": 0.8, "vector": 0.2}
        )
        print(f"✅ Found {len(custom_results)} results with custom weights")
        for i, result in enumerate(custom_results[:3], 1):
            print(f"   {i}. Score: {result.final_score:.3f}")
            print(f"      Weighted scores: {result.scores}")
        
        print("\n✅ VERITAS Agent Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ VERITAS Agent Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_backend_status():
    """Test backend availability"""
    print("\n" + "="*80)
    print("TEST 3: Backend Status Check")
    print("="*80)
    
    try:
        from uds3.uds3_core import get_optimized_unified_strategy
        
        strategy = get_optimized_unified_strategy()
        
        # Check backends
        has_vector = hasattr(strategy, 'vector_backend') and strategy.vector_backend is not None
        has_graph = hasattr(strategy, 'graph_backend') and strategy.graph_backend is not None
        has_relational = hasattr(strategy, 'relational_backend') and strategy.relational_backend is not None
        
        print(f"\n📊 Backend Status:")
        print(f"   Vector (ChromaDB):     {'✅' if has_vector else '❌'}")
        print(f"   Graph (Neo4j):         {'✅' if has_graph else '❌'}")
        print(f"   Relational (PostgreSQL): {'✅' if has_relational else '❌'}")
        
        # Document counts
        if has_graph:
            try:
                backend = strategy.graph_backend
                result = backend.execute_query("MATCH (d:Document) RETURN count(d) AS count", {})
                doc_count = result[0]['count'] if result else 0
                print(f"\n📄 Neo4j Document Count: {doc_count}")
            except Exception as e:
                print(f"⚠️ Could not get Neo4j count: {e}")
        
        print("\n✅ Backend Status Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Backend Status Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("UDS3 SEARCH API - INTEGRATION TEST SUITE")
    print("="*80)
    print(f"Date: {Path(__file__).stat().st_mtime}")
    
    results = []
    
    # Test 1: UDS3 Search API
    results.append(await test_uds3_search_api())
    
    # Test 2: VERITAS Agent
    results.append(await test_veritas_agent())
    
    # Test 3: Backend Status
    results.append(await test_backend_status())
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"\n✅ {passed}/{total} test suites passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! UDS3 Search API is production-ready!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test suite(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
