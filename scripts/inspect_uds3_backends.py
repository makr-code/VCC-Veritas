"""
UDS3 Backend Introspection Script

Prints available methods and attributes of UDS3 backends.
"""

import sys
from pathlib import Path

# Add UDS3 to path
uds3_path = Path("c:/VCC/uds3")
if uds3_path.exists():
    sys.path.insert(0, str(uds3_path))

from uds3.uds3_core import get_optimized_unified_strategy

# Get strategy
strategy = get_optimized_unified_strategy()

print("=" * 80)
print("🔍 UDS3 Backend Introspection")
print("=" * 80)

# PostgreSQL Backend
if strategy.relational_backend:
    print("\n📊 PostgreSQL Backend (relational_backend):")
    print(f"  Type: {type(strategy.relational_backend)}")
    print(f"  Module: {type(strategy.relational_backend).__module__}")
    
    print("\n  Available Methods:")
    for attr in dir(strategy.relational_backend):
        if not attr.startswith('_') and callable(getattr(strategy.relational_backend, attr)):
            print(f"    - {attr}()")
else:
    print("\n❌ PostgreSQL Backend not available")

# Neo4j Backend
if strategy.graph_backend:
    print("\n🕸️  Neo4j Backend (graph_backend):")
    print(f"  Type: {type(strategy.graph_backend)}")
    print(f"  Module: {type(strategy.graph_backend).__module__}")
    
    print("\n  Available Methods:")
    for attr in dir(strategy.graph_backend):
        if not attr.startswith('_') and callable(getattr(strategy.graph_backend, attr)):
            print(f"    - {attr}()")
else:
    print("\n❌ Neo4j Backend not available")

# ChromaDB Backend
if strategy.vector_backend:
    print("\n🔢 ChromaDB Backend (vector_backend):")
    print(f"  Type: {type(strategy.vector_backend)}")
    print(f"  Module: {type(strategy.vector_backend).__module__}")
    
    print("\n  Available Methods:")
    for attr in dir(strategy.vector_backend):
        if not attr.startswith('_') and callable(getattr(strategy.vector_backend, attr)):
            print(f"    - {attr}()")
else:
    print("\n❌ ChromaDB Backend not available")

print("\n" + "=" * 80)
