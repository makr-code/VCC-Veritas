"""
VERITAS API Router
==================

Konsolidierte API-Router (FLACH - kein v3/ Unterordner!)

Router werden in backend/backend.py gemountet.
"""

from fastapi import APIRouter
from .query_router import query_router
from .agent_router import agent_router
from .system_router import system_router
from .office_api_router import router as office_router

# API Info
API_VERSION = "4.0.0"
API_MODULES = [
    "query",      # Query Processing
    "agent",      # Agent System
    "system",     # System Info
    "office",     # Office Add-in Integration
]

# Haupt-Router
api_router = APIRouter(prefix="/api")

# Mount Sub-Router
api_router.include_router(query_router, tags=["Query"])
api_router.include_router(agent_router, tags=["Agents"])
api_router.include_router(system_router, tags=["System"])
api_router.include_router(office_router, tags=["Office Add-in"])


def get_api_info():
    """Get API Information"""
    return {
        "version": API_VERSION,
        "modules": API_MODULES,
        "base_path": "/api",
        "documentation": "/docs"
    }


__all__ = [
    "api_router",
    "get_api_info",
    "query_router",
    "agent_router",
    "system_router"
]
