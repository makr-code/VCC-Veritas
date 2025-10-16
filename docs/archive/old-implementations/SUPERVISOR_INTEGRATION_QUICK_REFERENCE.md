# SUPERVISOR INTEGRATION - QUICK REFERENCE 📋

**Version:** v7.0 (Config v2.0.0)  
**Last Updated:** 12. Oktober 2025  
**Status:** ✅ Implementation Complete | ⏸️ E2E Test Pending

---

## 🚀 Quick Start

### Enable/Disable Supervisor

**File:** `config/scientific_methods/default_method.json`

```json
{
  "supervisor_enabled": true  // ← Toggle here (true/false)
}
```

**Effect:**
- `true`: Execute all 9 phases (6 scientific + 3 supervisor)
- `false`: Execute only 6 scientific phases (skip 1.5, 1.6, 6.5)

---

## 📊 Phase Overview

| # | Phase ID | Executor | Purpose | LLM Call |
|---|----------|----------|---------|----------|
| 1 | hypothesis | llm | Generate hypothesis, identify gaps | ✅ |
| **1.5** | **supervisor_agent_selection** | **supervisor** | **Decompose query, select agents** | ✅ |
| **1.6** | **agent_execution** | **agent_coordinator** | **Execute agents (parallel)** | ❌ |
| 2 | synthesis | llm | Synthesize evidence | ✅ |
| 3 | analysis | llm | Critical analysis | ✅ |
| 4 | validation | llm | Validate results | ✅ |
| 5 | conclusion | llm | Final conclusion | ✅ |
| 6 | metacognition | llm | Self-assessment | ✅ |
| **6.5** | **agent_result_synthesis** | **supervisor** | **Merge scientific + agent results** | ✅ |

**Total LLM Calls:** 8 (with supervisor) | 6 (without supervisor)

---

## 🔧 Configuration Files

### Main Config
**File:** `config/scientific_methods/default_method.json`

**Key Fields:**
```json
{
  "version": "2.0.0",
  "supervisor_enabled": true,
  "phases": [/* 9 phases */],
  "orchestration_config": {
    "execution_mode": "sequential_with_supervisor",
    "phase_execution": {
      "conditional_phases": [
        "supervisor_agent_selection",
        "agent_execution",
        "agent_result_synthesis"
      ]
    }
  }
}
```

### Phase 1.5 (Agent Selection)
```json
{
  "phase_id": "supervisor_agent_selection",
  "phase_number": 1.5,
  "execution": {
    "executor": "supervisor",
    "method": "select_agents",
    "timeout_seconds": 10
  },
  "input_mapping": {
    "query": "user_query",
    "missing_information": "phases.hypothesis.output.missing_information",
    "rag_results": "rag_results"
  },
  "output_schema": {
    "subqueries": ["string"],
    "agent_plan": {
      "parallel_agents": ["string"],
      "sequential_agents": ["string"]
    },
    "selected_agents": ["string"]
  }
}
```

### Phase 1.6 (Agent Execution)
```json
{
  "phase_id": "agent_execution",
  "phase_number": 1.6,
  "execution": {
    "executor": "agent_coordinator",
    "method": "execute_agents",
    "max_parallel": 5,
    "timeout_seconds": 30
  },
  "input_mapping": {
    "agent_plan": "phases.supervisor_agent_selection.output.agent_plan",
    "subqueries": "phases.supervisor_agent_selection.output.subqueries"
  },
  "output_schema": {
    "agent_results": {},
    "execution_metadata": {
      "total_agents": 0,
      "successful": 0,
      "failed": 0
    }
  }
}
```

### Phase 6.5 (Result Synthesis)
```json
{
  "phase_id": "agent_result_synthesis",
  "phase_number": 6.5,
  "execution": {
    "executor": "supervisor",
    "method": "synthesize_results",
    "timeout_seconds": 15
  },
  "input_mapping": {
    "query": "user_query",
    "scientific_conclusion": "phases.conclusion.output.final_answer",
    "agent_results": "phases.agent_execution.output.agent_results"
  },
  "output_schema": {
    "final_answer": "",
    "confidence_score": 0.0,
    "sources": [],
    "conflicts_detected": []
  }
}
```

---

## 💻 Python API

### Initialize Orchestrator

```python
from backend.orchestration.unified_orchestrator_v7 import UnifiedOrchestratorV7

# With Supervisor Enabled
orchestrator = UnifiedOrchestratorV7(
    config_dir="config",
    method_id="default_method",  # supervisor_enabled=true in config
    ollama_client=ollama_client,
    uds3_strategy=None,  # Auto-initialize
    agent_orchestrator=agent_orchestrator,  # Real agents
    enable_streaming=True
)

# Check if supervisor is enabled
if orchestrator._is_supervisor_enabled():
    print("✅ Supervisor mode active")
```

### Process Query (Non-Streaming)

```python
result = await orchestrator.process_query(
    user_query="Brauche ich Baugenehmigung für Carport mit PV in München?",
    user_id="test_user",
    context={}
)

# Access results
print(f"Final Answer: {result.final_answer['main_answer']}")
print(f"Confidence: {result.confidence}")
print(f"Sources: {result.final_answer.get('sources', [])}")

# Access scientific process
for phase_id, phase_data in result.scientific_process.items():
    print(f"{phase_id}: {phase_data.get('status')}")
```

### Process Query (Streaming)

```python
async for event in orchestrator.process_query_stream(
    user_query="Brauche ich Baugenehmigung für Carport?"
):
    if event.type == "phase_complete":
        phase_id = event.data.get('phase_id')
        status = event.data.get('status')
        print(f"✅ {phase_id}: {status}")
    
    elif event.type == "final_result":
        final_answer = event.data.get('final_answer')
        print(f"🎯 {final_answer['main_answer']}")
```

---

## 🧪 Testing

### Config Validation (Fast - No Ollama/UDS3)

```bash
# Validate config structure + orchestrator import
python tests\test_supervisor_config_validation.py

# Expected output:
# ✅ Config Structure: PASSED
# ✅ Orchestrator Import: PASSED
```

### E2E Test (Full - With Ollama/UDS3)

```bash
# Full pipeline test (9 phases)
python tests\test_unified_orchestrator_v7_real.py

# Expected output:
# ✅ Phase 1: hypothesis
# ✅ Phase 1.5: supervisor_agent_selection
# ✅ Phase 1.6: agent_execution (mock)
# ✅ Phase 2-6: scientific process
# ✅ Phase 6.5: agent_result_synthesis
```

---

## 🔍 Troubleshooting

### Issue: Supervisor phases skipped

**Symptom:** Logs show "Phase 1.5/1.6/6.5 skipped"

**Cause:** `supervisor_enabled=false` in config

**Solution:**
```json
// config/scientific_methods/default_method.json
{
  "supervisor_enabled": true  // ← Set to true
}
```

---

### Issue: Agent execution returns mock results

**Symptom:** `execution_metadata.mock: true` in Phase 1.6

**Cause:** No real `agent_orchestrator` provided

**Solution:**
```python
# Initialize with real orchestrator
from backend.agents.veritas_api_agent_orchestrator import VeritasAgentOrchestrator

agent_orchestrator = VeritasAgentOrchestrator(...)

orchestrator = UnifiedOrchestratorV7(
    ...,
    agent_orchestrator=agent_orchestrator  # ← Provide real orchestrator
)
```

---

### Issue: Ollama timeout during test

**Symptom:** `asyncio.exceptions.CancelledError` during LLM call

**Cause:** Model name incorrect or timeout too short

**Solution:**
```python
# Use correct model name
ollama_client = VeritasOllamaClient(
    base_url="http://localhost:11434",
    timeout=120,  # ← Increase timeout
    model="llama3.2:latest"  # ← Add :latest suffix
)
```

---

### Issue: Input mapping error

**Symptom:** `KeyError` or missing data in supervisor phase

**Cause:** Path resolution failed (e.g., `phases.hypothesis.output.missing_information` not found)

**Solution:**
1. Check if previous phase executed successfully
2. Verify path exists in context:
   ```python
   print(context.previous_phases["hypothesis"]["output"])
   ```
3. Update input_mapping in config if path changed

---

## 📁 File Locations

### Core Files
```
config/
  └─ scientific_methods/
      └─ default_method.json          # Main config (supervisor_enabled)

backend/
  └─ orchestration/
      └─ unified_orchestrator_v7.py   # Orchestrator implementation
  └─ agents/
      └─ veritas_supervisor_agent.py  # SupervisorAgent
      └─ veritas_api_agent_orchestrator.py  # AgentOrchestrator

tests/
  ├─ test_supervisor_config_validation.py  # Config validation (fast)
  └─ test_unified_orchestrator_v7_real.py  # E2E test (full)

docs/
  ├─ SUPERVISOR_INTEGRATION_COMPLETE.md          # Implementation docs
  ├─ SUPERVISOR_INTEGRATION_VALIDATION.md        # Validation report
  ├─ SUPERVISOR_INTEGRATION_EXECUTIVE_SUMMARY.md # Executive summary
  └─ SUPERVISOR_INTEGRATION_QUICK_REFERENCE.md   # This file
```

---

## 🛠️ Maintenance

### Adding New Agent

**Step 1:** Register agent in SupervisorAgent capabilities

```python
# backend/agents/veritas_supervisor_agent.py
AGENT_CAPABILITIES = {
    # ... existing agents ...
    "new_agent": {
        "description": "Description of new agent",
        "capabilities": ["capability1", "capability2"],
        "data_sources": ["API name"]
    }
}
```

**Step 2:** Test agent selection

```python
# Query that should trigger new agent
query = "Query that needs new_agent capability"

# Check if agent is selected
result = await orchestrator.process_query(user_query=query)
selected_agents = result.scientific_process["supervisor_agent_selection"]["output"]["selected_agents"]

assert "new_agent" in selected_agents
```

---

### Debugging Phase Execution

**Enable Debug Logging:**

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run orchestrator
result = await orchestrator.process_query(...)

# Check logs:
# DEBUG: Phase 1.5 input: {'query': '...', 'missing_information': [...]}
# DEBUG: Phase 1.5 output: {'selected_agents': [...]}
```

**Inspect Context:**

```python
# After query execution
for phase_id, phase_data in result.scientific_process.items():
    print(f"\n{phase_id}:")
    print(f"  Status: {phase_data.get('status')}")
    print(f"  Output: {phase_data.get('output')}")
    print(f"  Metadata: {phase_data.get('metadata')}")
```

---

## 📊 Performance Metrics

### Expected Execution Times

| Configuration | Total Time | LLM Calls | Phases |
|---------------|------------|-----------|--------|
| **Without Supervisor** | 34-52s | 6 | 6 |
| **With Supervisor (Mock Agents)** | 44-62s | 8 | 9 |
| **With Supervisor (Real Agents)** | 44-72s | 8 | 9 |

**Breakdown (With Supervisor):**
- Phase 1 (Hypothesis): 5-8s
- Phase 1.5 (Agent Selection): 3-5s
- Phase 1.6 (Agent Execution): 5-10s (parallel)
- Phases 2-6 (Scientific): 25-35s
- Phase 6.5 (Synthesis): 2-5s

---

## 🎯 Common Use Cases

### Use Case 1: Construction Query

**Query:** "Brauche ich Baugenehmigung für Carport mit PV in München?"

**Expected Flow:**
1. Phase 1: Identifies missing: ["solar radiation", "cost estimate", "building regulations"]
2. Phase 1.5: Selects: ["construction", "weather", "financial"]
3. Phase 1.6: Executes agents (parallel)
4. Phase 6.5: Synthesizes: Legal basis + Solar data + Cost estimate

**Expected Agents:**
- Construction: Building regulations, Grenzabstand-Regeln
- Weather: DWD API, Solar radiation München
- Financial: Cost calculation 5K-15K EUR, ROI 8-12 years

---

### Use Case 2: Environmental Query

**Query:** "Wie ist die Luftqualität in Stuttgart?"

**Expected Flow:**
1. Phase 1: Identifies missing: ["air quality data", "pollutant levels"]
2. Phase 1.5: Selects: ["environmental"]
3. Phase 1.6: Executes environmental agent
4. Phase 6.5: Synthesizes: Scientific analysis + Real-time air quality data

**Expected Agents:**
- Environmental: UBA API, PM2.5/PM10/NO2 data, Air quality index

---

### Use Case 3: Pure Legal Query (No Agents)

**Query:** "Was besagt § 50 LBO BW?"

**Expected Flow:**
1. Phase 1: No missing information (legal text in UDS3)
2. Phase 1.5: Selects: [] (empty, no agents needed)
3. Phase 1.6: Skipped (no agents selected)
4. Phases 2-6: Standard scientific process
5. Phase 6.5: Returns scientific conclusion (no agent data)

**Result:** Pure scientific answer from UDS3 + Ollama (no external APIs)

---

## ✅ Checklist

### Before Production Deployment

- [ ] **Config validated:** Run `test_supervisor_config_validation.py` ✅
- [ ] **E2E test passed:** Run `test_unified_orchestrator_v7_real.py` ⏸️
- [ ] **Ollama running:** `curl http://localhost:11434/api/tags` ✅
- [ ] **UDS3 initialized:** PostgreSQL + ChromaDB + Neo4j + CouchDB ⏸️
- [ ] **Agents registered:** SupervisorAgent knows all agents ⏸️
- [ ] **Backup created:** Config backup exists ✅
- [ ] **Documentation updated:** README + API docs ✅
- [ ] **Monitoring setup:** Logs + Metrics ❌
- [ ] **Performance tested:** Load testing ❌

**Current Status:** 4/9 checks passed (44%)

---

## 🚀 Quick Commands

```bash
# Validate config (fast)
python tests\test_supervisor_config_validation.py

# Run E2E test (full)
python tests\test_unified_orchestrator_v7_real.py

# Check Ollama status
curl http://localhost:11434/api/tags

# Backup config
Copy-Item "config\scientific_methods\default_method.json" "config\scientific_methods\default_method.json.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# View logs
Get-Content data\veritas_auto_server.log -Tail 50
```

---

**END OF QUICK REFERENCE**

**Last Updated:** 12. Oktober 2025, 04:45 Uhr  
**Status:** ✅ Implementation Complete | ⏸️ E2E Test Pending
