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


class PeerReviewValidationService:
    def __init__(self, llm_client, reviewer_models=None):
        self.llm_client = llm_client
        self.reviewer_models = reviewer_models or [
            ("llama3.1:8b", "Generalist, stark in Rechtsfragen"),
            ("mixtral:latest", "Multi-lingual, ausgewogen"),
            ("gemma3:latest", "Faktenfokussiert, konservativ"),
        ]
        self.prompt_path = "backend/prompts/peer_review_prompt.txt"

    async def peer_review(
        self, query: str, final_response: str, agent_results: List[Dict[str, Any]], sources: List[str]
    ) -> PeerReviewResult:
        """Führt parallele Peer-Reviews mit mehreren LLMs durch"""
        prompt_base = self._build_prompt(query, final_response, agent_results, sources)
        tasks = [self._review_with_model(prompt_base, model, desc) for model, desc in self.reviewer_models]
        reviews: List[Review] = await asyncio.gather(*tasks)
        consensus = calculate_consensus_score(reviews)
        avg_score = sum(r.overall_score for r in reviews) / len(reviews) if reviews else 0.0
        approval_status = determine_approval_status(reviews)
        conflicts = identify_conflicts(reviews)
        recommendations = [r.detailed_comments for r in reviews if r.recommendation != ReviewRecommendation.APPROVE]
        return PeerReviewResult(
            reviews=reviews,
            consensus_score=consensus,
            average_score=avg_score,
            approval_status=approval_status,
            conflicts=conflicts,
            final_verdict=self._build_final_verdict(reviews, approval_status),
            confidence=consensus,
            recommendations=recommendations,
        )

    def _build_prompt(self, query, final_response, agent_results, sources):
        with open(self.prompt_path, encoding="utf-8") as f:
            prompt = f.read()
        prompt = prompt.replace("{query}", query)
        prompt = prompt.replace("{final_response}", final_response)
        prompt = prompt.replace("{sources}", json.dumps(sources, ensure_ascii=False))
        prompt = prompt.replace("{agent_results}", json.dumps(agent_results, ensure_ascii=False))
        return prompt

    async def _review_with_model(self, prompt, model, desc):
        # Simpler sync-Wrapper für LLM-Call (ggf. awaitable machen)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: self.llm_client.generate(prompt, model=model, temperature=0.2, max_tokens=2048)
        )
        data = json.loads(response)
        # Mapping auf Review-Dataclass
        criteria = {}
        for k, v in data.get("criteria_scores", {}).items():
            criteria[k] = ReviewCriteria(
                name=k,
                weight=DEFAULT_REVIEW_CRITERIA.get(k, {}).get("weight", 0.2),
                description=DEFAULT_REVIEW_CRITERIA.get(k, {}).get("description", ""),
                score=v.get("score", 0.0),
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
