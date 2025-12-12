"""
Checklist Endpoints for VERITAS API
===================================

FastAPI endpoints for checklist generation.

Endpoints:
- POST /api/checklist/generate - Generate a new checklist (JSON or ZIP format)
- GET /api/checklist/export/{session_id} - Export checklist as ZIP with embedded files
- GET /api/checklist/health - Health check

Integration:
- ChecklistAgent for generation
- ThemisDB for data retrieval
- Ollama LLM for intelligent generation
- Argus2 Android app compatible
- ZIP format support for embedded files (png, pdf, docx, xlsx, md, mp3, mpeg, etc.)

Author: VERITAS Development Team
Date: December 2025
"""
import io
import json
import logging
import time
import uuid
import zipfile
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from backend.models.request import ChecklistGenerationRequest
from backend.models.response import ChecklistGenerationResponse, ChecklistData

logger = logging.getLogger(__name__)

# Create router
checklist_router = APIRouter(prefix="/api/checklist", tags=["Checklist"])

# Global agent instance (will be initialized in main app)
_checklist_agent = None
_ollama_client = None


def set_checklist_agent(agent):
    """Set the global checklist agent instance."""
    global _checklist_agent
    _checklist_agent = agent
    logger.info("ChecklistAgent registered with endpoints")


def set_ollama_client(client):
    """Set the global Ollama client."""
    global _ollama_client
    _ollama_client = client
    logger.info("Ollama client registered with checklist endpoints")


def get_checklist_agent():
    """
    Dependency to get checklist agent.
    
    Returns the initialized agent or raises HTTPException if not available.
    """
    if _checklist_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Checklist agent not initialized. Please check backend configuration."
        )
    return _checklist_agent


@checklist_router.get("/health")
async def checklist_health():
    """
    Health check endpoint for checklist service.
    
    Returns:
        Service status and configuration
    """
    return {
        "status": "healthy",
        "service": "checklist_generation",
        "agent_available": _checklist_agent is not None,
        "ollama_available": _ollama_client is not None,
        "timestamp": datetime.now().isoformat()
    }


@checklist_router.post("/generate", response_model=ChecklistGenerationResponse)
async def generate_checklist(
    request: ChecklistGenerationRequest,
    agent=Depends(get_checklist_agent)
):
    """
    Generate a checklist based on topic and requirements.
    
    This endpoint creates a structured checklist in JSON format by:
    1. Querying ThemisDB for relevant documents and data
    2. Querying regulations (laws, ordinances, guidelines, DIN standards)
    3. Using Ollama LLM to generate intelligent checklist items
    4. Returning structured JSON suitable for Argus2 Android app
    
    Args:
        request: ChecklistGenerationRequest with topic and parameters
        agent: ChecklistAgent instance (injected)
    
    Returns:
        ChecklistGenerationResponse with generated checklist
    
    Raises:
        HTTPException: If generation fails
    
    Example:
        ```
        POST /api/checklist/generate
        {
            "topic": "Bauantrag für Einfamilienhaus",
            "checklist_type": "construction",
            "include_regulations": true,
            "include_themisdb": true
        }
        ```
    """
    start_time = time.time()
    
    # Generate session ID if not provided
    session_id = request.session_id or f"checklist_{uuid.uuid4().hex[:8]}"
    
    logger.info(
        f"Checklist generation request: topic='{request.topic}', "
        f"type='{request.checklist_type}', session={session_id}"
    )
    
    try:
        # Generate checklist using agent
        result = agent.generate_checklist(
            topic=request.topic,
            context=request.context,
            checklist_type=request.checklist_type,
            include_regulations=request.include_regulations,
            include_themisdb=request.include_themisdb,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Check result status
        if result.get("status") == "error":
            logger.error(f"Checklist generation failed: {result.get('error_message')}")
            raise HTTPException(
                status_code=500,
                detail=result.get("error_message", "Unknown error during checklist generation")
            )
        
        # Extract checklist data
        checklist_data = result.get("checklist", {})
        
        # Add timestamp
        if "created_at" not in checklist_data:
            checklist_data["created_at"] = datetime.now().isoformat()
        
        # Validate and create response
        try:
            # Create ChecklistData model
            checklist = ChecklistData(**checklist_data)
            
            response = ChecklistGenerationResponse(
                status="success",
                checklist=checklist,
                metadata=result.get("metadata", {}),
                sources=result.get("sources", []),
                processing_time_ms=processing_time_ms,
                session_id=session_id
            )
            
            logger.info(
                f"Checklist generated successfully: {len(checklist.categories)} categories, "
                f"{sum(len(cat.items) for cat in checklist.categories)} items, "
                f"time={processing_time_ms:.0f}ms"
            )
            
            return response
        
        except ValidationError as e:
            logger.error(f"Validation error in checklist data: {e}")
            # Return with raw data if validation fails
            return ChecklistGenerationResponse(
                status="success",
                checklist=None,
                metadata={
                    "raw_checklist": checklist_data,
                    "validation_error": str(e)
                },
                sources=result.get("sources", []),
                processing_time_ms=processing_time_ms,
                session_id=session_id
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in checklist generation: {e}", exc_info=True)
        processing_time_ms = (time.time() - start_time) * 1000
        
        return ChecklistGenerationResponse(
            status="error",
            checklist=None,
            error_message=str(e),
            processing_time_ms=processing_time_ms,
            session_id=session_id
        )


@checklist_router.get("/types")
async def get_checklist_types():
    """
    Get available checklist types.
    
    Returns:
        List of supported checklist types with descriptions
    """
    from backend.agents.specialized.checklist_constants import CHECKLIST_TYPES
    
    return {
        "checklist_types": CHECKLIST_TYPES
    }


@checklist_router.get("/capabilities")
async def get_checklist_capabilities():
    """
    Get checklist agent capabilities.
    
    Returns:
        Agent capabilities and features
    """
    capabilities = {
        "data_sources": [
            "ThemisDB Documents",
            "ThemisDB Approvals",
            "Measurement Reports",
            "Regulations (Laws, Ordinances)",
            "Judgments",
            "Guidelines",
            "DIN Standards",
            "Internet Sources"
        ],
        "generation_methods": [
            "LLM-based (Ollama)",
            "Template-based (Fallback)"
        ],
        "features": [
            "Multi-source data aggregation",
            "Regulation compliance checking",
            "Intelligent item generation",
            "Legal basis references",
            "Priority assignment",
            "Time estimation",
            "Category organization",
            "JSON output format",
            "ZIP export with embedded files",
            "Markdown link support",
            "Argus2 Android compatibility"
        ],
        "supported_llm_models": [
            "llama3.2",
            "llama3",
            "mistral",
            "Other Ollama models"
        ]
    }
    
    # Add agent-specific capabilities if available
    if _checklist_agent:
        try:
            capabilities["agent_capabilities"] = _checklist_agent.get_capabilities()
            capabilities["agent_type"] = _checklist_agent.get_agent_type()
        except Exception as e:
            logger.warning(f"Could not get agent capabilities: {e}")
    
    return capabilities


# Store generated checklists for ZIP export (in-memory, could be moved to database)
# TODO: Implement cache expiration and size limits for production use
_checklist_cache = {}
_CACHE_MAX_SIZE = 1000  # Maximum number of cached checklists
_CACHE_EXPIRY_SECONDS = 3600  # 1 hour expiry


def _clean_cache():
    """Remove expired entries from cache to prevent memory overflow."""
    current_time = datetime.now()
    expired_keys = [
        key for key, value in _checklist_cache.items()
        if (current_time - value["created_at"]).total_seconds() > _CACHE_EXPIRY_SECONDS
    ]
    for key in expired_keys:
        del _checklist_cache[key]
    
    # If still too large, remove oldest entries
    if len(_checklist_cache) > _CACHE_MAX_SIZE:
        sorted_items = sorted(
            _checklist_cache.items(),
            key=lambda x: x[1]["created_at"]
        )
        for key, _ in sorted_items[:len(_checklist_cache) - _CACHE_MAX_SIZE]:
            del _checklist_cache[key]


@checklist_router.post("/generate/zip")
async def generate_checklist_zip(
    request: ChecklistGenerationRequest,
    agent=Depends(get_checklist_agent)
):
    """
    Generate a checklist and return it as a consolidated ZIP file.
    
    The ZIP file contains:
    - checklist.json: The generated checklist in JSON format
    - Any embedded files referenced in the request (if provided)
    - Referenced files from ThemisDB (if available)
    
    This endpoint supports the consolidated ZIP format for Argus2 Android app,
    where additional files (png, pdf, docx, xlsx, md, mp3, mpeg, etc.) can be
    included and linked via markdown in both the question and response.
    
    Args:
        request: ChecklistGenerationRequest with optional attachments and embedded_markdown
    
    Returns:
        StreamingResponse with application/zip content
    
    Example request with embedded files:
        ```json
        {
            "topic": "Bauantrag für Einfamilienhaus",
            "checklist_type": "construction",
            "embedded_markdown": "Siehe Grundriss: ![Grundriss](grundriss.png)\\n[Lageplan PDF](lageplan.pdf)",
            "attachments": ["grundriss.png", "lageplan.pdf"]
        }
        ```
    """
    start_time = time.time()
    session_id = request.session_id or f"checklist_{uuid.uuid4().hex[:8]}"
    
    logger.info(
        f"Checklist ZIP generation request: topic='{request.topic}', "
        f"type='{request.checklist_type}', session={session_id}"
    )
    
    # Clean cache before adding new entry
    _clean_cache()
    
    try:
        # Generate checklist using agent (same as regular endpoint)
        result = agent.generate_checklist(
            topic=request.topic,
            context=request.context,
            checklist_type=request.checklist_type,
            include_regulations=request.include_regulations,
            include_themisdb=request.include_themisdb,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("error_message", "Unknown error during checklist generation")
            )
        
        checklist_data = result.get("checklist", {})
        
        # Add timestamp
        if "created_at" not in checklist_data:
            checklist_data["created_at"] = datetime.now().isoformat()
        
        # Add embedded markdown if provided in request
        if request.embedded_markdown:
            checklist_data["markdown_content"] = request.embedded_markdown
        
        # Extract file references from markdown
        embedded_files = []
        if request.attachments:
            embedded_files.extend(request.attachments)
        
        checklist_data["embedded_files"] = embedded_files
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add checklist JSON
            checklist_json = json.dumps(checklist_data, indent=2, ensure_ascii=False)
            zip_file.writestr("checklist.json", checklist_json)
            
            # Add metadata
            metadata = {
                "session_id": session_id,
                "generated_at": datetime.now().isoformat(),
                "processing_time_ms": processing_time_ms,
                "topic": request.topic,
                "checklist_type": request.checklist_type,
                "sources": result.get("sources", []),
                "embedded_files": embedded_files
            }
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            # Add README with instructions
            readme_content = f"""# VERITAS Checklist Export
            
## Contents

- `checklist.json`: Generated checklist in JSON format
- `metadata.json`: Generation metadata and session information
{f"- Embedded files: {', '.join(embedded_files)}" if embedded_files else ""}

## Checklist Details

- **Topic**: {request.topic}
- **Type**: {request.checklist_type}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Session ID**: {session_id}

## Embedded Files

The checklist may contain markdown references to embedded files.
These files should be placed in the same directory as the checklist.json.

Supported file formats:
- Images: png, jpg, jpeg, gif, svg
- Documents: pdf, docx, xlsx, txt, md
- Media: mp3, mp4, mpeg, wav

## Markdown Links

Embedded files are referenced using markdown syntax:
- Images: `![Alt text](filename.png)`
- Documents: `[Link text](filename.pdf)`

## Argus2 Android App

This ZIP format is designed for the Argus2 Android app.
Import the entire ZIP file to preserve all references and embedded content.
"""
            zip_file.writestr("README.md", readme_content)
            
            # Note: Actual file attachments would need to be provided via multipart/form-data
            # or fetched from storage. For now, we create placeholders for referenced files.
            if embedded_files:
                for filename in embedded_files:
                    # Preserve original filename, just add .placeholder suffix for clarity
                    placeholder_content = f"# Placeholder for {filename}\n\nThis file should be provided separately or fetched from storage."
                    zip_file.writestr(f"attachments/{filename}.placeholder", placeholder_content)
        
        zip_buffer.seek(0)
        
        # Cache the checklist for later retrieval
        _checklist_cache[session_id] = {
            "checklist": checklist_data,
            "metadata": metadata,
            "created_at": datetime.now()
        }
        
        logger.info(f"Checklist ZIP generated successfully: session={session_id}, size={len(zip_buffer.getvalue())} bytes")
        
        # Return ZIP file as streaming response (use zip_buffer directly, no extra copy)
        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=checklist_{session_id}.zip",
                "X-Session-ID": session_id,
                "X-Processing-Time-MS": str(int(processing_time_ms))
            }
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in ZIP generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating checklist ZIP: {str(e)}"
        )


@checklist_router.get("/export/{session_id}")
async def export_checklist_zip(session_id: str):
    """
    Export a previously generated checklist as a ZIP file.
    
    This endpoint retrieves a checklist from the cache and returns it as a
    consolidated ZIP file with embedded files and markdown references.
    
    Args:
        session_id: Session ID of the checklist to export (format: checklist_XXXXXXXX)
    
    Returns:
        StreamingResponse with application/zip content
    
    Example:
        ```
        GET /api/checklist/export/checklist_abc12345
        ```
    """
    # Validate session_id format to prevent path traversal
    import re
    if not re.match(r'^checklist_[a-f0-9]{8}$', session_id):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid session_id format. Expected format: checklist_XXXXXXXX (hex)"
        )
    
    logger.info(f"Exporting checklist ZIP: session={session_id}")
    
    # Check if checklist exists in cache
    if session_id not in _checklist_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Checklist with session_id '{session_id}' not found. Generate a checklist first."
        )
    
    try:
        cached_data = _checklist_cache[session_id]
        checklist_data = cached_data["checklist"]
        metadata = cached_data["metadata"]
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add checklist JSON
            checklist_json = json.dumps(checklist_data, indent=2, ensure_ascii=False)
            zip_file.writestr("checklist.json", checklist_json)
            
            # Add metadata
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            # Add README
            readme_content = f"""# VERITAS Checklist Export

## Session Information

- **Session ID**: {session_id}
- **Generated**: {metadata.get('generated_at', 'Unknown')}
- **Topic**: {metadata.get('topic', 'Unknown')}
- **Type**: {metadata.get('checklist_type', 'Unknown')}

## Contents

- `checklist.json`: Generated checklist
- `metadata.json`: Session metadata

## Argus2 Android App Compatible

Import this ZIP file directly into the Argus2 Android app.
"""
            zip_file.writestr("README.md", readme_content)
        
        zip_buffer.seek(0)
        
        logger.info(f"Checklist ZIP exported successfully: session={session_id}")
        
        # Use zip_buffer directly, no extra copy
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=checklist_{session_id}.zip",
                "X-Session-ID": session_id
            }
        )
    
    except Exception as e:
        logger.error(f"Error exporting checklist ZIP: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting checklist: {str(e)}"
        )
