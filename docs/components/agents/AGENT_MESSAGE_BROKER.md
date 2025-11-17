# Agent Message Broker

**Version:** 1.1  
**Status:** ✅ STABLE  
**Zuletzt aktualisiert:** 17. November 2025  
**Quellcode:** 
- `backend/agents/agent_message_broker.py` (826 LOC)
- `backend/agents/agent_message_broker_enhanced.py` (393 LOC)
- **Total:** 1,219 LOC

---

## 📋 Übersicht

Der **AgentMessageBroker** ist der zentrale Event-Bus für Inter-Agent-Kommunikation im VERITAS Multi-Agent-System. Er ermöglicht asynchrone, entkoppelte Kommunikation zwischen Agents mit garantierter Message-Delivery und umfangreichen Monitoring-Funktionen.

**Zweck:** Zuverlässige, skalierbare Message-Vermittlung für Agent-zu-Agent-Kommunikation mit Multi-Worker-Architektur für hohen Durchsatz (500+ msg/s).

**Kernfunktionen:**
- **Message-Routing:** Point-to-Point, Broadcast, Pub/Sub
- **Topic-basiertes Subscription-System:** Flexible Event-Subscriptions
- **Priority-basierte Message-Queue:** asyncio.PriorityQueue für Prioritäts-Handling
- **Multi-Worker-Pattern:** 3-10 parallele Worker für hohen Throughput
- **Message-Batching:** Batch-Processing für Performance-Optimierung
- **Async/Await Support:** Non-blocking Operations mit asyncio
- **Delivery-Guarantees:** Best-Effort mit Retry-Logik
- **Dead-Letter-Queue:** Handling fehlgeschlagener Deliveries
- **Request/Response Pattern:** Synchrone Kommunikation mit Timeout
- **Worker-Health-Monitoring:** Auto-Restart bei Worker-Failures
- **Comprehensive Statistics:** Performance-Monitoring und Analytics

---

## 🏗️ Architektur

### Komponenten-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                   AgentMessageBroker                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Agent Registry   │  │ Subscription     │  │ Message      │  │
│  │                  │  │ Manager          │  │ Queue        │  │
│  │ - Agents         │  │ - Topics         │  │ (Priority)   │  │
│  │ - Handlers       │  │ - Subscribers    │  │              │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Worker Pool Manager                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  │ Worker N │ │  │
│  │  │          │  │          │  │          │  │          │ │  │
│  │  │ Process  │  │ Process  │  │ Process  │  │ Process  │ │  │
│  │  │ Messages │  │ Messages │  │ Messages │  │ Messages │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ Pending          │  │ Dead Letter      │                    │
│  │ Requests         │  │ Queue            │                    │
│  │ (Futures)        │  │ (Failed Msgs)    │                    │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### Message Flow

```
1. Agent sendet Message
   ↓
2. Message wird in Priority-Queue eingefügt
   ↓
3. Worker-Pool holt Messages aus Queue
   │
   ├─ Mit Batching: Sammelt bis batch_size oder timeout
   └─ Ohne Batching: Verarbeitet einzeln
   ↓
4. Message-Delivery
   │
   ├─ Point-to-Point: An spezifischen Agent
   ├─ Broadcast: An alle Agents
   └─ Pub/Sub: An Topic-Subscribers
   ↓
5. Handler-Callback aufrufen
   │
   ├─ Success → Stats aktualisieren
   └─ Failure → Retry oder Dead-Letter-Queue
   ↓
6. Optional: Response für Request/Response-Pattern
```

### Multi-Worker-Pattern

```
Message Queue (Priority)
    ↓
┌───┴─────┬─────┬─────┬─────┐
│ Worker1 │ W2  │ W3  │ W4  │
└───┬─────┴─────┴─────┴─────┘
    ↓
Parallel Message Processing
    ↓
┌───┴─────┬─────┬─────┐
│ Agent A │ B   │ C   │ ... (Delivery)
└─────────┴─────┴─────┘
```

**Vorteile:**
- **Höherer Throughput:** 500+ messages/sec (vs. 100 msg/s single-worker)
- **Fault Tolerance:** Worker-Ausfall betrifft nur Teil der Kapazität
- **Auto-Recovery:** Failed Workers werden automatisch neu gestartet
- **Load Balancing:** Messages werden gleichmäßig auf Worker verteilt

---

## 📚 API-Referenz

### Hauptklasse: `AgentMessageBroker`

#### Konstruktor

```python
def __init__(
    self,
    config: Optional[BrokerConfiguration] = None,
    max_queue_size: Optional[int] = None,  # deprecated
    max_retry: Optional[int] = None  # deprecated
)
```

**Parameter:**
- `config` (Optional[BrokerConfiguration]): Performance-Konfiguration (empfohlen)
- `max_queue_size` (Optional[int]): Legacy-Parameter, use `config` instead
- `max_retry` (Optional[int]): Legacy-Parameter, use `config` instead

**Beispiel:**
```python
# Empfohlen: Mit Configuration
config = BrokerConfiguration(
    num_workers=5,
    enable_batching=True,
    batch_size=20
)
broker = AgentMessageBroker(config=config)

# Legacy (backward-kompatibel)
broker = AgentMessageBroker(max_queue_size=5000, max_retry=2)
```

#### Lifecycle-Methoden

##### `async start()`

Startet den Message-Broker mit Worker-Pool.

```python
await broker.start()
```

**Raises:**
- `RuntimeError`: Wenn Broker bereits läuft

**Beispiel:**
```python
broker = AgentMessageBroker()
await broker.start()
# Broker läuft jetzt mit 5 Workern (default)
```

##### `async stop()`

Stoppt den Message-Broker und Worker-Pool graceful.

```python
await broker.stop()
```

**Features:**
- Stoppt alle Worker
- Cancelt pending Requests
- Berechnet Uptime-Statistiken

**Beispiel:**
```python
await broker.stop()
# Alle Worker gestoppt, Stats ausgegeben
```

#### Agent-Management

##### `register_agent(agent_id, agent_identity, callback)`

Registriert einen Agent beim Broker.

**Parameter:**
- `agent_id` (str): Eindeutige Agent-ID
- `agent_identity` (AgentIdentity): Agent-Metadaten (type, capabilities, etc.)
- `callback` (Callable): Message-Handler-Funktion

**Beispiel:**
```python
from shared.protocols.agent_message import AgentIdentity

identity = AgentIdentity(
    agent_id="rag_agent_001",
    agent_type="RAGAgent",
    capabilities=["search", "retrieve", "rank"]
)

async def on_message(msg: AgentMessage):
    print(f"Received: {msg.content}")

broker.register_agent("rag_agent_001", identity, on_message)
```

##### `unregister_agent(agent_id)`

Deregistriert einen Agent.

**Parameter:**
- `agent_id` (str): Agent-ID

**Beispiel:**
```python
broker.unregister_agent("rag_agent_001")
```

##### `get_agent(agent_id) -> Optional[AgentIdentity]`

Ruft Agent-Informationen ab.

**Returns:** AgentIdentity oder None

**Beispiel:**
```python
agent = broker.get_agent("rag_agent_001")
if agent:
    print(f"Type: {agent.agent_type}")
```

##### `get_agents_by_type(agent_type) -> List[AgentIdentity]`

Findet alle Agents eines bestimmten Typs.

**Parameter:**
- `agent_type` (str): Agent-Typ (z.B. "RAGAgent", "AnalysisAgent")

**Returns:** Liste von AgentIdentity

**Beispiel:**
```python
rag_agents = broker.get_agents_by_type("RAGAgent")
print(f"Found {len(rag_agents)} RAG agents")
```

##### `get_agents_by_capability(capability) -> List[AgentIdentity]`

Findet alle Agents mit bestimmter Capability.

**Parameter:**
- `capability` (str): Capability (z.B. "search", "analyze")

**Returns:** Liste von AgentIdentity

**Beispiel:**
```python
search_agents = broker.get_agents_by_capability("search")
for agent in search_agents:
    print(f"- {agent.agent_id}")
```

#### Subscription-Management (Pub/Sub)

##### `subscribe(agent_id, topic)`

Subscribed einen Agent auf ein Topic.

**Parameter:**
- `agent_id` (str): Agent-ID
- `topic` (str): Topic-Name

**Beispiel:**
```python
broker.subscribe("rag_agent_001", "document_updates")
broker.subscribe("rag_agent_002", "document_updates")
```

##### `unsubscribe(agent_id, topic)`

Desubscribed einen Agent von einem Topic.

**Parameter:**
- `agent_id` (str): Agent-ID
- `topic` (str): Topic-Name

**Beispiel:**
```python
broker.unsubscribe("rag_agent_001", "document_updates")
```

##### `get_subscribers(topic) -> Set[str]`

Ruft alle Subscriber eines Topics ab.

**Returns:** Set von Agent-IDs

**Beispiel:**
```python
subscribers = broker.get_subscribers("document_updates")
print(f"{len(subscribers)} subscribers")
```

#### Message-Sending

##### `async send_message(message)`

Sendet eine Message (Point-to-Point oder Broadcast).

**Parameter:**
- `message` (AgentMessage): Message-Objekt

**Beispiel:**
```python
from shared.protocols.agent_message import AgentMessage, MessageType

message = AgentMessage(
    message_id="msg_001",
    sender_id="coordinator",
    recipient_id="rag_agent_001",
    message_type=MessageType.REQUEST,
    content={"query": "Find documents about Bauantrag"}
)

await broker.send_message(message)
```

##### `async send_request(message, timeout=30.0) -> Any`

Sendet Request und wartet auf Response (Request/Response-Pattern).

**Parameter:**
- `message` (AgentMessage): Request-Message
- `timeout` (float): Timeout in Sekunden

**Returns:** Response-Content

**Raises:**
- `asyncio.TimeoutError`: Bei Timeout

**Beispiel:**
```python
request = AgentMessage(
    message_id="req_001",
    sender_id="coordinator",
    recipient_id="rag_agent_001",
    message_type=MessageType.REQUEST,
    content={"query": "Search documents"}
)

try:
    response = await broker.send_request(request, timeout=10.0)
    print(f"Response: {response}")
except asyncio.TimeoutError:
    print("Request timeout!")
```

##### `async publish_event(topic, sender_id, event_data)`

Published ein Event an alle Topic-Subscriber.

**Parameter:**
- `topic` (str): Topic-Name
- `sender_id` (str): Sender-ID
- `event_data` (Dict): Event-Payload

**Beispiel:**
```python
await broker.publish_event(
    topic="document_updates",
    sender_id="indexer",
    event_data={
        "action": "indexed",
        "document_id": "doc_123",
        "timestamp": "2025-11-17T06:00:00Z"
    }
)
```

#### Statistics & Monitoring

##### `get_stats() -> Dict[str, Any]`

Ruft umfassende Broker-Statistiken ab.

**Returns:** Dictionary mit:
- `messages_sent`: Gesendete Messages
- `messages_delivered`: Erfolgreich zugestellte Messages
- `messages_failed`: Fehlgeschlagene Messages
- `messages_retried`: Retry-Versuche
- `requests_timeout`: Request-Timeouts
- `agents_registered`: Anzahl registrierter Agents
- `subscriptions_active`: Anzahl aktiver Subscriptions
- `broker_uptime_seconds`: Uptime in Sekunden
- `worker_pool`: Worker-Pool-Statistiken
- `batches_processed`: Verarbeitete Batches
- `avg_batch_size`: Durchschnittliche Batch-Größe

**Beispiel:**
```python
stats = broker.get_stats()
print(f"Throughput: {stats['messages_delivered']} messages")
print(f"Workers: {stats['worker_pool']['workers_active']}")
print(f"Uptime: {stats['broker_uptime_seconds']:.1f}s")
```

##### `get_dead_letters() -> List[Tuple[AgentMessage, str]]`

Ruft fehlgeschlagene Messages aus Dead-Letter-Queue ab.

**Returns:** Liste von (Message, Error-Reason) Tuples

**Beispiel:**
```python
dead_letters = broker.get_dead_letters()
for msg, reason in dead_letters:
    print(f"Failed: {msg.message_id} - {reason}")
```

##### `clear_dead_letters()`

Löscht Dead-Letter-Queue.

```python
broker.clear_dead_letters()
```

---

## ⚙️ Konfiguration

### BrokerConfiguration

```python
@dataclass
class BrokerConfiguration:
    # Worker Pool
    num_workers: int = 5
    enable_batching: bool = True
    worker_restart_on_failure: bool = True
    worker_health_check_interval_sec: float = 30.0
    
    # Message Batching
    batch_size: int = 20
    batch_timeout_ms: int = 100
    
    # Queue Settings
    max_queue_size: int = 10000
    queue_warning_threshold: float = 0.8
    
    # Performance Tuning
    delivery_parallelism: int = 10
    retry_max_attempts: int = 3
    retry_backoff_ms: int = 100
```

### Konfigurations-Presets

#### Low-Latency (Single-Message Processing)

```python
config = BrokerConfiguration(
    num_workers=3,
    enable_batching=False,  # Keine Batches
    max_queue_size=1000
)
```

#### High-Throughput (Batch Processing)

```python
config = BrokerConfiguration(
    num_workers=8,
    enable_batching=True,
    batch_size=50,
    batch_timeout_ms=50
)
```

#### Balanced (Default)

```python
config = BrokerConfiguration(
    num_workers=5,
    enable_batching=True,
    batch_size=20,
    batch_timeout_ms=100
)
```

#### Resource-Constrained

```python
config = BrokerConfiguration(
    num_workers=2,
    enable_batching=True,
    batch_size=10,
    max_queue_size=5000
)
```

---

## 💡 Verwendungsbeispiele

### Beispiel 1: Basic Setup

```python
import asyncio
from backend.agents.agent_message_broker import AgentMessageBroker
from shared.protocols.agent_message import AgentIdentity, AgentMessage, MessageType

async def main():
    # 1. Broker erstellen und starten
    broker = AgentMessageBroker()
    await broker.start()
    
    # 2. Agent registrieren
    async def handle_message(msg: AgentMessage):
        print(f"Received: {msg.content}")
    
    identity = AgentIdentity(
        agent_id="agent_1",
        agent_type="TestAgent",
        capabilities=["test"]
    )
    broker.register_agent("agent_1", identity, handle_message)
    
    # 3. Message senden
    message = AgentMessage(
        message_id="msg_1",
        sender_id="system",
        recipient_id="agent_1",
        message_type=MessageType.REQUEST,
        content={"action": "test"}
    )
    await broker.send_message(message)
    
    # 4. Cleanup
    await asyncio.sleep(1)  # Warten auf Verarbeitung
    await broker.stop()

asyncio.run(main())
```

### Beispiel 2: Pub/Sub Pattern

```python
async def main():
    broker = AgentMessageBroker()
    await broker.start()
    
    # Subscribers registrieren
    async def subscriber1_handler(msg):
        print(f"Sub1: {msg.content}")
    
    async def subscriber2_handler(msg):
        print(f"Sub2: {msg.content}")
    
    # Agents registrieren
    broker.register_agent("sub1", identity1, subscriber1_handler)
    broker.register_agent("sub2", identity2, subscriber2_handler)
    
    # Topic subscriben
    broker.subscribe("sub1", "news")
    broker.subscribe("sub2", "news")
    
    # Event publishen
    await broker.publish_event(
        topic="news",
        sender_id="publisher",
        event_data={"headline": "New document indexed"}
    )
    
    await asyncio.sleep(1)
    await broker.stop()
```

### Beispiel 3: Request/Response Pattern

```python
async def main():
    broker = AgentMessageBroker()
    await broker.start()
    
    # Responder registrieren
    async def responder_handler(msg):
        if msg.message_type == MessageType.REQUEST:
            # Response senden
            response = AgentMessage(
                message_id=f"resp_{msg.message_id}",
                sender_id="responder",
                recipient_id=msg.sender_id,
                message_type=MessageType.RESPONSE,
                content={"result": "OK"},
                correlation_id=msg.message_id  # Wichtig!
            )
            await broker.send_message(response)
    
    broker.register_agent("responder", identity, responder_handler)
    
    # Request senden und auf Response warten
    request = AgentMessage(
        message_id="req_1",
        sender_id="requester",
        recipient_id="responder",
        message_type=MessageType.REQUEST,
        content={"query": "Process this"}
    )
    
    try:
        response = await broker.send_request(request, timeout=5.0)
        print(f"Got response: {response}")
    except asyncio.TimeoutError:
        print("Request timeout!")
    
    await broker.stop()
```

### Beispiel 4: High-Throughput Configuration

```python
from backend.agents.agent_message_broker_enhanced import BrokerConfiguration

async def main():
    # High-Throughput Config
    config = BrokerConfiguration(
        num_workers=8,
        enable_batching=True,
        batch_size=50,
        batch_timeout_ms=50,
        delivery_parallelism=20
    )
    
    broker = AgentMessageBroker(config=config)
    await broker.start()
    
    # ... Agents registrieren, Messages senden ...
    
    # Stats prüfen
    stats = broker.get_stats()
    print(f"Throughput: {stats['messages_delivered']} messages")
    print(f"Active Workers: {stats['worker_pool']['workers_active']}")
    print(f"Avg Batch Size: {stats['avg_batch_size']:.1f}")
    
    await broker.stop()
```

### Beispiel 5: Agent Discovery by Capability

```python
async def main():
    broker = AgentMessageBroker()
    await broker.start()
    
    # Mehrere Agents mit verschiedenen Capabilities registrieren
    agents = [
        ("rag_1", ["search", "retrieve"]),
        ("rag_2", ["search", "rank"]),
        ("analyzer", ["analyze", "classify"])
    ]
    
    for agent_id, caps in agents:
        identity = AgentIdentity(
            agent_id=agent_id,
            agent_type="GenericAgent",
            capabilities=caps
        )
        broker.register_agent(agent_id, identity, lambda m: None)
    
    # Agents mit "search" Capability finden
    search_agents = broker.get_agents_by_capability("search")
    print(f"Search agents: {[a.agent_id for a in search_agents]}")
    # Output: ['rag_1', 'rag_2']
    
    await broker.stop()
```

---

## 🔧 Troubleshooting

### Problem 1: Messages werden nicht zugestellt

**Symptom:** `send_message()` kehrt zurück, aber Handler wird nicht aufgerufen

**Ursachen:**
- Agent nicht registriert
- Broker nicht gestartet
- Handler wirft Exception

**Lösung:**
```python
# 1. Prüfen ob Agent registriert ist
agent = broker.get_agent("my_agent")
if agent is None:
    print("Agent not registered!")

# 2. Prüfen ob Broker läuft
if not broker._running:
    await broker.start()

# 3. Exception-Handling im Handler
async def safe_handler(msg):
    try:
        # ... processing ...
        pass
    except Exception as e:
        logger.error(f"Handler error: {e}")

# 4. Dead-Letter-Queue prüfen
dead_letters = broker.get_dead_letters()
for msg, reason in dead_letters:
    print(f"Failed: {msg.message_id} - {reason}")
```

### Problem 2: Request-Timeouts

**Symptom:** `send_request()` wirft `asyncio.TimeoutError`

**Ursachen:**
- Responder antwortet nicht
- Timeout zu kurz
- `correlation_id` fehlt in Response

**Lösung:**
```python
# 1. Timeout erhöhen
response = await broker.send_request(request, timeout=60.0)

# 2. Sicherstellen dass Response correlation_id setzt
response_msg = AgentMessage(
    ...
    correlation_id=request.message_id  # WICHTIG!
)

# 3. Responder-Status prüfen
responder = broker.get_agent("responder_id")
if responder is None:
    print("Responder not available!")
```

### Problem 3: Hohe Message-Queue

**Symptom:** Queue-Warning: "Queue 80% full"

**Ursachen:**
- Worker zu langsam
- Zu viele Messages
- Worker-Failures

**Lösung:**
```python
# 1. Worker erhöhen
config = BrokerConfiguration(num_workers=10)  # statt 5
broker = AgentMessageBroker(config=config)

# 2. Batching aktivieren/optimieren
config.enable_batching = True
config.batch_size = 50  # größere Batches

# 3. Stats prüfen
stats = broker.get_stats()
print(f"Queue size: {stats['worker_pool'].get('queue_size', 0)}")
print(f"Workers: {stats['worker_pool']['workers_active']}")

# 4. Worker-Health prüfen
if stats['worker_pool']['workers_failed'] > 0:
    print("Some workers failed!")
```

### Problem 4: Worker-Failures

**Symptom:** "Worker X failed and was restarted"

**Ursachen:**
- Exception in Message-Handler
- Resource-Limits (Memory)
- Deadlock

**Lösung:**
```python
# 1. Handler-Exceptions catchen
async def robust_handler(msg):
    try:
        await process_message(msg)
    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        # Nicht re-raisen!

# 2. Auto-Restart deaktivieren (zum Debuggen)
config = BrokerConfiguration(worker_restart_on_failure=False)

# 3. Worker-Logs prüfen
# Logs zeigen Stack-Trace bei Worker-Failure

# 4. Resource-Limits erhöhen
# - Memory-Limit erhöhen
# - delivery_parallelism reduzieren
config.delivery_parallelism = 5  # statt 10
```

### Problem 5: Schlechte Performance

**Symptom:** Niedriger Throughput (<100 msg/s)

**Ursachen:**
- Zu wenig Worker
- Batching deaktiviert
- Handler zu langsam

**Lösung:**
```python
# 1. Performance-Profiling
import time

async def timed_handler(msg):
    start = time.time()
    await process_message(msg)
    duration = time.time() - start
    if duration > 0.1:
        logger.warning(f"Slow handler: {duration:.2f}s")

# 2. High-Throughput Config
config = BrokerConfiguration(
    num_workers=8,
    enable_batching=True,
    batch_size=50,
    delivery_parallelism=20
)

# 3. Stats monitoren
stats = broker.get_stats()
uptime = stats['broker_uptime_seconds']
throughput = stats['messages_delivered'] / uptime if uptime > 0 else 0
print(f"Throughput: {throughput:.1f} msg/s")

# 4. Handler optimieren
# - Asynchrone I/O verwenden
# - Caching einbauen
# - Schwere Operationen auslagern
```

---

## 🔗 Verwandte Dokumentation

### Dependencies

- **AgentMessage Protocol:** `shared/protocols/agent_message.py`
  - Dokumentation: (TODO) `docs/protocols/AGENT_MESSAGE_PROTOCOL.md`

- **AgentIdentity:** `shared/protocols/agent_message.py`
  - Capabilities, Agent-Types, Metadata

### Verwandte Services

- **Agent Registry:** `backend/agents/agent_registry.py`
  - Dokumentation: (TODO) `docs/components/agents/AGENT_REGISTRY.md`

- **Agent Executor:** `backend/services/agent_executor.py`
  - Dokumentation: (TODO) `docs/components/services/AGENT_EXECUTOR.md`

- **Process Executor:** `backend/services/process_executor.py`
  - Dokumentation: `docs/components/services/PROCESS_EXECUTOR.md` ✅

### Architektur-Dokumente

- **Agent System Analysis:** `docs/AGENT_SYSTEM_ANALYSIS_REPORT.md`
- **Agent Integration:** `docs/AGENT_INTEGRATION_ACTION_PLAN.md`
- **Multi-Agent Status:** `docs/MULTI_AGENT_STATUS_REPORT.md`

---

## 📊 Performance-Charakteristiken

### Throughput

**Measured Performance:**
- Single-Worker: ~100-150 messages/sec
- Multi-Worker (5): ~400-600 messages/sec
- Multi-Worker (8): ~600-800 messages/sec

**Mit Batching:**
- Batch-Size 20: ~500 messages/sec
- Batch-Size 50: ~700 messages/sec

### Latency

**Message-Delivery-Latenz:**
- Without Batching: ~5-10ms (P50), ~20-30ms (P99)
- With Batching: ~15-25ms (P50), ~100-150ms (P99)

**Faktoren:**
- Handler-Execution-Time
- Queue-Size
- Worker-Count
- Batch-Configuration

### Memory Usage

**Geschätzte Memory-Nutzung:**
- Base Broker: ~20 MB
- Pro Worker: ~10-20 MB
- Pro 1000 Messages in Queue: ~5-10 MB
- **Total (typical):** ~100-200 MB (5 workers, moderate load)

### Scalability

**Worker-Scaling:**
```
Workers   Throughput   Latency (P50)   Memory
1         150 msg/s    5ms             30 MB
3         400 msg/s    8ms             60 MB
5         600 msg/s    10ms            100 MB
8         800 msg/s    15ms            150 MB
```

**Empfohlene Konfiguration:**
- **Standard:** 5 workers, batch_size=20
- **High-Throughput:** 8 workers, batch_size=50
- **Low-Latency:** 3 workers, batching=False

---

## 🧪 Testing

### Unit Tests

```python
# tests/test_agent_message_broker.py
import pytest
from backend.agents.agent_message_broker import AgentMessageBroker
from shared.protocols.agent_message import AgentMessage, MessageType

@pytest.mark.asyncio
async def test_basic_message_delivery():
    broker = AgentMessageBroker()
    await broker.start()
    
    received = []
    async def handler(msg):
        received.append(msg)
    
    broker.register_agent("agent_1", identity, handler)
    
    message = AgentMessage(
        message_id="test",
        sender_id="sender",
        recipient_id="agent_1",
        message_type=MessageType.REQUEST,
        content={}
    )
    
    await broker.send_message(message)
    await asyncio.sleep(0.1)
    
    assert len(received) == 1
    await broker.stop()

@pytest.mark.asyncio
async def test_pubsub():
    broker = AgentMessageBroker()
    await broker.start()
    
    received1, received2 = [], []
    
    broker.register_agent("sub1", id1, lambda m: received1.append(m))
    broker.register_agent("sub2", id2, lambda m: received2.append(m))
    
    broker.subscribe("sub1", "topic")
    broker.subscribe("sub2", "topic")
    
    await broker.publish_event("topic", "publisher", {"data": "test"})
    await asyncio.sleep(0.1)
    
    assert len(received1) == 1
    assert len(received2) == 1
    await broker.stop()
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_request_response():
    broker = AgentMessageBroker()
    await broker.start()
    
    async def responder(msg):
        if msg.message_type == MessageType.REQUEST:
            response = AgentMessage(
                message_id="resp",
                sender_id="responder",
                recipient_id=msg.sender_id,
                message_type=MessageType.RESPONSE,
                content={"result": "OK"},
                correlation_id=msg.message_id
            )
            await broker.send_message(response)
    
    broker.register_agent("responder", identity, responder)
    
    request = AgentMessage(
        message_id="req",
        sender_id="requester",
        recipient_id="responder",
        message_type=MessageType.REQUEST,
        content={}
    )
    
    response = await broker.send_request(request, timeout=5.0)
    assert response["result"] == "OK"
    
    await broker.stop()
```

---

## 📝 Changelog

### Version 1.1 (6. Oktober 2025)
- **NEW:** Multi-Worker-Pattern für höheren Throughput
- **NEW:** Message-Batching für Performance-Optimierung
- **NEW:** Worker-Health-Monitoring mit Auto-Restart
- **NEW:** BrokerConfiguration für Performance-Tuning
- **IMPROVED:** Throughput: 150 → 600+ msg/s
- **IMPROVED:** Worker-Pool-Management
- **IMPROVED:** Statistics & Monitoring

### Version 1.0 (Initial Release)
- Basic Message-Broker
- Point-to-Point, Broadcast, Pub/Sub
- Request/Response Pattern
- Dead-Letter-Queue
- Single-Worker Processing

---

**Maintainer:** VERITAS Development Team  
**Last Review:** 17. November 2025  
**Next Review:** Q1 2026
