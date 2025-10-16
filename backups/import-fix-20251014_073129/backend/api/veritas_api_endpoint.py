#!/usr/bin/env python3
"""
FastAPI Implementation für Veritas RAG System - LEGACY VERSION
==============================================================

⚠️ DEPRECATED: Diese Datei wurde zu veritas_api_backend.py migriert
⚠️ Verwenden Sie stattdessen das neue Veritas API Backend System
⚠️ Diese Datei wird in einer zukünftigen Version entfernt

Migration Status: COMPLETED
Neue Datei: veritas_api_backend.py
Datum: 2025-09-21

Features (LEGACY):
- Komplette Flask-Kompatibilität
- Asynchrone Performance-Optimierung  
- VPB-Integration (wenn verfügbar)
- Automatische API-Dokumentation
- Echte Covina-Module Integration

Port: 5000 (gleich wie Flask für nahtlose Migration)
Dokumentation: http://localhost:5000/docs
"""
import logging
from datetime import datetime
import json
import os
from fastapi import FastAPI, HTTPException, Depends, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import asyncio
import time
import uuid
import random

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import der Universal JSON Payload Library
try:
    from shared.universal_json_payload import (
        # Universal Models
        UniversalQueryRequest, UniversalQueryResponse,
        ChatMessageRequest, ChatMessageResponse,
        FileUploadRequest, FileProcessingResponse,
        # Base Models
        MetadataPayload, SourceReference, QualityMetrics, ProcessingMetrics,
        # Enums
        RequestType, ResponseStatus, SystemComponent, QualityLevel, SecurityLevel,
        # Utility Functions
        create_request_id, create_session_id, validate_request_type,
        create_error_response, create_success_response, create_metadata
    )
    PAYLOADS_AVAILABLE = True
    logging.info("✅ Veritas Universal Payload Library geladen")
except ImportError as e:
    logging.warning(f"⚠️ Veritas Payloads nicht verfügbar: {e}")
    PAYLOADS_AVAILABLE = False
    # Fallback zu lokalen Definitionen
    from enum import Enum
    
    class RequestType(str, Enum):
        RAG = "rag"
        VPB = "vpb"
        CHAT = "chat"
        SYSTEM = "system"
        FEEDBACK = "feedback"
    
    class ResponseStatus(str, Enum):
        SUCCESS = "success"
        ERROR = "error"
        WARNING = "warning"

# ===== ZENTRALE SYSTEM MODI DEFINITION =====

class SystemModeManager:
    """Zentrale Verwaltung aller verfügbaren System-Modi"""
    
    def __init__(self):
        self._base_modes = {
            # VERITAS Core System
            "VERITAS": {
                "system": "veritas",
                "display_name": "Veritas RAG System",
                "description": "Hauptsystem für Retrieval-Augmented Generation mit Multi-Backend Support",
                "status": "implemented",
                "endpoints": ["/ask", "/search", "/chat"],
                "parameters": ["question", "model", "temperature", "max_tokens"],
                "example": "Erkläre mir das deutsche Verwaltungsrecht",
                "category": "core",
                "priority": 1
            },
            
            # COVINA Module System  
            "COVINA": {
                "system": "covina",
                "display_name": "Covina Module System",
                "description": "Erweiterte RAG-Pipeline mit Qualitäts-Enhancement und Multi-Source Integration",
                "status": "implemented" if self._check_covina_availability() else "unavailable",
                "endpoints": ["/covina/ask", "/covina/search", "/covina/quality"],
                "parameters": ["query", "sources", "quality_level", "enhancement_mode"],
                "example": "Suche Informationen zu Bebauungsplänen mit hoher Qualität",
                "category": "enhancement",
                "priority": 2
            },
            
            # VPB Process System
            "VPB": {
                "system": "vpb",
                "display_name": "VPB Verwaltungsprozesse",
                "description": "Verwaltungsprozess-Beschreibungssprache für deutsche Behörden",
                "status": "implemented" if self._check_vpb_availability() else "unavailable", 
                "endpoints": ["/vpb/ask", "/vpb/process", "/vpb/analyze"],
                "parameters": ["process_type", "analysis_depth", "compliance_check"],
                "example": "Wie läuft ein Baugenehmigungsverfahren ab?",
                "category": "domain_specific",
                "priority": 3
            },
            
            # Chat/Conversation System
            "CHAT": {
                "system": "chat",
                "display_name": "Conversation System",
                "description": "Persistente Chat-Sessions mit Kontext-Erhaltung",
                "status": "implemented" if self._check_conversation_availability() else "unavailable",
                "endpoints": ["/chat/start", "/chat/continue", "/chat/history"],
                "parameters": ["session_id", "message", "context_length"],
                "example": "Fortlaufende Diskussion über Rechtsfragen",
                "category": "interaction",
                "priority": 4
            },
            
            # Quality Management
            "QUALITY": {
                "system": "quality",
                "display_name": "Quality Enhancement",
                "description": "Qualitätsbewertung und -verbesserung für RAG-Antworten",
                "status": "implemented" if self._check_quality_availability() else "unavailable",
                "endpoints": ["/quality/analyze", "/quality/enhance", "/quality/metrics"],
                "parameters": ["content", "enhancement_level", "metrics_type"],
                "example": "Qualitätsbewertung einer generierten Antwort",
                "category": "analysis",
                "priority": 5
            },
            
            # Agent Engine System
            "AGENT": {
                "system": "agent",
                "display_name": "Agent Engine",
                "description": "Erweiterte RAG-Pipeline mit externen Datenquellen (EU LEX, Google Search, SQL)",
                "status": "implemented" if self._check_agent_availability() else "unavailable",
                "endpoints": ["/agent/query", "/agent/configure", "/agent/stats", "/agent/workers"],
                "parameters": ["query", "external_sources", "max_workers", "enable_external_sources"],
                "example": "Suche in EU-Recht und externen Datenbanken zur Baugenehmigung",
                "category": "external_integration",
                "priority": 2
            }
        }
        
        # Dynamische Modi (werden zur Laufzeit hinzugefügt)
        self._dynamic_modes = {}
    
    def _check_covina_availability(self):
        """Prüft Covina-Verfügbarkeit"""
        try:
            import veritas_api_module
            return True
        except ImportError:
            return False
    
    def _check_vpb_availability(self):
        """Prüft VPB-Verfügbarkeit"""
        try:
            from vpb_data_preparation import VPBDataPreparator
            from vpb_sqlite_db import VPBSQLiteDB
            return True
        except ImportError:
            return False
    
    def _check_conversation_availability(self):
        """Prüft Conversation-System-Verfügbarkeit"""
        try:
            # Prüfe verschiedene mögliche Conversation-Manager
            conversation_files = [
                'conversation_manager.py',
                'conversations.db',
                'covina_api_endpoint_conversation_manager.py'
            ]
            for file in conversation_files:
                if os.path.exists(file):
                    return True
            return False
        except Exception:
            return False
    
    def _check_quality_availability(self):
        """Prüft Quality-System-Verfügbarkeit"""
        try:
            from chunk_quality_management import ChunkQualityManager
            return True
        except ImportError:
            return False
    
    def _check_agent_availability(self):
        """Prüft Agent-Engine-Verfügbarkeit"""
        try:
            from backend.api.veritas_api_manager_enhanced import get_covina_manager_enhanced
            return True
        except ImportError:
            return False
    
    def register_mode(self, mode_id: str, mode_config: Dict[str, Any]):
        """Registriert einen neuen dynamischen Modus"""
        self._dynamic_modes[mode_id] = mode_config
        logger.info(f"🔧 Registered dynamic mode: {mode_id}")
    
    def get_all_modes(self) -> Dict[str, Dict[str, Any]]:
        """Gibt alle verfügbaren Modi zurück"""
        all_modes = {}
        all_modes.update(self._base_modes)
        all_modes.update(self._dynamic_modes)
        
        # Status aktualisieren (für dynamische Checks)
        for mode_id, mode_config in all_modes.items():
            if mode_id in self._base_modes:
                # Status neu prüfen für Base-Modi
                if mode_id == "COVINA":
                    mode_config["status"] = "implemented" if self._check_covina_availability() else "unavailable"
                elif mode_id == "VPB":
                    mode_config["status"] = "implemented" if self._check_vpb_availability() else "unavailable"
                elif mode_id == "CHAT":
                    mode_config["status"] = "implemented" if self._check_conversation_availability() else "unavailable"
                elif mode_id == "QUALITY":
                    mode_config["status"] = "implemented" if self._check_quality_availability() else "unavailable"
        
        return all_modes
    
    def get_available_modes(self) -> Dict[str, Dict[str, Any]]:
        """Gibt nur verfügbare Modi zurück"""
        all_modes = self.get_all_modes()
        return {k: v for k, v in all_modes.items() if v["status"] == "implemented"}
    
    def get_mode(self, mode_id: str) -> Optional[Dict[str, Any]]:
        """Gibt einen spezifischen Modus zurück"""
        all_modes = self.get_all_modes()
        return all_modes.get(mode_id.upper())

# Globale Instanz des Mode Managers
mode_manager = SystemModeManager()

# Legacy-Kompatibilität - Verfügbarkeitsprüfungen
COVINA_AVAILABLE = mode_manager._check_covina_availability()
VPB_AVAILABLE = mode_manager._check_vpb_availability()
CONVERSATION_AVAILABLE = mode_manager._check_conversation_availability()
QUALITY_AVAILABLE = mode_manager._check_quality_availability()

# Core system imports
if COVINA_AVAILABLE:
    import veritas_api_module
    logger.info("✅ Covina module loaded successfully")
else:
    logger.warning(f"❌ Covina module not available")

# VPB Integration imports
if VPB_AVAILABLE:
    from vpb_data_preparation import VPBDataPreparator
    from vpb_sqlite_db import VPBSQLiteDB  
    logger.info("✅ VPB integration loaded successfully")
else:
    logger.warning(f"❌ VPB integration not available")

# Chunk-Quality-Endpoints imports
try:
    from backend.api.veritas_api_chunk_quality_endpoints import chunk_quality_router
    CHUNK_QUALITY_ENDPOINTS_AVAILABLE = True
    logger.info("✅ Chunk-Quality endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"❌ Chunk-Quality endpoints not available: {e}")
    CHUNK_QUALITY_ENDPOINTS_AVAILABLE = False
    # Mock router für Fallback
    from fastapi import APIRouter
    chunk_quality_router = APIRouter()

try:
    from covina_api_quality_enhanced_rag import quality_rag_router
    QUALITY_RAG_AVAILABLE = True
    logger.info("✅ Quality-Enhanced RAG loaded successfully")
except ImportError as e:
    logger.warning(f"❌ Quality-Enhanced RAG not available: {e}")
    QUALITY_RAG_AVAILABLE = False
    # Mock router für Fallback
    from fastapi import APIRouter
    quality_rag_router = APIRouter()

try:
    from quality_enhanced_chat_formatter import QualityEnhancedResponseFormatter
    QUALITY_FORMATTER_AVAILABLE = True
    logger.info("✅ Quality Chat Formatter loaded successfully")
except ImportError as e:
    logger.warning(f"❌ Quality Chat Formatter not available: {e}")
    QUALITY_FORMATTER_AVAILABLE = False

# Conversation Management imports
try:
    from backend.api.veritas_api_endpoint_conversation_manager import (
        create_new_conversation, add_turn_to_conversation, get_all_conversations
    )
    CONVERSATION_AVAILABLE = True
    logger.info("✅ Conversation management loaded successfully")
except ImportError as e:
    CONVERSATION_AVAILABLE = False
    logger.warning(f"❌ Conversation management not available: {e}")

# ===== PYDANTIC MODELS =====

class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    checks: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SystemStatusResponse(BaseModel):
    status: str = "operational"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    components: Optional[Dict[str, Any]] = Field(default_factory=dict)
    performance: Optional[Dict[str, Any]] = Field(default_factory=dict)

class RAGRequest(BaseModel):
    query: str = Field(..., description="Die Benutzerfrage")
    session_id: Optional[str] = Field(None, description="Session ID für Konversations-Kontext")
    collection: Optional[str] = Field(None, description="Spezifische Collection für die Suche")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="LLM Temperature")
    max_tokens: Optional[int] = Field(150, ge=1, le=2000, description="Maximale Token-Anzahl")
    model: Optional[str] = Field("llama3:instruct", description="LLM Model Name")
    model_name: Optional[str] = Field("llama3:latest", description="Alternative model name field")
    top_p: Optional[float] = Field(0.9, ge=0.0, le=1.0, description="Top-p Parameter")
    user_profile: Optional[Dict[str, Any]] = Field(None, description="Benutzerprofil")

class SourceMetadata(BaseModel):
    """IEEE-konforme Quellen-Metadaten für wissenschaftliche Zitationen"""
    id: int = Field(..., description="1-basierte Zitations-ID")
    title: str = Field(..., description="Titel des Dokuments/Abschnitts")
    type: str = Field(default="Dokument", description="Typ: Gesetz, Verordnung, Urteil, Verwaltungsvorschrift, etc.")
    author: Optional[str] = Field(None, description="Autor/Herausgeber")
    year: Optional[str] = Field(None, description="Veröffentlichungsjahr")
    url: Optional[str] = Field(None, description="Online-Verfügbarkeit (URL)")
    source_file: Optional[str] = Field(None, description="Quelldatei")
    page: Optional[int] = Field(None, description="Seitenzahl (falls relevant)")
    confidence: Optional[float] = Field(None, description="Retrieval-Confidence Score")
    content_preview: Optional[str] = Field(None, description="Kurze Vorschau des Inhalts")

class RAGResponse(BaseModel):
    answer: str = Field(..., description="Die generierte Antwort (enthält [1], [2] Inline-Zitationen)")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Quellen (Legacy, für Kompatibilität)")
    sources_metadata: List[SourceMetadata] = Field(default_factory=list, description="IEEE-konforme Quellen-Metadaten")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Confidence Score")
    processing_time_seconds: float = Field(..., description="Verarbeitungszeit")
    session_id: str = Field(..., description="Session ID")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    suggestions: List[str] = Field(default_factory=list, description="Follow-up Vorschläge")
    # Quality Enhancement Felder
    enhanced_answer: Optional[str] = Field(None, description="Quality-Enhanced Antwort mit Indikatoren")
    quality_summary: Optional[str] = Field(None, description="Quality-Zusammenfassung")
    enhanced_sources: Optional[List[Dict[str, Any]]] = Field(None, description="Quality-Enhanced Quellen")
    citations: Optional[List[Dict[str, Any]]] = Field(None, description="Enhanced Citations")
    display_suggestions: Optional[List[str]] = Field(None, description="Display-Verbesserungsvorschläge")
    quality_info: Optional[Dict[str, Any]] = Field(None, description="Quality-Metadaten")

class VPBAnalysisRequest(BaseModel):
    query: str = Field(..., description="VPB-Prozess-Frage")
    analysis_depth: str = Field("standard", description="Analyse-Tiefe: basic, standard, detailed")
    include_suggestions: bool = Field(True, description="Verbesserungsvorschläge einschließen")
    session_id: Optional[str] = Field(None, description="Session ID")

class VPBAnalysisResponse(BaseModel):
    answer: str = Field(..., description="VPB-Analyse-Antwort")
    process_found: bool = Field(..., description="Ob ein passender Prozess gefunden wurde")
    details: Dict[str, Any] = Field(default_factory=dict, description="Prozess-Details")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="VPB-Quellen")
    suggestions: List[str] = Field(default_factory=list, description="Verbesserungsvorschläge")
    processing_time_seconds: float = Field(..., description="Verarbeitungszeit")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class StartSessionRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="Benutzer-ID")

class StartSessionResponse(BaseModel):
    session_id: str = Field(..., description="Neue Session ID")
    user_id: Optional[str] = Field(None, description="Benutzer-ID")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class FeedbackRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    rating: int = Field(..., ge=1, le=5, description="Bewertung 1-5")
    comment: Optional[str] = Field(None, description="Kommentar")
    category: Optional[str] = Field("general", description="Feedback-Kategorie")

# ===== APPLICATION LIFESPAN =====

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """
    Application lifespan management - modern FastAPI approach
    """
    # Startup
    logger.info("🚀 FastAPI Veritas RAG System starting...")
    logger.info(f"📊 VPB Integration: {'✅ Available' if VPB_AVAILABLE else '❌ Not Available'}")
    logger.info(f"🤖 Covina Module: {'✅ Available' if COVINA_AVAILABLE else '❌ Not Available'}")
    logger.info(f"💬 Conversations: {'✅ Available' if CONVERSATION_AVAILABLE else '❌ Not Available'}")
    logger.info(f"🔧 Agent Engine: {'✅ Available' if AGENT_ENGINE_AVAILABLE else '❌ Not Available'}")
    logger.info("🌐 Server ready on http://localhost:5000")
    logger.info("📚 Documentation: http://localhost:5000/docs")
    
    yield
    
    # Shutdown
    logger.info("🛑 FastAPI Veritas RAG System shutting down...")

# ===== FASTAPI APP CONFIGURATION =====

app = FastAPI(
    title="Veritas RAG System API",
    description="FastAPI Implementation des Veritas RAG Systems mit VPB-Integration und Chunk-Quality-Management",
    version="2.0.0-fastapi-production",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Router-Registrierungen
if CHUNK_QUALITY_ENDPOINTS_AVAILABLE:
    try:
        app.include_router(chunk_quality_router)
        logger.info("✅ Chunk-Quality endpoints registered")
    except Exception as e:
        logger.warning(f"❌ Failed to register chunk quality router: {e}")

if QUALITY_RAG_AVAILABLE:
    try:
        app.include_router(quality_rag_router)
        logger.info("✅ Quality-Enhanced RAG endpoints registered")
    except Exception as e:
        logger.warning(f"❌ Failed to register quality RAG router: {e}")

# Worker API Integration
try:
    from covina_api_worker_integration import router as worker_router
    app.include_router(worker_router)
    logger.info("✅ Worker API endpoints registered")
    WORKER_API_AVAILABLE = True
except Exception as e:
    logger.warning(f"❌ Failed to register worker API router: {e}")
    WORKER_API_AVAILABLE = False

# CORS Configuration für Frontend-Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: Specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== UTILITY FUNCTIONS =====

def generate_session_id() -> str:
    """Generate unique session ID"""
    return str(uuid.uuid4())

def safe_json_serialize(obj):
    """Safe JSON serialization like Flask version"""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, Exception):
        return str(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)

# VPB Integration Helper
_vpb_preparator = None
_vpb_db = None

# Quality Enhancement Formatter (Global Instance)
_quality_formatter = None

def get_quality_formatter():
    """Lazy initialization of Quality Response Formatter"""
    global _quality_formatter
    if QUALITY_FORMATTER_AVAILABLE and _quality_formatter is None:
        _quality_formatter = QualityEnhancedResponseFormatter()
    return _quality_formatter

def get_vpb_components():
    """Lazy initialization of VPB components"""
    global _vpb_preparator, _vpb_db
    if VPB_AVAILABLE:
        if _vpb_preparator is None:
            _vpb_preparator = VPBDataPreparator()
        if _vpb_db is None:
            _vpb_db = VPBSQLiteDB()
    return _vpb_preparator, _vpb_db

# ===== AGENT ENGINE INTEGRATION =====

# Agent Engine verfügbarkeit prüfen
AGENT_ENGINE_AVAILABLE = False
agent_manager = None

try:
    from backend.api.veritas_api_manager_enhanced import get_covina_manager_enhanced
    agent_manager = get_covina_manager_enhanced()
    AGENT_ENGINE_AVAILABLE = True
    logger.info("✅ Agent Engine Integration verfügbar")
except ImportError as e:
    logger.warning(f"⚠️ Agent Engine nicht verfügbar: {e}")

# Agent-spezifische Request/Response Models
class AgentQueryRequest(BaseModel):
    query: str = Field(..., description="Agent-Query für externe Datenquellen")
    session_id: Optional[str] = Field(None, description="Session ID")
    enable_external_sources: bool = Field(True, description="Externe Datenquellen aktivieren")
    max_workers: int = Field(3, ge=1, le=10, description="Maximale Anzahl paralleler Worker")
    external_sources: List[str] = Field(
        default=["eu_lex", "document_retrieval", "geo_context", "legal_framework"],
        description="Aktivierte externe Datenquellen"
    )
    user_profile: Optional[Dict[str, Any]] = Field(None, description="Benutzerprofil")

class AgentQueryResponse(BaseModel):
    answer: str = Field(..., description="Agent-generierte Antwort")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Alle Quellen")
    agent_results: Dict[str, Any] = Field(default_factory=dict, description="Detaillierte Agent-Ergebnisse")
    external_data: List[Dict[str, Any]] = Field(default_factory=list, description="Externe Datenquellen-Ergebnisse")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Gesamt-Confidence Score")
    processing_time_seconds: float = Field(..., description="Verarbeitungszeit")
    session_id: str = Field(..., description="Session ID")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    worker_stats: Dict[str, Any] = Field(default_factory=dict, description="Worker-Statistiken")

class AgentConfigRequest(BaseModel):
    source_type: str = Field(..., description="Datenquelle: google_search, legal_db, admin_db")
    config: Dict[str, Any] = Field(..., description="Konfiguration für die Datenquelle")

# ===== HEALTH & STATUS ENDPOINTS =====

@app.get("/health", response_model=HealthResponse, tags=["System"])
@app.post("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Umfassender Health Check - Flask-Kompatibel
    Unterstützt sowohl GET als auch POST wie die Flask-Version
    """
    checks = {}
    
    try:
        # VPB Integration Check
        if VPB_AVAILABLE:
            vpb_prep, vpb_db = get_vpb_components()
            checks["vpb_integration"] = "available"
            if vpb_db:
                checks["vpb_database"] = "connected"
        else:
            checks["vpb_integration"] = "not_available"
        
        # Agent Engine Check
        if AGENT_ENGINE_AVAILABLE:
            checks["agent_engine"] = "available"
            if agent_manager:
                checks["agent_status"] = agent_manager.get_module_status()
        else:
            checks["agent_engine"] = "not_available"
        
        # Database Connections
        try:
            if CONVERSATION_AVAILABLE:
                conversations = await asyncio.get_event_loop().run_in_executor(None, get_all_conversations)
                checks["conversation_db"] = "connected"
        except Exception:
            checks["conversation_db"] = "error"
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            checks=checks
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/status", response_model=SystemStatusResponse, tags=["System"]) 
async def system_status():
    """
    Umfassender System-Status - Flask-äquivalent
    """
    try:
        import psutil
        import os
        
        # System Performance
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        performance = {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_mb": memory.available // 1024 // 1024,
            "disk_usage_percent": disk.percent,
            "disk_free_gb": disk.free // 1024 // 1024 // 1024
        }
        
        # Component Status  
        components = {
            "api_framework": "FastAPI",
            "async_support": True,
            "auto_documentation": True,
            "vpb_integration": VPB_AVAILABLE,
            "covina_integration": COVINA_AVAILABLE,
            "conversation_system": CONVERSATION_AVAILABLE,
            "agent_engine": AGENT_ENGINE_AVAILABLE,
            "process_id": os.getpid(),
            "start_time": datetime.now().isoformat()
        }
        
        if VPB_AVAILABLE:
            vpb_prep, vpb_db = get_vpb_components()
            if vpb_db:
                try:
                    stats = await asyncio.get_event_loop().run_in_executor(None, vpb_db.get_statistics)
                    components["vpb_processes_count"] = stats.get("total_processes", 0)
                except:
                    components["vpb_processes_count"] = "error"
        
        # Agent Engine Status
        if AGENT_ENGINE_AVAILABLE and agent_manager:
            try:
                components["agent_stats"] = agent_manager.get_agent_stats()
                components["worker_stats"] = agent_manager.get_worker_stats()
            except Exception as e:
                components["agent_error"] = str(e)
        
        return SystemStatusResponse(
            status="operational",
            timestamp=datetime.now().isoformat(),
            components=components,
            performance=performance
        )
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/get_models", tags=["System"])
async def get_models():
    """
    Verfügbare LLM-Modelle von Ollama - Flask-äquivalent
    """
    try:
        import ollama
        
        # Async wrapper für Ollama-Call
        models_response = await asyncio.get_event_loop().run_in_executor(None, ollama.list)
        
        models = []
        for model in models_response.get('models', []):
            # Debug: Log the model structure
            logger.debug(f"Raw model data: {model}")
            
            # Ollama verwendet 'model' als Feld-Namen, nicht 'name'
            model_name = model.get('model', model.get('name', 'unknown'))
            
            models.append({
                "name": model_name,
                "size": model.get('size', 0),
                "modified_at": model.get('modified_at', '').isoformat() if hasattr(model.get('modified_at', ''), 'isoformat') else str(model.get('modified_at', '')),
                "digest": model.get('digest', '')[:16] + "..." if model.get('digest') else "",
                "details": model.get('details', {}),
            })
        
        # Sortiere Modelle alphabetisch
        models.sort(key=lambda x: x['name'])
        
        return {
            "success": True,
            "models": models,
            "count": len(models),
            "timestamp": datetime.now().isoformat(),
            "source": "ollama"
        }
        
    except ImportError:
        logger.warning("Ollama not available, providing default models")
        models = [
            {"name": "llama3.1:8b", "size": 0, "modified_at": "", "digest": "", "source": "fallback"},
            {"name": "llama3.1:70b", "size": 0, "modified_at": "", "digest": "", "source": "fallback"},
            {"name": "qwen2.5:7b", "size": 0, "modified_at": "", "digest": "", "source": "fallback"},
            {"name": "mistral:7b", "size": 0, "modified_at": "", "digest": "", "source": "fallback"}
        ]
        
        return {
            "success": True,
            "models": models,
            "count": len(models),
            "timestamp": datetime.now().isoformat(),
            "source": "fallback_no_ollama"
        }
        
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        
        # Emergency fallback
        models = [
            {"name": "llama3.1:8b", "size": 0, "modified_at": "", "digest": "", "source": "emergency"},
            {"name": "llama3.1:70b", "size": 0, "modified_at": "", "digest": "", "source": "emergency"},
            {"name": "qwen2.5:7b", "size": 0, "modified_at": "", "digest": "", "source": "emergency"},
            {"name": "mistral:7b", "size": 0, "modified_at": "", "digest": "", "source": "emergency"}
        ]
        
        return {
            "success": False,
            "models": models,
            "count": len(models),
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "source": "error_fallback"
        }

# ===== RAG CORE ENDPOINT =====

@app.post("/ask", response_model=RAGResponse, tags=["RAG"])
async def rag_ask(request: RAGRequest):
    """
    Haupt-RAG-Endpoint - Flask-Logik in FastAPI
    Integriert die gesamte Covina-Module-Logik asynchron
    """
    start_time = time.time()
    session_id = request.session_id or generate_session_id()
    
    try:
        if not COVINA_AVAILABLE:
            # Fallback without Covina
            response_data = {
                "answer": "Covina-Modul nicht verfügbar. System läuft im reduzierten Modus.",
                "sources": [],
                "confidence_score": 0.0,
                "processing_time_seconds": time.time() - start_time,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "suggestions": ["Covina-Modul installieren für volle Funktionalität"]
            }
        else:
            # Covina Module Query - async wrapper with correct parameter mapping
            query_params = {
                "session_id": session_id,
                "query": request.query,
                "user_profile": request.user_profile or {"user_id": session_id, "experience_years": 5},  # Use provided or default user profile
                "model_name": request.model_name or request.model or "llama3:latest",
                "temperature": request.temperature,
                "attachments": None
            }
            
            # Async execution of Covina query with correct function name
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: veritas_api_module.answer_query(**query_params)
            )
            
            # Format response like Flask version
            if isinstance(result, dict):
                response_data = {
                    "answer": result.get("response", "Keine Antwort verfügbar"),
                    "sources": result.get("sources", []),
                    "confidence_score": result.get("confidence", 0.0),
                    "processing_time_seconds": time.time() - start_time,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "suggestions": result.get("suggestions", []),
                    "quality_info": result.get("quality_info", {}),
                    "rag_metadata": result.get("rag_metadata", {})
                }
            else:
                # Fallback for string response
                response_data = {
                    "answer": str(result) if result else "Keine Antwort verfügbar",
                    "sources": [],
                    "confidence_score": 0.5,
                    "processing_time_seconds": time.time() - start_time,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "suggestions": [],
                    "quality_info": {},
                    "rag_metadata": {}
                }
        
        # Quality Enhancement Processing
        if QUALITY_FORMATTER_AVAILABLE:
            try:
                formatter = get_quality_formatter()
                if formatter:
                    enhanced_data = formatter.format_enhanced_response(response_data)
                    # Merge enhanced data into response_data
                    response_data.update({
                        "enhanced_answer": enhanced_data.get("enhanced_answer"),
                        "quality_summary": enhanced_data.get("quality_summary"),
                        "enhanced_sources": enhanced_data.get("enhanced_sources"),
                        "citations": enhanced_data.get("citations"),
                        "display_suggestions": enhanced_data.get("display_suggestions"),
                    })
                    logger.info(f"✅ Quality Enhancement applied for session: {session_id}")
                else:
                    logger.warning("Quality formatter not initialized properly")
            except Exception as quality_error:
                logger.error(f"Quality enhancement failed: {quality_error}")
                # Continue with original response_data ohne Quality Enhancement
        
        # Log conversation
        if CONVERSATION_AVAILABLE:
            try:
                # Erstelle eine neue Konversation falls keine Session-ID vorhanden
                user_id = "api_user"  # Default user für API calls
                retrieved_chunks = response_data.get("retrieved_chunks", [])
                chunk_ids = [chunk.get("id", "") for chunk in retrieved_chunks] if retrieved_chunks else []
                
                await asyncio.get_event_loop().run_in_executor(
                    None, add_turn_to_conversation, session_id, request.query, 
                    response_data["answer"], chunk_ids, user_id
                )
            except Exception as log_error:
                logger.warning(f"Failed to save conversation: {log_error}")
        
        return RAGResponse(**response_data)
        
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

# ===== VPB ENDPOINTS =====

@app.post("/vpb/analyze", response_model=VPBAnalysisResponse, tags=["VPB"])
async def vpb_analyze(request: VPBAnalysisRequest):
    """
    VPB-Prozessanalyse - Flask-äquivalent
    """
    if not VPB_AVAILABLE:
        raise HTTPException(status_code=503, detail="VPB integration not available")
    
    start_time = time.time()
    
    try:
        vpb_prep, vpb_db = get_vpb_components()
        
        # Async VPB analysis
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: vpb_prep.analyze_process_query(
                request.question, 
                depth=request.analysis_depth,
                include_suggestions=request.include_suggestions
            )
        )
        
        processing_time = time.time() - start_time
        
        return VPBAnalysisResponse(
            answer=result.get("answer", "Keine VPB-Antwort verfügbar"),
            process_found=result.get("process_found", False),
            details=result.get("details", {}),
            sources=result.get("sources", []),
            suggestions=result.get("suggestions", []) if request.include_suggestions else [],
            processing_time_seconds=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"VPB analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"VPB analysis failed: {str(e)}")

@app.get("/vpb/processes", tags=["VPB"])
async def vpb_get_processes(
    limit: int = Query(10, description="Maximum number of processes to return"),
    offset: int = Query(0, description="Number of processes to skip"),
    search: Optional[str] = Query(None, description="Search term for process names")
):
    """
    VPB-Prozesse auflisten - Flask-äquivalent
    """
    if not VPB_AVAILABLE:
        raise HTTPException(status_code=503, detail="VPB integration not available")
    
    try:
        vpb_prep, vpb_db = get_vpb_components()
        
        # Async database query
        processes = await asyncio.get_event_loop().run_in_executor(
            None, lambda: vpb_db.get_processes(limit=limit, offset=offset, search=search)
        )
        
        total_count = await asyncio.get_event_loop().run_in_executor(
            None, vpb_db.count_processes
        )
        
        return {
            "processes": processes,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "search": search,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"VPB processes error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch VPB processes: {str(e)}")

@app.post("/vpb/import", tags=["VPB"])
async def vpb_import_process(file: UploadFile = File(...)):
    """
    VPB-Prozess importieren - Flask-äquivalent für File Upload
    """
    if not VPB_AVAILABLE:
        raise HTTPException(status_code=503, detail="VPB integration not available")
    
    if not file.filename.endswith(('.json', '.xml', '.vpb')):
        raise HTTPException(status_code=400, detail="Unsupported file format. Use .json, .xml, or .vpb")
    
    try:
        # Read file content
        content = await file.read()
        
        vpb_prep, vpb_db = get_vpb_components()
        
        # Async import processing
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: vpb_prep.import_process_file(
                file.filename, content
            )
        )
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Import completed"),
            "process_id": result.get("process_id"),
            "filename": file.filename,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"VPB import error: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# ===== CONVERSATION MANAGEMENT =====

@app.post("/start_session", response_model=StartSessionResponse, tags=["Conversations"])
async def start_session(request: StartSessionRequest):
    """
    Erstellt neue Konversations-Session - Flask-äquivalent
    """
    try:
        if CONVERSATION_AVAILABLE:
            # Async wrapper für Database-Call
            session_id = await asyncio.get_event_loop().run_in_executor(
                None, create_new_conversation, request.user_id
            )
        else:
            # Fallback wenn Conversation System nicht verfügbar
            session_id = generate_session_id()
        
        if session_id:
            logger.info(f"Neue Session erstellt: {session_id} für User {request.user_id}")
            return StartSessionResponse(
                session_id=session_id,
                user_id=request.user_id,
                timestamp=datetime.now().isoformat()
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create conversation session")
            
    except Exception as e:
        logger.error(f"Start session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations", tags=["Conversations"])
async def get_conversations(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, description="Maximum conversations to return")
):
    """
    Konversationen abrufen - Flask-äquivalent
    """
    if not CONVERSATION_AVAILABLE:
        return {"conversations": [], "message": "Conversation system not available"}
    
    try:
        # Async conversation retrieval
        conversations = await asyncio.get_event_loop().run_in_executor(
            None, lambda: get_all_conversations(user_id=user_id, limit=limit)
        )
        
        return {
            "conversations": conversations or [],
            "count": len(conversations) if conversations else 0,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Conversation retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversations: {str(e)}")

# ===== AGENT ENGINE ENDPOINTS =====

@app.post("/agent/query", response_model=AgentQueryResponse, tags=["Agent Engine"])
async def agent_query(request: AgentQueryRequest):
    """
    Agent-Engine Query mit externen Datenquellen
    Führt erweiterte Suche mit EU LEX, Google Search und anderen externen APIs durch
    """
    if not AGENT_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent Engine nicht verfügbar")
    
    start_time = time.time()
    session_id = request.session_id or generate_session_id()
    
    try:
        logger.info(f"🤖 Agent Query: {request.query[:100]}... (Session: {session_id})")
        
        # Führe Agent-Engine-Verarbeitung durch
        agent_result = await agent_manager.process_agent_query(
            query=request.query,
            session_id=session_id,
            user_profile=request.user_profile
        )
        
        processing_time = time.time() - start_time
        
        # Extrahiere Daten aus Agent-Ergebnis
        answer = agent_result.get('final_answer', 'Keine Antwort generiert')
        sources = agent_result.get('all_sources', [])
        external_data = []
        
        # Worker-Ergebnisse verarbeiten
        worker_results = agent_result.get('worker_results', {})
        for worker_type, result in worker_results.items():
            if result.get('success'):
                external_data.append({
                    "worker_type": worker_type,
                    "summary": result.get('summary', ''),
                    "confidence": result.get('confidence_score', 0.0),
                    "data": result.get('data', {}),
                    "sources": result.get('sources', [])
                })
        
        # Statistiken sammeln
        worker_stats = {}
        if hasattr(agent_result, 'processing_stats'):
            worker_stats = agent_result.processing_stats
        
        # Confidence Score berechnen
        confidence_scores = [data.get('confidence', 0.0) for data in external_data]
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        logger.info(f"✅ Agent Query completed in {processing_time:.2f}s (Confidence: {overall_confidence:.2f})")
        
        return AgentQueryResponse(
            answer=answer,
            sources=sources,
            agent_results=agent_result,
            external_data=external_data,
            confidence_score=overall_confidence,
            processing_time_seconds=processing_time,
            session_id=session_id,
            worker_stats=worker_stats
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Agent Query Error: {e}")
        
        return AgentQueryResponse(
            answer=f"Agent-Verarbeitung fehlgeschlagen: {str(e)}",
            sources=[],
            agent_results={"error": str(e)},
            external_data=[],
            confidence_score=0.0,
            processing_time_seconds=processing_time,
            session_id=session_id,
            worker_stats={"error": str(e)}
        )

@app.post("/agent/configure", tags=["Agent Engine"])
async def configure_agent_source(request: AgentConfigRequest):
    """
    Konfiguriert externe Datenquellen für Agent-Engine
    """
    if not AGENT_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent Engine nicht verfügbar")
    
    try:
        agent_manager.configure_external_data_source(
            source_type=request.source_type,
            config=request.config
        )
        
        logger.info(f"✅ Agent source {request.source_type} konfiguriert")
        
        return {
            "success": True,
            "message": f"Datenquelle {request.source_type} erfolgreich konfiguriert",
            "source_type": request.source_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Agent configuration error: {e}")
        raise HTTPException(status_code=500, detail=f"Konfiguration fehlgeschlagen: {str(e)}")

@app.get("/agent/stats", tags=["Agent Engine"])
async def get_agent_stats():
    """
    Gibt Agent-Engine-Statistiken zurück
    """
    if not AGENT_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent Engine nicht verfügbar")
    
    try:
        agent_stats = agent_manager.get_agent_stats()
        worker_stats = agent_manager.get_worker_stats()
        module_status = agent_manager.get_module_status()
        
        return {
            "agent_engine": agent_stats,
            "workers": worker_stats,
            "modules": module_status,
            "external_sources": {
                "eu_lex": "available",
                "google_search": "configured" if agent_manager.external_workers.get("google_search") else "not_configured",
                "veritas_db": "available"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Agent stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Statistiken-Abruf fehlgeschlagen: {str(e)}")

@app.get("/agent/workers", tags=["Agent Engine"])
async def get_worker_info():
    """
    Gibt Informationen über verfügbare Worker zurück
    """
    if not AGENT_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent Engine nicht verfügbar")
    
    try:
        worker_info = {
            "available_workers": [
                {
                    "type": "document_retrieval",
                    "description": "Interne VERITAS Dokumentensuche",
                    "status": "active",
                    "cache_ttl": 300
                },
                {
                    "type": "geo_context",
                    "description": "Geografischer Kontext und Zuständigkeiten",
                    "status": "active",
                    "cache_ttl": 1800
                },
                {
                    "type": "legal_framework",
                    "description": "Rechtliche Rahmenanalyse",
                    "status": "active",
                    "cache_ttl": 3600
                },
                {
                    "type": "eu_lex",
                    "description": "EU-Rechtsportal-Integration",
                    "status": "active",
                    "cache_ttl": 3600
                }
            ],
            "external_apis": {
                "google_search": {
                    "status": "configured" if agent_manager.external_workers.get("google_search") else "not_configured",
                    "description": "Google Custom Search API"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return worker_info
        
    except Exception as e:
        logger.error(f"❌ Worker info error: {e}")
        raise HTTPException(status_code=500, detail=f"Worker-Info-Abruf fehlgeschlagen: {str(e)}")

# ===== ADDITIONAL ENDPOINTS =====

@app.post("/feedback", tags=["System"])
async def submit_feedback(request: FeedbackRequest):
    """
    Feedback-System - Flask-äquivalent
    """
    try:
        # Log feedback for analysis
        feedback_data = {
            "session_id": request.session_id,
            "rating": request.rating,
            "comment": request.comment,
            "timestamp": datetime.now().isoformat(),
            "category": request.category
        }
        
        # Async logging
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: logger.info(f"Feedback received: {json.dumps(feedback_data, default=safe_json_serialize)}")
        )
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@app.get("/metadata", tags=["System"])
async def get_metadata():
    """
    System-Metadaten - Flask-äquivalent
    """
    try:
        metadata = {
            "api_version": "2.0.0-fastapi-production",
            "framework": "FastAPI",
            "features": {
                "async_processing": True,
                "auto_documentation": True,
                "pydantic_validation": True,
                "cors_enabled": True,
                "vpb_integration": VPB_AVAILABLE,
                "covina_integration": COVINA_AVAILABLE,
                "conversation_system": CONVERSATION_AVAILABLE
            },
            "endpoints": {
                "documentation": "/docs",
                "redoc": "/redoc", 
                "openapi_spec": "/openapi.json",
                "health_check": "/health",
                "system_status": "/status"
            },
            "performance": {
                "async_support": True,
                "parallel_processing": True,
                "request_validation": True,
                "response_serialization": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return metadata
        
    except Exception as e:
        logger.error(f"Metadata retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metadata: {str(e)}")

# ===== UNIVERSAL SYSTEM ENDPOINTS =====

class SystemModeResponse(BaseModel):
    modes: Dict[str, Dict[str, Any]] = Field(..., description="Verfügbare System Modi")
    available_count: int = Field(..., description="Anzahl verfügbare Modi")
    total_count: int = Field(..., description="Gesamtanzahl definierter Modi")
    default_mode: Optional[str] = Field(None, description="Standard-Modus")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

@app.get("/modes", response_model=SystemModeResponse, tags=["System"])
async def get_system_modes():
    """
    Liefert alle verfügbaren System-Modi (Veritas, Covina, VPB, etc.)
    
    Dies ist der zentrale Endpoint für die Modi-Abfrage aller Backend-Systeme.
    Ersetzt die spezifischen /vpb/modes, /covina/modes etc. Endpoints.
    """
    try:
        all_modes = mode_manager.get_all_modes()
        available_modes = mode_manager.get_available_modes()
        
        # Standard-Modus bestimmen (erster verfügbarer Modus nach Priorität)
        default_mode = None
        if available_modes:
            sorted_modes = sorted(
                available_modes.items(), 
                key=lambda x: x[1].get("priority", 999)
            )
            default_mode = sorted_modes[0][0] if sorted_modes else None
        
        return SystemModeResponse(
            modes=all_modes,
            available_count=len(available_modes),
            total_count=len(all_modes),
            default_mode=default_mode,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"System modes retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system modes: {str(e)}")

# ===== VPB SPECIFIC ENDPOINTS =====

class VPBModeResponse(BaseModel):
    modes: List[Dict[str, Any]] = Field(..., description="Verfügbare VPB Modi")
    total_count: int = Field(..., description="Anzahl verfügbare Modi")
    active_mode: Optional[str] = Field(None, description="Aktuell aktiver Modus")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class VPBProcessRequest(BaseModel):
    process_type: str = Field(..., description="Prozesstyp (create, edit, analyze, validate)")
    data: Dict[str, Any] = Field(default_factory=dict, description="Prozessdaten")
    mode: Optional[str] = Field("standard", description="Verarbeitungsmodus")
    session_id: Optional[str] = Field(None, description="Session ID")

class VPBProcessResponse(BaseModel):
    success: bool = Field(..., description="Operation erfolgreich")
    result: Dict[str, Any] = Field(default_factory=dict, description="Prozessergebnis")
    process_id: Optional[str] = Field(None, description="Prozess-ID")
    message: str = Field(..., description="Status-Nachricht")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# DEPRECATED: Use /modes instead
@app.get("/vpb/modes", response_model=VPBModeResponse, tags=["VPB"], deprecated=True)
async def get_vpb_modes_legacy():
    """
    [DEPRECATED] Liefert VPB-spezifische Modi - use /modes instead
    """
    try:
        # Hole VPB-spezifische Modi aus dem zentralen System
        vpb_mode = mode_manager.get_mode("VPB")
        if not vpb_mode:
            raise HTTPException(status_code=404, detail="VPB mode not found")
        
        # Legacy Format für Rückwärtskompatibilität
        legacy_modes = [
            {
                "mode": "ASK",
                "display_name": "VPB Prozess Abfrage",
                "description": "Stellt Fragen zu Verwaltungsprozessen",
                "status": vpb_mode["status"],
                "endpoint": "/vpb/ask"
            },
            {
                "mode": "VPB",
                "display_name": "VPB Core System",
                "description": vpb_mode["description"],
                "status": vpb_mode["status"],
                "endpoint": "/vpb/core"
            }
        ]
        
        return VPBModeResponse(
            modes=legacy_modes,
            total_count=len(legacy_modes),
            active_mode="ASK" if vpb_mode["status"] == "implemented" else None
        )
        
    except Exception as e:
        logger.error(f"VPB legacy modes error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve VPB modes: {str(e)}")

@app.post("/vpb/process", response_model=VPBProcessResponse, tags=["VPB"])
async def handle_vpb_process(request: VPBProcessRequest):
    """
    Zentraler Endpoint für alle VPB Prozess-Operationen
    """
    try:
        if not VPB_AVAILABLE:
            raise HTTPException(status_code=503, detail="VPB System not available")
        
        session_id = request.session_id or generate_session_id()
        
        if request.process_type == "create":
            # Neuen Prozess erstellen (Stub)
            result = {
                "process_id": f"vpb_{str(uuid.uuid4())}",  # Vollständige UUID für Eindeutigkeit
                "status": "created",
                "elements": [],
                "connections": []
            }
            message = f"Prozess erfolgreich erstellt in Modus: {request.mode}"
            
        elif request.process_type == "edit":
            # Prozess bearbeiten (Stub)
            result = {
                "process_id": request.data.get("process_id", "unknown"),
                "status": "modified",
                "changes": len(request.data.get("modifications", []))
            }
            message = "Prozess erfolgreich bearbeitet"
            
        elif request.process_type == "analyze":
            # Prozess analysieren (Stub)
            result = {
                "analysis_score": 0.85,
                "compliance_status": "passed",
                "recommendations": [
                    "Frist für Genehmigung spezifizieren",
                    "Rechtsgrundlage ergänzen"
                ]
            }
            message = "Analyse erfolgreich durchgeführt"
            
        elif request.process_type == "validate":
            # Prozess validieren (Stub)
            result = {
                "validation_status": "valid",
                "errors": [],
                "warnings": ["Beschreibung könnte detaillierter sein"],
                "suggestions": ["BPMN 2.0 Export empfohlen"]
            }
            message = "Validierung erfolgreich abgeschlossen"
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown process_type: {request.process_type}")
        
        return VPBProcessResponse(
            success=True,
            result=result,
            process_id=result.get("process_id"),
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VPB process handling error: {e}")
        raise HTTPException(status_code=500, detail=f"VPB process failed: {str(e)}")

# Spezifische Modi als separate Endpoints (Stubs für zukünftige Implementierung)

@app.post("/vpb/ask", response_model=VPBAnalysisResponse, tags=["VPB-Modes"])
async def vpb_ask_mode(request: VPBAnalysisRequest):
    """
    VPB ASK Modus - Beantwortet Fragen zu Verwaltungsprozessen
    """
    start_time = time.time()
    
    try:
        if not VPB_AVAILABLE:
            # Fallback Antwort
            return VPBAnalysisResponse(
                answer="VPB System nicht verfügbar. Bitte installieren Sie die VPB-Komponenten.",
                process_found=False,
                details={},
                sources=[],
                suggestions=["VPB System installieren", "Testdaten laden"],
                processing_time_seconds=time.time() - start_time,
                timestamp=datetime.now().isoformat()
            )
        
        # VPB-spezifische Logik hier implementieren
        vpb_prep, vpb_db = get_vpb_components()
        
        # Beispiel-Implementierung (zu erweitern)
        answer = f"Analysiere Verwaltungsprozess für: '{request.query}'\n\nTiefe: {request.analysis_depth}"
        process_found = True
        
        details = {
            "analysis_depth": request.analysis_depth,
            "include_suggestions": request.include_suggestions,
            "matched_processes": ["Beispiel-Prozess-1", "Beispiel-Prozess-2"]
        }
        
        sources = [
            {
                "type": "vpb_process",
                "name": "Beispiel Verwaltungsprozess",
                "confidence": 0.92
            }
        ]
        
        suggestions = [
            "Rechtsgrundlage § 35 BauGB beachten",
            "Fristen gemäß VwVfG einhalten",
            "Bürgerbeteiligung prüfen"
        ] if request.include_suggestions else []
        
        return VPBAnalysisResponse(
            answer=answer,
            process_found=process_found,
            details=details,
            sources=sources,
            suggestions=suggestions,
            processing_time_seconds=time.time() - start_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"VPB ASK error: {e}")
        raise HTTPException(status_code=500, detail=f"VPB ASK failed: {str(e)}")

@app.post("/vpb/edit", tags=["VPB-Modes"])
async def vpb_edit_mode(data: Dict[str, Any]):
    """
    VPB EDIT Modus - Stub für Prozess-Bearbeitung
    """
    return {
        "status": "not_implemented", 
        "message": "VPB EDIT Modus ist in Entwicklung",
        "received_data": data,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/vpb/agent", tags=["VPB-Modes"])  
async def vpb_agent_mode(data: Dict[str, Any]):
    """
    VPB AGENT Modus - Stub für intelligenten VPB Assistant
    """
    return {
        "status": "not_implemented",
        "message": "VPB AGENT Modus ist in Planung",
        "received_data": data,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/vpb/core", tags=["VPB-Modes"])
async def vpb_core_mode(data: Dict[str, Any]):
    """
    VPB Core System - Direkter Zugriff auf VPB Funktionen
    """
    if not VPB_AVAILABLE:
        raise HTTPException(status_code=503, detail="VPB Core System not available")
    
    return {
        "status": "not_implemented",
        "message": "VPB Core Integration ist in Entwicklung", 
        "vpb_available": VPB_AVAILABLE,
        "received_data": data,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/vpb/analyze", tags=["VPB-Modes"])
async def vpb_analyze_mode(data: Dict[str, Any]):
    """
    VPB ANALYZE Modus - Stub für Prozess-Analyse
    """
    return {
        "status": "not_implemented",
        "message": "VPB ANALYZE Modus ist in Entwicklung",
        "received_data": data,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/vpb/template", tags=["VPB-Modes"])
async def vpb_template_mode(data: Dict[str, Any]):
    """
    VPB TEMPLATE Modus - Stub für Template-System
    """
    return {
        "status": "not_implemented",
        "message": "VPB TEMPLATE System ist in Entwicklung",
        "received_data": data,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/vpb/export", tags=["VPB-Modes"])
async def vpb_export_mode(data: Dict[str, Any]):
    """
    VPB EXPORT Modus - Stub für Export-System
    """
    return {
        "status": "not_implemented",
        "message": "VPB EXPORT System ist in Planung",
        "received_data": data,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/vpb/compliance", tags=["VPB-Modes"])
async def vpb_compliance_mode(data: Dict[str, Any]):
    """
    VPB COMPLIANCE Modus - Stub für Compliance-Check
    """
    return {
        "status": "not_implemented", 
        "message": "VPB COMPLIANCE Check ist in Planung",
        "received_data": data,
        "timestamp": datetime.now().isoformat()
    }

# ===== MAIN EXECUTION =====

def check_port_availability(host: str, port: int) -> bool:
    """Prüft ob ein Port verfügbar ist"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0  # Port ist verfügbar wenn Connection fehlschlägt
    except Exception:
        return False

def find_available_port(host: str, start_port: int, max_attempts: int = 10) -> int:
    """Findet einen verfügbaren Port beginnend bei start_port"""
    for port in range(start_port, start_port + max_attempts):
        if check_port_availability(host, port):
            return port
    return None

# ===== CHAT SYSTEM ENDPOINTS =====

class ChatStartRequest(BaseModel):
    question: str = Field(..., description="Die erste Nachricht für die Chat-Session")
    session_id: Optional[str] = Field(None, description="Optional: Bestehende Session ID")
    model: str = Field(default="llama3:latest", description="LLM Modell für den Chat")
    temperature: float = Field(default=0.7, description="LLM Temperature")
    max_tokens: int = Field(default=500, description="Maximale Token-Anzahl")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Chat-Antwort")
    session_id: str = Field(..., description="Session ID für weitere Nachrichten")
    model_used: str = Field(..., description="Verwendetes LLM Modell")
    processing_time_seconds: float = Field(..., description="Verarbeitungszeit in Sekunden")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

@app.post("/chat/start", response_model=ChatResponse, tags=["Chat"])
async def start_chat_session(request: ChatStartRequest):
    """
    Startet eine neue Chat-Session oder setzt eine bestehende Session fort
    """
    try:
        start_time = time.time()
        
        # Session ID generieren falls nicht vorhanden
        session_id = request.session_id or f"chat_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Für jetzt verwenden wir den standard /ask Endpoint als Fallback
        # In einer vollständigen Implementierung würde hier ein Chat-Manager verwendet
        ask_request = RAGRequest(
            question=request.question,
            session_id=session_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            model=request.model,
            collection=None
        )
        
        # Verwende den bestehenden ask Endpoint
        rag_response = await rag_ask(ask_request)
        
        processing_time = time.time() - start_time
        
        # Chat-Response erstellen
        chat_response = ChatResponse(
            answer=rag_response.answer,
            session_id=session_id,
            model_used=request.model,
            processing_time_seconds=processing_time
        )
        
        logger.info(f"💬 Chat-Session gestartet: {session_id}")
        return chat_response
        
    except Exception as e:
        logger.error(f"Chat start error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat session start failed: {str(e)}")

@app.post("/chat/continue", response_model=ChatResponse, tags=["Chat"])
async def continue_chat_session(request: ChatStartRequest):
    """
    Setzt eine bestehende Chat-Session fort
    """
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Session ID required for continuing chat")
    
    # Für jetzt identisch mit start_chat_session
    return await start_chat_session(request)

@app.get("/chat/history/{session_id}", tags=["Chat"])
async def get_chat_history(session_id: str):
    """
    Ruft die Chat-Historie für eine Session ab
    """
    # Placeholder - in einer vollständigen Implementierung würde hier die Historie abgerufen
    return {
        "session_id": session_id,
        "history": [],
        "message": "Chat history feature not yet implemented",
        "timestamp": datetime.now().isoformat()
    }

# ===== UNIVERSAL V2 ENDPOINTS =====

@app.post("/v2/query", tags=["Universal-v2"])
async def universal_query_v2(request: dict):
    """
    🌟 UNIVERSAL ENDPOINT v2 - Neue standardisierte Payload-Struktur
    
    Universeller Endpoint für alle Query-Arten mit der neuen Veritas Payload Library:
    - Einheitliche Request/Response-Struktur für alle Systeme
    - Vollständige Type Safety mit Pydantic (wenn verfügbar)
    - Erweiterte Error Handling und Metadata
    - Performance Tracking und Quality Enhancement
    
    Unterstützte Request Types:
    - "rag" -> Standard RAG-Verarbeitung (Veritas)
    - "vpb" -> VPB-Prozess-Analyse  
    - "chat" -> Chat-Session
    - "covina" -> Covina LLM System
    - "system" -> System-Queries
    """
    start_time = time.time()
    
    # Validiere und konvertiere Request falls Payloads verfügbar
    if PAYLOADS_AVAILABLE:
        try:
            validated_request = UniversalQueryRequest(**request)
            request = validated_request
        except Exception as e:
            logger.error(f"Request validation failed: {e}")
            return {
                "status": "error",
                "error_code": "INVALID_REQUEST",
                "error_message": f"Request validation failed: {str(e)}",
                "processing_time_seconds": time.time() - start_time
            }
    
    if not PAYLOADS_AVAILABLE:
        # Fallback für v2/query ohne Payload Library
        logger.warning("⚠️ Payload Library nicht verfügbar - verwende Fallback-Modus")
        # Einfache dict-basierte Verarbeitung
        question = request.get('question', 'Keine Frage')
        request_type = request.get('request_type', 'rag')
        session_id = request.get('session_id') or f"session_{int(time.time())}"
        
        # Fallback RAG-Response
        fallback_response = {
            "status": "success",
            "request_id": f"req_{int(time.time())}",
            "session_id": session_id,
            "processing_time_seconds": time.time() - start_time,
            "answer": f"Fallback-Antwort für '{question}' (Payload Library nicht verfügbar)",
            "sources": [],
            "confidence_score": 0.5,
            "model_used": "fallback",
            "suggestions": ["Payload Library installieren für volle Funktionalität"],
            "metadata": {
                "endpoint": "/v2/query",
                "mode": "fallback",
                "payload_available": False
            }
        }
        return fallback_response
    
    try:
        # Unterstütze sowohl dict als auch objekt-Zugriff
        request_type = getattr(request, 'request_type', None) or request.get('request_type')
        question = getattr(request, 'question', None) or request.get('question')
        request_id = getattr(request, 'request_id', None) or request.get('request_id', create_request_id())
        session_id = getattr(request, 'session_id', None) or request.get('session_id') or create_session_id()
        model = getattr(request, 'model', None) or request.get('model', 'llama3:instruct')
        
        logger.info(f"🔄 Universal Query v2: {request_type} - ID: {request_id}")
        
        # Route basierend auf request_type
        if request_type == RequestType.RAG or request_type == "rag":
            # Echte RAG-Verarbeitung mit Covina Module
            try:
                # Verwende echtes Covina Module falls verfügbar
                if COVINA_AVAILABLE:
                    # Covina-Parameter vorbereiten
                    query_params = {
                        'session_id': session_id,
                        'query': question,
                        'user_profile': {'user_id': session_id, 'experience_years': 3},
                        'model_name': model,
                        'temperature': getattr(request, 'temperature', None) or request.get('temperature', 0.7),
                        'attachments': None
                    }
                    
                    logger.info(f"🔄 Starte Covina-Anfrage mit Parameters: {query_params}")
                    
                    # Echte Covina-Anfrage
                    import veritas_api_module
                    covina_result = veritas_api_module.answer_query(**query_params)
                    
                    logger.info(f"✅ Covina-Result erhalten: {type(covina_result)}, Keys: {list(covina_result.keys()) if isinstance(covina_result, dict) else 'Not dict'}")
                    
                    # Echte Antwort extrahieren
                    answer = covina_result.get('answer', 'Keine Antwort vom LLM erhalten.')
                    sources = covina_result.get('sources', [])
                    rag_metadata = covina_result.get('rag_metadata', {})
                    
                    logger.info(f"✅ Echte Covina-Antwort: {len(answer)} Zeichen, {len(sources)} Quellen")
                    
                else:
                    # Fallback: Demo-Antwort
                    answer = f"🤖 RAG-Antwort (v2 Demo) für: {question}"
                    sources = [
                        {
                            "title": "Demo RAG Source v2",
                            "content": f"Kontext für: {question[:50] if question else 'N/A'}...",
                            "confidence": 0.95,
                            "metadata": {"source_type": "demo", "version": "v2"}
                        }
                    ]
                    rag_metadata = {"demo": True}
                    logger.warning("⚠️ Covina nicht verfügbar - verwende Demo-Antwort")
                
            except Exception as e:
                logger.error(f"❌ Fehler bei Covina-Anfrage: {e}")
                answer = f"Fehler bei der Verarbeitung: {str(e)}"
                sources = []
                rag_metadata = {"error": True}
            
            response_data = {
                "status": "success",
                "request_id": request_id,
                "session_id": session_id,
                "processing_time_seconds": time.time() - start_time,
                "answer": answer,
                "sources": sources,
                "confidence_score": 0.89,
                "suggestions": ["🔍 Weitere Details?", "📚 Verwandte Themen?", "💡 Vertiefung gewünscht?"],
                "model_used": model,
                "quality_score": 0.92,
                "data": {
                    "rag_metadata": rag_metadata,
                    "enhanced": True,
                    "covina_available": COVINA_AVAILABLE
                },
                "metadata": {
                    "endpoint": "/v2/query", 
                    "type": "rag",
                    "payload_version": "1.0.0"
                }
            }
            
            # Verwende UniversalQueryResponse falls verfügbar, sonst dict
            if PAYLOADS_AVAILABLE:
                return UniversalQueryResponse(**response_data)
            else:
                return response_data
            
            
        elif request.request_type == RequestType.VPB:
            # VPB-Verarbeitung
            answer = f"🏛️ VPB-Analyse (v2) für: {request.question}"
            
            return UniversalQueryResponse(
                status=ResponseStatus.SUCCESS,
                request_id=request.request_id,
                session_id=session_id,
                processing_time_seconds=time.time() - start_time,
                answer=answer,
                sources=[
                    {
                        "title": "VPB Prozess Referenz v2",
                        "content": f"Verwaltungsprozess für: {request.question[:50]}...",
                        "process_id": "VPB_2025_001",
                        "metadata": {"department": "verwaltung", "version": "v2"}
                    }
                ],
                process_found=True,
                process_details={
                    "analysis_depth": request.analysis_depth or "standard",
                    "process_category": "general",
                    "complexity": "medium",
                    "estimated_duration": "2-5 Werktage"
                },
                process_recommendations=[
                    "✅ Prozess-Optimierung möglich",
                    "📋 Digitalisierung empfohlen", 
                    "⚡ Automatisierung prüfen"
                ],
                suggestions=["🔧 Prozess optimieren", "📊 Weitere Analyse", "🎯 Spezialisierung"],
                model_used=request.model,
                metadata={
                    "endpoint": "/v2/query",
                    "type": "vpb", 
                    "payload_version": "1.0.0",
                    "vpb_enhanced": True
                }
            )
            
        elif request.request_type == RequestType.CHAT:
            # Chat-Verarbeitung
            answer = f"💬 Chat-Antwort (v2): {request.question}"
            
            return UniversalQueryResponse(
                status=ResponseStatus.SUCCESS,
                request_id=request.request_id,
                session_id=session_id,
                processing_time_seconds=time.time() - start_time,
                answer=answer,
                model_used=request.model,
                context_used=[
                    {"role": "user", "content": request.question},
                    {"role": "assistant", "content": "Kontext wird verfolgt..."}
                ],
                conversation_id=session_id,
                suggestions=["💭 Erzähl mir mehr", "🤔 Andere Perspektive?", "📝 Zusammenfassung?"],
                metadata={
                    "endpoint": "/v2/query",
                    "type": "chat",
                    "payload_version": "1.0.0",
                    "conversation_mode": request.parameters.get("conversation_mode", "standard")
                }
            )
            
        elif request.request_type == RequestType.COVINA:
            # Covina LLM-Verarbeitung
            answer = f"🧠 Covina LLM (v2) Antwort: {request.question}"
            
            return UniversalQueryResponse(
                status=ResponseStatus.SUCCESS,
                request_id=request.request_id,
                session_id=session_id,
                processing_time_seconds=time.time() - start_time,
                answer=answer,
                model_used=request.model,
                covina_response={
                    "model_type": "covina_enhanced",
                    "reasoning_steps": ["Analyse", "Kontext", "Generierung"],
                    "confidence": 0.94
                },
                model_performance={
                    "tokens_per_second": 45.2,
                    "memory_usage_mb": 234.5,
                    "gpu_utilization": 0.67
                },
                suggestions=["🚀 Covina erweitert", "🔬 Tiefe Analyse", "⚡ Optimierung"],
                metadata={
                    "endpoint": "/v2/query",
                    "type": "covina",
                    "payload_version": "1.0.0",
                    "covina_mode": request.parameters.get("covina_mode", "standard")
                }
            )
            
        elif request.request_type == RequestType.SYSTEM:
            # System-Query
            system_info = {
                "version": "2.0.0",
                "uptime_seconds": time.time() - start_time + 3600,  # Mock uptime
                "active_sessions": 12,
                "processed_requests": 1547,
                "system_health": "excellent"
            }
            
            return UniversalQueryResponse(
                status=ResponseStatus.SUCCESS,
                request_id=request.request_id,
                session_id=session_id,
                processing_time_seconds=time.time() - start_time,
                answer=f"🖥️ System-Status: {request.question}",
                data=system_info,
                metadata={
                    "endpoint": "/v2/query",
                    "type": "system",
                    "payload_version": "1.0.0"
                }
            )
            
        else:
            # Unbekannter Request Type
            return UniversalQueryResponse(
                status=ResponseStatus.ERROR,
                request_id=request.request_id,
                session_id=session_id,
                processing_time_seconds=time.time() - start_time,
                answer="",
                error_code="UNSUPPORTED_REQUEST_TYPE",
                error_message=f"Request type '{request.request_type}' wird noch nicht unterstützt",
                metadata={
                    "endpoint": "/v2/query",
                    "supported_types": [t.value for t in RequestType],
                    "payload_version": "1.0.0"
                }
            )
            
    except Exception as e:
        logger.error(f"❌ Universal Query v2 Fehler: {e}")
        return UniversalQueryResponse(
            status=ResponseStatus.ERROR,
            request_id=getattr(request, 'request_id', create_request_id()),
            session_id=getattr(request, 'session_id', None) or create_session_id(),
            processing_time_seconds=time.time() - start_time,
            answer="",
            error_code="INTERNAL_ERROR",
            error_message=str(e),
            error_details={"exception_type": type(e).__name__},
            metadata={
                "endpoint": "/v2/query",
                "error_context": "universal_query_v2",
                "payload_version": "1.0.0"
            }
        )

@app.get("/v2/system/info", response_model=UniversalQueryResponse if PAYLOADS_AVAILABLE else dict, tags=["Universal-v2"])
async def system_info_v2():
    """
    🌟 SYSTEM INFO v2 - Systeminfo mit standardisierter Payload-Struktur
    
    Liefert umfassende System-Informationen im neuen Universal Format:
    - Verfügbare Request Types und Components
    - System-Performance und Health Status  
    - Feature-Verfügbarkeit und Endpoints
    - Payload Library Version und Schema
    """
    start_time = time.time()
    
    if not PAYLOADS_AVAILABLE:
        return {
            "status": "error",
            "error_code": "PAYLOADS_UNAVAILABLE",
            "error_message": "Veritas Payload Library nicht verfügbar"
        }
    
    try:
        # Sammle erweiterte Systeminfo
        system_info = {
            "veritas_system": {
                "version": "2.0.0",
                "build": "2025.08.29",
                "environment": "production"
            },
            "payload_library": {
                "version": "1.0.0",
                "schema_version": "1.0.0",
                "available": PAYLOADS_AVAILABLE
            },
            "supported_request_types": [t.value for t in RequestType],
            "available_models": ["llama3:instruct", "codellama:latest", "phi3:latest", "covina:enhanced"],
            "available_modes": mode_manager.get_all_modes(),
            "system_components": {
                "veritas": {"status": "active", "version": "2.0.0"},
                "vpb": {"status": "active" if VPB_AVAILABLE else "inactive", "version": "1.5.0"},
                "covina": {"status": "active" if COVINA_AVAILABLE else "inactive", "version": "1.0.0"},
                "ollama": {"status": "active", "version": "0.1.x"},
                "chromadb": {"status": "active", "version": "0.4.x"}
            },
            "endpoints": {
                "legacy": ["/ask", "/vpb/ask", "/chat/start", "/conversations"],
                "universal_v2": ["/v2/query", "/v2/system/info"],
                "system": ["/health", "/status", "/modes", "/get_models"]
            },
            "features": {
                "rag": True,
                "vpb": VPB_AVAILABLE, 
                "chat": True,
                "covina": COVINA_AVAILABLE,
                "quality_enhancement": True,
                "conversations": CONVERSATION_AVAILABLE,
                "payload_validation": PAYLOADS_AVAILABLE,
                "type_safety": True,
                "performance_tracking": True,
                "error_handling": True
            },
            "performance": {
                "uptime_seconds": 7200,  # Mock data
                "processed_requests": 1547,
                "active_sessions": 12,
                "avg_response_time_ms": 234.5,
                "system_load": 0.45
            }
        }
        
        return UniversalQueryResponse(
            status=ResponseStatus.SUCCESS,
            request_id=create_request_id(),
            processing_time_seconds=time.time() - start_time,
            answer="🖥️ Veritas System v2.0 - Vollständige Systeminfo abgerufen",
            data=system_info,
            metadata={
                "endpoint": "/v2/system/info",
                "payload_version": "1.0.0",
                "info_type": "comprehensive"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ System Info v2 Fehler: {e}")
        return UniversalQueryResponse(
            status=ResponseStatus.ERROR,
            request_id=create_request_id(),
            processing_time_seconds=time.time() - start_time,
            answer="",
            error_code="SYSTEM_INFO_ERROR",
            error_message=str(e),
            metadata={
                "endpoint": "/v2/system/info",
                "payload_version": "1.0.0"
            }
        )

@app.get("/v2/examples", response_model=dict, tags=["Universal-v2"])
async def payload_examples_v2():
    """
    📚 PAYLOAD EXAMPLES v2 - Beispiele für die neue Payload-Struktur
    
    Liefert Beispiel-Requests und -Responses für alle unterstützten Request Types.
    Hilfreich für Client-Entwicklung und API-Integration.
    """
    if not PAYLOADS_AVAILABLE:
        return {
            "error": "Veritas Payload Library nicht verfügbar",
            "fallback_examples": {
                "rag_request": {
                    "request_type": "rag",
                    "question": "Was ist Verwaltungsrecht?",
                    "model": "llama3:instruct"
                }
            }
        }
    
    try:
        examples = {
            "rag_request": {
                "request_type": "rag",
                "question": "Was sind die wichtigsten Grundsätze des Verwaltungsrechts?",
                "max_results": 5,
                "model": "llama3:instruct",
                "metadata": {"example": True}
            },
            "vpb_request": {
                "request_type": "vpb_analysis",
                "question": "Analysiere diese VPB-Daten",
                "metadata": {"example": True}
            },
            "chat_request": {
                "request_type": "chat",
                "message": "Hallo, ich brauche Hilfe bei rechtlichen Fragen",
                "session_id": "example_session",
                "metadata": {"example": True}
            },
            "system_request": {
                "request_type": "system",
                "question": "Systemstatus anzeigen",
                "metadata": {"example": True}
            },
            "covina_request": {
                "request_type": "covina",
                "question": "Erweiterte LLM-Analyse durchführen",
                "parameters": {"covina_mode": "enhanced"},
                "metadata": {"example": True}
            }
        }
        
        return {
            "message": "Veritas Universal Payload Examples v2",
            "payload_version": "1.0.0",
            "examples": examples,
            "usage_info": {
                "endpoint": "/v2/query",
                "method": "POST",
                "content_type": "application/json",
                "documentation": "/docs"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Examples v2 Fehler: {e}")
        return {
            "error": f"Fehler beim Generieren der Beispiele: {str(e)}",
            "payload_version": "1.0.0"
        }

# ===== SERVER STARTUP =====
# ===== SERVER STARTUP =====

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Port-Verfügbarkeitsprüfung
    default_host = "0.0.0.0"
    default_port = 5000
    
    logger.info("🚀 Starting FastAPI Veritas RAG System (Production)")
    logger.info("🔍 Checking port availability...")
    
    if not check_port_availability(default_host, default_port):
        logger.warning(f"⚠️ Port {default_port} ist bereits belegt!")
        
        # Automatische Port-Suche
        available_port = find_available_port(default_host, default_port + 1)
        
        if available_port:
            logger.info(f"✅ Alternativer Port gefunden: {available_port}")
            default_port = available_port
        else:
            logger.error(f"❌ Keine verfügbaren Ports gefunden (geprüft: {default_port}-{default_port+9})")
            logger.error("💡 Mögliche Lösungen:")
            logger.error("   - Anderen VERITAS-Prozess beenden")
            logger.error("   - Port 5000 freigeben")
            logger.error("   - Anderes Terminal verwenden")
            sys.exit(1)
    else:
        logger.info(f"✅ Port {default_port} ist verfügbar")
    
    # Production-ready configuration
    logger.info(f"🌐 Server: http://localhost:{default_port}")
    logger.info(f"📚 Documentation: http://localhost:{default_port}/docs")
    logger.info(f"🔧 Alternative Docs: http://localhost:{default_port}/redoc")
    
    try:
        uvicorn.run(
            "api_endpoint:app",  # This is the correct module name
            host=default_host,
            port=default_port,
            reload=False,  # Production setting
            workers=1,     # Single worker for development/testing
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server gestoppt durch Benutzer")
    except Exception as e:
        logger.error(f"❌ Server-Fehler: {e}")
        sys.exit(1)

"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "api_endpoint"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...bmPjojA="  # Gekuerzt fuer Sicherheit
module_organization_key = "d04932bebbdabc412ecf434f5b6b54271bb478116833ee1a16879d10d58c2f54"
module_file_key = "df02713ab5f2e20a0052eab0e5a719371ee04e584b60bee2e8d02553b02a0a67"
module_version = "1.0"
module_protection_level = 3
# === END PROTECTION KEYS ===
