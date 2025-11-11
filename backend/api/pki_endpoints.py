"""
PKI API Endpoints
REST API für Zertifikatsverwaltung und CA-Operationen

Endpunkte:
- POST   /api/v1/pki/certificates          - Zertifikat erstellen
- GET    /api/v1/pki/certificates          - Zertifikate auflisten
- GET    /api/v1/pki/certificates/{cert_id} - Zertifikat abrufen
- DELETE /api/v1/pki/certificates/{cert_id} - Zertifikat widerrufen
- POST   /api/v1/pki/certificates/{cert_id}/renew - Zertifikat erneuern
- GET    /api/v1/pki/statistics            - PKI-Statistiken
- GET    /api/v1/pki/ca/info               - CA-Informationen
- GET    /api/v1/pki/ca/certificate        - CA-Zertifikat
- GET    /api/v1/pki/ca/crl                - CRL abrufen
- POST   /api/v1/pki/ca/sign               - CSR signieren
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pki import (
    CANotInitializedError,
    CAService,
    CertificateManager,
    CertificateNotFoundError,
    CertificateStatus,
    CertificateType,
    InvalidCertificateError,
    InvalidCSRError,
)
from pydantic import BaseModel, Field

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/pki", tags=["PKI & Certificates"])

# Globale Instanzen (Singleton-Pattern)
# In Produktion: Dependency Injection verwenden
cert_manager = CertificateManager(mock_mode=True)
ca_service = CAService(auto_initialize=True)


# ============================================================================
# Request/Response Models
# ============================================================================


class CertificateTypeEnum(str, Enum):
    """Zertifikatstyp Enum"""

    SERVER = "server"
    CLIENT = "client"
    CODE_SIGNING = "code_signing"
    EMAIL = "email"


class CertificateStatusEnum(str, Enum):
    """Zertifikatsstatus Enum"""

    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class CreateCertificateRequest(BaseModel):
    """Request: Zertifikat erstellen"""

    common_name: str = Field(..., description="Common Name (CN)", example="api.veritas.local")
    validity_days: int = Field(365, description="Gültigkeit in Tagen", ge=1, le=3650)
    key_size: int = Field(2048, description="RSA-Schlüsselgröße", enum=[2048, 4096])
    cert_type: CertificateTypeEnum = Field(CertificateTypeEnum.SERVER, description="Zertifikatstyp")
    country: Optional[str] = Field(None, description="Ländercode (C)", max_length=2, example="DE")
    state: Optional[str] = Field(None, description="Bundesland/Staat (ST)", example="NRW")
    locality: Optional[str] = Field(None, description="Stadt (L)", example="Köln")
    organization: Optional[str] = Field(None, description="Organisation (O)", example="VERITAS")
    organizational_unit: Optional[str] = Field(None, description="Organisationseinheit (OU)", example="IT")
    email: Optional[str] = Field(None, description="E-Mail-Adresse", example="admin@veritas.local")
    sans: Optional[List[str]] = Field(None, description="Subject Alternative Names", example=["www.veritas.local"])


class CertificateResponse(BaseModel):
    """Response: Zertifikat"""

    cert_id: str = Field(..., description="Zertifikats-ID")
    common_name: str = Field(..., description="Common Name")
    cert_type: str = Field(..., description="Zertifikatstyp")
    status: str = Field(..., description="Status")
    valid_from: datetime = Field(..., description="Gültig ab")
    valid_until: datetime = Field(..., description="Gültig bis")
    fingerprint: str = Field(..., description="SHA256 Fingerprint")
    serial_number: str = Field(..., description="Seriennummer")
    key_size: int = Field(..., description="Schlüsselgröße")
    created_at: datetime = Field(..., description="Erstellungsdatum")
    revoked_at: Optional[datetime] = Field(None, description="Widerrufsdatum")


class CertificateDetailResponse(CertificateResponse):
    """Response: Zertifikat mit Details"""

    cert_pem: str = Field(..., description="Zertifikat (PEM)")
    subject: dict = Field(..., description="Subject DN")
    sans: List[str] = Field(..., description="Subject Alternative Names")


class RevokeCertificateRequest(BaseModel):
    """Request: Zertifikat widerrufen"""

    reason: str = Field("unspecified", description="Widerrufsgrund", example="key_compromise")


class SignCSRRequest(BaseModel):
    """Request: CSR signieren"""

    csr_pem: str = Field(..., description="CSR (PEM-Format)")
    validity_days: int = Field(365, description="Gültigkeit in Tagen", ge=1, le=3650)
    cert_type: CertificateTypeEnum = Field(CertificateTypeEnum.SERVER, description="Zertifikatstyp")


class SignedCertificateResponse(BaseModel):
    """Response: Signiertes Zertifikat"""

    cert_id: str
    serial_number: str
    subject: str
    issuer: str
    valid_from: datetime
    valid_until: datetime
    fingerprint: str
    cert_pem: str


class CAInfoResponse(BaseModel):
    """Response: CA-Informationen"""

    ca_name: str
    initialized: bool
    certificate: dict
    statistics: dict


class StatisticsResponse(BaseModel):
    """Response: PKI-Statistiken"""

    total_certificates: int
    valid_certificates: int
    expired_certificates: int
    revoked_certificates: int
    certificates_by_type: dict
    mock_mode: bool
    ca_info: dict


# ============================================================================
# Certificate Endpoints
# ============================================================================


@router.post("/certificates", response_model=CertificateDetailResponse, status_code=201)
async def create_certificate(request: CreateCertificateRequest):
    """
    Erstellt ein neues Zertifikat.

    - **common_name**: Fully Qualified Domain Name (FQDN)
    - **validity_days**: Gültigkeit (1-3650 Tage)
    - **key_size**: 2048 oder 4096 Bit
    - **cert_type**: server, client, code_signing, email
    """
    try:
        cert = cert_manager.create_certificate(
            common_name=request.common_name,
            validity_days=request.validity_days,
            key_size=request.key_size,
            cert_type=CertificateType(request.cert_type.value),
            country=request.country,
            state=request.state,
            locality=request.locality,
            organization=request.organization,
            organizational_unit=request.organizational_unit,
            email=request.email,
            sans=request.sans,
        )
        return cert
    except InvalidCertificateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/certificates", response_model=List[CertificateResponse])
async def list_certificates(
    status: Optional[CertificateStatusEnum] = Query(None, description="Filter nach Status"),
    cert_type: Optional[CertificateTypeEnum] = Query(None, description="Filter nach Typ"),
    limit: int = Query(100, description="Max. Anzahl Ergebnisse", ge=1, le=1000),
    offset: int = Query(0, description="Offset für Pagination", ge=0),
):
    """
    Listet Zertifikate mit optionalen Filtern.

    - **status**: Filter nach Status (valid, expired, revoked, pending)
    - **cert_type**: Filter nach Typ (server, client, etc.)
    - **limit**: Max. Anzahl Ergebnisse (1-1000)
    - **offset**: Offset für Pagination
    """
    try:
        status_filter = CertificateStatus(status.value) if status else None
        type_filter = CertificateType(cert_type.value) if cert_type else None

        certs = cert_manager.list_certificates(status=status_filter, cert_type=type_filter, limit=limit, offset=offset)
        return certs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/certificates/{cert_id}", response_model=CertificateDetailResponse)
async def get_certificate(cert_id: str):
    """
    Ruft Details eines Zertifikats ab.

    - **cert_id**: Zertifikats-ID (UUID)
    """
    cert = cert_manager.get_certificate(cert_id)
    if not cert:
        raise HTTPException(status_code=404, detail=f"Certificate not found: {cert_id}")
    return cert


@router.delete("/certificates/{cert_id}")
async def revoke_certificate(cert_id: str, request: RevokeCertificateRequest = RevokeCertificateRequest()):
    """
    Widerruft ein Zertifikat.

    - **cert_id**: Zertifikats-ID
    - **reason**: Widerrufsgrund (unspecified, key_compromise, superseded, etc.)
    """
    try:
        cert_manager.revoke_certificate(cert_id, reason=request.reason)
        return {"message": "Certificate revoked successfully", "cert_id": cert_id}
    except CertificateNotFoundError:
        raise HTTPException(status_code=404, detail=f"Certificate not found: {cert_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/certificates/{cert_id}/renew", response_model=CertificateDetailResponse)
async def renew_certificate(
    cert_id: str, validity_days: int = Query(365, description="Neue Gültigkeit in Tagen", ge=1, le=3650)
):
    """
    Erneuert ein bestehendes Zertifikat.

    - **cert_id**: ID des zu erneuernden Zertifikats
    - **validity_days**: Neue Gültigkeit (1-3650 Tage)

    Das alte Zertifikat wird automatisch widerrufen.
    """
    try:
        new_cert = cert_manager.renew_certificate(cert_id, validity_days=validity_days)
        return new_cert
    except CertificateNotFoundError:
        raise HTTPException(status_code=404, detail=f"Certificate not found: {cert_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# CA Endpoints
# ============================================================================


@router.get("/ca/info", response_model=CAInfoResponse)
async def get_ca_info():
    """
    Ruft Informationen über die Certificate Authority ab.

    Gibt CA-Name, Zertifikatsdetails und Statistiken zurück.
    """
    try:
        info = ca_service.get_ca_info()
        return info
    except CANotInitializedError:
        raise HTTPException(status_code=503, detail="CA not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/ca/certificate")
async def get_ca_certificate():
    """
    Ruft das CA-Zertifikat ab (PEM-Format).

    Kann verwendet werden, um die CA als Trusted Root hinzuzufügen.
    """
    try:
        cert_pem = ca_service.get_ca_certificate()
        return {"ca_certificate": cert_pem}
    except CANotInitializedError:
        raise HTTPException(status_code=503, detail="CA not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/ca/crl")
async def get_crl():
    """
    Ruft die Certificate Revocation List (CRL) ab.

    Enthält alle widerrufenen Zertifikate.
    """
    try:
        crl_pem = ca_service.get_crl()
        return {"crl": crl_pem}
    except CANotInitializedError:
        raise HTTPException(status_code=503, detail="CA not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/ca/sign", response_model=SignedCertificateResponse, status_code=201)
async def sign_csr(request: SignCSRRequest):
    """
    Signiert einen Certificate Signing Request (CSR).

    - **csr_pem**: CSR im PEM-Format
    - **validity_days**: Gültigkeit des signierten Zertifikats (1-3650 Tage)
    - **cert_type**: Zertifikatstyp (server, client, etc.)
    """
    try:
        signed_cert = ca_service.sign_csr(
            csr_pem=request.csr_pem, validity_days=request.validity_days, cert_type=request.cert_type.value
        )
        return signed_cert
    except CANotInitializedError:
        raise HTTPException(status_code=503, detail="CA not initialized")
    except InvalidCSRError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# Statistics Endpoint
# ============================================================================


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """
    Ruft PKI-Statistiken ab.

    - Anzahl Zertifikate (gesamt, valide, abgelaufen, widerrufen)
    - Zertifikate nach Typ
    - CA-Informationen
    - Mock-Mode Status
    """
    try:
        cert_stats = cert_manager.get_statistics()

        try:
            ca_info = ca_service.get_ca_info()
        except:
            ca_info = {"initialized": False}

        return {**cert_stats, "ca_info": ca_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def health_check():
    """
    PKI Health Check

    Prüft ob PKI-Services verfügbar sind.
    """
    return {
        "status": "healthy",
        "cert_manager": "online",
        "ca_service": "online" if ca_service.ca_initialized else "not_initialized",
        "mock_mode": cert_manager.mock_mode,
    }
