# VERITAS PKI Integration - Complete Implementation Guide

**Status:** 🎯 **READY TO START**  
**PKI Server:** ✅ 100% Complete (C:\VCC\PKI)  
**Client Library:** ✅ Ready (`vcc-pki-client`)  
**Reference Implementation:** ✅ Covina (can be used as template)  
**Date:** 22. Oktober 2025  
**Estimated Total Time:** 3-4 hours

---

## 📋 Executive Summary

Diese TODO beschreibt die vollständige Integration des VCC PKI-Systems (C:\VCC\PKI) in VERITAS, basierend auf dem erfolgreichen Covina-Vorbild.

**Was wird erreicht:**
- ✅ **HTTPS statt HTTP:** Sichere API-Kommunikation mit TLS 1.3
- ✅ **Automatisches Certificate Management:** Kein manuelles Zertifikats-Handling
- ✅ **Auto-Renewal:** Zertifikate werden automatisch erneuert (90 Tage → 3 Tage vor Ablauf)
- ✅ **mTLS Support:** Optional für Service-zu-Service Kommunikation
- ✅ **Zentrale PKI:** Ein CA-System für alle VCC-Services (VERITAS, Covina, Clara, etc.)
- ✅ **Zero-Downtime:** Zertifikatswechsel ohne Service-Neustart

**Integration Points:**
1. Backend API (FastAPI)
2. Frontend API Client (Requests)
3. Streaming WebSocket
4. Database Connections (optional)
5. Ollama Client (optional)

---

## ✅ Status-Update (22. Oktober 2025)

Die PKI-Integration wurde um sichere Geheimnisverwaltung erweitert:

- [x] CA-Passwort in SecretsManager migriert (Windows DPAPI)
- [x] Backend nutzt `get_vcc_ca_password()` in `backend/app.py`
- [x] `.env` bereinigt: VCC_CA_PASSWORD nicht mehr im Klartext (kommentiert)
- [x] Migrations-Tool verfügbar: `python tools/migrate_secrets.py --backup`
- [x] Dokumentation: `docs/SECRETS_MANAGEMENT_GUIDE.md`

Hinweis: Für produktive Umgebungen kann optional Azure Key Vault verwendet werden. Der SecretsManager wählt automatisch zwischen Key Vault → DPAPI → ENV.

---

## 🎯 Phase 1: Core Backend Integration (60 minutes)

### 1.1 Prerequisites & Installation (5 minutes)

**Task 1: Install PKI Client Library**

```powershell
# Navigate to VERITAS root
cd C:\VCC\veritas

# Install PKI client in development mode
pip install -e C:\VCC\PKI\client

# Or add to requirements.txt
echo "-e C:\VCC\PKI\client" >> requirements.txt
pip install -r requirements.txt

# Verify installation
python -c "from vcc_pki_client import PKIClient; print('PKI Client installed successfully')"
```

**Expected Output:**
```
PKI Client installed successfully
```

**Task 2: Verify PKI Server Running**

```powershell
# Start PKI server if not running
cd C:\VCC\PKI\src
python pki_server.py --port 8443

# In another terminal, verify health
curl -k https://localhost:8443/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ca_initialized": true
}
```

**Task 3: Initialize CA (One-Time Setup)**

```powershell
# Only needed if CA not yet initialized
cd C:\VCC\PKI

# Create Root CA
python pki_admin_cli.py ca init-root --cn "VCC Root CA" --country DE --org "VCC GmbH"

# Create Intermediate CA
python pki_admin_cli.py ca create-intermediate --cn "VCC Intermediate CA" --country DE --org "VCC GmbH"

# Verify CA status
python pki_admin_cli.py ca info
```

---

### 1.2 Backend Code Integration (25 minutes)

**File:** `backend/app.py` (Main FastAPI Application)

**Task 4: Add PKI Client Import**

Add at the top of `backend/app.py`:

```python
from vcc_pki_client import PKIClient
import os
from pathlib import Path
```

**Task 5: Initialize PKI Client (Before app creation)**

Add before `app = FastAPI(...)`:

```python
# ============================================================================
# PKI CLIENT INITIALIZATION
# ============================================================================

from backend.security.secrets import get_vcc_ca_password  # secure CA password retrieval

# Initialize VCC PKI Client for certificate management
pki_client = PKIClient(
    pki_server_url=os.getenv("PKI_SERVER_URL", "https://localhost:8443"),
    service_id="veritas-backend",
    ca_password=get_vcc_ca_password(),  # DPAPI/Azure/ENV
    auto_register=True  # Auto-register service on first startup
)

logger.info("PKI Client initialized for VERITAS Backend")
```

**Task 6: Add Startup Event Handler**

Add after app creation:

```python
@app.on_event("startup")
async def startup_event():
    """
    Application startup tasks including PKI certificate management.
    """
    logger.info("🚀 VERITAS Backend starting up...")
    
    # === PKI CERTIFICATE MANAGEMENT ===
    try:
        # Check if certificate already exists
        cert_info = pki_client.get_certificate_info()
        logger.info(f"✅ Certificate found: {cert_info['common_name']}")
        logger.info(f"📅 Expires in {cert_info['days_until_expiry']} days")
        
        # Warn if certificate expires soon
        if cert_info['days_until_expiry'] < 30:
            logger.warning(f"⚠️ Certificate expires in {cert_info['days_until_expiry']} days!")
        
    except FileNotFoundError:
        # No certificate found - request new one
        logger.info("🔐 No certificate found - requesting new certificate from PKI server...")
        
        cert_request = pki_client.request_certificate(
            common_name="veritas-backend.vcc.local",
            san_dns=[
                "veritas-backend",
                "veritas-backend.vcc.local",
                "localhost",
                "127.0.0.1"
            ],
            san_ip=["127.0.0.1"],
            organization="VCC GmbH",
            organizational_unit="VERITAS Development",
            country="DE",
            validity_days=365
        )
        
        logger.info(f"✅ Certificate issued: {cert_request['certificate_id']}")
        logger.info(f"📅 Valid until: {cert_request['valid_until']}")
    
    # === REGISTER SERVICE ===
    try:
        registration = pki_client.register_service(
            service_name="VERITAS Backend API",
            service_version="4.0.1",
            endpoints=[
                "https://veritas-backend.vcc.local:8001/api",
                "https://localhost:8001/api"
            ],
            health_check_url="https://localhost:8001/api/system/health",
            metadata={
                "environment": os.getenv("APP_ENV", "production"),
                "uds3_enabled": True,
                "streaming_enabled": True,
                "agents_enabled": True
            }
        )
        logger.info(f"✅ Service registered: {registration['service_id']}")
    except Exception as e:
        logger.error(f"❌ Service registration failed: {e}")
        # Non-critical - continue startup
    
    # === ENABLE AUTO-RENEWAL ===
    try:
        pki_client.enable_auto_renewal(
            renewal_threshold_days=30,  # Renew 30 days before expiry
            check_interval_hours=6       # Check every 6 hours
        )
        logger.info("✅ Certificate auto-renewal enabled (checks every 6 hours)")
    except Exception as e:
        logger.error(f"❌ Auto-renewal setup failed: {e}")
    
    # === EXISTING STARTUP TASKS ===
    # UDS3 initialization
    # Pipeline initialization
    # Streaming service initialization
    # (keep existing code)
    
    logger.info("🎉 VERITAS Backend startup complete!")
```

**Task 7: Add Shutdown Event Handler**

```python
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown tasks including PKI cleanup.
    """
    logger.info("🛑 VERITAS Backend shutting down...")
    
    # === DISABLE AUTO-RENEWAL ===
    try:
        pki_client.disable_auto_renewal()
        logger.info("✅ Certificate auto-renewal disabled")
    except Exception as e:
        logger.error(f"❌ Auto-renewal disable failed: {e}")
    
    # === DEREGISTER SERVICE ===
    try:
        pki_client.deregister_service()
        logger.info("✅ Service deregistered from PKI")
    except Exception as e:
        logger.error(f"❌ Service deregistration failed: {e}")
    
    # === EXISTING SHUTDOWN TASKS ===
    # (keep existing code)
    
    logger.info("👋 VERITAS Backend shutdown complete!")
```

**Task 8: Update uvicorn.run() for HTTPS**

Update the main block at the bottom of `backend/app.py`:

```python
if __name__ == "__main__":
    import uvicorn
    
    # === GET SSL CONTEXT FROM PKI CLIENT ===
    try:
        ssl_context = pki_client.get_ssl_context(
            client_auth=False  # Set to True for mTLS
        )
        logger.info("✅ SSL context created from PKI certificates")
        
        # Start with HTTPS
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            ssl_certfile=pki_client.get_cert_path(),
            ssl_keyfile=pki_client.get_key_path(),
            # Or use ssl_context directly:
            # ssl_context=ssl_context,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"❌ Failed to start with HTTPS: {e}")
        logger.warning("⚠️ Falling back to HTTP (insecure!)")
        
        # Fallback to HTTP
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )
```

---

### 1.3 Environment Configuration (5 minutes)

**Task 9: Update .env File**

Create or update `C:\VCC\veritas\.env`:

```bash
# === VCC PKI CONFIGURATION ===
PKI_SERVER_URL=https://localhost:8443
# CA password is managed via Secrets Manager (DPAPI). Migrate with:
#   python tools/migrate_secrets.py --backup
ENABLE_SECURE_SECRETS=true

# Service identification
SERVICE_ID=veritas-backend
SERVICE_NAME=VERITAS Backend API
SERVICE_VERSION=4.0.1

# Certificate settings
CERT_AUTO_RENEWAL=true
CERT_RENEWAL_THRESHOLD_DAYS=30
CERT_CHECK_INTERVAL_HOURS=6

# === EXISTING CONFIGURATION ===
# (keep existing environment variables)
```

**Security Note:** Never commit `.env` to version control! Add to `.gitignore`:

```bash
# In .gitignore
.env
.env.*
!.env.example
```

**Task 10: Create .env.example Template**

Create `C:\VCC\veritas\.env.example`:

```bash
# VCC PKI Configuration
PKI_SERVER_URL=https://localhost:8443
# CA password managed by Secrets Manager (no plaintext here)
ENABLE_SECURE_SECRETS=true

# Service Settings
SERVICE_ID=veritas-backend
SERVICE_NAME=VERITAS Backend API
SERVICE_VERSION=4.0.1
```

---

### 1.4 Testing Backend Integration (25 minutes)

**Task 11: Start PKI Server**

```powershell
# Terminal 1: Start PKI Server
cd C:\VCC\PKI\src
python pki_server.py --port 8443

# Wait for "PKI Server started on https://0.0.0.0:8443"
```

**Task 12: Start VERITAS Backend**

```powershell
# Terminal 2: Start VERITAS Backend
cd C:\VCC\veritas
python backend/app.py

# Or use start script
python start_backend.py
```

**Expected Console Output:**
```
PKI Client initialized for VERITAS Backend
🚀 VERITAS Backend starting up...
🔐 No certificate found - requesting new certificate from PKI server...
✅ Certificate issued: cert_12345678
📅 Valid until: 2026-10-22 10:30:00
✅ Service registered: veritas-backend
✅ Certificate auto-renewal enabled (checks every 6 hours)
✅ UDS3 initialized
✅ Pipeline initialized
✅ Streaming service initialized
🎉 VERITAS Backend startup complete!
INFO:     Uvicorn running on https://0.0.0.0:8001 (Press CTRL+C to quit)
```

**Task 13: Verify Certificate Generated**

```powershell
# Check certificate files created
ls C:\VCC\PKI\client\pki_client\veritas-backend\

# Should show:
# - certificate.pem
# - private_key.pem
# - ca_bundle.pem
# - metadata.json
```

**Task 14: Test HTTPS Endpoint**

```powershell
# Test health endpoint with curl
curl -k https://localhost:8001/api/system/health

# Or with Python
python -c "import requests; print(requests.get('https://localhost:8001/api/system/health', verify=False).json())"
```

**Expected Output:**
```json
{
  "status": "healthy",
  "components": {
    "uds3": {"status": "ok"},
    "pipeline": {"status": "ok"},
    "streaming": {"status": "ok"},
    "pki": {
      "status": "ok",
      "certificate_valid": true,
      "days_until_expiry": 365
    }
  }
}
```

**Task 15: Verify Certificate in PKI Admin CLI**

```powershell
cd C:\VCC\PKI
python pki_admin_cli.py cert info veritas-backend

# Should show certificate details:
# - Status: VALID
# - Common Name: veritas-backend.vcc.local
# - Valid Until: ...
# - Auto-Renewal: ENABLED
```

---

## 🎯 Phase 2: Frontend Integration (45 minutes)

### 2.1 Frontend API Client Update (25 minutes)

**File:** `frontend/api_client.py` (or similar)

**Task 16: Update API Base URL to HTTPS**

```python
# Before:
API_BASE_URL = "http://localhost:8001/api"

# After:
API_BASE_URL = os.getenv("BACKEND_URL", "https://veritas-backend.vcc.local:8001/api")
```

**Task 17: Add PKI Client for Certificate Verification**

```python
from vcc_pki_client import PKIClient
import requests
from pathlib import Path

class VeritasAPIClient:
    def __init__(self):
        # Initialize PKI client for certificate verification
        self.pki_client = PKIClient(
            pki_server_url=os.getenv("PKI_SERVER_URL", "https://localhost:8443"),
            service_id="veritas-frontend"
        )
        
        # Get CA bundle for backend verification
        self.ca_bundle_path = self.pki_client.get_ca_bundle_path()
        
        # Create session with SSL verification
        self.session = requests.Session()
        self.session.verify = str(self.ca_bundle_path)
        
        # Optional: Set timeout
        self.session.timeout = 30
    
    def get(self, endpoint: str, **kwargs):
        """GET request to backend with SSL verification"""
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data=None, **kwargs):
        """POST request to backend with SSL verification"""
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        response = self.session.post(url, json=data, **kwargs)
        response.raise_for_status()
        return response.json()
```

**Task 18: Update WebSocket Connection for WSS**

If using WebSocket streaming:

```python
import websocket
import ssl

class StreamingClient:
    def __init__(self):
        self.pki_client = PKIClient(
            pki_server_url=os.getenv("PKI_SERVER_URL", "https://localhost:8443"),
            service_id="veritas-frontend"
        )
        
        # Create SSL context for WSS
        self.ssl_context = ssl.create_default_context(
            cafile=str(self.pki_client.get_ca_bundle_path())
        )
    
    def connect_stream(self, session_id: str):
        # Before: ws://localhost:8001/ws/stream/{session_id}
        # After:  wss://veritas-backend.vcc.local:8001/ws/stream/{session_id}
        
        ws_url = f"wss://veritas-backend.vcc.local:8001/ws/stream/{session_id}"
        
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        ws.run_forever(sslopt={"context": self.ssl_context})
```

---

### 2.2 Frontend Environment Configuration (5 minutes)

**Task 19: Update Frontend .env**

Create or update `frontend/.env`:

```bash
# Backend API Configuration
BACKEND_URL=https://veritas-backend.vcc.local:8001/api
BACKEND_WS_URL=wss://veritas-backend.vcc.local:8001/ws

# PKI Configuration
PKI_SERVER_URL=https://localhost:8443
PKI_VERIFY_SSL=true

# Optional: Frontend certificate (for mTLS)
FRONTEND_CERT_PATH=
FRONTEND_KEY_PATH=
```

---

### 2.3 Testing Frontend Integration (15 minutes)

**Task 20: Start Frontend**

```powershell
# Terminal 3: Start Frontend
cd C:\VCC\veritas
python start_frontend.py

# Or direct:
python frontend/veritas_app.py
```

**Task 21: Test End-to-End Communication**

1. **Open Frontend GUI**
2. **Send Test Query:** "Was ist VERITAS?"
3. **Verify HTTPS Communication:**
   - Check backend logs for HTTPS requests
   - No SSL/TLS errors
   - Response received successfully

**Task 22: Verify Certificate Chain**

```powershell
# Download CA bundle from PKI server
curl -k https://localhost:8443/api/ca/bundle -o ca_bundle.pem

# Verify backend certificate
openssl s_client -connect localhost:8001 -CAfile ca_bundle.pem -showcerts
# Should show: Verification: OK
```

---

## 🎯 Phase 3: Advanced Features (60 minutes)

### 3.1 mTLS for Service-to-Service Communication (30 minutes)

**Scenario:** VERITAS Backend needs to call another VCC service (e.g., Covina, Clara)

**Task 23: Request Client Certificate for Backend**

```python
# In backend/app.py startup event:

# Request client certificate for calling other services
client_cert = pki_client.request_client_certificate(
    common_name="veritas-backend-client",
    usage="service_to_service",
    allowed_services=["covina-backend", "clara-backend"]
)

logger.info(f"✅ Client certificate for service calls: {client_cert['certificate_id']}")
```

**Task 24: Create Service Client with mTLS**

```python
# backend/services/service_client.py

from vcc_pki_client import PKIClient
import requests

class VCCServiceClient:
    """Client for calling other VCC services with mTLS authentication"""
    
    def __init__(self, target_service: str):
        self.target_service = target_service
        self.pki_client = PKIClient(
            pki_server_url=os.getenv("PKI_SERVER_URL"),
            service_id="veritas-backend"
        )
        
        # Create session with client certificate
        self.session = requests.Session()
        self.session.cert = (
            self.pki_client.get_client_cert_path(),
            self.pki_client.get_client_key_path()
        )
        self.session.verify = str(self.pki_client.get_ca_bundle_path())
    
    def call_service(self, endpoint: str, method: str = "GET", data=None):
        """Call another VCC service with mTLS authentication"""
        
        # Get target service URL from service registry
        service_info = self.pki_client.get_service_info(self.target_service)
        base_url = service_info['endpoints'][0]
        
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        response = self.session.request(
            method=method,
            url=url,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()

# Usage:
covina_client = VCCServiceClient("covina-backend")
result = covina_client.call_service("/api/v1/documents/search", "POST", {
    "query": "Bauantrag",
    "limit": 10
})
```

---

### 3.2 Certificate Health Monitoring (15 minutes)

**Task 25: Add PKI Health Check to System Router**

Update `backend/api/system_router.py`:

```python
@system_router.get("/health")
async def health_check(request: Request) -> Dict[str, Any]:
    """System Health Check including PKI status"""
    
    # Existing health checks
    uds3_ok = hasattr(request.app.state, "uds3") and request.app.state.uds3 is not None
    pipeline_ok = hasattr(request.app.state, "pipeline") and request.app.state.pipeline is not None
    
    # === PKI HEALTH CHECK ===
    pki_ok = False
    pki_details = {}
    
    try:
        # Get certificate info from PKI client
        cert_info = pki_client.get_certificate_info()
        days_until_expiry = cert_info['days_until_expiry']
        
        # Determine PKI health status
        if days_until_expiry > 30:
            pki_status = "ok"
            pki_ok = True
        elif days_until_expiry > 7:
            pki_status = "warning"
            pki_ok = True
        else:
            pki_status = "critical"
            pki_ok = False
        
        pki_details = {
            "available": True,
            "required": True,
            "status": pki_status,
            "certificate_valid": True,
            "days_until_expiry": days_until_expiry,
            "common_name": cert_info['common_name'],
            "auto_renewal_enabled": cert_info.get('auto_renewal_enabled', False),
            "message": f"Certificate expires in {days_until_expiry} days"
        }
        
    except Exception as e:
        pki_details = {
            "available": False,
            "required": True,
            "status": "error",
            "error": str(e),
            "message": "PKI certificate not available or invalid"
        }
    
    # Combined health status
    all_components_ok = uds3_ok and pipeline_ok and pki_ok
    
    return {
        "status": "healthy" if all_components_ok else "degraded",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "uds3": {"available": uds3_ok, "status": "ok" if uds3_ok else "error"},
            "pipeline": {"available": pipeline_ok, "status": "ok" if pipeline_ok else "error"},
            "pki": pki_details  # ← NEW
        }
    }
```

**Task 26: Add Certificate Expiry Alert**

```python
# backend/services/monitoring.py

from apscheduler.schedulers.background import BackgroundScheduler
from vcc_pki_client import PKIClient
import logging

logger = logging.getLogger(__name__)

class CertificateMonitor:
    """Monitor certificate expiry and send alerts"""
    
    def __init__(self, pki_client: PKIClient):
        self.pki_client = pki_client
        self.scheduler = BackgroundScheduler()
    
    def start(self):
        """Start monitoring certificate expiry"""
        # Check every 24 hours
        self.scheduler.add_job(
            self.check_certificate_expiry,
            'interval',
            hours=24,
            id='cert_expiry_check'
        )
        self.scheduler.start()
        logger.info("✅ Certificate monitoring started (checks every 24 hours)")
    
    def check_certificate_expiry(self):
        """Check certificate expiry and log warnings"""
        try:
            cert_info = self.pki_client.get_certificate_info()
            days_until_expiry = cert_info['days_until_expiry']
            
            if days_until_expiry <= 7:
                logger.critical(f"🚨 CRITICAL: Certificate expires in {days_until_expiry} days!")
                # TODO: Send email/Slack notification
            elif days_until_expiry <= 30:
                logger.warning(f"⚠️ WARNING: Certificate expires in {days_until_expiry} days")
            else:
                logger.info(f"✅ Certificate valid for {days_until_expiry} days")
        
        except Exception as e:
            logger.error(f"❌ Certificate expiry check failed: {e}")
    
    def stop(self):
        """Stop monitoring"""
        self.scheduler.shutdown()
        logger.info("Certificate monitoring stopped")

# Usage in app.py:
cert_monitor = CertificateMonitor(pki_client)

@app.on_event("startup")
async def startup_event():
    # ... existing startup code
    cert_monitor.start()

@app.on_event("shutdown")
async def shutdown_event():
    # ... existing shutdown code
    cert_monitor.stop()
```

---

### 3.3 PKI Admin Endpoints (15 minutes)

**Task 27: Add PKI Management Endpoints**

Create new file `backend/api/pki_admin_router.py`:

```python
"""
PKI Admin Router
================

Admin endpoints for PKI certificate management.
Protected by admin authentication.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from datetime import datetime

from backend.services.pki_client import pki_client
from backend.api.v3.models import SuccessResponse

pki_admin_router = APIRouter(
    prefix="/admin/pki",
    tags=["PKI Administration"]
)

# TODO: Add authentication dependency
# def get_admin_user(token: str = Depends(oauth2_scheme)):
#     ...

@pki_admin_router.get("/certificate/info")
async def get_certificate_info() -> Dict[str, Any]:
    """
    Get current service certificate information.
    
    Returns:
        Certificate details including expiry, status, etc.
    """
    try:
        cert_info = pki_client.get_certificate_info()
        return {
            "success": True,
            "certificate": cert_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@pki_admin_router.post("/certificate/renew")
async def renew_certificate() -> Dict[str, Any]:
    """
    Manually trigger certificate renewal.
    
    Normally handled automatically, but can be triggered manually.
    """
    try:
        result = pki_client.renew_certificate()
        return {
            "success": True,
            "message": "Certificate renewed successfully",
            "certificate": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@pki_admin_router.get("/auto-renewal/status")
async def get_auto_renewal_status() -> Dict[str, Any]:
    """Get certificate auto-renewal status."""
    try:
        status = pki_client.get_auto_renewal_status()
        return {
            "success": True,
            "auto_renewal": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@pki_admin_router.post("/auto-renewal/enable")
async def enable_auto_renewal() -> SuccessResponse:
    """Enable certificate auto-renewal."""
    try:
        pki_client.enable_auto_renewal()
        return SuccessResponse(
            success=True,
            message="Auto-renewal enabled"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@pki_admin_router.post("/auto-renewal/disable")
async def disable_auto_renewal() -> SuccessResponse:
    """Disable certificate auto-renewal."""
    try:
        pki_client.disable_auto_renewal()
        return SuccessResponse(
            success=True,
            message="Auto-renewal disabled"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@pki_admin_router.get("/service/registration")
async def get_service_registration() -> Dict[str, Any]:
    """Get service registration details from PKI."""
    try:
        registration = pki_client.get_service_registration()
        return {
            "success": True,
            "registration": registration
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Task 28: Register PKI Admin Router**

Update `backend/api/__init__.py`:

```python
from .pki_admin_router import pki_admin_router

# In api_router setup:
api_router.include_router(pki_admin_router, tags=["PKI Admin"])
```

---

## 🎯 Phase 4: Documentation & Testing (30 minutes)

### 4.1 Update Documentation (15 minutes)

**Task 29: Create PKI Integration Guide**

Create `docs/PKI_INTEGRATION_GUIDE.md` (this file can be used as template).

**Task 30: Update README.md**

Add PKI section to `README.md`:

```markdown
## 🔐 PKI Security

VERITAS uses the VCC PKI system for certificate management:

- **HTTPS enabled by default**
- **Automatic certificate renewal**
- **mTLS support for service-to-service communication**
- **Zero manual certificate management**

### Setup

1. Ensure PKI server is running:
   ```bash
   cd C:\VCC\PKI\src
   python pki_server.py --port 8443
   ```

2. Start VERITAS backend (certificate auto-requested):
   ```bash
   python backend/app.py
   ```

3. Backend will automatically:
   - Request certificate from PKI server
   - Enable HTTPS on port 8001
   - Activate auto-renewal

See `docs/PKI_INTEGRATION_GUIDE.md` for details.
```

---

### 4.2 Integration Testing (15 minutes)

**Task 31: Create PKI Integration Test**

Create `tests/integration/test_pki_integration.py`:

```python
"""
PKI Integration Tests

Tests certificate management, HTTPS endpoints, and auto-renewal.
"""

import pytest
import requests
from pathlib import Path
from vcc_pki_client import PKIClient

# Test configuration
PKI_SERVER_URL = "https://localhost:8443"
BACKEND_URL = "https://localhost:8001"

class TestPKIIntegration:
    """Test PKI integration with VERITAS backend"""
    
    @pytest.fixture
    def pki_client(self):
        """Create PKI client for testing"""
        return PKIClient(
            pki_server_url=PKI_SERVER_URL,
            service_id="veritas-backend-test"
        )
    
    def test_pki_server_running(self):
        """Test PKI server is accessible"""
        response = requests.get(f"{PKI_SERVER_URL}/health", verify=False)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_backend_certificate_exists(self, pki_client):
        """Test backend has valid certificate"""
        cert_info = pki_client.get_certificate_info()
        
        assert cert_info["common_name"] == "veritas-backend.vcc.local"
        assert cert_info["certificate_valid"] == True
        assert cert_info["days_until_expiry"] > 0
    
    def test_backend_https_endpoint(self, pki_client):
        """Test backend HTTPS endpoint with certificate verification"""
        ca_bundle = pki_client.get_ca_bundle_path()
        
        response = requests.get(
            f"{BACKEND_URL}/api/system/health",
            verify=str(ca_bundle)
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check PKI component in health check
        assert "pki" in data["components"]
        assert data["components"]["pki"]["certificate_valid"] == True
    
    def test_auto_renewal_enabled(self, pki_client):
        """Test auto-renewal is enabled"""
        status = pki_client.get_auto_renewal_status()
        
        assert status["enabled"] == True
        assert status["renewal_threshold_days"] == 30
    
    def test_service_registered(self, pki_client):
        """Test service is registered with PKI"""
        registration = pki_client.get_service_registration()
        
        assert registration["service_id"] == "veritas-backend"
        assert registration["service_name"] == "VERITAS Backend API"
        assert len(registration["endpoints"]) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Task 32: Run Integration Tests**

```powershell
# Run PKI integration tests
cd C:\VCC\veritas
pytest tests/integration/test_pki_integration.py -v

# Expected output:
# ✅ test_pki_server_running PASSED
# ✅ test_backend_certificate_exists PASSED
# ✅ test_backend_https_endpoint PASSED
# ✅ test_auto_renewal_enabled PASSED
# ✅ test_service_registered PASSED
# 
# 5 passed in 2.34s
```

---

## 🎯 Phase 5: Production Deployment (Optional, 60 minutes)

### 5.1 DNS Configuration (10 minutes)

**Task 33: Add DNS Entry for veritas-backend.vcc.local**

**Option A: Windows Hosts File (Development)**

Edit `C:\Windows\System32\drivers\etc\hosts` (as Administrator):

```
127.0.0.1    veritas-backend.vcc.local
127.0.0.1    veritas-frontend.vcc.local
```

**Option B: Local DNS Server (Production)**

Configure DNS server to resolve:
- `veritas-backend.vcc.local` → Backend IP
- `veritas-frontend.vcc.local` → Frontend IP

---

### 5.2 Firewall Configuration (5 minutes)

**Task 34: Open Firewall Ports**

```powershell
# Open HTTPS port for backend
New-NetFirewallRule -DisplayName "VERITAS Backend HTTPS" -Direction Inbound -LocalPort 8001 -Protocol TCP -Action Allow

# Open PKI server port
New-NetFirewallRule -DisplayName "VCC PKI Server" -Direction Inbound -LocalPort 8443 -Protocol TCP -Action Allow
```

---

### 5.3 Service Deployment (30 minutes)

**Task 35: Create Windows Service for PKI Server**

See `C:\VCC\PKI\docs\PRODUCTION_DEPLOYMENT.md` for PKI server service setup.

**Task 36: Create Windows Service for VERITAS Backend**

Create `scripts/install_service.ps1`:

```powershell
# Install VERITAS Backend as Windows Service
$serviceName = "VeritasBackend"
$displayName = "VERITAS Backend API"
$pythonExe = "C:\Users\YourUser\AppData\Local\Programs\Python\Python312\python.exe"
$scriptPath = "C:\VCC\veritas\backend\app.py"

# Create service using NSSM (Non-Sucking Service Manager)
nssm install $serviceName $pythonExe $scriptPath
nssm set $serviceName DisplayName $displayName
nssm set $serviceName Description "VERITAS Backend API with PKI integration"
nssm set $serviceName Start SERVICE_AUTO_START
nssm set $serviceName AppDirectory "C:\VCC\veritas"
nssm set $serviceName AppEnvironmentExtra "PKI_SERVER_URL=https://localhost:8443" "ENABLE_SECURE_SECRETS=true"

# Start service
nssm start $serviceName
```

---

### 5.4 Monitoring & Logging (15 minutes)

**Task 37: Configure Logging**

Update `backend/logging_config.py`:

```python
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    """Configure logging with PKI-specific loggers"""
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Main application log
    app_handler = RotatingFileHandler(
        log_dir / "veritas.log",
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    
    # PKI-specific log
    pki_handler = RotatingFileHandler(
        log_dir / "pki.log",
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=3
    )
    
    # Configure formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app_handler.setFormatter(formatter)
    pki_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(app_handler)
    root_logger.setLevel(logging.INFO)
    
    # PKI logger
    pki_logger = logging.getLogger("vcc_pki_client")
    pki_logger.addHandler(pki_handler)
    pki_logger.setLevel(logging.DEBUG)
```

---

## 📊 Success Metrics

### Functionality Checklist

After completing integration, verify:

- [ ] PKI Server running on https://localhost:8443
- [ ] VERITAS Backend running on https://localhost:8001
- [ ] Certificate auto-requested on first startup
- [ ] HTTPS endpoints accessible with SSL verification
- [ ] Certificate auto-renewal enabled
- [ ] Service registered in PKI service registry
- [ ] Health check includes PKI status
- [ ] Frontend connects via HTTPS
- [ ] WebSocket streams via WSS
- [ ] Integration tests passing (5/5)
- [ ] Certificate expiry monitoring active
- [ ] Logs show PKI operations

### Performance Benchmarks

Expected performance impact:

- **HTTPS vs HTTP overhead:** ~5-10ms per request (negligible)
- **Certificate verification:** <1ms (cached)
- **Auto-renewal check:** Background thread, no impact
- **Total performance impact:** <1% (acceptable)

### Security Posture

Security improvements achieved:

- ✅ **Encrypted Communication:** TLS 1.3 (AES-256-GCM)
- ✅ **Certificate-Based Authentication:** mTLS support
- ✅ **Automatic Certificate Rotation:** No manual intervention
- ✅ **Centralized PKI:** Single CA for all VCC services
- ✅ **Audit Trail:** All certificate operations logged
- ✅ **Compliance:** Meets VCC security standards

---

## 🔧 Troubleshooting

### Common Issues

**Issue 1: Certificate Request Fails**

```
❌ Error: PKI server connection refused
```

**Solution:**
1. Check PKI server running: `curl -k https://localhost:8443/health`
2. Check PKI_SERVER_URL in .env
3. Verify firewall allows port 8443

**Issue 2: SSL Verification Fails**

```
❌ Error: SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution:**
1. Download CA bundle: `curl -k https://localhost:8443/api/ca/bundle -o ca_bundle.pem`
2. Verify CA bundle path in code
3. Check certificate not expired: `openssl x509 -in certificate.pem -noout -dates`

**Issue 3: Auto-Renewal Not Working**

```
⚠️ Certificate expires in 5 days but not renewed
```

**Solution:**
1. Check auto-renewal enabled: `pki_client.get_auto_renewal_status()`
2. Check background thread running: Look for "Auto-renewal check" in logs
3. Manually trigger renewal: `pki_client.renew_certificate()`

**Issue 4: Frontend Can't Connect to Backend**

```
❌ Error: Connection refused to https://veritas-backend.vcc.local:8001
```

**Solution:**
1. Add to hosts file: `127.0.0.1 veritas-backend.vcc.local`
2. Or use `https://localhost:8001` instead
3. Check backend running: `curl -k https://localhost:8001/api/system/health`

---

## 📚 References

### PKI Documentation

- **PKI Project Status:** `C:\VCC\PKI\PROJECT_STATUS.md`
- **PKI Integration Quick Start:** `C:\VCC\PKI\INTEGRATION_QUICK_START.md`
- **PKI Client Library:** `C:\VCC\PKI\client\README.md`
- **PKI Admin CLI:** `C:\VCC\PKI\docs\PKI_ADMIN_CLI.md`
- **Service Integration Examples:** `C:\VCC\PKI\VCC_SERVICE_INTEGRATION_EXAMPLES.md`

### VERITAS Documentation

- **Backend Status:** `docs/BACKEND_STATUS_v4.0.1_COMPLETE.md`
- **Frontend Status:** `docs/FRONTEND_STATUS_v4.0.1_COMPLETE.md`
- **System Architecture:** `docs/SYSTEM_ARCHITECTURE_ANALYSIS.md`

### External Resources

- **TLS 1.3 RFC:** https://datatracker.ietf.org/doc/html/rfc8446
- **X.509 Certificate Standard:** https://datatracker.ietf.org/doc/html/rfc5280
- **FastAPI HTTPS:** https://fastapi.tiangolo.com/deployment/https/

---

## 🎉 Completion Checklist

Mark tasks as completed:

### Phase 1: Core Backend Integration (60 min)
- [ ] Task 1: Install PKI Client Library
- [ ] Task 2: Verify PKI Server Running
- [ ] Task 3: Initialize CA
- [ ] Task 4-8: Backend Code Integration
- [ ] Task 9-10: Environment Configuration
- [ ] Task 11-15: Testing Backend Integration

### Phase 2: Frontend Integration (45 min)
- [ ] Task 16-18: Frontend API Client Update
- [ ] Task 19: Frontend Environment Configuration
- [ ] Task 20-22: Testing Frontend Integration

### Phase 3: Advanced Features (60 min)
- [ ] Task 23-24: mTLS Implementation
- [ ] Task 25-26: Certificate Health Monitoring
- [ ] Task 27-28: PKI Admin Endpoints

### Phase 4: Documentation & Testing (30 min)
- [ ] Task 29-30: Update Documentation
- [ ] Task 31-32: Integration Testing

### Phase 5: Production Deployment (60 min, Optional)
- [ ] Task 33: DNS Configuration
- [ ] Task 34: Firewall Configuration
- [ ] Task 35-36: Service Deployment
- [ ] Task 37: Monitoring & Logging

---

## 📞 Support

**Questions or Issues?**

1. Check PKI documentation: `C:\VCC\PKI\docs\`
2. Check VERITAS documentation: `C:\VCC\veritas\docs\`
3. Review PKI integration examples: `C:\VCC\PKI\VCC_SERVICE_INTEGRATION_EXAMPLES.md`
4. Test with PKI Admin CLI: `python C:\VCC\PKI\pki_admin_cli.py --help`

---

**Last Updated:** 22. Oktober 2025  
**Version:** 1.0  
**Status:** Ready for Implementation 🚀
