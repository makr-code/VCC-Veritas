# VERITAS WebSocket Protocol

**Version:** 1.0.0  
**Last Updated:** 2025-10-08  
**WebSocket Endpoint:** `wss://api.veritas.example.com/api/v1/streaming/ws/{client_id}`

---

## Table of Contents

1. [Overview](#overview)
2. [Connection](#connection)
3. [Message Format](#message-format)
4. [Event Types](#event-types)
5. [Client Examples](#client-examples)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

---

## Overview

The VERITAS WebSocket API provides real-time streaming for agent execution progress, quality gate checks, and metrics updates.

**Use Cases:**
- Real-time agent execution progress
- Live quality gate evaluation
- Streaming metrics and logs
- Interactive dashboards
- Progressive UI updates

**Protocol:** WebSocket (RFC 6455)  
**Format:** JSON  
**Encoding:** UTF-8  
**Max Message Size:** 1MB  

---

## Connection

### Connection URL

```
wss://api.veritas.example.com/api/v1/streaming/ws/{client_id}?plan_id={plan_id}
```

**Parameters:**
- `client_id` (path, required): Unique client identifier (UUID recommended)
- `plan_id` (query, required): Execution plan ID to stream

**Example:**
```
wss://api.veritas.example.com/api/v1/streaming/ws/client_abc123?plan_id=plan_001
```

### Authentication

WebSocket connections support query parameter authentication:

```
wss://api.veritas.example.com/api/v1/streaming/ws/client_abc123?plan_id=plan_001&token=YOUR_JWT_TOKEN
```

Alternatively, send token in the first message:

```json
{
  "type": "auth",
  "token": "YOUR_JWT_TOKEN"
}
```

### Connection Lifecycle

```
1. Client initiates WebSocket connection
2. Server validates client_id and plan_id
3. Server sends connection confirmation
4. Server streams events as they occur
5. Client receives real-time updates
6. Connection closes when plan completes or client disconnects
```

### Connection Confirmation

Upon successful connection:

```json
{
  "type": "connection",
  "status": "connected",
  "client_id": "client_abc123",
  "plan_id": "plan_001",
  "timestamp": "2025-10-08T14:30:00Z"
}
```

---

## Message Format

All messages are JSON objects with the following structure:

```json
{
  "event_type": "EVENT_TYPE",
  "plan_id": "plan_001",
  "step_id": "step_financial",
  "agent_id": "fin_001",
  "timestamp": "2025-10-08T14:30:05.123Z",
  "data": {
    "key": "value"
  },
  "message": "Human-readable message"
}
```

**Fields:**
- `event_type` (string, required): Event type identifier
- `plan_id` (string, required): Execution plan ID
- `step_id` (string, optional): Step ID (if event is step-specific)
- `agent_id` (string, optional): Agent ID (if event is agent-specific)
- `timestamp` (string, required): ISO 8601 timestamp with milliseconds
- `data` (object, optional): Event-specific data
- `message` (string, optional): Human-readable description

---

## Event Types

### Plan Events

#### PLAN_STARTED

Execution plan started.

```json
{
  "event_type": "PLAN_STARTED",
  "plan_id": "plan_001",
  "timestamp": "2025-10-08T14:30:00.000Z",
  "data": {
    "agents": ["financial", "environmental", "social"],
    "total_steps": 12,
    "estimated_duration": 15.0
  },
  "message": "Execution plan started"
}
```

#### PLAN_COMPLETED

Execution plan completed successfully.

```json
{
  "event_type": "PLAN_COMPLETED",
  "plan_id": "plan_001",
  "timestamp": "2025-10-08T14:30:12.456Z",
  "data": {
    "status": "completed",
    "quality_score": 0.86,
    "execution_time": 12.456,
    "steps_completed": 12,
    "steps_failed": 0
  },
  "message": "Execution completed successfully"
}
```

#### PLAN_FAILED

Execution plan failed.

```json
{
  "event_type": "PLAN_FAILED",
  "plan_id": "plan_001",
  "timestamp": "2025-10-08T14:30:08.123Z",
  "data": {
    "error": {
      "code": "AGENT_EXECUTION_FAILED",
      "message": "Financial agent execution failed",
      "details": "Connection timeout to external service"
    },
    "failed_step": "step_financial"
  },
  "message": "Execution failed"
}
```

---

### Step Events

#### STEP_STARTED

Step execution started.

```json
{
  "event_type": "STEP_STARTED",
  "plan_id": "plan_001",
  "step_id": "step_financial",
  "agent_id": "fin_001",
  "timestamp": "2025-10-08T14:30:02.000Z",
  "data": {
    "agent_type": "financial",
    "step_name": "Financial Analysis",
    "dependencies": []
  },
  "message": "Financial analysis started"
}
```

#### STEP_COMPLETED

Step execution completed.

```json
{
  "event_type": "STEP_COMPLETED",
  "plan_id": "plan_001",
  "step_id": "step_financial",
  "agent_id": "fin_001",
  "timestamp": "2025-10-08T14:30:07.234Z",
  "data": {
    "result": {
      "roi": 0.15,
      "risk_level": "moderate",
      "confidence": 0.89
    },
    "quality_score": 0.89,
    "duration": 5.234,
    "tokens_used": 1543
  },
  "message": "Financial analysis completed"
}
```

#### STEP_FAILED

Step execution failed.

```json
{
  "event_type": "STEP_FAILED",
  "plan_id": "plan_001",
  "step_id": "step_financial",
  "agent_id": "fin_001",
  "timestamp": "2025-10-08T14:30:05.123Z",
  "data": {
    "error": {
      "code": "TIMEOUT",
      "message": "Step execution timeout",
      "duration": 300.0
    },
    "retry_count": 2,
    "will_retry": false
  },
  "message": "Step failed after 2 retries"
}
```

---

### Quality Events

#### QUALITY_CHECK

Quality gate evaluation.

```json
{
  "event_type": "QUALITY_CHECK",
  "plan_id": "plan_001",
  "step_id": "step_financial",
  "agent_id": "fin_001",
  "timestamp": "2025-10-08T14:30:07.500Z",
  "data": {
    "score": 0.89,
    "threshold": 0.7,
    "passed": true,
    "metrics": {
      "relevance": 0.92,
      "coherence": 0.88,
      "completeness": 0.86,
      "accuracy": 0.90
    }
  },
  "message": "Quality check passed (0.89 > 0.70)"
}
```

#### REVIEW_REQUIRED

Manual review requested.

```json
{
  "event_type": "REVIEW_REQUIRED",
  "plan_id": "plan_001",
  "step_id": "step_financial",
  "agent_id": "fin_001",
  "timestamp": "2025-10-08T14:30:07.600Z",
  "data": {
    "score": 0.65,
    "threshold": 0.7,
    "reason": "Quality score below threshold",
    "review_id": "review_001",
    "reviewers": ["user_123"],
    "deadline": "2025-10-08T16:30:00Z"
  },
  "message": "Manual review required: quality score 0.65 < 0.70"
}
```

---

### Metrics Events

#### METRICS_UPDATE

Live metrics update.

```json
{
  "event_type": "METRICS_UPDATE",
  "plan_id": "plan_001",
  "timestamp": "2025-10-08T14:30:05.000Z",
  "data": {
    "progress": 0.45,
    "steps_completed": 5,
    "steps_total": 12,
    "elapsed_time": 5.0,
    "estimated_remaining": 8.3,
    "agents": {
      "financial": {
        "status": "completed",
        "quality_score": 0.89
      },
      "environmental": {
        "status": "running",
        "progress": 0.45
      },
      "social": {
        "status": "pending"
      }
    }
  },
  "message": "Progress: 45% (5/12 steps)"
}
```

---

### Log Events

#### LOG_MESSAGE

Log message (info, warning, error).

```json
{
  "event_type": "LOG_MESSAGE",
  "plan_id": "plan_001",
  "step_id": "step_financial",
  "agent_id": "fin_001",
  "timestamp": "2025-10-08T14:30:03.123Z",
  "data": {
    "level": "INFO",
    "message": "Retrieving financial data from database",
    "context": {
      "query": "SELECT * FROM financial_metrics WHERE year=2025"
    }
  },
  "message": "INFO: Retrieving financial data"
}
```

**Log Levels:**
- `DEBUG`: Detailed debugging information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

---

## Client Examples

### JavaScript/TypeScript

#### Basic Connection

```javascript
const client_id = 'client_' + Math.random().toString(36).substr(2, 9);
const plan_id = 'plan_001';
const ws = new WebSocket(
  `wss://api.veritas.example.com/api/v1/streaming/ws/${client_id}?plan_id=${plan_id}`
);

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`[${data.event_type}]`, data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log('WebSocket closed:', event.code, event.reason);
};
```

#### React Hook

```typescript
import { useEffect, useState } from 'react';

interface StreamEvent {
  event_type: string;
  plan_id: string;
  timestamp: string;
  data?: any;
  message?: string;
}

function useAgentStream(planId: string) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const clientId = 'client_' + Math.random().toString(36).substr(2, 9);
    const ws = new WebSocket(
      `wss://api.veritas.example.com/api/v1/streaming/ws/${clientId}?plan_id=${planId}`
    );

    ws.onopen = () => {
      setIsConnected(true);
      console.log('Connected to agent stream');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as StreamEvent;
      setEvents(prev => [...prev, data]);
      
      // Handle specific event types
      switch(data.event_type) {
        case 'PLAN_COMPLETED':
          console.log('Plan completed!', data.data);
          ws.close();
          break;
        case 'PLAN_FAILED':
          setError(new Error(data.message || 'Plan failed'));
          break;
        case 'QUALITY_CHECK':
          console.log('Quality score:', data.data.score);
          break;
      }
    };

    ws.onerror = (error) => {
      setError(error as Error);
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [planId]);

  return { events, isConnected, error };
}

// Usage
function AgentDashboard({ planId }: { planId: string }) {
  const { events, isConnected, error } = useAgentStream(planId);

  return (
    <div>
      <div>Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      {error && <div>Error: {error.message}</div>}
      <ul>
        {events.map((event, i) => (
          <li key={i}>{event.event_type}: {event.message}</li>
        ))}
      </ul>
    </div>
  );
}
```

---

### Python

#### Basic Connection

```python
import asyncio
import json
import websockets

async def stream_agent_execution(plan_id: str):
    client_id = f"client_{uuid.uuid4().hex[:8]}"
    uri = f"wss://api.veritas.example.com/api/v1/streaming/ws/{client_id}?plan_id={plan_id}"
    
    async with websockets.connect(uri) as websocket:
        print(f"Connected to agent stream for plan: {plan_id}")
        
        async for message in websocket:
            data = json.loads(message)
            event_type = data['event_type']
            
            print(f"[{event_type}] {data.get('message', '')}")
            
            # Handle specific events
            if event_type == 'PLAN_COMPLETED':
                print(f"Plan completed! Quality score: {data['data']['quality_score']}")
                break
            elif event_type == 'PLAN_FAILED':
                print(f"Plan failed: {data['message']}")
                break
            elif event_type == 'QUALITY_CHECK':
                score = data['data']['score']
                passed = data['data']['passed']
                print(f"Quality check: {score:.2f} ({'PASS' if passed else 'FAIL'})")

# Run
asyncio.run(stream_agent_execution('plan_001'))
```

#### Advanced Client with Reconnection

```python
import asyncio
import json
import logging
import websockets
from typing import Callable, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentStreamClient:
    def __init__(
        self,
        plan_id: str,
        client_id: Optional[str] = None,
        on_event: Optional[Callable] = None,
        max_reconnects: int = 3
    ):
        self.plan_id = plan_id
        self.client_id = client_id or f"client_{uuid.uuid4().hex[:8]}"
        self.on_event = on_event
        self.max_reconnects = max_reconnects
        self.reconnect_count = 0
        
    @property
    def uri(self) -> str:
        return f"wss://api.veritas.example.com/api/v1/streaming/ws/{self.client_id}?plan_id={self.plan_id}"
    
    async def connect(self):
        """Connect to WebSocket with automatic reconnection."""
        while self.reconnect_count < self.max_reconnects:
            try:
                async with websockets.connect(self.uri) as websocket:
                    logger.info(f"Connected to plan: {self.plan_id}")
                    self.reconnect_count = 0  # Reset on successful connection
                    
                    async for message in websocket:
                        data = json.loads(message)
                        
                        # Call event handler
                        if self.on_event:
                            await self.on_event(data)
                        
                        # Exit on completion
                        if data['event_type'] in ('PLAN_COMPLETED', 'PLAN_FAILED'):
                            logger.info(f"Plan finished: {data['event_type']}")
                            return
                            
            except websockets.exceptions.ConnectionClosed:
                self.reconnect_count += 1
                logger.warning(f"Connection closed. Reconnecting... ({self.reconnect_count}/{self.max_reconnects})")
                await asyncio.sleep(2 ** self.reconnect_count)  # Exponential backoff
                
            except Exception as e:
                logger.error(f"Error: {e}")
                break
        
        logger.error("Max reconnection attempts reached")

# Usage
async def handle_event(event):
    print(f"[{event['event_type']}] {event.get('message', '')}")

client = AgentStreamClient(
    plan_id='plan_001',
    on_event=handle_event,
    max_reconnects=5
)

asyncio.run(client.connect())
```

---

## Error Handling

### Connection Errors

**Error:** Connection refused

```json
{
  "type": "error",
  "code": "CONNECTION_REFUSED",
  "message": "Unable to connect to WebSocket server",
  "timestamp": "2025-10-08T14:30:00Z"
}
```

**Solution:** Check network connectivity and server status.

---

**Error:** Authentication failed

```json
{
  "type": "error",
  "code": "AUTHENTICATION_FAILED",
  "message": "Invalid or missing authentication token",
  "timestamp": "2025-10-08T14:30:00Z"
}
```

**Solution:** Provide valid JWT token in connection URL or first message.

---

**Error:** Plan not found

```json
{
  "type": "error",
  "code": "PLAN_NOT_FOUND",
  "message": "Execution plan plan_001 not found",
  "timestamp": "2025-10-08T14:30:00Z"
}
```

**Solution:** Verify plan_id exists and is accessible by authenticated user.

---

### Message Errors

**Error:** Invalid JSON

Client receives close frame with code `1003` (Unsupported Data).

**Solution:** Ensure all messages are valid JSON.

---

**Error:** Message too large

Client receives close frame with code `1009` (Message Too Big).

**Solution:** Messages must be < 1MB. Split large payloads.

---

### Close Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `1000` | Normal Closure | Normal closure, plan completed or client disconnected |
| `1001` | Going Away | Server shutting down or page navigating away |
| `1002` | Protocol Error | WebSocket protocol error |
| `1003` | Unsupported Data | Invalid data format (non-JSON) |
| `1006` | Abnormal Closure | Connection lost without close frame |
| `1008` | Policy Violation | Message violates policy (e.g., authentication failed) |
| `1009` | Message Too Big | Message exceeds 1MB limit |
| `1011` | Internal Error | Server error during processing |

---

## Best Practices

### 1. Connection Management

**✅ Do:**
- Generate unique client_id for each connection
- Implement automatic reconnection with exponential backoff
- Close connections when no longer needed
- Monitor connection state

**❌ Don't:**
- Reuse client_id across multiple connections
- Reconnect immediately after connection loss
- Leave connections open indefinitely
- Ignore connection state changes

---

### 2. Event Handling

**✅ Do:**
- Handle all event types gracefully
- Log events for debugging
- Update UI progressively as events arrive
- Handle completion and failure events

**❌ Don't:**
- Assume events arrive in order (they usually do, but aren't guaranteed)
- Block the event loop with heavy processing
- Ignore error events
- Parse events without error handling

---

### 3. Error Recovery

**✅ Do:**
- Implement retry logic with exponential backoff
- Log all errors with context
- Notify users of connection issues
- Fall back to polling if WebSocket unavailable

**❌ Don't:**
- Retry indefinitely without backoff
- Suppress errors silently
- Leave users in unknown state
- Abandon execution on temporary failures

---

### 4. Performance

**✅ Do:**
- Process events asynchronously
- Batch UI updates
- Debounce high-frequency events
- Close connections when plan completes

**❌ Don't:**
- Update UI on every single event
- Store unlimited event history in memory
- Open multiple connections for same plan
- Keep connections open after completion

---

### 5. Security

**✅ Do:**
- Always use WSS (secure WebSocket) in production
- Include authentication token
- Validate event data before using
- Implement rate limiting on client side

**❌ Don't:**
- Use WS (insecure) in production
- Send sensitive data without encryption
- Trust event data blindly
- Spam the server with connection requests

---

## Support

For WebSocket issues:

- **Documentation**: https://docs.veritas.example.com/websocket
- **Status**: https://status.veritas.example.com
- **GitHub**: https://github.com/veritas/framework/issues
- **Email**: support@veritas.example.com

---

**Last Updated:** 2025-10-08  
**Version:** 1.0.0  
**License:** MIT
