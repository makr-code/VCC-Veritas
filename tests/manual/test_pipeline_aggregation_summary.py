"""Manueller Test für die Multi-Agent Aggregation der Intelligent Pipeline."""

import asyncio
import os
import sys
from pprint import pprint

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.agents.veritas_intelligent_pipeline import IntelligentMultiAgentPipeline  # noqa: E402


async def run_aggregation_demo() -> None:
    pipeline = IntelligentMultiAgentPipeline()

    mock_results = {
        "environmental": pipeline._generate_mock_agent_result(  # type: ignore[attr-defined]
            "environmental",
            "Wie wird die Luftqualität aktuell bewertet?",
        ),
        "legal_framework": pipeline._generate_mock_agent_result(  # type: ignore[attr-defined]
            "legal_framework",
            "Welche Rechtsgrundlagen gelten für Emissionsschutz?",
        ),
    }

    normalized = pipeline._normalize_agent_results(mock_results)  # type: ignore[attr-defined]
    aggregation_summary, consensus_summary = pipeline._build_aggregation_summary(  # type: ignore[attr-defined]
        normalized,
        {
            "documents": [
                {"title": "Luftreinhalteplan München", "relevance": 0.88},
                {"title": "BImSchG §47", "relevance": 0.8},
            ],
            "meta": {"fallback_used": True},
        },
    )

    print("📊 Aggregationszusammenfassung:")
    pprint(aggregation_summary)

    print("\n🤝 Consensus:")
    pprint(consensus_summary)

    assert aggregation_summary["key_points"], "Key Points sollten nicht leer sein"
    assert consensus_summary["coverage"]["total_agents"] == len(normalized)
    assert "blended_confidence" not in consensus_summary  # wird erst in _step_result_aggregation gesetzt


if __name__ == "__main__":
    asyncio.run(run_aggregation_demo())
