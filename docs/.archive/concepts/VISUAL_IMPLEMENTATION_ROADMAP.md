# VISUAL IMPLEMENTATION ROADMAP

**Projekt:** VERITAS v5.0 Structured Response System
**Status:** 🟢 Ready to Start
**Erstellt:** 12. Oktober 2025

---

## 🗺️ High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         USER QUERY                              │
│                 "Wie ist das Wetter in Berlin?"                 │
└─────────────────────────┬──────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: FOUNDATION                           │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐            │
│  │ NLPService │───▶│ProcessBuild│───▶│ProcessExec │            │
│  │  (NEW)     │    │    (NEW)   │    │   (NEW)    │            │
│  └────────────┘    └────────────┘    └────┬───────┘            │
│       │                                    │                     │
│       │ Entities:                          │ Uses:              │
│       │ - Location: "Berlin"               │ ✅ DependencyResolv│
│       │ - Intent: "weather_query"          │    (EXISTS!)       │
│       │ - Type: "fact_retrieval"           │                    │
└───────┴────────────────────────────────────┴─────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 2: HYPOTHESIS GENERATION                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         HypothesisService (NEW)                          │   │
│  │  ┌──────────────┐                                        │   │
│  │  │ LLM Call 1   │ "Based on RAG context + query..."     │   │
│  │  │ (~500 tokens)│                                        │   │
│  │  └──────┬───────┘                                        │   │
│  │         │                                                 │   │
│  │         ▼                                                 │   │
│  │  {                                                        │   │
│  │    "question_type": "fact_retrieval",                    │   │
│  │    "hypothesis": "User wants current weather in Berlin", │   │
│  │    "required_data": ["temperature", "conditions"],       │   │
│  │    "confidence": 0.92                                    │   │
│  │  }                                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│         Uses: ✅ veritas_ollama_client.py (EXISTS!)             │
│         Uses: ✅ rag_context_service.py (EXISTS!)               │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│            PHASE 2: ADAPTIVE TEMPLATE CONSTRUCTION               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │     TemplateService (NEW)                                │   │
│  │                                                           │   │
│  │  if question_type == "fact_retrieval":                   │   │
│  │      template = FactRetrievalTemplate()                  │   │
│  │  elif question_type == "comparison":                     │   │
│  │      template = ComparisonTemplate()                     │   │
│  │  elif question_type == "timeline":                       │   │
│  │      template = TimelineTemplate()                       │   │
│  │  # ... 5 templates total                                 │   │
│  │                                                           │   │
│  │  Template Output:                                         │   │
│  │  {                                                        │   │
│  │    "sections": ["summary", "details", "source"],         │   │
│  │    "widgets": ["text", "table"],                         │   │
│  │    "fields": ["temperature", "conditions", "forecast"]   │   │
│  │  }                                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│         Extends: ⚠️ veritas_agent_template.py (EXISTS!)         │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 3: NDJSON STREAMING RESPONSE                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  StreamingService (EXTEND EXISTING!)                     │   │
│  │  ✅ backend/services/veritas_streaming_service.py        │   │
│  │                                                           │   │
│  │  New Message Types (NDJSON):                             │   │
│  │  ┌────────────────────────────────────────────────┐     │   │
│  │  │ {"type": "text_chunk", "content": "Das ..."}   │     │   │
│  │  │ {"type": "metadata", "stage": "llm", "prog": 50}│     │   │
│  │  │ {"type": "widget", "widget_type": "table", ...} │     │   │
│  │  │ {"type": "form", "reason": "missing_location"}  │     │   │
│  │  └────────────────────────────────────────────────┘     │   │
│  │                                                           │   │
│  │  Old Message Types (KEEP!):                              │   │
│  │  - STREAM_START, STREAM_PROGRESS, STREAM_COMPLETE        │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│             PHASE 4: QUALITY MONITORING (OPTIONAL)               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │    QualityMonitor (NEW)                                  │   │
│  │                                                           │   │
│  │  Check Completeness:                                     │   │
│  │  - Required field "temperature": ✅ Present              │   │
│  │  - Required field "conditions": ✅ Present               │   │
│  │  - Optional field "forecast": ❌ Missing                 │   │
│  │                                                           │   │
│  │  If gaps found:                                          │   │
│  │    → Generate Interactive Form                           │   │
│  │    → Stream {"type": "form", ...}                        │   │
│  │    → Wait for user input                                 │   │
│  │    → Re-execute with new parameters                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 5: API ENDPOINTS                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FastAPI Endpoints (NEW)                                 │   │
│  │                                                           │   │
│  │  POST /api/v1/query/structured                           │   │
│  │  ┌──────────────────────────────────────────────┐       │   │
│  │  │ Request:                                      │       │   │
│  │  │ {                                             │       │   │
│  │  │   "query": "Wie ist das Wetter in Berlin?", │       │   │
│  │  │   "session_id": "abc123"                     │       │   │
│  │  │ }                                             │       │   │
│  │  └──────────────────────────────────────────────┘       │   │
│  │                                                           │   │
│  │  WS /ws/query/structured                                 │   │
│  │  ┌──────────────────────────────────────────────┐       │   │
│  │  │ Bidirectional WebSocket                       │       │   │
│  │  │ - Send: Query                                 │       │   │
│  │  │ - Receive: NDJSON stream                      │       │   │
│  │  │ - Send: Form submission                       │       │   │
│  │  │ - Send: Cancel request                        │       │   │
│  │  └──────────────────────────────────────────────┘       │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 6: FRONTEND INTEGRATION                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  StreamingClient (NEW)                                   │   │
│  │  frontend/streaming_client.py                            │   │
│  │                                                           │   │
│  │  1. Connect to WebSocket                                 │   │
│  │  2. Parse NDJSON messages                                │   │
│  │  3. Dispatch to renderers:                               │   │
│  │     - text_chunk → ✅ Markdown (EXISTS!)                 │   │
│  │     - widget → TableWidget (NEW)                         │   │
│  │     - form → FormWidget (NEW)                            │   │
│  │     - metadata → Progress Bar (EXISTS!)                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Tkinter Widgets (NEW):                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ TableWidget │  │ ChartWidget │  │ FormWidget  │            │
│  │ (Treeview)  │  │ (matplotlib)│  │ (Entry/Btn) │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FINAL RENDERED RESPONSE                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🌤️ Wetter in Berlin                                     │   │
│  │                                                           │   │
│  │ **Aktuell:** 18°C, Leicht bewölkt                        │   │
│  │                                                           │   │
│  │ ┌───────────┬───────────┬───────────┐                   │   │
│  │ │ Uhrzeit   │ Temp      │ Regen     │  ← TableWidget    │   │
│  │ ├───────────┼───────────┼───────────┤                   │   │
│  │ │ 15:00     │ 18°C      │ 0%        │                   │   │
│  │ │ 18:00     │ 16°C      │ 10%       │                   │   │
│  │ │ 21:00     │ 14°C      │ 30%       │                   │   │
│  │ └───────────┴───────────┴───────────┘                   │   │
│  │                                                           │   │
│  │ [Quelle: OpenWeatherMap]  ← ButtonWidget                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Component Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                      EXISTING COMPONENTS                         │
│                         (REUSE! ✅)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DependencyResolver           veritas_streaming_service.py      │
│  (395 LOC)                    (639 LOC)                         │
│        │                              │                          │
│        │ Used by                      │ Extended by              │
│        ▼                              ▼                          │
│  ProcessExecutor              StreamingProtocol                  │
│  (NEW - 200 LOC)              (NEW - 150 LOC)                   │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  veritas_ollama_client.py     rag_context_service.py           │
│  (1,185 LOC)                  (~500 LOC)                        │
│        │                              │                          │
│        │ Used by                      │ Used by                  │
│        ▼                              ▼                          │
│  HypothesisService            ProcessBuilder                     │
│  (NEW - 300 LOC)              (NEW - 150 LOC)                   │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  veritas_agent_template.py    veritas_ui_markdown.py           │
│  (573 LOC)                    (1,000 LOC)                       │
│        │                              │                          │
│        │ Extended by                  │ Reused by                │
│        ▼                              ▼                          │
│  TemplateService              StreamingClient                    │
│  (NEW - 400 LOC)              (NEW - 200 LOC)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Implementation Priority Matrix

```
                    CRITICAL                 HIGH                 MEDIUM
                    (Do First)               (Do Next)            (Do Later)
              ┌───────────────────┐   ┌──────────────────┐  ┌──────────────┐
Phase 1       │ ProcessExecutor   │   │                  │  │              │
Foundation    │ ProcessBuilder    │   │                  │  │              │
(2-3 days)    │ NLPService        │   │                  │  │              │
              └───────────────────┘   └──────────────────┘  └──────────────┘
                       │
                       ▼
              ┌───────────────────┐   ┌──────────────────┐  ┌──────────────┐
Phase 2       │ HypothesisService │   │ TemplateService  │  │              │
Hypothesis    │ Hypothesis Models │   │ 5 Templates      │  │              │
(4-5 days)    │ Hypothesis Prompt │   │ Template Models  │  │              │
              └───────────────────┘   └──────────────────┘  └──────────────┘
                       │                       │
                       └───────────┬───────────┘
                                   ▼
              ┌───────────────────┐   ┌──────────────────┐  ┌──────────────┐
Phase 3       │                   │   │ NDJSON Protocol  │  │              │
Streaming     │                   │   │ Streaming Extend │  │              │
(2-3 days)    │                   │   │ Widget Schemas   │  │              │
              └───────────────────┘   └──────────────────┘  └──────────────┘
                                               │
                                               ▼
              ┌───────────────────┐   ┌──────────────────┐  ┌──────────────┐
Phase 4       │                   │   │                  │  │QualityMonitor│
Quality       │                   │   │                  │  │Quality Models│
(2-3 days)    │                   │   │                  │  │Form Generator│
              └───────────────────┘   └──────────────────┘  └──────────────┘
                                                                    │
                                                                    ▼
              ┌───────────────────┐   ┌──────────────────┐  ┌──────────────┐
Phase 5       │                   │   │ API Endpoints    │  │              │
API           │                   │   │ WebSocket        │  │              │
(2-3 days)    │                   │   │ Request Models   │  │              │
              └───────────────────┘   └──────────────────┘  └──────────────┘
                                               │
                                               ▼
              ┌───────────────────┐   ┌──────────────────┐  ┌──────────────┐
Phase 6       │                   │   │                  │  │StreamingClient│
Frontend      │                   │   │                  │  │Tkinter Widgets│
(3-4 days)    │                   │   │                  │  │Chat Integration│
              └───────────────────┘   └──────────────────┘  └──────────────┘
                                                                    │
                                                                    ▼
              ┌───────────────────┐   ┌──────────────────┐  ┌──────────────┐
Phase 7       │                   │   │                  │  │ Unit Tests   │
Testing       │                   │   │                  │  │ Integration  │
(3-4 days)    │                   │   │                  │  │ Documentation│
              └───────────────────┘   └──────────────────┘  └──────────────┘
```

**Legend:**
- 🔴 **CRITICAL:** Must be done first (blocks others)
- 🟡 **HIGH:** Important, do after critical
- 🟢 **MEDIUM:** Nice to have, do if time allows

---

## 🔄 Data Flow Diagram

```
┌──────────┐
│   USER   │
│  QUERY   │
└────┬─────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 1: NLP Extraction                                        │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Input:  "Wie ist das Wetter in Berlin?"               │  │
│ │                                                         │  │
│ │ Output: {                                              │  │
│ │   entities: [                                          │  │
│ │     {text: "Berlin", type: "LOCATION"}                │  │
│ │   ],                                                   │  │
│ │   intent: "weather_query",                            │  │
│ │   question_type: "fact_retrieval"                     │  │
│ │ }                                                       │  │
│ └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 2: Process Tree Construction                            │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ {                                                       │  │
│ │   root: {type: "user_query", content: "..."},         │  │
│ │   steps: [                                             │  │
│ │     {step_id: "nlp", depends_on: []},                 │  │
│ │     {step_id: "rag_semantic", depends_on: ["nlp"],    │  │
│ │      parallel_group: "rag"},                          │  │
│ │     {step_id: "rag_graph", depends_on: ["nlp"],       │  │
│ │      parallel_group: "rag"},                          │  │
│ │     {step_id: "hypothesis", depends_on: ["rag_*"]},   │  │
│ │     {step_id: "template", depends_on: ["hypothesis"]},│  │
│ │     {step_id: "llm_answer", depends_on: ["template"]}│  │
│ │   ]                                                    │  │
│ │ }                                                       │  │
│ └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 3: Dependency Resolution (✅ EXISTING!)                  │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ DependencyResolver.get_execution_plan():               │  │
│ │                                                         │  │
│ │ [                                                       │  │
│ │   ["nlp"],                        # Wave 1             │  │
│ │   ["rag_semantic", "rag_graph"],  # Wave 2 (Parallel!) │  │
│ │   ["hypothesis"],                 # Wave 3             │  │
│ │   ["template"],                   # Wave 4             │  │
│ │   ["llm_answer"]                  # Wave 5             │  │
│ │ ]                                                       │  │
│ └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 4: RAG Context Retrieval (✅ EXISTING!)                  │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ rag_semantic:                                          │  │
│ │   Query: "Wetter Berlin"                              │  │
│ │   Results: [                                           │  │
│ │     {doc: "Berlin Wetter heute 18°C", score: 0.92}   │  │
│ │   ]                                                    │  │
│ │                                                         │  │
│ │ rag_graph:                                             │  │
│ │   Query: "Berlin" → Related: ["Deutschland", "Wetter"]│  │
│ └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 5: Hypothesis Generation (NEW!)                         │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ LLM Call 1:                                            │  │
│ │   Prompt: "Based on RAG context + query, hypothesize" │  │
│ │   Input: {query: "...", rag_results: [...]}           │  │
│ │                                                         │  │
│ │   Output: {                                            │  │
│ │     question_type: "fact_retrieval",                   │  │
│ │     hypothesis: "User wants current weather in Berlin",│  │
│ │     required_data: ["temp", "conditions"],            │  │
│ │     confidence: 0.92                                   │  │
│ │   }                                                     │  │
│ └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 6: Adaptive Template Construction (NEW!)                │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ TemplateService.construct_template(hypothesis):        │  │
│ │                                                         │  │
│ │   if question_type == "fact_retrieval":                │  │
│ │       template = FactRetrievalTemplate()               │  │
│ │                                                         │  │
│ │   template.sections = ["summary", "details", "source"] │  │
│ │   template.widgets = ["text", "table"]                 │  │
│ │   template.fields = ["temp", "conditions", "forecast"] │  │
│ └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 7: LLM Answer Generation (✅ EXISTING!)                  │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ LLM Call 2:                                            │  │
│ │   Prompt: "Fill template with RAG data"               │  │
│ │   Input: {template: {...}, rag_data: {...}}           │  │
│ │                                                         │  │
│ │   Output: "Das Wetter in Berlin ist aktuell 18°C..." │  │
│ └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 8: NDJSON Streaming (NEW!)                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ {"type": "metadata", "stage": "nlp", "progress": 10}  │  │
│ │ {"type": "metadata", "stage": "rag", "progress": 30}  │  │
│ │ {"type": "metadata", "stage": "hypothesis", "prog": 50}│  │
│ │ {"type": "text_chunk", "content": "Das Wetter ..."}   │  │
│ │ {"type": "widget", "widget_type": "table", ...}       │  │
│ │ {"type": "metadata", "stage": "complete", "prog": 100}│  │
│ └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 9: Frontend Rendering (NEW!)                            │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ StreamingClient.on_message(msg):                       │  │
│ │   if msg.type == "text_chunk":                         │  │
│ │       markdown_renderer.append(msg.content) # ✅ EXISTS│  │
│ │   elif msg.type == "widget":                           │  │
│ │       widget_factory.create(msg.widget_type) # NEW    │  │
│ │   elif msg.type == "metadata":                         │  │
│ │       progress_bar.update(msg.progress) # ✅ EXISTS   │  │
│ └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────┐
│ RENDERED │
│ RESPONSE │
└──────────┘
```

---

## 📁 File Structure (Complete)

```
c:\VCC\veritas\
│
├── backend/
│   ├── services/               # Business Logic
│   │   ├── process_executor.py        # ✅ NEW (200 LOC) - Phase 1
│   │   ├── process_builder.py         # ✅ NEW (150 LOC) - Phase 1
│   │   ├── nlp_service.py             # ✅ NEW (300 LOC) - Phase 1
│   │   ├── hypothesis_service.py      # ✅ NEW (300 LOC) - Phase 2
│   │   ├── template_service.py        # ✅ NEW (400 LOC) - Phase 2
│   │   ├── quality_monitor.py         # ✅ NEW (250 LOC) - Phase 4
│   │   ├── form_generator.py          # ✅ NEW (150 LOC) - Phase 4
│   │   └── veritas_streaming_service.py # ⚠️ EXTEND (+150 LOC) - Phase 3
│   │
│   ├── models/                 # Data Classes
│   │   ├── process_step.py            # ✅ NEW (100 LOC) - Phase 1
│   │   ├── process_tree.py            # ✅ NEW (100 LOC) - Phase 1
│   │   ├── hypothesis.py              # ✅ NEW (100 LOC) - Phase 2
│   │   ├── response_template.py       # ✅ NEW (150 LOC) - Phase 2
│   │   ├── streaming_protocol.py      # ✅ NEW (150 LOC) - Phase 3
│   │   ├── widget_schema.py           # ✅ NEW (100 LOC) - Phase 3
│   │   ├── form_schema.py             # ✅ NEW (100 LOC) - Phase 3
│   │   └── quality_report.py          # ✅ NEW (100 LOC) - Phase 4
│   │
│   ├── templates/              # Template Implementations
│   │   ├── fact_retrieval_template.py # ✅ NEW (80 LOC) - Phase 2
│   │   ├── comparison_template.py     # ✅ NEW (80 LOC) - Phase 2
│   │   ├── timeline_template.py       # ✅ NEW (80 LOC) - Phase 2
│   │   ├── calculation_template.py    # ✅ NEW (80 LOC) - Phase 2
│   │   └── visual_template.py         # ✅ NEW (80 LOC) - Phase 2
│   │
│   ├── prompts/                # LLM Prompts
│   │   └── hypothesis_prompt.txt      # ✅ NEW (200 lines) - Phase 2
│   │
│   ├── api/                    # API Endpoints
│   │   ├── structured_query_endpoint.py # ✅ NEW (200 LOC) - Phase 5
│   │   ├── websocket_endpoint.py        # ✅ NEW (150 LOC) - Phase 5
│   │   └── models.py                    # ✅ NEW (100 LOC) - Phase 5
│   │
│   └── agents/
│       └── framework/
│           └── dependency_resolver.py   # ✅ EXISTS (395 LOC) - REUSE!
│
├── frontend/
│   ├── streaming_client.py             # ✅ NEW (200 LOC) - Phase 6
│   ├── enhanced_markdown_renderer.py   # ✅ NEW (150 LOC) - Phase 6
│   ├── chat_window_enhanced.py         # ✅ NEW (100 LOC) - Phase 6
│   └── widgets/                         # Widget Renderers
│       ├── table_widget.py              # ✅ NEW (100 LOC) - Phase 6
│       ├── chart_widget.py              # ✅ NEW (150 LOC) - Phase 6
│       ├── form_widget.py               # ✅ NEW (150 LOC) - Phase 6
│       └── button_widget.py             # ✅ NEW (50 LOC) - Phase 6
│
├── tests/
│   ├── test_process_executor.py        # ✅ NEW (100 LOC) - Phase 1
│   ├── test_process_builder.py         # ✅ NEW (100 LOC) - Phase 1
│   ├── test_nlp_service.py             # ✅ NEW (100 LOC) - Phase 1
│   ├── test_hypothesis_service.py      # ✅ NEW (150 LOC) - Phase 2
│   ├── test_template_service.py        # ✅ NEW (150 LOC) - Phase 2
│   ├── test_quality_monitor.py         # ✅ NEW (100 LOC) - Phase 4
│   ├── test_ndjson_streaming.py        # ✅ NEW (100 LOC) - Phase 3
│   ├── test_api_endpoints.py           # ✅ NEW (150 LOC) - Phase 5
│   ├── test_integration_e2e.py         # ✅ NEW (200 LOC) - Phase 7
│   ├── test_load_performance.py        # ✅ NEW (150 LOC) - Phase 7
│   └── frontend/
│       └── test_streaming_client.py    # ✅ NEW (100 LOC) - Phase 6
│
└── docs/
    ├── IMPLEMENTATION_GAP_ANALYSIS_TODO.md # ✅ Created (8,000 lines)
    ├── TODO_EXECUTIVE_SUMMARY.md           # ✅ Created (600 lines)
    ├── VISUAL_IMPLEMENTATION_ROADMAP.md    # ✅ This file
    ├── API_STRUCTURED_QUERY.md             # ✅ NEW (300 lines) - Phase 5
    ├── USER_GUIDE_STRUCTURED_RESPONSES.md  # ✅ NEW (500 lines) - Phase 7
    └── DEVELOPER_GUIDE_STRUCTURED_RESPONSES.md # ✅ NEW (800 lines) - Phase 7
```

**Legend:**
- ✅ **NEW** - To be created
- ⚠️ **EXTEND** - Extend existing file
- ✅ **EXISTS** - Already exists, reuse as-is

**Total New Code:** ~7,450 LOC
**Total Existing Code (Reused):** ~4,300 LOC

---

## ⏱️ Weekly Timeline (Gantt-Style)

```
Week 1: Foundation + Hypothesis
┌────────────────────────────────────────────────────────────────┐
│ Mon    │ Tue    │ Wed    │ Thu    │ Fri    │ Sat    │ Sun    │
├────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│ Phase 1│ Phase 1│ Phase 1│ Phase 2│ Phase 2│ Phase 2│ Phase 2│
│ NLP    │ Process│ Process│ Hypothe│ Hypothe│ Templat│ Templat│
│ Service│ Builder│ Executo│ sis    │ sis    │ e (1-3)│ e (4-5)│
│        │        │  r     │ Service│ Prompt │        │        │
└────────┴────────┴────────┴────────┴────────┴────────┴────────┘

Week 2: Streaming + Quality + API
┌────────────────────────────────────────────────────────────────┐
│ Mon    │ Tue    │ Wed    │ Thu    │ Fri    │ Sat    │ Sun    │
├────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│ Phase 3│ Phase 3│ Phase 4│ Phase 4│ Phase 5│ Phase 5│ Phase 5│
│ NDJSON │ Widget │ Quality│ Form   │ API    │ WebSock│ Request│
│ Protoco│ Schema │ Monitor│ Generat│ Endpoin│ et     │ Models │
│ l      │        │        │ or     │ t      │        │        │
└────────┴────────┴────────┴────────┴────────┴────────┴────────┘

Week 3: Frontend Integration
┌────────────────────────────────────────────────────────────────┐
│ Mon    │ Tue    │ Wed    │ Thu    │ Fri    │ Sat    │ Sun    │
├────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│ Phase 6│ Phase 6│ Phase 6│ Phase 6│ Phase 6│ Phase 6│ Phase 6│
│ Streami│ Table  │ Chart  │ Form   │ Button │ Chat   │ Buffer │
│ ng     │ Widget │ Widget │ Widget │ Widget │ Integra│        │
│ Client │        │        │        │        │ tion   │        │
└────────┴────────┴────────┴────────┴────────┴────────┴────────┘

Week 4: Testing + Documentation
┌────────────────────────────────────────────────────────────────┐
│ Mon    │ Tue    │ Wed    │ Thu    │ Fri    │ Sat    │ Sun    │
├────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│ Phase 7│ Phase 7│ Phase 7│ Phase 7│ Phase 7│ Phase 7│ DEPLOY │
│ Unit   │ Integra│ Load   │ API    │ User   │ Develop│ Produkt│
│ Tests  │ tion   │ Tests  │ Docs   │ Guide  │ er     │ ion    │
│        │ Tests  │        │        │        │ Guide  │        │
└────────┴────────┴────────┴────────┴────────┴────────┴────────┘
```

**Milestones:**
- 🎯 **End of Week 1:** Hypothesis generation working
- 🎯 **End of Week 2:** NDJSON streaming + API ready
- 🎯 **End of Week 3:** Full frontend integration
- 🎯 **End of Week 4:** Production deployment

---

## 🚀 MVP Fast Track (2-3 Wochen)

**Nur kritische Komponenten:**

```
Week 1: MVP Core
┌────────────────────────────────────────────────────────────────┐
│ Mon    │ Tue    │ Wed    │ Thu    │ Fri    │ Sat    │ Sun    │
├────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│ NLP    │ Process│ Process│ Hypothe│ Hypothe│ ONLY   │ Basic  │
│ Service│ Builder│ Executo│ sis    │ sis    │ Fact   │ NDJSON │
│        │        │  r     │ Service│ Prompt │ Templat│ (Text) │
│        │        │        │        │        │ e      │        │
└────────┴────────┴────────┴────────┴────────┴────────┴────────┘

Week 2: MVP Integration
┌────────────────────────────────────────────────────────────────┐
│ Mon    │ Tue    │ Wed    │ Thu    │ Fri    │ Sat    │ Sun    │
├────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│ API    │ API    │ Basic  │ Basic  │ Unit   │ E2E    │ DEMO   │
│ Endpoin│ WebSock│ Streami│ Chat   │ Tests  │ Test   │        │
│ t      │ et     │ ng     │ Integra│        │        │        │
│        │        │ Client │ tion   │        │        │        │
└────────┴────────┴────────┴────────┴────────┴────────┴────────┘
```

**MVP Features:**
- ✅ Process Execution (with DependencyResolver)
- ✅ Hypothesis Generation
- ✅ 1 Template (Fact Retrieval only)
- ✅ Basic NDJSON Streaming (Text + Metadata)
- ❌ No Widgets
- ❌ No Forms
- ❌ No Quality Monitoring

**MVP Deliverables:**
- Working end-to-end flow
- Hypothesis-driven template selection
- Streaming text responses
- Basic API endpoint

**MVP → Full v5.0:** Add remaining templates, widgets, forms in Weeks 3-4

---

## 🎯 Success Metrics

```
┌─────────────────────────────────────────────────────────────────┐
│                         SUCCESS CRITERIA                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: Foundation                                            │
│  ✅ ProcessExecutor wraps DependencyResolver                     │
│  ✅ ProcessBuilder converts query → ProcessTree                  │
│  ✅ NLPService extracts entities (80% accuracy)                  │
│  ✅ Unit tests >80% coverage                                     │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Phase 2: Hypothesis + Templates                                │
│  ✅ HypothesisService generates valid JSON (>90% success rate)   │
│  ✅ Confidence scoring >0.8 for clear questions                  │
│  ✅ 5 templates generate correct structure                       │
│  ✅ Template selection matches question type (>85% accuracy)     │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Phase 3: Streaming                                             │
│  ✅ NDJSON messages parse correctly (100% valid JSON)            │
│  ✅ Streaming latency <500ms per message                         │
│  ✅ Widget serialization works for all types                     │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Phase 4: Quality Monitoring                                    │
│  ✅ Completeness checker detects missing fields (>90%)           │
│  ✅ Forms generated for missing information                      │
│  ✅ User submissions processed correctly                         │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Phase 5: API Integration                                       │
│  ✅ API endpoint responds <2s for simple queries                 │
│  ✅ WebSocket handles 100+ concurrent connections                │
│  ✅ API documentation complete                                   │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Phase 6: Frontend                                              │
│  ✅ Widgets render correctly (table, chart, form)                │
│  ✅ Streaming client handles 1000+ messages/min                  │
│  ✅ UI responsive (<100ms lag)                                   │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Phase 7: Testing                                               │
│  ✅ Unit tests: >80% coverage                                    │
│  ✅ Integration tests: All passing                               │
│  ✅ Load tests: 100 concurrent users, <2s response               │
│  ✅ Documentation: Complete + examples                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📞 Quick Reference

**Full Details:** `docs/IMPLEMENTATION_GAP_ANALYSIS_TODO.md` (8,000+ lines)
**Executive Summary:** `docs/TODO_EXECUTIVE_SUMMARY.md` (600 lines)
**Visual Roadmap:** This document

**Next Steps:**
1. Read Gap Analysis (30 min)
2. Setup environment (30 min)
3. Start Phase 1 (Day 1-3)

**Questions?** Check existing code:
- `backend/agents/framework/dependency_resolver.py` - Dependency resolution
- `backend/services/veritas_streaming_service.py` - Streaming
- `backend/agents/veritas_agent_template.py` - Template pattern

---

**READY TO BUILD! 🚀**

**Status:** 🟢 All design documents complete, ready to implement
**Timeline:** 18-25 Tage (Full) oder 10-12 Tage (MVP)
**Start:** Phase 1 (NLPService, ProcessBuilder, ProcessExecutor)
