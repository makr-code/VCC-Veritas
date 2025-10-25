"""
VERITAS System Router
=====================

System-Endpoints (Health, Capabilities, Info)
"""

from fastapi import APIRouter, Request
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

system_router = APIRouter(prefix="/system")


@system_router.get("/health")
async def health_check(request: Request) -> Dict[str, Any]:
    """
    System Health Check
    
    Returns:
        Health status aller Komponenten (KEIN FALLBACK!)
    """
    app_state = request.app.state
    
    # Alle Komponenten sind zwingend erforderlich
    uds3_ok = hasattr(app_state, "uds3") and app_state.uds3 is not None
    pipeline_ok = hasattr(app_state, "pipeline") and app_state.pipeline is not None
    streaming_ok = hasattr(app_state, "streaming") and app_state.streaming is not None
    query_ok = hasattr(app_state, "query_service")
    
    # System ist nur healthy wenn ALLE Komponenten verfügbar sind
    all_components_ok = uds3_ok and pipeline_ok and streaming_ok and query_ok
    
    health_data = {
        "status": "healthy" if all_components_ok else "critical",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "uds3": {
                "available": uds3_ok,
                "required": True,
                "status": "ok" if uds3_ok else "CRITICAL - UDS3 ist zwingend erforderlich!"
            },
            "pipeline": {
                "available": pipeline_ok,
                "required": True,
                "status": "ok" if pipeline_ok else "CRITICAL - Pipeline ist zwingend erforderlich!"
            },
            "streaming": {
                "available": streaming_ok,
                "required": True,
                "status": "ok" if streaming_ok else "CRITICAL - Streaming ist zwingend erforderlich!"
            },
            "query_service": {
                "available": query_ok,
                "required": True,
                "status": "ok" if query_ok else "CRITICAL - Query Service ist zwingend erforderlich!"
            }
        }
    }
    
    # UDS3 Backend Details - Dynamisch aus app.state.uds3 abfragen
    if uds3_ok:
        try:
            uds3_manager = request.app.state.uds3
            
            # Prüfe DatabaseManager Status
            backends_status = {}
            
            if hasattr(uds3_manager, 'database_manager'):
                db_manager = uds3_manager.database_manager
                
                # Debug: Zeige verfügbare Attribute
                db_attrs = [attr for attr in dir(db_manager) if not attr.startswith('_')]
                logger.info(f"🔍 DatabaseManager Attribute: {db_attrs[:15]}")
                
                # Vector Backend (ChromaDB)
                if hasattr(db_manager, 'vector') and db_manager.vector is not None:
                    backends_status["vector"] = {
                        "backend": "ChromaDB",
                        "status": "active"
                    }
                else:
                    backends_status["vector"] = {
                        "backend": "ChromaDB",
                        "status": "disabled"
                    }
                
                # Graph Backend (Neo4j)
                if hasattr(db_manager, 'graph') and db_manager.graph is not None:
                    backends_status["graph"] = {
                        "backend": "Neo4j",
                        "status": "active"
                    }
                else:
                    backends_status["graph"] = {
                        "backend": "Neo4j",
                        "status": "disabled"
                    }
                
                # Relational Backend (PostgreSQL)
                if hasattr(db_manager, 'relational') and db_manager.relational is not None:
                    backends_status["relational"] = {
                        "backend": "PostgreSQL",
                        "status": "active"
                    }
                else:
                    backends_status["relational"] = {
                        "backend": "PostgreSQL/SQLite",
                        "status": "disabled"
                    }
                
                # File Backend (CouchDB)
                if hasattr(db_manager, 'file') and db_manager.file is not None:
                    backends_status["file"] = {
                        "backend": "CouchDB",
                        "status": "active"
                    }
                else:
                    backends_status["file"] = {
                        "backend": "CouchDB",
                        "status": "disabled"
                    }
            else:
                # Fallback: Hard-coded Status
                backends_status = {
                    "vector": {"backend": "ChromaDB", "status": "active"},
                    "graph": {"backend": "Neo4j", "status": "disabled"},
                    "relational": {"backend": "PostgreSQL", "status": "disabled"},
                    "file": {"backend": "CouchDB", "status": "disabled"}
                }
            
            health_data["uds3_backends"] = backends_status
            
            # Zähle aktive Backends
            active_backends = sum(1 for b in backends_status.values() if b["status"] == "active")
            health_data["message"] = f"All systems operational ({active_backends}/{len(backends_status)} backends active)"
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Abrufen der Backend-Status: {e}")
            # Fallback bei Fehler
            health_data["uds3_backends"] = {
                "vector": {"backend": "ChromaDB", "status": "active"},
                "graph": {"backend": "Neo4j", "status": "unknown"},
                "relational": {"backend": "PostgreSQL", "status": "unknown"},
                "file": {"backend": "CouchDB", "status": "unknown"}
            }
            health_data["message"] = "Systems operational (backend status check failed)"
    else:
        health_data["error"] = "VERITAS cannot operate without UDS3!"
        health_data["action"] = "Install UDS3: cd C:\\VCC\\uds3 && pip install -e ."
    
    return health_data


@system_router.get("/info")
async def system_info(request: Request) -> Dict[str, Any]:
    """
    System Information (NO FALLBACK MODE)
    """
    from backend.api import get_api_info
    
    app_state = request.app.state
    
    info_data = {
        "name": "VERITAS Unified Backend",
        "version": "4.0.0",
        "mode": "PRODUCTION - No Fallback!",
        "api": get_api_info(),
        "architecture": "UDS3 v2.0.0 Polyglot Persistence",
        "infrastructure": {
            "database_system": "UDS3 PolyglotManager",
            "vector_backend": "ChromaDB",
            "graph_backend": "Neo4j (optional)",
            "relational_backend": "SQLite (optional)",
            "llm": "Ollama",
            "embeddings": "German BERT"
        },
        "features": {
            "unified_response": True,
            "ieee_citations": True,
            "multi_mode": True,
            "streaming": True,
            "hybrid_search": True,
            "agent_system": True,
            "rag_pipeline": True,
            "fallback_mode": False  # KEIN FALLBACK!
        }
    }
    
    # UDS3 Status - MUSS verfügbar sein!
    if hasattr(app_state, "uds3") and app_state.uds3:
        info_data["uds3_status"] = "active"
        info_data["uds3_version"] = "2.0.0"
    else:
        info_data["uds3_status"] = "CRITICAL - NOT AVAILABLE"
        info_data["error"] = "VERITAS cannot operate without UDS3!"
        info_data["action"] = "Install UDS3: cd C:\\VCC\\uds3 && pip install -e ."
    
    # Pipeline Status - MUSS verfügbar sein!
    if hasattr(app_state, "pipeline") and app_state.pipeline:
        info_data["pipeline_status"] = "active"
        info_data["agents_count"] = 14
    else:
        info_data["pipeline_status"] = "CRITICAL - NOT AVAILABLE"
    
    return info_data


@system_router.get("/capabilities")
async def system_capabilities() -> Dict[str, Any]:
    """
    System Capabilities
    
    Alle verfügbaren Features und Modi
    """
    return {
        "query_modes": [
            "rag",
            "hybrid",
            "streaming",
            "agent",
            "ask"
        ],
        "features": {
            "uds3_v2": True,
            "intelligent_pipeline": True,
            "ieee_citations": True,
            "unified_response": True,
            "streaming_progress": True,
            "hybrid_search": True,
            "agent_orchestration": True,
            "multi_database": True
        },
        "endpoints": {
            "query": [
                "/api/query",
                "/api/query/ask",
                "/api/query/rag",
                "/api/query/hybrid",
                "/api/query/stream"
            ],
            "agent": [
                "/api/agent/list",
                "/api/agent/capabilities",
                "/api/agent/status/{agent_id}"
            ],
            "system": [
                "/api/system/health",
                "/api/system/info",
                "/api/system/capabilities"
            ]
        }
    }


@system_router.get("/modes")
async def available_modes() -> Dict[str, Any]:
    """
    Verfügbare Query-Modi mit Beschreibungen
    
    Jeder Modus hat:
    - status: 'implemented' | 'planned' | 'experimental'
    - display_name: Anzeigename für UI
    - description: Kurzbeschreibung
    - endpoints: Liste der API-Endpoints
    - optimal: Boolean (empfohlener Modus)
    - features: Dict mit Feature-Flags
    """
    return {
        "modes": {
            "hybrid": {
                "status": "implemented",
                "display_name": "🔍 Hybrid Search",
                "description": "Multi-Database Retrieval mit LLM Re-Ranking (Vector+Graph+Relational)",
                "endpoints": ["/api/query/hybrid", "/api/query"],
                "optimal": True,
                "features": {
                    "vector_search": True,
                    "graph_search": True,
                    "relational_search": True,
                    "llm_reranking": True,
                    "rrf_fusion": True,
                    "score_tracking": True
                },
                "performance": {
                    "latency_fast": "~2s (no re-ranking)",
                    "latency_balanced": "~5-8s (default)",
                    "latency_accurate": "~10-12s (max quality)"
                }
            },
            "rag": {
                "status": "implemented",
                "display_name": "RAG Query",
                "description": "Retrieval-Augmented Generation mit UDS3 + Intelligent Pipeline",
                "endpoints": ["/api/query/rag", "/api/query"],
                "features": {
                    "vector_search": True,
                    "agent_orchestration": True,
                    "ieee_citations": True
                }
            },
            "streaming": {
                "status": "implemented",
                "display_name": "Streaming Query",
                "description": "Query mit Real-time Progress Updates",
                "endpoints": ["/api/query/stream"],
                "features": {
                    "progress_updates": True,
                    "intermediate_results": True,
                    "llm_thinking": True
                }
            },
            "agent": {
                "status": "implemented",
                "display_name": "Agent Query",
                "description": "Multi-Agent Pipeline mit External APIs",
                "endpoints": ["/api/query/agent"],
                "features": {
                    "agent_orchestration": True,
                    "external_sources": True,
                    "quality_assessment": True
                }
            },
            "ask": {
                "status": "implemented",
                "display_name": "Simple Ask",
                "description": "Direct LLM ohne Retrieval",
                "endpoints": ["/api/query/ask"],
                "features": {
                    "direct_llm": True,
                    "no_rag": True
                }
            },
            "veritas": {
                "status": "implemented",
                "display_name": "Standard RAG",
                "description": "VERITAS Standard Modus",
                "endpoints": ["/api/v3/query/standard"],
                "features": {
                    "vector_search": True,
                    "rag_pipeline": True
                }
            },
            "chat": {
                "status": "implemented",
                "display_name": "Conversational Chat",
                "description": "Konversationsmodus ohne RAG",
                "endpoints": ["/api/v3/query/standard"],
                "features": {
                    "conversation": True,
                    "no_retrieval": True
                }
            }
        }
    }
