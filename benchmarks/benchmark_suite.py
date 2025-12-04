"""
VERITAS Benchmark Suite - Comprehensive Performance & Quality Comparison Framework

This module provides benchmarking capabilities to compare VERITAS against:
- Commercial RAG systems (LangChain, LlamaIndex)
- LLM clients (OpenAI, Claude, Ollama)
- Content validation systems
- Administrative law specialized systems
"""

import json
import time
import statistics
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Callable
from datetime import datetime
from pathlib import Path
import sys
from enum import Enum

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class BenchmarkCategory(Enum):
    """Benchmark categories for system comparison"""
    RETRIEVAL = "retrieval"           # Vector/keyword search speed and accuracy
    INFERENCE = "inference"            # LLM generation speed and quality
    STREAMING = "streaming"            # SSE and real-time event performance
    CONTENT_QUALITY = "content_quality"  # Citation, legal ref, accuracy validation
    MULTI_TURN = "multi_turn"          # Multi-turn conversation coherence
    END_TO_END = "end_to_end"          # Complete pipeline performance
    ADMINISTRATIVE_LAW = "admin_law"   # Domain-specific legal accuracy


class BenchmarkMetric(Enum):
    """Standard metrics for comparison"""
    LATENCY_MS = "latency_ms"          # Response time in milliseconds
    THROUGHPUT = "throughput"          # Requests per second
    ACCURACY = "accuracy"              # Factual accuracy percentage
    PRECISION = "precision"            # Precision of results
    RECALL = "recall"                  # Recall of results
    F1_SCORE = "f1_score"             # F1 score (harmonic mean)
    CITATION_QUALITY = "citation_quality"  # IEEE citation compliance
    LEGAL_REF_ACCURACY = "legal_ref_accuracy"  # Legal reference accuracy
    CONTEXT_PRESERVATION = "context_preservation"  # Multi-turn coherence
    COHERENCE_SCORE = "coherence_score"  # Answer coherence
    MEMORY_MB = "memory_mb"            # Memory usage in MB
    CPU_PERCENT = "cpu_percent"        # CPU utilization percentage


@dataclass
class BenchmarkResult:
    """Single benchmark result"""
    timestamp: str
    category: str
    metric: str
    value: float
    unit: str
    system: str
    test_name: str
    status: str = "pass"  # pass, fail, error
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = self.timestamp
        return data


@dataclass
class BenchmarkSuite:
    """Container for benchmark results"""
    timestamp: str
    system_name: str
    system_version: str
    python_version: str
    hardware_info: Dict[str, Any]
    results: List[BenchmarkResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "system_name": self.system_name,
            "system_version": self.system_version,
            "python_version": self.python_version,
            "hardware_info": self.hardware_info,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary
        }


class BenchmarkRunner:
    """Execute and track benchmarks"""

    def __init__(self, system_name: str, system_version: str):
        """Initialize benchmark runner"""
        self.system_name = system_name
        self.system_version = system_version
        self.results: List[BenchmarkResult] = []
        self.start_time = datetime.now()
        self._get_hardware_info()

    def _get_hardware_info(self) -> Dict[str, Any]:
        """Collect hardware information"""
        import platform
        try:
            import psutil
            cpu_count = psutil.cpu_count()
            ram_gb = psutil.virtual_memory().total / (1024**3)
        except ImportError:
            cpu_count = "unknown"
            ram_gb = "unknown"

        return {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_cores": cpu_count,
            "ram_gb": ram_gb,
            "python_version": platform.python_version()
        }

    def run_benchmark(
        self,
        test_func: Callable,
        test_name: str,
        category: BenchmarkCategory,
        metric: BenchmarkMetric,
        iterations: int = 10,
        unit: str = "ms"
    ) -> Dict[str, Any]:
        """
        Run a benchmark test

        Args:
            test_func: Callable that returns the metric value
            test_name: Name of the benchmark
            category: Category of benchmark
            metric: Metric being measured
            iterations: Number of iterations to run
            unit: Unit of measurement

        Returns:
            Dictionary with statistics
        """
        times = []
        values = []
        errors = []

        for i in range(iterations):
            try:
                start = time.time()
                result = test_func()
                elapsed = (time.time() - start) * 1000  # Convert to ms

                times.append(elapsed)
                if isinstance(result, (int, float)):
                    values.append(result)

            except Exception as e:
                errors.append(str(e))

        # Calculate statistics
        if times:
            stats = {
                "count": len(times),
                "mean_ms": statistics.mean(times),
                "median_ms": statistics.median(times),
                "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
                "min_ms": min(times),
                "max_ms": max(times),
                "p95_ms": self._percentile(times, 0.95),
                "p99_ms": self._percentile(times, 0.99),
            }
        else:
            stats = {}

        # Add result
        result = BenchmarkResult(
            timestamp=datetime.now().isoformat(),
            category=category.value,
            metric=metric.value,
            value=stats.get("mean_ms", 0),
            unit=unit,
            system=self.system_name,
            test_name=test_name,
            status="error" if errors else "pass",
            error_message="; ".join(errors) if errors else "",
            metadata={
                "iterations": iterations,
                "statistics": stats,
                "values": values if values else times
            }
        )

        self.results.append(result)
        return stats

    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def record_metric(
        self,
        metric_value: float,
        test_name: str,
        category: BenchmarkCategory,
        metric: BenchmarkMetric,
        unit: str = "",
        metadata: Dict[str, Any] = None
    ) -> None:
        """Record a single metric value"""
        result = BenchmarkResult(
            timestamp=datetime.now().isoformat(),
            category=category.value,
            metric=metric.value,
            value=metric_value,
            unit=unit,
            system=self.system_name,
            test_name=test_name,
            metadata=metadata or {}
        )
        self.results.append(result)

    def get_suite(self) -> BenchmarkSuite:
        """Get completed benchmark suite"""
        # Generate summary
        summary = self._generate_summary()

        return BenchmarkSuite(
            timestamp=self.start_time.isoformat(),
            system_name=self.system_name,
            system_version=self.system_version,
            python_version=self._get_hardware_info()["python_version"],
            hardware_info=self._get_hardware_info(),
            results=self.results,
            summary=summary
        )

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        if not self.results:
            return {}

        by_category = {}
        by_metric = {}

        for result in self.results:
            # By category
            if result.category not in by_category:
                by_category[result.category] = []
            by_category[result.category].append(result.value)

            # By metric
            if result.metric not in by_metric:
                by_metric[result.metric] = []
            by_metric[result.metric].append(result.value)

        summary = {
            "total_benchmarks": len(self.results),
            "total_passed": sum(1 for r in self.results if r.status == "pass"),
            "total_failed": sum(1 for r in self.results if r.status == "fail"),
            "total_errors": sum(1 for r in self.results if r.status == "error"),
            "by_category": {
                cat: {
                    "count": len(vals),
                    "mean": statistics.mean(vals),
                    "median": statistics.median(vals),
                    "min": min(vals),
                    "max": max(vals)
                }
                for cat, vals in by_category.items()
            },
            "by_metric": {
                metric: {
                    "count": len(vals),
                    "mean": statistics.mean(vals),
                    "median": statistics.median(vals),
                    "min": min(vals),
                    "max": max(vals)
                }
                for metric, vals in by_metric.items()
            }
        }

        return summary

    def save_results(self, filepath: str) -> None:
        """Save benchmark results to JSON"""
        suite = self.get_suite()
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(suite.to_dict(), f, indent=2, default=str)

        print(f"Benchmark results saved to {filepath}")


class CompetitiveBenchmark:
    """Compare VERITAS against competing systems"""

    def __init__(self):
        """Initialize competitive benchmark"""
        self.systems: Dict[str, BenchmarkSuite] = {}

    def add_system(self, suite: BenchmarkSuite) -> None:
        """Add system benchmark results"""
        self.systems[suite.system_name] = suite

    def compare_metric(self, metric: str) -> Dict[str, Any]:
        """Compare a specific metric across systems"""
        comparison = {
            "metric": metric,
            "timestamp": datetime.now().isoformat(),
            "systems": {}
        }

        for system_name, suite in self.systems.items():
            # Find all results for this metric
            metric_results = [
                r for r in suite.results
                if r.metric == metric
            ]

            if metric_results:
                values = [r.value for r in metric_results]
                comparison["systems"][system_name] = {
                    "count": len(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "unit": metric_results[0].unit
                }

        return comparison

    def compare_category(self, category: str) -> Dict[str, Any]:
        """Compare a specific category across systems"""
        comparison = {
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "systems": {}
        }

        for system_name, suite in self.systems.items():
            # Find all results for this category
            category_results = [
                r for r in suite.results
                if r.category == category
            ]

            if category_results:
                comparison["systems"][system_name] = {
                    "test_count": len(category_results),
                    "pass_count": sum(1 for r in category_results if r.status == "pass"),
                    "fail_count": sum(1 for r in category_results if r.status == "fail"),
                    "error_count": sum(1 for r in category_results if r.status == "error"),
                    "metrics": {}
                }

                # Group by metric
                by_metric = {}
                for r in category_results:
                    if r.metric not in by_metric:
                        by_metric[r.metric] = []
                    by_metric[r.metric].append(r.value)

                for metric, values in by_metric.items():
                    comparison["systems"][system_name]["metrics"][metric] = {
                        "mean": statistics.mean(values),
                        "min": min(values),
                        "max": max(values)
                    }

        return comparison

    def generate_comparison_report(self) -> str:
        """Generate text comparison report"""
        if not self.systems:
            return "No systems to compare"

        report = "=" * 80 + "\n"
        report += "BENCHMARK COMPARISON REPORT\n"
        report += "=" * 80 + "\n\n"

        # System overview
        report += "SYSTEM OVERVIEW\n"
        report += "-" * 80 + "\n"
        for system_name, suite in self.systems.items():
            report += f"\n{system_name} v{suite.system_version}\n"
            report += f"  Benchmarks: {suite.summary.get('total_benchmarks', 0)}\n"
            report += f"  Passed: {suite.summary.get('total_passed', 0)}\n"
            report += f"  Failed: {suite.summary.get('total_failed', 0)}\n"
            report += f"  Errors: {suite.summary.get('total_errors', 0)}\n"

        # Category comparison
        report += "\n" + "=" * 80 + "\n"
        report += "CATEGORY COMPARISON\n"
        report += "=" * 80 + "\n"

        categories = set()
        for suite in self.systems.values():
            categories.update(r.category for r in suite.results)

        for category in sorted(categories):
            comparison = self.compare_category(category)
            report += f"\n{category.upper()}\n"
            report += "-" * 80 + "\n"

            if comparison["systems"]:
                # Find best and worst for each metric
                metrics = {}
                for system_name, data in comparison["systems"].items():
                    for metric, stats in data.get("metrics", {}).items():
                        if metric not in metrics:
                            metrics[metric] = []
                        metrics[metric].append((system_name, stats["mean"]))

                for metric, values in metrics.items():
                    if values:
                        best_system = min(values, key=lambda x: x[1])
                        worst_system = max(values, key=lambda x: x[1])
                        improvement = (worst_system[1] - best_system[1]) / worst_system[1] * 100

                        report += f"\n  {metric}:\n"
                        for system_name, system_data in comparison["systems"].items():
                            metric_data = system_data.get("metrics", {}).get(metric, {})
                            mean = metric_data.get("mean", 0)
                            marker = " ⭐" if (system_name, mean) == best_system else ""
                            report += f"    {system_name}: {mean:.2f}{marker}\n"
                        report += f"    Improvement: {improvement:.1f}%\n"

        return report

    def save_comparison(self, filepath: str) -> None:
        """Save comparison results to JSON"""
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "systems": {}
        }

        for system_name, suite in self.systems.items():
            comparison["systems"][system_name] = suite.to_dict()

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)

        print(f"Comparison saved to {filepath}")


if __name__ == "__main__":
    # Example usage
    print("VERITAS Benchmark Suite")
    print("=" * 80)

    runner = BenchmarkRunner("VERITAS", "3.0.0")

    # Example benchmark
    def example_test():
        time.sleep(0.01)  # Simulate work
        return True

    stats = runner.run_benchmark(
        example_test,
        "test_example",
        BenchmarkCategory.RETRIEVAL,
        BenchmarkMetric.LATENCY_MS,
        iterations=5
    )

    print(f"Example benchmark stats: {stats}")

    # Save results
    results_path = Path(__file__).parent.parent / "benchmark_results.json"
    runner.save_results(str(results_path))
