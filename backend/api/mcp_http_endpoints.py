"""
MCP HTTP Bridge Endpoints
=========================

HTTP-Adapter für Office Web Add-ins (Word/Excel/PowerPoint),
die nicht per stdio auf den MCP-Server zugreifen können.

Stellt ausgewählte MCP-Funktionen als HTTP-API bereit:
- Prompts: Auflisten und Rendern (Templates aus config/mcp_prompts.json)
- Tools: hybrid_search
- Resources: Dokumentenabruf (alias für veritas://documents/{id})
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException

from backend.mcp.veritas_mcp_server import (
    load_prompt_templates,
    tool_hybrid_search,
    resource_get_document,
)

router = APIRouter(prefix="/api/mcp", tags=["MCP HTTP Bridge"])


@router.get("/prompts")
async def list_prompts() -> Dict[str, Any]:
    """Listet verfügbare Prompt-Templates auf (Name, Beschreibung, Parameter-Schema)."""
    templates = load_prompt_templates()
    return {
        "count": len(templates),
        "prompts": [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in templates
        ],
    }


@router.post("/prompts/{name}/render")
async def render_prompt(name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rendert einen Prompt anhand des Templates und der übergebenen Parameter.
    Gibt die Message-Liste (system + user) zurück.
    """
    templates = load_prompt_templates()
    tmpl = next((t for t in templates if t.name == name), None)
    if not tmpl:
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
    try:
        # Erzeuge die Messages wie im MCP-Server
        user_message = tmpl.user_template.format(**(params or {}))
        return {
            "name": tmpl.name,
            "description": tmpl.description,
            "messages": [
                {"role": "system", "content": tmpl.system_message},
                {"role": "user", "content": user_message},
            ],
        }
    except KeyError as e:
        missing = str(e).strip("'")
        raise HTTPException(status_code=400, detail=f"Missing required parameter: {missing}")


@router.post("/tools/hybrid_search")
async def http_tool_hybrid_search(payload: Dict[str, Any]) -> Dict[str, Any]:
    """HTTP-Bridge für das Tool 'hybrid_search'."""
    query = payload.get("query")
    top_k = payload.get("top_k", 5)
    if not query or not isinstance(query, str) or not query.strip():
        raise HTTPException(status_code=400, detail="Field 'query' is required")
    result = await tool_hybrid_search(query.strip(), int(top_k))
    return result


@router.get("/resources/documents/{document_id}")
async def http_resource_document(document_id: str) -> Dict[str, Any]:
    """HTTP-Bridge für die Resource 'veritas://documents/{id}'"""
    result = await resource_get_document(document_id)
    return result
