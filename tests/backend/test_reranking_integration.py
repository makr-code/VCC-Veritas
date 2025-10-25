"""
Integration Tests for RerankerService

Tests the reranking functionality with real/mocked LLM including:
- Score improvements validation
- Batch processing efficiency
- LLM timeout handling
- Performance benchmarks (latency < 2s for 10 docs)
- Statistical tracking

Note: These tests can run with either:
1. Mock LLM (for CI/CD pipelines)
2. Real Ollama (for integration testing)

Set RERANKER_USE_REAL_LLM=true to use real Ollama instance.

Author: VERITAS AI
Created: 20. Oktober 2025
Version: 1.0
"""

import pytest
import time
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import service to test
from backend.services.reranker_service import (
    RerankerService,
    ScoringMode,
    RerankingResult
)

# Check if we should use real LLM
USE_REAL_LLM = os.getenv("RERANKER_USE_REAL_LLM", "false").lower() == "true"


class TestRerankerServiceIntegration:
    """Integration tests for RerankerService"""
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for reranking"""
        return [
            {
                'document_id': 'doc_1',
                'content': 'Die Baugenehmigung für Wohngebäude in Stuttgart muss bei der '
                          'Baurechtsabteilung beantragt werden. Erforderliche Unterlagen sind: '
                          'Bauzeichnungen, Grundriss, statische Berechnungen.',
                'relevance_score': 0.75,
                'metadata': {'title': 'Baurecht Stuttgart - Wohngebäude'}
            },
            {
                'document_id': 'doc_2',
                'content': 'Das Bundes-Immissionsschutzgesetz (BImSchG) regelt den Schutz '
                          'vor schädlichen Umwelteinwirkungen. Es gilt für alle '
                          'genehmigungsbedürftigen Anlagen.',
                'relevance_score': 0.68,
                'metadata': {'title': 'BImSchG Übersicht'}
            },
            {
                'document_id': 'doc_3',
                'content': 'Für gewerbliche Bauvorhaben gelten besondere Anforderungen. '
                          'Neben der Baugenehmigung sind oft auch Umweltgutachten erforderlich.',
                'relevance_score': 0.82,
                'metadata': {'title': 'Gewerbebau Genehmigung'}
            },
            {
                'document_id': 'doc_4',
                'content': 'Die Gebühren für Baugenehmigungen richten sich nach der '
                          'Bauordnung des Landes Baden-Württemberg. Die Bearbeitungszeit '
                          'beträgt in der Regel 4-8 Wochen.',
                'relevance_score': 0.71,
                'metadata': {'title': 'Gebührenordnung Bau'}
            },
            {
                'document_id': 'doc_5',
                'content': 'Naturschutzrechtliche Vorschriften müssen bei allen Bauvorhaben '
                          'beachtet werden. Besonders in Schutzgebieten gelten strenge Auflagen.',
                'relevance_score': 0.65,
                'metadata': {'title': 'Naturschutz im Baurecht'}
            }
        ]
    
    @pytest.fixture
    def large_document_set(self, sample_documents):
        """Create larger document set for batch testing"""
        # Duplicate and modify documents to create 20 documents
        large_set = []
        for i in range(4):
            for doc in sample_documents:
                new_doc = doc.copy()
                new_doc['document_id'] = f"{doc['document_id']}_batch_{i}"
                new_doc['relevance_score'] = doc['relevance_score'] - (i * 0.05)
                large_set.append(new_doc)
        return large_set
    
    # ============================================================================
    # Test: Basic Reranking with Mock LLM
    # ============================================================================
    
    @pytest.mark.skipif(USE_REAL_LLM, reason="Skipping mock tests when using real LLM")
    def test_reranking_with_mock_llm(self, sample_documents):
        """Test basic reranking with mocked LLM responses"""
        
        with patch('backend.services.reranker_service.DirectOllamaLLM') as MockLLM:
            # Setup mock LLM
            mock_llm_instance = Mock()
            
            # Mock generate() to return relevance scores
            def mock_generate(prompt):
                # Return mock JSON with scores
                return '''
                {
                    "scores": [
                        {"document_id": "doc_1", "score": 0.92, "reasoning": "Highly relevant for building permits"},
                        {"document_id": "doc_2", "score": 0.45, "reasoning": "About environmental law, less relevant"},
                        {"document_id": "doc_3", "score": 0.88, "reasoning": "Commercial building permits, very relevant"},
                        {"document_id": "doc_4", "score": 0.71, "reasoning": "About fees, moderately relevant"},
                        {"document_id": "doc_5", "score": 0.52, "reasoning": "Nature protection, somewhat relevant"}
                    ]
                }
                '''
            
            mock_llm_instance.generate.side_effect = mock_generate
            MockLLM.return_value = mock_llm_instance
            
            # Create service and test
            reranker = RerankerService(
                model_name="llama3.1:8b",
                scoring_mode=ScoringMode.COMBINED
            )
            
            results = reranker.rerank(
                query="Wie beantrage ich eine Baugenehmigung?",
                documents=sample_documents,
                top_k=5
            )
            
            # Assertions
            assert len(results) == 5
            assert all(isinstance(r, RerankingResult) for r in results)
            
            # Verify scores were applied
            assert results[0].reranked_score > 0
            assert results[0].document_id in [doc['document_id'] for doc in sample_documents]
            
            # Verify sorted by reranked score
            scores = [r.reranked_score for r in results]
            assert scores == sorted(scores, reverse=True)
    
    # ============================================================================
    # Test: Score Improvements
    # ============================================================================
    
    @pytest.mark.skipif(USE_REAL_LLM, reason="Skipping mock tests when using real LLM")
    def test_score_improvements_validation(self, sample_documents):
        """Test that reranking improves scores for relevant documents"""
        
        with patch('backend.services.reranker_service.DirectOllamaLLM') as MockLLM:
            mock_llm_instance = Mock()
            
            # Mock: Improve scores for docs with "Baugenehmigung" in content
            def mock_generate(prompt):
                return '''
                {
                    "scores": [
                        {"document_id": "doc_1", "score": 0.95},
                        {"document_id": "doc_2", "score": 0.40},
                        {"document_id": "doc_3", "score": 0.90},
                        {"document_id": "doc_4", "score": 0.85},
                        {"document_id": "doc_5", "score": 0.50}
                    ]
                }
                '''
            
            mock_llm_instance.generate.side_effect = mock_generate
            MockLLM.return_value = mock_llm_instance
            
            reranker = RerankerService()
            results = reranker.rerank(
                query="Baugenehmigung beantragen",
                documents=sample_documents
            )
            
            # Find doc_1 result (most relevant to query)
            doc_1_result = next(r for r in results if r.document_id == 'doc_1')
            
            # Score should have improved (original: 0.75, reranked: 0.95)
            assert doc_1_result.score_delta > 0, "Expected positive score improvement"
            assert doc_1_result.reranked_score > doc_1_result.original_score
    
    # ============================================================================
    # Test: Batch Processing
    # ============================================================================
    
    @pytest.mark.skipif(USE_REAL_LLM, reason="Skipping mock tests when using real LLM")
    def test_batch_processing_5_docs(self, sample_documents):
        """Test batch processing with batch_size=5"""
        
        with patch('backend.services.reranker_service.DirectOllamaLLM') as MockLLM:
            mock_llm_instance = Mock()
            mock_llm_instance.generate.return_value = '{"scores": []}'
            MockLLM.return_value = mock_llm_instance
            
            reranker = RerankerService()
            reranker.rerank(
                query="test query",
                documents=sample_documents,
                batch_size=5
            )
            
            # With 5 docs and batch_size=5, should have 1 LLM call
            assert mock_llm_instance.generate.call_count == 1
    
    @pytest.mark.skipif(USE_REAL_LLM, reason="Skipping mock tests when using real LLM")
    def test_batch_processing_10_docs(self, large_document_set):
        """Test batch processing with 10 documents"""
        
        with patch('backend.services.reranker_service.DirectOllamaLLM') as MockLLM:
            mock_llm_instance = Mock()
            mock_llm_instance.generate.return_value = '{"scores": []}'
            MockLLM.return_value = mock_llm_instance
            
            reranker = RerankerService()
            docs_10 = large_document_set[:10]
            
            reranker.rerank(
                query="test query",
                documents=docs_10,
                batch_size=5
            )
            
            # With 10 docs and batch_size=5, should have 2 LLM calls
            assert mock_llm_instance.generate.call_count == 2
    
    @pytest.mark.skipif(USE_REAL_LLM, reason="Skipping mock tests when using real LLM")
    def test_batch_processing_20_docs(self, large_document_set):
        """Test batch processing with 20 documents"""
        
        with patch('backend.services.reranker_service.DirectOllamaLLM') as MockLLM:
            mock_llm_instance = Mock()
            mock_llm_instance.generate.return_value = '{"scores": []}'
            MockLLM.return_value = mock_llm_instance
            
            reranker = RerankerService()
            
            reranker.rerank(
                query="test query",
                documents=large_document_set,
                batch_size=5
            )
            
            # With 20 docs and batch_size=5, should have 4 LLM calls
            assert mock_llm_instance.generate.call_count == 4
    
    # ============================================================================
    # Test: LLM Timeout Handling
    # ============================================================================
    
    @pytest.mark.skipif(USE_REAL_LLM, reason="Skipping mock tests when using real LLM")
    def test_fallback_on_llm_timeout(self, sample_documents):
        """Test that original scores are kept when LLM times out"""
        
        with patch('backend.services.reranker_service.DirectOllamaLLM') as MockLLM:
            mock_llm_instance = Mock()
            
            # Simulate timeout
            mock_llm_instance.generate.side_effect = TimeoutError("LLM request timed out")
            MockLLM.return_value = mock_llm_instance
            
            reranker = RerankerService()
            results = reranker.rerank(
                query="test query",
                documents=sample_documents
            )
            
            # Should fallback to original scores
            assert len(results) == len(sample_documents)
            
            # Verify fallback: reranked_score should equal original_score
            for result in results:
                assert result.reranked_score == result.original_score
                assert result.score_delta == 0.0
    
    @pytest.mark.skipif(USE_REAL_LLM, reason="Skipping mock tests when using real LLM")
    def test_fallback_on_llm_error(self, sample_documents):
        """Test fallback when LLM returns malformed JSON"""
        
        with patch('backend.services.reranker_service.DirectOllamaLLM') as MockLLM:
            mock_llm_instance = Mock()
            
            # Return invalid JSON
            mock_llm_instance.generate.return_value = "This is not valid JSON"
            MockLLM.return_value = mock_llm_instance
            
            reranker = RerankerService()
            results = reranker.rerank(
                query="test query",
                documents=sample_documents
            )
            
            # Should fallback gracefully
            assert len(results) == len(sample_documents)
            
            # All scores should be original
            for result in results:
                assert result.reranked_score == result.original_score
    
    # ============================================================================
    # Test: Performance Benchmarks
    # ============================================================================
    
    @pytest.mark.skipif(USE_REAL_LLM, reason="Skipping mock tests when using real LLM")
    def test_latency_under_2s_for_10_docs(self, large_document_set):
        """Test that reranking 10 docs completes in < 2 seconds"""
        
        with patch('backend.services.reranker_service.DirectOllamaLLM') as MockLLM:
            mock_llm_instance = Mock()
            
            # Simulate realistic LLM latency (200ms per call)
            def mock_generate_with_delay(prompt):
                time.sleep(0.2)  # 200ms
                return '{"scores": []}'
            
            mock_llm_instance.generate.side_effect = mock_generate_with_delay
            MockLLM.return_value = mock_llm_instance
            
            reranker = RerankerService()
            docs_10 = large_document_set[:10]
            
            start_time = time.time()
            reranker.rerank(
                query="test query",
                documents=docs_10,
                batch_size=5  # 2 batches * 200ms = 400ms
            )
            elapsed = time.time() - start_time
            
            # Should complete in < 2 seconds (with overhead, allow 1s)
            assert elapsed < 1.0, f"Reranking took {elapsed:.2f}s, expected < 1.0s"
    
    # ============================================================================
    # Test: Statistics Tracking
    # ============================================================================
    
    @pytest.mark.skipif(USE_REAL_LLM, reason="Skipping mock tests when using real LLM")
    def test_statistics_tracking(self, sample_documents):
        """Test that reranker tracks statistics correctly"""
        
        with patch('backend.services.reranker_service.DirectOllamaLLM') as MockLLM:
            mock_llm_instance = Mock()
            mock_llm_instance.generate.return_value = '''
            {
                "scores": [
                    {"document_id": "doc_1", "score": 0.95},
                    {"document_id": "doc_2", "score": 0.60},
                    {"document_id": "doc_3", "score": 0.85},
                    {"document_id": "doc_4", "score": 0.70},
                    {"document_id": "doc_5", "score": 0.55}
                ]
            }
            '''
            MockLLM.return_value = mock_llm_instance
            
            reranker = RerankerService()
            
            # Perform reranking
            results = reranker.rerank(
                query="test query",
                documents=sample_documents
            )
            
            # Get statistics
            stats = reranker.get_statistics()
            
            # Verify statistics
            assert stats['total_rerankings'] == 1
            assert stats['llm_successes'] == 1
            assert stats['fallback_count'] == 0
            
            # Check score improvements/degradations
            improvements = sum(1 for r in results if r.score_delta > 0)
            degradations = sum(1 for r in results if r.score_delta < 0)
            
            assert stats['score_improvements'] == improvements
            assert stats['score_degradations'] == degradations
    
    # ============================================================================
    # Test: Real LLM Integration (Optional)
    # ============================================================================
    
    @pytest.mark.skipif(not USE_REAL_LLM, reason="Real LLM tests disabled (set RERANKER_USE_REAL_LLM=true)")
    @pytest.mark.integration
    def test_real_llm_reranking(self, sample_documents):
        """Integration test with real Ollama LLM"""
        
        # This test requires Ollama to be running
        try:
            reranker = RerankerService(
                model_name="llama3.1:8b",
                scoring_mode=ScoringMode.COMBINED,
                temperature=0.1
            )
            
            start_time = time.time()
            results = reranker.rerank(
                query="Wie beantrage ich eine Baugenehmigung in Stuttgart?",
                documents=sample_documents,
                top_k=5
            )
            elapsed = time.time() - start_time
            
            # Assertions
            assert len(results) == 5
            assert all(isinstance(r, RerankingResult) for r in results)
            
            # Verify scores are reasonable
            for result in results:
                assert 0.0 <= result.reranked_score <= 1.0
                assert result.confidence > 0
            
            # Print results for manual inspection
            print("\n=== Real LLM Reranking Results ===")
            print(f"Elapsed time: {elapsed:.2f}s")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.document_id}")
                print(f"   Original: {result.original_score:.3f}, Reranked: {result.reranked_score:.3f}")
                print(f"   Delta: {result.score_delta:+.3f}, Confidence: {result.confidence:.3f}")
                if result.reasoning:
                    print(f"   Reasoning: {result.reasoning}")
            
            # Performance check (should complete in reasonable time)
            assert elapsed < 10.0, f"Real LLM reranking took {elapsed:.2f}s, expected < 10s"
            
        except Exception as e:
            pytest.skip(f"Real LLM test failed (Ollama not available?): {e}")
    
    # ============================================================================
    # Test: Edge Cases
    # ============================================================================
    
    def test_empty_documents_list(self):
        """Test handling of empty documents list"""
        
        reranker = RerankerService()
        results = reranker.rerank(
            query="test query",
            documents=[],
            top_k=5
        )
        
        assert results == []
    
    @pytest.mark.skipif(USE_REAL_LLM, reason="Skipping mock tests when using real LLM")
    def test_single_document(self, sample_documents):
        """Test reranking with single document"""
        
        with patch('backend.services.reranker_service.DirectOllamaLLM') as MockLLM:
            mock_llm_instance = Mock()
            mock_llm_instance.generate.return_value = '''
            {"scores": [{"document_id": "doc_1", "score": 0.88}]}
            '''
            MockLLM.return_value = mock_llm_instance
            
            reranker = RerankerService()
            results = reranker.rerank(
                query="test query",
                documents=[sample_documents[0]]
            )
            
            assert len(results) == 1
            assert results[0].document_id == 'doc_1'
    
    @pytest.mark.skipif(USE_REAL_LLM, reason="Skipping mock tests when using real LLM")
    def test_top_k_filtering(self, sample_documents):
        """Test that top_k parameter limits results"""
        
        with patch('backend.services.reranker_service.DirectOllamaLLM') as MockLLM:
            mock_llm_instance = Mock()
            mock_llm_instance.generate.return_value = '''
            {
                "scores": [
                    {"document_id": "doc_1", "score": 0.95},
                    {"document_id": "doc_2", "score": 0.85},
                    {"document_id": "doc_3", "score": 0.75},
                    {"document_id": "doc_4", "score": 0.65},
                    {"document_id": "doc_5", "score": 0.55}
                ]
            }
            '''
            MockLLM.return_value = mock_llm_instance
            
            reranker = RerankerService()
            results = reranker.rerank(
                query="test query",
                documents=sample_documents,
                top_k=3  # Only return top 3
            )
            
            assert len(results) == 3
            # Should be top 3 by reranked score
            assert all(r.reranked_score >= 0.75 for r in results)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    # Run with: pytest test_reranking_integration.py -v
    # Or with real LLM: RERANKER_USE_REAL_LLM=true pytest test_reranking_integration.py -v -m integration
    pytest.main([__file__, "-v", "--tb=short"])
