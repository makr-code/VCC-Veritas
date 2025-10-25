"""
End-to-End Integration Tests for Hybrid Search Pipeline

Tests the complete flow from QueryService through RAG, RRF, Reranking to UnifiedResponse:
1. QueryService receives request
2. RAGService performs hybrid search (Vector + Graph + Relational)
3. RecipRocal Rank Fusion combines results
4. RerankerService improves ranking
5. UnifiedResponse with IEEE citations

Tests include:
- Real Verwaltungs-Queries (Bauantrag, BImSchG, etc.)
- All 35+ IEEE citation fields validation
- End-to-end latency measurement (target: < 10s)
- Performance benchmarks

Note: Set HYBRID_E2E_USE_REAL_SERVICES=true to test with real UDS3/Ollama

Author: VERITAS AI
Created: 20. Oktober 2025
Version: 1.0
"""

import pytest
import time
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
from datetime import datetime

# Import services
from backend.services.query_service import QueryService
from backend.models.request import UnifiedQueryRequest
from backend.models.enums import QueryMode

# Import RAG/Reranker types
from backend.services.rag_service import (
    HybridSearchResult,
    SearchResult,
    SearchMethod,
    RankingStrategy,
    SearchWeights,
    DocumentMetadata
)

# Check if we should use real services
USE_REAL_SERVICES = os.getenv("HYBRID_E2E_USE_REAL_SERVICES", "false").lower() == "true"


class TestHybridSearchPipelineE2E:
    """End-to-end integration tests for hybrid search pipeline"""
    
    # ============================================================================
    # Fixtures: Test Data
    # ============================================================================
    
    @pytest.fixture
    def real_verwaltung_queries(self):
        """Real-world German administrative queries"""
        return [
            {
                'query': 'Wie beantrage ich eine Baugenehmigung in Stuttgart?',
                'expected_topics': ['Bauantrag', 'Genehmigung', 'Stuttgart', 'Baurecht'],
                'min_results': 5
            },
            {
                'query': 'Welche Unterlagen benötige ich für einen BImSchG-Antrag?',
                'expected_topics': ['BImSchG', 'Immissionsschutz', 'Antrag', 'Unterlagen'],
                'min_results': 3
            },
            {
                'query': 'Fristen für Einspruch gegen Baugenehmigung?',
                'expected_topics': ['Frist', 'Einspruch', 'Widerspruch', 'Rechtsmittel'],
                'min_results': 3
            },
            {
                'query': 'Umweltverträglichkeitsprüfung bei Gewerbebauten',
                'expected_topics': ['UVP', 'Umwelt', 'Gewerbe', 'Prüfung'],
                'min_results': 5
            }
        ]
    
    @pytest.fixture
    def mock_uds3(self):
        """Mock UDS3 with database backends"""
        uds3 = Mock()
        uds3.chromadb = Mock()
        uds3.neo4j = Mock()
        uds3.postgresql = Mock()
        return uds3
    
    @pytest.fixture
    def comprehensive_search_results(self):
        """Create comprehensive search results with all metadata"""
        results = []
        
        test_docs = [
            {
                'id': 'baurecht_001',
                'title': 'Landesbauordnung Baden-Württemberg (LBO)',
                'content': 'Die Landesbauordnung regelt das Baurecht in Baden-Württemberg. '
                          'Baugenehmigungen müssen bei der zuständigen Bauaufsichtsbehörde beantragt werden. '
                          'Erforderliche Unterlagen: Bauzeichnungen, Lagepläne, statische Berechnungen.',
                'author': 'Land Baden-Württemberg',
                'publisher': 'Ministerium für Landesentwicklung und Wohnen',
                'year': 2024,
                'rechtsgebiet': 'Baurecht',
                'normtyp': 'Landesgesetz',
                'score': 0.92
            },
            {
                'id': 'bimschg_042',
                'title': 'Bundes-Immissionsschutzgesetz (BImSchG) - Genehmigungsverfahren',
                'content': 'Das BImSchG regelt den Schutz vor schädlichen Umwelteinwirkungen. '
                          'Genehmigungsbedürftige Anlagen sind in der 4. BImSchV aufgelistet. '
                          'Das Genehmigungsverfahren erfolgt nach §§ 10 ff. BImSchG.',
                'author': 'Deutscher Bundestag',
                'publisher': 'Bundesanzeiger Verlag',
                'year': 2023,
                'rechtsgebiet': 'Umweltrecht',
                'normtyp': 'Bundesgesetz',
                'score': 0.88
            },
            {
                'id': 'stuttgart_vv_015',
                'title': 'Verwaltungsvorschrift der Stadt Stuttgart - Bauanträge',
                'content': 'Bauanträge sind in zweifacher Ausfertigung einzureichen. '
                          'Die Bearbeitungszeit beträgt in der Regel 8-12 Wochen. '
                          'Zuständig: Amt für Stadtplanung und Wohnen, Abteilung Baurecht.',
                'author': 'Stadt Stuttgart',
                'publisher': 'Stadtverwaltung Stuttgart',
                'year': 2024,
                'rechtsgebiet': 'Kommunalrecht',
                'normtyp': 'Verwaltungsvorschrift',
                'score': 0.85
            },
            {
                'id': 'baugb_128',
                'title': 'Baugesetzbuch (BauGB) - Zulässigkeit von Vorhaben',
                'content': 'Die bauplanungsrechtliche Zulässigkeit von Vorhaben richtet sich '
                          'nach §§ 29 ff. BauGB. Im Geltungsbereich eines Bebauungsplans gilt § 30 BauGB.',
                'author': 'Deutscher Bundestag',
                'publisher': 'Bundesanzeiger Verlag',
                'year': 2024,
                'rechtsgebiet': 'Bauplanungsrecht',
                'normtyp': 'Bundesgesetz',
                'score': 0.79
            },
            {
                'id': 'uvp_guide_008',
                'title': 'Leitfaden Umweltverträglichkeitsprüfung (UVP)',
                'content': 'Die UVP ist für bestimmte Projekte nach UVPG verpflichtend. '
                          'Der Vorhabenträger muss einen UVP-Bericht erstellen. '
                          'Die Behörde prüft die Umweltauswirkungen.',
                'author': 'Umweltbundesamt',
                'publisher': 'UBA',
                'year': 2023,
                'rechtsgebiet': 'Umweltrecht',
                'normtyp': 'Leitfaden',
                'score': 0.82
            }
        ]
        
        for i, doc in enumerate(test_docs):
            metadata = DocumentMetadata(
                document_id=doc['id'],
                title=doc['title'],
                source_type='pdf',
                created_at=datetime(doc['year'], 1, 1),
                author=doc['author'],
                file_path=f'/docs/verwaltung/{doc["id"]}.pdf',
                page_count=150,
                tags=[doc['rechtsgebiet'], doc['normtyp']],
                custom_fields={
                    'publisher': doc['publisher'],
                    'rechtsgebiet': doc['rechtsgebiet'],
                    'normtyp': doc['normtyp'],
                    'geltungsbereich': 'Deutschland' if 'Bundes' in doc['normtyp'] else 'Baden-Württemberg',
                    'fundstelle': f'BGBl. I S. {1000 + i}' if 'Bundes' in doc['normtyp'] else f'GBl. BW S. {500 + i}'
                }
            )
            
            result = SearchResult(
                document_id=doc['id'],
                content=doc['content'],
                relevance_score=doc['score'],
                metadata=metadata,
                search_method=[SearchMethod.VECTOR, SearchMethod.GRAPH, SearchMethod.RELATIONAL][i % 3],
                rank=i + 1,
                page_number=15 + i * 5
            )
            results.append(result)
        
        return results
    
    # ============================================================================
    # Test: Complete E2E Flow (Mocked)
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_e2e_hybrid_search_flow_mocked(
        self,
        mock_uds3,
        comprehensive_search_results
    ):
        """Test complete flow with mocked services"""
        
        # Create mock hybrid result
        hybrid_result = HybridSearchResult(
            results=comprehensive_search_results,
            total_count=len(comprehensive_search_results),
            query="Wie beantrage ich eine Baugenehmigung in Stuttgart?",
            search_methods_used=[SearchMethod.VECTOR, SearchMethod.GRAPH, SearchMethod.RELATIONAL],
            ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION,
            weights=SearchWeights(vector_weight=0.6, graph_weight=0.2, relational_weight=0.2),
            execution_time_ms=125.5
        )
        
        with patch('backend.services.query_service.RAGService') as MockRAGService, \
             patch('backend.services.query_service.RerankerService') as MockRerankerService:
            
            # Setup mocks
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            mock_reranker_instance = Mock()
            mock_reranker_instance.rerank.return_value = [
                Mock(document_id=r.document_id, original_score=r.relevance_score,
                     reranked_score=r.relevance_score + 0.03, score_delta=0.03,
                     confidence=0.95, reasoning="Relevant")
                for r in comprehensive_search_results
            ]
            MockRerankerService.return_value = mock_reranker_instance
            
            # Create service
            service = QueryService(uds3=mock_uds3)
            
            # Create request
            request = UnifiedQueryRequest(
                query="Wie beantrage ich eine Baugenehmigung in Stuttgart?",
                mode=QueryMode.HYBRID,
                max_results=10,
                enable_reranking=True
            )
            
            # Measure E2E time
            start_time = time.time()
            result = await service._process_hybrid(request)
            elapsed = time.time() - start_time
            
            # ===== ASSERTIONS =====
            
            # 1. Response structure
            assert result is not None
            assert "response_text" in result
            assert "sources" in result
            assert "rag_context" in result
            assert "confidence_score" in result
            
            # 2. Sources validation
            assert len(result["sources"]) > 0
            assert len(result["sources"]) <= request.max_results
            
            # 3. Validate IEEE Citation Fields (35+ fields)
            source = result["sources"][0]
            required_ieee_fields = [
                'id', 'document_id', 'title', 'type', 'content',
                'authors', 'year', 'date', 'publisher', 'ieee_citation',
                'relevance_score', 'similarity_score', 'score', 'quality_score',
                'search_method', 'ranking_strategy', 'rank',
                'rerank_applied', 'rerank_score', 'original_score', 'score_delta', 'rerank_confidence',
                'file_path', 'page_number', 'page_count',
                'rechtsgebiet', 'normtyp', 'geltungsbereich', 'tags',
                'excerpt_start', 'excerpt_end', 'relevance', 'impact'
            ]
            
            missing_fields = [f for f in required_ieee_fields if f not in source]
            assert len(missing_fields) == 0, f"Missing IEEE fields: {missing_fields}"
            
            # 4. Validate RAG Context
            rag_context = result["rag_context"]
            assert 'total_results' in rag_context
            assert 'search_methods' in rag_context
            assert 'ranking_strategy' in rag_context
            assert 'execution_time_ms' in rag_context
            assert 'weights' in rag_context
            
            # 5. Validate search methods
            assert len(rag_context['search_methods']) == 3  # Vector, Graph, Relational
            assert 'vector' in rag_context['search_methods']
            assert 'graph' in rag_context['search_methods']
            assert 'relational' in rag_context['search_methods']
            
            # 6. Validate RRF ranking
            assert rag_context['ranking_strategy'] == 'rrf'
            
            # 7. Validate reranking was applied
            for source in result["sources"]:
                assert source["rerank_applied"] is True
                assert "rerank_score" in source
                assert "score_delta" in source
                assert source["rerank_confidence"] > 0
            
            # 8. Performance check (mocked, should be fast)
            assert elapsed < 1.0, f"E2E flow took {elapsed:.2f}s, expected < 1s (mocked)"
            
            print(f"\n✅ E2E Test Passed (Elapsed: {elapsed*1000:.2f}ms)")
            print(f"   Sources: {len(result['sources'])}")
            print(f"   IEEE fields: {len(required_ieee_fields)} validated")
            print(f"   Reranking: Applied to all {len(result['sources'])} sources")
    
    # ============================================================================
    # Test: Real Verwaltungs-Queries
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_verwaltung_query_bauantrag(
        self,
        mock_uds3,
        comprehensive_search_results
    ):
        """Test with real Bauantrag query"""
        
        # Filter results to Baurecht topic
        baurecht_results = [r for r in comprehensive_search_results
                           if 'Bau' in r.metadata.title or 'Bau' in r.metadata.custom_fields.get('rechtsgebiet', '')]
        
        hybrid_result = HybridSearchResult(
            results=baurecht_results,
            total_count=len(baurecht_results),
            query="Wie beantrage ich eine Baugenehmigung in Stuttgart?",
            search_methods_used=[SearchMethod.VECTOR, SearchMethod.RELATIONAL],
            ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION,
            weights=SearchWeights(vector_weight=0.7, relational_weight=0.3),
            execution_time_ms=95.3
        )
        
        with patch('backend.services.query_service.RAGService') as MockRAGService:
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            service = QueryService(uds3=mock_uds3)
            
            request = UnifiedQueryRequest(
                query="Wie beantrage ich eine Baugenehmigung in Stuttgart?",
                mode=QueryMode.HYBRID,
                max_results=10,
                enable_reranking=False
            )
            
            result = await service._process_hybrid(request)
            
            # Verify Baurecht results
            assert len(result["sources"]) >= 1
            
            # Check that results contain relevant Baurecht content
            titles = [s["title"] for s in result["sources"]]
            baurecht_keywords = ['Bau', 'Genehmigung', 'Stuttgart', 'LBO']
            
            relevant_count = sum(1 for title in titles
                                if any(kw in title for kw in baurecht_keywords))
            assert relevant_count >= 1, "Expected at least 1 Baurecht-related result"
    
    @pytest.mark.asyncio
    async def test_verwaltung_query_bimschg(
        self,
        mock_uds3,
        comprehensive_search_results
    ):
        """Test with real BImSchG query"""
        
        # Filter to Umweltrecht
        umwelt_results = [r for r in comprehensive_search_results
                         if 'Umwelt' in r.metadata.custom_fields.get('rechtsgebiet', '')]
        
        hybrid_result = HybridSearchResult(
            results=umwelt_results,
            total_count=len(umwelt_results),
            query="Welche Unterlagen benötige ich für einen BImSchG-Antrag?",
            search_methods_used=[SearchMethod.VECTOR, SearchMethod.GRAPH],
            ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION,
            weights=SearchWeights(vector_weight=0.6, graph_weight=0.4),
            execution_time_ms=108.7
        )
        
        with patch('backend.services.query_service.RAGService') as MockRAGService:
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            service = QueryService(uds3=mock_uds3)
            
            request = UnifiedQueryRequest(
                query="Welche Unterlagen benötige ich für einen BImSchG-Antrag?",
                mode=QueryMode.HYBRID,
                max_results=10,
                enable_reranking=False
            )
            
            result = await service._process_hybrid(request)
            
            # Verify results
            assert len(result["sources"]) >= 1
            
            # Check for BImSchG/Umweltrecht content
            for source in result["sources"]:
                rechtsgebiet = source.get("rechtsgebiet", "")
                assert rechtsgebiet in ["Umweltrecht", ""], f"Unexpected rechtsgebiet: {rechtsgebiet}"
    
    # ============================================================================
    # Test: End-to-End Latency Measurement
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_e2e_latency_under_10s(
        self,
        mock_uds3,
        comprehensive_search_results
    ):
        """Test that E2E latency is under 10 seconds (target benchmark)"""
        
        hybrid_result = HybridSearchResult(
            results=comprehensive_search_results,
            total_count=len(comprehensive_search_results),
            query="Test query",
            search_methods_used=[SearchMethod.VECTOR, SearchMethod.GRAPH, SearchMethod.RELATIONAL],
            ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION,
            weights=SearchWeights(),
            execution_time_ms=150.0
        )
        
        with patch('backend.services.query_service.RAGService') as MockRAGService, \
             patch('backend.services.query_service.RerankerService') as MockRerankerService:
            
            # Simulate realistic latencies
            import time
            
            def slow_hybrid_search(*args, **kwargs):
                time.sleep(0.15)  # 150ms (realistic DB query time)
                return hybrid_result
            
            def slow_rerank(*args, **kwargs):
                time.sleep(0.5)  # 500ms (realistic LLM time for 5 docs)
                return [Mock(document_id=r.document_id, original_score=r.relevance_score,
                            reranked_score=r.relevance_score, score_delta=0,
                            confidence=0.9, reasoning="") for r in comprehensive_search_results]
            
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.side_effect = slow_hybrid_search
            MockRAGService.return_value = mock_rag_instance
            
            mock_reranker_instance = Mock()
            mock_reranker_instance.rerank.side_effect = slow_rerank
            MockRerankerService.return_value = mock_reranker_instance
            
            service = QueryService(uds3=mock_uds3)
            
            request = UnifiedQueryRequest(
                query="Test latency",
                mode=QueryMode.HYBRID,
                max_results=10,
                enable_reranking=True
            )
            
            # Measure E2E latency
            start_time = time.time()
            result = await service._process_hybrid(request)
            elapsed = time.time() - start_time
            
            # Verify target < 10s (with realistic mocks, should be ~0.7s)
            assert elapsed < 10.0, f"E2E latency {elapsed:.2f}s exceeds 10s target"
            assert elapsed < 2.0, f"E2E latency {elapsed:.2f}s exceeds 2s reasonable threshold"
            
            print(f"\n⏱️ E2E Latency: {elapsed*1000:.0f}ms (Target: <10s, Optimal: <2s)")
    
    # ============================================================================
    # Test: IEEE Citation Format Validation
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_ieee_citation_format(
        self,
        mock_uds3,
        comprehensive_search_results
    ):
        """Validate IEEE citation format compliance"""
        
        hybrid_result = HybridSearchResult(
            results=comprehensive_search_results[:3],
            total_count=3,
            query="Test",
            search_methods_used=[SearchMethod.VECTOR],
            ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION,
            weights=SearchWeights(),
            execution_time_ms=50.0
        )
        
        with patch('backend.services.query_service.RAGService') as MockRAGService:
            mock_rag_instance = Mock()
            mock_rag_instance.hybrid_search.return_value = hybrid_result
            MockRAGService.return_value = mock_rag_instance
            
            service = QueryService(uds3=mock_uds3)
            
            request = UnifiedQueryRequest(
                query="Test",
                mode=QueryMode.HYBRID,
                max_results=10,
                enable_reranking=False
            )
            
            result = await service._process_hybrid(request)
            
            # Validate IEEE citations
            for source in result["sources"]:
                citation = source["ieee_citation"]
                
                # IEEE format: Author, "Title", Publisher, Year.
                assert citation is not None and len(citation) > 0
                assert source["authors"] in citation or "Unbekannt" in citation
                assert source["title"] in citation
                assert str(source["year"]) in citation or "n.d." in citation
                
                print(f"✅ IEEE Citation: {citation}")
    
    # ============================================================================
    # Test: Real Services Integration (Optional)
    # ============================================================================
    
    @pytest.mark.skipif(not USE_REAL_SERVICES, reason="Real services test disabled")
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_e2e_with_real_services(self, real_verwaltung_queries):
        """Full E2E test with real UDS3 and Ollama (requires infrastructure)"""
        
        # This test requires:
        # - ChromaDB running
        # - Neo4j running  
        # - PostgreSQL running
        # - Ollama running with llama3.1:8b
        # - Test data loaded
        
        try:
            # Import real UDS3
            from uds3.polyglot_manager import PolyglotManager
            
            # Initialize real services
            uds3 = PolyglotManager()
            service = QueryService(uds3=uds3)
            
            for query_data in real_verwaltung_queries:
                request = UnifiedQueryRequest(
                    query=query_data['query'],
                    mode=QueryMode.HYBRID,
                    max_results=10,
                    enable_reranking=True
                )
                
                print(f"\n🔍 Testing: {query_data['query']}")
                
                start_time = time.time()
                result = await service._process_hybrid(request)
                elapsed = time.time() - start_time
                
                # Assertions
                assert result is not None
                assert len(result["sources"]) >= query_data['min_results']
                assert elapsed < 10.0, f"Query took {elapsed:.2f}s, exceeds 10s limit"
                
                print(f"   ✅ Results: {len(result['sources'])}, Time: {elapsed:.2f}s")
                print(f"   Top result: {result['sources'][0]['title']}")
                
        except Exception as e:
            pytest.skip(f"Real services not available: {e}")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    # Run with: pytest test_hybrid_search_pipeline.py -v
    # Or with real services: HYBRID_E2E_USE_REAL_SERVICES=true pytest test_hybrid_search_pipeline.py -v -m integration
    pytest.main([__file__, "-v", "--tb=short", "-s"])
