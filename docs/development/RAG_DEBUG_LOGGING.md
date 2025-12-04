# Debug-Logging für RAG-Integration

**Datum:** 05.10.2025, 20:45 Uhr
**Status:** 🔍 Debug-Logging hinzugefügt

## Problem

Backend zeigt:
```
WARNING: ⚠️ RAG Backend fehlgeschlagen – wechsle auf Mock-Daten:
Keine ausführbare RAG-Schnittstelle gefunden
```

Aber:
- UDS3 ist importiert ✅
- UDS3 Strategy ist initialisiert ✅
- Backend hat Daten ✅

**Warum funktioniert es nicht?**

## Debug-Strategie

### 1. Logging hinzugefügt

**File:** `backend/agents/rag_context_service.py`

#### Zeile 117-118: Check ob Methode existiert
```python
query_method = getattr(self.uds3_strategy, "query_across_databases", None)
logger.info(f"🔍 UDS3 query_across_databases: {query_method is not None and callable(query_method)}")
```

**Output zeigt:**
- ✅ TRUE = Methode existiert und ist callable
- ❌ FALSE = Methode fehlt oder nicht callable

#### Zeile 135-137: Query-Parameter
```python
logger.info(f"📊 UDS3 Query: vector={vector_params is not None}, graph={graph_params is not None}, relational={relational_params is not None}")
```

**Output zeigt:** Welche Datenbanken abgefragt werden

#### Zeile 149: Erfolg
```python
logger.info(f"✅ UDS3 query_across_databases erfolgreich aufgerufen")
```

#### Zeile 153: Fehler-Details
```python
except Exception as e:
    logger.error(f"❌ UDS3 query_across_databases fehlgeschlagen: {e}")
```

**Output zeigt:** Warum die Methode fehlschlägt

#### Zeile 158: Fallback-Check
```python
unified_query = getattr(self.uds3_strategy, "unified_query", None)
logger.info(f"🔍 UDS3 unified_query (Fallback): {unified_query is not None and callable(unified_query)}")
```

#### Zeile 164: Fallback-Fehler
```python
except Exception as e:
    logger.error(f"❌ UDS3 unified_query (Fallback) fehlgeschlagen: {e}")
```

### 2. Try-Except um beide Methoden

**Vorher:** Keine Exception-Behandlung → erste Exception stoppt alles

**Nachher:** Try-Except um beide Methoden → Fallback möglich

## Erwartete Log-Ausgaben

### Scenario 1: `query_across_databases` funktioniert

```
INFO: 🔍 UDS3 query_across_databases: True
INFO: 📊 UDS3 Query: vector=True, graph=True, relational=True
INFO: ✅ UDS3 query_across_databases erfolgreich aufgerufen
```

### Scenario 2: `query_across_databases` fehlt, `unified_query` funktioniert

```
INFO: 🔍 UDS3 query_across_databases: False
INFO: 🔍 UDS3 unified_query (Fallback): True
INFO: ✅ UDS3 unified_query (Fallback) erfolgreich aufgerufen
```

### Scenario 3: Beide Methoden fehlen

```
INFO: 🔍 UDS3 query_across_databases: False
INFO: 🔍 UDS3 unified_query (Fallback): False
WARNING: ⚠️ RAG Backend fehlgeschlagen – wechsle auf Mock-Daten:
         Keine ausführbare RAG-Schnittstelle gefunden
```

### Scenario 4: Methode existiert, aber Exception

```
INFO: 🔍 UDS3 query_across_databases: True
INFO: 📊 UDS3 Query: vector=True, graph=True, relational=True
ERROR: ❌ UDS3 query_across_databases fehlgeschlagen: [EXCEPTION DETAILS]
INFO: 🔍 UDS3 unified_query (Fallback): False
WARNING: ⚠️ RAG Backend fehlgeschlagen – wechsle auf Mock-Daten:
         Keine ausführbare RAG-Schnittstelle gefunden
```

## Next Steps

### 1. Backend neu starten

```powershell
python start_backend.py
```

### 2. Test-Query ausführen

```bash
curl -X POST http://localhost:5000/v2/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Was steht im Taschengeldparagraphen?"}'
```

### 3. Logs analysieren

Im Backend-Log nach folgenden Zeilen suchen:
- `🔍 UDS3 query_across_databases:`
- `📊 UDS3 Query:`
- `✅ UDS3 ... erfolgreich`
- `❌ UDS3 ... fehlgeschlagen:`

### 4. Basierend auf Logs entscheiden:

#### Fall A: Methode fehlt
```
🔍 UDS3 query_across_databases: False
🔍 UDS3 unified_query (Fallback): False
```
**Lösung:** UDS3-Methode implementieren oder Adapter erstellen

#### Fall B: Exception bei Aufruf
```
✅ UDS3 query_across_databases: True
❌ UDS3 query_across_databases fehlgeschlagen: [ERROR]
```
**Lösung:** Exception-Details analysieren, Parameter anpassen

#### Fall C: Funktioniert!
```
✅ UDS3 query_across_databases erfolgreich aufgerufen
```
**Lösung:** Keine - weiter testen!

## Dateien geändert

### `backend/agents/rag_context_service.py`

**Zeilen 114-154:** Debug-Logging für `query_across_databases`
- Check ob Methode existiert
- Query-Parameter loggen
- Success/Error logging
- Try-Except um Methodenaufruf

**Zeilen 156-169:** Debug-Logging für `unified_query` (Fallback)
- Check ob Fallback-Methode existiert
- Success/Error logging
- Try-Except um Fallback

## Testing Checklist

Nach Backend-Neustart:

- [ ] Log zeigt: `✅ RAG Integration (UDS3) verfügbar`
- [ ] Log zeigt: `✅ UDS3 Strategy initialisiert`
- [ ] Test-Query ausführen
- [ ] Log zeigt: `🔍 UDS3 query_across_databases: True` oder `False`
- [ ] Bei `True`: Log zeigt `📊 UDS3 Query:` Parameter
- [ ] Log zeigt: `✅ ... erfolgreich` ODER `❌ ... fehlgeschlagen`
- [ ] Response enthält: KEINE "Mock-Dokument 1-5"
- [ ] Response enthält: Echte Dokumente aus UDS3

---

**Status:** 🔍 Debug-Logging aktiv - Backend-Neustart erforderlich
**Ziel:** Identifizieren warum RAG-Integration fehlschlägt trotz UDS3-Verfügbarkeit
**Next:** Backend neu starten und Logs analysieren
