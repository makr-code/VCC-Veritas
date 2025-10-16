#!/usr/bin/env python3
"""
mTLS Certificate Setup Script

Generates all required certificates for mTLS:
- Root CA (if not exists)
- Server Certificate (for FastAPI backend)
- Client Certificate (for testing)

Usage:
    python scripts/setup_mtls_certificates.py

Output:
    ca_storage/
    ├── ca_certificates/
    │   └── root_ca.pem
    ├── ca_keys/
    │   └── root_ca_key.pem
    ├── server_cert.pem
    ├── server_key.pem
    ├── client_cert.pem
    └── client_key.pem

Author: VERITAS Development Team
Created: 2025-10-13
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'backend'))

from backend.pki.ca_service import CAService
from backend.pki.crypto_utils import generate_keypair, generate_csr


def setup_mtls_certificates():
    """
    Generate all mTLS certificates:
    1. Root CA (self-signed)
    2. Server Certificate (for FastAPI backend)
    3. Client Certificate (for testing)
    """
    
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         mTLS Certificate Setup for VERITAS Framework              ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Initialize CA Service
    ca_storage_path = project_root / "ca_storage"
    ca_storage_path.mkdir(exist_ok=True)
    
    print(f"📁 CA Storage: {ca_storage_path}")
    print()
    
    ca_service = CAService(ca_storage_path=str(ca_storage_path))
    
    # ========================================================================
    # Step 1: Initialize Root CA (if not exists)
    # ========================================================================
    
    print("🔐 Step 1: Root CA Initialization")
    print("─" * 70)
    
    try:
        if ca_service.is_initialized():
            print("✅ Root CA already initialized")
            ca_config = ca_service._load_ca_config()
            if 'root_ca_info' in ca_config:
                ca_info = ca_config['root_ca_info']
                print(f"   Common Name: {ca_info.get('common_name', 'VERITAS Root CA')}")
                print(f"   Valid Until: {ca_info.get('not_valid_after', 'N/A')}")
            print()
        else:
            print("🔨 Creating Root CA...")
            root_ca = ca_service.initialize_root_ca(
                common_name="VERITAS Root CA",
                organization="VERITAS Framework",
                organizational_unit="Security",
                country="DE",
                state="NRW",
                locality="Köln",
                validity_days=3650  # 10 years
            )
            
            print("✅ Root CA created successfully!")
            print(f"   Common Name: {root_ca.get('common_name', 'VERITAS Root CA')}")
            print(f"   Valid Until: {root_ca['not_valid_after']}")
            print(f"   Key Size: {root_ca['key_size']} bit")
            print(f"   Serial Number: {root_ca['serial_number']}")
            print()
    
    except Exception as e:
        print(f"❌ Error initializing Root CA: {e}")
        return False
    
    # ========================================================================
    # Step 2: Generate Server Certificate
    # ========================================================================
    
    print("🖥️  Step 2: Server Certificate Generation")
    print("─" * 70)
    
    try:
        server_cert_path = ca_storage_path / "server_cert.pem"
        server_key_path = ca_storage_path / "server_key.pem"
        
        if server_cert_path.exists() and server_key_path.exists():
            print("✅ Server certificate already exists")
            print(f"   Certificate: {server_cert_path}")
            print(f"   Key: {server_key_path}")
            print()
        else:
            print("🔨 Generating server key pair...")
            server_key_pem, server_public_key_pem = generate_keypair(2048)
            
            print("🔨 Creating server CSR...")
            server_csr = generate_csr(
                private_key_pem=server_key_pem,
                common_name="veritas.local",
                organization="VERITAS Framework",
                organizational_unit="Backend API",
                country="DE",
                state="NRW",
                locality="Köln",
                email="admin@veritas.local"
            )
            
            print("🔨 Signing server certificate...")
            server_cert_info = ca_service.sign_csr(
                csr_pem=server_csr,
                validity_days=365,  # 1 year
                is_ca=False
            )
            
            # Save server certificate and key
            with open(server_cert_path, 'w') as f:
                f.write(server_cert_info['certificate_pem'])
            
            with open(server_key_path, 'wb') as f:
                f.write(server_key_pem)
            
            # Set restrictive permissions on private key (Unix-like systems)
            try:
                os.chmod(server_key_path, 0o600)
            except:
                pass  # Windows doesn't support chmod
            
            print("✅ Server certificate created successfully!")
            print(f"   Certificate: {server_cert_path}")
            print(f"   Key: {server_key_path}")
            print(f"   Common Name: veritas.local")
            print(f"   Valid Until: {server_cert_info['not_valid_after']}")
            print(f"   Serial Number: {server_cert_info['serial_number']}")
            print()
    
    except Exception as e:
        print(f"❌ Error generating server certificate: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ========================================================================
    # Step 3: Generate Client Certificate (for testing)
    # ========================================================================
    
    print("👤 Step 3: Client Certificate Generation (Test)")
    print("─" * 70)
    
    try:
        client_cert_path = ca_storage_path / "client_cert.pem"
        client_key_path = ca_storage_path / "client_key.pem"
        
        if client_cert_path.exists() and client_key_path.exists():
            print("✅ Client certificate already exists")
            print(f"   Certificate: {client_cert_path}")
            print(f"   Key: {client_key_path}")
            print()
        else:
            print("🔨 Generating client key pair...")
            client_key_pem, client_public_key_pem = generate_keypair(2048)
            
            print("🔨 Creating client CSR...")
            client_csr = generate_csr(
                private_key_pem=client_key_pem,
                common_name="veritas-client",
                organization="VERITAS Framework",
                organizational_unit="Test Client",
                country="DE",
                email="client@veritas.local"
            )
            
            print("🔨 Signing client certificate...")
            client_cert_info = ca_service.sign_csr(
                csr_pem=client_csr,
                validity_days=365,  # 1 year
                is_ca=False
            )
            
            # Save client certificate and key
            with open(client_cert_path, 'w') as f:
                f.write(client_cert_info['certificate_pem'])
            
            with open(client_key_path, 'wb') as f:
                f.write(client_key_pem)
            
            # Set restrictive permissions on private key
            try:
                os.chmod(client_key_path, 0o600)
            except:
                pass  # Windows doesn't support chmod
            
            print("✅ Client certificate created successfully!")
            print(f"   Certificate: {client_cert_path}")
            print(f"   Key: {client_key_path}")
            print(f"   Common Name: veritas-client")
            print(f"   Valid Until: {client_cert_info['not_valid_after']}")
            print(f"   Serial Number: {client_cert_info['serial_number']}")
            print()
    
    except Exception as e:
        print(f"❌ Error generating client certificate: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ========================================================================
    # Summary
    # ========================================================================
    
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                     ✅ mTLS Setup Complete!                        ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    print("📋 Generated Certificates:")
    print()
    print("🔐 Root CA:")
    print(f"   Certificate: {ca_storage_path / 'ca_certificates' / 'root_ca.pem'}")
    print(f"   Key:         {ca_storage_path / 'ca_keys' / 'root_ca_key.pem'}")
    print()
    print("🖥️  Server Certificate:")
    print(f"   Certificate: {server_cert_path}")
    print(f"   Key:         {server_key_path}")
    print()
    print("👤 Client Certificate (Test):")
    print(f"   Certificate: {client_cert_path}")
    print(f"   Key:         {client_key_path}")
    print()
    print("🚀 Next Steps:")
    print("   1. Implement SSL Context Helper (backend/pki/ssl_context.py)")
    print("   2. Create mTLS Middleware (backend/api/mtls_middleware.py)")
    print("   3. Configure FastAPI with mTLS")
    print("   4. Test with: curl --cert client_cert.pem --key client_key.pem https://localhost:5000/health")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = setup_mtls_certificates()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Certificate setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
