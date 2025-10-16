# PKI/CA Integration in VERITAS

**Version**: 0.1.0  
**Status**: Mock-Implementierung (Entwicklung)  
**Datum**: 8. Oktober 2025

---

## 📋 Übersicht

Die PKI (Public Key Infrastructure) Integration ermöglicht Zertifikatsverwaltung, Signierung und Verschlüsselung im VERITAS Framework. Das PKI-System ist als eigenständiges Python-Package implementiert und bietet sowohl Mock-Funktionalität für Entwicklung als auch eine Schnittstelle zur echten PKI in `C:\VCC\PKI`.

### Hauptfunktionen

✅ **Zertifikatsverwaltung**: Erstellung, Widerruf, Erneuerung, Verifikation  
✅ **Certificate Authority (CA)**: CSR-Signierung, CRL-Verwaltung  
✅ **Kryptografische Operationen**: Verschlüsselung, Signierung, Hash-Funktionen  
✅ **REST API**: Vollständige API-Endpunkte für alle PKI-Operationen  
✅ **Mock-Mode**: Entwicklung ohne echte PKI-Infrastruktur  

---

## 🏗️ Architektur

```
C:\VCC\
├── PKI/                          # Externe PKI (eine Ebene über VERITAS)
│   ├── ca/                       # CA-Dateien
│   ├── certs/                    # Zertifikate
│   ├── private/                  # Private Keys
│   ├── config/                   # PKI-Konfiguration
│   └── crl/                      # Certificate Revocation Lists
│
└── veritas/
    ├── pki/                      # PKI Package
    │   ├── __init__.py           # Package Exports
    │   ├── cert_manager.py       # Certificate Manager
    │   ├── ca_service.py         # CA Service
    │   ├── crypto_utils.py       # Crypto Utilities
    │   ├── config.py             # Konfiguration
    │   └── exceptions.py         # Exceptions
    │
    ├── backend/api/
    │   └── pki_endpoints.py      # REST API
    │
    └── tests/test_pki/
        ├── test_cert_manager.py
        ├── test_ca_service.py
        └── test_crypto_utils.py
```

---

## 📦 Komponenten

### 1. Certificate Manager

**Datei**: `pki/cert_manager.py`

Verwaltet Zertifikate: Erstellung, Widerruf, Verifikation, Suche.

```python
from pki import CertificateManager, CertificateType

# Initialisierung
manager = CertificateManager(mock_mode=True)

# Zertifikat erstellen
cert = manager.create_certificate(
    common_name="api.veritas.local",
    validity_days=365,
    key_size=2048,
    cert_type=CertificateType.SERVER,
    country="DE",
    organization="VERITAS"
)

# Zertifikate auflisten
certs = manager.list_certificates(status=CertificateStatus.VALID)

# Zertifikat widerrufen
manager.revoke_certificate(cert["cert_id"], reason="key_compromise")

# Zertifikat erneuern
new_cert = manager.renew_certificate(cert["cert_id"])
```

**Features**:
- ✅ Zertifikat erstellen mit vollständigen DN-Komponenten
- ✅ Schlüsselgenerierung (2048/4096 Bit RSA)
- ✅ Filter nach Status, Typ, Pagination
- ✅ Widerruf mit Grund
- ✅ Automatische Erneuerung
- ✅ Fingerprint-Berechnung (SHA256/384/512)

---

### 2. CA Service

**Datei**: `pki/ca_service.py`

Certificate Authority für CSR-Signierung und CRL-Verwaltung.

```python
from pki import CAService

# Initialisierung
ca = CAService(auto_initialize=True)

# CA-Info abrufen
info = ca.get_ca_info()
print(f"CA: {info['ca_name']}")

# CSR signieren
signed_cert = ca.sign_csr(
    csr_pem=csr_pem,
    validity_days=365,
    cert_type="server"
)

# CRL abrufen
crl = ca.get_crl()

# Zertifikatskette verifizieren
is_valid = ca.verify_chain(cert_pem, include_crl_check=True)
```

**Features**:
- ✅ CA-Initialisierung mit Self-Signed Root-Cert
- ✅ CSR-Signierung
- ✅ CRL-Generierung und -Verwaltung
- ✅ Zertifikatsketten-Verifikation
- ✅ Widerruf von CA-signierten Zertifikaten

---

### 3. Crypto Utilities

**Datei**: `pki/crypto_utils.py`

Kryptografische Hilfsfunktionen.

```python
from pki import (
    generate_key_pair,
    generate_csr,
    encrypt_data,
    decrypt_data,
    sign_data,
    verify_signature
)

# Schlüsselpaar generieren
private_key, public_key = generate_key_pair(key_size=2048)

# CSR erstellen
csr_pem = generate_csr(
    private_key_pem=private_key,
    common_name="test.veritas.local",
    country="DE",
    organization="VERITAS"
)

# Verschlüsselung
data = b"Secret message"
encrypted = encrypt_data(data, public_key)
decrypted = decrypt_data(encrypted, private_key)

# Signierung
signature = sign_data(data, private_key)
is_valid = verify_signature(data, signature, public_key)
```

**Features**:
- ✅ RSA-Schlüsselgenerierung (2048/4096 Bit)
- ✅ CSR-Generierung mit vollständigem DN
- ✅ Verschlüsselung/Entschlüsselung (Mock: Base64)
- ✅ Signierung/Verifikation (Mock: HMAC-SHA256)
- ✅ Hash-Funktionen (SHA256/384/512)
- ✅ Sichere Zufallsgenerierung

---

## 🌐 REST API

**Datei**: `backend/api/pki_endpoints.py`

Vollständige REST API für PKI-Operationen.

### Endpunkte

#### Zertifikate

```http
POST   /api/v1/pki/certificates              # Zertifikat erstellen
GET    /api/v1/pki/certificates              # Zertifikate auflisten
GET    /api/v1/pki/certificates/{cert_id}    # Zertifikat abrufen
DELETE /api/v1/pki/certificates/{cert_id}    # Zertifikat widerrufen
POST   /api/v1/pki/certificates/{cert_id}/renew  # Zertifikat erneuern
```

#### Certificate Authority

```http
GET    /api/v1/pki/ca/info                   # CA-Informationen
GET    /api/v1/pki/ca/certificate            # CA-Zertifikat
GET    /api/v1/pki/ca/crl                    # CRL abrufen
POST   /api/v1/pki/ca/sign                   # CSR signieren
```

#### Statistiken

```http
GET    /api/v1/pki/statistics                # PKI-Statistiken
GET    /api/v1/pki/health                    # Health Check
```

### Beispiel: Zertifikat erstellen

**Request**:
```http
POST /api/v1/pki/certificates
Content-Type: application/json

{
  "common_name": "api.veritas.local",
  "validity_days": 365,
  "key_size": 2048,
  "cert_type": "server",
  "country": "DE",
  "organization": "VERITAS",
  "sans": ["www.veritas.local", "api.veritas.local"]
}
```

**Response**:
```json
{
  "cert_id": "550e8400-e29b-41d4-a716-446655440000",
  "common_name": "api.veritas.local",
  "cert_type": "server",
  "status": "valid",
  "valid_from": "2025-10-08T10:00:00Z",
  "valid_until": "2026-10-08T10:00:00Z",
  "fingerprint": "a1b2c3d4...",
  "serial_number": "1234567890abcdef",
  "key_size": 2048,
  "cert_pem": "-----BEGIN CERTIFICATE-----\n...",
  "subject": {
    "common_name": "api.veritas.local",
    "country": "DE",
    "organization": "VERITAS"
  }
}
```

### Swagger UI

Nach Backend-Start verfügbar unter:
```
http://localhost:8000/docs#/PKI%20%26%20Certificates
```

---

## ⚙️ Konfiguration

### Umgebungsvariablen

**Datei**: `.env`

```bash
# PKI Base Configuration
PKI_ENABLED=true
PKI_MOCK_MODE=true
PKI_BASE_PATH=C:\VCC\PKI

# Certificate Settings
CERT_VALIDITY_DAYS=365
CERT_KEY_SIZE=2048
CERT_HASH_ALGORITHM=SHA256

# CA Settings
CA_NAME=VERITAS CA
CA_COUNTRY=DE
CA_STATE=NRW
CA_LOCALITY=Köln
CA_ORGANIZATION=VERITAS
CA_ORGANIZATIONAL_UNIT=IT Security
CA_EMAIL=ca@veritas.local
CA_VALIDITY_YEARS=10

# CRL Settings
CRL_UPDATE_INTERVAL_HOURS=24

# Mock Settings
MOCK_MAX_CERTIFICATES=1000
```

### Python-Konfiguration

**Datei**: `pki/config.py`

```python
from pki import get_pki_config, validate_config, is_mock_mode

# Komplette Konfiguration abrufen
config = get_pki_config()

# Konfiguration validieren
if validate_config():
    print("PKI config valid")

# Mock-Mode prüfen
if is_mock_mode():
    print("Running in MOCK mode")
```

---

## 🧪 Tests

### Unit Tests

**Dateien**: `tests/test_pki/`

```bash
# Alle PKI-Tests
pytest tests/test_pki/ -v

# Nur Certificate Manager
pytest tests/test_pki/test_cert_manager.py -v

# Nur CA Service
pytest tests/test_pki/test_ca_service.py -v

# Nur Crypto Utilities
pytest tests/test_pki/test_crypto_utils.py -v

# Mit Coverage
pytest tests/test_pki/ --cov=pki --cov-report=html
```

**Test-Abdeckung**:
- ✅ Certificate Manager: 25 Tests
- ✅ CA Service: 20 Tests
- ✅ Crypto Utilities: 18 Tests
- **Gesamt**: 63 Tests

### Testbeispiele

```python
import pytest
from pki import CertificateManager

def test_create_certificate():
    manager = CertificateManager(mock_mode=True)
    cert = manager.create_certificate("test.local")
    
    assert cert["common_name"] == "test.local"
    assert cert["status"] == "valid"
```

---

## 🚀 Verwendung

### Schnellstart (Mock-Mode)

```python
from pki import CertificateManager, CAService

# 1. Certificate Manager
manager = CertificateManager(mock_mode=True)

# Zertifikat erstellen
cert = manager.create_certificate(
    common_name="test.veritas.local",
    validity_days=365
)

print(f"Created: {cert['cert_id']}")
print(f"Fingerprint: {cert['fingerprint']}")

# 2. CA Service
ca = CAService(auto_initialize=True)

# CA-Zertifikat abrufen
ca_cert = ca.get_ca_certificate()
print(f"CA Certificate:\n{ca_cert}")

# 3. Crypto Operations
from pki import generate_key_pair, encrypt_data, decrypt_data

private_key, public_key = generate_key_pair()
encrypted = encrypt_data(b"Secret", public_key)
decrypted = decrypt_data(encrypted, private_key)
```

### Integration in Backend

**Datei**: `backend/api/main.py` (Beispiel)

```python
from fastapi import FastAPI
from backend.api import pki_endpoints

app = FastAPI()

# PKI Router einbinden
app.include_router(pki_endpoints.router)

# Server starten
# uvicorn backend.api.main:app --reload
```

---

## 🔐 Sicherheit

### Mock-Mode vs. Produktion

| Feature | Mock-Mode | Produktion |
|---------|-----------|------------|
| **Verschlüsselung** | Base64 | RSA/OAEP |
| **Signierung** | HMAC-SHA256 | RSA-PSS |
| **Schlüssel** | Fake PEM | Echte RSA-Keys |
| **Speicher** | In-Memory | Datenbank + Filesystem |
| **CA** | Self-Signed Mock | Echte CA |

### Best Practices

⚠️ **Entwicklung**:
- Mock-Mode verwenden (`PKI_MOCK_MODE=true`)
- Keine echten Private Keys generieren
- Test-Datenbank verwenden

⚠️ **Produktion**:
- Mock-Mode deaktivieren (`PKI_MOCK_MODE=false`)
- `cryptography` Library integrieren
- Private Keys sicher speichern (HSM, Vault)
- HTTPS für alle API-Zugriffe
- RBAC für PKI-Endpunkte
- Audit-Logging aktivieren

⚠️ **Niemals**:
- Private Keys in Git committen
- CA-Private-Key exponieren
- Mock-Mode in Produktion

---

## 🔄 Migration zu echter PKI

### Schritt 1: Dependencies installieren

```bash
pip install cryptography pyopenssl
```

### Schritt 2: PKI-Verzeichnis vorbereiten

```bash
mkdir C:\VCC\PKI\ca
mkdir C:\VCC\PKI\certs
mkdir C:\VCC\PKI\private
mkdir C:\VCC\PKI\crl
```

### Schritt 3: Mock-Mode deaktivieren

```bash
# .env
PKI_MOCK_MODE=false
```

### Schritt 4: Echte Implementierung

```python
# pki/crypto_utils.py - Ersetzen mit cryptography

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_key_pair(key_size: int = 2048):
    """Echte RSA-Schlüsselgenerierung"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem.decode(), public_pem.decode()
```

### Schritt 5: Tests mit echter PKI

```bash
pytest tests/test_pki/ -v --real-pki
```

---

## 📊 Statistiken & Monitoring

### PKI-Statistiken abrufen

```python
from pki import CertificateManager

manager = CertificateManager(mock_mode=True)
stats = manager.get_statistics()

print(f"Total: {stats['total_certificates']}")
print(f"Valid: {stats['valid_certificates']}")
print(f"Revoked: {stats['revoked_certificates']}")
print(f"By Type: {stats['certificates_by_type']}")
```

**API**:
```http
GET /api/v1/pki/statistics
```

**Response**:
```json
{
  "total_certificates": 42,
  "valid_certificates": 38,
  "expired_certificates": 2,
  "revoked_certificates": 2,
  "certificates_by_type": {
    "server": 30,
    "client": 10,
    "code_signing": 2
  },
  "mock_mode": true,
  "ca_info": {
    "ca_name": "VERITAS CA",
    "initialized": true
  }
}
```

---

## 🐛 Troubleshooting

### Problem: `CANotInitializedError`

**Lösung**:
```python
ca = CAService(auto_initialize=True)
# oder
ca = CAService()
ca.initialize_ca()
```

### Problem: `CertificateNotFoundError`

**Lösung**:
```python
# Prüfe ob cert_id existiert
cert = manager.get_certificate(cert_id)
if not cert:
    print("Certificate not found")
```

### Problem: Mock-Zertifikate nicht vertrauenswürdig

**Erwartetes Verhalten**: Mock-Zertifikate sind NICHT für Produktion gedacht!

**Lösung**: Migration zu echter PKI durchführen.

---

## 📚 API-Referenz

### CertificateManager

| Methode | Beschreibung |
|---------|--------------|
| `create_certificate()` | Erstellt neues Zertifikat |
| `get_certificate(cert_id)` | Ruft Zertifikat ab |
| `list_certificates()` | Listet Zertifikate |
| `revoke_certificate()` | Widerruft Zertifikat |
| `renew_certificate()` | Erneuert Zertifikat |
| `verify_certificate()` | Verifiziert Zertifikat |
| `get_statistics()` | Statistiken |

### CAService

| Methode | Beschreibung |
|---------|--------------|
| `initialize_ca()` | Initialisiert CA |
| `sign_csr()` | Signiert CSR |
| `get_ca_certificate()` | CA-Cert abrufen |
| `get_crl()` | CRL abrufen |
| `revoke_certificate()` | Zertifikat widerrufen |
| `verify_chain()` | Chain verifizieren |

### Crypto Utilities

| Funktion | Beschreibung |
|----------|--------------|
| `generate_key_pair()` | RSA-Schlüsselpaar |
| `generate_csr()` | CSR erstellen |
| `encrypt_data()` | Daten verschlüsseln |
| `decrypt_data()` | Daten entschlüsseln |
| `sign_data()` | Daten signieren |
| `verify_signature()` | Signatur prüfen |
| `calculate_fingerprint()` | Fingerprint |
| `hash_data()` | Hash berechnen |

---

## 📝 Changelog

### Version 0.1.0 (2025-10-08)

**Neu**:
- ✅ Vollständige Mock-Implementierung
- ✅ Certificate Manager mit CRUD-Operationen
- ✅ CA Service mit CSR-Signierung
- ✅ Crypto Utilities (Mock)
- ✅ REST API mit 11 Endpunkten
- ✅ 63 Unit-Tests
- ✅ Vollständige Dokumentation

**Geplant für v0.2.0**:
- 🔄 Echte Kryptografie (cryptography library)
- 🔄 Datenbank-Integration
- 🔄 Filesystem-Storage für Zertifikate
- 🔄 OCSP-Support
- 🔄 Intermediate CA Support

---

## 🤝 Kontakt & Support

**Entwickler**: VERITAS Team  
**Dokumentation**: `docs/PKI_INTEGRATION.md`  
**Tests**: `tests/test_pki/`  
**API**: `backend/api/pki_endpoints.py`

---

## 📄 Lizenz

Internes Projekt - VERITAS Framework

---

**Erstellt**: 8. Oktober 2025  
**Letzte Aktualisierung**: 8. Oktober 2025  
**Version**: 0.1.0 (Mock-Implementation)
