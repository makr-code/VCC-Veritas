# PowerPoint AI Agent - Quick Reference Guide

**Version:** 1.0.0  
**Datum:** 13. Dezember 2025  
**Status:** ✅ PRODUKTIONSREIF

---

## 🚀 Schnellstart

### Frage: "Kann der PowerPoint AI Agent direkt Diagramme, SmartArt, Formen und Pfeile verwenden?"

**Antwort: JA! ✅**

Der VERITAS Presentation Canvas Agent unterstützt:
- ✅ **182+ verschiedene Formen** (Shapes)
- ✅ **29 Pfeil-Typen** (Arrows)
- ✅ **29 Flussdiagramm-Formen** (Flowchart)
- ✅ **Verbindungslinien** (Connectors)
- ✅ **Diagramm-Templates** (Organigramm, Prozessflow, Zyklus)
- ✅ **Native PowerPoint-Shapes** (editierbar in PowerPoint!)
- ⚠️ **Kein natives SmartArt** (wird aus Shapes nachgebaut)

---

## 📦 Was ist verfügbar?

### 1. Basis-Formen (8 Typen)
```
rectangle, rounded_rectangle, oval, triangle,
diamond, pentagon, hexagon, octagon
```

### 2. Pfeile (29 Typen, häufigste)
```
right_arrow, left_arrow, up_arrow, down_arrow,
left_right_arrow, circular_arrow, bent_arrow,
curved_right_arrow, curved_left_arrow
```

### 3. Flussdiagramm-Formen (29 Typen, häufigste)
```
flowchart_process       - Prozess-Rechteck
flowchart_decision      - Entscheidungs-Raute
flowchart_terminator    - Start/Ende (abgerundet)
flowchart_data          - Daten-Parallelogramm
flowchart_document      - Dokument
flowchart_database      - Datenbank (Magnetic Disk)
```

### 4. Verbindungslinien (3 Typen)
```
straight    - Gerade Linie
elbow       - 90°-Winkel (L-Form)
curve       - Geschwungene Linie
```

### 5. Diagramm-Templates (4 Typen)
```
flowchart      - Lineares Flussdiagramm
org_chart      - Hierarchisches Organigramm
cycle_diagram  - Kreisförmiges Diagramm (z.B. PDCA)
pyramid        - Pyramiden-Diagramm (in Entwicklung)
```

---

## 💡 Best Practice: Was sollte man nutzen?

### ✅ EMPFOHLEN

#### 1. Template-basierte Diagramme (am einfachsten)
```json
{
  "type": "flowchart",
  "steps": [
    {"shape": "flowchart_terminator", "text": "Start"},
    {"shape": "flowchart_process", "text": "Schritt 1"},
    {"shape": "flowchart_decision", "text": "Entscheidung?"},
    {"shape": "flowchart_terminator", "text": "Ende"}
  ]
}
```

**Warum?**
- ✅ Automatisches Layout
- ✅ Connectors werden automatisch erstellt
- ✅ Konsistente Abstände
- ✅ Weniger fehleranfällig

#### 2. Native PowerPoint-Shapes
```json
{
  "use_native_shapes": true  // ← Wichtig!
}
```

**Warum?**
- ✅ Editierbar in PowerPoint
- ✅ Nutzer kann nachträglich anpassen
- ✅ PowerPoint-Features nutzbar (Animationen, etc.)

---

### ❌ NICHT EMPFOHLEN

#### 1. Manuelle Koordinaten-Berechnung
```json
// ❌ Vermeiden:
{
  "type": "shape",
  "position": {"x": 234, "y": 567},  // Zu spezifisch!
  ...
}
```

**Warum nicht?**
- ❌ Fehleranfällig
- ❌ Schwer wartbar
- ❌ LLM kann Koordinaten schlecht berechnen

**Besser:**
```json
// ✅ Template nutzen:
{
  "type": "org_chart",
  "levels": [["CEO"], ["Manager 1", "Manager 2"]]
}
```

#### 2. SmartArt versprechen
```
// ❌ Vermeiden:
"Erstelle ein SmartArt-Organigramm"
```

**Warum nicht?**
- ❌ python-pptx unterstützt kein natives SmartArt
- ❌ Falsche Erwartungen

**Besser:**
```
// ✅ Ehrlich sein:
"Erstelle ein Organigramm aus Shapes und Connectors"
```

---

## 🎯 Anwendungsbeispiele

### Beispiel 1: BImSchG-Genehmigungsprozess

**Nutzer-Frage:**
> "Erstelle eine Präsentation über den BImSchG-Genehmigungsprozess mit einem Flussdiagramm"

**LLM generiert VDL:**
```json
{
  "use_native_shapes": true,
  "slides": [
    {
      "type": "flowchart",
      "steps": [
        {"shape": "flowchart_terminator", "text": "Antragstellung", "color": "#70ad47"},
        {"shape": "flowchart_process", "text": "Formale Prüfung", "color": "#4472c4"},
        {"shape": "flowchart_decision", "text": "Vollständig?", "color": "#ed7d31"},
        {"shape": "flowchart_process", "text": "Fachliche Prüfung", "color": "#4472c4"},
        {"shape": "flowchart_terminator", "text": "Genehmigung", "color": "#70ad47"}
      ]
    }
  ]
}
```

**Ergebnis:**
- ✅ Professionelles Flussdiagramm
- ✅ 5 Schritte mit automatischen Connectors
- ✅ Farbcodiert (grün = Start/Ende, blau = Prozess, orange = Entscheidung)
- ✅ Editierbar in PowerPoint

---

### Beispiel 2: Organigramm Umweltbehörde

**Nutzer-Frage:**
> "Zeige die Organisationsstruktur der Umweltbehörde mit 3 Ebenen"

**LLM generiert VDL:**
```json
{
  "use_native_shapes": true,
  "slides": [
    {
      "type": "org_chart",
      "levels": [
        ["Leitung Umweltbehörde"],
        ["Immissionsschutz", "Naturschutz", "Gewässerschutz"],
        ["BImSchG", "Lärm", "Flora", "Fauna", "Wasser", "Boden"]
      ]
    }
  ]
}
```

**Ergebnis:**
- ✅ Hierarchisches Organigramm
- ✅ 3 Ebenen automatisch zentriert
- ✅ Elbow-Connectors zwischen Ebenen
- ✅ Editierbar in PowerPoint

---

### Beispiel 3: PDCA-Zyklus

**Nutzer-Frage:**
> "Visualisiere den kontinuierlichen Verbesserungsprozess (PDCA)"

**LLM generiert VDL:**
```json
{
  "use_native_shapes": true,
  "slides": [
    {
      "type": "cycle_diagram",
      "steps": ["Plan", "Do", "Check", "Act"]
    }
  ]
}
```

**Ergebnis:**
- ✅ Kreisförmige Anordnung
- ✅ 4 Schritte im Uhrzeigersinn
- ✅ Visualisiert kontinuierlichen Prozess
- ✅ Editierbar in PowerPoint

---

## 🔧 Technische Details

### VDL (Visual Description Language) - Struktur

```json
{
  "metadata": {
    "title": "Präsentationstitel",
    "author": "VERITAS",
    "theme": "professional"
  },
  "use_native_shapes": true,  // Native PowerPoint-Shapes (empfohlen)
  "slides": [
    {
      "layout": "content",
      "elements": [
        {
          "type": "text" | "shape" | "connector" | "flowchart" | "org_chart" | "cycle_diagram",
          "content": "...",
          "position": {"x": int, "y": int},
          "size": {"width": int, "height": int},
          "properties": {...}
        }
      ]
    }
  ]
}
```

### Koordinaten-System

```
Canvas: 800 x 600 (Standard)
┌─────────────────────────────┐
│ (0,0)                (800,0)│
│                             │
│         Canvas              │
│                             │
│ (0,600)            (800,600)│
└─────────────────────────────┘
```

### Farb-Schema (Empfohlen)

```python
PROFESSIONAL_COLORS = {
    "primary":    "#4472c4",  # Blau
    "success":    "#70ad47",  # Grün
    "warning":    "#ed7d31",  # Orange
    "info":       "#ffc000",  # Gelb
    "neutral":    "#a5a5a5"   # Grau
}
```

---

## 📊 Vergleich: SmartArt vs. Shape-basiert

| Feature | SmartArt (Microsoft) | Shape-basiert (VERITAS) |
|---------|---------------------|-------------------------|
| Native PowerPoint | ✅ Ja | ✅ Ja (mit use_native_shapes) |
| Editierbar | ✅ Ja | ✅ Ja |
| Automatisches Layout | ✅ Ja | ✅ Ja (via Templates) |
| python-pptx Support | ❌ Nein | ✅ Ja |
| Flexibilität | ⚠️ Begrenzt | ✅ Hoch |
| Komplexität | ⚠️ Mittel | ✅ Niedrig (via Templates) |

**Fazit:** Shape-basierte Diagramme sind die **Best Practice** für VERITAS!

---

## 🎓 Entwickler-Guide

### Neues Diagramm-Template erstellen

```python
def _render_custom_diagram_template(self, draw: ImageDraw.Draw, element: Dict[str, Any]):
    """Custom Diagramm-Template"""
    data = element.get('data', [])
    pos = element.get('position', {'x': 100, 'y': 100})
    
    # Layout-Logik hier...
    for idx, item in enumerate(data):
        # Shapes rendern
        shape_element = {
            'type': 'shape',
            'shape': 'rectangle',
            'content': item['text'],
            'position': {'x': pos['x'] + idx * 150, 'y': pos['y']},
            'size': {'width': 120, 'height': 80},
            'properties': {'fill_color': '#4472c4'}
        }
        self._render_shape(draw, shape_element, ...)
```

### Tests hinzufügen

```python
@pytest.mark.asyncio
async def test_custom_diagram():
    agent = PresentationCanvasAgent()
    
    vdl = {
        "slides": [{
            "elements": [{
                "type": "custom_diagram",
                "data": [...]
            }]
        }]
    }
    
    slides = await agent._render_slides(vdl)
    assert len(slides) == 1
```

---

## ❓ FAQ

### F: Kann ich SmartArt verwenden?
**A:** Nein, python-pptx unterstützt kein natives SmartArt. Nutze stattdessen **Shape-basierte Templates** (Organigramm, Flowchart, etc.) - sie sind genauso gut!

### F: Sind die Shapes editierbar in PowerPoint?
**A:** Ja! Mit `"use_native_shapes": true` werden **native PowerPoint-Shapes** erstellt, die vollständig editierbar sind.

### F: Wie viele Shapes sind verfügbar?
**A:** **182+ verschiedene Shapes**, darunter 29 Pfeile, 29 Flussdiagramm-Formen, Basis-Formen, Sterne, Callouts, etc.

### F: Kann das LLM Koordinaten berechnen?
**A:** Theoretisch ja, aber **nicht empfohlen**. Nutze lieber **Templates** (flowchart, org_chart, cycle_diagram), die automatisches Layout bieten.

### F: Was ist der Unterschied zu Bildern?
**A:** Mit `use_native_shapes: false` werden Slides als **Bilder** exportiert (nicht editierbar). Mit `use_native_shapes: true` werden **native Shapes** erstellt (editierbar).

### F: Kann ich eigene Farben definieren?
**A:** Ja! In den `properties` jedes Elements kannst du `fill_color`, `border_color` etc. setzen (als Hex-Code).

---

## 📚 Weitere Ressourcen

- **Best Practices Dokumentation:** `docs/components/POWERPOINT_SHAPES_BEST_PRACTICES.md`
- **Code-Beispiele:** `examples/presentation_shapes_demo.py`
- **Tests:** `tests/agents/test_presentation_shapes_diagrams.py`
- **Agent-Code:** `backend/agents/presentation_canvas_agent.py`

---

## ✅ Zusammenfassung

**Kann der PowerPoint AI Agent Diagramme, SmartArt, Formen und Pfeile verwenden?**

### JA! ✅

- ✅ **182+ Shapes** (Formen, Pfeile, Flowchart, etc.)
- ✅ **Connectors** (Verbindungslinien)
- ✅ **Diagram-Templates** (Organigramm, Prozessflow, Zyklus)
- ✅ **Native PowerPoint-Shapes** (editierbar!)
- ⚠️ **Kein natives SmartArt** (aber gute Alternativen!)

### Best Practice:
1. ✅ Nutze **Template-basierte Diagramme** (einfachstes & bestes Ergebnis)
2. ✅ Setze **`use_native_shapes: true`** (editierbar in PowerPoint)
3. ✅ Lass das **LLM High-Level-Struktur** generieren (nicht Koordinaten)
4. ✅ Nutze **konsistente Farb-Schemas**

---

**Version:** 1.0.0  
**Ersteller:** VERITAS Development Team  
**Datum:** 13. Dezember 2025  
**Status:** ✅ Produktionsreif
