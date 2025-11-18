Project: VCC-Veritas (Scientific Research Platform)
Language: Python

Purpose:
- AI-powered scientific research tools with multi-agent systems and retrieval-augmented generation.

What Copilot should help with:
- Implement research agents, data ingestion connectors, and RAG/LLM orchestration.
- Assist creating example notebooks, reproducible experiments and data citation guidance.

Coding style and constraints:
- Record datasets and citation metadata. Include provenance info in `docs/`.
- Keep experiments reproducible; provide seeds and environment specs.

Documentation duties (./docs):
- Add `docs/experiments.md`, `docs/agents.md` and a dataset/citation policy.

Todo.md continuation:
- Add tasks for agent improvements, dataset ingestion, and reproducibility checks.

Examples for Copilot prompts:
- "Create an agent that queries the indexed literature and returns a structured summary with sources."

Testing & CI:
- Add unit tests for agent logic and smoke tests for RAG components.
