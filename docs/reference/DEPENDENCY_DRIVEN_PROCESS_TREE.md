# 🌳 VERITAS Dependency-Driven Process Tree

**User Query als Wurzel | Dependency-Based Execution | Explicit Parallelization**

Vollständige Dokumentation siehe:
- `PROCESS_TREE_ARCHITECTURE.md` (8,000+ Zeilen)
- `SERVER_SIDE_PROCESSING_ARCHITECTURE.md` (6,000+ Zeilen)

---

## 🎯 Executive Summary

### Was ist neu? (dein Konzept!)

**❌ Vorher (Tree mit verschachtelten Children):**
```json
{
  "root": {
    "children": [
      {
        "step_id": "step_rag",
        "children": [
          {"step_id": "step_rag_semantic"},
          {"step_id": "step_rag_graph"}
        ]
      }
    ]
  }
}
```

**✅ Jetzt (Flat Steps mit Dependencies):**
```json
{
  "root": {
    "type": "user_query",
    "content": "Ist für meinen Carport eine Baugenehmigung nötig?"
  },
  "steps": [
    {
      "step_id": "step_nlp",
      "dependencies": [],
      "parallel_group": null
    },
    {
      "step_id": "step_rag_semantic",
      "dependencies": ["step_nlp"],
      "parallel_group": "rag_initial"
    },
    {
      "step_id": "step_rag_graph",
      "dependencies": ["step_nlp"],
      "parallel_group": "rag_initial"
    }
  ]
}
```

---

## 📊 Dependency Graph (Visuell)

```
User Query (Root): "Ist für meinen Carport eine Baugenehmigung nötig?"
    |
    v
[step_nlp] ← dependencies: []
    |
    +------------------+
    |                  |
    v                  v
[step_rag_semantic] [step_rag_graph]  ← dependencies: [step_nlp], parallel_group: "rag_initial"
    |                  |
    +--------+---------+
             |
             v
    [step_hypothesis_llm] ← dependencies: [step_rag_semantic, step_rag_graph]
             |
             v
    [step_interactive_form] ← dependencies: [step_hypothesis_llm]
             |
             +------------------+
             |                  |
             v                  v
    [step_rag_lbo]      [step_rag_process]  ← dependencies: [step_interactive_form], parallel_group: "rag_refined"
             |                  |
             +--------+---------+
                      |
                      v
              [step_evidence] ← dependencies: [step_rag_lbo, step_rag_process]
                      |
                      v
              [step_template] ← dependencies: [step_evidence, step_hypothesis_llm]
                      |
                      v
              [step_answer_llm] ← dependencies: [step_template]
                      |
                      +------------------+
                      |                  |
                      v                  v
         [step_quality_completeness] [step_quality_accuracy]  ← dependencies: [step_answer_llm], parallel_group: "quality_checks"
```

---

## 🔄 Execution Flow (Dependency-Driven)

### Algorithmus:

```python
completed_steps = set()

while len(completed_steps) < len(all_steps):
    # 1. Finde Steps, deren Dependencies erfüllt sind
    ready_steps = [step for step in all_steps
                   if all(dep in completed_steps for dep in step.dependencies)
                   and step.status == "pending"]

    # 2. Gruppiere nach parallel_group
    parallel_groups = {}
    sequential_steps = []

    for step in ready_steps:
        if step.parallel_group:
            parallel_groups.setdefault(step.parallel_group, []).append(step)
        else:
            sequential_steps.append(step)

    # 3. Starte parallele Groups
    for group_name, group_steps in parallel_groups.items():
        await asyncio.gather(*[execute_step(s) for s in group_steps])

    # 4. Starte sequentielle Steps
    for step in sequential_steps:
        await execute_step(step)

    # 5. Markiere als completed
    for step in ready_steps:
        completed_steps.add(step.step_id)
```

---

## � Beispiel Execution Timeline

```
t=0ms: Start
    ↓
t=0ms: step_nlp startet (dependencies: [] → sofort!)
    Status: pending → in_progress
    Duration: 150ms
    Status: completed ✅
    ↓
t=150ms: step_rag_semantic + step_rag_graph starten (parallel_group: "rag_initial")
    Dependencies: [step_nlp] ✅ → beide starten gleichzeitig!
    step_rag_semantic: 120ms → completed ✅ (t=270ms)
    step_rag_graph: 130ms → completed ✅ (t=280ms)
    ↓
t=280ms: step_hypothesis_llm startet
    Dependencies: [step_rag_semantic ✅, step_rag_graph ✅] → alle erfüllt!
    Duration: 600ms
    Status: completed ✅ (t=880ms)
    ↓
t=880ms: step_interactive_form startet
    Dependencies: [step_hypothesis_llm ✅]
    User Input Wait: 320ms
    Status: completed ✅ (t=1200ms)
    ↓
t=1200ms: step_rag_lbo + step_rag_process starten (parallel_group: "rag_refined")
    Dependencies: [step_interactive_form ✅] → beide starten!
    step_rag_lbo: 150ms → completed ✅ (t=1350ms)
    step_rag_process: 100ms → completed ✅ (t=1300ms)
    ↓
... (fortsetzung siehe PROCESS_TREE_ARCHITECTURE.md)
    ↓
Total: 5200ms (mit 3 parallel groups = 20% schneller als sequential)
```

---

## 🎯 Key Insights

### 1. Flat Structure > Nested Tree
- ✅ Einfacher zu serialisieren (JSON)
- ✅ Einfacher zu querien (Filter steps by type)
- ✅ Einfacher zu visualisieren (Dependency Graph)
- ✅ Kein Traversal-Code nötig

### 2. Dependencies = Explizite Beziehungen
- ✅ Step deklariert: "Ich brauche X, Y, Z"
- ✅ Executor berechnet automatisch: Wann kann ich starten?
- ✅ Keine impliziten Parent-Child Abhängigkeiten

### 3. parallel_group = Explizite Parallelisierung
- ✅ Step deklariert: "Ich kann parallel mit anderen in Gruppe X laufen"
- ✅ Executor startet alle in Gruppe gleichzeitig
- ✅ Keine manuelle asyncio.gather()-Logik in Business Code

### 4. User Query = Root
- ✅ Frage ist die Wurzel (nicht ein "Process Root Step")
- ✅ Alle Steps sind Antworten auf diese Frage
- ✅ Klare Semantik

---

## 🔧 Backend Implementation (Minimal)

### ProcessStep Class

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class ProcessStep:
    step_id: str
    step_type: str
    dependencies: List[str] = field(default_factory=list)
    parallel_group: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None
    duration_ms: Optional[int] = None
    result: Dict[str, Any] = field(default_factory=dict)

    def can_start(self, completed_steps: set) -> bool:
        """Check if all dependencies are satisfied"""
        return all(dep in completed_steps for dep in self.dependencies)
```

### ProcessExecutor Class

```python
class ProcessExecutor:
    def __init__(self, steps: List[ProcessStep]):
        self.steps = {step.step_id: step for step in steps}
        self.completed_steps = set()

    async def execute(self, step_executors: Dict[str, callable]):
        """Execute all steps respecting dependencies"""
        while len(self.completed_steps) < len(self.steps):
            # Find ready steps
            ready = [s for s in self.steps.values()
                     if s.can_start(self.completed_steps) and s.status == "pending"]

            if not ready:
                await asyncio.sleep(0.1)
                continue

            # Group by parallel_group
            parallel_groups = defaultdict(list)
            sequential = []

            for step in ready:
                if step.parallel_group:
                    parallel_groups[step.parallel_group].append(step)
                else:
                    sequential.append(step)

            # Execute parallel groups
            tasks = []
            for group_steps in parallel_groups.values():
                for step in group_steps:
                    tasks.append(self._execute_step(step, step_executors))

            # Execute sequential
            for step in sequential:
                tasks.append(self._execute_step(step, step_executors))

            # Wait for all
            await asyncio.gather(*tasks)

    async def _execute_step(self, step: ProcessStep, executors: Dict):
        step.status = "in_progress"
        step.timestamp_start = datetime.utcnow()

        # Get executor
        executor = executors[step.step_type]

        # Get dependency results
        dep_results = {dep_id: self.steps[dep_id].result
                       for dep_id in step.dependencies}

        # Execute
        result = await executor(step, dep_results)

        # Complete
        step.result = result
        step.status = "completed"
        step.timestamp_end = datetime.utcnow()
        step.duration_ms = int((step.timestamp_end - step.timestamp_start).total_seconds() * 1000)

        self.completed_steps.add(step.step_id)
```

---

## 📚 Vollständige Dokumentation

### 1. PROCESS_TREE_ARCHITECTURE.md (8,000+ Zeilen)
- ✅ Tree-Struktur mit verschachtelten Children (erste Version)
- ✅ Bottom-Up Aggregation
- ✅ Tree Traversal Algorithmen
- ✅ LLM Hauptknoten-Auswertung

### 2. SERVER_SIDE_PROCESSING_ARCHITECTURE.md (6,000+ Zeilen)
- ✅ 7-Step Pipeline Definition
- ✅ NDJSON Streaming Protocol
- ✅ Hypothesis-Driven Approach
- ✅ Quality Monitoring

### 3. DEPENDENCY_DRIVEN_PROCESS_TREE.md (dieses Dokument)
- ✅ Flat Structure mit Dependencies
- ✅ Parallel Execution Groups
- ✅ User Query als Root
- ✅ Minimal Implementation

---

## 🚀 Nächste Schritte

Was möchtest du implementieren?

### Option 1: ProcessExecutor Backend (2-3 Tage)
```bash
backend/services/
├── process_executor.py       # Dependency resolution + Execution
├── process_builder.py        # Pipeline definitions
└── step_executors.py         # Business logic (NLP, RAG, LLM, etc.)
```

### Option 2: Process Builder (Pipeline Definitions) (1-2 Tage)
```python
builder = ProcessBuilder(user_query)
steps = builder.build_standard_pipeline()
# Automatisch: NLP → RAG (parallel) → Hypothesis → Form → ...
```

### Option 3: Frontend Dependency Graph (2-3 Tage)
```javascript
// vis.js network graph
// Real-time status updates (pending → in_progress → completed)
// Interactive step details on click
```

### Option 4: Conditional Steps (Advanced) (1-2 Tage)
```python
# Hypothesis detektiert missing_info → step_interactive_form wird hinzugefügt
# Quality check fails → step_answer_regeneration wird hinzugefügt
# Dynamische Pipeline-Erweiterung während Execution
```

Was bevorzugst du? 🎯
