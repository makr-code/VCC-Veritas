"""
Office Agents API Endpoints
============================

FastAPI endpoints for PowerPoint, Excel/Table, Outlook, and OneNote agents.
Provides unified interface for all Office document generation and manipulation.

Author: VERITAS System
Date: 2025-12-13
Version: 1.0
"""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from backend.agents.orchestrator.office_agent_orchestrator_integration import get_office_orchestrator
from backend.agents.presentation_canvas_agent import PresentationCanvasAgent
from backend.agents.excel_table_agent import ExcelTableAgent
from backend.agents.outlook_agent import OutlookAgent
from backend.agents.onenote_agent import OneNoteAgent
from backend.agents.presentation_template_manager import get_template_manager as get_ppt_template_manager
from backend.agents.table_template_manager import get_table_template_manager
from backend.agents.outlook_template_manager import get_outlook_template_manager
from backend.agents.onenote_template_manager import get_onenote_template_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/office", tags=["Office Agents"])


# =============================
# Pydantic Models
# =============================

class OfficeAgentRequest(BaseModel):
    """Generic request model for office agents"""
    query: str = Field(..., description="User query/request")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    output_format: Optional[str] = Field(None, description="Desired output format")


class PresentationRequest(BaseModel):
    """Request model for PowerPoint presentations"""
    query: str = Field(..., description="Presentation description")
    template: Optional[str] = Field(None, description="Template category (list, process, cycle, etc.)")
    variation: Optional[str] = Field(None, description="Template variation")
    slides: Optional[int] = Field(None, description="Number of slides")
    use_native_shapes: bool = Field(True, description="Use native PowerPoint shapes")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class TableRequest(BaseModel):
    """Request model for Excel/table generation"""
    query: str = Field(..., description="Table description")
    template: Optional[str] = Field(None, description="Template category (data_table, comparison, etc.)")
    variation: Optional[str] = Field(None, description="Template variation")
    output_format: str = Field("excel", description="Output format: excel, csv, word, powerpoint")
    data: Optional[Dict[str, Any]] = Field(None, description="Table data")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class OutlookRequest(BaseModel):
    """Request model for Outlook items"""
    query: str = Field(..., description="Outlook item description")
    template: Optional[str] = Field(None, description="Template category (email, calendar, task, contact)")
    variation: Optional[str] = Field(None, description="Template variation")
    data: Optional[Dict[str, Any]] = Field(None, description="Item data")
    send: bool = Field(False, description="Send immediately (email only)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class OneNoteRequest(BaseModel):
    """Request model for OneNote notes"""
    query: str = Field(..., description="Note description")
    template: Optional[str] = Field(None, description="Template category (meeting_notes, project_notes, etc.)")
    variation: Optional[str] = Field(None, description="Template variation")
    data: Optional[Dict[str, Any]] = Field(None, description="Note data")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class TemplateListResponse(BaseModel):
    """Response model for template lists"""
    templates: List[Dict[str, Any]]
    count: int


class AgentStatusResponse(BaseModel):
    """Response model for agent status"""
    agents: Dict[str, Any]
    total_agents: int
    all_available: bool


# =============================
# Unified Orchestrator Endpoint
# =============================

@router.post("/process", summary="Process request with automatic agent selection")
async def process_office_request(request: OfficeAgentRequest):
    """
    Process user request with automatic agent selection based on intent recognition.
    
    The system analyzes the query and routes it to the appropriate agent:
    - PowerPoint: presentations, slides, diagrams
    - Excel/Table: tables, spreadsheets, data
    - Outlook: email, calendar, tasks, contacts
    - OneNote: notes, meeting minutes, documentation
    """
    try:
        orchestrator = get_office_orchestrator()
        result = await orchestrator.process_request(
            query=request.query,
            context=request.context
        )
        return result
    except Exception as e:
        logger.error(f"❌ Error processing office request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================
# PowerPoint Agent Endpoints
# =============================

@router.post("/presentations/generate", summary="Generate PowerPoint presentation")
async def generate_presentation(request: PresentationRequest):
    """
    Generate a PowerPoint presentation from a query.
    
    Supports:
    - 182+ native shapes
    - Flowcharts, org charts, cycle diagrams
    - 8 template categories with 28 variations
    - Native PowerPoint output (editable)
    """
    try:
        agent = PresentationCanvasAgent()
        
        # Call the actual generate_presentation method
        result = await agent.generate_presentation(
            user_prompt=request.query,
            context=request.context or {},
            template_hint=request.template
        )
        
        return result
    except Exception as e:
        logger.error(f"❌ Error generating presentation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presentations/templates", summary="List PowerPoint templates")
async def list_presentation_templates():
    """List all available PowerPoint templates"""
    try:
        manager = get_ppt_template_manager()
        templates = manager.list_templates()
        return TemplateListResponse(templates=templates, count=len(templates))
    except Exception as e:
        logger.error(f"❌ Error listing presentation templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presentations/templates/{category}", summary="Get presentation template details")
async def get_presentation_template(category: str):
    """Get details of a specific presentation template"""
    try:
        manager = get_ppt_template_manager()
        template = manager.read_template(category)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{category}' not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting presentation template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================
# Excel/Table Agent Endpoints
# =============================

@router.post("/tables/generate", summary="Generate Excel table or CSV")
async def generate_table(request: TableRequest):
    """
    Generate Excel spreadsheet, CSV, or embed table in Word/PowerPoint.
    
    Supports:
    - Excel (.xlsx) with formatting
    - CSV export
    - Word document embedding
    - PowerPoint slide embedding
    - 4 template categories with variations
    """
    try:
        agent = ExcelTableAgent()
        
        request_data = {
            "query": request.query,
            "template": request.template,
            "variation": request.variation,
            "output_format": request.output_format,
            "data": request.data,
            "context": request.context or {}
        }
        
        result = await agent.generate_table(request_data)
        return result
    except Exception as e:
        logger.error(f"❌ Error generating table: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/templates", summary="List table templates")
async def list_table_templates():
    """List all available table templates"""
    try:
        manager = get_table_template_manager()
        templates = manager.list_templates()
        return TemplateListResponse(templates=templates, count=len(templates))
    except Exception as e:
        logger.error(f"❌ Error listing table templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/templates/{category}", summary="Get table template details")
async def get_table_template(category: str):
    """Get details of a specific table template"""
    try:
        manager = get_table_template_manager()
        template = manager.read_template(category)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{category}' not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting table template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================
# Outlook Agent Endpoints
# =============================

@router.post("/outlook/compose", summary="Compose Outlook item (email, event, task, contact)")
async def compose_outlook_item(request: OutlookRequest):
    """
    Compose Outlook email, calendar event, task, or contact.
    
    Supports:
    - Email composition with HTML formatting
    - Calendar events and meetings
    - Task creation and management
    - Contact management
    - 4 template categories with 14 variations
    """
    try:
        agent = OutlookAgent()
        
        request_data = {
            "template": request.template,
            "variation": request.variation,
            "data": request.data,
            "send": request.send,
            "context": request.context or {}
        }
        
        # Route based on template category - use existing methods
        if request.template == "email_compose":
            result = await agent.compose_email(request_data)
        elif request.template == "calendar_event":
            result = await agent.create_calendar_event(request_data)
        elif request.template == "task_management":
            result = await agent.create_task(request_data)
        elif request.template == "contact_management":
            result = await agent.add_contact(request_data)
        else:
            # Default to email composition
            result = await agent.compose_email(request_data)
        
        return result
    except Exception as e:
        logger.error(f"❌ Error composing Outlook item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outlook/templates", summary="List Outlook templates")
async def list_outlook_templates():
    """List all available Outlook templates"""
    try:
        manager = get_outlook_template_manager()
        templates = manager.list_templates()
        return TemplateListResponse(templates=templates, count=len(templates))
    except Exception as e:
        logger.error(f"❌ Error listing Outlook templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outlook/templates/{category}", summary="Get Outlook template details")
async def get_outlook_template(category: str):
    """Get details of a specific Outlook template"""
    try:
        manager = get_outlook_template_manager()
        template = manager.read_template(category)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{category}' not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting Outlook template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================
# OneNote Agent Endpoints
# =============================

@router.post("/onenote/create", summary="Create OneNote note")
async def create_onenote_note(request: OneNoteRequest):
    """
    Create OneNote note (meeting notes, project docs, checklists, knowledge base).
    
    Supports:
    - Meeting notes (standup, formal, brainstorming)
    - Project documentation
    - Interactive checklists
    - Knowledge base articles
    - Research notes
    - 5 template categories with 19 variations
    """
    try:
        agent = OneNoteAgent()
        
        request_data = {
            "template": request.template,
            "variation": request.variation,
            "data": request.data,
            "context": request.context or {}
        }
        
        # Route based on template category - use existing methods
        if request.template == "meeting_notes":
            result = await agent.create_meeting_notes(request_data)
        elif request.template == "project_notes":
            result = await agent.create_project_notes(request_data)
        elif request.template == "checklist":
            result = await agent.create_checklist(request_data)
        else:
            # Default to create_note for other categories
            result = await agent.create_note(request_data)
        
        return result
    except Exception as e:
        logger.error(f"❌ Error creating OneNote note: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/onenote/templates", summary="List OneNote templates")
async def list_onenote_templates():
    """List all available OneNote templates"""
    try:
        manager = get_onenote_template_manager()
        templates = manager.list_templates()
        return TemplateListResponse(templates=templates, count=len(templates))
    except Exception as e:
        logger.error(f"❌ Error listing OneNote templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/onenote/templates/{category}", summary="Get OneNote template details")
async def get_onenote_template(category: str):
    """Get details of a specific OneNote template"""
    try:
        manager = get_onenote_template_manager()
        template = manager.read_template(category)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{category}' not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting OneNote template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================
# System Status Endpoints
# =============================

@router.get("/status", summary="Get office agents status")
async def get_agents_status():
    """Get status and capabilities of all office agents"""
    try:
        orchestrator = get_office_orchestrator()
        status = orchestrator.get_agent_status()
        
        all_available = all(
            agent["available"] for agent in status.values()
        )
        
        return AgentStatusResponse(
            agents=status,
            total_agents=len(status),
            all_available=all_available
        )
    except Exception as e:
        logger.error(f"❌ Error getting agents status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intents", summary="List all supported intents")
async def list_supported_intents():
    """List all supported intents and templates across all agents"""
    try:
        orchestrator = get_office_orchestrator()
        intents = orchestrator.get_supported_intents()
        return {
            "intents": intents,
            "count": len(intents)
        }
    except Exception as e:
        logger.error(f"❌ Error listing intents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Health check for office agents")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "office_agents",
        "version": "1.0"
    }


# =============================
# Helper Functions
# =============================

def register_office_agents_router(app):
    """Register office agents router with FastAPI app"""
    app.include_router(router)
    logger.info("✅ Office Agents API endpoints registered")
