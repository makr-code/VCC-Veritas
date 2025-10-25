"""
Test Research Plan Storage with DB and JSON fallback
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault("ENABLE_SECURE_SECRETS", "true")

from backend.database.research_plan_storage import get_storage
import json

print("=" * 80)
print("VERITAS Research Plan Storage Test")
print("=" * 80)

storage = get_storage()

print(f"\n✅ Storage initialized")
print(f"Backend: {storage.using_db and 'PostgreSQL' or 'JSON Fallback'}")

# Get stats
stats = storage.get_stats()
print(f"\nCurrent stats:")
for key, val in stats.items():
    print(f"  {key}: {val}")

# Create a test plan
test_plan = {
    "plan_id": "test_plan_001",
    "research_question": "What is the air quality in Munich?",
    "status": "pending",
    "plan_document": json.dumps({"steps": []}),
    "total_steps": 0,
    "uds3_databases": ["chromadb", "neo4j"],
    "phase5_hybrid_search": True,
    "security_level": "internal",
    "source_domains": ["environmental"]
}

print(f"\n→ Creating test plan: {test_plan['plan_id']}")
created = storage.create_plan(test_plan)
print(f"✅ Plan created: {created['plan_id']}")

# Retrieve it
print(f"\n→ Retrieving plan...")
retrieved = storage.get_plan("test_plan_001")
if retrieved:
    print(f"✅ Plan retrieved:")
    print(f"  Question: {retrieved['research_question']}")
    print(f"  Status: {retrieved['status']}")
    print(f"  Databases: {retrieved.get('uds3_databases', [])}")
else:
    print("❌ Plan not found")

# Create a step
test_step = {
    "step_id": "step_001",
    "plan_id": "test_plan_001",
    "step_index": 0,
    "step_name": "Query Environmental Data",
    "step_type": "data_retrieval",
    "agent_name": "environmental",
    "agent_type": "DataRetrievalAgent",
    "status": "pending",
    "step_config": json.dumps({"max_results": 10})
}

print(f"\n→ Creating test step: {test_step['step_id']}")
created_step = storage.create_step(test_step)
print(f"✅ Step created: {created_step['step_id']}")

# List steps
print(f"\n→ Listing steps for plan...")
steps = storage.list_steps("test_plan_001")
print(f"✅ Found {len(steps)} step(s):")
for step in steps:
    print(f"  - {step['step_name']} ({step['status']})")

# Update plan status
print(f"\n→ Updating plan status to 'running'...")
storage.update_plan("test_plan_001", {"status": "running"})
updated = storage.get_plan("test_plan_001")
print(f"✅ Plan status: {updated['status']}")

# Final stats
print(f"\n→ Final stats:")
final_stats = storage.get_stats()
for key, val in final_stats.items():
    print(f"  {key}: {val}")

print(f"\n" + "=" * 80)
print("✅ Storage test complete!")
print("=" * 80)
