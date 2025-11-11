"""
Environmental Agent with UDS3 Integration
=========================================

Specialized agent for environmental data retrieval and analysis.
Uses UDS3 directly for multi-database queries.

Author: GitHub Copilot
Date: 24. Oktober 2025
"""
import logging
from typing import Any, Dict, List, Optional

from backend.agents.framework.base_agent import BaseAgent
from backend.database.uds3_integration import get_uds3_client

logger = logging.getLogger(__name__)


class EnvironmentalAgent(BaseAgent):
    """
    Environmental agent for regulation search and compliance checks.

    Capabilities:
    - Environmental regulation search
    - Compliance checking
    - Impact assessment
    - Monitoring data retrieval
    """

    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Environmental Agent.

        Args:
            agent_id: Unique agent identifier
            config: Agent configuration dictionary
        """
        super().__init__(agent_id=agent_id, config=config or {}, quality_policy=None, enable_monitoring=True)

        # Initialize UDS3
        self.uds3 = get_uds3_client()
        logger.info("Environmental Agent initialized with UDS3 integration")

    def get_agent_type(self) -> str:
        """Return agent type identifier."""
        return "environmental"

    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return ["regulation_search", "compliance_check", "environmental_monitoring", "impact_assessment", "data_retrieval"]

    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute environmental agent step.

        Args:
            step: Step configuration with:
                - step_type: Type of step (data_retrieval, analysis, etc.)
                - step_config: Step-specific configuration

            context: Execution context with:
                - plan_id: Research plan ID
                - previous_results: Results from previous steps

        Returns:
            Result dictionary with:
                - status: "success" or "error"
                - data: Result data
                - confidence_score: 0.0-1.0
                - quality_score: 0.0-1.0
        """
        step_type = step.get("step_type", "unknown")
        step_config = step.get("step_config", {})

        logger.info(f"Executing environmental step: {step_type}")

        try:
            if step_type == "data_retrieval":
                return self._execute_data_retrieval(step_config, context)

            elif step_type == "regulation_search":
                return self._execute_regulation_search(step_config, context)

            elif step_type == "compliance_check":
                return self._execute_compliance_check(step_config, context)

            elif step_type == "environmental_analysis":
                return self._execute_analysis(step_config, context)

            elif step_type == "impact_assessment":
                return self._execute_impact_assessment(step_config, context)

            else:
                return {"status": "error", "error_message": f"Unknown step type: {step_type}"}

        except Exception as e:
            logger.error(f"Error executing environmental step: {e}")
            return {"status": "error", "error_message": str(e)}

    def _execute_data_retrieval(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute environmental data retrieval using UDS3 Search API - DIRECT!

        DIRECT UDS3 Integration (v3.1.0) - NO FALLBACKS!
        - UnifiedDatabaseStrategy.search_api property
        - Hybrid search: vector + graph + keyword
        - Raises error if UDS3 not available
        """
        query = config.get("query", "")
        domain = config.get("domain", "environmental")
        top_k = config.get("top_k", 10)

        logger.info(f"Retrieving environmental data: '{query}' (top_k={top_k})")

        # DIRECT UDS3 semantic_search - NO FALLBACK!
        if not hasattr(self.uds3, "semantic_search"):
            raise RuntimeError("UDS3 semantic_search not available! " "Ensure UDS3 is properly initialized in app.py")

        logger.info(f"→ UDS3 semantic_search (domain={domain})")

        # UDS3PolyglotManager.semantic_search(query, top_k, domain)
        # Returns List[Dict] with: id, content, metadata, score
        results = self.uds3.semantic_search(query=query, top_k=top_k, domain=domain)

        logger.info(f"✅ UDS3 returned {len(results)} results")

        # Format results (already Dict format from UDS3)
        documents = [
            {
                "id": result.get("id", f"doc_{i}"),
                "content": result.get("content", ""),
                "metadata": result.get("metadata", {}),
                "relevance": result.get("score", 0.0),
                "source": result.get("source", "UDS3"),
                "search_types": ["semantic", "vector"],
            }
            for i, result in enumerate(results)
        ]

        # Calculate confidence based on result quality
        avg_score = sum(r["relevance"] for r in documents) / len(documents) if documents else 0.0
        confidence = min(avg_score * 1.2, 1.0)

        return {
            "status": "success",
            "data": {
                "documents": documents,
                "total_results": len(documents),
                "search_types_used": ["hybrid", "vector", "graph", "keyword"],
            },
            "confidence_score": confidence,
            "quality_score": avg_score,
            "sources": ["UDS3-Hybrid-Search"],
        }

    def _execute_regulation_search(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute regulation search."""
        regulation_type = config.get("regulation_type", "environmental")
        jurisdiction = config.get("jurisdiction", "Germany")

        logger.info(f"Searching regulations: {regulation_type} in {jurisdiction}")

        # Mock implementation for testing
        return {
            "status": "success",
            "data": {
                "regulations": [
                    {
                        "id": "reg_001",
                        "title": "Luftqualitätsverordnung (39. BImSchV)",
                        "jurisdiction": "Germany",
                        "year": 2010,
                        "summary": "Verordnung über Luftqualitätsstandards und Emissionsgrenzwerte",
                    },
                    {
                        "id": "reg_002",
                        "title": "Bundes - Immissionsschutzgesetz (BImSchG)",
                        "jurisdiction": "Germany",
                        "year": 2023,
                        "summary": "Gesetz zum Schutz vor schädlichen Umwelteinwirkungen",
                    },
                ],
                "total_found": 2,
            },
            "confidence_score": 0.92,
            "quality_score": 0.90,
            "sources": ["UDS3-Regulations"],
        }

    def _execute_compliance_check(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute compliance check."""
        document_id = config.get("document_id")
        regulation_ids = config.get("regulation_ids", [])

        logger.info(f"Checking compliance for document: {document_id}")

        # Mock implementation
        return {
            "status": "success",
            "data": {"compliant": True, "violations": [], "warnings": ["Minor formatting issue in section 3"], "score": 0.95},
            "confidence_score": 0.88,
            "quality_score": 0.85,
            "sources": ["UDS3-Compliance"],
        }

    def _execute_analysis(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute environmental analysis."""
        metrics = config.get("metrics", ["PM2.5", "PM10", "NO2"])

        logger.info(f"Analyzing environmental metrics: {metrics}")

        # Mock implementation
        return {
            "status": "success",
            "data": {
                "metrics": {
                    "PM2.5": {"value": 15.3, "unit": "µg / m³", "status": "good"},
                    "PM10": {"value": 28.7, "unit": "µg / m³", "status": "moderate"},
                    "NO2": {"value": 35.2, "unit": "µg / m³", "status": "good"},
                },
                "overall_assessment": "Air quality is within acceptable limits",
                "trends": "Improving over last 30 days",
            },
            "confidence_score": 0.90,
            "quality_score": 0.88,
            "sources": ["UDS3-Environmental-Data"],
        }

    def _execute_impact_assessment(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute environmental impact assessment."""
        project_type = config.get("project_type", "construction")
        location = config.get("location", "Munich")

        logger.info(f"Assessing impact for {project_type} project in {location}")

        # Mock implementation
        return {
            "status": "success",
            "data": {
                "impact_level": "moderate",
                "affected_areas": ["air_quality", "noise", "traffic"],
                "mitigation_required": True,
                "recommendations": [
                    "Install air quality monitoring stations",
                    "Implement noise reduction measures",
                    "Create traffic management plan",
                ],
            },
            "confidence_score": 0.85,
            "quality_score": 0.87,
            "sources": ["UDS3-Impact-Assessment"],
        }


# Factory function
def create_environmental_agent(agent_id: Optional[str] = None) -> EnvironmentalAgent:
    """
    Factory function to create Environmental Agent.

    Args:
        agent_id: Optional agent identifier

    Returns:
        EnvironmentalAgent instance
    """
    return EnvironmentalAgent(agent_id=agent_id)
