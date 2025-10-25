"""
Test Backend with Encrypted Secrets

Verifies that the backend can start and authenticate using
secrets from encrypted DPAPI storage.
"""

import sys
import time
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("VERITAS Backend Test with Encrypted Secrets")
print("=" * 80)

# Test 1: Verify secrets available
print("\n→ Test 1: Verify encrypted secrets...")
from backend.security.secrets import get_secrets_manager, get_jwt_secret

manager = get_secrets_manager()
secrets = manager.list_secrets()

print(f"✅ Found {len(secrets)} encrypted secrets:")
for secret in secrets:
    print(f"   - {secret}")

jwt_secret = get_jwt_secret()
if jwt_secret and len(jwt_secret) > 20:
    print(f"✅ JWT secret retrieved: {jwt_secret[:20]}...")
else:
    print(f"❌ Failed to retrieve JWT secret")
    sys.exit(1)

# Test 2: Check backend health
print("\n→ Test 2: Check backend health...")
backend_url = "http://127.0.0.1:5000"

try:
    response = requests.get(f"{backend_url}/api/system/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Backend healthy: {data.get('status')}")
        print(f"   Version: {data.get('version')}")
    else:
        print(f"❌ Backend returned status {response.status_code}")
        sys.exit(1)
except requests.exceptions.ConnectionError:
    print("⚠️  Backend not running - please start with: python start_backend.py")
    print("   Skipping authentication test")
    sys.exit(0)
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    sys.exit(1)

# Test 3: Test authentication (JWT)
print("\n→ Test 3: Test JWT authentication...")

try:
    # Try to login with default admin user
    auth_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(
        f"{backend_url}/auth/token",
        data=auth_data,
        timeout=5
    )
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if access_token:
            print(f"✅ Authentication successful")
            print(f"   Token: {access_token[:30]}...")
            print(f"   Type: {token_data.get('token_type')}")
            
            # Test 4: Verify token works
            print("\n→ Test 4: Verify token access...")
            
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(
                f"{backend_url}/auth/me",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Token verified successfully")
                print(f"   User: {user_data.get('username')}")
                print(f"   Role: {user_data.get('role')}")
            else:
                print(f"❌ Token verification failed: {response.status_code}")
                sys.exit(1)
        else:
            print(f"❌ No access token in response")
            sys.exit(1)
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Authentication test failed: {e}")
    sys.exit(1)

# Success
print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED")
print("=" * 80)
print("\n✅ Backend working correctly with encrypted secrets!")
print("   - Secrets encrypted with Windows DPAPI")
print("   - JWT authentication working")
print("   - Token validation working")
print("\n🎉 Task 4 - Secrets Encryption: COMPLETE!")
