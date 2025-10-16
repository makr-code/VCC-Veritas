# VERITAS/VCC Deep Research System - Gap Analysis & Implementation Plan

**Datum:** 11. Oktober 2025  
**Version:** 1.0  
**Status:** 🔴 CRITICAL - Architektur-Refactoring erforderlich

---

## 📊 Executive Summary

### Konzept vs. Realität

| Aspekt | Konzept (Soll) | Implementierung (Ist) | Gap | Priorität |
|--------|----------------|----------------------|-----|-----------|
| **Macro-Orchestrierung** | Prefect (langlebige Workflows) | ❌ Nicht vorhanden | NIEDRIG | � P3 |
| **Micro-Orchestrierung** | ~~LangGraph~~ Custom StateGraph | ✅ SupervisorAgent vorhanden | NIEDRIG | ✅ OK |
| **Agenten-Architektur** | Spezialisierte Tool-Agenten | ✅ Vorhanden (9+ Agenten) | NIEDRIG | ✅ OK |
| **Zustandsverwaltung** | Persistentes JSON Framework | ❌ Nur In-Memory | HOCH | 🔴 P0 |
| **Reflexion/Selbstkorrektur** | LLM-as-a-Judge, RAG-Triade | ❌ Nicht vorhanden | HOCH | 🔴 P0 |
| **Kryptograph. Integrität** | Hash-Kette, Signaturen, QET | ❌ Nicht vorhanden | MITTEL | 🟡 P2 |
| **Rich Media** | Nicht im Konzept | ✅ **NEU: Implementiert!** | BONUS | ✅ ++ |
| **On-Premise LLM** | Ollama/vLLM | ✅ Ollama integriert | NIEDRIG | ✅ OK |
| **Datenquellen** | Neo4j, ChromaDB, SQL, SearxNG | Teilweise (ChromaDB, SQL) | MITTEL | 🟡 P1 |

**🔧 ARCHITEKTUR-ENTSCHEIDUNG:** Wir verzichten auf LangGraph und bauen stattdessen eine **Custom State Machine** in SupervisorAgent ein. Vorteil: Keine neue Dependency, volle Kontrolle, evolutionäre Erweiterung.

### Kritische Erkenntnisse

**✅ STÄRKEN (bereits implementiert):**
1. **Agenten-Ökosystem:** 9+ spezialisierte Agenten (Environmental, Financial, Social, Traffic, Wikipedia, Building, Atmospheric)
2. **JSON Citation System:** Revolutionärer Ansatz - NICHT im Konzept, aber BESSER als ursprünglich geplant!
3. **Rich Media Support:** Maps, Charts, Tables, Images - Geht über Konzept hinaus!
4. **SupervisorAgent:** Grundlegende Multi-Agent-Koordination vorhanden
5. **Ollama Integration:** On-Premise LLM funktioniert

**🔴 KRITISCHE LÜCKEN:**
1. **Keine Zustandspersistenz:** Kein progressives JSON Framework → Recherchen nicht wiederaufsetzbar
2. **Keine Reflexionsschleife:** Kein Evaluator-Agent → Keine Selbstkorrektur
3. **Fehlende Datenquellen:** Neo4j, SearxNG nicht integriert

**✅ NICHT KRITISCH (bereits gut gelöst):**
- ~~LangGraph~~ → SupervisorAgent reicht für Micro-Orchestrierung
- ~~Prefect~~ → FastAPI reicht für kurze Workflows (optional später)

**🎯 STRATEGISCHE EMPFEHLUNG:**

Das System hat eine **hervorragende Basis** (Agenten, Rich Media, JSON Citations). Wir brauchen **KEINE** neuen Libraries (LangGraph, Prefect), sondern nur **evolutionäre Erweiterung** der bestehenden Architektur.

**Empfehlung: Evolutionärer Ansatz (OHNE neue Dependencies!)**
- ✅ **Behalten:** SupervisorAgent, Agenten, JSON Citations, Rich Media
- 🔄 **Erweitern:** Custom State Machine in SupervisorAgent, Persistentes JSON Framework
- ➕ **Hinzufügen:** Evaluator-Agent, Neo4j, SearxNG
- 🚀 **Kein Prefect/LangGraph:** Zu komplex für unsere Anwendung

---

## 🏗️ Architektur-Abgleich

### Konzept: 4-Layer Deep Research Architecture

```
┌─────────────────────────────────────────────┐
│ Layer 4: Macro-Orchestrierung (OPTIONAL)   │
│  ❌ VERZICHTET: Prefect zu komplex         │
│  → FastAPI Endpoints reichen für MVP      │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ Layer 3: Micro-Orchestrierung (CUSTOM)     │
│  ✅ LÖSUNG: SupervisorAgent + State Machine│
│  - Custom Reflexions-Loop (kein LangGraph) │
│  - Bedingte Verzweigungen                  │
│  - Iterative Zyklen                        │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ Layer 2: Spezialisierte Agenten            │
│  ✅ BEREITS VORHANDEN (9+ Agenten)         │
│  + Evaluator Agent (NEU)                   │
│  + Neo4j Agent (NEU)                       │
│  + SearxNG Agent (NEU)                     │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ Layer 1: Persistente Zustandsverwaltung    │
│  ✅ LÖSUNG: PostgreSQL + JSON Framework    │
│  - Execution Trace (unveränderlich)        │
│  - Hash-Kette (Blockchain-ähnlich)         │
│  - Digitale Signaturen (optional)          │
└─────────────────────────────────────────────┘
```

### Ist-Zustand: VERITAS Current Architecture

```
┌─────────────────────────────────────────────┐
│ ✅ Layer 4: FastAPI Endpoints (AUSREICHEND)│
│    Direkte Endpoints reichen für MVP      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 🟡 Layer 3: SupervisorAgent (GUT)          │
│    ✅ Agent Selection                      │
│    ✅ Multi-Agent Coordination             │
│    ❌ FEHLT: Reflexions-Schleife           │
│    → LÖSUNG: Custom State Machine bauen   │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ ✅ Layer 2: GUT IMPLEMENTIERT              │
│    ✅ EnvironmentalAgent                   │
│    ✅ FinancialAgent                       │
│    ✅ SocialAgent                          │
│    ✅ TrafficAgent                         │
│    ✅ WikipediaAgent                       │
│    ✅ BuildingAgent                        │
│    ✅ AtmosphericFlowAgent                 │
│    ❌ Graph DB Agent (Neo4j) - FEHLT       │
│    ❌ Web Search Agent (SearxNG) - FEHLT   │
│    ❌ Evaluator Agent - FEHLT              │
│    ✅ **BONUS: JSON Citation Formatter**   │
│    ✅ **BONUS: Rich Media Schema**         │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ ❌ Layer 1: KRITISCH FEHLEND               │
│    ❌ Kein persistentes JSON Framework     │
│    ❌ Kein Execution Trace                 │
│    ❌ Keine Hash-Kette                     │
│    ❌ Keine Signaturen                     │
└─────────────────────────────────────────────┘
```

---

## 🔍 Detaillierte Gap-Analyse

### 1. Macro-Orchestrierung (Prefect)

**Konzept:**
- Prefect verwaltet langlebige Workflows (Stunden/Tage)
- Intelligent Retries bei temporären Fehlern
- Human-in-the-Loop Checkpoints
- Zentrales Observability Dashboard

**Ist-Zustand:** ❌ Nicht vorhanden

**Auswirkungen:**
- ❌ Workflows können nicht über Stunden/Tage laufen
- ❌ Keine automatischen Retries bei Fehlern
- ❌ Keine Human-Validierung möglich
- ❌ Keine zentrale Workflow-Überwachung

**Empfehlung:** 🟡 **Phase 2 (Optional)**
- Für Prototyp NICHT kritisch
- Erst relevant bei Multi-Stunden-Recherchen
- Kann später hinzugefügt werden ohne Architektur-Änderung

---

### 2. Micro-Orchestrierung (LangGraph)

**Konzept:**
```python
# LangGraph StateGraph mit bedingten Verzweigungen
from langgraph.graph import StateGraph

workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("parse_query", parse_initial_query)
workflow.add_node("generate_plan", planner_agent)
workflow.add_node("execute_step", execute_agent_step)
workflow.add_node("evaluate_results", evaluator_agent)
workflow.add_node("reformulate", reformulate_query)
workflow.add_node("synthesize", synthesize_report)

# Conditional Edges (Reflexions-Schleife!)
workflow.add_conditional_edges(
    "evaluate_results",
    decide_next_step,  # Router function
    {
        "refine": "reformulate",     # Schlecht → Neu formulieren
        "continue": "execute_step",  # OK → Nächster Schritt
        "complete": "synthesize"     # Gut → Abschluss
    }
)

# Compile
app = workflow.compile(checkpointer=postgres_checkpointer)
```

**Ist-Zustand:** 🟡 **Teilweise - SupervisorAgent**

```python
# veritas_supervisor_agent.py (Lines 916+)
class SupervisorAgent:
    async def process_query(self, query, context):
        # 1. Agent Selection
        selected_agents = await self.selector.select_agents(query)
        
        # 2. Agent Execution (parallel)
        agent_results = await self.execute_agents(selected_agents, query)
        
        # 3. Synthesis
        synthesized = await self.synthesize_results(agent_results, query)
        
        return synthesized
```

**Gap:**
- ✅ Hat: Agent Selection, Parallel Execution, Synthesis
- ❌ Fehlt: 
  - Keine explizite StateGraph (LangGraph)
  - Keine Reflexions-Schleife (evaluate → refine → retry)
  - Keine bedingten Verzweigungen
  - Keine persistente Zustandsverwaltung
  - Nicht wiederaufsetzbar

**Auswirkungen:**
- ❌ Schlechte Agenten-Antworten werden NICHT erkannt
- ❌ Keine automatische Neuformulierung bei schlechten Ergebnissen
- ❌ Kein iteratives Verfeinern
- ❌ Bei Crash → gesamter Progress verloren

**Empfehlung:** 🔴 **P0 - Kritisch**

**Implementierungsplan:**
1. LangGraph StateGraph einführen
2. Evaluator-Agent implementieren (LLM-as-a-Judge)
3. Reflexions-Schleife bauen (evaluate → decide → refine/continue)
4. PostgreSQL Checkpointer für Persistenz

---

### 3. Spezialisierte Agenten

**Konzept vs. Ist:**

| Agent-Typ | Konzept | Ist-Zustand | Gap |
|-----------|---------|-------------|-----|
| **Graph DB (Neo4j)** | ✅ Erforderlich | ❌ Fehlt | 🔴 Kritisch für Beziehungsanalysen |
| **Vector DB (ChromaDB)** | ✅ Erforderlich | ✅ Vorhanden | ✅ OK |
| **SQL DB (PostgreSQL)** | ✅ Erforderlich | ✅ Vorhanden | ✅ OK |
| **Web Search (SearxNG)** | ✅ Erforderlich | ❌ Fehlt | 🟡 Wichtig für externe Recherche |
| **Evaluator (LLM-as-Judge)** | ✅ Erforderlich | ❌ Fehlt | 🔴 Kritisch für Qualität |
| **Planner (CoT)** | ✅ Erforderlich | 🟡 SupervisorAgent.selector | 🟡 Erweitern |
| **Environmental** | ❌ Nicht im Konzept | ✅ Implementiert | ✅ Bonus! |
| **Financial** | ❌ Nicht im Konzept | ✅ Implementiert | ✅ Bonus! |
| **Social** | ❌ Nicht im Konzept | ✅ Implementiert | ✅ Bonus! |
| **Traffic** | ❌ Nicht im Konzept | ✅ Implementiert | ✅ Bonus! |
| **Wikipedia** | ❌ Nicht im Konzept | ✅ Implementiert | ✅ Bonus! |
| **Building** | ❌ Nicht im Konzept | ✅ Implementiert | ✅ Bonus! |
| **Atmospheric Flow** | ❌ Nicht im Konzept | ✅ Implementiert | ✅ Bonus! |

**Bewertung:**
- ✅ **Hervorragend:** 7 Domain-spezifische Agenten (über Konzept hinaus!)
- ❌ **Fehlt:** Neo4j, SearxNG, Evaluator (kritisch)
- 🎯 **Strategie:** Vorhandene Agenten behalten, fehlende hinzufügen

---

### 4. Persistente Zustandsverwaltung (Progressive JSON Framework)

**Konzept: Rechtssicheres Saga-Log**

```json
{
  "research_id": "uuid-v4-...",
  "initial_query": "Analyse der Auswirkungen von KI...",
  "status": "IN_PROGRESS",
  "global_state": {
    "known_entities": ["KI", "Lieferkette", "Europa"],
    "hypotheses": ["KI erhöht Effizienz um 10-15%"],
    "rejected_paths": ["Personalplanung out of scope"]
  },
  "execution_trace": [
    {
      "task_id": 1,
      "timestamp": "2024-10-27T10:00:00Z",
      "agent": "PlannerAgent",
      "action": "GENERATE_PLAN",
      "input": {...},
      "output": {...},
      "evaluation": {
        "metrics": {
          "context_relevance": 0.9,
          "groundedness": 0.85,
          "answer_relevance": 0.88
        }
      }
    },
    {
      "task_id": 2,
      "timestamp": "2024-10-27T10:15:00Z",
      "agent": "WebSearchAgent",
      "action": "SEARCH",
      ...
    }
  ],
  "integrity": {
    "currentStateHash": "sha256-abc123...",
    "previousStateHash": "sha256-def456...",
    "stateSignature": "RSA-signature...",
    "qualifiedTimestampToken": "RFC3161-token..."
  }
}
```

**Ist-Zustand:** ❌ **NICHT vorhanden**

Current response format (from Rich Media JSON):
```json
{
  "direct_answer": "...",
  "details": [...],
  "citations": [...],
  "sources": [...],
  "tables": [...],
  "maps": [...],
  "charts": [...]
}
```

**Gap:**
- ❌ Keine `execution_trace` → Kein Audit-Trail
- ❌ Keine `global_state` → Kein kumulatives Wissen
- ❌ Keine `integrity` → Keine Rechtssicherheit
- ❌ Nicht persistent → Bei Crash alles weg
- ❌ Kein `research_id` → Keine Wiederaufsetzbarkeit

**Auswirkungen:**
- ❌ **Keine Nachvollziehbarkeit:** Warum wurde Entscheidung X getroffen?
- ❌ **Keine Wiederaufsetzbarkeit:** Crash → Start von vorn
- ❌ **Keine Rechtssicherheit:** Kein gerichtsfester Beweis
- ❌ **Kein Debugging:** Wie kam das System zu diesem Ergebnis?
- ❌ **Keine Auditierung:** DSGVO/Compliance unmöglich

**Empfehlung:** 🔴 **P0 - Absolut kritisch!**

---

### 5. Reflexion & Selbstkorrektur (RAG-Triade)

**Konzept: Evaluator-Agent mit LLM-as-a-Judge**

```python
class EvaluatorAgent:
    async def evaluate(self, query: str, context: str, answer: str):
        """
        Bewertet Antwort-Qualität nach RAG-Triade
        
        Returns:
            {
                "context_relevance": 0.0-1.0,
                "groundedness": 0.0-1.0,
                "answer_relevance": 0.0-1.0,
                "feedback": "Text-Begründung",
                "refinement_needed": True/False
            }
        """
        
        evaluation_prompt = f"""
Du bist ein kritischer Evaluator. Bewerte die Qualität der Antwort:

**Frage:** {query}
**Kontext (Quellen):** {context}
**Antwort:** {answer}

Bewerte nach diesen Kriterien (0.0-1.0):

1. **Context Relevance:** Ist der Kontext relevant für die Frage?
2. **Groundedness:** Basiert die Antwort NUR auf dem Kontext (keine Halluzinationen)?
3. **Answer Relevance:** Beantwortet die Antwort die Frage direkt?

Gib JSON zurück:
{{
  "context_relevance": 0.X,
  "groundedness": 0.X,
  "answer_relevance": 0.X,
  "feedback": "Begründung...",
  "refinement_needed": true/false
}}
"""
        
        evaluation = await self.llm.generate(evaluation_prompt)
        return json.loads(evaluation)
```

**Ist-Zustand:** ❌ **NICHT vorhanden**

SupervisorAgent macht:
```python
# veritas_supervisor_agent.py
async def synthesize_results(self, agent_results, query):
    # 1. Deduplizierung
    deduplicated = self._deduplicate_information(agent_results)
    
    # 2. Konflikt-Detektion (basic)
    conflicts = self._detect_contradictions(agent_results)
    
    # 3. LLM Synthesis (JSON → IEEE)
    synthesized_text = await self.llm.generate(...)
    
    # ❌ KEINE Evaluation der Qualität!
    # ❌ KEINE Reflexion!
    # ❌ KEIN Feedback-Loop!
    
    return SynthesizedResult(response_text=synthesized_text)
```

**Gap:**
- ❌ Keine Qualitätsbewertung nach Synthesis
- ❌ Keine Halluzinations-Detektion
- ❌ Keine Neuformulierung bei schlechten Ergebnissen
- ❌ Keine iterative Verbesserung

**Auswirkungen:**
- ❌ Schlechte Antworten werden nicht erkannt
- ❌ Halluzinationen bleiben unentdeckt
- ❌ Irrelevante Ergebnisse nicht gefiltert
- ❌ Keine automatische Qualitätsverbesserung

**Empfehlung:** 🔴 **P0 - Kritisch für Qualität**

---

### 6. Kryptographische Integrität

**Konzept: 3-Layer Security**

1. **Hash-Kette (Blockchain-ähnlich):**
   ```python
   integrity = {
       "currentStateHash": sha256(execution_trace[-1]),
       "previousStateHash": sha256(execution_trace[-2]),
       # Jeder State versiegelt den vorherigen
   }
   ```

2. **Digitale Signatur (intern):**
   ```python
   # VCC Certificate Authority
   private_key = load_private_key("vcc_system.pem")
   signature = private_key.sign(current_hash)
   ```

3. **Qualifizierter Zeitstempel (extern):**
   ```python
   # eIDAS-zertifizierter TSP
   timestamp_token = tsp_client.get_timestamp(current_hash)
   # → Rechtlich verbindlich (EU-weit)
   ```

**Ist-Zustand:** ❌ **NICHT vorhanden**

**Gap:**
- ❌ Keine Hash-Kette → Manipulationen nicht erkennbar
- ❌ Keine Signaturen → Keine Authentizität
- ❌ Keine Zeitstempel → Keine rechtliche Beweiskraft

**Empfehlung:** 🟡 **P2 - Wichtig für Compliance, nicht kritisch für MVP**

---

## 🎯 Implementierungskonzept

### Phase 1: Foundation (4-6 Wochen) 🔴 KRITISCH

**Ziel:** Persistentes JSON Framework + LangGraph StateGraph

#### Sprint 1.1: Persistentes JSON Framework (2 Wochen)

**Tasks:**
1. **Schema Design**
   ```python
   # backend/agents/veritas_research_state.py
   
   from typing import TypedDict, List, Dict, Any
   from datetime import datetime
   
   class ExecutionTraceEntry(TypedDict):
       task_id: int
       timestamp: str
       agent: str
       action: str
       input: Dict[str, Any]
       output: Dict[str, Any]
       evaluation: Dict[str, Any]  # RAG-Triade Scores
   
   class ResearchState(TypedDict):
       research_id: str
       initial_query: str
       status: str  # "IN_PROGRESS", "COMPLETED", "FAILED"
       global_state: Dict[str, Any]
       execution_trace: List[ExecutionTraceEntry]
       current_task: Dict[str, Any]
       results_summary: Dict[str, Any]
       timestamps: Dict[str, str]
   ```

2. **PostgreSQL Persistence**
   ```python
   # backend/agents/veritas_state_persister.py
   
   class ResearchStatePersister:
       async def save_state(self, research_id: str, state: ResearchState):
           """Speichert Zustand in PostgreSQL"""
           await self.db.execute(
               "INSERT INTO research_states (id, state_json, updated_at) "
               "VALUES ($1, $2, $3) "
               "ON CONFLICT (id) DO UPDATE SET state_json = $2, updated_at = $3",
               research_id, json.dumps(state), datetime.utcnow()
           )
       
       async def load_state(self, research_id: str) -> ResearchState:
           """Lädt Zustand aus PostgreSQL"""
           row = await self.db.fetchrow(
               "SELECT state_json FROM research_states WHERE id = $1",
               research_id
           )
           return json.loads(row['state_json'])
   ```

3. **Integration in SupervisorAgent**
   ```python
   # backend/agents/veritas_supervisor_agent.py
   
   class SupervisorAgent:
       def __init__(self):
           self.persister = ResearchStatePersister()
       
       async def process_query(self, query: str, research_id: str = None):
           # Load or create state
           if research_id:
               state = await self.persister.load_state(research_id)
           else:
               state = self._create_initial_state(query)
           
           # Process with state tracking
           while state['status'] == 'IN_PROGRESS':
               result = await self._execute_next_step(state)
               state['execution_trace'].append(result)
               await self.persister.save_state(state['research_id'], state)
           
           return state
   ```

**Deliverables:**
- ✅ `veritas_research_state.py` - State Schema
- ✅ `veritas_state_persister.py` - PostgreSQL Persistence
- ✅ Migration: `CREATE TABLE research_states`
- ✅ Integration in SupervisorAgent
- ✅ Unit Tests

---

#### Sprint 1.2: LangGraph StateGraph (2 Wochen)

**Tasks:**
1. **LangGraph Installation**
   ```bash
   pip install langgraph langchain
   ```

2. **StateGraph Definition**
   ```python
   # backend/agents/veritas_langgraph_workflow.py
   
   from langgraph.graph import StateGraph
   from langgraph.checkpoint.postgres import PostgresSaver
   
   # State Schema
   class VeritasAgentState(TypedDict):
       query: str
       plan: Dict[str, Any]
       agent_results: List[AgentResult]
       evaluation: Dict[str, Any]
       refinement_count: int
       final_answer: str
   
   # Workflow Definition
   def create_veritas_workflow():
       workflow = StateGraph(VeritasAgentState)
       
       # Nodes
       workflow.add_node("parse_query", parse_initial_query)
       workflow.add_node("generate_plan", planner_agent)
       workflow.add_node("select_agents", agent_selector)
       workflow.add_node("execute_agents", execute_parallel_agents)
       workflow.add_node("evaluate", evaluator_agent)
       workflow.add_node("synthesize", synthesize_results)
       
       # Entry Point
       workflow.set_entry_point("parse_query")
       
       # Edges
       workflow.add_edge("parse_query", "generate_plan")
       workflow.add_edge("generate_plan", "select_agents")
       workflow.add_edge("select_agents", "execute_agents")
       workflow.add_edge("execute_agents", "evaluate")
       
       # Conditional Edge (Reflexions-Schleife!)
       workflow.add_conditional_edges(
           "evaluate",
           decide_next_action,
           {
               "refine": "generate_plan",  # Schlecht → Neu planen
               "retry": "execute_agents",  # Mittel → Retry
               "complete": "synthesize"    # Gut → Fertig
           }
       )
       
       workflow.add_edge("synthesize", END)
       
       # PostgreSQL Checkpointer
       checkpointer = PostgresSaver.from_conn_string(
           "postgresql://user:pass@localhost/veritas"
       )
       
       return workflow.compile(checkpointer=checkpointer)
   ```

3. **Router Function (Entscheidungslogik)**
   ```python
   def decide_next_action(state: VeritasAgentState) -> str:
       """
       Entscheidet basierend auf Evaluation, was als nächstes passiert
       """
       eval = state['evaluation']
       
       # Check RAG-Triade Scores
       avg_score = (
           eval['context_relevance'] +
           eval['groundedness'] +
           eval['answer_relevance']
       ) / 3
       
       # Check refinement limit
       if state['refinement_count'] >= 3:
           return "complete"  # Max. 3 Versuche
       
       # Decision based on quality
       if avg_score >= 0.8:
           return "complete"  # Gut genug!
       elif avg_score >= 0.5:
           return "retry"     # Retry mit gleicher Strategie
       else:
           return "refine"    # Neu planen mit anderer Strategie
   ```

**Deliverables:**
- ✅ `veritas_langgraph_workflow.py` - StateGraph Definition
- ✅ PostgreSQL Checkpointer Setup
- ✅ Conditional Edges für Reflexion
- ✅ Integration mit SupervisorAgent
- ✅ Integration Tests

---

#### Sprint 1.3: Evaluator-Agent (2 Wochen)

**Tasks:**
1. **Evaluator Implementation**
   ```python
   # backend/agents/veritas_evaluator_agent.py
   
   class EvaluatorAgent:
       def __init__(self, ollama_client):
           self.ollama = ollama_client
       
       async def evaluate_rag_triade(
           self, 
           query: str, 
           context: str, 
           answer: str
       ) -> Dict[str, Any]:
           """
           Bewertet Antwort nach RAG-Triade
           
           Returns:
               {
                   "context_relevance": 0.0-1.0,
                   "groundedness": 0.0-1.0,
                   "answer_relevance": 0.0-1.0,
                   "feedback": "Begründung",
                   "refinement_needed": True/False
               }
           """
           
           prompt = self._build_evaluation_prompt(query, context, answer)
           
           response = await self.ollama.generate(
               model="llama3.2:latest",
               prompt=prompt,
               temperature=0.2  # Niedrig für konsistente Bewertung
           )
           
           evaluation = json.loads(response)
           
           # Add refinement_needed flag
           avg_score = (
               evaluation['context_relevance'] +
               evaluation['groundedness'] +
               evaluation['answer_relevance']
           ) / 3
           
           evaluation['refinement_needed'] = avg_score < 0.7
           
           return evaluation
       
       def _build_evaluation_prompt(self, query, context, answer):
           return f"""
Du bist ein kritischer Qualitäts-Evaluator für RAG-Systeme.

Bewerte die folgende Antwort nach drei Kriterien (0.0-1.0):

**Frage:** {query}

**Kontext (Quellen):**
{context}

**Antwort:**
{answer}

**Bewertungskriterien:**

1. **Context Relevance (0.0-1.0):**
   - Ist der bereitgestellte Kontext relevant für die Frage?
   - Sind die Quellen hilfreich oder irrelevant?

2. **Groundedness / Faithfulness (0.0-1.0):**
   - Basiert die Antwort NUR auf dem Kontext?
   - Gibt es Halluzinationen (erfundene Fakten)?

3. **Answer Relevance (0.0-1.0):**
   - Beantwortet die Antwort die Frage direkt?
   - Ist sie fokussiert oder schweift sie ab?

**WICHTIG:** Antworte NUR mit valid JSON (kein Text davor/danach):

{{
  "context_relevance": 0.X,
  "groundedness": 0.X,
  "answer_relevance": 0.X,
  "feedback": "Kurze Begründung (2-3 Sätze)",
  "halluzination_detected": true/false,
  "suggested_improvement": "Optional: Was könnte verbessert werden?"
}}
"""
   ```

2. **Integration in Workflow**
   ```python
   # Im LangGraph Workflow
   
   async def evaluator_agent(state: VeritasAgentState):
       """Node: Evaluiert die Agent-Ergebnisse"""
       
       evaluator = EvaluatorAgent(ollama_client)
       
       # Kombiniere alle Agent-Antworten
       context = "\n\n".join([
           f"[Agent {r.agent_type}]: {r.response_text}"
           for r in state['agent_results']
       ])
       
       # Letzte Antwort (Synthesis)
       answer = state['agent_results'][-1].response_text
       
       # Evaluate
       evaluation = await evaluator.evaluate_rag_triade(
           query=state['query'],
           context=context,
           answer=answer
       )
       
       # Update State
       return {
           "evaluation": evaluation,
           "refinement_count": state['refinement_count'] + 1
       }
   ```

**Deliverables:**
- ✅ `veritas_evaluator_agent.py` - Evaluator Implementation
- ✅ RAG-Triade Prompts (Few-Shot Examples)
- ✅ Integration in LangGraph Workflow
- ✅ Evaluation Metrics Logging
- ✅ Unit Tests

---

### Phase 2: Datenquellen-Erweiterung (4-6 Wochen) 🟡 WICHTIG

#### Sprint 2.1: Neo4j Graph Database Agent (2 Wochen)

**Tasks:**
1. **Neo4j Setup (Docker)**
   ```yaml
   # docker-compose.yml
   services:
     neo4j:
       image: neo4j:5.13
       ports:
         - "7474:7474"  # Browser
         - "7687:7687"  # Bolt
       environment:
         NEO4J_AUTH: neo4j/veritas123
       volumes:
         - neo4j_data:/data
   ```

2. **Graph Agent Implementation**
   ```python
   # backend/agents/veritas_neo4j_agent.py
   
   from langchain.chains.graph_qa.cypher import GraphCypherQAChain
   from langchain_community.graphs import Neo4jGraph
   
   class Neo4jAgent:
       def __init__(self):
           self.graph = Neo4jGraph(
               url="bolt://localhost:7687",
               username="neo4j",
               password="veritas123"
           )
           
           self.qa_chain = GraphCypherQAChain.from_llm(
               llm=ollama_llm,
               graph=self.graph,
               verbose=True
           )
       
       async def query(self, question: str) -> Dict[str, Any]:
           """
           Beantwortet Fragen über Beziehungen/Netzwerke
           
           Beispiele:
           - "Welche Abteilungen arbeiten an Projekt X?"
           - "Wer sind die Experten für Thema Y?"
           - "Welche Projekte sind mit Technologie Z verbunden?"
           """
           
           result = await self.qa_chain.arun(question)
           
           return {
               "agent": "Neo4jAgent",
               "answer": result,
               "sources": ["Neo4j Graph Database"],
               "confidence": 0.9
           }
   ```

3. **Integration in SupervisorAgent**
   ```python
   # Registriere Neo4j Agent
   self.agents['neo4j'] = Neo4jAgent()
   
   # Agent Selector erkennt Graph-Queries
   if self._is_relationship_query(query):
       selected_agents.append('neo4j')
   ```

**Deliverables:**
- ✅ Neo4j Docker Setup
- ✅ `veritas_neo4j_agent.py`
- ✅ Sample Graph Data (Testdaten)
- ✅ Integration in SupervisorAgent
- ✅ Tests

---

#### Sprint 2.2: SearxNG Web Search Agent (2 Wochen)

**Tasks:**
1. **SearxNG Setup (Docker)**
   ```yaml
   # docker-compose.yml
   services:
     searxng:
       image: searxng/searxng:latest
       ports:
         - "8080:8080"
       volumes:
         - ./searxng:/etc/searxng
       environment:
         - SEARXNG_BASE_URL=http://localhost:8080
   ```

2. **Web Search Agent**
   ```python
   # backend/agents/veritas_web_search_agent.py
   
   import aiohttp
   
   class SearxNGAgent:
       def __init__(self):
           self.base_url = "http://localhost:8080"
       
       async def search(self, query: str, num_results: int = 5):
           """
           Sucht im Web über SearxNG (On-Premise!)
           
           Vorteile:
           - Keine Weitergabe von Queries an Google/Bing
           - Aggregiert Ergebnisse von 100+ Suchmaschinen
           - Datenschutzkonform
           """
           
           async with aiohttp.ClientSession() as session:
               async with session.get(
                   f"{self.base_url}/search",
                   params={
                       "q": query,
                       "format": "json",
                       "engines": "google,bing,duckduckgo"
                   }
               ) as resp:
                   data = await resp.json()
           
           results = []
           for item in data.get('results', [])[:num_results]:
               results.append({
                   "title": item['title'],
                   "url": item['url'],
                   "snippet": item['content']
               })
           
           return {
               "agent": "SearxNGAgent",
               "results": results,
               "sources": [r['url'] for r in results]
           }
   ```

**Deliverables:**
- ✅ SearxNG Docker Setup
- ✅ `veritas_web_search_agent.py`
- ✅ Privacy-Config (keine Logs)
- ✅ Integration in SupervisorAgent
- ✅ Tests

---

### Phase 3: Kryptographische Integrität (2-4 Wochen) 🟡 COMPLIANCE

#### Sprint 3.1: Hash-Kette + Signaturen (2 Wochen)

**Tasks:**
1. **Hash-Kette Implementation**
   ```python
   # backend/agents/veritas_integrity_manager.py
   
   import hashlib
   import json
   from cryptography.hazmat.primitives import hashes, serialization
   from cryptography.hazmat.primitives.asymmetric import rsa, padding
   
   class IntegrityManager:
       def __init__(self):
           self.private_key = self._load_or_generate_key()
       
       def compute_state_hash(self, execution_trace: List[Dict]) -> str:
           """
           Berechnet SHA-256 Hash über execution_trace
           """
           trace_json = json.dumps(execution_trace, sort_keys=True)
           hash_obj = hashlib.sha256(trace_json.encode('utf-8'))
           return hash_obj.hexdigest()
       
       def sign_state(self, state_hash: str) -> str:
           """
           Signiert Hash mit privatem Schlüssel
           """
           signature = self.private_key.sign(
               state_hash.encode('utf-8'),
               padding.PSS(
                   mgf=padding.MGF1(hashes.SHA256()),
                   salt_length=padding.PSS.MAX_LENGTH
               ),
               hashes.SHA256()
           )
           return signature.hex()
       
       def verify_integrity(self, state: ResearchState) -> bool:
           """
           Verifiziert Hash-Kette + Signatur
           """
           # 1. Check hash chain
           for i in range(1, len(state['execution_trace'])):
               prev_hash = self.compute_state_hash(
                   state['execution_trace'][:i]
               )
               
               if state['integrity_chain'][i-1] != prev_hash:
                   return False  # Manipulation detected!
           
           # 2. Verify signature
           current_hash = self.compute_state_hash(state['execution_trace'])
           return self._verify_signature(
               current_hash, 
               state['integrity']['stateSignature']
           )
   ```

2. **Integration in State Persister**
   ```python
   async def save_state(self, research_id, state):
       # Compute hash
       current_hash = self.integrity.compute_state_hash(
           state['execution_trace']
       )
       
       # Update integrity block
       state['integrity'] = {
           "currentStateHash": current_hash,
           "previousStateHash": state['integrity'].get('currentStateHash'),
           "stateSignature": self.integrity.sign_state(current_hash)
       }
       
       # Save
       await self.db.execute(...)
   ```

**Deliverables:**
- ✅ `veritas_integrity_manager.py`
- ✅ RSA Key Generation
- ✅ Hash-Kette Validation
- ✅ Integration in Persister
- ✅ Tests

---

#### Sprint 3.2: Qualifizierte Zeitstempel (2 Wochen) - OPTIONAL

**Tasks:**
1. **TSP Client Implementation**
   ```python
   # backend/agents/veritas_timestamp_client.py
   
   import requests
   from rfc3161ng import RemoteTimestamper
   
   class QualifiedTimestampClient:
       def __init__(self):
           # eIDAS-zertifizierter TSP (Beispiel: Deutsche Telekom)
           self.tsp_url = "https://tsp.telekom.de/timestamp"
           self.timestamper = RemoteTimestamper(
               self.tsp_url,
               certificate="telekom_tsp.crt"
           )
       
       async def get_timestamp(self, data_hash: str) -> str:
           """
           Holt qualifizierten Zeitstempel (QET)
           
           Rechtliche Wirkung (eIDAS):
           - EU-weite Beweiskraft
           - Vermutung der Richtigkeit
           - Gerichtlich verwertbar
           """
           
           timestamp_token = self.timestamper(
               data=data_hash.encode('utf-8'),
               hashname='sha256'
           )
           
           return timestamp_token.hex()
   ```

2. **Integration für finale States**
   ```python
   async def finalize_research(self, research_id):
       state = await self.load_state(research_id)
       
       # Sign
       final_hash = self.integrity.compute_state_hash(
           state['execution_trace']
       )
       signature = self.integrity.sign_state(final_hash)
       
       # Timestamp
       timestamp_token = await self.tsp.get_timestamp(final_hash)
       
       state['integrity']['qualifiedTimestampToken'] = timestamp_token
       state['status'] = 'COMPLETED_AND_SEALED'
       
       await self.save_state(research_id, state)
   ```

**Deliverables:**
- ✅ `veritas_timestamp_client.py`
- ✅ TSP Provider Integration
- ✅ Certificate Management
- ✅ Tests

---

### Phase 4: Prefect Macro-Orchestrierung (4-6 Wochen) 🟢 OPTIONAL

**Nur wenn Multi-Stunden-Workflows benötigt werden!**

#### Sprint 4.1: Prefect Setup (2 Wochen)

**Tasks:**
1. **Prefect Installation**
   ```bash
   pip install prefect
   prefect server start
   ```

2. **Workflow Definition**
   ```python
   # backend/workflows/deep_research_workflow.py
   
   from prefect import flow, task
   from prefect.task_runners import ConcurrentTaskRunner
   
   @task(retries=3, retry_delay_seconds=60)
   async def execute_research_phase(research_id: str, phase: str):
       """
       Eine Phase der Recherche (mit Auto-Retry!)
       """
       response = await requests.post(
           "http://localhost:5000/api/research/execute",
           json={"research_id": research_id, "phase": phase}
       )
       return response.json()
   
   @flow(name="Deep Research", task_runner=ConcurrentTaskRunner())
   async def deep_research_flow(query: str):
       """
       Langlebiger Deep Research Workflow
       
       Vorteile:
       - Läuft über Stunden/Tage
       - Automatische Retries bei Fehlern
       - Human-in-the-Loop Checkpoints
       - Zentrale Überwachung
       """
       
       # Phase 1: Initial Research
       research_id = await init_research(query)
       
       # Phase 2: Data Collection (parallelisiert)
       results = await execute_research_phase.map([
           (research_id, "web_search"),
           (research_id, "database_query"),
           (research_id, "graph_analysis")
       ])
       
       # Phase 3: Human Review (pausiert Workflow!)
       await human_review_checkpoint(research_id)
       
       # Phase 4: Synthesis
       final_result = await synthesize_results(research_id)
       
       return final_result
   ```

**Deliverables:**
- ✅ Prefect Server Setup
- ✅ `deep_research_workflow.py`
- ✅ Retry-Strategien
- ✅ Human-Checkpoints
- ✅ Monitoring Dashboard

---

## 📋 Zusammenfassung: Implementierungs-Roadmap

| Phase | Dauer | Priorität | Status | Deliverables |
|-------|-------|-----------|--------|--------------|
| **Phase 1: Foundation** | 4-6 Wochen | 🔴 P0 | ⏳ Pending | Persistentes JSON, LangGraph, Evaluator |
| **Phase 2: Datenquellen** | 4-6 Wochen | 🟡 P1 | ⏳ Pending | Neo4j, SearxNG |
| **Phase 3: Integrität** | 2-4 Wochen | 🟡 P2 | ⏳ Pending | Hash-Kette, Signaturen, Zeitstempel |
| **Phase 4: Prefect** | 4-6 Wochen | 🟢 P3 | ⏳ Optional | Macro-Orchestrierung |

**Gesamt-Zeitrahmen:**
- **Minimum (Phase 1+2):** 8-12 Wochen (2-3 Monate)
- **Empfohlen (Phase 1+2+3):** 10-16 Wochen (2.5-4 Monate)
- **Komplett (alle Phasen):** 14-22 Wochen (3.5-5.5 Monate)

---

## 🎯 Erfolgs-Kriterien

### MVP (Minimum Viable Product)

Nach **Phase 1** (4-6 Wochen):

✅ **Funktional:**
- Persistente Recherchen (wiederaufsetzbar)
- LangGraph StateGraph (zustandsbehaftet)
- Evaluator-Agent (Qualitätssicherung)
- Reflexions-Schleife (iterative Verbesserung)

✅ **Technisch:**
- PostgreSQL State Persistence
- LangGraph Checkpointer
- RAG-Triade Evaluation
- Execution Trace Logging

✅ **Messbar:**
- Erfolgsrate: 80%+ (mit Reflexion vs. 60% ohne)
- Durchschnittliche Refinements: 1-2 pro Recherche
- Crash-Wiederaufsetzbarkeit: 100%

### Production-Ready

Nach **Phase 1+2+3** (10-16 Wochen):

✅ **Enterprise-Grade:**
- Neo4j Graph Queries
- SearxNG Web Search (privacy-compliant)
- Kryptographische Integrität
- Audit-Trail (rechtssicher)

✅ **Compliance:**
- DSGVO-konform
- Nachvollziehbar
- Manipulationssicher
- Optional: eIDAS-QET

---

**Ende des Implementierungskonzepts**
