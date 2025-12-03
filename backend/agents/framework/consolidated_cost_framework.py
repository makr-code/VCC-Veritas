"""
VERITAS Consolidated Agent Cost-Benefit Framework
==================================================

Konsolidiert:
1. Polyglot Execution Plan Analysis System (neu)
2. VERITAS Agent Framework (bestehend)
3. Research Plan Schema (bestehend)
4. IntelligentMultiAgentPipeline (bestehend)

Einheitliches System für:
- Agent-basierte Kosten-Nutzen-Analyse
- Research Plan Execution
- Multi-Agent Orchestration
- Cost-optimized Query Processing

Author: VERITAS Backend Team
Date: 2025-12-03
Version: 3.0 (Consolidated)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import yaml
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

# Import from existing VERITAS framework
try:
    from backend.agents.veritas_shared_enums import (
        AgentCapability,
        QueryDomain,
        QueryComplexity,
    )
    VERITAS_ENUMS_AVAILABLE = True
except ImportError:
    VERITAS_ENUMS_AVAILABLE = False
    # Fallback enums
    class AgentCapability(Enum):
        LLM_REASONING = "llm_reasoning"
        VECTOR_SEARCH = "vector_search"
    
    class QueryDomain(Enum):
        GENERAL = "general"
        ENVIRONMENTAL = "environmental"
    
    class QueryComplexity(Enum):
        SIMPLE = "simple"
        STANDARD = "standard"
        COMPLEX = "complex"

logger = logging.getLogger(__name__)


# ============================================================================
# Consolidated Enums (kombiniert bestehend + neu)
# ============================================================================

class ResourceType(Enum):
    """AI/ML Resource Types (erweitert um VERITAS Agent-Typen)"""
    # Language Models
    LLM_LARGE = "llm_large"
    LLM_MEDIUM = "llm_medium"
    SLM_SMALL = "slm_small"
    
    # Search & Retrieval
    VECTOR_SEARCH = "vector_search"
    GRAPH_TRAVERSAL = "graph_traversal"
    FULLTEXT_SEARCH = "fulltext_search"
    
    # Traditional NLP
    NLP_TRADITIONAL = "nlp_traditional"
    
    # VERITAS-specific (NEW)
    AGENT_CONSTRUCTION = "agent_construction"
    AGENT_ENVIRONMENTAL = "agent_environmental"
    AGENT_WEATHER = "agent_weather"
    AGENT_FINANCIAL = "agent_financial"
    AGENT_TRAFFIC = "agent_traffic"
    AGENT_SOCIAL = "agent_social"
    AGENT_TECHNICAL_STANDARDS = "agent_technical_standards"
    AGENT_WIKIPEDIA = "agent_wikipedia"


class QueryApproach(Enum):
    """Query-Ansatz (kompatibel mit QueryComplexity)"""
    SIMPLE_ASK = "simple_ask"              # QueryComplexity.SIMPLE
    RESEARCH_BASIC = "research_basic"      # QueryComplexity.STANDARD
    RESEARCH_DEEP = "research_deep"        # QueryComplexity.COMPLEX
    SCIENTIFIC = "scientific"              # Custom: wissenschaftlich
    EXPERT_ANALYSIS = "expert_analysis"    # Custom: Experten-Level


class ExecutionMode(Enum):
    """Ausführungsmodus"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    ADAPTIVE = "adaptive"


# ============================================================================
# Consolidated Data Classes
# ============================================================================

@dataclass
class AgentCostProfile:
    """
    Kosten-Profil für einen VERITAS-Agenten
    
    Kombiniert:
    - ResourceCost (Execution Plan Analysis)
    - Agent Performance Stats (Agent Framework)
    """
    agent_type: str
    agent_capability: str
    
    # Kosten (from Execution Plan Analysis)
    computational_cost: float = 1.0
    time_cost: float = 1.0
    monetary_cost: float = 1.0
    quality_score: float = 0.5
    
    # Performance Stats (from Agent Framework)
    avg_execution_time_ms: float = 1000.0
    success_rate: float = 0.95
    total_executions: int = 0
    
    # UDS3 Integration
    requires_uds3: bool = False
    uds3_databases: List[str] = field(default_factory=list)
    phase5_hybrid_search: bool = False
    
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
        """Kosten-Nutzen-Verhältnis"""
        if self.total_cost == 0:
            return float('inf')
        # Adjust quality by success rate
        adjusted_quality = self.quality_score * self.success_rate
        return adjusted_quality / self.total_cost
    
    @property
    def reliability_score(self) -> float:
        """Reliability basierend auf Erfolgsrate und Ausführungen"""
        if self.total_executions == 0:
            return 0.5  # Neutral for untested agents
        
        # Higher executions = more confident in success_rate
        confidence = min(self.total_executions / 100, 1.0)
        return self.success_rate * confidence


@dataclass
class ConsolidatedExecutionStep:
    """
    Execution Step (konsolidiert)
    
    Kombiniert:
    - ExecutionStep (Execution Plan Analysis)
    - Research Plan Step (Agent Framework)
    """
    step_id: str
    step_name: str
    step_index: int
    
    # Agent Assignment
    agent_type: str
    agent_capability: str
    resource_type: ResourceType
    
    # Execution
    cost_profile: AgentCostProfile
    can_parallelize: bool = False
    depends_on: List[str] = field(default_factory=list)
    
    # Research Plan Integration
    step_config: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending/running/completed/failed
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None


@dataclass
class ConsolidatedExecutionPlan:
    """
    Consolidated Execution Plan
    
    Kombiniert:
    - ExecutionPlan (Execution Plan Analysis)
    - Research Plan (Agent Framework)
    """
    plan_id: str
    research_question: str
    
    # Query Classification
    query_approach: QueryApproach
    query_domain: QueryDomain
    query_complexity: QueryComplexity
    
    # Execution Strategy
    execution_mode: ExecutionMode
    steps: List[ConsolidatedExecutionStep] = field(default_factory=list)
    
    # Cost-Benefit Analysis
    total_cost: float = 0.0
    expected_quality: float = 0.0
    parallelization_factor: float = 1.0
    
    # Research Plan Metadata
    status: str = "pending"
    total_steps: int = 0
    completed_steps: int = 0
    progress_percentage: float = 0.0
    
    # UDS3 Integration
    uds3_databases: List[str] = field(default_factory=list)
    phase5_hybrid_search: bool = True
    
    # Security & Source
    security_level: str = "internal"
    source_domains: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def cost_benefit_score(self) -> float:
        """Kosten-Nutzen-Score"""
        if self.total_cost == 0:
            return float('inf')
        return self.expected_quality / self.total_cost
    
    @property
    def effective_time_cost(self) -> float:
        """Effektive Zeit unter Berücksichtigung Parallelisierung"""
        return sum(
            s.cost_profile.time_cost for s in self.steps
        ) / self.parallelization_factor


# ============================================================================
# Consolidated Cost Database
# ============================================================================

class ConsolidatedCostDatabase:
    """
    Zentrale Kosten-Datenbank
    
    Kombiniert:
    - ResourceCostDatabase (Execution Plan Analysis)
    - Agent Performance Stats (Agent Framework)
    - YAML Config (themisdb/config/)
    """
    
    _cost_profiles: Dict[str, AgentCostProfile] = {}
    _config_loaded: bool = False
    
    @classmethod
    def register_profile(cls, agent_type: str, profile: AgentCostProfile) -> None:
        """Registriere Agent Cost Profile"""
        cls._cost_profiles[agent_type] = profile
        logger.debug(f"✅ Registered cost profile: {agent_type}")
    
    @classmethod
    def get_profile(cls, agent_type: str) -> Optional[AgentCostProfile]:
        """Hole Agent Cost Profile"""
        return cls._cost_profiles.get(agent_type)
    
    @classmethod
    def load_from_yaml(cls, config_path: Optional[Path] = None) -> None:
        """
        Load cost profiles from YAML
        
        Path: themisdb/config/resource_costs.yaml
        """
        if cls._config_loaded:
            logger.debug("Config already loaded, skipping")
            return
        
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent / "themisdb" / "config" / "resource_costs.yaml"
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            cls._load_defaults()
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            resources = config.get('resources', {})
            
            for resource_name, resource_data in resources.items():
                agent_type = resource_data.get('agent_type', resource_name)
                
                profile = AgentCostProfile(
                    agent_type=agent_type,
                    agent_capability=resource_data.get('capabilities', [])[0] if resource_data.get('capabilities') else resource_name,
                    computational_cost=resource_data.get('computational_cost', 1.0),
                    time_cost=resource_data.get('time_cost', 1.0),
                    monetary_cost=resource_data.get('monetary_cost', 1.0),
                    quality_score=resource_data.get('quality_score', 0.5),
                    requires_uds3=resource_data.get('uds3_database') is not None,
                    uds3_databases=[resource_data.get('uds3_database')] if resource_data.get('uds3_database') else [],
                    phase5_hybrid_search=resource_data.get('phase5_hybrid_search', False),
                )
                
                cls.register_profile(resource_name, profile)
            
            cls._config_loaded = True
            logger.info(f"✅ Loaded {len(resources)} cost profiles from YAML")
            
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            cls._load_defaults()
    
    @classmethod
    def _load_defaults(cls) -> None:
        """Load default cost profiles"""
        defaults = {
            'llm_large': AgentCostProfile(
                agent_type='LLMAgent',
                agent_capability='LLM_REASONING',
                computational_cost=10.0,
                time_cost=5.0,
                monetary_cost=10.0,
                quality_score=0.95
            ),
            'vector_search': AgentCostProfile(
                agent_type='VectorSearchAgent',
                agent_capability='VECTOR_SEARCH',
                computational_cost=1.0,
                time_cost=0.1,
                monetary_cost=0.5,
                quality_score=0.75,
                requires_uds3=True,
                uds3_databases=['chromadb'],
                phase5_hybrid_search=True
            ),
            'agent_construction': AgentCostProfile(
                agent_type='ConstructionAgent',
                agent_capability='BUILDING_PERMIT_PROCESSING',
                computational_cost=2.0,
                time_cost=1.5,
                monetary_cost=1.0,
                quality_score=0.85,
                requires_uds3=True,
                uds3_databases=['neo4j', 'postgres']
            ),
            'agent_environmental': AgentCostProfile(
                agent_type='EnvironmentalAgent',
                agent_capability='ENVIRONMENTAL_DATA',
                computational_cost=2.0,
                time_cost=1.0,
                monetary_cost=0.5,
                quality_score=0.80,
                requires_uds3=True,
                uds3_databases=['chromadb']
            ),
        }
        
        for agent_type, profile in defaults.items():
            cls.register_profile(agent_type, profile)
        
        cls._config_loaded = True
        logger.info(f"✅ Loaded {len(defaults)} default cost profiles")
    
    @classmethod
    def update_performance_stats(
        cls,
        agent_type: str,
        execution_time_ms: float,
        success: bool
    ) -> None:
        """
        Update performance statistics from actual execution
        
        Integriert mit Agent Monitoring System
        """
        profile = cls.get_profile(agent_type)
        
        if profile is None:
            logger.warning(f"No profile for {agent_type}, cannot update stats")
            return
        
        # Update running average
        n = profile.total_executions
        profile.avg_execution_time_ms = (
            (profile.avg_execution_time_ms * n + execution_time_ms) / (n + 1)
        )
        
        # Update success rate
        profile.success_rate = (
            (profile.success_rate * n + (1.0 if success else 0.0)) / (n + 1)
        )
        
        profile.total_executions += 1
        
        logger.debug(
            f"✅ Updated stats for {agent_type}: "
            f"avg_time={profile.avg_execution_time_ms:.0f}ms, "
            f"success_rate={profile.success_rate:.2%}"
        )


# ============================================================================
# Consolidated Plan Builder
# ============================================================================

class ConsolidatedPlanBuilder:
    """
    Builds consolidated execution plans
    
    Kombiniert:
    - ExecutionPlanBuilder (Execution Plan Analysis)
    - OrchestrationController (Agent Framework)
    - AgentOrchestrator (Multi-Agent System)
    """
    
    def __init__(self):
        # Load cost profiles
        ConsolidatedCostDatabase.load_from_yaml()
    
    def build_plan(
        self,
        research_question: str,
        query_domain: Optional[QueryDomain] = None,
        query_complexity: Optional[QueryComplexity] = None,
        budget: Optional[Dict[str, float]] = None
    ) -> ConsolidatedExecutionPlan:
        """
        Build consolidated execution plan
        
        Args:
            research_question: User query
            query_domain: Domain (optional, auto-detected)
            query_complexity: Complexity (optional, auto-detected)
            budget: Budget constraints
            
        Returns:
            Consolidated execution plan
        """
        # 1. Detect query properties
        query_approach = self._detect_approach(research_question)
        query_domain = query_domain or self._detect_domain(research_question)
        query_complexity = query_complexity or self._detect_complexity(research_question)
        
        # 2. Select agents based on approach & domain
        selected_agents = self._select_agents(
            query_approach,
            query_domain,
            query_complexity,
            budget
        )
        
        # 3. Create execution steps
        steps = self._create_steps(selected_agents, query_approach)
        
        # 4. Optimize parallelization
        execution_mode, parallelization_factor = self._optimize_parallelization(steps)
        
        # 5. Calculate costs
        total_cost, expected_quality = self._calculate_total_cost(steps, parallelization_factor)
        
        # 6. Determine UDS3 requirements
        uds3_databases = self._collect_uds3_databases(steps)
        
        # 7. Build plan
        plan_id = f"consolidated_plan_{int(time.time())}"
        
        plan = ConsolidatedExecutionPlan(
            plan_id=plan_id,
            research_question=research_question,
            query_approach=query_approach,
            query_domain=query_domain,
            query_complexity=query_complexity,
            execution_mode=execution_mode,
            steps=steps,
            total_cost=total_cost,
            expected_quality=expected_quality,
            parallelization_factor=parallelization_factor,
            total_steps=len(steps),
            uds3_databases=uds3_databases,
            phase5_hybrid_search=any(s.cost_profile.phase5_hybrid_search for s in steps),
            source_domains=[query_domain.value] if query_domain else []
        )
        
        logger.info(
            f"✅ Built plan: {plan.query_approach.value}, "
            f"{len(steps)} steps, "
            f"cost={total_cost:.2f}, "
            f"quality={expected_quality:.2%}"
        )
        
        return plan
    
    def _detect_approach(self, query: str) -> QueryApproach:
        """Detect query approach from query text"""
        query_lower = query.lower()
        query_length = len(query.split())
        
        # Scientific keywords
        if any(kw in query_lower for kw in ['wissenschaftlich', 'studie', 'forschung', 'evidenz']):
            return QueryApproach.SCIENTIFIC
        
        # Deep research keywords
        if any(kw in query_lower for kw in ['analyse', 'vergleich', 'übersicht', 'zusammenhang']):
            return QueryApproach.RESEARCH_DEEP
        
        # Basic research
        if query_length > 10:
            return QueryApproach.RESEARCH_BASIC
        
        # Simple
        return QueryApproach.SIMPLE_ASK
    
    def _detect_domain(self, query: str) -> QueryDomain:
        """Detect query domain"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ['bau', 'carport', 'garage', 'genehmigung']):
            return QueryDomain.BUILDING if VERITAS_ENUMS_AVAILABLE else QueryDomain.GENERAL
        
        if any(kw in query_lower for kw in ['umwelt', 'luft', 'wasser', 'emission']):
            return QueryDomain.ENVIRONMENTAL
        
        return QueryDomain.GENERAL
    
    def _detect_complexity(self, query: str) -> QueryComplexity:
        """Detect query complexity"""
        query_length = len(query.split())
        
        if query_length < 10:
            return QueryComplexity.SIMPLE
        elif query_length < 20:
            return QueryComplexity.STANDARD
        else:
            return QueryComplexity.COMPLEX
    
    def _select_agents(
        self,
        approach: QueryApproach,
        domain: QueryDomain,
        complexity: QueryComplexity,
        budget: Optional[Dict[str, float]]
    ) -> List[str]:
        """Select agents based on approach, domain, and budget"""
        # Approach-based selection
        approach_agents = {
            QueryApproach.SIMPLE_ASK: ['vector_search', 'slm_small'],
            QueryApproach.RESEARCH_BASIC: ['vector_search', 'fulltext_search', 'slm_small'],
            QueryApproach.RESEARCH_DEEP: ['vector_search', 'graph_traversal', 'llm_medium'],
            QueryApproach.SCIENTIFIC: ['vector_search', 'graph_traversal', 'fulltext_search', 'llm_large'],
            QueryApproach.EXPERT_ANALYSIS: ['vector_search', 'graph_traversal', 'llm_large', 'nlp_traditional'],
        }
        
        agents = approach_agents.get(approach, ['vector_search'])
        
        # Domain-specific agents
        if domain == QueryDomain.BUILDING:
            agents.append('agent_construction')
        elif domain == QueryDomain.ENVIRONMENTAL:
            agents.append('agent_environmental')
            agents.append('agent_weather')
        
        # Filter by budget
        if budget:
            filtered_agents = []
            for agent in agents:
                profile = ConsolidatedCostDatabase.get_profile(agent)
                if profile and self._fits_budget(profile, budget):
                    filtered_agents.append(agent)
            agents = filtered_agents if filtered_agents else agents[:2]  # Minimum 2
        
        return agents
    
    def _fits_budget(self, profile: AgentCostProfile, budget: Dict[str, float]) -> bool:
        """Check if profile fits within budget"""
        return (
            profile.computational_cost <= budget.get('computational', float('inf')) and
            profile.time_cost <= budget.get('time', float('inf')) and
            profile.monetary_cost <= budget.get('monetary', float('inf'))
        )
    
    def _create_steps(
        self,
        agent_types: List[str],
        approach: QueryApproach
    ) -> List[ConsolidatedExecutionStep]:
        """Create execution steps from agent types"""
        steps = []
        
        for idx, agent_type in enumerate(agent_types):
            profile = ConsolidatedCostDatabase.get_profile(agent_type)
            
            if profile is None:
                logger.warning(f"No profile for {agent_type}, skipping")
                continue
            
            # Map agent type to resource type
            resource_type = self._map_agent_to_resource(agent_type)
            
            step = ConsolidatedExecutionStep(
                step_id=f"step_{idx:03d}_{agent_type}",
                step_name=f"Execute {agent_type}",
                step_index=idx,
                agent_type=profile.agent_type,
                agent_capability=profile.agent_capability,
                resource_type=resource_type,
                cost_profile=profile,
                can_parallelize=self._is_parallelizable(agent_type),
                depends_on=[] if self._is_parallelizable(agent_type) else (
                    [steps[idx-1].step_id] if idx > 0 else []
                ),
                step_config={
                    'agent_type': agent_type,
                    'estimated_cost': profile.total_cost,
                    'expected_quality': profile.quality_score,
                    'requires_uds3': profile.requires_uds3,
                    'uds3_databases': profile.uds3_databases,
                }
            )
            
            steps.append(step)
        
        return steps
    
    def _map_agent_to_resource(self, agent_type: str) -> ResourceType:
        """Map agent type string to ResourceType enum"""
        mapping = {
            'llm_large': ResourceType.LLM_LARGE,
            'llm_medium': ResourceType.LLM_MEDIUM,
            'slm_small': ResourceType.SLM_SMALL,
            'vector_search': ResourceType.VECTOR_SEARCH,
            'graph_traversal': ResourceType.GRAPH_TRAVERSAL,
            'fulltext_search': ResourceType.FULLTEXT_SEARCH,
            'nlp_traditional': ResourceType.NLP_TRADITIONAL,
            'agent_construction': ResourceType.AGENT_CONSTRUCTION,
            'agent_environmental': ResourceType.AGENT_ENVIRONMENTAL,
            'agent_weather': ResourceType.AGENT_WEATHER,
            'agent_financial': ResourceType.AGENT_FINANCIAL,
        }
        return mapping.get(agent_type, ResourceType.VECTOR_SEARCH)
    
    def _is_parallelizable(self, agent_type: str) -> bool:
        """Check if agent can run in parallel"""
        parallelizable = {
            'vector_search', 'fulltext_search', 'graph_traversal',
            'agent_construction', 'agent_environmental', 'agent_weather',
            'agent_financial', 'agent_traffic'
        }
        return agent_type in parallelizable
    
    def _optimize_parallelization(
        self,
        steps: List[ConsolidatedExecutionStep]
    ) -> tuple[ExecutionMode, float]:
        """Optimize parallelization"""
        parallel_steps = sum(1 for s in steps if s.can_parallelize)
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
        steps: List[ConsolidatedExecutionStep],
        parallelization_factor: float
    ) -> tuple[float, float]:
        """Calculate total cost and expected quality"""
        total_comp = sum(s.cost_profile.computational_cost for s in steps)
        total_time = sum(s.cost_profile.time_cost for s in steps) / parallelization_factor
        total_money = sum(s.cost_profile.monetary_cost for s in steps)
        
        # Total cost (weighted)
        total_cost = total_comp * 0.3 + total_time * 0.4 + total_money * 0.3
        
        # Expected quality = average of top 2 agents
        qualities = sorted([s.cost_profile.quality_score for s in steps], reverse=True)
        expected_quality = sum(qualities[:2]) / min(2, len(qualities)) if qualities else 0.0
        
        return total_cost, expected_quality
    
    def _collect_uds3_databases(
        self,
        steps: List[ConsolidatedExecutionStep]
    ) -> List[str]:
        """Collect required UDS3 databases"""
        databases = set()
        for step in steps:
            if step.cost_profile.requires_uds3:
                databases.update(step.cost_profile.uds3_databases)
        return list(databases)


# ============================================================================
# Factory Function
# ============================================================================

def create_consolidated_plan(
    research_question: str,
    query_domain: Optional[str] = None,
    query_complexity: Optional[str] = None,
    budget: Optional[Dict[str, float]] = None
) -> ConsolidatedExecutionPlan:
    """
    Create consolidated execution plan
    
    Usage:
        from backend.agents.themisdb import create_consolidated_plan
        
        plan = create_consolidated_plan(
            "Brauche ich Baugenehmigung für Carport?",
            query_domain="BUILDING",
            budget={"time": 5.0, "monetary": 3.0}
        )
    """
    builder = ConsolidatedPlanBuilder()
    
    # Convert string enums
    domain = QueryDomain[query_domain] if query_domain else None
    complexity = QueryComplexity[query_complexity] if query_complexity else None
    
    return builder.build_plan(
        research_question=research_question,
        query_domain=domain,
        query_complexity=complexity,
        budget=budget
    )


# ============================================================================
# Export
# ============================================================================

__all__ = [
    # Enums
    'ResourceType',
    'QueryApproach',
    'ExecutionMode',
    
    # Data Classes
    'AgentCostProfile',
    'ConsolidatedExecutionStep',
    'ConsolidatedExecutionPlan',
    
    # Core Classes
    'ConsolidatedCostDatabase',
    'ConsolidatedPlanBuilder',
    
    # Factory
    'create_consolidated_plan',
]
