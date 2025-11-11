"""
Scientific Phase Executor - Generischer Executor für alle wissenschaftlichen Phasen

Lädt JSON-basierte Methoden-Konfigurationen und führt LLM-Calls mit
Jinja2-Template-Rendering, Retry-Logic und Schema-Validierung aus.

Author: VERITAS v7.0 Implementation
Date: 12. Oktober 2025
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from jsonschema import ValidationError, validate

# VERITAS imports
from backend.agents.veritas_ollama_client import OllamaRequest, OllamaResponse, VeritasOllamaClient

logger = logging.getLogger(__name__)


@dataclass
class PhaseExecutionContext:
    """
    Kontext für Phase-Execution mit allen Template-Variablen
    """

    # Core variables
    user_query: str
    rag_results: Dict[str, Any]

    # Previous phase results (individual fields for backward compatibility)
    hypothesis: Optional[Dict[str, Any]] = None
    synthesis_result: Optional[Dict[str, Any]] = None
    analysis_result: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    conclusion_result: Optional[Dict[str, Any]] = None

    # Scientific foundation
    scientific_foundation: Optional[Dict[str, Any]] = None

    # All previous phases (for supervisor phase access)
    previous_phases: Dict[str, Any] = field(default_factory=dict)

    # Execution metadata (for supervisor phase access)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Execution ID
    execution_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    phase_start_time: Optional[float] = None

    def to_template_dict(self) -> Dict[str, Any]:
        """
        Konvertiert Context zu Dictionary für Jinja2-Templates
        """
        return {
            "user_query": self.user_query,
            "rag_results": self.rag_results,
            "hypothesis": self.hypothesis,
            "synthesis_result": self.synthesis_result,
            "analysis_result": self.analysis_result,
            "validation_result": self.validation_result,
            "conclusion_result": self.conclusion_result,
            "scientific_foundation": self.scientific_foundation,
            "execution_id": self.execution_id,
        }


@dataclass
class PhaseResult:
    """
    Result eines Phase-Executors
    """

    phase_id: str
    status: str  # 'success', 'failed', 'partial'
    output: Dict[str, Any]
    confidence: float
    execution_time_ms: float
    retry_count: int = 0
    validation_errors: List[str] = field(default_factory=list)
    raw_llm_output: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata


class ScientificPhaseExecutor:
    """
    Generischer Executor für alle wissenschaftlichen Phasen

    Features:
    - Lädt JSON-Methoden-Konfigurationen (default_method.json)
    - Lädt JSON-Prompt-Templates (phase1_hypothesis.json, etc.)
    - Rendert Prompts mit Jinja2 (template variables)
    - Führt LLM-Calls mit Retry-Logic aus
    - Validiert Output gegen JSON Schema
    - Sammelt Execution Metrics

    Usage:
        executor = ScientificPhaseExecutor(
            config_dir="config",
            method_id="default_scientific_method"
        )

        context = PhaseExecutionContext(
            user_query="Brauche ich Baugenehmigung für Carport in BW?",
            rag_results={"semantic": [...], "graph": [...]}
        )

        result = await executor.execute_phase("hypothesis", context)
    """

    def __init__(
        self,
        config_dir: str = "config",
        method_id: str = "default_scientific_method",
        ollama_client: Optional[Any] = None,  # OllamaClient später integrieren
    ):
        """
        Initialize ScientificPhaseExecutor

        Args:
            config_dir: Root config directory (enthält scientific_methods/, prompts/)
            method_id: ID der zu ladenden Methode (z.B. "default_scientific_method")
            ollama_client: OllamaClient-Instanz (optional, wird automatisch erstellt wenn None)
        """
        self.config_dir = Path(config_dir)
        self.method_id = method_id
        self.ollama_client = ollama_client

        # Load configurations
        self.method_config = self._load_method_config()
        self.scientific_foundation = self._load_scientific_foundation()
        self.phase_prompts: Dict[str, Dict[str, Any]] = {}

        # Setup Jinja2 environment
        # Use select_autoescape to enable escaping for markup templates while
        # keeping text templates unescaped by default. This avoids insecure
        # autoescape=False usage which Bandit flags (B701).
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.config_dir / "prompts" / "scientific")),
            autoescape=select_autoescape(enabled_extensions=("html", "xml"), default_for_string=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.info(f"ScientificPhaseExecutor initialized: method={method_id}")

    def _load_method_config(self) -> Dict[str, Any]:
        """
        Lädt default_method.json Konfiguration

        Returns:
            Method configuration dict

        Raises:
            FileNotFoundError: Wenn Datei nicht existiert
            json.JSONDecodeError: Wenn JSON ungültig
        """
        config_path = self.config_dir / "scientific_methods" / f"{self.method_id}.json"

        if not config_path.exists():
            raise FileNotFoundError(
                f"Method config nicht gefunden: {config_path}\n"
                f"Verfügbare Methoden: {list((self.config_dir / 'scientific_methods').glob(' * .json'))}"
            )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            logger.info(f"Method config geladen: {config_path} ({len(config.get('phases', []))} Phasen)")
            return config

        except json.JSONDecodeError as e:
            raise ValueError(f"Ungültiges JSON in {config_path}: {e}")

    def _load_scientific_foundation(self) -> Dict[str, Any]:
        """
        Lädt scientific_foundation.json

        Returns:
            Scientific foundation dict
        """
        foundation_path = self.config_dir / "scientific_foundation.json"

        if not foundation_path.exists():
            logger.warning(f"scientific_foundation.json nicht gefunden: {foundation_path}")
            return {}

        try:
            with open(foundation_path, "r", encoding="utf-8") as f:
                foundation = json.load(f)

            logger.info(f"Scientific foundation geladen: {foundation_path}")
            return foundation

        except json.JSONDecodeError as e:
            logger.error(f"Fehler beim Laden von scientific_foundation.json: {e}")
            return {}

    def _load_phase_prompt(self, phase_id: str) -> Dict[str, Any]:
        """
        Lädt Phase Prompt JSON (cached)

        Args:
            phase_id: Phase ID (z.B. "hypothesis", "synthesis")

        Returns:
            Phase prompt dict

        Raises:
            FileNotFoundError: Wenn Prompt-Datei nicht existiert
        """
        # Check cache
        if phase_id in self.phase_prompts:
            return self.phase_prompts[phase_id]

        # Find phase config in method
        phase_config = next((p for p in self.method_config["phases"] if p["phase_id"] == phase_id), None)

        if not phase_config:
            raise ValueError(
                f"Phase '{phase_id}' nicht in method_config gefunden. "
                f"Verfügbare Phasen: {[p['phase_id'] for p in self.method_config['phases']]}"
            )

        # Load prompt template JSON
        prompt_template_path = phase_config["prompt_template"]
        prompt_path = self.config_dir / "prompts" / prompt_template_path

        if not prompt_path.exists():
            raise FileNotFoundError(f"Phase prompt nicht gefunden: {prompt_path}")

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = json.load(f)

            # Cache it
            self.phase_prompts[phase_id] = prompt
            logger.info(f"Phase prompt geladen: {phase_id} ({prompt_path})")
            return prompt

        except json.JSONDecodeError as e:
            raise ValueError(f"Ungültiges JSON in {prompt_path}: {e}")

    def _construct_prompt(self, phase_id: str, context: PhaseExecutionContext) -> str:
        """
        Konstruiert finalen Prompt aus JSON-Template + Jinja2-Rendering

        Args:
            phase_id: Phase ID (z.B. "hypothesis")
            context: Execution context mit allen Template-Variablen

        Returns:
            Gerenderter Prompt (String für LLM)
        """
        # Load phase prompt JSON
        prompt_config = self._load_phase_prompt(phase_id)

        # Prepare template variables
        template_vars = context.to_template_dict()
        template_vars["scientific_foundation"] = self.scientific_foundation

        # Extract prompt sections
        system_prompt = prompt_config.get("system_prompt", {})
        instructions = prompt_config.get("instructions", [])
        output_format = prompt_config.get("output_format", {})
        quality_guidelines = prompt_config.get("quality_guidelines", {})
        example_outputs = prompt_config.get("example_outputs", [])

        # Construct prompt parts
        prompt_parts = []

        # 1. System Prompt
        if system_prompt:
            prompt_parts.append("# ROLLE & AUFGABE\n")
            prompt_parts.append(f"**Rolle:** {system_prompt.get('role', '')}\n")
            prompt_parts.append(f"**Aufgabe:** {system_prompt.get('task', '')}\n")
            prompt_parts.append(f"**Methodik:** {system_prompt.get('methodology', '')}\n")

        # 2. Instructions
        if instructions:
            prompt_parts.append("\n# ANWEISUNGEN\n")
            for idx, step in enumerate(instructions, 1):
                action = step.get("action", "")
                description = step.get("description", "")
                prompt_parts.append(f"\n## Schritt {idx}: {action}\n")
                if description:
                    prompt_parts.append(f"{description}\n")

        # 3. Output Format
        if output_format:
            prompt_parts.append("\n# OUTPUT-FORMAT\n")
            prompt_parts.append("**Typ:** JSON\n")
            prompt_parts.append("**Required Fields:** " + ", ".join(output_format.get("required_fields", [])) + "\n")

        # 4. Quality Guidelines
        if quality_guidelines:
            prompt_parts.append("\n# QUALITY GUIDELINES\n")
            prompt_parts.append(json.dumps(quality_guidelines, indent=2, ensure_ascii=False))
            prompt_parts.append("\n")

        # 5. Example Outputs (nur erstes Beispiel, nicht alle)
        if example_outputs and len(example_outputs) > 0:
            prompt_parts.append("\n# BEISPIEL-OUTPUT\n")
            prompt_parts.append("```json\n")
            prompt_parts.append(json.dumps(example_outputs[0], indent=2, ensure_ascii=False))
            prompt_parts.append("\n```\n")

        # 6. Template Variables (User Query, RAG Results, Previous Phases)
        prompt_parts.append("\n# INPUT-DATEN\n")
        prompt_parts.append(f"\n## User Query\n{template_vars.get('user_query', 'N / A')}\n")

        if template_vars.get("rag_results"):
            prompt_parts.append(
                f"\n## RAG Results\n```json\n{json.dumps(template_vars['rag_results'], indent=2, ensure_ascii=False)}\n```\n"
            )

        if template_vars.get("hypothesis"):
            prompt_parts.append(
                f"\n## Hypothesis (Phase 1)\n```json\n{json.dumps(template_vars['hypothesis'], indent=2, ensure_ascii=False)}\n```\n"
            )

        if template_vars.get("synthesis_result"):
            prompt_parts.append(
                f"\n## Synthesis (Phase 2)\n```json\n{json.dumps(template_vars['synthesis_result'], indent=2, ensure_ascii=False)}\n```\n"
            )

        if template_vars.get("analysis_result"):
            prompt_parts.append(
                f"\n## Analysis (Phase 3)\n```json\n{json.dumps(template_vars['analysis_result'], indent=2, ensure_ascii=False)}\n```\n"
            )

        if template_vars.get("validation_result"):
            prompt_parts.append(
                f"\n## Validation (Phase 4)\n```json\n{json.dumps(template_vars['validation_result'], indent=2, ensure_ascii=False)}\n```\n"
            )

        # Final prompt
        final_prompt = "".join(prompt_parts)

        logger.debug(f"Prompt konstruiert für Phase '{phase_id}' ({len(final_prompt)} chars)")
        return final_prompt

    async def _execute_llm_call_with_retry(
        self, phase_id: str, prompt: str, execution_config: Dict[str, Any], retry_policy: Dict[str, Any]
    ) -> tuple[str, int]:
        """
        Führt LLM-Call mit Retry-Logic aus

        Args:
            phase_id: Phase ID
            prompt: Konstruierter Prompt
            execution_config: Execution config (model, temperature, max_tokens, timeout)
            retry_policy: Retry policy (max_retries, temperature_adjustment)

        Returns:
            (llm_output, retry_count)
        """
        max_retries = retry_policy.get("max_retries", 2)
        temperature = execution_config.get("temperature", 0.3)
        temperature_adjustment = retry_policy.get("temperature_adjustment", 0.9)

        for attempt in range(max_retries + 1):
            try:
                # Adjust temperature on retry
                current_temp = temperature * (temperature_adjustment**attempt)

                logger.info(f"LLM call attempt {attempt + 1}/{max_retries + 1}: " f"phase={phase_id}, temp={current_temp:.3f}")

                # Real Ollama LLM Call
                if self.ollama_client:
                    try:
                        # Create Ollama Request
                        ollama_request = OllamaRequest(
                            model=execution_config.get("model", "llama3.2"),
                            prompt=prompt,
                            temperature=current_temp,
                            max_tokens=execution_config.get("max_tokens", 1000),
                            stream=False,
                            system="Du bist ein wissenschaftlicher Assistent für juristische Analysen.",
                        )

                        logger.info(f"🤖 Sending Ollama request: model={ollama_request.model}, temp={current_temp:.3f}")

                        # Execute LLM call
                        response: OllamaResponse = await self.ollama_client.generate_response(
                            request=ollama_request, stream=False
                        )

                        llm_output = response.response

                        logger.info(
                            f"✅ Ollama response received: {len(llm_output)} chars, "
                            f"duration={response.total_duration if response.total_duration else 'N / A'}ms"
                        )

                        return llm_output, attempt

                    except Exception as ollama_error:
                        logger.warning(f"⚠️ Ollama call failed: {ollama_error}")
                        raise

                else:
                    # Mock response (für Testing ohne Ollama)
                    logger.warning("⚠️ OllamaClient nicht initialisiert - nutze Mock-Response")
                    llm_output = json.dumps(
                        {
                            "mock": True,
                            "phase_id": phase_id,
                            "message": "MOCK LLM Response - OllamaClient nicht initialisiert",
                            "note": "Bitte VeritasOllamaClient initialisieren für echte LLM - Calls",
                        },
                        indent=2,
                    )
                    return llm_output, attempt

            except Exception as e:
                logger.warning(f"❌ LLM call failed (attempt {attempt + 1}/{max_retries + 1}): {e}")

                if attempt >= max_retries:
                    raise RuntimeError(f"LLM call failed nach {max_retries + 1} Versuchen: {e}")

                # Exponential backoff
                await asyncio.sleep(1.0 * (1.5**attempt))

        raise RuntimeError("Unexpected: Retry loop exited without return")

    def _parse_and_validate_output(
        self, phase_id: str, llm_output: str, output_schema: Dict[str, Any]
    ) -> tuple[Dict[str, Any], List[str]]:
        """
        Parse LLM output und validiere gegen JSON Schema

        Args:
            phase_id: Phase ID
            llm_output: Raw LLM output
            output_schema: JSON Schema für Validierung

        Returns:
            (parsed_output, validation_errors)
        """
        validation_errors = []

        try:
            # 1. Extract JSON from markdown code blocks (if present)
            if "```json" in llm_output:
                # Extract content between ```json and ```
                json_start = llm_output.find("```json") + 7
                json_end = llm_output.find("```", json_start)
                json_str = llm_output[json_start:json_end].strip()
            elif "```" in llm_output:
                # Generic code block
                json_start = llm_output.find("```") + 3
                json_end = llm_output.find("```", json_start)
                json_str = llm_output[json_start:json_end].strip()
            else:
                # Assume entire output is JSON
                json_str = llm_output.strip()

            # 2. Parse JSON
            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError as e:
                validation_errors.append(f"JSON Parse Error: {e}")
                # Return partial result
                return {"error": "invalid_json", "raw": llm_output}, validation_errors

            # 3. Validate against schema
            try:
                validate(instance=parsed, schema=output_schema)
            except ValidationError as e:
                validation_errors.append(f"Schema Validation Error: {e.message}")
                # Continue with parsed data (partial validation)

            return parsed, validation_errors

        except Exception as e:
            logger.error(f"Unexpected error in _parse_and_validate_output: {e}")
            validation_errors.append(f"Parse Error: {e}")
            return {"error": "parse_failed", "raw": llm_output}, validation_errors

    async def execute_phase(self, phase_id: str, context: PhaseExecutionContext) -> PhaseResult:
        """
        Execute eine einzelne wissenschaftliche Phase

        Args:
            phase_id: Phase ID (z.B. "hypothesis", "synthesis")
            context: Execution context mit User Query, RAG results, previous phases

        Returns:
            PhaseResult mit output, confidence, execution_time, etc.

        Raises:
            ValueError: Wenn Phase nicht existiert
            RuntimeError: Wenn LLM call fehlschlägt
        """
        start_time = datetime.now()
        context.phase_start_time = start_time.timestamp()

        logger.info(f"=== Executing Phase: {phase_id} ===")

        # 1. Get phase config
        phase_config = next((p for p in self.method_config["phases"] if p["phase_id"] == phase_id), None)

        if not phase_config:
            raise ValueError(
                f"Phase '{phase_id}' nicht gefunden. " f"Verfügbare: {[p['phase_id'] for p in self.method_config['phases']]}"
            )

        # 2. Construct prompt
        prompt = self._construct_prompt(phase_id, context)

        # 3. Execute LLM call with retry
        llm_output, retry_count = await self._execute_llm_call_with_retry(
            phase_id=phase_id,
            prompt=prompt,
            execution_config=phase_config["execution"],
            retry_policy=phase_config["retry_policy"],
        )

        # 4. Parse and validate output
        parsed_output, validation_errors = self._parse_and_validate_output(
            phase_id=phase_id, llm_output=llm_output, output_schema=phase_config["output_schema"]
        )

        # 5. Extract confidence
        confidence = parsed_output.get("confidence", 0.5)

        # 6. Determine status
        if validation_errors:
            status = "partial"
        elif "error" in parsed_output:
            status = "failed"
        else:
            status = "success"

        # 7. Calculate execution time
        end_time = datetime.now()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000

        result = PhaseResult(
            phase_id=phase_id,
            status=status,
            output=parsed_output,
            confidence=confidence,
            execution_time_ms=execution_time_ms,
            retry_count=retry_count,
            validation_errors=validation_errors,
            raw_llm_output=llm_output,
        )

        logger.info(
            f"Phase '{phase_id}' completed: status={status}, "
            f"confidence={confidence:.2f}, time={execution_time_ms:.0f}ms, "
            f"retries={retry_count}"
        )

        return result


# Example usage (wird später in UnifiedOrchestratorV7 integriert)
async def example_usage():
    """
    Beispiel: Single Phase Execution
    """
    # Initialize executor
    executor = ScientificPhaseExecutor(
        config_dir="config", method_id="default_scientific_method", ollama_client=None  # Mock mode
    )

    # Create context
    context = PhaseExecutionContext(
        user_query="Brauche ich eine Baugenehmigung für einen Carport in Baden-Württemberg?",
        rag_results={
            "semantic": [
                {
                    "source": "LBO BW § 50",
                    "content": "Verfahrensfreie Vorhaben: Gebäude bis 30m² Grundfläche...",
                    "confidence": 0.98,
                }
            ],
            "graph": [],
        },
    )

    # Execute Phase 1: Hypothesis
    result = await executor.execute_phase("hypothesis", context)

    print("\n=== Phase 1 Result ===")
    print(f"Status: {result.status}")
    print(f"Confidence: {result.confidence}")
    print(f"Output:\n{json.dumps(result.output, indent=2, ensure_ascii=False)}")
    print(f"Execution Time: {result.execution_time_ms:.0f}ms")

    return result


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
