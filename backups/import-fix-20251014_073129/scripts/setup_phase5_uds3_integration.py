"""
Phase 5 UDS3 Integration
Nutzt UDS3 Database API für Dokument-Indexierung und Vector Search
"""
import asyncio
import sys
import time
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Demo Corpus
DEMO_CORPUS = [
    {
        "doc_id": "bgb_110",
        "title": "§ 110 BGB - Taschengeldparagraph",
        "content": "§ 110 BGB - Bewirken der Leistung mit eigenen Mitteln. Ein von dem Minderjährigen ohne Zustimmung des gesetzlichen Vertreters geschlossener Vertrag gilt als von Anfang an wirksam, wenn der Minderjährige die vertragsmäßige Leistung mit Mitteln bewirkt, die ihm zu diesem Zweck oder zu freier Verfügung von dem Vertreter oder mit dessen Zustimmung von einem Dritten überlassen worden sind.",
        "metadata": {"source": "BGB", "paragraph": "110", "category": "Legal", "topic": "Vertragsrecht"},
    },
    {
        "doc_id": "bgb_433",
        "title": "§ 433 BGB - Kaufvertrag",
        "content": "§ 433 BGB - Vertragstypische Pflichten beim Kaufvertrag. Durch den Kaufvertrag wird der Verkäufer verpflichtet, dem Käufer die Sache zu übergeben und das Eigentum zu verschaffen. Der Käufer zahlt den Kaufpreis und nimmt die Sache ab.",
        "metadata": {"source": "BGB", "paragraph": "433", "category": "Legal", "topic": "Kaufrecht"},
    },
    {
        "doc_id": "vwvfg_24",
        "title": "§ 24 VwVfG - Anhörung",
        "content": "§ 24 VwVfG - Anhörung Beteiligter. Bevor ein Verwaltungsakt erlassen wird, der in Rechte eingreift, ist Gelegenheit zur Äußerung zu geben. Rechtliches Gehör ist Grundprinzip des Verwaltungsverfahrens.",
        "metadata": {"source": "VwVfG", "paragraph": "24", "category": "Administrative", "topic": "Verwaltungsverfahren"},
    },
    {
        "doc_id": "vwvfg_35",
        "title": "§ 35 VwVfG - Verwaltungsakt",
        "content": "§ 35 VwVfG - Begriff des Verwaltungsakts. Verwaltungsakt ist jede Verfügung, Entscheidung oder hoheitliche Maßnahme einer Behörde zur Regelung eines Einzelfalls mit unmittelbarer Rechtswirkung nach außen.",
        "metadata": {"source": "VwVfG", "paragraph": "35", "category": "Administrative", "topic": "Verwaltungsrecht"},
    },
    {
        "doc_id": "uwg_3",
        "title": "§ 3 UWG - Unlauterer Wettbewerb",
        "content": "§ 3 UWG - Verbot unlauterer geschäftlicher Handlungen. Unlautere geschäftliche Handlungen sind unzulässig. Verbraucherschutz im Wettbewerbsrecht.",
        "metadata": {"source": "UWG", "paragraph": "3", "category": "Legal", "topic": "Wettbewerbsrecht"},
    },
    {
        "doc_id": "umwelt_45",
        "title": "§ 45 Umweltgesetz - Emissionsschutz",
        "content": "§ 45 Umweltgesetz - Emissionsschutz. Anlagen sind so zu betreiben, dass schädliche Umwelteinwirkungen verhindert werden. Stand der Technik Prinzip für Umweltschutz.",
        "metadata": {"source": "Umweltgesetz", "paragraph": "45", "category": "Environmental", "topic": "Umweltschutz"},
    },
    {
        "doc_id": "stgb_242",
        "title": "§ 242 StGB - Diebstahl",
        "content": "§ 242 StGB - Diebstahl. Wer eine fremde bewegliche Sache in Zueignungsabsicht wegnimmt, wird bestraft. Grunddelikt des Eigentumsstrafrechts.",
        "metadata": {"source": "StGB", "paragraph": "242", "category": "Legal", "topic": "Strafrecht"},
    },
    {
        "doc_id": "gg_1",
        "title": "Art. 1 GG - Menschenwürde",
        "content": "Art. 1 GG - Menschenwürde. Die Würde des Menschen ist unantastbar. Sie zu achten und zu schützen ist Verpflichtung aller staatlichen Gewalt. Höchster Wert der deutschen Verfassung.",
        "metadata": {"source": "GG", "paragraph": "1", "category": "Constitutional", "topic": "Grundrechte"},
    },
]


async def setup_phase5_with_uds3():
    """Setup Phase 5 mit UDS3 Database API"""
    print("=" * 80)
    print("PHASE 5 - UDS3 DATABASE API INTEGRATION")
    print("=" * 80)
    print()

    try:
        # Step 1: Initialize UDS3
        print("📊 SCHRITT 1: UDS3 Initialisierung")
        print("-" * 80)

        from uds3.uds3_core import get_optimized_unified_strategy

        print("🔄 Initialisiere UDS3 Strategy...")
        uds3 = get_optimized_unified_strategy()
        print(f"✅ UDS3: {uds3.__class__.__name__}")
        print()

        # Step 2: Index Documents via UDS3 API
        print("📊 SCHRITT 2: Dokumente indexieren (UDS3 API)")
        print("-" * 80)
        print(f"Corpus: {len(DEMO_CORPUS)} Dokumente")
        print()

        indexed_count = 0

        # Try create_secure_document method
        if hasattr(uds3, "create_secure_document"):
            print("🔄 Nutze create_secure_document()...")

            for i, doc in enumerate(DEMO_CORPUS, 1):
                try:
                    print(f"   [{i}/{len(DEMO_CORPUS)}] {doc['doc_id']}... ", end="", flush=True)

                    result = uds3.create_secure_document(
                        file_path=f"demo/{doc['doc_id']}.txt",
                        content=doc["content"],
                        chunks=[doc["content"]],  # Single chunk
                        security_level="PUBLIC",
                        metadata={**doc["metadata"], "title": doc["title"], "doc_id": doc["doc_id"]},
                    )

                    if result and result.get("success", False):
                        print("✅")
                        indexed_count += 1
                    else:
                        print(f"⚠️ {result.get('error', 'Unknown error')}")

                except Exception as e:
                    print(f"❌ {str(e)[:50]}")

            print()
            print(f"✅ {indexed_count}/{len(DEMO_CORPUS)} Dokumente indexiert")

        else:
            print("❌ create_secure_document nicht verfügbar")
            print(f"   Verfügbare Methoden: {[m for m in dir(uds3) if not m.startswith('_') and 'create' in m.lower()][:5]}")
            return False

        print()

        # Step 3: Test Vector Search via UDS3 API
        print("📊 SCHRITT 3: Vector Search Test (UDS3 API)")
        print("-" * 80)

        test_query = "BGB Vertragsrecht Minderjährige"
        print(f'Query: "{test_query}"')
        print()

        # Try query_across_databases
        if hasattr(uds3, "query_across_databases"):
            print("🔄 Nutze query_across_databases()...")

            try:
                result = uds3.query_across_databases(
                    vector_params={"query_text": test_query, "top_k": 3, "threshold": 0.0},
                    graph_params=None,
                    relational_params=None,
                    join_strategy="union",
                    execution_mode="smart",
                )

                print(f"✅ Query ausgeführt")
                print(f"   Success: {result.success if hasattr(result, 'success') else 'N/A'}")
                print(f"   Join Strategy: {result.join_strategy if hasattr(result, 'join_strategy') else 'N/A'}")
                print(f"   Databases Queried: {len(result.databases_queried) if hasattr(result, 'databases_queried') else 0}")

                # Extract results
                docs = []
                if hasattr(result, "joined_results"):
                    docs = result.joined_results
                elif hasattr(result, "database_results") and result.database_results:
                    # Try to extract from database_results
                    for db_name, db_result in result.database_results.items():
                        if hasattr(db_result, "documents"):
                            docs.extend(db_result.documents)

                print()
                print(f"📄 Results: {len(docs)}")

                if docs:
                    print()
                    print("Top Results:")
                    for i, doc in enumerate(docs[:3], 1):
                        doc_id = doc.get("doc_id", doc.get("id", "N/A"))
                        score = doc.get("score", doc.get("relevance", 0))
                        print(f"   {i}. {doc_id} (Score: {score:.3f})")
                else:
                    print("⚠️ Keine Results - Vector DB möglicherweise nicht korrekt indexiert")

            except Exception as e:
                print(f"❌ Query Error: {e}")
                import traceback

                traceback.print_exc()

        else:
            print("❌ query_across_databases nicht verfügbar")
            return False

        print()

        # Step 4: Test Phase 5 Hybrid Search
        print("📊 SCHRITT 4: Phase 5 Hybrid Search Test")
        print("-" * 80)

        from backend.agents.veritas_hybrid_retrieval import HybridRetriever
        from backend.agents.veritas_sparse_retrieval import SparseRetrievalConfig

        print("🔄 Initialisiere Hybrid Retriever...")

        # HybridRetriever benötigt dense_retriever (= UDS3)
        hybrid = HybridRetriever(
            dense_retriever=uds3,  # UDS3 als Dense Retriever
            sparse_retriever=None,  # Wird automatisch erstellt
            config=None,  # Default Config
        )

        # Index BM25
        print("   🔄 Indexiere BM25 Sparse Retrieval...")
        bm25_docs = [{"doc_id": doc["doc_id"], "text": doc["content"]} for doc in DEMO_CORPUS]
        hybrid.sparse_retriever.index_documents(bm25_docs, content_field="text", id_field="doc_id")
        print(f"   ✅ BM25 Index: {len(bm25_docs)} docs")
        print()

        # Test Hybrid Retrieval
        print(f'Query: "{test_query}"')

        try:
            start_time = time.time()
            results = await hybrid.retrieve(test_query, top_k=5)
            latency = (time.time() - start_time) * 1000

            print(f"⏱️  Latency: {latency:.2f}ms")
            print(f"📄 Results: {len(results)}")
            print()

            if results:
                print("Top Results (Hybrid = Dense + BM25 via RRF):")
                for i, res in enumerate(results, 1):
                    print(f"   {i}. {res.doc_id}")
                    print(f"      Score: {res.score:.3f}, RRF: {res.rrf_score:.4f}")
                    if hasattr(res, "sources") and res.sources:
                        print(f"      Sources: {res.sources}")

                print()
                print("✅ Hybrid Search funktioniert!")

                # Performance Assessment
                if latency < 150:
                    print(f"🟢 Performance: EXCELLENT ({latency:.0f}ms < 150ms target)")
                elif latency < 200:
                    print(f"🟡 Performance: GOOD ({latency:.0f}ms < 200ms limit)")
                else:
                    print(f"🔴 Performance: NEEDS OPTIMIZATION ({latency:.0f}ms > 200ms)")

            else:
                print("⚠️ Keine Hybrid-Ergebnisse")
                print("   Mögliche Ursache: UDS3 Vector Search leer")

        except Exception as e:
            print(f"❌ Hybrid Search Error: {e}")
            import traceback

            traceback.print_exc()

        print()
        print("=" * 80)
        print("ZUSAMMENFASSUNG")
        print("=" * 80)
        print()

        print("✅ ABGESCHLOSSEN:")
        print(f"   • UDS3 initialisiert")
        print(f"   • {indexed_count}/{len(DEMO_CORPUS)} Dokumente indexiert (create_secure_document)")
        print(f"   • Vector Search via query_across_databases getestet")
        print(f"   • Phase 5 Hybrid Search getestet")
        print()

        print("NÄCHSTE SCHRITTE:")
        print("1. ✅ UDS3 Database API integriert")
        print("2. 🔄 Staging Phase 1 deployen (enable_hybrid_search=True)")
        print("3. 🔄 Ground-Truth Dataset erstellen")
        print("4. 🔄 Baseline vs Hybrid Evaluation")
        print("5. 🔄 Query Expansion testen (Staging Phase 2)")

        return indexed_count > 0

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        import traceback

        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(setup_phase5_with_uds3())
    sys.exit(0 if result else 1)
