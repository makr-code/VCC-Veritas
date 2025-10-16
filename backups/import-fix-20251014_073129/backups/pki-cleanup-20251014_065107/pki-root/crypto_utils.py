"""
Cryptographic Utilities
Mock-Implementierung für kryptografische Operationen

Diese Utilities bieten Mock-Implementierungen für Verschlüsselung,
Signierung und Schlüsselgenerierung während der Entwicklung.
"""

import hashlib
import secrets
import base64
from typing import Tuple, Optional
from datetime import datetime, timezone

from .exceptions import (
    KeyGenerationError,
    EncryptionError,
    DecryptionError,
    SignatureVerificationError,
    InvalidCSRError
)
from .config import (
    CERT_KEY_SIZE,
    CERT_HASH_ALGORITHM,
    MOCK_FINGERPRINT_LENGTH
)


# ============================================================================
# Key Generation
# ============================================================================

def generate_key_pair(key_size: int = CERT_KEY_SIZE) -> Tuple[str, str]:
    """
    Generiert ein RSA-Schlüsselpaar (Mock).
    
    In Produktion würde hier cryptography.hazmat verwendet.
    Aktuell: Mock-PEM-Strings
    
    Args:
        key_size: Schlüsselgröße in Bits (2048 oder 4096)
    
    Returns:
        Tuple: (private_key_pem, public_key_pem)
    
    Raises:
        KeyGenerationError: Bei ungültiger key_size
    """
    if key_size not in [2048, 4096]:
        raise KeyGenerationError(f"Unsupported key size: {key_size}")
    
    # Mock: Generiere zufällige "Keys"
    key_id = secrets.token_hex(16)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    private_key_pem = f"""-----BEGIN PRIVATE KEY-----
MOCK_PRIVATE_KEY_{key_id}
KeySize: {key_size}
Generated: {timestamp}
Type: RSA
-----END PRIVATE KEY-----"""
    
    public_key_pem = f"""-----BEGIN PUBLIC KEY-----
MOCK_PUBLIC_KEY_{key_id}
KeySize: {key_size}
Generated: {timestamp}
Type: RSA
-----END PUBLIC KEY-----"""
    
    return private_key_pem, public_key_pem


# ============================================================================
# CSR Generation
# ============================================================================

def generate_csr(
    private_key_pem: str,
    common_name: str,
    country: Optional[str] = None,
    state: Optional[str] = None,
    locality: Optional[str] = None,
    organization: Optional[str] = None,
    organizational_unit: Optional[str] = None,
    email: Optional[str] = None
) -> str:
    """
    Generiert einen Certificate Signing Request (Mock).
    
    Args:
        private_key_pem: Private Key PEM-String
        common_name: Common Name (CN) für das Zertifikat
        country: Ländercode (C)
        state: Bundesland/Staat (ST)
        locality: Stadt (L)
        organization: Organisation (O)
        organizational_unit: Organisationseinheit (OU)
        email: E-Mail-Adresse
    
    Returns:
        CSR PEM-String
    
    Raises:
        InvalidCSRError: Bei fehlenden Pflichtfeldern
    """
    if not common_name:
        raise InvalidCSRError("Common name is required")
    
    if not private_key_pem or "PRIVATE KEY" not in private_key_pem:
        raise InvalidCSRError("Invalid private key")
    
    # Mock: Erstelle CSR
    csr_id = secrets.token_hex(12)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    dn_components = [f"CN={common_name}"]
    if country:
        dn_components.append(f"C={country}")
    if state:
        dn_components.append(f"ST={state}")
    if locality:
        dn_components.append(f"L={locality}")
    if organization:
        dn_components.append(f"O={organization}")
    if organizational_unit:
        dn_components.append(f"OU={organizational_unit}")
    if email:
        dn_components.append(f"emailAddress={email}")
    
    dn = ", ".join(dn_components)
    
    csr_pem = f"""-----BEGIN CERTIFICATE REQUEST-----
MOCK_CSR_{csr_id}
Subject: {dn}
Generated: {timestamp}
Signature Algorithm: sha256WithRSAEncryption
-----END CERTIFICATE REQUEST-----"""
    
    return csr_pem


# ============================================================================
# Fingerprint Calculation
# ============================================================================

def calculate_fingerprint(
    cert_pem: str,
    algorithm: str = CERT_HASH_ALGORITHM
) -> str:
    """
    Berechnet den Fingerprint eines Zertifikats.
    
    Args:
        cert_pem: Zertifikat PEM-String
        algorithm: Hash-Algorithmus (SHA256, SHA384, SHA512)
    
    Returns:
        Fingerprint als Hex-String
    """
    # Mock: Verwende Hash über PEM-String
    if algorithm.upper() == "SHA256":
        hash_obj = hashlib.sha256()
    elif algorithm.upper() == "SHA384":
        hash_obj = hashlib.sha384()
    elif algorithm.upper() == "SHA512":
        hash_obj = hashlib.sha512()
    else:
        hash_obj = hashlib.sha256()  # Default
    
    hash_obj.update(cert_pem.encode('utf-8'))
    return hash_obj.hexdigest()


# ============================================================================
# Encryption / Decryption
# ============================================================================

def encrypt_data(data: bytes, public_key_pem: str) -> bytes:
    """
    Verschlüsselt Daten mit einem öffentlichen Schlüssel (Mock).
    
    Args:
        data: Zu verschlüsselnde Daten
        public_key_pem: Öffentlicher Schlüssel PEM
    
    Returns:
        Verschlüsselte Daten
    
    Raises:
        EncryptionError: Bei Verschlüsselungsfehlern
    """
    if not data:
        raise EncryptionError("No data to encrypt")
    
    if not public_key_pem or "PUBLIC KEY" not in public_key_pem:
        raise EncryptionError("Invalid public key")
    
    # Mock: Base64-Encoding als "Verschlüsselung"
    # In Produktion: RSA/OAEP mit cryptography
    try:
        encrypted = base64.b64encode(data)
        # Füge Mock-Header hinzu
        mock_encrypted = b"MOCK_ENCRYPTED:" + encrypted
        return mock_encrypted
    except Exception as e:
        raise EncryptionError(f"Encryption failed: {str(e)}")


def decrypt_data(encrypted_data: bytes, private_key_pem: str) -> bytes:
    """
    Entschlüsselt Daten mit einem privaten Schlüssel (Mock).
    
    Args:
        encrypted_data: Verschlüsselte Daten
        private_key_pem: Privater Schlüssel PEM
    
    Returns:
        Entschlüsselte Daten
    
    Raises:
        DecryptionError: Bei Entschlüsselungsfehlern
    """
    if not encrypted_data:
        raise DecryptionError("No data to decrypt")
    
    if not private_key_pem or "PRIVATE KEY" not in private_key_pem:
        raise DecryptionError("Invalid private key")
    
    # Mock: Base64-Decoding als "Entschlüsselung"
    try:
        # Entferne Mock-Header
        if encrypted_data.startswith(b"MOCK_ENCRYPTED:"):
            encrypted_data = encrypted_data[15:]  # len("MOCK_ENCRYPTED:")
        
        decrypted = base64.b64decode(encrypted_data)
        return decrypted
    except Exception as e:
        raise DecryptionError(f"Decryption failed: {str(e)}")


# ============================================================================
# Signing / Verification
# ============================================================================

def sign_data(data: bytes, private_key_pem: str) -> bytes:
    """
    Signiert Daten mit einem privaten Schlüssel (Mock).
    
    Args:
        data: Zu signierende Daten
        private_key_pem: Privater Schlüssel PEM
    
    Returns:
        Signatur als Bytes
    
    Raises:
        EncryptionError: Bei Signierungsfehlern
    """
    if not data:
        raise EncryptionError("No data to sign")
    
    if not private_key_pem or "PRIVATE KEY" not in private_key_pem:
        raise EncryptionError("Invalid private key")
    
    # Mock: HMAC-SHA256 als Signatur
    try:
        # Extrahiere "Key ID" aus Mock-Key
        key_id = private_key_pem.split("MOCK_PRIVATE_KEY_")[1].split("\n")[0]
        
        # Erstelle Signatur
        signature_data = data + key_id.encode('utf-8')
        signature = hashlib.sha256(signature_data).digest()
        
        # Füge Mock-Header hinzu
        mock_signature = b"MOCK_SIGNATURE:" + base64.b64encode(signature)
        return mock_signature
    except Exception as e:
        raise EncryptionError(f"Signing failed: {str(e)}")


def verify_signature(
    data: bytes,
    signature: bytes,
    public_key_pem: str
) -> bool:
    """
    Verifiziert eine Signatur (Mock).
    
    Args:
        data: Original-Daten
        signature: Signatur
        public_key_pem: Öffentlicher Schlüssel PEM
    
    Returns:
        True wenn Signatur valide
    
    Raises:
        SignatureVerificationError: Bei Verifikationsfehlern
    """
    if not data or not signature:
        raise SignatureVerificationError("Missing data or signature")
    
    if not public_key_pem or "PUBLIC KEY" not in public_key_pem:
        raise SignatureVerificationError("Invalid public key")
    
    try:
        # Entferne Mock-Header
        if signature.startswith(b"MOCK_SIGNATURE:"):
            signature = signature[15:]  # len("MOCK_SIGNATURE:")
        
        # Extrahiere "Key ID" aus Public Key
        key_id = public_key_pem.split("MOCK_PUBLIC_KEY_")[1].split("\n")[0]
        
        # Berechne erwartete Signatur
        signature_data = data + key_id.encode('utf-8')
        expected_signature = hashlib.sha256(signature_data).digest()
        
        # Dekodiere empfangene Signatur
        received_signature = base64.b64decode(signature)
        
        # Vergleiche
        return secrets.compare_digest(expected_signature, received_signature)
    
    except Exception as e:
        raise SignatureVerificationError(f"Verification failed: {str(e)}")


# ============================================================================
# Utility Functions
# ============================================================================

def generate_random_bytes(length: int = 32) -> bytes:
    """
    Generiert kryptografisch sichere Zufallsbytes.
    
    Args:
        length: Anzahl der Bytes
    
    Returns:
        Zufallsbytes
    """
    return secrets.token_bytes(length)


def generate_random_hex(length: int = 32) -> str:
    """
    Generiert kryptografisch sicheren Zufalls-Hex-String.
    
    Args:
        length: Anzahl der Hex-Zeichen (wird auf gerade Zahl gerundet)
    
    Returns:
        Hex-String
    """
    byte_length = (length + 1) // 2
    return secrets.token_hex(byte_length)[:length]


def hash_data(data: bytes, algorithm: str = CERT_HASH_ALGORITHM) -> str:
    """
    Hash-Funktion für Daten.
    
    Args:
        data: Zu hashende Daten
        algorithm: Hash-Algorithmus (SHA256, SHA384, SHA512)
    
    Returns:
        Hash als Hex-String
    """
    if algorithm.upper() == "SHA256":
        hash_obj = hashlib.sha256()
    elif algorithm.upper() == "SHA384":
        hash_obj = hashlib.sha384()
    elif algorithm.upper() == "SHA512":
        hash_obj = hashlib.sha512()
    else:
        hash_obj = hashlib.sha256()
    
    hash_obj.update(data)
    return hash_obj.hexdigest()
