"""
Unit Tests for QueryService Hybrid Mode

Tests the hybrid search functionality in QueryService including:
- Successful hybrid search execution
- RAGService integration
- RerankerService integration
- UnifiedResponse format validation
- Error handling and fallbacks
- Edge cases (empty results, unavailable services)

Author: VERITAS AI
Created: 20. Oktober 2025
Version: 1.0
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any

# Import classes to test
from backend.services.query_service import QueryService
from backend.models.request import UnifiedQueryRequest
from backend.models.enums import QueryMode

# Import RAG Service types
from backend.services.rag_service import (
    HybridSearchResult,
    SearchResult,
    SearchMethod,
    RankingStrategy,
    SearchWeights,
    DocumentMetadata
)

# Import Reranker types
from backend.services.reranker_service import (
    RerankingResult,
    ScoringMode
)


class TestQueryServiceHybridMode:
    """Test suite for QueryService hybrid search functionality"""
    
    @pytest.fixture
    def mock_uds3(self):
        """Create mock UDS3 instance"""
        uds3 = Mock()
        uds3.chromadb = Mock()
        uds3.neo4j = Mock()
        uds3.postgresql = Mock()
        return uds3
    
    @pytest.fixture
    def mock_pipeline(self):
        """Create mock pipeline"""
        return Mock()
    
    @pytest.fixture
    def sample_query_request(self):
        """Create sample query request"""
        return UnifiedQueryRequest(
            query="Wie beantrage ich eine Baugenehmigung in Stuttgart?",
            mode=QueryMode.HYBRID,
            max_results=10,
            enable_reranking=True
        )
    
    @pytest.fixture
    def sample_search_results(self):
        """Create sample search results"""
        results = []
        for i in range(5):
            metadata = DocumentMetadata(
                document_id=f"doc_{i}",
                title=f"Dokument {i}: Baurecht Stuttgart",
                source_type="pdf",
                created_at=datetime(2024, 1, 1),
                author="Stadt Stuttgart",
                file_path=f"/docs/baurecht_{i}.pdf",
                page_count=50,
                tags=["Baurecht", "Stuttgart"],
                custom_fields={
                    "publisher": "Stadtrecht Verlag",
                    "rechtsgebiet": "Baurecht",
                    "normtyp": "Verwaltungsvorschrift"
                }
            )
            
            result = SearchResult(
                document_id=f"doc_{i}",
                content=f"Inhalt des Dokuments {i} über Baugenehmigungen...",
                relevance_score=0.9 - (i * 0.1),  # Descending scores
                metadata=metadata,
                search_method=SearchMethod.VECTOR if i % 2 == 0 else SearchMethod.GRAPH,
                rank=i + 1,
                page_number=10 + i
            )
            results.append(result)
        
        return results
    
    @pytest.fixture
    def sample_hybrid_result(self, sample_search_results):
        """Create sample HybridSearchResult"""
        return HybridSearchResult(
            results=sample_search_results,
            total_count=len(sample_search_results),
            query="Wie beantrage ich eine Baugenehmigung in Stuttgart?",
            search_methods_used=[SearchMethod.VECTOR, SearchMethod.GRAPH, SearchMethod.RELATIONAL],
            ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION,
            weights=SearchWeights(vector_weight=0.6, graph_weight=0.2, relational_weight=0.2),
            execution_time_ms=125.5
        )
    
    @pytest.fixture
    def sample_reranking_results(self):
        """Create sample reranking results"""
        results = []
        for i in range(5):
            result = RerankingResult(
                document_id=f"doc_{i}",
                original_score=0.9 - (i * 0.1),
                reranked_score=0.85 - (i * 0.05),  # Slightly different ranking
                score_delta=-0.05 if i < 3 else 0.05,  # Some improve, some degrade
                confidence=0.95,
                reasoning=f"Document {i} is highly relevant to building permits"
            )
            results.append(result)
        return results
    
    # ============================================================================
    # Test: Successful Hybrid Search
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_hybrid_search_success(
        self,
        mock_uds3,
        mock_pipeline,
        sample_query_request,
        sample_hybrid_result
    ):
        """Test successful hybrid search execution"""
        
        # Create QueryService with mocked dependencies
        with patch('backend.services.query_service.RAGService') as MockRAGService:
            # Setup mock RAG service
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = sample_hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            # Create service
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            
            # Disable reranking for this test
            sample_query_request.enable_reranking = False
            
            # Execute
            result = await service._process_hybrid(sample_query_request)
            
            # Assertions
            assert result is not None
            assert "response_text" in result
            assert "sources" in result
            assert "rag_context" in result
            assert "confidence_score" in result
            
            # Verify sources
            assert len(result["sources"]) == 5
            for source in result["sources"]:
                assert "document_id" in source
                assert "title" in source
                assert "relevance_score" in source
                assert "search_method" in source
                assert "ieee_citation" in source
            
            # Verify RAG context
            rag_context = result["rag_context"]
            assert rag_context["total_results"] == 5
            assert rag_context["ranking_strategy"] == "rrf"
            assert "execution_time_ms" in rag_context
            assert "weights" in rag_context
    
    # ============================================================================
    # Test: RAGService Integration
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_rag_service_initialization(self, mock_uds3, mock_pipeline):
        """Test that RAGService is properly initialized"""
        
        with patch('backend.services.query_service.RAGService') as MockRAGService:
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            
            # Verify RAGService was instantiated
            MockRAGService.assert_called_once()
            assert service.rag_service is not None
    
    @pytest.mark.asyncio
    async def test_hybrid_search_calls_rag_service(
        self,
        mock_uds3,
        mock_pipeline,
        sample_query_request,
        sample_hybrid_result
    ):
        """Test that hybrid search properly calls RAGService.hybrid_search()"""
        
        with patch('backend.services.query_service.RAGService') as MockRAGService:
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = sample_hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            sample_query_request.enable_reranking = False
            
            await service._process_hybrid(sample_query_request)
            
            # Verify hybrid_search was called with correct parameters
            mock_rag_instance.hybrid_search.assert_called_once()
            call_args = mock_rag_instance.hybrid_search.call_args
            
            assert call_args.kwargs['query'] == sample_query_request.query
            assert isinstance(call_args.kwargs['weights'], SearchWeights)
            assert call_args.kwargs['ranking_strategy'] == RankingStrategy.RECIPROCAL_RANK_FUSION
    
    # ============================================================================
    # Test: RerankerService Integration
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_reranker_service_initialization(self, mock_uds3, mock_pipeline):
        """Test that RerankerService is properly initialized"""
        
        with patch('backend.services.query_service.RerankerService') as MockRerankerService:
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            
            # Verify RerankerService was instantiated with correct params
            MockRerankerService.assert_called_once_with(
                model_name="llama3.1:8b",
                scoring_mode=ScoringMode.COMBINED,
                temperature=0.1
            )
            assert service.reranker_service is not None
    
    @pytest.mark.asyncio
    async def test_reranking_applied_when_enabled(
        self,
        mock_uds3,
        mock_pipeline,
        sample_query_request,
        sample_hybrid_result,
        sample_reranking_results
    ):
        """Test that reranking is applied when enabled"""
        
        with patch('backend.services.query_service.RAGService') as MockRAGService, \
             patch('backend.services.query_service.RerankerService') as MockRerankerService:
            
            # Setup mocks
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = sample_hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            mock_reranker_instance = Mock()
            mock_reranker_instance.rerank.return_value = sample_reranking_results
            MockRerankerService.return_value = mock_reranker_instance
            
            # Create service and execute
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            sample_query_request.enable_reranking = True
            
            result = await service._process_hybrid(sample_query_request)
            
            # Verify reranker was called
            mock_reranker_instance.rerank.assert_called_once()
            
            # Verify reranking info is in sources
            for source in result["sources"]:
                assert "rerank_applied" in source
                assert source["rerank_applied"] is True
                assert "rerank_score" in source
                assert "score_delta" in source
    
    @pytest.mark.asyncio
    async def test_reranking_disabled_when_flag_false(
        self,
        mock_uds3,
        mock_pipeline,
        sample_query_request,
        sample_hybrid_result
    ):
        """Test that reranking is skipped when disabled"""
        
        with patch('backend.services.query_service.RAGService') as MockRAGService, \
             patch('backend.services.query_service.RerankerService') as MockRerankerService:
            
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = sample_hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            mock_reranker_instance = Mock()
            MockRerankerService.return_value = mock_reranker_instance
            
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            sample_query_request.enable_reranking = False
            
            result = await service._process_hybrid(sample_query_request)
            
            # Verify reranker was NOT called
            mock_reranker_instance.rerank.assert_not_called()
            
            # Verify no reranking info in sources
            for source in result["sources"]:
                assert source["rerank_applied"] is False or source.get("rerank_score") is None
    
    # ============================================================================
    # Test: UnifiedResponse Format Validation
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_unified_response_format(
        self,
        mock_uds3,
        mock_pipeline,
        sample_query_request,
        sample_hybrid_result
    ):
        """Test that response matches UnifiedResponse format"""
        
        with patch('backend.services.query_service.RAGService') as MockRAGService:
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = sample_hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            sample_query_request.enable_reranking = False
            
            result = await service._process_hybrid(sample_query_request)
            
            # Required top-level fields
            required_fields = ["response_text", "confidence_score", "sources", "rag_context", "agent_results"]
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"
            
            # Verify types
            assert isinstance(result["response_text"], str)
            assert isinstance(result["confidence_score"], float)
            assert isinstance(result["sources"], list)
            assert isinstance(result["rag_context"], dict)
            assert isinstance(result["agent_results"], list)
    
    @pytest.mark.asyncio
    async def test_source_metadata_fields(
        self,
        mock_uds3,
        mock_pipeline,
        sample_query_request,
        sample_hybrid_result
    ):
        """Test that source metadata contains all IEEE citation fields"""
        
        with patch('backend.services.query_service.RAGService') as MockRAGService:
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = sample_hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            sample_query_request.enable_reranking = False
            
            result = await service._process_hybrid(sample_query_request)
            
            # Check first source
            source = result["sources"][0]
            
            # Required IEEE citation fields
            ieee_fields = [
                "id", "document_id", "title", "type", "content",
                "authors", "year", "publisher", "ieee_citation",
                "relevance_score", "score", "search_method", "rank"
            ]
            
            for field in ieee_fields:
                assert field in source, f"Missing IEEE field: {field}"
    
    # ============================================================================
    # Test: Error Handling
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_fallback_when_rag_service_unavailable(
        self,
        mock_pipeline,
        sample_query_request
    ):
        """Test fallback to RAG mode when RAGService is unavailable"""
        
        # Create service without UDS3 (RAGService won't initialize)
        service = QueryService(uds3=None, pipeline=mock_pipeline)
        
        # Mock _process_rag
        service._process_rag = AsyncMock(return_value={"response_text": "Fallback response"})
        
        result = await service._process_hybrid(sample_query_request)
        
        # Verify fallback was called
        service._process_rag.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fallback_when_hybrid_search_fails(
        self,
        mock_uds3,
        mock_pipeline,
        sample_query_request
    ):
        """Test fallback to RAG mode when hybrid search raises exception"""
        
        with patch('backend.services.query_service.RAGService') as MockRAGService:
            # Setup mock to raise exception
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.side_effect = Exception("Database connection failed")
            MockRAGService.return_value = mock_rag_instance
            
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            service._process_rag = AsyncMock(return_value={"response_text": "Fallback response"})
            
            result = await service._process_hybrid(sample_query_request)
            
            # Verify fallback was called
            service._process_rag.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reranking_fallback_on_error(
        self,
        mock_uds3,
        mock_pipeline,
        sample_query_request,
        sample_hybrid_result
    ):
        """Test that original scores are kept when reranking fails"""
        
        with patch('backend.services.query_service.RAGService') as MockRAGService, \
             patch('backend.services.query_service.RerankerService') as MockRerankerService:
            
            # Setup mocks
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = sample_hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            # Reranker raises exception
            mock_reranker_instance = Mock()
            mock_reranker_instance.rerank.side_effect = Exception("LLM timeout")
            MockRerankerService.return_value = mock_reranker_instance
            
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            sample_query_request.enable_reranking = True
            
            result = await service._process_hybrid(sample_query_request)
            
            # Verify result is still returned (not failed)
            assert result is not None
            assert "sources" in result
            
            # Verify scores are still present (original scores)
            for source in result["sources"]:
                assert "relevance_score" in source
                assert source["relevance_score"] > 0
    
    # ============================================================================
    # Test: Edge Cases
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_empty_search_results(
        self,
        mock_uds3,
        mock_pipeline,
        sample_query_request
    ):
        """Test handling of empty search results"""
        
        with patch('backend.services.query_service.RAGService') as MockRAGService:
            # Create empty result
            empty_result = HybridSearchResult(
                results=[],
                total_count=0,
                query=sample_query_request.query,
                search_methods_used=[SearchMethod.VECTOR],
                ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION,
                weights=SearchWeights(),
                execution_time_ms=10.0
            )
            
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = empty_result
            MockRAGService.return_value = mock_rag_instance
            
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            sample_query_request.enable_reranking = False
            
            result = await service._process_hybrid(sample_query_request)
            
            # Verify empty result is handled gracefully
            assert result is not None
            assert len(result["sources"]) == 0
            assert result["rag_context"]["total_results"] == 0
    
    @pytest.mark.asyncio
    async def test_max_results_limit(
        self,
        mock_uds3,
        mock_pipeline,
        sample_query_request,
        sample_search_results
    ):
        """Test that max_results parameter limits returned results"""
        
        # Create result with 20 documents
        many_results = sample_search_results * 4  # 20 results
        hybrid_result = HybridSearchResult(
            results=many_results,
            total_count=20,
            query=sample_query_request.query,
            search_methods_used=[SearchMethod.VECTOR],
            ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION,
            weights=SearchWeights(),
            execution_time_ms=150.0
        )
        
        with patch('backend.services.query_service.RAGService') as MockRAGService:
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            sample_query_request.max_results = 5
            sample_query_request.enable_reranking = False
            
            result = await service._process_hybrid(sample_query_request)
            
            # Verify only 5 results are returned
            assert len(result["sources"]) == 5
    
    @pytest.mark.asyncio
    async def test_confidence_score_calculation(
        self,
        mock_uds3,
        mock_pipeline,
        sample_query_request,
        sample_hybrid_result
    ):
        """Test that confidence score is properly calculated"""
        
        with patch('backend.services.query_service.RAGService') as MockRAGService:
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = sample_hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            service = QueryService(uds3=mock_uds3, pipeline=mock_pipeline)
            sample_query_request.enable_reranking = False
            
            result = await service._process_hybrid(sample_query_request)
            
            # Confidence should be average of top 3 scores
            top_3_scores = [0.9, 0.8, 0.7]  # From sample_search_results
            expected_confidence = sum(top_3_scores) / 3
            
            assert result["confidence_score"] == pytest.approx(expected_confidence, rel=0.01)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
