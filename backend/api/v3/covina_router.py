"""
VERITAS API v3 - COVINA Router

COVINA (COVID-19 Intelligence Agent) Endpoints.
Spezialisierte Queries für COVID-19 Daten, Statistiken und Reports.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from .models import COVINAQueryRequest, COVINAQueryResponse, COVINAReport, COVINAStatistics, ErrorResponse
from .service_integration import execute_query_with_pipeline, get_services_from_app

logger = logging.getLogger(__name__)

# ============================================================================
# Router Setup
# ============================================================================

covina_router = APIRouter(prefix="/covina", tags=["COVINA - COVID-19 Intelligence"])

# ============================================================================
# Helper Functions
# ============================================================================


def get_backend_services(request: Request):
    """Hole Backend Services aus App State"""
    return get_services_from_app(request.app.state)


def generate_mock_statistics() -> List[COVINAStatistics]:
    """Generiere Mock COVID-19 Statistiken für Fallback"""
    today = datetime.now()
    stats = []

    regions = ["Deutschland", "Bayern", "Nordrhein-Westfalen", "Baden-Württemberg"]
    for i, region in enumerate(regions):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        stats.append(
            COVINAStatistics(
                region=region,
                date=date,
                cases=1000 + i * 100,
                incidence=50.5 + i * 5.2,
                r_value=0.95 + i * 0.05,
                data_source="RKI",
            )
        )

    return stats


# ============================================================================
# COVINA Endpoints
# ============================================================================


@covina_router.post("/query", response_model=COVINAQueryResponse)
async def covina_query(query_req: COVINAQueryRequest, request: Request):
    """
    COVINA-spezifische Query

    Führt eine spezialisierte Query für COVID-19-Daten durch.
    Unterstützt Statistik-Mode für reine Datenabfragen.
    """
    logger.info(f"🦠 COVINA Query: {query_req.query[:50]}...")

    try:
        services = get_backend_services(request)

        # Pipeline für COVINA-Query nutzen
        pipeline_result = await execute_query_with_pipeline(
            query_text=query_req.query,
            intelligent_pipeline=services["intelligent_pipeline"],
            session_id=query_req.session_id,
            mode="covina",  # COVINA Mode
            enable_commentary=(query_req.mode != "statistics"),  # Kein Commentary bei reinen Stats
            timeout=60,
        )

        # Statistiken aus Sources extrahieren oder generieren
        statistics = []
        if query_req.mode == "statistics":
            # Im Statistics-Mode: Versuche strukturierte Daten zu extrahieren
            # TODO: Integration mit UDS3 für echte COVID-Daten
            statistics = generate_mock_statistics()

        # Reports (falls vorhanden)
        reports = []

        # Metadata erweitern
        metadata = pipeline_result.get("metadata", {})
        if query_req.time_range:
            metadata["time_range"] = query_req.time_range
        metadata["statistics_count"] = len(statistics)
        metadata["reports_count"] = len(reports)

        response = COVINAQueryResponse(
            query_id=pipeline_result.get("query_id", f"covina_{uuid.uuid4().hex[:8]}"),
            content=pipeline_result["content"],
            statistics=statistics,
            reports=reports,
            metadata=metadata,
            duration=pipeline_result.get("duration"),
        )

        logger.info(f"✅ COVINA Query erfolgreich: {len(statistics)} Statistiken")
        return response

    except Exception as e:
        logger.error(f"❌ COVINA Query Fehler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"COVINA Query fehlgeschlagen: {str(e)}")


@covina_router.get("/statistics", response_model=List[COVINAStatistics])
async def get_covina_statistics(
    request: Request,
    region: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
):
    """
    COVID-19 Statistiken abrufen

    Ruft COVID-19 Statistiken ab, optional gefiltert nach Region und Zeitraum.
    """
    logger.info(f"📊 COVINA Statistiken (Region: {region}, From: {date_from}, To: {date_to})")

    try:
        services = get_backend_services(request)

        # Fallback: Mock-Statistiken wenn UDS3 nicht verfügbar
        if not services.get("uds3"):
            logger.warning("⚠️ UDS3 nicht verfügbar - Nutze Mock-Statistiken")
            stats = generate_mock_statistics()

            # Filter anwenden
            if region:
                stats = [s for s in stats if region.lower() in s.region.lower()]

            return stats[:limit]

        # TODO: UDS3 Integration für echte COVID-Statistiken
        # statistics = await retrieve_covina_statistics_from_uds3(
        #     uds3=services["uds3"],
        #     region=region,
        #     date_from=date_from,
        #     date_to=date_to,
        #     limit=limit
        # )

        raise HTTPException(status_code=503, detail="COVINA Statistik-Abruf noch nicht implementiert")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ COVINA Statistiken Fehler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"COVINA Statistiken konnten nicht abgerufen werden: {str(e)}")


@covina_router.get("/reports", response_model=List[COVINAReport])
async def get_covina_reports(request: Request, date_from: Optional[str] = None, limit: int = 10):
    """
    COVINA Reports abrufen

    Ruft generierte COVID-19 Intelligence Reports ab.
    """
    logger.info(f"📄 COVINA Reports (From: {date_from}, Limit: {limit})")

    try:
        services = get_backend_services(request)

        # Fallback: Mock-Reports
        if not services.get("uds3"):
            logger.warning("⚠️ UDS3 nicht verfügbar - Nutze Mock-Reports")

            today = datetime.now()
            mock_reports = [
                COVINAReport(
                    report_id="covina_report_001",
                    title="Wöchentlicher COVID-19 Lagebericht",
                    date=today.strftime("%Y-%m-%d"),
                    summary="Zusammenfassung der COVID-19 Situation in Deutschland. Inzidenz leicht rückläufig.",
                    statistics=generate_mock_statistics()[:2],
                ),
                COVINAReport(
                    report_id="covina_report_002",
                    title="Monatlicher Trend-Report",
                    date=(today - timedelta(days=7)).strftime("%Y-%m-%d"),
                    summary="Analyse der COVID-19 Trends über den letzten Monat.",
                    statistics=generate_mock_statistics()[2:],
                ),
            ]

            return mock_reports[:limit]

        # TODO: UDS3 Integration für echte Reports
        raise HTTPException(status_code=503, detail="COVINA Report-Abruf noch nicht implementiert")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ COVINA Reports Fehler: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"COVINA Reports konnten nicht abgerufen werden: {str(e)}")


# ============================================================================
# Router Export
# ============================================================================

__all__ = ["covina_router"]
