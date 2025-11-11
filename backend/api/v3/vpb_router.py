"""
VERITAS API v3 - VPB Router

VPB (Verwaltungspraxis der Bundesbehörden) Endpoints.
Spezialisierte Queries für Verwaltungsrecht und Verwaltungspraxis.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from .models import ErrorResponse, VPBAnalysisRequest, VPBAnalysisResponse, VPBDocument, VPBQueryRequest, VPBQueryResponse
from .service_integration import execute_query_with_pipeline, get_services_from_app

logger = logging.getLogger(__name__)

# ============================================================================
# Router Setup
# ============================================================================

vpb_router = APIRouter(prefix="/vpb", tags=["VPB - Verwaltungspraxis"])

# ============================================================================
# Helper Functions
# ============================================================================


def get_backend_services(request: Request):
    """Hole Backend Services aus App State"""
    return get_services_from_app(request.app.state)


def format_vpb_documents(sources: List[dict]) -> List[VPBDocument]:
    """Formatiere Sources als VPB Dokumente"""
    documents = []
    for source in sources[:10]:  # Max 10 Dokumente
        doc = VPBDocument(
            document_id=source.get("id", f"vpb_{uuid.uuid4().hex[:8]}"),
            title=source.get("title", source.get("file", "Unbekanntes Dokument")),
            authority=source.get("authority", None),
            year=source.get("year", None),
            reference=source.get("reference", None),
            content_preview=source.get("content", "")[:200] + "..." if source.get("content") else None,
            relevance_score=source.get("confidence", source.get("score", None)),
        )
        documents.append(doc)
    return documents


# ============================================================================
# VPB Endpoints
# ============================================================================


@vpb_router.post("/query", response_model=VPBQueryResponse)
async def vpb_query(query_req: VPBQueryRequest, request: Request):
    """
    VPB-spezifische Query

    Führt eine spezialisierte Query für Verwaltungspraxis durch.
    Nutzt VPB-Filter und kontextuelle Informationen.
    """
    logger.info(f"🏛️ VPB Query: {query_req.query[:50]}...")

    try:
        services = get_backend_services(request)

        # Pipeline für VPB-Query nutzen
        pipeline_result = await execute_query_with_pipeline(
            query_text=query_req.query,
            intelligent_pipeline=services["intelligent_pipeline"],
            session_id=query_req.session_id,
            mode="vpb",  # VPB Mode aktivieren
            enable_commentary=True,
            timeout=60,
        )

        # VPB Dokumente formatieren
        vpb_documents = format_vpb_documents(pipeline_result.get("sources", []))

        # Metadata erweitern
        metadata = pipeline_result.get("metadata", {})
        if query_req.filters:
            metadata["filters_applied"] = query_req.filters
        metadata["document_count"] = len(vpb_documents)

        response = VPBQueryResponse(
            query_id=pipeline_result.get("query_id", f"vpb_{uuid.uuid4().hex[:8]}"),
            content=pipeline_result["content"],
            documents=vpb_documents,
            metadata=metadata,
            duration=pipeline_result.get("duration"),
        )

        logger.info(f"✅ VPB Query erfolgreich: {len(vpb_documents)} Dokumente gefunden")
        return response

    except Exception as e:
        logger.error(f"❌ VPB Query Fehler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"VPB Query fehlgeschlagen: {str(e)}")


@vpb_router.get("/documents", response_model=List[VPBDocument])
async def get_vpb_documents(request: Request, year: Optional[int] = None, authority: Optional[str] = None, limit: int = 20):
    """
    Liste VPB Dokumente

    Ruft eine Liste von VPB-Dokumenten ab, optional gefiltert nach Jahr und Behörde.
    """
    logger.info(f"📚 VPB Dokumente abrufen (Year: {year}, Authority: {authority}, Limit: {limit})")

    try:
        services = get_backend_services(request)

        # Fallback: Mock-Dokumente wenn UDS3 nicht verfügbar
        if not services.get("uds3"):
            logger.warning("⚠️ UDS3 nicht verfügbar - Nutze Fallback-Dokumente")
            mock_documents = [
                VPBDocument(
                    document_id="vpb_001",
                    title="Verwaltungsverfahren nach VwVfG",
                    authority="Bundesverwaltungsamt",
                    year=2023,
                    reference="VPB 2023/45",
                    content_preview="Grundlagen des Verwaltungsverfahrens nach dem Verwaltungsverfahrensgesetz...",
                    relevance_score=0.95,
                ),
                VPBDocument(
                    document_id="vpb_002",
                    title="Rechtsbehelfsbelehrung in Bescheiden",
                    authority="BMI",
                    year=2023,
                    reference="VPB 2023/67",
                    content_preview="Anforderungen an die Rechtsbehelfsbelehrung in Verwaltungsbescheiden...",
                    relevance_score=0.92,
                ),
            ]

            # Filter anwenden
            filtered = mock_documents
            if year:
                filtered = [d for d in filtered if d.year == year]
            if authority:
                filtered = [d for d in filtered if authority.lower() in (d.authority or "").lower()]

            return filtered[:limit]

        # TODO: UDS3 Integration für echte VPB-Dokumente
        # documents = await retrieve_vpb_documents_from_uds3(
        #     uds3=services["uds3"],
        #     year=year,
        #     authority=authority,
        #     limit=limit
        # )

        raise HTTPException(status_code=503, detail="VPB Dokumenten-Abruf noch nicht implementiert")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ VPB Dokumente Fehler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"VPB Dokumente konnten nicht abgerufen werden: {str(e)}")


@vpb_router.post("/analysis", response_model=VPBAnalysisResponse)
async def analyze_administrative_process(analysis_req: VPBAnalysisRequest, request: Request):
    """
    Verwaltungsprozess-Analyse

    Analysiert einen Verwaltungsprozess und gibt Empfehlungen sowie rechtliche Referenzen.
    """
    logger.info(f"🔍 VPB Prozessanalyse: {analysis_req.process_description[:50]}...")

    try:
        services = get_backend_services(request)

        # Erweiterte Query für Analyse
        analysis_query = """
        Analysiere den folgenden Verwaltungsprozess:

        {analysis_req.process_description}

        Bitte gib eine detaillierte Analyse mit:
        1. Rechtliche Grundlagen und Vorschriften
        2. Empfehlungen für die Prozessoptimierung
        3. Risikobewertung (rechtliche und organisatorische Risiken)
        4. Verweise auf relevante VPB-Dokumente
        """

        # Pipeline für Analyse nutzen
        pipeline_result = await execute_query_with_pipeline(
            query_text=analysis_query,
            intelligent_pipeline=services["intelligent_pipeline"],
            mode="vpb",
            enable_commentary=True,
            timeout=90,  # Längerer Timeout für Analyse
        )

        # Extrahiere Empfehlungen aus Response
        content = pipeline_result["content"]
        recommendations = []
        if "Empfehlungen" in content or "empfohlen" in content.lower():
            # Simple Empfehlungs-Extraktion (könnte durch LLM verbessert werden)
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ["empfehlung", "sollte", "muss", "beachten"]):
                    recommendations.append(line.strip())

        if not recommendations:
            recommendations = [
                "Prüfen Sie die Einhaltung der VwVfG-Vorschriften",
                "Dokumentieren Sie alle Verfahrensschritte nachvollziehbar",
                "Stellen Sie die Rechtsbehelfsbelehrung sicher",
            ]

        # VPB Dokumente als rechtliche Referenzen
        legal_references = format_vpb_documents(pipeline_result.get("sources", []))

        # Risikobewertung
        risk_assessment = {
            "legal_risk": "medium",
            "process_complexity": "medium",
            "recommendation_priority": "high",
            "compliance_check_required": True,
        }

        response = VPBAnalysisResponse(
            analysis_id=f"analysis_{uuid.uuid4().hex[:8]}",
            summary=content,
            recommendations=recommendations[:5],  # Top 5 Empfehlungen
            legal_references=legal_references,
            risk_assessment=risk_assessment,
        )

        logger.info(f"✅ VPB Analyse erfolgreich: {len(recommendations)} Empfehlungen, {len(legal_references)} Referenzen")
        return response

    except Exception as e:
        logger.error(f"❌ VPB Analyse Fehler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"VPB Analyse fehlgeschlagen: {str(e)}")


# ============================================================================
# Router Export
# ============================================================================

__all__ = ["vpb_router"]
