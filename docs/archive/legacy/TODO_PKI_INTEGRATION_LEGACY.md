# TODO: PKI/CA Integration in VERITAS Framework

**Datum**: 8. Oktober 2025  
**Status**: 📋 Geplant  
**Priorität**: Mittel  
**Geschätzter Aufwand**: 4-6 Stunden

---

## Übersicht

Integration der PKI (Public Key Infrastructure) / CA (Certificate Authority) aus `C:\VCC\PKI` als Library-Package in das VERITAS Framework. Das PKI-System soll als shared package für Zertifikatsverwaltung, Signierung und Verschlüsselung verwendet werden.

---

## Ziele

1. **PKI als Python Package** integrieren
2. **Verzeichnisstruktur** im VERITAS-Projekt vorbereiten
3. **Mock-Implementierung** für Entwicklung/Tests
4. **Dokumentation** der PKI-Integration
5. **API-Endpunkte** für Zertifikatsverwaltung (Vorbereitung)

---

## Aufgaben

### 1. Verzeichnisstruktur erstellen

**Pfad**: `c:\VCC\veritas\pki\`

```
veritas/
├── pki/
│   ├── __init__.py              # Package initialization
│   ├── cert_manager.py          # Certificate management (mock)
│   ├── ca_service.py            # CA service interface (mock)
│   ├── crypto_utils.py          # Cryptographic utilities (mock)
│   ├── config.py                # PKI configuration
│   └── exceptions.py            # PKI-specific exceptions
├── docs/
│   └── PKI_INTEGRATION.md       # PKI documentation
└── tests/
    └── test_pki/
        ├── __init__.py
        ├── test_cert_manager.py
        └── test_ca_service.py
```

**Aufgabe**:
- [ ] Ordner `pki/` erstellen
- [ ] Basis-Dateien anlegen (`__init__.py`, etc.)
- [ ] Test-Ordner `tests/test_pki/` erstellen

---

### 2. PKI Package Konfiguration

**Datei**: `veritas/pki/config.py`

**Inhalt**:
```python
"""
PKI Configuration
Konfiguration für PKI/CA Integration
"""

import os
from pathlib import Path

# PKI Base Path (eine Ebene über veritas)
PKI_BASE_PATH = Path(r"C:\VCC\PKI")

# PKI Directories
PKI_CA_DIR = PKI_BASE_PATH / "ca"
PKI_CERTS_DIR = PKI_BASE_PATH / "certs"
PKI_PRIVATE_DIR = PKI_BASE_PATH / "private"
PKI_CONFIG_DIR = PKI_BASE_PATH / "config"

# Mock Mode (für Entwicklung ohne echte PKI)
PKI_MOCK_MODE = os.getenv("PKI_MOCK_MODE", "true").lower() == "true"

# Certificate Settings
CERT_VALIDITY_DAYS = 365
CERT_KEY_SIZE = 2048
CERT_HASH_ALGORITHM = "SHA256"

# CA Settings
CA_NAME = "VERITAS CA"
CA_COUNTRY = "DE"
CA_STATE = "NRW"
CA_LOCALITY = "Köln"
CA_ORGANIZATION = "VERITAS"
CA_ORGANIZATIONAL_UNIT = "IT Security"
```

**Aufgabe**:
- [ ] Konfigurationsdatei erstellen
- [ ] Umgebungsvariablen definieren
- [ ] Mock-Mode Toggle implementieren

---

### 3. Mock Certificate Manager

**Datei**: `veritas/pki/cert_manager.py`

**Funktionen** (Mock-Implementierung):
```python
"""
Certificate Manager
Mock-Implementierung für Zertifikatsverwaltung
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

class CertificateManager:
    """Mock Certificate Manager"""
    
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self._mock_certs: Dict[str, Dict[str, Any]] = {}
    
    def create_certificate(
        self,
        common_name: str,
        validity_days: int = 365,
        key_size: int = 2048
    ) -> Dict[str, Any]:
        """
        Erstellt ein neues Zertifikat (Mock)
        
        Returns:
            {
                'cert_id': str,
                'common_name': str,
                'valid_from': datetime,
                'valid_until': datetime,
                'fingerprint': str,
                'pem': str  # PEM-encoded cert
            }
        """
        pass
    
    def revoke_certificate(self, cert_id: str) -> bool:
        """Widerruft ein Zertifikat (Mock)"""
        pass
    
    def get_certificate(self, cert_id: str) -> Optional[Dict[str, Any]]:
        """Ruft Zertifikat-Details ab (Mock)"""
        pass
    
    def list_certificates(self, status: str = "valid") -> list:
        """Listet Zertifikate (Mock)"""
        pass
    
    def verify_certificate(self, cert_pem: str) -> bool:
        """Verifiziert ein Zertifikat (Mock)"""
        pass
```

**Aufgabe**:
- [ ] Mock-Klasse implementieren
- [ ] Basis-Methoden mit Dummy-Daten
- [ ] In-Memory-Storage für Mock-Zertifikate

---

### 4. Mock CA Service

**Datei**: `veritas/pki/ca_service.py`

**Funktionen** (Mock-Implementierung):
```python
"""
Certificate Authority Service
Mock-Implementierung für CA-Operationen
"""

from typing import Dict, Any, Optional

class CAService:
    """Mock Certificate Authority Service"""
    
    def __init__(self, ca_name: str = "VERITAS CA"):
        self.ca_name = ca_name
        self.ca_initialized = False
    
    def initialize_ca(self) -> bool:
        """Initialisiert die CA (Mock)"""
        pass
    
    def sign_csr(self, csr_pem: str) -> Dict[str, Any]:
        """Signiert einen CSR (Mock)"""
        pass
    
    def get_ca_certificate(self) -> str:
        """Ruft CA-Zertifikat ab (Mock)"""
        pass
    
    def get_crl(self) -> str:
        """Ruft Certificate Revocation List ab (Mock)"""
        pass
    
    def verify_chain(self, cert_pem: str) -> bool:
        """Verifiziert Zertifikatskette (Mock)"""
        pass
```

**Aufgabe**:
- [ ] Mock-CA-Klasse implementieren
- [ ] CSR-Signierung simulieren
- [ ] CRL-Generierung (Mock)

---

### 5. Crypto Utilities

**Datei**: `veritas/pki/crypto_utils.py`

**Funktionen** (Mock/Helper):
```python
"""
Cryptographic Utilities
Hilfs-Funktionen für Kryptografie
"""

import hashlib
from typing import Tuple

def generate_key_pair(key_size: int = 2048) -> Tuple[str, str]:
    """
    Generiert RSA-Schlüsselpaar (Mock)
    Returns: (private_key_pem, public_key_pem)
    """
    pass

def generate_csr(
    private_key_pem: str,
    common_name: str,
    **kwargs
) -> str:
    """Generiert CSR (Mock)"""
    pass

def calculate_fingerprint(cert_pem: str) -> str:
    """Berechnet Zertifikats-Fingerprint"""
    pass

def encrypt_data(data: bytes, public_key_pem: str) -> bytes:
    """Verschlüsselt Daten (Mock)"""
    pass

def decrypt_data(encrypted_data: bytes, private_key_pem: str) -> bytes:
    """Entschlüsselt Daten (Mock)"""
    pass

def sign_data(data: bytes, private_key_pem: str) -> bytes:
    """Signiert Daten (Mock)"""
    pass

def verify_signature(
    data: bytes,
    signature: bytes,
    public_key_pem: str
) -> bool:
    """Verifiziert Signatur (Mock)"""
    pass
```

**Aufgabe**:
- [ ] Helper-Funktionen implementieren
- [ ] Mock-Verschlüsselung/Signierung
- [ ] Fingerprint-Berechnung

---

### 6. PKI Exceptions

**Datei**: `veritas/pki/exceptions.py`

```python
"""
PKI Exceptions
Custom exceptions for PKI operations
"""

class PKIException(Exception):
    """Base exception for PKI errors"""
    pass

class CertificateNotFoundError(PKIException):
    """Certificate not found"""
    pass

class CertificateExpiredError(PKIException):
    """Certificate expired"""
    pass

class CertificateRevokedError(PKIException):
    """Certificate revoked"""
    pass

class InvalidCSRError(PKIException):
    """Invalid Certificate Signing Request"""
    pass

class CANotInitializedError(PKIException):
    """CA not initialized"""
    pass

class SignatureVerificationError(PKIException):
    """Signature verification failed"""
    pass
```

**Aufgabe**:
- [ ] Exception-Klassen definieren
- [ ] Docstrings hinzufügen

---

### 7. Package Initialization

**Datei**: `veritas/pki/__init__.py`

```python
"""
VERITAS PKI/CA Integration
Public Key Infrastructure für Zertifikatsverwaltung
"""

from .cert_manager import CertificateManager
from .ca_service import CAService
from .crypto_utils import (
    generate_key_pair,
    generate_csr,
    calculate_fingerprint,
    encrypt_data,
    decrypt_data,
    sign_data,
    verify_signature
)
from .exceptions import (
    PKIException,
    CertificateNotFoundError,
    CertificateExpiredError,
    CertificateRevokedError,
    InvalidCSRError,
    CANotInitializedError,
    SignatureVerificationError
)
from .config import (
    PKI_BASE_PATH,
    PKI_MOCK_MODE,
    CERT_VALIDITY_DAYS
)

__version__ = "0.1.0"
__all__ = [
    # Classes
    "CertificateManager",
    "CAService",
    
    # Functions
    "generate_key_pair",
    "generate_csr",
    "calculate_fingerprint",
    "encrypt_data",
    "decrypt_data",
    "sign_data",
    "verify_signature",
    
    # Exceptions
    "PKIException",
    "CertificateNotFoundError",
    "CertificateExpiredError",
    "CertificateRevokedError",
    "InvalidCSRError",
    "CANotInitializedError",
    "SignatureVerificationError",
    
    # Config
    "PKI_BASE_PATH",
    "PKI_MOCK_MODE",
    "CERT_VALIDITY_DAYS"
]
```

**Aufgabe**:
- [ ] Package-Exports definieren
- [ ] Version festlegen
- [ ] `__all__` Liste vollständig

---

### 8. API Endpunkte (Vorbereitung)

**Datei**: `veritas/backend/api/pki_endpoints.py` (neu)

**Geplante Endpunkte**:

```python
"""
PKI API Endpoints
REST API für Zertifikatsverwaltung
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1/pki", tags=["PKI"])

# Request/Response Models
class CreateCertificateRequest(BaseModel):
    common_name: str
    validity_days: int = 365
    key_size: int = 2048

class CertificateResponse(BaseModel):
    cert_id: str
    common_name: str
    valid_from: datetime
    valid_until: datetime
    fingerprint: str
    status: str

# Endpoints (Mock-Implementation)
@router.post("/certificates", response_model=CertificateResponse)
async def create_certificate(request: CreateCertificateRequest):
    """Erstellt ein neues Zertifikat"""
    pass

@router.get("/certificates", response_model=List[CertificateResponse])
async def list_certificates(status: Optional[str] = "valid"):
    """Listet Zertifikate"""
    pass

@router.get("/certificates/{cert_id}", response_model=CertificateResponse)
async def get_certificate(cert_id: str):
    """Ruft Zertifikat-Details ab"""
    pass

@router.delete("/certificates/{cert_id}")
async def revoke_certificate(cert_id: str):
    """Widerruft ein Zertifikat"""
    pass

@router.get("/ca/certificate")
async def get_ca_certificate():
    """Ruft CA-Zertifikat ab"""
    pass

@router.get("/ca/crl")
async def get_crl():
    """Ruft Certificate Revocation List ab"""
    pass
```

**Aufgabe**:
- [ ] API-Router erstellen
- [ ] Pydantic-Modelle definieren
- [ ] Mock-Endpoints implementieren
- [ ] In `backend/api/main.py` einbinden

---

### 9. Tests

**Datei**: `veritas/tests/test_pki/test_cert_manager.py`

```python
"""
Tests für Certificate Manager
"""

import pytest
from pki.cert_manager import CertificateManager

def test_create_certificate():
    """Test: Zertifikat erstellen"""
    manager = CertificateManager(mock_mode=True)
    cert = manager.create_certificate("test.veritas.local")
    
    assert cert is not None
    assert cert['common_name'] == "test.veritas.local"
    assert 'cert_id' in cert
    assert 'fingerprint' in cert

def test_list_certificates():
    """Test: Zertifikate auflisten"""
    manager = CertificateManager(mock_mode=True)
    certs = manager.list_certificates()
    
    assert isinstance(certs, list)

def test_revoke_certificate():
    """Test: Zertifikat widerrufen"""
    manager = CertificateManager(mock_mode=True)
    cert = manager.create_certificate("revoke.test")
    
    result = manager.revoke_certificate(cert['cert_id'])
    assert result is True
```

**Aufgabe**:
- [ ] Unit-Tests für CertificateManager
- [ ] Unit-Tests für CAService
- [ ] Unit-Tests für crypto_utils
- [ ] Pytest fixtures erstellen

---

### 10. Dokumentation

**Datei**: `veritas/docs/PKI_INTEGRATION.md`

**Inhalte**:
```markdown
# PKI/CA Integration in VERITAS

## Übersicht

Die PKI (Public Key Infrastructure) Integration ermöglicht 
Zertifikatsverwaltung, Signierung und Verschlüsselung im VERITAS Framework.

## Architektur

- **PKI Base Path**: `C:\VCC\PKI`
- **VERITAS PKI Package**: `veritas/pki/`
- **Mock Mode**: Entwicklung ohne echte PKI

## Komponenten

### 1. Certificate Manager
Verwaltet Zertifikate (Erstellung, Widerruf, Verifikation)

### 2. CA Service
Certificate Authority Operationen (CSR-Signierung, CRL)

### 3. Crypto Utilities
Verschlüsselung, Signierung, Key-Generierung

## Verwendung

### Mock Mode (Entwicklung)
```python
from pki import CertificateManager

manager = CertificateManager(mock_mode=True)
cert = manager.create_certificate("test.veritas.local")
```

### Produktion (mit echter PKI)
```python
import os
os.environ["PKI_MOCK_MODE"] = "false"

from pki import CertificateManager
manager = CertificateManager(mock_mode=False)
```

## API Endpoints

- POST `/api/v1/pki/certificates` - Zertifikat erstellen
- GET `/api/v1/pki/certificates` - Zertifikate auflisten
- GET `/api/v1/pki/certificates/{id}` - Zertifikat abrufen
- DELETE `/api/v1/pki/certificates/{id}` - Zertifikat widerrufen
- GET `/api/v1/pki/ca/certificate` - CA-Zertifikat
- GET `/api/v1/pki/ca/crl` - CRL abrufen

## Konfiguration

`.env`:
```
PKI_MOCK_MODE=true
PKI_BASE_PATH=C:\VCC\PKI
CERT_VALIDITY_DAYS=365
```

## Sicherheit

- Private Keys niemals committen
- Mock-Mode nur in Entwicklung
- HTTPS für API-Zugriff
- RBAC für PKI-Endpunkte

## Migration zur echten PKI

1. `C:\VCC\PKI` Ordnerstruktur prüfen
2. CA initialisieren
3. `PKI_MOCK_MODE=false` setzen
4. Echte Krypto-Bibliothek integrieren (cryptography)
5. Tests mit echter PKI durchführen
```

**Aufgabe**:
- [ ] Dokumentation erstellen
- [ ] Architektur-Diagramm hinzufügen
- [ ] Verwendungsbeispiele
- [ ] Security-Hinweise

---

## Dependencies

**Neue Python-Pakete** (für echte PKI, später):
```txt
# pki/requirements.txt
cryptography>=41.0.0  # Für echte Krypto-Operationen
pyopenssl>=23.0.0     # OpenSSL-Wrapper
pycryptodome>=3.19.0  # Zusätzliche Crypto-Funktionen
```

**Für Mock-Implementation**: Keine zusätzlichen Dependencies

**Aufgabe**:
- [ ] `pki/requirements.txt` erstellen
- [ ] In Haupt-`requirements.txt` referenzieren (optional)

---

## Integration in bestehendes System

### 1. Backend API

**Datei**: `veritas/backend/api/main.py`

```python
# PKI Router einbinden
from backend.api import pki_endpoints

app.include_router(pki_endpoints.router)
```

### 2. Konfiguration

**Datei**: `veritas/config/config.py`

```python
# PKI Configuration
PKI_ENABLED = os.getenv("PKI_ENABLED", "true") == "true"
PKI_MOCK_MODE = os.getenv("PKI_MOCK_MODE", "true") == "true"
PKI_BASE_PATH = os.getenv("PKI_BASE_PATH", r"C:\VCC\PKI")
```

### 3. Environment Variables

**Datei**: `veritas/.env.example`

```
# PKI Configuration
PKI_ENABLED=true
PKI_MOCK_MODE=true
PKI_BASE_PATH=C:\VCC\PKI
CERT_VALIDITY_DAYS=365
CERT_KEY_SIZE=2048
```

**Aufgabe**:
- [ ] Router in main.py einbinden
- [ ] Config-Variablen hinzufügen
- [ ] .env.example aktualisieren

---

## Phasenplan

### Phase 1: Vorbereitung/Mockup (2-3 Stunden)
- [ ] Verzeichnisstruktur erstellen
- [ ] Mock-Klassen implementieren
- [ ] Basis-Konfiguration
- [ ] Exceptions definieren
- [ ] Package-Struktur

### Phase 2: API Integration (1-2 Stunden)
- [ ] API-Endpunkte (Mock)
- [ ] Pydantic-Modelle
- [ ] Router einbinden
- [ ] OpenAPI-Schema

### Phase 3: Tests & Dokumentation (1-2 Stunden)
- [ ] Unit-Tests schreiben
- [ ] Integration-Tests (API)
- [ ] Dokumentation erstellen
- [ ] Beispiele hinzufügen

### Phase 4: Vorbereitung echte PKI (später)
- [ ] cryptography-Bibliothek integrieren
- [ ] Echte Implementierung (kein Mock)
- [ ] C:\VCC\PKI Ordnerstruktur prüfen
- [ ] Migration von Mock zu Prod

---

## Verzeichnisstruktur (Ziel)

```
C:\VCC\
├── PKI/                          # Externe PKI (eine Ebene über)
│   ├── ca/                       # CA-Dateien
│   ├── certs/                    # Zertifikate
│   ├── private/                  # Private Keys
│   ├── config/                   # PKI-Konfiguration
│   └── crl/                      # Certificate Revocation Lists
│
└── veritas/
    ├── pki/                      # PKI Package (Mock/Integration)
    │   ├── __init__.py
    │   ├── cert_manager.py       # ✅ Mock Certificate Manager
    │   ├── ca_service.py         # ✅ Mock CA Service
    │   ├── crypto_utils.py       # ✅ Crypto Utilities
    │   ├── config.py             # ✅ PKI Configuration
    │   └── exceptions.py         # ✅ PKI Exceptions
    │
    ├── backend/
    │   └── api/
    │       └── pki_endpoints.py  # ✅ PKI API Endpoints
    │
    ├── docs/
    │   └── PKI_INTEGRATION.md    # ✅ PKI Dokumentation
    │
    └── tests/
        └── test_pki/
            ├── __init__.py
            ├── test_cert_manager.py
            └── test_ca_service.py
```

---

## Checkliste

### Vorbereitung
- [ ] Verzeichnis `pki/` erstellen
- [ ] Verzeichnis `tests/test_pki/` erstellen
- [ ] `__init__.py` Dateien anlegen

### Implementierung
- [ ] `pki/config.py` - Konfiguration
- [ ] `pki/exceptions.py` - Exception-Klassen
- [ ] `pki/cert_manager.py` - Mock Certificate Manager
- [ ] `pki/ca_service.py` - Mock CA Service
- [ ] `pki/crypto_utils.py` - Crypto Utilities (Mock)
- [ ] `pki/__init__.py` - Package Exports

### API Integration
- [ ] `backend/api/pki_endpoints.py` - API Endpoints
- [ ] Pydantic-Modelle definieren
- [ ] Router in `main.py` einbinden
- [ ] OpenAPI-Schema prüfen

### Tests
- [ ] `test_cert_manager.py` - Unit-Tests
- [ ] `test_ca_service.py` - Unit-Tests
- [ ] `test_crypto_utils.py` - Unit-Tests
- [ ] `test_pki_endpoints.py` - API Integration-Tests

### Dokumentation
- [ ] `docs/PKI_INTEGRATION.md` - Vollständige Dokumentation
- [ ] Architektur-Diagramm
- [ ] Verwendungsbeispiele
- [ ] Migration-Guide (Mock → Prod)

### Konfiguration
- [ ] `.env.example` aktualisieren
- [ ] `config/config.py` erweitern
- [ ] `README.md` aktualisieren

### Optional (später)
- [ ] `pki/requirements.txt` - Python-Dependencies
- [ ] Echte Krypto-Implementierung
- [ ] Integration mit `C:\VCC\PKI`
- [ ] Produktions-Tests

---

## Hinweise

⚠️ **Mock-Mode**: Alle initialen Implementierungen sind Mocks/Stubs für Entwicklung und Tests.

⚠️ **Externe PKI**: Die echte PKI liegt in `C:\VCC\PKI` (eine Ebene über VERITAS).

⚠️ **Security**: Private Keys niemals in Git committen! `.gitignore` prüfen.

✅ **Testing**: Alle Mock-Funktionen müssen testbar sein.

✅ **Dokumentation**: Klare Trennung zwischen Mock und Produktion dokumentieren.

---

## Nächste Schritte

1. **Diese TODO-Datei reviewen**
2. **Phase 1 starten**: Verzeichnisstruktur + Mock-Klassen
3. **Tests schreiben** während der Implementierung
4. **Dokumentation** parallel erstellen
5. **API-Integration** testen (Swagger UI)
6. **Migration-Plan** für echte PKI ausarbeiten

---

**Erstellt**: 8. Oktober 2025  
**Status**: 📋 Bereit zur Implementierung  
**Geschätzte Zeit**: 4-6 Stunden (Mock/Vorbereitung)  
**Ziel**: PKI-Integration vorbereitet, Mock lauffähig
