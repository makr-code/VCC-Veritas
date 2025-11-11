"""
VERITAS API Agent: DWD Open Data Weather Agent
Verarbeitet historische Wetterdaten direkt von DWD Open Data mit dwdparse.

Keine Vendor Lock-in, keine externen API-Calls - nur direktes Parsing von DWD Dateien.
"""

import logging
import tempfile
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from dwdparse import get_parser, load_stations
from dwdparse.parsers import (
    CurrentObservationsParser,
    PrecipitationObservationsParser,
    PressureObservationsParser,
    TemperatureObservationsParser,
    WindObservationsParser,
)

logger = logging.getLogger(__name__)


class DWDOpenDataAgent:
    """
    DWD Open Data Weather Agent

    Verarbeitet Wetterdaten direkt von opendata.dwd.de mit dwdparse.
    Unterstützt historische Beobachtungen und aktuelle Messwerte.
    """

    # DWD Open Data FTP/HTTP Basis-URLs
    DWD_BASE_URL = "https://opendata.dwd.de/climate_environment/CDC"
    DWD_OBSERVATIONS_URL = f"{DWD_BASE_URL}/observations_germany/climate"

    # Verfügbare Zeitauflösungen
    RESOLUTIONS = {"hourly": "hourly", "daily": "daily", "monthly": "monthly", "annual": "annual"}

    # Verfügbare Parameter
    PARAMETERS = {
        "temperature": {
            "hourly": "air_temperature",
            "daily": "kl",  # Klima-Daten (enthält Temperatur)
            "parser": TemperatureObservationsParser,
        },
        "precipitation": {"hourly": "precipitation", "daily": "more_precip", "parser": PrecipitationObservationsParser},
        "wind": {"hourly": "wind", "daily": "kl", "parser": WindObservationsParser},
        "pressure": {"hourly": "pressure", "daily": "kl", "parser": PressureObservationsParser},
    }

    def __init__(self):
        """Initialisiere DWD Open Data Agent"""
        self.name = "DWD Open Data Weather Agent"
        self.capabilities = [
            "Historische Wetterdaten von DWD",
            "Temperatur, Niederschlag, Wind, Luftdruck",
            "Stündliche, tägliche, monatliche Auflösung",
            "Direktes Parsing von opendata.dwd.de",
            "Kein Vendor Lock-in",
        ]
        self.stations_cache: Optional[Dict] = None
        self.cache_dir = Path(tempfile.gettempdir()) / "veritas_dwd_cache"
        self.cache_dir.mkdir(exist_ok=True)

        logger.info(f"✅ {self.name} initialisiert")
        logger.info(f"   Cache-Verzeichnis: {self.cache_dir}")

    def get_stations(self, reload: bool = False) -> Dict[str, Any]:
        """
        Lade DWD Stationsliste

        HINWEIS: dwdparse bietet keine vollständige Stationsliste-API.
        Stattdessen verwenden wir bekannte Stationen oder DWD Station-IDs direkt.

        Args:
            reload: Stationen neu laden (ignoriere Cache)

        Returns:
            Dictionary mit bekannten Stationen (station_id -> station_data)
        """
        if self.stations_cache and not reload:
            return self.stations_cache

        # Bekannte DWD Stationen (Beispiele)
        # Vollständige Liste: https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/
        self.stations_cache = {
            "01766": {
                "station_id": "01766",
                "name": "Münster/Osnabrück (Flughafen)",
                "latitude": 52.1344,
                "longitude": 7.6969,
                "elevation": 48.0,
            },
            "00433": {
                "station_id": "00433",
                "name": "Berlin-Tempelhof",
                "latitude": 52.4675,
                "longitude": 13.4021,
                "elevation": 48.0,
            },
            "02928": {
                "station_id": "02928",
                "name": "Düsseldorf (Flughafen)",
                "latitude": 51.3007,
                "longitude": 6.7680,
                "elevation": 37.0,
            },
            "01975": {
                "station_id": "01975",
                "name": "München (Flughafen)",
                "latitude": 48.3479,
                "longitude": 11.8134,
                "elevation": 453.0,
            },
            "02014": {
                "station_id": "02014",
                "name": "Nürnberg",
                "latitude": 49.5025,
                "longitude": 11.0550,
                "elevation": 314.0,
            },
            "10379": {
                "station_id": "10379",
                "name": "Trier-Petrisberg",
                "latitude": 49.7476,
                "longitude": 6.6583,
                "elevation": 265.0,
            },
        }

        logger.info(f"✅ {len(self.stations_cache)} bekannte DWD Stationen geladen")
        return self.stations_cache

    def find_nearest_station(self, lat: float, lon: float, parameter: str = "temperature") -> Optional[Dict[str, Any]]:
        """
        Finde nächstgelegene DWD Station

        Args:
            lat: Breitengrad
            lon: Längengrad
            parameter: Gewünschter Parameter (temperature, precipitation, etc.)

        Returns:
            Station Dictionary oder None
        """
        stations = self.get_stations()
        if not stations:
            return None

        # Einfache Distanzberechnung (für Deutschland ausreichend)
        def distance(s: Dict) -> float:
            dlat = s.get("latitude", 0) - lat
            dlon = s.get("longitude", 0) - lon
            return dlat * dlat + dlon * dlon

        # Finde nächste Station
        nearest = min(stations.values(), key=distance)

        logger.info(f"Nächste Station: {nearest.get('name')} " f"(ID: {nearest.get('station_id')})")

        return nearest

    def build_dwd_url(self, station_id: str, parameter: str, resolution: str = "hourly", period: str = "recent") -> str:
        """
        Erstelle DWD Open Data URL

        Args:
            station_id: DWD Stations-ID (5-stellig)
            parameter: Parameter (temperature, precipitation, etc.)
            resolution: Zeitauflösung (hourly, daily, monthly)
            period: Zeitraum (recent, historical, now)

        Returns:
            Vollständige DWD URL
        """
        param_info = self.PARAMETERS.get(parameter, {})
        param_name = param_info.get(resolution, parameter)

        # Beispiel URL-Struktur:
        # https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/air_temperature/recent/
        url = f"{self.DWD_OBSERVATIONS_URL}/" f"{resolution}/" f"{param_name}/" f"{period}/"

        return url

    def download_and_parse(self, url: str, filename: str) -> List[Dict[str, Any]]:
        """
        Downloade und parse DWD Datei

        Args:
            url: Vollständige URL zur DWD Datei
            filename: Dateiname (z.B. stundenwerte_TU_01766_akt.zip)

        Returns:
            Liste von Wetter-Records
        """
        full_url = url + filename
        cache_file = self.cache_dir / filename

        try:
            # Download nur wenn nicht gecacht
            if not cache_file.exists():
                logger.info(f"Downloade: {full_url}")
                urllib.request.urlretrieve(full_url, cache_file)
                logger.info(f"✅ Heruntergeladen: {filename}")
            else:
                logger.info(f"Verwende Cache: {filename}")

            # Parse mit dwdparse
            # get_parser() erwartet nur den Dateinamen, nicht den vollständigen Pfad
            parser_class = get_parser(filename)
            if not parser_class:
                logger.error(f"❌ Kein Parser für Datei: {filename}")
                return []

            parser = parser_class()

            records = list(parser.parse(str(cache_file)))
            logger.info(f"✅ {len(records)} Records geparst")

            return records

        except Exception as e:
            logger.error(f"❌ Fehler beim Download/Parsing: {e}")
            return []

    def get_weather_data(
        self,
        station_id: str,
        parameter: str = "temperature",
        resolution: str = "hourly",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Hole Wetterdaten für Station

        Args:
            station_id: DWD Stations-ID (5-stellig)
            parameter: Parameter (temperature, precipitation, wind, pressure)
            resolution: Zeitauflösung (hourly, daily)
            start_date: Start-Datum (optional)
            end_date: End-Datum (optional)

        Returns:
            Liste von Wetter-Records
        """
        # Bestimme Zeitraum (recent = letzte ~1-2 Jahre)
        period = "recent"

        # Baue URL
        base_url = self.build_dwd_url(station_id=station_id, parameter=parameter, resolution=resolution, period=period)

        # DWD Dateinamen folgen Muster:
        # stundenwerte_<PARAM>_<STATION_ID>_akt.zip (für recent)
        # z.B. stundenwerte_TU_01766_akt.zip

        param_code = {"temperature": "TU", "precipitation": "RR", "wind": "FF", "pressure": "P0"}.get(parameter, "TU")

        filename = f"stundenwerte_{param_code}_{station_id}_akt.zip"

        # Download und Parse
        records = self.download_and_parse(base_url, filename)

        # Filtere nach Datum wenn gegeben
        if start_date or end_date:
            filtered = []
            for record in records:
                timestamp = record.get("timestamp")
                if not timestamp:
                    continue

                # Konvertiere zu datetime wenn String
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)

                # Entferne Timezone-Info für Vergleich (DWD Daten sind UTC)
                if hasattr(timestamp, "tzinfo") and timestamp.tzinfo is not None:
                    timestamp = timestamp.replace(tzinfo=None)

                # Stelle sicher dass start_date/end_date auch keine Timezone haben
                if start_date:
                    comp_start = start_date.replace(tzinfo=None) if hasattr(start_date, "tzinfo") else start_date
                    if timestamp < comp_start:
                        continue

                if end_date:
                    comp_end = end_date.replace(tzinfo=None) if hasattr(end_date, "tzinfo") else end_date
                    if timestamp > comp_end:
                        continue

                filtered.append(record)

            return filtered

        return records

    def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verarbeite Wetter-Anfrage

        Args:
            query: Nutzeranfrage (z.B. "Wetter Berlin letzte Woche")
            context: Query-Kontext (kann lat/lon enthalten)

        Returns:
            Antwort Dictionary mit Wetterdaten
        """
        try:
            # Extrahiere Ort wenn vorhanden
            lat = context.get("latitude")
            lon = context.get("longitude")

            if not lat or not lon:
                # Default: Berlin
                lat, lon = 52.5200, 13.4050
                logger.info("Kein Ort gegeben, verwende Berlin als Default")

            # Finde nächste Station
            station = self.find_nearest_station(lat, lon)
            if not station:
                return {"error": "Keine DWD Station gefunden", "success": False}

            station_id = str(station["station_id"]).zfill(5)

            # Hole letzte 7 Tage Temperaturdaten
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            records = self.get_weather_data(
                station_id=station_id, parameter="temperature", resolution="hourly", start_date=start_date, end_date=end_date
            )

            if not records:
                return {"error": "Keine Daten verfügbar", "success": False}

            # Berechne Statistiken
            temperatures = [r.get("temperature") for r in records if r.get("temperature") is not None]

            if temperatures:
                avg_temp = sum(temperatures) / len(temperatures)
                min_temp = min(temperatures)
                max_temp = max(temperatures)
            else:
                avg_temp = min_temp = max_temp = None

            return {
                "success": True,
                "station": {
                    "id": station_id,
                    "name": station.get("name"),
                    "latitude": station.get("latitude"),
                    "longitude": station.get("longitude"),
                },
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "data": {
                    "record_count": len(records),
                    "temperature": {
                        "average_kelvin": avg_temp,
                        "average_celsius": avg_temp - 273.15 if avg_temp else None,
                        "min_kelvin": min_temp,
                        "max_kelvin": max_temp,
                    },
                },
                "source": "DWD Open Data (opendata.dwd.de)",
                "parser": "dwdparse",
            }

        except Exception as e:
            logger.error(f"❌ Fehler bei Wetterabfrage: {e}", exc_info=True)
            return {"error": str(e), "success": False}


# Agent-Registrierung für VERITAS Pipeline
def get_agent_info() -> Dict[str, Any]:
    """Agent-Informationen für Registry"""
    return {
        "name": "DWD Open Data Weather Agent",
        "version": "1.0.0",
        "description": "Historische Wetterdaten von DWD Open Data (dwdparse)",
        "capabilities": [
            "Historische Wetterdaten",
            "DWD Stationsnetzwerk",
            "Temperatur, Niederschlag, Wind, Luftdruck",
            "Stündliche und tägliche Auflösung",
            "Direktes Parsing ohne Vendor Lock-in",
        ],
        "keywords": [
            "weather",
            "wetter",
            "dwd",
            "temperature",
            "temperatur",
            "precipitation",
            "niederschlag",
            "climate",
            "klima",
            "forecast",
            "vorhersage",
            "historical",
            "historisch",
        ],
        "agent_class": DWDOpenDataAgent,
    }


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    agent = DWDOpenDataAgent()

    # Test 1: Lade Stationen
    print("\n=== Test 1: Stationen laden ===")
    stations = agent.get_stations()
    print(f"Gefunden: {len(stations)} Stationen")
    if stations:
        example = next(iter(stations.values()))
        print(f"Beispiel: {example.get('name')} (ID: {example.get('station_id')})")

    # Test 2: Finde Station für Berlin
    print("\n=== Test 2: Nächste Station für Berlin ===")
    berlin_station = agent.find_nearest_station(52.5200, 13.4050)
    if berlin_station:
        print(f"Station: {berlin_station.get('name')}")
        print(f"ID: {berlin_station.get('station_id')}")
        print(f"Position: {berlin_station.get('latitude')}, {berlin_station.get('longitude')}")

    # Test 3: Hole Wetterdaten
    print("\n=== Test 3: Wetterdaten abrufen ===")
    if berlin_station:
        station_id = str(berlin_station["station_id"]).zfill(5)
        print(f"Rufe Daten für Station {station_id} ab...")

        # Nur testen wenn URL erreichbar
        try:
            result = agent.process_query("Wetter Berlin letzte Woche", {"latitude": 52.5200, "longitude": 13.4050})

            if result.get("success"):
                print("✅ Erfolgreich!")
                print(f"Records: {result['data']['record_count']}")
                temp = result["data"]["temperature"]
                if temp.get("average_celsius"):
                    print(f"Durchschnittstemperatur: {temp['average_celsius']:.1f}°C")
            else:
                print(f"⚠️ Fehler: {result.get('error')}")

        except Exception as e:
            print(f"⚠️ Test übersprungen (kein Internet?): {e}")
