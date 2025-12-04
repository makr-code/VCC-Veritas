# Geo Map Agent (OSM) - Orchestrator Integration

**Datum:** 2025-12-04
**Status:** ✅ PRODUKTIONSBEREIT

---

## 🎯 Integration abgeschlossen

Der **Geo Map Agent** (OSM) wurde vollständig in den VERITAS Orchestrator integriert und ist damit der **4. Visualisierungs-Agent** im System.

### ✅ Implementierte Komponenten

#### 1. Agent Registry Erweiterung

**Datei:** `backend/agents/registry/api_agent_registry.py`

**Neue AgentCapability Enum-Werte:**
```python
MAP_GENERATION = "map_generation"                # OSM Karten-Generierung
GEO_DATA_PROCESSING = "geo_data_processing"      # Geodaten-Verarbeitung
```

#### 2. Domain Agent Registrierung

**Datei:** `backend/agents/registry/domain_agent_registration.py`

**Registrierter Agent:**
- **Agent ID:** `geo_map`
- **Agent Class:** `GeoSubAgent`
- **Lifecycle:** SINGLETON (max_instances=1)
- **Capabilities:**
  - MAP_GENERATION
  - GEO_DATA_PROCESSING
  - DATA_ANALYSIS
- **Priority:** 8
- **Status:** ✅ Registriert

**Capability Mapping:**
```python
"geo_map": [
    AgentCapability.MAP_GENERATION,
    AgentCapability.GEO_DATA_PROCESSING,
    AgentCapability.DATA_ANALYSIS
]
```

#### 3. Task Blueprint

**Datei:** `backend/agents/orchestrator/agent_orchestrator.py`

```python
"map_generation": {
    "stage": "response_generation",
    "capability": "map_generation",
    "priority": 0.7,
    "parallel": True,
    "depends_on": ["data_analysis"],  # Benötigt Geo-Daten
}
```

**Eigenschaften:**
- **Stage:** response_generation (frühe Pipeline-Phase)
- **Priority:** 0.7 (gleich wie chart_generation)
- **Parallel:** True (kann parallel zu anderen Visualisierungen laufen)
- **Dependencies:** data_analysis (benötigt Geo-Daten-Abruf)

#### 4. Map Dispatcher

**Datei:** `backend/agents/orchestrator/visualization_dispatcher.py`

**Neue Funktion:** `dispatch_map_generation()` (~70 LOC)

```python
async def dispatch_map_generation(
    context: Dict[str, Any],
    geo_data: Optional[list[Dict[str, Any]]] = None,
    map_spec: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
```

**Features:**
- Async Geodaten-Abruf aus ThemisDB/BImSchG/WKA
- Koordinaten-Transformation (ETRS89 → WGS84)
- OSM Karten-Rendering (Matplotlib)
- Brandenburg-optimierte Defaults
- GeoJSON-Export
- PNG/Base64 Export

**Return-Format:**
```python
{
    "status": "success",
    "agent_type": "geo_map",
    "image_base64": "...",
    "png_path": "/tmp/veritas_geo/map_1234.png",
    "geojson": {...},
    "feature_count": 5
}
```

---

## 🧪 Integration Test

**Testskript:** `test_visualization_orchestrator.py`

### Test-Ergebnisse (2025-12-04 13:13:51)

```
Step 6: Testing map dispatcher...
  Status: success
  Features: 5
  PNG: \tmp\veritas_geo\map_1764850433622.png

=== INTEGRATION TEST COMPLETE ===

✅ ALL SYSTEMS INTEGRATED:
  - Agent Registry: 4/4 visualization agents registered
  - Task Blueprints: 4/4 blueprints added
  - Dispatcher: 4/4 dispatch functions operational
```

### Registry Capability Check

```
MAP_GENERATION: 1 agent (geo_map)
```

---

## 📊 Geo Map Agent Features

### Kernfunktionen

1. **Koordinaten-Transformation**
   - ETRS89 UTM Zone 33N → WGS84
   - Brandenburg-Validierung
   - pyproj-basiert

2. **Geodaten-Quellen**
   - BImSchG-Anlagen (~4,062 Standorte)
   - WKA-Anlagen (~5,457 Standorte)
   - ThemisDB Geo-Collections
   - Beispieldaten für Tests

3. **Karten-Generierung**
   - Statische PNG-Karten (Matplotlib)
   - Marker-basierte Visualisierung
   - Color-coding nach Quelle
   - Auto-Bounds für Brandenburg
   - Titel und Legenden

4. **Export-Formate**
   - PNG (lokaler Pfad)
   - Base64 (für Web-Integration)
   - GeoJSON (für Web-Mapping)

### Technologie-Stack

- **pyproj ≥ 3.6.0** - Koordinaten-Transformation
- **matplotlib ≥ 3.8.0** - Karten-Rendering
- **Pillow ≥ 10.1.0** - Bildverarbeitung

---

## 🔧 Verwendung

### Im Orchestrator

Der Orchestrator kann jetzt automatisch OSM-Karten basierend auf Geo-Daten erstellen:

```python
# Beispiel: Automatische Map-Generierung
if query_needs_geo_map(context):
    agents = registry.get_agents_for_capability(AgentCapability.MAP_GENERATION)
    # Orchestrator wählt geo_map
```

### Über Dispatcher

```python
from backend.agents.orchestrator.visualization_dispatcher import dispatch_map_generation

context = {
    'geo_query': {
        'source': 'bimschg',
        'filters': {'category': '1.1'}
    },
    'map_spec': {
        'title': 'BImSchG-Anlagen Brandenburg',
        'center': [52.5, 13.0],
        'zoom': 8,
        'style': 'markers'
    }
}

result = await dispatch_map_generation(context)

if result['status'] == 'success':
    print(f"Map generated: {result['png_path']}")
    print(f"Features: {result['feature_count']}")
```

### Über API (bereits vorhanden)

```bash
POST /api/geo/query
POST /api/geo/map
POST /api/geo/transform
```

---

## 🎯 Integration mit anderen Visualisierungs-Agents

### Kombinierte Verwendung

**Beispiel-Pipeline:**

```
data_analysis → geo_data_query
    ↓
map_generation (OSM Karte)
    ↓
chart_generation (Statistik-Charts)
    ↓
presentation_creation (PowerPoint mit Karte + Charts)
```

### Presentation Canvas Integration

Der Geo Map Agent kann direkt mit dem Presentation Canvas Agent kombiniert werden:

```python
# VDL-Element für Geo-Karten
{
    "type": "geo_map",
    "properties": {
        "source": "bimschg",
        "center": [52.5, 13.0],
        "zoom": 8,
        "title": "BImSchG-Anlagen"
    }
}
```

---

## 📈 Code-Statistiken

**Modifizierte Module:** 3
- `api_agent_registry.py` (2 neue Capabilities)
- `domain_agent_registration.py` (~25 LOC für geo_map Registration)
- `agent_orchestrator.py` (1 Task Blueprint)

**Neue Module:** 0 (Agent bereits vorhanden)

**Dispatcher-Erweiterung:**
- `visualization_dispatcher.py` (+70 LOC für map_dispatcher)

**Gesamt LOC hinzugefügt:** ~95 LOC

---

## 🚀 Produktionsstatus

### ✅ Checkliste

- [x] Agent Registry erweitert (2 Capabilities)
- [x] Geo Map Agent registriert (SINGLETON)
- [x] Task Blueprint hinzugefügt (map_generation)
- [x] Map Dispatcher implementiert
- [x] Integrationstests erfolgreich
- [x] Async/await Support
- [x] Error Handling
- [x] Dokumentation vollständig

### Deployment-Status

**Bereit für Produktionsumgebung:**
- Alle Tests bestanden ✅
- Keine kritischen Fehler ✅
- GeoSubAgent bereits in Produktion (API) ✅
- Performance validiert ✅

---

## 🌍 Brandenburg-Optimierung

### Geo-Bounds

**Default-Center:** [52.5°N, 13.0°E] (Brandenburg Zentrum)

**Brandenburg Bounding Box:**
- Latitude: 51.3° - 53.6° N
- Longitude: 11.3° - 14.8° E

**UTM Zone 33N (ETRS89):**
- Ostwert: 350000 - 600000 m
- Nordwert: 5700000 - 5950000 m

---

## 📚 Existierende Dokumentation

**Hauptdokumentation:** `docs/components/GEO_SUB_AGENT_README.md`

**Tests:** `tests/agents/test_geo_sub_agent.py` (36 Tests)

**API-Endpoints:** `backend/api/geo_endpoints.py`

---

## 🎊 Zusammenfassung

Der **Geo Map Agent** ist jetzt vollständig in den VERITAS Orchestrator integriert:

✅ **4/4 Visualisierungs-Agents vollständig orchestriert:**
1. Chart Engine - Diagramme
2. Presentation Canvas - PowerPoint
3. Image Generation - AI-Bilder
4. **Geo Map - OSM Karten** ← NEU

Der LLM-Orchestrator kann jetzt automatisch:
- OSM-Karten für Geo-Queries erstellen
- Geodaten transformieren (ETRS89 → WGS84)
- BImSchG/WKA-Standorte visualisieren
- Karten in Präsentationen integrieren

**Integration abgeschlossen am:** 2025-12-04 13:13:51
**Status:** ✅ PRODUCTION READY
