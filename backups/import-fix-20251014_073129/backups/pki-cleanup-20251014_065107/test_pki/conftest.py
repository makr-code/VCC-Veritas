"""
Pytest Configuration and Shared Fixtures for PKI Tests

Provides:
- Temporary storage fixtures
- PKI component fixtures (CertificateManager, CAService)
- Test data fixtures (keypairs, CSRs, certificates)
- Cleanup utilities
"""

import os
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta

# Import PKI modules
from backend.pki.crypto_utils import (
    generate_keypair,
    generate_csr,
    generate_random_key
)
from backend.pki.cert_manager import CertificateManager
from backend.pki.ca_service import CAService


# ============================================================================
# Storage Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def temp_pki_storage():
    """Create temporary PKI storage directory (function-scoped)"""
    temp_dir = tempfile.mkdtemp(prefix="pki_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def temp_ca_storage():
    """Create temporary CA storage directory (function-scoped)"""
    temp_dir = tempfile.mkdtemp(prefix="ca_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def temp_pki_storage_session():
    """Create temporary PKI storage directory (session-scoped)"""
    temp_dir = tempfile.mkdtemp(prefix="pki_test_session_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def temp_ca_storage_session():
    """Create temporary CA storage directory (session-scoped)"""
    temp_dir = tempfile.mkdtemp(prefix="ca_test_session_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# PKI Component Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def cert_manager(temp_pki_storage):
    """Create CertificateManager instance (function-scoped)"""
    return CertificateManager(temp_pki_storage)


@pytest.fixture(scope="function")
def ca_service(temp_ca_storage, cert_manager):
    """Create CAService instance (function-scoped)"""
    return CAService(temp_ca_storage, cert_manager)


@pytest.fixture(scope="session")
def cert_manager_session(temp_pki_storage_session):
    """Create CertificateManager instance (session-scoped)"""
    return CertificateManager(temp_pki_storage_session)


@pytest.fixture(scope="session")
def ca_service_session(temp_ca_storage_session, cert_manager_session):
    """Create CAService instance (session-scoped)"""
    return CAService(temp_ca_storage_session, cert_manager_session)


# ============================================================================
# Keypair Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def rsa_2048_keypair():
    """Generate RSA 2048-bit keypair"""
    return generate_keypair(2048)


@pytest.fixture(scope="function")
def rsa_3072_keypair():
    """Generate RSA 3072-bit keypair"""
    return generate_keypair(3072)


@pytest.fixture(scope="function")
def rsa_4096_keypair():
    """Generate RSA 4096-bit keypair"""
    return generate_keypair(4096)


@pytest.fixture(scope="session")
def rsa_2048_keypair_session():
    """Generate RSA 2048-bit keypair (session-scoped)"""
    return generate_keypair(2048)


# ============================================================================
# CSR Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def end_entity_csr(rsa_2048_keypair):
    """Generate end-entity CSR"""
    private_key, _ = rsa_2048_keypair
    csr = generate_csr(
        private_key,
        common_name="test.example.com",
        organization="Test Corp",
        country="DE",
        state="Bavaria",
        locality="Munich"
    )
    return csr, private_key


@pytest.fixture(scope="function")
def intermediate_ca_csr(rsa_3072_keypair):
    """Generate intermediate CA CSR"""
    private_key, _ = rsa_3072_keypair
    csr = generate_csr(
        private_key,
        common_name="Intermediate CA",
        organization="Test Corp",
        country="DE"
    )
    return csr, private_key


@pytest.fixture(scope="function")
def server_csr(rsa_2048_keypair):
    """Generate server certificate CSR"""
    private_key, _ = rsa_2048_keypair
    csr = generate_csr(
        private_key,
        common_name="server.example.com",
        organization="Test Corp"
    )
    return csr, private_key


@pytest.fixture(scope="function")
def client_csr(rsa_2048_keypair):
    """Generate client certificate CSR"""
    private_key, _ = rsa_2048_keypair
    csr = generate_csr(
        private_key,
        common_name="client@example.com",
        organization="Test Corp",
        email="client@example.com"
    )
    return csr, private_key


# ============================================================================
# Certificate Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def self_signed_cert(cert_manager):
    """Create self-signed certificate"""
    cert_id, cert_pem = cert_manager.create_certificate(
        subject_name="selfsigned.example.com",
        validity_days=365,
        key_size=2048
    )
    return cert_id, cert_pem


@pytest.fixture(scope="function")
def root_ca(ca_service):
    """Create Root CA"""
    ca_id, ca_cert_pem, ca_key_pem = ca_service.initialize_root_ca(
        common_name="Test Root CA",
        validity_days=3650,
        key_size=4096,
        organization="Test Corp"
    )
    return ca_id, ca_cert_pem, ca_key_pem


@pytest.fixture(scope="function")
def ca_signed_cert(ca_service, root_ca, end_entity_csr):
    """Create CA-signed certificate"""
    ca_id, _, _ = root_ca
    csr_pem, _ = end_entity_csr
    
    cert_id, cert_pem = ca_service.sign_csr(
        csr_pem=csr_pem,
        validity_days=365,
        is_ca=False,
        ca_id=ca_id
    )
    return cert_id, cert_pem, ca_id


@pytest.fixture(scope="session")
def root_ca_session(ca_service_session):
    """Create Root CA (session-scoped)"""
    ca_id, ca_cert_pem, ca_key_pem = ca_service_session.initialize_root_ca(
        common_name="Test Root CA (Session)",
        validity_days=3650,
        key_size=4096
    )
    return ca_id, ca_cert_pem, ca_key_pem


# ============================================================================
# Encryption Key Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def aes_256_key():
    """Generate AES-256 encryption key"""
    return generate_random_key(32)


@pytest.fixture(scope="function")
def aes_128_key():
    """Generate AES-128 encryption key"""
    return generate_random_key(16)


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def sample_data():
    """Sample data for encryption/signing"""
    return {
        "small": b"Hello, World!",
        "medium": b"X" * 1000,  # 1KB
        "large": b"Y" * 100000,  # 100KB
        "empty": b""
    }


@pytest.fixture(scope="function")
def revocation_reasons():
    """Valid revocation reasons"""
    return [
        "unspecified",
        "keyCompromise",
        "affiliationChanged",
        "superseded",
        "cessationOfOperation"
    ]


# ============================================================================
# Utility Functions
# ============================================================================

def create_test_certificate(cert_manager, name, validity=365, key_size=2048, is_ca=False):
    """Utility function to create test certificate"""
    cert_id, cert_pem = cert_manager.create_certificate(
        subject_name=name,
        validity_days=validity,
        key_size=key_size,
        is_ca=is_ca
    )
    return cert_id, cert_pem


def create_test_ca(ca_service, name, validity=3650, key_size=4096):
    """Utility function to create test CA"""
    ca_id, ca_cert_pem, ca_key_pem = ca_service.initialize_root_ca(
        common_name=name,
        validity_days=validity,
        key_size=key_size
    )
    return ca_id, ca_cert_pem, ca_key_pem


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "performance: marks tests as performance tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers to tests based on their names
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        
        # Mark performance tests
        if "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        # Mark slow tests (>1s expected)
        if any(keyword in item.nodeid.lower() for keyword in ["4096", "large", "benchmark"]):
            item.add_marker(pytest.mark.slow)


# ============================================================================
# Session Fixtures for Report
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def test_session_info(request):
    """Print test session information"""
    print("\n" + "=" * 80)
    print("PKI Test Suite - Production Tests (NO MOCK)")
    print("=" * 80)
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"Test Directory: {os.path.dirname(__file__)}")
    print("=" * 80 + "\n")
    
    yield
    
    print("\n" + "=" * 80)
    print(f"End Time: {datetime.now().isoformat()}")
    print("=" * 80)


# ============================================================================
# Autouse Fixtures for Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Cleanup temporary files after each test"""
    yield
    # Cleanup after test
    # (handled by temp_*_storage fixtures)


# ============================================================================
# Custom Assertions
# ============================================================================

def assert_valid_pem(pem_data, marker="BEGIN"):
    """Assert PEM data is valid"""
    assert pem_data is not None
    assert isinstance(pem_data, bytes)
    assert marker.encode() in pem_data


def assert_certificate_valid(cert_manager, cert_id):
    """Assert certificate is valid"""
    is_valid, message = cert_manager.validate_certificate(cert_id)
    assert is_valid is True, f"Certificate validation failed: {message}"


def assert_certificate_revoked(cert_manager, cert_id):
    """Assert certificate is revoked"""
    cert_info = cert_manager.get_certificate(cert_id)
    assert cert_info is not None
    assert cert_info["revoked"] is True


# ============================================================================
# Pytest Plugins (Optional)
# ============================================================================

# pytest_plugins = ["pytest_benchmark"]  # Uncomment if using benchmark
