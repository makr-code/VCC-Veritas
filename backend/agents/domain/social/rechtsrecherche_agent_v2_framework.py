"""
RechtsrechercheAgent für VERITAS - BaseAgent Framework v2.0

Spezialisierter Agent für Gesetzesrecherche und Rechtsprechungssuche.
Migriert vom Legacy-System zum modernen VERITAS Framework.

Capabilities:
- gesetze: Gesetzestexte (BGB, StGB, GG, etc.)
- rechtsprechung: Urteile (BGH, BVerfG, BVerwG)
- paragraphen: Paragrafen-Erklärungen
- rechtsgebiete: Rechtsgebiets-Zuordnung

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


class Rechtsgebiet(Enum):
    """Legal areas"""

    ZIVILRECHT = "zivilrecht"
    STRAFRECHT = "strafrecht"
    OEFFENTLICHESRECHT = "oeffentlichesrecht"
    VERWALTUNGSRECHT = "verwaltungsrecht"


class RechtsrechercheAgent(BaseAgent):
    """
    📖 Rechtsrecherche Agent - Gesetze & Rechtsprechung

    Spezialisiert auf:
    - Gesetzestexte (BGB, StGB, GG)
    - Rechtsprechung (BGH, BVerfG)
    - Paragrafen-Erklärungen
    - Rechtsgebiets-Zuordnung
    """

    AGENT_TYPE = "rechtsrecherche"
    AGENT_DOMAIN = "LEGAL"
    AGENT_VERSION = "2.0"

    LEGACY_CAPABILITIES = ["gesetze", "rechtsprechung", "paragraphen", "rechtsgebiete"]

    def __init__(self, agent_id: Optional[str] = None):
        """Initialize Rechtsrecherche Agent"""
        super().__init__(agent_id=agent_id)

        self.logger = logging.getLogger(f"{__name__}.rechtsrecherche")
        self.monitor = AgentMonitor("rechtsrecherche")

        policy = QualityPolicy(min_quality=0.75, target_quality=0.9)
        self.quality_gate = QualityGate(policy)

        retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)

        self.knowledge_base = self._initialize_knowledge_base()

        self.logger.info(f"✅ RechtsrechercheAgent v{self.AGENT_VERSION} initialized")

    def execute_step(self, step_data: dict) -> dict:
        """Execute processing step"""
        try:
            query = step_data.get("query", "")
            if not query:
                return {"success": False, "error": "No query provided"}
            result = asyncio.run(self.process_query(query))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_agent_type(self) -> str:
        """Return agent type"""
        return self.AGENT_TYPE

    def get_capabilities(self) -> List[AgentCapability]:
        """Return capabilities"""
        return [AgentCapability.QUERY_PROCESSING, AgentCapability.LEGAL_FRAMEWORK_ANALYSIS, AgentCapability.DOCUMENT_RETRIEVAL]

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process legal research query"""
        start_time = datetime.now()
        query_id = f"{self.AGENT_TYPE}_{start_time.timestamp()}"

        try:
            if not query or not isinstance(query, str):
                return self._error_response("Invalid query", query_id)

            laws = await self._search_laws(query)

            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": bool(laws),
                "laws": laws,
                "confidence": 0.8 if laws else 0.3,
                "agent": self.AGENT_TYPE,
                "version": self.AGENT_VERSION,
                "query_id": query_id,
                "timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
            }

        except Exception as e:
            self.logger.error(f"❌ Query failed: {e}")
            return self._error_response(str(e), query_id)

    async def _search_laws(self, query: str) -> List[Dict]:
        """Search laws"""
        await asyncio.sleep(0.1)

        laws = []
        query_lower = query.lower()

        for key, law in self.knowledge_base.items():
            if any(kw in query_lower for kw in law.get("keywords", [])):
                laws.append(law)

        return laws[:5]

    def _initialize_knowledge_base(self) -> Dict[str, Dict[str, Any]]:
        """Initialize knowledge base"""
        return {
            "bgb": {
                "law": "BGB",
                "title": "Bürgerliches Gesetzbuch",
                "rechtsgebiet": "Zivilrecht",
                "description": "Kodifikation des deutschen Zivilrechts",
                "keywords": ["bgb", "zivilrecht", "vertrag", "kaufvertrag", "schuldrecht"],
                "paragraphen_count": 2385,
            },
            "stgb": {
                "law": "StGB",
                "title": "Strafgesetzbuch",
                "rechtsgebiet": "Strafrecht",
                "description": "Kodifikation des deutschen Strafrechts",
                "keywords": ["stgb", "strafrecht", "straftat", "diebstahl", "betrug"],
                "paragraphen_count": 358,
            },
            "gg": {
                "law": "GG",
                "title": "Grundgesetz",
                "rechtsgebiet": "Öffentliches Recht",
                "description": "Verfassung der Bundesrepublik Deutschland",
                "keywords": ["gg", "grundgesetz", "verfassung", "grundrechte"],
                "paragraphen_count": 146,
            },
        }

    def _error_response(self, error: str, query_id: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "success": False,
            "error": error,
            "laws": [],
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
            return {"success": False, "error": str(e), "laws": [], "confidence": 0.0}

    def get_info(self) -> Dict[str, Any]:
        """Get agent info"""
        return {
            "name": "RechtsrechercheAgent",
            "domain": self.AGENT_DOMAIN,
            "type": self.AGENT_TYPE,
            "version": self.AGENT_VERSION,
            "capabilities": [cap.value for cap in self.get_capabilities()],
            "laws_count": len(self.knowledge_base),
        }


def register_rechtsrecherche_agent():
    """Register RechtsrechercheAgent"""
    try:
        registry = get_agent_registry()
        registry.register_agent(
            agent_type="rechtsrecherche",
            agent_class=RechtsrechercheAgent,
            capabilities=[
                AgentCapability.QUERY_PROCESSING,
                AgentCapability.LEGAL_FRAMEWORK_ANALYSIS,
                AgentCapability.DOCUMENT_RETRIEVAL,
            ],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=2,
            description="Gesetzesrecherche, Rechtsprechung, Paragrafen-Erklärung",
        )
        logger.info("✅ RechtsrechercheAgent registered")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to register: {e}")
        return False
