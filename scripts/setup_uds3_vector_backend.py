"""
UDS3 Vector Backend Setup
Konfiguriert ChromaDB und indexiert Demo-Corpus für Phase 5 Hybrid Search
"""
import asyncio
import sys
import time
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Demo Corpus (same as BM25 demo)
DEMO_CORPUS = [
    {
        "doc_id": "bgb_110",
        "title": "§ 110 BGB - Taschengeldparagraph",
        "content": "§ 110 BGB - Bewirken der Leistung mit eigenen Mitteln. Ein von dem Minderjährigen ohne Zustimmung des gesetzlichen Vertreters geschlossener Vertrag gilt als von Anfang an wirksam, wenn der Minderjährige die vertragsmäßige Leistung mit Mitteln bewirkt, die ihm zu diesem Zweck oder zu freier Verfügung von dem Vertreter oder mit dessen Zustimmung von einem Dritten überlassen worden sind. Praktische Bedeutung: Der sogenannte Taschengeldparagraph erlaubt es Minderjährigen, Verträge mit ihrem Taschengeld wirksam abzuschließen, ohne dass die Eltern zustimmen müssen.",
        "metadata": {"source": "BGB", "paragraph": "110", "category": "Legal", "topic": "Vertragsrecht"},
    },
    {
        "doc_id": "bgb_433",
        "title": "§ 433 BGB - Vertragstypische Pflichten beim Kaufvertrag",
        "content": "§ 433 BGB - Vertragstypische Pflichten beim Kaufvertrag. Durch den Kaufvertrag wird der Verkäufer einer Sache verpflichtet, dem Käufer die Sache zu übergeben und das Eigentum an der Sache zu verschaffen. Der Verkäufer hat dem Käufer die Sache frei von Sach- und Rechtsmängeln zu verschaffen. Der Käufer ist verpflichtet, dem Verkäufer den vereinbarten Kaufpreis zu zahlen und die gekaufte Sache abzunehmen. Grundnorm des Kaufvertragsrechts.",
        "metadata": {"source": "BGB", "paragraph": "433", "category": "Legal", "topic": "Kaufrecht"},
    },
    {
        "doc_id": "vwvfg_24",
        "title": "§ 24 VwVfG - Anhörung Beteiligter",
        "content": "§ 24 VwVfG - Anhörung Beteiligter. Bevor ein Verwaltungsakt erlassen wird, der in Rechte eines Beteiligten eingreift, ist diesem Gelegenheit zu geben, sich zu den für die Entscheidung erheblichen Tatsachen zu äußern. Von der Anhörung kann abgesehen werden bei Gefahr im Verzug oder im öffentlichen Interesse. Rechtliches Gehör ist ein Grundprinzip des Verwaltungsverfahrens.",
        "metadata": {"source": "VwVfG", "paragraph": "24", "category": "Administrative", "topic": "Verwaltungsverfahren"},
    },
    {
        "doc_id": "vwvfg_35",
        "title": "§ 35 VwVfG - Begriff des Verwaltungsakts",
        "content": "§ 35 VwVfG - Begriff des Verwaltungsakts. Verwaltungsakt ist jede Verfügung, Entscheidung oder andere hoheitliche Maßnahme, die eine Behörde zur Regelung eines Einzelfalls auf dem Gebiet des öffentlichen Rechts trifft und die auf unmittelbare Rechtswirkung nach außen gerichtet ist. Allgemeinverfügung ist ein Verwaltungsakt, der sich an einen nach allgemeinen Merkmalen bestimmten oder bestimmbaren Personenkreis richtet. Zentrale Definition für Verwaltungsrecht.",
        "metadata": {"source": "VwVfG", "paragraph": "35", "category": "Administrative", "topic": "Verwaltungsrecht"},
    },
    {
        "doc_id": "uwg_3",
        "title": "§ 3 UWG - Verbot unlauterer geschäftlicher Handlungen",
        "content": "§ 3 UWG - Verbot unlauterer geschäftlicher Handlungen. Unlautere geschäftliche Handlungen sind unzulässig. Geschäftliche Handlungen, die sich an Verbraucher richten oder diese erreichen, sind unlauter, wenn sie nicht der unternehmerischen Sorgfalt entsprechen und dazu geeignet sind, das wirtschaftliche Verhalten des Verbrauchers wesentlich zu beeinflussen. Verbraucherschutz im Wettbewerbsrecht.",
        "metadata": {"source": "UWG", "paragraph": "3", "category": "Legal", "topic": "Wettbewerbsrecht"},
    },
    {
        "doc_id": "umwelt_45",
        "title": "§ 45 Umweltgesetz - Emissionsschutz",
        "content": "§ 45 Umweltgesetz - Emissionsschutz und Grenzwerte. Genehmigungsbedürftige Anlagen sind so zu errichten und zu betreiben, dass zur Gewährleistung eines hohen Schutzniveaus für die Umwelt insgesamt schädliche Umwelteinwirkungen nicht hervorgerufen werden können. Die Pflichten sind zu erfüllen durch die dem Stand der Technik entsprechende Emissionsbegrenzung. Best-Available-Technology Prinzip für Umweltschutz.",
        "metadata": {"source": "Umweltgesetz", "paragraph": "45", "category": "Environmental", "topic": "Umweltschutz"},
    },
    {
        "doc_id": "stgb_242",
        "title": "§ 242 StGB - Diebstahl",
        "content": "§ 242 StGB - Diebstahl. Wer eine fremde bewegliche Sache einem anderen in der Absicht wegnimmt, die Sache sich oder einem Dritten rechtswidrig zuzueignen, wird mit Freiheitsstrafe bis zu fünf Jahren oder mit Geldstrafe bestraft. Der Versuch ist strafbar. Grunddelikt des Eigentumsstrafrechts. Tatbestandsmerkmale: fremd, beweglich, wegnehmen, Zueignungsabsicht.",
        "metadata": {"source": "StGB", "paragraph": "242", "category": "Legal", "topic": "Strafrecht"},
    },
    {
        "doc_id": "gg_1",
        "title": "Art. 1 GG - Menschenwürde",
        "content": "Art. 1 GG - Menschenwürde. Die Würde des Menschen ist unantastbar. Sie zu achten und zu schützen ist Verpflichtung aller staatlichen Gewalt. Das Deutsche Volk bekennt sich darum zu unverletzlichen und unveräußerlichen Menschenrechten als Grundlage jeder menschlichen Gemeinschaft, des Friedens und der Gerechtigkeit in der Welt. Höchster Wert der deutschen Verfassung, Kern aller Grundrechte.",
        "metadata": {"source": "GG", "paragraph": "1", "category": "Constitutional", "topic": "Grundrechte"},
    },
]


async def setup_vector_backend():
    """Setup UDS3 Vector Backend mit ChromaDB und Embeddings"""
    print("=" * 80)
    print("UDS3 VECTOR BACKEND SETUP")
    print("=" * 80)
    print()

    try:
        # Step 1: Check UDS3
        print("📊 SCHRITT 1: UDS3 System Check")
        print("-" * 80)

        from uds3.uds3_core import get_optimized_unified_strategy

        print("🔄 Initialisiere UDS3...")
        uds3 = get_optimized_unified_strategy()
        print(f"✅ UDS3 Strategy: {uds3.__class__.__name__}")
        print()

        # Step 2: Check Vector Backend
        print("📊 SCHRITT 2: Vector Backend Check")
        print("-" * 80)

        has_vector_backend = False
        collection = None

        # Try different approaches to access vector backend
        if hasattr(uds3, "vector_backend"):
            print("✅ vector_backend Attribut gefunden")
            vector_backend = uds3.vector_backend

            if hasattr(vector_backend, "collection"):
                collection = vector_backend.collection
                print(f"✅ ChromaDB Collection: {collection}")
                has_vector_backend = True
            else:
                print("⚠️ vector_backend hat keine collection")
        else:
            print("⚠️ UDS3 hat kein vector_backend Attribut")

            # Try to find collection via other paths
            for attr in dir(uds3):
                if not attr.startswith("_"):
                    obj = getattr(uds3, attr, None)
                    if obj and hasattr(obj, "collection"):
                        print(f"   🔍 Gefunden: {attr}.collection")
                        collection = obj.collection
                        has_vector_backend = True
                        break

        print()

        if not has_vector_backend or not collection:
            print("❌ PROBLEM: ChromaDB Collection nicht gefunden!")
            print()
            print("LÖSUNGSOPTIONEN:")
            print("1. ChromaDB manuell initialisieren")
            print("2. UDS3 Config überprüfen")
            print("3. Alternative: Mock Vector Search verwenden")
            print()

            # Try to initialize ChromaDB directly
            print("🔄 Versuche ChromaDB direkt zu initialisieren...")
            try:
                import chromadb

                chroma_client = chromadb.Client()
                collection = chroma_client.get_or_create_collection(name="veritas_demo", metadata={"hnsw:space": "cosine"})
                print(f"✅ ChromaDB Collection erstellt: {collection.name}")
                print(f"   Items: {collection.count()}")
                has_vector_backend = True
            except Exception as e:
                print(f"❌ ChromaDB Fehler: {e}")
                return False

        print()

        # Step 3: Check Ollama for Embeddings
        print("📊 SCHRITT 3: Ollama Embedding Check")
        print("-" * 80)

        ollama_available = False
        embedding_model = None

        try:
            import requests

            # Check Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=2)

            if response.status_code == 200:
                models = response.json().get("models", [])
                print(f"✅ Ollama läuft - {len(models)} Modelle verfügbar")

                # Check for embedding models
                embedding_models = [
                    m
                    for m in models
                    if "embed" in m.get("name", "").lower()
                    or m.get("name") in ["nomic-embed-text", "mxbai-embed-large", "all-minilm"]
                ]

                if embedding_models:
                    embedding_model = embedding_models[0]["name"]
                    print(f"✅ Embedding-Modell gefunden: {embedding_model}")
                    ollama_available = True
                else:
                    # Use any available model for embeddings
                    if models:
                        embedding_model = models[0]["name"]
                        print(f"⚠️ Kein dediziertes Embedding-Modell, nutze: {embedding_model}")
                        ollama_available = True
                    else:
                        print("⚠️ Keine Modelle verfügbar")
            else:
                print(f"⚠️ Ollama Response: {response.status_code}")

        except requests.exceptions.ConnectionError:
            print("❌ Ollama nicht erreichbar (http://localhost:11434)")
            print("   Start: ollama serve")
        except Exception as e:
            print(f"❌ Ollama Check Fehler: {e}")

        print()

        if not ollama_available:
            print("⚠️ OHNE OLLAMA: Verwende ChromaDB Default-Embeddings")
            print("   ChromaDB nutzt sentence-transformers als Fallback")
            embedding_model = "chroma_default"

        print()

        # Step 4: Index Demo Corpus
        print("📊 SCHRITT 4: Demo-Corpus Indexierung")
        print("-" * 80)
        print(f"Corpus: {len(DEMO_CORPUS)} Dokumente")
        print()

        if not collection:
            print("❌ Keine Collection verfügbar - Abbruch")
            return False

        # Check current count
        current_count = collection.count()
        print(f"📄 Aktuelle Collection-Größe: {current_count}")

        if current_count >= len(DEMO_CORPUS):
            print("⚠️ Collection enthält bereits Dokumente")
            print("   Optionen:")
            print("   A) Überspringen")
            print("   B) Neu indexieren (löscht alte Daten)")
            print()
            # For automation, skip if already indexed
            print("🔄 Auto-Entscheidung: Überspringen (bereits indexiert)")
        else:
            print("🔄 Indexiere Dokumente...")
            print()

            # Prepare data
            ids = [doc["doc_id"] for doc in DEMO_CORPUS]
            documents = [doc["content"] for doc in DEMO_CORPUS]
            metadatas = [{"doc_id": doc["doc_id"], "title": doc["title"], **doc["metadata"]} for doc in DEMO_CORPUS]

            # Generate embeddings and add to collection
            if ollama_available and embedding_model != "chroma_default":
                print(f"   🔄 Generiere Embeddings mit Ollama ({embedding_model})...")

                # Generate embeddings via Ollama
                embeddings = []
                for i, doc in enumerate(DEMO_CORPUS, 1):
                    try:
                        print(f"   [{i}/{len(DEMO_CORPUS)}] {doc['doc_id']}... ", end="", flush=True)

                        response = requests.post(
                            "http://localhost:11434/api/embeddings",
                            json={"model": embedding_model, "prompt": doc["content"]},
                            timeout=10,
                        )

                        if response.status_code == 200:
                            embedding = response.json().get("embedding", [])
                            embeddings.append(embedding)
                            print("✅")
                        else:
                            print(f"❌ Status {response.status_code}")
                            return False

                    except Exception as e:
                        print(f"❌ Error: {e}")
                        return False

                print()
                print(f"   ✅ {len(embeddings)} Embeddings generiert")
                print(f"   🔄 Füge zu ChromaDB hinzu...")

                # Add with embeddings
                collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
            else:
                print(f"   🔄 Nutze ChromaDB Default-Embeddings...")

                # Let ChromaDB generate embeddings
                collection.add(ids=ids, documents=documents, metadatas=metadatas)

            print(f"   ✅ Indexierung abgeschlossen!")

        print()

        # Step 5: Verify with Test Query
        print("📊 SCHRITT 5: Vector Search Test")
        print("-" * 80)

        test_query = "BGB Vertragsrecht Minderjährige"
        print(f'Query: "{test_query}"')
        print()

        # Query collection
        print("🔄 Führe Vector Search aus...")

        if ollama_available and embedding_model != "chroma_default":
            # Generate query embedding via Ollama
            print(f"   🔄 Generiere Query-Embedding ({embedding_model})...")
            response = requests.post(
                "http://localhost:11434/api/embeddings", json={"model": embedding_model, "prompt": test_query}, timeout=10
            )

            if response.status_code == 200:
                query_embedding = response.json().get("embedding", [])
                print(f"   ✅ Query-Embedding: {len(query_embedding)} dimensions")

                results = collection.query(query_embeddings=[query_embedding], n_results=3)
            else:
                print(f"   ❌ Embedding-Fehler: {response.status_code}")
                return False
        else:
            # ChromaDB generates query embedding
            results = collection.query(query_texts=[test_query], n_results=3)

        print()
        print("📄 Top Results:")

        if results and results.get("ids") and results["ids"][0]:
            for i, (doc_id, distance, doc) in enumerate(
                zip(results["ids"][0], results["distances"][0], results["documents"][0]), 1
            ):
                score = 1 / (1 + distance)  # Convert distance to similarity score
                print(f"   {i}. {doc_id} (Score: {score:.3f}, Distance: {distance:.3f})")
                print(f"      {doc[:100]}...")

            print()
            print("✅ Vector Search funktioniert!")

            # Check if expected doc is top-1
            if results["ids"][0][0] == "bgb_110":
                print("✅ EXPECTED DOC in Top-1: bgb_110")
            else:
                print(f"⚠️ Expected bgb_110, got {results['ids'][0][0]}")
        else:
            print("❌ Keine Ergebnisse!")
            return False

        print()
        print("=" * 80)
        print("✅ UDS3 VECTOR BACKEND SETUP ERFOLGREICH")
        print("=" * 80)
        print()

        print("ZUSAMMENFASSUNG:")
        print(f"• ChromaDB Collection: {collection.name}")
        print(f"• Dokumente: {collection.count()}")
        print(f"• Embedding-Modell: {embedding_model}")
        print(f"• Vector Search: Funktioniert ✅")
        print()

        print("NÄCHSTE SCHRITTE:")
        print("1. ✅ Vector Backend konfiguriert")
        print("2. 🔄 Hybrid Search testen (Dense + BM25)")
        print("3. 🔄 Staging Phase 1 deployen")
        print("4. 🔄 Ground-Truth Dataset erstellen")
        print("5. 🔄 Evaluation durchführen")

        return True

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print()
        print("Fehlende Dependencies:")
        print("  pip install chromadb requests")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(setup_vector_backend())
    sys.exit(0 if result else 1)
