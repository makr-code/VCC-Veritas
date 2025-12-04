# Agent System Integration Analysis - v7.0

**Date:** 13. Oktober 2025, 03:00 Uhr
**Status:** 🔍 **INTEGRATION ANALYSIS**
**Goal:** Agent-System ↔ UnifiedOrchestratorV7 Integration

---

## 📊 Current State Analysis

### Existing Agent Infrastructure

**1. Agent Registry System** (`veritas_api_agent_registry.py`, 680 LOC)
- ✅ **Self-registering agents** mit Capabilities
- ✅ **Shared Resource Pool** (Database, Ollama, UDS3)
- ✅ **Agent Lifecycle Management** (PERSISTENT, ON_DEMAND, SINGLETON, POOLED)
- ✅ **Capability-based Discovery**
- ✅ **35+ AgentCapabilities** definiert:
  - Core: `GEO_CONTEXT_RESOLUTION`, `LEGAL_FRAMEWORK_ANALYSIS`, `DOMAIN_CLASSIFICATION`
  - Domain: `ENVIRONMENTAL_DATA`, `BUILDING_PERMIT`, `TRANSPORT_DATA`, `TAXATION`
  - Integration: `EXTERNAL_API`, `REAL_TIME_DATA`, `DOCUMENT_RETRIEVAL`
  - Analysis: `FINANCIAL_IMPACT`, `SUCCESS_PROBABILITY`, `TIMELINE_PREDICTION`

**2. Agent Orchestrator** (`veritas_api_agent_orchestrator.py`, 1,137 LOC)
- ✅ **Query-based Pipeline Management**
- ✅ **JSON Schema-driven Task Creation**
- ✅ **Dynamic Agent Selection** (basierend auf Domain + Complexity)
- ✅ **RAG Context Integration** (adjusts priorities)
- ✅ **Parallel + Sequential Execution**
- ✅ **AgentCoordinator Integration**

**3. Agent Coordinator** (`veritas_api_agent_core_components.py`, ~800 LOC)
- ✅ **Query Queue Management**
- ✅ **Agent Execution** via AgentRegistry
- ✅ **Dynamic Scaling** (spawn/terminate based on load)
- ✅ **GUI Updates** (Message Broker)
- ✅ **Health Monitoring**

**4. Specialized Agents** (20+ agents im `backend/agents/`)
- ✅ **Construction Agent** (Baugenehmigungen)
- ✅ **Environmental Agent** (BImSchG, Luftqualität)
- ✅ **Financial Agent** (Finanzanalyse)
- ✅ **Traffic Agent** (ÖPNV, Verkehr)
- ✅ **Weather Agent** (DWD API)
- ✅ **Chemical Data Agent** (ChemSpider API)
- ✅ **Wikipedia Agent** (Hintergrund-Infos)
- ✅ **Technical Standards Agent** (DIN, ISO)

**5. Agent Pipeline Manager** (`veritas_api_agent_pipeline_manager.py`, ~400 LOC)
- ✅ **Pipeline Storage** (in-memory)
- ✅ **Task Tracking**
- ✅ **Status Management**

---

## 🔍 v7.0 Integration Points

### Current v7.0 Architecture

```
User Query
    ↓
UnifiedOrchestratorV7 (570 LOC)
    ├─ Query Enhancement (placeholder)
    ├─ UDS3 Hybrid Search (REAL) ✅
    ├─ Scientific Phases (6x Ollama) ✅
    │   ├─ Phase 1: Hypothesis
    │   ├─ Phase 2: Synthesis
    │   ├─ Phase 3: Analysis
    │   ├─ Phase 4: Validation
    │   ├─ Phase 5: Conclusion
    │   └─ Phase 6: Metacognition
    └─ Final Answer Extraction ✅
```

**Missing: Agent Coordination Layer** ❌

---

## 🎯 Integration Gap Analysis

### Gap 1: Agent Coordination Missing in v7.0

**Problem:**
- v7.0 UnifiedOrchestratorV7 hat **keine Agent-Integration**
- Nur UDS3 Search + Ollama LLM (wissenschaftliche Phasen)
- **Specialized Agents ignoriert** (Construction, Environmental, Financial, etc.)

**Impact:**
- ❌ Keine externe Datenquellen (DWD Weather, ChemSpider, etc.)
- ❌ Keine domain-spezifische Verarbeitung (Building Permits, Transport)
- ❌ Keine Financial/Timeline/Impact Analysis
- ❌ Keine Real-Time Data Integration

**Evidence:**
```python
# backend/orchestration/unified_orchestrator_v7.py, Line 85
def __init__(
    self,
    config_dir: str = "config",
    method_id: str = "default_method",
    ollama_client: Optional[VeritasOllamaClient] = None,
    uds3_strategy: Optional[Any] = None,
    agent_orchestrator: Optional[Any] = None,  # ⚠️ PARAMETER EXISTS BUT UNUSED!
    enable_streaming: bool = True
):
    # ...
    self.agent_orchestrator = agent_orchestrator  # ⚠️ STORED BUT NEVER CALLED!
```

---

### Gap 2: Dual Orchestration Systems

**Problem:**
- **AgentOrchestrator** (existing) manages Agent-Pipelines
- **UnifiedOrchestratorV7** (v7.0) manages Scientific Phases
- **No coordination between them!**

**Current Flow:**
```
Query
  ↓
[AgentOrchestrator]                [UnifiedOrchestratorV7]
  ├─ Domain Detection                ├─ UDS3 Search
  ├─ Agent Selection                 ├─ Scientific Phases
  ├─ Parallel Execution              └─ Final Answer
  └─ Result Aggregation

❌ No communication!
```

**Desired Flow:**
```
Query
  ↓
UnifiedOrchestratorV7 (Coordinator)
  ├─ 1. UDS3 Search (vector + graph)
  ├─ 2. Scientific Phases (6x LLM)
  ├─ 3. Agent Coordination ← NEW!
  │     ├─ Domain Detection
  │     ├─ Capability-based Agent Selection
  │     ├─ Parallel Agent Execution
  │     │   ├─ Construction Agent (if building query)
  │     │   ├─ Weather Agent (if environmental query)
  │     │   ├─ Financial Agent (if cost query)
  │     │   └─ ... (dynamic)
  │     └─ Result Aggregation
  └─ 4. Final Answer (synthesize all sources)
```

---

### Gap 3: Phase Execution Context Limited

**Problem:**
- Scientific Phases nur mit RAG Results (UDS3)
- **Agent Results not passed to LLM phases**

**Current PhaseExecutionContext:**
```python
@dataclass
class PhaseExecutionContext:
    user_query: str
    rag_results: Dict[str, Any]  # ✅ From UDS3

    # Previous phase results
    hypothesis: Optional[Dict[str, Any]] = None
    # ...

    # ❌ MISSING: agent_results: Dict[str, Any]
```

**Needed:**
```python
@dataclass
class PhaseExecutionContext:
    user_query: str
    rag_results: Dict[str, Any]  # From UDS3
    agent_results: Dict[str, Any]  # ← NEW! From specialized agents

    # Previous phase results
    hypothesis: Optional[Dict[str, Any]] = None
    # ...
```

**Use Case Example:**
```
Query: "Brauche ich Baugenehmigung für Carport mit Photovoltaik in BW?"

UDS3 RAG Results:
  - LBO BW § 50 (Carport-Regelung)
  - VwV zu § 50 (Verfahrensfreie Vorhaben)

Agent Results (should be added):
  - Construction Agent: Carport 30m² limit, Grenzabstand rules
  - Environmental Agent: Photovoltaik als privilegierte Nutzung
  - Weather Agent: Solar radiation data (München 1,200 kWh/m²/a)
  - Financial Agent: Kosten 5,000-15,000 EUR, ROI 8-12 Jahre

Scientific Phases (need BOTH RAG + Agent data):
  Phase 1: Hypothesis
    Input: RAG + Agent Results
    Output: "Carport <30m² verfahrensfrei, PV-Anlage privilegiert"

  Phase 2: Synthesis
    Input: RAG + Agent Results + Phase 1
    Output: Evidence clusters (legal + environmental + financial)

  # ...
```

---

## 🏗️ Integration Architecture (Proposed)

### Option 1: Agent Layer AFTER Scientific Phases (Recommended)

**Rationale:**
- Scientific Phases generate **structured hypotheses + validation**
- Agents execute **targeted data collection** based on identified needs
- Final synthesis combines **both streams**

**Flow:**
```
1. UDS3 RAG Search
   ↓
2. Scientific Phases (6x Ollama)
   Phase 1: Hypothesis
     → Identifies: "Need building permit info + solar radiation data"
   Phase 2-6: Continue with RAG data only
   ↓
3. Agent Coordination (NEW)
   Input: Phase results (identifies missing_information)
   Action:
     - If Phase 1 identifies "building permit" → Spawn Construction Agent
     - If Phase 1 identifies "solar data" → Spawn Weather Agent
     - If Phase 1 identifies "cost estimate" → Spawn Financial Agent
   Output: Agent results (external data)
   ↓
4. Agent-Enhanced Synthesis (NEW Phase 7?)
   Input: Phase 1-6 + Agent Results
   Output: Final answer with external data integrated
```

**Pros:**
- ✅ Agents only called when **scientifically justified** (Phase 1 identifies needs)
- ✅ Avoids unnecessary API calls
- ✅ Clear separation: Scientific reasoning → Data collection → Synthesis

**Cons:**
- ⚠️ Agent data not available in Phase 2-6 (could be limitation)
- ⚠️ Need new "Agent-Enhanced Synthesis" phase

---

### Option 2: Agent Layer PARALLEL to Scientific Phases

**Rationale:**
- Start Agents **immediately** based on query analysis
- Scientific Phases + Agent Execution run **in parallel**
- Final synthesis waits for both

**Flow:**
```
1. UDS3 RAG Search
   ↓
2a. Scientific Phases (6x Ollama)    2b. Agent Coordination (NEW)
    Phase 1-6: Ollama LLM             AgentOrchestrator:
    (uses RAG only)                     - Detect domain (building)
                                        - Select agents (Construction, Weather)
                                        - Execute in parallel
   ↓                                  ↓
3. Final Synthesis
   Input: Phase 6 Conclusion + Agent Results
   Output: Combined final answer
```

**Pros:**
- ✅ **Faster execution** (parallel)
- ✅ Agent data available for final synthesis
- ✅ Less changes to scientific phases

**Cons:**
- ⚠️ Agents called **blindly** (no scientific hypothesis-driven selection)
- ⚠️ Potential **wasted API calls** (agents not needed)

---

### Option 3: Agent Layer BEFORE Scientific Phases

**Rationale:**
- Agents **enrich RAG context** before LLM calls
- Scientific Phases work with **full dataset** (RAG + Agent)

**Flow:**
```
1. UDS3 RAG Search
   ↓
2. Agent Coordination (NEW)
   Input: User query + RAG results
   Action:
     - Domain detection
     - Capability-based agent selection
     - Parallel execution (Construction, Weather, Financial)
   Output: Agent results
   ↓
3. Scientific Phases (6x Ollama)
   Input: RAG + Agent Results (combined)
   Phase 1: Hypothesis (uses FULL dataset)
   Phase 2: Synthesis (uses FULL dataset)
   # ...
   ↓
4. Final Answer
```

**Pros:**
- ✅ **Maximum context** for scientific phases
- ✅ Agent data influences **all phases** (hypothesis → validation)
- ✅ Single synthesis point (no post-processing)

**Cons:**
- ⚠️ **Sequential delay** (wait for all agents before LLM)
- ⚠️ Agents called **without hypothesis** (less targeted)
- ⚠️ Higher latency (agents + LLM sequential)

---

## 🎯 Recommended Integration Strategy

### **OPTION 1: Agent Layer AFTER Scientific Phases**

**Implementation Plan:**

### Phase 1: Add Agent Orchestrator Integration (2-3 hours)

**1.1 Update UnifiedOrchestratorV7 Constructor**

```python
# backend/orchestration/unified_orchestrator_v7.py

from backend.agents.veritas_api_agent_orchestrator import AgentOrchestrator

def __init__(
    self,
    config_dir: str = "config",
    method_id: str = "default_method",
    ollama_client: Optional[VeritasOllamaClient] = None,
    uds3_strategy: Optional[Any] = None,
    agent_orchestrator: Optional[AgentOrchestrator] = None,  # NEW: Use real type
    enable_streaming: bool = True
):
    # ...

    # Initialize Agent Orchestrator
    if agent_orchestrator is None:
        try:
            from backend.agents.veritas_api_agent_orchestrator import create_agent_orchestrator
            self.agent_orchestrator = create_agent_orchestrator()
            logger.info("✅ Agent Orchestrator auto-initialized")
        except Exception as e:
            logger.warning(f"⚠️ Agent Orchestrator init failed: {e}")
            self.agent_orchestrator = None
    else:
        self.agent_orchestrator = agent_orchestrator
```

**1.2 Add Agent Coordination Method**

```python
async def _coordinate_agents(
    self,
    user_query: str,
    phase_results: Dict[str, PhaseResult],
    rag_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Coordinate specialized agents based on scientific phase results

    Strategy:
    - Phase 1 (Hypothesis) identifies missing_information
    - Map missing_information → Agent Capabilities
    - Spawn relevant agents
    - Collect results

    Args:
        user_query: Original query
        phase_results: Results from Phase 1-6
        rag_results: RAG search results

    Returns:
        {
            'construction': {...},      # If building query
            'weather': {...},           # If environmental query
            'financial': {...},         # If cost query
            'execution_time_ms': 2341
        }
    """
    if not self.agent_orchestrator:
        logger.warning("⚠️ Agent Orchestrator not available - skipping")
        return {}

    start_time = time.time()

    # Extract missing_information from Phase 1 (Hypothesis)
    hypothesis_result = phase_results.get('phase1_hypothesis')
    if not hypothesis_result:
        return {}

    missing_info = hypothesis_result.output.get('missing_information', [])

    # Map missing_information → Agent Types
    agent_requirements = self._map_missing_info_to_agents(missing_info)

    if not agent_requirements:
        logger.info("ℹ️ No agents required (all info in RAG)")
        return {}

    logger.info(f"🤖 Spawning agents: {list(agent_requirements.keys())}")

    # Execute agents via AgentOrchestrator
    agent_results = {}
    for agent_type, capability in agent_requirements.items():
        try:
            result = await self._execute_single_agent(
                agent_type=agent_type,
                capability=capability,
                query=user_query,
                context={'rag_results': rag_results, 'phase_results': phase_results}
            )
            agent_results[agent_type] = result
        except Exception as e:
            logger.error(f"❌ Agent {agent_type} failed: {e}")
            agent_results[agent_type] = {'error': str(e), 'status': 'failed'}

    execution_time = (time.time() - start_time) * 1000
    agent_results['execution_time_ms'] = execution_time

    logger.info(f"✅ Agents completed: {len(agent_results)} results, {execution_time:.0f}ms")

    return agent_results


def _map_missing_info_to_agents(
    self,
    missing_info: List[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Map missing_information from Phase 1 → Agent Types

    Example missing_info:
    [
        {"type": "user_input", "description": "Grundfläche Carport", "impact": "critical"},
        {"type": "data", "description": "Solarstrahlung München", "impact": "high"},
        {"type": "expertise", "description": "Kostenabschätzung PV-Anlage", "impact": "medium"}
    ]

    Returns:
    {
        'construction': 'BUILDING_PERMIT_PROCESSING',
        'weather': 'REAL_TIME_DATA_ACCESS',
        'financial': 'FINANCIAL_IMPACT_ANALYSIS'
    }
    """
    agent_requirements = {}

    # Keyword-based mapping (simple heuristic)
    for item in missing_info:
        desc = item.get('description', '').lower()

        # Building/Construction
        if any(kw in desc for kw in ['baugenehmigung', 'grundfläche', 'grenzabstand', 'carport', 'garage']):
            agent_requirements['construction'] = 'BUILDING_PERMIT_PROCESSING'

        # Weather/Environmental
        if any(kw in desc for kw in ['solarstrahlung', 'wetter', 'wind', 'temperatur', 'luftqualität']):
            agent_requirements['weather'] = 'REAL_TIME_DATA_ACCESS'

        # Financial
        if any(kw in desc for kw in ['kosten', 'preis', 'finanzierung', 'förderung', 'rentabilität']):
            agent_requirements['financial'] = 'FINANCIAL_IMPACT_ANALYSIS'

        # Transport
        if any(kw in desc for kw in ['öpnv', 'verkehr', 'bus', 'bahn', 'fahrplan']):
            agent_requirements['transport'] = 'TRANSPORT_DATA_PROCESSING'

    return agent_requirements


async def _execute_single_agent(
    self,
    agent_type: str,
    capability: str,
    query: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute single specialized agent

    Delegates to AgentOrchestrator.preprocess_query()
    """
    from backend.agents.veritas_shared_enums import QueryDomain, QueryComplexity

    # Map agent_type → QueryDomain
    domain_mapping = {
        'construction': QueryDomain.BUILDING,
        'environmental': QueryDomain.ENVIRONMENTAL,
        'weather': QueryDomain.ENVIRONMENTAL,
        'financial': QueryDomain.BUSINESS,
        'transport': QueryDomain.TRANSPORT
    }

    query_data = {
        'query': query,
        'user_context': context,
        'complexity': QueryComplexity.STANDARD,
        'domain': domain_mapping.get(agent_type, QueryDomain.ENVIRONMENTAL)
    }

    # Call AgentOrchestrator
    result = self.agent_orchestrator.preprocess_query(query_data)

    return result
```

**1.3 Update Main Processing Pipeline**

```python
async def process_query(self, query: str) -> OrchestratorResult:
    """
    Process Query (updated with Agent Coordination)
    """
    start_time = time.time()

    # 1. RAG Search
    rag_results = await self._collect_rag_results(query)

    # 2. Scientific Phases (6x Ollama)
    phase_results = await self._execute_scientific_phases(
        query=query,
        rag_results=rag_results
    )

    # 3. Agent Coordination (NEW!)
    agent_results = await self._coordinate_agents(
        user_query=query,
        phase_results=phase_results,
        rag_results=rag_results
    )

    # 4. Final Synthesis (combine Phase 6 + Agent Results)
    final_answer = self._synthesize_final_answer(
        phase_results=phase_results,
        agent_results=agent_results
    )

    # ...
```

---

### Phase 2: Add Agent Results to Context (1 hour)

**2.1 Update PhaseExecutionContext**

```python
@dataclass
class PhaseExecutionContext:
    user_query: str
    rag_results: Dict[str, Any]
    agent_results: Dict[str, Any] = field(default_factory=dict)  # NEW!

    # Previous phase results
    hypothesis: Optional[Dict[str, Any]] = None
    # ...
```

**2.2 Update Prompt Construction**

```python
# backend/services/scientific_phase_executor.py

def _construct_prompt(...):
    # ...

    # 6. Template Variables
    if template_vars.get('agent_results'):
        prompt_parts.append(f"\n## Agent Results (External Data)\n```json\n{json.dumps(template_vars['agent_results'], indent=2)}\n```\n")

    # ...
```

---

### Phase 3: Update Prompts for Agent Data (1 hour)

**3.1 Update phase5_conclusion.json**

```json
{
  "instructions": [
    {
      "step": 1,
      "action": "Synthesize final answer from:",
      "requirements": [
        "Phase 1-4 results (scientific reasoning)",
        "RAG results (legal documents)",
        "Agent results (external real-time data)"  // NEW!
      ]
    }
  ]
}
```

---

## 📊 Integration Impact Analysis

### Performance Impact

**Before (Current v7.0):**
```
Total Time: 40-50s
  - UDS3 Search: 2-3s
  - Phase 1-6 (Ollama): 35-45s
  - Final Synthesis: <1s
```

**After (with Agent Integration):**
```
Total Time: 45-60s (+5-10s)
  - UDS3 Search: 2-3s
  - Phase 1-6 (Ollama): 35-45s
  - Agent Coordination: 3-8s (NEW!)
    - Construction Agent: 1-2s (DB lookup)
    - Weather Agent: 2-4s (DWD API call)
    - Financial Agent: 1-2s (calculation)
  - Final Synthesis: <1s
```

**Parallelization Opportunity:**
If Agents run **in parallel** with Phase 2-6:
```
Total Time: 40-50s (NO INCREASE!)
  - UDS3 Search: 2-3s
  - Phase 1 (Hypothesis): 5-8s
  - [PARALLEL START]
    - Phase 2-6 (Ollama): 30-37s
    - Agent Coordination: 3-8s
  - [PARALLEL END]
  - Final Synthesis: <1s
```

---

### Data Quality Impact

**Enriched Context Example:**

**Query:** "Brauche ich Baugenehmigung für Carport mit PV in München?"

**Before (Only RAG):**
```json
{
  "rag_results": {
    "semantic": [
      {"source": "LBO BW § 50", "content": "Verfahrensfreie Vorhaben bis 30m²..."}
    ]
  }
}
```

**After (RAG + Agents):**
```json
{
  "rag_results": {
    "semantic": [
      {"source": "LBO BW § 50", "content": "Verfahrensfreie Vorhaben bis 30m²..."}
    ]
  },
  "agent_results": {
    "construction": {
      "building_permit_required": false,
      "conditions": ["Grundfläche <30m²", "Grenzabstand 3m"],
      "source": "Construction Agent (DB Lookup)"
    },
    "weather": {
      "solar_radiation_kwh_per_m2_year": 1200,
      "avg_sunshine_hours_per_year": 1800,
      "location": "München",
      "source": "DWD Weather Agent (API)"
    },
    "financial": {
      "cost_estimate_eur": {"min": 5000, "max": 15000},
      "roi_years": {"min": 8, "max": 12},
      "annual_savings_eur": 800,
      "source": "Financial Agent (Calculation)"
    }
  }
}
```

**Final Answer Quality:**
```
BEFORE:
"Nach § 50 LBO BW ist ein Carport bis 30m² verfahrensfrei."

AFTER (with Agent data):
"Nach § 50 LBO BW ist ein Carport bis 30m² verfahrensfrei.
Für München (1,200 kWh/m²/a Solarstrahlung) ist eine
Photovoltaikanlage sinnvoll mit Kosten von 5,000-15,000 EUR
und ROI von 8-12 Jahren (800 EUR/Jahr Ersparnis)."
```

---

## ✅ Implementation Checklist

### Phase 1: Core Integration (2-3 hours)
- [ ] Import AgentOrchestrator in unified_orchestrator_v7.py
- [ ] Add auto-initialization in __init__()
- [ ] Implement _coordinate_agents() method
- [ ] Implement _map_missing_info_to_agents() helper
- [ ] Implement _execute_single_agent() helper
- [ ] Update process_query() to call agent coordination
- [ ] Add agent_results to final synthesis

### Phase 2: Context Enhancement (1 hour)
- [ ] Add agent_results field to PhaseExecutionContext
- [ ] Update _construct_prompt() to include agent results
- [ ] Test prompt length (ensure <8K tokens)

### Phase 3: Prompt Updates (1 hour)
- [ ] Update phase5_conclusion.json (add agent results section)
- [ ] Update phase6_metacognition.json (assess agent data quality)
- [ ] Add examples with agent data

### Phase 4: Testing (2-3 hours)
- [ ] Create test_agent_integration.py
- [ ] Test with building query (Construction Agent)
- [ ] Test with environmental query (Weather Agent)
- [ ] Test with financial query (Financial Agent)
- [ ] Test with multi-domain query (multiple agents)
- [ ] Performance benchmarks (with/without agents)

### Phase 5: Documentation (1 hour)
- [ ] Update PHASE4_REAL_INTEGRATION_REPORT.md
- [ ] Create AGENT_INTEGRATION_GUIDE.md
- [ ] Update V7_IMPLEMENTATION_TODO.md
- [ ] Update architecture diagrams

**Total Estimated Time:** 7-9 hours

---

## 🎯 Success Criteria

### Functional
- ✅ Agent Orchestrator accessible from UnifiedOrchestratorV7
- ✅ missing_information → Agent mapping working
- ✅ Agent results passed to final synthesis
- ✅ Construction Agent executes for building queries
- ✅ Weather Agent executes for environmental queries
- ✅ Financial Agent executes for cost queries

### Performance
- ✅ Total execution time <60s (with agents)
- ✅ Agent overhead <10s
- ✅ No blocking (agents execute in parallel if possible)

### Quality
- ✅ Final answers include agent data
- ✅ Agent data properly cited
- ✅ Graceful degradation (agents optional)
- ✅ Error handling (agent failures don't crash system)

---

## 📚 Next Steps

**Option A: Implement Now** (7-9 hours)
1. Start with Phase 1 (Core Integration)
2. Test with simple building query
3. Expand to other agent types

**Option B: Run E2E Test First** (30 min + analysis)
1. Execute test_unified_orchestrator_v7_real.py
2. Analyze current v7.0 performance baseline
3. Then add agent integration

**Option C: Defer to Phase 6** (later)
1. Mark as "Phase 6: Agent Integration"
2. Focus on Phase 5 (E2E Testing + Prompt Tuning)
3. Add agents after v7.0 core is stable

---

**Recommendation:** **Option B** - Run E2E test first, then add agents based on observed gaps in final answers.

**Rationale:**
- See what v7.0 can achieve **without agents** (baseline)
- Identify **specific missing data** in real outputs
- **Targeted agent integration** (only what's needed)

---

**Author:** VERITAS v7.0 Integration Analysis
**Date:** 13. Oktober 2025, 03:00 Uhr
**Status:** Analysis Complete, Awaiting Decision
