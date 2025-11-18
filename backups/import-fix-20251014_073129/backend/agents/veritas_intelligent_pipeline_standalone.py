#!/usr/bin/env python3
"""
VERITAS INTELLIGENT PIPELINE - STANDALONE VERSION
================================================

Standalone Version der Intelligent Pipeline ohne komplexe Dependencies
Funktioniert vollständig im Mock-Modus für Testing

Author: VERITAS System
Date: 2025-09-28
Version: 1.0-standalone
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

# Projekt-Root für Paketimporte sicherstellen
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

# Shared Enums
from backend.agents.veritas_shared_enums import PipelineStage, QueryComplexity, QueryDomain, QueryStatus

# Ollama Client
try:
    from backend.agents.veritas_ollama_client import VeritasOllamaClient, get_ollama_client

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("⚠️ Ollama Client nicht verfügbar")

logger = logging.getLogger(__name__)

# ============================================================================
# STANDALONE PIPELINE DATASTRUKTUREN
# ============================================================================


@dataclass
class StandalonePipelineRequest:
    """Request für Standalone Pipeline"""

    query_id: str
    query_text: str
    user_context: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    enable_llm_commentary: bool = True
    timeout: int = 60


@dataclass
class StandalonePipelineResponse:
    """Response von Standalone Pipeline"""

    query_id: str
    session_id: str
    response_text: str
    confidence_score: float
    agent_results: Dict[str, Any] = field(default_factory=dict)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    llm_commentary: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============================================================================
# STANDALONE INTELLIGENT PIPELINE
# ============================================================================


class StandaloneIntelligentPipeline:
    """
    Standalone Intelligent Pipeline - funktioniert ohne externe Dependencies
    """

    def __init__(self):
        """Initialisiert die Standalone Pipeline"""
        self.ollama_client: Optional[VeritasOllamaClient] = None

        # Statistics
        self.stats = {
            "pipelines_processed": 0,
            "successful_pipelines": 0,
            "failed_pipelines": 0,
            "llm_comments_generated": 0,
        }

        logger.info("🧠 Standalone Intelligent Pipeline initialisiert")

    async def initialize(self) -> bool:
        """Initialisiert Pipeline-Komponenten"""
        try:
            if OLLAMA_AVAILABLE:
                self.ollama_client = await get_ollama_client()
                logger.info("✅ Ollama Client initialisiert")
            else:
                logger.info("ℹ️ Läuft im Mock-Modus ohne Ollama")

            return True
        except Exception as e:
            logger.warning(f"⚠️ Initialisierung mit Warnings: {e}")
            return True  # Läuft trotzdem im Mock-Modus

    async def process_query(
        self,
        request: StandalonePipelineRequest,
        comment_callback: Optional[Callable[[PipelineStage, str], Awaitable[None]]] = None,
    ) -> StandalonePipelineResponse:
        """Verarbeitet Query durch Standalone Pipeline"""
        start_time = time.time()
        llm_comments = []

        try:
            # STEP 1: Query Analysis
            await self._append_comment(
                PipelineStage.QUERY_ANALYSIS,
                "Ich ordne Ihre Frage thematisch ein und prüfe, welche Wissensbereiche involviert sind.",
                llm_comments,
                comment_callback,
                request.query_text,
                {"user_context": request.user_context},
            )
            await asyncio.sleep(0.5)  # Simulate processing

            analysis = await self._analyze_query(request.query_text)

            # STEP 2: RAG Search Simulation
            await asyncio.sleep(1.0)
            rag_results = self._simulate_rag_search(request.query_text)
            await self._append_comment(
                PipelineStage.RAG_SEARCH,
                "Ich gehe Ihre Wissensquellen durch und prüfe, welche Dokumente konkret zu Ihrer Frage passen.",
                llm_comments,
                comment_callback,
                request.query_text,
                {"rag_candidates": rag_results},
            )

            # STEP 3: Agent Selection
            await self._append_comment(
                PipelineStage.AGENT_SELECTION,
                "Ich entscheide, welche Spezialagenten den fehlenden Kontext am besten abdecken können.",
                llm_comments,
                comment_callback,
                request.query_text,
                {"analysis": analysis, "rag_summary": rag_results.get("documents", [])},
            )
            await asyncio.sleep(0.5)

            selected_agents = self._select_agents(analysis, rag_results)

            # STEP 4: Agent Execution
            await self._append_comment(
                PipelineStage.AGENT_EXECUTION,
                "Ich lasse die ausgewählten Agenten gezielt Antworten zusammenstellen und prüfe ihre Evidenzen.",
                llm_comments,
                comment_callback,
                request.query_text,
                {"active_agents": selected_agents},
            )
            await asyncio.sleep(2.0)

            agent_results = self._execute_agents(selected_agents, request.query_text)

            # STEP 5: Result Synthesis
            await self._append_comment(
                PipelineStage.RESULT_AGGREGATION,
                "Ich vergleiche die Agentenergebnisse miteinander, notiere offene Punkte und priorisiere belastbare Quellen.",
                llm_comments,
                comment_callback,
                request.query_text,
                {"agent_results": agent_results},
            )
            await asyncio.sleep(1.0)

            final_response = await self._synthesize_response(request.query_text, agent_results, rag_results)

            # Success
            processing_time = time.time() - start_time
            self.stats["pipelines_processed"] += 1
            self.stats["successful_pipelines"] += 1
            self.stats["llm_comments_generated"] += len(llm_comments)

            return StandalonePipelineResponse(
                query_id=request.query_id,
                session_id=request.session_id or str(uuid.uuid4()),
                response_text=final_response["response_text"],
                confidence_score=final_response["confidence_score"],
                agent_results=agent_results,
                sources=final_response["sources"],
                llm_commentary=llm_comments,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"❌ Pipeline Fehler: {e}")
            self.stats["failed_pipelines"] += 1

            return StandalonePipelineResponse(
                query_id=request.query_id,
                session_id=request.session_id or str(uuid.uuid4()),
                response_text=f"Entschuldigung, bei der Verarbeitung ist ein Fehler aufgetreten: {str(e)}",
                confidence_score=0.0,
                processing_time=time.time() - start_time,
            )

    async def _generate_comment(
        self, stage: PipelineStage, default_comment: str, query_text: str, context_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generiert LLM-Kommentar oder Fallback"""
        if self.ollama_client:
            try:
                return await self.ollama_client.comment_pipeline_step(
                    stage.value,
                    {"status": "active", "stage": stage.value, "query_excerpt": query_text[:160]},
                    {"original_query": query_text, "stage_context": context_data or {}},
                )
            except:
                pass
        return default_comment

    async def _append_comment(
        self,
        stage: PipelineStage,
        default_comment: str,
        llm_comments: List[str],
        comment_callback: Optional[Callable[[PipelineStage, str], Awaitable[None]]],
        query_text: str,
        context_data: Optional[Dict[str, Any]] = None,
    ):
        """Hilfsmethode, um Kommentar zu erzeugen und Callback auszulösen"""
        comment = await self._generate_comment(stage, default_comment, query_text, context_data)
        llm_comments.append(comment)

        if comment_callback:
            try:
                callback_result = comment_callback(stage, comment)
                if asyncio.iscoroutine(callback_result):
                    await callback_result
            except Exception as exc:
                logger.warning(f"⚠️ Kommentar-Callback fehlgeschlagen ({stage.value}): {exc}")

        return comment

    async def _analyze_query(self, query_text: str) -> Dict[str, Any]:
        """Query-Analyse"""
        if self.ollama_client:
            try:
                return await self.ollama_client.analyze_query(query_text)
            except:
                pass

        # Fallback Analysis
        query_lower = query_text.lower()

        if any(word in query_lower for word in ["komplex", "vergleich", "analyse"]):
            complexity = QueryComplexity.ADVANCED
        elif any(word in query_lower for word in ["wie", "was", "welche"]):
            complexity = QueryComplexity.STANDARD
        else:
            complexity = QueryComplexity.BASIC

        if any(word in query_lower for word in ["umwelt", "luft", "lärm"]):
            domain = QueryDomain.ENVIRONMENTAL
        elif any(word in query_lower for word in ["bau", "genehmigung"]):
            domain = QueryDomain.BUILDING
        else:
            domain = QueryDomain.GENERAL

        return {
            "complexity": complexity.value,
            "domain": domain.value,
            "required_agents": ["environmental", "legal_framework", "document_retrieval"],
        }

    def _simulate_rag_search(self, query_text: str) -> Dict[str, Any]:
        """Simuliert RAG-Suche"""
        return {
            "documents": [
                {"title": f"Relevantes Dokument zu '{query_text[:30]}...'", "relevance": 0.85},
                {"title": "Rechtliche Bestimmungen", "relevance": 0.78},
                {"title": "Verfahrenshinweise", "relevance": 0.72},
            ],
            "total_found": 3,
        }

    def _select_agents(self, analysis: Dict[str, Any], rag_results: Dict[str, Any]) -> List[str]:
        """Wählt Agents basierend auf Analyse"""
        domain = analysis.get("domain", "general")
        complexity = analysis.get("complexity", "standard")

        agents = ["legal_framework", "document_retrieval"]

        if domain == "environmental":
            agents.append("environmental")
        elif domain == "building":
            agents.append("construction")
        else:
            agents.append("general_info")

        if complexity == "advanced":
            agents.append("external_api")

        return agents[:4]  # Max 4 Agents

    def _execute_agents(self, agents: List[str], query_text: str) -> Dict[str, Any]:
        """Simuliert Agent-Execution"""
        results = {}

        for agent in agents:
            results[agent] = {
                "agent_type": agent,
                "status": "completed",
                "confidence_score": 0.75 + (hash(agent + query_text) % 20) / 100,
                "summary": f"{agent.title()}-Agent: Analyse abgeschlossen",
                "sources": [f"{agent}-Quelle-1", f"{agent}-Quelle-2"],
                "processing_time": 1.5 + (hash(agent) % 10) / 10,
            }

        return results

    async def _synthesize_response(
        self, query_text: str, agent_results: Dict[str, Any], rag_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthetisiert finale Antwort"""

        if self.ollama_client:
            try:
                synthesis = await self.ollama_client.synthesize_agent_results(query_text, agent_results, rag_results)
                if synthesis.get("response_text"):
                    return {
                        "response_text": synthesis["response_text"],
                        "confidence_score": synthesis.get("confidence_score", 0.8),
                        "sources": self._extract_sources(agent_results, rag_results),
                    }
            except:
                pass

        # Fallback Synthesis
        agent_summaries = []
        for agent, result in agent_results.items():
            agent_summaries.append(f"**{agent.title()}**: {result['summary']}")

        response_text = f"""**Antwort auf Ihre Frage**: {query_text}

**Zusammenfassung der Analyse**:

{chr(10).join(agent_summaries)}

**Basierend auf der Analyse** durch {len(agent_results)} spezialisierte Agenten können wir Ihnen eine umfassende Antwort liefern. Die gefundenen Informationen wurden aus {rag_results.get('total_found', 0)} relevanten Dokumenten zusammengestellt.

**Nächste Schritte**: Wenden Sie sich für weitere Details an die entsprechenden Fachbereiche oder nutzen Sie die bereitgestellten Quellen für vertiefende Informationen."""

        avg_confidence = sum(r["confidence_score"] for r in agent_results.values()) / len(agent_results)

        return {
            "response_text": response_text,
            "confidence_score": avg_confidence,
            "sources": self._extract_sources(agent_results, rag_results),
        }

    def _extract_sources(self, agent_results: Dict[str, Any], rag_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrahiert Quellen"""
        sources = []

        # RAG Sources
        for doc in rag_results.get("documents", []):
            sources.append({"title": doc["title"], "type": "document", "relevance": doc["relevance"]})

        # Agent Sources
        for agent, result in agent_results.items():
            for source in result.get("sources", []):
                sources.append(
                    {"title": source, "type": "agent_source", "agent": agent, "relevance": result.get("confidence_score", 0.8)}
                )

        return sources[:10]

    def get_statistics(self) -> Dict[str, Any]:
        """Liefert Pipeline-Statistiken"""
        success_rate = (self.stats["successful_pipelines"] / max(self.stats["pipelines_processed"], 1)) * 100

        return {
            "stats": self.stats.copy(),
            "success_rate_percent": round(success_rate, 2),
            "ollama_available": self.ollama_client is not None,
        }


# ============================================================================
# GLOBAL ACCESS
# ============================================================================

_global_standalone_pipeline: Optional[StandaloneIntelligentPipeline] = None


async def get_standalone_pipeline() -> StandaloneIntelligentPipeline:
    """Liefert globale Standalone Pipeline Instanz"""
    global _global_standalone_pipeline

    if _global_standalone_pipeline is None:
        _global_standalone_pipeline = StandaloneIntelligentPipeline()
        await _global_standalone_pipeline.initialize()

    return _global_standalone_pipeline


# ============================================================================
# MAIN FOR TESTING
# ============================================================================


async def main():
    """Test der Standalone Pipeline"""

    pipeline = await get_standalone_pipeline()

    print("🧠 Standalone Intelligent Pipeline Test")
    print("=" * 50)

    # Test Request
    request = StandalonePipelineRequest(
        query_id=str(uuid.uuid4()),
        query_text="Wie ist die Luftqualität in München und welche Behörden sind zuständig?",
        user_context={"location": "München"},
        enable_llm_commentary=True,
    )

    print(f"Query: {request.query_text}")
    print(f"Query ID: {request.query_id}")

    async def on_comment(stage: PipelineStage, comment: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {stage.name}: {comment}")

    # Pipeline ausführen
    response = await pipeline.process_query(request, comment_callback=on_comment)

    print(f"\n📋 Pipeline Response:")
    print(f"Confidence Score: {response.confidence_score:.2f}")
    print(f"Processing Time: {response.processing_time:.2f}s")
    print(f"Agents Used: {len(response.agent_results)}")
    print(f"Sources Found: {len(response.sources)}")
    print(f"LLM Comments: {len(response.llm_commentary)}")

    print(f"\n💬 LLM Commentary:")
    for i, comment in enumerate(response.llm_commentary, 1):
        print(f"{i}. {comment}")

    print(f"\n📊 Response Preview:")
    preview = response.response_text[:300] + "..." if len(response.response_text) > 300 else response.response_text
    print(preview)

    # Statistics
    stats = pipeline.get_statistics()
    print(f"\n📈 Pipeline Statistics:")
    print(f"Success Rate: {stats['success_rate_percent']}%")
    print(f"LLM Comments Generated: {stats['stats']['llm_comments_generated']}")


if __name__ == "__main__":
    asyncio.run(main())
