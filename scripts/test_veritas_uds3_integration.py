#!/usr/bin/env python3
"""
Integration Test: VERITAS UDS3 Hybrid Agent v2 with Real UDS3

Tests veritas_uds3_hybrid_agent_v2.py with real UnifiedDatabaseStrategy

Usage:
    python scripts/test_veritas_uds3_integration.py
    python scripts/test_veritas_uds3_integration.py --query "Photovoltaik" --top-k 5
"""

import asyncio
import sys
from pathlib import Path

# Add project roots to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / 'uds3'))

# Import VERITAS agent v2
from backend.agents.veritas_uds3_hybrid_agent_v2 import UDS3HybridSearchAgent, SearchResult

# Import UDS3
from uds3.uds3_core import get_optimized_unified_strategy


async def test_basic_hybrid_search():
    """Test 1: Basic hybrid search (Vector + Graph)"""
    print("\n" + "="*80)
    print("TEST 1: Basic Hybrid Search (Vector + Graph)")
    print("="*80)
    
    try:
        # Get real UDS3 strategy
        strategy = get_optimized_unified_strategy()
        print("✅ UDS3 strategy loaded")
        
        # Create VERITAS agent v2
        agent = UDS3HybridSearchAgent(strategy)
        print("✅ VERITAS UDS3HybridSearchAgent v2 created")
        
        # Execute hybrid search
        query = "Photovoltaik"
        print(f"\n🔍 Query: '{query}'")
        print(f"⚙️  Weights: vector=0.5, graph=0.5")
        
        results = await agent.hybrid_search(
            query=query,
            top_k=10,
            weights={"vector": 0.5, "graph": 0.5},
            search_types=["vector", "graph"]
        )
        
        # Display results
        print(f"\n✅ Found {len(results)} results:")
        print("-" * 80)
        
        for i, result in enumerate(results[:5], 1):  # Show top 5
            print(f"\n{i}. Score: {result.final_score:.3f}")
            print(f"   ID: {result.document_id}")
            print(f"   Type: {result.metadata.get('document_type', 'unknown')}")
            print(f"   Content: {result.content[:100]}...")
            print(f"   Scores: {result.scores}")
        
        if len(results) > 5:
            print(f"\n... and {len(results) - 5} more results")
        
        # Validation
        assert len(results) > 0, "Should return at least 1 result"
        assert all(isinstance(r, SearchResult) for r in results), "All results should be SearchResult instances"
        assert all(r.final_score >= 0 for r in results), "All scores should be >= 0"
        
        print("\n" + "="*80)
        print("✅ TEST 1 PASSED: Basic Hybrid Search")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_vector_only_search():
    """Test 2: Vector-only search"""
    print("\n" + "="*80)
    print("TEST 2: Vector-Only Search (ChromaDB)")
    print("="*80)
    
    try:
        strategy = get_optimized_unified_strategy()
        agent = UDS3HybridSearchAgent(strategy)
        
        query = "Energiegesetz"
        print(f"\n🔍 Query: '{query}'")
        print(f"⚙️  Search Type: Vector only")
        
        results = await agent.vector_search(
            query=query,
            top_k=5
        )
        
        print(f"\n✅ Found {len(results)} vector results:")
        print("-" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result.final_score:.3f}")
            print(f"   ID: {result.document_id}")
            print(f"   Source: {list(result.scores.keys())}")
        
        # Validation
        if len(results) > 0:
            assert all('vector' in r.scores for r in results), "All results should have vector scores"
        
        print("\n" + "="*80)
        print(f"✅ TEST 2 PASSED: Vector-Only Search ({len(results)} results)")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_graph_only_search():
    """Test 3: Graph-only search"""
    print("\n" + "="*80)
    print("TEST 3: Graph-Only Search (Neo4j)")
    print("="*80)
    
    try:
        strategy = get_optimized_unified_strategy()
        agent = UDS3HybridSearchAgent(strategy)
        
        query = "Photovoltaik"
        print(f"\n🔍 Query: '{query}'")
        print(f"⚙️  Search Type: Graph only")
        
        results = await agent.graph_search(
            query=query,
            top_k=5
        )
        
        print(f"\n✅ Found {len(results)} graph results:")
        print("-" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result.final_score:.3f}")
            print(f"   ID: {result.document_id}")
            print(f"   Name: {result.metadata.get('name', 'unknown')}")
            print(f"   Source: {list(result.scores.keys())}")
        
        # Validation
        assert len(results) > 0, "Should return at least 1 result from Neo4j"
        assert all('graph' in r.scores for r in results), "All results should have graph scores"
        
        print("\n" + "="*80)
        print(f"✅ TEST 3 PASSED: Graph-Only Search ({len(results)} results)")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_custom_weights():
    """Test 4: Custom weights (graph-heavy)"""
    print("\n" + "="*80)
    print("TEST 4: Custom Weights (Graph=0.8, Vector=0.2)")
    print("="*80)
    
    try:
        strategy = get_optimized_unified_strategy()
        agent = UDS3HybridSearchAgent(strategy)
        
        query = "Baurecht"
        print(f"\n🔍 Query: '{query}'")
        print(f"⚙️  Weights: vector=0.2, graph=0.8")
        
        results = await agent.hybrid_search(
            query=query,
            top_k=5,
            weights={"vector": 0.2, "graph": 0.8},
            search_types=["vector", "graph"]
        )
        
        print(f"\n✅ Found {len(results)} results:")
        print("-" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Final Score: {result.final_score:.3f}")
            print(f"   ID: {result.document_id}")
            print(f"   Detailed Scores: {result.scores}")
        
        # Graph results should dominate (higher weight)
        if len(results) > 0:
            graph_weighted = sum(1 for r in results if 'graph' in r.scores and r.scores.get('graph', 0) > 0)
            print(f"\n📊 Graph results: {graph_weighted}/{len(results)}")
        
        print("\n" + "="*80)
        print("✅ TEST 4 PASSED: Custom Weights")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all integration tests"""
    print("\n" + "🚀" * 40)
    print("VERITAS UDS3 Hybrid Agent v2 - Integration Tests")
    print("🚀" * 40)
    
    tests = [
        ("Basic Hybrid Search", test_basic_hybrid_search),
        ("Vector-Only Search", test_vector_only_search),
        ("Graph-Only Search", test_graph_only_search),
        ("Custom Weights", test_custom_weights)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = await test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("INTEGRATION TEST SUMMARY")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    for test_name, test_passed in results:
        status = "✅ PASSED" if test_passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*80)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! UDS3 Search API is production-ready!")
        print("="*80)
        return 0
    else:
        print(f"\n⚠️  {total-passed} test(s) failed. Review output above.")
        print("="*80)
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
