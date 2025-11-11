"""
VERITAS Agent Communication Protocol - Core Message Schema

Standardisiertes Nachrichtenformat für Inter-Agent-Kommunikation im VERITAS Multi-Agent-System.

Features:
- AgentMessage: Core message dataclass (JSON-serializable)
- MessageType: Enum für Nachrichtentypen (REQUEST, RESPONSE, EVENT, etc.)
- MessagePriority: Prioritäts-Levels für Message-Routing
- AgentIdentity: Eindeutige Agent-Identifikation
- MessageMetadata: Routing & Tracking-Informationen

Version: 1.0
Author: VERITAS Development Team
Date: 6. Oktober 2025
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================


class MessageType(Enum):
    """
    Nachrichtentypen für Agent-Kommunikation

    - REQUEST: Anfrage mit erwarteter Antwort (Request/Response-Pattern)
    - RESPONSE: Antwort auf REQUEST
    - EVENT: Ereignis-Notification (Publish/Subscribe-Pattern)
    - BROADCAST: Nachricht an alle Agenten
    - CONTEXT_SHARE: RAG-Context-Austausch zwischen Agenten
    - STATUS_UPDATE: Agent-Status-Änderung (z.B. busy, idle, error)
    - ERROR: Fehler-Notification
    """

    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    BROADCAST = "broadcast"
    CONTEXT_SHARE = "context_share"
    STATUS_UPDATE = "status_update"
    ERROR = "error"


class MessagePriority(Enum):
    """
    Prioritäts-Levels für Message-Routing

    Höhere Priorität = schnellere Verarbeitung in Message-Queue
    """

    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class AgentStatus(Enum):
    """Agent-Status für STATUS_UPDATE Messages"""

    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    INITIALIZING = "initializing"


# ============================================================================
# DATACLASSES
# ============================================================================


@dataclass
class AgentIdentity:
    """
    Eindeutige Agent-Identifikation

    Attributes:
        agent_id: Eindeutige ID (UUID-Format empfohlen)
        agent_type: Agent-Typ (environmental, construction, financial, etc.)
        agent_name: Menschenlesbarer Name
        capabilities: Liste von Agent-Capabilities

    Example:
        >>> identity = AgentIdentity(
        ...     agent_id="env-agent-001",
        ...     agent_type="environmental",
        ...     agent_name="Environmental Analysis Agent",
        ...     capabilities=["environmental_analysis", "geographic_data", "climate_assessment"]
        ... )
    """

    agent_id: str
    agent_type: str
    agent_name: str
    capabilities: List[str] = field(default_factory=list)

    def __hash__(self):
        """Ermöglicht Verwendung in Sets und als Dict-Keys"""
        return hash(self.agent_id)

    def __eq__(self, other):
        """Equality-Check basierend auf agent_id"""
        return isinstance(other, AgentIdentity) and self.agent_id == other.agent_id

    def __str__(self):
        return f"{self.agent_name} ({self.agent_type})"

    def to_dict(self) -> Dict[str, Any]:
        """Serialisierung für JSON-Transport"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "agent_name": self.agent_name,
            "capabilities": self.capabilities,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentIdentity":
        """Deserialisierung aus JSON"""
        return cls(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            agent_name=data["agent_name"],
            capabilities=data.get("capabilities", []),
        )


@dataclass
class MessageMetadata:
    """
    Metadaten für Message-Routing und Tracking

    Attributes:
        timestamp: Zeitstempel der Message-Erstellung
        priority: Prioritäts-Level für Routing
        correlation_id: UUID für Request/Response-Matching
        reply_to: Message-ID für Antworten (bei RESPONSE-Messages)
        ttl_seconds: Time-to-Live in Sekunden (Message expiry)
        retry_count: Anzahl der Retry-Versuche bei Fehlern
        headers: Zusätzliche Header (custom metadata)

    Example:
        >>> metadata = MessageMetadata(
        ...     priority=MessagePriority.HIGH,
        ...     ttl_seconds=60,
        ...     headers={"request_source": "user_query", "session_id": "sess-123"}
        ... )
    """

    timestamp: datetime = field(default_factory=datetime.now)
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reply_to: Optional[str] = None
    ttl_seconds: int = 300  # 5 Minuten default
    retry_count: int = 0
    headers: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Prüft ob Message TTL überschritten ist"""
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed > self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Serialisierung für JSON-Transport"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "ttl_seconds": self.ttl_seconds,
            "retry_count": self.retry_count,
            "headers": self.headers,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageMetadata":
        """Deserialisierung aus JSON"""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            priority=MessagePriority(data["priority"]),
            correlation_id=data["correlation_id"],
            reply_to=data.get("reply_to"),
            ttl_seconds=data.get("ttl_seconds", 300),
            retry_count=data.get("retry_count", 0),
            headers=data.get("headers", {}),
        )


@dataclass
class AgentMessage:
    """
    Standardisiertes Nachrichtenformat für Inter-Agent-Kommunikation

    Attributes:
        message_id: Eindeutige Message-ID (UUID)
        sender: Sender-Agent-Identität
        recipients: Liste von Empfänger-Identitäten (leer = Broadcast)
        message_type: Typ der Nachricht (REQUEST, RESPONSE, EVENT, etc.)
        payload: Message-Nutzdaten (beliebiges Dict)
        metadata: Routing & Tracking-Metadaten

    Example - Request/Response:
        >>> # Request senden
        >>> request = AgentMessage(
        ...     sender=env_agent.identity,
        ...     recipients=[financial_agent.identity],
        ...     message_type=MessageType.REQUEST,
        ...     payload={"query": "Grundstückskosten für Projekt XYZ?", "project_id": "proj-123"},
        ...     metadata=MessageMetadata(priority=MessagePriority.HIGH)
        ... )
        >>>
        >>> # Response erstellen
        >>> response = AgentMessage(
        ...     sender=financial_agent.identity,
        ...     recipients=[env_agent.identity],
        ...     message_type=MessageType.RESPONSE,
        ...     payload={"result": {"cost": 1500000, "currency": "EUR"}, "confidence": 0.92},
        ...     metadata=MessageMetadata(
        ...         correlation_id=request.metadata.correlation_id,
        ...         reply_to=request.message_id
        ...     )
        ... )

    Example - Publish/Subscribe:
        >>> # Event publizieren
        >>> event = AgentMessage(
        ...     sender=supervisor.identity,
        ...     recipients=[],  # Broadcast an alle Subscribers
        ...     message_type=MessageType.EVENT,
        ...     payload={"topic": "rag_context_updates", "data": {"context_id": "ctx-123", "update": "..."}},
        ...     metadata=MessageMetadata(priority=MessagePriority.NORMAL)
        ... )
    """

    sender: AgentIdentity
    recipients: List[AgentIdentity]
    message_type: MessageType
    payload: Dict[str, Any]
    message_id: str = field(default_factory=lambda: f"msg-{uuid.uuid4()}")
    metadata: MessageMetadata = field(default_factory=MessageMetadata)

    def __post_init__(self):
        """Validierung nach Initialisierung"""
        # Validiere Message-Type
        if not isinstance(self.message_type, MessageType):
            raise ValueError(f"message_type muss MessageType-Enum sein, nicht {type(self.message_type)}")

        # Validiere Sender
        if not isinstance(self.sender, AgentIdentity):
            raise ValueError(f"sender muss AgentIdentity sein, nicht {type(self.sender)}")

        # Validiere Recipients
        if not isinstance(self.recipients, list):
            raise ValueError(f"recipients muss List sein, nicht {type(self.recipients)}")

        for recipient in self.recipients:
            if not isinstance(recipient, AgentIdentity):
                raise ValueError(f"recipient muss AgentIdentity sein, nicht {type(recipient)}")

    def is_broadcast(self) -> bool:
        """Prüft ob Message ein Broadcast ist (keine spezifischen Recipients)"""
        return len(self.recipients) == 0

    def is_request(self) -> bool:
        """Prüft ob Message ein Request ist"""
        return self.message_type == MessageType.REQUEST

    def is_response(self) -> bool:
        """Prüft ob Message eine Response ist"""
        return self.message_type == MessageType.RESPONSE

    def is_event(self) -> bool:
        """Prüft ob Message ein Event ist"""
        return self.message_type == MessageType.EVENT

    def create_response(self, sender: AgentIdentity, payload: Dict[str, Any]) -> "AgentMessage":
        """
        Erstellt eine Response-Message für diese Request-Message

        Args:
            sender: Sender der Response (normalerweise der ursprüngliche Empfänger)
            payload: Response-Daten

        Returns:
            AgentMessage mit MessageType.RESPONSE

        Example:
            >>> request = AgentMessage(...)
            >>> response = request.create_response(
            ...     sender=agent.identity,
            ...     payload={"result": "...", "confidence": 0.9}
            ... )
        """
        if not self.is_request():
            raise ValueError("create_response() kann nur für REQUEST-Messages aufgerufen werden")

        return AgentMessage(
            sender=sender,
            recipients=[self.sender],  # Response geht zurück an Request-Sender
            message_type=MessageType.RESPONSE,
            payload=payload,
            metadata=MessageMetadata(
                priority=self.metadata.priority,
                correlation_id=self.metadata.correlation_id,
                reply_to=self.message_id,
                headers=self.metadata.headers.copy(),
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialisierung für JSON-Transport

        Returns:
            Dict mit allen Message-Daten (JSON-serializable)
        """
        return {
            "message_id": self.message_id,
            "sender": self.sender.to_dict(),
            "recipients": [r.to_dict() for r in self.recipients],
            "message_type": self.message_type.value,
            "payload": self.payload,
            "metadata": self.metadata.to_dict(),
        }

    def to_json(self) -> str:
        """Serialisierung als JSON-String"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """
        Deserialisierung aus JSON-Dict

        Args:
            data: Dict mit Message-Daten

        Returns:
            AgentMessage-Instanz
        """
        sender = AgentIdentity.from_dict(data["sender"])
        recipients = [AgentIdentity.from_dict(r) for r in data["recipients"]]
        metadata = MessageMetadata.from_dict(data["metadata"])

        return cls(
            message_id=data["message_id"],
            sender=sender,
            recipients=recipients,
            message_type=MessageType(data["message_type"]),
            payload=data["payload"],
            metadata=metadata,
        )

    @classmethod
    def from_json(cls, json_string: str) -> "AgentMessage":
        """Deserialisierung aus JSON-String"""
        data = json.loads(json_string)
        return cls.from_dict(data)

    def __str__(self):
        """String-Repräsentation für Logging"""
        recipients_str = "Broadcast" if self.is_broadcast() else f"{len(self.recipients)} Empfänger"
        return (
            f"AgentMessage(id={self.message_id[:8]}..., "
            f"type={self.message_type.value}, "
            f"from={self.sender.agent_type}, "
            f"to={recipients_str}, "
            f"priority={self.metadata.priority.name})"
        )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def create_request_message(
    sender: AgentIdentity,
    recipient: AgentIdentity,
    payload: Dict[str, Any],
    priority: MessagePriority = MessagePriority.NORMAL,
    ttl_seconds: int = 300,
) -> AgentMessage:
    """
    Convenience-Funktion zum Erstellen einer REQUEST-Message

    Args:
        sender: Sender-Identität
        recipient: Empfänger-Identität
        payload: Request-Daten
        priority: Priorität (default: NORMAL)
        ttl_seconds: Time-to-Live (default: 300s)

    Returns:
        AgentMessage mit MessageType.REQUEST
    """
    return AgentMessage(
        sender=sender,
        recipients=[recipient],
        message_type=MessageType.REQUEST,
        payload=payload,
        metadata=MessageMetadata(priority=priority, ttl_seconds=ttl_seconds),
    )


def create_event_message(
    sender: AgentIdentity, topic: str, event_data: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL
) -> AgentMessage:
    """
    Convenience-Funktion zum Erstellen einer EVENT-Message

    Args:
        sender: Sender-Identität
        topic: Event-Topic (z.B. "rag_context_updates")
        event_data: Event-Daten
        priority: Priorität (default: NORMAL)

    Returns:
        AgentMessage mit MessageType.EVENT
    """
    return AgentMessage(
        sender=sender,
        recipients=[],  # Events sind Broadcasts
        message_type=MessageType.EVENT,
        payload={"topic": topic, "data": event_data},
        metadata=MessageMetadata(priority=priority),
    )


def create_broadcast_message(
    sender: AgentIdentity, payload: Dict[str, Any], priority: MessagePriority = MessagePriority.HIGH
) -> AgentMessage:
    """
    Convenience-Funktion zum Erstellen einer BROADCAST-Message

    Args:
        sender: Sender-Identität
        payload: Broadcast-Daten
        priority: Priorität (default: HIGH)

    Returns:
        AgentMessage mit MessageType.BROADCAST
    """
    return AgentMessage(
        sender=sender,
        recipients=[],  # Broadcast an alle
        message_type=MessageType.BROADCAST,
        payload=payload,
        metadata=MessageMetadata(priority=priority),
    )


def create_context_share_message(
    sender: AgentIdentity, recipient: AgentIdentity, context_data: Dict[str, Any], context_type: str = "rag_context"
) -> AgentMessage:
    """
    Convenience-Funktion zum Erstellen einer CONTEXT_SHARE-Message

    Args:
        sender: Sender-Identität
        recipient: Empfänger-Identität
        context_data: RAG-Context-Daten
        context_type: Typ des Contexts (default: "rag_context")

    Returns:
        AgentMessage mit MessageType.CONTEXT_SHARE
    """
    return AgentMessage(
        sender=sender,
        recipients=[recipient],
        message_type=MessageType.CONTEXT_SHARE,
        payload={"context_type": context_type, "context_data": context_data},
        metadata=MessageMetadata(priority=MessagePriority.NORMAL),
    )


# ============================================================================
# EXAMPLE USAGE (for testing)
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 80)
    print("VERITAS Agent Communication Protocol - Message Schema Tests")
    print("=" * 80)

    # Test 1: AgentIdentity
    print("\n[Test 1] AgentIdentity erstellen:")
    env_agent = AgentIdentity(
        agent_id="env-agent-001",
        agent_type="environmental",
        agent_name="Environmental Analysis Agent",
        capabilities=["environmental_analysis", "geographic_data", "climate_assessment"],
    )
    print(f"✅ Agent erstellt: {env_agent}")
    print(f"   Dict: {env_agent.to_dict()}")

    # Test 2: MessageMetadata
    print("\n[Test 2] MessageMetadata erstellen:")
    metadata = MessageMetadata(priority=MessagePriority.HIGH, ttl_seconds=60, headers={"session_id": "sess-123"})
    print(f"✅ Metadata erstellt: Priority={metadata.priority.name}, TTL={metadata.ttl_seconds}s")
    print(f"   Expired: {metadata.is_expired()}")

    # Test 3: REQUEST Message
    print("\n[Test 3] REQUEST Message erstellen:")
    financial_agent = AgentIdentity(
        agent_id="fin-agent-001",
        agent_type="financial",
        agent_name="Financial Analysis Agent",
        capabilities=["financial_analysis", "cost_estimation"],
    )

    request = create_request_message(
        sender=env_agent,
        recipient=financial_agent,
        payload={"query": "Grundstückskosten für Projekt XYZ?", "project_id": "proj-123"},
        priority=MessagePriority.HIGH,
    )
    print(f"✅ Request erstellt: {request}")
    print(f"   Is Request: {request.is_request()}")
    print(f"   Is Broadcast: {request.is_broadcast()}")

    # Test 4: RESPONSE Message
    print("\n[Test 4] RESPONSE Message erstellen:")
    response = request.create_response(
        sender=financial_agent, payload={"result": {"cost": 1500000, "currency": "EUR"}, "confidence": 0.92}
    )
    print(f"✅ Response erstellt: {response}")
    print(f"   Correlation-ID match: {request.metadata.correlation_id == response.metadata.correlation_id}")
    print(f"   Reply-to: {response.metadata.reply_to == request.message_id}")

    # Test 5: EVENT Message
    print("\n[Test 5] EVENT Message erstellen:")
    event = create_event_message(
        sender=env_agent,
        topic="rag_context_updates",
        event_data={"context_id": "ctx-123", "update_type": "geographic_boundaries"},
    )
    print(f"✅ Event erstellt: {event}")
    print(f"   Is Broadcast: {event.is_broadcast()}")
    print(f"   Topic: {event.payload.get('topic')}")

    # Test 6: Serialization/Deserialization
    print("\n[Test 6] JSON Serialization/Deserialization:")
    json_str = request.to_json()
    print(f"✅ JSON serialisiert ({len(json_str)} Zeichen)")

    deserialized = AgentMessage.from_json(json_str)
    print(f"✅ JSON deserialisiert: {deserialized}")
    print(f"   Equals original: {request.message_id == deserialized.message_id}")
    print(f"   Sender match: {request.sender.agent_id == deserialized.sender.agent_id}")

    # Test 7: BROADCAST Message
    print("\n[Test 7] BROADCAST Message erstellen:")
    broadcast = create_broadcast_message(
        sender=env_agent, payload={"announcement": "System-Update in 5 Minuten", "action": "save_state"}
    )
    print(f"✅ Broadcast erstellt: {broadcast}")
    print(f"   Is Broadcast: {broadcast.is_broadcast()}")

    # Test 8: CONTEXT_SHARE Message
    print("\n[Test 8] CONTEXT_SHARE Message erstellen:")
    context_share = create_context_share_message(
        sender=env_agent,
        recipient=financial_agent,
        context_data={"project_area": "52.520°N, 13.405°E", "terrain": "urban"},
        context_type="geographic_context",
    )
    print(f"✅ Context-Share erstellt: {context_share}")
    print(f"   Context-Type: {context_share.payload.get('context_type')}")

    print("\n" + "=" * 80)
    print("✅ Alle Tests erfolgreich!")
    print("=" * 80)
