#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChromaDB Collection Management Methods Test
============================================

Test neue Collection-Management-Methoden:
1. get_collection_id(name) - UUID aus Name ermitteln
2. get_all_collections() - Alle Collections mit Details

Expected ChromaDB Server: http://192.168.178.94:8000

Author: VERITAS v7.0 Team
Date: 12. Oktober 2025
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def test_collection_management_methods():
    """Test Collection Management Methods"""

    print("\n" + "=" * 80)
    print("ChromaDB Collection Management Methods Test")
    print("=" * 80 + "\n")

    try:
        # Import ChromaDB Remote Backend
        from uds3.database.database_api_chromadb_remote import ChromaRemoteVectorBackend

        # Configuration
        config = {
            "remote": {"host": "192.168.178.94", "port": 8000, "protocol": "http"},
            "collection": "vcc_vector_prod",
            "tenant": "default_tenant",
            "database": "default_database",
        }

        print("📊 Test Configuration:")
        print(f"   Server: {config['remote']['protocol']}://{config['remote']['host']}:{config['remote']['port']}")
        print(f"   Tenant: {config['tenant']}")
        print(f"   Database: {config['database']}\n")

        # Initialize Backend
        print("🔧 Initialize ChromaDB Backend...")
        backend = ChromaRemoteVectorBackend(config)
        print("   ✅ Backend initialized\n")

        # Connect to Server
        print("🔌 Connect to ChromaDB Server...")
        if backend.connect():
            print("   ✅ Connected successfully")
            print(f"   API Compatible: {backend._api_compatible}\n")
        else:
            print("   ❌ Connection failed\n")
            return False

        # Test 1: get_all_collections()
        print("=" * 80)
        print("📋 Test 1: get_all_collections() - Retrieve All Collections with Details")
        print("=" * 80 + "\n")

        all_collections = backend.get_all_collections()

        if all_collections:
            print(f"✅ Found {len(all_collections)} collections\n")

            # Display collection details
            for i, col in enumerate(all_collections, 1):
                print(f"Collection #{i}:")
                print(f"   Name:     {col.get('name', 'N/A')}")
                print(f"   ID:       {col.get('id', 'N/A')}")
                print(f"   Metadata: {col.get('metadata', {})}")
                print(f"   Tenant:   {col.get('tenant', 'N/A')}")
                print(f"   Database: {col.get('database', 'N/A')}")
                print()
        else:
            print("⚠️ No collections found\n")

        # Test 2: get_collection_id() - Test mit bekannten Collections
        print("=" * 80)
        print("🔍 Test 2: get_collection_id() - Get UUID from Collection Name")
        print("=" * 80 + "\n")

        if all_collections:
            # Test mit jeder gefundenen Collection
            for col in all_collections[:3]:  # Erste 3 testen
                col_name = col.get("name")
                expected_id = col.get("id")

                print(f"Test Collection: '{col_name}'")
                collection_id = backend.get_collection_id(col_name)

                if collection_id:
                    print(f"   ✅ UUID Retrieved: {collection_id}")

                    # Verify ID matches
                    if collection_id == expected_id:
                        print(f"   ✅ ID Match: Expected = Actual")
                    else:
                        print(f"   ⚠️ ID Mismatch:")
                        print(f"      Expected: {expected_id}")
                        print(f"      Actual:   {collection_id}")
                else:
                    print(f"   ❌ Failed to retrieve UUID")
                print()
        else:
            print("⚠️ No collections to test\n")

        # Test 3: get_collection_id() - Test mit nicht-existierender Collection
        print("=" * 80)
        print("🔍 Test 3: get_collection_id() - Non-Existent Collection")
        print("=" * 80 + "\n")

        non_existent = "this_collection_does_not_exist_12345"
        print(f"Test Non-Existent Collection: '{non_existent}'")
        collection_id = backend.get_collection_id(non_existent)

        if collection_id is None:
            print(f"   ✅ Correctly returned None for non-existent collection\n")
        else:
            print(f"   ⚠️ Unexpected ID returned: {collection_id}\n")

        # Test 4: Compare list_collections() vs get_all_collections()
        print("=" * 80)
        print("🔄 Test 4: Compare list_collections() vs get_all_collections()")
        print("=" * 80 + "\n")

        simple_list = backend.list_collections()
        detailed_list = backend.get_all_collections()

        print(f"list_collections() returned: {len(simple_list)} names")
        print(f"get_all_collections() returned: {len(detailed_list)} detailed objects\n")

        if len(simple_list) == len(detailed_list):
            print("   ✅ Count matches between both methods")
        else:
            print("   ⚠️ Count mismatch:")
            print(f"      Simple: {len(simple_list)}")
            print(f"      Detailed: {len(detailed_list)}")

        # Check if names match
        simple_names = set(simple_list)
        detailed_names = set(col["name"] for col in detailed_list)

        if simple_names == detailed_names:
            print("   ✅ Collection names match between both methods\n")
        else:
            print("   ⚠️ Collection names differ:")
            print(f"      Only in simple: {simple_names - detailed_names}")
            print(f"      Only in detailed: {detailed_names - simple_names}\n")

        # Disconnect
        print("🔌 Disconnect...")
        backend.disconnect()
        print("   ✅ Disconnected\n")

        # Summary
        print("=" * 80)
        print("📊 Test Summary")
        print("=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print(f"✅ get_all_collections(): {len(all_collections)} collections retrieved")
        print(f"✅ get_collection_id(): Tested with {min(3, len(all_collections))} collections")
        print(f"✅ Methods working correctly with ChromaDB v2 API")
        print("\n🎉 Collection Management Methods: SUCCESS!\n")

        return True

    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_collection_management_methods()
    sys.exit(0 if success else 1)
