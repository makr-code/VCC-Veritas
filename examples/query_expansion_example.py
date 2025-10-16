"""
Query Expansion Example - Demonstrating Synonym Generation

This example shows how to use the expand_query() method to generate
query variations for improved search recall.

Phase 5 - Task 2.2: Query Expansion
"""

import sys
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from backend.services.rag_service import RAGService


def main():
    """Demonstrate query expansion functionality"""
    
    print("="*80)
    print("QUERY EXPANSION DEMONSTRATION")
    print("="*80)
    
    # Initialize RAG service
    print("\n1. Initializing RAG Service...")
    rag = RAGService()
    print("   ✅ RAG Service initialized")
    
    # Test queries
    test_queries = [
        "Bauantrag für Einfamilienhaus in Stuttgart",
        "Gewerbeanmeldung München",
        "Personalausweis beantragen",
        "Kosten für Bauantrag",
        "Kontakt Bauamt Stuttgart",
        "Ummeldung nach Umzug",
        "Führerschein verlängern"
    ]
    
    print("\n2. Query Expansion Examples:")
    print("   " + "-"*76)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: \"{query}\"")
        
        # Generate expansions
        expansions = rag.expand_query(query, max_expansions=3, include_original=True)
        
        print(f"   Expansions ({len(expansions)} total):")
        for j, expansion in enumerate(expansions, 1):
            marker = "📌" if expansion == query else "  "
            print(f"      {marker} {j}. {expansion}")
    
    print("\n   " + "-"*76)
    
    # Demonstrate use case: improved search recall
    print("\n3. Use Case: Improved Search Recall")
    print("   " + "-"*76)
    
    query = "Bauantrag Stuttgart"
    print(f"\n   Original query: \"{query}\"")
    
    # Standard search
    print("\n   A) Standard Search (1 query):")
    standard_result = rag.hybrid_search(query)
    print(f"      - Results: {len(standard_result.results)} documents")
    
    # Expanded search
    print("\n   B) Expanded Search (multiple query variations):")
    expansions = rag.expand_query(query, max_expansions=3, include_original=True)
    print(f"      - Query variations: {len(expansions)}")
    
    # Simulate searching with all expansions
    all_results = []
    for exp_query in expansions:
        result = rag.hybrid_search(exp_query)
        all_results.extend(result.results)
        print(f"      - '{exp_query}': {len(result.results)} results")
    
    # Deduplicate results
    unique_results = {}
    for result in all_results:
        result_hash = result.get_hash()
        if result_hash not in unique_results:
            unique_results[result_hash] = result
    
    print(f"\n      - Total unique results: {len(unique_results)} documents")
    print(f"      - Improvement: {len(unique_results) - len(standard_result.results)} additional documents")
    
    print("\n   " + "-"*76)
    
    # Advanced usage
    print("\n4. Advanced Usage:")
    print("   " + "-"*76)
    
    # A) Exclude original query
    print("\n   A) Generate variations only (exclude original):")
    query = "Personalausweis beantragen"
    expansions = rag.expand_query(query, max_expansions=3, include_original=False)
    print(f"      Original: \"{query}\"")
    print(f"      Variations only: {expansions}")
    
    # B) Control expansion count
    print("\n   B) Control expansion count:")
    query = "Bauantrag kosten"
    for max_exp in [1, 2, 3]:
        expansions = rag.expand_query(query, max_expansions=max_exp)
        print(f"      max_expansions={max_exp}: {len(expansions)} total queries")
    
    # C) Synonym coverage
    print("\n   C) Synonym categories covered:")
    categories = {
        "Building/Construction": "Bauantrag München",
        "Business": "Gewerbeanmeldung Stuttgart",
        "Documents": "Personalausweis verloren",
        "Procedures": "Anmeldung beim Rathaus",
        "Authorities": "Kontakt Bauamt"
    }
    
    for category, query in categories.items():
        expansions = rag.expand_query(query, max_expansions=2)
        print(f"      {category}: {len(expansions)-1} synonyms generated")
    
    print("\n   " + "-"*76)
    
    # Benefits summary
    print("\n5. Benefits of Query Expansion:")
    print("   ✅ Improved recall (find more relevant documents)")
    print("   ✅ Synonym handling (administrative terminology)")
    print("   ✅ Case-insensitive matching")
    print("   ✅ Duplicate prevention")
    print("   ✅ Configurable expansion limits")
    print("   ✅ German administrative domain coverage")
    
    print("\n" + "="*80)
    print("✅ Query expansion demonstration complete!")
    print("="*80)


if __name__ == "__main__":
    main()
