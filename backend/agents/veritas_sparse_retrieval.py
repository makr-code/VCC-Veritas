#!/usr/bin/env python3
"""
VERITAS SPARSE RETRIEVAL SERVICE
=================================

BM25-basierte Sparse Retrieval für lexikalisches Matching.
Komplementär zum Dense Retrieval (Embeddings) für Hybrid Search.

BM25 Vorteile:
- Exakte Begriffe (§ 242 BGB, DIN 18040-1)
- Akronyme & Abkürzungen (UVP, VOB, BGB)
- Zahlen & Daten (2024, 50.000 EUR)
- Terminologie-Matching

Use-Case:
---------
Dense Retrieval: "Bauvorhaben Umweltauflagen" → semantisch ähnliche Docs
Sparse Retrieval: "UVP §3a UVPG" → exakte terminologische Matches

Hybrid: Kombiniert beides für optimale Recall + Precision

Author: VERITAS System
Date: 2025-10-06
Version: 1.0
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# BM25 Import (optional - graceful degradation)
try:
    from rank_bm25 import BM25Okapi

    BM25_AVAILABLE = True
    logger.info("✅ rank_bm25 verfügbar - Sparse Retrieval aktiv")
except ImportError:
    BM25_AVAILABLE = False
    BM25Okapi = None
    logger.warning("⚠️ rank_bm25 nicht installiert - Sparse Retrieval deaktiviert")
    logger.warning("   Installation: pip install rank-bm25")


@dataclass
class SparseRetrievalConfig:
    """Konfiguration für BM25 Sparse Retrieval"""

    # BM25-Parameter
    k1: float = 1.5  # Term frequency saturation (default: 1.5, range: 1.2-2.0)
    b: float = 0.75  # Document length normalization (default: 0.75, range: 0-1)

    # Retrieval-Parameter
    top_k: int = 50  # Top-K Dokumente

    # Tokenization
    lowercase: bool = True  # Kleinschreibung
    remove_punctuation: bool = False  # Satzzeichen NICHT entfernen (wichtig für § etc.)
    min_token_length: int = 2  # Minimale Token-Länge

    # Cache
    enable_cache: bool = True  # Query-Cache
    cache_ttl: int = 3600  # Cache Time-To-Live (Sekunden)


@dataclass
class ScoredDocument:
    """Dokument mit BM25-Score"""

    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "bm25"  # Retrieval-Source


class SparseRetriever:
    """
    BM25-basierte Sparse Retrieval für lexikalisches Matching.

    BM25 (Best Matching 25) ist ein probabilistisches Retrieval-Modell,
    das auf Bag-of-Words und TF-IDF basiert. Es bewertet Dokumente nach:

    1. Term Frequency (TF): Wie oft kommt Query-Term im Dokument vor?
    2. Inverse Document Frequency (IDF): Wie selten ist Term im Corpus?
    3. Document Length Normalization: Längere Docs nicht bevorzugen

    BM25 Formula:
    ------------
    score(D,Q) = Σ IDF(q_i) * (f(q_i,D) * (k1+1)) / (f(q_i,D) + k1 * (1-b + b * |D|/avgdl))

    Wobei:
    - D = Dokument
    - Q = Query
    - q_i = Query-Term
    - f(q_i,D) = Frequenz von q_i in D
    - |D| = Länge von D
    - avgdl = Durchschnittliche Dokumentlänge im Corpus
    - k1, b = Tuning-Parameter

    Performance:
    -----------
    - Indexing: O(N * M) wobei N=Docs, M=Avg-Tokens
    - Retrieval: O(N) (linear scan, kann mit Inverted Index optimiert werden)
    - Memory: ~100-200 bytes pro Dokument (tokenized)
    """

    def __init__(self, config: Optional[SparseRetrievalConfig] = None):
        """
        Initialisiert BM25 Sparse Retriever.

        Args:
            config: BM25-Konfiguration (optional)
        """
        self.config = config or SparseRetrievalConfig()
        self.bm25: Optional[BM25Okapi] = None
        self.corpus: List[str] = []
        self.doc_ids: List[str] = []
        self.tokenized_corpus: List[List[str]] = []
        self._indexed = False
        self._cache: Dict[str, List[ScoredDocument]] = {}
        self._empty_index_warning_shown = False  # Flag für one-time warning

        if not BM25_AVAILABLE:
            logger.error("❌ BM25 nicht verfügbar - SparseRetriever funktioniert nicht!")

    def is_available(self) -> bool:
        """Prüft ob BM25 verfügbar ist (unabhängig vom Index-Status)."""
        return BM25_AVAILABLE

    def is_indexed(self) -> bool:
        """Prüft ob Dokumente indexiert sind."""
        return self._indexed

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenisiert Text für BM25.

        Args:
            text: Zu tokenisierender Text

        Returns:
            Liste von Tokens
        """
        # Lowercase
        if self.config.lowercase:
            text = text.lower()

        # Simple Whitespace-Tokenization
        tokens = text.split()

        # Filter: Minimale Token-Länge
        tokens = [token for token in tokens if len(token) >= self.config.min_token_length]

        return tokens

    def index_documents(self, documents: List[Dict[str, Any]], content_field: str = "content", id_field: str = "id") -> None:
        """
        Indexiert Dokumente für BM25-Suche.

        Args:
            documents: Liste von Dokumenten mit 'id' und 'content'
            content_field: Name des Content-Felds (default: 'content')
            id_field: Name des ID-Felds (default: 'id')

        Raises:
            RuntimeError: Wenn BM25 nicht verfügbar
        """
        if not BM25_AVAILABLE:
            raise RuntimeError("BM25 nicht verfügbar - installiere rank-bm25: pip install rank-bm25")

        logger.info(f"📥 Indexiere {len(documents)} Dokumente für BM25...")
        start_time = time.time()

        # Extract Content & IDs
        self.corpus = [doc.get(content_field, "") for doc in documents]
        self.doc_ids = [documents[i].get(id_field, f"doc_{i}") for i in range(len(documents))]

        # Tokenize Corpus
        self.tokenized_corpus = [self._tokenize(doc) for doc in self.corpus]

        # Create BM25 Index
        self.bm25 = BM25Okapi(self.tokenized_corpus, k1=self.config.k1, b=self.config.b)

        self._indexed = True
        index_time = time.time() - start_time

        logger.info(
            f"✅ BM25-Index erstellt in {index_time:.2f}s "
            f"({len(documents)} Docs, {sum(len(t) for t in self.tokenized_corpus)} Tokens)"
        )

    async def retrieve(self, query: str, top_k: Optional[int] = None, min_score: float = 0.0) -> List[ScoredDocument]:
        """
        BM25-Suche für eine Query.

        Args:
            query: Suchanfrage
            top_k: Anzahl Top-Dokumente (default: config.top_k)
            min_score: Minimaler BM25-Score (default: 0.0)

        Returns:
            Liste der Top-K Dokumente mit BM25-Scores

        Raises:
            RuntimeError: Wenn BM25 nicht indexiert
        """
        if not self.is_available():
            logger.warning("⚠️ BM25 nicht verfügbar - leere Results")
            return []

        # Prüfen ob BM25 indexiert ist
        if not self.is_indexed() or self.bm25 is None:
            # Log warning only once (first time empty index is detected)
            if not self._empty_index_warning_shown:
                logger.warning("⚠️ BM25 Index ist leer - keine Dokumente indexiert")
                self._empty_index_warning_shown = True
            return []

        top_k = top_k or self.config.top_k

        # Cache-Check
        cache_key = f"{query}:{top_k}:{min_score}"
        if self.config.enable_cache and cache_key in self._cache:
            logger.debug(f"💾 Cache-Hit für Query: {query[:50]}...")
            return self._cache[cache_key]

        # Tokenize Query
        tokenized_query = self._tokenize(query)

        if not tokenized_query:
            logger.warning(f"⚠️ Query '{query}' hat keine Tokens nach Tokenization")
            return []

        # BM25 Scoring
        scores = self.bm25.get_scores(tokenized_query)

        # Top-K Indizes (sortiert nach Score, absteigend)
        top_indices = np.argsort(scores)[-top_k:][::-1]

        # Erstelle ScoredDocuments
        results = []
        for idx in top_indices:
            score = float(scores[idx])

            # Filter: Minimaler Score
            if score < min_score:
                continue

            results.append(ScoredDocument(doc_id=self.doc_ids[idx], content=self.corpus[idx], score=score, source="bm25"))

        # Cache
        if self.config.enable_cache:
            self._cache[cache_key] = results

        top_score = results[0].score if results else 0.0
        logger.debug(f"🔍 BM25 Retrieval: {len(results)} Docs für Query '{query[:50]}...' " f"(Top-Score: {top_score:.2f})")

        return results

    async def retrieve_multi_query(
        self, queries: List[str], top_k: Optional[int] = None, aggregation: str = "max"  # "max", "sum", "avg"
    ) -> List[ScoredDocument]:
        """
        BM25-Suche für multiple Queries mit Score-Aggregation.

        Args:
            queries: Liste von Suchanfragen
            top_k: Anzahl Top-Dokumente
            aggregation: Score-Aggregation ("max", "sum", "avg")

        Returns:
            Liste der Top-K Dokumente mit aggregierten Scores
        """
        if not self.is_available():
            return []

        top_k = top_k or self.config.top_k

        # Retrieve für jede Query
        all_scores = []
        for query in queries:
            tokenized_query = self._tokenize(query)
            if tokenized_query:
                scores = self.bm25.get_scores(tokenized_query)
                all_scores.append(scores)

        if not all_scores:
            return []

        # Score-Aggregation
        all_scores = np.array(all_scores)

        if aggregation == "max":
            aggregated_scores = np.max(all_scores, axis=0)
        elif aggregation == "sum":
            aggregated_scores = np.sum(all_scores, axis=0)
        elif aggregation == "avg":
            aggregated_scores = np.mean(all_scores, axis=0)
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")

        # Top-K
        top_indices = np.argsort(aggregated_scores)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            score = float(aggregated_scores[idx])
            results.append(
                ScoredDocument(
                    doc_id=self.doc_ids[idx],
                    content=self.corpus[idx],
                    score=score,
                    metadata={"aggregation": aggregation, "num_queries": len(queries)},
                    source="bm25_multi",
                )
            )

        logger.debug(f"🔍 BM25 Multi-Query: {len(results)} Docs für {len(queries)} Queries " f"(Aggregation: {aggregation})")

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt BM25-Statistiken zurück.

        Returns:
            Dict mit Stats (num_docs, avg_doc_length, cache_size, etc.)
        """
        if not self._indexed:
            return {"indexed": False, "available": False}

        return {
            "indexed": True,
            "available": BM25_AVAILABLE,
            "num_documents": len(self.corpus),
            "num_tokens": sum(len(tokens) for tokens in self.tokenized_corpus),
            "avg_doc_length": np.mean([len(tokens) for tokens in self.tokenized_corpus]),
            "cache_size": len(self._cache),
            "config": {"k1": self.config.k1, "b": self.config.b, "top_k": self.config.top_k},
        }

    def clear_cache(self) -> None:
        """Leert den Query-Cache."""
        cache_size = len(self._cache)
        self._cache.clear()
        logger.info(f"🗑️ BM25-Cache geleert ({cache_size} Einträge)")


# Singleton Pattern für globalen Sparse Retriever
_sparse_retriever_instance: Optional[SparseRetriever] = None


def get_sparse_retriever(config: Optional[SparseRetrievalConfig] = None) -> SparseRetriever:
    """
    Gibt Singleton-Instanz des SparseRetrievers zurück.

    Args:
        config: BM25-Konfiguration (nur beim ersten Aufruf)

    Returns:
        SparseRetriever-Instanz
    """
    global _sparse_retriever_instance

    if _sparse_retriever_instance is None:
        _sparse_retriever_instance = SparseRetriever(config)

    return _sparse_retriever_instance
