#!/usr/bin/env python3
"""
VERITAS RE-RANKING SERVICE
==========================

Cross-Encoder-basiertes Re-Ranking für höhere Präzision bei der Dokumenten-Retrieval.

Inspiriert von:
- Azure Semantic Ranker
- AWS Bedrock Reranker
- GCP Vertex AI Ranking API

Architektur:
    Stufe 1: Initial Retrieval (UDS3) → Top-20 Dokumente (Recall-optimiert)
    Stufe 2: Re-Ranking (dieser Service) → Top-5 Dokumente (Precision-optimiert)
    Stufe 3: Graph-Context-Synthese (VCC-Stärke)

On-Premise Vorteile:
- Keine API-Kosten
- Volle Datensouveränität
- Niedrige Latenz
- Keine Größenbeschränkungen

Author: VERITAS System
Date: 2025-10-06
Version: 1.0
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Cross-Encoder Import (optional - graceful degradation)
try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
    logger.info("✅ Cross-Encoder (sentence-transformers) verfügbar")
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    logger.warning("⚠️ Cross-Encoder nicht verfügbar - Re-Ranking deaktiviert")
    CrossEncoder = None


@dataclass
class ReRankingConfig:
    """Konfiguration für Re-Ranking-Service"""
    
    # Modell-Konfiguration
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Re-Ranking-Parameter
    top_k: int = 5  # Top-K Dokumente nach Re-Ranking
    initial_k: int = 20  # Initial abgerufene Dokumente
    
    # Performance-Parameter
    batch_size: int = 32  # Batch-Größe für Cross-Encoder
    max_length: int = 512  # Max Token-Länge für Query+Document
    
    # Schwellenwerte
    min_score: float = 0.0  # Minimaler Re-Ranking-Score
    score_threshold: Optional[float] = None  # Optionaler Score-Cutoff
    
    # Cache-Einstellungen
    enable_cache: bool = False  # Cache für wiederholte Queries
    cache_ttl: int = 3600  # Cache Time-To-Live in Sekunden


class ReRankingService:
    """
    Cross-Encoder-basiertes Re-Ranking für höhere Retrieval-Präzision.
    
    Funktionsweise:
    ---------------
    1. Bi-Encoder (UDS3): Schnelle semantische Suche → Top-20 Kandidaten
    2. Cross-Encoder (dieser Service): Präzise Query-Doc-Bewertung → Top-5
    
    Der Cross-Encoder bewertet jedes Query-Document-Pair einzeln und gibt
    einen Relevanz-Score zurück. Dies ist rechenintensiver als Bi-Encoder,
    aber deutlich präziser für das finale Ranking.
    
    Vorteile gegenüber reinem Vektor-Retrieval:
    -------------------------------------------
    - Höhere Precision@K (typisch +10-20%)
    - Bessere Erfassung von Query-Semantik
    - Robuster gegenüber Synonym-Problemen
    - Berücksichtigt Query-Document-Interaktion
    
    Performance:
    ------------
    - Latenz: ~50-100ms für 20 Dokumente (CPU)
    - Latenz: ~10-20ms für 20 Dokumente (GPU)
    - Memory: ~500MB für Modell
    """
    
    def __init__(self, config: Optional[ReRankingConfig] = None):
        """
        Initialisiert Re-Ranking-Service.
        
        Args:
            config: Re-Ranking-Konfiguration (optional)
        """
        self.config = config or ReRankingConfig()
        self.model: Optional[CrossEncoder] = None
        self._cache: Dict[str, List[Tuple[str, float]]] = {}
        self._model_loaded = False
        
        # Modell laden wenn verfügbar
        if CROSS_ENCODER_AVAILABLE:
            try:
                self._load_model()
            except Exception as e:
                logger.error(f"❌ Cross-Encoder konnte nicht geladen werden: {e}")
                self._model_loaded = False
        else:
            logger.warning("⚠️ Re-Ranking deaktiviert - Cross-Encoder nicht verfügbar")
    
    def _load_model(self) -> None:
        """Lädt Cross-Encoder-Modell."""
        logger.info(f"📥 Lade Cross-Encoder-Modell: {self.config.model_name}")
        start_time = time.time()
        
        self.model = CrossEncoder(
            self.config.model_name,
            max_length=self.config.max_length
        )
        
        load_time = time.time() - start_time
        self._model_loaded = True
        logger.info(f"✅ Cross-Encoder geladen in {load_time:.2f}s")
    
    def is_available(self) -> bool:
        """Prüft ob Re-Ranking verfügbar ist."""
        return CROSS_ENCODER_AVAILABLE and self._model_loaded
    
    async def rerank_documents(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        return_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Re-rankt Dokumente mit Cross-Encoder.
        
        Args:
            query: Suchanfrage
            documents: Liste von Dokumenten mit 'id', 'title', 'snippet'/'content'
            top_k: Anzahl zurückzugebender Dokumente (default: config.top_k)
            return_scores: Ob Re-Ranking-Scores zurückgegeben werden sollen
            
        Returns:
            Liste der Top-K re-rankten Dokumente, sortiert nach Relevanz
            
        Raises:
            RuntimeError: Wenn Re-Ranking nicht verfügbar ist
        """
        if not self.is_available():
            logger.warning("⚠️ Re-Ranking übersprungen - nicht verfügbar")
            return documents[:top_k or self.config.top_k]
        
        if not documents:
            return []
        
        top_k = top_k or self.config.top_k
        start_time = time.time()
        
        # Cache-Check
        cache_key = self._get_cache_key(query, [doc.get('id', '') for doc in documents])
        if self.config.enable_cache and cache_key in self._cache:
            logger.debug(f"💾 Cache-Hit für Query: {query[:50]}...")
            return self._apply_cached_ranking(documents, self._cache[cache_key], top_k)
        
        # Cross-Encoder-Scoring
        try:
            scores = self._compute_relevance_scores(query, documents)
            
            # Dokumente mit Scores kombinieren
            doc_score_pairs = list(zip(documents, scores))
            
            # Nach Score sortieren (absteigend)
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            # Optionaler Score-Threshold
            if self.config.score_threshold is not None:
                doc_score_pairs = [
                    (doc, score) for doc, score in doc_score_pairs
                    if score >= self.config.score_threshold
                ]
            
            # Top-K extrahieren
            top_docs = []
            for doc, score in doc_score_pairs[:top_k]:
                if return_scores:
                    doc = doc.copy()  # Nicht original modifizieren
                    doc['rerank_score'] = float(score)
                    doc['rerank_rank'] = len(top_docs) + 1
                top_docs.append(doc)
            
            # Cache aktualisieren
            if self.config.enable_cache:
                self._cache[cache_key] = [(doc.get('id', ''), score) for doc, score in doc_score_pairs]
            
            # Metriken loggen
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"✅ Re-Ranking abgeschlossen: {len(documents)} → {len(top_docs)} Dokumente "
                f"({duration_ms:.1f}ms)"
            )
            
            if top_docs:
                logger.debug(
                    f"📊 Top-Scores: "
                    f"#1: {top_docs[0].get('rerank_score', 0):.3f}, "
                    f"#{len(top_docs)}: {top_docs[-1].get('rerank_score', 0):.3f}"
                )
            
            return top_docs
            
        except Exception as e:
            logger.error(f"❌ Re-Ranking fehlgeschlagen: {e}", exc_info=True)
            # Fallback auf ursprüngliche Reihenfolge
            return documents[:top_k]
    
    def _compute_relevance_scores(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> List[float]:
        """
        Berechnet Relevanz-Scores mit Cross-Encoder.
        
        Args:
            query: Suchanfrage
            documents: Dokumente
            
        Returns:
            Liste von Relevanz-Scores (ein Score pro Dokument)
        """
        # Query-Document-Paare erstellen
        pairs = []
        for doc in documents:
            # Text aus verschiedenen Feldern extrahieren
            doc_text = self._extract_document_text(doc)
            pairs.append([query, doc_text])
        
        # Batch-Prediction mit Cross-Encoder
        scores = self.model.predict(
            pairs,
            batch_size=self.config.batch_size,
            show_progress_bar=False
        )
        
        return scores.tolist()
    
    def _extract_document_text(self, doc: Dict[str, Any]) -> str:
        """
        Extrahiert relevanten Text aus Dokument für Re-Ranking.
        
        Priorität:
        1. snippet (optimiert für Suche)
        2. title + snippet
        3. content (fallback)
        
        Args:
            doc: Dokument-Dictionary
            
        Returns:
            Extrahierter Text
        """
        # Snippet bevorzugen (meist schon relevanter Auszug)
        if 'snippet' in doc and doc['snippet']:
            snippet = doc['snippet']
            # Optional: Titel hinzufügen für mehr Kontext
            if 'title' in doc and doc['title']:
                return f"{doc['title']}: {snippet}"
            return snippet
        
        # Fallback: Content
        if 'content' in doc and doc['content']:
            content = doc['content']
            # Auf maximale Länge beschränken
            max_chars = self.config.max_length * 4  # ~4 chars pro Token
            if len(content) > max_chars:
                content = content[:max_chars] + "..."
            
            if 'title' in doc and doc['title']:
                return f"{doc['title']}: {content}"
            return content
        
        # Fallback: Nur Titel
        if 'title' in doc and doc['title']:
            return doc['title']
        
        # Letzter Fallback
        return doc.get('id', 'Untitled Document')
    
    def _get_cache_key(self, query: str, doc_ids: List[str]) -> str:
        """Erstellt Cache-Key aus Query und Dokument-IDs."""
        import hashlib
        key_str = f"{query}:{','.join(sorted(doc_ids))}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _apply_cached_ranking(
        self,
        documents: List[Dict[str, Any]],
        cached_scores: List[Tuple[str, float]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Wendet gecachtes Ranking auf Dokumente an."""
        # Dokumente nach ID indexieren
        doc_by_id = {doc.get('id', ''): doc for doc in documents}
        
        # Nach gecachten Scores sortieren
        ranked_docs = []
        for doc_id, score in cached_scores[:top_k]:
            if doc_id in doc_by_id:
                doc = doc_by_id[doc_id].copy()
                doc['rerank_score'] = score
                doc['rerank_rank'] = len(ranked_docs) + 1
                ranked_docs.append(doc)
        
        return ranked_docs
    
    def clear_cache(self) -> None:
        """Leert den Re-Ranking-Cache."""
        self._cache.clear()
        logger.info("🗑️ Re-Ranking-Cache geleert")
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über Re-Ranking-Service zurück."""
        return {
            "available": self.is_available(),
            "model_name": self.config.model_name if self._model_loaded else None,
            "cache_enabled": self.config.enable_cache,
            "cache_size": len(self._cache),
            "config": {
                "top_k": self.config.top_k,
                "initial_k": self.config.initial_k,
                "batch_size": self.config.batch_size,
                "max_length": self.config.max_length,
            }
        }


# ============================================================================
# SINGLETON PATTERN
# ============================================================================

_reranking_service: Optional[ReRankingService] = None


def get_reranking_service(
    config: Optional[ReRankingConfig] = None,
    force_reload: bool = False
) -> ReRankingService:
    """
    Holt globale Re-Ranking-Service-Instanz (Singleton).
    
    Args:
        config: Optionale Konfiguration (nur beim ersten Aufruf)
        force_reload: Erzwingt Neuinstanziierung
        
    Returns:
        Re-Ranking-Service-Instanz
    """
    global _reranking_service
    
    if _reranking_service is None or force_reload:
        _reranking_service = ReRankingService(config)
        logger.info("✅ Re-Ranking-Service (Singleton) initialisiert")
    
    return _reranking_service


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def rerank_documents_simple(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Vereinfachte Re-Ranking-Funktion für direkten Aufruf.
    
    Args:
        query: Suchanfrage
        documents: Liste von Dokumenten
        top_k: Anzahl zurückzugebender Dokumente
        
    Returns:
        Top-K re-rankte Dokumente
    """
    service = get_reranking_service()
    return await service.rerank_documents(query, documents, top_k=top_k)


if __name__ == "__main__":
    """Test-Beispiel für Re-Ranking-Service"""
    import asyncio
    
    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test-Dokumente
    test_docs = [
        {
            "id": "doc1",
            "title": "Python Einführung",
            "snippet": "Python ist eine interpretierte Hochsprache für allgemeine Programmierung."
        },
        {
            "id": "doc2",
            "title": "JavaScript Grundlagen",
            "snippet": "JavaScript ist eine Skriptsprache für dynamische Webseiten."
        },
        {
            "id": "doc3",
            "title": "Python Best Practices",
            "snippet": "Bewährte Methoden für sauberen und wartbaren Python-Code."
        },
        {
            "id": "doc4",
            "title": "Machine Learning mit Python",
            "snippet": "Python ist die führende Sprache für Machine Learning und Data Science."
        },
    ]
    
    async def test_reranking():
        """Test-Funktion"""
        query = "Python Programmierung lernen"
        
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}\n")
        
        print("Ursprüngliche Reihenfolge:")
        for i, doc in enumerate(test_docs, 1):
            print(f"  {i}. {doc['title']}")
        
        # Re-Ranking
        reranked = await rerank_documents_simple(query, test_docs, top_k=3)
        
        print("\nNach Re-Ranking:")
        for doc in reranked:
            score = doc.get('rerank_score', 0)
            print(f"  {doc.get('rerank_rank')}. {doc['title']} (Score: {score:.3f})")
        
        # Statistiken
        service = get_reranking_service()
        stats = service.get_stats()
        print(f"\nService-Statistiken:")
        print(f"  Verfügbar: {stats['available']}")
        print(f"  Modell: {stats['model_name']}")
        print(f"  Top-K: {stats['config']['top_k']}")
    
    # Test ausführen
    asyncio.run(test_reranking())
