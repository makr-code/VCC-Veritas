"""
Performance Monitoring für Phase 5 Advanced RAG Pipeline

Provides comprehensive performance tracking for:
- Hybrid Search (Dense + Sparse + RRF)
- Query Expansion (LLM-based)
- End-to-End Pipeline Latency
- Component-level Metrics

Metrics Collected:
    - Latency (P50, P95, P99)
    - Retrieval Statistics (Dense vs Sparse vs Hybrid)
    - Fusion Statistics (RRF overlap, source distribution)
    - Query Expansion (LLM latency, variant generation)
    - Error Rates
    - Cache Hit Rates

Usage:
    from backend.monitoring.phase5_monitoring import Phase5Monitor

    monitor = Phase5Monitor()

    with monitor.track_hybrid_retrieval(query):
        results = hybrid_retriever.retrieve(query)

    monitor.log_stats()
"""

import logging
import statistics
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LatencyStats:
    """Latency statistics for a component."""

    samples: List[float] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.samples)

    @property
    def avg(self) -> float:
        return statistics.mean(self.samples) if self.samples else 0.0

    @property
    def median(self) -> float:
        return statistics.median(self.samples) if self.samples else 0.0

    @property
    def p95(self) -> float:
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.95)
        return sorted_samples[idx]

    @property
    def p99(self) -> float:
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.99)
        return sorted_samples[idx]

    @property
    def min(self) -> float:
        return min(self.samples) if self.samples else 0.0

    @property
    def max(self) -> float:
        return max(self.samples) if self.samples else 0.0

    def add_sample(self, latency_ms: float):
        """Add a latency sample."""
        self.samples.append(latency_ms)

        # Keep only last 1000 samples to avoid memory growth
        if len(self.samples) > 1000:
            self.samples = self.samples[-1000:]


@dataclass
class ComponentMetrics:
    """Metrics for a Phase 5 component."""

    latency: LatencyStats = field(default_factory=LatencyStats)
    success_count: int = 0
    error_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.error_count
        return self.success_count / total if total > 0 else 0.0

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


class Phase5Monitor:
    """Performance monitor for Phase 5 components.

    Thread-safe monitoring with component-level tracking.
    """

    def __init__(self):
        """Initialize monitor."""
        self.components: Dict[str, ComponentMetrics] = defaultdict(ComponentMetrics)
        self.fusion_stats: List[Dict[str, Any]] = []
        self.query_expansion_stats: List[Dict[str, Any]] = []

    @contextmanager
    def track_component(self, component_name: str):
        """Track component execution time.

        Args:
            component_name: Name of component (e.g., 'sparse_retrieval', 'rr')

        Yields:
            ComponentMetrics for the component

        Example:
            with monitor.track_component('sparse_retrieval'):
                results = sparse_retriever.retrieve(query)
        """
        start_time = time.time()
        metrics = self.components[component_name]

        try:
            yield metrics
            metrics.success_count += 1
        except Exception as e:
            metrics.error_count += 1
            logger.error(f"Error in {component_name}: {e}")
            raise
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            metrics.latency.add_sample(elapsed_ms)

            logger.debug(f"Phase5.{component_name}: {elapsed_ms:.2f}ms " f"(success_rate={metrics.success_rate:.2%})")

    @contextmanager
    def track_hybrid_retrieval(self, query: str):
        """Track full hybrid retrieval pipeline.

        Args:
            query: The search query

        Example:
            with monitor.track_hybrid_retrieval("DIN 18040-1"):
                results = hybrid_retriever.retrieve(query)
        """
        with self.track_component("hybrid_retrieval") as metrics:
            logger.info(f"Phase5.HybridRetrieval: query='{query}'")
            yield metrics

    @contextmanager
    def track_query_expansion(self, query: str, strategy: str):
        """Track query expansion execution.

        Args:
            query: Original query
            strategy: Expansion strategy used

        Example:
            with monitor.track_query_expansion(query, "multi_perspective"):
                variants = query_expander.expand(query)
        """
        with self.track_component("query_expansion") as metrics:
            logger.info(f"Phase5.QueryExpansion: query='{query}', strategy={strategy}")
            yield metrics

    def record_fusion_stats(self, stats: Dict[str, Any]):
        """Record RRF fusion statistics.

        Args:
            stats: Fusion stats from RRF (overlap_rate, source_distribution, etc.)
        """
        self.fusion_stats.append(stats)

        # Keep only last 100
        if len(self.fusion_stats) > 100:
            self.fusion_stats = self.fusion_stats[-100:]

        logger.debug(f"Phase5.RRF: fusion_stats={stats}")

    def record_query_expansion_variants(self, original: str, variants: List[str]):
        """Record query expansion variants.

        Args:
            original: Original query
            variants: Generated variants
        """
        self.query_expansion_stats.append(
            {
                "original": original,
                "variant_count": len(variants),
                "variants": variants,
            }
        )

        # Keep only last 100
        if len(self.query_expansion_stats) > 100:
            self.query_expansion_stats = self.query_expansion_stats[-100:]

        logger.info(f"Phase5.QueryExpansion: generated {len(variants)} variants for '{original}'")

    def record_cache_hit(self, component_name: str):
        """Record cache hit."""
        self.components[component_name].cache_hits += 1

    def record_cache_miss(self, component_name: str):
        """Record cache miss."""
        self.components[component_name].cache_misses += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics.

        Returns:
            Dictionary with all metrics
        """
        stats = {
            "components": {},
            "fusion": {},
            "query_expansion": {},
        }

        # Component stats
        for name, metrics in self.components.items():
            if metrics.latency.count > 0:
                stats["components"][name] = {
                    "latency_ms": {
                        "avg": round(metrics.latency.avg, 2),
                        "median": round(metrics.latency.median, 2),
                        "p95": round(metrics.latency.p95, 2),
                        "p99": round(metrics.latency.p99, 2),
                        "min": round(metrics.latency.min, 2),
                        "max": round(metrics.latency.max, 2),
                    },
                    "count": metrics.latency.count,
                    "success_rate": round(metrics.success_rate, 4),
                    "error_count": metrics.error_count,
                    "cache_hit_rate": round(metrics.cache_hit_rate, 4),
                }

        # Fusion stats
        if self.fusion_stats:
            avg_overlap = statistics.mean([s.get("overlap_rate", 0.0) for s in self.fusion_stats])
            stats["fusion"] = {
                "avg_overlap_rate": round(avg_overlap, 4),
                "sample_count": len(self.fusion_stats),
            }

        # Query expansion stats
        if self.query_expansion_stats:
            avg_variants = statistics.mean([s["variant_count"] for s in self.query_expansion_stats])
            stats["query_expansion"] = {
                "avg_variants": round(avg_variants, 2),
                "sample_count": len(self.query_expansion_stats),
            }

        return stats

    def log_stats(self, level: str = "INFO"):
        """Log current statistics.

        Args:
            level: Log level (INFO, DEBUG, WARNING)
        """
        stats = self.get_stats()

        log_func = getattr(logger, level.lower(), logger.info)

        log_func("=" * 80)
        log_func("PHASE 5 PERFORMANCE STATISTICS")
        log_func("=" * 80)

        # Component stats
        if stats["components"]:
            log_func("\nComponent Latencies:")
            for name, component_stats in stats["components"].items():
                latency = component_stats["latency_ms"]
                log_func(
                    f"  {name:.<30} "
                    f"Avg: {latency['avg']:>6.2f}ms  "
                    f"P95: {latency['p95']:>6.2f}ms  "
                    f"P99: {latency['p99']:>6.2f}ms  "
                    f"Count: {component_stats['count']:>5}  "
                    f"Success: {component_stats['success_rate']:.2%}"
                )

                if component_stats["cache_hit_rate"] > 0:
                    log_func(f"  {' ':.<30} " f"Cache Hit Rate: {component_stats['cache_hit_rate']:.2%}")

        # Fusion stats
        if stats["fusion"]:
            log_func("\nRRF Fusion:")
            log_func(f"  Avg Overlap Rate: {stats['fusion']['avg_overlap_rate']:.2%}")

        # Query expansion stats
        if stats["query_expansion"]:
            log_func("\nQuery Expansion:")
            log_func(f"  Avg Variants: {stats['query_expansion']['avg_variants']:.1f}")

        log_func("=" * 80)

    def reset_stats(self):
        """Reset all statistics."""
        self.components.clear()
        self.fusion_stats.clear()
        self.query_expansion_stats.clear()
        logger.info("Phase5 monitor stats reset")


# Global monitor instance
_global_monitor: Optional[Phase5Monitor] = None


def get_monitor() -> Phase5Monitor:
    """Get global Phase5Monitor instance.

    Returns:
        Phase5Monitor singleton
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = Phase5Monitor()
    return _global_monitor


def reset_monitor():
    """Reset global monitor."""
    global _global_monitor
    if _global_monitor is not None:
        _global_monitor.reset_stats()


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    monitor = get_monitor()

    # Simulate hybrid retrieval
    with monitor.track_hybrid_retrieval("DIN 18040-1"):
        time.sleep(0.05)  # Simulate 50ms

    # Simulate query expansion
    with monitor.track_query_expansion("§ 242 BGB", "multi_perspective"):
        time.sleep(0.5)  # Simulate 500ms LLM call

    monitor.record_query_expansion_variants("§ 242 BGB", ["Treu und Glauben BGB", "§ 242 Allgemeiner Teil"])

    # Simulate cache hit
    monitor.record_cache_hit("sparse_retrieval")

    # Log stats
    monitor.log_stats()
