#!/usr/bin/env python3
"""
Example: Polyglot Execution Plan Analysis System

Demonstriert die Verwendung des Kosten-Nutzen-Analyse-Systems
für intelligente Query-Ausführung.

Author: VERITAS Backend Team
Date: 2025-12-03
"""

from backend.agents.themisdb.execution_plan_analysis import (
    ResourceType,
    QueryApproach,
    ExecutionMode,
    ResourceCost,
    ExecutionPlan,
    ResourceCostDatabase,
    QueryAnalyzer,
    ExecutionPlanBuilder,
    ExecutionPlanOptimizer,
    format_execution_plan,
)


def example_1_simple_query():
    """Example 1: Einfache Query mit automatischer Analyse"""
    print("=" * 80)
    print("Example 1: Einfache Query")
    print("=" * 80)
    
    optimizer = ExecutionPlanOptimizer()
    
    query = "Was ist BGB?"
    plan = optimizer.optimize_balanced(query)
    
    print(f"\nQuery: {query}")
    print(format_execution_plan(plan))


def example_2_scientific_query():
    """Example 2: Wissenschaftliche Query"""
    print("\n" + "=" * 80)
    print("Example 2: Wissenschaftliche Query")
    print("=" * 80)
    
    optimizer = ExecutionPlanOptimizer()
    
    query = "Welche wissenschaftlichen Studien gibt es zur Evidenz von Klimaschutzmaßnahmen?"
    plan = optimizer.optimize_for_quality(query)
    
    print(f"\nQuery: {query}")
    print(format_execution_plan(plan))


def example_3_compare_strategies():
    """Example 3: Vergleich verschiedener Optimierungsstrategien"""
    print("\n" + "=" * 80)
    print("Example 3: Strategy Comparison")
    print("=" * 80)
    
    optimizer = ExecutionPlanOptimizer()
    
    query = "Analyse der Umweltschutzgesetze in Deutschland"
    plans = optimizer.compare_plans(query)
    
    print(f"\nQuery: {query}\n")
    
    # Tabelle formatieren
    print(f"{'Strategy':<12} {'Cost':<8} {'Time':<8} {'Quality':<10} {'C-B Score':<10}")
    print("-" * 60)
    
    for strategy, plan in plans.items():
        print(
            f"{strategy:<12} "
            f"{plan.total_cost.total_cost:<8.2f} "
            f"{plan.effective_time_cost:<8.2f} "
            f"{plan.expected_quality:<10.2%} "
            f"{plan.cost_benefit_score:<10.2f}"
        )
    
    # Beste Option basierend auf Cost-Benefit
    best_strategy = max(plans.items(), key=lambda x: x[1].cost_benefit_score)
    print(f"\n✅ Best Strategy: {best_strategy[0]} (C-B Score: {best_strategy[1].cost_benefit_score:.2f})")


def example_4_budget_constraints():
    """Example 4: Query mit Budget-Constraints"""
    print("\n" + "=" * 80)
    print("Example 4: Budget Constraints")
    print("=" * 80)
    
    builder = ExecutionPlanBuilder()
    
    query = "Komplexe wissenschaftliche Analyse"
    
    # Sehr strenges Budget
    budget = {
        "time": 1.0,  # Max 1.0 Zeit-Einheiten
        "computational": 2.0,  # Max 2.0 Rechenleistung
        "monetary": 1.5  # Max 1.5 monetäre Kosten
    }
    
    plan = builder.build_plan(query, budget=budget)
    
    print(f"\nQuery: {query}")
    print(f"Budget: {budget}")
    print(format_execution_plan(plan))
    
    # Validiere Budget
    print("\nBudget Validation:")
    print(f"  Time: {plan.total_cost.time_cost:.2f} <= {budget['time']} ✅")
    print(f"  Computational: {plan.total_cost.computational_cost:.2f} <= {budget['computational']} ✅")
    print(f"  Monetary: {plan.total_cost.monetary_cost:.2f} <= {budget['monetary']} ✅")


def example_5_resource_analysis():
    """Example 5: Ressourcen-Kosten-Analyse"""
    print("\n" + "=" * 80)
    print("Example 5: Resource Cost Analysis")
    print("=" * 80)
    
    print("\nResource Cost Matrix:")
    print(f"{'Resource':<20} {'Comp':<8} {'Time':<8} {'Money':<8} {'Quality':<10} {'C-B Ratio':<10}")
    print("-" * 80)
    
    for resource_type in ResourceType:
        cost = ResourceCostDatabase.get_cost(resource_type)
        print(
            f"{resource_type.value:<20} "
            f"{cost.computational_cost:<8.2f} "
            f"{cost.time_cost:<8.2f} "
            f"{cost.monetary_cost:<8.2f} "
            f"{cost.quality_score:<10.2%} "
            f"{cost.cost_benefit_ratio:<10.2f}"
        )
    
    # Beste Cost-Benefit-Ratio
    best_resource = max(
        ResourceType,
        key=lambda rt: ResourceCostDatabase.get_cost(rt).cost_benefit_ratio
    )
    best_cost = ResourceCostDatabase.get_cost(best_resource)
    print(f"\n✅ Best Cost-Benefit: {best_resource.value} (Ratio: {best_cost.cost_benefit_ratio:.2f})")


def example_6_query_approach_detection():
    """Example 6: Automatische Query-Approach-Erkennung"""
    print("\n" + "=" * 80)
    print("Example 6: Query Approach Detection")
    print("=" * 80)
    
    analyzer = QueryAnalyzer()
    
    test_queries = [
        "Was ist BGB?",
        "Übersicht über Umweltschutzgesetze",
        "Detaillierte Analyse der Zusammenhänge zwischen Verwaltungsrecht und Umweltschutz",
        "Welche wissenschaftlichen Studien gibt es zur Evidenz?",
        "Umfassende juristische Analyse mit Präzedenzfällen",
    ]
    
    print("\nQuery Classification:")
    print(f"{'Query':<70} {'Approach':<20}")
    print("-" * 90)
    
    for query in test_queries:
        approach = analyzer.analyze_query(query)
        query_short = query[:65] + "..." if len(query) > 65 else query
        print(f"{query_short:<70} {approach.value:<20}")


def example_7_parallelization():
    """Example 7: Parallelisierungs-Analyse"""
    print("\n" + "=" * 80)
    print("Example 7: Parallelization Analysis")
    print("=" * 80)
    
    optimizer = ExecutionPlanOptimizer()
    
    query = "Wissenschaftliche Recherche mit mehreren Datenquellen"
    plan = optimizer.optimize_for_speed(query)
    
    print(f"\nQuery: {query}")
    print(f"Execution Mode: {plan.execution_mode.value}")
    print(f"Parallelization Factor: {plan.parallelization_factor:.1f}x")
    
    print("\nParallelizable Steps:")
    parallel_count = 0
    sequential_count = 0
    
    for step in plan.steps:
        if step.can_parallelize:
            print(f"  ║ {step.step_id} - {step.resource_type.value} (PARALLEL)")
            parallel_count += 1
        else:
            print(f"  │ {step.step_id} - {step.resource_type.value} (SEQUENTIAL)")
            sequential_count += 1
    
    print(f"\n  Parallel: {parallel_count}, Sequential: {sequential_count}")
    print(f"  Time Savings: {(plan.parallelization_factor - 1) * 100:.0f}%")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  Polyglot Execution Plan Analysis System - Examples".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    
    try:
        example_1_simple_query()
        example_2_scientific_query()
        example_3_compare_strategies()
        example_4_budget_constraints()
        example_5_resource_analysis()
        example_6_query_approach_detection()
        example_7_parallelization()
        
        print("\n" + "=" * 80)
        print("✅ All examples completed successfully!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
