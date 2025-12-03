"""
Integration Layer: Polyglot Execution Plan Analysis ↔ VERITAS Agent Framework
==============================================================================

Verbindet das neue Cost-Benefit-Analyse-System mit:
- VERITAS Agent Registry (veritas_api_agent_registry.py)
- IntelligentMultiAgentPipeline (veritas_intelligent_pipeline.py)
- AgentOrchestrator (veritas_api_agent_orchestrator.py)
- UnifiedOrchestratorV7 (unified_orchestrator_v7.py)

Author: VERITAS Backend Team
Date: 2025-12-03
Version: 1.0
"""

from __future__ import annotations

import logging
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from .execution_plan_analysis import (
    ResourceType,
    QueryApproach,
    ExecutionMode,
    ExecutionPlan,
    ExecutionPlanOptimizer,
    ResourceCostDatabase,
    ResourceCost,
)

logger = logging.getLogger(__name__)


# ============================================================================
# YAML Config Loader
# ============================================================================

class ResourceCostConfigLoader:
    """
    Lädt Kostenstatistik aus themisdb/config/resource_costs.yaml
    """
    
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "themisdb" / "config" / "resource_costs.yaml"
    
    @classmethod
    def load_config(cls, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Load resource cost configuration from YAML"""
        config_path = config_path or cls.DEFAULT_CONFIG_PATH
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ Loaded resource cost config from {config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            return {}
    
    @classmethod
    def sync_costs_to_database(cls, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Synchronisiere YAML-Config mit ResourceCostDatabase
        """
        config = config or cls.load_config()
        
        if not config or 'resources' not in config:
            logger.warning("No resources in config, skipping sync")
            return
        
        resources = config.get('resources', {})
        
        for resource_name, resource_data in resources.items():
            try:
                # Map YAML resource name to ResourceType enum
                resource_type = cls._map_yaml_to_resource_type(resource_name)
                
                if resource_type is None:
                    logger.debug(f"Skipping unknown resource: {resource_name}")
                    continue
                
                # Create ResourceCost from YAML data
                cost = ResourceCost(
                    computational_cost=resource_data.get('computational_cost', 1.0),
                    time_cost=resource_data.get('time_cost', 1.0),
                    monetary_cost=resource_data.get('monetary_cost', 1.0),
                    quality_score=resource_data.get('quality_score', 0.5)
                )
                
                # Register in database
                ResourceCostDatabase.register_cost(resource_type, cost)
                logger.debug(f"✅ Synced {resource_name} → {resource_type.value}")
                
            except Exception as e:
                logger.error(f"❌ Failed to sync {resource_name}: {e}")
        
        logger.info(f"✅ Synced {len(resources)} resources to cost database")
    
    @staticmethod
    def _map_yaml_to_resource_type(yaml_name: str) -> Optional[ResourceType]:
        """Map YAML resource name to ResourceType enum"""
        mapping = {
            'llm_large': ResourceType.LLM_LARGE,
            'llm_medium': ResourceType.LLM_MEDIUM,
            'slm_small': ResourceType.SLM_SMALL,
            'nlp_traditional': ResourceType.NLP_TRADITIONAL,
            'vector_search': ResourceType.VECTOR_SEARCH,
            'graph_traversal': ResourceType.GRAPH_TRAVERSAL,
            'fulltext_search': ResourceType.FULLTEXT_SEARCH,
        }
        return mapping.get(yaml_name)


# ============================================================================
# Agent Capability Mapper
# ============================================================================

class AgentCapabilityMapper:
    """
    Maps AgentCapabilities (from Agent Registry) to ResourceTypes (Execution Plan)
    
    Based on: backend/agents/veritas_shared_enums.py - AgentCapability
    """
    
    # Map AgentCapability → ResourceType
    CAPABILITY_TO_RESOURCE = {
        # LLM Capabilities
        'LLM_REASONING': ResourceType.LLM_LARGE,
        'COMPLEX_REASONING': ResourceType.LLM_LARGE,
        'HYPOTHESIS_GENERATION': ResourceType.LLM_MEDIUM,
        'SYNTHESIS': ResourceType.LLM_MEDIUM,
        
        # Search Capabilities
        'VECTOR_SEARCH': ResourceType.VECTOR_SEARCH,
        'SEMANTIC_SEARCH': ResourceType.VECTOR_SEARCH,
        'DOCUMENT_RETRIEVAL': ResourceType.VECTOR_SEARCH,
        'FULL_TEXT_SEARCH': ResourceType.FULLTEXT_SEARCH,
        
        # Graph Capabilities
        'GRAPH_TRAVERSAL': ResourceType.GRAPH_TRAVERSAL,
        'RELATIONSHIP_DISCOVERY': ResourceType.GRAPH_TRAVERSAL,
        'CONTEXT_ENRICHMENT': ResourceType.GRAPH_TRAVERSAL,
        
        # NLP Capabilities
        'NLP_ANALYSIS': ResourceType.NLP_TRADITIONAL,
        'TEXT_CLASSIFICATION': ResourceType.SLM_SMALL,
        'ENTITY_EXTRACTION': ResourceType.NLP_TRADITIONAL,
    }
    
    # Map QueryDomain → QueryApproach
    DOMAIN_TO_APPROACH = {
        'GENERAL': QueryApproach.SIMPLE_ASK,
        'ENVIRONMENTAL': QueryApproach.RESEARCH_BASIC,
        'BUILDING': QueryApproach.RESEARCH_BASIC,
        'LEGAL': QueryApproach.RESEARCH_DEEP,
        'FINANCIAL': QueryApproach.RESEARCH_DEEP,
        'SCIENTIFIC': QueryApproach.SCIENTIFIC,
        'TRANSPORT': QueryApproach.RESEARCH_BASIC,
    }
    
    @classmethod
    def map_capability_to_resource(cls, capability: str) -> Optional[ResourceType]:
        """Map agent capability to resource type"""
        return cls.CAPABILITY_TO_RESOURCE.get(capability)
    
    @classmethod
    def map_domain_to_approach(cls, domain: str) -> QueryApproach:
        """Map query domain to query approach"""
        return cls.DOMAIN_TO_APPROACH.get(domain, QueryApproach.RESEARCH_BASIC)


# ============================================================================
# Research Plan Integration
# ============================================================================

class ResearchPlanIntegration:
    """
    Integriert Execution Plan Analysis mit VERITAS Research Plan Schema
    
    Compatible with:
    - backend/database/research_plan_storage.py
    - backend/agents/framework/orchestration_controller.py
    - docs/AGENT_FRAMEWORK_QUICKSTART.md
    """
    
    @staticmethod
    def execution_plan_to_research_plan(
        plan: ExecutionPlan,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Convert ExecutionPlan to Research Plan Schema
        
        Args:
            plan: Execution plan from optimizer
            user_query: Original user query
            
        Returns:
            Research plan compatible with storage.create_plan()
        """
        import json
        from datetime import datetime
        
        # Generate plan_id
        plan_id = f"exec_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create steps from execution plan
        steps = []
        for idx, step in enumerate(plan.steps):
            steps.append({
                "step_id": step.step_id,
                "step_name": f"Execute {step.resource_type.value}",
                "step_type": step.step_type,
                "step_index": idx,
                "agent_name": step.step_type,
                "agent_type": step.resource_type.value,
                "depends_on": step.depends_on,
                "step_config": {
                    "resource_type": step.resource_type.value,
                    "estimated_cost": step.estimated_cost.total_cost,
                    "expected_quality": step.estimated_cost.quality_score,
                    "can_parallelize": step.can_parallelize
                }
            })
        
        # Create research plan
        research_plan = {
            "plan_id": plan_id,
            "research_question": user_query,
            "status": "pending",
            "total_steps": len(steps),
            "plan_document": json.dumps({
                "schema_version": "1.0",
                "research_question": user_query,
                "execution_plan_id": plan.plan_id,
                "approach": plan.approach.value,
                "execution_mode": plan.execution_mode.value,
                "expected_quality": plan.expected_quality,
                "total_cost": plan.total_cost.total_cost,
                "parallelization_factor": plan.parallelization_factor,
                "steps": steps
            }),
            "uds3_databases": ["chromadb", "neo4j", "postgres"],
            "phase5_hybrid_search": True,
            "security_level": "internal",
            "source_domains": ["environmental"],
        }
        
        return research_plan


# ============================================================================
# Intelligent Pipeline Integration
# ============================================================================

class IntelligentPipelineIntegration:
    """
    Integration mit IntelligentMultiAgentPipeline
    
    Based on: backend/agents/veritas_intelligent_pipeline.py
    """
    
    def __init__(self):
        self.optimizer = ExecutionPlanOptimizer()
        self.config = ResourceCostConfigLoader.load_config()
        
        # Sync costs from YAML
        ResourceCostConfigLoader.sync_costs_to_database(self.config)
    
    async def enhance_pipeline_request(
        self,
        query: str,
        domain: Optional[str] = None,
        complexity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhance pipeline request with execution plan
        
        Args:
            query: User query
            domain: Query domain (optional)
            complexity: Query complexity (optional)
            
        Returns:
            Enhanced request with execution plan metadata
        """
        # Map domain to approach
        if domain:
            approach = AgentCapabilityMapper.map_domain_to_approach(domain)
        else:
            approach = None
        
        # Create execution plan
        plan = self.optimizer.optimize_balanced(query)
        
        # Build enhanced request
        enhanced_request = {
            "query": query,
            "execution_plan": {
                "plan_id": plan.plan_id,
                "approach": plan.approach.value,
                "execution_mode": plan.execution_mode.value,
                "total_cost": plan.total_cost.total_cost,
                "expected_quality": plan.expected_quality,
                "parallelization_factor": plan.parallelization_factor,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "resource_type": step.resource_type.value,
                        "can_parallelize": step.can_parallelize,
                        "estimated_cost": step.estimated_cost.total_cost
                    }
                    for step in plan.steps
                ]
            },
            "metadata": {
                "cost_benefit_score": plan.cost_benefit_score,
                "effective_time_cost": plan.effective_time_cost
            }
        }
        
        return enhanced_request


# ============================================================================
# UnifiedOrchestratorV7 Integration
# ============================================================================

class UnifiedOrchestratorV7Integration:
    """
    Integration mit UnifiedOrchestratorV7
    
    Based on:
    - docs/AGENT_INTEGRATION_ANALYSIS.md
    - backend/orchestration/unified_orchestrator_v7.py
    """
    
    def __init__(self):
        self.optimizer = ExecutionPlanOptimizer()
        
        # Load costs from YAML
        ResourceCostConfigLoader.sync_costs_to_database()
    
    async def coordinate_agents(
        self,
        user_query: str,
        phase_results: Optional[Dict[str, Any]] = None,
        rag_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate agents based on execution plan
        
        Compatible with UnifiedOrchestratorV7._coordinate_agents()
        
        Args:
            user_query: Original query
            phase_results: Results from scientific phases (optional)
            rag_results: RAG search results (optional)
            
        Returns:
            Agent coordination results with execution metadata
        """
        import time
        start_time = time.time()
        
        # Create execution plan
        plan = self.optimizer.optimize_balanced(user_query)
        
        logger.info(f"🤖 Execution Plan: {plan.approach.value}, {len(plan.steps)} steps")
        
        # Extract missing information from phase results (if available)
        missing_info = []
        if phase_results and 'phase1_hypothesis' in phase_results:
            hypothesis = phase_results['phase1_hypothesis']
            missing_info = hypothesis.get('output', {}).get('missing_information', [])
        
        # Map missing info to agent requirements
        agent_requirements = self._map_missing_info_to_agents(missing_info, plan)
        
        if not agent_requirements:
            logger.info("ℹ️ No agents required (all info in plan)")
            return {
                'execution_plan_id': plan.plan_id,
                'approach': plan.approach.value,
                'total_cost': plan.total_cost.total_cost,
                'expected_quality': plan.expected_quality,
                'execution_time_ms': (time.time() - start_time) * 1000
            }
        
        logger.info(f"🤖 Agent requirements: {list(agent_requirements.keys())}")
        
        # Build agent coordination results
        coordination_result = {
            'execution_plan_id': plan.plan_id,
            'approach': plan.approach.value,
            'execution_mode': plan.execution_mode.value,
            'total_cost': plan.total_cost.total_cost,
            'expected_quality': plan.expected_quality,
            'parallelization_factor': plan.parallelization_factor,
            'agent_requirements': agent_requirements,
            'execution_time_ms': (time.time() - start_time) * 1000
        }
        
        return coordination_result
    
    def _map_missing_info_to_agents(
        self,
        missing_info: List[Dict[str, Any]],
        plan: ExecutionPlan
    ) -> Dict[str, str]:
        """
        Map missing information to agent capabilities
        
        Compatible with UnifiedOrchestratorV7._map_missing_info_to_agents()
        """
        agent_requirements = {}
        
        # If no missing info, use execution plan steps
        if not missing_info:
            for step in plan.steps:
                resource_type = step.resource_type
                
                # Map resource type to agent
                if resource_type == ResourceType.VECTOR_SEARCH:
                    agent_requirements['vector_search'] = 'VECTOR_SEARCH'
                elif resource_type == ResourceType.GRAPH_TRAVERSAL:
                    agent_requirements['graph'] = 'GRAPH_TRAVERSAL'
                elif resource_type == ResourceType.LLM_LARGE:
                    agent_requirements['llm'] = 'LLM_REASONING'
        else:
            # Map missing info to agents (keyword-based)
            for item in missing_info:
                desc = item.get('description', '').lower()
                
                if any(kw in desc for kw in ['baugenehmigung', 'carport', 'garage']):
                    agent_requirements['construction'] = 'BUILDING_PERMIT_PROCESSING'
                
                if any(kw in desc for kw in ['wetter', 'solar', 'temperatur']):
                    agent_requirements['weather'] = 'REAL_TIME_DATA_ACCESS'
                
                if any(kw in desc for kw in ['kosten', 'preis', 'finanzierung']):
                    agent_requirements['financial'] = 'FINANCIAL_IMPACT_ANALYSIS'
        
        return agent_requirements


# ============================================================================
# Factory Functions
# ============================================================================

def create_intelligent_pipeline_integration() -> IntelligentPipelineIntegration:
    """Create IntelligentPipelineIntegration instance"""
    return IntelligentPipelineIntegration()


def create_unified_orchestrator_integration() -> UnifiedOrchestratorV7Integration:
    """Create UnifiedOrchestratorV7Integration instance"""
    return UnifiedOrchestratorV7Integration()


def sync_costs_from_yaml(config_path: Optional[Path] = None) -> None:
    """
    Synchronize costs from YAML config to ResourceCostDatabase
    
    Usage:
        from backend.agents.themisdb.agent_framework_integration import sync_costs_from_yaml
        
        # At startup
        sync_costs_from_yaml()
    """
    ResourceCostConfigLoader.sync_costs_to_database(
        ResourceCostConfigLoader.load_config(config_path)
    )
    logger.info("✅ Costs synced from YAML to ResourceCostDatabase")
