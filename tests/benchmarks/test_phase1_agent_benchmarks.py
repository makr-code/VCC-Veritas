#!/usr/bin/env python3
"""
Performance Benchmarks for Phase 1 Agents - BaseAgent Framework v2.0

Comprehensive benchmarking covering:
- Query execution time (single + concurrent)
- Memory usage (baseline + under load)
- Throughput (queries per second)
- Registry lookup performance
- Comparison with legacy agents
- Async overhead analysis

Author: VERITAS Framework Migration v2.0
Date: 2025-12-04
"""

import asyncio
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import psutil
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.agents.domain.construction.genehmigung_agent import GenehmigungAgent
    from backend.agents.domain.weather.dwd_weather_agent_v3_framework import DwdWeatherAgent

    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="Agents not available")


# ===== BENCHMARK UTILITIES =====


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""

    name: str
    agent_type: str
    metric: str
    value: float
    unit: str
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class BenchmarkRunner:
    """Execute and track benchmarks."""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process(os.getpid())

    def record(self, name: str, agent_type: str, metric: str, value: float, unit: str):
        """Record benchmark result."""
        result = BenchmarkResult(name, agent_type, metric, value, unit)
        self.results.append(result)
        print(f"  ✓ {agent_type:20} | {metric:25} | {value:10.4f} {unit}")

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            return self.process.memory_info().rss / 1024 / 1024
        except:
            return 0.0

    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "=" * 100)
        print("BENCHMARK SUMMARY")
        print("=" * 100)

        # Group by agent
        by_agent = {}
        for result in self.results:
            if result.agent_type not in by_agent:
                by_agent[result.agent_type] = []
            by_agent[result.agent_type].append(result)

        for agent_type, results in by_agent.items():
            print(f"\n{agent_type}:")
            for result in results:
                print(f"  {result.metric:30} | {result.value:10.4f} {result.unit}")


# ===== SINGLE QUERY BENCHMARKS =====


@pytest.mark.benchmark
@pytest.mark.asyncio
class TestGenehmigungAgentBenchmarks:
    """Benchmark GenehmigungAgent performance."""

    @pytest.fixture
    def agent(self):
        """Create agent for benchmarking."""
        return GenehmigungAgent(agent_id="bench_genehmigung")

    @pytest.fixture
    def runner(self):
        """Create benchmark runner."""
        return BenchmarkRunner()

    async def test_single_query_execution_time(self, agent, runner):
        """Benchmark single query execution time."""
        query = "Wie läuft ein Genehmigungsverfahren ab?"

        start = time.perf_counter()
        result = await agent.process_query(query)
        elapsed = time.perf_counter() - start

        runner.record("Single Query", "GenehmigungAgent", "Execution Time", elapsed * 1000, "ms")
        assert result is not None

    async def test_query_with_legacy_interface(self, agent, runner):
        """Benchmark legacy query() method."""
        query = "Beteiligungsrechte im Verfahren?"

        start = time.perf_counter()
        result = agent.query(query)
        elapsed = time.perf_counter() - start

        runner.record("Legacy Query", "GenehmigungAgent", "Execution Time", elapsed * 1000, "ms")
        assert result is not None

    async def test_knowledge_base_search(self, agent, runner):
        """Benchmark knowledge base search."""
        start = time.perf_counter()
        results = agent.search_genehmigung("genehmigungsverfahren")
        elapsed = time.perf_counter() - start

        runner.record("KB Search", "GenehmigungAgent", "Search Time", elapsed * 1000, "ms")
        assert isinstance(results, list)

    async def test_concurrent_queries_10(self, agent, runner):
        """Benchmark 10 concurrent queries."""
        queries = [f"Frage {i}: Genehmigungsverfahren" for i in range(10)]

        start = time.perf_counter()
        tasks = [agent.process_query(q) for q in queries]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        throughput = len(queries) / elapsed
        runner.record("Concurrent (10)", "GenehmigungAgent", "Throughput", throughput, "queries/sec")
        runner.record("Concurrent (10)", "GenehmigungAgent", "Total Time", elapsed * 1000, "ms")
        assert len(results) == 10

    async def test_concurrent_queries_50(self, agent, runner):
        """Benchmark 50 concurrent queries."""
        queries = [f"Frage {i}: Verwaltungsverfahren" for i in range(50)]

        start = time.perf_counter()
        tasks = [agent.process_query(q) for q in queries]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        throughput = len(queries) / elapsed
        runner.record("Concurrent (50)", "GenehmigungAgent", "Throughput", throughput, "queries/sec")
        runner.record("Concurrent (50)", "GenehmigungAgent", "Total Time", elapsed * 1000, "ms")
        assert len(results) == 50

    async def test_memory_baseline(self, agent, runner):
        """Benchmark memory usage at baseline."""
        memory_start = runner.get_memory_usage()

        # Warm up
        for _ in range(3):
            await agent.process_query("Test query")

        memory_end = runner.get_memory_usage()
        memory_delta = memory_end - memory_start

        runner.record("Memory", "GenehmigungAgent", "Usage Increase", memory_delta, "MB")


@pytest.mark.benchmark
@pytest.mark.asyncio
class TestDwdWeatherAgentBenchmarks:
    """Benchmark DwdWeatherAgent performance."""

    @pytest.fixture
    def agent(self):
        """Create agent for benchmarking."""
        return DwdWeatherAgent(agent_id="bench_weather")

    @pytest.fixture
    def runner(self):
        """Create benchmark runner."""
        return BenchmarkRunner()

    async def test_single_weather_query(self, agent, runner):
        """Benchmark single weather query."""
        query = "Wetter in Köln"

        start = time.perf_counter()
        result = await agent.process_query(query)
        elapsed = time.perf_counter() - start

        runner.record("Single Query", "DwdWeatherAgent", "Execution Time", elapsed * 1000, "ms")
        assert result is not None

    async def test_multiple_location_queries(self, agent, runner):
        """Benchmark queries for multiple locations."""
        locations = ["Köln", "Berlin", "Hamburg", "München", "Frankfurt"]

        start = time.perf_counter()
        tasks = [agent.process_query(f"Wetter in {loc}") for loc in locations]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        runner.record("Multi-Location", "DwdWeatherAgent", "Total Time", elapsed * 1000, "ms")
        runner.record("Multi-Location", "DwdWeatherAgent", "Avg Per Query", (elapsed / len(locations)) * 1000, "ms")
        assert len(results) == 5

    async def test_concurrent_weather_queries_10(self, agent, runner):
        """Benchmark 10 concurrent weather queries."""
        queries = [f"Wetter in Stadt {i}" for i in range(10)]

        start = time.perf_counter()
        tasks = [agent.process_query(q) for q in queries]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        throughput = len(queries) / elapsed
        runner.record("Concurrent (10)", "DwdWeatherAgent", "Throughput", throughput, "queries/sec")
        runner.record("Concurrent (10)", "DwdWeatherAgent", "Total Time", elapsed * 1000, "ms")
        assert len(results) == 10

    async def test_concurrent_weather_queries_30(self, agent, runner):
        """Benchmark 30 concurrent weather queries."""
        queries = [f"Temperatur Stadt {i}" for i in range(30)]

        start = time.perf_counter()
        tasks = [agent.process_query(q) for q in queries]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        throughput = len(queries) / elapsed
        runner.record("Concurrent (30)", "DwdWeatherAgent", "Throughput", throughput, "queries/sec")
        runner.record("Concurrent (30)", "DwdWeatherAgent", "Total Time", elapsed * 1000, "ms")
        assert len(results) == 30

    async def test_pooled_lifecycle_efficiency(self, agent, runner):
        """Benchmark pooled lifecycle efficiency."""
        # Test that pooled instances handle load efficiently
        queries = [f"Wetter Query {i}" for i in range(100)]

        start = time.perf_counter()
        tasks = [agent.process_query(q) for q in queries]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        throughput = len(queries) / elapsed
        runner.record("Pooled (100)", "DwdWeatherAgent", "Throughput", throughput, "queries/sec")
        assert len(results) == 100

    async def test_memory_baseline(self, agent, runner):
        """Benchmark memory usage at baseline."""
        memory_start = runner.get_memory_usage()

        # Warm up
        for _ in range(5):
            await agent.process_query("Test query")

        memory_end = runner.get_memory_usage()
        memory_delta = memory_end - memory_start

        runner.record("Memory", "DwdWeatherAgent", "Usage Increase", memory_delta, "MB")


# ===== COMPARATIVE BENCHMARKS =====


@pytest.mark.benchmark
@pytest.mark.asyncio
class TestComparativeBenchmarks:
    """Compare agent performance."""

    async def test_both_agents_single_query(self):
        """Compare single query execution time."""
        genehmigung = GenehmigungAgent(agent_id="comp_genehmigung")
        weather = DwdWeatherAgent(agent_id="comp_weather")

        # Genehmigung query
        start = time.perf_counter()
        r1 = await genehmigung.process_query("Genehmigungsverfahren?")
        time_genehmigung = (time.perf_counter() - start) * 1000

        # Weather query
        start = time.perf_counter()
        r2 = await weather.process_query("Wetter in Köln")
        time_weather = (time.perf_counter() - start) * 1000

        print(f"\nSingle Query Comparison:")
        print(f"  GenehmigungAgent: {time_genehmigung:.2f}ms")
        print(f"  DwdWeatherAgent:  {time_weather:.2f}ms")
        print(f"  Difference:       {abs(time_genehmigung - time_weather):.2f}ms")

    async def test_both_agents_concurrent_load(self):
        """Compare concurrent load handling."""
        genehmigung = GenehmigungAgent(agent_id="comp_genehmigung")
        weather = DwdWeatherAgent(agent_id="comp_weather")

        num_queries = 20

        # Genehmigung concurrent
        start = time.perf_counter()
        tasks = [genehmigung.process_query(f"Frage {i}") for i in range(num_queries)]
        await asyncio.gather(*tasks)
        time_genehmigung = time.perf_counter() - start

        # Weather concurrent
        start = time.perf_counter()
        tasks = [weather.process_query(f"Wetter {i}") for i in range(num_queries)]
        await asyncio.gather(*tasks)
        time_weather = time.perf_counter() - start

        throughput_genehmigung = num_queries / time_genehmigung
        throughput_weather = num_queries / time_weather

        print(f"\nConcurrent Queries ({num_queries}):")
        print(f"  GenehmigungAgent: {throughput_genehmigung:.2f} queries/sec")
        print(f"  DwdWeatherAgent:  {throughput_weather:.2f} queries/sec")


# ===== PROFILING HELPERS =====


def print_benchmark_report(results: List[BenchmarkResult]):
    """Print comprehensive benchmark report."""
    print("\n" + "=" * 100)
    print("BENCHMARK REPORT")
    print("=" * 100)

    # Group by metric
    by_metric = {}
    for result in results:
        key = f"{result.agent_type}:{result.metric}"
        if key not in by_metric:
            by_metric[key] = []
        by_metric[key].append(result)

    for key, values in sorted(by_metric.items()):
        avg = sum(v.value for v in values) / len(values)
        print(f"{key:50} | Avg: {avg:10.4f} {values[0].unit}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "benchmark", "--tb=short"])
