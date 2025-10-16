"""
Test LLM Reranker Service (Phase 5 - Task 2.3)

Tests the RerankerService for LLM-based result scoring.

Version: 1.0.0
Phase: 5 (v5.0 Enhanced RAG)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from services.reranker_service import (
    RerankerService, ScoringMode, RerankingResult
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def reranker_service():
    """Create RerankerService for testing"""
    return RerankerService(model_name="llama3.1:8b")


@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return [
        {
            'document_id': 'doc1',
            'content': 'Ein Bauantrag in Stuttgart erfordert verschiedene Unterlagen und Formulare.',
            'relevance_score': 0.85
        },
        {
            'document_id': 'doc2',
            'content': 'Die Geschichte der Automobilindustrie in Stuttgart ist sehr interessant.',
            'relevance_score': 0.60
        },
        {
            'document_id': 'doc3',
            'content': 'Bauantragsverfahren für Wohngebäude: Eine Schritt-für-Schritt Anleitung.',
            'relevance_score': 0.75
        }
    ]


# ============================================================================
# TESTS
# ============================================================================

def test_reranker_initialization(reranker_service):
    """Test RerankerService initialization"""
    assert reranker_service is not None
    assert reranker_service.model_name == "llama3.1:8b"
    assert reranker_service.scoring_mode == ScoringMode.COMBINED
    assert reranker_service.temperature == 0.1


def test_rerank_basic(reranker_service, sample_documents):
    """Test basic reranking functionality"""
    query = "Bauantrag Stuttgart"
    results = reranker_service.rerank(query, sample_documents)
    
    # Should return result for each document
    assert len(results) == len(sample_documents)
    
    # Each result should be RerankingResult
    for result in results:
        assert isinstance(result, RerankingResult)
        assert hasattr(result, 'document_id')
        assert hasattr(result, 'original_score')
        assert hasattr(result, 'reranked_score')
        assert hasattr(result, 'score_delta')


def test_rerank_empty_documents(reranker_service):
    """Test reranking with empty document list"""
    results = reranker_service.rerank("test query", [])
    assert len(results) == 0


def test_rerank_top_k(reranker_service, sample_documents):
    """Test top_k parameter"""
    query = "Bauantrag Stuttgart"
    
    # Get top 2 results
    results = reranker_service.rerank(query, sample_documents, top_k=2)
    
    assert len(results) == 2, "Should return only top 2 results"


def test_rerank_scoring_modes(sample_documents):
    """Test different scoring modes"""
    query = "Bauantrag Stuttgart"
    
    # Test each scoring mode
    for mode in ScoringMode:
        reranker = RerankerService(scoring_mode=mode)
        results = reranker.rerank(query, sample_documents)
        
        assert len(results) == len(sample_documents)
        assert reranker.scoring_mode == mode


def test_rerank_score_validation(reranker_service, sample_documents):
    """Test that scores are valid (0.0-1.0 range)"""
    query = "Bauantrag Stuttgart"
    results = reranker_service.rerank(query, sample_documents)
    
    for result in results:
        assert 0.0 <= result.original_score <= 1.0
        assert 0.0 <= result.reranked_score <= 1.0
        assert 0.0 <= result.confidence <= 1.0


def test_rerank_sorting(reranker_service, sample_documents):
    """Test that results are sorted by reranked_score"""
    query = "Bauantrag Stuttgart"
    results = reranker_service.rerank(query, sample_documents)
    
    # Check sorting (descending)
    for i in range(len(results) - 1):
        assert results[i].reranked_score >= results[i+1].reranked_score


def test_rerank_batch_processing(reranker_service):
    """Test batch processing with many documents"""
    query = "test query"
    
    # Create 20 documents
    documents = [
        {
            'document_id': f'doc{i}',
            'content': f'Document content {i}',
            'relevance_score': 0.5 + (i * 0.01)
        }
        for i in range(20)
    ]
    
    # Test with different batch sizes
    results_5 = reranker_service.rerank(query, documents, batch_size=5)
    results_10 = reranker_service.rerank(query, documents, batch_size=10)
    
    # Should process all documents regardless of batch size
    assert len(results_5) == 20
    assert len(results_10) == 20


def test_fallback_scoring(reranker_service, sample_documents):
    """Test fallback scoring when LLM fails"""
    # Fallback should preserve original scores
    results = reranker_service._fallback_scoring(sample_documents)
    
    for i, result in enumerate(results):
        assert result.original_score == result.reranked_score
        assert result.score_delta == 0.0
        assert result.reasoning == "Fallback: LLM unavailable"


def test_statistics_tracking(reranker_service, sample_documents):
    """Test statistics tracking"""
    query = "Bauantrag Stuttgart"
    
    # Reset stats
    reranker_service.reset_statistics()
    
    # Perform rerankings
    reranker_service.rerank(query, sample_documents)
    reranker_service.rerank(query, sample_documents)
    
    # Check stats
    stats = reranker_service.get_statistics()
    assert stats['total_rerankings'] == 2
    assert stats['avg_reranking_time_ms'] > 0


def test_statistics_reset(reranker_service, sample_documents):
    """Test statistics reset"""
    query = "Bauantrag Stuttgart"
    
    # Perform reranking
    reranker_service.rerank(query, sample_documents)
    
    # Reset
    reranker_service.reset_statistics()
    
    # Check all stats are zero
    stats = reranker_service.get_statistics()
    assert stats['total_rerankings'] == 0
    assert stats['llm_successes'] == 0
    assert stats['fallback_count'] == 0


def test_reranking_result_to_dict(reranker_service, sample_documents):
    """Test RerankingResult to_dict conversion"""
    query = "Bauantrag Stuttgart"
    results = reranker_service.rerank(query, sample_documents)
    
    # Convert to dict
    result_dict = results[0].to_dict()
    
    # Check required fields
    assert 'document_id' in result_dict
    assert 'original_score' in result_dict
    assert 'reranked_score' in result_dict
    assert 'score_delta' in result_dict
    assert 'confidence' in result_dict


def test_parse_llm_scores_valid_json(reranker_service):
    """Test parsing valid LLM score response"""
    response = "[0.9, 0.8, 0.7]"
    scores = reranker_service._parse_llm_scores(response, 3)
    
    assert len(scores) == 3
    assert scores[0] == 0.9
    assert scores[1] == 0.8
    assert scores[2] == 0.7


def test_parse_llm_scores_with_text(reranker_service):
    """Test parsing LLM scores with surrounding text"""
    response = "Here are the scores:\n[0.9, 0.8, 0.7]\nThese are my ratings."
    scores = reranker_service._parse_llm_scores(response, 3)
    
    assert len(scores) == 3
    assert scores[0] == 0.9


def test_parse_llm_scores_invalid(reranker_service):
    """Test parsing invalid LLM response"""
    response = "This is not a valid JSON array"
    scores = reranker_service._parse_llm_scores(response, 3)
    
    # Should return empty dict on parse error
    assert len(scores) == 0


def test_parse_llm_scores_out_of_range(reranker_service):
    """Test score normalization for out-of-range values"""
    response = "[1.5, -0.2, 0.5]"  # Values outside 0-1 range
    scores = reranker_service._parse_llm_scores(response, 3)
    
    # Should clamp to 0-1 range
    assert scores[0] == 1.0  # Clamped from 1.5
    assert scores[1] == 0.0  # Clamped from -0.2
    assert scores[2] == 0.5  # Within range


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("RERANKER SERVICE TEST SUITE")
    print("="*80)
    
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
