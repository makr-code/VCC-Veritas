# PowerPoint Shapes, Diagramme, SmartArt - Best Practices für VERITAS

**Erstellt:** 13. Dezember 2025  
**Version:** 1.0.0  
**Status:** 🟢 DOKUMENTIERT

---

## 📋 Übersicht

Dieses Dokument beschreibt die **Best Practices** für die Verwendung von **Diagrammen, Formen, Pfeilen und SmartArt-ähnlichen Visualisierungen** im VERITAS Presentation Canvas Agent unter Verwendung der **python-pptx** Bibliothek.

### Wichtige Erkenntnisse

✅ **Was python-pptx KANN:**
- **182+ verschiedene Formen** (Shapes) direkt unterstützt
- **29 Pfeil-Typen** für verschiedene Visualisierungen
- **29 Flussdiagramm-Formen** für Prozessdarstellungen
- **Connectors** (Verbindungslinien) zwischen Shapes
- **Gruppierung** von Shapes
- **Umfangreiche Formatierung** (Farben, Rahmen, Schatten, etc.)

❌ **Was python-pptx NICHT KANN:**
- **Kein natives SmartArt** - SmartArt ist eine proprietäre Microsoft-Funktion
- SmartArt muss als **Kombination von Shapes nachgebaut** werden

---

## 🎯 Best Practice: Shape-basierte Diagramme statt SmartArt

### Strategie

Da python-pptx **kein natives SmartArt** unterstützt, empfehlen wir:

1. **Deklarative Beschreibung**: Nutzer beschreibt das gewünschte Diagramm in natürlicher Sprache
2. **LLM-basierte Interpretation**: LLM interpretiert die Anfrage und erzeugt VDL (Visual Description Language)
3. **Shape-Komposition**: Der Presentation Canvas Agent erstellt das Diagramm aus **Einzelformen und Connectors**
4. **Template-basiert**: Häufige Diagramm-Typen als wiederverwendbare Templates

### Beispiel-Workflow

```
Nutzer: "Erstelle ein Organigramm mit 3 Ebenen"
    ↓
LLM: Generiert VDL mit Rechtecken und Verbindungslinien
    ↓
Canvas Agent: Rendert Shapes, Pfeile und Connectors
    ↓
PPTX: Präsentation mit shape-basiertem "Organigramm"
```

---

## 🔧 Verfügbare Shape-Kategorien

### 1. Basis-Formen (8)
```python
from pptx.enum.shapes import MSO_SHAPE

BASIC_SHAPES = [
    MSO_SHAPE.RECTANGLE,
    MSO_SHAPE.ROUNDED_RECTANGLE,
    MSO_SHAPE.OVAL,
    MSO_SHAPE.TRIANGLE,
    MSO_SHAPE.DIAMOND,
    MSO_SHAPE.PENTAGON,
    MSO_SHAPE.HEXAGON,
    MSO_SHAPE.OCTAGON,
]
```

**Verwendung:**
- Organigramme (Rechtecke)
- Entscheidungsbäume (Diamanten)
- Prozessschritte (Abgerundete Rechtecke)

### 2. Pfeile (29 Typen)
```python
ARROW_SHAPES = [
    MSO_SHAPE.RIGHT_ARROW,          # Standard-Pfeil
    MSO_SHAPE.LEFT_RIGHT_ARROW,     # Bidirektionaler Pfeil
    MSO_SHAPE.BENT_ARROW,           # Gebogener Pfeil
    MSO_SHAPE.CURVED_RIGHT_ARROW,   # Geschwungener Pfeil
    MSO_SHAPE.CIRCULAR_ARROW,       # Kreisförmiger Pfeil
    MSO_SHAPE.BLOCK_ARC,            # Block-Pfeil
    MSO_SHAPE.STRIPED_RIGHT_ARROW,  # Gestreifter Pfeil
    # ... 22 weitere
]
```

**Verwendung:**
- Prozessflüsse
- Datenflüsse
- Zeitlinien
- Ursache-Wirkung-Diagramme

### 3. Flussdiagramm-Shapes (29 Typen)
```python
FLOWCHART_SHAPES = [
    MSO_SHAPE.FLOWCHART_PROCESS,        # Prozess (Rechteck)
    MSO_SHAPE.FLOWCHART_DECISION,       # Entscheidung (Raute)
    MSO_SHAPE.FLOWCHART_TERMINATOR,     # Start/Ende (Abgerundet)
    MSO_SHAPE.FLOWCHART_DATA,           # Daten (Parallelogramm)
    MSO_SHAPE.FLOWCHART_DOCUMENT,       # Dokument
    MSO_SHAPE.FLOWCHART_MANUAL_INPUT,   # Manuelle Eingabe
    MSO_SHAPE.FLOWCHART_DATABASE,       # Datenbank
    # ... 22 weitere
]
```

**Verwendung:**
- Prozessdiagramme
- Workflow-Visualisierungen
- Algorithmus-Darstellungen

### 4. Connectors (Verbindungslinien)
```python
from pptx.enum.shapes import MSO_CONNECTOR

CONNECTOR_TYPES = [
    MSO_CONNECTOR.STRAIGHT,  # Gerade Linie
    MSO_CONNECTOR.ELBOW,     # Abgewinkelt (90°-Winkel)
    MSO_CONNECTOR.CURVE,     # Geschwungen
]
```

**Verwendung:**
- Verbindungen zwischen Shapes
- Beziehungen visualisieren
- Organigramm-Hierarchien

### 5. Sterne und Callouts
```python
# Sterne (11 Typen)
STAR_SHAPES = [
    MSO_SHAPE.STAR_5_POINT,
    MSO_SHAPE.STAR_6_POINT,
    # ...
]

# Callouts/Sprechblasen (20 Typen)
CALLOUT_SHAPES = [
    MSO_SHAPE.CLOUD_CALLOUT,
    MSO_SHAPE.LINE_CALLOUT_1,
    MSO_SHAPE.OVAL_CALLOUT,
    # ...
]
```

**Verwendung:**
- Kommentare und Anmerkungen
- Hervorhebungen
- Erklärungen

---

## 💡 Diagramm-Templates (SmartArt-Alternativen)

### Template 1: Organigramm

**Beschreibung:** Hierarchische Struktur mit 3 Ebenen

**VDL-Konzept:**
```json
{
  "diagram_type": "organization_chart",
  "levels": 3,
  "elements": [
    {
      "type": "shape",
      "shape": "rectangle",
      "level": 1,
      "position": {"x": 300, "y": 50},
      "text": "CEO"
    },
    {
      "type": "connector",
      "connector_type": "elbow",
      "from": "CEO",
      "to": "Manager 1"
    }
  ]
}
```

**Python-Implementierung:**
```python
def create_org_chart(slide, levels_data):
    """
    Erstellt ein Organigramm aus Rechtecken und Connectors
    
    levels_data: [
        ["CEO"],
        ["Manager 1", "Manager 2"],
        ["Team A", "Team B", "Team C"]
    ]
    """
    y_spacing = 120
    x_spacing = 150
    
    for level_idx, level in enumerate(levels_data):
        y_pos = 50 + level_idx * y_spacing
        total_width = len(level) * x_spacing
        start_x = (800 - total_width) / 2  # Zentriert
        
        for node_idx, node_text in enumerate(level):
            x_pos = start_x + node_idx * x_spacing
            
            # Shape erstellen
            shape = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(x_pos / 100),
                Inches(y_pos / 100),
                Inches(1.2),
                Inches(0.6)
            )
            shape.text = node_text
            shape.fill.solid()
            shape.fill.fore_color.rgb = RGBColor(68, 114, 196)
            
            # Connector zur vorherigen Ebene (falls nicht Level 1)
            if level_idx > 0:
                parent_idx = node_idx // 2  # Simplified parent
                connector = slide.shapes.add_connector(
                    MSO_CONNECTOR.ELBOW,
                    Inches((start_x + parent_idx * x_spacing + 60) / 100),
                    Inches((y_pos - y_spacing + 60) / 100),
                    Inches((x_pos + 60) / 100),
                    Inches(y_pos / 100)
                )
                connector.line.width = Pt(1.5)
```

### Template 2: Prozessdiagramm (Linear Flow)

**VDL-Konzept:**
```json
{
  "diagram_type": "process_flow",
  "steps": [
    {
      "type": "flowchart_terminator",
      "text": "Start"
    },
    {
      "type": "flowchart_process",
      "text": "Schritt 1"
    },
    {
      "type": "flowchart_decision",
      "text": "Entscheidung?"
    },
    {
      "type": "flowchart_terminator",
      "text": "Ende"
    }
  ]
}
```

**Python-Implementierung:**
```python
def create_process_flow(slide, steps):
    """
    Erstellt ein lineares Prozessdiagramm
    
    steps: [
        {"type": "start", "text": "Start"},
        {"type": "process", "text": "Schritt 1"},
        {"type": "decision", "text": "Prüfung"},
        {"type": "end", "text": "Ende"}
    ]
    """
    shape_map = {
        "start": MSO_SHAPE.FLOWCHART_TERMINATOR,
        "end": MSO_SHAPE.FLOWCHART_TERMINATOR,
        "process": MSO_SHAPE.FLOWCHART_PROCESS,
        "decision": MSO_SHAPE.FLOWCHART_DECISION,
        "data": MSO_SHAPE.FLOWCHART_DATA,
    }
    
    y_spacing = 100
    start_y = 100
    x_pos = 300
    
    prev_shape = None
    
    for idx, step in enumerate(steps):
        y_pos = start_y + idx * y_spacing
        
        # Shape erstellen
        shape_type = shape_map.get(step["type"], MSO_SHAPE.RECTANGLE)
        shape = slide.shapes.add_shape(
            shape_type,
            Inches(x_pos / 100),
            Inches(y_pos / 100),
            Inches(1.5),
            Inches(0.8)
        )
        shape.text = step["text"]
        shape.fill.solid()
        
        # Farbe basierend auf Typ
        if step["type"] in ["start", "end"]:
            shape.fill.fore_color.rgb = RGBColor(112, 173, 71)
        elif step["type"] == "decision":
            shape.fill.fore_color.rgb = RGBColor(237, 125, 49)
        else:
            shape.fill.fore_color.rgb = RGBColor(68, 114, 196)
        
        # Connector vom vorherigen Schritt
        if prev_shape is not None:
            connector = slide.shapes.add_connector(
                MSO_CONNECTOR.STRAIGHT,
                Inches((x_pos + 75) / 100),
                Inches((y_pos - 20) / 100),
                Inches((x_pos + 75) / 100),
                Inches(y_pos / 100)
            )
            connector.line.width = Pt(2)
            # Arrow-Ende
            connector.line.end_arrow_type = 2  # Arrow
        
        prev_shape = shape
```

### Template 3: Zyklisches Diagramm

**VDL-Konzept:**
```json
{
  "diagram_type": "cycle",
  "steps": ["Planung", "Durchführung", "Kontrolle", "Anpassung"]
}
```

**Python-Implementierung:**
```python
import math

def create_cycle_diagram(slide, steps):
    """
    Erstellt ein zyklisches Diagramm (kreisförmig)
    
    steps: ["Schritt 1", "Schritt 2", "Schritt 3", "Schritt 4"]
    """
    center_x = 400
    center_y = 300
    radius = 150
    n = len(steps)
    
    shapes_list = []
    
    for idx, step_text in enumerate(steps):
        # Berechne Position auf dem Kreis
        angle = (2 * math.pi * idx / n) - (math.pi / 2)  # Start oben
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        # Shape erstellen
        shape = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            Inches((x - 50) / 100),
            Inches((y - 50) / 100),
            Inches(1),
            Inches(1)
        )
        shape.text = step_text
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(68, 114, 196)
        
        shapes_list.append((x, y))
    
    # Pfeile zwischen den Schritten
    for idx in range(n):
        next_idx = (idx + 1) % n
        
        # Gebogener Pfeil
        connector = slide.shapes.add_connector(
            MSO_CONNECTOR.CURVE,
            Inches(shapes_list[idx][0] / 100),
            Inches(shapes_list[idx][1] / 100),
            Inches(shapes_list[next_idx][0] / 100),
            Inches(shapes_list[next_idx][1] / 100)
        )
        connector.line.width = Pt(2)
        connector.line.end_arrow_type = 2
```

### Template 4: Pyramid/Hierarchie-Diagramm

**Python-Implementierung:**
```python
def create_pyramid_diagram(slide, levels):
    """
    Erstellt ein Pyramiden-Diagramm
    
    levels: [
        "Top (CEO)",
        "Middle (Manager)",
        "Base (Mitarbeiter)"
    ]
    """
    n_levels = len(levels)
    base_width = 600
    height = 400
    
    for idx, level_text in enumerate(levels):
        # Breite nimmt nach unten zu
        level_width = base_width * (idx + 1) / n_levels
        level_height = height / n_levels
        
        x = (800 - level_width) / 2
        y = 50 + idx * level_height
        
        # Trapez oder Rechteck
        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(x / 100),
            Inches(y / 100),
            Inches(level_width / 100),
            Inches((level_height - 10) / 100)
        )
        shape.text = level_text
        shape.fill.solid()
        
        # Farbe wird heller nach unten
        base_color = 68 + idx * 40
        shape.fill.fore_color.rgb = RGBColor(base_color, 114, 196)
```

---

## 🚀 Integration in PresentationCanvasAgent

### Erweiterte VDL-Elemente

```python
class VisualDescriptionLanguage:
    ELEMENT_TYPES = [
        'text', 
        'shape', 
        'chart', 
        'image', 
        'icon', 
        'line', 
        'arrow',
        'connector',      # NEU
        'flowchart',      # NEU
        'org_chart',      # NEU (Template)
        'process_flow',   # NEU (Template)
        'cycle_diagram',  # NEU (Template)
        'pyramid',        # NEU (Template)
    ]
    
    SHAPE_TYPES = [
        'rectangle', 'rounded_rectangle', 'oval', 'triangle',
        'diamond', 'pentagon', 'hexagon', 'octagon',
        
        # Pfeile
        'right_arrow', 'left_arrow', 'up_arrow', 'down_arrow',
        'left_right_arrow', 'circular_arrow', 'bent_arrow',
        
        # Flussdiagramm
        'flowchart_process', 'flowchart_decision', 'flowchart_terminator',
        'flowchart_data', 'flowchart_document', 'flowchart_database',
        
        # ... weitere 150+ Shapes
    ]
    
    CONNECTOR_TYPES = [
        'straight',
        'elbow',
        'curve'
    ]
```

### Beispiel VDL mit Shapes und Connectors

```json
{
  "metadata": {
    "title": "BImSchG-Genehmigungsprozess",
    "theme": "professional"
  },
  "slides": [
    {
      "layout": "content",
      "elements": [
        {
          "type": "text",
          "content": "Genehmigungsprozess Übersicht",
          "position": {"x": 50, "y": 30},
          "properties": {"font_size": 32}
        },
        {
          "type": "flowchart",
          "flowchart_type": "process_flow",
          "steps": [
            {
              "shape": "flowchart_terminator",
              "text": "Antragstellung",
              "color": "#70ad47"
            },
            {
              "shape": "flowchart_process",
              "text": "Formale Prüfung",
              "color": "#4472c4"
            },
            {
              "shape": "flowchart_decision",
              "text": "Vollständig?",
              "color": "#ed7d31"
            },
            {
              "shape": "flowchart_process",
              "text": "Fachliche Prüfung",
              "color": "#4472c4"
            },
            {
              "shape": "flowchart_terminator",
              "text": "Genehmigung",
              "color": "#70ad47"
            }
          ],
          "position": {"x": 100, "y": 100}
        }
      ]
    },
    {
      "layout": "content",
      "elements": [
        {
          "type": "text",
          "content": "Organisationsstruktur",
          "position": {"x": 50, "y": 30},
          "properties": {"font_size": 32}
        },
        {
          "type": "org_chart",
          "levels": [
            ["Geschäftsführung"],
            ["Umweltabteilung", "Bauabteilung"],
            ["Team A", "Team B", "Team C"]
          ],
          "position": {"x": 100, "y": 100}
        }
      ]
    },
    {
      "layout": "content",
      "elements": [
        {
          "type": "text",
          "content": "Kontinuierlicher Verbesserungsprozess",
          "position": {"x": 50, "y": 30},
          "properties": {"font_size": 32}
        },
        {
          "type": "cycle_diagram",
          "steps": ["Plan", "Do", "Check", "Act"],
          "position": {"x": 200, "y": 150},
          "style": {
            "color_scheme": "blue"
          }
        }
      ]
    }
  ]
}
```

---

## 📚 Best Practices Zusammenfassung

### 1. **Nutze Templates für häufige Diagramm-Typen**

Anstatt jedes Mal einzelne Shapes zu positionieren:
- Definiere wiederverwendbare Templates (Organigramm, Prozessflow, etc.)
- Nutze parametrisierte Funktionen
- Speichere Templates als VDL-Dateien

### 2. **LLM generiert High-Level-Struktur**

Das LLM sollte **nicht** einzelne Shape-Koordinaten berechnen, sondern:
```
❌ Falsch: {"type": "shape", "position": {"x": 234, "y": 567}, ...}
✅ Richtig: {"type": "org_chart", "levels": [...]}
```

### 3. **Smart Defaults für Layout**

Der Canvas Agent sollte automatisch:
- Abstände berechnen
- Shapes zentrieren
- Connectors optimieren
- Überlappungen vermeiden

### 4. **Connector-Strategie**

Für Verbindungen zwischen Shapes:
- `STRAIGHT`: Einfache, direkte Verbindungen
- `ELBOW`: Hierarchische Strukturen (Organigramme)
- `CURVE`: Zyklische Diagramme, Feedback-Loops

### 5. **Farb-Schemas**

Definiere konsistente Farb-Paletten:
```python
COLOR_SCHEMES = {
    "professional": {
        "primary": RGBColor(68, 114, 196),
        "secondary": RGBColor(112, 173, 71),
        "accent": RGBColor(237, 125, 49),
        "neutral": RGBColor(166, 166, 166)
    },
    "environmental": {
        "primary": RGBColor(39, 119, 40),
        "secondary": RGBColor(76, 175, 80),
        "accent": RGBColor(255, 193, 7),
        "neutral": RGBColor(158, 158, 158)
    }
}
```

### 6. **Text-Formatierung in Shapes**

```python
shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
shape.text_frame.paragraphs[0].font.size = Pt(14)
shape.text_frame.paragraphs[0].font.bold = True
shape.text_frame.word_wrap = True
```

### 7. **Gruppierung komplexer Diagramme**

Für komplexe Diagramme, die aus mehreren Shapes bestehen:
```python
# Shapes zur Gruppe hinzufügen
group = slide.shapes.add_group_shape()
# Shapes zum Group hinzufügen (erfordert zusätzliche Logik)
```

### 8. **Fehlerbehandlung und Validierung**

```python
def validate_diagram_spec(diagram_spec):
    """Validiert Diagramm-Spezifikation vor dem Rendern"""
    required = ['diagram_type', 'elements']
    for key in required:
        if key not in diagram_spec:
            raise ValueError(f"Missing required key: {key}")
    
    # Prüfe auf gültige Positionen
    if 'position' in diagram_spec:
        if not (0 <= diagram_spec['position']['x'] <= 800):
            raise ValueError("X position out of bounds")
```

---

## 🔮 Zukünftige Erweiterungen

### Phase 2: Erweiterte Diagramm-Templates
- Matrix-Diagramme (2x2, 3x3)
- Venn-Diagramme
- Timeline-Diagramme
- SWOT-Analyse
- Gantt-Charts (vereinfacht)

### Phase 3: Interaktive Elemente
- Hyperlinks zwischen Slides
- Hover-Effekte (für HTML-Export)
- Animationen (begrenzt in PPTX)

### Phase 4: SmartArt-Nachbau
- Vollständiger SmartArt-Emulator
- Automatisches Layout-Engine
- Style-Templates für alle SmartArt-Kategorien

---

## 📖 Beispiel-Prompts für Nutzer

### Beispiel 1: Organigramm
```
Prompt: "Erstelle ein Organigramm mit 3 Ebenen: 
         CEO oben, 2 Manager in der Mitte, 4 Teams unten"

→ LLM generiert: org_chart mit levels: [["CEO"], ["Manager 1", "Manager 2"], ...]
→ Canvas Agent erstellt: Rechtecke + Elbow-Connectors
```

### Beispiel 2: Prozessdiagramm
```
Prompt: "Zeige den BImSchG-Genehmigungsprozess mit 5 Schritten: 
         Antrag → Prüfung → Entscheidung → Auflagen → Genehmigung"

→ LLM generiert: process_flow mit steps: [{type: "start", ...}, ...]
→ Canvas Agent erstellt: Flowchart-Shapes + Straight-Connectors
```

### Beispiel 3: Zyklus
```
Prompt: "Visualisiere den PDCA-Zyklus (Plan-Do-Check-Act)"

→ LLM generiert: cycle_diagram mit steps: ["Plan", "Do", "Check", "Act"]
→ Canvas Agent erstellt: Kreisförmige Anordnung + Curved-Connectors
```

---

## ⚠️ Limitierungen

### 1. Kein natives SmartArt
- SmartArt ist Microsoft-proprietär
- Muss aus Shapes nachgebaut werden
- PowerPoint kann diese nicht als SmartArt bearbeiten

### 2. Layout-Komplexität
- Automatisches Layout ist rechenintensiv
- Komplexe Verschachtelungen schwierig
- Trade-off: Einfachheit vs. Flexibilität

### 3. Connector-Routing
- Keine automatische Kollisionsvermeidung
- Manuelle Positionierung erforderlich
- Oder vereinfachte Layouts verwenden

---

## 🎓 Fazit

**Empfohlene Strategie:**
1. ✅ **Nutze python-pptx für Shapes, Pfeile, Diagramme**
2. ✅ **Definiere Template-basierte Diagramme** (Organigramm, Prozessflow, etc.)
3. ✅ **LLM generiert High-Level-VDL** (nicht Low-Level-Koordinaten)
4. ✅ **Canvas Agent übernimmt Layout-Logik** (Smart Defaults)
5. ❌ **Vermeide SmartArt-Versprechen** (Klarheit über Limitierungen)

**Best Practice = Shape-Komposition + Templates + LLM-Interpretation**

---

**Ersteller:** VERITAS Development Team  
**Letzte Aktualisierung:** 13. Dezember 2025  
**Version:** 1.0.0  
**Status:** ✅ Produktionsreif
