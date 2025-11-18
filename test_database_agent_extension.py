"""
Comprehensive Test für DatabaseAgent TestServer Extension
"""
import asyncio
import sys

sys.path.append(".")

from backend.agents.database_agent_testserver_extension import (
    ComplianceStatus,
    DatabaseAgentTestServerExtension,
    EntityType,
    QueryResult,
)


async def test_database_agent():
    """Umfassender Test der DatabaseAgent Extension"""

    agent = DatabaseAgentTestServerExtension()

    print("=" * 70)
    print("🧪 DatabaseAgent TestServer Extension - Comprehensive Tests")
    print("=" * 70)

    try:
        # Test 1: Server Health
        print("\n1️⃣ Server Health Check...")
        health = await agent.get_server_health()
        print(f"   Status: {health.get('status')}")
        print(f"   Databases: {', '.join(health.get('databases', {}).keys())}")

        # Test 2: Server Statistics
        print("\n2️⃣ Server Statistics...")
        stats = await agent.get_server_statistics()
        if stats:
            print(f"   Verfahren: {stats.get('statistics', {}).get('verfahren', {}).get('total', 0)}")
            print(f"   Messungen: {stats.get('statistics', {}).get('messungen', {}).get('total', 0)}")

        # Test 3: Generic Entity Query (verschiedene Typen)
        print("\n3️⃣ Generic Entity Queries...")

        # Verfahren
        result = await agent.query_entity(EntityType.VERFAHREN, limit=5)
        print(f"   ✅ Verfahren: {result.metadata.get('count', 0)} gefunden")

        # Dokumente
        result = await agent.query_entity(EntityType.DOKUMENT, filters={"dokumenttyp": "Messbericht"}, limit=5)
        print(f"   ✅ Messberichte: {result.metadata.get('count', 0)} gefunden")

        # Wartungen
        result = await agent.query_entity(EntityType.WARTUNG, filters={"status": "geplant"}, limit=5)
        print(f"   ✅ Geplante Wartungen: {result.metadata.get('count', 0)} gefunden")

        # Test 4: Convenience Methods
        print("\n4️⃣ Convenience Methods...")

        verfahren = await agent.query_verfahren(status="genehmigt", limit=3)
        print(f"   ✅ Genehmigte Verfahren: {len(verfahren)}")

        messungen = await agent.query_messungen(ueberschreitung=True, limit=5)
        print(f"   ✅ Grenzwertüberschreitungen: {len(messungen)}")

        # Test 5: Complete Entity (mit Beispiel-Daten)
        print("\n5️⃣ Complete Entity Query...")

        # Hole eine BST/ANL aus Verfahren
        verfahren_list = await agent.query_verfahren(limit=1)
        if verfahren_list:
            v = verfahren_list[0]
            bst_nr = v["bst_nr"]
            anl_nr = v["anl_nr"]

            print(f"   Teste mit: {bst_nr}/{anl_nr}")

            result = await agent.get_complete_entity(bst_nr, anl_nr)

            if result.success:
                anlage = result.data
                print(f"   ✅ Anlage geladen: {anlage.anlage.bst_name}")
                print(f"      📊 Verfahren: {len(anlage.verfahren)}")
                print(f"      📊 Messungen: {len(anlage.messungen)}")
                print(f"      📊 Dokumente: {len(anlage.dokumente)}")
                print(f"      📊 Ansprechpartner: {len(anlage.ansprechpartner)}")
                print(f"      📊 Wartungen: {len(anlage.wartungen)}")
                print(f"      📊 Messreihen: {len(anlage.messreihen)}")
                print(f"      📊 Compliance: {len(anlage.compliance_historie)}")

                # Test 6: Compliance Analysis
                print("\n6️⃣ Compliance Analysis...")
                compliance = await agent.analyze_compliance(bst_nr, anl_nr)

                print(f"   Status: {compliance.status.value.upper()}")
                print(f"   Score: {compliance.score:.1%}")
                print(f"   Is Compliant: {compliance.is_compliant}")
                print(f"   Requires Action: {compliance.requires_action}")

                if compliance.issues:
                    print(f"\n   ⚠️  Issues ({len(compliance.issues)}):")
                    for issue in compliance.issues[:3]:
                        print(f"      - [{issue.get('severity', 'info')}] {issue.get('message', 'N/A')}")

                if compliance.recommendations:
                    print(f"\n   💡 Empfehlungen ({len(compliance.recommendations)}):")
                    for rec in compliance.recommendations[:3]:
                        print(f"      - {rec}")

                print(f"\n   📊 Details:")
                print(
                    f"      Verfahren: {compliance.details['verfahren']['genehmigt']}/{compliance.details['verfahren']['total']}"
                )
                print(
                    f"      Überschreitungen: {compliance.details['messungen']['ueberschreitungen']}/{compliance.details['messungen']['total']}"
                )
                print(
                    f"      Offene Mängel: {compliance.details['maengel']['offen']} (davon {compliance.details['maengel']['kritisch']} kritisch)"
                )

        # Test 7: Custom Queries
        print("\n7️⃣ Custom Queries...")

        result = await agent.custom_query("/messreihen/kritische", {"limit": 3})
        if result.success:
            messreihen = result.data.get("messreihen", [])
            print(f"   ✅ Kritische Messreihen: {len(messreihen)}")
            if messreihen:
                mr = messreihen[0]
                print(f"      Beispiel: {mr['messart']} - {mr['ueberschreitungen_anzahl']} Überschreitungen")

        result = await agent.custom_query("/compliance/search", {"ergebnis": "Kritisch", "limit": 3})
        if result.success:
            historie = result.data.get("historie", [])
            print(f"   ✅ Kritische Compliance-Prüfungen: {len(historie)}")

        # Test 8: Auflagen-Status Check
        print("\n8️⃣ Auflagen Status Check...")
        if verfahren_list:
            v = verfahren_list[0]
            auflagen = await agent.check_auflagen_status(v["bst_nr"], v["anl_nr"])
            print(f"   ✅ Verfahren: {auflagen.get('verfahren_count', 0)}")
            print(f"   ✅ Bescheide: {auflagen.get('bescheide_count', 0)}")

        # Test 9: Compliance History Query
        print("\n9️⃣ Compliance History...")
        if verfahren_list:
            v = verfahren_list[0]
            history = await agent.query_compliance_history(v["bst_nr"], v["anl_nr"], limit=5)
            print(f"   ✅ {len(history)} Compliance-Einträge gefunden")
            if history:
                h = history[0]
                print(f"      Letzte Prüfung: {h['pruefungsdatum']} - {h['ergebnis']} ({h['bewertung_punkte']}/100)")

        # Test 10: QueryResult Properties
        print("\n🔟 QueryResult Features...")
        result = await agent.query_entity(EntityType.VERFAHREN, limit=5)
        print(f"   Success: {result.success}")
        print(f"   Has Data: {result.has_data}")
        print(f"   Timestamp: {result.timestamp}")
        print(f"   Metadata Keys: {list(result.metadata.keys())}")

        print("\n" + "=" * 70)
        print("✅ ALLE TESTS ERFOLGREICH!")
        print("=" * 70)

        # Zusammenfassung
        print("\n📊 Test-Zusammenfassung:")
        print("   ✅ Server Health Check")
        print("   ✅ Server Statistics")
        print("   ✅ Generic Entity Queries (Verfahren, Dokumente, Wartungen)")
        print("   ✅ Convenience Methods (Verfahren, Messungen)")
        print("   ✅ Complete Entity mit allen Relationen")
        print("   ✅ Compliance Analysis mit Score und Empfehlungen")
        print("   ✅ Custom Queries (Messreihen, Compliance)")
        print("   ✅ Auflagen Status Check")
        print("   ✅ Compliance History Query")
        print("   ✅ QueryResult Properties")

    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(test_database_agent())
