import json

import requests

# Hole erstmal ein Beispiel-Verfahren um BST/ANL zu bekommen
resp = requests.get("http://localhost:5001/verfahren/search?limit=1")
verfahren = resp.json()[0]
bst_nr = verfahren["bst_nr"]
anl_nr = verfahren["anl_nr"]

print(f"🔍 Teste erweiterte Anlage-Abfrage für: {bst_nr}/{anl_nr}")
print("=" * 60)

resp = requests.get(f"http://localhost:5001/anlage-extended/{bst_nr}/{anl_nr}")

if resp.status_code == 200:
    data = resp.json()

    print("\n✅ Erfolgreich abgerufen!\n")

    print(f"📍 Anlage: {data['anlage']['bst_name']} ({data['anlage']['ort']})")
    print(f"   BST-Nr: {data['anlage']['bst_nr']}")
    print(f"   Anl-Nr: {data['anlage']['anl_nr']}")

    print(f"\n📊 Statistik:")
    stats = data["statistik"]
    print(f"   Verfahren: {stats['verfahren_count']} (davon {stats['verfahren_genehmigt']} genehmigt)")
    print(f"   Messungen: {stats['messungen_count']} (davon {stats['messungen_ueberschreitungen']} Überschreitungen)")
    print(f"   Überwachungen: {stats['ueberwachungen_count']}")
    print(f"   Mängel: {stats['maengel_count']} (davon {stats['maengel_offen']} offen, {stats['maengel_kritisch']} kritisch)")
    print(f"   📁 Dokumente: {stats['dokumente_count']}")
    print(f"   👤 Ansprechpartner: {stats['ansprechpartner_count']}")
    print(f"   🔧 Wartungen: {stats['wartungen_count']} (davon {stats['wartungen_geplant']} geplant)")
    print(f"   📈 Messreihen: {stats['messreihen_count']} (davon {stats['messreihen_kritisch']} kritisch)")
    print(f"   📋 Compliance: {stats['compliance_count']} (Letztes Ergebnis: {stats['compliance_letztes_ergebnis']})")

    if data["ansprechpartner"]:
        print(f"\n👤 Ansprechpartner:")
        for ap in data["ansprechpartner"][:2]:
            print(f"   - {ap['name']} ({ap['funktion']})")
            print(f"     Tel: {ap['telefon']}, Email: {ap['email']}")

    if data["messreihen"]:
        print(f"\n📈 Messreihen:")
        for mr in data["messreihen"][:3]:
            print(f"   - {mr['messart']}: {mr['anzahl_messungen']} Messungen")
            print(f"     Mittelwert: {mr['mittelwert']:.2f}, Max: {mr['maximalwert']:.2f}, Trend: {mr['trend']}")
            print(f"     Bewertung: {mr['bewertung']} ({mr['ueberschreitungen_anzahl']} Überschreitungen)")

    if data["compliance_historie"]:
        print(f"\n📋 Compliance-Historie:")
        for ch in data["compliance_historie"][:2]:
            print(f"   - {ch['pruefungsdatum']}: {ch['pruefungstyp']}")
            print(f"     Ergebnis: {ch['ergebnis']} (Bewertung: {ch['bewertung_punkte']}/100)")
            print(f"     {ch['feststellungen']}")

    if data["wartungen"]:
        print(f"\n🔧 Wartungen:")
        for w in data["wartungen"][:3]:
            print(f"   - {w['wartungsart']}: {w['status']}")
            print(f"     Geplant: {w['geplant_datum']}, Durchgeführt: {w['durchgefuehrt_datum'] or 'noch nicht'}")

    print("\n" + "=" * 60)
    print("✅ ERWEITERTE ANLAGE-ABFRAGE ERFOLGREICH!")
    print("=" * 60)

else:
    print(f"❌ Fehler {resp.status_code}: {resp.text}")
