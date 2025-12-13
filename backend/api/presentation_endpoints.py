"""
Presentation Canvas API Endpoints - FastAPI Routes für Presentation Canvas Agent

Endpoints:
- POST /api/presentations/generate - Präsentation generieren
- POST /api/presentations/validate_vdl - VDL validieren
- GET /api/presentations/download/{filename} - Präsentation herunterladen
"""

import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.agents.presentation_canvas_agent import PresentationCanvasAgent, VisualDescriptionLanguage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/presentations", tags=["Presentations"])


# Pydantic Models
class PresentationGenerateRequest(BaseModel):
    """Request-Modell für Präsentations-Generierung"""
    prompt: str = Field(
        ...,
        description="Nutzer-Prompt für Präsentations-Generierung",
        examples=["Erstelle eine Präsentation über BImSchG mit 3 Folien"]
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional: Zusätzlicher Kontext"
    )


class PresentationGenerateResponse(BaseModel):
    """Response-Modell für Präsentations-Generierung"""
    success: bool
    vdl: Optional[Dict[str, Any]] = None
    slides: Optional[list] = None
    pptx_path: Optional[str] = None
    slide_count: Optional[int] = None
    error: Optional[str] = None


class VDLValidateRequest(BaseModel):
    """Request-Modell für VDL-Validierung"""
    vdl: Dict[str, Any] = Field(
        ...,
        description="VDL-Spezifikation zum Validieren"
    )


class VDLValidateResponse(BaseModel):
    """Response-Modell für VDL-Validierung"""
    is_valid: bool
    error_message: Optional[str] = None


# Global Agent-Instanz
_presentation_agent: Optional[PresentationCanvasAgent] = None


def get_presentation_agent() -> PresentationCanvasAgent:
    """Singleton-Zugriff auf PresentationCanvasAgent"""
    global _presentation_agent
    if _presentation_agent is None:
        _presentation_agent = PresentationCanvasAgent()
        logger.info("PresentationCanvasAgent initialisiert")
    return _presentation_agent


@router.post("/generate", response_model=PresentationGenerateResponse)
async def generate_presentation(request: PresentationGenerateRequest):
    """
    Präsentation generieren aus Nutzer-Prompt
    
    Der Agent nutzt LLM um eine Visual Description Language (VDL) zu generieren,
    die dann in Canvas-Elemente und PowerPoint-Slides umgesetzt wird.
    
    **Neue Features (Dezember 2025):**
    - ✅ 182+ verschiedene Formen (Shapes)
    - ✅ 29 Pfeil-Typen (Arrows)
    - ✅ 29 Flussdiagramm-Formen (Flowchart)
    - ✅ Verbindungslinien (Connectors)
    - ✅ Diagramm-Templates (Organigramm, Prozessflow, Zyklus)
    - ✅ Native PowerPoint-Shapes (editierbar in PowerPoint!)
    
    **VDL-Format:**
    - Strukturierte JSON-Beschreibung visueller Elemente
    - Unterstützt: Text, Shapes, Charts, Images (AI-generiert), Connectors, Diagrams
    - Templates: flowchart, org_chart, cycle_diagram, pyramid
    - Canvas-Koordinaten: 800x600
    
    **Beispiel 1: Einfache Formen**
    
    ```json
    {
        "prompt": "Erstelle eine Folie mit einem Rechteck, einem Kreis und einem Pfeil"
    }
    ```
    
    **Beispiel 2: Flussdiagramm (BImSchG-Prozess)**
    
    ```json
    {
        "prompt": "Erstelle ein Flussdiagramm für den BImSchG-Genehmigungsprozess mit 5 Schritten: Antragstellung, Formale Prüfung, Entscheidung, Fachliche Prüfung, Genehmigung"
    }
    ```
    
    **Beispiel 3: Organigramm**
    
    ```json
    {
        "prompt": "Erstelle ein Organigramm der Umweltbehörde mit 3 Ebenen: Leitung, Abteilungen (Immissionsschutz, Naturschutz, Gewässerschutz), Teams"
    }
    ```
    
    **Beispiel 4: Zyklisches Diagramm (PDCA)**
    
    ```json
    {
        "prompt": "Visualisiere den PDCA-Zyklus (Plan-Do-Check-Act) als kreisförmiges Diagramm"
    }
    ```
    
    **Response:**
    ```json
    {
        "success": true,
        "vdl": {
            "use_native_shapes": true,
            "slides": [
                {
                    "layout": "content",
                    "elements": [
                        {
                            "type": "flowchart",
                            "steps": [
                                {"shape": "flowchart_terminator", "text": "Start"},
                                {"shape": "flowchart_process", "text": "Schritt 1"}
                            ]
                        }
                    ]
                }
            ]
        },
        "slides": [
            {
                "image_base64": "iVBORw0KGgo...",
                "png_path": "/tmp/slide_1.png",
                "slide_number": 1
            }
        ],
        "pptx_path": "/tmp/presentation_123.pptx",
        "slide_count": 1
    }
    ```
    
    **Wichtig:**
    - Setze `use_native_shapes: true` in der VDL für editierbare PowerPoint-Shapes
    - Nutze Template-basierte Diagramme (flowchart, org_chart, etc.) für beste Ergebnisse
    - 182+ verschiedene Shapes verfügbar (siehe VDL-Dokumentation)
    """
    try:
        logger.info(f"Präsentations-Generierung angefordert: {request.prompt[:100]}")
        
        agent = get_presentation_agent()
        
        result = await agent.generate_presentation(
            user_prompt=request.prompt,
            context=request.context
        )
        
        logger.info(f"Präsentation generiert: {result.get('slide_count', 0)} Folien")
        
        return PresentationGenerateResponse(**result)
    
    except Exception as e:
        logger.error(f"Fehler bei Präsentations-Generierung: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate_vdl", response_model=VDLValidateResponse)
async def validate_vdl(request: VDLValidateRequest):
    """
    Visual Description Language (VDL) validieren
    
    Prüft ob eine VDL-Spezifikation korrekt strukturiert ist.
    
    **Beispiel:**
    
    ```json
    {
        "vdl": {
            "slides": [
                {
                    "layout": "title_slide",
                    "elements": [
                        {
                            "type": "text",
                            "content": "Titel",
                            "position": {"x": 100, "y": 200},
                            "size": {"width": 600, "height": 100},
                            "properties": {"font_size": 44}
                        }
                    ]
                }
            ]
        }
    }
    ```
    
    **Response:**
    ```json
    {
        "is_valid": true,
        "error_message": null
    }
    ```
    """
    try:
        is_valid, error_message = VisualDescriptionLanguage.validate(request.vdl)
        
        return VDLValidateResponse(
            is_valid=is_valid,
            error_message=error_message
        )
    
    except Exception as e:
        logger.error(f"VDL-Validierung fehlgeschlagen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vdl_example")
async def get_vdl_example():
    """
    Beispiel-VDL abrufen
    
    Gibt eine vollständige Visual Description Language (VDL) Spezifikation
    als Beispiel zurück.
    
    **Response:**
    ```json
    {
        "metadata": {
            "title": "Beispiel-Präsentation",
            "author": "VERITAS Canvas Agent",
            "theme": "professional"
        },
        "slides": [...]
    }
    ```
    """
    try:
        example_vdl = VisualDescriptionLanguage.create_example()
        return example_vdl
    
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des VDL-Beispiels: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_presentation(filename: str):
    """
    Präsentations-Datei herunterladen
    
    **Parameter:**
    - `filename`: Dateiname (mit Extension .pptx oder .png)
    
    **Beispiel:**
    ```
    GET /api/presentations/download/presentation_123.pptx
    ```
    """
    try:
        agent = get_presentation_agent()
        file_path = agent.output_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Datei nicht gefunden: {filename}")
        
        # Media-Type basierend auf Extension
        if filename.endswith('.pptx'):
            media_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        elif filename.endswith('.png'):
            media_type = 'image/png'
        else:
            media_type = 'application/octet-stream'
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Download: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health-Check für Presentation-Service
    
    **Response:**
    ```json
    {
        "status": "healthy",
        "agent_initialized": true,
        "output_dir": "/tmp/veritas_presentations",
        "vdl_element_types": ["text", "shape", "connector", "flowchart", ...],
        "vdl_layout_types": ["title_slide", "content", ...],
        "capabilities": {
            "total_shapes": 182,
            "arrows": 29,
            "flowchart_shapes": 29,
            "connectors": 3,
            "templates": ["flowchart", "org_chart", "cycle_diagram", "pyramid"],
            "native_powerpoint_shapes": true,
            "smartart_support": false
        }
    }
    ```
    """
    try:
        agent = get_presentation_agent()
        
        return {
            "status": "healthy",
            "agent_initialized": True,
            "output_dir": str(agent.output_dir),
            "vdl_element_types": VisualDescriptionLanguage.ELEMENT_TYPES,
            "vdl_layout_types": VisualDescriptionLanguage.LAYOUT_TYPES,
            "vdl_shape_types": VisualDescriptionLanguage.SHAPE_TYPES,
            "vdl_connector_types": VisualDescriptionLanguage.CONNECTOR_TYPES,
            "capabilities": {
                "total_shapes": 182,
                "arrows": 29,
                "flowchart_shapes": 29,
                "connectors": len(VisualDescriptionLanguage.CONNECTOR_TYPES),
                "templates": ["flowchart", "org_chart", "cycle_diagram", "pyramid"],
                "native_powerpoint_shapes": True,
                "smartart_support": False,
                "description": "Shapes werden aus nativen PowerPoint-Objekten erstellt, kein natives SmartArt (wird nachgebaut)"
            }
        }
    
    except Exception as e:
        logger.error(f"Health-Check fehlgeschlagen: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "agent_initialized": False,
            "error": str(e)
        }
