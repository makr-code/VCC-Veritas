"""
VERITAS API v3 - Agent Router

Endpoints für Agent Management:
- GET /api/v3/agent/list - Liste aller Agents
- GET /api/v3/agent/:agent_id/info - Agent Details
- POST /api/v3/agent/:agent_id/execute - Agent direkt ausführen
- GET /api/v3/agent/capabilities - Agent Capabilities

Integration mit Intelligent Pipeline.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Path, Request

from .models import AgentExecuteRequest, AgentExecuteResponse, AgentInfo, StatusEnum, SuccessResponse
from .service_integration import execute_agent_directly, get_agents_from_pipeline, get_services_from_app

logger = logging.getLogger(__name__)

# Router
agent_router = APIRouter(prefix="/agent", tags=["Agent Management"])

# ============================================================================
# Helper Functions
# ============================================================================


def get_intelligent_pipeline(request: Request):
    """Holt Intelligent Pipeline aus App State"""
    services = get_services_from_app(request.app.state)
    pipeline = services.get("intelligent_pipeline")
    if not pipeline:
        raise HTTPException(status_code=503, detail="Intelligent Pipeline unavailable")
    return pipeline


# ============================================================================
# Endpoints
# ============================================================================


@agent_router.get("/list", response_model=List[AgentInfo])
async def list_agents(request: Request):
    """
    Liste aller verfügbaren Agents

    Gibt eine Liste aller registrierten Agents zurück mit ID, Name,
    Beschreibung, Capabilities und Status.

    Response:
        - Array von AgentInfo Objekten
        - agent_id: Eindeutige Agent ID
        - name: Agent Name
        - description: Agent Beschreibung
        - capabilities: Liste von Capabilities
        - status: active, inactive, error
        - version: Optional Agent Version
    """
    try:
        pipeline = get_intelligent_pipeline(request)

        # ✅ ECHTE BACKEND INTEGRATION
        logger.info("📋 Fetching agent list from Intelligent Pipeline")
        agents_list = get_agents_from_pipeline(pipeline)

        # Konvertiere zu AgentInfo Pydantic Models
        agent_infos = []
        for agent in agents_list:
            agent_infos.append(
                AgentInfo(
                    agent_id=agent["agent_id"],
                    name=agent["name"],
                    description=agent.get("description", ""),
                    capabilities=agent.get("capabilities", []),
                    status=agent.get("status", "active"),
                    version=agent.get("version", "1.0.0"),
                )
            )

        logger.info(f"✅ Retrieved {len(agent_infos)} agents")
        return agent_infos

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ List Agents Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@agent_router.get("/{agent_id}/info", response_model=AgentInfo)
async def get_agent_info(agent_id: str = Path(..., description="Agent ID"), request: Request = None):
    """
    Agent Details

    Gibt detaillierte Informationen über einen spezifischen Agent zurück.

    Path Parameters:
        - agent_id: Agent ID (z.B. environmental_agent)

    Response:
        - AgentInfo Objekt mit vollständigen Details

    Errors:
        - 404: Agent not found
        - 503: Pipeline unavailable
    """
    try:
        pipeline = get_intelligent_pipeline(request)

        # TODO: Integration mit Pipeline
        # agent = pipeline.get_agent(agent_id)

        # Platzhalter: Mock Agent
        if agent_id not in ["environmental_agent", "verwaltungsrecht_agent", "immissionsschutz_agent"]:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

        return AgentInfo(
            agent_id=agent_id,
            name=agent_id.replace("_", " ").title(),
            description=f"Detaillierte Informationen für {agent_id}",
            capabilities=["capability_1", "capability_2"],
            status="active",
            version="1.0.0",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get Agent Info Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get agent info: {str(e)}")


@agent_router.post("/{agent_id}/execute", response_model=AgentExecuteResponse)
async def execute_agent(
    agent_id: str = Path(..., description="Agent ID"), exec_req: AgentExecuteRequest = None, request: Request = None
):
    """
    Agent direkt ausführen

    Führt einen spezifischen Agent direkt aus (ohne Multi-Agent Orchestration).
    Nützlich für Testing oder spezifische Single-Agent Tasks.

    Path Parameters:
        - agent_id: Agent ID

    Request Body:
        - agent_id: Agent ID (muss mit Path Parameter übereinstimmen)
        - task: Task Beschreibung
        - parameters: Optional Task Parameters (Dict)
        - timeout: Timeout in Sekunden (1-600, default: 60)

    Response:
        - agent_id: Ausgeführter Agent
        - result: Execution Result (Dict)
        - status: pending, in_progress, completed, failed
        - duration: Execution Dauer (Sekunden)
        - timestamp: Execution Timestamp

    Errors:
        - 400: Invalid Request (agent_id mismatch)
        - 404: Agent not found
        - 408: Timeout
        - 503: Pipeline unavailable
    """
    try:
        # Validate agent_id
        if exec_req.agent_id != agent_id:
            raise HTTPException(status_code=400, detail=f"agent_id mismatch: path={agent_id}, body={exec_req.agent_id}")

        pipeline = get_intelligent_pipeline(request)

        # ✅ ECHTE BACKEND INTEGRATION
        logger.info(f"⚙️ Executing agent '{agent_id}' with task: '{exec_req.task[:50]}...'")

        # Execute Agent direkt
        result = await execute_agent_directly(
            agent_id=agent_id,
            task=exec_req.task,
            intelligent_pipeline=pipeline,
            parameters=exec_req.parameters,
            timeout=exec_req.timeout,
        )

        logger.info(f"✅ Agent '{agent_id}' completed: {result['duration']:.2f}s")

        return AgentExecuteResponse(
            agent_id=agent_id,
            result=result,
            status=StatusEnum.COMPLETED,
            duration=result.get("duration", 0),
            timestamp=datetime.now(),
        )

    except HTTPException:
        raise
    except ValueError as e:
        # Agent nicht gefunden
        raise HTTPException(status_code=404, detail=str(e))
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail=f"Agent execution timeout ({exec_req.timeout}s)")
    except Exception as e:
        logger.error(f"❌ Execute Agent Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@agent_router.get("/capabilities")
async def get_agent_capabilities(request: Request):
    """
    Agent Capabilities Overview

    Gibt einen Überblick über alle verfügbaren Agent Capabilities zurück.
    Gruppiert nach Agent-Typ.

    Response:
        - Dict mit Capability Groups
        - Jede Group enthält Agents und deren Capabilities

    Format:
        {
          "environmental": {
            "agents": ["environmental_agent"],
            "capabilities": ["environmental_law", "emissions"]
          },
          "legal": {
            "agents": ["verwaltungsrecht_agent"],
            "capabilities": ["administrative_law"]
          }
        }
    """
    try:
        pipeline = get_intelligent_pipeline(request)

        # TODO: Integration mit Pipeline
        # capabilities = pipeline.get_capabilities_overview()

        # Platzhalter: Mock Capabilities
        capabilities = {
            "environmental": {
                "agents": ["environmental_agent", "immissionsschutz_agent"],
                "capabilities": ["environmental_law", "emissions", "wind_turbines", "immissions", "noise", "air_quality"],
            },
            "legal": {
                "agents": ["verwaltungsrecht_agent"],
                "capabilities": ["administrative_law", "court_procedures", "legal_analysis"],
            },
            "technical": {
                "agents": ["construction_agent", "traffic_agent"],
                "capabilities": ["construction_permits", "traffic_analysis", "infrastructure"],
            },
        }

        return SuccessResponse(success=True, message="Agent capabilities retrieved", data={"capabilities": capabilities})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get Capabilities Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


__all__ = ["agent_router"]
