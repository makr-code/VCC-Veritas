#!/usr/bin/env python3
"""
VERITAS HYBRID RETRIEVAL SERVICE
=================================

Kombiniert Dense Retrieval (Embeddings) und Sparse Retrieval (BM25)
via Reciprocal Rank Fusion (RRF) für optimale Recall + Precision.

Hybrid Search Workflow:
----------------------
1. Dense Retrieval (UDS3/Embeddings): Semantische Ähnlichkeit → Top-50
2. Sparse Retrieval (BM25): Lexikalisches Matching → Top-50
3. Reciprocal Rank Fusion (RRF): Kombiniert beide → Top-20
4. Cross-Encoder Re-Ranking: Precision-Optimierung → Top-5

Vorteile:
---------
- Dense: Semantik, Synonyme, Paraphrasen
- Sparse: Exakte Begriffe, Akronyme, Terminologie
- RRF: Robuste Fusion ohne Score-Normalisierung

Use-Cases:
----------
Dense allein: "Wie baue ich ein umweltfreundliches Haus?"
Sparse allein: "§ 3a UVPG DIN 18040-1"
Hybrid (best): Kombination von semantischer + terminologischer Suche

Author: VERITAS System
Date: 2025-10-06
Version: 1.0
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import Sparse Retriever & RRF
try:
    from backend.agents.veritas_sparse_retrieval import (
        SparseRetriever,
        SparseRetrievalConfig,
        get_sparse_retriever
    )
    from backend.agents.veritas_reciprocal_rank_fusion import (
        ReciprocalRankFusion,
        RRFConfig,
        FusedDocument,
        get_rrf
    )
    HYBRID_AVAILABLE = True
    logger.info("✅ Hybrid Retrieval verfügbar (Sparse + RRF)")
except ImportError as e:
    HYBRID_AVAILABLE = False
    logger.warning(f"⚠️ Hybrid Retrieval nicht verfügbar: {e}")

# Import Query Expansion (optional)
try:
    from backend.agents.veritas_query_expansion import (
        QueryExpander,
        QueryExpansionConfig,
        get_query_expander,
        ExpansionStrategy
    )
    QUERY_EXPANSION_AVAILABLE = True
    logger.info("✅ Query Expansion verfügbar (LLM-basiert)")
except ImportError as e:
    QUERY_EXPANSION_AVAILABLE = False
    logger.warning(f"⚠️ Query Expansion nicht verfügbar: {e}")


@dataclass
class HybridRetrievalConfig:
    """Konfiguration für Hybrid Retrieval"""
    
    # Retrieval-Parameter
    dense_top_k: int = 50  # Top-K für Dense Retrieval
    sparse_top_k: int = 50  # Top-K für Sparse Retrieval
    final_top_k: int = 20  # Top-K nach RRF-Fusion
    
    # Weights für RRF (optional)
    dense_weight: float = 0.6  # Dense Retrieval Weight
    sparse_weight: float = 0.4  # Sparse Retrieval Weight
    
    # RRF-Parameter
    rrf_k: int = 60  # RRF-Konstante
    
    # Feature-Toggles
    enable_sparse: bool = True  # Sparse Retrieval aktivieren
    enable_fusion: bool = True  # RRF-Fusion aktivieren
    enable_query_expansion: bool = True  # Query Expansion aktivieren
    
    # Query Expansion Parameter
    num_query_expansions: int = 2  # Anzahl Query-Varianten
    expansion_strategies: List[str] = field(
        default_factory=lambda: ["synonym", "context"]
    )
    
    # Fallback-Verhalten
    fallback_to_dense: bool = True  # Fallback auf Dense wenn Sparse fehlt
    enable_fusion: bool = True  # RRF-Fusion aktivieren
    
    # Fallback-Verhalten
    fallback_to_dense: bool = True  # Fallback auf Dense wenn Sparse fehlt


@dataclass
class HybridResult:
    """Ergebnis von Hybrid Retrieval"""
    
    doc_id: str
    content: str
    score: float  # RRF-Score oder Dense-Score (Fallback)
    
    # Source-Informationen
    sources: List[str] = field(default_factory=list)  # ["dense", "sparse"]
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieval_method: str = "hybrid"  # "hybrid", "dense_only", "sparse_only"


class HybridRetriever:
    """
    Hybrid Retrieval Service: Dense + Sparse + RRF-Fusion.
    
    Funktionsweise:
    --------------
    1. **Dense Retrieval (UDS3):**
       - Embedding-basiert
       - Semantische Ähnlichkeit
       - Gut für natürliche Sprache
    
    2. **Sparse Retrieval (BM25):**
       - Term-Matching-basiert
       - Lexikalische Ähnlichkeit
       - Gut für Terminologie, Akronyme
    
    3. **Reciprocal Rank Fusion:**
       - Kombiniert beide Rankings
       - Rank-basiert (nicht score-basiert)
       - Robust gegen unterschiedliche Score-Skalen
    
    Performance:
    -----------
    - Dense: ~50-100ms (UDS3 Vector Search)
    - Sparse: ~10-20ms (BM25)
    - RRF: ~1-2ms (Python, O(N))
    - Total: ~60-120ms (parallel execution)
    
    vs. Dense-Only: +20-50ms Overhead, aber deutlich bessere Relevanz
    """
    
    def __init__(
        self,
        dense_retriever: Any,  # UDS3 Strategy oder andere Dense-Retriever
        sparse_retriever: Optional[SparseRetriever] = None,
        config: Optional[HybridRetrievalConfig] = None
    ):
        """
        Initialisiert Hybrid Retriever.
        
        Args:
            dense_retriever: Dense Retrieval Backend (z.B. UDS3)
            sparse_retriever: BM25 Sparse Retriever (optional)
            config: Hybrid-Konfiguration (optional)
        """
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever or get_sparse_retriever()
        self.config = config or HybridRetrievalConfig()
        
        # RRF mit Weights
        rrf_config = RRFConfig(
            k=self.config.rrf_k,
            top_k=self.config.final_top_k,
            weights={
                "dense": self.config.dense_weight,
                "sparse": self.config.sparse_weight
            }
        )
        self.rrf = get_rrf(rrf_config)
        
        # Check Sparse availability
        self._sparse_available = (
            self.config.enable_sparse and 
            self.sparse_retriever.is_available()
        )
        
        if not self._sparse_available:
            logger.warning(
                "⚠️ Sparse Retrieval nicht verfügbar - verwende Dense-Only Modus"
            )
        
        # Check Dense Retriever capability (UDS3 v2.0.0 compatibility)
        # UDS3 v2.0.0 uses 'semantic_search' instead of 'vector_search'
        self._semantic_search_available = hasattr(self.dense_retriever, 'semantic_search')
        self._vector_search_available = hasattr(self.dense_retriever, 'vector_search')
        self._has_search_documents = hasattr(self.dense_retriever, 'search_documents')
        
        if not (self._semantic_search_available or self._vector_search_available or self._has_search_documents):
            logger.warning(
                "⚠️ Dense Retriever hat keine semantic_search/vector_search/search_documents Methode - Dense Retrieval deaktiviert"
            )
        elif self._semantic_search_available:
            logger.info("✅ UDS3 v2.0.0 semantic_search verfügbar für Dense Retrieval")
        elif self._vector_search_available:
            logger.info("✅ vector_search verfügbar für Dense Retrieval")
        elif self._has_search_documents:
            logger.info("✅ search_documents Fallback verfügbar für Dense Retrieval")
        
        # Query Expansion initialisieren (optional)
        self._query_expansion_available = (
            self.config.enable_query_expansion and
            QUERY_EXPANSION_AVAILABLE
        )
        
        self.query_expander = None
        if self._query_expansion_available:
            try:
                from backend.agents.veritas_query_expansion import ExpansionStrategy
                
                # Konvertiere String-Strategien zu Enum
                strategies = []
                for s in self.config.expansion_strategies:
                    if s == "synonym":
                        strategies.append(ExpansionStrategy.SYNONYM)
                    elif s == "context":
                        strategies.append(ExpansionStrategy.CONTEXT)
                    elif s == "technical":
                        strategies.append(ExpansionStrategy.TECHNICAL)
                
                expansion_config = QueryExpansionConfig(
                    num_expansions=self.config.num_query_expansions,
                    strategies=strategies
                )
                
                self.query_expander = get_query_expander(expansion_config)
                logger.info("✅ Query Expansion für HybridRetriever aktiviert")
            except Exception as e:
                logger.warning(f"⚠️ Query Expansion konnte nicht initialisiert werden: {e}")
                self._query_expansion_available = False
    
    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        enable_sparse: Optional[bool] = None,
        enable_query_expansion: Optional[bool] = None,
        dense_params: Optional[Dict[str, Any]] = None,
        sparse_params: Optional[Dict[str, Any]] = None
    ) -> List[HybridResult]:
        """
        Hybrid Retrieval: Dense + Sparse + RRF-Fusion + Query Expansion.
        
        Args:
            query: Suchanfrage
            top_k: Anzahl Top-Dokumente (default: config.final_top_k)
            enable_sparse: Sparse Retrieval aktivieren (override config)
            enable_query_expansion: Query Expansion aktivieren (override config)
            dense_params: Parameter für Dense Retrieval (optional)
            sparse_params: Parameter für Sparse Retrieval (optional)
            
        Returns:
            Liste der Top-K Hybrid-Results, sortiert nach RRF-Score
        """
        top_k = top_k or self.config.final_top_k
        enable_sparse = enable_sparse if enable_sparse is not None else self.config.enable_sparse
        enable_query_expansion = enable_query_expansion if enable_query_expansion is not None else self.config.enable_query_expansion
        
        start_time = time.time()
        
        # === QUERY EXPANSION (Optional) ===
        queries_to_search = [query]  # Original Query
        query_expansion_applied = False
        
        if enable_query_expansion and self._query_expansion_available:
            try:
                expanded = await self.query_expander.expand(
                    query,
                    num_expansions=self.config.num_query_expansions
                )
                
                # Füge expandierte Queries hinzu (ohne Original-Duplikat)
                for eq in expanded:
                    if eq.text != query and eq.text not in queries_to_search:
                        queries_to_search.append(eq.text)
                
                query_expansion_applied = len(queries_to_search) > 1
                
                if query_expansion_applied:
                    logger.debug(
                        f"🔍 Query Expansion: '{query[:50]}...' → {len(queries_to_search)} Varianten"
                    )
                
            except Exception as e:
                logger.warning(f"⚠️ Query Expansion fehlgeschlagen: {e}")
        
        # === MULTI-QUERY RETRIEVAL ===
        # Für jede Query: Dense + Sparse Retrieval
        all_dense_results = []
        all_sparse_results = []
        
        for q in queries_to_search:
            # Parallel Retrieval: Dense + Sparse
            tasks = []
            
            # Dense Retrieval (immer)
            dense_task = self._retrieve_dense(q, dense_params or {})
            tasks.append(dense_task)
            
            # Sparse Retrieval (optional)
            if enable_sparse and self._sparse_available:
                sparse_task = self._retrieve_sparse(q, sparse_params or {})
                tasks.append(sparse_task)
            
            # Parallel ausführen
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Extract Dense Results
            dense_results = results[0] if not isinstance(results[0], Exception) else []
            if isinstance(results[0], Exception):
                logger.error(f"❌ Dense Retrieval fehler für '{q[:30]}...': {results[0]}")
                dense_results = []
            
            all_dense_results.extend(dense_results)
            
            # Extract Sparse Results (wenn vorhanden)
            if len(results) > 1:
                sparse_results = results[1] if not isinstance(results[1], Exception) else []
                if isinstance(results[1], Exception):
                    logger.warning(f"⚠️ Sparse Retrieval fehler für '{q[:30]}...': {results[1]}")
                else:
                    all_sparse_results.extend(sparse_results)
        
        # RRF-Fusion oder Fallback
        if all_sparse_results and self.config.enable_fusion:
            # Hybrid: Dense + Sparse via RRF
            fused_docs = self.rrf.fuse_two(
                all_dense_results,
                all_sparse_results,
                top_k=top_k
            )
            
            hybrid_results = self._convert_fused_to_hybrid(fused_docs)
            
            retrieval_time = time.time() - start_time
            
            # Log mit Query Expansion Info
            expansion_info = f" + {len(queries_to_search)} Queries" if query_expansion_applied else ""
            logger.debug(
                f"🔍 Hybrid Retrieval{expansion_info}: {len(hybrid_results)} Docs in {retrieval_time*1000:.1f}ms "
                f"(Dense: {len(all_dense_results)}, Sparse: {len(all_sparse_results)})"
            )
            
        else:
            # Fallback: Dense-Only
            hybrid_results = self._convert_dense_to_hybrid(all_dense_results[:top_k])
            
            retrieval_time = time.time() - start_time
            expansion_info = f" + {len(queries_to_search)} Queries" if query_expansion_applied else ""
            logger.debug(
                f"🔍 Dense-Only Retrieval{expansion_info}: {len(hybrid_results)} Docs in {retrieval_time*1000:.1f}ms"
            )
        
        return hybrid_results
    
    async def _retrieve_dense(
        self,
        query: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Dense Retrieval via UDS3 oder ähnliches.
        
        Args:
            query: Suchanfrage
            params: Dense Retrieval Parameter
            
        Returns:
            Liste von Dokumenten mit 'doc_id', 'content', 'score'
        """
        # UDS3 v2.0.0 Semantic Search (oder Legacy vector_search/search_documents)
        try:
            # Remove top_k from params if present to avoid conflict
            clean_params = {k: v for k, v in params.items() if k != 'top_k'}
            
            # Priority 1: UDS3 v2.0.0 semantic_search
            if self._semantic_search_available:
                results = await self.dense_retriever.semantic_search(
                    query=query,
                    top_k=self.config.dense_top_k,
                    **clean_params
                )
            # Priority 2: Legacy vector_search
            elif self._vector_search_available:
                results = await self.dense_retriever.vector_search(
                    query=query,
                    top_k=self.config.dense_top_k,
                    **clean_params
                )
            # Priority 3: Generic search_documents fallback
            elif self._has_search_documents:
                results = await self.dense_retriever.search_documents(
                    query=query,
                    limit=self.config.dense_top_k,
                    **clean_params
                )
            else:
                # No vector search available - return empty results (warning already logged in __init__)
                return []
            
            # Normalisiere zu einheitlichem Format
            normalized = []
            for result in results:
                normalized.append({
                    "doc_id": result.get("id") or result.get("doc_id"),
                    "content": result.get("content") or result.get("text", ""),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                })
            
            return normalized
            
        except AttributeError as e:
            logger.warning(f"⚠️ Dense Retrieval Methode nicht verfügbar: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Dense Retrieval Fehler: {e}")
            return []
    
    async def _retrieve_sparse(
        self,
        query: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Sparse Retrieval via BM25.
        
        Args:
            query: Suchanfrage
            params: Sparse Retrieval Parameter
            
        Returns:
            Liste von Dokumenten mit 'doc_id', 'content', 'score'
        """
        try:
            # Remove top_k from params if present to avoid conflict
            clean_params = {k: v for k, v in params.items() if k != 'top_k'}
            
            results = await self.sparse_retriever.retrieve(
                query=query,
                top_k=self.config.sparse_top_k,
                **clean_params
            )
            
            # Konvertiere zu Dict-Format
            return [
                {
                    "doc_id": result.doc_id,
                    "content": result.content,
                    "score": result.score,
                    "metadata": result.metadata
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"❌ Sparse Retrieval fehler: {e}")
            return []
    
    def _convert_fused_to_hybrid(
        self,
        fused_docs: List[FusedDocument]
    ) -> List[HybridResult]:
        """Konvertiert FusedDocuments zu HybridResults."""
        return [
            HybridResult(
                doc_id=doc.doc_id,
                content=doc.content,
                score=doc.rrf_score,
                sources=doc.sources,
                dense_score=doc.source_scores.get("dense"),
                sparse_score=doc.source_scores.get("sparse"),
                dense_rank=doc.source_ranks.get("dense"),
                sparse_rank=doc.source_ranks.get("sparse"),
                metadata=doc.metadata,
                retrieval_method="hybrid"
            )
            for doc in fused_docs
        ]
    
    def _convert_dense_to_hybrid(
        self,
        dense_docs: List[Dict[str, Any]]
    ) -> List[HybridResult]:
        """Konvertiert Dense-Only Results zu HybridResults."""
        return [
            HybridResult(
                doc_id=doc["doc_id"],
                content=doc["content"],
                score=doc["score"],
                sources=["dense"],
                dense_score=doc["score"],
                dense_rank=i + 1,
                metadata=doc.get("metadata", {}),
                retrieval_method="dense_only"
            )
            for i, doc in enumerate(dense_docs)
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Hybrid-Retrieval-Statistiken zurück."""
        return {
            "hybrid_available": HYBRID_AVAILABLE,
            "sparse_available": self._sparse_available,
            "query_expansion_available": self._query_expansion_available,
            "config": {
                "dense_top_k": self.config.dense_top_k,
                "sparse_top_k": self.config.sparse_top_k,
                "final_top_k": self.config.final_top_k,
                "dense_weight": self.config.dense_weight,
                "sparse_weight": self.config.sparse_weight,
                "enable_sparse": self.config.enable_sparse,
                "enable_fusion": self.config.enable_fusion,
                "enable_query_expansion": self.config.enable_query_expansion,
                "num_query_expansions": self.config.num_query_expansions
            },
            "sparse_retriever_stats": self.sparse_retriever.get_stats() if self._sparse_available else {},
            "query_expander_stats": self.query_expander.get_stats() if self._query_expansion_available else {}
        }


# Factory-Funktion für einfache Erstellung
def create_hybrid_retriever(
    dense_retriever: Any,
    corpus: Optional[List[Dict[str, Any]]] = None,
    config: Optional[HybridRetrievalConfig] = None
) -> HybridRetriever:
    """
    Erstellt HybridRetriever mit optionaler Corpus-Indexierung.
    
    Args:
        dense_retriever: Dense Retrieval Backend
        corpus: Dokumente für BM25-Indexierung (optional)
        config: Hybrid-Konfiguration (optional)
        
    Returns:
        HybridRetriever-Instanz
    """
    sparse_retriever = get_sparse_retriever()
    
    # Indexiere Corpus wenn vorhanden
    if corpus and sparse_retriever.is_available():
        sparse_retriever.index_documents(corpus)
    
    return HybridRetriever(
        dense_retriever=dense_retriever,
        sparse_retriever=sparse_retriever,
        config=config
    )
