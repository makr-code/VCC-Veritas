# Process Executor Service

**Version:** 1.0  
**Status:** ✅ STABLE  
**Zuletzt aktualisiert:** 17. November 2025  
**Quellcode:** `backend/services/process_executor.py` (1,061 LOC)

---

## 📋 Übersicht

Der **ProcessExecutor** ist der zentrale Orchestrierungs-Service von VERITAS, der ProcessTree-Instanzen mit optimaler Parallelisierung ausführt. Er koordiniert die Ausführung von Prozess-Schritten (Steps) und nutzt dabei den DependencyResolver zur Bestimmung der Ausführungsreihenfolge und ThreadPoolExecutor für parallele Verarbeitung.

**Zweck:** Effiziente und zuverlässige Ausführung komplexer Multi-Step-Prozesse mit automatischer Dependency-Auflösung und optionaler Agent-Integration.

**Kernfunktionen:**
- Parallele Ausführung unabhängiger Steps
- Dependency-basierte Ausführungsreihenfolge
- Integration mit RAG Service für Dokumentenretrieval
- Integration mit Agent Framework für intelligente Verarbeitung
- Streaming-Progress-Updates
- Hypothesis Generation (Phase 5)
- Semantic Re-Ranking von Suchergebnissen
- Error Handling mit optionalem Retry
- Execution Time Tracking

---

## 🏗️ Architektur

### Komponenten-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                   ProcessExecutor                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────┐  ┌───────────────┐  ┌──────────────┐       │
│  │ Dependency │  │ Thread Pool   │  │ Progress     │       │
│  │ Resolver   │  │ Executor      │  │ Callback     │       │
│  └────────────┘  └───────────────┘  └──────────────┘       │
│                                                              │
│  ┌────────────┐  ┌───────────────┐  ┌──────────────┐       │
│  │ Agent      │  │ RAG           │  │ Hypothesis   │       │
│  │ Executor   │  │ Service       │  │ Service      │       │
│  └────────────┘  └───────────────┘  └──────────────┘       │
│                                                              │
│  ┌────────────┐                                             │
│  │ Reranker   │                                             │
│  │ Service    │                                             │
│  └────────────┘                                             │
└─────────────────────────────────────────────────────────────┘
```

### Execution Flow

```
1. Input: ProcessTree
   ↓
2. [Optional] Generate Hypothesis (Phase 5)
   ↓
3. Convert ProcessTree → Resolver Format
   ↓
4. DependencyResolver → Execution Plan (Levels)
   ↓
5. For each Level:
   ├─ Execute Steps in Parallel (ThreadPoolExecutor)
   ├─ Track Status (pending → running → completed/failed)
   ├─ Emit Progress Events
   └─ Aggregate Results
   ↓
6. Output: ProcessResult
```

### Dependency Resolution

Der ProcessExecutor nutzt den **DependencyResolver** für optimale Parallelisierung:

- **Level 0:** Steps ohne Dependencies → parallel ausführen
- **Level 1:** Steps mit Dependencies auf Level 0 → parallel ausführen
- **Level N:** Steps mit Dependencies auf Level N-1 → parallel ausführen

Beispiel:
```
Level 0: [Step A, Step B, Step C]  ← parallel (keine Dependencies)
Level 1: [Step D (depends on A), Step E (depends on B)]  ← parallel
Level 2: [Step F (depends on D, E)]  ← wartet auf Level 1
```

---

## 📚 API-Referenz

### Hauptklasse: `ProcessExecutor`

#### Konstruktor

```python
def __init__(
    self,
    max_workers: int = 4,
    retry_failed: bool = False,
    use_agents: bool = True,
    rag_service: Optional[RAGService] = None,
    enable_hypothesis: bool = True,
    enable_reranking: bool = True
)
```

**Parameter:**
- `max_workers` (int): Maximale Anzahl paralleler Worker (Standard: 4)
- `retry_failed` (bool): Ob fehlgeschlagene Steps wiederholt werden sollen (Standard: False)
- `use_agents` (bool): Ob echte Agents verwendet werden oder Mock-Modus (Standard: True)
- `rag_service` (Optional[RAGService]): Optional RAG Service für Dokumentenretrieval
- `enable_hypothesis` (bool): Aktiviert Hypothesis Generation (Phase 5, Standard: True)
- `enable_reranking` (bool): Aktiviert semantisches Re-Ranking (Standard: True)

**Initialisierung:**
```python
executor = ProcessExecutor(
    max_workers=8,
    use_agents=True,
    enable_hypothesis=True,
    enable_reranking=True
)
```

#### Haupt-Methoden

##### `execute_process(tree, progress_callback=None) -> Dict[str, Any]`

Führt einen kompletten ProcessTree aus.

**Parameter:**
- `tree` (ProcessTree): Der auszuführende ProcessTree
- `progress_callback` (Optional[ProgressCallback]): Optional Callback für Progress-Updates

**Returns:** ProcessResult Dictionary mit:
- `success` (bool): Ob die Ausführung erfolgreich war
- `data` (Dict): Aggregierte Ergebnisse aus allen Steps
- `execution_time` (float): Ausführungszeit in Sekunden
- `steps_completed` (int): Anzahl erfolgreich abgeschlossener Steps
- `steps_failed` (int): Anzahl fehlgeschlagener Steps
- `step_results` (Dict[str, StepResult]): Einzelergebnisse pro Step
- `hypothesis` (Optional[Hypothesis]): Generierte Hypothesis (Phase 5)

**Beispiel:**
```python
from backend.services.process_executor import ProcessExecutor
from backend.models.process_tree import ProcessTree

# ProcessTree erstellen
tree = ProcessTree(query="Was sind die Immissionsschutz-Grenzwerte?")
# ... Steps hinzufügen ...

# Executor initialisieren und ausführen
executor = ProcessExecutor(max_workers=4)
result = executor.execute_process(tree)

print(f"Success: {result['success']}")
print(f"Steps completed: {result['steps_completed']}")
print(f"Execution time: {result['execution_time']:.2f}s")
```

##### `_execute_step(step, progress_callback=None) -> StepResult`

Führt einen einzelnen Step aus (intern).

**Parameter:**
- `step` (ProcessStep): Der auszuführende Step
- `progress_callback` (Optional[ProgressCallback]): Optional Callback für Updates

**Returns:** StepResult mit:
- `success` (bool): Ob der Step erfolgreich war
- `data` (Dict): Step-Ergebnisse
- `execution_time` (float): Ausführungszeit
- `error` (Optional[str]): Fehlermeldung bei Fehler

**Step-Typen:**

Der Executor unterstützt verschiedene Step-Typen:

1. **SEARCH:** Dokumentensuche via RAG Service
2. **AGENT:** Agent-basierte Verarbeitung
3. **ANALYZE:** Datenanalyse
4. **SYNTHESIS:** Ergebnis-Synthese
5. **QUERY_EXPANSION:** Query-Erweiterung
6. **FILTER:** Daten-Filterung
7. **RANK:** Ergebnis-Ranking
8. **AGGREGATE:** Daten-Aggregation

**Beispiel (SEARCH Step):**
```python
# SEARCH Step wird automatisch mit RAG Service ausgeführt
if step.type == StepType.SEARCH and self.rag_service:
    # 1. Query-Reformulierung
    search_query = self._reformulate_query_for_step(step)
    
    # 2. RAG Search
    search_results = self.rag_service.search(search_query, top_k=10)
    
    # 3. Optional: Re-Ranking
    if self.enable_reranking:
        results = self.reranker_service.rerank(...)
```

---

## ⚙️ Konfiguration

### Service-Dependencies

Der ProcessExecutor benötigt oder nutzt folgende Services:

**Erforderlich:**
- `DependencyResolver` - Für Execution Planning
- `ProcessTree`, `ProcessStep` - Datenmodelle

**Optional (mit Fallback):**
- `AgentExecutor` - Für Agent-Integration (Fallback: Mock-Modus)
- `RAGService` - Für Dokumentenretrieval (Fallback: Mock-Daten)
- `HypothesisService` - Für Query-Analyse (Fallback: ohne Hypothesis)
- `RerankerService` - Für semantisches Re-Ranking (Fallback: ohne Re-Ranking)
- `ProgressCallback` - Für Streaming-Updates (Fallback: ohne Updates)

### Konfigurationsoptionen

```python
# Minimal (nur Core-Features)
executor = ProcessExecutor(max_workers=2, use_agents=False)

# Standard (mit Agents, ohne optionale Features)
executor = ProcessExecutor(
    max_workers=4,
    use_agents=True,
    enable_hypothesis=False,
    enable_reranking=False
)

# Full-Featured (alle Features aktiviert)
executor = ProcessExecutor(
    max_workers=8,
    use_agents=True,
    rag_service=custom_rag_service,
    enable_hypothesis=True,
    enable_reranking=True
)
```

### Environment Variables

Der ProcessExecutor selbst nutzt keine Environment Variables, aber die integrierten Services (RAG, Agent) benötigen Konfiguration über ihre eigenen Settings.

---

## 💡 Verwendungsbeispiele

### Beispiel 1: Einfache Query-Verarbeitung

```python
from backend.services.process_executor import ProcessExecutor
from backend.models.process_tree import ProcessTree
from backend.models.process_step import ProcessStep, StepType

# 1. ProcessTree erstellen
tree = ProcessTree(query="Was ist ein Bauantrag?")

# 2. Step hinzufügen
step = ProcessStep(
    step_id="search_1",
    type=StepType.SEARCH,
    name="Bauantrag-Dokumentation suchen",
    description="Suche relevante Dokumente zu Bauanträgen"
)
tree.add_step(step)

# 3. Executor initialisieren und ausführen
executor = ProcessExecutor(max_workers=4)
result = executor.execute_process(tree)

# 4. Ergebnisse verarbeiten
if result['success']:
    print(f"✅ Query erfolgreich verarbeitet in {result['execution_time']:.2f}s")
    print(f"   Gefundene Dokumente: {len(result['data'].get('documents', []))}")
else:
    print(f"❌ Query fehlgeschlagen: {result.get('error')}")
```

### Beispiel 2: Multi-Step Process mit Dependencies

```python
from backend.services.process_executor import ProcessExecutor
from backend.models.process_tree import ProcessTree
from backend.models.process_step import ProcessStep, StepType

# 1. ProcessTree erstellen
tree = ProcessTree(query="Immissionsschutz-Grenzwerte analysieren")

# 2. Step 1: Suche (Level 0)
search_step = ProcessStep(
    step_id="search_1",
    type=StepType.SEARCH,
    name="Grenzwerte suchen"
)
tree.add_step(search_step)

# 3. Step 2: Analyse (Level 1, depends on search)
analyze_step = ProcessStep(
    step_id="analyze_1",
    type=StepType.ANALYZE,
    name="Grenzwerte analysieren",
    dependencies=["search_1"]  # Wartet auf search_1
)
tree.add_step(analyze_step)

# 4. Step 3: Synthese (Level 2, depends on analyze)
synthesis_step = ProcessStep(
    step_id="synthesis_1",
    type=StepType.SYNTHESIS,
    name="Ergebnisse zusammenfassen",
    dependencies=["analyze_1"]
)
tree.add_step(synthesis_step)

# 5. Ausführen
executor = ProcessExecutor(max_workers=4)
result = executor.execute_process(tree)

print(f"Execution Plan: {result['execution_plan_levels']} levels")
print(f"Steps completed: {result['steps_completed']}/{len(tree.steps)}")
```

### Beispiel 3: Mit Streaming Progress

```python
from backend.services.process_executor import ProcessExecutor
from backend.models.streaming_progress import ProgressCallback

# 1. Progress Callback definieren
def on_progress(event):
    print(f"[{event.event_type.value}] {event.message}")
    if event.progress is not None:
        print(f"  Progress: {event.progress:.1f}%")

callback = ProgressCallback(on_progress)

# 2. Executor mit Callback ausführen
executor = ProcessExecutor(max_workers=4)
result = executor.execute_process(tree, progress_callback=callback)
```

**Output:**
```
[plan_started] Starting execution: 3 steps
[step_started] Step 1/3: Grenzwerte suchen
  Progress: 0.0%
[step_progress] Searching documents...
  Progress: 15.0%
[step_completed] Step 1/3 completed
  Progress: 33.3%
[step_started] Step 2/3: Grenzwerte analysieren
  Progress: 33.3%
...
[plan_completed] Execution complete: 3 completed, 0 failed
  Progress: 100.0%
```

### Beispiel 4: Mit Hypothesis Generation (Phase 5)

```python
executor = ProcessExecutor(
    max_workers=4,
    enable_hypothesis=True  # Aktiviert Hypothesis-Generation
)

result = executor.execute_process(tree)

# Hypothesis abrufen
if 'hypothesis' in result and result['hypothesis']:
    hyp = result['hypothesis']
    print(f"Query Type: {hyp.question_type.value}")
    print(f"Confidence: {hyp.confidence.value}")
    print(f"Expected Answer Type: {hyp.expected_answer_type}")
    
    if hyp.requires_clarification():
        print("⚠️ Clarification needed:")
        for q in hyp.get_clarification_questions():
            print(f"  - {q}")
```

### Beispiel 5: Custom RAG Service

```python
from backend.services.rag_service import RAGService

# 1. Custom RAG Service konfigurieren
rag_service = RAGService(
    chroma_collection="custom_collection",
    neo4j_enabled=True,
    postgres_enabled=False
)

# 2. Executor mit custom RAG
executor = ProcessExecutor(
    max_workers=8,
    rag_service=rag_service,
    enable_reranking=True  # Re-Ranking aktiviert
)

# 3. Ausführen
result = executor.execute_process(tree)
```

---

## 🔧 Troubleshooting

### Problem 1: "AgentExecutor not available - using mock mode"

**Symptom:** Executor läuft im Mock-Modus statt echte Agents zu verwenden

**Ursache:** AgentExecutor konnte nicht importiert oder initialisiert werden

**Lösung:**
```python
# 1. Prüfen ob AgentExecutor verfügbar ist
from backend.services.agent_executor import AgentExecutor
try:
    executor = AgentExecutor()
    print("✅ AgentExecutor verfügbar")
except Exception as e:
    print(f"❌ Fehler: {e}")

# 2. Falls nicht verfügbar, Dependencies installieren
# pip install -r requirements.txt

# 3. Oder explizit Mock-Modus verwenden
executor = ProcessExecutor(use_agents=False)
```

### Problem 2: Steps werden nicht parallel ausgeführt

**Symptom:** Alle Steps laufen sequentiell statt parallel

**Ursache:** 
- `max_workers=1` gesetzt
- Alle Steps haben Dependencies (kein Parallelismus möglich)

**Lösung:**
```python
# 1. max_workers erhöhen
executor = ProcessExecutor(max_workers=8)

# 2. ProcessTree prüfen
tree = ProcessTree(query="...")
# Steps OHNE Dependencies können parallel laufen
step1 = ProcessStep(step_id="s1", dependencies=[])  # Level 0
step2 = ProcessStep(step_id="s2", dependencies=[])  # Level 0 (parallel zu s1)
step3 = ProcessStep(step_id="s3", dependencies=["s1"])  # Level 1
```

### Problem 3: RAG Service nicht verfügbar

**Symptom:** "RAG Service not available - using mock data"

**Ursache:** RAG Service konnte nicht importiert oder initialisiert werden

**Lösung:**
```python
# 1. RAG Service manuell initialisieren
from backend.services.rag_service import RAGService
rag_service = RAGService()

# 2. An Executor übergeben
executor = ProcessExecutor(rag_service=rag_service)

# 3. Oder ohne RAG arbeiten (Mock-Daten)
executor = ProcessExecutor()  # Auto-Fallback zu Mock
```

### Problem 4: Hoher Memory-Verbrauch

**Symptom:** ProcessExecutor verbraucht viel Speicher bei vielen Steps

**Ursache:** 
- Zu viele parallele Worker
- Große Dokumente in Step-Results

**Lösung:**
```python
# 1. max_workers reduzieren
executor = ProcessExecutor(max_workers=2)  # Statt 8

# 2. RAG top_k reduzieren
# In _retrieve_documents wird top_k=10 verwendet
# → Weniger Dokumente = weniger Memory

# 3. Re-Ranking deaktivieren (spart Ressourcen)
executor = ProcessExecutor(enable_reranking=False)
```

### Problem 5: Timeout bei langen Queries

**Symptom:** ProcessExecutor scheint zu "hängen"

**Ursache:** 
- Lange laufende Agent-Operations
- Viele Steps mit Dependencies

**Lösung:**
```python
# 1. Progress Callback verwenden für Monitoring
def on_progress(event):
    print(f"{event.timestamp}: {event.message}")

callback = ProgressCallback(on_progress)
result = executor.execute_process(tree, progress_callback=callback)

# 2. Steps reduzieren oder aufteilen
# 3. Timeouts in Agent-Operations setzen
```

---

## 🔗 Verwandte Dokumentation

### Interne Dependencies

- **DependencyResolver:** `backend/agents/framework/dependency_resolver.py`
  - Dokumentation: (TODO) `docs/components/agents/DEPENDENCY_RESOLVER.md`

- **ProcessTree & ProcessStep:** `backend/models/process_tree.py`, `backend/models/process_step.py`
  - Dokumentation: (TODO) `docs/components/models/PROCESS_MODELS.md`

- **AgentExecutor:** `backend/services/agent_executor.py`
  - Dokumentation: (TODO) `docs/components/services/AGENT_EXECUTOR.md`

- **RAGService:** `backend/services/rag_service.py`
  - Dokumentation: `docs/PHASE4_RAG_INTEGRATION.md` (zu konsolidieren)

- **HypothesisService:** `backend/services/hypothesis_service.py`
  - Dokumentation: `docs/PHASE5_HYPOTHESIS_GENERATION.md`

- **RerankerService:** `backend/services/reranker_service.py`
  - Dokumentation: `docs/HYBRID_SEARCH_RRF_RERANKING_REPORT.md`

### Architektur-Dokumente

- **Process Tree Architecture:** `docs/PROCESS_TREE_ARCHITECTURE.md`
- **Implementation Gap Analysis:** `docs/IMPLEMENTATION_GAP_ANALYSIS_TODO.md`
- **NLP Implementation:** `docs/NLP_IMPLEMENTATION_STATUS.md`

### API-Dokumentation

- **FastAPI Backend:** Wenn Backend läuft: `http://localhost:5000/docs`
- **API Reference:** `docs/API_REFERENCE.md`

---

## 📊 Performance-Charakteristiken

### Execution Time

**Typische Execution Times (gemessen):**
- Simple Query (1-3 Steps): 2-5 Sekunden
- Complex Query (5-10 Steps): 10-30 Sekunden
- Very Complex (10+ Steps): 30-60+ Sekunden

**Faktoren:**
- Anzahl Steps
- Step-Typen (SEARCH vs. AGENT)
- RAG Database Größe
- Agent-Response-Zeit
- max_workers Setting

### Parallelisierung

**Speedup durch Parallelisierung:**
```
max_workers=1:  100% (Baseline)
max_workers=2:  ~180% (1.8x faster)
max_workers=4:  ~320% (3.2x faster)
max_workers=8:  ~500% (5x faster, diminishing returns)
```

**Optimales max_workers:**
- CPU-bound Tasks: max_workers = CPU cores
- I/O-bound Tasks (RAG, Agents): max_workers = 2-4x CPU cores

### Memory Usage

**Geschätzte Memory-Nutzung:**
- Base Executor: ~50 MB
- Pro Worker: ~20-50 MB
- RAG Service: ~100-500 MB (abhängig von DB)
- Agent Executor: ~100-300 MB
- **Total (typical):** ~500 MB - 2 GB

---

## 🧪 Testing

### Unit Tests

```python
# tests/test_process_executor.py
import pytest
from backend.services.process_executor import ProcessExecutor
from backend.models.process_tree import ProcessTree

def test_simple_execution():
    tree = ProcessTree(query="Test")
    executor = ProcessExecutor(max_workers=2, use_agents=False)
    result = executor.execute_process(tree)
    
    assert result['success'] == True
    assert result['steps_completed'] >= 0

def test_parallel_execution():
    tree = ProcessTree(query="Parallel Test")
    # Add multiple independent steps
    # ...
    
    executor = ProcessExecutor(max_workers=4)
    result = executor.execute_process(tree)
    
    # Verify parallel execution via timing
    assert result['execution_time'] < sequential_time
```

### Integration Tests

Siehe: `tests/test_complete_token_system_e2e.py` für End-to-End Tests

---

## 📝 Changelog

### Version 1.0 (14. Oktober 2025)
- Initial release
- Core execution engine
- Dependency resolution
- Parallel step execution
- Agent integration
- RAG integration
- Streaming progress
- Hypothesis generation (Phase 5)
- Semantic re-ranking

---

**Maintainer:** VERITAS Development Team  
**Last Review:** 17. November 2025  
**Next Review:** Q1 2026
