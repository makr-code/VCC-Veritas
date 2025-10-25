#!/usr/bin/env python3
"""
VERITAS AGENT REGISTRY SYSTEM
=============================

Dezentrales Agent-Registry-System für selbstregistrierende Agents
mit geteilten Ressourcen und automatischer Integration

ARCHITEKTUR:
• Agents registrieren sich selbst mit ihren Capabilities  
• Shared Database Connection Pool für alle Agents
• Plugin-ähnliche Architektur für dynamisches Laden
• Reduziert DB-Connection-Overhead durch Resource-Sharing

AGENT-TYPEN (basierend auf hypothetischen Queries):
• Core Agents: geo_context, legal_framework, document_retrieval, timeline
• Domain Agents: environmental, building, transport, social, business, taxation
• Processing Agents: preprocessor, postprocessor, aggregator, quality_assessor
• Integration Agents: ollama_llm, external_api, database_connector

INTEGRATION:
AgentCoordinator → AgentRegistry → Shared Resources → Individual Agents

Author: VERITAS System (Based on ingestion_core_worker_registry.py)
Date: 2025-09-21
Version: 1.0 (Agent-driven)
"""

import logging
import os
import threading
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Type, Set
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import queue
import importlib
from importlib.util import find_spec as _find_spec

# ========================================
# AGENT INSTANCE CAPS (Soft Cap Mechanismus)
# ========================================
# Ziele:
#  * Begrenze parallele Instanzen pro Agent-Typ
#  * Verhindere übermäßiges Autoscaling (Skew) – insbesondere llm/backend
#  * ENV Override Priorität > JSON-Konfiguration > vordefinierte Defaults > Registration Default (1)
#  * Soft Cap: Existierende Überhänge werden nicht sofort reduziert, nur weitere Spawns blockiert
#  * Transparente Diagnostics via get_cap_status()

CAP_ENV_PREFIX = "VERITAS_AGENT_CAP_"
DEFAULT_AGENT_CAPS = {
    'llm': 2,           # LLM Agents sind ressourcenintensiv
    'geo_context': 3,   # Geo-Context in 73% der Queries benötigt
    'legal_framework': 2, # Legal Framework in 60% der Queries
    'document_retrieval': 4, # RAG-basierte Dokumentensuche
    'environmental': 2,
    'building': 2,
    'transport': 2,
    'social': 2,
    'business': 2,
    'taxation': 1,      # Weniger häufig, aber ressourcenintensiv
    'external_api': 3,  # Multi-Source Integration
}

# Shared Resources (analog zu ingestion_core_worker_registry)
# ============================================================================
# RAG Database Integration - REQUIRED (NO FALLBACK)
# ============================================================================
from uds3.core import UDS3PolyglotManager  # ✨ UDS3 v2.0.0 (Legacy stable)

# Ollama Integration
try:
    from native_ollama_integration import DirectOllamaLLM, DirectOllamaEmbeddings
    _ollama_available = True
except Exception:
    _ollama_available = False

logger = logging.getLogger(__name__)

# Sanitize all log messages to ASCII (analog zu Worker Registry)
class _AsciiLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = record.msg.encode('ascii', 'replace').decode('ascii')
            if record.args:
                new_args = []
                for a in record.args:
                    if isinstance(a, str):
                        new_args.append(a.encode('ascii', 'replace').decode('ascii'))
                    else:
                        new_args.append(a)
                record.args = tuple(new_args)
        except Exception:
            pass
        return True

if not any(isinstance(f, _AsciiLogFilter) for f in logger.filters):
    logger.addFilter(_AsciiLogFilter())

# ========================================
# AGENT CAPABILITY DEFINITIONS
# ========================================

class AgentCapability(Enum):
    """Agent-Capabilities basierend auf hypothetischen Query-Analysen"""
    
    # Standard Capabilities (All Agents)
    QUERY_PROCESSING = "query_processing"                      # Standard für alle Agents
    DATA_ANALYSIS = "data_analysis"                            # Datenanalyse
    
    # Core Capabilities (Layer 1: Context Resolution Engine)
    GEO_CONTEXT_RESOLUTION = "geo_context_resolution"           # 73% der Queries
    TEMPORAL_ANALYSIS = "temporal_analysis"                     # 37% der Queries
    DOMAIN_CLASSIFICATION = "domain_classification"            # 100% der Queries
    JURISDICTION_MAPPING = "jurisdiction_mapping"              # 80% der Queries
    
    # Legal & Regulatory (Layer 3: Cross-Domain Intelligence)
    LEGAL_FRAMEWORK_ANALYSIS = "legal_framework_analysis"      # 60% der Queries
    COMPLIANCE_CHECKING = "compliance_checking"
    PROCESS_GUIDANCE = "process_guidance"                      # 47% der Queries
    
    # RAG & Knowledge (Layer 2: Domain-Specific Workers)
    DOCUMENT_RETRIEVAL = "document_retrieval"
    SEMANTIC_SEARCH = "semantic_search"
    KNOWLEDGE_SYNTHESIS = "knowledge_synthesis"
    
    # Domain-Specific Processing
    ENVIRONMENTAL_DATA_PROCESSING = "environmental_data"       # BImSchG, Umweltdaten
    BUILDING_PERMIT_PROCESSING = "building_permit"            # Baugenehmigungen
    TRANSPORT_DATA_PROCESSING = "transport_data"              # ÖPNV, Verkehr
    SOCIAL_SERVICES_PROCESSING = "social_services"            # Kita, Pflege, Sozial
    BUSINESS_LICENSE_PROCESSING = "business_license"          # Gewerbe, Genehmigungen
    TAXATION_PROCESSING = "taxation"                          # Steuern, Abgaben
    
    # External Integration
    EXTERNAL_API_INTEGRATION = "external_api"                 # 50% der Queries
    REAL_TIME_DATA_ACCESS = "real_time_data"
    REAL_TIME_PROCESSING = "real_time_processing"             # Echtzeit-Datenverarbeitung
    MULTI_SOURCE_SYNTHESIS = "multi_source_synthesis"
    
    # Analysis & Intelligence
    FINANCIAL_IMPACT_ANALYSIS = "financial_impact"            # 40% der Queries
    SUCCESS_PROBABILITY_ESTIMATION = "success_probability"
    TIMELINE_PREDICTION = "timeline_prediction"
    IMPACT_ASSESSMENT = "impact_assessment"                   # 33% der Queries
    
    # Response Generation (Layer 4)
    STRUCTURED_RESPONSE_GENERATION = "structured_response"
    ACTION_PLANNING = "action_planning"                       # 47% der Queries
    ALTERNATIVE_SUGGESTION = "alternative_suggestion"

class AgentLifecycleType(Enum):
    """Agent-Lifecycle-Typen"""
    PERSISTENT = "persistent"      # Langlebige Agents für häufige Tasks
    ON_DEMAND = "on_demand"       # Werden bei Bedarf erstellt
    SINGLETON = "singleton"       # Nur eine Instanz pro System
    POOLED = "pooled"            # Pool von wiederverwendbaren Instanzen

class AgentStatus(Enum):
    """Agent-Status-Werte"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING_FOR_DATA = "waiting_for_data"
    ERROR = "error"
    TERMINATED = "terminated"
    STARTING = "starting"

# ========================================
# AGENT DATASTRUCTURES
# ========================================

@dataclass
class AgentCapabilityInfo:
    """Information über Agent-Capability"""
    capability: AgentCapability
    processing_time_estimate: float  # Geschätzte Verarbeitungszeit in Sekunden
    resource_requirements: Dict[str, Any]  # CPU, Memory, External APIs
    confidence_level: float  # Vertrauensniveau für diese Capability
    data_sources: List[str]  # Benötigte Datenquellen
    dependencies: List[AgentCapability] = field(default_factory=list)

@dataclass
class AgentRegistration:
    """Agent-Registrierungsinformationen"""
    agent_id: str
    agent_type: str
    agent_class: Type
    capabilities: Set[AgentCapability]
    lifecycle_type: AgentLifecycleType
    max_concurrent_instances: int = 1
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    description: str = ""
    
    # Runtime Information
    active_instances: Dict[str, Any] = field(default_factory=dict)
    total_instances_created: int = 0
    total_queries_processed: int = 0
    average_processing_time: float = 0.0
    last_activity: Optional[str] = None

@dataclass
class AgentInstance:
    """Laufende Agent-Instanz"""
    instance_id: str
    agent_registration: AgentRegistration
    agent_object: Any
    status: AgentStatus
    current_query_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: time.time())
    last_activity: str = field(default_factory=lambda: time.time())
    processing_statistics: Dict[str, Any] = field(default_factory=dict)

# ========================================
# SHARED RESOURCE POOL
# ========================================

class SharedResourcePool:
    """Geteilte Ressourcen für alle Agents"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._database_api = None
        self._uds3_strategy = None
        self._ollama_llm = None
        self._ollama_embeddings = None
        self._external_api_cache = {}
        
        # Resource Usage Statistics
        self.resource_usage_stats = {
            'database_connections': 0,
            'ollama_requests': 0,
            'external_api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        logger.info("🔧 Shared Resource Pool initialisiert")
    
    def get_database_api(self):
        """Liefert geteilte Database API Instanz"""
        with self._lock:
            if not self._database_api and _database_api_available:
                try:
                    self._database_api = MultiDatabaseAPI()
                    # ✨ NEU: UDS3 v2.0.0 Polyglot Manager
                    backend_config = {
                        "vector": {"enabled": True, "backend": "chromadb"},
                        "graph": {"enabled": False},
                        "relational": {"enabled": False},
                        "file_storage": {"enabled": False}
                    }
                    self._uds3_strategy = UDS3PolyglotManager(
                        backend_config=backend_config,
                        enable_rag=True
                    )
                    logger.info("✅ Database API + UDS3 Polyglot Manager für Agents verfügbar")
                except Exception as e:
                    logger.error(f"❌ Database API Initialisierung fehlgeschlagen: {e}")
            
            self.resource_usage_stats['database_connections'] += 1
            return self._database_api, self._uds3_strategy
    
    def get_ollama_llm(self, model: str = "llama3.1:8b"):
        """Liefert geteilte Ollama LLM Instanz"""
        with self._lock:
            if not self._ollama_llm and _ollama_available:
                try:
                    self._ollama_llm = DirectOllamaLLM(model=model)
                    logger.info(f"✅ Ollama LLM für Agents verfügbar: {model}")
                except Exception as e:
                    logger.error(f"❌ Ollama LLM Initialisierung fehlgeschlagen: {e}")
            
            self.resource_usage_stats['ollama_requests'] += 1
            return self._ollama_llm
    
    def get_ollama_embeddings(self, model: str = "llama3.1:8b"):
        """Liefert geteilte Ollama Embeddings Instanz"""
        with self._lock:
            if not self._ollama_embeddings and _ollama_available:
                try:
                    self._ollama_embeddings = DirectOllamaEmbeddings(model=model)
                    logger.info(f"✅ Ollama Embeddings für Agents verfügbar: {model}")
                except Exception as e:
                    logger.error(f"❌ Ollama Embeddings Initialisierung fehlgeschlagen: {e}")
                    
            return self._ollama_embeddings
    
    def cache_external_api_result(self, cache_key: str, result: Any, ttl: int = 300):
        """Cached externe API-Ergebnisse"""
        with self._lock:
            self._external_api_cache[cache_key] = {
                'result': result,
                'cached_at': time.time(),
                'ttl': ttl
            }
            self.resource_usage_stats['cache_hits'] += 1
    
    def get_cached_external_api_result(self, cache_key: str) -> Optional[Any]:
        """Holt gecachte externe API-Ergebnisse"""
        with self._lock:
            if cache_key in self._external_api_cache:
                cache_entry = self._external_api_cache[cache_key]
                
                # TTL Check
                if time.time() - cache_entry['cached_at'] < cache_entry['ttl']:
                    self.resource_usage_stats['cache_hits'] += 1
                    return cache_entry['result']
                else:
                    # Expired - remove
                    del self._external_api_cache[cache_key]
            
            self.resource_usage_stats['cache_misses'] += 1
            return None
    
    def get_resource_usage_stats(self) -> Dict[str, Any]:
        """Liefert Ressourcen-Nutzungsstatistiken"""
        with self._lock:
            return self.resource_usage_stats.copy()

# ========================================
# AGENT REGISTRY
# ========================================

class AgentRegistry:
    """
    Zentrales Agent-Registry für selbstregistrierende Agents
    Analog zu ingestion_core_worker_registry.WorkerRegistry
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._registrations: Dict[str, AgentRegistration] = {}
        self._capability_map: Dict[AgentCapability, List[str]] = {}
        self._shared_resources = SharedResourcePool()
        
        # Instance Management
        self._active_instances: Dict[str, AgentInstance] = {}
        self._instance_pools: Dict[str, List[AgentInstance]] = {}
        
        # Statistics
        self.registry_stats = {
            'registered_agents': 0,
            'active_instances': 0,
            'total_queries_processed': 0,
            'average_response_time': 0.0
        }
        
        logger.info("🎯 Agent Registry initialisiert")
    
    def register_agent(self, 
                      agent_type: str,
                      agent_class: Type,
                      capabilities: Set[AgentCapability],
                      lifecycle_type: AgentLifecycleType = AgentLifecycleType.ON_DEMAND,
                      max_concurrent_instances: int = None,
                      priority: int = 1,
                      description: str = "") -> bool:
        """
        Registriert einen neuen Agent-Typ
        
        Args:
            agent_type: Eindeutiger Agent-Typ (z.B. "geo_context", "legal_framework")
            agent_class: Agent-Klasse (muss process_query Methode haben)
            capabilities: Set von AgentCapabilities
            lifecycle_type: Lifecycle-Management-Strategie
            max_concurrent_instances: Maximale parallele Instanzen
            priority: Priorität bei Agent-Selektion
            description: Beschreibung der Agent-Funktionalität
            
        Returns:
            bool: True wenn Registrierung erfolgreich
        """
        
        with self._lock:
            # Cap-Logik (analog zu Worker Registry)
            if max_concurrent_instances is None:
                # Environment Variable Check
                env_cap = os.getenv(f"{CAP_ENV_PREFIX}{agent_type.upper()}")
                if env_cap:
                    try:
                        max_concurrent_instances = int(env_cap)
                        logger.info(f"🔧 Agent Cap aus ENV: {agent_type} = {max_concurrent_instances}")
                    except ValueError:
                        logger.warning(f"⚠️ Ungültiger ENV Cap-Wert: {env_cap}")
                
                # Default Cap Lookup
                if max_concurrent_instances is None:
                    max_concurrent_instances = DEFAULT_AGENT_CAPS.get(agent_type, 1)
            
            # Agent-Registrierung erstellen
            registration = AgentRegistration(
                agent_id=f"agent_{agent_type}_{int(time.time())}",
                agent_type=agent_type,
                agent_class=agent_class,
                capabilities=capabilities,
                lifecycle_type=lifecycle_type,
                max_concurrent_instances=max_concurrent_instances,
                priority=priority,
                description=description
            )
            
            # In Registry eintragen
            self._registrations[agent_type] = registration
            
            # Capability-Map aktualisieren
            for capability in capabilities:
                if capability not in self._capability_map:
                    self._capability_map[capability] = []
                self._capability_map[capability].append(agent_type)
            
            # Pool initialisieren (für POOLED Lifecycle)
            if lifecycle_type == AgentLifecycleType.POOLED:
                self._instance_pools[agent_type] = []
            
            self.registry_stats['registered_agents'] += 1
            
            logger.info(f"✅ Agent registriert: {agent_type} (Cap: {max_concurrent_instances}, Capabilities: {len(capabilities)})")
            return True
    
    def get_agents_for_capability(self, capability: AgentCapability) -> List[str]:
        """
        Liefert alle Agent-Typen die eine bestimmte Capability unterstützen
        
        Args:
            capability: Gesuchte Agent-Capability
            
        Returns:
            List[str]: Liste von Agent-Typen
        """
        with self._lock:
            return self._capability_map.get(capability, []).copy()
    
    def get_agent_instance(self, agent_type: str, query_id: str = None) -> Optional[Any]:
        """
        Holt oder erstellt Agent-Instanz
        
        Args:
            agent_type: Agent-Typ
            query_id: Optional Query-ID für Tracking
            
        Returns:
            Agent-Instanz oder None wenn nicht verfügbar
        """
        with self._lock:
            if agent_type not in self._registrations:
                logger.warning(f"⚠️ Unbekannter Agent-Typ: {agent_type}")
                return None
            
            registration = self._registrations[agent_type]
            
            # Cap-Check
            active_count = len([inst for inst in self._active_instances.values() 
                              if inst.agent_registration.agent_type == agent_type])
            
            if active_count >= registration.max_concurrent_instances:
                logger.warning(f"⚠️ Agent Cap erreicht: {agent_type} ({active_count}/{registration.max_concurrent_instances})")
                return None
            
            # Lifecycle-spezifische Instanz-Erstellung
            instance = self._create_agent_instance(registration, query_id)
            
            if instance:
                self._active_instances[instance.instance_id] = instance
                self.registry_stats['active_instances'] += 1
                logger.info(f"🚀 Agent-Instanz erstellt: {instance.instance_id}")
                
                return instance.agent_object
            
            return None
    
    def _create_agent_instance(self, registration: AgentRegistration, query_id: str = None) -> Optional[AgentInstance]:
        """Erstellt neue Agent-Instanz"""
        try:
            # Agent-Objekt instanziieren
            agent_object = registration.agent_class()
            
            # Shared Resources injizieren
            if hasattr(agent_object, 'set_shared_resources'):
                agent_object.set_shared_resources(self._shared_resources)
            
            # Instanz-Wrapper erstellen
            instance_id = f"{registration.agent_type}_{int(time.time())}_{id(agent_object)}"
            
            instance = AgentInstance(
                instance_id=instance_id,
                agent_registration=registration,
                agent_object=agent_object,
                status=AgentStatus.IDLE,
                current_query_id=query_id
            )
            
            registration.total_instances_created += 1
            
            return instance
            
        except Exception as e:
            logger.error(f"❌ Agent-Instanz-Erstellung fehlgeschlagen: {registration.agent_type} - {e}")
            return None
    
    def release_agent_instance(self, instance_id: str):
        """Gibt Agent-Instanz frei"""
        with self._lock:
            if instance_id in self._active_instances:
                instance = self._active_instances[instance_id]
                
                # Lifecycle-spezifisches Cleanup
                if instance.agent_registration.lifecycle_type == AgentLifecycleType.POOLED:
                    # Zurück in Pool
                    instance.status = AgentStatus.IDLE
                    instance.current_query_id = None
                    
                    agent_type = instance.agent_registration.agent_type
                    if agent_type in self._instance_pools:
                        self._instance_pools[agent_type].append(instance)
                else:
                    # Instance terminieren
                    instance.status = AgentStatus.TERMINATED
                
                del self._active_instances[instance_id]
                self.registry_stats['active_instances'] -= 1
                
                logger.info(f"🔄 Agent-Instanz freigegeben: {instance_id}")
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Liefert aktuellen Registry-Status"""
        with self._lock:
            agent_summary = {}
            
            for agent_type, registration in self._registrations.items():
                active_count = len([inst for inst in self._active_instances.values() 
                                  if inst.agent_registration.agent_type == agent_type])
                
                agent_summary[agent_type] = {
                    'capabilities': [cap.value for cap in registration.capabilities],
                    'lifecycle_type': registration.lifecycle_type.value,
                    'max_concurrent': registration.max_concurrent_instances,
                    'active_instances': active_count,
                    'total_created': registration.total_instances_created,
                    'total_processed': registration.total_queries_processed,
                    'priority': registration.priority
                }
            
            return {
                'registry_stats': self.registry_stats.copy(),
                'agents': agent_summary,
                'capability_map': {cap.value: agents for cap, agents in self._capability_map.items()},
                'resource_usage': self._shared_resources.get_resource_usage_stats(),
                'active_instances': len(self._active_instances)
            }
    
    def auto_discover_agents(self, module_patterns: List[str] = None) -> int:
        """
        Automatische Agent-Entdeckung in veritas_api_agent_*.py Modulen
        
        Args:
            module_patterns: Liste von Modul-Patterns (default: veritas_api_agent_*)
            
        Returns:
            int: Anzahl entdeckter und registrierter Agents
        """
        if module_patterns is None:
            module_patterns = ["veritas_api_agent_*"]
        
        discovered_count = 0
        
        for pattern in module_patterns:
            try:
                # Finde passende Module
                import glob
                import sys
                
                # Search in current directory and Python path
                search_paths = [os.getcwd()] + sys.path
                
                for search_path in search_paths:
                    module_files = glob.glob(os.path.join(search_path, f"{pattern}.py"))
                    
                    for module_file in module_files:
                        module_name = os.path.basename(module_file)[:-3]  # Remove .py
                        
                        if module_name.startswith('veritas_api_agent_'):
                            try:
                                # Versuche Modul zu importieren
                                spec = _find_spec(module_name)
                                if spec and spec.loader:
                                    module = importlib.import_module(module_name)
                                    
                                    # Suche nach Agent-Klassen und Registry-Funktionen
                                    if hasattr(module, 'register_agents'):
                                        count = module.register_agents(self)
                                        discovered_count += count
                                        logger.info(f"✅ Auto-discovered {count} agents from {module_name}")
                                    
                            except Exception as e:
                                logger.warning(f"⚠️ Fehler beim Laden von {module_name}: {e}")
                
            except Exception as e:
                logger.error(f"❌ Auto-Discovery-Fehler für Pattern {pattern}: {e}")
        
        logger.info(f"🔍 Auto-Discovery abgeschlossen: {discovered_count} Agents entdeckt")
        return discovered_count

# ========================================
# GLOBAL REGISTRY INSTANCE
# ========================================

_global_agent_registry: Optional[AgentRegistry] = None
_registry_lock = threading.RLock()

def get_agent_registry() -> AgentRegistry:
    """
    Liefert globale Agent-Registry-Instanz (Singleton Pattern)
    
    Returns:
        AgentRegistry: Globale Registry-Instanz
    """
    global _global_agent_registry
    
    with _registry_lock:
        if _global_agent_registry is None:
            _global_agent_registry = AgentRegistry()
            
            # Auto-Discovery ausführen
            try:
                discovered = _global_agent_registry.auto_discover_agents()
                logger.info(f"🎯 Agent Registry initialisiert mit {discovered} auto-discovered Agents")
            except Exception as e:
                logger.warning(f"⚠️ Auto-Discovery fehlgeschlagen: {e}")
        
        return _global_agent_registry

# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

def register_agent_type(agent_type: str, 
                       agent_class: Type,
                       capabilities: Set[AgentCapability],
                       **kwargs) -> bool:
    """
    Convenience-Funktion für Agent-Registrierung
    
    Args:
        agent_type: Agent-Typ
        agent_class: Agent-Klasse
        capabilities: Agent-Capabilities
        **kwargs: Weitere Parameter für register_agent
        
    Returns:
        bool: True wenn erfolgreich registriert
    """
    registry = get_agent_registry()
    return registry.register_agent(agent_type, agent_class, capabilities, **kwargs)

def get_agent_for_capability(capability: AgentCapability) -> Optional[Any]:
    """
    Convenience-Funktion um Agent für bestimmte Capability zu holen
    
    Args:
        capability: Gesuchte Capability
        
    Returns:
        Agent-Instanz oder None
    """
    registry = get_agent_registry()
    agent_types = registry.get_agents_for_capability(capability)
    
    if agent_types:
        # Nimm ersten verfügbaren Agent (könnte durch Priorität erweitert werden)
        return registry.get_agent_instance(agent_types[0])
    
    return None

if __name__ == "__main__":
    # Test der Agent Registry
    registry = get_agent_registry()
    status = registry.get_registry_status()
    
    print(f"Agent Registry Status:")
    print(f"Registered Agents: {status['registry_stats']['registered_agents']}")
    print(f"Active Instances: {status['registry_stats']['active_instances']}")
    print(f"Available Capabilities: {len(status['capability_map'])}")