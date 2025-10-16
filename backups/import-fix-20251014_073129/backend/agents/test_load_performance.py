"""
VERITAS Agent Framework - Phase 5.1: Load Testing & Performance Suite

Comprehensive load testing and performance benchmarking for production deployment.

Tests:
1. Concurrent Agent Execution (100+ simultaneous agents)
2. Memory Profiling & Leak Detection
3. Response Time Benchmarks  
4. Quality Gate Performance
5. Monitoring Overhead
6. Streaming Performance
7. Orchestration Controller Performance
8. Sustained Load Test

Author: VERITAS Development Team
Created: 2025-10-08
Phase: 5.1 - Production Deployment
"""

import asyncio
import time
import psutil
import tracemalloc
import statistics
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Framework imports
from framework.base_agent import BaseAgent
from framework.quality_gate import QualityGate, QualityPolicy, QualityDecision
from framework.agent_monitoring import MonitoringService, AgentMonitor
from framework.streaming_manager import StreamingManager
from framework.orchestration_controller import OrchestrationController


@dataclass
class PerformanceMetrics:
    """Performance test metrics"""
    test_name: str
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    p50_time: float
    p95_time: float
    p99_time: float
    throughput: float  # operations per second
    memory_start_mb: float
    memory_peak_mb: float
    memory_end_mb: float
    memory_leaked_mb: float
    cpu_avg_percent: float
    cpu_peak_percent: float
    success_rate: float
    error_count: int
    total_operations: int
    concurrent_operations: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'test_name': self.test_name,
            'total_time': round(self.total_time, 3),
            'avg_time': round(self.avg_time, 3),
            'min_time': round(self.min_time, 3),
            'max_time': round(self.max_time, 3),
            'p50_time': round(self.p50_time, 3),
            'p95_time': round(self.p95_time, 3),
            'p99_time': round(self.p99_time, 3),
            'throughput': round(self.throughput, 2),
            'memory_start_mb': round(self.memory_start_mb, 2),
            'memory_peak_mb': round(self.memory_peak_mb, 2),
            'memory_end_mb': round(self.memory_end_mb, 2),
            'memory_leaked_mb': round(self.memory_leaked_mb, 2),
            'cpu_avg_percent': round(self.cpu_avg_percent, 2),
            'cpu_peak_percent': round(self.cpu_peak_percent, 2),
            'success_rate': round(self.success_rate, 2),
            'error_count': self.error_count,
            'total_operations': self.total_operations,
            'concurrent_operations': self.concurrent_operations,
            'timestamp': self.timestamp
        }


class PerformanceTester:
    """Load testing and performance benchmarking system"""
    
    def __init__(self):
        self.results: List[PerformanceMetrics] = []
        self.process = psutil.Process()
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete load testing suite"""
        print("\n" + "="*70)
        print("VERITAS AGENT FRAMEWORK - LOAD TESTING & PERFORMANCE SUITE")
        print("="*70 + "\n")
        
        # Test 1: Concurrent Plan Execution
        print("Test 1: Concurrent Plan Execution (100 plans)")
        metrics1 = await self.test_concurrent_plans(num_plans=100)
        self.results.append(metrics1)
        self._print_metrics(metrics1)
        
        # Test 2: Stress Test (250 plans)
        print("\nTest 2: Stress Test (250 concurrent plans)")
        metrics2 = await self.test_concurrent_plans(num_plans=250)
        self.results.append(metrics2)
        self._print_metrics(metrics2)
        
        # Test 3: Memory Leak Detection
        print("\nTest 3: Memory Leak Detection (500 sequential operations)")
        metrics3 = await self.test_memory_leaks(iterations=500)
        self.results.append(metrics3)
        self._print_metrics(metrics3)
        
        # Test 4: WebSocket Streaming Performance
        print("\nTest 4: WebSocket Streaming Performance (1000 events)")
        metrics4 = await self.test_streaming_performance(num_events=1000)
        self.results.append(metrics4)
        self._print_metrics(metrics4)
        
        # Test 5: Quality Gate Performance
        print("\nTest 5: Quality Gate Performance (10,000 validations)")
        metrics5 = await self.test_quality_gate_performance(num_validations=10000)
        self.results.append(metrics5)
        self._print_metrics(metrics5)
        
        # Test 6: Orchestration Controller Performance
        print("\nTest 6: Orchestration Controller (100 plans with interventions)")
        metrics6 = await self.test_orchestration_performance(num_plans=100)
        self.results.append(metrics6)
        self._print_metrics(metrics6)
        
        # Test 7: Sustained Load Test
        print("\nTest 7: Sustained Load (50 plans/minute for 5 minutes)")
        metrics7 = await self.test_sustained_load(plans_per_minute=50, duration_minutes=5)
        self.results.append(metrics7)
        self._print_metrics(metrics7)
        
        # Generate summary report
        print("\n" + "="*70)
        print("PERFORMANCE TEST SUMMARY")
        print("="*70 + "\n")
        
        summary = self._generate_summary()
        self._print_summary(summary)
        
        return summary
    
    async def test_concurrent_plans(self, num_plans: int) -> PerformanceMetrics:
        """Test concurrent plan execution"""
        # Setup
        tracemalloc.start()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        cpu_samples = []
        
        # Create test agent
        agent = await self._create_test_agent()
        engine = OrchestrationEngine()
        
        # Create plans
        plans = []
        for i in range(num_plans):
            plan = ExecutionPlan(
                plan_id=f"load_test_{i}",
                goal=f"Load test plan {i}",
                agent_id=agent.agent_id
            )
            # Add 5 steps per plan
            for j in range(5):
                plan.add_step(ExecutionStep(
                    step_id=f"step_{i}_{j}",
                    description=f"Step {j} of plan {i}",
                    agent_id=agent.agent_id
                ))
            plans.append(plan)
        
        # Execute concurrently
        start_time = time.time()
        memory_peak = memory_start
        errors = 0
        execution_times = []
        
        async def execute_plan(plan: ExecutionPlan) -> Tuple[float, bool]:
            """Execute single plan and track time"""
            plan_start = time.time()
            try:
                await engine.execute_plan(plan, [agent])
                # Sample CPU during execution
                cpu_samples.append(self.process.cpu_percent())
                # Sample memory
                nonlocal memory_peak
                current_mem = self.process.memory_info().rss / 1024 / 1024
                memory_peak = max(memory_peak, current_mem)
                return time.time() - plan_start, True
            except Exception as e:
                return time.time() - plan_start, False
        
        # Run all plans concurrently
        results = await asyncio.gather(*[execute_plan(p) for p in plans])
        
        total_time = time.time() - start_time
        
        # Extract metrics
        execution_times = [r[0] for r in results]
        errors = sum(1 for r in results if not r[1])
        
        # Memory metrics
        memory_end = self.process.memory_info().rss / 1024 / 1024
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        memory_leaked = memory_end - memory_start
        
        # CPU metrics
        cpu_avg = statistics.mean(cpu_samples) if cpu_samples else 0
        cpu_peak = max(cpu_samples) if cpu_samples else 0
        
        # Calculate percentiles
        sorted_times = sorted(execution_times)
        p50 = sorted_times[len(sorted_times) // 2]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        return PerformanceMetrics(
            test_name=f"Concurrent Plans ({num_plans})",
            total_time=total_time,
            avg_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            p50_time=p50,
            p95_time=p95,
            p99_time=p99,
            throughput=num_plans / total_time,
            memory_start_mb=memory_start,
            memory_peak_mb=memory_peak,
            memory_end_mb=memory_end,
            memory_leaked_mb=memory_leaked,
            cpu_avg_percent=cpu_avg,
            cpu_peak_percent=cpu_peak,
            success_rate=(num_plans - errors) / num_plans * 100,
            error_count=errors,
            total_operations=num_plans * 5,  # 5 steps per plan
            concurrent_operations=num_plans
        )
    
    async def test_memory_leaks(self, iterations: int) -> PerformanceMetrics:
        """Test for memory leaks over many iterations"""
        tracemalloc.start()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        
        agent = await self._create_test_agent()
        engine = OrchestrationEngine()
        
        execution_times = []
        memory_samples = []
        cpu_samples = []
        errors = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            plan = ExecutionPlan(
                plan_id=f"mem_test_{i}",
                goal=f"Memory test {i}",
                agent_id=agent.agent_id
            )
            plan.add_step(ExecutionStep(
                step_id=f"step_{i}",
                description=f"Test step {i}",
                agent_id=agent.agent_id
            ))
            
            iter_start = time.time()
            try:
                await engine.execute_plan(plan, [agent])
                execution_times.append(time.time() - iter_start)
            except:
                errors += 1
            
            # Sample memory every 50 iterations
            if i % 50 == 0:
                memory_samples.append(self.process.memory_info().rss / 1024 / 1024)
                cpu_samples.append(self.process.cpu_percent())
        
        total_time = time.time() - start_time
        
        memory_end = self.process.memory_info().rss / 1024 / 1024
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        memory_peak = max(memory_samples) if memory_samples else memory_end
        memory_leaked = memory_end - memory_start
        
        sorted_times = sorted(execution_times)
        
        return PerformanceMetrics(
            test_name=f"Memory Leak Test ({iterations} iterations)",
            total_time=total_time,
            avg_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            p50_time=sorted_times[len(sorted_times) // 2],
            p95_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_time=sorted_times[int(len(sorted_times) * 0.99)],
            throughput=iterations / total_time,
            memory_start_mb=memory_start,
            memory_peak_mb=memory_peak,
            memory_end_mb=memory_end,
            memory_leaked_mb=memory_leaked,
            cpu_avg_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            cpu_peak_percent=max(cpu_samples) if cpu_samples else 0,
            success_rate=(iterations - errors) / iterations * 100,
            error_count=errors,
            total_operations=iterations,
            concurrent_operations=1
        )
    
    async def test_streaming_performance(self, num_events: int) -> PerformanceMetrics:
        """Test WebSocket streaming performance"""
        tracemalloc.start()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        
        streaming_manager = StreamingManager()
        
        # Register test clients
        num_clients = 10
        for i in range(num_clients):
            await streaming_manager.register_client(f"client_{i}")
        
        execution_times = []
        cpu_samples = []
        errors = 0
        
        start_time = time.time()
        memory_peak = memory_start
        
        # Send events
        for i in range(num_events):
            event_start = time.time()
            try:
                await streaming_manager.broadcast_event({
                    'type': 'test_event',
                    'data': f'Event {i}',
                    'timestamp': datetime.now().isoformat()
                })
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
            test_name=f"WebSocket Streaming ({num_events} events, {num_clients} clients)",
            total_time=total_time,
            avg_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            p50_time=sorted_times[len(sorted_times) // 2],
            p95_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_time=sorted_times[int(len(sorted_times) * 0.99)],
            throughput=num_events / total_time,
            memory_start_mb=memory_start,
            memory_peak_mb=memory_peak,
            memory_end_mb=memory_end,
            memory_leaked_mb=memory_end - memory_start,
            cpu_avg_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            cpu_peak_percent=max(cpu_samples) if cpu_samples else 0,
            success_rate=(num_events - errors) / num_events * 100,
            error_count=errors,
            total_operations=num_events * num_clients,  # Each event goes to all clients
            concurrent_operations=num_clients
        )
    
    async def test_quality_gate_performance(self, num_validations: int) -> PerformanceMetrics:
        """Test quality gate validation performance"""
        tracemalloc.start()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        
        policy = QualityPolicy(
            min_quality_score=0.7,
            target_quality_score=0.9,
            require_review_below=0.8
        )
        gate = QualityGate(policy)
        
        execution_times = []
        cpu_samples = []
        errors = 0
        
        start_time = time.time()
        memory_peak = memory_start
        
        for i in range(num_validations):
            validation_start = time.time()
            try:
                # Create test result (simple dict format)
                result_data = {
                    'agent_id': "test_agent",
                    'status': 'success',
                    'data': {'test': f'data_{i}'},
                    'quality_score': 0.75 + (i % 20) / 100  # Varies between 0.75-0.94
                }
                
                # Simulate validation
                quality_score = result_data['quality_score']
                decision = gate.validate(result_data)
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
            test_name=f"Quality Gate Validation ({num_validations} validations)",
            total_time=total_time,
            avg_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            p50_time=sorted_times[len(sorted_times) // 2],
            p95_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_time=sorted_times[int(len(sorted_times) * 0.99)],
            throughput=num_validations / total_time,
            memory_start_mb=memory_start,
            memory_peak_mb=memory_peak,
            memory_end_mb=memory_end,
            memory_leaked_mb=memory_end - memory_start,
            cpu_avg_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            cpu_peak_percent=max(cpu_samples) if cpu_samples else 0,
            success_rate=(num_validations - errors) / num_validations * 100,
            error_count=errors,
            total_operations=num_validations,
            concurrent_operations=1
        )
    
    async def test_orchestration_performance(self, num_plans: int) -> PerformanceMetrics:
        """Test orchestration controller performance with interventions"""
        tracemalloc.start()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        
        agent = await self._create_test_agent()
        engine = OrchestrationEngine()
        controller = OrchestrationController(engine)
        
        execution_times = []
        cpu_samples = []
        errors = 0
        
        start_time = time.time()
        memory_peak = memory_start
        
        async def execute_with_interventions(plan_id: str) -> Tuple[float, bool]:
            """Execute plan with pause/resume and interventions"""
            plan_start = time.time()
            try:
                plan = ExecutionPlan(
                    plan_id=plan_id,
                    goal=f"Orchestration test {plan_id}",
                    agent_id=agent.agent_id
                )
                for j in range(3):
                    plan.add_step(ExecutionStep(
                        step_id=f"step_{plan_id}_{j}",
                        description=f"Step {j}",
                        agent_id=agent.agent_id
                    ))
                
                # Register plan
                await controller.register_plan(plan, [agent])
                
                # Execute with intervention after first step
                execution_task = asyncio.create_task(
                    controller.execute_plan(plan.plan_id)
                )
                
                # Wait a bit then pause
                await asyncio.sleep(0.01)
                await controller.pause_plan(plan.plan_id, "test_user")
                
                # Add intervention (skip step)
                if len(plan.steps) > 1:
                    await controller.skip_step(
                        plan.plan_id,
                        plan.steps[1].step_id,
                        "test_user",
                        "Performance test skip"
                    )
                
                # Resume
                await controller.resume_plan(plan.plan_id, "test_user")
                
                # Wait for completion
                await execution_task
                
                # Sample resources
                nonlocal memory_peak
                cpu_samples.append(self.process.cpu_percent())
                current_mem = self.process.memory_info().rss / 1024 / 1024
                memory_peak = max(memory_peak, current_mem)
                
                return time.time() - plan_start, True
            except Exception as e:
                return time.time() - plan_start, False
        
        # Execute plans with limited concurrency (10 at a time)
        batch_size = 10
        for i in range(0, num_plans, batch_size):
            batch = [execute_with_interventions(f"orch_test_{j}") 
                    for j in range(i, min(i + batch_size, num_plans))]
            results = await asyncio.gather(*batch)
            
            for exec_time, success in results:
                execution_times.append(exec_time)
                if not success:
                    errors += 1
        
        total_time = time.time() - start_time
        
        memory_end = self.process.memory_info().rss / 1024 / 1024
        tracemalloc.stop()
        
        sorted_times = sorted(execution_times)
        
        return PerformanceMetrics(
            test_name=f"Orchestration Controller ({num_plans} plans with interventions)",
            total_time=total_time,
            avg_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            p50_time=sorted_times[len(sorted_times) // 2],
            p95_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_time=sorted_times[int(len(sorted_times) * 0.99)],
            throughput=num_plans / total_time,
            memory_start_mb=memory_start,
            memory_peak_mb=memory_peak,
            memory_end_mb=memory_end,
            memory_leaked_mb=memory_end - memory_start,
            cpu_avg_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            cpu_peak_percent=max(cpu_samples) if cpu_samples else 0,
            success_rate=(num_plans - errors) / num_plans * 100,
            error_count=errors,
            total_operations=num_plans * 3,  # 3 steps per plan
            concurrent_operations=batch_size
        )
    
    async def test_sustained_load(self, plans_per_minute: int, duration_minutes: int) -> PerformanceMetrics:
        """Test sustained load over time"""
        tracemalloc.start()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        
        agent = await self._create_test_agent()
        engine = OrchestrationEngine()
        
        execution_times = []
        memory_samples = [memory_start]
        cpu_samples = []
        errors = 0
        total_plans = 0
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        interval = 60.0 / plans_per_minute  # Seconds between plans
        
        print(f"  Running sustained load: {plans_per_minute} plans/min for {duration_minutes} minutes...")
        print(f"  Interval between plans: {interval:.2f}s")
        
        async def execute_plan_task(plan_id: str) -> Tuple[float, bool]:
            """Execute single plan"""
            plan_start = time.time()
            try:
                plan = ExecutionPlan(
                    plan_id=plan_id,
                    goal=f"Sustained load test {plan_id}",
                    agent_id=agent.agent_id
                )
                for j in range(3):
                    plan.add_step(ExecutionStep(
                        step_id=f"step_{plan_id}_{j}",
                        description=f"Step {j}",
                        agent_id=agent.agent_id
                    ))
                
                await engine.execute_plan(plan, [agent])
                return time.time() - plan_start, True
            except:
                return time.time() - plan_start, False
        
        # Run sustained load
        next_plan_time = start_time
        while time.time() < end_time:
            # Execute plan
            plan_id = f"sustained_{total_plans}"
            exec_time, success = await execute_plan_task(plan_id)
            execution_times.append(exec_time)
            if not success:
                errors += 1
            total_plans += 1
            
            # Sample resources every 30 seconds
            if total_plans % (plans_per_minute // 2) == 0:
                memory_samples.append(self.process.memory_info().rss / 1024 / 1024)
                cpu_samples.append(self.process.cpu_percent())
                elapsed = (time.time() - start_time) / 60
                print(f"  Progress: {elapsed:.1f}/{duration_minutes} min, "
                      f"Plans: {total_plans}, Errors: {errors}")
            
            # Wait until next plan time
            next_plan_time += interval
            wait_time = next_plan_time - time.time()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        total_time = time.time() - start_time
        
        memory_end = self.process.memory_info().rss / 1024 / 1024
        tracemalloc.stop()
        
        memory_peak = max(memory_samples)
        sorted_times = sorted(execution_times)
        
        return PerformanceMetrics(
            test_name=f"Sustained Load ({plans_per_minute} plans/min, {duration_minutes} min)",
            total_time=total_time,
            avg_time=statistics.mean(execution_times),
            min_time=min(execution_times),
            max_time=max(execution_times),
            p50_time=sorted_times[len(sorted_times) // 2],
            p95_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_time=sorted_times[int(len(sorted_times) * 0.99)],
            throughput=total_plans / total_time,
            memory_start_mb=memory_start,
            memory_peak_mb=memory_peak,
            memory_end_mb=memory_end,
            memory_leaked_mb=memory_end - memory_start,
            cpu_avg_percent=statistics.mean(cpu_samples) if cpu_samples else 0,
            cpu_peak_percent=max(cpu_samples) if cpu_samples else 0,
            success_rate=(total_plans - errors) / total_plans * 100,
            error_count=errors,
            total_operations=total_plans * 3,
            concurrent_operations=1
        )
    
    async def _create_test_agent(self) -> BaseAgent:
        """Create test agent for benchmarking"""
        
        # Create simple test agent subclass
        class LoadTestAgent(BaseAgent):
            def get_agent_type(self) -> str:
                return "load_test"
            
            def get_capabilities(self) -> List[str]:
                return ["data_retrieval", "analysis"]
            
            async def execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
                await asyncio.sleep(0.001)  # 1ms simulated work
                return {
                    'status': 'success',
                    'data': {'result': 'test_data'},
                    'quality_score': 0.85
                }
        
        return LoadTestAgent(agent_id="load_test_agent")
    
    def _print_metrics(self, metrics: PerformanceMetrics):
        """Print formatted metrics"""
        print(f"  ✓ Completed in {metrics.total_time:.2f}s")
        print(f"  ├─ Throughput: {metrics.throughput:.2f} ops/sec")
        print(f"  ├─ Latency: avg={metrics.avg_time*1000:.2f}ms, "
              f"p50={metrics.p50_time*1000:.2f}ms, "
              f"p95={metrics.p95_time*1000:.2f}ms, "
              f"p99={metrics.p99_time*1000:.2f}ms")
        print(f"  ├─ Memory: start={metrics.memory_start_mb:.1f}MB, "
              f"peak={metrics.memory_peak_mb:.1f}MB, "
              f"leaked={metrics.memory_leaked_mb:.1f}MB")
        print(f"  ├─ CPU: avg={metrics.cpu_avg_percent:.1f}%, peak={metrics.cpu_peak_percent:.1f}%")
        print(f"  └─ Success Rate: {metrics.success_rate:.1f}% ({metrics.error_count} errors)")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary report"""
        return {
            'test_run': {
                'timestamp': datetime.now().isoformat(),
                'total_tests': len(self.results),
                'duration': sum(m.total_time for m in self.results)
            },
            'results': [m.to_dict() for m in self.results],
            'aggregates': {
                'total_operations': sum(m.total_operations for m in self.results),
                'total_errors': sum(m.error_count for m in self.results),
                'avg_throughput': statistics.mean([m.throughput for m in self.results]),
                'avg_memory_leaked': statistics.mean([m.memory_leaked_mb for m in self.results]),
                'avg_cpu': statistics.mean([m.cpu_avg_percent for m in self.results]),
                'overall_success_rate': statistics.mean([m.success_rate for m in self.results])
            }
        }
    
    def _print_summary(self, summary: Dict[str, Any]):
        """Print summary report"""
        agg = summary['aggregates']
        print(f"Total Tests: {summary['test_run']['total_tests']}")
        print(f"Total Duration: {summary['test_run']['duration']:.1f}s")
        print(f"Total Operations: {agg['total_operations']:,}")
        print(f"Total Errors: {agg['total_errors']}")
        print(f"\nAverage Metrics:")
        print(f"  Throughput: {agg['avg_throughput']:.2f} ops/sec")
        print(f"  Memory Leaked: {agg['avg_memory_leaked']:.2f} MB")
        print(f"  CPU Usage: {agg['avg_cpu']:.1f}%")
        print(f"  Success Rate: {agg['overall_success_rate']:.1f}%")
        
        # Performance assessment
        print(f"\n{'='*70}")
        print("PERFORMANCE ASSESSMENT")
        print(f"{'='*70}\n")
        
        # Throughput assessment
        if agg['avg_throughput'] > 50:
            print("✅ EXCELLENT: Throughput > 50 ops/sec")
        elif agg['avg_throughput'] > 20:
            print("✓ GOOD: Throughput > 20 ops/sec")
        else:
            print("⚠ WARNING: Throughput < 20 ops/sec - optimization needed")
        
        # Memory assessment
        if agg['avg_memory_leaked'] < 10:
            print("✅ EXCELLENT: Memory leak < 10 MB")
        elif agg['avg_memory_leaked'] < 50:
            print("✓ ACCEPTABLE: Memory leak < 50 MB")
        else:
            print("⚠ WARNING: Memory leak > 50 MB - investigation needed")
        
        # Success rate assessment
        if agg['overall_success_rate'] > 99:
            print("✅ EXCELLENT: Success rate > 99%")
        elif agg['overall_success_rate'] > 95:
            print("✓ GOOD: Success rate > 95%")
        else:
            print("⚠ WARNING: Success rate < 95% - stability issues detected")
        
        # Save to file
        report_path = os.path.join('reports', 'performance_test_results.json')
        os.makedirs('reports', exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n📄 Full report saved to: {report_path}")


# Main execution
async def main():
    """Run load testing suite"""
    tester = PerformanceTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
