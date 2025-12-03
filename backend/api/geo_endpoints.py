"""
Geo API Endpoints - FastAPI Routes für Geo Sub-Agent

Endpoints:
- POST /api/geo/query - Geodaten aus ThemisDB abrufen
- POST /api/geo/map - Karte generieren
- GET /api/geo/bbox/brandenburg - Brandenburg Bounding Box
- POST /api/geo/transform - Koordinaten transformieren
"""

import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.agents.geo_sub_agent import GeoSubAgent, CoordinateTransformer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/geo", tags=["Geo"])


# Pydantic Models
class GeoQueryRequest(BaseModel):
    """Request-Modell für Geo-Abfrage"""
    source: str = Field(
        ...,
        description="Datenquelle: 'bimschg', 'wka', 'themis:collection_name'",
        examples=["bimschg", "wka", "themis:facilities"]
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional: Filter-Parameter"
    )
    bbox: Optional[List[float]] = Field(
        None,
        description="Optional: Bounding Box [min_lat, min_lon, max_lat, max_lon]"
    )


class GeoQueryResponse(BaseModel):
    """Response-Modell für Geo-Abfrage"""
    features: List[Dict[str, Any]]
    count: int
    source: str


class MapGenerateRequest(BaseModel):
    """Request-Modell für Karten-Generierung"""
    geo_data: List[Dict[str, Any]] = Field(
        ...,
        description="GeoJSON Features"
    )
    center: Optional[List[float]] = Field(
        [52.5, 13.0],
        description="Karten-Zentrum [lat, lon]"
    )
    zoom: Optional[int] = Field(
        8,
        ge=1,
        le=18,
        description="Zoom-Level"
    )
    width: Optional[int] = Field(
        800,
        ge=400,
        le=2000,
        description="Breite in Pixel"
    )
    height: Optional[int] = Field(
        600,
        ge=300,
        le=1500,
        description="Höhe in Pixel"
    )
    title: Optional[str] = Field(
        "Karte",
        description="Karten-Titel"
    )
    style: Optional[str] = Field(
        "markers",
        description="Karten-Stil: 'markers', 'heatmap', 'cluster'"
    )


class MapGenerateResponse(BaseModel):
    """Response-Modell für Karten-Generierung"""
    success: bool
    image_base64: Optional[str] = None
    png_path: Optional[str] = None
    geojson: Optional[Dict[str, Any]] = None
    feature_count: Optional[int] = None
    error: Optional[str] = None


class CoordinateTransformRequest(BaseModel):
    """Request-Modell für Koordinaten-Transformation"""
    ostwert: float = Field(
        ...,
        description="UTM Easting (Ostwert) in Metern"
    )
    nordwert: float = Field(
        ...,
        description="UTM Northing (Nordwert) in Metern"
    )


class CoordinateTransformResponse(BaseModel):
    """Response-Modell für Koordinaten-Transformation"""
    latitude: float
    longitude: float
    valid: bool
    in_brandenburg: bool


# Global Agent-Instanz
_geo_agent: Optional[GeoSubAgent] = None


def get_geo_agent() -> GeoSubAgent:
    """Singleton-Zugriff auf GeoSubAgent"""
    global _geo_agent
    if _geo_agent is None:
        _geo_agent = GeoSubAgent()
        logger.info("GeoSubAgent initialisiert")
    return _geo_agent


@router.post("/query", response_model=GeoQueryResponse)
async def query_geo_data(request: GeoQueryRequest):
    """
    Geodaten aus verschiedenen Quellen abrufen
    
    **Datenquellen:**
    - `bimschg` - BImSchG-Anlagen mit ETRS89 UTM Koordinaten
    - `wka` - Windkraftanlagen mit ETRS89 UTM Koordinaten
    - `themis:collection` - ThemisDB Geo-Collection
    
    **Beispiel:**
    
    ```json
    {
        "source": "bimschg",
        "filters": {"category": "1.1"},
        "bbox": [51.0, 11.0, 54.0, 15.0]
    }
    ```
    
    **Response:**
    ```json
    {
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [13.404954, 52.520008]
                },
                "properties": {
                    "name": "Anlage XYZ",
                    "category": "1.1"
                }
            }
        ],
        "count": 5,
        "source": "bimschg"
    }
    ```
    """
    try:
        logger.info(f"Geo-Abfrage: {request.source}")
        
        agent = get_geo_agent()
        
        geo_data = await agent.get_geo_data({
            'source': request.source,
            'filters': request.filters or {},
            'bbox': request.bbox
        })
        
        return GeoQueryResponse(
            features=geo_data,
            count=len(geo_data),
            source=request.source
        )
    
    except Exception as e:
        logger.error(f"Geo-Abfrage fehlgeschlagen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/map", response_model=MapGenerateResponse)
async def generate_map(request: MapGenerateRequest):
    """
    Karte aus Geodaten generieren
    
    Generiert eine statische Karte (PNG) mit Markern für die übergebenen
    Geo-Features. Unterstützt verschiedene Stile und Export-Formate.
    
    **Beispiel:**
    
    ```json
    {
        "geo_data": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [13.4, 52.5]},
                "properties": {"name": "Berlin"}
            }
        ],
        "center": [52.5, 13.0],
        "zoom": 8,
        "width": 800,
        "height": 600,
        "title": "Brandenburg Anlagen",
        "style": "markers"
    }
    ```
    
    **Response:**
    ```json
    {
        "success": true,
        "image_base64": "iVBORw0KGgo...",
        "png_path": "/tmp/veritas_geo/map_123.png",
        "geojson": {...},
        "feature_count": 5
    }
    ```
    """
    try:
        logger.info(f"Karten-Generierung: {len(request.geo_data)} Features")
        
        agent = get_geo_agent()
        
        result = await agent.generate_map(
            geo_data=request.geo_data,
            map_spec={
                'center': request.center,
                'zoom': request.zoom,
                'width': request.width,
                'height': request.height,
                'title': request.title,
                'style': request.style
            }
        )
        
        return MapGenerateResponse(**result)
    
    except Exception as e:
        logger.error(f"Karten-Generierung fehlgeschlagen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bbox/brandenburg")
async def get_brandenburg_bbox():
    """
    Brandenburg Bounding Box abrufen
    
    Gibt die geografischen Grenzen von Brandenburg zurück.
    
    **Response:**
    ```json
    {
        "min_lat": 51.3,
        "min_lon": 11.3,
        "max_lat": 53.6,
        "max_lon": 14.8,
        "center": [52.45, 13.05],
        "description": "Brandenburg, Deutschland"
    }
    ```
    """
    return {
        "min_lat": 51.3,
        "min_lon": 11.3,
        "max_lat": 53.6,
        "max_lon": 14.8,
        "center": [52.45, 13.05],
        "description": "Brandenburg, Deutschland",
        "epsg_utm": "EPSG:25833",  # ETRS89 UTM Zone 33N
        "epsg_wgs84": "EPSG:4326"  # WGS84
    }


@router.post("/transform", response_model=CoordinateTransformResponse)
async def transform_coordinates(request: CoordinateTransformRequest):
    """
    Koordinaten transformieren (ETRS89 UTM → WGS84)
    
    Transformiert UTM-Koordinaten (Zone 33N) in WGS84 Latitude/Longitude.
    
    **Beispiel:**
    
    ```json
    {
        "ostwert": 480000,
        "nordwert": 5740000
    }
    ```
    
    **Response:**
    ```json
    {
        "latitude": 51.8123,
        "longitude": 13.4567,
        "valid": true,
        "in_brandenburg": true
    }
    ```
    """
    try:
        transformer = CoordinateTransformer()
        
        # Transformation
        lat, lon = transformer.utm33n_to_wgs84(request.ostwert, request.nordwert)
        
        # Validierung
        valid = transformer.is_valid_utm33n(request.ostwert, request.nordwert)
        in_brandenburg = transformer.is_valid_brandenburg(lat, lon)
        
        return CoordinateTransformResponse(
            latitude=lat,
            longitude=lon,
            valid=valid,
            in_brandenburg=in_brandenburg
        )
    
    except Exception as e:
        logger.error(f"Koordinaten-Transformation fehlgeschlagen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health-Check für Geo-Service
    
    **Response:**
    ```json
    {
        "status": "healthy",
        "agent_initialized": true,
        "pyproj_available": true,
        "matplotlib_available": true
    }
    ```
    """
    try:
        agent = get_geo_agent()
        
        from backend.agents.geo_sub_agent import PYPROJ_AVAILABLE, MATPLOTLIB_AVAILABLE, PIL_AVAILABLE
        
        return {
            "status": "healthy",
            "agent_initialized": True,
            "output_dir": str(agent.output_dir),
            "dependencies": {
                "pyproj": PYPROJ_AVAILABLE,
                "matplotlib": MATPLOTLIB_AVAILABLE,
                "pil": PIL_AVAILABLE
            }
        }
    
    except Exception as e:
        logger.error(f"Health-Check fehlgeschlagen: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "agent_initialized": False,
            "error": str(e)
        }
