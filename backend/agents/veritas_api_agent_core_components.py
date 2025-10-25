#!/usr/bin/env python3
"""
VERITAS AGENT CORE COMPONENTS
=============================

Agent-basierte Query-Verarbeitung analog zur Ingestion-Pipeline-Architektur

ARCHITEKTUR:
- Vollständig in-memory agent-basierte Pipeline
- Agent Registry Integration mit Shared Resource Pool
- Query-basierte Task-Verwaltung über AgentPipelineManager
- @dataclass basierte Datenstrukturen für Agents
- Parallele Agent-Verarbeitung mit RAG Integration

AGENT-TYPEN:
• Core Agents: document_retrieval, legal_framework, geo_context, timeline
• Domain Agents: environmental, construction, traffic, financial, social
• Processing Agents: preprocessor, postprocessor, aggregator, quality_assessor
• Integration Agents: ollama_llm, external_api, database_connector

INTEGRATION:
User Query → FastAPI → AgentCoordinator → AgentRegistry → RAG Pipeline → Response

Author: VERITAS System (Based on Ingestion Architecture)
Date: 2025-09-21
Version: 1.0 (Agent-driven)
"""

import os
import sys
import time
import threading
import logging
import queue
import json
import uuid
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass
from enum import Enum
import traceback
from datetime import datetime, timedelta, timezone
from queue import PriorityQueue, Empty
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path

# Agent Registry Integration (In-Memory)
try:
    from backend.agents.veritas_api_agent_registry import (
        get_agent_registry,
        AgentCapability,
        AgentLifecycleType,
        AgentStatus,
    )
    AGENT_REGISTRY_AVAILABLE = True
except ImportError as e:
    AGENT_REGISTRY_AVAILABLE = False
    logging.warning(f"⚠️ Agent Registry noch nicht verfügbar: {e}")

# Agent Pipeline Manager (No Database)
try:
    from backend.agents.veritas_api_agent_pipeline_manager import (
        get_agent_pipeline_db,
        AgentPipelineManager
    )
    AGENT_PIPELINE_AVAILABLE = True
except ImportError as e:
    AGENT_PIPELINE_AVAILABLE = False
    logging.warning(f"⚠️ Agent Pipeline Manager noch nicht verfügbar: {e}")

# ============================================================================
# RAG Integration - UDS3 Direct Integration (NO FALLBACK)
# ============================================================================
from uds3.core import UDS3PolyglotManager

logger = logging.getLogger(__name__)

# === AGENT MESSAGE TYPES ===

class AgentMessageType(Enum):
    """Nachrichtentypen für Agent-Query-Kommunikation"""
    QUERY_START = "query_start"
    QUERY_COMPLETE = "query_complete"
    QUERY_ERROR = "query_error"
    AGENT_RESULT = "agent_result"
    RAG_RETRIEVAL = "rag_retrieval"
    LLM_GENERATION = "llm_generation"
    PROGRESS_UPDATE = "progress_update"
    STATUS_UPDATE = "status_update"
    ERROR_MESSAGE = "error_message"
    AGENT_SPAWNED = "agent_spawned"
    AGENT_TERMINATED = "agent_terminated"

@dataclass
class AgentMessage:
    """Standardisierte Agent-Nachricht für query-basierte Pipeline"""
    message_type: AgentMessageType
    agent_id: str
    query_id: str
    timestamp: str
    data: Dict[str, Any]
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

@dataclass
class AgentStatistics:
    """Statistiken für einzelne Agents"""
    agent_id: str
    agent_type: str
    queries_processed: int = 0
    queries_failed: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    last_activity: Optional[str] = None
    status: str = "idle"
    confidence_scores: List[float] = None
    rag_retrievals: int = 0
    
    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = []

class AgentIdlenessManager:
    """Verwaltet Agent-Inaktivität für dynamisches Scaling (analog zu WorkerIdlenessManager)"""
    
    def __init__(self, max_idle_time: float = 60.0):
        self.max_idle_time = max_idle_time
        self.agent_activity: Dict[str, Dict[str, Any]] = {}
        self.activity_lock = threading.RLock()
        
    def register_agent(self, agent_id: str, agent_type: str, capabilities: Set[str]):
        """Registriert neuen Agent für Idleness-Tracking"""
        with self.activity_lock:
            self.agent_activity[agent_id] = {
                'agent_type': agent_type,
                'capabilities': capabilities,
                'last_activity': time.time(),
                'queries_processed': 0,
                'created_at': time.time()
            }
            
    def update_agent_activity(self, agent_id: str, query_processed: bool = False):
        """Aktualisiert Agent-Aktivität"""
        with self.activity_lock:
            if agent_id in self.agent_activity:
                self.agent_activity[agent_id]['last_activity'] = time.time()
                if query_processed:
                    self.agent_activity[agent_id]['queries_processed'] += 1
                        
    def should_terminate_agent(self, agent_id: str, query_demand_analysis: Dict[str, Any] = None) -> bool:
        """Entscheidet ob Agent terminiert werden soll"""
        with self.activity_lock:
            if agent_id not in self.agent_activity:
                return False
                
            activity = self.agent_activity[agent_id]
            idle_time = time.time() - activity['last_activity']
            
            # Basis-Regel: Agent idle länger als max_idle_time
            if idle_time > self.max_idle_time:
                # Erweiterte Logik: Berücksichtige Query-Demand
                if query_demand_analysis:
                    agent_type = activity['agent_type']
                    pending_queries = query_demand_analysis.get('pending_queries_by_type', {}).get(agent_type, 0)
                    
                    # Halte mindestens einen Agent pro Typ mit Queries
                    if pending_queries > 0:
                        active_agents_of_type = query_demand_analysis.get('active_agents_by_type', {}).get(agent_type, 0)
                        if active_agents_of_type <= 1:
                            return False
                
                return True
            
            return False

class QueryAnalyzer:
    """Intelligente Query-Analyse für Agent-Scaling (analog zu JobQueueAnalyzer)"""
    
    def __init__(self, agent_coordinator):
        self.agent_coordinator = agent_coordinator
        
    def analyze_query_demand(self) -> Dict[str, Any]:
        """Analysiert aktuelle Query-Nachfrage für optimales Agent-Scaling"""
        try:
            # Hole pending Queries vom AgentPipelineManager
            pending_queries = self.agent_coordinator.pipeline_manager.get_pending_queries(limit=1000)
            
            # Analysiere Queries nach Typ
            queries_by_type = {}
            total_queries = len(pending_queries)
            
            for query in pending_queries:
                agent_type = query.get('required_agent_type', 'unknown')
                if agent_type not in queries_by_type:
                    queries_by_type[agent_type] = 0
                queries_by_type[agent_type] += 1
            
            # Analysiere aktive Agents
            active_agents_by_type = {}
            total_active_agents = 0
            
            with self.agent_coordinator.agent_lock:
                for agent_id, agent_info in self.agent_coordinator.active_agents.items():
                    agent_type = agent_info.get('agent_type', 'unknown')
                    if agent_type not in active_agents_by_type:
                        active_agents_by_type[agent_type] = 0
                    active_agents_by_type[agent_type] += 1
                    total_active_agents += 1
            
            # Scaling-Empfehlungen
            scaling_recommendations = {}
            for agent_type, query_count in queries_by_type.items():
                current_agents = active_agents_by_type.get(agent_type, 0)
                
                # Agent-spezifische Scaling-Logik: 1 Agent pro 3 Queries, max 3 Agents pro Typ
                recommended_agents = min(max(1, query_count // 3), 3)
                
                if recommended_agents > current_agents:
                    scaling_recommendations[agent_type] = {
                        'action': 'scale_up',
                        'current': current_agents,
                        'recommended': recommended_agents,
                        'pending_queries': query_count
                    }
                elif current_agents > recommended_agents and current_agents > 1:
                    scaling_recommendations[agent_type] = {
                        'action': 'scale_down',
                        'current': current_agents,
                        'recommended': recommended_agents,
                        'pending_queries': query_count
                    }
            
            return {
                'total_pending_queries': total_queries,
                'total_active_agents': total_active_agents,
                'pending_queries_by_type': queries_by_type,
                'active_agents_by_type': active_agents_by_type,
                'scaling_recommendations': scaling_recommendations,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Query-Demand-Analyse fehlgeschlagen: {e}")
            return {}

class GUIAdapter:
    """GUI-Adapter für Agent-Status-Updates (analog zu Ingestion)"""
    
    def __init__(self, gui_queue: queue.Queue = None):
        self.gui_queue = gui_queue
        
    def send_agent_update(self, message_type: AgentMessageType, agent_id: str, data: Dict[str, Any]):
        """Sendet Agent-Update an GUI"""
        if self.gui_queue:
            try:
                message = AgentMessage(
                    message_type=message_type,
                    agent_id=agent_id,
                    query_id=data.get('query_id', 'unknown'),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    data=data
                )
                self.gui_queue.put_nowait(message)
            except queue.Full:
                logger.warning(f"⚠️ GUI Queue voll, Agent-Update verloren: {agent_id}")

# === AGENT COORDINATOR V1 - QUERY-BASED FINAL VERSION ===

class AgentCoordinator:
    """
    Agent-basierter Coordinator V1 - Query-Verarbeitung
    
    ARCHITEKTUR (analog zu ThreadCoordinator):
    - In-Memory Agent-Verwaltung
    - Query-basierte Task-Erstellung
    - Direkte AgentPipelineManager-Integration
    - RAG-Pipeline-Kopplung für Retrieval
    """
    
    def __init__(self, 
                 gui_queue: queue.Queue = None, 
                 check_interval: float = 2.0,
                 orchestrator=None,
                 pipeline_manager=None,
                 database_api=None,
                 uds3_strategy=None):
        """
        Initialisiert den Agent-Coordinator
        
        Args:
            gui_queue: Queue für GUI-Updates
            check_interval: Intervall für Agent-Monitoring (Sekunden)
            orchestrator: Agent-Orchestrator-Instanz
            pipeline_manager: Shared AgentPipelineManager-Instanz
            database_api: RAG Database API
            uds3_strategy: Unified Database Strategy
        """
        
        # Core Setup
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_lock = threading.RLock()
        self.query_queue = PriorityQueue()
        self.result_queue = queue.Queue()
        
        # Threading Control
        self.is_running = False
        self.coordinator_thread = None
        self.monitor_thread = None
        
        # Configuration
        self.check_interval = check_interval
        self.max_concurrent_agents = int(os.getenv('VERITAS_MAX_AGENTS', '10'))
        self.enable_dynamic_scaling = os.getenv('VERITAS_DYNAMIC_SCALING', 'true').lower() == 'true'
        
        # External Components
        self.orchestrator = orchestrator
        self.pipeline_manager = pipeline_manager
        self.gui_adapter = GUIAdapter(gui_queue)
        
        # RAG Integration
        self.database_api = database_api
        self.uds3_strategy = uds3_strategy
        
        # Management Components
        self.idleness_manager = AgentIdlenessManager()
        self.query_analyzer = QueryAnalyzer(self)
        
        # Statistics
        self.stats = {
            'queries_processed': 0,
            'queries_failed': 0,
            'agents_spawned': 0,
            'agents_terminated': 0,
            'total_processing_time': 0.0,
            'rag_retrievals': 0,
            'llm_generations': 0
        }
        
        # Agent Registry Integration
        if AGENT_REGISTRY_AVAILABLE:
            self.agent_registry = get_agent_registry()
            logger.info("✅ Agent Registry verfügbar")
        else:
            self.agent_registry = None
            logger.warning("⚠️ Agent Registry nicht verfügbar - Fallback-Modus")
        
        logger.info("🎯 AgentCoordinator initialisiert")
    
    def start(self):
        """Startet den Agent-Coordinator"""
        if self.is_running:
            logger.warning("⚠️ AgentCoordinator läuft bereits")
            return
        
        self.is_running = True
        
        # Starte Coordinator-Thread
        self.coordinator_thread = threading.Thread(
            target=self._coordinator_loop,
            name="AgentCoordinator-Main",
            daemon=True
        )
        self.coordinator_thread.start()
        
        # Starte Monitor-Thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="AgentCoordinator-Monitor",
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("🚀 AgentCoordinator gestartet")
    
    def stop(self):
        """Stoppt den Agent-Coordinator"""
        if not self.is_running:
            return
        
        logger.info("🛑 Stoppe AgentCoordinator...")
        self.is_running = False
        
        # Terminiere alle aktiven Agents
        self._terminate_all_agents()
        
        # Warte auf Thread-Beendigung
        if self.coordinator_thread and self.coordinator_thread.is_alive():
            self.coordinator_thread.join(timeout=5.0)
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        logger.info("✅ AgentCoordinator gestoppt")
    
    def submit_query(self, query_data: Dict[str, Any], priority: int = 1) -> str:
        """
        Fügt Query zur Verarbeitung hinzu
        
        Args:
            query_data: Query-Daten inkl. query, user_context, etc.
            priority: Priorität (höher = wichtiger)
            
        Returns:
            query_id: Eindeutige Query-ID
        """
        query_id = str(uuid.uuid4())
        
        query_item = {
            'query_id': query_id,
            'query_data': query_data,
            'priority': priority,
            'submitted_at': time.time(),
            'status': 'pending'
        }
        
        # Zur Query-Queue hinzufügen
        self.query_queue.put((priority, time.time(), query_item))
        
        # GUI Update
        self.gui_adapter.send_agent_update(
            AgentMessageType.QUERY_START,
            'coordinator',
            {'query_id': query_id, 'query_data': query_data}
        )
        
        logger.info(f"📥 Query eingereicht: {query_id}")
        return query_id
    
    def get_query_result(self, query_id: str, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """
        Holt Ergebnis für Query (blockierend)
        
        Args:
            query_id: Query-ID
            timeout: Timeout in Sekunden
            
        Returns:
            Query-Ergebnis oder None bei Timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Prüfe Result-Queue
                result = self.result_queue.get(timeout=1.0)
                
                if result.get('query_id') == query_id:
                    return result
                else:
                    # Nicht unser Ergebnis, zurück in Queue
                    self.result_queue.put(result)
                    
            except queue.Empty:
                continue
        
        logger.warning(f"⏰ Query-Timeout: {query_id}")
        return None
    
    def _coordinator_loop(self):
        """Haupt-Coordinator-Loop für Query-Verarbeitung"""
        logger.info("🔄 AgentCoordinator-Loop gestartet")
        
        while self.is_running:
            try:
                # Hole nächste Query (mit Timeout)
                try:
                    priority, timestamp, query_item = self.query_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Verarbeite Query
                self._process_query(query_item)
                
            except Exception as e:
                logger.error(f"❌ Coordinator-Loop Fehler: {e}")
                traceback.print_exc()
                time.sleep(1.0)
    
    def _monitor_loop(self):
        """Monitor-Loop für Agent-Management"""
        logger.info("📊 AgentCoordinator-Monitor gestartet")
        
        while self.is_running:
            try:
                # Agent-Status überprüfen
                self._check_agent_health()
                
                # Dynamic Scaling (wenn aktiviert)
                if self.enable_dynamic_scaling:
                    self._handle_dynamic_scaling()
                
                # Statistiken aktualisieren
                self._update_statistics()
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Monitor-Loop Fehler: {e}")
                time.sleep(5.0)
    
    def _process_query(self, query_item: Dict[str, Any]):
        """Verarbeitet einzelne Query durch Agent-Pipeline"""
        query_id = query_item['query_id']
        query_data = query_item['query_data']
        
        try:
            logger.info(f"🎯 Verarbeite Query: {query_id}")
            
            # 1. Query-Preprocessing durch Orchestrator
            if self.orchestrator:
                preprocessing_result = self.orchestrator.preprocess_query(query_data)
                required_agent_types = preprocessing_result.get('required_agents', ['document_retrieval'])
            else:
                # Fallback: Standard-Agents
                required_agent_types = ['document_retrieval', 'legal_framework']
            
            # 2. Spawn benötigte Agents
            agent_results = {}
            agent_futures = []
            
            with ThreadPoolExecutor(max_workers=len(required_agent_types)) as executor:
                for agent_type in required_agent_types:
                    future = executor.submit(self._execute_agent, agent_type, query_data, query_id)
                    agent_futures.append((agent_type, future))
                
                # Sammle Ergebnisse
                for agent_type, future in agent_futures:
                    try:
                        result = future.result(timeout=30.0)
                        agent_results[agent_type] = result
                    except Exception as e:
                        logger.error(f"❌ Agent {agent_type} fehlgeschlagen: {e}")
                        agent_results[agent_type] = {'error': str(e), 'confidence_score': 0.0}
            
            # 3. Ergebnis-Aggregation durch Orchestrator
            if self.orchestrator:
                final_result = self.orchestrator.aggregate_results(query_data, agent_results)
            else:
                # Fallback: Einfache Aggregation
                final_result = {
                    'response_text': "Verarbeitung abgeschlossen (Fallback-Modus)",
                    'confidence_score': 0.5,
                    'agent_results': agent_results
                }
            
            # 4. Ergebnis zur Result-Queue hinzufügen
            final_result['query_id'] = query_id
            final_result['processing_time'] = time.time() - query_item['submitted_at']
            
            self.result_queue.put(final_result)
            
            # Statistics Update
            self.stats['queries_processed'] += 1
            self.stats['total_processing_time'] += final_result['processing_time']
            
            # GUI Update
            self.gui_adapter.send_agent_update(
                AgentMessageType.QUERY_COMPLETE,
                'coordinator',
                {'query_id': query_id, 'result': final_result}
            )
            
            logger.info(f"✅ Query abgeschlossen: {query_id}")
            
        except Exception as e:
            logger.error(f"❌ Query-Verarbeitung fehlgeschlagen: {query_id} - {e}")
            
            # Fehler-Ergebnis
            error_result = {
                'query_id': query_id,
                'error': str(e),
                'processing_time': time.time() - query_item['submitted_at']
            }
            
            self.result_queue.put(error_result)
            self.stats['queries_failed'] += 1
            
            # GUI Update
            self.gui_adapter.send_agent_update(
                AgentMessageType.QUERY_ERROR,
                'coordinator',
                {'query_id': query_id, 'error': str(e)}
            )
    
    def _execute_agent(self, agent_type: str, query_data: Dict[str, Any], query_id: str) -> Dict[str, Any]:
        """Führt einzelnen Agent aus"""
        agent_id = f"{agent_type}_{query_id[:8]}_{int(time.time())}"
        
        try:
            # Agent-Registry: Hole Agent-Implementation
            if self.agent_registry:
                agent_instance = self.agent_registry.get_agent_instance(agent_type)
            else:
                # Fallback: Dummy-Agent
                agent_instance = self._create_fallback_agent(agent_type)
            
            # Registriere Agent als aktiv
            with self.agent_lock:
                self.active_agents[agent_id] = {
                    'agent_type': agent_type,
                    'query_id': query_id,
                    'started_at': time.time(),
                    'status': 'running'
                }
            
            self.stats['agents_spawned'] += 1
            
            # GUI Update
            self.gui_adapter.send_agent_update(
                AgentMessageType.AGENT_SPAWNED,
                agent_id,
                {'agent_type': agent_type, 'query_id': query_id}
            )
            
            # Agent ausführen
            start_time = time.time()
            result = agent_instance.process_query(query_data, query_id)
            processing_time = time.time() - start_time
            
            # Ergebnis anreichern
            result['agent_id'] = agent_id
            result['agent_type'] = agent_type
            result['processing_time'] = processing_time
            
            # Agent als abgeschlossen markieren
            with self.agent_lock:
                if agent_id in self.active_agents:
                    self.active_agents[agent_id]['status'] = 'completed'
                    self.active_agents[agent_id]['processing_time'] = processing_time
            
            logger.info(f"✅ Agent abgeschlossen: {agent_id} ({processing_time:.2f}s)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Agent-Ausführung fehlgeschlagen: {agent_id} - {e}")
            
            # Fehler-Status setzen
            with self.agent_lock:
                if agent_id in self.active_agents:
                    self.active_agents[agent_id]['status'] = 'failed'
                    self.active_agents[agent_id]['error'] = str(e)
            
            return {
                'agent_id': agent_id,
                'agent_type': agent_type,
                'error': str(e),
                'confidence_score': 0.0
            }
        
        finally:
            # Agent-Cleanup nach kurzer Verzögerung
            def cleanup_agent():
                time.sleep(5.0)  # Kurze Verzögerung für Debugging
                with self.agent_lock:
                    if agent_id in self.active_agents:
                        del self.active_agents[agent_id]
                
                self.stats['agents_terminated'] += 1
                
                self.gui_adapter.send_agent_update(
                    AgentMessageType.AGENT_TERMINATED,
                    agent_id,
                    {'agent_type': agent_type}
                )
            
            cleanup_thread = threading.Thread(target=cleanup_agent, daemon=True)
            cleanup_thread.start()
    
    def _create_fallback_agent(self, agent_type: str):
        """Erstellt Fallback-Agent für Testing"""
        class FallbackAgent:
            def __init__(self, agent_type: str):
                self.agent_type = agent_type
            
            def process_query(self, query_data: Dict[str, Any], query_id: str) -> Dict[str, Any]:
                # Simuliere Verarbeitung
                time.sleep(0.5)
                
                return {
                    'response_text': f"Fallback-Antwort von {self.agent_type}",
                    'confidence_score': 0.3,
                    'sources': [],
                    'metadata': {'fallback': True}
                }
        
        return FallbackAgent(agent_type)
    
    def _check_agent_health(self):
        """Überprüft Gesundheit aller aktiven Agents"""
        current_time = time.time()
        agents_to_terminate = []
        
        with self.agent_lock:
            for agent_id, agent_info in self.active_agents.items():
                # Timeout-Check (Agents sollten nicht ewig laufen)
                agent_runtime = current_time - agent_info['started_at']
                
                if agent_runtime > 60.0:  # 60 Sekunden Timeout
                    logger.warning(f"⏰ Agent-Timeout: {agent_id}")
                    agents_to_terminate.append(agent_id)
                
                # Status-Update
                agent_info['runtime'] = agent_runtime
        
        # Terminiere Timeout-Agents
        for agent_id in agents_to_terminate:
            self._terminate_agent(agent_id, reason="timeout")
    
    def _handle_dynamic_scaling(self):
        """Handhabt dynamisches Agent-Scaling"""
        try:
            # Analysiere Query-Demand
            demand_analysis = self.query_analyzer.analyze_query_demand()
            
            if not demand_analysis:
                return
            
            scaling_recommendations = demand_analysis.get('scaling_recommendations', {})
            
            for agent_type, recommendation in scaling_recommendations.items():
                action = recommendation['action']
                current = recommendation['current']
                recommended = recommendation['recommended']
                
                if action == 'scale_up' and recommended > current:
                    logger.info(f"📈 Scale-Up Empfehlung: {agent_type} ({current} → {recommended})")
                    # Note: Scaling wird durch Query-Processing automatisch gehandhabt
                
                elif action == 'scale_down' and recommended < current:
                    logger.info(f"📉 Scale-Down Empfehlung: {agent_type} ({current} → {recommended})")
                    # Terminiere überschüssige idle Agents
                    self._terminate_idle_agents(agent_type, current - recommended)
            
        except Exception as e:
            logger.error(f"❌ Dynamic Scaling Fehler: {e}")
    
    def _terminate_idle_agents(self, agent_type: str, count: int):
        """Terminiert idle Agents eines bestimmten Typs"""
        terminated = 0
        
        with self.agent_lock:
            for agent_id, agent_info in list(self.active_agents.items()):
                if (agent_info['agent_type'] == agent_type and 
                    agent_info['status'] == 'idle' and 
                    terminated < count):
                    
                    self._terminate_agent(agent_id, reason="scale_down")
                    terminated += 1
    
    def _terminate_agent(self, agent_id: str, reason: str = "unknown"):
        """Terminiert einzelnen Agent"""
        with self.agent_lock:
            if agent_id in self.active_agents:
                agent_info = self.active_agents[agent_id]
                logger.info(f"🔴 Terminiere Agent: {agent_id} (Grund: {reason})")
                
                agent_info['status'] = 'terminated'
                agent_info['termination_reason'] = reason
                
                # Aus Registry entfernen nach kurzer Verzögerung
                def delayed_removal():
                    time.sleep(2.0)
                    with self.agent_lock:
                        if agent_id in self.active_agents:
                            del self.active_agents[agent_id]
                
                threading.Thread(target=delayed_removal, daemon=True).start()
    
    def _terminate_all_agents(self):
        """Terminiert alle aktiven Agents"""
        with self.agent_lock:
            agent_ids = list(self.active_agents.keys())
        
        for agent_id in agent_ids:
            self._terminate_agent(agent_id, reason="shutdown")
        
        logger.info(f"🔴 {len(agent_ids)} Agents terminiert")
    
    def _update_statistics(self):
        """Aktualisiert Agent-Statistiken"""
        with self.agent_lock:
            active_count = len([a for a in self.active_agents.values() if a['status'] == 'running'])
            idle_count = len([a for a in self.active_agents.values() if a['status'] == 'idle'])
            
            self.stats.update({
                'active_agents': active_count,
                'idle_agents': idle_count,
                'total_agents': len(self.active_agents),
                'last_update': datetime.now(timezone.utc).isoformat()
            })
    
    def get_status(self) -> Dict[str, Any]:
        """Gibt aktuellen Agent-Coordinator-Status zurück"""
        with self.agent_lock:
            active_agents_info = {
                agent_id: {
                    'agent_type': info['agent_type'],
                    'status': info['status'],
                    'runtime': time.time() - info['started_at'],
                    'query_id': info.get('query_id', 'unknown')
                }
                for agent_id, info in self.active_agents.items()
            }
        
        return {
            'is_running': self.is_running,
            'stats': self.stats.copy(),
            'active_agents': active_agents_info,
            'query_queue_size': self.query_queue.qsize(),
            'result_queue_size': self.result_queue.qsize(),
            'configuration': {
                'max_concurrent_agents': self.max_concurrent_agents,
                'check_interval': self.check_interval,
                'dynamic_scaling': self.enable_dynamic_scaling
            }
        }

# === FACTORY FUNCTIONS ===

def create_agent_coordinator(gui_queue: queue.Queue = None, 
                           check_interval: float = 2.0, 
                           orchestrator=None, 
                           pipeline_manager=None,
                           database_api=None,
                           uds3_strategy=None) -> AgentCoordinator:
    """
    Factory für AgentCoordinator-Erstellung
    
    Args:
        gui_queue: Queue für GUI-Updates
        check_interval: Agent-Monitor-Intervall
        orchestrator: Agent-Orchestrator-Instanz
        pipeline_manager: Agent-Pipeline-Manager
        database_api: RAG Database API
        uds3_strategy: Unified Database Strategy
        
    Returns:
        AgentCoordinator-Instanz
    """
    return AgentCoordinator(
        gui_queue=gui_queue,
        check_interval=check_interval,
        orchestrator=orchestrator,
        pipeline_manager=pipeline_manager,
        database_api=database_api,
        uds3_strategy=uds3_strategy
    )

# === LEGACY COMPATIBILITY ===

class LegacyAgentCoordinatorWrapper:
    """Legacy-Wrapper für alte API-Kompatibilität"""
    
    def __init__(self, agent_coordinator: AgentCoordinator):
        self.agent_coordinator = agent_coordinator
    
    def process_query_sync(self, query: str, timeout: float = 30.0) -> Dict[str, Any]:
        """Synchrone Query-Verarbeitung (Legacy)"""
        query_data = {'query': query}
        query_id = self.agent_coordinator.submit_query(query_data)
        return self.agent_coordinator.get_query_result(query_id, timeout)

if __name__ == "__main__":
    # Test-Setup
    coordinator = create_agent_coordinator()
    coordinator.start()
    
    try:
        # Test-Query
        query_id = coordinator.submit_query({'query': 'Was sind die Bauvorschriften in München?'})
        result = coordinator.get_query_result(query_id, timeout=10.0)
        
        print(f"Query Result: {result}")
        print(f"Coordinator Status: {coordinator.get_status()}")
        
    finally:
        coordinator.stop()