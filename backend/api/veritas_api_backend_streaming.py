#!/usr/bin/env python3
"""
VERITAS API Backend - Mit Streaming Progress System
=================================================
Erweiterte Version mit Real-time Progress Updates für Frontend

Features:
- Server-Sent Events (SSE) für Progress Updates
- Agent Deep-thinking Zwischenergebnisse
- WebSocket-ähnliche Real-time Kommunikation
- Frontend Integration für veritas_app.py

Port: 5000
Dokumentation: http://localhost:5000/docs
"""
import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# Import Streaming Progress System
try:
    from shared.pipelines.veritas_streaming_progress import (
        ProgressStage,
        ProgressType,
        VeritasProgressManager,
        VeritasProgressStreamer,
        create_progress_manager,
        create_progress_streamer,
    )

    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


class VeritasStreamingQueryRequest(BaseModel):
    query: str = Field(..., description="Query für Streaming-Verarbeitung")
    session_id: Optional[str] = None
    enable_streaming: bool = Field(default=True, description="Aktiviere Progress Streaming")
    enable_intermediate_results: bool = Field(default=True, description="Zeige Zwischenergebnisse")
    enable_llm_thinking: bool = Field(default=True, description="Zeige LLM Deep-thinking")


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


# ===== FASTAPI APP SETUP =====

app = FastAPI(
    title="Veritas API Backend (Streaming)",
    description="Veritas Backend mit Real-time Progress Updates",
    version="1.0.0-streaming",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== STREAMING PROGRESS SETUP =====

# Global Progress Manager
progress_manager: Optional[VeritasProgressManager] = None
progress_streamer: Optional[VeritasProgressStreamer] = None


def initialize_streaming_system():
    """Initialisiert das Streaming Progress System"""
    global progress_manager, progress_streamer

    if STREAMING_AVAILABLE:
        progress_manager = create_progress_manager()
        progress_streamer = create_progress_streamer(progress_manager)
        logger.info("✅ Streaming Progress System initialisiert")
        return True
    else:
        logger.warning("⚠️ Streaming System nicht verfügbar")
        return False


# ===== CORE ENDPOINTS =====


@app.get("/")
async def root():
    """Root Endpoint - API Status"""
    return {
        "message": "Veritas API Backend (Streaming)",
        "version": "1.0.0 - streaming",
        "status": "active",
        "streaming_available": STREAMING_AVAILABLE,
        "endpoints": {
            "chat": " / v2/query",
            "streaming_chat": " / v2/query / stream",
            "progress": " / progress/{session_id}",
            "rag": "/ask",
            "agents": "/agents/ask",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    """Health Check Endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "streaming_available": STREAMING_AVAILABLE}


# ===== STREAMING ENDPOINTS =====


@app.post("/v2/query/stream")
async def veritas_streaming_query(request: VeritasStreamingQueryRequest):
    """
    STREAMING ENDPOINT für Real-time Progress Updates
    Startet Verarbeitung und gibt Stream-URL zurück
    """
    session_id = request.session_id or str(uuid.uuid4())
    query_id = f"stream_query_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    if not STREAMING_AVAILABLE or not progress_manager:
        raise HTTPException(status_code=503, detail="Streaming System nicht verfügbar")

    # Progress Session starten
    progress_manager.start_session(session_id=session_id, query_id=query_id, query_text=request.query)

    # Starte Async Processing
    asyncio.create_task(_process_streaming_query(session_id, query_id, request))

    return {
        "session_id": session_id,
        "query_id": query_id,
        "stream_url": f" / progress/{session_id}",
        "message": "Verarbeitung gestartet - verbinde mit Stream für Updates",
        "estimated_time": "5-15 Sekunden",
    }


@app.get("/progress/{session_id}")
async def get_progress_stream(session_id: str):
    """
    Server-Sent Events Stream für Progress Updates
    Frontend kann hier für Real-time Updates subscriben
    """
    if not STREAMING_AVAILABLE or not progress_streamer:
        raise HTTPException(status_code=503, detail="Streaming System nicht verfügbar")

    headers = {
        "Content - Type": "text / event-stream",
        "Cache - Control": "no - cache",
        "Connection": "keep - alive",
    }

    return StreamingResponse(
        progress_streamer.create_progress_stream(session_id), media_type="text/event-stream", headers=headers
    )


async def _process_streaming_query(session_id: str, query_id: str, request: VeritasStreamingQueryRequest):
    """
    Asynchrone Query-Verarbeitung mit Progress Updates
    Simuliert komplexes Agent-Processing mit Real-time Updates
    """
    try:
        # 1. Query Analysis Stage
        progress_manager.update_stage(
            session_id,
            ProgressStage.ANALYZING_QUERY,
            {"query_length": len(request.query), "complexity_detection": "in_progress"},
        )
        await asyncio.sleep(1.0)

        # Analysiere Query
        complexity = _analyze_query_complexity(request.query)
        domain = _analyze_query_domain(request.query)

        # 2. Agent Selection Stage
        selected_agents = _select_agents_for_query(request.query, complexity, domain)
        progress_manager.update_stage(
            session_id,
            ProgressStage.SELECTING_AGENTS,
            {"selected_agents": selected_agents, "complexity": complexity, "domain": domain},
        )
        await asyncio.sleep(0.5)

        # 3. Agent Processing Stage
        progress_manager.update_stage(session_id, ProgressStage.AGENT_PROCESSING)

        agent_results = {}
        for i, agent_type in enumerate(selected_agents):
            # Agent startet
            progress_manager.update_agent_progress(session_id, agent_type, ProgressType.AGENT_START)

            # Simuliere Agent-Verarbeitung
            await asyncio.sleep(1.0 + (i * 0.5))

            # Agent-Result generieren
            agent_result = _generate_agent_result(agent_type, request.query, complexity)
            agent_results[agent_type] = agent_result

            # Zwischenergebnis hinzufügen (falls aktiviert)
            if request.enable_intermediate_results:
                progress_manager.add_intermediate_result(
                    session_id=session_id,
                    result_type=f"{agent_type}_analysis",
                    content=agent_result.get("summary", "Analyse abgeschlossen"),
                    confidence=agent_result.get("confidence_score", 0.8),
                    sources=agent_result.get("sources", []),
                )

            # Agent abgeschlossen
            progress_manager.update_agent_progress(session_id, agent_type, ProgressType.AGENT_COMPLETE, result=agent_result)

        # 4. Context Gathering Stage
        progress_manager.update_stage(session_id, ProgressStage.GATHERING_CONTEXT)
        await asyncio.sleep(1.0)

        # 5. LLM Reasoning Stage (falls aktiviert)
        if request.enable_llm_thinking:
            progress_manager.update_stage(session_id, ProgressStage.LLM_REASONING)

            thinking_steps = [
                "Analysiere gesammelte Informationen",
                "Bewerte Relevanz und Vertrauenswürdigkeit",
                "Identifiziere Wissenslücken",
                "Strukturiere finale Antwort",
                "Überprüfe Konsistenz und Vollständigkeit",
            ]

            for step in thinking_steps:
                progress_manager.add_llm_thinking_step(session_id, step, f"LLM verarbeitet: {step}")
                await asyncio.sleep(0.8)

        # 6. Synthesis Stage
        progress_manager.update_stage(session_id, ProgressStage.SYNTHESIZING)
        await asyncio.sleep(1.0)

        # Generate final response
        final_response = _synthesize_final_response(request.query, agent_results, complexity, domain)

        # 7. Finalization
        progress_manager.update_stage(session_id, ProgressStage.FINALIZING)
        await asyncio.sleep(0.5)

        # Complete session
        progress_manager.complete_session(session_id, final_response)

    except Exception as e:
        logger.error(f"❌ Streaming Query Error: {e}")
        progress_manager.update_stage(session_id, ProgressStage.ERROR)
        progress_manager.complete_session(session_id, {"error": str(e)})


def _select_agents_for_query(query: str, complexity: str, domain: str) -> List[str]:
    """Wählt Agenten basierend auf Query aus"""
    base_agents = ["geo_context", "legal_framework"]

    # Domain-spezifische Agenten
    domain_agents = {
        "building": ["construction", "document_retrieval"],
        "environmental": ["environmental", "external_api"],
        "transport": ["traffic", "external_api"],
        "business": ["financial", "document_retrieval"],
        "general": ["document_retrieval"],
    }

    selected = base_agents + domain_agents.get(domain, ["document_retrieval"])

    # Komplexitäts-basierte Erweiterung
    if complexity == "advanced":
        selected.append("financial")
        selected.append("social")

    return list(set(selected))  # Remove duplicates


def _generate_agent_result(agent_type: str, query: str, complexity: str) -> Dict[str, Any]:
    """Generiert simuliertes Agent-Ergebnis"""

    base_confidence = 0.8 if complexity == "basic" else 0.75 if complexity == "standard" else 0.7

    agent_specialties = {
        "geo_context": {
            "summary": "Geografischer Kontext und lokale Bestimmungen identifiziert",
            "details": "Relevante Gebiets- und Standortinformationen gesammelt",
            "sources": ["OpenStreetMap", "Gemeinde - DB", "Geoportal"],
        },
        "legal_framework": {
            "summary": "Rechtliche Rahmenbedingungen und Vorschriften analysiert",
            "details": "Aktuelle Gesetze und Verordnungen ausgewertet",
            "sources": ["BauGB", "VwVfG", "GemO", "Landesrecht"],
        },
        "construction": {
            "summary": "Bautechnische Aspekte und Genehmigungsverfahren bewertet",
            "details": "Bauvorschriften und technische Anforderungen geprüft",
            "sources": ["DIN - Normen", "Bauordnung", "Technische Richtlinien"],
        },
        "environmental": {
            "summary": "Umweltaspekte und Emissionsbestimmungen untersucht",
            "details": "Umweltschutzauflagen und Grenzwerte ermittelt",
            "sources": ["Umweltbundesamt", "Luftreinhaltepläne", "EU - Richtlinien"],
        },
        "financial": {
            "summary": "Kostenstrukturen und finanzielle Aspekte kalkuliert",
            "details": "Gebühren, Kosten und Förderungsmöglichkeiten analysiert",
            "sources": ["Gebührenordnung", "Förderdatenbank", "Kostenschätzungen"],
        },
        "traffic": {
            "summary": "Verkehrsrechtliche Bestimmungen und Infrastruktur bewertet",
            "details": "Verkehrsregeln und Infrastrukturanforderungen geprüft",
            "sources": ["StVO", "Verkehrsbehörde", "ÖPNV - Pläne"],
        },
        "document_retrieval": {
            "summary": "Relevante Dokumente und Formulare gefunden",
            "details": "Antragsformulare und Informationsmaterialien identifiziert",
            "sources": ["Verwaltungsportal", "Formulardatenbank", "FAQ - Sammlung"],
        },
        "external_api": {
            "summary": "Aktuelle externe Daten abgerufen",
            "details": "Live - Daten und externe Informationsquellen ausgewertet",
            "sources": ["API - Services", "Open - Data-Portale", "Echtzeitdaten"],
        },
    }

    specialty = agent_specialties.get(
        agent_type,
        {
            "summary": f"{agent_type} Analyse abgeschlossen",
            "details": f"Spezifische {agent_type} Verarbeitung durchgeführt",
            "sources": ["Standard-Quellen"],
        },
    )

    return {
        "agent_type": agent_type,
        "confidence_score": base_confidence + (0.1 * hash(query + agent_type) % 3 / 10),
        "processing_time": 1.0 + (hash(agent_type) % 10 / 10),
        "summary": specialty["summary"],
        "details": specialty["details"],
        "sources": specialty["sources"],
        "status": "completed",
    }


def _synthesize_final_response(query: str, agent_results: Dict[str, Any], complexity: str, domain: str) -> Dict[str, Any]:
    """Generiert finale synthetisierte Antwort"""

    # Sammle beste Ergebnisse
    high_confidence_results = [result for result in agent_results.values() if result.get("confidence_score", 0) > 0.75]

    # Generiere Hauptantwort
    main_response = """
**Antwort auf Ihre Frage**: {query}

**Zusammenfassung der Analyse** ({domain.title()}, {complexity.title()}):

"""

    for agent_type, result in agent_results.items():
        confidence = result.get("confidence_score", 0)
        confidence_icon = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.7 else "🔴"
        main_response += f"{confidence_icon} **{agent_type.replace('_', ' ').title()}**: {result.get('summary', 'Verarbeitung abgeschlossen')}\n\n"

    # Sammle alle Quellen
    all_sources = []
    for result in agent_results.values():
        all_sources.extend(result.get("sources", []))

    unique_sources = list(set(all_sources))[:10]  # Limitiere auf 10

    main_response += """
**Nächste Schritte**: Basierend auf der Analyse empfehlen wir Ihnen, sich zunächst über die spezifischen Anforderungen zu informieren und die entsprechenden Antragsformulare zu beschaffen.

**Hinweis**: Diese Antwort wurde durch {len(agent_results)} spezialisierte Agenten erstellt und mit einem durchschnittlichen Vertrauenswert von {sum(r.get('confidence_score', 0) for r in agent_results.values()) / len(agent_results):.0%} bewertet.
"""

    return {
        "response_text": main_response.strip(),
        "confidence_score": sum(r.get("confidence_score", 0) for r in agent_results.values()) / len(agent_results),
        "sources": [
            {"title": source, "url": f'test://{source.lower().replace(" ", "_")}', "relevance": 0.8}
            for source in unique_sources
        ],
        "agent_results": agent_results,
        "processing_metadata": {
            "complexity": complexity,
            "domain": domain,
            "agent_count": len(agent_results),
            "high_confidence_count": len(high_confidence_results),
            "processing_method": "streaming_synthesis",
        },
    }


# ===== VERITAS CHAT-APP INTEGRATION (Legacy-kompatibel) =====


@app.post("/v2/query")
async def veritas_chat_query(query_data: Dict[str, Any]):
    """
    MAIN ENDPOINT für Veritas Chat-App Integration
    Funktioniert sowohl streaming als auch non-streaming
    """
    start_time = time.time()

    try:
        query_text = query_data.get("query", "")
        if not query_text:
            raise HTTPException(status_code=400, detail="Query ist erforderlich")

        session_id = query_data.get("session_id", str(uuid.uuid4()))
        enable_streaming = query_data.get("enable_streaming", False)

        # Falls Streaming gewünscht, delegiere an Streaming-Endpoint
        if enable_streaming and STREAMING_AVAILABLE:
            # Starte Streaming-Verarbeitung
            streaming_request = VeritasStreamingQueryRequest(
                query=query_text,
                session_id=session_id,
                enable_streaming=True,
                enable_intermediate_results=True,
                enable_llm_thinking=True,
            )

            return await veritas_streaming_query(streaming_request)

        # Standard non-streaming Verarbeitung
        complexity = _analyze_query_complexity(query_text)
        domain = _analyze_query_domain(query_text)

        # Simulierte Agent-Ergebnisse (wie im Test-Backend)
        agent_results = {
            "geo_context": {
                "response_text": f"Geo - Kontext für Query: {query_text[:50]}...",
                "confidence_score": 0.85,
                "processing_time": 0.2,
                "sources": ["OpenStreetMap", "Gemeinde-DB"],
            },
            "legal_framework": {
                "response_text": f"Rechtlicher Rahmen für: {query_text[:50]}...",
                "confidence_score": 0.92,
                "processing_time": 0.3,
                "sources": ["BauGB", "VwVfG", "GemO"],
            },
            "document_retrieval": {
                "response_text": f"Relevante Dokumente zu: {query_text[:50]}...",
                "confidence_score": 0.78,
                "processing_time": 0.4,
                "sources": ["Verordnungsblatt", "Amtsblatt", "FAQ-Sammlung"],
            },
        }

        # Simuliere finale Antwort
        main_response = """
        **Antwort auf Ihre Frage**: {query_text}

        **Geo-Kontext**: Die Anfrage bezieht sich auf den lokalen Verwaltungsbereich.

        **Rechtlicher Rahmen**: Basierend auf aktueller Rechtslage sind folgende Aspekte relevant:
        - Baugesetzbuch (BauGB) Regelungen
        - Verwaltungsverfahrensgesetz (VwVfG) Bestimmungen
        - Kommunale Satzungen

        **Dokumente**: Weitere Informationen finden Sie in den verlinkten Dokumenten.

        **System**: Non-Streaming Verarbeitung (für Streaming verwenden Sie enable_streaming=true)
        """

        processing_time = time.time() - start_time

        # Chat-App Response Format
        chat_response = {
            "response_text": main_response.strip(),
            "confidence_score": 0.85,
            "sources": [
                {"title": "BauGB", "url": "test://baugesetzbuch", "relevance": 0.9},
                {"title": "VwVfG", "url": "test://verwaltungsverfahrensgesetz", "relevance": 0.8},
                {"title": "Gemeinde - FAQ", "url": "test://gemeinde - faq", "relevance": 0.7},
            ],
            "worker_results": agent_results,  # Kompatibilität mit veritas_app.py
            "agent_results": agent_results,
            "rag_context": {"query_type": complexity, "domain": domain, "context_resolved": True},
            "follow_up_suggestions": [
                "Welche Unterlagen sind für den Antrag erforderlich?",
                "Wie lange dauert das Verfahren normalerweise?",
                "Gibt es Beratungstermine?",
                "Möchten Sie Streaming-Updates aktivieren? (enable_streaming=true)",
            ],
            "processing_metadata": {
                "complexity": complexity,
                "domain": domain,
                "processing_time": processing_time,
                "agent_count": len(agent_results),
                "successful_agents": len(agent_results),
                "system_mode": "streaming_backend",
                "streaming_available": STREAMING_AVAILABLE,
                "timestamp": datetime.now().isoformat(),
            },
        }

        logger.info(f"🎯 Chat-Query verarbeitet: {complexity}/{domain} - {processing_time:.2f}s")

        return chat_response

    except Exception as e:
        logger.error(f"❌ Fehler bei Chat-Query: {e}")

        return {
            "response_text": f"Entschuldigung, bei der Verarbeitung Ihrer Anfrage ist ein Fehler aufgetreten: {str(e)}",
            "confidence_score": 0.0,
            "sources": [],
            "worker_results": {},
            "processing_metadata": {
                "error": str(e),
                "processing_time": time.time() - start_time,
                "system_mode": "error_fallback",
            },
        }


def _analyze_query_complexity(query_text: str) -> str:
    """Einfache Query-Komplexitäts-Analyse"""
    query_lower = query_text.lower()

    if any(word in query_lower for word in ["vergleichen", "analysieren", "bewerten", "wahrscheinlichkeit"]):
        return "advanced"
    elif any(word in query_lower for word in ["wie", "welche", "genehmigung", "kosten"]):
        return "standard"
    else:
        return "basic"


def _analyze_query_domain(query_text: str) -> str:
    """Einfache Query-Domain-Analyse"""
    query_lower = query_text.lower()

    if any(word in query_lower for word in ["bau", "genehmigung", "planung", "gebäude"]):
        return "building"
    elif any(word in query_lower for word in ["verkehr", "parken", "straße"]):
        return "transport"
    elif any(word in query_lower for word in ["umwelt", "lärm", "luft"]):
        return "environmental"
    elif any(word in query_lower for word in ["gewerbe", "geschäft", "betrieb"]):
        return "business"
    else:
        return "general"


# ===== PROGRESS ENDPOINTS =====


@app.get("/progress/status/{session_id}")
async def get_session_progress(session_id: str):
    """Holt aktuellen Progress-Status für Session"""
    if not STREAMING_AVAILABLE or not progress_manager:
        raise HTTPException(status_code=503, detail="Streaming System nicht verfügbar")

    progress_status = progress_manager.get_session_progress(session_id)

    if not progress_status:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    return progress_status


# ===== RAG & AGENT ENDPOINTS (Legacy-kompatibel) =====


@app.post("/ask", response_model=VeritasRAGResponse)
async def veritas_rag_query(request: VeritasRAGRequest):
    """Standard RAG Query - Test Implementation"""
    session_id = request.session_id or str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        # Test RAG Response
        answer = f"Test RAG-Antwort für: {request.question}"
        sources = [
            {
                "title": "Test - Dokument 1",
                "content": "Relevanter Test - Inhalt...",
                "score": 0.95,
                "source": "test_veritas_db",
            }
        ]

        processing_time = time.time() - start_time

        return VeritasRAGResponse(
            answer=answer,
            sources=sources,
            metadata={
                "mode": request.mode,
                "model": request.model or "test - llama3:latest",
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "streaming_available": STREAMING_AVAILABLE,
            },
            session_id=session_id,
            mode=request.mode,
            quality_score=0.90,
            processing_time=processing_time,
            tokens_used=100,
            model_used=request.model or "test-llama3:latest",
            request_id=request_id,
        )

    except Exception as e:
        logger.error(f"Fehler bei Test RAG-Query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== SESSION MANAGEMENT =====


@app.post("/session/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """Startet eine neue Session"""
    session_id = str(uuid.uuid4())

    return StartSessionResponse(session_id=session_id, mode=request.mode)


from backend.orchestration.unified_orchestrator_v7 import UnifiedOrchestratorV7

# ===== V7 API ENDPOINT =====


class V7QueryRequest(BaseModel):
    query: str = Field(..., description="Benutzerfrage für die v7 API")
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    enable_streaming: bool = False


class V7QueryResponse(BaseModel):
    answer: str
    confidence: float
    scientific_process: Dict[str, Any]
    execution_time_ms: float
    metadata: Dict[str, Any]


orchestrator_v7 = UnifiedOrchestratorV7(
    config_dir="config",
    method_id="default_method",
    ollama_client=None,
    uds3_strategy=None,
    agent_orchestrator=None,
    enable_streaming=True,
)


@app.post("/api/v7/query", response_model=V7QueryResponse)
async def v7_query_endpoint(request: V7QueryRequest):
    """
    v7 API Endpoint: Führt Scientific Method Query mit UnifiedOrchestratorV7 aus
    """
    try:
        if request.enable_streaming:
            # Streaming-Modus: NDJSON-Events (optional, hier nur Hinweis)
            return JSONResponse(
                status_code=501, content={"error": "Streaming - Modus für v7 API ist noch nicht implementiert."}
            )
        result = await orchestrator_v7.process_query(
            user_query=request.query, user_id=request.user_id, context=request.context
        )
        return V7QueryResponse(
            answer=result.final_answer,
            confidence=result.confidence,
            scientific_process=result.scientific_process,
            execution_time_ms=result.execution_time_ms,
            metadata=result.metadata,
        )
    except Exception as e:
        logger.error(f"Fehler in v7_query_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== SYSTEM INFO ENDPOINTS =====


@app.get("/modes")
async def get_available_modes():
    """Verfügbare System-Modi"""
    return {
        "available_modes": ["VERITAS", "STREAMING", "TEST"],
        "default_mode": "VERITAS",
        "streaming_available": STREAMING_AVAILABLE,
    }


@app.get("/agents/types")
async def get_available_agent_types():
    """Verfügbare Agent-Typen"""
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
            "social",
        ],
        "system_mode": "streaming_backend",
        "streaming_features": {
            "progress_updates": STREAMING_AVAILABLE,
            "intermediate_results": STREAMING_AVAILABLE,
            "llm_thinking": STREAMING_AVAILABLE,
        },
    }


# ===== V7 CAPABILITIES ENDPOINT =====


class V7Capabilities(BaseModel):
    """v7 System Capabilities"""

    version: str
    supervisor_enabled: bool
    supervisor_available: bool
    phases: List[Dict[str, Any]]
    features: Dict[str, bool]
    uds3_available: bool
    agent_orchestrator_available: bool
    streaming_enabled: bool
    method_id: str
    config_version: str


@app.get("/api/v7/capabilities", response_model=V7Capabilities)
async def get_v7_capabilities():
    """
    v7 Capabilities Endpoint: Sendet System-Capabilities ans Frontend

    Returns:
        - version: v7.0
        - supervisor_enabled: Supervisor aktiviert (aus config)
        - supervisor_available: SupervisorAgent initialisiert
        - phases: Liste aller Phasen (ID, Name, Typ)
        - features: Dict mit allen Features (streaming, uds3, agents, etc.)
        - uds3_available: UDS3 Strategy verfügbar
        - agent_orchestrator_available: AgentOrchestrator verfügbar
        - streaming_enabled: Streaming aktiviert
        - method_id: Aktuelle Method ID (default_method)
        - config_version: Config Version (aus method config)
    """
    try:
        # Load method config
        method_config_path = Path("config/scientific_methods/default_method.json")
        if method_config_path.exists():
            with open(method_config_path, "r", encoding="utf-8") as f:
                method_config = json.load(f)
        else:
            method_config = {}

        # Extract capabilities from orchestrator_v7
        supervisor_enabled = orchestrator_v7._is_supervisor_enabled()
        supervisor_available = orchestrator_v7.supervisor_agent is not None
        uds3_available = orchestrator_v7.uds3_strategy is not None
        agent_orchestrator_available = orchestrator_v7.agent_orchestrator is not None
        streaming_enabled = orchestrator_v7.enable_streaming

        # Extract phases from method config
        phases = []
        for phase in method_config.get("phases", []):
            # Get executor type from execution.executor field
            executor = phase.get("execution", {}).get("executor", "llm")

            # Normalize executor type (agent_coordinator → agent_coordination)
            if executor == "agent_coordinator":
                executor = "agent_coordination"

            phases.append(
                {
                    "id": phase.get("phase_id"),  # Use phase_id not id
                    "name": phase.get("name"),
                    "type": executor,  # executor type: llm, supervisor, agent_coordination
                    "optional": phase.get("optional", False),
                }
            )

        # Build features dict
        features = {
            "scientific_method": True,
            "supervisor": supervisor_enabled,
            "agent_coordination": agent_orchestrator_available,
            "uds3_search": uds3_available,
            "streaming": streaming_enabled,
            "prompt_improvement": False,  # TODO: Enable when integrated
            "rag_semantic": True,
            "rag_graph": True,
            "llm_reasoning": True,
        }

        return V7Capabilities(
            version="7.0.0",
            supervisor_enabled=supervisor_enabled,
            supervisor_available=supervisor_available,
            phases=phases,
            features=features,
            uds3_available=uds3_available,
            agent_orchestrator_available=agent_orchestrator_available,
            streaming_enabled=streaming_enabled,
            method_id=orchestrator_v7.method_id,
            config_version=method_config.get("version", "unknown"),
        )

    except Exception as e:
        logger.error(f"Fehler beim Lesen der v7 Capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== APP STARTUP =====


@app.on_event("startup")
async def startup_event():
    """App-Initialisierung beim Start"""
    logger.info("🚀 Veritas API Backend (Streaming) wird gestartet...")

    # Streaming System initialisieren
    streaming_initialized = initialize_streaming_system()

    if streaming_initialized:
        logger.info("✅ Streaming Progress System erfolgreich initialisiert")
    else:
        logger.warning("⚠️ Streaming System nicht verfügbar - Legacy-Modus aktiv")

    logger.info("🎯 Veritas Streaming Backend gestartet - Port 5000")
    logger.info("📖 API-Dokumentation: http://localhost:5000/docs")
    logger.info("📡 Streaming Endpoint: /v2/query/stream")
    logger.info("📊 Progress Stream: /progress/{session_id}")


if __name__ == "__main__":
    import os

    import uvicorn

    host = os.getenv("VERITAS_API_HOST", "127.0.0.1")
    port = int(os.getenv("VERITAS_API_PORT", "5000"))
    logger.info(f"Starting Veritas streaming API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
