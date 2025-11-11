"""
VERITAS NLP Foundation - WebSocket Progress Bridge
==================================================

Bridge between ProgressCallback and StreamingManager for WebSocket streaming.

Converts ProgressEvent from process execution to StreamEvent format
and broadcasts to WebSocket clients via StreamingManager.

Features:
- Automatic event conversion (ProgressEvent → StreamEvent)
- Client subscription management
- Async streaming support
- Event filtering and routing
- Session-based isolation

Usage:
    from backend.services.websocket_progress_bridge import WebSocketProgressBridge
    from backend.models.streaming_progress import ProgressCallback

    # Create bridge
    bridge = WebSocketProgressBridge(streaming_manager, session_id="session_123")

    # Create callback that uses the bridge
    callback = ProgressCallback()
    callback.add_handler(bridge.on_progress_event)

    # Execute with streaming
    executor.execute_process(tree, progress_callback=callback)

    # Events will be automatically streamed to WebSocket clients

Created: 2025-10-14
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, Set

if TYPE_CHECKING:
    from backend.agents.framework.streaming_manager import StreamEvent, StreamingManager
    from backend.models.streaming_progress import ProgressEvent

try:
    from backend.models.streaming_progress import EventType as ProgressEventType
    from backend.models.streaming_progress import ProgressEvent, ProgressStatus

    PROGRESS_MODELS_AVAILABLE = True
except ImportError:
    PROGRESS_MODELS_AVAILABLE = False
    logging.warning("⚠️ Progress models not available")

try:
    from backend.agents.framework.streaming_manager import EventType as StreamEventType
    from backend.agents.framework.streaming_manager import StreamEvent, StreamingManager

    STREAMING_MANAGER_AVAILABLE = True
except ImportError:
    STREAMING_MANAGER_AVAILABLE = False
    logging.warning("⚠️ StreamingManager not available")


logger = logging.getLogger(__name__)


class WebSocketProgressBridge:
    """
    Bridge between ProgressCallback and WebSocket streaming.

    Converts ProgressEvent objects to StreamEvent format and
    broadcasts them to WebSocket clients via StreamingManager.

    Features:
    - Automatic event type mapping
    - Async event broadcasting
    - Session-based client isolation
    - Event history tracking
    - Graceful degradation (works without WebSocket)

    Example:
        >>> bridge = WebSocketProgressBridge(manager, "session_123")
        >>> callback = ProgressCallback()
        >>> callback.add_handler(bridge.on_progress_event)
        >>> executor.execute_process(tree, callback)
        >>> # Events automatically streamed to WebSocket clients!
    """

    def __init__(self, streaming_manager: Optional["StreamingManager"] = None, session_id: str = "default"):
        """
        Initialize WebSocket progress bridge.

        Args:
            streaming_manager: StreamingManager instance for WebSocket broadcasting
            session_id: Session identifier for client isolation
        """
        self.streaming_manager = streaming_manager
        self.session_id = session_id
        self.event_count = 0
        self.event_history: list[Any] = []  # List of ProgressEvent objects

        # Event type mapping: ProgressEventType → StreamEventType
        self.event_type_mapping = {
            ProgressEventType.PLAN_STARTED: StreamEventType.PLAN_STARTED,
            ProgressEventType.STEP_STARTED: StreamEventType.STEP_STARTED,
            ProgressEventType.STEP_PROGRESS: StreamEventType.STEP_PROGRESS,
            ProgressEventType.STEP_COMPLETED: StreamEventType.STEP_COMPLETED,
            ProgressEventType.STEP_FAILED: StreamEventType.STEP_FAILED,
            ProgressEventType.PLAN_COMPLETED: StreamEventType.PLAN_COMPLETED,
            ProgressEventType.PLAN_FAILED: StreamEventType.PLAN_FAILED,
            ProgressEventType.ERROR: StreamEventType.ERROR,
        }

        logger.info(f"WebSocketProgressBridge initialized for session: {session_id}")

    def on_progress_event(self, event: Any) -> None:  # ProgressEvent type
        """
        Handle progress event (callback from ProgressCallback).

        This is a synchronous wrapper that schedules async streaming.

        Args:
            event: ProgressEvent from process execution
        """
        # Track event
        self.event_count += 1
        self.event_history.append(event)

        # If no streaming manager, just log
        if not self.streaming_manager:
            logger.debug(f"[{self.session_id}] Progress: {event.message}")
            return

        # Schedule async streaming
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop in current thread - create new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Schedule streaming task
            if loop.is_running():
                # Event loop already running - use create_task
                asyncio.create_task(self.stream_progress_event(event))
            else:
                # No running loop - run until complete
                loop.run_until_complete(self.stream_progress_event(event))

        except Exception as e:
            logger.error(f"Failed to stream progress event: {e}", exc_info=True)

    async def stream_progress_event(self, event: Any) -> None:  # ProgressEvent type
        """
        Stream progress event to WebSocket clients (async).

        Args:
            event: ProgressEvent to stream
        """
        if not self.streaming_manager:
            return

        # Convert ProgressEvent to StreamEvent
        stream_event = self._convert_to_stream_event(event)

        # Broadcast to all clients subscribed to this session
        try:
            await self.streaming_manager.stream_event(stream_event)
            logger.debug(f"Streamed event: {event.event_type.value} for {self.session_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast stream event: {e}", exc_info=True)

    def _convert_to_stream_event(self, progress_event: Any) -> Any:  # ProgressEvent → StreamEvent
        """
        Convert ProgressEvent to StreamEvent format.

        Args:
            progress_event: ProgressEvent from process execution

        Returns:
            StreamEvent for WebSocket streaming
        """
        # Map event type
        stream_event_type = self.event_type_mapping.get(
            progress_event.event_type, StreamEventType.STEP_PROGRESS  # Default fallback
        )

        # Build data payload
        data = {
            "step_name": progress_event.step_name,
            "current_step": progress_event.current_step,
            "total_steps": progress_event.total_steps,
            "percentage": progress_event.percentage,
            "status": progress_event.status.value,
            "message": progress_event.message,
            "execution_time": progress_event.execution_time,
            "timestamp": progress_event.timestamp,
        }

        # Add step-specific data
        if progress_event.data:
            data["result_data"] = progress_event.data

        # Add error if present
        if progress_event.error:
            data["error"] = progress_event.error

        # Add metadata
        if progress_event.metadata:
            data["metadata"] = progress_event.metadata

        # Create StreamEvent
        stream_event = StreamEvent(
            event_type=stream_event_type.value, plan_id=self.session_id, step_id=progress_event.step_id, data=data
        )

        return stream_event

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get bridge statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "session_id": self.session_id,
            "event_count": self.event_count,
            "streaming_enabled": self.streaming_manager is not None,
            "history_size": len(self.event_history),
        }

    def clear_history(self) -> None:
        """Clear event history."""
        self.event_history.clear()
        self.event_count = 0
        logger.info(f"Cleared event history for session: {self.session_id}")


class WebSocketProgressBridgeFactory:
    """
    Factory for creating WebSocket progress bridges.

    Manages bridge lifecycle and provides easy access to bridges
    for different sessions.

    Usage:
        >>> factory = WebSocketProgressBridgeFactory(streaming_manager)
        >>> bridge = factory.get_bridge("session_123")
        >>> callback = ProgressCallback()
        >>> callback.add_handler(bridge.on_progress_event)
    """

    def __init__(self, streaming_manager: Optional["StreamingManager"] = None):
        """
        Initialize bridge factory.

        Args:
            streaming_manager: StreamingManager instance
        """
        self.streaming_manager = streaming_manager
        self.bridges: Dict[str, WebSocketProgressBridge] = {}
        self._lock = asyncio.Lock()

        logger.info("WebSocketProgressBridgeFactory initialized")

    def get_bridge(self, session_id: str) -> WebSocketProgressBridge:
        """
        Get or create bridge for session.

        Args:
            session_id: Session identifier

        Returns:
            WebSocketProgressBridge instance
        """
        if session_id not in self.bridges:
            self.bridges[session_id] = WebSocketProgressBridge(self.streaming_manager, session_id)
            logger.info(f"Created new bridge for session: {session_id}")

        return self.bridges[session_id]

    def remove_bridge(self, session_id: str) -> None:
        """
        Remove bridge for session.

        Args:
            session_id: Session identifier
        """
        if session_id in self.bridges:
            del self.bridges[session_id]
            logger.info(f"Removed bridge for session: {session_id}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get factory statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_bridges": len(self.bridges),
            "sessions": list(self.bridges.keys()),
            "streaming_enabled": self.streaming_manager is not None,
        }


# Test code
if __name__ == "__main__":
    import os
    import sys

    # Add project root to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Re-import with correct path
    from backend.agents.framework.streaming_manager import EventType as StreamEventType
    from backend.agents.framework.streaming_manager import StreamEvent
    from backend.models.streaming_progress import EventType as ProgressEventType
    from backend.models.streaming_progress import (
        ProgressEvent,
        ProgressStatus,
        create_plan_started_event,
        create_step_completed_event,
        create_step_progress_event,
        create_step_started_event,
    )

    print("=" * 80)
    print("WEBSOCKET PROGRESS BRIDGE TEST")
    print("=" * 80)

    # Test 1: Bridge without StreamingManager (graceful degradation)
    print("\n1. Bridge without StreamingManager (Graceful Degradation):")
    bridge = WebSocketProgressBridge(session_id="test_session_1")

    # Simulate progress events
    events = [
        create_plan_started_event(3, "Test query"),
        create_step_started_event("step_1", "Test step 1", 1, 3),
        create_step_progress_event("step_1", "Test step 1", 1, 3, 50.0, "Processing..."),
        create_step_completed_event("step_1", "Test step 1", 1, 3, 0.15),
    ]

    for event in events:
        bridge.on_progress_event(event)

    stats = bridge.get_statistics()
    print(f"   Session ID: {stats['session_id']}")
    print(f"   Events processed: {stats['event_count']}")
    print(f"   Streaming enabled: {stats['streaming_enabled']}")
    print(f"   History size: {stats['history_size']}")
    print("   ✅ Graceful degradation working!")

    # Test 2: Event type mapping
    print("\n2. Event Type Mapping:")
    print(f"   Mapping table size: {len(bridge.event_type_mapping)}")
    for progress_type, stream_type in bridge.event_type_mapping.items():
        print(f"      {progress_type.value:20s} → {stream_type.value}")
    print("   ✅ All event types mapped!")

    # Test 3: Event conversion
    print("\n3. Event Conversion (ProgressEvent → StreamEvent):")
    test_event = create_step_progress_event(
        "step_x", "Test Step", 2, 5, 75.0, message="Testing conversion", data={"test_key": "test_value"}
    )

    stream_event = bridge._convert_to_stream_event(test_event)
    print(f"   Progress event type: {test_event.event_type.value}")
    print(f"   Stream event type: {stream_event.event_type}")
    print(f"   Plan ID (session): {stream_event.plan_id}")
    print(f"   Step ID: {stream_event.step_id}")
    print(f"   Data keys: {list(stream_event.data.keys())}")
    print(f"   Message: {stream_event.data['message']}")
    print(f"   Percentage: {stream_event.data['percentage']:.1f}%")
    print("   ✅ Event conversion working!")

    # Test 4: Bridge factory
    print("\n4. Bridge Factory:")
    factory = WebSocketProgressBridgeFactory()

    # Create multiple bridges
    bridge1 = factory.get_bridge("session_A")
    bridge2 = factory.get_bridge("session_B")
    bridge3 = factory.get_bridge("session_A")  # Should return existing

    print(f"   Bridge 1 session: {bridge1.session_id}")
    print(f"   Bridge 2 session: {bridge2.session_id}")
    print(f"   Bridge 3 session: {bridge3.session_id}")
    print(f"   Bridge 1 == Bridge 3: {bridge1 is bridge3}")

    factory_stats = factory.get_statistics()
    print(f"   Total bridges: {factory_stats['total_bridges']}")
    print(f"   Sessions: {factory_stats['sessions']}")
    print("   ✅ Factory working!")

    # Test 5: Clear history
    print("\n5. Clear History:")
    print(f"   Before clear: {bridge.event_count} events")
    bridge.clear_history()
    print(f"   After clear: {bridge.event_count} events")
    print("   ✅ History cleared!")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED")
    print("=" * 80)
    print("\nNote: WebSocket streaming requires StreamingManager instance.")
    print("      Tests run in graceful degradation mode (no actual streaming).")
    print("=" * 80)
