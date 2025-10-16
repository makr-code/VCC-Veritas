"""Manueller Test der Agenten-Ausführungslogik in der Intelligent Pipeline.

Der Test stellt sicher, dass:
- Agenten anhand der Prioritätswerte sortiert werden
- Dynamisch deaktivierte Tasks übersprungen werden
- Parallel- und Sequenz-Plan eingehalten werden
"""

import asyncio
import os
import sys
from pprint import pprint

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.agents.veritas_intelligent_pipeline import (  # noqa: E402
    IntelligentMultiAgentPipeline,
    IntelligentPipelineRequest,
)


def _build_demo_request() -> IntelligentPipelineRequest:
    return IntelligentPipelineRequest(
        query_id="manual-plan-test",
        query_text="Wie wird die Luftqualität bewertet und wer ist zuständig?",
        user_context={"location": "München"},
        enable_llm_commentary=False,
    )


async def run_execution_plan_demo() -> None:
    pipeline = IntelligentMultiAgentPipeline()

    request = _build_demo_request()
    agent_selection = {
        "selected_agents": [
            "environmental",
            "financial",
            "quality_assessor",
            "document_retrieval",
        ],
        "priority_map": {
            "environmental": 0.9,
            "financial": 0.8,
            "quality_assessor": 0.4,
            "document_retrieval": 0.2,
        },
        "execution_plan": {
            "parallel_agents": ["environmental", "financial"],
            "sequential_agents": ["quality_assessor"],
        },
        "orchestrator_context": {
            "dynamic_actions": {"disabled": ["document_retrieval"]}
        },
    }

    context = {
        "agent_selection": agent_selection,
        "rag": {},
    }

    print("▶️ Ausführungsplan wird getestet...")
    result = await pipeline._step_parallel_agent_execution(request, context)

    execution_trace = result["execution_summary"]["execution_trace"]
    print("\nAusführungsspur:")
    pprint(execution_trace)

    assert execution_trace[0]["agent"] == "environmental"
    assert execution_trace[1]["agent"] == "financial"
    assert execution_trace[-1]["status"] == "skipped"
    assert execution_trace[-1]["agent"] == "document_retrieval"

    summary = result["execution_summary"]
    assert summary["agents_executed"] == 3
    assert summary["agents_skipped"] == 1

    print("\nZusammenfassung:")
    pprint(summary)
    print("\n✅ Prioritätsbasierte Ausführung erfolgreich validiert.")


if __name__ == "__main__":
    asyncio.run(run_execution_plan_demo())
