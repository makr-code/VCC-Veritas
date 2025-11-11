"""
VERITAS SUPERVISOR AGENT - MESSAGE-BASED EXTENSION
===================================================

Erweitert SupervisorAgent um Message-basierte Agent-Koordination.

NEUE FEATURES (Phase 4):
- Message-Broker Integration für Agent-Kommunikation
- Message-basierte SubQuery-Distribution
- Async Result-Collection via Message-Responses
- Agent-Status-Monitoring via Events
- Context-Sharing zwischen koordinierten Agenten

Version: 2.0 (Phase 4 Extension)
Author: VERITAS Development Team
Date: 6. Oktober 2025
"""

import asyncio
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add project root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

# VERITAS Imports
try:
    from backend.agents.agent_message_broker import AgentMessageBroker
    from backend.agents.veritas_supervisor_agent import (
        AgentAssignment,
        AgentExecutionPlan,
        AgentResult,
        AgentSelector,
        QueryDecomposer,
        ResultSynthesizer,
        SubQuery,
        SupervisorAgent,
        SynthesizedResult,
    )
    from shared.mixins.agent_communication_mixin import AgentCommunicationMixin
    from shared.protocols.agent_message import (
        AgentIdentity,
        AgentMessage,
        MessagePriority,
        MessageType,
        create_request_message,
    )
except ImportError as e:
    logger.error(f"Import-Fehler: {e}")
    raise

logger = logging.getLogger(__name__)


# ============================================================================
# MESSAGE-BASED SUPERVISOR AGENT
# ============================================================================


class MessageBasedSupervisorAgent(AgentCommunicationMixin):
    """
    SupervisorAgent mit Message-basierter Agent-Koordination

    Erweitert die Standard-Supervisor-Funktionalität um:
    - Message-Broker Integration
    - Async Message-basierte SubQuery-Distribution
    - Message-Response-basierte Result-Collection
    - Event-basiertes Agent-Status-Monitoring
    - Context-Sharing zwischen koordinierten Agenten

    Workflow:
    1. Query dekomponieren (wie zuvor)
    2. Agenten auswählen (wie zuvor)
    3. SubQueries via Messages an Agenten verteilen (NEU)
    4. Parallel auf Message-Responses warten (NEU)
    5. Ergebnisse synthetisieren (wie zuvor)
    6. Optional: Context-Sharing zwischen Agenten (NEU)

    Example:
        >>> broker = AgentMessageBroker()
        >>> await broker.start()
        >>>
        >>> supervisor = MessageBasedSupervisorAgent(
        ...     broker=broker,
        ...     query_decomposer=QueryDecomposer(),
        ...     agent_selector=AgentSelector(),
        ...     result_synthesizer=ResultSynthesizer()
        ... )
        >>>
        >>> result = await supervisor.process_query_with_messages(
        ...     query="Bauvorhaben in Berlin-Mitte: Umweltauflagen und Kosten?",
        ...     user_context={"location": "Berlin - Mitte"}
        ... )
    """

    def __init__(
        self,
        broker: AgentMessageBroker,
        query_decomposer: QueryDecomposer,
        agent_selector: AgentSelector,
        result_synthesizer: ResultSynthesizer,
        enable_context_sharing: bool = True,
    ):
        """
        Initialisiert Message-based Supervisor

        Args:
            broker: AgentMessageBroker-Instanz
            query_decomposer: QueryDecomposer für Query-Zerlegung
            agent_selector: AgentSelector für Agent-Auswahl
            result_synthesizer: ResultSynthesizer für Ergebnis-Aggregation
            enable_context_sharing: Aktiviert Context-Sharing zwischen Agenten
        """
        # Supervisor-Identität erstellen
        identity = AgentIdentity(
            agent_id="supervisor-agent-001",
            agent_type="supervisor",
            agent_name="VERITAS Supervisor Agent (Message-Based)",
            capabilities=[
                "query_decomposition",
                "agent_coordination",
                "result_synthesis",
                "context_orchestration",
                "message_based_routing",
            ],
        )

        # AgentCommunicationMixin initialisieren
        super().__init__(broker, identity)

        # Core-Komponenten
        self.query_decomposer = query_decomposer
        self.agent_selector = agent_selector
        self.result_synthesizer = result_synthesizer

        # Configuration
        self.enable_context_sharing = enable_context_sharing

        # Statistics
        self.stats = {
            "queries_processed": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "subqueries_distributed": 0,
            "agents_coordinated": 0,
            "contexts_shared": 0,
            "avg_response_time_ms": 0.0,
            "success_rate": 0.0,
        }

        # Custom Message-Handler registrieren
        self.register_message_handler(MessageType.STATUS_UPDATE, self._handle_agent_status)

        logger.info("🎯 Message-Based SupervisorAgent initialisiert")

    # ========================================================================
    # MAIN QUERY PROCESSING (MESSAGE-BASED)
    # ========================================================================

    async def process_query_with_messages(
        self, query: str, user_context: Optional[Dict[str, Any]] = None, timeout_per_agent: float = 60.0
    ) -> Dict[str, Any]:
        """
        Verarbeitet Query mit Message-basierter Agent-Koordination

        Args:
            query: User-Query
            user_context: Kontext-Informationen
            timeout_per_agent: Timeout pro Agent in Sekunden

        Returns:
            Dict mit final_answer, confidence_score, sources, metadata

        Workflow:
        1. Query dekomponieren → SubQueries
        2. Agenten auswählen → AgentExecutionPlan
        3. SubQueries via Messages verteilen
        4. Parallel auf Responses warten
        5. Optional: Context zwischen Agenten teilen
        6. Ergebnisse synthetisieren
        """
        start_time = datetime.now()
        logger.info(f"🎯 Supervisor verarbeitet Query (Message-Protokoll): {query[:100]}...")

        if user_context is None:
            user_context = {}

        try:
            # Step 1: Query dekomponieren
            logger.info("📋 Step 1: Query-Dekomposition")
            subqueries = await self.query_decomposer.decompose_query(query, user_context)
            logger.info(f"   ✅ {len(subqueries)} SubQueries erstellt")

            # Step 2: Agenten auswählen
            logger.info("🤖 Step 2: Agent-Selektion")
            agent_plan = await self.agent_selector.create_agent_plan(subqueries, user_context)
            logger.info(f"   ✅ Agent-Plan erstellt: {len(agent_plan.assignments)} Assignments")

            # Step 3: SubQueries via Messages verteilen
            logger.info("📤 Step 3: Message-basierte SubQuery-Distribution")
            results = await self._distribute_subqueries_via_messages(
                agent_plan=agent_plan, subqueries=subqueries, user_context=user_context, timeout_per_agent=timeout_per_agent
            )
            logger.info(f"   ✅ {len(results)} Agent-Responses erhalten")

            # Step 4: Optional Context-Sharing
            if self.enable_context_sharing and len(results) > 1:
                logger.info("🔄 Step 4: Context-Sharing zwischen Agenten")
                await self._share_contexts_between_agents(results)
                logger.info(f"   ✅ Context geteilt ({self.stats['contexts_shared']} Shares)")

            # Step 5: Ergebnisse synthetisieren
            logger.info("🧬 Step 5: Ergebnis-Synthese")
            agent_results = self._convert_to_agent_results(results)
            synthesized = await self.result_synthesizer.synthesize_results(
                query=query, agent_results=agent_results, user_context=user_context
            )
            logger.info(f"   ✅ Synthese abgeschlossen (Confidence: {synthesized.confidence_score:.2f})")

            # Statistics
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.stats["queries_processed"] += 1
            self.stats["subqueries_distributed"] += len(subqueries)
            self.stats["agents_coordinated"] += len(results)
            self.stats["avg_response_time_ms"] = (
                self.stats["avg_response_time_ms"] * (self.stats["queries_processed"] - 1) + elapsed_ms
            ) / self.stats["queries_processed"]

            logger.info(f"✅ Query erfolgreich verarbeitet (Message-Protokoll, {elapsed_ms:.0f}ms)")

            return {
                "final_answer": synthesized.final_answer,
                "confidence_score": synthesized.confidence_score,
                "sources": synthesized.sources,
                "metadata": {
                    "subqueries": len(subqueries),
                    "agents_used": len(results),
                    "protocol": "message_based",
                    "response_time_ms": elapsed_ms,
                    "context_sharing_enabled": self.enable_context_sharing,
                },
            }

        except Exception as e:
            logger.error(f"❌ Fehler bei Message-basierter Query-Verarbeitung: {e}", exc_info=True)
            return {
                "final_answer": f"Fehler bei der Verarbeitung: {str(e)}",
                "confidence_score": 0.0,
                "sources": [],
                "metadata": {"error": str(e), "protocol": "message_based", "status": "failed"},
            }

    # ========================================================================
    # MESSAGE-BASED SUBQUERY DISTRIBUTION
    # ========================================================================

    async def _distribute_subqueries_via_messages(
        self,
        agent_plan: AgentExecutionPlan,
        subqueries: List[SubQuery],
        user_context: Dict[str, Any],
        timeout_per_agent: float,
    ) -> List[Dict[str, Any]]:
        """
        Verteilt SubQueries via Messages an Agenten

        Args:
            agent_plan: AgentExecutionPlan mit Assignments
            subqueries: Liste von SubQueries
            user_context: Kontext-Informationen
            timeout_per_agent: Timeout pro Agent

        Returns:
            Liste von Agent-Responses
        """
        # Map: subquery_id -> SubQuery
        subquery_map = {sq.id: sq for sq in subqueries}

        # Tasks für parallele Message-Distribution erstellen
        tasks = []
        for assignment in agent_plan.assignments:
            subquery = subquery_map.get(assignment.subquery.id)
            if not subquery:
                logger.warning(f"⚠️ SubQuery {assignment.subquery.id} nicht gefunden")
                continue

            # Agent-Identity aus Broker-Registry holen
            agent_identity = self._get_agent_identity_by_type(assignment.agent_type)

            if agent_identity:
                task = self._send_subquery_request(
                    agent_identity=agent_identity,
                    subquery=subquery,
                    assignment=assignment,
                    user_context=user_context,
                    timeout=timeout_per_agent,
                )
                tasks.append((assignment.agent_type, subquery.id, task))
            else:
                logger.warning(f"⚠️ Agent-Identity für {assignment.agent_type} nicht gefunden")

        # Parallel auf Responses warten
        results = []
        for agent_type, subquery_id, task in tasks:
            try:
                response = await task
                if response:
                    results.append(
                        {
                            "agent_type": agent_type,
                            "subquery_id": subquery_id,
                            "result_data": response.get("result", {}),
                            "status": "completed",
                            "confidence_score": response.get("confidence", 0.8),
                            "metadata": response.get("metadata", {}),
                        }
                    )
                    self.stats["messages_received"] += 1
                else:
                    logger.warning(f"⚠️ Timeout bei Agent {agent_type} für SubQuery {subquery_id}")
                    results.append(
                        {
                            "agent_type": agent_type,
                            "subquery_id": subquery_id,
                            "result_data": {"error": "timeout"},
                            "status": "timeout",
                            "confidence_score": 0.0,
                            "metadata": {},
                        }
                    )
            except Exception as e:
                logger.error(f"❌ Fehler bei Agent {agent_type}: {e}")
                results.append(
                    {
                        "agent_type": agent_type,
                        "subquery_id": subquery_id,
                        "result_data": {"error": str(e)},
                        "status": "failed",
                        "confidence_score": 0.0,
                        "metadata": {},
                    }
                )

        return results

    async def _send_subquery_request(
        self,
        agent_identity: AgentIdentity,
        subquery: SubQuery,
        assignment: AgentAssignment,
        user_context: Dict[str, Any],
        timeout: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Sendet SubQuery-Request an einen Agenten

        Args:
            agent_identity: Agent-Identität
            subquery: SubQuery
            assignment: AgentAssignment
            user_context: Kontext
            timeout: Timeout

        Returns:
            Response-Payload oder None
        """
        payload = {
            "subquery": subquery.query_text,
            "subquery_id": subquery.id,
            "query_type": subquery.query_type,
            "priority": subquery.priority,
            "context": user_context,
            "expected_capabilities": assignment.required_capabilities,
            "assignment_metadata": assignment.metadata,
        }

        logger.debug(f"📤 Sende SubQuery an {agent_identity.agent_type}: {subquery.query_text[:50]}...")

        response = await self.send_request(
            recipient=agent_identity,
            payload=payload,
            timeout=timeout,
            priority=MessagePriority.HIGH if subquery.priority > 0.7 else MessagePriority.NORMAL,
        )

        self.stats["messages_sent"] += 1

        return response

    # ========================================================================
    # CONTEXT-SHARING
    # ========================================================================

    async def _share_contexts_between_agents(self, results: List[Dict[str, Any]]):
        """
        Teilt Contexts zwischen koordinierten Agenten

        Beispiel: Environmental-Agent teilt Geographic-Context mit Construction-Agent

        Args:
            results: Liste von Agent-Results
        """
        # Identify agents that produced useful context
        context_producers = [r for r in results if r["status"] == "completed" and r["confidence_score"] > 0.7]

        if len(context_producers) < 2:
            return  # Kein Context-Sharing nötig

        # Share contexts pairwise
        for i, producer in enumerate(context_producers):
            for consumer in context_producers[i + 1 :]:
                # Skip if same agent type
                if producer["agent_type"] == consumer["agent_type"]:
                    continue

                # Get agent identities
                producer_identity = self._get_agent_identity_by_type(producer["agent_type"])
                consumer_identity = self._get_agent_identity_by_type(consumer["agent_type"])

                if producer_identity and consumer_identity:
                    # Extract relevant context
                    context_data = {
                        "source_agent": producer["agent_type"],
                        "subquery_id": producer["subquery_id"],
                        "result_summary": str(producer["result_data"])[:200],  # Truncated
                        "confidence": producer["confidence_score"],
                        "metadata": producer.get("metadata", {}),
                    }

                    # Share via CONTEXT_SHARE message (fire-and-forget)
                    await self.share_context(
                        recipient=consumer_identity,
                        context_data=context_data,
                        context_type=f"{producer['agent_type']}_context",
                    )

                    self.stats["contexts_shared"] += 1
                    logger.debug(f"🔄 Context geteilt: {producer['agent_type']} → {consumer['agent_type']}")

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _get_agent_identity_by_type(self, agent_type: str) -> Optional[AgentIdentity]:
        """
        Holt Agent-Identity aus Broker-Registry by Agent-Type

        Args:
            agent_type: Agent-Typ (z.B. "environmental", "financial")

        Returns:
            AgentIdentity oder None
        """
        for agent_id, identity in self.broker._agents.items():
            if identity.agent_type == agent_type:
                return identity
        return None

    def _convert_to_agent_results(self, results: List[Dict[str, Any]]) -> List[AgentResult]:
        """
        Konvertiert Message-Responses zu AgentResult-Objekten

        Args:
            results: Liste von Message-Response-Dicts

        Returns:
            Liste von AgentResult-Objekten
        """
        agent_results = []
        for r in results:
            agent_result = AgentResult(
                agent_type=r["agent_type"],
                result_data=r["result_data"],
                status=r["status"],
                confidence_score=r["confidence_score"],
                processing_time_ms=r.get("metadata", {}).get("processing_time_ms", 0.0),
                metadata=r.get("metadata", {}),
            )
            agent_results.append(agent_result)

        return agent_results

    async def _handle_agent_status(self, message: AgentMessage) -> None:
        """
        Handler für Agent-Status-Updates

        Args:
            message: STATUS_UPDATE Message
        """
        agent_type = message.sender.agent_type
        status = message.payload.get("status", "unknown")
        logger.info(f"📊 Agent-Status-Update: {agent_type} → {status}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Liefert Supervisor-Statistiken

        Returns:
            Dict mit Statistiken
        """
        return {**self.stats, "broker_stats": self.broker.get_stats()}


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


def create_message_based_supervisor(
    broker: AgentMessageBroker, ollama_client: Optional[Any] = None, enable_context_sharing: bool = True
) -> MessageBasedSupervisorAgent:
    """
    Factory-Funktion zum Erstellen eines Message-based Supervisor

    Args:
        broker: AgentMessageBroker-Instanz
        ollama_client: Optional OllamaClient (wird für Decomposition/Synthesis benötigt)
        enable_context_sharing: Aktiviert Context-Sharing

    Returns:
        MessageBasedSupervisorAgent-Instanz
    """
    # Import core components
    from backend.agents.veritas_supervisor_agent import AgentSelector, QueryDecomposer, ResultSynthesizer

    # Create components
    query_decomposer = QueryDecomposer(ollama_client=ollama_client)
    agent_selector = AgentSelector()
    result_synthesizer = ResultSynthesizer(ollama_client=ollama_client)

    # Create supervisor
    supervisor = MessageBasedSupervisorAgent(
        broker=broker,
        query_decomposer=query_decomposer,
        agent_selector=agent_selector,
        result_synthesizer=result_synthesizer,
        enable_context_sharing=enable_context_sharing,
    )

    logger.info("✅ Message-based SupervisorAgent erstellt")

    return supervisor


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import logging

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    print("=" * 80)
    print("VERITAS Message-Based Supervisor Agent - Test")
    print("=" * 80)

    async def test_message_supervisor():
        """Test Message-based Supervisor"""

        # Test 1: Broker & Supervisor erstellen
        print("\n[Test 1] Broker & Supervisor erstellen:")
        broker = AgentMessageBroker()
        await broker.start()

        supervisor = create_message_based_supervisor(broker=broker, enable_context_sharing=True)

        print(f"✅ Supervisor erstellt: {supervisor.identity.agent_name}")

        # Test 2: Mock-Agents registrieren
        print("\n[Test 2] Mock-Agents registrieren:")

        # Environmental Agent Mock
        env_agent = AgentIdentity(
            agent_id="env-agent-test",
            agent_type="environmental",
            agent_name="Test Environmental Agent",
            capabilities=["environmental_analysis"],
        )

        async def env_handler(msg: AgentMessage) -> Optional[Dict[str, Any]]:
            if msg.is_request():
                await asyncio.sleep(0.1)  # Simulate work
                return {"result": {"environmental_assessment": "Good", "terrain": "urban"}, "confidence": 0.95}
            return None

        broker.register_agent(env_agent, env_handler)

        # Financial Agent Mock
        fin_agent = AgentIdentity(
            agent_id="fin-agent-test",
            agent_type="financial",
            agent_name="Test Financial Agent",
            capabilities=["financial_analysis"],
        )

        async def fin_handler(msg: AgentMessage) -> Optional[Dict[str, Any]]:
            if msg.is_request():
                await asyncio.sleep(0.1)  # Simulate work
                return {"result": {"total_cost": 1500000, "currency": "EUR"}, "confidence": 0.92}
            return None

        broker.register_agent(fin_agent, fin_handler)

        print("✅ 2 Mock-Agents registriert")

        # Test 3: Query verarbeiten (würde SubQuery-Distribution testen)
        print("\n[Test 3] Query-Verarbeitung (Mock):")
        print("   ℹ️ Volle Integration benötigt QueryDecomposer mit LLM")
        print("   ℹ️ Für vollständigen Test siehe Integration-Tests")

        # Test 4: Statistics
        print("\n[Test 4] Statistiken:")
        stats = supervisor.get_statistics()
        print(f"   Queries processed: {stats['queries_processed']}")
        print(f"   Messages sent: {stats['messages_sent']}")
        print(f"   Agents registered: {stats['broker_stats']['agents_registered']}")
        print("✅ Statistiken abgerufen")

        # Test 5: Cleanup
        print("\n[Test 5] Cleanup:")
        supervisor.cleanup()
        await broker.stop()
        print(f"✅ Cleanup durchgeführt")

        print("\n" + "=" * 80)
        print("✅ Basis-Tests erfolgreich!")
        print("=" * 80)

    # Run async tests
    asyncio.run(test_message_supervisor())
