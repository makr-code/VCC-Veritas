#!/usr/bin/env python3
"""
VERITAS BRIGHT SKY WEATHER AGENT
=================================

Spezialisierter Agent für deutsche Wetterdaten via Bright Sky API

Bright Sky ist ein kostenloses REST API für DWD-Wetterdaten:
- Einfache HTTP REST API (requests kompatibel!)
- Historische Wetterdaten
- Wettervorhersagen (MOSMIX)
- Stations-Informationen
- Keine Installation notwendig

API Dokumentation: https://brightsky.dev/docs/

VERWENDUNG:
- Eingabe: Ort (Lat/Lon), Datum
- Ausgabe: Wetterdaten (Temperatur, Niederschlag, Wind, etc.)

Author: VERITAS System
Date: 2025-10-19
Version: 1.0 (Bright Sky Integration)
"""

import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Bright Sky API Configuration
BRIGHTSKY_API_URL = "https://api.brightsky.dev"
BRIGHTSKY_WEATHER_ENDPOINT = f"{BRIGHTSKY_API_URL}/weather"
BRIGHTSKY_CURRENT_ENDPOINT = f"{BRIGHTSKY_API_URL}/current_weather"
BRIGHTSKY_ALERTS_ENDPOINT = f"{BRIGHTSKY_API_URL}/alerts"


@dataclass
class WeatherQuery:
    """Query-Request für Bright Sky Weather Agent"""
    latitude: float
    longitude: float
    date: Optional[datetime] = None
    last_date: Optional[datetime] = None
    
    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now() - timedelta(days=1)
        if self.last_date is None:
            self.last_date = datetime.now()


class BrightSkyWeatherAgent:
    """
    🌤️ Bright Sky Weather Agent - DWD Wetterdaten via REST API
    
    Nutzt die kostenlose Bright Sky API für:
    - Historische Wetterdaten (ab 2010)
    - Aktuelle Wetterdaten
    - 10-Tage Wettervorhersage (MOSMIX)
    - Wetterwarnungen
    
    Vorteile:
    - ✅ Keine Installation (nur requests)
    - ✅ requests>=2.31.0 kompatibel
    - ✅ Einfache REST API
    - ✅ Kostenlos und Open Source
    
    Example:
        >>> agent = BrightSkyWeatherAgent()
        >>> result = agent.get_current_weather(
        ...     latitude=48.1351,
        ...     longitude=11.5820
        ... )
        >>> print(result['temperature'])
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize Bright Sky Weather Agent
        
        Args:
            timeout: HTTP request timeout in seconds
        """
        self.logger = logging.getLogger(__name__)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VERITAS-Agent/1.0'
        })
        
        # Test API Verfügbarkeit
        try:
            response = self.session.get(BRIGHTSKY_API_URL, timeout=5)
            if response.status_code == 200:
                self.logger.info("✅ Bright Sky API verfügbar")
                self.available = True
            else:
                self.logger.warning(f"⚠️ Bright Sky API Status: {response.status_code}")
                self.available = False
        except Exception as e:
            self.logger.error(f"❌ Bright Sky API nicht erreichbar: {e}")
            self.available = False
    
    def get_current_weather(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """
        Hole aktuelles Wetter für Position
        
        Args:
            latitude: Breitengrad
            longitude: Längengrad
        
        Returns:
            Aktuelles Wetter-Dictionary
        """
        if not self.available:
            return {
                "success": False,
                "error": "Bright Sky API nicht verfügbar",
                "data": None
            }
        
        try:
<<<<<<< Updated upstream
            params = {
                "lat": latitude,
                "lon": longitude
            }
            
            response = self.session.get(
                BRIGHTSKY_CURRENT_ENDPOINT,
                params=params,
                timeout=self.timeout
            )
=======
            params: Dict[str, Any] = {"lat": latitude, "lon": longitude}

            response = self.session.get(BRIGHTSKY_CURRENT_ENDPOINT, params=params, timeout=self.timeout)
>>>>>>> Stashed changes
            response.raise_for_status()
            
            data = response.json()
            
            if "weather" in data:
                weather = data["weather"]
                
                return {
                    "success": True,
                    "location": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "current_weather": {
                        "timestamp": weather.get("timestamp"),
                        "temperature": weather.get("temperature"),
                        "precipitation": weather.get("precipitation"),
                        "wind_speed": weather.get("wind_speed"),
                        "wind_direction": weather.get("wind_direction"),
                        "cloud_cover": weather.get("cloud_cover"),
                        "pressure": weather.get("pressure_msl"),
                        "sunshine": weather.get("sunshine"),
                        "condition": weather.get("condition"),
                        "icon": weather.get("icon")
                    },
                    "sources": data.get("sources", [])
                }
            else:
                return {
                    "success": False,
                    "error": "Keine Wetterdaten verfügbar",
                    "data": None
                }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ API Request Fehler: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def get_weather_history(
        self,
        latitude: float,
        longitude: float,
        date: datetime,
        last_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Hole Wetterdaten für Zeitraum
        
        Args:
            latitude: Breitengrad
            longitude: Längengrad
            date: Start-Datum
            last_date: End-Datum (optional, default: heute)
        
        Returns:
            Historische Wetterdaten
        """
        if not self.available:
            return {
                "success": False,
                "error": "Bright Sky API nicht verfügbar",
                "data": []
            }
        
        if last_date is None:
            last_date = datetime.now()
        
        try:
            params: Dict[str, Any] = {
                "lat": latitude,
                "lon": longitude,
                "date": date.strftime("%Y-%m-%d"),
                "last_date": last_date.strftime("%Y-%m-%d")
            }
            
            response = self.session.get(
                BRIGHTSKY_WEATHER_ENDPOINT,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "weather" in data:
                return {
                    "success": True,
                    "location": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "timerange": {
                        "start": date.isoformat(),
                        "end": last_date.isoformat()
                    },
                    "weather": data["weather"],
                    "count": len(data["weather"]),
                    "sources": data.get("sources", [])
                }
            else:
                return {
                    "success": False,
                    "error": "Keine Wetterdaten verfügbar",
                    "data": []
                }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ API Request Fehler: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
    def get_weather_alerts(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """
        Hole aktuelle Wetterwarnungen
        
        Args:
            latitude: Breitengrad
            longitude: Längengrad
        
        Returns:
            Wetterwarnungen
        """
        if not self.available:
            return {
                "success": False,
                "error": "Bright Sky API nicht verfügbar",
                "alerts": []
            }
        
        try:
<<<<<<< Updated upstream
            params = {
                "lat": latitude,
                "lon": longitude
            }
            
            response = self.session.get(
                BRIGHTSKY_ALERTS_ENDPOINT,
                params=params,
                timeout=self.timeout
            )
=======
            params: Dict[str, Any] = {"lat": latitude, "lon": longitude}

            response = self.session.get(BRIGHTSKY_ALERTS_ENDPOINT, params=params, timeout=self.timeout)
>>>>>>> Stashed changes
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "alerts": data.get("alerts", []),
                "count": len(data.get("alerts", []))
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ API Request Fehler: {e}")
            return {
                "success": False,
                "error": str(e),
                "alerts": []
            }
    
    def query(self, query_text: str) -> Dict[str, Any]:
        """
        Verarbeite Natural Language Query
        
        Args:
            query_text: Query-Text (z.B. "Wetter in München")
        
        Returns:
            Wetterdaten-Dictionary
        """
        # Einfacher Parser (kann später erweitert werden)
        # Beispiel: "Wetter in München" → lat=48.1, lon=11.5
        
        # Standard: München
        latitude = 48.1351
        longitude = 11.5820
        
        # Hole aktuelles Wetter
        return self.get_current_weather(latitude, longitude)


# ==========================================
# STANDALONE TEST
# ==========================================

def test_brightsky_weather_agent():
    """Test Bright Sky Weather Agent"""
    print("=" * 80)
    print("🌤️ BRIGHT SKY WEATHER AGENT - TEST")
    print("=" * 80)
    print()
    
    # Erstelle Agent
    agent = BrightSkyWeatherAgent()
    
    if not agent.available:
        print("❌ Bright Sky API nicht verfügbar!")
        print("   Prüfe Internetverbindung")
        return
    
    # Test 1: Aktuelles Wetter (München)
    print("📍 Test 1: Aktuelles Wetter (München)")
    result = agent.get_current_weather(
        latitude=48.1351,
        longitude=11.5820
    )
    
    if result["success"]:
        weather = result["current_weather"]
        print(f"   ✅ Wetterdaten erfolgreich abgerufen")
        print(f"      Zeit: {weather.get('timestamp')}")
        print(f"      Temperatur: {weather.get('temperature')}°C")
        print(f"      Niederschlag: {weather.get('precipitation')} mm")
        print(f"      Windgeschwindigkeit: {weather.get('wind_speed')} m/s")
        print(f"      Bewölkung: {weather.get('cloud_cover')}%")
        print(f"      Bedingung: {weather.get('condition')}")
    else:
        print(f"   ❌ Fehler: {result['error']}")
    
    print()
    
    # Test 2: Wetterhistorie (letzte 3 Tage)
    print("📊 Test 2: Wetterhistorie (München, letzte 3 Tage)")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)
    
    result = agent.get_weather_history(
        latitude=48.1351,
        longitude=11.5820,
        date=start_date,
        last_date=end_date
    )
    
    if result["success"]:
        print(f"   ✅ {result['count']} Datenpunkte gefunden")
        print(f"   📅 Zeitraum: {result['timerange']['start']} bis {result['timerange']['end']}")
        
        # Zeige erste 5 Werte
        if result['weather']:
            print(f"\n   📈 Erste 5 Messwerte:")
            for i, measurement in enumerate(result['weather'][:5], 1):
                print(f"      {i}. {measurement.get('timestamp')}: {measurement.get('temperature')}°C")
    else:
        print(f"   ❌ Fehler: {result['error']}")
    
    print()
    
    # Test 3: Wetterwarnungen
    print("⚠️ Test 3: Wetterwarnungen (München)")
    result = agent.get_weather_alerts(
        latitude=48.1351,
        longitude=11.5820
    )
    
    if result["success"]:
        if result['count'] > 0:
            print(f"   ⚠️ {result['count']} Warnung(en) aktiv:")
            for alert in result['alerts']:
                print(f"      - {alert.get('headline')}")
        else:
            print("   ✅ Keine aktiven Wetterwarnungen")
    else:
        print(f"   ❌ Fehler: {result['error']}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    # Konfiguriere Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    
    test_brightsky_weather_agent()
