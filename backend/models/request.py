"""
VERITAS Unified Request Models
===============================

Request models for all query types.
Consistent structure across different modes.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from .enums import QueryComplexity, QueryMode


class UnifiedQueryRequest(BaseModel):
    """
    🎯 Unified Query Request for all modes

    Unterstützt:
        - RAG Queries
        - Hybrid Search
        - Simple Ask
        - VPB/COVINA/PKI/IMMI Queries
    """

    # === PFLICHT ===
    query: str = Field(..., min_length=1, max_length=10000, description="User Query")

    # === MODE & MODEL ===
    mode: QueryMode = Field(default=QueryMode.RAG, description="Query Mode")
    model: str = Field(default="llama3.2", description="LLM Model")

    # === LLM PARAMETERS ===
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature")
    max_tokens: int = Field(default=2000, ge=1, le=32000, description="Max Tokens")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-P")

    # === SESSION ===
    session_id: Optional[str] = Field(None, description="Session ID (auto-generated if None)")

    # === SEARCH PARAMETERS ===
    top_k: int = Field(default=5, ge=1, le=50, description="Anzahl Top-Ergebnisse")
    threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Mindest-Score für Ergebnisse")

    # === CUSTOM METADATA ===
    metadata: Optional[Dict[str, Any]] = Field(None, description="Custom Metadata")

    # === CONVERSATION HISTORY ===
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="Conversation History for Multi-Turn")

    @validator("query")
    def validate_query(cls, v):
        """Validate query is not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

    class Config:
        extra = "allow"  # ✨ Erlaubt zusätzliche Felder (Frontend-Kompatibilität)
        use_enum_values = True


class AgentQueryRequest(BaseModel):
    """
    Request for Agent-based Queries

    Erweitert UnifiedQueryRequest mit Agent-spezifischen Parametern.
    """

    # === PFLICHT ===
    query: str = Field(..., min_length=1, max_length=10000)

    # === AGENT SELECTION ===
    agent_types: List[str] = Field(default_factory=list, description="Gewünschte Agent-Typen (leer = auto-select)")

    # === COMPLEXITY ===
    complexity: QueryComplexity = Field(default=QueryComplexity.STANDARD, description="Query Complexity")

    # === EXTERNAL SOURCES ===
    external_sources: bool = Field(default=True, description="Externe Datenquellen nutzen (EU LEX, Google, etc.)")

    # === QUALITY ===
    quality_level: str = Field(default="high", description="Quality Level (high/medium/low)")

    # === SESSION ===
    session_id: Optional[str] = Field(None, description="Session ID")

    # === LLM ===
    model: str = Field(default="llama3.2")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=32000)

    class Config:
        extra = "allow"
        use_enum_values = True


class StreamingQueryRequest(BaseModel):
    """
    Request for Streaming Queries with Progress Updates
    """

    # === PFLICHT ===
    query: str = Field(..., min_length=1, max_length=10000)

    # === SESSION ===
    session_id: Optional[str] = Field(None, description="Session ID")

    # === STREAMING OPTIONS ===
    enable_streaming: bool = Field(default=True, description="Aktiviere Progress Streaming")
    enable_intermediate_results: bool = Field(default=True, description="Zeige Zwischenergebnisse")
    enable_llm_thinking: bool = Field(default=True, description="Zeige LLM Deep-thinking")

    # === LLM ===
    model: str = Field(default="llama3.2")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=32000)

    class Config:
        extra = "allow"
        use_enum_values = True


class HybridSearchRequest(BaseModel):
    """
    Request for Hybrid Search (BM25 + Dense + RRF)
    """

    # === PFLICHT ===
    query: str = Field(..., min_length=1, max_length=10000)

    # === SEARCH PARAMETERS ===
    top_k: int = Field(default=10, ge=1, le=100, description="Top-K Ergebnisse")
    bm25_weight: float = Field(default=0.5, ge=0.0, le=1.0, description="BM25 Gewichtung")
    dense_weight: float = Field(default=0.5, ge=0.0, le=1.0, description="Dense Gewichtung")

    # === RE-RANKING ===
    enable_reranking: bool = Field(default=True, description="Re-Ranking aktivieren")
    rerank_top_k: int = Field(default=5, ge=1, le=50, description="Re-Rank Top-K")

    # === RRF FUSION ===
    enable_rrf: bool = Field(default=True, description="RRF Fusion aktivieren")
    rrf_k: int = Field(default=60, description="RRF K-Parameter")

    # === SESSION ===
    session_id: Optional[str] = Field(None)

    # === LLM ===
    model: str = Field(default="llama3.2")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    class Config:
        extra = "allow"
        use_enum_values = True


class SimpleAskRequest(BaseModel):
    """
    Simple Ask Request (Direct LLM ohne RAG)
    """

    query: str = Field(..., min_length=1, max_length=10000)
    model: str = Field(default="llama3.2")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=16000)
    session_id: Optional[str] = Field(None)

    class Config:
        extra = "allow"
        use_enum_values = True
