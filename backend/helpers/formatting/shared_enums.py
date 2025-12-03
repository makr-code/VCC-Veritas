#!/usr/bin/env python3
"""
VERITAS SHARED ENUMS
===================

Gemeinsame Enumerations für das VERITAS Multi-Agent System
Verhindert circular imports zwischen den Modulen

Author: VERITAS System
Date: 2025-09-28
Version: 1.0
"""

from enum import Enum

# ============================================================================
# QUERY PROCESSING ENUMS
# ============================================================================

class QueryStatus(Enum):
    """Status-Werte für Query-Verarbeitung"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class QueryComplexity(Enum):
    """Query-Komplexitätslevel"""
    BASIC = "basic"         # 🟢 Basic: Einfache Kontext-Anreicherung (Geo + Zeit)
    STANDARD = "standard"   # 🟡 Standard: Multi-Domain + externe Datenquellen  
    ADVANCED = "advanced"   # 🔴 Advanced: Complex Reasoning + Multi-Step-Analysis

class QueryDomain(Enum):
    """Query-Domänen"""
    ENVIRONMENTAL = "environmental"     # Umwelt & Immissionsschutz
    BUILDING = "building"              # Bau & Stadtplanung
    TRANSPORT = "transport"            # Verkehr & Mobilität
    SOCIAL = "social"                  # Soziales & Gesundheit
    BUSINESS = "business"              # Wirtschaft & Gewerbe
    ENVIRONMENTAL_POLICY = "environmental_policy"  # Umwelt & Nachhaltigkeit
    TAXATION = "taxation"              # Steuern & Finanzen
    CIVIC_ENGAGEMENT = "civic_engagement"  # Bürgerbeteiligung & Demokratie
    SECURITY = "security"              # Sicherheit & Ordnung
    HEALTH = "health"                  # Gesundheit & Hygiene
    GENERAL = "general"                # Allgemeine Anfragen

# ============================================================================
# PIPELINE STAGE ENUMS
# ============================================================================

class PipelineStage(Enum):
    """Pipeline-Stages für spezielle Prompt-Templates"""
    QUERY_ANALYSIS = "query_analysis"
    RAG_SEARCH = "rag_search"
    AGENT_SELECTION = "agent_selection"
    AGENT_EXECUTION = "agent_execution"
    RESULT_AGGREGATION = "result_aggregation"
    RESPONSE_GENERATION = "response_generation"
    STEP_COMMENTARY = "step_commentary"