"""
IMMI API - Quick Test Script
=============================

Testet alle IMMI-Endpunkte und zeigt Beispiel-Daten
"""

import json
from typing import Any, Dict

import requests

BASE_URL = "http://localhost:5000"


def print_section(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_endpoint(name: str, url: str, params: Dict[str, Any] = None) -> dict:
    """Testet einen API-Endpunkt"""
    print(f"📡 {name}")
    print(f"   URL: {url}")
    if params:
        print(f"   Params: {params}")

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        print(f"   ✅ Status: {response.status_code}")
        print(f"   📊 Response: {len(json.dumps(data))} Bytes")

        return data

    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return None


def main():
    print("\n" + "🗺️ " * 40)
    print("  IMMI API - Quick Test")
    print("🗺️ " * 40)

    # Test 1: Root-Endpunkt
    print_section("1. Server Status")
    data = test_endpoint("Root", f"{BASE_URL}/")

    if data:
        print(f"\n   Version: {data.get('version')}")
        print(f"   IMMI verfügbar: {bool('immi_bimschg' in data.get('endpoints', {}))}")

    # Test 2: BImSchG-Marker
    print_section("2. BImSchG-Marker (erste 3)")
    data = test_endpoint("BImSchG Marker", f"{BASE_URL}/api/immi/markers/bimschg", params={"limit": 3})

    if data and len(data) > 0:
        print(f"\n   📍 Marker-Anzahl: {len(data)}")
        print(f"\n   Beispiel-Marker:")
        marker = data[0]
        print(f"   - ID: {marker['id']}")
        print(f"   - Titel: {marker['title']}")
        print(f"   - Koordinaten: {marker['lat']:.6f}°N, {marker['lon']:.6f}°E")
        print(f"   - Kategorie: {marker['category']}")
        print(f"   - 4. BImSchV: {marker['data']['nr_4bv']}")
        print(f"   - Ort: {marker['data']['ort']}")

    # Test 3: WKA-Marker
    print_section("3. WKA-Marker (erste 3)")
    data = test_endpoint("WKA Marker", f"{BASE_URL}/api/immi/markers/wka", params={"limit": 3})

    if data and len(data) > 0:
        print(f"\n   🌬️ Marker-Anzahl: {len(data)}")
        print(f"\n   Beispiel-WKA:")
        marker = data[0]
        print(f"   - ID: {marker['id']}")
        print(f"   - Anlage: {marker['title']}")
        print(f"   - Betreiber: {marker['description']}")
        print(f"   - Koordinaten: {marker['lat']:.6f}°N, {marker['lon']:.6f}°E")
        print(f"   - Leistung: {marker['data']['leistung']} MW")
        print(f"   - Nabenhöhe: {marker['data']['nabenhoehe']} m")
        print(f"   - Status: {marker['data']['status']}")

    # Test 4: Suche
    print_section("4. Suche (Schwedt)")
    data = test_endpoint("Suche", f"{BASE_URL}/api/immi/search", params={"query": "Schwedt", "limit": 5})

    if data:
        print(f"\n   🔍 Ergebnisse: {len(data)}")
        for i, result in enumerate(data[:3], 1):
            print(f"\n   {i}. {result['name']}")
            print(f"      Typ: {result['type']} | Ort: {result['ort']}")
            print(f"      Koordinaten: {result['lat']:.6f}°N, {result['lon']:.6f}°E")

    # Test 5: Filter-Optionen
    print_section("5. Filter-Optionen")
    data = test_endpoint("Filter", f"{BASE_URL}/api/immi/filters")

    if data:
        print(f"\n   📋 BImSchG-Kategorien: {len(data.get('bimschg_categories', []))}")
        print(f"\n   TOP 5 Kategorien:")
        for i, cat in enumerate(data.get("bimschg_categories", [])[:5], 1):
            print(f"   {i}. {cat['value']}: {cat['count']} Anlagen")

        print(f"\n   🌬️ WKA-Status: {', '.join(data.get('wka_status', []))}")
        print(f"   🏘️ Orte: {len(data.get('orte', []))}")

    # Test 6: Filter-Query (Zeitweilige Lagerung)
    print_section("6. Filter-Query (8.12.2V - Zeitweilige Lagerung)")
    data = test_endpoint("BImSchG Filter", f"{BASE_URL}/api/immi/markers/bimschg", params={"nr_4bv": "8.12.2V", "limit": 5})

    if data:
        print(f"\n   📦 Lager-Anlagen: {len(data)}")
        for i, marker in enumerate(data[:3], 1):
            print(f"\n   {i}. {marker['title']}")
            print(f"      Ort: {marker['data']['ort']}")
            print(f"      Nr: {marker['data']['nr_4bv']}")

    # Test 7: Heatmap
    print_section("7. Heatmap-Daten")
    data = test_endpoint("Heatmap", f"{BASE_URL}/api/immi/heatmap/bimschg")

    if data:
        print(f"\n   🔥 Heatmap-Punkte: {len(data)}")

        # Statistiken
        intensities = [p["intensity"] for p in data]
        print(f"   📊 Durchschnitt: {sum(intensities) / len(intensities):.2f} Anlagen/Standort")
        print(f"   📊 Maximum: {max(intensities):.0f} Anlagen an einem Standort")
        print(f"   📊 Minimum: {min(intensities):.0f} Anlagen an einem Standort")

    # Test 8: WKA Filter (In Betrieb)
    print_section("8. WKA Filter (In Betrieb, >= 2 MW)")
    data = test_endpoint(
        "WKA Filter", f"{BASE_URL}/api/immi/markers/wka", params={"status": "in Betrieb", "min_leistung": 2.0, "limit": 5}
    )

    if data:
        print(f"\n   ⚡ Hochleistungs-WKA: {len(data)}")
        for i, marker in enumerate(data[:3], 1):
            print(f"\n   {i}. {marker['title']}")
            print(f"      Leistung: {marker['data']['leistung']} MW")
            print(f"      Ort: {marker['data']['ort']}")

    # Zusammenfassung
    print("\n" + "=" * 80)
    print("  ✅ ALLE TESTS ABGESCHLOSSEN")
    print("=" * 80)
    print("\n💡 Nächste Schritte:")
    print("   1. Frontend Map-Komponente erstellen (MapView.vue)")
    print("   2. Leaflet.js Integration")
    print("   3. Marker-Icons bereitstellen")
    print("\n🌐 Swagger UI: http://localhost:5000/docs")
    print("📚 Dokumentation: docs/IMMI_API_DOCUMENTATION.md")
    print()


if __name__ == "__main__":
    main()
