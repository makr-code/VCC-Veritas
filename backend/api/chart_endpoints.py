"""
Chart API Endpoints - FastAPI Routes für Vector Chart Agent

Endpoints:
- POST /api/charts/generate - Chart generieren
- GET /api/charts/templates - Verfügbare Templates
- GET /api/charts/download/{filename} - Chart-Download
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.agents.vector_chart_agent import VectorChartAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/charts", tags=["Charts"])


# Pydantic Models
class ChartGenerateRequest(BaseModel):
    """Request-Modell für Chart-Generierung"""
    prompt: str = Field(
        ..., 
        description="Nutzer-Prompt für Chart-Generierung",
        examples=["Erstelle ein Bar Chart mit BImSchG-Anlagen pro Kategorie"]
    )
    template: Optional[str] = Field(
        None,
        description="Optional: Template-Name verwenden",
        examples=["bimschg_overview", "wka_leistung"]
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional: Zusätzlicher Kontext"
    )


class ChartGenerateResponse(BaseModel):
    """Response-Modell für Chart-Generierung"""
    success: bool
    chart_type: str
    title: str
    data: Dict[str, Any]
    image_base64: str
    exports: Dict[str, str]
    error: Optional[str] = None


class TemplateInfo(BaseModel):
    """Template-Informationen"""
    name: str
    title: str
    type: str


# Global Agent-Instanz (wird beim Start initialisiert)
_chart_agent: Optional[VectorChartAgent] = None


def get_chart_agent() -> VectorChartAgent:
    """Singleton-Zugriff auf VectorChartAgent"""
    global _chart_agent
    if _chart_agent is None:
        _chart_agent = VectorChartAgent()
        logger.info("VectorChartAgent initialisiert")
    return _chart_agent


@router.post("/generate", response_model=ChartGenerateResponse)
async def generate_chart(request: ChartGenerateRequest):
    """
    Chart generieren aus Nutzer-Prompt
    
    **Beispiele:**
    
    ```json
    {
        "prompt": "Erstelle ein Bar Chart mit BImSchG-Anlagen pro Kategorie"
    }
    ```
    
    ```json
    {
        "prompt": "Zeige ein Pie Chart der WKA-Leistung",
        "template": "wka_leistung"
    }
    ```
    
    **Response:**
    ```json
    {
        "success": true,
        "chart_type": "bar",
        "title": "BImSchG-Anlagen nach Kategorie",
        "data": {
            "labels": ["1.1 Feuerung", "1.2 Gasturbine", ...],
            "values": [850, 520, ...]
        },
        "image_base64": "iVBORw0KGgo...",
        "exports": {
            "png": "/tmp/veritas_charts/chart_123.png",
            "svg": "/tmp/veritas_charts/chart_123.svg",
            "pdf": "/tmp/veritas_charts/chart_123.pdf",
            "pptx": "/tmp/veritas_charts/chart_123.pptx"
        }
    }
    ```
    """
    try:
        logger.info(f"Chart-Generierung angefordert: {request.prompt[:100]}")
        
        agent = get_chart_agent()
        
        result = await agent.generate_chart(
            user_prompt=request.prompt,
            context=request.context,
            template=request.template
        )
        
        if not result.get('success', False):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Chart-Generierung fehlgeschlagen')
            )
        
        logger.info(f"Chart erfolgreich generiert: {result.get('chart_type')}")
        
        return ChartGenerateResponse(**result)
    
    except Exception as e:
        logger.error(f"Fehler bei Chart-Generierung: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=list[TemplateInfo])
async def list_templates():
    """
    Liste aller verfügbaren Chart-Templates
    
    **Response:**
    ```json
    [
        {
            "name": "bimschg_overview",
            "title": "BImSchG-Anlagen nach Kategorie",
            "type": "bar"
        },
        {
            "name": "wka_leistung",
            "title": "WKA-Leistung nach Status",
            "type": "pie"
        }
    ]
    ```
    """
    try:
        agent = get_chart_agent()
        templates = agent.list_templates()
        return templates
    
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_chart(
    filename: str,
    format: str = Query("png", regex="^(png|svg|pdf|pptx)$")
):
    """
    Chart-Datei herunterladen
    
    **Parameter:**
    - `filename`: Dateiname (ohne Extension)
    - `format`: Dateiformat (png, svg, pdf, pptx)
    
    **Beispiel:**
    ```
    GET /api/charts/download/chart_123?format=png
    ```
    """
    try:
        agent = get_chart_agent()
        file_path = agent.output_dir / f"{filename}.{format}"
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Datei nicht gefunden: {filename}.{format}")
        
        media_types = {
            'png': 'image/png',
            'svg': 'image/svg+xml',
            'pdf': 'application/pdf',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }
        
        return FileResponse(
            path=str(file_path),
            media_type=media_types.get(format, 'application/octet-stream'),
            filename=f"{filename}.{format}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Download: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health-Check für Chart-Service
    
    **Response:**
    ```json
    {
        "status": "healthy",
        "agent_initialized": true,
        "templates_available": 4
    }
    ```
    """
    try:
        agent = get_chart_agent()
        templates = agent.list_templates()
        
        return {
            "status": "healthy",
            "agent_initialized": True,
            "templates_available": len(templates),
            "output_dir": str(agent.output_dir)
        }
    
    except Exception as e:
        logger.error(f"Health-Check fehlgeschlagen: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "agent_initialized": False,
            "error": str(e)
        }
