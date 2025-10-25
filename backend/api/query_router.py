"""
VERITAS Query Router
====================

Query-Endpoints für alle Modi:
- POST /api/query - Unified Query Endpoint
- POST /api/ask - Simple Ask (Direct LLM)
- POST /api/rag - RAG Query
- POST /api/hybrid - Hybrid Search
- POST /api/stream - Streaming Query
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Request
from typing import Optional
import logging

from backend.models.request import (
    UnifiedQueryRequest,
    SimpleAskRequest,
    HybridSearchRequest,
    StreamingQueryRequest
)
from backend.models.response import UnifiedResponse
from backend.models.enums import QueryMode

logger = logging.getLogger(__name__)

query_router = APIRouter(prefix="/query", redirect_slashes=False)


# Dependency: Get QueryService from app state
def get_query_service(request: Request):
    """Get QueryService from app state"""
    return request.app.state.query_service


@query_router.post("", response_model=UnifiedResponse)
async def unified_query(
    request_body: UnifiedQueryRequest = Body(...),
    query_service = Depends(get_query_service)
) -> UnifiedResponse:
    """
    🎯 Unified Query Endpoint - Alle Modi
    
    Unterstützt:
    - mode="rag" - RAG Query
    - mode="hybrid" - Hybrid Search
    - mode="streaming" - Streaming Query
    - mode="agent" - Agent Query
    - mode="ask" - Simple Ask
    - mode="veritas" - Default VERITAS Mode
    
    Returns:
        UnifiedResponse mit IEEE Citations (35+ Felder)
    """
    logger.info(f"Unified Query: mode={request_body.mode}, query={request_body.query[:50]}...")
    
    try:
        response = await query_service.process_query(request_body)
        return response
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@query_router.post("/ask", response_model=UnifiedResponse)
async def simple_ask(
    ask_request: SimpleAskRequest = Body(..., embed=False),
    query_service = Depends(get_query_service)
) -> UnifiedResponse:
    """
    Simple Ask - Direct LLM ohne RAG
    
    Für einfache Fragen ohne Dokumenten-Retrieval.
    """
    logger.info(f"Simple Ask: {ask_request.query[:50]}...")
    
    # Convert to UnifiedQueryRequest
    unified_request = UnifiedQueryRequest(
        query=ask_request.query,
        mode=QueryMode.ASK,
        model=ask_request.model,
        temperature=ask_request.temperature,
        max_tokens=ask_request.max_tokens,
        session_id=ask_request.session_id
    )
    
    try:
        response = await query_service.process_query(unified_request)
        return response
    except Exception as e:
        logger.error(f"Ask error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@query_router.post("/rag", response_model=UnifiedResponse)
async def rag_query(
    rag_request: UnifiedQueryRequest = Body(..., embed=False),
    query_service = Depends(get_query_service)
) -> UnifiedResponse:
    """
    RAG Query - Retrieval-Augmented Generation
    
    Verwendet:
    - UDS3 Vector Database
    - Intelligent Multi-Agent Pipeline
    - IEEE Citations (35+ Felder)
    """
    logger.info(f"RAG Query: {rag_request.query[:50]}...")
    
    # Force RAG mode
    rag_request.mode = QueryMode.RAG
    
    try:
        response = await query_service.process_query(rag_request)
        return response
    except Exception as e:
        logger.error(f"RAG error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@query_router.post("/hybrid", response_model=UnifiedResponse)
async def hybrid_search(
    hybrid_request: HybridSearchRequest = Body(..., embed=False),
    query_service = Depends(get_query_service)
) -> UnifiedResponse:
    """
    🔍 Hybrid Search - Multi-Database Retrieval mit LLM Re-Ranking
    
    ## Architektur
    
    Kombiniert drei Retrieval-Methoden:
    - **Vector Search (60%)**: ChromaDB Dense Embeddings (Semantic)
    - **Graph Search (20%)**: Neo4j Knowledge Graph (Entity Relationships)
    - **Relational Search (20%)**: PostgreSQL Structured Metadata
    
    ## Ranking Strategies
    
    - **RRF (Reciprocal Rank Fusion)**: Default, robust gegen Outlier
    - **Weighted Combination**: Schneller, aber benötigt normalisierte Scores
    - **Borda Count**: Experimental, position-based
    
    ## Re-Ranking
    
    LLM-basierte semantische Neubewertung (llama3.1:8b):
    - **Relevance**: Query-Document Match
    - **Informativeness**: Information Quality
    - **Combined**: Balanced Scoring (Default)
    
    ## Request Parameters
    
    ```json
    {
        "query": "Was sind die Anforderungen für einen Bauantrag?",
        "model": "llama3.1:8b",
        "temperature": 0.1,
        "top_k": 20,
        "bm25_weight": 0.5,        # Legacy (deprecated)
        "dense_weight": 0.5,       # Legacy (deprecated)
        "enable_reranking": true,  # Enable LLM re-ranking
        "enable_rrf": true,        # Use RRF fusion
        "rrf_k": 60,               # RRF k parameter
        "session_id": "optional"
    }
    ```
    
    ## Response Format
    
    UnifiedResponse mit IEEE Citations (35+ Felder):
    
    ```json
    {
        "answer": "Ein Bauantrag nach BauGB erfordert...",
        "sources": [
            {
                "title": "§ 35 BauGB - Bauen im Außenbereich",
                "content": "...",
                "metadata": {
                    "document_id": "bauGB_35",
                    "search_method": "hybrid",
                    "ranking_strategy": "reciprocal_rank_fusion",
                    "original_score": 0.85,
                    "rerank_score": 0.92,
                    "score_delta": 0.07,
                    "rerank_confidence": 0.95,
                    "vector_rank": 1,
                    "graph_rank": 3,
                    "relational_rank": 2,
                    "rrf_score": 0.0486,
                    "execution_time_ms": 1250.5,
                    "...": "30+ more IEEE fields"
                }
            }
        ],
        "metadata": {
            "query_mode": "hybrid",
            "reranking_enabled": true,
            "total_sources": 15,
            "execution_time_ms": 5420.3
        }
    }
    ```
    
    ## Configuration
    
    Customize via Environment Variables:
    
    ```bash
    # Search Weights (must sum to 1.0)
    HYBRID_WEIGHT_VECTOR=0.6
    HYBRID_WEIGHT_GRAPH=0.2
    HYBRID_WEIGHT_RELATIONAL=0.2
    
    # Ranking Strategy
    HYBRID_RANKING_STRATEGY=reciprocal_rank_fusion
    
    # RRF Configuration
    HYBRID_RRF_K=60
    
    # Re-Ranking
    RERANKING_ENABLED=true
    RERANKING_MODEL=llama3.1:8b
    RERANKING_BATCH_SIZE=5
    ```
    
    ## Performance
    
    - **Fast Mode**: ~2s (no re-ranking)
    - **Balanced**: ~5-8s (default)
    - **Accurate**: ~10-12s (max quality)
    
    ## Use Cases
    
    - Legal document search with entity relationships
    - Complex queries requiring semantic + keyword matching
    - Research with citation networks
    - Verwaltungsrecht (BauGB, BImSchG, VwVfG, etc.)
    
    ## See Also
    
    - Developer Guide: `docs/HYBRID_SEARCH_DEVELOPER_GUIDE.md`
    - Configuration: `config/README_HYBRID_CONFIG.md`
    - Tests: `tests/backend/test_hybrid_search_*.py`
    """
    logger.info(f"Hybrid Search: {hybrid_request.query[:50]}...")
    
    # Convert to UnifiedQueryRequest
    unified_request = UnifiedQueryRequest(
        query=hybrid_request.query,
        mode=QueryMode.HYBRID,
        model=hybrid_request.model,
        temperature=hybrid_request.temperature,
        top_k=hybrid_request.top_k,
        session_id=hybrid_request.session_id,
        metadata={
            "bm25_weight": hybrid_request.bm25_weight,
            "dense_weight": hybrid_request.dense_weight,
            "enable_reranking": hybrid_request.enable_reranking,
            "enable_rrf": hybrid_request.enable_rrf,
            "rrf_k": hybrid_request.rrf_k
        }
    )
    
    try:
        response = await query_service.process_query(unified_request)
        return response
    except Exception as e:
        logger.error(f"Hybrid search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@query_router.post("/stream", response_model=UnifiedResponse)
async def streaming_query(
    stream_request: StreamingQueryRequest = Body(..., embed=False),
    query_service = Depends(get_query_service)
) -> UnifiedResponse:
    """
    Streaming Query - Mit Progress Updates
    
    Features:
    - Real-time Progress Updates via SSE
    - Intermediate Results
    - LLM Deep-thinking
    
    TODO: Implement SSE streaming response
    """
    logger.info(f"Streaming Query: {stream_request.query[:50]}...")
    
    # Convert to UnifiedQueryRequest
    unified_request = UnifiedQueryRequest(
        query=stream_request.query,
        mode=QueryMode.STREAMING,
        model=stream_request.model,
        temperature=stream_request.temperature,
        max_tokens=stream_request.max_tokens,
        session_id=stream_request.session_id,
        metadata={
            "enable_streaming": stream_request.enable_streaming,
            "enable_intermediate_results": stream_request.enable_intermediate_results,
            "enable_llm_thinking": stream_request.enable_llm_thinking
        }
    )
    
    try:
        # TODO: Return StreamingResponse instead
        response = await query_service.process_query(unified_request)
        return response
    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
