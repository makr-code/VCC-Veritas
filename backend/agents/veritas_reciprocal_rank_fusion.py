#!/usr/bin/env python3
"""
VERITAS RECIPROCAL RANK FUSION (RRF)
=====================================

Fusioniert Ergebnisse von mehreren Retrievern (Dense + Sparse) zu einem
kombinierten Ranking mit Reciprocal Rank Fusion (RRF).

RRF ist ein einfacher aber effektiver Fusion-Algorithmus, der rank-basiert
arbeitet (nicht score-basiert) und daher robust gegen unterschiedliche
Score-Skalen ist.

RRF Formula:
-----------
RRF_score(d) = Σ_{r ∈ R} 1 / (k + rank_r(d))

Wobei:
- d = Dokument
- R = Menge der Retriever (z.B. {Dense, Sparse})
- rank_r(d) = Rang von Dokument d in Retriever r (1-based)
- k = Konstante (typisch 60, reduziert Einfluss niedrig-gerankter Docs)

Vorteile gegenüber Score-Fusion:
--------------------------------
- Keine Normalisierung nötig (unterschiedliche Score-Skalen)
- Robust gegen Ausreißer
- Einfach & interpretierbar
- State-of-the-Art in Multi-Retriever-Fusion

Referenzen:
----------
- Cormack et al. (2009): "Reciprocal Rank Fusion outperforms Condorcet"
- Used by: Cohere Rerank, Pinecone Hybrid Search, Weaviate

Author: VERITAS System
Date: 2025-10-06
Version: 1.0
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class RRFConfig:
    """Konfiguration für Reciprocal Rank Fusion"""

    # RRF-Parameter
    k: int = 60  # RRF-Konstante (typisch 60, range: 1-100)

    # Fusion-Parameter
    top_k: int = 50  # Top-K Dokumente nach Fusion
    min_retriever_results: int = 1  # Min Anzahl Retriever mit Result für Dokument

    # Weights (optional)
    weights: Optional[Dict[str, float]] = None  # z.B. {"dense": 0.7, "sparse": 0.3}


@dataclass
class FusedDocument:
    """Dokument mit fusioniertem RRF-Score"""

    doc_id: str
    content: str
    rrf_score: float  # RRF-Score

    # Source-Informationen
    source_scores: Dict[str, float] = field(default_factory=dict)  # Original-Scores
    source_ranks: Dict[str, int] = field(default_factory=dict)  # Ranks in Sources
    sources: List[str] = field(default_factory=list)  # Welche Retriever fanden Doc

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion für Multi-Retriever-Kombination.

    Funktionsweise:
    --------------
    1. Retriever A liefert: [Doc1, Doc2, Doc3, ...]
    2. Retriever B liefert: [Doc3, Doc1, Doc5, ...]
    3. RRF berechnet für jedes Dokument:
       - RRF(Doc1) = 1/(60+1) + 1/(60+2) = 0.0164 + 0.0161 = 0.0325
       - RRF(Doc2) = 1/(60+2) + 0 = 0.0161
       - RRF(Doc3) = 1/(60+3) + 1/(60+1) = 0.0159 + 0.0164 = 0.0323
    4. Sortiere nach RRF-Score: [Doc1, Doc3, Doc2, ...]

    Interpretation:
    --------------
    - Höherer RRF-Score = Dokument in mehreren Retrievern hoch gerankt
    - Dokumente nur in einem Retriever = niedrigerer Score
    - Top-ranked Docs in allen Retrievern = höchster Score

    Performance:
    -----------
    - Zeit: O(N) wobei N = Summe aller Results
    - Memory: O(N)
    - Sehr schnell (keine ML-Inferenz)
    """

    def __init__(self, config: Optional[RRFConfig] = None):
        """
        Initialisiert RRF.

        Args:
            config: RRF-Konfiguration (optional)
        """
        self.config = config or RRFConfig()

    def fuse(
        self,
        retriever_results: Dict[str, List[Any]],
        top_k: Optional[int] = None,
        doc_id_field: str = "doc_id",
        content_field: str = "content",
    ) -> List[FusedDocument]:
        """
        Fusioniert Results von mehreren Retrievern via RRF.

        Args:
            retriever_results: Dict {retriever_name: [doc1, doc2, ...]}
                               Docs können Dicts oder Dataclasses sein
            top_k: Anzahl Top-Dokumente (default: config.top_k)
            doc_id_field: Name des ID-Felds (default: "doc_id")
            content_field: Name des Content-Felds (default: "content")

        Returns:
            Liste der Top-K fusionierte Dokumente, sortiert nach RRF-Score

        Example:
            >>> retriever_results = {
            ...     "dense": [doc1, doc2, doc3],
            ...     "sparse": [doc3, doc1, doc5]
            ... }
            >>> fused = rrf.fuse(retriever_results)
        """
        top_k = top_k or self.config.top_k

        # RRF-Scores berechnen
        rrf_scores = defaultdict(float)
        source_ranks = defaultdict(dict)
        source_scores = defaultdict(dict)
        sources = defaultdict(list)
        doc_contents = {}  # doc_id → content
        doc_metadata = {}  # doc_id → metadata

        for retriever_name, results in retriever_results.items():
            # Weight für Retriever
            weight = 1.0
            if self.config.weights and retriever_name in self.config.weights:
                weight = self.config.weights[retriever_name]

            for rank, doc in enumerate(results):
                # Extract doc_id & content
                if isinstance(doc, dict):
                    doc_id = doc.get(doc_id_field)
                    content = doc.get(content_field, "")
                    original_score = doc.get("score", 0.0)
                    metadata = doc.get("metadata", {})
                else:
                    # Dataclass/Object
                    doc_id = getattr(doc, doc_id_field, None)
                    content = getattr(doc, content_field, "")
                    original_score = getattr(doc, "score", 0.0)
                    metadata = getattr(doc, "metadata", {})

                if doc_id is None:
                    logger.warning(f"⚠️ Dokument ohne ID in {retriever_name} übersprungen")
                    continue

                # RRF-Score akkumulieren
                rank_score = 1.0 / (self.config.k + rank + 1)
                rrf_scores[doc_id] += weight * rank_score

                # Source-Informationen speichern
                source_ranks[doc_id][retriever_name] = rank + 1  # 1-based
                source_scores[doc_id][retriever_name] = original_score

                if retriever_name not in sources[doc_id]:
                    sources[doc_id].append(retriever_name)

                # Content & Metadata (erste Occurrence)
                if doc_id not in doc_contents:
                    doc_contents[doc_id] = content
                    doc_metadata[doc_id] = metadata

        # Filter: Minimale Anzahl Retriever
        if self.config.min_retriever_results > 1:
            rrf_scores = {
                doc_id: score
                for doc_id, score in rrf_scores.items()
                if len(sources[doc_id]) >= self.config.min_retriever_results
            }

        # Sortiere nach RRF-Score
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # Top-K extrahieren
        fused_docs = []
        for doc_id, rrf_score in sorted_docs[:top_k]:
            fused_docs.append(
                FusedDocument(
                    doc_id=doc_id,
                    content=doc_contents.get(doc_id, ""),
                    rrf_score=rrf_score,
                    source_scores=dict(source_scores[doc_id]),
                    source_ranks=dict(source_ranks[doc_id]),
                    sources=sources[doc_id],
                    metadata=doc_metadata.get(doc_id, {}),
                )
            )

        logger.debug(
            f"🔀 RRF Fusion: {len(fused_docs)} Docs aus {len(retriever_results)} Retrievern "
            f"(Total Input: {sum(len(r) for r in retriever_results.values())} Docs)"
        )

        return fused_docs

    def fuse_two(
        self,
        dense_results: List[Any],
        sparse_results: List[Any],
        top_k: Optional[int] = None,
        doc_id_field: str = "doc_id",
        content_field: str = "content",
    ) -> List[FusedDocument]:
        """
        Convenience-Methode für Dense + Sparse Fusion.

        Args:
            dense_results: Results von Dense Retrieval
            sparse_results: Results von Sparse Retrieval
            top_k: Anzahl Top-Dokumente
            doc_id_field: Name des ID-Felds
            content_field: Name des Content-Felds

        Returns:
            Liste der Top-K fusionierte Dokumente
        """
        return self.fuse(
            retriever_results={"dense": dense_results, "sparse": sparse_results},
            top_k=top_k,
            doc_id_field=doc_id_field,
            content_field=content_field,
        )

    def get_fusion_stats(self, fused_docs: List[FusedDocument]) -> Dict[str, Any]:
        """
        Berechnet Fusion-Statistiken.

        Args:
            fused_docs: Fusionierte Dokumente

        Returns:
            Dict mit Stats (avg_sources, source_distribution, etc.)
        """
        if not fused_docs:
            return {"num_docs": 0, "avg_sources_per_doc": 0.0, "source_distribution": {}}

        # Source-Distribution (wie viele Docs von jedem Retriever)
        source_counts = defaultdict(int)
        for doc in fused_docs:
            for source in doc.sources:
                source_counts[source] += 1

        # Avg Sources per Doc
        avg_sources = sum(len(doc.sources) for doc in fused_docs) / len(fused_docs)

        # Overlap (Docs in beiden Retrievern)
        both_sources = sum(1 for doc in fused_docs if len(doc.sources) > 1)
        overlap_rate = both_sources / len(fused_docs) if fused_docs else 0.0

        return {
            "num_docs": len(fused_docs),
            "avg_sources_per_doc": avg_sources,
            "source_distribution": dict(source_counts),
            "overlap_count": both_sources,
            "overlap_rate": overlap_rate,
            "avg_rrf_score": sum(doc.rrf_score for doc in fused_docs) / len(fused_docs),
            "max_rrf_score": max(doc.rrf_score for doc in fused_docs),
            "min_rrf_score": min(doc.rrf_score for doc in fused_docs),
        }


# Singleton Pattern
_rrf_instance: Optional[ReciprocalRankFusion] = None


def get_rrf(config: Optional[RRFConfig] = None) -> ReciprocalRankFusion:
    """
    Gibt Singleton-Instanz von RRF zurück.

    Args:
        config: RRF-Konfiguration (nur beim ersten Aufruf)

    Returns:
        ReciprocalRankFusion-Instanz
    """
    global _rrf_instance

    if _rrf_instance is None:
        _rrf_instance = ReciprocalRankFusion(config)

    return _rrf_instance
