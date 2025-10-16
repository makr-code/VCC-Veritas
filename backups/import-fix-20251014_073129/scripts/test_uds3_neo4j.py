"""
UDS3 Neo4j Backend Test - via UDS3 API
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from uds3.uds3_core import get_optimized_unified_strategy

def main():
    print("=" * 80)
    print("🧪 UDS3 Neo4j Backend Test")
    print("=" * 80)
    
    # Get Neo4j backend via UDS3
    strategy = get_optimized_unified_strategy()
    neo = strategy.graph_backend
    
    # Test 1: Count all Document nodes
    print("\n1️⃣ Count all Document nodes:")
    cypher = "MATCH (d:Document) RETURN count(d) as count"
    result = neo.execute_query(cypher, {})
    print(f"   Result Type: {type(result)}")
    print(f"   Result: {result}")
    if result:
        print(f"   ✅ Found {result[0].get('count', 0)} Document nodes")
    
    # Test 2: Get all Document nodes
    print("\n2️⃣ Get all Document nodes:")
    cypher = "MATCH (d:Document) RETURN d LIMIT 5"
    result = neo.execute_query(cypher, {})
    print(f"   Result count: {len(result) if result else 0}")
    if result:
        for idx, record in enumerate(result):
            print(f"\n   Record {idx+1}:")
            print(f"     Type: {type(record)}")
            print(f"     Keys: {record.keys() if hasattr(record, 'keys') else 'N/A'}")
            print(f"     Data: {record}")
            
            # Try different access methods
            if hasattr(record, 'get'):
                node = record.get('d', {})
            elif hasattr(record, '__getitem__'):
                try:
                    node = record['d']
                except:
                    node = record[0] if len(record) > 0 else {}
            else:
                node = {}
            
            print(f"     Node: {node}")
            if hasattr(node, 'get'):
                print(f"     - ID: {node.get('id', 'NO_ID')}")
                print(f"     - Name: {node.get('name', 'NO_NAME')}")
    
    # Test 3: Search with WHERE clause
    print("\n3️⃣ Search with WHERE clause (Photovoltaik):")
    cypher = """
    MATCH (d:Document)
    WHERE toLower(d.content) CONTAINS toLower($query)
       OR toLower(d.name) CONTAINS toLower($query)
    RETURN d
    LIMIT 5
    """
    params = {'query': 'Photovoltaik'}
    result = neo.execute_query(cypher, params)
    print(f"   Result count: {len(result) if result else 0}")
    if result:
        for record in result:
            # Handle different record types
            if hasattr(record, 'get'):
                node = record.get('d', {})
            elif hasattr(record, '__getitem__'):
                node = record[0] if len(record) > 0 else {}
            else:
                node = record
                
            if hasattr(node, 'get'):
                print(f"   - {node.get('id', 'NO_ID')}: {node.get('name', 'NO_NAME')}")
                content = node.get('content', '')
                if content:
                    print(f"     Content: {content[:100]}...")
            else:
                print(f"   - Node type not recognized: {type(node)}")
    else:
        print("   ❌ No results found")
    
    print("\n" + "=" * 80)
    print("✅ Neo4j test complete")
    print("=" * 80)

if __name__ == "__main__":
    main()
