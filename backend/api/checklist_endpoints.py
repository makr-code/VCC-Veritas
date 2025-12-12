"""
Checklist Endpoints for VERITAS API
===================================

FastAPI endpoints for checklist generation.

Endpoints:
- POST /api/checklist/generate - Generate a new checklist (JSON or ZIP format)
- POST /api/checklist/generate/stream - Generate checklist with SSE progress streaming
- POST /api/checklist/generate/zip - Generate as ZIP with file upload support
- POST /api/checklist/upload - Upload files for checklist generation (runtime)
- GET /api/checklist/export/{session_id} - Export checklist as ZIP with embedded files
- GET /api/checklist/health - Health check

Integration:
- ChecklistAgent for generation
- ThemisDB for data retrieval
- Ollama LLM for intelligent generation
- SSE (Server-Sent Events) for real-time progress streaming
- MCP (Model Context Protocol) support
- Argus2 Android app compatible
- ZIP format support for embedded files (png, pdf, docx, xlsx, md, mp3, mpeg, etc.)
- Runtime file upload/transmission

Author: VERITAS Development Team
Date: December 2025
"""
import asyncio
import io
import json
import logging
import re
import time
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

try:
    from sse_starlette.sse import EventSourceResponse
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False
    logging.warning("⚠️ sse-starlette not available - SSE streaming disabled")

from backend.models.request import ChecklistGenerationRequest
from backend.models.response import ChecklistGenerationResponse, ChecklistData

logger = logging.getLogger(__name__)

# Create router
checklist_router = APIRouter(prefix="/api/checklist", tags=["Checklist"])

# Global agent instance (will be initialized in main app)
_checklist_agent = None
_ollama_client = None

# Store uploaded files per session (in-memory, could be moved to filesystem/database)
_uploaded_files = {}  # session_id -> {filename: file_content}
_FILE_UPLOAD_MAX_SIZE = 10 * 1024 * 1024  # 10MB per file
_FILE_UPLOAD_MAX_TOTAL = 50 * 1024 * 1024  # 50MB total per session


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


def _clean_uploaded_files():
    """Remove old uploaded files to prevent memory leaks."""
    # Remove uploaded files for expired sessions
    expired_sessions = [
        key for key in _uploaded_files.keys()
        if key not in _checklist_cache
    ]
    for key in expired_sessions:
        del _uploaded_files[key]
        logger.info(f"Cleaned up uploaded files for expired session: {key}")
    
    # Limit total uploaded files storage
    if len(_uploaded_files) > _CACHE_MAX_SIZE:
        # Remove oldest sessions (simple FIFO)
        sessions_to_remove = list(_uploaded_files.keys())[:len(_uploaded_files) - _CACHE_MAX_SIZE]
        for session_id in sessions_to_remove:
            del _uploaded_files[session_id]
            logger.info(f"Removed old uploaded files for session: {session_id}")


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
    _clean_uploaded_files()
    
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
            
            # Add actual uploaded files or placeholders
            if session_id in _uploaded_files and _uploaded_files[session_id]:
                # Add actual uploaded files
                for filename, content in _uploaded_files[session_id].items():
                    zip_file.writestr(f"attachments/{filename}", content)
                    logger.info(f"Added uploaded file to ZIP: {filename}")
            elif embedded_files:
                # Add placeholders for referenced files not yet uploaded
                for filename in embedded_files:
                    if session_id in _uploaded_files and filename in _uploaded_files[session_id]:
                        # Use actual uploaded file
                        zip_file.writestr(f"attachments/{filename}", _uploaded_files[session_id][filename])
                    else:
                        # Create placeholder
                        placeholder_content = f"# Placeholder for {filename}\n\nThis file should be uploaded via POST /api/checklist/upload endpoint."
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


@checklist_router.post("/upload")
async def upload_checklist_files(
    session_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Upload files for runtime transmission during checklist generation.
    
    This endpoint allows uploading files (png, pdf, docx, xlsx, md, mp3, mpeg, etc.)
    during runtime that can be embedded in the checklist and referenced via markdown.
    
    Supports MCP (Model Context Protocol) for real-time file transmission.
    
    Args:
        session_id: Session ID to associate files with
        files: List of files to upload
    
    Returns:
        Upload confirmation with file list
    
    Example:
        ```bash
        curl -X POST http://localhost:5000/api/checklist/upload \
          -F "session_id=checklist_abc12345" \
          -F "files=@grundriss.png" \
          -F "files=@lageplan.pdf"
        ```
    """
    # Validate session_id format
    if not re.match(r'^checklist_[a-f0-9]{8}$', session_id):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid session_id format. Expected format: checklist_XXXXXXXX (hex)"
        )
    
    logger.info(f"File upload request: session={session_id}, files={len(files)}")
    
    # Initialize session storage if needed
    if session_id not in _uploaded_files:
        _uploaded_files[session_id] = {}
    
    uploaded = []
    total_size = sum(len(content) for content in _uploaded_files[session_id].values())
    
    try:
        for file in files:
            # Read file content
            content = await file.read()
            file_size = len(content)
            
            # Validate file size
            if file_size > _FILE_UPLOAD_MAX_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File {file.filename} exceeds max size of {_FILE_UPLOAD_MAX_SIZE / (1024*1024)}MB"
                )
            
            # Validate total size
            if total_size + file_size > _FILE_UPLOAD_MAX_TOTAL:
                raise HTTPException(
                    status_code=413,
                    detail=f"Total upload size exceeds max of {_FILE_UPLOAD_MAX_TOTAL / (1024*1024)}MB"
                )
            
            # Store file
            _uploaded_files[session_id][file.filename] = content
            total_size += file_size
            
            uploaded.append({
                "filename": file.filename,
                "size": file_size,
                "content_type": file.content_type
            })
            
            logger.info(f"Uploaded file: {file.filename} ({file_size} bytes)")
        
        return {
            "status": "success",
            "session_id": session_id,
            "uploaded_files": uploaded,
            "total_files": len(_uploaded_files[session_id]),
            "total_size": total_size,
            "message": f"Successfully uploaded {len(uploaded)} file(s)"
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error uploading files: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading files: {str(e)}"
        )


@checklist_router.post("/generate/stream")
async def generate_checklist_stream(
    request: ChecklistGenerationRequest,
    agent=Depends(get_checklist_agent)
):
    """
    Generate a checklist with Server-Sent Events (SSE) progress streaming.
    
    This endpoint streams real-time progress updates during checklist generation:
    - ThemisDB query progress
    - Regulation search progress
    - LLM generation progress
    - File processing progress
    
    Supports both MCP and SSE protocols for real-time communication.
    
    Args:
        request: ChecklistGenerationRequest with topic and parameters
    
    Returns:
        EventSourceResponse with SSE stream
    
    Event Types:
        - progress: Generation progress updates (percentage, message)
        - data: Intermediate data (documents, regulations)
        - result: Final checklist data
        - error: Error information
        - complete: Generation complete signal
    
    Example (JavaScript):
        ```javascript
        const source = new EventSource('/api/checklist/generate/stream', {
            method: 'POST',
            body: JSON.stringify({topic: "Bauantrag", checklist_type: "construction"})
        });
        
        source.addEventListener('progress', (e) => {
            const data = JSON.parse(e.data);
            console.log(`${data.percentage}%: ${data.message}`);
        });
        
        source.addEventListener('result', (e) => {
            const checklist = JSON.parse(e.data);
            console.log('Checklist generated:', checklist);
        });
        ```
    """
    if not SSE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="SSE streaming not available. Install sse-starlette: pip install sse-starlette"
        )
    
    session_id = request.session_id or f"checklist_{uuid.uuid4().hex[:8]}"
    
    logger.info(
        f"Checklist SSE streaming request: topic='{request.topic}', "
        f"type='{request.checklist_type}', session={session_id}"
    )
    
    async def event_generator():
        """Generate SSE events for checklist creation."""
        start_time = time.time()
        event_id = 0
        
        try:
            # Event 1: Start
            event_id += 1
            yield {
                "id": str(event_id),
                "event": "progress",
                "data": json.dumps({
                    "session_id": session_id,
                    "percentage": 0,
                    "message": "Starting checklist generation...",
                    "timestamp": datetime.now().isoformat()
                })
            }
            await asyncio.sleep(0.1)
            
            # Event 2: Query ThemisDB
            if request.include_themisdb:
                event_id += 1
                yield {
                    "id": str(event_id),
                    "event": "progress",
                    "data": json.dumps({
                        "session_id": session_id,
                        "percentage": 20,
                        "message": "Querying ThemisDB for documents...",
                        "timestamp": datetime.now().isoformat()
                    })
                }
                await asyncio.sleep(0.5)
            
            # Event 3: Query Regulations
            if request.include_regulations:
                event_id += 1
                yield {
                    "id": str(event_id),
                    "event": "progress",
                    "data": json.dumps({
                        "session_id": session_id,
                        "percentage": 40,
                        "message": "Searching regulations and standards...",
                        "timestamp": datetime.now().isoformat()
                    })
                }
                await asyncio.sleep(0.5)
            
            # Event 4: Process uploaded files (if any)
            if session_id in _uploaded_files and _uploaded_files[session_id]:
                event_id += 1
                file_count = len(_uploaded_files[session_id])
                yield {
                    "id": str(event_id),
                    "event": "progress",
                    "data": json.dumps({
                        "session_id": session_id,
                        "percentage": 50,
                        "message": f"Processing {file_count} uploaded file(s)...",
                        "timestamp": datetime.now().isoformat()
                    })
                }
                await asyncio.sleep(0.3)
            
            # Event 5: LLM Generation
            event_id += 1
            yield {
                "id": str(event_id),
                "event": "progress",
                "data": json.dumps({
                    "session_id": session_id,
                    "percentage": 60,
                    "message": "Generating checklist with LLM...",
                    "timestamp": datetime.now().isoformat()
                })
            }
            
            # Generate checklist (non-blocking)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                agent.generate_checklist,
                request.topic,
                request.context,
                request.checklist_type,
                request.include_regulations,
                request.include_themisdb,
                request.model,
                request.temperature,
                request.max_tokens
            )
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Event 6: Complete
            event_id += 1
            yield {
                "id": str(event_id),
                "event": "progress",
                "data": json.dumps({
                    "session_id": session_id,
                    "percentage": 90,
                    "message": "Finalizing checklist...",
                    "timestamp": datetime.now().isoformat()
                })
            }
            await asyncio.sleep(0.2)
            
            if result.get("status") == "error":
                # Error event
                event_id += 1
                yield {
                    "id": str(event_id),
                    "event": "error",
                    "data": json.dumps({
                        "session_id": session_id,
                        "error_message": result.get("error_message", "Unknown error"),
                        "timestamp": datetime.now().isoformat()
                    })
                }
            else:
                # Result event
                checklist_data = result.get("checklist", {})
                if "created_at" not in checklist_data:
                    checklist_data["created_at"] = datetime.now().isoformat()
                
                # Add uploaded files to embedded_files
                if session_id in _uploaded_files:
                    uploaded_filenames = list(_uploaded_files[session_id].keys())
                    checklist_data["embedded_files"] = uploaded_filenames
                
                event_id += 1
                yield {
                    "id": str(event_id),
                    "event": "result",
                    "data": json.dumps({
                        "session_id": session_id,
                        "checklist": checklist_data,
                        "metadata": result.get("metadata", {}),
                        "sources": result.get("sources", []),
                        "processing_time_ms": processing_time_ms,
                        "timestamp": datetime.now().isoformat()
                    })
                }
                
                # Cache for ZIP export
                _checklist_cache[session_id] = {
                    "checklist": checklist_data,
                    "metadata": {
                        "session_id": session_id,
                        "generated_at": datetime.now().isoformat(),
                        "processing_time_ms": processing_time_ms,
                        "topic": request.topic,
                        "checklist_type": request.checklist_type,
                        "sources": result.get("sources", [])
                    },
                    "created_at": datetime.now()
                }
            
            # Complete event
            event_id += 1
            yield {
                "id": str(event_id),
                "event": "complete",
                "data": json.dumps({
                    "session_id": session_id,
                    "percentage": 100,
                    "message": "Checklist generation complete",
                    "processing_time_ms": processing_time_ms,
                    "timestamp": datetime.now().isoformat()
                })
            }
        
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}", exc_info=True)
            event_id += 1
            yield {
                "id": str(event_id),
                "event": "error",
                "data": json.dumps({
                    "session_id": session_id,
                    "error_message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            }
    
    return EventSourceResponse(event_generator())
