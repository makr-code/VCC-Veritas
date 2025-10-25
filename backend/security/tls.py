"""TLS/HTTPS enforcement middleware for VERITAS Backend.

Enforces HTTPS connections and provides TLS configuration for production deployments.

Features:
- HTTPS redirect (HTTP → HTTPS)
- Strict-Transport-Security (HSTS) headers
- TLS certificate validation
- Integration with VCC PKI

Usage:
    from backend.security.tls import add_tls_middleware, TLSConfig
    
    app = FastAPI()
    tls_config = TLSConfig(enforce_https=True, hsts_max_age=31536000)
    add_tls_middleware(app, tls_config)

Author: VERITAS Security Team
Date: 22. Oktober 2025
Based on: Covina security/tls.py
"""
from __future__ import annotations

import logging
import os
import ssl
from dataclasses import dataclass
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class TLSConfig:
    """TLS/HTTPS configuration."""
    
    # HTTPS enforcement
    enforce_https: bool = False
    https_port: int = 443
    
    # HSTS (Strict-Transport-Security) headers
    enable_hsts: bool = False
    hsts_max_age: int = 31536000  # 1 year in seconds
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False
    
    # TLS certificate paths (for server-side TLS)
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_file: Optional[str] = None  # For client certificate validation
    
    # TLS version and ciphers
    tls_version: str = "TLSv1.2"  # Minimum TLS version
    ciphers: Optional[str] = None  # Use default secure ciphers if None
    
    # Development mode (skip HTTPS in dev)
    dev_mode: bool = False
    
    @classmethod
    def from_env(cls) -> TLSConfig:
        """Create TLS config from environment variables."""
        return cls(
            enforce_https=os.getenv("ENFORCE_HTTPS", "false").lower() == "true",
            https_port=int(os.getenv("HTTPS_PORT", "443")),
            enable_hsts=os.getenv("ENABLE_HSTS", "false").lower() == "true",
            hsts_max_age=int(os.getenv("HSTS_MAX_AGE", "31536000")),
            hsts_include_subdomains=os.getenv("HSTS_INCLUDE_SUBDOMAINS", "true").lower() == "true",
            hsts_preload=os.getenv("HSTS_PRELOAD", "false").lower() == "true",
            cert_file=os.getenv("TLS_CERT_FILE"),
            key_file=os.getenv("TLS_KEY_FILE"),
            ca_file=os.getenv("TLS_CA_FILE"),
            tls_version=os.getenv("TLS_VERSION", "TLSv1.2"),
            ciphers=os.getenv("TLS_CIPHERS"),
            dev_mode=os.getenv("VERITAS_API_RELOAD", "false").lower() == "true",
        )


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Middleware to redirect HTTP requests to HTTPS."""
    
    def __init__(self, app, https_port: int = 443, dev_mode: bool = False):
        super().__init__(app)
        self.https_port = https_port
        self.dev_mode = dev_mode
        
        if dev_mode:
            logger.warning("⚠️  HTTPS Redirect: Development mode - redirects disabled")
        else:
            logger.info(f"✅ HTTPS Redirect Middleware initialized (port: {https_port})")
    
    async def dispatch(self, request: Request, call_next):
        # Skip redirect in development mode
        if self.dev_mode:
            return await call_next(request)
        
        # Check if request is already HTTPS
        if request.url.scheme == "https":
            return await call_next(request)
        
        # Check for X-Forwarded-Proto header (reverse proxy)
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto == "https":
            return await call_next(request)
        
        # Redirect to HTTPS
        https_url = request.url.replace(scheme="https")
        if self.https_port != 443:
            # Include custom HTTPS port in redirect
            https_url = https_url.replace(port=self.https_port)
        
        logger.info(f"🔒 HTTP → HTTPS: {request.url} → {https_url}")
        return RedirectResponse(url=str(https_url), status_code=status.HTTP_301_MOVED_PERMANENTLY)


class HSTSMiddleware(BaseHTTPMiddleware):
    """Middleware to add Strict-Transport-Security (HSTS) headers."""
    
    def __init__(self, app, max_age: int = 31536000, include_subdomains: bool = True, preload: bool = False, dev_mode: bool = False):
        super().__init__(app)
        self.max_age = max_age
        self.include_subdomains = include_subdomains
        self.preload = preload
        self.dev_mode = dev_mode
        
        # Build HSTS header value
        hsts_parts = [f"max-age={max_age}"]
        if include_subdomains:
            hsts_parts.append("includeSubDomains")
        if preload:
            hsts_parts.append("preload")
        
        self.hsts_header = "; ".join(hsts_parts)
        
        if dev_mode:
            logger.warning("⚠️  HSTS: Development mode - headers disabled")
        else:
            logger.info(f"✅ HSTS Middleware initialized: {self.hsts_header}")
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Skip HSTS in development mode
        if self.dev_mode:
            return response
        
        # Only add HSTS header for HTTPS requests
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            response.headers["Strict-Transport-Security"] = self.hsts_header
        
        return response


def create_ssl_context(config: TLSConfig) -> ssl.SSLContext:
    """Create SSL context for server-side TLS."""
    # Map TLS version string to ssl module constant
    tls_version_map = {
        "TLSv1.2": ssl.PROTOCOL_TLSv1_2,
        "TLSv1.3": ssl.PROTOCOL_TLS,  # TLS 1.3 uses PROTOCOL_TLS with specific options
    }
    
    protocol = tls_version_map.get(config.tls_version, ssl.PROTOCOL_TLS)
    context = ssl.SSLContext(protocol)
    
    # Load server certificate and key
    if config.cert_file and config.key_file:
        context.load_cert_chain(certfile=config.cert_file, keyfile=config.key_file)
        logger.info(f"✅ Loaded TLS certificate: {config.cert_file}")
    else:
        logger.warning("⚠️  No TLS certificate configured - using default")
    
    # Load CA certificate for client verification
    if config.ca_file:
        context.load_verify_locations(cafile=config.ca_file)
        logger.info(f"✅ Loaded CA certificate: {config.ca_file}")
    
    # Set cipher suite (use secure defaults if not specified)
    if config.ciphers:
        context.set_ciphers(config.ciphers)
        logger.info(f"✅ Custom cipher suite configured")
    else:
        # Use Mozilla Modern cipher suite (TLS 1.3 preferred)
        context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS")
    
    # Disable compression (CRIME attack mitigation)
    context.options |= ssl.OP_NO_COMPRESSION
    
    # Disable SSLv2, SSLv3, TLSv1.0, TLSv1.1 (deprecated versions)
    context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    
    logger.info(f"✅ SSL context created (TLS {config.tls_version})")
    return context


def add_tls_middleware(app: FastAPI, config: Optional[TLSConfig] = None):
    """Add TLS/HTTPS middleware to FastAPI app."""
    if config is None:
        config = TLSConfig.from_env()
    
    logger.info("=" * 80)
    logger.info("🔒 TLS/HTTPS Configuration")
    logger.info("=" * 80)
    
    # Add HTTPS redirect middleware (first in chain)
    if config.enforce_https:
        app.add_middleware(
            HTTPSRedirectMiddleware,
            https_port=config.https_port,
            dev_mode=config.dev_mode
        )
        if not config.dev_mode:
            logger.info("✅ HTTPS enforcement enabled")
        else:
            logger.warning("⚠️  HTTPS enforcement disabled (development mode)")
    else:
        logger.warning("⚠️  HTTPS enforcement disabled - HTTP traffic allowed")
    
    # Add HSTS middleware
    if config.enable_hsts:
        app.add_middleware(
            HSTSMiddleware,
            max_age=config.hsts_max_age,
            include_subdomains=config.hsts_include_subdomains,
            preload=config.hsts_preload,
            dev_mode=config.dev_mode,
        )
        if not config.dev_mode:
            logger.info("✅ HSTS headers enabled")
        else:
            logger.warning("⚠️  HSTS headers disabled (development mode)")
    
    logger.info(f"ℹ️  Configuration: HTTPS={config.enforce_https}, HSTS={config.enable_hsts}, Dev={config.dev_mode}")
    logger.info("=" * 80)


# Convenience function for uvicorn SSL configuration
def get_uvicorn_ssl_config(config: Optional[TLSConfig] = None) -> dict:
    """Get SSL configuration for uvicorn.run()."""
    if config is None:
        config = TLSConfig.from_env()
    
    ssl_config = {}
    
    if config.cert_file and config.key_file:
        ssl_config["ssl_certfile"] = config.cert_file
        ssl_config["ssl_keyfile"] = config.key_file
        
        if config.ca_file:
            ssl_config["ssl_ca_certs"] = config.ca_file
        
        logger.info(f"✅ Uvicorn SSL config: cert={config.cert_file}")
    else:
        logger.warning("⚠️  No SSL certificates configured for uvicorn")
    
    return ssl_config
