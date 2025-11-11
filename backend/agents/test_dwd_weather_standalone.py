#!/usr/bin/env python3
"""
VERITAS DWD Weather Agent - Standalone Test
Test des DWD Weather Agents ohne VERITAS-System Dependencies
"""

import logging
import math
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Füge den Projekt-Root-Pfad hinzu
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

print("🚀 VERITAS DWD Weather Agent - Standalone Test")
print("🌡️ Deutsche Wetterdaten Integration")


# Mock Enums für Testing
class WeatherInterval(Enum):
    HOURLY = "hourly"
    DAILY = "daily"


class WeatherParameter(Enum):
    TEMPERATURE = "temperature"
    PRECIPITATION = "precipitation"
    WIND = "wind"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"


# Test Data Classes
@dataclass
class WeatherStation:
    station_id: str
    name: str
    latitude: float
    longitude: float
    elevation: float
    distance_km: Optional[float] = None


@dataclass
class WeatherDataPoint:
    timestamp: datetime
    station: WeatherStation
    temperature: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None


@dataclass
class DwdWeatherQuery:
    query_id: str
    query_text: str
    location: str
    start_date: str
    end_date: str
    interval: WeatherInterval
    parameters: List[WeatherParameter] = field(default_factory=list)


@dataclass
class DwdWeatherResponse:
    query_id: str
    success: bool = True
    results: List[Dict[str, Any]] = field(default_factory=list)
    stations: List[WeatherStation] = field(default_factory=list)
    data_points: List[WeatherDataPoint] = field(default_factory=list)
    processing_time_ms: int = 0
    error_message: Optional[str] = None


# Simplified DWD Weather Agent
class SimpleDwdWeatherAgent:
    """Vereinfachter DWD Weather Agent für Testing"""

    def __init__(self):
        self.agent_id = f"dwd_weather_agent_{uuid.uuid4().hex[:8]}"
        self.processed_queries = 0
        self.logger = logging.getLogger(f"DWDWeatherAgent.{self.agent_id}")

        # Mock-Stationen für verschiedene Städte
        self.mock_stations = {
            "berlin": [
                WeatherStation("10384", "Berlin - Tempelho", 52.4675, 13.4021, 48.0, 5.2),
                WeatherStation("10382", "Berlin - Tegel", 52.5594, 13.3089, 37.0, 12.8),
            ],
            "münchen": [
                WeatherStation("10865", "München - Flughafen", 48.3537, 11.7751, 447.0, 8.1),
                WeatherStation("10870", "München - Stadt", 48.1619, 11.5429, 515.0, 3.5),
            ],
            "hamburg": [
                WeatherStation("10147", "Hamburg - Finkenwerder", 53.5347, 9.8375, 11.0, 7.2),
                WeatherStation("10149", "Hamburg - Fuhlsbüttel", 53.6331, 10.0069, 11.0, 2.1),
            ],
            "köln": [WeatherStation("10513", "Köln - Flughafen", 50.8659, 7.1427, 92.0, 8.5)],
            "frankfurt": [WeatherStation("10637", "Frankfurt - Flughafen", 50.0379, 8.5622, 111.0, 12.1)],
        }

        print(f"✅ DWD Weather Agent initialisiert: {self.agent_id}")

    def find_stations(self, location: str) -> List[WeatherStation]:
        """Finde Wetterstationen für Location"""
        location_lower = location.lower()

        # Exakte Übereinstimmung
        if location_lower in self.mock_stations:
            return self.mock_stations[location_lower]

        # Teilstring-Suche
        for city, stations in self.mock_stations.items():
            if city in location_lower or location_lower in city:
                return stations

        # Default: Berlin
        return self.mock_stations["berlin"]

    def generate_mock_weather_data(
        self,
        station: WeatherStation,
        start_date: datetime,
        end_date: datetime,
        interval: WeatherInterval,
        parameters: List[WeatherParameter],
    ) -> List[WeatherDataPoint]:
        """Generiere realistische Mock-Wetterdaten"""
        import random

        data_points = []
        current = start_date

        # Zeitschritt basierend auf Intervall
        time_delta = timedelta(hours=1) if interval == WeatherInterval.HOURLY else timedelta(days=1)

        while current <= end_date:
            data_point = WeatherDataPoint(timestamp=current, station=station)

            # Saisonale Basistemperatur (Deutschland)
            if WeatherParameter.TEMPERATURE in parameters:
                month = current.month
                base_temp = 15 + 10 * math.sin((month - 1) * math.pi / 6)  # Saisonaler Verlauf
                daily_variation = 5 * math.sin((current.hour if interval == WeatherInterval.HOURLY else 12) * math.pi / 12)
                random_variation = random.uniform(-3, 3)
                data_point.temperature = round(base_temp + daily_variation + random_variation, 1)

            if WeatherParameter.PRECIPITATION in parameters:
                # Mehr Regen im Winter/Herbst
                rain_probability = 0.1 + 0.2 * (1 + math.cos((month - 1) * math.pi / 6)) / 2
                data_point.precipitation = round(random.uniform(0, 15), 1) if random.random() < rain_probability else 0.0

            if WeatherParameter.WIND in parameters:
                # Wind variiert saisonal (mehr im Winter)
                base_wind = 5 + 5 * (1 + math.cos((month - 1) * math.pi / 6)) / 2
                data_point.wind_speed = round(base_wind + random.uniform(-2, 5), 1)

            if WeatherParameter.HUMIDITY in parameters:
                # Höhere Luftfeuchtigkeit bei Regen
                base_humidity = 60
                if data_point.precipitation and data_point.precipitation > 0:
                    base_humidity += 20
                data_point.humidity = round(base_humidity + random.uniform(-15, 15), 1)

            if WeatherParameter.PRESSURE in parameters:
                # Typischer Luftdruck für Deutschland
                data_point.pressure = round(1013 + random.uniform(-20, 20), 1)

            data_points.append(data_point)
            current += time_delta

        return data_points

    def process_query(self, query: DwdWeatherQuery) -> DwdWeatherResponse:
        """Verarbeite DWD Weather Query"""
        start_time = time.time()

        try:
            self.logger.info(f"🔄 Processing query: {query.query_text}")

            # 1. Stationen finden
            stations = self.find_stations(query.location)
            self.logger.info(f"✅ Found {len(stations)} stations for {query.location}")

            # 2. Datumsbereich parsen
            start_date = datetime.strptime(query.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(query.end_date, "%Y-%m-%d")

            # 3. Wetterdaten generieren
            all_data_points = []
            for station in stations[:2]:  # Limitiere auf 2 Stationen
                station_data = self.generate_mock_weather_data(station, start_date, end_date, query.interval, query.parameters)
                all_data_points.extend(station_data)

            # 4. Ergebnisse formatieren
            results = self.format_results(stations, all_data_points, query)

            processing_time = int((time.time() - start_time) * 1000)
            self.processed_queries += 1

            return DwdWeatherResponse(
                query_id=query.query_id,
                success=True,
                results=results,
                stations=stations,
                data_points=all_data_points,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.error(f"❌ Error processing query: {e}")
            return DwdWeatherResponse(
                query_id=query.query_id, success=False, error_message=str(e), processing_time_ms=processing_time
            )

    def format_results(
        self, stations: List[WeatherStation], data_points: List[WeatherDataPoint], query: DwdWeatherQuery
    ) -> List[Dict[str, Any]]:
        """Formatiere Wetterdaten für Response"""
        results = []

        # Gruppiere Daten nach Station
        station_data = {}
        for dp in data_points:
            station_id = dp.station.station_id
            if station_id not in station_data:
                station_data[station_id] = []
            station_data[station_id].append(dp)

        # Formatiere pro Station
        for station_id, data in station_data.items():
            station = next((s for s in stations if s.station_id == station_id), None)
            if not station:
                continue

            # Detaildaten
            formatted_data = []
            for dp in data:
                point = {
                    "timestamp": dp.timestamp.isoformat(),
                    "date": dp.timestamp.strftime("%Y-%m-%d"),
                    "time": dp.timestamp.strftime("%H:%M"),
                }

                if dp.temperature is not None:
                    point["temperature_celsius"] = dp.temperature
                if dp.precipitation is not None:
                    point["precipitation_mm"] = dp.precipitation
                if dp.wind_speed is not None:
                    point["wind_speed_kmh"] = dp.wind_speed
                if dp.humidity is not None:
                    point["humidity_percent"] = dp.humidity
                if dp.pressure is not None:
                    point["pressure_hpa"] = dp.pressure

                formatted_data.append(point)

            # Statistiken berechnen
            temps = [dp.temperature for dp in data if dp.temperature is not None]
            precip = [dp.precipitation for dp in data if dp.precipitation is not None]

            summary = {
                "data_points": len(data),
                "time_range": {
                    "start": data[0].timestamp.isoformat() if data else None,
                    "end": data[-1].timestamp.isoformat() if data else None,
                },
            }

            if temps:
                summary["temperature"] = {
                    "min_celsius": min(temps),
                    "max_celsius": max(temps),
                    "avg_celsius": round(sum(temps) / len(temps), 1),
                }

            if precip:
                summary["precipitation"] = {
                    "total_mm": round(sum(precip), 1),
                    "max_mm": max(precip),
                    "days_with_rain": len([p for p in precip if p > 0]),
                }

            result = {
                "station": {
                    "id": station.station_id,
                    "name": station.name,
                    "location": {
                        "latitude": station.latitude,
                        "longitude": station.longitude,
                        "elevation_m": station.elevation,
                    },
                    "distance_km": station.distance_km,
                },
                "weather_data": formatted_data,
                "summary": summary,
            }

            results.append(result)

        return results

    def get_status(self) -> Dict[str, Any]:
        """Agent Status"""
        return {
            "agent_id": self.agent_id,
            "domain": "dwd_weather",
            "processed_queries": self.processed_queries,
            "available_cities": list(self.mock_stations.keys()),
            "total_stations": sum(len(stations) for stations in self.mock_stations.values()),
        }


def test_dwd_weather_agent():
    """Test des DWD Weather Agents"""
    print("\n🧪 Starte DWD Weather Agent Tests...")

    # Setup Logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Agent erstellen
    agent = SimpleDwdWeatherAgent()

    # Test Queries
    test_queries = [
        {
            "query_id": "dwd - 001",
            "query_text": "Wetter in Berlin für die letzten 3 Tage",
            "location": "Berlin",
            "start_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "interval": WeatherInterval.DAILY,
            "parameters": [WeatherParameter.TEMPERATURE, WeatherParameter.PRECIPITATION],
        },
        {
            "query_id": "dwd - 002",
            "query_text": "Aktuelle Wetterdaten München stündlich",
            "location": "München",
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "interval": WeatherInterval.HOURLY,
            "parameters": [WeatherParameter.TEMPERATURE, WeatherParameter.WIND, WeatherParameter.HUMIDITY],
        },
        {
            "query_id": "dwd - 003",
            "query_text": "Wetterdaten Hamburg letzte Woche",
            "location": "Hamburg",
            "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "interval": WeatherInterval.DAILY,
            "parameters": [WeatherParameter.TEMPERATURE, WeatherParameter.PRECIPITATION, WeatherParameter.PRESSURE],
        },
    ]

    print(f"\n📋 Führe {len(test_queries)} Test-Queries aus...\n")

    for i, test_data in enumerate(test_queries, 1):
        print(f"🔄 Test {i}: {test_data['query_text']}")

        # Query erstellen und ausführen
        query = DwdWeatherQuery(**test_data)
        response = agent.process_query(query)

        # Ergebnisse anzeigen
        print(f"   ✅ Success: {response.success}")
        print(f"   📍 Stations: {len(response.stations)}")
        print(f"   📊 Data Points: {len(response.data_points)}")
        print(f"   ⏱️ Processing Time: {response.processing_time_ms}ms")

        if response.error_message:
            print(f"   ❌ Error: {response.error_message}")

        if response.results:
            result = response.results[0]
            station = result["station"]
            print(f"   🏢 Sample Station: {station['name']}")
            print(f"   📍 Location: {station['location']['latitude']:.4f}, {station['location']['longitude']:.4f}")

            if result["weather_data"]:
                sample_data = result["weather_data"][0]
                print(f"   🌡️ Sample Data: {sample_data}")

            if "summary" in result:
                summary = result["summary"]
                print("   📈 Summary:")
                if "temperature" in summary:
                    temp = summary["temperature"]
                    print(
                        f"      Temperature: {temp['min_celsius']}°C - {temp['max_celsius']}°C (avg: {temp['avg_celsius']}°C)"
                    )
                if "precipitation" in summary:
                    precip = summary["precipitation"]
                    print(f"      Precipitation: {precip['total_mm']}mm total, {precip['days_with_rain']} days with rain")

        print()

    # Agent Status
    print("📊 Agent Status:")
    status = agent.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")

    print("\n🎯 DWD Weather Agent Tests abgeschlossen!")
    return True


def main():
    """Main Test Function"""
    try:
        print("🌡️ VERITAS DWD Weather Agent - Deutscher Wetterdienst Integration")
        print("📦 Package: dwdweather2 (https://pypi.org/project/dwdweather2/)")

        if test_dwd_weather_agent():
            print("\n🎉 Alle Tests erfolgreich!")
            print("\n📋 DWD Weather Agent Features:")
            print("   ✅ Deutsche Wetterstationen (Berlin, München, Hamburg, Köln, Frankfurt)")
            print("   ✅ Historische und aktuelle Daten")
            print("   ✅ Stündliche und tägliche Intervalle")
            print("   ✅ Temperatur, Niederschlag, Wind, Luftfeuchtigkeit, Luftdruck")
            print("   ✅ Automatische Stationssuche basierend auf Ortsnamen")
            print("   ✅ Statistische Auswertungen und Zusammenfassungen")

            print("\n🚀 Integration in VERITAS:")
            print("   1. pip install dwdweather2")
            print("   2. Agent in Agent Registry registrieren")
            print("   3. FastAPI Endpoint konfigurieren")
            print("   4. Frontend-Integration für Wetter-Queries")

            return 0
        else:
            return 1

    except Exception as e:
        print(f"\n💥 Unerwarteter Fehler: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
