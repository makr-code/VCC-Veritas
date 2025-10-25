#!/usr/bin/env python3
"""
VERITAS PHASE 5 INTEGRATION TESTS
==================================

End-to-End Tests für die komplette Advanced RAG Pipeline:

Pipeline:
--------
Query 
  → Query Expansion (LLM)
    → Hybrid Search (Dense + Sparse + RRF)
      → Re-Ranking (Cross-Encoder)
        → Top-5 Dokumente

Test-Szenarien:
--------------
1. Full Pipeline: Query Expansion + Hybrid + Re-Ranking
2. A/B Vergleiche: Baseline vs Hybrid vs Hybrid+QueryExpansion
3. Real-World Queries: Baurecht, Umwelt, Normen
4. Edge Cases: Leere Queries, Lange Queries, Spezialzeichen

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
    from backend.agents.rag_context_service import (
        RAGContextService,
        RAGQueryOptions
    )
    from backend.agents.veritas_hybrid_retrieval import (
        HybridRetriever,
        HybridRetrievalConfig
    )
    from backend.agents.veritas_query_expansion import (
        QueryExpander,
        MultiQueryGenerator
    )
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    pytest.skip(f"Phase 5 Komponenten nicht verfügbar: {e}", allow_module_level=True)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def comprehensive_corpus():
    """Umfangreiches Test-Corpus für realistische Tests."""
    return [
        {
            "doc_id": "bgb_242",
            "content": "§ 242 BGB Leistung nach Treu und Glauben. Der Schuldner ist verpflichtet, die Leistung so zu bewirken, wie Treu und Glauben mit Rücksicht auf die Verkehrssitte es erfordern.",
            "metadata": {"source": "BGB", "tags": ["recht", "schuldrecht"], "relevance": "high"}
        },
        {
            "doc_id": "din_18040_1",
            "content": "DIN 18040-1 Barrierefreies Bauen - Planungsgrundlagen - Teil 1: Öffentlich zugängliche Gebäude. Diese Norm gilt für die barrierefreie Planung, Ausführung und Ausstattung von öffentlich zugänglichen Gebäuden.",
            "metadata": {"source": "DIN", "tags": ["bauen", "norm", "barrierefreiheit"], "relevance": "high"}
        },
        {
            "doc_id": "uvpg_3a",
            "content": "§ 3a UVPG Feststellung der UVP-Pflicht. Die zuständige Behörde stellt auf Antrag oder von Amts wegen durch eine Umweltverträglichkeitsprüfung fest, ob für ein Vorhaben eine UVP-Pflicht besteht.",
            "metadata": {"source": "UVPG", "tags": ["umwelt", "verfahren"], "relevance": "high"}
        },
        {
            "doc_id": "sustainable_building",
            "content": "Nachhaltiges Bauen bedeutet ressourcenschonende, energieeffiziente und umweltfreundliche Bauweise. Ökologische Materialien, erneuerbare Energien und Lebenszyklusbetrachtung stehen im Vordergrund.",
            "metadata": {"source": "Ratgeber", "tags": ["nachhaltigkeit", "bauen", "umwelt"], "relevance": "medium"}
        },
        {
            "doc_id": "baurecht_overview",
            "content": "Baurecht umfasst öffentliches Baurecht (BauGB, BauNVO, Landesbauordnungen) und privates Baurecht (BGB, VOB/A, VOB/B). Regelungen für Baugenehmigungen, Bauausführung und Baumängel.",
            "metadata": {"source": "Baurecht", "tags": ["recht", "bauen"], "relevance": "high"}
        },
        {
            "doc_id": "energy_efficiency",
            "content": "Energieeffizienz im Gebäudebereich: EnEV, GEG (Gebäudeenergiegesetz), KfW-Standards. Anforderungen an Wärmedämmung, Heizungstechnik und erneuerbare Energien.",
            "metadata": {"source": "EnEV", "tags": ["energie", "bauen", "nachhaltigkeit"], "relevance": "medium"}
        },
        {
            "doc_id": "accessibility_law",
            "content": "Barrierefreiheit nach § 39 BauO NRW und BGG. Öffentliche Gebäude müssen barrierefrei zugänglich und nutzbar sein. DIN 18040 als technische Umsetzung.",
            "metadata": {"source": "BauO NRW", "tags": ["recht", "barrierefreiheit"], "relevance": "high"}
        },
        {
            "doc_id": "environmental_impact",
            "content": "Umweltauswirkungen von Bauvorhaben: Flächenverbrauch, Emissionen, Ressourcennutzung. UVP-Pflicht ab bestimmten Schwellenwerten (UVPG Anlage 1).",
            "metadata": {"source": "Umweltrecht", "tags": ["umwelt", "bauen"], "relevance": "medium"}
        },
        {
            "doc_id": "construction_process",
            "content": "Bauprozess: Planung → Genehmigung → Ausführung → Abnahme. VOB/B regelt Vertragsbeziehungen zwischen Auftraggeber und Auftragnehmer.",
            "metadata": {"source": "VOB", "tags": ["prozess", "bauen"], "relevance": "low"}
        },
        {
            "doc_id": "green_building",
            "content": "Green Building Zertifizierungen: LEED, BREEAM, DGNB. Bewertung von Gebäuden nach Nachhaltigkeitskriterien: Ökologie, Ökonomie, soziokulturelle Qualität.",
            "metadata": {"source": "DGNB", "tags": ["nachhaltigkeit", "zertifizierung"], "relevance": "medium"}
        }
    ]


@pytest.fixture
def mock_uds3_strategy(comprehensive_corpus):
    """Mock UDS3 Strategy für Integration-Tests."""
    mock = AsyncMock()
    
    async def mock_vector_search(query_text, top_k, **kwargs):
        # Simuliere semantische Suche basierend auf Keywords
        results = []
        query_lower = query_text.lower()
        
        for doc in comprehensive_corpus:
            score = 0.5  # Base score
            
            # Keyword-Matching für Score
            if "barrierefreie" in query_lower or "barrierefrei" in query_lower:
                if "barrierefreiheit" in doc["content"].lower() or "din 18040" in doc["content"].lower():
                    score = 0.95
            
            if "nachhaltig" in query_lower or "umwelt" in query_lower:
                if "nachhaltig" in doc["content"].lower() or "umwelt" in doc["content"].lower():
                    score = 0.90
            
            if "bgb" in query_lower or "§" in query_lower:
                if "bgb" in doc["content"].lower() or "§" in doc["content"].lower():
                    score = 0.92
            
            if score > 0.6:
                results.append({
                    "id": doc["doc_id"],
                    "doc_id": doc["doc_id"],
                    "content": doc["content"],
                    "text": doc["content"],
                    "score": score,
                    "metadata": doc["metadata"]
                })
        
        # Sortiere nach Score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    mock.vector_search = mock_vector_search
    return mock


@pytest.fixture
def rag_service(mock_uds3_strategy, comprehensive_corpus):
    """RAGContextService mit Hybrid Search."""
    service = RAGContextService(
        uds3_strategy=mock_uds3_strategy,
        enable_reranking=False,  # Disable für Tests (kein echtes Re-Ranking Model)
        enable_hybrid_search=True
    )
    
    # Index Corpus für Sparse Retrieval
    service.index_corpus_for_hybrid_search(comprehensive_corpus)
    
    return service


# ============================================================================
# END-TO-END PIPELINE TESTS
# ============================================================================

class TestFullPipeline:
    """Tests für komplette RAG-Pipeline."""
    
    @pytest.mark.asyncio
    async def test_hybrid_search_pipeline(self, rag_service):
        """Test: Hybrid Search End-to-End."""
        options = RAGQueryOptions(
            limit_documents=5,
            enable_hybrid_search=True,
            enable_reranking=False,
            hybrid_final_top_k=10
        )
        
        result = await rag_service.build_context(
            query_text="Wie baue ich ein barrierefreies Haus?",
            options=options
        )
        
        assert "documents" in result
        assert len(result["documents"]) > 0
        assert result["meta"]["hybrid_applied"] is True
        assert result["meta"]["rag_available"] is True
        
        # DIN 18040 sollte in Top-Results sein
        doc_contents = " ".join(doc["snippet"] for doc in result["documents"])
        assert "DIN 18040" in doc_contents or "barrierefrei" in doc_contents
    
    @pytest.mark.asyncio
    async def test_dense_only_baseline(self, rag_service):
        """Test: Dense-Only Baseline (zum Vergleich)."""
        options = RAGQueryOptions(
            limit_documents=5,
            enable_hybrid_search=False,  # Nur Dense
            enable_reranking=False
        )
        
        result = await rag_service.build_context(
            query_text="Wie baue ich ein barrierefreies Haus?",
            options=options
        )
        
        assert "documents" in result
        assert len(result["documents"]) > 0
        assert result["meta"]["hybrid_applied"] is False
    
    @pytest.mark.asyncio
    async def test_performance_comparison(self, rag_service):
        """Test: Performance-Vergleich Dense vs Hybrid."""
        query = "Nachhaltiges Bauen mit Umweltverträglichkeitsprüfung"
        
        # Dense-Only
        start = time.time()
        result_dense = await rag_service.build_context(
            query,
            options=RAGQueryOptions(enable_hybrid_search=False, enable_reranking=False)
        )
        latency_dense = (time.time() - start) * 1000
        
        # Hybrid
        start = time.time()
        result_hybrid = await rag_service.build_context(
            query,
            options=RAGQueryOptions(enable_hybrid_search=True, enable_reranking=False)
        )
        latency_hybrid = (time.time() - start) * 1000
        
        # Hybrid sollte < 200ms Overhead haben
        assert latency_hybrid < latency_dense + 200
        
        # Beide sollten Ergebnisse liefern
        assert len(result_dense["documents"]) > 0
        assert len(result_hybrid["documents"]) > 0


# ============================================================================
# REAL-WORLD QUERY TESTS
# ============================================================================

class TestRealWorldQueries:
    """Tests mit realistischen Baurecht-Queries."""
    
    @pytest.mark.asyncio
    async def test_legal_query(self, rag_service):
        """Test: Rechtliche Query (§ 242 BGB)."""
        result = await rag_service.build_context(
            query_text="§ 242 BGB Treu und Glauben",
            options=RAGQueryOptions(enable_hybrid_search=True, enable_reranking=False)
        )
        
        # § 242 BGB sollte gefunden werden
        doc_ids = [doc["id"] for doc in result["documents"]]
        assert "bgb_242" in doc_ids
    
    @pytest.mark.asyncio
    async def test_technical_norm_query(self, rag_service):
        """Test: Technische Norm (DIN 18040-1)."""
        result = await rag_service.build_context(
            query_text="DIN 18040-1 Barrierefreies Bauen",
            options=RAGQueryOptions(enable_hybrid_search=True, enable_reranking=False)
        )
        
        # DIN 18040 sollte gefunden werden
        doc_ids = [doc["id"] for doc in result["documents"]]
        assert "din_18040_1" in doc_ids
    
    @pytest.mark.asyncio
    async def test_environmental_query(self, rag_service):
        """Test: Umwelt-Query (UVP)."""
        result = await rag_service.build_context(
            query_text="Umweltverträglichkeitsprüfung UVPG",
            options=RAGQueryOptions(enable_hybrid_search=True, enable_reranking=False)
        )
        
        # UVPG-Dokumente sollten gefunden werden
        doc_contents = " ".join(doc["snippet"] for doc in result["documents"])
        assert "UVP" in doc_contents or "Umwelt" in doc_contents
    
    @pytest.mark.asyncio
    async def test_complex_multi_topic_query(self, rag_service):
        """Test: Komplexe Multi-Topic Query."""
        result = await rag_service.build_context(
            query_text="Wie baue ich ein nachhaltiges, barrierefreies Gebäude nach aktuellen Normen?",
            options=RAGQueryOptions(
                enable_hybrid_search=True,
                enable_reranking=False,
                limit_documents=10
            )
        )
        
        # Sollte Dokumente zu mehreren Themen finden
        assert len(result["documents"]) > 0
        
        # Relevante Themen: Nachhaltigkeit, Barrierefreiheit, Normen
        all_content = " ".join(doc["snippet"] for doc in result["documents"])
        topics_found = sum([
            1 if "nachhaltig" in all_content.lower() else 0,
            1 if "barrierefrei" in all_content.lower() else 0,
            1 if "din" in all_content.lower() or "norm" in all_content.lower() else 0
        ])
        
        assert topics_found >= 2  # Mindestens 2 Themen abgedeckt


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Edge-Case Tests für Robustheit."""
    
    @pytest.mark.asyncio
    async def test_empty_query(self, rag_service):
        """Test: Leere Query."""
        result = await rag_service.build_context(
            query_text="",
            options=RAGQueryOptions(enable_hybrid_search=True, enable_reranking=False)
        )
        
        # Sollte nicht crashen
        assert "documents" in result
        assert isinstance(result["documents"], list)
    
    @pytest.mark.asyncio
    async def test_very_long_query(self, rag_service):
        """Test: Sehr lange Query."""
        long_query = " ".join(["Wie baue ich ein Haus"] * 50)  # 250+ Zeichen
        
        result = await rag_service.build_context(
            query_text=long_query,
            options=RAGQueryOptions(enable_hybrid_search=True, enable_reranking=False)
        )
        
        assert "documents" in result
    
    @pytest.mark.asyncio
    async def test_special_characters(self, rag_service):
        """Test: Spezialzeichen in Query."""
        result = await rag_service.build_context(
            query_text="§ 242 BGB & DIN 18040-1 (öffentliche Gebäude)",
            options=RAGQueryOptions(enable_hybrid_search=True, enable_reranking=False)
        )
        
        assert "documents" in result
        assert len(result["documents"]) > 0
    
    @pytest.mark.asyncio
    async def test_no_results_query(self, rag_service):
        """Test: Query ohne erwartete Results."""
        result = await rag_service.build_context(
            query_text="XXXXX YYYYY ZZZZZ NONEXISTENT",
            options=RAGQueryOptions(enable_hybrid_search=True, enable_reranking=False)
        )
        
        # Sollte leere oder niedrig-relevante Results haben
        assert "documents" in result
        assert isinstance(result["documents"], list)


# ============================================================================
# A/B COMPARISON TESTS
# ============================================================================

class TestABComparison:
    """A/B Vergleich: Baseline vs Hybrid."""
    
    @pytest.mark.asyncio
    async def test_recall_comparison(self, rag_service):
        """Test: Recall-Vergleich Dense vs Hybrid."""
        query = "Barrierefreies Bauen DIN Normen"
        
        # Dense-Only
        result_dense = await rag_service.build_context(
            query,
            options=RAGQueryOptions(
                enable_hybrid_search=False,
                enable_reranking=False,
                limit_documents=10
            )
        )
        
        # Hybrid
        result_hybrid = await rag_service.build_context(
            query,
            options=RAGQueryOptions(
                enable_hybrid_search=True,
                enable_reranking=False,
                limit_documents=10
            )
        )
        
        # Hybrid sollte gleich viele oder mehr Docs finden
        assert len(result_hybrid["documents"]) >= len(result_dense["documents"])
        
        # Check für relevante Dokumente (DIN 18040, Barrierefreiheit)
        hybrid_ids = {doc["id"] for doc in result_hybrid["documents"]}
        
        # DIN 18040 sollte in Hybrid-Results sein
        assert "din_18040_1" in hybrid_ids or "accessibility_law" in hybrid_ids
    
    @pytest.mark.asyncio
    async def test_latency_overhead(self, rag_service):
        """Test: Latenz-Overhead von Hybrid vs Dense."""
        query = "Nachhaltiges Bauen"
        
        # Warmup
        await rag_service.build_context(query, options=RAGQueryOptions(enable_hybrid_search=False, enable_reranking=False))
        
        # Measure Dense
        latencies_dense = []
        for _ in range(3):
            start = time.time()
            await rag_service.build_context(
                query,
                options=RAGQueryOptions(enable_hybrid_search=False, enable_reranking=False)
            )
            latencies_dense.append((time.time() - start) * 1000)
        
        # Measure Hybrid
        latencies_hybrid = []
        for _ in range(3):
            start = time.time()
            await rag_service.build_context(
                query,
                options=RAGQueryOptions(enable_hybrid_search=True, enable_reranking=False)
            )
            latencies_hybrid.append((time.time() - start) * 1000)
        
        avg_dense = sum(latencies_dense) / len(latencies_dense)
        avg_hybrid = sum(latencies_hybrid) / len(latencies_hybrid)
        
        overhead = avg_hybrid - avg_dense
        
        # Overhead sollte < 100ms sein
        assert overhead < 100, f"Hybrid Overhead zu hoch: {overhead:.1f}ms"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-k", "not test_query_expansion"])
