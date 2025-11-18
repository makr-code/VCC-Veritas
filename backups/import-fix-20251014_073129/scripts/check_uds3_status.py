#!/usr/bin/env python3
"""
UDS3 Status Check Script

Prüft welche UDS3 Backends aktiv sind und zeigt Statistiken.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Add UDS3 to path (lokales Modul in c:\VCC\uds3)
uds3_path = Path("c:/VCC/uds3")
if uds3_path.exists() and str(uds3_path) not in sys.path:
    sys.path.insert(0, str(uds3_path))

try:
    from uds3.uds3_core import UnifiedDatabaseStrategy, get_optimized_unified_strategy

    UDS3_AVAILABLE = True
except ImportError as e:
    UDS3_AVAILABLE = False
    print("⚠️  UDS3 nicht gefunden!")
    print(f"   Fehler: {e}")
    print("   Stelle sicher dass c:\\VCC\\uds3 existiert")
    sys.exit(1)


def print_separator(char="=", length=60):
    """Print separator line"""
    print(char * length)


def check_uds3_status():
    """Check UDS3 backend status"""

    print_separator()
    print("🔍 UDS3 Status Report")
    print_separator()

    try:
        # Initialize UDS3 Strategy (Singleton)
        strategy = get_optimized_unified_strategy()

        # Backend Status
        print("\n📊 Backend Status:")
        has_vector = strategy.vector_backend is not None
        has_graph = strategy.graph_backend is not None
        has_relational = strategy.relational_backend is not None
        has_file = hasattr(strategy, "file_backend") and strategy.file_backend is not None

        print(f"  Vector Backend (ChromaDB):    {'✅ Aktiv' if has_vector else '❌ Inaktiv'}")
        print(f"  Metadata Backend (PostgreSQL): {'✅ Aktiv' if has_relational else '❌ Inaktiv'}")
        print(f"  Graph Backend (Neo4j):         {'✅ Aktiv' if has_graph else '❌ Inaktiv'}")
        print(f"  File Backend:                  {'✅ Aktiv' if has_file else '❌ Inaktiv'}")

        # Document Statistics (if available)
        print("\n📚 Dokument-Statistiken:")
        try:
            # Try to get document count from relational backend
            if has_relational:
                # Check if backend has count method
                if hasattr(strategy.relational_backend, "count_documents"):
                    count = strategy.relational_backend.count_documents()
                    print(f"  Gesamtanzahl Dokumente: {count:,}")
                else:
                    print(f"  Gesamtanzahl Dokumente: N/A (count_documents() nicht verfügbar)")
            else:
                print(f"  Gesamtanzahl Dokumente: N/A (kein Backend verfügbar)")
        except Exception as e:
            print(f"  Gesamtanzahl Dokumente: Fehler beim Abrufen ({e})")

        # Capabilities
        print("\n🔧 Verfügbare Capabilities:")
        capabilities = []
        if has_vector:
            capabilities.append("  ✅ Vector Search (Semantische Ähnlichkeit)")
        if has_relational:
            capabilities.append("  ✅ Keyword Search (Exakte Suche)")
        if has_graph:
            capabilities.append("  ✅ Graph Query (Beziehungen)")
        if has_file:
            capabilities.append("  ✅ File Storage (Dateiverwaltung)")

        if capabilities:
            for cap in capabilities:
                print(cap)
        else:
            print("  ⚠️  Keine Backends aktiv!")

        # Recommendations
        print("\n💡 Empfehlungen:")
        if not has_vector:
            print("  ⚠️  ChromaDB nicht verfügbar - Semantische Suche fehlt!")
            print("     → Konfiguriere ChromaDB in database/config.py")

        if not has_relational:
            print("  ⚠️  PostgreSQL nicht verfügbar - Keyword-Suche fehlt!")
            print("     → Konfiguriere PostgreSQL in database/config.py")

        if not has_graph:
            print("  ℹ️  Neo4j nicht verfügbar (optional)")
            print("     → Konfiguriere Neo4j für Graph-Queries in database/config.py")

        if has_vector and has_relational:
            print("  ✅ Alle essentiellen Backends aktiv!")
            print("  → Bereit für UDS3 Hybrid Search Implementation")

        print_separator()

        # Return status
        return {"vector": has_vector, "metadata": has_relational, "graph": has_graph, "file": has_file, "total_docs": "N/A"}

    except Exception as e:
        print(f"\n❌ Fehler beim UDS3 Status Check:")
        print(f"   {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        print_separator()
        return None


def main():
    """Main function"""
    status = check_uds3_status()

    if status:
        # Exit code based on status
        if status["vector"] and status["metadata"]:
            print("\n✅ Status: READY für UDS3 Hybrid Search")
            sys.exit(0)
        elif status["vector"] or status["metadata"]:
            print("\n⚠️  Status: PARTIAL (mindestens 1 Backend fehlt)")
            sys.exit(1)
        else:
            print("\n❌ Status: NOT READY (keine Backends aktiv)")
            sys.exit(2)
    else:
        print("\n❌ Status: ERROR (UDS3 Check fehlgeschlagen)")
        sys.exit(3)


if __name__ == "__main__":
    main()
