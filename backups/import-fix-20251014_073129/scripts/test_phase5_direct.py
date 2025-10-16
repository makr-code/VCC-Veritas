#!/usr/bin/env python3
"""
Direct test of Phase 5 Hybrid Search (ohne Backend)
"""

import sys
import os
import asyncio

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

async def main():
    print("=" * 80)
    print("PHASE 5 HYBRID SEARCH - DIRECT TEST")
    print("=" * 80)
    
    # Import Phase 5 Integration
    from backend.api.veritas_phase5_integration import (
        initialize_phase5_hybrid_search,
        get_hybrid_retriever,
        DEMO_CORPUS
    )
    
    # Initialize
    print("\nInitializing Phase 5 Hybrid Search...")
    success = await initialize_phase5_hybrid_search(demo_corpus=DEMO_CORPUS)
    
    if not success:
        print("\nERROR: Phase 5 initialization failed!")
        return
    
    print("\n" + "=" * 80)
    print("TESTING HYBRID SEARCH")
    print("=" * 80)
    
    # Get retriever
    hybrid_retriever = get_hybrid_retriever()
    
    # Test queries
    test_queries = [
        "BGB Taschengeldparagraph Minderjährige",
        "Verwaltungsakt Definition VwVfG",
        "nachhaltig bauen Umwelt"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] Query: '{query}'")
        print("-" * 60)
        
        import time
        start = time.time()
        
        results = await hybrid_retriever.retrieve(query, top_k=3)
        
        elapsed = (time.time() - start) * 1000
        
        print(f"Results: {len(results)} in {elapsed:.0f}ms")
        
        for j, result in enumerate(results, 1):
            print(f"\n  {j}. doc_id: {result.doc_id}")
            print(f"     score: {result.score:.4f}")
            print(f"     content: {result.content[:100]}...")
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
