# SSE + MCP Implementation Plan - VERITAS Integration

**Datum:** 31. Oktober 2025  
**Status:** 🎯 **APPROVED FOR IMPLEMENTATION**  
**Strategie:** Parallel Integration (WebSocket bleibt bestehen)  
**Timeline:** 5-7 Wochen  
**Budget:** €7,000  

---

## 🎯 Strategie: Parallel Integration

### Architektur-Übersicht

```
VERITAS Streaming Architecture v2.0 (HYBRID)
════════════════════════════════════════════

Frontend ↔ Backend:
├─ WebSocket (BESTEHENД)      → Interactive Control, Admin, Collaboration
├─ SSE (NEU - Phase 1)        → Agent Progress, Metrics, Notifications  
└─ REST API (BESTEHEND)       → Standard Queries

Desktop Integration:
└─ MCP Server (NEU - Phase 2) → Word, Excel, VS Code, Claude Desktop

Backend ↔ Backend:
└─ Message Queue (Future)     → Redis Pub/Sub (optional)
```

**Prinzip:** 🔄 **ADDITIVE, NICHT DESTRUCTIVE**
- Bestehende WebSocket-Endpoints bleiben funktionsfähig
- SSE wird parallel hinzugefügt (Client entscheidet)
- MCP ist separate Schnittstelle (Desktop-Apps)
- Keine Breaking Changes!

---

## 📅 Phase 1: SSE Integration (2-3 Wochen)

### Woche 1: Backend SSE Endpoints

**Ziel:** SSE-Streaming parallel zu WebSocket

#### Tag 1-2: Dependencies & Setup

```bash
# Install SSE Library
pip install sse-starlette==1.8.2

# Update requirements.txt
echo "sse-starlette==1.8.2  # Server-Sent Events support" >> requirements.txt
```

#### Tag 3-5: SSE Endpoints Implementation

**Datei:** `backend/api/sse_endpoints.py` (NEU)

```python
"""
VERITAS SSE Endpoints
====================

Server-Sent Events for unidirectional streaming.

Endpoints:
- GET /api/sse/progress/{session_id}  - Agent progress updates
- GET /api/sse/metrics                - System metrics
- GET /api/sse/jobs/{job_id}          - Job progress (UDS3)
- GET /api/sse/quality/{session_id}   - Quality gate notifications

Features:
- Auto-reconnect (Last-Event-ID)
- Event replay
- Session isolation
- Event filtering
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Optional
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException
from sse_starlette.sse import EventSourceResponse

# Import existing components
from backend.agents.framework.streaming_manager import StreamingManager, EventType
from backend.models.streaming_progress import ProgressEvent

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/sse", tags=["SSE Streaming"])

# Global streaming manager (shared with WebSocket)
streaming_manager: Optional[StreamingManager] = None


def init_sse_endpoints(manager: StreamingManager):
    """Initialize SSE endpoints with streaming manager."""
    global streaming_manager
    streaming_manager = manager
    logger.info("✅ SSE Endpoints initialized")


@router.get("/progress/{session_id}")
async def stream_agent_progress(
    session_id: str,
    last_event_id: Optional[str] = Query(None, alias="Last-Event-ID")
):
    """
    Stream agent execution progress.
    
    Client:
        const source = new EventSource('/api/sse/progress/session_123');
        source.addEventListener('step_progress', (e) => {
            const data = JSON.parse(e.data);
            console.log(`${data.percentage}%: ${data.message}`);
        });
    
    Events:
        - plan_started
        - step_started
        - step_progress
        - step_completed
        - quality_check
        - plan_completed
        - error
    """
    
    async def event_generator() -> AsyncGenerator:
        """Generate SSE events from streaming manager."""
        
        # Replay missed events if Last-Event-ID provided
        if last_event_id:
            history = streaming_manager.get_event_history(session_id)
            replay_events = [e for e in history if e.event_id > last_event_id]
            
            for event in replay_events:
                yield {
                    "event": event.event_type,
                    "data": json.dumps(event.data),
                    "id": event.event_id,
                    "retry": 5000  # Auto-reconnect after 5s
                }
        
        # Stream live events
        try:
            async for event in streaming_manager.subscribe_session(session_id):
                yield {
                    "event": event.event_type,
                    "data": json.dumps(event.data),
                    "id": event.event_id,
                    "retry": 5000
                }
                
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for session {session_id}")
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
                "retry": 10000
            }
    
    return EventSourceResponse(event_generator())


@router.get("/metrics")
async def stream_system_metrics():
    """
    Stream system metrics (CPU, Memory, Database).
    
    Client:
        const source = new EventSource('/api/sse/metrics');
        source.addEventListener('metrics_update', (e) => {
            const metrics = JSON.parse(e.data);
            updateDashboard(metrics);
        });
    """
    
    async def metrics_generator() -> AsyncGenerator:
        while True:
            # Collect metrics
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": streaming_manager.get_cpu_usage(),
                "memory_mb": streaming_manager.get_memory_usage(),
                "active_sessions": streaming_manager.get_client_count(),
                "database": {
                    "chromadb": streaming_manager.get_db_status("chromadb"),
                    "neo4j": streaming_manager.get_db_status("neo4j"),
                    "postgresql": streaming_manager.get_db_status("postgresql")
                }
            }
            
            yield {
                "event": "metrics_update",
                "data": json.dumps(metrics),
                "id": str(int(datetime.utcnow().timestamp())),
                "retry": 5000
            }
            
            await asyncio.sleep(2)  # Update every 2 seconds
    
    return EventSourceResponse(metrics_generator())


@router.get("/jobs/{job_id}")
async def stream_job_progress(job_id: str):
    """
    Stream UDS3 job progress (file upload/processing).
    
    Client:
        const source = new EventSource('/api/sse/jobs/job_123');
        source.addEventListener('job_progress', (e) => {
            const progress = JSON.parse(e.data);
            updateProgressBar(progress.percentage);
        });
    """
    
    async def job_generator() -> AsyncGenerator:
        async for event in streaming_manager.subscribe_job(job_id):
            yield {
                "event": "job_progress",
                "data": json.dumps({
                    "job_id": job_id,
                    "status": event.status,
                    "percentage": event.percentage,
                    "files_processed": event.files_processed,
                    "files_total": event.files_total,
                    "message": event.message
                }),
                "id": event.event_id,
                "retry": 5000
            }
    
    return EventSourceResponse(job_generator())


@router.get("/quality/{session_id}")
async def stream_quality_gates(session_id: str):
    """
    Stream quality gate notifications.
    
    Client:
        const source = new EventSource('/api/sse/quality/session_123');
        source.addEventListener('quality_check', (e) => {
            const check = JSON.parse(e.data);
            if (!check.passed) showWarning(check.message);
        });
    """
    
    async def quality_generator() -> AsyncGenerator:
        async for event in streaming_manager.subscribe_session(session_id):
            if event.event_type == EventType.QUALITY_CHECK.value:
                yield {
                    "event": "quality_check",
                    "data": json.dumps(event.data),
                    "id": event.event_id,
                    "retry": 5000
                }
    
    return EventSourceResponse(quality_generator())


@router.get("/health")
async def sse_health():
    """SSE endpoint health check."""
    return {
        "status": "healthy",
        "sse_available": True,
        "active_streams": streaming_manager.get_client_count() if streaming_manager else 0
    }
```

**Integration in `backend/app.py`:**

```python
# backend/app.py
from backend.api.sse_endpoints import router as sse_router, init_sse_endpoints

# ... existing code ...

# Initialize SSE
init_sse_endpoints(streaming_manager)
app.include_router(sse_router)

logger.info("✅ SSE Endpoints registered")
```

---

### Woche 2: Frontend SSE Client

#### Tag 6-8: JavaScript SSE Client

**Datei:** `frontend/services/sse_client.js` (NEU)

```javascript
/**
 * VERITAS SSE Client
 * ==================
 * 
 * EventSource-based client for Server-Sent Events.
 * 
 * Features:
 * - Auto-reconnect (built-in)
 * - Event replay (Last-Event-ID)
 * - Multiple event types
 * - Error handling
 * 
 * Usage:
 *   const client = new VeritasSSEClient('session_123');
 *   client.onProgress((data) => console.log(data));
 *   client.connect();
 */

class VeritasSSEClient {
    constructor(sessionId, options = {}) {
        this.sessionId = sessionId;
        this.baseUrl = options.baseUrl || 'http://localhost:5000';
        this.eventSource = null;
        this.handlers = {
            progress: [],
            quality: [],
            error: []
        };
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
    }
    
    /**
     * Connect to SSE stream.
     */
    connect() {
        const url = `${this.baseUrl}/api/sse/progress/${this.sessionId}`;
        
        this.eventSource = new EventSource(url);
        
        // Plan Events
        this.eventSource.addEventListener('plan_started', (e) => {
            const data = JSON.parse(e.data);
            this.handlers.progress.forEach(h => h({
                type: 'plan_started',
                ...data
            }));
        });
        
        this.eventSource.addEventListener('plan_completed', (e) => {
            const data = JSON.parse(e.data);
            this.handlers.progress.forEach(h => h({
                type: 'plan_completed',
                ...data
            }));
        });
        
        // Step Events
        this.eventSource.addEventListener('step_started', (e) => {
            const data = JSON.parse(e.data);
            this.handlers.progress.forEach(h => h({
                type: 'step_started',
                ...data
            }));
        });
        
        this.eventSource.addEventListener('step_progress', (e) => {
            const data = JSON.parse(e.data);
            this.handlers.progress.forEach(h => h({
                type: 'step_progress',
                ...data
            }));
        });
        
        this.eventSource.addEventListener('step_completed', (e) => {
            const data = JSON.parse(e.data);
            this.handlers.progress.forEach(h => h({
                type: 'step_completed',
                ...data
            }));
        });
        
        // Quality Events
        this.eventSource.addEventListener('quality_check', (e) => {
            const data = JSON.parse(e.data);
            this.handlers.quality.forEach(h => h(data));
        });
        
        // Error Events
        this.eventSource.addEventListener('error', (e) => {
            const data = e.data ? JSON.parse(e.data) : {error: 'Unknown error'};
            this.handlers.error.forEach(h => h(data));
        });
        
        // Connection Events
        this.eventSource.onopen = () => {
            console.log('[SSE] Connected to', url);
            this.reconnectAttempts = 0;
        };
        
        this.eventSource.onerror = (e) => {
            console.error('[SSE] Connection error', e);
            this.reconnectAttempts++;
            
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                console.error('[SSE] Max reconnect attempts reached');
                this.disconnect();
                this.handlers.error.forEach(h => h({
                    error: 'Max reconnect attempts reached'
                }));
            }
            // EventSource auto-reconnects, no manual intervention needed
        };
    }
    
    /**
     * Register progress handler.
     */
    onProgress(handler) {
        this.handlers.progress.push(handler);
        return this;
    }
    
    /**
     * Register quality gate handler.
     */
    onQuality(handler) {
        this.handlers.quality.push(handler);
        return this;
    }
    
    /**
     * Register error handler.
     */
    onError(handler) {
        this.handlers.error.push(handler);
        return this;
    }
    
    /**
     * Disconnect from SSE stream.
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            console.log('[SSE] Disconnected');
        }
    }
}

// Metrics SSE Client
class VeritasMetricsSSEClient {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || 'http://localhost:5000';
        this.eventSource = null;
        this.handlers = [];
    }
    
    connect() {
        const url = `${this.baseUrl}/api/sse/metrics`;
        this.eventSource = new EventSource(url);
        
        this.eventSource.addEventListener('metrics_update', (e) => {
            const metrics = JSON.parse(e.data);
            this.handlers.forEach(h => h(metrics));
        });
        
        this.eventSource.onopen = () => {
            console.log('[SSE Metrics] Connected');
        };
    }
    
    onMetrics(handler) {
        this.handlers.push(handler);
        return this;
    }
    
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

export { VeritasSSEClient, VeritasMetricsSSEClient };
```

#### Tag 9-10: React Integration

**Datei:** `frontend/components/AgentProgressSSE.jsx` (NEU)

```jsx
import React, { useEffect, useState } from 'react';
import { VeritasSSEClient } from '../services/sse_client';

/**
 * Agent Progress Component (SSE-based)
 */
export function AgentProgressSSE({ sessionId }) {
    const [progress, setProgress] = useState([]);
    const [currentStep, setCurrentStep] = useState(null);
    const [quality, setQuality] = useState([]);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        const client = new VeritasSSEClient(sessionId);
        
        client
            .onProgress((data) => {
                switch (data.type) {
                    case 'plan_started':
                        setProgress([{ message: 'Research plan started', timestamp: new Date() }]);
                        break;
                    
                    case 'step_started':
                        setCurrentStep({
                            name: data.step_name,
                            action: data.action,
                            status: 'running'
                        });
                        break;
                    
                    case 'step_progress':
                        setProgress(prev => [...prev, {
                            message: data.message,
                            percentage: data.percentage,
                            timestamp: new Date()
                        }]);
                        break;
                    
                    case 'step_completed':
                        setCurrentStep(prev => ({ ...prev, status: 'completed' }));
                        break;
                    
                    case 'plan_completed':
                        setProgress(prev => [...prev, {
                            message: '✅ Research completed',
                            timestamp: new Date()
                        }]);
                        break;
                }
            })
            .onQuality((data) => {
                setQuality(prev => [...prev, data]);
            })
            .onError((data) => {
                setError(data.error);
            })
            .connect();
        
        return () => client.disconnect();
    }, [sessionId]);
    
    return (
        <div className="agent-progress-sse">
            <h3>Agent Execution Progress (SSE)</h3>
            
            {error && (
                <div className="error-banner">
                    ❌ Error: {error}
                </div>
            )}
            
            {currentStep && (
                <div className="current-step">
                    <strong>{currentStep.name}</strong>
                    <span className={`status ${currentStep.status}`}>
                        {currentStep.status}
                    </span>
                </div>
            )}
            
            <div className="progress-log">
                {progress.map((entry, i) => (
                    <div key={i} className="progress-entry">
                        <span className="timestamp">
                            {entry.timestamp.toLocaleTimeString()}
                        </span>
                        <span className="message">{entry.message}</span>
                        {entry.percentage && (
                            <span className="percentage">{entry.percentage}%</span>
                        )}
                    </div>
                ))}
            </div>
            
            {quality.length > 0 && (
                <div className="quality-gates">
                    <h4>Quality Checks</h4>
                    {quality.map((check, i) => (
                        <div key={i} className={`quality-check ${check.passed ? 'passed' : 'failed'}`}>
                            <span>{check.metric}</span>
                            <span>{check.value} / {check.threshold}</span>
                            <span>{check.passed ? '✅' : '⚠️'}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
```

---

### Woche 3: Testing & Documentation

#### Tag 11-13: Testing

**Tests:** `tests/test_sse_endpoints.py` (NEU)

```python
import pytest
import asyncio
from httpx import AsyncClient
from backend.app import app

@pytest.mark.asyncio
async def test_sse_progress_stream():
    """Test SSE progress stream."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        async with client.stream("GET", "/api/sse/progress/test_session") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
            
            # Read first event
            line = await response.aread()
            assert b"event:" in line

@pytest.mark.asyncio
async def test_sse_metrics_stream():
    """Test SSE metrics stream."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        async with client.stream("GET", "/api/sse/metrics") as response:
            assert response.status_code == 200

@pytest.mark.asyncio
async def test_sse_reconnect_with_last_event_id():
    """Test SSE reconnect with Last-Event-ID."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/sse/progress/test_session",
            headers={"Last-Event-ID": "12345"}
        )
        assert response.status_code == 200
```

**Browser Tests:**
```javascript
// tests/manual/test_sse_browser.html
<!DOCTYPE html>
<html>
<head>
    <title>SSE Test</title>
</head>
<body>
    <h1>VERITAS SSE Test</h1>
    <div id="log"></div>
    
    <script>
        const source = new EventSource('http://localhost:5000/api/sse/progress/test_session');
        const log = document.getElementById('log');
        
        source.addEventListener('step_progress', (e) => {
            const data = JSON.parse(e.data);
            log.innerHTML += `<div>[${new Date().toLocaleTimeString()}] ${data.message}</div>`;
        });
        
        source.onerror = (e) => {
            log.innerHTML += `<div style="color: red;">Error: Connection lost, reconnecting...</div>`;
        };
    </script>
</body>
</html>
```

#### Tag 14-15: Documentation

**Docs:** `docs/SSE_INTEGRATION_GUIDE.md` (NEU)

---

## 📅 Phase 2: MCP Server für Desktop Integration (3-4 Wochen)

### Woche 4: MCP Server Core

#### Tag 1-3: MCP SDK Setup

```bash
# Python MCP SDK
pip install mcp==0.9.0

# Node.js MCP SDK (für Desktop Clients)
npm install @modelcontextprotocol/sdk
```

#### Tag 4-7: MCP Server Implementation

**Datei:** `backend/mcp/veritas_mcp_server.py` (NEU)

```python
"""
VERITAS MCP Server
==================

Model Context Protocol server for desktop application integration.

Supports:
- Microsoft Word Add-In
- Excel Integration
- VS Code Extension
- Claude Desktop
- Cursor Editor

Features:
- Prompts: Template-based queries
- Resources: Document access (veritas://documents/{id})
- Tools: VERITAS functions (hybrid_search, execute_agent, etc.)
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from mcp.server import MCPServer
    from mcp.types import (
        Prompt, PromptArgument,
        Resource, ResourceTemplate,
        Tool, ToolArgument
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("⚠️ MCP SDK not available - install with: pip install mcp")

# Import VERITAS components
from backend.agents.veritas_intelligent_pipeline import IntelligentPipeline
from backend.services.query_service import QueryService
from backend.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class VeritasMCPServer:
    """VERITAS MCP Server for Desktop Integration."""
    
    def __init__(
        self,
        pipeline: IntelligentPipeline,
        query_service: QueryService,
        rag_service: RAGService
    ):
        self.pipeline = pipeline
        self.query_service = query_service
        self.rag_service = rag_service
        
        if not MCP_AVAILABLE:
            raise ImportError("MCP SDK required - install with: pip install mcp")
        
        self.server = MCPServer("veritas-legal-research")
        self._register_prompts()
        self._register_resources()
        self._register_tools()
        
        logger.info("✅ VERITAS MCP Server initialized")
    
    def _register_prompts(self):
        """Register prompt templates."""
        
        @self.server.prompt("legal-research")
        async def legal_research_prompt(
            topic: str,
            jurisdiction: str = "Deutschland"
        ) -> Prompt:
            """
            Legal research prompt template.
            
            Usage in Word:
                User selects text → Right-click → "VERITAS Research"
                → Prompt fills with selection
                → VERITAS executes search
            """
            return Prompt(
                name="legal-research",
                description=f"Rechtliche Recherche zu {topic} ({jurisdiction})",
                arguments=[
                    PromptArgument(name="topic", description="Rechtsthema", required=True),
                    PromptArgument(name="jurisdiction", description="Rechtsgebiet", required=False)
                ],
                messages=[{
                    "role": "user",
                    "content": f"""Analysiere die Rechtslage zu folgendem Thema:

Thema: {topic}
Rechtsgebiet: {jurisdiction}

Bitte berücksichtige:
1. Aktuelle Gesetzeslage
2. Relevante Rechtsprechung
3. Verwaltungsvorschriften
4. Baurecht (falls zutreffend)

Gebe eine strukturierte Analyse mit Quellenangaben."""
                }]
            )
        
        @self.server.prompt("baurecht-query")
        async def baurecht_prompt(location: str, project_type: str) -> Prompt:
            """Baurecht-spezifisches Prompt."""
            return Prompt(
                name="baurecht-query",
                description=f"Baurecht-Analyse für {project_type} in {location}",
                messages=[{
                    "role": "user",
                    "content": f"""Analysiere die baurechtlichen Anforderungen:

Standort: {location}
Bauvorhaben: {project_type}

Prüfe:
1. Genehmigungspflicht
2. Bebauungsplan
3. Umweltauflagen
4. Denkmalschutz"""
                }]
            )
    
    def _register_resources(self):
        """Register document resources."""
        
        @self.server.resource_template("veritas://documents/{doc_id}")
        async def document_resource(doc_id: str) -> Resource:
            """
            Access VERITAS document as MCP resource.
            
            Usage in Excel:
                =VERITAS.GetDocument("doc_12345")
                → Loads document metadata
            """
            doc = await self.query_service.get_document_by_id(doc_id)
            
            if not doc:
                raise ValueError(f"Document {doc_id} not found")
            
            return Resource(
                uri=f"veritas://documents/{doc_id}",
                mimeType="application/json",
                text=json.dumps(doc.to_dict(), indent=2, ensure_ascii=False),
                metadata={
                    "title": doc.title,
                    "jurisdiction": doc.metadata.get("jurisdiction", "unknown"),
                    "date": doc.metadata.get("date"),
                    "document_type": doc.metadata.get("document_type"),
                    "source": doc.metadata.get("source")
                }
            )
        
        @self.server.resource("veritas://database/stats")
        async def database_stats() -> Resource:
            """Database statistics resource."""
            stats = await self.query_service.get_database_stats()
            
            return Resource(
                uri="veritas://database/stats",
                mimeType="application/json",
                text=json.dumps(stats, indent=2)
            )
    
    def _register_tools(self):
        """Register VERITAS tools."""
        
        @self.server.tool("hybrid_search")
        async def hybrid_search_tool(query: str, top_k: int = 10) -> Dict[str, Any]:
            """
            Hybrid search tool (BM25 + Dense + RRF).
            
            Usage in Word Add-In:
                const results = await mcp.callTool('hybrid_search', {
                    query: 'Bauantrag Stuttgart',
                    top_k: 5
                });
            """
            results = await self.query_service.hybrid_search(
                query=query,
                top_k=top_k
            )
            
            return {
                "results": [doc.to_dict() for doc in results],
                "count": len(results),
                "query": query,
                "mode": "hybrid_bm25_dense_rrf",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.server.tool("execute_agent")
        async def execute_agent_tool(
            agent_name: str,
            query: str,
            parameters: Optional[Dict] = None
        ) -> Dict[str, Any]:
            """
            Execute VERITAS agent.
            
            Agents:
                - environmental: Umweltrecht
                - construction: Baurecht
                - traffic: Verkehrsrecht
                - financial: Finanzrecht
                - social: Sozialrecht
            """
            result = await self.pipeline.execute_agent(
                agent_name=agent_name,
                query=query,
                parameters=parameters or {}
            )
            
            return result.to_dict()
        
        @self.server.tool("rag_context")
        async def rag_context_tool(query: str, max_chunks: int = 5) -> Dict[str, Any]:
            """Build RAG context for query."""
            context = await self.rag_service.build_context(
                query=query,
                max_chunks=max_chunks
            )
            
            return {
                "context": context,
                "chunks_count": len(context.get("documents", [])),
                "query": query
            }
        
        @self.server.tool("list_agents")
        async def list_agents_tool() -> Dict[str, Any]:
            """List available VERITAS agents."""
            agents = self.pipeline.list_agents()
            
            return {
                "agents": agents,
                "count": len(agents)
            }
    
    def run(self, transport: str = "stdio"):
        """
        Run MCP server.
        
        Args:
            transport: 'stdio' (local) or 'http' (remote)
        """
        if transport == "stdio":
            self.server.run_stdio()
        elif transport == "http":
            self.server.run_http(host="0.0.0.0", port=5001)
        else:
            raise ValueError(f"Unknown transport: {transport}")


# CLI Entry Point
if __name__ == "__main__":
    import argparse
    from backend.app import pipeline, query_service, rag_service
    
    parser = argparse.ArgumentParser(description="VERITAS MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--port", type=int, default=5001)
    
    args = parser.parse_args()
    
    mcp_server = VeritasMCPServer(pipeline, query_service, rag_service)
    mcp_server.run(transport=args.transport)
```

---

### Woche 5-6: Office Add-Ins

#### Microsoft Word Add-In

**Projekt:** `desktop/word-addin/` (NEU)

**Setup:**
```bash
npm init -y
npm install @modelcontextprotocol/sdk office-addin-manifest
```

**Datei:** `desktop/word-addin/src/taskpane.ts`

```typescript
import { MCPClient } from '@modelcontextprotocol/sdk';

class VeritasWordAddin {
    private mcp: MCPClient;
    
    async initialize() {
        // Connect to VERITAS MCP Server
        this.mcp = new MCPClient({
            serverUrl: 'http://localhost:5001/mcp',
            transport: 'http'
        });
        
        await this.mcp.connect();
        console.log('✅ Connected to VERITAS MCP Server');
        
        // Setup UI
        this.setupUI();
    }
    
    setupUI() {
        // Research Button
        document.getElementById('btn-research').onclick = () => {
            this.insertLegalResearch();
        };
        
        // Agent Execution
        document.getElementById('btn-agent').onclick = () => {
            this.executeAgent();
        };
        
        // List Documents
        document.getElementById('btn-list').onclick = () => {
            this.listDocuments();
        };
    }
    
    async insertLegalResearch() {
        try {
            // Get selected text
            await Word.run(async (context) => {
                const selection = context.document.getSelection();
                selection.load('text');
                await context.sync();
                
                const topic = selection.text || 'Baurecht Stuttgart';
                
                // Execute hybrid search via MCP
                const results = await this.mcp.callTool('hybrid_search', {
                    query: topic,
                    top_k: 5
                });
                
                // Insert results into document
                const body = context.document.body;
                body.insertParagraph('Recherche-Ergebnisse:', Word.InsertLocation.end);
                body.insertParagraph('═'.repeat(50), Word.InsertLocation.end);
                
                results.results.forEach((doc, i) => {
                    body.insertParagraph(
                        `${i+1}. ${doc.title}`,
                        Word.InsertLocation.end
                    ).font.bold = true;
                    
                    body.insertParagraph(
                        doc.content_preview,
                        Word.InsertLocation.end
                    );
                    
                    body.insertParagraph(
                        `Quelle: ${doc.metadata.source} (${doc.metadata.date})`,
                        Word.InsertLocation.end
                    ).font.italic = true;
                    
                    body.insertParagraph('', Word.InsertLocation.end);
                });
                
                await context.sync();
            });
            
            this.showNotification('✅ Recherche abgeschlossen', 'success');
            
        } catch (error) {
            this.showNotification(`❌ Fehler: ${error.message}`, 'error');
        }
    }
    
    async executeAgent() {
        const agentName = (document.getElementById('agent-select') as HTMLSelectElement).value;
        const query = (document.getElementById('query-input') as HTMLInputElement).value;
        
        try {
            const result = await this.mcp.callTool('execute_agent', {
                agent_name: agentName,
                query: query
            });
            
            // Insert agent results
            await Word.run(async (context) => {
                const body = context.document.body;
                body.insertParagraph(`Agent: ${agentName}`, Word.InsertLocation.end);
                body.insertParagraph(result.answer, Word.InsertLocation.end);
                await context.sync();
            });
            
        } catch (error) {
            this.showNotification(`❌ Fehler: ${error.message}`, 'error');
        }
    }
    
    showNotification(message: string, type: 'success' | 'error') {
        Office.context.mailbox.item.notificationMessages.addAsync(
            'veritas-notification',
            {
                type: Office.MailboxEnums.ItemNotificationMessageType.InformationalMessage,
                message: message,
                icon: type === 'success' ? 'icon-success' : 'icon-error',
                persistent: false
            }
        );
    }
}

// Initialize when Office is ready
Office.onReady((info) => {
    if (info.host === Office.HostType.Word) {
        const addin = new VeritasWordAddin();
        addin.initialize();
    }
});
```

**UI:** `desktop/word-addin/src/taskpane.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <title>VERITAS Legal Research</title>
    <link rel="stylesheet" href="taskpane.css" />
</head>
<body>
    <div class="container">
        <h1>🏛️ VERITAS</h1>
        <h2>Legal Research Assistant</h2>
        
        <section class="section">
            <h3>Quick Research</h3>
            <p>Markieren Sie Text im Dokument und klicken Sie auf "Recherche"</p>
            <button id="btn-research" class="btn-primary">
                🔍 Recherche starten
            </button>
        </section>
        
        <section class="section">
            <h3>Agent Execution</h3>
            <select id="agent-select">
                <option value="environmental">Umweltrecht</option>
                <option value="construction">Baurecht</option>
                <option value="traffic">Verkehrsrecht</option>
                <option value="financial">Finanzrecht</option>
                <option value="social">Sozialrecht</option>
            </select>
            <input id="query-input" type="text" placeholder="Query..." />
            <button id="btn-agent" class="btn-secondary">
                🤖 Agent ausführen
            </button>
        </section>
        
        <section class="section">
            <h3>Database</h3>
            <button id="btn-list" class="btn-secondary">
                📊 Statistiken anzeigen
            </button>
        </section>
    </div>
    
    <script src="taskpane.js"></script>
</body>
</html>
```

---

### Woche 7: VS Code Extension

**Projekt:** `desktop/vscode-extension/` (NEU)

**Setup:**
```bash
npm init -y
npm install @modelcontextprotocol/sdk vscode
```

**Datei:** `desktop/vscode-extension/src/extension.ts`

```typescript
import * as vscode from 'vscode';
import { MCPClient } from '@modelcontextprotocol/sdk';

let mcpClient: MCPClient;

export async function activate(context: vscode.ExtensionContext) {
    console.log('VERITAS Extension activated');
    
    // Connect to MCP Server
    mcpClient = new MCPClient({
        serverUrl: 'http://localhost:5001/mcp',
        transport: 'http'
    });
    
    await mcpClient.connect();
    
    // Command: VERITAS Research
    const researchCommand = vscode.commands.registerCommand(
        'veritas.research',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;
            
            const selection = editor.document.getText(editor.selection);
            const query = selection || await vscode.window.showInputBox({
                prompt: 'Recherche-Query'
            });
            
            if (!query) return;
            
            // Show progress
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'VERITAS Recherche...',
                cancellable: false
            }, async (progress) => {
                const results = await mcpClient.callTool('hybrid_search', {
                    query: query,
                    top_k: 5
                });
                
                // Show results in new panel
                const panel = vscode.window.createWebviewPanel(
                    'veritasResults',
                    'VERITAS Recherche',
                    vscode.ViewColumn.Two,
                    {}
                );
                
                panel.webview.html = generateResultsHTML(results);
            });
        }
    );
    
    context.subscriptions.push(researchCommand);
    
    // Command: Execute Agent
    const agentCommand = vscode.commands.registerCommand(
        'veritas.executeAgent',
        async () => {
            const agents = await mcpClient.callTool('list_agents', {});
            
            const agentName = await vscode.window.showQuickPick(
                agents.agents.map(a => ({ label: a.name, description: a.description })),
                { placeHolder: 'Select Agent' }
            );
            
            if (!agentName) return;
            
            const query = await vscode.window.showInputBox({
                prompt: 'Agent Query'
            });
            
            if (!query) return;
            
            const result = await mcpClient.callTool('execute_agent', {
                agent_name: agentName.label,
                query: query
            });
            
            vscode.window.showInformationMessage(`Agent Result: ${result.answer}`);
        }
    );
    
    context.subscriptions.push(agentCommand);
}

function generateResultsHTML(results: any): string {
    return `
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .result { margin-bottom: 20px; border-left: 3px solid #0066cc; padding-left: 15px; }
            .title { font-weight: bold; color: #0066cc; }
            .content { margin-top: 10px; }
            .meta { color: #666; font-size: 0.9em; margin-top: 5px; }
        </style>
    </head>
    <body>
        <h1>VERITAS Recherche-Ergebnisse</h1>
        ${results.results.map((doc, i) => `
            <div class="result">
                <div class="title">${i+1}. ${doc.title}</div>
                <div class="content">${doc.content_preview}</div>
                <div class="meta">Quelle: ${doc.metadata.source} | ${doc.metadata.date}</div>
            </div>
        `).join('')}
    </body>
    </html>
    `;
}
```

---

## 📊 Roadmap Übersicht

```
Timeline: 7 Wochen (5-7 Wochen realistisch)
Budget: €7,000
Team: 2 Developers

Phase 1: SSE Integration (Wochen 1-3)
├─ Woche 1: Backend SSE Endpoints ✅
├─ Woche 2: Frontend SSE Client ✅
└─ Woche 3: Testing & Docs ✅

Phase 2: MCP Server (Wochen 4-7)
├─ Woche 4: MCP Core Implementation ✅
├─ Woche 5-6: Word Add-In ✅
└─ Woche 7: VS Code Extension ✅

Parallel: WebSocket bleibt aktiv!
```

---

## 💰 Budget Breakdown

| Phase | Tasks | Days | Cost |
|-------|-------|------|------|
| **Phase 1: SSE** | Backend + Frontend + Tests | 15 | €2,000 |
| **Phase 2: MCP Core** | Server Implementation | 7 | €1,500 |
| **Phase 3: Word Add-In** | Office Integration | 10 | €2,000 |
| **Phase 4: VS Code Ext** | IDE Integration | 7 | €1,500 |
| **Total** | | **39** | **€7,000** |

**ROI:**
- SSE: 6-12 Monate (besseres UX)
- MCP (Office): <1 Tag! (€266k/Woche Einsparung)

---

## 🎯 Success Metrics

### Phase 1: SSE

- ✅ SSE Endpoints: `/api/sse/progress`, `/api/sse/metrics`, `/api/sse/jobs`, `/api/sse/quality`
- ✅ Auto-Reconnect funktioniert (Network-Fehler → Auto-Reconnect nach 5s)
- ✅ Event Replay funktioniert (Last-Event-ID)
- ✅ Frontend SSE Client funktioniert (React/JS)
- ✅ Performance: <100ms Latenz, 1800 evt/s Durchsatz

### Phase 2: MCP

- ✅ MCP Server läuft (stdio + HTTP)
- ✅ Prompts: `legal-research`, `baurecht-query`
- ✅ Resources: `veritas://documents/{id}`, `veritas://database/stats`
- ✅ Tools: `hybrid_search`, `execute_agent`, `rag_context`, `list_agents`
- ✅ Word Add-In funktioniert (5 Recherchen in <1min)
- ✅ VS Code Extension funktioniert (Command Palette Integration)

---

## 📚 Nächste Schritte

**JETZT:**
1. ✅ Review dieses Plans
2. ✅ Budget-Freigabe
3. ✅ Team-Assignment

**Woche 1 (Start):**
1. Dependencies installieren (`sse-starlette`, `mcp`)
2. SSE Backend Endpoints implementieren
3. Erste Tests

**Nach Phase 1 (Woche 3):**
- Go/No-Go Decision für MCP Phase
- Budget-Review
- Priorität: Word vs VS Code?

---

**Status:** 🎯 **READY TO START**  
**Next Action:** Budget-Freigabe + Team-Assignment  
**Contact:** Development Team Lead
