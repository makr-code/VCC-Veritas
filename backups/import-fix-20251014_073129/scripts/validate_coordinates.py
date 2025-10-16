"""
Validierung der Koordinaten in BImSchG und WKA Datenbanken
Testet ETRS89 UTM Zone 33N → WGS84 Transformation
"""

import sqlite3
from pathlib import Path
from pyproj import Transformer

class CoordinateValidator:
    def __init__(self):
        # ETRS89 UTM Zone 33N → WGS84
        self.transformer = Transformer.from_crs(
            "EPSG:25833",  # ETRS89 UTM Zone 33N
            "EPSG:4326",   # WGS84 (lat/lon)
            always_xy=True
        )
    
    def utm33n_to_wgs84(self, ostwert, nordwert):
        """
        Transformiert ETRS89 UTM Zone 33N → WGS84
        
        Args:
            ostwert: UTM Easting (Rechtswert) in Metern
            nordwert: UTM Northing (Hochwert) in Metern
        
        Returns:
            tuple: (lat, lon) in Grad
        """
        lon, lat = self.transformer.transform(ostwert, nordwert)
        return lat, lon
    
    def is_valid_brandenburg(self, lat, lon):
        """
        Prüft ob Koordinaten in Brandenburg liegen
        
        Brandenburg Bounds:
        - Latitude: 51.3° - 53.6° N
        - Longitude: 11.3° - 14.8° E
        """
        return (51.0 <= lat <= 54.0) and (11.0 <= lon <= 15.0)
    
    def is_valid_utm33n(self, ostwert, nordwert):
        """
        Prüft ob UTM Koordinaten plausibel sind
        
        Brandenburg UTM Zone 33N:
        - Ostwert (Easting): 350000 - 600000 m
        - Nordwert (Northing): 5700000 - 5950000 m
        """
        return (300000 <= ostwert <= 700000) and (5600000 <= nordwert <= 6000000)

def validate_bimschg():
    """Validiere BImSchG-Koordinaten"""
    db_path = Path("data/BImSchG.sqlite")
    
    if not db_path.exists():
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        return
    
    print("=" * 80)
    print("  VALIDIERUNG: BImSchG-Koordinaten (ETRS89 UTM Zone 33N)")
    print("=" * 80)
    
    validator = CoordinateValidator()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Alle Datensätze mit Koordinaten
    cursor.execute("""
        SELECT bimschg_id, bst_name, anl_bez, ort, ostwert, nordwert
        FROM BImSchG
        WHERE ostwert IS NOT NULL AND nordwert IS NOT NULL
        ORDER BY bimschg_id
    """)
    
    rows = cursor.fetchall()
    total = len(rows)
    
    valid_coords = 0
    invalid_utm = 0
    invalid_wgs84 = 0
    transform_errors = 0
    
    # Statistiken
    min_lat, max_lat = 90, -90
    min_lon, max_lon = 180, -180
    min_ost, max_ost = float('inf'), -float('inf')
    min_nord, max_nord = float('inf'), -float('inf')
    
    print(f"\n📊 Analysiere {total} Datensätze mit Koordinaten...")
    print()
    
    # Erste 10 Beispiele
    print("🔍 Erste 10 Beispiele:")
    print("-" * 120)
    print(f"{'ID':<20} {'Ort':<20} {'UTM Ost':>12} {'UTM Nord':>12} {'WGS84 Lat':>12} {'WGS84 Lon':>12} {'Status':<10}")
    print("-" * 120)
    
    for i, row in enumerate(rows):
        bimschg_id, bst_name, anl_bez, ort, ostwert, nordwert = row
        
        try:
            # UTM-Validierung
            if not validator.is_valid_utm33n(ostwert, nordwert):
                invalid_utm += 1
                if i < 10:
                    print(f"{bimschg_id:<20} {ort:<20} {ostwert:>12.1f} {nordwert:>12.1f} {'':>12} {'':>12} {'⚠️ UTM':<10}")
                continue
            
            # Transformation
            lat, lon = validator.utm33n_to_wgs84(ostwert, nordwert)
            
            # WGS84-Validierung
            if not validator.is_valid_brandenburg(lat, lon):
                invalid_wgs84 += 1
                if i < 10:
                    print(f"{bimschg_id:<20} {ort:<20} {ostwert:>12.1f} {nordwert:>12.1f} {lat:>12.6f} {lon:>12.6f} {'⚠️ WGS84':<10}")
                continue
            
            # Gültige Koordinate
            valid_coords += 1
            
            # Statistiken aktualisieren
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)
            min_lon = min(min_lon, lon)
            max_lon = max(max_lon, lon)
            min_ost = min(min_ost, ostwert)
            max_ost = max(max_ost, ostwert)
            min_nord = min(min_nord, nordwert)
            max_nord = max(max_nord, nordwert)
            
            # Erste 10 anzeigen
            if i < 10:
                print(f"{bimschg_id:<20} {ort:<20} {ostwert:>12.1f} {nordwert:>12.1f} {lat:>12.6f} {lon:>12.6f} {'✅':<10}")
        
        except Exception as e:
            transform_errors += 1
            if i < 10:
                print(f"{bimschg_id:<20} {ort:<20} {ostwert:>12.1f} {nordwert:>12.1f} {'ERROR':>12} {'ERROR':>12} {'❌':<10}")
    
    print("-" * 120)
    
    # Zusammenfassung
    print("\n" + "=" * 80)
    print("  ERGEBNIS")
    print("=" * 80)
    print(f"\n✅ Gültige Koordinaten:     {valid_coords:>6} ({valid_coords/total*100:>5.1f}%)")
    print(f"⚠️  Ungültige UTM:           {invalid_utm:>6} ({invalid_utm/total*100:>5.1f}%)")
    print(f"⚠️  Ungültige WGS84:         {invalid_wgs84:>6} ({invalid_wgs84/total*100:>5.1f}%)")
    print(f"❌ Transformations-Fehler:  {transform_errors:>6} ({transform_errors/total*100:>5.1f}%)")
    print(f"{'─'*40}")
    print(f"📊 Gesamt:                  {total:>6}")
    
    if valid_coords > 0:
        print("\n" + "=" * 80)
        print("  KOORDINATEN-BEREICHE")
        print("=" * 80)
        print(f"\nETRS89 UTM Zone 33N:")
        print(f"  Ostwert:  {min_ost:>12.1f} - {max_ost:>12.1f} m  (Δ {max_ost-min_ost:>10.1f} m)")
        print(f"  Nordwert: {min_nord:>12.1f} - {max_nord:>12.1f} m  (Δ {max_nord-min_nord:>10.1f} m)")
        
        print(f"\nWGS84:")
        print(f"  Latitude:  {min_lat:>10.6f}° - {max_lat:>10.6f}° N  (Δ {max_lat-min_lat:>8.6f}°)")
        print(f"  Longitude: {min_lon:>10.6f}° - {max_lon:>10.6f}° E  (Δ {max_lon-min_lon:>8.6f}°)")
        
        # Zentrum berechnen
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        print(f"\n🎯 Zentrum (für Karten-Init): {center_lat:.6f}°N, {center_lon:.6f}°E")
    
    conn.close()
    return valid_coords, total

def validate_wka():
    """Validiere WKA-Koordinaten"""
    db_path = Path("data/wka.sqlite")
    
    if not db_path.exists():
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        return
    
    print("\n" + "=" * 80)
    print("  VALIDIERUNG: WKA-Koordinaten (ETRS89 UTM Zone 33N)")
    print("=" * 80)
    
    validator = CoordinateValidator()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Alle Datensätze mit Koordinaten
    cursor.execute("""
        SELECT wka_id, anl_bez, betreiber, ort, ostwert, nordwert, status
        FROM wka
        WHERE ostwert IS NOT NULL AND nordwert IS NOT NULL
        ORDER BY wka_id
    """)
    
    rows = cursor.fetchall()
    total = len(rows)
    
    valid_coords = 0
    invalid_utm = 0
    invalid_wgs84 = 0
    transform_errors = 0
    
    # Statistiken
    min_lat, max_lat = 90, -90
    min_lon, max_lon = 180, -180
    min_ost, max_ost = float('inf'), -float('inf')
    min_nord, max_nord = float('inf'), -float('inf')
    
    print(f"\n📊 Analysiere {total} Datensätze mit Koordinaten...")
    print()
    
    # Erste 10 Beispiele
    print("🔍 Erste 10 Beispiele:")
    print("-" * 120)
    print(f"{'Anlagen-ID':<15} {'Ort':<20} {'UTM Ost':>12} {'UTM Nord':>12} {'WGS84 Lat':>12} {'WGS84 Lon':>12} {'Status':<10}")
    print("-" * 120)
    
    for i, row in enumerate(rows):
        wka_id, anl_bez, betreiber, ort, ostwert, nordwert, status = row
        
        try:
            # UTM-Validierung
            if not validator.is_valid_utm33n(ostwert, nordwert):
                invalid_utm += 1
                if i < 10:
                    print(f"{wka_id:<15} {ort:<20} {ostwert:>12.1f} {nordwert:>12.1f} {'':>12} {'':>12} {'⚠️ UTM':<10}")
                continue
            
            # Transformation
            lat, lon = validator.utm33n_to_wgs84(ostwert, nordwert)
            
            # WGS84-Validierung
            if not validator.is_valid_brandenburg(lat, lon):
                invalid_wgs84 += 1
                if i < 10:
                    print(f"{wka_id:<15} {ort:<20} {ostwert:>12.1f} {nordwert:>12.1f} {lat:>12.6f} {lon:>12.6f} {'⚠️ WGS84':<10}")
                continue
            
            # Gültige Koordinate
            valid_coords += 1
            
            # Statistiken aktualisieren
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)
            min_lon = min(min_lon, lon)
            max_lon = max(max_lon, lon)
            min_ost = min(min_ost, ostwert)
            max_ost = max(max_ost, ostwert)
            min_nord = min(min_nord, nordwert)
            max_nord = max(max_nord, nordwert)
            
            # Erste 10 anzeigen
            if i < 10:
                print(f"{wka_id:<15} {ort:<20} {ostwert:>12.1f} {nordwert:>12.1f} {lat:>12.6f} {lon:>12.6f} {'✅':<10}")
        
        except Exception as e:
            transform_errors += 1
            if i < 10:
                print(f"{wka_id:<15} {ort:<20} {ostwert:>12.1f} {nordwert:>12.1f} {'ERROR':>12} {'ERROR':>12} {'❌':<10}")
    
    print("-" * 120)
    
    # Zusammenfassung
    print("\n" + "=" * 80)
    print("  ERGEBNIS")
    print("=" * 80)
    print(f"\n✅ Gültige Koordinaten:     {valid_coords:>6} ({valid_coords/total*100:>5.1f}%)")
    print(f"⚠️  Ungültige UTM:           {invalid_utm:>6} ({invalid_utm/total*100:>5.1f}%)")
    print(f"⚠️  Ungültige WGS84:         {invalid_wgs84:>6} ({invalid_wgs84/total*100:>5.1f}%)")
    print(f"❌ Transformations-Fehler:  {transform_errors:>6} ({transform_errors/total*100:>5.1f}%)")
    print(f"{'─'*40}")
    print(f"📊 Gesamt:                  {total:>6}")
    
    if valid_coords > 0:
        print("\n" + "=" * 80)
        print("  KOORDINATEN-BEREICHE")
        print("=" * 80)
        print(f"\nETRS89 UTM Zone 33N:")
        print(f"  Ostwert:  {min_ost:>12.1f} - {max_ost:>12.1f} m  (Δ {max_ost-min_ost:>10.1f} m)")
        print(f"  Nordwert: {min_nord:>12.1f} - {max_nord:>12.1f} m  (Δ {max_nord-min_nord:>10.1f} m)")
        
        print(f"\nWGS84:")
        print(f"  Latitude:  {min_lat:>10.6f}° - {max_lat:>10.6f}° N  (Δ {max_lat-min_lat:>8.6f}°)")
        print(f"  Longitude: {min_lon:>10.6f}° - {max_lon:>10.6f}° E  (Δ {max_lon-min_lon:>8.6f}°)")
        
        # Zentrum berechnen
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        print(f"\n🎯 Zentrum (für Karten-Init): {center_lat:.6f}°N, {center_lon:.6f}°E")
    
    conn.close()
    return valid_coords, total

if __name__ == '__main__':
    print("\n" + "🗺️ " * 40)
    print("  KOORDINATEN-VALIDIERUNG: ETRS89 UTM Zone 33N → WGS84")
    print("🗺️ " * 40 + "\n")
    
    try:
        # BImSchG validieren
        bimschg_valid, bimschg_total = validate_bimschg()
        
        # WKA validieren
        wka_valid, wka_total = validate_wka()
        
        # Gesamt-Statistik
        print("\n" + "=" * 80)
        print("  GESAMT-ÜBERSICHT")
        print("=" * 80)
        print(f"\nBImSchG:  {bimschg_valid:>6} / {bimschg_total:>6} gültig ({bimschg_valid/bimschg_total*100:>5.1f}%)")
        print(f"WKA:      {wka_valid:>6} / {wka_total:>6} gültig ({wka_valid/wka_total*100:>5.1f}%)")
        print(f"{'─'*40}")
        print(f"GESAMT:   {bimschg_valid+wka_valid:>6} / {bimschg_total+wka_total:>6} gültig ({(bimschg_valid+wka_valid)/(bimschg_total+wka_total)*100:>5.1f}%)")
        
        print("\n✅ Validierung abgeschlossen!")
        
        if bimschg_valid + wka_valid > 0:
            print("\n💡 Nächste Schritte:")
            print("   1. Backend API-Endpunkte erstellen (map_endpoints.py)")
            print("   2. Frontend Map-Komponente implementieren (MapView.vue)")
            print("   3. Leaflet.js Integration testen")
        
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
