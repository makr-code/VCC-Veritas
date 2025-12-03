"""
Tests für Polyglot Execution Plan Analysis System
==================================================

Tests für Kosten-Nutzen-Analyse und Query-Optimierung.

Author: VERITAS Backend Team
Date: 2025-12-03
"""

import pytest
from backend.agents.themisdb.execution_plan_analysis import (
    ResourceType,
    QueryApproach,
    ExecutionMode,
    ResourceCost,
    ExecutionStep,
    ExecutionPlan,
    ResourceCostDatabase,
    QueryAnalyzer,
    ExecutionPlanBuilder,
    ExecutionPlanOptimizer,
    format_execution_plan,
)


class TestResourceCost:
    """Test ResourceCost calculations"""
    
    def test_total_cost(self):
        """Test total cost calculation"""
        cost = ResourceCost(
            computational_cost=2.0,
            time_cost=3.0,
            monetary_cost=1.0,
            quality_score=0.8
        )
        
        # Total cost = 2.0*0.3 + 3.0*0.4 + 1.0*0.3 = 0.6 + 1.2 + 0.3 = 2.1
        assert abs(cost.total_cost - 2.1) < 0.01
    
    def test_cost_benefit_ratio(self):
        """Test cost-benefit ratio"""
        cost = ResourceCost(
            computational_cost=2.0,
            time_cost=2.0,
            monetary_cost=2.0,
            quality_score=0.8
        )
        
        # Total cost = 2.0
        # Ratio = 0.8 / 2.0 = 0.4
        assert abs(cost.cost_benefit_ratio - 0.4) < 0.01
    
    def test_zero_cost_benefit(self):
        """Test cost-benefit with zero cost"""
        cost = ResourceCost(
            computational_cost=0.0,
            time_cost=0.0,
            monetary_cost=0.0,
            quality_score=1.0
        )
        
        assert cost.cost_benefit_ratio == float('inf')


class TestResourceCostDatabase:
    """Test ResourceCostDatabase"""
    
    def test_get_cost_llm_large(self):
        """Test getting cost for LLM Large"""
        cost = ResourceCostDatabase.get_cost(ResourceType.LLM_LARGE)
        
        assert cost.computational_cost == 10.0
        assert cost.quality_score == 0.95
    
    def test_get_cost_vector_search(self):
        """Test getting cost for vector search"""
        cost = ResourceCostDatabase.get_cost(ResourceType.VECTOR_SEARCH)
        
        assert cost.time_cost == 0.1  # Fast
        assert cost.quality_score == 0.75
    
    def test_register_custom_cost(self):
        """Test registering custom resource cost"""
        custom_type = ResourceType.SLM_SMALL
        custom_cost = ResourceCost(
            computational_cost=1.5,
            time_cost=0.5,
            monetary_cost=0.5,
            quality_score=0.65
        )
        
        ResourceCostDatabase.register_cost(custom_type, custom_cost)
        retrieved = ResourceCostDatabase.get_cost(custom_type)
        
        assert retrieved.computational_cost == 1.5


class TestQueryAnalyzer:
    """Test QueryAnalyzer"""
    
    def test_simple_ask_detection(self):
        """Test detection of simple ask query"""
        analyzer = QueryAnalyzer()
        
        # Short, simple question
        approach = analyzer.analyze_query("Was ist BGB?")
        assert approach == QueryApproach.SIMPLE_ASK
    
    def test_research_basic_detection(self):
        """Test detection of basic research query"""
        analyzer = QueryAnalyzer()
        
        # Medium length, research keyword
        approach = analyzer.analyze_query(
            "Bitte gib mir eine Übersicht über das Vertragsrecht im BGB"
        )
        assert approach == QueryApproach.RESEARCH_BASIC
    
    def test_research_deep_detection(self):
        """Test detection of deep research query"""
        analyzer = QueryAnalyzer()
        
        # Long query with analysis keyword
        approach = analyzer.analyze_query(
            "Ich benötige eine detaillierte Analyse der Zusammenhänge "
            "zwischen BGB Vertragsrecht und Handelsrecht mit Vergleich "
            "der verschiedenen Rechtsprechungen"
        )
        assert approach == QueryApproach.RESEARCH_DEEP
    
    def test_scientific_detection(self):
        """Test detection of scientific query"""
        analyzer = QueryAnalyzer()
        
        # Scientific keywords
        approach = analyzer.analyze_query(
            "Welche wissenschaftlichen Studien gibt es zur Evidenz "
            "der Wirksamkeit von Umweltschutzmaßnahmen?"
        )
        assert approach == QueryApproach.SCIENTIFIC
    
    def test_recommend_resources_simple(self):
        """Test resource recommendation for simple query"""
        analyzer = QueryAnalyzer()
        
        resources = analyzer.recommend_resources(QueryApproach.SIMPLE_ASK)
        
        assert ResourceType.VECTOR_SEARCH in resources
        assert ResourceType.SLM_SMALL in resources
        # Sollte keine teuren LLMs empfehlen
        assert ResourceType.LLM_LARGE not in resources
    
    def test_recommend_resources_scientific(self):
        """Test resource recommendation for scientific query"""
        analyzer = QueryAnalyzer()
        
        resources = analyzer.recommend_resources(QueryApproach.SCIENTIFIC)
        
        assert ResourceType.LLM_LARGE in resources
        assert ResourceType.GRAPH_TRAVERSAL in resources
    
    def test_recommend_with_budget_constraint(self):
        """Test resource recommendation with budget constraint"""
        analyzer = QueryAnalyzer()
        
        # Very tight budget
        budget = {
            "computational": 1.0,
            "time": 0.5,
            "monetary": 1.0
        }
        
        resources = analyzer.recommend_resources(
            QueryApproach.SCIENTIFIC,
            budget
        )
        
        # Should filter out expensive LLM_LARGE
        for resource_type in resources:
            cost = ResourceCostDatabase.get_cost(resource_type)
            assert cost.computational_cost <= budget["computational"] * 1.5  # Some tolerance


class TestExecutionPlanBuilder:
    """Test ExecutionPlanBuilder"""
    
    def test_build_simple_plan(self):
        """Test building simple execution plan"""
        builder = ExecutionPlanBuilder()
        
        plan = builder.build_plan("Was ist BGB?")
        
        assert plan.approach == QueryApproach.SIMPLE_ASK
        assert len(plan.steps) > 0
        assert plan.total_cost.total_cost > 0
    
    def test_build_research_plan(self):
        """Test building research execution plan"""
        builder = ExecutionPlanBuilder()
        
        plan = builder.build_plan(
            "Gib mir eine Analyse der Umweltschutzgesetze"
        )
        
        assert plan.approach in [
            QueryApproach.RESEARCH_BASIC,
            QueryApproach.RESEARCH_DEEP
        ]
        assert len(plan.steps) >= 2  # Multiple resources
    
    def test_parallelization_detection(self):
        """Test parallelization detection"""
        builder = ExecutionPlanBuilder()
        
        # Scientific query should have parallelizable steps
        plan = builder.build_plan(
            "Welche wissenschaftlichen Studien gibt es zu diesem Thema?"
        )
        
        parallel_steps = sum(1 for step in plan.steps if step.can_parallelize)
        assert parallel_steps > 0
        assert plan.parallelization_factor > 1.0
    
    def test_budget_constraint_respected(self):
        """Test that budget constraints are respected"""
        builder = ExecutionPlanBuilder()
        
        # Very tight budget
        budget = {
            "time": 1.0,
            "computational": 2.0,
            "monetary": 2.0
        }
        
        plan = builder.build_plan(
            "Komplexe wissenschaftliche Analyse",
            budget=budget
        )
        
        # Should not use expensive LLM_LARGE
        resource_types = [step.resource_type for step in plan.steps]
        assert ResourceType.LLM_LARGE not in resource_types


class TestExecutionPlan:
    """Test ExecutionPlan properties"""
    
    def test_cost_benefit_score(self):
        """Test cost-benefit score calculation"""
        plan = ExecutionPlan(
            plan_id="test",
            approach=QueryApproach.SIMPLE_ASK,
            execution_mode=ExecutionMode.SEQUENTIAL,
            total_cost=ResourceCost(
                computational_cost=2.0,
                time_cost=2.0,
                monetary_cost=2.0,
                quality_score=0.8
            )
        )
        
        assert plan.cost_benefit_score == 0.8 / 2.0
    
    def test_effective_time_cost(self):
        """Test effective time cost with parallelization"""
        plan = ExecutionPlan(
            plan_id="test",
            approach=QueryApproach.RESEARCH_DEEP,
            execution_mode=ExecutionMode.PARALLEL,
            total_cost=ResourceCost(time_cost=10.0),
            parallelization_factor=2.0
        )
        
        assert plan.effective_time_cost == 5.0  # 10.0 / 2.0


class TestExecutionPlanOptimizer:
    """Test ExecutionPlanOptimizer"""
    
    def test_optimize_for_speed(self):
        """Test optimization for speed"""
        optimizer = ExecutionPlanOptimizer()
        
        plan = optimizer.optimize_for_speed("Test query")
        
        # Should prefer fast resources
        assert plan.total_cost.time_cost < 5.0
    
    def test_optimize_for_cost(self):
        """Test optimization for cost"""
        optimizer = ExecutionPlanOptimizer()
        
        plan = optimizer.optimize_for_cost("Test query")
        
        # Should prefer cheap resources
        assert plan.total_cost.monetary_cost < 5.0
    
    def test_optimize_for_quality(self):
        """Test optimization for quality"""
        optimizer = ExecutionPlanOptimizer()
        
        plan = optimizer.optimize_for_quality(
            "Wissenschaftliche Analyse benötigt"
        )
        
        # Should aim for high quality
        assert plan.expected_quality > 0.7
    
    def test_compare_plans(self):
        """Test plan comparison"""
        optimizer = ExecutionPlanOptimizer()
        
        plans = optimizer.compare_plans("Test query")
        
        assert "speed" in plans
        assert "cost" in plans
        assert "quality" in plans
        assert "balanced" in plans
        
        # Speed plan should be faster
        assert plans["speed"].total_cost.time_cost <= plans["quality"].total_cost.time_cost
        
        # Cost plan should be cheaper
        assert plans["cost"].total_cost.monetary_cost <= plans["quality"].total_cost.monetary_cost


class TestExecutionStep:
    """Test ExecutionStep"""
    
    def test_step_creation(self):
        """Test execution step creation"""
        step = ExecutionStep(
            step_id="step_1",
            step_type="vector_search",
            resource_type=ResourceType.VECTOR_SEARCH,
            estimated_cost=ResourceCost(
                computational_cost=1.0,
                time_cost=0.1,
                monetary_cost=0.5,
                quality_score=0.75
            ),
            can_parallelize=True
        )
        
        assert step.step_id == "step_1"
        assert step.can_parallelize is True
        assert step.estimated_cost.quality_score == 0.75


class TestUtilities:
    """Test utility functions"""
    
    def test_format_execution_plan(self):
        """Test execution plan formatting"""
        plan = ExecutionPlan(
            plan_id="test_plan",
            approach=QueryApproach.RESEARCH_BASIC,
            execution_mode=ExecutionMode.PARALLEL,
            steps=[
                ExecutionStep(
                    step_id="step_1",
                    step_type="vector",
                    resource_type=ResourceType.VECTOR_SEARCH,
                    estimated_cost=ResourceCost(),
                    can_parallelize=True
                )
            ],
            total_cost=ResourceCost(
                computational_cost=2.0,
                time_cost=1.0,
                monetary_cost=1.5,
                quality_score=0.75
            ),
            expected_quality=0.75,
            parallelization_factor=2.0
        )
        
        formatted = format_execution_plan(plan)
        
        assert "test_plan" in formatted
        assert "RESEARCH_BASIC" in formatted
        assert "PARALLEL" in formatted
        assert "step_1" in formatted


class TestIntegration:
    """Integration tests"""
    
    def test_end_to_end_simple_query(self):
        """Test end-to-end for simple query"""
        optimizer = ExecutionPlanOptimizer()
        
        plan = optimizer.optimize_balanced("Was ist das BGB?")
        
        assert plan.approach == QueryApproach.SIMPLE_ASK
        assert len(plan.steps) >= 1
        assert plan.total_cost.total_cost > 0
        assert 0 <= plan.expected_quality <= 1.0
    
    def test_end_to_end_scientific_query(self):
        """Test end-to-end for scientific query"""
        optimizer = ExecutionPlanOptimizer()
        
        plan = optimizer.optimize_balanced(
            "Welche wissenschaftlichen Studien und Forschungsergebnisse "
            "gibt es zur Evidenz der Klimawandel-Maßnahmen?"
        )
        
        assert plan.approach == QueryApproach.SCIENTIFIC
        assert len(plan.steps) >= 3  # Multiple resources for scientific
        assert plan.expected_quality > 0.8  # High quality expected
    
    def test_plan_comparison_consistency(self):
        """Test that plan comparison is consistent"""
        optimizer = ExecutionPlanOptimizer()
        
        plans = optimizer.compare_plans("Komplexe Recherche-Anfrage")
        
        # All plans should have same approach (determined by query)
        approaches = {plan.approach for plan in plans.values()}
        assert len(approaches) == 1  # Same approach for all
        
        # But different execution characteristics
        time_costs = [plan.total_cost.time_cost for plan in plans.values()]
        assert len(set(time_costs)) > 1  # Different time costs


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
