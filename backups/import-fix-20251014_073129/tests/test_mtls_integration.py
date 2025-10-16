#!/usr/bin/env python3
"""
mTLS Integration Test

Tests the mTLS FastAPI server with various scenarios:
1. Health check without certificate (should succeed - exempt path)
2. API endpoint without certificate (should fail - 401)
3. API endpoint with valid certificate (should succeed)
4. Certificate info endpoint (should return cert details)

Usage:
    python tests/test_mtls_integration.py

Requirements:
    - mTLS server running on https://localhost:5000
    - Client certificate in ca_storage/client_cert.pem
    - Client key in ca_storage/client_key.pem
    - Root CA in ca_storage/ca_certificates/root_ca.pem
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx
import ssl
from typing import Dict, Any

# Certificate paths
CA_STORAGE = Path("ca_storage")
CLIENT_CERT = CA_STORAGE / "client_cert.pem"
CLIENT_KEY = CA_STORAGE / "client_key.pem"
ROOT_CA = CA_STORAGE / "ca_certificates" / "root_ca.pem"

# Server URL
SERVER_URL = "https://localhost:5000"


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(test_name: str, success: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"         {details}")


def test_health_check_no_cert():
    """Test 1: Health check without certificate (should succeed)."""
    print_section("Test 1: Health Check (No Certificate)")
    
    try:
        # Create SSL context that trusts our Root CA but doesn't send client cert
        ssl_context = ssl.create_default_context(cafile=str(ROOT_CA))
        
        with httpx.Client(verify=ssl_context) as client:
            response = client.get(f"{SERVER_URL}/health", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                print_result(
                    "Health endpoint accessible without certificate",
                    True,
                    f"Status: {data.get('status')}, mTLS: {data.get('mtls')}"
                )
                return True
            else:
                print_result(
                    "Health endpoint accessible without certificate",
                    False,
                    f"Unexpected status code: {response.status_code}"
                )
                return False
                
    except Exception as e:
        print_result(
            "Health endpoint accessible without certificate",
            False,
            f"Error: {e}"
        )
        return False


def test_api_endpoint_no_cert():
    """Test 2: API endpoint without certificate (should fail)."""
    print_section("Test 2: API Endpoint (No Certificate)")
    
    try:
        ssl_context = ssl.create_default_context(cafile=str(ROOT_CA))
        
        with httpx.Client(verify=ssl_context) as client:
            response = client.get(f"{SERVER_URL}/api/v1/test", timeout=5.0)
            
            # Should fail with 401 or connection error
            if response.status_code in [401, 403]:
                print_result(
                    "API endpoint blocks access without certificate",
                    True,
                    f"Status: {response.status_code} (as expected)"
                )
                return True
            else:
                print_result(
                    "API endpoint blocks access without certificate",
                    False,
                    f"Unexpected status: {response.status_code} (expected 401/403)"
                )
                return False
                
    except httpx.ConnectError as e:
        # Connection error is also acceptable (server requires client cert at TLS level)
        print_result(
            "API endpoint blocks access without certificate",
            True,
            "Connection blocked at TLS level (expected)"
        )
        return True
    except Exception as e:
        print_result(
            "API endpoint blocks access without certificate",
            False,
            f"Unexpected error: {e}"
        )
        return False


def test_api_endpoint_with_cert():
    """Test 3: API endpoint with valid certificate (should succeed)."""
    print_section("Test 3: API Endpoint (With Certificate)")
    
    if not CLIENT_CERT.exists():
        print_result(
            "Client certificate exists",
            False,
            f"Certificate not found: {CLIENT_CERT}"
        )
        return False
    
    if not CLIENT_KEY.exists():
        print_result(
            "Client key exists",
            False,
            f"Key not found: {CLIENT_KEY}"
        )
        return False
    
    try:
        # Create SSL context with client certificate
        ssl_context = ssl.create_default_context(cafile=str(ROOT_CA))
        ssl_context.load_cert_chain(
            certfile=str(CLIENT_CERT),
            keyfile=str(CLIENT_KEY)
        )
        
        with httpx.Client(verify=ssl_context) as client:
            response = client.get(f"{SERVER_URL}/api/v1/test", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                print_result(
                    "API endpoint accessible with certificate",
                    True,
                    f"Service: {data.get('client', {}).get('service')}"
                )
                
                # Validate response structure
                if 'client' in data and 'service' in data['client']:
                    print(f"         Client CN: {data['client'].get('cn')}")
                    print(f"         Authenticated: {data['client'].get('authenticated')}")
                    return True
                else:
                    print_result(
                        "Response structure valid",
                        False,
                        "Missing expected fields"
                    )
                    return False
            else:
                print_result(
                    "API endpoint accessible with certificate",
                    False,
                    f"Status: {response.status_code}"
                )
                return False
                
    except Exception as e:
        print_result(
            "API endpoint accessible with certificate",
            False,
            f"Error: {e}"
        )
        return False


def test_certificate_info():
    """Test 4: Certificate info endpoint (should return cert details)."""
    print_section("Test 4: Certificate Info Endpoint")
    
    try:
        ssl_context = ssl.create_default_context(cafile=str(ROOT_CA))
        ssl_context.load_cert_chain(
            certfile=str(CLIENT_CERT),
            keyfile=str(CLIENT_KEY)
        )
        
        with httpx.Client(verify=ssl_context) as client:
            response = client.get(f"{SERVER_URL}/api/v1/certificate-info", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                print_result(
                    "Certificate info endpoint accessible",
                    True,
                    f"CN: {data.get('subject', {}).get('common_name')}"
                )
                
                # Print certificate details
                print(f"         Serial: {data.get('serial_number', 'N/A')[:20]}...")
                print(f"         Valid Until: {data.get('validity', {}).get('not_after', 'N/A')[:10]}")
                print(f"         Service: {data.get('service', 'N/A')}")
                return True
            else:
                print_result(
                    "Certificate info endpoint accessible",
                    False,
                    f"Status: {response.status_code}"
                )
                return False
                
    except Exception as e:
        print_result(
            "Certificate info endpoint accessible",
            False,
            f"Error: {e}"
        )
        return False


def test_whoami():
    """Test 5: WhoAmI endpoint (should return service identity)."""
    print_section("Test 5: WhoAmI Endpoint")
    
    try:
        ssl_context = ssl.create_default_context(cafile=str(ROOT_CA))
        ssl_context.load_cert_chain(
            certfile=str(CLIENT_CERT),
            keyfile=str(CLIENT_KEY)
        )
        
        with httpx.Client(verify=ssl_context) as client:
            response = client.get(f"{SERVER_URL}/api/v1/whoami", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('authenticated'):
                    print_result(
                        "WhoAmI returns authenticated status",
                        True,
                        f"Service: {data.get('service')}"
                    )
                    print(f"         Method: {data.get('authentication_method')}")
                    return True
                else:
                    print_result(
                        "WhoAmI returns authenticated status",
                        False,
                        "Not authenticated"
                    )
                    return False
            else:
                print_result(
                    "WhoAmI endpoint accessible",
                    False,
                    f"Status: {response.status_code}"
                )
                return False
                
    except Exception as e:
        print_result(
            "WhoAmI endpoint accessible",
            False,
            f"Error: {e}"
        )
        return False


def main():
    """Run all mTLS integration tests."""
    print("\n" + "=" * 70)
    print("  VERITAS mTLS Integration Test Suite")
    print("=" * 70)
    print(f"\nServer URL: {SERVER_URL}")
    print(f"Client Cert: {CLIENT_CERT}")
    print(f"Client Key:  {CLIENT_KEY}")
    print(f"Root CA:     {ROOT_CA}")
    
    # Check if certificates exist
    if not CLIENT_CERT.exists():
        print(f"\n❌ Client certificate not found: {CLIENT_CERT}")
        print("   Run: python scripts/setup_mtls_certificates.py")
        sys.exit(1)
    
    if not CLIENT_KEY.exists():
        print(f"\n❌ Client key not found: {CLIENT_KEY}")
        sys.exit(1)
    
    if not ROOT_CA.exists():
        print(f"\n❌ Root CA not found: {ROOT_CA}")
        sys.exit(1)
    
    # Run tests
    results = []
    
    results.append(("Health Check (No Cert)", test_health_check_no_cert()))
    results.append(("API Endpoint (No Cert)", test_api_endpoint_no_cert()))
    results.append(("API Endpoint (With Cert)", test_api_endpoint_with_cert()))
    results.append(("Certificate Info", test_certificate_info()))
    results.append(("WhoAmI", test_whoami()))
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n  Total: {total} tests")
    print(f"  Passed: {passed} ({passed/total*100:.0f}%)")
    print(f"  Failed: {failed}")
    
    if failed == 0:
        print("\n✅ All tests passed! mTLS integration is working correctly.")
        sys.exit(0)
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
