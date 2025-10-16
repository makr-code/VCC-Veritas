# VERITAS - Simulation & Mock Status Zusammenfassung

**Datum**: 16. Oktober 2025  
**Prüfung**: Backend & Frontend auf Simulationen/Stubs

---

## 🎯 Kernergebnisse

### ✅ **POSITIV: Conversation History Integration**
- **Status**: Vollständig implementiert, KEINE Simulation
- **Code**: Echt, funktioniert wie designed
- **Test**: ✅ Erfolgreich (siehe `test_conversation_history.py`)
- **Frontend**: Sendet letzte 10 Nachrichten korrekt
- **Backend**: Verarbeitet Kontext und zeigt `**Gesprächskontext**:` Abschnitt

### ✅ **POSITIV: Frontend**
- **Status**: Nutzt echte Backend-Daten
- **Mocks**: Keine gefunden
- **Code-Qualität**: Sauber, keine Fake-Daten

### 🔴 **KRITISCH: Agent Results - Komplett simuliert**

**Problem**: 
Alle 8 Agenten (`geo_context`, `legal_framework`, `construction`, etc.) liefern **100% hardcodierte Daten**

**Code-Location**: `backend/api/veritas_api_backend.py`, Zeilen 1050-1203

**Was ist simuliert**:
```python
agent_specialties = {
    'geo_context': {
        'summary': 'Geografischer Kontext...',  # ← HARDCODED
        'sources': ['OpenStreetMap', 'Gemeinde-DB']  # ← FAKE QUELLEN
    },
    'legal_framework': {
        'summary': 'Rechtliche Rahmenbedingungen...',  # ← HARDCODED
        'sources': ['BauGB', 'VwVfG', 'GemO']  # ← FAKE QUELLEN
    },
    # ... 6 weitere Agenten mit Fake-Daten
}

return {
    'confidence_score': 0.8 + (random),  # ← ZUFÄLLIG
    'processing_time': 1.0 + (random),  # ← FAKE
    'sources': specialty['sources']  # ← HARDCODED
}
```

**Impact**:
- ❌ Jede Query bekommt **gleiche generische Antwort**
- ❌ Quellen sind **erfunden**, nicht aus Datenbank
- ❌ Keine **regionalen Unterschiede** (München = Stuttgart = Berlin)
- ❌ Keine **echte Recherche** passiert

**Grund**:
- UDS3 API fehlt (siehe `docs/UDS3_REAL_AGENT_INTEGRATION_PLAN.md`)
- `uds3_strategy = None` → Fallback auf Simulation läuft immer

---

## 📊 Vollständige Liste der Simulationen

### 🔴 **HIGH Priority - Sofort beheben**

| # | Location | Type | Status | Impact |
|---|----------|------|--------|--------|
| 1 | `_generate_agent_result()` | Agent Results | 🔴 Alle simuliert | HOCH - User sehen Fake-Daten |
| 2 | `/api/uds3/search` Endpoint | UDS3 Search | 🔴 Mock Response | HOCH - API gibt Fake zurück |

### 🟡 **MEDIUM Priority**

| # | Location | Type | Status | Impact |
|---|----------|------|--------|--------|
| 3 | `agents_success_rate: 1.0` | Statistik | 🟡 Hardcoded | MITTEL - Monitoring falsch |

### ✅ **LOW Priority - Umbenennen**

| # | Location | Type | Status | Impact |
|---|----------|------|--------|--------|
| 4 | `mock_session` Variable | Naming | ⚠️ Falscher Name | GERING - Code funktioniert |

---

## 🛠️ Empfohlene Fixes

### Fix 1: Simulation-Warnung anzeigen (Sofort)

**Ziel**: User informieren dass Demo-Daten genutzt werden

**Backend** (`backend/api/veritas_api_backend.py`):
```python
# Zeile ~1200 - In _generate_agent_result() Fallback-Block:
logger.warning(f"⚠️  SIMULATION: {agent_type} nutzt hardcoded Daten (UDS3 nicht verfügbar)")

return {
    'agent_type': agent_type,
    'confidence_score': base_confidence + (0.1 * hash(query + agent_type) % 3 / 10),
    'summary': specialty['summary'],
    'sources': specialty['sources'],
    'status': 'completed',
    'is_simulation': True,  # 🆕 NEU
    'simulation_reason': 'UDS3 database not available',  # 🆕 NEU
    'data_quality': 'simulated'  # 🆕 NEU
}
```

**Backend** (`backend/api/veritas_api_backend.py`):
```python
# Zeile ~1270 - In _synthesize_final_response():
simulated_agents = [
    agent for agent, result in agent_results.items() 
    if result.get('is_simulation', False)
]

if simulated_agents:
    main_response += f'''

⚠️  **DEMO-MODUS**: Diese Antwort basiert auf simulierten Beispieldaten.
   Betroffene Bereiche: {', '.join(simulated_agents)}
   Grund: UDS3-Datenbank nicht verfügbar.
   
'''
```

**Frontend** (`frontend/veritas_app.py`):
```python
# Zeile ~590 - In _handle_backend_response():
metadata = response_data.get('metadata', {})
if metadata.get('has_simulation') or any(
    r.get('is_simulation') for r in response_data.get('worker_results', {}).values()
):
    formatted_content = "⚠️  **DEMO-MODUS - Beispieldaten**\n\n" + formatted_content
```

### Fix 2: UDS3 Integration (Mittelfristig)

**Siehe**: `docs/UDS3_REAL_AGENT_INTEGRATION_PLAN.md`

**Schritte**:
1. UDS3 API-Problem lösen (fehlende `UnifiedDatabaseStrategy`)
2. `uds3_strategy` korrekt initialisieren
3. Echte Queries implementieren
4. Simulation nur als Fallback bei Fehlern

### Fix 3: Mock Endpoint deaktivieren (Sofort)

**Backend** (`backend/api/veritas_api_backend.py`):
```python
# Zeile ~1813 - /api/uds3/search Endpoint:
@app.post("/api/uds3/search")
async def uds3_search_endpoint(request: UDS3SearchRequest):
    raise HTTPException(
        status_code=501,
        detail={
            "error": "UDS3 Search API not implemented",
            "alternative": "Use /v2/query/stream endpoint instead",
            "status": "not_implemented"
        }
    )
```

---

## 📋 Test-Checkliste

Nach Implementierung der Fixes:

- [ ] **Backend neu starten**
  ```powershell
  .\scripts\stop_services.ps1
  .\scripts\start_services.ps1 -BackendOnly
  ```

- [ ] **Test 1: Simulation-Warnung erscheint**
  - Frontend starten
  - Query: "Baugenehmigung München"
  - ✅ Prüfen: Warnung "⚠️ DEMO-MODUS" erscheint

- [ ] **Test 2: Backend-Logs zeigen Warnung**
  ```powershell
  Get-Job | Receive-Job -Keep | Select-String "SIMULATION"
  ```
  - ✅ Erwartung: `⚠️ SIMULATION: geo_context nutzt hardcoded Daten`

- [ ] **Test 3: Agent Results enthalten Simulation-Flag**
  ```python
  result = _generate_agent_result('geo_context', 'test', 'standard')
  assert result['is_simulation'] == True
  assert 'simulation_reason' in result
  ```

- [ ] **Test 4: UDS3 Mock Endpoint disabled**
  ```powershell
  curl -X POST http://localhost:5000/api/uds3/search -d '{"query":"test"}'
  ```
  - ✅ Erwartung: HTTP 501 Not Implemented

---

## 📚 Dokumentation

### Erstellt:
1. ✅ `docs/SIMULATION_MOCK_ANALYSIS_REPORT.md` - Detaillierte Analyse
2. ✅ `docs/CHAT_HISTORY_INTEGRATION.md` - Chat-Verlauf Doku
3. ✅ `docs/MANUAL_FRONTEND_TEST.md` - Test-Anleitung
4. ✅ `scripts/show_simulation_fix.py` - Fix-Empfehlungen

### Besteht:
- `docs/UDS3_REAL_AGENT_INTEGRATION_PLAN.md` - UDS3 Integration Plan
- `docs/STREAMING_DISPLAY_FIX.md` - Streaming Fix Doku

---

## 🎯 Nächste Schritte

### Sofort (heute):
1. ✅ Simulation-Warnung implementieren (30 Min)
2. ✅ Mock UDS3 Endpoint deaktivieren (5 Min)
3. ✅ Backend neu starten und testen (10 Min)

### Kurzfristig (diese Woche):
4. ⏳ UDS3 API-Problem analysieren
5. ⏳ Alternative Datenquelle evaluieren (PostgreSQL direkt?)

### Mittelfristig (nächste Woche):
6. ⏳ Echte Agent Results implementieren
7. ⏳ UDS3 Integration abschließen
8. ⏳ Demo-Modus optional machen

---

## ✅ Fazit

**Conversation History**: ✅ Voll funktional, keine Probleme  
**Frontend**: ✅ Nutzt echte Backend-Daten  
**Agent Results**: 🔴 **Kritisch - Komplett simuliert**

**Hauptproblem**: UDS3-Datenbank-Integration fehlt  
**Sofort-Lösung**: Transparenz durch Warnung  
**Langfristig**: Echte Datenbank-Integration
