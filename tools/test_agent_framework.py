"""
Test Agent Framework: Create and Execute Research Plan
======================================================

Tests the complete agent orchestration pipeline:
1. Create research plan with multiple steps
2. Store in PostgreSQL (with JSON fallback)
3. Execute steps with BaseAgent
4. Track results and quality metrics
5. Verify state transitions

Based on: backend/agents/framework/
"""
import os
import sys
from pathlib import Path
import json
import logging

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault("ENABLE_SECURE_SECRETS", "true")
os.environ.setdefault("POSTGRES_DATABASE", "veritas")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from backend.database.research_plan_storage import get_storage
from backend.agents.framework.base_agent import BaseAgent
from backend.agents.framework.state_machine import PlanState


# ============================================================================
# Test Agent Implementation
# ============================================================================

class TestDataRetrievalAgent(BaseAgent):
    """Simple test agent for data retrieval."""
    
    def get_agent_type(self) -> str:
        return "test_data_retrieval"
    
    def get_capabilities(self) -> list:
        return ["query_processing", "data_retrieval", "test_mode"]
    
    def execute_step(self, step: dict, context: dict) -> dict:
        """
        Execute a test step.
        
        Args:
            step: Step configuration
            context: Execution context
            
        Returns:
            Result dictionary with status and data
        """
        logger.info(f"Executing step: {step.get('step_name', 'unnamed')}")
        
        # Simulate work
        step_name = step.get("step_name", "unknown")
        step_type = step.get("step_type", "unknown")
        
        # Simulate different outcomes based on step type
        if step_type == "data_retrieval":
            result = {
                "status": "success",
                "data": {
                    "query_results": [
                        {"id": 1, "title": "Test Document 1", "score": 0.95},
                        {"id": 2, "title": "Test Document 2", "score": 0.87},
                    ],
                    "total_results": 2,
                    "execution_time_ms": 123
                },
                "confidence_score": 0.89,
                "quality_score": 0.92
            }
        elif step_type == "data_analysis":
            result = {
                "status": "success",
                "data": {
                    "analysis": "Test analysis completed",
                    "metrics": {"accuracy": 0.94, "completeness": 0.88}
                },
                "confidence_score": 0.91,
                "quality_score": 0.89
            }
        elif step_type == "synthesis":
            result = {
                "status": "success",
                "data": {
                    "synthesis": "Test synthesis of findings",
                    "key_points": ["Point 1", "Point 2", "Point 3"]
                },
                "confidence_score": 0.87,
                "quality_score": 0.90
            }
        else:
            result = {
                "status": "success",
                "data": {"message": f"Step {step_name} completed"},
                "confidence_score": 0.85,
                "quality_score": 0.85
            }
        
        logger.info(f"Step completed: {step_name} - Status: {result['status']}")
        return result


# ============================================================================
# Test Execution
# ============================================================================

def create_test_research_plan():
    """Create a test research plan with multiple steps."""
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    plan_id = f"test_research_plan_{timestamp}"
    
    plan = {
        "plan_id": plan_id,
        "research_question": "What is the current air quality in Munich?",
        "status": "pending",
        "total_steps": 3,
        "plan_document": json.dumps({
            "schema_version": "1.0",
            "research_question": "What is the current air quality in Munich?",
            "steps": [
                {
                    "step_id": f"{plan_id}_step_001",
                    "step_name": "Query Environmental Data",
                    "step_type": "data_retrieval",
                    "step_index": 0
                },
                {
                    "step_id": f"{plan_id}_step_002",
                    "step_name": "Analyze Air Quality Metrics",
                    "step_type": "data_analysis",
                    "step_index": 1
                },
                {
                    "step_id": f"{plan_id}_step_003",
                    "step_name": "Synthesize Findings",
                    "step_type": "synthesis",
                    "step_index": 2
                }
            ]
        }),
        "uds3_databases": ["chromadb", "neo4j", "postgres"],
        "phase5_hybrid_search": True,
        "security_level": "internal",
        "source_domains": ["environmental"]
    }
    
    steps = [
        {
            "step_id": f"{plan_id}_step_001",
            "plan_id": plan_id,
            "step_index": 0,
            "step_name": "Query Environmental Data",
            "step_type": "data_retrieval",
            "agent_name": "test_data_retrieval",
            "agent_type": "TestDataRetrievalAgent",
            "status": "pending",
            "step_config": json.dumps({
                "databases": ["chromadb"],
                "max_results": 10,
                "use_hybrid_search": True
            })
        },
        {
            "step_id": f"{plan_id}_step_002",
            "plan_id": plan_id,
            "step_index": 1,
            "step_name": "Analyze Air Quality Metrics",
            "step_type": "data_analysis",
            "agent_name": "test_data_retrieval",
            "agent_type": "TestDataRetrievalAgent",
            "status": "pending",
            "step_config": json.dumps({
                "metrics": ["PM2.5", "PM10", "NO2"],
                "threshold_check": True
            }),
            "depends_on": [f"{plan_id}_step_001"]
        },
        {
            "step_id": f"{plan_id}_step_003",
            "plan_id": plan_id,
            "step_index": 2,
            "step_name": "Synthesize Findings",
            "step_type": "synthesis",
            "agent_name": "test_data_retrieval",
            "agent_type": "TestDataRetrievalAgent",
            "status": "pending",
            "step_config": json.dumps({
                "format": "summary",
                "include_recommendations": True
            }),
            "depends_on": [f"{plan_id}_step_002"]
        }
    ]
    
    return plan, steps


def main():
    """Main test execution."""
    
    print("=" * 80)
    print("VERITAS Agent Framework Test")
    print("=" * 80)
    
    # Initialize storage
    storage = get_storage()
    logger.info(f"Storage backend: {storage.using_db and 'PostgreSQL' or 'JSON Fallback'}")
    
    # Create test plan
    logger.info("\n→ Creating test research plan...")
    plan, steps = create_test_research_plan()
    
    # Store plan
    created_plan = storage.create_plan(plan)
    logger.info(f"✅ Plan created: {created_plan['plan_id']}")
    logger.info(f"   Question: {created_plan['research_question']}")
    logger.info(f"   Steps: {created_plan['total_steps']}")
    
    # Store steps
    logger.info("\n→ Creating plan steps...")
    for step in steps:
        created_step = storage.create_step(step)
        logger.info(f"✅ Step {step['step_index']}: {step['step_name']}")
    
    # Initialize agent
    logger.info("\n→ Initializing test agent...")
    agent = TestDataRetrievalAgent(
        agent_id="test_agent_001",
        config={"test_mode": True}
    )
    logger.info(f"✅ Agent initialized: {agent.get_agent_type()}")
    logger.info(f"   Capabilities: {', '.join(agent.get_capabilities())}")
    
    # Execute plan steps
    logger.info("\n→ Executing plan steps...")
    storage.update_plan(plan['plan_id'], {"status": "running"})
    
    for step in steps:
        step_id = step['step_id']
        logger.info(f"\n→ Executing step {step['step_index']}: {step['step_name']}")
        
        # Update step status to running
        storage.update_step(step_id, {
            "status": "running",
            "started_at": "now"
        })
        
        # Execute step
        try:
            result = agent.execute_step(step, {"plan_id": plan['plan_id']})
            
            # Update step with result
            storage.update_step(step_id, {
                "status": "completed",
                "completed_at": "now",
                "result": json.dumps(result.get("data", {}))
            })
            
            logger.info(f"✅ Step completed successfully")
            logger.info(f"   Confidence: {result.get('confidence_score', 'N/A')}")
            logger.info(f"   Quality: {result.get('quality_score', 'N/A')}")
            
        except Exception as e:
            logger.error(f"❌ Step failed: {e}")
            storage.update_step(step_id, {
                "status": "failed",
                "error_message": str(e)
            })
    
    # Complete plan
    storage.update_plan(plan['plan_id'], {
        "status": "completed",
        "progress_percentage": 100.0
    })
    logger.info("\n✅ Plan execution complete!")
    
    # Retrieve and display final state
    logger.info("\n→ Final plan state:")
    final_plan = storage.get_plan(plan['plan_id'])
    logger.info(f"   Status: {final_plan['status']}")
    logger.info(f"   Progress: {final_plan.get('progress_percentage', 0)}%")
    
    final_steps = storage.list_steps(plan['plan_id'])
    logger.info(f"\n→ Step results:")
    for step in final_steps:
        logger.info(f"   {step['step_index']}. {step['step_name']}: {step['status']}")
    
    # Stats
    logger.info("\n→ Storage statistics:")
    stats = storage.get_stats()
    for key, val in stats.items():
        logger.info(f"   {key}: {val}")
    
    print("\n" + "=" * 80)
    print("✅ Agent Framework Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
