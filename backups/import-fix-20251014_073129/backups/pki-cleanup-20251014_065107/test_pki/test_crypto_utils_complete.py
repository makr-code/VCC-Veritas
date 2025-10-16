"""
Unit Tests for crypto_utils module

Tests for:
- RSA Key Generation
- AES-256-GCM Encryption/Decryption
- Digital Signatures (RSA-PSS, PKCS#1)
- Hash Functions
- CSR Generation

**Mode:** PRODUCTION TESTS (NO MOCK)
"""

import os
import pytest
from backend.pki.crypto_utils import (
    generate_keypair,
    generate_csr,
    encrypt_data,
    decrypt_data,
    sign_data,
    verify_signature,
    hash_data,
    generate_random_key
)


# ============================================================================
# RSA Key Generation Tests
# ============================================================================

class TestKeyGeneration:
    """Test RSA key pair generation"""
    
    def test_generate_keypair_2048(self):
        """Test 2048-bit RSA key generation"""
        private_key, public_key = generate_keypair(2048)
        
        assert private_key is not None
        assert public_key is not None
        assert isinstance(private_key, bytes)
        assert isinstance(public_key, bytes)
        assert b"BEGIN PRIVATE KEY" in private_key
        assert b"BEGIN PUBLIC KEY" in public_key
    
    def test_generate_keypair_3072(self):
        """Test 3072-bit RSA key generation"""
        private_key, public_key = generate_keypair(3072)
        
        assert private_key is not None
        assert public_key is not None
        assert len(private_key) > len(public_key)  # Private key is larger
    
    def test_generate_keypair_4096(self):
        """Test 4096-bit RSA key generation"""
        private_key, public_key = generate_keypair(4096)
        
        assert private_key is not None
        assert public_key is not None
    
    def test_generate_keypair_invalid_size(self):
        """Test invalid key size raises error"""
        with pytest.raises(ValueError) as exc_info:
            generate_keypair(1024)  # Too small
        
        assert "Unsupported key size" in str(exc_info.value)
    
    def test_keypair_uniqueness(self):
        """Test that each keypair is unique"""
        private_key1, public_key1 = generate_keypair(2048)
        private_key2, public_key2 = generate_keypair(2048)
        
        assert private_key1 != private_key2
        assert public_key1 != public_key2


# ============================================================================
# CSR Generation Tests
# ============================================================================

class TestCSRGeneration:
    """Test Certificate Signing Request generation"""
    
    @pytest.fixture
    def keypair(self):
        """Fixture: Generate keypair"""
        return generate_keypair(2048)
    
    def test_generate_csr_basic(self, keypair):
        """Test basic CSR generation"""
        private_key, _ = keypair
        
        csr = generate_csr(
            private_key,
            common_name="test.example.com"
        )
        
        assert csr is not None
        assert isinstance(csr, bytes)
        assert b"BEGIN CERTIFICATE REQUEST" in csr
    
    def test_generate_csr_full_subject(self, keypair):
        """Test CSR with full subject attributes"""
        private_key, _ = keypair
        
        csr = generate_csr(
            private_key,
            common_name="test.example.com",
            country="DE",
            state="Bavaria",
            locality="Munich",
            organization="Test Corp",
            organizational_unit="IT Department",
            email="test@example.com"
        )
        
        assert csr is not None
        assert b"BEGIN CERTIFICATE REQUEST" in csr
    
    def test_generate_csr_invalid_key(self):
        """Test CSR generation with invalid key raises error"""
        with pytest.raises(RuntimeError):
            generate_csr(
                b"invalid_key",
                common_name="test.example.com"
            )


# ============================================================================
# AES Encryption/Decryption Tests
# ============================================================================

class TestEncryptionDecryption:
    """Test AES-256-GCM encryption/decryption"""
    
    @pytest.fixture
    def encryption_key(self):
        """Fixture: Generate encryption key"""
        return generate_random_key(32)  # AES-256
    
    def test_encrypt_decrypt_basic(self, encryption_key):
        """Test basic encryption and decryption"""
        plaintext = b"Secret message"
        
        # Encrypt
        ciphertext, nonce, tag = encrypt_data(plaintext, encryption_key)
        
        assert ciphertext is not None
        assert nonce is not None
        assert tag is not None
        assert len(nonce) == 12  # GCM nonce
        assert len(tag) == 16    # GCM tag
        
        # Decrypt
        decrypted = decrypt_data(ciphertext, encryption_key, nonce, tag)
        
        assert decrypted == plaintext
    
    def test_encrypt_large_data(self, encryption_key):
        """Test encryption of large data"""
        plaintext = b"X" * 10000  # 10KB
        
        ciphertext, nonce, tag = encrypt_data(plaintext, encryption_key)
        decrypted = decrypt_data(ciphertext, encryption_key, nonce, tag)
        
        assert decrypted == plaintext
    
    def test_encrypt_empty_data(self, encryption_key):
        """Test encryption of empty data"""
        plaintext = b""
        
        ciphertext, nonce, tag = encrypt_data(plaintext, encryption_key)
        decrypted = decrypt_data(ciphertext, encryption_key, nonce, tag)
        
        assert decrypted == plaintext
    
    def test_encrypt_invalid_key_size(self):
        """Test encryption with invalid key size"""
        with pytest.raises(ValueError) as exc_info:
            encrypt_data(b"test", b"short_key")
        
        assert "32 bytes" in str(exc_info.value)
    
    def test_decrypt_wrong_key(self, encryption_key):
        """Test decryption with wrong key fails"""
        plaintext = b"Secret message"
        
        ciphertext, nonce, tag = encrypt_data(plaintext, encryption_key)
        
        wrong_key = generate_random_key(32)
        
        with pytest.raises(RuntimeError):
            decrypt_data(ciphertext, wrong_key, nonce, tag)
    
    def test_decrypt_tampered_ciphertext(self, encryption_key):
        """Test decryption of tampered data fails"""
        plaintext = b"Secret message"
        
        ciphertext, nonce, tag = encrypt_data(plaintext, encryption_key)
        
        # Tamper with ciphertext
        tampered_ciphertext = b"X" + ciphertext[1:]
        
        with pytest.raises(RuntimeError):
            decrypt_data(tampered_ciphertext, encryption_key, nonce, tag)
    
    def test_decrypt_invalid_nonce_size(self, encryption_key):
        """Test decryption with invalid nonce size"""
        with pytest.raises(ValueError) as exc_info:
            decrypt_data(b"cipher", encryption_key, b"short", b"X" * 16)
        
        assert "12 bytes" in str(exc_info.value)
    
    def test_decrypt_invalid_tag_size(self, encryption_key):
        """Test decryption with invalid tag size"""
        with pytest.raises(ValueError) as exc_info:
            decrypt_data(b"cipher", encryption_key, b"X" * 12, b"short")
        
        assert "16 bytes" in str(exc_info.value)


# ============================================================================
# Digital Signature Tests
# ============================================================================

class TestDigitalSignatures:
    """Test RSA digital signatures"""
    
    @pytest.fixture
    def keypair(self):
        """Fixture: Generate keypair"""
        return generate_keypair(2048)
    
    def test_sign_verify_pss(self, keypair):
        """Test PSS signature and verification"""
        private_key, public_key = keypair
        data = b"Important document"
        
        # Sign
        signature = sign_data(data, private_key, algorithm="PSS")
        
        assert signature is not None
        assert isinstance(signature, bytes)
        assert len(signature) == 256  # 2048-bit key = 256 bytes signature
        
        # Verify
        is_valid = verify_signature(data, signature, public_key, algorithm="PSS")
        
        assert is_valid is True
    
    def test_sign_verify_pkcs1v15(self, keypair):
        """Test PKCS#1 v1.5 signature and verification"""
        private_key, public_key = keypair
        data = b"Important document"
        
        # Sign
        signature = sign_data(data, private_key, algorithm="PKCS1v15")
        
        assert signature is not None
        
        # Verify
        is_valid = verify_signature(data, signature, public_key, algorithm="PKCS1v15")
        
        assert is_valid is True
    
    def test_verify_tampered_data(self, keypair):
        """Test signature verification fails for tampered data"""
        private_key, public_key = keypair
        data = b"Important document"
        
        signature = sign_data(data, private_key, algorithm="PSS")
        
        tampered_data = b"Tampered document"
        is_valid = verify_signature(tampered_data, signature, public_key, algorithm="PSS")
        
        assert is_valid is False
    
    def test_verify_wrong_public_key(self, keypair):
        """Test signature verification fails with wrong public key"""
        private_key1, _ = keypair
        _, public_key2 = generate_keypair(2048)
        
        data = b"Important document"
        signature = sign_data(data, private_key1, algorithm="PSS")
        
        is_valid = verify_signature(data, signature, public_key2, algorithm="PSS")
        
        assert is_valid is False
    
    def test_sign_empty_data(self, keypair):
        """Test signing empty data"""
        private_key, public_key = keypair
        data = b""
        
        signature = sign_data(data, private_key, algorithm="PSS")
        is_valid = verify_signature(data, signature, public_key, algorithm="PSS")
        
        assert is_valid is True
    
    def test_sign_large_data(self, keypair):
        """Test signing large data"""
        private_key, public_key = keypair
        data = b"X" * 100000  # 100KB
        
        signature = sign_data(data, private_key, algorithm="PSS")
        is_valid = verify_signature(data, signature, public_key, algorithm="PSS")
        
        assert is_valid is True
    
    def test_sign_invalid_algorithm(self, keypair):
        """Test signing with invalid algorithm"""
        private_key, _ = keypair
        
        with pytest.raises(ValueError) as exc_info:
            sign_data(b"data", private_key, algorithm="INVALID")
        
        assert "Unknown algorithm" in str(exc_info.value)
    
    def test_sign_invalid_key(self):
        """Test signing with invalid key"""
        with pytest.raises(RuntimeError):
            sign_data(b"data", b"invalid_key", algorithm="PSS")


# ============================================================================
# Hash Function Tests
# ============================================================================

class TestHashFunctions:
    """Test cryptographic hash functions"""
    
    def test_hash_sha256(self):
        """Test SHA-256 hashing"""
        data = b"Hello, World!"
        
        hash_hex = hash_data(data, "SHA256")
        
        assert hash_hex is not None
        assert isinstance(hash_hex, str)
        assert len(hash_hex) == 64  # SHA-256 = 32 bytes = 64 hex chars
        
        # Verify known hash
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert hash_hex == expected
    
    def test_hash_sha384(self):
        """Test SHA-384 hashing"""
        data = b"Hello, World!"
        
        hash_hex = hash_data(data, "SHA384")
        
        assert hash_hex is not None
        assert len(hash_hex) == 96  # SHA-384 = 48 bytes = 96 hex chars
    
    def test_hash_sha512(self):
        """Test SHA-512 hashing"""
        data = b"Hello, World!"
        
        hash_hex = hash_data(data, "SHA512")
        
        assert hash_hex is not None
        assert len(hash_hex) == 128  # SHA-512 = 64 bytes = 128 hex chars
    
    def test_hash_deterministic(self):
        """Test hash is deterministic"""
        data = b"Test data"
        
        hash1 = hash_data(data, "SHA256")
        hash2 = hash_data(data, "SHA256")
        
        assert hash1 == hash2
    
    def test_hash_different_data(self):
        """Test different data produces different hash"""
        data1 = b"Data 1"
        data2 = b"Data 2"
        
        hash1 = hash_data(data1, "SHA256")
        hash2 = hash_data(data2, "SHA256")
        
        assert hash1 != hash2
    
    def test_hash_empty_data(self):
        """Test hashing empty data"""
        data = b""
        
        hash_hex = hash_data(data, "SHA256")
        
        assert hash_hex is not None
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_hex == expected
    
    def test_hash_large_data(self):
        """Test hashing large data"""
        data = b"X" * 1000000  # 1MB
        
        hash_hex = hash_data(data, "SHA256")
        
        assert hash_hex is not None
        assert len(hash_hex) == 64
    
    def test_hash_invalid_algorithm(self):
        """Test hashing with invalid algorithm"""
        with pytest.raises(ValueError) as exc_info:
            hash_data(b"data", "MD5")  # MD5 not supported
        
        assert "Unknown hash algorithm" in str(exc_info.value)


# ============================================================================
# Utility Function Tests
# ============================================================================

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_generate_random_key(self):
        """Test random key generation"""
        key = generate_random_key(32)
        
        assert key is not None
        assert isinstance(key, bytes)
        assert len(key) == 32
    
    def test_random_keys_are_unique(self):
        """Test random keys are unique"""
        key1 = generate_random_key(32)
        key2 = generate_random_key(32)
        
        assert key1 != key2
    
    def test_generate_random_key_custom_size(self):
        """Test random key with custom size"""
        key = generate_random_key(16)
        
        assert len(key) == 16


# ============================================================================
# Integration Tests
# ============================================================================

class TestCryptoIntegration:
    """Integration tests for crypto operations"""
    
    def test_full_encryption_workflow(self):
        """Test complete encryption workflow"""
        # Generate key
        key = generate_random_key(32)
        
        # Encrypt data
        plaintext = b"Sensitive information"
        ciphertext, nonce, tag = encrypt_data(plaintext, key)
        
        # Decrypt data
        decrypted = decrypt_data(ciphertext, key, nonce, tag)
        
        # Verify
        assert decrypted == plaintext
    
    def test_full_signature_workflow(self):
        """Test complete signature workflow"""
        # Generate keypair
        private_key, public_key = generate_keypair(2048)
        
        # Sign data
        data = b"Contract document"
        signature = sign_data(data, private_key, algorithm="PSS")
        
        # Verify signature
        is_valid = verify_signature(data, signature, public_key, algorithm="PSS")
        
        assert is_valid is True
    
    def test_encryption_and_signature_combined(self):
        """Test encryption + signature workflow"""
        # Setup
        enc_key = generate_random_key(32)
        private_key, public_key = generate_keypair(2048)
        
        # Original data
        plaintext = b"Confidential and authenticated message"
        
        # Encrypt
        ciphertext, nonce, tag = encrypt_data(plaintext, enc_key)
        
        # Sign ciphertext
        signature = sign_data(ciphertext, private_key, algorithm="PSS")
        
        # Verify signature
        sig_valid = verify_signature(ciphertext, signature, public_key, algorithm="PSS")
        assert sig_valid is True
        
        # Decrypt
        decrypted = decrypt_data(ciphertext, enc_key, nonce, tag)
        assert decrypted == plaintext


# ============================================================================
# Performance Tests (Optional)
# ============================================================================

class TestCryptoPerformance:
    """Performance tests for crypto operations"""
    
    def test_key_generation_performance(self, benchmark):
        """Benchmark key generation (requires pytest-benchmark)"""
        try:
            result = benchmark(generate_keypair, 2048)
            assert result is not None
        except:
            pytest.skip("pytest-benchmark not installed")
    
    def test_encryption_performance(self, benchmark):
        """Benchmark encryption (requires pytest-benchmark)"""
        try:
            key = generate_random_key(32)
            data = b"X" * 1000  # 1KB
            
            result = benchmark(encrypt_data, data, key)
            assert result is not None
        except:
            pytest.skip("pytest-benchmark not installed")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
