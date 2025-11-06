"""
VERITAS MCP Package
====================

Dieses Paket enthält den MCP-Server (Model Context Protocol) zur Integration
von Desktop-Anwendungen (z. B. Microsoft Word/Excel, VS Code, Claude Desktop)
mit der VERITAS-Backend-Funktionalität.

Enthaltene Module:
- veritas_mcp_server.py  → MCP-Server-Startpunkt (stdio)

Hinweis:
Der MCP-Server ist unabhängig vom FastAPI-Backend und wird als separater
Prozess über stdio gestartet. Dadurch bleibt die Microservice-Architektur
unberührt und es entstehen keine Breaking Changes.
"""

__all__ = [
    "veritas_mcp_server",
]
