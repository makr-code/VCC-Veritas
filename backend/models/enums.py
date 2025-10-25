"""
VERITAS Backend Enums
=====================

Shared enumerations for consistent typing across the system.
"""

from enum import Enum


class QueryMode(str, Enum):
    """Query processing modes"""
    RAG = "rag"
    HYBRID = "hybrid"
    STREAMING = "streaming"
    AGENT = "agent"
    ASK = "ask"
    VERITAS = "veritas"
    VPB = "vpb"
    COVINA = "covina"
    PKI = "pki"
    IMMI = "immi"


class QueryComplexity(str, Enum):
    """Query complexity levels"""
    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"
    EXPERT = "expert"


class QueryDomain(str, Enum):
    """Legal/Administrative domains"""
    GENERAL = "general"
    BUILDING = "building"
    ENVIRONMENTAL = "environmental"
    TRANSPORT = "transport"
    BUSINESS = "business"
    SOCIAL = "social"
    FINANCIAL = "financial"
    HEALTH = "health"
    CONSTRUCTION = "construction"
    TRAFFIC = "traffic"


class SourceType(str, Enum):
    """Document/Source types"""
    DOCUMENT = "document"
    WEB = "web"
    DATABASE = "database"
    API = "api"
    CITATION = "citation"


class ImpactLevel(str, Enum):
    """Impact assessment levels"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"


class RelevanceLevel(str, Enum):
    """Relevance assessment levels"""
    VERY_HIGH = "Very High"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"


class QueryStatus(str, Enum):
    """Query processing status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(str, Enum):
    """Agent capabilities for selection"""
    DOCUMENT_RETRIEVAL = "document_retrieval"
    GEO_CONTEXT = "geo_context"
    LEGAL_FRAMEWORK = "legal_framework"
    DOMAIN_SPECIFIC = "domain_specific_processing"
    QUALITY_ASSESSMENT = "quality_assessment"
    AUTHORITY_MAPPING = "authority_mapping"
    EXTERNAL_API = "external_api"
    DATABASE_QUERY = "database_query"
    CONSTRUCTION = "construction"
    ENVIRONMENTAL = "environmental"
    FINANCIAL = "financial"
    TRANSPORT = "transport"
    SOCIAL = "social"
    TRAFFIC = "traffic"
