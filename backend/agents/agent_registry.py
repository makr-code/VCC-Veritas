#!/usr/bin/env python3
"""
VERITAS Agent Registry
======================
Central registry for all specialized agents.

This registry provides:
- Auto-discovery of available agents
- Agent initialization with shared resources
- Fallback handling for unavailable agents
- Performance monitoring per agent
- Capability-based agent selection

Author: VERITAS Development Team
Date: 2025-10-16
Version: 1.0 (Production-focused)
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class AgentDomain(Enum):
    """Agent domain categories for production use-cases"""

    ENVIRONMENTAL = "environmental"  # Umwelt, Immissionsschutz
    LEGAL = "legal"  # Recht, Verwaltungsrecht
    TECHNICAL = "technical"  # Standards, Normen
    KNOWLEDGE = "knowledge"  # Wikipedia, Allgemeinwissen
    ATMOSPHERIC = "atmospheric"  # Atmosphärische Analysen
    DATABASE = "database"  # Datenbank-Queries
    ADMINISTRATIVE = "administrative"  # Verwaltung (future)


@dataclass
class AgentInfo:
    """Agent metadata and capabilities"""

    agent_id: str
    domain: AgentDomain
    capabilities: List[str]
    class_reference: Type
    requires_db: bool = False
    requires_api: bool = False
    initialized: bool = False
    description: str = ""


class AgentRegistry:
    """
    Central registry for all specialized agents.

    This registry manages 6 production-ready agents:
    - EnvironmentalAgent: Umwelt-Anfragen
    - ChemicalDataAgent: Chemische Daten, Gefahrstoffe
    - TechnicalStandardsAgent: DIN/ISO/EN Standards
    - WikipediaAgent: Enzyklopädie-Recherche
    - AtmosphericFlowAgent: Luftströmungen, Schadstoffausbreitung
    - DatabaseAgent: Datenbank-Queries

    Usage:
        >>> registry = AgentRegistry()
        >>> agent = registry.get_agent("EnvironmentalAgent")
        >>> result = agent.query("Luftqualität in München")

    Example:
        >>> # Get all environmental agents
        >>> env_agents = registry.get_agents_by_domain(AgentDomain.ENVIRONMENTAL)
        >>> print(env_workers)  # ['EnvironmentalAgent', 'ChemicalDataAgent', ...]

        >>> # Get agents by capability
        >>> air_quality_agents = registry.get_agents_by_capability("luftqualitaet")
        >>> print(air_quality_workers)  # ['EnvironmentalAgent', ...]
    """

    def __init__(self, db_pool=None, api_config=None):
        """
        Initialize worker registry.

        Args:
            db_pool: Database connection pool (optional)
            api_config: API configuration dict (optional)
        """
        self.db_pool = db_pool
        self.api_config = api_config or {}
        self.agents: Dict[str, AgentInfo] = {}
        self.initialized_agents: Dict[str, Any] = {}

        logger.info("🔧 Initializing Agent Registry...")
        self._register_all_agents()
        logger.info(f"✅ Agent Registry initialized with {len(self.agents)} agents")

    def _register_all_agents(self):
        """Register all available production agents"""

        # 1. ENVIRONMENTAL AGENT
        try:
            from backend.agents.veritas_api_agent_environmental import EnvironmentalAgent, EnvironmentalAgentConfig

            self._register_agent(
                agent_id="EnvironmentalAgent",
                domain=AgentDomain.ENVIRONMENTAL,
                capabilities=[
                    "environmental",
                    "umwelt",
                    "air_quality",
                    "luftqualitaet",
                    "noise",
                    "laerm",
                    "waste",
                    "abfall",
                    "water",
                    "wasser",
                    "nature_conservation",
                    "naturschutz",
                ],
                class_reference=EnvironmentalAgent,
                requires_db=False,
                requires_api=False,
                description="Umwelt-Anfragen: Luftqualität, Lärm, Abfall, Wasser, Naturschutz",
            )
            logger.info("  ✅ EnvironmentalAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ EnvironmentalAgent nicht verfügbar: {e}")

        # 2. CHEMICAL DATA AGENT
        try:
            from backend.agents.veritas_api_agent_chemical_data import ChemicalDataAgent

            self._register_agent(
                agent_id="ChemicalDataAgent",
                domain=AgentDomain.ENVIRONMENTAL,
                capabilities=[
                    "chemical",
                    "chemisch",
                    "hazardous",
                    "gefahrsto",
                    "substances",
                    "stoffe",
                    "safety",
                    "sicherheit",
                    "toxicity",
                    "toxizitaet",
                    "msds",
                ],
                class_reference=ChemicalDataAgent,
                requires_db=False,
                requires_api=False,
                description="Chemische Daten: Gefahrstoffe, Sicherheitsdatenblätter, Toxizität",
            )
            logger.info("  ✅ ChemicalDataAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ ChemicalDataAgent nicht verfügbar: {e}")

        # 3. TECHNICAL STANDARDS AGENT
        try:
            from backend.agents.veritas_api_agent_technical_standards import TechnicalStandardsAgent

            self._register_agent(
                agent_id="TechnicalStandardsAgent",
                domain=AgentDomain.TECHNICAL,
                capabilities=[
                    "standards",
                    "normen",
                    "din",
                    "iso",
                    "en",
                    "vdi",
                    "technical",
                    "technisch",
                    "specifications",
                    "spezifikationen",
                    "building_codes",
                    "bauvorschriften",
                ],
                class_reference=TechnicalStandardsAgent,
                requires_db=False,
                requires_api=False,
                description="Technische Normen: DIN, ISO, EN, VDI Standards",
            )
            logger.info("  ✅ TechnicalStandardsAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ TechnicalStandardsAgent nicht verfügbar: {e}")

        # 4. WIKIPEDIA AGENT
        try:
            from backend.agents.veritas_api_agent_wikipedia import WikipediaAgent

            self._register_agent(
                agent_id="WikipediaAgent",
                domain=AgentDomain.KNOWLEDGE,
                capabilities=[
                    "wikipedia",
                    "knowledge",
                    "wissen",
                    "encyclopedia",
                    "enzyklopaedie",
                    "definition",
                    "explanation",
                    "erklaerung",
                    "general_knowledge",
                ],
                class_reference=WikipediaAgent,
                requires_db=False,
                requires_api=True,  # Wikipedia API (optional, has mock fallback)
                description="Allgemeinwissen: Wikipedia-Recherche, Definitionen, Erklärungen",
            )
            logger.info("  ✅ WikipediaAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ WikipediaAgent nicht verfügbar: {e}")

        # 5. ATMOSPHERIC FLOW AGENT
        try:
            from backend.agents.veritas_api_agent_atmospheric_flow import AtmosphericFlowAgent

            self._register_agent(
                agent_id="AtmosphericFlowAgent",
                domain=AgentDomain.ATMOSPHERIC,
                capabilities=[
                    "atmospheric",
                    "atmosphaerisch",
                    "flow",
                    "stroemung",
                    "dispersion",
                    "ausbreitung",
                    "air_flow",
                    "luftstroemung",
                    "pollution_dispersion",
                    "schadstoffausbreitung",
                    "wind",
                ],
                class_reference=AtmosphericFlowAgent,
                requires_db=False,
                requires_api=True,  # DWD Weather integration
                description="Atmosphärische Analysen: Luftströmungen, Schadstoffausbreitung",
            )
            logger.info("  ✅ AtmosphericFlowAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ AtmosphericFlowAgent nicht verfügbar: {e}")

        # 6. DATABASE AGENT
        try:
            from backend.agents.veritas_api_agent_database import DatabaseAgent

            self._register_agent(
                agent_id="DatabaseAgent",
                domain=AgentDomain.DATABASE,
                capabilities=[
                    "database",
                    "datenbank",
                    "query",
                    "abfrage",
                    "sql",
                    "data",
                    "daten",
                    "search",
                    "suche",
                    "retrieval",
                ],
                class_reference=DatabaseAgent,
                requires_db=True,
                requires_api=False,
                description="Datenbank-Queries: Direkte Datenbank-Abfragen",
            )
            logger.info("  ✅ DatabaseAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ DatabaseAgent nicht verfügbar: {e}")

        # 7. VERWALTUNGSRECHT AGENT (Production Agent)
        try:
            from backend.agents.veritas_api_agent_verwaltungsrecht import VerwaltungsrechtAgent

            self._register_agent(
                agent_id="VerwaltungsrechtAgent",
                domain=AgentDomain.LEGAL,
                capabilities=[
                    "verwaltungsrecht",
                    "baurecht",
                    "baugenehmigung",
                    "planungsrecht",
                    "immissionsschutzrecht",
                    "verwaltungsverfahren",
                    "umweltrecht",
                    "genehmigungsverfahren",
                    "baugb",
                    "bimschg",
                    "lbo",
                    "bauordnung",
                    "bebauungsplan",
                    "außenbereich",
                    "innenbereich",
                    "verwaltungsakt",
                ],
                class_reference=VerwaltungsrechtAgent,
                requires_db=False,
                requires_api=False,
                description="Verwaltungsrecht: Baurecht, Genehmigungsverfahren, Immissionsschutzrecht",
            )
            logger.info("  ✅ VerwaltungsrechtAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ VerwaltungsrechtAgent nicht verfügbar: {e}")

        # 8. RECHTSRECHERCH AGENT (Production Agent)
        try:
            from backend.agents.veritas_api_agent_rechtsrecherche import RechtsrecherchAgent

            self._register_agent(
                agent_id="RechtsrecherchAgent",
                domain=AgentDomain.LEGAL,
                capabilities=[
                    "rechtsrecherche",
                    "gesetze",
                    "rechtsprechung",
                    "bgb",
                    "stgb",
                    "grundgesetz",
                    "gg",
                    "bgh",
                    "bverfg",
                    "bverwg",
                    "zivilrecht",
                    "strafrecht",
                    "öffentliches recht",
                    "kommentar",
                    "gesetzesauslegung",
                ],
                class_reference=RechtsrecherchAgent,
                requires_db=False,
                requires_api=False,
                description="Rechtsrecherche: Gesetzestexte, Rechtsprechung, Kommentare",
            )
            logger.info("  ✅ RechtsrecherchAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ RechtsrecherchAgent nicht verfügbar: {e}")

        # 9. IMMISSIONSSCHUTZ AGENT (Production Agent)
        try:
            from backend.agents.veritas_api_agent_immissionsschutz import ImmissionsschutzAgent

            self._register_agent(
                agent_id="ImmissionsschutzAgent",
                domain=AgentDomain.ENVIRONMENTAL,
                capabilities=[
                    "immissionsschutz",
                    "luftqualität",
                    "lärm",
                    "lärmschutz",
                    "ta luft",
                    "ta lärm",
                    "grenzwerte",
                    "no2",
                    "pm10",
                    "feinstaub",
                    "ozon",
                    "schadsto",
                    "emission",
                    "dezibel",
                    "lärmgrenzwert",
                ],
                class_reference=ImmissionsschutzAgent,
                requires_db=False,
                requires_api=False,
                description="Immissionsschutz: Luftqualität, Lärmschutz, TA Luft, TA Lärm",
            )
            logger.info("  ✅ ImmissionsschutzAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ ImmissionsschutzAgent nicht verfügbar: {e}")
        # 10. BODEN- UND GEWÄSSERSCHUTZ AGENT
        try:
            from backend.agents.veritas_api_agent_boden_gewaesserschutz import BodenGewaesserschutzAgent

            self._register_agent(
                agent_id="BodenGewaesserschutzAgent",
                domain=AgentDomain.ENVIRONMENTAL,
                capabilities=[
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
                ],
                class_reference=BodenGewaesserschutzAgent,
                requires_db=False,
                requires_api=False,
                description="Boden- und Gewässerschutz: Bodenschutz, Grundwasser, Altlasten, Wasserrahmenrichtlinie, Nitratbelastung",
            )
            logger.info("  ✅ BodenGewaesserschutzAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ BodenGewaesserschutzAgent nicht verfügbar: {e}")
        # 11. NATURSCHUTZ AGENT
        try:
            from backend.agents.veritas_api_agent_naturschutz import NaturschutzAgent

            self._register_agent(
                agent_id="NaturschutzAgent",
                domain=AgentDomain.ENVIRONMENTAL,
                capabilities=[
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
                ],
                class_reference=NaturschutzAgent,
                requires_db=False,
                requires_api=False,
                description="Naturschutz: BNatSchG, FFH-Richtlinie, UVP, Artenschutz, Biotopverbund",
            )
            logger.info("  ✅ NaturschutzAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ NaturschutzAgent nicht verfügbar: {e}")

        # 12. GENEHMIGUNGS AGENT
        try:
            from backend.agents.veritas_api_agent_genehmigung import GenehmigungsAgent

            self._register_agent(
                agent_id="GenehmigungsAgent",
                domain=AgentDomain.ADMINISTRATIVE,
                capabilities=[
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
                ],
                class_reference=GenehmigungsAgent,
                requires_db=False,
                requires_api=False,
                description="Genehmigungsverfahren: VwVfG, UIG, Fristen, Beteiligungsrechte",
            )
            logger.info("  ✅ GenehmigungsAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ GenehmigungsAgent nicht verfügbar: {e}")

        # 13. EMISSIONEN-MONITORING AGENT
        try:
            from backend.agents.veritas_api_agent_emissionen_monitoring import EmissionenMonitoringAgent

            self._register_agent(
                agent_id="EmissionenMonitoringAgent",
                domain=AgentDomain.ENVIRONMENTAL,
                capabilities=[
                    "emissionsmessung",
                    "kontinuierliche überwachung",
                    "emissionsbericht",
                    "grenzwertüberschreitung",
                    "messstellen",
                    "berichterstattung",
                    "emissionsdatenbank",
                    "fernüberwachung",
                ],
                class_reference=EmissionenMonitoringAgent,
                requires_db=False,
                requires_api=False,
                description="Emissionen-Monitoring: BImSchG, TA Luft, Messstellenverordnung, Emissionsdatenbank",
            )
            logger.info("  ✅ EmissionenMonitoringAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ EmissionenMonitoringAgent nicht verfügbar: {e}")

        # 14. VERWALTUNGSPROZESS AGENT
        try:
            from backend.agents.veritas_api_agent_verwaltungsprozess import VerwaltungsprozessAgent

            self._register_agent(
                agent_id="VerwaltungsprozessAgent",
                domain=AgentDomain.ADMINISTRATIVE,
                capabilities=[
                    "verwaltungsprozess",
                    "klageverfahren",
                    "einstweiliger rechtsschutz",
                    "gerichtsbarkeit",
                    "verwaltungsgericht",
                    "fristen",
                    "rechtsmittel",
                    "urteilsdatenbank",
                ],
                class_reference=VerwaltungsprozessAgent,
                requires_db=False,
                requires_api=False,
                description="Verwaltungsprozess: VwGO, Klageverfahren, Rechtsmittel, Urteilsdatenbank",
            )
            logger.info("  ✅ VerwaltungsprozessAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ VerwaltungsprozessAgent nicht verfügbar: {e}")

        # 15. DWD OPEN DATA WEATHER AGENT
        try:
            from backend.agents.veritas_api_agent_dwd_opendata import DWDOpenDataAgent

            self._register_agent(
                agent_id="DWDOpenDataAgent",
                domain=AgentDomain.ATMOSPHERIC,
                capabilities=[
                    "weather",
                    "wetter",
                    "dwd",
                    "temperature",
                    "temperatur",
                    "precipitation",
                    "niederschlag",
                    "climate",
                    "klima",
                    "forecast",
                    "vorhersage",
                    "historical",
                    "historisch",
                    "wind",
                    "pressure",
                    "luftdruck",
                    "station",
                ],
                class_reference=DWDOpenDataAgent,
                requires_db=False,
                requires_api=False,  # Direktes Parsing von opendata.dwd.de, kein API-Key nötig
                description="DWD Open Data: Historische Wetterdaten von opendata.dwd.de (dwdparse)",
            )
            logger.info("  ✅ DWDOpenDataAgent registered")
        except ImportError as e:
            logger.warning(f"  ⚠️ DWDOpenDataAgent nicht verfügbar: {e}")

        logger.info(f"📊 Registration complete: {len(self.agents)} agents available")

    def _register_agent(
        self,
        agent_id: str,
        domain: AgentDomain,
        capabilities: List[str],
        class_reference: Type,
        requires_db: bool = False,
        requires_api: bool = False,
        description: str = "",
    ):
        """
        Register a worker in the registry.

        Args:
            agent_id: Unique worker identifier
            domain: Worker domain category
            capabilities: List of capability keywords
            class_reference: Worker class
            requires_db: Whether worker needs database connection
            requires_api: Whether worker needs API access
            description: Human-readable description
        """
        self.agents[agent_id] = AgentInfo(
            agent_id=agent_id,
            domain=domain,
            capabilities=capabilities,
            class_reference=class_reference,
            requires_db=requires_db,
            requires_api=requires_api,
            description=description,
        )

    def get_agent(self, agent_id: str) -> Optional[Any]:
        """
        Get initialized worker instance.

        Args:
            agent_id: Worker identifier (e.g., "EnvironmentalAgent")

        Returns:
            Worker instance or None if not available

        Example:
            >>> registry = AgentRegistry()
            >>> agent = registry.get_agent("EnvironmentalAgent")
            >>> result = agent.query("Luftqualität München")
        """
        # Return cached instance if available
        if agent_id in self.initialized_agents:
            return self.initialized_agents[agent_id]

        # Check if worker is registered
        if agent_id not in self.agents:
            logger.warning(f"⚠️ Worker '{agent_id}' not registered")
            return None

        worker_info = self.agents[agent_id]

        try:
            # Check dependencies
            if worker_info.requires_db and not self.db_pool:
                logger.warning(f"⚠️ Worker '{agent_id}' needs database, " "but none available - using fallback mode")

            if worker_info.requires_api and not self.api_config:
                logger.info(f"ℹ️ Worker '{agent_id}' prefers API access, " "but none configured - using mock/fallback mode")

            # Instantiate worker
            # Note: Different agents have different constructors
            if agent_id == "EnvironmentalAgent":
                from backend.agents.veritas_api_agent_environmental import EnvironmentalAgentConfig

                config = EnvironmentalAgentConfig()
                worker_instance = worker_info.class_reference(config=config)
            else:
                # Most agents don't need special initialization
                worker_instance = worker_info.class_reference()

            # Cache the instance
            self.initialized_agents[agent_id] = worker_instance
            worker_info.initialized = True

            logger.info(f"✅ Worker '{agent_id}' initialized successfully")
            return worker_instance

        except Exception as e:
            logger.error(f"❌ Worker '{agent_id}' initialization failed: {e}")
            return None

    def get_agents_by_capability(self, capability: str) -> List[str]:
        """
        Get worker IDs that have a specific capability.

        Args:
            capability: Capability keyword (e.g., "luftqualitaet")

        Returns:
            List of worker IDs

        Example:
            >>> registry = AgentRegistry()
            >>> agents = registry.get_agents_by_capability("luftqualitaet")
            >>> print(workers)  # ['EnvironmentalAgent']
        """
        capability_lower = capability.lower()
        matching_agents = []

        for agent_id, info in self.agents.items():
            if capability_lower in [c.lower() for c in info.capabilities]:
                matching_agents.append(agent_id)

        return matching_agents

    def get_agents_by_domain(self, domain: AgentDomain) -> List[str]:
        """
        Get all worker IDs in a specific domain.

        Args:
            domain: AgentDomain enum value

        Returns:
            List of worker IDs

        Example:
            >>> registry = AgentRegistry()
            >>> agents = registry.get_agents_by_domain(AgentDomain.ENVIRONMENTAL)
            >>> print(workers)  # ['EnvironmentalAgent', 'ChemicalDataAgent']
        """
        return [agent_id for agent_id, info in self.agents.items() if info.domain == domain]

    def list_available_agents(self) -> Dict[str, Any]:
        """
        List all registered agents with their status.

        Returns:
            Dictionary with worker information

        Example:
            >>> registry = AgentRegistry()
            >>> agents = registry.list_available_workers()
            >>> for agent_id, info in agents.items():
            ...     print(f"{agent_id}: {info['description']}")
        """
        return {
            agent_id: {
                "domain": info.domain.value,
                "capabilities": info.capabilities,
                "initialized": info.initialized,
                "requires_db": info.requires_db,
                "requires_api": info.requires_api,
                "description": info.description,
            }
            for agent_id, info in self.agents.items()
        }

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific agent.

        Args:
            agent_id: Worker identifier

        Returns:
            Worker information dict or None
        """
        if agent_id not in self.agents:
            return None

        info = self.agents[agent_id]
        return {
            "agent_id": info.agent_id,
            "domain": info.domain.value,
            "capabilities": info.capabilities,
            "initialized": info.initialized,
            "requires_db": info.requires_db,
            "requires_api": info.requires_api,
            "description": info.description,
        }

    def search_agents(self, query: str) -> List[str]:
        """
        Search agents by query string (searches in capabilities and descriptions).

        Args:
            query: Search query

        Returns:
            List of matching worker IDs

        Example:
            >>> registry = AgentRegistry()
            >>> agents = registry.search_agents("luft")
            >>> print(workers)  # Workers with air quality capabilities
        """
        query_lower = query.lower()
        matching_agents = []

        for agent_id, info in self.agents.items():
            # Search in capabilities
            if any(query_lower in cap.lower() for cap in info.capabilities):
                matching_agents.append(agent_id)
                continue

            # Search in description
            if query_lower in info.description.lower():
                matching_agents.append(agent_id)
                continue

        return matching_agents


# Singleton instance
_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry(db_pool=None, api_config=None) -> AgentRegistry:
    """
    Get or create worker registry singleton.

    Args:
        db_pool: Database connection pool (optional)
        api_config: API configuration (optional)

    Returns:
        AgentRegistry instance

    Example:
        >>> registry = get_agent_registry()
        >>> agent = registry.get_agent("EnvironmentalAgent")
    """
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry(db_pool=db_pool, api_config=api_config)
    return _agent_registry


def reset_agent_registry():
    """
    Reset the worker registry singleton (useful for testing).

    Example:
        >>> reset_agent_registry()
        >>> registry = get_agent_registry()  # Creates new instance
    """
    global _agent_registry
    _agent_registry = None


# Convenience functions
def get_agent(agent_id: str) -> Optional[Any]:
    """Convenience function to get a worker from the global registry"""
    return get_agent_registry().get_agent(agent_id)


def list_agents() -> Dict[str, Any]:
    """Convenience function to list all agents"""
    return get_agent_registry().list_available_workers()


def search_agents(query: str) -> List[str]:
    """Convenience function to search agents"""
    return get_agent_registry().search_agents(query)


if __name__ == "__main__":
    # Demo usage
    print("=" * 80)
    print("VERITAS WORKER REGISTRY - DEMO")
    print("=" * 80)

    # Initialize registry
    registry = AgentRegistry()

    # List all agents
    print("\n📋 AVAILABLE WORKERS:")
    print("-" * 80)
    for agent_id, info in registry.list_available_workers().items():
        print(f"\n{agent_id}:")
        print(f"  Domain: {info['domain']}")
        print(f"  Capabilities: {', '.join(info['capabilities'][:5])}...")
        print(f"  Description: {info['description']}")

    # Search agents
    print("\n\n🔍 SEARCH: 'luft'")
    print("-" * 80)
    results = registry.search_agents("luft")
    print(f"Found {len(results)} agents: {results}")

    # Get worker by domain
    print("\n\n🌍 ENVIRONMENTAL DOMAIN WORKERS:")
    print("-" * 80)
    env_agents = registry.get_agents_by_domain(AgentDomain.ENVIRONMENTAL)
    print(f"Found {len(env_workers)} agents: {env_workers}")

    print("\n" + "=" * 80)
    print("✅ Agent Registry Demo Complete!")
    print("=" * 80)
