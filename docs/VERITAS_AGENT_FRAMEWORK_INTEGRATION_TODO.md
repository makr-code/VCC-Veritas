# 🤖 VERITAS AGENT FRAMEWORK INTEGRATION - TODO & ROADMAP

**Date:** 8. Oktober 2025
**Source:** `codespaces-blank/` Mockup Implementation
**Target:** Integration in Veritas Production System
**Priority:** HIGH (Next Major Feature after Phase 5)

---

## 📋 EXECUTIVE SUMMARY

Das **codespaces-blank** Repository enthält ein **hochmodernes Multi-Agenten-Framework** für komplexe Rechercheaufgaben, das das aktuelle Veritas-Agentensystem **signifikant verbessern** kann.

### Key Features des Mockup-Systems:

✅ **Hybrid Orchestration Model**
- Deterministische State Machine (Preprocessing → Execution → Postprocessing → Report)
- KI-native Agenten-Orchestrierung (Sequential, Parallel, Conditional, Collaborative)
- JSON-basierte Recherchepläne als "Living Documents"

✅ **Multi-Agent Architecture**
- **OrchestratorAgent** - Master-Agent für Workflow-Koordination
- **DataRetrievalAgent** - Web/DB-Suche
- **DataAnalysisAgent** - Code Interpreter, Statistik
- **SynthesisAgent** - LLM-gestützte Zusammenfassungen
- **ValidationAgent** - Faktenprüfung, Konsistenz ("Guardian of Integrity")
- **TriageAgent** - Automatische Plan-Auswahl

✅ **Production-Grade Features**
- **Schema-Driven Design** - JSON Schema Validation (Draft 2020-12)
- **Audit Trail** - History-Table Pattern für DSGVO/EU AI Act Compliance
- **Tool Registry** - OpenAPI-basierte Werkzeug-Spezifikationen
- **Telemetry System** - Agent-to-Agent Communication Tracking
- **Event Stream** - Real-time Polling für Frontend-Integration
- **Simulation/Replay** - Debugging & Analytics

✅ **Integration Points**
- PostgreSQL + jsonb als Saga-Log
- Tool-Scopes & Least Privilege
- Human-in-the-Loop Review
- Polyglot Storage (SQL/Graph/Vector/File)

---

## 🎯 INTEGRATION GOALS

### Short-Term (Week 1-2):
1. ✅ **Code Analyse** - Verstehen der Architektur
2. 🔄 **Gap Analysis** - Vergleich mit aktuellem Veritas-System
3. 🔄 **Proof of Concept** - Single-Agent Integration Test

### Medium-Term (Week 3-6):
1. 🔄 **Schema Integration** - Research Plan Schema in Veritas
2. 🔄 **Agent Migration** - Bestehende Agenten auf neues Framework
3. 🔄 **Orchestrator Setup** - Hybrid Orchestration Model

### Long-Term (Week 7-12):
1. 🔄 **Full Production** - Multi-Agent Orchestration Live
2. 🔄 **Advanced Features** - Collaborative Patterns, Telemetry
3. 🔄 **Compliance** - Audit Trail, DSGVO/EU AI Act

---

## 📊 CURRENT STATE ANALYSIS

### Veritas Existing Agent System:

| Component | Current Implementation | Mockup Equivalent | Gap |
|-----------|----------------------|-------------------|-----|
| **Orchestration** | Manual/hardcoded in `veritas_intelligent_pipeline.py` | `OrchestratorAgent` + State Machine | ❌ No dynamic orchestration |
| **Agents** | Single-purpose (Financial, Social, etc.) | Modular Registry-based | ⚠️ Limited collaboration |
| **Schema** | Implicit in code | JSON Schema (v2020-12) | ❌ No validation |
| **Audit Trail** | Basic logging | History-Table Pattern | ❌ Not compliance-ready |
| **Tool Registry** | Hardcoded in agents | OpenAPI-based Registry | ❌ No formal contracts |
| **State Management** | In-memory/ad-hoc | PostgreSQL jsonb Saga-Log | ❌ Not persistent |
| **Event System** | None | Event Stream + Telemetry | ❌ No real-time updates |
| **Parallel Execution** | Not supported | Orchestrator Pattern | ❌ Sequential only |
| **Human Review** | Not integrated | HumanInTheLoopReview | ❌ Manual process |

**Verdict:** 🔴 **Significant architectural gap** - Mockup is **2-3 generations ahead**!

---

## 🏗️ INTEGRATION ARCHITECTURE

### Proposed Hybrid Architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    VERITAS FRONTEND                         │
│              (veritas_app.py / Streamlit)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────▼─────────────────┐
        │   VERITAS API BACKEND            │
        │  (FastAPI + Streaming Progress)  │
        └────────┬────────────────┬────────┘
                 │                │
    ┌────────────▼────┐   ┌──────▼────────────┐
    │ Phase 5 Hybrid  │   │  Agent Framework  │
    │ Search System   │   │  (NEW!)           │
    └────────┬────────┘   └──────┬────────────┘
             │                   │
    ┌────────▼────────┐   ┌──────▼────────────────────────┐
    │ BM25 + UDS3     │   │  Research Plan Orchestrator   │
    │ Retrieval       │   │  (State Machine + OrchestratorAgent) │
    └─────────────────┘   └──────┬────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Agent Registry        │
                    │  - DataRetrievalAgent   │
                    │  - DataAnalysisAgent    │
                    │  - SynthesisAgent       │
                    │  - ValidationAgent      │
                    │  - TriageAgent          │
                    └────────┬────────────────┘
                             │
                ┌────────────▼──────────────────┐
                │   Tool Registry              │
                │  - BM25Search (Phase 5!)     │
                │  - UDS3VectorSearch          │
                │  - WebSearch                 │
                │  - CodeInterpreter           │
                │  - DatabaseQuery             │
                └──────────────────────────────┘
```

### Integration Strategy: **Parallel Development + Gradual Migration**

1. ✅ **Keep Phase 5 Running** - No disruption to Hybrid Search
2. 🔄 **New Module** - `backend/agents/framework/` for new architecture
3. 🔄 **Dual Mode** - Support both old & new agent systems
4. 🔄 **Gradual Migration** - Move agents one-by-one
5. 🔄 **Feature Flag** - `VERITAS_ENABLE_AGENT_FRAMEWORK=false` initially

---

## 📝 DETAILED INTEGRATION TODO

### PHASE 0: PREPARATION & ANALYSIS ✅ (CURRENT)

#### 0.1. Code Review ✅
- [x] Analysiere `codespaces-blank/` Struktur
- [x] Verstehe Orchestrator-Pattern
- [x] Identifiziere Kern-Komponenten
- [x] Dokumentiere Integration-Strategie

#### 0.2. Gap Analysis 🔄
- [ ] **Liste alle Veritas-Agenten** und ihre Funktionen
  ```bash
  # Run this:
  ls -la backend/agents/veritas_api_agent_*.py
  ```
- [ ] **Mappe auf Mockup-Agenten**:
  - `veritas_api_agent_financial.py` → `DataRetrievalAgent` + `DataAnalysisAgent`
  - `veritas_api_agent_social.py` → `DataRetrievalAgent`
  - etc.
- [ ] **Identifiziere fehlende Funktionen**:
  - Welche Veritas-Agenten haben KEINE Mockup-Äquivalente?
  - Welche neuen Tools brauchen wir?

#### 0.3. Dependency Check 🔄
- [ ] Prüfe Python-Versionen (Mockup: Python 3.9+)
- [ ] Prüfe FastAPI-Kompatibilität
- [ ] Prüfe PostgreSQL-Setup (falls noch nicht vorhanden)
- [ ] Prüfe `jsonschema` Library Version

---

### PHASE 1: SCHEMA & PERSISTENCE (Week 1-2)

#### 1.1. Research Plan Schema Integration

**Goal:** JSON Schema für Veritas-Recherchepläne definieren

**Tasks:**
- [ ] **Kopiere Schema-Files**:
  ```bash
  mkdir -p backend/agents/framework/schemas
  cp codespaces-blank/schemas/research_plan.schema.json backend/agents/framework/schemas/
  cp codespaces-blank/schemas/registry.json backend/agents/framework/schemas/
  ```

- [ ] **Erstelle Veritas-spezifisches Schema** (`veritas_research_plan.schema.json`):
  - Basierend auf Mockup-Schema
  - Erweitert um Veritas-spezifische Felder:
    - `uds3_databases`: Array von UDS3-Datenbanken
    - `phase5_hybrid_search`: Boolean flag
    - `security_level`: Veritas SecurityLevel
    - `source_domains`: Legal, Social, Environmental, etc.

- [ ] **Schema Validator** (`backend/agents/framework/schema_validation.py`):
  ```python
  from jsonschema import Draft202012Validator, ValidationError

  def validate_research_plan(plan_document: dict) -> bool:
      """Validate research plan against Veritas schema."""
      schema = load_schema("veritas_research_plan.schema.json")
      validator = Draft202012Validator(schema)
      try:
          validator.validate(plan_document)
          return True
      except ValidationError as e:
          logger.error(f"Schema validation failed: {e}")
          return False
  ```

- [ ] **Tests** (`tests/test_schema_validation.py`):
  - Valide Pläne akzeptiert
  - Invalide Pläne rejected
  - Edge cases (missing fields, wrong types)

**Files to Create:**
- `backend/agents/framework/schemas/veritas_research_plan.schema.json`
- `backend/agents/framework/schema_validation.py`
- `tests/test_schema_validation.py`

**Acceptance Criteria:**
- ✅ Schema validates valid plans
- ✅ Schema rejects invalid plans
- ✅ 100% test coverage

---

#### 1.2. PostgreSQL Persistence Layer

**Goal:** Datenbank-Tabellen für Research Plans

**Tasks:**
- [ ] **Database Setup Script** (`scripts/setup_research_plan_db.py`):
  ```sql
  -- research_plans (Templates)
  CREATE TABLE research_plans (
      plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name TEXT NOT NULL,
      description TEXT,
      latest_version INTEGER DEFAULT 1,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );

  -- research_plan_versions (Versionierung)
  CREATE TABLE research_plan_versions (
      plan_id UUID REFERENCES research_plans(plan_id),
      version INTEGER NOT NULL,
      plan_document JSONB NOT NULL,
      is_active BOOLEAN DEFAULT TRUE,
      created_by TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      PRIMARY KEY (plan_id, version)
  );

  -- research_plan_instances (Aktive Recherchen)
  CREATE TABLE research_plan_instances (
      instance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      plan_id UUID REFERENCES research_plans(plan_id),
      plan_version INTEGER NOT NULL,
      instance_document JSONB NOT NULL,
      status TEXT NOT NULL,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );

  -- instance_history (Audit Trail / Saga-Log)
  CREATE TABLE instance_history (
      history_id BIGSERIAL PRIMARY KEY,
      instance_id UUID REFERENCES research_plan_instances(instance_id),
      modification_date TIMESTAMPTZ DEFAULT NOW(),
      modified_by TEXT NOT NULL,
      change_delta JSONB,
      full_document_snapshot JSONB
  );

  -- Indexes
  CREATE INDEX idx_instances_status ON research_plan_instances(status);
  CREATE INDEX idx_history_instance ON instance_history(instance_id);
  CREATE INDEX idx_history_timestamp ON instance_history(modification_date);
  ```

- [ ] **History Trigger** (für automatisches Audit-Log):
  ```sql
  CREATE OR REPLACE FUNCTION log_instance_change()
  RETURNS TRIGGER AS $$
  BEGIN
      INSERT INTO instance_history (
          instance_id,
          modified_by,
          change_delta,
          full_document_snapshot
      ) VALUES (
          NEW.instance_id,
          current_user,
          to_jsonb(NEW) - to_jsonb(OLD),  -- Delta
          to_jsonb(NEW)  -- Full snapshot
      );
      RETURN NEW;
  END;
  $$ LANGUAGE plpgsql;

  CREATE TRIGGER instance_history_trigger
  AFTER UPDATE ON research_plan_instances
  FOR EACH ROW EXECUTE FUNCTION log_instance_change();
  ```

- [ ] **ORM Models** (`backend/agents/framework/models.py`):
  ```python
  from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean
  from sqlalchemy.dialects.postgresql import UUID, JSONB
  import uuid

  class ResearchPlan(Base):
      __tablename__ = "research_plans"
      plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      name = Column(String, nullable=False)
      description = Column(String)
      latest_version = Column(Integer, default=1)
      created_at = Column(DateTime, server_default=func.now())
      updated_at = Column(DateTime, onupdate=func.now())

  class ResearchPlanInstance(Base):
      __tablename__ = "research_plan_instances"
      instance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      plan_id = Column(UUID(as_uuid=True), ForeignKey("research_plans.plan_id"))
      plan_version = Column(Integer)
      instance_document = Column(JSONB, nullable=False)
      status = Column(String, nullable=False)
      created_at = Column(DateTime, server_default=func.now())
      updated_at = Column(DateTime, onupdate=func.now())
  ```

- [ ] **CRUD Operations** (`backend/agents/framework/plan_store.py`):
  ```python
  async def create_plan_instance(plan_id: UUID, overrides: dict) -> ResearchPlanInstance:
      """Create new research plan instance."""

  async def get_plan_instance(instance_id: UUID) -> ResearchPlanInstance:
      """Retrieve plan instance by ID."""

  async def update_plan_instance(instance_id: UUID, updates: dict) -> None:
      """Update plan instance (triggers audit log)."""

  async def get_instance_history(instance_id: UUID) -> List[dict]:
      """Retrieve full audit trail for instance."""
  ```

**Files to Create:**
- `scripts/setup_research_plan_db.py`
- `backend/agents/framework/models.py`
- `backend/agents/framework/plan_store.py`
- `tests/test_plan_store.py`

**Acceptance Criteria:**
- ✅ Database tables created
- ✅ History trigger working
- ✅ CRUD operations tested
- ✅ Audit trail captures all changes

---

### PHASE 2: ORCHESTRATOR ENGINE (Week 3-4)

#### 2.1. State Machine Implementation

**Goal:** Workflow State Machine für Research Plans

**Tasks:**
- [ ] **Copy & Adapt Orchestrator** (`backend/agents/framework/orchestrator.py`):
  ```python
  # Base auf codespaces-blank/app/orchestrator.py
  from enum import Enum

  class WorkflowState(Enum):
      PENDING = "PENDING"
      PREPROCESSING = "PREPROCESSING"
      EXECUTING = "EXECUTING"
      POSTPROCESSING = "POSTPROCESSING"
      AWAITING_REVIEW = "AWAITING_REVIEW"
      COMPLETED = "COMPLETED"
      FAILED = "FAILED"

  class WorkflowStateMachine:
      """Manages research plan workflow transitions."""

      def __init__(self, instance_id: UUID):
          self.instance_id = instance_id
          self.current_state = WorkflowState.PENDING

      async def advance(self) -> WorkflowState:
          """Advance to next state."""

      async def fail(self, reason: str) -> WorkflowState:
          """Mark workflow as failed."""

      async def retry(self) -> WorkflowState:
          """Retry from last successful state."""
  ```

- [ ] **OrchestratorAgent** (`backend/agents/framework/orchestrator_agent.py`):
  ```python
  class OrchestratorAgent(BaseAgent):
      """Master agent for workflow coordination."""

      async def execute_plan(self, instance_id: UUID) -> dict:
          """Execute complete research plan."""

          # 1. Load plan instance
          instance = await get_plan_instance(instance_id)

          # 2. Initialize state machine
          sm = WorkflowStateMachine(instance_id)

          # 3. Execute phases
          await self._execute_preprocess(instance)
          await sm.advance()

          await self._execute_execution_steps(instance)
          await sm.advance()

          await self._execute_postprocess(instance)
          await sm.advance()

          await self._generate_report(instance)
          await sm.advance()

          return {"status": "COMPLETED", "instance_id": instance_id}

      async def _execute_execution_steps(self, instance: dict) -> None:
          """Execute DAG of execution steps."""

          steps = instance["instance_document"]["stages"]["execution_steps"]

          # Build dependency graph
          dag = self._build_dag(steps)

          # Execute based on dependencies
          for step in dag.topological_sort():
              await self._execute_step(step)
  ```

- [ ] **DAG Execution Logic**:
  - Topological sort for dependency resolution
  - Parallel execution for independent tasks
  - Error handling & retry logic

**Files to Create:**
- `backend/agents/framework/orchestrator.py`
- `backend/agents/framework/orchestrator_agent.py`
- `backend/agents/framework/dag_executor.py`
- `tests/test_orchestrator.py`

**Acceptance Criteria:**
- ✅ State machine transitions correctly
- ✅ DAG executes in correct order
- ✅ Parallel tasks execute concurrently
- ✅ Error handling works

---

#### 2.2. Integration with Existing Pipeline

**Goal:** Verbinde Orchestrator mit Veritas Intelligent Pipeline

**Tasks:**
- [ ] **Adapter Pattern** (`backend/agents/framework/pipeline_adapter.py`):
  ```python
  class VeritasPipelineAdapter:
      """Adapts new Orchestrator to existing Intelligent Pipeline."""

      def __init__(self, orchestrator: OrchestratorAgent,
                   pipeline: IntelligentMultiAgentPipeline):
          self.orchestrator = orchestrator
          self.pipeline = pipeline

      async def execute_hybrid(self, query: str) -> dict:
          """Execute using both old and new system."""

          # Option 1: Use old pipeline
          if not self._should_use_new_orchestrator(query):
              return await self.pipeline.execute(query)

          # Option 2: Use new orchestrator
          plan_instance = await self._create_research_plan(query)
          return await self.orchestrator.execute_plan(plan_instance.instance_id)

      def _should_use_new_orchestrator(self, query: str) -> bool:
          """Decide which system to use based on query complexity."""
          # Feature flag
          if not os.getenv("VERITAS_ENABLE_AGENT_FRAMEWORK"):
              return False

          # Complexity heuristic
          return len(query.split()) > 20  # Complex queries use new system
  ```

- [ ] **Backend API Endpoint** (in `veritas_api_backend.py`):
  ```python
  @app.post("/v2/research/execute")
  async def execute_research_plan(
      query: str,
      template_id: Optional[str] = None
  ):
      """Execute research plan (new orchestrator)."""

      try:
          # Create plan instance
          if template_id:
              instance = await create_plan_instance(template_id, {"query": query})
          else:
              # Auto-select template via TriageAgent
              instance = await triage_and_create(query)

          # Execute
          orchestrator = get_orchestrator_agent()
          result = await orchestrator.execute_plan(instance.instance_id)

          return {
              "instance_id": str(instance.instance_id),
              "status": result["status"],
              "result": result
          }

      except Exception as e:
          logger.error(f"Research plan execution failed: {e}")
          raise HTTPException(status_code=500, detail=str(e))
  ```

**Files to Create:**
- `backend/agents/framework/pipeline_adapter.py`
- Update `backend/api/veritas_api_backend.py`
- `tests/test_pipeline_adapter.py`

**Acceptance Criteria:**
- ✅ Dual-mode execution works
- ✅ Feature flag respected
- ✅ API endpoint functional
- ✅ Fallback to old pipeline works

---

### PHASE 3: AGENT MIGRATION (Week 5-8)

#### 3.1. Agent Registry Setup

**Goal:** Centralized Agent Registry

**Tasks:**
- [ ] **Copy Registry** (`backend/agents/framework/registry.py`):
  ```python
  # Based on codespaces-blank/agents/registry.py

  class AgentRegistry:
      """Central registry for all agents."""

      def __init__(self):
          self._agents: Dict[str, BaseAgent] = {}

      def register(self, name: str, agent: BaseAgent) -> None:
          """Register agent."""
          self._agents[name] = agent

      def get(self, name: str) -> BaseAgent:
          """Get agent by name."""
          if name not in self._agents:
              raise ValueError(f"Agent '{name}' not registered")
          return self._agents[name]

      def execute(self, request: AgentRequest) -> AgentResult:
          """Execute agent task."""
          agent = self.get(request.agent)
          return agent.run(request)

  # Global instance
  _registry = None

  def get_agent_registry() -> AgentRegistry:
      global _registry
      if _registry is None:
          _registry = AgentRegistry()
          _initialize_default_agents(_registry)
      return _registry
  ```

- [ ] **Base Agent Class** (`backend/agents/framework/base.py`):
  ```python
  # Based on codespaces-blank/agents/base.py

  @dataclass
  class AgentRequest:
      task_id: str
      tool: str
      inputs: Dict[str, Any]
      context: Dict[str, Any] = field(default_factory=dict)

  @dataclass
  class AgentResult:
      agent: str
      task_id: str
      tool: str
      status: str
      source: Optional[str]
      preview: Dict[str, Any]
      metadata: Dict[str, Any] = field(default_factory=dict)

  class BaseAgent:
      name: str = "BaseAgent"

      def __init__(self, tool_registry: ToolRegistry):
          self._tool_registry = tool_registry

      async def run(self, request: AgentRequest) -> AgentResult:
          raise NotImplementedError
  ```

**Files to Create:**
- `backend/agents/framework/registry.py`
- `backend/agents/framework/base.py`
- `tests/test_registry.py`

---

#### 3.2. Migrate Existing Agents

**Goal:** Port Veritas Agents to New Framework

**Priority Order:**
1. **DataRetrievalAgent** (replaces `veritas_api_agent_construction.py`, etc.)
2. **SynthesisAgent** (LLM-based synthesis)
3. **ValidationAgent** (fact-checking)
4. **DataAnalysisAgent** (code interpreter)

**Example Migration:**

**OLD** (`veritas_api_agent_financial.py`):
```python
class FinancialDataAgent:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    async def query_financial_data(self, query: str) -> dict:
        # Direct DB query
        results = await self.db_manager.query(query)
        return results
```

**NEW** (`backend/agents/framework/agents/data_retrieval.py`):
```python
class DataRetrievalAgent(BaseAgent):
    name = "DataRetrievalAgent"

    async def run(self, request: AgentRequest) -> AgentResult:
        """Execute data retrieval task."""

        tool = request.tool

        if tool == "financial_query":
            return await self._query_financial(request)
        elif tool == "web_search":
            return await self._web_search(request)
        elif tool == "phase5_hybrid_search":  # NEW!
            return await self._phase5_search(request)
        else:
            raise AgentToolNotSupported(f"Tool '{tool}' not supported")

    async def _phase5_search(self, request: AgentRequest) -> AgentResult:
        """Use Phase 5 Hybrid Search."""
        from backend.api.veritas_phase5_integration import get_hybrid_retriever

        hybrid_retriever = get_hybrid_retriever()
        results = await hybrid_retriever.retrieve(
            request.inputs["query"],
            top_k=request.inputs.get("top_k", 10)
        )

        return AgentResult(
            agent=self.name,
            task_id=request.task_id,
            tool=tool,
            status="SUCCESS",
            source="phase5_hybrid",
            preview={"results": [r.to_dict() for r in results[:3]]},
            metadata={"total_results": len(results)}
        )
```

**Migration Checklist per Agent:**
- [ ] Create new agent class inheriting from `BaseAgent`
- [ ] Implement `run()` method with tool dispatch
- [ ] Migrate business logic to tool-specific methods
- [ ] Add tool to Tool Registry
- [ ] Write comprehensive tests
- [ ] Update documentation

**Files to Migrate:**
- `veritas_api_agent_construction.py` → `DataRetrievalAgent` (construction domain)
- `veritas_api_agent_environmental.py` → `DataRetrievalAgent` (environmental domain)
- `veritas_api_agent_financial.py` → `DataRetrievalAgent` + `DataAnalysisAgent`
- `veritas_api_agent_social.py` → `DataRetrievalAgent` (social domain)
- `veritas_api_agent_traffic.py` → `DataRetrievalAgent` (traffic domain)

**New Agents to Create:**
- `SynthesisAgent` (LLM-based)
- `ValidationAgent` (fact-checking)
- `TriageAgent` (plan selection)

---

#### 3.3. Tool Registry

**Goal:** OpenAPI-based Tool Registry

**Tasks:**
- [ ] **Tool Registry** (`backend/agents/framework/tool_registry.py`):
  ```python
  # Based on codespaces-blank/app/tool_registry.py

  @dataclass
  class ToolSpec:
      name: str
      description: str
      version: str
      scope: str  # "retrieval", "analysis", "synthesis", "validation"
      openapi_schema: dict
      metadata: dict = field(default_factory=dict)

  class ToolRegistry:
      """Registry for all tools with OpenAPI specs."""

      def __init__(self):
          self._tools: Dict[str, ToolSpec] = {}

      def register(self, spec: ToolSpec) -> None:
          """Register tool."""
          self._tools[spec.name] = spec

      def get(self, name: str) -> ToolSpec:
          """Get tool spec."""
          return self._tools[name]

      def list_by_scope(self, scope: str) -> List[ToolSpec]:
          """List tools by scope."""
          return [t for t in self._tools.values() if t.scope == scope]
  ```

- [ ] **Tool Definitions** (`backend/agents/framework/tools/`):
  ```python
  # tools/phase5_hybrid_search.json
  {
    "name": "phase5_hybrid_search",
    "description": "Hybrid Search using BM25 + UDS3 Vector Retrieval",
    "version": "1.0.0",
    "scope": "retrieval",
    "openapi_schema": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "Search query"
        },
        "top_k": {
          "type": "integer",
          "description": "Number of results",
          "default": 10
        }
      },
      "required": ["query"]
    },
    "metadata": {
      "latency_sla_ms": 200,
      "max_results": 100,
      "supports_filters": true
    }
  }
  ```

- [ ] **Tool Access Control** (Least Privilege):
  ```python
  class ToolAccessControl:
      """Enforce least privilege for tool access."""

      def __init__(self):
          self._agent_scopes = {
              "DataRetrievalAgent": ["retrieval"],
              "DataAnalysisAgent": ["analysis"],
              "SynthesisAgent": ["synthesis"],
              "ValidationAgent": ["validation"],
              "OrchestratorAgent": ["retrieval", "analysis", "synthesis", "validation"]
          }

      def can_access(self, agent: str, tool: str) -> bool:
          """Check if agent can access tool."""
          tool_spec = get_tool_registry().get(tool)
          agent_scopes = self._agent_scopes.get(agent, [])
          return tool_spec.scope in agent_scopes
  ```

**Files to Create:**
- `backend/agents/framework/tool_registry.py`
- `backend/agents/framework/tools/phase5_hybrid_search.json`
- `backend/agents/framework/tools/web_search.json`
- `backend/agents/framework/tools/code_interpreter.json`
- `backend/agents/framework/access_control.py`
- `tests/test_tool_registry.py`

---

### PHASE 4: ADVANCED FEATURES (Week 9-12)

#### 4.1. Parallel & Conditional Execution

**Goal:** Orchestration Patterns

**Tasks:**
- [ ] **Parallel Executor** (`backend/agents/framework/executors/parallel.py`):
  ```python
  async def execute_parallel_tasks(tasks: List[AgentRequest]) -> List[AgentResult]:
      """Execute tasks in parallel."""

      async def run_task(task):
          agent = get_agent_registry().get(task.agent)
          return await agent.run(task)

      results = await asyncio.gather(*[run_task(t) for t in tasks])
      return results
  ```

- [ ] **Conditional Executor** (`backend/agents/framework/executors/conditional.py`):
  ```python
  async def execute_conditional_step(step: dict) -> AgentResult:
      """Execute step with conditional routing."""

      # Execute first task
      first_result = await execute_task(step["tasks"][0])

      # Evaluate condition
      next_task = _evaluate_condition(first_result, step["conditions"])

      # Execute next task
      return await execute_task(next_task)
  ```

- [ ] **Collaborative Executor** (`backend/agents/framework/executors/collaborative.py`):
  ```python
  async def execute_collaborative_step(step: dict) -> AgentResult:
      """Execute with multi-agent collaboration."""

      # Assemble team
      team = [get_agent_registry().get(t["agent"]) for t in step["tasks"]]

      # Iterative refinement
      result = None
      for iteration in range(step.get("max_iterations", 3)):
          results = await asyncio.gather(*[
              agent.run(create_request(step, result)) for agent in team
          ])

          # Check quality
          if meets_quality_threshold(results):
              break

          result = aggregate_results(results)

      return result
  ```

**Files to Create:**
- `backend/agents/framework/executors/parallel.py`
- `backend/agents/framework/executors/conditional.py`
- `backend/agents/framework/executors/collaborative.py`
- `tests/test_executors.py`

---

#### 4.2. Telemetry & Event Stream

**Goal:** Real-time Monitoring & Debugging

**Tasks:**
- [ ] **Telemetry Store** (`backend/agents/framework/telemetry.py`):
  ```python
  @dataclass
  class TelemetryEvent:
      instance_id: UUID
      agent: str
      tool: str
      timestamp: datetime
      latency_ms: float
      status: str
      metadata: dict

  class TelemetryStore:
      """In-memory telemetry store."""

      def __init__(self):
          self._events: List[TelemetryEvent] = []

      def record(self, event: TelemetryEvent) -> None:
          """Record telemetry event."""
          self._events.append(event)

      def query(self,
                instance_id: Optional[UUID] = None,
                agent: Optional[str] = None,
                since: Optional[datetime] = None) -> List[TelemetryEvent]:
          """Query telemetry events."""
          # Filter logic
  ```

- [ ] **Event Stream** (`backend/agents/framework/event_stream.py`):
  ```python
  class EventStream:
      """SSE event stream for real-time updates."""

      def __init__(self):
          self._events: List[dict] = []
          self._sequence = 0

      def publish(self, event: dict) -> None:
          """Publish event."""
          event["sequence"] = self._sequence
          self._sequence += 1
          self._events.append(event)

      async def stream(self, since: int = 0) -> AsyncGenerator:
          """Stream events since sequence number."""
          for event in self._events:
              if event["sequence"] >= since:
                  yield f"data: {json.dumps(event)}\n\n"
  ```

- [ ] **API Endpoints**:
  ```python
  @app.get("/v2/research/instances/{instance_id}/events")
  async def stream_instance_events(instance_id: str):
      """SSE endpoint for instance events."""
      return StreamingResponse(
          get_event_stream().stream_instance(instance_id),
          media_type="text/event-stream"
      )

  @app.get("/telemetry")
  async def get_telemetry(
      instance_id: Optional[str] = None,
      agent: Optional[str] = None
  ):
      """Get telemetry data."""
      return get_telemetry_store().query(instance_id, agent)
  ```

**Files to Create:**
- `backend/agents/framework/telemetry.py`
- `backend/agents/framework/event_stream.py`
- Update `backend/api/veritas_api_backend.py`
- `tests/test_telemetry.py`

---

#### 4.3. Human-in-the-Loop Review

**Goal:** Compliance Gateway

**Tasks:**
- [ ] **Review Task** (`backend/agents/framework/tasks/human_review.py`):
  ```python
  async def execute_human_review_task(task: dict, instance_id: UUID) -> dict:
      """Execute human-in-the-loop review."""

      # 1. Prepare review package
      package = {
          "instance_id": instance_id,
          "status": "AWAITING_REVIEW",
          "report_preview": await generate_report_preview(instance_id),
          "validation_results": await run_validation_agent(instance_id),
          "review_deadline": datetime.now() + timedelta(hours=24)
      }

      # 2. Send notification
      await send_review_notification(package)

      # 3. Wait for approval (polling or webhook)
      approval = await wait_for_approval(instance_id)

      # 4. Update instance
      if approval["approved"]:
          await update_instance_status(instance_id, "COMPLETED")
      else:
          await update_instance_status(instance_id, "REJECTED")
          await log_rejection_reason(instance_id, approval["reason"])

      return approval
  ```

- [ ] **Review API**:
  ```python
  @app.get("/v2/research/instances/{instance_id}/review")
  async def get_review_package(instance_id: str):
      """Get review package."""
      return await prepare_review_package(instance_id)

  @app.post("/v2/research/instances/{instance_id}/approve")
  async def approve_instance(instance_id: str, approval: dict):
      """Approve/reject instance."""
      return await process_approval(instance_id, approval)
  ```

**Files to Create:**
- `backend/agents/framework/tasks/human_review.py`
- Update `backend/api/veritas_api_backend.py`
- `tests/test_human_review.py`

---

### PHASE 5: PRODUCTION DEPLOYMENT (Week 13-16)

#### 5.1. Feature Flag Rollout

**Environment Variables:**
```bash
# Stage 1: Development (Week 13)
VERITAS_ENABLE_AGENT_FRAMEWORK=true
VERITAS_AGENT_FRAMEWORK_MODE=development  # Logs everything
VERITAS_AGENT_FRAMEWORK_FALLBACK=true     # Falls back to old pipeline on error

# Stage 2: Staging (Week 14)
VERITAS_AGENT_FRAMEWORK_MODE=staging
VERITAS_AGENT_FRAMEWORK_PERCENTAGE=10     # 10% traffic

# Stage 3: Production Gradual (Week 15)
VERITAS_AGENT_FRAMEWORK_PERCENTAGE=25     # 25% → 50% → 100%

# Stage 4: Full Production (Week 16)
VERITAS_AGENT_FRAMEWORK_MODE=production
VERITAS_AGENT_FRAMEWORK_PERCENTAGE=100
VERITAS_AGENT_FRAMEWORK_FALLBACK=false    # No fallback
```

---

#### 5.2. Monitoring & Alerting

**Metrics to Track:**
- Agent execution latency (P50, P95, P99)
- Tool call success rate
- Plan completion rate
- Error rate by agent/tool
- Parallel execution efficiency
- Audit trail completeness

**Dashboards:**
- Research Plan Overview (active, completed, failed)
- Agent Performance (latency, success rate)
- Tool Usage (top tools, error rates)
- Audit Trail Viewer (compliance)

---

#### 5.3. Documentation

**Documents to Create:**
- [ ] **Architecture Overview** (`docs/AGENT_FRAMEWORK_ARCHITECTURE.md`)
- [ ] **Agent Developer Guide** (`docs/AGENT_DEVELOPER_GUIDE.md`)
- [ ] **Tool Registry Guide** (`docs/TOOL_REGISTRY_GUIDE.md`)
- [ ] **Research Plan Schema Reference** (`docs/RESEARCH_PLAN_SCHEMA.md`)
- [ ] **Migration Guide** (`docs/AGENT_MIGRATION_GUIDE.md`)
- [ ] **Deployment Guide** (`docs/AGENT_FRAMEWORK_DEPLOYMENT.md`)

---

## 📈 SUCCESS METRICS

### Phase 1-2 (Schema & Orchestrator):
- ✅ Schema validates 100% of test plans
- ✅ Database tables created & tested
- ✅ State machine passes all transition tests
- ✅ Audit trail captures all changes

### Phase 3 (Agent Migration):
- ✅ All core agents migrated (DataRetrieval, Synthesis, Validation)
- ✅ Tool Registry operational
- ✅ Access control enforced
- ✅ 100% backward compatibility

### Phase 4 (Advanced Features):
- ✅ Parallel execution 2-5x faster than sequential
- ✅ Telemetry captures all agent actions
- ✅ Event stream delivers real-time updates
- ✅ Human-in-the-loop review functional

### Phase 5 (Production):
- ✅ Gradual rollout to 100% traffic
- ✅ Zero critical incidents
- ✅ Agent latency <500ms P95
- ✅ Plan completion rate >95%
- ✅ Full audit trail for all plans

---

## ⚠️ RISKS & MITIGATIONS

### Risk 1: Schema Complexity
**Issue:** JSON Schema very complex, hard to maintain

**Mitigation:**
- Start with simplified schema (Phase 1)
- Add complexity incrementally
- Comprehensive schema tests
- Schema documentation generator

### Risk 2: PostgreSQL Performance
**Issue:** JSONB queries may be slow at scale

**Mitigation:**
- GIN indexes on JSONB fields
- Materialized views for common queries
- Caching layer (Redis)
- Load testing before production

### Risk 3: Agent Migration Breaking Changes
**Issue:** Migrating agents may break existing functionality

**Mitigation:**
- Dual-mode operation (old + new)
- Feature flag per agent
- Comprehensive integration tests
- Gradual migration (one agent at a time)

### Risk 4: Orchestrator Bugs
**Issue:** State machine logic errors

**Mitigation:**
- Extensive unit tests
- Property-based testing
- State machine visualization
- Dry-run mode

### Risk 5: Audit Trail Storage Growth
**Issue:** History table grows indefinitely

**Mitigation:**
- Partition by month
- Archival strategy (>6 months to cold storage)
- Delta-only storage (not full snapshots)
- Compression

---

## 🎯 IMMEDIATE NEXT STEPS

### Week 1 (THIS WEEK):

1. ✅ **READ THIS TODO** - Done!
2. 🔄 **Gap Analysis** - Compare Veritas agents vs Mockup
   ```bash
   python scripts/analyze_agent_gap.py
   ```
3. 🔄 **Setup Schema** - Copy & adapt research plan schema
   ```bash
   mkdir -p backend/agents/framework/schemas
   cp codespaces-blank/schemas/*.json backend/agents/framework/schemas/
   ```
4. 🔄 **Database Setup** - Create research plan tables
   ```bash
   python scripts/setup_research_plan_db.py
   ```
5. 🔄 **Proof of Concept** - Single-agent integration test
   ```bash
   python tests/test_single_agent_poc.py
   ```

### Week 2:

6. 🔄 **Schema Validation** - Implement & test
7. 🔄 **CRUD Operations** - Plan store CRUD
8. 🔄 **State Machine** - Basic orchestrator
9. 🔄 **First Agent** - DataRetrievalAgent migration
10. 🔄 **Integration Test** - End-to-end test

---

## 📞 CONTACTS & RESOURCES

### Documentation:
- **Mockup Docs:** `codespaces-blank/docs/konzept.md`
- **Mockup TODO:** `codespaces-blank/docs/todo.md`
- **Current Veritas:** `docs/STATUS_REPORT.md`

### Code Repositories:
- **Mockup:** `c:/VCC/veritas/codespaces-blank/`
- **Veritas:** `c:/VCC/veritas/`

### Key Files to Study:
1. `codespaces-blank/agents/base.py` - Agent architecture
2. `codespaces-blank/app/orchestrator.py` - State machine
3. `codespaces-blank/schemas/research_plan.schema.json` - Schema
4. `codespaces-blank/app/tool_registry.py` - Tool registry
5. `codespaces-blank/app/event_stream.py` - Event system

---

## 🎉 CONCLUSION

Das **codespaces-blank** Mockup-System ist ein **hochmodernes Multi-Agenten-Framework**, das Veritas **signifikant verbessern** kann!

### Key Benefits:

✅ **Compliance-Ready** - DSGVO/EU AI Act Audit Trail
✅ **Production-Grade** - State Machine, Error Handling, Retry
✅ **Flexible** - JSON Schema, Dynamic Orchestration
✅ **Scalable** - Parallel Execution, Event-Driven
✅ **Observable** - Telemetry, Event Stream, Replay

### Recommendation:

**START INTEGRATION NOW!** 🚀

Priorität: **HIGH** (Next major feature after Phase 5)

Timeline: **16 weeks** (4 months)

Effort: **~2-3 FTE** (Full-Time Equivalent)

**Let's build the future of intelligent research systems!** 💪

---

**Last Updated:** 8. Oktober 2025, 22:00
**Version:** 1.0 DRAFT
**Status:** READY FOR REVIEW

---

**Next Action:** Review this TODO with team → Start Phase 0.2 (Gap Analysis)
