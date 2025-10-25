# VERITAS: Wissenschaftliches Pipeline-Konzept - Status & Analyse
**Datum:** 16. Oktober 2025  
**Analysiert von:** GitHub Copilot  
**Kontext:** Ursprüngliches wissenschaftliches Konzept vs. aktuelle Implementierung

---

## 🎯 Zusammenfassung

**JA**, das wissenschaftliche Pipeline-Konzept ist **noch vorhanden und aktiv**, allerdings mit **moderner Orchestrierung** ergänzt:

- ✅ **Hypothesen-Generierung** (HypothesisService)
- ✅ **Stage-Reflection-System** (Meta-Analyse pro Pipeline-Stage)
- ✅ **Synthesis-Phase** (Ergebnis-Aggregation)
- ✅ **Validation** (Qualitäts-Checks)
- ⚠️ **Agent-Orchestrierung** ergänzt die wissenschaftliche Methode (nicht ersetzt!)

---

## 📊 Wissenschaftliche Methode: Soll-Konzept (Ursprung)

### Klassischer Wissenschaftlicher Workflow

```
1. HYPOTHESE
   ↓
2. INFORMATIONSBESCHAFFUNG (RAG/Agents)
   ↓
3. ANALYSE & VERGLEICH
   ↓
4. SYNTHESE
   ↓
5. VALIDIERUNG
   ↓
6. KONKLUSION
```

**Ziel:** Strukturierte, nachvollziehbare Antwort-Generierung nach wissenschaftlichen Prinzipien.

---

## 🔍 Aktuelle Implementierung: Ist-Zustand

### 1. **HypothesisService** (✅ Implementiert)

**Datei:** `backend/services/hypothesis_service.py`

```python
class HypothesisService:
    """
    Generiert strukturierte Hypothesen über Query-Intent
    
    Features:
    - LLM-basierte Intent-Analyse
    - Information Gap Identification
    - Confidence Scoring
    - Clarification Questions
    """
    
    def generate_hypothesis(query, rag_context) -> Hypothesis:
        """
        Analysiert Query und generiert Hypothese:
        
        Returns:
            Hypothesis:
                - question_type: QuestionType (FACTUAL, PROCEDURAL, etc.)
                - confidence: ConfidenceLevel (HIGH, MEDIUM, LOW)
                - information_gaps: List[InformationGap]
                - assumptions: List[str]
                - clarification_questions: List[str]
        """
```

**Status:** ✅ Voll funktionsfähig mit Ollama LLM

**Prompt-Template:** `backend/prompts/hypothesis_prompt.txt`

**Beispiel-Output:**
```json
{
  "question_type": "PROCEDURAL",
  "confidence": "LOW",
  "information_gaps": [
    {
      "gap_type": "location",
      "severity": "critical",
      "description": "Stadt/Bundesland nicht angegeben",
      "suggestions": ["In welcher Stadt soll gebaut werden?"]
    }
  ],
  "assumptions": ["Nutzer plant Wohngebäude"],
  "clarification_questions": ["Welches Bundesland?", "Welche Gebäudeart?"]
}
```

---

### 2. **StageReflectionService** (✅ Implementiert)

**Datei:** `backend/services/stage_reflection_service.py`

**Dual-Prompt-System:**
1. **User Query Prompt** → Primäre Verarbeitung
2. **Meta-Reflection Prompt** → Fortschritts-Analyse pro Stage

```python
class ReflectionStage(Enum):
    HYPOTHESIS = "hypothesis"           # ← Wissenschaftliche Phase 1
    AGENT_SELECTION = "agent_selection"  # ← Informationsbeschaffung
    RETRIEVAL = "retrieval"              # ← Datensammlung
    SYNTHESIS = "synthesis"              # ← Wissenschaftliche Phase 4
    VALIDATION = "validation"            # ← Wissenschaftliche Phase 5

class StageReflection:
    """Meta-Analyse für Pipeline-Stage"""
    completion_percent: float       # 0-100% Erfüllungsgrad
    fulfillment_status: str         # incomplete/partial/complete
    identified_gaps: List[str]      # Was fehlt noch?
    gathered_info: List[str]        # Was wurde gefunden?
    confidence: float               # 0-1
    next_actions: List[str]         # Empfohlene nächste Schritte
    llm_reasoning: str              # LLM Begründung
```

**Features:**
- ✅ Erfüllungsgrad-Tracking (0-100%)
- ✅ Gap-Identifikation pro Stage
- ✅ Konfidenz-Scoring
- ✅ Nächste Schritte Empfehlungen
- ✅ LLM-gestützte Meta-Reflection

**Status:** ✅ Voll implementiert, wird in Streaming-Pipeline genutzt

---

### 3. **IntelligentMultiAgentPipeline** (✅ Hybrides System)

**Datei:** `backend/agents/veritas_intelligent_pipeline.py`

**Workflow:**

```python
async def process_intelligent_query(request):
    """
    WISSENSCHAFTLICHE PIPELINE MIT AGENT-ORCHESTRIERUNG
    
    Stages:
    1. Query Analysis (→ Hypothese implizit)
    2. RAG Search (→ Informationsbeschaffung)
    3. Agent Selection (→ Experten-Matching)
    4. Agent Execution (→ Parallele Informationsbeschaffung)
       ├─ Environmental Agent
       ├─ Legal Framework Agent
       ├─ Construction Agent
       └─ ...
    5. Result Aggregation (→ Synthese)
    6. LLM Synthesis (→ Konklusion)
    
    Optional:
    - LLM Commentary pro Step
    - Stage Reflection (Meta-Analyse)
    - Confidence Scoring
    """
```

**Pipeline-Steps (aus Code):**

```python
STEP_PROGRESS_MAPPING = {
    "query_analysis": ProgressStage.ANALYZING_QUERY,      # ← Hypothese
    "rag_search": ProgressStage.GATHERING_CONTEXT,        # ← Informationsbeschaffung
    "agent_selection": ProgressStage.SELECTING_AGENTS,    # ← Agent-Matching
    "agent_execution": ProgressStage.AGENT_PROCESSING,    # ← Parallele Analyse
    "result_aggregation": ProgressStage.SYNTHESIZING,     # ← Synthese
}
```

---

### 4. **Streaming-Backend Integration** (✅ Implementiert)

**Datei:** `backend/api/veritas_api_backend.py`

**Funktion:** `_process_streaming_query()`

```python
async def _process_streaming_query(session_id, query_id, request):
    """
    SSE-Stream mit wissenschaftlichen Stages:
    
    1. Query Analysis → Hypothese
       progress_manager.update_stage(ANALYZING_QUERY)
       
    2. (Optional) Hypothesis Reflection
       if enable_llm_thinking:
           hypothesis_reflection = await reflection_service.reflect_on_stage(
               stage=ReflectionStage.HYPOTHESIS,
               ...
           )
    
    3. Agent Selection → Informationsbeschaffung
       progress_manager.update_stage(SELECTING_AGENTS)
       
    4. Agent Execution → Parallele Analyse
       intelligent_pipeline._step_parallel_agent_execution()
       
    5. Context Gathering → Informationskonsolidierung
       progress_manager.update_stage(GATHERING_CONTEXT)
       
    6. LLM Reasoning (optional) → Meta-Analyse
       progress_manager.update_stage(LLM_REASONING)
       
    7. Synthesis → Konklusion
       progress_manager.update_stage(SYNTHESIZING)
       
    8. Finalization → Qualitätssicherung
       progress_manager.update_stage(FINALIZING)
    """
```

**Status:** ✅ Voll funktionsfähig, wissenschaftliche Stages sichtbar im Progress-Stream

---

## 🎨 Visualisierung: Aktueller Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  USER QUERY: "Welche Genehmigungen brauche ich für...?"    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: HYPOTHESIS (HypothesisService)                    │
│  ✓ Intent: PROCEDURAL                                       │
│  ✓ Gaps: [location, building_type]                          │
│  ✓ Confidence: LOW → Frage nach Ort/Typ                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
         ┌────────────────────────────────┐
         │  STAGE REFLECTION (Meta-LLM)   │
         │  Completion: 30%               │
         │  Gaps: Location, Details       │
         └────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2: INFORMATION GATHERING (RAG + Agents)              │
│  ✓ UDS3 Vector Search: [BauGB, VwVfG, LBO]                  │
│  ✓ Selected Agents: [Verwaltungsrecht, Genehmigung, ...]    │
└─────────────────────────────────────────────────────────────┘
                          ↓
         ┌────────────────────────────────┐
         │  STAGE REFLECTION              │
         │  Completion: 60%               │
         │  Gathered: Legal Docs          │
         └────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 3: PARALLEL AGENT EXECUTION                          │
│  ├─ VerwaltungsrechtAgent → BauGB, VwVfG                    │
│  ├─ GenehmigungsAgent → Fristen, Formulare                  │
│  ├─ ImmissionsschutzAgent → TA Luft, Grenzwerte             │
│  └─ BodenGewaesserschutzAgent → WHG, BBodSchG               │
└─────────────────────────────────────────────────────────────┘
                          ↓
         ┌────────────────────────────────┐
         │  STAGE REFLECTION              │
         │  Completion: 85%               │
         │  Retrieved: 4 Agent Results    │
         └────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 4: SYNTHESIS (LLM Aggregation)                       │
│  ✓ Combine Agent Results                                    │
│  ✓ Cross-reference Legal Frameworks                         │
│  ✓ Identify Contradictions                                  │
│  ✓ Generate Structured Response                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
         ┌────────────────────────────────┐
         │  STAGE REFLECTION              │
         │  Completion: 100%              │
         │  Status: COMPLETE              │
         └────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 5: VALIDATION (Quality Check)                        │
│  ✓ Confidence Score: 0.88                                   │
│  ✓ Source Coverage: 4/4 Agents                              │
│  ✓ Legal Accuracy: HIGH                                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  FINAL RESPONSE (Strukturierte Antwort)                     │
│  ✓ Genehmigungen: [Baugenehmigung, BImSchG-Genehmigung]     │
│  ✓ Fristen: 3 Monate (§10 BauGB)                            │
│  ✓ Unterlagen: [Bauzeichnungen, Standsicherheit, TA Luft]   │
│  ✓ Follow-up: ["Welches Bundesland?", "Gebäudegröße?"]      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 Wissenschaftliche Komponenten: Vergleich

| **Wissenschaftliche Phase** | **Ursprungskonzept** | **Aktuelle Implementierung** | **Status** |
|----------------------------|----------------------|------------------------------|------------|
| **1. Hypothese** | Explizite Hypothesen-Generierung | `HypothesisService` + LLM | ✅ Implementiert |
| **2. Informationsbeschaffung** | RAG-Search | UDS3 + Agent-Orchestrierung | ✅ Erweitert |
| **3. Analyse** | Manuelle Annotation | Parallele Agent-Execution | ✅ Automatisiert |
| **4. Synthese** | LLM-Aggregation | `_synthesize_final_response()` | ✅ Implementiert |
| **5. Validierung** | Confidence-Scoring | Stage Reflection + Quality Metrics | ✅ Implementiert |
| **6. Meta-Reflection** | (Nicht im Original) | `StageReflectionService` | ✅ NEU hinzugefügt |

---

## ⚠️ Unterschiede zum Ursprungskonzept

### Was wurde **erweitert**:

1. **Agent-Orchestrierung** (NEU)
   - Parallele Experten-Agents statt sequenzielle Verarbeitung
   - 14 spezialisierte Production-Agents (Immissionsschutz, Verwaltungsrecht, etc.)
   - ThreadPool-basierte parallele Execution

2. **Stage Reflection** (NEU)
   - Dual-Prompt-System: User Query + Meta-Reflection
   - Erfüllungsgrad-Tracking pro Stage (0-100%)
   - Gap-Identifikation in Echtzeit
   - LLM-gestützte Fortschritts-Analyse

3. **Streaming Progress** (NEU)
   - Server-Sent Events (SSE) für Real-time Updates
   - Frontend kann jeden Pipeline-Step live verfolgen
   - Progress-Messages mit wissenschaftlichen Stages

### Was **beibehalten** wurde:

1. ✅ **Hypothesen-Generierung** als erster Schritt
2. ✅ **Strukturierte Information Gaps**
3. ✅ **Confidence Scoring**
4. ✅ **Synthesis-Phase** zur Ergebnis-Aggregation
5. ✅ **Validation** als Quality Gate

### Was **fehlt** (optional):

- ❌ **Explizite Thesis-Antithesis-Synthese** (Dialektischer Ansatz)
  - Könnte ergänzt werden: Agent-Results als "Thesen", LLM identifiziert Widersprüche als "Antithesen", Synthese löst auf
- ❌ **Peer-Review-Mechanismus** (Multi-LLM Validation)
  - Könnte ergänzt werden: 2-3 LLMs bewerten unabhängig, Consensus-Bildung

---

## 📈 Nutzung in aktuellen Endpoints

### `/v2/query/stream` (Streaming)
```python
# Nutzt wissenschaftliche Stages:
1. query_analysis → Hypothese implizit
2. agent_selection → Informationsbeschaffung
3. agent_execution → Parallele Analyse
4. synthesis → Ergebnis-Aggregation
5. finalization → Validierung

# Optional: Stage Reflection bei enable_llm_thinking=True
```

### `/v2/intelligent/query` (Synchron)
```python
# Nutzt IntelligentMultiAgentPipeline
# Alle wissenschaftlichen Stages werden durchlaufen
# Konfidenz-Scoring im Response
```

### Integration mit HypothesisService
```python
# AKTUELL: Nicht direkt in Endpoints genutzt
# Hypothesis-Generierung ist separater Service

# MÖGLICHE INTEGRATION:
@app.post("/v2/hypothesis")
async def generate_hypothesis(query: str):
    service = HypothesisService()
    hypothesis = service.generate_hypothesis(query)
    return hypothesis
```

---

## 🎯 Empfehlungen: Wissenschaftliches Konzept stärken

### 1. **Explizite Hypothesis-Stage** in Pipeline integrieren

```python
# In _process_streaming_query() ergänzen:

async def _process_streaming_query(...):
    # STAGE 0: Explizite Hypothesen-Generierung (NEU)
    hypothesis_service = HypothesisService(ollama_client)
    hypothesis = await hypothesis_service.generate_hypothesis(
        query=request.query,
        rag_context=[]  # Ohne RAG-Kontext für reine Hypothese
    )
    
    # Sende Hypothesis als Progress-Event
    progress_manager.add_hypothesis(
        session_id=session_id,
        hypothesis=hypothesis
    )
    
    # DANN: Bestehende Pipeline fortsetzen
    # Stage 1: Query Analysis...
```

### 2. **Dialektischer Ansatz** (Thesis-Antithesis-Synthesis)

```python
# In Synthesis-Phase:

def _synthesize_with_dialectic(agent_results):
    """
    Dialektische Synthese:
    
    1. Thesis: Identifiziere Haupt-Aussagen der Agents
    2. Antithesis: Finde Widersprüche/Konflikte
    3. Synthesis: Löse Widersprüche auf (LLM)
    """
    theses = extract_main_claims(agent_results)
    antitheses = find_contradictions(theses)
    synthesis = llm_resolve_contradictions(theses, antitheses)
    return synthesis
```

### 3. **Peer-Review Validation** (Multi-LLM)

```python
# In Validation-Phase:

async def _peer_review_validation(final_response):
    """
    Multi-LLM Peer Review:
    
    1. Reviewer 1: llama3.1:8b
    2. Reviewer 2: mixtral:latest
    3. Reviewer 3: gemma3:latest
    
    Consensus: Mindestens 2/3 müssen zustimmen
    """
    reviews = await asyncio.gather(
        llm_review(final_response, "llama3.1:8b"),
        llm_review(final_response, "mixtral:latest"),
        llm_review(final_response, "gemma3:latest")
    )
    consensus = calculate_consensus(reviews)
    return consensus
```

### 4. **Wissenschaftlicher Workflow als Feature-Flag**

```python
# Umgebungsvariable für strikte wissenschaftliche Methode
VERITAS_SCIENTIFIC_MODE = os.getenv("VERITAS_SCIENTIFIC_MODE", "false") == "true"

if VERITAS_SCIENTIFIC_MODE:
    # Explizite Hypothesen-Generierung erzwingen
    # Dialektische Synthese aktivieren
    # Peer-Review Validation aktivieren
    # Ausführliche Meta-Reflections pro Stage
```

---

## ✅ Fazit

**Das wissenschaftliche Konzept ist NOCH VORHANDEN**, aber:

1. ✅ **Hypothesen-Generierung** ist als eigenständiger Service implementiert (`HypothesisService`)
2. ✅ **Stage-Reflection** erweitert die wissenschaftliche Methode um Meta-Analyse
3. ✅ **Synthesis** ist integriert in `IntelligentMultiAgentPipeline`
4. ⚠️ **Agent-Orchestrierung** ergänzt die Methode (nicht ersetzt)
5. ⚠️ **Dialektischer Ansatz** (Thesis-Antithesis-Synthesis) ist NICHT explizit implementiert
6. ⚠️ **Peer-Review** (Multi-LLM Validation) ist NICHT implementiert

**Modernisierung vs. Ursprung:**
- ✅ Wissenschaftliche **Prinzipien** sind erhalten
- ✅ **Struktur** ist moderner (Streaming, Parallel-Execution)
- ⚠️ **Explizite wissenschaftliche Terminologie** könnte verstärkt werden

**Nächste Schritte:**
1. ✅ `HypothesisService` direkt in Streaming-Pipeline integrieren → **ERLEDIGT (16.10.2025)**
2. 🔄 Dialektischen Ansatz in Synthesis-Phase implementieren → **IN ARBEIT**
3. 🔄 Peer-Review Validation als Quality Gate → **IN ARBEIT**
4. 🔄 Feature-Flag `VERITAS_SCIENTIFIC_MODE` für strikte Einhaltung → **GEPLANT**

---

# 🔬 ERWEITERTE WISSENSCHAFTLICHE METHODE

## Dialektische Synthese (Thesis-Antithesis-Synthesis)

### 📚 Philosophischer Hintergrund

Die **dialektische Methode** nach Hegel folgt dem Dreischritt:

1. **These** - Eine Ausgangsbehauptung/Position
2. **Antithese** - Der Widerspruch/Gegensatz zur These
3. **Synthese** - Die Auflösung des Widerspruchs auf höherer Ebene

**Anwendung auf VERITAS:**
- **Thesen** = Agent-Results (verschiedene Experten-Perspektiven)
- **Antithesen** = Widersprüche zwischen Agent-Aussagen
- **Synthese** = LLM-gestützte Auflösung → kohärente Antwort

### 🎯 Implementierungskonzept

```python
class DialecticalSynthesisService:
    """
    Dialektische Synthese für wissenschaftliche Antwort-Generierung
    
    Prozess:
    1. Extraction: Extrahiere Kern-Aussagen (Thesen) aus Agent-Results
    2. Contradiction Detection: Identifiziere Widersprüche (Antithesen)
    3. Synthesis: LLM löst Widersprüche auf höherer Abstraktionsebene auf
    """
    
    def synthesize(self, agent_results: List[AgentResult]) -> DialecticalSynthesis:
        """
        Führt dialektische Synthese durch
        
        Returns:
            DialecticalSynthesis:
                - theses: List[Thesis] - Extrahierte Kern-Aussagen
                - antitheses: List[Contradiction] - Identifizierte Widersprüche
                - synthesis: str - Aufgelöste kohärente Antwort
                - resolution_strategy: str - Wie Widersprüche aufgelöst wurden
                - confidence: float - Konfidenz der Synthese
        """
```

### 📊 Datenmodelle

```python
@dataclass
class Thesis:
    """Kern-Aussage aus Agent-Result"""
    agent_source: str           # Welcher Agent
    claim: str                  # Die Behauptung
    evidence: List[str]         # Belege
    confidence: float           # Agent-Konfidenz
    legal_basis: Optional[str]  # Rechtsgrundlage (falls vorhanden)

@dataclass
class Contradiction:
    """Identifizierter Widerspruch zwischen Thesen"""
    thesis_a: Thesis
    thesis_b: Thesis
    contradiction_type: str     # "legal", "factual", "temporal", "regional"
    severity: str               # "critical", "moderate", "minor"
    description: str            # Was widerspricht sich?
    
@dataclass
class DialecticalSynthesis:
    """Ergebnis der dialektischen Synthese"""
    theses: List[Thesis]
    antitheses: List[Contradiction]
    synthesis: str              # Aufgelöste Antwort
    resolution_strategy: str    # Auflösungs-Methode
    unresolved_conflicts: List[Contradiction]  # Falls welche bleiben
    confidence: float
    reasoning: str              # LLM Begründung
```

### 🔧 LLM-Prompts

#### Prompt 1: Thesis Extraction
```
Du bist ein wissenschaftlicher Analyst. Extrahiere die Kern-Aussagen aus folgenden Agent-Results:

{agent_results}

Für jede Aussage:
1. Formuliere die Kernbehauptung präzise
2. Liste die Belege auf
3. Bewerte die Stärke der Aussage (0-1)

Format: JSON mit Thesis-Objekten
```

#### Prompt 2: Contradiction Detection
```
Du bist ein kritischer Wissenschaftler. Analysiere folgende Thesen auf Widersprüche:

{theses}

Identifiziere:
1. Direkte Widersprüche (A sagt X, B sagt ¬X)
2. Inkonsistenzen (A und B passen nicht zusammen)
3. Mehrdeutigkeiten (A und B können beide stimmen, je nach Interpretation)

Für jeden Widerspruch:
- Type: legal/factual/temporal/regional
- Severity: critical/moderate/minor
- Beschreibung

Format: JSON mit Contradiction-Objekten
```

#### Prompt 3: Dialectical Synthesis
```
Du bist ein wissenschaftlicher Synthesizer. Löse folgende Widersprüche auf:

THESEN:
{theses}

WIDERSPRÜCHE:
{contradictions}

Aufgabe:
1. Analysiere jeden Widerspruch
2. Finde die Auflösung auf höherer Ebene:
   - Sind beide Perspektiven teilweise richtig?
   - Gibt es unterschiedliche Kontexte?
   - Was ist die umfassendere Wahrheit?
3. Formuliere kohärente Gesamt-Antwort

Prinzipien:
- Keine Aussage unterdrücken
- Widersprüche erklären, nicht verstecken
- Unsicherheiten benennen
- Rechtsgrundlagen priorisieren

Format: Strukturierte Antwort mit Begründung
```

### 🚀 Integration in Pipeline

```python
# In _process_streaming_query() nach Agent-Execution:

# STAGE 4.1: Dialektische Analyse (NEU)
if VERITAS_SCIENTIFIC_MODE:
    dialectical_service = DialecticalSynthesisService(ollama_client)
    
    # Extrahiere Thesen
    theses = dialectical_service.extract_theses(agent_results)
    progress_manager.add_message(session_id, "📚 Thesen extrahiert: " + str(len(theses)))
    
    # Identifiziere Widersprüche
    contradictions = dialectical_service.detect_contradictions(theses)
    if contradictions:
        progress_manager.add_message(
            session_id, 
            f"⚠️ {len(contradictions)} Widersprüche identifiziert"
        )
    
    # Synthese
    dialectical_result = dialectical_service.synthesize(theses, contradictions)
    
    # Update Final Response
    final_response = dialectical_result.synthesis
    metadata['dialectical_analysis'] = {
        'theses_count': len(theses),
        'contradictions': [c.description for c in contradictions],
        'resolution_strategy': dialectical_result.resolution_strategy,
        'unresolved': len(dialectical_result.unresolved_conflicts)
    }
else:
    # Bestehende Standard-Synthese
    final_response = _synthesize_standard(agent_results)
```

---

## 🔍 Peer-Review Validation (Multi-LLM Consensus)

### 📚 Wissenschaftlicher Hintergrund

**Peer-Review** ist der Gold-Standard wissenschaftlicher Qualitätssicherung:
- Mehrere unabhängige Experten bewerten eine Arbeit
- Konsens erhöht Vertrauenswürdigkeit
- Bias einzelner Reviewer wird minimiert

**Anwendung auf VERITAS:**
- **Peers** = Verschiedene LLM-Modelle (llama3.1, mixtral, gemma3)
- **Review** = Validierung der Final Response
- **Consensus** = Mindestens 2/3 Zustimmung erforderlich

### 🎯 Implementierungskonzept

```python
class PeerReviewValidationService:
    """
    Multi-LLM Peer-Review für wissenschaftliche Validierung
    
    Prozess:
    1. Independent Review: Jedes LLM bewertet die Response unabhängig
    2. Review Criteria: Faktentreue, Vollständigkeit, Kohärenz, Rechtskonformität
    3. Consensus Calculation: Berechne Übereinstimmung (0-1)
    4. Conflict Resolution: Bei Uneinigkeit → Tiefenanalyse
    """
    
    def __init__(self):
        self.reviewers = [
            ("llama3.1:8b", "Generalist, stark in Rechtsfragen"),
            ("mixtral:latest", "Multi-lingual, ausgewogen"),
            ("gemma3:latest", "Faktenfokussiert, konservativ")
        ]
    
    async def peer_review(self, 
                         query: str,
                         final_response: str,
                         agent_results: List[AgentResult],
                         sources: List[str]) -> PeerReviewResult:
        """
        Führt Multi-LLM Peer-Review durch
        
        Returns:
            PeerReviewResult:
                - reviews: List[Review] - Einzelne Reviews
                - consensus_score: float - 0-1 (0=keine Einigkeit, 1=volle Einigkeit)
                - approval_status: str - "approved", "conditional", "rejected"
                - conflicts: List[ReviewConflict] - Uneinigkeiten
                - final_verdict: str - Zusammenfassende Bewertung
        """
```

### 📊 Datenmodelle

```python
@dataclass
class Review:
    """Einzelnes LLM-Review"""
    reviewer_model: str
    overall_score: float        # 0-1
    criteria_scores: Dict[str, float]  # factual_accuracy, completeness, etc.
    strengths: List[str]        # Was ist gut?
    weaknesses: List[str]       # Was fehlt/ist falsch?
    recommendation: str         # "approve", "revise", "reject"
    comments: str               # Detaillierte Begründung
    
@dataclass
class ReviewConflict:
    """Uneinigkeit zwischen Reviewern"""
    criterion: str              # Bei welchem Kriterium?
    reviewer_a: str
    score_a: float
    reviewer_b: str
    score_b: float
    difference: float           # Wie groß ist die Differenz?
    
@dataclass
class PeerReviewResult:
    """Gesamt-Ergebnis des Peer-Reviews"""
    reviews: List[Review]
    consensus_score: float      # 0-1
    approval_status: str        # approved/conditional/rejected
    conflicts: List[ReviewConflict]
    final_verdict: str
    confidence: float
    recommendations: List[str]  # Verbesserungsvorschläge
```

### 🎯 Review-Kriterien

```python
REVIEW_CRITERIA = {
    'factual_accuracy': {
        'weight': 0.30,
        'description': 'Stimmen Fakten? Gibt es falsche Aussagen?'
    },
    'completeness': {
        'weight': 0.25,
        'description': 'Wurde die Frage vollständig beantwortet?'
    },
    'legal_compliance': {
        'weight': 0.20,
        'description': 'Sind Rechtsgrundlagen korrekt zitiert?'
    },
    'coherence': {
        'weight': 0.15,
        'description': 'Ist die Antwort logisch kohärent?'
    },
    'source_coverage': {
        'weight': 0.10,
        'description': 'Wurden alle relevanten Quellen berücksichtigt?'
    }
}
```

### 🔧 LLM-Prompt

```
Du bist ein wissenschaftlicher Peer-Reviewer. Bewerte folgende Antwort:

URSPRÜNGLICHE FRAGE:
{query}

GENERIERTE ANTWORT:
{final_response}

VERWENDETE QUELLEN:
{sources}

AGENT-ANALYSEN:
{agent_results}

Bewerte die Antwort nach folgenden Kriterien (Score 0-10):

1. FAKTENTREUE (30%):
   - Sind alle Fakten korrekt?
   - Gibt es falsche/irreführende Aussagen?
   Score: __/10
   Begründung: __

2. VOLLSTÄNDIGKEIT (25%):
   - Wurde die Frage vollständig beantwortet?
   - Fehlen wichtige Aspekte?
   Score: __/10
   Begründung: __

3. RECHTSKONFORMITÄT (20%):
   - Sind Gesetze/Verordnungen korrekt zitiert?
   - Stimmen Paragraphen/Fristen?
   Score: __/10
   Begründung: __

4. KOHÄRENZ (15%):
   - Ist die Antwort logisch aufgebaut?
   - Gibt es Widersprüche?
   Score: __/10
   Begründung: __

5. QUELLENABDECKUNG (10%):
   - Wurden alle relevanten Quellen genutzt?
   - Fehlen wichtige Perspektiven?
   Score: __/10
   Begründung: __

GESAMT-BEWERTUNG:
- Gesamtscore: __/10
- Stärken: [Liste]
- Schwächen: [Liste]
- Empfehlung: APPROVE / REVISE / REJECT
- Kommentar: __

Format: JSON mit Review-Objekt
```

### 🚀 Integration in Pipeline

```python
# In _process_streaming_query() nach Synthese:

# STAGE 5: PEER-REVIEW VALIDATION (NEU)
if VERITAS_SCIENTIFIC_MODE:
    progress_manager.update_stage(session_id, ProgressStage.VALIDATING)
    progress_manager.add_message(session_id, "🔍 Starte Multi-LLM Peer-Review...")
    
    peer_review_service = PeerReviewValidationService()
    
    # Führe parallele Reviews durch (3 LLMs)
    review_result = await peer_review_service.peer_review(
        query=request.query,
        final_response=final_response,
        agent_results=agent_results,
        sources=sources
    )
    
    # Sende Review-Status
    progress_manager.add_message(
        session_id,
        f"📊 Consensus Score: {review_result.consensus_score:.2f} | "
        f"Status: {review_result.approval_status}"
    )
    
    # Bei niedrigem Consensus oder Ablehnung → Warnung
    if review_result.approval_status == "rejected":
        progress_manager.add_message(
            session_id,
            "⚠️ Peer-Review ABGELEHNT - Antwort wird überarbeitet..."
        )
        # Optional: Revision-Loop starten
        final_response = await _revise_response(
            final_response, 
            review_result.recommendations
        )
    
    elif review_result.approval_status == "conditional":
        progress_manager.add_message(
            session_id,
            f"⚠️ Peer-Review MIT VORBEHALTEN - {len(review_result.conflicts)} Konflikte"
        )
    
    else:
        progress_manager.add_message(
            session_id,
            "✅ Peer-Review BESTANDEN - Hohe Übereinstimmung"
        )
    
    # Füge Review-Metadaten zur Response hinzu
    metadata['peer_review'] = {
        'consensus_score': review_result.consensus_score,
        'approval_status': review_result.approval_status,
        'reviewers': [r.reviewer_model for r in review_result.reviews],
        'conflicts': [c.criterion for c in review_result.conflicts],
        'recommendations': review_result.recommendations
    }
```

---

## 🎛️ Feature-Flag: VERITAS_SCIENTIFIC_MODE

### Konfiguration

```python
# config/config.py

# Wissenschaftlicher Modus: Strikte wissenschaftliche Methode
VERITAS_SCIENTIFIC_MODE = os.getenv("VERITAS_SCIENTIFIC_MODE", "false").lower() == "true"

# Sub-Features
ENABLE_DIALECTICAL_SYNTHESIS = os.getenv("ENABLE_DIALECTICAL_SYNTHESIS", "true").lower() == "true"
ENABLE_PEER_REVIEW = os.getenv("ENABLE_PEER_REVIEW", "true").lower() == "true"
PEER_REVIEW_MIN_CONSENSUS = float(os.getenv("PEER_REVIEW_MIN_CONSENSUS", "0.67"))  # 2/3

# Performance-Settings
DIALECTICAL_TIMEOUT = int(os.getenv("DIALECTICAL_TIMEOUT", "30"))  # Sekunden
PEER_REVIEW_TIMEOUT = int(os.getenv("PEER_REVIEW_TIMEOUT", "45"))  # Sekunden
```

### Umgebungsvariablen

```bash
# .env

# Aktiviere wissenschaftlichen Modus
VERITAS_SCIENTIFIC_MODE=true

# Dialektische Synthese
ENABLE_DIALECTICAL_SYNTHESIS=true
DIALECTICAL_TIMEOUT=30

# Peer-Review
ENABLE_PEER_REVIEW=true
PEER_REVIEW_MIN_CONSENSUS=0.67  # 2/3 Zustimmung erforderlich
PEER_REVIEW_TIMEOUT=45
```

### Frontend-Integration

```typescript
// Frontend zeigt wissenschaftliche Features

if (response.metadata.scientific_mode) {
    // Zeige dialektische Analyse
    if (response.metadata.dialectical_analysis) {
        showDialecticalAnalysis({
            theses: response.metadata.dialectical_analysis.theses_count,
            contradictions: response.metadata.dialectical_analysis.contradictions,
            resolution: response.metadata.dialectical_analysis.resolution_strategy
        });
    }
    
    // Zeige Peer-Review-Status
    if (response.metadata.peer_review) {
        showPeerReviewBadge({
            consensus: response.metadata.peer_review.consensus_score,
            status: response.metadata.peer_review.approval_status,
            reviewers: response.metadata.peer_review.reviewers
        });
    }
}
```

---

## 📊 Erweiterter Workflow

```
USER QUERY
    ↓
🔬 STAGE 0: HYPOTHESIS
    ├─ HypothesisService
    ├─ Information Gaps
    └─ Clarification Questions
    ↓
📚 STAGE 1: INFORMATIONSBESCHAFFUNG
    ├─ RAG Search (UDS3)
    └─ Agent Selection
    ↓
⚙️ STAGE 2: PARALLELE ANALYSE
    ├─ 14 Spezialisierte Agents
    └─ Agent-Results
    ↓
🎭 STAGE 3: DIALEKTISCHE SYNTHESE (NEU!)
    ├─ Thesis Extraction
    ├─ Contradiction Detection
    ├─ Dialectical Resolution
    └─ Kohärente Synthese
    ↓
🔍 STAGE 4: PEER-REVIEW VALIDATION (NEU!)
    ├─ Reviewer 1: llama3.1:8b
    ├─ Reviewer 2: mixtral:latest
    ├─ Reviewer 3: gemma3:latest
    ├─ Consensus Calculation
    └─ Approval/Rejection/Conditional
    ↓
✅ STAGE 5: FINALISIERUNG
    ├─ Quality Metrics
    ├─ Confidence Score
    └─ Follow-up Suggestions
    ↓
FINAL RESPONSE (wissenschaftlich validiert)
```

---

## ⏱️ Performance-Überlegungen

| **Feature** | **Zusätzliche Zeit** | **LLM-Calls** | **Priorität** |
|-------------|---------------------|---------------|---------------|
| Hypothesis | +1-2s | 1 | ✅ Immer aktiv |
| Dialektische Synthese | +3-5s | 3 (Extraction, Detection, Synthesis) | 🟡 Optional |
| Peer-Review | +8-12s | 3 (parallel) | 🟡 Optional |
| **Total (Scientific Mode)** | **+12-19s** | **+7 LLM-Calls** | 🎯 Feature-Flag |

**Empfehlung:**
- Standard-Modus: Nur Hypothesis (schnell, immer aktiv)
- Scientific-Modus: Hypothesis + Dialektik + Peer-Review (langsam, hohe Qualität)
- Frontend: User kann Modus wählen

---

**Aktualisiert am:** 16. Oktober 2025  
**Version:** VERITAS Backend v1.1.0-scientific  
**Status:** Konzept erweitert, Implementation in Arbeit
