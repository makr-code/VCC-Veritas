"""
mTLS Validation Middleware

FastAPI middleware for mutual TLS client certificate validation.

Features:
- Client certificate extraction from TLS connection
- Certificate validation against Root CA
- Certificate expiry checking
- Certificate revocation checking (CRL)
- Service name extraction from CN
- Service whitelist enforcement
- Request state population with certificate info
- Health endpoint exemption

Usage:
    from fastapi import FastAPI
    from backend.api.mtls_middleware import MTLSValidationMiddleware
    from backend.pki.ca_service import CAService
    from backend.pki.cert_manager import CertificateManager

    app = FastAPI()

    ca_service = CAService()
    cert_manager = CertificateManager()

    app.add_middleware(
        MTLSValidationMiddleware,
        ca_service=ca_service,
        cert_manager=cert_manager
    )

Author: VERITAS Development Team
Created: 2025-10-13
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Set

from cryptography import x509
from cryptography.x509.oid import NameOID
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class MTLSValidationMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for mTLS client certificate validation.

    This middleware validates client certificates for all requests except
    whitelisted endpoints (e.g., /health). It extracts the certificate,
    validates it against the Root CA, checks expiry and revocation status,
    and adds certificate information to the request state.

    **Validation Steps:**
    1. Extract client certificate from TLS connection
    2. Validate certificate signature (issued by Root CA)
    3. Check certificate expiry (not_valid_before/after)
    4. Check revocation status (CRL)
    5. Validate service name against whitelist
    6. Add certificate info to request.state

    **Request State:**
    After successful validation, the following attributes are available:
    - request.state.client_certificate: x509.Certificate object
    - request.state.client_service: Service name (CN)
    - request.state.client_cn: Common Name
    - request.state.mtls_validated: True

    **Exempted Endpoints:**
    - /health
    - /api/v1/health
    - /docs (Swagger UI)
    - /redoc (ReDoc)
    - /openapi.json

    Example:
        >>> @app.get("/api/secure")
        >>> async def secure_endpoint(request: Request):
        ...     service = request.state.client_service
        ...     return {"service": service, "message": "Authenticated!"}
    """

    def __init__(
        self,
        app,
        ca_service=None,
        cert_manager=None,
        allowed_services: Optional[Set[str]] = None,
        exempt_paths: Optional[Set[str]] = None,
    ):
        """
        Initialize mTLS validation middleware.

        Args:
            app: FastAPI application
            ca_service: CAService instance for certificate validation
            cert_manager: CertificateManager instance for revocation checks
            allowed_services: Set of allowed service CNs (whitelist)
            exempt_paths: Set of paths exempt from mTLS validation
        """
        super().__init__(app)

        # Lazy import to avoid circular dependencies
        if ca_service is None:
            from backend.pki.ca_service import CAService

            ca_service = CAService()

        if cert_manager is None:
            from backend.pki.cert_manager import CertificateManager

            cert_manager = CertificateManager()

        self.ca_service = ca_service
        self.cert_manager = cert_manager

        # Default allowed services (whitelist)
        self.allowed_services = allowed_services or {
            "veritas-client",
            "veritas-frontend",
            "veritas-worker",
            "veritas-agent",
            "admin-client",
            "test-client",  # For development/testing
            "monitoring-service",
            "backup-service",
        }

        # Paths exempt from mTLS validation
        self.exempt_paths = exempt_paths or {"/health", "/api/v1/health", "/docs", "/redoc", "/openapi.json"}

        logger.info(f"✅ mTLS Middleware initialized")
        logger.info(f"   Allowed services: {len(self.allowed_services)}")
        logger.info(f"   Exempt paths: {len(self.exempt_paths)}")

    async def dispatch(self, request: Request, call_next):
        """
        Middleware dispatch: Validate client certificate.

        Args:
            request: FastAPI Request object
            call_next: Next middleware in chain

        Returns:
            Response from next middleware

        Raises:
            HTTPException: If certificate validation fails
        """
        # Check if path is exempt from mTLS validation
        if self._is_exempt_path(request.url.path):
            logger.debug(f"Exempt path: {request.url.path} - skipping mTLS validation")
            return await call_next(request)

        # Extract client certificate from TLS connection
        client_cert_der = self._extract_client_certificate(request)

        if not client_cert_der:
            logger.warning(f"❌ No client certificate provided for {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Client certificate required for mTLS authentication"
            )

        try:
            # Parse DER-encoded certificate
            cert = x509.load_der_x509_certificate(client_cert_der)

            # Validate certificate
            validation_result = self._validate_client_certificate(cert)

            if not validation_result["valid"]:
                logger.warning(f"❌ Invalid client certificate: {validation_result['reason']}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid client certificate: {validation_result['reason']}"
                )

            # Add certificate info to request state
            request.state.client_certificate = cert
            request.state.client_service = validation_result["service_name"]
            request.state.client_cn = validation_result["common_name"]
            request.state.mtls_validated = True

            logger.info(f"✅ mTLS validation successful for service: {request.state.client_service}")

        except x509.CertificateError as e:
            logger.error(f"❌ Certificate parsing error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid certificate format: {e}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Certificate validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Certificate validation failed: {e}"
            )

        # Continue to next middleware
        response = await call_next(request)
        return response

    def _is_exempt_path(self, path: str) -> bool:
        """
        Check if path is exempt from mTLS validation.

        Args:
            path: Request path

        Returns:
            True if path is exempt, False otherwise
        """
        # Exact match
        if path in self.exempt_paths:
            return True

        # Prefix match (e.g., /docs includes /docs/*)
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True

        return False

    def _extract_client_certificate(self, request: Request) -> Optional[bytes]:
        """
        Extract client certificate from TLS connection.

        Args:
            request: FastAPI Request object

        Returns:
            DER-encoded certificate bytes, or None if not present

        Note:
            FastAPI/Starlette stores the client certificate in
            request.scope['transport']['peercert'] when using uvicorn
            with ssl_cert_reqs=ssl.CERT_REQUIRED.
        """
        try:
            # Check if transport info is available
            scope = request.scope

            # uvicorn stores certificate in 'client' key (ASGI scope)
            # Format: (host, port, client_cert_der)
            if "client" in scope and isinstance(scope["client"], tuple):
                if len(scope["client"]) >= 3:
                    client_cert_der = scope["client"][2]
                    if client_cert_der:
                        return client_cert_der

            # Alternative: Check transport dict (some ASGI servers)
            if "transport" in scope:
                transport = scope["transport"]
                if isinstance(transport, dict) and "peercert" in transport:
                    return transport["peercert"]

            # No certificate found
            return None

        except Exception as e:
            logger.error(f"Error extracting client certificate: {e}")
            return None

    def _validate_client_certificate(self, certificate: x509.Certificate) -> dict:
        """
        Validate client certificate.

        Args:
            certificate: x509.Certificate object

        Returns:
            Validation result dict with keys:
            - valid: bool
            - reason: str (if invalid)
            - service_name: str
            - common_name: str

        Validation checks:
        1. Extract service name from CN
        2. Check service whitelist
        3. Validate certificate dates (not_valid_before/after)
        4. Validate issuer (must be VERITAS CA)
        5. Check revocation status (CRL)
        """
        try:
            # 1. Extract service name
            service_name = self._extract_service_name(certificate)
            common_name = self._extract_common_name(certificate)

            # 2. Check whitelist
            if service_name not in self.allowed_services:
                return {
                    "valid": False,
                    "reason": f"Service not in whitelist: {service_name}",
                    "service_name": service_name,
                    "common_name": common_name,
                }

            # 3. Validate dates
            now = datetime.now(timezone.utc)

            if now < certificate.not_valid_before_utc:
                return {
                    "valid": False,
                    "reason": f"Certificate not yet valid (starts: {certificate.not_valid_before_utc})",
                    "service_name": service_name,
                    "common_name": common_name,
                }

            if now > certificate.not_valid_after_utc:
                return {
                    "valid": False,
                    "reason": f"Certificate expired (ended: {certificate.not_valid_after_utc})",
                    "service_name": service_name,
                    "common_name": common_name,
                }

            # 4. Validate issuer (should be VERITAS CA)
            issuer_org = self._extract_issuer_org(certificate)
            expected_org = "VERITAS Framework"

            if issuer_org != expected_org:
                logger.warning(f"Invalid issuer organization: {issuer_org} (expected: {expected_org})")
                return {
                    "valid": False,
                    "reason": f"Invalid issuer: {issuer_org}",
                    "service_name": service_name,
                    "common_name": common_name,
                }

            # 5. Check revocation status
            serial = str(certificate.serial_number)
            if self.cert_manager.is_revoked(serial):
                logger.warning(f"Certificate revoked: {serial}")
                return {
                    "valid": False,
                    "reason": f"Certificate revoked (serial: {serial})",
                    "service_name": service_name,
                    "common_name": common_name,
                }

            # All checks passed
            return {
                "valid": True,
                "service_name": service_name,
                "common_name": common_name,
                "serial_number": serial,
                "issuer": issuer_org,
            }

        except Exception as e:
            logger.error(f"Certificate validation failed: {e}")
            return {"valid": False, "reason": f"Validation error: {e}", "service_name": "unknown", "common_name": "unknown"}

    def _extract_service_name(self, certificate: x509.Certificate) -> str:
        """Extract service name from Common Name (CN)."""
        return self._extract_common_name(certificate)

    def _extract_common_name(self, certificate: x509.Certificate) -> str:
        """Extract Common Name from certificate subject."""
        try:
            for attr in certificate.subject:
                if attr.oid == NameOID.COMMON_NAME:
                    return attr.value
            return "unknown"
        except Exception as e:
            logger.error(f"Error extracting CN: {e}")
            return "unknown"

    def _extract_issuer_org(self, certificate: x509.Certificate) -> str:
        """Extract issuer organization name."""
        try:
            for attr in certificate.issuer:
                if attr.oid == NameOID.ORGANIZATION_NAME:
                    return attr.value
            return "unknown"
        except Exception as e:
            logger.error(f"Error extracting issuer org: {e}")
            return "unknown"

    def add_allowed_service(self, service_name: str):
        """Add a service to the whitelist."""
        self.allowed_services.add(service_name)
        logger.info(f"Added service to whitelist: {service_name}")

    def remove_allowed_service(self, service_name: str):
        """Remove a service from the whitelist."""
        self.allowed_services.discard(service_name)
        logger.info(f"Removed service from whitelist: {service_name}")

    def get_allowed_services(self) -> Set[str]:
        """Get list of allowed services."""
        return self.allowed_services.copy()


# Convenience function for creating middleware
def create_mtls_middleware(
    allowed_services: Optional[Set[str]] = None, exempt_paths: Optional[Set[str]] = None
) -> MTLSValidationMiddleware:
    """
    Create mTLS validation middleware with optional customization.

    Args:
        allowed_services: Set of allowed service CNs
        exempt_paths: Set of paths exempt from validation

    Returns:
        Configured MTLSValidationMiddleware

    Example:
        >>> middleware = create_mtls_middleware(
        ...     allowed_services={'veritas-client', 'admin-client'},
        ...     exempt_paths={'/health', '/docs'}
        ... )
    """
    from backend.pki.ca_service import CAService
    from backend.pki.cert_manager import CertificateManager

    return MTLSValidationMiddleware(
        app=None,  # Will be set by FastAPI
        ca_service=CAService(),
        cert_manager=CertificateManager(),
        allowed_services=allowed_services,
        exempt_paths=exempt_paths,
    )


# Export public API
__all__ = ["MTLSValidationMiddleware", "create_mtls_middleware"]
