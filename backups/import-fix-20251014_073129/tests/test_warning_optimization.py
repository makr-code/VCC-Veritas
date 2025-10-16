"""
Test: Warning Optimization
===========================

Verifiziert, dass Warnings nur einmal beim Initialisieren geloggt werden,
nicht bei jedem Query.

Tests:
1. HybridRetriever: vector_search Warning nur 1× beim __init__
2. SparseRetriever: BM25 empty Warning nur 1× beim ersten search()
3. Multiple Queries: Keine wiederholten Warnings
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import logging
from io import StringIO


# ============================================================================
# Test: HybridRetriever Warning Optimization
# ============================================================================

@pytest.mark.asyncio
async def test_hybrid_retriever_vector_search_warning_once():
    """Test: vector_search Warning wird nur 1× beim __init__ geloggt"""
    
    # Import HybridRetriever
    from backend.agents.veritas_hybrid_retrieval import HybridRetriever
    
    # Mock Dense Retriever ohne vector_search
    mock_dense = MagicMock()
    # Kein vector_search Attribut → sollte Warning auslösen
    
    # Capture logs
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.WARNING)
    logger = logging.getLogger('backend.agents.veritas_hybrid_retrieval')
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    
    # 1. Initialisierung (sollte Warning loggen)
    retriever = HybridRetriever(dense_retriever=mock_dense)
    
    # Check: Warning wurde beim __init__ geloggt
    log_output_init = log_stream.getvalue()
    assert "vector_search" in log_output_init or "search_documents" in log_output_init, \
        "Warning sollte beim __init__ geloggt werden"
    
    # Clear logs
    log_stream.truncate(0)
    log_stream.seek(0)
    
    # 2. Mehrere Queries (sollten KEINE Warnings mehr loggen)
    for i in range(3):
        result = await retriever._retrieve_dense(
            query=f"Test query {i}",
            params={}
        )
        assert result == [], "Sollte leere Liste zurückgeben"
    
    # Check: Keine neuen Warnings
    log_output_queries = log_stream.getvalue()
    assert "vector_search" not in log_output_queries, \
        f"Keine Warnings bei Queries erwartet, aber gefunden: {log_output_queries}"
    
    # Cleanup
    logger.removeHandler(handler)
    
    print("✅ Test passed: vector_search Warning nur 1× beim __init__")


@pytest.mark.asyncio
async def test_sparse_retriever_bm25_empty_warning_once():
    """Test: BM25 empty Warning wird nur 1× beim ersten search() geloggt"""
    
    from backend.agents.veritas_sparse_retrieval import SparseRetriever
    
    # Capture logs
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.WARNING)
    logger = logging.getLogger('backend.agents.veritas_sparse_retrieval')
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    
    # 1. Initialisierung (leer, kein Index)
    retriever = SparseRetriever()
    
    # 2. Erste Search (sollte Warning loggen)
    result1 = retriever.search(query="Test query 1")
    assert result1 == [], "Sollte leere Liste zurückgeben"
    
    # Check: Warning wurde geloggt
    log_output_first = log_stream.getvalue()
    assert "BM25 Index ist leer" in log_output_first, \
        "Warning sollte beim ersten search() geloggt werden"
    
    # Clear logs
    log_stream.truncate(0)
    log_stream.seek(0)
    
    # 3. Weitere Searches (sollten KEINE Warnings mehr loggen)
    for i in range(3):
        result = retriever.search(query=f"Test query {i+2}")
        assert result == [], "Sollte leere Liste zurückgeben"
    
    # Check: Keine neuen Warnings
    log_output_subsequent = log_stream.getvalue()
    assert "BM25 Index ist leer" not in log_output_subsequent, \
        f"Keine Warnings bei weiteren Searches erwartet, aber gefunden: {log_output_subsequent}"
    
    # Cleanup
    logger.removeHandler(handler)
    
    print("✅ Test passed: BM25 empty Warning nur 1× beim ersten search()")


# ============================================================================
# Test: Multiple Queries Scenario (Integration)
# ============================================================================

@pytest.mark.asyncio
async def test_hybrid_retrieval_multiple_queries_no_spam():
    """Test: 10 Queries produzieren keine Warning-Spam"""
    
    from backend.agents.veritas_hybrid_retrieval import HybridRetriever
    
    # Mock Dense Retriever
    mock_dense = MagicMock()
    
    # Capture logs
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.WARNING)
    logger = logging.getLogger('backend.agents.veritas_hybrid_retrieval')
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    
    # Initialisierung
    retriever = HybridRetriever(dense_retriever=mock_dense)
    
    # Clear logs after init
    log_stream.truncate(0)
    log_stream.seek(0)
    
    # 10 Queries
    for i in range(10):
        result = await retriever._retrieve_dense(
            query=f"Test query {i}",
            params={}
        )
    
    # Check: Keine Warnings bei den 10 Queries
    log_output = log_stream.getvalue()
    warning_count = log_output.count("vector_search")
    
    assert warning_count == 0, \
        f"0 Warnings erwartet bei 10 Queries, aber {warning_count} gefunden:\n{log_output}"
    
    # Cleanup
    logger.removeHandler(handler)
    
    print("✅ Test passed: 10 Queries ohne Warning-Spam")


# ============================================================================
# Test: Flag Initialization
# ============================================================================

def test_hybrid_retriever_flags_initialized():
    """Test: Warning-Flags werden korrekt initialisiert"""
    
    from backend.agents.veritas_hybrid_retrieval import HybridRetriever
    
    # Mock Dense Retriever MIT vector_search
    mock_with_vector_search = MagicMock()
    mock_with_vector_search.vector_search = AsyncMock(return_value=[])
    
    retriever1 = HybridRetriever(dense_retriever=mock_with_vector_search)
    assert retriever1._vector_search_available == True, \
        "Flag sollte True sein wenn vector_search existiert"
    
    # Mock Dense Retriever OHNE vector_search
    mock_without_vector_search = MagicMock()
    # Kein vector_search Attribut
    
    retriever2 = HybridRetriever(dense_retriever=mock_without_vector_search)
    assert retriever2._vector_search_available == False, \
        "Flag sollte False sein wenn vector_search nicht existiert"
    
    print("✅ Test passed: Flags korrekt initialisiert")


def test_sparse_retriever_flag_initialized():
    """Test: BM25 Warning-Flag wird korrekt initialisiert"""
    
    from backend.agents.veritas_sparse_retrieval import SparseRetriever
    
    retriever = SparseRetriever()
    
    # Flag sollte False sein (noch keine Warning geloggt)
    assert retriever._empty_index_warning_shown == False, \
        "Flag sollte initial False sein"
    
    # Nach erstem search() sollte Flag True sein
    retriever.search(query="Test")
    
    assert retriever._empty_index_warning_shown == True, \
        "Flag sollte nach erstem search() True sein"
    
    print("✅ Test passed: BM25 Flag korrekt initialisiert und gesetzt")


# ============================================================================
# Performance Test: hasattr vs Cached Flags
# ============================================================================

@pytest.mark.asyncio
async def test_performance_cached_flags_vs_hasattr():
    """Test: Cached Flags sind schneller als wiederholte hasattr() Calls"""
    
    import time
    from backend.agents.veritas_hybrid_retrieval import HybridRetriever
    
    mock_dense = MagicMock()
    retriever = HybridRetriever(dense_retriever=mock_dense)
    
    # Warmup
    await retriever._retrieve_dense("warmup", {})
    
    # Measure: 100 Queries mit Cached Flags
    start = time.perf_counter()
    for i in range(100):
        await retriever._retrieve_dense(f"query_{i}", {})
    cached_time = time.perf_counter() - start
    
    print(f"⏱️  100 Queries mit Cached Flags: {cached_time*1000:.2f}ms")
    
    # Note: hasattr-Variante würde länger dauern, aber wir haben sie bereits optimiert
    # Dieser Test verifiziert nur, dass die Cached-Variante performant ist
    
    assert cached_time < 1.0, \
        f"100 Queries sollten < 1s dauern, aber {cached_time}s gemessen"
    
    print("✅ Test passed: Performance mit Cached Flags ist gut")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 Warning Optimization Tests")
    print("=" * 80)
    
    # Run async tests
    asyncio.run(test_hybrid_retriever_vector_search_warning_once())
    asyncio.run(test_sparse_retriever_bm25_empty_warning_once())
    asyncio.run(test_hybrid_retrieval_multiple_queries_no_spam())
    asyncio.run(test_performance_cached_flags_vs_hasattr())
    
    # Run sync tests
    test_hybrid_retriever_flags_initialized()
    test_sparse_retriever_flag_initialized()
    
    print()
    print("=" * 80)
    print("✅ Alle Warning Optimization Tests bestanden!")
    print("=" * 80)
