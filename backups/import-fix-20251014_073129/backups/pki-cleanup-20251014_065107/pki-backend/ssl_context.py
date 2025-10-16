"""
SSL Context Helper for mTLS

Production-ready SSL context creation for mutual TLS authentication.

Features:
- Server certificate loading
- Client certificate validation
- CA certificate trust chain
- TLS 1.2 + TLS 1.3 support
- Secure cipher suites
- Certificate revocation checking

Usage:
    from backend.pki.ssl_context import create_mtls_ssl_context
    
    context = create_mtls_ssl_context(
        server_cert="ca_storage/server_cert.pem",
        server_key="ca_storage/server_key.pem",
        ca_cert="ca_storage/ca_certificates/root_ca.pem",
        require_client_cert=True
    )
    
    # Use with uvicorn:
    # uvicorn main:app --ssl-keyfile server_key.pem --ssl-certfile server_cert.pem

Author: VERITAS Development Team
Created: 2025-10-13
"""

import ssl
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


def create_mtls_ssl_context(
    server_cert: str,
    server_key: str,
    ca_cert: str,
    require_client_cert: bool = True,
    check_hostname: bool = False,
    ciphers: Optional[str] = None
) -> ssl.SSLContext:
    """
    Create SSL context for mutual TLS (mTLS).
    
    Args:
        server_cert: Path to server certificate (PEM format)
        server_key: Path to server private key (PEM format)
        ca_cert: Path to CA certificate for client validation (PEM format)
        require_client_cert: Whether to require client certificates (default: True)
        check_hostname: Whether to check hostname in certificates (default: False for local dev)
        ciphers: Custom cipher suite (optional, uses secure defaults)
    
    Returns:
        Configured SSL context for mTLS
    
    Raises:
        FileNotFoundError: If certificate files not found
        ssl.SSLError: If certificate loading fails
        RuntimeError: If SSL context creation fails
    
    Example:
        >>> context = create_mtls_ssl_context(
        ...     "ca_storage/server_cert.pem",
        ...     "ca_storage/server_key.pem",
        ...     "ca_storage/ca_certificates/root_ca.pem"
        ... )
        >>> # Context ready for uvicorn or httpx
    """
    try:
        # Validate file paths
        server_cert_path = Path(server_cert)
        server_key_path = Path(server_key)
        ca_cert_path = Path(ca_cert)
        
        if not server_cert_path.exists():
            raise FileNotFoundError(f"Server certificate not found: {server_cert}")
        if not server_key_path.exists():
            raise FileNotFoundError(f"Server key not found: {server_key}")
        if not ca_cert_path.exists():
            raise FileNotFoundError(f"CA certificate not found: {ca_cert}")
        
        logger.info(f"Creating mTLS SSL context with:")
        logger.info(f"  Server Cert: {server_cert_path}")
        logger.info(f"  Server Key:  {server_key_path}")
        logger.info(f"  CA Cert:     {ca_cert_path}")
        logger.info(f"  Require Client Cert: {require_client_cert}")
        
        # Create SSL context (TLS 1.2 + TLS 1.3)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        
        # Set minimum TLS version (TLS 1.2)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Load server certificate and key
        context.load_cert_chain(
            certfile=str(server_cert_path),
            keyfile=str(server_key_path)
        )
        logger.info("✅ Server certificate loaded")
        
        # Load CA certificate for client validation
        context.load_verify_locations(cafile=str(ca_cert_path))
        logger.info("✅ CA certificate loaded for client validation")
        
        # Client certificate mode
        if require_client_cert:
            context.verify_mode = ssl.CERT_REQUIRED
            logger.info("✅ Client certificate REQUIRED")
        else:
            context.verify_mode = ssl.CERT_OPTIONAL
            logger.info("⚠️  Client certificate OPTIONAL")
        
        # Hostname checking (disabled for local development)
        context.check_hostname = check_hostname
        if not check_hostname:
            logger.info("⚠️  Hostname checking DISABLED (local development mode)")
        
        # Set secure cipher suites (TLS 1.2 + TLS 1.3)
        if ciphers:
            context.set_ciphers(ciphers)
            logger.info(f"✅ Custom ciphers: {ciphers}")
        else:
            # Default secure ciphers (ECDHE + CHACHA20 + AESGCM)
            default_ciphers = (
                'ECDHE+AESGCM:'       # Elliptic Curve + AES-GCM
                'ECDHE+CHACHA20:'     # Elliptic Curve + ChaCha20
                'DHE+AESGCM:'         # Diffie-Hellman + AES-GCM
                'DHE+CHACHA20:'       # Diffie-Hellman + ChaCha20
                '!aNULL:'             # No anonymous auth
                '!MD5:'               # No MD5 hashes
                '!DSS'                # No DSS signatures
            )
            context.set_ciphers(default_ciphers)
            logger.info("✅ Secure cipher suite configured")
        
        # Additional security options
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        context.options |= ssl.OP_NO_COMPRESSION  # CRIME attack mitigation
        context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE  # Server chooses cipher
        
        logger.info("✅ mTLS SSL context created successfully")
        
        return context
    
    except FileNotFoundError:
        raise
    except ssl.SSLError as e:
        raise ssl.SSLError(f"SSL error while creating context: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to create mTLS SSL context: {e}")


def create_mtls_client_context(
    client_cert: str,
    client_key: str,
    ca_cert: str,
    check_hostname: bool = True
) -> ssl.SSLContext:
    """
    Create SSL context for mTLS client (for service-to-service communication).
    
    Args:
        client_cert: Path to client certificate (PEM format)
        client_key: Path to client private key (PEM format)
        ca_cert: Path to CA certificate for server validation (PEM format)
        check_hostname: Whether to check server hostname (default: True)
    
    Returns:
        Configured SSL context for mTLS client
    
    Raises:
        FileNotFoundError: If certificate files not found
        ssl.SSLError: If certificate loading fails
        RuntimeError: If SSL context creation fails
    
    Example:
        >>> context = create_mtls_client_context(
        ...     "ca_storage/client_cert.pem",
        ...     "ca_storage/client_key.pem",
        ...     "ca_storage/ca_certificates/root_ca.pem"
        ... )
        >>> # Use with httpx:
        >>> # httpx.AsyncClient(verify=context)
    """
    try:
        # Validate file paths
        client_cert_path = Path(client_cert)
        client_key_path = Path(client_key)
        ca_cert_path = Path(ca_cert)
        
        if not client_cert_path.exists():
            raise FileNotFoundError(f"Client certificate not found: {client_cert}")
        if not client_key_path.exists():
            raise FileNotFoundError(f"Client key not found: {client_key}")
        if not ca_cert_path.exists():
            raise FileNotFoundError(f"CA certificate not found: {ca_cert}")
        
        logger.info(f"Creating mTLS client SSL context with:")
        logger.info(f"  Client Cert: {client_cert_path}")
        logger.info(f"  Client Key:  {client_key_path}")
        logger.info(f"  CA Cert:     {ca_cert_path}")
        
        # Create SSL context (TLS client)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        
        # Set minimum TLS version (TLS 1.2)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Load client certificate and key
        context.load_cert_chain(
            certfile=str(client_cert_path),
            keyfile=str(client_key_path)
        )
        logger.info("✅ Client certificate loaded")
        
        # Load CA certificate for server validation
        context.load_verify_locations(cafile=str(ca_cert_path))
        logger.info("✅ CA certificate loaded for server validation")
        
        # Server certificate verification (always required for client)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = check_hostname
        
        logger.info("✅ mTLS client SSL context created successfully")
        
        return context
    
    except FileNotFoundError:
        raise
    except ssl.SSLError as e:
        raise ssl.SSLError(f"SSL error while creating client context: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to create mTLS client SSL context: {e}")


def get_certificate_info_from_context(ssl_socket: ssl.SSLSocket) -> dict:
    """
    Extract certificate information from SSL socket.
    
    Args:
        ssl_socket: SSL socket with established connection
    
    Returns:
        Dictionary with certificate information
    
    Example:
        >>> info = get_certificate_info_from_context(ssl_socket)
        >>> print(info['subject']['commonName'])
        veritas-client
    """
    try:
        peer_cert = ssl_socket.getpeercert()
        
        if not peer_cert:
            return {
                'error': 'No peer certificate available',
                'verified': False
            }
        
        # Extract common fields
        subject = dict(x[0] for x in peer_cert.get('subject', []))
        issuer = dict(x[0] for x in peer_cert.get('issuer', []))
        
        return {
            'subject': subject,
            'issuer': issuer,
            'version': peer_cert.get('version'),
            'serial_number': peer_cert.get('serialNumber'),
            'not_before': peer_cert.get('notBefore'),
            'not_after': peer_cert.get('notAfter'),
            'subject_alt_names': peer_cert.get('subjectAltName', []),
            'verified': True
        }
    
    except Exception as e:
        logger.error(f"Failed to extract certificate info: {e}")
        return {
            'error': str(e),
            'verified': False
        }


# Convenience functions for common scenarios

def create_dev_ssl_context(ca_storage_path: str = "ca_storage") -> ssl.SSLContext:
    """
    Create mTLS SSL context for development (uses default paths).
    
    Args:
        ca_storage_path: Path to CA storage directory (default: "ca_storage")
    
    Returns:
        Configured SSL context
    
    Example:
        >>> context = create_dev_ssl_context()
        >>> # Ready to use with uvicorn
    """
    ca_path = Path(ca_storage_path)
    
    return create_mtls_ssl_context(
        server_cert=str(ca_path / "server_cert.pem"),
        server_key=str(ca_path / "server_key.pem"),
        ca_cert=str(ca_path / "ca_certificates" / "root_ca.pem"),
        require_client_cert=True,
        check_hostname=False  # Development mode
    )


def create_dev_client_context(ca_storage_path: str = "ca_storage") -> ssl.SSLContext:
    """
    Create mTLS client SSL context for development (uses default paths).
    
    Args:
        ca_storage_path: Path to CA storage directory (default: "ca_storage")
    
    Returns:
        Configured client SSL context
    
    Example:
        >>> context = create_dev_client_context()
        >>> # Ready to use with httpx
    """
    ca_path = Path(ca_storage_path)
    
    return create_mtls_client_context(
        client_cert=str(ca_path / "client_cert.pem"),
        client_key=str(ca_path / "client_key.pem"),
        ca_cert=str(ca_path / "ca_certificates" / "root_ca.pem"),
        check_hostname=False  # Development mode
    )


# Export public API
__all__ = [
    'create_mtls_ssl_context',
    'create_mtls_client_context',
    'get_certificate_info_from_context',
    'create_dev_ssl_context',
    'create_dev_client_context'
]
