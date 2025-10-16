"""Manueller Test für den RAGContextService ohne externe Backends."""

import asyncio
import json
import os
import sys
from pprint import pprint

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.agents.rag_context_service import RAGContextService, RAGQueryOptions


async def run_fallback_demo() -> None:
    service = RAGContextService()
    context = await service.build_context(
        "Wie wird die Luftqualität in München gemessen?",
        user_context={"strategy_weights": {"vector": 0.7, "graph": 0.2, "relational": 0.1}},
        options=RAGQueryOptions(limit_documents=3),
    )

    print("RAG-Kontext (Fallback-Modus):")
    pprint(context)
    print("\nJSON:")
    print(json.dumps(context, indent=2, ensure_ascii=False))

    assert context["meta"]["fallback_used"] is True
    assert len(context["documents"]) == 3
    assert context["vector"]["statistics"]["fallback"] is True


if __name__ == "__main__":
    asyncio.run(run_fallback_demo())
