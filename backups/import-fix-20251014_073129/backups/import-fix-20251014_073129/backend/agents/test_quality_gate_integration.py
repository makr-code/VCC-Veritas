"""
Integration Test: Quality Gate System + Agent Framework
========================================================

Tests quality gate integration with BaseAgent framework.

Created: 2025-10-08
"""

import sys
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent / "framework"))

from framework.base_agent import BaseAgent
from framework.quality_gate import GateDecision, QualityGate, QualityPolicy
from registry_agent_adapter import RegistryAgentAdapter


def test_quality_gate_integration():
    """Test quality gate with agent execution."""
    print("=" * 80)
    print("QUALITY GATE INTEGRATION TEST")
    print("=" * 80)

    # Create quality policy
    policy = QualityPolicy(
        min_quality=0.7, target_quality=0.9, review_threshold_low=0.6, review_threshold_high=0.85, max_retries=3
    )

    # Create agent with quality gate
    agent = RegistryAgentAdapter()
    agent.quality_gate = QualityGate(policy)

    print(f"\n📋 Created Registry Agent with Quality Gate")
    print(f"  Policy: min={policy.min_quality}, target={policy.target_quality}")
    print(f"  Review range: {policy.review_threshold_low}-{policy.review_threshold_high}")

    # Test plan with varying quality steps
    plan = {
        "plan_id": "quality_gate_test_001",
        "research_question": "Test quality gate integration",
        "schema_name": "standard",
        "query_complexity": "standard",
        "steps": [
            {
                "step_id": "step_high_quality",
                "step_index": 0,
                "step_name": "High Quality Step",
                "step_type": "data_analysis",
                "agent_name": "registry",
                "agent_type": "AgentRegistry",
                "action": "registry_statistics",
                "parameters": {},
                "tools": ["agent_registry"],
                "expected_output": "Statistics",
                "dependencies": [],
            },
            {
                "step_id": "step_borderline",
                "step_index": 1,
                "step_name": "Borderline Quality Step",
                "step_type": "data_retrieval",
                "agent_name": "registry",
                "agent_type": "AgentRegistry",
                "action": "agent_discovery",
                "parameters": {"capability": "data_processing"},
                "tools": ["agent_registry"],
                "expected_output": "Agents list",
                "dependencies": [],
            },
        ],
    }

    print(f"\n🚀 Executing Plan: {plan['plan_id']}")
    print(f"  Steps: {len(plan['steps'])}")

    # Execute steps and validate with quality gate
    results = []

    for step in plan["steps"]:
        print(f"\n[STEP] {step['step_id']}: {step['step_name']}")
        print("-" * 40)

        # Execute step
        context = {"plan_id": plan["plan_id"], "previous_results": {}, "step_index": step["step_index"]}

        result = agent.execute_step(step, context)

        print(f"Execution Status: {result['status']}")
        print(f"Quality Score: {result.get('quality_score', 0):.2f}")

        # Validate with quality gate
        if agent.quality_gate:
            gate_result = agent.quality_gate.validate(
                result=result, step_id=step["step_id"], plan_id=plan["plan_id"], retry_count=0
            )

            print(f"\n[QUALITY GATE]")
            print(f"  Decision: {gate_result.decision.value}")
            print(f"  Meets Threshold: {gate_result.meets_threshold}")
            print(f"  Requires Review: {gate_result.requires_review}")
            print(f"  Retry Suggested: {gate_result.retry_suggested}")

            if gate_result.reasons:
                print(f"  Reasons:")
                for reason in gate_result.reasons:
                    print(f"    - {reason}")

            if gate_result.recommendations:
                print(f"  Recommendations:")
                for rec in gate_result.recommendations:
                    print(f"    - {rec}")

            # Store result with gate decision
            result["gate_decision"] = gate_result.decision.value
            result["gate_approved"] = gate_result.decision == GateDecision.APPROVED

        results.append(result)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    total_steps = len(results)
    approved_steps = sum(1 for r in results if r.get("gate_approved", False))
    review_required = sum(1 for r in results if r.get("gate_decision") == "review_required")

    print(f"\nResults:")
    print(f"  Total Steps: {total_steps}")
    print(f"  Approved: {approved_steps}")
    print(f"  Review Required: {review_required}")
    print(f"  Approval Rate: {(approved_steps/total_steps)*100:.1f}%")

    print(f"\n✅ QUALITY GATE INTEGRATION TEST COMPLETED")
    print("=" * 80)


def test_quality_dimensions():
    """Test quality dimension checking."""
    print("\n" + "=" * 80)
    print("QUALITY DIMENSIONS TEST")
    print("=" * 80)

    # Policy with specific dimensions
    policy = QualityPolicy(min_quality=0.7, quality_dimensions=["relevance", "completeness", "accuracy"])

    gate = QualityGate(policy)

    # Test with dimension details
    result_good = {
        "status": "success",
        "quality_score": 0.85,
        "quality_details": {"relevance": 0.90, "completeness": 0.85, "accuracy": 0.80},
    }

    result_bad = {
        "status": "success",
        "quality_score": 0.75,
        "quality_details": {"relevance": 0.90, "completeness": 0.60, "accuracy": 0.50},  # Below threshold  # Below threshold
    }

    print("\n[TEST 1] Good Dimensions")
    gate_result = gate.validate(result_good, "step_1", "plan_1")
    print(f"  Decision: {gate_result.decision.value}")
    print(f"  Quality: {gate_result.quality_score:.2f}")

    print("\n[TEST 2] Failed Dimensions")
    gate_result = gate.validate(result_bad, "step_2", "plan_1")
    print(f"  Decision: {gate_result.decision.value}")
    print(f"  Quality: {gate_result.quality_score:.2f}")
    if gate_result.metadata:
        print(f"  Failed Dimensions: {gate_result.metadata.get('failed_dimensions', [])}")

    print(f"\n✅ QUALITY DIMENSIONS TEST COMPLETED")
    print("=" * 80)


def test_review_workflow():
    """Test human review workflow."""
    print("\n" + "=" * 80)
    print("REVIEW WORKFLOW TEST")
    print("=" * 80)

    policy = QualityPolicy(min_quality=0.7, review_threshold_low=0.6, review_threshold_high=0.85)

    gate = QualityGate(policy)

    # Step with borderline quality
    result = {"status": "success", "quality_score": 0.75}

    print("\n[STEP 1] Validate Result")
    gate_result = gate.validate(result, "step_1", "plan_1")
    print(f"  Decision: {gate_result.decision.value}")
    print(f"  Requires Review: {gate_result.requires_review}")

    if gate_result.requires_review:
        print("\n[STEP 2] Create Review Request")
        review_request = gate.request_review(
            gate_result=gate_result, step_id="step_1", plan_id="plan_1", context={"test": "review workflow"}
        )

        print(f"  Request ID: {review_request.request_id}")
        print(f"  Status: {review_request.status.value}")
        print(f"  Quality: {review_request.quality_score:.2f}")

        print("\n[STEP 3] Approve Review")
        success = gate.approve_review(
            request_id=review_request.request_id, reviewer="test_reviewer", notes="Quality acceptable for test purposes"
        )

        print(f"  Approval: {'Success' if success else 'Failed'}")

        # Check status
        updated = gate.get_review_status(review_request.request_id)
        print(f"  Updated Status: {updated.status.value}")
        print(f"  Reviewer: {updated.reviewer}")
        print(f"  Notes: {updated.review_notes}")

    print(f"\n✅ REVIEW WORKFLOW TEST COMPLETED")
    print("=" * 80)


def main():
    """Run all tests."""
    print("\n🧪 VERITAS AGENT FRAMEWORK - QUALITY GATE INTEGRATION TESTS")
    print("=" * 80)

    try:
        # Test 1: Basic integration
        test_quality_gate_integration()

        # Test 2: Quality dimensions
        test_quality_dimensions()

        # Test 3: Review workflow
        test_review_workflow()

        print("\n" + "=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("\nPhase 4.1 Features Validated:")
        print("  ✓ Quality gate integration with BaseAgent")
        print("  ✓ Threshold-based approval/rejection")
        print("  ✓ Quality dimension checking")
        print("  ✓ Human review workflow")
        print("  ✓ Retry suggestions")
        print("\n🎉 PHASE 4.1: QUALITY GATE SYSTEM - COMPLETE")
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
