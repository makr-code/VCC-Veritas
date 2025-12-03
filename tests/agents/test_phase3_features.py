"""
Tests for Phase 3 Features: Counterfactual reasoning, uncertainty quantification, and visual progress tree.

Author: GitHub Copilot
Date: 2025-12-03
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import json
import numpy as np

from backend.agents.framework.phase3_features import (
    CounterfactualReasoningEngine,
    UncertaintyQuantificationEngine,
    VisualProgressTreeManager,
    Phase3FeatureCoordinator,
    ScenarioType,
    UncertaintyMethod,
    NodeStatus,
    CounterfactualScenario,
    UncertaintyEstimate,
    TreeNode
)


# ============================================================================
# COUNTERFACTUAL REASONING TESTS
# ============================================================================

class TestCounterfactualReasoningEngine:
    """Tests for counterfactual reasoning engine."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client."""
        client = Mock()
        client.generate = AsyncMock()
        return client
    
    @pytest.fixture
    def engine(self, mock_llm_client):
        """Create engine instance."""
        return CounterfactualReasoningEngine(mock_llm_client)
    
    @pytest.mark.asyncio
    async def test_scenario_generation(self, engine, mock_llm_client):
        """Test counterfactual scenario generation."""
        # Mock LLM response
        mock_llm_client.generate.return_value = json.dumps([
            {
                "type": "edge_case",
                "description": "What if building is in flood zone?",
                "changed_parameters": {"location": "flood_zone"},
                "expected_impact": "Additional flood protection required",
                "probability": 0.3,
                "severity": "high"
            }
        ])
        
        analysis = await engine.analyze_counterfactuals(
            query="Bauantrag requirements",
            current_answer="Standard requirements apply",
            context={},
            max_scenarios=1
        )
        
        assert len(analysis.scenarios_explored) == 1
        assert analysis.scenarios_explored[0].scenario_type == ScenarioType.EDGE_CASE
        assert "flood" in analysis.scenarios_explored[0].description.lower()
    
    @pytest.mark.asyncio
    async def test_robustness_calculation(self, engine):
        """Test robustness score calculation."""
        scenarios = [
            CounterfactualScenario(
                scenario_id="s1",
                scenario_type=ScenarioType.RISK_SCENARIO,
                description="High risk",
                changed_parameters={},
                expected_impact="Critical",
                probability=0.8,
                severity="critical",
                confidence=0.9
            ),
            CounterfactualScenario(
                scenario_id="s2",
                scenario_type=ScenarioType.EDGE_CASE,
                description="Low risk",
                changed_parameters={},
                expected_impact="Minor",
                probability=0.2,
                severity="low",
                confidence=0.6
            )
        ]
        
        robustness = engine._calculate_robustness_score(scenarios)
        
        # High severity + high probability should reduce robustness
        assert 0.0 <= robustness <= 1.0
        assert robustness < 0.7  # Should be lower due to critical scenario
    
    @pytest.mark.asyncio
    async def test_risk_scenario_identification(self, engine, mock_llm_client):
        """Test identification of high-risk scenarios."""
        mock_llm_client.generate.side_effect = [
            json.dumps([{
                "type": "risk_scenario",
                "description": "Critical failure mode",
                "changed_parameters": {},
                "expected_impact": "System failure",
                "probability": 0.4,
                "severity": "critical"
            }]),
            json.dumps({
                "analysis": "This would cause major issues",
                "confidence": 0.85
            })
        ]
        
        analysis = await engine.analyze_counterfactuals(
            query="Test", current_answer="Answer", context={}, max_scenarios=1
        )
        
        assert len(analysis.risk_scenarios) == 1
        assert analysis.risk_scenarios[0].severity == "critical"


# ============================================================================
# UNCERTAINTY QUANTIFICATION TESTS
# ============================================================================

class TestUncertaintyQuantificationEngine:
    """Tests for uncertainty quantification engine."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client."""
        return Mock()
    
    @pytest.fixture
    def engine(self, mock_llm_client):
        """Create engine instance."""
        return UncertaintyQuantificationEngine(mock_llm_client)
    
    @pytest.mark.asyncio
    async def test_evidence_based_confidence(self, engine):
        """Test evidence-based confidence calculation."""
        # High authority sources
        sources = [
            {"authority": 0.9, "relevance": 0.8},
            {"authority": 0.85, "relevance": 0.9},
            {"authority": 0.88, "relevance": 0.85}
        ]
        
        estimate = await engine._evidence_based_confidence("answer", sources)
        
        assert estimate.point_estimate >= 0.8  # Strong evidence
        assert estimate.evidence_strength == "strong"
        assert estimate.lower_bound < estimate.point_estimate
        assert estimate.upper_bound > estimate.point_estimate
    
    @pytest.mark.asyncio
    async def test_ensemble_confidence(self, engine):
        """Test ensemble confidence estimation."""
        sources = [{"authority": 0.7}, {"authority": 0.8}]
        
        estimate = await engine._ensemble_confidence("answer", sources)
        
        assert 0.0 <= estimate.point_estimate <= 1.0
        assert estimate.method == UncertaintyMethod.ENSEMBLE
        assert estimate.confidence_level == 0.95
    
    @pytest.mark.asyncio
    async def test_bootstrap_confidence(self, engine):
        """Test bootstrap confidence interval."""
        sources = [
            {"relevance": 0.8, "authority": 0.7},
            {"relevance": 0.9, "authority": 0.8},
            {"relevance": 0.75, "authority": 0.85}
        ]
        
        estimate = await engine._bootstrap_confidence("answer", sources)
        
        assert estimate.method == UncertaintyMethod.BOOTSTRAP
        assert estimate.n_samples == 1000  # Bootstrap iterations
        assert estimate.lower_bound <= estimate.point_estimate <= estimate.upper_bound
    
    @pytest.mark.asyncio
    async def test_overall_uncertainty_calculation(self, engine):
        """Test overall uncertainty score calculation."""
        confidence = UncertaintyEstimate(
            point_estimate=0.8,
            lower_bound=0.7,
            upper_bound=0.9,
            confidence_level=0.95,
            method=UncertaintyMethod.EVIDENCE_BASED,
            evidence_strength="strong"
        )
        
        source_reliability = {
            "source_0": UncertaintyEstimate(
                point_estimate=0.75,
                lower_bound=0.65,
                upper_bound=0.85,
                confidence_level=0.90,
                method=UncertaintyMethod.EVIDENCE_BASED,
                evidence_strength="moderate"
            )
        }
        
        claim_uncertainty = {
            "claim_0": UncertaintyEstimate(
                point_estimate=0.85,
                lower_bound=0.75,
                upper_bound=0.95,
                confidence_level=0.95,
                method=UncertaintyMethod.EVIDENCE_BASED,
                evidence_strength="strong"
            )
        }
        
        overall = engine._calculate_overall_uncertainty(
            confidence, source_reliability, claim_uncertainty
        )
        
        assert 0.0 <= overall <= 1.0
        # High confidence should mean low uncertainty
        assert overall < 0.5
    
    @pytest.mark.asyncio
    async def test_uncertainty_breakdown(self, engine):
        """Test uncertainty source breakdown."""
        confidence = UncertaintyEstimate(
            point_estimate=0.7,
            lower_bound=0.6,
            upper_bound=0.8,
            confidence_level=0.95,
            method=UncertaintyMethod.EVIDENCE_BASED,
            evidence_strength="moderate"
        )
        
        breakdown = engine._breakdown_uncertainty_sources(confidence, {}, {})
        
        assert "evidence_quality" in breakdown
        assert "source_reliability" in breakdown
        assert "claim_support" in breakdown
        assert "model_uncertainty" in breakdown
        
        # All values should be between 0 and 1
        for value in breakdown.values():
            assert 0.0 <= value <= 1.0


# ============================================================================
# VISUAL PROGRESS TREE TESTS
# ============================================================================

class TestVisualProgressTreeManager:
    """Tests for visual progress tree manager."""
    
    @pytest.fixture
    def manager(self):
        """Create manager instance."""
        return VisualProgressTreeManager()
    
    def test_create_tree(self, manager):
        """Test tree creation."""
        tree = manager.create_tree("tree_1", "Test query")
        
        assert tree.tree_id == "tree_1"
        assert tree.query == "Test query"
        assert "root" in tree.nodes
        assert tree.nodes["root"].status == NodeStatus.PENDING
    
    def test_add_node(self, manager):
        """Test adding nodes to tree."""
        manager.create_tree("tree_1", "Test query")
        
        node = manager.add_node(
            "tree_1",
            "node_1",
            "root",
            "Test node",
            {"metadata": "test"}
        )
        
        assert node.node_id == "node_1"
        assert node.parent_id == "root"
        assert node.label == "Test node"
        assert node.metadata["metadata"] == "test"
        
        tree = manager.get_tree_data("tree_1")
        assert "node_1" in tree.nodes
        assert ("root", "node_1") in tree.edges
    
    def test_update_node_status(self, manager):
        """Test node status updates."""
        manager.create_tree("tree_1", "Test query")
        manager.add_node("tree_1", "node_1", "root", "Test")
        
        # Activate node
        manager.update_node_status(
            "tree_1", "node_1", NodeStatus.ACTIVE
        )
        tree = manager.get_tree_data("tree_1")
        assert tree.nodes["node_1"].status == NodeStatus.ACTIVE
        assert "node_1" in tree.active_nodes
        
        # Complete node
        manager.update_node_status(
            "tree_1", "node_1", NodeStatus.COMPLETED,
            result_summary="Done",
            cost_cu=2.5,
            time_seconds=1.2,
            quality_score=0.85
        )
        tree = manager.get_tree_data("tree_1")
        assert tree.nodes["node_1"].status == NodeStatus.COMPLETED
        assert "node_1" not in tree.active_nodes
        assert "node_1" in tree.completed_nodes
        assert tree.total_cost_cu == 2.5
        assert tree.total_time_seconds == 1.2
    
    def test_tree_json_export(self, manager):
        """Test tree JSON export."""
        manager.create_tree("tree_1", "Test query")
        manager.add_node("tree_1", "node_1", "root", "Child")
        
        json_str = manager.get_tree_json("tree_1")
        data = json.loads(json_str)
        
        assert data["tree_id"] == "tree_1"
        assert data["query"] == "Test query"
        assert len(data["nodes"]) == 2  # root + node_1
        assert len(data["edges"]) == 1
        assert "metrics" in data
    
    def test_pruned_node_tracking(self, manager):
        """Test tracking of pruned nodes."""
        manager.create_tree("tree_1", "Test")
        manager.add_node("tree_1", "node_1", "root", "Test")
        
        manager.update_node_status("tree_1", "node_1", NodeStatus.PRUNED)
        
        tree = manager.get_tree_data("tree_1")
        assert "node_1" in tree.pruned_nodes
        assert tree.nodes["node_1"].status == NodeStatus.PRUNED


# ============================================================================
# PHASE 3 COORDINATOR TESTS
# ============================================================================

class TestPhase3FeatureCoordinator:
    """Tests for Phase 3 feature coordinator."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client."""
        client = Mock()
        client.generate = AsyncMock()
        return client
    
    @pytest.fixture
    def coordinator(self, mock_llm_client):
        """Create coordinator instance."""
        counterfactual = CounterfactualReasoningEngine(mock_llm_client)
        uncertainty = UncertaintyQuantificationEngine(mock_llm_client)
        tree_manager = VisualProgressTreeManager()
        
        return Phase3FeatureCoordinator(
            counterfactual, uncertainty, tree_manager
        )
    
    @pytest.mark.asyncio
    async def test_full_phase3_processing(self, coordinator, mock_llm_client):
        """Test complete Phase 3 feature integration."""
        # Mock LLM responses
        mock_llm_client.generate.side_effect = [
            json.dumps([{  # Counterfactual scenarios
                "type": "edge_case",
                "description": "Edge case scenario",
                "changed_parameters": {},
                "expected_impact": "Minor impact",
                "probability": 0.3,
                "severity": "low"
            }]),
            json.dumps({  # Scenario analysis
                "analysis": "This would have minimal impact",
                "confidence": 0.7
            })
        ]
        
        result = await coordinator.process_query_with_phase3_features(
            tree_id="test_tree",
            query="Test query",
            answer="Test answer",
            sources=[{"authority": 0.8, "relevance": 0.9}],
            claims=["Test claim"],
            context={}
        )
        
        assert "answer" in result
        assert "counterfactual_analysis" in result
        assert "uncertainty_analysis" in result
        assert "visualization" in result
        
        # Check counterfactual analysis
        cf_analysis = result["counterfactual_analysis"]
        assert "robustness_score" in cf_analysis
        assert 0.0 <= cf_analysis["robustness_score"] <= 1.0
        
        # Check uncertainty analysis
        uq_analysis = result["uncertainty_analysis"]
        assert "confidence" in uq_analysis
        assert "overall_uncertainty" in uq_analysis
        
        # Check visualization
        viz = result["visualization"]
        assert viz["tree_id"] == "test_tree"
        assert "tree_json" in viz
    
    @pytest.mark.asyncio
    async def test_tree_node_creation(self, coordinator, mock_llm_client):
        """Test that tree nodes are created correctly."""
        mock_llm_client.generate.side_effect = [
            json.dumps([{"type": "edge_case", "description": "Test", 
                        "changed_parameters": {}, "expected_impact": "Test",
                        "probability": 0.5, "severity": "low"}]),
            json.dumps({"analysis": "Test", "confidence": 0.7})
        ]
        
        await coordinator.process_query_with_phase3_features(
            "test_tree", "Query", "Answer", 
            [{"authority": 0.8}], ["claim"], {}
        )
        
        tree = coordinator.tree_manager.get_tree_data("test_tree")
        
        # Should have root + counterfactual + uncertainty nodes
        assert len(tree.nodes) >= 3
        assert any("counterfactual" in nid.lower() for nid in tree.nodes.keys())
        assert any("uncertainty" in nid.lower() for nid in tree.nodes.keys())


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhase3Integration:
    """Integration tests for all Phase 3 features."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_phase3(self):
        """Test complete Phase 3 feature pipeline."""
        # Create mock LLM client
        llm_client = Mock()
        llm_client.generate = AsyncMock()
        llm_client.generate.side_effect = [
            json.dumps([{
                "type": "risk_scenario",
                "description": "Critical risk",
                "changed_parameters": {"risk": "high"},
                "expected_impact": "System failure",
                "probability": 0.6,
                "severity": "critical"
            }]),
            json.dumps({
                "analysis": "This is a serious risk",
                "confidence": 0.9
            })
        ]
        
        # Create components
        cf_engine = CounterfactualReasoningEngine(llm_client)
        uq_engine = UncertaintyQuantificationEngine(llm_client)
        tree_manager = VisualProgressTreeManager()
        coordinator = Phase3FeatureCoordinator(cf_engine, uq_engine, tree_manager)
        
        # Process query
        result = await coordinator.process_query_with_phase3_features(
            tree_id="integration_test",
            query="Complex query requiring Phase 3 analysis",
            answer="Comprehensive answer with multiple aspects",
            sources=[
                {"authority": 0.9, "relevance": 0.85, "recency_score": 0.9},
                {"authority": 0.8, "relevance": 0.9, "recency_score": 0.8}
            ],
            claims=[
                "Claim 1 about regulations",
                "Claim 2 about requirements"
            ],
            context={"domain": "legal"}
        )
        
        # Verify all Phase 3 features produced results
        assert result is not None
        assert "counterfactual_analysis" in result
        assert "uncertainty_analysis" in result
        assert "visualization" in result
        
        # Verify counterfactual analysis
        cf = result["counterfactual_analysis"]
        assert cf["scenarios_explored"] > 0
        assert "robustness_score" in cf
        assert len(cf["recommendations"]) > 0
        
        # Verify uncertainty analysis
        uq = result["uncertainty_analysis"]
        assert "confidence" in uq
        assert "confidence_interval" in uq["confidence"]
        assert len(uq["confidence"]["confidence_interval"]) == 2
        
        # Verify tree visualization
        viz = result["visualization"]
        tree_data = json.loads(viz["tree_json"])
        assert len(tree_data["nodes"]) >= 3  # root + 2 analysis nodes
        assert "metrics" in tree_data
    
    def test_performance_benchmarks(self):
        """Test that Phase 3 features meet performance targets."""
        # Placeholder for performance testing
        # In production, measure:
        # - Counterfactual analysis: <2s for 5 scenarios
        # - Uncertainty quantification: <1s
        # - Tree updates: <100ms per node
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
