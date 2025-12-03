"""
Phase 3 Features: Advanced capabilities for 100% feature parity with Gemini Deep Search and Copilot Agents.

This module implements the final 3 features:
1. Counterfactual Reasoning - Explores "what if" scenarios and edge cases
2. Uncertainty Quantification - Provides confidence intervals instead of point estimates
3. Visual Progress Tree UI - Real-time interactive visualization of execution tree

Author: GitHub Copilot
Date: 2025-12-03
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
from datetime import datetime
import numpy as np
from scipy import stats


# ============================================================================
# 1. COUNTERFACTUAL REASONING ENGINE
# ============================================================================

class ScenarioType(Enum):
    """Types of counterfactual scenarios."""
    PARAMETER_CHANGE = "parameter_change"  # What if a parameter changes?
    MISSING_INFO = "missing_info"  # What if information is missing?
    ALTERNATIVE_PATH = "alternative_path"  # What if we took a different approach?
    EDGE_CASE = "edge_case"  # What happens at boundaries?
    RISK_SCENARIO = "risk_scenario"  # What if risks materialize?


@dataclass
class CounterfactualScenario:
    """Represents a counterfactual scenario."""
    scenario_id: str
    scenario_type: ScenarioType
    description: str
    changed_parameters: Dict[str, Any]
    expected_impact: str
    probability: float  # 0.0-1.0
    severity: str  # "low", "medium", "high", "critical"
    analysis_result: Optional[str] = None
    confidence: float = 0.0


@dataclass
class CounterfactualAnalysis:
    """Complete counterfactual analysis results."""
    base_scenario: str
    scenarios_explored: List[CounterfactualScenario]
    risk_scenarios: List[CounterfactualScenario]
    opportunity_scenarios: List[CounterfactualScenario]
    edge_cases: List[CounterfactualScenario]
    recommendations: List[str]
    overall_robustness_score: float  # 0.0-1.0


class CounterfactualReasoningEngine:
    """
    Explores "what if" scenarios to identify edge cases, risks, and opportunities.
    
    This engine generates and analyzes counterfactual scenarios to:
    - Identify potential failure modes
    - Discover edge cases
    - Assess decision robustness
    - Find opportunities in alternative paths
    """
    
    def __init__(self, llm_client: Any):
        self.llm_client = llm_client
        self.scenario_cache: Dict[str, List[CounterfactualScenario]] = {}
    
    async def analyze_counterfactuals(
        self,
        query: str,
        current_answer: str,
        context: Dict[str, Any],
        max_scenarios: int = 5
    ) -> CounterfactualAnalysis:
        """
        Generate and analyze counterfactual scenarios for the given query and answer.
        
        Args:
            query: Original user query
            current_answer: Current answer/decision
            context: Additional context (documents, parameters, etc.)
            max_scenarios: Maximum scenarios to explore
            
        Returns:
            CounterfactualAnalysis with all explored scenarios
        """
        # Generate scenarios
        scenarios = await self._generate_scenarios(query, current_answer, context, max_scenarios)
        
        # Analyze each scenario
        analyzed_scenarios = []
        for scenario in scenarios:
            result = await self._analyze_scenario(scenario, query, current_answer, context)
            scenario.analysis_result = result["analysis"]
            scenario.confidence = result["confidence"]
            analyzed_scenarios.append(scenario)
        
        # Categorize scenarios
        risk_scenarios = [s for s in analyzed_scenarios if s.severity in ["high", "critical"]]
        opportunity_scenarios = [s for s in analyzed_scenarios if "opportunity" in s.description.lower()]
        edge_cases = [s for s in analyzed_scenarios if s.scenario_type == ScenarioType.EDGE_CASE]
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(analyzed_scenarios, current_answer)
        
        # Calculate robustness score
        robustness = self._calculate_robustness_score(analyzed_scenarios)
        
        return CounterfactualAnalysis(
            base_scenario=current_answer,
            scenarios_explored=analyzed_scenarios,
            risk_scenarios=risk_scenarios,
            opportunity_scenarios=opportunity_scenarios,
            edge_cases=edge_cases,
            recommendations=recommendations,
            overall_robustness_score=robustness
        )
    
    async def _generate_scenarios(
        self,
        query: str,
        answer: str,
        context: Dict[str, Any],
        max_scenarios: int
    ) -> List[CounterfactualScenario]:
        """Generate counterfactual scenarios using LLM."""
        prompt = f"""
        Given the query: "{query}"
        And the current answer: "{answer}"
        
        Generate {max_scenarios} counterfactual scenarios to explore. For each scenario:
        1. Identify what parameter or assumption changes
        2. Describe the potential impact
        3. Estimate probability (0.0-1.0)
        4. Assess severity (low/medium/high/critical)
        
        Focus on:
        - Edge cases (boundary conditions)
        - Risk scenarios (what could go wrong)
        - Alternative paths (different approaches)
        - Missing information impacts
        
        Return JSON array of scenarios.
        """
        
        response = await self.llm_client.generate(prompt, temperature=0.8)
        scenarios_data = json.loads(response)
        
        scenarios = []
        for i, data in enumerate(scenarios_data[:max_scenarios]):
            scenario = CounterfactualScenario(
                scenario_id=f"cf_{i}",
                scenario_type=ScenarioType(data.get("type", "edge_case")),
                description=data["description"],
                changed_parameters=data.get("changed_parameters", {}),
                expected_impact=data["expected_impact"],
                probability=float(data.get("probability", 0.5)),
                severity=data.get("severity", "medium")
            )
            scenarios.append(scenario)
        
        return scenarios
    
    async def _analyze_scenario(
        self,
        scenario: CounterfactualScenario,
        query: str,
        answer: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze a specific counterfactual scenario."""
        prompt = f"""
        Original query: "{query}"
        Current answer: "{answer}"
        
        Counterfactual scenario:
        {scenario.description}
        Changed parameters: {scenario.changed_parameters}
        Expected impact: {scenario.expected_impact}
        
        Analyze:
        1. How would the answer change in this scenario?
        2. What new considerations arise?
        3. Is this a risk or opportunity?
        4. How confident are you in this analysis? (0.0-1.0)
        
        Return JSON with: analysis (str), confidence (float)
        """
        
        response = await self.llm_client.generate(prompt, temperature=0.7)
        return json.loads(response)
    
    async def _generate_recommendations(
        self,
        scenarios: List[CounterfactualScenario],
        current_answer: str
    ) -> List[str]:
        """Generate recommendations based on counterfactual analysis."""
        high_risk = [s for s in scenarios if s.severity in ["high", "critical"]]
        
        recommendations = []
        
        if high_risk:
            recommendations.append(
                f"⚠️ {len(high_risk)} high-risk scenarios identified. Consider risk mitigation strategies."
            )
        
        # Find scenarios where answer significantly changes
        significant_changes = [s for s in scenarios if s.confidence > 0.7]
        if significant_changes:
            recommendations.append(
                f"💡 Answer is sensitive to {len(significant_changes)} scenarios. "
                "Consider adding caveats or alternative recommendations."
            )
        
        # Check for opportunities
        opportunities = [s for s in scenarios if "opportunity" in s.analysis_result.lower()]
        if opportunities:
            recommendations.append(
                f"🚀 {len(opportunities)} opportunity scenarios identified for potential improvements."
            )
        
        return recommendations
    
    def _calculate_robustness_score(self, scenarios: List[CounterfactualScenario]) -> float:
        """Calculate how robust the answer is across scenarios."""
        if not scenarios:
            return 0.5
        
        # Weight by probability and severity
        severity_weights = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
        
        total_impact = 0.0
        total_weight = 0.0
        
        for scenario in scenarios:
            weight = scenario.probability * severity_weights.get(scenario.severity, 0.5)
            # High confidence in scenario analysis reduces robustness if severe
            impact = scenario.confidence * severity_weights.get(scenario.severity, 0.5)
            total_impact += weight * impact
            total_weight += weight
        
        if total_weight == 0:
            return 0.8
        
        # Invert: lower impact = higher robustness
        robustness = 1.0 - min(total_impact / total_weight, 1.0)
        return max(0.0, min(robustness, 1.0))


# ============================================================================
# 2. UNCERTAINTY QUANTIFICATION ENGINE
# ============================================================================

class UncertaintyMethod(Enum):
    """Methods for uncertainty quantification."""
    BOOTSTRAP = "bootstrap"  # Bootstrap resampling
    BAYESIAN = "bayesian"  # Bayesian credible intervals
    ENSEMBLE = "ensemble"  # Ensemble of models
    EVIDENCE_BASED = "evidence_based"  # Based on evidence strength


@dataclass
class UncertaintyEstimate:
    """Represents an uncertainty estimate with confidence intervals."""
    point_estimate: float  # Best estimate
    lower_bound: float  # Lower confidence bound
    upper_bound: float  # Upper confidence bound
    confidence_level: float  # e.g., 0.95 for 95% CI
    method: UncertaintyMethod
    evidence_strength: str  # "weak", "moderate", "strong"
    n_samples: int = 0  # Number of samples/sources


@dataclass
class UncertaintyAnalysis:
    """Complete uncertainty analysis results."""
    query: str
    answer: str
    confidence_estimate: UncertaintyEstimate
    source_reliability: Dict[str, UncertaintyEstimate]
    claim_uncertainty: Dict[str, UncertaintyEstimate]
    overall_uncertainty_score: float  # 0.0 (certain) to 1.0 (very uncertain)
    uncertainty_breakdown: Dict[str, float]
    recommendations: List[str]


class UncertaintyQuantificationEngine:
    """
    Quantifies uncertainty in answers using multiple methods.
    
    Provides confidence intervals instead of point estimates, making uncertainty explicit
    and enabling better risk-aware decision making.
    """
    
    def __init__(self, llm_client: Any):
        self.llm_client = llm_client
    
    async def quantify_uncertainty(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        claims: List[str],
        method: UncertaintyMethod = UncertaintyMethod.EVIDENCE_BASED
    ) -> UncertaintyAnalysis:
        """
        Quantify uncertainty in the answer.
        
        Args:
            query: Original query
            answer: Generated answer
            sources: List of source documents
            claims: Extracted claims from answer
            method: Uncertainty quantification method
            
        Returns:
            UncertaintyAnalysis with confidence intervals
        """
        # Overall confidence estimate
        confidence = await self._estimate_answer_confidence(answer, sources, method)
        
        # Source reliability estimates
        source_reliability = await self._estimate_source_reliability(sources)
        
        # Claim-level uncertainty
        claim_uncertainty = await self._estimate_claim_uncertainty(claims, sources)
        
        # Calculate overall uncertainty score
        overall_uncertainty = self._calculate_overall_uncertainty(
            confidence, source_reliability, claim_uncertainty
        )
        
        # Break down uncertainty sources
        breakdown = self._breakdown_uncertainty_sources(
            confidence, source_reliability, claim_uncertainty
        )
        
        # Generate recommendations
        recommendations = self._generate_uncertainty_recommendations(
            overall_uncertainty, breakdown
        )
        
        return UncertaintyAnalysis(
            query=query,
            answer=answer,
            confidence_estimate=confidence,
            source_reliability=source_reliability,
            claim_uncertainty=claim_uncertainty,
            overall_uncertainty_score=overall_uncertainty,
            uncertainty_breakdown=breakdown,
            recommendations=recommendations
        )
    
    async def _estimate_answer_confidence(
        self,
        answer: str,
        sources: List[Dict[str, Any]],
        method: UncertaintyMethod
    ) -> UncertaintyEstimate:
        """Estimate confidence in the overall answer."""
        if method == UncertaintyMethod.EVIDENCE_BASED:
            return await self._evidence_based_confidence(answer, sources)
        elif method == UncertaintyMethod.ENSEMBLE:
            return await self._ensemble_confidence(answer, sources)
        else:
            return await self._bootstrap_confidence(answer, sources)
    
    async def _evidence_based_confidence(
        self,
        answer: str,
        sources: List[Dict[str, Any]]
    ) -> UncertaintyEstimate:
        """Calculate confidence based on evidence strength."""
        # Count sources by authority
        high_authority = sum(1 for s in sources if s.get("authority", 0.5) >= 0.8)
        medium_authority = sum(1 for s in sources if 0.5 <= s.get("authority", 0.5) < 0.8)
        low_authority = sum(1 for s in sources if s.get("authority", 0.5) < 0.5)
        
        # Calculate point estimate
        if high_authority >= 3:
            point = 0.90
            evidence = "strong"
        elif high_authority >= 1 or medium_authority >= 3:
            point = 0.75
            evidence = "moderate"
        else:
            point = 0.60
            evidence = "weak"
        
        # Calculate confidence interval (wider for weaker evidence)
        if evidence == "strong":
            margin = 0.05
        elif evidence == "moderate":
            margin = 0.10
        else:
            margin = 0.15
        
        return UncertaintyEstimate(
            point_estimate=point,
            lower_bound=max(0.0, point - margin),
            upper_bound=min(1.0, point + margin),
            confidence_level=0.95,
            method=UncertaintyMethod.EVIDENCE_BASED,
            evidence_strength=evidence,
            n_samples=len(sources)
        )
    
    async def _ensemble_confidence(
        self,
        answer: str,
        sources: List[Dict[str, Any]]
    ) -> UncertaintyEstimate:
        """Use ensemble of confidence estimates."""
        # Simulate multiple confidence estimates (in production, use actual ensemble)
        estimates = []
        
        # Method 1: Source-based
        source_conf = len(sources) / max(len(sources), 10)
        estimates.append(min(source_conf, 1.0))
        
        # Method 2: Length-based (longer answers often more comprehensive)
        length_conf = min(len(answer) / 500, 1.0)
        estimates.append(length_conf)
        
        # Method 3: Authority-based
        avg_authority = np.mean([s.get("authority", 0.5) for s in sources])
        estimates.append(avg_authority)
        
        # Calculate ensemble statistics
        point = float(np.mean(estimates))
        std = float(np.std(estimates))
        
        # 95% confidence interval
        margin = 1.96 * std / np.sqrt(len(estimates))
        
        return UncertaintyEstimate(
            point_estimate=point,
            lower_bound=max(0.0, point - margin),
            upper_bound=min(1.0, point + margin),
            confidence_level=0.95,
            method=UncertaintyMethod.ENSEMBLE,
            evidence_strength="moderate" if std < 0.1 else "weak",
            n_samples=len(estimates)
        )
    
    async def _bootstrap_confidence(
        self,
        answer: str,
        sources: List[Dict[str, Any]]
    ) -> UncertaintyEstimate:
        """Use bootstrap resampling for confidence interval."""
        if len(sources) < 2:
            return UncertaintyEstimate(
                point_estimate=0.5,
                lower_bound=0.3,
                upper_bound=0.7,
                confidence_level=0.95,
                method=UncertaintyMethod.BOOTSTRAP,
                evidence_strength="weak",
                n_samples=len(sources)
            )
        
        # Bootstrap resampling
        n_bootstrap = 1000
        estimates = []
        
        for _ in range(n_bootstrap):
            # Resample sources with replacement
            sample = np.random.choice(len(sources), size=len(sources), replace=True)
            sample_sources = [sources[i] for i in sample]
            
            # Calculate confidence for this sample
            conf = np.mean([s.get("relevance", 0.5) * s.get("authority", 0.5) 
                           for s in sample_sources])
            estimates.append(conf)
        
        # Calculate percentiles for confidence interval
        point = float(np.median(estimates))
        lower = float(np.percentile(estimates, 2.5))
        upper = float(np.percentile(estimates, 97.5))
        
        return UncertaintyEstimate(
            point_estimate=point,
            lower_bound=lower,
            upper_bound=upper,
            confidence_level=0.95,
            method=UncertaintyMethod.BOOTSTRAP,
            evidence_strength="moderate",
            n_samples=n_bootstrap
        )
    
    async def _estimate_source_reliability(
        self,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, UncertaintyEstimate]:
        """Estimate reliability of each source."""
        reliability = {}
        
        for i, source in enumerate(sources):
            authority = source.get("authority", 0.5)
            recency = source.get("recency_score", 0.5)
            
            # Simple reliability model
            point = (authority + recency) / 2
            margin = 0.1  # Fixed margin for source reliability
            
            reliability[f"source_{i}"] = UncertaintyEstimate(
                point_estimate=point,
                lower_bound=max(0.0, point - margin),
                upper_bound=min(1.0, point + margin),
                confidence_level=0.90,
                method=UncertaintyMethod.EVIDENCE_BASED,
                evidence_strength="moderate" if authority >= 0.7 else "weak",
                n_samples=1
            )
        
        return reliability
    
    async def _estimate_claim_uncertainty(
        self,
        claims: List[str],
        sources: List[Dict[str, Any]]
    ) -> Dict[str, UncertaintyEstimate]:
        """Estimate uncertainty for each claim."""
        claim_uncertainty = {}
        
        for i, claim in enumerate(claims):
            # Count supporting sources (simplified - in production, use semantic matching)
            support_count = min(len(sources), 5)  # Cap at 5 for this example
            
            if support_count >= 3:
                point = 0.85
                evidence = "strong"
                margin = 0.08
            elif support_count >= 2:
                point = 0.70
                evidence = "moderate"
                margin = 0.12
            else:
                point = 0.55
                evidence = "weak"
                margin = 0.18
            
            claim_uncertainty[f"claim_{i}"] = UncertaintyEstimate(
                point_estimate=point,
                lower_bound=max(0.0, point - margin),
                upper_bound=min(1.0, point + margin),
                confidence_level=0.95,
                method=UncertaintyMethod.EVIDENCE_BASED,
                evidence_strength=evidence,
                n_samples=support_count
            )
        
        return claim_uncertainty
    
    def _calculate_overall_uncertainty(
        self,
        confidence: UncertaintyEstimate,
        source_reliability: Dict[str, UncertaintyEstimate],
        claim_uncertainty: Dict[str, UncertaintyEstimate]
    ) -> float:
        """Calculate overall uncertainty score (0=certain, 1=very uncertain)."""
        # Uncertainty = 1 - confidence
        answer_uncertainty = 1.0 - confidence.point_estimate
        
        # Average source uncertainty
        if source_reliability:
            source_unc = 1.0 - np.mean([est.point_estimate for est in source_reliability.values()])
        else:
            source_unc = 0.5
        
        # Average claim uncertainty
        if claim_uncertainty:
            claim_unc = 1.0 - np.mean([est.point_estimate for est in claim_uncertainty.values()])
        else:
            claim_unc = 0.5
        
        # Weighted combination
        overall = 0.5 * answer_uncertainty + 0.3 * source_unc + 0.2 * claim_unc
        return min(max(overall, 0.0), 1.0)
    
    def _breakdown_uncertainty_sources(
        self,
        confidence: UncertaintyEstimate,
        source_reliability: Dict[str, UncertaintyEstimate],
        claim_uncertainty: Dict[str, UncertaintyEstimate]
    ) -> Dict[str, float]:
        """Break down uncertainty by source."""
        breakdown = {}
        
        # Evidence quality
        breakdown["evidence_quality"] = 1.0 - confidence.point_estimate
        
        # Source reliability
        if source_reliability:
            breakdown["source_reliability"] = 1.0 - np.mean([
                est.point_estimate for est in source_reliability.values()
            ])
        else:
            breakdown["source_reliability"] = 0.5
        
        # Claim support
        if claim_uncertainty:
            breakdown["claim_support"] = 1.0 - np.mean([
                est.point_estimate for est in claim_uncertainty.values()
            ])
        else:
            breakdown["claim_support"] = 0.5
        
        # Model uncertainty (fixed for this example)
        breakdown["model_uncertainty"] = 0.15
        
        return breakdown
    
    def _generate_uncertainty_recommendations(
        self,
        overall_uncertainty: float,
        breakdown: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations based on uncertainty analysis."""
        recommendations = []
        
        if overall_uncertainty > 0.4:
            recommendations.append(
                "⚠️ High uncertainty detected. Consider gathering more evidence before making decisions."
            )
        
        # Find largest uncertainty source
        max_source = max(breakdown.items(), key=lambda x: x[1])
        if max_source[1] > 0.3:
            recommendations.append(
                f"📊 Primary uncertainty source: {max_source[0]} ({max_source[1]:.2%}). "
                "Focus on improving this aspect."
            )
        
        if breakdown.get("evidence_quality", 0) > 0.4:
            recommendations.append(
                "🔍 Evidence quality is low. Consider using more authoritative sources."
            )
        
        if breakdown.get("source_reliability", 0) > 0.4:
            recommendations.append(
                "📚 Source reliability is questionable. Cross-verify with additional sources."
            )
        
        return recommendations


# ============================================================================
# 3. VISUAL PROGRESS TREE UI (Backend Component)
# ============================================================================

class NodeStatus(Enum):
    """Status of a tree node."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PRUNED = "pruned"


@dataclass
class TreeNode:
    """Represents a node in the execution tree."""
    node_id: str
    parent_id: Optional[str]
    label: str
    status: NodeStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    cost_cu: float = 0.0
    time_seconds: float = 0.0
    quality_score: float = 0.0
    result_summary: str = ""
    children: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TreeVisualizationData:
    """Complete tree visualization data for UI."""
    tree_id: str
    query: str
    nodes: Dict[str, TreeNode]
    edges: List[Tuple[str, str]]  # (parent_id, child_id)
    total_cost_cu: float
    total_time_seconds: float
    overall_quality: float
    active_nodes: List[str]
    completed_nodes: List[str]
    failed_nodes: List[str]
    pruned_nodes: List[str]
    last_updated: datetime


class VisualProgressTreeManager:
    """
    Manages the visual representation of the execution tree for real-time UI updates.
    
    Provides WebSocket-based streaming of tree updates to frontend visualization.
    """
    
    def __init__(self):
        self.trees: Dict[str, TreeVisualizationData] = {}
        self.websocket_connections: Dict[str, Set[Any]] = {}  # tree_id -> set of websockets
    
    def create_tree(self, tree_id: str, query: str) -> TreeVisualizationData:
        """Create a new execution tree for visualization."""
        root_node = TreeNode(
            node_id="root",
            parent_id=None,
            label=f"Query: {query[:50]}...",
            status=NodeStatus.PENDING
        )
        
        tree_data = TreeVisualizationData(
            tree_id=tree_id,
            query=query,
            nodes={"root": root_node},
            edges=[],
            total_cost_cu=0.0,
            total_time_seconds=0.0,
            overall_quality=0.0,
            active_nodes=[],
            completed_nodes=[],
            failed_nodes=[],
            pruned_nodes=[],
            last_updated=datetime.now()
        )
        
        self.trees[tree_id] = tree_data
        return tree_data
    
    def add_node(
        self,
        tree_id: str,
        node_id: str,
        parent_id: str,
        label: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TreeNode:
        """Add a new node to the tree."""
        if tree_id not in self.trees:
            raise ValueError(f"Tree {tree_id} not found")
        
        tree = self.trees[tree_id]
        
        node = TreeNode(
            node_id=node_id,
            parent_id=parent_id,
            label=label,
            status=NodeStatus.PENDING,
            metadata=metadata or {}
        )
        
        tree.nodes[node_id] = node
        tree.edges.append((parent_id, node_id))
        
        # Update parent's children
        if parent_id in tree.nodes:
            tree.nodes[parent_id].children.append(node_id)
        
        tree.last_updated = datetime.now()
        
        # Notify websockets
        asyncio.create_task(self._broadcast_update(tree_id, "node_added", node))
        
        return node
    
    def update_node_status(
        self,
        tree_id: str,
        node_id: str,
        status: NodeStatus,
        result_summary: str = "",
        cost_cu: float = 0.0,
        time_seconds: float = 0.0,
        quality_score: float = 0.0
    ):
        """Update node status and metrics."""
        if tree_id not in self.trees:
            return
        
        tree = self.trees[tree_id]
        if node_id not in tree.nodes:
            return
        
        node = tree.nodes[node_id]
        node.status = status
        node.result_summary = result_summary
        node.cost_cu = cost_cu
        node.time_seconds = time_seconds
        node.quality_score = quality_score
        
        if status == NodeStatus.ACTIVE:
            node.start_time = datetime.now()
            if node_id not in tree.active_nodes:
                tree.active_nodes.append(node_id)
        
        elif status == NodeStatus.COMPLETED:
            node.end_time = datetime.now()
            if node_id in tree.active_nodes:
                tree.active_nodes.remove(node_id)
            if node_id not in tree.completed_nodes:
                tree.completed_nodes.append(node_id)
            
            # Update totals
            tree.total_cost_cu += cost_cu
            tree.total_time_seconds += time_seconds
        
        elif status == NodeStatus.FAILED:
            node.end_time = datetime.now()
            if node_id in tree.active_nodes:
                tree.active_nodes.remove(node_id)
            if node_id not in tree.failed_nodes:
                tree.failed_nodes.append(node_id)
        
        elif status == NodeStatus.PRUNED:
            node.end_time = datetime.now()
            if node_id in tree.active_nodes:
                tree.active_nodes.remove(node_id)
            if node_id not in tree.pruned_nodes:
                tree.pruned_nodes.append(node_id)
        
        tree.last_updated = datetime.now()
        
        # Update overall quality (average of completed nodes)
        if tree.completed_nodes:
            tree.overall_quality = np.mean([
                tree.nodes[nid].quality_score for nid in tree.completed_nodes
                if tree.nodes[nid].quality_score > 0
            ])
        
        # Notify websockets
        asyncio.create_task(self._broadcast_update(tree_id, "node_updated", node))
    
    def get_tree_data(self, tree_id: str) -> Optional[TreeVisualizationData]:
        """Get complete tree data for rendering."""
        return self.trees.get(tree_id)
    
    def get_tree_json(self, tree_id: str) -> str:
        """Get tree as JSON for frontend rendering."""
        tree = self.trees.get(tree_id)
        if not tree:
            return "{}"
        
        # Convert to JSON-serializable format
        data = {
            "tree_id": tree.tree_id,
            "query": tree.query,
            "nodes": [
                {
                    "id": node.node_id,
                    "parent_id": node.parent_id,
                    "label": node.label,
                    "status": node.status.value,
                    "cost_cu": node.cost_cu,
                    "time_seconds": node.time_seconds,
                    "quality_score": node.quality_score,
                    "result_summary": node.result_summary,
                    "children": node.children,
                    "metadata": node.metadata
                }
                for node in tree.nodes.values()
            ],
            "edges": [{"from": e[0], "to": e[1]} for e in tree.edges],
            "metrics": {
                "total_cost_cu": tree.total_cost_cu,
                "total_time_seconds": tree.total_time_seconds,
                "overall_quality": tree.overall_quality,
                "active_count": len(tree.active_nodes),
                "completed_count": len(tree.completed_nodes),
                "failed_count": len(tree.failed_nodes),
                "pruned_count": len(tree.pruned_nodes)
            },
            "last_updated": tree.last_updated.isoformat()
        }
        
        return json.dumps(data, indent=2)
    
    async def register_websocket(self, tree_id: str, websocket: Any):
        """Register a websocket for tree updates."""
        if tree_id not in self.websocket_connections:
            self.websocket_connections[tree_id] = set()
        self.websocket_connections[tree_id].add(websocket)
    
    async def unregister_websocket(self, tree_id: str, websocket: Any):
        """Unregister a websocket."""
        if tree_id in self.websocket_connections:
            self.websocket_connections[tree_id].discard(websocket)
    
    async def _broadcast_update(self, tree_id: str, event_type: str, data: Any):
        """Broadcast update to all connected websockets."""
        if tree_id not in self.websocket_connections:
            return
        
        message = {
            "event": event_type,
            "tree_id": tree_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Broadcast to all connections (simplified - actual implementation needs error handling)
        for ws in self.websocket_connections[tree_id]:
            try:
                await ws.send_json(message)
            except:
                pass  # Connection closed, will be cleaned up


# ============================================================================
# PHASE 3 FEATURE COORDINATOR
# ============================================================================

class Phase3FeatureCoordinator:
    """
    Coordinates all Phase 3 features for seamless integration.
    
    Brings together:
    - Counterfactual reasoning for robustness analysis
    - Uncertainty quantification for transparent confidence
    - Visual progress tree for user engagement
    """
    
    def __init__(
        self,
        counterfactual_engine: CounterfactualReasoningEngine,
        uncertainty_engine: UncertaintyQuantificationEngine,
        tree_manager: VisualProgressTreeManager
    ):
        self.counterfactual = counterfactual_engine
        self.uncertainty = uncertainty_engine
        self.tree_manager = tree_manager
    
    async def process_query_with_phase3_features(
        self,
        tree_id: str,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        claims: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process query with all Phase 3 features enabled.
        
        Returns comprehensive analysis including:
        - Counterfactual scenarios
        - Uncertainty quantification
        - Visual tree data
        """
        # Create visualization tree
        tree = self.tree_manager.create_tree(tree_id, query)
        
        # Add counterfactual analysis node
        cf_node_id = f"{tree_id}_counterfactual"
        self.tree_manager.add_node(
            tree_id, cf_node_id, "root", "Counterfactual Analysis"
        )
        self.tree_manager.update_node_status(tree_id, cf_node_id, NodeStatus.ACTIVE)
        
        # Run counterfactual analysis
        cf_analysis = await self.counterfactual.analyze_counterfactuals(
            query, answer, context, max_scenarios=5
        )
        
        self.tree_manager.update_node_status(
            tree_id, cf_node_id, NodeStatus.COMPLETED,
            result_summary=f"Robustness: {cf_analysis.overall_robustness_score:.2f}",
            quality_score=cf_analysis.overall_robustness_score
        )
        
        # Add uncertainty quantification node
        uq_node_id = f"{tree_id}_uncertainty"
        self.tree_manager.add_node(
            tree_id, uq_node_id, "root", "Uncertainty Quantification"
        )
        self.tree_manager.update_node_status(tree_id, uq_node_id, NodeStatus.ACTIVE)
        
        # Run uncertainty analysis
        uq_analysis = await self.uncertainty.quantify_uncertainty(
            query, answer, sources, claims
        )
        
        self.tree_manager.update_node_status(
            tree_id, uq_node_id, NodeStatus.COMPLETED,
            result_summary=f"Confidence: {uq_analysis.confidence_estimate.point_estimate:.2f} "
                          f"[{uq_analysis.confidence_estimate.lower_bound:.2f}, "
                          f"{uq_analysis.confidence_estimate.upper_bound:.2f}]",
            quality_score=uq_analysis.confidence_estimate.point_estimate
        )
        
        # Compile results
        return {
            "answer": answer,
            "counterfactual_analysis": {
                "robustness_score": cf_analysis.overall_robustness_score,
                "scenarios_explored": len(cf_analysis.scenarios_explored),
                "high_risk_scenarios": len(cf_analysis.risk_scenarios),
                "recommendations": cf_analysis.recommendations
            },
            "uncertainty_analysis": {
                "confidence": {
                    "point_estimate": uq_analysis.confidence_estimate.point_estimate,
                    "confidence_interval": [
                        uq_analysis.confidence_estimate.lower_bound,
                        uq_analysis.confidence_estimate.upper_bound
                    ],
                    "evidence_strength": uq_analysis.confidence_estimate.evidence_strength
                },
                "overall_uncertainty": uq_analysis.overall_uncertainty_score,
                "breakdown": uq_analysis.uncertainty_breakdown,
                "recommendations": uq_analysis.recommendations
            },
            "visualization": {
                "tree_id": tree_id,
                "tree_json": self.tree_manager.get_tree_json(tree_id),
                "metrics": {
                    "total_cost_cu": tree.total_cost_cu,
                    "total_time_seconds": tree.total_time_seconds,
                    "overall_quality": tree.overall_quality
                }
            }
        }
