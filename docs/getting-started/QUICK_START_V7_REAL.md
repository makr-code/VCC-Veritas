# VERITAS v7.0 - Quick Start Guide (Real Systems)

**Version:** v7.0 Phase 4 Complete
**Date:** 13. Oktober 2025
**Status:** ✅ Ready for Real Testing

---

## 🚀 Quick Start

### Prerequisites

**1. UDS3 Database Running**
- ChromaDB: http://192.168.178.94:8000 ✅
- Neo4j: bolt://192.168.178.94:7687 ✅
- PostgreSQL: 192.168.178.94:5432 ✅

**2. Ollama Server Running**
- URL: http://localhost:11434 ✅
- Model: llama3.2:latest installed

**3. Python Dependencies**
```bash
pip install httpx jsonschema jinja2 asyncio
```

---

## ▶️ Run End-to-End Test

### Option 1: Full Test Suite (Recommended)

```powershell
cd C:\VCC\veritas
python tests\test_unified_orchestrator_v7_real.py
```

**Expected Output:**
```
🧪 VERITAS v7.0 - End-to-End Test Suite
================================================================================

📋 Test 1: Streaming Mode
⏳ Progress: 10% - Query Enhancement
🔍 UDS3 Hybrid Search: Brauche ich eine Baugenehmigung für...
✅ UDS3 Search: 10 total (7 vector, 3 graph)
🤖 LLM call attempt 1/3: phase=phase1_hypothesis, model=llama3.2
✅ Ollama response received: 1243 chars, duration=2341ms
✅ Phase Complete: phase1_hypothesis | Status: success | Confidence: 0.85
...
🎯 FINAL RESULT
Main Answer: Nach § 50 LBO BW sind Garagen und überdachte Stellplätze...
Confidence: 0.78
Total Execution Time: 42300ms (42.3s)

📊 TEST SUMMARY
Total Events: 27
  - progress: 10
  - processing_step: 10
  - phase_complete: 6
  - final_result: 1

✅ VALIDATION CHECKS
✅ PASS: All 6 phases executed
✅ PASS: Final result received
✅ PASS: No errors
✅ PASS: All phases successful
✅ PASS: Confidence > 0.5

🎉 TEST PASSED - All validation checks successful!
```

**Duration:** ~45-60 seconds (6 LLM calls)

### Option 2: Interactive Python REPL

```python
import asyncio
from backend.orchestration.unified_orchestrator_v7 import UnifiedOrchestratorV7
from backend.agents.veritas_ollama_client import VeritasOllamaClient

async def test():
    # Initialize
    ollama = VeritasOllamaClient(base_url="http://localhost:11434")
    await ollama.initialize()

    orchestrator = UnifiedOrchestratorV7(
        ollama_client=ollama,
        uds3_strategy=None  # Auto-init
    )

    # Process query
    async for event in orchestrator.process_query_stream(
        query="Brauche ich Baugenehmigung für Carport in BW?"
    ):
        if event.type == "final_result":
            print(f"Answer: {event.data['final_answer']['main_answer']}")

    await ollama.close()

asyncio.run(test())
```

---

## 🔍 What Gets Tested?

### Real System Integration

**1. UDS3 Hybrid Search** ✅
- ChromaDB Vector Search (semantic similarity)
- Neo4j Graph Search (relationships)
- Weighted combination (60% vector, 40% graph)
- Top 10 results returned

**2. Ollama LLM Calls (6 Phases)** ✅
- Phase 1: Hypothesis Generation (800 tokens, temp 0.3)
- Phase 2: Evidence Synthesis (1200 tokens, temp 0.2)
- Phase 3: Pattern Analysis (1000 tokens, temp 0.25)
- Phase 4: Validation (900 tokens, temp 0.2)
- Phase 5: Conclusion (1000 tokens, temp 0.15)
- Phase 6: Metacognition (800 tokens, temp 0.3)

**3. JSON Schema Validation** ✅
- All 6 phase outputs validated against schemas
- Partial results on validation errors
- Validation errors logged

**4. Streaming Events** ✅
- 10 progress events (0% → 100%)
- 10 processing_step events (query_enhancement, rag_search, phase1-6, final_answer)
- 6 phase_complete events (with confidence, execution_time)
- 1 final_result event

---

## 📊 Performance Expectations

### Execution Times

| Component | Expected | Typical |
|-----------|----------|---------|
| UDS3 Hybrid Search | <5s | 2-3s |
| Phase 1 (Hypothesis) | <10s | 5-8s |
| Phase 2 (Synthesis) | <15s | 8-12s |
| Phase 3 (Analysis) | <10s | 6-9s |
| Phase 4 (Validation) | <10s | 6-8s |
| Phase 5 (Conclusion) | <10s | 6-9s |
| Phase 6 (Metacognition) | <10s | 5-7s |
| **Total** | **<60s** | **40-50s** |

### Confidence Scores

| Phase | Expected | Interpretation |
|-------|----------|----------------|
| Hypothesis | 0.6-0.8 | Conservative (missing user input) |
| Synthesis | 0.7-0.9 | High (clear evidence clusters) |
| Analysis | 0.7-0.9 | High (strong patterns) |
| Validation | 0.8-0.95 | Very High (confirmed by VwV) |
| Conclusion | 0.7-0.85 | High (weighted average) |
| Final | 0.7-0.85 | High (overall) |

---

## ✅ Validation Checklist

### Before Running Test

- [ ] UDS3 Databases running (ChromaDB, Neo4j, PostgreSQL)
- [ ] Ollama Server running (localhost:11434)
- [ ] llama3.2 model installed (`ollama pull llama3.2`)
- [ ] Python dependencies installed
- [ ] Working directory: `C:\VCC\veritas`

### After Test Completion

**Expected Results:**
- [ ] All 6 phases executed successfully
- [ ] Final result received (main_answer not empty)
- [ ] No error events
- [ ] All phases status: 'success' or 'partial'
- [ ] All confidence scores > 0.5
- [ ] UDS3 search returned real results (not mock data)
- [ ] Ollama responses coherent (not mock JSON)
- [ ] Total execution time < 60s

**If Any Check Fails:**
1. Check logs for error messages (❌ indicator)
2. Verify UDS3 connection (🔍 search logs)
3. Verify Ollama connection (🤖 LLM logs)
4. Check JSON schema validation errors
5. Review phase-specific issues

---

## 🐛 Troubleshooting

### Common Issues

**Issue 1: UDS3 Connection Failed**
```
⚠️ UDS3 not available - using mock RAG
```

**Solution:**
- Check UDS3 databases are running
- Verify network connection to 192.168.178.94
- Check `uds3/` directory exists at `C:\VCC\uds3`

**Issue 2: Ollama Not Responding**
```
❌ LLM call failed: Connection refused
```

**Solution:**
```powershell
# Start Ollama server
ollama serve

# Verify model installed
ollama list
# Should show: llama3.2:latest

# Pull model if missing
ollama pull llama3.2
```

**Issue 3: Validation Errors**
```
⚠️ Schema validation failed: 'required_criteria' is required
```

**Solution:**
- This is expected occasionally (LLM output variations)
- Status becomes 'partial' instead of 'success'
- Final answer still generated
- Check if confidence > 0.5 (acceptable)

**Issue 4: Timeout**
```
RuntimeError: LLM call failed nach 3 Versuchen
```

**Solution:**
- Increase timeout in test: `VeritasOllamaClient(timeout=120)`
- Check Ollama server load (`ollama ps`)
- Reduce max_tokens in phase configs

---

## 📝 Test Queries

### Basic Queries (Start Here)
```
"Brauche ich eine Baugenehmigung für einen Carport in Baden-Württemberg?"
"Wie groß darf ein Carport ohne Baugenehmigung sein?"
"Was sind die Voraussetzungen für ein verfahrensfreies Vorhaben?"
```

### Advanced Queries
```
"Photovoltaikanlage auf Carport - Baugenehmigung in BW?"
"Grenzbebauung bei Carport in Baden-Württemberg"
"Carport 40m² - welche Genehmigung brauche ich?"
```

### Edge Cases
```
"Brauche ich eine Baugenehmigung?" (ambiguous)
"Was ist der beste Carport-Typ?" (non-legal)
"§ 50 LBO BW Auslegung" (very specific)
```

---

## 🎯 Next Steps After Successful Test

### 1. Analyze Results (15 min)
- Review phase execution times
- Check confidence distributions
- Identify slowest phases
- Review validation errors

### 2. Tune Prompts (1-2 hours)
Based on real outputs:
- Adjust system prompts
- Tune temperature values
- Refine quality guidelines
- Optimize max_tokens

### 3. Edge Case Testing (1 hour)
Test with:
- Ambiguous queries
- Missing information
- Multi-aspect queries
- Non-legal queries

### 4. Production Deployment (Optional)
- Create FastAPI endpoints
- Add WebSocket streaming
- Integrate with frontend
- Setup monitoring (Prometheus)

---

## 📚 Additional Resources

**Documentation:**
- `docs/PHASE4_REAL_INTEGRATION_REPORT.md` - Complete integration details
- `docs/V7_IMPLEMENTATION_TODO.md` - Overall progress
- `config/scientific_methods/default_method.json` - Phase configurations
- `config/prompts/scientific/` - Prompt templates

**Code:**
- `backend/orchestration/unified_orchestrator_v7.py` - Main orchestrator
- `backend/services/scientific_phase_executor.py` - Phase executor
- `backend/agents/veritas_uds3_hybrid_agent.py` - UDS3 search
- `backend/agents/veritas_ollama_client.py` - Ollama client

**Tests:**
- `tests/test_unified_orchestrator_v7.py` - Mock test (27 events, 38ms)
- `tests/test_unified_orchestrator_v7_real.py` - Real test (this guide)

---

## 🎉 Success!

**If all checks pass:**
```
🎉 ALL TESTS PASSED - v7.0 PRODUCTION READY!
```

**What this means:**
- ✅ Real UDS3 integration working
- ✅ Real Ollama integration working
- ✅ All 6 scientific phases executing
- ✅ JSON validation passing
- ✅ Streaming events working
- ✅ System ready for production deployment

**Congratulations!** 🎊

You've successfully validated VERITAS v7.0 with real systems!

---

**Questions?**
- Check logs for detailed execution trace
- Review `PHASE4_REAL_INTEGRATION_REPORT.md`
- Test with simpler queries first
- Verify all prerequisites above

**Happy Testing!** 🚀
