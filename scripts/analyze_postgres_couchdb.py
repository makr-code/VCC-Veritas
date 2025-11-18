#!/usr/bin/env python3
"""
PostgreSQL & CouchDB Backend Analysis

Untersucht die PostgreSQL und CouchDB Backends im UDS3 System:
- PostgreSQL: Relational Backend (Keyword Search, SQL Queries)
- CouchDB: File Backend (Document Storage)

Run: python scripts/analyze_postgres_couchdb.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / "uds3"))


async def analyze_postgresql():
    """Analysiere PostgreSQL Backend"""
    print("\n" + "=" * 80)
    print("POSTGRESQL BACKEND ANALYSIS")
    print("=" * 80)

    try:
        from uds3.uds3_core import get_optimized_unified_strategy

        strategy = get_optimized_unified_strategy()

        if not hasattr(strategy, "relational_backend") or strategy.relational_backend is None:
            print("❌ PostgreSQL Backend nicht verfügbar")
            return

        backend = strategy.relational_backend

        # 1. Backend Info
        print("\n📊 Backend Information:")
        print(f"   Type: {type(backend).__name__}")
        print(f"   Available: ✅")

        # 2. Available Methods
        print("\n🔧 Verfügbare Methoden:")
        methods = [m for m in dir(backend) if not m.startswith("_")]
        for method in sorted(methods):
            print(f"   - {method}()")

        # 3. Check for SQL Query API
        print("\n🔍 SQL Query API Check:")
        if hasattr(backend, "execute_sql"):
            print("   ✅ execute_sql() verfügbar")
            print("   → Keyword Search möglich")
        else:
            print("   ❌ execute_sql() NICHT verfügbar")
            print("   → Keyword Search NICHT möglich")
            print("   → Nur get_document() verfügbar")

        # 4. Test get_document_count()
        print("\n📄 Document Count Test:")
        if hasattr(backend, "get_document_count"):
            try:
                count = backend.get_document_count()
                print(f"   ✅ Dokumente in PostgreSQL: {count}")
            except Exception as e:
                print(f"   ⚠️ Fehler: {e}")
        else:
            print("   ⚠️ get_document_count() nicht verfügbar")

        # 5. Connection Info
        print("\n🔗 Connection Info:")
        if hasattr(backend, "host"):
            print(f"   Host: {getattr(backend, 'host', 'N/A')}")
            print(f"   Port: {getattr(backend, 'port', 'N/A')}")
            print(f"   Database: {getattr(backend, 'database', 'N/A')}")

        print("\n✅ PostgreSQL Backend Analysis complete")
        return backend

    except Exception as e:
        print(f"\n❌ PostgreSQL Analysis failed: {e}")
        import traceback

        traceback.print_exc()
        return None


async def analyze_couchdb():
    """Analysiere CouchDB Backend"""
    print("\n" + "=" * 80)
    print("COUCHDB BACKEND ANALYSIS")
    print("=" * 80)

    try:
        from uds3.uds3_core import get_optimized_unified_strategy

        strategy = get_optimized_unified_strategy()

        if not hasattr(strategy, "file_backend") or strategy.file_backend is None:
            print("❌ CouchDB Backend nicht verfügbar")
            return

        backend = strategy.file_backend

        # 1. Backend Info
        print("\n📊 Backend Information:")
        print(f"   Type: {type(backend).__name__}")
        print(f"   Available: ✅")

        # 2. Available Methods
        print("\n🔧 Verfügbare Methoden:")
        methods = [m for m in dir(backend) if not m.startswith("_")]
        for method in sorted(methods):
            print(f"   - {method}()")

        # 3. Check for Document Storage API
        print("\n🔍 Document Storage API Check:")
        if hasattr(backend, "save_file"):
            print("   ✅ save_file() verfügbar")
        if hasattr(backend, "get_file"):
            print("   ✅ get_file() verfügbar")
        if hasattr(backend, "delete_file"):
            print("   ✅ delete_file() verfügbar")
        if hasattr(backend, "list_files"):
            print("   ✅ list_files() verfügbar")

        # 4. Connection Info
        print("\n🔗 Connection Info:")
        if hasattr(backend, "url"):
            print(f"   URL: {getattr(backend, 'url', 'N/A')}")
        if hasattr(backend, "database"):
            print(f"   Database: {getattr(backend, 'database', 'N/A')}")

        # 5. Test file count
        print("\n📄 File Count Test:")
        if hasattr(backend, "list_files"):
            try:
                files = backend.list_files()
                if isinstance(files, list):
                    print(f"   ✅ Dateien in CouchDB: {len(files)}")
                    if files:
                        print(f"   📝 Beispiele:")
                        for f in files[:3]:
                            print(f"      - {f}")
                else:
                    print(f"   ⚠️ Unerwartetes Format: {type(files)}")
            except Exception as e:
                print(f"   ⚠️ Fehler: {e}")

        print("\n✅ CouchDB Backend Analysis complete")
        return backend

    except Exception as e:
        print(f"\n❌ CouchDB Analysis failed: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_postgresql_keyword_search():
    """Test PostgreSQL Keyword Search (wenn execute_sql verfügbar)"""
    print("\n" + "=" * 80)
    print("POSTGRESQL KEYWORD SEARCH TEST")
    print("=" * 80)

    try:
        from uds3.uds3_core import get_optimized_unified_strategy
        from uds3.uds3_search_api import UDS3SearchAPI

        strategy = get_optimized_unified_strategy()
        search_api = UDS3SearchAPI(strategy)

        # Test Keyword Search
        query = "Photovoltaik"
        results = await search_api.keyword_search(query, top_k=5)

        print(f"\n📊 Query: '{query}'")
        print(f"✅ Found {len(results)} keyword search results")

        if results:
            for i, result in enumerate(results, 1):
                print(f"\n{i}. Score: {result.score:.3f}")
                print(f"   ID: {result.document_id}")
                print(f"   Content: {result.content[:100]}...")
        else:
            print("\n⚠️ No results (PostgreSQL execute_sql() API not available)")
            print("   → Keyword Search currently disabled")
            print("   → Request execute_sql() API from UDS3 team")

        return results

    except Exception as e:
        print(f"\n❌ Keyword Search Test failed: {e}")
        import traceback

        traceback.print_exc()
        return []


async def test_couchdb_file_storage():
    """Test CouchDB File Storage"""
    print("\n" + "=" * 80)
    print("COUCHDB FILE STORAGE TEST")
    print("=" * 80)

    try:
        from uds3.uds3_core import get_optimized_unified_strategy

        strategy = get_optimized_unified_strategy()

        if not hasattr(strategy, "file_backend") or strategy.file_backend is None:
            print("❌ CouchDB Backend nicht verfügbar")
            return

        backend = strategy.file_backend

        # Test 1: List Files
        print("\n📊 Test 1: List Files")
        if hasattr(backend, "list_files"):
            try:
                files = backend.list_files()
                print(f"   ✅ Found {len(files) if isinstance(files, list) else 'N/A'} files")
                if isinstance(files, list) and files:
                    print(f"   📝 First 5 files:")
                    for f in files[:5]:
                        print(f"      - {f}")
            except Exception as e:
                print(f"   ⚠️ Error: {e}")

        # Test 2: Get File (if any files exist)
        print("\n📊 Test 2: Get File (Example)")
        if hasattr(backend, "get_file"):
            print("   ℹ️ get_file() available but needs file_id")
            print("   ℹ️ Use: backend.get_file(file_id)")

        print("\n✅ CouchDB File Storage Test complete")

    except Exception as e:
        print(f"\n❌ CouchDB File Storage Test failed: {e}")
        import traceback

        traceback.print_exc()


async def integration_recommendations():
    """Empfehlungen für PostgreSQL & CouchDB Integration"""
    print("\n" + "=" * 80)
    print("INTEGRATION RECOMMENDATIONS")
    print("=" * 80)

    print("\n📊 PostgreSQL (Relational Backend):")
    print("   Current Status: ⏭️ Keyword Search disabled")
    print("   Reason: No execute_sql() API")
    print("")
    print("   ✅ Option 1: Request execute_sql() API from UDS3 team")
    print("      → UDS3SearchAPI.keyword_search() ready (waiting for API)")
    print("")
    print("   ✅ Option 2: Direct psycopg2 wrapper")
    print("      → Bypass UDS3, direct SQL queries")
    print("      → Cons: Breaks 3-layer architecture")
    print("")
    print("   ✅ Option 3: Use Neo4j CONTAINS for text search")
    print("      → Already working (1930 documents)")
    print("      → Good enough for production")
    print("")
    print("   📝 Recommendation: Option 3 (Use Neo4j) + Request Option 1 (Future)")

    print("\n📊 CouchDB (File Backend):")
    print("   Current Status: ✅ Active")
    print("   Use Case: Document/File storage (PDFs, etc.)")
    print("")
    print("   ✅ Integration Options:")
    print("      1. Upload PDF → CouchDB")
    print("      2. Extract text → PostgreSQL/Neo4j")
    print("      3. Generate embeddings → ChromaDB")
    print("")
    print("   📝 Recommendation: Use for file storage, not search")

    print("\n📊 Search API Strategy:")
    print("   ✅ Current: Vector (ChromaDB ⚠️) + Graph (Neo4j ✅)")
    print("   ⏭️ Future: + Keyword (PostgreSQL)")
    print("   📁 CouchDB: File storage only (not search)")

    print("\n✅ Recommendations complete")


async def main():
    """Run all analyses"""
    print("\n" + "=" * 80)
    print("POSTGRESQL & COUCHDB BACKEND ANALYSIS")
    print("=" * 80)

    # Analyze PostgreSQL
    postgres = await analyze_postgresql()

    # Analyze CouchDB
    couchdb = await analyze_couchdb()

    # Test PostgreSQL Keyword Search
    await test_postgresql_keyword_search()

    # Test CouchDB File Storage
    await test_couchdb_file_storage()

    # Integration Recommendations
    await integration_recommendations()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✅ PostgreSQL Backend: {'✅ Available' if postgres else '❌ Not available'}")
    if postgres:
        has_execute_sql = hasattr(postgres, "execute_sql")
        print(f"   - execute_sql() API: {'✅ Available' if has_execute_sql else '❌ Missing'}")
        print(f"   - Keyword Search: {'✅ Enabled' if has_execute_sql else '⏭️ Disabled'}")

    print(f"\n✅ CouchDB Backend: {'✅ Available' if couchdb else '❌ Not available'}")
    if couchdb:
        print(f"   - File Storage: ✅ Active")
        print(f"   - Use Case: Document/File storage")

    print("\n📝 Next Steps:")
    print("   1. Use Neo4j for text search (production-ready)")
    print("   2. Request execute_sql() API for PostgreSQL (future)")
    print("   3. Use CouchDB for file storage (not search)")
    print("   4. Fix ChromaDB Remote API (vector search)")
    print("")


if __name__ == "__main__":
    asyncio.run(main())
