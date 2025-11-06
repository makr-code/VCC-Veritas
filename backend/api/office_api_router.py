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
from fastapi import APIRouter, HTTPException, Depends
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
        mode_map = {
            "ask": QueryMode.ASK,
            "agent": QueryMode.AGENT,
            "edit": QueryMode.EDIT,
            "plan": QueryMode.PLAN
        }
        query_mode = mode_map.get(request.metadata.mode.lower(), QueryMode.ASK)
        
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
            unified_response = await query_service.query(unified_request)
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
    return {
        "status": "healthy",
        "service": "veritas-office-api",
        "version": "1.0",
        "timestamp": datetime.now().isoformat()
    }
