"""
WebSocket Streaming Integration Tests
=====================================

Integration tests for WebSocket streaming with agent execution.

Tests:
1. Streaming Manager - Basic functionality
2. Client Management - Register/unregister/subscribe
3. Event Distribution - Multi-client broadcasting
4. Execution Wrapper - Plan execution with streaming
5. Event History - Historical event replay

Created: 2025-10-08
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent / "framework"))

from framework.streaming_manager import EventType, StreamEvent, StreamingExecutionWrapper, StreamingManager


async def test_streaming_manager():
    """Test streaming manager basic functionality."""
    print("\n" + "=" * 80)
    print("TEST 1: STREAMING MANAGER")
    print("=" * 80)

    manager = StreamingManager(ping_interval=30)

    print("\n✓ StreamingManager created")
    assert manager.get_client_count() == 0

    # Register mock client
    class MockWebSocket:
        def __init__(self, id):
            self.id = id

    await manager.register_client("client_test_1", MockWebSocket("ws1"), subscribe_to=["plan_stream_001"])

    print("✓ Client registered")
    assert manager.get_client_count() == 1
    assert manager.get_plan_subscriber_count("plan_stream_001") == 1

    # Stream event
    await manager.stream_event(
        StreamEvent(event_type=EventType.PLAN_STARTED.value, plan_id="plan_stream_001", data={"query": "Test query"})
    )

    print("✓ Event streamed")
    history = manager.get_event_history("plan_stream_001")
    assert len(history) == 1

    print("\n✅ TEST 1 PASSED - Basic streaming working")
    return True


async def test_client_management():
    """Test client registration and subscription."""
    print("\n" + "=" * 80)
    print("TEST 2: CLIENT MANAGEMENT")
    print("=" * 80)

    manager = StreamingManager()

    class MockWS:
        def __init__(self, id):
            self.id = id

    # Register multiple clients
    print(f"\n[Register Clients]")
    await manager.register_client("client_1", MockWS("ws1"))
    await manager.register_client("client_2", MockWS("ws2"))
    await manager.register_client("client_3", MockWS("ws3"))

    print(f"  ✓ Registered 3 clients")
    assert manager.get_client_count() == 3

    # Subscribe clients to different plans
    print(f"\n[Subscribe to Plans]")
    await manager.subscribe("client_1", "plan_A")
    await manager.subscribe("client_1", "plan_B")
    await manager.subscribe("client_2", "plan_A")
    await manager.subscribe("client_3", "plan_C")

    print(f"  ✓ Clients subscribed")
    assert manager.get_plan_subscriber_count("plan_A") == 2
    assert manager.get_plan_subscriber_count("plan_B") == 1
    assert manager.get_plan_subscriber_count("plan_C") == 1

    # Unsubscribe
    print(f"\n[Unsubscribe]")
    await manager.unsubscribe("client_1", "plan_A")

    assert manager.get_plan_subscriber_count("plan_A") == 1
    print(f"  ✓ Unsubscribe working")

    # Unregister client
    print(f"\n[Unregister Client]")
    await manager.unregister_client("client_3")

    assert manager.get_client_count() == 2
    assert manager.get_plan_subscriber_count("plan_C") == 0
    print(f"  ✓ Unregister working")

    print(f"\n✅ TEST 2 PASSED - Client management working")
    return True


async def test_event_distribution():
    """Test event distribution to multiple clients."""
    print("\n" + "=" * 80)
    print("TEST 3: EVENT DISTRIBUTION")
    print("=" * 80)

    manager = StreamingManager()

    class MockWS:
        def __init__(self, id):
            self.id = id

    # Register clients
    print(f"\n[Setup: 3 clients, plan_multi_001]")
    await manager.register_client("c1", MockWS("ws1"), subscribe_to=["plan_multi_001"])
    await manager.register_client("c2", MockWS("ws2"), subscribe_to=["plan_multi_001"])
    await manager.register_client("c3", MockWS("ws3"), subscribe_to=["plan_multi_001"])

    print(f"  ✓ 3 clients subscribed to plan_multi_001")

    # Stream events
    print(f"\n[Stream 5 Events]")
    events_to_send = [
        ("plan_started", {"query": "Multi - client test"}),
        ("step_started", {"step_id": "step_1"}),
        ("step_progress", {"progress": 0.5}),
        ("step_completed", {"status": "success"}),
        ("plan_completed", {"status": "completed"}),
    ]

    for event_type, data in events_to_send:
        await manager.stream_event(StreamEvent(event_type=event_type, plan_id="plan_multi_001", data=data))

    print(f"  ✓ Streamed {len(events_to_send)} events")

    # Verify all clients received events
    print("\n[Verify Distribution]")
    for client_id in ["c1", "c2", "c3"]:
        client = manager.clients[client_id]
        received_count = len(getattr(client, "_received_events", []))
        print(f"  Client {client_id}: {received_count} events received")
        assert received_count == 6  # 5 + welcome ping

    print("\n✅ TEST 3 PASSED - Event distribution working")
    return True


async def test_execution_wrapper():
    """Test streaming execution wrapper."""
    print("\n" + "=" * 80)
    print("TEST 4: EXECUTION WRAPPER")
    print("=" * 80)

    manager = StreamingManager()

    class MockWS:
        pass

    # Register client
    await manager.register_client("client_exec", MockWS(), subscribe_to=["plan_exec_001"])

    print("\n✓ Client registered and subscribed")

    # Create mock agent
    class MockAgent:
        agent_id = "exec_test_agent"

    # Create wrapper
    wrapper = StreamingExecutionWrapper(MockAgent(), manager)

    print(f"✓ StreamingExecutionWrapper created")

    # Execute plan with streaming
    print(f"\n[Execute Plan with Streaming]")
    plan = {
        "plan_id": "plan_exec_001",
        "query": "Test execution streaming",
        "research_type": "exploratory",
        "steps": [
            {"step_id": "step_1", "action": "search", "agent_type": "registry"},
            {"step_id": "step_2", "action": "analyze", "agent_type": "environmental"},
            {"step_id": "step_3", "action": "synthesize", "agent_type": "social"},
        ],
    }

    result = await wrapper.execute_research_plan_streaming(plan)

    print("\n[Result]")
    print(f"  Status: {result['status']}")
    print(f"  Completed: {result['completed_steps']}/{result['total_steps']}")

    assert result["status"] == "completed"
    assert result["completed_steps"] == 3

    # Verify events
    print("\n[Verify Events]")
    history = manager.get_event_history("plan_exec_001")

    event_counts = {}
    for event in history:
        event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

    print(f"  Total events: {len(history)}")
    for event_type, count in event_counts.items():
        print(f"    {event_type}: {count}")

    # Expected: 1 plan_started, 3 step_started, 9 step_progress (3 per step),
    # 3 step_completed, 1 plan_completed = 17 total
    assert len(history) == 17
    assert event_counts["plan_started"] == 1
    assert event_counts["step_started"] == 3
    assert event_counts["step_progress"] == 9
    assert event_counts["step_completed"] == 3
    assert event_counts["plan_completed"] == 1

    print("\n✅ TEST 4 PASSED - Execution wrapper working")
    return True


async def test_event_history():
    """Test event history and replay."""
    print("\n" + "=" * 80)
    print("TEST 5: EVENT HISTORY")
    print("=" * 80)

    manager = StreamingManager()

    class MockWS:
        pass

    # Stream events before client connects
    print("\n[Stream 3 Events (no clients yet)]")
    plan_id = "plan_history_001"

    for i in range(3):
        await manager.stream_event(
            StreamEvent(event_type="step_completed", plan_id=plan_id, step_id=f"step_{i + 1}", data={"status": "success"})
        )

    print("  ✓ 3 events streamed")

    history_before = manager.get_event_history(plan_id)
    assert len(history_before) == 3
    print(f"  ✓ History contains {len(history_before)} events")

    # Register client (should receive history)
    print("\n[Register Late Client]")
    await manager.register_client("late_client", MockWS())
    await manager.subscribe("late_client", plan_id)

    # Check if client received historical events
    client = manager.clients["late_client"]
    received = getattr(client, "_received_events", [])

    # Should have: welcome ping + 3 historical events
    print(f"  ✓ Late client received {len(received)} events")
    assert len(received) >= 3  # At least the historical events

    # Clear history
    print("\n[Clear History]")
    manager.clear_history(plan_id)

    history_after = manager.get_event_history(plan_id)
    assert len(history_after) == 0
    print("  ✓ History cleared")

    print(f"\n✅ TEST 5 PASSED - Event history working")
    return True


async def test_event_handlers():
    """Test event handler registration."""
    print("\n" + "=" * 80)
    print("TEST 6: EVENT HANDLERS")
    print("=" * 80)

    manager = StreamingManager()

    # Track handler calls
    handler_calls = []

    def sync_handler(event: StreamEvent):
        handler_calls.append(("sync", event.event_type))

    async def async_handler(event: StreamEvent):
        await asyncio.sleep(0.01)
        handler_calls.append(("async", event.event_type))

    # Register handlers
    print(f"\n[Register Handlers]")
    manager.register_handler("step_started", sync_handler)
    manager.register_handler("step_started", async_handler)

    print(f"  ✓ Registered 2 handlers for step_started")

    # Trigger event
    print(f"\n[Trigger Event]")
    await manager.stream_event(StreamEvent(event_type="step_started", plan_id="plan_handler_001", step_id="step_1"))

    # Small delay for async handler
    await asyncio.sleep(0.02)

    print(f"  ✓ Event triggered")
    print(f"  Handler calls: {len(handler_calls)}")

    assert len(handler_calls) == 2
    assert ("sync", "step_started") in handler_calls
    assert ("async", "step_started") in handler_calls

    print("\n✅ TEST 6 PASSED - Event handlers working")
    return True


async def run_all_tests():
    """Run all streaming integration tests."""
    print("\n" + "=" * 80)
    print("WEBSOCKET STREAMING INTEGRATION TESTS")
    print("=" * 80)

    results = []

    try:
        results.append(("Streaming Manager", await test_streaming_manager()))
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        results.append(("Streaming Manager", False))

    try:
        results.append(("Client Management", await test_client_management()))
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        results.append(("Client Management", False))

    try:
        results.append(("Event Distribution", await test_event_distribution()))
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        results.append(("Event Distribution", False))

    try:
        results.append(("Execution Wrapper", await test_execution_wrapper()))
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        results.append(("Execution Wrapper", False))

    try:
        results.append(("Event History", await test_event_history()))
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        results.append(("Event History", False))

    try:
        results.append(("Event Handlers", await test_event_handlers()))
    except Exception as e:
        print(f"\n❌ TEST 6 FAILED: {e}")
        results.append(("Event Handlers", False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results:
        icon = "✅" if passed else "❌"
        print(f"{icon} {test_name}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\nResults: {passed_count}/{total_count} tests passed ({passed_count / total_count * 100:.0f}%)")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return True
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")  # Reduce noise

    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
