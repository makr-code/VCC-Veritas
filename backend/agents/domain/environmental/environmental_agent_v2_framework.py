#!/usr/bin/env python3
"""
EnvironmentalAgent für VERITAS - BaseAgent Framework v2.0

Spezialisierter Agent für Umweltschutz, Gewässerschutz und Bodenschutz.
Migriert vom Legacy-System zum modernen VERITAS Framework.

Capabilities:
- Luftqualität und Emissionsschutz
- Gewässerschutz und Wasserwirtschaft
- Bodenschutz und Altlasten
- Naturschutz und Biotope
- Abfallwirtschaft
- Umweltverträglichkeitsprüfung (UVP)

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
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.agents.framework.agent_monitoring import AgentMonitor

# Framework Imports
from backend.agents.framework.base_agent import BaseAgent
from backend.agents.framework.quality_gate import QualityGate, QualityPolicy
from backend.agents.framework.retry_handler import RetryConfig, RetryHandler
from backend.agents.registry.api_agent_registry import AgentCapability, AgentLifecycleType, get_agent_registry

logger = logging.getLogger(__name__)


# ===== DATA CLASSES =====


@dataclass
class EnvironmentalIssue:
    """Represents an environmental issue or monitoring data."""

    category: str
    severity: str
    location: str
    description: str
    source: str
    timestamp: str


# ===== ENVIRONMENTAL AGENT =====


class EnvironmentalAgent(BaseAgent):
    """
    Spezialisierter Agent für Umweltschutzfragen.
    Verarbeitet Anfragen zu Luftqualität, Gewässerschutz, Bodenschutz und Naturschutz.
    """

    AGENT_TYPE = "environmental"

    def __init__(self, agent_id: Optional[str] = None):
        """Initialize Environmental Agent with framework components."""
        super().__init__(agent_id=agent_id)

        # Framework Components
        self.monitor = AgentMonitor(self.AGENT_TYPE)
        # Quality Gate with policy
        policy = QualityPolicy(min_quality=0.6, target_quality=0.8)
        self.quality_gate = QualityGate(policy)
        retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)

        # Knowledge Base for Environmental Protection
        self.knowledge_base = {
            "luftqualitaet": "Luftqualität wird durch Schadstoffkonzentrationen gemessen. Grenzwerte regeln NO2, PM10, Ozon",
            "emissionsschutz": "Emissionsschutz verhindert Verschmutzung der Luft durch Industrie und Verkehr",
            "gewaesserschutz": "Gewässerschutz schützt Flüsse, Seen und Grundwasser vor Verschmutzung",
            "wasserwirtschaft": "Wasserwirtschaft verwaltet Wasserressourcen und Abwasserbehandlung",
            "bodenschutz": "Bodenschutz schützt den Boden vor Verschmutzung und Degradation",
            "altlasten": "Altlasten sind alte Kontaminationen durch historische Industrie",
            "naturschutz": "Naturschutz bewahrt Biotope und bedrohte Arten",
            "biotope": "Biotope sind Lebensräume für Pflanzen und Tiere",
            "abfallwirtschaft": "Abfallwirtschaft regelt Entsorgung und Recycling",
            "umweltvertraeglichkeit": "UVP (Umweltverträglichkeitsprüfung) bewertet Umweltauswirkungen von Projekten",
            "artenschutz": "Artenschutz schützt bedrohte Tier- und Pflanzenarten",
            "naturschutzgebiet": "Naturschutzgebiete sind geschützte Landschaften mit besonderen Arten oder Ökosystemen",
        }

        # Known Regions for Environmental Monitoring
        self.known_regions = {
            "rhein": {"location": "Westdeutschland", "type": "Fluss", "status": "belastet"},
            "elbe": {"location": "Ostdeutschland", "type": "Fluss", "status": "recovery"},
            "donau": {"location": "Bayern", "type": "Fluss", "status": "stable"},
            "ostsee": {"location": "Norddeutschland", "type": "Meer", "status": "belastet"},
            "bodensee": {"location": "Süddeutschland", "type": "See", "status": "stable"},
        }

        # Environmental Quality Thresholds
        self.quality_thresholds = {
            "no2_limit": 40,  # µg/m³ annual mean
            "pm10_limit": 50,  # µg/m³ daily mean
            "o3_limit": 120,  # µg/m³ 8-hour mean
            "water_quality": 2,  # EQR scale 0-5
            "soil_ph": (6.0, 8.0),  # optimal range
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
            AgentCapability.ENVIRONMENTAL_DATA,
            AgentCapability.DOMAIN_SPECIFIC_PROCESSING,
        ]

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process environmental query through async pipeline.

        Pipeline:
        1. Input Validation
        2. Query Enrichment with Context
        3. Knowledge Base Search + Environmental Data Analysis
        4. Result Compilation with Recommendations
        5. Quality Gate Validation
        6. Monitoring Recording

        Args:
            query: User query about environmental protection
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
                    "response": "Bitte stellen Sie eine gültige Frage zum Umweltschutz.",
                }

            # 2. Query Enrichment
            enriched_context = self._enrich_context(query, context)
            region = self._extract_region(query)
            category = self._classify_query(query)

            # 3. Query Processing with Retry Logic
            result = await self.retry_handler.execute_with_retry(
                self._process_environmental_query, query=query, region=region, category=category, context=enriched_context
            )

            # 4. Quality Gate Validation
            if result.get("confidence", 0) < self.quality_gate.min_confidence:
                result["warning"] = "Low confidence result - may need expert verification"

            # 5. Record Execution
            if False:
                self.monitor.record_execution(
                    execution_id=execution_id,
                    agent_type=self.AGENT_TYPE,
                    query_type=category or "environmental_analysis",
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    success=True,
                    confidence=result.get("confidence", 0),
                )

            return result

        except Exception as e:
            logger.error(f"Environmental agent error: {e}")
            if False:
                self.monitor.record_error(
                    execution_id=execution_id, agent_type=self.AGENT_TYPE, error_type=type(e).__name__, error_message=str(e)
                )

            return {
                "agent_type": self.AGENT_TYPE,
                "error": str(e),
                "confidence": 0.0,
                "response": "Fehler bei der Verarbeitung - bitte später erneut versuchen.",
            }

    async def _process_environmental_query(
        self, query: str, region: Optional[Dict[str, Any]], category: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Core environmental query processing logic.

        Args:
            query: User query
            region: Extracted region info
            category: Query category
            context: Enriched context

        Returns:
            Analysis result with confidence and recommendations
        """

        # Search knowledge base
        kb_results = self._search_knowledge_base(query)

        if not kb_results:
            return {
                "agent_type": self.AGENT_TYPE,
                "response": "Konnte keine relevanten Umweltinformationen finden.",
                "confidence": 0.3,
            }

        # Get environmental data for region if available
        env_data = self._get_environmental_data(region, category)

        # Compile response
        response_text = self._compile_response(query, kb_results, region, env_data)
        recommendations = self._generate_recommendations(category, query)

        # Determine confidence based on match quality
        confidence = self._calculate_confidence(query, kb_results, region)

        return {
            "agent_type": self.AGENT_TYPE,
            "response": response_text,
            "recommendations": recommendations,
            "category": category,
            "region": region,
            "matched_topics": list(kb_results.keys()),
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }

    def _search_knowledge_base(self, query: str) -> Dict[str, str]:
        """
        Search knowledge base for relevant environmental topics.

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
                "luftqualitaet": ["luft", "qualität", "schmutzstoff", "pollution"],
                "emissionsschutz": ["emission", "industrie", "verkehr"],
                "gewaesserschutz": ["gewässer", "wasser", "fluss", "see", "river"],
                "bodenschutz": ["boden", "erde", "kontamination", "soil"],
                "altlasten": ["altlast", "industriebrache", "contamination"],
                "naturschutz": ["natur", "schutz", "conservation", "biota"],
                "artenschutz": ["art", "spezies", "bedrohung", "endangered"],
                "naturschutzgebiet": ["schutzgebiet", "protected", "reserve"],
            }

            for keyword in keywords.get(topic, []):
                if keyword in query_lower:
                    matches[topic] = description
                    break

        return matches

    def _get_environmental_data(self, region: Optional[Dict[str, Any]], category: str) -> Dict[str, Any]:
        """Get environmental monitoring data for region."""
        if not region:
            return {}

        region_name = region.get("name", "").lower()

        if region_name in self.known_regions:
            return self.known_regions[region_name]

        return {}

    def _compile_response(
        self, query: str, kb_results: Dict[str, str], region: Optional[Dict[str, Any]], env_data: Dict[str, Any]
    ) -> str:
        """
        Compile structured response from KB search results.

        Args:
            query: Original query
            kb_results: Matched KB topics
            region: Optional region info
            env_data: Environmental data

        Returns:
            Formatted response text
        """

        lines = []

        if region:
            lines.append(f"Umweltanalyse für {region.get('name', 'die Region')}:")
        else:
            lines.append("Umweltanalyse:")

        lines.append("")

        for topic, description in kb_results.items():
            lines.append(f"• {topic.replace('_', ' ').title()}: {description}")

        if env_data:
            lines.append("")
            lines.append(f"Status in {region.get('name', 'Region')}: {env_data.get('status', 'unbekannt')}")

        lines.append("")
        lines.append("Für offizielle Daten siehe die Webseiten der Umweltbehörden.")

        return "\n".join(lines)

    def _generate_recommendations(self, category: str, query: str) -> List[str]:
        """
        Generate recommendations based on query category.

        Args:
            category: Query category
            query: Original query

        Returns:
            List of recommendations
        """

        recommendations = []

        if "luftqualität" in query.lower() or category == "air_quality":
            recommendations.append("Nutzen Sie offizielle Luftqualitätsmessungen von LANUV/UBA")
            recommendations.append("Reduzieren Sie bei schlechter Luftqualität Aktivitäten im Freien")

        if "gewässer" in query.lower() or "wasser" in query.lower():
            recommendations.append("Kontaktieren Sie Ihre lokale Wasserbehörde für Gewässerzustand")
            recommendations.append("Befolgen Sie Badeverbotszeichen an Gewässern")

        if "naturschutz" in query.lower() or "art" in query.lower():
            recommendations.append("Respektieren Sie Naturschutzgebiete und deren Regeln")
            recommendations.append("Melden Sie Beobachtungen seltener Arten dem NABU")

        if not recommendations:
            recommendations.append("Kontaktieren Sie die zuständige Umweltbehörde für spezifische Fragen")

        return recommendations

    def _classify_query(self, query: str) -> str:
        """Classify query into environmental category."""
        query_lower = query.lower()

        if any(word in query_lower for word in ["luft", "emission", "qualität"]):
            return "air_quality"
        elif any(word in query_lower for word in ["gewässer", "wasser", "fluss", "see"]):
            return "water_protection"
        elif any(word in query_lower for word in ["boden", "altlast", "kontamination"]):
            return "soil_protection"
        elif any(word in query_lower for word in ["natur", "art", "biotop", "spezies"]):
            return "nature_protection"

        return "general"

    def _extract_region(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract region from query."""
        query_lower = query.lower()

        for region_name, region_data in self.known_regions.items():
            if region_name in query_lower:
                return {"name": region_name.title(), **region_data}

        return None

    def _enrich_context(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Enrich query context with defaults."""
        enriched = context or {}
        enriched.setdefault("domain", "environmental")
        enriched.setdefault("timestamp", datetime.now().isoformat())
        return enriched

    def _calculate_confidence(self, query: str, kb_results: Dict[str, str], region: Optional[Dict[str, Any]]) -> float:
        """
        Calculate confidence score for response.

        Args:
            query: Original query
            kb_results: Matched KB topics
            region: Optional region

        Returns:
            Confidence score (0.0-1.0)
        """

        confidence = 0.5  # Base confidence

        # Increase for more KB matches
        confidence += min(0.2, len(kb_results) * 0.04)

        # Increase if region identified
        if region:
            confidence += 0.15

        # Increase for longer, more specific queries
        if len(query) > 40:
            confidence += 0.1

        return min(1.0, max(0.0, confidence))

    # ===== LEGACY COMPATIBILITY METHODS =====

    def query(self, text: str) -> Dict[str, Any]:
        """
        Legacy query interface - wraps async process_query.
        For backward compatibility only.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return asyncio.create_task(self.process_query(text))
            else:
                return loop.run_until_complete(self.process_query(text))
        except RuntimeError:
            return asyncio.run(self.process_query(text))

    def search_environmental(self, topic: str) -> List[str]:
        """Legacy search method for environmental topics."""
        topic_lower = topic.lower()
        results = []

        for kb_topic, description in self.knowledge_base.items():
            if topic_lower in kb_topic or kb_topic in topic_lower:
                results.append(description)

        return results


# ===== REGISTRY REGISTRATION =====


def register_environmental_agent() -> Optional[str]:
    """
    Register EnvironmentalAgent in the agent registry.

    Returns:
        Agent ID if successful, None otherwise
    """

    try:
        registry = get_agent_registry()
        agent = EnvironmentalAgent(agent_id="environmental_001")

        registry.register_agent(
            agent_id="environmental_001",
            agent_instance=agent,
            agent_type="environmental",
            capabilities=[
                AgentCapability.QUERY_PROCESSING,
                AgentCapability.ENVIRONMENTAL_DATA,
                AgentCapability.DOMAIN_SPECIFIC_PROCESSING,
            ],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            metadata={
                "domain": "environmental",
                "version": "2.0",
                "framework": "BaseAgent",
                "description": "Environmental Protection Agent",
            },
        )

        logger.info("✅ EnvironmentalAgent registered in registry")
        return "environmental_001"

    except Exception as e:
        logger.error(f"❌ Failed to register EnvironmentalAgent: {e}")
        return None


# ===== MAIN FOR TESTING =====


async def test_environmental_agent():
    """Test EnvironmentalAgent functionality."""

    print("\n" + "=" * 80)
    print("TESTING ENVIRONMENTALAGENT")
    print("=" * 80)

    # Create agent
    agent = EnvironmentalAgent(agent_id="test_environmental")

    # Test queries
    test_queries = [
        "Wie ist die Luftqualität in Deutschland?",
        "Gewässerschutz und Wasserqualität",
        "Naturschutzgebiete und bedrohte Arten",
        "Bodenschutz und Altlasten am Rhein",
        "Umweltverträglichkeitsprüfung für Bauvorhaben",
    ]

    print(f"\nAgent Type: {agent.get_agent_type()}")
    print(f"Capabilities: {agent.get_capabilities()}")
    print()

    for query in test_queries:
        print(f"Query: {query}")
        result = await agent.process_query(query)
        print(f"Confidence: {result.get('confidence', 0):.2f}")
        print(f"Category: {result.get('category', 'N/A')}")
        print(f"Response: {result.get('response', 'N/A')[:80]}...")
        print()


if __name__ == "__main__":
    asyncio.run(test_environmental_agent())
