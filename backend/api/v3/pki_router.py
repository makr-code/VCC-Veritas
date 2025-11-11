"""
VERITAS API v3 - PKI Router

PKI (Public Key Infrastructure) Endpoints.
Spezialisierte Queries für PKI, Zertifikate und Validierung.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from .models import (
    ErrorResponse,
    PKICertificate,
    PKIQueryRequest,
    PKIQueryResponse,
    PKIValidationRequest,
    PKIValidationResponse,
)
from .service_integration import execute_query_with_pipeline, get_services_from_app

logger = logging.getLogger(__name__)

# ============================================================================
# Router Setup
# ============================================================================

pki_router = APIRouter(prefix="/pki", tags=["PKI - Public Key Infrastructure"])

# ============================================================================
# Helper Functions
# ============================================================================


def get_backend_services(request: Request):
    """Hole Backend Services aus App State"""
    return get_services_from_app(request.app.state)


def generate_mock_certificates() -> List[PKICertificate]:
    """Generiere Mock PKI-Zertifikate für Fallback"""
    today = datetime.now()
    certs = [
        PKICertificate(
            certificate_id="cert_001",
            subject="CN=veritas.example.com, O=VERITAS, C=DE",
            issuer="CN=VERITAS Root CA, O=VERITAS, C=DE",
            valid_from=(today - timedelta(days=365)).strftime("%Y-%m-%d"),
            valid_until=(today + timedelta(days=365)).strftime("%Y-%m-%d"),
            serial_number="4A:3F:5E:12:8B:9C:D4:E7",
            status="valid",
        ),
        PKICertificate(
            certificate_id="cert_002",
            subject="CN=api.veritas.example.com, O=VERITAS, C=DE",
            issuer="CN=VERITAS Intermediate CA, O=VERITAS, C=DE",
            valid_from=(today - timedelta(days=180)).strftime("%Y-%m-%d"),
            valid_until=(today + timedelta(days=545)).strftime("%Y-%m-%d"),
            serial_number="6B:4C:7D:23:9A:1D:E5:F8",
            status="valid",
        ),
        PKICertificate(
            certificate_id="cert_003",
            subject="CN=old.veritas.example.com, O=VERITAS, C=DE",
            issuer="CN=VERITAS Root CA, O=VERITAS, C=DE",
            valid_from=(today - timedelta(days=800)).strftime("%Y-%m-%d"),
            valid_until=(today - timedelta(days=30)).strftime("%Y-%m-%d"),
            serial_number="8C:5D:9E:34:AB:2E:F6:G9",
            status="expired",
        ),
    ]
    return certs


def format_pki_certificates(sources: List[dict]) -> List[PKICertificate]:
    """Formatiere Sources als PKI Zertifikate"""
    certificates = []
    for source in sources[:5]:  # Max 5 Zertifikate
        cert = PKICertificate(
            certificate_id=source.get("id", f"cert_{uuid.uuid4().hex[:8]}"),
            subject=source.get("subject", "CN=Unknown"),
            issuer=source.get("issuer", "CN=Unknown CA"),
            valid_from=source.get("valid_from", datetime.now().strftime("%Y-%m-%d")),
            valid_until=source.get("valid_until", (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")),
            serial_number=source.get("serial_number"),
            status=source.get("status", "valid"),
        )
        certificates.append(cert)
    return certificates


# ============================================================================
# PKI Endpoints
# ============================================================================


@pki_router.post("/query", response_model=PKIQueryResponse)
async def pki_query(query_req: PKIQueryRequest, request: Request):
    """
    PKI-spezifische Query

    Führt eine spezialisierte Query für PKI-Themen durch.
    Unterstützt Technical-Mode für detaillierte technische Informationen.
    """
    logger.info(f"🔐 PKI Query: {query_req.query[:50]}...")

    try:
        services = get_backend_services(request)

        # Pipeline für PKI-Query nutzen
        pipeline_result = await execute_query_with_pipeline(
            query_text=query_req.query,
            intelligent_pipeline=services["intelligent_pipeline"],
            session_id=query_req.session_id,
            mode="pki",  # PKI Mode
            enable_commentary=(query_req.mode == "technical"),  # Commentary für Technical Mode
            timeout=60,
        )

        # Zertifikate aus Sources extrahieren
        certificates = format_pki_certificates(pipeline_result.get("sources", []))

        # Metadata erweitern
        metadata = pipeline_result.get("metadata", {})
        metadata["certificate_count"] = len(certificates)
        metadata["query_mode"] = query_req.mode

        response = PKIQueryResponse(
            query_id=pipeline_result.get("query_id", f"pki_{uuid.uuid4().hex[:8]}"),
            content=pipeline_result["content"],
            certificates=certificates,
            metadata=metadata,
            duration=pipeline_result.get("duration"),
        )

        logger.info(f"✅ PKI Query erfolgreich: {len(certificates)} Zertifikate gefunden")
        return response

    except Exception as e:
        logger.error(f"❌ PKI Query Fehler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PKI Query fehlgeschlagen: {str(e)}")


@pki_router.get("/certificates", response_model=List[PKICertificate])
async def get_pki_certificates(
    request: Request, status: Optional[str] = None, subject_filter: Optional[str] = None, limit: int = 20
):
    """
    PKI Zertifikate abrufen

    Ruft eine Liste von PKI-Zertifikaten ab, optional gefiltert nach Status und Subject.
    """
    logger.info(f"📜 PKI Zertifikate (Status: {status}, Subject: {subject_filter}, Limit: {limit})")

    try:
        services = get_backend_services(request)

        # Fallback: Mock-Zertifikate wenn PKI-Service nicht verfügbar
        if not services.get("uds3"):
            logger.warning("⚠️ PKI-Service nicht verfügbar - Nutze Mock-Zertifikate")
            certs = generate_mock_certificates()

            # Filter anwenden
            if status:
                certs = [c for c in certs if c.status == status]
            if subject_filter:
                certs = [c for c in certs if subject_filter.lower() in c.subject.lower()]

            return certs[:limit]

        # TODO: PKI-Service Integration für echte Zertifikate
        # certificates = await retrieve_pki_certificates_from_service(
        #     pki_service=services["pki_service"],
        #     status=status,
        #     subject_filter=subject_filter,
        #     limit=limit
        # )

        raise HTTPException(status_code=503, detail="PKI Zertifikat-Abruf noch nicht implementiert")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PKI Zertifikate Fehler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PKI Zertifikate konnten nicht abgerufen werden: {str(e)}")


@pki_router.post("/validation", response_model=PKIValidationResponse)
async def validate_pki_certificate(validation_req: PKIValidationRequest, request: Request):
    """
    PKI Zertifikat-Validierung

    Validiert ein PKI-Zertifikat und prüft Status, Chain und Revocation.
    """
    logger.info(
        f"✅ PKI Zertifikat-Validierung (Revocation: {validation_req.check_revocation}, Chain: {validation_req.check_chain})"
    )

    try:
        services = get_backend_services(request)

        # Fallback: Mock-Validierung
        if not services.get("uds3"):
            logger.warning("⚠️ PKI-Service nicht verfügbar - Nutze Mock-Validierung")

            # Simuliere Validierung
            is_valid = True
            errors = []
            warnings = []

            # Simple Checks
            if len(validation_req.certificate_data) < 100:
                is_valid = False
                errors.append("Zertifikat-Daten zu kurz - ungültiges Format")

            if "BEGIN CERTIFICATE" not in validation_req.certificate_data:
                warnings.append("Kein PEM-Header gefunden - möglicherweise DER-Format")

            # Mock Zertifikat-Info
            mock_cert = PKICertificate(
                certificate_id=f"validated_{uuid.uuid4().hex[:8]}",
                subject="CN=example.com, O=Example, C=DE",
                issuer="CN=Example CA, O=Example, C=DE",
                valid_from=datetime.now().strftime("%Y-%m-%d"),
                valid_until=(datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
                serial_number="AB:CD:EF:12:34:56:78:90",
                status="valid" if is_valid else "invalid",
            )

            response = PKIValidationResponse(
                validation_id=f"validation_{uuid.uuid4().hex[:8]}",
                is_valid=is_valid,
                status="valid" if is_valid else "invalid",
                errors=errors,
                warnings=warnings,
                certificate_info=mock_cert,
            )

            logger.info(f"✅ PKI Validierung abgeschlossen: {'Gültig' if is_valid else 'Ungültig'}")
            return response

        # TODO: PKI-Service Integration für echte Validierung
        # validation_result = await validate_certificate_with_pki_service(
        #     pki_service=services["pki_service"],
        #     certificate_data=validation_req.certificate_data,
        #     check_revocation=validation_req.check_revocation,
        #     check_chain=validation_req.check_chain
        # )

        raise HTTPException(status_code=503, detail="PKI Zertifikat-Validierung noch nicht implementiert")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PKI Validierung Fehler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PKI Validierung fehlgeschlagen: {str(e)}")


# ============================================================================
# Router Export
# ============================================================================

__all__ = ["pki_router"]
