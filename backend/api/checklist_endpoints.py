"""
Checklist Endpoints for VERITAS API
===================================

FastAPI endpoints for checklist generation.

Endpoints:
- POST /api/checklist/generate - Generate a new checklist
- GET /api/checklist/health - Health check

Integration:
- ChecklistAgent for generation
- ThemisDB for data retrieval
- Ollama LLM for intelligent generation
- Argus2 Android app compatible

Author: VERITAS Development Team
Date: December 2025
"""
import logging
import time
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
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
