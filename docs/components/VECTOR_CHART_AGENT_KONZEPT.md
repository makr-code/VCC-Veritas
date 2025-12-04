# AI Agent für Vector Charts & Präsentationen - Konzept

**Erstellt:** 3. Dezember 2025  
**Version:** 1.0.0  
**Status:** 🟢 IMPLEMENTIERUNG  

---

## 📋 Übersicht

Integration eines KI-gestützten Agenten zur automatischen Erstellung von Vektor-Charts und Präsentationen ähnlich Microsoft PowerPoint, basierend auf:
- **On-Premise LLM** (Ollama/vLLM)
- **RAG-Daten** aus der VERITAS-Datenbank
- **Tkinter Canvas** für interaktive Visualisierungen
- **Best-Practice Python-Bibliotheken**

---

## 🎯 Anforderungen

### Funktional
1. **Chart-Generierung** basierend auf Nutzereingaben (Text-Prompts)
2. **Interaktive Charts** mit tkinter canvas
3. **Präsentations-Modi** (Folien-basiert)
4. **Export** zu PNG, SVG, PDF, PowerPoint (PPTX)
5. **RAG-Integration** für datenbasierte Charts
6. **Vorlagen-System** für wiederkehrende Visualisierungen

### Non-Funktional
1. **Performance**: Chart-Generierung < 5 Sekunden
2. **Qualität**: Vektorgrafiken (skalierbar)
3. **Interaktivität**: Echtzeit-Anpassungen
4. **Offline-Fähigkeit**: Kein Internet erforderlich

---

## 🛠️ Technologie-Stack

### Python-Bibliotheken (Best Practice)

#### 1. **Matplotlib** ⭐ EMPFOHLEN
- **Zweck**: Professionelle Charts und Plots
- **Vorteile**:
  - Industriestandard für wissenschaftliche Visualisierungen
  - Breite Unterstützung (Bar, Line, Scatter, Pie, etc.)
  - Export zu PNG, SVG, PDF
  - Tkinter-Integration via `FigureCanvasTkAgg`
- **Installation**: `pip install matplotlib`

```python
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

# Chart erstellen
fig, ax = plt.subplots()
ax.bar(['A', 'B', 'C'], [10, 20, 15])
ax.set_title('Sample Bar Chart')

# In Tkinter einbetten
root = tk.Tk()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack()
root.mainloop()
```

#### 2. **Plotly** ⭐ EMPFOHLEN (Interaktiv)
- **Zweck**: Interaktive, moderne Charts
- **Vorteile**:
  - HTML-basiert (für Web-Export)
  - Zoom, Pan, Hover-Effekte
  - 3D-Visualisierungen
  - Dash-Integration für Web-Apps
- **Installation**: `pip install plotly kaleido`

```python
import plotly.graph_objects as go

fig = go.Figure(data=[
    go.Bar(name='Series 1', x=['A', 'B', 'C'], y=[10, 20, 15])
])
fig.update_layout(title='Interactive Bar Chart')
fig.show()  # Öffnet im Browser
fig.write_image("chart.png")  # Export
```

#### 3. **Pillow (PIL)** 
- **Zweck**: Bildbearbeitung und Canvas-Zeichnung
- **Vorteile**:
  - Niedrig-Level Pixel/Vektor-Manipulation
  - Tkinter PhotoImage-Integration
  - Text-Rendering mit verschiedenen Fonts
- **Installation**: `pip install Pillow`

```python
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk

img = Image.new('RGB', (400, 300), 'white')
draw = ImageDraw.Draw(img)
draw.rectangle([50, 50, 350, 250], fill='lightblue', outline='black')
draw.text((100, 120), "Chart Title", fill='black')

# In Tkinter anzeigen
root = tk.Tk()
photo = ImageTk.PhotoImage(img)
label = tk.Label(root, image=photo)
label.pack()
root.mainloop()
```

#### 4. **python-pptx** ⭐ EMPFOHLEN
- **Zweck**: PowerPoint-Export
- **Vorteile**:
  - Erstellt native .pptx-Dateien
  - Charts, Tabellen, Shapes
  - Template-basiert
- **Installation**: `pip install python-pptx`

```python
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[5])  # Blank layout

# Chart hinzufügen
chart_data = CategoryChartData()
chart_data.categories = ['Q1', 'Q2', 'Q3', 'Q4']
chart_data.add_series('Sales', (10, 20, 30, 25))

x, y, cx, cy = Inches(2), Inches(2), Inches(6), Inches(4.5)
slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data
)

prs.save('presentation.pptx')
```

#### 5. **SVG Libraries**
- **svgwrite**: SVG-Dateien erstellen
- **cairosvg**: SVG → PNG/PDF Konvertierung
- **Installation**: `pip install svgwrite cairosvg`

```python
import svgwrite

dwg = svgwrite.Drawing('chart.svg', profile='tiny')
dwg.add(dwg.rect(insert=(0, 0), size=('400px', '300px'), fill='white'))
dwg.add(dwg.rect(insert=(50, 100), size=('100px', '150px'), fill='steelblue'))
dwg.add(dwg.text('Bar Chart', insert=(150, 50), font_size=24))
dwg.save()
```

#### 6. **Seaborn** (auf Matplotlib basierend)
- **Zweck**: Statistische Visualisierungen
- **Vorteile**:
  - Schönere Standard-Themes als Matplotlib
  - Heatmaps, Violin-Plots, Pairplots
- **Installation**: `pip install seaborn`

#### 7. **Bokeh**
- **Zweck**: Interaktive Visualisierungen für Web
- **Vorteile**:
  - Server-basiert (ähnlich Plotly)
  - Echtzeit-Streaming-Daten
- **Installation**: `pip install bokeh`

---

## 🏗️ Architektur

### Komponenten-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                     VERITAS Frontend (Tkinter)              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Chart Builder UI                                     │  │
│  │  - Prompt-Eingabe: "Erstelle Bar Chart für..."       │  │
│  │  - Chart-Preview (Canvas)                             │  │
│  │  - Interaktive Anpassungen (Farben, Labels, etc.)    │  │
│  │  - Export-Buttons (PNG, SVG, PDF, PPTX)              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↕ HTTP/HTTPS
┌─────────────────────────────────────────────────────────────┐
│                   VERITAS Backend (FastAPI)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Vector Chart Agent                                   │  │
│  │  1. Intent Detection (LLM)                            │  │
│  │  2. Data Extraction (RAG)                             │  │
│  │  3. Chart Generation (Matplotlib/Plotly)              │  │
│  │  4. Export Handling (python-pptx, svgwrite)           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LLM Service (Ollama/vLLM)                            │  │
│  │  - Prompt: "Extract chart type and data from query"  │  │
│  │  - Response: { type: 'bar', data: [...], labels: }   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  RAG Service (UDS3)                                   │  │
│  │  - Query: "BImSchG-Anlagen pro Kategorie"            │  │
│  │  - Result: Aggregierte Daten für Charts              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Chart-Typen

### Unterstützte Visualisierungen

1. **Bar Chart** (Balkendiagramm)
   - Vertikale/horizontale Balken
   - Gruppierte/gestapelte Balken
   - Use Cases: Vergleiche, Rankings

2. **Line Chart** (Liniendiagramm)
   - Single/Multi-Line
   - Zeitreihen
   - Use Cases: Trends, Zeitverläufe

3. **Pie Chart** (Kreisdiagramm)
   - Standard/Donut
   - Exploded Slices
   - Use Cases: Anteile, Prozentsätze

4. **Scatter Plot** (Streudiagramm)
   - Bubble-Chart-Variante
   - Use Cases: Korrelationen, Cluster

5. **Heatmap** (Wärmekarte)
   - Matrix-Visualisierung
   - Use Cases: Korrelationen, Geografie

6. **Table** (Tabelle)
   - Formatierte Datentabellen
   - Use Cases: Detaildaten, Listen

7. **Gantt Chart**
   - Projektplanung
   - Use Cases: Zeitpläne, Meilensteine

8. **Network Graph**
   - Knoten-Kanten-Diagramme
   - Use Cases: Relationen (Neo4j-Daten)

---

## 🤖 AI Agent - Vector Chart Agent

### Agent-Struktur

```python
# backend/agents/vector_chart_agent.py

from typing import Dict, Any, List
from backend.services.llm_service import LLMService
from backend.services.rag_service import RAGService
import matplotlib.pyplot as plt
import json

class VectorChartAgent:
    """
    AI Agent für automatische Chart-Generierung
    
    Pipeline:
    1. Intent Detection: Was möchte der User visualisieren?
    2. Data Extraction: Welche Daten werden benötigt?
    3. Chart Generation: Matplotlib/Plotly Chart erstellen
    4. Export: PNG, SVG, PDF, PPTX
    """
    
    def __init__(
        self, 
        llm_service: LLMService, 
        rag_service: RAGService
    ):
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.chart_templates = self._load_templates()
    
    async def generate_chart(
        self, 
        user_prompt: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Hauptmethode: Chart-Generierung aus Nutzer-Prompt
        
        Args:
            user_prompt: "Erstelle ein Bar Chart mit BImSchG-Anlagen pro Kategorie"
            context: Optional zusätzlicher Kontext
            
        Returns:
            {
                'chart_type': 'bar',
                'data': {...},
                'image_base64': '...',
                'export_formats': ['png', 'svg', 'pdf', 'pptx']
            }
        """
        # Step 1: Intent Detection
        intent = await self._detect_intent(user_prompt)
        
        # Step 2: Data Extraction
        data = await self._extract_data(intent, context)
        
        # Step 3: Chart Generation
        chart = await self._generate_chart(intent['chart_type'], data)
        
        # Step 4: Export-Vorbereitung
        exports = await self._prepare_exports(chart, intent)
        
        return {
            'chart_type': intent['chart_type'],
            'title': intent.get('title', 'Chart'),
            'data': data,
            'image_base64': exports['png_base64'],
            'svg_path': exports.get('svg_path'),
            'pdf_path': exports.get('pdf_path'),
            'pptx_path': exports.get('pptx_path')
        }
    
    async def _detect_intent(self, user_prompt: str) -> Dict[str, Any]:
        """
        Nutze LLM um Chart-Intent zu erkennen
        
        Prompt Template:
        "Analyze this request and extract:
        - chart_type (bar, line, pie, scatter, heatmap, table)
        - data_source (database query, RAG search, example data)
        - title
        - axis_labels
        - filters
        
        Request: {user_prompt}
        
        Respond in JSON format."
        """
        system_prompt = """You are a chart specification expert.
Analyze the user's request and extract chart parameters in JSON format.

Supported chart types: bar, line, pie, scatter, heatmap, table, gantt, network

Example:
User: "Erstelle ein Bar Chart mit BImSchG-Anlagen pro 4. BImSchV-Kategorie"
Response: {
  "chart_type": "bar",
  "data_source": "database",
  "query": "SELECT nr_4bv, COUNT(*) FROM BImSchG GROUP BY nr_4bv",
  "title": "BImSchG-Anlagen nach Kategorie",
  "x_label": "Kategorie (4. BImSchV)",
  "y_label": "Anzahl Anlagen",
  "filters": {}
}
"""
        
        response = await self.llm_service.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.1,  # Präzise Extraktion
            max_tokens=500
        )
        
        # Parse JSON response
        try:
            intent = json.loads(response['text'])
        except json.JSONDecodeError:
            # Fallback: Einfaches Bar Chart
            intent = {
                'chart_type': 'bar',
                'data_source': 'example',
                'title': 'Chart'
            }
        
        return intent
    
    async def _extract_data(
        self, 
        intent: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Daten aus Datenbank/RAG extrahieren
        
        Strategien:
        1. SQL Query (wenn intent['data_source'] == 'database')
        2. RAG Search (wenn intent['data_source'] == 'rag')
        3. Example Data (wenn intent['data_source'] == 'example')
        """
        data_source = intent.get('data_source', 'example')
        
        if data_source == 'database':
            # SQL-Query ausführen
            query = intent.get('query')
            data = await self._execute_sql_query(query)
        
        elif data_source == 'rag':
            # RAG-Suche
            search_query = intent.get('search_query')
            rag_results = await self.rag_service.search(search_query)
            data = self._aggregate_rag_data(rag_results, intent)
        
        else:
            # Example Data
            data = self._get_example_data(intent['chart_type'])
        
        return data
    
    async def _generate_chart(
        self, 
        chart_type: str, 
        data: Dict[str, Any]
    ) -> plt.Figure:
        """
        Matplotlib-Chart generieren
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == 'bar':
            ax.bar(data['labels'], data['values'])
            ax.set_xlabel(data.get('x_label', 'Category'))
            ax.set_ylabel(data.get('y_label', 'Value'))
        
        elif chart_type == 'line':
            ax.plot(data['x'], data['y'])
            ax.set_xlabel(data.get('x_label', 'X'))
            ax.set_ylabel(data.get('y_label', 'Y'))
        
        elif chart_type == 'pie':
            ax.pie(data['values'], labels=data['labels'], autopct='%1.1f%%')
        
        # ... weitere Chart-Typen
        
        ax.set_title(data.get('title', 'Chart'))
        plt.tight_layout()
        
        return fig
    
    async def _prepare_exports(
        self, 
        fig: plt.Figure, 
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exports vorbereiten: PNG, SVG, PDF, PPTX
        """
        import base64
        from io import BytesIO
        
        exports = {}
        
        # PNG (Base64 für Frontend)
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150)
        buf.seek(0)
        png_base64 = base64.b64encode(buf.read()).decode('utf-8')
        exports['png_base64'] = png_base64
        
        # SVG
        svg_path = f"/tmp/chart_{intent.get('title', 'chart')}.svg"
        fig.savefig(svg_path, format='svg')
        exports['svg_path'] = svg_path
        
        # PDF
        pdf_path = f"/tmp/chart_{intent.get('title', 'chart')}.pdf"
        fig.savefig(pdf_path, format='pdf')
        exports['pdf_path'] = pdf_path
        
        # PPTX (via python-pptx)
        pptx_path = await self._create_pptx(fig, intent)
        exports['pptx_path'] = pptx_path
        
        return exports
    
    async def _create_pptx(
        self, 
        fig: plt.Figure, 
        intent: Dict[str, Any]
    ) -> str:
        """
        PowerPoint-Präsentation erstellen
        """
        from pptx import Presentation
        from pptx.util import Inches
        from io import BytesIO
        
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # Blank
        
        # Chart als Bild einfügen
        img_buf = BytesIO()
        fig.savefig(img_buf, format='png', dpi=150)
        img_buf.seek(0)
        
        left = Inches(1)
        top = Inches(1.5)
        width = Inches(8)
        slide.shapes.add_picture(img_buf, left, top, width=width)
        
        # Titel hinzufügen
        title_box = slide.shapes.title
        title_box.text = intent.get('title', 'Chart')
        
        pptx_path = f"/tmp/presentation_{intent.get('title', 'chart')}.pptx"
        prs.save(pptx_path)
        
        return pptx_path
    
    def _load_templates(self) -> Dict[str, Any]:
        """
        Vordefinierte Chart-Templates laden
        """
        return {
            'bimschg_overview': {
                'chart_type': 'bar',
                'query': 'SELECT nr_4bv, COUNT(*) FROM BImSchG GROUP BY nr_4bv',
                'title': 'BImSchG-Anlagen nach Kategorie',
                'x_label': '4. BImSchV Nummer',
                'y_label': 'Anzahl Anlagen'
            },
            'wka_leistung': {
                'chart_type': 'pie',
                'query': 'SELECT status, SUM(leistung) FROM WKA GROUP BY status',
                'title': 'WKA-Leistung nach Status',
            }
        }
    
    async def _execute_sql_query(self, query: str) -> Dict[str, Any]:
        """SQL-Query ausführen und als Chart-Daten formatieren"""
        # TODO: Integration mit UDS3-Datenbank
        pass
    
    def _aggregate_rag_data(
        self, 
        rag_results: List[Dict], 
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """RAG-Ergebnisse zu Chart-Daten aggregieren"""
        # TODO: Implementierung
        pass
    
    def _get_example_data(self, chart_type: str) -> Dict[str, Any]:
        """Beispiel-Daten für Demo-Charts"""
        examples = {
            'bar': {
                'labels': ['A', 'B', 'C', 'D'],
                'values': [10, 25, 15, 30],
                'title': 'Sample Bar Chart',
                'x_label': 'Categories',
                'y_label': 'Values'
            },
            'line': {
                'x': [1, 2, 3, 4, 5],
                'y': [10, 15, 13, 20, 25],
                'title': 'Sample Line Chart',
                'x_label': 'Time',
                'y_label': 'Value'
            },
            'pie': {
                'labels': ['Category A', 'Category B', 'Category C'],
                'values': [30, 45, 25],
                'title': 'Sample Pie Chart'
            }
        }
        return examples.get(chart_type, examples['bar'])
```

---

## 🎨 Frontend-Integration (Tkinter)

### Chart Builder UI

```python
# frontend/ui/chart_builder.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import base64
from io import BytesIO
from PIL import Image, ImageTk

class ChartBuilderWindow:
    """
    Tkinter-Fenster für interaktive Chart-Erstellung
    """
    
    def __init__(self, parent, api_client):
        self.window = tk.Toplevel(parent)
        self.window.title("VERITAS - Vector Chart Builder")
        self.window.geometry("1200x800")
        
        self.api_client = api_client
        self.current_chart = None
        
        self._create_ui()
    
    def _create_ui(self):
        """UI-Elemente erstellen"""
        
        # Hauptcontainer (2 Spalten)
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Linke Spalte: Eingabe & Optionen
        left_frame = ttk.Frame(main_frame, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        # Rechte Spalte: Chart-Preview
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # --- Linke Spalte ---
        
        # Prompt-Eingabe
        ttk.Label(left_frame, text="Chart-Beschreibung:", font=("Arial", 12, "bold")).pack(anchor='w', pady=(0, 5))
        
        prompt_frame = ttk.Frame(left_frame)
        prompt_frame.pack(fill=tk.BOTH, pady=(0, 10))
        
        self.prompt_text = tk.Text(prompt_frame, height=6, wrap=tk.WORD, font=("Arial", 10))
        self.prompt_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        prompt_scroll = ttk.Scrollbar(prompt_frame, command=self.prompt_text.yview)
        prompt_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.prompt_text.config(yscrollcommand=prompt_scroll.set)
        
        # Placeholder
        placeholder = "Beispiele:\n- Erstelle ein Bar Chart mit BImSchG-Anlagen pro Kategorie\n- Zeige Liniendiagramm der WKA-Leistung über Zeit\n- Pie Chart: Verteilung der Anlagentypen"
        self.prompt_text.insert('1.0', placeholder)
        self.prompt_text.config(fg='gray')
        
        # Generieren-Button
        generate_btn = ttk.Button(
            left_frame, 
            text="🎨 Chart Generieren", 
            command=self._generate_chart
        )
        generate_btn.pack(fill=tk.X, pady=(0, 20))
        
        # Vorlagen-Auswahl
        ttk.Label(left_frame, text="Vorlagen:", font=("Arial", 11, "bold")).pack(anchor='w', pady=(0, 5))
        
        templates = [
            "BImSchG-Übersicht",
            "WKA-Leistung",
            "Anlagenverteilung",
            "Zeitreihe Genehmigungen"
        ]
        
        for template in templates:
            btn = ttk.Button(
                left_frame, 
                text=template, 
                command=lambda t=template: self._load_template(t)
            )
            btn.pack(fill=tk.X, pady=2)
        
        # Export-Optionen
        ttk.Separator(left_frame, orient='horizontal').pack(fill=tk.X, pady=20)
        ttk.Label(left_frame, text="Export:", font=("Arial", 11, "bold")).pack(anchor='w', pady=(0, 5))
        
        export_frame = ttk.Frame(left_frame)
        export_frame.pack(fill=tk.X)
        
        ttk.Button(export_frame, text="💾 PNG", command=lambda: self._export('png')).pack(side=tk.LEFT, padx=2)
        ttk.Button(export_frame, text="📄 SVG", command=lambda: self._export('svg')).pack(side=tk.LEFT, padx=2)
        ttk.Button(export_frame, text="📕 PDF", command=lambda: self._export('pdf')).pack(side=tk.LEFT, padx=2)
        ttk.Button(export_frame, text="📊 PPTX", command=lambda: self._export('pptx')).pack(side=tk.LEFT, padx=2)
        
        # --- Rechte Spalte ---
        
        ttk.Label(right_frame, text="Vorschau:", font=("Arial", 12, "bold")).pack(anchor='w', pady=(0, 5))
        
        # Canvas für Chart-Anzeige
        self.canvas_frame = ttk.Frame(right_frame, relief=tk.SUNKEN, borderwidth=2)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder
        placeholder_label = ttk.Label(
            self.canvas_frame, 
            text="Chart wird hier angezeigt...\n\nGeben Sie eine Beschreibung ein und klicken Sie auf 'Generieren'",
            font=("Arial", 12),
            foreground='gray'
        )
        placeholder_label.pack(expand=True)
    
    async def _generate_chart(self):
        """Chart generieren via Backend-API"""
        prompt = self.prompt_text.get('1.0', tk.END).strip()
        
        if not prompt or prompt == "Beispiele:...":
            messagebox.showwarning("Eingabe fehlt", "Bitte geben Sie eine Chart-Beschreibung ein.")
            return
        
        # Loading-Indikator
        self._show_loading()
        
        try:
            # API-Call
            response = await self.api_client.post(
                '/api/charts/generate',
                json={'prompt': prompt}
            )
            
            chart_data = response.json()
            self.current_chart = chart_data
            
            # Chart anzeigen
            self._display_chart(chart_data)
        
        except Exception as e:
            messagebox.showerror("Fehler", f"Chart-Generierung fehlgeschlagen:\n{e}")
        
        finally:
            self._hide_loading()
    
    def _display_chart(self, chart_data):
        """Chart im Canvas anzeigen"""
        # Clear canvas
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        
        # Decode Base64 image
        img_data = base64.b64decode(chart_data['image_base64'])
        img = Image.open(BytesIO(img_data))
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(img)
        
        # Display
        label = tk.Label(self.canvas_frame, image=photo)
        label.image = photo  # Keep reference
        label.pack(expand=True)
    
    def _load_template(self, template_name):
        """Vorlage laden"""
        templates = {
            "BImSchG-Übersicht": "Erstelle ein Bar Chart mit BImSchG-Anlagen gruppiert nach 4. BImSchV-Nummer",
            "WKA-Leistung": "Zeige ein Pie Chart der WKA-Gesamtleistung aufgeteilt nach Status",
            "Anlagenverteilung": "Erstelle eine Heatmap der BImSchG-Anlagen in Brandenburg",
            "Zeitreihe Genehmigungen": "Liniendiagramm: Anzahl Genehmigungen pro Jahr (2010-2024)"
        }
        
        prompt = templates.get(template_name, "")
        self.prompt_text.delete('1.0', tk.END)
        self.prompt_text.insert('1.0', prompt)
        self.prompt_text.config(fg='black')
    
    def _export(self, format_type):
        """Chart exportieren"""
        if not self.current_chart:
            messagebox.showwarning("Kein Chart", "Bitte generieren Sie zuerst ein Chart.")
            return
        
        # Datei-Dialog
        filetypes = {
            'png': [("PNG Image", "*.png")],
            'svg': [("SVG Vector", "*.svg")],
            'pdf': [("PDF Document", "*.pdf")],
            'pptx': [("PowerPoint", "*.pptx")]
        }
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}",
            filetypes=filetypes[format_type]
        )
        
        if filepath:
            # Download von Server
            file_path_key = f"{format_type}_path"
            server_path = self.current_chart.get(file_path_key)
            
            if server_path:
                # Copy file from server temp path
                import shutil
                shutil.copy(server_path, filepath)
                messagebox.showinfo("Export erfolgreich", f"Chart gespeichert als:\n{filepath}")
            else:
                messagebox.showerror("Fehler", f"{format_type.upper()}-Export nicht verfügbar.")
    
    def _show_loading(self):
        """Loading-Indikator anzeigen"""
        # TODO: Implementierung
        pass
    
    def _hide_loading(self):
        """Loading-Indikator verstecken"""
        # TODO: Implementierung
        pass
```

---

## 📁 Dateistruktur

```
veritas/
├── backend/
│   ├── agents/
│   │   └── vector_chart_agent.py          # 🆕 Chart-Agent
│   ├── api/
│   │   └── chart_endpoints.py             # 🆕 Chart-API
│   └── services/
│       └── chart_service.py               # 🆕 Chart-Service
├── frontend/
│   └── ui/
│       └── chart_builder.py               # 🆕 Chart-Builder-UI
├── docs/
│   ├── VECTOR_CHART_AGENT_KONZEPT.md      # 🆕 Dieses Dokument
│   └── CHART_TEMPLATES.md                 # 🆕 Vorlagen-Dokumentation
└── requirements.txt                        # 🆕 Neue Dependencies
```

---

## 🚀 Implementierungsplan

### Phase 1: Backend (4-6h)
- [ ] `vector_chart_agent.py` implementieren
- [ ] `chart_endpoints.py` erstellen (FastAPI)
- [ ] LLM-Prompts für Intent Detection optimieren
- [ ] Matplotlib/Plotly-Integration
- [ ] Export-Handler (PNG, SVG, PDF, PPTX)

### Phase 2: Frontend (4-6h)
- [ ] `chart_builder.py` UI erstellen
- [ ] Canvas-Integration
- [ ] Template-System
- [ ] Export-Funktionalität

### Phase 3: RAG-Integration (2-4h)
- [ ] UDS3-Datenbank-Queries
- [ ] Data Aggregation
- [ ] Caching

### Phase 4: Testing & Optimierung (2-3h)
- [ ] Unit-Tests
- [ ] Integration-Tests
- [ ] Performance-Optimierung
- [ ] Dokumentation

---

## 📦 Neue Dependencies

```txt
# requirements.txt (Ergänzungen)

# Chart-Generierung
matplotlib>=3.8.0
plotly>=5.18.0
seaborn>=0.13.0
kaleido>=0.2.1  # Plotly-Export

# PowerPoint-Export
python-pptx>=0.6.23

# Vektor-Grafiken
svgwrite>=1.4.3
cairosvg>=2.7.1

# Bildverarbeitung (bereits vorhanden)
Pillow>=10.1.0
```

---

## 📊 Beispiel-Anwendungsfälle

### 1. BImSchG-Anlagen-Übersicht

**User-Prompt:**  
"Erstelle ein Bar Chart mit der Anzahl der BImSchG-Anlagen pro 4. BImSchV-Kategorie"

**Agent-Workflow:**
1. Intent: `{chart_type: 'bar', data_source: 'database'}`
2. Query: `SELECT nr_4bv, COUNT(*) FROM BImSchG GROUP BY nr_4bv`
3. Chart: Matplotlib Bar Chart
4. Export: PNG, SVG, PDF, PPTX

### 2. WKA-Leistung nach Status

**User-Prompt:**  
"Zeige ein Pie Chart der WKA-Leistung aufgeteilt nach Status"

**Agent-Workflow:**
1. Intent: `{chart_type: 'pie', data_source: 'database'}`
2. Query: `SELECT status, SUM(leistung) FROM WKA GROUP BY status`
3. Chart: Matplotlib Pie Chart
4. Export: PPTX mit Legende

### 3. Zeitreihe Genehmigungen

**User-Prompt:**  
"Liniendiagramm: Anzahl Genehmigungen pro Jahr (2010-2024)"

**Agent-Workflow:**
1. Intent: `{chart_type: 'line', data_source: 'database'}`
2. Query: `SELECT YEAR(datum), COUNT(*) FROM BImSchG WHERE YEAR(datum) BETWEEN 2010 AND 2024 GROUP BY YEAR(datum)`
3. Chart: Matplotlib Line Chart mit Trendlinie
4. Export: PDF-Report

---

## 🔒 Sicherheit & Best Practices

1. **SQL-Injection-Schutz**: Parametrisierte Queries
2. **LLM-Prompt-Injection**: Input-Sanitization
3. **File-Upload-Limits**: Max 50 MB pro Chart
4. **Caching**: Redis für generierte Charts
5. **Rate-Limiting**: Max 10 Charts pro Minute

---

## 📚 Referenzen

- **Matplotlib**: https://matplotlib.org/
- **Plotly**: https://plotly.com/python/
- **python-pptx**: https://python-pptx.readthedocs.io/
- **svgwrite**: https://svgwrite.readthedocs.io/

---

**Ersteller:** VERITAS Development Team  
**Version:** 1.0.0  
**Letzte Aktualisierung:** 3. Dezember 2025
