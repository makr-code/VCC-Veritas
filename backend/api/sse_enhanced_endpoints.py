"""
Enhanced SSE Endpoint with Prompt Parser Integration
====================================================

Erweiterte SSE-Endpoints mit Prompt-Parser-Unterstützung für direkte
Agent-/Endpoint-Auswahl über Steuerzeichen.

Features:
- Prompt-Parsing mit Control Characters (@, #, /, !, $, +)
- Automatisches Agent-Routing
- Progress-Streaming
- Event-basierte Updates
- Template-Auswahl via Hashtags

Endpoints:
- POST /api/sse/query - Enhanced query mit Prompt-Parsing
- GET /api/sse/stream/{session_id} - SSE Stream für Progress
- GET /api/sse/examples - Beispiele für Control Characters

Usage:
    # Mit Control Characters
    POST /api/sse/query
    {
        "query": "@powerpoint #flowchart Genehmigungsprozess für Bauantrag"
    }
    
    # Progress via SSE
    EventSource('/api/sse/stream/session_123')

Author: VERITAS System  
Date: 2025-12-13
Version: 1.0
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

try:
    from sse_starlette.sse import EventSourceResponse
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False
    EventSourceResponse = StreamingResponse  # Fallback

from backend.utils.prompt_parser import get_prompt_parser, ParsedPrompt
from backend.agents.orchestrator.office_agent_orchestrator_integration import get_office_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sse/enhanced", tags=["SSE Enhanced"])


# =============================
# Pydantic Models
# =============================

class EnhancedQueryRequest(BaseModel):
    """Enhanced query request with prompt parsing"""
    query: str = Field(..., description="User query with optional control characters")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    parse_controls: bool = Field(True, description="Enable control character parsing")


class EnhancedQueryResponse(BaseModel):
    """Enhanced query response"""
    session_id: str
    parsed_prompt: Dict[str, Any]
    routing_info: Dict[str, Any]
    stream_url: str
    status: str


class PromptExampleResponse(BaseModel):
    """Example prompts with control characters"""
    examples: list
    controls: Dict[str, str]


# =============================
# In-Memory Session Storage
# =============================

active_sessions: Dict[str, Dict[str, Any]] = {}
session_events: Dict[str, list] = {}


# =============================
# Enhanced Query Endpoint
# =============================

@router.post("/query", response_model=EnhancedQueryResponse, summary="Submit query with control character parsing")
async def submit_enhanced_query(request: EnhancedQueryRequest):
    """
    Submit query with automatic parsing of control characters.
    
    Control Characters:
    - @ - Agent selection (@powerpoint, @excel, @outlook, @onenote)
    - # - Template category (#flowchart, #swot, #meeting_notes)
    - / - Commands (/generate, /list, /help)
    - ! - Priority (!high, !urgent, !low)
    - $ - Output format ($pdf, $xlsx, $html)
    - + - Tags (+confidential, +draft)
    
    Examples:
    - "@powerpoint #flowchart Genehmigungsprozess erstellen"
    - "@excel $xlsx #data_table Verkaufszahlen Q4"
    - "@outlook !urgent E-Mail an Team"
    - "/list @onenote #meeting_notes"
    
    Returns:
        Session info with SSE stream URL
    """
    try:
        session_id = str(uuid4())
        
        # Parse prompt if enabled
        if request.parse_controls:
            parser = get_prompt_parser()
            parsed = parser.parse(request.query)
            routing_info = parser.get_routing_info(request.query)
        else:
            parsed = None
            routing_info = {"clean_query": request.query}
        
        # Store session
        active_sessions[session_id] = {
            "session_id": session_id,
            "original_query": request.query,
            "parsed_prompt": parsed.to_dict() if parsed else None,
            "routing_info": routing_info,
            "context": request.context,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "events": []
        }
        
        session_events[session_id] = []
        
        # Start async processing
        asyncio.create_task(_process_query_async(session_id, routing_info, request.context))
        
        # Return session info
        stream_url = f"/api/sse/enhanced/stream/{session_id}"
        
        return EnhancedQueryResponse(
            session_id=session_id,
            parsed_prompt=parsed.to_dict() if parsed else {},
            routing_info=routing_info,
            stream_url=stream_url,
            status="processing"
        )
        
    except Exception as e:
        logger.error(f"❌ Error submitting enhanced query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _process_query_async(session_id: str, routing_info: Dict[str, Any], context: Optional[Dict[str, Any]]):
    """Process query asynchronously and emit events"""
    try:
        session = active_sessions.get(session_id)
        if not session:
            return
        
        # Update status
        session["status"] = "processing"
        _emit_event(session_id, "status", {"status": "processing", "message": "Processing query..."})
        
        # Extract routing information
        agent_type = routing_info.get("agent_type")
        clean_query = routing_info.get("clean_query")
        templates = routing_info.get("templates", [])
        output_format = routing_info.get("output_format")
        
        _emit_event(session_id, "routing", {
            "agent_type": agent_type,
            "templates": templates,
            "output_format": output_format
        })
        
        # Get orchestrator
        orchestrator = get_office_orchestrator()
        
        # Build request context
        request_context = context or {}
        if templates:
            request_context["template"] = templates[0]
        if output_format:
            request_context["output_format"] = output_format
        
        # Progress event
        _emit_event(session_id, "progress", {"percentage": 25, "message": "Routing to agent..."})
        
        # Process with orchestrator
        result = await orchestrator.process_request(
            query=clean_query,
            context=request_context
        )
        
        _emit_event(session_id, "progress", {"percentage": 75, "message": "Generating output..."})
        
        # Store result
        session["result"] = result
        session["status"] = "completed" if result.get("success") else "failed"
        session["completed_at"] = datetime.utcnow().isoformat()
        
        _emit_event(session_id, "progress", {"percentage": 100, "message": "Completed"})
        _emit_event(session_id, "result", result)
        _emit_event(session_id, "completed", {"session_id": session_id, "status": session["status"]})
        
    except Exception as e:
        logger.error(f"❌ Error processing query {session_id}: {e}", exc_info=True)
        session = active_sessions.get(session_id)
        if session:
            session["status"] = "error"
            session["error"] = str(e)
        _emit_event(session_id, "error", {"error": str(e)})


def _emit_event(session_id: str, event_type: str, data: Dict[str, Any]):
    """Emit event for session"""
    event = {
        "id": str(uuid4()),
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if session_id in session_events:
        session_events[session_id].append(event)
    
    session = active_sessions.get(session_id)
    if session:
        session["events"].append(event)


# =============================
# SSE Stream Endpoint
# =============================

@router.get("/stream/{session_id}", summary="Stream session events via SSE")
async def stream_session_events(
    session_id: str,
    last_event_id: Optional[str] = Query(None, alias="Last-Event-ID")
):
    """
    Stream session events via Server-Sent Events.
    
    Args:
        session_id: Session identifier
        last_event_id: Last received event ID (for reconnection)
    
    Returns:
        SSE stream with real-time events
    
    Client Example:
        ```javascript
        const source = new EventSource('/api/sse/enhanced/stream/session_123');
        
        source.addEventListener('progress', (e) => {
            const data = JSON.parse(e.data);
            console.log(`${data.percentage}%: ${data.message}`);
        });
        
        source.addEventListener('result', (e) => {
            const result = JSON.parse(e.data);
            console.log('Result:', result);
        });
        
        source.addEventListener('completed', (e) => {
            source.close();
        });
        ```
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events"""
        try:
            # Send initial connection event
            yield _format_sse_event("connected", {
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Send existing events (for reconnection)
            if last_event_id:
                events = session_events.get(session_id, [])
                replay_events = _get_events_after(events, last_event_id)
                for event in replay_events:
                    yield _format_sse_event(event["type"], event["data"], event["id"])
            
            # Stream new events
            last_count = len(session_events.get(session_id, []))
            
            while True:
                await asyncio.sleep(0.5)  # Poll interval
                
                events = session_events.get(session_id, [])
                new_events = events[last_count:]
                
                for event in new_events:
                    yield _format_sse_event(event["type"], event["data"], event["id"])
                
                last_count = len(events)
                
                # Check if session is complete
                session = active_sessions.get(session_id)
                if session and session["status"] in ["completed", "failed", "error"]:
                    # Send final event
                    yield _format_sse_event("end", {"session_id": session_id})
                    break
                
                # Timeout after 5 minutes
                if session and "created_at" in session:
                    created = datetime.fromisoformat(session["created_at"])
                    if (datetime.utcnow() - created).total_seconds() > 300:
                        break
        
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for session {session_id}")
        except Exception as e:
            logger.error(f"❌ Error in SSE stream: {e}", exc_info=True)
            yield _format_sse_event("error", {"error": str(e)})
    
    if SSE_AVAILABLE:
        return EventSourceResponse(event_generator())
    else:
        return StreamingResponse(event_generator(), media_type="text/event-stream")


def _format_sse_event(event_type: str, data: Dict[str, Any], event_id: Optional[str] = None) -> str:
    """Format SSE event"""
    lines = []
    
    if event_id:
        lines.append(f"id: {event_id}")
    
    lines.append(f"event: {event_type}")
    lines.append(f"data: {json.dumps(data)}")
    lines.append("")  # Empty line to end event
    
    return "\n".join(lines) + "\n"


def _get_events_after(events: list, event_id: str) -> list:
    """Get events after specific event ID"""
    for i, event in enumerate(events):
        if event["id"] == event_id:
            return events[i + 1:]
    return events


# =============================
# Helper Endpoints
# =============================

@router.get("/session/{session_id}", summary="Get session status")
async def get_session_status(session_id: str):
    """Get current status of a session"""
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return session


@router.get("/examples", response_model=PromptExampleResponse, summary="Get control character examples")
async def get_prompt_examples():
    """
    Get examples of prompts with control characters.
    
    Returns:
        Examples and control character documentation
    """
    return PromptExampleResponse(
        examples=[
            {
                "prompt": "@powerpoint #flowchart Genehmigungsprozess für Bauantrag",
                "description": "PowerPoint mit Flowchart-Template"
            },
            {
                "prompt": "@excel $xlsx #data_table Verkaufszahlen Q4 2024",
                "description": "Excel-Tabelle als XLSX mit Datentabellen-Template"
            },
            {
                "prompt": "@outlook !urgent E-Mail an Team über Meeting-Verschiebung",
                "description": "Dringende E-Mail via Outlook"
            },
            {
                "prompt": "@onenote #meeting_notes +confidential Strategiemeeting vom 13.12.2024",
                "description": "Vertrauliche Meeting-Notizen"
            },
            {
                "prompt": "/list @powerpoint #templates",
                "description": "Liste aller PowerPoint-Templates"
            },
            {
                "prompt": "@powerpoint #swot $pdf Wettbewerbsanalyse +draft",
                "description": "SWOT-Analyse als PDF-Entwurf"
            }
        ],
        controls={
            "@": "Agent selection (@powerpoint, @excel, @outlook, @onenote)",
            "#": "Template category (#flowchart, #swot, #meeting_notes)",
            "/": "Commands (/generate, /list, /help)",
            "!": "Priority (!high, !urgent, !low)",
            "$": "Output format ($pdf, $xlsx, $html)",
            "+": "Tags (+confidential, +draft, +important)"
        }
    )


@router.delete("/session/{session_id}", summary="Delete session")
async def delete_session(session_id: str):
    """Delete a session and its events"""
    if session_id in active_sessions:
        del active_sessions[session_id]
    if session_id in session_events:
        del session_events[session_id]
    
    return {"success": True, "message": f"Session {session_id} deleted"}


@router.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "sse_enhanced",
        "active_sessions": len(active_sessions),
        "parser_available": True,
        "sse_available": SSE_AVAILABLE
    }
