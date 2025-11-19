# VQB Frontend - Visual Query Builder

## Überblick

Der **Visual Query Builder (VQB)** ist eine Python/tkinter-basierte Frontend-Anwendung für VCC-Veritas, die VPB-Prozesse mit rechtlichen Dokumenten und Neo4j-Graph-Strukturen visuell verbindet.

## Features

### ✨ Kernfunktionen

- **Timeline-Ansicht**: Gantt-ähnliche Darstellung von VPB-Prozessen
- **Neo4j Graph-Visualisierung**: 
  - Rechtliche Chunks (Text-Segmente)
  - Rechtsbereiche (Baurecht, Umweltrecht, etc.)
  - Föderale Hierarchie (Bund → Land → Kommune)
  - Rechtsnormen (BImSchG, VwVfG, etc.)
  - Behörden und ihre Zuständigkeiten
- **VCC-URN System**: Einheitliche Identifikation über alle Systeme
- **AI-gestützte Filter**: Intelligente Suche und Filterung
- **Multi-DB Integration**: VPB, Neo4j, PostgreSQL, ChromaDB

### 🏗️ Architektur

```
vqb_frontend/
├── app.py                  # Hauptanwendung
├── config/                 # Konfiguration
│   ├── app_config.py       # App-Einstellungen
│   ├── api_config.py       # Backend-API-Konfiguration
│   └── color_scheme.py     # Farbschema
├── models/                 # Datenmodelle
│   ├── base_model.py       # Observable-Basisklasse
│   ├── process_model.py    # Prozess-Modell
│   └── document_model.py   # Dokument-Modell
├── services/               # Services
│   └── async_worker.py     # Threading/Queue-Manager
└── utils/                  # Utilities
    └── urn.py              # VCC-URN Implementierung
```

## Installation

### Voraussetzungen

- Python 3.12+
- tkinter (Teil der Python-Standardbibliothek)
- Zugriff auf VCC-Veritas Backend (läuft auf `http://localhost:5000`)

### Setup

```bash
# 1. Repository klonen (falls nicht bereits geschehen)
git clone <repository-url>
cd VCC-Veritas

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. Backend starten (in separatem Terminal)
python start_backend.py

# 4. VQB Frontend starten
python vqb_frontend/app.py
```

### Umgebungsvariablen (optional)

```bash
# Backend-URL überschreiben
export VERITAS_BACKEND_URL=http://localhost:5000

# Fenstergröße anpassen
export VQB_WINDOW_WIDTH=1600
export VQB_WINDOW_HEIGHT=1000

# Debug-Modus aktivieren
export VQB_DEBUG=1
```

## Verwendung

### Basis-Anwendung starten

```python
from vqb_frontend.app import VQBApplication

# Anwendung erstellen und starten
app = VQBApplication()
app.mainloop()
```

### Modelle verwenden

```python
from vqb_frontend.models.process_model import Process, ProcessModel, ProcessStatus
from datetime import datetime, timedelta

# Process Model erstellen
model = ProcessModel()

# Observer hinzufügen
def on_update(event, **kwargs):
    print(f"Model update: {event}")

model.attach(on_update)

# Prozess hinzufügen
process = Process(
    id="baugenehmigung-2024-001",
    title="Baugenehmigung Projekt X",
    start_time=datetime.now(),
    end_time=datetime.now() + timedelta(days=30),
    status=ProcessStatus.IN_PROGRESS,
    authority="Stadt Potsdam"
)

model.add_process(process)  # Benachrichtigt Observer
```

### VCC-URN verwenden

```python
from vqb_frontend.utils.urn import (
    URN, 
    create_vpb_process_urn,
    create_chunk_urn,
    create_legal_domain_urn
)

# URN erstellen
process_urn = create_vpb_process_urn("baugenehmigung-2024-001")
print(process_urn)  # urn:vcc:vpb:process:baugenehmigung-2024-001

# Chunk-URN
chunk_urn = create_chunk_urn("bimschg", "bimschg-2024-001", 42)
print(chunk_urn)  # urn:vcc:chunk:bimschg:bimschg-2024-001:42

# URN parsen
urn_obj = URN.from_string("urn:vcc:vpb:process:proc-001")
print(urn_obj.namespace)  # URNNamespace.VPB
print(urn_obj.identifier)  # proc-001
```

### Async Worker verwenden

```python
from vqb_frontend.services.async_worker import AsyncWorker, Task

class MyTask(Task):
    def execute(self):
        # Lange Berechnung
        return {"result": "success"}

# Worker erstellen
worker = AsyncWorker(num_threads=4)

# Task einreichen
task = MyTask()
task.callback = lambda result: print(f"Done: {result}")
worker.submit_task(task)

# Periodisch Results verarbeiten (im main thread)
worker.process_results()
```

## Tests

### Tests ausführen

```bash
# Alle VQB Tests
python -m unittest discover tests -p "test_vqb_*.py" -v

# Nur Model-Tests
python -m unittest tests.test_vqb_models -v

# Nur URN-Tests
python -m unittest tests.test_vqb_urn -v
```

### Test-Abdeckung

- ✅ Process Model: 10 Tests
- ✅ Document Model: 5 Tests
- ✅ URN Implementation: 22 Tests
- **Total: 37 Tests (alle bestanden)**

## Konzept-Dokumentation

Detaillierte Konzepte und Spezifikationen:

1. **[KONZEPT_VISUAL_QUERY_BUILDER.md](../KONZEPT_VISUAL_QUERY_BUILDER.md)**
   - Vollständige Architektur-Übersicht
   - UI/UX Design
   - Best Practices
   - Implementierungsplan

2. **[KONZEPT_VQB_NEO4J_GRAPH.md](../KONZEPT_VQB_NEO4J_GRAPH.md)**
   - Neo4j Graph-Struktur
   - Chunks, Rechtsbereiche, Föderale Ebenen
   - Graph-Visualisierung
   - Use Cases

3. **[VCC_URN_SCHEMA.md](../VCC_URN_SCHEMA.md)**
   - URN-Syntax und Namespaces
   - Factory Functions
   - URN Resolver
   - Integration Guide

## Beispiele

### Timeline mit Mock-Daten

```python
from vqb_frontend.models.process_model import Process, ProcessModel, ProcessStatus
from datetime import datetime, timedelta

# Mock-Daten erstellen
model = ProcessModel()

processes = [
    Process(
        id="proc-001",
        title="Baugenehmigung",
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 2, 1),
        status=ProcessStatus.COMPLETED
    ),
    Process(
        id="proc-002",
        title="Umweltgenehmigung",
        start_time=datetime(2024, 1, 15),
        end_time=datetime(2024, 3, 15),
        status=ProcessStatus.IN_PROGRESS
    )
]

for p in processes:
    model.add_process(p)

print(f"Processes loaded: {model.get_count()}")
```

### Rechtsbereiche filtern

```python
from vqb_frontend.models.document_model import Document, DocumentModel, DocumentType

model = DocumentModel()

# Dokumente mit Rechtsbereich-Tags
doc1 = Document(
    id="doc-001",
    title="BImSchG Volltext",
    doc_type=DocumentType.PDF,
    metadata={"rechtsbereich": "umweltrecht"}
)

doc2 = Document(
    id="doc-002",
    title="BauGB Auszug",
    doc_type=DocumentType.PDF,
    metadata={"rechtsbereich": "baurecht"}
)

model.add_document(doc1)
model.add_document(doc2)

# Filtern nach Metadata
umweltrecht_docs = [
    d for d in model.get_all_documents()
    if d.metadata.get("rechtsbereich") == "umweltrecht"
]

print(f"Umweltrecht docs: {len(umweltrecht_docs)}")
```

## API-Integration

### Backend-Endpoints

VQB kommuniziert mit folgenden Backend-Endpoints:

```python
# VPB Endpoints
GET  /api/v3/vpb/query              # VPB Prozesse abfragen
GET  /api/v3/vpb/documents          # VPB Dokumente listen
POST /api/v3/vpb/analysis           # Prozessanalyse

# Graph Endpoints (geplant)
GET  /api/v3/graph/chunks/{process_id}        # Chunks für Prozess
GET  /api/v3/graph/legal-domains              # Rechtsbereiche
GET  /api/v3/graph/federal-hierarchy          # Föderale Hierarchie
GET  /api/v3/graph/chunk-references/{chunk_id} # Chunk-Referenzen
```

### Beispiel API-Call

```python
from vqb_frontend.config.api_config import APIConfig
import requests

# Prozesse abfragen
url = APIConfig.get_endpoint("vpb/query")
response = requests.post(url, json={
    "query": "Alle Genehmigungsverfahren",
    "filters": {"status": "open"}
})

processes = response.json()
```

## Roadmap

### Phase 1: Grundgerüst ✅ (Abgeschlossen)
- [x] Projektstruktur
- [x] Basis-Klassen (Models, Services)
- [x] VCC-URN Implementierung
- [x] Tests

### Phase 2: Timeline View (Nächste Schritte)
- [ ] Canvas-basierte Timeline
- [ ] Prozess-Rendering
- [ ] Zoom/Pan Funktionalität
- [ ] Interaktion (Click, Hover)

### Phase 3: Graph View
- [ ] Neo4j Integration
- [ ] Graph-Visualisierung
- [ ] Force-directed Layout
- [ ] Chunk-Inspector

### Phase 4: AI Features
- [ ] Filter Panel
- [ ] Natural Language Search
- [ ] AI-Empfehlungen
- [ ] Intelligente Sortierung

### Phase 5: Polish & Production
- [ ] UI/UX Verbesserungen
- [ ] Performance-Optimierung
- [ ] Comprehensive Testing
- [ ] User Manual

## Troubleshooting

### Häufige Probleme

**Problem**: `ModuleNotFoundError: No module named 'tkinter'`

**Lösung**: 
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS (tkinter ist standardmäßig enthalten)
# Falls nicht: brew install python-tk

# Windows (tkinter ist standardmäßig enthalten)
```

**Problem**: Backend nicht erreichbar

**Lösung**:
1. Prüfen ob Backend läuft: `curl http://localhost:5000/health`
2. Backend-URL in Environment setzen: `export VERITAS_BACKEND_URL=http://localhost:5000`
3. Firewall prüfen

**Problem**: Tests schlagen fehl

**Lösung**:
```bash
# Sicherstellen dass alle Dependencies installiert sind
pip install -r requirements.txt

# Tests einzeln ausführen
python -m unittest tests.test_vqb_models.TestProcessModel -v
```

## Mitwirken

Contributions sind willkommen! Bitte:

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/amazing-feature`)
3. Committe deine Änderungen (`git commit -m 'Add amazing feature'`)
4. Push zum Branch (`git push origin feature/amazing-feature`)
5. Öffne einen Pull Request

### Coding Standards

- Python 3.12+ Type Hints verwenden
- Docstrings für alle öffentlichen Methoden
- Tests für neue Features
- Code-Style: PEP 8

## Lizenz

[Siehe Repository-Lizenz]

## Kontakt

**VCC-Veritas Development Team**

- Issues: [GitHub Issues](https://github.com/makr-code/VCC-Veritas/issues)
- Dokumentation: Siehe `docs/` Verzeichnis
- Logs: `vqb_frontend.log`

---

**Version**: 0.1.0  
**Status**: Konzept & Basis-Implementierung  
**Letztes Update**: 19. November 2025
