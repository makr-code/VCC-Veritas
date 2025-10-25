"""
Authentication Testing Script for VERITAS Backend
==================================================

Tests all authentication endpoints:
1. POST /auth/token - Login
2. GET /auth/me - Current user info
3. GET /auth/status - Auth system status
4. Protected endpoints (future)

Usage:
    python tests/test_auth.py

Requirements:
    - Backend must be running on http://localhost:5000
    - ENABLE_AUTH can be true or false (both tested)

Author: VERITAS Security Team
Date: 22. Oktober 2025
"""

import requests
import json
from typing import Dict, Optional
from datetime import datetime


# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "http://localhost:5000"
AUTH_URL = f"{BASE_URL}/auth"

# Test users (from backend/security/auth.py)
TEST_USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "expected_roles": ["admin", "manager", "user"]
    },
    "user": {
        "username": "user",
        "password": "user123",
        "expected_roles": ["user"]
    },
    "guest": {
        "username": "guest",
        "password": "guest123",
        "expected_roles": ["guest"]
    }
}

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


def print_json(data: dict, title: str = "Response"):
    """Pretty print JSON data"""
    print(f"\n{Colors.BOLD}{title}:{Colors.END}")
    print(json.dumps(data, indent=2))


# ============================================================================
# Test Functions
# ============================================================================

def test_auth_status() -> bool:
    """Test GET /auth/status endpoint"""
    print_test("Auth Status Check")
    
    try:
        response = requests.get(f"{AUTH_URL}/status")
        
        if response.status_code == 200:
            data = response.json()
            print_json(data)
            
            # Check expected fields
            if "enabled" in data and "method" in data:
                print_success(f"Auth status retrieved successfully")
                print_info(f"Authentication enabled: {data['enabled']}")
                print_info(f"Method: {data.get('method', 'N/A')}")
                return True
            else:
                print_error("Missing expected fields in response")
                return False
        else:
            print_error(f"Status check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception during status check: {e}")
        return False


def test_login(username: str, password: str, should_succeed: bool = True):
    """
    Test POST /auth/token endpoint
    
    Returns:
        - For should_succeed=True: token string if successful, None if failed
        - For should_succeed=False: True if correctly rejected, False if not
    """
    print_test(f"Login Test - User: {username}")
    
    try:
        response = requests.post(
            f"{AUTH_URL}/token",
            data={
                "username": username,
                "password": password
            }
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if should_succeed:
            if response.status_code == 200:
                data = response.json()
                print_json(data)
                
                # Check for required fields
                if "access_token" in data and "token_type" in data:
                    token = data["access_token"]
                    print_success(f"Login successful for user '{username}'")
                    print_info(f"Token type: {data['token_type']}")
                    print_info(f"Expires in: {data.get('expires_in', 'N/A')} seconds")
                    print_info(f"Token (first 20 chars): {token[:20]}...")
                    return token
                else:
                    print_error("Missing access_token or token_type in response")
                    return None
            else:
                print_error(f"Login failed (expected success): {response.status_code}")
                print_json(response.json())
                return None
        else:
            # Testing invalid login - should be rejected
            if response.status_code == 401:
                print_success(f"Login correctly rejected for invalid credentials")
                return True  # Test passed!
            else:
                print_error(f"Unexpected status code: {response.status_code} (expected 401)")
                return False  # Test failed!
                
    except Exception as e:
        print_error(f"Exception during login: {e}")
        return None if should_succeed else False


def test_get_current_user(token: str, expected_username: str) -> bool:
    """Test GET /auth/me endpoint"""
    print_test(f"Get Current User - Expected: {expected_username}")
    
    try:
        response = requests.get(
            f"{AUTH_URL}/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_json(data)
            
            # Verify username
            if data.get("username") == expected_username:
                print_success(f"Current user retrieved successfully")
                print_info(f"Username: {data.get('username')}")
                print_info(f"Full name: {data.get('full_name')}")
                print_info(f"Email: {data.get('email')}")
                print_info(f"Roles: {data.get('roles')}")
                return True
            else:
                print_error(f"Username mismatch: {data.get('username')} != {expected_username}")
                return False
        else:
            print_error(f"Get current user failed: {response.status_code}")
            print_json(response.json())
            return False
            
    except Exception as e:
        print_error(f"Exception during get current user: {e}")
        return False


def test_invalid_token() -> bool:
    """Test with invalid token"""
    print_test("Invalid Token Test")
    
    try:
        response = requests.get(
            f"{AUTH_URL}/me",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print_success("Invalid token correctly rejected (401)")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code} (expected 401)")
            return False
            
    except Exception as e:
        print_error(f"Exception during invalid token test: {e}")
        return False


def test_no_token() -> bool:
    """Test without token"""
    print_test("No Token Test")
    
    try:
        response = requests.get(f"{AUTH_URL}/me")
        
        print_info(f"Status Code: {response.status_code}")
        
        # In development mode (ENABLE_AUTH=false), this might return 200
        # In production mode (ENABLE_AUTH=true), this should return 401
        if response.status_code in [200, 401]:
            if response.status_code == 200:
                print_warning("No token accepted (development mode - ENABLE_AUTH=false)")
                data = response.json()
                print_info(f"Username: {data.get('username')} (dev_admin)")
            else:
                print_success("No token correctly rejected (401)")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception during no token test: {e}")
        return False


# ============================================================================
# Main Test Suite
# ============================================================================

def run_all_tests():
    """Run all authentication tests"""
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}VERITAS Authentication Test Suite{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend URL: {BASE_URL}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}")
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # Test 1: Auth Status
    results["total"] += 1
    if test_auth_status():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 2: Valid logins for all test users
    tokens = {}
    for user_type, user_data in TEST_USERS.items():
        results["total"] += 1
        token = test_login(user_data["username"], user_data["password"], should_succeed=True)
        if token:
            tokens[user_type] = token
            results["passed"] += 1
        else:
            results["failed"] += 1
    
    # Test 3: Invalid login
    results["total"] += 1
    if test_login("admin", "wrong_password", should_succeed=False):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 4: Get current user for each token
    for user_type, token in tokens.items():
        results["total"] += 1
        expected_username = TEST_USERS[user_type]["username"]
        if test_get_current_user(token, expected_username):
            results["passed"] += 1
        else:
            results["failed"] += 1
    
    # Test 5: Invalid token
    results["total"] += 1
    if test_invalid_token():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 6: No token
    results["total"] += 1
    if test_no_token():
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
        print(f"\n{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.END}")
    
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}\n")
    
    return results["failed"] == 0


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/")
        print_success("Backend is running")
    except Exception as e:
        print_error(f"Backend is not running at {BASE_URL}")
        print_error(f"Error: {e}")
        print_info("Please start the backend with: python backend/app.py")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
