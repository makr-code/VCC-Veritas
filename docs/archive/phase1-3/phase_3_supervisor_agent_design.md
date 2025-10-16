# Phase 3: Supervisor-Agent Pattern - Design Dokument

**Version:** 1.0  
**Status:** Design Phase  
**Datum:** 06.10.2025  
**Inspiriert von:** AWS Agents for Bedrock Multi-Agent Collaboration, Azure Semantic Kernel Planner

---

## 🎯 **Übersicht**

Der **Supervisor-Agent** ist die zentrale Orchestrierungsinstanz für komplexe Multi-Agent-Workflows im VERITAS-System. Er übernimmt die intelligente Zerlegung komplexer Queries, die optimale Auswahl von Spezial-Agents und die Synthese von Teilergebnissen zu kohärenten Antworten.

### **Kernverantwortlichkeiten**

1. **Query Decomposition** - Zerlegung komplexer Anfragen in atomare Subqueries
2. **Agent Selection** - Intelligente Auswahl passender Spezial-Agents (Environmental, Construction, Financial, etc.)
3. **Orchestration** - Koordination paralleler und sequenzieller Agent-Execution
4. **Result Synthesis** - Aggregation und Konfliktauflösung von Teilergebnissen

---

## 🏗️ **Architektur-Übersicht**

```
┌─────────────────────────────────────────────────────────┐
│            SUPERVISOR AGENT WORKFLOW                     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │   1. QUERY DECOMPOSITION          │
        │   LLM-basierte Zerlegung          │
        │   → List[SubQuery]                │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │   2. AGENT SELECTION              │
        │   Capability-Matching             │
        │   → Agent-Plan mit Prioritäten    │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │   3. ORCHESTRATION                │
        │   Parallel + Sequenziell          │
        │   → Agent-Execution mit Deps      │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │   4. RESULT SYNTHESIS             │
        │   Aggregation + Deduplizierung    │
        │   → Kohärente Antwort             │
        └───────────────────────────────────┘
```

---

## 📦 **Komponenten-Design**

### **1. QueryDecomposer**

**Verantwortlichkeit:** Zerlegt komplexe Queries in unabhängige Subqueries

**Input:**
```python
complex_query = "Wie ist die Luftqualität in München und welche Behörden sind für Umweltschutz zuständig?"
user_context = {"location": "München", "user_type": "citizen"}
```

**Output:**
```python
[
    SubQuery(
        id="sq_001",
        query_text="Aktuelle Luftqualitätswerte für München",
        query_type="environmental_data",
        priority=1.0,
        dependencies=[],
        required_capabilities=["air_quality_monitoring", "environmental_data"],
        metadata={"location": "München"}
    ),
    SubQuery(
        id="sq_002",
        query_text="Zuständige Behörden für Umweltschutz in München",
        query_type="authority_mapping",
        priority=0.8,
        dependencies=[],
        required_capabilities=["authority_finder", "administrative_structure"],
        metadata={"location": "München", "domain": "environmental"}
    )
]
```

**LLM Prompt Template:**
```python
DECOMPOSITION_PROMPT = """
Du bist ein Query-Decomposer für ein deutsches Verwaltungs-KI-System.

**Aufgabe:** Zerlege die komplexe User-Query in atomare Subqueries.

**Regeln:**
1. Jede Subquery sollte von EINEM Spezial-Agent beantwortet werden können
2. Identifiziere Abhängigkeiten zwischen Subqueries (Execution-Order)
3. Vergib Prioritäten (1.0 = höchste Priorität)
4. Ordne passende Agent-Capabilities zu

**Input Query:** {query_text}
**User Context:** {user_context}

**Output Format (JSON):**
[
    {{
        "query_text": "...",
        "query_type": "environmental_data | authority_mapping | legal_framework | ...",
        "priority": 0.0-1.0,
        "dependencies": ["sq_id_1", ...],
        "required_capabilities": ["capability_1", ...]
    }},
    ...
]
"""
```

**Algorithmus:**
```python
async def decompose_query(self, query_text: str, user_context: Dict[str, Any]) -> List[SubQuery]:
    """
    Zerlegt komplexe Query in Subqueries
    
    Workflow:
    1. LLM-basierte Analyse der Query-Komplexität
    2. Identifikation logisch unabhängiger Teilfragen
    3. Dependency-Graph erstellen (DAG)
    4. Capability-Matching für jede Subquery
    5. Prioritäten basierend auf User-Intent
    """
    # LLM Call
    llm_response = await self.ollama_client.generate(
        prompt=DECOMPOSITION_PROMPT.format(
            query_text=query_text,
            user_context=json.dumps(user_context, indent=2)
        ),
        model="llama3.2:3b",
        format="json"
    )
    
    # Parse JSON
    subqueries_data = json.loads(llm_response)
    
    # Validierung & Dependency-Check
    subqueries = []
    for idx, sq_data in enumerate(subqueries_data):
        subquery = SubQuery(
            id=f"sq_{uuid.uuid4().hex[:8]}",
            query_text=sq_data["query_text"],
            query_type=sq_data.get("query_type", "general"),
            priority=float(sq_data.get("priority", 0.5)),
            dependencies=sq_data.get("dependencies", []),
            required_capabilities=sq_data.get("required_capabilities", []),
            metadata={
                "original_query": query_text,
                "decomposition_index": idx
            }
        )
        subqueries.append(subquery)
    
    # Dependency-Validierung (keine zyklischen Dependencies)
    if not self._validate_dependency_graph(subqueries):
        logger.warning("⚠️ Zyklische Dependencies erkannt - Fallback auf flache Liste")
        for sq in subqueries:
            sq.dependencies = []
    
    return subqueries
```

---

### **2. AgentSelector**

**Verantwortlichkeit:** Wählt optimale Spezial-Agents basierend auf Subquery-Requirements

**Input:**
```python
subquery = SubQuery(
    query_text="Aktuelle Luftqualitätswerte für München",
    required_capabilities=["air_quality_monitoring", "environmental_data"]
)
```

**Output:**
```python
AgentSelection(
    subquery_id="sq_001",
    selected_agents=[
        AgentAssignment(
            agent_type="environmental",
            agent_id="env_agent_001",
            confidence_score=0.95,
            matching_capabilities=["air_quality_monitoring", "environmental_data"],
            priority=1.0,
            reason="Perfektes Capability-Match für Luftqualitätsdaten"
        )
    ],
    fallback_agents=[
        AgentAssignment(
            agent_type="general_knowledge",
            confidence_score=0.4,
            reason="Fallback für generische Umweltinformationen"
        )
    ]
)
```

**Capability-Matching-Matrix:**

| Agent Type           | Capabilities                                                      |
|---------------------|-------------------------------------------------------------------|
| `environmental`      | `air_quality_monitoring`, `water_quality`, `environmental_data`   |
| `construction`       | `building_permits`, `zoning_regulations`, `construction_law`      |
| `financial`          | `budgets`, `subsidies`, `public_spending`, `financial_reports`    |
| `social`             | `demographics`, `social_services`, `education_data`               |
| `traffic`            | `traffic_flow`, `parking`, `public_transport`                     |
| `authority_mapping`  | `administrative_structure`, `contact_finder`, `jurisdiction`      |
| `legal_framework`    | `law_retrieval`, `regulation_interpretation`, `legal_precedents`  |

**Algorithmus:**
```python
async def select_agents(self, subquery: SubQuery, rag_context: Dict[str, Any]) -> AgentSelection:
    """
    Wählt optimale Agents für Subquery
    
    Matching-Strategien:
    1. Exact Capability Match (Score: 1.0)
    2. Partial Match (Score: 0.5-0.9)
    3. RAG-Hint Match (Score: 0.3-0.7)
    4. Fallback to General Agent (Score: 0.2)
    """
    matches: List[AgentAssignment] = []
    
    # 1. Capability-basiertes Matching
    for agent_type, capabilities in AGENT_CAPABILITY_MAP.items():
        match_score = self._calculate_capability_overlap(
            subquery.required_capabilities,
            capabilities
        )
        
        if match_score > 0.5:
            matches.append(AgentAssignment(
                agent_type=agent_type,
                confidence_score=match_score,
                matching_capabilities=list(set(subquery.required_capabilities) & set(capabilities)),
                reason=f"Capability Match Score: {match_score:.2f}"
            ))
    
    # 2. RAG-Context-Boosting
    if rag_context:
        rag_documents = rag_context.get("documents", [])
        for doc in rag_documents:
            if "environmental" in doc.get("metadata", {}).get("domain", ""):
                # Boost Environmental Agent
                for match in matches:
                    if match.agent_type == "environmental":
                        match.confidence_score = min(1.0, match.confidence_score + 0.2)
                        match.reason += " + RAG-Context-Boost"
    
    # 3. Sortierung nach Confidence
    matches.sort(key=lambda m: m.confidence_score, reverse=True)
    
    # 4. Top-Agent + Fallbacks
    selected = matches[:1] if matches else []
    fallbacks = matches[1:3] if len(matches) > 1 else []
    
    return AgentSelection(
        subquery_id=subquery.id,
        selected_agents=selected,
        fallback_agents=fallbacks
    )
```

---

### **3. ResultSynthesizer**

**Verantwortlichkeit:** Aggregiert Teilergebnisse zu kohärenter Antwort

**Input:**
```python
agent_results = [
    AgentResult(
        subquery_id="sq_001",
        agent_type="environmental",
        result_data={
            "luftqualität": "gut",
            "pm10_wert": 25,
            "no2_wert": 18,
            "quelle": "Bayerisches Landesamt für Umwelt"
        },
        confidence_score=0.95
    ),
    AgentResult(
        subquery_id="sq_002",
        agent_type="authority_mapping",
        result_data={
            "zuständige_behörden": [
                {"name": "Referat für Gesundheit und Umwelt", "kontakt": "..."},
                {"name": "Bayerisches Landesamt für Umwelt", "kontakt": "..."}
            ]
        },
        confidence_score=0.88
    )
]
```

**Output:**
```python
SynthesizedResult(
    response_text="""
    Die Luftqualität in München ist aktuell gut. Die Messwerte zeigen:
    - PM10: 25 µg/m³
    - NO2: 18 µg/m³
    
    Zuständige Behörden für Umweltschutz in München:
    1. Referat für Gesundheit und Umwelt (Kontakt: ...)
    2. Bayerisches Landesamt für Umwelt (Kontakt: ...)
    
    Quelle: Bayerisches Landesamt für Umwelt
    """,
    confidence_score=0.92,
    sources=[...],
    subquery_coverage={
        "sq_001": 0.95,
        "sq_002": 0.88
    },
    conflicts_detected=[],
    synthesis_method="llm_narrative_generation"
)
```

**Synthese-Strategien:**

1. **LLM-basierte Narrative Generation** (DEFAULT)
   - Nutzt Ollama LLM um natürliche Antwort zu generieren
   - Input: Alle Agent-Ergebnisse als strukturierter Kontext
   - Output: Kohärente, lesbare Antwort in natürlicher Sprache

2. **Template-basierte Aggregation** (FALLBACK)
   - Nutzt vordefinierte Templates für Standard-Query-Typen
   - Schneller aber weniger flexibel

3. **Konflikt-Auflösung:**
   - **Contradiction Detection:** Identifiziert widersprüchliche Aussagen
   - **Confidence-based Priority:** Höhere Confidence-Scores gewinnen
   - **Source-Voting:** Bei gleichwertigen Scores entscheidet Quellenqualität

**Algorithmus:**
```python
async def synthesize_results(self, 
                             agent_results: List[AgentResult],
                             original_query: str) -> SynthesizedResult:
    """
    Aggregiert Agent-Ergebnisse zu kohärenter Antwort
    
    Workflow:
    1. Konflikt-Detektion zwischen Agent-Antworten
    2. Deduplizierung redundanter Informationen
    3. LLM-basierte Narrative-Generierung
    4. Confidence-Scoring der finalen Antwort
    """
    
    # 1. Konflikt-Detektion
    conflicts = self._detect_contradictions(agent_results)
    if conflicts:
        logger.warning(f"⚠️ {len(conflicts)} Konflikte erkannt - starte Auflösung")
        agent_results = self._resolve_conflicts(agent_results, conflicts)
    
    # 2. Deduplizierung
    deduplicated = self._deduplicate_information(agent_results)
    
    # 3. LLM Synthesis
    synthesis_prompt = SYNTHESIS_PROMPT.format(
        original_query=original_query,
        agent_results=json.dumps([r.to_dict() for r in deduplicated], indent=2)
    )
    
    synthesized_text = await self.ollama_client.generate(
        prompt=synthesis_prompt,
        model="llama3.2:3b",
        temperature=0.3  # Niedriger für faktische Genauigkeit
    )
    
    # 4. Confidence-Berechnung
    avg_confidence = sum(r.confidence_score for r in deduplicated) / len(deduplicated)
    
    return SynthesizedResult(
        response_text=synthesized_text,
        confidence_score=avg_confidence,
        sources=self._extract_sources(deduplicated),
        subquery_coverage={r.subquery_id: r.confidence_score for r in deduplicated},
        conflicts_detected=conflicts,
        synthesis_method="llm_narrative_generation"
    )
```

---

## 🔄 **Integration mit bestehender Pipeline**

### **Vor Supervisor-Agent (Status Quo):**
```python
# veritas_intelligent_pipeline.py - STEP 3: Agent Selection
selected_agents = ["environmental", "authority_mapping", "legal_framework"]
# Statische Selektion basierend auf Heuristiken
```

### **Nach Supervisor-Agent:**
```python
# veritas_supervisor_agent.py - Intelligente Multi-Phase-Orchestration
supervisor = SupervisorAgent(ollama_client, agent_registry)

# Phase 1: Query Decomposition
subqueries = await supervisor.decompose_query(request.query_text, request.user_context)

# Phase 2: Agent Selection pro Subquery
agent_plan = await supervisor.create_agent_plan(subqueries, rag_context)

# Phase 3: Orchestration mit Dependencies
results = await supervisor.orchestrate_execution(agent_plan)

# Phase 4: Result Synthesis
final_answer = await supervisor.synthesize_results(results, request.query_text)
```

---

## 📐 **Datenstrukturen**

### **SubQuery**
```python
@dataclass
class SubQuery:
    """Atomare Teilfrage aus Query Decomposition"""
    id: str
    query_text: str
    query_type: str  # "environmental_data", "authority_mapping", etc.
    priority: float  # 0.0 - 1.0
    dependencies: List[str]  # IDs anderer SubQueries
    required_capabilities: List[str]  # ["air_quality", "environmental_data"]
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### **AgentAssignment**
```python
@dataclass
class AgentAssignment:
    """Zuordnung Agent → Subquery"""
    agent_type: str
    agent_id: Optional[str] = None
    confidence_score: float = 0.0
    matching_capabilities: List[str] = field(default_factory=list)
    priority: float = 1.0
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### **SynthesizedResult**
```python
@dataclass
class SynthesizedResult:
    """Finales Ergebnis nach Result-Synthese"""
    response_text: str
    confidence_score: float
    sources: List[Dict[str, Any]]
    subquery_coverage: Dict[str, float]  # subquery_id → coverage_score
    conflicts_detected: List[Dict[str, Any]]
    synthesis_method: str  # "llm_narrative" | "template_based"
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## 🧪 **Testing-Strategie**

### **Unit-Tests**

1. **test_query_decomposition.py**
   ```python
   def test_simple_query_no_decomposition():
       # "Wer ist zuständig für X?" → 1 Subquery
       
   def test_complex_query_with_dependencies():
       # "Vergleiche X und Y" → 2 Subqueries mit Dependencies
       
   def test_multi_domain_query():
       # Environmental + Legal + Financial → 3 Domains
   ```

2. **test_agent_selection.py**
   ```python
   def test_exact_capability_match():
       # Subquery mit "air_quality" → Environmental Agent
       
   def test_partial_capability_match():
       # Subquery mit "environmental_data" → 2 Candidates
       
   def test_rag_context_boosting():
       # RAG liefert "environmental" docs → Boost Env Agent
   ```

3. **test_result_synthesis.py**
   ```python
   def test_conflict_detection():
       # Agent A sagt "gut", Agent B sagt "schlecht"
       
   def test_deduplication():
       # 2 Agents liefern identische Fakten
       
   def test_llm_synthesis():
       # Multi-Agent-Ergebnisse → Kohärente Narrative
   ```

### **Integration-Tests**

```python
async def test_supervisor_end_to_end():
    supervisor = SupervisorAgent(ollama_client, agent_registry)
    
    query = "Wie ist die Luftqualität in München und welche Behörden sind zuständig?"
    
    # Decomposition
    subqueries = await supervisor.decompose_query(query, {})
    assert len(subqueries) == 2
    
    # Selection
    agent_plan = await supervisor.create_agent_plan(subqueries, {})
    assert "environmental" in [a.agent_type for a in agent_plan.assignments]
    
    # Orchestration (Mock)
    mock_results = [...]
    
    # Synthesis
    final = await supervisor.synthesize_results(mock_results, query)
    assert final.confidence_score > 0.7
    assert "Luftqualität" in final.response_text
    assert "Behörden" in final.response_text
```

---

## 📊 **Performance-Metriken**

| Metrik                          | Target        | Beschreibung                               |
|--------------------------------|---------------|--------------------------------------------|
| **Decomposition Latency**      | < 2s          | Zeit für LLM-basierte Query-Zerlegung     |
| **Agent Selection Accuracy**   | > 90%         | Korrekte Agent-Auswahl für Capability     |
| **Synthesis Quality (Human)**  | > 4.0/5.0     | Manuelle Bewertung der Antwortqualität    |
| **Conflict Resolution Rate**   | > 95%         | Erfolgreiche Auflösung von Widersprüchen  |
| **End-to-End Latency**         | < 30s         | Gesamtzeit für komplexe Multi-Agent-Query |

---

## 🚀 **Implementierungs-Roadmap**

### **Phase 3.1: Core Components** (3-4 Tage)
- [ ] `backend/agents/veritas_supervisor_agent.py` - Hauptklasse
- [ ] `backend/agents/supervisor/query_decomposer.py` - Decomposition Logic
- [ ] `backend/agents/supervisor/agent_selector.py` - Selection Logic
- [ ] `backend/agents/supervisor/result_synthesizer.py` - Synthesis Logic
- [ ] Datenstrukturen: `SubQuery`, `AgentAssignment`, `SynthesizedResult`

### **Phase 3.2: Integration** (2 Tage)
- [ ] Integration mit `IntelligentMultiAgentPipeline`
- [ ] Supervisor als optionale Orchestrierungs-Schicht
- [ ] Backward-Compatibility für bestehende Workflows

### **Phase 3.3: Testing** (2 Tage)
- [ ] Unit-Tests für alle 3 Komponenten
- [ ] Integration-Tests mit Mock-Agents
- [ ] End-to-End-Test mit realen Agents

### **Phase 3.4: Evaluation** (1 Tag)
- [ ] Baseline vs. Supervisor Performance-Vergleich
- [ ] LLM-as-Judge für Synthesis-Qualität
- [ ] Latency-Profiling

---

## 🔗 **Referenzen**

- **AWS Agents for Bedrock:** Multi-Agent Collaboration Patterns
- **Azure Semantic Kernel:** Planner & Orchestrator Design
- **LangChain Multi-Agent:** Agent Supervisor Pattern
- **AutoGen:** Conversational Multi-Agent Framework

---

**Ende Design-Dokument**
