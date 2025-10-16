#!/usr/bin/env python3
"""
Test UDS3 Hybrid Search Agent

Usage:
    python scripts/test_uds3_hybrid.py
    python scripts/test_uds3_hybrid.py --query "Photovoltaik Baugenehmigung"
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Add UDS3 to path (lokales Modul in c:\VCC\uds3)
uds3_path = Path("c:/VCC/uds3")
if uds3_path.exists() and str(uds3_path) not in sys.path:
    sys.path.insert(0, str(uds3_path))

try:
    from uds3.uds3_core import UnifiedDatabaseStrategy, get_optimized_unified_strategy
    UDS3_AVAILABLE = True
except ImportError:
    UDS3_AVAILABLE = False
    print("⚠️  UDS3 nicht gefunden!")
    print("   Stelle sicher dass c:\\VCC\\uds3 existiert")
    sys.exit(1)

from backend.agents.veritas_uds3_hybrid_agent import UDS3HybridSearchAgent


def print_separator(char="=", length=80):
    """Print separator line"""
    print(char * length)


def print_result(result, index: int):
    """Print single search result"""
    print(f"\n{index}. Score: {result.final_score:.3f}")
    print(f"   ID: {result.document_id}")
    print(f"   Title: {result.metadata.get('title', 'N/A')}")
    print(f"   Type: {result.metadata.get('document_type', 'N/A')}")
    print(f"   Scores Breakdown:")
    print(f"     Vector:  {result.scores['vector']:.3f}")
    print(f"     Keyword: {result.scores['keyword']:.3f}")
    print(f"     Graph:   {result.scores['graph']:.3f}")
    print(f"   Content (first 150 chars):")
    print(f"     {result.content[:150]}...")


async def test_hybrid_search(query: str):
    """Test hybrid search with sample query"""
    
    print_separator()
    print("🔍 UDS3 Hybrid Search Test")
    print_separator()
    print(f"Query: {query}")
    print_separator()
    
    # Initialize UDS3 Strategy
    strategy = get_optimized_unified_strategy()
    agent = UDS3HybridSearchAgent(strategy)
    
    # Check backends
    print("\n📊 Available Backends:")
    print(f"  Vector (ChromaDB):    {'✅' if strategy.vector_backend else '❌'}")
    print(f"  Metadata (PostgreSQL): {'✅' if strategy.relational_backend else '❌'}")
    print(f"  Graph (Neo4j):         {'✅' if strategy.graph_backend else '❌'}")
    
    if not (strategy.vector_backend or strategy.relational_backend):
        print("\n❌ Keine Backends verfügbar!")
        print("   → Kann Hybrid Search nicht durchführen")
        return
    
    # Test 1: Hybrid Search (Default Weights)
    print("\n" + "=" * 80)
    print("Test 1: Hybrid Search (Default Weights)")
    print("=" * 80)
    print("Weights: Vector=0.5, Keyword=0.3, Graph=0.2")
    
    results = await agent.hybrid_search(
        query=query,
        top_k=5
    )
    
    print(f"\n✅ Found {len(results)} results")
    
    for i, result in enumerate(results, 1):
        print_result(result, i)
    
    # Test 2: Vector-Only Search
    if strategy.vector_backend is not None:
        print("\n" + "=" * 80)
        print("Test 2: Vector-Only Search")
        print("=" * 80)
        print("Weights: Vector=1.0, Keyword=0.0, Graph=0.0")
        
        results_vector = await agent.vector_search_only(
            query=query,
            top_k=5
        )
        
        print(f"\n✅ Found {len(results_vector)} results")
        
        for i, result in enumerate(results_vector, 1):
            print_result(result, i)
    
    # Test 3: Keyword-Only Search
    if strategy.relational_backend is not None:
        print("\n" + "=" * 80)
        print("Test 3: Keyword-Only Search")
        print("=" * 80)
        print("Weights: Vector=0.0, Keyword=1.0, Graph=0.0")
        
        results_keyword = await agent.keyword_search_only(
            query=query,
            top_k=5
        )
        
        print(f"\n✅ Found {len(results_keyword)} results")
        
        for i, result in enumerate(results_keyword, 1):
            print_result(result, i)
    
    # Test 4: Custom Weights
    print("\n" + "=" * 80)
    print("Test 4: Custom Weights (Heavy Vector)")
    print("=" * 80)
    print("Weights: Vector=0.7, Keyword=0.2, Graph=0.1")
    
    results_custom = await agent.hybrid_search(
        query=query,
        top_k=5,
        weights={"vector": 0.7, "keyword": 0.2, "graph": 0.1}
    )
    
    print(f"\n✅ Found {len(results_custom)} results")
    
    for i, result in enumerate(results_custom, 1):
        print_result(result, i)
    
    # Test 5: With Filters
    print("\n" + "=" * 80)
    print("Test 5: Hybrid Search with Filters")
    print("=" * 80)
    print("Filter: document_type = 'regulation'")
    
    results_filtered = await agent.hybrid_search(
        query=query,
        top_k=5,
        filters={"document_type": "regulation"}
    )
    
    print(f"\n✅ Found {len(results_filtered)} results")
    
    for i, result in enumerate(results_filtered, 1):
        print_result(result, i)
    
    print_separator()
    print("✅ All tests completed!")
    print_separator()


def main():
    """Main function"""
    
    # Default query
    default_query = "Was regelt § 58 LBO BW bezüglich Photovoltaik-Anlagen?"
    
    # Parse command line args
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print("Usage: python scripts/test_uds3_hybrid.py [--query 'Your query']")
            sys.exit(0)
        elif sys.argv[1] == "--query" and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
        else:
            query = " ".join(sys.argv[1:])
    else:
        query = default_query
        print(f"ℹ️  Using default query: {query}")
        print(f"   Custom query: python scripts/test_uds3_hybrid.py --query 'Your query'")
        print()
    
    # Run async test
    asyncio.run(test_hybrid_search(query))


if __name__ == "__main__":
    main()
