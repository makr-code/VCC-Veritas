"""
Unit Tests for backend/pki/ca_service.py (NEW Implementation)

Tests for PRODUCTION PKI - NO MOCK MODE
Based on actual API from backend/pki/ca_service.py
"""

import os
import pytest
import tempfile
import shutil
from backend.pki.ca_service import CAService
from backend.pki.cert_manager import CertificateManager
from backend.pki.crypto_utils import generate_keypair, generate_csr


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_storage():
    """Create temporary storage directories"""
    pki_dir = tempfile.mkdtemp(prefix="pki_test_")
    ca_dir = tempfile.mkdtemp(prefix="ca_test_")
    yield pki_dir, ca_dir
    shutil.rmtree(pki_dir, ignore_errors=True)
    shutil.rmtree(ca_dir, ignore_errors=True)


@pytest.fixture
def cert_manager(temp_storage):
    """Create CertificateManager instance"""
    pki_dir, _ = temp_storage
    return CertificateManager(pki_dir)


@pytest.fixture
def ca_service(temp_storage, cert_manager):
    """Create CAService instance"""
    _, ca_dir = temp_storage
    return CAService(ca_dir, cert_manager)


@pytest.fixture
def end_entity_csr():
    """Generate end-entity CSR"""
    private_key, _ = generate_keypair(2048)
    csr = generate_csr(
        private_key,
        common_name="test.example.com",
        organization="Test Corp"
    )
    return csr, private_key


# ============================================================================
# Root CA Tests
# ============================================================================

class TestRootCA:
    """Test Root CA operations"""
    
    def test_initialize_root_ca(self, ca_service):
        """Test Root CA initialization"""
        ca_info = ca_service.initialize_root_ca(
            common_name="Test Root CA",
            validity_days=3650
        )
        
        assert ca_info is not None
        assert isinstance(ca_info, dict)
        assert ca_info["common_name"] == "Test Root CA"
        assert "serial_number" in ca_info
        assert "key_size" in ca_info
    
    def test_get_ca_certificate(self, ca_service):
        """Test get CA certificate"""
        # Initialize first
        ca_service.initialize_root_ca("Test Root CA", 3650)
        
        # Get certificate
        ca_cert = ca_service.get_ca_certificate()
        
        assert ca_cert is not None
        assert isinstance(ca_cert, bytes)
        assert b"BEGIN CERTIFICATE" in ca_cert


# ============================================================================
# CSR Signing Tests
# ============================================================================

class TestCSRSigning:
    """Test CSR signing"""
    
    def test_sign_csr(self, ca_service, end_entity_csr):
        """Test CSR signing"""
        # Initialize CA
        ca_service.initialize_root_ca("Test Root CA", 3650)
        
        # Sign CSR
        csr_pem, _ = end_entity_csr
        cert_id, cert_pem = ca_service.sign_csr(
            csr_pem=csr_pem,
            validity_days=365,
            is_ca=False
        )
        
        assert cert_id is not None
        assert cert_pem is not None
        assert b"BEGIN CERTIFICATE" in cert_pem


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
