"""
Test-Script für Agent <-> TestServer Integration
=================================================

Testet die Kommunikation zwischen VERITAS Agents und dem
Immissionsschutz Test-Server.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.test_server_client import TestServerClient, TestServerClientContext


async def test_basic_connectivity():
    """Test 1: Basis-Konnektivität"""
    print("=" * 70)
    print("Test 1: Basis-Konnektivität")
    print("=" * 70)
    print()

    async with TestServerClientContext() as client:
        # Health Check
        health = await client.health_check()
        print(f"✅ Server Status: {health.get('status')}")

        # Datenbanken
        databases = await client.get_databases()
        print(f"✅ Verfügbare Datenbanken: {len(databases)}")
        for db in databases:
            print(f"   - {db['name']}: {db['description']} ({db['type']})")

        # Statistik
        stats = await client.get_statistics()
        if stats and "statistics" in stats:
            s = stats["statistics"]
            print("\n📊 Statistik:")
            print(f"   Verfahren: {s['verfahren']['total']} (Genehmigt: {s['verfahren']['genehmigt']})")
            print(f"   Messungen: {s['messungen']['total']} (Überschreitungen: {s['messungen']['ueberschreitungen']})")
            print(f"   Mängel: {s['maengel']['total']} (Offen: {s['maengel']['offen']})")

        print()


async def test_anlagen_search():
    """Test 2: Anlagen-Suche"""
    print("=" * 70)
    print("Test 2: Anlagen-Suche")
    print("=" * 70)
    print()

    async with TestServerClientContext() as client:
        # BImSchG Anlagen
        result = await client.search_anlagen(db="bimschg", limit=5)
        if result and "results" in result:
            print(f"✅ BImSchG Anlagen gefunden: {result['count']}")
            for anlage in result["results"][:3]:
                print(f"   - {anlage.get('bst_name', 'N / A')} ({anlage.get('ort', 'N / A')})")

        # WKA
        result = await client.search_anlagen(db="wka", ort="Oranienburg", limit=5)
        if result and "results" in result:
            print(f"\n✅ WKA in Oranienburg: {result['count']}")
            for anlage in result["results"][:3]:
                print(f"   - {anlage.get('anl_bez', 'N / A')} (Leistung: {anlage.get('leistung', 'N / A')} MW)")

        print()


async def test_verfahren_search():
    """Test 3: Verfahren-Suche"""
    print("=" * 70)
    print("Test 3: Genehmigungsverfahren")
    print("=" * 70)
    print()

    async with TestServerClientContext() as client:
        # Genehmigte Verfahren
        verfahren = await client.search_verfahren(status="genehmigt", limit=5)
        print(f"✅ Genehmigte Verfahren: {len(verfahren)}")

        if verfahren:
            v = verfahren[0]
            print(f"\n   Beispiel: {v.get('verfahren_id')}")
            print(f"   Art: {v.get('verfahrensart')}")
            print(f"   Anlage: {v.get('bst_nr')}/{v.get('anl_nr')}")
            print(f"   Behörde: {v.get('behoerde')}")
            print(f"   Status: {v.get('status')}")

            # Details abrufen
            details = await client.get_verfahren(v["verfahren_id"])
            if details and "bescheide" in details:
                print(f"\n   Bescheide: {len(details['bescheide'])}")
                print(f"   Auflagen: {len(details['auflagen'])}")

        # In Bearbeitung
        in_bearbeitung = await client.search_verfahren(status="in_bearbeitung", limit=3)
        print(f"\n✅ Verfahren in Bearbeitung: {len(in_bearbeitung)}")

        print()


async def test_messungen_analysis():
    """Test 4: Messungen-Analyse"""
    print("=" * 70)
    print("Test 4: Messungen-Analyse")
    print("=" * 70)
    print()

    async with TestServerClientContext() as client:
        # Alle Messungen
        alle_messungen = await client.search_messungen(limit=10)
        print(f"✅ Messungen gefunden: {len(alle_messungen)}")

        # Grenzwertüberschreitungen
        ueberschreitungen = await client.get_grenzwertueberschreitungen(limit=10)
        print(f"⚠️  Grenzwertüberschreitungen: {len(ueberschreitungen)}")

        if ueberschreitungen:
            m = ueberschreitungen[0]
            print("\n   Beispiel-Überschreitung:")
            print(f"   Anlage: {m.get('bst_nr')}/{m.get('anl_nr')}")
            print(f"   Messart: {m.get('messart')}")
            print(f"   Messwert: {m.get('messwert')} {m.get('einheit')}")
            print(f"   Grenzwert: {m.get('grenzwert')} {m.get('einheit')}")
            print(f"   Datum: {m.get('messdatum')} {m.get('messzeit')}")

        # Lärm-Messungen
        laerm = await client.search_messungen(messart="Lärm", limit=5)
        print(f"\n✅ Lärm-Messungen: {len(laerm)}")

        print()


async def test_ueberwachung_maengel():
    """Test 5: Überwachung & Mängel"""
    print("=" * 70)
    print("Test 5: Überwachung & Mängel")
    print("=" * 70)
    print()

    async with TestServerClientContext() as client:
        # Durchgeführte Überwachungen
        ueberwachung = await client.search_ueberwachung(status="durchgeführt", limit=5)
        print(f"✅ Durchgeführte Überwachungen: {len(ueberwachung)}")

        # Geplante Überwachungen
        geplant = await client.search_ueberwachung(status="geplant", limit=5)
        print(f"📅 Geplante Überwachungen: {len(geplant)}")

        # Offene Mängel
        offene_maengel = await client.get_offene_maengel()
        print(f"\n⚠️  Offene Mängel: {len(offene_maengel)}")

        # Kritische Mängel
        kritisch = await client.search_maengel(status="offen", schweregrad="kritisch")
        print(f"🚨 Kritische offene Mängel: {len(kritisch)}")

        if kritisch:
            m = kritisch[0]
            print("\n   Beispiel:")
            print(f"   Anlage: {m.get('bst_nr')}/{m.get('anl_nr')}")
            print(f"   Beschreibung: {m.get('beschreibung')}")
            print(f"   Schweregrad: {m.get('schweregrad')}")
            print(f"   Festgestellt: {m.get('festgestellt_datum')}")

        print()


async def test_cross_database_query():
    """Test 6: Cross-Database Query"""
    print("=" * 70)
    print("Test 6: Cross-Database Query (Vollständige Anlagen-Daten)")
    print("=" * 70)
    print()

    async with TestServerClientContext() as client:
        # Hole eine Anlage aus Verfahren
        verfahren = await client.search_verfahren(limit=1)
        if not verfahren:
            print("❌ Keine Verfahren gefunden")
            return

        v = verfahren[0]
        bst_nr = v["bst_nr"]
        anl_nr = v["anl_nr"]

        print(f"🔍 Analysiere Anlage: {bst_nr}/{anl_nr}")
        print()

        # Vollständige Daten
        anlage = await client.get_anlage_complete(bst_nr, anl_nr)

        if anlage:
            print("✅ Cross-DB Query erfolgreich!")
            print()
            print("📋 Basis-Daten:")
            print(f"   BST-Nr: {anlage.anlage.bst_nr}")
            print(f"   Name: {anlage.anlage.bst_name or 'N / A'}")
            print(f"   Bezeichnung: {anlage.anlage.anl_bez or 'N / A'}")
            print(f"   Ort: {anlage.anlage.ort or 'N / A'}")

            print("\n📊 Statistik:")
            print(f"   Verfahren: {anlage.statistik.get('verfahren_count', 0)}")
            print(f"   Bescheide: {anlage.statistik.get('bescheide_count', 0)}")
            print(f"   Messungen: {anlage.statistik.get('messungen_count', 0)}")
            print(f"   Überschreitungen: {anlage.statistik.get('messungen_ueberschreitungen', 0)}")
            print(f"   Überwachungen: {anlage.statistik.get('ueberwachungen_count', 0)}")
            print(f"   Mängel: {anlage.statistik.get('maengel_count', 0)}")
            print(f"   Mängel (offen): {anlage.statistik.get('maengel_offen', 0)}")

            # Details
            if anlage.verfahren:
                print("\n📝 Verfahren:")
                for v in anlage.verfahren[:2]:
                    print(f"   - {v.verfahrensart} ({v.status})")

            if anlage.messungen:
                print("\n📏 Messungen (Beispiele):")
                for m in anlage.messungen[:3]:
                    u = "⚠️ " if m.ueberschreitung else "✅"
                    print(f"   {u} {m.messart}: {m.messwert} {m.einheit} (Datum: {m.messdatum})")

            if anlage.maengel:
                print("\n⚠️  Mängel:")
                for m in anlage.maengel[:3]:
                    print(f"   - {m.schweregrad}: {m.beschreibung} ({m.status})")

        else:
            print("⚠️  Anlage nicht in Referenz-Datenbanken gefunden")
            print("   (Nur Verfahren/Messungen/Mängel verfügbar)")

        print()


async def test_kritische_anlagen():
    """Test 7: Kritische Anlagen identifizieren"""
    print("=" * 70)
    print("Test 7: Kritische Anlagen (Use Case Szenario)")
    print("=" * 70)
    print()

    async with TestServerClientContext() as client:
        print("🔍 Suche Anlagen mit kritischen Problemen...")
        print()

        kritische = await client.get_kritische_anlagen()

        print(f"🚨 Gefunden: {len(kritische)} kritische Anlagen")
        print()

        for i, item in enumerate(kritische[:3], 1):
            anlage_data = item["anlage"]
            print(f"{i}. {anlage_data.get('bst_name', 'N / A')}")
            print(f"   Ort: {anlage_data.get('ort', 'N / A')}")
            print(f"   Kritische Mängel: {item['kritische_maengel']}")
            print(f"   Grenzwertüberschreitungen: {item['ueberschreitungen']}")
            print()

        if kritische:
            print("💡 Diese Anlagen benötigen prioritäre Aufmerksamkeit!")

        print()


async def main():
    """Führt alle Tests aus"""
    print("\n")
    print("🚀 VERITAS Agent <-> TestServer Integration Tests")
    print("=" * 70)
    print()

    tests = [
        ("Basis-Konnektivität", test_basic_connectivity),
        ("Anlagen-Suche", test_anlagen_search),
        ("Genehmigungsverfahren", test_verfahren_search),
        ("Messungen-Analyse", test_messungen_analysis),
        ("Überwachung & Mängel", test_ueberwachung_maengel),
        ("Cross-Database Query", test_cross_database_query),
        ("Kritische Anlagen", test_kritische_anlagen),
    ]

    results = []

    for name, test_func in tests:
        try:
            await test_func()
            results.append((name, "✅ PASS"))
        except Exception as e:
            print(f"❌ Test fehlgeschlagen: {e}")
            results.append((name, "❌ FAIL"))
            import traceback

            traceback.print_exc()

        await asyncio.sleep(0.5)  # Kurze Pause zwischen Tests

    # Ergebnis
    print("=" * 70)
    print("📊 Test-Ergebnisse")
    print("=" * 70)
    print()

    for name, status in results:
        print(f"{status} {name}")

    passed = len([r for r in results if "PASS" in r[1]])
    total = len(results)

    print()
    print("=" * 70)
    print(f"✅ {passed}/{total} Tests bestanden")
    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
