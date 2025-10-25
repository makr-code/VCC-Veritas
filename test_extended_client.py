"""
Test für erweiterten TestServerClient
"""
import asyncio
import sys
sys.path.append('.')

from backend.agents.test_server_client import TestServerClient


async def test_extended_client():
    client = TestServerClient()
    
    print("="*70)
    print("🧪 Test: Erweiterte TestServerClient Methoden")
    print("="*70)
    
    try:
        # 1. Dokumente suchen
        print("\n1️⃣ Dokumente suchen...")
        dokumente = await client.search_dokumente(dokumenttyp="Messbericht", limit=3)
        print(f"   ✅ {len(dokumente)} Messberichte gefunden")
        if dokumente:
            print(f"   Beispiel: {dokumente[0]['titel']}")
        
        # 2. Ansprechpartner
        print("\n2️⃣ Ansprechpartner suchen...")
        ansprechpartner = await client.search_ansprechpartner(funktion="Betriebsleiter", limit=3)
        print(f"   ✅ {len(ansprechpartner)} Betriebsleiter gefunden")
        if ansprechpartner:
            ap = ansprechpartner[0]
            print(f"   Beispiel: {ap['name']} - {ap['email']}")
        
        # 3. Wartungen
        print("\n3️⃣ Wartungen suchen...")
        wartungen = await client.search_wartung(status="geplant", limit=5)
        print(f"   ✅ {len(wartungen)} geplante Wartungen gefunden")
        if wartungen:
            w = wartungen[0]
            print(f"   Beispiel: {w['wartungsart']} am {w['geplant_datum']}")
        
        # 4. Kritische Messreihen
        print("\n4️⃣ Kritische Messreihen...")
        messreihen = await client.get_kritische_messreihen(limit=3)
        print(f"   ✅ {len(messreihen)} kritische Messreihen gefunden")
        if messreihen:
            mr = messreihen[0]
            print(f"   Beispiel: {mr['messart']} - {mr['ueberschreitungen_anzahl']} Überschreitungen")
        
        # 5. Behörden-Kontakte
        print("\n5️⃣ Behörden-Kontakte...")
        behoerden = await client.search_behoerden(abteilung="Immissionsschutz", limit=3)
        print(f"   ✅ {len(behoerden)} Kontakte gefunden")
        if behoerden:
            bk = behoerden[0]
            print(f"   Beispiel: {bk['sachbearbeiter']} ({bk['behoerde']})")
        
        # 6. Compliance-Historie
        print("\n6️⃣ Compliance-Historie...")
        compliance = await client.search_compliance(ergebnis="Kritisch", limit=3)
        print(f"   ✅ {len(compliance)} kritische Prüfungen gefunden")
        if compliance:
            ch = compliance[0]
            print(f"   Beispiel: {ch['pruefungstyp']} am {ch['pruefungsdatum']} - {ch['bewertung_punkte']}/100")
        
        # 7. ERWEITERTE ANLAGE
        print("\n7️⃣ Erweiterte Anlage-Abfrage...")
        
        # Hole BST/ANL aus einem Verfahren
        verfahren = await client.search_verfahren(limit=1)
        if verfahren:
            v = verfahren[0]
            bst_nr = v['bst_nr']
            anl_nr = v['anl_nr']
            
            print(f"   Lade Anlage: {bst_nr}/{anl_nr}")
            
            anlage_ext = await client.get_anlage_extended(bst_nr, anl_nr)
            
            if anlage_ext:
                print(f"   ✅ Erweiterte Daten geladen!")
                print(f"      Anlage: {anlage_ext.anlage.bst_name}")
                print(f"      Verfahren: {len(anlage_ext.verfahren)}")
                print(f"      Messungen: {len(anlage_ext.messungen)}")
                print(f"      📁 Dokumente: {len(anlage_ext.dokumente)}")
                print(f"      👤 Ansprechpartner: {len(anlage_ext.ansprechpartner)}")
                print(f"      🔧 Wartungen: {len(anlage_ext.wartungen)}")
                print(f"      📈 Messreihen: {len(anlage_ext.messreihen)}")
                print(f"      📋 Compliance: {len(anlage_ext.compliance_historie)}")
                
                print(f"\n   📊 Statistik:")
                stats = anlage_ext.statistik
                print(f"      Wartungen geplant: {stats.get('wartungen_geplant', 0)}")
                print(f"      Messreihen kritisch: {stats.get('messreihen_kritisch', 0)}")
                print(f"      Compliance Status: {stats.get('compliance_letztes_ergebnis', 'N/A')}")
        
        print("\n" + "="*70)
        print("✅ ALLE TESTS ERFOLGREICH!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_extended_client())
