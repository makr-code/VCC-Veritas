"""
Certificate Manager
Mock-Implementierung für Zertifikatsverwaltung

Verwaltet Zertifikate: Erstellung, Widerruf, Verifikation, Suche.
Mock-Implementierung für Entwicklung und Tests.
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from enum import Enum

from .exceptions import (
    CertificateNotFoundError,
    CertificateExpiredError,
    CertificateRevokedError,
    InvalidCertificateError
)
from .config import CERT_VALIDITY_DAYS, MOCK_MAX_CERTIFICATES
from .crypto_utils import (
    generate_key_pair,
    generate_csr,
    calculate_fingerprint
)


class CertificateStatus(str, Enum):
    """Zertifikatsstatus"""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class CertificateType(str, Enum):
    """Zertifikatstyp"""
    SERVER = "server"
    CLIENT = "client"
    CODE_SIGNING = "code_signing"
    EMAIL = "email"


class CertificateManager:
    """
    Certificate Manager (Mock-Implementierung)
    
    Verwaltet Zertifikate in-memory für Entwicklung und Tests.
    In Produktion würde hier eine Datenbank verwendet.
    """
    
    def __init__(self, mock_mode: bool = True):
        """
        Initialisiert den Certificate Manager.
        
        Args:
            mock_mode: True für Mock-Implementierung
        """
        self.mock_mode = mock_mode
        self._mock_certs: Dict[str, Dict[str, Any]] = {}
        self._revoked_certs: Dict[str, datetime] = {}
    
    def create_certificate(
        self,
        common_name: str,
        validity_days: int = CERT_VALIDITY_DAYS,
        key_size: int = 2048,
        cert_type: CertificateType = CertificateType.SERVER,
        country: Optional[str] = None,
        state: Optional[str] = None,
        locality: Optional[str] = None,
        organization: Optional[str] = None,
        organizational_unit: Optional[str] = None,
        email: Optional[str] = None,
        sans: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Erstellt ein neues Zertifikat (Mock).
        
        Args:
            common_name: Common Name (CN) für das Zertifikat
            validity_days: Gültigkeit in Tagen
            key_size: RSA-Schlüsselgröße (2048, 4096)
            cert_type: Zertifikatstyp (server, client, etc.)
            country: Ländercode (C)
            state: Bundesland/Staat (ST)
            locality: Stadt (L)
            organization: Organisation (O)
            organizational_unit: Organisationseinheit (OU)
            email: E-Mail-Adresse
            sans: Subject Alternative Names
        
        Returns:
            Dict mit Zertifikatsinformationen
        
        Raises:
            InvalidCertificateError: Bei ungültigen Parametern
        """
        # Validierung
        if not common_name:
            raise InvalidCertificateError("Common name is required")
        
        if len(self._mock_certs) >= MOCK_MAX_CERTIFICATES:
            raise InvalidCertificateError(
                f"Maximum certificates reached: {MOCK_MAX_CERTIFICATES}"
            )
        
        # Generiere Schlüsselpaar
        private_key_pem, public_key_pem = generate_key_pair(key_size)
        
        # Generiere CSR
        csr_pem = generate_csr(
            private_key_pem=private_key_pem,
            common_name=common_name,
            country=country,
            state=state,
            locality=locality,
            organization=organization,
            organizational_unit=organizational_unit,
            email=email
        )
        
        # Erstelle Mock-Zertifikat
        cert_id = str(uuid.uuid4())
        valid_from = datetime.now(timezone.utc)
        valid_until = valid_from + timedelta(days=validity_days)
        
        # Mock-PEM-Zertifikat
        cert_pem = f"""-----BEGIN CERTIFICATE-----
MOCK_CERTIFICATE_{cert_id}
Subject: CN={common_name}
Issuer: CN=VERITAS CA
Valid From: {valid_from.isoformat()}
Valid Until: {valid_until.isoformat()}
Type: {cert_type.value}
Serial Number: {uuid.uuid4().hex}
-----END CERTIFICATE-----"""
        
        # Berechne Fingerprint
        fingerprint = calculate_fingerprint(cert_pem)
        
        # Speichere Zertifikat
        certificate = {
            "cert_id": cert_id,
            "common_name": common_name,
            "cert_type": cert_type.value,
            "status": CertificateStatus.VALID.value,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "fingerprint": fingerprint,
            "serial_number": uuid.uuid4().hex,
            "key_size": key_size,
            "cert_pem": cert_pem,
            "private_key_pem": private_key_pem,
            "public_key_pem": public_key_pem,
            "csr_pem": csr_pem,
            "subject": {
                "common_name": common_name,
                "country": country,
                "state": state,
                "locality": locality,
                "organization": organization,
                "organizational_unit": organizational_unit,
                "email": email
            },
            "sans": sans or [],
            "created_at": datetime.now(timezone.utc),
            "revoked_at": None
        }
        
        self._mock_certs[cert_id] = certificate
        return certificate
    
    def get_certificate(self, cert_id: str) -> Optional[Dict[str, Any]]:
        """
        Ruft Zertifikat-Details ab.
        
        Args:
            cert_id: Zertifikats-ID
        
        Returns:
            Zertifikatsinformationen oder None
        """
        return self._mock_certs.get(cert_id)
    
    def get_certificate_by_fingerprint(
        self,
        fingerprint: str
    ) -> Optional[Dict[str, Any]]:
        """
        Ruft Zertifikat über Fingerprint ab.
        
        Args:
            fingerprint: Zertifikats-Fingerprint
        
        Returns:
            Zertifikatsinformationen oder None
        """
        for cert in self._mock_certs.values():
            if cert["fingerprint"] == fingerprint:
                return cert
        return None
    
    def list_certificates(
        self,
        status: Optional[CertificateStatus] = None,
        cert_type: Optional[CertificateType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Listet Zertifikate mit optionalen Filtern.
        
        Args:
            status: Filter nach Status (valid, expired, revoked)
            cert_type: Filter nach Typ (server, client, etc.)
            limit: Maximale Anzahl Ergebnisse
            offset: Offset für Pagination
        
        Returns:
            Liste von Zertifikaten
        """
        # Update Status (prüfe Ablaufdatum)
        self._update_certificate_status()
        
        # Filtere Zertifikate
        certs = list(self._mock_certs.values())
        
        if status:
            certs = [c for c in certs if c["status"] == status.value]
        
        if cert_type:
            certs = [c for c in certs if c["cert_type"] == cert_type.value]
        
        # Sortiere nach Created Date (neueste zuerst)
        certs.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Pagination
        return certs[offset:offset + limit]
    
    def revoke_certificate(
        self,
        cert_id: str,
        reason: str = "unspecified"
    ) -> bool:
        """
        Widerruft ein Zertifikat.
        
        Args:
            cert_id: Zertifikats-ID
            reason: Widerrufsgrund
        
        Returns:
            True wenn erfolgreich
        
        Raises:
            CertificateNotFoundError: Wenn Zertifikat nicht existiert
        """
        cert = self._mock_certs.get(cert_id)
        
        if not cert:
            raise CertificateNotFoundError(cert_id)
        
        # Setze Status auf revoked
        cert["status"] = CertificateStatus.REVOKED.value
        cert["revoked_at"] = datetime.now(timezone.utc)
        cert["revocation_reason"] = reason
        
        # Merke Widerruf
        self._revoked_certs[cert_id] = cert["revoked_at"]
        
        return True
    
    def verify_certificate(self, cert_pem: str) -> bool:
        """
        Verifiziert ein Zertifikat (Mock).
        
        Args:
            cert_pem: Zertifikat PEM-String
        
        Returns:
            True wenn Zertifikat valide
        """
        # Mock: Prüfe ob PEM-String valide aussieht
        if not cert_pem or "BEGIN CERTIFICATE" not in cert_pem:
            return False
        
        # Mock: Prüfe ob Zertifikat in unserer Liste ist
        fingerprint = calculate_fingerprint(cert_pem)
        cert = self.get_certificate_by_fingerprint(fingerprint)
        
        if not cert:
            return False
        
        # Prüfe Status
        if cert["status"] == CertificateStatus.REVOKED.value:
            return False
        
        # Prüfe Ablaufdatum
        if datetime.now(timezone.utc) > cert["valid_until"]:
            return False
        
        return True
    
    def renew_certificate(
        self,
        cert_id: str,
        validity_days: int = CERT_VALIDITY_DAYS
    ) -> Dict[str, Any]:
        """
        Erneuert ein bestehendes Zertifikat.
        
        Args:
            cert_id: ID des zu erneuernden Zertifikats
            validity_days: Neue Gültigkeit in Tagen
        
        Returns:
            Neues Zertifikat
        
        Raises:
            CertificateNotFoundError: Wenn Zertifikat nicht existiert
        """
        old_cert = self._mock_certs.get(cert_id)
        
        if not old_cert:
            raise CertificateNotFoundError(cert_id)
        
        # Erstelle neues Zertifikat mit gleichen Parametern
        new_cert = self.create_certificate(
            common_name=old_cert["common_name"],
            validity_days=validity_days,
            key_size=old_cert["key_size"],
            cert_type=CertificateType(old_cert["cert_type"]),
            country=old_cert["subject"]["country"],
            state=old_cert["subject"]["state"],
            locality=old_cert["subject"]["locality"],
            organization=old_cert["subject"]["organization"],
            organizational_unit=old_cert["subject"]["organizational_unit"],
            email=old_cert["subject"]["email"],
            sans=old_cert["sans"]
        )
        
        # Widerrufe altes Zertifikat
        self.revoke_certificate(cert_id, reason="superseded")
        
        return new_cert
    
    def delete_certificate(self, cert_id: str) -> bool:
        """
        Löscht ein Zertifikat permanent.
        
        Args:
            cert_id: Zertifikats-ID
        
        Returns:
            True wenn erfolgreich
        
        Raises:
            CertificateNotFoundError: Wenn Zertifikat nicht existiert
        """
        if cert_id not in self._mock_certs:
            raise CertificateNotFoundError(cert_id)
        
        del self._mock_certs[cert_id]
        
        if cert_id in self._revoked_certs:
            del self._revoked_certs[cert_id]
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über Zertifikate zurück.
        
        Returns:
            Dict mit Statistiken
        """
        self._update_certificate_status()
        
        total = len(self._mock_certs)
        valid = len([c for c in self._mock_certs.values() 
                     if c["status"] == CertificateStatus.VALID.value])
        expired = len([c for c in self._mock_certs.values() 
                       if c["status"] == CertificateStatus.EXPIRED.value])
        revoked = len([c for c in self._mock_certs.values() 
                       if c["status"] == CertificateStatus.REVOKED.value])
        
        # Zertifikate nach Typ
        by_type = {}
        for cert_type in CertificateType:
            count = len([c for c in self._mock_certs.values() 
                        if c["cert_type"] == cert_type.value])
            by_type[cert_type.value] = count
        
        return {
            "total_certificates": total,
            "valid_certificates": valid,
            "expired_certificates": expired,
            "revoked_certificates": revoked,
            "certificates_by_type": by_type,
            "mock_mode": self.mock_mode
        }
    
    def _update_certificate_status(self) -> None:
        """
        Aktualisiert den Status aller Zertifikate (prüft Ablaufdatum).
        """
        now = datetime.now(timezone.utc)
        
        for cert in self._mock_certs.values():
            # Überspringe bereits widerrufene Zertifikate
            if cert["status"] == CertificateStatus.REVOKED.value:
                continue
            
            # Prüfe Ablaufdatum
            if now > cert["valid_until"]:
                cert["status"] = CertificateStatus.EXPIRED.value
            elif now >= cert["valid_from"]:
                cert["status"] = CertificateStatus.VALID.value
            else:
                cert["status"] = CertificateStatus.PENDING.value
    
    def clear_all(self) -> int:
        """
        Löscht alle Zertifikate (nur für Tests!).
        
        Returns:
            Anzahl gelöschter Zertifikate
        """
        count = len(self._mock_certs)
        self._mock_certs.clear()
        self._revoked_certs.clear()
        return count
