# 📋 Structured Response System - Quick Reference

**Version:** v4.1.0 | **Status:** Design Complete ✅ | **Next:** Implementation

---

## 🎯 The 3 Critical Requirements

| # | Requirement | Solution | Implementation |
|---|-------------|----------|----------------|
| 1️⃣ | **Streaming Client** ⚡ | NDJSON (Newline-Delimited JSON) | `StreamingStructuredResponseParser` (~300 LOC) |
| 2️⃣ | **Dynamic Token Size** 📏 | Adaptive Token Manager (1K-16K) | `AdaptiveTokenManager` (~200 LOC) |
| 3️⃣ | **Template System** 📋 | 5 Specialized Legal Templates | `PromptTemplateLibrary` (~400 LOC) |

---

## 📋 The 5 Legal Templates

| Template | Base Tokens | Focus | Widgets | Auto-Trigger Keywords |
|----------|-------------|-------|---------|----------------------|
| **Zuständigkeit** | 2048 | Authority Determination | Table | "zuständig", "behörde" |
| **Formale Prüfung** | 4096 | Formal Review (Completeness) | Table, Checklist | "vollständig", "unterlagen", "formell" |
| **Rechtliche Prüfung** | 6144 | Legal Review (Compliance) | Canvas, Table | "rechtlich", "zulässig", "baurecht" |
| **Sachliche Prüfung** | 8192 | Technical Review (Standards) | Chart, Table | "technisch", "statik", "brandschutz" |
| **Vollständige Prüfung** | 16384 | Complete (All 3 Reviews) | All Widgets | "komplett", "umfassend", "vollständige prüfung" |

---

## 📊 Token Estimation Examples

| Question | Template | Complexity | Estimated Tokens | Savings/Gain |
|----------|----------|------------|------------------|--------------|
| "Wer ist zuständig?" | Zuständigkeit | Simple (0.5x) | **1024** | ✅ -75% (was 4096) |
| "Formale Prüfung Bauantrag" | Formale Prüfung | Medium (1.0x) | **4608** | ➡️ +13% |
| "Vollständige Prüfung inkl. allen Aspekten" | Vollständige Prüfung | Very Complex (2.0x) | **16384** | ✅ +300% (was 4096) |

**Formula:**
```python
tokens = (TEMPLATE_BASE * COMPLEXITY_FACTOR + RAG_SIZE) * FOLLOWUP_REDUCTION
# Clamped: 1024 (min) - 16384 (max)
```

---

## 🎨 Widget Types Quick Reference

### Text (existing ✅)
```json
{"type":"text_chunk","content":"**Markdown** text here"}
```

### Table (new ⭐)
```json
{
  "type":"widget",
  "widget":{
    "type":"table",
    "headers":["Col1","Col2"],
    "rows":[["Val1","Val2"]]
  }
}
```

### Image (new ⭐)
```json
{
  "type":"widget",
  "widget":{
    "type":"image",
    "url":"https://...",
    "caption":"Description",
    "width":400
  }
}
```

### Canvas (new ⭐)
```json
{
  "type":"widget",
  "widget":{
    "type":"canvas",
    "width":400,
    "height":300,
    "draw_commands":[
      {"cmd":"line","x1":0,"y1":0,"x2":100,"y2":100,"color":"red"},
      {"cmd":"rect","x":50,"y":50,"width":100,"height":80,"fill":"gray"},
      {"cmd":"text","x":100,"y":90,"text":"Label","font":["Arial",10]}
    ]
  }
}
```

### Chart (new ⭐)
```json
{
  "type":"widget",
  "widget":{
    "type":"chart",
    "chart_type":"bar",
    "title":"Chart Title",
    "data":{
      "labels":["A","B","C"],
      "values":[10,20,15]
    },
    "unit":"kWh/m²a"
  }
}
```

### Button (new ⭐)
```json
{
  "type":"widget",
  "widget":{
    "type":"button",
    "label":"Click me",
    "action":"show_details",
    "payload":{"id":"123"}
  }
}
```

---

## 🌊 NDJSON Streaming Format

**Structure:**
```ndjson
{"type":"response_start","metadata":{...}}
{"type":"text_chunk","content":"..."}
{"type":"widget","widget":{...}}
{"type":"response_end","metadata":{...}}
```

**Chunk Types:**

| Type | When | Content |
|------|------|---------|
| `response_start` | Immediately (header) | Template, estimated tokens |
| `text_chunk` | During streaming | Markdown text (incremental) |
| `widget` | When widget appears | Widget spec (table, chart, etc.) |
| `response_end` | Final chunk | Confidence, sources, suggestions |

**Example:**
```ndjson
{"type":"response_start","metadata":{"template":"zustaendigkeit_behoerde","estimated_tokens":2048}}
{"type":"text_chunk","content":"Gemäß **BauGB §35**..."}
{"type":"widget","widget":{"type":"table","headers":["Behörde","Zuständigkeit"],"rows":[...]}}
{"type":"text_chunk","content":"Weitere Details..."}
{"type":"response_end","metadata":{"confidence":0.92,"sources":[...],"suggestions":[...]}}
```

---

## 🏗️ Implementation Checklist

### Phase 1: Foundation + Streaming (2-3 days)
- [ ] Define NDJSON schema
- [ ] Create `StreamingStructuredResponseParser`
- [ ] Create `WidgetRenderer` base class
- [ ] Test with mock NDJSON data

### Phase 2: Backend Templates (2-3 days)
- [ ] Create `PromptTemplateLibrary` (5 templates)
- [ ] Create `AdaptiveTokenManager`
- [ ] Create `/api/v1/chat/structured` endpoint
- [ ] Test template auto-selection

### Phase 3: Widgets (2-3 days)
- [ ] Image renderer (PIL/Pillow)
- [ ] Button renderer
- [ ] Canvas renderer (tkinter.Canvas)
- [ ] Chart renderer (matplotlib)

### Phase 4: Integration (1-2 days)
- [ ] Extend `ChatDisplayFormatter`
- [ ] Integrate with `StreamingUIMixin`
- [ ] Error handling

### Phase 5: Advanced (2-3 days)
- [ ] Video support
- [ ] Interactive widgets (sliders, dropdowns)
- [ ] Template selection UI

### Phase 6: Testing (2-3 days)
- [ ] Performance tests
- [ ] Memory management
- [ ] Template tests (all 5)
- [ ] Documentation

**Total:** 11-17 days

---

## 🚀 Quick Start Commands

### Test Streaming Parser (Mock)
```python
# Create parser
parser = StreamingStructuredResponseParser(chat_formatter, widget_renderer)

# Simulate NDJSON stream
chunks = [
    '{"type":"response_start","metadata":{"template":"zustaendigkeit_behoerde"}}',
    '{"type":"text_chunk","content":"**Zuständig:**\\n\\n"}',
    '{"type":"widget","widget":{"type":"table",...}}',
    '{"type":"response_end","metadata":{...}}'
]

for chunk in chunks:
    await parser.process_chunk(chunk)
```

### Test Template Selection
```python
template_lib = PromptTemplateLibrary()

# Auto-selection
template_id = template_lib.select_template_auto("Wer ist zuständig?", {})
# Returns: "zustaendigkeit_behoerde"

template = template_lib.get_template(template_id)
print(template.system_prompt)
```

### Test Adaptive Tokens
```python
token_mgr = AdaptiveTokenManager()

tokens = token_mgr.estimate_required_tokens(
    user_query="Vollständige Prüfung Bauantrag",
    template="vollstaendige_pruefung",
    rag_context_size=1024,
    is_followup=False
)
# Returns: 16384 (very complex, max tokens)
```

---

## 📚 Documentation Links

- **Full Concept:** `docs/STRUCTURED_RESPONSE_SYSTEM_CONCEPT.md` (1,500+ lines)
- **Executive Summary:** `docs/STRUCTURED_RESPONSE_EXECUTIVE_SUMMARY.md` (600+ lines)
- **This Quick Reference:** `docs/STRUCTURED_RESPONSE_QUICKREF.md`

---

## 💡 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **NDJSON (not JSON)** | Each line = complete object → parseable immediately during streaming |
| **Server-Side Templates** | Centralized, easier updates, no frontend code duplication |
| **Adaptive Tokens** | Optimize cost (simple) vs quality (complex) automatically |
| **Incremental Widget Rendering** | Better UX (widgets appear during LLM generation, not after) |
| **Tkinter-Native** | No web dependencies, full control, better performance |

---

## 🎯 Next Steps

**Recommended:** Start with **Streaming Prototype** (60-90 min)
1. Create `StreamingStructuredResponseParser` (~300 LOC)
2. Test with mock NDJSON data
3. Validate architecture
4. **Goal:** Proof that Streaming + Structured Response works

**Alternative:** Start with **Template System** (90-120 min)
1. Create `PromptTemplateLibrary` (5 templates)
2. Create `AdaptiveTokenManager`
3. Create backend endpoint
4. **Goal:** Validate administrative law specialization

---

## ✅ Success Criteria

- [ ] NDJSON parsing works (line-by-line, no blocking)
- [ ] Widgets appear **during** streaming (not after)
- [ ] 5 templates auto-select correctly (keyword-matching)
- [ ] Token estimation varies 1K-16K based on complexity
- [ ] All widget types render correctly (table, chart, canvas, image, button)
- [ ] Memory cleanup works (no leaks after 1000 messages)
- [ ] Graceful degradation (fallback to plain text if streaming fails)

---

**Ready to implement?** 🚀

See full documentation for detailed specs and code examples.

---

**END OF QUICK REFERENCE**
