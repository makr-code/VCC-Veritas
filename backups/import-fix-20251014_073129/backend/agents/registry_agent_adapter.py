"""
Registry Agent Adapter - BaseAgent Integration
==============================================

Wraps the existing AgentRegistry system to work with the new BaseAgent framework.

This adapter:
- Exposes AgentRegistry capabilities through BaseAgent interface
- Handles agent discovery and capability matching
- Manages agent instance lifecycle
- Provides database persistence for registry operations

Author: VERITAS Development Team
Created: 2025-10-08
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

# Import BaseAgent framework
import sys
sys.path.insert(0, str(Path(__file__).parent / "framework"))

from framework.base_agent import BaseAgent

# Import existing AgentRegistry
from backend.agents.veritas_api_agent_registry import (
    AgentRegistry,
    AgentCapability,
    AgentLifecycleType,
    AgentStatus
)

logger = logging.getLogger(__name__)


class RegistryAgentAdapter(BaseAgent):
    """
    Adapter that wraps AgentRegistry for BaseAgent framework integration.
    
    This agent handles:
    - Agent registration and discovery
    - Capability-based agent selection
    - Agent instance management
    - Resource pool coordination
    
    Step Types Supported:
    - agent_registration: Register new agent type
    - agent_discovery: Find agents by capability
    - agent_instantiation: Create agent instance
    - capability_query: Query agent capabilities
    - instance_status: Check agent instance status
    """
    
    def __init__(self):
        """Initialize Registry Agent Adapter."""
        super().__init__()
        
        # Create or reuse AgentRegistry singleton
        self._registry = AgentRegistry()
        
        logger.info(
            f"Initialized RegistryAgentAdapter: {self.agent_id}"
        )
    
    def get_agent_type(self) -> str:
        """Return agent type identifier."""
        return "AgentRegistry"
    
    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this agent provides.
        
        Returns:
            List of capability strings
        """
        return [
            "agent_registration",
            "agent_discovery",
            "agent_instantiation",
            "capability_query",
            "instance_management",
            "resource_coordination"
        ]
    
    def execute_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a registry operation step.
        
        Args:
            step: Step definition with action and parameters
            context: Execution context
        
        Returns:
            Step execution result
        
        Example steps:
            {
                "action": "agent_registration",
                "parameters": {
                    "agent_type": "environmental",
                    "capabilities": ["environmental_analysis"],
                    "max_instances": 2
                }
            }
            
            {
                "action": "agent_discovery",
                "parameters": {
                    "capability": "environmental_analysis"
                }
            }
        """
        action = step.get("action", "")
        parameters = step.get("parameters", {})
        
        logger.info(
            f"Executing registry action: {action}"
        )
        
        # Route to appropriate handler
        if action == "agent_registration":
            return self._handle_registration(parameters)
        elif action == "agent_discovery":
            return self._handle_discovery(parameters)
        elif action == "agent_instantiation":
            return self._handle_instantiation(parameters)
        elif action == "capability_query":
            return self._handle_capability_query(parameters)
        elif action == "instance_status":
            return self._handle_instance_status(parameters)
        elif action == "registry_statistics":
            return self._handle_statistics(parameters)
        else:
            return {
                "status": "failed",
                "error": f"Unknown action: {action}",
                "quality_score": 0.0,
                "sources": [],
                "metadata": {"action": action}
            }
    
    def _handle_registration(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle agent registration.
        
        Parameters:
            agent_type: str - Agent type identifier
            capabilities: List[str] - List of capability names
            max_instances: int - Max concurrent instances (optional)
            lifecycle: str - Lifecycle type (optional)
            priority: int - Selection priority (optional)
            description: str - Agent description (optional)
        """
        try:
            agent_type = parameters.get("agent_type")
            capability_names = parameters.get("capabilities", [])
            max_instances = parameters.get("max_instances")
            lifecycle_str = parameters.get("lifecycle", "on_demand")
            priority = parameters.get("priority", 1)
            description = parameters.get("description", "")
            
            # Validate required parameters
            if not agent_type:
                raise ValueError("agent_type is required")
            
            # Convert capability names to enum
            capabilities = set()
            for cap_name in capability_names:
                try:
                    # Try to match capability
                    cap = AgentCapability[cap_name.upper()]
                    capabilities.add(cap)
                except KeyError:
                    logger.warning(
                        f"Unknown capability: {cap_name}, skipping"
                    )
            
            # Convert lifecycle string to enum
            lifecycle_map = {
                "on_demand": AgentLifecycleType.ON_DEMAND,
                "persistent": AgentLifecycleType.PERSISTENT,
                "pooled": AgentLifecycleType.POOLED
            }
            lifecycle = lifecycle_map.get(
                lifecycle_str.lower(),
                AgentLifecycleType.ON_DEMAND
            )
            
            # Note: For now, we register with a placeholder class
            # In production, this would load the actual agent class
            class PlaceholderAgent:
                def process_query(self, query, context):
                    return {"result": "placeholder"}
            
            # Register agent
            success = self._registry.register_agent(
                agent_type=agent_type,
                agent_class=PlaceholderAgent,
                capabilities=capabilities,
                lifecycle_type=lifecycle,
                max_concurrent_instances=max_instances,
                priority=priority,
                description=description
            )
            
            if success:
                return {
                    "status": "success",
                    "data": {
                        "agent_type": agent_type,
                        "capabilities": capability_names,
                        "max_instances": max_instances,
                        "lifecycle": lifecycle_str,
                        "registered": True
                    },
                    "quality_score": 1.0,
                    "sources": ["agent_registry"],
                    "metadata": {
                        "operation": "agent_registration",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            else:
                raise RuntimeError("Registration failed")
                
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "quality_score": 0.0,
                "sources": [],
                "metadata": {"operation": "agent_registration"}
            }
    
    def _handle_discovery(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle agent discovery by capability.
        
        Parameters:
            capability: str - Capability name to search for
        """
        try:
            capability_name = parameters.get("capability")
            
            if not capability_name:
                raise ValueError("capability is required")
            
            # Convert to enum
            try:
                capability = AgentCapability[capability_name.upper()]
            except KeyError:
                raise ValueError(
                    f"Unknown capability: {capability_name}"
                )
            
            # Find agents
            agent_types = self._registry.get_agents_for_capability(
                capability
            )
            
            return {
                "status": "success",
                "data": {
                    "capability": capability_name,
                    "agents": agent_types,
                    "count": len(agent_types)
                },
                "quality_score": 1.0 if agent_types else 0.5,
                "sources": ["agent_registry"],
                "metadata": {
                    "operation": "agent_discovery",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "quality_score": 0.0,
                "sources": [],
                "metadata": {"operation": "agent_discovery"}
            }
    
    def _handle_instantiation(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle agent instance creation.
        
        Parameters:
            agent_type: str - Agent type to instantiate
            query_id: str - Optional query ID for tracking
        """
        try:
            agent_type = parameters.get("agent_type")
            query_id = parameters.get("query_id")
            
            if not agent_type:
                raise ValueError("agent_type is required")
            
            # Get instance
            instance = self._registry.get_agent_instance(
                agent_type=agent_type,
                query_id=query_id
            )
            
            if instance:
                return {
                    "status": "success",
                    "data": {
                        "agent_type": agent_type,
                        "instance_created": True,
                        "query_id": query_id
                    },
                    "quality_score": 1.0,
                    "sources": ["agent_registry"],
                    "metadata": {
                        "operation": "agent_instantiation",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            else:
                raise RuntimeError(
                    f"Failed to create instance for {agent_type}"
                )
                
        except Exception as e:
            logger.error(f"Instantiation failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "quality_score": 0.0,
                "sources": [],
                "metadata": {"operation": "agent_instantiation"}
            }
    
    def _handle_capability_query(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Query all available capabilities in the registry.
        """
        try:
            # Get all registered capabilities
            capabilities = list(self._registry._capability_map.keys())
            
            capability_info = {}
            for cap in capabilities:
                agents = self._registry.get_agents_for_capability(cap)
                capability_info[cap.value] = {
                    "agents": agents,
                    "count": len(agents)
                }
            
            return {
                "status": "success",
                "data": {
                    "capabilities": capability_info,
                    "total_capabilities": len(capabilities)
                },
                "quality_score": 1.0,
                "sources": ["agent_registry"],
                "metadata": {
                    "operation": "capability_query",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Capability query failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "quality_score": 0.0,
                "sources": [],
                "metadata": {"operation": "capability_query"}
            }
    
    def _handle_instance_status(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get status of agent instances.
        
        Parameters:
            agent_type: str - Optional agent type filter
        """
        try:
            agent_type = parameters.get("agent_type")
            
            # Get active instances
            with self._registry._lock:
                active_instances = {}
                
                for inst_id, instance in self._registry._active_instances.items():
                    if agent_type and instance.agent_registration.agent_type != agent_type:
                        continue
                    
                    active_instances[inst_id] = {
                        "agent_type": instance.agent_registration.agent_type,
                        "status": instance.status.value,
                        "created_at": instance.created_at,
                        "query_id": instance.current_query_id
                    }
            
            return {
                "status": "success",
                "data": {
                    "active_instances": active_instances,
                    "count": len(active_instances),
                    "filter": agent_type
                },
                "quality_score": 1.0,
                "sources": ["agent_registry"],
                "metadata": {
                    "operation": "instance_status",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Instance status check failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "quality_score": 0.0,
                "sources": [],
                "metadata": {"operation": "instance_status"}
            }
    
    def _handle_statistics(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get registry statistics."""
        try:
            stats = self._registry.registry_stats.copy()
            
            # Add resource pool stats
            resource_stats = self._registry._shared_resources.resource_usage_stats.copy()
            
            return {
                "status": "success",
                "data": {
                    "registry_stats": stats,
                    "resource_stats": resource_stats
                },
                "quality_score": 1.0,
                "sources": ["agent_registry"],
                "metadata": {
                    "operation": "registry_statistics",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Statistics retrieval failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "quality_score": 0.0,
                "sources": [],
                "metadata": {"operation": "registry_statistics"}
            }


# Test the adapter
def _test_registry_adapter():
    """Test RegistryAgentAdapter functionality."""
    print("=" * 80)
    print("REGISTRY AGENT ADAPTER TEST")
    print("=" * 80)
    
    adapter = RegistryAgentAdapter()
    
    # Test 1: Register an agent
    print("\n[TEST 1] Agent Registration")
    result = adapter.execute_step(
        step={
            "action": "agent_registration",
            "parameters": {
                "agent_type": "environmental",
                "capabilities": ["environmental_data_processing", "data_analysis"],
                "max_instances": 2,
                "lifecycle": "on_demand",
                "description": "Environmental data analysis agent"
            }
        },
        context={}
    )
    print(f"Status: {result['status']}")
    print(f"Data: {result.get('data', {})}")
    assert result['status'] == 'success', "Registration should succeed"
    
    # Test 2: Discover agents by capability
    print("\n[TEST 2] Agent Discovery")
    result = adapter.execute_step(
        step={
            "action": "agent_discovery",
            "parameters": {
                "capability": "environmental_data_processing"
            }
        },
        context={}
    )
    print(f"Status: {result['status']}")
    print(f"Agents found: {result.get('data', {}).get('agents', [])}")
    assert result['status'] == 'success', "Discovery should succeed"
    assert 'environmental' in result['data']['agents'], "Should find environmental agent"
    
    # Test 3: Query capabilities
    print("\n[TEST 3] Capability Query")
    result = adapter.execute_step(
        step={
            "action": "capability_query",
            "parameters": {}
        },
        context={}
    )
    print(f"Status: {result['status']}")
    print(f"Total capabilities: {result.get('data', {}).get('total_capabilities', 0)}")
    assert result['status'] == 'success', "Capability query should succeed"
    
    # Test 4: Get statistics
    print("\n[TEST 4] Registry Statistics")
    result = adapter.execute_step(
        step={
            "action": "registry_statistics",
            "parameters": {}
        },
        context={}
    )
    print(f"Status: {result['status']}")
    print(f"Stats: {result.get('data', {}).get('registry_stats', {})}")
    assert result['status'] == 'success', "Statistics should be available"
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    _test_registry_adapter()
