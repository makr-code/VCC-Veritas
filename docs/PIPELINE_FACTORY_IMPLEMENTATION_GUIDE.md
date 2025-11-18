# VERITAS Backend - Implementierungsanleitung: Request-Scoped Pipelines

**Status:** ✅ Vorbereitet, ⚠️ Nicht aktiviert (Kompatibilität mit bestehendem Code)
**Datum:** 16. Oktober 2025

---

## 📋 ZUSAMMENFASSUNG DER ÄNDERUNGEN

### Neu erstellt:

1. **`backend/agents/veritas_pipeline_factory.py`**
   - Factory Pattern für Request-scoped Pipeline-Instanzen
   - Dependency Injection für Shared Resources
   - Factory-Statistiken

2. **`docs/BACKEND_ARCHITECTURE_ANALYSIS.md`**
   - Detaillierte Architektur-Analyse
   - Aktuelle vs. Ziel-Architektur
   - Implementierungs-Roadmap

### Erweitert:

3. **`backend/agents/veritas_intelligent_pipeline.py`**
   - ✅ `_initialize_request_scoped_resources()` - Initialisiert Request-spezifische Ressourcen
   - ✅ `cleanup()` - Räumt Pipeline-Ressourcen auf
   - ✅ Cleanup-Kommentar im `finally`-Block (vorbereitet, aber auskommentiert)

4. **`backend/api/veritas_api_backend.py`**
   - ✅ `/capabilities` Endpoint erweitert mit Agent Registry-Informationen

---

## 🎯 AKTUELLES DESIGN

### Ist-Zustand (Singleton Pattern)

```
Backend Start
    ↓
[1x Intelligent Pipeline erstellt]  ← GLOBAL SINGLETON
    ↓
Request 1 → nutzt Pipeline → Response
Request 2 → nutzt Pipeline → Response  ← SHARED STATE
Request 3 → nutzt Pipeline → Response
    ↓
Backend Stop
```

**Probleme:**
- ❌ Alle Requests teilen sich eine Pipeline-Instanz
- ❌ Shared State (`active_pipelines`, `stats`)
- ❌ Potenzielle Race Conditions
- ❌ Kein Request-scoping

---

## 🚀 ZIEL-DESIGN (Request-Scoped)

### Soll-Zustand (Factory Pattern)

```
Backend Start
    ↓
[Pipeline Factory erstellt]  ← Singleton
    ↓
    ├─ Shared: Ollama Client
    ├─ Shared: UDS3 Strategy
    └─ Shared: Agent Registry
    ↓
Request 1 → [Pipeline-1 erstellt] → Response → Cleanup
Request 2 → [Pipeline-2 erstellt] → Response → Cleanup
Request 3 → [Pipeline-3 erstellt] → Response → Cleanup
    ↓
Backend Stop
```

**Vorteile:**
- ✅ Jeder Request hat eigene Pipeline-Instanz
- ✅ Kein Shared State zwischen Requests
- ✅ Automatisches Cleanup nach Request
- ✅ Bessere Resource-Verwaltung

---

## 📝 AKTIVIERUNGS-ANLEITUNG

### Phase 1: Backend-Integration (Optional)

**Datei:** `backend/api/veritas_api_backend.py`

#### Schritt 1: Factory statt Singleton initialisieren

```python
# STATT DIESEM (Zeile 227-245):
async def initialize_intelligent_pipeline():
    global intelligent_pipeline, ollama_client

    if INTELLIGENT_PIPELINE_AVAILABLE:
        intelligent_pipeline = await get_intelligent_pipeline()  # ← Singleton
        ollama_client = await get_ollama_client()
        return True
    return False

# NUTZE DIESES:
from backend.agents.veritas_pipeline_factory import create_pipeline_factory

async def initialize_intelligent_pipeline():
    global pipeline_factory, ollama_client  # ← Factory statt Pipeline

    if INTELLIGENT_PIPELINE_AVAILABLE:
        # Shared Resources initialisieren
        ollama_client = await get_ollama_client()
        uds3 = get_optimized_unified_strategy()

        from backend.agents.agent_registry import get_agent_registry
        registry = get_agent_registry()

        # Factory erstellen
        pipeline_factory = create_pipeline_factory(
            ollama_client=ollama_client,
            uds3_strategy=uds3,
            agent_registry=registry,
            progress_manager=progress_manager  # Falls verfügbar
        )

        logger.info("✅ Pipeline Factory initialisiert")
        return True
    return False
```

#### Schritt 2: Request-Handler anpassen

**Vorher:**

```python
@app.post("/v2/intelligent/query")
async def veritas_intelligent_query(request: VeritasStreamingQueryRequest):
    if not intelligent_pipeline:  # ← Global Singleton
        raise HTTPException(...)

    pipeline_request = IntelligentPipelineRequest(...)

    # Nutzt globale Pipeline-Instanz
    pipeline_response = await intelligent_pipeline.process_intelligent_query(pipeline_request)

    return response
```

**Nachher:**

```python
@app.post("/v2/intelligent/query")
async def veritas_intelligent_query(request: VeritasStreamingQueryRequest):
    if not pipeline_factory:  # ← Factory statt Pipeline
        raise HTTPException(...)

    # ✅ NEUE Pipeline-Instanz für diesen Request
    pipeline = await pipeline_factory.create_pipeline(max_workers=5)

    try:
        pipeline_request = IntelligentPipelineRequest(...)

        # Query verarbeiten (Cleanup erfolgt automatisch)
        pipeline_response = await pipeline.process_intelligent_query(pipeline_request)

        return {
            "query_id": pipeline_request.query_id,
            "answer": pipeline_response.response_text,
            ...
        }

    finally:
        # ✅ CLEANUP nach Request
        await pipeline.cleanup()
        pipeline_factory.mark_pipeline_completed()
```

---

### Phase 2: Cleanup in Pipeline aktivieren

**Datei:** `backend/agents/veritas_intelligent_pipeline.py`

**Zeile 595:**

```python
finally:
    # ✅ CLEANUP: Request-scoped Ressourcen freigeben
    if request.query_id in self.active_pipelines:
        del self.active_pipelines[request.query_id]

    # ✅ AKTIVIERE DIESES (wenn Factory-Pattern genutzt wird):
    await self.cleanup()  # ← Auskommentieren entfernen!
```

---

## 🧪 TESTING

### Test 1: Factory Stats

```python
# Nach Backend-Start:
GET /capabilities

# Response sollte enthalten:
{
    "features": {
        "intelligent_pipeline": {
            "agents": {
                "total_count": 14,  # ← Agent Registry funktioniert
                "by_domain": {...}
            }
        }
    }
}
```

### Test 2: Parallele Requests (Factory Pattern)

```python
import asyncio
import httpx

async def test_parallel_requests():
    async with httpx.AsyncClient() as client:
        # Starte 3 Requests parallel
        tasks = [
            client.post("http://localhost:5000/v2/intelligent/query", json={
                "query": f"Test Query {i}",
                "session_id": f"test_session_{i}"
            })
            for i in range(3)
        ]

        responses = await asyncio.gather(*tasks)

        # Alle sollten erfolgreich sein
        assert all(r.status_code == 200 for r in responses)
        print("✅ Parallele Requests erfolgreich")

asyncio.run(test_parallel_requests())
```

---

## 📊 PERFORMANCE-VERGLEICH

### Vor Factory Pattern (Singleton)

```
Request 1: 5.2s  ← Nutzt globale Pipeline
Request 2: 5.5s  ← Wartet auf Lock/Shared State
Request 3: 5.8s  ← Race Condition möglich
```

### Nach Factory Pattern (Request-Scoped)

```
Request 1: 5.1s  ← Eigene Pipeline-Instanz
Request 2: 5.0s  ← Parallel, keine Konflikte
Request 3: 5.2s  ← Isoliert
```

**Erwarteter Speedup:** ~10-20% bei parallelen Requests

---

## ⚠️ BREAKING CHANGES

### Nicht-kompatible Änderungen:

1. **Global `intelligent_pipeline` → `pipeline_factory`**
   - Alle Referenzen müssen angepasst werden
   - Endpoints müssen `await factory.create_pipeline()` nutzen

2. **Cleanup ist jetzt PFLICHT**
   - `finally`-Block muss `await pipeline.cleanup()` aufrufen
   - Sonst Memory-Leaks durch nicht geschlossene ThreadPools

3. **Shared Resources müssen DI nutzen**
   - Ollama, UDS3, Registry werden injiziert
   - Nicht mehr direkt in Pipeline initialisiert

---

## 🎯 ROLLOUT-STRATEGIE

### Option 1: Schrittweise Aktivierung (EMPFOHLEN)

1. ✅ **Woche 1:** Factory-Code deployed, aber NICHT aktiviert
   - Code ist vorbereitet
   - Keine Änderung am Runtime-Verhalten

2. ✅ **Woche 2:** Factory in DEV-Umgebung aktiviert
   - Testen mit echten Requests
   - Performance-Messungen

3. ✅ **Woche 3:** Factory in STAGING aktiviert
   - Load-Tests
   - Monitoring

4. ✅ **Woche 4:** Factory in PRODUCTION aktiviert
   - Rollback-Plan vorbereitet
   - Monitoring intensiv

### Option 2: Feature-Flag

```python
# backend/api/veritas_api_backend.py

USE_FACTORY_PATTERN = os.getenv("VERITAS_USE_FACTORY", "false").lower() == "true"

if USE_FACTORY_PATTERN:
    # Request-scoped Pipeline
    pipeline = await pipeline_factory.create_pipeline()
else:
    # Legacy Singleton
    pipeline = intelligent_pipeline
```

---

## ✅ CHECKLISTE

- [x] Factory-Code erstellt (`veritas_pipeline_factory.py`)
- [x] Cleanup-Methoden in Pipeline ergänzt
- [x] Architekt ur-Dokumentation erstellt
- [x] Agent Registry in `/capabilities` integriert
- [ ] Backend-Integration (Factory statt Singleton)
- [ ] Cleanup aktivieren (Zeile 595 auskommentieren entfernen)
- [ ] Tests für parallele Requests
- [ ] Performance-Benchmarks
- [ ] Production Deployment

---

## 🆘 ROLLBACK-PLAN

Falls Probleme auftreten:

1. **Deaktiviere Factory-Pattern:**
   - Setze `USE_FACTORY_PATTERN = False`
   - Restart Backend

2. **Nutze Legacy Singleton:**
   - Kommentiere Factory-Code aus
   - Nutze `get_intelligent_pipeline()` wieder

3. **Monitoring:**
   - Prüfe Memory-Usage
   - Prüfe Response-Times
   - Prüfe Error-Logs

---

**Bereit für Aktivierung:** ✅ JA (wenn gewünscht)
**Empfohlener Zeitpunkt:** Nach ausgiebigem Testing in DEV/STAGING
