#!/usr/bin/env python3
"""
UDS3 Search API - Quick Start Example

Zeigt die verschiedenen Verwendungsmöglichkeiten der UDS3 Search API.

NEW (v1.4.0): Uses strategy.search_api property ⭐
OLD: Manual UDS3SearchAPI() instantiation (deprecated)

Run: python scripts/quickstart_uds3_search_api.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / "uds3"))


async def example_1_basic_vector_search():
    """Beispiel 1: Einfache Vector Search (NEW API ⭐)"""
    print("\n" + "=" * 80)
    print("BEISPIEL 1: Vector Search (Semantische Ähnlichkeit)")
    print("=" * 80)

    from sentence_transformers import SentenceTransformer
    from uds3 import get_optimized_unified_strategy

    # Initialize (Search API via property) ✅
    strategy = get_optimized_unified_strategy()
    search_api = strategy.search_api  # NEW: Property access ⭐

    # Generate embedding
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query = "Photovoltaik Anforderungen"
    embedding = model.encode(query).tolist()

    # Vector Search
    results = await search_api.vector_search(embedding, top_k=5)

    print(f"\n📊 Query: '{query}'")
    print(f"✅ Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.3f}")
        print(f"   ID: {result.document_id}")
        print(f"   Content: {result.content[:100]}...")


async def example_2_graph_search():
    """Beispiel 2: Graph Search mit Neo4j (NEW API ⭐)"""
    print("\n" + "=" * 80)
    print("BEISPIEL 2: Graph Search (Beziehungen)")
    print("=" * 80)

    from uds3 import get_optimized_unified_strategy

    # Initialize (Search API via property) ✅
    strategy = get_optimized_unified_strategy()
    search_api = strategy.search_api  # NEW: Property access ⭐

    # Graph Search
    query = "Photovoltaik"
    results = await search_api.graph_search(query, top_k=5)

    print(f"\n📊 Query: '{query}'")
    print(f"✅ Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.3f}")
        print(f"   Name: {result.metadata.get('name', 'N/A')}")
        print(f"   Type: {result.metadata.get('document_type', 'N/A')}")
        print(f"   Related Docs: {len(result.related_docs)}")


async def example_3_hybrid_search():
    """Beispiel 3: Hybrid Search (Vector + Graph) (NEW API ⭐)"""
    print("\n" + "=" * 80)
    print("BEISPIEL 3: Hybrid Search (Best of Both Worlds)")
    print("=" * 80)

    from uds3 import get_optimized_unified_strategy
    from uds3.search import SearchQuery

    # Initialize (Search API via property) ✅
    strategy = get_optimized_unified_strategy()
    search_api = strategy.search_api  # NEW: Property access ⭐

    # Hybrid Search
    query = SearchQuery(
        query_text="Was regelt § 58 LBO BW?", top_k=5, search_types=["vector", "graph"], weights={"vector": 0.5, "graph": 0.5}
    )

    results = await search_api.hybrid_search(query)

    print(f"\n📊 Query: '{query.query_text}'")
    print(f"📊 Weights: {query.weights}")
    print(f"✅ Found {len(results)} hybrid results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.3f}")
        print(f"   Source: {result.source}")
        print(f"   ID: {result.document_id}")
        print(f"   Content: {result.content[:100]}...")


async def example_4_veritas_agent():
    """Beispiel 4: VERITAS Agent (High-Level API) (NEW API ⭐)"""
    print("\n" + "=" * 80)
    print("BEISPIEL 4: VERITAS Agent (Empfohlen für VERITAS)")
    print("=" * 80)

    from uds3 import get_optimized_unified_strategy

    from backend.agents.veritas_uds3_hybrid_agent import UDS3HybridSearchAgent

    # Initialize Agent (uses strategy.search_api internally) ✅
    strategy = get_optimized_unified_strategy()
    agent = UDS3HybridSearchAgent(strategy)

    # Hybrid Search
    results = await agent.hybrid_search(query="Photovoltaik Pflicht", top_k=5, weights={"vector": 0.5, "graph": 0.5})

    print(f"\n📊 Query: 'Photovoltaik Pflicht'")
    print(f"✅ Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Final Score: {result.final_score:.3f}")
        print(f"   Source Scores: {result.scores}")
        print(f"   ID: {result.document_id}")
        print(f"   Content: {result.content[:100]}...")


async def example_5_custom_weights():
    """Beispiel 5: Custom Weights für Domain-Specific Search"""
    print("\n" + "=" * 80)
    print("BEISPIEL 5: Custom Weights (Domain-Specific)")
    print("=" * 80)

    from uds3.uds3_core import get_optimized_unified_strategy

    from backend.agents.veritas_uds3_hybrid_agent import UDS3HybridSearchAgent

    # Initialize Agent
    strategy = get_optimized_unified_strategy()
    agent = UDS3HybridSearchAgent(strategy)

    # Baurecht: Graph wichtiger (Gesetzesbeziehungen)
    print("\n📊 Use Case: Baurecht (Graph-fokussiert)")
    baurecht_results = await agent.hybrid_search(query="Abstandsflächen", top_k=3, weights={"graph": 0.8, "vector": 0.2})
    print(f"✅ Found {len(baurecht_results)} results (Graph=80%, Vector=20%)")
    for i, result in enumerate(baurecht_results, 1):
        print(f"   {i}. Score: {result.final_score:.3f}, Scores: {result.scores}")

    # Umweltrecht: Vector wichtiger (viele Synonyme)
    print("\n📊 Use Case: Umweltrecht (Vector-fokussiert)")
    umwelt_results = await agent.hybrid_search(query="Luftqualität", top_k=3, weights={"vector": 0.7, "graph": 0.3})
    print(f"✅ Found {len(umwelt_results)} results (Vector=70%, Graph=30%)")
    for i, result in enumerate(umwelt_results, 1):
        print(f"   {i}. Score: {result.final_score:.3f}, Scores: {result.scores}")


async def example_6_graph_only_production():
    """Beispiel 6: Graph-Only Search (Production-Ready)"""
    print("\n" + "=" * 80)
    print("BEISPIEL 6: Graph-Only (Production Recommendation)")
    print("=" * 80)
    print("\nℹ️ ChromaDB hat aktuell ein Remote API Issue (Fallback-Docs)")
    print("ℹ️ Für Production wird Neo4j-Only empfohlen (1930 Dokumente)")

    from uds3.uds3_core import get_optimized_unified_strategy

    from backend.agents.veritas_uds3_hybrid_agent import UDS3HybridSearchAgent

    # Initialize Agent
    strategy = get_optimized_unified_strategy()
    agent = UDS3HybridSearchAgent(strategy)

    # Graph-Only Search
    results = await agent.hybrid_search(
        query="Energiegesetz", top_k=5, search_types=["graph"], weights={"graph": 1.0}  # Skip ChromaDB
    )

    print(f"\n📊 Query: 'Energiegesetz'")
    print(f"✅ Found {len(results)} graph-only results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.final_score:.3f}")
        print(f"   Name: {result.metadata.get('name', 'N/A')}")
        print(f"   Type: {result.metadata.get('document_type', 'N/A')}")


async def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("UDS3 SEARCH API - QUICK START EXAMPLES")
    print("=" * 80)

    # Uncomment the examples you want to run:

    # await example_1_basic_vector_search()
    # await example_2_graph_search()
    # await example_3_hybrid_search()
    await example_4_veritas_agent()  # Recommended for VERITAS
    # await example_5_custom_weights()
    await example_6_graph_only_production()  # Production recommendation

    print("\n" + "=" * 80)
    print("✅ QUICK START COMPLETE!")
    print("=" * 80)
    print("\nℹ️ Next Steps:")
    print("   1. Uncomment other examples to explore more features")
    print("   2. Read docs/UDS3_SEARCH_API_PRODUCTION_GUIDE.md for details")
    print("   3. Integrate into VERITAS application (backend.py)")
    print("\n🚀 Ready for Production: Use Graph-Only Search (Neo4j)")
    print("⏭️ Future: ChromaDB fix for full Hybrid Search\n")


if __name__ == "__main__":
    asyncio.run(main())
