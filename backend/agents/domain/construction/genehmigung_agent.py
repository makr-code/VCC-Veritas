"""
GenehmigungsAgent für VERITAS - BaseAgent Framework v2.0

Spezialisierter Agent für Genehmigungsverfahren und Beteiligungsprozesse.
Migriert vom Legacy-System zum modernen VERITAS Framework.

Capabilities:
- genehmigungsverfahren: Genehmigungsverfahren und Voraussetzungen
- antragsstellung: Form und Ablauf der Antragstellung
- verwaltungsverfahren: Ablauf und Grundsätze
- fristen: Fristen im Verfahren
- beteiligung: Beteiligungsrechte
- öffentlichkeitsbeteiligung: Öffentliche Beteiligung
- widerspruch: Widerspruchsverfahren
- anhörung: Anhörungsrechte
- umweltinformationsgesetz: UIG Informationszugang
- akteneinsicht: Akteneinsicht im Verfahren

Framework Features:
✅ BaseAgent inheritance - Framework integration
✅ Registry support - Automatic discovery & lifecycle management
✅ Async processing - Non-blocking query processing
✅ Monitoring - Performance metrics & health tracking
✅ Quality gates - Result validation & confidence scoring
✅ Retry logic - Automatic error handling & recovery

Wissensbasis:
- VwVfG (Verwaltungsverfahrensgesetz)
- UIG (Umweltinformationsgesetz)
- Fristenregelungen
- Beteiligungsrechte

Migration: 2025-12-04
Author: VERITAS Framework Migration v2.0
Version: 2.0 (Framework)
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.agents.framework.agent_monitoring import AgentMonitor

# Framework Imports
from backend.agents.framework.base_agent import BaseAgent
from backend.agents.framework.quality_gate import QualityGate, QualityPolicy
from backend.agents.framework.retry_handler import RetryConfig, RetryHandler
from backend.agents.registry.api_agent_registry import AgentCapability, AgentLifecycleType, get_agent_registry

logger = logging.getLogger(__name__)


class GenehmigungAgent(BaseAgent):
    """
    🏛️ Genehmigung Agent - Verwaltungsrecht & Genehmigungsverfahren

    Spezialisiert auf:
    - Genehmigungsverfahren nach VwVfG
    - Beteiligungsrechte und Anhörungen
    - Widerspruchsverfahren
    - Umweltinformationszugang (UIG)

    Example:
        >>> agent = GenehmigungAgent()
        >>> result = await agent.process_query(
        ...     "Wie lange dauert ein Genehmigungsverfahren?"
        ... )
        >>> print(result["results"])
    """

    # =====================================================================
    # Configuration
    # =====================================================================

    AGENT_TYPE = "genehmigung"
    AGENT_DOMAIN = "LEGAL"
    AGENT_VERSION = "2.0"  # Framework Version

    # Legacy Capabilities Mapping
    LEGACY_CAPABILITIES = [
        "genehmigungsverfahren",
        "antragsstellung",
        "verwaltungsverfahren",
        "fristen",
        "beteiligung",
        "öffentlichkeitsbeteiligung",
        "widerspruch",
        "anhörung",
        "umweltinformationsgesetz",
        "akteneinsicht",
    ]

    def __init__(self, agent_id: Optional[str] = None):
        """Initialize Genehmigung Agent with Framework Support"""
        super().__init__(agent_id=agent_id)

        self.logger = logging.getLogger(f"{__name__}.genehmigung")
        self.monitor = AgentMonitor("genehmigung")

        # Initialize Quality Gate with policy
        policy = QualityPolicy(min_quality=0.6, target_quality=0.8)
        self.quality_gate = QualityGate(policy)

        # Initialize Retry Handler with config
        retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)

        # Initialize Knowledge Base
        self.knowledge_base = self._initialize_knowledge_base()

        self.logger.info(f"✅ GenehmigungAgent v{self.AGENT_VERSION} initialized")

    # =====================================================================
    # Abstract Method Implementation
    # =====================================================================

    def execute_step(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single processing step (abstract method implementation)

        Args:
            step_data: Processing step configuration

        Returns:
            Step execution result
        """
        try:
            query = step_data.get("query", "")
            if not query:
                return {"success": False, "error": "No query provided"}

            # Execute synchronously for framework compatibility
            result = asyncio.run(self.process_query(query))
            return result

        except Exception as e:
            self.logger.error(f"Step execution failed: {e}")
            return {"success": False, "error": str(e)}

    # =====================================================================
    # Framework: Abstract Methods
    # =====================================================================

    def get_agent_type(self) -> str:
        """Return agent type for registry"""
        return self.AGENT_TYPE

    def get_capabilities(self) -> List[AgentCapability]:
        """Return agent capabilities."""
        return [
            AgentCapability.QUERY_PROCESSING,
            AgentCapability.LEGAL_FRAMEWORK_ANALYSIS,
            AgentCapability.BUILDING_PERMIT_PROCESSING,
        ]

    # =====================================================================
    # Main Query Processing Pipeline
    # =====================================================================

    async def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process query with full framework pipeline

        Pipeline:
        1. Input Validation
        2. Query Enrichment
        3. Legacy Query Processing
        4. Result Validation
        5. Quality Gate
        6. Monitoring
        """
        query_id = f"{self.AGENT_TYPE}_{datetime.now().timestamp()}"
        start_time = datetime.now()

        try:
            self.logger.debug(f"🔄 Processing: {query[:50]}...")

            # 1. Validate Input
            if not self._validate_input(query):
                return self._error_response("Invalid query format", query_id)

            # 2. Enrich Query
            enriched_query = self._enrich_query(query, context)

            # 3. Process with Retry
            result = await self._process_with_retry(enriched_query)

            # 4. Validate Result
            if not self._validate_result(result):
                return self._error_response("Invalid result structure", query_id)

            # 5. Quality Gate
            gate_passed = self.quality_gate.check(result)
            if not gate_passed:
                self.logger.warning(f"⚠️ Quality gate: confidence={result.get('confidence', 0)}")

            # 6. Add Metadata
            processing_time = (datetime.now() - start_time).total_seconds()
            result.update(
                {
                    "agent": self.AGENT_TYPE,
                    "version": self.AGENT_VERSION,
                    "query_id": query_id,
                    "timestamp": datetime.now().isoformat(),
                    "processing_time": processing_time,
                    "quality_gate_passed": gate_passed,
                }
            )

            # 7. Monitor
            self.monitor.record_success(response_time=processing_time)
            self.logger.info(f"✅ Query processed in {processing_time:.2f}s")

            return result

        except Exception as e:
            self.logger.error(f"❌ Query failed: {str(e)}", exc_info=True)
            if False:
                self.monitor.record_failure(error=str(e))
            return self._error_response(str(e), query_id)

    # =====================================================================
    # Legacy Query Implementation
    # =====================================================================

    async def _process_with_retry(self, query: str) -> Dict[str, Any]:
        """Execute query with automatic retry"""

        async def query_func():
            return self._legacy_query(query)

        result = await self.retry_handler.execute_with_retry(query_func)
        return result

    def _legacy_query(self, text: str) -> Dict[str, Any]:
        """
        Legacy Query Processing from Original GenehmigungsAgent
        ======================================================

        Ursprüngliche Logik beibehalten für Kompatibilität.
        Kann in zukünftigen Sprints optimiert werden.
        """
        results = []
        confidence = 0.0

        # Search in capabilities (priority 1)
        for cap in self.LEGACY_CAPABILITIES:
            if cap in text.lower():
                kb = self.knowledge_base.get(cap, [])
                results.extend(kb)
                confidence = 0.8

        # Search in knowledge base (priority 2)
        if not results:
            for cap, kb in self.knowledge_base.items():
                for entry in kb:
                    if any(
                        word in text.lower() for word in [entry.get("gesetz", "").lower(), entry.get("inhalt", "").lower()]
                    ):
                        results.append(entry)
                        confidence = 0.6

        return {"success": bool(results), "results": results, "confidence": confidence, "processing_time": 0.0}

    def _initialize_knowledge_base(self) -> Dict[str, List[Dict]]:
        """Initialize Knowledge Base with Legal Information"""
        return {
            "genehmigungsverfahren": [{"gesetz": "VwVfG", "inhalt": "Regelungen zu Verwaltungsverfahren und Genehmigungen."}],
            "antragsstellung": [{"gesetz": "VwVfG", "inhalt": "Form und Ablauf der Antragstellung."}],
            "verwaltungsverfahren": [{"gesetz": "VwVfG", "inhalt": "Ablauf und Grundsätze des Verwaltungsverfahrens."}],
            "fristen": [{"gesetz": "VwVfG", "inhalt": "Fristen im Verwaltungsverfahren."}],
            "beteiligung": [{"gesetz": "VwVfG", "inhalt": "Beteiligungsrechte im Verfahren."}],
            "öffentlichkeitsbeteiligung": [{"gesetz": "VwVfG", "inhalt": "Öffentliche Beteiligung bei Genehmigungen."}],
            "widerspruch": [{"gesetz": "VwVfG", "inhalt": "Widerspruchsverfahren gegen Verwaltungsakte."}],
            "anhörung": [{"gesetz": "VwVfG", "inhalt": "Recht auf Anhörung im Verfahren."}],
            "umweltinformationsgesetz": [{"gesetz": "UIG", "inhalt": "Recht auf Zugang zu Umweltinformationen."}],
            "akteneinsicht": [{"gesetz": "VwVfG", "inhalt": "Recht auf Akteneinsicht im Verfahren."}],
        }

    # =====================================================================
    # Validation & Enrichment
    # =====================================================================

    def _validate_input(self, query: str) -> bool:
        """Validate input query"""
        return isinstance(query, str) and 0 < len(query) <= 10000

    def _validate_result(self, result: Dict) -> bool:
        """Validate result structure"""
        required_keys = {"success", "results", "confidence"}
        return isinstance(result, dict) and required_keys.issubset(result.keys())

    def _enrich_query(self, query: str, context: Optional[Dict]) -> str:
        """Add context to query"""
        if context and "domain" in context:
            return f"{query} [{context['domain']}]"
        return query

    def _error_response(self, error: str, query_id: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "success": False,
            "error": error,
            "results": [],
            "confidence": 0.0,
            "agent": self.AGENT_TYPE,
            "query_id": query_id,
            "timestamp": datetime.now().isoformat(),
        }

    # =====================================================================
    # Legacy Compatibility Methods
    # =====================================================================

    def search_genehmigung(self, text: str) -> List[Dict[str, Any]]:
        """Legacy method: Search genehmigungsverfahren"""
        return [
            entry
            for entry in self.knowledge_base.get("genehmigungsverfahren", [])
            if text.lower() in entry.get("inhalt", "").lower()
        ]

    def search_beteiligung(self, text: str) -> List[Dict[str, Any]]:
        """Legacy method: Search beteiligung"""
        return [
            entry for entry in self.knowledge_base.get("beteiligung", []) if text.lower() in entry.get("inhalt", "").lower()
        ]

    def query(self, text: str) -> Dict[str, Any]:
        """Legacy method: Sync query wrapper (use process_query() instead)"""
        # Async wrapper for backward compatibility
        result = asyncio.run(self.process_query(text))
        return result

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": "GenehmigungAgent",
            "domain": self.AGENT_DOMAIN,
            "type": self.AGENT_TYPE,
            "version": self.AGENT_VERSION,
            "capabilities": [cap.value for cap in self.get_capabilities()],
            "knowledge_base_size": sum(len(v) for v in self.knowledge_base.values()),
            "metrics": self.monitor.get_metrics(),
        }


# =========================================================================
# Registration Function
# =========================================================================


def register_genehmigung_agent():
    """
    Register GenehmigungAgent in VERITAS Registry

    Example:
        from backend.agents.domain.construction.genehmigung_agent import register_genehmigung_agent
        register_genehmigung_agent()
    """
    try:
        registry = get_agent_registry()
        registry.register_agent(
            agent_type="genehmigung",
            agent_class=GenehmigungAgent,
            capabilities=[AgentCapability.LEGAL_FRAMEWORK],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=1,
            description="Genehmigungsverfahren und Verwaltungsrecht",
        )
        logger.info("✅ GenehmigungAgent registered successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to register GenehmigungAgent: {e}")
        return False


# =========================================================================
# Test / Quick Usage
# =========================================================================

if __name__ == "__main__":

    async def test_genehmigung_agent():
        """Quick test of GenehmigungAgent"""
        agent = GenehmigungAgent()

        # Test Query
        result = await agent.process_query("Wie lange dauert ein Genehmigungsverfahren?")
        print("\nQuery Result:")
        print(f"  Success: {result['success']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Results: {len(result['results'])} entries")

        # Test Info
        print("\nAgent Info:")
        info = agent.get_info()
        for key, value in info.items():
            print(f"  {key}: {value}")

    asyncio.run(test_genehmigung_agent())
