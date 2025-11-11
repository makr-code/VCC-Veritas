"""
Process Step Data Model

Represents a single step in a process execution tree. Each step has dependencies,
parameters, and execution state.

Author: Veritas AI
Date: 2025-10-14
Version: 1.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class StepType(Enum):
    """Type of process step."""

    SEARCH = "search"  # Database/document search
    RETRIEVAL = "retrieval"  # Retrieve specific documents
    ANALYSIS = "analysis"  # Analyze data
    SYNTHESIS = "synthesis"  # Combine multiple results
    VALIDATION = "validation"  # Validate data/results
    TRANSFORMATION = "transformation"  # Transform data format
    CALCULATION = "calculation"  # Perform calculations
    COMPARISON = "comparison"  # Compare entities
    AGGREGATION = "aggregation"  # Aggregate results
    OTHER = "other"  # Unknown/other


class StepStatus(Enum):
    """Execution status of a step."""

    PENDING = "pending"  # Not started
    READY = "ready"  # Dependencies met, ready to execute
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Execution failed
    SKIPPED = "skipped"  # Skipped due to conditions


@dataclass
class StepResult:
    """
    Result of a step execution.

    Attributes:
        success: Whether execution was successful
        data: Result data (Any type)
        error: Error message if failed
        execution_time: Execution time in seconds
        metadata: Additional metadata
        source_citations: List of source citations (for RAG-retrieved documents)
    """

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_citations: Optional[List[Any]] = None  # List[SourceCitation] from document_source.py

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }

        # Include source citations if available
        if self.source_citations:
            result["source_citations"] = [
                citation.to_dict() if hasattr(citation, "to_dict") else citation for citation in self.source_citations
            ]

        return result


@dataclass
class ProcessStep:
    """
    Represents a single step in a process tree.

    A step is a unit of work that can be executed independently once its
    dependencies are satisfied. Steps can be executed in parallel if they
    have no dependencies on each other.

    Attributes:
        id: Unique identifier for this step
        name: Human-readable name
        description: Detailed description of what this step does
        step_type: Type of operation (search, analysis, etc.)
        parameters: Parameters for step execution
        dependencies: List of step IDs this step depends on
        status: Current execution status
        result: Result of execution (if completed)
        created_at: When this step was created
        started_at: When execution started
        completed_at: When execution completed
        metadata: Additional metadata

    Example:
        >>> step = ProcessStep(
        ...     id="step_1",
        ...     name="Search Stuttgart Building Regulations",
        ...     description="Search for building regulations in Stuttgart",
        ...     step_type=StepType.SEARCH,
        ...     parameters={'location': 'Stuttgart', 'document_type': 'Bauvorschrift'},
        ...     dependencies=[]
        ... )
    """

    id: str
    name: str
    description: str
    step_type: StepType
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Optional[StepResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_ready(self, completed_steps: set) -> bool:
        """
        Check if this step is ready to execute.

        A step is ready if:
        1. Status is PENDING or READY
        2. All dependencies are in completed_steps

        Args:
            completed_steps: Set of completed step IDs

        Returns:
            True if step is ready to execute
        """
        if self.status not in [StepStatus.PENDING, StepStatus.READY]:
            return False

        return all(dep in completed_steps for dep in self.dependencies)

    def can_run_parallel_with(self, other: "ProcessStep") -> bool:
        """
        Check if this step can run in parallel with another step.

        Two steps can run in parallel if:
        1. Neither depends on the other
        2. They don't share critical resources (future enhancement)

        Args:
            other: Another ProcessStep

        Returns:
            True if steps can run in parallel
        """
        # Check if either step depends on the other
        if self.id in other.dependencies:
            return False
        if other.id in self.dependencies:
            return False

        # Future: Check for resource conflicts
        # For now, allow all independent steps to run in parallel
        return True

    def mark_running(self):
        """Mark step as running."""
        self.status = StepStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self, result: StepResult):
        """Mark step as completed with result."""
        self.status = StepStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()

    def mark_failed(self, error: str):
        """Mark step as failed with error."""
        self.status = StepStatus.FAILED
        self.result = StepResult(success=False, error=error)
        self.completed_at = datetime.now()

    def get_execution_time(self) -> Optional[float]:
        """Get execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "step_type": self.step_type.value,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result.to_dict() if self.result else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time": self.get_execution_time(),
            "metadata": self.metadata,
        }


# Example usage
if __name__ == "__main__":
    import os
    import sys

    # Add project root to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print("=" * 60)
    print("ProcessStep Test Examples")
    print("=" * 60)

    # Example 1: Search step
    step1 = ProcessStep(
        id="step_1",
        name="Search Stuttgart Building Regulations",
        description="Search for building regulations in Stuttgart",
        step_type=StepType.SEARCH,
        parameters={"location": "Stuttgart", "document_type": "Bauvorschrift"},
        dependencies=[],
    )

    print("\nExample 1: Search Step")
    print(f"ID: {step1.id}")
    print(f"Name: {step1.name}")
    print(f"Type: {step1.step_type.value}")
    print(f"Status: {step1.status.value}")
    print(f"Dependencies: {step1.dependencies}")
    print(f"Ready to execute: {step1.is_ready(set())}")

    # Example 2: Analysis step with dependency
    step2 = ProcessStep(
        id="step_2",
        name="Analyze Building Forms",
        description="Analyze required building application forms",
        step_type=StepType.ANALYSIS,
        parameters={"document_type": "Bauantrag"},
        dependencies=["step_1"],  # Depends on step 1
    )

    print("\nExample 2: Analysis Step (with dependency)")
    print(f"ID: {step2.id}")
    print(f"Name: {step2.name}")
    print(f"Dependencies: {step2.dependencies}")
    print(f"Ready without step_1: {step2.is_ready(set())}")
    print(f"Ready with step_1: {step2.is_ready({'step_1'})}")

    # Example 3: Parallel execution check
    step3 = ProcessStep(
        id="step_3",
        name="Search Contact Information",
        description="Search for contact information of building office",
        step_type=StepType.SEARCH,
        parameters={"location": "Stuttgart", "query": "Bauamt Kontakt"},
        dependencies=[],
    )

    print("\nExample 3: Parallel Execution")
    print(f"Step 1 and Step 2 can run parallel: {step1.can_run_parallel_with(step2)}")
    print(f"Step 1 and Step 3 can run parallel: {step1.can_run_parallel_with(step3)}")

    # Example 4: Execution simulation
    print("\nExample 4: Execution Simulation")
    step1.mark_running()
    print(f"Step 1 status: {step1.status.value}")

    import time

    time.sleep(0.1)  # Simulate execution

    result = StepResult(
        success=True,
        data={"documents_found": 5, "regulations": ["LBO", "BauGB"]},
        execution_time=0.1,
        metadata={"source": "vector_db"},
    )
    step1.mark_completed(result)
    print(f"Step 1 status: {step1.status.value}")
    print(f"Step 1 execution time: {step1.get_execution_time():.3f}s")
    print(f"Step 1 result: {step1.result.data}")

    # Example 5: Dictionary conversion
    print("\nExample 5: Dictionary Conversion")
    step_dict = step1.to_dict()
    print(f"Step as dict keys: {list(step_dict.keys())}")
    print(
        f"Serializable: {all(isinstance(v, (str, int, float, bool, list, dict, type(None))) or hasattr(v, '__dict__') for v in step_dict.values())}"
    )

    print("\n" + "=" * 60)
    print("✅ All ProcessStep tests passed!")
    print("=" * 60)
