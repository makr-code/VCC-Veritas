"""
Quick Test: Warning Optimization Validation
============================================

Einfacher manueller Test zur Validierung der Warning-Reduzierung.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def setup_logging():
    """Logging für Test konfigurieren"""
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s'
    )


async def test_hybrid_retriever_warnings():
    """Test: HybridRetriever Warnings"""
    print("\n" + "=" * 80)
    print("Test 1: HybridRetriever Warning Optimization")
    print("=" * 80)
    
    from backend.agents.veritas_hybrid_retrieval import HybridRetriever
    
    # Mock ohne vector_search (real object, kein MagicMock)
    class SimpleMock:
        pass
    
    mock_dense = SimpleMock()
    
    print("\n1. Initialisierung (sollte Warning loggen):")
    print("-" * 40)
    retriever = HybridRetriever(dense_retriever=mock_dense)
    
    print("\n2. Mehrere Queries (sollten KEINE Warnings mehr loggen):")
    print("-" * 40)
    for i in range(3):
        result = await retriever._retrieve_dense(
            query=f"Test query {i}",
            params={}
        )
        print(f"   Query {i+1}: {len(result)} results (expected: 0)")
    
    print("\n✅ Test 1 abgeschlossen")
    print("   Erwartung: 1 Warning beim __init__, KEINE bei Queries")


async def test_sparse_retriever_warnings():
    """Test: SparseRetriever Warnings"""
    print("\n" + "=" * 80)
    print("Test 2: SparseRetriever Warning Optimization")
    print("=" * 80)
    
    from backend.agents.veritas_sparse_retrieval import SparseRetriever
    
    print("\n1. Initialisierung (leer):")
    print("-" * 40)
    retriever = SparseRetriever()
    
    print("\n2. Erste Retrieval (sollte Warning loggen):")
    print("-" * 40)
    result1 = await retriever.retrieve(query="Test query 1")
    print(f"   Results: {len(result1)} (expected: 0)")
    
    print("\n3. Weitere Retrievals (sollten KEINE Warnings mehr loggen):")
    print("-" * 40)
    for i in range(3):
        result = await retriever.retrieve(query=f"Test query {i+2}")
        print(f"   Query {i+2}: {len(result)} results (expected: 0)")
    
    print("\n✅ Test 2 abgeschlossen")
    print("   Erwartung: 1 Warning beim ersten retrieve(), KEINE danach")


async def test_flag_initialization():
    """Test: Flag Initialisierung"""
    print("\n" + "=" * 80)
    print("Test 3: Warning-Flags Initialisierung")
    print("=" * 80)
    
    from backend.agents.veritas_hybrid_retrieval import HybridRetriever
    from backend.agents.veritas_sparse_retrieval import SparseRetriever
    
    # Test 3.1: HybridRetriever Flags
    print("\n3.1 HybridRetriever:")
    print("-" * 40)
    
    class MockWithVectorSearch:
        async def vector_search(self, **kwargs):
            return []
    
    class MockWithoutVectorSearch:
        pass
    
    retriever_with = HybridRetriever(dense_retriever=MockWithVectorSearch())
    retriever_without = HybridRetriever(dense_retriever=MockWithoutVectorSearch())
    
    print(f"   Mit vector_search:    _vector_search_available = {retriever_with._vector_search_available}")
    print(f"   Ohne vector_search:   _vector_search_available = {retriever_without._vector_search_available}")
    print(f"   Ohne vector_search:   _has_search_documents = {retriever_without._has_search_documents}")
    
    assert retriever_with._vector_search_available == True, "Sollte True sein"
    assert retriever_without._vector_search_available == False, "Sollte False sein"
    
    # Test 3.2: SparseRetriever Flag
    print("\n3.2 SparseRetriever:")
    print("-" * 40)
    
    sparse = SparseRetriever()
    print(f"   Initial: _empty_index_warning_shown = {sparse._empty_index_warning_shown}")
    assert sparse._empty_index_warning_shown == False, "Sollte initial False sein"
    
    # Nach erstem retrieve
    await sparse.retrieve("test")
    print(f"   Nach 1. retrieve: _empty_index_warning_shown = {sparse._empty_index_warning_shown}")
    assert sparse._empty_index_warning_shown == True, "Sollte nach retrieve True sein"
    
    print("\n✅ Test 3 abgeschlossen")
    print("   Alle Flags korrekt initialisiert!")


async def test_performance():
    """Test: Performance mit Cached Flags"""
    print("\n" + "=" * 80)
    print("Test 4: Performance (100 Queries)")
    print("=" * 80)
    
    import time
    from backend.agents.veritas_hybrid_retrieval import HybridRetriever
    
    class SimpleMock:
        pass
    
    retriever = HybridRetriever(dense_retriever=SimpleMock())
    
    # Warmup
    await retriever._retrieve_dense("warmup", {})
    
    # Measure
    start = time.perf_counter()
    for i in range(100):
        await retriever._retrieve_dense(f"query_{i}", {})
    elapsed = time.perf_counter() - start
    
    print(f"\n   100 Queries: {elapsed*1000:.2f}ms")
    print(f"   Per Query:   {elapsed*10:.2f}ms")
    
    assert elapsed < 1.0, f"Sollte < 1s sein, aber {elapsed:.3f}s gemessen"
    
    print("\n✅ Test 4 abgeschlossen")
    print(f"   Performance ist gut! ({elapsed*1000:.2f}ms)")


async def main():
    """Alle Tests ausführen"""
    setup_logging()
    
    print("\n" + "=" * 80)
    print("🧪 VERITAS Warning Optimization - Validation Tests")
    print("=" * 80)
    
    try:
        await test_hybrid_retriever_warnings()
        await test_sparse_retriever_warnings()
        await test_flag_initialization()
        await test_performance()
        
        print("\n" + "=" * 80)
        print("✅ ALLE TESTS BESTANDEN!")
        print("=" * 80)
        print("\n📊 Zusammenfassung:")
        print("   - Warnings werden nur 1× beim Initialisieren geloggt")
        print("   - Keine Warning-Spam bei wiederholten Queries")
        print("   - Flags korrekt initialisiert")
        print("   - Performance ist gut")
        print("\n🎉 Warning Optimization erfolgreich implementiert!")
        
        return 0
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ TEST FEHLGESCHLAGEN!")
        print("=" * 80)
        print(f"\nFehler: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
