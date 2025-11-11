#!/usr/bin/env python3
"""
VERITAS AGENT PIPELINE MANAGER
==============================

Agent-basiertes Pipeline Management - In-Memory Query-Based Architecture

ARCHITEKTUR ÜBERSICHT:
=====================
Vollständig in-memory query-basierte Pipeline ohne Datenbank-Abhängigkeiten
Analog zu ingestion_core_pipeline_manager.py aber für Agent-Query-Verarbeitung

HAUPTFUNKTIONEN:
- Query Discovery Buffer Management
- Agent-basierte Pipeline Verarbeitung
- Batch Processing Support für Queries
- CRUD-Operationen für Agent-Queries
- Pipeline-Statistiken und Monitoring

DATENSTRUKTUREN:
- QueryBufferItem: Queries im Discovery Buffer
- ProcessingBatch: Gruppen von Queries für Batch-Processing
- AgentQueryItem: Einzelne Queries für Agent-Verarbeitung

Author: VERITAS System (Based on ingestion_core_pipeline_manager.py)
Date: 2025-09-21
Version: 1.0 (Query-driven)
"""

import hashlib
import json
import logging
import os
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Shared Enums
from backend.agents.veritas_shared_enums import QueryComplexity, QueryDomain, QueryStatus

# Import der Konfiguration
try:
    from config import config

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    config = {}

logger = logging.getLogger(__name__)

# ============================================================================
# QUERY PROCESSING ENUMS (aus Shared Enums importiert)
# ============================================================================

# ============================================================================
# DATENSTRUKTUREN
# ============================================================================


@dataclass
class QueryBufferItem:
    """Query im Discovery Buffer"""

    query_id: str
    query_text: str
    user_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    complexity: Optional[QueryComplexity] = None
    domain: Optional[QueryDomain] = None
    submitted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: QueryStatus = QueryStatus.PENDING


@dataclass
class ProcessingBatch:
    """Batch von Queries für gemeinsame Verarbeitung"""

    batch_id: str
    queries: List[QueryBufferItem] = field(default_factory=list)
    batch_type: str = "standard"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    processing_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentQueryItem:
    """Einzelne Query für Agent-Verarbeitung"""

    query_id: str
    query_text: str
    user_context: Dict[str, Any]
    metadata: Dict[str, Any]
    required_agent_types: List[str] = field(default_factory=list)
    agent_capabilities: List[str] = field(default_factory=list)
    priority: int = 1
    complexity: QueryComplexity = QueryComplexity.STANDARD
    domain: QueryDomain = QueryDomain.ENVIRONMENTAL
    status: QueryStatus = QueryStatus.PENDING
    submitted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    processing_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    confidence_score: Optional[float] = None

    # Agent-spezifische Felder
    assigned_agents: List[str] = field(default_factory=list)
    agent_results: Dict[str, Any] = field(default_factory=dict)
    rag_context: Dict[str, Any] = field(default_factory=dict)
    follow_up_suggestions: List[str] = field(default_factory=list)


# ============================================================================
# AGENT PIPELINE MANAGER KLASSE
# ============================================================================


class AgentPipelineManager:
    """
    Agent Pipeline Manager - In-Memory Query-Based Architecture
    Analog zu ingestion_core_pipeline_manager.PipelineManager
    """

    def __init__(self, buffer_size: int = 100, **kwargs):
        """
        Initialisiert den Agent Pipeline Manager

        Args:
            buffer_size: Größe des Query Discovery Buffers
            **kwargs: Zusätzliche Konfigurationsparameter
        """

        # Threading
        self._lock = threading.RLock()

        # In-Memory Storage
        self.query_buffer: Dict[str, QueryBufferItem] = {}
        self.processing_batches: Dict[str, ProcessingBatch] = {}
        self.active_queries: Dict[str, AgentQueryItem] = {}
        self.completed_queries: Dict[str, AgentQueryItem] = {}

        # Configuration
        self.buffer_size = buffer_size
        self.max_completed_queries = kwargs.get("max_completed_queries", 1000)
        self.auto_batch_size = kwargs.get("auto_batch_size", 10)
        self.query_timeout = kwargs.get("query_timeout", 300)  # 5 Minuten

        # Statistics
        self.stats = {
            "queries_submitted": 0,
            "queries_processed": 0,
            "queries_failed": 0,
            "average_processing_time": 0.0,
            "total_processing_time": 0.0,
            "active_queries_count": 0,
            "buffer_utilization": 0.0,
            "last_activity": None,
        }

        # Agent-spezifische Statistiken
        self.agent_stats = {
            "agent_invocations": {},
            "agent_success_rates": {},
            "agent_processing_times": {},
            "capability_usage": {},
            "domain_distribution": {},
        }

        logger.info(f"🎯 Agent Pipeline Manager initialisiert (Buffer: {buffer_size})")

    def submit_query(
        self, query_text: str, user_context: Dict[str, Any] = None, priority: int = 1, metadata: Dict[str, Any] = None
    ) -> str:
        """
        Fügt neue Query zum Pipeline Buffer hinzu

        Args:
            query_text: Text der Benutzeranfrage
            user_context: Benutzerkontext (Standort, Präferenzen, etc.)
            priority: Query-Priorität (höher = wichtiger)
            metadata: Zusätzliche Metadaten

        Returns:
            str: Eindeutige Query-ID
        """

        query_id = str(uuid.uuid4())

        with self._lock:
            # Buffer-Kapazität prüfen
            if len(self.query_buffer) >= self.buffer_size:
                # Älteste Query entfernen (FIFO)
                oldest_query_id = min(self.query_buffer.keys(), key=lambda k: self.query_buffer[k].submitted_at)
                logger.warning(f"⚠️ Query Buffer voll, entferne älteste Query: {oldest_query_id}")
                del self.query_buffer[oldest_query_id]

            # Query-Item erstellen
            query_item = QueryBufferItem(
                query_id=query_id,
                query_text=query_text,
                user_context=user_context or {},
                metadata=metadata or {},
                priority=priority,
            )

            # Zum Buffer hinzufügen
            self.query_buffer[query_id] = query_item

            # Statistiken aktualisieren
            self.stats["queries_submitted"] += 1
            self.stats["buffer_utilization"] = len(self.query_buffer) / self.buffer_size
            self.stats["last_activity"] = datetime.now(timezone.utc).isoformat()

            logger.info(f"📥 Query eingereicht: {query_id} (Priority: {priority})")
            return query_id

    def get_pending_queries(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Holt ausstehende Queries für Agent-Verarbeitung

        Args:
            limit: Maximale Anzahl zurückzugebender Queries

        Returns:
            List[Dict]: Liste von Query-Dictionaries
        """

        with self._lock:
            pending_queries = []

            # Sortiere nach Priorität (höher zuerst) und Submission-Zeit
            sorted_queries = sorted(self.query_buffer.values(), key=lambda q: (-q.priority, q.submitted_at))

            for query_item in sorted_queries:
                if query_item.status == QueryStatus.PENDING:
                    query_dict = {
                        "query_id": query_item.query_id,
                        "query_text": query_item.query_text,
                        "user_context": query_item.user_context,
                        "metadata": query_item.metadata,
                        "priority": query_item.priority,
                        "complexity": query_item.complexity.value if query_item.complexity else None,
                        "domain": query_item.domain.value if query_item.domain else None,
                        "submitted_at": query_item.submitted_at,
                        "required_agent_type": self._analyze_required_agents(query_item),
                    }
                    pending_queries.append(query_dict)

                    if limit and len(pending_queries) >= limit:
                        break

            return pending_queries

    def _analyze_required_agents(self, query_item: QueryBufferItem) -> str:
        """
        Analysiert welche Agent-Typen für eine Query benötigt werden
        Vereinfachte Version - in der Realität würde hier der Agent Preprocessor verwendet

        Args:
            query_item: Query-Item zur Analyse

        Returns:
            str: Hauptsächlich benötigter Agent-Typ
        """

        query_text_lower = query_item.query_text.lower()

        # Domain-spezifische Keyword-Analyse (vereinfacht)
        if any(word in query_text_lower for word in ["geruch", "lärm", "luft", "umwelt", "emissionen"]):
            query_item.domain = QueryDomain.ENVIRONMENTAL
            return "environmental"

        elif any(word in query_text_lower for word in ["bau", "genehmigung", "planung", "bebauung"]):
            query_item.domain = QueryDomain.BUILDING
            return "building"

        elif any(word in query_text_lower for word in ["verkehr", "parken", "öpnv", "bus", "bahn"]):
            query_item.domain = QueryDomain.TRANSPORT
            return "transport"

        elif any(word in query_text_lower for word in ["kita", "pflege", "sozial", "kranken", "gesundheit"]):
            query_item.domain = QueryDomain.SOCIAL
            return "social"

        elif any(word in query_text_lower for word in ["gewerbe", "geschäft", "laden", "gaststätte"]):
            query_item.domain = QueryDomain.BUSINESS
            return "business"

        elif any(word in query_text_lower for word in ["steuer", "gebühr", "abgabe", "finanz"]):
            query_item.domain = QueryDomain.TAXATION
            return "taxation"

        else:
            # Fallback: Document Retrieval für allgemeine Anfragen
            return "document_retrieval"

    def start_query_processing(self, query_id: str) -> Optional[AgentQueryItem]:
        """
        Startet Verarbeitung einer Query

        Args:
            query_id: ID der zu verarbeitenden Query

        Returns:
            AgentQueryItem: Query-Item für Agent-Verarbeitung oder None
        """

        with self._lock:
            if query_id not in self.query_buffer:
                logger.warning(f"⚠️ Query nicht im Buffer gefunden: {query_id}")
                return None

            buffer_item = self.query_buffer[query_id]

            # Query zu aktiver Verarbeitung verschieben
            agent_query_item = AgentQueryItem(
                query_id=buffer_item.query_id,
                query_text=buffer_item.query_text,
                user_context=buffer_item.user_context,
                metadata=buffer_item.metadata,
                priority=buffer_item.priority,
                complexity=buffer_item.complexity or QueryComplexity.STANDARD,
                domain=buffer_item.domain or QueryDomain.ENVIRONMENTAL,
                status=QueryStatus.PROCESSING,
                started_at=datetime.now(timezone.utc).isoformat(),
            )

            # Von Buffer in aktive Queries verschieben
            self.active_queries[query_id] = agent_query_item
            del self.query_buffer[query_id]

            # Statistiken aktualisieren
            self.stats["active_queries_count"] = len(self.active_queries)
            self.stats["buffer_utilization"] = len(self.query_buffer) / self.buffer_size

            logger.info(f"🚀 Query-Verarbeitung gestartet: {query_id}")
            return agent_query_item

    def complete_query_processing(
        self,
        query_id: str,
        result: Dict[str, Any] = None,
        error_message: str = None,
        confidence_score: float = None,
        agent_results: Dict[str, Any] = None,
    ) -> bool:
        """
        Schließt Query-Verarbeitung ab

        Args:
            query_id: ID der abgeschlossenen Query
            result: Verarbeitungs-Ergebnis
            error_message: Fehlermeldung bei Fehler
            confidence_score: Vertrauenswert des Ergebnisses
            agent_results: Detaillierte Agent-Ergebnisse

        Returns:
            bool: True wenn erfolgreich abgeschlossen
        """

        with self._lock:
            if query_id not in self.active_queries:
                logger.warning(f"⚠️ Query nicht in aktiver Verarbeitung: {query_id}")
                return False

            query_item = self.active_queries[query_id]

            # Ergebnis setzen
            query_item.completed_at = datetime.now(timezone.utc).isoformat()
            query_item.result = result
            query_item.error_message = error_message
            query_item.confidence_score = confidence_score
            query_item.agent_results = agent_results or {}

            # Processing Zeit berechnen
            if query_item.started_at:
                start_time = datetime.fromisoformat(query_item.started_at)
                end_time = datetime.fromisoformat(query_item.completed_at)
                query_item.processing_time = (end_time - start_time).total_seconds()

            # Status setzen
            if error_message:
                query_item.status = QueryStatus.FAILED
                self.stats["queries_failed"] += 1
            else:
                query_item.status = QueryStatus.COMPLETED
                self.stats["queries_processed"] += 1

            # Von aktiv zu abgeschlossen verschieben
            self.completed_queries[query_id] = query_item
            del self.active_queries[query_id]

            # Completed Queries Limit prüfen
            if len(self.completed_queries) > self.max_completed_queries:
                # Älteste abgeschlossene Query entfernen
                oldest_completed_id = min(self.completed_queries.keys(), key=lambda k: self.completed_queries[k].completed_at)
                del self.completed_queries[oldest_completed_id]

            # Statistiken aktualisieren
            self._update_processing_statistics(query_item)

            logger.info(f"✅ Query-Verarbeitung abgeschlossen: {query_id} ({query_item.processing_time:.2f}s)")
            return True

    def _update_processing_statistics(self, query_item: AgentQueryItem):
        """Aktualisiert Verarbeitungsstatistiken"""

        # Allgemeine Statistiken
        if query_item.processing_time:
            total_time = self.stats["total_processing_time"] + query_item.processing_time
            processed_count = self.stats["queries_processed"]

            self.stats["total_processing_time"] = total_time
            self.stats["average_processing_time"] = total_time / max(processed_count, 1)

        self.stats["active_queries_count"] = len(self.active_queries)
        self.stats["last_activity"] = datetime.now(timezone.utc).isoformat()

        # Domain-Statistiken
        domain_key = query_item.domain.value if query_item.domain else "unknown"
        if domain_key not in self.agent_stats["domain_distribution"]:
            self.agent_stats["domain_distribution"][domain_key] = 0
        self.agent_stats["domain_distribution"][domain_key] += 1

        # Agent-Ergebnisse analysieren
        if query_item.agent_results:
            for agent_type, agent_result in query_item.agent_results.items():
                # Agent Invocations
                if agent_type not in self.agent_stats["agent_invocations"]:
                    self.agent_stats["agent_invocations"][agent_type] = 0
                self.agent_stats["agent_invocations"][agent_type] += 1

                # Success Rates
                if agent_type not in self.agent_stats["agent_success_rates"]:
                    self.agent_stats["agent_success_rates"][agent_type] = {"success": 0, "total": 0}

                self.agent_stats["agent_success_rates"][agent_type]["total"] += 1

                if not agent_result.get("error"):
                    self.agent_stats["agent_success_rates"][agent_type]["success"] += 1

    def get_query_status(self, query_id: str) -> Optional[Dict[str, Any]]:
        """
        Holt Status einer Query

        Args:
            query_id: Query-ID

        Returns:
            Dict: Query-Status oder None wenn nicht gefunden
        """

        with self._lock:
            # Suche in allen Queues
            for query_dict, location in [
                (self.query_buffer, "buffer"),
                (self.active_queries, "active"),
                (self.completed_queries, "completed"),
            ]:
                if query_id in query_dict:
                    query_item = query_dict[query_id]

                    status = {
                        "query_id": query_item.query_id,
                        "status": query_item.status.value,
                        "location": location,
                        "submitted_at": getattr(query_item, "submitted_at", None),
                        "started_at": getattr(query_item, "started_at", None),
                        "completed_at": getattr(query_item, "completed_at", None),
                        "processing_time": getattr(query_item, "processing_time", None),
                        "confidence_score": getattr(query_item, "confidence_score", None),
                    }

                    # Zusätzliche Felder für aktive/abgeschlossene Queries
                    if location in ["active", "completed"]:
                        status.update(
                            {
                                "complexity": query_item.complexity.value,
                                "domain": query_item.domain.value,
                                "assigned_agents": getattr(query_item, "assigned_agents", []),
                                "has_result": query_item.result is not None,
                                "has_error": query_item.error_message is not None,
                            }
                        )

                    return status

            return None

    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """
        Liefert detaillierte Pipeline-Statistiken

        Returns:
            Dict: Pipeline-Statistiken
        """

        with self._lock:
            # Basis-Statistiken
            statistics = {
                "general_stats": self.stats.copy(),
                "agent_stats": self.agent_stats.copy(),
                "queue_stats": {
                    "buffer_size": len(self.query_buffer),
                    "buffer_capacity": self.buffer_size,
                    "active_queries": len(self.active_queries),
                    "completed_queries": len(self.completed_queries),
                    "buffer_utilization_percent": (len(self.query_buffer) / self.buffer_size) * 100,
                },
                "query_complexity_distribution": {},
                "query_domain_distribution": self.agent_stats["domain_distribution"].copy(),
            }

            # Komplexitäts-Verteilung analysieren
            complexity_dist = {}
            for query_item in list(self.active_queries.values()) + list(self.completed_queries.values()):
                complexity = query_item.complexity.value if query_item.complexity else "unknown"
                complexity_dist[complexity] = complexity_dist.get(complexity, 0) + 1

            statistics["query_complexity_distribution"] = complexity_dist

            # Success Rates berechnen
            agent_success_rates = {}
            for agent_type, rates in self.agent_stats["agent_success_rates"].items():
                if rates["total"] > 0:
                    success_rate = (rates["success"] / rates["total"]) * 100
                    agent_success_rates[agent_type] = round(success_rate, 2)

            statistics["agent_success_rates_percent"] = agent_success_rates

            return statistics

    def cleanup_old_queries(self, max_age_hours: int = 24) -> int:
        """
        Räumt alte abgeschlossene Queries auf

        Args:
            max_age_hours: Maximales Alter in Stunden

        Returns:
            int: Anzahl aufgeräumter Queries
        """

        with self._lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
            cutoff_timestamp = cutoff_time.isoformat()

            cleanup_count = 0
            queries_to_remove = []

            for query_id, query_item in self.completed_queries.items():
                if query_item.completed_at and query_item.completed_at < cutoff_timestamp:
                    queries_to_remove.append(query_id)

            for query_id in queries_to_remove:
                del self.completed_queries[query_id]
                cleanup_count += 1

            if cleanup_count > 0:
                logger.info(f"🧹 {cleanup_count} alte Queries aufgeräumt (älter als {max_age_hours}h)")

            return cleanup_count


# ============================================================================
# FACTORY FUNCTIONS & GLOBAL ACCESS
# ============================================================================

# Globale Agent-Pipeline-Manager-Instanz (Singleton Pattern)
_global_agent_pipeline_manager: Optional[AgentPipelineManager] = None
_manager_lock = threading.RLock()


def get_agent_pipeline_db(buffer_size: int = 100, **kwargs) -> AgentPipelineManager:
    """
    Liefert globale Agent-Pipeline-Manager-Instanz (Singleton Pattern)

    Args:
        buffer_size: Größe des Query Buffers
        **kwargs: Zusätzliche Konfigurationsparameter

    Returns:
        AgentPipelineManager: Globale Pipeline-Manager-Instanz
    """
    global _global_agent_pipeline_manager

    with _manager_lock:
        if _global_agent_pipeline_manager is None:
            _global_agent_pipeline_manager = AgentPipelineManager(buffer_size=buffer_size, **kwargs)
            logger.info(f"🎯 Globaler Agent Pipeline Manager initialisiert")

        return _global_agent_pipeline_manager


# Alias für Kompatibilität mit anderen Modulen
AgentPipelineDB = AgentPipelineManager

if __name__ == "__main__":
    # Test des Agent Pipeline Managers
    manager = get_agent_pipeline_db(buffer_size=50)

    # Test-Query einreichen
    query_id = manager.submit_query(
        query_text="Wie ist die Luftqualität in München?",
        user_context={"location": "München", "user_type": "citizen"},
        priority=2,
    )

    print(f"Query eingereicht: {query_id}")

    # Pending Queries abrufen
    pending = manager.get_pending_queries(limit=5)
    print(f"Pending Queries: {len(pending)}")

    # Statistiken
    stats = manager.get_pipeline_statistics()
    print(f"Pipeline Statistiken: {stats['general_stats']}")
