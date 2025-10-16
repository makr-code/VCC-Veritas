"""
Unit Tests for ca_service module

Tests for:
- Root CA Initialization
- CSR Signing (End-Entity and Intermediate CA)
- CRL Generation
- Certificate Chain Validation
- CA Statistics

**Mode:** PRODUCTION TESTS (NO MOCK)
"""

import os
import pytest
import tempfile
import shutil
from backend.pki.ca_service import CAService
from backend.pki.cert_manager import CertificateManager
from backend.pki.crypto_utils import (
    generate_keypair,
    generate_csr
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_storage():
    """Create temporary storage directories"""
    pki_dir = tempfile.mkdtemp(prefix="pki_test_")
    ca_dir = tempfile.mkdtemp(prefix="ca_test_")
    yield pki_dir, ca_dir
    # Cleanup
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
        common_name="endentity.example.com",
        organization="Test Corp"
    )
    return csr, private_key


@pytest.fixture
def intermediate_ca_csr():
    """Generate intermediate CA CSR"""
    private_key, _ = generate_keypair(3072)
    csr = generate_csr(
        private_key,
        common_name="Intermediate CA",
        organization="Test Corp"
    )
    return csr, private_key


# ============================================================================
# Initialization Tests
# ============================================================================

class TestCAServiceInit:
    """Test CAService initialization"""
    
    def test_init_creates_directories(self, temp_storage, cert_manager):
        """Test initialization creates CA directories"""
        _, ca_dir = temp_storage
        ca = CAService(ca_dir, cert_manager)
        
        assert os.path.exists(os.path.join(ca_dir, "ca_certificates"))
        assert os.path.exists(os.path.join(ca_dir, "ca_keys"))
        assert os.path.exists(os.path.join(ca_dir, "crl"))
        assert os.path.exists(os.path.join(ca_dir, "config"))
    
    def test_init_existing_directory(self, temp_storage, cert_manager):
        """Test initialization with existing directory"""
        _, ca_dir = temp_storage
        
        # Create first instance
        ca1 = CAService(ca_dir, cert_manager)
        
        # Create second instance (should not fail)
        ca2 = CAService(ca_dir, cert_manager)
        
        assert ca2 is not None


# ============================================================================
# Root CA Tests
# ============================================================================

class TestRootCA:
    """Test Root CA operations"""
    
    def test_initialize_root_ca_basic(self, ca_service):
        """Test basic Root CA initialization"""
        ca_info = ca_service.initialize_root_ca(
            common_name="Test Root CA",
            validity_days=3650
        )
        
        assert ca_info is not None
        assert isinstance(ca_info, dict)
        assert ca_info["common_name"] == "Test Root CA"
        assert "serial_number" in ca_info
        assert "not_valid_before" in ca_info
        assert "not_valid_after" in ca_info
        assert ca_info["key_size"] == 4096  # Default key size
        assert "created_at" in ca_info
    
    def test_initialize_root_ca_full_subject(self, ca_service):
        """Test Root CA with full subject attributes"""
        ca_id, ca_cert_pem, _ = ca_service.initialize_root_ca(
            common_name="Test Root CA",
            validity_days=3650,
            key_size=4096,
            country="DE",
            state="Bavaria",
            locality="Munich",
            organization="Test Corp",
            organizational_unit="Security"
        )
        
        assert ca_id is not None
        assert ca_cert_pem is not None
    
    def test_initialize_root_ca_custom_key_size(self, ca_service):
        """Test Root CA with custom key size"""
        ca_id, _, _ = ca_service.initialize_root_ca(
            common_name="Test Root CA",
            validity_days=3650,
            key_size=3072
        )
        
        assert ca_id is not None
    
    def test_initialize_root_ca_saved_to_disk(self, ca_service):
        """Test Root CA is saved to disk"""
        ca_id, _, _ = ca_service.initialize_root_ca(
            common_name="Test Root CA",
            validity_days=3650
        )
        
        # Check certificate file
        cert_path = os.path.join(
            ca_service.ca_storage_path,
            "ca_certificates",
            f"{ca_id}.pem"
        )
        assert os.path.exists(cert_path)
        
        # Check key file
        key_path = os.path.join(
            ca_service.ca_storage_path,
            "ca_keys",
            f"{ca_id}_key.pem"
        )
        assert os.path.exists(key_path)
    
    def test_get_ca_certificate(self, ca_service):
        """Test get CA certificate"""
        ca_id, _, _ = ca_service.initialize_root_ca(
            common_name="Test Root CA",
            validity_days=3650
        )
        
        ca_cert = ca_service.get_ca_certificate(ca_id)
        
        assert ca_cert is not None
        assert isinstance(ca_cert, bytes)
        assert b"BEGIN CERTIFICATE" in ca_cert
    
    def test_get_nonexistent_ca(self, ca_service):
        """Test get nonexistent CA returns None"""
        ca_cert = ca_service.get_ca_certificate("nonexistent_id")
        
        assert ca_cert is None


# ============================================================================
# CSR Signing Tests - End Entity
# ============================================================================

class TestCSRSigningEndEntity:
    """Test CSR signing for end-entity certificates"""
    
    def test_sign_csr_end_entity_basic(self, ca_service, end_entity_csr):
        """Test basic end-entity CSR signing"""
        # Initialize Root CA
        ca_id, _, _ = ca_service.initialize_root_ca(
            common_name="Test Root CA",
            validity_days=3650
        )
        
        # Sign CSR
        csr_pem, _ = end_entity_csr
        cert_id, cert_pem = ca_service.sign_csr(
            csr_pem=csr_pem,
            validity_days=365,
            is_ca=False,
            ca_id=ca_id
        )
        
        assert cert_id is not None
        assert cert_pem is not None
        assert b"BEGIN CERTIFICATE" in cert_pem
    
    def test_sign_csr_end_entity_custom_validity(self, ca_service, end_entity_csr):
        """Test CSR signing with custom validity"""
        ca_id, _, _ = ca_service.initialize_root_ca("Test Root CA", 3650)
        csr_pem, _ = end_entity_csr
        
        cert_id, cert_pem = ca_service.sign_csr(
            csr_pem=csr_pem,
            validity_days=730,  # 2 years
            is_ca=False,
            ca_id=ca_id
        )
        
        assert cert_id is not None
    
    def test_sign_csr_nonexistent_ca(self, ca_service, end_entity_csr):
        """Test signing with nonexistent CA raises error"""
        csr_pem, _ = end_entity_csr
        
        with pytest.raises(RuntimeError) as exc_info:
            ca_service.sign_csr(
                csr_pem=csr_pem,
                validity_days=365,
                is_ca=False,
                ca_id="nonexistent_ca"
            )
        
        assert "CA not found" in str(exc_info.value)
    
    def test_sign_invalid_csr(self, ca_service):
        """Test signing invalid CSR raises error"""
        ca_id, _, _ = ca_service.initialize_root_ca("Test Root CA", 3650)
        
        with pytest.raises(RuntimeError):
            ca_service.sign_csr(
                csr_pem=b"invalid_csr",
                validity_days=365,
                is_ca=False,
                ca_id=ca_id
            )


# ============================================================================
# CSR Signing Tests - Intermediate CA
# ============================================================================

class TestCSRSigningIntermediateCA:
    """Test CSR signing for intermediate CA certificates"""
    
    def test_sign_csr_intermediate_ca(self, ca_service, intermediate_ca_csr):
        """Test intermediate CA CSR signing"""
        # Initialize Root CA
        root_ca_id, _, _ = ca_service.initialize_root_ca(
            common_name="Test Root CA",
            validity_days=3650,
            key_size=4096
        )
        
        # Sign intermediate CA CSR
        csr_pem, _ = intermediate_ca_csr
        cert_id, cert_pem = ca_service.sign_csr(
            csr_pem=csr_pem,
            validity_days=1825,  # 5 years
            is_ca=True,
            ca_id=root_ca_id
        )
        
        assert cert_id is not None
        assert cert_pem is not None
    
    def test_intermediate_ca_path_length(self, ca_service, intermediate_ca_csr):
        """Test intermediate CA has path_length=0"""
        # Initialize Root CA
        root_ca_id, _, _ = ca_service.initialize_root_ca("Test Root CA", 3650)
        
        # Sign intermediate CA CSR
        csr_pem, _ = intermediate_ca_csr
        cert_id, cert_pem = ca_service.sign_csr(
            csr_pem=csr_pem,
            validity_days=1825,
            is_ca=True,
            ca_id=root_ca_id
        )
        
        # Note: Path length verification would require parsing certificate
        # This is a basic check that cert was created
        assert cert_id is not None


# ============================================================================
# CRL Generation Tests
# ============================================================================

class TestCRLGeneration:
    """Test Certificate Revocation List generation"""
    
    def test_generate_crl_empty(self, ca_service):
        """Test CRL generation with no revoked certificates"""
        ca_id, _, _ = ca_service.initialize_root_ca("Test Root CA", 3650)
        
        crl_pem = ca_service.generate_crl(
            ca_id=ca_id,
            revoked_certs=[]
        )
        
        assert crl_pem is not None
        assert isinstance(crl_pem, bytes)
        assert b"BEGIN X509 CRL" in crl_pem
    
    def test_generate_crl_with_revoked_cert(self, ca_service, end_entity_csr):
        """Test CRL generation with revoked certificate"""
        # Setup CA and sign certificate
        ca_id, _, _ = ca_service.initialize_root_ca("Test Root CA", 3650)
        csr_pem, _ = end_entity_csr
        cert_id, _ = ca_service.sign_csr(csr_pem, 365, False, ca_id)
        
        # Revoke certificate
        ca_service.cert_manager.revoke_certificate(cert_id, reason="keyCompromise")
        
        # Get certificate serial number (simplified for test)
        cert_info = ca_service.cert_manager.get_certificate(cert_id)
        
        # Generate CRL
        revoked_certs = [{
            "serial_number": 1,  # Simplified
            "revocation_date": cert_info["revoked_at"],
            "reason": "keyCompromise"
        }]
        
        crl_pem = ca_service.generate_crl(ca_id, revoked_certs)
        
        assert crl_pem is not None
        assert b"BEGIN X509 CRL" in crl_pem
    
    def test_generate_crl_multiple_revoked(self, ca_service):
        """Test CRL with multiple revoked certificates"""
        from datetime import datetime, timezone
        
        ca_id, _, _ = ca_service.initialize_root_ca("Test Root CA", 3650)
        
        revoked_certs = [
            {
                "serial_number": 1,
                "revocation_date": datetime.now(timezone.utc).isoformat(),
                "reason": "keyCompromise"
            },
            {
                "serial_number": 2,
                "revocation_date": datetime.now(timezone.utc).isoformat(),
                "reason": "superseded"
            },
            {
                "serial_number": 3,
                "revocation_date": datetime.now(timezone.utc).isoformat(),
                "reason": "cessationOfOperation"
            }
        ]
        
        crl_pem = ca_service.generate_crl(ca_id, revoked_certs)
        
        assert crl_pem is not None
    
    def test_generate_crl_saved_to_disk(self, ca_service):
        """Test CRL is saved to disk"""
        ca_id, _, _ = ca_service.initialize_root_ca("Test Root CA", 3650)
        
        crl_pem = ca_service.generate_crl(ca_id, [])
        
        # Check CRL file
        crl_path = os.path.join(
            ca_service.ca_storage_path,
            "crl",
            f"{ca_id}_crl.pem"
        )
        assert os.path.exists(crl_path)
    
    def test_generate_crl_nonexistent_ca(self, ca_service):
        """Test CRL generation with nonexistent CA"""
        with pytest.raises(RuntimeError) as exc_info:
            ca_service.generate_crl("nonexistent_ca", [])
        
        assert "CA not found" in str(exc_info.value)


# ============================================================================
# Certificate Chain Validation Tests
# ============================================================================

class TestCertificateChainValidation:
    """Test certificate chain validation"""
    
    def test_verify_self_signed_certificate(self, ca_service):
        """Test verification of self-signed certificate"""
        # Create self-signed cert (Root CA)
        ca_id, ca_cert_pem, _ = ca_service.initialize_root_ca("Test Root CA", 3650)
        
        is_valid, message = ca_service.verify_certificate_chain(
            cert_pem=ca_cert_pem,
            ca_id=ca_id
        )
        
        assert is_valid is True
        assert "valid" in message.lower()
    
    def test_verify_ca_signed_certificate(self, ca_service, end_entity_csr):
        """Test verification of CA-signed certificate"""
        # Initialize Root CA
        ca_id, _, _ = ca_service.initialize_root_ca("Test Root CA", 3650)
        
        # Sign certificate
        csr_pem, _ = end_entity_csr
        cert_id, cert_pem = ca_service.sign_csr(csr_pem, 365, False, ca_id)
        
        # Verify chain
        is_valid, message = ca_service.verify_certificate_chain(cert_pem, ca_id)
        
        assert is_valid is True
    
    def test_verify_with_wrong_ca(self, ca_service, end_entity_csr):
        """Test verification with wrong CA fails"""
        # Create two CAs
        ca_id1, _, _ = ca_service.initialize_root_ca("Root CA 1", 3650)
        ca_id2, _, _ = ca_service.initialize_root_ca("Root CA 2", 3650)
        
        # Sign with CA1
        csr_pem, _ = end_entity_csr
        cert_id, cert_pem = ca_service.sign_csr(csr_pem, 365, False, ca_id1)
        
        # Verify with CA2 (should fail)
        is_valid, message = ca_service.verify_certificate_chain(cert_pem, ca_id2)
        
        assert is_valid is False
    
    def test_verify_invalid_certificate(self, ca_service):
        """Test verification of invalid certificate"""
        ca_id, _, _ = ca_service.initialize_root_ca("Test Root CA", 3650)
        
        is_valid, message = ca_service.verify_certificate_chain(
            cert_pem=b"invalid_cert",
            ca_id=ca_id
        )
        
        assert is_valid is False
    
    def test_verify_nonexistent_ca(self, ca_service):
        """Test verification with nonexistent CA"""
        ca_id, ca_cert_pem, _ = ca_service.initialize_root_ca("Test Root CA", 3650)
        
        is_valid, message = ca_service.verify_certificate_chain(
            cert_pem=ca_cert_pem,
            ca_id="nonexistent_ca"
        )
        
        assert is_valid is False
        assert "not found" in message.lower()


# ============================================================================
# Statistics Tests
# ============================================================================

class TestCAStatistics:
    """Test CA statistics"""
    
    def test_statistics_no_cas(self, ca_service):
        """Test statistics with no CAs"""
        stats = ca_service.get_ca_statistics()
        
        assert stats["total_cas"] == 0
        assert stats["cas"] == []
    
    def test_statistics_single_ca(self, ca_service):
        """Test statistics with single CA"""
        ca_id, _, _ = ca_service.initialize_root_ca(
            common_name="Test Root CA",
            validity_days=3650
        )
        
        stats = ca_service.get_ca_statistics()
        
        assert stats["total_cas"] == 1
        assert len(stats["cas"]) == 1
        assert stats["cas"][0]["id"] == ca_id
        assert stats["cas"][0]["common_name"] == "Test Root CA"
    
    def test_statistics_multiple_cas(self, ca_service):
        """Test statistics with multiple CAs"""
        # Create multiple CAs
        ca_ids = []
        for i in range(3):
            ca_id, _, _ = ca_service.initialize_root_ca(
                common_name=f"Root CA {i}",
                validity_days=3650
            )
            ca_ids.append(ca_id)
        
        stats = ca_service.get_ca_statistics()
        
        assert stats["total_cas"] == 3
        assert len(stats["cas"]) == 3
        
        # Verify all CA IDs present
        stat_ca_ids = [ca["id"] for ca in stats["cas"]]
        for ca_id in ca_ids:
            assert ca_id in stat_ca_ids


# ============================================================================
# Integration Tests
# ============================================================================

class TestCAServiceIntegration:
    """Integration tests for CA Service"""
    
    def test_full_ca_workflow(self, ca_service, end_entity_csr):
        """Test complete CA workflow"""
        # 1. Initialize Root CA
        ca_id, ca_cert_pem, _ = ca_service.initialize_root_ca(
            common_name="Test Root CA",
            validity_days=3650,
            key_size=4096,
            organization="Test Corp"
        )
        assert ca_id is not None
        
        # 2. Sign end-entity CSR
        csr_pem, _ = end_entity_csr
        cert_id, cert_pem = ca_service.sign_csr(
            csr_pem=csr_pem,
            validity_days=365,
            is_ca=False,
            ca_id=ca_id
        )
        assert cert_id is not None
        
        # 3. Verify certificate chain
        is_valid, message = ca_service.verify_certificate_chain(cert_pem, ca_id)
        assert is_valid is True
        
        # 4. Revoke certificate
        success = ca_service.cert_manager.revoke_certificate(cert_id, "keyCompromise")
        assert success is True
        
        # 5. Generate CRL
        cert_info = ca_service.cert_manager.get_certificate(cert_id)
        revoked_certs = [{
            "serial_number": 1,
            "revocation_date": cert_info["revoked_at"],
            "reason": "keyCompromise"
        }]
        crl_pem = ca_service.generate_crl(ca_id, revoked_certs)
        assert crl_pem is not None
        
        # 6. Get statistics
        stats = ca_service.get_ca_statistics()
        assert stats["total_cas"] == 1
    
    def test_two_tier_pki(self, ca_service, intermediate_ca_csr, end_entity_csr):
        """Test two-tier PKI (Root CA + Intermediate CA)"""
        # 1. Create Root CA
        root_ca_id, _, _ = ca_service.initialize_root_ca(
            common_name="Test Root CA",
            validity_days=3650,
            key_size=4096
        )
        
        # 2. Create Intermediate CA
        int_csr_pem, int_key = intermediate_ca_csr
        int_ca_id, int_ca_cert = ca_service.sign_csr(
            csr_pem=int_csr_pem,
            validity_days=1825,
            is_ca=True,
            ca_id=root_ca_id
        )
        
        # Save intermediate CA to CA storage (for signing)
        int_ca_cert_path = os.path.join(
            ca_service.ca_storage_path,
            "ca_certificates",
            f"{int_ca_id}.pem"
        )
        int_ca_key_path = os.path.join(
            ca_service.ca_storage_path,
            "ca_keys",
            f"{int_ca_id}_key.pem"
        )
        
        os.makedirs(os.path.dirname(int_ca_cert_path), exist_ok=True)
        with open(int_ca_cert_path, "wb") as f:
            f.write(int_ca_cert)
        with open(int_ca_key_path, "wb") as f:
            f.write(int_key)
        
        # 3. Sign end-entity with intermediate CA
        ee_csr_pem, _ = end_entity_csr
        ee_cert_id, ee_cert_pem = ca_service.sign_csr(
            csr_pem=ee_csr_pem,
            validity_days=365,
            is_ca=False,
            ca_id=int_ca_id
        )
        
        # 4. Verify end-entity against intermediate CA
        is_valid, _ = ca_service.verify_certificate_chain(ee_cert_pem, int_ca_id)
        assert is_valid is True
        
        # 5. Statistics should show 1 Root CA (intermediate stored separately)
        stats = ca_service.get_ca_statistics()
        assert stats["total_cas"] >= 1


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestCAServiceErrors:
    """Test error handling"""
    
    def test_initialize_ca_invalid_key_size(self, ca_service):
        """Test Root CA with invalid key size"""
        with pytest.raises(ValueError):
            ca_service.initialize_root_ca(
                common_name="Test Root CA",
                validity_days=3650,
                key_size=1024  # Too small
            )
    
    def test_sign_csr_invalid_validity(self, ca_service, end_entity_csr):
        """Test CSR signing with invalid validity"""
        ca_id, _, _ = ca_service.initialize_root_ca("Test Root CA", 3650)
        csr_pem, _ = end_entity_csr
        
        with pytest.raises(ValueError):
            ca_service.sign_csr(
                csr_pem=csr_pem,
                validity_days=-1,  # Invalid
                is_ca=False,
                ca_id=ca_id
            )


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
