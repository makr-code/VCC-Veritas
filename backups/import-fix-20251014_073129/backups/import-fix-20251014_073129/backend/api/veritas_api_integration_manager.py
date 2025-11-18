#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS API INTEGRATION MANAGER (Migrated from Covina)
=====================================================
Zentraler Manager für alle API-Endpunkte inkl. Worker-System

Features:
- FastAPI Integration Management
- Worker-System API Integration
- Quality-Endpoints Management
- Legacy API Support
- Health Monitoring
- Dynamic Router Registration

Author: VERITAS System
Created: 2025-09-21 (Migrated from Covina)
Version: 1.0.0
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Basis API System
try:
    from backend.api.veritas_api_backend import app as main_app

    MAIN_API_AVAILABLE = True
except ImportError:
    MAIN_API_AVAILABLE = False
    logging.error("Veritas API Backend nicht verfügbar")

# Worker API Integration
try:
    from backend.api.veritas_api_worker_integration import router as worker_router

    WORKER_API_AVAILABLE = True
except ImportError:
    WORKER_API_AVAILABLE = False
    logging.warning("Worker API nicht verfügbar")

# Quality API Module
try:
    from backend.api.veritas_api_quality_endpoints import router as quality_router

    QUALITY_API_AVAILABLE = True
except ImportError:
    QUALITY_API_AVAILABLE = False
    logging.warning("Quality API nicht verfügbar")

logger = logging.getLogger(__name__)


class VeritasAPIIntegrationManager:
    """
    Zentraler Manager für alle Veritas API-Endpunkte (Migrated from Covina)

    Integriert:
    - Haupt-FastAPI (veritas_api_backend)
    - Worker-System API (KGE, Keywords, Agent Engine)
    - Quality-Endpoints (Chunk Quality, RAG Optimization)
    - VPB-System API
    - Health & Monitoring
    """

    def __init__(self):
        self.main_app = main_app if MAIN_API_AVAILABLE else self._create_fallback_app()
        self.registered_routers = []
        self.api_status = {"main_api": MAIN_API_AVAILABLE, "worker_api": False, "quality_api": QUALITY_API_AVAILABLE}

        # System-Metriken
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "uptime_start": datetime.now(),
        }

        # API Integration
        self._integrate_apis()

        logger.info("🚀 Veritas API Integration Manager initialisiert")

    def _create_fallback_app(self) -> FastAPI:
        """Erstellt Fallback-App falls Haupt-API nicht verfügbar"""
        app = FastAPI(
            title="Veritas API Backend (Fallback)",
            description="Fallback-Implementation des Veritas API Systems",
            version="1.0.0-fallback",
        )

        @app.get("/health")
        async def fallback_health():
            return {"status": "fallback", "message": "Haupt-API nicht verfügbar"}

        return app

    def _integrate_apis(self):
        """Integriert alle verfügbaren API-Router in das Hauptsystem"""

        if not MAIN_API_AVAILABLE:
            logger.error("❌ Haupt-API nicht verfügbar - verwende Fallback")
            return

        # Worker API Integration
        if WORKER_API_AVAILABLE:
            try:
                self.main_app.include_router(worker_router)
                self.registered_routers.append("worker_api")
                self.api_status["worker_api"] = True
                logger.info("✅ Worker API erfolgreich integriert")
            except Exception as e:
                logger.error(f"❌ Worker API Integration fehlgeschlagen: {e}")

        # Quality API Integration
        if QUALITY_API_AVAILABLE:
            try:
                self.main_app.include_router(quality_router)
                self.registered_routers.append("quality_api")
                logger.info("✅ Quality API erfolgreich integriert")
            except Exception as e:
                logger.error(f"❌ Quality API Integration fehlgeschlagen: {e}")

        # Management-Endpunkte hinzufügen
        self._add_management_endpoints()

    def _add_management_endpoints(self):
        """Fügt Management-Endpunkte zur API hinzu"""

        @self.main_app.get("/api/system/status")
        async def get_veritas_system_status():
            """Status aller API-Systeme"""
            return {
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
                "apis": self.api_status,
                "registered_routers": self.registered_routers,
                "total_endpoints": len([route for route in self.main_app.routes if hasattr(route, "methods")]),
                "metrics": self.metrics,
                "system": "veritas",
            }

    def get_app(self) -> FastAPI:
        """Gibt die konfigurierte FastAPI-App zurück"""
        return self.main_app


# Factory Functions
def create_veritas_integration_manager() -> VeritasAPIIntegrationManager:
    """Factory-Funktion für Veritas API Integration Manager"""
    return VeritasAPIIntegrationManager()


# Globale Instanz
veritas_integration_manager = create_veritas_integration_manager()
integration_app = veritas_integration_manager.get_app()
