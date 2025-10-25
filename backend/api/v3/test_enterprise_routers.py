"""
VERITAS API v3 - Enterprise Router Test Script
===============================================

Testet alle Enterprise-Router (SAGA, Compliance, Governance) auf:
- Modul-Imports
- Pydantic Model Validierung
- Router-Konfiguration
- Endpoint-Verfügbarkeit

Author: VERITAS API v3
Version: 3.0.0
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_enterprise_router_imports():
    """Teste Enterprise-Router Imports"""
    print("🔧 Teste Enterprise-Router Imports...")
    
    try:
        # SAGA Router
        from backend.api.v3.saga_router import saga_router
        print("   ✅ SAGA Router importiert")
        
        # Compliance Router
        from backend.api.v3.compliance_router import compliance_router
        print("   ✅ Compliance Router importiert")
        
        # Governance Router
        from backend.api.v3.governance_router import governance_router
        print("   ✅ Governance Router importiert")
        
        return True
    except ImportError as e:
        print(f"   ❌ Import fehlgeschlagen: {e}")
        return False


def test_enterprise_models():
    """Teste Enterprise-Pydantic Models"""
    print("\n🔧 Teste Enterprise-Pydantic Models...")
    
    try:
        from backend.api.v3.models import (
            # SAGA Models
            SAGAOrchestrationRequest,
            SAGAStatus,
            SAGAStep,
            
            # Compliance Models
            ComplianceCheckRequest,
            ComplianceCheckResponse,
            ComplianceViolation,
            
            # Governance Models
            DataLineageRequest,
            DataLineageResponse,
            DataGovernancePolicy
        )
        print("   ✅ Alle Enterprise-Models importiert")
        
        # Test SAGA Model Creation
        saga_step = SAGAStep(
            step_id="step_1",
            service="test_service",
            action="test_action",
            parameters={"key": "value"}
        )
        print(f"   ✅ SAGAStep erstellt: step_id='{saga_step.step_id}', service={saga_step.service}")
        
        # Test Compliance Model Creation
        compliance_req = ComplianceCheckRequest(
            entity_type="document",
            entity_id="doc_123",
            rules=["GDPR", "DSGVO"]
        )
        print(f"   ✅ ComplianceCheckRequest erstellt: entity_type='{compliance_req.entity_type}', rules={compliance_req.rules}")
        
        # Test Governance Model Creation
        lineage_req = DataLineageRequest(
            entity_id="dataset_123",
            depth=3,
            direction="both"
        )
        print(f"   ✅ DataLineageRequest erstellt: entity_id='{lineage_req.entity_id}', depth={lineage_req.depth}")
        
        return True
    except Exception as e:
        print(f"   ❌ Model-Test fehlgeschlagen: {e}")
        return False


def test_router_endpoints():
    """Teste Router-Endpoint Konfiguration"""
    print("\n📊 Teste Router-Endpoints...")
    
    try:
        from backend.api.v3.saga_router import saga_router
        from backend.api.v3.compliance_router import compliance_router
        from backend.api.v3.governance_router import governance_router
        
        # SAGA Endpoints
        saga_endpoints = [route.path for route in saga_router.routes]
        print(f"\n   📌 SAGA Router ({len(saga_endpoints)} Endpoints):")
        for endpoint in saga_endpoints:
            print(f"      - {endpoint}")
        
        # Compliance Endpoints
        compliance_endpoints = [route.path for route in compliance_router.routes]
        print(f"\n   📌 Compliance Router ({len(compliance_endpoints)} Endpoints):")
        for endpoint in compliance_endpoints:
            print(f"      - {endpoint}")
        
        # Governance Endpoints
        governance_endpoints = [route.path for route in governance_router.routes]
        print(f"\n   📌 Governance Router ({len(governance_endpoints)} Endpoints):")
        for endpoint in governance_endpoints:
            print(f"      - {endpoint}")
        
        total_endpoints = len(saga_endpoints) + len(compliance_endpoints) + len(governance_endpoints)
        print(f"\n   ✅ Insgesamt {total_endpoints} Enterprise-Endpoints verfügbar")
        
        return True
    except Exception as e:
        print(f"   ❌ Endpoint-Test fehlgeschlagen: {e}")
        return False


def test_api_v3_integration():
    """Teste API v3 Integration"""
    print("\n🔧 Teste API v3 Integration...")
    
    try:
        from backend.api.v3 import api_v3_router
        
        # Get all routes from API v3
        all_routes = []
        for route in api_v3_router.routes:
            if hasattr(route, 'path'):
                all_routes.append(route.path)
        
        print(f"\n   📊 API v3 Router:")
        print(f"      Prefix: /api/v3")
        print(f"      Routes: {len(all_routes)} gesamt")
        
        # Count enterprise routes
        saga_routes = [r for r in all_routes if '/saga' in r]
        compliance_routes = [r for r in all_routes if '/compliance' in r]
        governance_routes = [r for r in all_routes if '/governance' in r]
        
        print(f"\n   📌 Enterprise-Module Status:")
        print(f"      ✅ /saga: {len(saga_routes)} Endpoints")
        print(f"      ✅ /compliance: {len(compliance_routes)} Endpoints")
        print(f"      ✅ /governance: {len(governance_routes)} Endpoints")
        
        total_enterprise_endpoints = len(saga_routes) + len(compliance_routes) + len(governance_routes)
        print(f"\n   ✨ {total_enterprise_endpoints} Enterprise-Endpoints in API v3 integriert!")
        print(f"   🎯 Gesamt API v3 Endpoints: {len(all_routes)}")
        
        return True
    except Exception as e:
        print(f"   ❌ API v3 Integration-Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Führe alle Tests aus"""
    print("=" * 60)
    print("VERITAS API v3 - Enterprise Router Test")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(test_enterprise_router_imports())
    
    # Test 2: Models
    results.append(test_enterprise_models())
    
    # Test 3: Endpoints
    results.append(test_router_endpoints())
    
    # Test 4: API v3 Integration
    results.append(test_api_v3_integration())
    
    # Summary
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 Enterprise Router Test erfolgreich!")
        print("   Alle 3 Router (SAGA, Compliance, Governance) sind bereit.")
        print("=" * 60)
        return 0
    else:
        print("❌ Enterprise Router Test fehlgeschlagen!")
        print(f"   {sum(results)}/{len(results)} Tests erfolgreich")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
