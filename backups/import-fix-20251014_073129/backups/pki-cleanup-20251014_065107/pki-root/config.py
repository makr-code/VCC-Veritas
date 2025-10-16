"""
PKI Configuration
Konfiguration für PKI/CA Integration

Zentrale Konfiguration für PKI-Operationen.
Unterstützt Mock-Mode für Entwicklung und echte PKI für Produktion.
"""

import os
from pathlib import Path
from typing import Dict, Any


# ============================================================================
# PKI Base Configuration
# ============================================================================

# PKI Base Path (eine Ebene über VERITAS: C:\VCC\PKI)
PKI_BASE_PATH = Path(os.getenv(
    "PKI_BASE_PATH",
    r"C:\VCC\PKI"
))

# Mock Mode (für Entwicklung ohne echte PKI)
# Wenn True: In-Memory Mock-Implementierung
# Wenn False: Echte PKI-Integration mit cryptography
PKI_MOCK_MODE = os.getenv("PKI_MOCK_MODE", "true").lower() == "true"

# PKI Enabled (globaler Toggle)
PKI_ENABLED = os.getenv("PKI_ENABLED", "true").lower() == "true"


# ============================================================================
# PKI Directory Structure
# ============================================================================

# CA-spezifische Verzeichnisse (nur für echte PKI)
PKI_CA_DIR = PKI_BASE_PATH / "ca"
PKI_CERTS_DIR = PKI_BASE_PATH / "certs"
PKI_PRIVATE_DIR = PKI_BASE_PATH / "private"
PKI_CONFIG_DIR = PKI_BASE_PATH / "config"
PKI_CRL_DIR = PKI_BASE_PATH / "crl"
PKI_CSR_DIR = PKI_BASE_PATH / "csr"


# ============================================================================
# Certificate Settings
# ============================================================================

# Standard-Gültigkeit für Zertifikate (in Tagen)
CERT_VALIDITY_DAYS = int(os.getenv("CERT_VALIDITY_DAYS", "365"))

# RSA-Schlüsselgröße (2048, 4096)
CERT_KEY_SIZE = int(os.getenv("CERT_KEY_SIZE", "2048"))

# Hash-Algorithmus für Signaturen
CERT_HASH_ALGORITHM = os.getenv("CERT_HASH_ALGORITHM", "SHA256")

# Zertifikatstypen
CERT_TYPES = {
    "server": "Server Certificate",
    "client": "Client Certificate",
    "code_signing": "Code Signing Certificate",
    "email": "Email Certificate"
}


# ============================================================================
# CA (Certificate Authority) Settings
# ============================================================================

# CA Distinguished Name (DN) Komponenten
CA_NAME = os.getenv("CA_NAME", "VERITAS CA")
CA_COUNTRY = os.getenv("CA_COUNTRY", "DE")
CA_STATE = os.getenv("CA_STATE", "NRW")
CA_LOCALITY = os.getenv("CA_LOCALITY", "Köln")
CA_ORGANIZATION = os.getenv("CA_ORGANIZATION", "VERITAS")
CA_ORGANIZATIONAL_UNIT = os.getenv("CA_ORGANIZATIONAL_UNIT", "IT Security")
CA_EMAIL = os.getenv("CA_EMAIL", "ca@veritas.local")

# CA-Zertifikat Gültigkeit (in Jahren)
CA_VALIDITY_YEARS = int(os.getenv("CA_VALIDITY_YEARS", "10"))

# CRL (Certificate Revocation List) Update-Intervall (in Stunden)
CRL_UPDATE_INTERVAL_HOURS = int(os.getenv("CRL_UPDATE_INTERVAL_HOURS", "24"))


# ============================================================================
# Crypto Settings
# ============================================================================

# Unterstützte Hash-Algorithmen
SUPPORTED_HASH_ALGORITHMS = ["SHA256", "SHA384", "SHA512"]

# Unterstützte Schlüsselgrößen
SUPPORTED_KEY_SIZES = [2048, 4096]

# Encryption Padding (für echte PKI)
ENCRYPTION_PADDING = "OAEP"  # OAEP oder PKCS1v15


# ============================================================================
# Mock Data Configuration
# ============================================================================

# Mock-Modus: Maximale Anzahl Zertifikate
MOCK_MAX_CERTIFICATES = int(os.getenv("MOCK_MAX_CERTIFICATES", "1000"))

# Mock-Modus: Standard-Fingerprint-Länge
MOCK_FINGERPRINT_LENGTH = 64  # SHA256 Hex-Length


# ============================================================================
# Helper Functions
# ============================================================================

def get_pki_config() -> Dict[str, Any]:
    """
    Gibt die komplette PKI-Konfiguration als Dictionary zurück.
    
    Returns:
        Dict mit allen Konfigurationswerten
    """
    return {
        # Base
        "pki_base_path": str(PKI_BASE_PATH),
        "pki_mock_mode": PKI_MOCK_MODE,
        "pki_enabled": PKI_ENABLED,
        
        # Directories
        "ca_dir": str(PKI_CA_DIR),
        "certs_dir": str(PKI_CERTS_DIR),
        "private_dir": str(PKI_PRIVATE_DIR),
        "config_dir": str(PKI_CONFIG_DIR),
        "crl_dir": str(PKI_CRL_DIR),
        "csr_dir": str(PKI_CSR_DIR),
        
        # Certificate Settings
        "cert_validity_days": CERT_VALIDITY_DAYS,
        "cert_key_size": CERT_KEY_SIZE,
        "cert_hash_algorithm": CERT_HASH_ALGORITHM,
        
        # CA Settings
        "ca_name": CA_NAME,
        "ca_country": CA_COUNTRY,
        "ca_state": CA_STATE,
        "ca_locality": CA_LOCALITY,
        "ca_organization": CA_ORGANIZATION,
        "ca_organizational_unit": CA_ORGANIZATIONAL_UNIT,
        "ca_email": CA_EMAIL,
        "ca_validity_years": CA_VALIDITY_YEARS,
        "crl_update_interval_hours": CRL_UPDATE_INTERVAL_HOURS,
        
        # Crypto Settings
        "supported_hash_algorithms": SUPPORTED_HASH_ALGORITHMS,
        "supported_key_sizes": SUPPORTED_KEY_SIZES,
        "encryption_padding": ENCRYPTION_PADDING,
        
        # Mock Settings
        "mock_max_certificates": MOCK_MAX_CERTIFICATES,
        "mock_fingerprint_length": MOCK_FINGERPRINT_LENGTH
    }


def validate_config() -> bool:
    """
    Validiert die PKI-Konfiguration.
    
    Returns:
        True wenn Konfiguration valide, sonst False
    """
    # Prüfe Key Size
    if CERT_KEY_SIZE not in SUPPORTED_KEY_SIZES:
        return False
    
    # Prüfe Hash Algorithm
    if CERT_HASH_ALGORITHM not in SUPPORTED_HASH_ALGORITHMS:
        return False
    
    # Prüfe Validity Days
    if CERT_VALIDITY_DAYS < 1 or CERT_VALIDITY_DAYS > 3650:
        return False
    
    # Wenn nicht Mock-Mode: Prüfe ob PKI-Verzeichnis existiert
    if not PKI_MOCK_MODE and PKI_ENABLED:
        if not PKI_BASE_PATH.exists():
            return False
    
    return True


def is_mock_mode() -> bool:
    """
    Prüft ob PKI im Mock-Mode läuft.
    
    Returns:
        True wenn Mock-Mode aktiv
    """
    return PKI_MOCK_MODE


def get_ca_distinguished_name() -> Dict[str, str]:
    """
    Gibt den Distinguished Name (DN) der CA zurück.
    
    Returns:
        Dict mit DN-Komponenten
    """
    return {
        "common_name": CA_NAME,
        "country": CA_COUNTRY,
        "state": CA_STATE,
        "locality": CA_LOCALITY,
        "organization": CA_ORGANIZATION,
        "organizational_unit": CA_ORGANIZATIONAL_UNIT,
        "email": CA_EMAIL
    }


# ============================================================================
# Konfiguration beim Import validieren
# ============================================================================

if not validate_config():
    import warnings
    warnings.warn(
        "PKI configuration validation failed! Check PKI_* environment variables.",
        RuntimeWarning
    )
