"""
Geo Sub-Agent - OSM Karten und GeoInformationen für Präsentationen

Dieser Sub-Agent integriert:
1. OpenStreetMap (OSM) Kartenmaterial
2. Geo-Informationen aus ThemisDB
3. Koordinaten-Transformation (ETRS89 UTM → WGS84)
4. Karten-Rendering für Präsentationen
5. Integration mit Presentation Canvas Agent

Datenquellen:
- BImSchG-Anlagen: ostwert/nordwert (ETRS89 UTM Zone 33N)
- WKA-Anlagen: rechts/hoch (ETRS89 UTM Zone 33N)
- ThemisDB: Geo-Collections mit Standortdaten
"""

import json
import logging
import base64
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from io import BytesIO
from pathlib import Path

if TYPE_CHECKING:
    from PIL import Image as PILImage

# Koordinaten-Transformation
try:
    from pyproj import Transformer
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False
    Transformer = None

# Kartengenerierung
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

# Matplotlib für statische Karten (Basemap-Alternative)
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

logger = logging.getLogger(__name__)


class CoordinateTransformer:
    """
    Koordinaten-Transformation zwischen verschiedenen Systemen
    
    Unterstützt:
    - ETRS89 UTM Zone 33N (EPSG:25833) → WGS84 (EPSG:4326)
    - Brandenburg-spezifische Validierung
    """
    
    def __init__(self):
        if not PYPROJ_AVAILABLE:
            logger.warning("pyproj nicht verfügbar, Koordinaten-Transformation deaktiviert")
            self.transformer = None
            return
        
        # ETRS89 UTM Zone 33N → WGS84
        self.transformer = Transformer.from_crs(
            "EPSG:25833",  # ETRS89 UTM Zone 33N (Brandenburg)
            "EPSG:4326",   # WGS84 (lat/lon für Web-Karten)
            always_xy=True
        )
    
    def utm33n_to_wgs84(self, ostwert: float, nordwert: float) -> Tuple[float, float]:
        """
        Transformiert ETRS89 UTM Zone 33N → WGS84
        
        Args:
            ostwert: UTM Easting (Rechtswert) in Metern
            nordwert: UTM Northing (Hochwert) in Metern
            
        Returns:
            tuple: (latitude, longitude) in Grad
        """
        if not self.transformer:
            raise RuntimeError("Koordinaten-Transformation nicht verfügbar (pyproj fehlt)")
        
        lon, lat = self.transformer.transform(ostwert, nordwert)
        return lat, lon
    
    def is_valid_brandenburg(self, lat: float, lon: float) -> bool:
        """
        Prüft ob Koordinaten in Brandenburg liegen
        
        Brandenburg Bounds:
        - Latitude: 51.3° - 53.6° N
        - Longitude: 11.3° - 14.8° E
        """
        return (51.0 <= lat <= 54.0) and (11.0 <= lon <= 15.0)
    
    def is_valid_utm33n(self, ostwert: float, nordwert: float) -> bool:
        """
        Prüft ob UTM Koordinaten plausibel sind
        
        Brandenburg UTM Zone 33N:
        - Ostwert (Easting): 350000 - 600000 m
        - Nordwert (Northing): 5700000 - 5950000 m
        """
        return (300000 <= ostwert <= 700000) and (5600000 <= nordwert <= 6000000)


class GeoSubAgent:
    """
    Geo Sub-Agent für OSM-Karten und Geo-Informationen
    
    Funktionen:
    1. Geodaten aus ThemisDB abrufen
    2. Koordinaten transformieren (ETRS89 → WGS84)
    3. OSM-Karten generieren
    4. Marker/Cluster für Anlagen
    5. Karten für Präsentationen rendern
    """
    
    def __init__(
        self,
        themis_db=None,
        output_dir: str = "/tmp/veritas_geo"
    ):
        """
        Args:
            themis_db: ThemisDB-Adapter für Geo-Abfragen
            output_dir: Verzeichnis für Karten-Exports
        """
        self.themis_db = themis_db
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.transformer = CoordinateTransformer()
        
        logger.info("GeoSubAgent initialisiert")
    
    async def get_geo_data(
        self,
        query_spec: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Geodaten aus ThemisDB abrufen
        
        Args:
            query_spec: {
                'source': 'bimschg' | 'wka' | 'themis_collection',
                'filters': {...},
                'bbox': [min_lat, min_lon, max_lat, max_lon]  # Optional
            }
            
        Returns:
            List of geo-features mit WGS84-Koordinaten
        """
        source = query_spec.get('source', 'bimschg')
        filters = query_spec.get('filters', {})
        bbox = query_spec.get('bbox')
        
        geo_data = []
        
        if source == 'bimschg':
            geo_data = await self._get_bimschg_data(filters, bbox)
        elif source == 'wka':
            geo_data = await self._get_wka_data(filters, bbox)
        elif source.startswith('themis:'):
            collection = source.split(':')[1]
            geo_data = await self._get_themis_geo_data(collection, filters, bbox)
        else:
            # Fallback: Beispieldaten
            geo_data = self._get_example_geo_data()
        
        return geo_data
    
    async def _get_bimschg_data(
        self,
        filters: Dict[str, Any],
        bbox: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """
        BImSchG-Anlagen mit Geodaten abrufen
        
        TODO: Integration mit UDS3/ThemisDB
        Aktuell: Beispieldaten
        """
        logger.info("BImSchG Geodaten werden abgerufen (Beispieldaten)")
        
        # Beispiel-Anlagen in Brandenburg
        example_sites = [
            {"name": "Kraftwerk Jänschwalde", "ostwert": 480000, "nordwert": 5740000, "type": "1.1"},
            {"name": "Zementwerk Rüdersdorf", "ostwert": 415000, "nordwert": 5820000, "type": "2.3"},
            {"name": "Papierfabrik Schwedt", "ostwert": 470000, "nordwert": 5890000, "type": "6.1"},
            {"name": "Tierhaltung Uckermark", "ostwert": 445000, "nordwert": 5910000, "type": "7.1"},
            {"name": "Abfallanlage Schöneiche", "ostwert": 405000, "nordwert": 5810000, "type": "8.1"},
        ]
        
        geo_features = []
        for site in example_sites:
            try:
                lat, lon = self.transformer.utm33n_to_wgs84(
                    site['ostwert'],
                    site['nordwert']
                )
                
                if bbox:
                    # Bbox-Filterung
                    min_lat, min_lon, max_lat, max_lon = bbox
                    if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
                        continue
                
                geo_features.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [lon, lat]
                    },
                    'properties': {
                        'name': site['name'],
                        'category': site['type'],
                        'source': 'bimschg'
                    }
                })
            except Exception as e:
                logger.warning(f"Fehler bei Koordinaten-Transformation: {e}")
        
        return geo_features
    
    async def _get_wka_data(
        self,
        filters: Dict[str, Any],
        bbox: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """
        WKA-Anlagen mit Geodaten abrufen
        
        TODO: Integration mit UDS3/ThemisDB
        Aktuell: Beispieldaten
        """
        logger.info("WKA Geodaten werden abgerufen (Beispieldaten)")
        
        # Beispiel-Windparks in Brandenburg
        example_sites = [
            {"name": "Windpark Prignitz", "ostwert": 365000, "nordwert": 5850000, "leistung": 45.5},
            {"name": "Windpark Uckermark Nord", "ostwert": 460000, "nordwert": 5920000, "leistung": 67.2},
            {"name": "Windpark Märkisch-Oderland", "ostwert": 440000, "nordwert": 5815000, "leistung": 32.8},
            {"name": "Windpark Spree-Neiße", "ostwert": 510000, "nordwert": 5730000, "leistung": 28.4},
            {"name": "Windpark Havelland", "ostwert": 370000, "nordwert": 5830000, "leistung": 51.6},
        ]
        
        geo_features = []
        for site in example_sites:
            try:
                lat, lon = self.transformer.utm33n_to_wgs84(
                    site['ostwert'],
                    site['nordwert']
                )
                
                if bbox:
                    min_lat, min_lon, max_lat, max_lon = bbox
                    if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
                        continue
                
                geo_features.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [lon, lat]
                    },
                    'properties': {
                        'name': site['name'],
                        'leistung': site['leistung'],
                        'source': 'wka'
                    }
                })
            except Exception as e:
                logger.warning(f"Fehler bei Koordinaten-Transformation: {e}")
        
        return geo_features
    
    async def _get_themis_geo_data(
        self,
        collection: str,
        filters: Dict[str, Any],
        bbox: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Geodaten aus ThemisDB-Collection abrufen
        
        TODO: ThemisDB Geo-Query implementieren
        """
        logger.info(f"ThemisDB Geodaten werden abgerufen: {collection}")
        
        if not self.themis_db:
            logger.warning("ThemisDB nicht verfügbar, nutze Beispieldaten")
            return self._get_example_geo_data()
        
        # TODO: ThemisDB Geo-Query
        # geo_data = await self.themis_db.geo_query(
        #     collection=collection,
        #     filters=filters,
        #     bbox=bbox
        # )
        
        return self._get_example_geo_data()
    
    def _get_example_geo_data(self) -> List[Dict[str, Any]]:
        """Beispiel-Geodaten für Tests"""
        return [
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [13.404954, 52.520008]  # Berlin
                },
                'properties': {
                    'name': 'Beispiel-Standort Berlin',
                    'source': 'example'
                }
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [14.550120, 52.406374]  # Frankfurt (Oder)
                },
                'properties': {
                    'name': 'Beispiel-Standort Frankfurt/Oder',
                    'source': 'example'
                }
            }
        ]
    
    async def generate_map(
        self,
        geo_data: List[Dict[str, Any]],
        map_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Karte generieren aus Geodaten
        
        Args:
            geo_data: GeoJSON-Features
            map_spec: {
                'center': [lat, lon],
                'zoom': 8,
                'width': 800,
                'height': 600,
                'title': 'Karten-Titel',
                'style': 'markers' | 'heatmap' | 'cluster'
            }
            
        Returns:
            {
                'success': bool,
                'image_base64': str,
                'png_path': str,
                'geojson': dict
            }
        """
        try:
            logger.info(f"Karte wird generiert: {len(geo_data)} Features")
            
            # Map-Parameter
            center = map_spec.get('center', [52.5, 13.0])  # Brandenburg Zentrum
            zoom = map_spec.get('zoom', 8)
            width = map_spec.get('width', 800)
            height = map_spec.get('height', 600)
            title = map_spec.get('title', 'Karte')
            style = map_spec.get('style', 'markers')
            
            # Karte rendern
            if MATPLOTLIB_AVAILABLE:
                img_data = self._render_map_matplotlib(
                    geo_data, center, width, height, title, style
                )
            elif PIL_AVAILABLE:
                img_data = self._render_map_pil(
                    geo_data, center, width, height, title
                )
            else:
                raise RuntimeError("Weder Matplotlib noch PIL verfügbar")
            
            # Speichern
            import time
            timestamp = int(time.time() * 1000)
            png_path = self.output_dir / f"map_{timestamp}.png"
            img_data.save(png_path, 'PNG')
            
            # Base64 encodieren
            buf = BytesIO()
            img_data.save(buf, format='PNG')
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')
            
            # GeoJSON-FeatureCollection
            geojson = {
                'type': 'FeatureCollection',
                'features': geo_data
            }
            
            return {
                'success': True,
                'image_base64': image_base64,
                'png_path': str(png_path),
                'geojson': geojson,
                'feature_count': len(geo_data)
            }
        
        except Exception as e:
            logger.error(f"Karten-Generierung fehlgeschlagen: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _render_map_matplotlib(
        self,
        geo_data: List[Dict[str, Any]],
        center: List[float],
        width: int,
        height: int,
        title: str,
        style: str
    ) -> Any:  # Returns PIL Image if available
        """
        Karte mit Matplotlib rendern (statische Karte)
        
        Zeigt Brandenburg-Region mit Markern
        """
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
        
        # Brandenburg Bounding Box
        # Latitude: 51.3° - 53.6° N
        # Longitude: 11.3° - 14.8° E
        ax.set_xlim(11.0, 15.0)
        ax.set_ylim(51.0, 54.0)
        
        # Hintergrund
        ax.set_facecolor('#e8f4f8')
        
        # Grid (als einfache OSM-Ersatz)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Marker zeichnen
        for feature in geo_data:
            coords = feature['geometry']['coordinates']
            lon, lat = coords[0], coords[1]
            props = feature['properties']
            
            # Marker-Farbe je nach Source
            source = props.get('source', 'unknown')
            if source == 'bimschg':
                color = 'red'
                marker = 's'  # Square
            elif source == 'wka':
                color = 'green'
                marker = '^'  # Triangle
            else:
                color = 'blue'
                marker = 'o'  # Circle
            
            ax.plot(lon, lat, marker=marker, color=color, markersize=10, 
                   markeredgecolor='black', markeredgewidth=1)
            
            # Label
            name = props.get('name', 'Unbekannt')
            ax.text(lon, lat + 0.05, name, fontsize=8, ha='center', 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
        
        # Titel
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('Longitude (°E)', fontsize=10)
        ax.set_ylabel('Latitude (°N)', fontsize=10)
        
        # Legende
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='s', color='w', label='BImSchG-Anlagen',
                  markerfacecolor='red', markersize=8, markeredgecolor='black'),
            Line2D([0], [0], marker='^', color='w', label='WKA-Anlagen',
                  markerfacecolor='green', markersize=8, markeredgecolor='black')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
        
        plt.tight_layout()
        
        # In PIL-Image konvertieren
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img = Image.open(buf)
        plt.close(fig)
        
        return img
    
    def _render_map_pil(
        self,
        geo_data: List[Dict[str, Any]],
        center: List[float],
        width: int,
        height: int,
        title: str
    ) -> Any:  # Returns PIL Image
        """
        Einfache Karte mit PIL rendern (Fallback)
        """
        img = Image.new('RGB', (width, height), '#e8f4f8')
        draw = ImageDraw.Draw(img)
        
        # Titel
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            font_title = ImageFont.load_default()
            font_label = ImageFont.load_default()
        
        draw.text((width//2, 20), title, fill='black', font=font_title, anchor='mt')
        
        # Platzhalter-Text
        draw.text(
            (width//2, height//2),
            f"Geo-Karte\n{len(geo_data)} Standorte\n\n"
            f"(Matplotlib für detaillierte Karte erforderlich)",
            fill='#666666',
            font=font_label,
            anchor='mm',
            align='center'
        )
        
        # Border
        draw.rectangle([(0, 0), (width-1, height-1)], outline='#1f4788', width=3)
        
        return img


# Standalone-Test
if __name__ == '__main__':
    import asyncio
    
    async def test():
        print('=' * 70)
        print('GEO SUB-AGENT - TEST')
        print('=' * 70)
        
        agent = GeoSubAgent()
        
        # Test 1: Geodaten abrufen
        print('\n📍 Test 1: Geodaten abrufen (BImSchG)')
        geo_data = await agent.get_geo_data({'source': 'bimschg'})
        print(f'   ✅ {len(geo_data)} Features abgerufen')
        
        # Test 2: Karte generieren
        print('\n🗺️  Test 2: Karte generieren')
        result = await agent.generate_map(
            geo_data,
            {
                'title': 'BImSchG-Anlagen in Brandenburg',
                'style': 'markers'
            }
        )
        
        if result['success']:
            print(f'   ✅ Karte generiert')
            print(f'      PNG: {result["png_path"]}')
            print(f'      Features: {result["feature_count"]}')
        else:
            print(f'   ❌ Fehler: {result["error"]}')
        
        print('\n' + '=' * 70)
        print('✅ Tests abgeschlossen')
        print('=' * 70)
    
    asyncio.run(test())
