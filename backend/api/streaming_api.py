"""
VERITAS NLP Foundation - WebSocket Streaming API
================================================

FastAPI WebSocket endpoints for real-time process execution streaming.

Provides WebSocket endpoints for streaming NLP process execution progress
to connected clients in real-time.

Features:
- WebSocket endpoint /ws/process/{session_id}
- Real-time progress streaming
- Query execution with streaming
- Session-based isolation
- Error handling and graceful disconnection

Usage:
    # Start the API server
    uvicorn backend.api.streaming_api:app --host 0.0.0.0 --port 8000

    # Connect from client
    ws = websocket.connect("ws://localhost:8000/ws/process/session_123")

    # Send query
    ws.send(json.dumps({"query": "Bauantrag für Stuttgart"}))

    # Receive progress updates
    while True:
        message = ws.recv()
        event = json.loads(message)
        print(f"{event['percentage']:.1f}%: {event['message']}")

Created: 2025-10-14
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Optional
from uuid import uuid4

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.warning("⚠️ FastAPI not available")

# Import NLP services
try:
    from backend.models.streaming_progress import ProgressCallback
    from backend.services.nlp_service import NLPService
    from backend.services.process_builder import ProcessBuilder
    from backend.services.process_executor import ProcessExecutor

    NLP_SERVICES_AVAILABLE = True
except ImportError as e:
    NLP_SERVICES_AVAILABLE = False
    logging.warning(f"⚠️ NLP services not available: {e}")

# Import WebSocket bridge
try:
    from backend.services.websocket_progress_bridge import WebSocketProgressBridge

    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False
    logging.warning("⚠️ WebSocket bridge not available")


logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="VERITAS NLP Streaming API", version="1.0.0")

# Global services (initialized on startup)
nlp_service: Optional[NLPService] = None
process_builder: Optional[ProcessBuilder] = None
process_executor: Optional[ProcessExecutor] = None
active_sessions: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global nlp_service, process_builder, process_executor

    logger.info("Initializing VERITAS NLP services...")

    if NLP_SERVICES_AVAILABLE:
        try:
            nlp_service = NLPService()
            process_builder = ProcessBuilder(nlp_service)
            process_executor = ProcessExecutor(max_workers=4, use_agents=True)
            logger.info("✅ NLP services initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize NLP services: {e}")
    else:
        logger.warning("⚠️ NLP services not available")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "VERITAS NLP Streaming API",
        "version": "1.0.0",
        "endpoints": {"websocket": "/ws/process/{session_id}", "test_page": "/test", "health": "/health"},
        "status": {"nlp_services": NLP_SERVICES_AVAILABLE, "fastapi": FASTAPI_AVAILABLE, "bridge": BRIDGE_AVAILABLE},
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "nlp": nlp_service is not None,
            "builder": process_builder is not None,
            "executor": process_executor is not None,
        },
        "active_sessions": len(active_sessions),
    }


@app.websocket("/ws/process/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time process execution streaming.

    Protocol:
        Client → Server: {"query": "Bauantrag für Stuttgart"}
        Server → Client: {"event_type": "plan_started", "data": {...}}
        Server → Client: {"event_type": "step_progress", "data": {...}}
        Server → Client: {"event_type": "plan_completed", "data": {...}}

    Args:
        websocket: WebSocket connection
        session_id: Unique session identifier
    """
    logger.info(f"WebSocket connection request for session: {session_id}")

    # Accept connection
    await websocket.accept()

    # Register session
    active_sessions[session_id] = {
        "websocket": websocket,
        "connected_at": asyncio.get_event_loop().time(),
        "queries_processed": 0,
    }

    try:
        # Send welcome message
        await websocket.send_json(
            {
                "event_type": "connected",
                "session_id": session_id,
                "message": "Connected to VERITAS NLP Streaming API",
                "services_available": NLP_SERVICES_AVAILABLE,
            }
        )

        logger.info(f"✅ WebSocket connected: {session_id}")

        # Listen for queries
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            data = json.loads(message)

            logger.info(f"Received query from {session_id}: {data}")

            # Extract query
            if "query" not in data:
                await websocket.send_json({"event_type": "error", "message": "Missing 'query' field in request"})
                continue

            query = data["query"]

            # Process query with streaming
            if NLP_SERVICES_AVAILABLE and nlp_service and process_builder and process_executor:
                try:
                    # Create progress callback with WebSocket sender
                    callback = ProgressCallback()

                    async def send_progress(event):
                        """Send progress event to WebSocket client."""
                        try:
                            await websocket.send_json(
                                {
                                    "event_type": event.event_type.value,
                                    "session_id": session_id,
                                    "data": {
                                        "step_id": event.step_id,
                                        "step_name": event.step_name,
                                        "current_step": event.current_step,
                                        "total_steps": event.total_steps,
                                        "percentage": event.percentage,
                                        "status": event.status.value,
                                        "message": event.message,
                                        "execution_time": event.execution_time,
                                        "timestamp": event.timestamp,
                                        "error": event.error,
                                        "metadata": event.metadata,
                                    },
                                }
                            )
                        except Exception as e:
                            logger.error(f"Failed to send progress event: {e}")

                    # Add async handler wrapper
                    def on_progress(event):
                        """Sync wrapper for async send_progress."""
                        try:
                            # Schedule async task
                            asyncio.create_task(send_progress(event))
                        except Exception as e:
                            logger.error(f"Failed to schedule progress send: {e}")

                    callback.add_handler(on_progress)

                    # Execute query with streaming
                    logger.info(f"Processing query: {query}")

                    # Build process tree
                    tree = process_builder.build_process_tree(query)

                    # Execute with progress callback
                    result = process_executor.execute_process(tree, progress_callback=callback)

                    # Send final result
                    await websocket.send_json(
                        {
                            "event_type": "result",
                            "session_id": session_id,
                            "success": result["success"],
                            "data": result["data"],
                            "execution_time": result["execution_time"],
                            "steps_completed": result["steps_completed"],
                            "steps_failed": result["steps_failed"],
                        }
                    )

                    # Update session stats
                    active_sessions[session_id]["queries_processed"] += 1
                    logger.info(f"✅ Query processed: {query} ({result['execution_time']:.2f}s)")

                except Exception as e:
                    logger.error(f"Error processing query: {e}", exc_info=True)
                    await websocket.send_json(
                        {"event_type": "error", "session_id": session_id, "message": f"Processing error: {str(e)}"}
                    )
            else:
                # Services not available - send error
                await websocket.send_json(
                    {"event_type": "error", "session_id": session_id, "message": "NLP services not available"}
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        if session_id in active_sessions:
            del active_sessions[session_id]

    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}", exc_info=True)
        if session_id in active_sessions:
            del active_sessions[session_id]
        try:
            await websocket.close()
        except:
            pass


@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Test page with WebSocket client."""
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>VERITAS NLP Streaming Test</title>
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    margin-bottom: 20px;
                }
                input, button {
                    padding: 12px;
                    margin: 10px 0;
                    font-size: 16px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }
                input {
                    width: calc(100% - 24px);
                }
                button {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    cursor: pointer;
                    width: 100%;
                }
                button:hover {
                    background-color: #2980b9;
                }
                button:disabled {
                    background-color: #95a5a6;
                    cursor: not-allowed;
                }
                #log {
                    border: 1px solid #ddd;
                    padding: 15px;
                    height: 400px;
                    overflow-y: auto;
                    background-color: #f9f9f9;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    margin-top: 20px;
                    border-radius: 5px;
                }
                .log-entry {
                    margin: 5px 0;
                    padding: 5px;
                    border-left: 3px solid #3498db;
                    background-color: white;
                }
                .log-entry.error {
                    border-left-color: #e74c3c;
                    background-color: #ffe6e6;
                }
                .log-entry.success {
                    border-left-color: #27ae60;
                    background-color: #e6ffe6;
                }
                .status {
                    display: inline-block;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-size: 12px;
                    margin-right: 10px;
                }
                .status.connected {
                    background-color: #27ae60;
                    color: white;
                }
                .status.disconnected {
                    background-color: #e74c3c;
                    color: white;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 VERITAS NLP Streaming Test</h1>

                <div>
                    <span id="status" class="status disconnected">Disconnected</span>
                    <span id="progress"></span>
                </div>

                <input type="text" id="query" placeholder="Enter query (e.g., 'Bauantrag für Stuttgart')" />
                <button id="connect" onclick="connect()">Connect</button>
                <button id="send" onclick="sendQuery()" disabled>Send Query</button>
                <button onclick="clearLog()">Clear Log</button>

                <div id="log"></div>
            </div>

            <script>
                let ws = null;
                const sessionId = 'test_session_' + Date.now();

                function connect() {
                    const wsUrl = `ws://${window.location.host}/ws/process/${sessionId}`;
                    log(`Connecting to ${wsUrl}...`);

                    ws = new WebSocket(wsUrl);

                    ws.onopen = function() {
                        log('✅ WebSocket connected!', 'success');
                        document.getElementById('status').className = 'status connected';
                        document.getElementById('status').textContent = 'Connected';
                        document.getElementById('send').disabled = false;
                        document.getElementById('connect').disabled = true;
                    };

                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        handleMessage(data);
                    };

                    ws.onerror = function(error) {
                        log('❌ WebSocket error!', 'error');
                    };

                    ws.onclose = function() {
                        log('WebSocket closed');
                        document.getElementById('status').className = 'status disconnected';
                        document.getElementById('status').textContent = 'Disconnected';
                        document.getElementById('send').disabled = true;
                        document.getElementById('connect').disabled = false;
                    };
                }

                function sendQuery() {
                    const query = document.getElementById('query').value;
                    if (!query) {
                        alert('Please enter a query');
                        return;
                    }

                    log(`📤 Sending query: ${query}`);
                    ws.send(JSON.stringify({ query: query }));
                }

                function handleMessage(data) {
                    const eventType = data.event_type;

                    if (eventType === 'connected') {
                        log(`🔗 ${data.message}`, 'success');
                    }
                    else if (eventType === 'plan_started') {
                        const steps = data.data.total_steps;
                        log(`🚀 Plan started: ${steps} steps`);
                        updateProgress(0);
                    }
                    else if (eventType === 'step_started') {
                        const step = data.data.current_step;
                        const total = data.data.total_steps;
                        const name = data.data.step_name;
                        log(`▶️  Step ${step}/${total}: ${name}`);
                    }
                    else if (eventType === 'step_progress') {
                        const pct = data.data.percentage.toFixed(1);
                        const msg = data.data.message;
                        log(`   ⏳ ${pct}%: ${msg}`);
                        updateProgress(data.data.percentage);
                    }
                    else if (eventType === 'step_completed') {
                        const step = data.data.current_step;
                        const total = data.data.total_steps;
                        const name = data.data.step_name;
                        const time = data.data.execution_time.toFixed(3);
                        log(`✅ Step ${step}/${total}: ${name} (${time}s)`, 'success');
                    }
                    else if (eventType === 'step_failed') {
                        const error = data.data.error;
                        log(`❌ Step failed: ${error}`, 'error');
                    }
                    else if (eventType === 'plan_completed') {
                        const time = data.data.execution_time.toFixed(3);
                        log(`🎉 Plan completed in ${time}s`, 'success');
                        updateProgress(100);
                    }
                    else if (eventType === 'result') {
                        const success = data.success;
                        const time = data.execution_time.toFixed(3);
                        const completed = data.steps_completed;
                        const failed = data.steps_failed;
                        log(`📊 Result: ${completed} completed, ${failed} failed (${time}s)`,
                            success ? 'success' : 'error');
                    }
                    else if (eventType === 'error') {
                        log(`❌ Error: ${data.message}`, 'error');
                    }
                    else {
                        log(`Unknown event: ${eventType}`);
                    }
                }

                function updateProgress(percentage) {
                    document.getElementById('progress').textContent =
                        `Progress: ${percentage.toFixed(1)}%`;
                }

                function log(message, type = '') {
                    const logDiv = document.getElementById('log');
                    const entry = document.createElement('div');
                    entry.className = 'log-entry ' + type;
                    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
                    logDiv.appendChild(entry);
                    logDiv.scrollTop = logDiv.scrollHeight;
                }

                function clearLog() {
                    document.getElementById('log').innerHTML = '';
                }

                // Allow Enter key to send query
                document.getElementById('query').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter' && !document.getElementById('send').disabled) {
                        sendQuery();
                    }
                });
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# Run with: uvicorn backend.api.streaming_api:app --reload
if __name__ == "__main__":
    import uvicorn

    print("=" * 80)
    print("VERITAS NLP STREAMING API")
    print("=" * 80)
    print("\nStarting server...")
    print(f"   WebSocket endpoint: ws://localhost:8000/ws/process/{{session_id}}")
    print(f"   Test page: http://localhost:8000/test")
    print(f"   Health check: http://localhost:8000/health")
    print("\n" + "=" * 80)

    import os

    host = os.getenv("VERITAS_API_HOST", "127.0.0.1")
    port = int(os.getenv("VERITAS_API_PORT", "8000"))
    logger.info(f"Starting streaming API on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
