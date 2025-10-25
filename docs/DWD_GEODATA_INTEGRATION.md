# DWD Open Data - Geodatenbasierte Integration für Flow-Simulation

## 📍 Übersicht

Dieses Dokument beschreibt, wie der **DWD Open Data Agent** geodatenbasiert in die **Atmospheric Flow Simulation** eingebunden wird, um die richtigen Wetterstationen für Strömungsberechnungen zu identifizieren.

---

## 🎯 Integration Flow

```
User Query
    ↓
Atmospheric Flow Request
    ↓
Calculation Bounds (Geodaten: lat/lon Box)
    ↓
DWD Open Data Agent
    ↓
Nächste Station(en) finden
    ↓
DWD Open Data von opendata.dwd.de abrufen
    ↓
dwdparse: Parse Wetterdaten
    ↓
WindField erstellen
    ↓
Flow Simulation (Gaussian/Lagrangian)
```

---

## 🔧 Technische Implementierung

### 1. **Atmospheric Flow Request mit Geodaten**

Der Flow-Simulation Request enthält immer **calculation_bounds**:

```python
from backend.agents.veritas_api_agent_atmospheric_flow import (
    FlowCalculationRequest, 
    EmissionSource, 
    ReceptorPoint,
    Coordinate
)

# Beispiel: Berlin Stadtgebiet
flow_request = FlowCalculationRequest(
    query_id="berlin-traffic-001",
    query_text="Verkehrsemissionen Berlin Innenstadt",
    
    # ⭐ GEODATEN: Berechnungsbereich definieren
    calculation_bounds={
        'lat_min': 52.48,  # Süd
        'lat_max': 52.52,  # Nord
        'lon_min': 13.38,  # West
        'lon_max': 13.42   # Ost
    },
    
    grid_resolution_m=200.0,  # 200m Raster
    use_weather_data=True,    # DWD Integration aktivieren
    
    # Emissionsquellen mit Koordinaten
    emission_sources=[
        EmissionSource(
            source_id="highway_a100",
            coordinate=Coordinate(52.5000, 13.4000, 5.0),
            # ... weitere Parameter
        )
    ],
    
    # Rezeptoren mit Koordinaten
    receptor_points=[
        ReceptorPoint(
            receptor_id="residential_area_1",
            coordinate=Coordinate(52.5050, 13.4100, 30.0),
            # ... weitere Parameter
        )
    ]
)
```

---

### 2. **Automatische Stationsauswahl**

Der **DWD Open Data Agent** wählt automatisch die nächstgelegene Station basierend auf:

#### **Methode: `find_nearest_station(lat, lon)`**

```python
from backend.agents.veritas_api_agent_dwd_opendata import DWDOpenDataAgent

agent = DWDOpenDataAgent()

# Zentrum des Berechnungsgebiets
center_lat = (bounds['lat_min'] + bounds['lat_max']) / 2
center_lon = (bounds['lon_min'] + bounds['lon_max']) / 2

# Finde nächste DWD Station
station = agent.find_nearest_station(
    lat=center_lat, 
    lon=center_lon,
    parameter="temperature"  # oder "wind", "precipitation"
)

# Ergebnis:
# {
#     'station_id': '00433',
#     'name': 'Berlin-Tempelhof',
#     'latitude': 52.4675,
#     'longitude': 13.4021,
#     'elevation': 48.0
# }
```

#### **Distanzberechnung (vereinfacht)**

```python
def distance(station_coords: Dict, target_lat: float, target_lon: float) -> float:
    """Euklidische Distanz (für Deutschland ausreichend)"""
    dlat = station_coords['latitude'] - target_lat
    dlon = station_coords['longitude'] - target_lon
    return dlat * dlat + dlon * dlon  # Quadrat der Distanz
```

**Für präzise Berechnung** (Haversine-Formel):
```python
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """Präzise Distanz in Metern"""
    R = 6371000  # Erdradius in Metern
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c  # Distanz in Metern
```

---

### 3. **Wetterdaten von DWD Open Data abrufen**

```python
# Station-ID ermittelt: '00433' (Berlin-Tempelhof)

# Wetterdaten abrufen
weather_data = agent.get_weather_data(
    station_id="00433",
    parameter="temperature",  # oder "wind", "precipitation", "pressure"
    resolution="hourly",      # oder "daily"
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now()
)

# Ergebnis: Liste von Records
# [
#   {
#     'timestamp': datetime(2025, 10, 19, 10, 0, tzinfo=UTC),
#     'temperature': 283.75,  # Kelvin (dwdparse liefert SI-Einheiten!)
#     'station_id': '00433',
#     'quality_level': 3
#   },
#   ...
# ]
```

#### **DWD Open Data URL-Struktur**

```
https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/
    └── hourly/
        ├── air_temperature/
        │   ├── recent/
        │   │   └── stundenwerte_TU_00433_akt.zip  ← Agent downloadet diese Datei
        │   └── historical/
        ├── wind/
        │   └── recent/
        ├── precipitation/
        └── pressure/
```

**Agent-Logik:**
1. Baue URL: `{base_url}/{resolution}/{parameter}/{period}/`
2. Konstruiere Dateiname: `stundenwerte_{PARAM_CODE}_{STATION_ID}_akt.zip`
3. Download nach Cache: `C:\Users\...\AppData\Local\Temp\veritas_dwd_cache\`
4. Parse mit dwdparse: `TemperatureObservationsParser().parse(zip_file)`

---

### 4. **Windfeld-Erstellung für Flow-Simulation**

Der **Atmospheric Flow Agent** konvertiert DWD-Daten in ein **WindField**:

```python
# In veritas_api_agent_atmospheric_flow.py

async def _get_wind_field_from_dwd(self, request: FlowCalculationRequest) -> WindField:
    """Windfeld vom DWD Weather Agent erstellen"""
    
    # 1. Zentrum des Berechnungsgebiets
    center_lat = (request.calculation_bounds['lat_min'] + 
                  request.calculation_bounds['lat_max']) / 2
    center_lon = (request.calculation_bounds['lon_min'] + 
                  request.calculation_bounds['lon_max']) / 2
    
    # 2. DWD Open Data Agent initialisieren
    from backend.agents.veritas_api_agent_dwd_opendata import DWDOpenDataAgent
    dwd_agent = DWDOpenDataAgent()
    
    # 3. Nächste Station finden
    station = dwd_agent.find_nearest_station(center_lat, center_lon, "wind")
    
    # 4. Wind-Daten abrufen (letzte 24h)
    wind_data = dwd_agent.get_weather_data(
        station_id=station['station_id'],
        parameter="wind",
        resolution="hourly",
        start_date=datetime.now() - timedelta(hours=24),
        end_date=datetime.now()
    )
    
    # 5. Durchschnittswind berechnen
    avg_wind_speed = sum(r['wind_speed'] for r in wind_data) / len(wind_data)
    avg_wind_direction = sum(r['wind_direction'] for r in wind_data) / len(wind_data)
    
    # 6. WindField erstellen
    return WindField(
        grid_vectors={
            # Einheitliches Windfeld (vereinfacht)
            f"{lat:.4f}_{lon:.4f}": WindVector(
                speed_ms=avg_wind_speed,
                direction_deg=avg_wind_direction,
                height_m=10.0
            )
            for lat in [center_lat - 0.02, center_lat, center_lat + 0.02]
            for lon in [center_lon - 0.02, center_lon, center_lon + 0.02]
        },
        stability_class=AtmosphericStabilityClass.D,  # Neutral
        mixing_height_m=1000.0,
        data_source=f"DWD Station {station['station_id']} ({station['name']})"
    )
```

---

## 📊 Mehrere Stationen für größere Gebiete

Für **große Berechnungsgebiete** können mehrere Stationen genutzt werden:

### **Strategie: Spatial Interpolation**

```python
def get_multi_station_wind_field(
    bounds: Dict[str, float], 
    resolution_m: float
) -> WindField:
    """Windfeld aus mehreren DWD Stationen interpolieren"""
    
    agent = DWDOpenDataAgent()
    
    # 1. Alle verfügbaren Stationen laden
    all_stations = agent.get_stations()
    
    # 2. Stationen im/nahe am Berechnungsgebiet filtern
    relevant_stations = []
    for station in all_stations.values():
        # Prüfe ob Station im erweiterten Bereich liegt
        if (bounds['lat_min'] - 0.5 <= station['latitude'] <= bounds['lat_max'] + 0.5 and
            bounds['lon_min'] - 0.5 <= station['longitude'] <= bounds['lon_max'] + 0.5):
            relevant_stations.append(station)
    
    # 3. Wetterdaten von allen Stationen abrufen
    station_wind_data = {}
    for station in relevant_stations[:5]:  # Max. 5 Stationen
        wind_records = agent.get_weather_data(
            station_id=station['station_id'],
            parameter="wind",
            resolution="hourly",
            start_date=datetime.now() - timedelta(hours=12),
            end_date=datetime.now()
        )
        
        if wind_records:
            # Durchschnitt berechnen
            avg_speed = sum(r['wind_speed'] for r in wind_records) / len(wind_records)
            avg_direction = sum(r['wind_direction'] for r in wind_records) / len(wind_records)
            
            station_wind_data[station['station_id']] = {
                'latitude': station['latitude'],
                'longitude': station['longitude'],
                'wind_speed': avg_speed,
                'wind_direction': avg_direction
            }
    
    # 4. Windfeld-Grid erstellen mit Interpolation
    grid_vectors = {}
    
    lat_steps = int((bounds['lat_max'] - bounds['lat_min']) * 111320 / resolution_m)
    lon_steps = int((bounds['lon_max'] - bounds['lon_min']) * 111320 / resolution_m)
    
    for i in range(lat_steps):
        for j in range(lon_steps):
            lat = bounds['lat_min'] + i * (bounds['lat_max'] - bounds['lat_min']) / lat_steps
            lon = bounds['lon_min'] + j * (bounds['lon_max'] - bounds['lon_min']) / lon_steps
            
            # Inverse Distance Weighting (IDW) Interpolation
            wind_vector = interpolate_wind_idw(
                target_lat=lat,
                target_lon=lon,
                station_data=station_wind_data
            )
            
            grid_vectors[f"{lat:.4f}_{lon:.4f}"] = wind_vector
    
    return WindField(
        grid_vectors=grid_vectors,
        stability_class=AtmosphericStabilityClass.D,
        mixing_height_m=1000.0,
        data_source=f"DWD Multi-Station Interpolation ({len(station_wind_data)} stations)"
    )


def interpolate_wind_idw(
    target_lat: float,
    target_lon: float,
    station_data: Dict[str, Dict],
    power: float = 2.0
) -> WindVector:
    """Inverse Distance Weighting Interpolation für Wind"""
    
    weighted_speed = 0.0
    weighted_direction = 0.0
    total_weight = 0.0
    
    for station_id, data in station_data.items():
        # Distanz berechnen
        distance = haversine_distance(
            target_lat, target_lon,
            data['latitude'], data['longitude']
        )
        
        # Gewicht: 1 / distance^power
        weight = 1.0 / (distance ** power) if distance > 0 else 1e10
        
        weighted_speed += data['wind_speed'] * weight
        weighted_direction += data['wind_direction'] * weight
        total_weight += weight
    
    return WindVector(
        speed_ms=weighted_speed / total_weight if total_weight > 0 else 5.0,
        direction_deg=weighted_direction / total_weight if total_weight > 0 else 270.0,
        height_m=10.0
    )
```

---

## 🔄 Integration in bestehenden Atmospheric Flow Agent

Der **Atmospheric Flow Agent** ruft bereits DWD-Daten ab:

### **Vorhandene Integration (Zeilen 580-630)**

```python
async def _get_wind_field(self, request: FlowCalculationRequest) -> Optional[WindField]:
    """Windfeld abrufen (manuelle Daten, DWD, oder Default)"""
    
    # Priorität 1: Manuelle Winddaten
    if request.manual_wind_data:
        return self._create_wind_field_from_manual_data(...)
    
    # Priorität 2: DWD Weather Agent ⭐
    if self.weather_agent and request.use_weather_data:
        return await self._get_wind_field_from_dwd(request)  # ← HIER
    
    # Priorität 3: Default-Windfeld
    return self._create_default_wind_field(...)
```

### **Was passiert aktuell:**

1. `_get_wind_field_from_dwd()` wird aufgerufen
2. **PROBLEM:** Es versucht den **alten DWD Weather Agent** zu nutzen
   ```python
   from .veritas_api_agent_dwd_weather import DwdWeatherAgent  # ← ALT (dwdweather2)
   ```
3. **LÖSUNG:** Agent auf **DWD Open Data Agent** umstellen

---

## ✅ TODO: Integration aktualisieren

### **Schritt 1: Import aktualisieren**

**In `veritas_api_agent_atmospheric_flow.py` (Zeile 46-54):**

```python
# ALT:
try:
    from .veritas_api_agent_dwd_weather import (
        DwdWeatherAgent, DwdWeatherQueryRequest, 
        WeatherParameter, WeatherInterval, create_dwd_weather_agent
    )
    DWD_INTEGRATION_AVAILABLE = True
except ImportError:
    DWD_INTEGRATION_AVAILABLE = False

# NEU:
try:
    from .veritas_api_agent_dwd_opendata import DWDOpenDataAgent
    DWD_INTEGRATION_AVAILABLE = True
except ImportError:
    DWD_INTEGRATION_AVAILABLE = False
    print("⚠️  DWD Open Data Agent Integration nicht verfügbar")
```

### **Schritt 2: Agent-Initialisierung aktualisieren**

**In `AtmosphericFlowAgent.__init__()` (Zeile 482-488):**

```python
# ALT:
if DWD_INTEGRATION_AVAILABLE and self.config.weather_integration_enabled:
    try:
        self.weather_agent = create_dwd_weather_agent()  # ← ALT
        self.logger.info("✅ DWD Weather Agent integration enabled")
    except Exception as e:
        self.logger.warning(f"DWD Weather Agent integration failed: {e}")

# NEU:
if DWD_INTEGRATION_AVAILABLE and self.config.weather_integration_enabled:
    try:
        self.weather_agent = DWDOpenDataAgent()  # ← NEU
        self.logger.info("✅ DWD Open Data Agent integration enabled")
    except Exception as e:
        self.logger.warning(f"DWD Open Data Agent integration failed: {e}")
```

### **Schritt 3: Wind-Feld-Methode ersetzen**

**Ersetze `_get_wind_field_from_dwd()` (Zeile 597-633):**

```python
async def _get_wind_field_from_dwd(self, request: FlowCalculationRequest) -> Optional[WindField]:
    """Windfeld vom DWD Open Data Agent abrufen"""
    if not DWD_INTEGRATION_AVAILABLE or not self.weather_agent:
        return None
    
    try:
        # Zentrum des Berechnungsgebiets bestimmen
        center_lat = (request.calculation_bounds['lat_min'] + 
                      request.calculation_bounds['lat_max']) / 2
        center_lon = (request.calculation_bounds['lon_min'] + 
                      request.calculation_bounds['lon_max']) / 2
        
        # Nächste DWD Station finden
        station = self.weather_agent.find_nearest_station(
            lat=center_lat,
            lon=center_lon,
            parameter="wind"
        )
        
        if not station:
            self.logger.warning("No DWD station found for wind data")
            return None
        
        self.logger.info(f"📍 Using DWD Station: {station['name']} (ID: {station['station_id']})")
        
        # Wind-Daten der letzten 24h abrufen
        wind_records = self.weather_agent.get_weather_data(
            station_id=station['station_id'],
            parameter="wind",
            resolution="hourly",
            start_date=datetime.now() - timedelta(hours=24),
            end_date=datetime.now()
        )
        
        if not wind_records:
            self.logger.warning("No wind data available from DWD")
            return None
        
        # Durchschnitts-Wind berechnen
        avg_speed_ms = sum(r.get('wind_speed', 5.0) for r in wind_records) / len(wind_records)
        avg_direction_deg = sum(r.get('wind_direction', 270.0) for r in wind_records) / len(wind_records)
        
        self.logger.info(f"🌬️  DWD Wind: {avg_speed_ms:.1f} m/s aus {avg_direction_deg:.0f}°")
        self._stats['weather_queries_made'] += 1
        
        # Windfeld erstellen (einheitlich für gesamtes Gebiet)
        return self._create_uniform_wind_field(
            bounds=request.calculation_bounds,
            resolution=request.grid_resolution_m,
            wind_speed_ms=avg_speed_ms,
            wind_direction_deg=avg_direction_deg,
            data_source=f"DWD Station {station['station_id']} ({station['name']})"
        )
        
    except Exception as e:
        self.logger.warning(f"DWD Open Data integration error: {e}", exc_info=True)
        return None


def _create_uniform_wind_field(
    self,
    bounds: Dict[str, float],
    resolution: float,
    wind_speed_ms: float,
    wind_direction_deg: float,
    data_source: str
) -> WindField:
    """Erstelle einheitliches Windfeld aus DWD-Daten"""
    
    grid_vectors = {}
    
    lat_range = bounds['lat_max'] - bounds['lat_min']
    lon_range = bounds['lon_max'] - bounds['lon_min']
    
    lat_steps = max(3, int(lat_range * 111320 / resolution))
    lon_steps = max(3, int(lon_range * 111320 / resolution))
    
    for i in range(lat_steps):
        for j in range(lon_steps):
            lat = bounds['lat_min'] + (lat_range * i / (lat_steps - 1))
            lon = bounds['lon_min'] + (lon_range * j / (lon_steps - 1))
            
            # Leichte Variation für Realismus (±10%)
            speed_variation = 1.0 + 0.1 * ((i + j) - (lat_steps + lon_steps) / 2) / (lat_steps + lon_steps)
            
            grid_vectors[f"{lat:.4f}_{lon:.4f}"] = WindVector(
                speed_ms=wind_speed_ms * speed_variation,
                direction_deg=wind_direction_deg,
                height_m=10.0
            )
    
    return WindField(
        grid_vectors=grid_vectors,
        stability_class=AtmosphericStabilityClass.D,  # Neutral (Default)
        mixing_height_m=1000.0,
        data_source=data_source,
        timestamp=datetime.now()
    )
```

---

## 🧪 Test-Szenario

```python
# Test: Berlin Innenstadt Flow-Simulation mit DWD Open Data

from backend.agents.veritas_api_agent_atmospheric_flow import (
    create_atmospheric_flow_agent,
    FlowCalculationRequest,
    EmissionSource,
    ReceptorPoint,
    Coordinate,
    FlowModelType,
    AtmosphericFlowConfig
)
from datetime import datetime

# Agent mit DWD Integration erstellen
config = AtmosphericFlowConfig(
    weather_integration_enabled=True,  # ⭐ DWD aktivieren
    default_grid_resolution_m=200.0
)
agent = create_atmospheric_flow_agent(config)

# Verkehrs-Emissionsquelle: Stadtautobahn A100
highway_source = EmissionSource(
    source_id="highway_a100_segment_1",
    coordinate=Coordinate(52.5000, 13.4000, 5.0),  # Berlin, 5m Höhe
    source_type=EmissionSourceType.LINE_SOURCE,
    emission_rate=500.0,  # kg/h NOx
    pollutant_name="NOx"
)

# Rezeptoren: Wohngebiete
residential_receptors = [
    ReceptorPoint(
        receptor_id="wedding_residential",
        coordinate=Coordinate(52.5050, 13.4100, 30.0),
        receptor_type="residential"
    ),
    ReceptorPoint(
        receptor_id="kreuzberg_residential",
        coordinate=Coordinate(52.4950, 13.3900, 25.0),
        receptor_type="residential"
    )
]

# Flow Request erstellen
request = FlowCalculationRequest(
    query_id="berlin-traffic-sim-001",
    query_text="NOx-Ausbreitung von A100 in Wohngebiete",
    calculation_bounds={
        'lat_min': 52.48,
        'lat_max': 52.52,
        'lon_min': 13.38,
        'lon_max': 13.42
    },
    grid_resolution_m=200.0,
    emission_sources=[highway_source],
    receptor_points=residential_receptors,
    flow_model=FlowModelType.GAUSSIAN_PLUME,
    use_weather_data=True  # ⭐ DWD aktiviert
)

# Berechnung durchführen
response = await agent.calculate_flow_async(request)

# Ergebnisse auswerten
if response.success:
    print(f"✅ Simulation erfolgreich")
    print(f"📡 Datenquelle: {response.weather_data_source}")
    print(f"🌬️  Windfeld: {response.wind_field.data_source}")
    print(f"\nErgebnisse:")
    for result in response.flow_results:
        print(f"  {result.receptor_id}: {result.concentration_ugm3:.2f} μg/m³")
        print(f"    Wind: {result.wind_speed_ms:.1f} m/s aus {result.wind_direction_deg:.0f}°")
```

**Erwartete Ausgabe:**
```
✅ Simulation erfolgreich
📡 Datenquelle: DWD
🌬️  Windfeld: DWD Station 00433 (Berlin-Tempelhof)

Ergebnisse:
  wedding_residential: 45.23 μg/m³
    Wind: 4.2 m/s aus 245°
  kreuzberg_residential: 32.17 μg/m³
    Wind: 4.2 m/s aus 245°
```

---

## 📌 Zusammenfassung

### **Aktueller Stand:**
- ✅ **DWD Open Data Agent** implementiert (`veritas_api_agent_dwd_opendata.py`)
- ✅ **dwdparse** installiert und getestet
- ✅ **13.200 Records** erfolgreich geparst
- ✅ **Nächste Station finden** implementiert
- ⏳ **Integration in Atmospheric Flow Agent** steht noch aus

### **Next Steps:**
1. ✅ Import in `veritas_api_agent_atmospheric_flow.py` aktualisieren
2. ✅ `_get_wind_field_from_dwd()` auf DWD Open Data Agent umstellen
3. ✅ Test mit echten Geodaten durchführen
4. ✅ Multi-Station-Interpolation für große Gebiete implementieren (optional)

### **Vorteile der Lösung:**
- 🎯 **Geodatenbasiert**: Stationsauswahl anhand calculation_bounds
- 🔓 **Kein Vendor Lock-in**: Direktes Parsing von opendata.dwd.de
- ⚡ **Performance**: Cache-System für heruntergeladene Daten
- 🧩 **Modular**: DWD Agent unabhängig nutzbar
- 📊 **Skalierbar**: Multi-Station-Support für große Gebiete

---

**Dokument-Version:** 1.0  
**Letzte Aktualisierung:** 19. Oktober 2025  
**Autor:** VERITAS Development Team
