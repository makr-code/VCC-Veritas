#!/usr/bin/env python3
"""
COVINA Configuration System - Bereinigte Version
===============================================

Zentrale Konfiguration für das COVINA Ingestion System
Fokus auf notwendige Elemente mit sauberer Strukturierung

Author: AI Assistant
Date: 2025-09-13
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Logging Setup
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s [%(module)s] - %(message)s'
)
logger = logging.getLogger(__name__)

class CovinaConfig:
    """
    Bereinigte Konfigurationsklasse für das COVINA System
    
    Enthält nur die tatsächlich verwendeten Konfigurationselemente:
    - Server-Konfiguration (Host, Port, API)
    - Datenbank-Pfade (nur notwendige)
    - LLM-Konfiguration (Ollama Integration)
    - Worker-System-Konfiguration
    - Environment-Variable-Synchronisation
    """
    
    def __init__(self):
        """Initialisiert die Konfiguration"""
        logger.info("[config] Initialisiere COVINA Config")
        
        # Environment-Variable-Synchronisation
        self._synchronize_env_prefixes()
        
        # File-basierte Konfiguration laden
        self._load_file_based_config()
        
        # Core-Konfiguration laden
        self._load_core_config()
        
        logger.info("[config] COVINA Config erfolgreich initialisiert")
    
    def _synchronize_env_prefixes(self):
        """
        Synchronisiert COVINA_* und VERITAS_* Environment-Variablen bidirektional
        """
        logger.debug("[config] Synchronisiere Environment-Variablen")
        
        # Alle Environment-Variablen durchgehen
        env_vars = dict(os.environ)
        
        for key, value in env_vars.items():
            if key.startswith('COVINA_'):
                # COVINA_ → VERITAS_ Mapping
                veritas_key = key.replace('COVINA_', 'VERITAS_', 1)
                if veritas_key not in os.environ:
                    os.environ[veritas_key] = value
                    logger.debug(f"Mapped {key} → {veritas_key}")
                    
            elif key.startswith('VERITAS_'):
                # VERITAS_ → COVINA_ Mapping  
                covina_key = key.replace('VERITAS_', 'COVINA_', 1)
                if covina_key not in os.environ:
                    os.environ[covina_key] = value
                    logger.debug(f"Mapped {key} → {covina_key}")
    
    def _load_file_based_config(self):
        """
        Lädt Konfiguration aus covina_config.json falls vorhanden
        """
        config_file = Path(__file__).parent / 'covina_config.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # Environment-Overrides anwenden
                if 'envOverrides' in file_config:
                    for key, value in file_config['envOverrides'].items():
                        if key not in os.environ:
                            os.environ[key] = str(value)
                            logger.debug(f"Config override: {key} = {value}")
                
                # System-Keys setzen
                if 'systemKeys' in file_config:
                    self.system_keys = file_config['systemKeys']
                    logger.info(f"System-Keys geladen: {len(self.system_keys)} Einträge")
                
                logger.info(f"File-basierte Konfiguration geladen: {config_file}")
                
            except Exception as e:
                logger.warning(f"Fehler beim Laden der Config-Datei {config_file}: {e}")
    
    def _load_core_config(self):
        """Lädt die Core-Konfigurationswerte"""
        
        # === SERVER CONFIGURATION ===
        self.app_host = os.getenv('COVINA_APP_HOST', '127.0.0.1')
        self.app_port = int(os.getenv('COVINA_APP_PORT', '5000'))
        self.api_base_url = os.getenv('COVINA_API_BASE_URL', f'http://{self.app_host}:{self.app_port}')
        
        # === DIRECTORY CONFIGURATION ===
        # Zentrales Datenverzeichnis
        self.data_dir = os.getenv('COVINA_DATA_DIR', 'Y:\\data')
        self._ensure_directory(self.data_dir)
        
        # Zentraler Datenbank-Ordner
        self.database_dir = os.getenv('COVINA_DATABASE_DIR', str(Path(__file__).parent / 'sqlite_db'))
        self._ensure_directory(self.database_dir)
        
        # === DATABASE PATHS (nur die tatsächlich verwendeten) ===
        # Ingestion System Databases
        self.ingestion_pipeline_db = os.path.join(self.database_dir, 'ingestion_pipeline.db')
        self.relational_db = os.path.join(self.database_dir, 'relational.db')
        self.quality_management_db = os.path.join(self.database_dir, 'quality_management.db')
        
        # DSGVO/GDPR Compliance Database (dedizierte SQLite für PII-Mappings)
        self.dsgvo_mappings_db = os.path.join(self.database_dir, 'dsgvo_mappings.db')
        
        # Vector Database (ChromaDB persistent storage)
        self.vector_db_path = os.path.join(self.database_dir, 'chroma_vector_db')
        self._ensure_directory(self.vector_db_path)
        
        # Graph Database (Neo4j data directory oder SQLite für lokale Graph-DB)
        self.graph_db_path = os.path.join(self.database_dir, 'graph.db')
        
        # Application Databases
        self.conversations_db = os.path.join(self.database_dir, 'conversations.db')
        self.collections_db = os.path.join(self.database_dir, 'collections.db')
        
        # License System
        self.licenses_db = os.path.join(str(Path(__file__).parent), 'licenses.db')
        
        # === LLM CONFIGURATION ===
        self.ollama_host = os.getenv('COVINA_OLLAMA_HOST', 'http://localhost:11434')
        self.llm_api_url = os.getenv('COVINA_LLM_API_URL', f'{self.ollama_host}/api/generate')
        self.llm_model = os.getenv('COVINA_LLM_MODEL', 'llama3:latest')
        self.llm_timeout = int(os.getenv('COVINA_LLM_TIMEOUT', '120'))
        
        # LLM Model Configuration (optimiert für Ingestion)
        self.llm_config = {
            'primary_model': self.llm_model,
            'fallback_models': ['gemma3:latest', 'phi3:latest'],
            'specialized_models': {
                'fast_ingestion': 'llama3:latest',
                'metadata_extraction': 'llama3:latest',
                'quality_assessment': 'gemma3:latest'
            }
        }
        
        # === WORKER SYSTEM CONFIGURATION ===
        # Autostart Worker (für Worker Registry)
        default_workers = 'file_scanner,preprocessor,documents,nlp,llm,quality,database'
        self.autostart_workers = os.getenv('COVINA_AUTOSTART_WORKERS', default_workers).split(',')
        self.autostart_workers = [w.strip().lower() for w in self.autostart_workers if w.strip()]
        
        # Worker-spezifische Einstellungen
        self.main_variants_only = os.getenv('COVINA_MAIN_VARIANTS_ONLY', '1') == '1'
        self.fast_discovery = os.getenv('COVINA_FAST_DISCOVERY', '1') == '1'
        self.import_timeout = float(os.getenv('COVINA_IMPORT_TIMEOUT', '2.5'))

        # File Scanner Settings (Time-Sliced)
        # Minimale Env-Nutzung: primär über config-Datei steuerbar
        self.file_scanner_time_sliced = True
        self.file_scanner_slice_seconds = 30
        self.file_scanner_idle_seconds = 30
        self.file_scanner_cooldown_seconds = 24 * 60 * 60
        
        # === BACKEND WORKER CONFIGURATION ===
        # Konsolidierter Backend Worker Konfiguration
        self.backend_worker_config = {
            'processing_mode': os.getenv('COVINA_BACKEND_PROCESSING_MODE', 'store_selective'),
            'enable_llm': os.getenv('COVINA_BACKEND_ENABLE_LLM', '1') == '1',
            'batch_size': int(os.getenv('COVINA_BACKEND_BATCH_SIZE', '25')),
            'enable_batch': os.getenv('COVINA_BACKEND_ENABLE_BATCH', '1') == '1',
            'quality_threshold': float(os.getenv('COVINA_BACKEND_QUALITY_THRESHOLD', '0.7')),
            'max_retries': int(os.getenv('COVINA_BACKEND_MAX_RETRIES', '3')),
            'timeout_seconds': int(os.getenv('COVINA_BACKEND_TIMEOUT', '300')),
            'enable_followup_tasks': os.getenv('COVINA_BACKEND_FOLLOWUP_TASKS', '1') == '1',
            'preferred_backends': os.getenv('COVINA_BACKEND_PREFERRED', 'vector,relational,graph').split(','),
            'fallback_mode': os.getenv('COVINA_BACKEND_FALLBACK_MODE', 'partial_storage'),  # 'partial_storage', 'fail', 'continue'
        }

        # === VERIFICATION/SECURITY CONFIGURATION ===
        # Optionale UDS3-gestützte Prüfungen in der Verification-Stage
        self.verification_config = {
            # Prüfe zusätzlich (optional) in einer relationalen UDS3-Tabelle, ob file_hash bereits existiert
            'use_uds3_relational_duplicate_check': os.getenv('COVINA_VERIFICATION_USE_UDS3_REL', '0') == '1',
            # Tabellenname und Spalten für den Lookup (nur wenn vorhanden; ansonsten wird ignoriert)
            'uds3_relational_table': os.getenv('COVINA_VERIFICATION_UDS3_REL_TABLE', 'documents_metadata'),
            'uds3_relational_hash_column': os.getenv('COVINA_VERIFICATION_UDS3_REL_HASH_COL', 'file_hash'),
            'uds3_relational_id_column': os.getenv('COVINA_VERIFICATION_UDS3_REL_ID_COL', 'document_id'),
        }
        
        # === DSGVO/GDPR CONFIGURATION ===
        # DSGVO Worker Database Configuration
        self.dsgvo_config = {
            'database_path': self.dsgvo_mappings_db,
            'enable_audit_trail': os.getenv('COVINA_DSGVO_AUDIT_TRAIL', '1') == '1',
            'audit_retention_days': int(os.getenv('COVINA_DSGVO_AUDIT_RETENTION_DAYS', '730')),  # 2 Jahre
            'mapping_retention_days': int(os.getenv('COVINA_DSGVO_MAPPING_RETENTION_DAYS', '2555')),  # 7 Jahre
            'enable_context_consistency': os.getenv('COVINA_DSGVO_CONTEXT_CONSISTENCY', '1') == '1',
            'uuid_format': os.getenv('COVINA_DSGVO_UUID_FORMAT', '[UUID-{uuid}]'),
            'confidence_threshold': float(os.getenv('COVINA_DSGVO_CONFIDENCE_THRESHOLD', '0.8')),
            'backup_interval_hours': int(os.getenv('COVINA_DSGVO_BACKUP_INTERVAL', '24')),
            'enable_encryption': os.getenv('COVINA_DSGVO_ENABLE_ENCRYPTION', '0') == '1',  # Optional für Zukunft
            'performance_mode': os.getenv('COVINA_DSGVO_PERFORMANCE_MODE', 'balanced'),  # 'fast', 'balanced', 'secure'
        }
        
        # === IMAGE PROCESSING CONFIGURATION ===
        # OCR und AI-Bildverarbeitung Konfiguration
        self.image_processing_config = {
            # OCR-Einstellungen
            'ocr_languages': os.getenv('COVINA_OCR_LANGUAGES', 'deu+eng').split('+'),
            'ocr_engine': os.getenv('COVINA_OCR_ENGINE', 'both'),  # 'tesseract', 'easyocr', 'both'
            'tesseract_path': os.getenv('COVINA_TESSERACT_PATH', None),
            'min_confidence': float(os.getenv('COVINA_OCR_MIN_CONFIDENCE', '0.3')),
            
            # AI-Modell-Einstellungen
            'enable_ai_description': os.getenv('COVINA_AI_DESCRIPTION_ENABLED', '1') == '1',
            'description_model': os.getenv('COVINA_AI_DESCRIPTION_MODEL', 'Salesforce/blip-image-captioning-base'),
            'stable_diffusion_model': os.getenv('COVINA_STABLE_DIFFUSION_MODEL', 'runwayml/stable-diffusion-v1-5'),
            'use_gpu': os.getenv('COVINA_USE_GPU', '1') == '1',
            'gpu_memory_fraction': float(os.getenv('COVINA_GPU_MEMORY_FRACTION', '0.7')),
            
            # Verarbeitungseinstellungen
            'processing_mode': os.getenv('COVINA_IMAGE_PROCESSING_MODE', 'auto'),  # 'auto', 'ocr_only', 'description_only', 'full'
            'max_image_size': int(os.getenv('COVINA_MAX_IMAGE_SIZE', '4096')),
            'batch_size': int(os.getenv('COVINA_IMAGE_BATCH_SIZE', '8')),
            'parallel_workers': int(os.getenv('COVINA_IMAGE_PARALLEL_WORKERS', '2')),
            
            # Unterstützte Formate
            'supported_formats': os.getenv('COVINA_SUPPORTED_IMAGE_FORMATS', 'png,jpg,jpeg,tiff,tif,bmp,webp,pdf').split(','),
            
            # Performance-Optimierung
            'enable_preprocessing': os.getenv('COVINA_IMAGE_PREPROCESSING', '1') == '1',
            'cache_models': os.getenv('COVINA_CACHE_AI_MODELS', '1') == '1',
            'memory_optimization': os.getenv('COVINA_IMAGE_MEMORY_OPTIMIZATION', 'balanced'),  # 'fast', 'balanced', 'memory_saving'
            
            # DSGVO-Integration
            'enable_dsgvo': os.getenv('COVINA_IMAGE_DSGVO_ENABLED', '1') == '1',
            'anonymize_extracted_text': os.getenv('COVINA_ANONYMIZE_EXTRACTED_TEXT', '1') == '1',
            
            # Qualitätskontrolle
            'quality_threshold': float(os.getenv('COVINA_IMAGE_QUALITY_THRESHOLD', '0.5')),
            'auto_enhance': os.getenv('COVINA_IMAGE_AUTO_ENHANCE', '1') == '1',
            
            # Ausgabe-Einstellungen
            'output_format': os.getenv('COVINA_IMAGE_OUTPUT_FORMAT', 'json'),  # 'json', 'text', 'structured'
            'include_metadata': os.getenv('COVINA_IMAGE_INCLUDE_METADATA', '1') == '1',
            'include_bounding_boxes': os.getenv('COVINA_IMAGE_INCLUDE_BBOXES', '0') == '1',
        }
        
        # === ARCHIVE PROCESSING CONFIGURATION ===
        # Archiv-Worker Konfiguration
        self.archive_processing_config = {
            # Extraktions-Einstellungen
            'extraction_mode': os.getenv('COVINA_ARCHIVE_EXTRACTION_MODE', 'subfolder'),  # 'in_place', 'subfolder', 'temp_dir', 'custom_path'
            'security_level': os.getenv('COVINA_ARCHIVE_SECURITY_LEVEL', 'balanced'),  # 'strict', 'balanced', 'permissive'
            'auto_cleanup_failed': os.getenv('COVINA_ARCHIVE_AUTO_CLEANUP_FAILED', '1') == '1',
            
            # Sicherheits-Limits
            'max_archive_size': int(os.getenv('COVINA_ARCHIVE_MAX_SIZE', str(5 * 1024 * 1024 * 1024))),  # 5GB
            'max_extraction_size': int(os.getenv('COVINA_ARCHIVE_MAX_EXTRACTION_SIZE', str(20 * 1024 * 1024 * 1024))),  # 20GB
            'max_files_per_archive': int(os.getenv('COVINA_ARCHIVE_MAX_FILES', '50000')),
            'max_extraction_depth': int(os.getenv('COVINA_ARCHIVE_MAX_DEPTH', '20')),
            'extraction_timeout': int(os.getenv('COVINA_ARCHIVE_EXTRACTION_TIMEOUT', '3600')),  # 1 Stunde
            
            # Unterstützte Formate
            'supported_formats': os.getenv('COVINA_SUPPORTED_ARCHIVE_FORMATS', 'zip,rar,7z,tar,tar.gz,tar.bz2,tar.xz,gz,bz2').split(','),
            'blocked_extensions': os.getenv('COVINA_ARCHIVE_BLOCKED_EXTENSIONS', '.exe,.bat,.cmd,.scr,.vbs,.js').split(','),
            
            # Task-Integration
            'enable_task_integration': os.getenv('COVINA_ARCHIVE_TASK_INTEGRATION', '1') == '1',
            'file_scanner_priority': os.getenv('COVINA_ARCHIVE_SCANNER_PRIORITY', 'normal'),  # 'low', 'normal', 'high', 'urgent'
            'auto_scan_extracted': os.getenv('COVINA_ARCHIVE_AUTO_SCAN_EXTRACTED', '1') == '1',
            
            # Metadaten-Einstellungen
            'enable_metadata_json': os.getenv('COVINA_ARCHIVE_METADATA_JSON', '1') == '1',
            'include_file_hashes': os.getenv('COVINA_ARCHIVE_INCLUDE_HASHES', '1') == '1',
            'include_compression_info': os.getenv('COVINA_ARCHIVE_INCLUDE_COMPRESSION', '1') == '1',
            'metadata_detail_level': os.getenv('COVINA_ARCHIVE_METADATA_DETAIL', 'standard'),  # 'minimal', 'standard', 'detailed'
            
            # Performance-Einstellungen
            'parallel_extraction': os.getenv('COVINA_ARCHIVE_PARALLEL_EXTRACTION', '0') == '1',
            'max_parallel_workers': int(os.getenv('COVINA_ARCHIVE_MAX_WORKERS', '2')),
            'streaming_extraction': os.getenv('COVINA_ARCHIVE_STREAMING', '1') == '1',
            'memory_limit_mb': int(os.getenv('COVINA_ARCHIVE_MEMORY_LIMIT', '2048')),  # 2GB
            
            # Path-Behandlung
            'preserve_directory_structure': os.getenv('COVINA_ARCHIVE_PRESERVE_STRUCTURE', '1') == '1',
            'flatten_single_directory': os.getenv('COVINA_ARCHIVE_FLATTEN_SINGLE_DIR', '0') == '1',
            'safe_filename_handling': os.getenv('COVINA_ARCHIVE_SAFE_FILENAMES', '1') == '1',
            'max_filename_length': int(os.getenv('COVINA_ARCHIVE_MAX_FILENAME_LENGTH', '255')),
            
            # Backup & Recovery
            'backup_original_archive': os.getenv('COVINA_ARCHIVE_BACKUP_ORIGINAL', '0') == '1',
            'backup_failed_extractions': os.getenv('COVINA_ARCHIVE_BACKUP_FAILED', '1') == '1',
            'recovery_mode': os.getenv('COVINA_ARCHIVE_RECOVERY_MODE', 'auto'),  # 'auto', 'manual', 'skip'
            
            # Logging & Monitoring
            'detailed_logging': os.getenv('COVINA_ARCHIVE_DETAILED_LOGGING', '1') == '1',
            'progress_reporting': os.getenv('COVINA_ARCHIVE_PROGRESS_REPORTING', '1') == '1',
            'performance_monitoring': os.getenv('COVINA_ARCHIVE_PERFORMANCE_MONITORING', '1') == '1',
            
            # Content Worker Mapping - Zuordnung von Dateierweiterungen zu Workern
            'content_worker_mapping': {
                '.txt': 'document',
                '.pdf': 'document', 
                '.docx': 'office',
                '.xlsx': 'office',
                '.pptx': 'office',
                '.doc': 'office',
                '.xls': 'office',
                '.ppt': 'office',
                '.odt': 'office',
                '.ods': 'office',
                '.odp': 'office',
                '.jpg': 'image',
                '.jpeg': 'image',
                '.png': 'image',
                '.gif': 'image',
                '.bmp': 'image',
                '.tiff': 'image',
                '.webp': 'image',
                '.mp3': 'audio',
                '.wav': 'audio',
                '.flac': 'audio',
                '.ogg': 'audio',
                '.aac': 'audio',
                '.m4a': 'audio',
                '.mp4': 'video',
                '.avi': 'video',
                '.mkv': 'video',
                '.mov': 'video',
                '.wmv': 'video',
                '.flv': 'video',
                '.webm': 'video',
                '.ply': '3d',
                '.obj': '3d',
                '.stl': '3d',
                '.dae': '3d',
                '.fbx': '3d',
                '.gltf': '3d',
                '.3ds': '3d',
                '.shp': 'geospatial',
                '.geojson': 'geospatial',
                '.kml': 'geospatial',
                '.gpx': 'geospatial',
                '.gml': 'geospatial',
                '.msg': 'email',
                '.eml': 'email',
                '.mbox': 'email',
                # Archive formats trigger recursive processing
                '.zip': 'archive',
                '.tar': 'archive',
                '.gz': 'archive',
                '.7z': 'archive',
                '.rar': 'archive',
                '.bz2': 'archive'
            },
            
            # Security Settings
            'security_enabled': True,
            'max_compression_ratio': 100.0,  # ZIP-bomb detection
            'allowed_extensions': ['.txt', '.pdf', '.docx', '.xlsx', '.pptx', '.jpg', '.jpeg', '.png', '.gif', 
                                 '.mp3', '.wav', '.mp4', '.avi', '.ply', '.obj', '.shp', '.geojson', '.msg', '.eml',
                                 '.zip', '.tar', '.gz', '.7z', '.rar', '.bz2'],
            'temp_dir': None  # Will use system temp if None
        }
        
        # === WATCHDOG CONFIGURATION ===
        self.watchdog_heartbeat_freshness = int(os.getenv('COVINA_WATCHDOG_HEARTBEAT_FRESHNESS', '30'))
        self.watchdog_heartbeat_extension_mode = os.getenv('COVINA_WATCHDOG_HEARTBEAT_EXTENSION_MODE', 'factor')
        self.watchdog_max_extension_factor = float(os.getenv('COVINA_WATCHDOG_MAX_EXTENSION_FACTOR', '2.0'))
        self.watchdog_ready_gating = os.getenv('COVINA_WATCHDOG_READY_GATING', '1') == '1'
        
        # === DOCUMENT PROCESSING ===
        self.chunk_size = int(os.getenv('COVINA_CHUNK_SIZE', '1000'))
        self.chunk_overlap = int(os.getenv('COVINA_CHUNK_OVERLAP', '200'))
        self.max_file_size_mb = int(os.getenv('COVINA_MAX_FILE_SIZE_MB', '50'))
        
        # === LOGGING CONFIGURATION ===
        self.log_level = os.getenv('COVINA_LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('COVINA_LOG_FILE', 'covina.log')

        # === FOLLOW-UP PIPELINE SETTINGS (Backpressure, Dedup, Digest) ===
        # Minimiert direkte Nutzung vieler Environment Variablen an anderer Stelle.
        # Falls Env Variablen mit VERITAS_ oder COVINA_ Präfix gesetzt werden, überschreiben sie Defaults.
        self.followup_config = {
            'max_pending_backend': int(os.getenv('COVINA_FOLLOWUP_MAX_PENDING_BACKEND', os.getenv('FOLLOWUP_MAX_PENDING_BACKEND', '250'))),
            'max_pending_llm': int(os.getenv('COVINA_FOLLOWUP_MAX_PENDING_LLM', os.getenv('FOLLOWUP_MAX_PENDING_LLM', '60'))),
            'digest_interval_s': int(os.getenv('COVINA_FOLLOWUP_DIGEST_INTERVAL_S', os.getenv('FOLLOWUP_DIGEST_INTERVAL_S', '60'))),
            'dedup_lru_size': int(os.getenv('COVINA_FOLLOWUP_DEDUP_LRU_SIZE', os.getenv('FOLLOWUP_DEDUP_LRU_SIZE', '5000')))
        }
        logger.info(f"[config] Follow-up Settings geladen: {self.followup_config}")
        
        logger.info("[config] Core-Konfiguration geladen")
    
    def _ensure_directory(self, directory: str):
        """Stellt sicher, dass ein Verzeichnis existiert"""
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            logger.warning(f"Kann Verzeichnis nicht erstellen {directory}: {e}")
    
    # === DATABASE BACKEND CONFIGURATION ===
    
    def get_database_backend_dict(self) -> Dict[str, Any]:
        """
        Datenbank-Backend-Konfiguration für database_api.py
        
        Konfiguriert alle Datenbank-Backends:
        - relational.db über SQLiteRelationalBackend
        - vector_db über ChromaDB mit persistentem Storage
        - graph_db über Neo4j oder SQLite-Graph-Backend
        """
        return {
            'relational': {
                'enabled': True,
                'backend': 'sqlite',
                'database_path': self.relational_db,
                'connection_pool_size': 5,
                'timeout': 30.0,
                'check_same_thread': False,
                'journal_mode': 'WAL',
                'synchronous': 'NORMAL',
                'cache_size': -64000  # 64MB Cache
            },
            'file': {
                'enabled': True,
                'backend': 'filesystem',
                # Assets-Root unterhalb des allgemeinen Datenordners
                'root_path': os.path.join(self.data_dir, 'assets'),
                # Optionales Verhalten
                'uri_scheme': 'file',             # 'file' oder 'path'
                'preserve_filenames': False,      # True: Originalnamen behalten
                'hash_subdirs': 2                  # Anzahl Hash-basierten Subdir-Ebenen
            },
            'vector': {
                'enabled': True,
                'backend': 'chromadb',
                'persist_directory': self.vector_db_path,
                'collection_name': os.getenv('COVINA_VECTOR_COLLECTION', 'covina_documents'),
                'host': os.getenv('COVINA_CHROMA_HOST', 'localhost'),
                'port': int(os.getenv('COVINA_CHROMA_PORT', '8000')),
                'embedding_function': os.getenv('COVINA_EMBEDDING_MODEL', 'all-minilm'),
                'distance_function': 'cosine'
            },
            'graph': {
                'enabled': True,
                'backend': os.getenv('COVINA_GRAPH_BACKEND', 'neo4j'),  # Neo4j als Standard
                'database_path': self.graph_db_path,
                # Neo4j Konfiguration (falls verwendet)
                'uri': os.getenv('COVINA_NEO4J_URI', 'bolt://localhost:7687'),
                'username': os.getenv('COVINA_NEO4J_USER', 'neo4j'),
                'password': os.getenv('COVINA_NEO4J_PASSWORD', 'v3f3b1d7'),  # Korrektes Passwort
                'database': os.getenv('COVINA_NEO4J_DATABASE', 'neo4j'),
                # SQLite Graph Konfiguration
                'connection_pool_size': 3,
                'timeout': 30.0,
                'enable_foreign_keys': True
            },
            'keyvalue': {
                'enabled': False,  # Redis deaktiviert - wird nicht mehr genutzt
                'backend': 'redis',
                'host': os.getenv('COVINA_REDIS_HOST', 'localhost'),
                'port': int(os.getenv('COVINA_REDIS_PORT', '6379')),
                'db': int(os.getenv('COVINA_REDIS_DB', '0')),
                'password': os.getenv('COVINA_REDIS_PASSWORD', None),
                'socket_timeout': 30.0,
                'connection_pool_size': 10,
                # Ingestion-spezifische Cache-Konfiguration
                'cache_ttl': int(os.getenv('COVINA_CACHE_TTL', '3600')),  # 1 Stunde Standard
                'cache_prefix': os.getenv('COVINA_CACHE_PREFIX', 'covina:'),
                'max_memory_policy': 'allkeys-lru'  # LRU eviction policy
            }
        }
    
    def get_server_config(self) -> Dict[str, Any]:
        """Gibt die Server-Konfiguration zurück"""
        return {
            'host': self.app_host,
            'port': self.app_port,
            'api_base_url': self.api_base_url
        }
    
    def get_relational_db_config(self) -> Dict[str, Any]:
        """
        Gibt die Konfiguration für die relationale Datenbank zurück
        """
        return self.get_database_backend_dict()['relational']
    
    def get_vector_db_config(self) -> Dict[str, Any]:
        """
        Gibt die Konfiguration für die Vector-Datenbank zurück
        """
        return self.get_database_backend_dict()['vector']
    
    def get_graph_db_config(self) -> Dict[str, Any]:
        """
        Gibt die Konfiguration für die Graph-Datenbank zurück
        """
        return self.get_database_backend_dict()['graph']
    
    def get_redis_config(self) -> Dict[str, Any]:
        """
        Gibt die Konfiguration für Redis (Key-Value Cache) zurück
        """
        return self.get_database_backend_dict()['keyvalue']
    
    def get_backend_worker_config(self) -> Dict[str, Any]:
        """
        Gibt die Konfiguration für den Backend Worker zurück
        """
        return self.backend_worker_config.copy()
    
    # === STATIC UTILITY METHODS ===
    
    @staticmethod
    def load_json(path: str) -> Optional[Dict[str, Any]]:
        """Lädt JSON-Datei sicher"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Fehler beim Laden von JSON ({path}): {e}")
            return None
    
    @staticmethod
    def save_json(path: str, data: Dict[str, Any]) -> bool:
        """Speichert JSON-Datei sicher"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"JSON erfolgreich gespeichert: {path}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern von JSON ({path}): {e}")
            return False

# === SINGLETON INSTANCE ===
# Globale Konfigurationsinstanz für Kompatibilität
config = CovinaConfig()

# === LEGACY COMPATIBILITY ===
# Für bestehenden Code, der diese Variablen erwartet

# Datenbankpfade (für direkte Imports)
INGESTION_PIPELINE_DB = config.ingestion_pipeline_db
RELATIONAL_DB = config.relational_db
QUALITY_MANAGEMENT_DB = config.quality_management_db
CONVERSATIONS_DB = config.conversations_db
COLLECTIONS_DB = config.collections_db
LICENSES_DB = config.licenses_db

# Vector und Graph Database Pfade
VECTOR_DB_PATH = config.vector_db_path
GRAPH_DB_PATH = config.graph_db_path

# Verzeichnisse
DATA_DIR = config.data_dir
DATABASE_DIR = config.database_dir

# Server-Konfiguration
API_BASE_URL = config.api_base_url

# LLM-Konfiguration
LLM_API_URL = config.llm_api_url
LLM_MODEL = config.llm_model
LLM_TIMEOUT = config.llm_timeout
OLLAMA_HOST = config.ollama_host

# Legacy Database Config (leer für Kompatibilität)
DATABASE_CONFIG = {}

# Convenience-Funktionen für Legacy-Code
def load_server_config():
    """Legacy-Funktion für Server-Config"""
    return config.get_server_config()

def get_image_processing_config():
    """Bildverarbeitungs-Konfiguration"""
    return config.image_processing_config

def get_archive_processing_config():
    """Archiv-Verarbeitungs-Konfiguration"""
    return config.archive_processing_config

# === CONFIGURATION SUMMARY ===
if __name__ == "__main__":
    print("COVINA Configuration Summary:")
    print(f"  Server: {config.app_host}:{config.app_port}")
    print(f"  Database Dir: {config.database_dir}")
    print(f"  Relational DB: {config.relational_db}")
    print(f"  Vector DB: {config.vector_db_path}")
    print(f"  Graph DB: {config.graph_db_path}")
    print(f"  LLM Model: {config.llm_model}")
    print(f"  Autostart Workers: {', '.join(config.autostart_workers)}")
    print(f"  Watchdog Heartbeat: {config.watchdog_heartbeat_freshness}s")
    print("\nDatabase Backends:")
    backends = config.get_database_backend_dict()
    for db_type, config_dict in backends.items():
        status = "✅ enabled" if config_dict.get('enabled') else "❌ disabled"
        backend = config_dict.get('backend', 'unknown')
        print(f"  {db_type.capitalize()}: {backend} ({status})")