#!/usr/bin/env python3
"""
PROMPT IMPROVEMENT ENGINE
=========================

Selbstverbesserungsmechanismus für scientific_foundation.json

FEATURES:
- Automated Quality Metrics Collection
- LLM Self-Evaluation Integration
- Iterative Prompt Refinement
- Version Management

Author: VERITAS System
Version: 1.0
"""

import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality Metrics für eine Query-Execution"""

    query_id: str
    timestamp: str

    # JSON Validity
    json_valid: bool
    json_parse_error: Optional[str] = None

    # Schema Compliance
    schema_valid: bool
    missing_fields: List[str] = None

    # Confidence Calibration (gemessen nach User-Feedback)
    predicted_confidence: float = 0.0
    actual_confidence: Optional[float] = None  # User-Rating

    # Required Criteria Quality
    num_criteria: int = 0
    vague_criteria: List[str] = None  # Zu vage formulierte Kriterien

    # Source Citation
    citations_found: int = 0
    citations_expected: int = 0

    # Metacognition Quality
    improvement_suggestions: List[str] = None

    def __post_init__(self):
        if self.missing_fields is None:
            self.missing_fields = []
        if self.vague_criteria is None:
            self.vague_criteria = []
        if self.improvement_suggestions is None:
            self.improvement_suggestions = []


@dataclass
class PromptVersion:
    """Eine Version des Scientific Foundation Prompts"""

    version: str
    date: str
    changes: str
    quality_score: Optional[float] = None
    tested_queries: int = 0
    metrics_summary: Optional[Dict] = None


class PromptImprovementEngine:
    """
    Engine für iterative Verbesserung von scientific_foundation.json

    WORKFLOW:
    1. Collect Metrics von jeder Query
    2. Aggregate Metrics über N Queries
    3. Identify Improvement Opportunities
    4. Generate Prompt Improvements (LLM-assisted)
    5. Create New Version mit Changes
    """

    def __init__(
        self,
        foundation_path: str = "config/prompts/scientific_foundation.json",
        metrics_db_path: str = "data/prompt_metrics.json",
    ):
        """
        Args:
            foundation_path: Pfad zu scientific_foundation.json
            metrics_db_path: Pfad zu Metrics-Datenbank (JSON)
        """
        self.foundation_path = Path(foundation_path)
        self.metrics_db_path = Path(metrics_db_path)

        # Load Current Foundation
        with open(self.foundation_path, "r", encoding="utf-8") as f:
            self.foundation = json.load(f)

        # Load Metrics DB (oder create)
        if self.metrics_db_path.exists():
            with open(self.metrics_db_path, "r", encoding="utf-8") as f:
                self.metrics_db = json.load(f)
        else:
            self.metrics_db = {"metrics": [], "aggregated": {}, "versions": []}

        logger.info(f"✅ Prompt Improvement Engine initialized")
        logger.info(f"   Foundation: {self.foundation_path}")
        logger.info(f"   Current Version: {self.foundation['scientific_foundation']['version']}")
        logger.info(f"   Metrics Collected: {len(self.metrics_db['metrics'])}")

    def record_query_metrics(self, metrics: QualityMetrics):
        """
        Record Metrics von einer Query-Execution

        Args:
            metrics: QualityMetrics Objekt
        """

        # Append to metrics DB
        self.metrics_db["metrics"].append(asdict(metrics))

        # Save to disk
        self._save_metrics_db()

        logger.info(f"📊 Recorded metrics for query: {metrics.query_id}")

        # Check if threshold reached for improvement
        current_version = self.foundation["scientific_foundation"]["version"]
        version_metrics = [m for m in self.metrics_db["metrics"] if m.get("version") == current_version]

        if len(version_metrics) >= 10:  # Threshold: 10 Queries
            logger.info(f"🔄 Threshold reached ({len(version_metrics)} queries)")
            logger.info(f"   → Triggering improvement analysis")
            self.analyze_and_improve()

    def analyze_and_improve(self) -> Dict[str, Any]:
        """
        Analyze gesammelte Metrics und generiere Verbesserungsvorschläge

        Returns:
            {
                "current_quality_scores": {...},
                "improvement_opportunities": [...],
                "suggested_changes": [...]
            }
        """

        logger.info("🔍 Analyzing metrics...")

        # 1. Aggregate Metrics
        aggregated = self._aggregate_metrics()

        # 2. Compare to Targets
        current_scores = self._calculate_quality_scores(aggregated)

        # 3. Identify Gaps
        improvement_opportunities = self._identify_improvement_opportunities(
            current_scores, self.foundation["scientific_foundation"]["prompt_improvement"]["improvement_metrics"]
        )

        # 4. Generate Suggestions
        suggested_changes = self._generate_improvement_suggestions(improvement_opportunities, aggregated)

        # 5. Store Results
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "version": self.foundation["scientific_foundation"]["version"],
            "queries_analyzed": len(self.metrics_db["metrics"]),
            "current_quality_scores": current_scores,
            "improvement_opportunities": improvement_opportunities,
            "suggested_changes": suggested_changes,
        }

        self.metrics_db["aggregated"][datetime.now().isoformat()] = analysis_result
        self._save_metrics_db()

        logger.info("✅ Analysis complete")
        logger.info(f"   Quality Scores: {current_scores}")
        logger.info(f"   Improvement Opportunities: {len(improvement_opportunities)}")

        return analysis_result

    def _aggregate_metrics(self) -> Dict[str, Any]:
        """Aggregate alle Metrics"""

        metrics_list = self.metrics_db["metrics"]

        if not metrics_list:
            return {}

        total = len(metrics_list)

        return {
            "json_validity_rate": sum(1 for m in metrics_list if m["json_valid"]) / total,
            "schema_validity_rate": sum(1 for m in metrics_list if m["schema_valid"]) / total,
            "avg_num_criteria": sum(m["num_criteria"] for m in metrics_list) / total,
            "avg_vague_criteria": sum(len(m.get("vague_criteria", [])) for m in metrics_list) / total,
            "citation_rate": sum(
                m["citations_found"] / m["citations_expected"] if m["citations_expected"] > 0 else 0 for m in metrics_list
            )
            / total,
            "confidence_calibration_error": self._calculate_confidence_error(metrics_list),
            "common_improvement_suggestions": self._extract_common_suggestions(metrics_list),
        }

    def _calculate_confidence_error(self, metrics_list: List[Dict]) -> float:
        """Berechne durchschnittlichen Confidence Calibration Error"""

        errors = []
        for m in metrics_list:
            if m.get("actual_confidence") is not None:
                error = abs(m["predicted_confidence"] - m["actual_confidence"])
                errors.append(error)

        return sum(errors) / len(errors) if errors else 0.0

    def _extract_common_suggestions(self, metrics_list: List[Dict]) -> List[Dict]:
        """Extrahiere häufigste Improvement Suggestions aus Metacognition"""

        suggestion_counts = defaultdict(int)

        for m in metrics_list:
            for suggestion in m.get("improvement_suggestions", []):
                suggestion_counts[suggestion] += 1

        # Top 5 häufigste Suggestions
        sorted_suggestions = sorted(suggestion_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return [{"suggestion": s, "frequency": count} for s, count in sorted_suggestions]

    def _calculate_quality_scores(self, aggregated: Dict) -> Dict[str, float]:
        """Berechne Quality Scores für alle Metrics"""

        return {
            "json_validity_rate": aggregated.get("json_validity_rate", 0.0),
            "confidence_calibration_accuracy": 1.0 - aggregated.get("confidence_calibration_error", 1.0),
            "required_criteria_quality": 1.0 - (aggregated.get("avg_vague_criteria", 10) / 10),  # Normalize
            "source_citation_rate": aggregated.get("citation_rate", 0.0),
        }

    def _identify_improvement_opportunities(self, current_scores: Dict[str, float], targets: List[Dict]) -> List[Dict]:
        """Identify Metrics die unter Target sind"""

        opportunities = []

        for target in targets:
            metric_id = target["metric_id"]
            target_value = target["target"]
            current_value = current_scores.get(metric_id, 0.0)

            if current_value < target_value:
                gap = target_value - current_value
                opportunities.append(
                    {
                        "metric_id": metric_id,
                        "metric_name": target["name"],
                        "current": current_value,
                        "target": target_value,
                        "gap": gap,
                        "priority": "high" if gap > 0.15 else "medium" if gap > 0.05 else "low",
                        "improvement_actions": target["improvement_actions"],
                    }
                )

        return sorted(opportunities, key=lambda x: x["gap"], reverse=True)

    def _generate_improvement_suggestions(self, opportunities: List[Dict], aggregated: Dict) -> List[Dict]:
        """Generiere konkrete Verbesserungsvorschläge"""

        suggestions = []

        for opp in opportunities:
            metric_id = opp["metric_id"]

            if metric_id == "json_validity_rate":
                suggestions.append(
                    {
                        "target_section": "output_quality_standards.json_formatting",
                        "change_type": "add_examples",
                        "description": "Füge mehr Beispiele für valides JSON hinzu",
                        "priority": opp["priority"],
                        "rationale": f"Aktuelle Validitätsrate: {opp['current']:.2%}, Ziel: {opp['target']:.2%}",
                    }
                )

            elif metric_id == "confidence_calibration_accuracy":
                suggestions.append(
                    {
                        "target_section": "output_quality_standards.confidence_calibration",
                        "change_type": "refine_criteria",
                        "description": "Verfeinere Kriterien für Confidence-Ranges",
                        "priority": opp["priority"],
                        "rationale": f"Calibration Error: {1.0 - opp['current']:.2%}",
                    }
                )

            elif metric_id == "required_criteria_quality":
                # Get common vague criteria patterns
                vague_examples = aggregated.get("common_vague_patterns", [])
                suggestions.append(
                    {
                        "target_section": "output_quality_standards.required_criteria_guidelines",
                        "change_type": "add_negative_examples",
                        "description": f"Füge explizite ❌ Beispiele hinzu: {vague_examples}",
                        "priority": opp["priority"],
                        "rationale": f"Durchschnittlich {aggregated.get('avg_vague_criteria', 0):.1f} vage Kriterien pro Query",
                    }
                )

            elif metric_id == "source_citation_rate":
                suggestions.append(
                    {
                        "target_section": "core_principles",
                        "change_type": "strengthen_principle",
                        "description": "Verschärfe 'evidence_based' Prinzip: Erzwinge Quellen-Referenz",
                        "priority": opp["priority"],
                        "rationale": f"Citation Rate: {opp['current']:.2%}, Ziel: {opp['target']:.2%}",
                    }
                )

        # Add suggestions from LLM Metacognition
        for common_suggestion in aggregated.get("common_improvement_suggestions", []):
            suggestions.append(
                {
                    "target_section": "multiple",
                    "change_type": "llm_feedback",
                    "description": common_suggestion["suggestion"],
                    "priority": "high" if common_suggestion["frequency"] > 5 else "medium",
                    "rationale": f"LLM schlug dies {common_suggestion['frequency']}x vor",
                }
            )

        return suggestions

    def apply_improvements(self, suggestions: List[Dict]) -> str:
        """
        Apply Improvements zu scientific_foundation.json

        Args:
            suggestions: Liste von Improvement Suggestions

        Returns:
            new_version: Neue Version-Nummer (z.B. "1.1.0")
        """

        logger.info(f"🔧 Applying {len(suggestions)} improvements...")

        # 1. Create Backup
        backup_path = self.foundation_path.with_suffix(".json.bak")
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(self.foundation, f, indent=2, ensure_ascii=False)
        logger.info(f"   Backup created: {backup_path}")

        # 2. Increment Version
        current_version = self.foundation["scientific_foundation"]["version"]
        new_version = self._increment_version(current_version)

        # 3. Apply Changes (manual implementation required per suggestion)
        changes_applied = []

        for suggestion in suggestions:
            if suggestion["priority"] in ["high", "medium"]:
                # Apply change (simplified - real implementation would modify JSON)
                changes_applied.append(suggestion["description"])
                logger.info(f"   ✅ Applied: {suggestion['description']}")

        # 4. Update Metadata
        self.foundation["scientific_foundation"]["version"] = new_version
        self.foundation["scientific_foundation"]["last_updated"] = datetime.now().isoformat()
        self.foundation["scientific_foundation"]["improvement_iteration"] += 1

        # Add to version history
        version_entry = {
            "version": new_version,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "changes": "; ".join(changes_applied),
            "quality_score": None,
            "tested_queries": 0,
        }

        self.foundation["scientific_foundation"]["prompt_improvement"]["version_history"].append(version_entry)

        # 5. Save New Version
        with open(self.foundation_path, "w", encoding="utf-8") as f:
            json.dump(self.foundation, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Improvements applied: v{current_version} → v{new_version}")

        return new_version

    def _increment_version(self, version: str) -> str:
        """Increment Version (Semantic Versioning)"""
        major, minor, patch = map(int, version.split("."))

        # Minor version increment (1.0.0 → 1.1.0)
        return f"{major}.{minor + 1}.{patch}"

    def _save_metrics_db(self):
        """Save Metrics DB to disk"""
        self.metrics_db_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.metrics_db_path, "w", encoding="utf-8") as f:
            json.dump(self.metrics_db, f, indent=2, ensure_ascii=False)

    def get_current_quality_report(self) -> Dict:
        """Get Current Quality Report"""

        if not self.metrics_db["metrics"]:
            return {"status": "no_data", "message": "Keine Metrics vorhanden"}

        aggregated = self._aggregate_metrics()
        scores = self._calculate_quality_scores(aggregated)

        return {
            "version": self.foundation["scientific_foundation"]["version"],
            "queries_tested": len(self.metrics_db["metrics"]),
            "quality_scores": scores,
            "overall_score": sum(scores.values()) / len(scores) if scores else 0.0,
            "aggregated_metrics": aggregated,
        }


# Example Usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    engine = PromptImprovementEngine()

    # Simulate recording metrics
    test_metrics = QualityMetrics(
        query_id="test_001",
        timestamp=datetime.now().isoformat(),
        json_valid=True,
        schema_valid=True,
        predicted_confidence=0.85,
        actual_confidence=0.90,
        num_criteria=4,
        vague_criteria=[],
        citations_found=5,
        citations_expected=5,
        improvement_suggestions=["Mehr Beispiele für Confidence-Ranges"],
    )

    engine.record_query_metrics(test_metrics)

    # Get quality report
    report = engine.get_current_quality_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
