#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick ChromaDB Collection Check
================================
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from uds3.database.database_api_chromadb_remote import ChromaRemoteVectorBackend

config = {
    'remote': {'host': '192.168.178.94', 'port': 8000},
    'collection': 'vcc_vector_prod',
    'tenant': 'default_tenant',
    'database': 'default_database'
}

backend = ChromaRemoteVectorBackend(config)
backend.connect()

print("\n=== ChromaDB Collections ===")
collections = backend.get_all_collections()
for col in collections:
    print(f"  - {col['name']} (ID: {col['id']})")

print(f"\nTotal: {len(collections)} collections")
print("\nTrying to create vcc_vector_prod...")

try:
    success = backend.create_collection('vcc_vector_prod', metadata={'created_by': 'veritas', 'version': '1.0'})
    if success:
        print("✅ Collection created successfully!")
        new_id = backend.get_collection_id('vcc_vector_prod')
        print(f"   UUID: {new_id}")
    else:
        print("❌ Collection creation failed")
except Exception as e:
    print(f"❌ Error: {e}")
