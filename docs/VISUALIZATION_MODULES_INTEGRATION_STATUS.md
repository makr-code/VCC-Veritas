# VERITAS Visualisierungs-Module - Integration Status & Empfehlungen

**Datum:** 2025-12-04
**Status:** ⚠️ TEILWEISE INTEGRIERT (API-basiert)
**Nächster Schritt:** Vollständige Orchestrator-Integration

---

## Aktuelle Situation

### ✅ Was FUNKTIONIERT

**1. PowerPoint-inspiriertes Präsentations-Tool**
- **Status:** ✅ OPERATIONAL
- **Datei:** `backend/agents/presentation_canvas_agent.py` (628 LOC)
- **API Endpoint:** `/api/presentations` (registriert in app.py Zeile 639-648)
- **Features:**
  - Visual Description Language (VDL) für LLM-basierte Präsentations-Generierung
  - Canvas-basierte Rendering (Tkinter/PIL)
  - PowerPoint-Export (.pptx)
  - Layouts: title_slide, content, two_column, chart, image, blank
  - Element-Typen: text, shape, chart, image, icon, line, arrow
- **Tests:** Vorhanden (`test_presentation_canvas_agent.py`)
- **Integration:** API-Endpoint verfügbar, kann per REST API genutzt werden

**2. Chart Integration Engine**
- **Status:** ✅ OPERATIONAL
- **Datei:** `backend/visualization/chart_engine.py` (380 LOC)
- **API Endpoint:** `/api/charts` (registriert in app.py Zeile 632-638)
- **Features:**
  - 8 Chart-Typen (LINE, BAR, PIE, SCATTER, HEATMAP, HISTOGRAM, BOX, WATERFALL)
  - 5 Color Schemes (Viridis, Plasma, Cool, VERITAS, Dark)
  - Export: JSON, HTML (interactive Plotly), PNG, SVG
- **Tests:** 36/36 PASSING ✅
- **Integration:** API-Endpoint verfügbar, kann per REST API genutzt werden

**3. Image Generation Module**
- **Status:** ✅ OPERATIONAL
- **Dateien:** `backend/imaging/image_engine.py` + `integration.py` (650 LOC)
- **API Endpoint:** `/api/images` (registriert in app.py Zeile 665-670)
- **Features:**
  - SwarmUI + Stable Diffusion Integration
  - 5 Models (SD 1.5, SDXL, SD Turbo, DALL-E 3, Flux)
  - 5 Tasks (Text2Img, Img2Img, Inpaint, Upscale, Variation)
  - 7 Schedulers (DDIM, PNDM, Heun, Euler, etc.)
  - Prompt-Optimierung mit Quality Presets
- **Tests:** 37/37 PASSING ✅
- **Integration:** API-Endpoint verfügbar, kann per REST API genutzt werden

---

### ⚠️ Was FEHLT - Orchestrator-Integration

**Problem:** Module sind NICHT in das Multi-Agent-System integriert

**Details:**
- ❌ Keine Einträge in Agent Registry (`backend/agents/registry/agent_registry.py`)
- ❌ Keine Integration in AgentOrchestrator (`backend/agents/orchestrator/agent_orchestrator.py`)
- ❌ Keine automatische Agent-Selection durch Orchestrator
- ❌ Module werden NICHT vom intelligenten Pipeline-Manager orchestriert

**Konsequenz:**
- LLM/Orchestrator kann die Module **nur per API-Call** nutzen (Tool Use)
- **Keine nahtlose Integration** in Multi-Agent-Workflows
- **Manuelle API-Aufrufe** erforderlich (nicht automatisch)

---

## Vergleich: API-basiert vs. Orchestrator-integriert

| Aspekt | ✅ API-basiert (IST) | ⭐ Orchestrator-integriert (SOLL) |
|--------|---------------------|-----------------------------------|
| **Verfügbarkeit** | Ja, über REST API | Ja, nativ im Agent-System |
| **LLM Tool Use** | Ja, manuelle API-Calls | Ja, automatisch |
| **Agent Selection** | Manuell | ✅ Automatisch via Capabilities |
| **Pipeline-Integration** | Nein | ✅ Ja, Task-basiert |
| **Dependency Management** | Manuell | ✅ Automatisch via DAG |
| **Progress Tracking** | Basic | ✅ Full Agent-Pipeline-Tracking |
| **Error Recovery** | Manuell | ✅ Orchestrator-gesteuert |
| **Parallel Execution** | Nein | ✅ Ja, via Pipeline Manager |

---

## Empfohlene Integration - 3 Schritte

### Schritt 1: Agent Registry Integration

**Datei:** `backend/agents/registry/agent_registry.py`

**Neue Capabilities hinzufügen:**
```python
class AgentCapability(Enum):
    # ... existing capabilities ...

    # Visualization & Generation
    CHART_GENERATION = "chart_generation"
    PRESENTATION_CREATION = "presentation_creation"
    IMAGE_GENERATION = "image_generation"
    VISUAL_DESIGN = "visual_design"
```

**Agents registrieren:**
```python
# In get_agent_registry() oder separater Registration-Funktion

# Chart Engine Agent
registry.register_agent(
    agent_id="chart_engine_v1",
    name="Chart Generation Agent",
    capabilities=[AgentCapability.CHART_GENERATION],
    priority=0.8,
    lifecycle="singleton",
    metadata={
        "chart_types": 8,
        "export_formats": ["json", "html", "png", "svg"],
        "endpoint": "/api/charts"
    }
)

# Presentation Canvas Agent
registry.register_agent(
    agent_id="presentation_canvas_v1",
    name="Presentation Canvas Agent",
    capabilities=[
        AgentCapability.PRESENTATION_CREATION,
        AgentCapability.VISUAL_DESIGN
    ],
    priority=0.85,
    lifecycle="singleton",
    metadata={
        "vdl_support": True,
        "layouts": 6,
        "export_format": "pptx",
        "endpoint": "/api/presentations"
    }
)

# Image Generation Agent
registry.register_agent(
    agent_id="image_generation_v1",
    name="Image Generation Agent",
    capabilities=[AgentCapability.IMAGE_GENERATION],
    priority=0.9,
    lifecycle="on_demand",
    metadata={
        "models": 5,
        "tasks": 5,
        "backend": "swarmui",
        "endpoint": "/api/images"
    }
)
```

---

### Schritt 2: Orchestrator Task Blueprints

**Datei:** `backend/agents/orchestrator/agent_orchestrator.py`

**Task Blueprints hinzufügen:**
```python
DYNAMIC_AGENT_TASK_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    # ... existing blueprints ...

    # Visualization Tasks
    "chart_generation": {
        "stage": "response_generation",
        "capability": "chart_generation",
        "priority": 0.7,
        "parallel": True,
        "depends_on": ["data_analysis", "statistics"],
    },

    "presentation_creation": {
        "stage": "response_generation",
        "capability": "presentation_creation",
        "priority": 0.75,
        "parallel": False,
        "depends_on": ["content_synthesis", "visual_design"],
    },

    "image_generation": {
        "stage": "response_enhancement",
        "capability": "image_generation",
        "priority": 0.65,
        "parallel": True,
        "depends_on": ["prompt_optimization"],
    },
}
```

---

### Schritt 3: Pipeline Manager Integration

**Datei:** `backend/agents/orchestrator/pipeline_manager.py`

**Agent Dispatch erweitern:**
```python
async def _execute_visualization_task(
    self,
    task: AgentPipelineTask,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute visualization task (chart, presentation, image)"""

    if task.capability == "chart_generation":
        # Call Chart Engine
        from backend.visualization.chart_engine import get_chart_manager
        manager = get_chart_manager()

        # Extract data from context
        chart_data = context.get("chart_data", {})

        # Generate chart
        chart = await manager.create_chart(
            chart_type=chart_data.get("type", "line"),
            title=chart_data.get("title", "Chart")
        )

        for series in chart_data.get("series", []):
            chart.add_series(series)

        result = await chart.generate_chart()

        return {
            "status": "success",
            "chart_id": chart.chart_id,
            "export_html": chart.export_html()
        }

    elif task.capability == "presentation_creation":
        # Call Presentation Canvas Agent
        from backend.agents.presentation_canvas_agent import PresentationCanvasAgent
        agent = PresentationCanvasAgent()

        # Generate VDL from prompt
        vdl = agent.create_vdl(
            prompt=context.get("presentation_prompt", ""),
            num_slides=context.get("num_slides", 3)
        )

        # Render to PowerPoint
        pptx_path = agent.export_powerpoint(vdl)

        return {
            "status": "success",
            "vdl": vdl,
            "pptx_path": pptx_path
        }

    elif task.capability == "image_generation":
        # Call Image Generation Module
        from backend.imaging.integration import get_image_generation_agent
        agent = get_image_generation_agent()

        # Generate image
        request_data = {
            "prompt": context.get("image_prompt", ""),
            "model": context.get("model", "sdxl"),
            "width": context.get("width", 768),
            "height": context.get("height", 768),
            "quality": context.get("quality", "high")
        }

        result = await agent.process_request(request_data)

        return result
```

---

## Integration-Vorteile

**Nach vollständiger Integration:**

✅ **Automatische Agent-Selection**
- Orchestrator wählt Chart/Presentation/Image Agent basierend auf Query-Intent
- Keine manuellen API-Calls mehr nötig

✅ **Pipeline-Integration**
- Visualisierungs-Tasks werden in Multi-Agent-Workflows eingebettet
- Dependency-Management via DAG (gerichteter azyklischer Graph)

✅ **Parallel Execution**
- Chart-Generierung parallel zu Datenanalyse
- Image-Generierung während Response-Synthesis

✅ **Error Recovery**
- Orchestrator kann Fehler abfangen und Retry-Logic anwenden
- Fallback zu alternativen Visualisierungs-Methoden

✅ **Progress Tracking**
- Visualisierungs-Tasks werden im Streaming Progress angezeigt
- User sieht "Generating chart...", "Creating presentation...", etc.

✅ **Context Sharing**
- Agents können Kontext aus vorherigen Pipeline-Steps nutzen
- Daten müssen nicht mehrfach extrahiert werden

---

## Implementierungs-Aufwand

| Schritt | Aufwand | LOC | Datei |
|---------|---------|-----|-------|
| Registry Integration | 🟢 Niedrig | ~60 LOC | `agent_registry.py` |
| Task Blueprints | 🟡 Mittel | ~40 LOC | `agent_orchestrator.py` |
| Pipeline Dispatch | 🟡 Mittel | ~80 LOC | `pipeline_manager.py` |
| **Total** | **~180 LOC** | **~3-4 Stunden** | **3 Dateien** |

---

## Entscheidungs-Matrix

### Option A: Nur API-basiert (IST-Zustand)

**Vorteile:**
- ✅ Sofort verfügbar
- ✅ Einfach zu nutzen (REST API)
- ✅ Unabhängig vom Agent-System

**Nachteile:**
- ❌ Manuelle Integration nötig
- ❌ Keine Pipeline-Orchestrierung
- ❌ Kein Progress Tracking
- ❌ Keine automatische Selection

**Geeignet für:**
- Externe Tool-Integration
- LLM mit Tool Use Capabilities
- Standalone-Nutzung

---

### Option B: Vollständige Orchestrator-Integration (EMPFOHLEN)

**Vorteile:**
- ✅ Nahtlose Multi-Agent-Workflows
- ✅ Automatische Agent-Selection
- ✅ Pipeline-Orchestrierung
- ✅ Progress Tracking & Error Recovery
- ✅ Context Sharing zwischen Agents

**Nachteile:**
- ⚠️ Zusätzlicher Implementierungs-Aufwand (~180 LOC)
- ⚠️ Abhängigkeit vom Agent-System

**Geeignet für:**
- Produktiv-Deployment
- Complex Multi-Step Queries
- Automatisierte Visualisierungs-Workflows
- Enterprise-Features

---

## Empfehlung

### ⭐ **Vollständige Integration implementieren**

**Begründung:**
1. **Konsistenz:** Alle anderen Domain-Agents sind im Orchestrator integriert
2. **Automatisierung:** LLM kann Visualisierungen automatisch generieren
3. **Skalierbarkeit:** Pipeline-Manager kann Visualisierungs-Tasks optimal planen
4. **User Experience:** Progress Tracking zeigt Visualisierungs-Status
5. **Zukunftssicherheit:** Neue Visualisierungs-Features einfach hinzufügbar

**Nächste Schritte (Priorität):**
1. 🔴 **Hoch:** Agent Registry Integration (~1 Stunde)
2. 🟡 **Mittel:** Task Blueprints hinzufügen (~1 Stunde)
3. 🟡 **Mittel:** Pipeline Dispatch erweitern (~1-2 Stunden)
4. 🟢 **Optional:** Tests für Integration (~1 Stunde)

**Gesamt-Aufwand:** ~4-5 Stunden für vollständige Integration

---

## Status-Übersicht

| Modul | Implementiert | API Endpoint | Tests | Orchestrator | Registry |
|-------|---------------|--------------|-------|--------------|----------|
| **Chart Engine** | ✅ Ja | ✅ Ja | ✅ 36/36 | ❌ Nein | ❌ Nein |
| **Presentation Canvas** | ✅ Ja | ✅ Ja | ✅ Ja | ❌ Nein | ❌ Nein |
| **Image Generation** | ✅ Ja | ✅ Ja | ✅ 37/37 | ❌ Nein | ❌ Nein |

**Zusammenfassung:**
- **Module:** ✅ 3/3 vollständig implementiert
- **API:** ✅ 3/3 Endpoints registriert
- **Tests:** ✅ 73/73 passing
- **Orchestrator:** ❌ 0/3 integriert
- **Registry:** ❌ 0/3 registriert

**Produktions-Bereitschaft:**
- **API-Nutzung:** ✅ 100% bereit
- **Orchestrator-Integration:** ⚠️ 0% (Empfohlen für Production)

---

## Fazit

**Aktueller Stand:**
Alle 3 Visualisierungs-Module (Chart, Presentation, Image) sind **vollständig implementiert und getestet**. Sie können sofort über REST API genutzt werden und sind in `app.py` registriert.

**Empfehlung:**
Für Production-Deployment wird **vollständige Orchestrator-Integration empfohlen** (~4-5 Stunden Aufwand), um nahtlose Multi-Agent-Workflows, automatische Agent-Selection und Progress Tracking zu ermöglichen.

**Priorisierung:**
1. ⭐ Agent Registry Integration (kritisch)
2. ⭐ Task Blueprints (wichtig)
3. 🟡 Pipeline Dispatch (wichtig)
4. 🟢 Integration Tests (optional)

Mit vollständiger Integration werden die Visualisierungs-Module zu **First-Class Citizens** im VERITAS Agent-System und können vom LLM/Orchestrator automatisch eingesetzt werden.
