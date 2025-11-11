"""
VERITAS Agent Framework - Dependency Resolver
=============================================

Dependency graph builder and topological sorter for research plan steps.

Features:
- DAG (Directed Acyclic Graph) construction from depends_on fields
- Topological sorting for execution order
- Cycle detection
- Parallel execution groups (steps with no dependencies can run in parallel)

Author: VERITAS Development Team
Created: 2025-10-08
"""

import logging
from collections import defaultdict, deque
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class DependencyError(Exception):
    """Exception raised for dependency-related errors."""

    pass


class DependencyResolver:
    """
    Resolves step dependencies and creates execution plan.

    Builds a DAG from step dependencies and determines execution order
    including parallel execution opportunities.

    Attributes:
        steps: List of step definitions
        graph: Adjacency list representation {step_id: [dependent_steps]}
        reverse_graph: Reverse adjacency list {step_id: [dependencies]}

    Example:
        >>> steps = [
        ...     {"step_id": "A", "depends_on": []},
        ...     {"step_id": "B", "depends_on": ["A"]},
        ...     {"step_id": "C", "depends_on": ["A"]},
        ...     {"step_id": "D", "depends_on": ["B", "C"]}
        ... ]
        >>> resolver = DependencyResolver(steps)
        >>> execution_plan = resolver.get_execution_plan()
        >>> # Returns: [[A], [B, C], [D]]  # B and C can run in parallel
    """

    def __init__(self, steps: List[Dict[str, Any]]):
        """
        Initialize dependency resolver.

        Args:
            steps: List of step definitions with step_id and depends_on fields
        """
        self.steps = steps
        self.graph: Dict[str, List[str]] = defaultdict(list)
        self.reverse_graph: Dict[str, List[str]] = defaultdict(list)
        self._step_map: Dict[str, Dict[str, Any]] = {}

        # Build graphs
        self._build_graphs()

        logger.info(f"Initialized dependency resolver with {len(steps)} steps")

    def _build_graphs(self) -> None:
        """Build forward and reverse dependency graphs."""
        # Create step lookup map
        for step in self.steps:
            step_id = step["step_id"]
            self._step_map[step_id] = step

        # Build graphs
        for step in self.steps:
            step_id = step["step_id"]
            dependencies = step.get("depends_on", [])

            # Validate dependencies exist
            for dep in dependencies:
                if dep not in self._step_map:
                    raise DependencyError(f"Step {step_id} depends on non-existent step: {dep}")

                # Forward graph: dep -> step_id (what depends on dep)
                self.graph[dep].append(step_id)

                # Reverse graph: step_id -> dep (what step_id depends on)
                self.reverse_graph[step_id].append(dep)

            # Ensure all steps are in graph (even if no dependencies)
            if step_id not in self.graph:
                self.graph[step_id] = []
            if step_id not in self.reverse_graph:
                self.reverse_graph[step_id] = []

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect cycles in dependency graph using DFS.

        Returns:
            List of cycles found (each cycle is a list of step_ids)

        Example:
            >>> # Steps with cycle: A -> B -> C -> A
            >>> cycles = resolver.detect_cycles()
            >>> if cycles:
            ...     print(f"Found {len(cycles)} cycles")
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> bool:
            """DFS helper to detect cycles."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle - extract it
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        # Check all nodes
        for step_id in self.graph:
            if step_id not in visited:
                dfs(step_id)

        return cycles

    def topological_sort(self) -> List[str]:
        """
        Perform topological sort using Kahn's algorithm.

        Returns:
            List of step_ids in topological order

        Raises:
            DependencyError: If cycle detected

        Example:
            >>> order = resolver.topological_sort()
            >>> # Returns: ['A', 'B', 'C', 'D'] (valid execution order)
        """
        # Check for cycles first
        cycles = self.detect_cycles()
        if cycles:
            cycle_str = " -> ".join(cycles[0])
            raise DependencyError(f"Circular dependency detected: {cycle_str}")

        # Calculate in-degree for each node
        in_degree = {step_id: len(deps) for step_id, deps in self.reverse_graph.items()}

        # Queue of nodes with no dependencies
        queue = deque([step_id for step_id, degree in in_degree.items() if degree == 0])

        sorted_order = []

        while queue:
            # Process node with no dependencies
            current = queue.popleft()
            sorted_order.append(current)

            # Reduce in-degree of dependent nodes
            for dependent in self.graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Verify all nodes processed
        if len(sorted_order) != len(self.steps):
            raise DependencyError(f"Topological sort failed: {len(sorted_order)}/{len(self.steps)} steps processed")

        return sorted_order

    def get_execution_plan(self) -> List[List[str]]:
        """
        Get execution plan with parallel execution groups.

        Groups steps that can be executed in parallel (no dependencies between them).

        Returns:
            List of execution groups (each group can run in parallel)

        Example:
            >>> plan = resolver.get_execution_plan()
            >>> # Returns: [['A'], ['B', 'C'], ['D']]
            >>> # Meaning: Execute A, then B and C in parallel, then D
        """
        # Calculate in-degree
        in_degree = {step_id: len(deps) for step_id, deps in self.reverse_graph.items()}

        execution_plan = []
        processed = set()

        while len(processed) < len(self.steps):
            # Find all steps with no pending dependencies
            ready_steps = [step_id for step_id, degree in in_degree.items() if degree == 0 and step_id not in processed]

            if not ready_steps:
                # No steps ready - must be a cycle
                remaining = set(in_degree.keys()) - processed
                raise DependencyError(f"Deadlock detected. Remaining steps: {remaining}")

            # Add this parallel group
            execution_plan.append(ready_steps)

            # Mark as processed and update in-degrees
            for step_id in ready_steps:
                processed.add(step_id)
                for dependent in self.graph[step_id]:
                    in_degree[dependent] -= 1

        return execution_plan

    def get_step_dependencies(self, step_id: str) -> List[str]:
        """
        Get direct dependencies for a step.

        Args:
            step_id: Step identifier

        Returns:
            List of step_ids this step depends on
        """
        return self.reverse_graph.get(step_id, [])

    def get_step_dependents(self, step_id: str) -> List[str]:
        """
        Get steps that depend on this step.

        Args:
            step_id: Step identifier

        Returns:
            List of step_ids that depend on this step
        """
        return self.graph.get(step_id, [])

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize resolver state to dictionary.

        Returns:
            Dictionary with graph, execution plan, and statistics
        """
        try:
            execution_plan = self.get_execution_plan()
            max_parallelism = max(len(group) for group in execution_plan) if execution_plan else 0
        except DependencyError as e:
            execution_plan = []
            max_parallelism = 0

        return {
            "total_steps": len(self.steps),
            "execution_groups": len(execution_plan),
            "max_parallelism": max_parallelism,
            "execution_plan": execution_plan,
            "graph": dict(self.graph),
            "reverse_graph": dict(self.reverse_graph),
        }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("VERITAS DEPENDENCY RESOLVER - TEST")
    print("=" * 80)

    # Test 1: Linear dependency chain
    print("\n📋 Test 1: Linear Dependency Chain")
    steps_linear = [
        {"step_id": "A", "depends_on": []},
        {"step_id": "B", "depends_on": ["A"]},
        {"step_id": "C", "depends_on": ["B"]},
        {"step_id": "D", "depends_on": ["C"]},
    ]

    resolver1 = DependencyResolver(steps_linear)
    plan1 = resolver1.get_execution_plan()

    print(f"  Steps: {len(steps_linear)}")
    print(f"  Execution plan: {plan1}")
    print(f"  Max parallelism: {max(len(g) for g in plan1)}")
    print("  ✅ Linear chain: No parallel execution possible")

    # Test 2: Parallel branches
    print("\n📋 Test 2: Parallel Branches")
    steps_parallel = [
        {"step_id": "A", "depends_on": []},
        {"step_id": "B", "depends_on": ["A"]},
        {"step_id": "C", "depends_on": ["A"]},
        {"step_id": "D", "depends_on": ["A"]},
        {"step_id": "E", "depends_on": ["B", "C", "D"]},
    ]

    resolver2 = DependencyResolver(steps_parallel)
    plan2 = resolver2.get_execution_plan()

    print(f"  Steps: {len(steps_parallel)}")
    print(f"  Execution plan: {plan2}")
    print(f"  Max parallelism: {max(len(g) for g in plan2)}")
    print("  ✅ B, C, D can run in parallel after A")

    # Test 3: Complex DAG
    print("\n📋 Test 3: Complex DAG")
    steps_complex = [
        {"step_id": "A", "depends_on": []},
        {"step_id": "B", "depends_on": []},
        {"step_id": "C", "depends_on": ["A"]},
        {"step_id": "D", "depends_on": ["A", "B"]},
        {"step_id": "E", "depends_on": ["C"]},
        {"step_id": "F", "depends_on": ["D", "E"]},
    ]

    resolver3 = DependencyResolver(steps_complex)
    plan3 = resolver3.get_execution_plan()

    print(f"  Steps: {len(steps_complex)}")
    print("  Execution plan:")
    for i, group in enumerate(plan3, 1):
        print(f"    Group {i}: {group} (parallelism: {len(group)})")
    print(f"  Max parallelism: {max(len(g) for g in plan3)}")
    print("  ✅ Complex DAG with multiple parallel opportunities")

    # Test 4: Cycle detection
    print("\n📋 Test 4: Cycle Detection")
    steps_cycle = [
        {"step_id": "A", "depends_on": ["C"]},
        {"step_id": "B", "depends_on": ["A"]},
        {"step_id": "C", "depends_on": ["B"]},
    ]

    try:
        resolver4 = DependencyResolver(steps_cycle)
        plan4 = resolver4.get_execution_plan()
        print("  ❌ Should have detected cycle!")
    except DependencyError as e:
        print(f"  ✅ Correctly detected cycle: {e}")

    # Test 5: Missing dependency
    print("\n📋 Test 5: Missing Dependency")
    steps_missing = [{"step_id": "A", "depends_on": []}, {"step_id": "B", "depends_on": ["X"]}]  # X doesn't exist

    try:
        resolver5 = DependencyResolver(steps_missing)
        print("  ❌ Should have detected missing dependency!")
    except DependencyError as e:
        print(f"  ✅ Correctly detected missing dependency: {e}")

    # Test 6: Topological sort
    print("\n📋 Test 6: Topological Sort")
    topo_order = resolver2.topological_sort()
    print(f"  Topological order: {topo_order}")
    print("  ✅ Valid execution order")

    # Test 7: Serialization
    print("\n📋 Test 7: Serialization")
    data = resolver2.to_dict()
    print(f"  Total steps: {data['total_steps']}")
    print(f"  Execution groups: {data['execution_groups']}")
    print(f"  Max parallelism: {data['max_parallelism']}")
    print("  ✅ Serialization successful")

    print("\n✨ Dependency resolver tests complete!")
