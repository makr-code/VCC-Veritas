"""
PKI Quick Start Example

Production-Ready PKI Usage Examples:
- Root CA Setup
- Certificate Creation
- CSR Signing
- Certificate Validation
- Encryption/Decryption
- Digital Signatures

**Mode:** PRODUCTION (NO MOCK)
**Date:** 13. Oktober 2025
"""

from backend.pki import (
    CertificateManager,
    CAService,
    generate_keypair,
    generate_csr,
    encrypt_data,
    decrypt_data,
    sign_data,
    verify_signature,
    hash_data,
    generate_random_key
)


def example_1_root_ca_setup():
    """Example 1: Initialize Root CA"""
    print("\n=== Example 1: Root CA Setup ===")
    
    # Initialize CA Service
    ca_service = CAService(ca_storage_path="./example_ca_storage")
    
    # Create Root CA
    if not ca_service.is_initialized():
        root_ca = ca_service.initialize_root_ca(
            common_name="Example Root CA",
            validity_days=3650,  # 10 years
            key_size=4096,
            organization="Example Corp",
            country="DE",
            state="Bavaria",
            locality="Munich"
        )
        print(f"✅ Root CA created:")
        print(f"   Common Name: {root_ca['common_name']}")
        print(f"   Valid until: {root_ca['not_valid_after']}")
        print(f"   Serial: {root_ca['serial_number']}")
    else:
        print("✅ Root CA already initialized")
        stats = ca_service.get_ca_statistics()
        print(f"   Root CA: {stats['root_ca_id']}")


def example_2_create_certificate():
    """Example 2: Create End-Entity Certificate"""
    print("\n=== Example 2: Create Certificate ===")
    
    # Initialize Certificate Manager
    cert_manager = CertificateManager(storage_path="./example_cert_storage")
    
    # Create certificate
    cert_info = cert_manager.create_certificate(
        subject_name="example.com",
        validity_days=365,
        key_size=2048,
        is_ca=False,
        organization="Example Corp",
        country="DE"
    )
    
    print(f"✅ Certificate created:")
    print(f"   Certificate ID: {cert_info['cert_id']}")
    print(f"   Subject: {cert_info['subject_name']}")
    print(f"   Valid until: {cert_info['not_valid_after']}")
    print(f"   Serial: {cert_info['serial_number']}")
    
    return cert_info['cert_id']


def example_3_csr_signing():
    """Example 3: CSR Signing by CA"""
    print("\n=== Example 3: CSR Signing ===")
    
    # Generate key pair for client
    print("Generating key pair...")
    private_key, public_key = generate_keypair(2048)
    
    # Generate CSR
    print("Creating CSR...")
    csr = generate_csr(
        private_key,
        common_name="client.example.com",
        organization="Example Corp",
        country="DE"
    )
    print(f"✅ CSR created: {len(csr)} bytes")
    
    # Sign CSR with CA
    ca_service = CAService(ca_storage_path="./example_ca_storage")
    
    if ca_service.is_initialized():
        print("Signing CSR with Root CA...")
        signed_cert = ca_service.sign_csr(
            csr,
            validity_days=365,
            is_ca=False
        )
        
        print(f"✅ Certificate signed:")
        print(f"   Subject: {signed_cert['subject_name']}")
        print(f"   Serial: {signed_cert['serial_number']}")
        print(f"   Issuer CA: {signed_cert['issuer_ca_id']}")
    else:
        print("⚠️  Root CA not initialized. Run example_1_root_ca_setup() first.")


def example_4_certificate_validation():
    """Example 4: Certificate Validation"""
    print("\n=== Example 4: Certificate Validation ===")
    
    cert_manager = CertificateManager(storage_path="./example_cert_storage")
    
    # List certificates
    certs = cert_manager.list_certificates(include_revoked=False)
    
    if not certs:
        print("⚠️  No certificates found. Run example_2_create_certificate() first.")
        return
    
    # Validate first certificate
    cert_id = certs[0]['cert_id']
    print(f"Validating certificate: {cert_id}")
    
    validation_result = cert_manager.validate_certificate(cert_id)
    
    print(f"\n{'✅' if validation_result['valid'] else '❌'} Validation Result:")
    print(f"   Valid: {validation_result['valid']}")
    print(f"   Checks:")
    for check, passed in validation_result['checks'].items():
        print(f"     - {check}: {'✅' if passed else '❌'}")
    
    if validation_result['errors']:
        print(f"   Errors: {validation_result['errors']}")
    if validation_result['warnings']:
        print(f"   Warnings: {validation_result['warnings']}")


def example_5_encryption_decryption():
    """Example 5: AES-256-GCM Encryption/Decryption"""
    print("\n=== Example 5: Encryption/Decryption ===")
    
    # Generate encryption key
    key = generate_random_key(32)  # AES-256
    print(f"Key generated: {key.hex()[:32]}...")
    
    # Encrypt data
    plaintext = b"This is a secret message!"
    print(f"Plaintext: {plaintext.decode()}")
    
    ciphertext, nonce, tag = encrypt_data(plaintext, key)
    print(f"✅ Encrypted: {len(ciphertext)} bytes")
    print(f"   Ciphertext: {ciphertext.hex()[:32]}...")
    print(f"   Nonce: {nonce.hex()}")
    print(f"   Tag: {tag.hex()}")
    
    # Decrypt data
    decrypted = decrypt_data(ciphertext, key, nonce, tag)
    print(f"✅ Decrypted: {decrypted.decode()}")
    
    assert plaintext == decrypted, "Decryption failed!"
    print("✅ Verification: Plaintext matches decrypted data")


def example_6_digital_signatures():
    """Example 6: RSA Digital Signatures"""
    print("\n=== Example 6: Digital Signatures ===")
    
    # Generate key pair
    private_key, public_key = generate_keypair(2048)
    print("Key pair generated")
    
    # Sign data
    data = b"Important document that needs signing"
    print(f"Data: {data.decode()}")
    
    signature = sign_data(data, private_key, algorithm="PSS")
    print(f"✅ Signature created: {len(signature)} bytes")
    print(f"   Signature: {signature.hex()[:32]}...")
    
    # Verify signature
    is_valid = verify_signature(data, signature, public_key, algorithm="PSS")
    print(f"✅ Signature verification: {'VALID' if is_valid else 'INVALID'}")
    
    # Test with tampered data
    tampered_data = b"Tampered document"
    is_valid_tampered = verify_signature(tampered_data, signature, public_key, algorithm="PSS")
    print(f"✅ Tampered data verification: {'VALID' if is_valid_tampered else 'INVALID (expected)'}")


def example_7_hash_functions():
    """Example 7: Cryptographic Hash Functions"""
    print("\n=== Example 7: Hash Functions ===")
    
    data = b"Hello, PKI World!"
    print(f"Data: {data.decode()}")
    
    # SHA-256
    hash_256 = hash_data(data, "SHA256")
    print(f"SHA-256: {hash_256}")
    
    # SHA-384
    hash_384 = hash_data(data, "SHA384")
    print(f"SHA-384: {hash_384}")
    
    # SHA-512
    hash_512 = hash_data(data, "SHA512")
    print(f"SHA-512: {hash_512}")


def example_8_crl_generation():
    """Example 8: Certificate Revocation List (CRL)"""
    print("\n=== Example 8: CRL Generation ===")
    
    ca_service = CAService(ca_storage_path="./example_ca_storage")
    
    if not ca_service.is_initialized():
        print("⚠️  Root CA not initialized. Run example_1_root_ca_setup() first.")
        return
    
    # Revoke a certificate (example)
    cert_manager = CertificateManager(storage_path="./example_cert_storage")
    certs = cert_manager.list_certificates(include_revoked=False)
    
    revoked_certs = []
    if certs:
        # Revoke first certificate as example
        cert_id = certs[0]['cert_id']
        success = cert_manager.revoke_certificate(cert_id, reason="key_compromise")
        
        if success:
            print(f"✅ Certificate revoked: {cert_id}")
            revoked_certs = [{
                'serial_number': certs[0]['serial_number'],
                'revoked_at': certs[0].get('revoked_at', ''),
                'reason': 'key_compromise'
            }]
    
    # Generate CRL
    crl_pem = ca_service.generate_crl("root_ca", revoked_certs)
    print(f"✅ CRL generated: {len(crl_pem)} bytes")
    print(f"CRL Preview:")
    print(crl_pem.decode()[:200] + "...")


def example_9_statistics():
    """Example 9: Get Statistics"""
    print("\n=== Example 9: Statistics ===")
    
    # Certificate Manager Stats
    cert_manager = CertificateManager(storage_path="./example_cert_storage")
    cert_stats = cert_manager.get_statistics()
    
    print("Certificate Manager Statistics:")
    print(f"   Total Certificates: {cert_stats['total_certificates']}")
    print(f"   Active Certificates: {cert_stats['active_certificates']}")
    print(f"   CA Certificates: {cert_stats['ca_certificates']}")
    print(f"   Revoked Certificates: {cert_stats['revoked_certificates']}")
    
    # CA Service Stats
    ca_service = CAService(ca_storage_path="./example_ca_storage")
    ca_stats = ca_service.get_ca_statistics()
    
    print("\nCA Service Statistics:")
    print(f"   Root CA Initialized: {ca_stats['root_ca_initialized']}")
    print(f"   Root CA ID: {ca_stats['root_ca_id']}")
    print(f"   Intermediate CAs: {ca_stats['intermediate_cas_count']}")


# ============================================================================
# Main Runner
# ============================================================================

def run_all_examples():
    """Run all PKI examples"""
    print("=" * 60)
    print("PKI Production Implementation - Quick Start Examples")
    print("=" * 60)
    
    try:
        # Setup
        example_1_root_ca_setup()
        
        # Certificate Operations
        example_2_create_certificate()
        example_3_csr_signing()
        example_4_certificate_validation()
        
        # Cryptographic Operations
        example_5_encryption_decryption()
        example_6_digital_signatures()
        example_7_hash_functions()
        
        # Advanced Operations
        example_8_crl_generation()
        example_9_statistics()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()
