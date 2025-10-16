"""
Tests für Certificate Manager
Unit tests für die CertificateManager-Klasse
"""

import pytest
from datetime import datetime, timedelta

from pki.cert_manager import (
    CertificateManager,
    CertificateStatus,
    CertificateType
)
from pki.exceptions import (
    CertificateNotFoundError,
    InvalidCertificateError
)


@pytest.fixture
def cert_manager():
    """Certificate Manager Fixture"""
    manager = CertificateManager(mock_mode=True)
    yield manager
    manager.clear_all()


class TestCertificateCreation:
    """Tests für Zertifikatserstellung"""
    
    def test_create_certificate_basic(self, cert_manager):
        """Test: Basis-Zertifikat erstellen"""
        cert = cert_manager.create_certificate("test.veritas.local")
        
        assert cert is not None
        assert cert["common_name"] == "test.veritas.local"
        assert "cert_id" in cert
        assert "fingerprint" in cert
        assert "cert_pem" in cert
        assert cert["status"] == CertificateStatus.VALID.value
    
    def test_create_certificate_with_details(self, cert_manager):
        """Test: Zertifikat mit vollständigen Details"""
        cert = cert_manager.create_certificate(
            common_name="api.veritas.local",
            validity_days=730,
            key_size=4096,
            cert_type=CertificateType.SERVER,
            country="DE",
            state="NRW",
            locality="Köln",
            organization="VERITAS",
            organizational_unit="IT",
            email="admin@veritas.local",
            sans=["www.veritas.local", "api.veritas.local"]
        )
        
        assert cert["common_name"] == "api.veritas.local"
        assert cert["key_size"] == 4096
        assert cert["cert_type"] == CertificateType.SERVER.value
        assert cert["subject"]["country"] == "DE"
        assert cert["subject"]["organization"] == "VERITAS"
        assert len(cert["sans"]) == 2
    
    def test_create_certificate_invalid_cn(self, cert_manager):
        """Test: Zertifikat ohne Common Name"""
        with pytest.raises(InvalidCertificateError):
            cert_manager.create_certificate("")
    
    def test_create_certificate_generates_keys(self, cert_manager):
        """Test: Schlüsselgenerierung bei Zertifikatserstellung"""
        cert = cert_manager.create_certificate("keys.test")
        
        assert "private_key_pem" in cert
        assert "public_key_pem" in cert
        assert "PRIVATE KEY" in cert["private_key_pem"]
        assert "PUBLIC KEY" in cert["public_key_pem"]


class TestCertificateRetrieval:
    """Tests für Zertifikatsabruf"""
    
    def test_get_certificate_by_id(self, cert_manager):
        """Test: Zertifikat per ID abrufen"""
        created_cert = cert_manager.create_certificate("get.test")
        cert_id = created_cert["cert_id"]
        
        retrieved_cert = cert_manager.get_certificate(cert_id)
        
        assert retrieved_cert is not None
        assert retrieved_cert["cert_id"] == cert_id
        assert retrieved_cert["common_name"] == "get.test"
    
    def test_get_certificate_not_found(self, cert_manager):
        """Test: Nicht existierendes Zertifikat"""
        cert = cert_manager.get_certificate("non-existent-id")
        assert cert is None
    
    def test_get_certificate_by_fingerprint(self, cert_manager):
        """Test: Zertifikat per Fingerprint abrufen"""
        created_cert = cert_manager.create_certificate("fingerprint.test")
        fingerprint = created_cert["fingerprint"]
        
        retrieved_cert = cert_manager.get_certificate_by_fingerprint(fingerprint)
        
        assert retrieved_cert is not None
        assert retrieved_cert["fingerprint"] == fingerprint


class TestCertificateListing:
    """Tests für Zertifikatslistung"""
    
    def test_list_certificates_empty(self, cert_manager):
        """Test: Leere Liste"""
        certs = cert_manager.list_certificates()
        assert certs == []
    
    def test_list_certificates_multiple(self, cert_manager):
        """Test: Mehrere Zertifikate auflisten"""
        cert_manager.create_certificate("test1.local")
        cert_manager.create_certificate("test2.local")
        cert_manager.create_certificate("test3.local")
        
        certs = cert_manager.list_certificates()
        
        assert len(certs) == 3
    
    def test_list_certificates_filter_by_status(self, cert_manager):
        """Test: Filter nach Status"""
        cert1 = cert_manager.create_certificate("valid.test")
        cert2 = cert_manager.create_certificate("revoke.test")
        cert_manager.revoke_certificate(cert2["cert_id"])
        
        valid_certs = cert_manager.list_certificates(
            status=CertificateStatus.VALID
        )
        revoked_certs = cert_manager.list_certificates(
            status=CertificateStatus.REVOKED
        )
        
        assert len(valid_certs) == 1
        assert len(revoked_certs) == 1
        assert valid_certs[0]["cert_id"] == cert1["cert_id"]
    
    def test_list_certificates_filter_by_type(self, cert_manager):
        """Test: Filter nach Typ"""
        cert_manager.create_certificate(
            "server.test",
            cert_type=CertificateType.SERVER
        )
        cert_manager.create_certificate(
            "client.test",
            cert_type=CertificateType.CLIENT
        )
        
        server_certs = cert_manager.list_certificates(
            cert_type=CertificateType.SERVER
        )
        client_certs = cert_manager.list_certificates(
            cert_type=CertificateType.CLIENT
        )
        
        assert len(server_certs) == 1
        assert len(client_certs) == 1
    
    def test_list_certificates_pagination(self, cert_manager):
        """Test: Pagination"""
        for i in range(10):
            cert_manager.create_certificate(f"test{i}.local")
        
        page1 = cert_manager.list_certificates(limit=5, offset=0)
        page2 = cert_manager.list_certificates(limit=5, offset=5)
        
        assert len(page1) == 5
        assert len(page2) == 5
        assert page1[0]["cert_id"] != page2[0]["cert_id"]


class TestCertificateRevocation:
    """Tests für Zertifikatswiderruf"""
    
    def test_revoke_certificate(self, cert_manager):
        """Test: Zertifikat widerrufen"""
        cert = cert_manager.create_certificate("revoke.test")
        cert_id = cert["cert_id"]
        
        result = cert_manager.revoke_certificate(cert_id)
        
        assert result is True
        revoked_cert = cert_manager.get_certificate(cert_id)
        assert revoked_cert["status"] == CertificateStatus.REVOKED.value
        assert revoked_cert["revoked_at"] is not None
    
    def test_revoke_certificate_with_reason(self, cert_manager):
        """Test: Zertifikat mit Grund widerrufen"""
        cert = cert_manager.create_certificate("revoke_reason.test")
        
        cert_manager.revoke_certificate(
            cert["cert_id"],
            reason="key_compromise"
        )
        
        revoked_cert = cert_manager.get_certificate(cert["cert_id"])
        assert revoked_cert["revocation_reason"] == "key_compromise"
    
    def test_revoke_nonexistent_certificate(self, cert_manager):
        """Test: Nicht existierendes Zertifikat widerrufen"""
        with pytest.raises(CertificateNotFoundError):
            cert_manager.revoke_certificate("non-existent-id")


class TestCertificateVerification:
    """Tests für Zertifikatsverifikation"""
    
    def test_verify_valid_certificate(self, cert_manager):
        """Test: Valides Zertifikat verifizieren"""
        cert = cert_manager.create_certificate("verify.test")
        
        is_valid = cert_manager.verify_certificate(cert["cert_pem"])
        
        assert is_valid is True
    
    def test_verify_revoked_certificate(self, cert_manager):
        """Test: Widerrufenes Zertifikat"""
        cert = cert_manager.create_certificate("verify_revoked.test")
        cert_manager.revoke_certificate(cert["cert_id"])
        
        is_valid = cert_manager.verify_certificate(cert["cert_pem"])
        
        assert is_valid is False
    
    def test_verify_invalid_pem(self, cert_manager):
        """Test: Ungültiger PEM-String"""
        is_valid = cert_manager.verify_certificate("invalid pem")
        assert is_valid is False


class TestCertificateRenewal:
    """Tests für Zertifikatserneuerung"""
    
    def test_renew_certificate(self, cert_manager):
        """Test: Zertifikat erneuern"""
        old_cert = cert_manager.create_certificate("renew.test")
        old_cert_id = old_cert["cert_id"]
        
        new_cert = cert_manager.renew_certificate(old_cert_id)
        
        assert new_cert["cert_id"] != old_cert_id
        assert new_cert["common_name"] == old_cert["common_name"]
        
        # Altes Zertifikat sollte widerrufen sein
        old_cert_updated = cert_manager.get_certificate(old_cert_id)
        assert old_cert_updated["status"] == CertificateStatus.REVOKED.value
    
    def test_renew_nonexistent_certificate(self, cert_manager):
        """Test: Nicht existierendes Zertifikat erneuern"""
        with pytest.raises(CertificateNotFoundError):
            cert_manager.renew_certificate("non-existent-id")


class TestCertificateDeletion:
    """Tests für Zertifikatslöschung"""
    
    def test_delete_certificate(self, cert_manager):
        """Test: Zertifikat löschen"""
        cert = cert_manager.create_certificate("delete.test")
        cert_id = cert["cert_id"]
        
        result = cert_manager.delete_certificate(cert_id)
        
        assert result is True
        assert cert_manager.get_certificate(cert_id) is None
    
    def test_delete_nonexistent_certificate(self, cert_manager):
        """Test: Nicht existierendes Zertifikat löschen"""
        with pytest.raises(CertificateNotFoundError):
            cert_manager.delete_certificate("non-existent-id")


class TestCertificateStatistics:
    """Tests für Statistiken"""
    
    def test_get_statistics_empty(self, cert_manager):
        """Test: Statistiken bei leerer Datenbank"""
        stats = cert_manager.get_statistics()
        
        assert stats["total_certificates"] == 0
        assert stats["valid_certificates"] == 0
        assert stats["mock_mode"] is True
    
    def test_get_statistics_with_certs(self, cert_manager):
        """Test: Statistiken mit Zertifikaten"""
        cert_manager.create_certificate("stat1.test")
        cert_manager.create_certificate("stat2.test")
        cert2 = cert_manager.create_certificate("stat3.test")
        cert_manager.revoke_certificate(cert2["cert_id"])
        
        stats = cert_manager.get_statistics()
        
        assert stats["total_certificates"] == 3
        assert stats["valid_certificates"] == 2
        assert stats["revoked_certificates"] == 1
    
    def test_get_statistics_by_type(self, cert_manager):
        """Test: Statistiken nach Typ"""
        cert_manager.create_certificate(
            "server.test",
            cert_type=CertificateType.SERVER
        )
        cert_manager.create_certificate(
            "client.test",
            cert_type=CertificateType.CLIENT
        )
        
        stats = cert_manager.get_statistics()
        
        assert stats["certificates_by_type"]["server"] == 1
        assert stats["certificates_by_type"]["client"] == 1
