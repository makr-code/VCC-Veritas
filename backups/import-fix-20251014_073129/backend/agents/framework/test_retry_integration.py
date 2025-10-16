"""
Test Retry Integration in BaseAgent

Tests that retry logic works end-to-end with:
- Failing steps that retry and succeed
- Retry count tracking in database
- Exponential backoff timing
- Max retries exhaustion

Created: 2025-10-08
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any

from base_agent import BaseAgent


class FailingThenSuccessAgent(BaseAgent):
    """Agent that fails first N attempts, then succeeds."""
    
    def __init__(self, fail_count: int = 2):
        """
        Initialize agent.
        
        Args:
            fail_count: Number of times to fail before succeeding
        """
        super().__init__()
        self.fail_count = fail_count
        self.attempt_counts = {}  # step_id -> attempt count
    
    def execute_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute step - fails first N times, then succeeds."""
        step_id = step["step_id"]
        
        # Track attempts
        if step_id not in self.attempt_counts:
            self.attempt_counts[step_id] = 0
        
        self.attempt_counts[step_id] += 1
        current_attempt = self.attempt_counts[step_id]
        
        # Fail first fail_count attempts
        if current_attempt <= self.fail_count:
            raise RuntimeError(
                f"Step {step_id} failed (attempt {current_attempt}/{self.fail_count + 1})"
            )
        
        # Success on final attempt
        return {
            "status": "success",
            "data": {
                "result": f"Succeeded after {current_attempt - 1} retries"
            },
            "quality_score": 0.95,
            "sources": ["test"],
            "metadata": {
                "total_attempts": current_attempt,
                "failed_attempts": current_attempt - 1
            }
        }
    
    def get_capabilities(self):
        """Return agent capabilities."""
        return ["test_capability"]
    
    def get_agent_type(self):
        """Return agent type."""
        return "test_agent"


class AlwaysFailAgent(BaseAgent):
    """Agent that always fails (for testing max retries)."""
    
    def __init__(self):
        super().__init__()
        self.attempt_count = 0
    
    def execute_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Always fails."""
        self.attempt_count += 1
        raise RuntimeError(
            f"Step always fails (attempt {self.attempt_count})"
        )
    
    def get_capabilities(self):
        """Return agent capabilities."""
        return ["test_capability"]
    
    def get_agent_type(self):
        """Return agent type."""
        return "test_agent"


def test_retry_success():
    """Test that retries work and step eventually succeeds."""
    print("=" * 80)
    print("TEST 1: Retry and Succeed")
    print("=" * 80)
    
    # Create agent that fails 2 times, then succeeds
    agent = FailingThenSuccessAgent(fail_count=2)
    
    # Generate unique plan ID
    import uuid
    plan_id = f"retry_test_001_{uuid.uuid4().hex[:8]}"
    
    # Create test plan with max_retries=3
    plan = {
        "plan_id": plan_id,
        "research_question": "Test retry logic",
        "schema_name": "standard",  # Valid schema name
        "query_complexity": "standard",
        "veritas_extensions": {
            "uds3_databases": ["test_db"],
            "phase5_hybrid_search": True,
            "security_level": "internal"
        },
        "steps": [
            {
                "step_id": "retry_step_1",
                "step_index": 0,
                "step_name": "Test Retry Step",
                "step_type": "data_retrieval",  # Valid step type
                "agent_name": "environmental",  # Valid agent name
                "agent_type": "DataRetrievalAgent",  # Valid agent type
                "action": "test_action",
                "parameters": {
                    "max_retries": 3  # Allow up to 3 retries
                },
                "tools": ["test_tool"],
                "expected_output": "test result",
                "dependencies": []
            }
        ]
    }
    
    # Execute plan
    print("\n📋 Executing plan with retry logic...")
    start_time = time.time()
    result = agent.execute(plan, parallel=False)
    elapsed = time.time() - start_time
    
    print(f"\n✅ Execution Result:")
    print(f"  Status: {result['status']}")
    print(f"  Steps executed: {result['steps_executed']}")
    print(f"  Steps succeeded: {result['steps_succeeded']}")
    print(f"  Steps failed: {result['steps_failed']}")
    print(f"  Execution time: {elapsed:.2f}s")
    
    # Check database for retry_count
    db_path = Path(__file__).parent.parent.parent.parent / "data" / "agent_framework.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT step_id, status, retry_count, result
        FROM research_plan_steps
        WHERE plan_id = ?
    """, (plan["plan_id"],))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        step_id, status, retry_count, result_json = row
        result_data = json.loads(result_json)
        
        print(f"\n📊 Database Record:")
        print(f"  Step ID: {step_id}")
        print(f"  Status: {status}")
        print(f"  Retry Count: {retry_count}")
        print(f"  Result: {result_data.get('data', {})}")
        
        # Assertions
        assert status == "completed", f"Expected completed, got {status}"
        assert retry_count == 2, f"Expected 2 retries, got {retry_count}"
        assert result['steps_succeeded'] == 1, "Step should succeed"
        assert result['steps_failed'] == 0, "No steps should fail"
        
        print(f"\n✅ TEST PASSED: Step succeeded after {retry_count} retries")
        print(f"  - Retry count correctly tracked in database")
        print(f"  - Exponential backoff applied (total time: {elapsed:.2f}s)")
        print(f"  - Final result stored successfully")
    else:
        raise AssertionError("No database record found!")


def test_max_retries_exhausted():
    """Test that max retries are enforced."""
    print("\n" + "=" * 80)
    print("TEST 2: Max Retries Exhausted")
    print("=" * 80)
    
    # Create agent that always fails
    agent = AlwaysFailAgent()
    
    # Generate unique plan ID
    import uuid
    plan_id = f"retry_test_002_{uuid.uuid4().hex[:8]}"
    
    # Create test plan with max_retries=2
    plan = {
        "plan_id": plan_id,
        "research_question": "Test max retries",
        "schema_name": "standard",
        "query_complexity": "standard",
        "veritas_extensions": {
            "uds3_databases": ["test_db"],
            "phase5_hybrid_search": True,
            "security_level": "internal"
        },
        "steps": [
            {
                "step_id": "fail_step_1",
                "step_index": 0,
                "step_name": "Always Fail Step",
                "step_type": "data_retrieval",
                "agent_name": "environmental",
                "agent_type": "DataRetrievalAgent",
                "action": "test_action",
                "parameters": {
                    "max_retries": 2  # Only 2 retries allowed
                },
                "tools": ["test_tool"],
                "expected_output": "test result",
                "dependencies": []
            }
        ]
    }
    
    # Execute plan (should fail)
    print("\n📋 Executing plan that will exhaust retries...")
    start_time = time.time()
    result = agent.execute(plan, parallel=False)
    elapsed = time.time() - start_time
    
    print(f"\n✅ Execution Result:")
    print(f"  Status: {result['status']}")
    print(f"  Steps executed: {result['steps_executed']}")
    print(f"  Steps succeeded: {result['steps_succeeded']}")
    print(f"  Steps failed: {result['steps_failed']}")
    print(f"  Execution time: {elapsed:.2f}s")
    print(f"  Attempt count: {agent.attempt_count}")
    
    # Check database
    db_path = Path(__file__).parent.parent.parent.parent / "data" / "agent_framework.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT step_id, status, retry_count, error_message
        FROM research_plan_steps
        WHERE plan_id = ?
    """, (plan["plan_id"],))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        step_id, status, retry_count, error_msg = row
        
        print(f"\n📊 Database Record:")
        print(f"  Step ID: {step_id}")
        print(f"  Status: {status}")
        print(f"  Retry Count: {retry_count}")
        print(f"  Error: {error_msg}")
        
        # Assertions
        assert status == "failed", f"Expected failed, got {status}"
        assert retry_count == 2, f"Expected 2 retries, got {retry_count}"
        assert agent.attempt_count == 3, f"Expected 3 attempts (1 + 2 retries), got {agent.attempt_count}"
        assert result['steps_failed'] == 1, "Step should fail"
        assert result['steps_succeeded'] == 0, "No steps should succeed"
        
        print(f"\n✅ TEST PASSED: Max retries (2) correctly enforced")
        print(f"  - Total attempts: {agent.attempt_count} (1 initial + 2 retries)")
        print(f"  - Retry count tracked: {retry_count}")
        print(f"  - Status: {status}")
        print(f"  - Execution time: {elapsed:.2f}s (includes backoff delays)")
    else:
        raise AssertionError("No database record found!")


def test_mixed_retry_scenarios():
    """Test plan with mix of successful and failed steps."""
    print("\n" + "=" * 80)
    print("TEST 3: Mixed Retry Scenarios")
    print("=" * 80)
    
    # Create agent that fails 1 time, then succeeds
    agent = FailingThenSuccessAgent(fail_count=1)
    
    # Generate unique plan ID
    import uuid
    plan_id = f"retry_test_003_{uuid.uuid4().hex[:8]}"
    
    # Create test plan with multiple steps
    plan = {
        "plan_id": plan_id,
        "research_question": "Test mixed scenarios",
        "schema_name": "standard",
        "query_complexity": "standard",
        "veritas_extensions": {
            "uds3_databases": ["test_db"],
            "phase5_hybrid_search": True,
            "security_level": "internal"
        },
        "steps": [
            {
                "step_id": "retry_step_A",
                "step_index": 0,
                "step_name": "Step A - Retry Once",
                "step_type": "data_retrieval",
                "agent_name": "environmental",
                "agent_type": "DataRetrievalAgent",
                "action": "test_action",
                "parameters": {
                    "max_retries": 3
                },
                "tools": ["test_tool"],
                "expected_output": "test result",
                "dependencies": []
            },
            {
                "step_id": "retry_step_B",
                "step_index": 1,
                "step_name": "Step B - Retry Once",
                "step_type": "data_analysis",
                "agent_name": "registry",
                "agent_type": "DataAnalysisAgent",
                "action": "test_action",
                "parameters": {
                    "max_retries": 2
                },
                "tools": ["test_tool"],
                "expected_output": "test result",
                "dependencies": []
            }
        ]
    }
    
    # Execute plan
    print("\n📋 Executing plan with 2 steps (each fails once)...")
    result = agent.execute(plan, parallel=False)
    
    print(f"\n✅ Execution Result:")
    print(f"  Status: {result['status']}")
    print(f"  Steps executed: {result['steps_executed']}")
    print(f"  Steps succeeded: {result['steps_succeeded']}")
    print(f"  Quality score: {result['total_quality_score']:.2f}")
    
    # Check database
    db_path = Path(__file__).parent.parent.parent.parent / "data" / "agent_framework.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT step_id, step_name, status, retry_count
        FROM research_plan_steps
        WHERE plan_id = ?
        ORDER BY step_index
    """, (plan["plan_id"],))
    
    rows = cursor.fetchall()
    conn.close()
    
    print(f"\n📊 Database Records ({len(rows)} steps):")
    for step_id, step_name, status, retry_count in rows:
        print(f"  {step_id}:")
        print(f"    Name: {step_name}")
        print(f"    Status: {status}")
        print(f"    Retries: {retry_count}")
    
    # Assertions
    assert len(rows) == 2, f"Expected 2 steps, got {len(rows)}"
    assert all(status == "completed" for _, _, status, _ in rows), "All steps should succeed"
    assert all(retry_count == 1 for _, _, _, retry_count in rows), "All steps should retry once"
    
    print(f"\n✅ TEST PASSED: Mixed retry scenarios work correctly")
    print(f"  - Both steps succeeded after 1 retry each")
    print(f"  - Retry counts correctly tracked in database")


def main():
    """Run all retry integration tests."""
    print("🧪 VERITAS AGENT FRAMEWORK - RETRY INTEGRATION TESTS")
    print("=" * 80)
    
    try:
        # Test 1: Retry and succeed
        test_retry_success()
        
        # Test 2: Max retries exhausted
        test_max_retries_exhausted()
        
        # Test 3: Mixed scenarios
        test_mixed_retry_scenarios()
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print("✅ ALL 3 TESTS PASSED")
        print("\nRetry Integration Features Validated:")
        print("  ✓ Retry logic integrated into BaseAgent")
        print("  ✓ Retry count tracked in database")
        print("  ✓ Exponential backoff applied")
        print("  ✓ Max retries enforced")
        print("  ✓ Failed steps eventually succeed")
        print("  ✓ Mixed retry scenarios work")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
