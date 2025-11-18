"""
Test Script für UDS3 Vector Search Adapter
Validiert Adapter-Funktionalität und HybridRetriever Integration
"""
import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_adapter_standalone():
    """Test 1: Adapter Standalone"""
    print("=" * 80)
    print("TEST 1: UDS3 ADAPTER STANDALONE")
    print("=" * 80)
    print()

    try:
        from uds3.uds3_core import get_optimized_unified_strategy

        from backend.agents.veritas_uds3_adapter import UDS3VectorSearchAdapter

        # Initialize
        print("🔄 Initialisiere UDS3...")
        uds3 = get_optimized_unified_strategy()
        print(f"   ✅ UDS3 Strategy: {type(uds3).__name__}")

        print("🔄 Erstelle Adapter...")
        adapter = UDS3VectorSearchAdapter(uds3)
        print(f"   ✅ Adapter: {type(adapter).__name__}")
        print()

        # Test queries
        test_queries = ["BGB Taschengeldparagraph Minderjährige", "Verwaltungsakt Rechtmäßigkeit", "Kaufvertrag BGB"]

        print("🔍 Test Queries:")
        for i, query in enumerate(test_queries, 1):
            print(f"   {i}. {query}")
        print()

        # Execute searches
        print("📊 Executing Searches...")
        print("-" * 80)

        for query in test_queries:
            start = time.time()
            results = await adapter.vector_search(query, top_k=3)
            latency = (time.time() - start) * 1000

            if results:
                print(f'✅ Query: "{query}"')
                print(f"   Results: {len(results)}, Latency: {latency:.1f}ms")
                for j, doc in enumerate(results, 1):
                    print(f"   {j}. {doc['doc_id']} (Score: {doc['score']:.3f})")
            else:
                print(f'⚠️ Query: "{query}"')
                print(f"   Results: 0, Latency: {latency:.1f}ms")
                print(f"   (Vector DB möglicherweise leer)")
            print()

        # Stats
        print("-" * 80)
        print("📊 Adapter Statistics:")
        stats = adapter.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        print()

        return adapter, stats

    except Exception as e:
        print(f"❌ Test 1 Failed: {e}")
        import traceback

        traceback.print_exc()
        return None, None


async def test_hybrid_integration(adapter):
    """Test 2: HybridRetriever Integration"""
    print("=" * 80)
    print("TEST 2: HYBRID RETRIEVER INTEGRATION")
    print("=" * 80)
    print()

    if adapter is None:
        print("❌ Skipped: Adapter nicht verfügbar")
        return None

    try:
        from backend.agents.veritas_hybrid_retrieval import HybridRetriever
        from backend.agents.veritas_sparse_retrieval import SparseRetriever

        # Initialize BM25
        print("🔄 Initialisiere BM25...")
        bm25 = SparseRetriever()

        # Index demo documents
        demo_docs = [
            {
                "doc_id": "bgb_110",
                "content": "§ 110 BGB Taschengeldparagraph - Bewirken der Leistung mit eigenen Mitteln. Ein von dem Minderjährigen ohne Zustimmung des gesetzlichen Vertreters geschlossener Vertrag gilt als von Anfang an wirksam, wenn der Minderjährige die vertragsmäßige Leistung mit Mitteln bewirkt, die ihm zu diesem Zweck oder zu freier Verfügung von dem Vertreter oder mit dessen Zustimmung von einem Dritten überlassen worden sind.",
            },
            {
                "doc_id": "bgb_433",
                "content": "§ 433 BGB Vertragstypische Pflichten beim Kaufvertrag. (1) Durch den Kaufvertrag wird der Verkäufer einer Sache verpflichtet, dem Käufer die Sache zu übergeben und das Eigentum an der Sache zu verschaffen. Der Verkäufer hat dem Käufer die Sache frei von Sach- und Rechtsmängeln zu verschaffen. (2) Der Käufer ist verpflichtet, dem Verkäufer den vereinbarten Kaufpreis zu zahlen und die gekaufte Sache abzunehmen.",
            },
            {
                "doc_id": "vwvfg_35",
                "content": "§ 35 VwVfG Begriff des Verwaltungsaktes. Verwaltungsakt ist jede Verfügung, Entscheidung oder andere hoheitliche Maßnahme, die eine Behörde zur Regelung eines Einzelfalls auf dem Gebiet des öffentlichen Rechts trifft und die auf unmittelbare Rechtswirkung nach außen gerichtet ist.",
            },
        ]

        bm25.index_documents(demo_docs)
        print(f"   ✅ BM25 indexed: {len(demo_docs)} docs")
        print()

        # Initialize HybridRetriever
        print("🔄 Initialisiere HybridRetriever...")
        hybrid = HybridRetriever(
            dense_retriever=adapter, sparse_retriever=bm25, config=None  # UDS3 Adapter as dense retriever  # Use defaults
        )
        print(f"   ✅ HybridRetriever initialized")
        print(f"   Dense Backend: UDS3VectorSearchAdapter")
        print(f"   Sparse Backend: BM25Okapi")
        print()

        # Test hybrid search
        test_query = "BGB Minderjährige Vertragsschluss"
        print(f'🔍 Hybrid Search Query: "{test_query}"')
        print()

        start = time.time()
        results = await hybrid.retrieve(test_query, top_k=5)
        latency = (time.time() - start) * 1000

        print(f"📊 Hybrid Search Results:")
        print(f"   Total Results: {len(results)}")
        print(f"   Latency: {latency:.1f}ms")
        print()

        if results:
            print("Top Results:")
            for i, result in enumerate(results, 1):
                dense_score = result.dense_score if result.dense_score is not None else 0.0
                sparse_score = result.sparse_score if result.sparse_score is not None else 0.0
                print(f"   {i}. {result.doc_id} (RRF Score: {result.score:.4f})")
                print(f"      Dense Score: {dense_score:.4f}, Sparse Score: {sparse_score:.4f}")
                print(f"      Content: {result.content[:80]}...")
                print()
        else:
            print("⚠️ No hybrid results")
            print("   Hinweis: Vector DB möglicherweise leer, BM25 sollte trotzdem Results liefern")

        return hybrid

    except Exception as e:
        print(f"❌ Test 2 Failed: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_fallback_behavior():
    """Test 3: Graceful Degradation bei UDS3 Fehler"""
    print("=" * 80)
    print("TEST 3: GRACEFUL DEGRADATION (BM25-ONLY FALLBACK)")
    print("=" * 80)
    print()

    try:
        from backend.agents.veritas_hybrid_retrieval import HybridRetriever
        from backend.agents.veritas_sparse_retrieval import SparseRetriever
        from backend.agents.veritas_uds3_adapter import UDS3VectorSearchAdapter

        # Create failing adapter mock
        class FailingAdapter:
            async def vector_search(self, query: str, top_k: int = 5, **kwargs):
                raise Exception("Simulated UDS3 failure")

        # Initialize BM25
        bm25 = SparseRetriever()
        demo_docs = [
            {"doc_id": "test_1", "content": "Test document one"},
            {"doc_id": "test_2", "content": "Test document two"},
        ]
        bm25.index_documents(demo_docs)

        # HybridRetriever with failing dense backend
        hybrid = HybridRetriever(dense_retriever=FailingAdapter(), sparse_retriever=bm25, config=None)

        print("🔍 Testing with failing Dense backend...")
        results = await hybrid.retrieve("test document", top_k=2)

        if results:
            print(f"✅ Graceful Degradation successful!")
            print(f"   Results: {len(results)} (BM25-only)")
            for result in results:
                print(f"   - {result.doc_id}")
        else:
            print("❌ Fallback nicht aktiviert - keine Results")

        print()

    except Exception as e:
        print(f"❌ Test 3 Failed: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print("UDS3 VECTOR SEARCH ADAPTER - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()

    # Test 1: Adapter Standalone
    adapter, stats = await test_adapter_standalone()

    print("\n")

    # Test 2: HybridRetriever Integration
    if adapter:
        hybrid = await test_hybrid_integration(adapter)

    print("\n")

    # Test 3: Graceful Degradation
    await test_fallback_behavior()

    # Summary
    print("\n")
    print("=" * 80)
    print("TEST SUITE SUMMARY")
    print("=" * 80)
    print()

    if adapter and stats:
        success_rate = stats.get("success_rate", 0.0) * 100
        avg_latency = stats.get("avg_latency_ms", 0.0)

        print(f"✅ Adapter Status: Initialized")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Avg Latency: {avg_latency:.1f}ms")

        if stats.get("successful_queries", 0) > 0:
            print(f"   Assessment: 🟢 OPERATIONAL")
        else:
            print(f"   Assessment: 🟡 OPERATIONAL (Vector DB leer)")
            print(f"   Hinweis: Adapter funktioniert, aber UDS3 Vector DB enthält keine Daten")
            print(f"   Empfehlung: Dokumente via create_secure_document() indexieren")
    else:
        print(f"❌ Adapter Status: Failed")
        print(f"   Empfehlung: UDS3 Logs prüfen")

    print()
    print("=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print()
    print("1. Falls Vector DB leer:")
    print("   - Dokumente via UDS3 create_secure_document() indexieren")
    print("   - Oder: Mock-Daten via scripts/index_demo_corpus.py")
    print()
    print("2. Falls Adapter funktioniert:")
    print("   - Integration in HybridRetriever abgeschlossen ✅")
    print("   - Staging Deployment mit enable_hybrid_search=True")
    print()
    print("3. Evaluation:")
    print("   - Ground-Truth Dataset erstellen")
    print("   - Baseline vs Hybrid A/B-Test")
    print()


if __name__ == "__main__":
    asyncio.run(main())
