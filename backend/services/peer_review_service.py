"""
Service für Multi-LLM Peer-Review Validation
Führt parallele Reviews mit verschiedenen LLMs durch und berechnet Consensus.
"""
import asyncio
import json
from typing import Any, Dict, List

from backend.models.peer_review import (
    DEFAULT_REVIEW_CRITERIA,
    ApprovalStatus,
    PeerReviewResult,
    Review,
    ReviewCriteria,
    ReviewRecommendation,
    calculate_consensus_score,
    determine_approval_status,
    identify_conflicts,
)

                weight=float(cast(Any, weight_val)),
                description=str(cast(Any, desc_val)),
                score=float(cast(Any, v.get("score", 0.0))),
                comments=v.get("comments", ""),
            )
        return Review(
            reviewer_model=model,
            reviewer_description=desc,
            overall_score=data.get("overall_score", 0.0),
            criteria_scores=criteria,
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            recommendation=ReviewRecommendation(data.get("recommendation", "revise")),
            detailed_comments=data.get("detailed_comments", ""),
        )

    def _build_final_verdict(self, reviews: List[Review], approval_status: ApprovalStatus) -> str:
        if approval_status == ApprovalStatus.APPROVED:
            return "Peer-Review bestanden: Hohe Übereinstimmung."
        if approval_status == ApprovalStatus.REJECTED:
            return "Peer-Review abgelehnt: Kritische Mängel festgestellt."
        return "Peer-Review mit Vorbehalten: Überarbeitung empfohlen."
