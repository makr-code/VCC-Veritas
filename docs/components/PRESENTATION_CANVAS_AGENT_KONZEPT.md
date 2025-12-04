# Presentation Canvas Agent - Erweiterte Präsentations-Generierung

**Erstellt:** 3. Dezember 2025
**Version:** 2.0.0
**Status:** 🟢 IMPLEMENTIERT

---

## 📋 Übersicht

Der **Presentation Canvas Agent** erweitert den Vector Chart Agent um umfassende Präsentations-Erstellungsfähigkeiten. Anstatt nur Charts zu generieren, kann das System jetzt komplette Präsentationen mit einer **bildbeschreibenden Sprache** (Visual Description Language - VDL) erstellen.

### Kernkonzept: Visual Description Language (VDL)

Die VDL ist eine strukturierte JSON-basierte Sprache, die visuelle Elemente beschreibt. Sie fungiert als Vermittler zwischen:

1. **LLM** → Generiert VDL-Spezifikationen aus natürlicher Sprache
2. **Canvas Agent** → Interpretiert VDL und rendert Grafikelemente
3. **AI-Bildgenerator** (Zukunft) → Kann VDL-Beschreibungen für Bildgenerierung nutzen

---

## 🎯 Neue Funktionen

### 1. Bildbeschreibende Sprache (VDL)

Die VDL definiert Präsentationen strukturiert:

```json
{
  "metadata": {
    "title": "Präsentationstitel",
    "author": "VERITAS Canvas Agent",
    "theme": "professional"
  },
  "slides": [
    {
      "layout": "title_slide",
      "elements": [
        {
          "type": "text",
          "content": "Haupttitel",
          "position": {"x": 50, "y": 200},
          "size": {"width": 700, "height": 100},
          "properties": {
            "font_size": 44,
            "font_weight": "bold",
            "align": "center",
            "color": "#1f4788"
          }
        }
      ]
    }
  ]
}
```

### 2. Unterstützte Element-Typen

#### Text-Elemente
```json
{
  "type": "text",
  "content": "Beispieltext",
  "position": {"x": 100, "y": 200},
  "size": {"width": 600, "height": 50},
  "properties": {
    "font_size": 24,
    "color": "#000000",
    "align": "center"
  }
}
```

#### Formen (Shapes)
```json
{
  "type": "shape",
  "shape": "rectangle",  // rectangle, circle, triangle
  "position": {"x": 100, "y": 150},
  "size": {"width": 200, "height": 150},
  "properties": {
    "fill_color": "#e8f4f8",
    "border_color": "#1f4788",
    "border_width": 2
  }
}
```

#### Chart-Integration
```json
{
  "type": "chart",
  "chart_spec": "bar_chart_bimschg",
  "position": {"x": 100, "y": 150},
  "size": {"width": 600, "height": 400},
  "properties": {
    "chart_id": "bimschg_overview"
  }
}
```

#### AI-Bild-Platzhalter
```json
{
  "type": "image",
  "ai_prompt": "Photorealistic wind turbine at sunset",
  "position": {"x": 200, "y": 200},
  "size": {"width": 400, "height": 300},
  "properties": {
    "ai_generator": "stable_diffusion",
    "style": "photorealistic"
  }
}
```

### 3. Layout-Typen

- **title_slide** - Titelfolie mit Gradient
- **content** - Standard-Inhaltsfolie
- **two_column** - Zweispaltige Folie
- **chart** - Chart-fokussierte Folie
- **image** - Bild-fokussierte Folie
- **blank** - Leere Folie

---

## 🤖 LLM-Integration

### Workflow

```
Nutzer-Prompt
    ↓
LLM (Ollama/vLLM)
    ↓ Generiert VDL
{
  "slides": [
    {"layout": "title_slide", ...},
    {"layout": "content", ...}
  ]
}
    ↓ VDL-Validierung
Canvas Agent
    ↓ Rendering
PNG/PPTX-Export
```

### Beispiel-Prompt an LLM

**System-Prompt:**
```
Du bist ein Experte für visuelle Präsentationsgestaltung.
Erstelle eine Visual Description Language (VDL) Spezifikation.

VDL-Format (JSON):
{
  "metadata": {...},
  "slides": [
    {
      "layout": "title_slide" | "content" | ...,
      "elements": [...]
    }
  ]
}

Elemente-Typen: text, shape, chart, image, icon
Koordinaten-System: Canvas 800x600
```

**Nutzer-Prompt:**
```
Erstelle eine Präsentation über BImSchG-Anlagen mit:
- Titel-Slide: "BImSchG-Anlagen in Brandenburg"
- Inhalts-Slide: Übersicht mit 3 Kategorien
- Chart-Slide: Bar Chart der Anlagen pro Typ
```

**LLM-Antwort (VDL):**
```json
{
  "metadata": {
    "title": "BImSchG-Anlagen in Brandenburg",
    "author": "VERITAS",
    "theme": "professional"
  },
  "slides": [
    {
      "layout": "title_slide",
      "elements": [
        {
          "type": "text",
          "content": "BImSchG-Anlagen in Brandenburg",
          "position": {"x": 50, "y": 200},
          "size": {"width": 700, "height": 100},
          "properties": {"font_size": 44, "align": "center"}
        }
      ]
    },
    {
      "layout": "content",
      "elements": [
        {
          "type": "text",
          "content": "Übersicht Anlagenkategorien",
          "position": {"x": 50, "y": 50},
          "properties": {"font_size": 32}
        },
        {
          "type": "shape",
          "shape": "rectangle",
          "position": {"x": 100, "y": 150},
          "size": {"width": 200, "height": 120}
        }
      ]
    },
    {
      "layout": "chart",
      "elements": [
        {
          "type": "chart",
          "chart_spec": "bimschg_by_type",
          "position": {"x": 100, "y": 100},
          "size": {"width": 600, "height": 400}
        }
      ]
    }
  ]
}
```

---

## 🎨 Canvas-Rendering

### PIL/Pillow-basiertes Rendering

Der Canvas Agent verwendet **Pillow (PIL)** für headless Rendering:

```python
from PIL import Image, ImageDraw, ImageFont

# Canvas erstellen
img = Image.new('RGB', (800, 600), 'white')
draw = ImageDraw.Draw(img)

# Layout anwenden
apply_layout(img, draw, 'title_slide')

# Elemente rendern
for element in vdl['slides'][0]['elements']:
    if element['type'] == 'text':
        render_text(draw, element)
    elif element['type'] == 'shape':
        render_shape(draw, element)

# Speichern
img.save('slide_1.png', 'PNG')
```

### Chart-Integration

Charts werden via VectorChartAgent erstellt und eingebettet:

```python
# VDL-Element für Chart
{
  "type": "chart",
  "chart_spec": "bimschg_overview",
  "position": {"x": 100, "y": 100},
  "size": {"width": 600, "height": 400}
}

# Canvas Agent ruft VectorChartAgent auf
chart_result = await vector_chart_agent.generate_chart(
    template='bimschg_overview'
)

# Chart-Bild in Canvas einfügen
chart_img = Image.open(BytesIO(base64.b64decode(chart_result['image_base64'])))
img.paste(chart_img, (100, 100))
```

---

## 🔮 AI-Bildgenerator-Integration (Zukunft)

Die VDL bereitet bereits die Integration mit AI-Bildgeneratoren vor:

### Platzhalter für AI-Bilder

```json
{
  "type": "image",
  "ai_prompt": "Photorealistic wind turbine farm at golden hour, aerial view",
  "position": {"x": 200, "y": 200},
  "size": {"width": 400, "height": 300},
  "properties": {
    "ai_generator": "stable_diffusion",
    "style": "photorealistic",
    "negative_prompt": "cartoon, unrealistic",
    "steps": 50,
    "cfg_scale": 7.5
  }
}
```

### Zukünftiger Workflow

```
VDL mit AI-Image-Element
    ↓
AI-Bildgenerator-Service
  (Stable Diffusion / DALL-E)
    ↓ Generiert Bild
Canvas Agent
    ↓ Bild einfügen
Finale Präsentation
```

### Implementierungs-Vorbereitung

```python
async def _render_ai_image(self, element: Dict[str, Any]) -> Image.Image:
    """
    AI-Bild generieren (zukünftig)

    Aktuell: Platzhalter
    Zukunft: Integration mit Stable Diffusion / DALL-E
    """
    ai_prompt = element.get('ai_prompt', '')
    properties = element.get('properties', {})

    # TODO: Integration mit AI-Bildgenerator
    # if ai_generator_available:
    #     return await ai_generator.generate(
    #         prompt=ai_prompt,
    #         width=element['size']['width'],
    #         height=element['size']['height'],
    #         **properties
    #     )

    # Aktuell: Platzhalter
    return self._create_placeholder_image(element)
```

---

## 🚀 API-Verwendung

### 1. Präsentation generieren

**Endpoint:** `POST /api/presentations/generate`

**Request:**
```json
{
  "prompt": "Erstelle eine Präsentation über Windkraftanlagen mit 3 Folien: Titel, Übersicht, Statistik"
}
```

**Response:**
```json
{
  "success": true,
  "vdl": {
    "metadata": {...},
    "slides": [...]
  },
  "slides": [
    {
      "image_base64": "iVBORw0KGgo...",
      "png_path": "/tmp/slide_1.png",
      "slide_number": 1
    }
  ],
  "pptx_path": "/tmp/presentation_123.pptx",
  "slide_count": 3
}
```

### 2. VDL validieren

**Endpoint:** `POST /api/presentations/validate_vdl`

**Request:**
```json
{
  "vdl": {
    "slides": [
      {
        "layout": "title_slide",
        "elements": [...]
      }
    ]
  }
}
```

**Response:**
```json
{
  "is_valid": true,
  "error_message": null
}
```

### 3. VDL-Beispiel abrufen

**Endpoint:** `GET /api/presentations/vdl_example`

**Response:**
```json
{
  "metadata": {
    "title": "Beispiel-Präsentation",
    "author": "VERITAS Canvas Agent"
  },
  "slides": [...]
}
```

---

## 💻 Python-Verwendung

### Standalone

```python
from backend.agents.presentation_canvas_agent import PresentationCanvasAgent

agent = PresentationCanvasAgent()

result = await agent.generate_presentation(
    "Erstelle eine Präsentation über BImSchG mit 2 Folien"
)

if result['success']:
    print(f"Präsentation: {result['slide_count']} Folien")
    print(f"PPTX: {result['pptx_path']}")
```

### Mit LLM-Service

```python
from backend.agents.presentation_canvas_agent import PresentationCanvasAgent
from backend.services.llm_service import LLMService

llm_service = LLMService()
agent = PresentationCanvasAgent(llm_service=llm_service)

result = await agent.generate_presentation(
    "Präsentation über Umweltgenehmigungen: "
    "Titel-Slide, Prozess-Übersicht mit Flowchart, Statistik-Chart"
)
```

---

## 📐 VDL-Schema

### Vollständiges JSON-Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Visual Description Language (VDL)",
  "type": "object",
  "required": ["slides"],
  "properties": {
    "metadata": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "author": {"type": "string"},
        "theme": {"enum": ["professional", "minimal", "colorful"]}
      }
    },
    "slides": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["layout"],
        "properties": {
          "layout": {
            "enum": ["title_slide", "content", "two_column", "chart", "image", "blank"]
          },
          "elements": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["type", "position"],
              "properties": {
                "type": {
                  "enum": ["text", "shape", "chart", "image", "icon", "line", "arrow"]
                },
                "position": {
                  "type": "object",
                  "properties": {
                    "x": {"type": "integer", "minimum": 0, "maximum": 800},
                    "y": {"type": "integer", "minimum": 0, "maximum": 600}
                  }
                },
                "size": {
                  "type": "object",
                  "properties": {
                    "width": {"type": "integer"},
                    "height": {"type": "integer"}
                  }
                },
                "properties": {"type": "object"}
              }
            }
          }
        }
      }
    }
  }
}
```

---

## 🔧 Konfiguration

### Umgebungsvariablen

```bash
# LLM für VDL-Generierung
LLM_PROVIDER=ollama  # oder: vllm

# Presentation-Output-Verzeichnis
VERITAS_PRESENTATIONS_DIR=/tmp/veritas_presentations

# Canvas-Größe
CANVAS_WIDTH=800
CANVAS_HEIGHT=600

# AI-Bildgenerator (Zukunft)
AI_IMAGE_GENERATOR=stable_diffusion
AI_IMAGE_API_URL=http://localhost:7860
```

---

## 🎯 Vorteile der VDL-Architektur

### 1. LLM-Freundlich
- Strukturierte, parsbare Ausgabe
- Keine freie Bildgenerierung
- Validierbar und korrigierbar

### 2. Erweiterbar
- Neue Element-Typen einfach hinzufügbar
- AI-Bildgenerator-Integration vorbereitet
- Custom Properties möglich

### 3. Plattform-unabhängig
- JSON-Format
- Kann von verschiedenen Renderern interpretiert werden
- Export zu Canvas, PPTX, HTML, etc.

### 4. Wiederverwendbar
- VDL-Spezifikationen können gespeichert werden
- Templates basierend auf VDL
- Kollaboration möglich

---

## 📚 Beispiele

### Beispiel 1: Titel-Slide mit Logo-Bereich

```json
{
  "layout": "title_slide",
  "elements": [
    {
      "type": "text",
      "content": "VERITAS Präsentation",
      "position": {"x": 50, "y": 250},
      "size": {"width": 700, "height": 80},
      "properties": {
        "font_size": 48,
        "font_weight": "bold",
        "align": "center",
        "color": "#1f4788"
      }
    },
    {
      "type": "image",
      "ai_prompt": "Professional company logo, blue and white, minimalist",
      "position": {"x": 300, "y": 100},
      "size": {"width": 200, "height": 100},
      "properties": {
        "ai_generator": "stable_diffusion"
      }
    }
  ]
}
```

### Beispiel 2: Content-Slide mit Chart

```json
{
  "layout": "content",
  "elements": [
    {
      "type": "text",
      "content": "Anlagen-Statistik",
      "position": {"x": 50, "y": 40},
      "properties": {"font_size": 36, "font_weight": "bold"}
    },
    {
      "type": "chart",
      "chart_spec": "bimschg_overview",
      "position": {"x": 100, "y": 120},
      "size": {"width": 600, "height": 400}
    }
  ]
}
```

---

## 🔜 Roadmap

### Phase 1 (Aktuell): ✅
- VDL-Definition
- LLM-basierte VDL-Generierung
- Canvas-Rendering (PIL)
- PowerPoint-Export

### Phase 2 (In Planung):
- AI-Bildgenerator-Integration (Stable Diffusion)
- Erweiterte Layouts (3-Column, Grid)
- Animations-Unterstützung
- Interaktive HTML-Export

### Phase 3 (Zukunft):
- Kollaboratives Editing
- VDL-Template-Library
- Real-time Preview (WebSocket)
- Video-Export (MP4)

---

**Ersteller:** VERITAS Development Team
**Version:** 2.0.0
**Letzte Aktualisierung:** 3. Dezember 2025
**Status:** ✅ Implementiert und getestet
