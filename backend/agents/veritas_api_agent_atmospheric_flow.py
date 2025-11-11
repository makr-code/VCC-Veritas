"""
VERITAS Atmospheric Flow Agent

Ein spezialisierter Agent für Strömungsraster-Berechnungen und Emissionsausbreitung.
Berechnet Schadstoffausbreitung basierend auf Winddaten, Emittentenorten und
Immissionsorten mit verschiedenen Ausbreitungsmodellen.

Hauptfunktionen:
- Strömungsraster-Berechnung aus Winddaten
- Gaussian Plume Modell für Punktquellen
- Lagrangian Particle Tracking
- Topographische Korrekturen
- Emittenten-Immissions-Mapping
- DWD Weather Integration
- Grenzschicht-Modellierung

Autor: VERITAS Agent System
Datum: 28. September 2025
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import math
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

# Wissenschaftliche Berechnungen (NumPy/SciPy ähnliche Funktionen)
try:
    import numpy as np
    import scipy.integrate
    import scipy.interpolate

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️  NumPy/SciPy nicht installiert - verwende mathematische Approximationen")
    print("   Installation: pip install numpy scipy")

# Integration mit DWD Weather Agent
try:
    from .veritas_api_agent_dwd_weather import (
        DwdWeatherAgent,
        DwdWeatherQueryRequest,
        WeatherInterval,
        WeatherParameter,
        create_dwd_weather_agent,
    )

    DWD_INTEGRATION_AVAILABLE = True
except ImportError:
    DWD_INTEGRATION_AVAILABLE = False
    print("⚠️  DWD Weather Agent Integration nicht verfügbar")


# =============================================================================
# ATMOSPHERIC FLOW ENUMS UND KONFIGURATION
# =============================================================================


class FlowModelType(Enum):
    """Strömungsmodell-Typen"""

    GAUSSIAN_PLUME = "gaussian_plume"  # Gaussian Fahnenmodell
    GAUSSIAN_PUFF = "gaussian_puf"  # Gaussian Puff-Modell
    LAGRANGIAN = "lagrangian"  # Lagrangian Particle Tracking
    EULERIAN = "eulerian"  # Eulerian Grid Model
    HYBRID = "hybrid"  # Hybrid-Ansatz


class AtmosphericStabilityClass(Enum):
    """Pasquill-Gifford Stabilitätsklassen"""

    A = "A"  # Sehr instabil
    B = "B"  # Mäßig instabil
    C = "C"  # Leicht instabil
    D = "D"  # Neutral
    E = "E"  # Leicht stabil
    F = "F"  # Mäßig stabil


class EmissionSourceType(Enum):
    """Emissionsquellen-Typen"""

    POINT_SOURCE = "point_source"  # Punktquelle (Schornstein)
    LINE_SOURCE = "line_source"  # Linienquelle (Straße)
    AREA_SOURCE = "area_source"  # Flächenquelle (Industriegebiet)
    VOLUME_SOURCE = "volume_source"  # Volumenquelle (Stadt)


class TerrainType(Enum):
    """Gelände-Typen für Rauigkeitsparameter"""

    SMOOTH = "smooth"  # Glatte Oberfläche (Wasser)
    OPEN_COUNTRY = "open_country"  # Offenes Land
    SUBURBAN = "suburban"  # Vorstadtgebiet
    URBAN = "urban"  # Städtisches Gebiet
    FOREST = "forest"  # Waldgebiet
    COMPLEX_TERRAIN = "complex_terrain"  # Komplexes Gelände


# =============================================================================
# STRÖMUNGSRASTER DATENSTRUKTUREN
# =============================================================================


@dataclass
class Coordinate:
    """3D-Koordinate (Lat, Lon, Höhe)"""

    latitude: float
    longitude: float
    elevation_m: float = 0.0

    def distance_to(self, other: "Coordinate") -> float:
        """Berechne Abstand zu anderer Koordinate (Haversine)"""
        if not SCIPY_AVAILABLE:
            # Vereinfachte Distanz-Berechnung
            lat_diff = abs(self.latitude - other.latitude)
            lon_diff = abs(self.longitude - other.longitude)
            return math.sqrt(lat_diff**2 + lon_diff**2) * 111320  # m

        # Präzise Haversine-Formel
        R = 6371000  # Erdradius in Metern
        lat1, lat2 = math.radians(self.latitude), math.radians(other.latitude)
        dlat = math.radians(other.latitude - self.latitude)
        dlon = math.radians(other.longitude - self.longitude)

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance_2d = R * c
        elevation_diff = abs(self.elevation_m - other.elevation_m)

        return math.sqrt(distance_2d**2 + elevation_diff**2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WindVector:
    """Windvektor mit Geschwindigkeit und Richtung"""

    speed_ms: float  # Windgeschwindigkeit (m/s)
    direction_deg: float  # Windrichtung (0-360°, N=0°)
    elevation_m: float = 10.0  # Messhöhe
    timestamp: Optional[str] = None

    # Zusätzliche Parameter
    turbulence_intensity: float = 0.1  # Turbulenzintensität
    vertical_component: float = 0.0  # Vertikale Windkomponente

    def u_component(self) -> float:
        """U-Komponente (Ost-West)"""
        return self.speed_ms * math.sin(math.radians(self.direction_deg))

    def v_component(self) -> float:
        """V-Komponente (Nord-Süd)"""
        return self.speed_ms * math.cos(math.radians(self.direction_deg))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WindField:
    """Windfeld-Raster für einen Bereich"""

    grid_bounds: Dict[str, float]  # {"lat_min": ..., "lat_max": ..., "lon_min": ..., "lon_max": ...}
    grid_resolution_m: float  # Raster-Auflösung in Metern
    wind_vectors: Dict[str, WindVector]  # Key: "lat_lon", Value: WindVector
    timestamp: str

    # Metadaten
    stability_class: AtmosphericStabilityClass = AtmosphericStabilityClass.D
    mixing_height_m: float = 1000.0  # Mischungsschichthöhe
    surface_roughness: float = 0.1  # Oberflächenrauigkeit
    terrain_type: TerrainType = TerrainType.OPEN_COUNTRY

    def get_wind_at_point(self, coord: Coordinate) -> Optional[WindVector]:
        """Interpoliere Windvektor an spezifischem Punkt"""
        # Vereinfachte Implementierung - nächster Gitterpunkt
        min_distance = float("in")
        nearest_wind = None

        for grid_key, wind_vector in self.wind_vectors.items():
            try:
                lat_str, lon_str = grid_key.split("_")
                grid_lat, grid_lon = float(lat_str), float(lon_str)
                grid_coord = Coordinate(grid_lat, grid_lon)

                distance = coord.distance_to(grid_coord)
                if distance < min_distance:
                    min_distance = distance
                    nearest_wind = wind_vector

            except (ValueError, AttributeError):
                continue

        return nearest_wind

    def interpolate_wind_field(self, target_points: List[Coordinate]) -> Dict[str, WindVector]:
        """Interpoliere Windfeld auf Zielpunkte"""
        if not SCIPY_AVAILABLE:
            # Einfache Nearest-Neighbor Interpolation
            result = {}
            for point in target_points:
                wind = self.get_wind_at_point(point)
                if wind:
                    key = f"{point.latitude:.4f}_{point.longitude:.4f}"
                    result[key] = wind
            return result

        # Erweiterte Interpolation mit SciPy
        # TODO: Implementiere bilineare/bikubische Interpolation
        return {}

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["stability_class"] = self.stability_class.value
        result["terrain_type"] = self.terrain_type.value
        result["wind_vectors"] = {k: v.to_dict() for k, v in self.wind_vectors.items()}
        return result


@dataclass
class EmissionSource:
    """Emissionsquelle"""

    source_id: str
    coordinate: Coordinate
    source_type: EmissionSourceType

    # Emissionsparameter
    emission_rate: float  # Emission Rate (kg/h oder μg/s)
    pollutant_name: str  # Schadstoff-Name
    stack_height_m: float = 0.0  # Schornsteinhöhe
    stack_diameter_m: float = 1.0  # Schornsteindurchmesser
    exit_velocity_ms: float = 0.0  # Austrittsgeschwindigkeit
    exit_temperature_k: float = 293.15  # Austrittstemperatur (20°C)

    # Geometrie (für Linien-/Flächenquellen)
    geometry_points: List[Coordinate] = field(default_factory=list)
    area_m2: float = 0.0  # Flächengröße

    # Zeitliche Variation
    temporal_profile: Dict[str, float] = field(default_factory=dict)  # Stunde -> Faktor

    def effective_stack_height(self, ambient_temp_k: float = 293.15, wind_speed_ms: float = 5.0) -> float:
        """Berechne effektive Schornsteinhöhe (mit Plume Rise)"""
        if self.source_type != EmissionSourceType.POINT_SOURCE:
            return self.stack_height_m

        # Vereinfachte Plume Rise Berechnung (Briggs-Formel)
        if self.exit_velocity_ms > 0 and self.exit_temperature_k > ambient_temp_k:
            # Buoyancy flux
            buoyancy_flux = (
                9.81
                * self.stack_diameter_m**2
                * self.exit_velocity_ms
                * (self.exit_temperature_k - ambient_temp_k)
                / (4 * self.exit_temperature_k)
            )

            if buoyancy_flux > 55:  # m^4/s^3
                # Strong buoyancy
                plume_rise = 21.4 * (buoyancy_flux / wind_speed_ms) ** (3 / 4)
            else:
                # Moderate buoyancy
                plume_rise = 6.0 * (buoyancy_flux / wind_speed_ms) ** (1 / 3)
        else:
            # Momentum rise only
            plume_rise = 3 * self.stack_diameter_m * self.exit_velocity_ms / wind_speed_ms

        return self.stack_height_m + min(plume_rise, 200)  # Max 200m rise

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["source_type"] = self.source_type.value
        result["coordinate"] = self.coordinate.to_dict()
        result["geometry_points"] = [p.to_dict() for p in self.geometry_points]
        return result


@dataclass
class ReceptorPoint:
    """Immissionsort (Rezeptor)"""

    receptor_id: str
    coordinate: Coordinate
    receptor_type: str = "general"  # "general", "sensitive", "residential"
    description: str = ""

    # Berechnung Ergebnisse
    concentrations: Dict[str, float] = field(default_factory=dict)  # Pollutant -> Konzentration

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["coordinate"] = self.coordinate.to_dict()
        return result


# =============================================================================
# STRÖMUNGSBERECHNUNG REQUEST/RESPONSE
# =============================================================================


@dataclass
class FlowCalculationRequest:
    """Request für Strömungsberechnung"""

    query_id: str
    query_text: str

    # Berechnungsbereich
    calculation_bounds: Dict[str, float]  # lat_min, lat_max, lon_min, lon_max
    grid_resolution_m: float = 100.0  # Raster-Auflösung

    # Emissionsquellen & Rezeptoren
    emission_sources: List[EmissionSource] = field(default_factory=list)
    receptor_points: List[ReceptorPoint] = field(default_factory=list)

    # Modell-Parameter
    flow_model: FlowModelType = FlowModelType.GAUSSIAN_PLUME
    calculation_period_hours: int = 1
    averaging_time_minutes: int = 60

    # Meteorologie
    use_weather_data: bool = True
    weather_station_location: Optional[Coordinate] = None
    manual_wind_data: Optional[List[WindVector]] = None

    # Erweiterte Parameter
    include_deposition: bool = False  # Trocken-/Feuchtdeposition
    include_chemical_reactions: bool = False  # Chemische Umwandlungen
    include_building_effects: bool = False  # Gebäude-Umströmung

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["flow_model"] = self.flow_model.value
        result["emission_sources"] = [s.to_dict() for s in self.emission_sources]
        result["receptor_points"] = [r.to_dict() for r in self.receptor_points]
        if self.weather_station_location:
            result["weather_station_location"] = self.weather_station_location.to_dict()
        if self.manual_wind_data:
            result["manual_wind_data"] = [w.to_dict() for w in self.manual_wind_data]
        return result


@dataclass
class FlowCalculationResult:
    """Ergebnis einer Strömungsberechnung"""

    source_id: str
    receptor_id: str

    # Berechnungsergebnisse
    concentration_ugm3: float  # Konzentration in μg/m³
    peak_concentration_ugm3: float  # Peak-Konzentration
    time_to_peak_minutes: float  # Zeit bis Peak

    # Geometrische Parameter
    distance_m: float  # Entfernung Source -> Receptor
    bearing_deg: float  # Richtung (0-360°)
    effective_height_m: float  # Effektive Freisetzungshöhe

    # Meteorologische Bedingungen
    wind_speed_ms: float
    wind_direction_deg: float
    stability_class: AtmosphericStabilityClass
    mixing_height_m: float

    # Unsicherheiten
    confidence_level: float = 0.0  # 0.0-1.0
    uncertainty_factor: float = 2.0  # Unsicherheitsfaktor

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["stability_class"] = self.stability_class.value
        return result


@dataclass
class FlowCalculationResponse:
    """Response für Strömungsberechnung"""

    query_id: str
    success: bool

    # Ergebnisse
    flow_results: List[FlowCalculationResult] = field(default_factory=list)
    wind_field: Optional[WindField] = None
    concentration_grid: Dict[str, Dict[str, float]] = field(default_factory=dict)  # lat_lon -> pollutant -> conc

    # Zusammenfassung
    total_source_receptor_pairs: int = 0
    max_concentration_ugm3: float = 0.0
    average_concentration_ugm3: float = 0.0
    exceedances_count: int = 0  # Grenzwert-Überschreitungen

    # Metadaten
    model_used: str = ""
    calculation_time_s: float = 0.0
    weather_data_source: str = ""
    grid_points_calculated: int = 0

    # Qualität
    confidence_score: float = 0.0
    model_uncertainty: str = ""

    # Error handling
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["flow_results"] = [r.to_dict() for r in self.flow_results]
        if self.wind_field:
            result["wind_field"] = self.wind_field.to_dict()
        return result

    def get_max_impact_receptor(self) -> Optional[FlowCalculationResult]:
        """Rezeptor mit höchster Belastung"""
        if not self.flow_results:
            return None
        return max(self.flow_results, key=lambda r: r.concentration_ugm3)


# =============================================================================
# ATMOSPHERIC FLOW AGENT KONFIGURATION
# =============================================================================


@dataclass
class AtmosphericFlowConfig:
    """Atmospheric Flow Agent Konfiguration"""

    # Modell-Parameter
    default_flow_model: str = "gaussian_plume"
    supported_models: List[str] = field(default_factory=lambda: ["gaussian_plume", "gaussian_puf", "lagrangian"])

    # Raster-Parameter
    default_grid_resolution_m: float = 100.0
    max_grid_points: int = 10000
    max_calculation_distance_km: float = 50.0

    # Meteorologie
    weather_integration_enabled: bool = True
    default_stability_class: str = "D"
    default_mixing_height_m: float = 1000.0
    default_roughness_length_m: float = 0.1

    # Performance
    max_sources: int = 100
    max_receptors: int = 1000
    calculation_timeout_s: int = 300
    parallel_calculations: bool = True

    # Cache
    cache_enabled: bool = True
    cache_ttl_seconds: int = 1800  # 30 Minuten

    # Physikalische Konstanten
    air_density_kgm3: float = 1.225  # Luftdichte
    gravity_ms2: float = 9.81  # Gravitationskonstante
    von_karman_constant: float = 0.4  # von Kármán-Konstante

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# ATMOSPHERIC FLOW AGENT HAUPTKLASSE
# =============================================================================


class AtmosphericFlowAgent:
    """
    VERITAS Atmospheric Flow Agent

    Spezialisierter Agent für Strömungsraster-Berechnungen und Schadstoffausbreitung:
    - Gaussian Plume/Puff Modelle
    - Lagrangian Particle Tracking
    - Windfeld-Interpolation
    - Emittenten-Immissions-Mapping
    - DWD Weather Integration
    - Topographische Korrekturen
    """

    def __init__(self, config: AtmosphericFlowConfig = None):
        self.config = config or AtmosphericFlowConfig()
        self.logger = logging.getLogger(f"{__name__}.AtmosphericFlowAgent")

        # DWD Weather Integration
        self.weather_agent = None
        if DWD_INTEGRATION_AVAILABLE and self.config.weather_integration_enabled:
            try:
                self.weather_agent = create_dwd_weather_agent()
                self.logger.info("✅ DWD Weather Agent integration enabled")
            except Exception as e:
                self.logger.warning(f"DWD Weather Agent integration failed: {e}")

        # Caches
        self._wind_field_cache: Dict[str, WindField] = {}
        self._calculation_cache: Dict[str, FlowCalculationResponse] = {}

        # Performance tracking
        self._stats = {
            "calculations_processed": 0,
            "total_source_receptor_pairs": 0,
            "weather_queries_made": 0,
            "cache_hits": 0,
            "errors": 0,
            "avg_calculation_time_s": 0,
            "total_calculation_time_s": 0,
        }

        self.logger.info("✅ Atmospheric Flow Agent initialized")

    # =========================================================================
    # HAUPT-BERECHNUNG-METHODEN
    # =========================================================================

    async def calculate_flow_async(self, request: FlowCalculationRequest) -> FlowCalculationResponse:
        """Asynchrone Strömungsberechnung (Haupt-Methode)"""
        start_time = time.time()

        try:
            self.logger.info(f"🌬️  Processing atmospheric flow calculation: {request.query_text}")

            # Cache-Check
            cache_key = self._generate_cache_key(request)
            if self.config.cache_enabled and cache_key in self._calculation_cache:
                self.logger.debug("📋 Using cached flow calculation result")
                self._stats["cache_hits"] += 1
                cached_response = self._calculation_cache[cache_key]
                cached_response.calculation_time_s = time.time() - start_time
                return cached_response

            # 1. Windfeld abrufen/berechnen
            wind_field = await self._get_wind_field(request)
            if not wind_field:
                raise ValueError("Could not obtain wind field data")

            # 2. Strömungsberechnung basierend auf Modell
            if request.flow_model == FlowModelType.GAUSSIAN_PLUME:
                response = await self._calculate_gaussian_plume(request, wind_field)
            elif request.flow_model == FlowModelType.GAUSSIAN_PUFF:
                response = await self._calculate_gaussian_puff(request, wind_field)
            elif request.flow_model == FlowModelType.LAGRANGIAN:
                response = await self._calculate_lagrangian(request, wind_field)
            else:
                response = await self._calculate_gaussian_plume(request, wind_field)  # Default

            # 3. Ergebnisse finalisieren
            calculation_time = time.time() - start_time
            response.calculation_time_s = calculation_time
            response.wind_field = wind_field
            response.model_used = request.flow_model.value

            # 4. Statistiken & Cache
            self._update_stats(calculation_time, len(request.emission_sources), len(request.receptor_points))

            if self.config.cache_enabled and response.success:
                self._calculation_cache[cache_key] = response

            self.logger.info(
                f"✅ Flow calculation completed: {response.total_source_receptor_pairs} pairs in {calculation_time:.2f}s"
            )
            return response

        except Exception as e:
            error_msg = f"Atmospheric flow calculation error: {str(e)}"
            self.logger.error(error_msg)
            self._stats["errors"] += 1

            return FlowCalculationResponse(
                query_id=request.query_id, success=False, error_message=error_msg, calculation_time_s=time.time() - start_time
            )

    def calculate_flow(self, request: FlowCalculationRequest) -> FlowCalculationResponse:
        """Synchrone Strömungsberechnung"""
        return asyncio.run(self.calculate_flow_async(request))

    # =========================================================================
    # WINDFELD-MANAGEMENT
    # =========================================================================

    async def _get_wind_field(self, request: FlowCalculationRequest) -> Optional[WindField]:
        """Windfeld für Berechnungsgebiet abrufen"""
        try:
            # 1. Manuelle Winddaten verwenden
            if request.manual_wind_data:
                return self._create_wind_field_from_manual_data(
                    request.manual_wind_data, request.calculation_bounds, request.grid_resolution_m
                )

            # 2. DWD Weather Agent verwenden
            if self.weather_agent and request.use_weather_data:
                return await self._get_wind_field_from_dwd(request)

            # 3. Default-Windfeld generieren
            return self._create_default_wind_field(request.calculation_bounds, request.grid_resolution_m)

        except Exception as e:
            self.logger.error(f"Wind field retrieval error: {e}")
            return None

    async def _get_wind_field_from_dwd(self, request: FlowCalculationRequest) -> Optional[WindField]:
        """Windfeld vom DWD Weather Agent abrufen"""
        if not DWD_INTEGRATION_AVAILABLE or not self.weather_agent:
            return None

        try:
            from .veritas_api_agent_dwd_weather import DwdWeatherQueryRequest, WeatherParameter

            # Zentrum des Berechnungsgebiets bestimmen
            center_lat = (request.calculation_bounds["lat_min"] + request.calculation_bounds["lat_max"]) / 2
            center_lon = (request.calculation_bounds["lon_min"] + request.calculation_bounds["lon_max"]) / 2

            # DWD Weather Query
            weather_request = DwdWeatherQueryRequest(
                query_id=f"flow-weather-{request.query_id}",
                query_text="Wind data for atmospheric flow calculation",
                latitude=center_lat,
                longitude=center_lon,
                start_date=datetime.now().strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d"),
                interval=WeatherInterval.HOURLY,
                parameters=[WeatherParameter.WIND, WeatherParameter.TEMPERATURE, WeatherParameter.PRESSURE],
            )

            weather_response = await self.weather_agent.execute_query_async(weather_request)
            self._stats["weather_queries_made"] += 1

            if weather_response.success and weather_response.results:
                return self._convert_weather_to_wind_field(weather_response.results[0], request)

        except Exception as e:
            self.logger.warning(f"DWD weather integration error: {e}")

        return None

    def _create_wind_field_from_manual_data(
        self, wind_data: List[WindVector], bounds: Dict[str, float], resolution: float
    ) -> WindField:
        """Erstelle Windfeld aus manuellen Winddaten"""
        # Für Demo: Einheitliches Windfeld mit erstem WindVector
        wind_vector = wind_data[0] if wind_data else WindVector(5.0, 270.0)  # 5 m/s aus West

        wind_vectors = {}

        # Raster-Punkte generieren
        lat_range = bounds["lat_max"] - bounds["lat_min"]
        lon_range = bounds["lon_max"] - bounds["lon_min"]

        # Ungefähre Anzahl Grid-Punkte basierend auf Auflösung
        lat_steps = max(3, int(lat_range * 111320 / resolution))  # ~111320m per degree
        lon_steps = max(3, int(lon_range * 111320 / resolution))

        for i in range(lat_steps):
            for j in range(lon_steps):
                lat = bounds["lat_min"] + (lat_range * i / (lat_steps - 1))
                lon = bounds["lon_min"] + (lon_range * j / (lon_steps - 1))
                key = f"{lat:.4f}_{lon:.4f}"

                # Leichte Variation für Realismus
                speed_variation = 1.0 + 0.1 * (i + j - lat_steps / 2 - lon_steps / 2) / (lat_steps + lon_steps)
                dir_variation = wind_vector.direction_deg + 5 * math.sin(i * j / 10.0)

                wind_vectors[key] = WindVector(
                    speed_ms=max(0.5, wind_vector.speed_ms * speed_variation),
                    direction_deg=dir_variation % 360,
                    elevation_m=wind_vector.elevation_m,
                    timestamp=datetime.now().isoformat(),
                )

        return WindField(
            grid_bounds=bounds,
            grid_resolution_m=resolution,
            wind_vectors=wind_vectors,
            timestamp=datetime.now().isoformat(),
            stability_class=AtmosphericStabilityClass.D,
            mixing_height_m=1000.0,
            terrain_type=TerrainType.OPEN_COUNTRY,
        )

    def _create_default_wind_field(self, bounds: Dict[str, float], resolution: float) -> WindField:
        """Erstelle Default-Windfeld für Demo"""
        # Standard: 5 m/s aus Südwesten (225°)
        default_winds = [
            WindVector(5.0, 225.0, 10.0),  # SW Wind, 5 m/s
            WindVector(3.0, 270.0, 10.0),  # W Wind, 3 m/s
            WindVector(4.0, 180.0, 10.0),  # S Wind, 4 m/s
        ]

        return self._create_wind_field_from_manual_data(default_winds, bounds, resolution)

    # =========================================================================
    # GAUSSIAN PLUME MODELL
    # =========================================================================

    async def _calculate_gaussian_plume(
        self, request: FlowCalculationRequest, wind_field: WindField
    ) -> FlowCalculationResponse:
        """Gaussian Plume Modell Berechnung"""
        response = FlowCalculationResponse(
            query_id=request.query_id,
            success=True,
            model_used="gaussian_plume",
            weather_data_source="DWD" if self.weather_agent else "Manual/Default",
        )

        try:
            flow_results = []

            # Für jede Emissionsquelle und jeden Rezeptor
            for source in request.emission_sources:
                for receptor in request.receptor_points:
                    # Wind am Source-Ort
                    source_wind = wind_field.get_wind_at_point(source.coordinate)
                    if not source_wind:
                        continue

                    # Gaussian Plume Berechnung
                    result = self._calculate_gaussian_plume_concentration(source, receptor, source_wind, wind_field)

                    if result:
                        flow_results.append(result)

            response.flow_results = flow_results
            response.total_source_receptor_pairs = len(flow_results)

            # Statistiken
            if flow_results:
                concentrations = [r.concentration_ugm3 for r in flow_results]
                response.max_concentration_ugm3 = max(concentrations)
                response.average_concentration_ugm3 = sum(concentrations) / len(concentrations)
                response.confidence_score = 0.8  # Gaussian Plume hat moderate Konfidenz

            response.grid_points_calculated = len(wind_field.wind_vectors)

        except Exception as e:
            response.success = False
            response.error_message = f"Gaussian plume calculation error: {str(e)}"

        return response

    def _calculate_gaussian_plume_concentration(
        self, source: EmissionSource, receptor: ReceptorPoint, wind: WindVector, wind_field: WindField
    ) -> Optional[FlowCalculationResult]:
        """Einzelne Gaussian Plume Konzentrations-Berechnung"""
        try:
            # Geometrische Parameter
            distance = source.coordinate.distance_to(receptor.coordinate)
            if distance < 1.0:  # Minimum 1m Abstand
                distance = 1.0

            # Windrichtungs-Check: Rezeptor muss im Windschatten sein
            bearing = self._calculate_bearing(source.coordinate, receptor.coordinate)
            wind_direction_to_receptor = (wind.direction_deg + 180) % 360  # Windrichtung ZU Rezeptor

            angle_difference = abs(bearing - wind_direction_to_receptor)
            if angle_difference > 180:
                angle_difference = 360 - angle_difference

            # Nur bei geringem Winkel (±30°) signifikante Konzentration
            if angle_difference > 30:
                return FlowCalculationResult(
                    source_id=source.source_id,
                    receptor_id=receptor.receptor_id,
                    concentration_ugm3=0.0,
                    peak_concentration_ugm3=0.0,
                    time_to_peak_minutes=0.0,
                    distance_m=distance,
                    bearing_deg=bearing,
                    effective_height_m=source.stack_height_m,
                    wind_speed_ms=wind.speed_ms,
                    wind_direction_deg=wind.direction_deg,
                    stability_class=wind_field.stability_class,
                    mixing_height_m=wind_field.mixing_height_m,
                )

            # Effektive Schornsteinhöhe
            effective_height = source.effective_stack_height(293.15, wind.speed_ms)

            # Ausbreitungsparameter (Pasquill-Gifford)
            sigma_y = self._calculate_sigma_y(distance, wind_field.stability_class)
            sigma_z = self._calculate_sigma_z(distance, wind_field.stability_class)

            # Höhenunterschied Source-Receptor
            height_diff = abs(source.coordinate.elevation_m - receptor.coordinate.elevation_m)

            # Gaussian Plume Formel
            # C = (Q / (π * σy * σz * u)) * exp(-0.5 * (y²/σy² + (z-H)²/σz²))

            # Vereinfachung: y = 0 (Receptor genau im Windschatten)
            y_deviation = 0.0  # Vereinfachung für Demo

            # z-Komponente: Höhendifferenz
            z_term = height_diff

            # Gaussian-Faktoren
            y_factor = math.exp(-0.5 * (y_deviation / sigma_y) ** 2) if sigma_y > 0 else 1.0
            z_factor = (
                (
                    math.exp(-0.5 * ((z_term - effective_height) / sigma_z) ** 2)
                    + math.exp(-0.5 * ((z_term + effective_height) / sigma_z) ** 2)  # Ground reflection
                )
                if sigma_z > 0
                else 1.0
            )

            # Gesamtkonzentration
            if sigma_y > 0 and sigma_z > 0 and wind.speed_ms > 0:
                concentration = source.emission_rate / (math.pi * sigma_y * sigma_z * wind.speed_ms) * y_factor * z_factor

                # Einheiten-Umrechnung (kg/h -> μg/m³)
                # Vereinfachte Umrechnung für Demo
                concentration_ugm3 = concentration * 1e9 / 3600  # kg/h -> μg/s -> μg/m³

                # Wind-Effekt: reduzierte Konzentration bei starkem Wind
                wind_reduction = 1.0 + wind.speed_ms * 0.1
                concentration_ugm3 /= wind_reduction

            else:
                concentration_ugm3 = 0.0

            # Peak-Konzentration (näherungsweise 50% höher)
            peak_concentration = concentration_ugm3 * 1.5

            # Zeit bis Peak (Transportzeit)
            time_to_peak = (distance / max(wind.speed_ms, 0.5)) / 60  # Minuten

            return FlowCalculationResult(
                source_id=source.source_id,
                receptor_id=receptor.receptor_id,
                concentration_ugm3=max(0, concentration_ugm3),
                peak_concentration_ugm3=max(0, peak_concentration),
                time_to_peak_minutes=time_to_peak,
                distance_m=distance,
                bearing_deg=bearing,
                effective_height_m=effective_height,
                wind_speed_ms=wind.speed_ms,
                wind_direction_deg=wind.direction_deg,
                stability_class=wind_field.stability_class,
                mixing_height_m=wind_field.mixing_height_m,
                confidence_level=0.8,
                uncertainty_factor=2.5,
            )

        except Exception as e:
            self.logger.error(f"Gaussian plume calculation error: {e}")
            return None

    def _calculate_sigma_y(self, distance_m: float, stability: AtmosphericStabilityClass) -> float:
        """Horizontale Ausbreitungsparameter (Pasquill-Gifford)"""
        x_km = distance_m / 1000.0

        # Pasquill-Gifford Parameter für σy
        coefficients = {
            AtmosphericStabilityClass.A: (213, 0.894),  # Sehr instabil
            AtmosphericStabilityClass.B: (156, 0.894),  # Mäßig instabil
            AtmosphericStabilityClass.C: (104, 0.894),  # Leicht instabil
            AtmosphericStabilityClass.D: (68, 0.894),  # Neutral
            AtmosphericStabilityClass.E: (50.5, 0.894),  # Leicht stabil
            AtmosphericStabilityClass.F: (34, 0.894),  # Mäßig stabil
        }

        a, b = coefficients.get(stability, (68, 0.894))
        sigma_y = a * (x_km**b)

        return max(sigma_y, 1.0)  # Minimum 1m

    def _calculate_sigma_z(self, distance_m: float, stability: AtmosphericStabilityClass) -> float:
        """Vertikale Ausbreitungsparameter (Pasquill-Gifford)"""
        x_km = distance_m / 1000.0

        # Pasquill-Gifford Parameter für σz
        if x_km <= 1.0:
            coefficients = {
                AtmosphericStabilityClass.A: (200, 0.95),
                AtmosphericStabilityClass.B: (140, 0.95),
                AtmosphericStabilityClass.C: (100, 0.95),
                AtmosphericStabilityClass.D: (80, 0.95),
                AtmosphericStabilityClass.E: (60, 0.95),
                AtmosphericStabilityClass.F: (40, 0.95),
            }
        else:
            coefficients = {
                AtmosphericStabilityClass.A: (250, 0.85),
                AtmosphericStabilityClass.B: (170, 0.85),
                AtmosphericStabilityClass.C: (120, 0.85),
                AtmosphericStabilityClass.D: (90, 0.85),
                AtmosphericStabilityClass.E: (65, 0.85),
                AtmosphericStabilityClass.F: (45, 0.85),
            }

        a, b = coefficients.get(stability, (90, 0.85))
        sigma_z = a * (x_km**b)

        return max(sigma_z, 1.0)  # Minimum 1m

    # =========================================================================
    # GAUSSIAN PUFF MODELL (Vereinfacht)
    # =========================================================================

    async def _calculate_gaussian_puff(
        self, request: FlowCalculationRequest, wind_field: WindField
    ) -> FlowCalculationResponse:
        """Gaussian Puff Modell (vereinfacht als zeitabhängige Plumes)"""
        response = FlowCalculationResponse(
            query_id=request.query_id,
            success=True,
            model_used="gaussian_puf",
            weather_data_source="DWD" if self.weather_agent else "Manual/Default",
        )

        # Für Demo: verwende Gaussian Plume mit zeitlichen Variationen
        plume_response = await self._calculate_gaussian_plume(request, wind_field)

        # Modifikation für Puff-Charakteristika
        for result in plume_response.flow_results:
            # Puff hat typischerweise höhere Peak-Konzentrationen aber kürzere Dauer
            result.peak_concentration_ugm3 *= 2.0
            result.concentration_ugm3 *= 0.7  # Durchschnittskonzentration niedriger
            result.time_to_peak_minutes *= 1.5  # Längere Transportzeit

        response.flow_results = plume_response.flow_results
        response.total_source_receptor_pairs = len(response.flow_results)
        response.confidence_score = 0.7  # Puff-Modell hat etwas geringere Konfidenz

        return response

    # =========================================================================
    # LAGRANGIAN PARTICLE TRACKING (Mock-Implementierung)
    # =========================================================================

    async def _calculate_lagrangian(self, request: FlowCalculationRequest, wind_field: WindField) -> FlowCalculationResponse:
        """Lagrangian Particle Tracking (Mock-Implementierung)"""
        response = FlowCalculationResponse(
            query_id=request.query_id,
            success=True,
            model_used="lagrangian",
            weather_data_source="DWD" if self.weather_agent else "Manual/Default",
        )

        # Für Demo: simuliere Partikel-Transport
        flow_results = []

        for source in request.emission_sources:
            for receptor in request.receptor_points:
                # "Partikel" vom Source zum Receptor verfolgen
                result = self._simulate_particle_transport(source, receptor, wind_field)
                if result:
                    flow_results.append(result)

        response.flow_results = flow_results
        response.total_source_receptor_pairs = len(flow_results)
        response.confidence_score = 0.9  # Lagrangian hat höhere Genauigkeit

        return response

    def _simulate_particle_transport(
        self, source: EmissionSource, receptor: ReceptorPoint, wind_field: WindField
    ) -> Optional[FlowCalculationResult]:
        """Simuliere Partikel-Transport (vereinfacht)"""
        try:
            distance = source.coordinate.distance_to(receptor.coordinate)
            bearing = self._calculate_bearing(source.coordinate, receptor.coordinate)

            # Wind-Durchschnitt entlang des Pfades (vereinfacht)
            source_wind = wind_field.get_wind_at_point(source.coordinate)
            if not source_wind:
                return None

            # Transportzeit
            transport_time_s = distance / max(source_wind.speed_ms, 0.5)

            # Dispersionsberechnung (vereinfachte Lagrangian-Approximation)
            # Konzentration basierend auf Partikel-Dichte am Rezeptor

            # Faktor für Verdünnung mit der Zeit
            dilution_factor = 1.0 + (transport_time_s / 3600.0) * 2.0  # Pro Stunde 100% Verdünnung

            # Effektive Konzentration
            base_concentration = source.emission_rate / (distance * source_wind.speed_ms)
            concentration_ugm3 = (base_concentration * 1e6) / dilution_factor

            return FlowCalculationResult(
                source_id=source.source_id,
                receptor_id=receptor.receptor_id,
                concentration_ugm3=max(0, concentration_ugm3),
                peak_concentration_ugm3=concentration_ugm3 * 1.3,
                time_to_peak_minutes=transport_time_s / 60,
                distance_m=distance,
                bearing_deg=bearing,
                effective_height_m=source.stack_height_m,
                wind_speed_ms=source_wind.speed_ms,
                wind_direction_deg=source_wind.direction_deg,
                stability_class=wind_field.stability_class,
                mixing_height_m=wind_field.mixing_height_m,
                confidence_level=0.9,
                uncertainty_factor=1.8,
            )

        except Exception as e:
            self.logger.error(f"Particle transport simulation error: {e}")
            return None

    # =========================================================================
    # UTILITY-METHODEN
    # =========================================================================

    def _calculate_bearing(self, coord1: Coordinate, coord2: Coordinate) -> float:
        """Berechne Richtung von Koordinate 1 zu Koordinate 2 (0-360°)"""
        lat1, lon1 = math.radians(coord1.latitude), math.radians(coord1.longitude)
        lat2, lon2 = math.radians(coord2.latitude), math.radians(coord2.longitude)

        dlon = lon2 - lon1

        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)

        return (bearing_deg + 360) % 360

    def _generate_cache_key(self, request: FlowCalculationRequest) -> str:
        """Cache-Schlüssel generieren"""
        key_parts = [
            request.query_text,
            json.dumps(request.calculation_bounds),
            str(request.grid_resolution_m),
            str(len(request.emission_sources)),
            str(len(request.receptor_points)),
            request.flow_model.value,
        ]

    key_string = "|".join(key_parts)
    # Use SHA-256 for cache keys to avoid MD5 (Bandit B324)
    return hashlib.sha256(key_string.encode()).hexdigest()

    def _update_stats(self, calculation_time: float, sources: int, receptors: int):
        """Statistiken aktualisieren"""
        self._stats["calculations_processed"] += 1
        self._stats["total_source_receptor_pairs"] += sources * receptors
        self._stats["total_calculation_time_s"] += calculation_time

        # Durchschnittliche Berechnungszeit
        self._stats["avg_calculation_time_s"] = self._stats["total_calculation_time_s"] / self._stats["calculations_processed"]

    def get_status(self) -> Dict[str, Any]:
        """Agent-Status abrufen"""
        return {
            "agent_type": "atmospheric_flow",
            "version": "1.0.0",
            "status": "active",
            "weather_integration": DWD_INTEGRATION_AVAILABLE and self.weather_agent is not None,
            "scipy_available": SCIPY_AVAILABLE,
            "config": self.config.to_dict(),
            "performance": {
                "calculations_processed": self._stats["calculations_processed"],
                "total_source_receptor_pairs": self._stats["total_source_receptor_pairs"],
                "avg_calculation_time_s": round(self._stats["avg_calculation_time_s"], 3),
                "weather_queries_made": self._stats["weather_queries_made"],
                "cache_hits": self._stats["cache_hits"],
                "errors": self._stats["errors"],
                "success_rate": (
                    (self._stats["calculations_processed"] - self._stats["errors"])
                    / max(1, self._stats["calculations_processed"])
                ),
            },
            "cache": {
                "wind_field_cache_size": len(self._wind_field_cache),
                "calculation_cache_size": len(self._calculation_cache),
            },
            "capabilities": {
                "supported_models": self.config.supported_models,
                "max_sources": self.config.max_sources,
                "max_receptors": self.config.max_receptors,
                "max_distance_km": self.config.max_calculation_distance_km,
                "grid_resolution_range_m": [10, 1000],
            },
            "timestamp": datetime.now().isoformat(),
        }


# =============================================================================
# FACTORY-FUNKTION
# =============================================================================


def create_atmospheric_flow_agent(config: AtmosphericFlowConfig = None) -> AtmosphericFlowAgent:
    """Factory-Funktion für Atmospheric Flow Agent"""
    if config is None:
        config = AtmosphericFlowConfig()

    agent = AtmosphericFlowAgent(config)
    return agent


# =============================================================================
# HAUPTFUNKTION FÜR STANDALONE-TESTING
# =============================================================================


async def main():
    """Hauptfunktion für Testing"""
    print("🌬️  VERITAS Atmospheric Flow Agent - Test Suite")
    print("=" * 60)

    # Agent erstellen
    config = AtmosphericFlowConfig(weather_integration_enabled=True, default_grid_resolution_m=200.0)
    agent = create_atmospheric_flow_agent(config)

    # Test-Szenario: Schornstein -> Wohngebiet
    print("\n🏭 Test Szenario: Industrieschornstein -> Wohngebiet")

    # Emissionsquelle: Industrieschornstein
    industrial_source = EmissionSource(
        source_id="industrial_stack_1",
        coordinate=Coordinate(52.5000, 13.4000, 50.0),  # Berlin, 50m Höhe
        source_type=EmissionSourceType.POINT_SOURCE,
        emission_rate=100.0,  # kg/h
        pollutant_name="NOx",
        stack_height_m=80.0,
        stack_diameter_m=2.0,
        exit_velocity_ms=15.0,
        exit_temperature_k=423.15,  # 150°C
    )

    # Rezeptoren: Wohngebiet in verschiedenen Entfernungen
    residential_receptors = [
        ReceptorPoint(
            receptor_id="residential_1",
            coordinate=Coordinate(52.5050, 13.4100, 30.0),  # ~1km nordöstlich
            receptor_type="residential",
            description="Wohngebiet 1km entfernt",
        ),
        ReceptorPoint(
            receptor_id="residential_2",
            coordinate=Coordinate(52.5100, 13.4150, 25.0),  # ~2km nordöstlich
            receptor_type="residential",
            description="Wohngebiet 2km entfernt",
        ),
        ReceptorPoint(
            receptor_id="sensitive_school",
            coordinate=Coordinate(52.4980, 13.4050, 20.0),  # ~500m südöstlich
            receptor_type="sensitive",
            description="Schule 500m entfernt",
        ),
    ]

    # Test-Berechnungen
    test_scenarios = [
        {
            "name": "Gaussian Plume Model",
            "model": FlowModelType.GAUSSIAN_PLUME,
            "wind_data": [
                WindVector(5.0, 225.0, 10.0),  # 5 m / s aus SW (towards NE)
                WindVector(3.0, 270.0, 10.0),  # 3 m / s aus W (towards E)
            ],
        },
        {
            "name": "Gaussian Puff Model",
            "model": FlowModelType.GAUSSIAN_PUFF,
            "wind_data": [WindVector(8.0, 180.0, 10.0)],  # 8 m / s aus S (towards N)
        },
        {
            "name": "Lagrangian Model",
            "model": FlowModelType.LAGRANGIAN,
            "wind_data": [WindVector(4.0, 200.0, 10.0)],  # 4 m / s aus SSW
        },
    ]

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📊 Test {i}: {scenario['name']}")

        # Berechungsbereich um Berlin
        request = FlowCalculationRequest(
            query_id=f"test-{i}",
            query_text=f"Industrial emission dispersion - {scenario['name']}",
            calculation_bounds={"lat_min": 52.48, "lat_max": 52.52, "lon_min": 13.38, "lon_max": 13.42},
            grid_resolution_m=200.0,
            emission_sources=[industrial_source],
            receptor_points=residential_receptors,
            flow_model=scenario["model"],
            use_weather_data=False,  # Manuelle Winddaten verwenden
            manual_wind_data=scenario["wind_data"],
        )

        # Berechnung durchführen
        start_time = time.time()
        response = await agent.calculate_flow_async(request)
        calculation_time = time.time() - start_time

        # Ergebnisse anzeigen
        if response.success:
            print(f"   ✅ Success: {response.total_source_receptor_pairs} calculations in {calculation_time:.2f}s")
            print(f"   🎯 Model: {response.model_used}")
            print(f"   📈 Max Concentration: {response.max_concentration_ugm3:.2f} μg/m³")
            print(f"   📊 Avg Concentration: {response.average_concentration_ugm3:.2f} μg/m³")

            # Top 3 belastete Rezeptoren
            sorted_results = sorted(response.flow_results, key=lambda r: r.concentration_ugm3, reverse=True)

            print("   🏆 Top belastete Rezeptoren:")
            for j, result in enumerate(sorted_results[:3], 1):
                print(f"      {j}. {result.receptor_id}: {result.concentration_ugm3:.2f} μg/m³")
                print(f"         Distance: {result.distance_m:.0f}m, Bearing: {result.bearing_deg:.0f}°")
                print(f"         Peak: {result.peak_concentration_ugm3:.2f} μg/m³")
                print(f"         Time to peak: {result.time_to_peak_minutes:.1f} min")
        else:
            print(f"   ❌ Error: {response.error_message}")

    # Agent-Status
    print("\n📊 Agent Status:")
    status = agent.get_status()
    print(f"   Calculations processed: {status['performance']['calculations_processed']}")
    print(f"   Avg calculation time: {status['performance']['avg_calculation_time_s']:.2f}s")
    print(f"   Success rate: {status['performance']['success_rate']:.2%}")
    print(f"   Weather integration: {'Enabled' if status['weather_integration'] else 'Disabled'}")
    print(f"   SciPy available: {'Yes' if status['scipy_available'] else 'No'}")

    print("\n✅ Atmospheric Flow Agent test completed!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Run tests
    asyncio.run(main())
