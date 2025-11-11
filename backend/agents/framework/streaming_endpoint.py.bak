"""
FastAPI WebSocket Endpoint for Agent Streaming
==============================================

FastAPI-compatible WebSocket endpoints for real-time agent execution streaming.

Usage:
    from fastapi import FastAPI
    from streaming_endpoint import create_streaming_router

    app = FastAPI()
    router = create_streaming_router(streaming_manager)
    app.include_router(router)

Created: 2025-10-08
"""

import asyncio
import json
import logging
from typing import Optional

try:
    from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
    from fastapi.responses import JSONResponse

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

    # Create placeholder for when FastAPI not available
    class APIRouter:
        def __init__(self, *args, **kwargs):
            pass

        def websocket(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

        def get(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator


from framework.streaming_manager import StreamEvent, StreamingManager

logger = logging.getLogger(__name__)


def create_streaming_router(streaming_manager: StreamingManager) -> APIRouter:
    """
    Create FastAPI router with WebSocket endpoints.

    Args:
        streaming_manager: StreamingManager instance

    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/api/v1/streaming", tags=["streaming"])

    @router.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str, plan_id: Optional[str] = Query(None)):
        """
        WebSocket endpoint for real-time streaming.

        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
            plan_id: Optional plan ID to subscribe to immediately
        """
        await websocket.accept()

        # Register client
        subscribe_to = [plan_id] if plan_id else []
        await streaming_manager.register_client(client_id, websocket, subscribe_to)

        logger.info(f"WebSocket connected: {client_id}")

        try:
            while True:
                # Receive messages from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle client messages
                await handle_client_message(streaming_manager, client_id, message)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {client_id}")
            await streaming_manager.unregister_client(client_id)
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
            await streaming_manager.unregister_client(client_id)

    @router.get("/clients")
    async def get_clients():
        """Get connected client count."""
        return {"client_count": streaming_manager.get_client_count(), "clients": list(streaming_manager.clients.keys())}

    @router.get("/plans/{plan_id}/subscribers")
    async def get_plan_subscribers(plan_id: str):
        """Get subscriber count for a plan."""
        return {"plan_id": plan_id, "subscriber_count": streaming_manager.get_plan_subscriber_count(plan_id)}

    @router.get("/plans/{plan_id}/history")
    async def get_plan_history(plan_id: str):
        """Get event history for a plan."""
        history = streaming_manager.get_event_history(plan_id)
        return {"plan_id": plan_id, "event_count": len(history), "events": [event.to_dict() for event in history]}

    return router


async def handle_client_message(streaming_manager: StreamingManager, client_id: str, message: dict):
    """
    Handle client WebSocket message.

    Args:
        streaming_manager: StreamingManager instance
        client_id: Client identifier
        message: Parsed message from client
    """
    action = message.get("action")

    if action == "subscribe":
        plan_id = message.get("plan_id")
        if plan_id:
            await streaming_manager.subscribe(client_id, plan_id)
            logger.info(f"Client {client_id} subscribed to {plan_id}")

    elif action == "unsubscribe":
        plan_id = message.get("plan_id")
        if plan_id:
            await streaming_manager.unsubscribe(client_id, plan_id)
            logger.info(f"Client {client_id} unsubscribed from {plan_id}")

    elif action == "ping":
        # Send pong
        await streaming_manager._send_to_client(
            client_id, StreamEvent(event_type="pong", plan_id="system", data={"timestamp": message.get("timestamp")})
        )

    else:
        logger.warning(f"Unknown action from client {client_id}: {action}")


# ========================================
# Usage Example
# ========================================


def create_app_with_streaming():
    """
    Example: Create FastAPI app with streaming support.

    Returns:
        Configured FastAPI application
    """
    if not FASTAPI_AVAILABLE:
        print("FastAPI not available - install with: pip install fastapi uvicorn")
        return None

    from fastapi import FastAPI

    app = FastAPI(title="VERITAS Agent Streaming API")

    # Create streaming manager
    streaming_manager = StreamingManager()

    # Create and mount router
    router = create_streaming_router(streaming_manager)
    app.include_router(router)

    @app.get("/")
    async def root():
        return {
            "service": "VERITAS Agent Streaming API",
            "version": "1.0.0",
            "websocket_endpoint": "/api/v1/streaming/ws/{client_id}?plan_id={plan_id}",
        }

    # Store manager in app state
    app.state.streaming_manager = streaming_manager

    return app


if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        app = create_app_with_streaming()
        print("FastAPI app created with streaming support")
        print("To run: uvicorn streaming_endpoint:app --reload")
    else:
        print("FastAPI not installed - skipping endpoint creation")
        print("Install with: pip install fastapi uvicorn websockets")
