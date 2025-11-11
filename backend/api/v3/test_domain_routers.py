"""
VERITAS API v3 - Domain Router Test Script
===========================================

Testet alle Domain-Router (VPB, COVINA, PKI, IMMI) auf:
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


def test_domain_router_imports():
    """Teste Domain-Router Imports"""
    print("🔧 Teste Domain-Router Imports...")

    try:
        # VPB Router
        from backend.api.v3.vpb_router import vpb_router

        print("   ✅ VPB Router importiert")

        # COVINA Router
        from backend.api.v3.covina_router import covina_router

        print("   ✅ COVINA Router importiert")

        # PKI Router
        from backend.api.v3.pki_router import pki_router

        print("   ✅ PKI Router importiert")

        # IMMI Router
        from backend.api.v3.immi_router import immi_router

        print("   ✅ IMMI Router importiert")

        return True
    except ImportError as e:
        print(f"   ❌ Import fehlgeschlagen: {e}")
        return False


def test_domain_models():
    """Teste Domain-Pydantic Models"""
    print("\n🔧 Teste Domain-Pydantic Models...")

    try:
        from backend.api.v3.models import (  # VPB Models; COVINA Models; PKI Models; IMMI Models
            COVINAQueryRequest,
            COVINAQueryResponse,
            COVINAReport,
            COVINAStatistics,
            IMMIGeoData,
            IMMIQueryRequest,
            IMMIQueryResponse,
            IMMIRegulation,
            PKICertificate,
            PKIQueryRequest,
            PKIQueryResponse,
            PKIValidationRequest,
            PKIValidationResponse,
            VPBAnalysisRequest,
            VPBAnalysisResponse,
            VPBDocument,
            VPBQueryRequest,
            VPBQueryResponse,
        )

        print("   ✅ Alle Domain-Models importiert")

        # Test VPB Model Creation
        vpb_req = VPBQueryRequest(query="Test VPB Query", mode="veritas")
        print(f"   ✅ VPBQueryRequest erstellt: query='{vpb_req.query}', mode={vpb_req.mode}")

        # Test COVINA Model Creation
        covina_req = COVINAQueryRequest(query="Test COVINA Query", mode="statistics")
        print(f"   ✅ COVINAQueryRequest erstellt: query='{covina_req.query}', mode={covina_req.mode}")

        # Test PKI Model Creation
        pki_req = PKIQueryRequest(query="Test PKI Query", mode="technical")
        print(f"   ✅ PKIQueryRequest erstellt: query='{pki_req.query}', mode={pki_req.mode}")

        # Test IMMI Model Creation
        immi_req = IMMIQueryRequest(query="Test IMMI Query", mode="technical")
        print(f"   ✅ IMMIQueryRequest erstellt: query='{immi_req.query}', mode={immi_req.mode}")

        return True
    except Exception as e:
        print(f"   ❌ Model-Test fehlgeschlagen: {e}")
        return False


def test_router_endpoints():
    """Teste Router-Endpoint Konfiguration"""
    print("\n📊 Teste Router-Endpoints...")

    try:
        from backend.api.v3.covina_router import covina_router
        from backend.api.v3.immi_router import immi_router
        from backend.api.v3.pki_router import pki_router
        from backend.api.v3.vpb_router import vpb_router

        # VPB Endpoints
        vpb_endpoints = [route.path for route in vpb_router.routes]
        print(f"\n   📌 VPB Router ({len(vpb_endpoints)} Endpoints):")
        for endpoint in vpb_endpoints:
            print(f"      - {endpoint}")

        # COVINA Endpoints
        covina_endpoints = [route.path for route in covina_router.routes]
        print(f"\n   📌 COVINA Router ({len(covina_endpoints)} Endpoints):")
        for endpoint in covina_endpoints:
            print(f"      - {endpoint}")

        # PKI Endpoints
        pki_endpoints = [route.path for route in pki_router.routes]
        print(f"\n   📌 PKI Router ({len(pki_endpoints)} Endpoints):")
        for endpoint in pki_endpoints:
            print(f"      - {endpoint}")

        # IMMI Endpoints
        immi_endpoints = [route.path for route in immi_router.routes]
        print(f"\n   📌 IMMI Router ({len(immi_endpoints)} Endpoints):")
        for endpoint in immi_endpoints:
            print(f"      - {endpoint}")

        total_endpoints = len(vpb_endpoints) + len(covina_endpoints) + len(pki_endpoints) + len(immi_endpoints)
        print(f"\n   ✅ Insgesamt {total_endpoints} Domain-Endpoints verfügbar")

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
            if hasattr(route, "path"):
                all_routes.append(route.path)

        print("\n   📊 API v3 Router:")
        print(f"      Prefix: /api/v3")
        print(f"      Routes: {len(all_routes)} gesamt")

        # Count domain routes by checking full paths
        vpb_routes = [r for r in all_routes if "/vpb" in r or r.startswith("/vpb")]
        covina_routes = [r for r in all_routes if "/covina" in r or r.startswith("/covina")]
        pki_routes = [r for r in all_routes if "/pki" in r or r.startswith("/pki")]
        immi_routes = [r for r in all_routes if "/immi" in r or r.startswith("/immi")]

        print("\n   📌 Domain-Module Status:")
        print(f"      ✅ /vpb: {len(vpb_routes)} Endpoints")
        print(f"      ✅ /covina: {len(covina_routes)} Endpoints")
        print(f"      ✅ /pki: {len(pki_routes)} Endpoints")
        print(f"      ✅ /immi: {len(immi_routes)} Endpoints")

        total_domain_endpoints = len(vpb_routes) + len(covina_routes) + len(pki_routes) + len(immi_routes)
        print(f"\n   ✨ {total_domain_endpoints} Domain-Endpoints in API v3 integriert!")

        return True
    except Exception as e:
        print(f"   ❌ API v3 Integration-Test fehlgeschlagen: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Führe alle Tests aus"""
    print("=" * 60)
    print("VERITAS API v3 - Domain Router Test")
    print("=" * 60)

    results = []

    # Test 1: Imports
    results.append(test_domain_router_imports())

    # Test 2: Models
    results.append(test_domain_models())

    # Test 3: Endpoints
    results.append(test_router_endpoints())

    # Test 4: API v3 Integration
    results.append(test_api_v3_integration())

    # Summary
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 Domain Router Test erfolgreich!")
        print("   Alle 4 Router (VPB, COVINA, PKI, IMMI) sind bereit.")
        print("=" * 60)
        return 0
    else:
        print("❌ Domain Router Test fehlgeschlagen!")
        print(f"   {sum(results)}/{len(results)} Tests erfolgreich")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
