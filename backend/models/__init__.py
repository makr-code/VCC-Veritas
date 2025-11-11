"""
VERITAS Backend Models
======================

Shared data models for requests, responses, and enums.
"""

from .enums import ImpactLevel, QueryComplexity, QueryDomain, QueryMode, RelevanceLevel, SourceType
from .request import AgentQueryRequest, StreamingQueryRequest, UnifiedQueryRequest
from .response import UnifiedResponse, UnifiedResponseMetadata, UnifiedSourceMetadata

__all__ = [
    # Response Models
    "UnifiedResponse",
    "UnifiedResponseMetadata",
    "UnifiedSourceMetadata",
    # Request Models
    "UnifiedQueryRequest",
    "AgentQueryRequest",
    "StreamingQueryRequest",
    # Enums
    "QueryMode",
    "QueryComplexity",
    "QueryDomain",
    "SourceType",
    "ImpactLevel",
    "RelevanceLevel",
]
