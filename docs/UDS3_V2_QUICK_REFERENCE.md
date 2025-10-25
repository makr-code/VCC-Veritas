# UDS3 v2.0.0 - Quick Reference

**Schnellreferenz für UDS3 v2.0.0 Polyglot Manager im VERITAS Backend**

---

## 🚀 Quick Start

### **Import**
```python
from uds3 import UDS3PolyglotManager
```

### **Minimale Initialisierung (ChromaDB)**
```python
backend_config = {
    "vector": {"enabled": True, "backend": "chromadb"},
    "graph": {"enabled": False},
    "relational": {"enabled": False},
    "file_storage": {"enabled": False}
}

uds3 = UDS3PolyglotManager(
    backend_config=backend_config,
    enable_rag=True
)
```

### **Erweiterte Initialisierung**
```python
backend_config = {
    "vector": {
        "enabled": True,
        "backend": "chromadb",
        "path": "data/chromadb",
        "collection": "veritas_documents"
    },
    "graph": {"enabled": True, "uri": "bolt://localhost:7687"},
    "relational": {"enabled": True, "connection_string": "postgresql://..."},
    "file_storage": {"enabled": True, "url": "http://localhost:5984"}
}

uds3 = UDS3PolyglotManager(
    backend_config=backend_config,
    embeddings_model="deutsche-telekom/gbert-base",  # German BERT
    llm_base_url="http://localhost:11434",          # Ollama
    llm_model="llama3.2",
    enable_rag=True,
    cache_dir=Path("data/embeddings_cache")
)
```

---

## 🔍 RAG Operations

### **Semantic Search**
```python
# Einfache Suche
results = uds3.semantic_search("Photovoltaik Genehmigung")

# Mit Konfiguration
results = uds3.semantic_search(
    query="BImSchG Grenzwerte",
    top_k=10,
    threshold=0.7
)
```

### **LLM Query (RAG)**
```python
answer = uds3.answer_query(
    "Was regelt das Bundes-Immissionsschutzgesetz?"
)

# Result
{
    "answer": "Das BImSchG regelt...",
    "sources": [
        {"id": 1, "title": "...", "score": 0.95},
        {"id": 2, "title": "...", "score": 0.87}
    ],
    "metadata": {
        "model": "llama3.2",
        "tokens": 350,
        "duration": 2.3
    }
}
```

### **Process Management**
```python
# Speichern eines Prozesses
process_id = uds3.save_process(
    process_data={
        "name": "Baugenehmigung",
        "description": "...",
        "elements": [...]
    },
    domain="vpb"
)

# Prozess-Details abrufen
details = uds3.get_process_details(process_id)
```

---

## 🛡️ Error Handling

### **Graceful Degradation**
```python
try:
    uds3 = UDS3PolyglotManager(backend_config, enable_rag=True)
except Exception as e:
    logger.warning(f"UDS3 Init failed: {e}")
    uds3 = None  # Fallback auf Mock

# In Query-Handler
if uds3 is not None:
    results = uds3.semantic_search(query)
else:
    # Mock-Daten verwenden
    results = generate_mock_results(query)
```

### **Check Backend Availability**
```python
# Prüfe welche Backends verfügbar sind
if hasattr(uds3, 'db_manager'):
    vector_available = uds3.db_manager.vector_backend is not None
    graph_available = uds3.db_manager.graph_backend is not None
    relational_available = uds3.db_manager.relational_backend is not None
```

---

## 🔧 VERITAS Integration Patterns

### **Pattern 1: Backend API**
```python
# In veritas_api_backend_v3.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        from uds3 import UDS3PolyglotManager
        backend_config = {
            "vector": {"enabled": True, "backend": "chromadb"}
        }
        app.state.uds3 = UDS3PolyglotManager(backend_config, enable_rag=True)
        logger.info("✅ UDS3 Polyglot Manager initialisiert")
    except Exception as e:
        logger.warning(f"⚠️ UDS3 Init failed: {e}")
        app.state.uds3 = None
    
    yield
    
    # Shutdown
    if hasattr(app.state, 'uds3') and app.state.uds3:
        # Cleanup if needed
        pass
```

### **Pattern 2: Intelligent Pipeline**
```python
# In veritas_intelligent_pipeline.py

class IntelligentMultiAgentPipeline:
    def __init__(self):
        self.uds3_strategy: Optional[UDS3PolyglotManager] = None
        
    async def initialize(self):
        if RAG_INTEGRATION_AVAILABLE:
            try:
                backend_config = {
                    "vector": {"enabled": True, "backend": "chromadb"}
                }
                self.uds3_strategy = UDS3PolyglotManager(
                    backend_config, enable_rag=True
                )
                logger.info("✅ UDS3 Polyglot Manager initialized")
            except Exception as e:
                logger.warning(f"⚠️ UDS3 Init failed: {e}")
                self.uds3_strategy = None
```

### **Pattern 3: Agent System**
```python
# In veritas_api_agent_registry.py

class SharedResourcePool:
    def get_database_api(self):
        if not self._uds3_strategy:
            try:
                backend_config = {
                    "vector": {"enabled": True, "backend": "chromadb"}
                }
                self._uds3_strategy = UDS3PolyglotManager(
                    backend_config, enable_rag=True
                )
            except Exception as e:
                logger.error(f"UDS3 Init failed: {e}")
        
        return self._database_api, self._uds3_strategy
```

---

## 📚 Mock-Klassen (Fallback)

### **Mock Polyglot Manager**
```python
# In veritas_intelligent_pipeline.py

class UDS3PolyglotManager:
    """Mock UDS3 Polyglot Manager für Fallback"""
    def __init__(self, backend_config=None, enable_rag=True, **kwargs):
        pass
    
    def semantic_search(self, query_text, top_k=10):
        return []  # Leere Ergebnisse
    
    def answer_query(self, query_text):
        return {"answer": "", "sources": []}
```

### **IEEE Mock Sources**
```python
# In veritas_intelligent_pipeline.py

def _generate_mock_ieee_sources(self) -> List[Dict[str, Any]]:
    """Generiert Mock-IEEE-Quellen für Demo"""
    mock_sources = [
        {
            'id': 1,
            'title': 'Bundes-Immissionsschutzgesetz (BImSchG) - Kommentar',
            'authors': 'Bundesministerium für Umwelt et al.',
            'year': 2023,
            'similarity_score': 0.9234,
            'rerank_score': 0.9456,
            'impact': 'High',
            'relevance': 'Very High',
            'ieee_citation': '[1] Bundesministerium...',
            # ... weitere 30+ Felder
        }
    ]
    return random.sample(mock_sources, random.randint(3, 5))
```

---

## ⚙️ Environment Variables

### **UDS3 Konfiguration**
```bash
# RAG Mode
export VERITAS_RAG_MODE=auto        # auto, disabled, mock

# Backend Aktivierung
export UDS3_VECTOR_ENABLED=true
export UDS3_GRAPH_ENABLED=false
export UDS3_RELATIONAL_ENABLED=false

# Paths
export UDS3_CHROMADB_PATH=data/chromadb
export UDS3_EMBEDDINGS_CACHE=data/embeddings_cache

# LLM
export UDS3_OLLAMA_URL=http://localhost:11434
export UDS3_LLM_MODEL=llama3.2
```

---

## 🔍 Debugging

### **Enable Logging**
```python
import logging
logging.getLogger('UDS3PolyglotManager').setLevel(logging.DEBUG)
logging.getLogger('backend.agents.veritas_intelligent_pipeline').setLevel(logging.INFO)
```

### **Check UDS3 Status**
```python
# In Backend
if app.state.uds3:
    logger.info("✅ UDS3 Active")
    logger.info(f"  Vector: {app.state.uds3.db_manager.vector_backend is not None}")
else:
    logger.warning("⚠️ UDS3 Demo Mode")
```

### **Test Query**
```python
# Minimal Test
try:
    results = uds3.semantic_search("Test Query")
    logger.info(f"✅ UDS3 works: {len(results)} results")
except Exception as e:
    logger.error(f"❌ UDS3 error: {e}")
```

---

## 📖 Additional Resources

- **UDS3 Docs**: `c:\VCC\uds3\README.md`
- **Polyglot Manager**: `c:\VCC\uds3\core\polyglot_manager.py`
- **Search API**: `c:\VCC\uds3\docs\UDS3_SEARCH_API_PRODUCTION_GUIDE.md`
- **Migration Report**: `c:\VCC\veritas\docs\UDS3_V2_MIGRATION_COMPLETE.md`

---

## 🆘 Troubleshooting

### **Problem: "No module named 'uds3'"**
```bash
# Solution: Install UDS3
cd c:\VCC\uds3
pip install -e .
```

### **Problem: "ChromaDB not available"**
```bash
# Solution: Install ChromaDB
pip install chromadb
```

### **Problem: "Backend returns empty results"**
- **Check**: ChromaDB Collection exists?
- **Check**: Documents ingested?
- **Solution**: Use Mock-Quellen für Demo

### **Problem: "UDS3 Init fails"**
- **Check**: Alle dependencies installiert?
- **Check**: ChromaDB Server läuft?
- **Solution**: System läuft im Mock-Modus (graceful degradation)

---

**Version**: UDS3 v2.0.0  
**Last Updated**: 18. Oktober 2025  
**Author**: VERITAS Development Team
