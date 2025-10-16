"""
Tests für Crypto Utilities
Unit tests für kryptografische Funktionen
"""

import pytest

from pki.crypto_utils import (
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
from pki.exceptions import (
    KeyGenerationError,
    EncryptionError,
    DecryptionError,
    SignatureVerificationError,
    InvalidCSRError
)


class TestKeyGeneration:
    """Tests für Schlüsselgenerierung"""
    
    def test_generate_key_pair_default(self):
        """Test: Schlüsselpaar mit Standardgröße"""
        private_key, public_key = generate_key_pair()
        
        assert private_key is not None
        assert public_key is not None
        assert "PRIVATE KEY" in private_key
        assert "PUBLIC KEY" in public_key
        assert "2048" in private_key  # Default size
    
    def test_generate_key_pair_4096(self):
        """Test: Schlüsselpaar mit 4096 Bit"""
        private_key, public_key = generate_key_pair(key_size=4096)
        
        assert "4096" in private_key
        assert "4096" in public_key
    
    def test_generate_key_pair_invalid_size(self):
        """Test: Ungültige Schlüsselgröße"""
        with pytest.raises(KeyGenerationError):
            generate_key_pair(key_size=1024)
    
    def test_generate_key_pair_unique(self):
        """Test: Eindeutigkeit der Schlüssel"""
        key1_priv, key1_pub = generate_key_pair()
        key2_priv, key2_pub = generate_key_pair()
        
        assert key1_priv != key2_priv
        assert key1_pub != key2_pub


class TestCSRGeneration:
    """Tests für CSR-Generierung"""
    
    def test_generate_csr_basic(self):
        """Test: Basis-CSR"""
        private_key, _ = generate_key_pair()
        csr_pem = generate_csr(
            private_key_pem=private_key,
            common_name="test.veritas.local"
        )
        
        assert csr_pem is not None
        assert "CERTIFICATE REQUEST" in csr_pem
        assert "CN=test.veritas.local" in csr_pem
    
    def test_generate_csr_with_details(self):
        """Test: CSR mit vollständigen Details"""
        private_key, _ = generate_key_pair()
        csr_pem = generate_csr(
            private_key_pem=private_key,
            common_name="api.veritas.local",
            country="DE",
            state="NRW",
            locality="Köln",
            organization="VERITAS",
            organizational_unit="IT",
            email="admin@veritas.local"
        )
        
        assert "CN=api.veritas.local" in csr_pem
        assert "C=DE" in csr_pem
        assert "O=VERITAS" in csr_pem
        assert "emailAddress=admin@veritas.local" in csr_pem
    
    def test_generate_csr_no_common_name(self):
        """Test: CSR ohne Common Name"""
        private_key, _ = generate_key_pair()
        
        with pytest.raises(InvalidCSRError):
            generate_csr(private_key_pem=private_key, common_name="")
    
    def test_generate_csr_invalid_key(self):
        """Test: CSR mit ungültigem Key"""
        with pytest.raises(InvalidCSRError):
            generate_csr(
                private_key_pem="not a key",
                common_name="test.local"
            )


class TestFingerprint:
    """Tests für Fingerprint-Berechnung"""
    
    def test_calculate_fingerprint_default(self):
        """Test: Fingerprint mit SHA256"""
        cert_pem = "-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
        fingerprint = calculate_fingerprint(cert_pem)
        
        assert fingerprint is not None
        assert len(fingerprint) == 64  # SHA256 = 64 hex chars
    
    def test_calculate_fingerprint_sha384(self):
        """Test: Fingerprint mit SHA384"""
        cert_pem = "-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
        fingerprint = calculate_fingerprint(cert_pem, algorithm="SHA384")
        
        assert len(fingerprint) == 96  # SHA384 = 96 hex chars
    
    def test_calculate_fingerprint_sha512(self):
        """Test: Fingerprint mit SHA512"""
        cert_pem = "-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
        fingerprint = calculate_fingerprint(cert_pem, algorithm="SHA512")
        
        assert len(fingerprint) == 128  # SHA512 = 128 hex chars
    
    def test_calculate_fingerprint_same_input(self):
        """Test: Gleicher Input = gleicher Fingerprint"""
        cert_pem = "-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
        fp1 = calculate_fingerprint(cert_pem)
        fp2 = calculate_fingerprint(cert_pem)
        
        assert fp1 == fp2
    
    def test_calculate_fingerprint_different_input(self):
        """Test: Unterschiedlicher Input = unterschiedlicher Fingerprint"""
        cert1 = "-----BEGIN CERTIFICATE-----\ntest1\n-----END CERTIFICATE-----"
        cert2 = "-----BEGIN CERTIFICATE-----\ntest2\n-----END CERTIFICATE-----"
        
        fp1 = calculate_fingerprint(cert1)
        fp2 = calculate_fingerprint(cert2)
        
        assert fp1 != fp2


class TestEncryption:
    """Tests für Verschlüsselung/Entschlüsselung"""
    
    def test_encrypt_decrypt_basic(self):
        """Test: Basis-Verschlüsselung und Entschlüsselung"""
        private_key, public_key = generate_key_pair()
        data = b"Hello VERITAS"
        
        # Verschlüsseln
        encrypted = encrypt_data(data, public_key)
        
        # Entschlüsseln
        decrypted = decrypt_data(encrypted, private_key)
        
        assert decrypted == data
    
    def test_encrypt_empty_data(self):
        """Test: Leere Daten verschlüsseln"""
        _, public_key = generate_key_pair()
        
        with pytest.raises(EncryptionError):
            encrypt_data(b"", public_key)
    
    def test_encrypt_invalid_key(self):
        """Test: Verschlüsselung mit ungültigem Key"""
        with pytest.raises(EncryptionError):
            encrypt_data(b"test", "not a key")
    
    def test_decrypt_empty_data(self):
        """Test: Leere Daten entschlüsseln"""
        private_key, _ = generate_key_pair()
        
        with pytest.raises(DecryptionError):
            decrypt_data(b"", private_key)
    
    def test_decrypt_invalid_key(self):
        """Test: Entschlüsselung mit ungültigem Key"""
        with pytest.raises(DecryptionError):
            decrypt_data(b"encrypted_data", "not a key")
    
    def test_encrypt_decrypt_large_data(self):
        """Test: Große Daten"""
        private_key, public_key = generate_key_pair()
        data = b"A" * 1000  # 1KB
        
        encrypted = encrypt_data(data, public_key)
        decrypted = decrypt_data(encrypted, private_key)
        
        assert decrypted == data


class TestSigning:
    """Tests für Signierung/Verifikation"""
    
    def test_sign_and_verify(self):
        """Test: Signieren und Verifizieren"""
        private_key, public_key = generate_key_pair()
        data = b"Sign this message"
        
        # Signieren
        signature = sign_data(data, private_key)
        
        # Verifizieren
        is_valid = verify_signature(data, signature, public_key)
        
        assert is_valid is True
    
    def test_verify_tampered_data(self):
        """Test: Manipulierte Daten"""
        private_key, public_key = generate_key_pair()
        data = b"Original message"
        
        signature = sign_data(data, private_key)
        
        # Ändere Daten
        tampered_data = b"Tampered message"
        is_valid = verify_signature(tampered_data, signature, public_key)
        
        assert is_valid is False
    
    def test_sign_empty_data(self):
        """Test: Leere Daten signieren"""
        private_key, _ = generate_key_pair()
        
        with pytest.raises(EncryptionError):
            sign_data(b"", private_key)
    
    def test_sign_invalid_key(self):
        """Test: Signierung mit ungültigem Key"""
        with pytest.raises(EncryptionError):
            sign_data(b"test", "not a key")
    
    def test_verify_empty_data(self):
        """Test: Leere Daten verifizieren"""
        _, public_key = generate_key_pair()
        
        with pytest.raises(SignatureVerificationError):
            verify_signature(b"", b"signature", public_key)
    
    def test_verify_invalid_key(self):
        """Test: Verifikation mit ungültigem Key"""
        with pytest.raises(SignatureVerificationError):
            verify_signature(b"data", b"signature", "not a key")
    
    def test_sign_verify_different_keys(self):
        """Test: Verifikation mit falschem Public Key"""
        private_key1, _ = generate_key_pair()
        _, public_key2 = generate_key_pair()
        
        data = b"Test message"
        signature = sign_data(data, private_key1)
        
        # Sollte fehlschlagen (falscher Public Key)
        is_valid = verify_signature(data, signature, public_key2)
        assert is_valid is False


class TestRandomGeneration:
    """Tests für Zufallsgenerierung"""
    
    def test_generate_random_bytes(self):
        """Test: Zufallsbytes generieren"""
        random_bytes = generate_random_bytes(32)
        
        assert len(random_bytes) == 32
        assert isinstance(random_bytes, bytes)
    
    def test_generate_random_bytes_unique(self):
        """Test: Eindeutigkeit von Zufallsbytes"""
        bytes1 = generate_random_bytes(32)
        bytes2 = generate_random_bytes(32)
        
        assert bytes1 != bytes2
    
    def test_generate_random_hex(self):
        """Test: Zufalls-Hex generieren"""
        random_hex = generate_random_hex(32)
        
        assert len(random_hex) == 32
        assert isinstance(random_hex, str)
        # Prüfe ob Hex-Zeichen
        assert all(c in "0123456789abcdef" for c in random_hex)
    
    def test_generate_random_hex_unique(self):
        """Test: Eindeutigkeit von Zufalls-Hex"""
        hex1 = generate_random_hex(32)
        hex2 = generate_random_hex(32)
        
        assert hex1 != hex2


class TestHashing:
    """Tests für Hash-Funktionen"""
    
    def test_hash_data_sha256(self):
        """Test: SHA256 Hash"""
        data = b"Test data"
        hash_value = hash_data(data, algorithm="SHA256")
        
        assert len(hash_value) == 64  # SHA256 = 64 hex chars
        assert isinstance(hash_value, str)
    
    def test_hash_data_sha384(self):
        """Test: SHA384 Hash"""
        data = b"Test data"
        hash_value = hash_data(data, algorithm="SHA384")
        
        assert len(hash_value) == 96  # SHA384 = 96 hex chars
    
    def test_hash_data_sha512(self):
        """Test: SHA512 Hash"""
        data = b"Test data"
        hash_value = hash_data(data, algorithm="SHA512")
        
        assert len(hash_value) == 128  # SHA512 = 128 hex chars
    
    def test_hash_data_same_input(self):
        """Test: Gleicher Input = gleicher Hash"""
        data = b"Test data"
        hash1 = hash_data(data)
        hash2 = hash_data(data)
        
        assert hash1 == hash2
    
    def test_hash_data_different_input(self):
        """Test: Unterschiedlicher Input = unterschiedlicher Hash"""
        hash1 = hash_data(b"Data 1")
        hash2 = hash_data(b"Data 2")
        
        assert hash1 != hash2
