"""
Certificate Authority Service
Mock-Implementierung für CA-Operationen

Bietet CA-Funktionen: CSR-Signierung, CRL-Verwaltung, Chain-Verifikation.
Mock-Implementierung für Entwicklung und Tests.
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone

from .exceptions import (
    CANotInitializedError,
    InvalidCSRError,
    CertificateRevokedError
)
from .config import (
    CA_NAME,
    CA_COUNTRY,
    CA_STATE,
    CA_LOCALITY,
    CA_ORGANIZATION,
    CA_ORGANIZATIONAL_UNIT,
    CA_EMAIL,
    CA_VALIDITY_YEARS,
    CERT_VALIDITY_DAYS,
    CRL_UPDATE_INTERVAL_HOURS,
    get_ca_distinguished_name
)
from .crypto_utils import (
    generate_key_pair,
    calculate_fingerprint
)


class CAService:
    """
    Certificate Authority Service (Mock-Implementierung)
    
    Bietet CA-Funktionalität für Zertifikatsverwaltung.
    Mock-Implementierung für Entwicklung und Tests.
    """
    
    def __init__(
        self,
        ca_name: str = CA_NAME,
        auto_initialize: bool = False
    ):
        """
        Initialisiert den CA Service.
        
        Args:
            ca_name: Name der Certificate Authority
            auto_initialize: Automatische CA-Initialisierung
        """
        self.ca_name = ca_name
        self.ca_initialized = False
        self._ca_certificate: Optional[Dict[str, Any]] = None
        self._ca_private_key: Optional[str] = None
        self._ca_public_key: Optional[str] = None
        self._signed_certificates: Dict[str, Dict[str, Any]] = {}
        self._revoked_serials: List[Dict[str, Any]] = []
        self._crl_last_update: Optional[datetime] = None
        
        if auto_initialize:
            self.initialize_ca()
    
    def initialize_ca(
        self,
        validity_years: int = CA_VALIDITY_YEARS
    ) -> bool:
        """
        Initialisiert die Certificate Authority (Mock).
        
        Erstellt CA-Zertifikat und Schlüsselpaar.
        
        Args:
            validity_years: Gültigkeit des CA-Zertifikats in Jahren
        
        Returns:
            True wenn erfolgreich initialisiert
        """
        if self.ca_initialized:
            return True
        
        # Generiere CA-Schlüsselpaar
        private_key_pem, public_key_pem = generate_key_pair(key_size=4096)
        
        self._ca_private_key = private_key_pem
        self._ca_public_key = public_key_pem
        
        # Erstelle CA-Zertifikat
        ca_dn = get_ca_distinguished_name()
        valid_from = datetime.now(timezone.utc)
        valid_until = valid_from + timedelta(days=validity_years * 365)
        
        ca_cert_pem = f"""-----BEGIN CERTIFICATE-----
MOCK_CA_CERTIFICATE
Subject: CN={ca_dn['common_name']}, C={ca_dn['country']}, ST={ca_dn['state']}, L={ca_dn['locality']}, O={ca_dn['organization']}, OU={ca_dn['organizational_unit']}
Issuer: CN={ca_dn['common_name']} (Self-Signed)
Valid From: {valid_from.isoformat()}
Valid Until: {valid_until.isoformat()}
Serial Number: {uuid.uuid4().hex}
Key Usage: Certificate Sign, CRL Sign
Basic Constraints: CA:TRUE
-----END CERTIFICATE-----"""
        
        fingerprint = calculate_fingerprint(ca_cert_pem)
        
        self._ca_certificate = {
            "cert_id": "ca_root",
            "common_name": ca_dn["common_name"],
            "serial_number": uuid.uuid4().hex,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "fingerprint": fingerprint,
            "cert_pem": ca_cert_pem,
            "subject": ca_dn,
            "issuer": ca_dn,  # Self-signed
            "is_ca": True,
            "created_at": datetime.now(timezone.utc)
        }
        
        self.ca_initialized = True
        return True
    
    def sign_csr(
        self,
        csr_pem: str,
        validity_days: int = CERT_VALIDITY_DAYS,
        cert_type: str = "server"
    ) -> Dict[str, Any]:
        """
        Signiert einen Certificate Signing Request (Mock).
        
        Args:
            csr_pem: CSR PEM-String
            validity_days: Gültigkeit in Tagen
            cert_type: Zertifikatstyp (server, client, etc.)
        
        Returns:
            Signiertes Zertifikat
        
        Raises:
            CANotInitializedError: Wenn CA nicht initialisiert
            InvalidCSRError: Wenn CSR ungültig
        """
        if not self.ca_initialized:
            raise CANotInitializedError()
        
        if not csr_pem or "CERTIFICATE REQUEST" not in csr_pem:
            raise InvalidCSRError("Invalid CSR format")
        
        # Mock: Extrahiere Subject aus CSR
        # In Produktion würde hier cryptography verwendet
        try:
            subject_line = [
                line for line in csr_pem.split("\n") 
                if line.startswith("Subject:")
            ][0]
            subject = subject_line.replace("Subject:", "").strip()
        except:
            raise InvalidCSRError("Cannot extract subject from CSR")
        
        # Erstelle signiertes Zertifikat
        serial_number = uuid.uuid4().hex
        valid_from = datetime.now(timezone.utc)
        valid_until = valid_from + timedelta(days=validity_days)
        
        cert_pem = f"""-----BEGIN CERTIFICATE-----
MOCK_SIGNED_CERTIFICATE
Subject: {subject}
Issuer: CN={self.ca_name}
Valid From: {valid_from.isoformat()}
Valid Until: {valid_until.isoformat()}
Serial Number: {serial_number}
Type: {cert_type}
Signed By: {self.ca_name}
-----END CERTIFICATE-----"""
        
        fingerprint = calculate_fingerprint(cert_pem)
        
        signed_cert = {
            "cert_id": str(uuid.uuid4()),
            "serial_number": serial_number,
            "subject": subject,
            "issuer": self.ca_name,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "fingerprint": fingerprint,
            "cert_type": cert_type,
            "cert_pem": cert_pem,
            "csr_pem": csr_pem,
            "signed_at": datetime.now(timezone.utc),
            "revoked": False
        }
        
        # Speichere signiertes Zertifikat
        self._signed_certificates[serial_number] = signed_cert
        
        return signed_cert
    
    def get_ca_certificate(self) -> str:
        """
        Ruft das CA-Zertifikat ab.
        
        Returns:
            CA-Zertifikat PEM-String
        
        Raises:
            CANotInitializedError: Wenn CA nicht initialisiert
        """
        if not self.ca_initialized or not self._ca_certificate:
            raise CANotInitializedError()
        
        return self._ca_certificate["cert_pem"]
    
    def get_ca_info(self) -> Dict[str, Any]:
        """
        Ruft CA-Informationen ab.
        
        Returns:
            Dict mit CA-Informationen
        
        Raises:
            CANotInitializedError: Wenn CA nicht initialisiert
        """
        if not self.ca_initialized or not self._ca_certificate:
            raise CANotInitializedError()
        
        return {
            "ca_name": self.ca_name,
            "initialized": self.ca_initialized,
            "certificate": {
                "common_name": self._ca_certificate["common_name"],
                "serial_number": self._ca_certificate["serial_number"],
                "valid_from": self._ca_certificate["valid_from"].isoformat(),
                "valid_until": self._ca_certificate["valid_until"].isoformat(),
                "fingerprint": self._ca_certificate["fingerprint"]
            },
            "statistics": {
                "signed_certificates": len(self._signed_certificates),
                "revoked_certificates": len(self._revoked_serials)
            }
        }
    
    def get_crl(self) -> str:
        """
        Ruft die Certificate Revocation List (CRL) ab (Mock).
        
        Returns:
            CRL PEM-String
        
        Raises:
            CANotInitializedError: Wenn CA nicht initialisiert
        """
        if not self.ca_initialized:
            raise CANotInitializedError()
        
        # Aktualisiere CRL-Timestamp
        now = datetime.now(timezone.utc)
        self._crl_last_update = now
        next_update = now + timedelta(hours=CRL_UPDATE_INTERVAL_HOURS)
        
        # Erstelle CRL
        revoked_entries = "\n".join([
            f"Serial Number: {entry['serial_number']}, "
            f"Revocation Date: {entry['revocation_date'].isoformat()}, "
            f"Reason: {entry['reason']}"
            for entry in self._revoked_serials
        ])
        
        crl_pem = f"""-----BEGIN X509 CRL-----
MOCK_CRL
Issuer: CN={self.ca_name}
Last Update: {now.isoformat()}
Next Update: {next_update.isoformat()}
Revoked Certificates: {len(self._revoked_serials)}

{revoked_entries if revoked_entries else "No revoked certificates"}
-----END X509 CRL-----"""
        
        return crl_pem
    
    def revoke_certificate(
        self,
        serial_number: str,
        reason: str = "unspecified"
    ) -> bool:
        """
        Widerruft ein von der CA signiertes Zertifikat.
        
        Args:
            serial_number: Seriennummer des Zertifikats
            reason: Widerrufsgrund
        
        Returns:
            True wenn erfolgreich
        
        Raises:
            CANotInitializedError: Wenn CA nicht initialisiert
        """
        if not self.ca_initialized:
            raise CANotInitializedError()
        
        # Prüfe ob Zertifikat existiert
        if serial_number not in self._signed_certificates:
            return False
        
        # Markiere als widerrufen
        cert = self._signed_certificates[serial_number]
        cert["revoked"] = True
        
        # Füge zur CRL hinzu
        revocation_entry = {
            "serial_number": serial_number,
            "revocation_date": datetime.now(timezone.utc),
            "reason": reason
        }
        self._revoked_serials.append(revocation_entry)
        
        return True
    
    def verify_chain(
        self,
        cert_pem: str,
        include_crl_check: bool = True
    ) -> bool:
        """
        Verifiziert eine Zertifikatskette (Mock).
        
        Args:
            cert_pem: Zertifikat PEM-String
            include_crl_check: CRL-Prüfung durchführen
        
        Returns:
            True wenn Zertifikatskette valide
        
        Raises:
            CANotInitializedError: Wenn CA nicht initialisiert
        """
        if not self.ca_initialized:
            raise CANotInitializedError()
        
        if not cert_pem or "BEGIN CERTIFICATE" not in cert_pem:
            return False
        
        # Mock: Prüfe ob Zertifikat von unserer CA signiert wurde
        # In Produktion würde hier die Signatur verifiziert
        if f"Issuer: CN={self.ca_name}" not in cert_pem:
            return False
        
        # Extrahiere Serial Number
        try:
            serial_line = [
                line for line in cert_pem.split("\n") 
                if "Serial Number:" in line
            ][0]
            serial_number = serial_line.split("Serial Number:")[1].strip()
        except:
            return False
        
        # Prüfe ob Zertifikat existiert
        if serial_number not in self._signed_certificates:
            return False
        
        cert = self._signed_certificates[serial_number]
        
        # CRL-Check
        if include_crl_check and cert.get("revoked", False):
            return False
        
        # Prüfe Gültigkeit
        now = datetime.now(timezone.utc)
        if now < cert["valid_from"] or now > cert["valid_until"]:
            return False
        
        return True
    
    def get_signed_certificates(
        self,
        include_revoked: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Ruft alle von der CA signierten Zertifikate ab.
        
        Args:
            include_revoked: Auch widerrufene Zertifikate einbeziehen
        
        Returns:
            Liste von Zertifikaten
        
        Raises:
            CANotInitializedError: Wenn CA nicht initialisiert
        """
        if not self.ca_initialized:
            raise CANotInitializedError()
        
        certs = list(self._signed_certificates.values())
        
        if not include_revoked:
            certs = [c for c in certs if not c.get("revoked", False)]
        
        # Sortiere nach Signatur-Datum (neueste zuerst)
        certs.sort(key=lambda x: x["signed_at"], reverse=True)
        
        return certs
    
    def export_ca_bundle(self) -> str:
        """
        Exportiert CA-Bundle (CA-Cert + Chain).
        
        Returns:
            CA-Bundle PEM-String
        
        Raises:
            CANotInitializedError: Wenn CA nicht initialisiert
        """
        if not self.ca_initialized or not self._ca_certificate:
            raise CANotInitializedError()
        
        # Mock: Nur CA-Zertifikat (keine Chain in Mock)
        return self._ca_certificate["cert_pem"]
    
    def reset(self) -> None:
        """
        Setzt die CA zurück (nur für Tests!).
        """
        self.ca_initialized = False
        self._ca_certificate = None
        self._ca_private_key = None
        self._ca_public_key = None
        self._signed_certificates.clear()
        self._revoked_serials.clear()
        self._crl_last_update = None
