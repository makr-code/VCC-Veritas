"""
NaturschutzAgent für VERITAS - BaseAgent Framework v2.0

Spezialisierter Agent für Naturschutz und Artenschutz.
Migriert vom Legacy-System zum modernen VERITAS Framework.

Capabilities:
- naturschutz: Grundlagen des Naturschutzes
- artenschutz: Schutz gefährdeter Arten
- flora-fauna-habitat: FFH-Richtlinie und Lebensräume
- landschaftsschutz: Landschaftserhalt und -entwicklung
- naturschutzgebiete: Schutzgebiete und deren Ausweisung
- biotopverbund: Biotopvernetzung
- uvp: Umweltverträglichkeitsprüfung
- eingriffsregelung: Ausgleich und Ersatz
- ökokonto: Ökokonten und Bilanzierung

Framework Features:
✅ BaseAgent inheritance
✅ Registry support
✅ Async processing
✅ Monitoring & Quality gates
✅ Retry logic

Wissensbasis:
- BNatSchG (Bundesnaturschutzgesetz)
- FFH-Richtlinie
- UVPG (Umweltverträglichkeitsprüfungsgesetz)

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


class NaturschutzAgent(BaseAgent):
    """
    🌿 Naturschutz Agent - Natur- und Artenschutz

    Spezialisiert auf:
    - Naturschutzrecht (BNatSchG)
    - Artenschutz und FFH-Richtlinie
    - Landschaftsschutz und Schutzgebiete
    - Umweltverträglichkeitsprüfung (UVP)
    - Eingriffsregelung und Ökokonto
    """

    AGENT_TYPE = "naturschutz"
    AGENT_DOMAIN = "ENVIRONMENTAL"
    AGENT_VERSION = "2.0"

    LEGACY_CAPABILITIES = [
        "naturschutz",
        "flora-fauna-habitat",
        "artenschutz",
        "landschaftsschutz",
        "naturschutzgebiete",
        "ffh-richtlinie",
        "biotopverbund",
        "umweltverträglichkeitsprüfung",
        "eingriffsregelung",
        "ökokonto",
    ]

    def __init__(self, agent_id: Optional[str] = None):
        """Initialize Naturschutz Agent with Framework Support"""
        super().__init__(agent_id=agent_id)

        self.logger = logging.getLogger(f"{__name__}.naturschutz")
        self.monitor = AgentMonitor("naturschutz")

        # Quality Gate
        policy = QualityPolicy(min_quality=0.6, target_quality=0.8)
        self.quality_gate = QualityGate(policy)

        # Retry Handler
        retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)

        # Knowledge Base
        self.knowledge_base = self._initialize_knowledge_base()

        self.logger.info(f"✅ NaturschutzAgent v{self.AGENT_VERSION} initialized")

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
        """Process nature conservation query through async pipeline"""
        start_time = datetime.now()
        query_id = f"{self.AGENT_TYPE}_{start_time.timestamp()}"

        try:
            # 1. Validation
            if not query or not isinstance(query, str):
                return self._error_response("Invalid query", query_id)

            # 2. Search knowledge base
            results = []
            confidence = 0.0
            query_lower = query.lower()

            # Keyword matching with expanded synonyms
            keyword_map = {
                "naturschutz": ["naturschutz", "natur"],
                "flora-fauna-habitat": ["ffh", "flora", "fauna", "habitat", "richtlinie"],
                "artenschutz": ["artenschutz", "arten", "art"],
                "landschaftsschutz": ["landschaftsschutz", "landschaft"],
                "naturschutzgebiete": ["naturschutzgebiet", "schutzgebiet"],
                "ffh-richtlinie": ["ffh", "richtlinie"],
                "biotopverbund": ["biotop", "verbund"],
                "umweltverträglichkeitsprüfung": ["uvp", "umweltverträglichkeit", "prüfung"],
                "eingriffsregelung": ["eingriff", "ausgleich", "ersatz"],
                "ökokonto": ["ökokonto", "öko"],
            }

            # Search with keyword matching
            for cap in self.LEGACY_CAPABILITIES:
                keywords = keyword_map.get(cap, [cap.replace("-", "")])
                if any(kw in query_lower for kw in keywords):
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
        """Initialize Knowledge Base with Nature Conservation Information"""
        return {
            "naturschutz": [{"gesetz": "BNatSchG", "inhalt": "Schutz von Natur und Landschaft."}],
            "flora-fauna-habitat": [
                {"gesetz": "FFH-Richtlinie", "inhalt": "Schutz von Lebensräumen und Arten nach EU-Recht."}
            ],
            "artenschutz": [
                {"gesetz": "BNatSchG", "inhalt": "Besonderer Schutz gefährdeter Arten."},
                {"gesetz": "Artenschutzrecht", "inhalt": "Internationale und nationale Regelungen zum Artenschutz."},
            ],
            "landschaftsschutz": [{"gesetz": "BNatSchG", "inhalt": "Erhalt und Entwicklung der Landschaft."}],
            "naturschutzgebiete": [{"gesetz": "BNatSchG", "inhalt": "Ausweisung und Schutz von Naturschutzgebieten."}],
            "ffh-richtlinie": [
                {"gesetz": "FFH-Richtlinie", "inhalt": "Erhalt von Lebensräumen und Arten von gemeinschaftlichem Interesse."}
            ],
            "biotopverbund": [{"gesetz": "BNatSchG", "inhalt": "Vernetzung von Biotopen zur Förderung der Artenvielfalt."}],
            "umweltverträglichkeitsprüfung": [{"gesetz": "UVPG", "inhalt": "Prüfung der Umweltauswirkungen von Projekten."}],
            "eingriffsregelung": [
                {"gesetz": "BNatSchG", "inhalt": "Ausgleich und Ersatz bei Eingriffen in Natur und Landschaft."}
            ],
            "ökokonto": [{"gesetz": "BNatSchG", "inhalt": "Instrument zur Bilanzierung von Ausgleichs- und Ersatzmaßnahmen."}],
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

    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate result structure"""
        required_keys = ["success", "results", "confidence"]
        return all(key in result for key in required_keys)

    # =====================================================================
    # Legacy Compatibility Methods
    # =====================================================================

    def query(self, text: str) -> Dict[str, Any]:
        """Legacy method: Sync query wrapper"""
        try:
            result = asyncio.run(self.process_query(text))
            return result
        except Exception as e:
            return {"success": False, "error": str(e), "results": [], "confidence": 0.0}

    def search_naturschutz(self, text: str) -> List[Dict[str, Any]]:
        """Legacy method: Search naturschutz"""
        return [
            entry for entry in self.knowledge_base.get("naturschutz", []) if text.lower() in entry.get("inhalt", "").lower()
        ]

    def search_uvp(self, text: str) -> List[Dict[str, Any]]:
        """Legacy method: Search UVP"""
        return [
            entry
            for entry in self.knowledge_base.get("umweltverträglichkeitsprüfung", [])
            if text.lower() in entry.get("inhalt", "").lower()
        ]

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": "NaturschutzAgent",
            "domain": self.AGENT_DOMAIN,
            "type": self.AGENT_TYPE,
            "version": self.AGENT_VERSION,
            "capabilities": [cap.value for cap in self.get_capabilities()],
            "knowledge_base_size": sum(len(v) for v in self.knowledge_base.values()),
        }


# =========================================================================
# Registration Function
# =========================================================================


def register_naturschutz_agent():
    """Register NaturschutzAgent in VERITAS Registry"""
    try:
        registry = get_agent_registry()
        registry.register_agent(
            agent_type="naturschutz",
            agent_class=NaturschutzAgent,
            capabilities=[
                AgentCapability.QUERY_PROCESSING,
                AgentCapability.ENVIRONMENTAL_DATA_PROCESSING,
                AgentCapability.LEGAL_FRAMEWORK_ANALYSIS,
            ],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=1,
            description="Naturschutz und Artenschutz",
        )
        logger.info("✅ NaturschutzAgent registered successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to register NaturschutzAgent: {e}")
        return False
