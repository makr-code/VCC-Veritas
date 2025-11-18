"""
VERITAS Agent Framework - Advanced Orchestration Controller
===========================================================

Advanced plan orchestration with pause/resume, manual intervention,
and dynamic plan modification capabilities.

Features:
- Plan pause/resume with state persistence
- Manual retry intervention
- Dynamic plan modification (add/remove/reorder steps)
- Checkpoint system for recovery
- Step skipping and rollback
- Plan state snapshots

Usage:
    from orchestration_controller import OrchestrationController

    # Create controller
    controller = OrchestrationController()

    # Start plan execution
    await controller.execute_plan_async(plan_id, plan)

    # Pause execution
    await controller.pause_plan(plan_id)

    # Resume execution
    await controller.resume_plan(plan_id)

    # Modify plan
    await controller.add_step(plan_id, new_step, insert_after="step_2")

Created: 2025-10-08
"""

import asyncio
import json
import logging
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

try:
    from .state_machine import PlanState
except ImportError:
    from state_machine import PlanState


logger = logging.getLogger(__name__)


class OrchestrationState(Enum):
    """Plan orchestration state."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InterventionType(Enum):
    """Manual intervention types."""

    RETRY_STEP = "retry_step"
    SKIP_STEP = "skip_step"
    MODIFY_STEP = "modify_step"
    ADD_STEP = "add_step"
    REMOVE_STEP = "remove_step"
    REORDER_STEPS = "reorder_steps"


@dataclass
class Checkpoint:
    """
    Plan execution checkpoint.

    Attributes:
        checkpoint_id: Unique checkpoint identifier
        plan_id: Plan identifier
        step_index: Current step index
        completed_steps: List of completed step IDs
        plan_state: Current plan state
        context: Execution context snapshot
        timestamp: Checkpoint timestamp
    """

    checkpoint_id: str
    plan_id: str
    step_index: int
    completed_steps: List[str]
    plan_state: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Intervention:
    """
    Manual intervention record.

    Attributes:
        intervention_id: Unique intervention identifier
        plan_id: Plan identifier
        intervention_type: Type of intervention
        target_step_id: Target step identifier (optional)
        parameters: Intervention parameters
        user: User who triggered intervention
        timestamp: Intervention timestamp
        status: Intervention status (pending/applied/failed)
    """

    intervention_id: str
    plan_id: str
    intervention_type: str
    target_step_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    user: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PlanSnapshot:
    """
    Complete plan state snapshot.

    Attributes:
        snapshot_id: Unique snapshot identifier
        plan_id: Plan identifier
        plan: Complete plan definition
        orchestration_state: Current orchestration state
        current_step_index: Current step index
        completed_steps: List of completed steps
        failed_steps: List of failed steps
        skipped_steps: List of skipped steps
        checkpoints: List of checkpoints
        interventions: List of interventions
        timestamp: Snapshot timestamp
    """

    snapshot_id: str
    plan_id: str
    plan: Dict[str, Any]
    orchestration_state: str
    current_step_index: int
    completed_steps: List[str]
    failed_steps: List[str]
    skipped_steps: List[str]
    checkpoints: List[Dict[str, Any]]
    interventions: List[Dict[str, Any]]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class OrchestrationController:
    """
    Advanced orchestration controller for research plan execution.

    Provides pause/resume, manual intervention, and dynamic
    plan modification capabilities.
    """

    def __init__(self, checkpoint_dir: Optional[Path] = None):
        """
        Initialize orchestration controller.

        Args:
            checkpoint_dir: Directory for checkpoint persistence
        """
        self.checkpoint_dir = checkpoint_dir or Path("data/checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Execution state
        self.plans: Dict[str, Dict[str, Any]] = {}  # plan_id -> plan data
        self.states: Dict[str, OrchestrationState] = {}  # plan_id -> state
        self.current_steps: Dict[str, int] = {}  # plan_id -> step_index
        self.completed_steps: Dict[str, List[str]] = {}  # plan_id -> [step_ids]
        self.failed_steps: Dict[str, List[str]] = {}  # plan_id -> [step_ids]
        self.skipped_steps: Dict[str, List[str]] = {}  # plan_id -> [step_ids]

        # Checkpoints and interventions
        self.checkpoints: Dict[str, List[Checkpoint]] = {}  # plan_id -> checkpoints
        self.interventions: Dict[str, List[Intervention]] = {}  # plan_id -> interventions

        # Pause/resume control
        self.pause_events: Dict[str, asyncio.Event] = {}  # plan_id -> Event
        self.cancel_flags: Dict[str, bool] = {}  # plan_id -> cancelled

        # Callbacks
        self.on_state_change: Optional[Callable] = None
        self.on_checkpoint: Optional[Callable] = None
        self.on_intervention: Optional[Callable] = None

        logger.info(f"Initialized OrchestrationController with checkpoint_dir={checkpoint_dir}")

    def register_plan(self, plan_id: str, plan: Dict[str, Any]) -> None:
        """
        Register a plan for orchestration.

        Args:
            plan_id: Plan identifier
            plan: Plan definition
        """
        self.plans[plan_id] = deepcopy(plan)
        self.states[plan_id] = OrchestrationState.IDLE
        self.current_steps[plan_id] = 0
        self.completed_steps[plan_id] = []
        self.failed_steps[plan_id] = []
        self.skipped_steps[plan_id] = []
        self.checkpoints[plan_id] = []
        self.interventions[plan_id] = []
        self.pause_events[plan_id] = asyncio.Event()
        self.pause_events[plan_id].set()  # Start unpaused
        self.cancel_flags[plan_id] = False

        logger.info(f"Registered plan {plan_id} with {len(plan.get('steps', []))} steps")

    async def execute_plan_async(self, plan_id: str, executor: Callable) -> Dict[str, Any]:
        """
        Execute plan with orchestration control.

        Args:
            plan_id: Plan identifier
            executor: Async function that executes a step

        Returns:
            Execution result
        """
        if plan_id not in self.plans:
            raise ValueError(f"Plan {plan_id} not registered")

        plan = self.plans[plan_id]
        steps = plan.get("steps", [])

        # Set state to running
        await self._set_state(plan_id, OrchestrationState.RUNNING)

        # Create initial checkpoint
        await self._create_checkpoint(plan_id)

        try:
            for i, step in enumerate(steps):
                step_id = step["step_id"]

                # Check for cancellation
                if self.cancel_flags.get(plan_id, False):
                    logger.info(f"Plan {plan_id} cancelled at step {step_id}")
                    await self._set_state(plan_id, OrchestrationState.CANCELLED)
                    break

                # Wait if paused
                await self.pause_events[plan_id].wait()

                # Update current step
                self.current_steps[plan_id] = i

                # Check if step should be skipped
                if step_id in self.skipped_steps.get(plan_id, []):
                    logger.info(f"Skipping step {step_id} (manual skip)")
                    continue

                # Execute step
                logger.info(f"Executing step {i+1}/{len(steps)}: {step_id}")

                try:
                    result = await executor(step)

                    if result.get("status") == "success":
                        self.completed_steps[plan_id].append(step_id)
                        logger.info(f"Step {step_id} completed successfully")
                    else:
                        self.failed_steps[plan_id].append(step_id)
                        logger.warning(f"Step {step_id} failed")

                    # Create checkpoint after each step
                    await self._create_checkpoint(plan_id)

                except Exception as e:
                    logger.error(f"Error executing step {step_id}: {e}")
                    self.failed_steps[plan_id].append(step_id)
                    raise

            # Plan completed
            await self._set_state(plan_id, OrchestrationState.COMPLETED)

            return {
                "status": "completed",
                "plan_id": plan_id,
                "completed_steps": len(self.completed_steps[plan_id]),
                "failed_steps": len(self.failed_steps[plan_id]),
                "skipped_steps": len(self.skipped_steps[plan_id]),
            }

        except Exception as e:
            await self._set_state(plan_id, OrchestrationState.FAILED)
            raise

    async def pause_plan(self, plan_id: str) -> bool:
        """
        Pause plan execution.

        Args:
            plan_id: Plan identifier

        Returns:
            True if paused successfully
        """
        if plan_id not in self.plans:
            raise ValueError(f"Unknown plan: {plan_id}")

        if self.states[plan_id] != OrchestrationState.RUNNING:
            logger.warning(f"Cannot pause plan {plan_id} in state {self.states[plan_id]}")
            return False

        # Clear pause event (blocks execution)
        self.pause_events[plan_id].clear()

        # Update state
        await self._set_state(plan_id, OrchestrationState.PAUSED)

        # Create checkpoint
        await self._create_checkpoint(plan_id)

        logger.info(f"Paused plan {plan_id}")
        return True

    async def resume_plan(self, plan_id: str) -> bool:
        """
        Resume paused plan execution.

        Args:
            plan_id: Plan identifier

        Returns:
            True if resumed successfully
        """
        if plan_id not in self.plans:
            raise ValueError(f"Unknown plan: {plan_id}")

        if self.states[plan_id] != OrchestrationState.PAUSED:
            logger.warning(f"Cannot resume plan {plan_id} in state {self.states[plan_id]}")
            return False

        # Set pause event (allows execution)
        self.pause_events[plan_id].set()

        # Update state
        await self._set_state(plan_id, OrchestrationState.RUNNING)

        logger.info(f"Resumed plan {plan_id}")
        return True

    async def cancel_plan(self, plan_id: str) -> bool:
        """
        Cancel plan execution.

        Args:
            plan_id: Plan identifier

        Returns:
            True if cancelled successfully
        """
        if plan_id not in self.plans:
            raise ValueError(f"Unknown plan: {plan_id}")

        self.cancel_flags[plan_id] = True

        # If paused, resume to allow cancellation
        if self.states[plan_id] == OrchestrationState.PAUSED:
            self.pause_events[plan_id].set()

        logger.info(f"Cancelled plan {plan_id}")
        return True

    async def retry_step(self, plan_id: str, step_id: str, user: Optional[str] = None) -> str:
        """
        Manually retry a failed step.

        Args:
            plan_id: Plan identifier
            step_id: Step identifier to retry
            user: User triggering retry

        Returns:
            Intervention ID
        """
        intervention = Intervention(
            intervention_id=str(uuid4()),
            plan_id=plan_id,
            intervention_type=InterventionType.RETRY_STEP.value,
            target_step_id=step_id,
            user=user,
        )

        self.interventions[plan_id].append(intervention)

        # Remove from failed steps
        if step_id in self.failed_steps.get(plan_id, []):
            self.failed_steps[plan_id].remove(step_id)

        intervention.status = "applied"

        logger.info(f"Retry intervention for step {step_id} by {user}")

        if self.on_intervention:
            await self.on_intervention(intervention)

        return intervention.intervention_id

    async def skip_step(self, plan_id: str, step_id: str, user: Optional[str] = None) -> str:
        """
        Skip a step.

        Args:
            plan_id: Plan identifier
            step_id: Step identifier to skip
            user: User triggering skip

        Returns:
            Intervention ID
        """
        intervention = Intervention(
            intervention_id=str(uuid4()),
            plan_id=plan_id,
            intervention_type=InterventionType.SKIP_STEP.value,
            target_step_id=step_id,
            user=user,
        )

        self.interventions[plan_id].append(intervention)
        self.skipped_steps[plan_id].append(step_id)

        intervention.status = "applied"

        logger.info(f"Skip intervention for step {step_id} by {user}")

        if self.on_intervention:
            await self.on_intervention(intervention)

        return intervention.intervention_id

    async def add_step(
        self, plan_id: str, step: Dict[str, Any], insert_after: Optional[str] = None, user: Optional[str] = None
    ) -> str:
        """
        Add a new step to the plan.

        Args:
            plan_id: Plan identifier
            step: Step definition
            insert_after: Insert after this step ID (None = append)
            user: User triggering addition

        Returns:
            Intervention ID
        """
        if plan_id not in self.plans:
            raise ValueError(f"Unknown plan: {plan_id}")

        intervention = Intervention(
            intervention_id=str(uuid4()),
            plan_id=plan_id,
            intervention_type=InterventionType.ADD_STEP.value,
            parameters={"step": step, "insert_after": insert_after},
            user=user,
        )

        self.interventions[plan_id].append(intervention)

        # Add step to plan
        steps = self.plans[plan_id].get("steps", [])

        if insert_after:
            # Find insertion point
            for i, s in enumerate(steps):
                if s["step_id"] == insert_after:
                    steps.insert(i + 1, step)
                    break
        else:
            # Append
            steps.append(step)

        self.plans[plan_id]["steps"] = steps

        intervention.status = "applied"

        logger.info(f"Added step {step['step_id']} after {insert_after} by {user}")

        if self.on_intervention:
            await self.on_intervention(intervention)

        return intervention.intervention_id

    async def remove_step(self, plan_id: str, step_id: str, user: Optional[str] = None) -> str:
        """
        Remove a step from the plan.

        Args:
            plan_id: Plan identifier
            step_id: Step identifier to remove
            user: User triggering removal

        Returns:
            Intervention ID
        """
        if plan_id not in self.plans:
            raise ValueError(f"Unknown plan: {plan_id}")

        intervention = Intervention(
            intervention_id=str(uuid4()),
            plan_id=plan_id,
            intervention_type=InterventionType.REMOVE_STEP.value,
            target_step_id=step_id,
            user=user,
        )

        self.interventions[plan_id].append(intervention)

        # Remove step from plan
        steps = self.plans[plan_id].get("steps", [])
        self.plans[plan_id]["steps"] = [s for s in steps if s["step_id"] != step_id]

        intervention.status = "applied"

        logger.info(f"Removed step {step_id} by {user}")

        if self.on_intervention:
            await self.on_intervention(intervention)

        return intervention.intervention_id

    async def _create_checkpoint(self, plan_id: str) -> Checkpoint:
        """
        Create execution checkpoint.

        Args:
            plan_id: Plan identifier

        Returns:
            Created checkpoint
        """
        checkpoint = Checkpoint(
            checkpoint_id=str(uuid4()),
            plan_id=plan_id,
            step_index=self.current_steps.get(plan_id, 0),
            completed_steps=self.completed_steps.get(plan_id, []).copy(),
            plan_state=deepcopy(self.plans.get(plan_id, {})),
            context={
                "orchestration_state": self.states[plan_id].value,
                "failed_steps": self.failed_steps.get(plan_id, []).copy(),
                "skipped_steps": self.skipped_steps.get(plan_id, []).copy(),
            },
        )

        self.checkpoints[plan_id].append(checkpoint)

        # Persist checkpoint
        await self._save_checkpoint(checkpoint)

        logger.debug(f"Created checkpoint {checkpoint.checkpoint_id} for plan {plan_id}")

        if self.on_checkpoint:
            await self.on_checkpoint(checkpoint)

        return checkpoint

    async def _save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Save checkpoint to disk."""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint.checkpoint_id}.json"

        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

        logger.debug(f"Saved checkpoint {checkpoint.checkpoint_id}")

    async def restore_from_checkpoint(self, plan_id: str, checkpoint_id: str) -> bool:
        """
        Restore plan from checkpoint.

        Args:
            plan_id: Plan identifier
            checkpoint_id: Checkpoint identifier

        Returns:
            True if restored successfully
        """
        # Find checkpoint
        checkpoint = None
        for cp in self.checkpoints.get(plan_id, []):
            if cp.checkpoint_id == checkpoint_id:
                checkpoint = cp
                break

        if not checkpoint:
            logger.error(f"Checkpoint {checkpoint_id} not found")
            return False

        # Restore state
        self.plans[plan_id] = deepcopy(checkpoint.plan_state)
        self.current_steps[plan_id] = checkpoint.step_index
        self.completed_steps[plan_id] = checkpoint.completed_steps.copy()
        self.failed_steps[plan_id] = checkpoint.context.get("failed_steps", []).copy()
        self.skipped_steps[plan_id] = checkpoint.context.get("skipped_steps", []).copy()

        logger.info(f"Restored plan {plan_id} from checkpoint {checkpoint_id}")
        return True

    def get_snapshot(self, plan_id: str) -> PlanSnapshot:
        """
        Get complete plan state snapshot.

        Args:
            plan_id: Plan identifier

        Returns:
            Plan snapshot
        """
        if plan_id not in self.plans:
            raise ValueError(f"Unknown plan: {plan_id}")

        return PlanSnapshot(
            snapshot_id=str(uuid4()),
            plan_id=plan_id,
            plan=deepcopy(self.plans[plan_id]),
            orchestration_state=self.states[plan_id].value,
            current_step_index=self.current_steps.get(plan_id, 0),
            completed_steps=self.completed_steps.get(plan_id, []).copy(),
            failed_steps=self.failed_steps.get(plan_id, []).copy(),
            skipped_steps=self.skipped_steps.get(plan_id, []).copy(),
            checkpoints=[cp.to_dict() for cp in self.checkpoints.get(plan_id, [])],
            interventions=[iv.to_dict() for iv in self.interventions.get(plan_id, [])],
        )

    def get_state(self, plan_id: str) -> Dict[str, Any]:
        """Get current plan state."""
        if plan_id not in self.plans:
            raise ValueError(f"Unknown plan: {plan_id}")

        return {
            "plan_id": plan_id,
            "orchestration_state": self.states[plan_id].value,
            "current_step": self.current_steps.get(plan_id, 0),
            "total_steps": len(self.plans[plan_id].get("steps", [])),
            "completed_steps": len(self.completed_steps.get(plan_id, [])),
            "failed_steps": len(self.failed_steps.get(plan_id, [])),
            "skipped_steps": len(self.skipped_steps.get(plan_id, [])),
            "checkpoints": len(self.checkpoints.get(plan_id, [])),
            "interventions": len(self.interventions.get(plan_id, [])),
        }

    async def _set_state(self, plan_id: str, state: OrchestrationState) -> None:
        """Set orchestration state and trigger callback."""
        old_state = self.states.get(plan_id)
        self.states[plan_id] = state

        logger.info(f"Plan {plan_id} state: {old_state} -> {state.value}")

        if self.on_state_change:
            await self.on_state_change(plan_id, old_state, state)


# ========================================
# Example Usage & Tests
# ========================================


async def _test_orchestration_controller():
    """Test orchestration controller."""
    print("=" * 80)
    print("ORCHESTRATION CONTROLLER TEST")
    print("=" * 80)

    controller = OrchestrationController()

    # Test plan
    plan = {
        "plan_id": "test_plan_001",
        "query": "Test orchestration",
        "steps": [
            {"step_id": "step_1", "action": "search"},
            {"step_id": "step_2", "action": "analyze"},
            {"step_id": "step_3", "action": "synthesize"},
        ],
    }

    # Register plan
    print(f"\n[TEST 1] Register Plan")
    controller.register_plan(plan["plan_id"], plan)
    state = controller.get_state(plan["plan_id"])
    print(f"  ✓ Plan registered: {state['orchestration_state']}")
    print(f"  ✓ Total steps: {state['total_steps']}")

    # Test pause/resume
    print(f"\n[TEST 2] Pause/Resume")

    async def mock_executor(step):
        await asyncio.sleep(0.1)
        return {"status": "success", "step_id": step["step_id"]}

    # Start execution in background
    execution_task = asyncio.create_task(controller.execute_plan_async(plan["plan_id"], mock_executor))

    # Wait a bit then pause
    await asyncio.sleep(0.15)
    paused = await controller.pause_plan(plan["plan_id"])
    print(f"  ✓ Plan paused: {paused}")

    state = controller.get_state(plan["plan_id"])
    print(f"  ✓ State: {state['orchestration_state']}")
    print(f"  ✓ Completed: {state['completed_steps']} steps")

    # Resume
    await asyncio.sleep(0.1)
    resumed = await controller.resume_plan(plan["plan_id"])
    print(f"  ✓ Plan resumed: {resumed}")

    # Wait for completion
    result = await execution_task
    print(f"  ✓ Execution completed: {result['status']}")
    print(f"  ✓ Final: {result['completed_steps']} steps completed")

    # Test interventions
    print(f"\n[TEST 3] Manual Interventions")

    # Register new plan
    plan2 = deepcopy(plan)
    plan2["plan_id"] = "test_plan_002"
    controller.register_plan(plan2["plan_id"], plan2)

    # Skip step
    intervention_id = await controller.skip_step(plan2["plan_id"], "step_2", user="test_user")
    print(f"  ✓ Skip intervention: {intervention_id[:8]}...")

    # Add step
    new_step = {"step_id": "step_4", "action": "validate"}
    intervention_id = await controller.add_step(plan2["plan_id"], new_step, insert_after="step_2")
    print(f"  ✓ Add step intervention: {intervention_id[:8]}...")

    state = controller.get_state(plan2["plan_id"])
    print(f"  ✓ Total steps now: {state['total_steps']}")
    print(f"  ✓ Interventions: {state['interventions']}")

    # Test snapshot
    print(f"\n[TEST 4] Snapshot")
    snapshot = controller.get_snapshot(plan["plan_id"])
    print(f"  ✓ Snapshot ID: {snapshot.snapshot_id[:8]}...")
    print(f"  ✓ Checkpoints: {len(snapshot.checkpoints)}")
    print(f"  ✓ Completed steps: {len(snapshot.completed_steps)}")

    print("\n" + "=" * 80)
    print("✅ ORCHESTRATION CONTROLLER TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    asyncio.run(_test_orchestration_controller())
