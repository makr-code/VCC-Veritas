"""
Polyglot Execution Plan Analysis System
========================================

Kosten-Nutzen-Analyse für effiziente Query-Ausführung.
Basierend auf ThemisDB Kostenverfahren für Recherchepläne.

Features:
- Cost-Benefit Analysis (einfache ASK bis wissenschaftlich)
- Resource Analysis (LLM, SLM, NLP)
- Parallel Execution Planning
- Query Optimization

Design Pattern: Strategy + Chain of Responsibility
Author: VERITAS Backend Team
Date: 2025-12-03
Version: 1.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class ResourceType(Enum):
    """AI/ML Resource Types"""
    LLM_LARGE = "llm_large"          # GPT-4, Claude-3 (teuer, langsam, beste Qualität)
    LLM_MEDIUM = "llm_medium"        # GPT-3.5, Llama-70B (mittel)
    SLM_SMALL = "slm_small"          # Llama-7B, Phi-3 (schnell, günstig)
    NLP_TRADITIONAL = "nlp_trad"     # spaCy, NLTK (sehr schnell, günstig)
    VECTOR_SEARCH = "vector_search"  # Embedding-basiert
    GRAPH_TRAVERSAL = "graph"        # Neo4j, ThemisDB Graph
    FULLTEXT_SEARCH = "fulltext"     # Elasticsearch, PostgreSQL FTS


class QueryApproach(Enum):
    """Query-Ansatz nach wissenschaftlichem Niveau"""
    SIMPLE_ASK = "simple_ask"              # Einfache Frage-Antwort
    RESEARCH_BASIC = "research_basic"      # Grundlegende Recherche
    RESEARCH_DEEP = "research_deep"        # Tiefe Recherche mit Kontext
    SCIENTIFIC = "scientific"              # Wissenschaftlicher Ansatz
    EXPERT_ANALYSIS = "expert_analysis"    # Experten-Level-Analyse


class ExecutionMode(Enum):
    """Ausführungsmodus"""
    SEQUENTIAL = "sequential"      # Nacheinander
    PARALLEL = "parallel"         # Parallel
    PIPELINE = "pipeline"         # Pipeline (Stream)
    ADAPTIVE = "adaptive"         # Adaptiv basierend auf Ergebnissen


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ResourceCost:
    """
    Kosten für eine Ressource.
    
    Alle Kosten in relativen Einheiten (1.0 = Baseline)
    """
    computational_cost: float = 1.0    # CPU/GPU Kosten
    time_cost: float = 1.0             # Zeitkosten (Latency)
    monetary_cost: float = 1.0         # Monetäre Kosten (API calls)
    quality_score: float = 0.5         # Erwartete Qualität (0-1)
    
    @property
    def total_cost(self) -> float:
        """Gesamtkosten (gewichtet)"""
        return (
            self.computational_cost * 0.3 +
            self.time_cost * 0.4 +
            self.monetary_cost * 0.3
        )
    
    @property
    def cost_benefit_ratio(self) -> float:
        """Kosten-Nutzen-Verhältnis (höher = besser)"""
        if self.total_cost == 0:
            return float('inf')
        return self.quality_score / self.total_cost


@dataclass
class ExecutionStep:
    """
    Einzelner Schritt im Ausführungsplan.
    """
    step_id: str
    step_type: str
    resource_type: ResourceType
    estimated_cost: ResourceCost
    can_parallelize: bool = False
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """
    Vollständiger Ausführungsplan mit Kosten-Nutzen-Analyse.
    """
    plan_id: str
    approach: QueryApproach
    execution_mode: ExecutionMode
    steps: List[ExecutionStep] = field(default_factory=list)
    total_cost: ResourceCost = field(default_factory=ResourceCost)
    expected_quality: float = 0.0
    parallelization_factor: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def cost_benefit_score(self) -> float:
        """Kosten-Nutzen-Score des gesamten Plans"""
        return self.total_cost.cost_benefit_ratio
    
    @property
    def effective_time_cost(self) -> float:
        """Effektive Zeitkosten unter Berücksichtigung Parallelisierung"""
        return self.total_cost.time_cost / self.parallelization_factor


# ============================================================================
# Resource Cost Database
# ============================================================================

class ResourceCostDatabase:
    """
    Datenbank mit Kosten für verschiedene Ressourcen.
    
    Design Pattern: Repository Pattern
    """
    
    # Kosten-Matrix basierend auf empirischen Daten
    _costs: Dict[ResourceType, ResourceCost] = {
        # LLMs - Teuer, hohe Qualität
        ResourceType.LLM_LARGE: ResourceCost(
            computational_cost=10.0,
            time_cost=5.0,
            monetary_cost=10.0,
            quality_score=0.95
        ),
        ResourceType.LLM_MEDIUM: ResourceCost(
            computational_cost=5.0,
            time_cost=3.0,
            monetary_cost=5.0,
            quality_score=0.85
        ),
        
        # SLMs - Mittel, gute Balance
        ResourceType.SLM_SMALL: ResourceCost(
            computational_cost=2.0,
            time_cost=1.0,
            monetary_cost=1.0,
            quality_score=0.70
        ),
        
        # NLP Traditional - Schnell, günstig
        ResourceType.NLP_TRADITIONAL: ResourceCost(
            computational_cost=0.5,
            time_cost=0.2,
            monetary_cost=0.1,
            quality_score=0.50
        ),
        
        # Vector Search - Sehr schnell
        ResourceType.VECTOR_SEARCH: ResourceCost(
            computational_cost=1.0,
            time_cost=0.1,
            monetary_cost=0.5,
            quality_score=0.75
        ),
        
        # Graph Traversal - Schnell, mittlere Kosten
        ResourceType.GRAPH_TRAVERSAL: ResourceCost(
            computational_cost=2.0,
            time_cost=0.5,
            monetary_cost=1.0,
            quality_score=0.80
        ),
        
        # Fulltext Search - Sehr schnell, günstig
        ResourceType.FULLTEXT_SEARCH: ResourceCost(
            computational_cost=0.3,
            time_cost=0.1,
            monetary_cost=0.2,
            quality_score=0.60
        ),
    }
    
    @classmethod
    def get_cost(cls, resource_type: ResourceType) -> ResourceCost:
        """Hole Kosten für Ressourcen-Typ"""
        return cls._costs.get(resource_type, ResourceCost())
    
    @classmethod
    def register_cost(
        cls,
        resource_type: ResourceType,
        cost: ResourceCost
    ) -> None:
        """Registriere neue Kosten (für Custom Resources)"""
        cls._costs[resource_type] = cost


# ============================================================================
# Query Analyzer
# ============================================================================

class QueryAnalyzer:
    """
    Analysiert User-Query und bestimmt optimalen Ansatz.
    
    Design Pattern: Strategy Pattern
    """
    
    def __init__(self):
        self._cost_db = ResourceCostDatabase()
    
    def analyze_query(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QueryApproach:
        """
        Bestimme optimalen Query-Ansatz basierend auf Query-Komplexität.
        
        Strategie:
        - Einfache Fragen → SIMPLE_ASK
        - Recherche-Fragen → RESEARCH_BASIC/DEEP
        - Wissenschaftliche Fragen → SCIENTIFIC
        """
        context = context or {}
        
        # Einfache Heuristiken (kann durch ML ersetzt werden)
        query_length = len(user_query.split())
        
        # Keywords für wissenschaftlichen Ansatz
        scientific_keywords = {
            "studien", "forschung", "wissenschaftlich", "meta-analyse",
            "evidenz", "publikation", "peer-review"
        }
        
        # Keywords für tiefe Recherche
        research_keywords = {
            "vergleich", "analyse", "übersicht", "zusammenhang",
            "ursachen", "auswirkungen", "entwicklung"
        }
        
        query_lower = user_query.lower()
        
        # Wissenschaftlicher Ansatz
        if any(kw in query_lower for kw in scientific_keywords):
            return QueryApproach.SCIENTIFIC
        
        # Tiefe Recherche
        if any(kw in query_lower for kw in research_keywords) or query_length > 20:
            return QueryApproach.RESEARCH_DEEP
        
        # Grundlegende Recherche
        if query_length > 10:
            return QueryApproach.RESEARCH_BASIC
        
        # Einfache Frage
        return QueryApproach.SIMPLE_ASK
    
    def recommend_resources(
        self,
        approach: QueryApproach,
        budget: Optional[Dict[str, float]] = None
    ) -> List[ResourceType]:
        """
        Empfehle Ressourcen basierend auf Ansatz und Budget.
        
        Args:
            approach: Query-Ansatz
            budget: Budget-Limits (computational, time, monetary)
            
        Returns:
            Liste empfohlener Ressourcen
        """
        budget = budget or {
            "computational": float('inf'),
            "time": float('inf'),
            "monetary": float('inf')
        }
        
        # Ansatz-spezifische Empfehlungen
        recommendations = {
            QueryApproach.SIMPLE_ASK: [
                ResourceType.VECTOR_SEARCH,
                ResourceType.SLM_SMALL,
            ],
            QueryApproach.RESEARCH_BASIC: [
                ResourceType.VECTOR_SEARCH,
                ResourceType.FULLTEXT_SEARCH,
                ResourceType.SLM_SMALL,
            ],
            QueryApproach.RESEARCH_DEEP: [
                ResourceType.VECTOR_SEARCH,
                ResourceType.GRAPH_TRAVERSAL,
                ResourceType.LLM_MEDIUM,
            ],
            QueryApproach.SCIENTIFIC: [
                ResourceType.VECTOR_SEARCH,
                ResourceType.GRAPH_TRAVERSAL,
                ResourceType.FULLTEXT_SEARCH,
                ResourceType.LLM_LARGE,
            ],
            QueryApproach.EXPERT_ANALYSIS: [
                ResourceType.VECTOR_SEARCH,
                ResourceType.GRAPH_TRAVERSAL,
                ResourceType.LLM_LARGE,
                ResourceType.NLP_TRADITIONAL,  # Für Statistiken
            ],
        }
        
        # Filtere nach Budget
        resources = recommendations.get(approach, [])
        filtered = []
        
        for resource_type in resources:
            cost = self._cost_db.get_cost(resource_type)
            
            if (cost.computational_cost <= budget.get("computational", float('inf')) and
                cost.time_cost <= budget.get("time", float('inf')) and
                cost.monetary_cost <= budget.get("monetary", float('inf'))):
                filtered.append(resource_type)
        
        return filtered if filtered else resources[:2]  # Mindestens 2 Ressourcen


# ============================================================================
# Execution Plan Builder
# ============================================================================

class ExecutionPlanBuilder:
    """
    Erstellt optimierte Ausführungspläne.
    
    Design Pattern: Builder Pattern
    """
    
    def __init__(self):
        self._analyzer = QueryAnalyzer()
        self._cost_db = ResourceCostDatabase()
    
    def build_plan(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None,
        budget: Optional[Dict[str, float]] = None
    ) -> ExecutionPlan:
        """
        Erstelle optimierten Ausführungsplan.
        
        Pipeline:
        1. Analysiere Query → Bestimme Ansatz
        2. Empfehle Ressourcen basierend auf Ansatz & Budget
        3. Erstelle Execution Steps
        4. Optimiere für Parallelisierung
        5. Berechne Gesamt-Kosten
        """
        # 1. Analysiere Query
        approach = self._analyzer.analyze_query(user_query, context)
        
        # 2. Empfehle Ressourcen
        resources = self._analyzer.recommend_resources(approach, budget)
        
        # 3. Erstelle Steps
        steps = self._create_steps(resources, approach)
        
        # 4. Optimiere Parallelisierung
        execution_mode, parallelization_factor = self._optimize_parallelization(steps)
        
        # 5. Berechne Gesamt-Kosten
        total_cost, expected_quality = self._calculate_total_cost(steps, parallelization_factor)
        
        return ExecutionPlan(
            plan_id=f"plan_{hash(user_query)}",
            approach=approach,
            execution_mode=execution_mode,
            steps=steps,
            total_cost=total_cost,
            expected_quality=expected_quality,
            parallelization_factor=parallelization_factor,
            metadata={
                "user_query": user_query,
                "num_resources": len(resources)
            }
        )
    
    def _create_steps(
        self,
        resources: List[ResourceType],
        approach: QueryApproach
    ) -> List[ExecutionStep]:
        """Erstelle Execution Steps aus Ressourcen"""
        steps = []
        
        for i, resource_type in enumerate(resources):
            cost = self._cost_db.get_cost(resource_type)
            
            # Bestimme ob parallelisierbar
            can_parallel = resource_type in {
                ResourceType.VECTOR_SEARCH,
                ResourceType.FULLTEXT_SEARCH,
                ResourceType.GRAPH_TRAVERSAL
            }
            
            step = ExecutionStep(
                step_id=f"step_{i}_{resource_type.value}",
                step_type=resource_type.value,
                resource_type=resource_type,
                estimated_cost=cost,
                can_parallelize=can_parallel,
                depends_on=[] if can_parallel else [f"step_{i-1}_{resources[i-1].value}"] if i > 0 else []
            )
            steps.append(step)
        
        return steps
    
    def _optimize_parallelization(
        self,
        steps: List[ExecutionStep]
    ) -> tuple[ExecutionMode, float]:
        """
        Optimiere für Parallelisierung.
        
        Returns:
            (execution_mode, parallelization_factor)
        """
        # Zähle parallelisierbare Steps
        parallel_steps = sum(1 for step in steps if step.can_parallelize)
        total_steps = len(steps)
        
        if parallel_steps == 0:
            return ExecutionMode.SEQUENTIAL, 1.0
        
        if parallel_steps == total_steps:
            return ExecutionMode.PARALLEL, float(parallel_steps)
        
        if parallel_steps > total_steps / 2:
            return ExecutionMode.PIPELINE, 1.0 + (parallel_steps / total_steps)
        
        return ExecutionMode.ADAPTIVE, 1.0 + (parallel_steps / total_steps * 0.5)
    
    def _calculate_total_cost(
        self,
        steps: List[ExecutionStep],
        parallelization_factor: float
    ) -> tuple[ResourceCost, float]:
        """
        Berechne Gesamt-Kosten und erwartete Qualität.
        
        Returns:
            (total_cost, expected_quality)
        """
        # Summiere Kosten
        total_comp = sum(s.estimated_cost.computational_cost for s in steps)
        total_time = sum(s.estimated_cost.time_cost for s in steps) / parallelization_factor
        total_money = sum(s.estimated_cost.monetary_cost for s in steps)
        
        # Erwartete Qualität = Durchschnitt der besten 2 Ressourcen
        qualities = sorted([s.estimated_cost.quality_score for s in steps], reverse=True)
        expected_quality = sum(qualities[:2]) / min(2, len(qualities)) if qualities else 0.0
        
        total_cost = ResourceCost(
            computational_cost=total_comp,
            time_cost=total_time,
            monetary_cost=total_money,
            quality_score=expected_quality
        )
        
        return total_cost, expected_quality


# ============================================================================
# Plan Optimizer
# ============================================================================

class ExecutionPlanOptimizer:
    """
    Optimiert Ausführungspläne basierend auf verschiedenen Kriterien.
    
    Design Pattern: Strategy Pattern
    """
    
    def __init__(self):
        self._builder = ExecutionPlanBuilder()
    
    def optimize_for_speed(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """Optimiere für minimale Latenz"""
        budget = {
            "time": 1.0,  # Sehr strikt
            "computational": float('inf'),
            "monetary": float('inf')
        }
        return self._builder.build_plan(user_query, context, budget)
    
    def optimize_for_cost(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """Optimiere für minimale Kosten"""
        budget = {
            "time": float('inf'),
            "computational": 2.0,
            "monetary": 2.0
        }
        return self._builder.build_plan(user_query, context, budget)
    
    def optimize_for_quality(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """Optimiere für maximale Qualität"""
        budget = {
            "time": float('inf'),
            "computational": float('inf'),
            "monetary": float('inf')
        }
        return self._builder.build_plan(user_query, context, budget)
    
    def optimize_balanced(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """Balancierte Optimierung (Standard)"""
        budget = {
            "time": 5.0,
            "computational": 5.0,
            "monetary": 5.0
        }
        return self._builder.build_plan(user_query, context, budget)
    
    def compare_plans(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, ExecutionPlan]:
        """
        Vergleiche verschiedene Optimierungsstrategien.
        
        Returns:
            Dict mit Plan-Typ → ExecutionPlan
        """
        return {
            "speed": self.optimize_for_speed(user_query, context),
            "cost": self.optimize_for_cost(user_query, context),
            "quality": self.optimize_for_quality(user_query, context),
            "balanced": self.optimize_balanced(user_query, context)
        }


# ============================================================================
# Utilities
# ============================================================================

def format_execution_plan(plan: ExecutionPlan) -> str:
    """Formatiere Execution Plan für Logging/Debugging"""
    lines = [
        f"Execution Plan: {plan.plan_id}",
        f"  Approach: {plan.approach.value}",
        f"  Execution Mode: {plan.execution_mode.value}",
        f"  Total Cost: {plan.total_cost.total_cost:.2f}",
        f"  Expected Quality: {plan.expected_quality:.2%}",
        f"  Cost-Benefit Score: {plan.cost_benefit_score:.2f}",
        f"  Parallelization Factor: {plan.parallelization_factor:.1f}x",
        f"  Effective Time: {plan.effective_time_cost:.2f}",
        f"  Steps ({len(plan.steps)}):"
    ]
    
    for step in plan.steps:
        parallel_marker = "║" if step.can_parallelize else "│"
        lines.append(
            f"    {parallel_marker} {step.step_id}: {step.resource_type.value} "
            f"(cost: {step.estimated_cost.total_cost:.2f}, "
            f"quality: {step.estimated_cost.quality_score:.2%})"
        )
    
    return "\n".join(lines)
