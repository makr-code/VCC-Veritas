"""
Batch Search Example - Demonstrating Parallel Query Processing

This example shows how to use the batch_search() method to process
multiple queries in parallel for improved throughput.

Phase 5 - Task 2.1: Batch RAG Search
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from backend.services.rag_service import (
    RAGService, SearchMethod, SearchWeights, SearchFilters
)


async def main():
    """Demonstrate batch search functionality"""
    
    print("="*80)
    print("BATCH SEARCH DEMONSTRATION")
    print("="*80)
    
    # Initialize RAG service
    print("\n1. Initializing RAG Service...")
    rag = RAGService()
    print("   ✅ RAG Service initialized")
    
    # Define multiple queries
    queries = [
        "Bauantrag für Einfamilienhaus in Stuttgart",
        "Gewerbeanmeldung in München",
        "Personalausweis beantragen",
        "Führerschein verlängern",
        "Steuererklärung abgeben",
        "Hund anmelden",
        "Ummeldung nach Umzug",
        "Elterngeld beantragen"
    ]
    
    print(f"\n2. Processing {len(queries)} queries...")
    print("   Queries:")
    for i, q in enumerate(queries, 1):
        print(f"      {i}. {q}")
    
    # Perform batch search
    print("\n3. Executing batch search...")
    results = await rag.batch_search(
        queries=queries,
        search_method=SearchMethod.HYBRID,
        filters=SearchFilters(max_results=5)
    )
    
    # Display results
    print("\n4. Results:")
    print("   " + "-"*76)
    
    total_docs = 0
    for i, (query, result) in enumerate(zip(queries, results), 1):
        print(f"\n   Query {i}: {query}")
        print(f"   Results: {len(result.results)} documents")
        print(f"   Methods: {', '.join([m.value for m in result.search_methods_used])}")
        print(f"   Time: {result.execution_time_ms:.2f}ms")
        
        # Show top result
        if result.results:
            top_result = result.results[0]
            print(f"   Top: {top_result.metadata.title} (score: {top_result.relevance_score:.3f})")
        
        total_docs += len(result.results)
    
    print("\n" + "   " + "-"*76)
    print(f"\n5. Summary:")
    print(f"   Total queries: {len(queries)}")
    print(f"   Total documents: {total_docs}")
    print(f"   Avg documents per query: {total_docs/len(queries):.1f}")
    
    # Performance comparison
    print("\n6. Performance Comparison:")
    print("   Running sequential search for comparison...")
    
    import time
    
    # Sequential execution
    start_seq = time.time()
    seq_results = []
    for query in queries:
        result = rag.hybrid_search(query, filters=SearchFilters(max_results=5))
        seq_results.append(result)
    seq_time = time.time() - start_seq
    
    # Calculate batch time from results
    batch_time = sum(r.execution_time_ms for r in results) / 1000
    
    print(f"\n   Sequential: {seq_time*1000:.2f}ms")
    print(f"   Batch:      {batch_time*1000:.2f}ms (estimated)")
    
    if seq_time > batch_time:
        speedup = seq_time / batch_time
        print(f"   Speedup:    {speedup:.2f}x faster with batch processing! 🚀")
    else:
        print(f"   Note: Speedup may vary with real backends and network latency")
    
    print("\n" + "="*80)
    print("✅ Batch search demonstration complete!")
    print("="*80)


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
