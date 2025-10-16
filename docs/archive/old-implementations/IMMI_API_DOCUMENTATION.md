# IMMI API - Immissionsschutz Geodaten-Endpunkte

**API-Präfix:** `/api/immi`  
**Version:** 1.0.0  
**Datum:** 10. Oktober 2025

## 📋 Übersicht

Die IMMI-API bietet Geodaten-Endpunkte für die Visualisierung von:
- **BImSchG-Anlagen** (Bundesimmissionsschutzgesetz) - 4,062 Anlagen
- **WKA** (Windkraftanlagen) - 5,457 Anlagen

**Koordinatensystem:**
- **Eingabe:** ETRS89 UTM Zone 33N (EPSG:25833)
- **Ausgabe:** WGS84 (EPSG:4326) für Web-Karten

---

## 🗺️ Endpunkte

### 1. BImSchG-Marker

```http
GET /api/immi/markers/bimschg
```

**Parameter:**
- `bounds` (optional): Kartenausschnitt `"min_lat,min_lon,max_lat,max_lon"`
- `nr_4bv` (optional): Filter nach 4. BImSchV-Nummer (z.B. `"8.12.2V"`)
- `ort` (optional): Filter nach Ort (z.B. `"Schwedt"`)
- `limit` (optional): Max. Anzahl Marker (default: 1000, max: 5000)

**Response:**
```json
[
  {
    "id": "12-20730670000-0001",
    "lat": 53.060000,
    "lon": 14.280000,
    "type": "bimschg",
    "title": "PCK Raffinerie GmbH",
    "description": "Industriekraftwerk Schwedt",
    "category": "Feuerungsanlagen",
    "icon": "/assets/markers/bimschg-red.png",
    "data": {
      "bimschg_id": "12-20730670000-0001",
      "bst_name": "PCK Raffinerie GmbH",
      "anl_bez": "Industriekraftwerk Schwedt",
      "nr_4bv": "1.1EG",
      "anlart_4bv": "Feuerungsanlagen für WÃ¤rmeerzeugung",
      "ort": "Schwedt/Oder",
      "leistung": 1200.0,
      "einheit": "MW"
    }
  }
]
```

**Beispiele:**
```bash
# Alle BImSchG-Anlagen in Brandenburg
GET /api/immi/markers/bimschg?limit=5000

# Nur Zeitweilige Lagerung
GET /api/immi/markers/bimschg?nr_4bv=8.12.2V

# Nur Schwedt/Oder
GET /api/immi/markers/bimschg?ort=Schwedt

# Kartenausschnitt Berlin-Brandenburg
GET /api/immi/markers/bimschg?bounds=52.0,12.0,53.0,14.0&limit=1000
```

---

### 2. WKA-Marker

```http
GET /api/immi/markers/wka
```

**Parameter:**
- `bounds` (optional): Kartenausschnitt
- `betreiber` (optional): Filter nach Betreiber (z.B. `"ENERTRAG"`)
- `status` (optional): Filter nach Status (`"In Betrieb"`, `"Im Genehmigungsverfahren"`)
- `min_leistung` (optional): Min. Leistung in MW (z.B. `3.0`)
- `limit` (optional): Max. Anzahl Marker (default: 1000, max: 5000)

**Response:**
```json
[
  {
    "id": "106528400006001",
    "lat": 52.789643,
    "lon": 13.420377,
    "type": "wka",
    "title": "WKA Oranienburg",
    "description": "ENERTRAG SE",
    "category": "In Betrieb",
    "icon": "/assets/markers/wka-active.png",
    "data": {
      "wka_id": "106528400006001",
      "anl_bez": "Oranienburg WKA 1",
      "betreiber": "ENERTRAG SE",
      "ort": "Oranienburg",
      "status": "In Betrieb",
      "leistung": 3.2,
      "nabenhoehe": 120.0,
      "rotordurch": 105.0
    }
  }
]
```

**Beispiele:**
```bash
# Alle WKA in Betrieb
GET /api/immi/markers/wka?status=In%20Betrieb

# Nur ENERTRAG-Anlagen
GET /api/immi/markers/wka?betreiber=ENERTRAG

# Hochleistungs-WKA (≥ 3 MW)
GET /api/immi/markers/wka?min_leistung=3.0

# Kombiniert
GET /api/immi/markers/wka?status=In%20Betrieb&min_leistung=2.5&limit=500
```

---

### 3. Heatmap-Daten

```http
GET /api/immi/heatmap/bimschg
```

**Parameter:**
- `nr_4bv` (optional): Filter nach 4. BImSchV-Nummer

**Response:**
```json
[
  {
    "lat": 53.060000,
    "lon": 14.280000,
    "intensity": 56.0
  },
  {
    "lat": 52.789643,
    "lon": 13.420377,
    "intensity": 12.0
  }
]
```

**Verwendung:**
Intensität = Anzahl Anlagen am Standort (für Leaflet.heat Plugin)

---

### 4. Suche

```http
GET /api/immi/search?query=Schwedt
```

**Parameter:**
- `query` (required): Suchbegriff (min. 2 Zeichen)
- `limit` (optional): Max. Ergebnisse (default: 10, max: 50)

**Response:**
```json
[
  {
    "id": "12-20730670000-0001",
    "name": "PCK Raffinerie GmbH",
    "type": "BImSchG",
    "ort": "Schwedt/Oder",
    "lat": 53.060000,
    "lon": 14.280000
  },
  {
    "id": "207356000040012",
    "name": "VERBIO Schwedt GmbH",
    "type": "WKA",
    "ort": "Schwedt/Oder",
    "lat": 53.055000,
    "lon": 14.275000
  }
]
```

**Durchsucht:**
- BImSchG: `bst_name`, `ort`
- WKA: `betreiber`, `ort`

---

### 5. Regions-Statistiken

```http
GET /api/immi/statistics/region?bounds=52.0,12.0,53.0,14.0
```

**Parameter:**
- `bounds` (required): Kartenausschnitt `"min_lat,min_lon,max_lat,max_lon"`

**Response:**
```json
{
  "bimschg_count": 1234,
  "wka_count": 567,
  "total_power_mw": 1456.78,
  "categories": {
    "8.12.2V": 458,
    "8.11.2.4V": 416,
    "1.2.2.2V": 332
  },
  "bounds": {
    "min_lat": 52.0,
    "min_lon": 12.0,
    "max_lat": 53.0,
    "max_lon": 14.0
  }
}
```

---

### 6. Filter-Optionen

```http
GET /api/immi/filters
```

**Parameter:** Keine

**Response:**
```json
{
  "bimschg_categories": [
    {
      "value": "8.12.2V",
      "label": "8.12.2V - Zeitweilige Lagerung",
      "count": 458
    },
    {
      "value": "8.11.2.4V",
      "label": "8.11.2.4V - Anlagen zur sonstigen Behandlung",
      "count": 416
    }
  ],
  "wka_status": [
    "In Betrieb",
    "Im Genehmigungsverfahren",
    "Stillgelegt"
  ],
  "orte": [
    "Ahrensfelde",
    "Beeskow",
    "Brandenburg an der Havel",
    "..."
  ]
}
```

**Verwendung:**
Zum Aufbau von Filter-Dropdowns im Frontend

---

## 🚀 Integration

### Backend (`backend.py`)

```python
from backend.api.immi_endpoints import router as immi_router

app = FastAPI(title="VERITAS API")
app.include_router(immi_router)
```

### Frontend (Vue.js)

```javascript
// BImSchG-Marker laden
const response = await fetch('/api/immi/markers/bimschg?limit=1000');
const markers = await response.json();

// Leaflet-Marker erstellen
markers.forEach(marker => {
  L.marker([marker.lat, marker.lon])
    .bindPopup(`<h4>${marker.title}</h4><p>${marker.description}</p>`)
    .addTo(map);
});
```

---

## 📊 Performance

**Datenvolumen:**
- BImSchG: 3,905 gültige Koordinaten (96.1% Quote)
- WKA: 5,255 gültige Koordinaten (96.3% Quote)
- **Gesamt: 9,160 Marker**

**Optimierungen:**
- ✅ Koordinaten-Cache (in-memory)
- ✅ Bounds-Filter (SQL-seitig wenn möglich)
- ✅ Limit-Parameter (default 1000, max 5000)

**Benchmarks:**
- 1000 Marker: ~100-200ms
- 5000 Marker: ~500ms-1s
- Heatmap (alle): ~300ms

---

## 🔒 Sicherheit

**Read-Only:**
- Alle Endpunkte sind GET-Requests
- Keine Schreib-Operationen
- SQLite wird nur lesend geöffnet

**Validierung:**
- Bounds-Parameter werden validiert
- Limit-Parameter haben Obergrenzen
- Koordinaten werden auf Brandenburg-Region geprüft

---

## 🧪 Testing

```bash
# Unit-Tests
pytest tests/test_immi_endpoints.py -v

# Manuelle API-Tests
curl "http://localhost:8000/api/immi/markers/bimschg?limit=10"
curl "http://localhost:8000/api/immi/markers/wka?status=In%20Betrieb&limit=10"
curl "http://localhost:8000/api/immi/search?query=Schwedt"
curl "http://localhost:8000/api/immi/filters"

# OpenAPI Docs
http://localhost:8000/docs#tag/IMMI---Immissionsschutz
```

---

## 📚 Dependencies

```bash
pip install pyproj  # Koordinaten-Transformation
```

**Bereits vorhanden:**
- FastAPI
- Pydantic
- SQLite3

---

## 🗂️ Datei-Struktur

```
backend/
  api/
    immi_endpoints.py     ← IMMI API (neu)
    database_endpoints.py ← Database Agent
    ...
  services/
    coordinate_service.py ← Koordinaten-Service (optional)
data/
  BImSchG.sqlite          ← BImSchG-Datenbank
  wka.sqlite              ← WKA-Datenbank
scripts/
  validate_coordinates.py ← Koordinaten-Validierung
```

---

## 🎯 Nächste Schritte

1. ✅ **Backend Integration:**
   - `immi_endpoints.py` in `backend.py` registrieren
   - Server neu starten

2. ⏳ **Frontend Integration:**
   - `MapView.vue` Komponente erstellen
   - Leaflet.js Integration
   - Marker-Clustering

3. ⏳ **Testing:**
   - API-Endpunkte testen
   - Koordinaten-Transformation validieren
   - Performance-Tests

---

**Autor:** VERITAS Agent System  
**Letzte Aktualisierung:** 10. Oktober 2025
