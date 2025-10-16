# Phase 4: Agent-Kommunikationsprotokoll - Design-Dokument

**Version:** 1.0  
**Datum:** 6. Oktober 2025  
**Status:** 🔄 In Entwicklung  
**Autor:** VERITAS Development Team

---

## 📋 Executive Summary

### Zielsetzung
Implementierung eines standardisierten, ereignisbasierten Kommunikationsprotokolls für Inter-Agent-Messaging im VERITAS Multi-Agent-System. Ermöglicht direkte Agent-zu-Agent-Kommunikation, Context-Sharing, asynchrone Kollaboration und verbesserte Supervisor-Koordination.

### Key Features
- ✅ **AgentMessage Schema:** Standardisiertes Nachrichtenformat (JSON-serializable)
- ✅ **Message Broker:** Zentraler Event-Bus für Routing und Delivery
- ✅ **Kommunikationsmuster:** Request/Response, Pub/Sub, Broadcast, Point-to-Point
- ✅ **Async Support:** asyncio-basiert für non-blocking Operations
- ✅ **Context-Sharing:** RAG-Context-Austausch zwischen Agenten
- ✅ **Supervisor-Integration:** Message-basierte SubQuery-Distribution

### Erfolgs-Kriterien
1. **Latenz:** < 50ms für Message-Delivery (intra-process)
2. **Throughput:** > 1000 Messages/sec
3. **Reliability:** 99.9% Delivery-Guarantee (mindestens best-effort)
4. **Backward-Kompatibilität:** 100% (opt-in für bestehende Agenten)
5. **Code-Qualität:** 90%+ Test-Coverage
6. **Performance:** < 5% Overhead vs. direkte Funktion-Calls

---

## 🏗️ Architektur-Übersicht

### Komponenten-Hierarchie

```
┌─────────────────────────────────────────────────────────────────┐
│                     VERITAS Agent System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐         ┌───────────────┐                   │
│  │ Supervisor    │◄────────┤ Message       │                   │
│  │ Agent         │────────►│ Broker        │                   │
│  └───────────────┘         └───────┬───────┘                   │
│         │                          │                            │
│         │ coordinates              │ routes                     │
│         ▼                          ▼                            │
│  ┌──────────────────────────────────────────────────────┐      │
│  │            Agent Communication Layer                 │      │
│  ├──────────────────────────────────────────────────────┤      │
│  │                                                       │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │      │
│  │  │Environmental│  │Construction │  │ Financial   │ │      │
│  │  │Agent        │  │Agent        │  │ Agent       │ │      │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │      │
│  │         │                │                 │         │      │
│  │         └────────────────┼─────────────────┘         │      │
│  │                          │                           │      │
│  │                    sends/receives                    │      │
│  │                     AgentMessage                     │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │         Shared Protocols & Data Structures           │      │
│  ├──────────────────────────────────────────────────────┤      │
│  │  • AgentMessage (Dataclass)                          │      │
│  │  • MessageType (Enum)                                │      │
│  │  • AgentIdentity (Dataclass)                         │      │
│  │  • MessageMetadata (Dataclass)                       │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### Datenfluss-Diagramm

```
Request/Response Pattern:
────────────────────────────

  Agent A                Message Broker           Agent B
    │                         │                      │
    │  1. send_message()      │                      │
    ├────────────────────────►│                      │
    │     (Request)           │  2. route_message()  │
    │                         ├─────────────────────►│
    │                         │                      │
    │                         │  3. on_message()     │
    │                         │       callback       │
    │                         │                      │
    │                         │  4. send_response()  │
    │  6. receive_message()   │◄─────────────────────┤
    │◄────────────────────────┤     (Response)       │
    │     (Response)          │                      │
    │                         │                      │


Publish/Subscribe Pattern:
────────────────────────────

  Publisher              Message Broker         Subscribers
    │                         │                  │  │  │
    │  1. publish_event()     │                  │  │  │
    ├────────────────────────►│                  │  │  │
    │     (Event)             │  2. broadcast    │  │  │
    │                         ├──────────────────┼──┼──┤
    │                         │                  │  │  │
    │                         │  3. on_event()   │  │  │
    │                         │     callbacks    ▼  ▼  ▼
    │                         │               Subscriber
    │                         │               Handlers
```

---

## 📦 Datenstrukturen

### 1. AgentMessage (Core Message Schema)

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class MessageType(Enum):
    """Nachrichtentypen für Agent-Kommunikation"""
    REQUEST = "request"           # Anfrage mit erwarteter Antwort
    RESPONSE = "response"         # Antwort auf REQUEST
    EVENT = "event"              # Ereignis-Notification (Pub/Sub)
    BROADCAST = "broadcast"      # An alle Agenten
    CONTEXT_SHARE = "context_share"  # RAG-Context-Austausch
    STATUS_UPDATE = "status_update"  # Agent-Status-Änderung
    ERROR = "error"              # Fehler-Notification

class MessagePriority(Enum):
    """Prioritäts-Levels für Message-Routing"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

@dataclass
class AgentIdentity:
    """Eindeutige Agent-Identifikation"""
    agent_id: str               # Eindeutige ID (UUID)
    agent_type: str            # Typ (environmental, construction, etc.)
    agent_name: str            # Menschenlesbarer Name
    capabilities: List[str] = field(default_factory=list)
    
    def __hash__(self):
        return hash(self.agent_id)
    
    def __eq__(self, other):
        return isinstance(other, AgentIdentity) and self.agent_id == other.agent_id

@dataclass
class MessageMetadata:
    """Metadaten für Message-Routing und Tracking"""
    timestamp: datetime = field(default_factory=datetime.now)
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Für Request/Response-Matching
    reply_to: Optional[str] = None  # Message-ID für Antworten
    ttl_seconds: int = 300         # Time-to-Live (5 min default)
    retry_count: int = 0
    headers: Dict[str, Any] = field(default_factory=dict)  # Zusätzliche Header

@dataclass
class AgentMessage:
    """
    Standardisiertes Nachrichtenformat für Inter-Agent-Kommunikation
    
    Beispiel:
        message = AgentMessage(
            message_id="msg-123",
            sender=AgentIdentity("agent-env-1", "environmental", "EnvAgent1"),
            recipients=[AgentIdentity("agent-fin-1", "financial", "FinAgent1")],
            message_type=MessageType.REQUEST,
            payload={"query": "Grundstückskosten für Bauvorhaben XYZ?"},
            metadata=MessageMetadata(priority=MessagePriority.HIGH)
        )
    """
    message_id: str = field(default_factory=lambda: f"msg-{uuid.uuid4()}")
    sender: AgentIdentity
    recipients: List[AgentIdentity]  # Leer = Broadcast
    message_type: MessageType
    payload: Dict[str, Any]
    metadata: MessageMetadata = field(default_factory=MessageMetadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialisierung für JSON-Transport"""
        return {
            "message_id": self.message_id,
            "sender": {
                "agent_id": self.sender.agent_id,
                "agent_type": self.sender.agent_type,
                "agent_name": self.sender.agent_name,
                "capabilities": self.sender.capabilities
            },
            "recipients": [
                {
                    "agent_id": r.agent_id,
                    "agent_type": r.agent_type,
                    "agent_name": r.agent_name,
                    "capabilities": r.capabilities
                }
                for r in self.recipients
            ],
            "message_type": self.message_type.value,
            "payload": self.payload,
            "metadata": {
                "timestamp": self.metadata.timestamp.isoformat(),
                "priority": self.metadata.priority.value,
                "correlation_id": self.metadata.correlation_id,
                "reply_to": self.metadata.reply_to,
                "ttl_seconds": self.metadata.ttl_seconds,
                "retry_count": self.metadata.retry_count,
                "headers": self.metadata.headers
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Deserialisierung aus JSON"""
        sender_data = data["sender"]
        sender = AgentIdentity(
            agent_id=sender_data["agent_id"],
            agent_type=sender_data["agent_type"],
            agent_name=sender_data["agent_name"],
            capabilities=sender_data.get("capabilities", [])
        )
        
        recipients = [
            AgentIdentity(
                agent_id=r["agent_id"],
                agent_type=r["agent_type"],
                agent_name=r["agent_name"],
                capabilities=r.get("capabilities", [])
            )
            for r in data["recipients"]
        ]
        
        metadata_data = data["metadata"]
        metadata = MessageMetadata(
            timestamp=datetime.fromisoformat(metadata_data["timestamp"]),
            priority=MessagePriority(metadata_data["priority"]),
            correlation_id=metadata_data["correlation_id"],
            reply_to=metadata_data.get("reply_to"),
            ttl_seconds=metadata_data.get("ttl_seconds", 300),
            retry_count=metadata_data.get("retry_count", 0),
            headers=metadata_data.get("headers", {})
        )
        
        return cls(
            message_id=data["message_id"],
            sender=sender,
            recipients=recipients,
            message_type=MessageType(data["message_type"]),
            payload=data["payload"],
            metadata=metadata
        )
```

---

## 🔄 AgentMessageBroker (Event-Bus)

### Kernfunktionalität

```python
import asyncio
from typing import Callable, Dict, List, Optional, Set
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class AgentMessageBroker:
    """
    Zentraler Message-Broker für Agent-zu-Agent-Kommunikation
    
    Features:
    - Message-Routing (Point-to-Point, Broadcast, Pub/Sub)
    - Topic-basiertes Subscription-System
    - Priority-basierte Message-Queue
    - Async/Await Support
    - Delivery-Guarantees (Best-Effort)
    - Dead-Letter-Queue für fehlgeschlagene Deliveries
    """
    
    def __init__(self):
        # Agent-Registry: agent_id -> AgentIdentity
        self._agents: Dict[str, AgentIdentity] = {}
        
        # Message-Handler-Registry: agent_id -> callback
        self._handlers: Dict[str, Callable[[AgentMessage], Any]] = {}
        
        # Topic-Subscriptions: topic -> Set[agent_id]
        self._subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # Message-Queue (Priority-Queue mit asyncio)
        self._message_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        
        # Pending Requests: correlation_id -> asyncio.Future
        self._pending_requests: Dict[str, asyncio.Future] = {}
        
        # Dead-Letter-Queue für fehlgeschlagene Messages
        self._dead_letter_queue: List[AgentMessage] = []
        
        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "subscriptions_active": 0,
            "agents_registered": 0
        }
        
        # Background-Worker für Message-Processing
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Startet den Message-Broker Background-Worker"""
        if self._running:
            logger.warning("⚠️ Message-Broker läuft bereits")
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._message_worker())
        logger.info("✅ Message-Broker gestartet")
    
    async def stop(self):
        """Stoppt den Message-Broker"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Message-Broker gestoppt")
    
    def register_agent(self, identity: AgentIdentity, handler: Callable[[AgentMessage], Any]):
        """
        Registriert einen Agenten mit Message-Handler
        
        Args:
            identity: Agent-Identität
            handler: Callback-Funktion für eingehende Messages
        """
        self._agents[identity.agent_id] = identity
        self._handlers[identity.agent_id] = handler
        self._stats["agents_registered"] = len(self._agents)
        logger.info(f"📝 Agent registriert: {identity.agent_name} ({identity.agent_id})")
    
    def unregister_agent(self, agent_id: str):
        """Entfernt einen Agenten aus dem Broker"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            del self._handlers[agent_id]
            
            # Remove from all subscriptions
            for topic in self._subscriptions:
                self._subscriptions[topic].discard(agent_id)
            
            self._stats["agents_registered"] = len(self._agents)
            logger.info(f"🗑️ Agent deregistriert: {agent_id}")
    
    def subscribe(self, agent_id: str, topic: str):
        """
        Abonniert ein Topic für einen Agenten
        
        Args:
            agent_id: Agent-ID
            topic: Topic-Name (z.B. "rag_context_updates", "agent_status_changes")
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} nicht registriert")
        
        self._subscriptions[topic].add(agent_id)
        self._stats["subscriptions_active"] = sum(len(subs) for subs in self._subscriptions.values())
        logger.info(f"📬 Agent {agent_id} abonniert Topic: {topic}")
    
    def unsubscribe(self, agent_id: str, topic: str):
        """Beendet Subscription für ein Topic"""
        self._subscriptions[topic].discard(agent_id)
        self._stats["subscriptions_active"] = sum(len(subs) for subs in self._subscriptions.values())
        logger.info(f"📭 Agent {agent_id} deabonniert Topic: {topic}")
    
    async def send_message(self, message: AgentMessage) -> bool:
        """
        Sendet eine Message (Point-to-Point oder Broadcast)
        
        Args:
            message: AgentMessage-Objekt
            
        Returns:
            True wenn Message in Queue eingereiht wurde
        """
        # Priority-basiertes Queuing
        priority = -message.metadata.priority.value  # Negative für Max-Heap
        await self._message_queue.put((priority, message))
        self._stats["messages_sent"] += 1
        
        logger.debug(f"📤 Message gesendet: {message.message_id} ({message.message_type.value})")
        return True
    
    async def send_request(self, message: AgentMessage, timeout: float = 30.0) -> Optional[AgentMessage]:
        """
        Sendet eine REQUEST-Message und wartet auf RESPONSE
        
        Args:
            message: Request-Message
            timeout: Timeout in Sekunden
            
        Returns:
            Response-Message oder None bei Timeout
        """
        if message.message_type != MessageType.REQUEST:
            raise ValueError("send_request() erfordert MessageType.REQUEST")
        
        # Future für Response erstellen
        future = asyncio.Future()
        self._pending_requests[message.metadata.correlation_id] = future
        
        # Request senden
        await self.send_message(message)
        
        try:
            # Auf Response warten (mit Timeout)
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Request-Timeout: {message.message_id}")
            del self._pending_requests[message.metadata.correlation_id]
            return None
    
    async def publish_event(self, topic: str, sender: AgentIdentity, payload: Dict[str, Any]):
        """
        Publiziert ein Event an alle Subscribers eines Topics
        
        Args:
            topic: Topic-Name
            sender: Sender-Identität
            payload: Event-Daten
        """
        # Subscribers für Topic ermitteln
        subscribers = self._subscriptions.get(topic, set())
        
        if not subscribers:
            logger.debug(f"📢 Kein Subscriber für Topic: {topic}")
            return
        
        # Event-Message erstellen
        recipients = [self._agents[agent_id] for agent_id in subscribers if agent_id in self._agents]
        
        message = AgentMessage(
            sender=sender,
            recipients=recipients,
            message_type=MessageType.EVENT,
            payload={"topic": topic, "data": payload},
            metadata=MessageMetadata(priority=MessagePriority.NORMAL)
        )
        
        await self.send_message(message)
        logger.info(f"📢 Event publiziert: {topic} → {len(recipients)} Subscribers")
    
    async def _message_worker(self):
        """Background-Worker für Message-Delivery"""
        logger.info("🔄 Message-Worker gestartet")
        
        while self._running:
            try:
                # Message aus Queue holen (mit Timeout)
                priority, message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )
                
                # Message verarbeiten
                await self._deliver_message(message)
                
            except asyncio.TimeoutError:
                # Keine Messages in Queue, weiter warten
                continue
            except Exception as e:
                logger.error(f"❌ Fehler im Message-Worker: {e}", exc_info=True)
    
    async def _deliver_message(self, message: AgentMessage):
        """Liefert eine Message an Empfänger"""
        try:
            # Broadcast oder Point-to-Point?
            if not message.recipients:
                # Broadcast an alle Agenten
                recipients = list(self._agents.values())
            else:
                recipients = message.recipients
            
            # TTL prüfen
            elapsed = (datetime.now() - message.metadata.timestamp).total_seconds()
            if elapsed > message.metadata.ttl_seconds:
                logger.warning(f"⏱️ Message expired (TTL {message.metadata.ttl_seconds}s): {message.message_id}")
                self._dead_letter_queue.append(message)
                self._stats["messages_failed"] += 1
                return
            
            # An jeden Empfänger ausliefern
            delivery_count = 0
            for recipient in recipients:
                if recipient.agent_id not in self._handlers:
                    logger.warning(f"⚠️ Handler für Agent {recipient.agent_id} nicht gefunden")
                    continue
                
                try:
                    # Handler aufrufen (async oder sync)
                    handler = self._handlers[recipient.agent_id]
                    if asyncio.iscoroutinefunction(handler):
                        response = await handler(message)
                    else:
                        response = handler(message)
                    
                    # Für REQUEST: Response verarbeiten
                    if message.message_type == MessageType.REQUEST and response:
                        # Response-Message erstellen
                        if isinstance(response, dict):
                            response_msg = AgentMessage(
                                sender=recipient,
                                recipients=[message.sender],
                                message_type=MessageType.RESPONSE,
                                payload=response,
                                metadata=MessageMetadata(
                                    correlation_id=message.metadata.correlation_id,
                                    reply_to=message.message_id
                                )
                            )
                            await self.send_message(response_msg)
                    
                    # Für RESPONSE: Pending-Request auflösen
                    if message.message_type == MessageType.RESPONSE:
                        correlation_id = message.metadata.correlation_id
                        if correlation_id in self._pending_requests:
                            self._pending_requests[correlation_id].set_result(message)
                            del self._pending_requests[correlation_id]
                    
                    delivery_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Fehler bei Message-Delivery an {recipient.agent_id}: {e}", exc_info=True)
            
            self._stats["messages_delivered"] += delivery_count
            logger.debug(f"✅ Message zugestellt: {message.message_id} → {delivery_count} Empfänger")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Message-Delivery: {e}", exc_info=True)
            self._dead_letter_queue.append(message)
            self._stats["messages_failed"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Liefert Broker-Statistiken"""
        return {
            **self._stats,
            "queue_size": self._message_queue.qsize(),
            "pending_requests": len(self._pending_requests),
            "dead_letter_queue_size": len(self._dead_letter_queue)
        }
```

---

## 🤖 Agent Base-Class Erweiterung

### Kommunikations-Mixin

```python
from typing import Optional, Callable, Dict, Any
import asyncio

class AgentCommunicationMixin:
    """
    Mixin für Agent-Klassen zur Aktivierung von Message-basierter Kommunikation
    
    Usage:
        class EnvironmentalAgent(AgentCommunicationMixin):
            def __init__(self, broker: AgentMessageBroker):
                self.identity = AgentIdentity(
                    agent_id="env-agent-1",
                    agent_type="environmental",
                    agent_name="Environmental Analysis Agent",
                    capabilities=["environmental_analysis", "geographic_data"]
                )
                super().__init__(broker, self.identity)
    """
    
    def __init__(self, broker: AgentMessageBroker, identity: AgentIdentity):
        self.broker = broker
        self.identity = identity
        self._message_handlers: Dict[MessageType, Callable] = {}
        
        # Bei Broker registrieren
        self.broker.register_agent(self.identity, self._on_message)
        
        # Standard-Handler registrieren
        self.register_message_handler(MessageType.REQUEST, self._handle_request)
        self.register_message_handler(MessageType.EVENT, self._handle_event)
        self.register_message_handler(MessageType.CONTEXT_SHARE, self._handle_context_share)
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Registriert einen Handler für einen Message-Typ"""
        self._message_handlers[message_type] = handler
    
    async def _on_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Callback für eingehende Messages"""
        handler = self._message_handlers.get(message.message_type)
        
        if handler:
            if asyncio.iscoroutinefunction(handler):
                return await handler(message)
            else:
                return handler(message)
        else:
            logger.warning(f"⚠️ Kein Handler für Message-Typ {message.message_type.value}")
            return None
    
    async def send_message(self, recipients: List[AgentIdentity], message_type: MessageType, 
                          payload: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """Sendet eine Message an andere Agenten"""
        message = AgentMessage(
            sender=self.identity,
            recipients=recipients,
            message_type=message_type,
            payload=payload,
            metadata=MessageMetadata(priority=priority)
        )
        return await self.broker.send_message(message)
    
    async def send_request(self, recipient: AgentIdentity, payload: Dict[str, Any], 
                          timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Sendet eine Request-Message und wartet auf Response"""
        message = AgentMessage(
            sender=self.identity,
            recipients=[recipient],
            message_type=MessageType.REQUEST,
            payload=payload,
            metadata=MessageMetadata(priority=MessagePriority.NORMAL)
        )
        response = await self.broker.send_request(message, timeout=timeout)
        return response.payload if response else None
    
    async def publish_event(self, topic: str, payload: Dict[str, Any]):
        """Publiziert ein Event an Topic-Subscribers"""
        await self.broker.publish_event(topic, self.identity, payload)
    
    def subscribe(self, topic: str):
        """Abonniert ein Topic"""
        self.broker.subscribe(self.identity.agent_id, topic)
    
    # Standard-Handler (können überschrieben werden)
    
    async def _handle_request(self, message: AgentMessage) -> Dict[str, Any]:
        """Standard-Handler für REQUEST-Messages"""
        logger.info(f"📨 Request erhalten: {message.payload}")
        return {"status": "acknowledged", "message_id": message.message_id}
    
    async def _handle_event(self, message: AgentMessage) -> None:
        """Standard-Handler für EVENT-Messages"""
        logger.info(f"📢 Event erhalten: {message.payload}")
    
    async def _handle_context_share(self, message: AgentMessage) -> None:
        """Standard-Handler für CONTEXT_SHARE-Messages"""
        logger.info(f"🔄 Context-Share erhalten: {message.payload}")
```

---

## 🎯 Kommunikationsmuster

### 1. Request/Response Pattern

**Use-Case:** Agent A benötigt Informationen von Agent B

```python
# Agent A (Financial Agent) sendet Request an Agent B (Construction Agent)
response = await financial_agent.send_request(
    recipient=construction_agent.identity,
    payload={
        "query": "Baukosten für Projekt XYZ?",
        "project_id": "proj-123",
        "detail_level": "high"
    },
    timeout=30.0
)

if response:
    construction_costs = response["construction_costs"]
    logger.info(f"Baukosten erhalten: {construction_costs}")
```

### 2. Publish/Subscribe Pattern

**Use-Case:** RAG-Context-Updates an interessierte Agenten broadcasen

```python
# Agent A published Context-Update
await environmental_agent.publish_event(
    topic="rag_context_updates",
    payload={
        "context_type": "geographic_boundaries",
        "project_id": "proj-123",
        "data": {"boundaries": [...], "coordinates": [...]}
    }
)

# Agents B, C, D haben Topic abonniert und erhalten Event automatisch
financial_agent.subscribe("rag_context_updates")
construction_agent.subscribe("rag_context_updates")
social_agent.subscribe("rag_context_updates")
```

### 3. Broadcast Pattern

**Use-Case:** Status-Update an alle Agenten

```python
# Supervisor sendet Broadcast (recipients = [])
await supervisor.send_message(
    recipients=[],  # Broadcast
    message_type=MessageType.BROADCAST,
    payload={
        "announcement": "System-Update in 5 Minuten",
        "action_required": "save_state"
    },
    priority=MessagePriority.HIGH
)
```

### 4. Context-Sharing Pattern

**Use-Case:** Agent teilt RAG-Context mit anderen Agenten

```python
# Environmental Agent teilt Geo-Context mit Construction Agent
await environmental_agent.send_message(
    recipients=[construction_agent.identity],
    message_type=MessageType.CONTEXT_SHARE,
    payload={
        "context_id": "geo-ctx-123",
        "context_type": "geographic",
        "data": {
            "project_area": "52.520°N, 13.405°E",
            "terrain_type": "urban",
            "soil_quality": "good"
        },
        "metadata": {
            "source": "official_geodata_api",
            "confidence": 0.95
        }
    }
)
```

---

## 🔗 SupervisorAgent Integration

### Message-basierte SubQuery-Distribution

```python
class SupervisorAgent(AgentCommunicationMixin):
    """
    SupervisorAgent mit Message-basierter Agent-Koordination
    """
    
    def __init__(self, broker: AgentMessageBroker, query_decomposer, agent_selector, result_synthesizer):
        identity = AgentIdentity(
            agent_id="supervisor-agent-1",
            agent_type="supervisor",
            agent_name="Supervisor Orchestration Agent",
            capabilities=["query_decomposition", "agent_coordination", "result_synthesis"]
        )
        super().__init__(broker, identity)
        
        self.query_decomposer = query_decomposer
        self.agent_selector = agent_selector
        self.result_synthesizer = result_synthesizer
    
    async def process_query_with_messages(self, query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verarbeitet Query mit Message-basierter Agent-Koordination
        
        Workflow:
        1. Query dekomponieren
        2. Agenten für SubQueries auswählen
        3. SubQueries via Messages an Agenten verteilen
        4. Responses sammeln
        5. Ergebnisse synthetisieren
        """
        logger.info(f"🎯 Supervisor verarbeitet Query mit Message-Protokoll: {query[:100]}")
        
        # Step 1: Query dekomponieren
        subqueries = await self.query_decomposer.decompose_query(query, user_context)
        logger.info(f"📋 {len(subqueries)} SubQueries erstellt")
        
        # Step 2: Agenten auswählen
        agent_plan = await self.agent_selector.create_agent_plan(subqueries, user_context)
        logger.info(f"🤖 Agent-Plan erstellt: {len(agent_plan.assignments)} Assignments")
        
        # Step 3: SubQueries via Messages verteilen
        tasks = []
        for assignment in agent_plan.assignments:
            # Agent-Identity aus Registry holen
            agent_identity = self._get_agent_identity(assignment.agent_type)
            
            if agent_identity:
                # Request-Message erstellen und senden
                task = self.send_request(
                    recipient=agent_identity,
                    payload={
                        "subquery": assignment.subquery.text,
                        "subquery_id": assignment.subquery.metadata.get("decomposition_index"),
                        "context": user_context,
                        "expected_capabilities": assignment.required_capabilities
                    },
                    timeout=60.0
                )
                tasks.append((assignment.agent_type, task))
        
        # Step 4: Parallel auf Responses warten
        results = []
        for agent_type, task in tasks:
            try:
                response = await task
                if response:
                    results.append({
                        "agent_type": agent_type,
                        "result_data": response.get("result", {}),
                        "status": "completed",
                        "confidence_score": response.get("confidence", 0.8)
                    })
            except Exception as e:
                logger.error(f"❌ Fehler bei Agent {agent_type}: {e}")
                results.append({
                    "agent_type": agent_type,
                    "result_data": {"error": str(e)},
                    "status": "failed",
                    "confidence_score": 0.0
                })
        
        # Step 5: Ergebnisse synthetisieren
        agent_results = [
            AgentResult(
                agent_type=r["agent_type"],
                result_data=r["result_data"],
                status=r["status"],
                confidence_score=r["confidence_score"]
            )
            for r in results
        ]
        
        synthesized = await self.result_synthesizer.synthesize_results(
            query=query,
            agent_results=agent_results,
            user_context=user_context
        )
        
        logger.info(f"✅ Query erfolgreich verarbeitet (Message-Protokoll)")
        
        return {
            "final_answer": synthesized.final_answer,
            "confidence_score": synthesized.confidence_score,
            "sources": synthesized.sources,
            "metadata": {
                "subqueries": len(subqueries),
                "agents_used": len(results),
                "protocol": "message_based"
            }
        }
    
    def _get_agent_identity(self, agent_type: str) -> Optional[AgentIdentity]:
        """Holt Agent-Identity aus Broker-Registry"""
        for agent_id, identity in self.broker._agents.items():
            if identity.agent_type == agent_type:
                return identity
        return None
```

---

## 📊 Performance-Benchmarks & Ziele

### Latenz-Ziele

| Operation | Target | Acceptable |
|-----------|--------|------------|
| Message-Routing (intra-process) | < 10ms | < 50ms |
| Request/Response Round-Trip | < 100ms | < 500ms |
| Publish/Subscribe Broadcast (10 Subscribers) | < 50ms | < 200ms |
| Message-Serialization (to_dict/from_dict) | < 1ms | < 5ms |

### Throughput-Ziele

| Metric | Target | Acceptable |
|--------|--------|------------|
| Messages/Second (Single-Broker) | > 1000 | > 500 |
| Concurrent-Requests | > 100 | > 50 |
| Subscribers-per-Topic | > 50 | > 20 |

### Overhead-Ziele

| Metric | Target | Acceptable |
|--------|--------|------------|
| Memory-Overhead vs. Direct-Calls | < 3% | < 10% |
| CPU-Overhead vs. Direct-Calls | < 5% | < 15% |
| Latency-Overhead vs. Direct-Calls | < 5% | < 20% |

---

## 🧪 Testing-Strategie

### 1. Unit-Tests

**Dateien:**
- `tests/test_agent_message.py` - AgentMessage Serialization/Deserialization
- `tests/test_message_broker.py` - Broker Core-Funktionalität
- `tests/test_communication_mixin.py` - Agent Mixin-Funktionalität

**Coverage-Ziel:** 90%+

### 2. Integration-Tests

**Dateien:**
- `tests/test_request_response_pattern.py`
- `tests/test_publish_subscribe_pattern.py`
- `tests/test_context_sharing_pattern.py`
- `tests/test_supervisor_message_coordination.py`

**Szenarien:**
- 2-Agent Request/Response
- 5-Agent Pub/Sub mit Topic
- Supervisor koordiniert 3 Agenten via Messages
- Concurrent-Requests (100 parallel)

### 3. Performance-Tests

**Datei:** `tests/performance/test_message_throughput.py`

**Benchmarks:**
- Message-Routing Latency (1000 Messages)
- Throughput-Test (10.000 Messages in 10s)
- Concurrent-Request-Test (100 parallel Requests)
- Memory-Profiling (100.000 Messages)

### 4. End-to-End-Tests

**Datei:** `tests/e2e/test_full_pipeline_with_messages.py`

**Szenario:**
- User-Query → SupervisorAgent
- Supervisor dekomponiert → 3 SubQueries
- Supervisor sendet Messages an 3 Agenten (Environmental, Construction, Financial)
- Agenten antworten mit Results
- Supervisor synthetisiert Final-Answer
- Verify: Performance < 15s, Accuracy > 0.85

---

## 🚀 Implementation-Roadmap

### Phase 4.1: Core Protocol (Tag 1-2)
- ✅ AgentMessage Dataclass implementieren
- ✅ MessageType & MessagePriority Enums
- ✅ AgentIdentity & MessageMetadata
- ✅ Serialization/Deserialization (to_dict/from_dict)
- ✅ Unit-Tests für AgentMessage

### Phase 4.2: Message-Broker (Tag 2-3)
- ✅ AgentMessageBroker Basis-Implementierung
- ✅ Agent-Registry & Handler-Registry
- ✅ Message-Queue (Priority-basiert)
- ✅ Message-Worker (Background-Task)
- ✅ send_message() & _deliver_message()
- ✅ Unit-Tests für Broker

### Phase 4.3: Kommunikationsmuster (Tag 3-4)
- ✅ Request/Response mit Pending-Requests
- ✅ Publish/Subscribe mit Topic-Subscriptions
- ✅ Broadcast-Mechanismus
- ✅ Context-Sharing-Pattern
- ✅ Integration-Tests für alle Pattern

### Phase 4.4: Agent-Integration (Tag 4-5)
- ✅ AgentCommunicationMixin erstellen
- ✅ Bestehende Agenten migrieren (Environmental, Construction, Financial)
- ✅ Message-Handler implementieren
- ✅ Integration-Tests für Agent-Kommunikation

### Phase 4.5: Supervisor-Integration (Tag 5-6)
- ✅ SupervisorAgent um Message-Protokoll erweitern
- ✅ process_query_with_messages() implementieren
- ✅ Message-basierte SubQuery-Distribution
- ✅ E2E-Tests mit Supervisor

### Phase 4.6: Performance & Optimierung (Tag 6-7)
- ✅ Performance-Benchmarks durchführen
- ✅ Bottlenecks identifizieren
- ✅ Optimierungen implementieren (z.B. Message-Batching)
- ✅ Load-Tests (1000+ concurrent requests)

### Phase 4.7: Dokumentation & Abschluss (Tag 7)
- ✅ API-Dokumentation erstellen
- ✅ Usage-Examples & Best-Practices
- ✅ Migration-Guide für bestehende Agenten
- ✅ Implementation-Report mit Lessons-Learned

---

## 📚 Best Practices & Guidelines

### 1. Message-Design

**DO:**
- ✅ Kleine, fokussierte Payloads (< 100KB)
- ✅ Klare Message-Types verwenden
- ✅ Correlation-IDs für Request/Response
- ✅ TTL für zeitkritische Messages setzen

**DON'T:**
- ❌ Große Binär-Daten in Payload (> 1MB)
- ❌ Sensitive-Daten unverschlüsselt
- ❌ Zirkuläre Message-Chains (A→B→C→A)
- ❌ Blocking-Operations in Message-Handlers

### 2. Error-Handling

**DO:**
- ✅ Graceful Degradation bei fehlgeschlagener Delivery
- ✅ Dead-Letter-Queue für fehlerhafte Messages
- ✅ Retry-Logic mit Exponential-Backoff
- ✅ Comprehensive-Logging für Debugging

**DON'T:**
- ❌ Silent-Failures ohne Logging
- ❌ Infinite-Retry-Loops
- ❌ Exception-Swallowing in Handlers

### 3. Performance

**DO:**
- ✅ Async/Await für non-blocking Operations
- ✅ Priority-basiertes Queuing für wichtige Messages
- ✅ Message-Batching für hohen Durchsatz
- ✅ Connection-Pooling bei Remote-Agents

**DON'T:**
- ❌ Synchronous-Blocking in Async-Context
- ❌ Unbounded-Queues ohne Memory-Limits
- ❌ Polling statt Event-basiert

---

## 🔄 Migration-Guide für bestehende Agenten

### Schritt 1: AgentCommunicationMixin hinzufügen

```python
# Vorher:
class EnvironmentalAgent:
    def __init__(self):
        self.agent_type = "environmental"

# Nachher:
class EnvironmentalAgent(AgentCommunicationMixin):
    def __init__(self, broker: AgentMessageBroker):
        identity = AgentIdentity(
            agent_id="env-agent-1",
            agent_type="environmental",
            agent_name="Environmental Agent",
            capabilities=["environmental_analysis"]
        )
        super().__init__(broker, identity)
```

### Schritt 2: Message-Handler implementieren

```python
class EnvironmentalAgent(AgentCommunicationMixin):
    def __init__(self, broker: AgentMessageBroker):
        # ... (wie oben)
        
        # Custom-Handler registrieren
        self.register_message_handler(MessageType.REQUEST, self._handle_analysis_request)
    
    async def _handle_analysis_request(self, message: AgentMessage) -> Dict[str, Any]:
        """Handler für Environmental-Analysis-Requests"""
        query = message.payload.get("query")
        project_id = message.payload.get("project_id")
        
        # Analyse durchführen
        result = await self.analyze_environment(query, project_id)
        
        # Response zurückgeben
        return {
            "result": result,
            "confidence": 0.92,
            "agent": "environmental"
        }
```

### Schritt 3: Broker beim Start initialisieren

```python
# In main() oder setup():
broker = AgentMessageBroker()
await broker.start()

# Agenten erstellen
env_agent = EnvironmentalAgent(broker)
construction_agent = ConstructionAgent(broker)
financial_agent = FinancialAgent(broker)

# Supervisor erstellen
supervisor = SupervisorAgent(
    broker=broker,
    query_decomposer=QueryDecomposer(),
    agent_selector=AgentSelector(),
    result_synthesizer=ResultSynthesizer()
)
```

---

## 📈 Erfolgs-Metriken

### Technische Metriken

| Kriterium | Ziel | Status |
|-----------|------|--------|
| Message-Latency | < 50ms | 🔄 TBD |
| Throughput | > 1000 msg/s | 🔄 TBD |
| Test-Coverage | > 90% | 🔄 TBD |
| Backward-Kompatibilität | 100% | ✅ Garantiert |
| Performance-Overhead | < 5% | 🔄 TBD |

### Funktionale Metriken

| Kriterium | Ziel | Status |
|-----------|------|--------|
| Request/Response Pattern | ✅ Implementiert | 🔄 In Progress |
| Publish/Subscribe Pattern | ✅ Implementiert | 🔄 In Progress |
| Context-Sharing | ✅ Implementiert | 🔄 In Progress |
| Supervisor-Integration | ✅ Implementiert | 🔄 In Progress |
| Dead-Letter-Queue | ✅ Implementiert | 🔄 In Progress |

### Code-Metriken

| Komponente | Geschätzt | Aktuell |
|------------|-----------|---------|
| agent_message.py | 300 Zeilen | 🔄 TBD |
| agent_message_broker.py | 500 Zeilen | 🔄 TBD |
| communication_mixin.py | 200 Zeilen | 🔄 TBD |
| Tests | 600 Zeilen | 🔄 TBD |
| Dokumentation | 800 Zeilen | ✅ 800+ |
| **TOTAL** | **2400 Zeilen** | 🔄 TBD |

---

## 🎓 Lessons Learned (aus Phase 3)

### Was funktioniert hat:
1. ✅ **Design-First-Approach:** Umfassendes Design-Dokument vor Implementation
2. ✅ **Dataclass-basierte Designs:** Klare, typsichere Datenstrukturen
3. ✅ **Backward-Kompatibilität:** Feature-Flags für opt-in Adoption
4. ✅ **Fallback-Strategien:** Graceful Degradation bei Fehlern

### Was verbessert werden kann:
1. 🔧 **LLM-Integration:** Robustere JSON-Parsing mit Retry-Logic
2. 🔧 **Testing:** Mehr Unit-Tests vor Integration-Tests
3. 🔧 **Performance-Testing:** Frühere Benchmarks während Development

### Anwendung auf Phase 4:
- ✅ Design-Dokument zuerst (✓ Done)
- ✅ Unit-Tests parallel zur Implementation
- ✅ Performance-Benchmarks nach jedem Major-Component
- ✅ Kontinuierliche Integration-Tests
- ✅ Backward-Kompatibilität von Anfang an

---

## 🔮 Zukunfts-Erweiterungen

### Short-Term (Post Phase 4)
- 🔄 **Message-Persistence:** Redis/RabbitMQ für distributed Messaging
- 🔄 **Circuit-Breaker:** Automatische Fehler-Isolation
- 🔄 **Rate-Limiting:** Schutz vor Message-Flooding

### Medium-Term
- 🔄 **Remote-Agent-Support:** gRPC/HTTP für verteilte Agenten
- 🔄 **Message-Encryption:** End-to-End-Verschlüsselung
- 🔄 **Monitoring-Dashboard:** Real-time Message-Flow-Visualisierung

### Long-Term
- 🔄 **Federated-Messaging:** Multi-Cluster Agent-Kommunikation
- 🔄 **AI-based-Routing:** ML-optimierte Message-Routing-Entscheidungen
- 🔄 **Blockchain-Audit-Trail:** Unveränderbare Message-History

---

## 📝 Offene Fragen & Entscheidungen

### Technische Entscheidungen
1. **Message-Persistence:** In-Memory (asyncio.Queue) vs. Persistent (Redis)?
   - **Entscheidung:** Phase 4.1 mit In-Memory starten, Redis als Phase 4.8 Extension
   
2. **Serialization-Format:** JSON vs. Protocol-Buffers vs. MessagePack?
   - **Entscheidung:** JSON für Phase 4 (readable, debuggable), Protobuf als Optimization später
   
3. **Error-Handling:** Best-Effort vs. At-Least-Once vs. Exactly-Once Delivery?
   - **Entscheidung:** Best-Effort für Phase 4, At-Least-Once als Extension

### Architektur-Entscheidungen
1. **Broker-Architektur:** Single-Broker vs. Multi-Broker (per Agent-Type)?
   - **Entscheidung:** Single-Broker für Simplicity, Multi-Broker als Scaling-Option
   
2. **Message-Ordering:** FIFO vs. Priority-based vs. No-Guarantee?
   - **Entscheidung:** Priority-based (balanciert Performance und Fairness)

---

## ✅ Acceptance-Criteria

### Must-Have (Phase 4 Completion)
- ✅ AgentMessage Dataclass mit Serialization/Deserialization
- ✅ AgentMessageBroker mit Request/Response, Pub/Sub, Broadcast
- ✅ AgentCommunicationMixin für Agent-Integration
- ✅ SupervisorAgent Message-basierte Koordination
- ✅ 90%+ Test-Coverage
- ✅ Performance < 50ms Latency, > 500 msg/s Throughput
- ✅ 100% Backward-Kompatibilität

### Should-Have
- ✅ Dead-Letter-Queue für fehlerhafte Messages
- ✅ TTL-basiertes Message-Expiry
- ✅ Priority-basiertes Queuing
- ✅ Comprehensive-Logging & Statistics

### Nice-to-Have (Future Extensions)
- 🔄 Message-Persistence (Redis)
- 🔄 Remote-Agent-Support (gRPC)
- 🔄 Monitoring-Dashboard

---

**Status:** 🎯 **DESIGN ABGESCHLOSSEN - BEREIT FÜR IMPLEMENTATION**

**Nächster Schritt:** Phase 4.1 - Core Protocol Implementation starten

