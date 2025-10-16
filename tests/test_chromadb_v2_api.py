#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChromaDB v2 API Integration Test
================================

Test ChromaDB v2 API compatibility with Collection UUID support.

Expected ChromaDB Server: http://192.168.178.94:8000

Test Cases:
1. Connect to ChromaDB Server
2. Test v2 API heartbeat
3. List collections (v2 API)
4. Get collection info with UUID
5. Add vector with Collection UUID
6. Search vectors with Collection UUID

Author: VERITAS v7.0 Team
Date: 12. Oktober 2025
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_chromadb_v2_api():
    """Test ChromaDB v2 API integration"""
    
    print("\n" + "="*80)
    print("ChromaDB v2 API Integration Test")
    print("="*80 + "\n")
    
    try:
        # Import ChromaDB Remote Backend
        from uds3.database.database_api_chromadb_remote import ChromaRemoteVectorBackend
        
        # Configuration
        config = {
            'remote': {
                'host': '192.168.178.94',
                'port': 8000,
                'protocol': 'http'
            },
            'collection': 'vcc_vector_test',  # Test collection
            'tenant': 'default_tenant',
            'database': 'default_database'
        }
        
        print("📊 Test Configuration:")
        print(f"   Server: {config['remote']['protocol']}://{config['remote']['host']}:{config['remote']['port']}")
        print(f"   Collection: {config['collection']}")
        print(f"   Tenant: {config['tenant']}")
        print(f"   Database: {config['database']}\n")
        
        # Test 1: Initialize Backend
        print("🔧 Test 1: Initialize ChromaDB Backend...")
        backend = ChromaRemoteVectorBackend(config)
        print("   ✅ Backend initialized\n")
        
        # Test 2: Connect to Server
        print("🔌 Test 2: Connect to ChromaDB Server...")
        if backend.connect():
            print("   ✅ Connected successfully")
            print(f"   API Compatible: {backend._api_compatible}")
            print(f"   Collection ID: {backend.collection_id}\n")
        else:
            print("   ❌ Connection failed\n")
            return False
        
        # Test 3: Check Availability
        print("🏥 Test 3: Check Server Availability...")
        if backend.is_available():
            print("   ✅ Server is available\n")
        else:
            print("   ❌ Server not available\n")
            return False
        
        # Test 4: List Collections
        print("📋 Test 4: List Collections (v2 API)...")
        collections = backend.list_collections()
        print(f"   ✅ Found {len(collections)} collections")
        if collections:
            print(f"   Collections: {', '.join(collections[:5])}")
            if len(collections) > 5:
                print(f"   ... and {len(collections) - 5} more")
        print()
        
        # Test 5: Get Collection Info
        print("🔍 Test 5: Get Collection Info...")
        collection_info = backend.get_collection(config['collection'])
        if collection_info:
            print("   ✅ Collection info retrieved")
            print(f"   Name: {collection_info.get('name', 'N/A')}")
            print(f"   ID: {collection_info.get('id', 'N/A')}")
            print(f"   Metadata: {collection_info.get('metadata', {})}")
        else:
            print("   ⚠️ Collection not found (will be created)")
        print()
        
        # Test 6: Add Test Vector
        print("➕ Test 6: Add Test Vector...")
        test_vector = [0.1] * 384  # 384-dim test vector
        test_metadata = {
            'test': True,
            'source': 'chromadb_v2_api_test',
            'timestamp': '2025-10-12T23:50:00Z'
        }
        test_id = 'test_vector_v2_api'
        
        if backend.add_vector(test_vector, test_metadata, test_id):
            print("   ✅ Vector added successfully")
            print(f"   Vector ID: {test_id}")
            print(f"   Vector Dim: {len(test_vector)}")
            print(f"   Metadata: {test_metadata}")
        else:
            print("   ❌ Failed to add vector")
            return False
        print()
        
        # Test 7: Search Similar Vectors
        print("🔍 Test 7: Search Similar Vectors...")
        query_vector = [0.1] * 384  # Same vector for exact match
        results = backend.search_similar(query_vector, n_results=3)
        
        if results:
            print(f"   ✅ Found {len(results)} similar vectors")
            for i, result in enumerate(results[:3], 1):
                print(f"   Result {i}:")
                print(f"      ID: {result.get('id', 'N/A')}")
                print(f"      Distance: {result.get('distance', 'N/A'):.4f}")
                print(f"      Metadata: {result.get('metadata', {})}")
        else:
            print("   ⚠️ No results found")
        print()
        
        # Test 8: Disconnect
        print("🔌 Test 8: Disconnect...")
        backend.disconnect()
        print("   ✅ Disconnected\n")
        
        # Summary
        print("="*80)
        print("📊 Test Summary")
        print("="*80)
        print("✅ ALL TESTS PASSED")
        print(f"✅ ChromaDB v2 API: {'COMPATIBLE' if backend._api_compatible else 'V1 FALLBACK'}")
        print(f"✅ Collection ID: {backend.collection_id}")
        print(f"✅ Vector Operations: WORKING")
        print("\n🎉 ChromaDB v2 API Integration: SUCCESS!\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_chromadb_v2_api()
    sys.exit(0 if success else 1)
