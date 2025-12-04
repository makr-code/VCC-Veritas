#!/usr/bin/env python3
"""
VERITAS DWD WEATHER AGENT V2
=============================

Spezialisierter Agent für deutsche Wetterdaten mit Wetterdienst Integration

Wetterdienst ist der moderne Nachfolger von dwdweather2 und unterstützt:
- Deutscher Wetterdienst (DWD) Daten-Integration
- Historische und aktuelle Wetterdaten
- Vorhersagen (MOSMIX)
- Ort-basierte Stationssuche
- Verschiedene Zeitauflösungen
- Moderne Python API (requests>=2.31.0 kompatibel!)

VERWENDUNG:
- Eingabe: Ort, Zeitraum, Parameter
- Ausgabe: Meteorologische Daten (Temperatur, Niederschlag, Wind, etc.)

Author: VERITAS System
Date: 2025-10-19
Version: 2.0 (Wetterdienst Integration)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Wetterdienst Integration (moderner Nachfolger von dwdweather2)
try:
    from wetterdienst import Settings
    from wetterdienst.provider.dwd.observation import DwdObservationRequest

    WETTERDIENST_AVAILABLE = True
except ImportError as e:
    WETTERDIENST_AVAILABLE = False
    logging.warning(f"⚠️ Wetterdienst nicht installiert: {e}")
    logging.info("💡 Installiere mit: pip install wetterdienst")

logger = logging.getLogger(__name__)


@dataclass
class DwdWeatherQuery:
    """Query-Request für DWD Weather Agent V2"""

    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    parameters: List[str] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = ["temperature_air"]
        if self.end_date is None:
            self.end_date = datetime.now()
        if self.start_date is None:
            self.start_date = self.end_date - timedelta(days=7)


class DwdWeatherAgentV2:
    """
    🌡️ DWD Weather Agent V2 - Deutscher Wetterdienst Integration

    Verwendet Wetterdienst (Nachfolger von dwdweather2):
    - Moderne API (requests>=2.31.0 kompatibel)
    - Umfangreiche DWD-Datenquellen
    - Historische Daten, Vorhersagen, Warnungen
    - Optimierte Performance

    Example:
        >>> agent = DwdWeatherAgentV2()
        >>> result = agent.get_weather(
        ...     latitude=51.0,
        ...     longitude=7.0,
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 7)
        ... )
    """

    def __init__(self):
        """Initialize DWD Weather Agent V2"""
        self.logger = logging.getLogger(__name__)
        self.available = WETTERDIENST_AVAILABLE

        if not self.available:
            self.logger.warning("❌ Wetterdienst nicht verfügbar!")
            self.logger.info("   Installiere mit: pip install wetterdienst")
            return

        # Wetterdienst Settings (nur unterstützte Parameter)
        self.settings = Settings(
            ts_shape="long", ts_humanize=True  # Long format für einfachere Verarbeitung  # Menschenlesbare Spaltennamen
        )

        self.logger.info("✅ DWD Weather Agent V2 initialisiert (Wetterdienst)")

    def get_nearest_station(
        self, latitude: float, longitude: float, parameter: str = "temperature_air_mean_200", resolution: str = "hourly"
    ) -> Optional[Dict[str, Any]]:
        """
        Finde nächste DWD-Wetterstation

        Args:
            latitude: Breitengrad
            longitude: Längengrad
            parameter: Wetter-Parameter (String, z.B. temperature_air_mean_200)
            resolution: Zeitauflösung (hourly, daily, etc.)

        Returns:
            Station-Informationen oder None
        """
        if not self.available:
            return None

        try:
            # Erstelle Request (parameter als String)
            request = DwdObservationRequest(
                parameters=[parameter], resolution=resolution, settings=self.settings  # Liste von Strings  # String
            )

            # Finde nächste Station
            stations = request.filter_by_distance(
                latitude=latitude, longitude=longitude, distance=50.0, unit="km"  # 50 km Radius
            )

            stations_df = stations.df

            if stations_df.empty:
                self.logger.warning(f"⚠️ Keine Station gefunden bei ({latitude}, {longitude})")
                return None

            # Erste Station (nächste)
            station = stations_df.iloc[0]

            return {
                "station_id": str(station["station_id"]),
                "name": str(station["name"]),
                "latitude": float(station["latitude"]),
                "longitude": float(station["longitude"]),
                "height": float(station["height"]),
                "distance_km": float(station.get("distance", 0)),
            }

        except Exception as e:
            self.logger.error(f"❌ Fehler bei Stationssuche: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            return None

    def get_weather_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
        parameters: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Hole Wetterdaten für Position und Zeitraum

        Args:
            latitude: Breitengrad
            longitude: Längengrad
            start_date: Start-Datum
            end_date: End-Datum
            parameters: Liste der gewünschten Parameter

        Returns:
            Wetterdaten-Dictionary
        """
        if not self.available:
            return {"success": False, "error": "Wetterdienst nicht verfügbar", "data": []}

        if parameters is None:
            parameters = ["temperature_air"]

        try:
            # Finde nächste Station
            station = self.get_nearest_station(latitude, longitude)

            if not station:
                return {"success": False, "error": "Keine Station gefunden", "data": []}

            self.logger.info(f"📍 Verwende Station: {station['name']} (ID: {station['station_id']})")

            # Erstelle Request für Temperaturdaten (parameter als String)
            request = DwdObservationRequest(
                parameters=["temperature_air_mean_200"],  # Liste von Strings
                resolution="hourly",  # String
                start_date=start_date,
                end_date=end_date,
                settings=self.settings,
            )

            # Filtere nach Station
            stations = request.filter_by_station_id(station_id=[station["station_id"]])

            # Hole Werte
            values = stations.values.all()
            values_df = values.df

            if values_df.empty:
                return {"success": False, "error": "Keine Daten verfügbar", "station": station, "data": []}

            # Konvertiere zu Liste
            data_list = []
            for _, row in values_df.iterrows():
                data_list.append(
                    {
                        "timestamp": row["date"].isoformat() if hasattr(row["date"], "isoformat") else str(row["date"]),
                        "parameter": row["parameter"],
                        "value": float(row["value"]) if row["value"] is not None else None,
                        "quality": row.get("quality", None),
                    }
                )

            return {
                "success": True,
                "station": station,
                "data": data_list,
                "count": len(data_list),
                "timerange": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            }

        except Exception as e:
            self.logger.error(f"❌ Fehler bei Datenabruf: {e}")
            import traceback

            self.logger.error(traceback.format_exc())

            return {"success": False, "error": str(e), "data": []}

    def query(self, query_text: str) -> Dict[str, Any]:
        """
        Verarbeite Natural Language Query

        Args:
            query_text: Query-Text (z.B. "Temperatur in München letzte Woche")

        Returns:
            Wetterdaten-Dictionary
        """
        # Einfacher Parser (kann später erweitert werden)
        # Beispiel: "Temperatur in München" → lat=48.1, lon=11.5

        # Standard: München
        latitude = 48.1351
        longitude = 11.5820

        # Zeitraum: letzte 7 Tage
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        return self.get_weather_data(latitude=latitude, longitude=longitude, start_date=start_date, end_date=end_date)


# ==========================================
# STANDALONE TEST
# ==========================================


def test_dwd_weather_agent():
    """Test DWD Weather Agent V2"""
    print("=" * 80)
    print("🌡️ DWD WEATHER AGENT V2 - TEST")
    print("=" * 80)
    print()

    if not WETTERDIENST_AVAILABLE:
        print("❌ Wetterdienst nicht installiert!")
        print("💡 Installiere mit: pip install wetterdienst")
        return

    # Erstelle Agent
    agent = DwdWeatherAgentV2()

    # Test 1: Finde nächste Station (München)
    print("📍 Test 1: Finde nächste Station (München)")
    station = agent.get_nearest_station(latitude=48.1351, longitude=11.5820)

    if station:
        print(f"   ✅ Station gefunden:")
        print(f"      Name: {station['name']}")
        print(f"      ID: {station['station_id']}")
        print(f"      Position: ({station['latitude']}, {station['longitude']})")
        print(f"      Höhe: {station['height']} m")
        print(f"      Entfernung: {station.get('distance_km', 0):.2f} km")
    else:
        print("   ❌ Keine Station gefunden")

    print()

    # Test 2: Hole Wetterdaten (letzte 3 Tage)
    print("📊 Test 2: Hole Wetterdaten (München, letzte 3 Tage)")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)

    result = agent.get_weather_data(latitude=48.1351, longitude=11.5820, start_date=start_date, end_date=end_date)

    if result["success"]:
        print(f"   ✅ {result['count']} Datenpunkte gefunden")
        print(f"   📍 Station: {result['station']['name']}")
        print(f"   📅 Zeitraum: {result['timerange']['start']} bis {result['timerange']['end']}")

        # Zeige erste 5 Werte
        if result["data"]:
            print(f"\n   📈 Erste 5 Messwerte:")
            for i, measurement in enumerate(result["data"][:5], 1):
                print(f"      {i}. {measurement['timestamp']}: {measurement['value']}°C")
    else:
        print(f"   ❌ Fehler: {result['error']}")

    print()
    print("=" * 80)


if __name__ == "__main__":
    # Konfiguriere Logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

    test_dwd_weather_agent()
