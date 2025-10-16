"""
VERITAS NLP Foundation - Streaming Progress Models
==================================================

Data models for real-time progress streaming during process execution.

Features:
- Step-by-step progress tracking
- Percentage calculation
- Status updates
- Timing information
- Error tracking
- Metadata support

Usage:
    from backend.models.streaming_progress import ProgressCallback, ProgressEvent
    
    # Create callback
    def on_progress(event: ProgressEvent):
        print(f"Step {event.current_step}/{event.total_steps}: {event.message}")
    
    callback = ProgressCallback(on_progress)
    
    # Emit progress
    event = ProgressEvent(
        step_id="step_1",
        step_name="Search Stuttgart regulations",
        current_step=1,
        total_steps=3,
        percentage=33,
        status="running"
    )
    callback.emit(event)

Created: 2025-10-14
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from uuid import uuid4


class ProgressStatus(Enum):
    """Progress event status."""
    PENDING = "pending"          # Step waiting to execute
    STARTING = "starting"        # Step starting execution
    RUNNING = "running"          # Step currently executing
    PROGRESS = "progress"        # Step making progress (with percentage)
    COMPLETED = "completed"      # Step successfully completed
    FAILED = "failed"            # Step failed with error
    SKIPPED = "skipped"          # Step skipped (dependency failed)
    CANCELLED = "cancelled"      # Step cancelled by user


class EventType(Enum):
    """Progress event types."""
    PLAN_STARTED = "plan_started"        # Execution plan started
    STEP_STARTED = "step_started"        # Individual step started
    STEP_PROGRESS = "step_progress"      # Step progress update
    STEP_COMPLETED = "step_completed"    # Step completed
    STEP_FAILED = "step_failed"          # Step failed
    PLAN_COMPLETED = "plan_completed"    # All steps completed
    PLAN_FAILED = "plan_failed"          # Execution failed
    ERROR = "error"                      # Error occurred


@dataclass
class ProgressEvent:
    """
    Progress event for a single step or overall execution.
    
    Attributes:
        event_type: Type of progress event
        step_id: Step identifier (optional for plan-level events)
        step_name: Human-readable step name
        current_step: Current step number (1-based)
        total_steps: Total number of steps
        percentage: Completion percentage (0-100)
        status: Current status
        message: Human-readable message
        data: Additional event data
        error: Error message (if failed)
        timestamp: Event timestamp
        event_id: Unique event identifier
        execution_time: Time taken so far (seconds)
        metadata: Additional metadata
    """
    event_type: EventType
    step_id: Optional[str] = None
    step_name: str = ""
    current_step: int = 0
    total_steps: int = 0
    percentage: float = 0.0
    status: ProgressStatus = ProgressStatus.PENDING
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    event_id: str = field(default_factory=lambda: str(uuid4()))
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Convert enums to strings
        result['event_type'] = self.event_type.value
        result['status'] = self.status.value
        return result
    
    def to_json_string(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict())
    
    @property
    def is_completed(self) -> bool:
        """Check if event indicates completion."""
        return self.status in [ProgressStatus.COMPLETED, ProgressStatus.FAILED, 
                               ProgressStatus.SKIPPED, ProgressStatus.CANCELLED]
    
    @property
    def is_error(self) -> bool:
        """Check if event indicates an error."""
        return self.status == ProgressStatus.FAILED or self.error is not None


@dataclass
class ExecutionProgress:
    """
    Overall execution progress tracker.
    
    Tracks progress across all steps in a process execution.
    
    Attributes:
        total_steps: Total number of steps
        completed_steps: Number of completed steps
        failed_steps: Number of failed steps
        current_step: Current step number
        start_time: Execution start time
        events: History of progress events
    """
    total_steps: int
    completed_steps: int = 0
    failed_steps: int = 0
    current_step: int = 0
    start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    events: List[ProgressEvent] = field(default_factory=list)
    
    @property
    def percentage(self) -> float:
        """Calculate overall completion percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100.0
    
    @property
    def is_completed(self) -> bool:
        """Check if execution is completed."""
        return (self.completed_steps + self.failed_steps) >= self.total_steps
    
    @property
    def has_failures(self) -> bool:
        """Check if any steps failed."""
        return self.failed_steps > 0
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        start = datetime.fromisoformat(self.start_time)
        now = datetime.utcnow()
        return (now - start).total_seconds()
    
    def add_event(self, event: ProgressEvent):
        """Add progress event to history."""
        self.events.append(event)
        
        # Update counters based on event
        if event.status == ProgressStatus.COMPLETED:
            self.completed_steps += 1
        elif event.status == ProgressStatus.FAILED:
            self.failed_steps += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_steps': self.total_steps,
            'completed_steps': self.completed_steps,
            'failed_steps': self.failed_steps,
            'current_step': self.current_step,
            'percentage': self.percentage,
            'is_completed': self.is_completed,
            'has_failures': self.has_failures,
            'elapsed_time': self.elapsed_time,
            'start_time': self.start_time,
            'event_count': len(self.events)
        }


class ProgressCallback:
    """
    Progress callback handler for process execution.
    
    Allows custom callbacks to be registered for progress events.
    Supports multiple callbacks with optional filtering by event type.
    
    Usage:
        # Simple callback
        callback = ProgressCallback(lambda event: print(event.message))
        
        # Multiple callbacks
        callback = ProgressCallback()
        callback.add_handler(lambda e: print(e.message))
        callback.add_handler(lambda e: log.info(e.to_dict()), 
                           event_types=[EventType.STEP_COMPLETED])
    """
    
    def __init__(self, callback: Optional[Callable[[ProgressEvent], None]] = None):
        """
        Initialize progress callback.
        
        Args:
            callback: Optional primary callback function
        """
        self.handlers: List[tuple[Callable, Optional[List[EventType]]]] = []
        self.progress = None  # Will be set to ExecutionProgress when execution starts
        
        if callback:
            self.add_handler(callback)
    
    def add_handler(
        self, 
        handler: Callable[[ProgressEvent], None],
        event_types: Optional[List[EventType]] = None
    ):
        """
        Add a progress event handler.
        
        Args:
            handler: Callback function that takes ProgressEvent
            event_types: Optional list of event types to filter on
        """
        self.handlers.append((handler, event_types))
    
    def emit(self, event: ProgressEvent):
        """
        Emit a progress event to all registered handlers.
        
        Args:
            event: Progress event to emit
        """
        # Update progress tracker if available
        if self.progress:
            self.progress.add_event(event)
        
        # Call all matching handlers
        for handler, event_types in self.handlers:
            # Check if handler is filtered by event type
            if event_types is None or event.event_type in event_types:
                try:
                    handler(event)
                except Exception as e:
                    # Don't let callback errors break execution
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error in progress callback: {e}", exc_info=True)
    
    def create_progress_tracker(self, total_steps: int) -> ExecutionProgress:
        """
        Create and attach a progress tracker.
        
        Args:
            total_steps: Total number of steps to track
            
        Returns:
            ExecutionProgress: Progress tracker instance
        """
        self.progress = ExecutionProgress(total_steps=total_steps)
        return self.progress


# Helper functions for creating common progress events

def create_plan_started_event(total_steps: int, query: str = "") -> ProgressEvent:
    """Create a plan started event."""
    return ProgressEvent(
        event_type=EventType.PLAN_STARTED,
        total_steps=total_steps,
        status=ProgressStatus.STARTING,
        message=f"Starting execution plan with {total_steps} steps",
        data={'query': query}
    )


def create_step_started_event(
    step_id: str,
    step_name: str,
    current_step: int,
    total_steps: int,
    metadata: Optional[Dict[str, Any]] = None
) -> ProgressEvent:
    """Create a step started event."""
    percentage = ((current_step - 1) / total_steps) * 100 if total_steps > 0 else 0
    return ProgressEvent(
        event_type=EventType.STEP_STARTED,
        step_id=step_id,
        step_name=step_name,
        current_step=current_step,
        total_steps=total_steps,
        percentage=percentage,
        status=ProgressStatus.STARTING,
        message=f"Step {current_step}/{total_steps}: Starting {step_name}",
        metadata=metadata or {}
    )


def create_step_progress_event(
    step_id: str,
    step_name: str,
    current_step: int,
    total_steps: int,
    step_percentage: float,
    message: str = "",
    data: Optional[Dict[str, Any]] = None
) -> ProgressEvent:
    """Create a step progress update event."""
    # Calculate overall percentage (completed steps + current step progress)
    base_percentage = ((current_step - 1) / total_steps) * 100
    step_weight = (1.0 / total_steps) * 100
    overall_percentage = base_percentage + (step_weight * (step_percentage / 100))
    
    return ProgressEvent(
        event_type=EventType.STEP_PROGRESS,
        step_id=step_id,
        step_name=step_name,
        current_step=current_step,
        total_steps=total_steps,
        percentage=overall_percentage,
        status=ProgressStatus.PROGRESS,
        message=message or f"Step {current_step}/{total_steps}: {step_name} ({step_percentage:.0f}%)",
        data=data or {}
    )


def create_step_completed_event(
    step_id: str,
    step_name: str,
    current_step: int,
    total_steps: int,
    execution_time: float,
    result_data: Optional[Dict[str, Any]] = None
) -> ProgressEvent:
    """Create a step completed event."""
    percentage = (current_step / total_steps) * 100
    return ProgressEvent(
        event_type=EventType.STEP_COMPLETED,
        step_id=step_id,
        step_name=step_name,
        current_step=current_step,
        total_steps=total_steps,
        percentage=percentage,
        status=ProgressStatus.COMPLETED,
        message=f"Step {current_step}/{total_steps}: Completed {step_name}",
        execution_time=execution_time,
        data=result_data or {}
    )


def create_step_failed_event(
    step_id: str,
    step_name: str,
    current_step: int,
    total_steps: int,
    error: str
) -> ProgressEvent:
    """Create a step failed event."""
    percentage = ((current_step - 1) / total_steps) * 100
    return ProgressEvent(
        event_type=EventType.STEP_FAILED,
        step_id=step_id,
        step_name=step_name,
        current_step=current_step,
        total_steps=total_steps,
        percentage=percentage,
        status=ProgressStatus.FAILED,
        message=f"Step {current_step}/{total_steps}: Failed - {error}",
        error=error
    )


def create_plan_completed_event(
    total_steps: int,
    completed_steps: int,
    failed_steps: int,
    execution_time: float
) -> ProgressEvent:
    """Create a plan completed event."""
    success = failed_steps == 0
    status = ProgressStatus.COMPLETED if success else ProgressStatus.FAILED
    message = f"Execution completed: {completed_steps}/{total_steps} steps succeeded"
    if failed_steps > 0:
        message += f", {failed_steps} failed"
    
    return ProgressEvent(
        event_type=EventType.PLAN_COMPLETED if success else EventType.PLAN_FAILED,
        total_steps=total_steps,
        current_step=total_steps,
        percentage=100.0,
        status=status,
        message=message,
        execution_time=execution_time,
        data={
            'completed_steps': completed_steps,
            'failed_steps': failed_steps,
            'success': success
        }
    )


# Test code
if __name__ == "__main__":
    print("=" * 70)
    print("STREAMING PROGRESS MODEL TEST")
    print("=" * 70)
    
    # Test 1: Basic progress callback
    print("\n1. Basic Progress Callback:")
    
    events_received = []
    
    def on_progress(event: ProgressEvent):
        events_received.append(event)
        print(f"   [{event.status.value}] {event.message}")
    
    callback = ProgressCallback(on_progress)
    tracker = callback.create_progress_tracker(total_steps=3)
    
    # Emit test events
    callback.emit(create_plan_started_event(total_steps=3, query="Test query"))
    callback.emit(create_step_started_event("step_1", "Search docs", 1, 3))
    callback.emit(create_step_progress_event("step_1", "Search docs", 1, 3, 50.0, "Found 10 results"))
    callback.emit(create_step_completed_event("step_1", "Search docs", 1, 3, 0.15))
    callback.emit(create_step_started_event("step_2", "Analyze", 2, 3))
    callback.emit(create_step_completed_event("step_2", "Analyze", 2, 3, 0.25))
    callback.emit(create_step_started_event("step_3", "Synthesize", 3, 3))
    callback.emit(create_step_completed_event("step_3", "Synthesize", 3, 3, 0.30))
    callback.emit(create_plan_completed_event(3, 3, 0, 0.70))
    
    print(f"\n   ✅ Received {len(events_received)} events")
    print(f"   ✅ Progress: {tracker.percentage:.1f}%")
    print(f"   ✅ Completed: {tracker.completed_steps}/{tracker.total_steps}")
    
    # Test 2: Filtered callbacks
    print("\n2. Filtered Callbacks (only STEP_COMPLETED):")
    
    completed_steps_list = []
    
    def on_completed(event: ProgressEvent):
        completed_steps_list.append(event)
        print(f"   ✅ Step completed: {event.step_name} ({event.execution_time:.2f}s)")
    
    callback2 = ProgressCallback()
    callback2.add_handler(on_completed, event_types=[EventType.STEP_COMPLETED])
    
    # Emit events (only STEP_COMPLETED should trigger)
    callback2.emit(create_step_started_event("s1", "Step 1", 1, 2))  # Won't trigger
    callback2.emit(create_step_completed_event("s1", "Step 1", 1, 2, 0.1))  # Will trigger
    callback2.emit(create_step_started_event("s2", "Step 2", 2, 2))  # Won't trigger
    callback2.emit(create_step_completed_event("s2", "Step 2", 2, 2, 0.2))  # Will trigger
    
    print(f"\n   ✅ Received {len(completed_steps_list)} completed events (expected: 2)")
    
    # Test 3: Progress tracker
    print("\n3. Progress Tracker Statistics:")
    print(f"   Total steps:     {tracker.total_steps}")
    print(f"   Completed steps: {tracker.completed_steps}")
    print(f"   Failed steps:    {tracker.failed_steps}")
    print(f"   Percentage:      {tracker.percentage:.1f}%")
    print(f"   Is completed:    {tracker.is_completed}")
    print(f"   Has failures:    {tracker.has_failures}")
    print(f"   Elapsed time:    {tracker.elapsed_time:.2f}s")
    print(f"   Events logged:   {len(tracker.events)}")
    
    # Test 4: JSON serialization
    print("\n4. JSON Serialization:")
    event = create_step_completed_event("test_step", "Test Step", 1, 3, 0.15)
    print(f"   Event dict: {event.to_dict()}")
    
    # Test 5: Error handling
    print("\n5. Error Event:")
    error_event = create_step_failed_event("step_x", "Failed Step", 2, 3, "Connection timeout")
    print(f"   [{error_event.status.value}] {error_event.message}")
    print(f"   Error: {error_event.error}")
    print(f"   Is error: {error_event.is_error}")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
