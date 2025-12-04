"""
ChemicalDataAgent für VERITAS - BaseAgent Framework v2.0

Spezialisierter Agent für chemische Stoffdaten, Sicherheitsinformationen und Regulatorik.
Migriert vom Legacy-System zum modernen VERITAS Framework.

Capabilities:
- chemical_properties: Stoffeigenschaften (physikalisch/chemisch)
- safety_data: Sicherheitsdatenblätter (SDS/MSDS)
- toxicology: Toxikologische Daten (LD50, LC50)
- ghs_classification: GHS-Klassifikation und Piktogramme
- exposure_limits: Arbeitsplatz-Grenzwerte (MAK, TLV)
- cas_lookup: CAS/EC-Nummern Suche
- environmental_data: Umwelteigenschaften

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
import re
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


class ChemicalIdentifierType(Enum):
    """Chemical identifier types"""

    CAS_NUMBER = "cas_number"
    EC_NUMBER = "ec_number"
    IUPAC_NAME = "iupac_name"
    COMMON_NAME = "common_name"


class GHSHazardClass(Enum):
    """GHS hazard classes (simplified)"""

    FLAMMABLE = "flammable"
    TOXIC = "toxic"
    CORROSIVE = "corrosive"
    OXIDIZING = "oxidizing"
    ENVIRONMENTAL = "environmental"


class ChemicalDataAgent(BaseAgent):
    """
    🧪 Chemical Data Agent - Chemische Stoffdaten & Sicherheit

    Spezialisiert auf:
    - CAS/EC-Nummern Lookup
    - Sicherheitsdatenblätter (SDS)
    - GHS-Klassifikation
    - Toxikologische Daten
    - Arbeitsplatz-Grenzwerte (MAK/TLV)
    - Umwelteigenschaften
    """

    AGENT_TYPE = "chemical_data"
    AGENT_DOMAIN = "CHEMICAL"
    AGENT_VERSION = "2.0"

    LEGACY_CAPABILITIES = [
        "chemical_properties",
        "safety_data",
        "toxicology",
        "ghs_classification",
        "exposure_limits",
        "cas_lookup",
        "environmental_data",
    ]

    def __init__(self, agent_id: Optional[str] = None):
        """Initialize Chemical Data Agent with Framework Support"""
        super().__init__(agent_id=agent_id)

        self.logger = logging.getLogger(f"{__name__}.chemical_data")
        self.monitor = AgentMonitor("chemical_data")

        # Quality Gate
        policy = QualityPolicy(min_quality=0.7, target_quality=0.9)
        self.quality_gate = QualityGate(policy)

        # Retry Handler
        retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)

        # Knowledge Base
        self.knowledge_base = self._initialize_knowledge_base()

        self.logger.info(f"✅ ChemicalDataAgent v{self.AGENT_VERSION} initialized")

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
        return [AgentCapability.QUERY_PROCESSING, AgentCapability.KNOWLEDGE_SYNTHESIS, AgentCapability.DATA_ANALYSIS]

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process chemical data query through async pipeline"""
        start_time = datetime.now()
        query_id = f"{self.AGENT_TYPE}_{start_time.timestamp()}"

        try:
            # 1. Validation
            if not query or not isinstance(query, str):
                return self._error_response("Invalid query", query_id)

            # 2. Extract chemical identifier
            identifier = self._extract_chemical_identifier(query)

            # 3. Search chemical database
            substance = await self._search_chemical_database(identifier, query)

            # 4. Build detailed response
            processing_time = (datetime.now() - start_time).total_seconds()
            result = {
                "success": bool(substance),
                "substance": substance,
                "identifier": identifier,
                "confidence": 0.85 if substance else 0.3,
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

    def _extract_chemical_identifier(self, query: str) -> Dict[str, Any]:
        """Extract chemical identifier from query"""
        identifier = {"type": None, "value": None, "full_query": query}

        # CAS Number pattern: 123-45-6
        cas_pattern = r"\b\d{1,7}-\d{2}-\d\b"
        cas_match = re.search(cas_pattern, query)
        if cas_match:
            identifier["type"] = "cas_number"
            identifier["value"] = cas_match.group(0)
            return identifier

        # EC Number pattern: 200-123-4
        ec_pattern = r"\b\d{3}-\d{3}-\d\b"
        ec_match = re.search(ec_pattern, query)
        if ec_match:
            identifier["type"] = "ec_number"
            identifier["value"] = ec_match.group(0)
            return identifier

        # Common name search
        query_lower = query.lower()
        for substance in self.knowledge_base.values():
            if substance["common_name"].lower() in query_lower:
                identifier["type"] = "common_name"
                identifier["value"] = substance["common_name"]
                return identifier

            # Check synonyms
            for synonym in substance.get("synonyms", []):
                if synonym.lower() in query_lower:
                    identifier["type"] = "common_name"
                    identifier["value"] = synonym
                    return identifier

        # Default to common name
        identifier["type"] = "common_name"
        identifier["value"] = query.strip()
        return identifier

    async def _search_chemical_database(self, identifier: Dict, query: str) -> Optional[Dict]:
        """Search chemical database for substance"""
        await asyncio.sleep(0.1)  # Simulate external API call

        # Search by CAS number (most specific)
        if identifier["type"] == "cas_number":
            for substance in self.knowledge_base.values():
                if substance["cas_number"] == identifier["value"]:
                    return substance

        # Search by EC number
        if identifier["type"] == "ec_number":
            for substance in self.knowledge_base.values():
                if substance.get("ec_number") == identifier["value"]:
                    return substance

        # Search by common name or synonyms
        if identifier["type"] == "common_name":
            query_lower = query.lower()
            for substance in self.knowledge_base.values():
                # Exact name match
                if substance["common_name"].lower() == identifier["value"].lower():
                    return substance

                # Synonym match
                for synonym in substance.get("synonyms", []):
                    if synonym.lower() in query_lower:
                        return substance

        return None

    def _initialize_knowledge_base(self) -> Dict[str, Dict[str, Any]]:
        """Initialize knowledge base with common chemicals"""
        return {
            "ethanol": {
                "substance_id": "chem_001",
                "common_name": "Ethanol",
                "cas_number": "64-17-5",
                "ec_number": "200-578-6",
                "iupac_name": "Ethanol",
                "molecular_formula": "C2H5OH",
                "molecular_weight": 46.07,
                "physical_state": "liquid",
                "synonyms": ["Ethylalkohol", "Alcohol", "Äthanol"],
                "ghs_classification": {
                    "hazard_class": "flammable",
                    "signal_word": "Gefahr",
                    "h_statements": ["H225 - Flüssigkeit und Dampf leicht entzündbar"],
                    "p_statements": ["P210 - Von Hitze fernhalten", "P233 - Behälter dicht verschlossen halten"],
                    "pictograms": ["GHS02"],
                },
                "physical_properties": {
                    "boiling_point_c": 78.4,
                    "melting_point_c": -114.1,
                    "density_g_cm3": 0.789,
                    "flash_point_c": 13,
                },
                "toxicology": {"ld50_oral_rat_mg_kg": 7060, "lc50_inhalation_rat_mg_l": 124.7},
                "exposure_limits": {"mak_germany_ppm": 500, "mak_germany_mg_m3": 960, "tlv_usa_ppm": 1000},
                "uses": ["Lösungsmittel", "Desinfektionsmittel", "Kraftstoffzusatz"],
            },
            "benzene": {
                "substance_id": "chem_002",
                "common_name": "Benzol",
                "cas_number": "71-43-2",
                "ec_number": "200-753-7",
                "iupac_name": "Benzene",
                "molecular_formula": "C6H6",
                "molecular_weight": 78.11,
                "physical_state": "liquid",
                "synonyms": ["Benzene", "Benzen"],
                "ghs_classification": {
                    "hazard_class": "toxic",
                    "signal_word": "Gefahr",
                    "h_statements": [
                        "H225 - Flüssigkeit und Dampf leicht entzündbar",
                        "H350 - Kann Krebs erzeugen",
                        "H340 - Kann genetische Defekte verursachen",
                    ],
                    "p_statements": ["P201 - Vor Gebrauch besondere Anweisungen einholen"],
                    "pictograms": ["GHS02", "GHS08"],
                },
                "physical_properties": {
                    "boiling_point_c": 80.1,
                    "melting_point_c": 5.5,
                    "density_g_cm3": 0.876,
                    "flash_point_c": -11,
                },
                "toxicology": {
                    "ld50_oral_rat_mg_kg": 930,
                    "lc50_inhalation_rat_mg_l": 13.7,
                    "carcinogenicity": "IARC Group 1 - Karzinogen für den Menschen",
                },
                "exposure_limits": {"mak_germany_ppm": 0.5, "mak_germany_mg_m3": 1.6, "tlv_usa_ppm": 0.5},
                "uses": ["Chemische Synthese", "Lösungsmittel"],
            },
            "sulfuric_acid": {
                "substance_id": "chem_003",
                "common_name": "Schwefelsäure",
                "cas_number": "7664-93-9",
                "ec_number": "231-639-5",
                "iupac_name": "Sulfuric acid",
                "molecular_formula": "H2SO4",
                "molecular_weight": 98.08,
                "physical_state": "liquid",
                "synonyms": ["Sulfuric acid", "Vitriol"],
                "ghs_classification": {
                    "hazard_class": "corrosive",
                    "signal_word": "Gefahr",
                    "h_statements": ["H314 - Verursacht schwere Verätzungen der Haut und schwere Augenschäden"],
                    "p_statements": [
                        "P280 - Schutzhandschuhe/Schutzkleidung/Augenschutz tragen",
                        "P305+P351+P338 - Bei Kontakt mit den Augen: Einige Minuten lang behutsam mit Wasser spülen",
                    ],
                    "pictograms": ["GHS05"],
                },
                "physical_properties": {"boiling_point_c": 337, "melting_point_c": 10, "density_g_cm3": 1.84},
                "toxicology": {"ld50_oral_rat_mg_kg": 2140, "corrosivity": "Stark ätzend"},
                "exposure_limits": {"mak_germany_mg_m3": 0.1, "tlv_usa_mg_m3": 0.2},
                "uses": ["Düngemittelproduktion", "Batterien", "Chemische Synthese"],
            },
            "ammonia": {
                "substance_id": "chem_004",
                "common_name": "Ammoniak",
                "cas_number": "7664-41-7",
                "ec_number": "231-635-3",
                "iupac_name": "Ammonia",
                "molecular_formula": "NH3",
                "molecular_weight": 17.03,
                "physical_state": "gas",
                "synonyms": ["Ammonia"],
                "ghs_classification": {
                    "hazard_class": "toxic",
                    "signal_word": "Gefahr",
                    "h_statements": [
                        "H221 - Entzündbares Gas",
                        "H331 - Giftig bei Einatmen",
                        "H314 - Verursacht schwere Verätzungen",
                    ],
                    "p_statements": ["P280 - Schutzhandschuhe/Augenschutz tragen"],
                    "pictograms": ["GHS02", "GHS05", "GHS06"],
                },
                "physical_properties": {"boiling_point_c": -33.3, "melting_point_c": -77.7, "density_g_cm3": 0.73},
                "toxicology": {"lc50_inhalation_rat_ppm": 2000},
                "exposure_limits": {"mak_germany_ppm": 20, "mak_germany_mg_m3": 14, "tlv_usa_ppm": 25},
                "uses": ["Düngemittel", "Kältemittel", "Reinigungsmittel"],
            },
            "sodium_hydroxide": {
                "substance_id": "chem_005",
                "common_name": "Natriumhydroxid",
                "cas_number": "1310-73-2",
                "ec_number": "215-185-5",
                "iupac_name": "Sodium hydroxide",
                "molecular_formula": "NaOH",
                "molecular_weight": 40.00,
                "physical_state": "solid",
                "synonyms": ["Natronlauge", "Ätznatron", "Caustic soda"],
                "ghs_classification": {
                    "hazard_class": "corrosive",
                    "signal_word": "Gefahr",
                    "h_statements": ["H314 - Verursacht schwere Verätzungen der Haut und schwere Augenschäden"],
                    "p_statements": ["P280 - Schutzhandschuhe/Augenschutz tragen"],
                    "pictograms": ["GHS05"],
                },
                "physical_properties": {"boiling_point_c": 1388, "melting_point_c": 323, "density_g_cm3": 2.13},
                "toxicology": {"ld50_oral_rat_mg_kg": 40},
                "exposure_limits": {"mak_germany_mg_m3": 2, "tlv_usa_mg_m3": 2},
                "uses": ["Seifenherstellung", "Papierherstellung", "Wasseraufbereitung"],
            },
        }

    def _error_response(self, error: str, query_id: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "success": False,
            "error": error,
            "substance": None,
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
        try:
            result = asyncio.run(self.process_query(text))
            return result
        except Exception as e:
            return {"success": False, "error": str(e), "substance": None, "confidence": 0.0}

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": "ChemicalDataAgent",
            "domain": self.AGENT_DOMAIN,
            "type": self.AGENT_TYPE,
            "version": self.AGENT_VERSION,
            "capabilities": [cap.value for cap in self.get_capabilities()],
            "substances_count": len(self.knowledge_base),
            "supported_identifiers": ["cas_number", "ec_number", "common_name"],
        }


# =========================================================================
# Registration Function
# =========================================================================


def register_chemical_data_agent():
    """Register ChemicalDataAgent in VERITAS Registry"""
    try:
        registry = get_agent_registry()
        registry.register_agent(
            agent_type="chemical_data",
            agent_class=ChemicalDataAgent,
            capabilities=[
                AgentCapability.QUERY_PROCESSING,
                AgentCapability.KNOWLEDGE_SYNTHESIS,
                AgentCapability.DATA_ANALYSIS,
            ],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=3,
            priority=2,
            description="Chemische Stoffdaten, SDS, GHS-Klassifikation, Toxikologie",
        )
        logger.info("✅ ChemicalDataAgent registered successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to register ChemicalDataAgent: {e}")
        return False
