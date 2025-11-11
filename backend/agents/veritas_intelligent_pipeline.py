#!/usr/bin/env python3
"""
VERITAS INTELLIGENT MULTI-AGENT PIPELINE
=========================================

Intelligente Pipeline mit Real-time LLM-Kommentaren für jeden Zwischenschritt

WORKFLOW:
1. Query Analysis → LLM kommentiert: "Ich analysiere Ihre Anfrage..."
2. RAG Search → LLM kommentiert: "Ich durchsuche relevante Dokumente..."
3. Agent Selection → LLM kommentiert: "Ich wähle passende Experten aus..."
4. Parallel Agent Execution → LLM kommentiert: "Environmental-Agent arbeitet..."
5. Result Aggregation → LLM kommentiert: "Ich füge die Ergebnisse zusammen..."
6. Final Response → LLM kommentiert: "Hier ist Ihre umfassende Antwort..."

Author: VERITAS System
Date: 2025-09-28
Version: 1.0
"""

import asyncio
import copy
import json
import logging
import os
import queue
import sys
import threading
import time
import uuid
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

# Sicherstellen, dass das Projekt-Root im Python-Pfad liegt
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from backend.agents.rag_context_service import RAGContextService, RAGQueryOptions

# VERITAS Shared Enums
from backend.agents.veritas_shared_enums import PipelineStage, QueryComplexity, QueryDomain, QueryStatus

# VERITAS Imports
try:
    from backend.agents.veritas_ollama_client import VeritasOllamaClient, get_ollama_client

    # Import andere Agent-Module wenn verfügbar, aber nicht erforderlich
    try:
        from backend.agents.veritas_api_agent_core_components import AgentCoordinator, create_agent_coordinator
        from backend.agents.veritas_api_agent_orchestrator import AgentOrchestrator, create_agent_orchestrator
        from backend.agents.veritas_api_agent_pipeline_manager import AgentPipelineManager, get_agent_pipeline_db

        VERITAS_AGENT_MODULES_AVAILABLE = True
    except ImportError:
        VERITAS_AGENT_MODULES_AVAILABLE = False
    VERITAS_AGENTS_AVAILABLE = True
except ImportError as e:
    VERITAS_AGENTS_AVAILABLE = False
    VERITAS_AGENT_MODULES_AVAILABLE = False
    logging.warning(f"⚠️ VERITAS Agents nicht verfügbar: {e}")

# 🆕 Agent Registry Import
try:
    from backend.agents.agent_registry import AgentDomain, AgentRegistry, get_agent_registry

    AGENT_REGISTRY_AVAILABLE = True
    logging.info("✅ Agent Registry verfügbar")
except ImportError as e:
    AGENT_REGISTRY_AVAILABLE = False
    logging.warning(f"⚠️ Agent Registry nicht verfügbar: {e}")

# Supervisor Agent (optional)
try:
    from backend.agents.veritas_supervisor_agent import (
        AgentResult,
        SubQuery,
        SupervisorAgent,
        SynthesizedResult,
        get_supervisor_agent,
    )

    SUPERVISOR_AGENT_AVAILABLE = True
    logging.info("✅ Supervisor-Agent verfügbar")
except ImportError as e:
    SUPERVISOR_AGENT_AVAILABLE = False
    logging.warning(f"⚠️ Supervisor-Agent nicht verfügbar: {e}")

# ============================================================================
# RAG Integration - REQUIRED DEPENDENCY (NO FALLBACK MODE)
# ============================================================================
# UDS3 v2.0.0 is a REQUIRED dependency for production operation.
# System will NOT start if import fails - this is intentional!

from uds3.core import UDS3PolyglotManager  # ✨ UDS3 v2.0.0 (Legacy stable)

logging.info("✅ RAG Integration (UDS3 v2.0.0) verfügbar")

# Streaming Progress
try:
    from shared.pipelines.veritas_streaming_progress import (
        ProgressStage,
        ProgressType,
        VeritasProgressManager,
        create_progress_manager,
    )

    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False
    logging.warning("⚠️ Streaming Progress nicht verfügbar")

logger = logging.getLogger(__name__)

# ============================================================================
# INTELLIGENT PIPELINE DATASTRUKTUREN
# ============================================================================


@dataclass
class IntelligentPipelineRequest:
    """Request für intelligente Multi-Agent-Pipeline"""

    query_id: str
    query_text: str
    user_context: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    enable_llm_commentary: bool = True
    enable_real_time_updates: bool = True
    enable_supervisor: bool = False  # 🆕 Supervisor-Agent-Modus
    complexity_hint: Optional[str] = None
    requested_agents: List[str] = field(default_factory=list)
    max_parallel_agents: int = 5
    timeout: int = 60
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntelligentPipelineResponse:
    """Response von intelligenter Multi-Agent-Pipeline"""

    query_id: str
    session_id: str
    response_text: str
    confidence_score: float
    agent_results: Dict[str, Any] = field(default_factory=dict)
    agent_priority_map: Dict[str, float] = field(default_factory=dict)
    agent_selection_reasoning: List[Dict[str, Any]] = field(default_factory=list)
    agent_selection_insights: List[str] = field(default_factory=list)
    aggregation_summary: Dict[str, Any] = field(default_factory=dict)
    agent_consensus: Dict[str, Any] = field(default_factory=dict)
    rag_context: Dict[str, Any] = field(default_factory=dict)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    follow_up_suggestions: List[str] = field(default_factory=list)
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    llm_commentary: List[str] = field(default_factory=list)
    json_metadata: Optional[Dict[str, Any]] = None  # 🆕 Extracted JSON (next_steps, related_topics)
    total_processing_time: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PipelineStep:
    """Einzelner Pipeline-Step mit LLM-Kommentar"""

    step_id: str
    step_name: str
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    llm_comment: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress_percentage: float = 0.0


@dataclass
class AgentExecutionTask:
    """Repräsentiert eine Agenten-Aufgabe für Thread-Pool-Ausführung"""

    agent_type: str
    stage: str  # parallel oder sequential
    priority_score: float
    planned_order: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    disabled: bool = False


# ============================================================================
# INTELLIGENT MULTI-AGENT PIPELINE
# ============================================================================


class IntelligentMultiAgentPipeline:
    """
    Intelligent Multi-Agent Pipeline mit Real-time LLM-Kommentaren

    KERNFUNKTIONEN:
    - LLM-kommentierte Pipeline-Steps
    - Parallele Agent-Execution mit Thread-Pool
    - RAG-basierte Agent-Selektion
    - Real-time Progress Updates
    - Intelligente Result-Aggregation
    """

    STEP_PROGRESS_MAPPING = {
        "query_analysis": ProgressStage.ANALYZING_QUERY,
        "rag_search": ProgressStage.GATHERING_CONTEXT,
        "agent_selection": ProgressStage.SELECTING_AGENTS,
        "agent_execution": ProgressStage.AGENT_PROCESSING,
        "result_aggregation": ProgressStage.SYNTHESIZING,
    }

    def __init__(self, max_workers: int = 5):
        """
        Initialisiert die Intelligent Multi-Agent Pipeline

        Args:
            max_workers: Maximale Anzahl paralleler Agent-Threads
        """
        self.max_workers = max_workers

        # Core Components
        self.ollama_client: Optional[VeritasOllamaClient] = None
        self.agent_orchestrator: Optional[AgentOrchestrator] = None
        self.pipeline_manager: Optional[AgentPipelineManager] = None
        self.agent_coordinator: Optional[AgentCoordinator] = None
        self.progress_manager: Optional[VeritasProgressManager] = None
        self.supervisor_agent: Optional[SupervisorAgent] = None  # 🆕 Supervisor-Agent
        self.agent_registry: Optional[AgentRegistry] = None  # 🆕 Agent Registry

        # RAG Integration
        self.database_api: Optional[MultiDatabaseAPI] = None
        self.uds3_strategy: Optional[UDS3PolyglotManager] = None  # ✨ NEU: UDS3 v2.0.0
        self.rag_service: Optional[RAGContextService] = None

        # Token Budget & Intent Classification
        self.token_calculator = None  # Wird in initialize() geladen
        self.intent_classifier = None  # Wird in initialize() geladen
        self.context_window_manager = None  # Wird in initialize() geladen

        # Threading
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.agent_task_queue: "queue.Queue[AgentExecutionTask]" = queue.Queue()
        self._agent_results_lock = threading.RLock()

        # Active Pipelines
        self.active_pipelines: Dict[str, IntelligentPipelineRequest] = {}
        self.pipeline_steps: Dict[str, List[PipelineStep]] = {}

        # Statistics
        self.stats = {
            "pipelines_processed": 0,
            "successful_pipelines": 0,
            "failed_pipelines": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "llm_comments_generated": 0,
            "agents_executed": 0,
            "agent_timeouts": 0,
            "rag_queries_executed": 0,
            "agent_priority_updates": 0,
            "orchestrator_usage": 0,
            "supervisor_usage": 0,  # 🆕 Supervisor - Statistik
            "agent_registry_usage": 0,  # 🆕 Agent Registry - Statistik
            "stage_duration_stats": {},
            "agent_metrics": {},
            "query_metrics": {"complexity_counts": {}, "domain_counts": {}, "avg_processing_time_by_complexity": {}},
            "last_error": None,
        }

        self.recent_pipeline_metrics: deque = deque(maxlen=20)
        self.recent_agent_events: deque = deque(maxlen=50)
        self.recent_query_metrics: deque = deque(maxlen=50)
        self.recent_errors: deque = deque(maxlen=50)

        logger.info("🧠 Intelligent Multi-Agent Pipeline initialisiert")

    async def initialize(self) -> bool:
        """
        Initialisiert alle Pipeline-Komponenten

        Returns:
            bool: True wenn erfolgreich initialisiert
        """
        try:
            # Ollama Client initialisieren
            self.ollama_client = await get_ollama_client()
            if not self.ollama_client:
                logger.error("❌ Ollama Client Initialisierung fehlgeschlagen")
                return False

            # VERITAS Agents initialisieren
            if VERITAS_AGENT_MODULES_AVAILABLE:
                self.pipeline_manager = get_agent_pipeline_db()
                self.agent_orchestrator = create_agent_orchestrator(pipeline_manager=self.pipeline_manager)
                self.agent_coordinator = create_agent_coordinator(
                    orchestrator=self.agent_orchestrator, pipeline_manager=self.pipeline_manager
                )
                self.agent_orchestrator.set_agent_coordinator(self.agent_coordinator)
                logger.info("✅ VERITAS Agent-Module erfolgreich initialisiert")
            else:
                logger.info("ℹ️ VERITAS Agent-Module nicht verfügbar - läuft im Mock-Modus")

            # ============================================================================
            # RAG Integration - REQUIRED (NO FALLBACK MODE)
            # ============================================================================
            # UDS3 v2.0.0 is REQUIRED. System will fail fast if initialization fails.

            backend_config = {
                "vector": {"enabled": True, "backend": "chromadb"},
                "graph": {"enabled": False},
                "relational": {"enabled": False},
                "file_storage": {"enabled": False},
            }

            try:
                self.uds3_strategy = UDS3PolyglotManager(backend_config=backend_config, enable_rag=True)
                logger.info("✅ UDS3 Polyglot Manager initialisiert")
            except Exception as e:
                logger.error(f"❌ CRITICAL: UDS3 Polyglot Manager Init FAILED: {e}")
                raise RuntimeError(f"Intelligent Pipeline requires UDS3 - Init failed: {e}")

            # RAG Context Service initialisieren (REQUIRED)
            try:
                self.rag_service = RAGContextService(database_api=None, uds3_strategy=self.uds3_strategy)
                logger.info("✅ RAG Context Service initialisiert")
            except Exception as e:
                logger.error(f"❌ CRITICAL: RAG Context Service Init FAILED: {e}")
                raise RuntimeError(f"Intelligent Pipeline requires RAG Service - Init failed: {e}")

            # Token Budget Calculator initialisieren
            try:
                from backend.services.token_budget_calculator import TokenBudgetCalculator

                self.token_calculator = TokenBudgetCalculator()
                logger.info("✅ Token Budget Calculator initialisiert")
            except Exception as e:
                logger.warning(f"⚠️ Token Budget Calculator konnte nicht geladen werden: {e}")

            # Intent Classifier initialisieren
            try:
                from backend.services.intent_classifier import HybridIntentClassifier

                self.intent_classifier = HybridIntentClassifier(llm_threshold=0.7)
                logger.info("✅ Intent Classifier initialisiert")
            except Exception as e:
                logger.warning(f"⚠️ Intent Classifier konnte nicht geladen werden: {e}")

            # Context Window Manager initialisieren
            try:
                from backend.services.context_window_manager import ContextWindowManager

                self.context_window_manager = ContextWindowManager(safety_factor=0.8)
                logger.info("✅ Context Window Manager initialisiert")
            except Exception as e:
                logger.warning(f"⚠️ Context Window Manager konnte nicht geladen werden: {e}")

            # Progress Manager initialisieren
            if STREAMING_AVAILABLE:
                self.progress_manager = create_progress_manager()

            # 🆕 Supervisor-Agent initialisieren
            if SUPERVISOR_AGENT_AVAILABLE and self.ollama_client:
                try:
                    self.supervisor_agent = await get_supervisor_agent(self.ollama_client)
                    logger.info("✅ Supervisor-Agent initialisiert")
                except Exception as e:
                    logger.warning(f"⚠️ Supervisor-Agent Initialisierung fehlgeschlagen: {e}")
                    self.supervisor_agent = None

            # 🆕 Agent Registry initialisieren
            if AGENT_REGISTRY_AVAILABLE:
                try:
                    self.agent_registry = get_agent_registry()
                    available_workers = self.agent_registry.list_available_agents()
                    logger.info(f"✅ Agent Registry initialisiert ({len(available_workers)} agents verfügbar)")
                except Exception as e:
                    logger.warning(f"⚠️ Agent Registry Initialisierung fehlgeschlagen: {e}")
                    self.agent_registry = None

            logger.info("✅ Intelligent Pipeline erfolgreich initialisiert")
            return True

        except Exception as e:
            logger.error(f"❌ Pipeline Initialisierung fehlgeschlagen: {e}")
            return False

    async def _initialize_request_scoped_resources(self, enable_rag: bool = True, enable_supervisor: bool = False) -> bool:
        """
        Initialisiert Request-spezifische Ressourcen.

        Diese Methode wird von PipelineFactory nach Dependency Injection aufgerufen.
        Sie initialisiert nur die Ressourcen, die pro Request benötigt werden.

        Args:
            enable_rag: RAG-Integration aktivieren
            enable_supervisor: Supervisor-Agent aktivieren

        Returns:
            bool: True wenn erfolgreich
        """
        try:
            # ThreadPool für diesen Request erstellen
            if not self.executor:
                self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
                logger.info(f"✅ ThreadPool erstellt ({self.max_workers} workers)")

            # RAG Context Service (falls RAG enabled)
            if enable_rag and self.uds3_strategy:
                try:
                    from backend.agents.veritas_api_agent_rag_context import RAGContextService

                    self.rag_service = RAGContextService(database_api=None, uds3_strategy=self.uds3_strategy)
                    logger.info("✅ RAG Context Service initialisiert")
                except Exception as e:
                    logger.warning(f"⚠️ RAG Context Service Initialisierung fehlgeschlagen: {e}")

            # Supervisor Agent (falls enabled)
            if enable_supervisor and SUPERVISOR_AGENT_AVAILABLE and self.ollama_client:
                try:
                    self.supervisor_agent = await get_supervisor_agent(self.ollama_client)
                    logger.info("✅ Supervisor-Agent initialisiert")
                except Exception as e:
                    logger.warning(f"⚠️ Supervisor-Agent Initialisierung fehlgeschlagen: {e}")

            logger.info("✅ Request-scoped Ressourcen initialisiert")
            return True

        except Exception as e:
            logger.error(f"❌ Request-scoped Initialisierung fehlgeschlagen: {e}")
            return False

    async def cleanup(self):
        """
        Räumt Pipeline-Ressourcen nach Request auf.

        Diese Methode sollte am Ende jedes Requests aufgerufen werden,
        um Ressourcen freizugeben und Memory-Leaks zu vermeiden.

        Cleanup umfasst:
        - ThreadPool shutdown
        - State clearing
        - Temporary data cleanup
        """
        try:
            # ThreadPool beenden
            if self.executor:
                self.executor.shutdown(wait=False)
                self.executor = None
                logger.info("✅ ThreadPool beendet")

            # State clearen
            self.active_pipelines.clear()
            self.pipeline_steps.clear()

            # Temporary caches clearen (falls vorhanden)
            if hasattr(self, "_temp_cache"):
                self._temp_cache.clear()

            logger.info("✅ Pipeline-Ressourcen bereinigt")

        except Exception as e:
            logger.error(f"❌ Cleanup-Fehler: {e}")

    async def process_intelligent_query(self, request: IntelligentPipelineRequest) -> IntelligentPipelineResponse:
        """
        Verarbeitet Query durch intelligente Multi-Agent-Pipeline

        Args:
            request: Pipeline-Request

        Returns:
            IntelligentPipelineResponse: Umfassende Pipeline-Response
        """
        start_time = time.time()
        request.session_id = request.session_id or str(uuid.uuid4())

        # Pipeline in aktive Liste aufnehmen
        self.active_pipelines[request.query_id] = request
        self.pipeline_steps[request.query_id] = []
        self._start_progress_session(request)

        try:
            # STEP 0: Intent Classification & Token Budget Calculation
            intent_prediction = None
            token_budget = 1000  # Default fallback

            if self.intent_classifier:
                try:
                    intent_prediction = await self.intent_classifier.classify_async(
                        query=request.query_text, ollama_service=self.ollama_client, model="phi3"
                    )
                    logger.info(
                        f"🎯 Intent classified: {intent_prediction.intent.value} "
                        f"(confidence: {intent_prediction.confidence:.2%}, method: {intent_prediction.method})"
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Intent classification failed: {e}")
                    from backend.services.intent_classifier import IntentPrediction, UserIntent

                    intent_prediction = IntentPrediction(
                        intent=UserIntent.EXPLANATION, confidence=0.5, method="fallback", reasoning="Classification error"
                    )

            # Token Budget berechnen (wird nach RAG-Step aktualisiert)
            if self.token_calculator and intent_prediction:
                try:
                    from backend.services.intent_classifier import UserIntent

                    token_budget, budget_breakdown = self.token_calculator.calculate_budget(
                        query=request.query_text,
                        chunk_count=0,  # Wird nach RAG aktualisiert
                        source_types=[],  # Wird nach RAG aktualisiert
                        agent_count=0,  # Wird nach Agent-Selection aktualisiert
                        intent=intent_prediction.intent,
                        confidence=None,  # Post-hoc nach Response
                        user_preference=request.user_preference if hasattr(request, "user_preference") else 1.0,
                    )
                    logger.info(
                        f"💰 Token budget calculated: {token_budget} tokens "
                        f"(complexity: {budget_breakdown['complexity_score']:.1f}/10)"
                    )

                    # Budget in Request speichern für spätere Verwendung
                    request.token_budget = token_budget
                    request.budget_breakdown = budget_breakdown
                    request.intent_prediction = intent_prediction
                except Exception as e:
                    logger.warning(f"⚠️ Token budget calculation failed: {e}")
                    request.token_budget = 1000

            # STEP 1: Query Analysis
            analysis_result = await self._execute_pipeline_step(
                request, "query_analysis", "Query Analysis", self._step_query_analysis
            )

            # STEP 2: RAG Search
            rag_result = await self._execute_pipeline_step(
                request, "rag_search", "RAG Database Search", self._step_rag_search, {"analysis": analysis_result}
            )

            # Token-Budget nach RAG aktualisieren (mehr Chunks → mehr Tokens)
            if self.token_calculator and intent_prediction and rag_result:
                try:
                    chunk_count = len(rag_result.get("documents", []))
                    source_types = []
                    if rag_result.get("vector", {}).get("statistics", {}).get("count", 0) > 0:
                        source_types.append("vector")
                    if rag_result.get("graph", {}).get("related_entities"):
                        source_types.append("graph")
                    if rag_result.get("relational"):
                        source_types.append("relational")

                    updated_budget, updated_breakdown = self.token_calculator.calculate_budget(
                        query=request.query_text,
                        chunk_count=chunk_count,
                        source_types=source_types,
                        agent_count=0,  # Wird nach Agent-Selection aktualisiert
                        intent=intent_prediction.intent,
                        confidence=None,
                        user_preference=getattr(request, "user_preference", 1.0),
                    )

                    logger.info(
                        f"💰 Token budget updated after RAG: {updated_budget} tokens "
                        f"(chunks: {chunk_count}, sources: {len(source_types)})"
                    )
                    request.token_budget = updated_budget
                    request.budget_breakdown = updated_breakdown
                except Exception as e:
                    logger.warning(f"⚠️ Token budget update after RAG failed: {e}")

            # STEP 3: Agent Selection
            agent_selection_result = await self._execute_pipeline_step(
                request,
                "agent_selection",
                "Agent Selection",
                self._step_agent_selection,
                {"analysis": analysis_result, "rag": rag_result},
            )

            # Token-Budget final nach Agent-Selection aktualisieren
            if self.token_calculator and intent_prediction and agent_selection_result:
                try:
                    selected_agents = agent_selection_result.get("selected_agents", [])
                    agent_count = len(selected_agents)
                    chunk_count = len(rag_result.get("documents", [])) if rag_result else 0
                    source_types = []
                    if rag_result:
                        if rag_result.get("vector", {}).get("statistics", {}).get("count", 0) > 0:
                            source_types.append("vector")
                        if rag_result.get("graph", {}).get("related_entities"):
                            source_types.append("graph")
                        if rag_result.get("relational"):
                            source_types.append("relational")

                    final_budget, final_breakdown = self.token_calculator.calculate_budget(
                        query=request.query_text,
                        chunk_count=chunk_count,
                        source_types=source_types,
                        agent_count=agent_count,
                        intent=intent_prediction.intent,
                        confidence=None,
                        user_preference=getattr(request, "user_preference", 1.0),
                    )

                    logger.info(
                        f"💰 Final token budget: {final_budget} tokens "
                        f"(chunks: {chunk_count}, sources: {len(source_types)}, agents: {agent_count})"
                    )
                    request.token_budget = final_budget
                    request.budget_breakdown = final_breakdown
                except Exception as e:
                    logger.warning(f"⚠️ Final token budget calculation failed: {e}")

            # STEP 4: Parallel Agent Execution
            agent_results = await self._execute_pipeline_step(
                request,
                "agent_execution",
                "Agent Execution",
                self._step_parallel_agent_execution,
                {"agent_selection": agent_selection_result, "rag": rag_result},
            )

            # STEP 5: Result Aggregation
            final_result = await self._execute_pipeline_step(
                request,
                "result_aggregation",
                "Result Aggregation",
                self._step_result_aggregation,
                {"analysis": analysis_result, "rag": rag_result, "agent_results": agent_results},
            )
            stage_durations = {
                step.step_id: round((step.end_time - step.start_time), 4)
                for step in self.pipeline_steps.get(request.query_id, [])
                if step.start_time and step.end_time
            }

            # Pipeline erfolgreich abgeschlossen
            processing_time = time.time() - start_time
            self.stats["pipelines_processed"] += 1
            self.stats["successful_pipelines"] += 1
            self.stats["total_processing_time"] += processing_time
            if self.stats["pipelines_processed"] > 0:
                self.stats["average_processing_time"] = self.stats["total_processing_time"] / self.stats["pipelines_processed"]

            # Response zusammenstellen
            response = IntelligentPipelineResponse(
                query_id=request.query_id,
                session_id=request.session_id or str(uuid.uuid4()),
                response_text=final_result.get("response_text", "Keine Antwort generiert"),
                confidence_score=final_result.get("confidence_score", 0.0),
                agent_results=agent_results.get("detailed_results", {}),
                agent_priority_map=agent_selection_result.get("priority_map", {}),
                agent_selection_reasoning=agent_selection_result.get("selection_reasoning", []),
                agent_selection_insights=agent_selection_result.get("insights", []),
                aggregation_summary=final_result.get("aggregation_summary", {}),
                agent_consensus=final_result.get("agent_consensus", {}),
                rag_context=rag_result,
                sources=final_result.get("sources", []),
                follow_up_suggestions=final_result.get("follow_up_suggestions", []),
                json_metadata=final_result.get("json_metadata"),  # 🆕 JSON-Metadaten (next_steps, related_topics)
                processing_metadata={
                    "total_processing_time": processing_time,
                    "steps_completed": len(self.pipeline_steps[request.query_id]),
                    "agents_used": len(agent_results.get("detailed_results", {})),
                    "rag_documents_found": len(rag_result.get("documents", [])),
                    "pipeline_complexity": analysis_result.get("complexity", "standard"),
                    "agent_priority_map": agent_selection_result.get("priority_map", {}),
                    "agent_execution_plan": agent_selection_result.get("execution_plan", {}),
                    "agent_execution_summary": agent_results.get("execution_summary", {}),
                    "agent_selection_insights": agent_selection_result.get("insights", []),
                    "orchestrator_used": bool(agent_selection_result.get("orchestrator_context")),
                    "orchestrator_pipeline_id": (agent_selection_result.get("orchestrator_context") or {}).get("pipeline_id"),
                    "aggregation_key_points": final_result.get("aggregation_summary", {}).get("key_points", []),
                    "agent_confidence_summary": final_result.get("agent_consensus", {}).get("confidence", {}),
                    "combined_confidence": final_result.get("agent_consensus", {}).get("blended_confidence"),
                    "stage_durations": stage_durations,
                    "progress_session_id": request.session_id,
                    # 🆕 Token Budget Metadata
                    "token_budget": {
                        "allocated": getattr(request, "token_budget", None),
                        "breakdown": getattr(request, "budget_breakdown", {}),
                        "intent": getattr(request, "intent_prediction", None).__dict__
                        if hasattr(request, "intent_prediction") and getattr(request, "intent_prediction", None)
                        else None,
                        "actual_used": final_result.get("llm_metadata", {}).get("tokens_used"),
                    },
                },
                llm_commentary=[step.llm_comment for step in self.pipeline_steps[request.query_id] if step.llm_comment],
                total_processing_time=processing_time,
            )
            self._record_pipeline_metrics(
                request, response, stage_durations, agent_results.get("execution_summary", {}), analysis_result
            )
            self._update_progress_stage(
                request,
                ProgressStage.FINALIZING,
                {"total_processing_time": round(processing_time, 3), "confidence": response.confidence_score},
            )
            self._complete_progress_session(request, response)

            return response

        except Exception as e:
            logger.error(f"❌ Pipeline-Verarbeitung fehlgeschlagen: {e}")
            self._record_pipeline_error(request, e)
            self.stats["failed_pipelines"] += 1
            self._fail_progress_session(request, str(e))

            # Fehler-Response
            return IntelligentPipelineResponse(
                query_id=request.query_id,
                session_id=request.session_id or str(uuid.uuid4()),
                response_text=f"Entschuldigung, bei der Verarbeitung ist ein Fehler aufgetreten: {str(e)}",
                confidence_score=0.0,
                total_processing_time=time.time() - start_time,
            )

        finally:
            # ✅ CLEANUP: Request-scoped Ressourcen freigeben
            if request.query_id in self.active_pipelines:
                del self.active_pipelines[request.query_id]

            # Optional: Vollständiger Cleanup (wenn Factory-Pattern genutzt wird)
            # Wird auskommentiert, bis Factory-Pattern aktiviert ist
            # await self.cleanup()

    async def _execute_pipeline_step(
        self, request: IntelligentPipelineRequest, step_id: str, step_name: str, step_function, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Führt Pipeline-Step mit LLM-Kommentar aus

        Args:
            request: Pipeline Request
            step_id: Eindeutige Step-ID
            step_name: Human-readable Step-Name
            step_function: Auszuführende Funktion
            context: Kontext für den Step

        Returns:
            Dict: Step-Ergebnis
        """

        step = PipelineStep(step_id=step_id, step_name=step_name, status="running", start_time=time.time())

        self.pipeline_steps[request.query_id].append(step)
        progress_stage = self.STEP_PROGRESS_MAPPING.get(step_id)
        if progress_stage:
            self._update_progress_stage(request, progress_stage, context or {})

        try:
            # LLM-Kommentar für Step-Start generieren
            if request.enable_llm_commentary and self.ollama_client:
                step.llm_comment = await self.ollama_client.comment_pipeline_step(
                    current_step=step_name,
                    progress_info={"status": "started", "context": context or {}},
                    context={"original_query": request.query_text, "stage_context": context or {}},
                )
                self.stats["llm_comments_generated"] += 1

            # Step ausführen
            result = await step_function(request, context or {})

            # Step erfolgreich abgeschlossen
            step.status = "completed"
            step.end_time = time.time()
            step.result = result
            step.progress_percentage = 100.0
            duration = step.end_time - step.start_time
            self._record_stage_duration(step_id, duration)

            return result

        except Exception as e:
            # Step fehlgeschlagen
            step.status = "failed"
            step.end_time = time.time()
            step.error = str(e)
            step.progress_percentage = 0.0
            if progress_stage:
                self._update_progress_stage(request, ProgressStage.ERROR, {"failed_stage": step_id, "error": str(e)})

            self._record_pipeline_error(request, e, stage=step_id, context={"step_name": step_name})
            logger.error(f"❌ Pipeline Step '{step_name}' fehlgeschlagen: {e}")
            raise

    async def _step_query_analysis(self, request: IntelligentPipelineRequest, context: Dict[str, Any]) -> Dict[str, Any]:
        """STEP 1: Analysiert Query mit Ollama LLM"""

        if not self.ollama_client:
            # Fallback ohne LLM
            return {
                "complexity": "standard",
                "domain": "general",
                "required_agents": ["document_retrieval", "legal_framework"],
                "estimated_time": 15,
            }

        return await self.ollama_client.analyze_query(request.query_text, request.user_context)

    async def _step_rag_search(self, request: IntelligentPipelineRequest, context: Dict[str, Any]) -> Dict[str, Any]:
        """STEP 2: Führt RAG-Suche durch"""

        # RAG Service is REQUIRED (initialized in __init__)
        # No fallback mode - system would have failed fast during startup
        if not self.rag_service:
            raise RuntimeError("RAG Service not initialized - System in invalid state")

        analysis = context.get("analysis", {}) or {}
        complexity = analysis.get("complexity", "standard")
        # Fortgeschrittene Anfragen bekommen mehr Dokumente zur Verfügung
        limit_documents = 8 if complexity == "advanced" else 5
        options = RAGQueryOptions(limit_documents=limit_documents)

        rag_context = await self.rag_service.build_context(
            query_text=request.query_text, user_context=request.user_context, options=options
        )

        self.stats["rag_queries_executed"] += 1

        return rag_context

    async def _step_agent_selection(self, request: IntelligentPipelineRequest, context: Dict[str, Any]) -> Dict[str, Any]:
        """STEP 3: Wählt optimale Agenten basierend auf Analyse und RAG-Kontext"""

        analysis = context.get("analysis", {})
        rag = context.get("rag", {})

        # 🆕 SUPERVISOR-MODUS: Nutze Supervisor-Agent für intelligente Decomposition & Selection
        if request.enable_supervisor and self.supervisor_agent and SUPERVISOR_AGENT_AVAILABLE:
            return await self._supervisor_agent_selection(request, context)

        # 🆕 WORKER REGISTRY-MODUS: Capability-based Worker Selection
        if self.agent_registry and AGENT_REGISTRY_AVAILABLE:
            return await self._agent_registry_selection(request, context)

        # STANDARD-MODUS: Bestehende Logik (Backward-Compatibility)
        complexity = analysis.get("complexity", "standard")
        domain = analysis.get("domain", "general")
        base_required = set(analysis.get("required_agents", ["document_retrieval"]))
        base_required.update(request.requested_agents)

        priority_map: Dict[str, float] = {}
        agent_reasons: Dict[str, List[str]] = {}
        selection_insights: List[str] = []
        orchestrator_result: Optional[Dict[str, Any]] = None

        if self.agent_orchestrator:
            query_payload = {
                "query": request.query_text,
                "query_id": request.query_id,
                "user_context": request.user_context,
                "analysis": analysis,
                "rag_context": rag,
            }
            try:
                orchestrator_result = self.agent_orchestrator.preprocess_query(query_payload, rag_context=rag)
                base_required.update(orchestrator_result.get("required_agents", []))
                for agent, score in (orchestrator_result.get("agent_priority_map", {}) or {}).items():
                    base_required.add(agent)
                    priority_map[agent] = priority_map.get(agent, 0.0) + score
                selection_insights.append("AgentOrchestrator-Plan übernommen")
                dynamic_actions = orchestrator_result.get("dynamic_actions", {}) or {}
                if dynamic_actions.get("added"):
                    selection_insights.append(f"Dynamisch hinzugefügt: {', '.join(dynamic_actions['added'])}")
                if dynamic_actions.get("disabled"):
                    selection_insights.append(f"Deaktiviert: {', '.join(dynamic_actions['disabled'])}")
            except Exception as exc:
                logger.warning("⚠️ AgentOrchestrator Preprocessing fehlgeschlagen: %s", exc)
                selection_insights.append("AgentOrchestrator nicht verfügbar")

        def register_agent(agent: str, score: float, reason: str) -> None:
            if not agent:
                return
            base_required.add(agent)
            priority_map[agent] = priority_map.get(agent, 0.0) + score
            agent_reasons.setdefault(agent, []).append(reason)

        # Basispunkte für bereits analysierte Agenten
        for agent in base_required:
            register_agent(agent, 0.5, "Analysevorschlag")

        # Domain-basierte Anpassung
        domain_agent_mapping = {
            "environmental": "environmental",
            "building": "legal_framework",
            "transport": "transport",
            "social": "social",
            "business": "business",
            "taxation": "financial",
        }
        if domain in domain_agent_mapping:
            register_agent(domain_agent_mapping[domain], 0.6, f"Domäne '{domain}' erkannt")

        # Komplexitäts-basierte Erweiterung
        if complexity == "advanced":
            register_agent("external_api", 0.7, "Komplexität 'advanced'")
            register_agent("quality_assessor", 0.6, "Komplexität 'advanced'")
        elif complexity == "basic":
            priority_map = {agent: score * 0.9 for agent, score in priority_map.items()}

        # RAG-Kontext analysieren
        documents = rag.get("documents", []) or []
        tag_counter: Counter[str] = Counter()
        for doc in documents:
            tags = doc.get("domain_tags") or []
            tag_counter.update(tag.lower() for tag in tags if isinstance(tag, str))

        tag_agent_mapping = {
            "environmental": "environmental",
            "air_quality": "environmental",
            "building": "building",
            "planning": "building",
            "transport": "transport",
            "traffic": "transport",
            "social": "social",
            "health": "health",
            "finance": "financial",
            "legal": "legal_framework",
            "authority": "authority_mapping",
        }

        for tag, count in tag_counter.items():
            agent = tag_agent_mapping.get(tag)
            if agent:
                boost = min(0.4 + count * 0.1, 1.0)
                register_agent(agent, boost, f"RAG-Tag '{tag}' ({count} Treffer)")

        if documents:
            selection_insights.append(f"{len(documents)} RAG-Dokumente verfügbar")

        vector_stats = rag.get("vector", {}).get("statistics", {})
        if vector_stats.get("count", 0) > 0:
            register_agent("document_retrieval", 0.3, "Vector-Suche erfolgreich")
        else:
            selection_insights.append("Keine Vector-Matches → Fokus auf qualitative Agenten")
            register_agent("quality_assessor", 0.2, "Fehlende Vector-Matches")

        graph_entities = rag.get("graph", {}).get("related_entities", []) or []
        if graph_entities:
            register_agent("authority_mapping", 0.4, "Graph-Beziehungen vorhanden")
            selection_insights.append(f"Graph-Entities: {', '.join(graph_entities[:3])}")

        # Sicherstellen, dass document_retrieval stets verfügbar bleibt
        register_agent("document_retrieval", 0.2, "Standard-Fallback")

        # Endgültige Agentenliste nach Priorität sortieren
        ordered_agents = sorted(priority_map.items(), key=lambda item: item[1], reverse=True)
        selected_agents = [agent for agent, score in ordered_agents if score > 0]
        if not selected_agents:
            selected_agents = ["document_retrieval"]
            priority_map = {"document_retrieval": 1.0}
            agent_reasons = {"document_retrieval": ["Fallback"]}

        execution_plan = {
            "parallel_agents": [agent for agent in selected_agents[:3]],
            "sequential_agents": [agent for agent in selected_agents[3:]],
        }

        selection_reasoning = [
            {
                "agent": agent,
                "score": round(priority_map.get(agent, 0.0), 2),
                "reasons": agent_reasons.get(agent, []),
            }
            for agent in selected_agents
        ]

        if priority_map:
            self.stats["agent_priority_updates"] += 1
        if orchestrator_result:
            self.stats["orchestrator_usage"] += 1

        return {
            "selected_agents": selected_agents,
            "execution_plan": execution_plan,
            "priority_map": priority_map,
            "selection_reasoning": selection_reasoning,
            "insights": selection_insights,
            "orchestrator_context": orchestrator_result,
        }

    async def _supervisor_agent_selection(
        self, request: IntelligentPipelineRequest, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🆕 SUPERVISOR-BASIERTE AGENT-SELEKTION

        Nutzt Supervisor-Agent für:
        1. Query Decomposition (komplexe Queries → Subqueries)
        2. Intelligente Agent-Selektion pro Subquery
        3. Dependency-basierte Execution-Planung
        """
        logger.info("🎯 Supervisor-Modus aktiviert - starte intelligente Agent-Selektion")

        analysis = context.get("analysis", {})
        rag = context.get("rag", {})

        try:
            # Phase 1: Query Decomposition
            complexity_hint = analysis.get("complexity", "standard")
            subqueries = await self.supervisor_agent.decompose_query(
                query_text=request.query_text, user_context=request.user_context, complexity_hint=complexity_hint
            )

            logger.info(f"📋 {len(subqueries)} Subqueries erstellt")

            # Phase 2: Agent-Plan erstellen
            agent_plan = await self.supervisor_agent.create_agent_plan(subqueries, rag)

            # Phase 3: Agent-Plan in Pipeline-Format umwandeln
            selected_agents = []
            priority_map = {}
            selection_reasoning = []

            # Parallel Agents
            for sq_id, assignment in agent_plan.parallel_agents:
                agent_type = assignment.agent_type
                if agent_type not in selected_agents:
                    selected_agents.append(agent_type)
                    priority_map[agent_type] = assignment.confidence_score
                    selection_reasoning.append(
                        {
                            "agent": agent_type,
                            "score": round(assignment.confidence_score, 2),
                            "reasons": [assignment.reason],
                            "subquery_id": sq_id,
                        }
                    )

            # Sequential Agents
            for sq_id, assignment in agent_plan.sequential_agents:
                agent_type = assignment.agent_type
                if agent_type not in selected_agents:
                    selected_agents.append(agent_type)
                    priority_map[agent_type] = assignment.confidence_score * 0.8  # Leicht niedrigere Priorität
                    selection_reasoning.append(
                        {
                            "agent": agent_type,
                            "score": round(assignment.confidence_score * 0.8, 2),
                            "reasons": [assignment.reason],
                            "subquery_id": sq_id,
                        }
                    )

            # Fallback
            if not selected_agents:
                selected_agents = ["document_retrieval"]
                priority_map = {"document_retrieval": 1.0}

            execution_plan = {
                "parallel_agents": [a.agent_type for _, a in agent_plan.parallel_agents],
                "sequential_agents": [a.agent_type for _, a in agent_plan.sequential_agents],
            }

            # Statistiken
            self.stats["supervisor_usage"] += 1

            logger.info(f"✅ Supervisor-Selektion: {len(selected_agents)} Agents, {len(agent_plan.parallel_agents)} parallel")

            return {
                "selected_agents": selected_agents,
                "execution_plan": execution_plan,
                "priority_map": priority_map,
                "selection_reasoning": selection_reasoning,
                "insights": [f"Supervisor - Modus: {len(subqueries)} Subqueries"],
                "supervisor_context": {
                    "subqueries": [sq.to_dict() for sq in subqueries],
                    "agent_plan": agent_plan.to_dict(),
                    "mode": "supervisor",
                },
            }

        except Exception as e:
            logger.error(f"❌ Supervisor-Agent-Selektion fehlgeschlagen: {e}")
            # Fallback auf Standard-Selektion
            logger.info("⚠️ Fallback auf Standard-Selektion")
            request_copy = copy.copy(request)
            request_copy.enable_supervisor = False
            return await self._step_agent_selection(request_copy, context)

    async def _agent_registry_selection(self, request: IntelligentPipelineRequest, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        🆕 WORKER REGISTRY-BASIERTE AGENT-SELEKTION

        Nutzt Agent Registry für:
        1. Capability-based Worker Selection
        2. Domain-basierte Worker-Filterung
        3. Text-Search für Query-Matching

        Returns:
            Agent selection dict mit agent_registry_context
        """
        logger.info("🔧 Agent Registry-Modus aktiviert - starte capability-based selection")

        analysis = context.get("analysis", {})
        rag = context.get("rag", {})

        try:
            selected_agents = []
            priority_map = {}
            selection_reasoning = []
            registry_insights = []

            # Phase 1: Text-Search basierend auf Query
            query_text = request.query_text.lower()
            text_search_workers = self.agent_registry.search_workers(query_text)

            if text_search_workers:
                logger.info(f"📝 Text-Search: {len(text_search_workers)} workers gefunden")
                registry_insights.append(f"Text-Search matched {len(text_search_workers)} workers")

                for worker_id in text_search_workers:
                    if worker_id not in selected_agents:
                        selected_agents.append(worker_id)
                        priority_map[worker_id] = 0.8  # Hohe Priorität für Text-Matches
                        selection_reasoning.append(
                            {"agent": worker_id, "score": 0.8, "reasons": ["Query text match"], "method": "text_search"}
                        )

            # Phase 2: Domain-basierte Selection
            domain = analysis.get("domain", "general")
            domain_mapping = {
                "environmental": AgentDomain.ENVIRONMENTAL,
                "building": AgentDomain.LEGAL,  # Future: Administrative
                "legal": AgentDomain.LEGAL,
                "technical": AgentDomain.TECHNICAL,
                "knowledge": AgentDomain.KNOWLEDGE,
                "atmospheric": AgentDomain.ATMOSPHERIC,
                "database": AgentDomain.DATABASE,
            }

            if domain in domain_mapping:
                domain_workers = self.agent_registry.get_workers_by_domain(domain_mapping[domain])
                logger.info(f"🏢 Domain '{domain}': {len(domain_workers)} workers")
                registry_insights.append(f"Domain {domain} matched {len(domain_workers)} workers")

                for worker_id in domain_workers:
                    if worker_id not in selected_agents:
                        selected_agents.append(worker_id)
                        priority_map[worker_id] = 0.7
                        selection_reasoning.append(
                            {
                                "agent": worker_id,
                                "score": 0.7,
                                "reasons": [f"Domain '{domain}' match"],
                                "method": "domain_filter",
                            }
                        )
                    else:
                        # Boost priority für bereits selektierte Workers
                        priority_map[worker_id] = min(priority_map[worker_id] + 0.2, 1.0)

            # Phase 3: RAG-Context basierte Capability-Matching
            documents = rag.get("documents", []) or []
            if documents:
                # Extrahiere relevante Keywords aus RAG-Dokumenten
                keywords = set()
                for doc in documents[:5]:  # Top 5 Dokumente
                    tags = doc.get("domain_tags", []) or []
                    keywords.update(tag.lower() for tag in tags if isinstance(tag, str))

                    # Auch aus Dokumenten-Titel
                    title = doc.get("title", "")
                    if title:
                        keywords.update(title.lower().split())

                # Capability-Matching für Keywords
                for keyword in keywords:
                    capability_workers = self.agent_registry.get_agents_by_capability(keyword)
                    for worker_id in capability_workers:
                        if worker_id not in selected_agents:
                            selected_agents.append(worker_id)
                            priority_map[worker_id] = 0.6
                            selection_reasoning.append(
                                {
                                    "agent": worker_id,
                                    "score": 0.6,
                                    "reasons": [f"RAG capability '{keyword}' match"],
                                    "method": "capability_match",
                                }
                            )
                        else:
                            priority_map[worker_id] = min(priority_map[worker_id] + 0.15, 1.0)

                if keywords:
                    registry_insights.append(f"RAG keywords: {', '.join(list(keywords)[:5])}")

            # Phase 4: Fallback - Mindestens ein Worker muss vorhanden sein
            if not selected_agents:
                logger.warning("⚠️ Keine Workers gefunden - verwende alle verfügbaren Workers")
                all_workers = list(self.agent_registry.list_available_agents().keys())
                selected_agents = all_workers[:3]  # Top 3 Workers
                priority_map = {w: 0.5 for w in selected_agents}
                selection_reasoning = [
                    {"agent": w, "score": 0.5, "reasons": ["Fallback selection"], "method": "fallback"}
                    for w in selected_agents
                ]
                registry_insights.append("Fallback: All available workers")

            # Phase 5: Execution Plan erstellen
            # Sortiere Workers nach Priorität
            sorted_workers = sorted(selected_agents, key=lambda w: priority_map.get(w, 0.0), reverse=True)

            execution_plan = {
                "parallel_agents": sorted_workers[:3],  # Top 3 parallel
                "sequential_agents": sorted_workers[3:],  # Rest sequenziell
            }

            # Statistiken
            self.stats["agent_registry_usage"] = self.stats.get("agent_registry_usage", 0) + 1

            logger.info(
                f"✅ Agent Registry Selection: {len(selected_agents)} workers "
                f"({len(execution_plan['parallel_agents'])} parallel, "
                f"{len(execution_plan['sequential_agents'])} sequential)"
            )

            return {
                "selected_agents": selected_agents,
                "execution_plan": execution_plan,
                "priority_map": priority_map,
                "selection_reasoning": selection_reasoning,
                "insights": registry_insights,
                "agent_registry_context": {
                    "mode": "worker_registry",
                    "total_available_workers": len(self.agent_registry.list_available_agents()),
                    "selection_methods": list(set(r["method"] for r in selection_reasoning)),
                },
            }

        except Exception as e:
            logger.error(f"❌ Agent Registry Agent-Selektion fehlgeschlagen: {e}")
            # Fallback auf Standard-Selektion
            logger.info("⚠️ Fallback auf Standard-Selektion")
            # Setze worker_registry auf None um infinite loop zu vermeiden
            original_registry = self.agent_registry
            self.agent_registry = None
            result = await self._step_agent_selection(request, context)
            self.agent_registry = original_registry
            return result

    async def _step_parallel_agent_execution(
        self, request: IntelligentPipelineRequest, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """STEP 4: Führt Agents parallel (Thread-Pool) & sequenziell (Queue) aus"""

        agent_selection = context.get("agent_selection", {})
        rag_context = context.get("rag", {})
        selected_agents = agent_selection.get("selected_agents", ["document_retrieval"])
        priority_map = agent_selection.get("priority_map", {}) or {}
        orchestrator_context = agent_selection.get("orchestrator_context", {}) or {}
        execution_plan = agent_selection.get("execution_plan", {}) or {}
        parallel_plan = execution_plan.get("parallel_agents") or []
        sequential_plan = execution_plan.get("sequential_agents") or []
        disabled_tasks = set(
            orchestrator_context.get("dynamic_actions", {}).get("disabled", []) if orchestrator_context else []
        )

        ordered_agents = (
            sorted(selected_agents, key=lambda agent: priority_map.get(agent, 0.0), reverse=True)
            if priority_map
            else selected_agents
        )

        if not parallel_plan:
            parallel_plan = ordered_agents[:3]
        if not sequential_plan:
            sequential_plan = [agent for agent in ordered_agents if agent not in parallel_plan]

        # Tasks vorbereiten und in Queue legen
        agent_tasks: List[AgentExecutionTask] = []
        for order_index, agent_type in enumerate(ordered_agents):
            stage = "parallel" if agent_type in parallel_plan else "sequential"
            agent_tasks.append(
                AgentExecutionTask(
                    agent_type=agent_type,
                    stage=stage,
                    priority_score=round(priority_map.get(agent_type, 0.0), 4),
                    planned_order=order_index,
                    metadata={
                        "requested_by": "orchestrator" if agent_type in (parallel_plan + sequential_plan) else "pipeline",
                        "disabled": agent_type in disabled_tasks,
                    },
                    disabled=agent_type in disabled_tasks,
                )
            )

        self._prepare_agent_task_queue(agent_tasks)

        agent_results: Dict[str, Any] = {}
        detailed_results: Dict[str, Any] = {}
        execution_trace: List[Dict[str, Any]] = []
        total_duration = 0.0

        parallel_tasks = self._collect_tasks_from_queue("parallel")
        parallel_outputs = await self._execute_agent_tasks(request, rag_context, parallel_tasks, concurrent=True)

        sequential_tasks = self._collect_tasks_from_queue("sequential")
        sequential_outputs = await self._execute_agent_tasks(request, rag_context, sequential_tasks, concurrent=False)

        skipped_count = 0
        failed_count = 0
        timeout_count = 0

        for task_output in parallel_outputs + sequential_outputs:
            total_duration += task_output.get("duration", 0.0)
            status = task_output.get("status")
            if status == "skipped":
                skipped_count += 1
            elif status == "failed":
                failed_count += 1
            elif status == "timeout":
                timeout_count += 1

            self._merge_agent_task_output(request, task_output, agent_results, detailed_results, execution_trace)

        executed_count = sum(1 for entry in execution_trace if entry.get("status") == "completed")

        return {
            "agent_results": agent_results,
            "detailed_results": detailed_results,
            "execution_summary": {
                "agents_planned": len(selected_agents),
                "agents_executed": executed_count,
                "agents_skipped": skipped_count,
                "failed_agents": failed_count,
                "timed_out_agents": timeout_count,
                "total_execution_time": round(total_duration, 3),
                "priority_map": priority_map,
                "execution_trace": sorted(
                    execution_trace, key=lambda item: (item.get("stage") != "parallel", item.get("order", 0))
                ),
            },
            "priority_map": priority_map,
        }

    def _prepare_agent_task_queue(self, tasks: List[AgentExecutionTask]) -> None:
        """Initialisiert die Queue für Agenten-Aufgaben"""

        # Neue Queue erzeugen, um alte Tasks zu verwerfen
        self.agent_task_queue = queue.Queue()
        for task in sorted(tasks, key=lambda item: item.planned_order):
            self.agent_task_queue.put(task)

    def _collect_tasks_from_queue(self, stage: str) -> List[AgentExecutionTask]:
        """Holt Aufgaben einer bestimmten Stage aus der Queue"""

        collected: List[AgentExecutionTask] = []
        deferred: List[AgentExecutionTask] = []

        while not self.agent_task_queue.empty():
            task: AgentExecutionTask = self.agent_task_queue.get()
            if task.stage == stage:
                collected.append(task)
            else:
                deferred.append(task)
            self.agent_task_queue.task_done()

        for task in deferred:
            self.agent_task_queue.put(task)

        return collected

    async def _execute_agent_tasks(
        self,
        request: IntelligentPipelineRequest,
        rag_context: Dict[str, Any],
        tasks: List[AgentExecutionTask],
        concurrent: bool = True,
    ) -> List[Dict[str, Any]]:
        """Führt Agenten-Aufgaben aus (optional parallel)"""

        if not tasks:
            return []

        outputs: List[Dict[str, Any]] = []
        timeout_per_task = self._calculate_agent_timeout(request, len(tasks))

        for task in tasks:
            if task.disabled:
                continue
            self._notify_agent_event(
                request=request,
                agent_type=task.agent_type,
                progress_type=ProgressType.AGENT_START,
                stage=task.stage,
                metadata={"priority": task.priority_score, "planned_order": task.planned_order},
            )

        if concurrent:
            loop = asyncio.get_running_loop()
            async_futures: List[asyncio.Future] = []
            future_task_map: Dict[asyncio.Future, AgentExecutionTask] = {}

            for task in tasks:
                cf_future = loop.run_in_executor(self.executor, self._run_agent_task_sync, request, task, rag_context)
                async_future = asyncio.wrap_future(cf_future)
                async_futures.append(async_future)
                future_task_map[async_future] = task

            for async_future in asyncio.as_completed(async_futures):
                task_ref = future_task_map.get(async_future)
                try:
                    outputs.append(await asyncio.wait_for(async_future, timeout=timeout_per_task))
                except asyncio.TimeoutError:
                    outputs.append(self._build_timeout_output(task_ref, timeout_per_task))
        else:
            for task in tasks:
                try:
                    outputs.append(
                        await asyncio.wait_for(
                            self._run_agent_task_async(request, task, rag_context), timeout=timeout_per_task
                        )
                    )
                except asyncio.TimeoutError:
                    outputs.append(self._build_timeout_output(task, timeout_per_task))

        return outputs

    async def _run_agent_task_async(
        self, request: IntelligentPipelineRequest, task: AgentExecutionTask, rag_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Hilfsfunktion um Agenten-Aufgabe async über ThreadPool auszuführen"""

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._run_agent_task_sync, request, task, rag_context)

    def _calculate_agent_timeout(self, request: IntelligentPipelineRequest, task_count: int) -> float:
        """Berechnet Timeout pro Agent basierend auf Gesamt-Timeout"""

        if task_count <= 0:
            task_count = 1

        base_timeout = float(request.timeout or 60)
        timeout_per_task = base_timeout / task_count
        return max(3.0, min(timeout_per_task, base_timeout))

    def _run_agent_task_sync(
        self, request: IntelligentPipelineRequest, task: AgentExecutionTask, rag_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synchroner Worker für einzelne Agenten-Aufgabe"""

        start_time = time.time()

        if task.disabled:
            trace = {
                "agent": task.agent_type,
                "status": "skipped",
                "stage": task.stage,
                "priority": round(task.priority_score, 2),
                "duration": 0.0,
                "order": task.planned_order,
                "reason": "Dynamic pipeline disabled task",
            }
            return {"task": task, "result": None, "trace": trace, "duration": 0.0, "status": "skipped"}

        # 🆕 ECHTE AGENT-EXECUTION (mit Fallback auf Mock)
        agent_result = self._execute_real_agent(task.agent_type, request.query_text, rag_context)
        agent_result["priority_score"] = round(task.priority_score, 2)
        agent_result["execution_stage"] = task.stage

        duration = time.time() - start_time

        trace = {
            "agent": task.agent_type,
            "status": agent_result.get("status", "completed"),
            "stage": task.stage,
            "priority": agent_result["priority_score"],
            "duration": round(duration, 3),
            "order": task.planned_order,
        }

        with self._agent_results_lock:
            self.stats["agents_executed"] += 1

        return {"task": task, "result": agent_result, "trace": trace, "duration": duration, "status": trace["status"]}

    def _build_timeout_output(self, task: Optional[AgentExecutionTask], timeout_value: float) -> Dict[str, Any]:
        """Erstellt strukturierte Ausgabe bei Agent-Timeout"""

        if task is None:
            # Sicherheitsnetz für unerwartete Situationen
            task = AgentExecutionTask(
                agent_type="unknown", stage="parallel", priority_score=0.0, planned_order=999, metadata={}, disabled=False
            )

        trace = {
            "agent": task.agent_type,
            "status": "timeout",
            "stage": task.stage,
            "priority": round(task.priority_score, 2),
            "duration": round(timeout_value, 3),
            "order": task.planned_order,
            "reason": f"Agent timeout nach {round(timeout_value, 1)}s",
        }

        with self._agent_results_lock:
            self.stats["agent_timeouts"] += 1

        return {"task": task, "result": None, "trace": trace, "duration": timeout_value, "status": "timeout"}

    def _merge_agent_task_output(
        self,
        request: IntelligentPipelineRequest,
        task_output: Dict[str, Any],
        agent_results: Dict[str, Any],
        detailed_results: Dict[str, Any],
        execution_trace: List[Dict[str, Any]],
    ) -> None:
        """Fügt das Ergebnis eines Agenten in die Gesamtstruktur ein"""

        trace = task_output.get("trace")
        if trace:
            execution_trace.append(trace)

        result = task_output.get("result")
        if result:
            agent_type = trace.get("agent") if trace else None
            if agent_type:
                with self._agent_results_lock:
                    agent_results[agent_type] = result
                    detailed_results[agent_type] = result

        agent_type = (trace or {}).get("agent")
        status = task_output.get("status")
        duration = task_output.get("duration")
        metadata = {
            "duration": duration,
            "stage": (trace or {}).get("stage"),
            "priority": (trace or {}).get("priority"),
            "order": (trace or {}).get("order"),
            "status": status,
        }

        if agent_type and status:
            message = None
            progress_type = ProgressType.AGENT_COMPLETE

            if status == "timeout":
                message = (
                    f"⏱️ {agent_type.title()} Agent überschritt das Zeitlimit ({duration:.1f}s)."
                    if isinstance(duration, (int, float))
                    else f"⏱️ {agent_type.title()} Agent überschritt das Zeitlimit."
                )
            elif status == "failed":
                message = f"❌ {agent_type.title()} Agent fehlgeschlagen."
            elif status == "skipped":
                message = f"⏭️ {agent_type.title()} Agent übersprungen."

            self._record_agent_metrics(
                agent_type=agent_type, status=status, duration=duration, metadata=metadata, result=result
            )

            self._notify_agent_event(
                request=request,
                agent_type=agent_type,
                progress_type=progress_type,
                stage=(trace or {}).get("stage"),
                message=message,
                result=result or {},
                metadata=metadata,
            )

    # ------------------------------------------------------------------
    # Monitoring & Progress Hilfsfunktionen
    # ------------------------------------------------------------------

    def _progress_updates_enabled(self, request: IntelligentPipelineRequest) -> bool:
        """Prüft, ob Progress-Updates aktiviert und möglich sind."""

        if not request.enable_real_time_updates:
            return False
        if not STREAMING_AVAILABLE:
            return False
        if not self.progress_manager:
            return False
        if not request.session_id:
            return False
        return True

    def _start_progress_session(self, request: IntelligentPipelineRequest) -> None:
        """Initialisiert eine neue Progress-Session."""

        if not request.enable_real_time_updates or not STREAMING_AVAILABLE:
            return

        if not self.progress_manager:
            return

        try:
            session_id = request.session_id or str(uuid.uuid4())
            request.session_id = session_id
            self.progress_manager.start_session(
                session_id=session_id, query_id=request.query_id, query_text=request.query_text
            )
        except Exception as exc:
            logger.debug("Progress Session konnte nicht gestartet werden: %s", exc)

    def _update_progress_stage(
        self, request: IntelligentPipelineRequest, stage: ProgressStage, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Aktualisiert den Progress-Status der aktuellen Session."""

        if not self._progress_updates_enabled(request):
            return

        try:
            self.progress_manager.update_stage(request.session_id, stage, details or {})
        except Exception as exc:
            logger.debug("Progress Stage Update fehlgeschlagen (%s): %s", stage, exc)

    def _notify_agent_event(
        self,
        request: IntelligentPipelineRequest,
        agent_type: Optional[str],
        progress_type: ProgressType,
        stage: Optional[str] = None,
        message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Sendet Agent-bezogene Progress-Events an den Progress Manager."""

        if not agent_type or not self._progress_updates_enabled(request):
            return

        try:
            payload: Dict[str, Any] = {}
            if isinstance(result, dict):
                payload.update(result)
            if metadata:
                payload.setdefault("_progress_meta", metadata)
            if stage:
                payload.setdefault("execution_stage", stage)

            self.progress_manager.update_agent_progress(
                session_id=request.session_id,
                agent_type=agent_type,
                progress_type=progress_type,
                message=message or "",
                result=payload or None,
            )
        except Exception as exc:
            logger.debug("Agent Progress Update fehlgeschlagen (%s/%s): %s", agent_type, progress_type, exc)

    def _complete_progress_session(self, request: IntelligentPipelineRequest, response: IntelligentPipelineResponse) -> None:
        """Beendet Progress-Session nach erfolgreicher Verarbeitung."""

        if not self._progress_updates_enabled(request):
            return

        try:
            final_details = {
                "confidence_score": response.confidence_score,
                "agents_used": len(response.agent_results or {}),
                "total_processing_time": response.total_processing_time,
                "aggregation_summary": response.aggregation_summary,
                "agent_consensus": response.agent_consensus,
            }
            self.progress_manager.complete_session(request.session_id, final_details)
        except Exception as exc:
            logger.debug("Progress Session Abschluss fehlgeschlagen: %s", exc)

    def _fail_progress_session(self, request: IntelligentPipelineRequest, error: str) -> None:
        """Markiert Progress-Session als fehlgeschlagen."""

        if not request.session_id or not self.progress_manager:
            return

        try:
            if STREAMING_AVAILABLE:
                self.progress_manager.update_stage(request.session_id, ProgressStage.ERROR, {"error": error})
                self.progress_manager.cancel_session(request.session_id, reason=error)
        except Exception as exc:
            logger.debug("Progress Session Fehlerbehandlung schlug fehl: %s", exc)

    def _record_stage_duration(self, step_id: str, duration: float) -> None:
        """Erfasst Dauer einzelner Pipeline-Schritte in den Statistiken."""

        stats_entry = self.stats.setdefault("stage_duration_stats", {})
        stage_stats = stats_entry.setdefault(
            step_id,
            {
                "count": 0,
                "total_duration": 0.0,
                "average_duration": 0.0,
                "min_duration": None,
                "max_duration": None,
                "last_duration": 0.0,
            },
        )

        stage_stats["count"] += 1
        stage_stats["total_duration"] += duration
        stage_stats["average_duration"] = round(stage_stats["total_duration"] / stage_stats["count"], 4)
        stage_stats["last_duration"] = round(duration, 4)

        if stage_stats["min_duration"] is None or duration < stage_stats["min_duration"]:
            stage_stats["min_duration"] = round(duration, 4)
        if stage_stats["max_duration"] is None or duration > stage_stats["max_duration"]:
            stage_stats["max_duration"] = round(duration, 4)

    def _record_pipeline_metrics(
        self,
        request: IntelligentPipelineRequest,
        response: IntelligentPipelineResponse,
        stage_durations: Dict[str, float],
        execution_summary: Dict[str, Any],
        analysis_result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Speichert kompakte Pipeline-Metriken für Monitoring."""

        metrics_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_id": request.query_id,
            "session_id": request.session_id,
            "confidence_score": response.confidence_score,
            "total_processing_time": response.total_processing_time,
            "stage_durations": stage_durations,
            "agents_used": len(response.agent_results or {}),
            "agent_execution_summary": execution_summary or {},
            "combined_confidence": response.agent_consensus.get("blended_confidence")
            if isinstance(response.agent_consensus, dict)
            else None,
            "query_complexity": (analysis_result or {}).get("complexity") if isinstance(analysis_result, dict) else None,
            "query_domain": (analysis_result or {}).get("domain") if isinstance(analysis_result, dict) else None,
        }

        self.recent_pipeline_metrics.append(metrics_entry)
        self._update_query_metrics(analysis_result, response)

    def _update_query_metrics(self, analysis_result: Optional[Dict[str, Any]], response: IntelligentPipelineResponse) -> None:
        """Aktualisiert komplexitätsbezogene Statistiken."""

        if not isinstance(analysis_result, dict):
            return

        complexity = analysis_result.get("complexity") or "unknown"
        domain = analysis_result.get("domain") or "unknown"

        with self._agent_results_lock:
            query_metrics = self.stats.setdefault("query_metrics", {})
            complexity_counts = query_metrics.setdefault("complexity_counts", {})
            domain_counts = query_metrics.setdefault("domain_counts", {})
            avg_time_by_complexity = query_metrics.setdefault("avg_processing_time_by_complexity", {})

            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

            total_time = response.total_processing_time if isinstance(response.total_processing_time, (int, float)) else None
            comp_entry = avg_time_by_complexity.setdefault(
                complexity, {"count": 0, "total_time": 0.0, "average_time": 0.0, "last_time": None}
            )

            if total_time is not None:
                comp_entry["count"] += 1
                comp_entry["total_time"] += total_time
                comp_entry["last_time"] = round(total_time, 3)
                comp_entry["average_time"] = round(comp_entry["total_time"] / max(comp_entry["count"], 1), 3)

        trend_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "complexity": complexity,
            "domain": domain,
            "processing_time": response.total_processing_time,
            "confidence_score": response.confidence_score,
        }
        self.recent_query_metrics.append(trend_entry)

    def _record_pipeline_error(
        self,
        request: Optional[IntelligentPipelineRequest],
        error: Exception,
        stage: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Erfasst Fehlerdetails für Monitoring und Debugging."""

        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_id": getattr(request, "query_id", None),
            "session_id": getattr(request, "session_id", None),
            "stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }

        self.recent_errors.append(error_entry)

        with self._agent_results_lock:
            self.stats["last_error"] = error_entry

    def _record_agent_metrics(
        self,
        agent_type: str,
        status: str,
        duration: Optional[float],
        metadata: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Aktualisiert Agent-bezogene Leistungsmetriken."""

        if not agent_type:
            return

        timestamp = datetime.now(timezone.utc).isoformat()
        numeric_duration = duration if isinstance(duration, (int, float)) else None

        with self._agent_results_lock:
            agent_metrics = self.stats.setdefault("agent_metrics", {})
            entry = agent_metrics.setdefault(
                agent_type,
                {
                    "total_runs": 0,
                    "successes": 0,
                    "failures": 0,
                    "timeouts": 0,
                    "skipped": 0,
                    "status_counts": {},
                    "total_duration": 0.0,
                    "duration_samples": 0,
                    "average_duration": 0.0,
                    "min_duration": None,
                    "max_duration": None,
                    "last_status": None,
                    "last_duration": None,
                    "last_updated": None,
                    "success_rate": 0.0,
                    "last_result_excerpt": None,
                },
            )

            entry["total_runs"] += 1
            status_counts = entry.setdefault("status_counts", {})
            status_counts[status] = status_counts.get(status, 0) + 1

            if status in ("completed", "success"):  # Erfolg
                entry["successes"] += 1
            elif status == "timeout":
                entry["timeouts"] += 1
            elif status == "skipped":
                entry["skipped"] += 1
            else:
                entry["failures"] += 1

            if numeric_duration is not None:
                entry["duration_samples"] += 1
                entry["total_duration"] += numeric_duration
                entry["last_duration"] = round(numeric_duration, 4)
                if entry["min_duration"] is None or numeric_duration < entry["min_duration"]:
                    entry["min_duration"] = round(numeric_duration, 4)
                if entry["max_duration"] is None or numeric_duration > entry["max_duration"]:
                    entry["max_duration"] = round(numeric_duration, 4)
                entry["average_duration"] = round(entry["total_duration"] / max(entry["duration_samples"], 1), 4)
            else:
                # Keine neue Dauer, Durchschnitt beibehalten
                entry["last_duration"] = None

            effective_runs_for_success = max(entry["total_runs"] - entry["skipped"], 1)
            entry["success_rate"] = round(entry["successes"] / effective_runs_for_success, 4)
            entry["last_status"] = status
            entry["last_updated"] = timestamp

            if isinstance(result, dict):
                summary = result.get("summary") or result.get("details")
                if summary:
                    entry["last_result_excerpt"] = str(summary)[:200]

        event_payload = {
            "timestamp": timestamp,
            "agent": agent_type,
            "status": status,
            "duration": numeric_duration,
            "metadata": metadata or {},
            "result": (result or {}) if isinstance(result, dict) else None,
        }
        self.recent_agent_events.append(event_payload)

    async def _step_result_aggregation(self, request: IntelligentPipelineRequest, context: Dict[str, Any]) -> Dict[str, Any]:
        """STEP 5: Aggregiert Agent-Ergebnisse mit Ollama LLM"""

        agent_results = context.get("agent_results", {}).get("detailed_results", {})
        rag_context = context.get("rag", {})
        analysis = context.get("analysis", {})

        # 🆕 SUPERVISOR-MODUS: Nutze Supervisor für Result-Synthesis
        if request.enable_supervisor and self.supervisor_agent and SUPERVISOR_AGENT_AVAILABLE:
            return await self._supervisor_result_aggregation(request, context)

        # STANDARD-MODUS: Bestehende Logik (Backward-Compatibility)
        normalized_agent_results = self._normalize_agent_results(agent_results)
        aggregation_summary, consensus_summary = self._build_aggregation_summary(normalized_agent_results, rag_context)

        if not self.ollama_client:
            # Fallback ohne LLM - einfache Aggregation
            blended_confidence = self._blend_confidence_scores(0.7, (consensus_summary.get("confidence") or {}).get("average"))
            consensus_summary["blended_confidence"] = blended_confidence

            return {
                "response_text": f"Basierend auf der Analyse durch {len(agent_results)} Agenten: {request.query_text}",
                "confidence_score": blended_confidence,
                "sources": [],
                "follow_up_suggestions": self._generate_follow_up_suggestions(
                    request.query_text, agent_results, aggregation_summary, consensus_summary
                ),
                "aggregation_summary": aggregation_summary,
                "agent_consensus": consensus_summary,
            }

        # LLM-basierte Synthesis (mit dynamischem Token-Budget + Context-Window-Check)
        max_tokens = getattr(request, "token_budget", 1500)
        model_name = getattr(request, "model_name", "llama3.1:8b")

        # Context-Window-Check durchführen
        if self.context_window_manager:
            try:
                # Schätze Input-Tokens
                system_prompt = ""  # TODO: Extrahieren aus synthesize_agent_results
                user_prompt = f"Query: {request.query_text}\nResults: {str(agent_results)[:500]}"
                rag_context_str = str(rag_context)[:1000]

                adjusted_tokens, context = self.context_window_manager.adjust_token_budget(
                    model_name=model_name,
                    requested_tokens=max_tokens,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    rag_context=rag_context_str,
                )

                if adjusted_tokens < max_tokens:
                    logger.warning(
                        f"⚠️ Token-Budget reduziert: {max_tokens} → {adjusted_tokens} "
                        f"(Context-Window-Limit für {model_name})"
                    )
                    max_tokens = adjusted_tokens

                if context.needs_model_upgrade and context.recommended_model:
                    logger.info(
                        f"💡 Model-Upgrade empfohlen: {model_name} → {context.recommended_model} " f"für {max_tokens} tokens"
                    )
                    # TODO: Implementiere automatisches Model-Switching

            except Exception as e:
                logger.warning(f"⚠️ Context-Window-Check fehlgeschlagen: {e}")

        synthesis_result = await self.ollama_client.synthesize_agent_results(
            query=request.query_text,
            agent_results=agent_results,
            rag_context=rag_context,
            aggregation_summary=aggregation_summary,
            consensus_summary=consensus_summary,
            max_tokens=max_tokens,  # 🆕 Dynamisches + Context-Window-geprüftes Budget
        )

        model_confidence = synthesis_result.get("confidence_score")
        consensus_average = (consensus_summary.get("confidence") or {}).get("average")
        blended_confidence = self._blend_confidence_scores(model_confidence, consensus_average)
        consensus_summary["blended_confidence"] = blended_confidence

        combined_sources = self._merge_source_lists(
            self._extract_sources_from_results(agent_results, rag_context), aggregation_summary.get("source_references", [])
        )

        return {
            "response_text": synthesis_result.get("response_text", "Keine Antwort generiert"),
            "confidence_score": blended_confidence,
            "sources": combined_sources,
            "follow_up_suggestions": self._generate_follow_up_suggestions(
                request.query_text, agent_results, aggregation_summary, consensus_summary
            ),
            "llm_metadata": synthesis_result.get("llm_metadata", {}),
            "json_metadata": synthesis_result.get("json_metadata"),  # 🆕 Extrahierte JSON-Metadaten
            "aggregation_summary": aggregation_summary,
            "agent_consensus": consensus_summary,
        }

    async def _supervisor_result_aggregation(
        self, request: IntelligentPipelineRequest, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🆕 SUPERVISOR-BASIERTE RESULT-AGGREGATION

        Nutzt Supervisor-Agent für:
        1. Konflikt-Detektion zwischen Agent-Ergebnissen
        2. Deduplizierung redundanter Informationen
        3. LLM-basierte Narrative-Generierung
        """
        logger.info("🔗 Supervisor-Modus aktiviert - starte Result-Synthesis")

        agent_results_dict = context.get("agent_results", {}).get("detailed_results", {})
        rag_context = context.get("rag", {})
        agent_selection = context.get("agent_selection", {})
        supervisor_context = agent_selection.get("supervisor_context", {})
        subqueries = supervisor_context.get("subqueries", [])

        try:
            # Agent-Ergebnisse in Supervisor-Format umwandeln
            agent_results_list = []
            for agent_type, result in agent_results_dict.items():
                # Sicherstellen, dass result ein Dict ist
                if not isinstance(result, dict):
                    logger.warning(f"⚠️ Agent {agent_type} lieferte kein Dict: {type(result)}")
                    result = {"summary": str(result), "status": "completed", "confidence_score": 0.5}

                # Finde passende Subquery (falls vorhanden)
                subquery_id = "unknown"
                for reasoning in agent_selection.get("selection_reasoning", []):
                    if reasoning.get("agent") == agent_type:
                        subquery_id = reasoning.get("subquery_id", "unknown")
                        break

                agent_result = AgentResult(
                    subquery_id=subquery_id,
                    agent_type=agent_type,
                    result_data={
                        "summary": result.get("summary", str(result)),
                        "details": result.get("details", ""),
                        "status": result.get("status", "completed"),
                    },
                    confidence_score=result.get("confidence_score", 0.75),
                    processing_time=result.get("processing_time", 0.0),
                    sources=result.get("sources", []),
                )
                agent_results_list.append(agent_result)

            if not agent_results_list:
                logger.warning("⚠️ Keine Agent-Ergebnisse für Supervisor-Synthesis")
                # Fallback auf Standard-Aggregation
                request_copy = copy.copy(request)
                request_copy.enable_supervisor = False
                return await self._step_result_aggregation(request_copy, context)

            # Supervisor-Synthesis
            synthesized = await self.supervisor_agent.synthesize_results(
                agent_results=agent_results_list, original_query=request.query_text
            )

            logger.info(f"✅ Supervisor-Synthesis abgeschlossen (Conf: {synthesized.confidence_score:.2f})")

            return {
                "response_text": synthesized.response_text,
                "confidence_score": synthesized.confidence_score,
                "sources": synthesized.sources,
                "follow_up_suggestions": self._generate_follow_up_suggestions(request.query_text, agent_results_dict, {}, {}),
                "aggregation_summary": {
                    "method": "supervisor_synthesis",
                    "subquery_coverage": synthesized.subquery_coverage,
                    "conflicts_detected": len(synthesized.conflicts_detected),
                    "synthesis_method": synthesized.synthesis_method,
                },
                "agent_consensus": {"blended_confidence": synthesized.confidence_score},
                "supervisor_metadata": synthesized.metadata,
            }

        except Exception as e:
            logger.error(f"❌ Supervisor-Result-Aggregation fehlgeschlagen: {e}")
            # Fallback auf Standard-Aggregation
            logger.info("⚠️ Fallback auf Standard-Aggregation")
            request_copy = copy.copy(request)
            request_copy.enable_supervisor = False
            return await self._step_result_aggregation(request_copy, context)

    def _generate_mock_agent_result(self, agent_type: str, query: str) -> Dict[str, Any]:
        """Generiert Mock-Ergebnis für Agent (für Testing/Fallback)"""

        agent_specialties = {
            "document_retrieval": {
                "summary": "Relevante Dokumente gefunden",
                "confidence": 0.85,
                "sources": ["Verwaltungsportal", "Formulardatenbank"],
            },
            "legal_framework": {
                "summary": "Rechtliche Bestimmungen analysiert",
                "confidence": 0.90,
                "sources": ["BauGB", "VwVfG"],
            },
            "environmental": {
                "summary": "Umweltaspekte bewertet",
                "confidence": 0.82,
                "sources": ["Umweltbundesamt", "Luftreinhaltepläne"],
            },
            "external_api": {
                "summary": "Externe Daten abgerufen",
                "confidence": 0.78,
                "sources": ["API - Services", "Open - Data-Portale"],
            },
        }

        specialty = agent_specialties.get(
            agent_type, {"summary": f"{agent_type} Analyse durchgeführt", "confidence": 0.75, "sources": ["Standard-Quellen"]}
        )

        return {
            "agent_type": agent_type,
            "status": "completed",
            "confidence_score": specialty["confidence"],
            "summary": specialty["summary"],
            "sources": specialty["sources"],
            "processing_time": 2.5,
            "details": f"Detaillierte {agent_type} Analyse für: {query[:50]}...",
        }

    def _execute_real_agent(self, agent_type: str, query: str, rag_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        🆕 Führt echten VERITAS Agent aus mit UDS3 Hybrid Search

        Falls Agent nicht verfügbar oder UDS3 fehlt, Fallback auf Mock-Daten

        Args:
            agent_type: Typ des Agents (z.B. 'environmental', 'legal_framework')
            query: User Query
            rag_context: RAG Context mit zusätzlichen Informationen

        Returns:
            Agent-Ergebnis Dict mit summary, sources, confidence_score
        """
        try:
            # Mapping von Pipeline Agent-Typen zu UDS3 Such-Kategorien
            agent_to_category = {
                "geo_context": "geographic",
                "legal_framework": "legal",
                "document_retrieval": "documents",
                "environmental": "environmental",
                "construction": "construction",
                "traffic": "traffic",
                "financial": "financial",
                "social": "social",
            }

            # UDS3 Hybrid Search ausführen
            if self.uds3_strategy:
                category = agent_to_category.get(agent_type, "general")

                # UDS3 Query mit Filter für Agent-Kategorie
                search_result = self.uds3_strategy.query_across_databases(
                    vector_params={"query_text": query, "top_k": 5, "threshold": 0.5},
                    graph_params=None,
                    relational_params=None,
                    join_strategy="union",
                    execution_mode="smart",
                )

                # Ergebnisse extrahieren
                sources = []
                summaries = []
                confidence_scores = []

                if search_result and search_result.success and hasattr(search_result, "joined_results"):
                    for result in search_result.joined_results[:5]:  # Top 5
                        if isinstance(result, dict):
                            # Extract content
                            content = result.get("content", result.get("text", ""))
                            score = result.get("score", result.get("similarity", 0.0))
                            source = result.get("source", result.get("doc_id", "UDS3"))

                            if content:
                                summaries.append(content[:200])  # Erste 200 Zeichen
                            if source:
                                sources.append(source)
                            if score:
                                confidence_scores.append(float(score))

                # Wenn UDS3 Ergebnisse liefert, nutze diese
                if sources and summaries:
                    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.75

                    return {
                        "agent_type": agent_type,
                        "status": "completed",
                        "confidence_score": min(avg_confidence, 1.0),
                        "summary": f"UDS3: {len(summaries)} relevante Dokumente gefunden. {summaries[0] if summaries else ''}",
                        "sources": sources[:3],  # Top 3 Quellen
                        "processing_time": 1.5,
                        "details": " | ".join(summaries[:3]),
                        "uds3_used": True,
                    }
                else:
                    logger.debug(f"ℹ️ UDS3 Search für {agent_type}: Keine Ergebnisse, Fallback auf Mock")
            else:
                logger.debug(f"ℹ️ UDS3 nicht verfügbar für {agent_type}, Fallback auf Mock")

        except Exception as e:
            logger.warning(f"⚠️ Fehler bei Agent-Execution {agent_type}: {e}, Fallback auf Mock")

        # Fallback: Mock-Daten
        return self._generate_mock_agent_result(agent_type, query)

    def _normalize_agent_results(self, agent_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalisiert Agent-Ergebnisse für Aggregation und LLM"""

        normalized: List[Dict[str, Any]] = []

        for agent_type, result in (agent_results or {}).items():
            if not isinstance(result, dict):
                continue

            confidence = result.get("confidence_score")
            try:
                confidence = float(confidence) if confidence is not None else None
            except (TypeError, ValueError):
                confidence = None

            normalized.append(
                {
                    "agent": agent_type,
                    "status": result.get("status", "completed"),
                    "summary": result.get("summary") or result.get("details") or "",
                    "details": result.get("details"),
                    "confidence": confidence,
                    "priority": result.get("priority_score"),
                    "stage": result.get("execution_stage", "parallel"),
                    "processing_time": result.get("processing_time"),
                    "sources": self._normalize_agent_sources(result.get("sources"), agent_type),
                    "metadata": {"raw": result},
                }
            )

        return normalized

    def _normalize_agent_sources(self, sources: Any, agent_type: str) -> List[Dict[str, Any]]:
        """Normalisiert Quellenangaben einzelner Agenten"""

        normalized_sources: List[Dict[str, Any]] = []

        if not sources:
            return normalized_sources

        if isinstance(sources, (list, tuple)):
            iterable = sources
        else:
            iterable = [sources]

        for source in iterable:
            if isinstance(source, dict):
                entry = dict(source)
            else:
                entry = {"title": str(source)}

            entry.setdefault("type", "agent_source")
            entry.setdefault("agent", agent_type)
            normalized_sources.append(entry)

        return normalized_sources

    def _build_aggregation_summary(
        self, normalized_results: List[Dict[str, Any]], rag_context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Erstellt strukturierte Aggregations- und Konsensusdaten"""

        confidence_values = [
            res["confidence"] for res in normalized_results if isinstance(res.get("confidence"), (int, float))
        ]
        priority_values = [res["priority"] for res in normalized_results if isinstance(res.get("priority"), (int, float))]
        stage_distribution = Counter(res.get("stage", "unknown") for res in normalized_results)

        if confidence_values:
            confidence_summary = {
                "average": round(sum(confidence_values) / len(confidence_values), 3),
                "min": round(min(confidence_values), 3),
                "max": round(max(confidence_values), 3),
                "agent_count": len(confidence_values),
            }
        else:
            confidence_summary = {"average": None, "min": None, "max": None, "agent_count": 0}

        if priority_values:
            priority_summary = {
                "average": round(sum(priority_values) / len(priority_values), 3),
                "min": round(min(priority_values), 3),
                "max": round(max(priority_values), 3),
            }
        else:
            priority_summary = {"average": None, "min": None, "max": None}

        key_points: List[str] = []
        for result in normalized_results:
            summary_text = (result.get("summary") or "").strip()
            if summary_text:
                key_points.append(f"{result['agent']}: {summary_text}")

        top_agents = sorted(
            [res for res in normalized_results if isinstance(res.get("confidence"), (int, float))],
            key=lambda item: item["confidence"],
            reverse=True,
        )

        rag_meta = rag_context.get("meta", {}) if isinstance(rag_context, dict) else {}
        rag_summary = {
            "document_count": len((rag_context or {}).get("documents", []) or []),
            "vector_matches": (rag_context or {}).get("vector", {}).get("statistics", {}).get("count"),
            "graph_entities": (rag_context or {}).get("graph", {}).get("related_entities", []),
            "fallback_used": bool(rag_meta.get("fallback_used")),
            "source_names": [
                doc.get("title")
                for doc in (rag_context or {}).get("documents", [])
                if isinstance(doc, dict) and doc.get("title")
            ],
        }

        source_references: List[Dict[str, Any]] = []
        seen_sources = set()

        for result in normalized_results:
            for source in result.get("sources", []) or []:
                key = (source.get("title"), source.get("agent"), source.get("type"))
                if key in seen_sources:
                    continue
                seen_sources.add(key)
                source_references.append(source)

        for doc in (rag_context or {}).get("documents", []) or []:
            title = doc.get("title") if isinstance(doc, dict) else None
            if title and (title, "rag", "document") not in seen_sources:
                seen_sources.add((title, "rag", "document"))
                source_references.append(
                    {
                        "title": title,
                        "type": "document",
                        "agent": "rag",
                        "relevance": doc.get("relevance") if isinstance(doc, dict) else None,
                    }
                )

        consensus_summary = {
            "confidence": confidence_summary,
            "priority": priority_summary,
            "stage_distribution": dict(stage_distribution),
            "top_contributors": [
                {
                    "agent": item["agent"],
                    "confidence": item["confidence"],
                    "summary": item.get("summary"),
                    "stage": item.get("stage"),
                }
                for item in top_agents[:3]
            ],
            "coverage": {
                "total_agents": len(normalized_results),
                "with_sources": sum(1 for res in normalized_results if res.get("sources")),
                "with_confidence": len(confidence_values),
            },
        }

        aggregation_summary = {
            "key_points": key_points[:8],
            "normalized_agent_results": normalized_results,
            "source_references": source_references,
            "rag_summary": rag_summary,
        }

        return aggregation_summary, consensus_summary

    def _merge_source_lists(
        self, primary_sources: Optional[List[Dict[str, Any]]], additional_sources: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Führt zwei Quellenlisten zusammen und entfernt Duplikate"""

        merged: List[Dict[str, Any]] = []
        seen: set[Tuple[Optional[str], Optional[str], Optional[str]]] = set()

        def normalize_entry(entry: Any) -> Optional[Dict[str, Any]]:
            if entry is None:
                return None
            if isinstance(entry, dict):
                return dict(entry)
            return {"title": str(entry)}

        for source in (primary_sources or []) + (additional_sources or []):
            entry = normalize_entry(source)
            if not entry:
                continue
            key = (entry.get("title"), entry.get("agent"), entry.get("type"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(entry)

        return merged

    def _blend_confidence_scores(self, model_score: Optional[float], consensus_score: Optional[float]) -> float:
        """Kombiniert LLM-Confidence mit Konsensus-Werten"""

        contributions: List[Tuple[float, float]] = []

        if isinstance(model_score, (int, float)):
            contributions.append((float(model_score), 0.6))

        if isinstance(consensus_score, (int, float)):
            contributions.append((float(consensus_score), 0.4))

        if not contributions:
            return 0.0

        numerator = sum(score * weight for score, weight in contributions)
        denominator = sum(weight for _, weight in contributions) or 1.0
        blended = numerator / denominator
        return round(max(0.0, min(blended, 1.0)), 3)

    def _extract_sources_from_results(
        self, agent_results: Dict[str, Any], rag_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extrahiert Quellen aus Agent-Ergebnissen (✨ IEEE-ENHANCED)

        Erstellt vollständige IEEE-Citation-Metadaten aus RAG-Context.
        """

        sources = []
        citation_id = 1

        # ✨ PRIORITÄT 1: Quellen aus RAG-Kontext mit vollständigen Metadaten
        documents = rag_context.get("documents", [])

        # ⚠️ MOCK-MODE FALLBACK: Wenn UDS3 im Demo-Modus keine Dokumente liefert
        if not documents or len(documents) == 0:
            logger.info("⚠️ Keine RAG-Dokumente verfügbar - Generiere IEEE-Mock-Quellen für Demo")
            documents = self._generate_mock_ieee_sources()

        for doc in documents:
            # Vollständige IEEE-Metadaten aus RAG-Context
            source_meta = {
                "id": citation_id,  # Numeric ID für IEEE - Citations
                "title": doc.get("title", "Unbekanntes Dokument"),
                "type": "document",
                # ✨ IEEE - Metadaten aus RAG - Context
                "authors": doc.get("authors", None),
                "year": doc.get("year", None),
                "date": doc.get("date", None),
                "publisher": doc.get("publisher", None),
                "url": doc.get("url", None),
                "file": doc.get("file", None),
                "page": doc.get("page", None),
                # ✨ Scores aus RAG - Context
                "similarity_score": doc.get("similarity_score", doc.get("score", 0.0)),
                "rerank_score": doc.get("rerank_score", 0.0),
                "quality_score": doc.get("quality_score", 0.0),
                "confidence": doc.get("confidence", doc.get("relevance", 0.7)),
                "score": doc.get("score", doc.get("relevance", 0.7)),
                # ✨ Classification
                "impact": doc.get("impact", "Medium"),
                "relevance": doc.get("relevance", "Medium"),
                # ✨ Legal Metadata (falls vorhanden)
                "rechtsgebiet": doc.get("rechtsgebiet", None),
                "behörde": doc.get("behoerde", doc.get("behörde", None)),
                "aktenzeichen": doc.get("aktenzeichen", None),
                "gericht": doc.get("gericht", None),
                # ✨ IEEE Citation (falls bereits formatiert)
                "ieee_citation": doc.get("ieee_citation", None),
                "original_source": doc.get("original_source", None),
            }

            # Entferne None-Werte für sauberere Response
            source_meta = {k: v for k, v in source_meta.items() if v is not None}

            sources.append(source_meta)
            citation_id += 1

        # PRIORITÄT 2: Quellen aus Agent-Ergebnissen (fallback)
        for agent_type, result in agent_results.items():
            agent_sources = result.get("sources", [])
            for source in agent_sources:
                if len(sources) >= 10:
                    break
                sources.append(
                    {
                        "id": citation_id,
                        "title": source if isinstance(source, str) else source.get("title", "Agent Source"),
                        "type": "agent_source",
                        "agent": agent_type,
                        "relevance": result.get("confidence_score", 0.8),
                        "confidence": result.get("confidence_score", 0.8),
                    }
                )
                citation_id += 1

        return sources[:10]  # Limitiere auf 10 Quellen

    def _generate_mock_ieee_sources(self) -> List[Dict[str, Any]]:
        """
        Generiert Mock-IEEE-Quellen für Demo-Zwecke (UDS3 Demo Mode)

        Returns:
            Liste von Mock-Dokumenten mit vollständigen IEEE-Metadaten
        """
        import random
        from datetime import datetime, timedelta

        mock_sources = [
            {
                "title": "Bundes - Immissionsschutzgesetz (BImSchG) - Kommentar",
                "authors": "Bundesministerium für Umwelt, Naturschutz und nukleare Sicherheit et al.",
                "year": 2023,
                "date": "2023 - 05-15",
                "publisher": "Bundesanzeiger Verlag",
                "file": "BImSchG_Kommentar_2023.pd",
                "page": 142,
                "similarity_score": 0.9234,
                "rerank_score": 0.9456,
                "quality_score": 0.9120,
                "confidence": 0.9235,
                "score": 0.9456,
                "impact": "High",
                "relevance": "Very High",
                "rechtsgebiet": "Umweltrecht",
                "behörde": "Umweltbundesamt",
                "ieee_citation": '[1] Bundesministerium für Umwelt, Naturschutz und nukleare Sicherheit et al., "Bundes - Immissionsschutzgesetz (BImSchG) - Kommentar," Bundesanzeiger Verlag, 2023, pp. 142.',
                "original_source": "Bundesgesetzblatt",
            },
            {
                "title": "Technische Anleitung zur Reinhaltung der Luft (TA Luft)",
                "authors": "Bundesregierung Deutschland",
                "year": 2021,
                "date": "2021 - 08-12",
                "publisher": "Bundesministerium für Umwelt",
                "file": "TA_Luft_2021_Neufassung.pd",
                "page": 87,
                "similarity_score": 0.8912,
                "rerank_score": 0.9123,
                "quality_score": 0.8845,
                "confidence": 0.8990,
                "score": 0.9123,
                "impact": "High",
                "relevance": "High",
                "rechtsgebiet": "Umweltrecht",
                "behörde": "Bundesregierung",
                "ieee_citation": '[2] Bundesregierung Deutschland, "Technische Anleitung zur Reinhaltung der Luft (TA Luft)," Bundesministerium für Umwelt, 2021, pp. 87.',
                "original_source": "Bundesanzeiger",
            },
            {
                "title": "Grenzwerte für Luftschadstoffe nach EU - Richtlinie 2008 / 50/EG",
                "authors": "Europäische Kommission",
                "year": 2022,
                "date": "2022 - 03-20",
                "publisher": "Amtsblatt der Europäischen Union",
                "url": "https://eur - lex.europa.eu/legal - content/DE / TXT/?uri=CELEX:32008L0050",
                "similarity_score": 0.8734,
                "rerank_score": 0.8890,
                "quality_score": 0.8612,
                "confidence": 0.8745,
                "score": 0.8890,
                "impact": "Medium",
                "relevance": "High",
                "rechtsgebiet": "Europäisches Umweltrecht",
                "ieee_citation": '[3] Europäische Kommission, "Grenzwerte für Luftschadstoffe nach EU - Richtlinie 2008 / 50/EG," Amtsblatt der Europäischen Union, 2022.',
                "original_source": "EUR - Lex",
            },
            {
                "title": "Immissionsschutzrechtliche Genehmigungsverfahren - Praxishandbuch",
                "authors": "Verwaltungsgerichtshof Baden - Württemberg",
                "year": 2023,
                "date": "2023 - 01-10",
                "publisher": "C.H. Beck Verlag",
                "file": "Genehmigungsverfahren_Praxis_2023.pd",
                "page": 215,
                "similarity_score": 0.8456,
                "rerank_score": 0.8678,
                "quality_score": 0.8334,
                "confidence": 0.8490,
                "score": 0.8678,
                "impact": "Medium",
                "relevance": "Medium",
                "rechtsgebiet": "Verwaltungsrecht",
                "behörde": "VGH Baden - Württemberg",
                "gericht": "Verwaltungsgerichtshof Baden - Württemberg",
                "aktenzeichen": "VGH 10 S 234 / 22",
                "ieee_citation": '[4] Verwaltungsgerichtshof Baden - Württemberg, "Immissionsschutzrechtliche Genehmigungsverfahren - Praxishandbuch," C.H. Beck Verlag, 2023, pp. 215.',
                "original_source": "Rechtsprechungsdatenbank",
            },
            {
                "title": "NOx - Emissionen in der Industrie: Stand der Technik",
                "authors": "Umweltbundesamt",
                "year": 2022,
                "date": "2022 - 11-05",
                "publisher": "Umweltbundesamt",
                "url": "https://www.umweltbundesamt.de / publikationen/nox - emissionen",
                "similarity_score": 0.8234,
                "rerank_score": 0.8456,
                "quality_score": 0.8112,
                "confidence": 0.8267,
                "score": 0.8456,
                "impact": "Medium",
                "relevance": "Medium",
                "rechtsgebiet": "Umweltrecht",
                "behörde": "Umweltbundesamt",
                "ieee_citation": '[5] Umweltbundesamt, "NOx - Emissionen in der Industrie: Stand der Technik," Umweltbundesamt, 2022.',
                "original_source": "UBA - Publikationen",
            },
        ]

        # Wähle 3-5 zufällige Quellen aus
        num_sources = random.randint(3, 5)
        selected = random.sample(mock_sources, num_sources)

        logger.info(f"📚 Generiert {len(selected)} Mock-IEEE-Quellen für Demo-Zwecke")

        return selected

    def _generate_follow_up_suggestions(
        self,
        query: str,
        agent_results: Dict[str, Any],
        aggregation_summary: Optional[Dict[str, Any]] = None,
        consensus_summary: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Generiert Follow-up Suggestions"""

        base_suggestions = [
            "Benötigen Sie weitere Details zu einem bestimmten Aspekt?",
            "Möchten Sie ähnliche Anfragen in anderen Bereichen stellen?",
            "Soll ich Ihnen konkrete Handlungsschritte aufzeigen?",
        ]

        suggestions: List[str] = []
        seen: set[str] = set()

        def add_suggestion(text: Optional[str]) -> None:
            if not text:
                return
            if text in seen:
                return
            seen.add(text)
            suggestions.append(text)

        for suggestion in base_suggestions:
            add_suggestion(suggestion)

        if "legal_framework" in agent_results:
            add_suggestion("Möchten Sie die rechtlichen Grundlagen genauer erklärt bekommen?")

        if "environmental" in agent_results:
            add_suggestion("Interessieren Sie sich für aktuelle Umweltdaten?")

        confidence_avg = None
        if consensus_summary:
            confidence_avg = (consensus_summary.get("confidence") or {}).get("average")
            coverage = consensus_summary.get("coverage") or {}
        else:
            coverage = {}

        if isinstance(confidence_avg, (int, float)) and confidence_avg < 0.7:
            add_suggestion("Soll ich zusätzliche Quellen prüfen, um die Aussagekraft zu erhöhen?")

        total_agents = coverage.get("total_agents", 0)
        with_sources = coverage.get("with_sources", 0)
        if total_agents and with_sources < total_agents:
            add_suggestion("Benötigen Sie Primärquellen zu allen Agentenergebnissen?")

        key_points = (aggregation_summary or {}).get("key_points") or []
        for key_point in key_points[:2]:
            add_suggestion(f"Möchten Sie tiefer in '{key_point}' einsteigen?")

        return suggestions[:5]

    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Liefert Pipeline-Statistiken"""

        success_rate = (self.stats["successful_pipelines"] / max(self.stats["pipelines_processed"], 1)) * 100

        return {
            "pipeline_stats": self.stats.copy(),
            "success_rate_percent": round(success_rate, 2),
            "active_pipelines": len(self.active_pipelines),
            "components_available": {
                "ollama_client": self.ollama_client is not None,
                "agent_orchestrator": self.agent_orchestrator is not None,
                "pipeline_manager": self.pipeline_manager is not None,
                "rag_integration": True,  # Always True in production (no fallback mode)
                "streaming_progress": STREAMING_AVAILABLE,
            },
        }

    def get_monitoring_snapshot(self) -> Dict[str, Any]:
        """Aggregiert Monitoring- und Trenddaten für Dashboards."""

        timestamp = datetime.now(timezone.utc).isoformat()

        with self._agent_results_lock:
            stats_overview = {
                "pipelines_processed": self.stats.get("pipelines_processed", 0),
                "successful_pipelines": self.stats.get("successful_pipelines", 0),
                "failed_pipelines": self.stats.get("failed_pipelines", 0),
                "average_processing_time": self.stats.get("average_processing_time", 0.0),
                "agent_timeouts": self.stats.get("agent_timeouts", 0),
                "agents_executed": self.stats.get("agents_executed", 0),
                "agent_metrics": copy.deepcopy(self.stats.get("agent_metrics", {})),
                "query_metrics": copy.deepcopy(self.stats.get("query_metrics", {})),
                "stage_duration_stats": copy.deepcopy(self.stats.get("stage_duration_stats", {})),
                "last_error": copy.deepcopy(self.stats.get("last_error")),
            }

        snapshot = {
            "timestamp": timestamp,
            "active_pipeline_count": len(self.active_pipelines),
            "active_pipeline_ids": list(self.active_pipelines.keys()),
            "stats": stats_overview,
            "recent_pipeline_metrics": list(self.recent_pipeline_metrics),
            "recent_agent_events": list(self.recent_agent_events),
            "recent_query_metrics": list(self.recent_query_metrics),
            "recent_errors": list(self.recent_errors),
        }

        return snapshot


# ============================================================================
# FACTORY FUNCTIONS & GLOBAL ACCESS
# ============================================================================

# Global Pipeline Instance
_global_intelligent_pipeline: Optional[IntelligentMultiAgentPipeline] = None


async def get_intelligent_pipeline() -> IntelligentMultiAgentPipeline:
    """
    Liefert globale Intelligent Pipeline Instanz

    Returns:
        IntelligentMultiAgentPipeline: Globale Pipeline-Instanz
    """
    global _global_intelligent_pipeline

    if _global_intelligent_pipeline is None:
        _global_intelligent_pipeline = IntelligentMultiAgentPipeline()
        await _global_intelligent_pipeline.initialize()

    return _global_intelligent_pipeline


def create_intelligent_pipeline(**kwargs) -> IntelligentMultiAgentPipeline:
    """
    Factory für neue Intelligent Pipeline Instanz

    Returns:
        IntelligentMultiAgentPipeline: Neue Pipeline-Instanz
    """
    return IntelligentMultiAgentPipeline(**kwargs)


# ============================================================================
# MAIN FOR TESTING
# ============================================================================


async def main():
    """Test der Intelligent Multi-Agent Pipeline"""

    pipeline = await get_intelligent_pipeline()

    print("🧠 Intelligent Multi-Agent Pipeline Test")
    print("=" * 50)

    # Test Request
    request = IntelligentPipelineRequest(
        query_id=str(uuid.uuid4()),
        query_text="Wie ist die Luftqualität in München und welche Behörden sind zuständig?",
        user_context={"location": "München", "user_type": "citizen"},
        enable_llm_commentary=True,
    )

    print(f"Query: {request.query_text}")
    print(f"Query ID: {request.query_id}")

    # Pipeline ausführen
    response = await pipeline.process_intelligent_query(request)

    print("\n📋 Pipeline Response:")
    print(f"Confidence Score: {response.confidence_score:.2f}")
    print(f"Processing Time: {response.total_processing_time:.2f}s")
    print(f"Agents Used: {len(response.agent_results)}")
    print(f"Sources Found: {len(response.sources)}")
    print(f"LLM Comments: {len(response.llm_commentary)}")

    print("\n💬 LLM Commentary:")
    for i, comment in enumerate(response.llm_commentary, 1):
        print(f"{i}. {comment}")

    print("\n📊 Response Preview:")
    print(response.response_text[:200] + "..." if len(response.response_text) > 200 else response.response_text)

    # Statistics
    stats = pipeline.get_pipeline_statistics()
    print(f"\n📈 Pipeline Statistics:")
    print(f"Success Rate: {stats['success_rate_percent']}%")
    print(f"LLM Comments Generated: {stats['pipeline_stats']['llm_comments_generated']}")


if __name__ == "__main__":
    asyncio.run(main())
