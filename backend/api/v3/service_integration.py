"""
VERITAS API v3 - Service Integration Helper

Zentrale Helper-Funktionen für Backend-Service Integration.
Ermöglicht einfache Nutzung von UDS3, Intelligent Pipeline, Ollama, etc.

Verwendung:
    from backend.api.v3.service_integration import (
        execute_query_with_pipeline,
        get_agents_from_pipeline,
        get_models_from_ollama
    )
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
import uuid

logger = logging.getLogger(__name__)

# ============================================================================
# Service Access Functions
# ============================================================================

def get_services_from_app(app_state) -> Dict[str, Any]:
    """
    Holt alle Backend-Services aus FastAPI App State.
    
    Args:
        app_state: FastAPI app.state Object
        
    Returns:
        Dict mit Services (uds3, intelligent_pipeline, ollama, streaming)
    """
    return {
        "uds3": getattr(app_state, "uds3", None),
        "intelligent_pipeline": getattr(app_state, "intelligent_pipeline", None),
        "ollama": getattr(app_state, "ollama_service", None),
        "ollama_client": getattr(app_state, "ollama_client", None),
        "streaming": getattr(app_state, "streaming_service", None),
        "progress_manager": getattr(app_state, "progress_manager", None)
    }


def get_uds3_strategy(request):
    """
    Holt UDS3 Strategy aus FastAPI Request.
    
    Args:
        request: FastAPI Request Object
        
    Returns:
        UDS3Strategy Instance oder None
        
    Usage:
        uds3 = get_uds3_strategy(request)
        if uds3:
            result = uds3.query_vector_db(...)
    """
    if hasattr(request, "app") and hasattr(request.app, "state"):
        return getattr(request.app.state, "uds3", None)
    return None


# ============================================================================
# Query Execution (Intelligent Pipeline Integration)
# ============================================================================

async def execute_query_with_pipeline(
    query_text: str,
    intelligent_pipeline,
    session_id: Optional[str] = None,
    mode: str = "veritas",
    enable_commentary: bool = False,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Führt Query mit Intelligent Pipeline aus.
    
    Args:
        query_text: User Query
        intelligent_pipeline: IntelligentMultiAgentPipeline Instance
        session_id: Optional Session ID
        mode: Query Mode (veritas, chat, vpb, covina)
        enable_commentary: LLM Commentary aktivieren
        timeout: Timeout in Sekunden
        
    Returns:
        Dict mit Response (content, metadata, sources, agents)
        
    Raises:
        RuntimeError: Pipeline nicht verfügbar
        Exception: Pipeline Execution Error
    """
    if not intelligent_pipeline:
        raise RuntimeError("Intelligent Pipeline not available")
    
    # Import Pipeline Models
    try:
        from backend.agents.veritas_intelligent_pipeline import IntelligentPipelineRequest
    except ImportError:
        raise RuntimeError("IntelligentPipelineRequest not available")
    
    # Generate IDs
    query_id = f"query_{uuid.uuid4().hex[:8]}"
    session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create Pipeline Request
    pipeline_request = IntelligentPipelineRequest(
        query_id=query_id,
        query_text=query_text,
        user_context={
            "session_id": session_id,
            "mode": mode,
            "api_version": "v3"
        },
        session_id=session_id,
        enable_llm_commentary=enable_commentary,
        enable_real_time_updates=False,
        max_parallel_agents=5,
        timeout=timeout
    )
    
    # Execute Pipeline
    start_time = time.time()
    try:
        pipeline_response = await intelligent_pipeline.process_intelligent_query(pipeline_request)
        duration = time.time() - start_time
        
        # Format Response
        return {
            "content": pipeline_response.response_text,
            "confidence": pipeline_response.confidence_score,
            "duration": duration,
            "query_id": query_id,
            "session_id": session_id,
            "sources": pipeline_response.sources or [],
            "agent_results": pipeline_response.agent_results or {},
            "rag_context": pipeline_response.rag_context,
            "follow_up_suggestions": pipeline_response.follow_up_suggestions or [],
            "processing_metadata": pipeline_response.processing_metadata or {},
            "llm_commentary": pipeline_response.llm_commentary if enable_commentary else []
        }
        
    except Exception as e:
        logger.error(f"Pipeline execution error: {e}", exc_info=True)
        raise

# ============================================================================
# Agent Management (Intelligent Pipeline Integration)
# ============================================================================

def get_agents_from_pipeline(intelligent_pipeline) -> List[Dict[str, Any]]:
    """
    Holt Liste aller verfügbaren Agents aus Pipeline.
    
    Args:
        intelligent_pipeline: IntelligentMultiAgentPipeline Instance
        
    Returns:
        Liste von Agent-Dicts (id, name, description, capabilities, status)
    """
    if not intelligent_pipeline:
        return []
    
    try:
        # Versuche Agent Registry zu nutzen
        if hasattr(intelligent_pipeline, 'agent_registry'):
            agent_registry = intelligent_pipeline.agent_registry
            available_agents = agent_registry.list_available_agents()
            
            agents_list = []
            for agent_id, agent_info in available_agents.items():
                agents_list.append({
                    "agent_id": agent_id,
                    "name": agent_info.get("name", agent_id.replace("_", " ").title()),
                    "description": agent_info.get("description", f"Agent: {agent_id}"),
                    "capabilities": agent_info.get("capabilities", []),
                    "status": "active" if agent_info.get("available", True) else "inactive",
                    "version": agent_info.get("version", "1.0.0"),
                    "domain": agent_info.get("domain", "general")
                })
            
            return agents_list
        
        # Fallback: Hardcoded Agent List
        return _get_default_agents()
        
    except Exception as e:
        logger.warning(f"Could not fetch agents from pipeline: {e}")
        return _get_default_agents()

def _get_default_agents() -> List[Dict[str, Any]]:
    """Default Agent List als Fallback"""
    return [
        {
            "agent_id": "environmental_agent",
            "name": "Environmental Agent",
            "description": "Spezialist für Umweltrecht und BImSchG",
            "capabilities": ["environmental_law", "emissions", "wind_turbines"],
            "status": "active",
            "version": "1.0.0",
            "domain": "environmental"
        },
        {
            "agent_id": "verwaltungsrecht_agent",
            "name": "Verwaltungsrecht Agent",
            "description": "Spezialist für Verwaltungsrecht und VwGO",
            "capabilities": ["administrative_law", "court_procedures"],
            "status": "active",
            "version": "1.0.0",
            "domain": "legal"
        },
        {
            "agent_id": "immissionsschutz_agent",
            "name": "Immissionsschutz Agent",
            "description": "Spezialist für Immissionsschutzrecht",
            "capabilities": ["immissions", "noise", "air_quality"],
            "status": "active",
            "version": "1.0.0",
            "domain": "environmental"
        },
        {
            "agent_id": "construction_agent",
            "name": "Construction Agent",
            "description": "Baurecht und Genehmigungsverfahren",
            "capabilities": ["construction_law", "permits", "building_codes"],
            "status": "active",
            "version": "1.0.0",
            "domain": "construction"
        },
        {
            "agent_id": "traffic_agent",
            "name": "Traffic Agent",
            "description": "Verkehrsplanung und -analyse",
            "capabilities": ["traffic_analysis", "infrastructure", "planning"],
            "status": "active",
            "version": "1.0.0",
            "domain": "infrastructure"
        }
    ]

async def execute_agent_directly(
    agent_id: str,
    task: str,
    intelligent_pipeline,
    parameters: Optional[Dict[str, Any]] = None,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Führt einen einzelnen Agent direkt aus (ohne Pipeline-Orchestration).
    
    Args:
        agent_id: Agent ID
        task: Task Beschreibung
        intelligent_pipeline: Pipeline Instance
        parameters: Optional Task Parameters
        timeout: Timeout in Sekunden
        
    Returns:
        Dict mit Execution Result
        
    Raises:
        ValueError: Agent nicht gefunden
        RuntimeError: Execution Error
    """
    if not intelligent_pipeline:
        raise RuntimeError("Intelligent Pipeline not available")
    
    try:
        # Versuche Agent direkt auszuführen
        if hasattr(intelligent_pipeline, 'execute_single_agent'):
            start_time = time.time()
            result = await intelligent_pipeline.execute_single_agent(
                agent_id=agent_id,
                task=task,
                parameters=parameters or {},
                timeout=timeout
            )
            duration = time.time() - start_time
            
            return {
                "agent_id": agent_id,
                "task": task,
                "output": result.get("output", ""),
                "status": "completed",
                "duration": duration,
                "parameters": parameters,
                "metadata": result.get("metadata", {})
            }
        
        # Fallback: Nutze Pipeline mit nur einem Agent
        query_text = f"[{agent_id}] {task}"
        pipeline_result = await execute_query_with_pipeline(
            query_text=query_text,
            intelligent_pipeline=intelligent_pipeline,
            enable_commentary=False,
            timeout=timeout
        )
        
        # Extrahiere Agent-spezifisches Ergebnis
        agent_results = pipeline_result.get("agent_results", {})
        agent_specific = agent_results.get(agent_id, {})
        
        return {
            "agent_id": agent_id,
            "task": task,
            "output": agent_specific.get("result", pipeline_result.get("content", "")),
            "status": "completed",
            "duration": pipeline_result.get("duration", 0),
            "parameters": parameters,
            "metadata": agent_specific
        }
        
    except Exception as e:
        logger.error(f"Agent execution error: {e}", exc_info=True)
        raise RuntimeError(f"Agent execution failed: {str(e)}")

# ============================================================================
# Ollama Model Management
# ============================================================================

def get_models_from_ollama(ollama_client) -> List[Dict[str, Any]]:
    """
    Holt Liste aller verfügbaren LLM Models von Ollama.
    
    Args:
        ollama_client: VeritasOllamaClient Instance
        
    Returns:
        Liste von Model-Dicts (name, version, context_length, capabilities, status)
    """
    if not ollama_client:
        return _get_default_models()
    
    try:
        # Hole Models vom Client
        if hasattr(ollama_client, 'available_models'):
            models_dict = ollama_client.available_models
            
            models_list = []
            for model_name, model_info in models_dict.items():
                models_list.append({
                    "name": model_name,
                    "version": model_info.get("version", "latest"),
                    "context_length": model_info.get("context_length", 8192),
                    "capabilities": model_info.get("capabilities", ["text_generation", "chat"]),
                    "status": "available" if not ollama_client.offline_mode else "offline"
                })
            
            return models_list if models_list else _get_default_models()
        
        return _get_default_models()
        
    except Exception as e:
        logger.warning(f"Could not fetch models from Ollama: {e}")
        return _get_default_models()

def _get_default_models() -> List[Dict[str, Any]]:
    """Default Model List als Fallback"""
    return [
        {
            "name": "llama3.2:latest",
            "version": "latest",
            "context_length": 8192,
            "capabilities": ["text_generation", "chat", "rag"],
            "status": "available"
        },
        {
            "name": "llama3.1:8b",
            "version": "8b",
            "context_length": 8192,
            "capabilities": ["text_generation", "chat", "rag"],
            "status": "available"
        },
        {
            "name": "mixtral:latest",
            "version": "latest",
            "context_length": 32768,
            "capabilities": ["text_generation", "chat", "rag", "long_context"],
            "status": "available"
        }
    ]

# ============================================================================
# UDS3 Integration
# ============================================================================

async def retrieve_sources_from_uds3(
    query_text: str,
    uds3_strategy,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieval von Sources aus UDS3.
    
    Args:
        query_text: Query für Retrieval
        uds3_strategy: UDS3 UnifiedDatabaseStrategy Instance
        top_k: Anzahl zu retrievender Dokumente
        
    Returns:
        Liste von Source-Dicts (id, file, page, confidence, etc.)
    """
    if not uds3_strategy:
        return []
    
    try:
        # Hole Dokumente aus UDS3
        results = await uds3_strategy.search_unified(
            query=query_text,
            top_k=top_k
        )
        
        # Formatiere als Sources
        sources = []
        for i, doc in enumerate(results):
            sources.append({
                "id": f"src_{i+1}",
                "file": doc.get("file_name", "Unknown"),
                "page": doc.get("page", None),
                "confidence": doc.get("score", 0.0),
                "content": doc.get("content", ""),
                "metadata": doc.get("metadata", {})
            })
        
        return sources
        
    except Exception as e:
        logger.warning(f"UDS3 retrieval error: {e}")
        return []

__all__ = [
    # Service Access
    "get_services_from_app",
    # Query Execution
    "execute_query_with_pipeline",
    # Agent Management
    "get_agents_from_pipeline",
    "execute_agent_directly",
    # Ollama
    "get_models_from_ollama",
    # UDS3
    "retrieve_sources_from_uds3"
]
