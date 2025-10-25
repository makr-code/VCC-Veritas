# Frontend Integration Guide - Backend v4.0.0

**Version:** 4.0.0  
**Date:** 19. Oktober 2025  
**Status:** Migration Guide

---

## 🎯 Ziel

Integration des neuen **Unified Backend v4.0.0** in das Streamlit Frontend.

### Änderungen:

| Vorher | Nachher |
|--------|---------|
| `/ask`, `/v2/query`, `/vpb/ask` | `/api/query` (unified) |
| 3-4 verschiedene Response-Formate | `UnifiedResponse` |
| Manuelle Source-Parsing | `SourceMetadata` mit IEEE-Feldern |
| Verschiedene Payloads pro Modus | Einheitliche Payload-Struktur |

---

## 📦 Neue API Client Klasse

### Installation

Die neue `VeritasAPIClient` Klasse ist in `frontend/api_client.py`:

```python
from frontend.api_client import VeritasAPIClient, UnifiedResponse

# Create client
client = VeritasAPIClient(
    base_url="http://localhost:5000",
    session_id="sess_123"
)

# Query
response: UnifiedResponse = client.query(
    query="Was regelt das BImSchG?",
    mode="rag",
    model="llama3.2"
)
```

---

## 🔄 Migration Schritte

### 1. Import API Client

**Vorher (`veritas_app.py`):**
```python
import requests

# Direct requests.post()
response = requests.post(f"{API_BASE_URL}/ask", json=payload)
```

**Nachher:**
```python
from frontend.api_client import VeritasAPIClient, UnifiedResponse

# In __init__:
self.api_client = VeritasAPIClient(
    base_url=API_BASE_URL,
    session_id=self.session_id
)

# Use client:
response: UnifiedResponse = self.api_client.query(
    query=message,
    mode="rag",
    model=llm
)
```

---

### 2. Query-Methode anpassen

**Vorher (`send_message()` in `veritas_app.py`):**

```python
# Zeilen ~5940-6050

# Endpoint basierend auf Modus
endpoint = "/ask"
if hasattr(self, 'current_question_mode'):
    endpoints = self.current_question_mode.get('endpoints', ['/ask'])
    endpoint = endpoints[0]

# Payload zusammenstellen
payload = {
    "question": message,
    "session_id": self.session_id,
    "temperature": self.temperature_var.get(),
    "max_tokens": self.max_tokens_var.get(),
    "model": llm,
    # ...
}

# API-Anfrage
api_response = requests.post(
    f"{API_BASE_URL}{endpoint}",
    json=payload,
    timeout=60
)

if api_response.status_code == 200:
    response_data = api_response.json()
    answer = response_data.get('answer', '')
    sources = response_data.get('sources', [])
    # ...
```

**Nachher:**

```python
# Zeilen ~5940-6050 (angepasst)

# Bestimme Modus
mode = "rag"  # Standard
if hasattr(self, 'current_question_mode'):
    mode = self.current_question_mode.get('key', 'rag')

# API-Anfrage via Client
try:
    unified_response: UnifiedResponse = self.api_client.query(
        query=message,
        mode=mode,
        model=llm,
        temperature=self.temperature_var.get(),
        max_tokens=self.max_tokens_var.get(),
        top_k=5,
        conversation_history=self._get_conversation_history()
    )
    
    # Response verarbeiten
    answer = unified_response.content
    sources = unified_response.sources  # List[SourceMetadata]
    
    # Metadata
    duration = unified_response.metadata.duration
    tokens_used = unified_response.metadata.tokens_used
    agents = unified_response.metadata.agents_involved
    
except Exception as e:
    logger.error(f"API Error: {e}")
    self.add_error_message(f"API-Fehler: {str(e)}")
    return
```

---

### 3. Source-Parsing anpassen

**Vorher:**

```python
# Sources waren einfache Dicts
sources = response_data.get('sources', [])

for src in sources:
    src_id = src.get('id', 'unknown')
    title = src.get('title', 'Unknown')
    confidence = src.get('confidence', 0.0)
    # ... nur wenige Felder
```

**Nachher:**

```python
# Sources sind SourceMetadata-Objekte mit 35+ Feldern
sources: List[SourceMetadata] = unified_response.sources

for src in sources:
    # Basis
    src_id = src.id           # Numeric: "1", "2", "3"
    title = src.title
    
    # IEEE Extended
    authors = src.authors
    ieee_citation = src.ieee_citation
    year = src.year
    publisher = src.publisher
    
    # Scoring
    similarity = src.similarity_score
    rerank = src.rerank_score
    quality = src.quality_score
    
    # Legal Domain
    rechtsgebiet = src.rechtsgebiet
    behörde = src.behörde
    
    # Assessment
    impact = src.impact          # "High", "Medium", "Low"
    relevance = src.relevance    # "Very High", "High", ...
    
    # Extra fields
    extra = src.extra  # Dict mit weiteren Feldern
```

---

### 4. Citations anzeigen

**Vorher:**

```python
# Citations wurden manuell geparst
# Frontend musste [1], [2], [3] selbst rendern
```

**Nachher:**

```python
# Content enthält bereits [1], [2], [3]
content = unified_response.content
# "Das BImSchG regelt... [1]\n\nGenehmigung... [2]"

# Sources mit vollständigen IEEE-Daten
for src in unified_response.sources:
    # Zeige Citation-Details
    citation_html = f"""
    <div class="citation">
        <strong>[{src.id}] {src.title}</strong>
        {f'<div class="ieee">{src.ieee_citation}</div>' if src.ieee_citation else ''}
        {f'<div class="authors">{src.authors}</div>' if src.authors else ''}
        <div class="scores">
            {f'Similarity: {src.similarity_score:.2f}' if src.similarity_score else ''}
            {f' | Quality: {src.quality_score:.2f}' if src.quality_score else ''}
        </div>
        {f'<div class="impact">Impact: {src.impact}</div>' if src.impact else ''}
        {f'<div class="rechtsgebiet">{src.rechtsgebiet}</div>' if src.rechtsgebiet else ''}
    </div>
    """
```

---

### 5. Modi anpassen

**Vorher (`_fetch_available_modes()`):**

```python
# Zeilen ~4490-4560

# Verschiedene Endpoints pro Modus
available_modes = [
    {'key': 'veritas', 'endpoints': ['/v2/query'], ...},
    {'key': 'vpb', 'endpoints': ['/vpb/ask'], ...},
    {'key': 'chat', 'endpoints': ['/v2/query'], ...}
]
```

**Nachher:**

```python
# Alle Modi nutzen /api/query mit mode-Parameter
available_modes = [
    {
        'key': 'rag',
        'display': 'VERITAS RAG',
        'description': 'Retrieval-Augmented Generation',
        'optimal': True
    },
    {
        'key': 'hybrid',
        'display': 'Hybrid Search',
        'description': 'BM25 + Dense + RRF',
        'optimal': True
    },
    {
        'key': 'streaming',
        'display': 'Streaming',
        'description': 'Real-time Progress',
        'optimal': False
    },
    {
        'key': 'agent',
        'display': 'Agent Query',
        'description': 'Multi-Agent Pipeline',
        'optimal': False
    },
    {
        'key': 'ask',
        'display': 'Simple Ask',
        'description': 'Direct LLM',
        'optimal': False
    }
]

# Oder dynamisch via API:
modes = self.api_client.get_available_modes()
```

---

## 📝 Code-Beispiele

### Vollständige Query-Funktion

```python
def send_message_v4(self, message: str, llm: str = "llama3.2"):
    """
    Sendet Message via neuen API Client (v4.0.0)
    """
    # Bestimme Modus
    mode = "rag"
    if hasattr(self, 'current_question_mode'):
        mode = self.current_question_mode.get('key', 'rag')
    
    logger.info(f"📤 Query: mode={mode}, llm={llm}")
    
    # Conversation History (optional)
    history = self._get_conversation_history() if hasattr(self, 'chat_session') else None
    
    try:
        # API Query via Client
        response: UnifiedResponse = self.api_client.query(
            query=message,
            mode=mode,
            model=llm,
            temperature=self.temperature_var.get() if hasattr(self, 'temperature_var') else 0.7,
            max_tokens=self.max_tokens_var.get() if hasattr(self, 'max_tokens_var') else 2000,
            top_k=5,
            conversation_history=history
        )
        
        # Verarbeite Response
        self._process_unified_response(response)
        
    except requests.HTTPError as e:
        logger.error(f"❌ API HTTP Error: {e}")
        self.add_error_message(f"API-Fehler: {e.response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        self.add_error_message(f"Fehler: {str(e)}")


def _process_unified_response(self, response: UnifiedResponse):
    """
    Verarbeitet UnifiedResponse
    """
    # Content
    content = response.content
    
    # Sources
    sources = response.sources
    
    # Metadata
    metadata = response.metadata
    
    logger.info(f"✅ Response: {len(sources)} sources, {metadata.duration:.2f}s")
    
    # Add to Chat
    self.add_assistant_message(
        content=content,
        sources=sources,
        metadata=metadata
    )
    
    # Update UI
    self.status_var.set(f"✅ Antwort erhalten ({metadata.duration:.2f}s)")
    
    # Show Source Details
    if sources:
        self._show_source_details(sources)


def _show_source_details(self, sources: List[SourceMetadata]):
    """
    Zeigt Source-Details (IEEE Citations)
    """
    for idx, src in enumerate(sources, 1):
        logger.info(f"[{src.id}] {src.title}")
        
        if src.ieee_citation:
            logger.info(f"   IEEE: {src.ieee_citation}")
        
        if src.similarity_score:
            logger.info(f"   Similarity: {src.similarity_score:.2f}")
        
        if src.impact:
            logger.info(f"   Impact: {src.impact}")
        
        if src.rechtsgebiet:
            logger.info(f"   Rechtsgebiet: {src.rechtsgebiet}")


def _get_conversation_history(self) -> Optional[List[Dict[str, str]]]:
    """
    Extrahiert Conversation History für Multi-Turn
    """
    if not hasattr(self, 'chat_session') or not self.chat_session:
        return None
    
    if not hasattr(self.chat_session, 'messages'):
        return None
    
    # Letzte 10 Messages
    recent = self.chat_session.messages[-10:]
    
    return [
        {
            'role': msg.role,
            'content': msg.content
        }
        for msg in recent
    ]
```

---

## 🧪 Testing

### 1. API Client testen

```python
# In Python Console oder Test-Script
from frontend.api_client import VeritasAPIClient

client = VeritasAPIClient(base_url="http://localhost:5000")

# Health Check
health = client.health_check()
print(health)  # {'status': 'healthy', ...}

# Test Query
response = client.query("Was regelt das BImSchG?", mode="rag")
print(f"Content: {response.content[:100]}")
print(f"Sources: {len(response.sources)}")

# Source Details
for src in response.sources:
    print(f"[{src.id}] {src.title}")
    if src.ieee_citation:
        print(f"  IEEE: {src.ieee_citation}")
```

### 2. Frontend Integration testen

```python
# In veritas_app.py __init__
self.api_client = VeritasAPIClient(
    base_url=API_BASE_URL,
    session_id=self.session_id
)

# Health Check beim Start
health = self.api_client.health_check()
if health.get('status') == 'healthy':
    logger.info("✅ Backend healthy")
else:
    logger.warning("⚠️  Backend not healthy")
```

---

## 📊 Änderungs-Übersicht

### Dateien zu ändern:

| Datei | Änderungen | Zeilen |
|-------|-----------|--------|
| `veritas_app.py` | API Client Integration | ~100 |
| `veritas_app.py` | Query-Methode anpassen | ~50 |
| `veritas_app.py` | Source-Parsing aktualisieren | ~30 |
| `veritas_app.py` | Modi anpassen | ~20 |
| `veritas_ui_ieee_citations.py` | IEEE-Felder erweitern | ~50 |

**Total:** ~250 Zeilen zu ändern

### Neue Dateien:

- ✅ `frontend/api_client.py` - API Client Klasse (500 Zeilen)

---

## ✅ Checkliste

### Phase 1: Setup
- [x] `frontend/api_client.py` erstellt
- [ ] API Client in `veritas_app.py` importieren
- [ ] `self.api_client` in `__init__` initialisieren
- [ ] Health Check beim Start einbauen

### Phase 2: Query Migration
- [ ] `send_message()` Methode anpassen
- [ ] Endpoint-Logic entfernen
- [ ] `api_client.query()` verwenden
- [ ] Response-Parsing auf `UnifiedResponse` umstellen

### Phase 3: Source Display
- [ ] Source-Parsing auf `SourceMetadata` umstellen
- [ ] IEEE-Felder in UI anzeigen
- [ ] Citation-Tooltips erweitern (35+ Felder)
- [ ] Impact/Relevance anzeigen

### Phase 4: Modi
- [ ] Modi-Liste auf neue Struktur umstellen
- [ ] `mode`-Parameter statt `endpoints` verwenden
- [ ] VPB/COVINA/PKI als Modi integrieren

### Phase 5: Testing
- [ ] Backend starten
- [ ] Frontend starten
- [ ] Query testen (alle Modi)
- [ ] Citations prüfen (IEEE-Felder)
- [ ] Multi-Turn testen

---

## 🚀 Nächste Schritte

1. **API Client testen:**
   ```python
   python frontend/api_client.py
   ```

2. **Integration beginnen:**
   - Import in `veritas_app.py`
   - `send_message()` anpassen

3. **UI testen:**
   - Backend starten: `python start_backend.py`
   - Frontend starten: `streamlit run frontend/veritas_app.py`

---

**Bereit für Migration? Die Struktur steht! 🚀**
