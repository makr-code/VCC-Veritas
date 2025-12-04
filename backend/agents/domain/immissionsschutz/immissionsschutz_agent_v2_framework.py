"""
ImmissionsschutzAgent für VERITAS - BaseAgent Framework v2.0

Spezialisierter Agent für Immissionsschutz, Luftqualität und Lärmschutz.
Migriert vom Legacy-System zum modernen VERITAS Framework.

Capabilities:
- luftqualitaet: Luftqualitätsüberwachung
- laermschutz: Lärmschutz und Grenzwerte
- ta_luft: TA Luft Anforderungen
- ta_laerm: TA Lärm Anforderungen
- grenzwerte: Emissionsgrenzwerte
- emissionen: Emissionsberechnung
- immissionspruefung: Immissionsschutzrechtliche Prüfung

Framework Features:
✅ BaseAgent inheritance
✅ Registry support
✅ Async processing
✅ Monitoring & Quality gates
✅ Retry logic

Wissensbasis:
- BImSchG (Bundes-Immissionsschutzgesetz)
- 39. BImSchV (Luftqualität)
- TA Luft (Technische Anleitung zur Reinhaltung der Luft)
- TA Lärm (Technische Anleitung zum Schutz gegen Lärm)

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


class ImmissionsschutzAgent(BaseAgent):
    """
    🏭 Immissionsschutz Agent - Luftqualität und Lärmschutz

    Spezialisiert auf:
    - Luftqualitätsgrenzwerte (NO2, PM10, PM2.5, O3, SO2)
    - Lärmschutzgrenzwerte (TA Lärm)
    - TA Luft Anforderungen
    - Emissionsberechnung
    - Immissionsschutzrechtliche Genehmigungen
    """

    AGENT_TYPE = "immissionsschutz"
    AGENT_DOMAIN = "ENVIRONMENTAL"
    AGENT_VERSION = "2.0"

    LEGACY_CAPABILITIES = [
        "luftqualitaet",
        "laermschutz",
        "ta_luft",
        "ta_laerm",
        "grenzwerte",
        "emissionen",
        "immissionspruefung",
    ]

    def __init__(self, agent_id: Optional[str] = None):
        """Initialize Immissionsschutz Agent with Framework Support"""
        super().__init__(agent_id=agent_id)

        self.logger = logging.getLogger(f"{__name__}.immissionsschutz")
        self.monitor = AgentMonitor("immissionsschutz")

        # Quality Gate
        policy = QualityPolicy(min_quality=0.6, target_quality=0.8)
        self.quality_gate = QualityGate(policy)

        # Retry Handler
        retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)

        # Knowledge Base
        self.knowledge_base = self._initialize_knowledge_base()

        self.logger.info(f"✅ ImmissionsschutzAgent v{self.AGENT_VERSION} initialized")

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
        """Process immission protection query through async pipeline"""
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

            # Check for pollutants (NO2, PM10, etc.)
            for pollutant, data in self.knowledge_base["luftqualitaet"].items():
                if pollutant.lower() in query_lower or data["schadstoff"].lower() in query_lower:
                    results.append({"type": "luftqualitaet", "schadstoff": pollutant, **data})
                    confidence = 0.9

            # Check for noise protection
            for gebiet, data in self.knowledge_base["laermschutz"].items():
                if gebiet.lower() in query_lower or data["gebietstyp"].lower() in query_lower:
                    results.append({"type": "laermschutz", "gebiet": gebiet, **data})
                    confidence = 0.9

            # Check for TA Luft/TA Lärm
            if "ta luft" in query_lower or "taluft" in query_lower:
                results.append(self.knowledge_base["ta_luft"])
                confidence = 0.85

            if "ta lärm" in query_lower or "taläerm" in query_lower or "ta laerm" in query_lower:
                results.append(self.knowledge_base["ta_laerm"])
                confidence = 0.85

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

    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """Initialize Knowledge Base with Immission Protection Information"""
        return {
            "luftqualitaet": {
                "NO2": {
                    "schadstoff": "Stickstoffdioxid (NO2)",
                    "jahresgrenzwert": "40 µg/m³",
                    "stundengrenzwert": "200 µg/m³ (max. 18 Überschreitungen/Jahr)",
                    "quelle": "39. BImSchV",
                    "gesundheit": "Atemwegsreizungen, erhöhte Anfälligkeit für Infektionen",
                },
                "PM10": {
                    "schadstoff": "Feinstaub PM10",
                    "jahresgrenzwert": "40 µg/m³",
                    "tagesgrenzwert": "50 µg/m³ (max. 35 Überschreitungen/Jahr)",
                    "quelle": "39. BImSchV",
                    "gesundheit": "Atemwegs- und Herz-Kreislauf-Erkrankungen",
                },
                "PM2.5": {
                    "schadstoff": "Feinstaub PM2.5",
                    "jahresgrenzwert": "25 µg/m³",
                    "quelle": "39. BImSchV",
                    "gesundheit": "Lungenschäden, erhöhtes Krebsrisiko",
                },
                "O3": {
                    "schadstoff": "Ozon (O3)",
                    "zielwert": "120 µg/m³ (8-Stunden-Mittelwert, max. 25 Tage/Jahr)",
                    "informationsschwelle": "180 µg/m³",
                    "alarmschwelle": "240 µg/m³",
                    "quelle": "39. BImSchV",
                    "gesundheit": "Atemwegsreizungen, Kopfschmerzen",
                },
                "SO2": {
                    "schadstoff": "Schwefeldioxid (SO2)",
                    "stundengrenzwert": "350 µg/m³ (max. 24 Überschreitungen/Jahr)",
                    "tagesgrenzwert": "125 µg/m³ (max. 3 Überschreitungen/Jahr)",
                    "quelle": "39. BImSchV",
                    "gesundheit": "Atemwegsreizungen, Verschlimmerung von Asthma",
                },
            },
            "laermschutz": {
                "Industriegebiet": {
                    "gebietstyp": "Industriegebiet",
                    "tag": "70 dB(A)",
                    "nacht": "70 dB(A)",
                    "quelle": "TA Lärm Nr. 6.1",
                },
                "Gewerbegebiet": {
                    "gebietstyp": "Gewerbegebiet",
                    "tag": "65 dB(A)",
                    "nacht": "50 dB(A)",
                    "quelle": "TA Lärm Nr. 6.1",
                },
                "Mischgebiet": {
                    "gebietstyp": "Mischgebiet/Dorfgebiet",
                    "tag": "60 dB(A)",
                    "nacht": "45 dB(A)",
                    "quelle": "TA Lärm Nr. 6.1",
                },
                "Wohngebiet": {
                    "gebietstyp": "Allgemeines Wohngebiet",
                    "tag": "55 dB(A)",
                    "nacht": "40 dB(A)",
                    "quelle": "TA Lärm Nr. 6.1",
                },
                "Reines Wohngebiet": {
                    "gebietstyp": "Reines Wohngebiet",
                    "tag": "50 dB(A)",
                    "nacht": "35 dB(A)",
                    "quelle": "TA Lärm Nr. 6.1",
                },
                "Kurgebiet": {
                    "gebietstyp": "Kurgebiet/Krankenhaus",
                    "tag": "45 dB(A)",
                    "nacht": "35 dB(A)",
                    "quelle": "TA Lärm Nr. 6.1",
                },
            },
            "ta_luft": {
                "titel": "TA Luft - Technische Anleitung zur Reinhaltung der Luft",
                "beschreibung": "Anforderungen zur Vorsorge gegen schädliche Umwelteinwirkungen durch Luftverunreinigungen",
                "anforderungen": [
                    "Emissionsbegrenzungen",
                    "Immissionswerte",
                    "Messung und Überwachung",
                    "Ableitbedingungen (Schornsteinhöhe)",
                ],
                "quelle": "TA Luft 2021",
            },
            "ta_laerm": {
                "titel": "TA Lärm - Technische Anleitung zum Schutz gegen Lärm",
                "beschreibung": "Schutz der Allgemeinheit und der Nachbarschaft vor schädlichen Umwelteinwirkungen durch Geräusche",
                "anforderungen": [
                    "Immissionsrichtwerte für verschiedene Gebietstypen",
                    "Tag-/Nachtzeiten",
                    "Beurteilungspegel",
                    "Einzelne kurzzeitige Geräuschspitzen",
                ],
                "quelle": "TA Lärm 1998",
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

    def query(self, text: str) -> Dict[str, Any]:
        """Legacy method: Sync query wrapper"""
        result = asyncio.run(self.process_query(text))
        return result

    def get_luftqualitaet_grenzwerte(self, schadstoff: str) -> Dict[str, Any]:
        """Get air quality limits for pollutant"""
        return self.knowledge_base["luftqualitaet"].get(schadstoff.upper(), {})

    def get_laermschutz_grenzwerte(self, gebietstyp: str) -> Dict[str, Any]:
        """Get noise protection limits for area type"""
        return self.knowledge_base["laermschutz"].get(gebietstyp, {})

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": "ImmissionsschutzAgent",
            "domain": self.AGENT_DOMAIN,
            "type": self.AGENT_TYPE,
            "version": self.AGENT_VERSION,
            "capabilities": [cap.value for cap in self.get_capabilities()],
            "pollutants": list(self.knowledge_base["luftqualitaet"].keys()),
            "area_types": list(self.knowledge_base["laermschutz"].keys()),
        }


# =========================================================================
# Registration Function
# =========================================================================


def register_immissionsschutz_agent():
    """Register ImmissionsschutzAgent in VERITAS Registry"""
    try:
        registry = get_agent_registry()
        registry.register_agent(
            agent_type="immissionsschutz",
            agent_class=ImmissionsschutzAgent,
            capabilities=[
                AgentCapability.QUERY_PROCESSING,
                AgentCapability.ENVIRONMENTAL_DATA_PROCESSING,
                AgentCapability.LEGAL_FRAMEWORK_ANALYSIS,
            ],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=1,
            description="Immissionsschutz, Luftqualität und Lärmschutz",
        )
        logger.info("✅ ImmissionsschutzAgent registered successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to register ImmissionsschutzAgent: {e}")
        return False
