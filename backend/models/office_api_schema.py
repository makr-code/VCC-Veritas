"""
VERITAS Office API Schema
==========================

Versioniertes JSON-Schema für Office Add-in Integration.
Request/Response mit Metadaten-Wrapper und embedded Markdown.

Version: 1.0
Author: VERITAS System
Date: 2025-11-01
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from .enums import QueryMode, SourceType

# ============================================================================
# Request Models
# ============================================================================


class OfficeRequestMetadata(BaseModel):
    """
    Metadata für Office Add-in Requests

    Enthält:
        - mode: ask|agent|edit|plan
        - scope: selection|document
        - host: word|excel|powerpoint|outlook
        - user_context: Selection-Info, Dokument-Name, etc.
    """

    mode: str = Field(default="ask", description="Query Mode: ask|agent|edit|plan")

    scope: str = Field(default="selection", description="Scope: selection|document")

    host: str = Field(default="word", description="Office Host: word|excel|powerpoint|outlook")

    user_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="User Context (selection_length, document_name, etc.)"
    )


class OfficeRequestContent(BaseModel):
    """
    Content-Payload für Office Add-in Requests

    Enthält:
        - query: User-Frage
        - context: Selection/Document-Text (Markdown)
        - history: Conversation History
    """

    query: str = Field(..., min_length=1, max_length=10000, description="User-Frage")

    context: Optional[str] = Field(None, description="Markdown-formatierter Kontext (Selection/Document)")

    history: Optional[List[Dict[str, str]]] = Field(
        default_factory=list, description="Conversation History [{'role': 'user|assistant', 'content': '...'}]"
    )


class OfficeAPIRequest(BaseModel):
    """
    🎯 Versionierter Request für Office Add-ins

    Struktur:
        - version: API-Version (1.0)
        - session_id: Session UUID
        - timestamp: ISO 8601
        - metadata: Mode, Scope, Host, Context
        - content: Query, Context, History

    Beispiel:
        {
            "version": "1.0",
            "session_id": "uuid - v4-string",
            "timestamp": "2025 - 11-01T14:30:00Z",
            "metadata": {
                "mode": "ask",
                "scope": "selection",
                "host": "word",
                "user_context": {"selection_length": 1234}
            },
            "content": {
                "query": "Was bedeutet BImSchG?",
                "context": "**Bundes - Immissionsschutzgesetz**...",
                "history": []
            }
        }
    """

    version: str = Field(default="1.0", description="API Version")

    session_id: Optional[str] = Field(None, description="Session ID (auto-generated if None)")

    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Request Timestamp (ISO 8601)")

    metadata: OfficeRequestMetadata = Field(
        default_factory=OfficeRequestMetadata, description="Request Metadata (Mode, Scope, Host)"
    )

    content: OfficeRequestContent = Field(..., description="Request Content (Query, Context, History)")

    @validator("version")
    def validate_version(cls, v):
        """Validate API version"""
        supported = ["1.0"]
        if v not in supported:
            raise ValueError(f"Unsupported API version: {v}. Supported: {supported}")
        return v


# ============================================================================
# Response Models
# ============================================================================


class OfficeResponseMetadata(BaseModel):
    """
    Metadata für Office Add-in Responses

    Enthält:
        - confidence_score: 0.0-1.0
        - processing_time_ms: Verarbeitungszeit
        - model: LLM Model (z.B. "llama3.2")
        - tokens_used: Token-Verbrauch
        - sources_count: Anzahl Quellen
    """

    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence Score")

    processing_time_ms: Optional[int] = Field(None, description="Processing Time (Millisekunden)")

    model: Optional[str] = Field(None, description="LLM Model (z.B. 'llama3.2')")

    tokens_used: Optional[int] = Field(None, description="Token Usage")

    sources_count: int = Field(0, description="Anzahl Quellen")


class OfficeCitation(BaseModel):
    """
    Citation für Office Add-in

    Vereinfacht, aber kompatibel mit IEEE-Standard.
    Mapping von UnifiedSourceMetadata.
    """

    document_id: str = Field(..., description="Document ID")

    document_title: str = Field(..., description="Document Title")

    excerpt: Optional[str] = Field(None, description="Text Excerpt")

    url: Optional[str] = Field(None, description="URL")

    page_number: Optional[int] = Field(None, description="Page Number")

    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance Score")


class OfficeResponseContent(BaseModel):
    """
    Content-Payload für Office Add-in Responses

    Enthält:
        - answer: Markdown-formatierte Antwort
        - format: "markdown"
        - citations: Quellen-Liste
        - suggestions: Optional Follow-up-Vorschläge
    """

    answer: str = Field(..., description="Markdown-formatierte Antwort mit [1], [2], [3] Citations")

    format: str = Field(default="markdown", description="Content Format (immer 'markdown')")

    citations: List[OfficeCitation] = Field(default_factory=list, description="Quellen-Liste")

    suggestions: Optional[List[str]] = Field(None, description="Follow-up Suggestions")


class OfficeResponseError(BaseModel):
    """
    Error-Info für Office Add-in Responses

    Enthält:
        - code: Error Code (z.B. "RATE_LIMIT")
        - message: Human-readable Message
        - retry_after_ms: Optional Retry-Delay
    """

    code: str = Field(..., description="Error Code")

    message: str = Field(..., description="Error Message")

    retry_after_ms: Optional[int] = Field(None, description="Retry After (Millisekunden)")


class OfficeAPIResponse(BaseModel):
    """
    🎯 Versionierte Response für Office Add-ins

    Struktur:
        - version: API-Version (1.0)
        - request_id: UUID des Requests
        - timestamp: ISO 8601
        - status: success|error|partial
        - metadata: Confidence, Processing Time, Model, etc.
        - content: Answer (Markdown), Citations, Suggestions
        - error: Optional Error-Info

    Beispiel:
        {
            "version": "1.0",
            "request_id": "uuid - v4-string",
            "timestamp": "2025 - 11-01T14:30:05Z",
            "status": "success",
            "metadata": {
                "confidence_score": 0.95,
                "processing_time_ms": 1234,
                "model": "llama3.2",
                "tokens_used": 500,
                "sources_count": 2
            },
            "content": {
                "answer": "# BImSchG\n\nDas **Bundes - Immissionsschutzgesetz** [1]...",
                "format": "markdown",
                "citations": [
                    {
                        "document_id": "doc123",
                        "document_title": "BImSchG",
                        "excerpt": "...",
                        "relevance_score": 0.92
                    }
                ],
                "suggestions": ["Möchten Sie mehr über Genehmigungsverfahren erfahren?"]
            },
            "error": null
        }
    """

    version: str = Field(default="1.0", description="API Version")

    request_id: str = Field(..., description="Request ID (UUID)")

    timestamp: datetime = Field(default_factory=datetime.now, description="Response Timestamp (ISO 8601)")

    status: str = Field(..., description="Status: success|error|partial")

    metadata: OfficeResponseMetadata = Field(default_factory=OfficeResponseMetadata, description="Response Metadata")

    content: Optional[OfficeResponseContent] = Field(None, description="Response Content (nur bei success/partial)")

    error: Optional[OfficeResponseError] = Field(None, description="Error Info (nur bei error)")

    @validator("status")
    def validate_status(cls, v):
        """Validate status"""
        allowed = ["success", "error", "partial"]
        if v not in allowed:
            raise ValueError(f"Invalid status: {v}. Allowed: {allowed}")
        return v


# ============================================================================
# Utility: Mapping UnifiedResponse → OfficeAPIResponse
# ============================================================================


def map_unified_to_office_response(
    unified_response, request_id: str, status: str = "success"  # UnifiedResponse
) -> OfficeAPIResponse:
    """
    Mapper: UnifiedResponse → OfficeAPIResponse

    Args:
        unified_response: UnifiedResponse vom Backend
        request_id: Request UUID
        status: success|error|partial

    Returns:
        OfficeAPIResponse
    """

    # Map Metadata
    metadata = OfficeResponseMetadata(
        confidence_score=unified_response.metadata.confidence,
        processing_time_ms=int(unified_response.metadata.duration * 1000),
        model=unified_response.metadata.model,
        tokens_used=unified_response.metadata.tokens_used,
        sources_count=len(unified_response.sources),
    )

    # Map Citations
    citations = []
    for src in unified_response.sources:
        citations.append(
            OfficeCitation(
                document_id=src.id,
                document_title=src.title,
                excerpt=src.excerpt,
                url=src.url,
                page_number=src.page,
                relevance_score=src.similarity_score or src.score,
            )
        )

    # Map Content
    content = OfficeResponseContent(
        answer=unified_response.content,
        format="markdown",
        citations=citations,
        suggestions=None,  # TODO: extract from processing_details if available
    )

    # Build Response
    return OfficeAPIResponse(
        version="1.0",
        request_id=request_id,
        timestamp=unified_response.timestamp,
        status=status,
        metadata=metadata,
        content=content,
        error=None,
    )
