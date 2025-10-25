# VERITAS ↔ UDS3 Integration

## 🎯 Architektur-Prinzip

**VERITAS benötigt UDS3 ZWINGEND!**

UDS3 ist **keine** optionale Dependency, sondern die **zentrale Infrastruktur** von VERITAS:

```
┌─────────────────────────────────────────────────┐
│         VERITAS Unified Backend v4.0.0          │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │      Intelligent Multi-Agent Pipeline    │ │
│  │      Query Service (RAG/Hybrid/etc.)     │ │
│  │      Streaming Progress System           │ │
│  └───────────────────────────────────────────┘ │
│                      ↓                          │
│  ┌───────────────────────────────────────────┐ │
│  │        UDS3 v2.0.0 PolyglotManager       │ │
│  │  ┌─────────────────────────────────────┐ │ │
│  │  │  Vector DB    (ChromaDB)            │ │ │
│  │  │  Graph DB     (Neo4j)      optional │ │ │
│  │  │  Relational   (SQLite)     optional │ │ │
│  │  │  LLM Client   (Ollama)              │ │ │
│  │  │  Embeddings   (German BERT)         │ │ │
│  │  │  RAG Pipeline                       │ │ │
│  │  └─────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## 📋 Was UDS3 bereitstellt

### 1. **Database Backends**
- **Vector Database**: ChromaDB für semantische Suche
- **Graph Database**: Neo4j für Beziehungen (optional)
- **Relational Database**: SQLite für strukturierte Daten (optional)

### 2. **LLM Infrastructure**
- **Ollama Client**: LLM-Integration (llama3.1, mixtral, etc.)
- **German BERT Embeddings**: Optimiert für deutsche Texte
- **RAG Pipeline**: Retrieval-Augmented Generation

### 3. **Core Services**
- **DatabaseManager**: Unified API für alle Backends
- **Polyglot Query**: Queries über mehrere DBs
- **Streaming Operations**: Chunk-basiertes Processing
- **Document Classifier**: Automatische Kategorisierung

## 🚀 Integration in VERITAS Backend

### Direkte Integration (backend/app.py)

```python
# UDS3 v2.0.0 - Zwingend erforderlich
try:
    from uds3 import UDS3PolyglotManager
    UDS3_AVAILABLE = True
except ImportError as e:
    logger.error("❌ KRITISCH: UDS3 nicht verfügbar!")
    raise RuntimeError("UDS3 ist zwingend erforderlich!")

# Initialisierung
backend_config = {
    "vector": {
        "enabled": True,
        "backend": "chromadb",
        "collection_name": "veritas_documents",
        "persist_directory": "data/chromadb"
    },
    "graph": {"enabled": False},      # Optional
    "relational": {"enabled": False}  # Optional
}

app.state.uds3 = UDS3PolyglotManager(
    backend_config=backend_config,
    enable_rag=True
)
```

## 📦 Installation

### UDS3 als Schwester-Projekt

```powershell
# Projekt-Struktur
C:\VCC\
├── veritas\         # VERITAS Backend
└── uds3\            # UDS3 Infrastructure

# UDS3 im Entwicklungsmodus installieren
cd C:\VCC\uds3
pip install -e .

# VERITAS kann jetzt UDS3 importieren
cd C:\VCC\veritas
python start_backend.py
```

### Requirements

**uds3/requirements.txt**:
```
chromadb>=0.4.0
ollama>=0.1.0
sentence-transformers>=2.2.0
neo4j>=5.0.0  # optional
```

## 🔧 Konfiguration

### Minimal (nur Vector DB)

```python
backend_config = {
    "vector": {
        "enabled": True,
        "backend": "chromadb",
        "collection_name": "veritas_documents",
        "persist_directory": "data/chromadb"
    },
    "graph": {"enabled": False},
    "relational": {"enabled": False}
}
```

### Full Stack (alle Backends)

```python
backend_config = {
    "vector": {
        "enabled": True,
        "backend": "chromadb",
        "collection_name": "veritas_documents",
        "persist_directory": "data/chromadb"
    },
    "graph": {
        "enabled": True,
        "backend": "neo4j",
        "uri": "bolt://localhost:7687",
        "user": "neo4j",
        "password": "your_password"
    },
    "relational": {
        "enabled": True,
        "backend": "sqlite",
        "path": "data/veritas.db"
    }
}
```

## 🧪 Health Check

```python
# Backend v4.0.0 Health Endpoint
GET /api/system/health

{
  "status": "healthy",
  "components": {
    "uds3": true,              # MUSS true sein!
    "pipeline": true,
    "query_service": true,
    "streaming": true
  },
  "uds3_backends": {
    "vector": true,            # ChromaDB
    "graph": false,            # Neo4j (optional)
    "relational": false        # SQLite (optional)
  }
}
```

## 📊 UDS3 API Usage

### Semantic Search

```python
# Über UDS3 PolyglotManager
results = app.state.uds3.semantic_search(
    query="Wie beantrage ich eine Baugenehmigung?",
    top_k=5
)

# Results enthalten:
# - content: Dokument-Text
# - metadata: IEEE Citations (35+ Felder)
# - similarity_score: Relevanz
```

### Document Storage

```python
# Dokument hinzufügen
doc_id = app.state.uds3.add_document(
    content="Baugenehmigung...",
    metadata={
        "title": "BauGB §29",
        "rechtsgebiet": "Baurecht",
        "authors": "Gesetzgeber"
    }
)
```

### LLM Query (RAG)

```python
# RAG Query über UDS3
answer = app.state.uds3.answer_query(
    query="Was sind die Voraussetzungen für eine Baugenehmigung?",
    context_docs=5
)

# Answer enthält:
# - answer: LLM-generierte Antwort
# - sources: Verwendete Dokumente
# - citations: IEEE-Format
```

## 🔄 Lifecycle Management

### Startup

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.uds3 = UDS3PolyglotManager(backend_config)
    logger.info("✅ UDS3 PolyglotManager initialisiert")
    
    yield
    
    # Shutdown
    if hasattr(app.state.uds3, 'shutdown'):
        app.state.uds3.shutdown()
    logger.info("✅ UDS3 heruntergefahren")
```

## ⚠️ Fehlerbehandlung

### UDS3 nicht verfügbar

```python
if not UDS3_AVAILABLE:
    logger.error("❌ KRITISCH: UDS3 nicht verfügbar!")
    logger.error("   VERITAS kann ohne UDS3 nicht arbeiten!")
    logger.error("   Installiere UDS3: pip install -e ../uds3")
    raise RuntimeError("UDS3 ist zwingend erforderlich!")
```

### Initialisierung fehlgeschlagen

```python
try:
    app.state.uds3 = UDS3PolyglotManager(backend_config)
except Exception as e:
    logger.error(f"❌ UDS3 Initialisierung fehlgeschlagen: {e}")
    logger.error("   Prüfe:")
    logger.error("   1. Ist ChromaDB installiert?")
    logger.error("   2. Läuft Ollama? (http://localhost:11434)")
    logger.error("   3. Ist das Persist-Directory beschreibbar?")
    raise RuntimeError(f"UDS3 Init failed: {e}")
```

## 🎯 Best Practices

### 1. **Keine Wrapper/Abstractions**
- UDS3 direkt verwenden
- Keine zusätzlichen Service-Layer
- Klare Dependency: VERITAS → UDS3

### 2. **Explizite Dependencies**
- UDS3 als "required" in requirements.txt
- Keine optionalen Imports
- Klare Fehlermeldungen wenn fehlt

### 3. **Backend Configuration**
- Vector DB (ChromaDB) immer enabled
- Graph/Relational optional
- Persist Directory sichern

### 4. **Error Handling**
- Startup blockieren wenn UDS3 fehlt
- Keine Silent Fallbacks
- Klare Fehlermeldungen

## 📚 Weiterführende Dokumentation

- **UDS3 Repository**: `C:\VCC\uds3\`
- **UDS3 README**: `C:\VCC\uds3\README.md`
- **VERITAS Backend**: `backend/app.py`
- **Health Check**: `backend/api/system_router.py`

## ✅ Checklist: UDS3 Integration

- [x] UDS3 als Schwester-Projekt installiert
- [x] Import `from uds3 import UDS3PolyglotManager`
- [x] Backend-Config mit ChromaDB
- [x] Persist-Directory erstellt
- [x] Initialisierung mit `enable_rag=True`
- [x] Health Check zeigt `uds3: true`
- [x] Shutdown in lifespan()
- [x] Fehlerbehandlung bei Missing UDS3
- [x] Keine optionalen Fallbacks
- [x] Explizite Error Messages

## 🚫 Anti-Patterns

### ❌ NICHT so:
```python
# Wrapper/Service-Layer (ÜBERFLÜSSIG!)
class UDS3IntegrationService:
    def __init__(self):
        self.uds3 = UDS3PolyglotManager(...)
    
    def semantic_search(self, query):
        return self.uds3.semantic_search(query)

# Mock-Modus (GEFÄHRLICH!)
if not UDS3_AVAILABLE:
    logger.warning("⚠️  Läuft ohne UDS3")
    return mock_results()
```

### ✅ STATTDESSEN so:
```python
# Direkte Integration
from uds3 import UDS3PolyglotManager

# Zwingend erforderlich
if not UDS3_AVAILABLE:
    raise RuntimeError("UDS3 ist zwingend erforderlich!")

# Direkte Nutzung
app.state.uds3 = UDS3PolyglotManager(backend_config)
results = app.state.uds3.semantic_search(query)
```

---

**Fazit**: VERITAS und UDS3 sind **untrennbar**. UDS3 ist die Infrastruktur, VERITAS ist die Anwendungslogik.
