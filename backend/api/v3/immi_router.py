"""
VERITAS API v3 - IMMI Router

IMMI (Immissionsschutz) Endpoints.
Spezialisierte Queries für Immissionsschutz, BImSchG und WKA-Geodaten.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List, Optional
import logging
from datetime import datetime
import uuid

from .models import (
    IMMIQueryRequest, IMMIQueryResponse,
    IMMIRegulation, IMMIGeoData,
    ErrorResponse
)
from .service_integration import (
    get_services_from_app,
    execute_query_with_pipeline
)

logger = logging.getLogger(__name__)

# ============================================================================
# Router Setup
# ============================================================================

immi_router = APIRouter(
    prefix="/immi",
    tags=["IMMI - Immissionsschutz"]
)

# ============================================================================
# Helper Functions
# ============================================================================

def get_backend_services(request: Request):
    """Hole Backend Services aus App State"""
    return get_services_from_app(request.app.state)

def generate_mock_regulations() -> List[IMMIRegulation]:
    """Generiere Mock BImSchG-Vorschriften für Fallback"""
    regulations = [
        IMMIRegulation(
            regulation_id="bimschg_004",
            title="Genehmigungsbedürftige Anlagen",
            reference="§4 BImSchG",
            content="Die Errichtung und der Betrieb von Anlagen, die auf Grund ihrer Beschaffenheit oder ihres Betriebs in besonderem Maße geeignet sind, schädliche Umwelteinwirkungen hervorzurufen...",
            category="Genehmigung"
        ),
        IMMIRegulation(
            regulation_id="bimschg_005",
            title="Pflichten der Betreiber genehmigungsbedürftiger Anlagen",
            reference="§5 BImSchG",
            content="Genehmigungsbedürftige Anlagen sind so zu errichten und zu betreiben, dass zur Gewährleistung eines hohen Schutzniveaus für die Umwelt...",
            category="Betreiberpflichten"
        ),
        IMMIRegulation(
            regulation_id="bimschg_022",
            title="Störfallverhütung",
            reference="§22 BImSchG",
            content="Die Bundesregierung wird ermächtigt, nach Anhörung der beteiligten Kreise durch Rechtsverordnung mit Zustimmung des Bundesrates...",
            category="Störfall"
        ),
        IMMIRegulation(
            regulation_id="bimschg_048",
            title="Immissionsschutzbeauftragte",
            reference="§53 BImSchG",
            content="Betreiber genehmigungsbedürftiger Anlagen haben Immissionsschutzbeauftragte zu bestellen...",
            category="Organisation"
        )
    ]
    return regulations

def generate_mock_geodata() -> List[IMMIGeoData]:
    """Generiere Mock WKA-Geodaten für Fallback"""
    geodata = [
        IMMIGeoData(
            location_id="wka_001",
            name="WKA Nordwest 1",
            latitude=52.5200,
            longitude=13.4050,
            type="wka",
            distance_to_residential=850.5,
            metadata={"height": 150, "capacity_mw": 3.5, "manufacturer": "Vestas"}
        ),
        IMMIGeoData(
            location_id="wka_002",
            name="WKA Südost 2",
            latitude=51.3397,
            longitude=12.3731,
            type="wka",
            distance_to_residential=1200.0,
            metadata={"height": 180, "capacity_mw": 4.2, "manufacturer": "Enercon"}
        ),
        IMMIGeoData(
            location_id="industrial_001",
            name="Industriegebiet Ost",
            latitude=52.4000,
            longitude=13.5000,
            type="industrial",
            distance_to_residential=500.0,
            metadata={"area_sqm": 50000, "emissions_type": "noise"}
        )
    ]
    return geodata

def format_immi_regulations(sources: List[dict]) -> List[IMMIRegulation]:
    """Formatiere Sources als BImSchG-Vorschriften"""
    regulations = []
    for source in sources[:10]:  # Max 10 Vorschriften
        reg = IMMIRegulation(
            regulation_id=source.get("id", f"reg_{uuid.uuid4().hex[:8]}"),
            title=source.get("title", source.get("file", "Unbekannte Vorschrift")),
            reference=source.get("reference", "BImSchG"),
            content=source.get("content", "")[:500] + "...",
            category=source.get("category")
        )
        regulations.append(reg)
    return regulations

# ============================================================================
# IMMI Endpoints
# ============================================================================

@immi_router.post("/query", response_model=IMMIQueryResponse)
async def immi_query(
    query_req: IMMIQueryRequest,
    request: Request
):
    """
    IMMI-spezifische Query
    
    Führt eine spezialisierte Query für Immissionsschutz durch.
    Unterstützt Technical-Mode für detaillierte rechtliche Analysen.
    """
    logger.info(f"🏭 IMMI Query: {query_req.query[:50]}...")
    
    try:
        services = get_backend_services(request)
        
        # Pipeline für IMMI-Query nutzen
        pipeline_result = await execute_query_with_pipeline(
            query_text=query_req.query,
            intelligent_pipeline=services["intelligent_pipeline"],
            session_id=query_req.session_id,
            mode="immi",  # IMMI Mode
            enable_commentary=(query_req.mode == "technical"),
            timeout=60
        )
        
        # BImSchG-Vorschriften aus Sources formatieren
        regulations = format_immi_regulations(pipeline_result.get("sources", []))
        
        # Geodaten (falls Standort angegeben)
        geodata = []
        if query_req.location:
            logger.info(f"📍 Standort-basierte Query: {query_req.location}")
            # TODO: GIS-Integration für standortbasierte WKA-Suche
            geodata = generate_mock_geodata()[:3]
        
        # Metadata erweitern
        metadata = pipeline_result.get("metadata", {})
        metadata["regulation_count"] = len(regulations)
        metadata["geodata_count"] = len(geodata)
        if query_req.location:
            metadata["location"] = query_req.location
        
        response = IMMIQueryResponse(
            query_id=pipeline_result.get("query_id", f"immi_{uuid.uuid4().hex[:8]}"),
            content=pipeline_result["content"],
            regulations=regulations,
            geodata=geodata,
            metadata=metadata,
            duration=pipeline_result.get("duration")
        )
        
        logger.info(f"✅ IMMI Query erfolgreich: {len(regulations)} Vorschriften, {len(geodata)} Geodaten")
        return response
        
    except Exception as e:
        logger.error(f"❌ IMMI Query Fehler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"IMMI Query fehlgeschlagen: {str(e)}")


@immi_router.get("/regulations", response_model=List[IMMIRegulation])
async def get_immi_regulations(
    request: Request,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20
):
    """
    BImSchG Vorschriften abrufen
    
    Ruft BImSchG-Vorschriften ab, optional gefiltert nach Kategorie und Suchbegriff.
    """
    logger.info(f"📋 IMMI Vorschriften (Category: {category}, Search: {search}, Limit: {limit})")
    
    try:
        services = get_backend_services(request)
        
        # Fallback: Mock-Vorschriften wenn UDS3 nicht verfügbar
        if not services.get("uds3"):
            logger.warning("⚠️ UDS3 nicht verfügbar - Nutze Mock-Vorschriften")
            regs = generate_mock_regulations()
            
            # Filter anwenden
            if category:
                regs = [r for r in regs if r.category and category.lower() in r.category.lower()]
            if search:
                regs = [r for r in regs if search.lower() in r.title.lower() or search.lower() in r.content.lower()]
            
            return regs[:limit]
        
        # TODO: UDS3 Integration für echte BImSchG-Vorschriften
        # regulations = await retrieve_immi_regulations_from_uds3(
        #     uds3=services["uds3"],
        #     category=category,
        #     search=search,
        #     limit=limit
        # )
        
        raise HTTPException(
            status_code=503,
            detail="IMMI Vorschriften-Abruf noch nicht implementiert"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ IMMI Vorschriften Fehler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"IMMI Vorschriften konnten nicht abgerufen werden: {str(e)}")


@immi_router.get("/geodata", response_model=List[IMMIGeoData])
async def get_immi_geodata(
    request: Request,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: float = 10.0,
    type_filter: Optional[str] = None,
    limit: int = 50
):
    """
    WKA Geodaten abrufen
    
    Ruft WKA-Geodaten ab, optional gefiltert nach Standort, Radius und Typ.
    """
    logger.info(f"🗺️ IMMI Geodaten (Lat: {latitude}, Lon: {longitude}, Radius: {radius_km}km, Type: {type_filter})")
    
    try:
        services = get_backend_services(request)
        
        # Fallback: Mock-Geodaten wenn GIS-Service nicht verfügbar
        if not services.get("uds3"):
            logger.warning("⚠️ GIS-Service nicht verfügbar - Nutze Mock-Geodaten")
            geodata = generate_mock_geodata()
            
            # Filter anwenden
            if type_filter:
                geodata = [g for g in geodata if g.type == type_filter]
            
            # TODO: Radius-Filter basierend auf Lat/Lon
            # if latitude and longitude:
            #     geodata = filter_by_distance(geodata, latitude, longitude, radius_km)
            
            return geodata[:limit]
        
        # TODO: GIS-Integration für echte WKA-Geodaten
        # geodata = await retrieve_immi_geodata_from_gis(
        #     gis_service=services["gis_service"],
        #     latitude=latitude,
        #     longitude=longitude,
        #     radius_km=radius_km,
        #     type_filter=type_filter,
        #     limit=limit
        # )
        
        raise HTTPException(
            status_code=503,
            detail="IMMI Geodaten-Abruf noch nicht implementiert"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ IMMI Geodaten Fehler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"IMMI Geodaten konnten nicht abgerufen werden: {str(e)}")


# ============================================================================
# Router Export
# ============================================================================

__all__ = ["immi_router"]
