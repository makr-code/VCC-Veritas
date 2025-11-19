# VCC-Veritas Visual Query Builder - Konzept

## Version 1.0
**Datum**: 19. November 2025  
**Status**: Konzept für Implementierung

---

## 1. Executive Summary

Der **Visual Query Builder** (VQB) ist eine neue Python/tkinter-basierte Frontend-Komponente für VCC-Veritas, die Prozesse aus dem VPB (Verwaltungspraxis der Bundesbehörden) mit unterschiedlichen Dokumententypen (relational, graph, vector, file) visuell verbindet. Die Anwendung nutzt eine horizontale Zeitschiene ähnlich einem Gantt-Diagramm zur Prozessdarstellung und bietet AI-gestützte Filter- und Sortiermechanismen.

### Kernfunktionen
- **Prozessvisualisierung**: Timeline/Gantt-View für VPB-Prozesse
- **Dokumenten-Verknüpfung**: Multi-modale Beziehungen (Graph, Vector, Relational)
- **AI-gestützte Navigation**: Intelligente Filter, Sortierung, Empfehlungen
- **Multi-Datenbank-Integration**: UDS3, Neo4j, PostgreSQL, ChromaDB
- **Interaktive Exploration**: Drill-down, Zoom, Pan, Suchfunktionen

---

## 2. Architektur-Übersicht

### 2.1 System-Kontext

```
┌─────────────────────────────────────────────────────────────┐
│                Visual Query Builder (VQB)                    │
│                    (Python/tkinter)                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Timeline    │  │  Document    │  │  AI Filter   │     │
│  │  View        │  │  Graph View  │  │  Panel       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Process     │  │  Metadata    │  │  Search      │     │
│  │  Details     │  │  Inspector   │  │  Interface   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTP/REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            VERITAS Backend (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  VPB Router  │  │  UDS3        │  │  Intelligent │     │
│  │  (Processes) │  │  (Multi-DB)  │  │  Pipeline    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Layer                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Neo4j    │  │PostgreSQL│  │ChromaDB  │  │  Files   │   │
│  │ (Graph)  │  │(Relation)│  │ (Vector) │  │  (Docs)  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Frontend-Architektur (MVC Pattern)

```
vqb_frontend/
├── app.py                      # Main Application Entry Point
├── models/                     # Data Models
│   ├── __init__.py
│   ├── process_model.py        # Process/Timeline Data
│   ├── document_model.py       # Document Metadata
│   ├── relationship_model.py   # Graph Relationships
│   └── filter_model.py         # Filter/Search Criteria
├── views/                      # UI Components (tkinter)
│   ├── __init__.py
│   ├── main_window.py          # Main Application Window
│   ├── timeline_view.py        # Gantt/Timeline Widget
│   ├── graph_view.py           # Relationship Graph Widget
│   ├── document_panel.py       # Document List/Details
│   ├── filter_panel.py         # AI Filter Interface
│   ├── search_bar.py           # Search Component
│   └── dialogs/                # Modal Dialogs
│       ├── process_detail_dialog.py
│       ├── document_detail_dialog.py
│       └── settings_dialog.py
├── controllers/                # Business Logic
│   ├── __init__.py
│   ├── timeline_controller.py  # Timeline Logic
│   ├── document_controller.py  # Document Operations
│   ├── search_controller.py    # Search/Filter Logic
│   └── api_controller.py       # Backend API Communication
├── services/                   # Background Services
│   ├── __init__.py
│   ├── api_client.py           # REST API Client
│   ├── data_cache.py           # Local Data Cache
│   ├── async_worker.py         # Threading/Queue Manager
│   └── ai_service.py           # AI Filter/Recommendation Service
├── utils/                      # Utilities
│   ├── __init__.py
│   ├── layout_manager.py       # Layout Helpers
│   ├── color_scheme.py         # Theming/Colors
│   ├── validators.py           # Input Validation
│   └── formatters.py           # Data Formatting
└── config/                     # Configuration
    ├── __init__.py
    ├── app_config.py           # App Settings
    └── api_config.py           # API Endpoints
```

---

## 3. Hauptkomponenten

### 3.1 Timeline View (Gantt-ähnliche Darstellung)

**Zweck**: Visualisierung von VPB-Prozessen auf einer horizontalen Zeitschiene

**Features**:
- Prozessschritte als horizontale Balken
- Zeitskala (anpassbar: Tage, Wochen, Monate)
- Abhängigkeiten zwischen Prozessschritten (Pfeile)
- Zoom und Pan (Mausrad, Drag)
- Farbcodierung nach Status (geplant, in Bearbeitung, abgeschlossen)
- Tooltips mit Prozessdetails
- Klick-Events für Drill-down

**Technische Umsetzung**:
```python
class TimelineView(tk.Canvas):
    """
    Gantt-ähnliche Timeline-Darstellung für Prozesse
    
    Features:
    - Canvas-basierte Zeichnung
    - Zoom/Pan mit Maus-Events
    - Event-Handling für Interaktivität
    - Observer Pattern für Updates
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.zoom_level = 1.0
        self.offset_x = 0
        self.processes = []
        
        # Event Bindings
        self.bind("<Button-1>", self.on_process_click)
        self.bind("<MouseWheel>", self.on_zoom)
        self.bind("<B1-Motion>", self.on_pan)
        
    def render_processes(self, processes):
        """Zeichne alle Prozesse auf der Timeline"""
        self.delete("all")  # Clear canvas
        for process in processes:
            self._draw_process_bar(process)
            self._draw_dependencies(process)
    
    def _draw_process_bar(self, process):
        """Zeichne einen einzelnen Prozess-Balken"""
        # Calculate position based on time
        x1 = self._time_to_x(process.start_time)
        x2 = self._time_to_x(process.end_time)
        y = self._get_y_position(process.level)
        
        # Draw bar with color based on status
        color = self._get_status_color(process.status)
        self.create_rectangle(x1, y, x2, y + 30, 
                             fill=color, tags=f"process_{process.id}")
        self.create_text((x1 + x2) / 2, y + 15, 
                        text=process.title, tags=f"process_{process.id}")
```

### 3.2 Document Graph View

**Zweck**: Visualisierung der Beziehungen zwischen Dokumenten und Prozessen

**Features**:
- Netzwerk-Graph (Nodes = Dokumente/Prozesse, Edges = Beziehungen)
- Beziehungstypen: 
  - Graph (Neo4j): Strukturelle Verbindungen
  - Vector (ChromaDB): Semantische Ähnlichkeit
  - Relational (PostgreSQL): Foreign Keys
- Force-directed Layout oder hierarchisches Layout
- Filter nach Beziehungstyp
- Highlighting von Pfaden
- Zoom und Pan

**Technische Umsetzung**:
```python
class GraphView(tk.Canvas):
    """
    Netzwerk-Graph für Dokument-Beziehungen
    
    Nutzt Force-Directed Layout für automatische Anordnung
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.nodes = {}
        self.edges = []
        self.layout_engine = ForceDirectedLayout()
        
    def render_graph(self, nodes, edges):
        """Zeichne Graph mit automatischem Layout"""
        self.delete("all")
        
        # Calculate positions using layout engine
        positions = self.layout_engine.calculate(nodes, edges)
        
        # Draw edges first (behind nodes)
        for edge in edges:
            self._draw_edge(edge, positions)
        
        # Draw nodes
        for node in nodes:
            self._draw_node(node, positions[node.id])
    
    def _draw_node(self, node, position):
        """Zeichne einen Node (Kreis mit Label)"""
        x, y = position
        radius = 20
        
        # Color by type
        color = self._get_node_color(node.type)
        
        # Draw circle
        self.create_oval(x - radius, y - radius, 
                        x + radius, y + radius,
                        fill=color, tags=f"node_{node.id}")
        
        # Draw label
        self.create_text(x, y + radius + 10, 
                        text=node.label, tags=f"node_{node.id}")
```

### 3.3 AI Filter Panel

**Zweck**: Intelligente Filter- und Sortierfunktionen mit AI-Unterstützung

**Features**:
- Natural Language Queries ("Zeige mir alle offenen Genehmigungsverfahren")
- Vordefinierte Filter-Templates
- Multi-Kriterien-Filter (UND/ODER-Verknüpfung)
- AI-Empfehlungen basierend auf Kontext
- Gespeicherte Filter-Profile
- Echtzeitvorschau der Filter-Ergebnisse

**Technische Umsetzung**:
```python
class FilterPanel(tk.Frame):
    """
    AI-gestütztes Filter-Interface
    
    Kommuniziert mit Backend AI für intelligente Filterung
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Natural Language Input
        self.nl_entry = tk.Entry(self, width=50)
        self.nl_entry.pack()
        
        # Filter Template Buttons
        self.template_frame = tk.Frame(self)
        self.template_frame.pack()
        self._create_filter_templates()
        
        # Active Filters Display
        self.active_filters = tk.Listbox(self)
        self.active_filters.pack()
        
    def on_natural_language_search(self, query):
        """
        Sende Natural Language Query an Backend
        Backend übersetzt zu strukturierten Filtern
        """
        # Async call to backend
        self.controller.async_nl_search(
            query, 
            callback=self.apply_filters
        )
```

### 3.4 Process Detail Dialog

**Zweck**: Detaillierte Ansicht eines ausgewählten Prozesses

**Features**:
- Prozess-Metadaten (Titel, Beschreibung, Status, Dauer)
- Verknüpfte Dokumente (Liste mit Thumbnails)
- Prozessschritte (Hierarchie)
- Verantwortliche/Beteiligte
- Historische Änderungen
- Aktionen (Bearbeiten, Exportieren)

---

## 4. OOP Design Patterns

### 4.1 Model-View-Controller (MVC)

**Separation of Concerns**:
- **Models**: Daten und Geschäftslogik
- **Views**: UI-Komponenten (tkinter Widgets)
- **Controllers**: Vermittler zwischen Model und View

### 4.2 Observer Pattern

**Use Case**: Model-Updates propagieren zu Views

```python
class Observable:
    """Base class for Observable objects"""
    
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        self._observers.append(observer)
    
    def detach(self, observer):
        self._observers.remove(observer)
    
    def notify(self, *args, **kwargs):
        for observer in self._observers:
            observer.update(*args, **kwargs)

class ProcessModel(Observable):
    """Model mit Observer-Support"""
    
    def __init__(self):
        super().__init__()
        self._processes = []
    
    def add_process(self, process):
        self._processes.append(process)
        self.notify(event="process_added", process=process)
    
    def update_process(self, process_id, data):
        # Update logic
        self.notify(event="process_updated", process_id=process_id)

class TimelineView(tk.Canvas):
    """View als Observer"""
    
    def __init__(self, parent, model):
        super().__init__(parent)
        self.model = model
        self.model.attach(self)  # Subscribe to model updates
    
    def update(self, event, **kwargs):
        """Observer callback"""
        if event == "process_added":
            self.render_processes(self.model.get_all())
        elif event == "process_updated":
            self.refresh()
```

### 4.3 Singleton Pattern

**Use Case**: Globale Services (API Client, Cache)

```python
class APIClient:
    """Singleton API Client"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
```

### 4.4 Factory Pattern

**Use Case**: Erstellung verschiedener View-Typen

```python
class ViewFactory:
    """Factory für View-Komponenten"""
    
    @staticmethod
    def create_view(view_type, parent, controller):
        if view_type == "timeline":
            return TimelineView(parent, controller)
        elif view_type == "graph":
            return GraphView(parent, controller)
        elif view_type == "document":
            return DocumentPanel(parent, controller)
        else:
            raise ValueError(f"Unknown view type: {view_type}")
```

---

## 5. Threading und Queue-Management

### 5.1 Async Worker Pattern

**Zweck**: Nicht-blockierende Backend-Kommunikation

```python
import threading
from queue import Queue

class AsyncWorker:
    """
    Managed asynchronous tasks in background threads
    
    Features:
    - Thread pool for concurrent tasks
    - Task queue with priority
    - Callback mechanism for results
    - Error handling and retry logic
    """
    
    def __init__(self, num_threads=4):
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.threads = []
        
        # Start worker threads
        for i in range(num_threads):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.threads.append(t)
    
    def _worker(self):
        """Worker thread loop"""
        while True:
            task = self.task_queue.get()
            try:
                result = task.execute()
                self.result_queue.put(("success", task.id, result))
            except Exception as e:
                self.result_queue.put(("error", task.id, str(e)))
            finally:
                self.task_queue.task_done()
    
    def submit_task(self, task, callback=None):
        """Submit task for async execution"""
        task.callback = callback
        self.task_queue.put(task)
    
    def process_results(self):
        """
        Process results from result queue
        Called periodically from main thread (after callback)
        """
        while not self.result_queue.empty():
            status, task_id, result = self.result_queue.get()
            # Handle result (call callback)
```

### 5.2 Periodic UI Updates

**Pattern**: Tkinter `after()` für Queue-Processing

```python
class Application(tk.Tk):
    """Main Application mit Async Support"""
    
    def __init__(self):
        super().__init__()
        self.worker = AsyncWorker(num_threads=4)
        
        # Start periodic result processing
        self._process_async_results()
    
    def _process_async_results(self):
        """
        Periodically check for async results
        Runs in main thread (safe for UI updates)
        """
        self.worker.process_results()
        
        # Schedule next check (100ms)
        self.after(100, self._process_async_results)
    
    def load_processes_async(self):
        """Example: Load processes in background"""
        task = LoadProcessesTask()
        task.callback = self.on_processes_loaded
        self.worker.submit_task(task)
    
    def on_processes_loaded(self, processes):
        """Callback (runs in main thread)"""
        self.timeline_view.render_processes(processes)
```

---

## 6. Integration mit VCC-Teilsystemen

### 6.1 VPB Integration

**Endpoint**: `/api/v3/vpb/query`

**Datenfluss**:
1. VQB sendet Prozess-Query an Backend
2. Backend nutzt VPB Router
3. VPB Router liefert Prozess-Daten und Dokumente
4. VQB visualisiert auf Timeline

**Beispiel API Call**:
```python
class VPBController:
    """Controller für VPB-Integration"""
    
    def __init__(self):
        self.api_client = APIClient()
    
    async def load_vpb_processes(self, filters=None):
        """Load processes from VPB backend"""
        response = await self.api_client.post(
            "/api/v3/vpb/query",
            json={
                "query": "Alle Genehmigungsverfahren",
                "filters": filters or {},
                "session_id": self.session_id
            }
        )
        
        # Parse response
        processes = self._parse_vpb_response(response)
        return processes
    
    def _parse_vpb_response(self, response):
        """Convert VPB response to Process models"""
        processes = []
        for doc in response.get("documents", []):
            process = ProcessModel(
                id=doc["document_id"],
                title=doc["title"],
                authority=doc["authority"],
                year=doc["year"],
                # ... more fields
            )
            processes.append(process)
        return processes
```

### 6.2 UDS3 Multi-DB Integration

**UDS3 Strategien**:
- **Graph (Neo4j)**: Prozess-Abhängigkeiten, Dokument-Relationen
- **Vector (ChromaDB)**: Semantische Ähnlichkeitssuche
- **Relational (PostgreSQL)**: Strukturierte Metadaten
- **File (Filesystem)**: Dokument-Inhalte

**Graph Query Beispiel**:
```python
class DocumentController:
    """Controller für Dokument-Operationen"""
    
    async def get_related_documents(self, process_id, relation_type="all"):
        """
        Hole verwandte Dokumente für einen Prozess
        
        relation_type: "graph", "vector", "relational", "all"
        """
        response = await self.api_client.get(
            f"/api/v3/documents/related/{process_id}",
            params={"relation_type": relation_type}
        )
        
        documents = []
        for doc_data in response.get("documents", []):
            doc = DocumentModel(
                id=doc_data["id"],
                title=doc_data["title"],
                type=doc_data["type"],
                relationships=doc_data.get("relationships", [])
            )
            documents.append(doc)
        
        return documents
```

### 6.3 AI Service Integration

**Intelligent Pipeline Integration**:

```python
class AIService:
    """AI-gestützte Features"""
    
    def __init__(self):
        self.api_client = APIClient()
    
    async def natural_language_filter(self, nl_query):
        """
        Übersetze Natural Language in strukturierte Filter
        
        Beispiel: "Zeige offene Verfahren aus 2024"
        -> {"status": "open", "year": 2024}
        """
        response = await self.api_client.post(
            "/api/v3/ai/parse_filter",
            json={"query": nl_query}
        )
        
        return response.get("filters", {})
    
    async def recommend_documents(self, process_id):
        """
        AI-Empfehlungen für relevante Dokumente
        
        Nutzt Vector Search und Graph Analysis
        """
        response = await self.api_client.get(
            f"/api/v3/ai/recommend/{process_id}"
        )
        
        return response.get("recommendations", [])
```

---

## 7. UI/UX Design

### 7.1 Layout-Konzept

```
┌─────────────────────────────────────────────────────────────┐
│  Menu: File | Edit | View | Tools | Help           [X] [-] │
├─────────────────────────────────────────────────────────────┤
│  🔍 Search: [_____________________________] [Filter] [AI]   │
├─────────┬───────────────────────────────────────────────────┤
│         │                                                   │
│ Filter  │         Timeline View (Gantt)                     │
│ Panel   │   ┌────────────────────────────────────────┐     │
│         │   │ [Process A    ████████████]            │     │
│ [ ] All │   │ [Process B       ██████████████]       │     │
│ [x] 2024│   │ [Process C  ███████]                   │     │
│ [ ] Open│   │                                        │     │
│         │   └────────────────────────────────────────┘     │
│ Presets:│                                                   │
│ - Aktiv │   Document/Graph View (Tabs)                      │
│ - Neues │   ┌─[Documents]─┬─[Graph]─┬─[Details]────┐     │
│         │   │                                        │     │
│ AI      │   │  📄 Doc 1  [Graph Network]   Metadata │     │
│ Suggest:│   │  📄 Doc 2   (Interactive)    Details  │     │
│ - Genehm│   │  📄 Doc 3                             │     │
│         │   └────────────────────────────────────────┘     │
└─────────┴───────────────────────────────────────────────────┘
│  Status: 15 Processes | 42 Documents | Connected to Backend│
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Farbschema

```python
# config/color_scheme.py

class ColorScheme:
    """Zentrales Farbschema für VQB"""
    
    # Primary Colors
    PRIMARY_BLUE = "#0066CC"
    PRIMARY_DARK = "#003366"
    PRIMARY_LIGHT = "#6699FF"
    
    # Status Colors
    STATUS_OPEN = "#FFA500"      # Orange
    STATUS_IN_PROGRESS = "#4169E1"  # Royal Blue
    STATUS_COMPLETED = "#32CD32"    # Lime Green
    STATUS_BLOCKED = "#DC143C"      # Crimson
    
    # Relationship Colors
    REL_GRAPH = "#9370DB"        # Medium Purple (Graph)
    REL_VECTOR = "#FF6347"       # Tomato (Vector)
    REL_RELATIONAL = "#4682B4"   # Steel Blue (Relational)
    REL_FILE = "#DAA520"         # Goldenrod (File)
    
    # UI Elements
    BACKGROUND = "#F5F5F5"       # White Smoke
    PANEL_BG = "#FFFFFF"         # White
    BORDER = "#CCCCCC"           # Light Gray
    TEXT_PRIMARY = "#333333"     # Dark Gray
    TEXT_SECONDARY = "#666666"   # Medium Gray
```

### 7.3 Responsive Layout

**Grid-basiertes Layout mit tkinter.Grid**:

```python
class MainWindow(tk.Tk):
    """Hauptfenster mit responsivem Layout"""
    
    def __init__(self):
        super().__init__()
        
        # Configure grid weights für responsive Verhalten
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Menu Bar (Row 0)
        self.menu_bar = self._create_menu_bar()
        self.config(menu=self.menu_bar)
        
        # Search Bar (Row 1)
        self.search_frame = SearchBar(self)
        self.search_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        # Filter Panel (Column 0, Row 2)
        self.filter_panel = FilterPanel(self)
        self.filter_panel.grid(row=1, column=0, sticky="nsw", padx=5, pady=5)
        
        # Main Content (Column 1, Row 2)
        self.content_paned = tk.PanedWindow(self, orient=tk.VERTICAL)
        self.content_paned.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Timeline View (Top Pane)
        self.timeline_view = TimelineView(self.content_paned)
        self.content_paned.add(self.timeline_view, minsize=200)
        
        # Document/Graph Tabbed View (Bottom Pane)
        self.tabbed_view = tk.ttk.Notebook(self.content_paned)
        self.document_panel = DocumentPanel(self.tabbed_view)
        self.graph_view = GraphView(self.tabbed_view)
        self.tabbed_view.add(self.document_panel, text="Documents")
        self.tabbed_view.add(self.graph_view, text="Graph")
        self.content_paned.add(self.tabbed_view, minsize=200)
        
        # Status Bar (Row 3)
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
```

---

## 8. Best Practices

### 8.1 Code-Organisation

**Prinzipien**:
- **Single Responsibility**: Jede Klasse hat eine klar definierte Aufgabe
- **DRY (Don't Repeat Yourself)**: Gemeinsame Funktionalität in Utils auslagern
- **SOLID Principles**: Besonders Open/Closed und Dependency Inversion
- **Type Hints**: Python 3.12+ Type Annotations nutzen
- **Docstrings**: Jede öffentliche Methode dokumentieren

**Beispiel**:
```python
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Process:
    """
    Datenmodell für einen VPB-Prozess
    
    Attributes:
        id: Eindeutige Prozess-ID
        title: Prozess-Titel
        start_time: Start-Zeitpunkt
        end_time: End-Zeitpunkt
        status: Aktueller Status
    """
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    status: str
    authority: Optional[str] = None
    documents: List[str] = field(default_factory=list)
```

### 8.2 Error Handling

**Strategie**: Try-Except mit spezifischen Exceptions und Logging

```python
import logging

logger = logging.getLogger(__name__)

class APIController:
    """API Controller mit robustem Error Handling"""
    
    async def fetch_data(self, endpoint: str) -> Optional[dict]:
        """
        Fetch data from backend with error handling
        
        Returns None on error, logs exception
        """
        try:
            response = await self.api_client.get(endpoint)
            response.raise_for_status()
            return response.json()
            
        except requests.HTTPError as e:
            logger.error(f"HTTP Error beim Abruf von {endpoint}: {e}")
            self._show_error_dialog(
                f"Backend-Fehler: {e.response.status_code}"
            )
            return None
            
        except requests.ConnectionError as e:
            logger.error(f"Verbindungsfehler: {e}")
            self._show_error_dialog(
                "Backend nicht erreichbar. Bitte prüfen Sie die Verbindung."
            )
            return None
            
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler: {e}")
            self._show_error_dialog(f"Unerwarteter Fehler: {str(e)}")
            return None
```

### 8.3 Testing

**Test-Strategie**:
- Unit Tests für Models und Controllers
- Integration Tests für API Communication
- UI Tests (simuliert mit unittest.mock)

**Beispiel Unit Test**:
```python
import unittest
from models.process_model import ProcessModel, Process

class TestProcessModel(unittest.TestCase):
    """Tests für ProcessModel"""
    
    def setUp(self):
        self.model = ProcessModel()
    
    def test_add_process(self):
        """Test: Process hinzufügen"""
        process = Process(
            id="p1",
            title="Test Process",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=7),
            status="open"
        )
        
        self.model.add_process(process)
        
        self.assertEqual(len(self.model.get_all()), 1)
        self.assertEqual(self.model.get_by_id("p1").title, "Test Process")
    
    def test_observer_notification(self):
        """Test: Observer wird bei Update benachrichtigt"""
        observer = MockObserver()
        self.model.attach(observer)
        
        process = Process(id="p1", title="Test", ...)
        self.model.add_process(process)
        
        self.assertTrue(observer.was_notified)
        self.assertEqual(observer.last_event, "process_added")
```

### 8.4 Performance

**Optimierungen**:
- **Lazy Loading**: Daten nur bei Bedarf laden
- **Caching**: Häufig genutzte Daten cachen
- **Virtualisierung**: Für große Listen (z.B. 1000+ Dokumente)
- **Debouncing**: Für Search-Input (verzögerte API-Calls)

**Beispiel Debouncing**:
```python
class SearchBar(tk.Frame):
    """Search Bar mit Debouncing"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.search_entry = tk.Entry(self)
        self.search_entry.pack()
        
        self._search_timer = None
        self.search_entry.bind("<KeyRelease>", self._on_key_release)
    
    def _on_key_release(self, event):
        """Cancel previous timer, start new one"""
        if self._search_timer:
            self.after_cancel(self._search_timer)
        
        # Wait 500ms before triggering search
        self._search_timer = self.after(500, self._perform_search)
    
    def _perform_search(self):
        """Actual search (called after debounce delay)"""
        query = self.search_entry.get()
        if query:
            self.controller.search(query)
```

---

## 9. Implementierungsplan

### Phase 1: Grundgerüst (Woche 1)

**Ziele**:
- Projektstruktur erstellen
- Basis-Klassen implementieren (Models, Views, Controllers)
- Main Window mit Menü und Layout
- API Client mit Basis-Funktionalität

**Deliverables**:
- Lauffähige Anwendung mit leerer UI
- API-Verbindung zum Backend
- Logging und Error Handling

### Phase 2: Timeline View (Woche 2)

**Ziele**:
- Canvas-basierte Timeline implementieren
- Prozess-Rendering (Balken, Labels)
- Zoom und Pan Funktionalität
- Click-Events für Prozess-Details

**Deliverables**:
- Funktionale Timeline-Ansicht
- Mock-Daten-Integration
- Unit Tests für Timeline-Logik

### Phase 3: Document Integration (Woche 3)

**Ziele**:
- Document Panel implementieren
- Graph View (Basis)
- UDS3 Integration (Multi-DB)
- Document Detail Dialog

**Deliverables**:
- Dokument-Liste und -Details
- Basis Graph-Visualisierung
- Integration mit Backend APIs

### Phase 4: AI Features (Woche 4)

**Ziele**:
- Filter Panel mit AI
- Natural Language Search
- AI-Empfehlungen
- Intelligente Sortierung

**Deliverables**:
- AI-gestützte Filterung
- NL Query Parser
- Recommendation Engine Integration

### Phase 5: Polish & Testing (Woche 5)

**Ziele**:
- UI/UX Verbesserungen
- Performance-Optimierung
- Comprehensive Testing
- Dokumentation

**Deliverables**:
- Produktionsreife Anwendung
- Test Coverage >80%
- User Manual

---

## 10. Offene Fragen & Next Steps

### Offene Fragen

1. **Backend API Erweiterungen**: Welche zusätzlichen Endpoints werden für VQB benötigt?
2. **Prozess-Datenmodell**: Wie ist die genaue Struktur der VPB-Prozesse?
3. **Performance-Anforderungen**: Wie viele Prozesse/Dokumente müssen gleichzeitig dargestellt werden?
4. **Deployment**: Standalone Executable (PyInstaller) oder Python-Skript?
5. **Authentifizierung**: Braucht VQB separate Authentifizierung oder nutzt es Backend-Sessions?

### Next Steps (zur Klärung/Verfeinerung)

1. **API Contract definieren**: Genaue Request/Response-Formate zwischen VQB und Backend
2. **Datenmodell spezifizieren**: Detaillierte Struktur für Processes, Documents, Relationships
3. **Mockups erstellen**: Detaillierte UI-Mockups für alle Views
4. **Performance-Tests planen**: Baseline-Tests mit realistischen Datenmengen
5. **Security Review**: Authentifizierung, Autorisierung, Datenschutz

---

## 11. Beziehung zu anderen VCC-Teilprojekten

### VCC-VPB (Verwaltungspraxis der Bundesbehörden)

**Integration**:
- VQB nutzt VPB als Prozess-Datenquelle
- VPB-Router im Backend liefert Prozess-Daten
- VQB visualisiert VPB-Prozesse auf Timeline

**Datenaustausch**:
```
VPB (Data Source) -> Backend (VPB Router) -> VQB (Visualization)
```

### UDS3 (Universal Distribution System 3)

**Integration**:
- VQB nutzt UDS3 für Multi-DB-Zugriff
- Graph (Neo4j), Vector (ChromaDB), Relational (PostgreSQL)
- UDS3 liefert Dokumente und Beziehungen

**Strategien**:
- Graph: Prozess-Abhängigkeiten visualisieren
- Vector: Semantische Ähnlichkeit für Empfehlungen
- Relational: Strukturierte Metadaten für Filter

### VERITAS Backend

**Integration**:
- VQB kommuniziert ausschließlich über REST API
- Nutzt Intelligent Pipeline für AI-Features
- Streaming für große Datenmengen

### Weitere Potenzielle Integrationen

- **VCC-Knowledge-Graph**: Erweiterte Graph-Analysen
- **VCC-Reporting**: Export von Prozess-Reports
- **VCC-Workflow**: Prozess-Steuerung aus VQB

---

## 12. Zusammenfassung

Der **Visual Query Builder** ist eine mächtige Ergänzung zum VCC-Veritas-Ökosystem, die Prozess- und Dokumentenmanagement durch intuitive Visualisierung vereint. Durch den Einsatz moderner OOP-Prinzipien, Threading für Performance und AI-Integration bietet VQB eine zukunftssichere Lösung für komplexe Verwaltungsprozesse.

**Kernvorteile**:
- ✅ **Visuelle Klarheit**: Gantt-ähnliche Timeline für sofortiges Verständnis
- ✅ **Multi-modale Integration**: Graph, Vector, Relational, File - alles in einer Ansicht
- ✅ **AI-Unterstützung**: Intelligente Filter und Empfehlungen
- ✅ **Erweiterbarkeit**: Modulare Architektur für zukünftige Features
- ✅ **Performance**: Threading und Caching für flüssige UX

**Nächste Schritte**: Feedback einholen, offene Fragen klären, mit Phase 1 der Implementierung beginnen.

---

**Version**: 1.0  
**Autoren**: VCC-Veritas Development Team  
**Datum**: 19. November 2025  
**Status**: Bereit zur Review und Verfeinerung
