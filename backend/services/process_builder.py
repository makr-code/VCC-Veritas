"""
Process Builder Service

Converts NLP analysis into an executable ProcessTree. This is the bridge between
query understanding (NLPService) and process execution (ProcessExecutor).

The ProcessBuilder infers necessary steps and their dependencies based on:
- Detected intent (what the user wants)
- Extracted entities (what to search for)
- Question type (how to structure the answer)

Author: Veritas AI
Date: 2025-10-14
Version: 1.0
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional, Set

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.models.nlp_models import EntityType, IntentType, NLPAnalysisResult, QuestionType
from backend.models.process_step import ProcessStep, StepType
from backend.models.process_tree import ProcessTree

logger = logging.getLogger(__name__)


class ProcessBuilder:
    """
    Builds a ProcessTree from NLP analysis.

    The builder uses rule-based inference to determine:
    1. What steps are needed (based on intent and entities)
    2. How steps depend on each other
    3. What parameters each step needs

    Example:
        >>> nlp = NLPService()
        >>> builder = ProcessBuilder(nlp)
        >>> tree = builder.build_process_tree("Bauantrag für Stuttgart")
        >>> # tree has 3 steps: search regulations, search forms, compile checklist
    """

    def __init__(self, nlp_service):
        """
        Initialize ProcessBuilder.

        Args:
            nlp_service: NLPService instance for query analysis
        """
        self.nlp = nlp_service
        self.step_counter = 0

        # Step templates for different intents
        self._init_step_templates()

    def _init_step_templates(self):
        """Initialize step templates for different intents."""
        # Templates define what steps are needed for each intent type
        self.step_templates = {
            IntentType.FACT_RETRIEVAL: ["search", "retrieval"],
            IntentType.PROCEDURE_QUERY: ["search", "retrieval", "synthesis"],
            IntentType.COMPARISON: ["search", "search", "analysis", "comparison"],
            IntentType.TIMELINE: ["search", "retrieval", "aggregation"],
            IntentType.CALCULATION: ["search", "retrieval", "calculation"],
            IntentType.DEFINITION: ["search", "retrieval"],
            IntentType.LOCATION_QUERY: ["search", "retrieval"],
            IntentType.CONTACT_QUERY: ["search", "retrieval"],
            IntentType.UNKNOWN: ["search"],
        }

    def build_process_tree(self, query: str) -> ProcessTree:
        """
        Build a ProcessTree from a query.

        Args:
            query: User query

        Returns:
            ProcessTree with inferred steps and dependencies
        """
        logger.info(f"Building process tree for query: {query}")

        # Step 1: Analyze query with NLP
        nlp_result = self.nlp.analyze(query)

        # Step 2: Create ProcessTree
        tree = ProcessTree(
            query=query,
            nlp_analysis=nlp_result,
            metadata={
                "intent": nlp_result.intent.intent_type.value,
                "entities": [e.entity_type.value for e in nlp_result.entities],
                "question_type": nlp_result.question_type.value,
            },
        )

        # Step 3: Infer steps based on intent and entities
        steps = self._infer_steps(nlp_result)

        # Step 4: Infer dependencies between steps
        self._infer_dependencies(steps, nlp_result)

        # Step 5: Add steps to tree
        for step in steps:
            tree.add_step(step)

        # Step 6: Calculate execution order
        tree.get_parallel_groups()

        # Step 7: Estimate execution time
        tree.estimated_time = self._estimate_execution_time(tree)

        logger.info(f"Process tree built: {tree.total_steps} steps, " f"{len(tree.execution_order)} levels")

        return tree

    def _infer_steps(self, nlp_result: NLPAnalysisResult) -> List[ProcessStep]:
        """
        Infer process steps from NLP analysis.

        Args:
            nlp_result: NLP analysis result

        Returns:
            List of ProcessSteps
        """
        steps = []
        self.step_counter = 0

        intent = nlp_result.intent.intent_type
        entities = nlp_result.entities
        params = nlp_result.parameters

        # Get step template for this intent
        template = self.step_templates.get(intent, ["search"])

        # Special handling for comparison (needs 2 search steps)
        if intent == IntentType.COMPARISON:
            steps.extend(self._create_comparison_steps(nlp_result))

        # Special handling for procedure query
        elif intent == IntentType.PROCEDURE_QUERY:
            steps.extend(self._create_procedure_steps(nlp_result))

        # Special handling for calculation
        elif intent == IntentType.CALCULATION:
            steps.extend(self._create_calculation_steps(nlp_result))

        # Default: Create steps from template
        else:
            steps.extend(self._create_default_steps(template, nlp_result))

        return steps

    def _create_comparison_steps(self, nlp_result: NLPAnalysisResult) -> List[ProcessStep]:
        """Create steps for comparison intent."""
        steps = []

        # Find entities to compare
        entities = [
            e
            for e in nlp_result.entities
            if e.entity_type in [EntityType.ORGANIZATION, EntityType.DOCUMENT, EntityType.PROCEDURE]
        ]

        if len(entities) >= 2:
            # Search step for entity 1
            steps.append(
                self._create_step(
                    f"Search {entities[0].text} information",
                    f"Search for information about {entities[0].text}",
                    StepType.SEARCH,
                    {"entity": entities[0].text, "entity_type": entities[0].entity_type.value},
                    [],
                )
            )

            # Search step for entity 2
            steps.append(
                self._create_step(
                    f"Search {entities[1].text} information",
                    f"Search for information about {entities[1].text}",
                    StepType.SEARCH,
                    {"entity": entities[1].text, "entity_type": entities[1].entity_type.value},
                    [],
                )
            )

            # Analysis for both
            step1_id = steps[0].id
            step2_id = steps[1].id

            steps.append(
                self._create_step(
                    f"Analyze {entities[0].text}",
                    f"Analyze key characteristics of {entities[0].text}",
                    StepType.ANALYSIS,
                    {},
                    [step1_id],
                )
            )

            steps.append(
                self._create_step(
                    f"Analyze {entities[1].text}",
                    f"Analyze key characteristics of {entities[1].text}",
                    StepType.ANALYSIS,
                    {},
                    [step2_id],
                )
            )

            # Comparison step
            step3_id = steps[2].id
            step4_id = steps[3].id

            steps.append(
                self._create_step(
                    f"Compare {entities[0].text} vs {entities[1].text}",
                    "Compare differences and similarities",
                    StepType.COMPARISON,
                    {"entities": [entities[0].text, entities[1].text]},
                    [step3_id, step4_id],
                )
            )

        else:
            # Fallback: simple search
            steps.append(
                self._create_step(
                    "Search comparison information",
                    "Search for comparison information",
                    StepType.SEARCH,
                    {"query": nlp_result.query},
                    [],
                )
            )

        return steps

    def _create_procedure_steps(self, nlp_result: NLPAnalysisResult) -> List[ProcessStep]:
        """Create steps for procedure query intent."""
        steps = []

        # Extract location and document type
        location = nlp_result.parameters.location
        doc_type = nlp_result.parameters.document_type
        proc_type = nlp_result.parameters.procedure_type

        # Step 1: Search regulations/requirements
        search_params = {}
        if location:
            search_params["location"] = location
        if doc_type:
            search_params["document_type"] = doc_type
        if proc_type:
            search_params["procedure_type"] = proc_type

        steps.append(
            self._create_step(
                f"Search requirements for {doc_type or proc_type or 'procedure'}",
                "Search for requirements and regulations",
                StepType.SEARCH,
                search_params,
                [],
            )
        )

        # Step 2: Search forms/documents
        steps.append(
            self._create_step(
                "Search required forms", "Search for necessary forms and documents", StepType.SEARCH, search_params, []
            )
        )

        # Step 3: Compile checklist
        step1_id = steps[0].id
        step2_id = steps[1].id

        steps.append(
            self._create_step(
                "Compile procedure checklist",
                "Compile complete checklist with all requirements",
                StepType.SYNTHESIS,
                {},
                [step1_id, step2_id],
            )
        )

        return steps

    def _create_calculation_steps(self, nlp_result: NLPAnalysisResult) -> List[ProcessStep]:
        """Create steps for calculation intent."""
        steps = []

        # Step 1: Search for pricing/cost information
        search_params = {}
        if nlp_result.parameters.document_type:
            search_params["document_type"] = nlp_result.parameters.document_type
        if nlp_result.parameters.location:
            search_params["location"] = nlp_result.parameters.location

        steps.append(
            self._create_step(
                "Search cost information", "Search for pricing and cost information", StepType.SEARCH, search_params, []
            )
        )

        # Step 2: Calculate total cost
        step1_id = steps[0].id

        steps.append(
            self._create_step(
                "Calculate total cost", "Calculate total cost based on found information", StepType.CALCULATION, {}, [step1_id]
            )
        )

        return steps

    def _create_default_steps(self, template: List[str], nlp_result: NLPAnalysisResult) -> List[ProcessStep]:
        """Create default steps from template."""
        steps = []
        previous_ids = []

        for step_type_name in template:
            step_type = StepType[step_type_name.upper()]

            # Create step with generic name
            step = self._create_step(
                f"{step_type_name.title()} information",
                f"{step_type_name.title()} relevant information for query",
                step_type,
                {"query": nlp_result.query, **nlp_result.parameters.to_dict()},
                previous_ids.copy(),
            )

            steps.append(step)
            previous_ids = [step.id]

        return steps

    def _create_step(
        self, name: str, description: str, step_type: StepType, parameters: Dict[str, Any], dependencies: List[str]
    ) -> ProcessStep:
        """Helper to create a ProcessStep with unique ID."""
        self.step_counter += 1
        return ProcessStep(
            id=f"step_{self.step_counter}",
            name=name,
            description=description,
            step_type=step_type,
            parameters=parameters,
            dependencies=dependencies,
        )

    def _infer_dependencies(self, steps: List[ProcessStep], nlp_result: NLPAnalysisResult):
        """
        Infer and refine dependencies between steps.

        This is already done in step creation, but this method can add
        additional dependency logic if needed.

        Args:
            steps: List of ProcessSteps
            nlp_result: NLP analysis result
        """
        # Dependencies are already set during step creation
        # This method can be extended for more complex dependency inference
        pass

    def _estimate_execution_time(self, tree: ProcessTree) -> float:
        """
        Estimate total execution time.

        Args:
            tree: ProcessTree

        Returns:
            Estimated time in seconds
        """
        # Simple estimation: sum of max times per parallel group
        # Assume: search=2s, retrieval=1s, analysis=3s, synthesis=2s, etc.
        time_estimates = {
            StepType.SEARCH: 2.0,
            StepType.RETRIEVAL: 1.0,
            StepType.ANALYSIS: 3.0,
            StepType.SYNTHESIS: 2.0,
            StepType.VALIDATION: 1.0,
            StepType.TRANSFORMATION: 1.0,
            StepType.CALCULATION: 1.5,
            StepType.COMPARISON: 2.5,
            StepType.AGGREGATION: 2.0,
            StepType.OTHER: 2.0,
        }

        total_time = 0.0
        for group in tree.get_parallel_groups():
            # Max time in this parallel group
            group_time = max(time_estimates.get(tree.get_step(sid).step_type, 2.0) for sid in group)
            total_time += group_time

        return total_time


# Example usage
if __name__ == "__main__":
    from backend.services.nlp_service import NLPService

    print("=" * 60)
    print("ProcessBuilder Test Examples")
    print("=" * 60)

    # Initialize services
    nlp = NLPService()
    builder = ProcessBuilder(nlp)

    # Test queries
    test_queries = [
        "Bauantrag für Einfamilienhaus in Stuttgart",
        "Unterschied zwischen GmbH und AG",
        "Wie viel kostet ein Bauantrag?",
        "Kontakt Bauamt München",
        "Was ist der Hauptsitz von BMW?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {i}: {query}")
        print("=" * 60)

        # Build process tree
        tree = builder.build_process_tree(query)

        # Display results
        print(f"\nQuery: {tree.query}")
        print(f"Intent: {tree.metadata['intent']}")
        print(f"Total steps: {tree.total_steps}")
        print(f"Estimated time: {tree.estimated_time:.1f}s")

        print("\nExecution Plan:")
        for level_num, group in enumerate(tree.get_parallel_groups()):
            print(f"\nLevel {level_num} ({len(group)} steps in parallel):")
            for step_id in group:
                step = tree.get_step(step_id)
                print(f"  - {step.name} ({step.step_type.value})")
                if step.parameters:
                    print(f"    Parameters: {step.parameters}")
                if step.dependencies:
                    dep_names = [tree.get_step(d).name for d in step.dependencies]
                    print(f"    Depends on: {dep_names}")

    print("\n" + "=" * 60)
    print("✅ All ProcessBuilder tests completed!")
    print("=" * 60)
