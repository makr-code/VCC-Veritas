"""
Universal JSON Payload Library
===============================
Standardisierte Payload-Strukturen für VERITAS-Kommunikation

Dieses Modul definiert einheitliche Request/Response-Formate für
die Kommunikation zwischen Frontend, Backend und verschiedenen Services.
"""

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# ===== ENUMS =====

class RequestType(Enum):
    """Typen von Anfragen"""
    QUERY = "query"
    CHAT = "chat"
    RAG = "rag"
    AGENT = "agent"
    STREAMING = "streaming"
    DOCUMENT = "document"
    ANALYSIS = "analysis"
    SEARCH = "search"

class ResponseStatus(Enum):
    """Status von Antworten"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    PENDING = "pending"
    TIMEOUT = "timeout"

class SystemComponent(Enum):
    """System-Komponenten"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    AGENT = "agent"
    DATABASE = "database"
    LLM = "llm"
    RAG = "rag"
    UDS3 = "uds3"
    VERITAS = "veritas"

class QualityLevel(Enum):
    """Qualitätsstufen"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    STANDARD = "standard"
    BEST_EFFORT = "best_effort"

# ===== DATACLASSES =====

@dataclass
class UniversalQueryRequest:
    """Standardisierte Query-Anfrage"""

    query: str
    # Backwards-compatible defaults so callers may omit request_id/request_type
    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:16]}")
    request_type: RequestType = RequestType.QUERY
    session_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    quality_level: QualityLevel = QualityLevel.MEDIUM
    max_tokens: int = 1000
    temperature: float = 0.7
    source_component: SystemComponent = SystemComponent.FRONTEND
    # Compatibility fields expected by older callers
    system_component: SystemComponent = SystemComponent.BACKEND
    system_prompt: Optional[str] = None
    context_files: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        data = asdict(self)
        # Enums zu Strings konvertieren
        data["request_type"] = self.request_type.value
        data["quality_level"] = self.quality_level.value
        data["source_component"] = self.source_component.value
        data["system_component"] = (
            self.system_component.value if isinstance(self.system_component, SystemComponent) else self.system_component
        )
        return data

    # Compatibility: some callers expect a `dict()` method (pydantic-like)
    def dict(self) -> Dict[str, Any]:
        return self.to_dict()


@dataclass
class UniversalQueryResponse:
    """Standardisierte Query-Antwort"""
    request_id: str
    response_id: str
    status: ResponseStatus
    answer: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    confidence_score: float = 0.0
    processing_time: float = 0.0
    tokens_used: int = 0
    suggestions: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    source_component: SystemComponent = SystemComponent.BACKEND
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['source_component'] = self.source_component.value
        return data

# ===== UTILITY FUNCTIONS =====

def create_request_id() -> str:
    """Generiert eine eindeutige Request-ID"""
    return f"req_{uuid.uuid4().hex[:16]}"

def create_session_id() -> str:
    """Generiert eine eindeutige Session-ID"""
    return f"session_{uuid.uuid4().hex[:16]}"

def create_response_id() -> str:
    """Generiert eine eindeutige Response-ID"""
    return f"resp_{uuid.uuid4().hex[:16]}"

def validate_request_type(request_type: str) -> bool:
    """Validiert Request-Typ"""
    try:
        RequestType(request_type)
        return True
    except ValueError:
        return False

# ===== FACTORY FUNCTIONS =====

def create_query_request(
    query: str,
    request_type: RequestType = RequestType.QUERY,
    session_id: Optional[str] = None,
    **kwargs
) -> UniversalQueryRequest:
    """Erstellt eine standardisierte Query-Anfrage"""
    return UniversalQueryRequest(
        request_id=create_request_id(),
        request_type=request_type,
        query=query,
        session_id=session_id or create_session_id(),
        **kwargs
    )

def create_query_response(
    request_id: str,
    answer: str,
    status: ResponseStatus = ResponseStatus.SUCCESS,
    **kwargs
) -> UniversalQueryResponse:
    """Erstellt eine standardisierte Query-Antwort"""
    return UniversalQueryResponse(
        request_id=request_id,
        response_id=create_response_id(),
        status=status,
        answer=answer,
        **kwargs
    )

    "create_request_id",
    "create_session_id",
    "create_response_id",
    "validate_request_type",
    "create_query_request",
    "create_query_response",
    "create_error_response",
    # Compatibility dataclasses
    "ChatMessageRequest",
    "FileUploadRequest",
    # Additional compatibility stubs
    "ChatMessageResponse",
    "FileProcessingResponse",
    "MetadataPayload",
    "ProcessingMetrics",
    "QualityMetrics",
    "SourceReference",
    "SecurityLevel",
    "create_metadata",
    "create_success_response",
    # Legacy
    'generate_request_id',
    'generate_session_id',
]


# ===== Compatibility stubs referenced by older backend modules =====


class SecurityLevel(Enum):
    """Compatibility enum for security levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class MetadataPayload:
    """Lightweight metadata payload used by older endpoints"""

    source: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[str] = None


@dataclass
class ProcessingMetrics:
    """Basic processing metrics placeholder"""

    processing_time: float = 0.0
    tokens_used: int = 0


@dataclass
class QualityMetrics:
    """Placeholder for quality metrics"""

    score: float = 0.0


@dataclass
class SourceReference:
    """Simple source reference used in legacy responses"""

    id: str = ""
    file: Optional[str] = None
    page: Optional[int] = None


@dataclass
class ChatMessageResponse:
    """Compatibility response for chat messages"""

    message_id: str
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileProcessingResponse:
    """Compatibility response for file processing endpoints"""

    file_id: str
    status: str
    metrics: ProcessingMetrics = field(default_factory=ProcessingMetrics)


def create_metadata(source: Optional[str] = None, author: Optional[str] = None) -> MetadataPayload:
    """Create a minimal metadata payload for legacy callers."""
    return MetadataPayload(source=source, author=author, published_at=datetime.now().isoformat())


def create_success_response(data: Optional[Dict[str, Any]] = None, message: str = "OK") -> Dict[str, Any]:
    """Return a minimal success response dict for compatibility."""
    return {"success": True, "message": message, "data": data or {}, "timestamp": datetime.now().isoformat()}
