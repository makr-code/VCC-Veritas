"""
VERITAS API v3 - Phase 2 Integration Test

Testet die Domain-spezifischen Router: VPB, COVINA, PKI, IMMI
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

def test_domain_router_imports():
    """Teste Domain Router Imports"""
    print("🔧 Teste API v3 Domain Router Imports...")
    
    try:
        # VPB Router
        from backend.api.v3.vpb_router import vpb_router
        print("✅ VPB Router importiert")
        
        # COVINA Router
        from backend.api.v3.covina_router import covina_router
        print("✅ COVINA Router importiert")
        
        # PKI Router
        from backend.api.v3.pki_router import pki_router
        print("✅ PKI Router importiert")
        
        # IMMI Router
        from backend.api.v3.immi_router import immi_router
        print("✅ IMMI Router importiert")
        
        return True
        
    except Exception as e:
        print(f"❌ Import-Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_domain_models():
    """Teste Domain-spezifische Pydantic Models"""
    print("\n🔧 Teste Domain Models...")
    
    try:
        from backend.api.v3.models import (
            # VPB Models
            VPBQueryRequest, VPBQueryResponse, VPBDocument,
            VPBAnalysisRequest, VPBAnalysisResponse,
            # COVINA Models
            COVINAQueryRequest, COVINAQueryResponse,
            COVINAStatistics, COVINAReport,
            # PKI Models
            PKIQueryRequest, PKIQueryResponse, PKICertificate,
            PKIValidationRequest, PKIValidationResponse,
            # IMMI Models
            IMMIQueryRequest, IMMIQueryResponse,
            IMMIRegulation, IMMIGeoData
        )
        print("✅ Alle Domain Models importiert")
        
        # Test VPB Model Instanziierung
        vpb_req = VPBQueryRequest(query="Test VPB Query", mode="veritas")
        print(f"  ✅ VPBQueryRequest: {vpb_req.query}")
        
        # Test COVINA Model Instanziierung
        covina_stat = COVINAStatistics(
            region="Deutschland",
            date="2025-10-17",
            cases=1000,
            incidence=50.5,
            r_value=0.95
        )
        print(f"  ✅ COVINAStatistics: {covina_stat.region}, Incidence={covina_stat.incidence}")
        
        # Test PKI Model Instanziierung
        pki_cert = PKICertificate(
            certificate_id="test_001",
            subject="CN=test.com",
            issuer="CN=Test CA",
            valid_from="2025-01-01",
            valid_until="2026-01-01",
            status="valid"
        )
        print(f"  ✅ PKICertificate: {pki_cert.subject}, Status={pki_cert.status}")
        
        # Test IMMI Model Instanziierung
        immi_geo = IMMIGeoData(
            location_id="wka_001",
            latitude=52.5200,
            longitude=13.4050,
            type="wka"
        )
        print(f"  ✅ IMMIGeoData: {immi_geo.location_id}, Type={immi_geo.type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model-Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_router_structure():
    """Teste Router Struktur"""
    print("\n🔧 Teste Router Struktur...")
    
    try:
        from backend.api.v3.vpb_router import vpb_router
        from backend.api.v3.covina_router import covina_router
        from backend.api.v3.pki_router import pki_router
        from backend.api.v3.immi_router import immi_router
        
        # Check Router Prefixes
        print(f"  ✅ VPB Router Prefix: {vpb_router.prefix}")
        print(f"  ✅ COVINA Router Prefix: {covina_router.prefix}")
        print(f"  ✅ PKI Router Prefix: {pki_router.prefix}")
        print(f"  ✅ IMMI Router Prefix: {immi_router.prefix}")
        
        # Count Routes
        vpb_routes = len(vpb_router.routes)
        covina_routes = len(covina_router.routes)
        pki_routes = len(pki_router.routes)
        immi_routes = len(immi_router.routes)
        
        print(f"\n  📊 Route Count:")
        print(f"    VPB: {vpb_routes} routes")
        print(f"    COVINA: {covina_routes} routes")
        print(f"    PKI: {pki_routes} routes")
        print(f"    IMMI: {immi_routes} routes")
        print(f"    Total: {vpb_routes + covina_routes + pki_routes + immi_routes} routes")
        
        return True
        
    except Exception as e:
        print(f"❌ Router Struktur Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main Test Function"""
    print("=" * 60)
    print("VERITAS API v3 - Phase 2 Domain Endpoints Integration Test")
    print("=" * 60)
    
    results = []
    
    # Test 1: Router Imports
    results.append(("Router Imports", test_domain_router_imports()))
    
    # Test 2: Domain Models
    results.append(("Domain Models", test_domain_models()))
    
    # Test 3: Router Structure
    results.append(("Router Structure", test_router_structure()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 Alle Tests erfolgreich - Phase 2 Domain Endpoints bereit!")
        return 0
    else:
        print("\n❌ Einige Tests fehlgeschlagen - Bitte Fehler beheben")
        return 1

if __name__ == "__main__":
    sys.exit(main())
