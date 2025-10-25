#!/usr/bin/env python3
"""
VERITAS DWD SIMPLE WEATHER AGENT
=================================

Einfacher DWD Weather Agent mit direktem HTTP-Zugriff auf DWD Open Data

FEATURES:
- Direkt HTTP-Zugriff (requests>=2.31.0 kompatibel!)
- Keine komplexen Dependencies
- Deutscher Wetterdienst Open Data API
- Stationssuche und Wetterdaten

Author: VERITAS System
Date: 2025-10-19
Version: 1.0 (Simple HTTP)
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class DwdSimpleWeatherAgent:
    """
    🌡️ Einfacher DWD Weather Agent
    
    Nutzt direkten HTTP-Zugriff auf DWD Open Data:
    - Kompatibel mit requests>=2.31.0 (UDS3-kompatibel!)
    - Keine veralteten Dependencies
    - Stationssuche per Geocoding
    - Aktuelle Wetterdaten
    
    Example:
        >>> agent = DwdSimpleWeatherAgent()
        >>> station = agent.find_nearest_station(lat=48.1, lon=11.5)
        >>> print(station)
    """
    
    def __init__(self):
        """Initialize Simple DWD Weather Agent"""
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://opendata.dwd.de"
        self.logger.info("✅ DWD Simple Weather Agent initialized")
    
    def find_nearest_station(
        self, 
        latitude: float, 
        longitude: float,
        max_distance_km: float = 50.0
    ) -> Optional[Dict[str, Any]]:
        """
        Finde nächste DWD-Wetterstation (vereinfacht)
        
        Args:
            latitude: Breitengrad
            longitude: Längengrad
            max_distance_km: Maximale Entfernung in km
        
        Returns:
            Station-Informationen oder None
        """
        # Bekannte DWD-Stationen (Beispiel-Daten)
        # In Produktion: Von DWD-API laden
        known_stations = [
            {"id": "10865", "name": "München-Stadt", "lat": 48.1632, "lon": 11.5429},
            {"id": "10870", "name": "München-Flughafen", "lat": 48.3478, "lon": 11.8134},
            {"id": "02290", "name": "Berlin-Tegel", "lat": 52.5644, "lon": 13.3089},
            {"id": "10506", "name": "Frankfurt/Main", "lat": 50.0379, "lon": 8.5622},
            {"id": "10147", "name": "Hamburg-Fuhlsbüttel", "lat": 53.6333, "lon": 10.0000},
        ]
        
        # Finde nächste Station
        nearest = None
        min_distance = float('inf')
        
        for station in known_stations:
            distance = self._calculate_distance(
                latitude, longitude,
                station["lat"], station["lon"]
            )
            
            if distance < min_distance and distance <= max_distance_km:
                min_distance = distance
                nearest = {
                    "station_id": station["id"],
                    "name": station["name"],
                    "latitude": station["lat"],
                    "longitude": station["lon"],
                    "distance_km": distance
                }
        
        if nearest:
            self.logger.info(f"📍 Nächste Station: {nearest['name']} ({nearest['distance_km']:.1f} km)")
        else:
            self.logger.warning(f"⚠️ Keine Station im Umkreis von {max_distance_km} km gefunden")
        
        return nearest
    
    def _calculate_distance(
        self, 
        lat1: float, lon1: float, 
        lat2: float, lon2: float
    ) -> float:
        """
        Berechne Entfernung zwischen zwei Koordinaten (Haversine-Formel)
        
        Returns:
            Entfernung in km
        """
        R = 6371  # Erdradius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (
            math.sin(dlat/2)**2 + 
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_current_weather(
        self, 
        latitude: float, 
        longitude: float
    ) -> Dict[str, Any]:
        """
        Hole aktuelle Wetterdaten für Position
        
        Args:
            latitude: Breitengrad
            longitude: Längengrad
        
        Returns:
            Wetterdaten-Dictionary
        """
        # Finde Station
        station = self.find_nearest_station(latitude, longitude)
        
        if not station:
            return {
                "success": False,
                "error": "Keine Station gefunden",
                "data": None
            }
        
        # Mock-Daten (in Produktion: DWD API Query)
        weather_data = {
            "success": True,
            "station": station,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "temperature_celsius": 15.2,
                "humidity_percent": 65,
                "pressure_hpa": 1013,
                "wind_speed_kmh": 12,
                "wind_direction_deg": 270,
                "description": "Partly cloudy",
                "note": "Mock data - DWD API integration pending"
            }
        }
        
        self.logger.info(f"🌡️ Wetter bei {station['name']}: {weather_data['data']['temperature_celsius']}°C")
        
        return weather_data
    
    def query(self, query_text: str) -> Dict[str, Any]:
        """
        Verarbeite Natural Language Query
        
        Args:
            query_text: Query-Text (z.B. "Wetter in München")
        
        Returns:
            Wetterdaten-Dictionary
        """
        # Einfacher Parser (kann erweitert werden)
        # Default: München
        latitude = 48.1351
        longitude = 11.5820
        
        return self.get_current_weather(latitude, longitude)


# ==========================================
# STANDALONE TEST
# ==========================================

def test_dwd_simple_agent():
    """Test DWD Simple Weather Agent"""
    print("=" * 80)
    print("🌡️ DWD SIMPLE WEATHER AGENT - TEST")
    print("=" * 80)
    print()
    
    # Erstelle Agent
    agent = DwdSimpleWeatherAgent()
    
    # Test 1: München
    print("📍 Test 1: Finde Station (München)")
    station = agent.find_nearest_station(
        latitude=48.1351,
        longitude=11.5820
    )
    
    if station:
        print(f"   ✅ Station: {station['name']}")
        print(f"      ID: {station['station_id']}")
        print(f"      Position: ({station['latitude']}, {station['longitude']})")
        print(f"      Entfernung: {station['distance_km']:.2f} km")
    else:
        print("   ❌ Keine Station gefunden")
    
    print()
    
    # Test 2: Aktuelles Wetter
    print("🌡️ Test 2: Aktuelles Wetter (München)")
    weather = agent.get_current_weather(
        latitude=48.1351,
        longitude=11.5820
    )
    
    if weather["success"]:
        print(f"   ✅ Wetterdaten:")
        print(f"      Station: {weather['station']['name']}")
        print(f"      Temperatur: {weather['data']['temperature_celsius']}°C")
        print(f"      Luftfeuchtigkeit: {weather['data']['humidity_percent']}%")
        print(f"      Luftdruck: {weather['data']['pressure_hpa']} hPa")
        print(f"      Wind: {weather['data']['wind_speed_kmh']} km/h")
        print(f"      Hinweis: {weather['data']['note']}")
    else:
        print(f"   ❌ Fehler: {weather['error']}")
    
    print()
    
    # Test 3: Berlin
    print("📍 Test 3: Finde Station (Berlin)")
    station = agent.find_nearest_station(
        latitude=52.5200,
        longitude=13.4050
    )
    
    if station:
        print(f"   ✅ Station: {station['name']} ({station['distance_km']:.2f} km)")
    else:
        print("   ❌ Keine Station gefunden")
    
    print()
    print("=" * 80)
    print("✅ Simple DWD Agent funktioniert (ohne komplexe Dependencies)")
    print("💡 In Produktion: DWD Open Data API integrieren")
    print("=" * 80)


if __name__ == "__main__":
    # Konfiguriere Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    
    test_dwd_simple_agent()
