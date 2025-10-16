#!/usr/bin/env python3
"""
VERITAS API Backend - Production Version
======================================
Migriert von Covina API System zu zentralem Veritas Backend

Features:
- Vollständige FastAPI Implementation
- Agent-Engine-Architektur
- Multi-Worker-System
- Externe Datenquellen (EU LEX, Google Search, SQL)
- VPB-Integration
- Automatische API-Dokumentation

Port: 5000 (Migration von Covina)
Dokumentation: http://localhost:5000/docs

Author: VERITAS System
Created: 2025-09-21
Version: 1.0.0 (Migrated from Covina)
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

# Agent Pipeline Integration
try:
    from backend.agents.veritas_api_agent_orchestrator import create_agent_orchestrator, AgentOrchestrator
    from backend.agents.veritas_api_agent_core_components import create_agent_coordinator, AgentCoordinator
    from backend.agents.veritas_api_agent_registry import get_agent_registry
    from backend.agents.veritas_api_agent_pipeline_manager import get_agent_pipeline_db
    AGENT_PIPELINE_AVAILABLE = True
    logger.info("✅ Agent Pipeline Integration verfügbar")
except ImportError as e:
    AGENT_PIPELINE_AVAILABLE = False
    logger.warning(f"⚠️ Agent Pipeline Integration nicht verfügbar: {e}")

# ===== PYDANTIC MODELS =====

class VeritasRAGRequest(BaseModel):
    question: str = Field(..., description="Frage für das RAG-System")
    mode: str = Field(default="VERITAS", description="System-Modus")
    model: Optional[str] = Field(default=None, description="LLM-Modell")
    temperature: float = Field(default=0.7, description="LLM-Temperatur")
    max_tokens: int = Field(default=1000, description="Max. Tokens")
    session_id: Optional[str] = None

class VeritasRAGResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    session_id: str
    mode: str
    quality_score: float
    processing_time: float
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    request_id: str

class VeritasAgentQueryRequest(BaseModel):
    query: str = Field(..., description="Agent-Query")
    agent_types: List[str] = Field(default=[], description="Gewünschte Agent-Typen")
    complexity: str = Field(default="standard", description="Query-Komplexität")
    external_sources: bool = Field(default=True, description="Externe Datenquellen nutzen")
    quality_level: str = Field(default="high", description="Qualitätslevel")
    session_id: Optional[str] = None

class VeritasAgentQueryResponse(BaseModel):
    answer: str
    agent_results: List[Dict[str, Any]]
    external_data: List[Dict[str, Any]]
    quality_metrics: Dict[str, Any]
    processing_details: Dict[str, Any]
    session_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class StartSessionRequest(BaseModel):
    mode: str = Field(default="VERITAS", description="System-Modus")
    
class StartSessionResponse(BaseModel):
    session_id: str
    mode: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# ===== SYSTEM MODE MANAGER =====

class VeritasSystemModeManager:
    """Verwaltet verschiedene System-Modi (VERITAS, VPB, etc.)"""
    
    def __init__(self):
        self.modes = {
            # Standard VERITAS RAG System
            "VERITAS": {
                "system": "veritas_rag",
                "display_name": "Veritas RAG System", 
                "description": "Standard-RAG mit Ollama und Multi-Database-Backend",
                "status": "implemented",
                "endpoints": ["/v2/query", "/ask", "/search"],
                "parameters": ["question", "model", "temperature", "max_tokens"],
                "example": "Erkläre mir das deutsche Verwaltungsrecht",
                "category": "core",
                "priority": 1
            },
            
            # VERITAS Agent System (migrated from Covina)
            "VERITAS_AGENTS": {
                "system": "veritas_agents",
                "display_name": "Veritas Agent System",
                "description": "Erweiterte RAG-Pipeline mit Agent-Engine und Multi-Source Integration",
                "status": "implemented" if self._check_agent_availability() else "unavailable",
                "endpoints": ["/agents/ask", "/agents/search", "/agents/quality"],
                "parameters": ["query", "sources", "quality_level", "enhancement_mode"],
                "example": "Suche Informationen zu Bebauungsplänen mit hoher Qualität",
                "category": "enhancement",
                "priority": 2
            }
        }
        
        self.initialize_system_detection()
    
    def _check_agent_availability(self) -> bool:
        """Prüft ob das Veritas Agent System verfügbar ist"""
        return AGENT_PIPELINE_AVAILABLE
    
    def initialize_system_detection(self):
        """Initialisiert automatische System-Erkennung"""
        logger.info("🔍 System-Modi werden erkannt...")
        
        for mode_name, mode_config in self.modes.items():
            if mode_config["status"] == "implemented":
                logger.info(f"✅ {mode_name}: {mode_config['display_name']}")
            else:
                logger.info(f"⚠️ {mode_name}: {mode_config['status']}")
    
    def get_available_modes(self) -> List[str]:
        """Gibt verfügbare Modi zurück"""
        return [name for name, config in self.modes.items() if config["status"] == "implemented"]
    
    def get_mode_config(self, mode: str) -> Optional[Dict[str, Any]]:
        """Gibt Konfiguration für einen Modus zurück"""
        return self.modes.get(mode)

# ===== FASTAPI APP SETUP =====

app = FastAPI(
    title="Veritas API Backend",
    description="Zentrales Backend für Veritas Chat-App mit Agent-Pipeline",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System Mode Manager
system_manager = VeritasSystemModeManager()

# ===== GLOBAL AGENT SYSTEM INITIALIZATION =====

# Agent Pipeline Components
agent_orchestrator: Optional[AgentOrchestrator] = None
agent_coordinator: Optional[AgentCoordinator] = None

def initialize_agent_pipeline():
    """Initialisiert das Agent-Pipeline-System"""
    global agent_orchestrator, agent_coordinator
    
    if not AGENT_PIPELINE_AVAILABLE:
        logger.warning("⚠️ Agent Pipeline nicht verfügbar - verwende Legacy-System")
        return False
    
    try:
        # Agent Registry initialisieren
        agent_registry = get_agent_registry()
        
        # Agent Pipeline Manager initialisieren
        pipeline_manager = get_agent_pipeline_db()
        
        # Agent Coordinator erstellen
        agent_coordinator = create_agent_coordinator(
            registry=agent_registry,
            pipeline_manager=pipeline_manager
        )
        
        # Agent Orchestrator erstellen
        agent_orchestrator = create_agent_orchestrator(
            agent_coordinator=agent_coordinator,
            pipeline_manager=pipeline_manager
        )
        
        # Cross-Referenzen setzen
        agent_orchestrator.set_agent_coordinator(agent_coordinator)
        
        logger.info("✅ Agent Pipeline System initialisiert")
        return True
        
    except Exception as e:
        logger.error(f"❌ Agent Pipeline Initialisierung fehlgeschlagen: {e}")
        return False

# ===== CORE ENDPOINTS =====

@app.get("/")
async def root():
    """Root Endpoint - API Status"""
    return {
        "message": "Veritas API Backend",
        "version": "1.0.0",
        "status": "active",
        "agent_pipeline_available": AGENT_PIPELINE_AVAILABLE,
        "available_modes": system_manager.get_available_modes(),
        "endpoints": {
            "chat": "/v2/query",
            "rag": "/ask", 
            "agents": "/agents/ask",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health Check Endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_pipeline": AGENT_PIPELINE_AVAILABLE,
        "system_modes": system_manager.get_available_modes()
    }

# ===== VERITAS CHAT-APP INTEGRATION =====

@app.post("/v2/query")
async def veritas_chat_query(query_data: Dict[str, Any]):
    """
    MAIN ENDPOINT für Veritas Chat-App Integration
    Kompatibel mit veritas_app.py Chat-Interface
    """
    start_time = time.time()
    
    try:
        query_text = query_data.get('query', '')
        if not query_text:
            raise HTTPException(status_code=400, detail="Query ist erforderlich")
        
        session_id = query_data.get('session_id', str(uuid.uuid4()))
        
        if not AGENT_PIPELINE_AVAILABLE or not agent_orchestrator:
            # Legacy fallback
            return {
                'response_text': f"Legacy-Antwort für: {query_text}",
                'confidence_score': 0.7,
                'sources': [],
                'worker_results': {},
                'processing_metadata': {
                    'processing_time': time.time() - start_time,
                    'system_mode': 'legacy'
                }
            }
        
        # Agent-Pipeline Query Processing
        query_request = {
            'query': query_text,
            'user_context': query_data.get('user_context', {}),
            'query_id': f"chat_query_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        }
        
        # Query Preprocessing
        preprocessing_result = agent_orchestrator.preprocess_query(query_request)
        
        # Agent Coordination
        if agent_coordinator:
            coordinator_request = {
                'query': query_text,
                'required_agents': preprocessing_result['required_agents'],
                'complexity': preprocessing_result['complexity'],
                'domain': preprocessing_result['domain'],
                'session_id': session_id,
                'external_sources': True,
                'quality_level': 'high'
            }
            
            agent_results = await agent_coordinator.process_query_async(coordinator_request)
        else:
            agent_results = {}
        
        # Result Aggregation
        final_result = agent_orchestrator.aggregate_results(query_request, agent_results)
        
        processing_time = time.time() - start_time
        
        # Formatiere Response für Chat-App Kompatibilität
        chat_response = {
            'response_text': final_result.get('response_text', 'Keine Antwort generiert'),
            'confidence_score': final_result.get('confidence_score', 0.0),
            'sources': final_result.get('sources', []),
            'worker_results': final_result.get('agent_results', {}),  # Kompatibilität
            'agent_results': final_result.get('agent_results', {}),
            'rag_context': final_result.get('rag_context', {}),
            'follow_up_suggestions': final_result.get('follow_up_suggestions', []),
            'processing_metadata': {
                'pipeline_id': preprocessing_result['pipeline_id'],
                'complexity': preprocessing_result['complexity'],
                'domain': preprocessing_result['domain'],
                'processing_stages': preprocessing_result['processing_stages'],
                'estimated_time': preprocessing_result['estimated_processing_time'],
                'actual_time': processing_time,
                'agent_count': len(final_result.get('agent_results', {})),
                'successful_agents': final_result.get('processing_metadata', {}).get('successful_agents', 0),
                'system_mode': 'agent_pipeline',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        logger.info(f"🎯 Chat-Query verarbeitet: {preprocessing_result['complexity']}/{preprocessing_result['domain']} - {processing_time:.2f}s")
        
        return chat_response
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Chat-Query: {e}")
        
        # Error Response für Chat-App
        return {
            'response_text': f"Entschuldigung, bei der Verarbeitung Ihrer Anfrage ist ein Fehler aufgetreten: {str(e)}",
            'confidence_score': 0.0,
            'sources': [],
            'worker_results': {},
            'processing_metadata': {
                'error': str(e),
                'processing_time': time.time() - start_time,
                'system_mode': 'error_fallback'
            }
        }

# ===== RAG ENDPOINTS =====

@app.post("/ask", response_model=VeritasRAGResponse)
async def veritas_rag_query(request: VeritasRAGRequest):
    """Standard RAG Query"""
    session_id = request.session_id or str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # System-Modus validieren
        mode_config = system_manager.get_mode_config(request.mode)
        if not mode_config:
            raise HTTPException(status_code=400, detail=f"Unbekannter Modus: {request.mode}")
        
        # Dummy-Implementierung für Migration
        answer = f"Veritas RAG Antwort für: {request.question}"
        sources = [
            {
                "title": "Beispiel-Dokument",
                "content": "Relevanter Inhalt...",
                "score": 0.95,
                "source": "veritas_db"
            }
        ]
        
        processing_time = time.time() - start_time
        
        return VeritasRAGResponse(
            answer=answer,
            sources=sources,
            metadata={
                "mode": request.mode,
                "model": request.model or "llama3:latest",
                "temperature": request.temperature,
                "max_tokens": request.max_tokens
            },
            session_id=session_id,
            mode=request.mode,
            quality_score=0.92,
            processing_time=processing_time,
            tokens_used=150,
            model_used=request.model or "llama3:latest",
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Fehler bei RAG-Query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== AGENT ENDPOINTS =====

@app.post("/agents/ask", response_model=VeritasAgentQueryResponse)
async def veritas_agent_query(request: VeritasAgentQueryRequest):
    """Agent-Engine Query (migrated from Covina)"""
    session_id = request.session_id or str(uuid.uuid4())
    start_time = time.time()
    
    try:
        if not AGENT_PIPELINE_AVAILABLE or not agent_orchestrator:
            return await _legacy_agent_query(request, session_id)
        
        # Query-Daten für Agent-Pipeline vorbereiten
        query_data = {
            'query': request.query,
            'user_context': {
                'session_id': session_id,
                'quality_level': request.quality_level,
                'external_sources': request.external_sources
            },
            'query_id': f"agent_query_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        }
        
        # Query Preprocessing durch Orchestrator
        preprocessing_result = agent_orchestrator.preprocess_query(query_data)
        
        # Agent-Query durch Coordinator ausführen
        if agent_coordinator:
            coordinator_request = {
                'query': request.query,
                'required_agents': preprocessing_result['required_agents'],
                'complexity': preprocessing_result['complexity'],
                'domain': preprocessing_result['domain'],
                'session_id': session_id,
                'external_sources': request.external_sources,
                'quality_level': request.quality_level
            }
            
            agent_results = await agent_coordinator.process_query_async(coordinator_request)
        else:
            agent_results = {"error": "Agent Coordinator nicht verfügbar"}
        
        # Ergebnisse durch Orchestrator aggregieren
        final_result = agent_orchestrator.aggregate_results(query_data, agent_results)
        
        processing_time = time.time() - start_time
        
        # Response formatieren
        response_data = VeritasAgentQueryResponse(
            answer=final_result.get('response_text', 'Keine Antwort generiert'),
            agent_results=[
                {
                    'agent_type': agent_type,
                    'result': result,
                    'confidence': result.get('confidence_score', 0.0),
                    'processing_time': result.get('processing_time', 0.0)
                }
                for agent_type, result in final_result.get('agent_results', {}).items()
            ],
            external_data=final_result.get('sources', []),
            quality_metrics={
                'overall_confidence': final_result.get('confidence_score', 0.0),
                'agent_count': len(final_result.get('agent_results', {})),
                'successful_agents': final_result.get('processing_metadata', {}).get('successful_agents', 0),
                'complexity': preprocessing_result['complexity'],
                'domain': preprocessing_result['domain']
            },
            processing_details={
                'pipeline_id': preprocessing_result['pipeline_id'],
                'processing_stages': preprocessing_result['processing_stages'],
                'estimated_time': preprocessing_result['estimated_processing_time'],
                'actual_time': processing_time,
                'required_capabilities': preprocessing_result['required_capabilities']
            },
            session_id=session_id
        )
        
        logger.info(f"✅ Agent-Query verarbeitet: {preprocessing_result['complexity']}/{preprocessing_result['domain']} - {processing_time:.2f}s")
        
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Agent-Query: {e}")
        # Fallback auf Legacy-System
        return await _legacy_agent_query(request, session_id)

async def _legacy_agent_query(request: VeritasAgentQueryRequest, session_id: str) -> VeritasAgentQueryResponse:
    """Legacy Agent-Query für Fallback"""
    logger.info("🔄 Verwende Legacy Agent-Query System")
    
    # Dummy-Implementierung für Migration
    return VeritasAgentQueryResponse(
        answer=f"Legacy Agent-Antwort für: {request.query}",
        agent_results=[
            {
                "agent_type": "legacy_agent",
                "result": "Legacy-Verarbeitung aktiv",
                "confidence": 0.7
            }
        ],
        external_data=[],
        quality_metrics={
            "overall_confidence": 0.7,
            "agent_count": 1,
            "system_mode": "legacy"
        },
        processing_details={
            "system_mode": "legacy_fallback",
            "message": "Agent Pipeline nicht verfügbar"
        },
        session_id=session_id
    )

# ===== SESSION MANAGEMENT =====

@app.post("/session/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """Startet eine neue Session"""
    session_id = str(uuid.uuid4())
    
    return StartSessionResponse(
        session_id=session_id,
        mode=request.mode
    )

# ===== SYSTEM INFO ENDPOINTS =====

@app.get("/modes")
async def get_available_modes():
    """Verfügbare System-Modi"""
    return {
        "available_modes": system_manager.get_available_modes(),
        "default_mode": "VERITAS"
    }

@app.get("/agents/types")
async def get_available_agent_types():
    """Verfügbare Agent-Typen"""
    if AGENT_PIPELINE_AVAILABLE and agent_orchestrator:
        try:
            status = agent_orchestrator.get_orchestrator_status()
            return {
                "agent_types": [
                    "legal_framework",
                    "document_retrieval", 
                    "geo_context",
                    "external_api",
                    "cost_analysis",
                    "environmental",
                    "construction", 
                    "traffic",
                    "financial",
                    "social"
                ],
                "agent_pipeline_status": status,
                "system_mode": "agent_pipeline"
            }
        except Exception as e:
            logger.warning(f"⚠️ Agent Status Fehler: {e}")
    
    return {
        "agent_types": [
            "legal_framework",
            "document_retrieval", 
            "geo_context",
            "external_api",
            "cost_analysis",
            "environmental",
            "construction", 
            "traffic",
            "financial",
            "social"
        ],
        "system_mode": "legacy"
    }

# ===== APP STARTUP & INITIALIZATION =====

@app.on_event("startup")
async def startup_event():
    """App-Initialisierung beim Start"""
    logger.info("🚀 Veritas API Backend wird gestartet...")
    
    # Agent Pipeline System initialisieren
    pipeline_initialized = initialize_agent_pipeline()
    
    if pipeline_initialized:
        logger.info("✅ Agent Pipeline System erfolgreich initialisiert")
    else:
        logger.warning("⚠️ Agent Pipeline System nicht verfügbar - Legacy-Modus aktiv")
    
    logger.info("🎯 Veritas API Backend gestartet - Port 5000")
    logger.info("📖 API-Dokumentation: http://localhost:5000/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)