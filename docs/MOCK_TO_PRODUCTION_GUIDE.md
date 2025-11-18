# VERITAS Mock zu Production Migration Guide

## 🚨 Aktueller Status

### Backend Mockups (AKTIV):

1. **`/v2/query`** ← Frontend nutzt diesen
   - 📍 Datei: `backend/api/veritas_api_backend.py` Zeile 772
   - ❌ Status: 100% Mock-Daten
   - 🔧 Simuliert: Agent-Ergebnisse, Antworten, Quellen
   - 📊 Gibt zurück: Hardcodierte Texte wie "Die Anfrage bezieht sich auf..."

2. **`/ask`**
   - 📍 Datei: `backend/api/veritas_api_backend.py` Zeile 990
   - ❌ Status: 100% Mock (Test-Implementation)
   - 🔧 Gibt zurück: "Test RAG-Antwort für: ..."

### Production-Ready Endpoints (UNGENUTZT):

3. **`/v2/intelligent/query`** ← ECHTE PIPELINE!
   - 📍 Datei: `backend/api/veritas_api_backend.py` Zeile 333
   - ✅ Status: Produktiv
   - 🧠 Features:
     - IntelligentMultiAgentPipeline
     - Ollama LLM Integration
     - RAG-basierte Agent-Selektion
     - Multi-Agent Orchestration
     - Real-time LLM Commentary
   - ⚠️ Problem: Frontend nutzt es NICHT

---

## 🔧 Migration Option 1: `/v2/query` auf echte Pipeline umstellen

### Änderungen in `backend/api/veritas_api_backend.py`:

```python
@app.post("/v2/query")
async def veritas_chat_query(query_data: Dict[str, Any]):
    """
    MAIN ENDPOINT für Veritas Chat-App Integration
    Nutzt jetzt die echte Intelligent Pipeline!
    """
    start_time = time.time()

    try:
        query_text = query_data.get('query', '')
        if not query_text:
            raise HTTPException(status_code=400, detail="Query ist erforderlich")

        session_id = query_data.get('session_id', str(uuid.uuid4()))
        enable_streaming = query_data.get('enable_streaming', False)

        # PRODUKTIV: Nutze Intelligent Pipeline statt Mock
        if INTELLIGENT_PIPELINE_AVAILABLE and intelligent_pipeline:
            # Erstelle Pipeline Request
            pipeline_request = IntelligentPipelineRequest(
                query_id=f"query_{uuid.uuid4().hex[:8]}",
                query_text=query_text,
                user_context={"session_id": session_id, "mode": query_data.get('mode', 'veritas')},
                session_id=session_id,
                enable_llm_commentary=False,  # Für schnellere Antworten
                enable_real_time_updates=enable_streaming,
                max_parallel_agents=5,
                timeout=60
            )

            # Pipeline ausführen
            pipeline_response = await intelligent_pipeline.process_intelligent_query(pipeline_request)
            processing_time = time.time() - start_time

            # Response im erwarteten Format
            return {
                'response_text': pipeline_response.response_text,
                'confidence_score': pipeline_response.confidence_score,
                'sources': pipeline_response.sources,
                'worker_results': pipeline_response.agent_results,
                'agent_results': pipeline_response.agent_results,
                'rag_context': pipeline_response.rag_context,
                'follow_up_suggestions': pipeline_response.follow_up_suggestions,
                'processing_metadata': {
                    'complexity': 'intelligent',
                    'processing_time': processing_time,
                    'agent_count': len(pipeline_response.agent_results),
                    'successful_agents': len(pipeline_response.agent_results),
                    'system_mode': 'intelligent_pipeline',
                    'streaming_available': STREAMING_AVAILABLE,
                    'timestamp': datetime.now().isoformat()
                }
            }
        else:
            # FALLBACK: Mock-Daten (wenn Pipeline nicht verfügbar)
            logger.warning("⚠️ Intelligent Pipeline nicht verfügbar - nutze Mock-Daten")
            return _generate_mock_response(query_text, session_id)

    except Exception as e:
        logger.error(f"❌ Fehler bei Query: {e}")
        return _generate_error_response(str(e))


def _generate_mock_response(query_text: str, session_id: str):
    """Fallback Mock-Daten"""
    # ... bestehender Mock-Code ...
```

### Vorteile:
- ✅ Keine Frontend-Änderung nötig
- ✅ Sofortige echte LLM-Integration
- ✅ Echter RAG mit Dokumenten-Suche
- ✅ Graceful Fallback bei Fehler

### Nachteile:
- ⚠️ Benötigt laufende Ollama-Installation
- ⚠️ Benötigt konfigurierte Dokumente/Datenbank

---

## 🔧 Migration Option 2: Frontend auf `/v2/intelligent/query` umstellen

### Änderungen in `frontend/veritas_app.py`:

```python
def _send_to_backend(self, message: str):
    # ... bestehender Code ...

    # Erstelle Request für Intelligent Pipeline
    request_payload = {
        "query": message,
        "session_id": self.session_id,
        "enable_streaming": False,
        "enable_intermediate_results": False,
        "enable_llm_thinking": False  # oder True für LLM Commentary
    }

    # Sende an Intelligent Pipeline Endpoint
    logger.info(f"🧠 Sende Query an /v2/intelligent/query")
    api_response = requests.post(
        f"{API_BASE_URL}/v2/intelligent/query",
        json=request_payload,
        timeout=60
    )

    # Response-Format ist kompatibel!
    # answer, confidence_score, sources, agent_results, etc.
```

### Vorteile:
- ✅ Nutzt dedizierte Pipeline-Endpoint
- ✅ Zugriff auf LLM Commentary (optional)
- ✅ Bessere Trennung Mock/Prod

### Nachteile:
- ⚠️ Frontend-Änderung nötig
- ⚠️ Anderes Response-Format (aber ähnlich)

---

## 📊 Empfehlung: **Option 1**

Ändere `/v2/query` Backend-Endpoint, um echte Pipeline zu nutzen:

1. **Sofortige Produktivität**: Frontend funktioniert ohne Änderung
2. **Sauberer Fallback**: Mock-Daten bei Pipeline-Fehler
3. **Schrittweise Migration**: Kann später optimiert werden

---

## ✅ Checkliste vor Production:

### Backend:
- [ ] IntelligentMultiAgentPipeline initialisiert
- [ ] Ollama läuft und ist erreichbar
- [ ] LLM-Modelle heruntergeladen (llama3.1:latest etc.)
- [ ] RAG-Dokumente importiert
- [ ] UDS3 Datenbanken konfiguriert (optional)

### Frontend:
- [ ] API_BASE_URL korrekt (aktuell: http://127.0.0.1:5000)
- [ ] Error-Handling für Pipeline-Fehler
- [ ] Timeout erhöht für echte LLM-Anfragen (60s+)

### Testing:
- [ ] Test-Query mit echter Pipeline: `curl POST /v2/intelligent/query`
- [ ] Frontend-Test mit echter Backend-Antwort
- [ ] Fehlerfall-Test (Pipeline nicht verfügbar)

---

## 🚀 Quick-Start Migration:

```bash
# 1. Prüfe ob Pipeline verfügbar
curl http://localhost:5000/health

# Sollte zeigen:
# "intelligent_pipeline_available": true
# "ollama_available": true

# 2. Test echte Pipeline
curl -X POST http://localhost:5000/v2/intelligent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Was ist VERITAS?", "session_id": "test", "enable_streaming": false}'

# 3. Wenn erfolgreich: Ersetze /v2/query Implementation im Backend
# 4. Starte Backend neu
# 5. Frontend testen - sollte echte Antworten bekommen
```

---

## 📝 Aktueller Code-Status:

### Mock-Code in `/v2/query` (Zeile 772-898):
```python
# Simulierte Agent-Ergebnisse (wie im Test-Backend)
agent_results = {
    'geo_context': {
        'response_text': f'Geo-Kontext für Query: {query_text[:50]}...',
        # ... FAKE DATEN
    }
}

# Simuliere finale Antwort
main_response = f"""
**Antwort auf Ihre Frage**: {query_text}
**Geo-Kontext**: Die Anfrage bezieht sich auf den lokalen Verwaltungsbereich.
# ... HARDCODIERT
"""
```

### Produktiv-Code in `/v2/intelligent/query` (Zeile 377):
```python
# Pipeline ausführen - ECHT!
pipeline_response = await intelligent_pipeline.process_intelligent_query(pipeline_request)

# ECHTE Antworten vom LLM
# ECHTE RAG-Dokumente
# ECHTE Agent-Orchestration
```

---

## 🎯 Nächste Schritte:

1. **Entscheidung**: Option 1 oder Option 2?
2. **Backup**: Aktuellen `/v2/query` Code sichern
3. **Migration**: Code ersetzen
4. **Testen**: Mit echten Queries testen
5. **Monitoring**: Logs beobachten für Fehler

**Empfehlung: Option 1 - Backend `/v2/query` auf echte Pipeline umstellen**
