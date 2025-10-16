# SUPERVISOR LAYER DESIGN - Intelligent Agent Selection in Scientific Pipeline

**Author:** VERITAS v7.0 Development  
**Date:** 12. Oktober 2025, 03:30 Uhr  
**Status:** 🎯 **DESIGN PROPOSAL - Ready for Implementation**

---

## 📋 Executive Summary

**Problem:**  
UnifiedOrchestratorV7 hat einen `agent_orchestrator` Parameter, nutzt ihn aber nicht. Es gibt bereits einen **SupervisorAgent** (`veritas_supervisor_agent.py`, 1,154 LOC) der **LLM-basiert Agents auswählt**, aber er ist nicht in die Scientific Pipeline integriert.

**Lösung:**  
**Intelligente Supervisor-Schicht zwischen Scientific Phases**

```
Flow:
1. RAG Search (UDS3)
2. Phase 1: Hypothesis → identifiziert missing_information
3. 🆕 Phase 1.5: Supervisor Agent Selection (LLM-driven)
   - Input: missing_information + query + rag_results
   - SupervisorAgent decompose query → select agents
   - Output: selected_agents[] mit reasoning
4. 🆕 Phase 1.6: Parallel Agent Execution
   - Execution via existing AgentCoordinator
   - Results: agent_results{}
5. Phase 2-6: Scientific Process (mit agent_results als Context)
6. 🆕 Phase 6.5: Agent Result Synthesis
   - Merge scientific_process + agent_results
   - Final answer mit external data
```

**Key Innovation:**  
**JSON-Driven Supervisor Integration** - Kein Code-Refactoring der Scientific Phases nötig!

---

## 🏗️ Bestehende Komponenten (Inventar)

### ✅ SupervisorAgent (bereits vorhanden!)

**File:** `backend/agents/veritas_supervisor_agent.py` (1,154 LOC)

**Komponenten:**

1. **QueryDecomposer** (Lines 280-493)
   - LLM-basierte Query-Zerlegung in atomare Subqueries
   - Dependency-Graph-Validierung (DAG)
   - Output: `List[SubQuery]`
   
   ```python
   subqueries = await query_decomposer.decompose_query(
       query_text="Brauche ich Baugenehmigung für Carport mit PV in München?",
       user_context={"location": "München"},
       complexity_hint="standard"
   )
   # Output:
   # [
   #   SubQuery(query_text="Baugenehmigung Carport Bayern", query_type="construction_info", priority=1.0),
   #   SubQuery(query_text="Solarstrahlung München", query_type="environmental_data", priority=0.9),
   #   SubQuery(query_text="Kosten PV-Anlage Carport", query_type="financial_data", priority=0.8)
   # ]
   ```

2. **AgentSelector** (Lines 494-692)
   - Capability-basiertes Agent-Matching
   - RAG-Context-Boosting
   - Confidence-Scoring
   - Output: `AgentSelection` (selected_agents + fallback_agents)
   
   ```python
   agent_selection = await agent_selector.select_agents(
       subquery=subqueries[0],
       rag_context=rag_results
   )
   # Output:
   # AgentSelection(
   #   selected_agents=[
   #     AgentAssignment(agent_type="construction", confidence_score=0.95),
   #     AgentAssignment(agent_type="environmental", confidence_score=0.85)
   #   ],
   #   fallback_agents=[
   #     AgentAssignment(agent_type="document_retrieval", confidence_score=0.70)
   #   ]
   # )
   ```

3. **ResultSynthesizer** (Lines 693-930)
   - LLM-basierte Narrative-Generierung
   - Konflikt-Detektion zwischen Agent-Ergebnissen
   - Deduplizierung redundanter Informationen
   - Output: `SynthesizedResult`
   
   ```python
   synthesized = await result_synthesizer.synthesize_results(
       query_text="Brauche ich Baugenehmigung...",
       agent_results=[construction_result, weather_result, financial_result],
       rag_context=rag_results
   )
   # Output:
   # SynthesizedResult(
   #   response_text="Nach § 50 LBO BW ist ein Carport bis 30m² verfahrensfrei. Für München (Solarstrahlung: 1,200 kWh/m²/a) lohnt sich eine PV-Anlage mit Kosten von 5,000-15,000 EUR und ROI von 8-12 Jahren.",
   #   confidence_score=0.85,
   #   sources=[...],
   #   conflicts_detected=[]
   # )
   ```

**Main Class:** `SupervisorAgent` (Lines 931-1045)
- Orchestriert alle 3 Komponenten
- Factory: `get_supervisor_agent()`, `create_supervisor_agent()`
- Fully async

### ✅ UnifiedOrchestratorV7 (Scientific Pipeline)

**File:** `backend/orchestration/unified_orchestrator_v7.py` (693 LOC)

**Flow:**
```python
async def process_query(user_query: str) -> OrchestratorResult:
    # 1. RAG Search (UDS3)
    rag_results = await self._collect_rag_results(user_query)
    
    # 2. Scientific Phases (6 phases)
    phase_results = await self._execute_scientific_phases(
        query=user_query,
        rag_results=rag_results
    )
    
    # 3. Final Answer
    final_answer = self._extract_final_answer(phase_results)
    
    return OrchestratorResult(...)
```

**Problem:**
- `self.agent_orchestrator` Parameter vorhanden aber ungenutzt (Line 127)
- Keine Agent-Koordination zwischen Phasen
- Keine external data sources (APIs)

### ✅ ScientificPhaseExecutor

**File:** `backend/services/scientific_phase_executor.py` (740 LOC)

**Flow:**
```python
async def execute_phase(phase_config: Dict, context: PhaseExecutionContext):
    # 1. Load Jinja2 prompt from JSON
    prompt = self._construct_prompt(phase_config, context)
    
    # 2. Ollama LLM Call
    llm_response = await self.ollama_client.generate_response(...)
    
    # 3. JSON Schema Validation
    validated_output = self._validate_output(llm_response, phase_config["output_schema"])
    
    return PhaseResult(...)
```

**Key Feature:**  
`PhaseExecutionContext` (Lines 20-47) - **Kann erweitert werden!**

```python
@dataclass
class PhaseExecutionContext:
    user_query: str
    rag_results: Dict[str, Any]
    previous_phases: Dict[str, PhaseResult]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 🆕 NEW: Supervisor-Ergebnisse
    # supervisor_subqueries: List[SubQuery] = field(default_factory=list)
    # supervisor_agent_plan: AgentExecutionPlan = None
    # agent_results: Dict[str, Any] = field(default_factory=dict)
```

---

## 🎯 Implementierungskonzept

### Option 1: JSON-Driven Supervisor Phases ⭐ **EMPFOHLEN**

**Idee:**  
Supervisor-Logik als **zusätzliche Pseudo-Phases** in JSON-Config

**Vorteile:**
- ✅ Keine Änderung an Scientific Phases (clean separation)
- ✅ Supervisor optional (via config)
- ✅ Klar definierte Input/Output-Schema
- ✅ Testbar wie normale Phases

**Implementation:**

#### 1️⃣ Extend `default_method.json`

```json
{
  "method_id": "default_scientific_method",
  "version": "2.0.0",
  "supervisor_enabled": true,  // 🆕 Feature Flag
  
  "phases": [
    // ... existing Phase 1: Hypothesis ...
    
    {
      "phase_id": "supervisor_agent_selection",  // 🆕 NEW
      "phase_number": 1.5,
      "name": "Intelligente Agent-Auswahl",
      "description": "LLM-basierte Auswahl von Spezial-Agents basierend auf missing_information",
      
      "dependencies": {
        "required_steps": ["hypothesis"],
        "wait_for_completion": true
      },
      
      "execution": {
        "executor": "supervisor",  // 🆕 Custom Executor
        "method": "select_agents",
        "timeout_seconds": 10
      },
      
      "input_mapping": {
        "query": "user_query",
        "missing_information": "phases.hypothesis.output.missing_information",
        "rag_results": "rag_results",
        "user_context": "metadata.user_context"
      },
      
      "output_schema": {
        "type": "object",
        "required": ["subqueries", "agent_plan", "selected_agents"],
        "properties": {
          "subqueries": {
            "type": "array",
            "description": "Atomare Teilfragen",
            "items": {
              "type": "object",
              "properties": {
                "id": {"type": "string"},
                "query_text": {"type": "string"},
                "query_type": {"type": "string"},
                "priority": {"type": "number"}
              }
            }
          },
          "agent_plan": {
            "type": "object",
            "properties": {
              "parallel_agents": {"type": "array"},
              "sequential_agents": {"type": "array"}
            }
          },
          "selected_agents": {
            "type": "array",
            "description": "Ausgewählte Agents mit Reasoning",
            "items": {
              "type": "object",
              "properties": {
                "agent_type": {"type": "string"},
                "confidence_score": {"type": "number"},
                "reason": {"type": "string"}
              }
            }
          }
        }
      }
    },
    
    {
      "phase_id": "agent_execution",  // 🆕 NEW
      "phase_number": 1.6,
      "name": "Parallel Agent-Execution",
      "description": "Führt ausgewählte Agents parallel aus",
      
      "dependencies": {
        "required_steps": ["supervisor_agent_selection"],
        "wait_for_completion": true
      },
      
      "execution": {
        "executor": "agent_coordinator",  // 🆕 Custom Executor
        "method": "execute_agents",
        "max_parallel": 5,
        "timeout_seconds": 30
      },
      
      "input_mapping": {
        "agent_plan": "phases.supervisor_agent_selection.output.agent_plan",
        "rag_results": "rag_results",
        "user_query": "user_query"
      },
      
      "output_schema": {
        "type": "object",
        "required": ["agent_results", "execution_metadata"],
        "properties": {
          "agent_results": {
            "type": "object",
            "description": "Results per agent type",
            "additionalProperties": {
              "type": "object",
              "properties": {
                "summary": {"type": "string"},
                "confidence_score": {"type": "number"},
                "processing_time": {"type": "number"},
                "sources": {"type": "array"}
              }
            }
          },
          "execution_metadata": {
            "type": "object",
            "properties": {
              "total_agents_executed": {"type": "number"},
              "successful_agents": {"type": "number"},
              "failed_agents": {"type": "number"}
            }
          }
        }
      }
    },
    
    // ... existing Phase 2-6 ...
    
    {
      "phase_id": "agent_result_synthesis",  // 🆕 NEW
      "phase_number": 6.5,
      "name": "Agent Result Synthesis",
      "description": "Merge scientific process + agent results zu finaler Antwort",
      
      "dependencies": {
        "required_steps": ["metacognition", "agent_execution"],
        "wait_for_completion": true
      },
      
      "execution": {
        "executor": "supervisor",
        "method": "synthesize_results",
        "timeout_seconds": 15
      },
      
      "input_mapping": {
        "query": "user_query",
        "scientific_conclusion": "phases.conclusion.output",
        "agent_results": "phases.agent_execution.output.agent_results",
        "rag_results": "rag_results"
      },
      
      "output_schema": {
        "type": "object",
        "required": ["final_answer", "confidence_score", "sources"],
        "properties": {
          "final_answer": {
            "type": "string",
            "description": "Finale Antwort mit allen Quellen"
          },
          "confidence_score": {"type": "number"},
          "sources": {"type": "array"},
          "conflicts_detected": {"type": "array"}
        }
      }
    }
  ]
}
```

#### 2️⃣ Extend `UnifiedOrchestratorV7`

**File:** `backend/orchestration/unified_orchestrator_v7.py`

```python
class UnifiedOrchestratorV7:
    def __init__(self, ...):
        # ... existing code ...
        
        # 🆕 Initialize SupervisorAgent
        if self.agent_orchestrator or self._is_supervisor_enabled():
            from backend.agents.veritas_supervisor_agent import get_supervisor_agent
            self.supervisor_agent = await get_supervisor_agent(self.ollama_client)
        else:
            self.supervisor_agent = None
    
    def _is_supervisor_enabled(self) -> bool:
        """Check if supervisor is enabled in method config"""
        method_config = self.phase_executor.get_method_config()
        return method_config.get("supervisor_enabled", False)
    
    async def _execute_scientific_phases(self, ...):
        """Execute all phases INCLUDING supervisor phases"""
        
        for phase_config in phases:
            phase_id = phase_config["phase_id"]
            
            # Check executor type
            executor = phase_config.get("execution", {}).get("executor", "llm")
            
            if executor == "supervisor":
                # 🆕 Supervisor-Phase
                result = await self._execute_supervisor_phase(phase_config, context)
            
            elif executor == "agent_coordinator":
                # 🆕 Agent-Execution-Phase
                result = await self._execute_agent_coordination_phase(phase_config, context)
            
            else:
                # Standard LLM-Phase
                result = await self.phase_executor.execute_phase(phase_config, context)
            
            phase_results[phase_id] = result
        
        return phase_results
    
    async def _execute_supervisor_phase(
        self,
        phase_config: Dict[str, Any],
        context: PhaseExecutionContext
    ) -> PhaseResult:
        """
        Execute Supervisor-Phase
        
        Possible methods:
        - select_agents: Query Decomposition + Agent Selection
        - synthesize_results: Final Answer Synthesis
        """
        method = phase_config["execution"]["method"]
        input_mapping = phase_config.get("input_mapping", {})
        
        # Map inputs from context
        inputs = self._map_inputs(input_mapping, context)
        
        if method == "select_agents":
            # Phase 1.5: Agent Selection
            subqueries = await self.supervisor_agent.query_decomposer.decompose_query(
                query_text=inputs["query"],
                user_context=inputs.get("user_context", {}),
                complexity_hint=self._infer_complexity(inputs["missing_information"])
            )
            
            agent_plan = await self.supervisor_agent.create_agent_plan(
                subqueries=subqueries,
                rag_context=inputs["rag_results"]
            )
            
            output = {
                "subqueries": [sq.to_dict() for sq in subqueries],
                "agent_plan": agent_plan.to_dict(),
                "selected_agents": [
                    {
                        "agent_type": a.agent_type,
                        "confidence_score": a.confidence_score,
                        "reason": a.reason
                    }
                    for _, a in agent_plan.parallel_agents + agent_plan.sequential_agents
                ]
            }
            
        elif method == "synthesize_results":
            # Phase 6.5: Final Synthesis
            synthesized = await self.supervisor_agent.result_synthesizer.synthesize_results(
                query_text=inputs["query"],
                agent_results=self._convert_to_agent_results(inputs["agent_results"]),
                rag_context=inputs["rag_results"]
            )
            
            output = synthesized.to_dict()
        
        else:
            raise ValueError(f"Unknown supervisor method: {method}")
        
        # Validate output against schema
        validated_output = self._validate_output(output, phase_config["output_schema"])
        
        return PhaseResult(
            phase_id=phase_config["phase_id"],
            status="completed",
            output=validated_output,
            execution_time_ms=...,
            metadata={"executor": "supervisor", "method": method}
        )
    
    async def _execute_agent_coordination_phase(
        self,
        phase_config: Dict[str, Any],
        context: PhaseExecutionContext
    ) -> PhaseResult:
        """
        Execute Agent-Coordination-Phase (Phase 1.6)
        
        Uses existing AgentCoordinator to execute agents in parallel
        """
        input_mapping = phase_config.get("input_mapping", {})
        inputs = self._map_inputs(input_mapping, context)
        
        agent_plan = inputs["agent_plan"]
        
        # Execute agents via AgentCoordinator
        if self.agent_orchestrator:
            # Use existing AgentCoordinator
            from backend.agents.veritas_api_agent_core_components import create_agent_coordinator
            
            coordinator = create_agent_coordinator(
                orchestrator=self.agent_orchestrator
            )
            
            agent_results = {}
            successful = 0
            failed = 0
            
            # Execute parallel agents
            for subquery_id, assignment in agent_plan["parallel_agents"]:
                try:
                    result = coordinator._execute_agent(
                        agent_type=assignment["agent_type"],
                        query_data={
                            "query": inputs["user_query"],
                            "rag_context": inputs["rag_results"]
                        },
                        query_id=subquery_id
                    )
                    agent_results[assignment["agent_type"]] = result
                    successful += 1
                except Exception as e:
                    logger.error(f"Agent {assignment['agent_type']} failed: {e}")
                    failed += 1
            
            output = {
                "agent_results": agent_results,
                "execution_metadata": {
                    "total_agents_executed": successful + failed,
                    "successful_agents": successful,
                    "failed_agents": failed
                }
            }
        else:
            # Fallback: Mock results
            output = {
                "agent_results": {},
                "execution_metadata": {
                    "total_agents_executed": 0,
                    "successful_agents": 0,
                    "failed_agents": 0
                }
            }
        
        validated_output = self._validate_output(output, phase_config["output_schema"])
        
        return PhaseResult(
            phase_id=phase_config["phase_id"],
            status="completed",
            output=validated_output,
            execution_time_ms=...,
            metadata={"executor": "agent_coordinator"}
        )
    
    def _map_inputs(
        self,
        input_mapping: Dict[str, str],
        context: PhaseExecutionContext
    ) -> Dict[str, Any]:
        """
        Map input_mapping to actual values from context
        
        Example:
            input_mapping = {
                "query": "user_query",
                "missing_information": "phases.hypothesis.output.missing_information"
            }
            
            → {
                "query": "Brauche ich Baugenehmigung...",
                "missing_information": ["solar radiation", "cost estimate"]
            }
        """
        inputs = {}
        
        for key, path in input_mapping.items():
            if path == "user_query":
                inputs[key] = context.user_query
            elif path == "rag_results":
                inputs[key] = context.rag_results
            elif path.startswith("phases."):
                # Navigate through previous phases
                parts = path.split(".")
                value = context.previous_phases
                for part in parts[1:]:  # Skip "phases"
                    if part == "output":
                        value = value.output if hasattr(value, 'output') else value
                    else:
                        value = value.get(part) if isinstance(value, dict) else getattr(value, part, None)
                inputs[key] = value
            elif path.startswith("metadata."):
                key_name = path.split(".", 1)[1]
                inputs[key] = context.metadata.get(key_name)
        
        return inputs
    
    def _infer_complexity(self, missing_information: List[str]) -> str:
        """
        Infer query complexity from missing_information
        
        Rules:
        - 0-1 items: "simple"
        - 2-3 items: "standard"
        - 4+ items: "complex"
        """
        count = len(missing_information)
        if count <= 1:
            return "simple"
        elif count <= 3:
            return "standard"
        else:
            return "complex"
```

---

## 📊 Performance Analysis

### Expected Timeline

**Current (v7.0 without agents):** 40-50s
- RAG Search: 2-3s
- Phase 1-6: 35-45s (6x Ollama calls)

**With Supervisor Integration:** 50-65s (+10-15s)
- RAG Search: 2-3s
- Phase 1: 5-8s
- **Phase 1.5 (Supervisor Selection):** 3-5s (1x Ollama call für decomposition)
- **Phase 1.6 (Agent Execution):** 5-10s (parallel: Construction 2s, Weather 4s, Financial 2s)
- Phase 2-6: 30-40s (with agent_results context)
- **Phase 6.5 (Agent Synthesis):** 2-5s (1x Ollama call)

**Total LLM Calls:** 6 → 8 (+2)

### Optimization: Parallel Execution

**Option: Phase 1.6 parallel zu Phase 2-3**

```
Flow:
Phase 1: Hypothesis (5-8s)
[PARALLEL:
  Phase 1.5 + 1.6: Supervisor + Agents (8-15s)
  ||
  Phase 2-3: Synthesis + Analysis (12-18s)
]
Phase 4-6: Validation + Conclusion + Metacognition (15-20s)
Phase 6.5: Agent Synthesis (2-5s)

Total: 40-50s (NO INCREASE!)
```

---

## 🎯 Implementation Plan

### Phase 1: JSON Config Extension (1-2 hours)

**Tasks:**
1. ✅ Backup `default_method.json`
2. ✅ Add 3 new phases:
   - 1.5: supervisor_agent_selection
   - 1.6: agent_execution
   - 6.5: agent_result_synthesis
3. ✅ Add `supervisor_enabled: true` flag
4. ✅ Define output_schema for each phase
5. ✅ Test JSON syntax validation

**Files:**
- `config/scientific_methods/default_method.json`

### Phase 2: Orchestrator Extension (2-3 hours)

**Tasks:**
1. ✅ Add `_execute_supervisor_phase()` method
2. ✅ Add `_execute_agent_coordination_phase()` method
3. ✅ Add `_map_inputs()` helper
4. ✅ Add `_infer_complexity()` helper
5. ✅ Update `_execute_scientific_phases()` to check executor type
6. ✅ Initialize `self.supervisor_agent` in `__init__()`

**Files:**
- `backend/orchestration/unified_orchestrator_v7.py`

### Phase 3: Context Extension (30 min)

**Tasks:**
1. ✅ Extend `PhaseExecutionContext`:
   ```python
   supervisor_subqueries: List[SubQuery] = field(default_factory=list)
   supervisor_agent_plan: Optional[Dict[str, Any]] = None
   agent_results: Dict[str, Any] = field(default_factory=dict)
   ```
2. ✅ Update prompt construction to include agent_results

**Files:**
- `backend/services/scientific_phase_executor.py`

### Phase 4: Testing (1-2 hours)

**Tasks:**
1. ✅ Test Supervisor Phase Execution (Phase 1.5)
2. ✅ Test Agent Coordination (Phase 1.6)
3. ✅ Test Agent Synthesis (Phase 6.5)
4. ✅ Test full pipeline with construction query
5. ✅ Test with environmental query
6. ✅ Performance benchmarks

**Test Queries:**
- "Brauche ich Baugenehmigung für Carport mit PV in München?"
- "Wie ist die Luftqualität in Stuttgart?"
- "Welche Förderungen gibt es für energetische Sanierung in BW?"

### Phase 5: Documentation (30 min)

**Tasks:**
1. ✅ Update integration reports
2. ✅ Create supervisor integration guide
3. ✅ Update v7.0 architecture diagrams

---

## ✅ Advantages of This Approach

1. **✅ Clean Separation:**
   - Scientific phases unverändert
   - Supervisor als zusätzliche Schichten
   - Klar definierte Interfaces

2. **✅ JSON-Driven:**
   - Supervisor aktivierbar via `supervisor_enabled: true`
   - Keine Code-Änderungen für On/Off
   - Testbar wie normale Phases

3. **✅ Re-uses Existing Code:**
   - SupervisorAgent bereits vorhanden (1,154 LOC)
   - AgentCoordinator bereits vorhanden
   - Keine Duplikation

4. **✅ Flexible Input Mapping:**
   - `input_mapping` in JSON definiert Datenzugriff
   - `phases.hypothesis.output.missing_information` → automatisch aufgelöst
   - Kein hard-coded Context-Access

5. **✅ Extensible:**
   - Weitere Supervisor-Methods einfach hinzufügbar
   - Weitere Custom Executors möglich (`executor: "custom"`)

---

## 🚀 Next Steps

**Empfehlung:** User Decision

**Option A: Implement NOW (4-6 hours)**
1. Backup config files
2. Implement Phase 1-3 (JSON + Orchestrator + Context)
3. Test with 3 test queries
4. Validate performance impact

**Option B: Run E2E Test FIRST (30 min)**
1. Execute `python tests\test_unified_orchestrator_v7_real.py`
2. Analyze gaps in final answers
3. Decide if Supervisor is needed
4. Then implement (4-6 hours)

**Option C: Defer to v7.1 (focus on prompt tuning)**
1. Mark as "Future Enhancement"
2. Tune existing prompts (4-6 hours)
3. Implement Supervisor in v7.1

---

## 📝 Summary

**Status:** ✅ **DESIGN COMPLETE - Ready for Implementation**

**Key Innovation:**
- **JSON-Driven Supervisor Integration**
- **LLM-based Agent Selection** (keine hard-coded Regeln)
- **Clean Separation** (Scientific Phases unverändert)

**Implementation Effort:** 4-6 hours

**Expected Outcome:**
```
Query: "Brauche ich Baugenehmigung für Carport mit PV in München?"

Current Output (v7.0 without agents):
"Nach § 50 LBO BW ist ein Carport bis 30m² verfahrensfrei."

With Supervisor Integration:
"Nach § 50 LBO BW ist ein Carport bis 30m² verfahrensfrei. 
Für München (Solarstrahlung: 1,200 kWh/m²/a) lohnt sich eine 
PV-Anlage mit Kosten von 5,000-15,000 EUR und ROI von 8-12 Jahren 
(800 EUR/Jahr Ersparnis). Beachten Sie Grenzabstand (3m) und ggf. 
Denkmalschutz."

Sources:
- UDS3 Vector Search (LBO BW § 50)
- Ollama LLM Reasoning (Scientific Phases 1-6)
- Construction Agent (Grenzabstand-Regeln)
- Weather Agent (DWD API, Solar Data)
- Financial Agent (Cost Calculation)
```

**Bereit für User-Decision!** 🚀

---

**END OF DESIGN DOCUMENT**
