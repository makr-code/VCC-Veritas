"""
Quick DPAPI Test for VERITAS

Tests that Windows DPAPI encryption/decryption works correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
os.environ["ENABLE_SECURE_SECRETS"] = "true"

from backend.security.secrets import get_secrets_manager, DPAPI_AVAILABLE

print("=" * 80)
print("VERITAS DPAPI Test")
print("=" * 80)

# Check DPAPI availability
print(f"\n✅ DPAPI Available: {DPAPI_AVAILABLE}")

if not DPAPI_AVAILABLE:
    print("❌ ERROR: DPAPI not available!")
    print("   Please install pywin32: pip install pywin32")
    sys.exit(1)

# Get secrets manager
print("\n→ Initializing Secrets Manager...")
manager = get_secrets_manager()
print(f"✅ Backend: {manager.backend.__class__.__name__}")

# Test 1: Set secret
print("\n→ Test 1: Setting secret...")
test_key = "test_secret_123"
test_value = "my_super_secret_password_456"

if manager.set_secret(test_key, test_value):
    print(f"✅ Secret stored: {test_key}")
else:
    print(f"❌ Failed to store secret")
    sys.exit(1)

# Test 2: Retrieve secret
print("\n→ Test 2: Retrieving secret...")
retrieved = manager.get_secret(test_key)

if retrieved == test_value:
    print(f"✅ Secret retrieved correctly")
    print(f"   Original:  {test_value}")
    print(f"   Retrieved: {retrieved}")
else:
    print(f"❌ Secret mismatch!")
    print(f"   Expected: {test_value}")
    print(f"   Got:      {retrieved}")
    sys.exit(1)

# Test 3: List secrets
print("\n→ Test 3: Listing secrets...")
secrets = manager.list_secrets()
print(f"✅ Found {len(secrets)} secret(s):")
for secret in secrets:
    print(f"   - {secret}")

# Test 4: Delete secret
print("\n→ Test 4: Deleting secret...")
if manager.delete_secret(test_key):
    print(f"✅ Secret deleted: {test_key}")
else:
    print(f"❌ Failed to delete secret")
    sys.exit(1)

# Test 5: Verify deletion
print("\n→ Test 5: Verifying deletion...")
retrieved_after = manager.get_secret(test_key)

if retrieved_after is None:
    print(f"✅ Secret successfully deleted (returns None)")
else:
    print(f"❌ Secret still exists after deletion!")
    sys.exit(1)

# Success
print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED")
print("=" * 80)
print("\nDPAPI encryption/decryption working correctly!")
print("Storage location: data/secrets/dpapi_secrets.json")
