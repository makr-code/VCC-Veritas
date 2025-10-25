"""
VERITAS API v3 - System Router

Endpoints für System Information:
- GET /api/v3/system/health - Health Check
- GET /api/v3/system/capabilities - System Capabilities
- GET /api/v3/system/modes - Verfügbare Modi
- GET /api/v3/system/models - LLM Models
- GET /api/v3/system/metrics - System Metrics

System Status & Monitoring.
"""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any
import logging
import time
from datetime import datetime

from .models import (
    SystemHealth, SystemCapabilities, SystemMetrics,
    SuccessResponse
)
from .service_integration import (
    get_services_from_app,
    get_agents_from_pipeline,
    get_models_from_ollama
)

logger = logging.getLogger(__name__)

# Router
system_router = APIRouter(
    prefix="/system",
    tags=["System Information"]
)

# Metrics Tracking (In-Memory für MVP)
_metrics = {
    "requests_total": 0,
    "requests_success": 0,
    "requests_error": 0,
    "start_time": time.time()
}

# ============================================================================
# Helper Functions
# ============================================================================

def get_backend_services(request: Request) -> Dict[str, Any]:
    """Holt alle Backend Services"""
    return get_services_from_app(request.app.state)

def increment_metric(metric: str, value: int = 1):
    """Erhöht einen Metric-Counter"""
    if metric in _metrics:
        _metrics[metric] += value

# ============================================================================
# Endpoints
# ============================================================================

@system_router.get("/health", response_model=SystemHealth)
async def get_health(request: Request):
    """
    System Health Check
    
    Prüft die Verfügbarkeit aller System-Komponenten.
    
    Response:
        - status: healthy, degraded, unhealthy
        - timestamp: Check Zeitpunkt
        - services: Dict mit Service Status (bool)
        - uptime: System Uptime (Sekunden)
        
    Status Levels:
        - healthy: Alle Services verfügbar
        - degraded: Einige Services unavailable
        - unhealthy: Critical Services unavailable
    """
    try:
        services = get_backend_services(request)
        
        # Service Status Check
        service_status = {
            "uds3": services["uds3"] is not None,
            "intelligent_pipeline": services["intelligent_pipeline"] is not None,
            "ollama": services["ollama"] is not None,
            "streaming": services["streaming"] is not None
        }
        
        # Determine Overall Health
        available_services = sum(service_status.values())
        total_services = len(service_status)
        
        if available_services == total_services:
            status = "healthy"
        elif available_services >= total_services * 0.5:
            status = "degraded"
        else:
            status = "unhealthy"
        
        # Uptime
        uptime = time.time() - _metrics["start_time"]
        
        return SystemHealth(
            status=status,
            timestamp=datetime.now(),
            services=service_status,
            uptime=uptime
        )
        
    except Exception as e:
        logger.error(f"❌ Health Check Error: {e}", exc_info=True)
        return SystemHealth(
            status="unhealthy",
            timestamp=datetime.now(),
            services={},
            uptime=0
        )

@system_router.get("/capabilities", response_model=SystemCapabilities)
async def get_capabilities(request: Request):
    """
    System Capabilities
    
    Gibt vollständige System Capabilities zurück: Endpoints, Features,
    verfügbare Models, Agents.
    
    Response:
        - version: System Version
        - endpoints: Liste aller verfügbaren Endpoints
        - features: Feature Flags (Dict[str, bool])
        - models: Verfügbare LLM Models (Liste)
        - agents: Verfügbare Agents (Liste)
        
    Feature Flags:
        - streaming_available: Streaming Query Support
        - intelligent_pipeline_available: Multi-Agent Pipeline
        - uds3_available: UDS3 Multi-Database
        - ollama_available: Ollama LLM
        - rag_available: RAG Support
    """
    try:
        services = get_backend_services(request)
        
        # Endpoints (API v3)
        endpoints = [
            "/api/v3/query/standard",
            "/api/v3/query/stream",
            "/api/v3/query/intelligent",
            "/api/v3/agent/list",
            "/api/v3/agent/{agent_id}/info",
            "/api/v3/agent/{agent_id}/execute",
            "/api/v3/agent/capabilities",
            "/api/v3/system/health",
            "/api/v3/system/capabilities",
            "/api/v3/system/modes",
            "/api/v3/system/models",
            "/api/v3/system/metrics"
        ]
        
        # Feature Flags
        features = {
            "streaming_available": services["streaming"] is not None,
            "intelligent_pipeline_available": services["intelligent_pipeline"] is not None,
            "uds3_available": services["uds3"] is not None,
            "ollama_available": services["ollama_client"] is not None,
            "rag_available": services["uds3"] is not None
        }
        
        # ✅ Models aus Ollama Client holen
        models = []
        if services["ollama_client"]:
            models_list = get_models_from_ollama(services["ollama_client"])
            models = [m["name"] for m in models_list]
        
        # ✅ Agents aus Pipeline holen
        agents = []
        if services["intelligent_pipeline"]:
            agents_list = get_agents_from_pipeline(services["intelligent_pipeline"])
            agents = [a["agent_id"] for a in agents_list]
        
        logger.info(f"📊 System Capabilities: {len(models)} models, {len(agents)} agents")
        
        return SystemCapabilities(
            version="3.0.0",
            endpoints=endpoints,
            features=features,
            models=models,
            agents=agents
        )
        
    except Exception as e:
        logger.error(f"❌ Get Capabilities Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get capabilities: {str(e)}"
        )

@system_router.get("/modes")
async def get_modes(request: Request):
    """
    Verfügbare Modi
    
    Gibt alle verfügbaren Query-Modi zurück mit Display-Name,
    Endpoints und Status.
    
    Response:
        {
          "modes": {
            "veritas": {
              "display_name": "Standard RAG",
              "endpoints": ["/api/v3/query/standard", "/api/v3/query/stream"],
              "status": "implemented"
            },
            ...
          }
        }
        
    Modi:
        - veritas: Standard RAG mit UDS3
        - chat: Conversational Mode
        - vpb: VPB Module (Verwaltungsprozessbearbeitung)
        - covina: COVINA Module (COVID-Datenanalyse)
    """
    try:
        modes = {
            "hybrid": {
                "display_name": "🔍 Hybrid Search",
                "description": "Multi-Database Retrieval mit LLM Re-Ranking (Vector+Graph+Relational)",
                "endpoints": [
                    "/api/query/hybrid",
                    "/api/query"
                ],
                "status": "implemented",
                "optimal": True,
                "features": {
                    "vector_search": True,
                    "graph_search": True,
                    "relational_search": True,
                    "llm_reranking": True,
                    "rrf_fusion": True
                },
                "performance": {
                    "latency_fast": "~2s (no re-ranking)",
                    "latency_balanced": "~5-8s (default)",
                    "latency_accurate": "~10-12s (max quality)"
                }
            },
            "veritas": {
                "display_name": "Standard RAG",
                "description": "Retrieval-Augmented Generation mit UDS3",
                "endpoints": [
                    "/api/v3/query/standard",
                    "/api/v3/query/stream",
                    "/api/v3/query/intelligent"
                ],
                "status": "implemented"
            },
            "rag": {
                "display_name": "RAG (Vector Only)",
                "description": "Standard RAG mit Vector Database",
                "endpoints": ["/api/query/rag"],
                "status": "implemented"
            },
            "chat": {
                "display_name": "Conversational Chat",
                "description": "Konversationsmodus ohne RAG",
                "endpoints": ["/api/v3/query/standard"],
                "status": "implemented"
            },
            "ask": {
                "display_name": "Simple Ask",
                "description": "Direct LLM ohne Retrieval",
                "endpoints": ["/api/query/ask"],
                "status": "implemented"
            },
            "streaming": {
                "display_name": "Streaming Query",
                "description": "Progressive Results mit SSE",
                "endpoints": ["/api/query/stream"],
                "status": "implemented"
            },
            "vpb": {
                "display_name": "VPB Module",
                "description": "Verwaltungsprozessbearbeitung",
                "endpoints": ["/api/v3/vpb/query"],
                "status": "planned"
            },
            "covina": {
                "display_name": "COVINA Module",
                "description": "COVID-19 Datenanalyse",
                "endpoints": ["/api/v3/covina/query"],
                "status": "experimental"
            }
        }
        
        return SuccessResponse(
            success=True,
            message="Available modes retrieved",
            data={"modes": modes}
        )
        
    except Exception as e:
        logger.error(f"❌ Get Modes Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get modes: {str(e)}"
        )

@system_router.get("/models")
async def get_models(request: Request):
    """
    LLM Models
    
    Gibt alle verfügbaren LLM Models zurück mit Details
    (Name, Version, Context Length, Capabilities).
    
    Response:
        {
          "models": [
            {
              "name": "llama3.2:latest",
              "version": "latest",
              "context_length": 8192,
              "capabilities": ["text_generation", "chat"],
              "status": "available"
            },
            ...
          ]
        }
    """
    try:
        services = get_backend_services(request)
        
        if not services["ollama_client"]:
            raise HTTPException(
                status_code=503,
                detail="Ollama service unavailable"
            )
        
        # ✅ ECHTE BACKEND INTEGRATION
        logger.info("🤖 Fetching models from Ollama")
        models = get_models_from_ollama(services["ollama_client"])
        
        logger.info(f"✅ Retrieved {len(models)} models")
        
        return SuccessResponse(
            success=True,
            message="Available models retrieved",
            data={"models": models}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get Models Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get models: {str(e)}"
        )

@system_router.get("/metrics", response_model=SystemMetrics)
async def get_metrics(request: Request):
    """
    System Metrics
    
    Gibt System Performance Metrics zurück:
    - Total Requests
    - Requests/Second
    - Average Latency
    - Error Rate
    - Uptime
    
    Response:
        - requests_total: Gesamt Requests
        - requests_per_second: Requests pro Sekunde
        - average_latency: Durchschnittliche Latenz (ms)
        - error_rate: Error Rate (0.0-1.0)
        - uptime: System Uptime (Sekunden)
        - timestamp: Metrics Zeitpunkt
        
    Note: MVP verwendet In-Memory Tracking.
    Production sollte Redis/Prometheus nutzen.
    """
    try:
        # Calculate Metrics
        uptime = time.time() - _metrics["start_time"]
        requests_total = _metrics["requests_total"]
        requests_per_second = requests_total / uptime if uptime > 0 else 0
        
        # Error Rate
        requests_success = _metrics["requests_success"]
        requests_error = _metrics["requests_error"]
        total = requests_success + requests_error
        error_rate = requests_error / total if total > 0 else 0.0
        
        # Average Latency (Platzhalter, TODO: Track actual latencies)
        average_latency = 250.0  # ms
        
        return SystemMetrics(
            requests_total=requests_total,
            requests_per_second=round(requests_per_second, 2),
            average_latency=average_latency,
            error_rate=round(error_rate, 4),
            uptime=round(uptime, 2),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"❌ Get Metrics Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )

__all__ = ["system_router", "increment_metric"]
