"""
VERITAS PKI/CA Integration
Public Key Infrastructure für Zertifikatsverwaltung

Dieses Package bietet Mock-Implementierungen für PKI-Funktionalität
während der Entwicklung. Die echte PKI liegt in C:\VCC\PKI.

Verwendung:
    from pki import CertificateManager, CAService
    
    # Certificate Manager
    cert_manager = CertificateManager(mock_mode=True)
    cert = cert_manager.create_certificate("test.veritas.local")
    
    # CA Service
    ca = CAService(auto_initialize=True)
    signed_cert = ca.sign_csr(csr_pem)
"""

from .cert_manager import CertificateManager, CertificateStatus, CertificateType
from .ca_service import CAService
from .crypto_utils import (
    generate_key_pair,
    generate_csr,
    calculate_fingerprint,
    encrypt_data,
    decrypt_data,
    sign_data,
    verify_signature,
    generate_random_bytes,
    generate_random_hex,
    hash_data
)
from .exceptions import (
    PKIException,
    CertificateNotFoundError,
    CertificateExpiredError,
    CertificateRevokedError,
    InvalidCSRError,
    CANotInitializedError,
    SignatureVerificationError,
    InvalidCertificateError,
    KeyGenerationError,
    EncryptionError,
    DecryptionError
)
from .config import (
    PKI_BASE_PATH,
    PKI_MOCK_MODE,
    PKI_ENABLED,
    CERT_VALIDITY_DAYS,
    CERT_KEY_SIZE,
    CERT_HASH_ALGORITHM,
    CA_NAME,
    get_pki_config,
    validate_config,
    is_mock_mode,
    get_ca_distinguished_name
)

__version__ = "0.1.0"
__author__ = "VERITAS Team"

__all__ = [
    # Classes
    "CertificateManager",
    "CertificateStatus",
    "CertificateType",
    "CAService",
    
    # Crypto Functions
    "generate_key_pair",
    "generate_csr",
    "calculate_fingerprint",
    "encrypt_data",
    "decrypt_data",
    "sign_data",
    "verify_signature",
    "generate_random_bytes",
    "generate_random_hex",
    "hash_data",
    
    # Exceptions
    "PKIException",
    "CertificateNotFoundError",
    "CertificateExpiredError",
    "CertificateRevokedError",
    "InvalidCSRError",
    "CANotInitializedError",
    "SignatureVerificationError",
    "InvalidCertificateError",
    "KeyGenerationError",
    "EncryptionError",
    "DecryptionError",
    
    # Config
    "PKI_BASE_PATH",
    "PKI_MOCK_MODE",
    "PKI_ENABLED",
    "CERT_VALIDITY_DAYS",
    "CERT_KEY_SIZE",
    "CERT_HASH_ALGORITHM",
    "CA_NAME",
    "get_pki_config",
    "validate_config",
    "is_mock_mode",
    "get_ca_distinguished_name"
]
