"""
API v3 Integration Test Script

Testet die API v3 Module und Integration.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    print("🔧 Teste API v3 Imports...")

    # Test Base Module
    from backend.api.v3 import api_v3_router, get_v3_info

    print("✅ Base Module importiert")

    # Test Router Module
    from backend.api.v3.agent_router import agent_router
    from backend.api.v3.query_router import query_router
    from backend.api.v3.system_router import system_router

    print("✅ Router Module importiert")

    # Test Models
    from backend.api.v3.models import AgentInfo, QueryRequest, QueryResponse, SystemHealth

    print("✅ Pydantic Models importiert")

    # Get API Info
    info = get_v3_info()
    print("\n📊 API v3 Info:")
    print(f"   Version: {info['version']}")
    print(f"   Status: {info['status']}")
    print(f"   Modules: {len(info['modules'])}")
    print(f"   Base Path: {info['base_path']}")

    # Test Model Creation
    query_req = QueryRequest(query="Test Query", mode="veritas", model="llama3.2")
    print(f"\n✅ QueryRequest erstellt: mode={query_req.mode}, model={query_req.model}")

    print("\n🎉 API v3 Integration Test erfolgreich!")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ Fehler: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
