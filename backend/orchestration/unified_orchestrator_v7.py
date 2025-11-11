"""
Unified Orchestrator v7.0 - JSON-driven Scientific Method Orchestrator

Koordiniert:
- RAG Search (Semantic + Graph)
- Scientific Phase Execution (6 Phasen)
- Agent Coordination (Baurecht, Umweltrecht, etc.)
- Prompt Improvement (Auto-Iteration alle 10 Queries)
- Streaming Progress (NDJSON)

Author: VERITAS v7.0 Implementation
Date: 12. Oktober 2025
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.agents.veritas_ollama_client import OllamaRequest, VeritasOllamaClient
from backend.agents.veritas_uds3_hybrid_agent import UDS3HybridSearchAgent

# VERITAS imports
from backend.services.scientific_phase_executor import PhaseExecutionContext, PhaseResult, ScientificPhaseExecutor

# UDS3 imports
try:
    import sys
    from pathlib import Path

    uds3_path = Path(__file__).parent.parent.parent.parent / "uds3"
    if str(uds3_path) not in sys.path:
        sys.path.insert(0, str(uds3_path))

    from uds3 import get_optimized_unified_strategy

    UDS3_AVAILABLE = True
except ImportError as e:
    logger.warning(f"UDS3 not available: {e}")
    UDS3_AVAILABLE = False
    get_optimized_unified_strategy = None


logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    """
    Streaming Event für Frontend

    Types:
    - processing_step: Ein Processing-Schritt (z.B. "rag_semantic", "phase_hypothesis")
    - phase_complete: Eine wissenschaftliche Phase abgeschlossen
    - progress: Fortschritts-Update (0.0-1.0)
    - error: Fehler-Event
    - final_result: Finale Antwort
    """

    type: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    data: Dict[str, Any] = field(default_factory=dict)

    def to_ndjson(self) -> str:
        """Konvertiert zu NDJSON-Zeile"""
        return json.dumps({"type": self.type, "timestamp": self.timestamp, "data": self.data}, ensure_ascii=False)


@dataclass
class OrchestratorResult:
    """
    Finale Result des Orchestrators
    """

    query: str
    scientific_process: Dict[str, Any]  # All 6 phases
    final_answer: str
    confidence: float
    execution_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class UnifiedOrchestratorV7:
    """
    Unified Orchestrator v7.0 - JSON-driven Scientific Method

    Features:
    - Scientific Method Execution (6 Phasen)
    - RAG Integration (Semantic + Graph)
    - Agent Coordination (Optional, parallel)
    - Prompt Improvement (Auto-Iteration alle 10 Queries)
    - Streaming Progress (NDJSON für Frontend)
    - Error Handling + Fallback Logic

    Usage:
        orchestrator = UnifiedOrchestratorV7(
            config_dir="config",
            ollama_client=ollama_client,
            rag_service=rag_service
        )

        # Streaming execution
        async for event in orchestrator.process_query_stream(
            "Brauche ich Baugenehmigung für Carport in BW?"
        ):
            print(event.to_ndjson())

        # Non-streaming execution
        result = await orchestrator.process_query(
            "Brauche ich Baugenehmigung für Carport in BW?"
        )
    """

    def __init__(
        self,
        config_dir: str = "config",
        method_id: str = "default_method",
        ollama_client: Optional[VeritasOllamaClient] = None,
        uds3_strategy: Optional[Any] = None,  # UDS3 UnifiedDatabaseStrategy
        agent_orchestrator: Optional[Any] = None,
        enable_streaming: bool = True,
    ):
        """
        Initialize UnifiedOrchestratorV7

        Args:
            config_dir: Root config directory
            method_id: Scientific method ID (default: "default_method")
            ollama_client: VeritasOllamaClient instance
            uds3_strategy: UDS3 UnifiedDatabaseStrategy (replaces rag_service)
            agent_orchestrator: Agent orchestrator (optional)
            enable_streaming: Enable streaming progress
        """
        self.config_dir = Path(config_dir)
        self.method_id = method_id
        self.ollama_client = ollama_client
        self.agent_orchestrator = agent_orchestrator
        self.enable_streaming = enable_streaming

        # Initialize UDS3 Strategy
        if uds3_strategy is None and UDS3_AVAILABLE:
            try:
                self.uds3_strategy = get_optimized_unified_strategy()
                logger.info("✅ UDS3 Strategy auto-initialized")
            except Exception as e:
                logger.warning(f"⚠️ UDS3 auto-initialization failed: {e}")
                self.uds3_strategy = None
        else:
            self.uds3_strategy = uds3_strategy

        # Initialize UDS3 Hybrid Search Agent (replaces rag_service)
        if self.uds3_strategy:
            try:
                self.search_agent = UDS3HybridSearchAgent(self.uds3_strategy)
                logger.info("✅ UDS3 Hybrid Search Agent initialized")
            except Exception as e:
                logger.warning(f"⚠️ UDS3 Search Agent init failed: {e}")
                self.search_agent = None
        else:
            self.search_agent = None
            logger.warning("⚠️ UDS3 not available - using mock RAG")

        # Initialize ScientificPhaseExecutor
        self.phase_executor = ScientificPhaseExecutor(
            config_dir=str(config_dir), method_id=method_id, ollama_client=ollama_client
        )

        # Initialize SupervisorAgent (if enabled in method config)
        self.supervisor_agent = None
        if self._is_supervisor_enabled():
            try:
                from backend.agents.veritas_supervisor_agent import get_supervisor_agent

                # Note: get_supervisor_agent is async, will be initialized in first query
                self._supervisor_initialization_pending = True
                logger.info("✅ Supervisor mode enabled - will initialize on first query")
            except ImportError as e:
                logger.warning(f"⚠️ SupervisorAgent not available: {e}")
                self._supervisor_initialization_pending = False
        else:
            self._supervisor_initialization_pending = False
            logger.info("ℹ️ Supervisor mode disabled in method config")

        # Query counter für Prompt Improvement
        self.query_count = 0

        # Prompt Improvement Engine (TODO: Integration)
        self.prompt_improvement_engine = None

        logger.info(
            f"UnifiedOrchestratorV7 initialized: method={method_id}, "
            f"streaming={enable_streaming}, uds3={bool(self.uds3_strategy)}"
        )

    async def process_query(
        self, user_query: str, user_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None
    ) -> OrchestratorResult:
        """
        Main Entry Point: Process User Query (Non-Streaming)

        Args:
            user_query: User's question
            user_id: Optional user ID
            context: Optional additional context

        Returns:
            OrchestratorResult with final answer + scientific process
        """
        start_time = datetime.now()

        logger.info(f"Processing query: {user_query[:100]}...")

        # 1. Query Enhancement (Optional)
        enhanced_query = await self._enhance_query(user_query)

        # 2. RAG Search (Semantic + Graph)
        rag_results = await self._collect_rag_results(enhanced_query or user_query)

        # 3. Execute Scientific Phases (6 Phasen)
        scientific_process = await self._execute_scientific_phases(user_query=user_query, rag_results=rag_results)

        # 4. Extract Final Answer
        final_answer = self._extract_final_answer(scientific_process)
        final_confidence = self._extract_final_confidence(scientific_process)

        # 5. Calculate Execution Time
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        # 6. Increment Query Counter (für Prompt Improvement)
        self.query_count += 1

        result = OrchestratorResult(
            query=user_query,
            scientific_process=scientific_process,
            final_answer=final_answer,
            confidence=final_confidence,
            execution_time_ms=execution_time_ms,
            metadata={"user_id": user_id, "query_count": self.query_count, "method_id": self.method_id},
        )

        logger.info(
            f"Query processed: {execution_time_ms:.0f}ms, "
            f"confidence={final_confidence:.2f}, "
            f"queries_total={self.query_count}"
        )

        return result

    async def process_query_stream(
        self, user_query: str, user_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Main Entry Point: Process User Query (Streaming)

        Args:
            user_query: User's question
            user_id: Optional user ID
            context: Optional additional context

        Yields:
            StreamEvent objects (type=processing_step, phase_complete, progress, final_result)
        """
        start_time = datetime.now()

        logger.info(f"Processing query (streaming): {user_query[:100]}...")

        # Emit start event
        yield StreamEvent(type="progress", data={"stage": "start", "progress": 0.0, "message": "Query wird verarbeitet..."})

        try:
            # 1. Query Enhancement (Optional)
            yield StreamEvent(type="processing_step", data={"step_id": "query_enhancement", "status": "started"})

            enhanced_query = await self._enhance_query(user_query)

            yield StreamEvent(type="processing_step", data={"step_id": "query_enhancement", "status": "completed"})
            yield StreamEvent(type="progress", data={"stage": "query_enhancement", "progress": 0.1})

            # 2. RAG Search
            yield StreamEvent(type="processing_step", data={"step_id": "rag_search", "status": "started"})

            rag_results = await self._collect_rag_results(enhanced_query or user_query)

            yield StreamEvent(
                type="processing_step",
                data={
                    "step_id": "rag_search",
                    "status": "completed",
                    "results_count": len(rag_results.get("semantic", [])) + len(rag_results.get("graph", [])),
                },
            )
            yield StreamEvent(type="progress", data={"stage": "rag_search", "progress": 0.2})

            # 3. Execute Scientific Phases (6 Phasen mit Streaming)
            scientific_process = {}
            phase_ids = ["hypothesis", "synthesis", "analysis", "validation", "conclusion", "metacognition"]

            for idx, phase_id in enumerate(phase_ids):
                progress = 0.2 + (0.7 * (idx / len(phase_ids)))

                yield StreamEvent(type="processing_step", data={"step_id": f"phase_{phase_id}", "status": "started"})

                # Execute phase
                phase_result = await self._execute_single_phase(
                    phase_id=phase_id, user_query=user_query, rag_results=rag_results, previous_phases=scientific_process
                )

                scientific_process[phase_id] = phase_result.output

                yield StreamEvent(
                    type="phase_complete",
                    data={
                        "phase_id": phase_id,
                        "status": phase_result.status,
                        "confidence": phase_result.confidence,
                        "execution_time_ms": phase_result.execution_time_ms,
                    },
                )
                yield StreamEvent(
                    type="progress", data={"stage": f"phase_{phase_id}", "progress": progress + (0.7 / len(phase_ids))}
                )

            # 4. Extract Final Answer
            final_answer = self._extract_final_answer(scientific_process)
            final_confidence = self._extract_final_confidence(scientific_process)

            # 5. Calculate Execution Time
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            # 6. Increment Query Counter
            self.query_count += 1

            # Emit final result
            yield StreamEvent(
                type="final_result",
                data={
                    "query": user_query,
                    "final_answer": final_answer,
                    "confidence": final_confidence,
                    "execution_time_ms": execution_time_ms,
                    "scientific_process": scientific_process,
                    "metadata": {"user_id": user_id, "query_count": self.query_count, "method_id": self.method_id},
                },
            )

            yield StreamEvent(type="progress", data={"stage": "complete", "progress": 1.0, "message": "Abgeschlossen"})

            logger.info(f"Query processed (streaming): {execution_time_ms:.0f}ms, " f"confidence={final_confidence:.2f}")

        except Exception as e:
            logger.error(f"Error in process_query_stream: {e}", exc_info=True)

            yield StreamEvent(type="error", data={"error": str(e), "stage": "processing"})

    async def _enhance_query(self, user_query: str) -> Optional[str]:
        """
        Optional: Enhance User Query mit Query Enhancement Prompt

        Args:
            user_query: Original query

        Returns:
            Enhanced query or None (if enhancement fails)
        """
        # TODO: Implementierung mit user_query_enhancement.json
        # Für jetzt: Return None (kein Enhancement)
        return None

    async def _collect_rag_results(self, query: str) -> Dict[str, Any]:
        """
        Collect RAG Results using UDS3 Hybrid Search

        Args:
            query: Search query

        Returns:
            {
                'semantic': [list of search results],
                'graph': [list of graph search results],
                'hybrid': [list of hybrid results]
            }
        """
        if not self.search_agent:
            logger.warning("⚠️ UDS3 Search Agent nicht verfügbar - nutze Mock-Daten")
            return {
                "semantic": [
                    {
                        "source": "MOCK: LBO BW § 50",
                        "source_type": "gesetz",
                        "content": "MOCK: Verfahrensfreie Vorhaben bis 30m² Grundfläche...",
                        "confidence": 0.95,
                        "relevance": 0.90,
                    }
                ],
                "graph": [],
                "hybrid": [],
            }

        try:
            # Use UDS3 Hybrid Search (Vector + Graph)
            logger.info(f"🔍 UDS3 Hybrid Search: {query[:100]}...")

            hybrid_results = await self.search_agent.hybrid_search(
                query=query, top_k=10, weights={"vector": 0.6, "graph": 0.4}, search_types=["vector", "graph"]
            )

            # Convert to RAG result format
            semantic_results = []
            graph_results = []

            for result in hybrid_results:
                # Extract source type from metadata
                source_type = result.metadata.get("source_type", "unknown")
                source_name = result.metadata.get("name", result.document_id)

                # Determine if vector or graph result
                if "vector" in result.scores:
                    semantic_results.append(
                        {
                            "source": source_name,
                            "source_type": source_type,
                            "content": result.content,
                            "confidence": result.scores.get("vector", 0.0),
                            "relevance": result.final_score,
                            "metadata": result.metadata,
                        }
                    )

                if "graph" in result.scores:
                    graph_results.append(
                        {
                            "source": source_name,
                            "source_type": source_type,
                            "content": result.content,
                            "confidence": result.scores.get("graph", 0.0),
                            "relevance": result.final_score,
                            "metadata": result.metadata,
                        }
                    )

            logger.info(
                f"✅ UDS3 Search: {len(hybrid_results)} total " f"({len(semantic_results)} vector, {len(graph_results)} graph)"
            )

            return {
                "semantic": semantic_results,
                "graph": graph_results,
                "hybrid": [
                    {
                        "source": r.metadata.get("name", r.document_id),
                        "source_type": r.metadata.get("source_type", "unknown"),
                        "content": r.content,
                        "confidence": r.final_score,
                        "metadata": r.metadata,
                    }
                    for r in hybrid_results
                ],
            }

        except Exception as e:
            logger.error(f"❌ UDS3 Search failed: {e}", exc_info=True)

            # Fallback to mock data
            return {
                "semantic": [
                    {
                        "source": "ERROR: UDS3 Search failed",
                        "source_type": "error",
                        "content": f"Error: {str(e)}",
                        "confidence": 0.0,
                        "relevance": 0.0,
                    }
                ],
                "graph": [],
                "hybrid": [],
            }

    async def _execute_scientific_phases(self, user_query: str, rag_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute alle wissenschaftlichen Phasen sequentiell (inkl. Supervisor-Phasen falls enabled)

        Args:
            user_query: User's question
            rag_results: RAG search results

        Returns:
            {
                'hypothesis': {...},
                'supervisor_agent_selection': {...},  // Optional
                'agent_execution': {...},  // Optional
                'synthesis': {...},
                'analysis': {...},
                'validation': {...},
                'conclusion': {...},
                'metacognition': {...},
                'agent_result_synthesis': {...}  // Optional
            }
        """
        scientific_process = {}

        # Load method config to get phase order
        method_config_path = self.config_dir / "scientific_methods" / f"{self.method_id}.json"
        with open(method_config_path, "r", encoding="utf-8") as f:
            method_config = json.load(f)

        phases = method_config.get("phases", [])
        supervisor_enabled = method_config.get("supervisor_enabled", False)

        # Create execution context with previous_phases and metadata
        context = PhaseExecutionContext(
            user_query=user_query,
            rag_results=rag_results,
            previous_phases={},  # Will be updated as phases complete
            metadata={},  # Additional metadata
        )

        # Execute phases in order
        for phase_config in phases:
            phase_id = phase_config["phase_id"]
            executor = phase_config.get("execution", {}).get("executor", "llm")

            # Skip supervisor phases if supervisor is disabled
            if not supervisor_enabled and executor in ["supervisor", "agent_coordinator"]:
                logger.info(f"⏭️ Skipping {phase_id} (supervisor disabled)")
                continue

            logger.info(f"🔄 Executing phase: {phase_id} (executor={executor})")

            try:
                if executor == "supervisor":
                    # Supervisor-Phase (1.5 oder 6.5)
                    result = await self._execute_supervisor_phase(phase_config, context)

                elif executor == "agent_coordinator":
                    # Agent-Execution-Phase (1.6)
                    result = await self._execute_agent_coordination_phase(phase_config, context)

                else:
                    # Standard LLM-Phase (1, 2, 3, 4, 5, 6)
                    result = await self.phase_executor.execute_phase(phase_id, context)

                # Store result
                scientific_process[phase_id] = result.output

                # Update context.previous_phases (for supervisor phase access)
                context.previous_phases = scientific_process

                # Update context with new result (update individual phase fields for backward compatibility)
                if phase_id == "hypothesis":
                    context.hypothesis = result.output
                elif phase_id == "synthesis":
                    context.synthesis_result = result.output
                elif phase_id == "analysis":
                    context.analysis_result = result.output
                elif phase_id == "validation":
                    context.validation_result = result.output
                elif phase_id == "conclusion":
                    context.conclusion_result = result.output

                logger.info(f"✅ Phase {phase_id} completed in {result.execution_time_ms:.0f}ms")

            except Exception as e:
                logger.error(f"❌ Phase {phase_id} failed: {e}")

                # Store error in scientific_process
                scientific_process[phase_id] = {"error": str(e), "status": "failed"}

                # Check if phase is critical
                critical_phases = (
                    method_config.get("orchestration_config", {})
                    .get("error_handling", {})
                    .get("critical_phases", ["hypothesis", "conclusion"])
                )

                if phase_id in critical_phases:
                    logger.error(f"💥 Critical phase {phase_id} failed - stopping execution")
                    break
                else:
                    logger.warning(f"⚠️ Non-critical phase {phase_id} failed - continuing")

        return scientific_process

    async def _execute_single_phase(
        self, phase_id: str, user_query: str, rag_results: Dict[str, Any], previous_phases: Dict[str, Any]
    ) -> PhaseResult:
        """
        Execute eine einzelne wissenschaftliche Phase

        Args:
            phase_id: Phase ID (z.B. "hypothesis")
            user_query: User's question
            rag_results: RAG results
            previous_phases: Results von vorherigen Phasen

        Returns:
            PhaseResult
        """
        # Create context mit previous phases
        context = PhaseExecutionContext(
            user_query=user_query,
            rag_results=rag_results,
            hypothesis=previous_phases.get("hypothesis"),
            synthesis_result=previous_phases.get("synthesis"),
            analysis_result=previous_phases.get("analysis"),
            validation_result=previous_phases.get("validation"),
            conclusion_result=previous_phases.get("conclusion"),
        )

        # Execute phase
        return await self.phase_executor.execute_phase(phase_id, context)

    def _extract_final_answer(self, scientific_process: Dict[str, Any]) -> str:
        """
        Extract final answer from scientific process

        Priority:
        1. Phase 6.5 (agent_result_synthesis) - if available
        2. Phase 5 (conclusion)
        3. Fallback

        Args:
            scientific_process: Complete scientific process

        Returns:
            Final answer string
        """
        # Priority 1: Agent Result Synthesis (Phase 6.5)
        if "agent_result_synthesis" in scientific_process:
            synthesis = scientific_process["agent_result_synthesis"]
            if "final_answer" in synthesis:
                return synthesis["final_answer"]

        # Priority 2: Conclusion (Phase 5)
        conclusion = scientific_process.get("conclusion", {})
        if "main_answer" in conclusion:
            return conclusion["main_answer"]

        # Fallback
        return "Keine finale Antwort verfügbar."

    def _extract_final_confidence(self, scientific_process: Dict[str, Any]) -> float:
        """
        Extract final confidence from scientific process

        Priority:
        1. Phase 6.5 (agent_result_synthesis) - if available
        2. Phase 5 (conclusion)
        3. Average from all phases

        Args:
            scientific_process: Complete scientific process

        Returns:
            Confidence score (0.0-1.0)
        """
        # Priority 1: Agent Result Synthesis (Phase 6.5)
        if "agent_result_synthesis" in scientific_process:
            synthesis = scientific_process["agent_result_synthesis"]
            if "confidence_score" in synthesis:
                return float(synthesis["confidence_score"])

        # Priority 2: Conclusion (Phase 5)
        conclusion = scientific_process.get("conclusion", {})
        if "confidence" in conclusion:
            return float(conclusion["confidence"])

        # Fallback: Average confidence aus allen Phasen
        confidences = []
        for phase_result in scientific_process.values():
            if isinstance(phase_result, dict) and "confidence" in phase_result:
                confidences.append(float(phase_result["confidence"]))

        if confidences:
            return sum(confidences) / len(confidences)

        return 0.5  # Default fallback

    def _is_supervisor_enabled(self) -> bool:
        """
        Check if supervisor is enabled in method config

        Returns:
            True if supervisor_enabled flag is set in method config
        """
        try:
            method_config_path = self.config_dir / "scientific_methods" / f"{self.method_id}.json"
            if method_config_path.exists():
                with open(method_config_path, "r", encoding="utf-8") as f:
                    method_config = json.load(f)
                    return method_config.get("supervisor_enabled", False)
        except Exception as e:
            logger.warning(f"⚠️ Could not check supervisor_enabled flag: {e}")

        return False

    async def _ensure_supervisor_initialized(self):
        """
        Ensure SupervisorAgent is initialized (async initialization)
        """
        if self._supervisor_initialization_pending and self.supervisor_agent is None:
            try:
                from backend.agents.veritas_supervisor_agent import get_supervisor_agent

                self.supervisor_agent = await get_supervisor_agent(self.ollama_client)
                self._supervisor_initialization_pending = False
                logger.info("✅ SupervisorAgent initialized")
            except Exception as e:
                logger.error(f"❌ SupervisorAgent initialization failed: {e}")
                self._supervisor_initialization_pending = False

    def _map_inputs(self, input_mapping: Dict[str, str], context: PhaseExecutionContext) -> Dict[str, Any]:
        """
        Map input_mapping to actual values from context

        Example:
            input_mapping = {
                "query": "user_query",
                "missing_information": "phases.hypothesis.output.missing_information"
            }

            → {
                "query": "Brauche ich Baugenehmigung...",
                "missing_information": ["solar radiation", "cost estimate"]
            }

        Args:
            input_mapping: Mapping definition from phase config
            context: Phase execution context

        Returns:
            Mapped inputs dictionary
        """
        inputs = {}

        for key, path in input_mapping.items():
            try:
                if path == "user_query":
                    inputs[key] = context.user_query
                elif path == "rag_results":
                    inputs[key] = context.rag_results
                elif path.startswith("phases."):
                    # Navigate through previous phases
                    # Example: "phases.hypothesis.output.missing_information"
                    parts = path.split(".")
                    value = context.previous_phases

                    for part in parts[1:]:  # Skip "phases"
                        if isinstance(value, dict):
                            value = value.get(part)
                        elif hasattr(value, part):
                            value = getattr(value, part)
                        elif hasattr(value, "output") and part == "output":
                            value = value.output
                        else:
                            logger.warning(f"⚠️ Could not resolve path {path} at part '{part}'")
                            value = None
                            break

                    inputs[key] = value

                elif path.startswith("metadata."):
                    key_name = path.split(".", 1)[1]
                    inputs[key] = context.metadata.get(key_name)
                else:
                    logger.warning(f"⚠️ Unknown input path: {path}")
                    inputs[key] = None
            except Exception as e:
                logger.error(f"❌ Error mapping input {key} from {path}: {e}")
                inputs[key] = None

        return inputs

    def _infer_complexity(self, missing_information: List[str]) -> str:
        """
        Infer query complexity from missing_information

        Rules:
        - 0-1 items: "simple"
        - 2-3 items: "standard"
        - 4+ items: "complex"

        Args:
            missing_information: List of missing info items from hypothesis

        Returns:
            Complexity hint: "simple", "standard", or "complex"
        """
        if not missing_information:
            return "simple"

        count = len(missing_information)
        if count <= 1:
            return "simple"
        elif count <= 3:
            return "standard"
        else:
            return "complex"

    async def _execute_supervisor_phase(self, phase_config: Dict[str, Any], context: PhaseExecutionContext) -> PhaseResult:
        """
        Execute Supervisor-Phase (custom executor)

        Possible methods:
        - select_agents: Query Decomposition + Agent Selection (Phase 1.5)
        - synthesize_results: Final Answer Synthesis (Phase 6.5)

        Args:
            phase_config: Phase configuration from JSON
            context: Current execution context

        Returns:
            PhaseResult with supervisor output
        """
        await self._ensure_supervisor_initialized()

        if not self.supervisor_agent:
            logger.warning("⚠️ SupervisorAgent not available - skipping phase")
            return PhaseResult(
                phase_id=phase_config["phase_id"],
                status="skipped",
                output={"reason": "supervisor_not_available"},
                execution_time_ms=0,
                metadata={"executor": "supervisor", "skipped": True},
            )

        start_time = datetime.now()
        method = phase_config["execution"]["method"]
        input_mapping = phase_config.get("input_mapping", {})

        # Map inputs from context
        inputs = self._map_inputs(input_mapping, context)

        try:
            if method == "select_agents":
                # Phase 1.5: Agent Selection
                logger.info("🎯 Supervisor: Agent Selection started")

                # Decompose query into subqueries
                subqueries = await self.supervisor_agent.query_decomposer.decompose_query(
                    query_text=inputs.get("query", ""),
                    user_context=inputs.get("user_context", {}),
                    complexity_hint=self._infer_complexity(inputs.get("missing_information", [])),
                )

                # Create agent plan
                agent_plan = await self.supervisor_agent.create_agent_plan(
                    subqueries=subqueries, rag_context=inputs.get("rag_results", {})
                )

                # Format output
                output = {
                    "subqueries": [sq.to_dict() for sq in subqueries],
                    "agent_plan": agent_plan.to_dict(),
                    "selected_agents": [
                        {
                            "agent_type": a.agent_type,
                            "confidence_score": a.confidence_score,
                            "reason": a.reason,
                            "matching_capabilities": a.matching_capabilities,
                        }
                        for _, a in (agent_plan.parallel_agents + agent_plan.sequential_agents)
                    ],
                    "selection_reasoning": f"Selected {len(agent_plan.parallel_agents)} parallel + {len(agent_plan.sequential_agents)} sequential agents",
                }

                logger.info(
                    f"✅ Supervisor: {len(subqueries)} subqueries, "
                    f"{len(agent_plan.parallel_agents)} parallel agents, "
                    f"{len(agent_plan.sequential_agents)} sequential agents"
                )

            elif method == "synthesize_results":
                # Phase 6.5: Final Synthesis
                logger.info("🎯 Supervisor: Result Synthesis started")

                # Convert agent_results to AgentResult objects
                agent_results_dict = inputs.get("agent_results", {})
                agent_results = []

                for agent_type, result_data in agent_results_dict.items():
                    from backend.agents.veritas_supervisor_agent import AgentResult

                    agent_results.append(
                        AgentResult(
                            subquery_id=result_data.get("subquery_id", "unknown"),
                            agent_type=agent_type,
                            result_data=result_data,
                            confidence_score=result_data.get("confidence_score", 0.5),
                            processing_time=result_data.get("processing_time", 0.0),
                            sources=result_data.get("sources", []),
                        )
                    )

                # Synthesize results
                synthesized = await self.supervisor_agent.result_synthesizer.synthesize_results(
                    query_text=inputs.get("query", ""), agent_results=agent_results, rag_context=inputs.get("rag_results", {})
                )

                output = synthesized.to_dict()

                logger.info(
                    "✅ Supervisor: Synthesis complete, "
                    f"confidence={synthesized.confidence_score:.2f}, "
                    f"conflicts={len(synthesized.conflicts_detected)}"
                )

            else:
                raise ValueError(f"Unknown supervisor method: {method}")

            # Validate output against schema
            # Note: Validation happens in phase_executor if needed

            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            return PhaseResult(
                phase_id=phase_config["phase_id"],
                status="completed",
                output=output,
                execution_time_ms=execution_time_ms,
                metadata={"executor": "supervisor", "method": method},
            )

        except Exception as e:
            logger.error(f"❌ Supervisor phase failed: {e}")
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            return PhaseResult(
                phase_id=phase_config["phase_id"],
                status="failed",
                output={"error": str(e)},
                execution_time_ms=execution_time_ms,
                metadata={"executor": "supervisor", "method": method, "error": str(e)},
            )

    async def _execute_agent_coordination_phase(
        self, phase_config: Dict[str, Any], context: PhaseExecutionContext
    ) -> PhaseResult:
        """
        Execute Agent-Coordination-Phase (Phase 1.6)

        Uses existing AgentCoordinator to execute agents in parallel

        Args:
            phase_config: Phase configuration from JSON
            context: Current execution context

        Returns:
            PhaseResult with agent execution results
        """
        start_time = datetime.now()
        input_mapping = phase_config.get("input_mapping", {})
        inputs = self._map_inputs(input_mapping, context)

        agent_plan = inputs.get("agent_plan", {})
        subqueries = inputs.get("subqueries", [])

        # Check if agent_orchestrator is available
        if not self.agent_orchestrator:
            logger.warning("⚠️ AgentOrchestrator not available - using mock results")

            # Mock agent results
            mock_results = {}
            for agent in agent_plan.get("parallel_agents", []):
                agent_type = agent.get("agent_type") or agent.get("assignment", {}).get("agent_type")
                if agent_type:
                    mock_results[agent_type] = {
                        "summary": f"Mock result from {agent_type}",
                        "confidence_score": 0.7,
                        "processing_time": 0.1,
                        "sources": [],
                        "data": {},
                    }

            output = {
                "agent_results": mock_results,
                "execution_metadata": {
                    "total_agents_executed": len(mock_results),
                    "successful_agents": len(mock_results),
                    "failed_agents": 0,
                    "total_execution_time": 0.1,
                    "agent_execution_order": list(mock_results.keys()),
                },
            }

            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            return PhaseResult(
                phase_id=phase_config["phase_id"],
                status="completed",
                output=output,
                execution_time_ms=execution_time_ms,
                metadata={"executor": "agent_coordinator", "mock": True},
            )

        # Execute agents via AgentCoordinator
        try:
            from backend.agents.veritas_api_agent_core_components import create_agent_coordinator

            coordinator = create_agent_coordinator(orchestrator=self.agent_orchestrator)

            agent_results = {}
            successful = 0
            failed = 0
            execution_order = []

            # Execute parallel agents
            parallel_agents = agent_plan.get("parallel_agents", [])
            for agent_entry in parallel_agents:
                # Handle both dict formats from agent_plan
                if isinstance(agent_entry, dict):
                    if "assignment" in agent_entry:
                        assignment = agent_entry["assignment"]
                        subquery_id = agent_entry.get("subquery_id", "unknown")
                    else:
                        assignment = agent_entry
                        subquery_id = agent_entry.get("subquery_id", "unknown")
                else:
                    # Tuple format: (subquery_id, assignment)
                    subquery_id, assignment = agent_entry

                agent_type = assignment.get("agent_type") if isinstance(assignment, dict) else assignment.agent_type

                try:
                    logger.info(f"🤖 Executing agent: {agent_type}")

                    result = coordinator._execute_agent(
                        agent_type=agent_type,
                        query_data={
                            "query": inputs.get("user_query", ""),
                            "rag_context": inputs.get("rag_results", {}),
                            "subquery_id": subquery_id,
                        },
                        query_id=subquery_id,
                    )

                    agent_results[agent_type] = {
                        "summary": result.get("summary", str(result)),
                        "confidence_score": result.get("confidence_score", 0.7),
                        "processing_time": result.get("processing_time", 0.0),
                        "sources": result.get("sources", []),
                        "data": result,
                    }

                    successful += 1
                    execution_order.append(agent_type)
                    logger.info(f"✅ Agent {agent_type} completed")

                except Exception as e:
                    logger.error(f"❌ Agent {agent_type} failed: {e}")
                    failed += 1

            output = {
                "agent_results": agent_results,
                "execution_metadata": {
                    "total_agents_executed": successful + failed,
                    "successful_agents": successful,
                    "failed_agents": failed,
                    "total_execution_time": (datetime.now() - start_time).total_seconds(),
                    "agent_execution_order": execution_order,
                },
            }

            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(f"✅ Agent Coordination: {successful} successful, {failed} failed, " f"{execution_time_ms:.0f}ms")

            return PhaseResult(
                phase_id=phase_config["phase_id"],
                status="completed",
                output=output,
                execution_time_ms=execution_time_ms,
                metadata={"executor": "agent_coordinator"},
            )

        except Exception as e:
            logger.error(f"❌ Agent coordination failed: {e}")
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            return PhaseResult(
                phase_id=phase_config["phase_id"],
                status="failed",
                output={"error": str(e), "agent_results": {}},
                execution_time_ms=execution_time_ms,
                metadata={"executor": "agent_coordinator", "error": str(e)},
            )


# Example usage
async def example_usage():
    """
    Beispiel: Query Processing mit UnifiedOrchestratorV7
    """
    # Initialize orchestrator
    orchestrator = UnifiedOrchestratorV7(
        config_dir="config",
        method_id="default_method",
        ollama_client=None,  # Mock mode
        rag_service=None,  # Mock RAG
        enable_streaming=True,
    )

    # Test Query
    query = "Brauche ich eine Baugenehmigung für einen Carport in Baden-Württemberg?"

    print("\n" + "=" * 60)
    print("UNIFIED ORCHESTRATOR V7.0 - STREAMING TEST")
    print("=" * 60)
    print(f"Query: {query}\n")

    # Streaming execution
    async for event in orchestrator.process_query_stream(query):
        print(f"[{event.type:20s}] {event.to_ndjson()}")

    print("\n" + "=" * 60)
    print("STREAMING TEST COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(example_usage())
