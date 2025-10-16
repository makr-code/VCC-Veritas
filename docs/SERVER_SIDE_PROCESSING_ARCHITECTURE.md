# 🔄 VERITAS Server-Side Processing Architecture v5.0

**Basierend auf User-Gedankengerüst vom 12. Oktober 2025**

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Request-Response-Zyklus](#request-response-zyklus)
3. [JSON Schema](#json-schema)
4. [Streaming Protocol](#streaming-protocol)
5. [Phase-by-Phase Breakdown](#phase-by-phase-breakdown)
6. [Implementierung](#implementierung)

---

## 🎯 Übersicht

### Architektur-Prinzipien

```
User Query
    ↓
1. NLP Pre-Processing (query_enrichment, intent detection)
    ↓
2. Initial RAG Retrieval (semantic + graph)
    ↓
3. Hypothesis Generation (LLM Call 1: Was brauche ich noch?)
    ↓
4. Evidence Evaluation (RAG sources relevance scoring)
    ↓
5. Adaptive Template Construction (auto-generate structure)
    ↓
6. Answer Generation (LLM Call 2: Mit Quality Checks)
    ↓
7. Response Streaming (NDJSON mit Zwischenergebnissen)
```

**Key Features:**
- ✅ **Streaming Client Updates:** Jeder Prozessschritt sendet Status
- ✅ **Hypothesis-Driven:** LLM entscheidet Struktur basierend auf Evidence
- ✅ **Quality Monitoring:** Completeness, Accuracy, Consistency
- ✅ **Incremental Delivery:** Client sieht Fortschritt in Echtzeit

---

## 🔄 Request-Response-Zyklus

### Phase 1: Client Request

**HTTP POST** `/api/v1/query` oder **WebSocket** `/ws/query`

```json
{
  "user_id": "uuid-1234",
  "username": "johndoe",
  "query": "Ist für meinen Carport eine Baugenehmigung nötig?",
  "context": {
    "session_id": "session-5678",
    "previous_queries": [],
    "user_preferences": {
      "detail_level": "medium",
      "include_sources": true
    }
  },
  "metadata": {
    "timestamp": "2025-10-12T18:45:00Z",
    "source": "web",
    "device": "desktop",
    "language": "de"
  }
}
```

---

### Phase 2: Server Processing (7 Schritte)

#### Schritt 1: NLP Pre-Processing

**Server → Client (Stream Event 1):**
```json
{
  "type": "processing_step",
  "step_id": "nlp_preprocessing",
  "status": "completed",
  "timestamp": "2025-10-12T18:45:00.150Z",
  "data": {
    "nlp": {
      "query_enrichment": {
        "language": "de",
        "intent": "rechtliche_bewertung",
        "entities": ["Carport", "Baugenehmigung"],
        "query_type": "verwaltungsrechtliche_frage"
      },
      "parsed_query": {
        "main_topic": "Baugenehmigung",
        "subtopics": ["Carport", "Verfahrensfreiheit"],
        "keywords": ["Baugenehmigung", "Carport", "BauGB", "LBO", "Bauordnung"]
      },
      "estimated_complexity": "medium",
      "sentiment": "neutral"
    }
  }
}
```

**Backend Logic:**
```python
async def nlp_preprocessing(query: str) -> NLPResult:
    # 1. Spracherkennung (langdetect)
    language = detect_language(query)
    
    # 2. Intent Detection (keyword-based + LLM optional)
    intent = detect_intent(query)  # "rechtliche_bewertung", "prozess_navigation", etc.
    
    # 3. Entity Extraction (spaCy NER + custom rules)
    entities = extract_entities(query)  # ["Carport", "Baugenehmigung"]
    
    # 4. Query Expansion (Synonyme, Abkürzungen)
    keywords = expand_query(query)  # "Carport" → "Stellplatz", "Überdachung"
    
    # 5. Complexity Estimation (heuristic)
    complexity = estimate_complexity(query)  # "simple", "medium", "complex"
    
    return NLPResult(...)
```

---

#### Schritt 2: Initial RAG Retrieval

**Server → Client (Stream Event 2):**
```json
{
  "type": "processing_step",
  "step_id": "rag_retrieval",
  "status": "in_progress",
  "timestamp": "2025-10-12T18:45:00.300Z",
  "data": {
    "retrieval": {
      "semantic_search": {
        "status": "completed",
        "results_count": 15,
        "top_score": 0.89
      },
      "graph_search": {
        "status": "in_progress",
        "traversal_depth": 2
      }
    }
  }
}
```

**Update (Completion):**
```json
{
  "type": "processing_step",
  "step_id": "rag_retrieval",
  "status": "completed",
  "timestamp": "2025-10-12T18:45:00.550Z",
  "data": {
    "retrieval": {
      "semantic_search": {
        "status": "completed",
        "results_count": 15,
        "retrieval_time_ms": 120
      },
      "graph_search": {
        "status": "completed",
        "nodes_found": 8,
        "relationships_found": 12,
        "retrieval_time_ms": 130
      },
      "documents": [
        {
          "document_id": "doc_baugb_35",
          "title": "BauGB §35 - Bauen im Außenbereich",
          "source": "gesetze-im-internet.de",
          "relevance_score": 0.92,
          "chunk_type": "legal_text",
          "preview": "Im Außenbereich ist ein Vorhaben nur zulässig, wenn..."
        },
        {
          "document_id": "doc_lbo_bw_50",
          "title": "LBO BW §50 - Verfahrensfreie Vorhaben",
          "source": "landesrecht-bw.de",
          "relevance_score": 0.89,
          "chunk_type": "legal_text",
          "preview": "Verfahrensfrei sind: ... Gebäude ohne Aufenthaltsräume bis 30m²..."
        }
      ],
      "graph_context": [
        {
          "node_id": "process_baugenehmigung",
          "label": "Baugenehmigungsverfahren",
          "relationships": [
            {"type": "requires", "target": "zustaendigkeitspruefung"},
            {"type": "includes", "target": "formale_pruefung"}
          ]
        }
      ]
    }
  }
}
```

**Backend Logic:**
```python
async def rag_retrieval(nlp_result: NLPResult) -> RAGResult:
    # 1. Semantic Search (ChromaDB)
    semantic_results = await chroma_client.query(
        query_texts=[nlp_result.parsed_query.main_topic],
        n_results=15
    )
    
    # 2. Graph Search (Neo4j)
    graph_results = await neo4j_client.run(f"""
        MATCH (n:Concept {{name: '{nlp_result.entities[0]}'}})-[r*1..2]-(related)
        RETURN n, r, related
        LIMIT 20
    """)
    
    # 3. Hybrid Ranking (RRF - Reciprocal Rank Fusion)
    ranked_docs = reciprocal_rank_fusion(semantic_results, graph_results)
    
    return RAGResult(documents=ranked_docs, graph_context=graph_results)
```

---

#### Schritt 3: Hypothesis Generation (🧠 LLM Call 1)

**Server → Client (Stream Event 3):**
```json
{
  "type": "processing_step",
  "step_id": "hypothesis_generation",
  "status": "in_progress",
  "timestamp": "2025-10-12T18:45:00.600Z",
  "data": {
    "llm_call": {
      "model": "llama3.1:70b",
      "prompt_type": "hypothesis_generation",
      "estimated_tokens": 500,
      "status": "streaming"
    }
  }
}
```

**Update (Completion):**
```json
{
  "type": "processing_step",
  "step_id": "hypothesis_generation",
  "status": "completed",
  "timestamp": "2025-10-12T18:45:01.200Z",
  "data": {
    "hypothesis": {
      "required_criteria": [
        "Bundesland bestimmen",
        "Carport-Größe prüfen",
        "Grundstückslage klären (Bebauungsplan/Außenbereich)",
        "Bauordnung des Bundeslandes prüfen",
        "Verfahrensfreiheit bewerten"
      ],
      "missing_information": [
        {
          "key": "bundesland",
          "description": "Bundesland nicht angegeben",
          "required": true,
          "options": ["Baden-Württemberg", "Bayern", "Berlin", "..."]
        },
        {
          "key": "carport_groesse",
          "description": "Carport-Größe nicht angegeben",
          "required": true,
          "unit": "m²"
        },
        {
          "key": "grundstueckslage",
          "description": "Grundstückslage unklar",
          "required": true,
          "options": ["Bebauungsplan Innenbereich", "Außenbereich", "Unbeplanter Innenbereich"]
        }
      ],
      "available_information": [
        "BauGB §35 (Außenbereich) gefunden",
        "LBO BW §50 (Verfahrensfreiheit) gefunden",
        "Prozess 'Baugenehmigungsverfahren' im Graph verfügbar"
      ],
      "suggested_structure": {
        "base_framework": "verwaltungsrechtliche_frage",
        "sections": [
          {
            "id": "missing_info_form",
            "type": "interactive_form",
            "priority": 1,
            "fields": ["bundesland", "carport_groesse", "grundstueckslage"]
          },
          {
            "id": "legal_assessment",
            "type": "markdown",
            "priority": 2,
            "requires": ["bundesland", "carport_groesse"]
          },
          {
            "id": "bundeslaender_comparison",
            "type": "table",
            "priority": 3
          },
          {
            "id": "process_graph",
            "type": "neo4j_graph",
            "priority": 4,
            "condition": "if genehmigungspflichtig"
          }
        ]
      },
      "confidence_estimate": 0.55,
      "confidence_reason": "Kernfrage identifiziert, aber 3 kritische Informationen fehlen",
      "recommended_token_budget": 3500,
      "recommended_detail_level": "medium"
    }
  }
}
```

**Backend Logic:**
```python
HYPOTHESIS_GENERATION_PROMPT = """
Du bist VERITAS Hypothesis Generator.

USER QUERY: {query}

RAG CONTEXT (Semantic Search Top 5):
{semantic_docs}

RAG CONTEXT (Graph Search):
{graph_context}

AUFGABE:
Analysiere die User-Frage und den RAG-Kontext.
Erstelle eine Hypothese: Welche Informationen brauchst du, um diese Frage vollständig und korrekt zu beantworten?

OUTPUT (JSON):
{{
  "required_criteria": ["Kriterium 1", "Kriterium 2", ...],
  "missing_information": [
    {{"key": "...", "description": "...", "required": true/false, "options": [...], "unit": "..."}}
  ],
  "available_information": ["Info 1 aus RAG", "Info 2 aus RAG", ...],
  "suggested_structure": {{
    "base_framework": "verwaltungsrechtliche_frage" | "vollstaendigkeitspruefung" | ...,
    "sections": [
      {{"id": "...", "type": "interactive_form"|"markdown"|"table"|"graph", "priority": 1-5}}
    ]
  }},
  "confidence_estimate": 0.0-1.0,
  "confidence_reason": "Warum diese Confidence?",
  "recommended_token_budget": 1000-16000,
  "recommended_detail_level": "simple"|"medium"|"detailed"
}}
"""

async def generate_hypothesis(query: str, rag_result: RAGResult) -> Hypothesis:
    prompt = HYPOTHESIS_GENERATION_PROMPT.format(
        query=query,
        semantic_docs=format_semantic_docs(rag_result.documents[:5]),
        graph_context=format_graph_context(rag_result.graph_context)
    )
    
    # LLM Call 1 (FAST, ~500 tokens, no streaming needed)
    response = await ollama_client.generate(
        model="llama3.1:70b",
        prompt=prompt,
        options={"num_predict": 1024, "temperature": 0.3}
    )
    
    hypothesis = json.loads(response['response'])
    return Hypothesis(**hypothesis)
```

---

#### Schritt 4: Evidence Evaluation

**Server → Client (Stream Event 4):**
```json
{
  "type": "processing_step",
  "step_id": "evidence_evaluation",
  "status": "completed",
  "timestamp": "2025-10-12T18:45:01.350Z",
  "data": {
    "evidence": {
      "documents_evaluated": 15,
      "documents_relevant": 8,
      "documents_used": 5,
      "scores": [
        {
          "document_id": "doc_baugb_35",
          "relevance_score": 0.92,
          "criteria_coverage": ["Grundstückslage klären"],
          "used_in_response": true
        },
        {
          "document_id": "doc_lbo_bw_50",
          "relevance_score": 0.89,
          "criteria_coverage": ["Carport-Größe prüfen", "Verfahrensfreiheit"],
          "used_in_response": true
        }
      ]
    }
  }
}
```

**Backend Logic:**
```python
async def evaluate_evidence(hypothesis: Hypothesis, rag_result: RAGResult) -> EvidenceEvaluation:
    evaluated_docs = []
    
    for doc in rag_result.documents:
        # Check which required_criteria this document covers
        criteria_coverage = []
        for criterion in hypothesis.required_criteria:
            if criterion_is_covered(doc.content, criterion):
                criteria_coverage.append(criterion)
        
        # Re-rank based on hypothesis relevance
        hypothesis_score = len(criteria_coverage) / len(hypothesis.required_criteria)
        final_score = (doc.relevance_score + hypothesis_score) / 2
        
        evaluated_docs.append({
            "document_id": doc.id,
            "relevance_score": final_score,
            "criteria_coverage": criteria_coverage,
            "used_in_response": final_score > 0.7
        })
    
    # Sort by final score
    evaluated_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return EvidenceEvaluation(
        documents_evaluated=len(rag_result.documents),
        documents_relevant=len([d for d in evaluated_docs if d['relevance_score'] > 0.5]),
        documents_used=len([d for d in evaluated_docs if d['used_in_response']]),
        scores=evaluated_docs
    )
```

---

#### Schritt 5: Adaptive Template Construction

**Server → Client (Stream Event 5):**
```json
{
  "type": "processing_step",
  "step_id": "template_construction",
  "status": "completed",
  "timestamp": "2025-10-12T18:45:01.450Z",
  "data": {
    "template": {
      "base_framework": "verwaltungsrechtliche_frage",
      "sections_generated": 4,
      "interactive_elements": 1,
      "estimated_response_length": "medium",
      "system_prompt_hash": "abc123def456",
      "structure": [
        {
          "section_id": "missing_info_form",
          "type": "interactive_form",
          "title": "Zusätzliche Informationen benötigt",
          "fields": [
            {"name": "bundesland", "type": "dropdown", "label": "In welchem Bundesland?"},
            {"name": "carport_groesse", "type": "text", "label": "Carport-Größe (m²)?"},
            {"name": "grundstueckslage", "type": "dropdown", "label": "Grundstückslage?"}
          ]
        },
        {
          "section_id": "legal_assessment",
          "type": "markdown",
          "title": "Rechtliche Einordnung",
          "quality_requirements": {
            "completeness_min": 0.9,
            "accuracy_min": 0.92,
            "required_sources": ["BauGB", "LBO"]
          }
        },
        {
          "section_id": "bundeslaender_comparison",
          "type": "table",
          "title": "Bundesländer-Vergleich",
          "columns": ["Bundesland", "Verfahrensfreiheit bis", "Besonderheiten"]
        },
        {
          "section_id": "process_graph",
          "type": "neo4j_graph",
          "title": "Baugenehmigungsprozess",
          "query": "MATCH (n:Process {name: 'Baugenehmigung'})-[r*1..3]-(related) RETURN n,r,related"
        }
      ]
    }
  }
}
```

**Backend Logic:**
```python
class AdaptiveTemplateGenerator:
    BASIC_FRAMEWORKS = {
        'verwaltungsrechtliche_frage': {
            'default_sections': ['legal_assessment', 'sources'],
            'default_token_budget': 2500,
            'quality_requirements': {'completeness_min': 0.9, 'accuracy_min': 0.92}
        },
        # ... other frameworks
    }
    
    async def construct_template(self, hypothesis: Hypothesis, evidence: EvidenceEvaluation) -> AdaptiveTemplate:
        # 1. Select base framework
        base_framework = self.BASIC_FRAMEWORKS[hypothesis.suggested_structure['base_framework']]
        
        # 2. Generate sections from hypothesis
        sections = []
        
        # 2a. Interactive Form (if missing info)
        if hypothesis.missing_information:
            form_section = self._create_interactive_form(hypothesis.missing_information)
            sections.append(form_section)
        
        # 2b. Auto-generate sections from suggested_structure
        for section_spec in hypothesis.suggested_structure['sections']:
            if section_spec['type'] == 'markdown':
                section = self._create_markdown_section(section_spec, evidence)
            elif section_spec['type'] == 'table':
                section = self._create_table_section(section_spec, evidence)
            elif section_spec['type'] == 'neo4j_graph':
                section = self._create_graph_section(section_spec)
            
            sections.append(section)
        
        # 3. Generate unique system prompt
        system_prompt = self._generate_system_prompt(hypothesis, evidence, base_framework)
        
        return AdaptiveTemplate(
            base_framework=hypothesis.suggested_structure['base_framework'],
            sections=sections,
            system_prompt=system_prompt,
            token_budget=hypothesis.recommended_token_budget
        )
    
    def _create_interactive_form(self, missing_info: List[MissingInfo]) -> FormSection:
        fields = []
        for info in missing_info:
            if info.options:
                field = {"name": info.key, "type": "dropdown", "options": info.options}
            else:
                field = {"name": info.key, "type": "text", "placeholder": f"z.B. {info.unit}" if info.unit else ""}
            
            fields.append(field)
        
        return FormSection(id="missing_info_form", fields=fields)
```

---

#### Schritt 6: Answer Generation (🧠 LLM Call 2 - Streaming)

**Server → Client (Stream Event 6 - Start):**
```json
{
  "type": "processing_step",
  "step_id": "answer_generation",
  "status": "in_progress",
  "timestamp": "2025-10-12T18:45:01.500Z",
  "data": {
    "llm_call": {
      "model": "llama3.1:70b",
      "prompt_type": "adaptive_response",
      "token_budget": 3500,
      "quality_monitoring": true,
      "status": "streaming"
    }
  }
}
```

**Stream Event 6.1 - Text Chunk (NDJSON):**
```json
{"type": "text_chunk", "section_id": "missing_info_form", "content": "# Zusätzliche Informationen benötigt\n\nFür eine präzise Antwort benötige ich noch folgende Angaben:\n"}
{"type": "widget", "section_id": "missing_info_form", "widget": {"type": "interactive_form", "fields": [{"name": "bundesland", "type": "dropdown", "label": "In welchem Bundesland befindet sich das Grundstück?", "options": ["Baden-Württemberg", "Bayern", "..."]}, {"name": "carport_groesse", "type": "text", "label": "Wie groß ist der geplante Carport (m²)?", "placeholder": "z.B. 20"}, {"name": "grundstueckslage", "type": "dropdown", "label": "Wo liegt das Grundstück?", "options": ["Bebauungsplan Innenbereich", "Außenbereich", "Unbeplanter Innenbereich"]}]}}
{"type": "text_chunk", "section_id": "legal_assessment", "content": "\n\n## Rechtliche Einordnung (vorläufig)\n\n"}
{"type": "text_chunk", "section_id": "legal_assessment", "content": "Gemäß **BauGB §35** sind im Außenbereich Vorhaben nur zulässig, wenn sie einem land- oder forstwirtschaftlichen Betrieb dienen oder die Errichtung sonstiger Vorhaben im Einzelfall zulässig ist.\n\n"}
{"type": "quality_check", "check_type": "accuracy", "status": "passed", "details": {"source_cited": "BauGB §35", "source_valid": true, "document_id": "doc_baugb_35"}}
{"type": "text_chunk", "section_id": "legal_assessment", "content": "Die **Landesbauordnungen** (LBO) der einzelnen Bundesländer regeln jedoch Verfahrensfreiheit für bestimmte bauliche Anlagen. Beispielsweise sieht die **LBO Baden-Württemberg §50** vor, dass Gebäude ohne Aufenthaltsräume bis 30m² verfahrensfrei sind.\n\n"}
{"type": "quality_check", "check_type": "accuracy", "status": "passed", "details": {"source_cited": "LBO BW §50", "source_valid": true, "document_id": "doc_lbo_bw_50"}}
{"type": "text_chunk", "section_id": "bundeslaender_comparison", "content": "\n\n## Bundesländer-Vergleich\n\n"}
{"type": "widget", "section_id": "bundeslaender_comparison", "widget": {"type": "table", "headers": ["Bundesland", "Verfahrensfreiheit bis", "Besonderheiten"], "rows": [["Baden-Württemberg", "30 m²", "Gebäude ohne Aufenthaltsräume"], ["Bayern", "40 m²", "Garagen und Stellplätze"], ["..."], ...]}}
{"type": "quality_check", "check_type": "completeness", "status": "in_progress", "details": {"criteria_addressed": 3, "criteria_total": 5, "percentage": 0.60}}
{"type": "text_chunk", "section_id": "process_graph", "content": "\n\n## Baugenehmigungsprozess (falls erforderlich)\n\n"}
{"type": "widget", "section_id": "process_graph", "widget": {"type": "neo4j_graph", "query": "MATCH (n:Process {name: 'Baugenehmigung'})-[r*1..3]-(related) RETURN n,r,related", "layout": "hierarchical"}}
{"type": "quality_check", "check_type": "completeness", "status": "passed", "details": {"criteria_addressed": 5, "criteria_total": 5, "percentage": 1.0}}
{"type": "response_end", "section_id": null}
```

**Stream Event 6.2 - Completion:**
```json
{
  "type": "processing_step",
  "step_id": "answer_generation",
  "status": "completed",
  "timestamp": "2025-10-12T18:45:03.800Z",
  "data": {
    "generation_stats": {
      "tokens_generated": 2847,
      "generation_time_ms": 2300,
      "quality_checks_performed": 12,
      "quality_checks_passed": 12,
      "quality_checks_failed": 0
    }
  }
}
```

**Backend Logic:**
```python
async def generate_answer_streaming(
    template: AdaptiveTemplate,
    hypothesis: Hypothesis,
    evidence: EvidenceEvaluation
) -> AsyncGenerator[dict, None]:
    
    # 1. Build system prompt
    system_prompt = template.system_prompt
    
    # 2. Build user prompt with RAG context
    user_prompt = f"""
USER QUERY: {original_query}

REQUIRED CRITERIA TO ADDRESS:
{json.dumps(hypothesis.required_criteria, indent=2)}

RAG CONTEXT:
{format_rag_context(evidence.scores)}

TEMPLATE STRUCTURE:
{json.dumps([s.dict() for s in template.sections], indent=2)}

Generate response following the template structure.
"""
    
    # 3. Stream LLM response
    quality_monitor = ResponseQualityMonitor(hypothesis, evidence)
    
    async for chunk in ollama_client.generate_stream(
        model="llama3.1:70b",
        system=system_prompt,
        prompt=user_prompt,
        options={"num_predict": template.token_budget}
    ):
        # Parse NDJSON chunk
        chunk_data = parse_ndjson_chunk(chunk['response'])
        
        # Quality check
        quality_result = await quality_monitor.check_chunk(chunk_data)
        if not quality_result.passed:
            # Emit quality check failure
            yield {
                "type": "quality_check",
                "check_type": quality_result.check_type,
                "status": "failed",
                "details": quality_result.details,
                "action": quality_result.action
            }
            
            # Handle self-correction if needed
            if quality_result.action == "request_correction":
                # Pause streaming, request correction, resume
                pass
        
        # Emit chunk to client
        yield chunk_data
    
    # 4. Final quality check
    final_quality = quality_monitor.final_check()
    yield {
        "type": "quality_summary",
        "completeness": final_quality.completeness,
        "accuracy": final_quality.accuracy,
        "consistency": final_quality.consistency
    }
```

---

#### Schritt 7: Response Finalization

**Server → Client (Stream Event 7):**
```json
{
  "type": "processing_complete",
  "timestamp": "2025-10-12T18:45:03.850Z",
  "data": {
    "total_processing_time_ms": 3700,
    "steps_completed": 7,
    "quality_summary": {
      "completeness": 0.95,
      "accuracy": 0.92,
      "consistency": 0.88,
      "overall_confidence": 0.55,
      "confidence_reason": "Alle Kriterien behandelt, aber 3 Informationen fehlen noch"
    },
    "metadata": {
      "tokens_used_hypothesis": 487,
      "tokens_used_response": 2847,
      "tokens_total": 3334,
      "documents_used": 5,
      "llm_calls": 2
    }
  }
}
```

---

## 📡 Streaming Protocol (NDJSON über WebSocket/SSE)

### Connection Setup

**WebSocket:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/query');

ws.onopen = () => {
  ws.send(JSON.stringify({
    user_id: "uuid-1234",
    query: "Ist für meinen Carport eine Baugenehmigung nötig?",
    context: {...}
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleStreamEvent(data);
};
```

**Server-Sent Events (SSE):**
```python
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

@app.post("/api/v1/query/stream")
async def query_stream(request: QueryRequest):
    async def event_generator():
        # Step 1: NLP
        yield {"event": "processing_step", "data": json.dumps({...})}
        
        # Step 2: RAG
        yield {"event": "processing_step", "data": json.dumps({...})}
        
        # ... all 7 steps
    
    return EventSourceResponse(event_generator())
```

---

### Event Types

| Event Type | Wann? | Zweck |
|------------|-------|-------|
| `processing_step` | Jeder Prozessschritt | Status-Update für Client (Fortschrittsbalken) |
| `text_chunk` | LLM generiert Text | Incrementales Rendering (wie ChatGPT) |
| `widget` | LLM generiert Widget | Rendern von Forms, Tabellen, Graphs |
| `quality_check` | Während Streaming | Transparenz über Quality Monitoring |
| `quality_summary` | Am Ende | Finale Quality Metrics |
| `processing_complete` | Ganz am Ende | Metadata, Stats, Closing |

---

### Client-Side Handling

```javascript
function handleStreamEvent(event) {
  switch(event.type) {
    case 'processing_step':
      updateProgressBar(event.step_id, event.status);
      if (event.status === 'completed') {
        displayStepResult(event.step_id, event.data);
      }
      break;
    
    case 'text_chunk':
      appendTextToSection(event.section_id, event.content);
      break;
    
    case 'widget':
      renderWidget(event.section_id, event.widget);
      break;
    
    case 'quality_check':
      displayQualityBadge(event.check_type, event.status);
      break;
    
    case 'quality_summary':
      displayFinalQuality(event.data);
      break;
    
    case 'processing_complete':
      hideProgressBar();
      displayMetadata(event.data.metadata);
      break;
  }
}

function renderWidget(sectionId, widget) {
  const container = document.getElementById(sectionId);
  
  switch(widget.type) {
    case 'interactive_form':
      const form = createForm(widget.fields);
      form.onsubmit = (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        ws.send(JSON.stringify({
          type: 'form_submission',
          data: Object.fromEntries(formData)
        }));
      };
      container.appendChild(form);
      break;
    
    case 'table':
      const table = createTable(widget.headers, widget.rows);
      container.appendChild(table);
      break;
    
    case 'neo4j_graph':
      renderNeo4jGraph(container, widget.query);
      break;
  }
}
```

---

## 🔧 Phase-by-Phase Implementation

### Phase 1: Foundation (3-4 Tage)

**Files to Create:**
```
backend/api/v1/
├── query_endpoint.py         # FastAPI endpoints
├── streaming_handler.py      # WebSocket/SSE logic
└── models.py                 # Pydantic models

backend/services/
├── nlp_service.py            # NLP Pre-Processing
├── rag_service.py            # RAG Retrieval (semantic + graph)
├── hypothesis_service.py     # Hypothesis Generation (LLM Call 1)
├── evidence_service.py       # Evidence Evaluation
├── template_service.py       # Adaptive Template Construction
└── response_service.py       # Answer Generation (LLM Call 2)
```

**Pydantic Models:**
```python
# backend/api/v1/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class QueryRequest(BaseModel):
    user_id: UUID
    username: str
    query: str
    context: Optional[Dict[str, Any]] = {}
    metadata: Dict[str, Any]

class NLPResult(BaseModel):
    language: str
    intent: str
    entities: List[str]
    parsed_query: Dict[str, Any]
    estimated_complexity: str
    sentiment: str

class RAGDocument(BaseModel):
    document_id: str
    title: str
    source: str
    relevance_score: float
    chunk_type: str
    preview: str
    content: str

class RAGResult(BaseModel):
    documents: List[RAGDocument]
    graph_context: List[Dict[str, Any]]
    retrieval_time_ms: int

class MissingInformation(BaseModel):
    key: str
    description: str
    required: bool
    options: Optional[List[str]] = None
    unit: Optional[str] = None

class Hypothesis(BaseModel):
    required_criteria: List[str]
    missing_information: List[MissingInformation]
    available_information: List[str]
    suggested_structure: Dict[str, Any]
    confidence_estimate: float
    confidence_reason: str
    recommended_token_budget: int
    recommended_detail_level: str

class EvidenceScore(BaseModel):
    document_id: str
    relevance_score: float
    criteria_coverage: List[str]
    used_in_response: bool

class EvidenceEvaluation(BaseModel):
    documents_evaluated: int
    documents_relevant: int
    documents_used: int
    scores: List[EvidenceScore]

class AdaptiveTemplate(BaseModel):
    base_framework: str
    sections: List[Dict[str, Any]]
    system_prompt: str
    token_budget: int

class StreamEvent(BaseModel):
    type: str  # processing_step, text_chunk, widget, quality_check, etc.
    timestamp: datetime
    data: Dict[str, Any]
```

---

### Phase 2: NLP + RAG (2-3 Tage)

**NLP Service:**
```python
# backend/services/nlp_service.py
from langdetect import detect
import spacy

class NLPService:
    def __init__(self):
        self.nlp = spacy.load("de_core_news_lg")
    
    async def process(self, query: str) -> NLPResult:
        # 1. Language detection
        language = detect(query)
        
        # 2. Intent detection (keyword-based for now)
        intent = self._detect_intent(query)
        
        # 3. Entity extraction
        doc = self.nlp(query)
        entities = [ent.text for ent in doc.ents]
        
        # 4. Keyword expansion
        keywords = self._expand_keywords(query)
        
        # 5. Complexity estimation
        complexity = self._estimate_complexity(query)
        
        return NLPResult(
            language=language,
            intent=intent,
            entities=entities,
            parsed_query={
                "main_topic": self._extract_main_topic(doc),
                "subtopics": self._extract_subtopics(doc),
                "keywords": keywords
            },
            estimated_complexity=complexity,
            sentiment="neutral"
        )
    
    def _detect_intent(self, query: str) -> str:
        if any(kw in query.lower() for kw in ["baugenehmigung", "genehmigung", "zulässig"]):
            return "rechtliche_bewertung"
        elif any(kw in query.lower() for kw in ["prozess", "ablauf", "schritte"]):
            return "prozess_navigation"
        else:
            return "information_request"
```

**RAG Service:**
```python
# backend/services/rag_service.py
from chromadb import Client as ChromaClient
from neo4j import AsyncGraphDatabase

class RAGService:
    def __init__(self, chroma_client: ChromaClient, neo4j_driver):
        self.chroma = chroma_client
        self.neo4j = neo4j_driver
    
    async def retrieve(self, nlp_result: NLPResult) -> RAGResult:
        # 1. Semantic search
        semantic_results = await self._semantic_search(nlp_result)
        
        # 2. Graph search
        graph_results = await self._graph_search(nlp_result)
        
        # 3. Hybrid ranking
        ranked_docs = self._reciprocal_rank_fusion(semantic_results, graph_results)
        
        return RAGResult(
            documents=ranked_docs,
            graph_context=graph_results,
            retrieval_time_ms=...
        )
    
    async def _semantic_search(self, nlp_result: NLPResult) -> List[RAGDocument]:
        collection = self.chroma.get_collection("veritas_knowledge")
        results = collection.query(
            query_texts=[nlp_result.parsed_query['main_topic']],
            n_results=15
        )
        
        return [RAGDocument(...) for ... in results]
    
    async def _graph_search(self, nlp_result: NLPResult) -> List[Dict]:
        async with self.neo4j.session() as session:
            result = await session.run(f"""
                MATCH (n:Concept {{name: '{nlp_result.entities[0]}'}})
                      -[r*1..2]-(related)
                RETURN n, r, related
                LIMIT 20
            """)
            
            return await result.data()
```

---

### Phase 3: Hypothesis Generation (2-3 Tage)

```python
# backend/services/hypothesis_service.py
from .prompts import HYPOTHESIS_GENERATION_PROMPT

class HypothesisService:
    def __init__(self, ollama_client):
        self.ollama = ollama_client
    
    async def generate(self, query: str, rag_result: RAGResult) -> Hypothesis:
        # 1. Format prompt
        prompt = HYPOTHESIS_GENERATION_PROMPT.format(
            query=query,
            semantic_docs=self._format_semantic_docs(rag_result.documents[:5]),
            graph_context=self._format_graph_context(rag_result.graph_context)
        )
        
        # 2. LLM Call 1 (FAST, ~500 tokens)
        response = await self.ollama.generate(
            model="llama3.1:70b",
            prompt=prompt,
            options={
                "num_predict": 1024,
                "temperature": 0.3,
                "format": "json"  # Force JSON output
            }
        )
        
        # 3. Parse JSON
        hypothesis_data = json.loads(response['response'])
        
        return Hypothesis(**hypothesis_data)
```

---

### Phase 4: Template Construction + Answer Generation (3-4 Tage)

**Template Service:**
```python
# backend/services/template_service.py
class TemplateService:
    BASIC_FRAMEWORKS = {...}  # As defined in v5.0 spec
    
    async def construct(self, hypothesis: Hypothesis, evidence: EvidenceEvaluation) -> AdaptiveTemplate:
        base_framework = self.BASIC_FRAMEWORKS[hypothesis.suggested_structure['base_framework']]
        
        sections = []
        
        # Auto-generate interactive form
        if hypothesis.missing_information:
            form_section = self._create_interactive_form(hypothesis.missing_information)
            sections.append(form_section)
        
        # Auto-generate other sections
        for section_spec in hypothesis.suggested_structure['sections']:
            section = self._create_section(section_spec, evidence)
            sections.append(section)
        
        # Generate system prompt
        system_prompt = self._generate_system_prompt(hypothesis, evidence, base_framework)
        
        return AdaptiveTemplate(
            base_framework=hypothesis.suggested_structure['base_framework'],
            sections=sections,
            system_prompt=system_prompt,
            token_budget=hypothesis.recommended_token_budget
        )
```

**Response Service:**
```python
# backend/services/response_service.py
class ResponseService:
    async def generate_streaming(
        self,
        template: AdaptiveTemplate,
        hypothesis: Hypothesis,
        evidence: EvidenceEvaluation
    ) -> AsyncGenerator[StreamEvent, None]:
        
        # Build prompts
        system_prompt = template.system_prompt
        user_prompt = self._build_user_prompt(hypothesis, evidence, template)
        
        # Quality monitor
        quality_monitor = ResponseQualityMonitor(hypothesis, evidence)
        
        # Stream LLM response
        async for chunk in self.ollama.generate_stream(
            model="llama3.1:70b",
            system=system_prompt,
            prompt=user_prompt,
            options={"num_predict": template.token_budget}
        ):
            # Parse chunk
            chunk_data = parse_ndjson_chunk(chunk['response'])
            
            # Quality check
            quality_result = await quality_monitor.check_chunk(chunk_data)
            
            # Emit events
            yield StreamEvent(type="text_chunk", data=chunk_data, ...)
            
            if not quality_result.passed:
                yield StreamEvent(type="quality_check", data=quality_result.dict(), ...)
```

---

### Phase 5: API Endpoints + Streaming (2-3 Tage)

```python
# backend/api/v1/query_endpoint.py
from fastapi import FastAPI, WebSocket
from sse_starlette.sse import EventSourceResponse

app = FastAPI()

@app.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    await websocket.accept()
    
    # Receive query
    data = await websocket.receive_json()
    query_request = QueryRequest(**data)
    
    # Process pipeline
    async for event in query_pipeline(query_request):
        await websocket.send_json(event.dict())
    
    await websocket.close()

@app.post("/api/v1/query/stream")
async def sse_query(request: QueryRequest):
    async def event_generator():
        async for event in query_pipeline(request):
            yield {
                "event": event.type,
                "data": json.dumps(event.data)
            }
    
    return EventSourceResponse(event_generator())

async def query_pipeline(request: QueryRequest):
    # Step 1: NLP
    nlp_result = await nlp_service.process(request.query)
    yield StreamEvent(type="processing_step", step_id="nlp_preprocessing", ...)
    
    # Step 2: RAG
    rag_result = await rag_service.retrieve(nlp_result)
    yield StreamEvent(type="processing_step", step_id="rag_retrieval", ...)
    
    # Step 3: Hypothesis
    hypothesis = await hypothesis_service.generate(request.query, rag_result)
    yield StreamEvent(type="processing_step", step_id="hypothesis_generation", ...)
    
    # Step 4: Evidence
    evidence = await evidence_service.evaluate(hypothesis, rag_result)
    yield StreamEvent(type="processing_step", step_id="evidence_evaluation", ...)
    
    # Step 5: Template
    template = await template_service.construct(hypothesis, evidence)
    yield StreamEvent(type="processing_step", step_id="template_construction", ...)
    
    # Step 6: Answer (streaming)
    async for response_event in response_service.generate_streaming(template, hypothesis, evidence):
        yield response_event
    
    # Step 7: Finalization
    yield StreamEvent(type="processing_complete", ...)
```

---

## 🎯 Zusammenfassung

### Was haben wir erreicht?

1. ✅ **Dein JSON-Gedankengerüst** als Basis genommen
2. ✅ **v5.0 Hypothesis-Driven Approach** integriert
3. ✅ **7-Step Pipeline** definiert (NLP → RAG → Hypothesis → Evidence → Template → Answer → Finalize)
4. ✅ **Streaming Protocol** mit NDJSON + WebSocket/SSE
5. ✅ **Client-Side Handling** (JavaScript-Beispiel)
6. ✅ **Backend Services** (NLP, RAG, Hypothesis, Template, Response)
7. ✅ **API Endpoints** (WebSocket + SSE)

### Key Features

- 🔄 **Streaming Updates:** Client sieht jeden Schritt in Echtzeit
- 🧠 **Hypothesis-Driven:** LLM entscheidet Struktur basierend auf RAG
- 🎯 **Quality Monitoring:** Completeness, Accuracy, Consistency während Streaming
- 📊 **Interactive Forms:** Auto-generiert aus missing_information
- 📈 **Transparent Confidence:** Von Anfang an sichtbar

### Nächste Schritte

Möchtest du:
1. **Backend Services implementieren?** (Start mit NLP + RAG)
2. **Frontend Client erstellen?** (WebSocket-Handler + UI)
3. **Quality Monitoring verfeinern?** (Detaillierte Checks)

Was ist deine Präferenz? 🚀
