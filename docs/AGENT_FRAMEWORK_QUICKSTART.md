# VERITAS Agent Framework - Quick Start Guide

**Status:** ✅ Production Ready  
**Database:** PostgreSQL with JSON Fallback  
**Version:** 1.0  
**Last Updated:** 2025-10-22

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Creating Custom Agents](#creating-custom-agents)
5. [Research Plan Schema](#research-plan-schema)
6. [Execution Flow](#execution-flow)
7. [Database Schema](#database-schema)
8. [Monitoring & Quality Gates](#monitoring--quality-gates)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The VERITAS Agent Framework provides orchestrated, schema-driven research plan execution with:

- **Multi-Agent Orchestration:** Coordinate specialized agents for complex tasks
- **State Management:** Track execution progress with state machine
- **Quality Gates:** Enforce quality policies and validation
- **Retry Logic:** Configurable retry strategies with backoff
- **Database Persistence:** PostgreSQL with automatic JSON fallback
- **Dependency Resolution:** Handle step dependencies automatically
- **Monitoring:** Built-in performance tracking and metrics

---

## Architecture

```
Research Question
       ↓
Research Plan (JSON Schema)
       ↓
OrchestrationController
       ↓
    Steps (0, 1, 2, ...)
       ↓
BaseAgent.execute_step()
       ↓
Results → Database (PostgreSQL/JSON)
```

### Components

1. **BaseAgent** (`backend/agents/framework/base_agent.py`)
   - Abstract base class for all agents
   - Schema-based execution
   - Quality metrics and error handling

2. **OrchestrationController** (`backend/agents/framework/orchestration_controller.py`)
   - Plan execution engine
   - Pause/resume capabilities
   - Dynamic plan modification
   - Checkpoint system

3. **Storage Layer** (`backend/database/research_plan_storage.py`)
   - Unified storage interface
   - PostgreSQL primary backend
   - Automatic JSON fallback

4. **Supporting Components**
   - `state_machine.py`: Plan state management (pending/running/paused/completed/failed)
   - `dependency_resolver.py`: Step dependency graph
   - `retry_handler.py`: Retry strategies with exponential backoff
   - `quality_gate.py`: Quality policy enforcement
   - `agent_monitoring.py`: Performance metrics

---

## Quick Start

### Prerequisites

```powershell
# 1. PostgreSQL running (remote or local)
$env:POSTGRES_HOST = "192.168.178.94"  # or "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DATABASE = "veritas"

# 2. Database schema deployed
python backend\agents\framework\setup_database.py
```

### Run Test

```powershell
# Test with PostgreSQL
python tools\test_agent_framework.py

# Test with JSON fallback
$env:POSTGRES_PORT = "9999"  # unreachable port
python tools\test_agent_framework.py
```

### Expected Output

```
====================================================================
VERITAS Agent Framework Test
====================================================================
2025-10-22 16:38:46,664 - INFO - Storage backend: PostgreSQL
2025-10-22 16:38:46,722 - INFO - ✅ Plan created: test_research_plan_20251022_163846
2025-10-22 16:38:46,748 - INFO - ✅ Step 0: Query Environmental Data
2025-10-22 16:38:46,756 - INFO - ✅ Step 1: Analyze Air Quality Metrics
2025-10-22 16:38:46,765 - INFO - ✅ Step 2: Synthesize Findings
2025-10-22 16:38:46,766 - INFO - ✅ Agent initialized: test_data_retrieval

→ Executing plan steps...
2025-10-22 16:38:46,956 - INFO - Executing step: Query Environmental Data
2025-10-22 16:38:46,974 - INFO - ✅ Step completed successfully
2025-10-22 16:38:46,974 - INFO -    Confidence: 0.89
2025-10-22 16:38:46,974 - INFO -    Quality: 0.92

✅ Plan execution complete!
Status: completed
Progress: 100.00%
====================================================================
```

---

## Creating Custom Agents

### Step 1: Inherit from BaseAgent

```python
from backend.agents.framework.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    """Custom agent for specific domain."""
    
    def get_agent_type(self) -> str:
        """Return unique agent type identifier."""
        return "my_custom_agent"
    
    def get_capabilities(self) -> list:
        """Return list of capabilities."""
        return ["capability_1", "capability_2", "capability_3"]
    
    def execute_step(self, step: dict, context: dict) -> dict:
        """
        Execute a single step.
        
        Args:
            step: Step configuration with:
                - step_id: Unique step identifier
                - step_name: Human-readable name
                - step_type: Type of step
                - step_config: JSON configuration
                - depends_on: List of step_ids
            
            context: Execution context with:
                - plan_id: Research plan ID
                - previous_results: Results from dependencies
                - uds3_databases: Available databases
                - phase5_hybrid_search: Enable hybrid search
        
        Returns:
            Result dictionary with:
                - status: "success" or "error"
                - data: Result data (any JSON-serializable)
                - confidence_score: 0.0-1.0 (optional)
                - quality_score: 0.0-1.0 (optional)
                - error_message: Error details (if failed)
        """
        
        # Your domain-specific logic here
        try:
            # Example: Query UDS3 database
            results = self._query_database(step)
            
            # Example: Process results
            processed = self._process_results(results)
            
            return {
                "status": "success",
                "data": {
                    "results": processed,
                    "count": len(processed)
                },
                "confidence_score": 0.9,
                "quality_score": 0.85
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
```

### Step 2: Use the Agent

```python
from backend.database.research_plan_storage import get_storage

# Initialize storage
storage = get_storage()

# Initialize agent
agent = MyCustomAgent(
    agent_id="my_agent_001",
    config={
        "database_timeout": 30,
        "max_results": 100
    }
)

# Execute step
step = {
    "step_id": "step_001",
    "step_name": "Query Data",
    "step_type": "data_retrieval",
    "step_config": {"query": "air quality Munich"}
}

context = {"plan_id": "plan_001"}
result = agent.execute_step(step, context)

print(f"Status: {result['status']}")
print(f"Data: {result['data']}")
```

---

## Research Plan Schema

### Plan Structure

```python
plan = {
    "plan_id": "unique_plan_id",
    "research_question": "What is the air quality in Munich?",
    "status": "pending",  # pending/running/paused/completed/failed
    "total_steps": 3,
    
    # JSON document with full plan
    "plan_document": json.dumps({
        "schema_version": "1.0",
        "research_question": "What is the air quality in Munich?",
        "steps": [
            {
                "step_id": "step_001",
                "step_name": "Query Environmental Data",
                "step_type": "data_retrieval",
                "step_index": 0
            },
            # ... more steps
        ]
    }),
    
    # UDS3 Integration
    "uds3_databases": ["chromadb", "neo4j", "postgres"],
    "phase5_hybrid_search": True,
    
    # Security & Metadata
    "security_level": "internal",  # public/internal/confidential/secret
    "source_domains": ["environmental"],
    "created_by": "user_id",
}
```

### Step Structure

```python
step = {
    "step_id": "unique_step_id",
    "plan_id": "parent_plan_id",
    "step_index": 0,  # Execution order
    
    # Step details
    "step_name": "Query Environmental Data",
    "step_type": "data_retrieval",  # Custom type
    
    # Agent assignment
    "agent_name": "environmental_agent",
    "agent_type": "EnvironmentalAgent",
    
    # Execution state
    "status": "pending",  # pending/running/completed/failed/skipped
    
    # Dependencies
    "depends_on": ["step_000"],  # List of step_ids
    
    # Configuration
    "step_config": json.dumps({
        "databases": ["chromadb"],
        "max_results": 10,
        "filters": {"location": "Munich"}
    })
}
```

---

## Execution Flow

### Sequential Execution

```python
from backend.database.research_plan_storage import get_storage

storage = get_storage()
agent = MyCustomAgent()

# Create plan
plan = storage.create_plan({
    "plan_id": "plan_001",
    "research_question": "Test question",
    "status": "pending",
    "total_steps": 2,
    "plan_document": json.dumps({"steps": [...]})
})

# Create steps
step1 = storage.create_step({
    "step_id": "step_001",
    "plan_id": "plan_001",
    "step_index": 0,
    "step_name": "First Step",
    "agent_name": "my_agent",
    "status": "pending"
})

step2 = storage.create_step({
    "step_id": "step_002",
    "plan_id": "plan_001",
    "step_index": 1,
    "step_name": "Second Step",
    "agent_name": "my_agent",
    "status": "pending",
    "depends_on": ["step_001"]  # Wait for step_001
})

# Execute steps
storage.update_plan("plan_001", {"status": "running"})

for step in [step1, step2]:
    # Update status
    storage.update_step(step['step_id'], {"status": "running"})
    
    # Execute
    result = agent.execute_step(step, {"plan_id": "plan_001"})
    
    # Store result
    storage.update_step(step['step_id'], {
        "status": "completed",
        "result": json.dumps(result.get("data", {}))
    })

storage.update_plan("plan_001", {"status": "completed"})
```

### With OrchestrationController

```python
from backend.agents.framework.orchestration_controller import OrchestrationController

controller = OrchestrationController(storage=get_storage())

# Execute plan asynchronously
await controller.execute_plan_async("plan_001", plan)

# Pause/resume
await controller.pause_plan("plan_001")
await controller.resume_plan("plan_001")

# Dynamic modification
await controller.add_step("plan_001", new_step, insert_after="step_002")
```

---

## Database Schema

### Tables

#### 1. `research_plans`
Main research plans with metadata.

```sql
CREATE TABLE research_plans (
    plan_id TEXT PRIMARY KEY,
    research_question TEXT NOT NULL,
    plan_document JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_steps INTEGER DEFAULT 0,
    completed_steps INTEGER DEFAULT 0,
    progress_percentage FLOAT DEFAULT 0.0,
    uds3_databases TEXT[],
    phase5_hybrid_search BOOLEAN DEFAULT FALSE,
    security_level TEXT DEFAULT 'internal',
    source_domains TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT,
    assigned_to TEXT
);
```

#### 2. `research_plan_steps`
Individual execution steps.

```sql
CREATE TABLE research_plan_steps (
    step_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL REFERENCES research_plans(plan_id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    step_type TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    agent_type TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    depends_on TEXT[],
    step_config JSONB,
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_ms INTEGER
);
```

#### 3. `step_results`
Detailed step results with quality metrics.

```sql
CREATE TABLE step_results (
    result_id SERIAL PRIMARY KEY,
    plan_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    result_data JSONB NOT NULL,
    confidence_score FLOAT,
    quality_score FLOAT,
    uds3_sources TEXT[],
    hybrid_search_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 4. `agent_execution_log`
Performance logs and debugging info.

```sql
CREATE TABLE agent_execution_log (
    log_id SERIAL PRIMARY KEY,
    plan_id TEXT NOT NULL,
    step_id TEXT,
    agent_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data JSONB,
    execution_time_ms INTEGER,
    memory_usage_mb FLOAT,
    error_occurred BOOLEAN DEFAULT FALSE,
    error_details TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

#### 5. `agent_registry_metadata`
Agent capabilities and performance stats.

```sql
CREATE TABLE agent_registry_metadata (
    agent_id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    capabilities JSONB NOT NULL,
    version TEXT,
    performance_stats JSONB,
    last_executed TIMESTAMP,
    total_executions INTEGER DEFAULT 0,
    success_rate FLOAT,
    avg_execution_time_ms FLOAT
);
```

### Views

#### 1. `active_research_plans`
All non-completed plans.

```sql
CREATE VIEW active_research_plans AS
SELECT * FROM research_plans
WHERE status IN ('pending', 'running', 'paused');
```

#### 2. `step_execution_summary`
Step execution statistics per plan.

```sql
CREATE VIEW step_execution_summary AS
SELECT 
    rp.plan_id,
    rp.research_question,
    COUNT(rps.step_id) as total_steps,
    SUM(CASE WHEN rps.status = 'completed' THEN 1 ELSE 0 END) as completed_steps,
    AVG(rps.execution_time_ms) as avg_execution_time_ms
FROM research_plans rp
LEFT JOIN research_plan_steps rps ON rp.plan_id = rps.plan_id
GROUP BY rp.plan_id;
```

#### 3. `agent_performance_stats`
Agent performance metrics.

```sql
CREATE VIEW agent_performance_stats AS
SELECT 
    agent_type,
    COUNT(*) as total_executions,
    AVG(execution_time_ms) as avg_execution_time_ms,
    SUM(CASE WHEN error_occurred THEN 1 ELSE 0 END)::float / COUNT(*) as error_rate
FROM agent_execution_log
GROUP BY agent_type;
```

---

## Monitoring & Quality Gates

### Quality Policy Example

```python
from backend.agents.framework.quality_gate import QualityPolicy, QualityGate

policy = QualityPolicy(
    min_confidence_score=0.7,
    min_quality_score=0.6,
    require_sources=True,
    max_retries=3
)

gate = QualityGate(policy)

# Check result quality
result = agent.execute_step(step, context)
decision = gate.evaluate(result)

if decision.passed:
    print("Quality check passed!")
else:
    print(f"Quality check failed: {decision.reason}")
```

### Monitoring Example

```python
from backend.agents.framework.agent_monitoring import AgentMonitor

monitor = AgentMonitor(agent_id="my_agent_001")

# Record metrics
monitor.record_execution(
    step_id="step_001",
    execution_time_ms=1234,
    memory_usage_mb=56.7,
    success=True
)

# Get statistics
stats = monitor.get_stats()
print(f"Total executions: {stats['total_executions']}")
print(f"Success rate: {stats['success_rate']}")
print(f"Avg time: {stats['avg_execution_time_ms']}ms")
```

---

## Troubleshooting

### Database Connection Issues

**Problem:** `PostgreSQL unavailable, using JSON fallback`

**Solutions:**
1. Check PostgreSQL is running:
   ```powershell
   Test-NetConnection -ComputerName 192.168.178.94 -Port 5432
   ```

2. Verify credentials:
   ```powershell
   $env:POSTGRES_HOST = "192.168.178.94"
   $env:POSTGRES_PORT = "5432"
   $env:POSTGRES_DATABASE = "veritas"
   ```

3. Check database exists:
   ```sql
   psql -h 192.168.178.94 -U postgres -l
   ```

4. Run setup if missing:
   ```powershell
   python backend\agents\framework\setup_database.py
   ```

### JSON Fallback Location

When PostgreSQL is unavailable, data is stored in:
```
data/fallback_db/
├── research_plans.json
├── research_plan_steps.json
├── step_results.json
└── agent_execution_log.json
```

### Agent Execution Errors

**Problem:** Step fails with error

**Debug Steps:**
1. Check logs:
   ```python
   steps = storage.list_steps(plan_id)
   for step in steps:
       if step['status'] == 'failed':
           print(f"Error: {step['error_message']}")
   ```

2. Check agent logs:
   ```sql
   SELECT * FROM agent_execution_log
   WHERE error_occurred = TRUE
   ORDER BY timestamp DESC;
   ```

3. Enable debug logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Performance Issues

**Problem:** Slow execution

**Optimization:**
1. Use connection pooling (already enabled)
2. Batch database operations
3. Enable indexes:
   ```sql
   CREATE INDEX idx_steps_plan_id ON research_plan_steps(plan_id);
   CREATE INDEX idx_results_plan_id ON step_results(plan_id);
   ```

4. Monitor execution time:
   ```sql
   SELECT step_name, AVG(execution_time_ms)
   FROM research_plan_steps
   WHERE status = 'completed'
   GROUP BY step_name
   ORDER BY AVG(execution_time_ms) DESC;
   ```

---

## Next Steps

1. **Create Specialized Agents:**
   - EnvironmentalAgent (regulation search)
   - FinancialAgent (company data)
   - SocialAgent (social media analysis)

2. **Integrate with UDS3:**
   - ChromaDB vector search
   - Neo4j knowledge graph
   - CouchDB document store

3. **Add Phase 5 Hybrid Search:**
   - Combine vector + keyword search
   - Re-ranking algorithms

4. **Build Frontend UI:**
   - Research plan builder
   - Live execution monitoring
   - Result visualization

5. **Production Deployment:**
   - Configure pgBouncer
   - Set up Azure KeyVault
   - Enable PKI certificates
   - Add Prometheus monitoring

---

## References

- **Architecture:** `docs/SYSTEM_ARCHITECTURE_ANALYSIS.md`
- **Database:** `docs/DB_CONNECTION_POOLING.md`
- **Security:** `docs/AUTHENTICATION_GUIDE.md`
- **API:** `backend/api/agent_router.py`
- **Tests:** `tools/test_agent_framework.py`

---

**Version:** 1.0  
**Status:** ✅ Production Ready  
**Last Test:** 2025-10-22 (All tests passed)
