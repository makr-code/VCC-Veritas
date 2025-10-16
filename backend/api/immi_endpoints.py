"""
IMMI API Endpoints - Immissionsschutz Datenvisualisierung
==========================================================

Geodaten-Endpunkte für BImSchG-Anlagen und Windkraftanlagen (WKA)
mit ETRS89 UTM Zone 33N → WGS84 Koordinaten-Transformation.

Endpoints:
- GET /api/immi/markers/bimschg - BImSchG-Anlagen als Kartenmarker
- GET /api/immi/markers/wka - Windkraftanlagen als Kartenmarker
- GET /api/immi/heatmap/bimschg - Heatmap-Daten für BImSchG-Anlagen
- GET /api/immi/search - Suche nach Orten, Betriebsstätten
- GET /api/immi/statistics/region - Statistiken für Kartenausschnitt
- GET /api/immi/filters - Verfügbare Filter-Optionen

Autor: VERITAS Agent System
Datum: 10. Oktober 2025
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import sqlite3
from pathlib import Path
from pyproj import Transformer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/immi", tags=["IMMI - Immissionsschutz"])

# ============================================================================
# Pydantic Models
# ============================================================================

class GeoCoordinate(BaseModel):
    """Geografische Koordinate in WGS84"""
    lat: float
    lon: float

class MapMarker(BaseModel):
    """Marker für Kartenanzeige"""
    id: str
    lat: float
    lon: float
    type: str  # 'bimschg' | 'wka'
    title: str
    description: str
    category: str
    icon: str
    data: Dict[str, Any]

class HeatmapPoint(BaseModel):
    """Punkt für Heatmap"""
    lat: float
    lon: float
    intensity: float

class SearchResult(BaseModel):
    """Suchergebnis"""
    id: str
    name: str
    type: str
    ort: str
    lat: float
    lon: float

class RegionStatistics(BaseModel):
    """Statistiken für Kartenausschnitt"""
    bimschg_count: int
    wka_count: int
    total_power_mw: float
    categories: Dict[str, int]
    bounds: Dict[str, float]

class FilterOptions(BaseModel):
    """Verfügbare Filter-Optionen"""
    bimschg_categories: List[Dict[str, Any]]
    wka_status: List[str]
    orte: List[str]

# ============================================================================
# Koordinaten-Transformation
# ============================================================================

class CoordinateTransformer:
    """ETRS89 UTM Zone 33N → WGS84 Transformation"""
    
    def __init__(self):
        # ETRS89 UTM Zone 33N (EPSG:25833) → WGS84 (EPSG:4326)
        self.transformer = Transformer.from_crs(
            "EPSG:25833",  # ETRS89 UTM Zone 33N
            "EPSG:4326",   # WGS84 (lat/lon)
            always_xy=True
        )
        self._cache = {}  # Simple in-memory cache
    
    def transform(self, ostwert: float, nordwert: float) -> tuple[float, float]:
        """
        Transformiert UTM → WGS84
        
        Args:
            ostwert: UTM Easting in Metern
            nordwert: UTM Northing in Metern
        
        Returns:
            tuple: (latitude, longitude) in Grad
        """
        # Cache-Key
        cache_key = f"{ostwert:.1f},{nordwert:.1f}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            lon, lat = self.transformer.transform(ostwert, nordwert)
            
            # Validierung (Brandenburg-Region)
            if not (51.0 <= lat <= 54.0 and 11.0 <= lon <= 15.0):
                logger.warning(f"Koordinate außerhalb Brandenburg: {lat}, {lon}")
                return None, None
            
            self._cache[cache_key] = (lat, lon)
            return lat, lon
        
        except Exception as e:
            logger.error(f"Koordinaten-Transformation fehlgeschlagen: {e}")
            return None, None
    
    def is_in_bounds(
        self, 
        lat: float, 
        lon: float, 
        bounds: Optional[str]
    ) -> bool:
        """
        Prüft ob Koordinate innerhalb Bounds liegt
        
        Args:
            lat: Latitude
            lon: Longitude
            bounds: "min_lat,min_lon,max_lat,max_lon"
        
        Returns:
            bool: True wenn innerhalb Bounds
        """
        if not bounds:
            return True
        
        try:
            min_lat, min_lon, max_lat, max_lon = map(float, bounds.split(','))
            return (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)
        except:
            return True

# Globaler Transformer (wird beim Start initialisiert)
transformer = CoordinateTransformer()

# ============================================================================
# Database Helpers
# ============================================================================

def get_db_path(db_name: str) -> Path:
    """Gibt Pfad zur Datenbank zurück"""
    base_path = Path(__file__).parent.parent.parent / "data"
    return base_path / f"{db_name}.sqlite"

def get_bimschg_connection():
    """Öffnet BImSchG-Datenbank"""
    db_path = get_db_path("BImSchG")
    if not db_path.exists():
        raise HTTPException(status_code=500, detail=f"BImSchG-Datenbank nicht gefunden: {db_path}")
    return sqlite3.connect(db_path)

def get_wka_connection():
    """Öffnet WKA-Datenbank"""
    db_path = get_db_path("wka")
    if not db_path.exists():
        raise HTTPException(status_code=500, detail=f"WKA-Datenbank nicht gefunden: {db_path}")
    return sqlite3.connect(db_path)

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/markers/bimschg", response_model=List[MapMarker])
async def get_bimschg_markers(
    bounds: Optional[str] = Query(None, description="min_lat,min_lon,max_lat,max_lon"),
    nr_4bv: Optional[str] = Query(None, description="4. BImSchV-Nummer filtern"),
    ort: Optional[str] = Query(None, description="Ort filtern"),
    limit: int = Query(default=1000, le=5000, description="Max. Anzahl Marker")
) -> List[MapMarker]:
    """
    BImSchG-Anlagen als Kartenmarker
    
    - Koordinaten-Transformation ETRS89 UTM → WGS84
    - Filterung nach Bounds, 4. BImSchV-Nummer, Ort
    - Clustering-freundliches Format
    
    Example:
        GET /api/immi/markers/bimschg?bounds=52.0,12.0,53.0,14.0&nr_4bv=8.12.2V&limit=500
    """
    markers = []
    
    try:
        conn = get_bimschg_connection()
        cursor = conn.cursor()
        
        # SQL-Query zusammenbauen
        query = """
            SELECT 
                bimschg_id, 
                bst_name, 
                anl_bez, 
                nr_4bv, 
                anlart_4bv,
                ort,
                ostwert,
                nordwert,
                leistung,
                einheit
            FROM BImSchG
            WHERE ostwert IS NOT NULL AND nordwert IS NOT NULL
        """
        
        params = []
        
        if nr_4bv:
            query += " AND nr_4bv = ?"
            params.append(nr_4bv)
        
        if ort:
            query += " AND ort LIKE ?"
            params.append(f"%{ort}%")
        
        query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        logger.info(f"BImSchG: {len(rows)} Anlagen abgerufen (Filter: nr_4bv={nr_4bv}, ort={ort})")
        
        for row in rows:
            bimschg_id, bst_name, anl_bez, nr_4bv_val, anlart_4bv, ort_val, ostwert, nordwert, leistung, einheit = row
            
            # Koordinaten-Transformation
            lat, lon = transformer.transform(ostwert, nordwert)
            
            if lat is None or lon is None:
                continue
            
            # Bounds-Filter
            if not transformer.is_in_bounds(lat, lon, bounds):
                continue
            
            # Kategorie bestimmen (für Icon-Auswahl)
            category = get_bimschg_category(nr_4bv_val)
            
            marker = MapMarker(
                id=bimschg_id,
                lat=lat,
                lon=lon,
                type="bimschg",
                title=f"{bst_name}",
                description=anl_bez or "Keine Beschreibung",
                category=category,
                icon=get_bimschg_icon(category),
                data={
                    "bimschg_id": bimschg_id,
                    "bst_name": bst_name,
                    "anl_bez": anl_bez,
                    "nr_4bv": nr_4bv_val,
                    "anlart_4bv": anlart_4bv,
                    "ort": ort_val,
                    "leistung": leistung,
                    "einheit": einheit
                }
            )
            
            markers.append(marker)
        
        conn.close()
        logger.info(f"BImSchG: {len(markers)} Marker zurückgegeben")
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der BImSchG-Marker: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return markers

@router.get("/markers/wka", response_model=List[MapMarker])
async def get_wka_markers(
    bounds: Optional[str] = Query(None, description="min_lat,min_lon,max_lat,max_lon"),
    betreiber: Optional[str] = Query(None, description="Betreiber filtern"),
    status: Optional[str] = Query(None, description="Status filtern"),
    min_leistung: Optional[float] = Query(None, description="Min. Leistung in MW"),
    limit: int = Query(default=1000, le=5000, description="Max. Anzahl Marker")
) -> List[MapMarker]:
    """
    Windkraftanlagen als Kartenmarker
    
    - Koordinaten-Transformation ETRS89 UTM → WGS84
    - Filterung nach Bounds, Betreiber, Status, Leistung
    - Clustering-freundliches Format
    
    Example:
        GET /api/immi/markers/wka?bounds=52.0,12.0,53.0,14.0&status=In%20Betrieb&min_leistung=2.0
    """
    markers = []
    
    try:
        conn = get_wka_connection()
        cursor = conn.cursor()
        
        # SQL-Query zusammenbauen
        query = """
            SELECT 
                wka_id,
                anl_bez,
                betreiber,
                ort,
                ostwert,
                nordwert,
                status,
                leistung,
                nabenhoehe,
                rotordurch
            FROM wka
            WHERE ostwert IS NOT NULL AND nordwert IS NOT NULL
        """
        
        params = []
        
        if betreiber:
            query += " AND betreiber LIKE ?"
            params.append(f"%{betreiber}%")
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if min_leistung:
            query += " AND leistung >= ?"
            params.append(min_leistung)
        
        query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        logger.info(f"WKA: {len(rows)} Anlagen abgerufen (Filter: betreiber={betreiber}, status={status})")
        
        for row in rows:
            wka_id, anl_bez, betreiber_val, ort_val, ostwert, nordwert, status_val, leistung, nabenhoehe, rotordurch = row
            
            # Koordinaten-Transformation
            lat, lon = transformer.transform(ostwert, nordwert)
            
            if lat is None or lon is None:
                continue
            
            # Bounds-Filter
            if not transformer.is_in_bounds(lat, lon, bounds):
                continue
            
            marker = MapMarker(
                id=wka_id,
                lat=lat,
                lon=lon,
                type="wka",
                title=f"WKA {anl_bez or wka_id}",
                description=f"{betreiber_val or 'Unbekannter Betreiber'}",
                category=status_val or "Unbekannt",
                icon=get_wka_icon(status_val),
                data={
                    "wka_id": wka_id,
                    "anl_bez": anl_bez,
                    "betreiber": betreiber_val,
                    "ort": ort_val,
                    "status": status_val,
                    "leistung": leistung,
                    "nabenhoehe": nabenhoehe,
                    "rotordurch": rotordurch
                }
            )
            
            markers.append(marker)
        
        conn.close()
        logger.info(f"WKA: {len(markers)} Marker zurückgegeben")
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der WKA-Marker: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return markers

@router.get("/heatmap/bimschg", response_model=List[HeatmapPoint])
async def get_bimschg_heatmap(
    nr_4bv: Optional[str] = Query(None, description="4. BImSchV-Nummer filtern")
) -> List[HeatmapPoint]:
    """
    Heatmap-Daten für BImSchG-Anlagen
    
    Returns:
        Liste von Heatmap-Punkten mit Intensität (Anzahl Anlagen pro Ort)
    """
    points = []
    
    try:
        conn = get_bimschg_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                ostwert,
                nordwert,
                COUNT(*) as count
            FROM BImSchG
            WHERE ostwert IS NOT NULL AND nordwert IS NOT NULL
        """
        
        if nr_4bv:
            query += " AND nr_4bv = ?"
            cursor.execute(query + " GROUP BY ostwert, nordwert", [nr_4bv])
        else:
            cursor.execute(query + " GROUP BY ostwert, nordwert")
        
        rows = cursor.fetchall()
        
        for ostwert, nordwert, count in rows:
            lat, lon = transformer.transform(ostwert, nordwert)
            
            if lat is None or lon is None:
                continue
            
            points.append(HeatmapPoint(
                lat=lat,
                lon=lon,
                intensity=float(count)
            ))
        
        conn.close()
        logger.info(f"Heatmap: {len(points)} Punkte")
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Heatmap-Daten: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return points

@router.get("/search", response_model=List[SearchResult])
async def search_location(
    query: str = Query(..., min_length=2, description="Suchbegriff (Ort, Betriebsstätte)"),
    limit: int = Query(default=10, le=50, description="Max. Anzahl Ergebnisse")
) -> List[SearchResult]:
    """
    Suche nach Orten, Betriebsstätten
    
    Durchsucht BImSchG und WKA Datenbanken
    
    Example:
        GET /api/immi/search?query=Schwedt&limit=10
    """
    results = []
    
    try:
        # BImSchG durchsuchen
        conn_bimschg = get_bimschg_connection()
        cursor = conn_bimschg.cursor()
        
        cursor.execute("""
            SELECT DISTINCT
                bimschg_id,
                bst_name,
                ort,
                ostwert,
                nordwert
            FROM BImSchG
            WHERE (bst_name LIKE ? OR ort LIKE ?)
            AND ostwert IS NOT NULL AND nordwert IS NOT NULL
            LIMIT ?
        """, [f"%{query}%", f"%{query}%", limit])
        
        for row in cursor.fetchall():
            bimschg_id, bst_name, ort, ostwert, nordwert = row
            lat, lon = transformer.transform(ostwert, nordwert)
            
            if lat is None or lon is None:
                continue
            
            results.append(SearchResult(
                id=bimschg_id,
                name=bst_name,
                type="BImSchG",
                ort=ort,
                lat=lat,
                lon=lon
            ))
        
        conn_bimschg.close()
        
        # WKA durchsuchen (wenn noch Platz)
        if len(results) < limit:
            conn_wka = get_wka_connection()
            cursor = conn_wka.cursor()
            
            cursor.execute("""
                SELECT DISTINCT
                    wka_id,
                    betreiber,
                    ort,
                    ostwert,
                    nordwert
                FROM wka
                WHERE (betreiber LIKE ? OR ort LIKE ?)
                AND ostwert IS NOT NULL AND nordwert IS NOT NULL
                LIMIT ?
            """, [f"%{query}%", f"%{query}%", limit - len(results)])
            
            for row in cursor.fetchall():
                wka_id, betreiber, ort, ostwert, nordwert = row
                lat, lon = transformer.transform(ostwert, nordwert)
                
                if lat is None or lon is None:
                    continue
                
                results.append(SearchResult(
                    id=wka_id,
                    name=betreiber or "Unbekannter Betreiber",
                    type="WKA",
                    ort=ort,
                    lat=lat,
                    lon=lon
                ))
            
            conn_wka.close()
        
        logger.info(f"Suche '{query}': {len(results)} Ergebnisse")
        
    except Exception as e:
        logger.error(f"Fehler bei der Suche: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return results

@router.get("/statistics/region", response_model=RegionStatistics)
async def get_region_statistics(
    bounds: str = Query(..., description="min_lat,min_lon,max_lat,max_lon")
) -> RegionStatistics:
    """
    Statistiken für sichtbaren Kartenausschnitt
    
    Returns:
        Anzahl BImSchG/WKA-Anlagen, Gesamtleistung, Kategorien
    """
    try:
        min_lat, min_lon, max_lat, max_lon = map(float, bounds.split(','))
        
        stats = {
            "bimschg_count": 0,
            "wka_count": 0,
            "total_power_mw": 0.0,
            "categories": {},
            "bounds": {
                "min_lat": min_lat,
                "min_lon": min_lon,
                "max_lat": max_lat,
                "max_lon": max_lon
            }
        }
        
        # BImSchG zählen
        conn_bimschg = get_bimschg_connection()
        cursor = conn_bimschg.cursor()
        
        cursor.execute("""
            SELECT nr_4bv, COUNT(*) as count
            FROM BImSchG
            WHERE ostwert IS NOT NULL AND nordwert IS NOT NULL
            GROUP BY nr_4bv
        """)
        
        for nr_4bv, count in cursor.fetchall():
            stats["categories"][nr_4bv] = count
            stats["bimschg_count"] += count
        
        conn_bimschg.close()
        
        # WKA zählen
        conn_wka = get_wka_connection()
        cursor = conn_wka.cursor()
        
        cursor.execute("""
            SELECT COUNT(*), SUM(leistung)
            FROM wka
            WHERE ostwert IS NOT NULL AND nordwert IS NOT NULL
        """)
        
        row = cursor.fetchone()
        stats["wka_count"] = row[0] or 0
        stats["total_power_mw"] = row[1] or 0.0
        
        conn_wka.close()
        
        return RegionStatistics(**stats)
        
    except Exception as e:
        logger.error(f"Fehler bei Statistik-Berechnung: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/filters", response_model=FilterOptions)
async def get_filter_options() -> FilterOptions:
    """
    Verfügbare Filter-Optionen
    
    Returns:
        Listen aller verfügbaren 4. BImSchV-Nummern, WKA-Status, Orte
    """
    try:
        # BImSchG-Kategorien
        conn_bimschg = get_bimschg_connection()
        cursor = conn_bimschg.cursor()
        
        cursor.execute("""
            SELECT nr_4bv, anlart_4bv, COUNT(*) as count
            FROM BImSchG
            WHERE nr_4bv IS NOT NULL
            GROUP BY nr_4bv, anlart_4bv
            ORDER BY count DESC
        """)
        
        bimschg_categories = [
            {"value": nr_4bv, "label": f"{nr_4bv} - {anlart_4bv}", "count": count}
            for nr_4bv, anlart_4bv, count in cursor.fetchall()
        ]
        
        conn_bimschg.close()
        
        # WKA-Status
        conn_wka = get_wka_connection()
        cursor = conn_wka.cursor()
        
        cursor.execute("""
            SELECT DISTINCT status
            FROM wka
            WHERE status IS NOT NULL
        """)
        
        wka_status = [row[0] for row in cursor.fetchall()]
        
        # Orte (kombiniert)
        cursor.execute("""
            SELECT DISTINCT ort
            FROM wka
            WHERE ort IS NOT NULL
            ORDER BY ort
            LIMIT 100
        """)
        
        orte = [row[0] for row in cursor.fetchall()]
        
        conn_wka.close()
        
        return FilterOptions(
            bimschg_categories=bimschg_categories,
            wka_status=wka_status,
            orte=orte
        )
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Filter-Optionen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Helper Functions
# ============================================================================

def get_bimschg_category(nr_4bv: str) -> str:
    """Bestimmt Kategorie aus 4. BImSchV-Nummer"""
    if not nr_4bv:
        return "Sonstige"
    
    # Erste Ziffer extrahieren
    prefix = nr_4bv.split('.')[0]
    
    categories = {
        "1": "Feuerungsanlagen",
        "2": "Steine/Erden",
        "3": "Glas/Keramik",
        "4": "Chemische Industrie",
        "5": "Oberflächenbehandlung",
        "6": "Holz/Papier",
        "7": "Tierhaltung",
        "8": "Abfallbehandlung",
        "9": "Lagerung",
        "10": "Sonstige"
    }
    
    return categories.get(prefix, "Sonstige")

def get_bimschg_icon(category: str) -> str:
    """Icon-URL für BImSchG-Kategorie"""
    icon_map = {
        "Feuerungsanlagen": "bimschg-red.png",
        "Chemische Industrie": "bimschg-orange.png",
        "Tierhaltung": "bimschg-green.png",
        "Abfallbehandlung": "bimschg-brown.png",
        "Lagerung": "bimschg-blue.png",
        "Sonstige": "bimschg-gray.png"
    }
    
    return f"/assets/markers/{icon_map.get(category, 'bimschg-gray.png')}"

def get_wka_icon(status: str) -> str:
    """Icon-URL für WKA-Status"""
    if status == "In Betrieb":
        return "/assets/markers/wka-active.png"
    elif status == "Im Genehmigungsverfahren":
        return "/assets/markers/wka-planned.png"
    else:
        return "/assets/markers/wka-gray.png"
