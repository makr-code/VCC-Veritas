"""
VERITAS Query Service
=====================

Zentrale Business Logic für Query-Processing.

Unterstützt alle Query-Modi:
- RAG (Retrieval-Augmented Generation)
- Hybrid Search (BM25 + Dense + RRF)
- Streaming (Progress Updates)
- Agent (Multi-Agent Pipeline)
- Ask (Direct LLM)

Immer: UnifiedResponse mit IEEE Citations
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

# Import Pipeline Request/Response
from backend.agents.veritas_intelligent_pipeline import IntelligentPipelineRequest, IntelligentPipelineResponse
from backend.models.enums import QueryMode, SourceType
from backend.models.request import UnifiedQueryRequest
from backend.models.response import UnifiedResponse, UnifiedResponseMetadata, UnifiedSourceMetadata

# Import RAG Service for Hybrid Search
from backend.services.rag_service import (
    HybridSearchResult,
    RAGService,
    RankingStrategy,
    SearchFilters,
    SearchMethod,
    SearchWeights,
)

# Import Reranker Service for Semantic Re-Ranking
from backend.services.reranker_service import RerankerService, RerankingResult, ScoringMode

# Import JSON Extractor
from backend.utils.json_extractor import (
    extract_json_from_text,
    extract_next_steps,
    extract_related_topics,
    format_next_steps_as_markdown,
)

logger = logging.getLogger(__name__)


class QueryService:
    """
    🎯 Zentrale Query-Processing-Logik

    Eine Methode für ALLE Query-Typen → UnifiedResponse
    """

    def __init__(self, uds3=None, pipeline=None, streaming=None):
        """
        Initialize Query Service

        Args:
            uds3: UDS3 PolyglotManager (v2.0.0)
            pipeline: IntelligentMultiAgentPipeline
            streaming: StreamingService
        """
        self.uds3 = uds3
        self.pipeline = pipeline
        self.streaming = streaming

        # Initialize RAG Service for Hybrid Search
        self.rag_service = None
        if uds3:
            try:
                # RAGService nutzt UDS3 PolyglotManager intern (Auto-Config)
                # Keine Parameter nötig - strikte Trennung der Zuständigkeiten
                self.rag_service = RAGService()
                logger.info("✅ RAGService initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ RAGService initialization failed: {e}")
                logger.warning("   Hybrid mode will use fallback to RAG mode")

        # Initialize Reranker Service for Semantic Re-Ranking
        self.reranker_service = None
        try:
            self.reranker_service = RerankerService(
                model_name="llama3.1:8b", scoring_mode=ScoringMode.COMBINED, temperature=0.1
            )
            logger.info("✅ RerankerService initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ RerankerService initialization failed: {e}")
            logger.warning("   Re-ranking will be disabled")

        logger.info("✅ QueryService initialized")
        logger.info(f"   UDS3: {'Available' if uds3 else 'Mock Mode'}")
        logger.info(f"   Pipeline: {'Available' if pipeline else 'Mock Mode'}")
        logger.info(f"   Streaming: {'Available' if streaming else 'Disabled'}")
        logger.info(f"   RAGService: {'Available' if self.rag_service else 'Not Available'}")
        logger.info(f"   RerankerService: {'Available' if self.reranker_service else 'Not Available'}")

    async def process_query(self, request: UnifiedQueryRequest) -> UnifiedResponse:
        """
        🎯 EINE Methode für ALLE Query-Typen

        Args:
            request: UnifiedQueryRequest mit mode-spezifischen Parametern

        Returns:
            UnifiedResponse (immer gleiche Struktur)
        """
        start_time = time.time()
        session_id = request.session_id or self._generate_session_id()

        logger.info(f"Processing query: mode={request.mode}, session={session_id}")
        logger.debug(f"Query: {request.query[:100]}...")

        # Route based on mode
        try:
            if request.mode == QueryMode.RAG:
                result = await self._process_rag(request)
            elif request.mode == QueryMode.HYBRID:
                result = await self._process_hybrid(request)
            elif request.mode == QueryMode.STREAMING:
                result = await self._process_streaming(request, session_id)
            elif request.mode == QueryMode.AGENT:
                result = await self._process_agent(request)
            elif request.mode == QueryMode.ASK:
                result = await self._process_ask(request)
            else:
                # Fallback für Domain-spezifische Modi (VPB, COVINA, etc.)
                result = await self._process_rag(request)

            duration = time.time() - start_time

            # Build unified response
            response = UnifiedResponse(
                content=result.get("content") or result.get("response_text", ""),  # ✅ Try both keys
                sources=self._normalize_sources(result.get("sources", [])),
                metadata=UnifiedResponseMetadata(
                    model=request.model,
                    mode=request.mode,
                    duration=duration,
                    tokens_used=result.get("tokens_used"),
                    sources_count=len(result.get("sources", [])),
                    complexity=result.get("complexity"),
                    domain=result.get("domain"),
                    agents_involved=result.get("agents_involved"),
                    search_method=result.get("search_method"),
                    rerank_applied=result.get("rerank_applied"),
                    stream_enabled=request.mode == QueryMode.STREAMING,
                    quality_score=result.get("quality_score"),
                    confidence=result.get("confidence"),
                ),
                session_id=session_id,
                agent_results=result.get("agent_results"),
                external_data=result.get("external_data"),
                quality_metrics=result.get("quality_metrics"),
                processing_details={
                    **(result.get("processing_details") or {}),
                    "json_metadata": result.get("json_metadata"),  # 🆕 Extracted JSON (next_steps, related_topics)
                }
                if result.get("json_metadata")
                else result.get("processing_details"),
            )

            logger.info(f"Query completed: duration={duration:.2f}s, sources={len(response.sources)}")
            return response

        except Exception as e:
            logger.error(f"Query processing error: {e}", exc_info=True)
            # Return error as response
            return await self._generate_error_response(request, session_id, str(e))

    def _normalize_sources(self, sources: List[Dict]) -> List[UnifiedSourceMetadata]:
        """
        Normalisiert Sources auf IEEE-Standard (35+ Felder)

        Funktioniert für:
        - RAG Sources (UDS3 Documents)
        - Hybrid Search Results
        - Agent Pipeline Results
        - Mock Sources

        Args:
            sources: Liste von Source-Dictionaries

        Returns:
            Liste von UnifiedSourceMetadata (IEEE-Standard)
        """
        normalized = []

        for idx, src in enumerate(sources, start=1):
            try:
                # Ensure numeric ID (not "src_1")
                if "id" not in src or str(src["id"]).startswith("src_"):
                    src["id"] = str(idx)

                # Ensure required fields
                if "title" not in src:
                    src["title"] = f"Dokument {idx}"

                if "type" not in src:
                    src["type"] = SourceType.DOCUMENT

                # Create UnifiedSourceMetadata (extra="allow" accepts all fields)
                normalized.append(UnifiedSourceMetadata(**src))

            except Exception as e:
                logger.warning(f"Failed to normalize source {idx}: {e}")
                # Fallback: minimal source
                normalized.append(UnifiedSourceMetadata(id=str(idx), title=f"Dokument {idx}", type=SourceType.DOCUMENT))

        return normalized

    async def _process_rag(self, request: UnifiedQueryRequest) -> Dict[str, Any]:
        """
        RAG Processing via Intelligent Multi-Agent Pipeline
        """
        logger.debug("Processing RAG query...")

        if self.pipeline:
            try:
                # Build IntelligentPipelineRequest
                pipeline_request = IntelligentPipelineRequest(
                    query_id=str(uuid.uuid4()),
                    query_text=request.query,
                    session_id=request.session_id,
                    enable_llm_commentary=True,
                    enable_real_time_updates=False,
                    enable_supervisor=False,
                    metadata={"model": request.model, "temperature": request.temperature, "max_tokens": request.max_tokens},
                )

                # Call correct method: process_intelligent_query
                result: IntelligentPipelineResponse = await self.pipeline.process_intelligent_query(pipeline_request)

                # Convert agent_results from Dict to List[Dict]
                agent_results_list = []
                if result.agent_results and isinstance(result.agent_results, dict):
                    for agent_name, agent_data in result.agent_results.items():
                        agent_results_list.append({"agent_name": agent_name, **agent_data})

                # Convert to UnifiedResponse format
                # JSON-Extraktion passiert bereits im Ollama Client
                return {
                    "response_text": result.response_text,  # ✅ Bereits ohne JSON
                    "confidence_score": result.confidence_score,
                    "sources": result.sources,
                    "rag_context": result.rag_context,
                    "agent_results": agent_results_list,  # ✅ List instead of Dict
                }
            except Exception as e:
                logger.error(f"Pipeline error: {e}", exc_info=True)
                return await self._generate_mock_response(request, "rag")
        else:
            # Mock fallback
            return await self._generate_mock_response(request, "rag")

    async def _process_hybrid(self, request: UnifiedQueryRequest) -> Dict[str, Any]:
        """
        Hybrid Search (BM25 + Dense + RRF)

        Combines Vector (semantic), Graph (relationships), and Relational (metadata) search
        with Reciprocal Rank Fusion for optimal result ranking.
        """
        logger.debug("Processing Hybrid Search query...")

        # Check if RAG Service is available
        if not self.rag_service:
            logger.warning("RAGService not available, falling back to RAG mode")
            return await self._process_rag(request)

        try:
            # Configure search weights (can be customized via request params)
            weights = SearchWeights(
                vector_weight=0.6,  # Semantic similarity (primary)
                graph_weight=0.2,  # Relationship relevance
                relational_weight=0.2,  # Metadata matching
            )

            # Configure search filters
            filters = SearchFilters(
                max_results=request.max_results or 20, min_relevance=0.5, metadata_filters={}  # Minimum relevance threshold
            )

            # Extract additional filters from request if available
            if hasattr(request, "filters") and request.filters:
                filters.metadata_filters = request.filters

            # Perform hybrid search
            logger.info(f"🔍 Executing hybrid search: query='{request.query}', weights={weights}")
            hybrid_result: HybridSearchResult = self.rag_service.hybrid_search(
                query=request.query, weights=weights, filters=filters, ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION
            )

            logger.info(
                f"✅ Hybrid search completed: {len(hybrid_result.results)} results in {hybrid_result.execution_time_ms:.2f}ms"
            )
            logger.debug(f"   Methods used: {[m.value for m in hybrid_result.search_methods_used]}")
            logger.debug(f"   Ranking: {hybrid_result.ranking_strategy.value}")

            # Apply semantic re-ranking if enabled and available
            enable_reranking = getattr(request, "enable_reranking", True)  # Default: enabled
            if enable_reranking and self.reranker_service and hybrid_result.results:
                try:
                    hybrid_result = await self._apply_reranking(hybrid_result, request.query)
                except Exception as e:
                    logger.warning(f"Re-ranking failed, using original scores: {e}")

            # Convert to UnifiedResponse format
            return self._convert_hybrid_result_to_response(hybrid_result, request)

        except Exception as e:
            logger.error(f"Hybrid search error: {e}", exc_info=True)
            logger.warning("Falling back to RAG mode")
            return await self._process_rag(request)

    async def _process_streaming(self, request: UnifiedQueryRequest, session_id: str) -> Dict[str, Any]:
        """
        Streaming Processing mit Progress Updates
        """
        logger.debug("Processing Streaming query...")

        # TODO: Implement Streaming via StreamingService
        # For now: use RAG and simulate streaming
        return await self._process_rag(request)

    async def _process_agent(self, request: UnifiedQueryRequest) -> Dict[str, Any]:
        """
        Agent-based Processing
        """
        logger.debug("Processing Agent query...")

        # TODO: Implement dedicated Agent Query Processing
        # For now: use pipeline
        return await self._process_rag(request)

    async def _process_ask(self, request: UnifiedQueryRequest) -> Dict[str, Any]:
        """
        Simple Ask (Direct LLM ohne RAG)
        """
        logger.debug("Processing Simple Ask query...")

        # TODO: Implement Direct LLM Call
        # For now: mock
        return {"content": f"Mock - Antwort auf: {request.query}", "sources": [], "tokens_used": 150, "complexity": "basic"}

    async def _apply_reranking(self, hybrid_result: HybridSearchResult, query: str, top_k: int = 20) -> HybridSearchResult:
        """
        Apply semantic re-ranking to hybrid search results

        Uses LLM-based scoring to improve result relevance.

        Args:
            hybrid_result: Original hybrid search results
            query: User's search query
            top_k: Number of results to re-rank (default: 20)

        Returns:
            HybridSearchResult with updated relevance scores
        """
        logger.info(f"🎯 Applying semantic re-ranking to {len(hybrid_result.results)} results...")

        import time

        start_time = time.time()

        # Prepare documents for reranking
        documents = []
        for result in hybrid_result.results[:top_k]:
            documents.append(
                {
                    "document_id": result.document_id,
                    "content": result.content,
                    "relevance_score": result.relevance_score,
                    "metadata": result.metadata,
                }
            )

        # Perform reranking
        reranking_results: List[RerankingResult] = self.reranker_service.rerank(
            query=query,
            documents=documents,
            top_k=None,  # Re-rank all documents
            batch_size=5,  # Process in batches for efficiency
        )

        # Create mapping of document_id to reranking result
        rerank_map = {r.document_id: r for r in reranking_results}

        # Update scores in original results
        updated_results = []
        score_improvements = 0
        for result in hybrid_result.results:
            if result.document_id in rerank_map:
                rerank = rerank_map[result.document_id]

                # Store original score in metadata
                if not hasattr(result.metadata, "custom_fields"):
                    result.metadata.custom_fields = {}
                result.metadata.custom_fields["original_score"] = result.relevance_score
                result.metadata.custom_fields["rerank_score"] = rerank.reranked_score
                result.metadata.custom_fields["score_delta"] = rerank.score_delta
                result.metadata.custom_fields["rerank_confidence"] = rerank.confidence

                # Update relevance score with reranked score
                result.relevance_score = rerank.reranked_score

                if rerank.score_delta > 0:
                    score_improvements += 1

            updated_results.append(result)

        # Re-sort by updated scores
        updated_results.sort(key=lambda x: x.relevance_score, reverse=True)

        # Update ranks
        for idx, result in enumerate(updated_results, start=1):
            result.rank = idx

        reranking_time_ms = (time.time() - start_time) * 1000

        logger.info(f"✅ Re-ranking completed in {reranking_time_ms:.2f}ms")
        logger.info(f"   Score improvements: {score_improvements}/{len(reranking_results)}")

        # Update hybrid result
        hybrid_result.results = updated_results
        hybrid_result.execution_time_ms += reranking_time_ms

        return hybrid_result

    def _convert_hybrid_result_to_response(
        self, hybrid_result: HybridSearchResult, request: UnifiedQueryRequest
    ) -> Dict[str, Any]:
        """
        Convert HybridSearchResult to UnifiedResponse format

        Maps SearchResult to UnifiedSourceMetadata with full IEEE citation support.

        Args:
            hybrid_result: Result from RAGService.hybrid_search()
            request: Original query request

        Returns:
            Dict compatible with UnifiedResponse format
        """
        logger.debug("Converting HybridSearchResult to UnifiedResponse format...")

        # Convert search results to sources
        sources = []
        for idx, result in enumerate(hybrid_result.results[: request.max_results or 20], start=1):
            metadata = result.metadata

            # Build IEEE citation
            ieee_citation = self._build_ieee_citation(metadata)

            # Create source metadata with all required fields
            source = {
                "id": str(idx),
                "document_id": result.document_id,
                "title": metadata.title,
                "type": metadata.source_type,
                "content": result.content,
                # Scores (including re - ranking if applied)
                "relevance_score": result.relevance_score,
                "similarity_score": result.relevance_score,  # Alias for compatibility
                "score": result.relevance_score,
                "quality_score": 0.85,  # Default quality
                # Re - ranking information (if applied)
                "original_score": metadata.custom_fields.get("original_score"),
                "rerank_score": metadata.custom_fields.get("rerank_score"),
                "score_delta": metadata.custom_fields.get("score_delta"),
                "rerank_confidence": metadata.custom_fields.get("rerank_confidence"),
                "rerank_applied": "rerank_score" in metadata.custom_fields,
                # Search method info
                "search_method": result.search_method.value,
                "ranking_strategy": hybrid_result.ranking_strategy.value,
                "rank": result.rank,
                # IEEE Citation
                "ieee_citation": ieee_citation,
                # Metadata
                "authors": metadata.author or "Unbekannt",
                "year": metadata.created_at.year if metadata.created_at else None,
                "date": metadata.created_at.isoformat() if metadata.created_at else None,
                "publisher": metadata.custom_fields.get("publisher", ""),
                "file_path": metadata.file_path,
                "page_number": result.page_number,
                "page_count": metadata.page_count,
                # Additional fields for frontend
                "rechtsgebiet": metadata.custom_fields.get("rechtsgebiet", ""),
                "normtyp": metadata.custom_fields.get("normtyp", ""),
                "geltungsbereich": metadata.custom_fields.get("geltungsbereich", ""),
                "tags": metadata.tags,
                # Excerpt info
                "excerpt_start": result.excerpt_start,
                "excerpt_end": result.excerpt_end,
                # Relevance indicators
                "relevance": "High" if result.relevance_score > 0.8 else "Medium" if result.relevance_score > 0.6 else "Low",
                "impact": "High" if result.relevance_score > 0.8 else "Medium",
            }

            sources.append(source)

        # Generate summary response text
        response_text = self._generate_hybrid_summary(hybrid_result, request)

        return {
            "response_text": response_text,
            "confidence_score": self._calculate_confidence(hybrid_result),
            "sources": sources,
            "rag_context": {
                "total_results": hybrid_result.total_count,
                "returned_results": len(sources),
                "search_methods": [m.value for m in hybrid_result.search_methods_used],
                "ranking_strategy": hybrid_result.ranking_strategy.value,
                "execution_time_ms": hybrid_result.execution_time_ms,
                "weights": {
                    "vector": hybrid_result.weights.vector_weight,
                    "graph": hybrid_result.weights.graph_weight,
                    "relational": hybrid_result.weights.relational_weight,
                },
            },
            "agent_results": [],  # No agents in hybrid mode
        }

    def _build_ieee_citation(self, metadata) -> str:
        """Build IEEE-style citation from document metadata"""
        author = metadata.author or "Unbekannt"
        title = metadata.title
        year = metadata.created_at.year if metadata.created_at else "n.d."
        publisher = metadata.custom_fields.get("publisher", "")

        if publisher:
            return f"{author}, '{title}', {publisher}, {year}."
        else:
            return f"{author}, '{title}', {year}."

    def _calculate_confidence(self, hybrid_result: HybridSearchResult) -> float:
        """Calculate overall confidence score from hybrid results"""
        if not hybrid_result.results:
            return 0.0

        # Average of top 3 results
        top_scores = [r.relevance_score for r in hybrid_result.results[:3]]
        return sum(top_scores) / len(top_scores) if top_scores else 0.0

    def _generate_hybrid_summary(self, hybrid_result: HybridSearchResult, request: UnifiedQueryRequest) -> str:
        """Generate summary text for hybrid search results"""
        methods_str = ", ".join([m.value for m in hybrid_result.search_methods_used])

        summary = f"**Hybrid Search Ergebnisse** (Methoden: {methods_str})\n\n"
        summary += f"Gefunden: {hybrid_result.total_count} Dokumente "
        summary += f"(Ranking: {hybrid_result.ranking_strategy.value})\n\n"

        if hybrid_result.results:
            top_result = hybrid_result.results[0]
            summary += f"**Top-Ergebnis:** {top_result.metadata.title}\n"
            summary += f"- Relevanz: {top_result.relevance_score:.2%}\n"
            summary += f"- Methode: {top_result.search_method.value}\n\n"

            # Add excerpt from top result
            if top_result.content:
                excerpt = top_result.content[:300] + "..." if len(top_result.content) > 300 else top_result.content
                summary += f"**Auszug:**\n{excerpt}\n\n"

        summary += f"*Ausführungszeit: {hybrid_result.execution_time_ms:.2f}ms*"

        return summary

    async def _generate_mock_response(self, request: UnifiedQueryRequest, mode: str) -> Dict[str, Any]:
        """
        Generiert Mock-Response für Development/Testing

        Enthält IEEE-konforme Mock-Sources (35+ Felder)
        """
        logger.warning(f"Generating mock response for mode={mode}")

        mock_sources = [
            {
                "id": "1",
                "title": "Bundes - Immissionsschutzgesetz (BImSchG)",
                "type": "document",
                "authors": "Deutscher Bundestag",
                "ieee_citation": "Deutscher Bundestag, 'Bundes - Immissionsschutzgesetz', BGBl. I S. 1193, 2024.",
                "year": 2024,
                "publisher": "Bundesanzeiger Verlag",
                "date": "2024 - 03-15",
                "similarity_score": 0.92,
                "rerank_score": 0.95,
                "quality_score": 0.90,
                "score": 0.93,
                "impact": "High",
                "relevance": "Very High",
                "rechtsgebiet": "Umweltrecht",
                "normtyp": "Gesetz",
                "fundstelle": "BGBl. I S. 1193",
            },
            {
                "id": "2",
                "title": "4. BImSchV - Genehmigungsverfahren",
                "type": "document",
                "authors": "Bundesministerium für Umwelt",
                "year": 2023,
                "similarity_score": 0.88,
                "quality_score": 0.85,
                "impact": "High",
                "relevance": "High",
                "rechtsgebiet": "Umweltrecht",
            },
            {
                "id": "3",
                "title": "TA Luft - Technische Anleitung zur Reinhaltung der Luft",
                "type": "document",
                "year": 2021,
                "similarity_score": 0.82,
                "impact": "Medium",
                "relevance": "Medium",
            },
        ]

        return {
            "content": f"Mock - Antwort für Query: '{request.query[:50]}...'\n\nDas BImSchG regelt... [1]\n\nGenehmigungsverfahren... [2]\n\nTA Luft... [3]",
            "sources": mock_sources,
            "tokens_used": 456,
            "complexity": "standard",
            "domain": "environmental",
            "agents_involved": ["document_retrieval", "legal_framework"],
            "quality_score": 0.88,
            "confidence": 0.85,
            "processing_details": {"mode": mode, "mock": True, "message": "Mock response - Pipeline / UDS3 not available"},
        }

    async def _generate_error_response(
        self, request: UnifiedQueryRequest, session_id: str, error_message: str
    ) -> UnifiedResponse:
        """Generiert Error-Response in UnifiedResponse-Format"""

        return UnifiedResponse(
            content=f"❌ Fehler bei der Verarbeitung: {error_message}",
            sources=[],
            metadata=UnifiedResponseMetadata(model=request.model, mode=request.mode, duration=0.0, sources_count=0),
            session_id=session_id,
            processing_details={"error": True, "error_message": error_message},
        )

    def _generate_session_id(self) -> str:
        """Generiert neue Session ID"""
        return f"sess_{uuid.uuid4().hex[:12]}"
