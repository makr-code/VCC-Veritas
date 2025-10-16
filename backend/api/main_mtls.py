#!/usr/bin/env python3
"""
VERITAS mTLS-enabled FastAPI Backend

Production-ready FastAPI application with mutual TLS authentication.

Features:
- mTLS client certificate validation
- Certificate-based authentication
- Service-to-service secure communication
- Health check endpoint (no mTLS)
- Test endpoints for validation
- Comprehensive logging

Usage:
    # Development (with auto-generated certificates)
    python backend/api/main_mtls.py
    
    # Production (with custom certificates)
    uvicorn backend.api.main_mtls:app \
        --host 0.0.0.0 \
        --port 5000 \
        --ssl-keyfile ca_storage/server_key.pem \
        --ssl-certfile ca_storage/server_cert.pem \
        --ssl-ca-certs ca_storage/ca_certificates/root_ca.pem \
        --ssl-cert-reqs 2

Testing:
    # With client certificate (success)
    curl --cert ca_storage/client_cert.pem \
         --key ca_storage/client_key.pem \
         --cacert ca_storage/ca_certificates/root_ca.pem \
         https://localhost:5000/health
    
    # Without certificate (failure)
    curl https://localhost:5000/health

Author: VERITAS Development Team
Created: 2025-10-13
"""

import sys
import os
from pathlib import Path
import logging
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'backend'))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.api.mtls_middleware import MTLSValidationMiddleware
from backend.pki.ca_service import CAService
from backend.pki.cert_manager import CertificateManager
from backend.pki.ssl_context import create_dev_ssl_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="VERITAS Framework API (mTLS)",
    description="Production-ready API with mutual TLS authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware (optional, for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PKI services
try:
    ca_service = CAService()
    cert_manager = CertificateManager()
    logger.info("✅ PKI services initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize PKI services: {e}")
    ca_service = None
    cert_manager = None

# Add mTLS validation middleware
if ca_service and cert_manager:
    app.add_middleware(
        MTLSValidationMiddleware,
        ca_service=ca_service,
        cert_manager=cert_manager
    )
    logger.info("✅ mTLS middleware added")
else:
    logger.warning("⚠️  Running without mTLS middleware (PKI services not available)")


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with detailed logging."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": request.url.path
        }
    )


# ============================================================================
# Health Check Endpoint (No mTLS)
# ============================================================================

@app.get("/health", tags=["Monitoring"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint (exempt from mTLS).
    
    Returns:
        Health status dict
    
    Example:
        >>> curl https://localhost:5000/health
        {"status": "healthy", "mtls": "enabled", "service": "VERITAS API"}
    """
    return {
        "status": "healthy",
        "mtls": "enabled" if ca_service else "disabled",
        "service": "VERITAS API",
        "version": "1.0.0"
    }


@app.get("/api/v1/health", tags=["Monitoring"])
async def health_check_v1() -> Dict[str, Any]:
    """Alternative health check endpoint."""
    return await health_check()


# ============================================================================
# Test Endpoints (mTLS Required)
# ============================================================================

@app.get("/", tags=["Info"])
async def root(request: Request) -> Dict[str, Any]:
    """
    Root endpoint - shows mTLS status.
    
    Requires mTLS authentication.
    
    Returns:
        API info dict with client certificate details
    """
    mtls_info = {}
    
    if hasattr(request.state, 'mtls_validated') and request.state.mtls_validated:
        mtls_info = {
            "authenticated": True,
            "client_service": request.state.client_service,
            "client_cn": request.state.client_cn
        }
    else:
        mtls_info = {
            "authenticated": False,
            "message": "mTLS validation bypassed or failed"
        }
    
    return {
        "service": "VERITAS Framework API",
        "version": "1.0.0",
        "mtls": "enabled",
        "authentication": mtls_info
    }


@app.get("/api/v1/test", tags=["Testing"])
async def test_endpoint(request: Request) -> Dict[str, Any]:
    """
    Test endpoint to verify mTLS authentication.
    
    Requires valid client certificate.
    
    Returns:
        Test response with client certificate details
    
    Example:
        >>> curl --cert client_cert.pem --key client_key.pem \
        ...      --cacert root_ca.pem https://localhost:5000/api/v1/test
        {
            "message": "mTLS authentication successful",
            "client": {
                "service": "veritas-client",
                "cn": "veritas-client",
                "authenticated": true
            }
        }
    """
    if not hasattr(request.state, 'mtls_validated'):
        raise HTTPException(
            status_code=401,
            detail="mTLS authentication required"
        )
    
    return {
        "message": "mTLS authentication successful",
        "client": {
            "service": request.state.client_service,
            "cn": request.state.client_cn,
            "authenticated": request.state.mtls_validated
        },
        "endpoint": "/api/v1/test"
    }


@app.get("/api/v1/certificate-info", tags=["Certificate"])
async def certificate_info(request: Request) -> Dict[str, Any]:
    """
    Get detailed client certificate information.
    
    Requires valid client certificate.
    
    Returns:
        Detailed certificate info
    """
    if not hasattr(request.state, 'client_certificate'):
        raise HTTPException(
            status_code=401,
            detail="mTLS authentication required"
        )
    
    cert = request.state.client_certificate
    
    return {
        "subject": {
            "common_name": request.state.client_cn,
            "full_dn": cert.subject.rfc4514_string()
        },
        "issuer": {
            "full_dn": cert.issuer.rfc4514_string()
        },
        "validity": {
            "not_before": cert.not_valid_before_utc.isoformat(),
            "not_after": cert.not_valid_after_utc.isoformat()
        },
        "serial_number": str(cert.serial_number),
        "version": cert.version.name,
        "service": request.state.client_service
    }


@app.get("/api/v1/whoami", tags=["Authentication"])
async def whoami(request: Request) -> Dict[str, Any]:
    """
    Get current authenticated service identity.
    
    Returns:
        Service identity information
    """
    if not hasattr(request.state, 'mtls_validated'):
        return {
            "authenticated": False,
            "message": "Not authenticated via mTLS"
        }
    
    return {
        "authenticated": True,
        "service": request.state.client_service,
        "common_name": request.state.client_cn,
        "authentication_method": "mTLS"
    }


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("=" * 70)
    logger.info("🚀 VERITAS Framework API (mTLS) - Starting")
    logger.info("=" * 70)
    logger.info(f"PKI Services: {'✅ Initialized' if ca_service else '❌ Not available'}")
    logger.info(f"mTLS Middleware: {'✅ Active' if ca_service else '⚠️  Disabled'}")
    logger.info(f"Endpoints:")
    logger.info(f"  - Health Check: /health (no mTLS)")
    logger.info(f"  - API Test: /api/v1/test (mTLS required)")
    logger.info(f"  - Certificate Info: /api/v1/certificate-info (mTLS required)")
    logger.info(f"  - Who Am I: /api/v1/whoami (mTLS required)")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("🛑 VERITAS Framework API (mTLS) - Shutting down")


# ============================================================================
# Main Entry Point
# ============================================================================

def run_server(
    host: str = "0.0.0.0",
    port: int = 5000,
    ca_storage_path: str = "ca_storage"
):
    """
    Run the mTLS-enabled FastAPI server.
    
    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to bind to (default: 5000)
        ca_storage_path: Path to CA storage directory
    """
    ca_path = Path(ca_storage_path)
    
    # Check if certificates exist
    server_cert = ca_path / "server_cert.pem"
    server_key = ca_path / "server_key.pem"
    root_ca = ca_path / "ca_certificates" / "root_ca.pem"
    
    if not server_cert.exists():
        logger.error(f"❌ Server certificate not found: {server_cert}")
        logger.error("   Run: python scripts/setup_mtls_certificates.py")
        sys.exit(1)
    
    if not server_key.exists():
        logger.error(f"❌ Server key not found: {server_key}")
        sys.exit(1)
    
    if not root_ca.exists():
        logger.error(f"❌ Root CA certificate not found: {root_ca}")
        sys.exit(1)
    
    logger.info("✅ All certificates found")
    logger.info(f"   Server Cert: {server_cert}")
    logger.info(f"   Server Key:  {server_key}")
    logger.info(f"   Root CA:     {root_ca}")
    logger.info("")
    
    # Run server with mTLS
    logger.info(f"🚀 Starting VERITAS API with mTLS on https://{host}:{port}")
    logger.info("")
    logger.info("🔒 Client certificate required for all endpoints except /health")
    logger.info("")
    logger.info("📋 Test commands:")
    logger.info(f"   # Health check (no cert):")
    logger.info(f"   curl -k https://{host}:{port}/health")
    logger.info("")
    logger.info(f"   # API test (with cert):")
    logger.info(f"   curl --cert {ca_path}/client_cert.pem \\")
    logger.info(f"        --key {ca_path}/client_key.pem \\")
    logger.info(f"        --cacert {root_ca} \\")
    logger.info(f"        https://{host}:{port}/api/v1/test")
    logger.info("")
    
    # Note: ssl_cert_reqs=2 means ssl.CERT_REQUIRED
    uvicorn.run(
        app,
        host=host,
        port=port,
        ssl_keyfile=str(server_key),
        ssl_certfile=str(server_cert),
        ssl_ca_certs=str(root_ca),
        ssl_cert_reqs=2,  # ssl.CERT_REQUIRED
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
