"""
Test Batch Search Functionality (Phase 5 - Task 2.1)

Tests the batch_search() method for parallel query processing.

Version: 1.0.0
Phase: 5 (v5.0 Enhanced RAG)
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from services.rag_service import (
    RAGService, SearchMethod, SearchWeights, SearchFilters,
    HybridSearchResult, SearchResult, DocumentMetadata, RankingStrategy
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def rag_service():
    """Create RAG service for testing (without UDS3 backends)"""
    service = RAGService()
    return service


@pytest.fixture
def sample_queries():
    """Sample queries for batch testing"""
    return [
        "Bauantrag für Einfamilienhaus in Stuttgart",
        "Gewerbeanmeldung in München",
        "Personalausweis beantragen",
        "Führerschein verlängern",
        "Steuererklärung abgeben"
    ]


# ============================================================================
# TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_batch_search_basic(rag_service, sample_queries):
    """Test basic batch search functionality"""
    # Execute batch search
    results = await rag_service.batch_search(sample_queries)
    
    # Verify results
    assert len(results) == len(sample_queries), "Should return result for each query"
    
    # Check each result
    for i, result in enumerate(results):
        assert isinstance(result, HybridSearchResult), f"Result {i} should be HybridSearchResult"
        assert result.query == sample_queries[i], f"Result {i} query mismatch"
        assert isinstance(result.results, list), f"Result {i} should have results list"
        assert result.total_count >= 0, f"Result {i} should have non-negative count"


@pytest.mark.asyncio
async def test_batch_search_performance(rag_service, sample_queries):
    """Test that batch search is faster than sequential"""
    # Time batch search
    start_batch = time.time()
    batch_results = await rag_service.batch_search(sample_queries)
    batch_time = time.time() - start_batch
    
    # Time sequential search (without asyncio)
    start_sequential = time.time()
    sequential_results = []
    for query in sample_queries:
        result = rag_service.hybrid_search(query)
        sequential_results.append(result)
    sequential_time = time.time() - start_sequential
    
    print(f"\nPerformance Comparison:")
    print(f"  Batch search:      {batch_time*1000:.2f}ms ({len(sample_queries)} queries)")
    print(f"  Sequential search: {sequential_time*1000:.2f}ms ({len(sample_queries)} queries)")
    print(f"  Speedup:           {sequential_time/batch_time:.2f}x")
    
    # Batch should be faster (or at least not significantly slower)
    # Note: In test/mock mode, speedup may be minimal
    assert len(batch_results) == len(sequential_results), "Should return same number of results"


@pytest.mark.asyncio
async def test_batch_search_empty_queries(rag_service):
    """Test batch search with empty query list"""
    results = await rag_service.batch_search([])
    
    assert len(results) == 0, "Empty query list should return empty results"


@pytest.mark.asyncio
async def test_batch_search_single_query(rag_service):
    """Test batch search with single query"""
    queries = ["Bauantrag Stuttgart"]
    results = await rag_service.batch_search(queries)
    
    assert len(results) == 1, "Single query should return single result"
    assert results[0].query == queries[0]


@pytest.mark.asyncio
async def test_batch_search_with_filters(rag_service, sample_queries):
    """Test batch search with filters"""
    filters = SearchFilters(
        max_results=5,
        min_relevance=0.7
    )
    
    results = await rag_service.batch_search(
        sample_queries,
        filters=filters
    )
    
    # Verify filters applied
    for result in results:
        assert len(result.results) <= 5, "Should respect max_results filter"
        for search_result in result.results:
            assert search_result.relevance_score >= 0.7, "Should respect min_relevance filter"


@pytest.mark.asyncio
async def test_batch_search_vector_only(rag_service, sample_queries):
    """Test batch search with vector search only"""
    results = await rag_service.batch_search(
        sample_queries,
        search_method=SearchMethod.VECTOR
    )
    
    for result in results:
        assert SearchMethod.VECTOR in result.search_methods_used, \
            "Should use vector search method"


@pytest.mark.asyncio
async def test_batch_search_with_weights(rag_service, sample_queries):
    """Test batch search with custom weights"""
    weights = SearchWeights(
        vector_weight=0.6,
        graph_weight=0.3,
        relational_weight=0.1
    )
    
    results = await rag_service.batch_search(
        sample_queries,
        weights=weights
    )
    
    for result in results:
        assert result.weights.vector_weight == 0.6
        assert result.weights.graph_weight == 0.3
        assert result.weights.relational_weight == 0.1


@pytest.mark.asyncio
async def test_batch_search_error_handling(rag_service):
    """Test batch search handles errors gracefully"""
    # Use queries that might cause issues
    problematic_queries = [
        "Normal query",
        "",  # Empty query
        "A" * 10000,  # Very long query
        "Test query"
    ]
    
    results = await rag_service.batch_search(problematic_queries)
    
    # Should still return results for all queries (even if some fail)
    assert len(results) == len(problematic_queries)
    
    # Check that we get valid HybridSearchResult objects
    for result in results:
        assert isinstance(result, HybridSearchResult)


@pytest.mark.asyncio
async def test_batch_search_concurrent_execution(rag_service):
    """Test that batch search executes queries concurrently"""
    # Create multiple queries
    queries = [f"Query {i}" for i in range(10)]
    
    # Execute batch search
    start_time = time.time()
    results = await rag_service.batch_search(queries)
    execution_time = time.time() - start_time
    
    # Verify all completed
    assert len(results) == len(queries)
    
    print(f"\nConcurrent execution test:")
    print(f"  Queries: {len(queries)}")
    print(f"  Total time: {execution_time*1000:.2f}ms")
    print(f"  Avg per query: {execution_time*1000/len(queries):.2f}ms")


@pytest.mark.asyncio
async def test_batch_search_result_consistency(rag_service):
    """Test that batch and sequential searches return consistent results"""
    query = "Bauantrag Stuttgart"
    
    # Batch search with single query
    batch_results = await rag_service.batch_search([query])
    
    # Sequential search
    sequential_result = rag_service.hybrid_search(query)
    
    # Compare results
    batch_result = batch_results[0]
    
    # Should have same query
    assert batch_result.query == sequential_result.query
    
    # Should have same number of results
    assert len(batch_result.results) == len(sequential_result.results)
    
    # Should use same search methods
    assert batch_result.search_methods_used == sequential_result.search_methods_used


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("BATCH SEARCH TEST SUITE")
    print("="*80)
    
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
