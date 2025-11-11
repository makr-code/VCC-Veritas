"""
Process Tree Data Model

Represents a complete process execution plan with steps and dependencies.
The tree is executed by the ProcessExecutor using topological sorting.

Author: Veritas AI
Date: 2025-10-14
Version: 1.0
"""

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.models.nlp_models import NLPAnalysisResult
from backend.models.process_step import ProcessStep, StepStatus, StepType


@dataclass
class ProcessTree:
    """
    Represents a complete process execution plan.

    A process tree contains all steps needed to answer a query, along with
    their dependencies. The tree can be executed in optimal order using
    topological sorting and parallel execution.

    Attributes:
        query: Original user query
        nlp_analysis: NLP analysis result
        steps: Dictionary of step_id -> ProcessStep
        execution_order: List of execution levels (parallel groups)
        total_steps: Total number of steps
        estimated_time: Estimated execution time (seconds)
        created_at: When this tree was created
        metadata: Additional metadata

    Example:
        >>> tree = ProcessTree(
        ...     query="Bauantrag für Stuttgart",
        ...     nlp_analysis=nlp_result,
        ...     steps={
        ...         'step_1': ProcessStep(...),
        ...         'step_2': ProcessStep(...)
        ...     }
        ... )
        >>> # Execution order: [[step_1, step_2], [step_3]]
        >>> # step_1 and step_2 run in parallel, then step_3
    """

    query: str
    nlp_analysis: Optional[NLPAnalysisResult]
    steps: Dict[str, ProcessStep] = field(default_factory=dict)
    execution_order: List[List[str]] = field(default_factory=list)
    total_steps: int = 0
    estimated_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: ProcessStep):
        """
        Add a step to the tree.

        Args:
            step: ProcessStep to add
        """
        self.steps[step.id] = step
        self.total_steps = len(self.steps)

    def get_step(self, step_id: str) -> Optional[ProcessStep]:
        """
        Get a step by ID.

        Args:
            step_id: Step ID

        Returns:
            ProcessStep or None if not found
        """
        return self.steps.get(step_id)

    def get_root_steps(self) -> List[ProcessStep]:
        """
        Get all root steps (steps with no dependencies).

        Returns:
            List of root ProcessSteps
        """
        return [step for step in self.steps.values() if not step.dependencies]

    def get_leaf_steps(self) -> List[ProcessStep]:
        """
        Get all leaf steps (steps that no other step depends on).

        Returns:
            List of leaf ProcessSteps
        """
        # Get all steps that are dependencies
        dependency_ids = set()
        for step in self.steps.values():
            dependency_ids.update(step.dependencies)

        # Leaf steps are steps NOT in dependency_ids
        return [step for step in self.steps.values() if step.id not in dependency_ids]

    def get_ready_steps(self) -> List[ProcessStep]:
        """
        Get all steps that are ready to execute.

        A step is ready if all its dependencies are completed.

        Returns:
            List of ready ProcessSteps
        """
        completed_ids = {step.id for step in self.steps.values() if step.status == StepStatus.COMPLETED}

        return [step for step in self.steps.values() if step.is_ready(completed_ids)]

    def get_parallel_groups(self) -> List[List[str]]:
        """
        Get execution order as parallel groups.

        Uses simple level-based grouping: steps at the same dependency
        level can run in parallel.

        Returns:
            List of parallel groups (each group is a list of step IDs)
        """
        if self.execution_order:
            return self.execution_order

        # Build execution order using level-based grouping
        levels: Dict[int, List[str]] = {}
        visited = set()

        def get_level(step_id: str) -> int:
            """Get the execution level of a step."""
            if step_id in visited:
                return levels.get(step_id, 0)

            step = self.steps[step_id]
            visited.add(step_id)

            if not step.dependencies:
                level = 0
            else:
                # Level is max(dependency levels) + 1
                dep_levels = [get_level(dep) for dep in step.dependencies]
                level = max(dep_levels) + 1

            if level not in levels:
                levels[level] = []
            levels[level].append(step_id)

            return level

        # Calculate levels for all steps
        for step_id in self.steps:
            get_level(step_id)

        # Convert to execution order
        self.execution_order = [levels[i] for i in sorted(levels.keys())]
        return self.execution_order

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get tree statistics.

        Returns:
            Dictionary with statistics
        """
        status_counts = {}
        for status in StepStatus:
            count = sum(1 for step in self.steps.values() if step.status == status)
            status_counts[status.value] = count

        type_counts = {}
        for step_type in StepType:
            count = sum(1 for step in self.steps.values() if step.step_type == step_type)
            type_counts[step_type.value] = count

        return {
            "total_steps": self.total_steps,
            "status_counts": status_counts,
            "type_counts": type_counts,
            "root_steps": len(self.get_root_steps()),
            "leaf_steps": len(self.get_leaf_steps()),
            "execution_levels": len(self.get_parallel_groups()),
            "estimated_time": self.estimated_time,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "nlp_analysis": self.nlp_analysis.to_dict() if self.nlp_analysis else None,
            "steps": {step_id: step.to_dict() for step_id, step in self.steps.items()},
            "execution_order": self.execution_order,
            "total_steps": self.total_steps,
            "estimated_time": self.estimated_time,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "statistics": self.get_statistics(),
        }


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("ProcessTree Test Examples")
    print("=" * 60)

    # Example 1: Simple tree with 3 steps
    tree = ProcessTree(query="Bauantrag für Stuttgart", nlp_analysis=None)

    # Add steps
    step1 = ProcessStep(
        id="step_1",
        name="Search Building Regulations",
        description="Search for building regulations in Stuttgart",
        step_type=StepType.SEARCH,
        parameters={"location": "Stuttgart"},
        dependencies=[],
    )
    tree.add_step(step1)

    step2 = ProcessStep(
        id="step_2",
        name="Search Application Forms",
        description="Search for building application forms",
        step_type=StepType.SEARCH,
        parameters={"document_type": "Bauantrag"},
        dependencies=[],
    )
    tree.add_step(step2)

    step3 = ProcessStep(
        id="step_3",
        name="Compile Checklist",
        description="Compile checklist from regulations and forms",
        step_type=StepType.SYNTHESIS,
        parameters={},
        dependencies=["step_1", "step_2"],
    )
    tree.add_step(step3)

    print("\nExample 1: Simple Tree Structure")
    print(f"Query: {tree.query}")
    print(f"Total steps: {tree.total_steps}")
    print(f"Root steps: {[s.name for s in tree.get_root_steps()]}")
    print(f"Leaf steps: {[s.name for s in tree.get_leaf_steps()]}")

    # Example 2: Execution order
    print("\nExample 2: Execution Order")
    parallel_groups = tree.get_parallel_groups()
    for i, group in enumerate(parallel_groups):
        step_names = [tree.get_step(sid).name for sid in group]
        print(f"Level {i}: {step_names}")
        print(f"  → Can run {len(group)} steps in parallel")

    # Example 3: Ready steps
    print("\nExample 3: Ready Steps")
    ready = tree.get_ready_steps()
    print(f"Ready to execute: {[s.name for s in ready]}")

    # Mark step1 and step2 as completed
    from backend.models.process_step import StepResult

    step1.mark_completed(StepResult(success=True, data={"regulations": ["LBO", "BauGB"]}))
    step2.mark_completed(StepResult(success=True, data={"forms": ["Bauantrag.pdf"]}))

    ready = tree.get_ready_steps()
    print(f"After completing level 0: {[s.name for s in ready]}")

    # Example 4: Statistics
    print("\nExample 4: Tree Statistics")
    stats = tree.get_statistics()
    print(f"Total steps: {stats['total_steps']}")
    print(f"Status counts: {stats['status_counts']}")
    print(f"Type counts: {stats['type_counts']}")
    print(f"Execution levels: {stats['execution_levels']}")

    # Example 5: Complex tree with 5 steps
    print("\nExample 5: Complex Tree (5 steps)")
    complex_tree = ProcessTree(query="Unterschied zwischen GmbH und AG gründen in München", nlp_analysis=None)

    # Add steps
    steps_config = [
        ("s1", "Search GmbH info", StepType.SEARCH, {"entity": "GmbH"}, []),
        ("s2", "Search AG info", StepType.SEARCH, {"entity": "AG"}, []),
        ("s3", "Analyze GmbH", StepType.ANALYSIS, {}, ["s1"]),
        ("s4", "Analyze AG", StepType.ANALYSIS, {}, ["s2"]),
        ("s5", "Compare GmbH vs AG", StepType.COMPARISON, {}, ["s3", "s4"]),
    ]

    for step_id, name, step_type, params, deps in steps_config:
        step = ProcessStep(id=step_id, name=name, description=name, step_type=step_type, parameters=params, dependencies=deps)
        complex_tree.add_step(step)

    print(f"Query: {complex_tree.query}")
    print(f"Total steps: {complex_tree.total_steps}")

    # Show execution order
    print("\nExecution Order:")
    parallel_groups = complex_tree.get_parallel_groups()
    for i, group in enumerate(parallel_groups):
        step_names = [complex_tree.get_step(sid).name for sid in group]
        print(f"Level {i}: {step_names} ({len(group)} parallel)")

    # Example 6: Dictionary conversion
    print("\nExample 6: Dictionary Conversion")
    tree_dict = tree.to_dict()
    print(f"Dictionary keys: {list(tree_dict.keys())}")
    print(f"Steps serialized: {len(tree_dict['steps'])}")
    print(f"Execution order: {tree_dict['execution_order']}")

    print("\n" + "=" * 60)
    print("✅ All ProcessTree tests passed!")
    print("=" * 60)
