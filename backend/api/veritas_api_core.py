#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Agent Core - Agent-Engine Foundation (Migrated from Covina)
==================================================================

Core-Modul für das VERITAS Agent-System mit externen Datenquellen.
Implementiert die Agent-Engine-Architektur mit Preprocessor, Worker-Ecosystem und Postprocessor.

Features:
- Parallelisierte Worker-Pipeline
- Externe Datenquellen (EU LEX, Google Search, SQL)
- Metadaten-gesteuerte Verarbeitung
- Native Ollama-Integration
- Intelligente Fallback-Systeme

Author: VERITAS System
Created: 2025-09-21 (Migrated from Covina)
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

# VERITAS Core Imports
try:
    from native_ollama_integration import DirectOllamaEmbeddings, DirectOllamaLLM

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Native Ollama Integration nicht verfügbar")

try:
    from config import DATABASE_CONFIG

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    DATABASE_CONFIG = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# VERITAS AGENT-ENGINE CORE TYPES
# =============================================================================


class QueryComplexity(Enum):
    """Query-Komplexitätslevel"""

    SIMPLE = "simple"  # Einfache Faktenfrage
    STANDARD = "standard"  # Standard-RAG mit externen Daten
    COMPLEX = "complex"  # Multi-Step-Reasoning
    EXPERT = "expert"  # Hochkomplexe Analyse


class VeritasWorkerType(Enum):
    """Verfügbare Worker-Typen im Veritas System"""

    # Core Workers
    GEO_CONTEXT = "geo_context"
    LEGAL_FRAMEWORK = "legal_framework"
    DOCUMENT_RETRIEVAL = "document_retrieval"
    EXTERNAL_API = "external_api"
    COST_ANALYSIS = "cost_analysis"
    TIMELINE = "timeline"
    AUTHORITY_MAPPING = "authority_mapping"
    RISK_ASSESSMENT = "risk_assessment"

    # Environmental Domain Workers
    ENVIRONMENTAL = "environmental"
    AIR_QUALITY = "air_quality"
    NOISE_COMPLAINT = "noise_complaint"
    WASTE_MANAGEMENT = "waste_management"

    # Construction Domain Workers
    CONSTRUCTION = "construction"
    BUILDING_PERMIT = "building_permit"
    URBAN_PLANNING = "urban_planning"
    HERITAGE_PROTECTION = "heritage_protection"

    # Traffic Domain Workers
    TRAFFIC = "traffic"
    TRAFFIC_MANAGEMENT = "traffic_management"
    PUBLIC_TRANSPORT = "public_transport"
    PARKING_MANAGEMENT = "parking_management"

    # Financial Domain Workers
    FINANCIAL = "financial"
    TAX_ASSESSMENT = "tax_assessment"
    FUNDING_OPPORTUNITIES = "funding_opportunities"
    BUSINESS_TAX = "business_tax"

    # Social Services Domain Workers
    SOCIAL = "social"
    SOCIAL_BENEFITS = "social_benefits"
    CITIZEN_SERVICES = "citizen_services"
    HEALTH_INSURANCE = "health_insurance"


class ProcessingPhase(Enum):
    """Verarbeitungsphasen"""

    PREPROCESSOR = "preprocessor"
    WORKER_EXECUTION = "worker_execution"
    POSTPROCESSOR = "postprocessor"


@dataclass
class VeritasQueryMetadata:
    """Metadaten für eine Agent-Query"""

    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    complexity: QueryComplexity = QueryComplexity.STANDARD
    domain: str = "general"
    priority: int = 1
    max_workers: int = 5
    timeout_seconds: int = 30
    external_sources_enabled: bool = True
    cache_enabled: bool = True
    quality_threshold: float = 0.7
    created_at: datetime = field(default_factory=datetime.now)
    user_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VeritasWorkerResult:
    """Ergebnis eines Worker-Prozesses"""

    worker_type: VeritasWorkerType
    success: bool
    data: Dict[str, Any]
    confidence_score: float
    processing_time: float
    sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    external_data: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class VeritasProcessingResult:
    """Gesamtergebnis der Agent-Engine-Verarbeitung"""

    query_id: str
    final_answer: str
    worker_results: List[VeritasWorkerResult]
    overall_confidence: float
    processing_time: float
    sources_used: List[str]
    quality_metrics: Dict[str, float]
    metadata: VeritasQueryMetadata
    external_data_summary: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# VERITAS AGENT PREPROCESSOR
# =============================================================================


class VeritasAgentPreprocessor:
    """
    Preprocessor für eingehende Queries
    Analysiert und klassifiziert die Anfrage, bestimmt notwendige Worker
    """

    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm
        self.domain_keywords = {
            "construction": ["bau", "gebäude", "bauplan", "bauantrag", "sanierung"],
            "environmental": ["umwelt", "lärm", "luft", "wasser", "abfall"],
            "traffic": ["verkehr", "straße", "parking", "öffentlich", "transport"],
            "financial": ["steuer", "gebühr", "kosten", "förderung", "finanzierung"],
            "social": ["sozial", "hilfe", "unterstützung", "kranken", "rente"],
        }

        logger.info("✅ Veritas Agent Preprocessor initialisiert")

    async def analyze_query(self, query: str, context: Dict[str, Any] = None) -> VeritasQueryMetadata:
        """
        Analysiert die eingehende Query und erstellt Metadaten
        """
        metadata = VeritasQueryMetadata()

        # Domain-Erkennung basierend auf Keywords
        detected_domain = self._detect_domain(query)
        metadata.domain = detected_domain

        # Komplexitäts-Analyse
        complexity = self._analyze_complexity(query)
        metadata.complexity = complexity

        # Context einbinden falls vorhanden
        if context:
            metadata.user_context = context

        logger.info(f"📋 Query analysiert: Domain={detected_domain}, Complexity={complexity.value}")

        return metadata

    def _detect_domain(self, query: str) -> str:
        """Erkennt die Domain basierend auf Keywords"""
        query_lower = query.lower()

        domain_scores = {}
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            return max(domain_scores, key=domain_scores.get)

        return "general"

    def _analyze_complexity(self, query: str) -> QueryComplexity:
        """Analysiert die Komplexität der Query"""
        query_lower = query.lower()

        # Komplexitäts-Indikatoren
        complex_indicators = ["vergleiche", "analysiere", "bewerte", "optimiere", "berechne"]
        expert_indicators = ["rechtliche grundlage", "verfahrensrecht", "präzedenzfall"]

        if any(indicator in query_lower for indicator in expert_indicators):
            return QueryComplexity.EXPERT
        elif any(indicator in query_lower for indicator in complex_indicators):
            return QueryComplexity.COMPLEX
        elif len(query.split()) > 10:
            return QueryComplexity.STANDARD
        else:
            return QueryComplexity.SIMPLE

    def select_workers(self, metadata: VeritasQueryMetadata) -> List[VeritasWorkerType]:
        """Wählt passende Worker basierend auf Domain und Komplexität"""
        selected_workers = []

        # Basis-Worker für alle Queries
        selected_workers.append(VeritasWorkerType.DOCUMENT_RETRIEVAL)

        # Domain-spezifische Worker
        domain_worker_mapping = {
            "construction": [VeritasWorkerType.CONSTRUCTION, VeritasWorkerType.BUILDING_PERMIT],
            "environmental": [VeritasWorkerType.ENVIRONMENTAL, VeritasWorkerType.AIR_QUALITY],
            "traffic": [VeritasWorkerType.TRAFFIC, VeritasWorkerType.TRAFFIC_MANAGEMENT],
            "financial": [VeritasWorkerType.FINANCIAL, VeritasWorkerType.TAX_ASSESSMENT],
            "social": [VeritasWorkerType.SOCIAL, VeritasWorkerType.SOCIAL_BENEFITS],
        }

        if metadata.domain in domain_worker_mapping:
            selected_workers.extend(domain_worker_mapping[metadata.domain])

        # Komplexitäts-basierte Worker
        if metadata.complexity in [QueryComplexity.COMPLEX, QueryComplexity.EXPERT]:
            selected_workers.extend([VeritasWorkerType.LEGAL_FRAMEWORK, VeritasWorkerType.EXTERNAL_API])

        # Externe Datenquellen bei höherer Komplexität
        if metadata.external_sources_enabled and metadata.complexity != QueryComplexity.SIMPLE:
            selected_workers.append(VeritasWorkerType.EXTERNAL_API)

        # Duplikate entfernen und auf max_workers begrenzen
        unique_workers = list(dict.fromkeys(selected_workers))
        return unique_workers[: metadata.max_workers]


# =============================================================================
# VERITAS AGENT ENGINE
# =============================================================================


class VeritasAgentEngine:
    """
    Hauptklasse für das Veritas Agent-System
    Orchestriert Preprocessor, Worker-Execution und Postprocessor
    """

    def __init__(self, llm: Optional[Any] = None, embeddings: Optional[Any] = None):
        self.llm = llm
        self.embeddings = embeddings
        self.preprocessor = VeritasAgentPreprocessor(llm)
        self.workers = {}
        self.session_data = {}

        # Worker-Registry initialisieren
        self._initialize_worker_registry()

        logger.info("🚀 Veritas Agent Engine initialisiert")

    def _initialize_worker_registry(self):
        """Initialisiert die Worker-Registry"""
        # TODO: Hier werden die spezifischen Worker-Implementierungen registriert
        # from veritas_agent_workers import (
        #     VeritasDocumentWorker, VeritasLegalWorker, VeritasExternalAPIWorker
        # )

        logger.info("📋 Worker-Registry initialisiert")

    async def process_query(
        self, query: str, session_id: Optional[str] = None, context: Dict[str, Any] = None
    ) -> VeritasProcessingResult:
        """
        Hauptmethode zur Verarbeitung einer Agent-Query
        """
        start_time = time.time()

        # 1. Preprocessing - Query analysieren
        metadata = await self.preprocessor.analyze_query(query, context)
        if session_id:
            metadata.session_id = session_id

        logger.info(f"🔍 Verarbeite Query: {metadata.query_id}")

        # 2. Worker-Auswahl
        selected_workers = self.preprocessor.select_workers(metadata)
        logger.info(f"⚙️ Ausgewählte Worker: {[w.value for w in selected_workers]}")

        # 3. Worker-Execution (parallel)
        worker_results = await self._execute_workers(query, selected_workers, metadata)

        # 4. Postprocessing - Ergebnisse zusammenführen
        final_result = await self._postprocess_results(query, worker_results, metadata)

        processing_time = time.time() - start_time
        final_result.processing_time = processing_time

        logger.info(f"✅ Query verarbeitet in {processing_time:.2f}s")

        return final_result

    async def _execute_workers(
        self, query: str, worker_types: List[VeritasWorkerType], metadata: VeritasQueryMetadata
    ) -> List[VeritasWorkerResult]:
        """
        Führt alle ausgewählten Worker parallel aus
        """
        tasks = []

        for worker_type in worker_types:
            task = self._execute_single_worker(query, worker_type, metadata)
            tasks.append(task)

        # Alle Worker parallel ausführen
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Fehlerbehandlung
        worker_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Worker {worker_types[i].value} fehlgeschlagen: {result}")
                # Fallback-Result erstellen
                worker_results.append(
                    VeritasWorkerResult(
                        worker_type=worker_types[i],
                        success=False,
                        data={},
                        confidence_score=0.0,
                        processing_time=0.0,
                        error_message=str(result),
                    )
                )
            else:
                worker_results.append(result)

        return worker_results

    async def _execute_single_worker(
        self, query: str, worker_type: VeritasWorkerType, metadata: VeritasQueryMetadata
    ) -> VeritasWorkerResult:
        """
        Führt einen einzelnen Worker aus
        """
        start_time = time.time()

        try:
            # TODO: Hier wird der spezifische Worker ausgeführt
            # worker = self.workers.get(worker_type)
            # if worker:
            #     result = await worker.process(query, metadata)
            # else:
            #     # Fallback-Implementierung

            # Dummy-Implementierung für Migration
            await asyncio.sleep(0.1)  # Simuliere Verarbeitung

            processing_time = time.time() - start_time

            return VeritasWorkerResult(
                worker_type=worker_type,
                success=True,
                data={"query": query, "worker_type": worker_type.value, "result": f"Verarbeitet von {worker_type.value}"},
                confidence_score=0.85,
                processing_time=processing_time,
                sources=[f"{worker_type.value}_source"],
                metadata={"domain": metadata.domain},
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Fehler in Worker {worker_type.value}: {e}")

            return VeritasWorkerResult(
                worker_type=worker_type,
                success=False,
                data={},
                confidence_score=0.0,
                processing_time=processing_time,
                error_message=str(e),
            )

    async def _postprocess_results(
        self, query: str, worker_results: List[VeritasWorkerResult], metadata: VeritasQueryMetadata
    ) -> VeritasProcessingResult:
        """
        Postprocessing - Zusammenführung aller Worker-Ergebnisse
        """
        successful_results = [r for r in worker_results if r.success]

        # Gesamtantwort generieren
        if successful_results:
            # TODO: Hier intelligente Zusammenführung mit LLM
            final_answer = self._generate_final_answer(query, successful_results)
            overall_confidence = sum(r.confidence_score for r in successful_results) / len(successful_results)
        else:
            final_answer = "Entschuldigung, ich konnte keine verlässliche Antwort generieren."
            overall_confidence = 0.0

        # Quellen sammeln
        sources_used = []
        for result in successful_results:
            sources_used.extend(result.sources)

        # Qualitäts-Metriken berechnen
        quality_metrics = {
            "success_rate": len(successful_results) / len(worker_results) if worker_results else 0,
            "avg_confidence": overall_confidence,
            "source_count": len(sources_used),
            "worker_count": len(worker_results),
        }

        return VeritasProcessingResult(
            query_id=metadata.query_id,
            final_answer=final_answer,
            worker_results=worker_results,
            overall_confidence=overall_confidence,
            processing_time=0.0,  # Wird später gesetzt
            sources_used=list(set(sources_used)),
            quality_metrics=quality_metrics,
            metadata=metadata,
        )

    def _generate_final_answer(self, query: str, results: List[VeritasWorkerResult]) -> str:
        """Generiert finale Antwort aus Worker-Ergebnissen"""
        # TODO: Hier LLM-basierte Zusammenführung

        # Einfache Implementierung für Migration
        answer_parts = []
        for result in results:
            if result.data:
                answer_parts.append(f"• {result.worker_type.value}: {result.data.get('result', 'Keine Daten')}")

        if answer_parts:
            return "Basierend auf der Analyse verschiedener Datenquellen:\n\n" + "\n".join(answer_parts)
        else:
            return "Keine verwertbaren Ergebnisse gefunden."


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def create_veritas_agent_engine(config: Dict[str, Any] = None) -> VeritasAgentEngine:
    """Factory-Funktion für Veritas Agent Engine"""

    # LLM und Embeddings initialisieren falls verfügbar
    llm = None
    embeddings = None

    if OLLAMA_AVAILABLE:
        try:
            llm = DirectOllamaLLM()
            embeddings = DirectOllamaEmbeddings()
            logger.info("✅ Ollama LLM und Embeddings geladen")
        except Exception as e:
            logger.warning(f"⚠️ Ollama nicht verfügbar: {e}")

    return VeritasAgentEngine(llm=llm, embeddings=embeddings)


def get_available_worker_types() -> List[str]:
    """Gibt alle verfügbaren Worker-Typen zurück"""
    return [worker.value for worker in VeritasWorkerType]


def get_default_agent_config() -> Dict[str, Any]:
    """Standard-Konfiguration für Agent Engine"""
    return {
        "max_workers": 5,
        "timeout_seconds": 30,
        "quality_threshold": 0.7,
        "external_sources_enabled": True,
        "cache_enabled": True,
    }
