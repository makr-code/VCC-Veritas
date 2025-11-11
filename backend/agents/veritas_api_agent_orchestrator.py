#!/usr/bin/env python3
"""
VERITAS AGENT ORCHESTRATOR
==========================

Query-basierter Orchestrator mit In-Memory Agent-Management

ARCHITEKTUR:
- In-Memory Query-Orchestrator ohne Database-Dependencies
- JSON-Schema-basierte Agent-Pipeline-Definition
- Direkte AgentCoordinator-Integration
- Dynamic Agent-Selection für Query-Processing
- Vereinfachte Schema-Verwaltung

Author: VERITAS System (Based on ingestion_core_orchestrator.py)
Date: 2025-09-21
Version: 1.0 (Query-driven)
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from queue import Queue
from typing import Any, Dict, List, Optional, Sequence, Tuple, cast

# Shared Enums
from backend.agents.veritas_shared_enums import QueryComplexity, QueryDomain, QueryStatus

# Agent Pipeline Manager Integration
try:
    from backend.agents.veritas_api_agent_pipeline_manager import AgentPipelineManager, get_agent_pipeline_db

    AGENT_PIPELINE_AVAILABLE = True
except ImportError:
    AGENT_PIPELINE_AVAILABLE = False
    logging.warning("⚠️ Agent Pipeline Manager nicht verfügbar")

# Agent Registry Integration
try:
    from backend.agents.veritas_api_agent_registry import AgentCapability, get_agent_registry

    AGENT_REGISTRY_AVAILABLE = True
except ImportError:
    AGENT_REGISTRY_AVAILABLE = False
    logging.warning("⚠️ Agent Registry nicht verfügbar")

# Database Agent Integration
try:
    from backend.agents.veritas_api_agent_database import (
        DatabaseAgent,
        DatabaseConfig,
        DatabaseQueryRequest,
        DatabaseQueryResponse,
        create_database_agent,
    )

    DATABASE_AGENT_AVAILABLE = True
except ImportError:
    DATABASE_AGENT_AVAILABLE = False
    logging.warning("⚠️ Database Agent nicht verfügbar")

# RAG Integration
try:
    from database.database_api import MultiDatabaseAPI
    from uds3.core import UDS3PolyglotManager  # ✨ UDS3 v2.0.0 (Legacy stable)

    RAG_INTEGRATION_AVAILABLE = True
except ImportError:
    RAG_INTEGRATION_AVAILABLE = False
    logging.info("ℹ️ RAG Integration läuft im Mock-Modus (optional)")

logger = logging.getLogger(__name__)


@dataclass
class AgentPipelineTask:
    """Einzelner Task in der Agent-Pipeline"""

    task_id: str
    task_type: str
    agent_type: str
    capability: str
    priority: float
    status: str = "pending"
    depends_on: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryPipeline:
    """Pipeline für eine einzelne Query"""

    pipeline_id: str
    query_id: str
    query_text: str
    schema_name: str
    tasks: Dict[str, AgentPipelineTask] = field(default_factory=dict)
    task_order: List[str] = field(default_factory=list)
    status: str = "active"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_tasks: List[str] = field(default_factory=list)
    complexity: QueryComplexity = QueryComplexity.STANDARD
    domain: QueryDomain = QueryDomain.ENVIRONMENTAL


class AgentOrchestrator:
    """
    Query-basierter Orchestrator - Agent Pipeline Management

    VEREINFACHTE ARCHITEKTUR:
    - In-Memory Pipeline-Verwaltung
    - Schema-basierte Agent-Task-Erstellung
    - Direkte AgentPipelineManager-Integration
    - AgentCoordinator-Kopplung für Agent-Dispatch
    """

    DYNAMIC_AGENT_TASK_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
        "authority_mapping": {
            "stage": "integration",
            "capability": "authority_mapping",
            "priority": 0.8,
            "parallel": False,
            "depends_on": ["domain_agent", "primary_domain_agent"],
        },
        "quality_assessor": {
            "stage": "response_generation",
            "capability": "quality_assessment",
            "priority": 0.75,
            "parallel": False,
            "depends_on": ["response_aggregator", "response_synthesizer"],
        },
        "environmental": {
            "stage": "domain_processing",
            "capability": "domain_specific_processing",
            "priority": 0.85,
            "parallel": True,
            "depends_on": ["legal_framework", "geo_context"],
        },
        "financial": {
            "stage": "domain_processing",
            "capability": "domain_specific_processing",
            "priority": 0.8,
            "parallel": True,
            "depends_on": ["legal_framework"],
        },
        "transport": {
            "stage": "domain_processing",
            "capability": "domain_specific_processing",
            "priority": 0.8,
            "parallel": True,
            "depends_on": ["geo_context"],
        },
        "health": {
            "stage": "domain_processing",
            "capability": "domain_specific_processing",
            "priority": 0.78,
            "parallel": True,
            "depends_on": ["legal_framework"],
        },
        "database": {
            "stage": "data_retrieval",
            "capability": "database_query",
            "priority": 0.85,
            "parallel": True,
            "depends_on": [],  # Kann unabhängig laufen
        },
    }

    def __init__(self, schema_dir: str = None, agent_coordinator=None, pipeline_manager=None):
        """
        Initialisiert den Agent-Orchestrator

        Args:
            schema_dir: Verzeichnis für Agent-Pipeline-Schema-Dateien
            agent_coordinator: AgentCoordinator-Instanz für Agent-Dispatch
            pipeline_manager: Shared AgentPipelineManager-Instanz
        """
        self.schema_dir = schema_dir or os.path.join(os.path.dirname(__file__), "agent_pipeline_schemas")
        self.agent_coordinator = agent_coordinator

        # In-Memory Storage
        self.pipelines: Dict[str, QueryPipeline] = {}
        self.pipeline_lock = threading.RLock()

        # Schema Cache
        self.schema_cache: Dict[str, Dict[str, Any]] = {}
        self.schema_lock = threading.RLock()

        # Agent Pipeline Manager Integration
        if AGENT_PIPELINE_AVAILABLE:
            self.pipeline_manager = pipeline_manager or get_agent_pipeline_db()
        else:
            self.pipeline_manager = None

        # Agent Registry Integration
        if AGENT_REGISTRY_AVAILABLE:
            self.agent_registry = get_agent_registry()
        else:
            self.agent_registry = None

        # RAG Integration
        if RAG_INTEGRATION_AVAILABLE:
            try:
                self.database_api = MultiDatabaseAPI()
                # ✨ NEU: UDS3 v2.0.0 Polyglot Manager
                backend_config = {
                    "vector": {"enabled": True, "backend": "chromadb"},
                    "graph": {"enabled": False},
                    "relational": {"enabled": False},
                    "file_storage": {"enabled": False},
                }
                self.uds3_strategy = UDS3PolyglotManager(backend_config=backend_config, enable_rag=True)
                logger.info("[OK] UDS3 Polyglot Manager initialisiert (Agent Orchestrator)")
            except Exception as e:
                logger.warning(f"⚠️ RAG Integration Fehler: {e}")
                self.database_api = None
                self.uds3_strategy = None
        else:
            self.database_api = None
            self.uds3_strategy = None

        # Database Agent Integration
        if DATABASE_AGENT_AVAILABLE:
            try:
                self.database_agent = create_database_agent()
                logger.info("[OK] Database Agent initialisiert (Read-Only Mode)")
            except Exception as e:
                logger.warning(f"⚠️ Database Agent Initialisierung fehlgeschlagen: {e}")
                self.database_agent = None
        else:
            self.database_agent = None

        # Monitoring
        self.orchestration_active = False
        self.orchestration_thread = None
        self.monitoring_thread = None

        # Statistics
        self.stats = {
            "pipelines_created": 0,
            "pipelines_completed": 0,
            "tasks_created": 0,
            "tasks_completed": 0,
            "active_pipelines": 0,
            "total_processing_time": 0.0,
        }

        # Agent-Pipeline-Schema laden
        self._load_agent_pipeline_schemas()

        logger.info("🎯 Agent Orchestrator initialisiert")

    def set_agent_coordinator(self, agent_coordinator):
        """Setzt AgentCoordinator-Referenz für Agent-Pipeline"""
        self.agent_coordinator = agent_coordinator
        logger.info("🔗 AgentCoordinator mit Orchestrator verknüpft")

    def _load_agent_pipeline_schemas(self):
        """Lädt Agent-Pipeline-Schemas aus JSON-Dateien"""
        schema_dir = Path(self.schema_dir)

        if not schema_dir.exists():
            logger.info(f"ℹ️ Schema-Verzeichnis nicht gefunden, verwende Standard-Schemas: {schema_dir}")
            self._create_default_agent_schemas()
            return

        try:
            schema_files = list(schema_dir.glob("*.json"))

            with self.schema_lock:
                for schema_file in schema_files:
                    with open(schema_file, "r", encoding="utf-8") as f:
                        schema = json.load(f)
                        schema_name = schema_file.stem
                        self.schema_cache[schema_name] = schema

                        logger.debug(f"📋 Agent Schema geladen: {schema_name}")

            logger.info(f"[OK] {len(self.schema_cache)} Agent Pipeline Schemas geladen")

        except Exception as e:
            logger.error(f"❌ Agent Schema-Laden fehlgeschlagen: {e}")
            self._create_default_agent_schemas()

    def _create_default_agent_schemas(self):
        """Erstellt Standard-Agent-Pipeline-Schemas basierend auf hypothetischen Query-Analysen"""
        logger.info("🔧 Erstelle Standard-Agent-Pipeline-Schemas...")

        # Schema für BASIC Queries (🟢 Basic: Einfache Kontext-Anreicherung)
        basic_schema = {
            "schema_name": "basic_query_pipeline",
            "description": "Einfache Queries mit Geo + Zeit Kontext",
            "complexity": "basic",
            "stages": [
                {
                    "stage": "context_resolution",
                    "tasks": [
                        {
                            "task_id": "geo_context",
                            "agent_type": "geo_context",
                            "capability": "geo_context_resolution",
                            "priority": 1.0,
                            "parallel": False,
                        },
                        {
                            "task_id": "temporal_analysis",
                            "agent_type": "temporal_analyzer",
                            "capability": "temporal_analysis",
                            "priority": 0.8,
                            "parallel": True,
                        },
                    ],
                },
                {
                    "stage": "response_generation",
                    "tasks": [
                        {
                            "task_id": "response_generator",
                            "agent_type": "response_generator",
                            "capability": "structured_response_generation",
                            "priority": 1.0,
                            "depends_on": ["geo_context", "temporal_analysis"],
                        }
                    ],
                },
            ],
        }

        # Schema für STANDARD Queries (🟡 Standard: Multi-Domain + externe Datenquellen)
        standard_schema = {
            "schema_name": "standard_query_pipeline",
            "description": "Multi - Domain Queries mit externen Datenquellen",
            "complexity": "standard",
            "stages": [
                {
                    "stage": "preprocessing",
                    "tasks": [
                        {
                            "task_id": "query_analyzer",
                            "agent_type": "query_preprocessor",
                            "capability": "domain_classification",
                            "priority": 1.0,
                        }
                    ],
                },
                {
                    "stage": "context_resolution",
                    "tasks": [
                        {
                            "task_id": "geo_context",
                            "agent_type": "geo_context",
                            "capability": "geo_context_resolution",
                            "priority": 1.0,
                            "depends_on": ["query_analyzer"],
                        },
                        {
                            "task_id": "legal_framework",
                            "agent_type": "legal_framework",
                            "capability": "legal_framework_analysis",
                            "priority": 0.9,
                            "depends_on": ["query_analyzer"],
                        },
                    ],
                },
                {
                    "stage": "domain_processing",
                    "tasks": [
                        {
                            "task_id": "domain_agent",
                            "agent_type": "dynamic",  # Wird zur Laufzeit bestimmt
                            "capability": "domain_specific_processing",
                            "priority": 1.0,
                            "depends_on": ["geo_context", "legal_framework"],
                        },
                        {
                            "task_id": "document_retrieval",
                            "agent_type": "document_retrieval",
                            "capability": "document_retrieval",
                            "priority": 0.8,
                            "parallel": True,
                        },
                    ],
                },
                {
                    "stage": "integration",
                    "tasks": [
                        {
                            "task_id": "external_api",
                            "agent_type": "external_api",
                            "capability": "external_api_integration",
                            "priority": 0.7,
                            "depends_on": ["domain_agent"],
                        }
                    ],
                },
                {
                    "stage": "response_generation",
                    "tasks": [
                        {
                            "task_id": "response_aggregator",
                            "agent_type": "response_aggregator",
                            "capability": "structured_response_generation",
                            "priority": 1.0,
                            "depends_on": ["domain_agent", "document_retrieval", "external_api"],
                        }
                    ],
                },
            ],
        }

        # Schema für ADVANCED Queries (🔴 Advanced: Complex Reasoning + Multi-Step-Analysis)
        advanced_schema = {
            "schema_name": "advanced_query_pipeline",
            "description": "Komplexe Queries mit Multi - Step-Analysis",
            "complexity": "advanced",
            "stages": [
                {
                    "stage": "preprocessing",
                    "tasks": [
                        {
                            "task_id": "query_analyzer",
                            "agent_type": "query_preprocessor",
                            "capability": "domain_classification",
                            "priority": 1.0,
                        },
                        {
                            "task_id": "complexity_analyzer",
                            "agent_type": "complexity_analyzer",
                            "capability": "impact_assessment",
                            "priority": 0.9,
                            "depends_on": ["query_analyzer"],
                        },
                    ],
                },
                {
                    "stage": "context_resolution",
                    "tasks": [
                        {
                            "task_id": "geo_context",
                            "agent_type": "geo_context",
                            "capability": "geo_context_resolution",
                            "priority": 1.0,
                            "depends_on": ["complexity_analyzer"],
                        },
                        {
                            "task_id": "legal_framework",
                            "agent_type": "legal_framework",
                            "capability": "legal_framework_analysis",
                            "priority": 1.0,
                            "depends_on": ["complexity_analyzer"],
                        },
                        {
                            "task_id": "temporal_analysis",
                            "agent_type": "temporal_analyzer",
                            "capability": "temporal_analysis",
                            "priority": 0.8,
                            "parallel": True,
                        },
                    ],
                },
                {
                    "stage": "domain_processing",
                    "tasks": [
                        {
                            "task_id": "primary_domain_agent",
                            "agent_type": "dynamic",
                            "capability": "domain_specific_processing",
                            "priority": 1.0,
                            "depends_on": ["geo_context", "legal_framework"],
                        },
                        {
                            "task_id": "secondary_domain_agent",
                            "agent_type": "dynamic",
                            "capability": "domain_specific_processing",
                            "priority": 0.8,
                            "depends_on": ["geo_context", "legal_framework"],
                        },
                        {
                            "task_id": "document_retrieval",
                            "agent_type": "document_retrieval",
                            "capability": "document_retrieval",
                            "priority": 0.9,
                            "parallel": True,
                        },
                    ],
                },
                {
                    "stage": "analysis",
                    "tasks": [
                        {
                            "task_id": "financial_impact",
                            "agent_type": "financial_analyzer",
                            "capability": "financial_impact_analysis",
                            "priority": 0.8,
                            "depends_on": ["primary_domain_agent", "secondary_domain_agent"],
                        },
                        {
                            "task_id": "success_probability",
                            "agent_type": "success_estimator",
                            "capability": "success_probability_estimation",
                            "priority": 0.7,
                            "depends_on": ["primary_domain_agent", "legal_framework"],
                        },
                        {
                            "task_id": "external_api",
                            "agent_type": "external_api",
                            "capability": "multi_source_synthesis",
                            "priority": 0.6,
                            "depends_on": ["primary_domain_agent"],
                        },
                    ],
                },
                {
                    "stage": "response_generation",
                    "tasks": [
                        {
                            "task_id": "response_synthesizer",
                            "agent_type": "response_synthesizer",
                            "capability": "structured_response_generation",
                            "priority": 1.0,
                            "depends_on": ["financial_impact", "success_probability", "external_api", "document_retrieval"],
                        },
                        {
                            "task_id": "action_planner",
                            "agent_type": "action_planner",
                            "capability": "action_planning",
                            "priority": 0.9,
                            "depends_on": ["response_synthesizer"],
                        },
                    ],
                },
            ],
        }

        # Schemas in Cache speichern
        with self.schema_lock:
            self.schema_cache["basic_query_pipeline"] = basic_schema
            self.schema_cache["standard_query_pipeline"] = standard_schema
            self.schema_cache["advanced_query_pipeline"] = advanced_schema

    logger.info("[OK] Standard-Agent-Pipeline-Schemas erstellt")

    def preprocess_query(self, query_data: Dict[str, Any], rag_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Preprocessing einer Query - Analyse und Agent-Selektion

        Args:
            query_data: Query-Daten (query, user_context, etc.)
            rag_context: Optionaler vorliegender RAG-Kontext (vector/graph/relational)

        Returns:
            Dict: Preprocessing-Ergebnis mit required_agents, complexity, etc.
        """

        query_text = query_data.get("query", "")
        # user_context currently not used here; keep for future use if needed
        # (intentionally not assigned to avoid unused-variable lint)
        # user_context = query_data.get("user_context", {})
        rag_context = rag_context or query_data.get("rag_context") or {}

        # Einfache Query-Analyse (in Realität würde hier ML/NLP verwendet)
        complexity = self._analyze_query_complexity(query_text)
        domain = self._analyze_query_domain(query_text)
        required_capabilities = self._analyze_required_capabilities(query_text, complexity)

        # Schema-basierte Agent-Pipeline-Erstellung
        schema_name = self._select_pipeline_schema(complexity, domain)
        pipeline_id = self._create_query_pipeline(query_data, schema_name, complexity, domain)
        agent_priority_map, rag_signals, dynamic_actions = self._apply_rag_context_to_pipeline(
            pipeline_id, rag_context, complexity, domain
        )
        priority_sorted_agents = (
            [agent for agent, _ in sorted(agent_priority_map.items(), key=lambda item: item[1], reverse=True)]
            if agent_priority_map
            else None
        )

        preprocessing_result = {
            "pipeline_id": pipeline_id,
            "complexity": complexity.value,
            "domain": domain.value,
            "schema_name": schema_name,
            "required_capabilities": [cap.value for cap in required_capabilities],
            "required_agents": priority_sorted_agents or self._extract_agent_types_from_pipeline(pipeline_id),
            "estimated_processing_time": self._estimate_processing_time(complexity, len(required_capabilities)),
            "processing_stages": self._get_pipeline_stages(pipeline_id),
            "agent_priority_map": agent_priority_map,
            "rag_signals": rag_signals,
            "dynamic_actions": dynamic_actions,
        }

        agents = cast(Sequence[Any], preprocessing_result.get("required_agents") or [])
        agents_count = len(agents)
        logger.info(f"🔍 Query Preprocessing abgeschlossen: {complexity.value}/{domain.value} - {agents_count} Agents")

        return preprocessing_result

    def _analyze_query_complexity(self, query_text: str) -> QueryComplexity:
        """Analysiert Query-Komplexität basierend auf Textinhalt"""

        query_lower = query_text.lower()

        # Komplexitäts-Indikatoren
        advanced_indicators = [
            "vergleichen",
            "analysieren",
            "bewerten",
            "optimieren",
            "kombinieren",
            "wahrscheinlichkeit",
            "risiko",
            "auswirkung",
            "alternative",
            "strategie",
            "mehrere",
            "verschiedene",
            "komplex",
            "detailliert",
        ]

        standard_indicators = [
            "wie",
            "welche",
            "wo",
            "wann",
            "genehmigung",
            "kosten",
            "verfahren",
            "zuständig",
            "berechtigt",
            "antrag",
            "frist",
            "voraussetzung",
        ]

        # Scoring
        advanced_score = sum(1 for indicator in advanced_indicators if indicator in query_lower)
        standard_score = sum(1 for indicator in standard_indicators if indicator in query_lower)

        if advanced_score >= 2 or len(query_text.split()) > 20:
            return QueryComplexity.ADVANCED
        elif standard_score >= 2 or len(query_text.split()) > 10:
            return QueryComplexity.STANDARD
        else:
            return QueryComplexity.BASIC

    def _analyze_query_domain(self, query_text: str) -> QueryDomain:
        """Analysiert Query-Domain basierend auf Keywords"""

        query_lower = query_text.lower()

        # Domain-Keyword-Mapping (basierend auf hypothetischen Query-Analysen)
        domain_keywords = {
            QueryDomain.ENVIRONMENTAL: ["geruch", "lärm", "luft", "umwelt", "emissionen", "verschmutzung", "qualität"],
            QueryDomain.BUILDING: ["bau", "genehmigung", "planung", "bebauung", "sanierung", "denkmal", "gebäude"],
            QueryDomain.TRANSPORT: ["verkehr", "parken", "öpnv", "bus", "bahn", "fahrrad", "straße"],
            QueryDomain.SOCIAL: ["kita", "pflege", "sozial", "kranken", "gesundheit", "betreuung", "hilfe"],
            QueryDomain.BUSINESS: ["gewerbe", "geschäft", "laden", "gaststätte", "betrieb", "unternehmen"],
            QueryDomain.TAXATION: ["steuer", "gebühr", "abgabe", "finanz", "förder", "unterstützung"],
            QueryDomain.CIVIC_ENGAGEMENT: ["bürger", "wahl", "beteiligung", "antrag", "beschwerde", "petition"],
            QueryDomain.SECURITY: ["sicherheit", "ordnung", "polizei", "feuerwehr", "notru", "gefahr"],
            QueryDomain.HEALTH: ["arzt", "krankenhaus", "impf", "medizin", "therapie", "behandlung"],
        }

        # Scoring pro Domain
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                domain_scores[domain] = score

        # Beste Domain zurückgeben
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        else:
            return QueryDomain.ENVIRONMENTAL  # Fallback

    def _analyze_required_capabilities(self, query_text: str, complexity: QueryComplexity) -> List[AgentCapability]:
        """Analysiert welche Agent-Capabilities benötigt werden"""

        capabilities = set()
        query_lower = query_text.lower()

        # Basis-Capabilities (immer benötigt)
        capabilities.add(AgentCapability.DOMAIN_CLASSIFICATION)

        # Geo-Context (73% der Queries)
        if any(word in query_lower for word in ["wo", "ort", "stadt", "gemeinde", "adresse", "nähe"]):
            capabilities.add(AgentCapability.GEO_CONTEXT_RESOLUTION)

        # Legal Framework (60% der Queries)
        if any(word in query_lower for word in ["recht", "gesetz", "genehmigung", "legal", "vorschrift", "regel"]):
            capabilities.add(AgentCapability.LEGAL_FRAMEWORK_ANALYSIS)

        # Temporal Analysis (37% der Queries)
        if any(word in query_lower for word in ["wann", "zeit", "dauer", "frist", "termin", "schnell"]):
            capabilities.add(AgentCapability.TEMPORAL_ANALYSIS)

        # Document Retrieval (für faktische Informationen)
        if any(word in query_lower for word in ["info", "dokument", "unterlagen", "nachweis", "bescheid"]):
            capabilities.add(AgentCapability.DOCUMENT_RETRIEVAL)

        # External API Integration (50% der Queries)
        if any(word in query_lower for word in ["aktuell", "verfügbar", "status", "preis", "öffnungszeit"]):
            capabilities.add(AgentCapability.EXTERNAL_API_INTEGRATION)

        # Financial Impact (40% der Queries)
        if any(word in query_lower for word in ["kosten", "preis", "gebühr", "förder", "finanz", "euro"]):
            capabilities.add(AgentCapability.FINANCIAL_IMPACT_ANALYSIS)

        # Action Planning (47% der Queries)
        if any(word in query_lower for word in ["wie", "antrag", "beantragen", "vorgehen", "schritte"]):
            capabilities.add(AgentCapability.ACTION_PLANNING)

        # Komplexitäts-spezifische Capabilities
        if complexity == QueryComplexity.ADVANCED:
            capabilities.add(AgentCapability.IMPACT_ASSESSMENT)
            capabilities.add(AgentCapability.SUCCESS_PROBABILITY_ESTIMATION)
            capabilities.add(AgentCapability.MULTI_SOURCE_SYNTHESIS)

        return list(capabilities)

    def _select_pipeline_schema(self, complexity: QueryComplexity, domain: QueryDomain) -> str:
        """Wählt passendes Pipeline-Schema basierend auf Komplexität und Domain"""

        if complexity == QueryComplexity.BASIC:
            return "basic_query_pipeline"
        elif complexity == QueryComplexity.STANDARD:
            return "standard_query_pipeline"
        else:
            return "advanced_query_pipeline"

    def _create_query_pipeline(
        self, query_data: Dict[str, Any], schema_name: str, complexity: QueryComplexity, domain: QueryDomain
    ) -> str:
        """Erstellt Query-Pipeline basierend auf Schema"""

        pipeline_id = f"pipeline_{domain.value}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        query_id = query_data.get("query_id", f"query_{int(time.time())}")

        with self.pipeline_lock:
            # Schema laden
            if schema_name not in self.schema_cache:
                logger.warning(f"⚠️ Unbekanntes Schema: {schema_name}")
                schema_name = "standard_query_pipeline"

            schema = self.schema_cache[schema_name]

            # Pipeline erstellen
            pipeline = QueryPipeline(
                pipeline_id=pipeline_id,
                query_id=query_id,
                query_text=query_data.get("query", ""),
                schema_name=schema_name,
                complexity=complexity,
                domain=domain,
            )

            # Tasks aus Schema erstellen
            task_counter = 0
            for stage in schema.get("stages", []):
                for task_config in stage.get("tasks", []):
                    task_counter += 1

                    # Agent-Typ bestimmen (dynamic agents zur Laufzeit)
                    agent_type = task_config["agent_type"]
                    if agent_type == "dynamic":
                        agent_type = self._resolve_dynamic_agent_type(domain, task_config["capability"])

                    task = AgentPipelineTask(
                        task_id=task_config["task_id"],
                        task_type=task_config.get("task_type", "agent_processing"),
                        agent_type=agent_type,
                        capability=task_config["capability"],
                        priority=task_config.get("priority", 1.0),
                        depends_on=task_config.get("depends_on", []),
                        metadata={
                            "stage": stage["stage"],
                            "parallel": task_config.get("parallel", False),
                            "schema_name": schema_name,
                        },
                    )

                    pipeline.tasks[task.task_id] = task
                    pipeline.task_order.append(task.task_id)

            # Pipeline registrieren
            self.pipelines[pipeline_id] = pipeline
            self.stats["pipelines_created"] += 1
            self.stats["tasks_created"] += task_counter

            logger.info(f"🏗️ Query-Pipeline erstellt: {pipeline_id} ({task_counter} Tasks)")

            return pipeline_id

    def _resolve_dynamic_agent_type(self, domain: QueryDomain, capability: str) -> str:
        """Löst dynamic agent types basierend auf Domain au"""

        # Domain-zu-Agent-Typ Mapping
        domain_agent_mapping = {
            QueryDomain.ENVIRONMENTAL: "environmental",
            QueryDomain.BUILDING: "building",
            QueryDomain.TRANSPORT: "transport",
            QueryDomain.SOCIAL: "social",
            QueryDomain.BUSINESS: "business",
            QueryDomain.TAXATION: "taxation",
            QueryDomain.CIVIC_ENGAGEMENT: "civic_engagement",
            QueryDomain.SECURITY: "security",
            QueryDomain.HEALTH: "health",
        }

        return domain_agent_mapping.get(domain, "document_retrieval")

    def _extract_agent_types_from_pipeline(self, pipeline_id: str) -> List[str]:
        """Extrahiert Agent-Typen aus Pipeline"""

        with self.pipeline_lock:
            if pipeline_id not in self.pipelines:
                return []

            pipeline = self.pipelines[pipeline_id]
            agent_types = []

            for task in pipeline.tasks.values():
                if task.agent_type not in agent_types:
                    agent_types.append(task.agent_type)

            return agent_types

    def _apply_rag_context_to_pipeline(
        self, pipeline_id: str, rag_context: Dict[str, Any], complexity: QueryComplexity, domain: QueryDomain
    ) -> Tuple[Dict[str, float], Dict[str, Any], Dict[str, List[str]]]:  # noqa: C901
        """Passt Pipeline-Prioritäten anhand des RAG-Kontexts an."""

        rag_context = rag_context or {}
        documents = rag_context.get("documents", []) or []
        vector_stats = (rag_context.get("vector", {}) or {}).get("statistics", {}) or {}
        graph_entities = rag_context.get("graph", {}).get("related_entities", []) or []
        fallback_used = bool((rag_context.get("meta", {}) or {}).get("fallback_used", False))
        tag_counter: Counter[str] = Counter()
        for doc in documents:
            tags = doc.get("domain_tags") or []
            tag_counter.update(tag.lower() for tag in tags if isinstance(tag, str))

        top_relevance = None
        if documents:
            first_doc = documents[0]
            if isinstance(first_doc, dict):
                top_relevance = first_doc.get("relevance")
            else:
                top_relevance = getattr(first_doc, "relevance", None)

        signals = {
            "document_count": len(documents),
            "vector_matches": vector_stats.get("count", 0),
            "graph_entities": graph_entities,
            "fallback_used": fallback_used,
            "top_relevance": top_relevance,
            "tags": dict(tag_counter),
        }

        priority_map: Dict[str, float] = {}

        dynamic_actions: Dict[str, List[str]] = {"added": [], "disabled": []}

        with self.pipeline_lock:
            pipeline = self.pipelines.get(pipeline_id)
            if not pipeline:
                return priority_map, signals, dynamic_actions

            agent_boost: Dict[str, float] = {}

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
                    agent_boost[agent] = agent_boost.get(agent, 0.0) + min(0.25 + 0.05 * count, 0.6)

            if signals["vector_matches"] > 0:
                agent_boost["document_retrieval"] = agent_boost.get("document_retrieval", 0.0) + min(
                    0.2 + signals["vector_matches"] * 0.02, 0.5
                )
            if graph_entities:
                agent_boost["authority_mapping"] = agent_boost.get("authority_mapping", 0.0) + 0.3
            if complexity == QueryComplexity.ADVANCED:
                agent_boost["quality_assessor"] = agent_boost.get("quality_assessor", 0.0) + 0.2
            if domain == QueryDomain.BUILDING:
                agent_boost["legal_framework"] = agent_boost.get("legal_framework", 0.0) + 0.15

            present_agents = {task.agent_type for task in pipeline.tasks.values()}

            for agent, boost in agent_boost.items():
                if boost >= 0.35 and agent not in present_agents:
                    new_task = self._create_dynamic_task(pipeline, agent, boost)
                    if new_task:
                        present_agents.add(agent)
                        priority_map[agent] = max(priority_map.get(agent, 0.0), new_task.priority)
                        dynamic_actions["added"].append(new_task.task_id)

            for task_id in list(pipeline.task_order):
                task = pipeline.tasks.get(task_id)
                if not task:
                    continue
                base_priority = task.priority or 0.5
                boost = agent_boost.get(task.agent_type, 0.0)
                adjusted_priority = round(min(base_priority + boost, 1.5), 3)
                task.priority = adjusted_priority
                if boost:
                    task.metadata["rag_boost"] = boost
                    task.metadata["rag_tags"] = list(tag_counter.keys())
                    task.metadata["rag_vector_matches"] = signals["vector_matches"]
                priority_map[task.agent_type] = max(priority_map.get(task.agent_type, 0.0), adjusted_priority)

                if adjusted_priority < 0.25 and boost == 0 and not task.metadata.get("stage", "").startswith("response"):
                    task.metadata["dynamic_skip"] = True
                    dynamic_actions["disabled"].append(task.task_id)

        return priority_map, signals, dynamic_actions

    def _create_dynamic_task(self, pipeline: QueryPipeline, agent_type: str, boost: float) -> Optional[AgentPipelineTask]:
        """Erstellt bei Bedarf einen dynamischen Task für die Pipeline."""

        blueprint = self.DYNAMIC_AGENT_TASK_BLUEPRINTS.get(agent_type)
        if not blueprint:
            return None

        task_id = f"dynamic_{agent_type}_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        depends_on = blueprint.get("depends_on", [])

        task = AgentPipelineTask(
            task_id=task_id,
            task_type="agent_processing",
            agent_type=agent_type,
            capability=blueprint.get("capability", "dynamic"),
            priority=round(min(blueprint.get("priority", 0.75) + boost, 1.5), 3),
            depends_on=depends_on,
            metadata={
                "stage": blueprint.get("stage", "domain_processing"),
                "parallel": blueprint.get("parallel", True),
                "dynamic": True,
                "rag_boost": boost,
            },
        )

        pipeline.tasks[task_id] = task
        pipeline.task_order.append(task_id)
        return task

    def _estimate_processing_time(self, complexity: QueryComplexity, capability_count: int) -> float:
        """Schätzt Verarbeitungszeit basierend auf Komplexität"""

        base_time = {QueryComplexity.BASIC: 2.0, QueryComplexity.STANDARD: 5.0, QueryComplexity.ADVANCED: 10.0}

        return base_time[complexity] + (capability_count * 0.5)

    def _get_pipeline_stages(self, pipeline_id: str) -> List[str]:
        """Holt Pipeline-Stages"""

        with self.pipeline_lock:
            if pipeline_id not in self.pipelines:
                return []

            pipeline = self.pipelines[pipeline_id]
            stages = []

            for task in pipeline.tasks.values():
                stage = task.metadata.get("stage", "unknown")
                if stage not in stages:
                    stages.append(stage)

            return stages

    def aggregate_results(self, query_data: Dict[str, Any], agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregiert Agent-Ergebnisse zu finaler Antwort

        Args:
            query_data: Ursprüngliche Query-Daten
            agent_results: Ergebnisse aller Agents

        Returns:
            Dict: Finale aggregierte Antwort
        """

        # Vertrauens-Score berechnen
        confidence_scores = [
            result.get("confidence_score", 0.0) for result in agent_results.values() if "confidence_score" in result
        ]

        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        # Hauptantwort aus besten Agent-Ergebnissen zusammenstellen
        primary_responses = []
        for agent_type, result in agent_results.items():
            if result.get("confidence_score", 0.0) > 0.7:
                response_text = result.get("response_text", "")
                if response_text:
                    primary_responses.append(f"**{agent_type.title()}**: {response_text}")

        main_response = (
            "\n\n".join(primary_responses) if primary_responses else "Keine vertrauenswürdigen Ergebnisse gefunden."
        )

        # Quellen sammeln
        sources = []
        for result in agent_results.values():
            if "sources" in result:
                sources.extend(result["sources"])

        # Follow-up Suggestions sammeln
        follow_up_suggestions = []
        for result in agent_results.values():
            if "follow_up_suggestions" in result:
                follow_up_suggestions.extend(result["follow_up_suggestions"])

        # RAG Context sammeln
        rag_context = {}
        for agent_type, result in agent_results.items():
            if "rag_context" in result:
                rag_context[agent_type] = result["rag_context"]

        aggregated_result = {
            "response_text": main_response,
            "confidence_score": overall_confidence,
            "sources": sources[:10],  # Limitiere auf 10 Quellen
            "worker_results": agent_results,  # Kompatibilität mit veritas_app.py
            "agent_results": agent_results,
            "rag_context": rag_context,
            "follow_up_suggestions": list(set(follow_up_suggestions))[:5],  # Unique, max 5
            "processing_metadata": {
                "total_agents": len(agent_results),
                "successful_agents": len([r for r in agent_results.values() if not r.get("error")]),
                "aggregation_method": "confidence_weighted",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        logger.info(f"🔗 Agent-Ergebnisse aggregiert: {len(agent_results)} Agents, Confidence: {overall_confidence:.2f}")

        return aggregated_result

    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Liefert aktuellen Orchestrator-Status"""

        with self.pipeline_lock:
            active_pipelines = [p for p in self.pipelines.values() if p.status == "active"]

            pipeline_summary = {}
            for pipeline in self.pipelines.values():
                pipeline_summary[pipeline.pipeline_id] = {
                    "query_id": pipeline.query_id,
                    "domain": pipeline.domain.value,
                    "complexity": pipeline.complexity.value,
                    "status": pipeline.status,
                    "total_tasks": len(pipeline.tasks),
                    "completed_tasks": len(pipeline.completed_tasks),
                    "schema_name": pipeline.schema_name,
                }

        return {
            "stats": self.stats.copy(),
            "active_pipelines": len(active_pipelines),
            "total_pipelines": len(self.pipelines),
            "loaded_schemas": len(self.schema_cache),
            "pipeline_summary": pipeline_summary,
            "component_status": {
                "agent_pipeline_manager": AGENT_PIPELINE_AVAILABLE,
                "agent_registry": AGENT_REGISTRY_AVAILABLE,
                "rag_integration": RAG_INTEGRATION_AVAILABLE,
            },
        }


# === FACTORY FUNCTIONS ===


def create_agent_orchestrator(schema_dir: str = None, agent_coordinator=None, pipeline_manager=None) -> AgentOrchestrator:
    """
    Factory für Agent-Orchestrator-Erstellung

    Args:
        schema_dir: Verzeichnis für Pipeline-Schema-Dateien
        agent_coordinator: AgentCoordinator-Instanz
        pipeline_manager: Agent-Pipeline-Manager

    Returns:
        AgentOrchestrator-Instanz
    """
    return AgentOrchestrator(schema_dir=schema_dir, agent_coordinator=agent_coordinator, pipeline_manager=pipeline_manager)


# === LEGACY COMPATIBILITY ===


class LegacyAgentOrchestratorWrapper:
    """Legacy-Wrapper für alte API-Kompatibilität"""

    def __init__(self, agent_orchestrator: AgentOrchestrator):
        self.agent_orchestrator = agent_orchestrator

    def process_query_with_pipeline(self, query: str, complexity: str = "standard") -> Dict[str, Any]:
        """Legacy Query-Verarbeitung mit Pipeline"""

        complexity_mapping = {
            "basic": QueryComplexity.BASIC,
            "standard": QueryComplexity.STANDARD,
            "advanced": QueryComplexity.ADVANCED,
        }

        query_data = {
            "query": query,
            "user_context": {},
            "complexity": complexity_mapping.get(complexity, QueryComplexity.STANDARD),
        }

        return self.agent_orchestrator.preprocess_query(query_data)


# === MAIN FOR TESTING ===


def main():
    """Test des Agent-Orchestrators"""

    orchestrator = create_agent_orchestrator()

    # Test Query Preprocessing
    test_query = {
        "query": "Wie ist die Luftqualität in München und welche Anlagen beeinflussen sie?",
        "user_context": {"location": "München"},
        "query_id": "test_001",
    }

    result = orchestrator.preprocess_query(test_query)

    print("Agent Orchestrator Test:")
    print(f"Complexity: {result['complexity']}")
    print(f"Domain: {result['domain']}")
    print(f"Required Agents: {result['required_agents']}")
    print(f"Processing Stages: {result['processing_stages']}")
    print(f"Estimated Time: {result['estimated_processing_time']}s")

    # Status
    status = orchestrator.get_orchestrator_status()
    print("\nOrchestrator Status:")
    print(f"Pipelines Created: {status['stats']['pipelines_created']}")
    print(f"Loaded Schemas: {status['loaded_schemas']}")


if __name__ == "__main__":
    main()
