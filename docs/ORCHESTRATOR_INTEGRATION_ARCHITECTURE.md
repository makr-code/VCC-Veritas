# ORCHESTRATOR INTEGRATION ARCHITECTURE

**Projekt:** VERITAS v5.0 - Dependency-Driven Process Tree ↔ Agent Orchestrator Integration  
**Erstellt:** 12. Oktober 2025, 20:10 Uhr  
**Status:** 🟡 Design Phase - Integration Strategy

---

## 🎯 Executive Summary

**Problem:** Wir haben **zwei parallele Orchestrierungs-Systeme**:

1. **Dependency-Driven Process Tree** (NEU - aus v5.0 Design)
   - Flat steps mit explicit dependencies
   - Parallel execution groups
   - User query als root
   - DependencyResolver (395 LOC) ✅ EXISTS

2. **Agent Orchestrator** (EXISTING - Production Code)
   - AgentOrchestrator (1,137 LOC)
   - OrchestrationController (819 LOC)
   - Pipeline-basierte Agent-Verwaltung
   - In-Memory Task Management

**Lösung:** **Unified Orchestration Layer** - Die beiden Systeme verbinden

---

## 🏗️ Current Architecture (Before Integration)

### System 1: Dependency-Driven Process Tree (v5.0 Design)

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPENDENCY-DRIVEN SYSTEM                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User Query → ProcessBuilder → ProcessTree                  │
│                                                              │
│  {                                                           │
│    root: {type: "user_query", content: "..."},             │
│    steps: [                                                 │
│      {step_id: "nlp", depends_on: []},                     │
│      {step_id: "rag_semantic", depends_on: ["nlp"],        │
│       parallel_group: "rag"},                              │
│      {step_id: "rag_graph", depends_on: ["nlp"],           │
│       parallel_group: "rag"},                              │
│      {step_id: "hypothesis", depends_on: ["rag_*"]},       │
│      {step_id: "template", depends_on: ["hypothesis"]},    │
│      {step_id: "llm_answer", depends_on: ["template"]}     │
│    ]                                                        │
│  }                                                           │
│                                                              │
│  ProcessExecutor + DependencyResolver ✅                     │
│  → Topological Sort                                         │
│  → Parallel Execution Groups                               │
│  → Result Aggregation                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Generic process execution (not agent-specific)
- Dependency-based scheduling
- Parallel group support
- Result chaining

**Status:** ✅ DependencyResolver exists, ProcessExecutor to be created

---

### System 2: Agent Orchestrator (Existing Production)

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT ORCHESTRATOR SYSTEM                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User Query → AgentOrchestrator → QueryPipeline             │
│                                                              │
│  AgentPipelineTask:                                         │
│  {                                                           │
│    task_id: "task_env_001",                                │
│    task_type: "domain_processing",                         │
│    agent_type: "environmental",                            │
│    capability: "domain_specific_processing",               │
│    priority: 0.85,                                         │
│    status: "pending",                                      │
│    depends_on: ["legal_framework", "geo_context"]          │
│  }                                                           │
│                                                              │
│  OrchestrationController:                                   │
│  - Pause/Resume                                             │
│  - Manual Intervention                                      │
│  - Dynamic Plan Modification                                │
│  - Checkpoint System                                        │
│  - Step Skipping & Rollback                                │
│                                                              │
│  AgentCoordinator:                                          │
│  - Agent Discovery & Dispatch                               │
│  - Message-based Communication                              │
│  - Agent Lifecycle Management                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Agent-specific orchestration
- Pipeline-based task management
- Schema-driven agent selection
- Advanced intervention capabilities
- Checkpoint/recovery system

**Status:** ✅ Production-ready (1,137 + 819 LOC)

---

## 🔄 Integration Strategy: Unified Orchestration Layer

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER QUERY                                    │
│                  "Wie ist das Wetter in Berlin?"                      │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    UNIFIED ORCHESTRATION LAYER (NEW!)                 │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ UnifiedOrchestrator (NEW - ~400 LOC)                         │   │
│  │                                                               │   │
│  │  Responsibilities:                                            │   │
│  │  1. Query Analysis → ProcessTree + AgentPipeline             │   │
│  │  2. Dual-Track Execution:                                    │   │
│  │     - Generic Steps (NLP, RAG) → ProcessExecutor             │   │
│  │     - Agent Tasks (Domain, Quality) → AgentOrchestrator      │   │
│  │  3. Result Synchronization & Aggregation                     │   │
│  │  4. Unified Progress Tracking                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────┐         ┌──────────────────────┐          │
│  │  ProcessExecutor     │         │  AgentOrchestrator   │          │
│  │  (Generic Steps)     │         │  (Agent Tasks)       │          │
│  │                      │         │                      │          │
│  │  - NLP Analysis      │         │  - Domain Agents     │          │
│  │  - RAG Retrieval     │         │  - Database Agent    │          │
│  │  - Hypothesis Gen    │         │  - Quality Assessor  │          │
│  │  - Template Build    │         │  - Authority Mapping │          │
│  │  - LLM Response      │         │                      │          │
│  │                      │         │                      │          │
│  │  Uses:               │         │  Uses:               │          │
│  │  ✅ DependencyResolv │         │  ✅ OrchestrationCtrl│          │
│  │  ✅ StreamingService │         │  ✅ AgentCoordinator │          │
│  └──────────────────────┘         └──────────────────────┘          │
│           │                                     │                     │
│           └─────────────┬───────────────────────┘                     │
│                         ▼                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │         ResultAggregator (NEW - ~200 LOC)                    │   │
│  │  - Merge ProcessExecutor Results + Agent Results             │   │
│  │  - Dependency-aware aggregation                              │   │
│  │  - Conflict resolution (same data from multiple sources)     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    NDJSON STREAMING RESPONSE                          │
│  {"type": "metadata", "stage": "nlp", "progress": 10}               │
│  {"type": "metadata", "stage": "agent_environmental", "progress": 30}│
│  {"type": "text_chunk", "content": "Das Wetter in Berlin..."}       │
│  {"type": "widget", "widget_type": "table", "data": {...}}          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Integration Components

### 1. UnifiedOrchestrator (NEW - ~400 LOC)

**Location:** `backend/services/unified_orchestrator.py`

**Responsibilities:**

1. **Query Analysis & Planning:**
   ```python
   def plan_execution(self, query: str) -> UnifiedExecutionPlan:
       """
       Analyze query → Create dual-track plan
       
       Returns:
       {
           "generic_steps": [  # For ProcessExecutor
               {step_id: "nlp", executor: "process", ...},
               {step_id: "rag_semantic", executor: "process", ...}
           ],
           "agent_tasks": [    # For AgentOrchestrator
               {task_id: "env_agent", executor: "agent", agent_type: "environmental", ...},
               {task_id: "db_agent", executor: "agent", agent_type: "database", ...}
           ],
           "dependencies": {
               "hypothesis": ["nlp", "rag_semantic", "env_agent"],  # Mixed deps!
               "template": ["hypothesis", "db_agent"]
           }
       }
       ```

2. **Dual-Track Execution:**
   ```python
   async def execute_unified_plan(self, plan: UnifiedExecutionPlan) -> Dict[str, Any]:
       """
       Execute plan across both systems in parallel
       """
       # Create ProcessTree for generic steps
       process_tree = self._create_process_tree(plan.generic_steps)
       
       # Create AgentPipeline for agent tasks
       agent_pipeline = self._create_agent_pipeline(plan.agent_tasks)
       
       # Execute both in parallel with dependency coordination
       process_future = asyncio.create_task(
           self.process_executor.execute_process(process_tree)
       )
       agent_future = asyncio.create_task(
           self.agent_orchestrator.execute_pipeline(agent_pipeline)
       )
       
       # Coordinate execution (wait for dependencies across systems)
       results = await self._coordinate_execution(process_future, agent_future, plan.dependencies)
       
       return results
   ```

3. **Result Synchronization:**
   ```python
   async def _coordinate_execution(
       self, 
       process_future, 
       agent_future, 
       cross_dependencies: Dict[str, List[str]]
   ) -> Dict[str, Any]:
       """
       Coordinate execution when steps depend on results from other system
       
       Example:
       - "hypothesis" step needs: nlp (process) + rag (process) + env_agent (agent)
       - Wait for all 3 to complete before starting hypothesis
       """
       pass
   ```

---

### 2. ResultAggregator (NEW - ~200 LOC)

**Location:** `backend/services/result_aggregator.py`

**Features:**

```python
class ResultAggregator:
    """
    Aggregate results from ProcessExecutor and AgentOrchestrator
    """
    
    def aggregate_results(
        self, 
        process_results: Dict[str, Any],
        agent_results: Dict[str, Any]
    ) -> AggregatedResult:
        """
        Merge results from both systems
        
        Handle:
        - Duplicate data (same info from process RAG + database agent)
        - Confidence scores (which source is more reliable?)
        - Schema mapping (process result → agent result format)
        """
        pass
    
    def resolve_conflicts(
        self, 
        sources: List[ResultSource]
    ) -> ResolvedResult:
        """
        Resolve conflicts when multiple sources provide same data
        
        Strategy:
        - Highest confidence wins
        - Agent results preferred over generic process (domain expertise)
        - Database agent > RAG semantic search (exact data)
        """
        pass
```

---

### 3. ExecutionPlanBuilder (NEW - ~250 LOC)

**Location:** `backend/services/execution_plan_builder.py`

**Features:**

```python
class ExecutionPlanBuilder:
    """
    Analyze user query → Decide which steps go where
    """
    
    def build_plan(self, query: str, hypothesis: Hypothesis) -> UnifiedExecutionPlan:
        """
        Decision Logic:
        
        Generic Steps (ProcessExecutor):
        - NLP Analysis (always)
        - RAG Semantic Search (always)
        - RAG Graph Search (always)
        - Hypothesis Generation (always)
        - Template Construction (always)
        - LLM Response Generation (always)
        
        Agent Tasks (AgentOrchestrator):
        - Domain-Specific Processing (if hypothesis.domain in [environmental, financial, ...])
        - Database Queries (if hypothesis.requires_exact_data)
        - Quality Assessment (always for important queries)
        - Authority Mapping (if hypothesis.requires_legal_references)
        - Wikipedia Agent (if hypothesis.requires_general_knowledge)
        """
        
        plan = UnifiedExecutionPlan()
        
        # Always add generic pipeline
        plan.add_generic_steps([
            {"step_id": "nlp", "type": "nlp_analysis"},
            {"step_id": "rag_semantic", "type": "rag_retrieval", "depends_on": ["nlp"]},
            {"step_id": "hypothesis", "type": "hypothesis_generation", "depends_on": ["rag_*"]}
        ])
        
        # Conditionally add agent tasks
        if hypothesis.domain == QueryDomain.ENVIRONMENTAL:
            plan.add_agent_task({
                "task_id": "env_agent",
                "agent_type": "environmental",
                "depends_on": ["nlp"],  # Can run in parallel with RAG!
                "parallel_group": "domain_processing"
            })
        
        if hypothesis.requires_exact_data:
            plan.add_agent_task({
                "task_id": "db_agent",
                "agent_type": "database",
                "depends_on": ["nlp"],
                "parallel_group": "domain_processing"
            })
        
        return plan
```

---

## 📊 Execution Flow Example

### Example Query: "Wie ist die Luftqualität in Berlin heute?"

**Step 1: Query Analysis**

```python
# UnifiedOrchestrator.plan_execution()

query = "Wie ist die Luftqualität in Berlin heute?"

# NLP Analysis
entities = ["Berlin", "heute"]
intent = "environmental_data_query"
question_type = "fact_retrieval"

# Hypothesis Generation (LLM Call 1)
hypothesis = {
    "question_type": "fact_retrieval",
    "domain": QueryDomain.ENVIRONMENTAL,
    "requires_exact_data": True,
    "required_data": ["air_quality_index", "pollutants", "measurement_time"],
    "confidence": 0.92
}
```

---

**Step 2: Execution Plan Creation**

```python
# ExecutionPlanBuilder.build_plan(query, hypothesis)

plan = UnifiedExecutionPlan(
    generic_steps=[
        {"step_id": "nlp", "type": "nlp_analysis", "depends_on": []},
        {"step_id": "rag_semantic", "type": "rag_retrieval", "depends_on": ["nlp"], "parallel_group": "rag"},
        {"step_id": "rag_graph", "type": "rag_retrieval", "depends_on": ["nlp"], "parallel_group": "rag"},
        {"step_id": "hypothesis", "type": "hypothesis_generation", "depends_on": ["rag_semantic", "rag_graph"]},
        {"step_id": "template", "type": "template_construction", "depends_on": ["hypothesis", "env_agent", "db_agent"]},  # ← Mixed deps!
        {"step_id": "llm_answer", "type": "llm_generation", "depends_on": ["template"]}
    ],
    agent_tasks=[
        {"task_id": "env_agent", "agent_type": "environmental", "depends_on": ["nlp"], "parallel_group": "domain"},
        {"task_id": "db_agent", "agent_type": "database", "depends_on": ["nlp"], "parallel_group": "domain"},
        {"task_id": "quality_agent", "agent_type": "quality_assessor", "depends_on": ["llm_answer"]}
    ]
)
```

---

**Step 3: Dependency Resolution (Cross-System)**

```python
# UnifiedOrchestrator._coordinate_execution()

# Wave 1: Independent steps
execute_parallel([
    "nlp"  # Generic step
])

# Wave 2: Depends on nlp (cross-system parallelization!)
execute_parallel([
    "rag_semantic",     # Generic step (ProcessExecutor)
    "rag_graph",        # Generic step (ProcessExecutor)
    "env_agent",        # Agent task (AgentOrchestrator)
    "db_agent"          # Agent task (AgentOrchestrator)
])

# Wave 3: Depends on rag_* (generic only)
execute_parallel([
    "hypothesis"        # Generic step
])

# Wave 4: Depends on hypothesis + agents (CROSS-SYSTEM!)
# Wait for: hypothesis (process) + env_agent (agent) + db_agent (agent)
execute_parallel([
    "template"          # Generic step
])

# Wave 5: Depends on template
execute_parallel([
    "llm_answer"        # Generic step
])

# Wave 6: Depends on llm_answer
execute_parallel([
    "quality_agent"     # Agent task (final quality check)
])
```

---

**Step 4: Result Aggregation**

```python
# ResultAggregator.aggregate_results()

process_results = {
    "nlp": {
        "entities": ["Berlin", "heute"],
        "intent": "environmental_data_query"
    },
    "rag_semantic": {
        "documents": [
            {"text": "Luftqualität Berlin...", "score": 0.87}
        ]
    },
    "hypothesis": {
        "question_type": "fact_retrieval",
        "confidence": 0.92
    },
    "template": {
        "template_type": "fact_retrieval",
        "sections": ["summary", "details", "source"]
    },
    "llm_answer": {
        "text": "Die Luftqualität in Berlin..."
    }
}

agent_results = {
    "env_agent": {
        "air_quality_index": 45,  # From Environmental API
        "pollutants": {"NO2": 32, "PM10": 18},
        "source": "Umweltbundesamt",
        "confidence": 0.95
    },
    "db_agent": {
        "air_quality_index": 45,  # From Database (same value!)
        "measurement_time": "2025-10-12T19:00:00Z",
        "source": "Internal DB",
        "confidence": 1.0  # Exact data
    },
    "quality_agent": {
        "quality_score": 0.88,
        "completeness": 0.95,
        "coherence": 0.92
    }
}

# Aggregate
aggregated = {
    "nlp": process_results["nlp"],
    "rag": process_results["rag_semantic"],
    "hypothesis": process_results["hypothesis"],
    "template": process_results["template"],
    "environmental_data": {
        "air_quality_index": 45,  # Conflict resolved: db_agent wins (confidence 1.0 > 0.95)
        "pollutants": agent_results["env_agent"]["pollutants"],  # Only env_agent has this
        "measurement_time": agent_results["db_agent"]["measurement_time"],  # Only db_agent has this
        "sources": ["Umweltbundesamt", "Internal DB"]  # Merged
    },
    "answer": process_results["llm_answer"],
    "quality": agent_results["quality_agent"]
}
```

---

## 🔄 Integration Patterns

### Pattern 1: Sequential Dependency (Generic → Agent)

```python
# Generic step produces input for agent task

plan.add_generic_step({
    "step_id": "nlp",
    "type": "nlp_analysis"
})

plan.add_agent_task({
    "task_id": "env_agent",
    "agent_type": "environmental",
    "depends_on": ["nlp"],  # Agent uses NLP results
    "input_mapping": {
        "entities": "nlp.entities",
        "intent": "nlp.intent"
    }
})
```

---

### Pattern 2: Parallel Execution (Both Systems)

```python
# Generic steps and agent tasks run in parallel

plan.add_generic_step({
    "step_id": "rag_semantic",
    "depends_on": ["nlp"],
    "parallel_group": "retrieval"
})

plan.add_agent_task({
    "task_id": "db_agent",
    "depends_on": ["nlp"],
    "parallel_group": "retrieval"  # Same group = can run in parallel
})

# Both execute simultaneously after nlp completes
```

---

### Pattern 3: Multi-Source Aggregation (Agent → Generic)

```python
# Generic step waits for multiple agent results

plan.add_agent_task({
    "task_id": "env_agent",
    "agent_type": "environmental",
    "depends_on": ["nlp"]
})

plan.add_agent_task({
    "task_id": "db_agent",
    "agent_type": "database",
    "depends_on": ["nlp"]
})

plan.add_generic_step({
    "step_id": "template",
    "type": "template_construction",
    "depends_on": ["hypothesis", "env_agent", "db_agent"],  # Waits for agents!
    "aggregation_strategy": "merge_with_conflict_resolution"
})
```

---

## 🎯 Implementation Phases

### Phase 1: Core Integration (3-4 Tage)

**Create:**
- [ ] `backend/services/unified_orchestrator.py` (~400 LOC)
- [ ] `backend/services/result_aggregator.py` (~200 LOC)
- [ ] `backend/services/execution_plan_builder.py` (~250 LOC)
- [ ] `backend/models/unified_execution_plan.py` (~150 LOC)

**Modify:**
- [ ] Extend `ProcessExecutor` to accept external dependencies (~50 LOC)
- [ ] Extend `AgentOrchestrator` to expose task completion events (~50 LOC)

**Tests:**
- [ ] `tests/test_unified_orchestrator.py` (~200 LOC)
- [ ] `tests/test_cross_system_dependencies.py` (~150 LOC)

**Total:** ~1,450 LOC

---

### Phase 2: Advanced Features (2-3 Tage)

**Create:**
- [ ] Cross-system checkpoint/resume (~150 LOC)
- [ ] Unified progress tracking (~100 LOC)
- [ ] Conflict resolution strategies (~200 LOC)
- [ ] Dynamic plan modification (~150 LOC)

**Total:** ~600 LOC

---

### Phase 3: Integration Testing (2-3 Tage)

**Create:**
- [ ] End-to-end integration tests (~300 LOC)
- [ ] Load tests (concurrent queries with mixed execution) (~200 LOC)
- [ ] Failure recovery tests (~150 LOC)

**Documentation:**
- [ ] Integration guide (~400 lines)
- [ ] Migration guide (existing code → unified) (~300 lines)

**Total:** ~1,350 LOC

---

## 📋 TODO List (Integration)

### Phase 1: Core Integration (3-4 Tage)

#### Backend - Unified Orchestration Layer

- [ ] **1.1 UnifiedOrchestrator** (~400 LOC, 8-10h)
  - **File:** `backend/services/unified_orchestrator.py`
  - **Dependencies:** ProcessExecutor, AgentOrchestrator
  - **Features:**
    - Query analysis
    - Dual-track planning
    - Cross-system dependency coordination
    - Result synchronization
  - **Tests:** `tests/test_unified_orchestrator.py`

- [ ] **1.2 ResultAggregator** (~200 LOC, 4-6h)
  - **File:** `backend/services/result_aggregator.py`
  - **Features:**
    - Result merging (process + agent)
    - Conflict resolution (confidence-based)
    - Schema mapping
    - Source tracking
  - **Tests:** `tests/test_result_aggregator.py`

- [ ] **1.3 ExecutionPlanBuilder** (~250 LOC, 5-7h)
  - **File:** `backend/services/execution_plan_builder.py`
  - **Features:**
    - Hypothesis-based plan creation
    - Step/task classification (generic vs. agent)
    - Dependency inference
    - Parallel group detection
  - **Tests:** `tests/test_execution_plan_builder.py`

- [ ] **1.4 Data Models** (~150 LOC, 2-3h)
  - **File:** `backend/models/unified_execution_plan.py`
  - **Features:**
    - `UnifiedExecutionPlan` dataclass
    - `GenericStep` class
    - `AgentTask` class (extends existing)
    - `AggregatedResult` class

- [ ] **1.5 Extend Existing Components** (~100 LOC, 2-3h)
  - **Modify:** `backend/services/process_executor.py`
    - Add external dependency support (wait for agent results)
    - Add event emission (step completed)
  - **Modify:** `backend/agents/veritas_api_agent_orchestrator.py`
    - Add task completion events
    - Add result export interface

**Phase 1 Total:** ~1,100 LOC, 21-29 Stunden (3-4 Tage)

---

### Phase 2: Advanced Features (2-3 Tage)

- [ ] **2.1 Cross-System Checkpoint** (~150 LOC, 3-4h)
  - Save state across both systems
  - Resume from checkpoint

- [ ] **2.2 Unified Progress Tracking** (~100 LOC, 2-3h)
  - Single progress metric (process + agent)
  - NDJSON streaming integration

- [ ] **2.3 Conflict Resolution** (~200 LOC, 4-5h)
  - Confidence-based resolution
  - Domain expert priority
  - User override support

- [ ] **2.4 Dynamic Plan Modification** (~150 LOC, 3-4h)
  - Add/remove steps at runtime
  - Recompute dependencies

**Phase 2 Total:** ~600 LOC, 12-16 Stunden (2-3 Tage)

---

### Phase 3: Integration Testing (2-3 Tage)

- [ ] **3.1 End-to-End Tests** (~300 LOC, 6-8h)
  - Simple query (only generic steps)
  - Complex query (mixed generic + agent)
  - Agent-heavy query

- [ ] **3.2 Load Tests** (~200 LOC, 4-5h)
  - 100 concurrent queries
  - Mixed execution patterns
  - Resource usage monitoring

- [ ] **3.3 Failure Recovery** (~150 LOC, 3-4h)
  - Agent task fails → continue with generic steps
  - Generic step fails → abort early
  - Checkpoint restore

- [ ] **3.4 Documentation** (~700 lines, 6-8h)
  - Integration guide
  - Migration guide
  - API reference

**Phase 3 Total:** ~1,350 LOC, 19-25 Stunden (2-3 Tage)

---

## 📊 Timeline & Effort

### Total Integration Effort

| Phase | LOC | Stunden | Tage | Komponenten |
|-------|-----|---------|------|-------------|
| **Phase 1:** Core Integration | 1,100 | 21-29 | 3-4 | UnifiedOrchestrator, ResultAggregator, PlanBuilder |
| **Phase 2:** Advanced Features | 600 | 12-16 | 2-3 | Checkpoint, Progress, Conflict Resolution |
| **Phase 3:** Testing & Docs | 1,350 | 19-25 | 2-3 | E2E/Load/Failure Tests, Docs |
| **TOTAL** | **3,050 LOC** | **52-70h** | **7-10 Tage** | **12 Komponenten** |

### Combined Timeline (v5.0 + Integration)

| Project | LOC | Tage |
|---------|-----|------|
| **v5.0 Structured Response** (Phases 1-7) | 7,450 | 18-25 |
| **Orchestrator Integration** (Phases 1-3) | 3,050 | 7-10 |
| **COMBINED TOTAL** | **10,500 LOC** | **25-35 Tage** |

**With Parallelization (some overlap):** ~20-28 Tage

---

## 🎯 Quick Start (Integration)

### Step 1: Review Existing Systems (2h)

```bash
# Understand DependencyResolver
cat backend/agents/framework/dependency_resolver.py

# Understand AgentOrchestrator
cat backend/agents/veritas_api_agent_orchestrator.py

# Understand OrchestrationController
cat backend/agents/framework/orchestration_controller.py
```

---

### Step 2: Create UnifiedOrchestrator Skeleton (4h)

```python
# backend/services/unified_orchestrator.py

from typing import Dict, Any, List
from backend.services.process_executor import ProcessExecutor
from backend.agents.veritas_api_agent_orchestrator import AgentOrchestrator
from backend.services.execution_plan_builder import ExecutionPlanBuilder
from backend.services.result_aggregator import ResultAggregator

class UnifiedOrchestrator:
    """
    Unified orchestration layer for generic steps and agent tasks
    """
    
    def __init__(self):
        self.process_executor = ProcessExecutor()
        self.agent_orchestrator = AgentOrchestrator()
        self.plan_builder = ExecutionPlanBuilder()
        self.result_aggregator = ResultAggregator()
    
    async def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Main entry point: Execute query across both systems
        """
        # 1. Build unified plan
        plan = self.plan_builder.build_plan(query)
        
        # 2. Execute dual-track
        results = await self._execute_dual_track(plan)
        
        # 3. Aggregate results
        aggregated = self.result_aggregator.aggregate_results(results)
        
        return aggregated
    
    async def _execute_dual_track(self, plan):
        """Execute process steps and agent tasks with dependency coordination"""
        pass
```

---

### Step 3: Test Integration (2h)

```python
# tests/test_unified_orchestrator.py

import pytest
from backend.services.unified_orchestrator import UnifiedOrchestrator

@pytest.mark.asyncio
async def test_simple_query_generic_only():
    """Test query that only uses generic steps (no agents)"""
    orchestrator = UnifiedOrchestrator()
    
    query = "What is 2+2?"
    result = await orchestrator.execute_query(query)
    
    assert "nlp" in result
    assert "llm_answer" in result
    # No agent results expected

@pytest.mark.asyncio
async def test_complex_query_mixed_execution():
    """Test query that uses both generic steps and agents"""
    orchestrator = UnifiedOrchestrator()
    
    query = "Wie ist die Luftqualität in Berlin?"
    result = await orchestrator.execute_query(query)
    
    # Should have generic results
    assert "nlp" in result
    assert "rag_semantic" in result
    
    # Should have agent results
    assert "env_agent" in result
    assert "db_agent" in result
    
    # Should be aggregated
    assert "environmental_data" in result
    assert result["environmental_data"]["air_quality_index"] is not None
```

---

## 🚨 Migration Path (Existing Code)

### Current Code (Before Integration)

```python
# Current: Direct agent orchestrator usage
orchestrator = AgentOrchestrator()
pipeline = orchestrator.create_pipeline(query)
results = orchestrator.execute_pipeline(pipeline)
```

### After Integration (Unified)

```python
# After: Unified orchestrator (backward compatible!)
unified = UnifiedOrchestrator()
results = await unified.execute_query(query)

# Internally decides: generic steps vs. agent tasks
# No code changes needed for simple agent-only queries!
```

**Backward Compatibility:** AgentOrchestrator still works standalone for agent-only workflows.

---

## 📚 Documentation Updates Needed

### New Documentation (3 files)

1. **ORCHESTRATOR_INTEGRATION_ARCHITECTURE.md** (This file)
2. **UNIFIED_ORCHESTRATION_USER_GUIDE.md** (~500 lines)
   - How to use UnifiedOrchestrator
   - When to use generic vs. agent
   - Example queries
3. **MIGRATION_GUIDE_ORCHESTRATOR.md** (~300 lines)
   - Migrating from AgentOrchestrator-only
   - Code examples (before/after)

### Updated Documentation (2 files)

1. **IMPLEMENTATION_GAP_ANALYSIS_TODO.md**
   - Add Orchestrator Integration section
   - Update Phase 8: Integration (new phase)
2. **VISUAL_IMPLEMENTATION_ROADMAP.md**
   - Add integration flow diagrams
   - Update timeline (+ 7-10 Tage)

---

## ✅ Success Criteria

### Integration Success

- [ ] UnifiedOrchestrator executes generic-only queries
- [ ] UnifiedOrchestrator executes agent-only queries
- [ ] UnifiedOrchestrator executes mixed queries (generic + agent)
- [ ] Cross-system dependencies work (agent result → generic step)
- [ ] Result aggregation handles conflicts correctly
- [ ] Progress tracking shows both systems
- [ ] Checkpoint/resume works across systems
- [ ] Load test passing (100 concurrent queries)
- [ ] Backward compatibility maintained (AgentOrchestrator still works)

---

## 🎯 Next Steps

1. **Read This Document** (30 min)
2. **Review Existing Systems** (2h)
   - DependencyResolver
   - AgentOrchestrator
   - OrchestrationController
3. **Start Phase 1** (3-4 Tage)
   - Create UnifiedOrchestrator
   - Create ResultAggregator
   - Create ExecutionPlanBuilder
4. **Integration Testing** (2-3 Tage)
   - E2E tests
   - Load tests
5. **Documentation** (2 Tage)
   - User guide
   - Migration guide

**Total Timeline:** 7-10 Tage (Integration only)  
**Combined with v5.0:** 25-35 Tage (with overlap: 20-28 Tage)

---

**STATUS:** 🟢 **READY FOR INTEGRATION PHASE**

**Created:** 12. Oktober 2025, 20:10 Uhr  
**Integration Effort:** ~3,050 LOC in 7-10 Tagen  
**Combined Effort (v5.0 + Integration):** ~10,500 LOC in 20-28 Tagen

---

**LET'S UNIFY THE ORCHESTRATION! 🚀**
