"""
VerwaltungsrechtAgent für VERITAS - BaseAgent Framework v2.0

Spezialisierter Agent für Verwaltungsrecht, Baurecht und Genehmigungsverfahren.
Migriert vom Legacy-System zum modernen VERITAS Framework.

Capabilities:
- baurecht: Baurecht (BauGB, BauNVO, LBO)
- verwaltungsverfahren: VwVfG, Verwaltungsakte
- planungsrecht: Raumordnung und Bauleitplanung
- immissionsschutzrecht: BImSchG (Verwaltungsaspekte)
- umweltrecht: Umweltverwaltungsrecht

Framework Features:
✅ BaseAgent inheritance
✅ Registry support
✅ Async processing
✅ Monitoring & Quality gates
✅ Retry logic

Migration: 2025-12-04 (Phase 3)
Version: 2.0 (Framework)
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from backend.agents.framework.agent_monitoring import AgentMonitor

# Framework Imports
from backend.agents.framework.base_agent import BaseAgent
from backend.agents.framework.quality_gate import QualityGate, QualityPolicy
from backend.agents.framework.retry_handler import RetryConfig, RetryHandler
from backend.agents.registry.api_agent_registry import AgentCapability, AgentLifecycleType, get_agent_registry

logger = logging.getLogger(__name__)


class VerwaltungsrechtCategory(Enum):
    """Administrative law categories"""

    BAURECHT = "baurecht"
    VERWALTUNGSVERFAHREN = "verwaltungsverfahren"
    PLANUNGSRECHT = "planungsrecht"
    IMMISSIONSSCHUTZRECHT = "immissionsschutzrecht"


class VerwaltungsrechtAgent(BaseAgent):
    """
    ⚖️ Verwaltungsrecht Agent - Baurecht & Genehmigungen

    Spezialisiert auf:
    - Baurecht (BauGB, BauNVO, LBO)
    - Verwaltungsverfahrensrecht (VwVfG)
    - Planungsrecht
    - Immissionsschutz (Verwaltung)
    - Genehmigungsverfahren
    """

    AGENT_TYPE = "verwaltungsrecht"
    AGENT_DOMAIN = "LEGAL"
    AGENT_VERSION = "2.0"

    LEGACY_CAPABILITIES = ["baurecht", "verwaltungsverfahren", "planungsrecht", "immissionsschutzrecht", "baugenehmigung"]

    def __init__(self, agent_id: Optional[str] = None):
        """Initialize Verwaltungsrecht Agent with Framework Support"""
        super().__init__(agent_id=agent_id)

        self.logger = logging.getLogger(f"{__name__}.verwaltungsrecht")
        self.monitor = AgentMonitor("verwaltungsrecht")

        # Quality Gate
        policy = QualityPolicy(min_quality=0.75, target_quality=0.9)
        self.quality_gate = QualityGate(policy)

        # Retry Handler
        retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)

        # Knowledge Base
        self.knowledge_base = self._initialize_knowledge_base()

        self.logger.info(f"✅ VerwaltungsrechtAgent v{self.AGENT_VERSION} initialized")

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
        return [AgentCapability.QUERY_PROCESSING, AgentCapability.LEGAL_FRAMEWORK_ANALYSIS, AgentCapability.PROCESS_GUIDANCE]

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process administrative law query"""
        start_time = datetime.now()
        query_id = f"{self.AGENT_TYPE}_{start_time.timestamp()}"

        try:
            if not query or not isinstance(query, str):
                return self._error_response("Invalid query", query_id)

            # Search legal provisions
            provisions = await self._search_provisions(query)

            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": bool(provisions),
                "provisions": provisions,
                "confidence": 0.8 if provisions else 0.3,
                "agent": self.AGENT_TYPE,
                "version": self.AGENT_VERSION,
                "query_id": query_id,
                "timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
            }

        except Exception as e:
            self.logger.error(f"❌ Query failed: {e}")
            return self._error_response(str(e), query_id)

    async def _search_provisions(self, query: str) -> List[Dict]:
        """Search legal provisions"""
        await asyncio.sleep(0.1)

        provisions = []
        query_lower = query.lower()

        for key, prov in self.knowledge_base.items():
            if any(kw in query_lower for kw in prov.get("keywords", [])):
                provisions.append(prov)

        return provisions[:5]

    def _initialize_knowledge_base(self) -> Dict[str, Dict[str, Any]]:
        """Initialize knowledge base"""
        return {
            "baugb": {
                "law": "BauGB",
                "title": "Baugesetzbuch",
                "description": "Bundesrechtliche Grundlage für Bauleitplanung und Bodennutzung",
                "keywords": ["baurecht", "bebauungsplan", "flächennutzungsplan", "baugenehmigung"],
                "key_provisions": ["§29 Zulässigkeit", "§30 Bebauungsplan", "§34 Innerhalb bebauter Ortsteile"],
            },
            "vwvfg": {
                "law": "VwVfG",
                "title": "Verwaltungsverfahrensgesetz",
                "description": "Regelungen für Verwaltungsverfahren und Verwaltungsakte",
                "keywords": ["verwaltungsverfahren", "verwaltungsakt", "anhörung", "begründung"],
                "key_provisions": ["§28 Anhörung", "§35 Begründung", "§48 Rücknahme"],
            },
            "bimschg": {
                "law": "BImSchG",
                "title": "Bundesimmissionsschutzgesetz",
                "description": "Schutz vor schädlichen Umwelteinwirkungen",
                "keywords": ["immissionsschutz", "genehmigung", "anlagen", "emissionen"],
                "key_provisions": ["§4 Genehmigung", "§5 Pflichten", "§22 Anlagenbetrieb"],
            },
        }

    def _error_response(self, error: str, query_id: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "success": False,
            "error": error,
            "provisions": [],
            "confidence": 0.0,
            "agent": self.AGENT_TYPE,
            "query_id": query_id,
            "timestamp": datetime.now().isoformat(),
        }

    def query(self, text: str) -> Dict[str, Any]:
        """Legacy method"""
        try:
            return asyncio.run(self.process_query(text))
        except Exception as e:
            return {"success": False, "error": str(e), "provisions": [], "confidence": 0.0}

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": "VerwaltungsrechtAgent",
            "domain": self.AGENT_DOMAIN,
            "type": self.AGENT_TYPE,
            "version": self.AGENT_VERSION,
            "capabilities": [cap.value for cap in self.get_capabilities()],
            "laws_count": len(self.knowledge_base),
        }


def register_verwaltungsrecht_agent():
    """Register VerwaltungsrechtAgent"""
    try:
        registry = get_agent_registry()
        registry.register_agent(
            agent_type="verwaltungsrecht",
            agent_class=VerwaltungsrechtAgent,
            capabilities=[
                AgentCapability.QUERY_PROCESSING,
                AgentCapability.LEGAL_FRAMEWORK_ANALYSIS,
                AgentCapability.PROCESS_GUIDANCE,
            ],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=2,
            description="Verwaltungsrecht, Baurecht, Genehmigungsverfahren",
        )
        logger.info("✅ VerwaltungsrechtAgent registered")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to register: {e}")
        return False
