#!/usr/bin/env python3
"""
Direct Neo4j Connection Test
Testet direkt die Neo4j-Verbindung und zeigt vorhandene Nodes/Relationships
"""

try:
    from neo4j import GraphDatabase
except ImportError:
    print("❌ neo4j-Paket nicht installiert!")
    print("   Installieren mit: pip install neo4j")
    exit(1)

def test_neo4j_connection():
    """Test Neo4j connection and show available data"""
    print("=" * 80)
    print("NEO4J CONNECTION TEST (Direct)")
    print("=" * 80)
    print()
    
    # Connection parameters from config.py
    uri = "neo4j://192.168.178.94:7687"
    username = "neo4j"
    password = "v3f3b1d7"
    
    try:
        print(f"🔌 Verbinde zu Neo4j: {uri}")
        print(f"   User: {username}")
        print()
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            # Test connection
            result = session.run("RETURN 1 AS num")
            record = result.single()
            
            if record and record["num"] == 1:
                print("✅ Verbindung erfolgreich!")
                print()
            
            # 1. Count all nodes
            print("📊 Datenbank-Statistiken:")
            result = session.run("MATCH (n) RETURN count(n) AS total_nodes")
            total_nodes = result.single()["total_nodes"]
            print(f"   - Total Nodes: {total_nodes:,}")
            
            # 2. Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS total_rels")
            total_rels = result.single()["total_rels"]
            print(f"   - Total Relationships: {total_rels:,}")
            print()
            
            # 3. Show node labels
            print("🏷️  Node Labels:")
            result = session.run("CALL db.labels()")
            labels = [record["label"] for record in result]
            
            if labels:
                for label in sorted(labels):
                    # Count nodes for each label
                    count_result = session.run(f"MATCH (n:{label}) RETURN count(n) AS count")
                    count = count_result.single()["count"]
                    print(f"   - {label}: {count:,} Nodes")
            else:
                print("   ⚠️  Keine Labels gefunden!")
            print()
            
            # 4. Show relationship types
            print("🔗 Relationship Types:")
            result = session.run("CALL db.relationshipTypes()")
            rel_types = [record["relationshipType"] for record in result]
            
            if rel_types:
                for rel_type in sorted(rel_types):
                    # Count relationships for each type
                    count_result = session.run(
                        f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count"
                    )
                    count = count_result.single()["count"]
                    print(f"   - {rel_type}: {count:,} Relationships")
            else:
                print("   ⚠️  Keine Relationship Types gefunden!")
            print()
            
            # 5. Search for BGB/Gesetz nodes
            print("🔍 Suche nach BGB/Gesetz-bezogenen Nodes:")
            search_queries = [
                ("BGB", "MATCH (n) WHERE n.title CONTAINS 'BGB' OR n.name CONTAINS 'BGB' RETURN n LIMIT 5"),
                ("Taschengeld", "MATCH (n) WHERE n.title CONTAINS 'Taschengeld' OR n.content CONTAINS 'Taschengeld' RETURN n LIMIT 5"),
                ("Gesetz", "MATCH (n) WHERE n.title CONTAINS 'Gesetz' OR n.name CONTAINS 'Gesetz' RETURN n LIMIT 5"),
                ("§ 110", "MATCH (n) WHERE n.title CONTAINS '110' OR n.paragraph = '110' RETURN n LIMIT 5"),
            ]
            
            for search_term, query in search_queries:
                try:
                    result = session.run(query)
                    records = list(result)
                    if records:
                        print(f"   ✅ '{search_term}': {len(records)} Treffer")
                        # Show first result details
                        first_node = records[0]["n"]
                        node_labels = list(first_node.labels)
                        props = dict(first_node)
                        print(f"      Beispiel: {node_labels}, Props: {list(props.keys())[:5]}")
                    else:
                        print(f"   ❌ '{search_term}': 0 Treffer")
                except Exception as search_e:
                    print(f"   ⚠️  '{search_term}': Query fehlgeschlagen ({search_e})")
            
            # 6. Show sample nodes
            if total_nodes > 0:
                print("\n📄 Beispiel-Nodes (erste 5):")
                result = session.run("MATCH (n) RETURN n LIMIT 5")
                for i, record in enumerate(result, 1):
                    node = record["n"]
                    labels = list(node.labels)
                    props = dict(node)
                    # Show first few properties
                    prop_preview = {k: str(v)[:50] for k, v in list(props.items())[:3]}
                    print(f"   {i}. {labels}: {prop_preview}")
        
        driver.close()
        
        print()
        print("=" * 80)
        print("TEST ABGESCHLOSSEN")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_neo4j_connection()
