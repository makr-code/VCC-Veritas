"""
Phase 4.1: Throughput-Optimierung - Performance Benchmarks

Umfassende Performance-Tests für AgentMessageBroker mit Multi-Worker-Pattern.
Vergleicht Baseline (Single-Worker) vs. Optimized (Multi-Worker + Batching).

Test-Scenarios:
1. Baseline vs. Multi-Worker Throughput
2. Worker-Scaling-Tests (1, 3, 5, 10 Workers)
3. Batch-Size-Optimization
4. Latency under Load
5. Concurrent Requests Performance

Version: 1.0
Author: VERITAS Development Team
Date: 6. Oktober 2025
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import statistics

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared"))

try:
    from backend.agents.agent_message_broker import AgentMessageBroker
    from backend.agents.agent_message_broker_enhanced import BrokerConfiguration
    from shared.protocols.agent_message import (
        AgentIdentity,
        AgentMessage,
        MessageType,
        MessagePriority,
        create_request_message
    )
except ModuleNotFoundError:
    from agents.agent_message_broker import AgentMessageBroker
    from agents.agent_message_broker_enhanced import BrokerConfiguration
    from protocols.agent_message import (
        AgentIdentity,
        AgentMessage,
        MessageType,
        MessagePriority,
        create_request_message
    )


class PerformanceBenchmark:
    """
    Performance-Benchmark-Suite für AgentMessageBroker
    """
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
    
    async def run_all_benchmarks(self):
        """Führt alle Benchmarks aus"""
        print("=" * 80)
        print("PHASE 4.1: THROUGHPUT-OPTIMIERUNG - PERFORMANCE BENCHMARKS")
        print("=" * 80)
        print()
        
        # Test 1: Baseline vs. Optimized
        await self.test_baseline_vs_optimized()
        
        # Test 2: Worker Scaling
        await self.test_worker_scaling()
        
        # Test 3: Batch Size Optimization
        await self.test_batch_size_optimization()
        
        # Test 4: Latency under Load
        await self.test_latency_under_load()
        
        # Test 5: Concurrent Requests
        await self.test_concurrent_requests()
        
        # Summary
        self.print_summary()
    
    async def test_baseline_vs_optimized(self):
        """Test 1: Baseline (1 Worker, No Batching) vs. Optimized (5 Workers, Batching)"""
        print("TEST 1: Baseline vs. Optimized")
        print("-" * 80)
        
        num_messages = 1000
        
        # Baseline: 1 Worker, No Batching
        print(f"  Running BASELINE (1 worker, no batching, {num_messages} messages)...")
        config_baseline = BrokerConfiguration(
            num_workers=1,
            enable_batching=False
        )
        throughput_baseline, latency_baseline = await self.measure_throughput(
            config_baseline,
            num_messages
        )
        
        # Optimized: 5 Workers, Batching
        print(f"  Running OPTIMIZED (5 workers, batching, {num_messages} messages)...")
        config_optimized = BrokerConfiguration(
            num_workers=5,
            enable_batching=True,
            batch_size=20
        )
        throughput_optimized, latency_optimized = await self.measure_throughput(
            config_optimized,
            num_messages
        )
        
        # Results
        improvement_factor = throughput_optimized / throughput_baseline
        
        self.results.append({
            "test": "Baseline vs. Optimized",
            "baseline_throughput": throughput_baseline,
            "optimized_throughput": throughput_optimized,
            "improvement_factor": improvement_factor,
            "baseline_latency": latency_baseline,
            "optimized_latency": latency_optimized
        })
        
        print(f"\n  RESULTS:")
        print(f"    Baseline Throughput:   {throughput_baseline:.1f} msg/s")
        print(f"    Optimized Throughput:  {throughput_optimized:.1f} msg/s")
        print(f"    Improvement Factor:    {improvement_factor:.1f}x")
        print(f"    Baseline Latency:      {latency_baseline:.1f}ms")
        print(f"    Optimized Latency:     {latency_optimized:.1f}ms")
        print(f"    [PASS]" if throughput_optimized >= 500 else f"    [FAIL] (< 500 msg/s)")
        print()
    
    async def test_worker_scaling(self):
        """Test 2: Worker Scaling (1, 3, 5, 10 Workers)"""
        print("TEST 2: Worker Scaling")
        print("-" * 80)
        
        num_messages = 500
        worker_counts = [1, 3, 5, 10]
        results_scaling = []
        
        for num_workers in worker_counts:
            print(f"  Testing {num_workers} worker(s)...")
            
            config = BrokerConfiguration(
                num_workers=num_workers,
                enable_batching=True,
                batch_size=20
            )
            
            throughput, latency = await self.measure_throughput(config, num_messages)
            results_scaling.append({
                "workers": num_workers,
                "throughput": throughput,
                "latency": latency
            })
            
            print(f"    -> {throughput:.1f} msg/s, {latency:.1f}ms latency")
        
        self.results.append({
            "test": "Worker Scaling",
            "results": results_scaling
        })
        
        print(f"\n  SCALING ANALYSIS:")
        for i, result in enumerate(results_scaling):
            if i == 0:
                print(f"    {result['workers']} worker(s):  {result['throughput']:.1f} msg/s (baseline)")
            else:
                scaling_factor = result['throughput'] / results_scaling[0]['throughput']
                expected = result['workers'] / results_scaling[0]['workers']
                efficiency = (scaling_factor / expected) * 100
                print(f"    {result['workers']} worker(s):  {result['throughput']:.1f} msg/s ({scaling_factor:.1f}x, {efficiency:.0f}% efficiency)")
        print()
    
    async def test_batch_size_optimization(self):
        """Test 3: Batch Size Optimization"""
        print("TEST 3: Batch Size Optimization")
        print("-" * 80)
        
        num_messages = 500
        batch_sizes = [1, 5, 10, 20, 50]
        results_batching = []
        
        for batch_size in batch_sizes:
            print(f"  Testing batch_size={batch_size}...")
            
            config = BrokerConfiguration(
                num_workers=5,
                enable_batching=True,
                batch_size=batch_size
            )
            
            throughput, latency = await self.measure_throughput(config, num_messages)
            results_batching.append({
                "batch_size": batch_size,
                "throughput": throughput,
                "latency": latency
            })
            
            print(f"    -> {throughput:.1f} msg/s, {latency:.1f}ms latency")
        
        # Find optimal batch size
        optimal = max(results_batching, key=lambda x: x['throughput'])
        
        self.results.append({
            "test": "Batch Size Optimization",
            "results": results_batching,
            "optimal_batch_size": optimal['batch_size']
        })
        
        print(f"\n  OPTIMAL BATCH SIZE: {optimal['batch_size']} ({optimal['throughput']:.1f} msg/s)")
        print()
    
    async def test_latency_under_load(self):
        """Test 4: Latency under Load (P50, P95, P99)"""
        print("TEST 4: Latency under Load")
        print("-" * 80)
        
        num_messages = 1000
        
        print(f"  Measuring latency distribution ({num_messages} messages)...")
        
        config = BrokerConfiguration(
            num_workers=5,
            enable_batching=True,
            batch_size=20
        )
        
        broker = AgentMessageBroker(config=config)
        await broker.start()
        
        # Setup test agents
        agent_a = await self.create_test_agent("agent-a", broker)
        agent_b = await self.create_test_agent("agent-b", broker)
        
        # Measure latencies
        latencies = []
        
        for i in range(num_messages):
            start = asyncio.get_event_loop().time()
            
            message = create_request_message(
                sender=agent_a,
                recipient=agent_b,
                payload={"data": i}
            )
            await broker.send_message(message)
            
            # Wait for delivery (approximation)
            await asyncio.sleep(0.001)
            
            latency_ms = (asyncio.get_event_loop().time() - start) * 1000
            latencies.append(latency_ms)
        
        # Wait for completion
        await asyncio.sleep(1.0)
        
        await broker.stop()
        
        # Calculate percentiles
        p50 = statistics.median(latencies)
        p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        
        self.results.append({
            "test": "Latency under Load",
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "p99_latency_ms": p99
        })
        
        print(f"\n  LATENCY PERCENTILES:")
        print(f"    P50: {p50:.1f}ms")
        print(f"    P95: {p95:.1f}ms")
        print(f"    P99: {p99:.1f}ms")
        print(f"    [PASS]" if p95 < 200 else f"    [FAIL] (P95 >= 200ms)")
        print()
    
    async def test_concurrent_requests(self):
        """Test 5: Concurrent Requests Performance"""
        print("TEST 5: Concurrent Requests")
        print("-" * 80)
        
        num_concurrent = 50
        
        print(f"  Sending {num_concurrent} concurrent requests...")
        
        config = BrokerConfiguration(
            num_workers=5,
            enable_batching=True,
            batch_size=20
        )
        
        broker = AgentMessageBroker(config=config)
        await broker.start()
        
        # Setup test agents
        agent_a = await self.create_test_agent("agent-a", broker)
        agent_b = await self.create_test_agent("agent-b", broker)
        
        # Send concurrent requests
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for i in range(num_concurrent):
            message = create_request_message(
                sender=agent_a,
                recipient=agent_b,
                payload={"request_id": i}
            )
            task = asyncio.create_task(broker.send_message(message))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Wait for delivery
        await asyncio.sleep(1.0)
        
        elapsed = asyncio.get_event_loop().time() - start_time
        throughput = num_concurrent / elapsed
        
        await broker.stop()
        
        self.results.append({
            "test": "Concurrent Requests",
            "num_concurrent": num_concurrent,
            "elapsed_sec": elapsed,
            "throughput": throughput
        })
        
        print(f"\n  RESULTS:")
        print(f"    Concurrent Requests: {num_concurrent}")
        print(f"    Elapsed Time:        {elapsed:.2f}s")
        print(f"    Throughput:          {throughput:.1f} msg/s")
        print()
    
    async def measure_throughput(
        self,
        config: BrokerConfiguration,
        num_messages: int
    ) -> tuple[float, float]:
        """
        Misst Throughput und Latency für gegebene Konfiguration
        
        Returns:
            (throughput_msg_per_sec, avg_latency_ms)
        """
        broker = AgentMessageBroker(config=config)
        await broker.start()
        
        # Setup test agents
        agent_a = await self.create_test_agent("agent-a", broker)
        agent_b = await self.create_test_agent("agent-b", broker)
        
        # Measure throughput
        start_time = asyncio.get_event_loop().time()
        
        for i in range(num_messages):
            message = create_request_message(
                sender=agent_a,
                recipient=agent_b,
                payload={"data": i}
            )
            await broker.send_message(message)
        
        # Wait for all deliveries
        await asyncio.sleep(0.5)
        
        # Poll queue until empty
        while broker._message_queue.qsize() > 0:
            await asyncio.sleep(0.01)
        
        # Extra buffer
        await asyncio.sleep(0.5)
        
        elapsed = asyncio.get_event_loop().time() - start_time
        throughput = num_messages / elapsed
        avg_latency = (elapsed / num_messages) * 1000  # ms
        
        await broker.stop()
        
        return throughput, avg_latency
    
    async def create_test_agent(self, agent_id: str, broker: AgentMessageBroker) -> AgentIdentity:
        """Erstellt Test-Agent"""
        identity = AgentIdentity(
            agent_id=agent_id,
            agent_type="test",
            agent_name=f"Test Agent {agent_id}",
            capabilities=["test"]
        )
        
        async def handler(message: AgentMessage):
            # Einfacher Echo-Handler
            return {"echo": message.payload}
        
        broker.register_agent(identity, handler)
        
        return identity
    
    def print_summary(self):
        """Druckt Zusammenfassung aller Tests"""
        print("=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        print()
        
        # Test 1: Baseline vs. Optimized
        test1 = next((r for r in self.results if r["test"] == "Baseline vs. Optimized"), None)
        if test1:
            print(f"[OK] Baseline vs. Optimized:")
            print(f"   Improvement: {test1['improvement_factor']:.1f}x ({test1['baseline_throughput']:.1f} -> {test1['optimized_throughput']:.1f} msg/s)")
            print(f"   Target Met: {'YES [PASS]' if test1['optimized_throughput'] >= 500 else 'NO [FAIL]'} (>= 500 msg/s)")
            print()
        
        # Test 4: Latency
        test4 = next((r for r in self.results if r["test"] == "Latency under Load"), None)
        if test4:
            print(f"[OK] Latency under Load:")
            print(f"   P50: {test4['p50_latency_ms']:.1f}ms")
            print(f"   P95: {test4['p95_latency_ms']:.1f}ms ({('< 200ms [PASS]' if test4['p95_latency_ms'] < 200 else '>= 200ms [FAIL]')})")
            print(f"   P99: {test4['p99_latency_ms']:.1f}ms")
            print()
        
        print("=" * 80)
        print("BENCHMARKS COMPLETE")
        print("=" * 80)


async def main():
    """Main Benchmark Runner"""
    benchmark = PerformanceBenchmark()
    await benchmark.run_all_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())
