#!/usr/bin/env python3
"""
Test UDS3 Database Backends Connection

Tests whether UDS3 backends (ChromaDB, Neo4j, PostgreSQL) are connected.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "uds3"))

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("="*80)
print("VERITAS UDS3 Database Backends Test")
print("="*80)
print()

# Import UDS3
print("→ Importing UDS3...")
from uds3_core import UnifiedDatabaseStrategy

try:
    # Initialize UDS3
    print("→ Initializing UDS3...")
    uds3 = UnifiedDatabaseStrategy(
        strict_quality=False,
        enforce_governance=False,
        enable_dynamic_naming=True
    )
    print("✅ UDS3 initialized")
    print()
    
    # Check database manager
    print("→ Checking database manager...")
    manager = uds3._resolve_database_manager()
    print(f"✅ Database Manager: {type(manager).__name__}")
    print()
    
    # Check backends
    print("="*80)
    print("Backend Status:")
    print("="*80)
    print()
    
    # Vector Backend
    print("→ Vector Backend (ChromaDB):")
    if hasattr(manager, 'vector_backend') and manager.vector_backend:
        print(f"   ✅ Connected: {type(manager.vector_backend).__name__}")
        # Try to get backend info
        try:
            if hasattr(manager.vector_backend, 'is_connected'):
                is_connected = manager.vector_backend.is_connected()
                print(f"   Connection Status: {is_connected}")
        except Exception as e:
            print(f"   ⚠️  Connection check failed: {e}")
    else:
        print("   ❌ Not available")
        # Try to start backend
        print("   → Attempting to start backend...")
        try:
            if hasattr(manager, 'start_all_backends'):
                manager.start_all_backends()
                print("   ✅ Backends started")
            elif hasattr(manager, '_backend_factories'):
                print(f"   Backend factories: {list(manager._backend_factories.keys())}")
        except Exception as e:
            print(f"   ❌ Start failed: {e}")
    print()
    
    # Graph Backend
    print("→ Graph Backend (Neo4j):")
    if hasattr(manager, 'graph_backend') and manager.graph_backend:
        print(f"   ✅ Connected: {type(manager.graph_backend).__name__}")
    else:
        print("   ❌ Not available")
    print()
    
    # Relational Backend
    print("→ Relational Backend (PostgreSQL):")
    if hasattr(manager, 'relational_backend') and manager.relational_backend:
        print(f"   ✅ Connected: {type(manager.relational_backend).__name__}")
    else:
        print("   ❌ Not available")
    print()
    
    # File Backend
    print("→ File Backend (CouchDB):")
    if hasattr(manager, 'file_backend') and manager.file_backend:
        print(f"   ✅ Connected: {type(manager.file_backend).__name__}")
    else:
        print("   ❌ Not available")
    print()
    
    # Inspect manager attributes
    print("="*80)
    print("Database Manager Attributes:")
    print("="*80)
    print()
    attrs = [attr for attr in dir(manager) if not attr.startswith('_')]
    print(f"Total attributes: {len(attrs)}")
    print()
    backend_attrs = [attr for attr in attrs if 'backend' in attr.lower()]
    print(f"Backend-related: {backend_attrs}")
    print()
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("Test Complete")
print("="*80)
