"""
Test ChromaDB search_similar output format
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from uds3.uds3_core import get_optimized_unified_strategy
from sentence_transformers import SentenceTransformer

def main():
    print("=" * 80)
    print("Test ChromaDB search_similar")
    print("=" * 80)
    
    # Initialize
    strategy = get_optimized_unified_strategy()
    chroma = strategy.vector_backend
    
    # Generate embedding
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query = "Photovoltaik"
    embedding = model.encode(query).tolist()
    
    print(f"\nQuery: {query}")
    print(f"Embedding dimension: {len(embedding)}")
    
    # Test search_similar
    print("\n1️⃣ Testing search_similar()...")
    results = chroma.search_similar(embedding, n_results=3)
    
    print(f"\nResult type: {type(results)}")
    print(f"Result keys: {results.keys() if isinstance(results, dict) else 'N/A'}")
    print(f"Result length: {len(results)}")
    
    if isinstance(results, dict):
        for key in results:
            print(f"  - {key}: {type(results[key])}, length={len(results[key]) if hasattr(results[key], '__len__') else 'N/A'}")
            if key == 'metadatas' and results[key]:
                print(f"    Sample metadata: {results[key][0] if results[key] else 'EMPTY'}")
    
    elif isinstance(results, list):
        print(f"\nList with {len(results)} items")
        if results:
            print(f"First item type: {type(results[0])}")
            print(f"First item: {results[0]}")
    
    # Test query_vectors
    print("\n\n2️⃣ Testing query_vectors()...")
    results2 = chroma.query_vectors(embedding, limit=3)
    
    print(f"\nResult type: {type(results2)}")
    print(f"Result keys: {results2.keys() if isinstance(results2, dict) else 'N/A'}")
    print(f"Result length: {len(results2)}")
    
    if isinstance(results2, dict):
        for key in results2:
            print(f"  - {key}: {type(results2[key])}, length={len(results2[key]) if hasattr(results2[key], '__len__') else 'N/A'}")
            if key == 'metadatas' and results2[key]:
                print(f"    Sample metadata: {results2[key][0] if results2[key] else 'EMPTY'}")
    
    elif isinstance(results2, list):
        print(f"\nList with {len(results2)} items")
        if results2:
            print(f"First item type: {type(results2[0])}")
            print(f"First item: {results2[0]}")

if __name__ == "__main__":
    main()
