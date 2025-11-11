#!/usr/bin/env python3
"""
VERITAS API v3 Backend - Clean Implementation
==============================================

Vollständig auf API v3 migriertes Backend.
Alle Legacy-Endpoints wurden entfernt.

Version: 3.0.0
Date: 18. Oktober 2025
Port: 5000
Docs: http://localhost:5000/docs
API: http://localhost:5000/api/v3/

Features:
- 12 Modular Router (58 Endpoints)
- UDS3 Integration
- Intelligent Pipeline Integration
- Streaming Progress System
- CORS enabled
"""

import asyncio
import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
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
    log_file = os.path.join(data_dir, "veritas_api_v3.log")

    # Format
    formatter = logging.Formatter(fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # File handler
    file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
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
# Import Optional Dependencies
# ============================================================================

# UDS3
try:
    import uds3
    from uds3.core import UDS3PolyglotManager  # ✨ UDS3 v2.0.0 (Legacy stable)

    UDS3_AVAILABLE = True
    logger.info("✅ UDS3 verfügbar (v2.0.0)")
except ImportError as e:
    UDS3_AVAILABLE = False
    logger.warning(f"⚠️  UDS3 nicht verfügbar: {e}")

# Intelligent Pipeline
try:
    from backend.agents.veritas_intelligent_pipeline import IntelligentMultiAgentPipeline, get_intelligent_pipeline
    from backend.agents.veritas_ollama_client import get_ollama_client

    INTELLIGENT_PIPELINE_AVAILABLE = True
    logger.info("✅ Intelligent Pipeline verfügbar")
except ImportError as e:
    INTELLIGENT_PIPELINE_AVAILABLE = False
    logger.warning(f"⚠️  Intelligent Pipeline nicht verfügbar: {e}")

# Streaming Progress
try:
    from shared.pipelines.veritas_streaming_progress import VeritasProgressManager, create_progress_manager

    STREAMING_AVAILABLE = True
    logger.info("✅ Streaming Progress verfügbar")
except ImportError as e:
    STREAMING_AVAILABLE = False
    logger.warning(f"⚠️  Streaming nicht verfügbar: {e}")

# API v3 Router
try:
    from backend.api.v3 import api_v3_router, get_v3_info

    API_V3_AVAILABLE = True
    logger.info("✅ API v3 Router verfügbar")
except ImportError as e:
    API_V3_AVAILABLE = False
    logger.error(f"❌ API v3 Router FEHLT: {e}")
    raise

# ============================================================================
# Lifecycle Management
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""

    # ===== STARTUP =====
    logger.info("=" * 70)
    logger.info("🚀 VERITAS API v3 Backend wird gestartet...")
    logger.info("=" * 70)

    # Initialize UDS3
    if UDS3_AVAILABLE:
        try:
            logger.info("🔧 Initialisiere UDS3 Polyglot Manager...")
            # ✨ NEU: UDS3 v2.0.0 Polyglot Manager
            backend_config = {
                "vector": {"enabled": True, "backend": "chromadb"},
                "graph": {"enabled": False},  # Optional: Neo4j aktivieren
                "relational": {"enabled": False},  # Optional: PostgreSQL aktivieren
                "file_storage": {"enabled": False},
            }
            app.state.uds3 = UDS3PolyglotManager(backend_config=backend_config, enable_rag=True)
            logger.info("✅ UDS3 Polyglot Manager initialisiert")
        except Exception as e:
            logger.warning(f"⚠️  UDS3 Initialization fehlgeschlagen: {e}")
            app.state.uds3 = None
    else:
        app.state.uds3 = None

    # Initialize Intelligent Pipeline
    if INTELLIGENT_PIPELINE_AVAILABLE:
        try:
            logger.info("🔧 Initialisiere Intelligent Pipeline...")
            app.state.intelligent_pipeline = await get_intelligent_pipeline()
            app.state.ollama_client = await get_ollama_client()
            logger.info("✅ Intelligent Pipeline initialisiert")
        except Exception as e:
            logger.warning(f"⚠️  Pipeline Initialization fehlgeschlagen: {e}")
            app.state.intelligent_pipeline = None
            app.state.ollama_client = None
    else:
        app.state.intelligent_pipeline = None
        app.state.ollama_client = None

    # Initialize Streaming Progress
    if STREAMING_AVAILABLE:
        try:
            logger.info("🔧 Initialisiere Streaming Progress Manager...")
            app.state.progress_manager = create_progress_manager()
            logger.info("✅ Progress Manager initialisiert")
        except Exception as e:
            logger.warning(f"⚠️  Progress Manager Initialization fehlgeschlagen: {e}")
            app.state.progress_manager = None
    else:
        app.state.progress_manager = None

    # Startup Summary
    logger.info("=" * 70)
    logger.info("✅ VERITAS API v3 Backend Ready!")
    logger.info("=" * 70)
    logger.info("📍 API Base: http://localhost:5000/api/v3")
    logger.info(f"📖 Docs: http://localhost:5000/docs")
    logger.info(f"📊 UDS3: {'✅ Active' if app.state.uds3 else '⚠️  Demo Mode'}")
    logger.info(f"🤖 Pipeline: {'✅ Active' if app.state.intelligent_pipeline else '⚠️  Demo Mode'}")
    logger.info(f"📡 Streaming: {'✅ Active' if app.state.progress_manager else '⚠️  Disabled'}")
    logger.info("=" * 70)

    v3_info = get_v3_info()
    logger.info(f"🎯 API v3 Version: {v3_info['version']}")
    logger.info(f"📦 Modules: {', '.join(v3_info['modules'])}")
    logger.info("=" * 70)

    yield

    # ===== SHUTDOWN =====
    logger.info("=" * 70)
    logger.info("🛑 VERITAS API v3 Backend wird heruntergefahren...")
    logger.info("=" * 70)

    # Cleanup (if needed)
    if hasattr(app.state, "uds3") and app.state.uds3:
        try:
            # UDS3 cleanup
            pass
        except Exception as e:
            logger.warning(f"⚠️  UDS3 Cleanup Fehler: {e}")

    logger.info("✅ Shutdown complete")
    logger.info("=" * 70)


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="VERITAS API v3",
    description="Modular REST API for VERITAS Knowledge Base System",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ============================================================================
# CORS Configuration
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Mount API v3 Router
# ============================================================================

if API_V3_AVAILABLE:
    app.include_router(api_v3_router)
    logger.info("✅ API v3 Router mounted at /api/v3")
else:
    logger.error("❌ API v3 Router konnte nicht gemountet werden!")

# ============================================================================
# Root Endpoints
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint - redirects to API v3"""
    v3_info = get_v3_info()
    return {
        "message": "VERITAS API v3 Backend",
        "version": "3.0.0",
        "api_base": " / api/v3",
        "documentation": " / docs",
        "api_info": v3_info,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "api": "v3",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "uds3": UDS3_AVAILABLE and app.state.uds3 is not None,
            "pipeline": INTELLIGENT_PIPELINE_AVAILABLE and app.state.intelligent_pipeline is not None,
            "streaming": STREAMING_AVAILABLE and app.state.progress_manager is not None,
        },
    }


# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code, "timestamp": datetime.now().isoformat()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc), "timestamp": datetime.now().isoformat()},
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Configuration
    # Default to localhost to avoid unintentionally exposing the service.
    host = os.getenv("VERITAS_API_HOST", "127.0.0.1")
    port = int(os.getenv("VERITAS_API_PORT", "5000"))
    reload = os.getenv("VERITAS_API_RELOAD", "false").lower() == "true"

    logger.info("=" * 70)
    logger.info("🚀 Starting VERITAS API v3 Backend")
    logger.info("=" * 70)
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Reload: {reload}")
    logger.info(f"API Base: http://{host}:{port}/api/v3")
    logger.info(f"Docs: http://{host}:{port}/docs")
    logger.info("=" * 70)

    uvicorn.run("veritas_api_backend_v3:app", host=host, port=port, reload=reload, log_level="info")
