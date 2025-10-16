#!/usr/bin/env python3
"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "covina_module_manager_enhanced"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...OU8AhQ=="  # Gekuerzt fuer Sicherheit
module_organization_key = "7d9a9d7d59677dbeb3b6aa3fefe4224aea1c846b7329b9b83b18ad134707fa6d"
module_file_key = "52cf02e5b58590419089e065d7b7be9b1d1abc0936ca599d9feb5d50b1bdbf60"
module_version = "2.0"
module_protection_level = 1
# === END PROTECTION KEYS ===
"""
COVINA Module Manager - Enhanced Agent System
Koordiniert alle Covina-Module und deren Interaktionen
Enhanced with Agent-Engine Integration and External Data Sources
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configure logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# VERITAS Agent Engine Integration
try:
    from covina_core import CovinaAgentEngine, get_agent_engine, WorkerType
    from covina_base import BaseWorker, ExternalAPIWorker, DatabaseWorker, EULexWorker, GoogleSearchWorker
    AGENT_ENGINE_AVAILABLE = True
    logging.info("✅ Agent Engine Integration verfügbar")
except ImportError as e:
    AGENT_ENGINE_AVAILABLE = False
    logging.warning(f"⚠️ Agent Engine nicht verfügbar: {e}")

# UDS3 Integration
try:
    from uds3.uds3_admin_types import AdminDocumentType, AdminLevel, AdminDomain
    from uds3.uds3_document_classifier import classify_document_by_content
    UDS3_AVAILABLE = True
except ImportError as e:
    logging.error(f"UDS3 Integration nicht verfügbar: {e}")
    UDS3_AVAILABLE = False

# Covina Module Imports (Optional) - Kommentiert aus bis Module verfügbar sind
GUI_COMPONENTS_AVAILABLE = False
# try:
#     from covina_gui_components import (
#         SplitButton, Tooltip, StatusBar, 
#         FileTreeView, ProgressDialog
#     )
#     GUI_COMPONENTS_AVAILABLE = True
# except ImportError:
#     logging.warning("⚠️ GUI Components nicht verfügbar - Fallback-Modus")

SCRAPER_DIALOG_AVAILABLE = False
# try:
#     from covina_scraper_dialog import (
#         WebsiteScrapingDialog, ScrapingProgressDialog,
#         CovinaWebsiteProcessor
#     )
#     SCRAPER_DIALOG_AVAILABLE = True
# except ImportError:
#     logging.warning("⚠️ Scraper Dialog nicht verfügbar - Fallback-Modus")

FILE_MANAGER_AVAILABLE = False
try:
    from covina_file_manager import (
        CovinaFileManager, CovinaConfigManager
    )
    FILE_MANAGER_AVAILABLE = True
except ImportError:
    logging.warning("⚠️ File Manager nicht verfügbar - Fallback-Modus")

THEME_MANAGER_AVAILABLE = False
# try:
#     from covina_theme_manager import CovinaThemeManager
#     THEME_MANAGER_AVAILABLE = True
# except ImportError:
#     logging.warning("⚠️ Theme Manager nicht verfügbar - Fallback-Modus")

PROCESS_MINING_AVAILABLE = False
try:
    from uds3.uds3_process_mining import ProcessComplexityAnalyzer, ProcessWorkflowExtractor
    PROCESS_MINING_AVAILABLE = True
except ImportError:
    logging.warning("⚠️ Process Mining nicht verfügbar - Fallback-Modus")

# Module-Verfügbarkeit zusammenfassen
COVINA_MODULES_AVAILABLE = any([
    GUI_COMPONENTS_AVAILABLE,
    SCRAPER_DIALOG_AVAILABLE, 
    FILE_MANAGER_AVAILABLE,
    THEME_MANAGER_AVAILABLE,
    PROCESS_MINING_AVAILABLE
])

# External Data Sources Configuration
EXTERNAL_DATA_CONFIG = {
    "eu_lex": {
        "enabled": True,
        "base_url": "https://eur-lex.europa.eu/",
        "cache_ttl": 3600
    },
    "google_search": {
        "enabled": False,  # Benötigt API-Key
        "api_key": None,
        "search_engine_id": None,
        "cache_ttl": 1800
    },
    "sql_databases": {
        "legal_db": {
            "type": "sqlite",
            "path": "sqlite_db/legal_data.db",
            "enabled": False
        },
        "admin_db": {
            "type": "postgresql", 
            "host": "localhost",
            "port": 5432,
            "database": "admin_data",
            "user": None,
            "password": None,
            "enabled": False
        }
    }
}

# =============================================================================
# ENHANCED AGENT WORKERS
# =============================================================================

class DocumentRetrievalWorker(BaseWorker):
    """Worker für interne Dokumentensuche (VERITAS Datenbank)"""
    
    def __init__(self):
        from covina_core import WorkerType
        super().__init__(WorkerType.DOCUMENT_RETRIEVAL, cache_ttl=300)  # 5 Minuten Cache
        
        # Integration mit bestehendem VERITAS RAG
        try:
            from covina_module_native import answer_query
            self.rag_function = answer_query
            self.rag_available = True
        except ImportError:
            self.rag_available = False
            logging.warning("⚠️ VERITAS RAG nicht verfügbar in DocumentRetrievalWorker")
    
    async def _process_internal(self, metadata, user_profile: Dict = None) -> Dict[str, Any]:
        """Führt interne Dokumentensuche durch"""
        
        if not self.rag_available:
            return {
                "retrieved_docs": [],
                "summary": "VERITAS RAG nicht verfügbar",
                "confidence_score": 0.0
            }
        
        try:
            # Führe Standard VERITAS RAG aus
            session_id = f"agent_{metadata.query_id}"
            rag_result = self.rag_function(
                session_id=session_id,
                query=metadata.original_query,
                user_profile=user_profile or {},
                model_name="llama3:latest",
                temperature=0.7
            )
            
            # Extrahiere Dokumente
            retrieved_docs = []
            if 'retrieved_chunks' in rag_result:
                for chunk in rag_result['retrieved_chunks'][:10]:  # Max 10 Dokumente
                    retrieved_docs.append({
                        "content": chunk.get('content', ''),
                        "metadata": chunk.get('metadata', {}),
                        "score": chunk.get('score', 0.0),
                        "source": "veritas_db"
                    })
            
            return {
                "retrieved_docs": retrieved_docs,
                "summary": f"VERITAS DB: {len(retrieved_docs)} Dokumente gefunden",
                "confidence_score": min(0.9, rag_result.get('confidence_score', 0.5)),
                "rag_answer": rag_result.get('answer', ''),
                "sources": [{"type": "veritas_database", "count": len(retrieved_docs)}]
            }
            
        except Exception as e:
            logging.error(f"❌ DocumentRetrievalWorker Error: {e}")
            return {
                "retrieved_docs": [],
                "summary": f"Dokumentensuche fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }

class GeoContextWorker(BaseWorker):
    """Worker für geografischen Kontext und Zuständigkeiten"""
    
    def __init__(self):
        from covina_core import WorkerType
        super().__init__(WorkerType.GEO_CONTEXT, cache_ttl=1800)  # 30 Minuten Cache
    
    async def _process_internal(self, metadata, user_profile: Dict = None) -> Dict[str, Any]:
        """Analysiert geografischen Kontext"""
        
        # Extrahiere Ortsangaben
        locations = self._extract_locations(metadata.normalized_query)
        
        if not locations:
            return {
                "locations": [],
                "authorities": [],
                "summary": "Keine geografischen Angaben gefunden",
                "confidence_score": 0.1
            }
        
        try:
            # Mock Geo-Kontext-Analyse
            geo_data = await self._analyze_geo_context(locations)
            
            return {
                "locations": locations,
                "authorities": geo_data.get("authorities", []),
                "jurisdiction": geo_data.get("jurisdiction", ""),
                "summary": f"Geografischer Kontext für: {', '.join(locations)}",
                "confidence_score": 0.8,
                "sources": [{"type": "geo_analysis", "locations": len(locations)}]
            }
            
        except Exception as e:
            logging.error(f"❌ GeoContextWorker Error: {e}")
            return {
                "locations": locations,
                "authorities": [],
                "summary": f"Geo-Analyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _extract_locations(self, query: str) -> List[str]:
        """Extrahiert Ortsangaben aus Query"""
        # Vereinfachte Ortserkennung
        location_indicators = []
        words = query.split()
        
        for i, word in enumerate(words):
            # Suche nach Straßenangaben
            if "straße" in word.lower() or "str." in word.lower():
                if i > 0:
                    location_indicators.append(f"{words[i-1]} {word}")
            
            # Suche nach Städtenamen (vereinfacht)
            city_patterns = ["berlin", "münchen", "hamburg", "köln", "frankfurt"]
            if word.lower() in city_patterns:
                location_indicators.append(word.title())
        
        return location_indicators
    
    async def _analyze_geo_context(self, locations: List[str]) -> Dict[str, Any]:
        """Analysiert geografischen Kontext"""
        import asyncio
        await asyncio.sleep(0.3)  # Simuliere Verarbeitung
        
        # Mock-Analyse
        authorities = []
        jurisdiction = ""
        
        for location in locations:
            if "berlin" in location.lower():
                authorities.append({
                    "name": "Bezirksamt Berlin",
                    "type": "Bezirksverwaltung",
                    "contact": "https://service.berlin.de"
                })
                jurisdiction = "Land Berlin"
            elif "münchen" in location.lower():
                authorities.append({
                    "name": "Landeshauptstadt München",
                    "type": "Stadtverwaltung", 
                    "contact": "https://www.muenchen.de"
                })
                jurisdiction = "Bayern"
        
        return {
            "authorities": authorities,
            "jurisdiction": jurisdiction
        }

class LegalFrameworkWorker(BaseWorker):
    """Worker für rechtliche Rahmenanalyse"""
    
    def __init__(self):
        from covina_core import WorkerType
        super().__init__(WorkerType.LEGAL_FRAMEWORK, cache_ttl=3600)  # 1 Stunde Cache
    
    async def _process_internal(self, metadata, user_profile: Dict = None) -> Dict[str, Any]:
        """Analysiert rechtlichen Rahmen"""
        
        try:
            # Identifiziere relevante Rechtsbereiche
            legal_areas = self._identify_legal_areas(metadata.normalized_query, metadata.domains)
            
            # Identifiziere relevante Gesetze
            relevant_laws = await self._identify_relevant_laws(metadata.normalized_query, legal_areas)
            
            return {
                "legal_areas": legal_areas,
                "relevant_laws": relevant_laws,
                "summary": f"Rechtlicher Rahmen: {', '.join(legal_areas)}",
                "confidence_score": 0.85 if legal_areas else 0.3,
                "sources": [{"type": "legal_analysis", "laws": len(relevant_laws)}]
            }
            
        except Exception as e:
            logging.error(f"❌ LegalFrameworkWorker Error: {e}")
            return {
                "legal_areas": [],
                "relevant_laws": [],
                "summary": f"Rechtsanalyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _identify_legal_areas(self, query: str, domains: List[str]) -> List[str]:
        """Identifiziert relevante Rechtsbereiche"""
        legal_areas = []
        
        # Domain-basierte Zuordnung
        domain_mapping = {
            "baurecht": ["Bauplanungsrecht", "Bauordnungsrecht"],
            "umweltrecht": ["Immissionsschutzrecht", "Gewässerschutzrecht", "Abfallrecht"],
            "steuerrecht": ["Einkommensteuerrecht", "Umsatzsteuerrecht", "Gewerbesteuerrecht"],
            "verkehrsrecht": ["Straßenverkehrsrecht", "Straßenrecht"]
        }
        
        for domain in domains:
            if domain in domain_mapping:
                legal_areas.extend(domain_mapping[domain])
        
        # Keyword-basierte Erkennung
        if "genehmigung" in query:
            legal_areas.append("Verwaltungsverfahrensrecht")
        if "umwelt" in query:
            legal_areas.append("Umweltrecht")
        
        return list(set(legal_areas))  # Duplikate entfernen
    
    async def _identify_relevant_laws(self, query: str, legal_areas: List[str]) -> List[Dict[str, str]]:
        """Identifiziert relevante Gesetze"""
        import asyncio
        await asyncio.sleep(0.2)  # Simuliere Verarbeitung
        
        laws = []
        
        # Mock Gesetzeszuordnung
        law_mapping = {
            "Bauplanungsrecht": [
                {"name": "Baugesetzbuch (BauGB)", "key_provisions": "§§ 29-37 (Zulässigkeit von Vorhaben)"},
                {"name": "Baunutzungsverordnung (BauNVO)", "key_provisions": "§§ 1-23 (Art der baulichen Nutzung)"}
            ],
            "Immissionsschutzrecht": [
                {"name": "Bundes-Immissionsschutzgesetz (BImSchG)", "key_provisions": "§§ 4-21 (Genehmigungsbedürftige Anlagen)"},
                {"name": "TA Lärm", "key_provisions": "Richtwerte für Lärmemissionen"}
            ],
            "Verwaltungsverfahrensrecht": [
                {"name": "Verwaltungsverfahrensgesetz (VwVfG)", "key_provisions": "§§ 28-78 (Verwaltungsakt)"}
            ]
        }
        
        for area in legal_areas:
            if area in law_mapping:
                laws.extend(law_mapping[area])
        
        return laws

# =============================================================================
# ENHANCED COVINA MODULE MANAGER
# =============================================================================

class CovinaModuleManagerEnhanced:
    """
    Zentraler Manager für alle Covina-Module mit Agent-Engine-Integration
    Koordiniert die Interaktionen zwischen den verschiedenen Komponenten
    """
    
    def __init__(self):
        self.modules = {}
        self.agent_engine = None
        self.external_workers = {}
        
        # Status-Tracking
        self.initialization_status = {
            "core_modules": False,
            "agent_engine": False,
            "external_workers": False,
            "uds3_components": False
        }
        
        # Initialisiere Module
        self._initialize_modules()
        
        if AGENT_ENGINE_AVAILABLE:
            self._initialize_agent_engine()
            self._initialize_external_workers()
        
        if UDS3_AVAILABLE:
            self.initialize_uds3_components()
    
    def _initialize_modules(self):
        """Initialisiert Standard Covina-Module"""
        try:
            # File Manager (falls verfügbar)
            if FILE_MANAGER_AVAILABLE:
                self.modules['file_manager'] = CovinaFileManager()
                self.modules['config_manager'] = CovinaConfigManager()
                logging.info("✅ File Manager initialisiert")
            
            # Theme Manager (falls verfügbar)
            if THEME_MANAGER_AVAILABLE:
                # self.modules['theme_manager'] = CovinaThemeManager()
                logging.info("✅ Theme Manager verfügbar")
            
            # Website Processor (falls verfügbar) 
            if SCRAPER_DIALOG_AVAILABLE:
                # self.modules['website_processor'] = CovinaWebsiteProcessor()
                logging.info("✅ Website Processor verfügbar")
                
            logging.info("✅ Covina Module-Initialisierung abgeschlossen")
            self.initialization_status["core_modules"] = True
            
        except Exception as e:
            logging.error(f"❌ Fehler bei Core Module Initialisierung: {e}")
            self.initialization_status["core_modules"] = False
    
    def _initialize_agent_engine(self):
        """Initialisiert Agent-Engine"""
        try:
            self.agent_engine = get_agent_engine()
            logging.info("✅ Agent Engine initialisiert")
            self.initialization_status["agent_engine"] = True
            
        except Exception as e:
            logging.error(f"❌ Fehler bei Agent Engine Initialisierung: {e}")
            self.initialization_status["agent_engine"] = False
    
    def _initialize_external_workers(self):
        """Initialisiert und registriert externe Workers"""
        try:
            # Standard Workers
            doc_worker = DocumentRetrievalWorker()
            geo_worker = GeoContextWorker()
            legal_worker = LegalFrameworkWorker()
            
            # Externe API Workers
            eu_lex_worker = EULexWorker()
            
            # Google Search Worker (falls konfiguriert)
            google_config = EXTERNAL_DATA_CONFIG["google_search"]
            if google_config["enabled"] and google_config["api_key"]:
                google_worker = GoogleSearchWorker(
                    api_key=google_config["api_key"],
                    search_engine_id=google_config["search_engine_id"]
                )
                self.external_workers["google_search"] = google_worker
                self.agent_engine.register_worker(WorkerType.EXTERNAL_API, google_worker)
            
            # Registriere Standard Workers bei Agent Engine
            self.agent_engine.register_worker(WorkerType.DOCUMENT_RETRIEVAL, doc_worker)
            self.agent_engine.register_worker(WorkerType.GEO_CONTEXT, geo_worker)
            self.agent_engine.register_worker(WorkerType.LEGAL_FRAMEWORK, legal_worker)
            
            # EU LEX als External API Worker
            self.external_workers["eu_lex"] = eu_lex_worker
            
            # Import und Registrierung der spezialisierten Worker-Module
            self._initialize_specialized_workers()
            
            logging.info("✅ External Workers initialisiert und registriert")
            self.initialization_status["external_workers"] = True
            
        except Exception as e:
            logging.error(f"❌ Fehler bei External Workers Initialisierung: {e}")
            self.initialization_status["external_workers"] = False
    
    def _initialize_specialized_workers(self):
        """Initialisiert spezialisierte Domain-Worker"""
        try:
            # Import der Worker-Module mit neuer Namenskonvention
            from covina_module_agent_environmental import ENVIRONMENTAL_WORKERS
            from covina_module_agent_construction import CONSTRUCTION_WORKERS
            from covina_module_agent_traffic import TRAFFIC_WORKERS
            from covina_module_agent_financial import FINANCIAL_WORKERS
            from covina_module_agent_social import SOCIAL_WORKERS
            
            # Registrierung der Environmental Workers
            for worker_key, worker_class in ENVIRONMENTAL_WORKERS.items():
                worker_instance = worker_class()
                self.external_workers[f"environmental_{worker_key}"] = worker_instance
                
                # Bestimme WorkerType basierend auf worker_key
                if "air_quality" in worker_key:
                    worker_type = WorkerType.AIR_QUALITY
                elif "noise_complaint" in worker_key:
                    worker_type = WorkerType.NOISE_COMPLAINT
                elif "waste_management" in worker_key:
                    worker_type = WorkerType.WASTE_MANAGEMENT
                else:
                    worker_type = WorkerType.ENVIRONMENTAL
                
                self.agent_engine.register_worker(worker_type, worker_instance)
            
            # Registrierung der Construction Workers
            for worker_key, worker_class in CONSTRUCTION_WORKERS.items():
                worker_instance = worker_class()
                self.external_workers[f"construction_{worker_key}"] = worker_instance
                
                if "building_permit" in worker_key:
                    worker_type = WorkerType.BUILDING_PERMIT
                elif "urban_planning" in worker_key:
                    worker_type = WorkerType.URBAN_PLANNING
                elif "heritage_protection" in worker_key:
                    worker_type = WorkerType.HERITAGE_PROTECTION
                else:
                    worker_type = WorkerType.CONSTRUCTION
                
                self.agent_engine.register_worker(worker_type, worker_instance)
            
            # Registrierung der Traffic Workers
            for worker_key, worker_class in TRAFFIC_WORKERS.items():
                worker_instance = worker_class()
                self.external_workers[f"traffic_{worker_key}"] = worker_instance
                
                if "traffic_management" in worker_key:
                    worker_type = WorkerType.TRAFFIC_MANAGEMENT
                elif "public_transport" in worker_key:
                    worker_type = WorkerType.PUBLIC_TRANSPORT
                elif "parking_management" in worker_key:
                    worker_type = WorkerType.PARKING_MANAGEMENT
                else:
                    worker_type = WorkerType.TRAFFIC
                
                self.agent_engine.register_worker(worker_type, worker_instance)
            
            # Registrierung der Financial Workers
            for worker_key, worker_class in FINANCIAL_WORKERS.items():
                worker_instance = worker_class()
                self.external_workers[f"financial_{worker_key}"] = worker_instance
                
                if "tax_assessment" in worker_key:
                    worker_type = WorkerType.TAX_ASSESSMENT
                elif "funding_opportunities" in worker_key:
                    worker_type = WorkerType.FUNDING_OPPORTUNITIES
                elif "business_tax" in worker_key:
                    worker_type = WorkerType.BUSINESS_TAX
                else:
                    worker_type = WorkerType.FINANCIAL
                
                self.agent_engine.register_worker(worker_type, worker_instance)
            
            # Registrierung der Social Workers
            for worker_key, worker_class in SOCIAL_WORKERS.items():
                worker_instance = worker_class()
                self.external_workers[f"social_{worker_key}"] = worker_instance
                
                if "social_benefits" in worker_key:
                    worker_type = WorkerType.SOCIAL_BENEFITS
                elif "citizen_services" in worker_key:
                    worker_type = WorkerType.CITIZEN_SERVICES
                elif "health_insurance" in worker_key:
                    worker_type = WorkerType.HEALTH_INSURANCE
                else:
                    worker_type = WorkerType.SOCIAL
                
                self.agent_engine.register_worker(worker_type, worker_instance)
            
            total_workers = (len(ENVIRONMENTAL_WORKERS) + len(CONSTRUCTION_WORKERS) + 
                           len(TRAFFIC_WORKERS) + len(FINANCIAL_WORKERS) + len(SOCIAL_WORKERS))
            
            logging.info(f"✅ Spezialisierte Worker geladen: {total_workers} Domain-Worker registriert")
            
        except ImportError as e:
            logging.warning(f"⚠️ Spezialisierte Worker-Module nicht verfügbar: {e}")
        except Exception as e:
            logging.error(f"❌ Fehler bei spezialisierten Worker Initialisierung: {e}")
    
    def initialize_uds3_components(self):
        """Initialisiert UDS3-spezifische Komponenten"""
        try:
            if UDS3_AVAILABLE:
                self.modules['process_analyzer'] = ProcessComplexityAnalyzer()
                self.modules['workflow_extractor'] = ProcessWorkflowExtractor()
                logging.info("✅ UDS3 Components initialisiert")
                
            self.initialization_status["uds3_components"] = True
            
        except Exception as e:
            logging.error(f"❌ Fehler bei UDS3 Components Initialisierung: {e}")
            self.initialization_status["uds3_components"] = False
    
    # =============================================================================
    # AGENT INTEGRATION METHODS
    # =============================================================================
    
    async def process_agent_query(self, query: str, session_id: str = None, user_profile: Dict = None):
        """Verarbeitet Query über Agent-Engine"""
        if not self.agent_engine:
            raise ValueError("Agent Engine nicht verfügbar")
        
        return await self.agent_engine.process_query(query, session_id, user_profile)
    
    def configure_external_data_source(self, source_type: str, config: Dict[str, Any]):
        """Konfiguriert externe Datenquelle"""
        if source_type == "google_search":
            EXTERNAL_DATA_CONFIG["google_search"].update(config)
            
            # Re-initialisiere Google Worker falls jetzt aktiviert
            if config.get("enabled") and config.get("api_key"):
                try:
                    google_worker = GoogleSearchWorker(
                        api_key=config["api_key"],
                        search_engine_id=config.get("search_engine_id")
                    )
                    self.external_workers["google_search"] = google_worker
                    
                    if self.agent_engine:
                        self.agent_engine.register_worker(WorkerType.EXTERNAL_API, google_worker)
                    
                    logging.info("✅ Google Search Worker konfiguriert und aktiviert")
                    
                except Exception as e:
                    logging.error(f"❌ Google Search Worker Konfiguration fehlgeschlagen: {e}")
        
        elif source_type in ["legal_db", "admin_db"]:
            EXTERNAL_DATA_CONFIG["sql_databases"][source_type].update(config)
            logging.info(f"✅ Database {source_type} konfiguriert")
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Gibt Agent-Engine-Statistiken zurück"""
        if not self.agent_engine:
            return {"error": "Agent Engine nicht verfügbar"}
        
        return self.agent_engine.get_stats()
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Gibt Worker-Statistiken zurück"""
        stats = {}
        
        if self.agent_engine and hasattr(self.agent_engine, 'workers'):
            for worker_type, worker in self.agent_engine.workers.items():
                if hasattr(worker, 'get_stats'):
                    stats[worker_type.value] = worker.get_stats()
        
        return stats
    
    # =============================================================================
    # LEGACY COMPATIBILITY METHODS
    # =============================================================================
    
    def get_module(self, module_name: str):
        """Legacy-Methode für Modul-Zugriff"""
        return self.modules.get(module_name)
    
    def get_file_manager(self) -> Optional[Any]:
        """Legacy-Methode für File Manager"""
        return self.modules.get('file_manager')
    
    def get_config_manager(self) -> Optional[Any]:
        """Legacy-Methode für Config Manager"""
        return self.modules.get('config_manager')
    
    def get_theme_manager(self) -> Optional[Any]:
        """Legacy-Methode für Theme Manager"""
        return self.modules.get('theme_manager')
    
    def get_website_processor(self) -> Optional[Any]:
        """Legacy-Methode für Website Processor"""
        return self.modules.get('website_processor')
    
    def is_module_available(self, module_name: str) -> bool:
        """Prüft ob Modul verfügbar ist"""
        return module_name in self.modules
    
    def get_module_status(self) -> Dict[str, bool]:
        """Gibt Status aller Module zurück"""
        status = self.initialization_status.copy()
        
        # Füge individuelle Module hinzu
        for module_name in self.modules:
            status[f"module_{module_name}"] = True
        
        # Füge externe Workers hinzu
        for worker_name in self.external_workers:
            status[f"worker_{worker_name}"] = True
        
        return status

# Globale Instanz (Singleton-Pattern)
_covina_manager_enhanced_instance = None

def get_covina_manager_enhanced() -> CovinaModuleManagerEnhanced:
    """Singleton-Zugriff auf Enhanced Covina Manager"""
    global _covina_manager_enhanced_instance
    if _covina_manager_enhanced_instance is None:
        _covina_manager_enhanced_instance = CovinaModuleManagerEnhanced()
    return _covina_manager_enhanced_instance

# =============================================================================
# LEGACY HELPER FUNCTIONS
# =============================================================================

def create_gui_component(component_type: str, parent, **kwargs):
    """Legacy-Funktion für GUI-Komponenten"""
    manager = get_covina_manager_enhanced()
    
    if not GUI_COMPONENTS_AVAILABLE:
        logging.warning("GUI Components nicht verfügbar")
        return None
    
    # GUI Components sind derzeit nicht verfügbar
    # TODO: Implementierung wenn Module verfügbar sind
    
    return None

def create_scraper_dialog(parent, dialog_type: str = "website", **kwargs):
    """Legacy-Funktion für Scraper-Dialoge"""
    if not SCRAPER_DIALOG_AVAILABLE:
        logging.warning("Scraper Dialoge nicht verfügbar")
        return None
    
    # Scraper Dialoge sind derzeit nicht verfügbar
    # TODO: Implementierung wenn Module verfügbar sind
    
    return None

def get_theme_color(color_name: str, default: str = "#000000") -> str:
    """Legacy-Funktion für Theme-Farben"""
    manager = get_covina_manager_enhanced()
    theme_manager = manager.get_theme_manager()
    
    if theme_manager and hasattr(theme_manager, 'get_color'):
        return theme_manager.get_color(color_name, default)
    
    return default

def configure_widget_theme(widget, style_type: str = "default"):
    """Legacy-Funktion für Widget-Theming"""
    manager = get_covina_manager_enhanced()
    theme_manager = manager.get_theme_manager()
    
    if theme_manager and hasattr(theme_manager, 'apply_style'):
        theme_manager.apply_style(widget, style_type)

def load_ingestion_plan(plan_file: str = None) -> Dict[str, Any]:
    """Legacy-Funktion für Ingestion-Plan laden"""
    manager = get_covina_manager_enhanced()
    file_manager = manager.get_file_manager()
    
    if file_manager and hasattr(file_manager, 'load_plan'):
        return file_manager.load_plan(plan_file)
    
    return {}

def save_ingestion_plan(plan_data: Dict[str, Any], plan_file: str = None) -> bool:
    """Legacy-Funktion für Ingestion-Plan speichern"""
    manager = get_covina_manager_enhanced()
    file_manager = manager.get_file_manager()
    
    if file_manager and hasattr(file_manager, 'save_plan'):
        return file_manager.save_plan(plan_data, plan_file)
    
    return False

# Modul-Informationen
__version__ = "2.0.0"
__author__ = "VERITAS System"
__description__ = "Enhanced Covina Module Manager with Agent Engine Integration"

# Logging
logging.info("✅ Enhanced Covina Module Manager geladen - Agent Engine Integration aktiv")
