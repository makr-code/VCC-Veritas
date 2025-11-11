"""
VERITAS Agent Framework - Schema Validation
============================================

JSON Schema validation for research plans and agent configurations.

Usage:
    from backend.agents.framework.schema_validation import validate_research_plan

    plan = {...}
    is_valid, errors = validate_research_plan(plan)

Created: 2025-10-08
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from jsonschema import Draft202012Validator, SchemaError, ValidationError
    from jsonschema.validators import validator_for

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("⚠️  jsonschema not installed. Install with: pip install jsonschema")

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates research plans against JSON schema."""

    def __init__(self, schema_dir: Optional[Path] = None):
        """
        Initialize schema validator.

        Args:
            schema_dir: Directory containing schema files.
                       Defaults to backend/agents/framework/schemas/
        """
        if schema_dir is None:
            schema_dir = Path(__file__).parent / "schemas"

        self.schema_dir = Path(schema_dir)
        self.schemas = {}
        self._load_schemas()

    def _load_schemas(self):
        """Load all schema files from schema directory."""
        if not self.schema_dir.exists():
            logger.warning(f"Schema directory not found: {self.schema_dir}")
            return

        for schema_file in self.schema_dir.glob("*.json"):
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    schema = json.load(f)

                schema_name = schema_file.stem
                self.schemas[schema_name] = schema
                logger.info(f"Loaded schema: {schema_name}")

            except Exception as e:
                logger.error(f"Error loading schema {schema_file}: {e}")

    def get_schema(self, schema_name: str) -> Optional[Dict]:
        """
        Get schema by name.

        Args:
            schema_name: Name of schema (e.g., 'research_plan')

        Returns:
            Schema dictionary or None if not found
        """
        return self.schemas.get(schema_name)

    def validate(self, document: Dict[str, Any], schema_name: str = "research_plan.schema") -> Tuple[bool, List[str]]:
        """
        Validate document against schema.

        Args:
            document: Document to validate
            schema_name: Name of schema to validate against

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        if not JSONSCHEMA_AVAILABLE:
            return False, ["jsonschema library not available"]

        schema = self.get_schema(schema_name)
        if schema is None:
            return False, [f"Schema '{schema_name}' not found"]

        try:
            # Get appropriate validator class for schema
            ValidatorClass = validator_for(schema)
            ValidatorClass.check_schema(schema)

            # Create validator instance
            validator = ValidatorClass(schema)

            # Validate document
            errors = list(validator.iter_errors(document))

            if errors:
                error_messages = [f"{'.'.join(map(str, e.path))}: {e.message}" for e in errors]
                return False, error_messages

            return True, []

        except SchemaError as e:
            return False, [f"Schema error: {e.message}"]
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]

    def validate_strict(self, document: Dict[str, Any], schema_name: str = "research_plan") -> bool:
        """
        Strict validation - raises exception on error.

        Args:
            document: Document to validate
            schema_name: Name of schema to validate against

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
            SchemaError: If schema is invalid
        """
        if not JSONSCHEMA_AVAILABLE:
            raise ImportError("jsonschema library not available")

        schema = self.get_schema(schema_name)
        if schema is None:
            raise ValueError(f"Schema '{schema_name}' not found")

        ValidatorClass = validator_for(schema)
        validator = ValidatorClass(schema)
        validator.validate(document)

        return True


# ========================================
# Convenience Functions
# ========================================

_validator = None


def get_validator() -> SchemaValidator:
    """Get global schema validator instance."""
    global _validator
    if _validator is None:
        _validator = SchemaValidator()
    return _validator


def validate_research_plan(plan: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate research plan document.

    Args:
        plan: Research plan document

    Returns:
        Tuple of (is_valid, list of error messages)

    Example:
        >>> plan = {
        ...     "plan_id": "test_plan_001",
        ...     "research_question": "What are the environmental regulations?",
        ...     "schema_name": "environmental",
        ...     "steps": [...]
        ... }
        >>> is_valid, errors = validate_research_plan(plan)
        >>> if not is_valid:
        ...     print("Validation errors:", errors)
    """
    validator = get_validator()
    return validator.validate(plan, "research_plan.schema")


def validate_step(step: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate individual research plan step.

    Args:
        step: Step document

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    # Create minimal plan to validate step
    test_plan = {"plan_id": "validation_test", "research_question": "Test", "schema_name": "standard", "steps": [step]}

    validator = get_validator()
    is_valid, errors = validator.validate(test_plan, "research_plan")

    # Filter errors to only step-related ones
    step_errors = [e for e in errors if "steps[0]" in e or "steps.0" in e]

    return len(step_errors) == 0, step_errors


def load_plan_from_file(file_path: Path) -> Tuple[bool, Optional[Dict], List[str]]:
    """
    Load and validate research plan from file.

    Args:
        file_path: Path to JSON file

    Returns:
        Tuple of (is_valid, plan_document, error_messages)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            plan = json.load(f)

        is_valid, errors = validate_research_plan(plan)
        return is_valid, plan, errors

    except json.JSONDecodeError as e:
        return False, None, [f"JSON decode error: {e}"]
    except FileNotFoundError:
        return False, None, [f"File not found: {file_path}"]
    except Exception as e:
        return False, None, [f"Error loading file: {e}"]


def create_minimal_plan(
    plan_id: str, research_question: str, schema_name: str = "standard", steps: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Create a minimal valid research plan.

    Args:
        plan_id: Unique plan identifier
        research_question: Research question
        schema_name: Schema to use
        steps: List of steps (empty if not provided)

    Returns:
        Valid research plan document
    """
    if steps is None:
        steps = []

    plan = {
        "plan_id": plan_id,
        "research_question": research_question,
        "schema_name": schema_name,
        "steps": steps,
        "status": "pending",
        "priority": 5,
        "query_complexity": "standard",
        "source_domains": ["general"],
        "security_level": "internal",
        "phase5_hybrid_search": True,
    }

    return plan


def create_step(
    step_id: str, step_name: str, agent_name: str, step_type: str = "data_retrieval", depends_on: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a minimal valid research plan step.

    Args:
        step_id: Unique step identifier
        step_name: Human-readable step name
        agent_name: Name of agent to execute step
        step_type: Type of step
        depends_on: List of step_ids this depends on

    Returns:
        Valid step document
    """
    if depends_on is None:
        depends_on = []

    step = {
        "step_id": step_id,
        "step_name": step_name,
        "step_type": step_type,
        "agent_name": agent_name,
        "agent_type": "DataRetrievalAgent",
        "depends_on": depends_on,
        "status": "pending",
        "retry_count": 0,
        "max_retries": 3,
        "timeout_seconds": 60,
    }

    return step


# ========================================
# Example Usage
# ========================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("VERITAS AGENT FRAMEWORK - SCHEMA VALIDATION TEST")
    print("=" * 80)

    # Create test plan
    plan = create_minimal_plan(
        plan_id="test_plan_001",
        research_question="What are the environmental regulations for construction?",
        schema_name="environmental",
        steps=[
            create_step(step_id="step_001", step_name="Retrieve environmental regulations", agent_name="environmental"),
            create_step(
                step_id="step_002",
                step_name="Analyze construction requirements",
                agent_name="construction",
                depends_on=["step_001"],
            ),
        ],
    )

    # Validate
    is_valid, errors = validate_research_plan(plan)

    if is_valid:
        print("\n✅ Plan is VALID")
        print(f"Plan ID: {plan['plan_id']}")
        print(f"Question: {plan['research_question']}")
        print(f"Steps: {len(plan['steps'])}")
    else:
        print("\n❌ Plan is INVALID")
        print("Errors:")
        for error in errors:
            print(f"  - {error}")

    # Test invalid plan
    print("\n" + "=" * 80)
    print("Testing INVALID plan...")
    print("=" * 80)

    invalid_plan = {
        "plan_id": "test",
        # Missing required fields
        "steps": [],
    }

    is_valid, errors = validate_research_plan(invalid_plan)

    if not is_valid:
        print("\n✅ Correctly identified as INVALID")
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n❌ Should have been INVALID!")

    print("\n✨ Validation test complete!")
