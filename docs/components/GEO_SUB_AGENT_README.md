# Geo Sub-Agent - OSM Karten & GeoInformationen

**Erstellt:** 3. Dezember 2025
**Version:** 1.0.0
**Status:** ✅ IMPLEMENTIERT

---

## 📋 Übersicht

Der **Geo Sub-Agent** ist ein spezialisierter Sub-Agent für die Verarbeitung von **OSM-Kartenmaterial** und **Geo-Informationen aus ThemisDB**. Er integriert sich nahtlos in den Presentation Canvas Agent, um geo-basierte Inhalte für Präsentationen bereitzustellen.

### Kernfunktionen

1. **Koordinaten-Transformation** - ETRS89 UTM Zone 33N → WGS84
2. **Geodaten-Abruf** - BImSchG-Anlagen, WKA-Anlagen, ThemisDB
3. **Karten-Generierung** - Statische Karten mit Matplotlib
4. **Brandenburg-Fokus** - Optimiert für Brandenburg-Geo-Daten
5. **Präsentations-Integration** - Für Canvas Agent & VDL

---

## 🗺️ Koordinaten-Transformation

### ETRS89 UTM Zone 33N → WGS84

Brandenburg nutzt das **ETRS89 UTM Zone 33N** System (EPSG:25833) für Geo-Daten:
- **Ostwert** (Easting): Rechtswert in Metern
- **Nordwert** (Northing): Hochwert in Metern

Web-Karten benötigen **WGS84** (EPSG:4326):
- **Latitude**: Breitengrad in Grad
- **Longitude**: Längengrad in Grad

**Beispiel:**
```python
from backend.agents.geo_sub_agent import CoordinateTransformer

transformer = CoordinateTransformer()

# UTM → WGS84
lat, lon = transformer.utm33n_to_wgs84(
    ostwert=480000,   # Ostwert in Metern
    nordwert=5740000  # Nordwert in Metern
)

print(f"WGS84: {lat:.6f}°N, {lon:.6f}°E")
# Output: WGS84: 51.810485°N, 14.709893°E

# Validierung
in_bb = transformer.is_valid_brandenburg(lat, lon)
print(f"In Brandenburg: {in_bb}")
# Output: In Brandenburg: True
```

### Brandenburg Bounds

```python
# Latitude: 51.3° - 53.6° N
# Longitude: 11.3° - 14.8° E

# UTM Zone 33N:
# Ostwert: 300,000 - 700,000 m
# Nordwert: 5,600,000 - 6,000,000 m
```

---

## 📍 Geodaten-Quellen

### 1. BImSchG-Anlagen

**Datenbank:** `data/BImSchG.sqlite`
**Felder:** `ostwert`, `nordwert` (ETRS89 UTM Zone 33N)
**Anzahl:** ~4,062 Anlagen mit Koordinaten

**Beispiel-Abfrage:**
```python
from backend.agents.geo_sub_agent import GeoSubAgent

agent = GeoSubAgent()

geo_data = await agent.get_geo_data({
    'source': 'bimschg',
    'filters': {'category': '1.1'},  # Feuerungsanlagen
    'bbox': [51.0, 11.0, 54.0, 15.0]  # Brandenburg
})

# Returns GeoJSON Features:
# [
#   {
#     'type': 'Feature',
#     'geometry': {
#       'type': 'Point',
#       'coordinates': [13.404954, 52.520008]  # [lon, lat]
#     },
#     'properties': {
#       'name': 'Kraftwerk Jänschwalde',
#       'category': '1.1',
#       'source': 'bimschg'
#     }
#   }
# ]
```

### 2. WKA-Anlagen (Windkraftanlagen)

**Datenbank:** `data/wka.sqlite`
**Felder:** `rechts`, `hoch` (ETRS89 UTM Zone 33N)
**Anzahl:** ~5,457 Anlagen mit Koordinaten

**Beispiel-Abfrage:**
```python
geo_data = await agent.get_geo_data({
    'source': 'wka',
    'filters': {'status': 'in_betrieb'},
    'bbox': None  # Ganz Brandenburg
})
```

### 3. ThemisDB Geo-Collections

**Datenbank:** ThemisDB (Multi-Model)
**Collections:** Beliebige Geo-Collections
**Abfrage:** Via AQL oder Geo-Queries

**Beispiel-Abfrage:**
```python
geo_data = await agent.get_geo_data({
    'source': 'themis:facilities',  # ThemisDB Collection
    'filters': {'type': 'solar'},
    'bbox': [52.0, 13.0, 53.0, 14.0]
})
```

---

## 🎨 Karten-Generierung

### Statische Karten (Matplotlib)

Der Geo Sub-Agent generiert statische PNG-Karten mit **Matplotlib**:

```python
from backend.agents.geo_sub_agent import GeoSubAgent

agent = GeoSubAgent()

# Geodaten abrufen
geo_data = await agent.get_geo_data({'source': 'bimschg'})

# Karte generieren
result = await agent.generate_map(
    geo_data=geo_data,
    map_spec={
        'center': [52.5, 13.0],  # Brandenburg Zentrum
        'zoom': 8,
        'width': 800,
        'height': 600,
        'title': 'BImSchG-Anlagen in Brandenburg',
        'style': 'markers'  # oder 'heatmap', 'cluster'
    }
)

if result['success']:
    print(f"Karte: {result['png_path']}")
    print(f"Features: {result['feature_count']}")
    print(f"Base64: {result['image_base64'][:50]}...")
```

**Generierte Karte:**
- Hintergrund: Brandenburg-Region mit Grid
- Marker: Rot (BImSchG), Grün (WKA), Blau (Sonstige)
- Labels: Anlagen-Namen
- Legende: Automatisch generiert

### Karten-Stile

1. **markers** (Standard) - Einzelne Marker mit Labels
2. **heatmap** (Zukunft) - Dichte-Visualisierung
3. **cluster** (Zukunft) - Marker-Clustering bei vielen Features

---

## 🔌 API-Verwendung

### 1. Geodaten abrufen

**Endpoint:** `POST /api/geo/query`

**Request:**
```json
{
  "source": "bimschg",
  "filters": {"category": "1.1"},
  "bbox": [51.0, 11.0, 54.0, 15.0]
}
```

**Response:**
```json
{
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [13.404954, 52.520008]
      },
      "properties": {
        "name": "Kraftwerk Jänschwalde",
        "category": "1.1",
        "source": "bimschg"
      }
    }
  ],
  "count": 5,
  "source": "bimschg"
}
```

### 2. Karte generieren

**Endpoint:** `POST /api/geo/map`

**Request:**
```json
{
  "geo_data": [...],  // GeoJSON Features
  "center": [52.5, 13.0],
  "zoom": 8,
  "width": 800,
  "height": 600,
  "title": "BImSchG-Anlagen in Brandenburg",
  "style": "markers"
}
```

**Response:**
```json
{
  "success": true,
  "image_base64": "iVBORw0KGgo...",
  "png_path": "/tmp/veritas_geo/map_123.png",
  "geojson": {...},
  "feature_count": 5
}
```

### 3. Koordinaten transformieren

**Endpoint:** `POST /api/geo/transform`

**Request:**
```json
{
  "ostwert": 480000,
  "nordwert": 5740000
}
```

**Response:**
```json
{
  "latitude": 51.810485,
  "longitude": 14.709893,
  "valid": true,
  "in_brandenburg": true
}
```

### 4. Brandenburg Bounding Box

**Endpoint:** `GET /api/geo/bbox/brandenburg`

**Response:**
```json
{
  "min_lat": 51.3,
  "min_lon": 11.3,
  "max_lat": 53.6,
  "max_lon": 14.8,
  "center": [52.45, 13.05],
  "description": "Brandenburg, Deutschland",
  "epsg_utm": "EPSG:25833",
  "epsg_wgs84": "EPSG:4326"
}
```

---

## 🎯 Integration mit Presentation Canvas Agent

### VDL-Element für Geo-Karten

```json
{
  "type": "geo_map",
  "position": {"x": 100, "y": 100},
  "size": {"width": 600, "height": 400},
  "properties": {
    "source": "bimschg",
    "filters": {"category": "1.1"},
    "center": [52.5, 13.0],
    "zoom": 8,
    "style": "markers",
    "title": "BImSchG-Anlagen in Brandenburg"
  }
}
```

### Workflow: Präsentation mit Geo-Karten

```
User Prompt
    ↓
LLM generiert VDL mit geo_map-Element
    ↓
Presentation Canvas Agent
    ↓ Erkennt geo_map
Geo Sub-Agent
    ↓ Geodaten abrufen
    ↓ Karte generieren
PNG-Karte
    ↓ In Slide einfügen
Finale Präsentation mit Geo-Karte
```

**Beispiel-Prompt:**
> "Erstelle eine Präsentation über BImSchG-Anlagen in Brandenburg mit einer Karte aller Kraftwerke."

**Generierte VDL:**
```json
{
  "slides": [
    {
      "layout": "title_slide",
      "elements": [
        {
          "type": "text",
          "content": "BImSchG-Anlagen in Brandenburg"
        }
      ]
    },
    {
      "layout": "content",
      "elements": [
        {
          "type": "geo_map",
          "properties": {
            "source": "bimschg",
            "filters": {"category": "1.1"},
            "title": "Kraftwerke in Brandenburg"
          }
        }
      ]
    }
  ]
}
```

---

## 📐 Technologie-Stack

### Dependencies

```bash
pip install pyproj>=3.6.0  # Koordinaten-Transformation
pip install matplotlib>=3.8.0  # Karten-Rendering
pip install Pillow>=10.1.0  # Bildverarbeitung
```

### Verwendete Libraries

1. **pyproj** - Koordinaten-Transformation
   - ETRS89 UTM Zone 33N → WGS84
   - PROJ.4 Transformation-Engine

2. **Matplotlib** - Statische Karten
   - Scatter Plots für Marker
   - Anpassbare Achsen (Lat/Lon)
   - Legende und Labels

3. **Pillow (PIL)** - Bildverarbeitung
   - PNG-Speicherung
   - Base64-Encoding
   - Fallback-Rendering

---

## 🧪 Tests

### Test 1: Koordinaten-Transformation

```bash
python -c "
from backend.agents.geo_sub_agent import CoordinateTransformer

t = CoordinateTransformer()
lat, lon = t.utm33n_to_wgs84(480000, 5740000)
print(f'WGS84: {lat:.6f}°N, {lon:.6f}°E')
print(f'Valid: {t.is_valid_brandenburg(lat, lon)}')
"
```

**Output:**
```
WGS84: 51.810485°N, 14.709893°E
Valid: True
```

### Test 2: Geodaten-Abruf

```bash
python backend/agents/geo_sub_agent.py
```

**Output:**
```
📍 Test 1: Geodaten abrufen (BImSchG)
   ✅ 5 Features abgerufen

🗺️  Test 2: Karte generieren
   ✅ Karte generiert
      PNG: /tmp/veritas_geo/map_123.png
      Features: 5
```

### Test 3: API-Endpoints

```bash
# Health-Check
curl http://localhost:5000/api/geo/health

# Brandenburg Bounds
curl http://localhost:5000/api/geo/bbox/brandenburg

# Koordinaten transformieren
curl -X POST http://localhost:5000/api/geo/transform \
  -H "Content-Type: application/json" \
  -d '{"ostwert": 480000, "nordwert": 5740000}'
```

---

## 🔧 Konfiguration

### Umgebungsvariablen

```bash
# Geo-Output-Verzeichnis
VERITAS_GEO_DIR=/tmp/veritas_geo

# ThemisDB-Verbindung (optional)
THEMIS_DB_URL=http://localhost:8529
```

---

## 🚀 Roadmap

### Phase 1 (Aktuell): ✅
- Koordinaten-Transformation (ETRS89 → WGS84)
- Geodaten-Abruf (BImSchG, WKA)
- Statische Karten (Matplotlib)
- API-Endpunkte

### Phase 2 (In Planung):
- ThemisDB Geo-Query Integration
- Heatmap-Visualisierung
- Marker-Clustering (bei vielen Features)
- Interaktive Karten (Leaflet.js Export)

### Phase 3 (Zukunft):
- OSM Tile-Download (Offline-Karten)
- Routing-Funktionen
- Geo-Analysen (Distanzen, Regionen)
- 3D-Visualisierung (Höhenmodelle)

---

## 📚 Verwendungsbeispiele

### Beispiel 1: BImSchG-Karte für Präsentation

```python
from backend.agents.geo_sub_agent import GeoSubAgent

agent = GeoSubAgent()

# Geodaten abrufen
geo_data = await agent.get_geo_data({'source': 'bimschg'})

# Karte generieren
map_result = await agent.generate_map(
    geo_data,
    {
        'title': 'BImSchG-Anlagen in Brandenburg',
        'width': 1200,
        'height': 800
    }
)

# In Präsentation einbetten
print(f"Karte: {map_result['png_path']}")
```

### Beispiel 2: WKA-Cluster-Analyse

```python
# Windparks in Uckermark
geo_data = await agent.get_geo_data({
    'source': 'wka',
    'bbox': [53.0, 13.5, 53.5, 14.5]  # Uckermark Region
})

map_result = await agent.generate_map(
    geo_data,
    {
        'title': 'Windkraftanlagen Uckermark',
        'style': 'cluster'  # Clustering aktivieren
    }
)
```

### Beispiel 3: Custom ThemisDB-Query

```python
# Solarkraftwerke aus ThemisDB
geo_data = await agent.get_geo_data({
    'source': 'themis:solar_facilities',
    'filters': {'leistung_mw': {'$gte': 5.0}}
})

map_result = await agent.generate_map(
    geo_data,
    {'title': 'Solarkraftwerke (>5 MW)'}
)
```

---

**Ersteller:** VERITAS Development Team
**Version:** 1.0.0
**Letzte Aktualisierung:** 3. Dezember 2025
**Status:** ✅ Implementiert und getestet

**Commit:** `tbd`
