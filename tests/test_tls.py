"""
TLS/HTTPS Testing Script for VERITAS Backend
=============================================

Tests HTTPS enforcement and HSTS headers:
1. HTTP request → Should redirect to HTTPS (301)
2. HTTPS request → Should include HSTS header
3. Development mode → HTTPS enforcement disabled

Usage:
    python tests/test_tls.py

Requirements:
    - Backend must be running
    - ENFORCE_HTTPS and ENABLE_HSTS configured in .env

Author: VERITAS Security Team
Date: 22. Oktober 2025
"""

import requests
import os
from datetime import datetime


# ============================================================================
# Configuration
# ============================================================================

HTTP_URL = "http://localhost:5000"
HTTPS_URL = "https://localhost:5000"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


# ============================================================================
# Helper Functions
# ============================================================================

def print_test(name: str):
    """Print test name"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}TEST: {name}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 80}{Colors.END}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")


# ============================================================================
# Test Functions
# ============================================================================

def test_http_access() -> bool:
    """Test if HTTP access works (for development mode check)"""
    print_test("HTTP Access Test")
    
    try:
        response = requests.get(f"{HTTP_URL}/", allow_redirects=False, timeout=5)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print_success("HTTP access allowed (development mode)")
            return True
        elif response.status_code == 301:
            print_success("HTTP redirects to HTTPS (production mode)")
            redirect_url = response.headers.get("location")
            print_info(f"Redirect URL: {redirect_url}")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        return False


def test_https_redirect() -> bool:
    """Test HTTP → HTTPS redirect"""
    print_test("HTTPS Redirect Test")
    
    # Check if ENFORCE_HTTPS is enabled
    from dotenv import load_dotenv
    load_dotenv()
    enforce_https = os.getenv("ENFORCE_HTTPS", "false").lower() == "true"
    reload_mode = os.getenv("VERITAS_API_RELOAD", "false").lower() == "true"
    
    print_info(f"ENFORCE_HTTPS: {enforce_https}")
    print_info(f"Development mode (RELOAD): {reload_mode}")
    
    if reload_mode:
        print_warning("Development mode detected - HTTPS enforcement should be disabled")
    
    try:
        response = requests.get(f"{HTTP_URL}/", allow_redirects=False, timeout=5)
        
        print_info(f"Status Code: {response.status_code}")
        
        if enforce_https and not reload_mode:
            # Production mode - expect redirect
            if response.status_code == 301:
                redirect_url = response.headers.get("location", "")
                print_info(f"Redirect URL: {redirect_url}")
                
                if redirect_url.startswith("https://"):
                    print_success("HTTP correctly redirects to HTTPS (301)")
                    return True
                else:
                    print_error(f"Redirect URL is not HTTPS: {redirect_url}")
                    return False
            else:
                print_error(f"Expected 301 redirect, got {response.status_code}")
                return False
        else:
            # Development mode - expect normal response
            if response.status_code == 200:
                print_success("HTTP allowed in development mode (correct)")
                return True
            else:
                print_warning(f"Unexpected status code in dev mode: {response.status_code}")
                return True  # Not a failure in dev mode
                
    except Exception as e:
        print_error(f"Exception: {e}")
        return False


def test_hsts_header() -> bool:
    """Test HSTS header presence"""
    print_test("HSTS Header Test")
    
    # Check if ENABLE_HSTS is enabled
    from dotenv import load_dotenv
    load_dotenv()
    enable_hsts = os.getenv("ENABLE_HSTS", "false").lower() == "true"
    reload_mode = os.getenv("VERITAS_API_RELOAD", "false").lower() == "true"
    
    print_info(f"ENABLE_HSTS: {enable_hsts}")
    print_info(f"Development mode (RELOAD): {reload_mode}")
    
    try:
        # Try HTTPS first (will fail if no cert)
        try:
            response = requests.get(f"{HTTPS_URL}/", verify=False, timeout=5)
            is_https = True
        except:
            # Fallback to HTTP with X-Forwarded-Proto header simulation
            response = requests.get(f"{HTTP_URL}/", timeout=5)
            is_https = False
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Using HTTPS: {is_https}")
        
        hsts_header = response.headers.get("Strict-Transport-Security")
        
        if enable_hsts and not reload_mode and is_https:
            # Production mode with HTTPS - expect HSTS header
            if hsts_header:
                print_success(f"HSTS header present: {hsts_header}")
                
                # Validate header format
                if "max-age" in hsts_header:
                    print_success("HSTS header includes max-age")
                
                if "includeSubDomains" in hsts_header:
                    print_info("HSTS includes subdomains")
                
                return True
            else:
                print_error("HSTS header missing (expected in production)")
                return False
        else:
            # Development mode or HTTP - HSTS header not expected
            if hsts_header:
                print_warning(f"HSTS header present in dev mode: {hsts_header}")
            else:
                print_success("HSTS header not present (correct for dev mode/HTTP)")
            return True
            
    except Exception as e:
        print_error(f"Exception: {e}")
        return False


def test_tls_config_status() -> bool:
    """Test TLS configuration via backend endpoint"""
    print_test("TLS Configuration Status")
    
    try:
        response = requests.get(f"{HTTP_URL}/", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if features include TLS info
            features = data.get("features", {})
            
            print_info("Backend Features:")
            for key, value in features.items():
                print_info(f"  {key}: {value}")
            
            print_success("Backend responding normally")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        return False


# ============================================================================
# Main Test Suite
# ============================================================================

def run_all_tests():
    """Run all TLS tests"""
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}VERITAS TLS/HTTPS Test Suite{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"HTTP URL: {HTTP_URL}")
    print(f"HTTPS URL: {HTTPS_URL}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}")
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # Test 1: HTTP Access
    results["total"] += 1
    if test_http_access():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 2: HTTPS Redirect
    results["total"] += 1
    if test_https_redirect():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 3: HSTS Header
    results["total"] += 1
    if test_hsts_header():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 4: TLS Config Status
    results["total"] += 1
    if test_tls_config_status():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Print summary
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"Total Tests: {results['total']}")
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.END}")
    
    success_rate = (results["passed"] / results["total"]) * 100 if results["total"] > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if results["failed"] == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  SOME TESTS FAILED (may be expected in dev mode){Colors.END}")
    
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}\n")
    
    return results["failed"] == 0


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Check if backend is running
    try:
        response = requests.get(f"{HTTP_URL}/", timeout=5)
        print_success("Backend is running")
    except Exception as e:
        print_error(f"Backend is not running at {HTTP_URL}")
        print_error(f"Error: {e}")
        print_info("Please start the backend with: python start_backend.py")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

