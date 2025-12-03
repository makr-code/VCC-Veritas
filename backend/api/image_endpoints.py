"""
Image Generation & Analysis API Endpoints

FastAPI Endpoints für AI Image Generator Agent:
- Bildgenerierung (SwarmUI, Stable Diffusion, DALL-E)
- Bildanalyse (Vision Models: LLaVA, BLIP, GPT-4 Vision)
- Integration für Covina Ingestion
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
import base64

from backend.agents.ai_image_generator import AIImageGenerator

logger = logging.getLogger(__name__)

# Router erstellen
router = APIRouter(prefix="/api/images", tags=["images"])

# Pydantic Models
class ImageGenerationRequest(BaseModel):
    """Request für Bildgenerierung"""
    prompt: str = Field(..., description="Text-Beschreibung des Bildes")
    generator: Optional[str] = Field(None, description="AI Generator (swarmui, stable_diffusion, comfyui, dalle)")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Generator-spezifische Parameter")
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "Photorealistic wind turbine farm at sunset, beautiful landscape",
                "generator": "swarmui",
                "properties": {
                    "width": 1024,
                    "height": 1024,
                    "steps": 30,
                    "cfg_scale": 7.5,
                    "model": "sd_xl_base_1.0.safetensors"
                }
            }
        }


class ImageGenerationResponse(BaseModel):
    """Response nach Bildgenerierung"""
    success: bool
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    generator: Optional[str] = None
    prompt: Optional[str] = None
    is_placeholder: Optional[bool] = False
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Response für Health-Check"""
    generator: str
    api_url: str
    available: bool
    status_code: Optional[int] = None
    error: Optional[str] = None


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest):
    """
    Generiere Bild mit AI Image Generator
    
    Unterstützt:
    - SwarmUI (Stable Diffusion Web UI)
    - Stable Diffusion WebUI (Automatic1111)
    - ComfyUI
    - DALL-E (OpenAI)
    
    Bei nicht-verfügbaren Generatoren wird ein Platzhalter-Bild erstellt.
    """
    try:
        generator = AIImageGenerator(generator_type=request.generator)
        result = await generator.generate_image(request.prompt, request.properties)
        
        return ImageGenerationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in image generation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{generator_type}", response_model=HealthCheckResponse)
async def health_check(generator_type: str):
    """
    Prüfe ob Generator verfügbar ist
    
    Args:
        generator_type: swarmui, stable_diffusion, comfyui, dalle
    """
    try:
        generator = AIImageGenerator(generator_type=generator_type)
        result = await generator.health_check()
        
        return HealthCheckResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generators")
async def list_generators():
    """
    Liste alle unterstützten Generatoren
    """
    return {
        "generators": [
            {
                "name": "swarmui",
                "description": "SwarmUI - Modern Stable Diffusion Web UI",
                "default_url": "http://localhost:7801/api",
                "models": ["sd_xl_base_1.0", "sd_1.5", "sd_2.1"],
                "features": ["txt2img", "img2img", "inpainting", "outpainting"]
            },
            {
                "name": "stable_diffusion",
                "description": "Stable Diffusion WebUI (Automatic1111)",
                "default_url": "http://localhost:7860/sdapi/v1",
                "models": ["custom models via checkpoints"],
                "features": ["txt2img", "img2img", "extras", "png_info"]
            },
            {
                "name": "comfyui",
                "description": "ComfyUI - Node-based Workflow System",
                "default_url": "http://localhost:8188/api",
                "models": ["workflow-based"],
                "features": ["custom_workflows", "nodes"]
            },
            {
                "name": "dalle",
                "description": "DALL-E (OpenAI)",
                "default_url": "https://api.openai.com/v1/images/generations",
                "models": ["dall-e-3", "dall-e-2"],
                "features": ["txt2img", "variations", "edits"]
            }
        ]
    }


@router.get("/config")
async def get_config():
    """
    Hole aktuelle Generator-Konfiguration aus Umgebungsvariablen
    """
    import os
    
    return {
        "active_generator": os.getenv('AI_IMAGE_GENERATOR', 'swarmui'),
        "swarmui_url": os.getenv('SWARMUI_URL', 'http://localhost:7801/api'),
        "sd_webui_url": os.getenv('SD_WEBUI_URL', 'http://localhost:7860/sdapi/v1'),
        "comfyui_url": os.getenv('COMFYUI_URL', 'http://localhost:8188/api'),
        "output_dir": os.getenv('VERITAS_IMAGE_DIR', '/tmp/veritas_images'),
        "api_key_configured": bool(os.getenv('AI_IMAGE_API_KEY'))
    }


@router.post("/batch", response_model=List[ImageGenerationResponse])
async def generate_batch(requests: List[ImageGenerationRequest], background_tasks: BackgroundTasks):
    """
    Generiere mehrere Bilder in einem Request
    
    Nützlich für Präsentationen mit mehreren AI-Bildern
    """
    try:
        results = []
        
        for req in requests:
            generator = AIImageGenerator(generator_type=req.generator)
            result = await generator.generate_image(req.prompt, req.properties)
            results.append(ImageGenerationResponse(**result))
        
        return results
        
    except Exception as e:
        logger.error(f"Error in batch generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Image Analysis Endpoints (Vision Models)
# ============================================================================

class ImageAnalysisRequest(BaseModel):
    """Request für Bildanalyse"""
    image_path: Optional[str] = Field(None, description="Pfad zum Bild")
    image_base64: Optional[str] = Field(None, description="Base64-kodiertes Bild")
    prompt: Optional[str] = Field(None, description="Optionale Frage zum Bild (für VQA)")
    task: str = Field("caption", description="Analyse-Task: caption, ocr, vqa, objects")
    generator: Optional[str] = Field(None, description="Vision Model (swarmui, dalle, etc.)")
    
    class Config:
        schema_extra = {
            "example": {
                "image_base64": "iVBORw0KGgoAAAANSUhEU...",
                "task": "ocr",
                "generator": "swarmui"
            }
        }


class ImageAnalysisResponse(BaseModel):
    """Response nach Bildanalyse"""
    success: bool
    analysis: Optional[str] = None
    task: Optional[str] = None
    model: Optional[str] = None
    confidence: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    is_fallback: Optional[bool] = False
    error: Optional[str] = None


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest):
    """
    Analysiere Bild mit Vision Model
    
    **Unterstützte Tasks:**
    - `caption`: Bildbeschreibung generieren
    - `ocr`: Text aus Bild extrahieren
    - `vqa`: Visual Question Answering (mit prompt)
    - `objects`: Objekte erkennen und auflisten
    
    **Unterstützte Models:**
    - SwarmUI mit LLaVA/BLIP
    - GPT-4 Vision (OpenAI)
    - CLIP Interrogator
    
    **Verwendung für Covina Ingestion:**
    - OCR für Dokumente
    - Bildbeschreibung für Katalogisierung
    - Objekterkennung für Diagramme
    """
    try:
        generator = AIImageGenerator(generator_type=request.generator)
        result = await generator.analyze_image(
            image_path=request.image_path,
            image_base64=request.image_base64,
            prompt=request.prompt,
            task=request.task
        )
        
        return ImageAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in image analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/upload", response_model=ImageAnalysisResponse)
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    task: str = "caption",
    prompt: Optional[str] = None,
    generator: Optional[str] = None
):
    """
    Analysiere hochgeladenes Bild
    
    Praktischer Endpoint für File-Upload + Analyse in einem Schritt.
    Ideal für Covina Ingestion Pipeline.
    """
    try:
        # Bild lesen
        image_data = await file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Analysieren
        ai_generator = AIImageGenerator(generator_type=generator)
        result = await ai_generator.analyze_image(
            image_base64=image_base64,
            prompt=prompt,
            task=task
        )
        
        return ImageAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in upload analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/batch", response_model=List[ImageAnalysisResponse])
async def analyze_batch(requests: List[ImageAnalysisRequest]):
    """
    Analysiere mehrere Bilder in einem Request
    
    Nützlich für Batch-Ingestion von Dokumenten mit Bildern.
    """
    try:
        results = []
        
        for req in requests:
            generator = AIImageGenerator(generator_type=req.generator)
            result = await generator.analyze_image(
                image_path=req.image_path,
                image_base64=req.image_base64,
                prompt=req.prompt,
                task=req.task
            )
            results.append(ImageAnalysisResponse(**result))
        
        return results
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_capabilities():
    """
    Liste alle verfügbaren Bild-Capabilities (Generierung + Analyse)
    """
    return {
        "generation": {
            "swarmui": {
                "models": ["sd_xl_base_1.0", "sd_1.5", "sd_2.1"],
                "tasks": ["txt2img", "img2img", "inpainting"]
            },
            "stable_diffusion": {
                "models": ["custom checkpoints"],
                "tasks": ["txt2img", "img2img", "extras"]
            },
            "dalle": {
                "models": ["dall-e-3", "dall-e-2"],
                "tasks": ["txt2img", "variations", "edits"]
            }
        },
        "analysis": {
            "swarmui": {
                "models": ["llava-v1.5-13b", "blip", "instructblip"],
                "tasks": ["caption", "ocr", "vqa", "objects"]
            },
            "stable_diffusion": {
                "models": ["clip"],
                "tasks": ["caption", "tags"]
            },
            "dalle": {
                "models": ["gpt-4-vision"],
                "tasks": ["caption", "ocr", "vqa", "objects"]
            }
        },
        "use_cases": {
            "presentation_generation": "Bildgenerierung für VDL",
            "covina_ingestion": "Bildanalyse & OCR für Dokumente",
            "document_understanding": "Vision Models für komplexe Layouts",
            "catalog_enrichment": "Automatische Bildbeschreibungen"
        }
    }
