#!/usr/bin/env python3
"""
VERITAS RAG CONTEXT SERVICE
===========================

Bereitet vereinheitlichte RAG-Kontexte für die Intelligent Multi-Agent Pipeline auf.
Erfordert UDS3-Backend - KEINE Mock-Daten-Fallbacks mehr!

Features:
- Zweistufiges Retrieval: Initial Recall → Re-Ranking Precision
- Graph-basierte Kontext-Synthese
- Normalisierte Response-Formate
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Re-Ranking-Service Import (optional)
try:
    from backend.agents.veritas_reranking_service import ReRankingConfig, get_reranking_service

    RERANKING_AVAILABLE = True
    logger.info("✅ Re-Ranking-Service verfügbar")
except ImportError:
    RERANKING_AVAILABLE = False
    logger.warning("⚠️ Re-Ranking-Service nicht verfügbar - läuft ohne Re-Ranking")

# Hybrid Retrieval Import (optional)
try:
    from backend.agents.veritas_hybrid_retrieval import HybridRetrievalConfig, HybridRetriever, create_hybrid_retriever
    from backend.agents.veritas_sparse_retrieval import get_sparse_retriever

    HYBRID_AVAILABLE = True
    logger.info("✅ Hybrid Retrieval verfügbar (Dense + Sparse + RRF)")
except ImportError:
    HYBRID_AVAILABLE = False
    logger.warning("⚠️ Hybrid Retrieval nicht verfügbar - läuft nur mit Dense Retrieval")


@dataclass
class RAGQueryOptions:
    """Optionen für die RAG-Suche."""

    limit_documents: int = 5
    include_vector: bool = True
    include_graph: bool = True
    include_relational: bool = True

    # Hybrid Retrieval Optionen
    enable_hybrid_search: bool = True  # Hybrid Search (Dense + Sparse + RRF) aktivieren
    hybrid_dense_top_k: int = 50  # Top-K für Dense Retrieval
    hybrid_sparse_top_k: int = 50  # Top-K für Sparse Retrieval
    hybrid_final_top_k: int = 20  # Top-K nach RRF-Fusion
    hybrid_dense_weight: float = 0.6  # Dense Weight für RRF
    hybrid_sparse_weight: float = 0.4  # Sparse Weight für RRF

    # Re-Ranking-Optionen
    enable_reranking: bool = True  # Re-Ranking aktivieren
    reranking_initial_k: int = 20  # Initial abgerufene Dokumente für Re-Ranking
    reranking_final_k: int = 5  # Nach Re-Ranking zurückgegebene Dokumente


class RAGContextService:
    """Kapselt den Zugriff auf RAG-Backends und normalisiert Ergebnisse."""

    def __init__(
        self,
        database_api: Any = None,
        uds3_strategy: Any = None,
        fallback_seed: int = 42,
        enable_reranking: bool = True,
        enable_hybrid_search: bool = True,
    ) -> None:
        """Initialisiert RAGContextService - UDS3 ist ERFORDERLICH!

        Args:
            database_api: Veraltet, wird ignoriert
            uds3_strategy: UDS3-Strategie (ERFORDERLICH)
            fallback_seed: Nicht mehr verwendet
            enable_reranking: Re-Ranking-Service aktivieren (default: True)
            enable_hybrid_search: Hybrid Search aktivieren (default: True)

        Raises:
            RuntimeError: Wenn uds3_strategy nicht verfügbar ist
        """
        if uds3_strategy is None:
            raise RuntimeError(
                "❌ RAGContextService erfordert UDS3!\n"
                "UDS3 Strategy ist None - System kann nicht ohne RAG-Backend arbeiten.\n"
                "Bitte stellen Sie sicher, dass UDS3 korrekt initialisiert ist."
            )

        self.database_api = database_api  # Deprecated, für Rückwärtskompatibilität
        self.uds3_strategy = uds3_strategy
        self.fallback_seed = fallback_seed  # Unused
        self._rag_available = True  # Immer True, da UDS3 erforderlich ist

        # Hybrid Retrieval initialisieren (optional)
        self.hybrid_enabled = enable_hybrid_search and HYBRID_AVAILABLE
        self.hybrid_retriever = None

        if self.hybrid_enabled:
            try:
                # Erstelle Hybrid Retriever mit UDS3 als Dense Backend
                hybrid_config = HybridRetrievalConfig(
                    dense_top_k=50,
                    sparse_top_k=50,
                    final_top_k=20,
                    dense_weight=0.6,
                    sparse_weight=0.4,
                    enable_sparse=True,
                    enable_fusion=True,
                    fallback_to_dense=True,
                )

                self.hybrid_retriever = create_hybrid_retriever(
                    dense_retriever=self.uds3_strategy, corpus=None, config=hybrid_config  # Corpus wird später indexiert
                )

                logger.info("✅ Hybrid Retrieval für RAGContextService aktiviert (Dense + Sparse + RRF)")
            except Exception as e:
                logger.warning(f"⚠️ Hybrid Retrieval konnte nicht initialisiert werden: {e}")
                self.hybrid_enabled = False

        # Re-Ranking-Service initialisieren (optional)
        self.reranking_enabled = enable_reranking and RERANKING_AVAILABLE
        self.reranking_service = None

        if self.reranking_enabled:
            try:
                self.reranking_service = get_reranking_service()
                logger.info("✅ Re-Ranking-Service für RAGContextService aktiviert")
            except Exception as e:
                logger.warning(f"⚠️ Re-Ranking-Service konnte nicht initialisiert werden: {e}")
                self.reranking_enabled = False

    async def build_context(
        self,
        query_text: str,
        user_context: Optional[Dict[str, Any]] = None,
        options: Optional[RAGQueryOptions] = None,
    ) -> Dict[str, Any]:
        """Erstellt strukturierten RAG-Kontext für die Pipeline.

        Args:
            query_text: Die Suchanfrage
            user_context: Zusätzlicher Kontext (strategy_weights, etc.)
            options: RAG-Query-Optionen

        Returns:
            Normalisierter RAG-Kontext mit documents, vector, graph, relational

        Raises:
            RuntimeError: Wenn UDS3-Query fehlschlägt
        """
        opts = options or RAGQueryOptions()
        user_context = user_context or {}
        start_ts = time.time()

        # UDS3 Query ausführen - KEIN Fallback auf Mock-Daten!
        try:
            # === HYBRID RETRIEVAL-SCHRITT (Phase 5.1) ===
            # Dreistufiges Retrieval für optimale Recall + Precision:
            # Stufe 1: Hybrid Search (Dense UDS3 + Sparse BM25 + RRF)
            # Stufe 2: Cross-Encoder Re-Ranking (Precision-optimiert)
            # Stufe 3: Kontext-Normalisierung

            hybrid_applied = False
            if self.hybrid_enabled and opts.enable_hybrid_search:
                try:
                    hybrid_start = time.time()

                    # Hybrid Retrieval: Dense + Sparse + RRF
                    hybrid_results = await self.hybrid_retriever.retrieve(
                        query=query_text,
                        top_k=opts.hybrid_final_top_k or opts.reranking_initial_k,
                        enable_sparse=True,
                        dense_params={
                            "top_k": opts.hybrid_dense_top_k,
                            "strategy_weights": user_context.get("strategy_weights"),
                        },
                        sparse_params={"top_k": opts.hybrid_sparse_top_k},
                    )

                    # Konvertiere HybridResult zu normalisiertem Format
                    raw_result = self._convert_hybrid_to_raw(hybrid_results)
                    normalized = self._normalize_result(raw_result, opts)
                    hybrid_applied = True

                    hybrid_duration = (time.time() - hybrid_start) * 1000

                    # Extrahiere Fusion-Stats
                    fusion_stats = self.hybrid_retriever.rrf.get_fusion_stats(hybrid_results) if hybrid_results else {}
                    overlap_rate = fusion_stats.get("overlap_rate", 0)

                    logger.info(
                        f"🔍 Hybrid Search: {len(hybrid_results)} Dokumente "
                        f"({hybrid_duration:.1f}ms, Overlap: {overlap_rate:.1%})"
                    )

                except Exception as e:
                    logger.warning(f"⚠️ Hybrid Retrieval fehlgeschlagen, Fallback auf Dense-Only: {e}")
                    # Fallback auf klassisches UDS3 Retrieval
                    raw_result = await self._run_unified_query(query_text, user_context, opts)
                    normalized = self._normalize_result(raw_result, opts)
            else:
                # Klassisches UDS3 Retrieval (Dense-Only)
                raw_result = await self._run_unified_query(query_text, user_context, opts)
                normalized = self._normalize_result(raw_result, opts)

            # === RE-RANKING-SCHRITT (Hyperscaler-Best-Practice) ===
            # Zweistufiges Retrieval für höhere Präzision:
            # Nach Hybrid Search: Re-Ranking für finale Top-5
            reranking_applied = False
            if self.reranking_enabled and opts.enable_reranking:
                documents = normalized.get("documents", [])
                if documents and len(documents) > 0:
                    try:
                        rerank_start = time.time()

                        # Re-Ranking mit Cross-Encoder
                        reranked_docs = await self.reranking_service.rerank_documents(
                            query=query_text, documents=documents, top_k=opts.reranking_final_k or opts.limit_documents
                        )

                        # Dokumente durch re-rankte ersetzen
                        normalized["documents"] = reranked_docs
                        reranking_applied = True

                        rerank_duration = (time.time() - rerank_start) * 1000
                        logger.info(
                            f"✨ Re-Ranking: {len(documents)} → {len(reranked_docs)} Dokumente " f"({rerank_duration:.1f}ms)"
                        )

                    except Exception as e:
                        logger.warning(f"⚠️ Re-Ranking fehlgeschlagen, verwende Original-Ranking: {e}")

            metadata = {
                "query_text": query_text,
                "backend": "uds3",
                "rag_available": True,
                "fallback_used": False,
                "hybrid_applied": hybrid_applied,
                "reranking_applied": reranking_applied,
                "duration_ms": round((time.time() - start_ts) * 1000, 2),
                "result_summary": self._summarize_result(normalized),
            }
            normalized.setdefault("meta", {}).update(metadata)

            # Log-Nachricht mit Pipeline-Info
            pipeline_info = []
            if hybrid_applied:
                pipeline_info.append("Hybrid Search")
            if reranking_applied:
                pipeline_info.append("Re-Ranking")
            pipeline_str = " → ".join(pipeline_info) if pipeline_info else "Dense-Only"

            logger.info(
                f"✅ RAG-Kontext erstellt: {len(normalized.get('documents', []))} Dokumente, "
                f"{normalized['meta']['duration_ms']}ms ({pipeline_str})"
            )
            return normalized

        except Exception as e:
            logger.error(f"❌ UDS3 Query fehlgeschlagen: {e}", exc_info=True)
            raise RuntimeError(
                "❌ RAG-Backend (UDS3) fehlgeschlagen!\n"
                f"Fehler: {e}\n"
                f"Query: '{query_text}'\n"
                "Das System kann ohne funktionierendes UDS3-Backend nicht arbeiten."
            ) from e

    async def _run_unified_query(
        self,
        query_text: str,
        user_context: Dict[str, Any],
        opts: RAGQueryOptions,
    ) -> Any:
        """Versucht verschiedene bekannte RAG-Integrationspfade aufzurufen."""

        strategy_weights = user_context.get(
            "strategy_weights",
            {"vector": 0.6, "graph": 0.25, "relational": 0.15},
        )

        # 1) UDS3 Strategie bevorzugen, sofern verfügbar
        if self.uds3_strategy is not None:
            # Prüfe auf query_across_databases (UDS3 v3.0)
            query_method = getattr(self.uds3_strategy, "query_across_databases", None)
            logger.info(f"🔍 UDS3 query_across_databases: {query_method is not None and callable(query_method)}")

            if callable(query_method):
                try:
                    # Erstelle UDS3-kompatible Parameter basierend auf strategy_weights
                    vector_params = (
                        {"query_text": query_text, "top_k": opts.limit_documents, "threshold": 0.7}
                        if strategy_weights.get("vector", 0) > 0
                        else None
                    )

                    graph_params = (
                        {"relationship_type": "RELATED_TO", "max_depth": 2} if strategy_weights.get("graph", 0) > 0 else None
                    )

                    relational_params = (
                        {"table": "documents_metadata", "limit": opts.limit_documents}
                        if strategy_weights.get("relational", 0) > 0
                        else None
                    )

                    logger.info(
                        f"📊 UDS3 Query: vector={vector_params is not None}, graph={graph_params is not None}, relational={relational_params is not None}"
                    )

                    result = query_method(
                        vector_params=vector_params,
                        graph_params=graph_params,
                        relational_params=relational_params,
                        join_strategy="union",
                        execution_mode="smart",
                    )

                    logger.info("✅ UDS3 query_across_databases erfolgreich aufgerufen")

                    if asyncio.iscoroutine(result):
                        return await result
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(None, lambda: result)
                except Exception as e:
                    logger.error(f"❌ UDS3 query_across_databases fehlgeschlagen: {e}")
                    # Weiter zum Fallback

            # Fallback: Alte unified_query Methode
            unified_query = getattr(self.uds3_strategy, "unified_query", None)
            logger.info(f"🔍 UDS3 unified_query (Fallback): {unified_query is not None and callable(unified_query)}")

            if callable(unified_query):
                try:
                    result = unified_query(query_text, strategy_weights)  # type: ignore[arg-type]
                    logger.info("✅ UDS3 unified_query (Fallback) erfolgreich aufgerufen")
                    if asyncio.iscoroutine(result):
                        return await result
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(None, lambda: result)
                except Exception as e:
                    logger.error(f"❌ UDS3 unified_query (Fallback) fehlgeschlagen: {e}")

        # 2) MultiDatabaseAPI als Fallback nutzen
        if self.database_api is not None:
            # Bevorzugt `unified_search`, ansonsten generischer `search`
            for candidate in ("unified_search", "search", "query"):
                method = getattr(self.database_api, candidate, None)
                if not callable(method):
                    continue
                result = method(query_text)
                if asyncio.iscoroutine(result):
                    return await result
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, lambda: result)

        raise RuntimeError("Keine ausführbare RAG-Schnittstelle gefunden")

    def _convert_hybrid_to_raw(self, hybrid_results: List[Any]) -> Any:
        """Konvertiert HybridResults zu UDS3-kompatiblem Raw-Format.

        Args:
            hybrid_results: Liste von HybridResult-Objekten

        Returns:
            UDS3-kompatibles Result-Objekt mit 'documents' Attribut
        """
        from dataclasses import dataclass, field
        from typing import Any, List, Optional

        @dataclass
        class Document:
            """Simpler Document-Container für Normalisierung."""

            id: Optional[str] = None
            title: str = "Unbenannt"
            snippet: str = ""
            score: float = 0.0
            source: Optional[str] = None
            tags: List[str] = field(default_factory=list)
            # Hybrid-spezifische Metadaten
            retrieval_method: str = "hybrid"
            sources: List[str] = field(default_factory=list)
            dense_score: Optional[float] = None
            sparse_score: Optional[float] = None

        @dataclass
        class RawResult:
            """Container für normalisierte Dokumente."""

            documents: List[Document] = field(default_factory=list)

        # Konvertiere HybridResults zu Document-Objekten
        documents = []
        for hr in hybrid_results:
            doc = Document(
                id=hr.doc_id,
                title=hr.metadata.get("title", "Unbenannt"),
                snippet=hr.content[:500] if hr.content else "",  # Ersten 500 Zeichen
                score=hr.score,  # RRF-Score
                source=hr.retrieval_method,
                tags=hr.metadata.get("tags", []),
                retrieval_method=hr.retrieval_method,
                sources=hr.sources,
                dense_score=hr.dense_score,
                sparse_score=hr.sparse_score,
            )
            documents.append(doc)

        return RawResult(documents=documents)

    def _normalize_result(self, raw_result: Any, opts: RAGQueryOptions) -> Dict[str, Any]:
        """Normalisiert Backend-Ergebnisse in das Pipeline-Format."""

        normalized: Dict[str, Any] = {
            "documents": [],
            "vector": {},
            "graph": {},
            "relational": {},
            "meta": {},
        }

        if not raw_result:
            return normalized

        # UnifiedResult-Objekte enthalten häufig Attribute
        documents = getattr(raw_result, "documents", None) or getattr(raw_result, "content", None)
        if isinstance(documents, list):
            for item in documents[: opts.limit_documents]:
                # ✨ BEWAHRE ALLE METADATEN (IEEE-Extended)
                # Basis-Dokument-Struktur
                doc = {
                    "id": getattr(item, "id", None) or item.get("id") if isinstance(item, dict) else None,
                    "title": getattr(item, "title", "Unbenannt")
                    if not isinstance(item, dict)
                    else item.get("title", "Unbenannt"),
                    "snippet": getattr(item, "snippet", "") if not isinstance(item, dict) else item.get("snippet", ""),
                    "relevance": float(
                        getattr(item, "score", item.get("score", 0.75))
                        if isinstance(item, dict)
                        else getattr(item, "score", 0.75)
                    ),
                    "source": getattr(item, "source", None) if not isinstance(item, dict) else item.get("source"),
                    "domain_tags": getattr(item, "tags", []) if not isinstance(item, dict) else item.get("tags", []),
                }

                # ✨ IEEE-EXTENDED: Bewahre alle zusätzlichen Metadaten aus UDS3
                if isinstance(item, dict):
                    # Füge alle zusätzlichen Felder hinzu, die UDS3 bereitstellt
                    for key, value in item.items():
                        if key not in doc:  # Nur neue Felder, keine Überschreibung
                            doc[key] = value
                else:
                    # Für Objekte: Extrahiere alle Attribute
                    for attr in dir(item):
                        if not attr.startswith("_") and attr not in doc:
                            try:
                                value = getattr(item, attr)
                                if not callable(value):
                                    doc[attr] = value
                            except:
                                pass

                normalized["documents"].append(doc)

        # Vector Resultate
        if opts.include_vector:
            vector_data = getattr(raw_result, "vector", None) or getattr(raw_result, "vector_results", None)
            if vector_data:
                normalized["vector"] = {
                    "matches": getattr(vector_data, "matches", None) or getattr(vector_data, "results", None) or vector_data,
                    "statistics": {
                        "count": len(getattr(vector_data, "matches", []) or getattr(vector_data, "results", []) or []),
                    },
                }

        # Graph Resultate
        if opts.include_graph:
            graph_data = getattr(raw_result, "graph", None) or getattr(raw_result, "graph_results", None)
            if graph_data:
                related = (
                    getattr(graph_data, "related_entities", None) or graph_data.get("related_entities")
                    if isinstance(graph_data, dict)
                    else []
                )
                normalized["graph"] = {
                    "related_entities": related or [],
                    "confidence": float(graph_data.get("confidence", 0.7)) if isinstance(graph_data, dict) else 0.7,
                }

        # Relationale Daten
        if opts.include_relational:
            rel_data = getattr(raw_result, "relational", None) or getattr(raw_result, "relational_results", None)
            if rel_data:
                metadata_hits = (
                    rel_data.get("metadata_matches")
                    if isinstance(rel_data, dict)
                    else getattr(rel_data, "metadata_matches", None)
                )
                normalized["relational"] = {
                    "metadata_hits": metadata_hits or 0,
                    "filters": rel_data.get("filters", []) if isinstance(rel_data, dict) else [],
                }

        return normalized

    @staticmethod
    def _summarize_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Erzeugt kompakten Überblick für Logs & Monitoring."""

        documents = result.get("documents", [])
        return {
            "documents": len(documents),
            "top_relevance": documents[0]["relevance"] if documents else None,
            "vector_matches": len(result.get("vector", {}).get("matches", []) or []),
            "related_entities": len(result.get("graph", {}).get("related_entities", []) or []),
        }

    def index_corpus_for_hybrid_search(self, corpus: List[Dict[str, Any]]) -> None:
        """Indexiert Corpus für BM25 Sparse Retrieval.

        Args:
            corpus: Liste von Dokumenten mit 'doc_id' und 'content'

        Beispiel:
            corpus = [
                {"doc_id": "doc1", "content": "§ 242 BGB Leistung nach Treu und Glauben"},
                {"doc_id": "doc2", "content": "DIN 18040 - 1 Barrierefreies Bauen"}
            ]
            service.index_corpus_for_hybrid_search(corpus)
        """
        if not self.hybrid_enabled:
            logger.warning("⚠️ Hybrid Search nicht aktiviert - Corpus-Indexierung übersprungen")
            return

        try:
            sparse_retriever = get_sparse_retriever()
            sparse_retriever.index_documents(corpus)
            logger.info(f"✅ BM25-Index erstellt: {len(corpus)} Dokumente indexiert")
        except Exception as e:
            logger.error(f"❌ BM25-Indexierung fehlgeschlagen: {e}")
