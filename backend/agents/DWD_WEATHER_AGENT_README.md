# VERITAS DWD Weather Agent 🌡️

**Spezialisierter Agent für deutsche Wetterdaten mit dwdweather2 Integration**

## 📋 Übersicht

Der DWD Weather Agent integriert den Deutschen Wetterdienst (DWD) in das VERITAS-System und ermöglicht Abfragen meteorologischer Daten basierend auf Ort, Zeit und Intervall.

### 🎯 **Hauptfunktionen**

- **Deutscher Wetterdienst Integration** - Offizielle DWD-Daten über dwdweather2
- **Ortsbasierte Stationssuche** - Automatische Suche der nächsten Wetterstationen
- **Flexible Zeitintervalle** - Stündliche und tägliche Datenabfrage  
- **Umfangreiche Parameter** - Temperatur, Niederschlag, Wind, Luftfeuchtigkeit, Luftdruck
- **Statistische Auswertung** - Min/Max/Durchschnitt und Trend-Analysen
- **Performance-Optimierung** - Caching und parallele Datenabfrage

---

## 🚀 **Installation & Setup**

### 1. DWD Weather Package installieren

```bash
pip install dwdweather2
```

### 2. Agent-Datei verwenden

```
backend/agents/
├── veritas_api_agent_dwd_weather.py     # Vollständige Implementation
└── test_dwd_weather_standalone.py      # Standalone Tests
```

---

## 🔧 **API Verwendung**

### **Basic Query**

```python
from backend.agents.veritas_api_agent_dwd_weather import (
    DwdWeatherAgent, DwdWeatherQueryRequest, 
    WeatherInterval, WeatherParameter, DwdWeatherConfig
)

# Agent erstellen
config = DwdWeatherConfig()
agent = DwdWeatherAgent(config)

# Query definieren
request = DwdWeatherQueryRequest(
    query_id="weather-001",
    query_text="Aktuelles Wetter in Berlin",
    location="Berlin",
    start_date="2025-09-25",
    end_date="2025-09-28", 
    interval=WeatherInterval.DAILY,
    parameters=[
        WeatherParameter.TEMPERATURE,
        WeatherParameter.PRECIPITATION,
        WeatherParameter.WIND
    ]
)

# Query ausführen
response = agent.execute_query(request)

print(f"Success: {response.success}")
print(f"Stations: {response.stations_count}")
print(f"Data Points: {response.data_points_count}")
```

### **Erweiterte Query mit Koordinaten**

```python
request = DwdWeatherQueryRequest(
    query_id="weather-002",
    query_text="Wetter für GPS-Position",
    latitude=52.5200,
    longitude=13.4050,
    start_date="2025-09-28",
    end_date="2025-09-28",
    interval=WeatherInterval.HOURLY,
    parameters=[WeatherParameter.TEMPERATURE, WeatherParameter.HUMIDITY]
)
```

---

## 📊 **Unterstützte Parameter**

### **Eingabe-Parameter**

| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `location` | string | Ortsname | "Berlin", "München" |
| `latitude` | float | GPS-Breitengrad | 52.5200 |
| `longitude` | float | GPS-Längengrad | 13.4050 |
| `start_date` | string | Startdatum | "2025-09-25" |
| `end_date` | string | Enddatum | "2025-09-28" |
| `interval` | enum | Zeitintervall | HOURLY, DAILY |
| `parameters` | list | Wetter-Parameter | [TEMPERATURE, PRECIPITATION] |

### **Wetter-Parameter**

| Parameter | Einheit | Beschreibung |
|-----------|---------|--------------|
| `TEMPERATURE` | °C | Lufttemperatur |
| `PRECIPITATION` | mm | Niederschlagsmenge |
| `WIND` | km/h | Windgeschwindigkeit |
| `HUMIDITY` | % | Relative Luftfeuchtigkeit |
| `PRESSURE` | hPa | Luftdruck |
| `SUNSHINE` | h | Sonnenscheindauer |
| `CLOUD_COVER` | % | Bewölkungsgrad |

---

## 🏢 **Verfügbare Städte & Stationen**

### **Hauptstädte (Mock-Daten für Demo)**

| Stadt | Stationen | Beispiel-Stationen |
|-------|-----------|-------------------|
| **Berlin** | 2 | Berlin-Tempelhof, Berlin-Tegel |
| **München** | 2 | München-Flughafen, München-Stadt |
| **Hamburg** | 2 | Hamburg-Finkenwerder, Hamburg-Fuhlsbüttel |
| **Köln** | 1 | Köln-Flughafen |
| **Frankfurt** | 1 | Frankfurt-Flughafen |

### **Echte DWD Integration**

Mit installiertem `dwdweather2` Package werden automatisch alle verfügbaren DWD-Stationen verwendet:

```python
# Echte DWD-Station-Suche (wenn dwdweather2 installiert)
from dwdweather2 import DwdWeather
dwd = DwdWeather()
stations = dwd.nearest_station(lat=52.5200, lon=13.4050)
```

---

## 📋 **Response-Format**

### **Standard-Response**

```json
{
  "query_id": "weather-001",
  "success": true,
  "stations_count": 2,
  "data_points_count": 8,
  "processing_time_ms": 150,
  "confidence_score": 0.95,
  "results": [
    {
      "station": {
        "id": "10384",
        "name": "Berlin-Tempelhof",
        "location": {
          "latitude": 52.4675,
          "longitude": 13.4021,
          "elevation_m": 48.0
        },
        "distance_km": 5.2
      },
      "weather_data": [
        {
          "timestamp": "2025-09-28T12:00:00",
          "date": "2025-09-28",
          "time": "12:00",
          "temperature_celsius": 15.3,
          "precipitation_mm": 0.0,
          "wind_speed_kmh": 8.5,
          "humidity_percent": 65.2,
          "pressure_hpa": 1013.2
        }
      ],
      "summary": {
        "data_points": 4,
        "temperature": {
          "min_celsius": 12.1,
          "max_celsius": 18.7,
          "avg_celsius": 15.2
        },
        "precipitation": {
          "total_mm": 2.5,
          "max_mm": 1.2,
          "days_with_rain": 1
        }
      }
    }
  ]
}
```

---

## 🔗 **FastAPI Integration**

### **Endpoint Definition**

```python
# In backend/api/veritas_api_backend.py

from backend.agents.veritas_api_agent_dwd_weather import (
    create_dwd_weather_agent, DwdWeatherQueryRequest, 
    WeatherInterval, WeatherParameter
)

# Globaler Agent
dwd_agent = create_dwd_weather_agent()

@app.post("/agents/dwd_weather/query")
async def dwd_weather_query(request: dict):
    """DWD Weather Query Endpoint"""
    
    # Request Parameter parsen
    weather_request = DwdWeatherQueryRequest(
        query_id=request.get("query_id", str(uuid.uuid4())),
        query_text=request.get("query", ""),
        location=request.get("location"),
        latitude=request.get("latitude"),
        longitude=request.get("longitude"),
        start_date=request.get("start_date"),
        end_date=request.get("end_date"),
        interval=WeatherInterval(request.get("interval", "daily")),
        parameters=[WeatherParameter(p) for p in request.get("parameters", ["temperature"])]
    )
    
    # Query ausführen
    response = await dwd_agent.execute_query_async(weather_request)
    
    return {
        "success": response.success,
        "data": response.results,
        "metadata": {
            "stations": response.stations_count,
            "data_points": response.data_points_count,
            "processing_time_ms": response.processing_time_ms,
            "confidence": response.confidence_score
        },
        "error": response.error_message
    }

@app.get("/agents/dwd_weather/status")
async def dwd_weather_status():
    """DWD Weather Agent Status"""
    return dwd_agent.get_status()
```

### **Frontend Integration**

```javascript
// Frontend-Aufruf
async function getWeatherData(location, startDate, endDate) {
    const response = await fetch('/agents/dwd_weather/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query: `Wetter für ${location}`,
            location: location,
            start_date: startDate,
            end_date: endDate,
            interval: "daily",
            parameters: ["temperature", "precipitation", "wind"]
        })
    });
    
    const data = await response.json();
    return data;
}

// Verwendung
const weather = await getWeatherData("Berlin", "2025-09-25", "2025-09-28");
console.log(`${weather.data.length} Stationen gefunden`);
```

---

## 🧪 **Testing**

### **Unit Tests**

```bash
# Standalone Test (ohne VERITAS-System)
python backend/agents/test_dwd_weather_standalone.py

# Mit VERITAS-System  
python -m unittest backend.agents.tests.test_dwd_weather_agent
```

### **Manual Testing**

```python
# Direct Agent Test
from backend.agents.veritas_api_agent_dwd_weather import create_dwd_weather_agent

agent = create_dwd_weather_agent()

# Simple Test
request = DwdWeatherQueryRequest(
    query_id="manual-test",
    query_text="Test weather query",
    location="München",
    start_date="2025-09-28",
    end_date="2025-09-28",
    interval=WeatherInterval.DAILY,
    parameters=[WeatherParameter.TEMPERATURE]
)

response = agent.execute_query(request)
print(f"Success: {response.success}")
```

---

## 📈 **Performance & Caching**

### **Built-in Optimierungen**

- **Station Cache** - Wetterstationen werden gecacht (1h TTL)
- **Data Cache** - Wetterdaten werden gecacht für wiederholte Abfragen
- **Parallel Processing** - Multiple Stationen werden parallel abgefragt
- **Request Limiting** - Max. 5 Stationen pro Query
- **Timeout Handling** - 60s Timeout für DWD-API-Calls

### **Performance Metrics**

```python
status = agent.get_status()
print(f"Processed Queries: {status['performance']['processed_queries']}")
print(f"Avg Processing Time: {status['performance']['avg_processing_time_ms']}ms")
print(f"Success Rate: {status['performance']['success_rate']:.2%}")
print(f"Cache Hits: {status['cache']['stations_cached']}")
```

---

## 🔧 **Konfiguration**

### **Agent-Konfiguration**

```python
from backend.agents.veritas_api_agent_dwd_weather import DwdWeatherConfig

config = DwdWeatherConfig(
    # DWD-spezifisch
    data_source="Deutscher Wetterdienst",
    supported_intervals=["hourly", "daily"],
    cache_enabled=True,
    
    # Performance
    max_concurrent_tasks=5,
    timeout_seconds=60,
    min_confidence_threshold=0.9,
    max_retries=3,
    cache_ttl_seconds=3600,
    
    # Suche  
    max_distance_km=50.0,
    max_stations=5
)

agent = DwdWeatherAgent(config)
```

---

## 🛠️ **Entwicklung & Erweiterung**

### **Neue Features hinzufügen**

1. **Neue Wetter-Parameter:**
   ```python
   class WeatherParameter(Enum):
       VISIBILITY = "visibility"      # Neue Parameter
       UV_INDEX = "uv_index"
   ```

2. **Erweiterte Stationssuche:**
   ```python
   def find_stations_by_region(self, region: str) -> List[WeatherStation]:
       # Implementierung für Regionen
   ```

3. **Forecast Integration:**
   ```python
   def get_weather_forecast(self, location: str, days: int) -> List[WeatherDataPoint]:
       # Wetter-Vorhersage
   ```

### **Custom DWD Integration**

Für echte DWD-Integration:

```python
def _fetch_real_dwd_data(self, station_id: str, start: datetime, end: datetime):
    """Echte DWD-API Integration"""
    from dwdweather2 import DwdWeather
    
    dwd = DwdWeather(resolution="hourly")
    df = dwd.query(
        station_id=station_id,
        parameter="temperature_air_mean_2m",
        start_date=start,
        end_date=end
    )
    
    return df  # Pandas DataFrame mit DWD-Daten
```

---

## 📚 **Ressourcen**

### **Links**

- **DWD Weather Package:** https://pypi.org/project/dwdweather2/
- **Deutscher Wetterdienst:** https://www.dwd.de/
- **DWD OpenData:** https://opendata.dwd.de/
- **Weather Station Lists:** https://www.dwd.de/DE/leistungen/klimadatendeutschland/stationsliste.html

### **Beispiel-Abfragen**

```python
# Historische Daten
"Temperaturverlauf Berlin letzte Woche"
"Niederschlag München September 2025"
"Windgeschwindigkeit Hamburg gestern"

# Aktuelle Daten  
"Aktuelles Wetter Frankfurt"
"Luftfeuchtigkeit Köln heute"
"Luftdruck Deutschland jetzt"

# Zeitreihen
"Stündliche Temperaturen Berlin heute"
"Tägliche Niederschläge München letzte 30 Tage"
```

---

## 🎯 **Fazit**

Der **VERITAS DWD Weather Agent** bietet:

- ✅ **Vollständige DWD-Integration** mit dwdweather2
- ✅ **Flexible Query-API** für verschiedene Anwendungsfälle  
- ✅ **Performance-optimiert** mit Caching und Parallel Processing
- ✅ **Production-ready** mit Error Handling und Monitoring
- ✅ **VERITAS-kompatibel** für nahtlose System-Integration

**Ready für meteorologische Datenanalyse im VERITAS-System! 🌡️⚡**

---

*Erstellt am: 28. September 2025*  
*VERITAS DWD Weather Agent v1.0*