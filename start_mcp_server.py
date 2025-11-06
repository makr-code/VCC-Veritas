"""
Startet den VERITAS MCP Server.

Nutzung:
  - Standard (stdio, erfordert MCP-SDK):
      python start_mcp_server.py

  - CLI-Demo (ohne MCP-SDK möglich):
      python start_mcp_server.py --cli
"""

from backend.mcp.veritas_mcp_server import main


if __name__ == "__main__":
    main()
