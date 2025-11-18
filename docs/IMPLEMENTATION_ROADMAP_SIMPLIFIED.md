# VERITAS Deep Research System - Vereinfachte Implementierungs-Roadmap

**Datum:** 11. Oktober 2025
**Version:** 2.0 (OHNE LangGraph/Prefect)
**Philosophie:** Evolutionär statt revolutionär - Bestehende Architektur erweitern

---

## 🎯 Architektur-Entscheidungen

### ❌ VERZICHTET AUF:
1. **LangGraph** - Zu komplex, wir haben bereits SupervisorAgent
2. **Prefect** - Overkill für kurze Workflows (< 5 Minuten)
3. **Neue Dependencies** - Minimiere externe Abhängigkeiten

### ✅ BAUEN AUF:
1. **SupervisorAgent** - Erweitern mit Custom State Machine
2. **UDS3 RAG System** - Polyglot Persistenz bereits vorhanden! (ChromaDB, PostgreSQL, Neo4j)
3. **Bestehende Agenten** - 9+ Agenten bereits funktional
4. **JSON Citation System** - 100% Erfolgsrate, keep it!
5. **Rich Media** - Einzigartiges Feature, ausbauen!

### 🎯 **WICHTIG: UDS3 Integration**
VERITAS nutzt bereits **UDS3 (Universal Document System 3)** - ein polyglot RAG-System mit:
- ✅ **ChromaDB** - Vector Embeddings
- ✅ **PostgreSQL** - Dokumenten-Metadaten
- ✅ **Neo4j** - Knowledge Graph (falls konfiguriert)
- ✅ **Document Processing** - PDF, DOCX, TXT, etc.

**Konsequenz:** Wir brauchen KEIN neues RAG-System bauen, nur UDS3 besser nutzen!

---

## 📊 Vereinfachte 3-Phasen Roadmap

### Phase 1: Foundation (3-4 Wochen) 🔴 KRITISCH

**Ziel:** Persistentes JSON Framework + Reflexions-Loop

#### Sprint 1.1: Persistentes JSON Framework (1-2 Wochen)

**Tasks:**
1. **Research State Schema** (1 Tag)
   - `backend/agents/veritas_research_state.py`
   - TypedDicts für ResearchState, ExecutionTraceEntry

2. **PostgreSQL Persistence** (2-3 Tage)
   - `backend/agents/veritas_state_persister.py`
   - Migration: `CREATE TABLE research_states`
   - CRUD Operations (save, load, list, delete)

3. **SupervisorAgent Integration** (3-4 Tage)
   - Erweitere `process_query()` um `research_id` Parameter
   - State Loading/Saving
   - Execution Trace Logging

**Code-Beispiel:**
```python
# backend/agents/veritas_supervisor_agent.py

class SupervisorAgent:
    def __init__(self, db_config, ...):
        self.persister = ResearchStatePersister(db_config)

    async def process_query(
        self,
        query: str,
        research_id: Optional[str] = None  # NEW!
    ):
        # Load or create state
        if research_id:
            state = await self.persister.load_state(research_id)
        else:
            state = self._create_initial_state(query)

        # Process with state tracking
        while state['status'] == 'IN_PROGRESS':
            result = await self._execute_next_step(state)

            # Log execution
            state['execution_trace'].append({
                "task_id": len(state['execution_trace']) + 1,
                "agent": result.agent_type,
                "action": "EXECUTE",
                "output": result.dict()
            })

            # Persist
            await self.persister.save_state(state['research_id'], state)

        return state
```

**Deliverables:**
- ✅ Wiederaufsetzbare Recherchen (bei Crash/Neustart)
- ✅ Execution Trace (Audit-Log)
- ✅ PostgreSQL Persistence

---

#### Sprint 1.2: Reflexions-Loop (Custom State Machine) (1-2 Wochen)

**Ziel:** Selbstkorrektur OHNE LangGraph

**Architektur:**
```python
# Custom State Machine in SupervisorAgent

class WorkflowState(Enum):
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    REFINING = "refining"
    COMPLETED = "completed"
    FAILED = "failed"

class SupervisorAgent:
    async def _execute_workflow_with_refinement(self, state: ResearchState):
        """
        Custom State Machine mit Reflexions-Loop

        Flow:
        PLANNING → EXECUTING → EVALUATING
                        ↑           ↓
                        └─ REFINING ←┘ (wenn Qualität schlecht)
                                ↓
                            COMPLETED
        """

        max_refinements = 3
        refinement_count = 0
        current_state = WorkflowState.PLANNING

        while current_state != WorkflowState.COMPLETED:
            if current_state == WorkflowState.PLANNING:
                # Step 1: Agent Selection
                selected_agents = await self._select_agents(state['query'])
                state['selected_agents'] = selected_agents
                current_state = WorkflowState.EXECUTING

            elif current_state == WorkflowState.EXECUTING:
                # Step 2: Execute Agents
                results = await self._execute_agents(
                    state['selected_agents'],
                    state['query']
                )
                state['agent_results'] = results
                current_state = WorkflowState.EVALUATING

            elif current_state == WorkflowState.EVALUATING:
                # Step 3: Evaluate Quality (NEW!)
                evaluator = EvaluatorAgent(self.ollama)
                evaluation = await evaluator.evaluate_rag_triade(
                    query=state['query'],
                    context=self._format_context(results),
                    answer=results[-1].response_text
                )

                state['evaluation'] = evaluation

                # Decision: Good enough or refine?
                avg_score = (
                    evaluation['context_relevance'] +
                    evaluation['groundedness'] +
                    evaluation['answer_relevance']
                ) / 3

                if avg_score >= 0.75:
                    # Good enough!
                    current_state = WorkflowState.COMPLETED
                elif refinement_count >= max_refinements:
                    # Max retries reached
                    logger.warning("Max refinements reached, completing anyway")
                    current_state = WorkflowState.COMPLETED
                else:
                    # Refine!
                    logger.info(f"Quality too low ({avg_score:.2f}), refining...")
                    current_state = WorkflowState.REFINING

            elif current_state == WorkflowState.REFINING:
                # Step 4: Reformulate Query
                refinement_count += 1

                # Use evaluator feedback to improve query
                refined_query = await self._reformulate_query(
                    original_query=state['query'],
                    feedback=state['evaluation']['feedback']
                )

                state['query'] = refined_query
                state['refinement_history'].append({
                    "iteration": refinement_count,
                    "original_query": state['initial_query'],
                    "refined_query": refined_query,
                    "reason": state['evaluation']['feedback']
                })

                # Go back to planning
                current_state = WorkflowState.PLANNING

            # Persist state after each step
            await self.persister.save_state(state['research_id'], state)

        return state
```

**Tasks:**
1. **Evaluator Agent Implementation** (3-4 Tage)
   - `backend/agents/veritas_evaluator_agent.py`
   - RAG-Triade: Context Relevance, Groundedness, Answer Relevance
   - LLM-as-a-Judge mit Few-Shot Prompts

2. **State Machine in SupervisorAgent** (2-3 Tage)
   - `WorkflowState` Enum
   - `_execute_workflow_with_refinement()` Methode
   - Decision Logic (Score-basiert)

3. **Query Reformulation** (1-2 Tage)
   - `_reformulate_query()` Methode
   - Uses Evaluator Feedback
   - Keeps refinement history

**Deliverables:**
- ✅ Reflexions-Loop (max 3 Iterationen)
- ✅ Evaluator Agent (RAG-Triade)
- ✅ Automatische Qualitätsverbesserung

---

### Phase 2: Datenquellen-Erweiterung (2-3 Wochen) 🟡 VEREINFACHT

**Ziel:** UDS3 optimal nutzen + SearxNG Web Search

**🎯 WICHTIG:** UDS3 liefert bereits ChromaDB, PostgreSQL und optional Neo4j!

#### Sprint 2.1: UDS3 Optimierung (1 Woche) - STATT Neo4j neu aufsetzen

**Warum vereinfacht?**
- ✅ UDS3 hat bereits **ChromaDB** (Vector DB) → Keine neue Installation nötig
- ✅ UDS3 hat bereits **PostgreSQL** → Dokumenten-Metadaten vorhanden
- ✅ UDS3 hat optional **Neo4j** → Nur aktivieren, nicht neu bauen!

**Tasks:**
1. **UDS3 Capabilities inventarisieren** (1 Tag)
   - Check welche Backends aktiviert sind
   - ChromaDB Status prüfen
   - Neo4j Status prüfen (falls vorhanden)
   - Dokumenten-Statistiken

2. **UDS3 Query-Optimierung** (2-3 Tage)
   ```python
   # Nutze UDS3's bestehende APIs besser
   from uds3 import DocumentStore

   class UDS3EnhancedAgent:
       """Nutzt UDS3 RAG-System optimal"""

       def __init__(self, uds3_store: DocumentStore):
           self.store = uds3_store

       async def hybrid_search(self, query: str, top_k: int = 10):
           """
           Hybrid Search: Vector + Keyword + Graph (falls Neo4j aktiv)
           """
           # 1. Vector Search (ChromaDB via UDS3)
           vector_results = await self.store.vector_search(
               query=query,
               top_k=top_k,
               filters={"status": "active"}
           )

           # 2. Keyword Search (PostgreSQL via UDS3)
           keyword_results = await self.store.keyword_search(
               query=query,
               top_k=top_k
           )

           # 3. Graph Search (Neo4j via UDS3, falls vorhanden)
           if self.store.has_graph_backend:
               graph_results = await self.store.graph_query(
                   cypher_template="MATCH (d:Document)-[:RELATED_TO]->(r) WHERE d.content CONTAINS $query RETURN r",
                   params={"query": query}
               )
           else:
               graph_results = []

           # 4. Merge & Re-rank
           merged = self._merge_results(vector_results, keyword_results, graph_results)
           return merged
   ```

3. **Integration in SupervisorAgent** (2-3 Tage)
   - Nutze UDS3 statt separate ChromaDB/Neo4j Calls
   - Hybrid Search aktivieren
   - Dokumenten-Metadaten enrichen

**Deliverables:**
- ✅ UDS3 optimal genutzt (statt neue DB-Agenten)
- ✅ Hybrid Search (Vector + Keyword + Graph)
- ✅ Keine neuen Dependencies!

---

#### Sprint 2.2: SearxNG Web Search Agent (1.5-2 Wochen)

**Bleibt wie geplant** - SearxNG ist NICHT in UDS3, also müssen wir das hinzufügen.

**Tasks:**
1. **SearxNG Docker Setup** (1 Tag)
   - `docker-compose.yml` mit SearxNG
   - Privacy-Config (keine Logs)

2. **SearxNG Agent Implementation** (4-5 Tage)
   - `backend/agents/veritas_searxng_agent.py`
   - Web Search mit Deduplication
   - Integration in SupervisorAgent

3. **Testing** (2-3 Tage)
   - Unit Tests
   - Integration Tests

**Deliverables:**
- ✅ SearxNG Agent für Web-Recherche
- ✅ Privacy-compliant (On-Premise)

---

### Phase 3: Kryptographische Integrität (2-3 Wochen) 🟠 COMPLIANCE

**Ziel:** Hash-Kette + Digitale Signaturen (optional: QET)

#### Sprint 3.1: Integrity Manager (1.5-2 Wochen)

**Tasks:**
1. **Hash-Kette Implementation** (3-4 Tage)
   - `backend/agents/veritas_integrity_manager.py`
   - SHA-256 Hash Chain
   - RSA Digital Signatures

2. **Integration in State Persister** (2-3 Tage)
   - `save_state()` berechnet Hash + Signatur
   - `load_state()` verifiziert Integrität

3. **Testing** (2-3 Tage)
   - Manipulation Detection Tests
   - Performance Tests

**Code-Beispiel:**
```python
# backend/agents/veritas_integrity_manager.py

class IntegrityManager:
    def compute_state_hash(self, execution_trace: List[Dict]) -> str:
        """SHA-256 Hash über execution_trace"""
        trace_json = json.dumps(execution_trace, sort_keys=True)
        return hashlib.sha256(trace_json.encode()).hexdigest()

    def sign_state(self, state_hash: str) -> str:
        """RSA-PSS Signatur"""
        signature = self.private_key.sign(
            state_hash.encode(),
            padding.PSS(...),
            hashes.SHA256()
        )
        return signature.hex()

    def verify_integrity(self, state: ResearchState) -> bool:
        """Verifiziert Hash-Kette + Signatur"""
        # Check hash chain
        for i in range(1, len(state['execution_trace'])):
            prev_hash = self.compute_state_hash(
                state['execution_trace'][:i]
            )
            if state['integrity_chain'][i-1] != prev_hash:
                return False  # Manipulation!

        # Verify signature
        current_hash = self.compute_state_hash(state['execution_trace'])
        return self._verify_signature(current_hash, state['signature'])
```

**Deliverables:**
- ✅ Hash-Kette (Blockchain-ähnlich)
- ✅ Digitale Signaturen
- ✅ Manipulations-Erkennung

---

#### Sprint 3.2: Qualifizierte Zeitstempel (Optional, 1 Woche)

**NUR wenn eIDAS-Compliance erforderlich!**

**Tasks:**
1. **TSP Client Implementation** (3-4 Tage)
   - `backend/agents/veritas_timestamp_client.py`
   - Integration mit eIDAS TSP (z.B. Deutsche Telekom)
   - RFC 3161 Timestamp Requests

**Deliverables:**
- ✅ QET für rechtliche Beweiskraft (EU-weit)

---

## 📊 Zeitplan & Meilensteine

### Meilenstein 1: MVP Foundation (Woche 1-4)
**Datum:** 11.10.2025 - 08.11.2025

- ✅ Persistentes JSON Framework (Research State in PostgreSQL)
- ✅ Reflexions-Loop (Custom State Machine)
- ✅ Evaluator-Agent (RAG-Triade)

**Demo:** Wiederaufsetzbare Recherche mit automatischer Qualitätsverbesserung

---

### Meilenstein 2: UDS3 Optimierung + Web Search (Woche 5-7) - VERKÜRZT!
**Datum:** 11.11.2025 - 29.11.2025

- ✅ UDS3 Hybrid Search (Vector + Keyword + Graph)
- ✅ SearxNG Web Search Agent

**Demo:** Komplexe Recherche mit UDS3 Hybrid Search + Web-Suche

**🎯 ZEITGEWINN:** 1-2 Wochen gespart, da UDS3 bereits ChromaDB, PostgreSQL, Neo4j liefert!

---

### Meilenstein 3: Production-Ready (Woche 8-10)
**Datum:** 02.12.2025 - 20.12.2025

- ✅ Kryptographische Integrität
- ✅ Hash-Kette + Signaturen
- ✅ Optional: QET (eIDAS)

**Demo:** Rechtssicherer Audit-Trail mit Manipulationsschutz

---

## 🎯 Erfolgs-Kriterien

### Nach Phase 1 (MVP):
- [ ] Recherchen sind wiederaufsetzbar (bei Crash)
- [ ] Execution Trace wird persistiert (PostgreSQL)
- [ ] Evaluator-Agent bewertet Qualität (RAG-Triade)
- [ ] Reflexions-Loop verbessert Ergebnisse automatisch
- [ ] Max. 3 Refinement-Iterationen
- [ ] Erfolgsrate: 70% → 85%+ (durch Reflexion)

### Nach Phase 2 (Datenquellen):
- [ ] UDS3 Hybrid Search aktiviert (Vector + Keyword + Graph)
- [ ] ChromaDB optimal genutzt (via UDS3)
- [ ] Neo4j aktiviert (via UDS3, falls verfügbar)
- [ ] SearxNG Agent findet aktuelle Web-Infos
- [ ] 10+ Spezialisierte Agenten verfügbar
- [ ] Coverage: Baurecht, Umwelt, Verkehr, Soziales, Web, UDS3-Dokumente

### Nach Phase 3 (Integrität):
- [ ] Hash-Kette schützt vor Manipulation
- [ ] Digitale Signaturen beweisen Authentizität
- [ ] Optional: QET für rechtliche Beweiskraft
- [ ] DSGVO-konform (Audit-Trail)

---

## 📋 Task-Übersicht nach Priorität

### 🔴 P0 - Sofort (Phase 1)

| Task | Aufwand | Sprint |
|------|---------|--------|
| Research State Schema | 1 Tag | 1.1 |
| PostgreSQL Migration | 1 Tag | 1.1 |
| State Persister Implementation | 2-3 Tage | 1.1 |
| SupervisorAgent Integration | 3-4 Tage | 1.1 |
| Evaluator Agent Implementation | 3-4 Tage | 1.2 |
| Custom State Machine | 2-3 Tage | 1.2 |
| Query Reformulation | 1-2 Tage | 1.2 |
| Unit Tests | 2-3 Tage | 1.1+1.2 |

**Gesamt P0:** 3-4 Wochen

---

### 🟡 P1 - Wichtig (Phase 2)

| Task | Aufwand | Sprint |
|------|---------|--------|
| UDS3 Capabilities Check | 1 Tag | 2.1 |
| UDS3 Hybrid Search Implementation | 2-3 Tage | 2.1 |
| UDS3 Integration in SupervisorAgent | 2-3 Tage | 2.1 |
| SearxNG Docker Setup | 1 Tag | 2.2 |
| SearxNG Agent Implementation | 4-5 Tage | 2.2 |
| SearxNG Integration | 1-2 Tage | 2.2 |
| Tests | 2-3 Tage | 2.1+2.2 |

**Gesamt P1:** 2-3 Wochen (VERKÜRZT von 3-4 Wochen dank UDS3!)

---

### 🟠 P2 - Compliance (Phase 3)

| Task | Aufwand | Sprint |
|------|---------|--------|
| Integrity Manager Implementation | 3-4 Tage | 3.1 |
| Hash-Kette + Signaturen | 2-3 Tage | 3.1 |
| Integration in Persister | 2-3 Tage | 3.1 |
| Tests | 2-3 Tage | 3.1 |

**Gesamt P2:** 2-3 Wochen

---

### 🟢 P3 - Optional

| Task | Aufwand | Sprint |
|------|---------|--------|
| QET (eIDAS Timestamp) | 3-4 Tage | 3.2 |

**Gesamt P3:** 1 Woche (nur wenn eIDAS erforderlich)

---

## 🚀 Quick Start

### Schritt 1: Phase 1 Sprint 1.1 starten (HEUTE!)

```bash
# 1. PostgreSQL Migration erstellen
touch migrations/001_create_research_states.sql

# 2. Research State Schema erstellen
touch backend/agents/veritas_research_state.py

# 3. State Persister erstellen
touch backend/agents/veritas_state_persister.py

# 4. Tests erstellen
touch tests/test_state_persister.py
```

### Schritt 2: Team-Meeting (Morgen)

**Agenda:**
1. Review dieser Roadmap (15 Min)
2. Ressourcen-Allocation klären (10 Min)
3. Sprint 1.1 Tasks zuweisen (10 Min)
4. Questions & Concerns (10 Min)

### Schritt 3: Sprint 1.1 Kickoff (Übermorgen)

**Ziel:** Persistentes JSON Framework in 1-2 Wochen

**Daily Standups:** 10:00 Uhr (15 Min)

---

## 🎯 Warum OHNE LangGraph/Prefect?

### ❌ LangGraph Probleme:
1. **Neue Dependency** → Mehr Komplexität
2. **Lernkurve** → Team muss LangGraph lernen
3. **Overkill** → SupervisorAgent reicht für unsere Anwendung
4. **Migration** → Bestehenden Code umschreiben

### ✅ Custom State Machine Vorteile:
1. **Volle Kontrolle** → Genau was wir brauchen
2. **Kein Vendor Lock-in** → Unabhängig
3. **Einfacher Debug** → Verstehen den Code
4. **Evolutionär** → Bestehenden Code erweitern

### ❌ Prefect Probleme:
1. **Workflows < 5 Min** → Prefect für langlebige Workflows (Stunden/Tage)
2. **Overhead** → Komplexes Setup
3. **Nicht nötig** → FastAPI reicht

### ✅ Unser Ansatz:
- **SupervisorAgent** als Orchestrator
- **Custom State Machine** für Reflexion
- **PostgreSQL** für Persistence
- **FastAPI** für Endpoints

→ **KISS Principle:** Keep It Simple, Stupid!

---

## 📈 Erfolgsmetriken

### Baseline (Aktuell):
- ✅ 100% JSON Citation Success
- ✅ 100% Rich Media Generation
- ✅ 9+ Spezialisierte Agenten
- ❌ 0% Wiederaufsetzbarkeit (bei Crash)
- ❌ 0% Qualitäts-Evaluation
- ❌ 0% Reflexion

### Ziel nach Phase 1:
- ✅ 100% Wiederaufsetzbarkeit
- ✅ 100% Execution Trace Logging
- ✅ 80%+ Qualitäts-Evaluation Accuracy
- ✅ 30%+ Verbesserung durch Reflexion

### Ziel nach Phase 2:
- ✅ 11+ Spezialisierte Agenten
- ✅ Graph-Queries (Neo4j)
- ✅ Web-Recherche (SearxNG)

### Ziel nach Phase 3:
- ✅ 100% Manipulations-Erkennung
- ✅ Rechtssicherer Audit-Trail
- ✅ Optional: eIDAS-Compliance

---

## 🎓 Lessons Learned

**Was wir gelernt haben:**
1. **JSON Citation System** war BRILLANT → Keep it!
2. **Rich Media** geht über Konzept hinaus → Ausbauen!
3. **SupervisorAgent** funktioniert gut → Erweitern statt ersetzen!
4. **Zu viele Dependencies** sind schlecht → Minimieren!

**Was wir ändern:**
1. ~~LangGraph~~ → Custom State Machine
2. ~~Prefect~~ → FastAPI reicht
3. **Evolutionär** statt revolutionär
4. **Schritt für Schritt** statt Big Bang

---

**Ende der vereinfachten Roadmap**

**Nächster Schritt:** Sprint 1.1 starten - Research State Schema erstellen!
