"""
Quick Demo Data Indexer for UDS3
Creates sample documents to test hybrid search
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from uds3.uds3_core import get_optimized_unified_strategy

def create_demo_documents():
    """Create sample building regulation documents"""
    return [
        {
            "id": "lbo_bw_58",
            "content": "§ 58 LBO BW regelt die Anforderungen an Photovoltaik-Anlagen auf Gebäuden. Photovoltaik-Anlagen müssen auf Dächern von Wohngebäuden installiert werden, sofern dies technisch möglich und wirtschaftlich zumutbar ist.",
            "name": "LBO BW § 58 Photovoltaik",
            "document_type": "regulation",
            "classification": "Erneuerbare Energien",
            "source": "demo",
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "lbo_bw_5",
            "content": "§ 5 LBO BW definiert die Abstandsflächenregelungen für Gebäude. Die Tiefe der Abstandsflächen beträgt mindestens 0,4 H, mindestens aber 3 m.",
            "name": "LBO BW § 5 Abstandsflächen",
            "document_type": "regulation",
            "classification": "Bauordnungsrecht",
            "source": "demo",
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "lbo_bw_6",
            "content": "§ 6 LBO BW regelt die Teilungsgenehmigung bei Grundstücksteilungen. Eine Teilungsgenehmigung ist erforderlich, wenn durch die Teilung ein Grundstück entsteht, das die bauplanungsrechtlichen Anforderungen nicht erfüllt.",
            "name": "LBO BW § 6 Teilungsgenehmigung",
            "document_type": "regulation",
            "classification": "Bauplanungsrecht",
            "source": "demo",
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "energiegesetz_bw_2023",
            "content": "Das Energiegesetz Baden-Württemberg 2023 verpflichtet zur Installation von Photovoltaik-Anlagen bei Neubauten und grundlegenden Dachsanierungen. Dies gilt für Wohn- und Nichtwohngebäude.",
            "name": "Energiegesetz BW 2023",
            "document_type": "regulation",
            "classification": "Erneuerbare Energien",
            "source": "demo",
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "brandschutz_richtlinie_2024",
            "content": "Die Brandschutzrichtlinie 2024 definiert Anforderungen an Rettungswege, Feuerwiderstandsklassen und Brandmeldesysteme in Gebäuden ab 7m Höhe.",
            "name": "Brandschutzrichtlinie 2024",
            "document_type": "guideline",
            "classification": "Brandschutz",
            "source": "demo",
            "created_at": datetime.now().isoformat()
        }
    ]

def index_to_neo4j(strategy, documents):
    """Index documents to Neo4j graph database"""
    print("\n🕸️  Indexing to Neo4j...")
    neo = strategy.graph_backend
    
    indexed_count = 0
    for doc in documents:
        try:
            # Create Document node
            node_props = {
                'id': doc['id'],
                'name': doc['name'],
                'content': doc['content'],
                'document_type': doc['document_type'],
                'classification': doc['classification'],
                'source': doc['source'],
                'created_at': doc['created_at']
            }
            
            neo.create_node('Document', node_props)
            indexed_count += 1
            print(f"  ✅ {doc['id']}")
            
        except Exception as e:
            print(f"  ❌ {doc['id']}: {e}")
    
    print(f"\n  Indexed {indexed_count}/{len(documents)} documents to Neo4j")
    
    # Create some relationships
    print("\n  Creating relationships...")
    try:
        # Link PV-related documents
        cypher = """
        MATCH (d1:Document {id: 'lbo_bw_58'})
        MATCH (d2:Document {id: 'energiegesetz_bw_2023'})
        CREATE (d1)-[:RELATED_TO {type: 'similar_topic'}]->(d2)
        """
        neo.execute_query(cypher, {})
        print("  ✅ Created PV relationship")
        
        # Link building regulation documents
        cypher = """
        MATCH (d1:Document {id: 'lbo_bw_5'})
        MATCH (d2:Document {id: 'lbo_bw_6'})
        CREATE (d1)-[:RELATED_TO {type: 'same_law'}]->(d2)
        """
        neo.execute_query(cypher, {})
        print("  ✅ Created LBO relationship")
        
    except Exception as e:
        print(f"  ⚠️  Relationships: {e}")

def index_to_chromadb(strategy, documents):
    """Index documents to ChromaDB vector database using sentence-transformers"""
    print("\n🔢 Indexing to ChromaDB...")
    
    try:
        # Use sentence-transformers for proper embeddings
        from sentence_transformers import SentenceTransformer
        
        chroma = strategy.vector_backend
        
        # Load embedding model (same as used in queries)
        print("  Loading embedding model (all-MiniLM-L6-v2)...")
        model = SentenceTransformer('all-MiniLM-L6-v2')  # 384D embeddings
        
        # Generate embeddings for all documents
        contents = [doc['content'] for doc in documents]
        print(f"  Generating embeddings for {len(contents)} documents...")
        embeddings = model.encode(contents)
        
        # Add documents to ChromaDB
        indexed_count = 0
        for doc, embedding in zip(documents, embeddings):
            try:
                metadata = {
                    'name': doc['name'],
                    'document_type': doc['document_type'],
                    'classification': doc['classification'],
                    'source': doc['source'],
                    'content': doc['content']  # Store content in metadata
                }
                
                # ChromaDB add_vector API (discovered via introspection)
                # Signature: add_vector(vector, metadata, doc_id, collection=None)
                success = chroma.add_vector(
                    vector=embedding.tolist(),
                    metadata=metadata,
                    doc_id=doc['id'],
                    collection='veritas_demo'  # Use dedicated demo collection
                )
                
                if success:
                    indexed_count += 1
                    print(f"  ✅ {doc['id']}")
                else:
                    print(f"  ⚠️  {doc['id']}: add_vector returned False")
                
            except Exception as e:
                print(f"  ❌ {doc['id']}: {e}")
        
        print(f"\n  Indexed {indexed_count}/{len(documents)} documents to ChromaDB")
        
    except ImportError:
        print(f"  ❌ sentence-transformers not installed!")
        print(f"     Run: pip install sentence-transformers")
    except ImportError:
        print(f"  ❌ sentence-transformers not installed!")
        print(f"     Run: pip install sentence-transformers")
    except Exception as e:
        print(f"  ❌ ChromaDB indexing failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("=" * 80)
    print("📚 UDS3 Demo Data Indexer")
    print("=" * 80)
    
    # Create demo documents
    print("\n📄 Creating demo documents...")
    documents = create_demo_documents()
    print(f"  Created {len(documents)} sample documents")
    
    # Initialize UDS3
    print("\n🔄 Initializing UDS3...")
    strategy = get_optimized_unified_strategy()
    print("  ✅ UDS3 Strategy initialized")
    
    # Index to Neo4j
    index_to_neo4j(strategy, documents)
    
    # Index to ChromaDB
    index_to_chromadb(strategy, documents)
    
    print("\n" + "=" * 80)
    print("✅ Demo data indexed successfully!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Run: python scripts/test_uds3_hybrid.py")
    print("  2. Should now return results from Neo4j + ChromaDB")

if __name__ == "__main__":
    main()
