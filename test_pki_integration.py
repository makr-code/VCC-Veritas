"""
PKI Service Integration Test

Prüft ob externer PKI-Service (C:\\VCC\\PKI) erreichbar ist und funktioniert.

Usage:
    python test_pki_integration.py

Author: VCC Development Team
Date: 2025-10-14
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.pki_client import VeritasPKIClient, get_pki_client, PKIConnectionError


# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Suppress debug logs
    format='%(levelname)s: %(message)s'
)


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_step(number: int, total: int, text: str):
    """Print step"""
    print(f"\n[{number}/{total}] {text}")


def print_success(text: str):
    """Print success message"""
    print(f"  ✅ {text}")


def print_error(text: str):
    """Print error message"""
    print(f"  ❌ {text}")


def print_info(text: str):
    """Print info message"""
    print(f"  ℹ️  {text}")


def test_pki_connection() -> bool:
    """
    Test PKI service connection and basic operations.
    
    Returns:
        True if all tests passed, False otherwise
    """
    print_header("PKI SERVICE INTEGRATION TEST")
    print_info("Testing connection to external PKI service (C:\\VCC\\PKI)")
    
    # ========================================
    # TEST 1: Connection
    # ========================================
    print_step(1, 5, "Connecting to PKI service...")
    
    try:
        client = VeritasPKIClient(
            base_url='https://localhost:8443',
            verify_ssl=False  # Development mode
        )
        print_success("PKI client created")
    except Exception as e:
        print_error(f"Failed to create PKI client: {e}")
        return False
    
    # ========================================
    # TEST 2: Health Check
    # ========================================
    print_step(2, 5, "Checking PKI service health...")
    
    try:
        health = client.health_check()
        
        if health.get('status') == 'healthy':
            print_success(f"PKI service is healthy")
        else:
            print_error(f"PKI service unhealthy: {health}")
            return False
    
    except PKIConnectionError as e:
        print_error(f"Cannot connect to PKI service: {e}")
        print_info("Make sure PKI service is running:")
        print_info("  cd C:\\VCC\\PKI")
        print_info("  python src\\pki_server.py")
        return False
    
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False
    
    # ========================================
    # TEST 3: Get CA Certificate
    # ========================================
    print_step(3, 5, "Retrieving CA certificate...")
    
    try:
        ca_cert = client.get_ca_certificate()
        
        if ca_cert and '-----BEGIN CERTIFICATE-----' in ca_cert:
            cert_size = len(ca_cert)
            print_success(f"CA certificate retrieved ({cert_size} bytes)")
            print_info(f"First 100 chars: {ca_cert[:100]}...")
        else:
            print_error("Invalid CA certificate format")
            return False
    
    except Exception as e:
        print_error(f"Failed to get CA certificate: {e}")
        return False
    
    # ========================================
    # TEST 4: Request Test Certificate
    # ========================================
    print_step(4, 5, "Requesting test certificate...")
    
    subject = {
        'CN': 'test.veritas.local',
        'O': 'VCC',
        'OU': 'VERITAS Integration Test'
    }
    
    try:
        result = client.request_certificate(
            subject=subject,
            valid_days=30,
            cert_type='client'
        )
        
        if result.get('status') == 'success':
            serial = result.get('serial_number', 'N/A')
            valid_from = result.get('valid_from', 'N/A')
            valid_to = result.get('valid_to', 'N/A')
            
            print_success("Test certificate requested successfully")
            print_info(f"Serial Number: {serial}")
            print_info(f"Valid From: {valid_from}")
            print_info(f"Valid To: {valid_to}")
            
            # Store certificate for verification test
            test_cert = result.get('certificate')
        else:
            print_error(f"Certificate request failed: {result}")
            return False
    
    except Exception as e:
        print_error(f"Certificate request failed: {e}")
        return False
    
    # ========================================
    # TEST 5: Verify Certificate
    # ========================================
    print_step(5, 5, "Verifying test certificate...")
    
    try:
        verify_result = client.verify_certificate(
            cert_pem=test_cert,
            check_revocation=False  # Don't check revocation for new cert
        )
        
        if verify_result.get('valid'):
            print_success("Test certificate is valid")
            
            details = verify_result.get('details', {})
            if details:
                print_info(f"Subject: {details.get('subject', 'N/A')}")
                print_info(f"Issuer: {details.get('issuer', 'N/A')}")
        else:
            reason = verify_result.get('reason', 'Unknown')
            print_error(f"Certificate verification failed: {reason}")
            return False
    
    except Exception as e:
        print_error(f"Certificate verification failed: {e}")
        return False
    
    # ========================================
    # BONUS TEST: Singleton Pattern
    # ========================================
    print_step("BONUS", "BONUS", "Testing singleton pattern...")
    
    try:
        singleton_client1 = get_pki_client()
        singleton_client2 = get_pki_client()
        
        if singleton_client1 is singleton_client2:
            print_success("Singleton pattern works correctly")
        else:
            print_error("Singleton pattern failed - different instances!")
            return False
    
    except Exception as e:
        print_error(f"Singleton test failed: {e}")
        return False
    
    # ========================================
    # SUCCESS
    # ========================================
    client.close()
    
    print_header("✅ ALL TESTS PASSED")
    print_info("PKI service integration is working correctly")
    print_info("External PKI service: https://localhost:8443")
    print_info("")
    print_info("Next steps:")
    print_info("  1. Update backend to use PKI client")
    print_info("  2. Remove old PKI references")
    print_info("  3. Run full test suite: pytest")
    print_info("  4. Commit changes")
    print("")
    
    return True


def test_connection_failure():
    """Test handling of connection failures (optional)"""
    print_header("BONUS: CONNECTION FAILURE TEST")
    print_info("Testing graceful failure handling...")
    
    try:
        # Try to connect to wrong port
        client = VeritasPKIClient(
            base_url='https://localhost:9999',  # Wrong port!
            verify_ssl=False
        )
        
        health = client.health_check()
        
        if health.get('status') == 'unhealthy':
            print_success("Connection failure handled gracefully")
            print_info(f"Error: {health.get('error', 'N/A')}")
            return True
        else:
            print_error("Expected connection failure but got success?!")
            return False
    
    except Exception as e:
        print_success(f"Exception caught as expected: {type(e).__name__}")
        return True


def main():
    """Main entry point"""
    print_header("VERITAS PKI SERVICE INTEGRATION TEST")
    print_info("Date: 2025-10-14")
    print_info("External PKI Service: C:\\VCC\\PKI")
    print("")
    
    # Run main tests
    success = test_pki_connection()
    
    if not success:
        print_header("❌ TESTS FAILED")
        print_error("PKI service integration is not working")
        print_info("")
        print_info("Troubleshooting:")
        print_info("  1. Check if PKI service is running:")
        print_info("     cd C:\\VCC\\PKI")
        print_info("     python src\\pki_server.py")
        print_info("")
        print_info("  2. Check if port 8443 is available:")
        print_info("     netstat -an | findstr 8443")
        print_info("")
        print_info("  3. Check PKI service logs:")
        print_info("     Get-Content C:\\VCC\\PKI\\logs\\pki-service.log -Tail 50")
        print_info("")
        print_info("  4. Check firewall settings (allow port 8443)")
        print("")
        sys.exit(1)
    
    # Optional: Test connection failure handling
    print("")
    test_connection_failure()
    
    print_header("🎉 INTEGRATION TEST COMPLETE")
    sys.exit(0)


if __name__ == '__main__':
    main()
