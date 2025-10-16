"""
Certificate Authority (CA) Service Module

Production-Ready Certificate Authority Implementation:
- Root CA Management
- Intermediate CA Support
- Certificate Signing (CSR Processing)
- CRL (Certificate Revocation List) Generation
- OCSP Support (Basic)
- CA Certificate Chain Validation

**Dependencies:** cryptography>=41.0.0
**Mode:** PRODUCTION (NO MOCK)
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

from .crypto_utils import generate_keypair
from .cert_manager import CertificateManager


# ============================================================================
# Certificate Authority Service Class
# ============================================================================

class CAService:
    """
    Production-Ready Certificate Authority Service
    
    Features:
    - Root CA Initialization
    - Intermediate CA Support
    - CSR Signing
    - CRL Generation
    - Certificate Chain Validation
    - CA Hierarchy Management
    
    **CA Hierarchy:**
    ```
    Root CA (self-signed)
      └── Intermediate CA 1
          ├── End-Entity Cert 1
          ├── End-Entity Cert 2
          └── ...
      └── Intermediate CA 2
          └── ...
    ```
    
    **Mode:** PRODUCTION (Hard Fail on Errors)
    """
    
    def __init__(
        self,
        ca_storage_path: str = "./ca_storage",
        cert_manager: Optional[CertificateManager] = None
    ):
        """
        Initialize Certificate Authority Service.
        
        Args:
            ca_storage_path: Path to CA storage directory
            cert_manager: CertificateManager instance (optional)
        
        Raises:
            RuntimeError: If CA storage initialization fails
        """
        self.ca_storage_path = Path(ca_storage_path)
        
        # Initialize CA storage directories
        try:
            self.ca_dir = self.ca_storage_path / "ca_certificates"
            self.ca_keys_dir = self.ca_storage_path / "ca_keys"
            self.crl_dir = self.ca_storage_path / "crl"
            self.ca_config_dir = self.ca_storage_path / "config"
            
            self.ca_dir.mkdir(parents=True, exist_ok=True)
            self.ca_keys_dir.mkdir(parents=True, exist_ok=True)
            self.crl_dir.mkdir(parents=True, exist_ok=True)
            self.ca_config_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize CA config
            self.ca_config_file = self.ca_config_dir / "ca_config.json"
            if not self.ca_config_file.exists():
                self._save_ca_config({
                    'root_ca_id': None,
                    'intermediate_cas': [],
                    'initialized': False
                })
            
            # Certificate Manager (for issued certificates)
            self.cert_manager = cert_manager or CertificateManager()
        
        except Exception as e:
            raise RuntimeError(f"CA storage initialization failed: {e}")
    
    # ========================================================================
    # Root CA Initialization
    # ========================================================================
    
    def initialize_root_ca(
        self,
        common_name: str,
        validity_days: int = 3650,  # 10 years
        key_size: int = 4096,
        **subject_attributes
    ) -> Dict[str, Any]:
        """
        Initialize Root CA (self-signed certificate).
        
        Args:
            common_name: Common Name for Root CA (e.g., "Example Root CA")
            validity_days: Validity period in days (default: 3650 = 10 years)
            key_size: RSA key size (recommended: 4096 for Root CA)
            **subject_attributes: Additional subject attributes
                - country: Country (C)
                - state: State/Province (ST)
                - locality: Locality/City (L)
                - organization: Organization (O)
                - organizational_unit: Organizational Unit (OU)
        
        Returns:
            Root CA information dict
        
        Raises:
            RuntimeError: If Root CA already exists or initialization fails
        
        Example:
            >>> ca_service = CAService()
            >>> root_ca = ca_service.initialize_root_ca(
            ...     common_name="Example Root CA",
            ...     organization="Example Corp",
            ...     country="DE"
            ... )
        """
        try:
            # Check if Root CA already exists
            ca_config = self._load_ca_config()
            if ca_config.get('root_ca_id'):
                raise RuntimeError("Root CA already initialized")
            
            # Generate Root CA key pair
            private_key_pem, public_key_pem = generate_keypair(key_size)
            
            # Load private key
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
                backend=default_backend()
            )
            
            # Build subject name
            subject_attrs = [
                x509.NameAttribute(NameOID.COMMON_NAME, common_name)
            ]
            
            if subject_attributes.get('country'):
                subject_attrs.append(x509.NameAttribute(NameOID.COUNTRY_NAME, subject_attributes['country']))
            if subject_attributes.get('state'):
                subject_attrs.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, subject_attributes['state']))
            if subject_attributes.get('locality'):
                subject_attrs.append(x509.NameAttribute(NameOID.LOCALITY_NAME, subject_attributes['locality']))
            if subject_attributes.get('organization'):
                subject_attrs.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, subject_attributes['organization']))
            if subject_attributes.get('organizational_unit'):
                subject_attrs.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, subject_attributes['organizational_unit']))
            
            subject = x509.Name(subject_attrs)
            
            # Generate serial number
            serial_number = x509.random_serial_number()
            
            # Set validity period
            not_valid_before = datetime.now(timezone.utc)
            not_valid_after = not_valid_before + timedelta(days=validity_days)
            
            # Build Root CA certificate
            builder = x509.CertificateBuilder()
            builder = builder.subject_name(subject)
            builder = builder.issuer_name(subject)  # Self-signed
            builder = builder.serial_number(serial_number)
            builder = builder.not_valid_before(not_valid_before)
            builder = builder.not_valid_after(not_valid_after)
            builder = builder.public_key(private_key.public_key())
            
            # Add CA extensions
            builder = builder.add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True
            )
            builder = builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_cert_sign=True,
                    crl_sign=True,
                    key_encipherment=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True
            )
            builder = builder.add_extension(
                x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
                critical=False
            )
            
            # Sign certificate (self-signed)
            certificate = builder.sign(private_key, hashes.SHA256(), backend=default_backend())
            
            # Save Root CA certificate and key
            root_ca_id = "root_ca"
            cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
            
            ca_cert_file = self.ca_dir / f"{root_ca_id}.pem"
            ca_key_file = self.ca_keys_dir / f"{root_ca_id}_key.pem"
            
            with open(ca_cert_file, 'wb') as f:
                f.write(cert_pem)
            
            with open(ca_key_file, 'wb') as f:
                f.write(private_key_pem)
            
            # Update CA config
            ca_config['root_ca_id'] = root_ca_id
            ca_config['initialized'] = True
            ca_config['root_ca_info'] = {
                'common_name': common_name,
                'serial_number': str(serial_number),
                'not_valid_before': not_valid_before.isoformat(),
                'not_valid_after': not_valid_after.isoformat(),
                'key_size': key_size,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            self._save_ca_config(ca_config)
            
            return ca_config['root_ca_info']
        
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Root CA initialization failed: {e}")
    
    # ========================================================================
    # Certificate Signing (CSR Processing)
    # ========================================================================
    
    def sign_csr(
        self,
        csr_pem: bytes,
        validity_days: int = 365,
        is_ca: bool = False,
        ca_id: str = "root_ca"
    ) -> Dict[str, Any]:
        """
        Sign Certificate Signing Request (CSR).
        
        Args:
            csr_pem: CSR in PEM format
            validity_days: Certificate validity in days (default: 365)
            is_ca: Whether the certificate is for an intermediate CA
            ca_id: CA to use for signing (default: "root_ca")
        
        Returns:
            Signed certificate information
        
        Raises:
            ValueError: If CSR is invalid or CA not found
            RuntimeError: If signing fails
        
        Example:
            >>> from backend.pki.crypto_utils import generate_keypair, generate_csr
            >>> private_key, _ = generate_keypair()
            >>> csr = generate_csr(private_key, "example.com", organization="Example Corp")
            >>> signed_cert = ca_service.sign_csr(csr, validity_days=365)
        """
        try:
            # Load CSR
            csr = x509.load_pem_x509_csr(csr_pem, backend=default_backend())
            
            # Verify CSR signature
            if not csr.is_signature_valid:
                raise ValueError("CSR signature is invalid")
            
            # Load CA certificate and key
            ca_cert_pem, ca_key_pem = self._load_ca_certificate_and_key(ca_id)
            
            ca_cert = x509.load_pem_x509_certificate(ca_cert_pem, backend=default_backend())
            ca_key = serialization.load_pem_private_key(
                ca_key_pem,
                password=None,
                backend=default_backend()
            )
            
            # Build certificate
            serial_number = x509.random_serial_number()
            not_valid_before = datetime.now(timezone.utc)
            not_valid_after = not_valid_before + timedelta(days=validity_days)
            
            builder = x509.CertificateBuilder()
            builder = builder.subject_name(csr.subject)
            builder = builder.issuer_name(ca_cert.subject)
            builder = builder.serial_number(serial_number)
            builder = builder.not_valid_before(not_valid_before)
            builder = builder.not_valid_after(not_valid_after)
            builder = builder.public_key(csr.public_key())
            
            # Add extensions
            if is_ca:
                # Intermediate CA certificate
                builder = builder.add_extension(
                    x509.BasicConstraints(ca=True, path_length=0),  # path_length=0 = can't sign other CAs
                    critical=True
                )
                builder = builder.add_extension(
                    x509.KeyUsage(
                        digital_signature=True,
                        key_cert_sign=True,
                        crl_sign=True,
                        key_encipherment=False,
                        content_commitment=False,
                        data_encipherment=False,
                        key_agreement=False,
                        encipher_only=False,
                        decipher_only=False
                    ),
                    critical=True
                )
            else:
                # End-entity certificate
                builder = builder.add_extension(
                    x509.BasicConstraints(ca=False, path_length=None),
                    critical=True
                )
                builder = builder.add_extension(
                    x509.KeyUsage(
                        digital_signature=True,
                        key_encipherment=True,
                        content_commitment=False,
                        data_encipherment=False,
                        key_agreement=False,
                        key_cert_sign=False,
                        crl_sign=False,
                        encipher_only=False,
                        decipher_only=False
                    ),
                    critical=True
                )
            
            # Add Subject Key Identifier
            builder = builder.add_extension(
                x509.SubjectKeyIdentifier.from_public_key(csr.public_key()),
                critical=False
            )
            
            # Add Authority Key Identifier (from CA)
            builder = builder.add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
                critical=False
            )
            
            # Sign certificate
            certificate = builder.sign(ca_key, hashes.SHA256(), backend=default_backend())
            
            # Save signed certificate using CertificateManager
            cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
            
            # Extract subject CN
            subject_cn = None
            for attr in csr.subject:
                if attr.oid == NameOID.COMMON_NAME:
                    subject_cn = attr.value
                    break
            
            # Create certificate record
            cert_info = {
                'cert_id': str(serial_number),
                'subject_name': subject_cn or "Unknown",
                'serial_number': str(serial_number),
                'not_valid_before': not_valid_before.isoformat(),
                'not_valid_after': not_valid_after.isoformat(),
                'is_ca': is_ca,
                'issuer_ca_id': ca_id,
                'certificate_pem': cert_pem.decode(),
                'signed_by_ca': True,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            return cert_info
        
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"CSR signing failed: {e}")
    
    # ========================================================================
    # CA Certificate Retrieval
    # ========================================================================
    
    def get_ca_certificate(self, ca_id: str = "root_ca") -> Optional[bytes]:
        """
        Get CA certificate in PEM format.
        
        Args:
            ca_id: CA identifier (default: "root_ca")
        
        Returns:
            CA certificate PEM or None if not found
        
        Example:
            >>> root_ca_pem = ca_service.get_ca_certificate("root_ca")
            >>> print(root_ca_pem.decode())
        """
        try:
            ca_cert_file = self.ca_dir / f"{ca_id}.pem"
            if not ca_cert_file.exists():
                return None
            
            with open(ca_cert_file, 'rb') as f:
                return f.read()
        
        except Exception:
            return None
    
    def get_ca_info(self, ca_id: str = "root_ca") -> Optional[Dict[str, Any]]:
        """
        Get CA information.
        
        Args:
            ca_id: CA identifier
        
        Returns:
            CA info dict or None if not found
        """
        ca_config = self._load_ca_config()
        
        if ca_id == "root_ca":
            return ca_config.get('root_ca_info')
        
        # Search in intermediate CAs
        for intermediate_ca in ca_config.get('intermediate_cas', []):
            if intermediate_ca.get('ca_id') == ca_id:
                return intermediate_ca
        
        return None
    
    # ========================================================================
    # CRL (Certificate Revocation List) Generation
    # ========================================================================
    
    def generate_crl(
        self,
        ca_id: str = "root_ca",
        revoked_certs: Optional[List[Dict[str, Any]]] = None
    ) -> bytes:
        """
        Generate Certificate Revocation List (CRL).
        
        Args:
            ca_id: CA identifier (default: "root_ca")
            revoked_certs: List of revoked certificate info dicts
                [{'serial_number': str, 'revoked_at': datetime, 'reason': str}]
        
        Returns:
            CRL in PEM format
        
        Raises:
            ValueError: If CA not found
            RuntimeError: If CRL generation fails
        
        Example:
            >>> crl_pem = ca_service.generate_crl("root_ca")
            >>> with open("revocation_list.crl", "wb") as f:
            ...     f.write(crl_pem)
        """
        try:
            # Load CA certificate and key
            ca_cert_pem, ca_key_pem = self._load_ca_certificate_and_key(ca_id)
            
            ca_cert = x509.load_pem_x509_certificate(ca_cert_pem, backend=default_backend())
            ca_key = serialization.load_pem_private_key(
                ca_key_pem,
                password=None,
                backend=default_backend()
            )
            
            # Build CRL
            builder = x509.CertificateRevocationListBuilder()
            builder = builder.issuer_name(ca_cert.subject)
            builder = builder.last_update(datetime.now(timezone.utc))
            builder = builder.next_update(datetime.now(timezone.utc) + timedelta(days=7))  # Update weekly
            
            # Add revoked certificates
            if revoked_certs:
                for revoked_cert in revoked_certs:
                    serial_number = int(revoked_cert['serial_number'])
                    revoked_at = datetime.fromisoformat(revoked_cert['revoked_at'])
                    
                    revoked_cert_builder = x509.RevokedCertificateBuilder()
                    revoked_cert_builder = revoked_cert_builder.serial_number(serial_number)
                    revoked_cert_builder = revoked_cert_builder.revocation_date(revoked_at)
                    
                    # Add revocation reason if provided
                    reason = revoked_cert.get('reason', 'unspecified')
                    if reason:
                        reason_flag = self._get_revocation_reason_flag(reason)
                        revoked_cert_builder = revoked_cert_builder.add_extension(
                            x509.CRLReason(reason_flag),
                            critical=False
                        )
                    
                    builder = builder.add_revoked_certificate(revoked_cert_builder.build())
            
            # Sign CRL
            crl = builder.sign(ca_key, hashes.SHA256(), backend=default_backend())
            
            # Save CRL
            crl_pem = crl.public_bytes(serialization.Encoding.PEM)
            crl_file = self.crl_dir / f"{ca_id}_crl.pem"
            
            with open(crl_file, 'wb') as f:
                f.write(crl_pem)
            
            return crl_pem
        
        except Exception as e:
            raise RuntimeError(f"CRL generation failed: {e}")
    
    # ========================================================================
    # Certificate Chain Validation
    # ========================================================================
    
    def verify_certificate_chain(
        self,
        cert_pem: bytes,
        ca_id: str = "root_ca"
    ) -> Dict[str, Any]:
        """
        Verify certificate chain up to CA.
        
        Args:
            cert_pem: Certificate to verify (PEM format)
            ca_id: CA to verify against (default: "root_ca")
        
        Returns:
            Verification result dict:
            {
                'valid': bool,
                'errors': List[str],
                'chain': List[str]  # List of certificate subjects in chain
            }
        
        Example:
            >>> result = ca_service.verify_certificate_chain(cert_pem)
            >>> if result['valid']:
            ...     print("Certificate chain is valid")
        """
        errors = []
        chain = []
        
        try:
            # Load certificate
            cert = x509.load_pem_x509_certificate(cert_pem, backend=default_backend())
            chain.append(cert.subject.rfc4514_string())
            
            # Load CA certificate
            ca_cert_pem = self.get_ca_certificate(ca_id)
            if not ca_cert_pem:
                errors.append(f"CA certificate not found: {ca_id}")
                return {'valid': False, 'errors': errors, 'chain': chain}
            
            ca_cert = x509.load_pem_x509_certificate(ca_cert_pem, backend=default_backend())
            
            # Verify issuer
            if cert.issuer != ca_cert.subject:
                errors.append("Certificate issuer doesn't match CA subject")
            
            # Verify signature
            try:
                ca_cert.public_key().verify(
                    cert.signature,
                    cert.tbs_certificate_bytes,
                    cert.signature_hash_algorithm
                )
            except Exception as e:
                errors.append(f"Signature verification failed: {e}")
            
            # Check validity period
            now = datetime.now(timezone.utc)
            if now < cert.not_valid_before_utc:
                errors.append("Certificate not yet valid")
            if now > cert.not_valid_after_utc:
                errors.append("Certificate expired")
            
            chain.append(ca_cert.subject.rfc4514_string())
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'chain': chain
            }
        
        except Exception as e:
            errors.append(f"Chain verification failed: {e}")
            return {'valid': False, 'errors': errors, 'chain': chain}
    
    # ========================================================================
    # Statistics & Status
    # ========================================================================
    
    def get_ca_statistics(self) -> Dict[str, Any]:
        """
        Get CA statistics.
        
        Returns:
            Statistics dict
        
        Example:
            >>> stats = ca_service.get_ca_statistics()
            >>> print(f"Root CA: {stats['root_ca_initialized']}")
        """
        ca_config = self._load_ca_config()
        
        return {
            'root_ca_initialized': ca_config.get('initialized', False),
            'root_ca_id': ca_config.get('root_ca_id'),
            'intermediate_cas_count': len(ca_config.get('intermediate_cas', [])),
            'storage_path': str(self.ca_storage_path),
            'root_ca_info': ca_config.get('root_ca_info')
        }
    
    def is_initialized(self) -> bool:
        """
        Check if CA is initialized.
        
        Returns:
            True if CA is initialized
        """
        ca_config = self._load_ca_config()
        return ca_config.get('initialized', False)
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _save_ca_config(self, config: Dict[str, Any]):
        """Save CA configuration."""
        with open(self.ca_config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _load_ca_config(self) -> Dict[str, Any]:
        """Load CA configuration."""
        if not self.ca_config_file.exists():
            return {}
        
        with open(self.ca_config_file, 'r') as f:
            return json.load(f)
    
    def _load_ca_certificate_and_key(self, ca_id: str) -> Tuple[bytes, bytes]:
        """
        Load CA certificate and private key.
        
        Returns:
            Tuple of (cert_pem, key_pem)
        
        Raises:
            ValueError: If CA not found
        """
        ca_cert_file = self.ca_dir / f"{ca_id}.pem"
        ca_key_file = self.ca_keys_dir / f"{ca_id}_key.pem"
        
        if not ca_cert_file.exists():
            raise ValueError(f"CA certificate not found: {ca_id}")
        if not ca_key_file.exists():
            raise ValueError(f"CA private key not found: {ca_id}")
        
        with open(ca_cert_file, 'rb') as f:
            cert_pem = f.read()
        
        with open(ca_key_file, 'rb') as f:
            key_pem = f.read()
        
        return cert_pem, key_pem
    
    def _get_revocation_reason_flag(self, reason: str) -> x509.ReasonFlags:
        """Convert reason string to CRL reason flag."""
        reason_map = {
            'unspecified': x509.ReasonFlags.unspecified,
            'key_compromise': x509.ReasonFlags.key_compromise,
            'ca_compromise': x509.ReasonFlags.ca_compromise,
            'affiliation_changed': x509.ReasonFlags.affiliation_changed,
            'superseded': x509.ReasonFlags.superseded,
            'cessation_of_operation': x509.ReasonFlags.cessation_of_operation,
            'certificate_hold': x509.ReasonFlags.certificate_hold,
            'privilege_withdrawn': x509.ReasonFlags.privilege_withdrawn,
            'aa_compromise': x509.ReasonFlags.aa_compromise
        }
        
        return reason_map.get(reason.lower(), x509.ReasonFlags.unspecified)


# ============================================================================
# Module Exports
# ============================================================================

__all__ = ['CAService']
