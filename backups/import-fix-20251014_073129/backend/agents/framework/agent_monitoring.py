"""
VERITAS Agent Framework - Agent Monitoring System
=================================================

Prometheus-compatible metrics and health checks for agent monitoring.

Features:
- Prometheus metrics export
- Health check endpoints
- Execution tracking
- Performance metrics
- Agent status monitoring

Usage:
    from agent_monitoring import AgentMonitor, HealthStatus
    
    # Create monitor
    monitor = AgentMonitor(agent_id="my_agent")
    
    # Record metrics
    monitor.record_step_execution(
        step_id="step_1",
        duration=0.123,
        status="success",
        quality_score=0.95
    )
    
    # Check health
    health = monitor.get_health_status()
    print(f"Status: {health.status}")

Created: 2025-10-08
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional
from threading import Lock


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Agent health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Metric types for Prometheus export."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class HealthCheck:
    """
    Health check result.
    
    Attributes:
        status: Overall health status
        checks: Individual check results
        message: Status message
        timestamp: Check timestamp
        metrics: Current metrics snapshot
    """
    status: HealthStatus
    checks: Dict[str, bool]
    message: str
    timestamp: str
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionMetrics:
    """
    Execution metrics for an agent.
    
    Attributes:
        total_executions: Total number of executions
        successful_executions: Number of successful executions
        failed_executions: Number of failed executions
        total_duration: Total execution time (seconds)
        average_duration: Average execution time (seconds)
        quality_scores: List of quality scores
        average_quality: Average quality score
        retry_count: Total retry attempts
        last_execution: Last execution timestamp
    """
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration: float = 0.0
    average_duration: float = 0.0
    quality_scores: List[float] = field(default_factory=list)
    average_quality: float = 0.0
    retry_count: int = 0
    last_execution: Optional[str] = None
    
    def update(self, duration: float, status: str, quality: float, retries: int = 0):
        """Update metrics with new execution."""
        self.total_executions += 1
        self.total_duration += duration
        self.average_duration = self.total_duration / self.total_executions
        
        if status == "success":
            self.successful_executions += 1
        else:
            self.failed_executions += 1
        
        self.quality_scores.append(quality)
        self.average_quality = sum(self.quality_scores) / len(self.quality_scores)
        
        self.retry_count += retries
        self.last_execution = datetime.utcnow().isoformat()


class AgentMonitor:
    """
    Monitoring system for VERITAS agents.
    
    Tracks execution metrics, health status, and provides
    Prometheus-compatible metric export.
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str = "unknown",
        health_check_interval: int = 60
    ):
        """
        Initialize agent monitor.
        
        Args:
            agent_id: Agent identifier
            agent_type: Type of agent
            health_check_interval: Health check interval in seconds
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.health_check_interval = health_check_interval
        
        # Metrics storage
        self.metrics = ExecutionMetrics()
        self.step_metrics: Dict[str, ExecutionMetrics] = defaultdict(ExecutionMetrics)
        
        # Health tracking
        self.last_health_check: Optional[datetime] = None
        self.consecutive_failures = 0
        self.is_available = True
        
        # Thread safety
        self._lock = Lock()
        
        # Prometheus metrics (labels)
        self.labels = {
            "agent_id": agent_id,
            "agent_type": agent_type
        }
        
        logger.info(f"Initialized AgentMonitor for {agent_type}:{agent_id}")
    
    def record_step_execution(
        self,
        step_id: str,
        duration: float,
        status: str,
        quality_score: float,
        retry_count: int = 0
    ):
        """
        Record step execution metrics.
        
        Args:
            step_id: Step identifier
            duration: Execution duration in seconds
            status: Execution status (success/failed)
            quality_score: Quality score (0.0-1.0)
            retry_count: Number of retries
        """
        with self._lock:
            # Update global metrics
            self.metrics.update(duration, status, quality_score, retry_count)
            
            # Update step-specific metrics
            self.step_metrics[step_id].update(duration, status, quality_score, retry_count)
            
            # Update health tracking
            if status == "success":
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
            
            logger.debug(f"Recorded execution: step={step_id}, duration={duration:.3f}s, "
                        f"status={status}, quality={quality_score:.2f}")
    
    def record_plan_execution(
        self,
        plan_id: str,
        duration: float,
        status: str,
        steps_executed: int,
        steps_succeeded: int,
        average_quality: float
    ):
        """
        Record research plan execution metrics.
        
        Args:
            plan_id: Plan identifier
            duration: Total execution duration
            status: Plan status
            steps_executed: Number of steps executed
            steps_succeeded: Number of successful steps
            average_quality: Average quality score
        """
        with self._lock:
            logger.info(f"Plan execution recorded: {plan_id} - {status} - "
                       f"{steps_succeeded}/{steps_executed} steps - "
                       f"quality={average_quality:.2f} - duration={duration:.2f}s")
    
    def get_health_status(self) -> HealthCheck:
        """
        Get current health status.
        
        Returns:
            HealthCheck with current status
        """
        with self._lock:
            checks = {}
            
            # Check 1: Agent availability
            checks["agent_available"] = self.is_available
            
            # Check 2: Recent failures
            checks["low_failure_rate"] = self.consecutive_failures < 3
            
            # Check 3: Recent execution
            if self.metrics.last_execution:
                last_exec = datetime.fromisoformat(self.metrics.last_execution)
                time_since_last = datetime.utcnow() - last_exec
                checks["recently_executed"] = time_since_last < timedelta(minutes=10)
            else:
                checks["recently_executed"] = True  # No executions yet is OK
            
            # Check 4: Quality threshold
            if self.metrics.quality_scores:
                checks["quality_acceptable"] = self.metrics.average_quality >= 0.6
            else:
                checks["quality_acceptable"] = True
            
            # Determine overall status
            all_healthy = all(checks.values())
            some_unhealthy = any(not v for v in checks.values())
            
            if all_healthy:
                status = HealthStatus.HEALTHY
                message = "All health checks passed"
            elif self.consecutive_failures >= 5:
                status = HealthStatus.UNHEALTHY
                message = f"Agent unhealthy: {self.consecutive_failures} consecutive failures"
            elif some_unhealthy:
                status = HealthStatus.DEGRADED
                failed_checks = [k for k, v in checks.items() if not v]
                message = f"Some checks failed: {', '.join(failed_checks)}"
            else:
                status = HealthStatus.UNKNOWN
                message = "Health status unknown"
            
            self.last_health_check = datetime.utcnow()
            
            return HealthCheck(
                status=status,
                checks=checks,
                message=message,
                timestamp=datetime.utcnow().isoformat(),
                metrics={
                    "total_executions": self.metrics.total_executions,
                    "success_rate": self._calculate_success_rate(),
                    "average_quality": self.metrics.average_quality,
                    "consecutive_failures": self.consecutive_failures
                }
            )
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.metrics.total_executions == 0:
            return 1.0
        return self.metrics.successful_executions / self.metrics.total_executions
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.
        
        Returns:
            Dictionary with all current metrics
        """
        with self._lock:
            return {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "timestamp": datetime.utcnow().isoformat(),
                "execution_metrics": {
                    "total_executions": self.metrics.total_executions,
                    "successful_executions": self.metrics.successful_executions,
                    "failed_executions": self.metrics.failed_executions,
                    "success_rate": self._calculate_success_rate(),
                    "average_duration_seconds": self.metrics.average_duration,
                    "average_quality_score": self.metrics.average_quality,
                    "total_retries": self.metrics.retry_count,
                    "last_execution": self.metrics.last_execution
                },
                "health": {
                    "consecutive_failures": self.consecutive_failures,
                    "is_available": self.is_available,
                    "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None
                },
                "step_count": len(self.step_metrics)
            }
    
    def get_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus format.
        
        Returns:
            Metrics in Prometheus text format
        """
        with self._lock:
            metrics_lines = []
            
            # Agent execution counter
            metrics_lines.append("# HELP agent_executions_total Total number of agent executions")
            metrics_lines.append("# TYPE agent_executions_total counter")
            metrics_lines.append(
                f'agent_executions_total{{agent_id="{self.agent_id}",agent_type="{self.agent_type}",status="success"}} '
                f'{self.metrics.successful_executions}'
            )
            metrics_lines.append(
                f'agent_executions_total{{agent_id="{self.agent_id}",agent_type="{self.agent_type}",status="failed"}} '
                f'{self.metrics.failed_executions}'
            )
            
            # Average duration gauge
            metrics_lines.append("# HELP agent_execution_duration_seconds Average execution duration")
            metrics_lines.append("# TYPE agent_execution_duration_seconds gauge")
            metrics_lines.append(
                f'agent_execution_duration_seconds{{agent_id="{self.agent_id}",agent_type="{self.agent_type}"}} '
                f'{self.metrics.average_duration:.6f}'
            )
            
            # Quality score gauge
            metrics_lines.append("# HELP agent_quality_score Average quality score")
            metrics_lines.append("# TYPE agent_quality_score gauge")
            metrics_lines.append(
                f'agent_quality_score{{agent_id="{self.agent_id}",agent_type="{self.agent_type}"}} '
                f'{self.metrics.average_quality:.6f}'
            )
            
            # Retry counter
            metrics_lines.append("# HELP agent_retries_total Total number of retries")
            metrics_lines.append("# TYPE agent_retries_total counter")
            metrics_lines.append(
                f'agent_retries_total{{agent_id="{self.agent_id}",agent_type="{self.agent_type}"}} '
                f'{self.metrics.retry_count}'
            )
            
            # Health status gauge (1=healthy, 0.5=degraded, 0=unhealthy)
            health = self.get_health_status()
            health_value = {
                HealthStatus.HEALTHY: 1.0,
                HealthStatus.DEGRADED: 0.5,
                HealthStatus.UNHEALTHY: 0.0,
                HealthStatus.UNKNOWN: 0.0
            }[health.status]
            
            metrics_lines.append("# HELP agent_health_status Agent health status (1=healthy, 0.5=degraded, 0=unhealthy)")
            metrics_lines.append("# TYPE agent_health_status gauge")
            metrics_lines.append(
                f'agent_health_status{{agent_id="{self.agent_id}",agent_type="{self.agent_type}"}} '
                f'{health_value}'
            )
            
            return "\n".join(metrics_lines) + "\n"
    
    def reset_metrics(self):
        """Reset all metrics (for testing/development)."""
        with self._lock:
            self.metrics = ExecutionMetrics()
            self.step_metrics.clear()
            self.consecutive_failures = 0
            logger.info(f"Reset metrics for agent {self.agent_id}")


class MonitoringService:
    """
    Central monitoring service for all agents.
    
    Aggregates metrics from multiple agents and provides
    system-wide monitoring capabilities.
    """
    
    def __init__(self):
        """Initialize monitoring service."""
        self.monitors: Dict[str, AgentMonitor] = {}
        self._lock = Lock()
        
        logger.info("Initialized MonitoringService")
    
    def register_agent(self, agent_id: str, agent_type: str) -> AgentMonitor:
        """
        Register an agent for monitoring.
        
        Args:
            agent_id: Agent identifier
            agent_type: Type of agent
        
        Returns:
            AgentMonitor instance
        """
        with self._lock:
            if agent_id in self.monitors:
                logger.warning(f"Agent {agent_id} already registered")
                return self.monitors[agent_id]
            
            monitor = AgentMonitor(agent_id, agent_type)
            self.monitors[agent_id] = monitor
            
            logger.info(f"Registered agent for monitoring: {agent_type}:{agent_id}")
            return monitor
    
    def get_monitor(self, agent_id: str) -> Optional[AgentMonitor]:
        """Get monitor for specific agent."""
        with self._lock:
            return self.monitors.get(agent_id)
    
    def get_all_health_status(self) -> Dict[str, HealthCheck]:
        """
        Get health status for all registered agents.
        
        Returns:
            Dictionary mapping agent_id to HealthCheck
        """
        with self._lock:
            return {
                agent_id: monitor.get_health_status()
                for agent_id, monitor in self.monitors.items()
            }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get aggregated system-wide metrics.
        
        Returns:
            Dictionary with system metrics
        """
        with self._lock:
            total_executions = sum(m.metrics.total_executions for m in self.monitors.values())
            total_successes = sum(m.metrics.successful_executions for m in self.monitors.values())
            total_failures = sum(m.metrics.failed_executions for m in self.monitors.values())
            
            # Calculate system-wide averages
            if self.monitors:
                avg_quality = sum(m.metrics.average_quality for m in self.monitors.values()) / len(self.monitors)
                avg_duration = sum(m.metrics.average_duration for m in self.monitors.values()) / len(self.monitors)
            else:
                avg_quality = 0.0
                avg_duration = 0.0
            
            # Count agent health statuses
            health_counts = {status: 0 for status in HealthStatus}
            for monitor in self.monitors.values():
                health = monitor.get_health_status()
                health_counts[health.status] += 1
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "total_agents": len(self.monitors),
                "execution_metrics": {
                    "total_executions": total_executions,
                    "successful_executions": total_successes,
                    "failed_executions": total_failures,
                    "success_rate": total_successes / total_executions if total_executions > 0 else 1.0,
                    "average_quality_score": avg_quality,
                    "average_duration_seconds": avg_duration
                },
                "health_summary": {
                    "healthy": health_counts[HealthStatus.HEALTHY],
                    "degraded": health_counts[HealthStatus.DEGRADED],
                    "unhealthy": health_counts[HealthStatus.UNHEALTHY],
                    "unknown": health_counts[HealthStatus.UNKNOWN]
                }
            }
    
    def get_all_prometheus_metrics(self) -> str:
        """
        Export metrics for all agents in Prometheus format.
        
        Returns:
            Aggregated Prometheus metrics
        """
        with self._lock:
            metrics_parts = []
            
            for agent_id, monitor in self.monitors.items():
                metrics_parts.append(f"# Agent: {agent_id}")
                metrics_parts.append(monitor.get_prometheus_metrics())
            
            return "\n".join(metrics_parts)


# ========================================
# Example Usage & Tests
# ========================================

def _test_agent_monitoring():
    """Test agent monitoring system."""
    print("=" * 80)
    print("AGENT MONITORING SYSTEM TEST")
    print("=" * 80)
    
    # Create monitor
    monitor = AgentMonitor(
        agent_id="test_agent_001",
        agent_type="TestAgent"
    )
    
    print(f"\n[TEST 1] Record Executions")
    print("-" * 40)
    
    # Simulate successful executions
    for i in range(5):
        monitor.record_step_execution(
            step_id=f"step_{i+1}",
            duration=0.1 + i * 0.05,
            status="success",
            quality_score=0.85 + i * 0.02,
            retry_count=0
        )
        time.sleep(0.01)
    
    # Simulate one failure
    monitor.record_step_execution(
        step_id="step_6",
        duration=0.5,
        status="failed",
        quality_score=0.3,
        retry_count=2
    )
    
    print(f"  Recorded 6 executions (5 success, 1 failed)")
    
    # Get metrics
    print(f"\n[TEST 2] Metrics Snapshot")
    print("-" * 40)
    snapshot = monitor.get_metrics_snapshot()
    exec_metrics = snapshot['execution_metrics']
    
    print(f"  Total Executions: {exec_metrics['total_executions']}")
    print(f"  Success Rate: {exec_metrics['success_rate']*100:.1f}%")
    print(f"  Average Quality: {exec_metrics['average_quality_score']:.2f}")
    print(f"  Average Duration: {exec_metrics['average_duration_seconds']:.3f}s")
    print(f"  Total Retries: {exec_metrics['total_retries']}")
    
    # Health check
    print(f"\n[TEST 3] Health Check")
    print("-" * 40)
    health = monitor.get_health_status()
    
    print(f"  Status: {health.status.value}")
    print(f"  Message: {health.message}")
    print(f"  Checks:")
    for check_name, result in health.checks.items():
        status_icon = "✅" if result else "❌"
        print(f"    {status_icon} {check_name}")
    
    # Prometheus metrics
    print(f"\n[TEST 4] Prometheus Export")
    print("-" * 40)
    prometheus_metrics = monitor.get_prometheus_metrics()
    print(prometheus_metrics)
    
    print("=" * 80)
    print("✅ ALL MONITORING TESTS COMPLETED")
    print("=" * 80)


def _test_monitoring_service():
    """Test monitoring service."""
    print("\n" + "=" * 80)
    print("MONITORING SERVICE TEST")
    print("=" * 80)
    
    service = MonitoringService()
    
    # Register agents
    print(f"\n[TEST 1] Register Agents")
    print("-" * 40)
    
    monitor1 = service.register_agent("agent_001", "RegistryAgent")
    monitor2 = service.register_agent("agent_002", "EnvironmentalAgent")
    
    print(f"  Registered 2 agents")
    
    # Simulate executions
    print(f"\n[TEST 2] Simulate Executions")
    print("-" * 40)
    
    monitor1.record_step_execution("step_1", 0.1, "success", 0.95)
    monitor1.record_step_execution("step_2", 0.15, "success", 0.90)
    monitor2.record_step_execution("step_3", 0.2, "success", 0.85)
    
    print(f"  Recorded 3 executions")
    
    # System metrics
    print(f"\n[TEST 3] System Metrics")
    print("-" * 40)
    
    system_metrics = service.get_system_metrics()
    print(f"  Total Agents: {system_metrics['total_agents']}")
    print(f"  Total Executions: {system_metrics['execution_metrics']['total_executions']}")
    print(f"  System Success Rate: {system_metrics['execution_metrics']['success_rate']*100:.1f}%")
    print(f"  System Avg Quality: {system_metrics['execution_metrics']['average_quality_score']:.2f}")
    
    # Health summary
    print(f"\n[TEST 4] Health Summary")
    print("-" * 40)
    health_summary = system_metrics['health_summary']
    print(f"  Healthy: {health_summary['healthy']}")
    print(f"  Degraded: {health_summary['degraded']}")
    print(f"  Unhealthy: {health_summary['unhealthy']}")
    
    print("\n" + "=" * 80)
    print("✅ MONITORING SERVICE TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    _test_agent_monitoring()
    _test_monitoring_service()
