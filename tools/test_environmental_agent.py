"""
Test Environmental Agent with UDS3
==================================

Tests the Environmental Agent with direct UDS3 integration.

Usage:
    python tools\test_environmental_agent.py
"""
import os
import sys
from pathlib import Path
import json
import logging

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure environment
os.environ.setdefault("POSTGRES_HOST", "192.168.178.94")
os.environ.setdefault("POSTGRES_DATABASE", "veritas")
os.environ.setdefault("CHROMA_HOST", "192.168.178.94")
os.environ.setdefault("NEO4J_URI", "bolt://192.168.178.94:7687")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from backend.agents.specialized.environmental_agent import create_environmental_agent
from backend.database.research_plan_storage import get_storage

# Direct UDS3 initialization for standalone testing
from uds3.core import UDS3PolyglotManager
from backend.database.uds3_integration import set_uds3_instance


def create_environmental_research_plan():
    """Create research plan for environmental agent testing."""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    plan_id = f"env_research_{timestamp}"
    
    plan = {
        "plan_id": plan_id,
        "research_question": "What are the current air quality regulations in Munich?",
        "status": "pending",
        "total_steps": 4,
        "plan_document": json.dumps({
            "schema_version": "1.0",
            "research_question": "What are the current air quality regulations in Munich?",
            "steps": [
                {
                    "step_id": f"{plan_id}_step_001",
                    "step_name": "Retrieve Environmental Data",
                    "step_type": "data_retrieval",
                    "step_index": 0
                },
                {
                    "step_id": f"{plan_id}_step_002",
                    "step_name": "Search Regulations",
                    "step_type": "regulation_search",
                    "step_index": 1
                },
                {
                    "step_id": f"{plan_id}_step_003",
                    "step_name": "Analyze Environmental Metrics",
                    "step_type": "environmental_analysis",
                    "step_index": 2
                },
                {
                    "step_id": f"{plan_id}_step_004",
                    "step_name": "Assess Impact",
                    "step_type": "impact_assessment",
                    "step_index": 3
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
            "step_name": "Retrieve Environmental Data",
            "step_type": "data_retrieval",
            "agent_name": "environmental",
            "agent_type": "EnvironmentalAgent",
            "status": "pending",
            "step_config": json.dumps({
                "query": "air quality Munich",
                "domain": "environmental",
                "top_k": 10,
                "use_uds3": True
            })
        },
        {
            "step_id": f"{plan_id}_step_002",
            "plan_id": plan_id,
            "step_index": 1,
            "step_name": "Search Regulations",
            "step_type": "regulation_search",
            "agent_name": "environmental",
            "agent_type": "EnvironmentalAgent",
            "status": "pending",
            "step_config": json.dumps({
                "regulation_type": "environmental",
                "jurisdiction": "Germany",
                "topic": "air_quality"
            }),
            "depends_on": [f"{plan_id}_step_001"]
        },
        {
            "step_id": f"{plan_id}_step_003",
            "plan_id": plan_id,
            "step_index": 2,
            "step_name": "Analyze Environmental Metrics",
            "step_type": "environmental_analysis",
            "agent_name": "environmental",
            "agent_type": "EnvironmentalAgent",
            "status": "pending",
            "step_config": json.dumps({
                "metrics": ["PM2.5", "PM10", "NO2", "O3"],
                "location": "Munich",
                "timeframe": "30_days"
            }),
            "depends_on": [f"{plan_id}_step_001"]
        },
        {
            "step_id": f"{plan_id}_step_004",
            "plan_id": plan_id,
            "step_index": 3,
            "step_name": "Assess Impact",
            "step_type": "impact_assessment",
            "agent_name": "environmental",
            "agent_type": "EnvironmentalAgent",
            "status": "pending",
            "step_config": json.dumps({
                "project_type": "urban_development",
                "location": "Munich",
                "scope": "air_quality"
            }),
            "depends_on": [f"{plan_id}_step_002", f"{plan_id}_step_003"]
        }
    ]
    
    return plan, steps


def main():
    """Test Environmental Agent with UDS3."""
    print("=" * 80)
    print("VERITAS Environmental Agent with UDS3 Test")
    print("=" * 80)
    
    # Initialize UDS3 for standalone testing
    logger.info("\n→ Initializing UDS3 PolyglotManager (Direct Integration)...")
    try:
        # Minimal Config - DatabaseManager lädt echte Credentials aus uds3/config.py
        backend_config = {
            "vector": {"enabled": True},      # ChromaDB - Embeddings/Semantic Search
            "graph": {"enabled": True},       # Neo4j - Knowledge Graph
            "relational": {"enabled": True},  # PostgreSQL - Structured Data
            "file": {"enabled": True}         # CouchDB - Original Files/Documents
        }
        
        uds3 = UDS3PolyglotManager(
            backend_config=backend_config,
            enable_rag=True
        )
        set_uds3_instance(uds3)
        logger.info("✅ UDS3 initialized successfully")
    except Exception as e:
        logger.error(f"❌ UDS3 initialization failed: {e}")
        logger.error("   Databases may not be available. Test will use mock data.")
        # Don't exit - let agents handle missing UDS3
    
    # Initialize storage
    storage = get_storage()
    logger.info(f"Storage backend: {storage.using_db and 'PostgreSQL' or 'JSON Fallback'}")
    
    # Create test plan
    logger.info("\n→ Creating environmental research plan...")
    plan, steps = create_environmental_research_plan()
    
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
    logger.info("\n→ Initializing Environmental Agent with UDS3...")
    agent = create_environmental_agent(agent_id="env_agent_001")
    logger.info(f"✅ Agent initialized: {agent.get_agent_type()}")
    logger.info(f"   Capabilities: {', '.join(agent.get_capabilities())}")
    logger.info(f"   UDS3 Integration: {'✅ Active' if hasattr(agent, 'uds3') else '❌ Missing'}")
    
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
        
        # Parse step config
        step_config = json.loads(step['step_config']) if isinstance(step['step_config'], str) else step['step_config']
        
        # Execute step
        try:
            result = agent.execute_step(
                {
                    "step_type": step['step_type'],
                    "step_config": step_config
                },
                {"plan_id": plan['plan_id']}
            )
            
            # Update step with result
            storage.update_step(step_id, {
                "status": "completed",
                "completed_at": "now",
                "result": json.dumps(result.get("data", {}))
            })
            
            logger.info(f"✅ Step completed successfully")
            logger.info(f"   Status: {result.get('status')}")
            logger.info(f"   Confidence: {result.get('confidence_score', 'N/A')}")
            logger.info(f"   Quality: {result.get('quality_score', 'N/A')}")
            logger.info(f"   Sources: {', '.join(result.get('sources', []))}")
            
            # Show data summary
            if result.get("data"):
                data = result["data"]
                if isinstance(data, dict):
                    keys = list(data.keys())[:5]
                    logger.info(f"   Data keys: {', '.join(keys)}")
        
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
    print("✅ Environmental Agent with UDS3 Test Complete!")
    print("=" * 80)
    
    print("\nNext Steps:")
    print("1. Create more specialized agents (Financial, Social, Legal)")
    print("2. Implement real UDS3 database connections")
    print("3. Add Phase 5 hybrid search with re-ranking")
    print("4. Build frontend UI for research plan execution")


if __name__ == "__main__":
    main()
