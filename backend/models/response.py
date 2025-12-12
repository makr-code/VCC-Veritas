"""
VERITAS Unified Response Model
===============================

🎯 ONE Response Model for ALL Query Types:
- RAG Queries
- Hybrid Search
- Streaming Queries
- Agent Queries
- Simple Ask

IEEE-Standard Citations (35+ fields per source)
All modes return the same consistent structure.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .enums import QueryMode, SourceType, ImpactLevel, RelevanceLevel


class UnifiedSourceMetadata(BaseModel):
    """
    IEEE-Standard Source Metadata (35+ Fields)
    
    Basis-Felder (immer vorhanden):
        - id: Eindeutige Source ID (1, 2, 3 NICHT "src_1")
        - title: Dokumenttitel
        - type: Source-Typ (document/web/database)
    
    IEEE-Erweiterte Felder (optional via extra="allow"):
        - authors: Autoren formatiert nach IEEE Standard
        - ieee_citation: Vollständige IEEE-Zitation
        - date: ISO 8601 Datum
        - year: Erscheinungsjahr
        - publisher: Verlag/Herausgeber
        - original_source: Quelle der Quelle
        
    Scoring-Felder (optional):
        - similarity_score: Vector-Similarity (0-1)
        - rerank_score: Re-Ranking Score (0-1)
        - quality_score: Quality Assessment (0-1)
        - score: Combined Score (0-1)
        - confidence: Confidence Score (0-1)
        
    Legal Domain Felder (optional):
        - rechtsgebiet: Rechtsgebiet
        - behörde: Zuständige Behörde
        - aktenzeichen: Aktenzeichen
        - gericht: Gericht
        - normtyp: Normtyp (Gesetz/Verordnung/etc)
        - fundstelle: Fundstelle
        
    Assessment Felder (optional):
        - impact: High/Medium/Low
        - relevance: Very High/High/Medium/Low
        
    Weitere 15+ Felder möglich via extra="allow"
    """
    
    # === PFLICHT-FELDER ===
    id: str = Field(..., description="Source ID (numeric: 1, 2, 3 NOT 'src_1')")
    title: str = Field(..., description="Dokumenttitel")
    type: SourceType = Field(default=SourceType.DOCUMENT, description="Source Type")
    
    # === BASIS-FELDER (Optional) ===
    file: Optional[str] = Field(None, description="Dateiname/Pfad")
    page: Optional[int] = Field(None, description="Seitennummer")
    url: Optional[str] = Field(None, description="URL")
    excerpt: Optional[str] = Field(None, description="Text-Auszug")
    
    # === IEEE-FELDER (Optional) ===
    authors: Optional[str] = Field(None, description="Autoren (IEEE-formatiert)")
    ieee_citation: Optional[str] = Field(None, description="Vollständige IEEE-Zitation")
    date: Optional[str] = Field(None, description="Datum (ISO 8601)")
    year: Optional[int] = Field(None, description="Erscheinungsjahr")
    publisher: Optional[str] = Field(None, description="Verlag/Herausgeber")
    original_source: Optional[str] = Field(None, description="Original-Quelle")
    
    # === SCORING-FELDER (Optional) ===
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Vector Similarity")
    rerank_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Re-Ranking Score")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality Score")
    score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Combined Score")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence")
    
    # === LEGAL DOMAIN FELDER (Optional) ===
    rechtsgebiet: Optional[str] = Field(None, description="Rechtsgebiet")
    behörde: Optional[str] = Field(None, description="Zuständige Behörde")
    aktenzeichen: Optional[str] = Field(None, description="Aktenzeichen")
    gericht: Optional[str] = Field(None, description="Gericht")
    normtyp: Optional[str] = Field(None, description="Normtyp")
    fundstelle: Optional[str] = Field(None, description="Fundstelle")
    
    # === ASSESSMENT-FELDER (Optional) ===
    impact: Optional[ImpactLevel] = Field(None, description="Impact Assessment")
    relevance: Optional[RelevanceLevel] = Field(None, description="Relevance Assessment")
    
    # === AGENT-FELDER (Optional) ===
    agent: Optional[str] = Field(None, description="Agent der die Quelle gefunden hat")
    
    class Config:
        extra = "allow"  # ✨ Erlaubt weitere 15+ Felder dynamisch
        use_enum_values = True


class UnifiedResponseMetadata(BaseModel):
    """
    Response Metadata für alle Query-Typen
    
    Enthält:
        - Processing Details (model, mode, duration)
        - Token Usage
        - Source Statistics
        - Query Analysis (complexity, domain)
        - Agent Information
        - Mode-spezifische Details (streaming, hybrid, etc.)
    """
    
    # === PFLICHT-FELDER ===
    model: str = Field(..., description="LLM Model verwendet")
    mode: QueryMode = Field(..., description="Query Mode verwendet")
    duration: float = Field(..., description="Query Dauer (Sekunden)")
    
    # === TOKEN & RESOURCES ===
    tokens_used: Optional[int] = Field(None, description="Tokens verwendet")
    tokens_input: Optional[int] = Field(None, description="Input Tokens")
    tokens_output: Optional[int] = Field(None, description="Output Tokens")
    
    # === SOURCE STATISTICS ===
    sources_count: int = Field(0, description="Anzahl Quellen")
    sources_retrieved: Optional[int] = Field(None, description="Anzahl abgerufene Quellen")
    sources_filtered: Optional[int] = Field(None, description="Anzahl gefilterte Quellen")
    
    # === QUERY ANALYSIS ===
    complexity: Optional[str] = Field(None, description="Query Complexity")
    domain: Optional[str] = Field(None, description="Query Domain")
    
    # === AGENT INFORMATION ===
    agents_involved: Optional[List[str]] = Field(None, description="Verwendete Agents")
    agents_count: Optional[int] = Field(None, description="Anzahl Agents")
    
    # === STREAMING-SPEZIFISCH ===
    stream_enabled: Optional[bool] = Field(None, description="Streaming aktiviert")
    progress_updates: Optional[int] = Field(None, description="Anzahl Progress Updates")
    
    # === HYBRID SEARCH-SPEZIFISCH ===
    search_method: Optional[str] = Field(None, description="Search Method (z.B. 'bm25+dense+rrf')")
    rerank_applied: Optional[bool] = Field(None, description="Re-Ranking angewendet")
    bm25_results: Optional[int] = Field(None, description="BM25 Results")
    dense_results: Optional[int] = Field(None, description="Dense Results")
    rrf_fusion: Optional[bool] = Field(None, description="RRF Fusion applied")
    
    # === QUALITY METRICS ===
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall Quality")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall Confidence")
    
    class Config:
        use_enum_values = True


class UnifiedResponse(BaseModel):
    """
    🎯 UNIFIED Response Model for ALL Query Types
    
    Verwendet von:
        - RAG Queries (/api/query)
        - Hybrid Search (/api/hybrid/search)
        - Streaming Queries (/api/query/stream)
        - Agent Queries (/api/agent/query)
        - Simple Ask (/api/ask)
        - VPB Queries (/api/vpb/query)
        - COVINA Queries (/api/covina/query)
        - etc.
    
    Frontend muss nur EINE Response-Struktur parsen!
    
    IEEE Citations mit 35+ Feldern pro Source.
    Markdown-Content mit eingebetteten [1], [2], [3] Citations.
    """
    
    # === CONTENT (Pflicht) ===
    content: str = Field(
        ..., 
        description="LLM-generierte Antwort (Markdown mit Citations [1], [2], [3])"
    )
    
    # === METADATA (Pflicht) ===
    metadata: UnifiedResponseMetadata = Field(
        ...,
        description="Response Metadata (Model, Mode, Duration, etc.)"
    )
    
    # === SOURCES (Pflicht - kann leer sein) ===
    sources: List[UnifiedSourceMetadata] = Field(
        default_factory=list,
        description="IEEE-Standard Quellen (35+ Felder pro Source)"
    )
    
    # === SESSION (Pflicht) ===
    session_id: str = Field(..., description="Session ID")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response-Zeitpunkt"
    )
    
    # === ADVANCED FEATURES (Optional) ===
    
    # Agent-spezifisch
    agent_results: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Detaillierte Agent-Ergebnisse (für Agent Queries)"
    )
    
    # External API Data
    external_data: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Externe Datenquellen (EU LEX, Google Search, etc.)"
    )
    
    # Quality Assessment
    quality_metrics: Optional[Dict[str, Any]] = Field(
        None,
        description="Detaillierte Quality Metrics"
    )
    
    # Processing Details
    processing_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detaillierte Processing-Informationen"
    )
    
    # Conversation History
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Conversation History (für Multi-Turn)"
    )
    
    # Streaming-spezifisch
    stream_session_id: Optional[str] = Field(
        None,
        description="Streaming Session ID (für Progress Tracking)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Das BImSchG regelt den Schutz vor schädlichen Umwelteinwirkungen [1]. Es gilt für genehmigungsbedürftige Anlagen [2].",
                "sources": [
                    {
                        "id": "1",
                        "title": "Bundes-Immissionsschutzgesetz (BImSchG)",
                        "type": "document",
                        "authors": "Deutscher Bundestag",
                        "ieee_citation": "Deutscher Bundestag, 'Bundes-Immissionsschutzgesetz', BGBl. I S. 1193, 2024.",
                        "year": 2024,
                        "similarity_score": 0.92,
                        "rerank_score": 0.95,
                        "impact": "High",
                        "relevance": "Very High",
                        "rechtsgebiet": "Umweltrecht"
                    },
                    {
                        "id": "2",
                        "title": "4. BImSchV - Genehmigungsverfahren",
                        "type": "document",
                        "similarity_score": 0.88,
                        "impact": "High"
                    }
                ],
                "metadata": {
                    "model": "llama3.2",
                    "mode": "rag",
                    "duration": 2.34,
                    "tokens_used": 456,
                    "sources_count": 2,
                    "complexity": "standard",
                    "agents_involved": ["document_retrieval", "legal_framework"]
                },
                "session_id": "sess_123456",
                "timestamp": "2025-10-19T14:30:00"
            }
        }


class ErrorResponse(BaseModel):
    """Standard Error Response"""
    error: str = Field(..., description="Fehlermeldung")
    error_code: Optional[str] = Field(None, description="Error Code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error Details")
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: Optional[str] = Field(None, description="Session ID")


class ChecklistItem(BaseModel):
    """
    Individual checklist item.
    """
    item_id: int = Field(..., description="Unique item ID within checklist")
    title: str = Field(..., description="Item title")
    description: str = Field(default="", description="Detailed description")
    required: bool = Field(default=True, description="Whether this item is required")
    legal_basis: Optional[str] = Field(None, description="Legal basis or regulation reference")
    references: List[str] = Field(default_factory=list, description="References and sources")
    priority: str = Field(default="medium", description="Priority level (high/medium/low)")
    estimated_duration: Optional[str] = Field(None, description="Estimated time to complete")
    completed: bool = Field(default=False, description="Completion status")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        extra = "allow"


class ChecklistCategory(BaseModel):
    """
    Category grouping checklist items.
    """
    category_name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    items: List[ChecklistItem] = Field(default_factory=list, description="Items in this category")
    
    class Config:
        extra = "allow"


class ChecklistData(BaseModel):
    """
    Complete checklist data structure.
    
    This is the main checklist JSON format returned by the ChecklistAgent.
    Compatible with Argus2 Android app.
    """
    title: str = Field(..., description="Checklist title")
    description: str = Field(default="", description="Checklist description")
    checklist_type: str = Field(default="general", description="Type of checklist")
    categories: List[ChecklistCategory] = Field(
        default_factory=list,
        description="Checklist categories with items"
    )
    notes: Optional[str] = Field(None, description="General notes and remarks")
    references: List[str] = Field(default_factory=list, description="References and sources")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    version: str = Field(default="1.0", description="Checklist version")
    
    class Config:
        extra = "allow"


class ChecklistGenerationResponse(BaseModel):
    """
    Response from checklist generation endpoint.
    
    Returns structured checklist data with metadata.
    """
    status: str = Field(..., description="Response status (success/error)")
    checklist: Optional[ChecklistData] = Field(None, description="Generated checklist")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Generation metadata")
    sources: List[str] = Field(default_factory=list, description="Data sources used")
    error_message: Optional[str] = Field(None, description="Error message if status=error")
    
    # === TIMING ===
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    
    # === SESSION ===
    session_id: Optional[str] = Field(None, description="Session ID")
    
    class Config:
        extra = "allow"
