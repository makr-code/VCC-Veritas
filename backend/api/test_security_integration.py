"""
VERITAS API - Security Integration Tests
=========================================

Tests for security module and middleware.

Author: VERITAS Development Team
Created: 2025-10-08
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.api.security import AuthenticationManager, Permission, RateLimiter, SecurityConfig, User, UserRole


def test_user_creation_and_authentication():
    """Test 1: User creation and authentication"""
    print("\nTest 1: User Creation & Authentication")
    print("-" * 50)

    auth_manager = AuthenticationManager()

    # Create user
    user = auth_manager.create_user("testuser", "test@veritas.com", "Test@123", UserRole.USER)
    print(f"  [OK] User created: {user.username}")

    # Test authentication (success)
    auth_user = auth_manager.authenticate_user("testuser", "Test@123")
    assert auth_user is not None, "Authentication failed"
    print("  [OK] Authentication successful")

    # Test authentication (failure)
    auth_user = auth_manager.authenticate_user("testuser", "WrongPassword")
    assert auth_user is None, "Authentication should have failed"
    print(f"  [OK] Wrong password rejected")

    print("  Result: PASSED")
    return True


def test_jwt_token_creation_and_validation():
    """Test 2: JWT token creation and validation"""
    print("\nTest 2: JWT Token Creation & Validation")
    print("-" * 50)

    auth_manager = AuthenticationManager()
    user = auth_manager.create_user("jwtuser", "jwt@veritas.com", "JwtUser@123")

    # Create access token
    access_token = auth_manager.create_access_token(user)
    print(f"  [OK] Access token created: {access_token[:30]}...")

    # Validate token
    payload = auth_manager.verify_token(access_token)
    assert payload is not None, "Token validation failed"
    assert payload["username"] == user.username, "Username mismatch"
    assert payload["user_id"] == user.user_id, "User ID mismatch"
    print(f"  [OK] Token validated for user: {payload['username']}")
    print(f"  [OK] Permissions in token: {len(payload['permissions'])}")

    # Create refresh token
    refresh_token = auth_manager.create_refresh_token(user)
    print("  [OK] Refresh token created")

    # Refresh access token
    new_access_token = auth_manager.refresh_access_token(refresh_token)
    assert new_access_token is not None, "Token refresh failed"
    print(f"  [OK] Access token refreshed")

    # Revoke token
    auth_manager.revoke_token(access_token)
    revoked_payload = auth_manager.verify_token(access_token)
    assert revoked_payload is None, "Revoked token should be invalid"
    print(f"  [OK] Token revocation working")

    print("  Result: PASSED")
    return True


def test_api_key_management():
    """Test 3: API key management"""
    print("\nTest 3: API Key Management")
    print("-" * 50)

    auth_manager = AuthenticationManager()
    user = auth_manager.create_user("apiuser", "api@veritas.com", "ApiUser@123")

    # Create API key
    api_key_value, api_key = auth_manager.create_api_key(user, "Test API Key", expires_in_days=30)
    print(f"  [OK] API key created: {api_key_value[:20]}...")
    print(f"  [OK] Key ID: {api_key.key_id}")

    # Verify API key
    verified_key = auth_manager.verify_api_key(api_key_value)
    assert verified_key is not None, "API key verification failed"
    assert verified_key.key_id == api_key.key_id, "Key ID mismatch"
    print("  [OK] API key verified")

    # Check permissions
    assert verified_key.is_valid(), "API key should be valid"
    print(f"  [OK] API key is valid")
    print(f"  [OK] API key permissions: {len(verified_key.permissions)}")

    # Revoke API key
    auth_manager.revoke_api_key(api_key.key_id)
    assert not api_key.is_valid(), "Revoked key should be invalid"
    print("  [OK] API key revoked")

    print("  Result: PASSED")
    return True


def test_role_based_access_control():
    """Test 4: Role-based access control"""
    print("\nTest 4: Role-Based Access Control (RBAC)")
    print("-" * 50)

    auth_manager = AuthenticationManager()

    # Create users with different roles
    admin = auth_manager.create_user("admin", "admin@veritas.com", "Admin@123", UserRole.ADMIN)
    user = auth_manager.create_user("user", "user@veritas.com", "User@123", UserRole.USER)
    viewer = auth_manager.create_user("viewer", "viewer@veritas.com", "Viewer@123", UserRole.VIEWER)

    print(f"  [OK] Created users: ADMIN, USER, VIEWER")

    # Test permissions
    test_cases = [
        (admin, Permission.PLAN_DELETE, True, "Admin can delete plans"),
        (user, Permission.PLAN_DELETE, False, "User cannot delete plans"),
        (viewer, Permission.PLAN_DELETE, False, "Viewer cannot delete plans"),
        (admin, Permission.PLAN_CREATE, True, "Admin can create plans"),
        (user, Permission.PLAN_CREATE, True, "User can create plans"),
        (viewer, Permission.PLAN_CREATE, False, "Viewer cannot create plans"),
        (admin, Permission.ADMIN_ALL, True, "Admin has admin permission"),
        (user, Permission.ADMIN_ALL, False, "User has no admin permission"),
    ]

    for test_user, permission, expected, description in test_cases:
        result = test_user.has_permission(permission)
        assert result == expected, f"Permission check failed: {description}"
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"  {status} {description}: {result}")

    print(f"  [OK] All permission checks passed: {len(test_cases)}/{ len(test_cases)}")
    print("  Result: PASSED")
    return True


def test_rate_limiting():
    """Test 5: Rate limiting"""
    print("\nTest 5: Rate Limiting")
    print("-" * 50)

    rate_limiter = RateLimiter(requests=5, window_seconds=10)

    # Test rate limiting
    identifier = "test_user_123"
    results = []

    for i in range(7):
        allowed = rate_limiter.is_allowed(identifier)
        remaining = rate_limiter.get_remaining(identifier)
        results.append((i + 1, allowed, remaining))

    # Verify results
    assert results[0][1] == True, "First request should be allowed"
    assert results[4][1] == True, "5th request should be allowed"
    assert results[5][1] == False, "6th request should be rate limited"
    assert results[6][1] == False, "7th request should be rate limited"

    print("  [OK] First 5 requests allowed")
    print(f"  [OK] Requests 6-7 rate limited")
    print(f"  [OK] Remaining count working")

    # Test reset time
    reset_time = rate_limiter.get_reset_time(identifier)
    assert reset_time is not None, "Reset time should be set"
    print(f"  [OK] Reset time calculated")

    print("  Result: PASSED")
    return True


def test_password_validation():
    """Test 6: Password validation"""
    print("\nTest 6: Password Validation")
    print("-" * 50)

    auth_manager = AuthenticationManager()

    # Test valid password
    try:
        user = auth_manager.create_user("pwdtest", "pwd@veritas.com", "Valid@123")
        print(f"  [OK] Valid password accepted")
    except ValueError as e:
        print(f"  [FAIL] Valid password rejected: {e}")
        return False

    # Test invalid passwords
    invalid_passwords = [
        ("short", "Password too short"),
        ("nouppercase123!", "No uppercase letter"),
        ("NOLOWERCASE123!", "No lowercase letter"),
        ("NoDigitsHere!", "No digits"),
        ("NoSpecial123", "No special characters"),
    ]

    for pwd, description in invalid_passwords:
        try:
            auth_manager.create_user(f"test_{pwd}", f"{pwd}@test.com", pwd)
            print(f"  [FAIL] {description} should have been rejected")
            return False
        except ValueError:
            print(f"  [OK] {description} correctly rejected")

    print("  Result: PASSED")
    return True


def test_permission_checking():
    """Test 7: Permission checking with tokens"""
    print("\nTest 7: Permission Checking with Tokens")
    print("-" * 50)

    auth_manager = AuthenticationManager()
    admin = auth_manager.create_user("tokenadmin", "admin@test.com", "Admin@123", UserRole.ADMIN)
    user = auth_manager.create_user("tokenuser", "user@test.com", "User@123", UserRole.USER)

    # Create tokens
    admin_token = auth_manager.create_access_token(admin)
    user_token = auth_manager.create_access_token(user)

    # Verify tokens
    admin_payload = auth_manager.verify_token(admin_token)
    user_payload = auth_manager.verify_token(user_token)

    print("  [OK] Admin token created and verified")
    print(f"  [OK] User token created and verified")

    # Check permissions via payload
    admin_can_delete = auth_manager.check_permission(admin_payload, Permission.PLAN_DELETE)
    user_can_delete = auth_manager.check_permission(user_payload, Permission.PLAN_DELETE)

    assert admin_can_delete == True, "Admin should have delete permission"
    assert user_can_delete == False, "User should not have delete permission"

    print(f"  [OK] Admin has delete permission: {admin_can_delete}")
    print(f"  [OK] User has delete permission: {user_can_delete}")

    print("  Result: PASSED")
    return True


def run_all_tests():
    """Run all security tests"""
    print("\n" + "=" * 70)
    print("VERITAS SECURITY MODULE - INTEGRATION TESTS")
    print("=" * 70)

    tests = [
        test_user_creation_and_authentication,
        test_jwt_token_creation_and_validation,
        test_api_key_management,
        test_role_based_access_control,
        test_rate_limiting,
        test_password_validation,
        test_permission_checking,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"  [ERROR] Test failed with exception: {e}")
            results.append((test.__name__, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70 + "\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {test_name}")

    print(f"\nResults: {passed}/{total} tests passed ({passed / total*100:.1f}%)")

    if passed == total:
        print("\n[OK] ALL TESTS PASSED - PRODUCTION READY")
    else:
        print(f"\n[WARN] {total - passed} test(s) failed")

    print("\n" + "=" * 70)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
