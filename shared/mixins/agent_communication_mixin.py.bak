"""
VERITAS Agent Communication Protocol - Agent Communication Mixin

Mixin-Klasse zur Erweiterung von Agenten mit Message-basierter Kommunikation.

Features:
- Message-Senden/Empfangen
- Request/Response-Handling
- Publish/Subscribe für Events
- Context-Sharing zwischen Agenten
- Automatic Broker-Registration
- Customizable Message-Handlers

Version: 1.0
Author: VERITAS Development Team
Date: 6. Oktober 2025
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.agents.agent_message_broker import AgentMessageBroker
    from shared.protocols.agent_message import (
        AgentIdentity,
        AgentMessage,
        MessagePriority,
        MessageType,
        create_broadcast_message,
        create_context_share_message,
        create_event_message,
        create_request_message,
    )
except ModuleNotFoundError:
    # Fallback für direkte Imports
    from agent_message_broker import AgentMessageBroker
    from protocols.agent_message import (
        AgentIdentity,
        AgentMessage,
        MessagePriority,
        MessageType,
        create_broadcast_message,
        create_context_share_message,
        create_event_message,
        create_request_message,
    )

logger = logging.getLogger(__name__)


class AgentCommunicationMixin:
    """
    Mixin für Agent-Klassen zur Aktivierung von Message-basierter Kommunikation

    Fügt Kommunikationsfähigkeiten zu bestehenden Agent-Klassen hinzu:
    - Message senden/empfangen
    - Request/Response Pattern
    - Publish/Subscribe für Events
    - Context-Sharing

    Usage:
        >>> class EnvironmentalAgent(AgentCommunicationMixin):
        ...     def __init__(self, broker: AgentMessageBroker):
        ...         identity = AgentIdentity(
        ...             agent_id="env-agent-1",
        ...             agent_type="environmental",
        ...             agent_name="Environmental Analysis Agent",
        ...             capabilities=["environmental_analysis", "geographic_data"]
        ...         )
        ...         super().__init__(broker, identity)
        ...
        ...         # Custom-Handler registrieren
        ...         self.register_message_handler(MessageType.REQUEST, self._handle_analysis_request)
        ...
        ...     async def _handle_analysis_request(self, message: AgentMessage) -> Dict[str, Any]:
        ...         # Custom Request-Handling
        ...         query = message.payload.get("query")
        ...         result = await self.analyze_environment(query)
        ...         return {"result": result, "confidence": 0.95}
    """

    def __init__(self, broker: AgentMessageBroker, identity: AgentIdentity):
        """
        Initialisiert Kommunikations-Mixin

        Args:
            broker: AgentMessageBroker-Instanz
            identity: Agent-Identität
        """
        self.broker = broker
        self.identity = identity
        self._message_handlers: Dict[MessageType, Callable] = {}

        # Bei Broker registrieren
        self.broker.register_agent(self.identity, self._on_message)

        # Standard-Handler registrieren
        self.register_message_handler(MessageType.REQUEST, self._handle_request)
        self.register_message_handler(MessageType.RESPONSE, self._handle_response)
        self.register_message_handler(MessageType.EVENT, self._handle_event)
        self.register_message_handler(MessageType.BROADCAST, self._handle_broadcast)
        self.register_message_handler(MessageType.CONTEXT_SHARE, self._handle_context_share)
        self.register_message_handler(MessageType.STATUS_UPDATE, self._handle_status_update)
        self.register_message_handler(MessageType.ERROR, self._handle_error)

        logger.info(f"🔌 Agent {self.identity.agent_name} mit Kommunikation initialisiert")

    # ========================================================================
    # MESSAGE HANDLER REGISTRATION
    # ========================================================================

    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """
        Registriert einen Handler für einen Message-Typ

        Args:
            message_type: MessageType-Enum
            handler: Callable mit Signatur: handler(message: AgentMessage) -> Optional[Dict[str, Any]]
                     Kann sync oder async sein

        Example:
            >>> async def custom_handler(message: AgentMessage) -> Dict[str, Any]:
            ...     return {"status": "processed"}
            >>>
            >>> agent.register_message_handler(MessageType.REQUEST, custom_handler)
        """
        self._message_handlers[message_type] = handler
        logger.debug(f"📋 Handler registriert für {message_type.value}")

    async def _on_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """
        Callback für eingehende Messages (wird vom Broker aufgerufen)

        Args:
            message: Eingehende Message

        Returns:
            Response-Payload (für REQUEST-Messages) oder None
        """
        handler = self._message_handlers.get(message.message_type)

        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    return await handler(message)
                else:
                    return handler(message)
            except Exception as e:
                logger.error(f"❌ Fehler in Message-Handler ({message.message_type.value}): {e}", exc_info=True)
                return {"error": str(e), "status": "failed"}
        else:
            logger.warning(f"⚠️ Kein Handler für Message-Typ {message.message_type.value}")
            return None

    # ========================================================================
    # MESSAGE SENDING
    # ========================================================================

    async def send_message(
        self,
        recipients: List[AgentIdentity],
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl_seconds: int = 300,
    ) -> bool:
        """
        Sendet eine Message an andere Agenten

        Args:
            recipients: Liste von Empfänger-Identitäten (leer = Broadcast)
            message_type: Typ der Message
            payload: Message-Daten
            priority: Priorität (default: NORMAL)
            ttl_seconds: Time-to-Live (default: 300s)

        Returns:
            True wenn erfolgreich in Queue eingereiht

        Example:
            >>> await agent.send_message(
            ...     recipients=[other_agent.identity],
            ...     message_type=MessageType.REQUEST,
            ...     payload={"query": "Grundstückskosten?"},
            ...     priority=MessagePriority.HIGH
            ... )
        """
        from shared.protocols.agent_message import MessageMetadata

        message = AgentMessage(
            sender=self.identity,
            recipients=recipients,
            message_type=message_type,
            payload=payload,
            metadata=MessageMetadata(priority=priority, ttl_seconds=ttl_seconds),
        )
        return await self.broker.send_message(message)

    async def send_request(
        self,
        recipient: AgentIdentity,
        payload: Dict[str, Any],
        timeout: float = 30.0,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> Optional[Dict[str, Any]]:
        """
        Sendet eine Request-Message und wartet auf Response

        Args:
            recipient: Empfänger-Identität
            payload: Request-Daten
            timeout: Timeout in Sekunden (default: 30s)
            priority: Priorität (default: NORMAL)

        Returns:
            Response-Payload oder None bei Timeout

        Example:
            >>> response = await agent.send_request(
            ...     recipient=financial_agent.identity,
            ...     payload={"query": "Baukosten für Projekt XYZ?"},
            ...     timeout=30.0
            ... )
            >>> if response:
            ...     cost = response.get("result", {}).get("cost")
        """
        message = create_request_message(sender=self.identity, recipient=recipient, payload=payload, priority=priority)
        response = await self.broker.send_request(message, timeout=timeout)
        return response.payload if response else None

    async def send_response(self, request_message: AgentMessage, payload: Dict[str, Any]) -> bool:
        """
        Sendet eine Response auf eine Request-Message

        Args:
            request_message: Ursprüngliche Request-Message
            payload: Response-Daten

        Returns:
            True wenn erfolgreich gesendet

        Example:
            >>> # In Custom-Handler
            >>> async def _handle_request(self, message: AgentMessage) -> Dict[str, Any]:
            ...     result = await self.process_query(message.payload["query"])
            ...     return {"result": result, "confidence": 0.92}
        """
        response = request_message.create_response(sender=self.identity, payload=payload)
        return await self.broker.send_message(response)

    async def publish_event(self, topic: str, payload: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL):
        """
        Publiziert ein Event an Topic-Subscribers

        Args:
            topic: Topic-Name (z.B. "rag_context_updates")
            payload: Event-Daten
            priority: Priorität (default: NORMAL)

        Example:
            >>> await agent.publish_event(
            ...     topic="rag_context_updates",
            ...     payload={"context_id": "ctx-123", "update": "Geographic data updated"}
            ... )
        """
        await self.broker.publish_event(topic, self.identity, payload, priority)

    async def send_broadcast(self, payload: Dict[str, Any], priority: MessagePriority = MessagePriority.HIGH):
        """
        Sendet Broadcast-Message an alle Agenten

        Args:
            payload: Broadcast-Daten
            priority: Priorität (default: HIGH)

        Example:
            >>> await agent.send_broadcast({
            ...     "announcement": "System-Update in 5 Minuten",
            ...     "action": "save_state"
            ... })
        """
        message = create_broadcast_message(sender=self.identity, payload=payload, priority=priority)
        await self.broker.send_message(message)

    async def share_context(self, recipient: AgentIdentity, context_data: Dict[str, Any], context_type: str = "rag_context"):
        """
        Teilt RAG-Context mit einem anderen Agenten

        Args:
            recipient: Empfänger-Identität
            context_data: Context-Daten
            context_type: Typ des Contexts (default: "rag_context")

        Example:
            >>> await env_agent.share_context(
            ...     recipient=construction_agent.identity,
            ...     context_data={"project_area": "52.520°N, 13.405°E", "terrain": "urban"},
            ...     context_type="geographic_context"
            ... )
        """
        message = create_context_share_message(
            sender=self.identity, recipient=recipient, context_data=context_data, context_type=context_type
        )
        await self.broker.send_message(message)

    # ========================================================================
    # SUBSCRIPTION MANAGEMENT
    # ========================================================================

    def subscribe(self, topic: str):
        """
        Abonniert ein Topic

        Args:
            topic: Topic-Name (z.B. "rag_context_updates")

        Example:
            >>> agent.subscribe("rag_context_updates")
        """
        self.broker.subscribe(self.identity.agent_id, topic)

    def unsubscribe(self, topic: str):
        """
        Beendet Subscription für ein Topic

        Args:
            topic: Topic-Name
        """
        self.broker.unsubscribe(self.identity.agent_id, topic)

    # ========================================================================
    # DEFAULT MESSAGE HANDLERS (können überschrieben werden)
    # ========================================================================

    async def _handle_request(self, message: AgentMessage) -> Dict[str, Any]:
        """
        Standard-Handler für REQUEST-Messages

        Override in Subclass für Custom-Handling:
            async def _handle_request(self, message: AgentMessage) -> Dict[str, Any]:
                result = await self.process_query(message.payload["query"])
                return {"result": result}
        """
        logger.info(f"📨 [{self.identity.agent_type}] Request erhalten: {message.payload}")
        return {
            "status": "acknowledged",
            "message": f"Request acknowledged by {self.identity.agent_name}",
            "message_id": message.message_id,
        }

    async def _handle_response(self, message: AgentMessage) -> None:
        """Standard-Handler für RESPONSE-Messages"""
        logger.info(f"📬 [{self.identity.agent_type}] Response erhalten: {message.payload}")

    async def _handle_event(self, message: AgentMessage) -> None:
        """Standard-Handler für EVENT-Messages"""
        topic = message.payload.get("topic", "unknown")
        logger.info(f"📢 [{self.identity.agent_type}] Event erhalten (Topic: {topic}): {message.payload.get('data')}")

    async def _handle_broadcast(self, message: AgentMessage) -> None:
        """Standard-Handler für BROADCAST-Messages"""
        logger.info(f"📣 [{self.identity.agent_type}] Broadcast erhalten: {message.payload}")

    async def _handle_context_share(self, message: AgentMessage) -> None:
        """Standard-Handler für CONTEXT_SHARE-Messages"""
        context_type = message.payload.get("context_type", "unknown")
        logger.info(f"🔄 [{self.identity.agent_type}] Context-Share erhalten (Type: {context_type})")

    async def _handle_status_update(self, message: AgentMessage) -> None:
        """Standard-Handler für STATUS_UPDATE-Messages"""
        logger.info(f"📊 [{self.identity.agent_type}] Status-Update erhalten: {message.payload}")

    async def _handle_error(self, message: AgentMessage) -> None:
        """Standard-Handler für ERROR-Messages"""
        logger.error(f"❌ [{self.identity.agent_type}] Error-Message erhalten: {message.payload}")

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_identity(self) -> AgentIdentity:
        """Liefert Agent-Identität"""
        return self.identity

    def is_registered(self) -> bool:
        """Prüft ob Agent beim Broker registriert ist"""
        return self.broker.get_agent(self.identity.agent_id) is not None

    def cleanup(self):
        """Räumt auf und deregistriert Agent vom Broker"""
        self.broker.unregister_agent(self.identity.agent_id)
        logger.info(f"🧹 Agent {self.identity.agent_name} cleanup durchgeführt")


# ============================================================================
# EXAMPLE AGENT IMPLEMENTATIONS
# ============================================================================


class ExampleEnvironmentalAgent(AgentCommunicationMixin):
    """
    Beispiel-Agent: Environmental Analysis Agent mit Message-Kommunikation
    """

    def __init__(self, broker: AgentMessageBroker):
        identity = AgentIdentity(
            agent_id="env-agent-example",
            agent_type="environmental",
            agent_name="Example Environmental Agent",
            capabilities=["environmental_analysis", "geographic_data", "climate_assessment"],
        )
        super().__init__(broker, identity)

        # Custom-Handler registrieren
        self.register_message_handler(MessageType.REQUEST, self._handle_analysis_request)

        # Topics abonnieren
        self.subscribe("rag_context_updates")
        self.subscribe("project_updates")

    async def _handle_analysis_request(self, message: AgentMessage) -> Dict[str, Any]:
        """Custom-Handler für Environmental-Analysis-Requests"""
        query = message.payload.get("query", "")
        project_id = message.payload.get("project_id", "unknown")

        logger.info(f"🌍 Environmental-Analyse für Projekt {project_id}: {query}")

        # Simulate analysis
        await asyncio.sleep(0.1)

        return {
            "result": {
                "project_id": project_id,
                "environmental_assessment": "Good",
                "terrain_type": "urban",
                "climate_zone": "temperate",
                "geographic_coordinates": "52.520°N, 13.405°E",
            },
            "confidence": 0.95,
            "agent": "environmental",
        }


class ExampleFinancialAgent(AgentCommunicationMixin):
    """
    Beispiel-Agent: Financial Analysis Agent mit Message-Kommunikation
    """

    def __init__(self, broker: AgentMessageBroker):
        identity = AgentIdentity(
            agent_id="fin-agent-example",
            agent_type="financial",
            agent_name="Example Financial Agent",
            capabilities=["financial_analysis", "cost_estimation", "budget_planning"],
        )
        super().__init__(broker, identity)

        # Custom-Handler registrieren
        self.register_message_handler(MessageType.REQUEST, self._handle_cost_request)

        # Topics abonnieren
        self.subscribe("rag_context_updates")

    async def _handle_cost_request(self, message: AgentMessage) -> Dict[str, Any]:
        """Custom-Handler für Cost-Estimation-Requests"""
        query = message.payload.get("query", "")
        project_id = message.payload.get("project_id", "unknown")

        logger.info(f"💰 Kostenanalyse für Projekt {project_id}: {query}")

        # Simulate analysis
        await asyncio.sleep(0.1)

        return {
            "result": {
                "project_id": project_id,
                "total_cost": 1500000,
                "currency": "EUR",
                "breakdown": {"land": 500000, "construction": 800000, "permits": 100000, "contingency": 100000},
            },
            "confidence": 0.92,
            "agent": "financial",
        }


# ============================================================================
# EXAMPLE USAGE (for testing)
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    print("=" * 80)
    print("VERITAS Agent Communication Protocol - Communication Mixin Tests")
    print("=" * 80)

    async def test_communication_mixin():
        """Async Test-Funktion"""

        # Test 1: Broker & Agents erstellen
        print("\n[Test 1] Broker & Agents erstellen:")
        broker = AgentMessageBroker()
        await broker.start()

        env_agent = ExampleEnvironmentalAgent(broker)
        fin_agent = ExampleFinancialAgent(broker)

        print(f"✅ Broker gestartet, 2 Agents erstellt")

        # Test 2: Request/Response zwischen Agents
        print("\n[Test 2] Request/Response Pattern (Env → Fin):")

        response = await env_agent.send_request(
            recipient=fin_agent.identity,
            payload={"query": "Grundstückskosten für Projekt XYZ?", "project_id": "proj-123"},
            timeout=5.0,
        )

        if response:
            print(f"✅ Response erhalten:")
            print(f"   Total Cost: {response.get('result', {}).get('total_cost')} EUR")
            print(f"   Confidence: {response.get('confidence')}")

        # Test 3: Context-Sharing
        print("\n[Test 3] Context-Sharing (Env → Fin):")

        await env_agent.share_context(
            recipient=fin_agent.identity,
            context_data={"project_area": "52.520°N, 13.405°E", "terrain_type": "urban", "soil_quality": "good"},
            context_type="geographic_context",
        )

        await asyncio.sleep(0.5)
        print(f"✅ Context geteilt")

        # Test 4: Pub/Sub Event
        print("\n[Test 4] Publish/Subscribe Event:")

        await env_agent.publish_event(
            topic="rag_context_updates", payload={"context_id": "ctx-123", "update": "Geographic boundaries updated"}
        )

        await asyncio.sleep(0.5)
        print(f"✅ Event publiziert")

        # Test 5: Broadcast
        print("\n[Test 5] Broadcast Message:")

        await env_agent.send_broadcast({"announcement": "System-Update in 5 Minuten", "action": "save_state"})

        await asyncio.sleep(0.5)
        print(f"✅ Broadcast gesendet")

        # Test 6: Statistics
        print("\n[Test 6] Broker-Statistiken:")
        stats = broker.get_stats()
        print(f"   Messages sent: {stats['messages_sent']}")
        print(f"   Messages delivered: {stats['messages_delivered']}")
        print(f"   Agents registered: {stats['agents_registered']}")
        print(f"✅ Statistiken abgerufen")

        # Test 7: Cleanup
        print("\n[Test 7] Cleanup:")
        env_agent.cleanup()
        fin_agent.cleanup()
        await broker.stop()
        print(f"✅ Cleanup durchgeführt")

        print("\n" + "=" * 80)
        print("✅ Alle Tests erfolgreich!")
        print("=" * 80)

    # Run async tests
    asyncio.run(test_communication_mixin())
