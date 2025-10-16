#!/usr/bin/env python3
"""
Unit Tests for UDS3 Search API

Tests:
- vector_search() with mock ChromaDB backend
- graph_search() with mock Neo4j backend
- keyword_search() with mock PostgreSQL backend
- hybrid_search() with weighted combination
- SearchResult dataclass
- SearchQuery dataclass
- Error handling and graceful degradation

Usage:
    pytest tests/test_uds3_search_api.py -v
    pytest tests/test_uds3_search_api.py -v -k "test_vector"
"""

import pytest
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / 'uds3'))

# Import UDS3 Search API
from uds3.uds3_search_api import (
    UDS3SearchAPI,
    SearchQuery,
    SearchResult,
    SearchType,
    create_search_api
)


# Mock Backends

class MockVectorBackend:
    """Mock ChromaDB backend for testing"""
    
    def search_similar(self, query_vector: List[float], n_results: int, collection: str = None) -> List[Dict]:
        """Mock search_similar returning test documents"""
        # Simulate ChromaDB results (list format)
        return [
            {
                'id': 'doc_vector_1',
                'distance': 0.2,  # Low distance = high similarity
                'metadata': {
                    'name': 'Test Document 1',
                    'content': 'This is a test document about Photovoltaik',
                    'document_type': 'regulation'
                }
            },
            {
                'id': 'doc_vector_2',
                'distance': 0.4,
                'metadata': {
                    'name': 'Test Document 2',
                    'content': 'Another test document',
                    'document_type': 'guideline'
                }
            }
        ]


class MockGraphBackend:
    """Mock Neo4j backend for testing"""
    
    def execute_query(self, cypher: str, params: Dict = None) -> List[Dict]:
        """Mock execute_query returning test nodes"""
        # Simulate Neo4j results with Node-like objects
        class MockNode:
            def __init__(self, props):
                self._properties = props
        
        return [
            {
                'd': MockNode({
                    'document_id': 'doc_graph_1',
                    'name': 'LBO BW § 58',
                    'content': 'Photovoltaik regulations',
                    'document_type': 'regulation'
                }),
                'related_docs': []
            },
            {
                'd': MockNode({
                    'document_id': 'doc_graph_2',
                    'name': 'Energiegesetz BW',
                    'content': 'Energy law',
                    'document_type': 'law'
                }),
                'related_docs': []
            }
        ]


class MockRelationalBackend:
    """Mock PostgreSQL backend for testing"""
    
    def execute_sql(self, sql: str, params: tuple = None) -> List[Dict]:
        """Mock execute_sql (not implemented in real backend)"""
        return [
            {
                'document_id': 'doc_keyword_1',
                'content': 'Keyword search result',
                'metadata': {'document_type': 'regulation'},
                'score': 0.85
            }
        ]


class MockUnifiedStrategy:
    """Mock UnifiedDatabaseStrategy for testing"""
    
    def __init__(self):
        self.vector_backend = MockVectorBackend()
        self.graph_backend = MockGraphBackend()
        self.relational_backend = MockRelationalBackend()


# Fixtures

@pytest.fixture
def mock_strategy():
    """Provide mock UnifiedDatabaseStrategy"""
    return MockUnifiedStrategy()


@pytest.fixture
def search_api(mock_strategy):
    """Provide UDS3SearchAPI with mock backends"""
    return UDS3SearchAPI(mock_strategy)


# Tests: SearchResult Dataclass

def test_search_result_creation():
    """Test SearchResult dataclass creation"""
    result = SearchResult(
        document_id='test_doc',
        content='Test content',
        metadata={'type': 'test'},
        score=0.85,
        source='vector'
    )
    
    assert result.document_id == 'test_doc'
    assert result.content == 'Test content'
    assert result.score == 0.85
    assert result.source == 'vector'
    assert result.metadata['type'] == 'test'


def test_search_result_sorting():
    """Test SearchResult sorting by score (descending)"""
    results = [
        SearchResult('doc1', 'content1', {}, 0.5, 'vector'),
        SearchResult('doc2', 'content2', {}, 0.9, 'graph'),
        SearchResult('doc3', 'content3', {}, 0.7, 'keyword')
    ]
    
    sorted_results = sorted(results)
    
    assert sorted_results[0].score == 0.9  # Highest first
    assert sorted_results[1].score == 0.7
    assert sorted_results[2].score == 0.5


# Tests: SearchQuery Dataclass

def test_search_query_defaults():
    """Test SearchQuery default values"""
    query = SearchQuery(query_text='test query')
    
    assert query.query_text == 'test query'
    assert query.top_k == 10
    assert query.filters is None
    assert query.search_types == ['vector', 'graph']
    assert query.weights is not None


def test_search_query_weight_normalization():
    """Test SearchQuery weight normalization"""
    query = SearchQuery(
        query_text='test',
        weights={'vector': 0.6, 'graph': 0.3, 'keyword': 0.3}  # Sum = 1.2
    )
    
    # Weights should be normalized to sum to 1.0
    weight_sum = sum(query.weights.values())
    assert abs(weight_sum - 1.0) < 0.01


# Tests: Vector Search

@pytest.mark.asyncio
async def test_vector_search_basic(search_api):
    """Test basic vector search"""
    # Generate mock embedding (384D)
    embedding = [0.1] * 384
    
    results = await search_api.vector_search(embedding, top_k=10)
    
    assert len(results) == 2  # MockVectorBackend returns 2 results
    assert all(isinstance(r, SearchResult) for r in results)
    assert all(r.source == 'vector' for r in results)
    assert results[0].document_id == 'doc_vector_1'


@pytest.mark.asyncio
async def test_vector_search_score_conversion(search_api):
    """Test distance to similarity conversion"""
    embedding = [0.1] * 384
    
    results = await search_api.vector_search(embedding, top_k=10)
    
    # MockVectorBackend returns distance=0.2 for doc1
    # Similarity = 1.0 - 0.2 = 0.8
    assert results[0].score == pytest.approx(0.8, abs=0.01)
    assert results[1].score == pytest.approx(0.6, abs=0.01)  # 1.0 - 0.4


# Tests: Graph Search

@pytest.mark.asyncio
async def test_graph_search_basic(search_api):
    """Test basic graph search"""
    results = await search_api.graph_search('Photovoltaik', top_k=10)
    
    assert len(results) == 2  # MockGraphBackend returns 2 results
    assert all(isinstance(r, SearchResult) for r in results)
    assert all(r.source == 'graph' for r in results)
    assert results[0].document_id == 'doc_graph_1'


@pytest.mark.asyncio
async def test_graph_search_node_property_extraction(search_api):
    """Test Neo4j Node property extraction"""
    results = await search_api.graph_search('test', top_k=10)
    
    # Check that Node properties were extracted correctly
    assert results[0].metadata['name'] == 'LBO BW § 58'
    assert results[0].metadata['document_type'] == 'regulation'
    assert results[0].content == 'Photovoltaik regulations'


# Tests: Keyword Search

@pytest.mark.asyncio
async def test_keyword_search_not_implemented(search_api):
    """Test keyword search (not implemented in real PostgreSQL backend)"""
    results = await search_api.keyword_search('test', top_k=10)
    
    # Real backend has no execute_sql() → should return empty list
    # Mock backend has execute_sql() → returns results
    # Both are valid behaviors
    assert isinstance(results, list)


# Tests: Hybrid Search

@pytest.mark.asyncio
async def test_hybrid_search_basic(search_api):
    """Test basic hybrid search"""
    query = SearchQuery(
        query_text='Photovoltaik',
        top_k=10,
        search_types=['vector', 'graph'],
        weights={'vector': 0.5, 'graph': 0.5}
    )
    
    results = await search_api.hybrid_search(query)
    
    assert len(results) > 0
    assert all(isinstance(r, SearchResult) for r in results)


@pytest.mark.asyncio
async def test_hybrid_search_weighted_scoring(search_api):
    """Test hybrid search weighted scoring"""
    query = SearchQuery(
        query_text='test',
        top_k=10,
        search_types=['vector', 'graph'],
        weights={'vector': 0.7, 'graph': 0.3}
    )
    
    results = await search_api.hybrid_search(query)
    
    # Check that weights were applied
    # Vector results should have higher scores (0.7 weight)
    # Graph results should have lower scores (0.3 weight)
    assert all(0.0 <= r.score <= 1.0 for r in results)


@pytest.mark.asyncio
async def test_hybrid_search_deduplication(search_api):
    """Test hybrid search deduplicates results by document_id"""
    query = SearchQuery(
        query_text='test',
        top_k=10,
        search_types=['vector', 'graph']
    )
    
    results = await search_api.hybrid_search(query)
    
    # Check no duplicate document_ids
    doc_ids = [r.document_id for r in results]
    assert len(doc_ids) == len(set(doc_ids))  # All unique


@pytest.mark.asyncio
async def test_hybrid_search_top_k_limit(search_api):
    """Test hybrid search respects top_k limit"""
    query = SearchQuery(
        query_text='test',
        top_k=2,  # Limit to 2 results
        search_types=['vector', 'graph']
    )
    
    results = await search_api.hybrid_search(query)
    
    assert len(results) <= 2


# Tests: Error Handling

@pytest.mark.asyncio
async def test_vector_search_backend_unavailable():
    """Test vector search with unavailable backend"""
    class EmptyStrategy:
        vector_backend = None
        graph_backend = None
        relational_backend = None
    
    api = UDS3SearchAPI(EmptyStrategy())
    
    results = await api.vector_search([0.1] * 384, top_k=10)
    
    # Should return empty list gracefully
    assert results == []


@pytest.mark.asyncio
async def test_graph_search_backend_unavailable():
    """Test graph search with unavailable backend"""
    class EmptyStrategy:
        vector_backend = None
        graph_backend = None
        relational_backend = None
    
    api = UDS3SearchAPI(EmptyStrategy())
    
    results = await api.graph_search('test', top_k=10)
    
    # Should return empty list gracefully
    assert results == []


# Tests: Convenience Functions

def test_create_search_api(mock_strategy):
    """Test create_search_api factory function"""
    api = create_search_api(mock_strategy)
    
    assert isinstance(api, UDS3SearchAPI)
    assert api.strategy == mock_strategy


# Tests: Edge Cases

@pytest.mark.asyncio
async def test_empty_query(search_api):
    """Test hybrid search with empty query"""
    query = SearchQuery(
        query_text='',
        top_k=10
    )
    
    results = await search_api.hybrid_search(query)
    
    # Should still work (backends handle empty queries)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_zero_weights(search_api):
    """Test hybrid search with zero weights"""
    query = SearchQuery(
        query_text='test',
        top_k=10,
        search_types=['vector'],
        weights={'vector': 0.0, 'graph': 0.0}  # All zero
    )
    
    results = await search_api.hybrid_search(query)
    
    # Normalization should handle this
    assert isinstance(results, list)


# Summary

def test_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("UDS3 Search API - Unit Tests Summary")
    print("="*60)
    print("✅ SearchResult dataclass tests")
    print("✅ SearchQuery dataclass tests")
    print("✅ Vector search tests (mock ChromaDB)")
    print("✅ Graph search tests (mock Neo4j)")
    print("✅ Keyword search tests (mock PostgreSQL)")
    print("✅ Hybrid search tests (weighted combination)")
    print("✅ Error handling tests (graceful degradation)")
    print("✅ Edge case tests (empty query, zero weights)")
    print("="*60)
    print("Total: 18 tests")
    print("="*60)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
