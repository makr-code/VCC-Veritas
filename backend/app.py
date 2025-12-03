#!/usr/bin/env python3
"""
VERITAS Unified Backend
=======================

🎯 Konsolidiertes Backend - EINE Datei für ALLES

Features:
- UDS3 v2.0.0 Integration (Polyglot Database)
- Intelligent Multi-Agent Pipeline
- Hybrid Search (BM25 + Dense + RRF)
- Streaming Progress System
- Unified Response Model (IEEE Citations - 35+ Felder)

Alle Query-Modi nutzen dasselbe Response-Format:
- RAG, Hybrid, Streaming, Agent, Ask
- Immer: UnifiedResponse mit IEEE-Standard Citations

Port: 5000
Docs: http://localhost:5000/docs
API: http://localhost:5000/api

Author: VERITAS System
Version: 4.0.0
Date: 2025-10-19
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles
import uvicorn
import ssl

# PKI Integration
try:
    from vcc_pki_client import PKIClient
    PKI_AVAILABLE = True
except ImportError:
    PKI_AVAILABLE = False
    PKIClient = None

# TLS/HTTPS Enforcement
try:
    from backend.security.tls import add_tls_middleware, TLSConfig
    TLS_AVAILABLE = True
except ImportError:
    TLS_AVAILABLE = False
    TLSConfig = None
    add_tls_middleware = None

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging() -> logging.Logger:
    """Setup logging with console and file handlers"""
    log_level = getattr(logging, os.getenv("VERITAS_LOG_LEVEL", "INFO").upper(), logging.INFO)
    
    # Create data directory
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    log_file = os.path.join(data_dir, "veritas_backend.log")
    
    # Format
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

logger = setup_logging()

# ============================================================================
# Import Required Dependencies (NO FALLBACK!)
# ============================================================================

# Ensure CouchDB availability is detected before importing UDS3 so the
# `UDS3_DISABLE_FILE_BACKEND` environment flag is available to UDS3 init.
try:
    import backend.database.uds3_direct  # module-level detection sets env flag
except Exception:
    logger.debug("Early CouchDB availability detection failed (non-fatal)")

# UDS3 v2.0.0 - Direct import may cause circular imports in some setups.
try:
    from uds3.core import UDS3PolyglotManager
    UDS3_AVAILABLE = True
except Exception as e:  # pragma: no cover - defensive fallback
    UDS3_AVAILABLE = False
    UDS3PolyglotManager = None
    logger.warning(f"⚠️ UDS3 import failed or caused circular import: {e}")

# Intelligent Pipeline - ZWINGEND ERFORDERLICH!
from backend.agents.veritas_intelligent_pipeline import (
    IntelligentMultiAgentPipeline, 
    get_intelligent_pipeline
)

# Streaming Progress - ZWINGEND ERFORDERLICH!
from shared.pipelines.veritas_streaming_progress import create_progress_manager

# Services - ZWINGEND ERFORDERLICH!
from backend.services.query_service import QueryService

# API Router - ZWINGEND ERFORDERLICH!
from backend.api import api_router, get_api_info

# SSE Endpoints - SERVER-SENT EVENTS (NEU!)
try:
    from backend.api.sse_endpoints import router as sse_router, init_sse_endpoints
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False
    sse_router = None
    init_sse_endpoints = None
    logger.warning("⚠️ SSE Endpoints not available - install sse-starlette")

# MCP HTTP Bridge (für Office Add-ins)
try:
    from backend.api.mcp_http_endpoints import router as mcp_http_router
    MCP_HTTP_AVAILABLE = True
except ImportError:
    MCP_HTTP_AVAILABLE = False
    mcp_http_router = None
    logger.warning("ℹ️  MCP HTTP Bridge not available")

# Office Ingestion (RAG Upload für Word/Excel/PowerPoint)
try:
    from backend.api.office_ingestion import router as office_ingestion_router
    OFFICE_INGESTION_AVAILABLE = True
except ImportError:
    OFFICE_INGESTION_AVAILABLE = False
    office_ingestion_router = None
    logger.warning("ℹ️  Office Ingestion API not available")

# ============================================================================
# Feature Flags
# ============================================================================

# `UDS3_AVAILABLE` is set by the defensive import above; keep that value.
INTELLIGENT_PIPELINE_AVAILABLE = True  # Required dependency
STREAMING_AVAILABLE = True  # Required dependency

# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application Lifespan - Startup and Shutdown"""
    
    # ===== STARTUP =====
    logger.info("=" * 80)
    logger.info("🚀 VERITAS Unified Backend - Starting")
    logger.info("=" * 80)
    logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🐍 Python: {sys.version.split()[0]}")
    logger.info(f"📁 Project Root: {project_root}")
    logger.info("=" * 80)
    
    # ============================================================================
    # PKI Integration - Certificate Management
    # ============================================================================
    if PKI_AVAILABLE:
        try:
            logger.info("🔐 Initializing PKI Client...")
            
            # Import secrets manager for secure CA password retrieval
            from backend.security.secrets import get_vcc_ca_password
            
            pki_server_url = os.getenv("PKI_SERVER_URL", "https://localhost:8443")
            service_id = os.getenv("SERVICE_ID", "veritas-backend")
            ca_password = get_vcc_ca_password()  # Securely retrieve from encrypted storage
            
            if not ca_password:
                logger.warning("⚠️  VCC_CA_PASSWORD not set - using default")
                ca_password = "your-secure-ca-password"
            
            # Initialize PKI client
            pki_client = PKIClient(
                pki_server_url=pki_server_url,
                service_id=service_id,
                ca_password=ca_password
            )
            
            # Request certificate (auto-renewal enabled)
            logger.info(f"📋 Requesting certificate for service: {service_id}")
            cert_result = pki_client.request_certificate(
                common_name=service_id,
                validity_days=365
            )
            
            if cert_result.get("success"):
                logger.info("✅ Certificate obtained successfully")
                logger.info(f"   Serial: {cert_result.get('serial_number')}")
                logger.info(f"   Valid until: {cert_result.get('valid_until')}")
                logger.info(f"   Auto-renewal: Enabled")
                
                # Store PKI client in app state
                app.state.pki_client = pki_client
                app.state.pki_enabled = True
                app.state.ssl_context = pki_client.get_ssl_context()
            else:
                logger.error(f"❌ Certificate request failed: {cert_result.get('error')}")
                logger.warning("⚠️  Falling back to HTTP mode")
                app.state.pki_enabled = False
                
        except Exception as e:
            logger.error(f"❌ PKI initialization failed: {e}")
            logger.warning("⚠️  Falling back to HTTP mode")
            app.state.pki_enabled = False
    else:
        logger.info("ℹ️  PKI not available - running in HTTP mode")
        app.state.pki_enabled = False
    
    logger.info("=" * 80)
<<<<<<< Updated upstream
    
    # Initialize UDS3 PolyglotManager - DIRECT INTEGRATION!
    # NO WRAPPERS, NO STUBS, NO FALLBACKS - PRODUCTION READY!
    logger.info("🔄 Initialisiere UDS3 PolyglotManager (DIRECT)...")
    
=======

    # Initialize UDS3 Remote Client - Simplified minimal initialization
    logger.info("🔄 Initialisiere UDS3 Remote Client (minimal rumpf)...")

>>>>>>> Stashed changes
    # ============================================================================
    # UDS3 REMOTE INTEGRATION (NEW):
    # ============================================================================
    # Request minimal backend "rumpf" with only required databases:
    # - Vector (ChromaDB) for semantic search
    # - Graph (Neo4j) for knowledge relationships
    # - Relational (PostgreSQL) for structured data
    # - File (CouchDB) only if driver available
    #
    # Old approach requested full UDS3PolyglotManager with local config.
    # New approach: Request lightweight remote stub from UDS3 service.
    # ============================================================================
    
    try:
<<<<<<< Updated upstream
        # DIRECT: UDS3PolyglotManager (Legacy stable version)
        # Minimal Config - DatabaseManager lädt echte Credentials aus uds3/config.py
        backend_config = {
            "vector": {"enabled": True},      # ChromaDB - Embeddings/Semantic Search
            "graph": {"enabled": True},       # Neo4j - Knowledge Graph
            "relational": {"enabled": True},  # PostgreSQL - Structured Data
            "file": {"enabled": True}         # CouchDB - Original Files/Documents
        }
        
        app.state.uds3 = UDS3PolyglotManager(
            backend_config=backend_config,
            enable_rag=True
        )
        
        logger.info("✅ UDS3 PolyglotManager initialisiert (Direct Integration)")
        
=======
        # Determine which backends to request from remote UDS3
        requested_backends = ["vector", "graph", "relational"]
        
        # Only request file backend if CouchDB driver is available
        try:
            import importlib
            if importlib.util.find_spec("couchdb") is not None:
                uds3_disable_flag = os.getenv("UDS3_DISABLE_FILE_BACKEND", "0")
                if uds3_disable_flag != "1":
                    requested_backends.append("file")
                    logger.info("ℹ️  CouchDB driver available - requesting file backend")
                else:
                    logger.info("ℹ️  UDS3_DISABLE_FILE_BACKEND=1 - skipping file backend")
            else:
                logger.info("ℹ️  CouchDB driver not installed - skipping file backend")
        except Exception:
            logger.info("ℹ️  Error checking CouchDB availability - skipping file backend")

        logger.info(f"📋 Requesting UDS3 backends: {', '.join(requested_backends)}")

        # Request minimal UDS3 rumpf with only the databases we need
        backend_config = {backend: {"enabled": True} for backend in requested_backends}

        app.state.uds3 = UDS3PolyglotManager(backend_config=backend_config, enable_rag=True)

        logger.info("✅ UDS3 Remote Client initialisiert (minimal rumpf)")

        # Log requested backends
        logger.info(f"📊 Requested backends: {len(requested_backends)}")
        for backend in requested_backends:
            logger.info(f"   ✓ {backend}")

>>>>>>> Stashed changes
        # Check database backends (optional logging)
        if hasattr(app.state.uds3, 'db_manager'):
            try:
                dm = app.state.uds3.db_manager
                logger.info("📊 UDS3 DatabaseManager:")
                
                try:
                    from database.config import DatabaseType
                    
                    vector_dbs = dm.get_databases_by_type(DatabaseType.VECTOR)
                    graph_dbs = dm.get_databases_by_type(DatabaseType.GRAPH)
                    relational_dbs = dm.get_databases_by_type(DatabaseType.RELATIONAL)
                    file_dbs = dm.get_databases_by_type(DatabaseType.FILE)
                    
                    logger.info(f"   Vector DBs: {len(vector_dbs)} backends")
                    logger.info(f"   Graph DBs: {len(graph_dbs)} backends")
                    logger.info(f"   Relational DBs: {len(relational_dbs)} backends")
                    logger.info(f"   File DBs: {len(file_dbs)} backends")
                    
                    # Log connection details
                    if vector_dbs:
                        logger.info(f"   → Vector: {vector_dbs[0].backend.value} @ {vector_dbs[0].host}:{vector_dbs[0].port}")
                    if graph_dbs:
                        logger.info(f"   → Graph: {graph_dbs[0].backend.value} @ {graph_dbs[0].host}:{graph_dbs[0].port}")
                    if relational_dbs:
                        logger.info(f"   → Relational: {relational_dbs[0].backend.value} @ {relational_dbs[0].host}:{relational_dbs[0].port}")
                    if file_dbs:
                        logger.info(f"   → File: {file_dbs[0].backend.value} @ {file_dbs[0].host}:{file_dbs[0].port}")
                        
                except (ImportError, AttributeError) as ie:
                    logger.debug(f"Backend details not available: {ie}")
            except Exception as db_err:
                logger.debug(f"DatabaseManager not accessible: {db_err}")
        
        # Share UDS3 instance with agent framework (DIRECT - NO WRAPPER!)
        from backend.database.uds3_integration import set_uds3_instance
        set_uds3_instance(app.state.uds3)
        logger.info("✅ UDS3 shared with agents (direct access)")
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ KRITISCHER FEHLER: UDS3 Remote Client Initialisierung fehlgeschlagen!")
        logger.error("=" * 80)
        logger.error(f"Fehler: {e}")
        logger.error("")
        logger.error("🔧 UDS3 REMOTE INTEGRATION:")
        logger.error("   • Verbindung zu UDS3 Remote Service fehlgeschlagen")
        logger.error("   • Backend 'rumpf' konnte nicht angefordert werden")
        logger.error("")
        logger.error("💡 Prüfe:")
        logger.error("   1. UDS3 Remote Service läuft und ist erreichbar")
        logger.error("   2. Netzwerkverbindung zu Remote-Datenbanken")
        logger.error("   3. Umgebungsvariablen für DB-Endpoints gesetzt:")
        logger.error("      - CHROMA_HOST, CHROMA_PORT (Vector)")
        logger.error("      - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD (Graph)")
        logger.error("      - POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB (Relational)")
        logger.error("      - COUCHDB_URL (File, optional)")
        logger.error("")
        logger.error("✅ LÖSUNG:")
        logger.error("   1. Starte UDS3 Remote Service")
        logger.error("   2. Prüfe Erreichbarkeit der Remote-DBs")
        logger.error("   3. Starte dann VERITAS Backend")
        logger.error("")
        logger.error("❌ KEIN FALLBACK - Minimal-Rumpf erforderlich!")
        logger.error("   VERITAS benötigt mindestens Vector + Graph + Relational.")
        logger.error("=" * 80)
        raise RuntimeError(
            "VERITAS Backend kann ohne UDS3 Remote Service nicht starten! "
            "Mindestens Vector, Graph und Relational DBs müssen verfügbar sein."
        )
    
    # Initialize Intelligent Multi-Agent Pipeline - REQUIRED!
    logger.info("🔄 Initialisiere Intelligent Multi-Agent Pipeline...")
    
    try:
        app.state.pipeline = await get_intelligent_pipeline()
        logger.info("✅ Intelligent Pipeline initialisiert")
    except Exception as e:
        logger.error(f"❌ KRITISCHER FEHLER: Pipeline konnte nicht initialisiert werden!")
        logger.error(f"   Fehler: {e}")
        raise RuntimeError("Pipeline initialization failed - cannot start VERITAS") from e
    
    # Initialize Streaming Progress - REQUIRED!
    logger.info("🔄 Initialisiere Streaming Progress Manager...")
    
    try:
        app.state.streaming = create_progress_manager()
        logger.info("✅ Streaming Progress Manager initialisiert")
    except Exception as e:
        logger.error(f"❌ KRITISCHER FEHLER: Streaming konnte nicht initialisiert werden!")
        logger.error(f"   Fehler: {e}")
        raise RuntimeError("Streaming initialization failed - cannot start VERITAS") from e
    
    # Initialize Query Service - REQUIRED!
    logger.info("🔄 Initialisiere Query Service...")
    
    try:
        app.state.query_service = QueryService(
            uds3=app.state.uds3,  # FIXED: richtige Parameter-Namen!
            pipeline=app.state.pipeline,
            streaming=app.state.streaming
        )
        logger.info("✅ Query Service initialisiert")
    except Exception as e:
        logger.error(f"❌ KRITISCHER FEHLER: Query Service konnte nicht initialisiert werden!")
        logger.error(f"   Fehler: {e}")
        raise RuntimeError("Query Service initialization failed - cannot start VERITAS") from e
<<<<<<< Updated upstream
    
=======

    # Initialize / register a shared Ollama client on app.state for reuse
    try:
        from backend.agents.veritas_ollama_client import VeritasOllamaClient

        try:
            app.state.ollama_client = VeritasOllamaClient()
            # initialize (health + model list) but do not fail hard if unavailable
            try:
                await app.state.ollama_client.initialize()
                logger.info("✅ Shared Ollama client initialized and stored in app.state")
            except Exception as e:
                logger.warning(f"⚠️ Shared Ollama client initialization failed (continuing): {e}")
                # keep the instance (may be offline_mode=True)
                app.state.ollama_client.offline_mode = True
        except Exception as e:
            logger.warning(f"⚠️ Could not create VeritasOllamaClient: {e}")
            app.state.ollama_client = None
    except ImportError:
        logger.info("ℹ️ VeritasOllamaClient not available in environment - skipping shared client setup")

>>>>>>> Stashed changes
    # Startup Summary
    logger.info("=" * 80)
    logger.info("✅ VERITAS Backend Ready!")
    logger.info("=" * 80)
    
    # Determine protocol based on PKI status
    protocol = "https" if app.state.pki_enabled else "http"
    logger.info(f"📍 API Base: {protocol}://localhost:5000/api")
    logger.info(f"📖 Docs: {protocol}://localhost:5000/docs")
    logger.info(f"📊 Health: {protocol}://localhost:5000/api/system/health")
    logger.info("=" * 80)
    logger.info("🔧 Components:")
    logger.info(f"   PKI: {'✅ Active (HTTPS)' if app.state.pki_enabled else 'ℹ️  Inactive (HTTP)'}")
    logger.info(f"   UDS3: ✅ Active (ChromaDB)")
    logger.info(f"   Pipeline: ✅ Active (14 Agents)")
    logger.info(f"   Streaming: ✅ Active")
    logger.info(f"   SSE: {'✅ Active' if SSE_AVAILABLE else 'ℹ️  Not available'}")
    logger.info(f"   Query Service: ✅ Active")
    logger.info("=" * 80)
    
    api_info = get_api_info()
    logger.info(f"🎯 API Version: {api_info['version']}")
    logger.info(f"📦 Modules: {', '.join(api_info['modules'])}")
    logger.info("=" * 80)
    logger.info("🌐 Endpoints:")
    logger.info("   POST /api/query - Unified Query (alle Modi)")
    logger.info("   POST /api/query/ask - Simple Ask")
    logger.info("   POST /api/query/rag - RAG Query")
    logger.info("   POST /api/query/hybrid - Hybrid Search")
    logger.info("   POST /api/query/stream - Streaming Query")
    logger.info("   GET  /api/agent/list - Agent Liste")
    logger.info("   GET  /api/system/health - Health Check")
    logger.info("   GET  /api/system/info - System Info")
    if SSE_AVAILABLE:
        logger.info("   --- SSE Streaming (NEW!) ---")
        logger.info("   GET  /api/sse/progress/{session_id} - Agent Progress")
        logger.info("   GET  /api/sse/metrics - System Metrics")
        logger.info("   GET  /api/sse/jobs/{job_id} - Job Progress")
        logger.info("   GET  /api/sse/quality/{session_id} - Quality Gates")
    logger.info("=" * 80)
    
    yield
    
    # ===== SHUTDOWN =====
    logger.info("=" * 80)
    logger.info("🛑 VERITAS Backend - Shutting Down")
    logger.info("=" * 80)
    
    # PKI Cleanup
    if hasattr(app.state, 'pki_client') and app.state.pki_client:
        try:
            logger.info("🔐 Cleaning up PKI client...")
            # PKI client cleanup (if needed)
            app.state.pki_client = None
            logger.info("✅ PKI client cleaned up")
        except Exception as e:
            logger.warning(f"⚠️  PKI cleanup error: {e}")
    
    # Shutdown UDS3 PolyglotManager
    if hasattr(app.state, 'uds3') and app.state.uds3:
        try:
            if hasattr(app.state.uds3, 'shutdown'):
                app.state.uds3.shutdown()
            logger.info("✅ UDS3 PolyglotManager heruntergefahren")
        except Exception as e:
            logger.warning(f"⚠️  UDS3 Shutdown: {e}")
    logger.info("=" * 80)
    
    # Cleanup
    if hasattr(app.state, 'uds3') and app.state.uds3:
        try:
            logger.info("🔄 Closing UDS3 connections...")
            # UDS3 cleanup if needed
            logger.info("✅ UDS3 closed")
        except Exception as e:
            logger.error(f"❌ UDS3 cleanup error: {e}")
<<<<<<< Updated upstream
    
=======

    # Close shared Ollama client if present
    if hasattr(app.state, "ollama_client") and app.state.ollama_client:
        try:
            try:
                await app.state.ollama_client.close()
                logger.info("✅ Shared Ollama client closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing shared Ollama client: {e}")
        except Exception:
            pass

>>>>>>> Stashed changes
    logger.info("✅ Shutdown complete")
    logger.info("=" * 80)

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="VERITAS Unified Backend",
    description=(
        "Konsolidiertes Backend mit allen Features:\n\n"
        "- **UDS3 v2.0.0** - Polyglot Database Integration\n"
        "- **Intelligent Pipeline** - Multi-Agent System\n"
        "- **Hybrid Search** - BM25 + Dense + RRF\n"
        "- **Streaming** - Real-time Progress Updates\n"
        "- **Unified Response** - IEEE Citations (35+ Felder)\n\n"
        "Alle Query-Modi nutzen dasselbe Response-Format."
    ),
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ============================================================================
# CORS Configuration
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: In production specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# TLS/HTTPS Middleware
# ============================================================================

if TLS_AVAILABLE:
    try:
        add_tls_middleware(app)
        logger.info("✅ TLS/HTTPS middleware added")
    except Exception as e:
        logger.warning(f"⚠️  TLS middleware error: {e}")
else:
    logger.warning("⚠️  TLS module not available - HTTPS enforcement disabled")

# ============================================================================
# Mount API Router
# ============================================================================

app.include_router(api_router)
logger.info("✅ API Router mounted at /api")

# ============================================================================
# Mount SSE Router (Server-Sent Events)
# ============================================================================

if SSE_AVAILABLE and sse_router:
    app.include_router(sse_router)
    logger.info("✅ SSE Router mounted at /api/sse")
    
    # Initialize SSE endpoints with StreamingManager (if available)
    # Note: StreamingManager initialized later in lifespan, this is OK
    # SSE endpoints work standalone or with StreamingManager
    init_sse_endpoints(None)  # Will be updated in lifespan
    logger.info("✅ SSE Endpoints initialized (will connect to StreamingManager on startup)")

# ============================================================================
# Mount MCP HTTP Bridge (Office Adapter)
# ============================================================================

if MCP_HTTP_AVAILABLE and mcp_http_router:
    app.include_router(mcp_http_router)
    logger.info("✅ MCP HTTP Bridge mounted at /api/mcp")

# ============================================================================
# Mount Office Ingestion API (RAG Upload)
# ============================================================================

if OFFICE_INGESTION_AVAILABLE and office_ingestion_router:
    app.include_router(office_ingestion_router)
    logger.info("✅ Office Ingestion API mounted at /api/office")

# ============================================================================
# Serve Office Add-in static files (Word Taskpane)
# ============================================================================

try:
    office_dir = os.path.join(project_root, "desktop", "word-addin")
    if os.path.isdir(office_dir):
        app.mount("/office", StaticFiles(directory=office_dir, html=True), name="office")
        logger.info("✅ Office Add-in static files mounted at /office")
    else:
        logger.info("ℹ️  Office Add-in directory not found (desktop/word-addin)")
except Exception as e:
    logger.warning(f"⚠️  Failed to mount Office static files: {e}")

# ============================================================================
# Mount Authentication Router
# ============================================================================

try:
    from backend.api.auth_endpoints import router as auth_router
    app.include_router(auth_router)
    logger.info("✅ Authentication Router mounted at /auth")
except ImportError as e:
    logger.warning(f"⚠️  Authentication router not available: {e}")

# ============================================================================
# Mount Chart API Router (Vector Chart Agent)
# ============================================================================

try:
    from backend.api.chart_endpoints import router as chart_router
    app.include_router(chart_router)
    logger.info("✅ Chart API Router mounted at /api/charts")
except ImportError as e:
    logger.warning(f"⚠️  Chart API router not available: {e}")

# ============================================================================
# Mount Presentation API Router (Presentation Canvas Agent)
# ============================================================================

try:
    from backend.api.presentation_endpoints import router as presentation_router
    app.include_router(presentation_router)
    logger.info("✅ Presentation API Router mounted at /api/presentations")
except ImportError as e:
    logger.warning(f"⚠️  Presentation API router not available: {e}")

# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - System information"""
    api_info = get_api_info()
    
    return {
        "service": "VERITAS Unified Backend",
        "version": "4.0.0",
        "description": "Konsolidiertes Backend mit Unified Response Model",
        "api": {
            "base": "/api",
            "version": api_info["version"],
            "modules": api_info["modules"]
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "query": "/api/query",
            "health": "/api/system/health",
            "info": "/api/system/info"
        },
        "features": {
            "unified_response": True,
            "ieee_citations": True,
            "multi_mode": True,
            "uds3_v2": UDS3_AVAILABLE,
            "intelligent_pipeline": INTELLIGENT_PIPELINE_AVAILABLE,
            "streaming": STREAMING_AVAILABLE
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health():
    """Quick health check (alias for /api/system/health)"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "uds3": UDS3_AVAILABLE and app.state.uds3 is not None,
            "pipeline": INTELLIGENT_PIPELINE_AVAILABLE and app.state.pipeline is not None,
            "streaming": STREAMING_AVAILABLE and app.state.streaming is not None
        }
    }

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Configuration
    host = os.getenv("VERITAS_API_HOST", "0.0.0.0")
    port = int(os.getenv("VERITAS_API_PORT", "5000"))
    reload = os.getenv("VERITAS_API_RELOAD", "true").lower() == "true"
    
    # Check if PKI is configured
    use_https = PKI_AVAILABLE and os.getenv("PKI_SERVER_URL") is not None
    protocol = "https" if use_https else "http"
    
    logger.info("=" * 80)
    logger.info("🚀 Starting VERITAS Unified Backend")
    logger.info("=" * 80)
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Protocol: {protocol.upper()}")
    logger.info(f"Reload: {reload}")
    logger.info(f"API Base: {protocol}://{host}:{port}/api")
    logger.info(f"Docs: {protocol}://{host}:{port}/docs")
    logger.info("=" * 80)
    
    # Prepare SSL configuration if PKI is available
    ssl_keyfile = None
    ssl_certfile = None
    ssl_ca_certs = None
    
    if use_https:
        try:
            # Initialize temporary PKI client to get certificate paths
            pki_server_url = os.getenv("PKI_SERVER_URL", "https://localhost:8443")
            service_id = os.getenv("SERVICE_ID", "veritas-backend")
            # Retrieve CA password securely via SecretsManager
            try:
                from backend.security.secrets import get_vcc_ca_password
                ca_password = get_vcc_ca_password() or "your-secure-ca-password"
            except Exception:
                ca_password = os.getenv("VCC_CA_PASSWORD", "your-secure-ca-password")
<<<<<<< Updated upstream
            
            temp_pki = PKIClient(
                pki_server_url=pki_server_url,
                service_id=service_id,
                ca_password=ca_password
            )
            
            cert_paths = temp_pki.get_certificate_paths()
=======

            temp_pki = PKIClient(pki_server_url=pki_server_url, service_id=service_id, ca_password=ca_password)

            # Some PKI client implementations (older/newer) may not provide
            # `get_certificate_paths`. Guard against AttributeError and
            # fall back to HTTP if certificate paths cannot be obtained.
            try:
                cert_paths = temp_pki.get_certificate_paths()
            except AttributeError:
                logger.warning("⚠️ PKI client does not expose 'get_certificate_paths' - using HTTP")
                cert_paths = None

>>>>>>> Stashed changes
            if cert_paths:
                ssl_keyfile = cert_paths.get("key")
                ssl_certfile = cert_paths.get("cert")
                ssl_ca_certs = cert_paths.get("ca")
                logger.info(f"🔐 HTTPS enabled with PKI certificates")
                logger.info(f"   Cert: {ssl_certfile}")
                logger.info(f"   Key: {ssl_keyfile}")
                logger.info(f"   CA: {ssl_ca_certs}")
            else:
                logger.warning("⚠️  PKI configured but certificates not found - using HTTP")
                use_https = False
                protocol = "http"
        except Exception as e:
            logger.error(f"❌ Failed to setup SSL: {e}")
            logger.warning("⚠️  Falling back to HTTP")
            use_https = False
            protocol = "http"
    
    logger.info("=" * 80)
    
    uvicorn.run(
        "backend.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        ssl_keyfile=ssl_keyfile if use_https else None,
        ssl_certfile=ssl_certfile if use_https else None,
        ssl_ca_certs=ssl_ca_certs if use_https else None
    )
