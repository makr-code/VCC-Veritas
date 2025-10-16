# NÄCHSTER TODO-PUNKT - Empfehlung 🎯

**Datum:** 14. Oktober 2025, 09:05 Uhr  
**Basis:** IMPLEMENTATION_GAP_ANALYSIS_TODO.md  
**Aktueller Status:** Phase 2 Complete (Streaming funktioniert!)

---

## 🎯 EMPFEHLUNG: Phase 1 - Foundation (NLP + Process Building)

### Warum Phase 1?

**Gründe:**
1. ✅ **Streaming läuft** - Backend ist bereit für neue Features
2. ✅ **DependencyResolver existiert** - 80% der Basis vorhanden
3. ✅ **Schneller Erfolg** - Foundation in 2-3 Tagen machbar
4. ✅ **Blockt nichts** - Kann parallel zu Frontend-Tests laufen

**Was Phase 1 bringt:**
- User Query → Automatische Process Steps
- NLP-basierte Intent Detection
- Dependency Resolution (bereits da!)
- Process Tree Execution

---

## 📋 Phase 1: Foundation - Detailed Breakdown

### 1.1: NLPService (~300 LOC, 6-8h) 🟢 START HIER!

**File:** `backend/services/nlp_service.py`

**Features:**
```python
class NLPService:
    def extract_entities(self, query: str) -> List[Entity]
    def detect_intent(self, query: str) -> Intent
    def extract_parameters(self, query: str) -> Dict[str, Any]
    def classify_question_type(self, query: str) -> str
```

**Warum zuerst?**
- Keine Dependencies auf andere neue Komponenten
- Nutzt nur Standard-Python (regex, string operations)
- Sofort testbar
- Optional: spaCy integration später

**Test Query Examples:**
```python
"Was ist der Hauptsitz von BMW?"
→ Intent: fact_retrieval
→ Entities: ["BMW"]
→ Type: factual_question

"Bauantrag für Einfamilienhaus in Stuttgart"
→ Intent: procedure_query
→ Entities: ["Stuttgart", "Einfamilienhaus"]
→ Type: process_question
```

**Estimated Time:** 6-8 Stunden (1 Tag)

---

### 1.2: ProcessBuilder (~150 LOC, 4-6h) 🟡 DANACH

**File:** `backend/services/process_builder.py`

**Features:**
```python
class ProcessBuilder:
    def __init__(self, nlp_service: NLPService)
    
    def build_process_tree(self, query: str) -> ProcessTree:
        """Converts user query → ProcessTree with steps + dependencies"""
        
    def _infer_steps(self, intent: Intent, entities: List[Entity]) -> List[ProcessStep]
    def _infer_dependencies(self, steps: List[ProcessStep]) -> Dict[str, List[str]]
```

**Dependencies:**
- ✅ Needs NLPService (1.1)
- ✅ Needs DependencyResolver (existiert!)

**Example Output:**
```python
Query: "Bauantrag Stuttgart - welche Unterlagen?"

ProcessTree:
  steps:
    - id: "search_regulations"
      name: "Suche Bauvorschriften Stuttgart"
      dependencies: []
      
    - id: "search_forms"
      name: "Suche Antragsformulare"
      dependencies: []
      
    - id: "compile_checklist"
      name: "Erstelle Unterlagen-Checkliste"
      dependencies: ["search_regulations", "search_forms"]
```

**Estimated Time:** 4-6 Stunden

---

### 1.3: ProcessExecutor (~200 LOC, 6-8h) 🟡 PARALLEL MÖGLICH

**File:** `backend/services/process_executor.py`

**Features:**
```python
class ProcessExecutor:
    def __init__(self, dependency_resolver: DependencyResolver)
    
    def execute_process(self, process: ProcessTree) -> ProcessResult:
        """Executes process with parallel execution where possible"""
        
    def _execute_parallel_group(self, step_ids: List[str]) -> Dict[str, StepResult]
    def _aggregate_results(self, results: Dict[str, StepResult]) -> ProcessResult
```

**Dependencies:**
- ✅ Needs DependencyResolver (existiert!)
- ✅ ProcessTree model (simple dataclass)

**Key Feature:**
- Nutzt existing `DependencyResolver.get_execution_plan()` für parallele Gruppen!

**Estimated Time:** 6-8 Stunden

---

### 1.4: Data Models (~200 LOC, 3-4h) 🟢 EINFACH

**Files:**
- `backend/models/process_step.py`
- `backend/models/process_tree.py`
- `backend/models/nlp_models.py`

**Content:**
```python
@dataclass
class ProcessStep:
    id: str
    name: str
    description: str
    dependencies: List[str]
    parameters: Dict[str, Any]
    step_type: str

@dataclass
class ProcessTree:
    query: str
    steps: List[ProcessStep]
    execution_plan: List[List[str]]  # Parallel groups

@dataclass
class Entity:
    text: str
    type: str  # location, organization, person, etc.
    
@dataclass
class Intent:
    type: str  # fact_retrieval, procedure_query, etc.
    confidence: float
```

**Estimated Time:** 3-4 Stunden

---

### 1.5: Unit Tests (~300 LOC, 6-8h) 🔴 WICHTIG

**Files:**
- `tests/test_nlp_service.py`
- `tests/test_process_builder.py`
- `tests/test_process_executor.py`

**Test Cases:**
```python
# test_nlp_service.py
def test_entity_extraction():
    nlp = NLPService()
    entities = nlp.extract_entities("BMW in München")
    assert len(entities) == 2
    assert entities[0].text == "BMW"
    assert entities[1].text == "München"

# test_process_builder.py
def test_build_process_tree():
    builder = ProcessBuilder(nlp_service)
    tree = builder.build_process_tree("Bauantrag Stuttgart")
    assert len(tree.steps) >= 2
    assert tree.execution_plan  # Has parallel groups

# test_process_executor.py
def test_execute_parallel_steps():
    executor = ProcessExecutor(dependency_resolver)
    result = executor.execute_process(process_tree)
    assert result.success
    assert len(result.step_results) == len(process_tree.steps)
```

**Estimated Time:** 6-8 Stunden

---

## 📊 Phase 1 Summary

### Total Effort:
```
1.1 NLPService:        6-8h   (1 Tag)
1.2 ProcessBuilder:    4-6h   (0.5 Tag)
1.3 ProcessExecutor:   6-8h   (1 Tag)
1.4 Data Models:       3-4h   (0.5 Tag)
1.5 Unit Tests:        6-8h   (1 Tag)
────────────────────────────────────
TOTAL:                 25-34h (2-3 Tage)
```

### Files Created:
```
backend/services/
  ├─ nlp_service.py           (~300 LOC)
  ├─ process_builder.py       (~150 LOC)
  └─ process_executor.py      (~200 LOC)

backend/models/
  ├─ process_step.py          (~50 LOC)
  ├─ process_tree.py          (~50 LOC)
  └─ nlp_models.py            (~100 LOC)

tests/
  ├─ test_nlp_service.py      (~100 LOC)
  ├─ test_process_builder.py  (~100 LOC)
  └─ test_process_executor.py (~100 LOC)

TOTAL: ~1,150 LOC
```

---

## 🚀 Implementation Order (Recommended)

### Day 1: NLP Foundation (8h)
**Morning (4h):**
1. Create `backend/models/nlp_models.py` (1h)
   - Entity, Intent dataclasses
2. Create `backend/services/nlp_service.py` skeleton (1h)
   - Class structure, method signatures
3. Implement `extract_entities()` (2h)
   - Regex-based entity extraction
   - Location, organization, person detection

**Afternoon (4h):**
4. Implement `detect_intent()` (2h)
   - Keyword-based intent classification
   - 5 intent types: fact_retrieval, procedure_query, comparison, timeline, calculation
5. Write `tests/test_nlp_service.py` (2h)
   - 10+ test cases
   - Run tests, fix issues

**End of Day 1:** ✅ NLPService working + tested

---

### Day 2: Process Building (8h)
**Morning (4h):**
1. Create `backend/models/process_step.py` + `process_tree.py` (1h)
2. Create `backend/services/process_builder.py` (3h)
   - Implement `build_process_tree()`
   - Implement `_infer_steps()`
   - Implement `_infer_dependencies()`

**Afternoon (4h):**
3. Write `tests/test_process_builder.py` (2h)
   - Test with 5 example queries
4. Create `backend/services/process_executor.py` (2h)
   - Implement `execute_process()`
   - Wrap DependencyResolver

**End of Day 2:** ✅ ProcessBuilder + Executor working

---

### Day 3: Integration + Polish (6-8h)
**Morning (3-4h):**
1. Write `tests/test_process_executor.py` (2h)
2. End-to-end test (1-2h)
   - Query → NLP → Builder → Executor → Result

**Afternoon (3-4h):**
3. Documentation (2h)
   - `docs/PHASE1_COMPLETE.md`
   - Code docstrings
4. Code review + cleanup (1-2h)
   - Type hints
   - Linting
   - Error handling

**End of Day 3:** ✅ Phase 1 COMPLETE!

---

## 🎯 Success Criteria

### Must Have:
- [x] NLPService extracts entities from queries
- [x] NLPService detects intents (5 types minimum)
- [x] ProcessBuilder creates ProcessTree from query
- [x] ProcessExecutor executes steps with dependencies
- [x] Unit tests pass (>80% coverage)

### Nice to Have:
- [ ] spaCy integration for advanced NLP
- [ ] Caching for repeated queries
- [ ] Performance benchmarks

---

## 🔄 Alternative: Quick Win Option

### Falls Phase 1 zu groß:

**Option A: Mini-Phase 1A (1 Tag, 6-8h)**
- Nur NLPService + Tests
- **Benefit:** Sofort nutzbar für Query-Analyse
- **Next:** ProcessBuilder in separater Session

**Option B: Prototype First (4h)**
- Hardcoded Process Trees (no NLP)
- Test ProcessExecutor mit existing DependencyResolver
- **Benefit:** Validate execution logic schnell

---

## 📝 Next Steps

### Option 1: Start Phase 1 (Empfohlen) ✅
```powershell
# Create branch
git checkout -b feature/phase1-foundation

# Create directory structure
mkdir backend\services
mkdir backend\models
mkdir tests\services

# Start with NLPService
# → File: backend\services\nlp_service.py
```

### Option 2: Test Existing DependencyResolver First (1h)
```powershell
# Verify DependencyResolver works
python -c "from backend.agents.framework.dependency_resolver import DependencyResolver; print('OK')"

# Run example
python tests/test_dependency_resolver.py
```

### Option 3: Review Design Docs (30 min)
```powershell
# Read architecture
cat docs\DEPENDENCY_DRIVEN_PROCESS_TREE.md
cat docs\SERVER_SIDE_PROCESSING_ARCHITECTURE.md
```

---

## 🎉 Why Phase 1 Now?

**Perfect Timing:**
1. ✅ Streaming works (Phase 2 done)
2. ✅ Backend stable
3. ✅ DependencyResolver ready
4. ✅ Clear design documents
5. ✅ No blocking dependencies

**Value:**
- Foundation for all future phases
- Immediate value (Query → Process Trees)
- Builds on existing code (80% reuse!)

**Risk:**
- 🟢 LOW - No external dependencies
- 🟢 LOW - Small scope (3 days)
- 🟢 LOW - Well-documented

---

## ❓ Fragen zum Starten?

1. **Soll ich mit Phase 1 starten?** → NLPService first (6-8h)
2. **Oder lieber Mini-Prototype?** → Hardcoded Process Trees (4h)
3. **Oder etwas anderes?** → Siehe TODO andere Phases

**Meine Empfehlung:** 🎯 **START MIT PHASE 1.1 (NLPService)**

---

**Status:** ✅ READY TO START!  
**Nächster Schritt:** Create `backend/services/nlp_service.py`  
**Estimated Time:** 2-3 Tage bis Phase 1 Complete

---

**Version:** 1.0  
**Erstellt:** 14. Oktober 2025, 09:10 Uhr  
**Basis:** IMPLEMENTATION_GAP_ANALYSIS_TODO.md  
**Recommendation:** Phase 1 Foundation ✅
