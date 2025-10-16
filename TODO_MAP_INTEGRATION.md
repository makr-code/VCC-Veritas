# TODO: Kartendienst-Integration für BImSchG/WKA-Datenvisualisierung

**Erstellt:** 10. Oktober 2025  
**Priorität:** HOCH  
**Geschätzter Aufwand:** 12-16 Stunden  
**Status:** 🟡 PLANUNG

---

## 📋 Übersicht

Integration eines interaktiven Kartendienstes zur geografischen Visualisierung von:
- **BImSchG-Anlagen** (4,062 Umweltgenehmigungen mit Koordinaten)
- **WKA-Anlagen** (5,457 Windkraftanlagen mit Geodaten)

**Geodaten verfügbar:**
- BImSchG: `ostwert`, `nordwert` (ETRS89 UTM Zone 33N - EPSG:25833)
- WKA: `rechts`, `hoch` (ETRS89 UTM Zone 33N - EPSG:25833)

---

## 🎯 Ziele

1. **Kartenansicht** im VERITAS Frontend
2. **Marker/Cluster** für Anlagen (unterschiedliche Icons je Typ)
3. **Info-Popups** beim Klick (Details zur Anlage)
4. **Filter** (nach 4. BImSchV-Nr, Betreiber, Status, etc.)
5. **Heatmap** für Konzentration von Anlagen
6. **Suchfunktion** (Adresse, Ort, Betriebsstätte)

---

## 🗺️ Technologie-Optionen

### Option 1: **Leaflet.js** (EMPFOHLEN ✅)
- **Vorteile:**
  - Open Source, kostenlos
  - Leichtgewichtig (~40 KB)
  - Große Community, viele Plugins
  - Offline-fähig (selbst gehostete Tiles)
  - Vue.js Integration: `vue-leaflet` oder `@vue-leaflet/vue-leaflet`
- **Nachteile:**
  - Weniger Features als kommerzielle Lösungen
- **Tile-Provider:**
  - OpenStreetMap (kostenlos)
  - MapBox (kostenlos bis 50k requests/Monat)
  - CartoDB (kostenlos)

### Option 2: **Mapbox GL JS**
- **Vorteile:**
  - Moderne 3D-Visualisierung
  - Performant bei großen Datenmengen
  - Schönes Design
- **Nachteile:**
  - API-Key erforderlich
  - Kostenlos bis 50k Kartenaufrufe/Monat
  - Danach: $5/1000 requests

### Option 3: **Google Maps API**
- **Vorteile:**
  - Beste Kartenqualität
  - Umfangreiche Features
- **Nachteile:**
  - **Kostenpflichtig** ($7/1000 Kartenaufrufe)
  - API-Key + Kreditkarte erforderlich
  - Vendor Lock-in

### Option 4: **OpenLayers**
- **Vorteile:**
  - Sehr mächtig, viele GIS-Features
  - Unterstützt viele Projektionen (WGS84, Gauß-Krüger, etc.)
- **Nachteile:**
  - Komplexer als Leaflet
  - Größere Bundle-Size (~200 KB)

---

## 📐 Koordinaten-Transformation

**Geodaten-System:** 
- **Eingabe:** ETRS89 UTM Zone 33N (EPSG:25833)
- **Ausgabe:** WGS84 (EPSG:4326) für Leaflet/Web-Karten

**ETRS89 vs. WGS84:**
- ETRS89 UTM Zone 33N: Europäisches Terrestrisches Referenzsystem 1989
- UTM Zone 33N: Gültig für 12°E - 18°E (Brandenburg liegt perfekt in dieser Zone!)
- Koordinaten in Metern (Ostwert/Nordwert)
- WGS84: Weltweites Geodätisches System (lat/lon in Grad)

### Lösung: `pyproj` Library

```python
from pyproj import Transformer

# ETRS89 UTM Zone 33N (EPSG:25833) → WGS84 (EPSG:4326)
transformer = Transformer.from_crs(
    "EPSG:25833",  # ETRS89 UTM Zone 33N
    "EPSG:4326",   # WGS84 (lat/lon)
    always_xy=True
)

def utm33n_to_wgs84(ostwert, nordwert):
    """
    ETRS89 UTM Zone 33N → WGS84
    
    Args:
        ostwert: UTM Easting (Ostwert) in Metern, z.B. 400000 - 600000
        nordwert: UTM Northing (Nordwert) in Metern, z.B. 5700000 - 5950000
    
    Returns:
        tuple: (lon, lat) in WGS84 Grad
    
    Beispiel Brandenburg:
        ostwert=500000, nordwert=5850000 
        → lon=13.4°E, lat=52.5°N (Berlin-Region)
    """
    lon, lat = transformer.transform(ostwert, nordwert)
    return lon, lat

# Beispiel Brandenburg (typische Werte):
# Schwedt/Oder: ostwert ~400000, nordwert ~5895000
lon, lat = utm33n_to_wgs84(400000, 5895000)
print(f"WGS84: {lat:.6f}°N, {lon:.6f}°E")
# Ausgabe: WGS84: 53.060000°N, 14.280000°E
```

**Validierungs-Bereiche für Brandenburg:**
- **Ostwert (UTM Easting):** ~350000 - 600000 m
- **Nordwert (UTM Northing):** ~5700000 - 5950000 m
- **WGS84 Latitude:** ~51.3° - 53.6° N
- **WGS84 Longitude:** ~11.3° - 14.8° E

---

## 🏗️ Implementierungsplan

### Phase 1: Backend-Erweiterungen (4-6h)

#### 1.1 Neue API-Endpunkte

**Datei:** `backend/api/immi_endpoints.py` (NEU)

```python
from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/immi", tags=["IMMI - Immissionsschutz"])

class GeoCoordinate(BaseModel):
    lat: float
    lon: float
    
class MapMarker(BaseModel):
    id: str
    lat: float
    lon: float
    type: str  # 'bimschg' | 'wka'
    title: str
    description: str
    category: str
    icon: str
    data: dict

@router.get("/markers/bimschg")
async def get_bimschg_markers(
    bounds: Optional[str] = None,  # "min_lat,min_lon,max_lat,max_lon"
    nr_4bv: Optional[str] = None,
    ort: Optional[str] = None,
    limit: int = Query(default=500, le=5000)
) -> List[MapMarker]:
    """
    BImSchG-Anlagen als Kartenmarker
    - Koordinaten-Transformation ETRS89 UTM → WGS84
    - Filterung nach Bounds (Kartenausschnitt)
    - Clustering-freundliches Format
    """
    pass

@router.get("/markers/wka")
async def get_wka_markers(
    bounds: Optional[str] = None,
    betreiber: Optional[str] = None,
    status: Optional[str] = None,
    min_leistung: Optional[float] = None,
    limit: int = Query(default=500, le=5000)
) -> List[MapMarker]:
    """WKA-Anlagen als Kartenmarker"""
    pass

@router.get("/heatmap/bimschg")
async def get_bimschg_heatmap(
    nr_4bv: Optional[str] = None
) -> List[dict]:
    """Heatmap-Daten für BImSchG-Anlagen"""
    pass

@router.get("/search")
async def search_location(
    query: str,
    limit: int = 10
) -> List[dict]:
    """
    Suche nach Orten, Betriebsstätten, Adressen
    - Nutzt BImSchG/WKA Datenbank
    - Optional: Nominatim API für Adresssuche
    """
    pass

@router.get("/statistics/region")
async def get_region_statistics(
    bounds: str  # "min_lat,min_lon,max_lat,max_lon"
) -> dict:
    """Statistiken für sichtbaren Kartenausschnitt"""
    pass
```

#### 1.2 Koordinaten-Service

**Datei:** `backend/services/coordinate_service.py` (NEU)

```python
from typing import Tuple, Optional
import sqlite3

class CoordinateService:
    """
    Service für Koordinaten-Transformation und Validierung
    """
    
    @staticmethod
    def utm33n_to_wgs84(ostwert: float, nordwert: float) -> Tuple[float, float]:
        """
        ETRS89 UTM Zone 33N (EPSG:25833) → WGS84 (EPSG:4326)
        
        Args:
            ostwert: UTM Easting in Metern (ca. 350000-600000 für Brandenburg)
            nordwert: UTM Northing in Metern (ca. 5700000-5950000 für Brandenburg)
        
        Returns:
            tuple: (latitude, longitude) in WGS84 Grad
        """
        from pyproj import Transformer
        
        # ETRS89 UTM Zone 33N → WGS84
        transformer = Transformer.from_crs(
            "EPSG:25833",  # ETRS89 UTM Zone 33N
            "EPSG:4326",   # WGS84
            always_xy=True
        )
        
        lon, lat = transformer.transform(ostwert, nordwert)
        return lat, lon
    
    @staticmethod
    def is_valid_coordinate(lat: float, lon: float) -> bool:
        """Validierung: Brandenburg-Region"""
        # Brandenburg: ~51.3 - 53.6°N, ~11.3 - 14.8°E
        return (51.0 <= lat <= 54.0) and (11.0 <= lon <= 15.0)
    
    def get_bimschg_coordinates(
        self, 
        db_path: str,
        filters: dict = None
    ) -> list:
        """
        Alle BImSchG-Koordinaten mit Transformation
        
        Returns:
            [{"id": "...", "lat": 52.5, "lon": 13.4, ...}, ...]
        """
        pass
    
    def get_wka_coordinates(
        self,
        db_path: str,
        filters: dict = None
    ) -> list:
        """WKA-Koordinaten mit Transformation"""
        pass
```

#### 1.3 Cache-Layer für Geo-Daten

```python
from functools import lru_cache
from datetime import datetime, timedelta

class GeoCache:
    """
    Cache für transformierte Koordinaten
    - Transformation ist teuer → Cache für 1h
    - Redis optional für Multi-Instance Setup
    """
    
    _cache = {}
    _cache_ttl = timedelta(hours=1)
    
    @classmethod
    def get_or_compute(cls, key: str, compute_fn):
        if key in cls._cache:
            data, timestamp = cls._cache[key]
            if datetime.now() - timestamp < cls._cache_ttl:
                return data
        
        data = compute_fn()
        cls._cache[key] = (data, datetime.now())
        return data
```

---

### Phase 2: Frontend-Komponenten (6-8h)

#### 2.1 Vue.js Map-Komponente (Leaflet)

**Datei:** `frontend/src/components/MapView.vue` (NEU)

```vue
<template>
  <div class="map-container">
    <!-- Karte -->
    <div id="map" ref="mapElement" class="map"></div>
    
    <!-- Kontrollpanel -->
    <div class="map-controls">
      <div class="control-section">
        <h3>Filter</h3>
        
        <!-- Datenlayer Toggle -->
        <label>
          <input type="checkbox" v-model="layers.bimschg" @change="toggleLayer('bimschg')">
          BImSchG-Anlagen ({{ stats.bimschg }})
        </label>
        <label>
          <input type="checkbox" v-model="layers.wka" @change="toggleLayer('wka')">
          Windkraftanlagen ({{ stats.wka }})
        </label>
        
        <!-- Filter: BImSchG -->
        <div v-if="layers.bimschg">
          <select v-model="filters.nr_4bv" @change="applyFilters">
            <option value="">Alle 4. BImSchV-Nummern</option>
            <option v-for="nr in bimschvNumbers" :key="nr.value" :value="nr.value">
              {{ nr.label }} ({{ nr.count }})
            </option>
          </select>
        </div>
        
        <!-- Filter: WKA -->
        <div v-if="layers.wka">
          <select v-model="filters.wka_status" @change="applyFilters">
            <option value="">Alle Status</option>
            <option value="In Betrieb">In Betrieb</option>
            <option value="Im Genehmigungsverfahren">Im Genehmigungsverfahren</option>
          </select>
        </div>
        
        <!-- Clustering Toggle -->
        <label>
          <input type="checkbox" v-model="clustering" @change="toggleClustering">
          Marker gruppieren
        </label>
        
        <!-- Heatmap Toggle -->
        <label>
          <input type="checkbox" v-model="heatmap" @change="toggleHeatmap">
          Heatmap anzeigen
        </label>
      </div>
      
      <!-- Suche -->
      <div class="control-section">
        <h3>Suche</h3>
        <input 
          type="text" 
          v-model="searchQuery" 
          @input="searchLocation"
          placeholder="Ort, Betriebsstätte..."
        >
        <ul v-if="searchResults.length">
          <li v-for="result in searchResults" :key="result.id" @click="flyTo(result)">
            {{ result.name }} - {{ result.ort }}
          </li>
        </ul>
      </div>
      
      <!-- Statistiken -->
      <div class="control-section">
        <h3>Sichtbarer Bereich</h3>
        <p>BImSchG-Anlagen: <strong>{{ visibleStats.bimschg }}</strong></p>
        <p>Windkraftanlagen: <strong>{{ visibleStats.wka }}</strong></p>
        <p>Gesamtleistung: <strong>{{ visibleStats.totalPower }} MW</strong></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet.markercluster';
import 'leaflet.heat';

const mapElement = ref(null);
let map = null;
let markerClusters = {
  bimschg: null,
  wka: null
};
let heatmapLayer = null;

// State
const layers = ref({
  bimschg: true,
  wka: true
});

const filters = ref({
  nr_4bv: '',
  wka_status: ''
});

const clustering = ref(true);
const heatmap = ref(false);
const searchQuery = ref('');
const searchResults = ref([]);

const stats = ref({
  bimschg: 0,
  wka: 0
});

const visibleStats = ref({
  bimschg: 0,
  wka: 0,
  totalPower: 0
});

// Lifecycle
onMounted(async () => {
  initMap();
  await loadMarkers();
});

// Methods
function initMap() {
  // Initialisiere Karte (Brandenburg-Zentrum)
  map = L.map(mapElement.value).setView([52.4125, 12.5316], 8);
  
  // Tile Layer (OpenStreetMap)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);
  
  // Event-Listener
  map.on('moveend', updateVisibleStats);
  map.on('zoomend', updateVisibleStats);
}

async function loadMarkers() {
  // BImSchG-Marker
  if (layers.value.bimschg) {
            const bimschgData = await fetch('/api/immi/markers/bimschg').then(r => r.json());
    stats.value.bimschg = bimschgData.length;
    
    markerClusters.bimschg = L.markerClusterGroup();
    
    bimschgData.forEach(item => {
      const marker = L.marker([item.lat, item.lon], {
        icon: getBimSchGIcon(item.category)
      });
      
      marker.bindPopup(`
        <div class="marker-popup">
          <h4>${item.title}</h4>
          <p><strong>BST:</strong> ${item.data.bst_name}</p>
          <p><strong>Anlage:</strong> ${item.data.anl_bez}</p>
          <p><strong>4. BImSchV:</strong> ${item.data.nr_4bv} - ${item.data.anlart_4bv}</p>
          <p><strong>Ort:</strong> ${item.data.ort}</p>
          <button onclick="showDetails('${item.id}')">Details</button>
        </div>
      `);
      
      markerClusters.bimschg.addLayer(marker);
    });
    
    map.addLayer(markerClusters.bimschg);
  }
  
  // WKA-Marker
  if (layers.value.wka) {
            const wkaData = await fetch('/api/immi/markers/wka').then(r => r.json());
    stats.value.wka = wkaData.length;
    
    markerClusters.wka = L.markerClusterGroup();
    
    wkaData.forEach(item => {
      const marker = L.marker([item.lat, item.lon], {
        icon: getWKAIcon(item.data.status)
      });
      
      marker.bindPopup(`
        <div class="marker-popup">
          <h4>WKA: ${item.title}</h4>
          <p><strong>Betreiber:</strong> ${item.data.betreiber}</p>
          <p><strong>Leistung:</strong> ${item.data.leistung} MW</p>
          <p><strong>Nabenhöhe:</strong> ${item.data.nabenhoehe} m</p>
          <p><strong>Status:</strong> ${item.data.status}</p>
          <p><strong>Ort:</strong> ${item.data.ort}</p>
          <button onclick="showDetails('${item.id}')">Details</button>
        </div>
      `);
      
      markerClusters.wka.addLayer(marker);
    });
    
    map.addLayer(markerClusters.wka);
  }
}

function getBimSchGIcon(category) {
  const iconColors = {
    'Feuerungsanlagen': 'red',
    'Tierhaltung': 'green',
    'Chemische Industrie': 'orange',
    'Abfallbehandlung': 'brown',
    'default': 'blue'
  };
  
  const color = iconColors[category] || iconColors.default;
  
  return L.icon({
    iconUrl: `/assets/markers/bimschg-${color}.png`,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34]
  });
}

function getWKAIcon(status) {
  const iconUrl = status === 'In Betrieb' 
    ? '/assets/markers/wka-active.png'
    : '/assets/markers/wka-planned.png';
    
  return L.icon({
    iconUrl,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32]
  });
}

function toggleLayer(layerName) {
  // Toggle layer visibility
  if (layers.value[layerName]) {
    map.addLayer(markerClusters[layerName]);
  } else {
    map.removeLayer(markerClusters[layerName]);
  }
}

function toggleHeatmap() {
  if (heatmap.value) {
    // Load heatmap data
    fetch('/api/immi/heatmap/bimschg').then(r => r.json()).then(data => {
      const heatData = data.map(d => [d.lat, d.lon, d.intensity]);
      heatmapLayer = L.heatLayer(heatData, {
        radius: 25,
        blur: 35,
        maxZoom: 13
      }).addTo(map);
    });
  } else {
    if (heatmapLayer) {
      map.removeLayer(heatmapLayer);
    }
  }
}

async function searchLocation() {
  if (searchQuery.value.length < 3) {
    searchResults.value = [];
    return;
  }
  
  const results = await fetch(`/api/immi/search?query=${searchQuery.value}`)
    .then(r => r.json());
  searchResults.value = results;
}

function flyTo(location) {
  map.flyTo([location.lat, location.lon], 14);
  searchResults.value = [];
}

function updateVisibleStats() {
  const bounds = map.getBounds();
  
  // Count visible markers
  // ... implementation
}
</script>

<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: 100vh;
}

.map {
  width: 100%;
  height: 100%;
}

.map-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  max-width: 300px;
  max-height: 90vh;
  overflow-y: auto;
}

.control-section {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ddd;
}

.control-section:last-child {
  border-bottom: none;
}

.marker-popup {
  min-width: 200px;
}

.marker-popup h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.marker-popup button {
  margin-top: 10px;
  padding: 5px 10px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
```

#### 2.2 Marker-Icons erstellen

**Aufgaben:**
- [ ] Icon-Set für BImSchG-Kategorien (Feuerung, Tierhaltung, Chemie, etc.)
- [ ] Icon-Set für WKA-Status (Betrieb, Planung)
- [ ] SVG-Icons optimieren für verschiedene Zoom-Stufen

#### 2.3 Integration in VERITAS Frontend

**Datei:** `frontend/src/router/index.js`

```javascript
{
  path: '/map',
  name: 'Map',
  component: () => import('@/components/MapView.vue'),
  meta: { 
    title: 'Karte',
    requiresAuth: true 
  }
}
```

---

### Phase 3: Optimierungen (2-4h)

#### 3.1 Performance-Optimierung

**Problem:** 10,000+ Marker können Browser verlangsamen

**Lösungen:**
1. **Server-Side Clustering:**
   - Backend berechnet Cluster-Zentren
   - Nur aggregierte Daten senden bei Zoom-Out
   
2. **Viewport-basiertes Laden:**
   - Nur Marker im sichtbaren Bereich laden
   - "bounds" Parameter in API nutzen
   
3. **Marker-Simplification:**
   - Zoom < 10: Nur Cluster-Circles (keine Icons)
   - Zoom 10-14: Standard-Icons
   - Zoom > 14: Detaillierte Icons + Labels

4. **GeoJSON statt einzelne Marker:**
   ```javascript
   const geojsonFeature = {
     type: 'FeatureCollection',
     features: markers.map(m => ({
       type: 'Feature',
       geometry: {
         type: 'Point',
         coordinates: [m.lon, m.lat]
       },
       properties: { ...m.data }
     }))
   };
   
   L.geoJSON(geojsonFeature).addTo(map);
   ```

#### 3.2 Offline-Fähigkeit

**Tile-Caching:**
- Selbst gehostete Tile-Server
- Oder: Service Worker für Tile-Caching
- Fallback auf offline Tiles

#### 3.3 Mobile-Optimierung

- Responsive Controls
- Touch-Gesten (Pinch-to-Zoom)
- Kleinere Icons für mobile Devices

---

### Phase 4: Testing & Deployment (2h)

#### 4.1 Unit-Tests

**Datei:** `tests/test_map_endpoints.py`

```python
def test_gk_to_wgs84_transformation():
    """Test Koordinaten-Transformation"""
    from backend.services.coordinate_service import CoordinateService
    
    # Schwedt/Oder: GK 4587234, 5895678
    lat, lon = CoordinateService.gk_to_wgs84(4587234, 5895678)
    
    assert 53.0 < lat < 53.1  # ~53.06°N
    assert 14.2 < lon < 14.3  # ~14.28°E

def test_get_bimschg_markers():
    """Test BImSchG-Marker API"""
    response = client.get("/api/immi/markers/bimschg?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    assert all('lat' in m and 'lon' in m for m in data)

def test_bounds_filtering():
    """Test Bounds-Filter"""
    # Brandenburg-Bounds
    bounds = "52.0,12.0,53.0,14.0"
    response = client.get(f"/api/immi/markers/bimschg?bounds={bounds}")
    data = response.json()
    
    for marker in data:
        assert 52.0 <= marker['lat'] <= 53.0
        assert 12.0 <= marker['lon'] <= 14.0
```

#### 4.2 Integration-Tests

- [ ] Test Map-Rendering
- [ ] Test Marker-Clustering
- [ ] Test Filter-Funktionalität
- [ ] Test Search-API

#### 4.3 Performance-Tests

```python
def test_marker_load_performance():
    """10k Marker sollten < 2s laden"""
    import time
    
    start = time.time()
    response = client.get("/api/immi/markers/bimschg?limit=5000")
    duration = time.time() - start
    
    assert duration < 2.0
    assert response.status_code == 200
```

---

## 📦 Dependencies

### Backend (Python)

```bash
pip install pyproj  # Koordinaten-Transformation
pip install shapely  # Geometrie-Operationen (optional)
pip install geojson  # GeoJSON-Serialisierung (optional)
```

**`requirements.txt` erweitern:**
```txt
pyproj==3.6.1
shapely==2.0.2
geojson==3.1.0
```

### Frontend (Node.js)

```bash
npm install leaflet@1.9.4
npm install leaflet.markercluster@1.5.3
npm install leaflet.heat@0.2.0
npm install @vue-leaflet/vue-leaflet@0.10.1  # Vue 3 Integration
```

**`package.json` erweitern:**
```json
{
  "dependencies": {
    "leaflet": "^1.9.4",
    "leaflet.markercluster": "^1.5.3",
    "leaflet.heat": "^0.2.0",
    "@vue-leaflet/vue-leaflet": "^0.10.1"
  }
}
```

---

## 🧪 Daten-Validierung

### Koordinaten-Qualität prüfen

**Script:** `scripts/validate_coordinates.py`

```python
import sqlite3
from backend.services.coordinate_service import CoordinateService

def validate_bimschg_coordinates():
    """Prüfe BImSchG-Koordinaten (ETRS89 UTM Zone 33N)"""
    conn = sqlite3.connect('data/BImSchG.sqlite')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT bimschg_id, ostwert, nordwert, bst_name, ort
        FROM BImSchG
        WHERE ostwert IS NOT NULL AND nordwert IS NOT NULL
    """)
    
    service = CoordinateService()
    valid = 0
    invalid = 0
    
    for row in cursor.fetchall():
        bimschg_id, ostwert, nordwert, bst_name, ort = row
        
        try:
            lat, lon = service.utm33n_to_wgs84(ostwert, nordwert)
            
            if service.is_valid_coordinate(lat, lon):
                valid += 1
            else:
                invalid += 1
                print(f"⚠️ Ungültige Koordinate: {bimschg_id} - {bst_name} ({ort})")
                print(f"   UTM: {ostwert}, {nordwert} → WGS84: {lat:.6f}, {lon:.6f}")
        except Exception as e:
            invalid += 1
            print(f"❌ Fehler bei {bimschg_id}: {e}")
    
    print(f"\n✅ Gültig: {valid}")
    print(f"❌ Ungültig: {invalid}")
    print(f"📊 Quote: {valid/(valid+invalid)*100:.1f}%")

if __name__ == '__main__':
    validate_bimschg_coordinates()
```

---

## 🎨 UI/UX Design-Konzept

### Farbschema für Kategorien

**BImSchG-Anlagen:**
- 🔴 **Rot:** Feuerungsanlagen, Energieerzeugung (1.x)
- 🟠 **Orange:** Chemische Industrie (4.x)
- 🟢 **Grün:** Tierhaltung, Landwirtschaft (7.x)
- 🟤 **Braun:** Abfallbehandlung (8.x)
- 🔵 **Blau:** Lagerung, Logistik (9.x)
- ⚫ **Grau:** Sonstige (10.x)

**WKA-Anlagen:**
- 🟢 **Grün:** In Betrieb
- 🟡 **Gelb:** Im Genehmigungsverfahren
- 🔴 **Rot:** Stillgelegt
- 🔵 **Blau:** Im Bau

### Beispiel-Layout

```
┌────────────────────────────────────────────────┬─────────────────┐
│                                                │  🔍 Suche       │
│                                                │  ───────────────│
│                                                │  ☑ BImSchG (4k) │
│                                                │  ☑ WKA (5.4k)   │
│                                                │                 │
│             KARTE                              │  Filter:        │
│         (Brandenburg)                          │  └─ 4. BImSchV  │
│                                                │  └─ Status      │
│                                                │                 │
│    🔴🟢🔵 Marker                               │  ☐ Clustering   │
│                                                │  ☐ Heatmap      │
│                                                │                 │
│                                                │  Statistik:     │
│                                                │  ───────────────│
│                                                │  BImSchG: 1,234 │
└────────────────────────────────────────────────┤  WKA: 567       │
│  [+] [-] 🧭 📍                                 │  Σ 456 MW       │
└────────────────────────────────────────────────┴─────────────────┘
```

---

## 🚀 Deployment-Checklist

- [ ] Backend API-Endpunkte registrieren (`backend.py`)
  ```python
  from backend.api.immi_endpoints import router as immi_router
  app.include_router(immi_router)
  ```
- [ ] pyproj installieren
- [ ] Koordinaten-Transformation testen
- [ ] Frontend Dependencies installieren
- [ ] Map-Komponente in Router einfügen
- [ ] Marker-Icons bereitstellen (`public/assets/markers/`)
- [ ] Tile-Provider konfigurieren (API-Key wenn nötig)
- [ ] Performance-Tests (10k+ Marker)
- [ ] Mobile-Testing (responsive Design)
- [ ] Dokumentation schreiben

---

## 📊 Erfolgskriterien

1. ✅ Karte zeigt alle BImSchG + WKA Anlagen
2. ✅ Marker-Clustering funktioniert performant (< 2s Ladezeit)
3. ✅ Filter reduzieren Marker in Echtzeit
4. ✅ Popup zeigt relevante Detailinformationen
5. ✅ Suche findet Orte/Betriebsstätten
6. ✅ Heatmap zeigt Konzentrationszonen
7. ✅ Mobile-freundlich (Touch-Gesten)
8. ✅ Offline-fähig (gecachte Tiles)

---

## 🔄 Erweiterungsmöglichkeiten (Phase 5+)

### Erweiterte Features:

1. **Routing/Wegplanung**
   - Leaflet Routing Machine
   - Route zu ausgewählter Anlage

2. **Draw-Tools**
   - Eigene Shapes zeichnen (Polygone, Linien)
   - Flächen-Statistiken

3. **Layer-Overlays**
   - Naturschutzgebiete
   - Windvorranggebiete
   - Lärmbelastung-Konturen

4. **3D-Visualisierung**
   - Gebäudehöhen (WKA-Nabenhöhe)
   - Mapbox GL 3D

5. **Zeitachse**
   - Slider für Inbetriebnahme-Jahr
   - Animation der Entwicklung

6. **Export-Funktionen**
   - Kartenausschnitt als PNG
   - GeoJSON-Export sichtbarer Marker
   - PDF-Report mit Karte + Statistiken

7. **Collaboration**
   - Marker kommentieren
   - Notizen zu Anlagen
   - Teilen von Kartenansichten (URL mit Filtern)

---

## 📚 Referenzen & Links

**Leaflet:**
- Docs: https://leafletjs.com/
- Vue Integration: https://vue2-leaflet.netlify.app/
- Clustering Plugin: https://github.com/Leaflet/Leaflet.markercluster
- Heatmap Plugin: https://github.com/Leaflet/Leaflet.heat

**Koordinaten-Transformation:**
- pyproj Docs: https://pyproj4.github.io/pyproj/stable/
- EPSG Codes: https://epsg.io/

**Tile-Provider:**
- OpenStreetMap: https://www.openstreetmap.org/
- MapBox: https://www.mapbox.com/
- CartoDB: https://carto.com/basemaps/

**Alternative Kartendienste:**
- Mapbox GL: https://docs.mapbox.com/mapbox-gl-js/
- OpenLayers: https://openlayers.org/
- Google Maps: https://developers.google.com/maps

---

## 💡 Hinweise

**Datenschutz:**
- BImSchG/WKA-Daten sind öffentlich zugänglich (Umweltinformationsgesetz)
- Keine personenbezogenen Daten in Popups anzeigen

**Lizenz-Compliance:**
- OpenStreetMap: Attribution erforderlich ("© OpenStreetMap contributors")
- Leaflet: BSD-2-Clause License (kostenlos)

**API-Limits:**
- OpenStreetMap Tiles: Max 200 req/sec
- MapBox: 50k requests/Monat kostenlos
- Nominatim (Geocoding): Max 1 req/sec

---

**Ersteller:** VERITAS Agent System  
**Version:** 1.0.0  
**Letzte Aktualisierung:** 10. Oktober 2025
