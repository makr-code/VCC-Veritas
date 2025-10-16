#!/usr/bin/env python3
"""
VERITAS SUPERVISOR AGENT
========================

Intelligenter Supervisor für Multi-Agent-Orchestrierung

KERNFUNKTIONEN:
1. Query Decomposition - Zerlegung komplexer Queries in atomare Subqueries
2. Agent Selection - Intelligente Auswahl von Spezial-Agents
3. Orchestration - Koordination paralleler und sequenzieller Agent-Execution
4. Result Synthesis - Aggregation von Teilergebnissen

Inspiriert von:
- AWS Agents for Bedrock Multi-Agent Collaboration
- Azure Semantic Kernel Planner
- LangChain Multi-Agent Supervisor Pattern

Author: VERITAS System
Date: 06.10.2025
Version: 1.0
"""

import os
import sys
import asyncio
import logging
import json
import uuid
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime, timezone

# Sicherstellen, dass das Projekt-Root im Python-Pfad liegt
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

# VERITAS Imports
from backend.agents.veritas_ollama_client import VeritasOllamaClient, OllamaRequest
from backend.agents.veritas_shared_enums import QueryComplexity, QueryDomain
from backend.agents.veritas_enhanced_prompts import EnhancedPromptTemplates, PromptMode
from backend.agents.veritas_json_citation_formatter import JSONCitationFormatter

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class QueryType(Enum):
    """Typen von Subqueries"""
    ENVIRONMENTAL_DATA = "environmental_data"
    AUTHORITY_MAPPING = "authority_mapping"
    LEGAL_FRAMEWORK = "legal_framework"
    CONSTRUCTION_INFO = "construction_info"
    FINANCIAL_DATA = "financial_data"
    SOCIAL_DATA = "social_data"
    TRAFFIC_DATA = "traffic_data"
    GENERAL_KNOWLEDGE = "general_knowledge"
    DOCUMENT_RETRIEVAL = "document_retrieval"

class AgentCapability(Enum):
    """Agent-Capabilities für Matching"""
    # Environmental
    AIR_QUALITY_MONITORING = "air_quality_monitoring"
    WATER_QUALITY = "water_quality"
    ENVIRONMENTAL_DATA = "environmental_data"
    WASTE_MANAGEMENT = "waste_management"
    
    # Construction
    BUILDING_PERMITS = "building_permits"
    ZONING_REGULATIONS = "zoning_regulations"
    CONSTRUCTION_LAW = "construction_law"
    
    # Financial
    BUDGETS = "budgets"
    SUBSIDIES = "subsidies"
    PUBLIC_SPENDING = "public_spending"
    FINANCIAL_REPORTS = "financial_reports"
    
    # Social
    DEMOGRAPHICS = "demographics"
    SOCIAL_SERVICES = "social_services"
    EDUCATION_DATA = "education_data"
    
    # Traffic
    TRAFFIC_FLOW = "traffic_flow"
    PARKING = "parking"
    PUBLIC_TRANSPORT = "public_transport"
    
    # Authority
    ADMINISTRATIVE_STRUCTURE = "administrative_structure"
    CONTACT_FINDER = "contact_finder"
    JURISDICTION = "jurisdiction"
    
    # Legal
    LAW_RETRIEVAL = "law_retrieval"
    REGULATION_INTERPRETATION = "regulation_interpretation"
    LEGAL_PRECEDENTS = "legal_precedents"
    
    # General
    DOCUMENT_SEARCH = "document_search"
    QUALITY_ASSESSMENT = "quality_assessment"

# Agent Capability Mapping
AGENT_CAPABILITY_MAP = {
    "environmental": [
        AgentCapability.AIR_QUALITY_MONITORING,
        AgentCapability.WATER_QUALITY,
        AgentCapability.ENVIRONMENTAL_DATA,
        AgentCapability.WASTE_MANAGEMENT,
    ],
    "construction": [
        AgentCapability.BUILDING_PERMITS,
        AgentCapability.ZONING_REGULATIONS,
        AgentCapability.CONSTRUCTION_LAW,
    ],
    "financial": [
        AgentCapability.BUDGETS,
        AgentCapability.SUBSIDIES,
        AgentCapability.PUBLIC_SPENDING,
        AgentCapability.FINANCIAL_REPORTS,
    ],
    "social": [
        AgentCapability.DEMOGRAPHICS,
        AgentCapability.SOCIAL_SERVICES,
        AgentCapability.EDUCATION_DATA,
    ],
    "traffic": [
        AgentCapability.TRAFFIC_FLOW,
        AgentCapability.PARKING,
        AgentCapability.PUBLIC_TRANSPORT,
    ],
    "authority_mapping": [
        AgentCapability.ADMINISTRATIVE_STRUCTURE,
        AgentCapability.CONTACT_FINDER,
        AgentCapability.JURISDICTION,
    ],
    "legal_framework": [
        AgentCapability.LAW_RETRIEVAL,
        AgentCapability.REGULATION_INTERPRETATION,
        AgentCapability.LEGAL_PRECEDENTS,
    ],
    "document_retrieval": [
        AgentCapability.DOCUMENT_SEARCH,
    ],
    "quality_assessor": [
        AgentCapability.QUALITY_ASSESSMENT,
    ]
}

# ============================================================================
# DATASTRUKTUREN
# ============================================================================

@dataclass
class SubQuery:
    """Atomare Teilfrage aus Query Decomposition"""
    id: str
    query_text: str
    query_type: str  # QueryType Enum value
    priority: float  # 0.0 - 1.0
    dependencies: List[str] = field(default_factory=list)  # IDs anderer SubQueries
    required_capabilities: List[str] = field(default_factory=list)  # AgentCapability values
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query_text": self.query_text,
            "query_type": self.query_type,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "required_capabilities": self.required_capabilities,
            "metadata": self.metadata
        }

@dataclass
class AgentAssignment:
    """Zuordnung Agent → Subquery"""
    agent_type: str
    agent_id: Optional[str] = None
    confidence_score: float = 0.0
    matching_capabilities: List[str] = field(default_factory=list)
    priority: float = 1.0
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_type": self.agent_type,
            "agent_id": self.agent_id,
            "confidence_score": self.confidence_score,
            "matching_capabilities": self.matching_capabilities,
            "priority": self.priority,
            "reason": self.reason,
            "metadata": self.metadata
        }

@dataclass
class AgentSelection:
    """Resultat der Agent-Selektion für eine Subquery"""
    subquery_id: str
    selected_agents: List[AgentAssignment] = field(default_factory=list)
    fallback_agents: List[AgentAssignment] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "subquery_id": self.subquery_id,
            "selected_agents": [a.to_dict() for a in self.selected_agents],
            "fallback_agents": [a.to_dict() for a in self.fallback_agents]
        }

@dataclass
class AgentExecutionPlan:
    """Vollständiger Ausführungsplan für Multi-Agent-Orchestration"""
    parallel_agents: List[Tuple[str, AgentAssignment]] = field(default_factory=list)  # (subquery_id, assignment)
    sequential_agents: List[Tuple[str, AgentAssignment]] = field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)  # subquery_id → dependency_ids
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "parallel_agents": [
                {"subquery_id": sq_id, "assignment": a.to_dict()}
                for sq_id, a in self.parallel_agents
            ],
            "sequential_agents": [
                {"subquery_id": sq_id, "assignment": a.to_dict()}
                for sq_id, a in self.sequential_agents
            ],
            "dependency_graph": self.dependency_graph,
            "metadata": self.metadata
        }

@dataclass
class AgentResult:
    """Ergebnis eines einzelnen Agents"""
    subquery_id: str
    agent_type: str
    result_data: Dict[str, Any]
    confidence_score: float
    processing_time: float = 0.0
    sources: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "subquery_id": self.subquery_id,
            "agent_type": self.agent_type,
            "result_data": self.result_data,
            "confidence_score": self.confidence_score,
            "processing_time": self.processing_time,
            "sources": self.sources,
            "metadata": self.metadata
        }

@dataclass
class SynthesizedResult:
    """Finales Ergebnis nach Result-Synthese"""
    response_text: str
    confidence_score: float
    sources: List[Dict[str, Any]] = field(default_factory=list)
    subquery_coverage: Dict[str, float] = field(default_factory=dict)  # subquery_id → coverage_score
    conflicts_detected: List[Dict[str, Any]] = field(default_factory=list)
    synthesis_method: str = "llm_narrative_generation"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_text": self.response_text,
            "confidence_score": self.confidence_score,
            "sources": self.sources,
            "subquery_coverage": self.subquery_coverage,
            "conflicts_detected": self.conflicts_detected,
            "synthesis_method": self.synthesis_method,
            "metadata": self.metadata
        }

# ============================================================================
# QUERY DECOMPOSER
# ============================================================================

class QueryDecomposer:
    """
    Zerlegt komplexe Queries in atomare Subqueries
    
    Features:
    - LLM-basierte Analyse der Query-Komplexität
    - Dependency-Graph-Validierung (DAG)
    - Capability-Matching für jede Subquery
    """
    
    DECOMPOSITION_PROMPT = """Du bist ein Query-Decomposer für ein deutsches Verwaltungs-KI-System.

**Aufgabe:** Zerlege die komplexe User-Query in atomare Subqueries.

**Regeln:**
1. Jede Subquery sollte von EINEM Spezial-Agent beantwortet werden können
2. Identifiziere Abhängigkeiten zwischen Subqueries (Execution-Order)
3. Vergib Prioritäten (1.0 = höchste Priorität, 0.0 = niedrigste)
4. Ordne passende Agent-Capabilities zu

**Verfügbare Query-Typen:**
- environmental_data: Umweltdaten (Luftqualität, Wasser, Abfall)
- authority_mapping: Zuständige Behörden und Kontakte
- legal_framework: Rechtliche Grundlagen und Gesetze
- construction_info: Baugenehmigungen und Baurecht
- financial_data: Haushalt, Förderungen, Ausgaben
- social_data: Demographie, Sozialleistungen, Bildung
- traffic_data: Verkehr, Parken, ÖPNV
- general_knowledge: Allgemeinwissen
- document_retrieval: Dokumentensuche

**Input Query:** {query_text}

**User Context:** {user_context}

**Output Format (JSON):**
[
    {{
        "query_text": "Konkrete Teilfrage...",
        "query_type": "environmental_data",
        "priority": 1.0,
        "dependencies": [],
        "required_capabilities": ["air_quality_monitoring", "environmental_data"]
    }},
    ...
]

**WICHTIG:** 
- Bei einfachen Queries: Nur 1 Subquery zurückgeben
- Bei komplexen Queries: 2-4 Subqueries
- Keine redundanten Subqueries
- Dependencies nur wenn wirklich notwendig

Antworte NUR mit dem JSON-Array, kein zusätzlicher Text!"""

    def __init__(self, ollama_client: VeritasOllamaClient):
        self.ollama_client = ollama_client
        self.stats = {
            'queries_decomposed': 0,
            'avg_subqueries_per_query': 0.0,
            'dependency_cycles_detected': 0
        }
    
    async def decompose_query(self, 
                             query_text: str, 
                             user_context: Dict[str, Any],
                             complexity_hint: Optional[str] = None) -> List[SubQuery]:
        """
        Zerlegt komplexe Query in Subqueries
        
        Args:
            query_text: Ursprüngliche User-Query
            user_context: User-Kontext (Location, etc.)
            complexity_hint: Optional - "simple", "standard", "complex"
        
        Returns:
            List[SubQuery]: Liste atomarer Subqueries
        """
        try:
            # Für sehr einfache Queries: Kein Decomposition nötig
            if complexity_hint == "simple" or len(query_text.split()) < 5:
                return self._create_single_subquery(query_text, user_context)
            
            # LLM Call
            prompt = self.DECOMPOSITION_PROMPT.format(
                query_text=query_text,
                user_context=json.dumps(user_context, indent=2, ensure_ascii=False)
            )
            
            ollama_request = OllamaRequest(
                model="llama3.2:latest",
                prompt=prompt,
                temperature=0.3,  # Niedriger für konsistente Struktur
                max_tokens=1500
            )
            
            llm_response = await self.ollama_client.generate_response(ollama_request)
            
            # Parse JSON
            response_text = llm_response.response
            subqueries_data = json.loads(response_text)
            
            # Validierung
            if not isinstance(subqueries_data, list):
                logger.warning("⚠️ LLM lieferte kein Array - Fallback auf Single-Subquery")
                return self._create_single_subquery(query_text, user_context)
            
            if len(subqueries_data) == 0:
                return self._create_single_subquery(query_text, user_context)
            
            # Subqueries erstellen
            subqueries = []
            for idx, sq_data in enumerate(subqueries_data):
                subquery = SubQuery(
                    id=f"sq_{uuid.uuid4().hex[:8]}",
                    query_text=sq_data.get("query_text", query_text),
                    query_type=sq_data.get("query_type", "general_knowledge"),
                    priority=float(sq_data.get("priority", 1.0 - (idx * 0.1))),
                    dependencies=sq_data.get("dependencies", []),
                    required_capabilities=sq_data.get("required_capabilities", []),
                    metadata={
                        "original_query": query_text,
                        "decomposition_index": idx
                        # user_context nicht in metadata (unhashable dict)
                    }
                )
                subqueries.append(subquery)
            
            # Dependency-Validierung (keine Zyklen)
            if not self._validate_dependency_graph(subqueries):
                logger.warning("⚠️ Zyklische Dependencies erkannt - entferne Dependencies")
                for sq in subqueries:
                    sq.dependencies = []
                self.stats['dependency_cycles_detected'] += 1
            
            # Statistiken
            self.stats['queries_decomposed'] += 1
            total_subqueries = len(subqueries) * self.stats['queries_decomposed']
            self.stats['avg_subqueries_per_query'] = total_subqueries / self.stats['queries_decomposed'] if self.stats['queries_decomposed'] > 0 else 0.0
            
            logger.info(f"✅ Query zerlegt in {len(subqueries)} Subqueries")
            return subqueries
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Parsing Error: {e}")
            return self._create_single_subquery(query_text, user_context)
        except Exception as e:
            logger.error(f"❌ Query Decomposition Error: {e}")
            return self._create_single_subquery(query_text, user_context)
    
    def _create_single_subquery(self, query_text: str, user_context: Dict[str, Any]) -> List[SubQuery]:
        """Fallback: Erstellt eine einzelne Subquery"""
        return [
            SubQuery(
                id=f"sq_{uuid.uuid4().hex[:8]}",
                query_text=query_text,
                query_type="general_knowledge",
                priority=1.0,
                dependencies=[],
                required_capabilities=["document_search"],
                metadata={"original_query": query_text, "fallback": True}
            )
        ]
    
    def _validate_dependency_graph(self, subqueries: List[SubQuery]) -> bool:
        """
        Validiert Dependency-Graph (DAG - Directed Acyclic Graph)
        
        Returns:
            True wenn gültig (keine Zyklen), False bei Zyklen
        """
        # Dependency-Graph aufbauen
        graph: Dict[str, Set[str]] = defaultdict(set)
        sq_ids = {sq.id for sq in subqueries}
        
        for sq in subqueries:
            for dep_id in sq.dependencies:
                if dep_id in sq_ids:
                    graph[sq.id].add(dep_id)
        
        # Zyklen-Detektion mit DFS
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for sq in subqueries:
            if sq.id not in visited:
                if has_cycle(sq.id):
                    return False
        
        return True

# ============================================================================
# AGENT SELECTOR
# ============================================================================

class AgentSelector:
    """
    Wählt optimale Spezial-Agents basierend auf Subquery-Requirements
    
    Features:
    - Capability-basiertes Matching
    - RAG-Context-Boosting
    - Confidence-Scoring
    """
    
    def __init__(self):
        self.agent_capability_map = AGENT_CAPABILITY_MAP
        self.stats = {
            'selections_performed': 0,
            'avg_confidence_score': 0.0,
            'agent_usage_counts': defaultdict(int)
        }
    
    async def select_agents(self, 
                           subquery: SubQuery, 
                           rag_context: Optional[Dict[str, Any]] = None) -> AgentSelection:
        """
        Wählt optimale Agents für Subquery
        
        Args:
            subquery: Subquery mit Required-Capabilities
            rag_context: Optional - RAG-Kontext für Context-Boosting
        
        Returns:
            AgentSelection: Selected + Fallback Agents
        """
        matches: List[AgentAssignment] = []
        
        # 1. Capability-basiertes Matching
        for agent_type, capabilities in self.agent_capability_map.items():
            capability_strs = [cap.value for cap in capabilities]
            match_score = self._calculate_capability_overlap(
                subquery.required_capabilities,
                capability_strs
            )
            
            if match_score > 0.3:  # Threshold
                matching_caps = list(
                    set(subquery.required_capabilities) & set(capability_strs)
                )
                matches.append(AgentAssignment(
                    agent_type=agent_type,
                    confidence_score=match_score,
                    matching_capabilities=matching_caps,
                    reason=f"Capability Match Score: {match_score:.2f}"
                ))
        
        # 2. RAG-Context-Boosting
        if rag_context:
            rag_documents = rag_context.get("documents", [])
            for doc in rag_documents:
                doc_metadata = doc.get("metadata", {})
                doc_domain = doc_metadata.get("domain", "")
                
                # Boost passende Agents
                if "environmental" in doc_domain.lower():
                    self._boost_agent(matches, "environmental", 0.2, "RAG-Context-Boost")
                elif "construction" in doc_domain.lower():
                    self._boost_agent(matches, "construction", 0.2, "RAG-Context-Boost")
                elif "legal" in doc_domain.lower():
                    self._boost_agent(matches, "legal_framework", 0.2, "RAG-Context-Boost")
        
        # 3. Fallback auf General-Agent
        if not matches:
            matches.append(AgentAssignment(
                agent_type="document_retrieval",
                confidence_score=0.4,
                reason="Fallback - Keine spezifischen Capabilities gemappt"
            ))
        
        # 4. Sortierung nach Confidence
        matches.sort(key=lambda m: m.confidence_score, reverse=True)
        
        # 5. Selektion: Top-1 als Selected, Rest als Fallbacks
        selected = matches[:1]
        fallbacks = matches[1:3]
        
        # Statistiken
        self.stats['selections_performed'] += 1
        if selected:
            self.stats['agent_usage_counts'][selected[0].agent_type] += 1
            total_conf = sum(m.confidence_score for m in matches)
            self.stats['avg_confidence_score'] = total_conf / len(matches) if matches else 0.0
        
        logger.info(f"✅ Agent Selected: {selected[0].agent_type if selected else 'None'} (Conf: {selected[0].confidence_score if selected else 0.0:.2f})")
        
        return AgentSelection(
            subquery_id=subquery.id,
            selected_agents=selected,
            fallback_agents=fallbacks
        )
    
    def _calculate_capability_overlap(self, 
                                      required: List[str], 
                                      available: List[str]) -> float:
        """
        Berechnet Overlap-Score zwischen Required und Available Capabilities
        
        Returns:
            Float: 0.0 - 1.0 (Jaccard-Ähnlichkeit)
        """
        if not required or not available:
            return 0.0
        
        required_set = set(required)
        available_set = set(available)
        
        intersection = len(required_set & available_set)
        union = len(required_set | available_set)
        
        return intersection / union if union > 0 else 0.0
    
    def _boost_agent(self, 
                    matches: List[AgentAssignment], 
                    agent_type: str, 
                    boost_value: float,
                    reason_suffix: str):
        """Erhöht Confidence-Score eines Agents"""
        for match in matches:
            if match.agent_type == agent_type:
                match.confidence_score = min(1.0, match.confidence_score + boost_value)
                match.reason += f" + {reason_suffix}"
                break

# ============================================================================
# RESULT SYNTHESIZER
# ============================================================================

class ResultSynthesizer:
    """
    Aggregiert Teilergebnisse zu kohärenter Antwort
    
    Features:
    - LLM-basierte Narrative-Generierung
    - Konflikt-Detektion und -Auflösung
    - Deduplizierung redundanter Informationen
    """
    
    SYNTHESIS_PROMPT = """Du bist ein Result-Synthesizer für ein deutsches Verwaltungs-KI-System.

**Aufgabe:** Aggregiere die Teilergebnisse verschiedener Spezial-Agents zu einer kohärenten, natürlichen Antwort.

**Original User-Query:** {original_query}

**Agent-Ergebnisse:**
{agent_results}

**Regeln:**
1. Beantworte die Original-Query vollständig und präzise
2. Integriere alle relevanten Informationen aus den Agent-Ergebnissen
3. Nutze eine klare, bürgerfreundliche Sprache
4. Nenne konkrete Fakten, Zahlen und Quellen
5. Strukturiere die Antwort logisch (bei Bedarf mit Aufzählungen)
6. Vermeide Wiederholungen und Redundanzen

**Ausgabeformat:**
Eine natürliche, kohärente Antwort in deutscher Sprache (max. 500 Wörter).

Antworte NUR mit der finalen Antwort, kein zusätzlicher Text!"""

    def __init__(self, ollama_client: VeritasOllamaClient):
        self.ollama_client = ollama_client
        self.stats = {
            'syntheses_performed': 0,
            'conflicts_detected': 0,
            'avg_confidence_score': 0.0
        }
    
    async def synthesize_results(self, 
                                agent_results: List[AgentResult],
                                original_query: str) -> SynthesizedResult:
        """
        Aggregiert Agent-Ergebnisse zu kohärenter Antwort
        ✨ ENHANCED: Nutzt EnhancedPromptTemplates (USER_FACING_MODE) mit IEEE-Zitationen
        
        Args:
            agent_results: Liste von Agent-Ergebnissen
            original_query: Ursprüngliche User-Query
        
        Returns:
            SynthesizedResult: Finale, synthesisierte Antwort
        """
        if not agent_results:
            return SynthesizedResult(
                response_text="Leider konnte ich keine passenden Informationen finden.",
                confidence_score=0.0,
                synthesis_method="fallback_empty"
            )
        
        try:
            # 1. Konflikt-Detektion
            conflicts = self._detect_contradictions(agent_results)
            if conflicts:
                logger.warning(f"⚠️ {len(conflicts)} Konflikte erkannt")
                self.stats['conflicts_detected'] += len(conflicts)
                agent_results = self._resolve_conflicts(agent_results, conflicts)
            
            # 2. Deduplizierung
            deduplicated = self._deduplicate_information(agent_results)
            
            # 3. ✨ NEW APPROACH: JSON-strukturierte Ausgabe statt direkter IEEE-Zitationen
            logger.info("[JSON SYNTHESIS] Nutze JSON Citation Formatter Approach")
            
            # Bereite RAG Context auf (aus Agent-Ergebnissen)
            rag_context_parts = []
            for i, agent_result in enumerate(deduplicated, 1):
                rag_context_parts.append(
                    f"[{i}] {agent_result.agent_type}: {agent_result.response_text}"
                )
            rag_context = "\n\n".join(rag_context_parts)
            
            # Bereite Source-List für Zitationen
            source_list = "\n".join([
                f"[{i}] Agent: {agent_result.agent_type} (Conf: {agent_result.confidence_score:.2f})"
                for i, agent_result in enumerate(deduplicated, 1)
            ])
            
            # Agent-Results als strukturierter Text
            agent_results_text = "\n\n".join([
                f"**{agent_result.agent_type}** (Confidence: {agent_result.confidence_score:.2f}):\n{agent_result.response_text}"
                for agent_result in deduplicated
            ])
            
            # 4. ✨ Build JSON Prompt (LLM gibt JSON zurück, wir formatieren zu IEEE)
            # Enable Rich Media for complex queries (maps, charts, tables)
            enable_rich_media = len(deduplicated) >= 3  # Rich media nur bei umfangreichen Antworten
            
            json_prompts = JSONCitationFormatter.get_json_prompt_template(
                enable_rich_media=enable_rich_media
            )
            
            logger.info(f"[JSON SYNTHESIS] Rich Media: {'✅ Enabled' if enable_rich_media else '❌ Disabled'}")
            
            system_prompt = json_prompts["system"]
            
            user_prompt = json_prompts["user_template"].format(
                query=original_query,
                rag_context=rag_context,
                agent_results=agent_results_text,
                source_list=source_list
            )
            
            # Kombiniere System + User Prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            logger.info(f"[JSON SYNTHESIS] Prompt: {len(full_prompt)} Zeichen, "
                       f"Quellen: {len(deduplicated)}, Format: JSON → IEEE")
            
            # 5. LLM Synthesis (mit JSON Output)
            ollama_request = OllamaRequest(
                model="llama3.2:latest",
                prompt=full_prompt,
                temperature=0.5,  # Mittel für strukturierte Ausgabe
                max_tokens=2000
            )
            
            llm_response = await self.ollama_client.generate_response(ollama_request)
            
            # 6. ✨ Format JSON Output zu IEEE-Standard
            raw_llm_output = llm_response.response
            
            logger.info(f"[JSON SYNTHESIS] Raw LLM Output: {len(raw_llm_output)} chars")
            logger.debug(f"[JSON SYNTHESIS] Raw output preview: {raw_llm_output[:200]}...")
            
            # Format JSON → IEEE
            synthesized_text, success = JSONCitationFormatter.format_with_fallback(raw_llm_output)
            
            if success:
                logger.info("✅ [JSON SYNTHESIS] Successfully formatted JSON → IEEE citations")
            else:
                logger.warning("⚠️ [JSON SYNTHESIS] Fallback to raw output (JSON parsing failed)")
            
            # 7. Confidence-Berechnung
            avg_confidence = sum(r.confidence_score for r in deduplicated) / len(deduplicated)
            
            # 8. Quellen extrahieren
            all_sources = []
            for result in deduplicated:
                all_sources.extend(result.sources)
            
            # Deduplizierung der Quellen
            unique_sources = []
            seen_sources = set()
            for source in all_sources:
                source_id = source.get("id") or source.get("title") or str(source)
                if source_id not in seen_sources:
                    unique_sources.append(source)
                    seen_sources.add(source_id)
            
            # 9. Subquery-Coverage
            subquery_coverage = {
                r.subquery_id: r.confidence_score 
                for r in deduplicated
            }
            
            # Statistiken
            self.stats['syntheses_performed'] += 1
            self.stats['avg_confidence_score'] = avg_confidence
            
            logger.info(f"✅ Result-Synthese abgeschlossen (Conf: {avg_confidence:.2f})")
            
            return SynthesizedResult(
                response_text=synthesized_text,
                confidence_score=avg_confidence,
                sources=unique_sources,
                subquery_coverage=subquery_coverage,
                conflicts_detected=conflicts,
                synthesis_method="llm_narrative_generation",
                metadata={
                    "agent_count": len(deduplicated),
                    "synthesis_timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Result-Synthese Error: {e}")
            # Fallback: Einfache Aggregation
            return self._simple_aggregation_fallback(agent_results, original_query)
    
    def _detect_contradictions(self, agent_results: List[AgentResult]) -> List[Dict[str, Any]]:
        """
        Detektiert Widersprüche zwischen Agent-Ergebnissen
        
        Returns:
            List[Dict]: Erkannte Konflikte
        """
        conflicts = []
        
        # Einfache Heuristik: Vergleiche numerische Werte
        numeric_data: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
        
        for result in agent_results:
            for key, value in result.result_data.items():
                if isinstance(value, (int, float)):
                    numeric_data[key].append((value, result.agent_type))
        
        # Prüfe auf signifikante Abweichungen
        for key, values in numeric_data.items():
            if len(values) > 1:
                nums = [v[0] for v in values]
                mean = sum(nums) / len(nums)
                for num, agent_type in values:
                    if abs(num - mean) / mean > 0.3:  # > 30% Abweichung
                        conflicts.append({
                            "key": key,
                            "value": num,
                            "agent_type": agent_type,
                            "mean": mean,
                            "deviation": abs(num - mean) / mean
                        })
        
        return conflicts
    
    def _resolve_conflicts(self, 
                          agent_results: List[AgentResult],
                          conflicts: List[Dict[str, Any]]) -> List[AgentResult]:
        """
        Löst Konflikte basierend auf Confidence-Scores
        
        Strategy: Höherer Confidence-Score gewinnt
        """
        # Sortiere nach Confidence (höher = besser)
        sorted_results = sorted(
            agent_results, 
            key=lambda r: r.confidence_score, 
            reverse=True
        )
        
        return sorted_results
    
    def _deduplicate_information(self, agent_results: List[AgentResult]) -> List[AgentResult]:
        """
        Entfernt redundante Informationen
        
        Strategy: Erste Occurrence bleibt, Rest wird entfernt
        """
        seen_data = set()
        deduplicated = []
        
        for result in agent_results:
            # Nutze JSON-Repr als Identifier
            data_repr = json.dumps(result.result_data, sort_keys=True)
            if data_repr not in seen_data:
                seen_data.add(data_repr)
                deduplicated.append(result)
        
        return deduplicated
    
    def _simple_aggregation_fallback(self, 
                                    agent_results: List[AgentResult],
                                    original_query: str) -> SynthesizedResult:
        """Fallback: Einfache Template-basierte Aggregation"""
        response_parts = []
        sources = []
        
        for result in agent_results:
            result_text = json.dumps(result.result_data, indent=2, ensure_ascii=False)
            response_parts.append(f"**{result.agent_type}:**\n{result_text}\n")
            sources.extend(result.sources)
        
        response_text = "\n".join(response_parts)
        avg_confidence = sum(r.confidence_score for r in agent_results) / len(agent_results)
        
        return SynthesizedResult(
            response_text=response_text,
            confidence_score=avg_confidence,
            sources=sources,
            synthesis_method="template_based_fallback"
        )

# ============================================================================
# SUPERVISOR AGENT (MAIN)
# ============================================================================

class SupervisorAgent:
    """
    Intelligenter Supervisor für Multi-Agent-Orchestrierung
    
    WORKFLOW:
    1. decompose_query() - Query Decomposition
    2. create_agent_plan() - Agent Selection pro Subquery
    3. orchestrate_execution() - Parallel/Sequential Execution
    4. synthesize_results() - Result Aggregation
    """
    
    def __init__(self, ollama_client: VeritasOllamaClient):
        """
        Initialisiert den Supervisor-Agent
        
        Args:
            ollama_client: VeritasOllamaClient für LLM-Calls
        """
        self.ollama_client = ollama_client
        
        # Sub-Komponenten
        self.decomposer = QueryDecomposer(ollama_client)
        self.selector = AgentSelector()
        self.synthesizer = ResultSynthesizer(ollama_client)
        
        # Statistics
        self.stats = {
            'queries_processed': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_processing_time': 0.0,
            'avg_processing_time': 0.0,
            'avg_subqueries_per_query': 0.0,
            'avg_agents_per_query': 0.0
        }
        
        logger.info("🎯 Supervisor-Agent initialisiert")
    
    async def decompose_query(self, 
                             query_text: str, 
                             user_context: Dict[str, Any],
                             complexity_hint: Optional[str] = None) -> List[SubQuery]:
        """
        Zerlegt komplexe Query in atomare Subqueries
        
        Args:
            query_text: User-Query
            user_context: User-Kontext
            complexity_hint: Optional - "simple", "standard", "complex"
        
        Returns:
            List[SubQuery]: Subqueries
        """
        return await self.decomposer.decompose_query(query_text, user_context, complexity_hint)
    
    async def create_agent_plan(self, 
                               subqueries: List[SubQuery],
                               rag_context: Optional[Dict[str, Any]] = None) -> AgentExecutionPlan:
        """
        Erstellt Execution-Plan mit parallelen und sequenziellen Agents
        
        Args:
            subqueries: Liste von Subqueries
            rag_context: Optional - RAG-Kontext für Boosting
        
        Returns:
            AgentExecutionPlan: Vollständiger Execution-Plan
        """
        parallel_agents: List[Tuple[str, AgentAssignment]] = []
        sequential_agents: List[Tuple[str, AgentAssignment]] = []
        dependency_graph: Dict[str, List[str]] = {}
        
        # Agent-Selektion für jede Subquery
        for subquery in subqueries:
            selection = await self.selector.select_agents(subquery, rag_context)
            
            if selection.selected_agents:
                agent_assignment = selection.selected_agents[0]
                
                # Dependency-Check
                if subquery.dependencies:
                    # Hat Dependencies → Sequential
                    sequential_agents.append((subquery.id, agent_assignment))
                    dependency_graph[subquery.id] = subquery.dependencies
                else:
                    # Keine Dependencies → Parallel
                    parallel_agents.append((subquery.id, agent_assignment))
        
        logger.info(f"📋 Agent-Plan erstellt: {len(parallel_agents)} parallel, {len(sequential_agents)} sequenziell")
        
        return AgentExecutionPlan(
            parallel_agents=parallel_agents,
            sequential_agents=sequential_agents,
            dependency_graph=dependency_graph,
            metadata={
                "total_subqueries": len(subqueries),
                "plan_created_at": datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def synthesize_results(self, 
                                agent_results: List[AgentResult],
                                original_query: str) -> SynthesizedResult:
        """
        Synthesisiert Agent-Ergebnisse zu finaler Antwort
        
        Args:
            agent_results: Agent-Ergebnisse
            original_query: Original-Query
        
        Returns:
            SynthesizedResult: Finale Antwort
        """
        return await self.synthesizer.synthesize_results(agent_results, original_query)
    
    def get_stats(self) -> Dict[str, Any]:
        """Liefert Supervisor-Statistiken"""
        return {
            "supervisor": self.stats,
            "decomposer": self.decomposer.stats,
            "selector": self.selector.stats,
            "synthesizer": self.synthesizer.stats
        }

# ============================================================================
# FACTORY & GLOBAL ACCESS
# ============================================================================

_global_supervisor_agent: Optional[SupervisorAgent] = None

async def get_supervisor_agent(ollama_client: Optional[VeritasOllamaClient] = None) -> SupervisorAgent:
    """
    Liefert globale Supervisor-Agent-Instanz
    
    Args:
        ollama_client: Optional - VeritasOllamaClient
    
    Returns:
        SupervisorAgent: Globale Instanz
    """
    global _global_supervisor_agent
    
    if _global_supervisor_agent is None:
        if ollama_client is None:
            from backend.agents.veritas_ollama_client import get_ollama_client
            ollama_client = await get_ollama_client()
        
        _global_supervisor_agent = SupervisorAgent(ollama_client)
    
    return _global_supervisor_agent

def create_supervisor_agent(ollama_client: VeritasOllamaClient) -> SupervisorAgent:
    """
    Factory für neue Supervisor-Agent-Instanz
    
    Args:
        ollama_client: VeritasOllamaClient
    
    Returns:
        SupervisorAgent: Neue Instanz
    """
    return SupervisorAgent(ollama_client)

# ============================================================================
# MAIN FOR TESTING
# ============================================================================

async def main():
    """Test des Supervisor-Agents"""
    from backend.agents.veritas_ollama_client import get_ollama_client
    
    print("🎯 Supervisor-Agent Test")
    print("=" * 60)
    
    # Initialisierung
    ollama_client = await get_ollama_client()
    supervisor = SupervisorAgent(ollama_client)
    
    # Test Query
    query = "Wie ist die Luftqualität in München und welche Behörden sind für Umweltschutz zuständig?"
    user_context = {"location": "München", "user_type": "citizen"}
    
    print(f"\n📝 Query: {query}")
    print(f"👤 Context: {user_context}")
    
    # Phase 1: Decomposition
    print("\n🔍 Phase 1: Query Decomposition")
    subqueries = await supervisor.decompose_query(query, user_context)
    print(f"✅ {len(subqueries)} Subqueries erstellt:")
    for sq in subqueries:
        print(f"   - [{sq.query_type}] {sq.query_text} (Prio: {sq.priority})")
    
    # Phase 2: Agent Plan
    print("\n🤖 Phase 2: Agent Selection")
    agent_plan = await supervisor.create_agent_plan(subqueries)
    print(f"✅ Agent-Plan: {len(agent_plan.parallel_agents)} parallel, {len(agent_plan.sequential_agents)} sequenziell")
    for sq_id, assignment in agent_plan.parallel_agents:
        print(f"   - Parallel: {assignment.agent_type} (Conf: {assignment.confidence_score:.2f})")
    
    # Phase 3: Orchestration (Mock)
    print("\n⚙️ Phase 3: Orchestration (MOCK)")
    mock_results = [
        AgentResult(
            subquery_id=subqueries[0].id,
            agent_type="environmental",
            result_data={"luftqualität": "gut", "pm10_wert": 25},
            confidence_score=0.92,
            sources=[{"title": "Bayerisches Landesamt für Umwelt"}]
        )
    ]
    if len(subqueries) > 1:
        mock_results.append(
            AgentResult(
                subquery_id=subqueries[1].id,
                agent_type="authority_mapping",
                result_data={"zuständige_behörden": ["Referat für Gesundheit und Umwelt"]},
                confidence_score=0.88,
                sources=[]
            )
        )
    print(f"✅ {len(mock_results)} Mock-Ergebnisse erstellt")
    
    # Phase 4: Synthesis
    print("\n🔗 Phase 4: Result Synthesis")
    final_result = await supervisor.synthesize_results(mock_results, query)
    print(f"✅ Finale Antwort (Conf: {final_result.confidence_score:.2f}):")
    print(f"\n{final_result.response_text}\n")
    
    # Statistiken
    print("\n📊 Supervisor-Statistiken:")
    stats = supervisor.get_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    print("\n✅ Test abgeschlossen!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
