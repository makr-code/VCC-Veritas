"""
VERITAS Agent Framework - Phase 5.1: Load Testing & Performance Suite (Simplified)

Comprehensive load testing with existing framework components.

Author: VERITAS Development Team
Created: 2025-10-08
"""

import asyncio
import json
import logging
import os
import statistics
import sys
import time
import tracemalloc
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple

import psutil

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

# Reduce logging noise
logging.basicConfig(level=logging.WARNING)

from agents.framework.agent_monitoring import AgentMonitor, MonitoringService
from agents.framework.base_agent import BaseAgent
from agents.framework.quality_gate import QualityGate, QualityPolicy
from agents.framework.streaming_manager import StreamingManager


@dataclass
class PerformanceMetrics:
    """Performance test metrics"""

    test_name: str
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    p95_time: float
    p99_time: float
    throughput: float
    memory_start_mb: float
    memory_peak_mb: float
    memory_leaked_mb: float
    cpu_avg_percent: float
    success_rate: float
    error_count: int
    total_operations: int


class LoadTestAgent(BaseAgent):
    """Simple test agent for load testing"""

    def get_agent_type(self) -> str:
        return "load_test"

    def get_capabilities(self) -> List[str]:
        return ["testing", "benchmarking"]

    async def execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate fast execution"""
        await asyncio.sleep(0.001)  # 1ms work
        return {
            "status": "success",
            "agent_id": self.agent_id,
            "data": {"result": f'test_result_{step.get("step_id", "unknown")}'},
            "quality_score": 0.85,
            "timestamp": datetime.now().isoformat(),
        }


class PerformanceTester:
    """Load testing system"""

    def __init__(self):
        self.results: List[PerformanceMetrics] = []
        self.process = psutil.Process()

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print("\n" + "=" * 70)
        print("VERITAS AGENT FRAMEWORK - LOAD TESTING SUITE")
        print("=" * 70 + "\n")

        # Test 1: Concurrent Agent Execution
        print("Test 1: Concurrent Agent Execution (100 agents)")
        metrics1 = await self.test_concurrent_agents(num_agents=100)
        self.results.append(metrics1)
        self._print_metrics(metrics1)

        # Test 2: Stress Test
        print("\nTest 2: Stress Test (250 concurrent agents)")
        metrics2 = await self.test_concurrent_agents(num_agents=250)
        self.results.append(metrics2)
        self._print_metrics(metrics2)

        # Test 3: Memory Leak Detection
        print("\nTest 3: Memory Leak Detection (500 sequential operations)")
        metrics3 = await self.test_memory_leaks(iterations=500)
        self.results.append(metrics3)
        self._print_metrics(metrics3)

        # Test 4: Quality Gate Performance
        print("\nTest 4: Quality Gate Performance (10,000 validations)")
        metrics4 = await self.test_quality_gate(num_validations=10000)
        self.results.append(metrics4)
        self._print_metrics(metrics4)

        # Test 5: Monitoring Overhead
        print("\nTest 5: Monitoring Overhead (1,000 tracked executions)")
        metrics5 = await self.test_monitoring_overhead(num_executions=1000)
        self.results.append(metrics5)
        self._print_metrics(metrics5)

        # Test 6: Streaming Performance
        print("\nTest 6: Streaming Performance (1,000 events, 10 clients)")
        metrics6 = await self.test_streaming(num_events=1000, num_clients=10)
        self.results.append(metrics6)
        self._print_metrics(metrics6)

        # Test 7: Sustained Load
        print("\nTest 7: Sustained Load (50 ops/min for 3 minutes)")
        metrics7 = await self.test_sustained_load(ops_per_minute=50, duration_minutes=3)
        self.results.append(metrics7)
        self._print_metrics(metrics7)

        # Summary
        print("\n" + "=" * 70)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 70 + "\n")

        summary = self._generate_summary()
        self._print_summary(summary)

        return summary

    async def test_concurrent_agents(self, num_agents: int) -> PerformanceMetrics:
        """Test concurrent agent execution"""
        tracemalloc.start()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        cpu_samples = []

        execution_times = []
        errors = 0
        memory_peak = memory_start

        async def execute_agent_task(agent_id: int) -> Tuple[float, bool]:
            """Execute single agent task"""
            start = time.time()
            try:
                agent = LoadTestAgent(agent_id=f"agent_{agent_id}")

                # Execute 5 steps
                for i in range(5):
                    step = {"step_id": f"step_{agent_id}_{i}", "description": f"Test step {i}"}
                    result = await agent.execute_step(step, {})

                    # Sample resources periodically
                    if i == 2:
                        cpu_samples.append(self.process.cpu_percent())
                        nonlocal memory_peak
                        current_mem = self.process.memory_info().rss / 1024 / 1024
                        memory_peak = max(memory_peak, current_mem)

                return time.time() - start, True
            except Exception as e:
                return time.time() - start, False

        start_time = time.time()
        results = await asyncio.gather(*[execute_agent_task(i) for i in range(num_agents)])
        total_time = time.time() - start_time

        execution_times = [r[0] for r in results]
        errors = sum(1 for r in results if not r[1])

        memory_end = self.process.memory_info().rss / 1024 / 1024
        tracemalloc.stop()

        sorted_times = sorted(execution_times)

        return PerformanceMetrics(
            test_name=f"Concurrent Agents ({num_agents})",
            total_time=total_time,
            avg_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            p95_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_time=sorted_times[int(len(sorted_times) * 0.99)],
            throughput=num_agents * 5 / total_time,
            memory_start_mb=memory_start,
            memory_peak_mb=memory_peak,
            memory_leaked_mb=memory_end - memory_start,
            cpu_avg_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            success_rate=(num_agents - errors) / num_agents * 100,
            error_count=errors,
            total_operations=num_agents * 5,
        )

    async def test_memory_leaks(self, iterations: int) -> PerformanceMetrics:
        """Test for memory leaks"""
        tracemalloc.start()
        memory_start = self.process.memory_info().rss / 1024 / 1024

        agent = LoadTestAgent(agent_id="mem_test_agent")

        execution_times = []
        memory_samples = [memory_start]
        cpu_samples = []
        errors = 0

        start_time = time.time()

        for i in range(iterations):
            iter_start = time.time()
            try:
                step = {"step_id": f"step_{i}", "description": f"Test {i}"}
                await agent.execute_step(step, {})
                execution_times.append(time.time() - iter_start)
            except:
                errors += 1

            if i % 50 == 0:
                memory_samples.append(self.process.memory_info().rss / 1024 / 1024)
                cpu_samples.append(self.process.cpu_percent())

        total_time = time.time() - start_time
        memory_end = self.process.memory_info().rss / 1024 / 1024
        tracemalloc.stop()

        sorted_times = sorted(execution_times)

        return PerformanceMetrics(
            test_name=f"Memory Leak Test ({iterations} iterations)",
            total_time=total_time,
            avg_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            p95_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_time=sorted_times[int(len(sorted_times) * 0.99)],
            throughput=iterations / total_time,
            memory_start_mb=memory_start,
            memory_peak_mb=max(memory_samples),
            memory_leaked_mb=memory_end - memory_start,
            cpu_avg_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            success_rate=(iterations - errors) / iterations * 100,
            error_count=errors,
            total_operations=iterations,
        )

    async def test_quality_gate(self, num_validations: int) -> PerformanceMetrics:
        """Test quality gate performance"""
        tracemalloc.start()
        memory_start = self.process.memory_info().rss / 1024 / 1024

        policy = QualityPolicy(min_quality=0.7, target_quality=0.9)
        gate = QualityGate(policy)

        execution_times = []
        cpu_samples = []
        errors = 0
        memory_peak = memory_start

        start_time = time.time()

        for i in range(num_validations):
            validation_start = time.time()
            try:
                result = {
                    "agent_id": "test_agent",
                    "status": "success",
                    "data": {"test": f"data_{i}"},
                    "quality_score": 0.75 + (i % 20) / 100,
                }

                decision = gate.validate(result)
                execution_times.append(time.time() - validation_start)

                if i % 1000 == 0:
                    cpu_samples.append(self.process.cpu_percent())
                    current_mem = self.process.memory_info().rss / 1024 / 1024
                    memory_peak = max(memory_peak, current_mem)
            except:
                errors += 1

        total_time = time.time() - start_time
        memory_end = self.process.memory_info().rss / 1024 / 1024
        tracemalloc.stop()

        sorted_times = sorted(execution_times)

        return PerformanceMetrics(
            test_name=f"Quality Gate ({num_validations} validations)",
            total_time=total_time,
            avg_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            p95_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_time=sorted_times[int(len(sorted_times) * 0.99)],
            throughput=num_validations / total_time,
            memory_start_mb=memory_start,
            memory_peak_mb=memory_peak,
            memory_leaked_mb=memory_end - memory_start,
            cpu_avg_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            success_rate=(num_validations - errors) / num_validations * 100,
            error_count=errors,
            total_operations=num_validations,
        )

    async def test_monitoring_overhead(self, num_executions: int) -> PerformanceMetrics:
        """Test monitoring overhead"""
        tracemalloc.start()
        memory_start = self.process.memory_info().rss / 1024 / 1024

        monitor = AgentMonitor("test_agent")

        execution_times = []
        cpu_samples = []
        memory_peak = memory_start

        start_time = time.time()

        for i in range(num_executions):
            exec_start = time.time()

            # Record start
            monitor.record_execution_start(f"step_{i}")

            # Simulate work
            await asyncio.sleep(0.001)

            # Record success
            monitor.record_execution_success(f"step_{i}", {"data": f"result_{i}"}, 0.85)

            execution_times.append(time.time() - exec_start)

            if i % 100 == 0:
                cpu_samples.append(self.process.cpu_percent())
                current_mem = self.process.memory_info().rss / 1024 / 1024
                memory_peak = max(memory_peak, current_mem)

        total_time = time.time() - start_time
        memory_end = self.process.memory_info().rss / 1024 / 1024
        tracemalloc.stop()

        sorted_times = sorted(execution_times)

        return PerformanceMetrics(
            test_name=f"Monitoring Overhead ({num_executions} tracked)",
            total_time=total_time,
            avg_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            p95_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_time=sorted_times[int(len(sorted_times) * 0.99)],
            throughput=num_executions / total_time,
            memory_start_mb=memory_start,
            memory_peak_mb=memory_peak,
            memory_leaked_mb=memory_end - memory_start,
            cpu_avg_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            success_rate=100.0,
            error_count=0,
            total_operations=num_executions,
        )

    async def test_streaming(self, num_events: int, num_clients: int) -> PerformanceMetrics:
        """Test streaming performance"""
        tracemalloc.start()
        memory_start = self.process.memory_info().rss / 1024 / 1024

        streaming = StreamingManager()

        # Register clients
        for i in range(num_clients):
            await streaming.register_client(f"client_{i}")

        execution_times = []
        cpu_samples = []
        errors = 0
        memory_peak = memory_start

        start_time = time.time()

        for i in range(num_events):
            event_start = time.time()
            try:
                await streaming.broadcast_event(
                    {"type": "test_event", "data": f"Event {i}", "timestamp": datetime.now().isoformat()}
                )
                execution_times.append(time.time() - event_start)

                if i % 100 == 0:
                    cpu_samples.append(self.process.cpu_percent())
                    current_mem = self.process.memory_info().rss / 1024 / 1024
                    memory_peak = max(memory_peak, current_mem)
            except:
                errors += 1

        total_time = time.time() - start_time
        memory_end = self.process.memory_info().rss / 1024 / 1024
        tracemalloc.stop()

        sorted_times = sorted(execution_times)

        return PerformanceMetrics(
            test_name=f"Streaming ({num_events} events, {num_clients} clients)",
            total_time=total_time,
            avg_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            p95_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_time=sorted_times[int(len(sorted_times) * 0.99)],
            throughput=num_events / total_time,
            memory_start_mb=memory_start,
            memory_peak_mb=memory_peak,
            memory_leaked_mb=memory_end - memory_start,
            cpu_avg_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            success_rate=(num_events - errors) / num_events * 100,
            error_count=errors,
            total_operations=num_events * num_clients,
        )

    async def test_sustained_load(self, ops_per_minute: int, duration_minutes: int) -> PerformanceMetrics:
        """Test sustained load"""
        tracemalloc.start()
        memory_start = self.process.memory_info().rss / 1024 / 1024

        agent = LoadTestAgent(agent_id="sustained_test_agent")

        execution_times = []
        memory_samples = [memory_start]
        cpu_samples = []
        errors = 0
        total_ops = 0

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        interval = 60.0 / ops_per_minute

        print(f"  Running sustained load: {ops_per_minute} ops/min for {duration_minutes} minutes...")

        next_op_time = start_time
        while time.time() < end_time:
            op_start = time.time()
            try:
                step = {"step_id": f"step_{total_ops}", "description": f"Sustained test {total_ops}"}
                await agent.execute_step(step, {})
                execution_times.append(time.time() - op_start)
                total_ops += 1
            except:
                errors += 1

            if total_ops % (ops_per_minute // 2) == 0:
                memory_samples.append(self.process.memory_info().rss / 1024 / 1024)
                cpu_samples.append(self.process.cpu_percent())
                elapsed = (time.time() - start_time) / 60
                print(f"  Progress: {elapsed:.1f}/{duration_minutes} min, Ops: {total_ops}, Errors: {errors}")

            next_op_time += interval
            wait_time = next_op_time - time.time()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        total_time = time.time() - start_time
        memory_end = self.process.memory_info().rss / 1024 / 1024
        tracemalloc.stop()

        sorted_times = sorted(execution_times)

        return PerformanceMetrics(
            test_name=f"Sustained Load ({ops_per_minute} ops/min, {duration_minutes} min)",
            total_time=total_time,
            avg_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            p95_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_time=sorted_times[int(len(sorted_times) * 0.99)],
            throughput=total_ops / total_time,
            memory_start_mb=memory_start,
            memory_peak_mb=max(memory_samples),
            memory_leaked_mb=memory_end - memory_start,
            cpu_avg_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            success_rate=(total_ops - errors) / total_ops * 100 if total_ops > 0 else 0,
            error_count=errors,
            total_operations=total_ops,
        )

    def _print_metrics(self, metrics: PerformanceMetrics):
        """Print formatted metrics"""
        print(f"  [OK] Completed in {metrics.total_time:.2f}s")
        print(f"  |-- Throughput: {metrics.throughput:.2f} ops/sec")
        print(
            f"  |-- Latency: avg={metrics.avg_time*1000:.2f}ms, "
            f"p95={metrics.p95_time*1000:.2f}ms, "
            f"p99={metrics.p99_time*1000:.2f}ms"
        )
        print(
            f"  |-- Memory: start={metrics.memory_start_mb:.1f}MB, "
            f"peak={metrics.memory_peak_mb:.1f}MB, "
            f"leaked={metrics.memory_leaked_mb:.1f}MB"
        )
        print(f"  |-- CPU: avg={metrics.cpu_avg_percent:.1f}%")
        print(f"  +-- Success Rate: {metrics.success_rate:.1f}% ({metrics.error_count} errors)")

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary report"""
        return {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.results),
                "duration": sum(m.total_time for m in self.results),
            },
            "aggregates": {
                "total_operations": sum(m.total_operations for m in self.results),
                "total_errors": sum(m.error_count for m in self.results),
                "avg_throughput": statistics.mean([m.throughput for m in self.results]),
                "avg_memory_leaked": statistics.mean([m.memory_leaked_mb for m in self.results]),
                "avg_cpu": statistics.mean([m.cpu_avg_percent for m in self.results]),
                "overall_success_rate": statistics.mean([m.success_rate for m in self.results]),
            },
            "results": [
                {
                    "test_name": m.test_name,
                    "total_time": round(m.total_time, 3),
                    "throughput": round(m.throughput, 2),
                    "avg_latency_ms": round(m.avg_time * 1000, 2),
                    "p95_latency_ms": round(m.p95_time * 1000, 2),
                    "memory_leaked_mb": round(m.memory_leaked_mb, 2),
                    "success_rate": round(m.success_rate, 2),
                }
                for m in self.results
            ],
        }

    def _print_summary(self, summary: Dict[str, Any]):
        """Print summary report"""
        agg = summary["aggregates"]
        print(f"Total Tests: {summary['test_run']['total_tests']}")
        print(f"Total Duration: {summary['test_run']['duration']:.1f}s")
        print(f"Total Operations: {agg['total_operations']:,}")
        print(f"Total Errors: {agg['total_errors']}")
        print(f"\nAverage Metrics:")
        print(f"  Throughput: {agg['avg_throughput']:.2f} ops/sec")
        print(f"  Memory Leaked: {agg['avg_memory_leaked']:.2f} MB")
        print(f"  CPU Usage: {agg['avg_cpu']:.1f}%")
        print(f"  Success Rate: {agg['overall_success_rate']:.1f}%")

        print(f"\n{'='*70}")
        print("PERFORMANCE ASSESSMENT")
        print(f"{'='*70}\n")

        # Assess performance
        if agg["avg_throughput"] > 50:
            print("[OK] EXCELLENT: Throughput > 50 ops/sec")
        elif agg["avg_throughput"] > 20:
            print("[OK] GOOD: Throughput > 20 ops/sec")
        else:
            print("[WARN] WARNING: Throughput < 20 ops/sec")

        if agg["avg_memory_leaked"] < 10:
            print("[OK] EXCELLENT: Memory leak < 10 MB")
        elif agg["avg_memory_leaked"] < 50:
            print("[OK] ACCEPTABLE: Memory leak < 50 MB")
        else:
            print("[WARN] WARNING: Memory leak > 50 MB")

        if agg["overall_success_rate"] > 99:
            print("[OK] EXCELLENT: Success rate > 99%")
        elif agg["overall_success_rate"] > 95:
            print("[OK] GOOD: Success rate > 95%")
        else:
            print("[WARN] WARNING: Success rate < 95%")

        # Save results
        os.makedirs("../../reports", exist_ok=True)
        report_path = "../../reports/performance_test_results.json"
        with open(report_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\n[INFO] Full report saved to: {report_path}")


async def main():
    """Run load testing suite"""
    tester = PerformanceTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
