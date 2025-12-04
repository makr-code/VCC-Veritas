#!/usr/bin/env python3
"""
ConstructionAgent für VERITAS - BaseAgent Framework v2.0

Spezialisierter Agent für Bau- und Stadtplanungsanfragen.
Migriert vom Legacy-System zum modernen VERITAS Framework.

Capabilities:
- Baugenehmigungen und Baurecht
- Zoniering und Flächennutzung
- Baubeschränkungen und Vorschriften
- Bauvorhaben-Analysen
- Nachbarschaftsrecht
- Denkmalschutz

Framework Features:
✅ BaseAgent inheritance - Framework integration
✅ Registry support - Automatic discovery & lifecycle management
✅ Async processing - Non-blocking query processing
✅ Monitoring - Performance metrics & health tracking
✅ Quality gates - Result validation & confidence scoring
✅ Retry logic - Automatic error handling & recovery

Migration: 2025-12-04
Author: VERITAS Framework Migration v2.0
Version: 2.0 (Framework)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

from backend.agents.framework.agent_monitoring import AgentMonitor

# Framework Imports
from backend.agents.framework.base_agent import BaseAgent
from backend.agents.framework.quality_gate import QualityGate, QualityPolicy
from backend.agents.framework.retry_handler import RetryConfig, RetryHandler
from backend.agents.registry.api_agent_registry import AgentCapability, AgentLifecycleType, get_agent_registry

logger = logging.getLogger(__name__)


# ===== CONSTRUCTION AGENT =====


class ConstructionAgent(BaseAgent):
    """
    Spezialisierter Agent für Bau- und Stadtplanungsrecht.
    Verarbeitet Anfragen zu Baugenehmigungen, Zonierung und Bauvorhaben.
    """

    AGENT_TYPE = "construction"

    def __init__(self, agent_id: Optional[str] = None):
        """Initialize Construction Agent with framework components."""
        super().__init__(agent_id=agent_id)

        # Framework Components
        self.monitor = AgentMonitor(self.AGENT_TYPE)
        # Quality Gate with policy
        policy = QualityPolicy(min_quality=0.6, target_quality=0.8)
        self.quality_gate = QualityGate(policy)
        retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)

        # Knowledge Base for Construction & Urban Planning
        self.knowledge_base = {
            "baugenehmigung": "Baugenehmigungen sind behördliche Genehmigungen für Bauvorhaben nach BauOrdnung",
            "baurecht": "Baurecht regelt die Zulässigkeit von Bauvorhaben durch Zoniierung und Flächennutzungspläne",
            "zoniering": "Zoniering teilt Flächen in Zonen ein (Wohngebiet, Gewerbegebiet, Mischgebiet, etc.)",
            "baubeschraenkung": "Baubeschränkungen entstehen durch Denkmalschutz, Naturschutz oder Nachbarschaftsrecht",
            "flaechennutzungsplan": "Flächennutzungspläne definieren die zukünftige Nutzung von Stadtflächen",
            "bebauungsplan": "Bebauungspläne regeln konkret Nutzung, Größe und Gestalt von Bauvorhaben",
            "nachbarschaftsrecht": "Nachbarschaftsrecht schützt Nachbarn vor Beeinträchtigung durch Bauvorhaben",
            "denkmalschutz": "Denkmalschutz schützt historisch oder künstlerisch wertvolle Bauwerke",
            "bauvorhaben_analyse": "Analyse der Zulässigkeit von Bauvorhaben nach Zonierung und Rechtslage",
            "erschliessung": "Erschließung regelt Zugang zu Ver- und Entsorgungsnetzen für Baugrundstücke",
        }

        # Known Locations for Testing
        self.known_locations = {
            "münchen": {"lat": 48.1351, "lon": 11.5820, "state": "Bayern"},
            "berlin": {"lat": 52.5200, "lon": 13.4050, "state": "Berlin"},
            "hamburg": {"lat": 53.5511, "lon": 9.9937, "state": "Hamburg"},
            "frankfurt": {"lat": 50.1109, "lon": 8.6821, "state": "Hessen"},
            "köln": {"lat": 50.9365, "lon": 6.9589, "state": "Nordrhein-Westfalen"},
        }

        # API endpoints (would be used with real data)
        self.api_endpoints = {
            "building_permits": "https://api.bauamt.de/permits/",
            "zoning_info": "https://api.bauamt.de/zoning/",
            "building_restrictions": "https://api.bauamt.de/restrictions/",
        }

    def execute_step(self, step_data: dict) -> dict:
        """Execute a single processing step."""
        try:
            query = step_data.get("query", "")
            if not query:
                return {"success": False, "error": "No query provided"}
            result = asyncio.run(self.process_query(query))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_agent_type(self) -> str:
        """Return agent type identifier."""
        return self.AGENT_TYPE

    def get_capabilities(self) -> List[AgentCapability]:
        """Return agent capabilities."""
        return [
            AgentCapability.QUERY_PROCESSING,
            AgentCapability.LEGAL_FRAMEWORK_ANALYSIS,
            AgentCapability.BUILDING_PERMIT_PROCESSING,
        ]

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process construction/urban planning query through async pipeline.

        Pipeline:
        1. Input Validation
        2. Query Enrichment with Context
        3. Knowledge Base Search + Analysis
        4. Result Compilation
        5. Quality Gate Validation
        6. Monitoring Recording

        Args:
            query: User query about construction/planning
            context: Optional context with domain info, user preferences

        Returns:
            Dict with analysis results and confidence score
        """

        # Track execution
        start_time = datetime.now()
        execution_id = f"{self.agent_id}_{start_time.timestamp()}"

        try:
            # 1. Input Validation
            if not query or not isinstance(query, str):
                return {
                    "agent_type": self.AGENT_TYPE,
                    "error": "Invalid query",
                    "confidence": 0.0,
                    "response": "Bitte stellen Sie eine gültige Frage zum Baurecht oder Stadtplanung.",
                }

            # 2. Query Enrichment
            enriched_context = self._enrich_context(query, context)
            location = self._extract_location(query)

            # 3. Query Processing with Retry Logic
            result = await self.retry_handler.execute_with_retry(
                self._process_construction_query, query=query, location=location, context=enriched_context
            )

            # 4. Quality Gate Validation
            if result.get("confidence", 0) < self.quality_gate.min_confidence:
                result["warning"] = "Low confidence result - may need verification"

            # 5. Record Execution
            self.monitor.record_execution(
                execution_id=execution_id,
                agent_type=self.AGENT_TYPE,
                query_type="construction_analysis",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                success=True,
                confidence=result.get("confidence", 0),
            )

            return result

        except Exception as e:
            logger.error(f"Construction agent error: {e}")

            return {
                "agent_type": self.AGENT_TYPE,
                "error": str(e),
                "confidence": 0.0,
                "response": "Fehler bei der Verarbeitung - bitte später erneut versuchen.",
            }

    async def _process_construction_query(
        self, query: str, location: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Core construction query processing logic.

        Args:
            query: User query
            location: Extracted location info
            context: Enriched context

        Returns:
            Analysis result with confidence
        """

        # Search knowledge base
        kb_results = self._search_knowledge_base(query)

        if not kb_results:
            return {
                "agent_type": self.AGENT_TYPE,
                "response": "Konnte keine relevanten Baurecht-Informationen finden.",
                "confidence": 0.3,
            }

        # Compile response
        response_text = self._compile_response(query, kb_results, location)

        # Determine confidence based on match quality
        confidence = self._calculate_confidence(query, kb_results, location)

        return {
            "agent_type": self.AGENT_TYPE,
            "response": response_text,
            "location": location,
            "matched_topics": list(kb_results.keys()),
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }

    def _search_knowledge_base(self, query: str) -> Dict[str, str]:
        """
        Search knowledge base for relevant construction topics.

        Args:
            query: User query

        Returns:
            Dict of matched topics and their descriptions
        """

        query_lower = query.lower()
        matches = {}

        for topic, description in self.knowledge_base.items():
            # Check for direct topic mentions
            if topic.replace("_", " ") in query_lower or topic in query_lower:
                matches[topic] = description

            # Check for related keywords
            keywords = {
                "baugenehmigung": ["baugenehmigung", "genehmigung", "erlaubnis", "permission"],
                "baurecht": ["baurecht", "bauen", "konstruktion", "construction"],
                "zoniering": ["zone", "zoniering", "zonierung", "gebiet"],
                "baubeschraenkung": ["beschränkung", "verbot", "restriction", "schutz"],
                "nachbarschaftsrecht": ["nachbar", "nachbarschaft", "neighbor"],
                "denkmalschutz": ["denkmal", "historic", "schutz", "preservation"],
            }

            for keyword in keywords.get(topic, []):
                if keyword in query_lower:
                    matches[topic] = description
                    break

        return matches

    def _compile_response(self, query: str, kb_results: Dict[str, str], location: Optional[Dict[str, Any]] = None) -> str:
        """
        Compile structured response from KB search results.

        Args:
            query: Original query
            kb_results: Matched KB topics
            location: Optional location info

        Returns:
            Formatted response text
        """

        lines = []

        if location:
            lines.append(f"Baurechtsanalyse für {location.get('name', 'die Region')}:")
        else:
            lines.append("Baurechtsanalyse:")

        lines.append("")

        for topic, description in kb_results.items():
            lines.append(f"• {topic.replace('_', ' ').title()}: {description}")

        lines.append("")
        lines.append("Für verbindliche Auskünfte wenden Sie sich bitte an die zuständige Bauaufsichtsbehörde.")

        return "\n".join(lines)

    def _calculate_confidence(self, query: str, kb_results: Dict[str, str], location: Optional[Dict[str, Any]]) -> float:
        """
        Calculate confidence score for response.

        Args:
            query: Original query
            kb_results: Matched KB topics
            location: Optional location

        Returns:
            Confidence score (0.0-1.0)
        """

        confidence = 0.5  # Base confidence

        # Increase for more KB matches
        confidence += min(0.2, len(kb_results) * 0.05)

        # Increase if location identified
        if location:
            confidence += 0.15

        # Increase for longer, more specific queries
        if len(query) > 50:
            confidence += 0.1

        return min(1.0, max(0.0, confidence))

    def _extract_location(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract location from query."""
        query_lower = query.lower()

        for location_name, location_data in self.known_locations.items():
            if location_name in query_lower:
                return {"name": location_name.title(), **location_data}

        return None

    def _enrich_context(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Enrich query context with defaults."""
        enriched = context or {}
        enriched.setdefault("domain", "construction")
        enriched.setdefault("timestamp", datetime.now().isoformat())
        return enriched

    # ===== LEGACY COMPATIBILITY METHODS =====

    def query(self, text: str) -> Dict[str, Any]:
        """
        Legacy query interface - wraps async process_query.
        For backward compatibility only.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in event loop, create task
                return asyncio.create_task(self.process_query(text))
            else:
                # Otherwise run in new event loop
                return loop.run_until_complete(self.process_query(text))
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(self.process_query(text))

    def search_construction(self, topic: str) -> List[str]:
        """Legacy search method for construction topics."""
        topic_lower = topic.lower()
        results = []

        for kb_topic, description in self.knowledge_base.items():
            if topic_lower in kb_topic or kb_topic in topic_lower:
                results.append(description)

        return results

    def search_planning(self, topic: str) -> List[str]:
        """Legacy search method for urban planning topics."""
        return self.search_construction(topic)  # Same knowledge base


# ===== REGISTRY REGISTRATION =====


def register_construction_agent() -> Optional[str]:
    """
    Register ConstructionAgent in the agent registry.

    Returns:
        Agent ID if successful, None otherwise
    """

    try:
        registry = get_agent_registry()
        agent = ConstructionAgent(agent_id="construction_001")

        registry.register_agent(
            agent_id="construction_001",
            agent_instance=agent,
            agent_type="construction",
            capabilities=[
                AgentCapability.QUERY_PROCESSING,
                AgentCapability.LEGAL_FRAMEWORK,
                AgentCapability.DOMAIN_SPECIFIC_PROCESSING,
            ],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            metadata={
                "domain": "construction",
                "version": "2.0",
                "framework": "BaseAgent",
                "description": "Construction & Urban Planning Agent",
            },
        )

        logger.info("✅ ConstructionAgent registered in registry")
        return "construction_001"

    except Exception as e:
        logger.error(f"❌ Failed to register ConstructionAgent: {e}")
        return None


# ===== MAIN FOR TESTING =====


async def test_construction_agent():
    """Test ConstructionAgent functionality."""

    print("\n" + "=" * 80)
    print("TESTING CONSTRUCTIONAGENT")
    print("=" * 80)

    # Create agent
    agent = ConstructionAgent(agent_id="test_construction")

    # Test queries
    test_queries = [
        "Wie läuft ein Baugenehmigungsverfahren ab?",
        "Was ist Zoniering und wie beeinflusst es Bauvorhaben?",
        "Welche Rechte haben Nachbarn bei Bauvorhaben?",
        "Baugenehmigung München",
        "Denkmalschutz und Sanierung",
    ]

    print(f"\nAgent Type: {agent.get_agent_type()}")
    print(f"Capabilities: {agent.get_capabilities()}")
    print()

    for query in test_queries:
        print(f"Query: {query}")
        result = await agent.process_query(query)
        print(f"Confidence: {result.get('confidence', 0):.2f}")
        print(f"Response: {result.get('response', 'N/A')[:100]}...")
        print()


if __name__ == "__main__":
    asyncio.run(test_construction_agent())
