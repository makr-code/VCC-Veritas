"""
VERITAS Agent Framework - Quality Gate System
==============================================

Quality gates provide threshold-based validation and approval for research plan steps.

Features:
- Quality score thresholds (minimum, target)
- Automatic approval/rejection based on quality
- Human-in-the-loop review for borderline cases
- Quality history tracking
- Configurable gate policies

Usage:
    from quality_gate import QualityGate, QualityPolicy

    # Create policy
    policy = QualityPolicy(
        min_quality=0.7,
        target_quality=0.9,
        require_review=True
    )

    # Create gate
    gate = QualityGate(policy)

    # Validate result
    decision = gate.validate(result)
    if decision.approved:
        print("Quality gate passed!")

Created: 2025-10-08
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class GateDecision(Enum):
    """Quality gate decision."""

    APPROVED = "approved"
    REJECTED = "rejected"
    REVIEW_REQUIRED = "review_required"
    RETRY_SUGGESTED = "retry_suggested"


class ReviewStatus(Enum):
    """Human review status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


@dataclass
class QualityPolicy:
    """
    Quality gate policy configuration.

    Attributes:
        min_quality: Minimum acceptable quality score (0.0-1.0)
        target_quality: Target quality score for automatic approval
        review_threshold_low: Below this, automatic rejection
        review_threshold_high: Above this, automatic approval
        require_review: Always require human review
        max_retries: Maximum retry attempts before requiring review
        quality_dimensions: Specific quality dimensions to check
    """

    min_quality: float = 0.7
    target_quality: float = 0.9
    review_threshold_low: float = 0.6
    review_threshold_high: float = 0.85
    require_review: bool = False
    max_retries: int = 3
    quality_dimensions: Optional[List[str]] = None

    def __post_init__(self):
        """Validate policy configuration."""
        if not 0.0 <= self.min_quality <= 1.0:
            raise ValueError("min_quality must be between 0.0 and 1.0")
        if not 0.0 <= self.target_quality <= 1.0:
            raise ValueError("target_quality must be between 0.0 and 1.0")
        if self.min_quality > self.target_quality:
            raise ValueError("min_quality cannot exceed target_quality")


@dataclass
class GateResult:
    """
    Quality gate validation result.

    Attributes:
        decision: Gate decision (approved/rejected/review)
        quality_score: Overall quality score
        meets_threshold: Whether score meets minimum threshold
        reasons: List of reasons for decision
        recommendations: Recommended actions
        requires_review: Whether human review is needed
        retry_suggested: Whether retry is suggested
        metadata: Additional metadata
    """

    decision: GateDecision
    quality_score: float
    meets_threshold: bool
    reasons: List[str]
    recommendations: List[str]
    requires_review: bool = False
    retry_suggested: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ReviewRequest:
    """
    Human review request.

    Attributes:
        request_id: Unique request identifier
        step_id: Step being reviewed
        plan_id: Plan being reviewed
        quality_score: Current quality score
        gate_result: Gate validation result
        context: Additional context for reviewer
        status: Review status
        reviewer: Assigned reviewer
        review_notes: Reviewer notes
        created_at: Request creation timestamp
        reviewed_at: Review completion timestamp
    """

    request_id: str
    step_id: str
    plan_id: str
    quality_score: float
    gate_result: GateResult
    context: Dict[str, Any]
    status: ReviewStatus = ReviewStatus.PENDING
    reviewer: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: str = None
    reviewed_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


class QualityGate:
    """
    Quality gate for validating research plan step results.

    Validates results against quality policies and determines
    whether steps should be approved, rejected, or require review.
    """

    def __init__(self, policy: QualityPolicy, review_callback: Optional[Callable[[ReviewRequest], ReviewStatus]] = None):
        """
        Initialize quality gate.

        Args:
            policy: Quality policy configuration
            review_callback: Optional callback for human review
        """
        self.policy = policy
        self.review_callback = review_callback
        self.review_history: List[ReviewRequest] = []

        logger.info(f"Initialized QualityGate with policy: " f"min={policy.min_quality}, target={policy.target_quality}")

    def validate(self, result: Dict[str, Any], step_id: str, plan_id: str, retry_count: int = 0) -> GateResult:
        """
        Validate step result against quality policy.

        Args:
            result: Step execution result
            step_id: Step identifier
            plan_id: Plan identifier
            retry_count: Number of retry attempts

        Returns:
            GateResult with validation decision
        """
        quality_score = result.get("quality_score", 0.0)
        status = result.get("status", "unknown")

        logger.info(f"Validating step {step_id}: quality={quality_score:.2f}, " f"retries={retry_count}")

        # Check if step failed
        if status == "failed":
            return self._create_failed_result(quality_score, retry_count)

        # Check quality dimensions if specified
        if self.policy.quality_dimensions:
            dimension_check = self._check_quality_dimensions(result, self.policy.quality_dimensions)
            if not dimension_check["passed"]:
                return self._create_dimension_failure_result(quality_score, dimension_check)

        # Force review if policy requires it
        if self.policy.require_review:
            return self._create_review_required_result(quality_score, "Policy requires human review")

        # Automatic rejection for very low quality
        if quality_score < self.policy.review_threshold_low:
            return self._create_rejection_result(quality_score, retry_count)

        # Automatic approval for high quality
        if quality_score >= self.policy.review_threshold_high:
            return self._create_approval_result(quality_score)

        # Review required for borderline cases
        if self.policy.review_threshold_low <= quality_score < self.policy.review_threshold_high:
            return self._create_review_required_result(quality_score, "Quality in review range")

        # Default: check against minimum threshold
        meets_threshold = quality_score >= self.policy.min_quality

        if meets_threshold:
            return self._create_approval_result(quality_score)
        else:
            return self._create_rejection_result(quality_score, retry_count)

    def _create_approval_result(self, quality_score: float) -> GateResult:
        """Create approval result."""
        return GateResult(
            decision=GateDecision.APPROVED,
            quality_score=quality_score,
            meets_threshold=True,
            reasons=[
                f"Quality score {quality_score:.2f} meets requirements",
                f"Exceeds minimum threshold {self.policy.min_quality:.2f}",
            ],
            recommendations=["Proceed to next step"],
            requires_review=False,
            retry_suggested=False,
        )

    def _create_rejection_result(self, quality_score: float, retry_count: int) -> GateResult:
        """Create rejection result."""
        retry_suggested = retry_count < self.policy.max_retries

        reasons = [
            f"Quality score {quality_score:.2f} below minimum {self.policy.min_quality:.2f}",
            f"Retry count: {retry_count}/{self.policy.max_retries}",
        ]

        recommendations = []
        if retry_suggested:
            recommendations.append(f"Retry step (attempt {retry_count + 1})")
            recommendations.append("Consider adjusting parameters")
        else:
            recommendations.append("Maximum retries exceeded")
            recommendations.append("Requires review or plan modification")

        return GateResult(
            decision=GateDecision.RETRY_SUGGESTED if retry_suggested else GateDecision.REJECTED,
            quality_score=quality_score,
            meets_threshold=False,
            reasons=reasons,
            recommendations=recommendations,
            requires_review=not retry_suggested,
            retry_suggested=retry_suggested,
        )

    def _create_review_required_result(self, quality_score: float, reason: str) -> GateResult:
        """Create review required result."""
        return GateResult(
            decision=GateDecision.REVIEW_REQUIRED,
            quality_score=quality_score,
            meets_threshold=quality_score >= self.policy.min_quality,
            reasons=[reason, f"Quality score: {quality_score:.2f}"],
            recommendations=["Human review recommended", "Assess result quality manually"],
            requires_review=True,
            retry_suggested=False,
        )

    def _create_failed_result(self, quality_score: float, retry_count: int) -> GateResult:
        """Create result for failed step."""
        retry_suggested = retry_count < self.policy.max_retries

        return GateResult(
            decision=GateDecision.RETRY_SUGGESTED if retry_suggested else GateDecision.REJECTED,
            quality_score=quality_score,
            meets_threshold=False,
            reasons=["Step execution failed", f"Retry count: {retry_count}/{self.policy.max_retries}"],
            recommendations=[
                "Review error logs",
                "Retry with modified parameters" if retry_suggested else "Requires intervention",
            ],
            requires_review=not retry_suggested,
            retry_suggested=retry_suggested,
        )

    def _create_dimension_failure_result(self, quality_score: float, dimension_check: Dict[str, Any]) -> GateResult:
        """Create result for quality dimension failure."""
        failed_dimensions = dimension_check.get("failed_dimensions", [])

        return GateResult(
            decision=GateDecision.REJECTED,
            quality_score=quality_score,
            meets_threshold=False,
            reasons=[f"Quality dimension check failed", f"Failed dimensions: {', '.join(failed_dimensions)}"],
            recommendations=["Review dimension-specific quality", "Address failing quality aspects"],
            requires_review=True,
            retry_suggested=True,
            metadata={"failed_dimensions": failed_dimensions},
        )

    def _check_quality_dimensions(self, result: Dict[str, Any], dimensions: List[str]) -> Dict[str, Any]:
        """
        Check specific quality dimensions.

        Args:
            result: Step result
            dimensions: Quality dimensions to check

        Returns:
            Dict with check results
        """
        quality_details = result.get("quality_details", {})
        failed_dimensions = []

        for dimension in dimensions:
            dimension_score = quality_details.get(dimension)
            if dimension_score is None:
                failed_dimensions.append(f"{dimension} (missing)")
            elif dimension_score < self.policy.min_quality:
                failed_dimensions.append(f"{dimension} ({dimension_score:.2f})")

        return {"passed": len(failed_dimensions) == 0, "failed_dimensions": failed_dimensions}

    def request_review(self, gate_result: GateResult, step_id: str, plan_id: str, context: Dict[str, Any]) -> ReviewRequest:
        """
        Create human review request.

        Args:
            gate_result: Gate validation result
            step_id: Step identifier
            plan_id: Plan identifier
            context: Additional context

        Returns:
            ReviewRequest object
        """
        import uuid

        request = ReviewRequest(
            request_id=str(uuid.uuid4()),
            step_id=step_id,
            plan_id=plan_id,
            quality_score=gate_result.quality_score,
            gate_result=gate_result,
            context=context,
        )

        self.review_history.append(request)

        logger.info(f"Created review request {request.request_id} " f"for step {step_id}")

        # Call review callback if provided
        if self.review_callback:
            try:
                status = self.review_callback(request)
                request.status = status
                request.reviewed_at = datetime.utcnow().isoformat()
            except Exception as e:
                logger.error(f"Review callback failed: {e}")

        return request

    def get_review_status(self, request_id: str) -> Optional[ReviewRequest]:
        """
        Get review request status.

        Args:
            request_id: Review request identifier

        Returns:
            ReviewRequest or None if not found
        """
        for request in self.review_history:
            if request.request_id == request_id:
                return request
        return None

    def approve_review(self, request_id: str, reviewer: str, notes: Optional[str] = None) -> bool:
        """
        Approve review request.

        Args:
            request_id: Review request identifier
            reviewer: Reviewer name
            notes: Optional review notes

        Returns:
            True if successful
        """
        request = self.get_review_status(request_id)
        if request is None:
            logger.error(f"Review request not found: {request_id}")
            return False

        request.status = ReviewStatus.APPROVED
        request.reviewer = reviewer
        request.review_notes = notes
        request.reviewed_at = datetime.utcnow().isoformat()

        logger.info(f"Review {request_id} approved by {reviewer}")
        return True

    def reject_review(self, request_id: str, reviewer: str, notes: Optional[str] = None) -> bool:
        """
        Reject review request.

        Args:
            request_id: Review request identifier
            reviewer: Reviewer name
            notes: Optional review notes

        Returns:
            True if successful
        """
        request = self.get_review_status(request_id)
        if request is None:
            logger.error(f"Review request not found: {request_id}")
            return False

        request.status = ReviewStatus.REJECTED
        request.reviewer = reviewer
        request.review_notes = notes
        request.reviewed_at = datetime.utcnow().isoformat()

        logger.info(f"Review {request_id} rejected by {reviewer}")
        return True


# ========================================
# Example Usage & Tests
# ========================================


def _test_quality_gate():
    """Test quality gate system."""
    print("=" * 80)
    print("QUALITY GATE SYSTEM TEST")
    print("=" * 80)

    # Create policy
    policy = QualityPolicy(
        min_quality=0.7, target_quality=0.9, review_threshold_low=0.6, review_threshold_high=0.85, max_retries=3
    )

    # Create gate
    gate = QualityGate(policy)

    # Test cases
    test_cases = [
        {"name": "High Quality (Auto-Approve)", "result": {"status": "success", "quality_score": 0.95}, "retry_count": 0},
        {"name": "Borderline Quality (Review)", "result": {"status": "success", "quality_score": 0.75}, "retry_count": 0},
        {"name": "Low Quality (Reject/Retry)", "result": {"status": "success", "quality_score": 0.50}, "retry_count": 0},
        {"name": "Failed Step", "result": {"status": "failed", "quality_score": 0.0}, "retry_count": 0},
        {"name": "Max Retries Exceeded", "result": {"status": "success", "quality_score": 0.50}, "retry_count": 3},
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {test['name']}")
        print("-" * 40)

        gate_result = gate.validate(
            result=test["result"], step_id=f"step_{i}", plan_id="test_plan_001", retry_count=test["retry_count"]
        )

        print(f"Decision: {gate_result.decision.value}")
        print(f"Quality Score: {gate_result.quality_score:.2f}")
        print(f"Meets Threshold: {gate_result.meets_threshold}")
        print(f"Requires Review: {gate_result.requires_review}")
        print(f"Retry Suggested: {gate_result.retry_suggested}")
        print(f"Reasons:")
        for reason in gate_result.reasons:
            print(f"  - {reason}")
        print(f"Recommendations:")
        for rec in gate_result.recommendations:
            print(f"  - {rec}")

    print("\n" + "=" * 80)
    print("✅ ALL QUALITY GATE TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    _test_quality_gate()
