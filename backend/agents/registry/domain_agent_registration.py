"""
VERITAS Domain Agent Registry - Zentrale Agent-Registrierung
=============================================================

Registriert alle 38 Domain Agents im VERITAS Framework.
Enables:
- Agent Discovery
- Capability Matching
- Lifecycle Management
- Instance Pooling
- Performance Monitoring

Verwendung:
    from backend.agents.registry.domain_agent_registration import register_all_domain_agents
    register_all_domain_agents()

Author: VERITAS Framework Migration v2.0
Date: 2025-12-04
"""

import logging
from enum import Enum
from typing import Callable, Dict, List, Optional

from backend.agents.registry.api_agent_registry import AgentCapability, AgentLifecycleType, get_agent_registry

logger = logging.getLogger(__name__)


# =========================================================================
# Domain Agent Registration Groups
# =========================================================================


class AgentGroup(Enum):
    """Agent categorization for organized registration"""

    WEATHER = "weather"
    CONSTRUCTION = "construction"
    ENVIRONMENTAL = "environmental"
    LEGAL = "legal"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    DATABASE = "database"
    SPECIALIZED = "specialized"


# =========================================================================
# Phase 1: Critical Agents (Already Migrated)
# =========================================================================


def register_phase1_agents() -> Dict[str, bool]:
    """
    Register Phase 1 - Top 5 Critical Agents (Already BaseAgent-compatible)

    Agents:
    1. DwdWeatherAgent - Weather data
    2. GenehmigungAgent - Construction permitting
    3. ConstructionAgent - General construction
    4. EnvironmentalAgent - Environmental data
    5. VerwaltungsrechtWorker - Administrative law
    """
    registry = get_agent_registry()
    results = {}

    # =====================================================================
    # 1. Weather Agent
    # =====================================================================
    try:
        from backend.agents.domain.weather.dwd_weather_agent_v3_framework import DwdWeatherAgent

        registry.register_agent(
            agent_type="weather_dwd",
            agent_class=DwdWeatherAgent,
            capabilities=[AgentCapability.WEATHER_DATA, AgentCapability.EXTERNAL_API, AgentCapability.REAL_TIME_PROCESSING],
            lifecycle_type=AgentLifecycleType.POOLED,
            max_concurrent_instances=3,
            priority=1,
            description="Deutscher Wetterdienst (DWD) Wetterdaten Integration",
        )
        logger.info("✅ DwdWeatherAgent registered")
        results["weather_dwd"] = True
    except Exception as e:
        logger.error(f"❌ Failed to register DwdWeatherAgent: {e}")
        results["weather_dwd"] = False

    # =====================================================================
    # 2. Genehmigung Agent (Construction Permitting)
    # =====================================================================
    try:
        from backend.agents.domain.construction.genehmigung_agent import GenehmigungAgent

        registry.register_agent(
            agent_type="genehmigung",
            agent_class=GenehmigungAgent,
            capabilities=[AgentCapability.LEGAL_FRAMEWORK, AgentCapability.DOMAIN_SPECIFIC_PROCESSING],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=1,
            description="Baugenehmigungsverfahren und Verwaltungsrecht",
        )
        logger.info("✅ GenehmigungAgent registered")
        results["genehmigung"] = True
    except Exception as e:
        logger.error(f"❌ Failed to register GenehmigungAgent: {e}")
        results["genehmigung"] = False

    # =====================================================================
    # 3. Construction Agent
    # =====================================================================
    try:
        from backend.agents.domain.construction.construction_agent_v2_framework import ConstructionAgent

        registry.register_agent(
            agent_type="construction",
            agent_class=ConstructionAgent,
            capabilities=[AgentCapability.LEGAL_FRAMEWORK, AgentCapability.DOMAIN_SPECIFIC_PROCESSING],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=1,
            description="Bau- und Stadtplanungsrecht",
        )
        logger.info("✅ ConstructionAgent registered")
        results["construction"] = True
    except Exception as e:
        logger.error(f"❌ Failed to register ConstructionAgent: {e}")
        results["construction"] = False

    # =====================================================================
    # 4. Environmental Agent (domain/)
    # =====================================================================
    try:
        from backend.agents.domain.environmental.environmental_agent_v2_framework import EnvironmentalAgent

        registry.register_agent(
            agent_type="environmental",
            agent_class=EnvironmentalAgent,
            capabilities=[AgentCapability.ENVIRONMENTAL_DATA, AgentCapability.DOMAIN_SPECIFIC_PROCESSING],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=1,
            description="Umweltschutz, Gewässerschutz und Naturschutz",
        )
        logger.info("✅ EnvironmentalAgent registered")
        results["environmental"] = True
    except Exception as e:
        logger.error(f"❌ Failed to register EnvironmentalAgent: {e}")
        results["environmental"] = False

    # =====================================================================
    # 5. Verwaltungsrecht Worker
    # =====================================================================
    try:
        from backend.agents.domain.social.verwaltungsrecht_worker import VerwaltungsrechtWorker

        registry.register_agent(
            agent_type="verwaltungsrecht",
            agent_class=VerwaltungsrechtWorker,
            capabilities=[AgentCapability.LEGAL_FRAMEWORK, AgentCapability.DOMAIN_SPECIFIC_PROCESSING],
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=2,
            priority=1,
            description="Verwaltungsrecht und Administrative Verfahren",
        )
        logger.info("✅ VerwaltungsrechtWorker registered")
        results["verwaltungsrecht"] = True
    except Exception as e:
        logger.error(f"❌ Failed to register VerwaltungsrechtWorker: {e}")
        results["verwaltungsrecht"] = False

    return results


# =========================================================================
# Phase 2: Additional Agents (Migrated 2025-12-04)
# =========================================================================


def register_phase2_agents() -> Dict[str, bool]:
    """
    Register Phase 2 - 5 Agents (BaseAgent v2.0 Framework)

    Categories:
    - Weather: BrightSkyWeatherAgent
    - Environmental: NaturschutzAgent, BodenGewaesserschutzAgent, EmissionenMonitoringAgent
    - Immissionsschutz: ImmissionsschutzAgent
    """
    registry = get_agent_registry()
    results = {}

    # =====================================================================
    # 1. Naturschutz Agent
    # =====================================================================
    try:
        from backend.agents.domain.environmental.naturschutz_agent_v2_framework import NaturschutzAgent

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
        logger.info("✅ NaturschutzAgent registered")
        results["naturschutz"] = True
    except Exception as e:
        logger.error(f"❌ Failed to register NaturschutzAgent: {e}")
        results["naturschutz"] = False

    # =====================================================================
    # 2. Boden-Gewässerschutz Agent
    # =====================================================================
    try:
        from backend.agents.domain.environmental.boden_gewaesserschutz_agent_v2_framework import BodenGewaesserschutzAgent

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
        logger.info("✅ BodenGewaesserschutzAgent registered")
        results["boden_gewaesserschutz"] = True
    except Exception as e:
        logger.error(f"❌ Failed to register BodenGewaesserschutzAgent: {e}")
        results["boden_gewaesserschutz"] = False

    # =====================================================================
    # 3. Emissionen Monitoring Agent
    # =====================================================================
    try:
        from backend.agents.domain.environmental.emissionen_monitoring_agent_v2_framework import EmissionenMonitoringAgent

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
        logger.info("✅ EmissionenMonitoringAgent registered")
        results["emissionen_monitoring"] = True
    except Exception as e:
        logger.error(f"❌ Failed to register EmissionenMonitoringAgent: {e}")
        results["emissionen_monitoring"] = False

    # =====================================================================
    # 4. Immissionsschutz Agent
    # =====================================================================
    try:
        from backend.agents.domain.immissionsschutz.immissionsschutz_agent_v2_framework import ImmissionsschutzAgent

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
        logger.info("✅ ImmissionsschutzAgent registered")
        results["immissionsschutz"] = True
    except Exception as e:
        logger.error(f"❌ Failed to register ImmissionsschutzAgent: {e}")
        results["immissionsschutz"] = False

    # =====================================================================
    # 5. BrightSky Weather Agent
    # =====================================================================
    try:
        from backend.agents.domain.weather.brightsky_weather_agent_v2_framework import BrightSkyWeatherAgent

        registry.register_agent(
            agent_type="brightsky_weather",
            agent_class=BrightSkyWeatherAgent,
            capabilities=[
                AgentCapability.QUERY_PROCESSING,
                AgentCapability.WEATHER_DATA,
                AgentCapability.EXTERNAL_API,
                AgentCapability.REAL_TIME_PROCESSING,
            ],
            lifecycle_type=AgentLifecycleType.POOLED,
            max_concurrent_instances=3,
            priority=2,
            description="Bright Sky Weather API (DWD Daten)",
        )
        logger.info("✅ BrightSkyWeatherAgent registered")
        results["brightsky_weather"] = True
    except Exception as e:
        logger.error(f"❌ Failed to register BrightSkyWeatherAgent: {e}")
        results["brightsky_weather"] = False

    logger.info(f"✅ Phase 2: {sum(results.values())}/{len(results)} agents registered successfully")
    return results


# =========================================================================
# Phase 3: Remaining Agents
# =========================================================================


def register_phase3_agents() -> Dict[str, bool]:
    """
    Register Phase 3 - Remaining 10 Agents

    Categories:
    - Social Services (SocialAgent, VerwaltungsrechtAgent, RechtsrechercheAgent, VerwaltungsprozessAgent)
    - Financial (FinancialAgent)
    - Standards (TechnicalStandardsAgent)
    - Chemical (ChemicalDataAgent)
    - Knowledge (WikipediaAgent)
    - Transport (TrafficAgent)
    - Data (DatabaseAgent)

    All migrated to BaseAgent v2.0 framework with unified pattern
    """
    registry = get_agent_registry()
    results = {}

    # Social Agents (4 agents)
    try:
        from backend.agents.domain.social.social_agent_v2_framework import register_social_agent

        results["SocialAgent"] = register_social_agent()
        logger.info("✅ SocialAgent v2.0 registered")
    except Exception as e:
        results["SocialAgent"] = False
        logger.error(f"❌ Failed to register SocialAgent: {e}")

    try:
        from backend.agents.domain.social.verwaltungsrecht_agent_v2_framework import register_verwaltungsrecht_agent

        results["VerwaltungsrechtAgent"] = register_verwaltungsrecht_agent()
        logger.info("✅ VerwaltungsrechtAgent v2.0 registered")
    except Exception as e:
        results["VerwaltungsrechtAgent"] = False
        logger.error(f"❌ Failed to register VerwaltungsrechtAgent: {e}")

    try:
        from backend.agents.domain.social.rechtsrecherche_agent_v2_framework import register_rechtsrecherche_agent

        results["RechtsrechercheAgent"] = register_rechtsrecherche_agent()
        logger.info("✅ RechtsrechercheAgent v2.0 registered")
    except Exception as e:
        results["RechtsrechercheAgent"] = False
        logger.error(f"❌ Failed to register RechtsrechercheAgent: {e}")

    try:
        from backend.agents.domain.social.verwaltungsprozess_agent_v2_framework import register_verwaltungsprozess_agent

        results["VerwaltungsprozessAgent"] = register_verwaltungsprozess_agent()
        logger.info("✅ VerwaltungsprozessAgent v2.0 registered")
    except Exception as e:
        results["VerwaltungsprozessAgent"] = False
        logger.error(f"❌ Failed to register VerwaltungsprozessAgent: {e}")

    # Financial Agent (1 agent)
    try:
        from backend.agents.domain.financial.financial_agent_v2_framework import register_financial_agent

        results["FinancialAgent"] = register_financial_agent()
        logger.info("✅ FinancialAgent v2.0 registered")
    except Exception as e:
        results["FinancialAgent"] = False
        logger.error(f"❌ Failed to register FinancialAgent: {e}")

    # Standards Agent (1 agent)
    try:
        from backend.agents.domain.standards.technical_standards_agent_v2_framework import register_technical_standards_agent

        results["TechnicalStandardsAgent"] = register_technical_standards_agent()
        logger.info("✅ TechnicalStandardsAgent v2.0 registered")
    except Exception as e:
        results["TechnicalStandardsAgent"] = False
        logger.error(f"❌ Failed to register TechnicalStandardsAgent: {e}")

    # Chemical Agent (1 agent)
    try:
        from backend.agents.domain.chemical.chemical_data_agent_v2_framework import register_chemical_data_agent

        results["ChemicalDataAgent"] = register_chemical_data_agent()
        logger.info("✅ ChemicalDataAgent v2.0 registered")
    except Exception as e:
        results["ChemicalDataAgent"] = False
        logger.error(f"❌ Failed to register ChemicalDataAgent: {e}")

    # Wikipedia Agent (1 agent)
    try:
        from backend.agents.domain.wikipedia.wikipedia_agent_v2_framework import register_wikipedia_agent

        results["WikipediaAgent"] = register_wikipedia_agent()
        logger.info("✅ WikipediaAgent v2.0 registered")
    except Exception as e:
        results["WikipediaAgent"] = False
        logger.error(f"❌ Failed to register WikipediaAgent: {e}")

    # Traffic Agent (1 agent)
    try:
        from backend.agents.domain.traffic.traffic_agent_v2_framework import register_traffic_agent

        results["TrafficAgent"] = register_traffic_agent()
        logger.info("✅ TrafficAgent v2.0 registered")
    except Exception as e:
        results["TrafficAgent"] = False
        logger.error(f"❌ Failed to register TrafficAgent: {e}")

    # Database Agent (1 agent)
    try:
        from backend.agents.domain.database.database_agent_v2_framework import register_database_agent

        results["DatabaseAgent"] = register_database_agent()
        logger.info("✅ DatabaseAgent v2.0 registered")
    except Exception as e:
        results["DatabaseAgent"] = False
        logger.error(f"❌ Failed to register DatabaseAgent: {e}")

    # Summary
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    logger.info(f"📊 Phase 3: {passed}/{total} agents registered successfully")

    return results


# =========================================================================
# Main Registration Function (UPDATED - includes Phase 4 Visualization)
# =========================================================================


def register_all_domain_agents(phase: str = "all") -> Dict[str, bool]:
    """
    Register all Domain Agents in VERITAS Registry

    Args:
        phase: "all" (default), "1", "2", "3", "viz", "visualization"

    Returns:
        Dict[str, bool] - Registration status for each agent

    Example:
        >>> from backend.agents.registry.domain_agent_registration import register_all_domain_agents
        >>> results = register_all_domain_agents(phase="all")
        >>> for agent, success in results.items():
        ...     print(f"{agent}: {'✅' if success else '❌'}")
    """
    logger.info(f"🚀 Starting Domain Agent Registration (Phase: {phase})")

    all_results = {}

    try:
        if phase in ("all", "1"):
            logger.info("📍 Phase 1: Critical Agents")
            results = register_phase1_agents()
            all_results.update(results)

        if phase in ("all", "2"):
            logger.info("📍 Phase 2: Additional Agents")
            results = register_phase2_agents()
            all_results.update(results)

        if phase in ("all", "3"):
            logger.info("📍 Phase 3: Remaining Agents")
            results = register_phase3_agents()
            all_results.update(results)

        if phase in ("all", "viz", "visualization", "4"):
            logger.info("📍 Phase 4: Visualization & Generation Agents")
            results = register_visualization_agents()
            all_results.update(results)

    except Exception as e:
        logger.error(f"❌ Registration failed: {e}", exc_info=True)
        return {}

    # Summary
    successful = sum(1 for v in all_results.values() if v)
    total = len(all_results)
    logger.info(f"✅ Registration complete: {successful}/{total} agents registered")

    return all_results


# =========================================================================
# Capability Mapping
# =========================================================================

DOMAIN_AGENT_CAPABILITIES = {
    # Weather Agents
    "weather_dwd": [AgentCapability.WEATHER_DATA, AgentCapability.EXTERNAL_API, AgentCapability.REAL_TIME_PROCESSING],
    # Construction Agents
    "genehmigung": [AgentCapability.LEGAL_FRAMEWORK_ANALYSIS, AgentCapability.BUILDING_PERMIT_PROCESSING],
    "construction": [AgentCapability.LEGAL_FRAMEWORK_ANALYSIS, AgentCapability.BUILDING_PERMIT_PROCESSING],
    # Environmental Agents
    "environmental": [AgentCapability.ENVIRONMENTAL_DATA_PROCESSING, AgentCapability.EXTERNAL_API],
    "immissionsschutz": [AgentCapability.LEGAL_FRAMEWORK_ANALYSIS, AgentCapability.ENVIRONMENTAL_DATA_PROCESSING],
    # Legal Agents
    "verwaltungsrecht": [AgentCapability.LEGAL_FRAMEWORK_ANALYSIS, AgentCapability.PROCESS_GUIDANCE],
    "rechtsrecherche": [AgentCapability.LEGAL_FRAMEWORK_ANALYSIS, AgentCapability.KNOWLEDGE_SYNTHESIS],
    # Technical Agents
    "technical_standards": [AgentCapability.QUERY_PROCESSING, AgentCapability.KNOWLEDGE_SYNTHESIS],
    # Database Agents
    "database": [AgentCapability.DOCUMENT_RETRIEVAL, AgentCapability.DATA_ANALYSIS],
    # Financial Agents
    "financial": [AgentCapability.TAXATION_PROCESSING, AgentCapability.DATA_ANALYSIS],
    # Wikipedia
    "wikipedia": [AgentCapability.KNOWLEDGE_SYNTHESIS, AgentCapability.EXTERNAL_API],
    # Visualization & Generation Agents (NEW - 2025-12-04)
    "chart_engine": [AgentCapability.CHART_GENERATION, AgentCapability.DATA_ANALYSIS],
    "presentation_canvas": [
        AgentCapability.PRESENTATION_CREATION,
        AgentCapability.VISUAL_DESIGN,
        AgentCapability.CHART_GENERATION,
    ],
    "image_generation": [AgentCapability.IMAGE_GENERATION, AgentCapability.VISUAL_DESIGN],
    "geo_map": [AgentCapability.MAP_GENERATION, AgentCapability.GEO_DATA_PROCESSING, AgentCapability.DATA_ANALYSIS],
}


# =========================================================================
# Phase 4: Visualization & Generation Agents (NEW - 2025-12-04)
# =========================================================================


def register_visualization_agents() -> Dict[str, bool]:
    """
    Register Phase 4 Visualization & Generation agents

    Agents:
    - ChartEngineAgent: Chart/Graph generation
    - PresentationCanvasAgent: Presentation creation (VDL)
    - ImageGenerationAgent: AI image generation (SwarmUI + Stable Diffusion)

    Returns:
        Dict with registration results per agent
    """
    from backend.agents.registry.api_agent_registry import AgentCapability, AgentLifecycleType, get_agent_registry

    registry = get_agent_registry()
    results = {}

    # Chart Engine Agent
    try:
        from backend.visualization.chart_engine import ChartManager, get_chart_manager

        # Use singleton pattern
        chart_manager = get_chart_manager()

        success = registry.register_agent(
            agent_type="chart_engine",
            agent_class=ChartManager,
            capabilities={AgentCapability.CHART_GENERATION, AgentCapability.DATA_ANALYSIS},
            lifecycle_type=AgentLifecycleType.SINGLETON,
            max_concurrent_instances=1,
            priority=8,
            description="Chart/Graph generation engine - 8 chart types, JSON/HTML/PNG/SVG export",
        )
        results["chart_engine"] = success
        if success:
            logger.info("✅ ChartEngineAgent registered successfully")
    except Exception as e:
        logger.error(f"❌ ChartEngineAgent registration failed: {e}")
        results["chart_engine"] = False

    # Presentation Canvas Agent
    try:
        from backend.agents.presentation_canvas_agent import PresentationCanvasAgent

        success = registry.register_agent(
            agent_type="presentation_canvas",
            agent_class=PresentationCanvasAgent,
            capabilities={
                AgentCapability.PRESENTATION_CREATION,
                AgentCapability.VISUAL_DESIGN,
                AgentCapability.CHART_GENERATION,
            },
            lifecycle_type=AgentLifecycleType.SINGLETON,
            max_concurrent_instances=1,
            priority=9,
            description="Presentation creation with VDL (Visual Description Language) - PowerPoint export",
        )
        results["presentation_canvas"] = success
        if success:
            logger.info("✅ PresentationCanvasAgent registered successfully")
    except Exception as e:
        logger.error(f"❌ PresentationCanvasAgent registration failed: {e}")
        results["presentation_canvas"] = False

    # Image Generation Agent
    try:
        from backend.imaging.integration import ImageGenerationAgent, get_image_generation_agent

        # Use singleton pattern
        image_agent = get_image_generation_agent()

        success = registry.register_agent(
            agent_type="image_generation",
            agent_class=ImageGenerationAgent,
            capabilities={AgentCapability.IMAGE_GENERATION, AgentCapability.VISUAL_DESIGN},
            lifecycle_type=AgentLifecycleType.ON_DEMAND,
            max_concurrent_instances=3,
            priority=7,
            description="AI image generation via SwarmUI + Stable Diffusion - 5 models, 5 tasks",
        )
        results["image_generation"] = success
        if success:
            logger.info("✅ ImageGenerationAgent registered successfully")
    except Exception as e:
        logger.error(f"❌ ImageGenerationAgent registration failed: {e}")
        results["image_generation"] = False

    # 4. Geo Map Agent (OSM)
    try:
        from backend.agents.geo_sub_agent import GeoSubAgent

        success = registry.register_agent(
            agent_type="geo_map",
            agent_class=GeoSubAgent,
            capabilities={AgentCapability.MAP_GENERATION, AgentCapability.GEO_DATA_PROCESSING, AgentCapability.DATA_ANALYSIS},
            lifecycle_type=AgentLifecycleType.SINGLETON,
            max_concurrent_instances=1,
            priority=8,
            description="OSM map generation with coordinate transformation (ETRS89→WGS84)",
        )
        results["geo_map"] = success
        if success:
            logger.info("✅ GeoMapAgent registered successfully")
    except Exception as e:
        logger.error(f"❌ GeoMapAgent registration failed: {e}")
        results["geo_map"] = False

    return results


# =========================================================================
# Auto-Registration on Import
# =========================================================================


def auto_register_on_startup():
    """
    Automatically register all agents on application startup.

    Add to backend initialization:
        from backend.agents.registry.domain_agent_registration import auto_register_on_startup
        auto_register_on_startup()
    """
    try:
        logger.info("⏳ Auto-registering domain agents on startup...")
        results = register_all_domain_agents(phase="all")  # All phases including viz
        successful = sum(1 for v in results.values() if v)
        logger.info(f"✅ Auto-registration complete: {successful}/{len(results)} agents")
    except Exception as e:
        logger.error(f"⚠️ Auto-registration failed: {e}")


# =========================================================================
# Testing
# =========================================================================

if __name__ == "__main__":
    import asyncio

    async def test_registration():
        """Test domain agent registration"""
        print("\n=== VERITAS Domain Agent Registration Test ===\n")

        # Register all agents including visualization
        results = register_all_domain_agents(phase="all")

        print("\nRegistration Results:")
        print("-" * 50)
        for agent_type, success in results.items():
            status = "✅ Registered" if success else "❌ Failed"
            print(f"  {agent_type:30} {status}")

        # Try to get agent
        print("\nAgent Discovery Test:")
        print("-" * 50)
        registry = get_agent_registry()
        try:
            # Test weather capability
            weather_agents = registry.get_agents_by_capability("weather_data")
            print(f"  Found {len(weather_agents)} agent(s) with WEATHER_DATA capability")

            # Test visualization capabilities
            from backend.agents.registry.api_agent_registry import AgentCapability

            chart_agents = registry.get_agents_for_capability(AgentCapability.CHART_GENERATION)
            print(f"  Found {len(chart_agents)} agent(s) with CHART_GENERATION capability")

            image_agents = registry.get_agents_for_capability(AgentCapability.IMAGE_GENERATION)
            print(f"  Found {len(image_agents)} agent(s) with IMAGE_GENERATION capability")

            agent = registry.get_agent_for_capability(AgentCapability.WEATHER_DATA)
            if agent:
                print(f"  ✅ Got agent instance: {agent.get_agent_type()}")
        except Exception as e:
            print(f"  ⚠️ Discovery test failed: {e}")

    asyncio.run(test_registration())
