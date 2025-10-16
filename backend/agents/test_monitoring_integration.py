"""
Test Monitoring System Integration with Agent Framework
========================================================

Integration tests for agent monitoring with BaseAgent.

Tests:
1. Monitoring Integration - Agent execution tracking
2. Health Checks - Status monitoring
3. Prometheus Metrics - Export format
4. Monitoring Service - Multi-agent tracking

Created: 2025-10-08
"""

import logging
import sys
import time
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent / "framework"))

from framework.agent_monitoring import AgentMonitor, MonitoringService, HealthStatus
from adapters.registry_agent_adapter import RegistryAgentAdapter


def test_monitoring_integration():
    """Test monitoring integration with agent execution."""
    print("\n" + "=" * 80)
    print("TEST 1: MONITORING INTEGRATION")
    print("=" * 80)
    
    # Create agent with monitoring enabled
    agent = RegistryAgentAdapter(enable_monitoring=True)
    
    print(f"\n✓ Agent created: {agent.agent_id}")
    print(f"✓ Monitoring enabled: {agent.monitor is not None}")
    
    # Create test plan
    plan = {
        "plan_id": "test_monitoring_001",
        "query": "Test monitoring integration",
        "research_type": "exploratory",
        "steps": [
            {
                "step_id": "step_1",
                "step_number": 1,
                "agent_type": "registry",
                "action": "list_agents",
                "parameters": {},
                "expected_output": "List of registered agents"
            }
        ]
    }
    
    # Execute plan (this should record metrics)
    print(f"\nExecuting plan...")
    result = agent.execute_research_plan(plan)
    
    print(f"\n✓ Plan executed: {result['status']}")
    print(f"✓ Steps completed: {result['steps_completed']}/{result['total_steps']}")
    
    # Check monitoring metrics
    if agent.monitor:
        snapshot = agent.monitor.get_metrics_snapshot()
        exec_metrics = snapshot['execution_metrics']
        
        print(f"\n[Monitoring Metrics]")
        print(f"  Total Executions: {exec_metrics['total_executions']}")
        print(f"  Success Rate: {exec_metrics['success_rate']*100:.1f}%")
        print(f"  Average Quality: {exec_metrics['average_quality_score']:.2f}")
        print(f"  Average Duration: {exec_metrics['average_duration_seconds']:.3f}s")
        
        # Verify metrics were recorded
        assert exec_metrics['total_executions'] > 0, "No executions recorded!"
        print(f"\n✅ TEST 1 PASSED - Monitoring integration working")
    else:
        print(f"\n❌ TEST 1 FAILED - Monitoring not enabled")
        return False
    
    return True


def test_health_checks():
    """Test health check functionality."""
    print("\n" + "=" * 80)
    print("TEST 2: HEALTH CHECKS")
    print("=" * 80)
    
    # Create monitor
    monitor = AgentMonitor(
        agent_id="test_agent_health",
        agent_type="TestAgent"
    )
    
    # Initially should be healthy (no executions yet)
    health = monitor.get_health_status()
    print(f"\n[Initial Health Check]")
    print(f"  Status: {health.status.value}")
    print(f"  Message: {health.message}")
    
    # Simulate successful executions
    print(f"\n[Simulating 5 successful executions...]")
    for i in range(5):
        monitor.record_step_execution(
            step_id=f"step_{i+1}",
            duration=0.1 + i * 0.02,
            status="success",
            quality_score=0.85 + i * 0.02
        )
        time.sleep(0.01)
    
    health = monitor.get_health_status()
    print(f"\nAfter successful executions:")
    print(f"  Status: {health.status.value}")
    print(f"  Checks:")
    for check_name, result in health.checks.items():
        icon = "✅" if result else "❌"
        print(f"    {icon} {check_name}")
    
    assert health.status == HealthStatus.HEALTHY, f"Expected HEALTHY, got {health.status}"
    print(f"\n✅ Healthy status verified")
    
    # Simulate failures
    print(f"\n[Simulating 3 failures...]")
    for i in range(3):
        monitor.record_step_execution(
            step_id=f"failed_{i+1}",
            duration=0.5,
            status="failed",
            quality_score=0.3,
            retry_count=2
        )
    
    health = monitor.get_health_status()
    print(f"\nAfter failures:")
    print(f"  Status: {health.status.value}")
    print(f"  Consecutive Failures: {monitor.consecutive_failures}")
    
    assert health.status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY], \
        f"Expected DEGRADED/UNHEALTHY, got {health.status}"
    print(f"\n✅ Degraded status verified after failures")
    
    print(f"\n✅ TEST 2 PASSED - Health checks working")
    return True


def test_prometheus_metrics():
    """Test Prometheus metrics export."""
    print("\n" + "=" * 80)
    print("TEST 3: PROMETHEUS METRICS")
    print("=" * 80)
    
    # Create monitor and record some data
    monitor = AgentMonitor(
        agent_id="prom_test_agent",
        agent_type="PrometheusTest"
    )
    
    # Record executions
    for i in range(3):
        monitor.record_step_execution(
            step_id=f"step_{i+1}",
            duration=0.15,
            status="success" if i < 2 else "failed",
            quality_score=0.9 if i < 2 else 0.4
        )
    
    # Get Prometheus metrics
    metrics = monitor.get_prometheus_metrics()
    
    print(f"\n[Prometheus Metrics Export]")
    print(metrics)
    
    # Verify required metrics present
    required_metrics = [
        "agent_executions_total",
        "agent_execution_duration_seconds",
        "agent_quality_score",
        "agent_retries_total",
        "agent_health_status"
    ]
    
    for metric in required_metrics:
        assert metric in metrics, f"Missing required metric: {metric}"
        print(f"  ✓ {metric}")
    
    # Verify format
    assert "# HELP" in metrics, "Missing HELP comments"
    assert "# TYPE" in metrics, "Missing TYPE comments"
    assert 'agent_id="prom_test_agent"' in metrics, "Missing agent_id label"
    
    print(f"\n✅ TEST 3 PASSED - Prometheus export working")
    return True


def test_monitoring_service():
    """Test monitoring service with multiple agents."""
    print("\n" + "=" * 80)
    print("TEST 4: MONITORING SERVICE")
    print("=" * 80)
    
    # Create service
    service = MonitoringService()
    
    # Register agents
    print(f"\n[Registering Agents]")
    monitor1 = service.register_agent("agent_001", "RegistryAgent")
    monitor2 = service.register_agent("agent_002", "EnvironmentalAgent")
    monitor3 = service.register_agent("agent_003", "SocialAgent")
    
    print(f"  ✓ Registered 3 agents")
    
    # Simulate executions
    print(f"\n[Simulating Executions]")
    monitor1.record_step_execution("step_1", 0.1, "success", 0.95)
    monitor1.record_step_execution("step_2", 0.12, "success", 0.92)
    monitor2.record_step_execution("step_3", 0.15, "success", 0.88)
    monitor2.record_step_execution("step_4", 0.2, "failed", 0.4)
    monitor3.record_step_execution("step_5", 0.18, "success", 0.90)
    
    print(f"  ✓ Recorded 5 executions")
    
    # Get system metrics
    print(f"\n[System Metrics]")
    system_metrics = service.get_system_metrics()
    
    print(f"  Total Agents: {system_metrics['total_agents']}")
    print(f"  Total Executions: {system_metrics['execution_metrics']['total_executions']}")
    print(f"  System Success Rate: {system_metrics['execution_metrics']['success_rate']*100:.1f}%")
    print(f"  System Avg Quality: {system_metrics['execution_metrics']['average_quality_score']:.2f}")
    
    assert system_metrics['total_agents'] == 3
    assert system_metrics['execution_metrics']['total_executions'] == 5
    assert system_metrics['execution_metrics']['successful_executions'] == 4
    assert system_metrics['execution_metrics']['failed_executions'] == 1
    
    # Health summary
    print(f"\n[Health Summary]")
    health_summary = system_metrics['health_summary']
    print(f"  Healthy: {health_summary['healthy']}")
    print(f"  Degraded: {health_summary['degraded']}")
    print(f"  Unhealthy: {health_summary['unhealthy']}")
    
    # Get all health status
    all_health = service.get_all_health_status()
    print(f"\n[Individual Agent Health]")
    for agent_id, health in all_health.items():
        print(f"  {agent_id}: {health.status.value}")
    
    print(f"\n✅ TEST 4 PASSED - Monitoring service working")
    return True


def run_all_tests():
    """Run all monitoring integration tests."""
    print("\n" + "=" * 80)
    print("AGENT MONITORING INTEGRATION TESTS")
    print("=" * 80)
    
    results = []
    
    try:
        # Test 1: Monitoring Integration
        results.append(("Monitoring Integration", test_monitoring_integration()))
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        results.append(("Monitoring Integration", False))
    
    try:
        # Test 2: Health Checks
        results.append(("Health Checks", test_health_checks()))
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        results.append(("Health Checks", False))
    
    try:
        # Test 3: Prometheus Metrics
        results.append(("Prometheus Metrics", test_prometheus_metrics()))
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        results.append(("Prometheus Metrics", False))
    
    try:
        # Test 4: Monitoring Service
        results.append(("Monitoring Service", test_monitoring_service()))
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        results.append(("Monitoring Service", False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        icon = "✅" if passed else "❌"
        print(f"{icon} {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nResults: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.0f}%)")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return True
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
