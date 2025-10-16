"""
VCC PKI Service Client für VERITAS

Integriert externen PKI-Service (C:\\VCC\\PKI) als zentrale Certificate Authority.

Features:
- Certificate Request/Issuance
- Certificate Verification
- Certificate Revocation
- SSL Context Creation (mit externen Zertifikaten)

Author: VCC Development Team
Date: 2025-10-14
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Optional, List
import ssl
import json
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class PKIServiceError(Exception):
    """Base exception for PKI service errors"""
    pass


class PKIConnectionError(PKIServiceError):
    """PKI service connection error"""
    pass


class PKICertificateError(PKIServiceError):
    """Certificate-related error"""
    pass


class VeritasPKIClient:
    """
    Client für VCC PKI-Service.
    
    Stellt Verbindung zum externen PKI-Service her und
    bietet Certificate Management Funktionen.
    
    Example:
        >>> client = VeritasPKIClient()
        >>> subject = {'CN': 'api.veritas.local', 'O': 'VCC'}
        >>> cert = client.request_certificate(subject)
        >>> print(cert['status'])
        'success'
    """
    
    def __init__(
        self,
        base_url: str = 'https://localhost:8443',
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        ca_cert_path: Optional[str] = None,
        verify_ssl: bool = True
    ):
        """
        Initialize PKI client.
        
        Args:
            base_url: PKI service URL (default: https://localhost:8443)
            cert_path: Path to client certificate (optional)
            key_path: Path to client private key (optional)
            ca_cert_path: Path to CA certificate for verification (optional)
            verify_ssl: Verify SSL certificates (default: True)
        """
        self.base_url = base_url.rstrip('/')
        self.verify_ssl = verify_ssl
        
        # Auto-detect service certificates if not provided
        pki_root = Path('C:/VCC/PKI')
        service_certs = pki_root / 'service_certificates'
        
        if not cert_path:
            cert_path = service_certs / 'veritas_client.pem'
            if not cert_path.exists():
                logger.warning(f"Client certificate not found: {cert_path}")
                cert_path = None
        
        if not key_path and cert_path:
            key_path = service_certs / 'veritas_client_key.pem'
            if not key_path.exists():
                logger.warning(f"Client key not found: {key_path}")
                key_path = None
        
        if not ca_cert_path:
            ca_cert_path = pki_root / 'ca_storage' / 'ca_certificates' / 'root_ca.pem'
            if not ca_cert_path.exists():
                logger.warning(f"CA certificate not found: {ca_cert_path}")
                ca_cert_path = None
        
        self.cert_path = str(cert_path) if cert_path else None
        self.key_path = str(key_path) if key_path else None
        self.ca_cert_path = str(ca_cert_path) if ca_cert_path else None
        
        # Session for connection pooling
        self.session = requests.Session()
        
        # Configure client certificate
        if self.cert_path and self.key_path:
            self.session.cert = (self.cert_path, self.key_path)
        
        # Configure CA verification
        if self.ca_cert_path and self.verify_ssl:
            self.session.verify = self.ca_cert_path
        elif not self.verify_ssl:
            self.session.verify = False
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        logger.info(f"PKI Client initialized: {self.base_url}")
        logger.debug(f"  Client cert: {self.cert_path}")
        logger.debug(f"  CA cert: {self.ca_cert_path}")
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make HTTP request to PKI service.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/api/v1/certificates/request')
            data: Request body (JSON)
            params: Query parameters
        
        Returns:
            Response JSON
        
        Raises:
            PKIConnectionError: Connection failed
            PKIServiceError: Service error
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"PKI service connection failed: {e}")
            raise PKIConnectionError(f"Cannot connect to PKI service at {url}")
        
        except requests.exceptions.Timeout as e:
            logger.error(f"PKI service timeout: {e}")
            raise PKIConnectionError(f"PKI service timeout: {url}")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"PKI service HTTP error: {e}")
            try:
                error_detail = response.json().get('detail', str(e))
            except:
                error_detail = str(e)
            raise PKIServiceError(f"PKI service error: {error_detail}")
        
        except Exception as e:
            logger.error(f"Unexpected PKI error: {e}")
            raise PKIServiceError(f"Unexpected error: {e}")
    
    def health_check(self) -> Dict:
        """
        Check PKI service health.
        
        Returns:
            Health status dict
        
        Example:
            >>> client = VeritasPKIClient()
            >>> health = client.health_check()
            >>> print(health['status'])
            'healthy'
        """
        try:
            return self._request('GET', '/health')
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}
    
    def request_certificate(
        self,
        subject: Dict[str, str],
        key_size: int = 2048,
        valid_days: int = 365,
        cert_type: str = 'server'
    ) -> Dict:
        """
        Request certificate from PKI service.
        
        Args:
            subject: Certificate subject (CN, O, OU, etc.)
            key_size: RSA key size (default: 2048)
            valid_days: Certificate validity in days (default: 365)
            cert_type: Certificate type ('server', 'client', 'intermediate')
        
        Returns:
            Certificate data dict with keys:
                - status: 'success' or 'error'
                - certificate: PEM-encoded certificate
                - private_key: PEM-encoded private key (if generated)
                - serial_number: Certificate serial number
                - valid_from: Start date (ISO format)
                - valid_to: End date (ISO format)
        
        Example:
            >>> client = VeritasPKIClient()
            >>> subject = {'CN': 'api.veritas.local', 'O': 'VCC', 'OU': 'VERITAS'}
            >>> result = client.request_certificate(subject)
            >>> print(result['certificate'])
            '-----BEGIN CERTIFICATE-----\n...'
        """
        data = {
            'subject': subject,
            'key_size': key_size,
            'valid_days': valid_days,
            'cert_type': cert_type,
            'requester': 'veritas'
        }
        
        try:
            result = self._request('POST', '/api/v1/certificates/request', data=data)
            logger.info(f"Certificate requested: {subject.get('CN')}")
            return result
        except Exception as e:
            logger.error(f"Certificate request failed: {e}")
            raise PKICertificateError(f"Certificate request failed: {e}")
    
    def verify_certificate(
        self,
        cert_pem: str,
        check_revocation: bool = True
    ) -> Dict:
        """
        Verify certificate signature and validity.
        
        Args:
            cert_pem: Certificate in PEM format
            check_revocation: Check if certificate is revoked (default: True)
        
        Returns:
            Verification result dict:
                - valid: True/False
                - reason: Reason for invalidity (if valid=False)
                - details: Additional details
        
        Example:
            >>> cert_pem = "-----BEGIN CERTIFICATE-----\n..."
            >>> result = client.verify_certificate(cert_pem)
            >>> print(result['valid'])
            True
        """
        data = {
            'certificate': cert_pem,
            'check_revocation': check_revocation
        }
        
        try:
            result = self._request('POST', '/api/v1/certificates/verify', data=data)
            return result
        except Exception as e:
            logger.error(f"Certificate verification failed: {e}")
            return {
                'valid': False,
                'reason': f'Verification error: {e}',
                'details': {}
            }
    
    def revoke_certificate(
        self,
        serial_number: str,
        reason: str = 'unspecified'
    ) -> Dict:
        """
        Revoke certificate.
        
        Args:
            serial_number: Certificate serial number (hex string)
            reason: Revocation reason (e.g., 'key_compromise', 'superseded')
        
        Returns:
            Revocation result dict
        
        Example:
            >>> result = client.revoke_certificate('0A1B2C3D', 'key_compromise')
            >>> print(result['status'])
            'revoked'
        """
        data = {
            'serial_number': serial_number,
            'reason': reason,
            'requester': 'veritas'
        }
        
        try:
            result = self._request('POST', '/api/v1/certificates/revoke', data=data)
            logger.info(f"Certificate revoked: {serial_number} (reason: {reason})")
            return result
        except Exception as e:
            logger.error(f"Certificate revocation failed: {e}")
            raise PKICertificateError(f"Certificate revocation failed: {e}")
    
    def get_ca_certificate(self) -> str:
        """
        Get Root CA certificate (PEM format).
        
        Returns:
            CA certificate PEM string
        
        Example:
            >>> ca_cert = client.get_ca_certificate()
            >>> print(ca_cert[:50])
            '-----BEGIN CERTIFICATE-----\nMIIDXTCCAkWgAwIBAgI...'
        """
        try:
            result = self._request('GET', '/api/v1/ca/certificate')
            return result['certificate']
        except Exception as e:
            logger.error(f"Failed to get CA certificate: {e}")
            raise PKICertificateError(f"Failed to get CA certificate: {e}")
    
    def list_certificates(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        List certificates issued by PKI service.
        
        Args:
            status: Filter by status ('valid', 'revoked', 'expired')
            limit: Maximum number of results
        
        Returns:
            List of certificate metadata dicts
        
        Example:
            >>> certs = client.list_certificates(status='valid')
            >>> for cert in certs:
            ...     print(cert['subject']['CN'])
        """
        params = {'limit': limit}
        if status:
            params['status'] = status
        
        try:
            result = self._request('GET', '/api/v1/certificates', params=params)
            return result.get('certificates', [])
        except Exception as e:
            logger.error(f"Failed to list certificates: {e}")
            return []
    
    def create_ssl_context(
        self,
        purpose: ssl.Purpose = ssl.Purpose.SERVER_AUTH
    ) -> ssl.SSLContext:
        """
        Create SSL context with PKI service certificates.
        
        Args:
            purpose: SSL purpose (SERVER_AUTH or CLIENT_AUTH)
        
        Returns:
            Configured SSLContext
        
        Example:
            >>> client = VeritasPKIClient()
            >>> ssl_ctx = client.create_ssl_context()
            >>> # Use with HTTPS server/client
        """
        context = ssl.create_default_context(purpose)
        
        # Load CA certificate from PKI service
        try:
            if self.ca_cert_path and Path(self.ca_cert_path).exists():
                context.load_verify_locations(self.ca_cert_path)
            else:
                # Fetch CA cert from service
                ca_cert = self.get_ca_certificate()
                ca_cert_path = Path('temp_ca.pem')
                ca_cert_path.write_text(ca_cert)
                context.load_verify_locations(str(ca_cert_path))
                ca_cert_path.unlink()  # Clean up
        except Exception as e:
            logger.warning(f"Failed to load CA certificate: {e}")
        
        # Load client certificate if available
        if self.cert_path and self.key_path:
            if Path(self.cert_path).exists() and Path(self.key_path).exists():
                try:
                    context.load_cert_chain(
                        certfile=self.cert_path,
                        keyfile=self.key_path
                    )
                except Exception as e:
                    logger.warning(f"Failed to load client certificate: {e}")
        
        return context
    
    def close(self):
        """Close HTTP session."""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# ==================== Singleton Pattern ====================

_pki_client: Optional[VeritasPKIClient] = None


def get_pki_client(
    base_url: Optional[str] = None,
    **kwargs
) -> VeritasPKIClient:
    """
    Get or create PKI client singleton.
    
    Args:
        base_url: Override default PKI service URL
        **kwargs: Additional arguments for VeritasPKIClient
    
    Returns:
        VeritasPKIClient instance
    
    Example:
        >>> from backend.services.pki_client import get_pki_client
        >>> pki = get_pki_client()
        >>> cert = pki.request_certificate({'CN': 'test.local'})
    """
    global _pki_client
    
    if _pki_client is None:
        if base_url:
            kwargs['base_url'] = base_url
        _pki_client = VeritasPKIClient(**kwargs)
    
    return _pki_client


def reset_pki_client():
    """Reset PKI client singleton (for testing)."""
    global _pki_client
    if _pki_client:
        _pki_client.close()
    _pki_client = None


# ==================== Example Usage ====================

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create client
    with VeritasPKIClient() as client:
        # Health check
        print("=" * 60)
        print("PKI SERVICE HEALTH CHECK")
        print("=" * 60)
        
        health = client.health_check()
        print(f"Status: {health.get('status')}")
        print()
        
        # Get CA certificate
        print("=" * 60)
        print("CA CERTIFICATE")
        print("=" * 60)
        
        try:
            ca_cert = client.get_ca_certificate()
            print(f"CA Certificate: {ca_cert[:100]}...")
        except Exception as e:
            print(f"Error: {e}")
        print()
        
        # Request certificate
        print("=" * 60)
        print("CERTIFICATE REQUEST")
        print("=" * 60)
        
        subject = {
            'CN': 'test.veritas.local',
            'O': 'VCC',
            'OU': 'VERITAS Testing'
        }
        
        try:
            result = client.request_certificate(subject)
            print(f"Status: {result.get('status')}")
            print(f"Serial: {result.get('serial_number')}")
            print(f"Valid: {result.get('valid_from')} → {result.get('valid_to')}")
        except Exception as e:
            print(f"Error: {e}")
        print()
        
        print("=" * 60)
        print("EXAMPLE COMPLETE")
        print("=" * 60)
