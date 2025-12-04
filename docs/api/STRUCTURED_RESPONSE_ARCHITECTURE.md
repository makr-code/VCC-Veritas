# 🏗️ VERITAS Structured Response System - Architecture Diagrams

**Version:** v4.1.0
**Date:** 12. Oktober 2025

---

## 📊 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE (Tkinter)                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      ChatWindowBase                               │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │  │
│  │  │  Chat Display  │  │ Input Field    │  │ Template Badge │     │  │
│  │  │  (Text Widget) │  │                │  │ (Current Mode) │     │  │
│  │  └────────────────┘  └────────────────┘  └────────────────┘     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓ ↑
                    User Query  /  NDJSON Streaming Response
                                    ↓ ↑
┌─────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Python/Tkinter)                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │        StreamingStructuredResponseParser (NEW ~300 LOC)          │  │
│  │  - Parse NDJSON line-by-line                                     │  │
│  │  - Handle chunk types: response_start, text_chunk, widget, end   │  │
│  │  - Buffer incomplete JSON chunks                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │ MarkdownRenderer │  │  WidgetRenderer  │  │ ChatDisplayFormatter│ │
│  │  (EXISTING ✅)   │  │   (NEW ~500 LOC) │  │   (EXTEND ~200 LOC) │ │
│  │  - Headers       │  │  - Images (PIL)  │  │  - Sources         │  │
│  │  - Bold/Italic   │  │  - Buttons       │  │  - Confidence      │  │
│  │  - Code Blocks   │  │  - Canvas        │  │  - Suggestions     │  │
│  │  - Lists/Tables  │  │  - Charts (plt)  │  │  - Metadata        │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘    │
│                                    ↓                                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                 Tkinter Text Widget + Embedded Widgets            │  │
│  │  - text.insert() for markdown                                     │  │
│  │  - text.window_create() for widgets (buttons, canvas, images)    │  │
│  │  - Tag-based styling (30+ tags)                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↑
                       NDJSON Stream (HTTP/WebSocket)
                                    ↑
┌─────────────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI)                                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │         /api/v1/chat/structured (NEW Endpoint ~100 LOC)          │  │
│  │  1. Receive user_query + template_id (optional)                  │  │
│  │  2. Template Auto-Selection (if not provided)                    │  │
│  │  3. Adaptive Token Estimation                                    │  │
│  │  4. Generate NDJSON Stream                                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │PromptTemplateLib │  │AdaptiveTokenMgr  │  │ StreamingService │    │
│  │  (NEW ~400 LOC)  │  │  (NEW ~200 LOC)  │  │  (EXISTING ✅)   │    │
│  │ - 5 Templates    │  │ - Complexity NLP │  │ - WebSocket      │    │
│  │ - Auto-Selection │  │ - 1K-16K Tokens  │  │ - Progress       │    │
│  │ - System Prompts │  │ - RAG Context    │  │ - Cancel         │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘    │
│                                    ↓                                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Ollama Client (EXISTING ✅ ~1,200 LOC)              │  │
│  │  - generate_response(stream=True) → AsyncGenerator               │  │
│  │  - Dynamic num_predict (tokens)                                  │  │
│  │  - Template-specific system prompt                               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
                         Ollama API (llama3.2:latest)
                                    ↓
                     LLM Response Stream (text chunks)
```

---

## 🌊 NDJSON Streaming Flow

```
TIME: 0ms
┌────────────────────────────────────────────────────────────────┐
│ Backend: Template Selected = "zustaendigkeit_behoerde"        │
│ Backend: Estimated Tokens = 2048 (simple question, 0.5x)      │
└────────────────────────────────────────────────────────────────┘
                            ↓
TIME: 10ms
┌────────────────────────────────────────────────────────────────┐
│ NDJSON Chunk 1 (response_start):                              │
│ {"type":"response_start","metadata":{"template":"...","...}}  │
│                                                                │
│ Frontend: Parse → Display Template Badge "Zuständigkeit"      │
└────────────────────────────────────────────────────────────────┘
                            ↓
TIME: 200ms (LLM starts generating)
┌────────────────────────────────────────────────────────────────┐
│ NDJSON Chunk 2 (text_chunk):                                  │
│ {"type":"text_chunk","content":"Gemäß **BauGB §35** ist..."}  │
│                                                                │
│ Frontend: Parse → MarkdownRenderer.render_markdown(append=True)│
│ UI: Text appears IMMEDIATELY                                  │
└────────────────────────────────────────────────────────────────┘
                            ↓
TIME: 500ms (LLM continues)
┌────────────────────────────────────────────────────────────────┐
│ NDJSON Chunk 3 (text_chunk):                                  │
│ {"type":"text_chunk","content":"Die Zuständigkeiten sind..."}  │
│                                                                │
│ Frontend: Parse → More text appended                          │
└────────────────────────────────────────────────────────────────┘
                            ↓
TIME: 800ms (Widget appears)
┌────────────────────────────────────────────────────────────────┐
│ NDJSON Chunk 4 (widget):                                      │
│ {"type":"widget","widget":{"type":"table","headers":[...]}}   │
│                                                                │
│ Frontend: Parse → WidgetRenderer.render_widget()              │
│ UI: Table appears DURING LLM generation                       │
└────────────────────────────────────────────────────────────────┘
                            ↓
TIME: 1200ms (More text)
┌────────────────────────────────────────────────────────────────┐
│ NDJSON Chunk 5 (text_chunk):                                  │
│ {"type":"text_chunk","content":"Weitere Informationen..."}    │
└────────────────────────────────────────────────────────────────┘
                            ↓
TIME: 1500ms (LLM done, finalize)
┌────────────────────────────────────────────────────────────────┐
│ NDJSON Chunk 6 (response_end):                                │
│ {"type":"response_end","metadata":{"confidence":0.92,...}}    │
│                                                                │
│ Frontend: Parse → ChatDisplayFormatter adds:                  │
│  - Sources (clickable links)                                  │
│  - Suggestions (clickable buttons)                            │
│  - Confidence badge (0.92 → "Hoch 92%")                       │
└────────────────────────────────────────────────────────────────┘
                            ↓
TIME: 1500ms - DONE ✅
User sees: Text + Table + Sources + Suggestions (all streamed in real-time)
```

---

## 📋 Template Selection Flow

```
User Query: "Vollständige Prüfung Bauantrag mit allen Aspekten"
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ Backend: PromptTemplateLibrary.select_template_auto()         │
│                                                                │
│ Keyword Matching:                                             │
│  ✅ "vollständig" found → Check for "vollstaendige_pruefung"  │
│  ✅ "alle" found → Confirms complex template                  │
│  ✅ "aspekte" found → Multi-part question                     │
│                                                                │
│ Selected: "vollstaendige_pruefung"                            │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ Backend: AdaptiveTokenManager.estimate_required_tokens()      │
│                                                                │
│ Input:                                                         │
│  - template: "vollstaendige_pruefung"                         │
│  - base_tokens: 16384 (from template spec)                    │
│  - query_complexity: "very_complex" (NLP analysis)            │
│  - complexity_factor: 2.0x                                    │
│  - rag_context_size: 1024 tokens                              │
│  - is_followup: False                                         │
│                                                                │
│ Calculation:                                                  │
│  (16384 * 2.0 + 1024) * 1.0 = 33792                          │
│  Clamped to max: 16384                                        │
│                                                                │
│ Estimated Tokens: 16384 (max)                                 │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ Backend: Get Template System Prompt                           │
│                                                                │
│ Template: vollstaendige_pruefung                              │
│ System Prompt: (800+ Zeilen spezialisierter Prompt)          │
│  - Executive Summary mit Ampel (✅/⚠️/❌)                     │
│  - Formale Prüfung (Checkliste)                              │
│  - Rechtliche Prüfung (BauGB, BauNVO, LBO)                   │
│  - Sachliche Prüfung (Statik, Brandschutz, EnEV/GEG)         │
│  - Gesamtfazit + Handlungsempfehlungen                       │
│                                                                │
│ Expected Widgets:                                             │
│  - Table (Prüfungsübersicht)                                  │
│  - Canvas (Abstandsflächen-Visualisierung)                    │
│  - Chart (Energieeffizienz-Anforderungen)                     │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ Backend: Ollama Request                                       │
│                                                                │
│ POST /api/generate                                            │
│ {                                                             │
│   "model": "llama3.2:latest",                                │
│   "prompt": "[User Query]",                                  │
│   "system": "[Template System Prompt 800+ Zeilen]",         │
│   "stream": true,                                            │
│   "options": {                                               │
│     "num_predict": 16384,  ← DYNAMIC!                       │
│     "temperature": 0.3     ← Low for legal precision        │
│   }                                                          │
│ }                                                            │
└────────────────────────────────────────────────────────────────┘
                            ↓
                  LLM generates 16,384 tokens
             (enough for complete review with all 3 aspects)
```

---

## 🎨 Widget Rendering Architecture

```
┌────────────────────────────────────────────────────────────────┐
│              WidgetRenderer (NEW ~500 LOC)                    │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ render_widget(widget_spec: dict) → None                  │ │
│  │                                                           │ │
│  │ Dispatcher:                                              │ │
│  │  - widget_spec['type'] == 'table'  → _render_table()    │ │
│  │  - widget_spec['type'] == 'image'  → _render_image()    │ │
│  │  - widget_spec['type'] == 'button' → _render_button()   │ │
│  │  - widget_spec['type'] == 'canvas' → _render_canvas()   │ │
│  │  - widget_spec['type'] == 'chart'  → _render_chart()    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ _render_image(spec: dict)                                │ │
│  │  1. Load image (URL/path/base64) via PIL                │ │
│  │  2. Resize if spec['width'] provided                    │ │
│  │  3. Convert to ImageTk.PhotoImage                       │ │
│  │  4. text_widget.image_create(END, image=photo)          │ │
│  │  5. Store ref (self.embedded_widgets.append(photo))     │ │
│  │  6. Add caption if provided                             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ _render_button(spec: dict)                               │ │
│  │  1. Create tk.Button with spec['label']                 │ │
│  │  2. Bind click → _handle_button_click(spec)             │ │
│  │  3. text_widget.window_create(END, window=button)       │ │
│  │  4. Store ref (self.embedded_widgets.append(button))    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ _render_canvas(spec: dict)                               │ │
│  │  1. Create tk.Canvas(width, height)                     │ │
│  │  2. Execute draw_commands:                              │ │
│  │     - "line" → canvas.create_line(...)                  │ │
│  │     - "rect" → canvas.create_rectangle(...)             │ │
│  │     - "text" → canvas.create_text(...)                  │ │
│  │  3. text_widget.window_create(END, window=canvas)       │ │
│  │  4. Store ref                                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ _render_chart(spec: dict)                                │ │
│  │  1. Create matplotlib Figure (plt.subplots)             │ │
│  │  2. Plot based on chart_type (bar/line/pie)            │ │
│  │  3. Convert to Tkinter via FigureCanvasTkAgg            │ │
│  │  4. text_widget.window_create(END, window=canvas_widget)│ │
│  │  5. Store ref + close figure (plt.close)               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ cleanup()                                                │ │
│  │  - Destroy all embedded widgets                         │ │
│  │  - Clear reference list                                 │ │
│  │  - Prevent memory leaks                                 │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Request-Response Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: USER INPUT                                              │
│  User types: "Vollständige Prüfung Bauantrag"                   │
│  Clicks: Send Button                                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: FRONTEND → BACKEND REQUEST                              │
│  POST /api/v1/chat/structured                                  │
│  Body: {"user_query": "...", "template_id": null}              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: BACKEND TEMPLATE SELECTION                              │
│  PromptTemplateLibrary.select_template_auto()                  │
│  Keywords: "vollständig" → "vollstaendige_pruefung"            │
│  Base Tokens: 16384                                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: BACKEND TOKEN ESTIMATION                                │
│  AdaptiveTokenManager.estimate_required_tokens()               │
│  Complexity: very_complex (2.0x)                               │
│  Estimated: 16384 tokens (max)                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: BACKEND OLLAMA REQUEST                                  │
│  ollama_client.generate_response(stream=True)                  │
│  System Prompt: [800+ Zeilen Template]                        │
│  Num Predict: 16384                                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: BACKEND NDJSON STREAMING                                │
│  StreamingResponse (media_type="application/x-ndjson")         │
│  Yield: response_start                                         │
│  Yield: text_chunk (multiple)                                  │
│  Yield: widget (table, canvas, chart)                          │
│  Yield: response_end                                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: FRONTEND NDJSON PARSING                                 │
│  StreamingStructuredResponseParser.process_chunk()             │
│  For each line:                                                │
│   - Parse JSON                                                 │
│   - Handle based on type                                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: FRONTEND RENDERING                                      │
│  - response_start → Display template badge                     │
│  - text_chunk → MarkdownRenderer (append mode)                 │
│  - widget → WidgetRenderer (table/chart/canvas)                │
│  - response_end → ChatDisplayFormatter (sources/suggestions)   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: USER SEES RESULT (Real-Time!)                           │
│  ✅ Template badge appeared at 10ms                            │
│  ✅ Text started appearing at 200ms (streaming)                │
│  ✅ Table appeared at 800ms (during LLM generation)            │
│  ✅ Canvas appeared at 1200ms                                  │
│  ✅ Chart appeared at 1400ms                                   │
│  ✅ Sources/Suggestions appeared at 1500ms (done)              │
│                                                                │
│  Total Response Time: 1500ms (1.5s)                            │
│  User Experience: Saw progress in real-time, never "frozen"   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Component Dependency Graph

```
                      ┌─────────────────┐
                      │   User Query    │
                      └────────┬────────┘
                               │
                               ↓
          ┌────────────────────────────────────────┐
          │                                        │
    ┌─────▼─────┐                          ┌──────▼──────┐
    │ Frontend  │                          │  Backend    │
    └─────┬─────┘                          └──────┬──────┘
          │                                       │
          │                                       │
    ┌─────▼──────────────────┐         ┌─────────▼─────────────┐
    │                        │         │                       │
    │ StreamingStructured    │         │ PromptTemplateLibrary │
    │  ResponseParser        │         │   - 5 Templates       │
    │  (NEW ~300 LOC)        │         │   - Auto-Selection    │
    │                        │         │   (NEW ~400 LOC)      │
    └─────┬──────────────────┘         └─────────┬─────────────┘
          │                                       │
          │                                       │
    ┌─────▼─────────┐                    ┌───────▼────────┐
    │               │                    │                │
    │ MarkdownRenderer                   │ AdaptiveToken  │
    │ (EXISTING ✅)                      │  Manager       │
    │ - 1,000 LOC                        │ (NEW ~200 LOC) │
    │               │                    │                │
    └───────────────┘                    └───────┬────────┘
                                                 │
    ┌──────────────┐                    ┌────────▼────────┐
    │              │                    │                 │
    │ WidgetRenderer                    │ Ollama Client   │
    │ (NEW ~500 LOC)                    │ (EXISTING ✅)   │
    │  - Images    │                    │ - Streaming     │
    │  - Buttons   │                    │ - ~1,200 LOC    │
    │  - Canvas    │                    │                 │
    │  - Charts    │                    │                 │
    │              │                    │                 │
    └──────┬───────┘                    └─────────────────┘
           │
           │
    ┌──────▼────────┐
    │               │
    │ ChatDisplay   │
    │  Formatter    │
    │ (EXTEND ✅)   │
    │ - Sources     │
    │ - Suggestions │
    │ - Confidence  │
    │               │
    └───────────────┘
```

---

## 💾 Memory Management Flow

```
BEFORE: New Response arrives
┌────────────────────────────────────────────────────────────────┐
│ WidgetRenderer.cleanup()                                       │
│  - Destroy all tk.Button widgets                              │
│  - Destroy all tk.Canvas widgets                              │
│  - Destroy all matplotlib FigureCanvasTkAgg widgets           │
│  - Release PIL Image references                               │
│  - Clear embedded_widgets list                                │
│                                                                │
│ ChatDisplayFormatter.clear_chat()                              │
│  - Delete text widget content (1.0, END)                      │
│  - Reset scroll position                                      │
└────────────────────────────────────────────────────────────────┘
                            ↓
DURING: Streaming Response
┌────────────────────────────────────────────────────────────────┐
│ StreamingStructuredResponseParser                              │
│  - Buffer size limit: 10MB (prevent memory overflow)          │
│  - Widget queue limit: 100 widgets per response               │
│  - Auto-flush buffer after each complete JSON chunk           │
└────────────────────────────────────────────────────────────────┘
                            ↓
AFTER: Response complete
┌────────────────────────────────────────────────────────────────┐
│ Memory Cleanup (automatic)                                     │
│  - Python GC collects unreferenced objects                    │
│  - PIL images released if no widget references                │
│  - matplotlib figures closed (plt.close)                       │
│                                                                │
│ Memory Usage (estimated per response):                        │
│  - Text: ~10-50 KB (markdown)                                 │
│  - Images: ~100-500 KB each (resized)                         │
│  - Charts: ~50-200 KB each (matplotlib)                       │
│  - Canvas: ~10-50 KB (vector graphics)                        │
│  - Total: ~200 KB - 2 MB per response                         │
└────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Success Metrics

```
┌────────────────────────────────────────────────────────────────┐
│ METRIC 1: Streaming Latency                                    │
│  - First chunk visible: < 200ms                               │
│  - Widget appears during streaming: ✅                        │
│  - Total response time: 1-3s (complex templates)              │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ METRIC 2: Token Optimization                                   │
│  - Simple questions: 1024 tokens (was 4096) → 75% savings     │
│  - Complex questions: 16384 tokens (was 4096) → 300% more     │
│  - Auto-detection accuracy: > 90% correct template            │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ METRIC 3: Widget Rendering                                     │
│  - Image rendering: < 100ms                                   │
│  - Chart rendering: < 200ms                                   │
│  - Canvas rendering: < 50ms                                   │
│  - Memory cleanup: No leaks after 1000 responses              │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ METRIC 4: Template Accuracy                                    │
│  - Keyword-matching: > 85% correct selection                  │
│  - User override: Available (dropdown in UI)                  │
│  - Template coverage: 100% (5 templates cover all use-cases)  │
└────────────────────────────────────────────────────────────────┘
```

---

**END OF ARCHITECTURE DIAGRAMS**
