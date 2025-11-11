"""
VERITAS API v3 - Pydantic Models

Gemeinsame Request/Response Models für API v3.
Konsistente Struktur über alle Endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, validator

# ============================================================================
# Base Models
# ============================================================================


class StatusEnum(str, Enum):
    """Status für asynchrone Operationen"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorResponse(BaseModel):
    """Standard Error Response"""

    error: str = Field(..., description="Fehlermeldung")
    error_code: Optional[str] = Field(None, description="Error Code")
    details: Optional[Dict[str, Any]] = Field(None, description="Zusätzliche Details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Fehler-Zeitpunkt")


class SuccessResponse(BaseModel):
    """Standard Success Response"""

    success: bool = Field(True, description="Erfolg-Flag")
    message: Optional[str] = Field(None, description="Erfolgsmeldung")
    data: Optional[Dict[str, Any]] = Field(None, description="Response Data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response-Zeitpunkt")


# ============================================================================
# Query Models
# ============================================================================


class SourceMetadata(BaseModel):
    """
    Source Metadata für Citations (✨ IEEE-EXTENDED)

    Basis-Felder:
        - id, file, page, confidence, author, title, year, publisher, url, type

    IEEE-Erweiterte Felder (via extra="allow"):
        - authors (formatiert nach IEEE)
        - ieee_citation (vollständige IEEE-Zitation)
        - date (ISO 8601)
        - original_source (Quelle der Quelle)
        - similarity_score, rerank_score, quality_score, score
        - impact (High/Medium/Low)
        - relevance (Very High/High/Medium/Low)
        - rechtsgebiet, behörde, aktenzeichen, gericht
        - und weitere 25+ Felder aus Native RAG Chain
    """

    id: str = Field(..., description="Source ID")
    file: Optional[str] = Field(None, description="Dateiname")
    page: Optional[int] = Field(None, description="Seitennummer")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence Score")
    author: Optional[str] = Field(None, description="Autor")
    title: Optional[str] = Field(None, description="Titel")
    year: Optional[int] = Field(None, description="Erscheinungsjahr")
    publisher: Optional[str] = Field(None, description="Publisher")
    url: Optional[str] = Field(None, description="URL")
    type: Optional[str] = Field("document", description="Source Type (document, web, database)")

    class Config:
        extra = "allow"  # ✨ Erlaubt IEEE-erweiterte Felder ohne explizite Definition


class QueryMetadata(BaseModel):
    """Query Response Metadata"""

    model: str = Field(..., description="LLM Model verwendet")
    mode: str = Field(..., description="Query Mode verwendet")
    duration: float = Field(..., description="Query Dauer (Sekunden)")
    tokens_used: Optional[int] = Field(None, description="Tokens verwendet")
    sources_count: int = Field(0, description="Anzahl Sources")
    sources_metadata: Optional[List[SourceMetadata]] = Field(None, description="Source Details")
    complexity: Optional[str] = Field(None, description="Query Complexity")
    agents_involved: Optional[List[str]] = Field(None, description="Verwendete Agents")


class QueryRequest(BaseModel):
    """Standard Query Request"""

    query: str = Field(..., min_length=1, max_length=10000, description="User Query")
    mode: Optional[str] = Field("veritas", description="Query Mode (veritas, chat, vpb, covina)")
    model: Optional[str] = Field("llama3.2", description="LLM Model")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Temperature")
    max_tokens: Optional[int] = Field(2000, ge=1, le=32000, description="Max Tokens")
    top_p: Optional[float] = Field(0.9, ge=0.0, le=1.0, description="Top-P")
    session_id: Optional[str] = Field(None, description="Session ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Custom Metadata")


class QueryResponse(BaseModel):
    """Standard Query Response"""

    content: str = Field(..., description="Generated Response")
    metadata: QueryMetadata = Field(..., description="Response Metadata")
    session_id: str = Field(..., description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    publisher: Optional[str] = Field(None, description="Publisher")
    url: Optional[str] = Field(None, description="URL")
    type: Optional[str] = Field("document", description="Source Type (document, web, database)")


# ============================================================================
# Agent Models
# ============================================================================


class AgentInfo(BaseModel):
    """Agent Information"""

    agent_id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent Name")
    description: Optional[str] = Field(None, description="Agent Beschreibung")
    capabilities: List[str] = Field(..., description="Agent Capabilities")
    status: Literal["active", "inactive", "error"] = Field("active", description="Agent Status")
    version: Optional[str] = Field(None, description="Agent Version")


class AgentExecuteRequest(BaseModel):
    """Agent Execution Request"""

    agent_id: str = Field(..., description="Agent ID")
    task: str = Field(..., description="Task Beschreibung")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Task Parameters")
    timeout: Optional[int] = Field(60, ge=1, le=600, description="Timeout (Sekunden)")


class AgentExecuteResponse(BaseModel):
    """Agent Execution Response"""

    agent_id: str = Field(..., description="Agent ID")
    result: Dict[str, Any] = Field(..., description="Execution Result")
    status: StatusEnum = Field(..., description="Execution Status")
    duration: float = Field(..., description="Execution Dauer")
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# System Models
# ============================================================================


class SystemHealth(BaseModel):
    """System Health Response"""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="System Status")
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Dict[str, bool] = Field(..., description="Service Status")
    uptime: Optional[float] = Field(None, description="Uptime (Sekunden)")


class SystemCapabilities(BaseModel):
    """System Capabilities Response"""

    version: str = Field(..., description="System Version")
    endpoints: List[str] = Field(..., description="Verfügbare Endpoints")
    features: Dict[str, bool] = Field(..., description="Feature Flags")
    models: List[str] = Field(..., description="Verfügbare LLM Models")
    agents: List[str] = Field(..., description="Verfügbare Agents")


class SystemMetrics(BaseModel):
    """System Metrics Response"""

    requests_total: int = Field(..., description="Total Requests")
    requests_per_second: float = Field(..., description="Requests/Second")
    average_latency: float = Field(..., description="Avg Latency (ms)")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Error Rate")
    uptime: float = Field(..., description="Uptime (Sekunden)")
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# SAGA Models
# ============================================================================


class SAGAStep(BaseModel):
    """SAGA Step Definition"""

    step_id: str = Field(..., description="Step ID")
    service: str = Field(..., description="Service Name")
    action: str = Field(..., description="Action Name")
    parameters: Dict[str, Any] = Field(..., description="Action Parameters")
    compensation: Optional[Dict[str, Any]] = Field(None, description="Compensation Action")
    timeout: int = Field(60, ge=1, le=600, description="Timeout (Sekunden)")


class SAGAOrchestrationRequest(BaseModel):
    """SAGA Orchestration Request"""

    saga_name: str = Field(..., description="SAGA Name")
    steps: List[SAGAStep] = Field(..., min_items=1, description="SAGA Steps")
    timeout: int = Field(300, ge=1, le=3600, description="Total Timeout")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Custom Metadata")


class SAGAStatus(BaseModel):
    """SAGA Status Response"""

    saga_id: str = Field(..., description="SAGA ID")
    saga_name: str = Field(..., description="SAGA Name")
    status: StatusEnum = Field(..., description="SAGA Status")
    current_step: int = Field(..., description="Aktueller Step (1-based)")
    total_steps: int = Field(..., description="Gesamt Steps")
    steps_completed: List[str] = Field(..., description="Abgeschlossene Steps")
    steps_failed: Optional[List[str]] = Field(None, description="Fehlgeschlagene Steps")
    compensation_executed: bool = Field(False, description="Compensation ausgeführt")
    created_at: datetime = Field(..., description="Erstellungs-Zeitpunkt")
    updated_at: datetime = Field(..., description="Update-Zeitpunkt")


# ============================================================================
# Compliance Models
# ============================================================================


class ComplianceViolation(BaseModel):
    """Compliance Violation"""

    violation_id: str = Field(..., description="Violation ID")
    rule: str = Field(..., description="Verletzte Regel")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Severity")
    description: str = Field(..., description="Violation Beschreibung")
    remediation: Optional[str] = Field(None, description="Remediation Vorschlag")


class ComplianceCheckRequest(BaseModel):
    """Compliance Check Request"""

    entity_type: str = Field(..., description="Entity Type (document, dataset, process)")
    entity_id: str = Field(..., description="Entity ID")
    rules: List[str] = Field(..., min_items=1, description="Compliance Rules (GDPR, DSGVO, BImSchG)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Check Parameters")


class ComplianceCheckResponse(BaseModel):
    """Compliance Check Response"""

    entity_id: str = Field(..., description="Entity ID")
    status: Literal["compliant", "non_compliant", "unknown"] = Field(..., description="Compliance Status")
    score: float = Field(..., ge=0.0, le=1.0, description="Compliance Score")
    violations: List[ComplianceViolation] = Field(..., description="Violations")
    recommendations: List[str] = Field(..., description="Empfehlungen")
    checked_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Governance Models
# ============================================================================


class DataLineageRequest(BaseModel):
    """Data Lineage Request"""

    entity_id: str = Field(..., description="Entity ID")
    depth: int = Field(3, ge=1, le=10, description="Lineage Depth")
    direction: Literal["upstream", "downstream", "both"] = Field("both", description="Lineage Direction")


class DataLineageResponse(BaseModel):
    """Data Lineage Response"""

    entity_id: str = Field(..., description="Root Entity ID")
    lineage: Dict[str, Any] = Field(..., description="Lineage Graph (JSON)")
    total_nodes: int = Field(..., description="Anzahl Nodes")
    total_edges: int = Field(..., description="Anzahl Edges")
    max_depth: int = Field(..., description="Maximale Depth")
    generated_at: datetime = Field(default_factory=datetime.now)


class DataGovernancePolicy(BaseModel):
    """Data Governance Policy"""

    policy_id: str = Field(..., description="Policy ID")
    name: str = Field(..., description="Policy Name")
    description: str = Field(..., description="Policy Beschreibung")
    type: Literal["access", "retention", "quality", "security"] = Field(..., description="Policy Type")
    rules: List[Dict[str, Any]] = Field(..., description="Policy Rules")
    status: Literal["active", "inactive", "draft"] = Field("active", description="Policy Status")
    created_at: datetime = Field(..., description="Erstellungs-Zeitpunkt")
    updated_at: datetime = Field(..., description="Update-Zeitpunkt")


# ============================================================================
# Domain Endpoints - Phase 2
# ============================================================================


# VPB (Verwaltungspraxis der Bundesbehörden)
class VPBQueryRequest(BaseModel):
    """VPB Query Request"""

    query: str = Field(..., min_length=1, description="VPB-spezifische Query")
    mode: Literal["veritas", "simple", "deep"] = Field("veritas", description="Query Mode")
    session_id: Optional[str] = Field(None, description="Session ID")
    filters: Optional[Dict[str, Any]] = Field(None, description="VPB-Filters (Jahr, Behörde, etc.)")


class VPBDocument(BaseModel):
    """VPB Dokument"""

    document_id: str = Field(..., description="VPB Dokument ID")
    title: str = Field(..., description="Titel")
    authority: Optional[str] = Field(None, description="Behörde")
    year: Optional[int] = Field(None, description="Jahr")
    reference: Optional[str] = Field(None, description="VPB Referenz")
    content_preview: Optional[str] = Field(None, description="Vorschau")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevanz")


class VPBQueryResponse(BaseModel):
    """VPB Query Response"""

    query_id: str = Field(..., description="Query ID")
    content: str = Field(..., description="Response Content")
    documents: List[VPBDocument] = Field(default_factory=list, description="VPB Dokumente")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Zusätzliche Metadaten")
    duration: Optional[float] = Field(None, description="Query Duration (Sekunden)")


class VPBAnalysisRequest(BaseModel):
    """VPB Verwaltungsprozess-Analyse Request"""

    process_description: str = Field(..., min_length=1, description="Beschreibung des Verwaltungsprozesses")
    context: Optional[Dict[str, Any]] = Field(None, description="Kontext-Informationen")


class VPBAnalysisResponse(BaseModel):
    """VPB Verwaltungsprozess-Analyse Response"""

    analysis_id: str = Field(..., description="Analyse ID")
    summary: str = Field(..., description="Analyse-Zusammenfassung")
    recommendations: List[str] = Field(default_factory=list, description="Empfehlungen")
    legal_references: List[VPBDocument] = Field(default_factory=list, description="Rechtliche Referenzen")
    risk_assessment: Optional[Dict[str, Any]] = Field(None, description="Risikobewertung")


# COVINA (COVID-19 Intelligence Agent)
class COVINAQueryRequest(BaseModel):
    """COVINA Query Request"""

    query: str = Field(..., min_length=1, description="COVID-19-bezogene Query")
    mode: Literal["veritas", "simple", "statistics"] = Field("veritas", description="Query Mode")
    session_id: Optional[str] = Field(None, description="Session ID")
    time_range: Optional[Dict[str, str]] = Field(None, description="Zeitbereich (from, to)")


class COVINAStatistics(BaseModel):
    """COVINA Statistiken"""

    region: str = Field(..., description="Region")
    date: str = Field(..., description="Datum (ISO 8601)")
    cases: Optional[int] = Field(None, description="Fallzahlen")
    incidence: Optional[float] = Field(None, description="Inzidenz")
    r_value: Optional[float] = Field(None, description="R-Wert")
    data_source: Optional[str] = Field(None, description="Datenquelle")


class COVINAReport(BaseModel):
    """COVINA Report"""

    report_id: str = Field(..., description="Report ID")
    title: str = Field(..., description="Report Titel")
    date: str = Field(..., description="Datum")
    summary: str = Field(..., description="Zusammenfassung")
    statistics: List[COVINAStatistics] = Field(default_factory=list, description="Statistiken")


class COVINAQueryResponse(BaseModel):
    """COVINA Query Response"""

    query_id: str = Field(..., description="Query ID")
    content: str = Field(..., description="Response Content")
    statistics: List[COVINAStatistics] = Field(default_factory=list, description="Statistiken")
    reports: List[COVINAReport] = Field(default_factory=list, description="Reports")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Zusätzliche Metadaten")
    duration: Optional[float] = Field(None, description="Query Duration (Sekunden)")


# PKI (Public Key Infrastructure)
class PKIQueryRequest(BaseModel):
    """PKI Query Request"""

    query: str = Field(..., min_length=1, description="PKI-bezogene Query")
    mode: Literal["veritas", "simple", "technical"] = Field("veritas", description="Query Mode")
    session_id: Optional[str] = Field(None, description="Session ID")


class PKICertificate(BaseModel):
    """PKI Zertifikat"""

    certificate_id: str = Field(..., description="Zertifikat ID")
    subject: str = Field(..., description="Subject (CN)")
    issuer: str = Field(..., description="Issuer")
    valid_from: str = Field(..., description="Gültig ab (ISO 8601)")
    valid_until: str = Field(..., description="Gültig bis (ISO 8601)")
    serial_number: Optional[str] = Field(None, description="Seriennummer")
    status: Literal["valid", "expired", "revoked"] = Field("valid", description="Status")


class PKIQueryResponse(BaseModel):
    """PKI Query Response"""

    query_id: str = Field(..., description="Query ID")
    content: str = Field(..., description="Response Content")
    certificates: List[PKICertificate] = Field(default_factory=list, description="Zertifikate")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Zusätzliche Metadaten")
    duration: Optional[float] = Field(None, description="Query Duration (Sekunden)")


class PKIValidationRequest(BaseModel):
    """PKI Zertifikat-Validierung Request"""

    certificate_data: str = Field(..., description="Zertifikat-Daten (PEM/DER)")
    check_revocation: bool = Field(True, description="Revocation-Check durchführen")
    check_chain: bool = Field(True, description="Chain-Validierung durchführen")


class PKIValidationResponse(BaseModel):
    """PKI Zertifikat-Validierung Response"""

    validation_id: str = Field(..., description="Validierungs-ID")
    is_valid: bool = Field(..., description="Zertifikat gültig?")
    status: str = Field(..., description="Validierungs-Status")
    errors: List[str] = Field(default_factory=list, description="Validierungs-Fehler")
    warnings: List[str] = Field(default_factory=list, description="Warnungen")
    certificate_info: Optional[PKICertificate] = Field(None, description="Zertifikat-Info")


# IMMI (Immissionsschutz)
class IMMIQueryRequest(BaseModel):
    """IMMI Query Request"""

    query: str = Field(..., min_length=1, description="Immissionsschutz-bezogene Query")
    mode: Literal["veritas", "simple", "technical"] = Field("veritas", description="Query Mode")
    session_id: Optional[str] = Field(None, description="Session ID")
    location: Optional[Dict[str, float]] = Field(None, description="Standort (lat, lon)")


class IMMIRegulation(BaseModel):
    """IMMI BImSchG Vorschrift"""

    regulation_id: str = Field(..., description="Vorschrift ID")
    title: str = Field(..., description="Titel")
    reference: str = Field(..., description="Gesetzesreferenz (z.B. §4 BImSchG)")
    content: str = Field(..., description="Vorschrift-Inhalt")
    category: Optional[str] = Field(None, description="Kategorie")


class IMMIGeoData(BaseModel):
    """IMMI WKA Geodaten"""

    location_id: str = Field(..., description="Standort ID")
    name: Optional[str] = Field(None, description="Anlagenname")
    latitude: float = Field(..., description="Breitengrad")
    longitude: float = Field(..., description="Längengrad")
    type: Literal["wka", "industrial", "residential"] = Field("wka", description="Anlagentyp")
    distance_to_residential: Optional[float] = Field(None, description="Abstand zu Wohngebieten (m)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Zusätzliche Geodaten")


class IMMIQueryResponse(BaseModel):
    """IMMI Query Response"""

    query_id: str = Field(..., description="Query ID")
    content: str = Field(..., description="Response Content")
    regulations: List[IMMIRegulation] = Field(default_factory=list, description="BImSchG Vorschriften")
    geodata: List[IMMIGeoData] = Field(default_factory=list, description="WKA Geodaten")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Zusätzliche Metadaten")
    duration: Optional[float] = Field(None, description="Query Duration (Sekunden)")


# ============================================================================
# UDS3 Endpoints - Phase 4
# ============================================================================


class UDS3QueryRequest(BaseModel):
    """Unified Database Query Request"""

    query: str = Field(..., min_length=1, description="Query Text")
    database_type: Literal["vector", "graph", "relational", "file"] = Field(..., description="Database Type")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query Parameters")
    timeout: int = Field(60, ge=1, le=300, description="Timeout in Sekunden")


class UDS3QueryResponse(BaseModel):
    """Unified Database Query Response"""

    query_id: str = Field(..., description="Query ID")
    database_type: str = Field(..., description="Database Type")
    results: List[Dict[str, Any]] = Field(..., description="Query Results")
    count: int = Field(..., description="Result Count")
    metadata: Dict[str, Any] = Field(..., description="Query Metadata")
    duration: float = Field(..., description="Query Duration (Sekunden)")


class VectorSearchRequest(BaseModel):
    """Vector Search Request"""

    query_vector: Optional[List[float]] = Field(None, description="Query Vector (optional wenn query_text gegeben)")
    query_text: Optional[str] = Field(None, description="Query Text (wird zu Vector konvertiert)")
    top_k: int = Field(10, ge=1, le=100, description="Top K Results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata Filters")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity Threshold")


class VectorSearchResponse(BaseModel):
    """Vector Search Response"""

    results: List[Dict[str, Any]] = Field(..., description="Search Results with Scores")
    count: int = Field(..., description="Result Count")
    query_vector: Optional[List[float]] = Field(None, description="Query Vector Used")
    duration: float = Field(..., description="Search Duration (Sekunden)")


class GraphQueryRequest(BaseModel):
    """Graph Query Request (Cypher)"""

    cypher_query: str = Field(..., min_length=1, description="Cypher Query")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query Parameters")
    limit: int = Field(100, ge=1, le=1000, description="Result Limit")


class GraphQueryResponse(BaseModel):
    """Graph Query Response"""

    nodes: List[Dict[str, Any]] = Field(..., description="Graph Nodes")
    relationships: List[Dict[str, Any]] = Field(..., description="Graph Relationships")
    count: int = Field(..., description="Node Count")
    duration: float = Field(..., description="Query Duration (Sekunden)")


class BulkOperationRequest(BaseModel):
    """Bulk Operation Request"""

    operation: Literal["insert", "update", "delete"] = Field(..., description="Operation Type")
    database_type: Literal["vector", "graph", "relational"] = Field(..., description="Target Database")
    data: List[Dict[str, Any]] = Field(..., description="Data to Process")
    batch_size: int = Field(100, ge=1, le=1000, description="Batch Size")


class BulkOperationResponse(BaseModel):
    """Bulk Operation Response"""

    operation_id: str = Field(..., description="Operation ID")
    status: Literal["completed", "partial", "failed"] = Field(..., description="Operation Status")
    total_items: int = Field(..., description="Total Items")
    successful: int = Field(..., description="Successful Operations")
    failed: int = Field(..., description="Failed Operations")
    errors: List[str] = Field(default_factory=list, description="Error Messages")
    duration: float = Field(..., description="Operation Duration (Sekunden)")


class DatabaseInfo(BaseModel):
    """Database Information"""

    database_type: str = Field(..., description="Database Type")
    name: str = Field(..., description="Database Name")
    status: Literal["online", "offline", "degraded"] = Field(..., description="Database Status")
    size_mb: float = Field(..., description="Database Size (MB)")
    record_count: int = Field(..., description="Record Count")
    last_updated: datetime = Field(..., description="Last Update")


class UDS3Statistics(BaseModel):
    """UDS3 Statistics"""

    total_databases: int = Field(..., description="Total Databases")
    total_queries: int = Field(..., description="Total Queries (last 24h)")
    average_query_time: float = Field(..., description="Average Query Time (ms)")
    databases: List[DatabaseInfo] = Field(..., description="Database List")
    cache_hit_rate: float = Field(..., ge=0.0, le=1.0, description="Cache Hit Rate")
    uptime_seconds: int = Field(..., description="Uptime in Seconds")


# ============================================================================
# User Endpoints - Phase 4
# ============================================================================


class UserRegistration(BaseModel):
    """User Registration Request"""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email Address")
    password: str = Field(..., min_length=8, description="Password")
    full_name: Optional[str] = Field(None, description="Full Name")
    organization: Optional[str] = Field(None, description="Organization")


class UserProfile(BaseModel):
    """User Profile"""

    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email Address")
    full_name: Optional[str] = Field(None, description="Full Name")
    organization: Optional[str] = Field(None, description="Organization")
    role: Literal["user", "analyst", "admin"] = Field("user", description="User Role")
    created_at: datetime = Field(..., description="Registration Date")
    last_login: Optional[datetime] = Field(None, description="Last Login")
    query_count: int = Field(0, description="Total Query Count")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User Preferences")


class UserPreferences(BaseModel):
    """User Preferences"""

    user_id: str = Field(..., description="User ID")
    theme: Literal["light", "dark", "forest"] = Field("forest", description="UI Theme")
    language: Literal["de", "en", "fr", "it"] = Field("de", description="Language")
    default_mode: Literal["veritas", "chat", "vpb", "covina"] = Field("veritas", description="Default Query Mode")
    enable_llm_commentary: bool = Field(False, description="LLM Commentary aktivieren")
    results_per_page: int = Field(10, ge=5, le=100, description="Results per Page")
    auto_save_queries: bool = Field(True, description="Queries automatisch speichern")
    notifications_enabled: bool = Field(True, description="Notifications aktivieren")


class UserFeedback(BaseModel):
    """User Feedback"""

    user_id: str = Field(..., description="User ID")
    feedback_type: Literal["bug", "feature", "improvement", "question", "other"] = Field(..., description="Feedback Type")
    title: str = Field(..., min_length=5, max_length=200, description="Feedback Title")
    description: str = Field(..., min_length=10, description="Feedback Description")
    priority: Literal["low", "medium", "high"] = Field("medium", description="Priority")
    related_query_id: Optional[str] = Field(None, description="Related Query ID")
    attachments: Optional[List[str]] = Field(None, description="Attachment URLs")


class UserQueryHistory(BaseModel):
    """User Query History Entry"""

    query_id: str = Field(..., description="Query ID")
    user_id: str = Field(..., description="User ID")
    query_text: str = Field(..., description="Query Text")
    mode: str = Field(..., description="Query Mode")
    results_count: int = Field(..., description="Results Count")
    confidence: float = Field(..., description="Confidence Score")
    duration: float = Field(..., description="Query Duration (Sekunden)")
    timestamp: datetime = Field(..., description="Query Timestamp")
    bookmarked: bool = Field(False, description="Bookmarked by User")


__all__ = [
    # Base
    "StatusEnum",
    "ErrorResponse",
    "SuccessResponse",
    # Query
    "QueryRequest",
    "QueryResponse",
    "QueryMetadata",
    "SourceMetadata",
    # Agent
    "AgentInfo",
    "AgentExecuteRequest",
    "AgentExecuteResponse",
    # System
    "SystemHealth",
    "SystemCapabilities",
    "SystemMetrics",
    # SAGA
    "SAGAStep",
    "SAGAOrchestrationRequest",
    "SAGAStatus",
    # Compliance
    "ComplianceCheckRequest",
    "ComplianceCheckResponse",
    "ComplianceViolation",
    # Governance
    "DataLineageRequest",
    "DataLineageResponse",
    "DataGovernancePolicy",
    # Domain Endpoints (Phase 2)
    "VPBQueryRequest",
    "VPBQueryResponse",
    "VPBDocument",
    "VPBAnalysisRequest",
    "VPBAnalysisResponse",
    "COVINAQueryRequest",
    "COVINAQueryResponse",
    "COVINAStatistics",
    "COVINAReport",
    "PKIQueryRequest",
    "PKIQueryResponse",
    "PKICertificate",
    "PKIValidationRequest",
    "PKIValidationResponse",
    "IMMIQueryRequest",
    "IMMIQueryResponse",
    "IMMIRegulation",
    "IMMIGeoData",
    # Phase 4: UDS3 & User
    "UDS3QueryRequest",
    "UDS3QueryResponse",
    "VectorSearchRequest",
    "VectorSearchResponse",
    "GraphQueryRequest",
    "GraphQueryResponse",
    "BulkOperationRequest",
    "BulkOperationResponse",
    "DatabaseInfo",
    "UDS3Statistics",
    "UserRegistration",
    "UserProfile",
    "UserPreferences",
    "UserFeedback",
    "UserQueryHistory",
]
