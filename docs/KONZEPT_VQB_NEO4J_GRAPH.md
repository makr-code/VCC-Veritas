# VCC-Veritas Visual Query Builder - Erweiterte Neo4j Graph-Integration

## Ergänzung zum Hauptkonzept
**Version**: 1.1  
**Datum**: 19. November 2025

---

## Neo4j Graph-Struktur: Chunks, Rechtsbereiche & Föderale Systeme

### 1. Graph-Datenmodell (Neo4j)

Der Graph in VCC-Veritas repräsentiert **keine generischen Dokument-Beziehungen**, sondern spezifische **rechtliche und administrative Strukturen** auf Chunk-Ebene:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Neo4j Graph Structure                         │
└─────────────────────────────────────────────────────────────────┘

Nodes (Knotentypen):
├── Chunk (Text-Segmente aus Dokumenten)
│   ├── Properties: id, content, source_doc, position, ...
│   └── Labels: :Chunk, :LegalText, :Regulation, etc.
│
├── Rechtsbereich (Legal Domain)
│   ├── Properties: name, code, description
│   ├── Examples: "Baurecht", "Umweltrecht", "Verwaltungsrecht"
│   └── Labels: :LegalDomain
│
├── FöderaleEbene (Federal Level)
│   ├── Properties: level, jurisdiction, name
│   ├── Examples: "Bund", "Land Brandenburg", "Kommune Berlin"
│   └── Labels: :FederalLevel, :Federation, :State, :Municipality
│
├── Behörde (Authority)
│   ├── Properties: name, jurisdiction, level
│   └── Labels: :Authority
│
├── Rechtsnorm (Legal Norm)
│   ├── Properties: name, abbreviation, year
│   ├── Examples: "BImSchG", "VwVfG", "BauGB"
│   └── Labels: :LegalNorm, :Law, :Regulation
│
└── Prozessschritt (Process Step - from VPB)
    ├── Properties: step_id, title, description
    └── Labels: :ProcessStep

Relationships (Beziehungstypen):
├── (Chunk)-[:BELONGS_TO]->(Rechtsbereich)
│   └── Chunk gehört zu Rechtsbereich (z.B. Baurecht, Umweltrecht)
│
├── (Chunk)-[:GOVERNED_BY]->(FöderaleEbene)
│   └── Chunk unterliegt föderaler Zuständigkeit
│
├── (Chunk)-[:REFERENCES]->(Chunk)
│   └── Cross-References zwischen Chunks (Querverweise)
│
├── (Chunk)-[:IMPLEMENTS]->(Rechtsnorm)
│   └── Chunk setzt Rechtsnorm um
│
├── (Chunk)-[:ISSUED_BY]->(Behörde)
│   └── Chunk von Behörde herausgegeben
│
├── (Rechtsbereich)-[:OVERLAPS]->(Rechtsbereich)
│   └── Rechtsbereiche überschneiden sich
│
├── (FöderaleEbene)-[:SUBORDINATE_TO]->(FöderaleEbene)
│   └── Hierarchie: Kommune → Land → Bund
│
├── (ProcessStep)-[:REQUIRES]->(Chunk)
│   └── Prozessschritt benötigt rechtliche Grundlage
│
└── (ProcessStep)-[:APPLIES_IN]->(FöderaleEbene)
    └── Prozessschritt gilt in föderaler Ebene
```

---

### 2. Angepasste Graph View Komponente

Die **Graph View** im VQB muss diese spezifische Struktur visualisieren:

#### 2.1 Visualisierungs-Modi

```python
class GraphViewMode(Enum):
    """Verschiedene Graph-Ansichtsmodi"""
    
    CHUNK_NETWORK = "chunk_network"
    # Zeigt Chunks und ihre Referenzen
    
    LEGAL_DOMAINS = "legal_domains"
    # Zeigt Rechtsbereiche und ihre Überschneidungen
    
    FEDERAL_HIERARCHY = "federal_hierarchy"
    # Zeigt föderale Struktur (Bund → Land → Kommune)
    
    PROCESS_LEGAL_BASIS = "process_legal_basis"
    # Verbindet VPB-Prozesse mit rechtlichen Grundlagen
    
    AUTHORITY_NETWORK = "authority_network"
    # Zeigt Behörden und ihre Zuständigkeiten
```

#### 2.2 Node-Darstellung nach Typ

```python
class GraphView(tk.Canvas):
    """Erweiterte Graph View für rechtliche Strukturen"""
    
    NODE_COLORS = {
        "Chunk": "#87CEEB",           # Sky Blue
        "Rechtsbereich": "#FFD700",    # Gold
        "FöderaleEbene": "#90EE90",    # Light Green
        "Behörde": "#DDA0DD",          # Plum
        "Rechtsnorm": "#F0E68C",       # Khaki
        "ProcessStep": "#FF6347"       # Tomato
    }
    
    NODE_SHAPES = {
        "Chunk": "rectangle",
        "Rechtsbereich": "hexagon",
        "FöderaleEbene": "triangle",
        "Behörde": "pentagon",
        "Rechtsnorm": "octagon",
        "ProcessStep": "diamond"
    }
    
    def _draw_node(self, node, position):
        """Zeichne Node basierend auf Typ"""
        node_type = node.labels[0]  # Primary label
        
        color = self.NODE_COLORS.get(node_type, "#CCCCCC")
        shape = self.NODE_SHAPES.get(node_type, "circle")
        
        # Zeichne entsprechende Form
        if shape == "rectangle":
            self._draw_rect_node(position, color, node.properties["content"][:30])
        elif shape == "hexagon":
            self._draw_hexagon_node(position, color, node.properties["name"])
        # ... weitere Formen
```

#### 2.3 Edge-Darstellung nach Relationship-Typ

```python
EDGE_STYLES = {
    "BELONGS_TO": {"color": "#FFD700", "width": 2, "style": "solid"},
    "GOVERNED_BY": {"color": "#90EE90", "width": 2, "style": "solid"},
    "REFERENCES": {"color": "#87CEEB", "width": 1, "style": "dashed"},
    "IMPLEMENTS": {"color": "#F0E68C", "width": 2, "style": "solid"},
    "ISSUED_BY": {"color": "#DDA0DD", "width": 1, "style": "solid"},
    "OVERLAPS": {"color": "#FFA500", "width": 1, "style": "dotted"},
    "SUBORDINATE_TO": {"color": "#32CD32", "width": 3, "style": "solid"},
    "REQUIRES": {"color": "#FF6347", "width": 2, "style": "solid"},
    "APPLIES_IN": {"color": "#4169E1", "width": 1, "style": "dashed"}
}

def _draw_edge(self, edge, positions):
    """Zeichne Edge mit spezifischem Stil"""
    rel_type = edge.type
    style = EDGE_STYLES.get(rel_type, {"color": "#CCCCCC", "width": 1, "style": "solid"})
    
    x1, y1 = positions[edge.start_node]
    x2, y2 = positions[edge.end_node]
    
    if style["style"] == "dashed":
        self.create_line(x1, y1, x2, y2, fill=style["color"], 
                        width=style["width"], dash=(5, 3))
    elif style["style"] == "dotted":
        self.create_line(x1, y1, x2, y2, fill=style["color"], 
                        width=style["width"], dash=(2, 2))
    else:
        self.create_line(x1, y1, x2, y2, fill=style["color"], 
                        width=style["width"])
    
    # Pfeil für gerichtete Beziehungen
    self._draw_arrow(x2, y2, math.atan2(y2-y1, x2-x1), style["color"])
```

---

### 3. Erweiterte Datenmodelle

#### 3.1 Chunk Model

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Chunk:
    """
    Repräsentiert einen Text-Chunk aus Neo4j
    
    Attributes:
        id: Chunk ID (Neo4j node ID)
        content: Text-Inhalt des Chunks
        source_doc: Quelldokument-ID
        position: Position im Dokument
        rechtsbereiche: Zugeordnete Rechtsbereiche
        foederale_ebene: Föderale Zuständigkeit
        rechtsnormen: Implementierte Rechtsnormen
        behoerde: Herausgebende Behörde
        metadata: Weitere Metadaten
    """
    id: str
    content: str
    source_doc: str
    position: int
    rechtsbereiche: List[str] = field(default_factory=list)
    foederale_ebene: Optional[str] = None
    rechtsnormen: List[str] = field(default_factory=list)
    behoerde: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def preview(self) -> str:
        """Kurze Vorschau (erste 100 Zeichen)"""
        return self.content[:100] + "..." if len(self.content) > 100 else self.content


@dataclass
class Rechtsbereich:
    """
    Rechtsbereich (Legal Domain)
    
    Attributes:
        name: Name des Rechtsbereichs
        code: Kurz-Code
        description: Beschreibung
        chunk_count: Anzahl zugeordneter Chunks
        overlaps_with: Überschneidungen mit anderen Rechtsbereichen
    """
    name: str
    code: str
    description: str = ""
    chunk_count: int = 0
    overlaps_with: List[str] = field(default_factory=list)


@dataclass
class FoederaleEbene:
    """
    Föderale Ebene (Federal Level)
    
    Attributes:
        level: Ebene (bund, land, kommune)
        jurisdiction: Zuständigkeitsbereich
        name: Name (z.B. "Brandenburg", "Berlin")
        parent: Übergeordnete Ebene
        children: Untergeordnete Ebenen
    """
    level: str  # "bund", "land", "kommune"
    jurisdiction: str
    name: str
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
```

#### 3.2 Graph Relationship Model

```python
@dataclass
class GraphRelationship:
    """
    Neo4j Graph-Beziehung
    
    Attributes:
        source_id: Quell-Node ID
        target_id: Ziel-Node ID
        rel_type: Beziehungstyp (BELONGS_TO, GOVERNED_BY, etc.)
        properties: Beziehungs-Properties
    """
    source_id: str
    target_id: str
    rel_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_neo4j(cls, relationship) -> "GraphRelationship":
        """Erstelle aus Neo4j Relationship object"""
        return cls(
            source_id=str(relationship.start_node.id),
            target_id=str(relationship.end_node.id),
            rel_type=relationship.type,
            properties=dict(relationship)
        )
```

---

### 4. API Integration für Neo4j Queries

#### 4.1 Backend API Endpoints (neu)

```python
# Neue Endpoints im Backend

@router.get("/graph/chunks/{process_id}")
async def get_process_legal_chunks(process_id: str):
    """
    Hole alle rechtlichen Chunks für einen Prozess
    
    Returns:
        - Chunks
        - Rechtsbereiche
        - Föderale Zuständigkeiten
        - Beziehungen
    """
    pass

@router.get("/graph/legal-domains")
async def get_legal_domain_network():
    """
    Hole Rechtsbereiche und ihre Überschneidungen
    
    Returns:
        - Rechtsbereiche (Nodes)
        - Überschneidungen (Edges)
    """
    pass

@router.get("/graph/federal-hierarchy")
async def get_federal_hierarchy():
    """
    Hole föderale Hierarchie
    
    Returns:
        - Föderale Ebenen (Nodes)
        - Hierarchie (Edges: SUBORDINATE_TO)
    """
    pass

@router.get("/graph/chunk-references/{chunk_id}")
async def get_chunk_references(chunk_id: str, depth: int = 2):
    """
    Hole Chunk und alle Referenzen bis Tiefe N
    
    Returns:
        - Zentral-Chunk
        - Referenzierte Chunks
        - Beziehungen
    """
    pass
```

#### 4.2 Frontend API Client

```python
class GraphAPIClient:
    """API Client für Neo4j Graph Queries"""
    
    async def get_process_legal_chunks(self, process_id: str) -> Dict[str, Any]:
        """
        Hole rechtliche Chunks für Prozess
        
        Args:
            process_id: VPB Prozess ID
        
        Returns:
            Dict mit chunks, rechtsbereiche, foederale_ebenen, relationships
        """
        response = await self.api_client.get(
            f"/api/v3/graph/chunks/{process_id}"
        )
        return response.json()
    
    async def get_legal_domain_network(self) -> Dict[str, Any]:
        """Hole Rechtsbereiche-Netzwerk"""
        response = await self.api_client.get(
            "/api/v3/graph/legal-domains"
        )
        return response.json()
    
    async def get_federal_hierarchy(self) -> Dict[str, Any]:
        """Hole föderale Hierarchie"""
        response = await self.api_client.get(
            "/api/v3/graph/federal-hierarchy"
        )
        return response.json()
    
    async def get_chunk_references(self, chunk_id: str, depth: int = 2) -> Dict[str, Any]:
        """
        Hole Chunk-Referenzen
        
        Args:
            chunk_id: Chunk ID
            depth: Traversierungs-Tiefe
        
        Returns:
            Dict mit chunks und references
        """
        response = await self.api_client.get(
            f"/api/v3/graph/chunk-references/{chunk_id}",
            params={"depth": depth}
        )
        return response.json()
```

---

### 5. UI-Komponenten für Graph-Exploration

#### 5.1 Chunk Inspector Panel

```python
class ChunkInspectorPanel(tk.Frame):
    """
    Detailansicht für ausgewählten Chunk
    
    Zeigt:
    - Chunk-Inhalt
    - Rechtsbereiche
    - Föderale Zuständigkeit
    - Rechtsnormen
    - Referenzen (ausgehend/eingehend)
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Chunk Content
        self.content_label = tk.Label(self, text="Chunk Content:")
        self.content_label.pack()
        
        self.content_text = tk.Text(self, height=10, wrap=tk.WORD)
        self.content_text.pack(fill=tk.BOTH, expand=True)
        
        # Metadata Frame
        self.metadata_frame = ttk.LabelFrame(self, text="Metadata")
        self.metadata_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Rechtsbereiche
        tk.Label(self.metadata_frame, text="Rechtsbereiche:").grid(row=0, column=0, sticky="w")
        self.rechtsbereiche_label = tk.Label(self.metadata_frame, text="")
        self.rechtsbereiche_label.grid(row=0, column=1, sticky="w")
        
        # Föderale Ebene
        tk.Label(self.metadata_frame, text="Föderale Ebene:").grid(row=1, column=0, sticky="w")
        self.foederale_label = tk.Label(self.metadata_frame, text="")
        self.foederale_label.grid(row=1, column=1, sticky="w")
        
        # Rechtsnormen
        tk.Label(self.metadata_frame, text="Rechtsnormen:").grid(row=2, column=0, sticky="w")
        self.rechtsnormen_label = tk.Label(self.metadata_frame, text="")
        self.rechtsnormen_label.grid(row=2, column=1, sticky="w")
        
        # Referenzen
        self.ref_frame = ttk.LabelFrame(self, text="Referenzen")
        self.ref_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.ref_tree = ttk.Treeview(self.ref_frame, columns=("Direction", "Type"))
        self.ref_tree.heading("#0", text="Chunk")
        self.ref_tree.heading("Direction", text="Direction")
        self.ref_tree.heading("Type", text="Type")
        self.ref_tree.pack(fill=tk.BOTH, expand=True)
    
    def display_chunk(self, chunk: Chunk, references: List[GraphRelationship]):
        """Zeige Chunk-Details"""
        # Content
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(1.0, chunk.content)
        
        # Metadata
        self.rechtsbereiche_label.config(text=", ".join(chunk.rechtsbereiche))
        self.foederale_label.config(text=chunk.foederale_ebene or "N/A")
        self.rechtsnormen_label.config(text=", ".join(chunk.rechtsnormen))
        
        # Referenzen
        self.ref_tree.delete(*self.ref_tree.get_children())
        
        for ref in references:
            direction = "→" if ref.source_id == chunk.id else "←"
            other_id = ref.target_id if ref.source_id == chunk.id else ref.source_id
            
            self.ref_tree.insert("", tk.END, text=other_id,
                               values=(direction, ref.rel_type))
```

#### 5.2 Legal Domain Filter

```python
class LegalDomainFilter(tk.Frame):
    """
    Filter für Rechtsbereiche
    
    Ermöglicht:
    - Multi-Select von Rechtsbereichen
    - AND/OR Verknüpfung
    - Föderale Ebenen-Filter
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Rechtsbereich Multi-Select
        tk.Label(self, text="Rechtsbereiche:").pack()
        
        self.rechtsbereiche_frame = tk.Frame(self)
        self.rechtsbereiche_frame.pack(fill=tk.BOTH, expand=True)
        
        self.rechtsbereich_vars = {}
        
        # Wird dynamisch gefüllt
        self._load_rechtsbereiche()
        
        # AND/OR Toggle
        self.logic_var = tk.StringVar(value="AND")
        tk.Radiobutton(self, text="UND (alle)", variable=self.logic_var, 
                      value="AND").pack()
        tk.Radiobutton(self, text="ODER (mind. einer)", variable=self.logic_var,
                      value="OR").pack()
        
        # Föderale Ebene Filter
        tk.Label(self, text="Föderale Ebene:").pack()
        self.foederale_var = tk.StringVar(value="Alle")
        
        foederale_combo = ttk.Combobox(self, textvariable=self.foederale_var,
                                      values=["Alle", "Bund", "Land", "Kommune"])
        foederale_combo.pack()
        
        # Apply Button
        tk.Button(self, text="Filter anwenden", 
                 command=self._apply_filter).pack(pady=5)
    
    def _load_rechtsbereiche(self):
        """Lade verfügbare Rechtsbereiche"""
        # Async Task
        task = LoadRechtsbereicheTask()
        task.callback = self._on_rechtsbereiche_loaded
        self.controller.submit_task(task)
    
    def _on_rechtsbereiche_loaded(self, result):
        """Callback: Rechtsbereiche geladen"""
        if result.success:
            for rb in result.result:
                var = tk.BooleanVar()
                self.rechtsbereich_vars[rb.code] = var
                
                cb = tk.Checkbutton(self.rechtsbereiche_frame, 
                                   text=f"{rb.name} ({rb.chunk_count})",
                                   variable=var)
                cb.pack(anchor="w")
    
    def _apply_filter(self):
        """Wende Filter an"""
        # Sammle ausgewählte Rechtsbereiche
        selected = [code for code, var in self.rechtsbereich_vars.items() 
                   if var.get()]
        
        logic = self.logic_var.get()
        foederale_ebene = self.foederale_var.get()
        
        # Benachrichtige Controller
        self.controller.apply_graph_filter(
            rechtsbereiche=selected,
            logic=logic,
            foederale_ebene=foederale_ebene if foederale_ebene != "Alle" else None
        )
```

---

### 6. Use Cases für Graph-Visualisierung

#### Use Case 1: Prozess → Rechtliche Grundlagen

```
User Action:
1. Klickt auf Prozess in Timeline
2. Wählt "Rechtliche Grundlagen anzeigen"

System Response:
1. Lädt alle Chunks, die mit Prozess verbunden sind (REQUIRES)
2. Visualisiert Chunks im Graph
3. Färbt nach Rechtsbereich
4. Zeigt föderale Zuständigkeit als Labels
```

#### Use Case 2: Rechtsbereich-Übersicht

```
User Action:
1. Wählt "Rechtsbereiche" im View-Menü
2. System zeigt alle Rechtsbereiche als Nodes

Interaktion:
- Node-Größe = Anzahl Chunks
- Edge-Dicke = Anzahl Überschneidungen
- Klick auf Node → Zeigt zugehörige Chunks
```

#### Use Case 3: Föderale Hierarchie

```
User Action:
1. Wählt "Föderale Struktur" im View-Menü

System Response:
1. Zeigt hierarchischen Tree:
   - Bund (top)
   - Länder (middle)
   - Kommunen (bottom)
2. Färbt Nodes nach Ebene
3. Zeigt Anzahl Chunks pro Ebene
```

#### Use Case 4: Chunk-Referenz-Exploration

```
User Action:
1. Doppelklick auf Chunk im Graph
2. System expandiert Referenzen

System Response:
1. Zeigt ausgehende und eingehende Referenzen
2. Tiefe 2 (konfigurierbar)
3. Highlighting des Pfades bei Hover
```

---

### 7. Zusammenfassung der Anpassungen

**Hauptunterschiede zum initialen Konzept**:

1. **Graph = Neo4j-Chunks**, nicht generische Dokument-Relationen
2. **Fokus auf rechtliche Strukturen**: Rechtsbereiche, föderale Ebenen
3. **Chunk-basierte Visualisierung**: Text-Segmente statt ganzer Dokumente
4. **Spezifische Relationship-Types**: BELONGS_TO, GOVERNED_BY, etc.
5. **Multi-dimensionale Filter**: Nach Rechtsbereich UND föderaler Ebene
6. **Hierarchische Darstellung**: Für föderale Strukturen

**Neue Komponenten**:
- `ChunkInspectorPanel`: Detailansicht für Chunks
- `LegalDomainFilter`: Filter nach Rechtsbereichen
- `FederalHierarchyView`: Föderale Struktur-Ansicht
- Erweiterte Graph-Visualisierung mit spezifischen Node/Edge-Typen

**Backend-Integration**:
- Neue API-Endpoints für Neo4j-Queries
- Chunk-basierte Datenmodelle
- Graph-Traversierung mit konfigurierbarer Tiefe

---

Diese erweiterte Konzeption integriert sich nahtlos in das Haupt-VQB-Konzept und erweitert es um die spezifischen Anforderungen für Neo4j-basierte rechtliche Graph-Strukturen.
