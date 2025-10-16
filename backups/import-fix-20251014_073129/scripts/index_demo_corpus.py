"""
UDS3 Demo Corpus - Erstellt und indexiert einen Demo-Corpus für Phase 5 Testing
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Demo Documents - Verwaltungsrecht & BGB
DEMO_CORPUS = [
    {
        "doc_id": "bgb_110",
        "title": "§ 110 BGB - Taschengeldparagraph",
        "content": """§ 110 BGB - Bewirken der Leistung mit eigenen Mitteln

Ein von dem Minderjährigen ohne Zustimmung des gesetzlichen Vertreters geschlossener Vertrag gilt als von Anfang an wirksam, wenn der Minderjährige die vertragsmäßige Leistung mit Mitteln bewirkt, die ihm zu diesem Zweck oder zu freier Verfügung von dem Vertreter oder mit dessen Zustimmung von einem Dritten überlassen worden sind.

Praktische Bedeutung: Der sogenannte "Taschengeldparagraph" erlaubt es Minderjährigen, Verträge mit ihrem Taschengeld wirksam abzuschließen, ohne dass die Eltern zustimmen müssen.

Beispiel: Ein 15-Jähriger kauft mit seinem Taschengeld ein Computerspiel. Der Kaufvertrag ist wirksam, auch ohne Zustimmung der Eltern.""",
        "metadata": {
            "source": "BGB",
            "paragraph": "110",
            "category": "Legal",
            "topic": "Vertragsrecht",
            "keywords": ["Minderjährige", "Taschengeld", "Vertragsrecht", "BGB"]
        }
    },
    {
        "doc_id": "bgb_433",
        "title": "§ 433 BGB - Vertragstypische Pflichten beim Kaufvertrag",
        "content": """§ 433 BGB - Vertragstypische Pflichten beim Kaufvertrag

(1) Durch den Kaufvertrag wird der Verkäufer einer Sache verpflichtet, dem Käufer die Sache zu übergeben und das Eigentum an der Sache zu verschaffen. Der Verkäufer hat dem Käufer die Sache frei von Sach- und Rechtsmängeln zu verschaffen.

(2) Der Käufer ist verpflichtet, dem Verkäufer den vereinbarten Kaufpreis zu zahlen und die gekaufte Sache abzunehmen.

Praktische Bedeutung: Grundnorm des Kaufvertragsrechts. Definiert die Hauptpflichten von Käufer und Verkäufer.

Beispiel: Beim Autokauf muss der Verkäufer das Auto übergeben und Eigentum verschaffen. Der Käufer zahlt den Kaufpreis und nimmt das Auto ab.""",
        "metadata": {
            "source": "BGB",
            "paragraph": "433",
            "category": "Legal",
            "topic": "Kaufrecht",
            "keywords": ["Kaufvertrag", "Verkäufer", "Käufer", "Pflichten"]
        }
    },
    {
        "doc_id": "vwvfg_24",
        "title": "§ 24 VwVfG - Anhörung Beteiligter",
        "content": """§ 24 VwVfG - Anhörung Beteiligter

(1) Bevor ein Verwaltungsakt erlassen wird, der in Rechte eines Beteiligten eingreift, ist diesem Gelegenheit zu geben, sich zu den für die Entscheidung erheblichen Tatsachen zu äußern.

(2) Von der Anhörung kann abgesehen werden, wenn
1. eine sofortige Entscheidung wegen Gefahr im Verzug oder im öffentlichen Interesse notwendig erscheint,
2. durch die Anhörung die Einhaltung einer für die Entscheidung maßgeblichen Frist in Frage gestellt würde,
3. von den tatsächlichen Angaben eines Beteiligten, die dieser in einem Antrag oder einer Erklärung gemacht hat, nicht zu seinen Ungunsten abgewichen werden soll.

Praktische Bedeutung: Grundprinzip des Verwaltungsverfahrens - "rechtliches Gehör". Betroffene müssen vor belastenden Entscheidungen angehört werden.

Beispiel: Bevor ein Bußgeldbescheid erlassen wird, muss dem Betroffenen Gelegenheit zur Stellungnahme gegeben werden.""",
        "metadata": {
            "source": "VwVfG",
            "paragraph": "24",
            "category": "Administrative",
            "topic": "Verwaltungsverfahren",
            "keywords": ["Anhörung", "Verwaltungsakt", "Rechtliches Gehör", "Verfahren"]
        }
    },
    {
        "doc_id": "vwvfg_35",
        "title": "§ 35 VwVfG - Begriff des Verwaltungsakts",
        "content": """§ 35 VwVfG - Begriff des Verwaltungsakts

Verwaltungsakt ist jede Verfügung, Entscheidung oder andere hoheitliche Maßnahme, die eine Behörde zur Regelung eines Einzelfalls auf dem Gebiet des öffentlichen Rechts trifft und die auf unmittelbare Rechtswirkung nach außen gerichtet ist. Allgemeinverfügung ist ein Verwaltungsakt, der sich an einen nach allgemeinen Merkmalen bestimmten oder bestimmbaren Personenkreis richtet oder die öffentlich-rechtliche Eigenschaft einer Sache oder ihre Benutzung durch die Allgemeinheit betrifft.

Praktische Bedeutung: Definition des zentralen Begriffs des Verwaltungsrechts. Alle Verwaltungsentscheidungen folgen diesem Schema.

Beispiel: Ein Baugenehmigungsbescheid ist ein Verwaltungsakt. Ein Verkehrsschild ist eine Allgemeinverfügung.""",
        "metadata": {
            "source": "VwVfG",
            "paragraph": "35",
            "category": "Administrative",
            "topic": "Verwaltungsrecht",
            "keywords": ["Verwaltungsakt", "Behörde", "Einzelfall", "Rechtswirkung"]
        }
    },
    {
        "doc_id": "uwg_3",
        "title": "§ 3 UWG - Verbot unlauterer geschäftlicher Handlungen",
        "content": """§ 3 UWG - Verbot unlauterer geschäftlicher Handlungen

(1) Unlautere geschäftliche Handlungen sind unzulässig.

(2) Geschäftliche Handlungen, die sich an Verbraucher richten oder diese erreichen, sind unlauter, wenn sie nicht der unternehmerischen Sorgfalt entsprechen und dazu geeignet sind, das wirtschaftliche Verhalten des Verbrauchers wesentlich zu beeinflussen.

(3) Die im Anhang dieses Gesetzes aufgeführten geschäftlichen Handlungen gegenüber Verbrauchern sind stets unzulässig.

Praktische Bedeutung: Generalklausel des Wettbewerbsrechts. Schützt Verbraucher und Mitbewerber vor unlauteren Geschäftspraktiken.

Beispiel: Irreführende Werbung oder aggressive Verkaufsmethoden sind unlautere geschäftliche Handlungen.""",
        "metadata": {
            "source": "UWG",
            "paragraph": "3",
            "category": "Legal",
            "topic": "Wettbewerbsrecht",
            "keywords": ["Unlautere Wettbewerb", "Verbraucherschutz", "Geschäftliche Handlung"]
        }
    },
    {
        "doc_id": "umweltg_45",
        "title": "§ 45 Umweltgesetz - Emissionsschutz",
        "content": """§ 45 Umweltgesetz - Emissionsschutz und Grenzwerte

(1) Genehmigungsbedürftige Anlagen sind so zu errichten und zu betreiben, dass zur Gewährleistung eines hohen Schutzniveaus für die Umwelt insgesamt
1. schädliche Umwelteinwirkungen und sonstige Gefahren, erhebliche Nachteile und erhebliche Belästigungen für die Allgemeinheit und die Nachbarschaft nicht hervorgerufen werden können,
2. Vorsorge gegen schädliche Umwelteinwirkungen und sonstige Gefahren, erhebliche Nachteile und erhebliche Belästigungen getroffen wird.

(2) Die Pflichten nach Absatz 1 sind zu erfüllen durch
1. die dem Stand der Technik entsprechende Emissionsbegrenzung,
2. die nach Art und Menge unvermeidlichen Emissionen zu minimieren.

Praktische Bedeutung: Zentrale Norm für Umweltschutz bei industriellen Anlagen. Definiert Emissions-Grenzwerte und Best-Available-Technology Prinzip.

Beispiel: Ein Kraftwerk muss moderne Filter installieren, um CO2- und Stickoxid-Emissionen zu minimieren.""",
        "metadata": {
            "source": "Umweltgesetz",
            "paragraph": "45",
            "category": "Environmental",
            "topic": "Umweltschutz",
            "keywords": ["Emissionen", "Umweltschutz", "Grenzwerte", "Stand der Technik"]
        }
    },
    {
        "doc_id": "stgb_242",
        "title": "§ 242 StGB - Diebstahl",
        "content": """§ 242 StGB - Diebstahl

(1) Wer eine fremde bewegliche Sache einem anderen in der Absicht wegnimmt, die Sache sich oder einem Dritten rechtswidrig zuzueignen, wird mit Freiheitsstrafe bis zu fünf Jahren oder mit Geldstrafe bestraft.

(2) Der Versuch ist strafbar.

Praktische Bedeutung: Grunddelikt des Eigentumsstrafrechts. Schützt das Eigentum an beweglichen Sachen.

Tatbestandsmerkmale:
- Fremd: Die Sache gehört einem anderen
- Beweglich: Kann fortbewegt werden (im Gegensatz zu Grundstücken)
- Wegnehmen: Gewahrsamsbruch
- Zueignungsabsicht: Bereicherungswille

Beispiel: Jemand nimmt im Supermarkt eine Flasche Wasser und verlässt das Geschäft ohne zu bezahlen.""",
        "metadata": {
            "source": "StGB",
            "paragraph": "242",
            "category": "Legal",
            "topic": "Strafrecht",
            "keywords": ["Diebstahl", "Eigentum", "Straftat", "Wegnahme"]
        }
    },
    {
        "doc_id": "gg_1",
        "title": "Art. 1 GG - Menschenwürde",
        "content": """Art. 1 GG - Menschenwürde

(1) Die Würde des Menschen ist unantastbar. Sie zu achten und zu schützen ist Verpflichtung aller staatlichen Gewalt.

(2) Das Deutsche Volk bekennt sich darum zu unverletzlichen und unveräußerlichen Menschenrechten als Grundlage jeder menschlichen Gemeinschaft, des Friedens und der Gerechtigkeit in der Welt.

(3) Die nachfolgenden Grundrechte binden Gesetzgebung, vollziehende Gewalt und Rechtsprechung als unmittelbar geltendes Recht.

Praktische Bedeutung: Höchster Wert der deutschen Verfassung. Die Menschenwürde ist der Kern aller Grundrechte und darf nicht relativiert werden.

Die Menschenwürde schützt:
- Persönlichkeitsrechte
- Verbot entwürdigender Behandlung
- Recht auf selbstbestimmtes Leben
- Schutz vor Objektifizierung

Beispiel: Folter ist mit der Menschenwürde unvereinbar und absolut verboten, selbst in extremen Situationen.""",
        "metadata": {
            "source": "GG",
            "paragraph": "1",
            "category": "Constitutional",
            "topic": "Grundrechte",
            "keywords": ["Menschenwürde", "Grundrechte", "Verfassung", "Schutzpflicht"]
        }
    }
]

async def index_demo_corpus():
    """Indexiert Demo-Corpus in UDS3"""
    print("=" * 80)
    print("UDS3 DEMO CORPUS INDEXIERUNG")
    print("=" * 80)
    print()
    
    try:
        from uds3.uds3_core import get_optimized_unified_strategy
        
        print(f"📊 Demo-Corpus: {len(DEMO_CORPUS)} Dokumente")
        print(f"   • {sum(1 for d in DEMO_CORPUS if d['metadata']['category'] == 'Legal')} Legal")
        print(f"   • {sum(1 for d in DEMO_CORPUS if d['metadata']['category'] == 'Administrative')} Administrative")
        print(f"   • {sum(1 for d in DEMO_CORPUS if d['metadata']['category'] == 'Environmental')} Environmental")
        print(f"   • {sum(1 for d in DEMO_CORPUS if d['metadata']['category'] == 'Constitutional')} Constitutional")
        print()
        
        print("🔄 Initialisiere UDS3...")
        uds3 = get_optimized_unified_strategy()
        print(f"✅ UDS3 Strategy: {uds3.__class__.__name__}")
        print()
        
        # Index Documents
        print("📥 Indexiere Dokumente...")
        
        # Check if we have create_secure_document (UDS3 v3.0 method)
        if hasattr(uds3, 'create_secure_document'):
            for i, doc in enumerate(DEMO_CORPUS, 1):
                try:
                    print(f"   [{i}/{len(DEMO_CORPUS)}] {doc['doc_id']}... ", end="")
                    result = uds3.create_secure_document(
                        file_path=f"demo/{doc['doc_id']}.txt",
                        content=doc['content'],
                        chunks=[doc['content']],  # Single chunk
                        security_level="PUBLIC",
                        metadata=doc['metadata']
                    )
                    print("✅")
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        elif hasattr(uds3, 'db_manager') and uds3.db_manager:
            # Direct vector backend access
            dm = uds3.db_manager
            if hasattr(dm, 'vector_backend') and dm.vector_backend:
                vb = dm.vector_backend
                
                # Prepare data for batch insert
                texts = [doc['content'] for doc in DEMO_CORPUS]
                metadatas = [
                    {
                        "doc_id": doc['doc_id'],
                        "title": doc['title'],
                        **doc['metadata']
                    }
                    for doc in DEMO_CORPUS
                ]
                ids = [doc['doc_id'] for doc in DEMO_CORPUS]
                
                print(f"   🔄 Batch-Insert {len(texts)} Dokumente...")
                
                try:
                    if hasattr(vb, 'collection') and vb.collection:
                        vb.collection.add(
                            documents=texts,
                            metadatas=metadatas,
                            ids=ids
                        )
                        print(f"   ✅ {len(texts)} Dokumente indexiert!")
                    else:
                        print(f"   ❌ Collection nicht verfügbar")
                except Exception as e:
                    print(f"   ❌ Batch-Insert Error: {e}")
                    # Try one-by-one
                    print(f"   🔄 Fallback: Einzeln indexieren...")
                    for i, doc in enumerate(DEMO_CORPUS, 1):
                        try:
                            print(f"   [{i}/{len(DEMO_CORPUS)}] {doc['doc_id']}... ", end="")
                            vb.collection.add(
                                documents=[doc['content']],
                                metadatas=[{
                                    "doc_id": doc['doc_id'],
                                    "title": doc['title'],
                                    **doc['metadata']
                                }],
                                ids=[doc['doc_id']]
                            )
                            print("✅")
                        except Exception as e:
                            print(f"❌ {e}")
            else:
                print(f"   ❌ Vector Backend nicht verfügbar")
                return False
        else:
            print(f"   ❌ Keine Index-Methode gefunden")
            print(f"   📝 Verfügbare Methoden: {[m for m in dir(uds3) if not m.startswith('_')]}")
            return False
        
        print()
        print("=" * 80)
        print("✅ INDEXIERUNG ABGESCHLOSSEN")
        print("=" * 80)
        print()
        
        # Verify
        print("🔍 Verifikation...")
        if hasattr(uds3.db_manager, 'vector_backend') and uds3.db_manager.vector_backend:
            if hasattr(uds3.db_manager.vector_backend, 'collection'):
                count = uds3.db_manager.vector_backend.collection.count()
                print(f"   📄 Vector DB enthält jetzt: {count} Dokumente")
                
                if count >= len(DEMO_CORPUS):
                    print(f"   ✅ Alle Dokumente erfolgreich indexiert!")
                    print()
                    print("➡️ Sie können jetzt Phase 5 testen:")
                    print("   1. Staging Phase 1 deployen: .\\scripts\\deploy_staging_phase1.ps1")
                    print("   2. Backend starten: python start_backend.py")
                    print("   3. Test-Query: BGB Vertragsrecht, Verwaltungsakt, Umweltschutz")
                    return True
                else:
                    print(f"   ⚠️ Nur {count}/{len(DEMO_CORPUS)} Dokumente indexiert")
                    return False
        
        return True
        
    except ImportError as e:
        print(f"❌ UDS3 Import-Fehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(index_demo_corpus())
    sys.exit(0 if result else 1)
