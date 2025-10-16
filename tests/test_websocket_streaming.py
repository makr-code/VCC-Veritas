"""
VERITAS NLP Foundation - WebSocket Streaming Test Client
=========================================================

Test client for WebSocket streaming API.

Tests the complete streaming pipeline:
- Connect to WebSocket
- Send query
- Receive real-time progress updates
- Display results

Created: 2025-10-14
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    print("❌ websockets library not installed. Install with: pip install websockets")
    WEBSOCKETS_AVAILABLE = False
    sys.exit(1)


class StreamingTestClient:
    """Test client for WebSocket streaming API."""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        """
        Initialize test client.
        
        Args:
            host: API host
            port: API port
        """
        self.host = host
        self.port = port
        self.session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.ws_url = f"ws://{host}:{port}/ws/process/{self.session_id}"
        self.events_received = []
    
    async def connect_and_test(self, query: str):
        """
        Connect to WebSocket and test query processing.
        
        Args:
            query: Query to process
        """
        print("=" * 80)
        print(f"WEBSOCKET STREAMING TEST CLIENT")
        print("=" * 80)
        print(f"\nSession ID: {self.session_id}")
        print(f"WebSocket URL: {self.ws_url}")
        print(f"Query: {query}")
        print("\n" + "-" * 80)
        
        try:
            # Connect to WebSocket
            print(f"\n🔗 Connecting to {self.ws_url}...")
            
            async with websockets.connect(self.ws_url) as websocket:
                print(f"✅ Connected!")
                
                # Receive welcome message
                welcome = await websocket.recv()
                welcome_data = json.loads(welcome)
                print(f"📩 Welcome: {welcome_data.get('message', 'Connected')}")
                self.events_received.append(welcome_data)
                
                # Send query
                print(f"\n📤 Sending query: {query}")
                await websocket.send(json.dumps({"query": query}))
                
                # Receive progress updates
                print(f"\n🚀 Receiving progress updates:\n")
                
                plan_started = False
                plan_completed = False
                
                while not plan_completed:
                    # Receive message
                    message = await websocket.recv()
                    data = json.loads(message)
                    self.events_received.append(data)
                    
                    event_type = data.get("event_type")
                    
                    if event_type == "plan_started":
                        total_steps = data.get("data", {}).get("total_steps", 0)
                        print(f"🚀 Plan started: {total_steps} steps")
                        plan_started = True
                    
                    elif event_type == "step_started":
                        step_data = data.get("data", {})
                        current = step_data.get("current_step", 0)
                        total = step_data.get("total_steps", 0)
                        name = step_data.get("step_name", "Unknown")
                        print(f"   ▶️  Step {current}/{total}: {name}")
                    
                    elif event_type == "step_progress":
                        step_data = data.get("data", {})
                        pct = step_data.get("percentage", 0)
                        msg = step_data.get("message", "")
                        print(f"      ⏳ {pct:.1f}%: {msg}")
                    
                    elif event_type == "step_completed":
                        step_data = data.get("data", {})
                        current = step_data.get("current_step", 0)
                        total = step_data.get("total_steps", 0)
                        name = step_data.get("step_name", "Unknown")
                        time = step_data.get("execution_time", 0)
                        print(f"   ✅ Step {current}/{total}: {name} ({time:.3f}s)")
                    
                    elif event_type == "step_failed":
                        step_data = data.get("data", {})
                        error = step_data.get("error", "Unknown error")
                        print(f"   ❌ Step failed: {error}")
                    
                    elif event_type == "plan_completed":
                        step_data = data.get("data", {})
                        time = step_data.get("execution_time", 0)
                        msg = step_data.get("message", "Completed")
                        print(f"\n🎉 {msg} ({time:.3f}s)")
                        plan_completed = True
                    
                    elif event_type == "result":
                        success = data.get("success", False)
                        exec_time = data.get("execution_time", 0)
                        completed = data.get("steps_completed", 0)
                        failed = data.get("steps_failed", 0)
                        print(f"\n📊 Final Result:")
                        print(f"   Success: {success}")
                        print(f"   Execution time: {exec_time:.3f}s")
                        print(f"   Steps completed: {completed}")
                        print(f"   Steps failed: {failed}")
                        break
                    
                    elif event_type == "error":
                        msg = data.get("message", "Unknown error")
                        print(f"❌ Error: {msg}")
                        break
                
                print("\n" + "-" * 80)
                print(f"\n✅ Test completed!")
                print(f"   Total events received: {len(self.events_received)}")
                
        except websockets.exceptions.ConnectionError as e:
            print(f"❌ Connection error: {e}")
            print("\n⚠️  Is the server running? Start with:")
            print(f"   python backend/api/streaming_api.py")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def print_statistics(self):
        """Print test statistics."""
        print("\n" + "=" * 80)
        print("TEST STATISTICS")
        print("=" * 80)
        
        # Count event types
        event_counts = {}
        for event in self.events_received:
            event_type = event.get("event_type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        print(f"\nTotal events: {len(self.events_received)}")
        print(f"\nEvent breakdown:")
        for event_type, count in sorted(event_counts.items()):
            print(f"   {event_type:20s}: {count}")
        
        print("\n" + "=" * 80)


async def run_tests():
    """Run multiple test queries."""
    print("=" * 80)
    print("WEBSOCKET STREAMING - MULTIPLE TEST QUERIES")
    print("=" * 80)
    
    test_queries = [
        "Bauantrag für Einfamilienhaus in Stuttgart",
        "Unterschied zwischen GmbH und AG gründen",
        "Wie viel kostet ein Bauantrag in München?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}/{len(test_queries)}: {query}")
        print(f"{'=' * 80}")
        
        client = StreamingTestClient()
        await client.connect_and_test(query)
        client.print_statistics()
        
        if i < len(test_queries):
            print("\n⏳ Waiting 2 seconds before next test...")
            await asyncio.sleep(2)
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 80)


if __name__ == "__main__":
    if not WEBSOCKETS_AVAILABLE:
        print("❌ websockets library not available")
        sys.exit(1)
    
    print("\n⚠️  Make sure the server is running first:")
    print("   python backend/api/streaming_api.py")
    print("\n" + "=" * 80)
    
    # Run single test
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        client = StreamingTestClient()
        asyncio.run(client.connect_and_test(query))
        client.print_statistics()
    else:
        # Run multiple tests
        asyncio.run(run_tests())
