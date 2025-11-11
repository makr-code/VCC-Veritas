"""
Service für dialektische Synthese (Thesis-Antithesis-Synthesis)
Nutze Ollama LLM für Thesen-Extraktion, Widerspruchs-Erkennung und Synthese.
"""
import json
from typing import Any, Dict, List

from backend.models.dialectical_synthesis import (
    Contradiction,
    DialecticalSynthesis,
    Thesis,
    create_contradiction_from_dict,
    create_thesis_from_dict,
)


class DialecticalSynthesisService:
    def __init__(self, llm_client, model_name="llama3.1:8b"):
        self.llm_client = llm_client
        self.model_name = model_name
        self.prompts = {
            "thesis_extraction": "backend / prompts/thesis_extraction_prompt.txt",
            "contradiction_detection": "backend / prompts/contradiction_detection_prompt.txt",
            "dialectical_synthesis": "backend / prompts/dialectical_synthesis_prompt.txt",
        }

    def extract_theses(self, agent_results: List[Dict[str, Any]]) -> List[Thesis]:
        """Extrahiert Thesen aus Agent-Results via LLM"""
        with open(self.prompts["thesis_extraction"], encoding="utf-8") as f:
            prompt = f.read().replace("{agent_results}", json.dumps(agent_results, ensure_ascii=False))
        llm_response = self.llm_client.generate(prompt, model=self.model_name, temperature=0.2, max_tokens=2048)
        data = json.loads(llm_response)
        return [create_thesis_from_dict(t) for t in data.get("theses", [])]

    def detect_contradictions(self, theses: List[Thesis]) -> List[Contradiction]:
        """Identifiziert Widersprüche zwischen Thesen via LLM"""
        theses_json = json.dumps([t.to_dict() for t in theses], ensure_ascii=False)
        with open(self.prompts["contradiction_detection"], encoding="utf-8") as f:
            prompt = f.read().replace("{theses}", theses_json)
        llm_response = self.llm_client.generate(prompt, model=self.model_name, temperature=0.2, max_tokens=2048)
        data = json.loads(llm_response)
        return [create_contradiction_from_dict(c, theses) for c in data.get("contradictions", [])]

    def synthesize(self, query: str, theses: List[Thesis], contradictions: List[Contradiction]) -> DialecticalSynthesis:
        """Erstellt dialektische Synthese via LLM"""
        prompt_vars = {
            "query": query,
            "theses": json.dumps([t.to_dict() for t in theses], ensure_ascii=False),
            "contradictions": json.dumps([c.to_dict() for c in contradictions], ensure_ascii=False),
        }
        with open(self.prompts["dialectical_synthesis"], encoding="utf-8") as f:
            prompt = f.read()
            for k, v in prompt_vars.items():
                prompt = prompt.replace(f"{{{k}}}", v)
        llm_response = self.llm_client.generate(prompt, model=self.model_name, temperature=0.2, max_tokens=3072)
        data = json.loads(llm_response)
        # Mapping der Felder auf DialecticalSynthesis
        resolved = [
            contradictions[c["contradiction_index"]]
            for c in data.get("resolved_contradictions", [])
            if "contradiction_index" in c
        ]
        unresolved = [
            contradictions[c["contradiction_index"]]
            for c in data.get("unresolved_conflicts", [])
            if "contradiction_index" in c
        ]
        return DialecticalSynthesis(
            theses=theses,
            contradictions=contradictions,
            synthesis_text=data.get("synthesis_text", ""),
            resolution_strategies=data.get("resolution_strategies", []),
            unresolved_conflicts=unresolved,
            confidence=data.get("confidence", 0.7),
            reasoning=data.get("reasoning", ""),
            metadata={"resolved": len(resolved), "unresolved": len(unresolved)},
        )
