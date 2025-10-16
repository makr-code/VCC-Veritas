# 🚀 VERITAS Agent Integration - Action Plan

**Ziel**: Von Mock-Daten zu echten spezialisierten Agenten  
**Aufwand**: 2-4 Stunden  
**Impact**: 🔴 CRITICAL - User bekommen echte Expertise statt Platzhalter

---

## 📋 Phase 1: Proof of Concept (30 Min)

### Schritt 1.1: Test BuildingPermitWorker Standalone

**Datei**: `tests/test_building_permit_agent.py` (NEU)

```python
import asyncio
from backend.agents.veritas_api_agent_construction import BuildingPermitWorker

async def test_building_permit():
    """Teste BuildingPermitWorker direkt"""
    
    agent = BuildingPermitWorker()
    
    query = "Baugenehmigung für Anbau in München"
    metadata = {
        'query': query,
        'location': 'München',
        'project_type': 'Anbau'
    }
    
    result = await agent._process_internal(metadata)
    
    print("=== BuildingPermitWorker Test ===")
    print(f"Query: {query}")
    print(f"Result: {result}")
    print(f"Sources: {result.get('sources', [])}")
    print(f"Summary: {result.get('summary', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_building_permit())
```

**Erwartung**:
- ✅ Agent funktioniert standalone
- ✅ Gibt echte Baugenehmigung-Logik zurück
- ✅ Keine Mock-Daten

**Falls Fehler**:
- Prüfe Dependencies (externe APIs)
- Prüfe ob Agent-Klasse richtig importiert
- Checke Logs

---

### Schritt 1.2: Test EnvironmentalAgent Standalone

**Datei**: `tests/test_environmental_agent.py` (NEU)

```python
import asyncio
from backend.agents.veritas_api_agent_environmental import EnvironmentalAgent

async def test_environmental():
    """Teste EnvironmentalAgent direkt"""
    
    agent = EnvironmentalAgent()
    
    query = "Luftqualität und Umweltbelastung in Berlin"
    
    result = await agent.process_query(query)
    
    print("=== EnvironmentalAgent Test ===")
    print(f"Query: {query}")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_environmental())
```

---

## 📋 Phase 2: Integration in Intelligent Pipeline (1 Std)

### Schritt 2.1: Erweitere `_execute_real_agent()`

**Datei**: `backend/agents/veritas_intelligent_pipeline.py`  
**Zeile**: ~1745

**ÄNDERUNG**:

```python
def _execute_real_agent(self, agent_type: str, query: str, rag_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Führt echten VERITAS Agent aus
    
    Priorität:
    1. Spezialisierter Agent (falls vorhanden)
    2. UDS3 Hybrid Search (falls verfügbar)
    3. Mock Fallback (nur als letztes Mittel)
    """
    
    # 🆕 SCHRITT 1: Versuche spezialisierten Agent
    specialized_result = self._try_specialized_agent(agent_type, query, rag_context)
    if specialized_result and not specialized_result.get('is_mock'):
        logger.info(f"✅ Spezialisierter Agent '{agent_type}' erfolgreich")
        return specialized_result
    
    # SCHRITT 2: Versuche UDS3 (bestehender Code)
    try:
        if self.uds3_strategy:
            # ... bestehende UDS3 Logik ...
            if sources and summaries:
                logger.info(f"✅ UDS3 Search für '{agent_type}' erfolgreich")
                return {...}
    except Exception as e:
        logger.warning(f"⚠️ UDS3 Search für '{agent_type}' fehlgeschlagen: {e}")
    
    # SCHRITT 3: Fallback auf Mock
    logger.warning(f"⚠️ Fallback auf Mock für '{agent_type}'")
    result = self._generate_mock_agent_result(agent_type, query)
    result['is_simulation'] = True  # ← Transparenz!
    result['simulation_reason'] = 'Specialized agent and UDS3 not available'
    return result


def _try_specialized_agent(self, agent_type: str, query: str, rag_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    🆕 NEU: Versucht spezialisierten Agent aufzurufen
    
    Returns:
        Agent-Ergebnis oder None falls Agent nicht verfügbar
    """
    
    # Agent-Mapping
    agent_class_mapping = {
        'construction': ('backend.agents.veritas_api_agent_construction', 'BuildingPermitWorker'),
        'environmental': ('backend.agents.veritas_api_agent_environmental', 'EnvironmentalAgent'),
        'social': ('backend.agents.veritas_api_agent_social', 'SocialBenefitsWorker'),
        'financial': ('backend.agents.veritas_api_agent_financial', 'FinancialAgent'),
        'traffic': ('backend.agents.veritas_api_agent_traffic', 'TrafficAgent'),
        'weather': ('backend.agents.veritas_api_agent_dwd_weather', 'DwdWeatherAgent'),
        'technical_standards': ('backend.agents.veritas_api_agent_technical_standards', 'TechnicalStandardsAgent'),
    }
    
    mapping = agent_class_mapping.get(agent_type)
    if not mapping:
        return None
    
    module_name, class_name = mapping
    
    try:
        # Dynamisch importieren
        module = __import__(module_name, fromlist=[class_name])
        agent_class = getattr(module, class_name)
        
        # Agent instanziieren
        agent_instance = agent_class()
        
        # Metadata vorbereiten
        metadata = {
            'query': query,
            'rag_context': rag_context
        }
        
        # Agent ausführen
        result = None
        if asyncio.iscoroutinefunction(agent_instance._process_internal):
            # Async Agent
            result = asyncio.run(agent_instance._process_internal(metadata))
        else:
            # Sync Agent
            result = agent_instance._process_internal(metadata)
        
        if result:
            # Standardisiere Format
            return {
                'agent_type': agent_type,
                'status': 'completed',
                'confidence_score': result.get('confidence_score', 0.80),
                'summary': result.get('summary', result.get('details', '')),
                'sources': result.get('sources', []),
                'processing_time': result.get('processing_time', 2.0),
                'details': result.get('details', ''),
                'specialized_agent_used': True  # ← Markierung
            }
        
    except ImportError as e:
        logger.debug(f"ℹ️ Agent '{agent_type}' nicht importierbar: {e}")
    except AttributeError as e:
        logger.debug(f"ℹ️ Agent-Klasse '{class_name}' nicht gefunden: {e}")
    except Exception as e:
        logger.warning(f"⚠️ Fehler beim Ausführen von Agent '{agent_type}': {e}")
    
    return None
```

---

### Schritt 2.2: Import-Statements hinzufügen

**Datei**: `backend/agents/veritas_intelligent_pipeline.py`  
**Zeile**: ~1-50 (Import-Bereich)

**HINZUFÜGEN**:

```python
import asyncio
from typing import Optional
```

---

## 📋 Phase 3: Integration in Backend API (1 Std)

### Schritt 3.1: Nutze Intelligent Pipeline für Streaming

**Datei**: `backend/api/veritas_api_backend.py`  
**Zeile**: ~950-1010 (`_process_streaming_query`)

**ÄNDERUNG**:

**ALT**:
```python
# Generiere Mock-Agent-Results
agent_results = {}
for agent_type in selected_agents:
    agent_results[agent_type] = _generate_agent_result(agent_type, request.query, complexity)
    # ← 🔴 MOCK-DATEN
```

**NEU**:
```python
# 🆕 Nutze Intelligent Pipeline auch für Streaming
if INTELLIGENT_PIPELINE_AVAILABLE and intelligent_pipeline:
    # Pipeline Request erstellen
    pipeline_request = IntelligentPipelineRequest(
        query_text=request.query,
        query_id=str(uuid.uuid4()),
        session_id=request.session_id,
        user_context={"user_id": "stream_user"},
        enable_llm_commentary=False,  # Für Performance
        enable_supervisor=False
    )
    
    # Agent Execution über Pipeline
    agent_selection = {'selected_agents': selected_agents}
    rag_context = {}
    
    context = {
        'agent_selection': agent_selection,
        'rag': rag_context
    }
    
    # Nutze Pipeline's Agent Execution
    agent_results_raw = await intelligent_pipeline._step_parallel_agent_execution(
        pipeline_request,
        context
    )
    
    # Extrahiere Results
    agent_results = agent_results_raw.get('detailed_results', {})
else:
    # Fallback: Alte Mock-Logik
    logger.warning("⚠️ Intelligent Pipeline nicht verfügbar, Fallback auf Mock")
    agent_results = {}
    for agent_type in selected_agents:
        result = _generate_agent_result(agent_type, request.query, complexity)
        result['is_simulation'] = True  # ← Transparenz
        agent_results[agent_type] = result
```

---

### Schritt 3.2: Simulation-Warnung beibehalten

**Datei**: `backend/api/veritas_api_backend.py`  
**Zeile**: ~1260-1285

**KEINE ÄNDERUNG** - Bestehende Simulation-Warnung bleibt!

**Warum?**
- Falls spezialisierte Agenten nicht verfügbar → Mock als Fallback
- Warnung zeigt an welche Bereiche simuliert sind
- Transparenz bleibt erhalten

---

## 📋 Phase 4: Testing (1 Std)

### Schritt 4.1: Unit Tests

**Datei**: `tests/test_intelligent_pipeline_agents.py` (NEU)

```python
import asyncio
import pytest
from backend.agents.veritas_intelligent_pipeline import IntelligentMultiAgentPipeline

@pytest.mark.asyncio
async def test_execute_real_agent_construction():
    """Test ob BuildingPermitWorker über Pipeline aufgerufen wird"""
    
    pipeline = IntelligentMultiAgentPipeline()
    await pipeline.initialize()
    
    result = pipeline._execute_real_agent(
        agent_type='construction',
        query='Baugenehmigung München',
        rag_context={}
    )
    
    # Assertions
    assert result is not None
    assert result.get('agent_type') == 'construction'
    assert 'specialized_agent_used' in result or 'uds3_used' in result or 'is_simulation' in result
    
    # Prüfe ob es KEIN Mock ist
    if not result.get('is_simulation'):
        assert result.get('specialized_agent_used') or result.get('uds3_used')
        print(f"✅ Echter Agent genutzt: {result.get('summary')}")
    else:
        print(f"⚠️ Mock genutzt: {result.get('simulation_reason')}")

@pytest.mark.asyncio
async def test_execute_real_agent_environmental():
    """Test EnvironmentalAgent"""
    
    pipeline = IntelligentMultiAgentPipeline()
    await pipeline.initialize()
    
    result = pipeline._execute_real_agent(
        agent_type='environmental',
        query='Luftqualität Berlin',
        rag_context={}
    )
    
    assert result is not None
    assert result.get('agent_type') == 'environmental'
```

**Ausführen**:
```bash
pytest tests/test_intelligent_pipeline_agents.py -v
```

---

### Schritt 4.2: Integration Test

**Datei**: `tests/test_streaming_with_real_agents.py` (NEU)

```python
import asyncio
import aiohttp
import json

async def test_streaming_endpoint_with_agents():
    """Test /v2/query/stream mit echten Agenten"""
    
    query = "Baugenehmigung für Anbau in München"
    
    async with aiohttp.ClientSession() as session:
        payload = {
            "query": query,
            "session_id": "test_session_123"
        }
        
        async with session.post(
            'http://localhost:5000/v2/query/stream',
            json=payload
        ) as response:
            
            async for line in response.content:
                if line:
                    try:
                        event = line.decode('utf-8')
                        if event.startswith('data: '):
                            data = json.loads(event[6:])
                            
                            if data.get('event') == 'STREAM_COMPLETE':
                                final_result = data.get('final_result', {})
                                worker_results = final_result.get('worker_results', {})
                                
                                print("=== Agent Results ===")
                                for agent, result in worker_results.items():
                                    is_sim = result.get('is_simulation', False)
                                    specialized = result.get('specialized_agent_used', False)
                                    
                                    status = "🔴 MOCK" if is_sim else ("✅ SPECIALIZED" if specialized else "✅ REAL")
                                    print(f"{agent}: {status}")
                                    print(f"  Summary: {result.get('summary', 'N/A')[:100]}")
                                
                                # Assertion
                                construction_result = worker_results.get('construction', {})
                                assert not construction_result.get('is_simulation'), \
                                    "Construction agent should use specialized agent, not mock!"
                                
                    except json.JSONDecodeError:
                        pass

if __name__ == "__main__":
    asyncio.run(test_streaming_endpoint_with_agents())
```

**Ausführen**:
```bash
# Backend starten
python start_backend.py

# In neuem Terminal
python tests/test_streaming_with_real_agents.py
```

---

### Schritt 4.3: Frontend Manual Test

**Schritte**:
1. Start Backend: `python start_backend.py`
2. Start Frontend: `python start_frontend.py`
3. Öffne Browser: http://localhost:7860
4. Test-Queries:
   - "Baugenehmigung für Anbau in München"
   - "Luftqualität und Umweltbelastung in Berlin"
   - "Sozialleistungen für Familien"
5. **Prüfe**:
   - Erscheint "⚠️ DEMO-MODUS" Warnung?
   - Falls JA: Welche Bereiche sind betroffen?
   - Falls NEIN: Agenten funktionieren! ✅

---

## 📋 Phase 5: Monitoring & Rollout (30 Min)

### Schritt 5.1: Logging erweitern

**Datei**: `backend/agents/veritas_intelligent_pipeline.py`  
**In `_try_specialized_agent()`**:

**HINZUFÜGEN**:
```python
logger.info(f"✅ Spezialisierter Agent '{agent_type}' ({class_name}) erfolgreich ausgeführt")
logger.info(f"   Confidence: {result.get('confidence_score', 0.0):.2f}")
logger.info(f"   Sources: {len(result.get('sources', []))} Quellen")
```

---

### Schritt 5.2: Metrics erfassen

**Datei**: `backend/agents/veritas_intelligent_pipeline.py`  
**In `__init__`**:

**HINZUFÜGEN**:
```python
self.stats['specialized_agents_used'] = 0
self.stats['specialized_agents_failed'] = 0
self.stats['uds3_queries'] = 0
self.stats['mock_fallbacks'] = 0
```

**In `_try_specialized_agent()`**:
```python
if result:
    self.stats['specialized_agents_used'] += 1
    return result
else:
    self.stats['specialized_agents_failed'] += 1
    return None
```

**In `_execute_real_agent()`**:
```python
if self.uds3_strategy:
    self.stats['uds3_queries'] += 1
    # ...
    
if is_mock_fallback:
    self.stats['mock_fallbacks'] += 1
```

---

### Schritt 5.3: Health Check Endpoint

**Datei**: `backend/api/veritas_api_backend.py`

**HINZUFÜGEN**:
```python
@app.get("/v2/agents/health")
async def agents_health_check():
    """Health Check für Agent-System"""
    
    if not INTELLIGENT_PIPELINE_AVAILABLE or not intelligent_pipeline:
        return {
            "status": "unavailable",
            "message": "Intelligent Pipeline not available"
        }
    
    stats = intelligent_pipeline.get_stats()
    
    specialized_agents_used = stats.get('specialized_agents_used', 0)
    mock_fallbacks = stats.get('mock_fallbacks', 0)
    total = specialized_agents_used + mock_fallbacks
    
    specialized_percentage = (specialized_agents_used / total * 100) if total > 0 else 0
    
    status = "healthy" if specialized_percentage > 50 else "degraded" if specialized_percentage > 0 else "mock_only"
    
    return {
        "status": status,
        "statistics": {
            "specialized_agents_used": specialized_agents_used,
            "specialized_agents_failed": stats.get('specialized_agents_failed', 0),
            "uds3_queries": stats.get('uds3_queries', 0),
            "mock_fallbacks": mock_fallbacks,
            "specialized_percentage": round(specialized_percentage, 2)
        },
        "agents_available": list(intelligent_pipeline._try_specialized_agent.__code__.co_consts)  # Agent-Liste
    }
```

**Test**:
```bash
curl http://localhost:5000/v2/agents/health
```

---

## ✅ Erfolgs-Kriterien

### Minimum Viable Product (MVP):
- ✅ BuildingPermitWorker läuft über Intelligent Pipeline
- ✅ `/v2/query/stream` nutzt Intelligent Pipeline statt Mock
- ✅ Frontend zeigt keine Simulation-Warnung bei Construction-Queries
- ✅ Logging zeigt "✅ Spezialisierter Agent ... erfolgreich"

### Optimal:
- ✅ 3+ spezialisierte Agenten integriert (Construction, Environmental, Social)
- ✅ Specialized Agent Usage > 50%
- ✅ Health Check Endpoint gibt "healthy" Status
- ✅ Frontend Tests zeigen echte Agent-Ergebnisse

---

## 🚨 Fallback Plan

### Falls spezialisierte Agenten nicht funktionieren:

**Plan B**: UDS3 Integration reparieren

1. **Prüfe**: `backend/agents/veritas_api_agent_registry.py`
2. **Finde**: `get_optimized_unified_strategy()` Funktion
3. **Debug**: Warum gibt sie `None` zurück?
4. **Repariere**: UDS3 Database Connection
5. **Aktiviere**: `UDS3_AVAILABLE = True`

**Ergebnis**:
- Generic UDS3 Search statt spezialisierte Agenten
- Immer noch besser als Mock!

---

## 📊 Zeitplan

| Phase | Dauer | Status |
|-------|-------|--------|
| **Phase 1**: Proof of Concept | 30 Min | ⏳ Pending |
| **Phase 2**: Pipeline Integration | 1 Std | ⏳ Pending |
| **Phase 3**: Backend API Integration | 1 Std | ⏳ Pending |
| **Phase 4**: Testing | 1 Std | ⏳ Pending |
| **Phase 5**: Monitoring & Rollout | 30 Min | ⏳ Pending |
| **GESAMT** | **4 Std** | |

---

## 🎯 Nächster Schritt

**START HIER**:

```bash
# Test BuildingPermitWorker standalone
python tests/test_building_permit_agent.py
```

**Falls erfolgreich** → Weiter zu Phase 2  
**Falls Fehler** → Debug Agent-Implementierung

**Bereit?** Los geht's! 🚀
