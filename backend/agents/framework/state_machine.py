"""
VERITAS Agent Framework - State Machine
=======================================

State machine for research plan execution lifecycle management.

Lifecycle States:
- pending: Plan created, waiting to start
- running: Currently executing steps
- paused: Execution temporarily suspended
- completed: All steps finished successfully
- failed: Execution failed (critical error)
- cancelled: Manually cancelled by user

Transition Rules:
- pending → running (start execution)
- running → paused (pause execution)
- running → completed (all steps succeeded)
- running → failed (critical error)
- running → cancelled (user cancellation)
- paused → running (resume execution)
- paused → cancelled (cancel while paused)

Author: VERITAS Development Team
Created: 2025-10-08
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set

logger = logging.getLogger(__name__)


class PlanState(Enum):
    """Research plan execution states."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepState(Enum):
    """Individual step execution states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StateTransition:
    """
    Represents a state transition with metadata.

    Attributes:
        from_state: Source state
        to_state: Target state
        timestamp: When transition occurred
        reason: Why transition occurred
        metadata: Additional context
    """

    from_state: PlanState
    to_state: PlanState
    timestamp: str
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateMachine:
    """
    State machine for research plan execution lifecycle.

    Enforces valid state transitions and tracks history.

    Attributes:
        plan_id: Research plan identifier
        current_state: Current execution state
        transition_history: List of all state transitions

    Example:
        >>> sm = StateMachine("plan_001")
        >>> sm.can_transition_to(PlanState.RUNNING)  # True
        >>> sm.transition_to(PlanState.RUNNING, "User started execution")
        >>> sm.current_state  # PlanState.RUNNING
        >>> sm.transition_to(PlanState.PENDING, "Invalid")  # Raises StateTransitionError
    """

    # Valid transitions: {from_state: {allowed_to_states}}
    VALID_TRANSITIONS: Dict[PlanState, Set[PlanState]] = {
        PlanState.PENDING: {PlanState.RUNNING, PlanState.CANCELLED},
        PlanState.RUNNING: {PlanState.PAUSED, PlanState.COMPLETED, PlanState.FAILED, PlanState.CANCELLED},
        PlanState.PAUSED: {PlanState.RUNNING, PlanState.CANCELLED},
        PlanState.COMPLETED: set(),  # Terminal state
        PlanState.FAILED: set(),  # Terminal state
        PlanState.CANCELLED: set(),  # Terminal state
    }

    def __init__(
        self,
        plan_id: str,
        initial_state: PlanState = PlanState.PENDING,
        on_state_change: Optional[Callable[[StateTransition], None]] = None,
    ):
        """
        Initialize state machine.

        Args:
            plan_id: Research plan identifier
            initial_state: Starting state (default: PENDING)
            on_state_change: Optional callback for state changes
        """
        self.plan_id = plan_id
        self.current_state = initial_state
        self.transition_history: list[StateTransition] = []
        self._on_state_change = on_state_change

        logger.info(f"Initialized state machine for plan {plan_id}: {initial_state.value}")

    def can_transition_to(self, target_state: PlanState) -> bool:
        """
        Check if transition to target state is allowed.

        Args:
            target_state: Desired target state

        Returns:
            True if transition is allowed, False otherwise

        Example:
            >>> sm = StateMachine("plan_001")
            >>> sm.can_transition_to(PlanState.RUNNING)  # True
            >>> sm.can_transition_to(PlanState.COMPLETED)  # False
        """
        allowed_states = self.VALID_TRANSITIONS.get(self.current_state, set())
        return target_state in allowed_states

    def transition_to(
        self, target_state: PlanState, reason: str = "", metadata: Optional[Dict[str, Any]] = None
    ) -> StateTransition:
        """
        Transition to target state.

        Args:
            target_state: Desired target state
            reason: Reason for transition
            metadata: Additional context

        Returns:
            StateTransition object

        Raises:
            StateTransitionError: If transition is not allowed

        Example:
            >>> sm = StateMachine("plan_001")
            >>> transition = sm.transition_to(
            ...     PlanState.RUNNING,
            ...     "User started execution",
            ...     {"user_id": "user_123"}
            ... )
            >>> print(transition.from_state)  # PlanState.PENDING
            >>> print(transition.to_state)     # PlanState.RUNNING
        """
        if not self.can_transition_to(target_state):
            raise StateTransitionError(
                f"Invalid transition: {self.current_state.value} → {target_state.value}. "
                f"Allowed: {[s.value for s in self.VALID_TRANSITIONS.get(self.current_state, set())]}"
            )

        # Create transition record
        transition = StateTransition(
            from_state=self.current_state,
            to_state=target_state,
            timestamp=datetime.utcnow().isoformat(),
            reason=reason,
            metadata=metadata or {},
        )

        # Update state
        old_state = self.current_state
        self.current_state = target_state
        self.transition_history.append(transition)

        logger.info(f"Plan {self.plan_id}: {old_state.value} → {target_state.value} " f"({reason})")

        # Trigger callback
        if self._on_state_change:
            try:
                self._on_state_change(transition)
            except Exception as e:
                logger.error(f"State change callback failed: {e}", exc_info=True)

        return transition

    def is_terminal(self) -> bool:
        """
        Check if current state is terminal (no further transitions).

        Returns:
            True if in terminal state (completed/failed/cancelled)

        Example:
            >>> sm = StateMachine("plan_001")
            >>> sm.is_terminal()  # False
            >>> sm.transition_to(PlanState.RUNNING)
            >>> sm.transition_to(PlanState.COMPLETED)
            >>> sm.is_terminal()  # True
        """
        return self.current_state in {PlanState.COMPLETED, PlanState.FAILED, PlanState.CANCELLED}

    def is_active(self) -> bool:
        """
        Check if plan is actively running.

        Returns:
            True if state is RUNNING

        Example:
            >>> sm = StateMachine("plan_001")
            >>> sm.is_active()  # False
            >>> sm.transition_to(PlanState.RUNNING)
            >>> sm.is_active()  # True
        """
        return self.current_state == PlanState.RUNNING

    def is_paused(self) -> bool:
        """
        Check if plan is paused.

        Returns:
            True if state is PAUSED
        """
        return self.current_state == PlanState.PAUSED

    def get_allowed_transitions(self) -> Set[PlanState]:
        """
        Get all allowed target states from current state.

        Returns:
            Set of allowed target states

        Example:
            >>> sm = StateMachine("plan_001")
            >>> allowed = sm.get_allowed_transitions()
            >>> PlanState.RUNNING in allowed  # True
            >>> PlanState.COMPLETED in allowed  # False
        """
        return self.VALID_TRANSITIONS.get(self.current_state, set()).copy()

    def get_transition_history(self) -> list[StateTransition]:
        """
        Get complete transition history.

        Returns:
            List of all transitions (oldest first)
        """
        return self.transition_history.copy()

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize state machine to dictionary.

        Returns:
            Dictionary representation

        Example:
            >>> sm = StateMachine("plan_001")
            >>> data = sm.to_dict()
            >>> data["current_state"]  # "pending"
            >>> len(data["transition_history"])  # 0
        """
        return {
            "plan_id": self.plan_id,
            "current_state": self.current_state.value,
            "is_terminal": self.is_terminal(),
            "is_active": self.is_active(),
            "allowed_transitions": [s.value for s in self.get_allowed_transitions()],
            "transition_count": len(self.transition_history),
            "transition_history": [
                {
                    "from_state": t.from_state.value,
                    "to_state": t.to_state.value,
                    "timestamp": t.timestamp,
                    "reason": t.reason,
                    "metadata": t.metadata,
                }
                for t in self.transition_history
            ],
        }


class StateTransitionError(Exception):
    """Exception raised for invalid state transitions."""

    pass


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("VERITAS STATE MACHINE - TEST")
    print("=" * 80)

    # Test 1: Valid transitions
    print("\n📋 Test 1: Valid Transition Sequence")
    sm = StateMachine("test_plan_001")

    print(f"  Initial state: {sm.current_state.value}")
    print(f"  Allowed transitions: {[s.value for s in sm.get_allowed_transitions()]}")

    # Start execution
    print("\n  Transition: PENDING → RUNNING")
    sm.transition_to(PlanState.RUNNING, "User started execution")
    print(f"  ✅ Current state: {sm.current_state.value}")
    print(f"  Is active: {sm.is_active()}")

    # Pause
    print("\n  Transition: RUNNING → PAUSED")
    sm.transition_to(PlanState.PAUSED, "User paused execution")
    print(f"  ✅ Current state: {sm.current_state.value}")
    print(f"  Is paused: {sm.is_paused()}")

    # Resume
    print("\n  Transition: PAUSED → RUNNING")
    sm.transition_to(PlanState.RUNNING, "User resumed execution")
    print(f"  ✅ Current state: {sm.current_state.value}")

    # Complete
    print("\n  Transition: RUNNING → COMPLETED")
    sm.transition_to(PlanState.COMPLETED, "All steps succeeded")
    print(f"  ✅ Current state: {sm.current_state.value}")
    print(f"  Is terminal: {sm.is_terminal()}")

    # Test 2: Invalid transition
    print("\n📋 Test 2: Invalid Transition (should fail)")
    try:
        sm.transition_to(PlanState.RUNNING, "Cannot resume from completed")
        print("  ❌ Should have raised StateTransitionError!")
    except StateTransitionError as e:
        print(f"  ✅ Correctly rejected: {e}")

    # Test 3: Transition history
    print("\n📋 Test 3: Transition History")
    print(f"  Total transitions: {len(sm.transition_history)}")
    for i, transition in enumerate(sm.transition_history, 1):
        print(f"  {i}. {transition.from_state.value} → {transition.to_state.value} ({transition.reason})")

    # Test 4: State machine with callback
    print("\n📋 Test 4: State Change Callback")

    def on_state_change(transition: StateTransition):
        print(f"  📢 Callback triggered: {transition.from_state.value} → {transition.to_state.value}")

    sm2 = StateMachine("test_plan_002", on_state_change=on_state_change)
    sm2.transition_to(PlanState.RUNNING, "Test callback")
    sm2.transition_to(PlanState.FAILED, "Test error handling")

    # Test 5: Serialization
    print("\n📋 Test 5: Serialization")
    data = sm.to_dict()
    print(f"  Plan ID: {data['plan_id']}")
    print(f"  Current state: {data['current_state']}")
    print(f"  Is terminal: {data['is_terminal']}")
    print(f"  Transition count: {data['transition_count']}")
    print(f"  Allowed transitions: {data['allowed_transitions']}")

    # Test 6: Failed plan scenario
    print("\n📋 Test 6: Failed Plan Scenario")
    sm3 = StateMachine("test_plan_003")
    sm3.transition_to(PlanState.RUNNING, "Start execution")
    sm3.transition_to(PlanState.FAILED, "Critical error in step 5")
    print(f"  ✅ Final state: {sm3.current_state.value}")
    print(f"  Is terminal: {sm3.is_terminal()}")
    print(f"  Can recover: {sm3.can_transition_to(PlanState.RUNNING)}")

    print("\n✨ State machine tests complete!")
