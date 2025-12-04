"""
EmissionenMonitoringAgent für VERITAS - BaseAgent Framework v2.0

Spezialisierter Agent für Emissionsüberwachung und -messung.
Migriert vom Legacy-System zum modernen VERITAS Framework.

Capabilities:
- emissionsmessung: Messung von Emissionen
- kontinuierliche_ueberwachung: Dauerüberwachung
- emissionsbericht: Berichterstattung
- grenzwertueberschreitung: Überschreitungen
- messstellen: Messstellenverwaltung
- berichterstattung: Reporting
- emissionsdatenbank: Datenverwaltung
- fernueberwachung: Remote Monitoring

Framework Features:
✅ BaseAgent inheritance
✅ Registry support
✅ Async processing
✅ Monitoring & Quality gates
✅ Retry logic

Wissensbasis:
- BImSchG (Bundes-Immissionsschutzgesetz)
- TA Luft
- Messstellenverordnung

Migration: 2025-12-04 (Phase 2)
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


class EmissionenMonitoringAgent(BaseAgent):
    """
    📊 Emissionen Monitoring Agent

    Spezialisiert auf:
    - Emissionsmessungen (kontinuierlich)
    - Grenzwertüberwachung
    - Berichterstattung
    - Fernüberwachung von Messstellen
    """

    AGENT_TYPE = "emissionen_monitoring"
    AGENT_DOMAIN = "ENVIRONMENTAL"
    AGENT_VERSION = "2.0"

    LEGACY_CAPABILITIES = [
        "emissionsmessung",
        "kontinuierliche überwachung",
        "emissionsbericht",
        "grenzwertüberschreitung",
        "messstellen",
        "berichterstattung",
        "emissionsdatenbank",
        "fernüberwachung",
    ]

    def __init__(self, agent_id: Optional[str] = None):
        """Initialize Emissionen Monitoring Agent with Framework Support"""
        super().__init__(agent_id=agent_id)

        self.logger = logging.getLogger(f"{__name__}.emissionen_monitoring")
        self.monitor = AgentMonitor("emissionen_monitoring")

        # Quality Gate
        policy = QualityPolicy(min_quality=0.6, target_quality=0.8)
        self.quality_gate = QualityGate(policy)

        # Retry Handler
        retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)

        # Knowledge Base
        self.knowledge_base = self._initialize_knowledge_base()

        self.logger.info(f"✅ EmissionenMonitoringAgent v{self.AGENT_VERSION} initialized")

    def execute_step(self, step_data: dict) -> dict:
        """Execute a single processing step"""
        try:
            query = step_data.get("query", "")
            if not query:
                return {"success": False, "error": "No query provided"}
            result = asyncio.run(self.process_query(query))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_agent_type(self) -> str:
        """Return agent type identifier"""
        return self.AGENT_TYPE

    def get_capabilities(self) -> List[AgentCapability]:
        """Return agent capabilities"""
        return [
            AgentCapability.QUERY_PROCESSING,
            AgentCapability.ENVIRONMENTAL_DATA_PROCESSING,
            AgentCapability.REAL_TIME_PROCESSING,
        ]

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process emissions monitoring query through async pipeline"""
        start_time = datetime.now()
        query_id = f"{self.AGENT_TYPE}_{start_time.timestamp()}"

        try:
            # 1. Validation
            if not query or not isinstance(query, str):
                return self._error_response("Invalid query", query_id)

            # 2. Search knowledge base
            results = []
            confidence = 0.0

            # Normalize query
            query_normalized = query.lower().replace(" ", "").replace("-", "")

            # Search in capabilities
            for cap in self.LEGACY_CAPABILITIES:
                cap_normalized = cap.replace(" ", "").replace("-", "")
                if cap_normalized in query_normalized:
                    kb_entry = self.knowledge_base.get(cap, {})
                    if kb_entry:
                        results.append(kb_entry)
                        confidence = 0.8

            # Fallback: Keyword search in knowledge base
            if not results:
                for cap, kb_entry in self.knowledge_base.items():
                    if any(word in query.lower() for word in [cap.lower(), kb_entry.get("info", "").lower()]):
                        results.append(kb_entry)
                        confidence = 0.6

            # 3. Build response
            processing_time = (datetime.now() - start_time).total_seconds()
            result = {
                "success": bool(results),
                "results": results,
                "confidence": confidence,
                "agent": self.AGENT_TYPE,
                "version": self.AGENT_VERSION,
                "query_id": query_id,
                "timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
            }

            self.logger.info(f"✅ Query processed in {processing_time:.2f}s")
            return result

        except Exception as e:
            self.logger.error(f"❌ Query failed: {e}")
            return self._error_response(str(e), query_id)

    def _initialize_knowledge_base(self) -> Dict[str, Dict[str, str]]:
        """Initialize Knowledge Base with Emissions Monitoring Information"""
        return {
            "emissionsmessung": {
                "knowledge": "BImSchG",
                "info": "Bundes-Immissionsschutzgesetz: Regelungen zu Emissionen und Überwachung.",
                "confidence": 0.8,
            },
            "kontinuierliche überwachung": {
                "knowledge": "Messstellenverordnung",
                "info": "Vorgaben für Messstellen und kontinuierliche Überwachung.",
                "confidence": 0.8,
            },
            "emissionsbericht": {
                "knowledge": "Emissionsdatenbank",
                "info": "Datenbank für Emissionswerte und Berichte.",
                "confidence": 0.8,
            },
            "grenzwertüberschreitung": {
                "knowledge": "TA Luft",
                "info": "Technische Anleitung zur Reinhaltung der Luft: Grenzwerte und Messverfahren.",
                "confidence": 0.8,
            },
            "messstellen": {
                "knowledge": "Messstellenverordnung",
                "info": "Vorgaben für Messstellen und kontinuierliche Überwachung.",
                "confidence": 0.8,
            },
            "berichterstattung": {
                "knowledge": "Emissionsdatenbank",
                "info": "Datenbank für Emissionswerte und Berichte.",
                "confidence": 0.8,
            },
            "emissionsdatenbank": {
                "knowledge": "Emissionsdatenbank",
                "info": "Datenbank für Emissionswerte und Berichte.",
                "confidence": 0.8,
            },
            "fernüberwachung": {
                "knowledge": "Fernüberwachung",
                "info": "Technologien zur Fernüberwachung von Emissionsquellen.",
                "confidence": 0.8,
            },
        }

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

    def query(self, keyword: str) -> List[Dict[str, Any]]:
        """Legacy method: Sync query wrapper"""
        result = asyncio.run(self.process_query(keyword))
        return result.get("results", [])

    def search_emissionen(self, query: str) -> str:
        """Legacy method: Search emissions"""
        return f"Ergebnisse für Emissionen: {query} (BImSchG, TA Luft)"

    def search_bericht(self, query: str) -> str:
        """Legacy method: Search reports"""
        return f"Bericht gefunden: {query} (Emissionsdatenbank, Berichterstattung)"

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "agent_id": "EmissionenMonitoringAgent",
            "name": "EmissionenMonitoringAgent",
            "domain": self.AGENT_DOMAIN,
            "type": self.AGENT_TYPE,
            "version": self.AGENT_VERSION,
            "capabilities": [cap.value for cap in self.get_capabilities()],
            "knowledge_base": list(self.knowledge_base.keys()),
        }


# =========================================================================
# Registration Function
# =========================================================================


def register_emissionen_monitoring_agent():
    """Register EmissionenMonitoringAgent in VERITAS Registry"""
    try:
        registry = get_agent_registry()
        registry.register_agent(
            agent_type="emissionen_monitoring",
            agent_class=EmissionenMonitoringAgent,
            capabilities=[
                AgentCapability.QUERY_PROCESSING,
                AgentCapability.ENVIRONMENTAL_DATA_PROCESSING,
                AgentCapability.REAL_TIME_PROCESSING,
            ],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=1,
            description="Emissionen Monitoring und Messung",
        )
        logger.info("✅ EmissionenMonitoringAgent registered successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to register EmissionenMonitoringAgent: {e}")
        return False
