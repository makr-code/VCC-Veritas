"""
WebSocket Router für Real-time ThemisDB/UDS3 Adapter Communication

Erstellt: 7. November 2025
Features:
- Real-time Vector Search mit Streaming Results
- Live Adapter Status Updates
- Query Log Streaming
- Bidirektionale Kommunikation
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.adapters.adapter_factory import get_database_adapter, is_themisdb_available, is_uds3_available

logger = logging.getLogger(__name__)

websocket_router = APIRouter(prefix="/ws", tags=["WebSocket"])


# ===========================
# Connection Manager
# ===========================


class ConnectionManager:
    """
    Verwaltet aktive WebSocket-Verbindungen
    Unterstützt Broadcast und gezielte Nachrichten
    """

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str, metadata: Optional[Dict] = None):
        """
        Registriert neue WebSocket-Verbindung
        """
        await websocket.accept()

        if client_id not in self.active_connections:
            self.active_connections[client_id] = []

        self.active_connections[client_id].append(websocket)
        self.connection_metadata[websocket] = {
            "client_id": client_id,
            "connected_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        logger.info(f"WebSocket connected: client_id={client_id}, total_connections={self.total_connections}")

    def disconnect(self, websocket: WebSocket, client_id: str):
        """
        Entfernt WebSocket-Verbindung
        """
        try:
            if client_id in self.active_connections:
                self.active_connections[client_id].remove(websocket)

                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]

            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]

            logger.info(f"WebSocket disconnected: client_id={client_id}, remaining={self.total_connections}")

        except ValueError:
            pass

    async def send_personal_message(self, message: dict, client_id: str):
        """
        Sendet Nachricht an alle Verbindungen eines Clients
        """
        if client_id in self.active_connections:
            disconnected = []

            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to {client_id}: {e}")
                    disconnected.append(connection)

            # Cleanup disconnected
            for conn in disconnected:
                self.disconnect(conn, client_id)

    async def broadcast(self, message: dict, exclude_client: Optional[str] = None):
        """
        Sendet Nachricht an alle verbundenen Clients
        """
        for client_id, connections in list(self.active_connections.items()):
            if exclude_client and client_id == exclude_client:
                continue

            await self.send_personal_message(message, client_id)

    @property
    def total_connections(self) -> int:
        """Gesamtzahl aktiver Verbindungen"""
        return sum(len(conns) for conns in self.active_connections.values())

    @property
    def active_clients(self) -> Set[str]:
        """Set aller verbundenen Client-IDs"""
        return set(self.active_connections.keys())


# Global Connection Manager
manager = ConnectionManager()


# ===========================
# WebSocket Endpoints
# ===========================


@websocket_router.websocket("/search")
async def websocket_search(websocket: WebSocket, client_id: str = Query(..., description="Unique client identifier")):
    """
    Real-time Vector Search mit progressivem Ergebnis-Streaming

    **Client sendet:**
    ```json
    {
      "action": "search",
      "query": "machine learning best practices",
      "top_k": 10,
      "collection": "documents",
      "threshold": 0.7
    }
    ```

    **Server antwortet:**
    ```json
    {
      "type": "search_started",
      "query": "...",
      "timestamp": "2025 - 11-07T10:30:00"
    }

    {
      "type": "result",
      "data": {...},
      "index": 0,
      "total": 10,
      "score": 0.95
    }

    {
      "type": "search_complete",
      "total_results": 10,
      "duration_ms": 45.2,
      "adapter_used": "themis"
    }
    ```

    **Ping/Pong:**
    ```json
    { "action": "ping" }  →  { "type": "pong", "timestamp": "..." }
    ```
    """
    await manager.connect(websocket, client_id, {"endpoint": "search"})

    try:
        # Welcome Message
        await websocket.send_json(
            {
                "type": "connected",
                "client_id": client_id,
                "endpoint": "search",
                "timestamp": datetime.now().isoformat(),
                "message": "Ready to receive search queries",
            }
        )

        while True:
            # Warte auf Client-Nachricht
            data = await websocket.receive_json()
            action = data.get("action")

            # Ping/Pong für Keep-Alive
            if action == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                continue

            # Vector Search
            elif action == "search":
                query = data.get("query")
                top_k = data.get("top_k", 5)
                collection = data.get("collection", "documents")
                threshold = data.get("threshold")

                if not query:
                    await websocket.send_json({"type": "error", "message": "Missing required field: query"})
                    continue

                start_time = datetime.now()

                try:
                    # Adapter abrufen
                    adapter = await get_database_adapter()
                    adapter_name = "themis" if await is_themisdb_available() else "uds3"

                    # Search Started
                    await websocket.send_json(
                        {
                            "type": "search_started",
                            "query": query,
                            "top_k": top_k,
                            "collection": collection,
                            "adapter": adapter_name,
                            "timestamp": start_time.isoformat(),
                        }
                    )

                    # Führe Suche aus
                    results = await adapter.vector_search(query=query, top_k=top_k, collection=collection, threshold=threshold)

                    # Stream Results progressiv
                    for i, result in enumerate(results):
                        await websocket.send_json(
                            {
                                "type": "result",
                                "data": result,
                                "index": i,
                                "total": len(results),
                                "score": result.get("score", 0.0),
                            }
                        )
                        # Kleine Verzögerung für progressive UI
                        await asyncio.sleep(0.05)

                    # Search Complete
                    duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                    await websocket.send_json(
                        {
                            "type": "search_complete",
                            "total_results": len(results),
                            "duration_ms": round(duration_ms, 2),
                            "adapter_used": adapter_name,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                except Exception as e:
                    logger.error(f"Search error for client {client_id}: {e}")
                    await websocket.send_json(
                        {"type": "error", "message": f"Search failed: {str(e)}", "timestamp": datetime.now().isoformat()}
                    )

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown action: {action}"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        logger.info(f"Client {client_id} disconnected from search endpoint")

    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(websocket, client_id)


@websocket_router.websocket("/adapter/status")
async def websocket_adapter_status(
    websocket: WebSocket,
    client_id: str = Query(..., description="Unique client identifier"),
    interval: int = Query(5, ge=1, le=60, description="Update interval in seconds"),
):
    """
    Real-time Adapter Status Updates

    Sendet periodisch Status-Updates über ThemisDB/UDS3 Verfügbarkeit,
    Metriken und aktuelle Konfiguration.

    **Server sendet (alle {interval} Sekunden):**
    ```json
    {
      "type": "status_update",
      "timestamp": "2025 - 11-07T10:30:00",
      "current_adapter": "themis",
      "themis": {
        "available": true,
        "query_count": 1523,
        "avg_latency_ms": 34.2,
        "success_rate": 0.987
      },
      "uds3": {
        "available": true,
        "query_count": 245,
        "avg_latency_ms": 78.5
      },
      "failover_enabled": true,
      "active_connections": 12
    }
    ```
    """
    await manager.connect(websocket, client_id, {"endpoint": "adapter_status", "interval": interval})

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "client_id": client_id,
                "endpoint": "adapter_status",
                "update_interval_seconds": interval,
                "timestamp": datetime.now().isoformat(),
            }
        )

        while True:
            try:
                # Adapter Status sammeln
                adapter = await get_database_adapter()
                themis_available = await is_themisdb_available()
                uds3_available = await is_uds3_available()

                current_adapter = "themis" if themis_available else "uds3"

                # Status-Nachricht
                status_update = {
                    "type": "status_update",
                    "timestamp": datetime.now().isoformat(),
                    "current_adapter": current_adapter,
                    "themis": {"available": themis_available},
                    "uds3": {"available": uds3_available},
                    "failover_enabled": True,
                    "active_websocket_connections": manager.total_connections,
                    "active_clients": len(manager.active_clients),
                }

                # Adapter Stats hinzufügen falls verfügbar
                if hasattr(adapter, "get_stats"):
                    stats = adapter.get_stats()
                    if themis_available:
                        status_update["themis"].update(stats)
                    else:
                        status_update["uds3"].update(stats)

                await websocket.send_json(status_update)

            except Exception as e:
                logger.error(f"Error collecting adapter status: {e}")
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"Failed to collect status: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # Warte bis zum nächsten Update
            await asyncio.sleep(interval)

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        logger.info(f"Client {client_id} disconnected from adapter status")


@websocket_router.websocket("/logs")
async def websocket_logs(
    websocket: WebSocket,
    client_id: str = Query(..., description="Unique client identifier"),
    log_level: str = Query("INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
):
    """
    Real-time Log Streaming

    Streamt Backend-Logs in Echtzeit an verbundene Clients.
    Nützlich für Debugging und Monitoring.

    **Server sendet:**
    ```json
    {
      "type": "log",
      "level": "INFO",
      "message": "Vector search completed",
      "timestamp": "2025 - 11-07T10:30:00.123",
      "logger": "backend.adapters.themisdb_adapter",
      "extra": {...}
    }
    ```
    """
    await manager.connect(websocket, client_id, {"endpoint": "logs", "log_level": log_level})

    # Custom WebSocket Log Handler
    class WebSocketLogHandler(logging.Handler):
        def __init__(self, websocket: WebSocket, level=logging.INFO):
            super().__init__(level)
            self.websocket = websocket
            self.formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        def emit(self, record):
            try:
                log_entry = {
                    "type": "log",
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "logger": record.name,
                    "filename": record.filename,
                    "lineno": record.lineno,
                }

                # Extra Fields
                if hasattr(record, "extra"):
                    log_entry["extra"] = record.extra

                # Async send via event loop
                asyncio.create_task(self.websocket.send_json(log_entry))

            except Exception:
                self.handleError(record)

    # Handler registrieren
    handler = WebSocketLogHandler(websocket, level=getattr(logging, log_level))
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "client_id": client_id,
                "endpoint": "logs",
                "log_level": log_level,
                "timestamp": datetime.now().isoformat(),
                "message": f"Streaming logs at {log_level} level",
            }
        )

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_json()

                if data.get("action") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})

                elif data.get("action") == "change_level":
                    new_level = data.get("level", "INFO")
                    handler.setLevel(getattr(logging, new_level))
                    await websocket.send_json({"type": "info", "message": f"Log level changed to {new_level}"})

            except WebSocketDisconnect:
                break

    finally:
        root_logger.removeHandler(handler)
        manager.disconnect(websocket, client_id)
        logger.info(f"Client {client_id} disconnected from logs")


@websocket_router.websocket("/graph/traverse")
async def websocket_graph_traverse(websocket: WebSocket, client_id: str = Query(..., description="Unique client identifier")):
    """
    Real-time Graph Traversal mit progressivem Node-Streaming

    **Client sendet:**
    ```json
    {
      "action": "traverse",
      "start_vertex": "doc123",
      "edge_collection": "citations",
      "direction": "outbound",
      "max_depth": 3
    }
    ```

    **Server streamt:**
    ```json
    {
      "type": "traversal_started",
      "start_vertex": "doc123",
      "timestamp": "..."
    }

    {
      "type": "node",
      "data": {...},
      "depth": 1,
      "path": ["doc123", "doc456"]
    }

    {
      "type": "traversal_complete",
      "total_nodes": 15,
      "total_edges": 18,
      "max_depth_reached": 3
    }
    ```
    """
    await manager.connect(websocket, client_id, {"endpoint": "graph_traverse"})

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "client_id": client_id,
                "endpoint": "graph_traverse",
                "timestamp": datetime.now().isoformat(),
            }
        )

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                continue

            elif action == "traverse":
                start_vertex = data.get("start_vertex")
                edge_collection = data.get("edge_collection", "edges")
                direction = data.get("direction", "outbound")
                max_depth = data.get("max_depth", 3)

                if not start_vertex:
                    await websocket.send_json({"type": "error", "message": "Missing required field: start_vertex"})
                    continue

                try:
                    adapter = await get_database_adapter()

                    await websocket.send_json(
                        {
                            "type": "traversal_started",
                            "start_vertex": start_vertex,
                            "edge_collection": edge_collection,
                            "direction": direction,
                            "max_depth": max_depth,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    # Graph Traversal
                    result = await adapter.graph_traverse(
                        start_vertex=start_vertex, edge_collection=edge_collection, direction=direction, max_depth=max_depth
                    )

                    # Stream Vertices progressiv
                    vertices = result.get("vertices", [])
                    edges = result.get("edges", [])

                    for i, vertex in enumerate(vertices):
                        await websocket.send_json({"type": "node", "data": vertex, "index": i, "total": len(vertices)})
                        await asyncio.sleep(0.05)

                    # Stream Edges
                    for i, edge in enumerate(edges):
                        await websocket.send_json({"type": "edge", "data": edge, "index": i, "total": len(edges)})
                        await asyncio.sleep(0.05)

                    await websocket.send_json(
                        {
                            "type": "traversal_complete",
                            "total_nodes": len(vertices),
                            "total_edges": len(edges),
                            "max_depth_reached": max_depth,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                except Exception as e:
                    logger.error(f"Graph traversal error: {e}")
                    await websocket.send_json({"type": "error", "message": f"Traversal failed: {str(e)}"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)


# ===========================
# Admin/Monitoring Endpoints
# ===========================


@websocket_router.get("/connections")
async def get_active_connections():
    """
    Gibt Übersicht über aktive WebSocket-Verbindungen zurück
    (REST endpoint für Monitoring)
    """
    return {
        "total_connections": manager.total_connections,
        "active_clients": len(manager.active_clients),
        "clients": list(manager.active_clients),
        "timestamp": datetime.now().isoformat(),
    }
