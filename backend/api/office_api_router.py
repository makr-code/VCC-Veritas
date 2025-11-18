"""
VERITAS Office API Endpoints
=============================

Office Add-in Integration mit versioniertem JSON-Schema.
Request/Response mit Metadaten-Wrapper und embedded Markdown.

Endpoints:
    POST /api/office/query - Office Add-in Query

Author: VERITAS System
Date: 2025-11-01
"""

import logging
import uuid
from datetime import datetime
<<<<<<< Updated upstream
from fastapi import APIRouter, HTTPException, Depends
=======

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
>>>>>>> Stashed changes
from fastapi.responses import JSONResponse

from backend.models.office_api_schema import (
    OfficeAPIRequest,
    OfficeAPIResponse,
    OfficeResponseContent,
    OfficeResponseMetadata,
    OfficeResponseError,
    OfficeCitation,
    map_unified_to_office_response
)
from backend.models.request import UnifiedQueryRequest
from backend.models.enums import QueryMode
from backend.services.query_service import QueryService
from backend.agents.veritas_ollama_client import VeritasOllamaClient
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/office", tags=["Office Add-in"])


# ============================================================================
# Dependency: Get QueryService
# ============================================================================

async def get_query_service() -> QueryService:
    """Get QueryService from app state"""
    from backend.app import app
    if not hasattr(app.state, 'query_service'):
        raise HTTPException(
            status_code=503,
            detail="QueryService not initialized"
        )
    return app.state.query_service


# ============================================================================
# POST /api/office/query
# ============================================================================

@router.post(
    "/query",
    response_model=OfficeAPIResponse,
    summary="Office Add-in Query",
    description="""
    📝 Versionierter Endpoint für Office Add-ins (Word/Excel/PowerPoint/Outlook)
    
    Request:
        - version: API Version (1.0)
        - session_id: Session UUID (auto-generated)
        - metadata: Mode (ask/agent/edit/plan), Scope (selection/document), Host (word/excel/...)
        - content: Query, Context (Markdown), History
    
    Response:
        - version: API Version (1.0)
        - status: success|error|partial
        - metadata: Confidence, Processing Time, Model, Tokens, Sources Count
        - content: Answer (Markdown mit [1], [2] Citations), Citations, Suggestions
        - error: Optional Error Info
    
    Features:
        - Versionierung (Breaking Changes sicher)
        - Metadaten-Trennung (Business Logic ≠ Payload)
        - Embedded Markdown (sauber im content.answer)
        - IEEE-Standard Citations (OfficeCitation-Format)
        - Error-Handling (Retry-Logic)
    """
)
async def office_query(
    request: OfficeAPIRequest,
    query_service: QueryService = Depends(get_query_service)
) -> OfficeAPIResponse:
    """
    Office Add-in Query Endpoint
    
    Flow:
        1. Validate Request (Version, Content)
        2. Map OfficeAPIRequest → UnifiedQueryRequest
        3. Execute Query via QueryService
        4. Map UnifiedResponse → OfficeAPIResponse
        5. Return Response
    """
    
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[Office API] Request {request_id}: {request.metadata.mode} query from {request.metadata.host}")
        logger.debug(f"[Office API] Query: {request.content.query[:100]}...")
        
        # ========== Step 1: Generate Session ID ==========
        session_id = request.session_id or str(uuid.uuid4())
        
        # ========== Step 2: Map OfficeAPIRequest → UnifiedQueryRequest ==========
        
        # Determine QueryMode
<<<<<<< Updated upstream
        mode_map = {
            "ask": QueryMode.ASK,
            "agent": QueryMode.AGENT,
            "edit": QueryMode.EDIT,
            "plan": QueryMode.PLAN
        }
        query_mode = mode_map.get(request.metadata.mode.lower(), QueryMode.ASK)
        
=======
        normalized_mode = (request.metadata.mode or "ask").lower()
        mode_aliases = {
            "ask": QueryMode.ASK,
            "agent": QueryMode.AGENT,
            "edit": QueryMode.ASK,  # edit currently reuses ask flow on backend
            "plan": QueryMode.AGENT,  # plan uses agent orchestration until dedicated mode exists
        }
        query_mode = mode_aliases.get(normalized_mode, QueryMode.ASK)

        if normalized_mode not in mode_aliases:
            logger.warning(
                "[Office API] Unsupported mode '%s' requested, defaulting to ask",
                request.metadata.mode,
            )

>>>>>>> Stashed changes
        # Build query text: combine user query + context
        full_query = request.content.query
        if request.content.context:
            full_query += f"\n\n**Kontext ({request.metadata.scope}):**\n{request.content.context}"
        
        # Build UnifiedQueryRequest
        unified_request = UnifiedQueryRequest(
            query=full_query,
            mode=query_mode,
            session_id=session_id,
            conversation_history=request.content.history,
            metadata={
                "office_host": request.metadata.host,
                "office_scope": request.metadata.scope,
                "office_mode": request.metadata.mode,
                "user_context": request.metadata.user_context
            }
        )
        
        logger.debug(f"[Office API] Mapped to UnifiedQueryRequest: mode={query_mode}, session={session_id}")
        
        # ========== Step 3: Execute Query ==========
        
        start_time = datetime.now()
        
        try:
            unified_response = await query_service.process_query(unified_request)
        except Exception as query_err:
            logger.error(f"[Office API] Query execution failed: {query_err}")
            raise HTTPException(
                status_code=500,
                detail=f"Query execution failed: {str(query_err)}"
            )
        
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        logger.info(f"[Office API] Query completed in {duration_ms}ms")
        
        # ========== Step 4: Map UnifiedResponse → OfficeAPIResponse ==========
        
        office_response = map_unified_to_office_response(
            unified_response=unified_response,
            request_id=request_id,
            status="success"
        )
        
        # Override processing_time_ms with measured value
        office_response.metadata.processing_time_ms = duration_ms
        
        logger.info(f"[Office API] Response ready: {len(office_response.content.citations)} citations")
        
        return office_response
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"[Office API] Unexpected error: {e}", exc_info=True)
        
        # Build Error Response
        error_response = OfficeAPIResponse(
            version="1.0",
            request_id=request_id,
            timestamp=datetime.now(),
            status="error",
            metadata=OfficeResponseMetadata(),
            content=None,
            error=OfficeResponseError(
                code="INTERNAL_ERROR",
                message=str(e),
                retry_after_ms=None
            )
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )
<<<<<<< Updated upstream
=======

        return JSONResponse(status_code=500, content=jsonable_encoder(error_response))
>>>>>>> Stashed changes


# ============================================================================
# Health Check
# ============================================================================

@router.get(
    "/health",
    summary="Office API Health Check",
    description="Health check für Office Add-in Integration"
)
async def office_health():
    """Office API Health Check"""
<<<<<<< Updated upstream
    return {
        "status": "healthy",
        "service": "veritas-office-api",
        "version": "1.0",
        "timestamp": datetime.now().isoformat()
    }
=======
    return {"status": "healthy", "service": "veritas - office-api", "version": "1.0", "timestamp": datetime.now().isoformat()}


@router.get(
    "/capabilities",
    summary="Office Capabilities & API Documentation",
    description="""
    Vollständige API-Dokumentation für Office Add-ins (analog zu FastAPI /docs).
    
    Enthält:
    - Verfügbare Endpunkte mit Beschreibungen
    - Request/Response-Schemas und Beispiele
    - Verfügbare LLM-Modelle (Ollama)
    - API-Features und Versionen
    - Error-Codes und Retry-Strategien
    """,
)
async def office_capabilities() -> Dict[str, Any]:
    """
    Return comprehensive capabilities for Office Add-in.
    
    Bietet analog zu FastAPI /docs eine maschinenlesbare API-Beschreibung:
    - Alle verfügbaren Endpunkte
    - Request/Response-Schemas mit Beispielen
    - LLM-Modelle der Ollama-Instanz
    - Fehlerbehandlung und Retry-Strategien
    """
    from backend.app import app

    # ========== 1. API Metadata ==========
    api_metadata = {
        "version": "1.0",
        "name": "VERITAS Office API",
        "description": "Office Add-in Integration für Word, Excel, PowerPoint und Outlook",
        "timestamp": datetime.now().isoformat(),
        "base_path": "/api/office",
    }

    # ========== 2. Available Endpoints ==========
    endpoints = {
        "query": {
            "path": "/api/office/query",
            "method": "POST",
            "summary": "Office Add-in Query",
            "description": "Hauptendpoint für Queries aus Office Add-ins (ask/agent/edit/plan modes)",
            "request_schema": {
                "type": "object",
                "required": ["content"],
                "properties": {
                    "version": {"type": "string", "default": "1.0", "description": "API Version"},
                    "session_id": {"type": "string", "format": "uuid", "description": "Session UUID (optional)"},
                    "timestamp": {"type": "string", "format": "date-time", "description": "ISO 8601 timestamp"},
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "mode": {"type": "string", "enum": ["ask", "agent", "edit", "plan"], "default": "ask"},
                            "scope": {"type": "string", "enum": ["selection", "document"], "default": "selection"},
                            "host": {"type": "string", "enum": ["word", "excel", "powerpoint", "outlook"], "default": "word"},
                            "user_context": {"type": "object", "description": "Zusätzlicher Kontext (selection_length, etc.)"},
                        },
                    },
                    "content": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {"type": "string", "minLength": 1, "maxLength": 10000, "description": "Benutzerfrage"},
                            "context": {"type": "string", "description": "Markdown-formatierter Kontext (Selection/Document)"},
                            "history": {
                                "type": "array",
                                "items": {"type": "object", "properties": {"role": {"type": "string"}, "content": {"type": "string"}}},
                                "description": "Conversation History",
                            },
                        },
                    },
                },
            },
            "response_schema": {
                "type": "object",
                "properties": {
                    "version": {"type": "string"},
                    "request_id": {"type": "string", "format": "uuid"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "status": {"type": "string", "enum": ["success", "error", "partial"]},
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "processing_time_ms": {"type": "integer"},
                            "model": {"type": "string"},
                            "tokens_used": {"type": "integer"},
                            "sources_count": {"type": "integer"},
                        },
                    },
                    "content": {
                        "type": "object",
                        "properties": {
                            "answer": {"type": "string", "description": "Markdown-Antwort mit [1], [2] Citations"},
                            "format": {"type": "string", "default": "markdown"},
                            "citations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "document_id": {"type": "string"},
                                        "document_title": {"type": "string"},
                                        "excerpt": {"type": "string"},
                                        "url": {"type": "string"},
                                        "page_number": {"type": "integer"},
                                        "relevance_score": {"type": "number"},
                                    },
                                },
                            },
                            "suggestions": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "error": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "message": {"type": "string"},
                            "retry_after_ms": {"type": "integer"},
                        },
                    },
                },
            },
            "example_request": {
                "version": "1.0",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "metadata": {"mode": "ask", "scope": "selection", "host": "word", "user_context": {"selection_length": 1234}},
                "content": {
                    "query": "Was bedeutet BImSchG?",
                    "context": "**Bundes-Immissionsschutzgesetz**\n\nDas BImSchG regelt...",
                    "history": [],
                },
            },
            "example_response": {
                "version": "1.0",
                "request_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "timestamp": "2025-11-17T10:30:00Z",
                "status": "success",
                "metadata": {"confidence_score": 0.92, "processing_time_ms": 1234, "model": "llama3.1:8b", "tokens_used": 567, "sources_count": 3},
                "content": {
                    "answer": "Das **Bundes-Immissionsschutzgesetz (BImSchG)** [1] regelt den Schutz vor schädlichen Umwelteinwirkungen...",
                    "format": "markdown",
                    "citations": [
                        {
                            "document_id": "doc_123",
                            "document_title": "BImSchG Kommentar 2024",
                            "excerpt": "Das Bundes-Immissionsschutzgesetz...",
                            "page_number": 42,
                            "relevance_score": 0.95,
                        }
                    ],
                    "suggestions": ["Welche Grenzwerte gelten?", "Wie wird das Gesetz angewendet?"],
                },
            },
        },
        "upload": {
            "path": "/api/office/upload",
            "method": "POST",
            "summary": "Office Document Upload",
            "description": "Upload eines einzelnen Office-Dokuments (Word/Excel/PowerPoint) für RAG-Indexierung",
            "request_schema": {
                "type": "multipart/form-data",
                "properties": {
                    "file": {"type": "file", "required": True, "description": "Office-Dokument (.docx, .xlsx, .pptx)"},
                    "metadata": {"type": "string", "description": "Optional JSON-Metadata"},
                },
            },
            "response_schema": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "format": "uuid"},
                    "filename": {"type": "string"},
                    "file_type": {"type": "string"},
                    "size_bytes": {"type": "integer"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                    "timestamp": {"type": "string"},
                },
            },
            "example_response": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "document.docx",
                "file_type": "docx",
                "size_bytes": 45678,
                "status": "processing",
                "message": "Document uploaded successfully",
                "timestamp": "2025-11-17T10:30:00Z",
            },
        },
        "upload_batch": {
            "path": "/api/office/upload/batch",
            "method": "POST",
            "summary": "Batch Office Document Upload",
            "description": "Upload mehrerer Office-Dokumente gleichzeitig",
            "request_schema": {
                "type": "multipart/form-data",
                "properties": {"files": {"type": "array", "items": {"type": "file"}, "description": "Liste von Office-Dokumenten"}},
            },
            "response_schema": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string"},
                    "total_files": {"type": "integer"},
                    "successful": {"type": "integer"},
                    "failed": {"type": "integer"},
                    "files": {"type": "array", "items": {"type": "object"}},
                    "timestamp": {"type": "string"},
                },
            },
        },
        "job_status": {
            "path": "/api/office/jobs/{job_id}",
            "method": "GET",
            "summary": "Job Status",
            "description": "Status-Abfrage eines Ingestion-Jobs",
            "parameters": [{"name": "job_id", "in": "path", "required": True, "type": "string", "description": "Job UUID"}],
            "response_schema": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "processing", "completed", "failed"]},
                    "progress": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "total_documents": {"type": "integer"},
                    "processed_documents": {"type": "integer"},
                    "errors": {"type": "array", "items": {"type": "string"}},
                    "started_at": {"type": "string"},
                    "completed_at": {"type": "string", "nullable": True},
                },
            },
            "example_response": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "progress": 1.0,
                "total_documents": 5,
                "processed_documents": 5,
                "errors": [],
                "started_at": "2025-11-17T10:30:00Z",
                "completed_at": "2025-11-17T10:32:15Z",
            },
        },
        "jobs_list": {
            "path": "/api/office/jobs",
            "method": "GET",
            "summary": "List All Jobs",
            "description": "Liste aller Ingestion-Jobs",
            "response_schema": {"type": "array", "items": {"type": "object"}},
        },
        "job_delete": {
            "path": "/api/office/jobs/{job_id}",
            "method": "DELETE",
            "summary": "Delete Job",
            "description": "Löscht einen Job und zugehörige Daten",
            "parameters": [{"name": "job_id", "in": "path", "required": True, "type": "string"}],
        },
        "stats": {
            "path": "/api/office/stats",
            "method": "GET",
            "summary": "Ingestion Statistics",
            "description": "Statistiken über alle Ingestion-Jobs",
            "response_schema": {
                "type": "object",
                "properties": {
                    "total_jobs": {"type": "integer"},
                    "completed_jobs": {"type": "integer"},
                    "failed_jobs": {"type": "integer"},
                    "total_documents_processed": {"type": "integer"},
                    "average_processing_time_ms": {"type": "number"},
                },
            },
        },
        "health": {
            "path": "/api/office/health",
            "method": "GET",
            "summary": "Health Check",
            "description": "Health check für Office Add-in Integration",
            "response_schema": {
                "type": "object",
                "properties": {"status": {"type": "string"}, "service": {"type": "string"}, "version": {"type": "string"}, "timestamp": {"type": "string"}},
            },
            "example_response": {"status": "healthy", "service": "veritas-office-api", "version": "1.0", "timestamp": "2025-11-17T10:30:00Z"},
        },
        "capabilities": {
            "path": "/api/office/capabilities",
            "method": "GET",
            "summary": "API Capabilities",
            "description": "Dieser Endpunkt - vollständige API-Dokumentation und verfügbare Modelle",
        },
    }

    # ========== 3. LLM Models (Ollama) ==========
    ollama_info = {"available": False, "models": [], "error": None}

    ollama_client: VeritasOllamaClient | None = getattr(app.state, "ollama_client", None)
    created_local = False

    if not ollama_client:
        ollama_client = VeritasOllamaClient()
        created_local = True

    try:
        await ollama_client.initialize()
        models = await ollama_client.list_models()
        ollama_info = {"available": not ollama_client.offline_mode, "default_model": ollama_client.default_model, "models": models, "error": None}
    except Exception as e:
        ollama_info["error"] = str(e)
    finally:
        if created_local:
            try:
                await ollama_client.close()
            except Exception:
                pass

    # ========== 4. Features & Modes ==========
    features = {
        "query_modes": {
            "ask": {"description": "Standard Q&A Mode - direkte Beantwortung", "example": "Was bedeutet BImSchG?"},
            "agent": {"description": "Agent Mode - komplexe Multi-Step-Reasoning", "example": "Analysiere die rechtlichen Implikationen"},
            "edit": {"description": "Edit Mode - Textbearbeitung mit Kontext", "example": "Verbessere diesen Absatz"},
            "plan": {"description": "Plan Mode - Strukturierung und Planung", "example": "Erstelle einen Projektplan"},
        },
        "query_scopes": {
            "selection": {"description": "Nur ausgewählter Text wird berücksichtigt"},
            "document": {"description": "Gesamtes Dokument wird analysiert"},
        },
        "supported_hosts": ["word", "excel", "powerpoint", "outlook"],
        "supported_formats": ["docx", "xlsx", "pptx"],
        "content_format": "markdown",
        "citation_style": "IEEE-inspired numeric [1], [2], [3]",
        "versioning": {"current": "1.0", "breaking_changes_policy": "Version prefix in all requests"},
    }

    # ========== 5. Error Codes & Retry Strategy ==========
    error_handling = {
        "error_codes": {
            "RATE_LIMIT": {"description": "Rate limit exceeded", "http_status": 429, "retry": True, "retry_after_ms": 5000},
            "INVALID_REQUEST": {"description": "Invalid request format", "http_status": 400, "retry": False},
            "INTERNAL_ERROR": {"description": "Internal server error", "http_status": 500, "retry": True, "retry_after_ms": 2000},
            "SERVICE_UNAVAILABLE": {"description": "Service temporarily unavailable", "http_status": 503, "retry": True, "retry_after_ms": 10000},
            "UNAUTHORIZED": {"description": "Authentication required", "http_status": 401, "retry": False},
        },
        "retry_strategy": {
            "max_retries": 3,
            "backoff": "exponential",
            "base_delay_ms": 1000,
            "max_delay_ms": 30000,
            "retryable_status_codes": [429, 500, 502, 503, 504],
        },
    }

    # ========== 6. Build Complete Response ==========
    return {
        "api": api_metadata,
        "endpoints": endpoints,
        "llm": ollama_info,
        "features": features,
        "error_handling": error_handling,
    }


# ============================================================================
# GET /api/office/models
# ============================================================================


@router.get(
    "/models",
    summary="Get Available LLM Models",
    description="""
    🤖 Dynamische Liste der verfügbaren Ollama-Modelle für Office Add-ins

    Response:
        - models: Liste von verfügbaren Modell-Namen
        - default: Empfohlenes Default-Modell
        - count: Anzahl verfügbarer Modelle
    """,
)
async def get_available_models() -> Dict[str, Any]:
    """
    Holt verfügbare Ollama-Modelle für dynamische LLM-Dropdown-Population

    Returns:
        Dict mit models (List[str]), default (str), count (int)
    """
    try:
        # Hole Ollama-Modelle über VeritasOllamaClient
        ollama_client = VeritasOllamaClient()
        created_local = False

        try:
            # Prüfe ob Client bereits existiert (app.state)
            from backend.app import app

            if hasattr(app.state, "ollama_client"):
                ollama_client = app.state.ollama_client
            else:
                created_local = True

            # Hole verfügbare Modelle
            available_models = await ollama_client.list_models()

            # Extrahiere Modell-Namen
            model_names = [model.get("name", "") for model in available_models if model.get("name")]

            # Fallback auf bekannte Standard-Modelle falls Ollama nicht erreichbar
            if not model_names:
                logger.warning("No Ollama models found, using fallback defaults")
                model_names = ["llama3.1:8b", "phi3:latest", "llama3:latest"]

            # Bestimme Default-Modell (erstes in Liste oder llama3.1)
            default_model = next(
                (m for m in model_names if "llama3.1" in m.lower()), model_names[0] if model_names else "llama3.1:8b"
            )

            return {"models": model_names, "default": default_model, "count": len(model_names), "timestamp": datetime.utcnow().isoformat()}

        finally:
            if created_local:
                try:
                    await ollama_client.close()
                except Exception:
                    pass

    except Exception as e:
        logger.error(f"Failed to fetch Ollama models: {e}")
        # Fallback auf hardcodierte Modelle bei Fehler
        fallback_models = ["llama3.1:8b", "phi3:latest", "llama3:latest"]
        return {
            "models": fallback_models,
            "default": "llama3.1:8b",
            "count": len(fallback_models),
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
>>>>>>> Stashed changes
