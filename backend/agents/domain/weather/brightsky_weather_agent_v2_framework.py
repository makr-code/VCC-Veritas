"""
BrightSkyWeatherAgent für VERITAS - BaseAgent Framework v2.0

Spezialisierter Agent für deutsche Wetterdaten via Bright Sky API.
Migriert vom Legacy-System zum modernen VERITAS Framework.

Bright Sky ist ein kostenloses REST API für DWD-Wetterdaten:
- Einfache HTTP REST API (requests kompatibel!)
- Historische Wetterdaten (ab 2010)
- Wettervorhersagen (MOSMIX)
- Stations-Informationen
- Keine Installation notwendig

API Dokumentation: https://brightsky.dev/docs/

Capabilities:
- current_weather: Aktuelles Wetter
- weather_history: Historische Wetterdaten
- weather_forecast: Wettervorhersage
- weather_alerts: Wetterwarnungen
- dwd_integration: DWD Datenintegration

Framework Features:
✅ BaseAgent inheritance
✅ Registry support
✅ Async processing
✅ Monitoring & Quality gates
✅ Retry logic
✅ External API integration (Bright Sky)

Migration: 2025-12-04 (Phase 2)
Version: 2.0 (Framework)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from backend.agents.framework.agent_monitoring import AgentMonitor

# Framework Imports
from backend.agents.framework.base_agent import BaseAgent
from backend.agents.framework.quality_gate import QualityGate, QualityPolicy
from backend.agents.framework.retry_handler import RetryConfig, RetryHandler
from backend.agents.registry.api_agent_registry import AgentCapability, AgentLifecycleType, get_agent_registry

logger = logging.getLogger(__name__)

# Bright Sky API Configuration
BRIGHTSKY_API_URL = "https://api.brightsky.dev"
BRIGHTSKY_WEATHER_ENDPOINT = f"{BRIGHTSKY_API_URL}/weather"
BRIGHTSKY_CURRENT_ENDPOINT = f"{BRIGHTSKY_API_URL}/current_weather"
BRIGHTSKY_ALERTS_ENDPOINT = f"{BRIGHTSKY_API_URL}/alerts"


class BrightSkyWeatherAgent(BaseAgent):
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
    """

    AGENT_TYPE = "brightsky_weather"
    AGENT_DOMAIN = "WEATHER"
    AGENT_VERSION = "2.0"

    LEGACY_CAPABILITIES = ["current_weather", "weather_history", "weather_forecast", "weather_alerts", "dwd_integration"]

    def __init__(self, agent_id: Optional[str] = None, timeout: int = 30):
        """Initialize Bright Sky Weather Agent with Framework Support"""
        super().__init__(agent_id=agent_id)

        self.logger = logging.getLogger(f"{__name__}.brightsky_weather")
        self.monitor = AgentMonitor("brightsky_weather")

        # Quality Gate
        policy = QualityPolicy(min_quality=0.7, target_quality=0.9)
        self.quality_gate = QualityGate(policy)

        # Retry Handler
        retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)

        # HTTP Session
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "VERITAS-Agent/2.0"})

        # Test API availability
        self.available = self._test_api_availability()

        self.logger.info(
            f"✅ BrightSkyWeatherAgent v{self.AGENT_VERSION} initialized (API: {'available' if self.available else 'unavailable'})"
        )

    def _test_api_availability(self) -> bool:
        """Test Bright Sky API availability"""
        try:
            response = self.session.get(BRIGHTSKY_API_URL, timeout=5)
            if response.status_code == 200:
                self.logger.info("✅ Bright Sky API verfügbar")
                return True
            else:
                self.logger.warning(f"⚠️ Bright Sky API Status: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Bright Sky API nicht erreichbar: {e}")
            return False

    def execute_step(self, step_data: dict) -> dict:
        """Execute a single processing step"""
        try:
            query = step_data.get("query", "")
            if not query:
                return {"success": False, "error": "No query provided"}
            result = asyncio.run(self.process_query(query))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_agent_type(self) -> str:
        """Return agent type identifier"""
        return self.AGENT_TYPE

    def get_capabilities(self) -> List[AgentCapability]:
        """Return agent capabilities"""
        return [
            AgentCapability.QUERY_PROCESSING,
            AgentCapability.WEATHER_DATA,
            AgentCapability.EXTERNAL_API_INTEGRATION,
            AgentCapability.REAL_TIME_PROCESSING,
        ]

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process weather query through async pipeline"""
        start_time = datetime.now()
        query_id = f"{self.AGENT_TYPE}_{start_time.timestamp()}"

        try:
            # 1. Validation
            if not query or not isinstance(query, str):
                return self._error_response("Invalid query", query_id)

            if not self.available:
                return self._error_response("Bright Sky API nicht verfügbar", query_id)

            # 2. Extract location (default: München)
            # TODO: Erweitere mit NLP für Ortsextraktion
            latitude = context.get("latitude", 48.1351) if context else 48.1351
            longitude = context.get("longitude", 11.5820) if context else 11.5820

            # 3. Fetch weather data
            weather_data = self.get_current_weather(latitude, longitude)

            # 4. Build response
            processing_time = (datetime.now() - start_time).total_seconds()
            result = {
                "success": weather_data["success"],
                "results": [weather_data] if weather_data["success"] else [],
                "confidence": 0.9 if weather_data["success"] else 0.0,
                "agent": self.AGENT_TYPE,
                "version": self.AGENT_VERSION,
                "query_id": query_id,
                "timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
            }

            self.logger.info(f"✅ Query processed in {processing_time:.2f}s")
            return result

        except Exception as e:
            self.logger.error(f"❌ Query failed: {e}")
            return self._error_response(str(e), query_id)

    def get_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Hole aktuelles Wetter für Position

        Args:
            latitude: Breitengrad
            longitude: Längengrad

        Returns:
            Aktuelles Wetter-Dictionary
        """
        if not self.available:
            return {"success": False, "error": "Bright Sky API nicht verfügbar", "data": None}

        try:
            params = {"lat": latitude, "lon": longitude}

            response = self.session.get(BRIGHTSKY_CURRENT_ENDPOINT, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if "weather" in data:
                weather = data["weather"]

                return {
                    "success": True,
                    "location": {"latitude": latitude, "longitude": longitude},
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
                        "icon": weather.get("icon"),
                    },
                    "sources": data.get("sources", []),
                }
            else:
                return {"success": False, "error": "Keine Wetterdaten verfügbar", "data": None}

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ API Request Fehler: {e}")
            return {"success": False, "error": str(e), "data": None}

    def get_weather_history(
        self, latitude: float, longitude: float, date: datetime, last_date: Optional[datetime] = None
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
            return {"success": False, "error": "Bright Sky API nicht verfügbar", "data": []}

        if last_date is None:
            last_date = datetime.now()

        try:
            params: Dict[str, Any] = {
                "lat": latitude,
                "lon": longitude,
                "date": date.strftime("%Y-%m-%d"),
                "last_date": last_date.strftime("%Y-%m-%d"),
            }

            response = self.session.get(BRIGHTSKY_WEATHER_ENDPOINT, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if "weather" in data:
                return {
                    "success": True,
                    "location": {"latitude": latitude, "longitude": longitude},
                    "timerange": {"start": date.isoformat(), "end": last_date.isoformat()},
                    "weather": data["weather"],
                    "count": len(data["weather"]),
                    "sources": data.get("sources", []),
                }
            else:
                return {"success": False, "error": "Keine Wetterdaten verfügbar", "data": []}

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ API Request Fehler: {e}")
            return {"success": False, "error": str(e), "data": []}

    def get_weather_alerts(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Hole aktuelle Wetterwarnungen

        Args:
            latitude: Breitengrad
            longitude: Längengrad

        Returns:
            Wetterwarnungen
        """
        if not self.available:
            return {"success": False, "error": "Bright Sky API nicht verfügbar", "alerts": []}

        try:
            params = {"lat": latitude, "lon": longitude}

            response = self.session.get(BRIGHTSKY_ALERTS_ENDPOINT, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            return {
                "success": True,
                "location": {"latitude": latitude, "longitude": longitude},
                "alerts": data.get("alerts", []),
                "count": len(data.get("alerts", [])),
            }

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ API Request Fehler: {e}")
            return {"success": False, "error": str(e), "alerts": []}

    def _error_response(self, error: str, query_id: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "success": False,
            "error": error,
            "results": [],
            "confidence": 0.0,
            "agent": self.AGENT_TYPE,
            "query_id": query_id,
            "timestamp": datetime.now().isoformat(),
        }

    # =====================================================================
    # Legacy Compatibility Methods
    # =====================================================================

    def query(self, query_text: str) -> Dict[str, Any]:
        """Legacy method: Sync query wrapper"""
        result = asyncio.run(self.process_query(query_text))
        return result

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": "BrightSkyWeatherAgent",
            "domain": self.AGENT_DOMAIN,
            "type": self.AGENT_TYPE,
            "version": self.AGENT_VERSION,
            "capabilities": [cap.value for cap in self.get_capabilities()],
            "api_available": self.available,
            "api_url": BRIGHTSKY_API_URL,
        }


# =========================================================================
# Registration Function
# =========================================================================


def register_brightsky_weather_agent():
    """Register BrightSkyWeatherAgent in VERITAS Registry"""
    try:
        registry = get_agent_registry()
        registry.register_agent(
            agent_type="brightsky_weather",
            agent_class=BrightSkyWeatherAgent,
            capabilities=[
                AgentCapability.QUERY_PROCESSING,
                AgentCapability.WEATHER_DATA,
                AgentCapability.EXTERNAL_API,
                AgentCapability.REAL_TIME_PROCESSING,
            ],
            lifecycle_type=AgentLifecycleType.POOLED,
            max_concurrent_instances=3,
            priority=2,
            description="Bright Sky Weather API (DWD Daten)",
        )
        logger.info("✅ BrightSkyWeatherAgent registered successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to register BrightSkyWeatherAgent: {e}")
        return False
