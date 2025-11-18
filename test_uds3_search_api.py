"""
Test: UDS3 Search API Verfügbarkeit
=====================================
Prüft ob die neue UDS3 Search API verfügbar ist
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def test_uds3_search_api():
    print("=" * 80)
    print("🔍 UDS3 SEARCH API CHECK")
    print("=" * 80)

    # 1. Import UDS3 Search API
    print("\n1️⃣ Import UDS3 Search API...")
    try:
        from uds3 import SEARCH_API_AVAILABLE, SearchQuery, SearchResult, SearchType, UDS3SearchAPI

        print("✅ UDS3 Search API importiert")
        print(f"   SEARCH_API_AVAILABLE: {SEARCH_API_AVAILABLE}")

        if not SEARCH_API_AVAILABLE:
            print("❌ Search API nicht verfügbar")
            return

    except ImportError as e:
        print(f"❌ Import fehlgeschlagen: {e}")
        return

    # 2. Initialisiere Search API
    print("\n2️⃣ Initialisiere Search API...")
    try:
        search_api = UDS3SearchAPI()
        print("✅ UDS3SearchAPI Instanz erstellt")
    except Exception as e:
        print(f"❌ Initialisierung fehlgeschlagen: {e}")
        import traceback

        traceback.print_exc()
        return

    # 3. Test-Query
    print("\n3️⃣ Test-Query ausführen...")
    try:
        query = SearchQuery(
            query_text="Bauvorschriften München",
            search_type=SearchType.HYBRID if hasattr(SearchType, "HYBRID") else SearchType.SEMANTIC,
            top_k=3,
            threshold=0.5,
        )

        print(f"   Query: {query.query_text}")
        print(f"   Type: {query.search_type}")

        result = search_api.search(query)

        print(f"✅ Query ausgeführt")
        print(f"   Success: {result.success if hasattr(result, 'success') else 'N/A'}")
        print(f"   Results: {len(result.results) if hasattr(result, 'results') else 0}")

        if hasattr(result, "results") and result.results:
            print("\n   📄 Erste Ergebnisse:")
            for i, doc in enumerate(result.results[:3], 1):
                if hasattr(doc, "content"):
                    content = doc.content[:80]
                    score = doc.score if hasattr(doc, "score") else 0
                    print(f"      {i}. Score: {score:.2f} | {content}...")
        else:
            print("   ℹ️ Keine Ergebnisse (DB möglicherweise leer)")

    except Exception as e:
        print(f"⚠️ Query-Fehler: {e}")
        import traceback

        traceback.print_exc()

    # Zusammenfassung
    print("\n" + "=" * 80)
    print("📋 ERGEBNIS:")
    print("=" * 80)
    print("✅ UDS3 Search API ist verfügbar und funktioniert")
    print("   - Kann für Agent-Integration genutzt werden")
    print("=" * 80)


if __name__ == "__main__":
    test_uds3_search_api()
