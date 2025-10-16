# 🧠 VERITAS Adaptive Response Framework - Konzept v5.0

**Version:** v5.0.0 (LLM-Generierte Adaptive Templates)  
**Created:** 12. Oktober 2025, 18:30 Uhr  
**Status:** 📋 KONZEPTPHASE - Paradigmenwechsel

---

## 🎯 Paradigmenwechsel: Von Fix zu Adaptiv

### ❌ **ALT (v4.1): Feste Template-Bibliothek**
```python
# 5 vordefinierte Templates (zustaendigkeit_behoerde, formale_pruefung, ...)
# Problem: Starr, kann nicht auf unerwartete Fragen reagieren
template = PromptTemplateLibrary.get_template('rechtliche_pruefung')
```

### ✅ **NEU (v5.0): LLM-Generierte Adaptive Templates**
```python
# LLM erstellt Template basierend auf Frage + RAG Kontext
# Vorteil: Flexibel, passt sich jeder Frage an
template = await AdaptiveTemplateGenerator.generate_from_query(
    user_query="Ist eine Baugenehmigung für mein Carport nötig?",
    rag_context=semantic_search_results + process_graph_results
)
```

---

## 🏗️ Neue Architektur: 3-Phasen-System

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: RAG-BASED HYPOTHESIS GENERATION                           │
│ ─────────────────────────────────────────────────────────────────── │
│ User Query: "Ist eine Baugenehmigung für mein Carport nötig?"      │
│                                    ↓                                │
│ RAG System (Parallel):                                             │
│  1. Semantic Search (ChromaDB) → Relevante Paragraphen             │
│  2. Process Graph (Neo4j) → Verwaltungsprozess-Schritte            │
│                                    ↓                                │
│ LLM Hypothesis Generation (SCHNELL, ~500 Tokens):                 │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ System Prompt:                                                │ │
│  │ "Basierend auf der Frage und dem RAG-Kontext, erstelle eine  │ │
│  │  Hypothese: Welche Informationen brauchst du noch?           │ │
│  │  Output als JSON mit:                                        │ │
│  │  - required_criteria: [Liste von Prüfkriterien]             │ │
│  │  - missing_information: [Was fehlt noch?]                   │ │
│  │  - suggested_structure: [Antwort-Struktur]                  │ │
│  │  - confidence_estimate: float (0.0-1.0)"                    │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                    ↓                                │
│ Output (JSON):                                                     │
│  {                                                                 │
│    "required_criteria": [                                          │
│      "Gebäudeklasse (Carport = Gebäude?)",                        │
│      "Grundstückslage (Außenbereich vs. Bebauungsplan)",          │
│      "Bundesland-spezifische Verfahrensfreiheit",                 │
│      "Abstandsflächen zu Nachbargrundstücken"                     │
│    ],                                                             │
│    "missing_information": [                                        │
│      "Bundesland nicht angegeben → LBO unklar",                   │
│      "Carport-Größe/Höhe nicht angegeben → Verfahrensfreiheit?"   │
│    ],                                                             │
│    "suggested_structure": {                                        │
│      "sections": [                                                │
│        {"type": "question_clarification", "priority": 1},         │
│        {"type": "legal_assessment", "priority": 2},               │
│        {"type": "process_steps", "priority": 3},                  │
│        {"type": "conditions_table", "priority": 4}                │
│      ]                                                            │
│    },                                                             │
│    "confidence_estimate": 0.65,  # Mittel (Info fehlt)           │
│    "estimated_complexity": "medium",                              │
│    "recommended_token_budget": 3500                               │
│  }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: TEMPLATE CONSTRUCTION FROM HYPOTHESIS                     │
│ ─────────────────────────────────────────────────────────────────── │
│ Input: Hypothesis JSON + Basic Template Frameworks                 │
│                                    ↓                                │
│ Template Generator:                                                │
│  1. Wähle Basic Framework (z.B. "verwaltungsrechtliche_frage")    │
│  2. Füge Hypothesis-basierte Sections hinzu                       │
│  3. Generiere Widget-Specs basierend auf required_criteria        │
│  4. Setze Token-Budget (aus Hypothesis.recommended_token_budget)  │
│                                    ↓                                │
│ Generated Template (Adaptive):                                     │
│  {                                                                 │
│    "template_id": "adaptive_carport_genehmigung_2025-10-12",     │
│    "base_framework": "verwaltungsrechtliche_frage",               │
│    "system_prompt": "[AUTO-GENERIERT basierend auf Hypothesis]",  │
│    "required_tokens": 3500,  # Aus Hypothesis                     │
│    "response_structure": {                                         │
│      "sections": [                                                │
│        {                                                          │
│          "id": "question_clarification",                          │
│          "title": "Fehlende Informationen",                      │
│          "widget": {                                              │
│            "type": "interactive_form",                            │
│            "fields": [                                            │
│              {"name": "bundesland", "type": "dropdown",           │
│               "options": ["Baden-Württemberg", "Bayern", ...]},  │
│              {"name": "carport_groesse", "type": "text",          │
│               "placeholder": "z.B. 20m²"},                        │
│              {"name": "carport_hoehe", "type": "text",            │
│               "placeholder": "z.B. 2.5m"}                         │
│            ]                                                      │
│          }                                                        │
│        },                                                         │
│        {                                                          │
│          "id": "legal_assessment",                                │
│          "title": "Rechtliche Einordnung",                       │
│          "content_type": "markdown"                               │
│        },                                                         │
│        {                                                          │
│          "id": "process_steps",                                   │
│          "title": "Verfahrensschritte",                          │
│          "widget": {                                              │
│            "type": "process_graph",                               │
│            "data_source": "neo4j_query",                          │
│            "query": "MATCH (p:Process {type:'Baugenehmigung'})..." │
│          }                                                        │
│        },                                                         │
│        {                                                          │
│          "id": "conditions_table",                                │
│          "title": "Verfahrensfreiheit nach Bundesland",          │
│          "widget": {                                              │
│            "type": "table",                                       │
│            "headers": ["Bundesland", "Max. Größe", "Max. Höhe",  │
│                        "Genehmigungsfrei?"],                      │
│            "rows": "[AUTO-POPULATED from RAG]"                    │
│          }                                                        │
│        }                                                          │
│      ]                                                            │
│    }                                                              │
│  }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: ITERATIVE RESPONSE GENERATION WITH QUALITY CHECKS         │
│ ─────────────────────────────────────────────────────────────────── │
│ LLM Response Generation (mit adaptivem Template):                  │
│                                    ↓                                │
│ STREAMING (NDJSON):                                                │
│  {"type":"response_start","metadata":{"template":"adaptive_..."}} │
│  {"type":"section_start","section_id":"question_clarification"}   │
│  {"type":"text_chunk","content":"Für eine präzise Antwort..."}    │
│  {"type":"widget","widget":{"type":"interactive_form",...}}       │
│  {"type":"section_end","section_id":"question_clarification"}     │
│                                    ↓                                │
│ QUALITY CHECKS (während Streaming):                                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Backend Quality Monitor:                                      │ │
│  │  1. Vollständigkeit: Alle required_criteria behandelt?       │ │
│  │  2. Accuracy: RAG-Quellen korrekt zitiert?                   │ │
│  │  3. Konsistenz: Widersprüche in Antwort?                     │ │
│  │  4. Token-Budget: Innerhalb estimated_tokens?                │ │
│  │                                                               │ │
│  │ Bei Problemen:                                                │ │
│  │  → Streaming pausieren                                        │ │
│  │  → LLM-Nachfrage (Self-Correction)                           │ │
│  │  → Streaming fortsetzen mit Korrektur                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                    ↓                                │
│ FINAL METADATA (response_end):                                     │
│  {                                                                 │
│    "quality_metrics": {                                            │
│      "completeness": 0.95,  # 95% der Kriterien behandelt        │
│      "accuracy": 0.92,      # 92% RAG-Quellen korrekt            │
│      "consistency": 0.88,   # 88% konsistent                     │
│      "token_efficiency": 0.91  # 3200/3500 Tokens genutzt        │
│    },                                                             │
│    "confidence": 0.89,  # Finale Confidence                       │
│    "sources": [...],                                              │
│    "suggestions": [                                                │
│      "Bitte gib dein Bundesland an für präzise Antwort",         │
│      "Möchtest du wissen welche Unterlagen du brauchst?"          │
│    ]                                                              │
│  }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Basic Template Frameworks (Handvoll Basis-Strukturen)

### Framework 1: **Verwaltungsrechtliche Frage** (Default)
```json
{
  "framework_id": "verwaltungsrechtliche_frage",
  "description": "Standard-Framework für verwaltungsrechtliche Fragen",
  "structure": {
    "required_sections": [
      {"id": "legal_basis", "title": "Rechtsgrundlage", "type": "markdown"},
      {"id": "assessment", "title": "Rechtliche Bewertung", "type": "markdown"},
      {"id": "sources", "title": "Quellen", "type": "source_list"}
    ],
    "optional_sections": [
      {"id": "clarification", "title": "Rückfragen", "type": "interactive_form"},
      {"id": "process", "title": "Verfahren", "type": "process_graph"},
      {"id": "comparison", "title": "Vergleichstabelle", "type": "table"},
      {"id": "visualization", "title": "Visualisierung", "type": "canvas"}
    ]
  },
  "default_token_budget": 2500,
  "quality_criteria": {
    "min_rag_sources": 2,
    "min_confidence": 0.7,
    "required_legal_citations": true
  }
}
```

### Framework 2: **Vollständigkeitsprüfung** (Checklist-basiert)
```json
{
  "framework_id": "vollstaendigkeitspruefung",
  "description": "Framework für formale Vollständigkeitsprüfungen",
  "structure": {
    "required_sections": [
      {"id": "checklist", "title": "Prüfkriterien", "type": "checklist"},
      {"id": "missing_items", "title": "Fehlende Elemente", "type": "table"},
      {"id": "recommendations", "title": "Handlungsempfehlungen", "type": "markdown"}
    ]
  },
  "default_token_budget": 3000,
  "quality_criteria": {
    "completeness": 1.0,  # MUSS alle Kriterien prüfen
    "min_confidence": 0.8
  }
}
```

### Framework 3: **Prozess-Navigation** (Graph-basiert)
```json
{
  "framework_id": "prozess_navigation",
  "description": "Framework für Verwaltungsprozess-Anleitungen",
  "structure": {
    "required_sections": [
      {"id": "current_step", "title": "Aktueller Schritt", "type": "markdown"},
      {"id": "process_graph", "title": "Prozessablauf", "type": "neo4j_graph"},
      {"id": "next_steps", "title": "Nächste Schritte", "type": "ordered_list"}
    ]
  },
  "default_token_budget": 2000,
  "quality_criteria": {
    "process_graph_required": true,
    "min_steps_shown": 3
  }
}
```

### Framework 4: **Vergleichsanalyse** (Multi-Option)
```json
{
  "framework_id": "vergleichsanalyse",
  "description": "Framework für Vergleiche (z.B. Bundesländer, Verfahren)",
  "structure": {
    "required_sections": [
      {"id": "comparison_table", "title": "Vergleichstabelle", "type": "table"},
      {"id": "recommendation", "title": "Empfehlung", "type": "markdown"}
    ]
  },
  "default_token_budget": 2500
}
```

### Framework 5: **Detaillierte Rechtsanalyse** (Umfassend)
```json
{
  "framework_id": "detaillierte_rechtsanalyse",
  "description": "Framework für komplexe rechtliche Analysen",
  "structure": {
    "required_sections": [
      {"id": "executive_summary", "title": "Executive Summary", "type": "markdown"},
      {"id": "legal_basis", "title": "Rechtsgrundlagen", "type": "markdown"},
      {"id": "legal_assessment", "title": "Rechtliche Bewertung", "type": "markdown"},
      {"id": "case_law", "title": "Rechtsprechung", "type": "table"},
      {"id": "conclusion", "title": "Fazit", "type": "markdown"}
    ]
  },
  "default_token_budget": 8000,  # SEHR HOCH
  "quality_criteria": {
    "min_rag_sources": 5,
    "min_confidence": 0.85,
    "legal_citations_required": true
  }
}
```

---

## 🧠 LLM Hypothesis Generation - Prompt

```python
HYPOTHESIS_GENERATION_PROMPT = """
Du bist VERITAS Hypothesis Generator.

AUFGABE: Analysiere die User-Frage und den RAG-Kontext (semantisch + Prozess-Graph).
Erstelle eine Hypothese: Welche Informationen brauchst du noch für eine vollständige Antwort?

INPUT:
- User Query: "{user_query}"
- RAG Semantic Results: {rag_semantic_results}
- RAG Process Graph: {rag_process_graph}

OUTPUT (JSON):
{{
  "required_criteria": [
    "Liste von Prüfkriterien, die beantwortet werden müssen",
    "z.B. 'Gebäudeklasse bestimmen', 'Bundesland-Regelung prüfen'"
  ],
  "missing_information": [
    "Informationen, die in der Frage NICHT angegeben wurden",
    "z.B. 'Bundesland nicht genannt', 'Grundstücksgröße fehlt'"
  ],
  "available_information": [
    "Informationen, die aus RAG-Kontext VERFÜGBAR sind",
    "z.B. 'BauGB §35 gefunden', 'Prozess-Graph für Baugenehmigung vorhanden'"
  ],
  "suggested_structure": {{
    "base_framework": "verwaltungsrechtliche_frage",  # Wähle aus: {framework_ids}
    "sections": [
      {{"id": "section_id", "type": "markdown|table|canvas|interactive_form|process_graph", "priority": 1-10}},
      ...
    ]
  }},
  "confidence_estimate": 0.0-1.0,  # Wie sicher bist du, die Frage VOLLSTÄNDIG beantworten zu können?
  "estimated_complexity": "simple|medium|complex|very_complex",
  "recommended_token_budget": 1000-16000,  # Geschätzte Token-Anzahl
  "quality_checks_required": [
    "completeness",  # Alle Kriterien behandelt?
    "accuracy",      # RAG-Quellen korrekt?
    "consistency"    # Keine Widersprüche?
  ]
}}

REGELN:
1. Sei EHRLICH: Wenn Info fehlt → in missing_information listen
2. Nutze RAG-Kontext: available_information basiert NUR auf RAG-Results
3. Wähle Framework weise: Einfache Frage → verwaltungsrechtliche_frage, Checkliste → vollstaendigkeitspruefung
4. Token-Budget: Simple: 1000-2500, Medium: 2500-5000, Complex: 5000-10000, Very Complex: 10000-16000
5. Confidence: Hoch (>0.8) nur wenn ALLE Infos verfügbar, sonst Medium (0.5-0.8) oder Niedrig (<0.5)

Erstelle jetzt die Hypothese für die User-Frage.
"""
```

---

## 🔄 Adaptive Template Generator - Pseudocode

```python
class AdaptiveTemplateGenerator:
    """
    Generiert Templates dynamisch basierend auf:
    1. User Query
    2. RAG Kontext (Semantic + Process Graph)
    3. LLM Hypothesis
    """
    
    BASIC_FRAMEWORKS = {
        'verwaltungsrechtliche_frage': Framework(...),
        'vollstaendigkeitspruefung': Framework(...),
        'prozess_navigation': Framework(...),
        'vergleichsanalyse': Framework(...),
        'detaillierte_rechtsanalyse': Framework(...)
    }
    
    async def generate_from_query(
        self,
        user_query: str,
        rag_context: Dict[str, Any]
    ) -> AdaptiveTemplate:
        """
        Generiert adaptives Template in 3 Schritten
        """
        
        # STEP 1: Hypothesis Generation (LLM Call 1 - SCHNELL ~500 Tokens)
        hypothesis = await self._generate_hypothesis(user_query, rag_context)
        
        # STEP 2: Framework Selection
        base_framework = self.BASIC_FRAMEWORKS[hypothesis['suggested_structure']['base_framework']]
        
        # STEP 3: Template Construction
        adaptive_template = self._construct_template(
            hypothesis=hypothesis,
            base_framework=base_framework,
            rag_context=rag_context
        )
        
        return adaptive_template
    
    async def _generate_hypothesis(
        self,
        user_query: str,
        rag_context: Dict
    ) -> Dict:
        """
        LLM Call 1: Hypothesis Generation
        """
        
        # Format RAG results
        rag_semantic = self._format_semantic_results(rag_context.get('semantic', []))
        rag_graph = self._format_graph_results(rag_context.get('graph', []))
        
        # LLM Prompt
        prompt = HYPOTHESIS_GENERATION_PROMPT.format(
            user_query=user_query,
            rag_semantic_results=rag_semantic,
            rag_process_graph=rag_graph,
            framework_ids=list(self.BASIC_FRAMEWORKS.keys())
        )
        
        # Call Ollama (FAST, nur ~500 Tokens)
        response = await ollama_client.generate_response(
            OllamaRequest(
                model="llama3.2:latest",
                prompt=prompt,
                system="Du bist VERITAS Hypothesis Generator. Output NUR JSON.",
                temperature=0.3,
                max_tokens=1000  # Hypothesis ist kurz
            ),
            stream=False  # Kein Streaming für Hypothesis
        )
        
        # Parse JSON
        hypothesis = json.loads(response.response)
        
        logger.info(f"📊 Hypothesis: Confidence={hypothesis['confidence_estimate']}, "
                    f"Complexity={hypothesis['estimated_complexity']}, "
                    f"Tokens={hypothesis['recommended_token_budget']}")
        
        return hypothesis
    
    def _construct_template(
        self,
        hypothesis: Dict,
        base_framework: Framework,
        rag_context: Dict
    ) -> AdaptiveTemplate:
        """
        Konstruiert adaptives Template aus Hypothesis + Framework
        """
        
        # Start mit Base Framework
        sections = base_framework.structure['required_sections'].copy()
        
        # Füge Hypothesis-basierte Sections hinzu
        for suggested_section in hypothesis['suggested_structure']['sections']:
            section_id = suggested_section['id']
            section_type = suggested_section['type']
            
            # Konstruiere Section-Spec
            if section_type == 'interactive_form':
                # Auto-generiere Form basierend auf missing_information
                section_spec = self._create_interactive_form(
                    hypothesis['missing_information']
                )
            elif section_type == 'process_graph':
                # Neo4j Query aus RAG Graph
                section_spec = self._create_process_graph(
                    rag_context['graph']
                )
            elif section_type == 'table':
                # Table aus required_criteria
                section_spec = self._create_comparison_table(
                    hypothesis['required_criteria'],
                    rag_context['semantic']
                )
            elif section_type == 'canvas':
                # Canvas-Visualisierung (z.B. Abstandsflächen)
                section_spec = self._create_visualization(
                    hypothesis['required_criteria']
                )
            else:  # markdown
                section_spec = {
                    'type': 'markdown',
                    'id': section_id
                }
            
            sections.append(section_spec)
        
        # Sortiere nach Priority
        sections.sort(key=lambda s: suggested_section.get('priority', 999))
        
        # Konstruiere System Prompt
        system_prompt = self._generate_system_prompt(
            hypothesis=hypothesis,
            sections=sections,
            base_framework=base_framework
        )
        
        # Return Adaptive Template
        return AdaptiveTemplate(
            template_id=f"adaptive_{hash(user_query)}_{datetime.now().isoformat()}",
            base_framework=base_framework.framework_id,
            system_prompt=system_prompt,
            required_tokens=hypothesis['recommended_token_budget'],
            response_structure=sections,
            quality_checks=hypothesis['quality_checks_required'],
            confidence_estimate=hypothesis['confidence_estimate']
        )
    
    def _create_interactive_form(self, missing_info: List[str]) -> Dict:
        """
        Auto-generiert Interactive Form aus fehlenden Informationen
        
        Beispiel:
        missing_info = ["Bundesland nicht angegeben", "Carport-Größe fehlt"]
        
        →
        {
          "type": "interactive_form",
          "fields": [
            {"name": "bundesland", "type": "dropdown", "options": [...]},
            {"name": "carport_groesse", "type": "text", "placeholder": "z.B. 20m²"}
          ]
        }
        """
        
        fields = []
        
        for info in missing_info:
            # Einfaches Keyword-Matching (später NLP)
            if 'bundesland' in info.lower():
                fields.append({
                    'name': 'bundesland',
                    'type': 'dropdown',
                    'label': 'Bundesland',
                    'options': ['Baden-Württemberg', 'Bayern', 'Berlin', ...]
                })
            elif 'größe' in info.lower() or 'fläche' in info.lower():
                fields.append({
                    'name': 'groesse',
                    'type': 'text',
                    'label': 'Größe/Fläche',
                    'placeholder': 'z.B. 20m²'
                })
            elif 'höhe' in info.lower():
                fields.append({
                    'name': 'hoehe',
                    'type': 'text',
                    'label': 'Höhe',
                    'placeholder': 'z.B. 2.5m'
                })
            # ... weitere Muster
        
        return {
            'type': 'interactive_form',
            'title': 'Fehlende Informationen',
            'description': 'Bitte ergänze folgende Angaben für eine präzise Antwort:',
            'fields': fields
        }
    
    def _generate_system_prompt(
        self,
        hypothesis: Dict,
        sections: List[Dict],
        base_framework: Framework
    ) -> str:
        """
        Generiert System Prompt aus Hypothesis + Sections
        """
        
        prompt = f"""
Du bist VERITAS, ein Experte für deutsches Verwaltungsrecht.

AUFGABE: Beantworte die User-Frage basierend auf dem RAG-Kontext.

WICHTIG - HYPOTHESE-BASIERTE STRUKTUR:
- Required Criteria: {', '.join(hypothesis['required_criteria'])}
- Fehlende Informationen: {', '.join(hypothesis['missing_information'])}
- Verfügbare Informationen: {', '.join(hypothesis['available_information'])}

ANTWORT-STRUKTUR (ZWINGEND):
"""
        
        for i, section in enumerate(sections, 1):
            prompt += f"\n{i}. {section.get('title', section['id'])} ({section['type']})"
            
            if section['type'] == 'interactive_form':
                prompt += "\n   → Erstelle interaktives Formular für fehlende Infos"
            elif section['type'] == 'process_graph':
                prompt += "\n   → Zeige Prozess-Graph aus Neo4j RAG"
            elif section['type'] == 'table':
                prompt += "\n   → Erstelle Vergleichstabelle"
        
        prompt += f"""

QUALITÄTS-CHECKS (während Generation):
{', '.join(hypothesis['quality_checks_required'])}

TOKEN-BUDGET: {hypothesis['recommended_token_budget']} Tokens

OUTPUT-FORMAT (NDJSON Streaming):
{{"type":"response_start","metadata":{{"template":"adaptive_..."}}}}
{{"type":"section_start","section_id":"..."}}
{{"type":"text_chunk","content":"..."}}
{{"type":"widget","widget":{{...}}}}
{{"type":"section_end","section_id":"..."}}
{{"type":"response_end","metadata":{{"quality_metrics":{{...}}}}}}

Beantworte jetzt die User-Frage.
"""
        
        return prompt
```

---

## 🎯 Quality Checks während Streaming

```python
class ResponseQualityMonitor:
    """
    Überwacht LLM-Response während Streaming
    Prüft: Vollständigkeit, Accuracy, Konsistenz
    """
    
    def __init__(self, hypothesis: Dict, rag_context: Dict):
        self.hypothesis = hypothesis
        self.rag_context = rag_context
        self.sections_completed = set()
        self.criteria_addressed = set()
        self.sources_cited = set()
    
    async def check_chunk(self, chunk: Dict) -> QualityCheckResult:
        """
        Prüft einzelnen NDJSON-Chunk während Streaming
        """
        
        chunk_type = chunk.get('type')
        
        if chunk_type == 'section_end':
            section_id = chunk.get('section_id')
            self.sections_completed.add(section_id)
            
        elif chunk_type == 'text_chunk':
            # Prüfe ob required_criteria erwähnt werden
            content = chunk.get('content', '')
            for criterion in self.hypothesis['required_criteria']:
                if self._criterion_mentioned(criterion, content):
                    self.criteria_addressed.add(criterion)
            
            # Prüfe RAG-Source-Citations
            sources = self._extract_sources(content)
            for source in sources:
                if self._source_valid(source, self.rag_context):
                    self.sources_cited.add(source)
                else:
                    # WARNUNG: Ungültige Quelle zitiert (Hallucination!)
                    return QualityCheckResult(
                        passed=False,
                        issue="invalid_source_citation",
                        details=f"Quelle '{source}' nicht in RAG-Kontext gefunden",
                        action="request_correction"
                    )
        
        # Vollständigkeits-Check (am Ende)
        if chunk_type == 'response_end':
            completeness = len(self.criteria_addressed) / len(self.hypothesis['required_criteria'])
            
            if completeness < 0.8:  # Weniger als 80% der Kriterien behandelt
                return QualityCheckResult(
                    passed=False,
                    issue="incomplete_response",
                    details=f"Nur {completeness*100:.0f}% der Kriterien behandelt",
                    missing_criteria=set(self.hypothesis['required_criteria']) - self.criteria_addressed,
                    action="request_completion"
                )
        
        # Alles OK
        return QualityCheckResult(passed=True)
    
    def get_final_quality_metrics(self) -> Dict:
        """
        Berechnet finale Qualitäts-Metriken
        """
        
        return {
            'completeness': len(self.criteria_addressed) / len(self.hypothesis['required_criteria']),
            'accuracy': len(self.sources_cited) / max(1, len(self._extract_all_citations())),
            'consistency': self._check_consistency(),  # TODO: Widerspruchs-Detektion
            'sections_completed': len(self.sections_completed),
            'criteria_addressed': list(self.criteria_addressed),
            'sources_cited': list(self.sources_cited)
        }
```

---

## 📊 Beispiel: Adaptive Response Generation

### User Query:
```
"Ist für meinen Carport eine Baugenehmigung nötig?"
```

### Phase 1: RAG + Hypothesis

**RAG Results (Semantic):**
```json
{
  "semantic": [
    {"text": "BauGB §35 Abs. 2: Außenbereich - Baugenehmigungspflicht", "score": 0.92},
    {"text": "LBO BW §50: Verfahrensfreie Vorhaben - Garagen bis 30m²", "score": 0.88}
  ],
  "graph": [
    {"process": "Baugenehmigung", "steps": ["Antrag", "Prüfung", "Bescheid"]}
  ]
}
```

**LLM Hypothesis:**
```json
{
  "required_criteria": [
    "Bundesland bestimmen (LBO variiert!)",
    "Carport-Größe/Höhe prüfen (Verfahrensfreiheit?)",
    "Grundstückslage prüfen (Außenbereich vs. Bebauungsplan)",
    "Carport als 'Garage' oder 'Gebäude' klassifizieren"
  ],
  "missing_information": [
    "Bundesland nicht angegeben",
    "Carport-Größe nicht angegeben",
    "Carport-Höhe nicht angegeben",
    "Grundstückslage unklar"
  ],
  "available_information": [
    "BauGB §35 Abs. 2 gefunden (Außenbereich)",
    "LBO BW §50 gefunden (Verfahrensfreiheit bis 30m²)",
    "Prozess-Graph für Baugenehmigung vorhanden"
  ],
  "suggested_structure": {
    "base_framework": "verwaltungsrechtliche_frage",
    "sections": [
      {"id": "missing_info_form", "type": "interactive_form", "priority": 1},
      {"id": "legal_assessment", "type": "markdown", "priority": 2},
      {"id": "bundesland_comparison", "type": "table", "priority": 3},
      {"id": "process_steps", "type": "process_graph", "priority": 4}
    ]
  },
  "confidence_estimate": 0.55,  # NIEDRIG (viele Infos fehlen)
  "estimated_complexity": "medium",
  "recommended_token_budget": 3500
}
```

### Phase 2: Template Construction

**Generated Adaptive Template:**
```json
{
  "template_id": "adaptive_carport_genehmigung_2025-10-12-18-30-45",
  "base_framework": "verwaltungsrechtliche_frage",
  "system_prompt": "[AUTO-GENERIERT, siehe oben]",
  "required_tokens": 3500,
  "response_structure": {
    "sections": [
      {
        "id": "missing_info_form",
        "title": "Fehlende Informationen",
        "type": "interactive_form",
        "widget": {
          "type": "interactive_form",
          "fields": [
            {"name": "bundesland", "type": "dropdown", "options": ["Baden-Württemberg", ...]},
            {"name": "carport_groesse", "type": "text", "placeholder": "z.B. 20m²"},
            {"name": "carport_hoehe", "type": "text", "placeholder": "z.B. 2.5m"},
            {"name": "grundstueckslage", "type": "dropdown", "options": ["Bebauungsplan", "Außenbereich"]}
          ]
        }
      },
      {
        "id": "legal_assessment",
        "title": "Rechtliche Einordnung (vorläufig)",
        "type": "markdown"
      },
      {
        "id": "bundesland_comparison",
        "title": "Verfahrensfreiheit nach Bundesland",
        "type": "table",
        "widget": {
          "type": "table",
          "headers": ["Bundesland", "Max. Größe", "Max. Höhe", "Genehmigungsfrei?"],
          "rows": [
            ["Baden-Württemberg", "30m²", "3m", "Ja (LBO §50)"],
            ["Bayern", "30m²", "3m", "Ja (BayBO Art. 57)"],
            ["..."]
          ]
        }
      },
      {
        "id": "process_steps",
        "title": "Falls genehmigungspflichtig: Verfahrensschritte",
        "type": "process_graph"
      }
    ]
  }
}
```

### Phase 3: Response Generation (NDJSON Streaming)

```ndjson
{"type":"response_start","metadata":{"template":"adaptive_carport_genehmigung_2025-10-12-18-30-45","confidence_estimate":0.55}}
{"type":"section_start","section_id":"missing_info_form"}
{"type":"text_chunk","content":"Für eine präzise Antwort benötige ich noch folgende Informationen:"}
{"type":"widget","widget":{"type":"interactive_form","fields":[{"name":"bundesland","type":"dropdown",...}]}}
{"type":"section_end","section_id":"missing_info_form"}
{"type":"section_start","section_id":"legal_assessment"}
{"type":"text_chunk","content":"## Rechtliche Einordnung (vorläufig)\n\nGemäß **BauGB §35 Abs. 2** sind im **Außenbereich** grundsätzlich Bauvorhaben genehmigungspflichtig..."}
{"type":"text_chunk","content":"ABER: Viele Bundesländer haben **Verfahrensfreiheit** für kleinere Garagen/Carports (siehe Tabelle)..."}
{"type":"section_end","section_id":"legal_assessment"}
{"type":"section_start","section_id":"bundesland_comparison"}
{"type":"widget","widget":{"type":"table","headers":["Bundesland","Max. Größe",...],"rows":[...]}}
{"type":"section_end","section_id":"bundesland_comparison"}
{"type":"section_start","section_id":"process_steps"}
{"type":"text_chunk","content":"Falls Ihr Carport **nicht** unter Verfahrensfreiheit fällt:"}
{"type":"widget","widget":{"type":"process_graph","nodes":[...],"edges":[...]}}
{"type":"section_end","section_id":"process_steps"}
{"type":"response_end","metadata":{"quality_metrics":{"completeness":0.95,"accuracy":0.92,"consistency":0.88},"confidence":0.78,"sources":[...],"suggestions":["Bitte gib dein Bundesland an","Möchtest du wissen welche Unterlagen du brauchst?"]}}
```

---

## ✅ Vorteile des Adaptive-Template-Ansatzes

| Aspekt | Fix Templates (v4.1) | Adaptive Templates (v5.0) |
|--------|---------------------|---------------------------|
| **Flexibilität** | ❌ 5 feste Templates | ✅ Unbegrenzt (LLM-generiert) |
| **Unerwartete Fragen** | ❌ Fallback auf Default | ✅ Passt sich an |
| **Fehlende Informationen** | ❌ Keine Rückfrage | ✅ Auto-generiertes Formular |
| **Komplexität** | ❌ Manuell kategorisieren | ✅ LLM schätzt automatisch |
| **Token-Effizienz** | ⚠️ Feste Limits | ✅ Dynamisch basierend auf Bedarf |
| **Quality Checks** | ❌ Keine | ✅ Während Streaming |
| **RAG-Integration** | ⚠️ Nachträglich | ✅ Von Anfang an (Hypothesis) |
| **Wartung** | ❌ 5 Templates pflegen | ✅ Nur 5 Basic Frameworks |

---

## 🚀 Implementation Roadmap (AKTUALISIERT für v5.0)

### Phase 1: Hypothesis Generation (2-3 Tage)
- [ ] `HYPOTHESIS_GENERATION_PROMPT` erstellen
- [ ] `AdaptiveTemplateGenerator._generate_hypothesis()` implementieren
- [ ] 5 Basic Frameworks definieren (JSON-Specs)
- [ ] Ollama-Integration für Hypothesis (fast, ~500 tokens)
- [ ] Test mit Mock-RAG-Results

### Phase 2: Template Construction (2-3 Tage)
- [ ] `AdaptiveTemplateGenerator._construct_template()` implementieren
- [ ] Auto-Form-Generator (`_create_interactive_form()`)
- [ ] Auto-Table-Generator (`_create_comparison_table()`)
- [ ] Auto-Graph-Integration (`_create_process_graph()`)
- [ ] System-Prompt-Generator (`_generate_system_prompt()`)

### Phase 3: Quality Monitoring (2-3 Tage)
- [ ] `ResponseQualityMonitor` implementieren
- [ ] Completeness-Check (Kriterien-Abdeckung)
- [ ] Accuracy-Check (RAG-Source-Validation)
- [ ] Consistency-Check (Widerspruchs-Detektion)
- [ ] Self-Correction-Mechanismus (bei Quality-Fails)

### Phase 4: Frontend Integration (2-3 Tage)
- [ ] Interactive Form Widget (`_render_interactive_form()`)
- [ ] Process Graph Widget (`_render_neo4j_graph()`)
- [ ] Quality Metrics Display (Completeness, Accuracy, Consistency)
- [ ] Template Badge (zeigt Framework + Confidence)

### Phase 5: End-to-End Testing (2-3 Tage)
- [ ] Test mit realen verwaltungsrechtlichen Fragen
- [ ] Hypothesis Quality (sind Kriterien korrekt?)
- [ ] Template Quality (ist Struktur sinnvoll?)
- [ ] Response Quality (Completeness, Accuracy, Consistency)
- [ ] Performance (Hypothesis-Zeit + Response-Zeit)

### Phase 6: Optimization (1-2 Tage)
- [ ] Hypothesis-Caching (gleiche Frage → gleiche Hypothesis)
- [ ] Framework-Selection-Tuning (bessere Auto-Selection)
- [ ] Quality-Threshold-Tuning (wann Self-Correction?)
- [ ] Documentation

**Total:** 11-17 Tage (gleich wie v4.1, aber VIEL flexibler!)

---

## 🎯 Success Metrics (v5.0)

```
┌────────────────────────────────────────────────────────────────┐
│ METRIC 1: Hypothesis Quality                                   │
│  - Required Criteria Accuracy: > 90% (vom User bestätigt)     │
│  - Missing Information Detection: > 95%                        │
│  - Framework Selection Accuracy: > 85%                         │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ METRIC 2: Response Quality (Auto-Checked)                      │
│  - Completeness: > 0.90 (90% der Kriterien behandelt)         │
│  - Accuracy: > 0.92 (92% der Quellen korrekt)                 │
│  - Consistency: > 0.88 (88% konsistent)                       │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ METRIC 3: Performance                                          │
│  - Hypothesis Generation: < 500ms                             │
│  - Template Construction: < 200ms                             │
│  - Response Streaming: Same as v4.1 (1-3s)                    │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ METRIC 4: User Satisfaction                                    │
│  - Fragen ohne fehlende Info: Confidence > 0.8 (80%)          │
│  - Fragen mit fehlender Info: Interactive Form erscheint 95%  │
│  - Quality Metrics transparent (User versteht Confidence)     │
└────────────────────────────────────────────────────────────────┘
```

---

**END OF ADAPTIVE RESPONSE FRAMEWORK CONCEPT (v5.0)**

**Hauptunterschied zu v4.1:**
- v4.1: 5 **feste** Templates (manuell definiert)
- v5.0: **LLM-generierte** Templates (adaptiv, unbegrenzt)
- v5.0: **Hypothesis-basiert** (LLM entscheidet selbst was es braucht)
- v5.0: **Quality Checks** während Streaming (Self-Correction)
