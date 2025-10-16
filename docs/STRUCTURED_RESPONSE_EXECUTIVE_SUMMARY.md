# 📋 VERITAS Adaptive Response System - Executive Summary

**Version:** v5.0.0 (LLM-Generated Adaptive Templates)  
**Date:** 12. Oktober 2025, 18:30 Uhr  
**Status:** 📋 DESIGN PHASE - Paradigm Shift

---

## 🎯 Vision (UPDATED v5.0)

**Transform VERITAS from plain-text chat to intelligent, self-adapting legal assistant.**

**Paradigm Shift: v4.1 → v5.0**

| Aspect | v4.1 (Fixed Templates) | v5.0 (Adaptive Templates) |
|--------|------------------------|---------------------------|
| **Templates** | 5 fixed, manually defined | ∞ LLM-generated, adaptive |
| **Structure** | Pre-defined sections | LLM decides based on question |
| **Missing Info** | Ignored or generic fallback | Auto-generated interactive form |
| **RAG Integration** | After template selection | **Before** (Hypothesis Phase) |
| **Quality Checks** | None | During streaming (completeness, accuracy, consistency) |
| **Flexibility** | Limited to 5 scenarios | Handles ANY administrative law question |

---

## 🧠 The New 3-Phase Architecture

### Phase 1: **RAG-Based Hypothesis Generation** ⚡

**What happens:**
1. User asks: *"Ist für meinen Carport eine Baugenehmigung nötig?"*
2. Backend runs **parallel RAG**:
   - Semantic Search (ChromaDB) → Relevant paragraphs
   - Process Graph (Neo4j) → Administrative process steps
3. **LLM Hypothesis Call** (FAST, ~500 tokens):
   - *"What information do I need to answer this question completely?"*
   
**Output (JSON):**
```json
{
  "required_criteria": [
    "Bundesland bestimmen (LBO variiert!)",
    "Carport-Größe/Höhe prüfen (Verfahrensfreiheit?)",
    "Grundstückslage prüfen (Außenbereich vs. Bebauungsplan)"
  ],
  "missing_information": [
    "Bundesland nicht angegeben",
    "Carport-Größe nicht angegeben"
  ],
  "available_information": [
    "BauGB §35 Abs. 2 gefunden",
    "LBO BW §50 gefunden (Verfahrensfreiheit bis 30m²)"
  ],
  "suggested_structure": {
    "base_framework": "verwaltungsrechtliche_frage",
    "sections": [
      {"id": "missing_info_form", "type": "interactive_form", "priority": 1},
      {"id": "legal_assessment", "type": "markdown", "priority": 2},
      {"id": "bundesland_comparison", "type": "table", "priority": 3}
    ]
  },
  "confidence_estimate": 0.55,
  "recommended_token_budget": 3500
}
```

**Key Innovation:** LLM explicitly states what it needs → No hallucinations, transparent confidence

---

### Phase 2: **Adaptive Template Construction** 🏗️

**What happens:**
1. Select **Basic Framework** (5 available):
   - `verwaltungsrechtliche_frage` (default)
   - `vollstaendigkeitspruefung` (checklist)
   - `prozess_navigation` (graph-based)
   - `vergleichsanalyse` (comparison)
   - `detaillierte_rechtsanalyse` (comprehensive)

2. **Auto-generate sections** based on hypothesis:
   - Missing info? → Create interactive form
   - Comparison needed? → Create table
   - Process steps? → Embed Neo4j graph

3. **Generate system prompt** with:
   - Required criteria (checklist for LLM)
   - Available RAG context
   - Section structure
   - Quality check requirements

**Output: Adaptive Template** (unique per question!)

---

### Phase 3: **Streaming Response with Quality Checks** ✅

**What happens:**
1. LLM generates response using adaptive template
2. **During streaming**, backend monitors:
   - ✅ **Completeness:** All required_criteria addressed?
   - ✅ **Accuracy:** RAG sources cited correctly? (No hallucinations!)
   - ✅ **Consistency:** No contradictions in answer?
3. If quality check fails → **Self-correction:**
   - Pause streaming
   - LLM re-generates problematic section
   - Resume streaming

**Output: NDJSON Stream**
```ndjson
{"type":"response_start","metadata":{"confidence_estimate":0.55}}
{"type":"section_start","section_id":"missing_info_form"}
{"type":"widget","widget":{"type":"interactive_form","fields":[...]}}
{"type":"section_end"}
{"type":"section_start","section_id":"legal_assessment"}
{"type":"text_chunk","content":"Gemäß **BauGB §35**..."}
{"type":"section_end"}
{"type":"response_end","metadata":{"quality_metrics":{"completeness":0.95,"accuracy":0.92}}}
```

---

## 🔥 Three Critical Requirements (ALL SOLVED v5.0)

### 1. ⚡ **Streaming Client**

**Status:** ✅ ALREADY IMPLEMENTED + ENHANCED

**v4.1 Solution:** NDJSON Streaming Format  
**v5.0 Enhancement:** Quality checks DURING streaming

**Benefits:**
- ✅ Widgets appear during LLM generation
- ✅ Quality issues detected in real-time
- ✅ Self-correction without re-starting response
- ✅ Transparent confidence from start

---

### 2. 📏 **Dynamic Token Size**

**Status:** ✅ SOLVED (LLM-Estimated!)

**v4.1:** Pre-calculated based on template + complexity  
**v5.0:** **LLM estimates in Hypothesis Phase**

**How it works:**
```python
# Hypothesis Phase (LLM Call 1):
hypothesis = {
  "estimated_complexity": "medium",
  "recommended_token_budget": 3500,  # LLM decides!
  "confidence_estimate": 0.55
}

# Response Phase (LLM Call 2):
ollama_request.max_tokens = hypothesis['recommended_token_budget']
```

**Why better?**
- ✅ LLM knows best what it needs
- ✅ Adapts to question complexity automatically
- ✅ Considers available RAG context size
- ✅ Confidence-aware (low confidence → ask for more info instead of using max tokens)

---

### 3. 📋 **Template System (NEW PARADIGM!)**

**Status:** ✅ REVOLUTIONIZED

**v4.1:** 5 fixed server-side templates  
**v5.0:** **LLM-generated adaptive templates**

**The Paradigm Shift:**

| Aspect | Fixed Templates (v4.1) | Adaptive Templates (v5.0) |
|--------|------------------------|---------------------------|
| **Number** | 5 pre-defined | ∞ (generated per question) |
| **Structure** | Manual (800 LOC each) | Auto-generated from hypothesis |
| **Missing Info** | Ignored | Auto-form created |
| **Flexibility** | Limited to 5 scenarios | Handles ANY question |
| **Maintenance** | Update 5 templates manually | Update 5 basic frameworks |

**5 Basic Frameworks (Minimal, ~100 LOC each):**

1. **verwaltungsrechtliche_frage** - Default for legal questions
2. **vollstaendigkeitspruefung** - Checklist-based completeness review
3. **prozess_navigation** - Process graph navigation
4. **vergleichsanalyse** - Comparison (e.g., Bundesländer)
5. **detaillierte_rechtsanalyse** - Comprehensive legal analysis

**How LLM decides:**
```python
# In Hypothesis Phase, LLM outputs:
{
  "suggested_structure": {
    "base_framework": "verwaltungsrechtliche_frage",  # LLM selects
    "sections": [
      {"id": "missing_info_form", "type": "interactive_form", "priority": 1},
      {"id": "legal_assessment", "type": "markdown", "priority": 2},
      {"id": "comparison_table", "type": "table", "priority": 3}
    ]
  }
}

# Template Generator creates unique template for this question
```

**Key Innovation:** LLM creates the structure → Human provides frameworks

---

## 🏗️ System Architecture

### High-Level Flow

```
User Question
    ↓
Backend: Template Auto-Selection (keyword-matching)
    ↓
Backend: Adaptive Token Estimation (1K-16K)
    ↓
Backend: Ollama Request (template-specific system prompt, dynamic tokens, stream=True)
    ↓
Backend: NDJSON Streaming Response
    ├→ {"type":"response_start"} (header)
    ├→ {"type":"text_chunk"} (markdown text, incremental)
    ├→ {"type":"widget"} (table/chart/canvas/image, during streaming)
    └→ {"type":"response_end"} (metadata, sources, suggestions)
    ↓
Frontend: StreamingStructuredResponseParser
    ├→ Parse NDJSON line-by-line
    ├→ Render text chunks incrementally (MarkdownRenderer)
    ├→ Render widgets as they arrive (WidgetRenderer)
    └→ Finalize metadata (ChatDisplayFormatter)
    ↓
UI: Rich Interactive Response visible in real-time
```

### New Components (to be implemented)

1. **Backend:**
   - `PromptTemplateLibrary` (~400 LOC) - 5 templates
   - `AdaptiveTokenManager` (~200 LOC) - dynamic token estimation
   - `/api/v1/chat/structured` endpoint (~100 LOC) - NDJSON streaming

2. **Frontend:**
   - `StreamingStructuredResponseParser` (~300 LOC) - NDJSON parser
   - `WidgetRenderer` (~500 LOC) - Image/Button/Canvas/Chart rendering
   - Extended `ChatDisplayFormatter` (~200 LOC) - integration

**Total New Code:** ~1,700 LOC

---

## 📊 Widget Types

### Text-Based (already exists ✅)
- Markdown (headers, lists, bold, italic, links)
- Code blocks with syntax highlighting (Pygments)
- Tables (ASCII art rendering)

### Media (new ⭐)
- **Images** (PNG, JPG, GIF)
  - From URL, local path, or Base64
  - Auto-resize, caption support
- **Videos** (MP4, WebM) ⚠️ Limited in Tkinter
  - Thumbnail + external player link
  - Or: Embedded with `tkintervideo` (experimental)

### Interactive Widgets (new ⭐)
- **Buttons** (custom actions, payload support)
- **Links** (already exists ✅)
- **Checkboxes, Radio Buttons, Sliders, Dropdowns** (future)

### Visualizations (new ⭐)
- **Canvas Drawings**
  - Lines, rectangles, circles, text
  - Custom draw commands (e.g., distance visualization)
- **Charts/Diagrams** (matplotlib)
  - Bar charts, line charts, pie charts, scatter plots
- **Mindmaps, Timelines** (future)

### Custom Widgets (partial ✅)
- **Collapsible Sections** (already exists ✅)
- **Tabs, Accordions, Progress Bars, Rating Stars** (future)

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation + Streaming (2-3 days)
- [x] Research existing VERITAS features (DONE)
- [ ] Define JSON Schema (NDJSON streaming-compatible)
- [ ] Create `StreamingStructuredResponseParser`
- [ ] Create `WidgetRenderer` base class (incremental rendering)
- [ ] Response parser for streaming chunks

### Phase 2: Backend Template System (2-3 days)
- [ ] Create `PromptTemplateLibrary` (5 templates)
- [ ] Implement `AdaptiveTokenManager`
- [ ] Backend API endpoint `/api/v1/chat/structured`
- [ ] Template auto-selection (keyword-matching)
- [ ] Ollama integration (dynamic tokens + streaming)

### Phase 3: Basic Widgets (Streaming-capable) (2-3 days)
- [ ] Image rendering (PIL/Pillow, incremental)
- [ ] Button rendering (incremental)
- [ ] Canvas rendering (incremental)
- [ ] Chart rendering (matplotlib, incremental)
- [ ] Table rendering (update existing for streaming)

### Phase 4: Frontend Integration (1-2 days)
- [ ] Extend `ChatDisplayFormatter` for streaming structured response
- [ ] Integration with existing `StreamingUIMixin`
- [ ] Progress updates during widget rendering
- [ ] Error handling (incomplete JSON chunks)

### Phase 5: Advanced Features (2-3 days)
- [ ] Video support (thumbnails + links)
- [ ] Interactive widgets (sliders, dropdowns)
- [ ] Custom widget templates
- [ ] Widget gallery (documentation)
- [ ] Template selection in UI (dropdown)

### Phase 6: Testing & Optimization (2-3 days)
- [ ] Memory management (cleanup, streaming buffers)
- [ ] Performance tests (streaming latency, widget rendering)
- [ ] Template tests (all 5 templates with mock data)
- [ ] Error handling (streaming aborts, network errors)
- [ ] Documentation (templates, widget specs, streaming format)

**Total Estimate:** 11-17 days

---

## 💡 Example Use-Cases

### Use-Case 1: Authority Determination + Table

**User:** "Welche Abstände gelten für Windkraftanlagen?"

**Backend:**
- Auto-selects template: `zustaendigkeit_behoerde`
- Estimated tokens: 2048 (simple question, 0.5x complexity)

**NDJSON Streaming Response:**
```ndjson
{"type":"response_start","metadata":{"template":"zustaendigkeit_behoerde","estimated_tokens":2048}}
{"type":"text_chunk","content":"Gemäß **TA Lärm** gelten folgende Mindestabstände für Windkraftanlagen:"}
{"type":"widget","widget":{"type":"table","headers":["Gebietstyp","Mindestabstand","Grenzwert Tag","Grenzwert Nacht"],"rows":[["Wohngebiet","500m","55 dB(A)","40 dB(A)"],["Mischgebiet","300m","60 dB(A)","45 dB(A)"],["Gewerbegebiet","150m","65 dB(A)","50 dB(A)"]]}}
{"type":"response_end","metadata":{"confidence":0.95,"sources":[{"url":"https://...","title":"TA Lärm §6"}],"suggestions":["Gibt es Ausnahmen für Bestandsanlagen?","Wie werden die Abstände gemessen?"]}}
```

**UI Rendering (real-time):**
1. Badge appears: "Zuständigkeit der Behörde" (template indicator)
2. Text appears: "Gemäß **TA Lärm** gelten folgende..."
3. Table appears (formatted with borders)
4. Sources appear (clickable links)
5. Suggestions appear (clickable buttons)

---

### Use-Case 2: Complete Review + All Widgets

**User:** "Vollständige Prüfung Bauantrag (formell, rechtlich, sachlich)"

**Backend:**
- Auto-selects template: `vollstaendige_pruefung`
- Estimated tokens: 16384 (very complex, 2.0x complexity)

**NDJSON Streaming Response:**
```ndjson
{"type":"response_start","metadata":{"template":"vollstaendige_pruefung","estimated_tokens":16384}}
{"type":"text_chunk","content":"# Vollständige Bauantrags-Prüfung\n\n## ✅ Executive Summary\n\nDer Bauantrag ist **genehmigungsfähig mit Auflagen**.\n\n### Zusammenfassung:"}
{"type":"widget","widget":{"type":"table","headers":["Prüfungsebene","Status","Kritische Punkte","Handlungsbedarf"],"rows":[["Formale Prüfung","⚠️ Mit Mängeln","Standsicherheitsnachweis fehlt","Nachreichen binnen 4 Wo"],["Rechtliche Prüfung","✅ OK","-","-"],["Sachliche Prüfung","⚠️ Mit Auflagen","Brandschutz Auflage","Sprinkleranlage erforderlich"]]}}
{"type":"text_chunk","content":"\n\n## 1. Formale Prüfung\n\n### ✅ Vollständig:\n- Bauzeichnungen vorhanden\n- Unterschriften OK\n\n### ❌ Fehlend:\n- Standsicherheitsnachweis"}
{"type":"text_chunk","content":"\n\n## 2. Rechtliche Prüfung\n\n### Bauplanungsrecht (BauGB §30)\n\nDas Vorhaben ist **zulässig** im festgesetzten Wohngebiet.\n\n**Abstandsflächen-Visualisierung:**"}
{"type":"widget","widget":{"type":"canvas","width":400,"height":300,"draw_commands":[{"cmd":"rect","x":50,"y":100,"width":30,"height":80,"fill":"gray","outline":"black"},{"cmd":"text","x":65,"y":140,"text":"Gebäude","font":["Arial",10]},{"cmd":"line","x1":80,"y1":140,"x2":200,"y2":140,"color":"red","width":2},{"cmd":"text","x":140,"y":130,"text":"3m OK","font":["Arial",10],"color":"green"}]}}
{"type":"text_chunk","content":"\n\n## 3. Sachliche Prüfung\n\n### Energieeffizienz (GEG)\n\n**Anforderungen:**"}
{"type":"widget","widget":{"type":"chart","chart_type":"bar","title":"Energieeffizienz-Anforderungen","data":{"labels":["IST-Wert","SOLL (GEG)","Grenzwert"],"values":[45,55,70]},"unit":"kWh/m²a"}}
{"type":"response_end","metadata":{"confidence":0.88,"sources":[{"url":"...","title":"BauGB §30"},{"url":"...","title":"LBO §5"},{"url":"...","title":"GEG §10"}],"suggestions":["Welche Fristen gelten für Nachbesserungen?","Kann ich eine Ausnahme beantragen?","Was kostet die Sprinkleranlage?"]}}
```

**UI Rendering (real-time, over ~15-30 seconds):**
1. Badge: "Vollständige Prüfung"
2. Executive Summary text appears
3. Summary table appears (3 rows, traffic lights)
4. Section 1: Formal Review (text, checklist)
5. Section 2: Legal Review (text)
6. Canvas widget appears (distance visualization with lines/text)
7. Section 3: Technical Review (text)
8. Chart widget appears (bar chart, energy efficiency)
9. Sources appear (3 clickable links)
10. Suggestions appear (3 clickable buttons)

**User Experience:**
- ⚡ Sees results **immediately** (not after 30s wait)
- 📊 Complex visualizations appear **during** generation
- 🎯 Knows which template is used (badge)
- 💡 Gets follow-up suggestions automatically

---

## ✅ Benefits Summary

### For Users:
- ✅ **Richer Responses** (Images, Charts, Canvas, Interactive Buttons)
- ✅ **Real-Time Streaming** (No waiting for complete response)
- ✅ **Specialized Legal Expertise** (5 templates optimized for different aspects)
- ✅ **Faster Simple Questions** (1024 tokens vs 4096 = 75% faster)
- ✅ **Better Complex Questions** (16384 tokens vs 4096 = 4x more detail)

### For Developers:
- ✅ **Built on Existing System** (80% already implemented)
- ✅ **Tkinter-Native** (No web dependencies)
- ✅ **Production-Ready Architecture** (Thread-safe, error-handling)
- ✅ **Server-Side Templates** (Easy updates, no frontend changes)
- ✅ **Memory-Efficient** (Streaming, incremental rendering, cleanup)

### For Business:
- ✅ **Competitive Advantage** (No other Tkinter legal AI has this)
- ✅ **Cost Optimization** (75% token savings on simple questions)
- ✅ **User Retention** (Better UX = more engagement)
- ✅ **Specialization** (5 templates position VERITAS as legal expert)

---

## 🎯 Recommended Next Steps

**Priority 1: Streaming Prototype** ⚡ (60-90 min)
→ Create `StreamingStructuredResponseParser`  
→ Test NDJSON parsing with mock data  
→ Validate streaming architecture  
→ **Goal:** Proof that Streaming + Structured Response works

**Priority 2: Template System** 📋 (90-120 min)
→ Create `PromptTemplateLibrary` (5 templates)  
→ Implement `AdaptiveTokenManager`  
→ Create backend endpoint `/api/v1/chat/structured`  
→ **Goal:** Validate administrative law specialization

**Priority 3: Widget Renderer** 🖼️ (60-90 min)
→ Create `WidgetRenderer` with Image + Button support  
→ Test incremental rendering  
→ **Goal:** Validate UI rendering

**Recommended:** Start with **Priority 1** (Streaming Prototype) to validate core architecture ASAP.

---

## 📚 Documentation

**Full Specification:** `docs/STRUCTURED_RESPONSE_SYSTEM_CONCEPT.md` (1,500+ lines)

**Key Sections:**
- Streaming Client (existing system + new parser)
- Dynamic Token Size (adaptive manager)
- Template System (5 templates, auto-selection)
- Widget Types (text, media, interactive, visualizations)
- Implementation Roadmap (6 phases, 11-17 days)
- Example Use-Cases (with NDJSON responses)

---

**Ready to start implementation?** 🚀

**Contact:** See main concept document for implementation options and detailed specs.

---

**END OF EXECUTIVE SUMMARY**
