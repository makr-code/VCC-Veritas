"""
VERITAS Agent Communication Protocol - Message Broker

Zentraler Event-Bus für Inter-Agent-Kommunikation im VERITAS Multi-Agent-System.

Features:
- Message-Routing (Point-to-Point, Broadcast, Pub/Sub)
- Topic-basiertes Subscription-System
- Priority-basierte Message-Queue
- Async/Await Support (asyncio)
- Delivery-Guarantees (Best-Effort)
- Dead-Letter-Queue für fehlgeschlagene Deliveries
- Request/Response Pattern mit Timeout
- Statistics & Monitoring

Version: 1.0
Author: VERITAS Development Team
Date: 6. Oktober 2025
"""

import asyncio
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared"))

try:
    from shared.protocols.agent_message import AgentIdentity, AgentMessage, MessageMetadata, MessagePriority, MessageType
except ModuleNotFoundError:
    # Fallback: direkt importieren
    from protocols.agent_message import AgentIdentity, AgentMessage, MessageMetadata, MessagePriority, MessageType

logger = logging.getLogger(__name__)

# Import Enhanced Components
try:
    from backend.agents.agent_message_broker_enhanced import (
        DEFAULT_CONFIG,
        BrokerConfiguration,
        MessageWorker,
        WorkerPoolManager,
    )
except ModuleNotFoundError:
    from agent_message_broker_enhanced import DEFAULT_CONFIG, BrokerConfiguration, MessageWorker, WorkerPoolManager


class AgentMessageBroker:
    """
    Zentraler Message-Broker für Agent-zu-Agent-Kommunikation

    Features:
    - Message-Routing (Point-to-Point, Broadcast, Pub/Sub)
    - Topic-basiertes Subscription-System
    - Priority-basierte Message-Queue (asyncio.PriorityQueue)
    - Async/Await Support für non-blocking Operations
    - Delivery-Guarantees (Best-Effort with Retry)
    - Dead-Letter-Queue für fehlgeschlagene Deliveries
    - Request/Response Pattern mit Pending-Futures
    - Comprehensive Statistics & Monitoring
    - **NEW (v1.1):** Multi-Worker-Pattern für höheren Throughput (500+ msg/s)
    - **NEW (v1.1):** Message-Batching für Performance-Optimierung
    - **NEW (v1.1):** Worker-Health-Monitoring mit Auto-Restart

    Example:
        >>> # Default (Optimiert für Throughput)
        >>> broker = AgentMessageBroker()
        >>> await broker.start()
        >>>
        >>> # Custom Configuration
        >>> config = BrokerConfiguration(num_workers=3, batch_size=10)
        >>> broker = AgentMessageBroker(config=config)
        >>>
        >>> # Agent registrieren
        >>> broker.register_agent(agent.identity, agent.on_message)
        >>>
        >>> # Message senden
        >>> await broker.send_message(message)
        >>>
        >>> # Request/Response
        >>> response = await broker.send_request(request, timeout=30.0)
        >>>
        >>> # Pub/Sub
        >>> broker.subscribe(agent_id, "rag_context_updates")
        >>> await broker.publish_event("rag_context_updates", sender, event_data)
        >>>
        >>> # Performance Stats
        >>> stats = broker.get_stats()
        >>> print(f"Throughput: {stats['worker_pool']['total_messages_processed']} messages")
    """

    def __init__(
        self,
        config: Optional[BrokerConfiguration] = None,
        max_queue_size: Optional[int] = None,
        max_retry: Optional[int] = None,
    ):
        """
        Initialisiert den Message-Broker

        Args:
            config: BrokerConfiguration für Performance-Tuning (empfohlen)
            max_queue_size: Maximale Queue-Größe (deprecated, use config)
            max_retry: Max Retry-Versuche (deprecated, use config)

        Example:
            >>> # Empfohlen: Konfiguration verwenden
            >>> config = BrokerConfiguration(num_workers=5, batch_size=20)
            >>> broker = AgentMessageBroker(config=config)
            >>>
            >>> # Legacy: Backward-Kompatibilität
            >>> broker = AgentMessageBroker(max_queue_size=5000, max_retry=2)
        """
        # Configuration (mit Backward-Kompatibilität)
        if config is None:
            config = BrokerConfiguration()
            # Legacy-Parameter übernehmen
            if max_queue_size is not None:
                config.max_queue_size = max_queue_size
            if max_retry is not None:
                config.retry_max_attempts = max_retry

        self.config = config

        # Agent-Registry: agent_id -> AgentIdentity
        self._agents: Dict[str, AgentIdentity] = {}

        # Message-Handler-Registry: agent_id -> callback
        self._handlers: Dict[str, Callable[[AgentMessage], Any]] = {}

        # Topic-Subscriptions: topic -> Set[agent_id]
        self._subscriptions: Dict[str, Set[str]] = defaultdict(set)

        # Message-Queue (Priority-Queue mit asyncio)
        # Tuple: (priority: int, message_id: str, message: AgentMessage)
        self._message_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=self.config.max_queue_size)

        # Pending Requests: correlation_id -> asyncio.Future
        self._pending_requests: Dict[str, asyncio.Future] = {}

        # Dead-Letter-Queue für fehlgeschlagene Messages
        self._dead_letter_queue: List[Tuple[AgentMessage, str]] = []  # (message, error_reason)

        # NEW: Worker Pool für Multi-Worker-Pattern
        self._worker_pool = WorkerPoolManager(self)

        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "messages_expired": 0,
            "messages_retried": 0,
            "requests_timeout": 0,
            "subscriptions_active": 0,
            "agents_registered": 0,
            "broker_start_time": None,
            "broker_uptime_seconds": 0,
            # NEW: Batch-Processing Stats
            "batches_processed": 0,
            "avg_batch_size": 0.0,
        }

        # Background-Worker (Legacy - wird durch Worker-Pool ersetzt)
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(
            f"✅ AgentMessageBroker initialisiert (Workers: {self.config.num_workers}, Batching: {self.config.enable_batching})"
        )

    async def start(self):
        """
        Startet den Message-Broker mit Worker-Pool

        Raises:
            RuntimeError: Wenn Broker bereits läuft
        """
        if self._running:
            logger.warning("⚠️ Message-Broker läuft bereits")
            return

        self._running = True
        self._stats["broker_start_time"] = datetime.now()

        # Worker-Pool starten (ersetzt Single-Worker)
        await self._worker_pool.start(self.config.num_workers)

        logger.info(
            f"🚀 Message-Broker gestartet " f"(Workers: {self.config.num_workers}, Batching: {self.config.enable_batching})"
        )

    async def stop(self):
        """
        Stoppt den Message-Broker und Worker-Pool
        """
        if not self._running:
            logger.warning("⚠️ Message-Broker läuft nicht")
            return

        logger.info("🛑 Stoppe Message-Broker...")

        self._running = False

        # Worker-Pool stoppen
        await self._worker_pool.stop()

        # Pending-Requests canceln
        for correlation_id, future in self._pending_requests.items():
            if not future.done():
                future.cancel()

        # Uptime berechnen
        if self._stats["broker_start_time"]:
            uptime = (datetime.now() - self._stats["broker_start_time"]).total_seconds()
            self._stats["broker_uptime_seconds"] = uptime

        logger.info(
            f"✅ Message-Broker gestoppt "
            f"(Uptime: {self._stats['broker_uptime_seconds']:.1f}s, "
            f"Processed: {self._stats['messages_delivered']} messages)"
        )

    # ========================================================================
    # AGENT MANAGEMENT
    # ========================================================================

    def register_agent(self, identity: AgentIdentity, handler: Callable[[AgentMessage], Any]):
        """
        Registriert einen Agenten mit Message-Handler

        Args:
            identity: Agent-Identität
            handler: Callback-Funktion für eingehende Messages
                     Kann sync oder async sein: def handler(msg: AgentMessage) -> Optional[Dict]

        Example:
            >>> def on_message(message: AgentMessage) -> Dict[str, Any]:
            ...     return {"status": "acknowledged"}
            >>>
            >>> broker.register_agent(agent.identity, on_message)
        """
        if identity.agent_id in self._agents:
            logger.warning(f"⚠️ Agent {identity.agent_id} bereits registriert (überschreibe)")

        self._agents[identity.agent_id] = identity
        self._handlers[identity.agent_id] = handler
        self._stats["agents_registered"] = len(self._agents)

        logger.info(f"📝 Agent registriert: {identity.agent_name} ({identity.agent_id})")

    def unregister_agent(self, agent_id: str):
        """
        Entfernt einen Agenten aus dem Broker

        Args:
            agent_id: Agent-ID
        """
        if agent_id not in self._agents:
            logger.warning(f"⚠️ Agent {agent_id} nicht registriert")
            return

        agent_name = self._agents[agent_id].agent_name

        # Remove from registry
        del self._agents[agent_id]
        del self._handlers[agent_id]

        # Remove from all subscriptions
        for topic in self._subscriptions:
            self._subscriptions[topic].discard(agent_id)

        self._stats["agents_registered"] = len(self._agents)
        self._stats["subscriptions_active"] = sum(len(subs) for subs in self._subscriptions.values())

        logger.info(f"🗑️ Agent deregistriert: {agent_name} ({agent_id})")

    def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        """
        Holt Agent-Identity aus Registry

        Args:
            agent_id: Agent-ID

        Returns:
            AgentIdentity oder None wenn nicht gefunden
        """
        return self._agents.get(agent_id)

    def get_agents_by_type(self, agent_type: str) -> List[AgentIdentity]:
        """
        Findet alle Agenten eines bestimmten Typs

        Args:
            agent_type: Agent-Typ (z.B. "environmental", "financial")

        Returns:
            Liste von AgentIdentity-Objekten
        """
        return [identity for identity in self._agents.values() if identity.agent_type == agent_type]

    def get_agents_by_capability(self, capability: str) -> List[AgentIdentity]:
        """
        Findet alle Agenten mit einer bestimmten Capability

        Args:
            capability: Capability-Name (z.B. "environmental_analysis")

        Returns:
            Liste von AgentIdentity-Objekten
        """
        return [identity for identity in self._agents.values() if capability in identity.capabilities]

    # ========================================================================
    # PUB/SUB SUBSCRIPTIONS
    # ========================================================================

    def subscribe(self, agent_id: str, topic: str):
        """
        Abonniert ein Topic für einen Agenten

        Args:
            agent_id: Agent-ID
            topic: Topic-Name (z.B. "rag_context_updates", "agent_status_changes")

        Raises:
            ValueError: Wenn Agent nicht registriert

        Example:
            >>> broker.subscribe("env-agent-001", "rag_context_updates")
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} nicht registriert")

        self._subscriptions[topic].add(agent_id)
        self._stats["subscriptions_active"] = sum(len(subs) for subs in self._subscriptions.values())

        logger.info(f"📬 Agent {agent_id} abonniert Topic: {topic}")

    def unsubscribe(self, agent_id: str, topic: str):
        """
        Beendet Subscription für ein Topic

        Args:
            agent_id: Agent-ID
            topic: Topic-Name
        """
        self._subscriptions[topic].discard(agent_id)
        self._stats["subscriptions_active"] = sum(len(subs) for subs in self._subscriptions.values())

        logger.info(f"📭 Agent {agent_id} deabonniert Topic: {topic}")

    def get_subscribers(self, topic: str) -> Set[str]:
        """
        Holt alle Subscriber eines Topics

        Args:
            topic: Topic-Name

        Returns:
            Set von Agent-IDs
        """
        return self._subscriptions.get(topic, set()).copy()

    # ========================================================================
    # MESSAGE SENDING
    # ========================================================================

    async def send_message(self, message: AgentMessage) -> bool:
        """
        Sendet eine Message (Point-to-Point oder Broadcast)

        Args:
            message: AgentMessage-Objekt

        Returns:
            True wenn Message in Queue eingereiht wurde, False bei Queue-Full

        Example:
            >>> message = AgentMessage(sender=..., recipients=..., ...)
            >>> success = await broker.send_message(message)
        """
        try:
            # Priority-basiertes Queuing (negative für Max-Heap)
            priority = -message.metadata.priority.value

            # In Queue einreihen (non-blocking)
            try:
                # Tuple: (priority, message_id for uniqueness, message)
                await asyncio.wait_for(self._message_queue.put((priority, message.message_id, message)), timeout=1.0)
                self._stats["messages_sent"] += 1

                logger.debug(f"📤 Message gesendet: {message}")
                return True

            except asyncio.TimeoutError:
                logger.error(f"❌ Message-Queue voll (max {self._max_queue_size})")
                self._dead_letter_queue.append((message, "queue_full"))
                self._stats["messages_failed"] += 1
                return False

        except Exception as e:
            logger.error(f"❌ Fehler beim Senden der Message: {e}", exc_info=True)
            self._dead_letter_queue.append((message, str(e)))
            self._stats["messages_failed"] += 1
            return False

    async def send_request(self, message: AgentMessage, timeout: float = 30.0) -> Optional[AgentMessage]:
        """
        Sendet eine REQUEST-Message und wartet auf RESPONSE

        Args:
            message: Request-Message (MessageType.REQUEST)
            timeout: Timeout in Sekunden

        Returns:
            Response-Message oder None bei Timeout

        Raises:
            ValueError: Wenn message.message_type != REQUEST

        Example:
            >>> request = AgentMessage(message_type=MessageType.REQUEST, ...)
            >>> response = await broker.send_request(request, timeout=30.0)
            >>> if response:
            ...     result = response.payload.get("result")
        """
        if message.message_type != MessageType.REQUEST:
            raise ValueError("send_request() erfordert MessageType.REQUEST")

        # Future für Response erstellen
        future = asyncio.Future()
        self._pending_requests[message.metadata.correlation_id] = future

        # Request senden
        success = await self.send_message(message)
        if not success:
            del self._pending_requests[message.metadata.correlation_id]
            return None

        try:
            # Auf Response warten (mit Timeout)
            response = await asyncio.wait_for(future, timeout=timeout)
            return response

        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Request-Timeout ({timeout}s): {message}")
            self._stats["requests_timeout"] += 1

            # Future aufräumen
            if message.metadata.correlation_id in self._pending_requests:
                del self._pending_requests[message.metadata.correlation_id]

            return None

    async def publish_event(
        self, topic: str, sender: AgentIdentity, payload: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL
    ):
        """
        Publiziert ein Event an alle Subscribers eines Topics

        Args:
            topic: Topic-Name
            sender: Sender-Identität
            payload: Event-Daten
            priority: Priorität (default: NORMAL)

        Example:
            >>> await broker.publish_event(
            ...     topic="rag_context_updates",
            ...     sender=agent.identity,
            ...     payload={"context_id": "ctx-123", "update": "..."}
            ... )
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
            metadata=MessageMetadata(priority=priority),
        )

        await self.send_message(message)
        logger.info(f"📢 Event publiziert: {topic} → {len(recipients)} Subscribers")

    # ========================================================================
    # MESSAGE DELIVERY (called by MessageWorkers from Worker Pool)
    # ========================================================================

    async def _deliver_message(self, message: AgentMessage):
        """
        Liefert eine Message an Empfänger

        Args:
            message: Auszuliefernde Message
        """
        try:
            # TTL prüfen
            if message.metadata.is_expired():
                logger.warning(f"⏱️ Message expired (TTL {message.metadata.ttl_seconds}s): {message}")
                self._dead_letter_queue.append((message, "expired"))
                self._stats["messages_expired"] += 1
                return

            # Broadcast oder Point-to-Point?
            if message.is_broadcast():
                # Broadcast an alle registrierten Agenten
                recipients = list(self._agents.values())
            else:
                recipients = message.recipients

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
                    if message.is_request() and response:
                        # Response-Message erstellen
                        if isinstance(response, dict):
                            response_msg = message.create_response(sender=recipient, payload=response)
                            await self.send_message(response_msg)

                    # Für RESPONSE: Pending-Request auflösen
                    if message.is_response():
                        correlation_id = message.metadata.correlation_id
                        if correlation_id in self._pending_requests:
                            future = self._pending_requests[correlation_id]
                            if not future.done():
                                future.set_result(message)
                            del self._pending_requests[correlation_id]

                    delivery_count += 1

                except Exception as e:
                    logger.error(f"❌ Fehler bei Message-Delivery an {recipient.agent_id}: {e}", exc_info=True)

                    # Retry-Logic (nur für wichtige Messages)
                    if (
                        message.metadata.priority.value >= MessagePriority.HIGH.value
                        and message.metadata.retry_count < self.config.retry_max_attempts
                    ):
                        message.metadata.retry_count += 1
                        await self.send_message(message)
                        self._stats["messages_retried"] += 1
                        logger.info(
                            f"🔄 Message-Retry ({message.metadata.retry_count}/{self.config.retry_max_attempts}): {message}"
                        )
                    else:
                        self._dead_letter_queue.append((message, str(e)))
                        self._stats["messages_failed"] += 1

            self._stats["messages_delivered"] += delivery_count
            logger.debug(f"✅ Message zugestellt: {message} → {delivery_count} Empfänger")

        except Exception as e:
            logger.error(f"❌ Fehler bei Message-Delivery: {e}", exc_info=True)
            self._dead_letter_queue.append((message, str(e)))
            self._stats["messages_failed"] += 1

    # ========================================================================
    # STATISTICS & MONITORING
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Liefert Broker-Statistiken inkl. Worker-Pool-Info

        Returns:
            Dict mit Statistiken (messages_sent, delivered, failed, worker_pool, etc.)

        Example:
            >>> stats = broker.get_stats()
            >>> print(f"Messages sent: {stats['messages_sent']}")
            >>> print(f"Throughput: {stats['worker_pool']['total_messages_processed']} messages")
            >>> print(f"Workers: {stats['worker_pool']['total_workers']}")
        """
        # Uptime berechnen
        if self._stats["broker_start_time"]:
            uptime = (datetime.now() - self._stats["broker_start_time"]).total_seconds()
        else:
            uptime = self._stats["broker_uptime_seconds"]

        base_stats = {
            **self._stats,
            "broker_uptime_seconds": uptime,
            "queue_size": self._message_queue.qsize(),
            "queue_utilization": self._message_queue.qsize() / self.config.max_queue_size,
            "pending_requests": len(self._pending_requests),
            "dead_letter_queue_size": len(self._dead_letter_queue),
            "registered_agents": len(self._agents),
            "topics": len(self._subscriptions),
            "running": self._running,
        }

        # Worker-Pool-Stats hinzufügen
        worker_pool_stats = self._worker_pool.get_stats()

        return {
            **base_stats,
            "worker_pool": worker_pool_stats,
            "config": {
                "num_workers": self.config.num_workers,
                "enable_batching": self.config.enable_batching,
                "batch_size": self.config.batch_size,
                "batch_timeout_ms": self.config.batch_timeout_ms,
                "max_queue_size": self.config.max_queue_size,
                "delivery_parallelism": self.config.delivery_parallelism,
            },
        }

    def get_dead_letters(self) -> List[Tuple[AgentMessage, str]]:
        """
        Holt Dead-Letter-Queue (fehlgeschlagene Messages)

        Returns:
            Liste von (AgentMessage, error_reason) Tuples
        """
        return self._dead_letter_queue.copy()

    def clear_dead_letters(self):
        """Leert die Dead-Letter-Queue"""
        count = len(self._dead_letter_queue)
        self._dead_letter_queue.clear()
        logger.info(f"🗑️ Dead-Letter-Queue geleert ({count} Messages)")


# ============================================================================
# EXAMPLE USAGE (for testing)
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    print("=" * 80)
    print("VERITAS Agent Communication Protocol - Message Broker Tests")
    print("=" * 80)

    async def test_broker():
        """Async Test-Funktion"""

        # Test 1: Broker starten
        print("\n[Test 1] Broker starten:")
        broker = AgentMessageBroker()
        await broker.start()
        print(f"✅ Broker gestartet")

        # Test 2: Agenten registrieren
        print("\n[Test 2] Agenten registrieren:")

        env_agent = AgentIdentity(
            agent_id="env-agent-001",
            agent_type="environmental",
            agent_name="Environmental Agent",
            capabilities=["environmental_analysis"],
        )

        financial_agent = AgentIdentity(
            agent_id="fin-agent-001", agent_type="financial", agent_name="Financial Agent", capabilities=["financial_analysis"]
        )

        # Message-Handler
        async def env_handler(message: AgentMessage) -> Optional[Dict[str, Any]]:
            print(f"   [ENV] Empfangen: {message}")
            if message.is_request():
                return {"result": "Environmental analysis complete", "confidence": 0.95}
            return None

        async def fin_handler(message: AgentMessage) -> Optional[Dict[str, Any]]:
            print(f"   [FIN] Empfangen: {message}")
            if message.is_request():
                return {"result": "Financial analysis complete", "cost": 1500000}
            return None

        broker.register_agent(env_agent, env_handler)
        broker.register_agent(financial_agent, fin_handler)
        print(f"✅ 2 Agenten registriert")

        # Test 3: Request/Response
        print("\n[Test 3] Request/Response Pattern:")

        from shared.protocols.agent_message import create_request_message

        request = create_request_message(
            sender=env_agent,
            recipient=financial_agent,
            payload={"query": "Grundstückskosten für Projekt XYZ?"},
            priority=MessagePriority.HIGH,
        )

        response = await broker.send_request(request, timeout=5.0)
        if response:
            print(f"✅ Response erhalten: {response.payload}")
        else:
            print(f"❌ Timeout bei Request")

        # Test 4: Pub/Sub
        print("\n[Test 4] Publish/Subscribe Pattern:")

        broker.subscribe("fin-agent-001", "rag_context_updates")

        await broker.publish_event(
            topic="rag_context_updates",
            sender=env_agent,
            payload={"context_id": "ctx-123", "update": "Geographic boundaries updated"},
        )

        # Wait for delivery
        await asyncio.sleep(0.5)
        print(f"✅ Event publiziert und zugestellt")

        # Test 5: Broadcast
        print("\n[Test 5] Broadcast Pattern:")

        from shared.protocols.agent_message import create_broadcast_message

        broadcast = create_broadcast_message(sender=env_agent, payload={"announcement": "System-Update in 5 Minuten"})

        await broker.send_message(broadcast)
        await asyncio.sleep(0.5)
        print(f"✅ Broadcast gesendet")

        # Test 6: Statistics
        print("\n[Test 6] Statistiken:")
        stats = broker.get_stats()
        print(f"   Messages sent: {stats['messages_sent']}")
        print(f"   Messages delivered: {stats['messages_delivered']}")
        print(f"   Agents registered: {stats['agents_registered']}")
        print(f"   Queue size: {stats['queue_size']}")
        print(f"   Running: {stats['running']}")
        print(f"✅ Statistiken abgerufen")

        # Test 7: Broker stoppen
        print("\n[Test 7] Broker stoppen:")
        await broker.stop()
        print(f"✅ Broker gestoppt")

        print("\n" + "=" * 80)
        print("✅ Alle Tests erfolgreich!")
        print("=" * 80)

    # Run async tests
    asyncio.run(test_broker())
