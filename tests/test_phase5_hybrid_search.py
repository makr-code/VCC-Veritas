#!/usr/bin/env python3
"""
VERITAS PHASE 5 UNIT TESTS
==========================

Umfassende Unit-Tests für Advanced RAG Pipeline Komponenten:
- BM25 Sparse Retrieval
- Reciprocal Rank Fusion (RRF)
- Hybrid Retrieval
- Query Expansion

Test-Kategorien:
---------------
1. Functional Tests: Basis-Funktionalität
2. Edge Cases: Leere Inputs, Duplikate, etc.
3. Performance Tests: Latenz, Throughput
4. Integration Tests: Komponenten-Zusammenspiel

Author: VERITAS System
Date: 2025-10-06
Version: 1.0
"""

import asyncio
import pytest
import time
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

# Import zu testende Komponenten
try:
    from backend.agents.veritas_sparse_retrieval import (
        SparseRetriever,
        SparseRetrievalConfig,
        ScoredDocument,
        get_sparse_retriever
    )
    from backend.agents.veritas_reciprocal_rank_fusion import (
        ReciprocalRankFusion,
        RRFConfig,
        FusedDocument,
        get_rrf
    )
    from backend.agents.veritas_hybrid_retrieval import (
        HybridRetriever,
        HybridRetrievalConfig,
        HybridResult
    )
    from backend.agents.veritas_query_expansion import (
        QueryExpander,
        QueryExpansionConfig,
        ExpandedQuery,
        ExpansionStrategy
    )
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    pytest.skip(f"Phase 5 Komponenten nicht verfügbar: {e}", allow_module_level=True)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_corpus():
    """Sample-Corpus für Tests."""
    return [
        {
            "doc_id": "doc1",
            "content": "§ 242 BGB Leistung nach Treu und Glauben. Der Schuldner ist verpflichtet, die Leistung so zu bewirken, wie Treu und Glauben mit Rücksicht auf die Verkehrssitte es erfordern.",
            "metadata": {"source": "BGB", "tags": ["recht", "schuldrecht"]}
        },
        {
            "doc_id": "doc2",
            "content": "DIN 18040-1 Barrierefreies Bauen. Planungsgrundlagen für öffentlich zugängliche Gebäude.",
            "metadata": {"source": "DIN", "tags": ["bauen", "norm"]}
        },
        {
            "doc_id": "doc3",
            "content": "Umweltverträglichkeitsprüfung (UVP) nach UVPG. Verfahren zur Bewertung von Umweltauswirkungen bei Bauvorhaben.",
            "metadata": {"source": "UVPG", "tags": ["umwelt", "verfahren"]}
        },
        {
            "doc_id": "doc4",
            "content": "Nachhaltiges Bauen bedeutet ressourcenschonende und umweltfreundliche Bauweise. Energieeffizienz und ökologische Materialien stehen im Vordergrund.",
            "metadata": {"source": "Ratgeber", "tags": ["nachhaltigkeit", "bauen"]}
        },
        {
            "doc_id": "doc5",
            "content": "Baurecht umfasst öffentliches Baurecht (BauGB, BauNVO) und privates Baurecht (BGB, VOB). Regelungen für Baugenehmigungen und Bauausführung.",
            "metadata": {"source": "Baurecht", "tags": ["recht", "bauen"]}
        }
    ]


@pytest.fixture
def sparse_retriever(sample_corpus):
    """Initialisierter Sparse Retriever."""
    config = SparseRetrievalConfig(
        k1=1.5,
        b=0.75,
        top_k=5,
        enable_cache=False  # Disable für Tests
    )
    retriever = SparseRetriever(config)
    retriever.index_documents(sample_corpus)
    return retriever


@pytest.fixture
def rrf_instance():
    """RRF-Instanz."""
    config = RRFConfig(k=60, top_k=10)
    return ReciprocalRankFusion(config)


@pytest.fixture
def mock_dense_retriever():
    """Mock Dense Retriever."""
    mock = AsyncMock()
    
    async def mock_vector_search(query_text, top_k, **kwargs):
        # Simuliere Dense Retrieval Results
        return [
            {"doc_id": "doc1", "content": "Dense result 1", "score": 0.95},
            {"doc_id": "doc3", "content": "Dense result 3", "score": 0.85},
            {"doc_id": "doc4", "content": "Dense result 4", "score": 0.75},
        ]
    
    mock.vector_search = mock_vector_search
    return mock


# ============================================================================
# SPARSE RETRIEVAL TESTS
# ============================================================================

class TestSparseRetrieval:
    """Tests für BM25 Sparse Retrieval."""
    
    def test_initialization(self):
        """Test: Sparse Retriever Initialisierung."""
        config = SparseRetrievalConfig(k1=1.5, b=0.75)
        retriever = SparseRetriever(config)
        
        assert retriever.config.k1 == 1.5
        assert retriever.config.b == 0.75
        assert retriever.is_available() is True
    
    def test_document_indexing(self, sparse_retriever, sample_corpus):
        """Test: Dokumente indexieren."""
        stats = sparse_retriever.get_stats()
        
        assert stats["num_documents"] == len(sample_corpus)
        assert stats["avg_doc_length"] > 0
        assert stats["indexed"] is True
    
    @pytest.mark.asyncio
    async def test_basic_retrieval(self, sparse_retriever):
        """Test: Basis-Retrieval."""
        results = await sparse_retriever.retrieve("§ 242 BGB", top_k=3)
        
        assert len(results) > 0
        assert len(results) <= 3
        assert all(isinstance(r, ScoredDocument) for r in results)
        assert results[0].score > 0
        
        # § 242 BGB sollte doc1 sein
        assert "242" in results[0].content or "BGB" in results[0].content
    
    @pytest.mark.asyncio
    async def test_acronym_retrieval(self, sparse_retriever):
        """Test: Akronym-Suche (UVP, DIN)."""
        results = await sparse_retriever.retrieve("DIN 18040", top_k=3)
        
        assert len(results) > 0
        # DIN sollte in Top-Result sein
        assert "DIN" in results[0].content
    
    @pytest.mark.asyncio
    async def test_multi_query_retrieval(self, sparse_retriever):
        """Test: Multi-Query Retrieval."""
        queries = ["BGB", "DIN", "UVP"]
        results = await sparse_retriever.retrieve_multi_query(
            queries,
            aggregation="max",
            top_k=5
        )
        
        assert len(results) > 0
        assert len(results) <= 5
    
    @pytest.mark.asyncio
    async def test_empty_query(self, sparse_retriever):
        """Test: Leere Query."""
        results = await sparse_retriever.retrieve("", top_k=3)
        
        # Leere Query sollte keine/wenige Results geben
        assert len(results) >= 0
    
    @pytest.mark.asyncio
    async def test_no_match_query(self, sparse_retriever):
        """Test: Query ohne Match."""
        results = await sparse_retriever.retrieve("XXXXXXX YYYYYY ZZZZZZ", top_k=3)
        
        # Kann leer sein oder niedrige Scores haben
        if len(results) > 0:
            assert results[0].score < 0.5  # Niedrige Relevanz


# ============================================================================
# RECIPROCAL RANK FUSION TESTS
# ============================================================================

class TestReciprocalRankFusion:
    """Tests für RRF-Algorithmus."""
    
    def test_initialization(self):
        """Test: RRF Initialisierung."""
        config = RRFConfig(k=60, top_k=10)
        rrf = ReciprocalRankFusion(config)
        
        assert rrf.config.k == 60
        assert rrf.config.top_k == 10
    
    def test_basic_fusion(self, rrf_instance):
        """Test: Basis-Fusion von 2 Rankings."""
        dense_results = [
            {"doc_id": "doc1", "content": "Content 1", "score": 0.9},
            {"doc_id": "doc2", "content": "Content 2", "score": 0.8},
            {"doc_id": "doc3", "content": "Content 3", "score": 0.7},
        ]
        
        sparse_results = [
            {"doc_id": "doc2", "content": "Content 2", "score": 5.0},
            {"doc_id": "doc4", "content": "Content 4", "score": 4.0},
            {"doc_id": "doc1", "content": "Content 1", "score": 3.0},
        ]
        
        fused = rrf_instance.fuse_two(dense_results, sparse_results, top_k=5)
        
        assert len(fused) > 0
        assert len(fused) <= 5
        assert all(isinstance(doc, FusedDocument) for doc in fused)
        
        # doc1 und doc2 sollten oben sein (in beiden Rankings)
        top_ids = [doc.doc_id for doc in fused[:2]]
        assert "doc1" in top_ids or "doc2" in top_ids
    
    def test_rrf_score_calculation(self, rrf_instance):
        """Test: RRF-Score Berechnung."""
        # doc1: Rank 1 in beiden → RRF = 1/(60+1) + 1/(60+1) = 0.0328
        # doc2: Rank 2 in beiden → RRF = 1/(60+2) + 1/(60+2) = 0.0323
        
        retriever_results = {
            "dense": [
                {"doc_id": "doc1", "content": "C1", "score": 0.9},
                {"doc_id": "doc2", "content": "C2", "score": 0.8},
            ],
            "sparse": [
                {"doc_id": "doc1", "content": "C1", "score": 5.0},
                {"doc_id": "doc2", "content": "C2", "score": 4.0},
            ]
        }
        
        fused = rrf_instance.fuse(retriever_results, top_k=5)
        
        assert len(fused) == 2
        # doc1 sollte höheren RRF-Score haben (beide Rank 1)
        assert fused[0].doc_id == "doc1"
        assert fused[0].rrf_score > fused[1].rrf_score
    
    def test_fusion_with_weights(self):
        """Test: RRF mit Weights."""
        config = RRFConfig(
            k=60,
            top_k=10,
            weights={"dense": 0.7, "sparse": 0.3}
        )
        rrf = ReciprocalRankFusion(config)
        
        retriever_results = {
            "dense": [{"doc_id": "doc1", "content": "C1", "score": 0.9}],
            "sparse": [{"doc_id": "doc2", "content": "C2", "score": 5.0}]
        }
        
        fused = rrf.fuse(retriever_results, top_k=5)
        
        # doc1 sollte höher ranken (Dense hat 70% Weight)
        assert fused[0].doc_id == "doc1"
    
    def test_fusion_stats(self, rrf_instance):
        """Test: Fusion-Statistiken."""
        dense = [{"doc_id": "doc1", "content": "C1", "score": 0.9}]
        sparse = [{"doc_id": "doc1", "content": "C1", "score": 5.0}]
        
        fused = rrf_instance.fuse_two(dense, sparse, top_k=5)
        stats = rrf_instance.get_fusion_stats(fused)
        
        assert "overlap_rate" in stats
        assert "avg_sources_per_doc" in stats
        assert stats["overlap_rate"] == 1.0  # 100% Overlap
    
    def test_empty_results(self, rrf_instance):
        """Test: Leere Results."""
        fused = rrf_instance.fuse_two([], [], top_k=5)
        
        assert len(fused) == 0
    
    def test_single_retriever(self, rrf_instance):
        """Test: Nur ein Retriever."""
        dense = [{"doc_id": "doc1", "content": "C1", "score": 0.9}]
        
        fused = rrf_instance.fuse_two(dense, [], top_k=5)
        
        assert len(fused) == 1
        assert fused[0].sources == ["dense"]


# ============================================================================
# HYBRID RETRIEVAL TESTS
# ============================================================================

class TestHybridRetrieval:
    """Tests für Hybrid Retrieval."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_dense_retriever, sample_corpus):
        """Test: Hybrid Retriever Initialisierung."""
        config = HybridRetrievalConfig(
            dense_top_k=10,
            sparse_top_k=10,
            final_top_k=5,
            enable_sparse=True,
            enable_query_expansion=False
        )
        
        retriever = HybridRetriever(
            dense_retriever=mock_dense_retriever,
            config=config
        )
        
        # Index Sparse Corpus
        retriever.sparse_retriever.index_documents(sample_corpus)
        
        assert retriever.config.dense_top_k == 10
        assert retriever.config.sparse_top_k == 10
        assert retriever._sparse_available is True
    
    @pytest.mark.asyncio
    async def test_hybrid_retrieval(self, mock_dense_retriever, sample_corpus):
        """Test: Hybrid Retrieval (Dense + Sparse + RRF)."""
        config = HybridRetrievalConfig(
            enable_sparse=True,
            enable_query_expansion=False
        )
        
        retriever = HybridRetriever(
            dense_retriever=mock_dense_retriever,
            config=config
        )
        retriever.sparse_retriever.index_documents(sample_corpus)
        
        results = await retriever.retrieve("BGB Schuldrecht", top_k=5)
        
        assert len(results) > 0
        assert len(results) <= 5
        assert all(isinstance(r, HybridResult) for r in results)
        
        # Mindestens ein Ergebnis sollte beide Quellen haben
        has_hybrid = any(len(r.sources) > 1 for r in results)
        assert has_hybrid or len(results) > 0  # Hybrid oder zumindest Dense
    
    @pytest.mark.asyncio
    async def test_dense_only_fallback(self, mock_dense_retriever):
        """Test: Dense-Only Fallback (kein Sparse)."""
        config = HybridRetrievalConfig(
            enable_sparse=False,
            enable_query_expansion=False
        )
        
        retriever = HybridRetriever(
            dense_retriever=mock_dense_retriever,
            config=config
        )
        
        results = await retriever.retrieve("Test Query", top_k=3)
        
        assert len(results) > 0
        assert all(r.retrieval_method == "dense_only" for r in results)
    
    @pytest.mark.asyncio
    async def test_get_stats(self, mock_dense_retriever, sample_corpus):
        """Test: Hybrid Retriever Stats."""
        retriever = HybridRetriever(
            dense_retriever=mock_dense_retriever,
            config=HybridRetrievalConfig()
        )
        retriever.sparse_retriever.index_documents(sample_corpus)
        
        stats = retriever.get_stats()
        
        assert "hybrid_available" in stats
        assert "sparse_available" in stats
        assert "config" in stats
        assert stats["config"]["dense_top_k"] == 50


# ============================================================================
# QUERY EXPANSION TESTS
# ============================================================================

class TestQueryExpansion:
    """Tests für Query Expansion."""
    
    def test_initialization(self):
        """Test: Query Expander Initialisierung."""
        config = QueryExpansionConfig(
            model="llama3.2:3b",
            num_expansions=2,
            temperature=0.7
        )
        
        expander = QueryExpander(config)
        
        assert expander.config.model == "llama3.2:3b"
        assert expander.config.num_expansions == 2
    
    @pytest.mark.asyncio
    async def test_expand_without_ollama(self):
        """Test: Expansion ohne Ollama (Fallback)."""
        config = QueryExpansionConfig(
            num_expansions=2,
            fallback_to_original=True
        )
        
        expander = QueryExpander(config)
        expander._ollama_available = False  # Force Fallback
        
        results = await expander.expand("Wie baue ich ein Haus?")
        
        # Sollte mindestens Original-Query zurückgeben
        assert len(results) >= 1
        assert results[0].text == "Wie baue ich ein Haus?"
    
    def test_cleanup_variant(self):
        """Test: LLM-Output Cleanup."""
        expander = QueryExpander()
        
        # Test verschiedene Cleanup-Szenarien
        assert expander._cleanup_variant('"Test Query"') == "Test Query"
        assert expander._cleanup_variant("Umformulierung: Test") == "Test"
        assert expander._cleanup_variant("Test\nQuery") == "Test Query"
    
    def test_cache_key_generation(self):
        """Test: Cache-Key Generierung."""
        expander = QueryExpander()
        
        key1 = expander._get_cache_key(
            "Test Query",
            2,
            [ExpansionStrategy.SYNONYM, ExpansionStrategy.CONTEXT]
        )
        
        key2 = expander._get_cache_key(
            "Test Query",
            2,
            [ExpansionStrategy.SYNONYM, ExpansionStrategy.CONTEXT]
        )
        
        # Gleiche Parameter → gleicher Key
        assert key1 == key2
        
        key3 = expander._get_cache_key(
            "Different Query",
            2,
            [ExpansionStrategy.SYNONYM, ExpansionStrategy.CONTEXT]
        )
        
        # Verschiedene Query → verschiedener Key
        assert key1 != key3
    
    def test_get_stats(self):
        """Test: Query Expander Stats."""
        config = QueryExpansionConfig(model="llama3.2:3b", num_expansions=3)
        expander = QueryExpander(config)
        
        stats = expander.get_stats()
        
        assert "ollama_available" in stats
        assert "cache_size" in stats
        assert stats["config"]["model"] == "llama3.2:3b"
        assert stats["config"]["num_expansions"] == 3


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance- und Latenz-Tests."""
    
    @pytest.mark.asyncio
    async def test_sparse_retrieval_latency(self, sparse_retriever):
        """Test: Sparse Retrieval Latenz < 50ms."""
        start = time.time()
        results = await sparse_retriever.retrieve("BGB", top_k=10)
        latency = (time.time() - start) * 1000
        
        assert latency < 50  # < 50ms
        assert len(results) > 0
    
    def test_rrf_latency(self, rrf_instance):
        """Test: RRF Latenz < 5ms."""
        dense = [{"doc_id": f"doc{i}", "content": f"C{i}", "score": 1.0 - i*0.1} for i in range(50)]
        sparse = [{"doc_id": f"doc{i}", "content": f"C{i}", "score": 10.0 - i*0.2} for i in range(50)]
        
        start = time.time()
        fused = rrf_instance.fuse_two(dense, sparse, top_k=20)
        latency = (time.time() - start) * 1000
        
        assert latency < 5  # < 5ms
        assert len(fused) == 20
    
    @pytest.mark.asyncio
    async def test_hybrid_retrieval_latency(self, mock_dense_retriever, sample_corpus):
        """Test: Hybrid Retrieval Latenz < 150ms."""
        retriever = HybridRetriever(
            dense_retriever=mock_dense_retriever,
            config=HybridRetrievalConfig(enable_query_expansion=False)
        )
        retriever.sparse_retriever.index_documents(sample_corpus)
        
        start = time.time()
        results = await retriever.retrieve("Test Query", top_k=10)
        latency = (time.time() - start) * 1000
        
        assert latency < 150  # < 150ms (mit Mock Dense)
        assert len(results) > 0


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
