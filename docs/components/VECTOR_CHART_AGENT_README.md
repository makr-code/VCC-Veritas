# Vector Chart Agent - AI-gestützte Chart-Generierung 📊

## Übersicht

Der **Vector Chart Agent** ist ein KI-gestütztes System zur automatischen Generierung von professionellen Charts und Präsentationen in VERITAS. Er kombiniert:

- 🤖 **On-Premise LLM** (Ollama/vLLM) für Intent-Erkennung
- 📊 **RAG-Daten** aus der VERITAS-Datenbank
- 🎨 **Tkinter Canvas** für interaktive Visualisierungen
- 📈 **Matplotlib & Seaborn** für hochwertige Charts
- 💾 **Multi-Format-Export** (PNG, SVG, PDF, PowerPoint)

## Features

### Unterstützte Chart-Typen

- **Bar Chart** (Balkendiagramm) - Vergleiche und Rankings
- **Line Chart** (Liniendiagramm) - Zeitreihen und Trends
- **Pie Chart** (Kreisdiagramm) - Prozentuale Anteile
- **Scatter Plot** (Streudiagramm) - Korrelationen
- **Heatmap** (Wärmekarte) - Matrix-Visualisierungen

### Export-Formate

- **PNG** - Hochauflösende Rastergrafik (150 DPI)
- **SVG** - Vektorgrafik (skalierbar)
- **PDF** - Dokumentenformat
- **PPTX** - Microsoft PowerPoint-Präsentation

### Vorlagen-System

4 vordefinierte Templates für häufige Anwendungsfälle:

1. **BImSchG-Übersicht** - Bar Chart der Anlagen nach Kategorie
2. **WKA-Leistung** - Pie Chart der Windkraftanlagen nach Status
3. **Anlagenverteilung** - Pie Chart der Anlagentypen
4. **Zeitreihe Genehmigungen** - Line Chart der Genehmigungen pro Jahr

## Installation

### Dependencies installieren

```bash
pip install -r requirements.txt
```

Neue Dependencies (automatisch installiert):
- matplotlib>=3.8.0
- seaborn>=0.13.0
- plotly>=5.18.0
- python-pptx>=0.6.23
- svgwrite>=1.4.3
- Pillow>=10.1.0

### Backend-Integration

Die Chart-API wird automatisch beim Start des Backends geladen:

```bash
python start_backend.py
```

Der Chart-Service ist verfügbar unter: `http://localhost:5000/api/charts`

## Verwendung

### 1. Via Frontend UI (empfohlen)

**Öffnen des Chart Builders:**

```python
# In VERITAS-App:
Tools > Chart Builder
# Oder Keyboard-Shortcut: Ctrl+Shift+C
```

**Workflow:**

1. **Template auswählen** oder eigenen Prompt eingeben
2. **"Chart Generieren"** klicken
3. **Vorschau** im Canvas betrachten
4. **Export** in gewünschtem Format (PNG, SVG, PDF, PPTX)

### 2. Via API (programmatisch)

**Endpoint:** `POST /api/charts/generate`

**Request:**
```json
{
  "prompt": "Erstelle ein Bar Chart mit BImSchG-Anlagen pro Kategorie",
  "template": "bimschg_overview"
}
```

**Response:**
```json
{
  "success": true,
  "chart_type": "bar",
  "title": "BImSchG-Anlagen nach Kategorie",
  "data": {
    "labels": ["1.1 Feuerung", "1.2 Gasturbine", ...],
    "values": [850, 520, ...]
  },
  "image_base64": "iVBORw0KGgo...",
  "exports": {
    "png": "/tmp/veritas_charts/chart_123.png",
    "svg": "/tmp/veritas_charts/chart_123.svg",
    "pdf": "/tmp/veritas_charts/chart_123.pdf",
    "pptx": "/tmp/veritas_charts/chart_123.pptx"
  }
}
```

### 3. Via Python (standalone)

```python
from backend.agents.vector_chart_agent import VectorChartAgent

agent = VectorChartAgent()

# Chart generieren
result = await agent.generate_chart(
    "Erstelle ein Bar Chart",
    template='bimschg_overview'
)

if result['success']:
    print(f"Chart erstellt: {result['exports']['png']}")
```

## API-Endpoints

### `POST /api/charts/generate`
Chart generieren aus Nutzer-Prompt

**Parameter:**
- `prompt` (string, required) - Chart-Beschreibung
- `template` (string, optional) - Template-Name
- `context` (object, optional) - Zusätzlicher Kontext

### `GET /api/charts/templates`
Liste aller verfügbaren Templates

**Response:**
```json
[
  {
    "name": "bimschg_overview",
    "title": "BImSchG-Anlagen nach Kategorie",
    "type": "bar"
  }
]
```

### `GET /api/charts/download/{filename}?format=png`
Chart-Datei herunterladen

**Parameter:**
- `filename` (string) - Dateiname (ohne Extension)
- `format` (string) - png | svg | pdf | pptx

### `GET /api/charts/health`
Health-Check für Chart-Service

## Beispiele

### Beispiel 1: Bar Chart mit Template

```python
result = await agent.generate_chart(
    "Zeige Anlagenübersicht",
    template='bimschg_overview'
)
```

**Generiert:**
- Bar Chart mit BImSchG-Anlagen gruppiert nach 4. BImSchV-Nummer
- Beispieldaten: 5 Kategorien mit jeweils 340-1200 Anlagen
- Export: PNG, SVG, PDF, PPTX

### Beispiel 2: Line Chart (Zeitreihe)

```python
result = await agent.generate_chart(
    "Liniendiagramm: Genehmigungen 2010-2024",
    template='zeitreihe_genehmigungen'
)
```

**Generiert:**
- Line Chart mit Zeitreihen-Daten
- X-Achse: Jahre 2010-2024
- Y-Achse: Anzahl Genehmigungen
- Trend-Visualisierung

### Beispiel 3: Pie Chart (WKA-Status)

```python
result = await agent.generate_chart(
    "Pie Chart der WKA-Leistung",
    template='wka_leistung'
)
```

**Generiert:**
- Pie Chart mit 4 Segmenten
- In Betrieb, Im Genehmigungsverfahren, Stillgelegt, Im Bau
- Prozentuale Anteile mit Labels

### Beispiel 4: Custom Prompt (ohne Template)

```python
result = await agent.generate_chart(
    "Erstelle ein Scatter Plot: Leistung vs. Nabenhöhe für WKA"
)
```

**Nutzt:**
- LLM für Intent-Erkennung → Chart-Typ: scatter
- Fallback auf Beispieldaten (da keine DB-Connection)
- Generiert Scatter Plot mit 10 Datenpunkten

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Tkinter)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Chart Builder UI (frontend/ui/chart_builder.py)     │  │
│  │  - Prompt-Eingabe                                     │  │
│  │  - Template-Auswahl                                   │  │
│  │  - Canvas-Preview                                     │  │
│  │  - Export-Buttons                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↕ HTTP
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Chart API (backend/api/chart_endpoints.py)          │  │
│  │  - POST /api/charts/generate                         │  │
│  │  - GET /api/charts/templates                         │  │
│  │  - GET /api/charts/download/{filename}               │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↕                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Vector Chart Agent                                   │  │
│  │  (backend/agents/vector_chart_agent.py)              │  │
│  │                                                        │  │
│  │  1. Intent Detection (LLM)                            │  │
│  │  2. Data Extraction (RAG/DB)                          │  │
│  │  3. Chart Generation (Matplotlib)                     │  │
│  │  4. Export (PNG, SVG, PDF, PPTX)                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Testing

### Standalone Agent Test

```bash
python test_vector_chart_agent.py
```

**Tests:**
1. ✅ VectorChartAgent (standalone) - 5 Tests
2. ✅ Backend API Endpoints - 3 Tests
3. ✅ Frontend UI (manuell)

### Ergebnis der Tests

```
✅ VectorChartAgent-Tests abgeschlossen
   - Bar Chart: ✅
   - Pie Chart: ✅
   - Line Chart: ✅
   - Fallback: ✅
   - Templates: ✅ 4 verfügbar
```

**Generierte Dateien:**
```
/tmp/veritas_charts/
├── bimschg-anlagen_nach_kategorie_*.png  (54 KB)
├── bimschg-anlagen_nach_kategorie_*.svg  (43 KB)
├── bimschg-anlagen_nach_kategorie_*.pdf  (22 KB)
├── bimschg-anlagen_nach_kategorie_*.pptx (69 KB)
├── wka-leistung_nach_status_*.png        (52 KB)
├── wka-leistung_nach_status_*.svg        (29 KB)
└── ...
```

### Unit Tests

```bash
python -m pytest backend/agents/test_vector_chart_agent.py
```

## Konfiguration

### Umgebungsvariablen

```bash
# LLM-Provider (optional, für Intent Detection)
LLM_PROVIDER=ollama  # oder: vllm

# Chart-Output-Verzeichnis
VERITAS_CHARTS_DIR=/tmp/veritas_charts

# Log-Level
VERITAS_LOG_LEVEL=INFO
```

### Chart-Styling (anpassbar)

```python
# In vector_chart_agent.py:

# Seaborn-Theme
sns.set_theme(style="whitegrid")  # Optionen: darkgrid, white, dark, ticks

# Matplotlib-Parameter
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11
```

## Best Practices

### 1. Prompt-Formulierung

**Gut:**
- "Erstelle ein Bar Chart mit BImSchG-Anlagen pro Kategorie"
- "Zeige Liniendiagramm der Genehmigungen 2010-2024"
- "Pie Chart: WKA-Leistung nach Status"

**Vermeiden:**
- Zu allgemein: "Zeige Daten"
- Zu komplex: "Erstelle einen interaktiven 3D-Chart mit 50 Variablen"

### 2. Template-Nutzung

Für wiederkehrende Charts → Template verwenden:
```python
result = await agent.generate_chart(
    "...",  # Prompt kann kurz sein
    template='bimschg_overview'  # Template überschreibt Intent
)
```

### 3. Export-Format-Wahl

- **PNG** - Für Web, Präsentationen (schnell, gute Qualität)
- **SVG** - Für Druck, Vektorgrafiken (skalierbar)
- **PDF** - Für Dokumentation, Archivierung
- **PPTX** - Für PowerPoint-Präsentationen (editierbar)

### 4. Performance

- Templates nutzen (schneller als LLM-Intent-Detection)
- Caching für häufig generierte Charts
- Batch-Generierung für multiple Charts

## Troubleshooting

### Problem: "LLM-Service nicht verfügbar"

**Ursache:** LLM-Service (Ollama/vLLM) nicht gestartet

**Lösung:**
- Fallback wird automatisch genutzt (Keyword-basiert)
- Für LLM-Intent: Backend mit LLM starten

### Problem: "PPTX-Export fehlgeschlagen"

**Ursache:** python-pptx nicht installiert

**Lösung:**
```bash
pip install python-pptx
```

### Problem: "Chart-Anzeige im Frontend fehlgeschlagen"

**Ursache:** PIL/Pillow nicht verfügbar

**Lösung:**
```bash
pip install Pillow
```

### Problem: "Backend nicht erreichbar"

**Ursache:** Backend nicht gestartet

**Lösung:**
```bash
python start_backend.py
# Warte auf: ✅ Chart API Router mounted at /api/charts
```

## Weiterentwicklung

### Geplante Features (Roadmap)

1. **RAG-Integration** - Echte Daten aus UDS3-Datenbank
2. **SQL-Query-Generator** - Automatische Query-Erstellung via LLM
3. **Interaktive Charts** - Plotly-basierte Web-Charts
4. **Custom Styles** - Theme-Unterstützung (Corporate Design)
5. **Batch-Export** - Multiple Charts auf einmal
6. **Chart-Templates-Editor** - UI zum Erstellen eigener Templates

### Erweiterungsmöglichkeiten

```python
# Neue Chart-Typen hinzufügen:

def _generate_chart(self, chart_type, data, intent):
    # ... existing types ...

    elif chart_type == 'gantt':
        # Gantt-Chart für Projektplanung
        pass

    elif chart_type == 'network':
        # Network-Graph für Neo4j-Daten
        pass
```

## Lizenz & Credits

**Entwickelt für:** VERITAS - Verwaltungs-Informations- und Recherche-System

**Technologie-Stack:**
- FastAPI (Backend-Framework)
- Matplotlib & Seaborn (Chart-Generierung)
- python-pptx (PowerPoint-Export)
- Tkinter (Frontend-UI)
- Ollama/vLLM (LLM für Intent Detection)

**Version:** 1.0.0
**Datum:** 3. Dezember 2025

---

## Quick Reference

```bash
# Backend starten
python start_backend.py

# Frontend starten
python start_frontend.py

# Tests ausführen
python test_vector_chart_agent.py

# Chart Builder öffnen
# In VERITAS-App: Tools > Chart Builder (Ctrl+Shift+C)

# API-Dokumentation
http://localhost:5000/docs#/Charts

# Generierte Charts
ls -lh /tmp/veritas_charts/
```

**Happy Charting! 📊**
