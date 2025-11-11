"""VERITAS API v3 - Modular REST API Architecture"""

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "3.0.0"
API_RELEASE_DATE = "2025-10-18"
API_STATUS = "implementation"

api_v3_router = APIRouter(prefix="/api/v3", tags=["API v3"])

try:
    from .adapter_router import adapter_router
    from .agent_router import agent_router
    from .compliance_router import compliance_router
    from .covina_router import covina_router
    from .database_router import router as database_router
    from .governance_router import governance_router
    from .immi_router import immi_router
    from .pki_router import pki_router
    from .query_router import query_router
    from .saga_router import saga_router
    from .system_router import system_router
    from .themis_router import themis_router
    from .uds3_router import uds3_router
    from .user_router import user_router
    from .vpb_router import vpb_router
    from .websocket_router import websocket_router

    api_v3_router.include_router(query_router)
    api_v3_router.include_router(agent_router)
    api_v3_router.include_router(system_router)
    api_v3_router.include_router(vpb_router)
    api_v3_router.include_router(covina_router)
    api_v3_router.include_router(pki_router)
    api_v3_router.include_router(immi_router)
    api_v3_router.include_router(saga_router)
    api_v3_router.include_router(compliance_router)
    api_v3_router.include_router(governance_router)
    api_v3_router.include_router(uds3_router)
    api_v3_router.include_router(themis_router)
    api_v3_router.include_router(adapter_router)
    api_v3_router.include_router(user_router)
    api_v3_router.include_router(database_router)
    api_v3_router.include_router(websocket_router)
except ImportError as e:
    print(f"Warning: {e}")


def get_v3_info() -> Dict[str, Any]:
    return {
        "version": API_VERSION,
        "status": API_STATUS,
        "modules": [
            "query",
            "agent",
            "system",
            "vpb",
            "covina",
            "pki",
            "immi",
            "saga",
            "compliance",
            "governance",
            "uds3",
            "themis",
            "adapters",
            "user",
            "database",
        ],
    }


@api_v3_router.get("/")
async def get_api_info():
    return {"message": "VERITAS API v3", "info": get_v3_info()}


__all__ = ["api_v3_router", "get_v3_info", "API_VERSION"]
