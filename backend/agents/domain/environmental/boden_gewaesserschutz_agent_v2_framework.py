"""
BodenGewaesserschutzAgent für VERITAS - BaseAgent Framework v2.0

Spezialisierter Agent für Boden- und Gewässerschutz.
Migriert vom Legacy-System zum modernen VERITAS Framework.

Capabilities:
- bodenschutz: Schutz des Bodens
- altlasten: Altlastensanierung
- grundwasser: Grund wasserschutz
- wasserrahmenrichtlinie: EU-WRRL
- bodenverunreinigung: Bodenkontamination
- schutzgebiete: Wasserschutzgebiete
- hydrogeologie: Hydrogeologische Grundlagen
- abfallrecht: Kreislaufwirtschaft
- wasserrecht: WHG
- abwasser: Abwasserbehandlung
- nitratbelastung: Nitrat im Grundwasser

Framework Features:
✅ BaseAgent inheritance
✅ Registry support
✅ Async processing
✅ Monitoring & Quality gates
✅ Retry logic

Wissensbasis:
- BBodSchG (Bodenschutzgesetz)
- WHG (Wasserhaushaltsgesetz)
- WRRL (Wasserrahmenrichtlinie)
- Altlastenverordnung

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


class BodenGewaesserschutzAgent(BaseAgent):
    """
    💧 Boden- und Gewässerschutz Agent

    Spezialisiert auf:
    - Bodenschutzrecht (BBodSchG)
    - Wasserrecht (WHG)
    - Altlastensanierung
    - Wasserrahmenrichtlinie (WRRL)
    - Grundwasser- und Gewässerschutz
    """

    AGENT_TYPE = "boden_gewaesserschutz"
    AGENT_DOMAIN = "ENVIRONMENTAL"
    AGENT_VERSION = "2.0"

    LEGACY_CAPABILITIES = [
        "bodenschutz",
        "altlasten",
        "grundwasser",
        "wasserrahmenrichtlinie",
        "bodenverunreinigung",
        "schutzgebiete",
        "hydrogeologie",
        "abfallrecht",
        "wasserrecht",
        "abwasser",
        "nitratbelastung",
    ]

    def __init__(self, agent_id: Optional[str] = None):
        """Initialize Boden-Gewässerschutz Agent with Framework Support"""
        super().__init__(agent_id=agent_id)

        self.logger = logging.getLogger(f"{__name__}.boden_gewaesserschutz")
        self.monitor = AgentMonitor("boden_gewaesserschutz")

        # Quality Gate
        policy = QualityPolicy(min_quality=0.6, target_quality=0.8)
        self.quality_gate = QualityGate(policy)

        # Retry Handler
        retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)

        # Knowledge Base
        self.knowledge_base = self._initialize_knowledge_base()

        self.logger.info(f"✅ BodenGewaesserschutzAgent v{self.AGENT_VERSION} initialized")

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
            AgentCapability.LEGAL_FRAMEWORK_ANALYSIS,
        ]

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process soil and water protection query through async pipeline"""
        start_time = datetime.now()
        query_id = f"{self.AGENT_TYPE}_{start_time.timestamp()}"

        try:
            # 1. Validation
            if not query or not isinstance(query, str):
                return self._error_response("Invalid query", query_id)

            # 2. Search knowledge base
            results = []
            confidence = 0.0

            # Search in capabilities
            for cap in self.LEGACY_CAPABILITIES:
                if cap.replace("-", "") in query.lower().replace("-", ""):
                    kb = self.knowledge_base.get(cap, [])
                    results.extend(kb)
                    confidence = 0.8

            # Fallback: Search in knowledge base content
            if not results:
                for cap, kb in self.knowledge_base.items():
                    for entry in kb:
                        if any(
                            word in query.lower()
                            for word in [entry.get("gesetz", "").lower(), entry.get("inhalt", "").lower()]
                        ):
                            results.append(entry)
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

    def _initialize_knowledge_base(self) -> Dict[str, List[Dict]]:
        """Initialize Knowledge Base with Soil and Water Protection Information"""
        return {
            "bodenschutz": [
                {"gesetz": "BBodSchG", "inhalt": "Schutz des Bodens vor schädlichen Veränderungen."},
                {"gesetz": "Altlastenverordnung", "inhalt": "Regelungen zu Altlasten und Sanierung."},
            ],
            "altlasten": [
                {"gesetz": "Altlastenverordnung", "inhalt": "Definition und Sanierung von Altlasten."},
                {"gesetz": "BBodSchG", "inhalt": "Pflichten zur Erkundung und Sanierung von Altlasten."},
            ],
            "grundwasser": [
                {"gesetz": "WHG", "inhalt": "Schutz und Nutzung des Grundwassers."},
                {"gesetz": "WRRL", "inhalt": "Europäische Wasserrahmenrichtlinie."},
            ],
            "wasserrahmenrichtlinie": [
                {"gesetz": "WRRL", "inhalt": "Ziel: Guter Zustand aller Gewässer bis 2027."},
                {"gesetz": "WHG", "inhalt": "Umsetzung der WRRL im deutschen Wasserrecht."},
            ],
            "nitratbelastung": [{"gesetz": "Nitrat-Richtlinie", "inhalt": "Grenzwerte für Nitrat im Grundwasser."}],
            "abfallrecht": [{"gesetz": "KrWG", "inhalt": "Kreislaufwirtschaftsgesetz für Abfallmanagement."}],
            "wasserrecht": [{"gesetz": "WHG", "inhalt": "Wasserhaushaltsgesetz für Oberflächengewässer und Grundwasser."}],
            "abwasser": [{"gesetz": "Abwasserverordnung", "inhalt": "Grenzwerte und Anforderungen für Abwasser."}],
            "schutzgebiete": [{"gesetz": "BNatSchG", "inhalt": "Schutz von Gebieten mit besonderer Bedeutung."}],
            "hydrogeologie": [{"gesetz": "WHG", "inhalt": "Hydrogeologische Grundlagen im Wasserrecht."}],
            "bodenverunreinigung": [{"gesetz": "BBodSchG", "inhalt": "Sanierung und Vorsorge bei Bodenverunreinigung."}],
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

    def query(self, text: str) -> Dict[str, Any]:
        """Legacy method: Sync query wrapper"""
        result = asyncio.run(self.process_query(text))
        return result

    def search_bodenschutz(self, text: str) -> List[Dict[str, Any]]:
        """Legacy method: Search bodenschutz"""
        return [
            entry for entry in self.knowledge_base.get("bodenschutz", []) if text.lower() in entry.get("inhalt", "").lower()
        ]

    def search_wasserrecht(self, text: str) -> List[Dict[str, Any]]:
        """Legacy method: Search wasserrecht"""
        return [
            entry for entry in self.knowledge_base.get("wasserrecht", []) if text.lower() in entry.get("inhalt", "").lower()
        ]

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": "BodenGewaesserschutzAgent",
            "domain": self.AGENT_DOMAIN,
            "type": self.AGENT_TYPE,
            "version": self.AGENT_VERSION,
            "capabilities": [cap.value for cap in self.get_capabilities()],
            "knowledge_base_size": sum(len(v) for v in self.knowledge_base.values()),
        }


# =========================================================================
# Registration Function
# =========================================================================


def register_boden_gewaesserschutz_agent():
    """Register BodenGewaesserschutzAgent in VERITAS Registry"""
    try:
        registry = get_agent_registry()
        registry.register_agent(
            agent_type="boden_gewaesserschutz",
            agent_class=BodenGewaesserschutzAgent,
            capabilities=[
                AgentCapability.QUERY_PROCESSING,
                AgentCapability.ENVIRONMENTAL_DATA_PROCESSING,
                AgentCapability.LEGAL_FRAMEWORK_ANALYSIS,
            ],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=1,
            description="Boden- und Gewässerschutz",
        )
        logger.info("✅ BodenGewaesserschutzAgent registered successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to register BodenGewaesserschutzAgent: {e}")
        return False
