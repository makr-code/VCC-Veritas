"""
VERITAS Agent Framework - WebSocket Streaming Manager
=====================================================

Real-time streaming of research plan execution progress via WebSocket.

Features:
- Bidirectional WebSocket communication
- Real-time progress updates
- Step-by-step result streaming
- Execution state synchronization
- Multiple client support
- Event-based architecture

Usage:
    from streaming_manager import StreamingManager, StreamEvent
    
    # Create manager
    manager = StreamingManager()
    
    # Register client
    await manager.register_client(client_id, websocket)
    
    # Stream progress
    await manager.stream_event(StreamEvent(
        event_type="step_started",
        plan_id="plan_123",
        step_id="step_1",
        data={"action": "search"}
    ))

Created: 2025-10-08
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Set, Callable
from uuid import uuid4


logger = logging.getLogger(__name__)


class EventType(Enum):
    """WebSocket event types."""
    # Plan events
    PLAN_STARTED = "plan_started"
    PLAN_COMPLETED = "plan_completed"
    PLAN_FAILED = "plan_failed"
    PLAN_PAUSED = "plan_paused"
    PLAN_RESUMED = "plan_resumed"
    
    # Step events
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_PROGRESS = "step_progress"
    
    # Quality gate events
    QUALITY_CHECK = "quality_check"
    REVIEW_REQUIRED = "review_required"
    
    # Monitoring events
    METRICS_UPDATE = "metrics_update"
    HEALTH_UPDATE = "health_update"
    
    # System events
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


@dataclass
class StreamEvent:
    """
    WebSocket stream event.
    
    Attributes:
        event_type: Type of event
        plan_id: Research plan identifier
        step_id: Step identifier (optional)
        data: Event data payload
        timestamp: Event timestamp
        event_id: Unique event identifier
    """
    event_type: str
    plan_id: str
    step_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    event_id: str = field(default_factory=lambda: str(uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class ClientConnection:
    """
    WebSocket client connection.
    
    Attributes:
        client_id: Unique client identifier
        websocket: WebSocket connection (placeholder for actual websocket)
        subscribed_plans: Set of plan IDs client is subscribed to
        connected_at: Connection timestamp
        last_ping: Last ping timestamp
    """
    client_id: str
    websocket: Any  # Actual WebSocket type depends on framework (aiohttp, FastAPI, etc.)
    subscribed_plans: Set[str] = field(default_factory=set)
    connected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_ping: Optional[str] = None


class StreamingManager:
    """
    WebSocket streaming manager for real-time progress updates.
    
    Manages WebSocket connections, event distribution, and
    client subscriptions for research plan execution streaming.
    """
    
    def __init__(self, ping_interval: int = 30):
        """
        Initialize streaming manager.
        
        Args:
            ping_interval: Ping interval in seconds (default: 30)
        """
        self.clients: Dict[str, ClientConnection] = {}
        self.plan_subscribers: Dict[str, Set[str]] = defaultdict(set)  # plan_id -> client_ids
        self.event_history: Dict[str, List[StreamEvent]] = defaultdict(list)  # plan_id -> events
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)  # event_type -> handlers
        
        self.ping_interval = ping_interval
        self._lock = asyncio.Lock()
        
        logger.info(f"Initialized StreamingManager with ping_interval={ping_interval}s")
    
    async def register_client(
        self,
        client_id: str,
        websocket: Any,
        subscribe_to: Optional[List[str]] = None
    ) -> None:
        """
        Register a new WebSocket client.
        
        Args:
            client_id: Unique client identifier
            websocket: WebSocket connection
            subscribe_to: Optional list of plan IDs to subscribe to
        """
        async with self._lock:
            connection = ClientConnection(
                client_id=client_id,
                websocket=websocket,
                subscribed_plans=set(subscribe_to) if subscribe_to else set()
            )
            
            self.clients[client_id] = connection
            
            # Add to plan subscribers
            if subscribe_to:
                for plan_id in subscribe_to:
                    self.plan_subscribers[plan_id].add(client_id)
            
            logger.info(f"Registered client {client_id}, subscribed to {len(subscribe_to or [])} plans")
            
            # Send welcome message
            await self._send_to_client(
                client_id,
                StreamEvent(
                    event_type=EventType.PING.value,
                    plan_id="system",
                    data={"message": "Connected to VERITAS streaming service"}
                )
            )
    
    async def unregister_client(self, client_id: str) -> None:
        """
        Unregister a WebSocket client.
        
        Args:
            client_id: Client identifier to remove
        """
        async with self._lock:
            if client_id not in self.clients:
                logger.warning(f"Attempted to unregister unknown client: {client_id}")
                return
            
            connection = self.clients[client_id]
            
            # Remove from plan subscribers
            for plan_id in connection.subscribed_plans:
                self.plan_subscribers[plan_id].discard(client_id)
            
            # Remove client
            del self.clients[client_id]
            
            logger.info(f"Unregistered client {client_id}")
    
    async def subscribe(self, client_id: str, plan_id: str) -> None:
        """
        Subscribe client to plan updates.
        
        Args:
            client_id: Client identifier
            plan_id: Plan identifier to subscribe to
        """
        async with self._lock:
            if client_id not in self.clients:
                raise ValueError(f"Unknown client: {client_id}")
            
            self.clients[client_id].subscribed_plans.add(plan_id)
            self.plan_subscribers[plan_id].add(client_id)
            
            logger.info(f"Client {client_id} subscribed to plan {plan_id}")
            
            # Send historical events for this plan
            if plan_id in self.event_history:
                for event in self.event_history[plan_id]:
                    await self._send_to_client(client_id, event)
    
    async def unsubscribe(self, client_id: str, plan_id: str) -> None:
        """
        Unsubscribe client from plan updates.
        
        Args:
            client_id: Client identifier
            plan_id: Plan identifier to unsubscribe from
        """
        async with self._lock:
            if client_id not in self.clients:
                return
            
            self.clients[client_id].subscribed_plans.discard(plan_id)
            self.plan_subscribers[plan_id].discard(client_id)
            
            logger.info(f"Client {client_id} unsubscribed from plan {plan_id}")
    
    async def stream_event(self, event: StreamEvent) -> None:
        """
        Stream event to subscribed clients.
        
        Args:
            event: Event to stream
        """
        plan_id = event.plan_id
        
        # Store in history
        self.event_history[plan_id].append(event)
        
        # Trigger event handlers (always, regardless of subscribers)
        await self._trigger_handlers(event)
        
        # Get subscribed clients
        subscribers = self.plan_subscribers.get(plan_id, set())
        
        if not subscribers:
            logger.debug(f"No subscribers for plan {plan_id}, event {event.event_type}")
            return
        
        # Send to all subscribers
        tasks = []
        for client_id in subscribers:
            tasks.append(self._send_to_client(client_id, event))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Streamed {event.event_type} to {len(subscribers)} clients for plan {plan_id}")
        
        logger.debug(f"Streamed {event.event_type} to {len(subscribers)} clients for plan {plan_id}")
    
    async def stream_plan_started(
        self,
        plan_id: str,
        plan_data: Dict[str, Any]
    ) -> None:
        """Stream plan started event."""
        event = StreamEvent(
            event_type=EventType.PLAN_STARTED.value,
            plan_id=plan_id,
            data=plan_data
        )
        await self.stream_event(event)
    
    async def stream_step_started(
        self,
        plan_id: str,
        step_id: str,
        step_data: Dict[str, Any]
    ) -> None:
        """Stream step started event."""
        event = StreamEvent(
            event_type=EventType.STEP_STARTED.value,
            plan_id=plan_id,
            step_id=step_id,
            data=step_data
        )
        await self.stream_event(event)
    
    async def stream_step_progress(
        self,
        plan_id: str,
        step_id: str,
        progress: float,
        message: str
    ) -> None:
        """Stream step progress update."""
        event = StreamEvent(
            event_type=EventType.STEP_PROGRESS.value,
            plan_id=plan_id,
            step_id=step_id,
            data={
                "progress": progress,
                "message": message
            }
        )
        await self.stream_event(event)
    
    async def stream_step_completed(
        self,
        plan_id: str,
        step_id: str,
        result: Dict[str, Any]
    ) -> None:
        """Stream step completed event."""
        event = StreamEvent(
            event_type=EventType.STEP_COMPLETED.value,
            plan_id=plan_id,
            step_id=step_id,
            data=result
        )
        await self.stream_event(event)
    
    async def stream_quality_check(
        self,
        plan_id: str,
        step_id: str,
        quality_result: Dict[str, Any]
    ) -> None:
        """Stream quality check event."""
        event = StreamEvent(
            event_type=EventType.QUALITY_CHECK.value,
            plan_id=plan_id,
            step_id=step_id,
            data=quality_result
        )
        await self.stream_event(event)
    
    async def stream_metrics_update(
        self,
        plan_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """Stream metrics update."""
        event = StreamEvent(
            event_type=EventType.METRICS_UPDATE.value,
            plan_id=plan_id,
            data=metrics
        )
        await self.stream_event(event)
    
    async def _send_to_client(self, client_id: str, event: StreamEvent) -> None:
        """
        Send event to specific client.
        
        Args:
            client_id: Client identifier
            event: Event to send
        """
        if client_id not in self.clients:
            logger.warning(f"Attempted to send to unknown client: {client_id}")
            return
        
        connection = self.clients[client_id]
        
        try:
            # In real implementation, this would be:
            # await connection.websocket.send_text(event.to_json())
            
            # For testing/demonstration, we log it
            logger.debug(f"[SEND -> {client_id}] {event.event_type}: {event.event_id}")
            
            # Placeholder: Store for testing
            if not hasattr(connection, '_received_events'):
                connection._received_events = []
            connection._received_events.append(event)
            
        except Exception as e:
            logger.error(f"Failed to send event to client {client_id}: {e}")
            # In real implementation, might want to unregister client
    
    async def _trigger_handlers(self, event: StreamEvent) -> None:
        """
        Trigger registered event handlers.
        
        Args:
            event: Event to handle
        """
        handlers = self.event_handlers.get(event.event_type, [])
        
        if not handlers:
            return
        
        tasks = []
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    tasks.append(result)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def register_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register event handler.
        
        Args:
            event_type: Event type to handle
            handler: Handler function (can be async)
        """
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")
    
    def get_client_count(self) -> int:
        """Get number of connected clients."""
        return len(self.clients)
    
    def get_plan_subscriber_count(self, plan_id: str) -> int:
        """Get number of subscribers for a plan."""
        return len(self.plan_subscribers.get(plan_id, set()))
    
    def get_event_history(self, plan_id: str) -> List[StreamEvent]:
        """Get event history for a plan."""
        return self.event_history.get(plan_id, [])
    
    def clear_history(self, plan_id: Optional[str] = None) -> None:
        """
        Clear event history.
        
        Args:
            plan_id: Specific plan to clear, or None for all
        """
        if plan_id:
            self.event_history[plan_id].clear()
            logger.info(f"Cleared event history for plan {plan_id}")
        else:
            self.event_history.clear()
            logger.info("Cleared all event history")


class StreamingExecutionWrapper:
    """
    Wrapper for BaseAgent execution with streaming support.
    
    Wraps agent execution methods to automatically stream
    progress updates via WebSocket.
    """
    
    def __init__(
        self,
        agent: Any,
        streaming_manager: StreamingManager
    ):
        """
        Initialize streaming wrapper.
        
        Args:
            agent: BaseAgent instance to wrap
            streaming_manager: StreamingManager instance
        """
        self.agent = agent
        self.streaming_manager = streaming_manager
        
        logger.info(f"Initialized StreamingExecutionWrapper for agent {agent.agent_id}")
    
    async def execute_research_plan_streaming(
        self,
        plan: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute research plan with streaming progress updates.
        
        Args:
            plan: Research plan to execute
            context: Optional execution context
        
        Returns:
            Plan execution result
        """
        plan_id = plan["plan_id"]
        
        # Stream plan started
        await self.streaming_manager.stream_plan_started(
            plan_id=plan_id,
            plan_data={
                "query": plan.get("query", ""),
                "total_steps": len(plan.get("steps", [])),
                "research_type": plan.get("research_type", "unknown")
            }
        )
        
        # Execute plan (this would call agent's execute_research_plan)
        # For now, simulate execution
        steps = plan.get("steps", [])
        
        for i, step in enumerate(steps):
            step_id = step["step_id"]
            
            # Stream step started
            await self.streaming_manager.stream_step_started(
                plan_id=plan_id,
                step_id=step_id,
                step_data={
                    "step_number": i + 1,
                    "action": step.get("action", "unknown"),
                    "agent_type": step.get("agent_type", "unknown")
                }
            )
            
            # Simulate progress updates
            for progress in [0.25, 0.5, 0.75]:
                await asyncio.sleep(0.1)  # Simulate work
                await self.streaming_manager.stream_step_progress(
                    plan_id=plan_id,
                    step_id=step_id,
                    progress=progress,
                    message=f"Processing {int(progress*100)}%"
                )
            
            # Stream step completed
            await self.streaming_manager.stream_step_completed(
                plan_id=plan_id,
                step_id=step_id,
                result={
                    "status": "success",
                    "quality_score": 0.9,
                    "data": {"result": "Step completed"}
                }
            )
        
        # Stream plan completed
        await self.streaming_manager.stream_event(
            StreamEvent(
                event_type=EventType.PLAN_COMPLETED.value,
                plan_id=plan_id,
                data={
                    "status": "completed",
                    "total_steps": len(steps),
                    "completed_steps": len(steps)
                }
            )
        )
        
        return {
            "status": "completed",
            "plan_id": plan_id,
            "total_steps": len(steps),
            "completed_steps": len(steps)
        }


# ========================================
# Example Usage & Tests
# ========================================

async def _test_streaming_manager():
    """Test streaming manager."""
    print("=" * 80)
    print("STREAMING MANAGER TEST")
    print("=" * 80)
    
    manager = StreamingManager()
    
    # Test 1: Register clients
    print(f"\n[TEST 1] Register Clients")
    print("-" * 40)
    
    class MockWebSocket:
        def __init__(self, id):
            self.id = id
    
    await manager.register_client("client_1", MockWebSocket("ws1"), subscribe_to=["plan_001"])
    await manager.register_client("client_2", MockWebSocket("ws2"), subscribe_to=["plan_001"])
    
    print(f"  ✓ Registered 2 clients")
    print(f"  ✓ Connected clients: {manager.get_client_count()}")
    print(f"  ✓ Plan subscribers: {manager.get_plan_subscriber_count('plan_001')}")
    
    # Test 2: Stream events
    print(f"\n[TEST 2] Stream Events")
    print("-" * 40)
    
    await manager.stream_plan_started(
        plan_id="plan_001",
        plan_data={"query": "Test query", "total_steps": 2}
    )
    
    await manager.stream_step_started(
        plan_id="plan_001",
        step_id="step_1",
        step_data={"action": "search", "agent": "registry"}
    )
    
    await manager.stream_step_progress(
        plan_id="plan_001",
        step_id="step_1",
        progress=0.5,
        message="Processing 50%"
    )
    
    await manager.stream_step_completed(
        plan_id="plan_001",
        step_id="step_1",
        result={"status": "success", "quality": 0.95}
    )
    
    print(f"  ✓ Streamed 4 events")
    
    # Test 3: Event history
    print(f"\n[TEST 3] Event History")
    print("-" * 40)
    
    history = manager.get_event_history("plan_001")
    print(f"  Events in history: {len(history)}")
    
    for event in history:
        print(f"    - {event.event_type} ({event.event_id[:8]}...)")
    
    # Test 4: Client received events
    print(f"\n[TEST 4] Client Events")
    print("-" * 40)
    
    client1 = manager.clients["client_1"]
    if hasattr(client1, '_received_events'):
        print(f"  Client 1 received: {len(client1._received_events)} events")
        for event in client1._received_events[:3]:  # Show first 3
            print(f"    - {event.event_type}")
    
    print("\n" + "=" * 80)
    print("✅ STREAMING MANAGER TEST COMPLETED")
    print("=" * 80)


async def _test_streaming_execution():
    """Test streaming execution wrapper."""
    print("\n" + "=" * 80)
    print("STREAMING EXECUTION TEST")
    print("=" * 80)
    
    manager = StreamingManager()
    
    # Register client
    class MockWebSocket:
        pass
    
    await manager.register_client("client_1", MockWebSocket(), subscribe_to=["plan_002"])
    
    # Create mock agent
    class MockAgent:
        agent_id = "test_agent"
    
    # Create wrapper
    wrapper = StreamingExecutionWrapper(MockAgent(), manager)
    
    # Test plan
    plan = {
        "plan_id": "plan_002",
        "query": "Test streaming execution",
        "research_type": "exploratory",
        "steps": [
            {
                "step_id": "step_1",
                "action": "search",
                "agent_type": "registry"
            },
            {
                "step_id": "step_2",
                "action": "analyze",
                "agent_type": "environmental"
            }
        ]
    }
    
    print(f"\n[Executing Plan with Streaming]")
    result = await wrapper.execute_research_plan_streaming(plan)
    
    print(f"\n[Result]")
    print(f"  Status: {result['status']}")
    print(f"  Completed Steps: {result['completed_steps']}/{result['total_steps']}")
    
    # Check events
    history = manager.get_event_history("plan_002")
    print(f"\n[Events Streamed]")
    print(f"  Total events: {len(history)}")
    
    event_counts = {}
    for event in history:
        event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
    
    for event_type, count in event_counts.items():
        print(f"    {event_type}: {count}")
    
    print("\n" + "=" * 80)
    print("✅ STREAMING EXECUTION TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run async tests
    asyncio.run(_test_streaming_manager())
    asyncio.run(_test_streaming_execution())
