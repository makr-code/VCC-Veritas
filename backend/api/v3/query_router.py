"""
VERITAS API v3 - Query Router

Endpoints für Query Operations:
- POST /api/v3/query/standard - Standard Query
- POST /api/v3/query/stream - Streaming Query (SSE)
- POST /api/v3/query/intelligent - Intelligent Pipeline Query

Integration mit bestehendem Backend.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncIterator, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .models import ErrorResponse, QueryMetadata, QueryRequest, QueryResponse, SourceMetadata, StatusEnum
from .service_integration import execute_query_with_pipeline, get_services_from_app, retrieve_sources_from_uds3

logger = logging.getLogger(__name__)

# Router
query_router = APIRouter(prefix="/query", tags=["Query Operations"])

# ============================================================================
# Helper Functions
# ============================================================================


def get_backend_services(request: Request) -> Dict[str, Any]:
    """
    Holt Backend-Services aus FastAPI App State.

    Args:
        request: FastAPI Request Object

    Returns:
        Dict mit Services (uds3, intelligent_pipeline, ollama, etc.)
    """
    return {
        "uds3": getattr(request.app.state, "uds3", None),
        "intelligent_pipeline": getattr(request.app.state, "intelligent_pipeline", None),
        "ollama": getattr(request.app.state, "ollama_service", None),
        "streaming": getattr(request.app.state, "streaming_service", None),
    }


def create_query_metadata(
    mode: str, model: str, duration: float, tokens_used: int = None, sources: list = None, agents: list = None
) -> QueryMetadata:
    """
    Erstellt QueryMetadata Objekt.
    """
    return QueryMetadata(
        model=model,
        mode=mode,
        duration=duration,
        tokens_used=tokens_used,
        sources_count=len(sources) if sources else 0,
        sources_metadata=sources,
        agents_involved=agents,
    )


# ============================================================================
# Endpoints
# ============================================================================


@query_router.post("/standard", response_model=QueryResponse)
async def query_standard(query_req: QueryRequest, request: Request):
    """
    Standard Query Endpoint (✨ ENHANCED WITH IEEE METADATA)

    Führt eine Standard RAG-Query aus mit Retrieval und LLM-Generation.
    Verwendet Intelligent Pipeline mit IEEE-Citation-Metadaten-Extraktion.

    Request Body:
        - query: User Query (1-10000 Zeichen)
        - mode: Query Mode (veritas, chat, vpb, covina)
        - model: LLM Model (default: llama3.2)
        - temperature: 0.0-2.0
        - max_tokens: 1-32000
        - top_p: 0.0-1.0
        - session_id: Optional Session ID

    Response:
        - content: Generated Response
        - metadata: Query Metadata mit IEEE-Citations (35+ Felder pro Source)
        - session_id: Session ID
        - timestamp: Response Timestamp

    Errors:
        - 400: Invalid Request
        - 500: Backend Error
        - 503: Service Unavailable
    """
    start_time = datetime.now()
    services = get_services_from_app(request.app.state)

    try:
        # Service Availability Check
        if not services["intelligent_pipeline"]:
            raise HTTPException(status_code=503, detail="Intelligent Pipeline unavailable")

        # ✅ INTELLIGENT PIPELINE MIT IEEE-METADATEN
        logger.info(f"🔍 Standard Query: '{query_req.query[:50]}...' (mode={query_req.mode})")

        # Execute Query mit Intelligent Pipeline
        pipeline_result = await execute_query_with_pipeline(
            query_text=query_req.query,
            intelligent_pipeline=services["intelligent_pipeline"],
            session_id=query_req.session_id,
            mode=query_req.mode,
            enable_commentary=False,
            timeout=60,
        )

        # Duration berechnen
        duration = (datetime.now() - start_time).total_seconds()

        # ✨ IEEE-Metadaten aus Pipeline (jetzt enhanced!)
        sources_metadata = []
        for src in pipeline_result.get("sources", []):
            # Pipeline gibt jetzt vollständige IEEE-Metadaten zurück
            sources_metadata.append(
                SourceMetadata(
                    id=str(src.get("id", len(sources_metadata) + 1)),
                    file=src.get("file", None),
                    page=src.get("page", None),
                    confidence=src.get("confidence", 0.0),
                    author=src.get("authors", None),  # ✨ IEEE: authors
                    title=src.get("title", None),
                    year=src.get("year", None),
                    # ✨ Alle zusätzlichen IEEE-Felder via extra="allow"
                    **{
                        k: v
                        for k, v in src.items()
                        if k not in ["id", "file", "page", "confidence", "authors", "title", "year"]
                    },
                )
            )

        # Metadata erstellen
        metadata = create_query_metadata(
            mode=query_req.mode,
            model=query_req.model,
            duration=duration,
            tokens_used=None,  # Nicht verfügbar aus Pipeline
            sources=sources_metadata,
            agents=list(pipeline_result.get("agent_results", {}).keys()),
        )

        # Session ID
        session_id = pipeline_result.get("session_id", query_req.session_id)

        logger.info(f"✅ Standard Query completed: {duration:.2f}s, {len(sources_metadata)} sources with IEEE metadata")

        return QueryResponse(
            content=pipeline_result.get("content", ""), metadata=metadata, session_id=session_id, timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Standard Query Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@query_router.post("/stream")
async def query_stream(query_req: QueryRequest, request: Request):
    """
    Streaming Query Endpoint

    Führt eine Streaming Query aus mit Server-Sent Events (SSE).

    Request Body:
        - query: User Query
        - mode: Query Mode
        - model: LLM Model
        - temperature, max_tokens, top_p
        - session_id: Optional

    Response:
        - Server-Sent Events (SSE)
        - Content-Type: text/event-stream
        - Events: token, metadata, done, error

    Event Format:
        data: {"type": "token", "content": "word"}
        data: {"type": "metadata", "data": {...}}
        data: {"type": "done", "session_id": "..."}
        data: {"type": "error", "error": "..."}
    """
    services = get_backend_services(request)

    try:
        # Service Check
        if not services["streaming"] or not services["ollama"]:
            raise HTTPException(status_code=503, detail="Streaming service unavailable")

        async def event_generator() -> AsyncIterator[str]:
            """Generator für SSE Events"""
            try:
                start_time = datetime.now()

                # TODO: Integration mit bestehendem Streaming Service
                # Hier wird die bestehende Streaming-Logic integriert

                # Platzhalter: Simuliere Streaming
                words = f"[Streaming Response für: {query_req.query}]".split()
                for word in words:
                    # Token Event
                    yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
                    await asyncio.sleep(0.1)  # Simuliere Delay

                # Metadata Event
                duration = (datetime.now() - start_time).total_seconds()
                metadata = create_query_metadata(mode=query_req.mode, model=query_req.model, duration=duration)
                yield f"data: {json.dumps({'type': 'metadata', 'data': metadata.dict()})}\n\n"

                # Done Event
                session_id = query_req.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

            except Exception as e:
                logger.error(f"❌ Streaming Error: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache - Control": "no - cache", "Connection": "keep - alive", "X - Accel-Buffering": "no"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Stream Setup Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Streaming setup failed: {str(e)}")


@query_router.post("/intelligent", response_model=QueryResponse)
async def query_intelligent(query_req: QueryRequest, request: Request):
    """
    Intelligent Pipeline Query Endpoint

    Führt eine Query mit dem Intelligent Pipeline System aus.
    Multi-Agent Orchestration, Komplexitäts-Analyse, dynamische Agent-Auswahl.

    Request Body:
        - query: User Query
        - mode: Query Mode
        - model: LLM Model
        - temperature, max_tokens, top_p
        - session_id: Optional

    Response:
        - content: Generated Response mit Agent-Insights
        - metadata: Erweiterte Metadata (agents_involved, complexity)
        - session_id: Session ID
        - timestamp: Response Timestamp

    Metadata erweitert um:
        - complexity: Query Complexity (simple, moderate, complex)
        - agents_involved: Liste verwendeter Agents
    """
    start_time = datetime.now()
    services = get_services_from_app(request.app.state)

    try:
        # Service Check
        if not services["intelligent_pipeline"]:
            raise HTTPException(status_code=503, detail="Intelligent Pipeline unavailable")

        # ✅ ECHTE BACKEND INTEGRATION mit LLM Commentary
        logger.info(f"🧠 Intelligent Query: '{query_req.query[:50]}...' (mode={query_req.mode})")

        # Execute Query mit LLM Commentary aktiviert
        pipeline_result = await execute_query_with_pipeline(
            query_text=query_req.query,
            intelligent_pipeline=services["intelligent_pipeline"],
            session_id=query_req.session_id,
            mode=query_req.mode,
            enable_commentary=True,  # ✅ LLM Commentary für Intelligent Mode
            timeout=90,  # Längerer Timeout für komplexe Queries
        )

        # Duration berechnen
        duration = (datetime.now() - start_time).total_seconds()

        # Sources formatieren
        sources_metadata = []
        for src in pipeline_result.get("sources", []):
            sources_metadata.append(
                SourceMetadata(
                    id=src.get("id", f"src_{len(sources_metadata) + 1}"),
                    file=src.get("file", None),
                    page=src.get("page", None),
                    confidence=src.get("confidence", 0.0),
                    author=src.get("author", None),
                    title=src.get("title", None),
                    year=src.get("year", None),
                )
            )

        # Agents involved
        agents_involved = list(pipeline_result.get("agent_results", {}).keys())

        # Metadata mit Agent-Info und Complexity
        metadata = create_query_metadata(
            mode=query_req.mode,
            model=query_req.model,
            duration=duration,
            tokens_used=None,
            sources=sources_metadata,
            agents=agents_involved,
        )

        # Complexity schätzen basierend auf Agent-Anzahl
        if len(agents_involved) <= 2:
            metadata.complexity = "simple"
        elif len(agents_involved) <= 4:
            metadata.complexity = "moderate"
        else:
            metadata.complexity = "complex"

        # Session ID
        session_id = pipeline_result.get("session_id", query_req.session_id)

        logger.info(
            f"✅ Intelligent Query completed: {duration:.2f}s, {len(agents_involved)} agents, complexity={metadata.complexity}"
        )

        return QueryResponse(
            content=pipeline_result.get("content", ""), metadata=metadata, session_id=session_id, timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Intelligent Query Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Intelligent query failed: {str(e)}")


__all__ = ["query_router"]
