"""
Tests für CA Service
Unit tests für die CAService-Klasse
"""

import pytest
from datetime import datetime

from pki.ca_service import CAService
from pki.crypto_utils import generate_key_pair, generate_csr
from pki.exceptions import (
    CANotInitializedError,
    InvalidCSRError
)


@pytest.fixture
def ca_service():
    """CA Service Fixture (nicht initialisiert)"""
    service = CAService()
    yield service
    service.reset()


@pytest.fixture
def initialized_ca():
    """CA Service Fixture (initialisiert)"""
    service = CAService(auto_initialize=True)
    yield service
    service.reset()


class TestCAInitialization:
    """Tests für CA-Initialisierung"""
    
    def test_ca_not_initialized_by_default(self, ca_service):
        """Test: CA ist standardmäßig nicht initialisiert"""
        assert ca_service.ca_initialized is False
    
    def test_ca_auto_initialize(self):
        """Test: Auto-Initialisierung"""
        ca = CAService(auto_initialize=True)
        assert ca.ca_initialized is True
        ca.reset()
    
    def test_initialize_ca(self, ca_service):
        """Test: Manuelle CA-Initialisierung"""
        result = ca_service.initialize_ca()
        
        assert result is True
        assert ca_service.ca_initialized is True
    
    def test_initialize_ca_twice(self, ca_service):
        """Test: Doppelte Initialisierung"""
        ca_service.initialize_ca()
        result = ca_service.initialize_ca()
        
        assert result is True  # Sollte OK sein
    
    def test_ca_certificate_created(self, initialized_ca):
        """Test: CA-Zertifikat wird erstellt"""
        cert_pem = initialized_ca.get_ca_certificate()
        
        assert "BEGIN CERTIFICATE" in cert_pem
        assert "MOCK_CA_CERTIFICATE" in cert_pem
        assert "CA:TRUE" in cert_pem


class TestCAInfo:
    """Tests für CA-Informationen"""
    
    def test_get_ca_info(self, initialized_ca):
        """Test: CA-Informationen abrufen"""
        info = initialized_ca.get_ca_info()
        
        assert "ca_name" in info
        assert "initialized" in info
        assert info["initialized"] is True
        assert "certificate" in info
        assert "statistics" in info
    
    def test_get_ca_info_not_initialized(self, ca_service):
        """Test: CA-Info ohne Initialisierung"""
        with pytest.raises(CANotInitializedError):
            ca_service.get_ca_info()
    
    def test_get_ca_certificate(self, initialized_ca):
        """Test: CA-Zertifikat abrufen"""
        cert_pem = initialized_ca.get_ca_certificate()
        
        assert cert_pem is not None
        assert isinstance(cert_pem, str)
        assert "BEGIN CERTIFICATE" in cert_pem
    
    def test_get_ca_certificate_not_initialized(self, ca_service):
        """Test: CA-Cert ohne Initialisierung"""
        with pytest.raises(CANotInitializedError):
            ca_service.get_ca_certificate()


class TestCSRSigning:
    """Tests für CSR-Signierung"""
    
    def test_sign_csr_basic(self, initialized_ca):
        """Test: Basis CSR-Signierung"""
        # Erstelle CSR
        private_key, public_key = generate_key_pair()
        csr_pem = generate_csr(
            private_key_pem=private_key,
            common_name="test.veritas.local"
        )
        
        # Signiere CSR
        signed_cert = initialized_ca.sign_csr(csr_pem)
        
        assert signed_cert is not None
        assert "cert_id" in signed_cert
        assert "serial_number" in signed_cert
        assert "cert_pem" in signed_cert
        assert "BEGIN CERTIFICATE" in signed_cert["cert_pem"]
    
    def test_sign_csr_with_validity(self, initialized_ca):
        """Test: CSR-Signierung mit custom Validity"""
        private_key, _ = generate_key_pair()
        csr_pem = generate_csr(
            private_key_pem=private_key,
            common_name="validity.test"
        )
        
        signed_cert = initialized_ca.sign_csr(csr_pem, validity_days=730)
        
        assert signed_cert is not None
        # Prüfe dass Validity gesetzt wurde
        delta = signed_cert["valid_until"] - signed_cert["valid_from"]
        assert delta.days == 730
    
    def test_sign_csr_not_initialized(self, ca_service):
        """Test: CSR-Signierung ohne CA-Init"""
        with pytest.raises(CANotInitializedError):
            ca_service.sign_csr("fake_csr")
    
    def test_sign_invalid_csr(self, initialized_ca):
        """Test: Ungültiger CSR"""
        with pytest.raises(InvalidCSRError):
            initialized_ca.sign_csr("not a valid csr")
    
    def test_sign_csr_empty(self, initialized_ca):
        """Test: Leerer CSR"""
        with pytest.raises(InvalidCSRError):
            initialized_ca.sign_csr("")
    
    def test_sign_multiple_csrs(self, initialized_ca):
        """Test: Mehrere CSRs signieren"""
        certs = []
        for i in range(5):
            private_key, _ = generate_key_pair()
            csr_pem = generate_csr(
                private_key_pem=private_key,
                common_name=f"test{i}.local"
            )
            cert = initialized_ca.sign_csr(csr_pem)
            certs.append(cert)
        
        assert len(certs) == 5
        # Seriennummern sollten unique sein
        serials = [c["serial_number"] for c in certs]
        assert len(set(serials)) == 5


class TestCRL:
    """Tests für Certificate Revocation List"""
    
    def test_get_crl_empty(self, initialized_ca):
        """Test: Leere CRL"""
        crl_pem = initialized_ca.get_crl()
        
        assert "BEGIN X509 CRL" in crl_pem
        assert "Revoked Certificates: 0" in crl_pem
        assert "No revoked certificates" in crl_pem
    
    def test_get_crl_not_initialized(self, ca_service):
        """Test: CRL ohne Initialisierung"""
        with pytest.raises(CANotInitializedError):
            ca_service.get_crl()
    
    def test_get_crl_with_revoked(self, initialized_ca):
        """Test: CRL mit widerrufenen Zertifikaten"""
        # Erstelle und signiere Zertifikat
        private_key, _ = generate_key_pair()
        csr_pem = generate_csr(
            private_key_pem=private_key,
            common_name="revoke.test"
        )
        cert = initialized_ca.sign_csr(csr_pem)
        
        # Widerrufe Zertifikat
        initialized_ca.revoke_certificate(
            cert["serial_number"],
            reason="key_compromise"
        )
        
        # Hole CRL
        crl_pem = initialized_ca.get_crl()
        
        assert "Revoked Certificates: 1" in crl_pem
        assert cert["serial_number"] in crl_pem
        assert "key_compromise" in crl_pem


class TestCertificateRevocation:
    """Tests für Zertifikatswiderruf"""
    
    def test_revoke_certificate(self, initialized_ca):
        """Test: Zertifikat widerrufen"""
        # Erstelle Zertifikat
        private_key, _ = generate_key_pair()
        csr_pem = generate_csr(
            private_key_pem=private_key,
            common_name="revoke.test"
        )
        cert = initialized_ca.sign_csr(csr_pem)
        
        # Widerrufe
        result = initialized_ca.revoke_certificate(cert["serial_number"])
        
        assert result is True
    
    def test_revoke_with_reason(self, initialized_ca):
        """Test: Widerruf mit Grund"""
        private_key, _ = generate_key_pair()
        csr_pem = generate_csr(
            private_key_pem=private_key,
            common_name="revoke_reason.test"
        )
        cert = initialized_ca.sign_csr(csr_pem)
        
        result = initialized_ca.revoke_certificate(
            cert["serial_number"],
            reason="superseded"
        )
        
        assert result is True
        
        # Prüfe CRL
        crl = initialized_ca.get_crl()
        assert "superseded" in crl
    
    def test_revoke_nonexistent_certificate(self, initialized_ca):
        """Test: Nicht existierendes Zertifikat widerrufen"""
        result = initialized_ca.revoke_certificate("non-existent-serial")
        assert result is False
    
    def test_revoke_not_initialized(self, ca_service):
        """Test: Widerruf ohne Initialisierung"""
        with pytest.raises(CANotInitializedError):
            ca_service.revoke_certificate("some-serial")


class TestChainVerification:
    """Tests für Zertifikatsketten-Verifikation"""
    
    def test_verify_valid_chain(self, initialized_ca):
        """Test: Valide Chain verifizieren"""
        # Erstelle und signiere Zertifikat
        private_key, _ = generate_key_pair()
        csr_pem = generate_csr(
            private_key_pem=private_key,
            common_name="verify.test"
        )
        cert = initialized_ca.sign_csr(csr_pem)
        
        # Verifiziere
        is_valid = initialized_ca.verify_chain(cert["cert_pem"])
        
        assert is_valid is True
    
    def test_verify_revoked_certificate(self, initialized_ca):
        """Test: Widerrufenes Zertifikat"""
        # Erstelle Zertifikat
        private_key, _ = generate_key_pair()
        csr_pem = generate_csr(
            private_key_pem=private_key,
            common_name="verify_revoked.test"
        )
        cert = initialized_ca.sign_csr(csr_pem)
        
        # Widerrufe
        initialized_ca.revoke_certificate(cert["serial_number"])
        
        # Verifiziere (mit CRL-Check)
        is_valid = initialized_ca.verify_chain(
            cert["cert_pem"],
            include_crl_check=True
        )
        
        assert is_valid is False
    
    def test_verify_invalid_cert(self, initialized_ca):
        """Test: Ungültiges Zertifikat"""
        is_valid = initialized_ca.verify_chain("not a certificate")
        assert is_valid is False
    
    def test_verify_not_initialized(self, ca_service):
        """Test: Verifikation ohne Initialisierung"""
        with pytest.raises(CANotInitializedError):
            ca_service.verify_chain("fake_cert")


class TestSignedCertificates:
    """Tests für signierte Zertifikate"""
    
    def test_get_signed_certificates_empty(self, initialized_ca):
        """Test: Leere Liste"""
        certs = initialized_ca.get_signed_certificates()
        assert certs == []
    
    def test_get_signed_certificates(self, initialized_ca):
        """Test: Signierte Zertifikate abrufen"""
        # Erstelle mehrere Zertifikate
        for i in range(3):
            private_key, _ = generate_key_pair()
            csr_pem = generate_csr(
                private_key_pem=private_key,
                common_name=f"test{i}.local"
            )
            initialized_ca.sign_csr(csr_pem)
        
        certs = initialized_ca.get_signed_certificates()
        
        assert len(certs) == 3
    
    def test_get_signed_certificates_exclude_revoked(self, initialized_ca):
        """Test: Widerrufene ausschließen"""
        # Erstelle Zertifikate
        private_key1, _ = generate_key_pair()
        csr1 = generate_csr(private_key1, "test1.local")
        cert1 = initialized_ca.sign_csr(csr1)
        
        private_key2, _ = generate_key_pair()
        csr2 = generate_csr(private_key2, "test2.local")
        cert2 = initialized_ca.sign_csr(csr2)
        
        # Widerrufe eins
        initialized_ca.revoke_certificate(cert2["serial_number"])
        
        # Ohne revoked
        active_certs = initialized_ca.get_signed_certificates(
            include_revoked=False
        )
        assert len(active_certs) == 1
        
        # Mit revoked
        all_certs = initialized_ca.get_signed_certificates(
            include_revoked=True
        )
        assert len(all_certs) == 2
    
    def test_get_signed_certificates_not_initialized(self, ca_service):
        """Test: Ohne Initialisierung"""
        with pytest.raises(CANotInitializedError):
            ca_service.get_signed_certificates()


class TestCABundle:
    """Tests für CA-Bundle"""
    
    def test_export_ca_bundle(self, initialized_ca):
        """Test: CA-Bundle exportieren"""
        bundle = initialized_ca.export_ca_bundle()
        
        assert bundle is not None
        assert "BEGIN CERTIFICATE" in bundle
        assert "MOCK_CA_CERTIFICATE" in bundle
    
    def test_export_ca_bundle_not_initialized(self, ca_service):
        """Test: Bundle ohne Initialisierung"""
        with pytest.raises(CANotInitializedError):
            ca_service.export_ca_bundle()


class TestCAReset:
    """Tests für CA-Reset"""
    
    def test_reset_ca(self, initialized_ca):
        """Test: CA zurücksetzen"""
        # Erstelle Zertifikat
        private_key, _ = generate_key_pair()
        csr_pem = generate_csr(private_key, "reset.test")
        initialized_ca.sign_csr(csr_pem)
        
        # Reset
        initialized_ca.reset()
        
        assert initialized_ca.ca_initialized is False
