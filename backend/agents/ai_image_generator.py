"""
AI Image Generator Agent - Integration für Bildgenerierung & Bildanalyse

Unterstützt mehrere AI-Funktionen:

**Bildgenerierung:**
1. SwarmUI - Modernes Web-UI für Stable Diffusion
2. Stable Diffusion WebUI (Automatic1111)
3. ComfyUI - Node-based Workflow System
4. DALL-E - OpenAI API

**Bildanalyse (Vision Models):**
1. SwarmUI mit LLaVA/BLIP - Bildbeschreibung & OCR
2. GPT-4 Vision - OpenAI Multimodal
3. LLaMA Vision - Open-Source Multimodal
4. CLIP - Bild-Text-Matching

Der Agent integriert sich in:
- Presentation Canvas Agent (Bildgenerierung)
- Covina Ingestion (Bildanalyse für Dokumente)
"""

import json
import logging
import base64
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Tuple
from io import BytesIO
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class AIImageGenerator:
    """
    AI Image Generator Agent
    
    Generiert Bilder mit verschiedenen AI-Backends (SwarmUI, SD, ComfyUI, DALL-E)
    """
    
    def __init__(
        self,
        generator_type: str = "swarmui",
        api_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize AI Image Generator
        
        Args:
            generator_type: Art des Generators ("swarmui", "stable_diffusion", "comfyui", "dalle")
            api_url: URL zum Generator-API (optional, nutzt Umgebungsvariablen)
            api_key: API-Key für Generator (optional, nur für DALL-E)
        """
        self.generator_type = generator_type or os.getenv('AI_IMAGE_GENERATOR', 'swarmui')
        self.api_url = api_url or self._get_default_api_url()
        self.api_key = api_key or os.getenv('AI_IMAGE_API_KEY', '')
        
        # Output-Verzeichnis
        self.output_dir = Path(os.getenv('VERITAS_IMAGE_DIR', '/tmp/veritas_images'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AI Image Generator initialized: {self.generator_type} @ {self.api_url}")
    
    def _get_default_api_url(self) -> str:
        """Standard-API-URLs für verschiedene Generatoren"""
        urls = {
            'swarmui': os.getenv('SWARMUI_URL', 'http://localhost:7801/api'),
            'stable_diffusion': os.getenv('SD_WEBUI_URL', 'http://localhost:7860/sdapi/v1'),
            'comfyui': os.getenv('COMFYUI_URL', 'http://localhost:8188/api'),
            'dalle': 'https://api.openai.com/v1/images/generations'
        }
        return urls.get(self.generator_type, urls['swarmui'])
    
    async def generate_image(
        self,
        prompt: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generiere Bild aus Text-Prompt
        
        Args:
            prompt: Text-Beschreibung des Bildes
            properties: Generator-spezifische Parameter
            
        Returns:
            Dict mit:
            - success: bool
            - image_path: str (Pfad zum Bild)
            - image_base64: str (Base64-kodiertes Bild)
            - width: int
            - height: int
            - error: str (bei Fehler)
        """
        try:
            properties = properties or {}
            
            # Generator-spezifische Generierung
            if self.generator_type == 'swarmui':
                return await self._generate_swarmui(prompt, properties)
            elif self.generator_type == 'stable_diffusion':
                return await self._generate_sd_webui(prompt, properties)
            elif self.generator_type == 'comfyui':
                return await self._generate_comfyui(prompt, properties)
            elif self.generator_type == 'dalle':
                return await self._generate_dalle(prompt, properties)
            else:
                # Fallback: Platzhalter-Bild
                return await self._generate_placeholder(prompt, properties)
                
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _generate_swarmui(
        self,
        prompt: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        SwarmUI Image Generation
        
        SwarmUI API: POST /api/generateimage
        """
        # Standard-Parameter für SwarmUI
        params = {
            'prompt': prompt,
            'negative_prompt': properties.get('negative_prompt', 'ugly, blurry, low quality'),
            'model': properties.get('model', 'sd_xl_base_1.0.safetensors'),
            'width': properties.get('width', 1024),
            'height': properties.get('height', 1024),
            'steps': properties.get('steps', 30),
            'cfg_scale': properties.get('cfg_scale', 7.5),
            'sampler': properties.get('sampler', 'euler'),
            'seed': properties.get('seed', -1)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/generateimage",
                    json=params,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # SwarmUI gibt Base64-Bild zurück
                        if 'image' in result:
                            image_data = base64.b64decode(result['image'])
                            
                            # Speichern mit UUID für Eindeutigkeit
                            import time
                            import uuid
                            timestamp = int(time.time() * 1000)
                            unique_id = str(uuid.uuid4())[:8]
                            image_path = self.output_dir / f"swarmui_{timestamp}_{unique_id}.png"
                            
                            with open(image_path, 'wb') as f:
                                f.write(image_data)
                            
                            return {
                                'success': True,
                                'image_path': str(image_path),
                                'image_base64': result['image'],
                                'width': params['width'],
                                'height': params['height'],
                                'generator': 'swarmui',
                                'prompt': prompt
                            }
                    
                    # Fehler
                    error_text = await response.text()
                    logger.warning(f"SwarmUI error {response.status}: {error_text}")
                    return await self._generate_placeholder(prompt, properties)
                    
        except asyncio.TimeoutError:
            logger.warning("SwarmUI timeout, using placeholder")
            return await self._generate_placeholder(prompt, properties)
        except Exception as e:
            logger.warning(f"SwarmUI error: {e}, using placeholder")
            return await self._generate_placeholder(prompt, properties)
    
    async def _generate_sd_webui(
        self,
        prompt: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stable Diffusion WebUI (Automatic1111) Image Generation
        
        API: POST /sdapi/v1/txt2img
        """
        params = {
            'prompt': prompt,
            'negative_prompt': properties.get('negative_prompt', 'ugly, blurry, low quality'),
            'width': properties.get('width', 512),
            'height': properties.get('height', 512),
            'steps': properties.get('steps', 20),
            'cfg_scale': properties.get('cfg_scale', 7.0),
            'sampler_name': properties.get('sampler', 'Euler a'),
            'seed': properties.get('seed', -1)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/txt2img",
                    json=params,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if 'images' in result and result['images']:
                            image_base64 = result['images'][0]
                            image_data = base64.b64decode(image_base64)
                            
                            # Speichern mit UUID
                            import time
                            import uuid
                            timestamp = int(time.time() * 1000)
                            unique_id = str(uuid.uuid4())[:8]
                            image_path = self.output_dir / f"sd_{timestamp}_{unique_id}.png"
                            
                            with open(image_path, 'wb') as f:
                                f.write(image_data)
                            
                            return {
                                'success': True,
                                'image_path': str(image_path),
                                'image_base64': image_base64,
                                'width': params['width'],
                                'height': params['height'],
                                'generator': 'stable_diffusion',
                                'prompt': prompt
                            }
                    
                    return await self._generate_placeholder(prompt, properties)
                    
        except Exception as e:
            logger.warning(f"SD WebUI error: {e}, using placeholder")
            return await self._generate_placeholder(prompt, properties)
    
    async def _generate_comfyui(
        self,
        prompt: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ComfyUI Image Generation
        
        ComfyUI verwendet Workflows - hier vereinfachtes Beispiel
        """
        # TODO: ComfyUI Workflow-Integration
        logger.info("ComfyUI integration not yet implemented, using placeholder")
        return await self._generate_placeholder(prompt, properties)
    
    async def _generate_dalle(
        self,
        prompt: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        DALL-E (OpenAI) Image Generation
        
        API: POST https://api.openai.com/v1/images/generations
        """
        if not self.api_key:
            logger.warning("DALL-E API key not configured, using placeholder")
            return await self._generate_placeholder(prompt, properties)
        
        params = {
            'prompt': prompt,
            'n': 1,
            'size': properties.get('size', '1024x1024'),  # 256x256, 512x512, 1024x1024
            'response_format': 'b64_json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=params,
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if 'data' in result and result['data']:
                            image_base64 = result['data'][0]['b64_json']
                            image_data = base64.b64decode(image_base64)
                            
                            # Speichern mit UUID
                            import time
                            import uuid
                            timestamp = int(time.time() * 1000)
                            unique_id = str(uuid.uuid4())[:8]
                            image_path = self.output_dir / f"dalle_{timestamp}_{unique_id}.png"
                            
                            with open(image_path, 'wb') as f:
                                f.write(image_data)
                            
                            # Parse size
                            size_str = params['size']
                            width, height = map(int, size_str.split('x'))
                            
                            return {
                                'success': True,
                                'image_path': str(image_path),
                                'image_base64': image_base64,
                                'width': width,
                                'height': height,
                                'generator': 'dalle',
                                'prompt': prompt
                            }
                    
                    return await self._generate_placeholder(prompt, properties)
                    
        except Exception as e:
            logger.warning(f"DALL-E error: {e}, using placeholder")
            return await self._generate_placeholder(prompt, properties)
    
    async def _generate_placeholder(
        self,
        prompt: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generiere Platzhalter-Bild wenn kein Generator verfügbar
        """
        from PIL import Image, ImageDraw, ImageFont
        
        width = properties.get('width', 512)
        height = properties.get('height', 512)
        
        # Erstelle Platzhalter
        img = Image.new('RGB', (width, height), '#f0f0f0')
        draw = ImageDraw.Draw(img)
        
        # Rand
        draw.rectangle([10, 10, width-10, height-10], outline='#cccccc', width=2)
        
        # Text
        # Font with cross-platform paths
        font_paths = [
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            # macOS
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            # Windows
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\Arial.ttf"
        ]
        
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, 16)
                break
            except (OSError, IOError):
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        # Prompt-Text (gekürzt)
        prompt_short = prompt[:50] + '...' if len(prompt) > 50 else prompt
        
        # Zentrierter Text
        text_lines = [
            "[AI Image Placeholder]",
            "",
            f"Prompt: {prompt_short}",
            "",
            f"Generator: {self.generator_type}",
            "Not available"
        ]
        
        y = height // 2 - 60
        for line in text_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, y), line, fill='#666666', font=font)
            y += 25
        
        # Speichern mit UUID
        import time
        import uuid
        timestamp = int(time.time() * 1000)
        unique_id = str(uuid.uuid4())[:8]
        image_path = self.output_dir / f"placeholder_{timestamp}_{unique_id}.png"
        img.save(image_path, 'PNG')
        
        # Base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            'success': True,
            'image_path': str(image_path),
            'image_base64': image_base64,
            'width': width,
            'height': height,
            'generator': 'placeholder',
            'prompt': prompt,
            'is_placeholder': True
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Prüfe ob Generator verfügbar ist
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Timeout kürzer für Health-Check
                async with session.get(
                    self.api_url,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    available = response.status in [200, 404]  # 404 ok wenn Endpoint existiert
                    
                    return {
                        'generator': self.generator_type,
                        'api_url': self.api_url,
                        'available': available,
                        'status_code': response.status
                    }
        except Exception as e:
            return {
                'generator': self.generator_type,
                'api_url': self.api_url,
                'available': False,
                'error': str(e)
            }
    
    async def analyze_image(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        prompt: Optional[str] = None,
        task: str = "caption"
    ) -> Dict[str, Any]:
        """
        Analysiere Bild mit Vision Model
        
        Args:
            image_path: Pfad zum Bild
            image_base64: Base64-kodiertes Bild
            prompt: Optionale Frage zum Bild
            task: Art der Analyse ("caption", "ocr", "vqa", "objects")
            
        Returns:
            Dict mit:
            - success: bool
            - analysis: str (Bildbeschreibung/OCR-Text/Antwort)
            - task: str
            - model: str
            - error: str (bei Fehler)
        """
        try:
            # Bild laden
            if image_path:
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
            elif image_base64:
                # Base64 direkt verwenden
                pass
            else:
                return {
                    'success': False,
                    'error': 'No image provided (image_path or image_base64 required)'
                }
            
            # Generator-spezifische Analyse
            if self.generator_type == 'swarmui':
                return await self._analyze_swarmui(image_base64, prompt, task)
            elif self.generator_type in ['stable_diffusion', 'comfyui']:
                return await self._analyze_sd_vision(image_base64, prompt, task)
            elif self.generator_type == 'dalle':
                return await self._analyze_gpt4_vision(image_base64, prompt, task)
            else:
                # Fallback: Einfache Bildanalyse
                return await self._analyze_basic(image_base64, task)
                
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _analyze_swarmui(
        self,
        image_base64: str,
        prompt: Optional[str],
        task: str
    ) -> Dict[str, Any]:
        """
        SwarmUI Vision Model Analysis (LLaVA, BLIP, etc.)
        
        SwarmUI unterstützt Vision Models wie:
        - LLaVA (Large Language-and-Vision Assistant)
        - BLIP (Bootstrapping Language-Image Pre-training)
        - InstructBLIP
        """
        # Task-spezifischer Prompt
        task_prompts = {
            'caption': 'Describe this image in detail.',
            'ocr': 'Extract all visible text from this image.',
            'vqa': prompt or 'What do you see in this image?',
            'objects': 'List all objects visible in this image.'
        }
        
        analysis_prompt = task_prompts.get(task, task_prompts['caption'])
        
        params = {
            'image': image_base64,
            'prompt': analysis_prompt,
            'model': 'llava-v1.5-13b',  # Vision Model
            'max_tokens': 500
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/analyzeimage",
                    json=params,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        return {
                            'success': True,
                            'analysis': result.get('text', result.get('description', '')),
                            'task': task,
                            'model': 'llava-v1.5-13b',
                            'confidence': result.get('confidence', 1.0)
                        }
                    else:
                        # Fallback zu Basic
                        return await self._analyze_basic(image_base64, task)
                        
        except Exception as e:
            logger.warning(f"SwarmUI vision error: {e}, using basic analysis")
            return await self._analyze_basic(image_base64, task)
    
    async def _analyze_sd_vision(
        self,
        image_base64: str,
        prompt: Optional[str],
        task: str
    ) -> Dict[str, Any]:
        """
        Stable Diffusion WebUI mit Vision Extension
        
        Unterstützt CLIP Interrogator für Bildbeschreibung
        """
        try:
            async with aiohttp.ClientSession() as session:
                # CLIP Interrogator
                async with session.post(
                    f"{self.api_url}/interrogate",
                    json={
                        'image': image_base64,
                        'model': 'clip'
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        return {
                            'success': True,
                            'analysis': result.get('caption', ''),
                            'task': task,
                            'model': 'clip',
                            'tags': result.get('tags', [])
                        }
                    else:
                        return await self._analyze_basic(image_base64, task)
                        
        except Exception as e:
            logger.warning(f"SD Vision error: {e}, using basic analysis")
            return await self._analyze_basic(image_base64, task)
    
    async def _analyze_gpt4_vision(
        self,
        image_base64: str,
        prompt: Optional[str],
        task: str
    ) -> Dict[str, Any]:
        """
        GPT-4 Vision Analysis (OpenAI)
        """
        if not self.api_key:
            logger.warning("GPT-4 Vision API key not configured")
            return await self._analyze_basic(image_base64, task)
        
        # Task-spezifischer Prompt
        task_prompts = {
            'caption': 'Describe this image in detail.',
            'ocr': 'Extract all visible text from this image. Format as plain text.',
            'vqa': prompt or 'What do you see in this image?',
            'objects': 'List all objects visible in this image with their locations.'
        }
        
        user_prompt = task_prompts.get(task, task_prompts['caption'])
        
        params = {
            'model': 'gpt-4-vision-preview',
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': user_prompt},
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/jpeg;base64,{image_base64}'
                            }
                        }
                    ]
                }
            ],
            'max_tokens': 500
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/chat/completions',
                    json=params,
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        analysis_text = result['choices'][0]['message']['content']
                        
                        return {
                            'success': True,
                            'analysis': analysis_text,
                            'task': task,
                            'model': 'gpt-4-vision',
                            'tokens': result.get('usage', {}).get('total_tokens', 0)
                        }
                    else:
                        return await self._analyze_basic(image_base64, task)
                        
        except Exception as e:
            logger.warning(f"GPT-4 Vision error: {e}, using basic analysis")
            return await self._analyze_basic(image_base64, task)
    
    async def _analyze_basic(
        self,
        image_base64: str,
        task: str
    ) -> Dict[str, Any]:
        """
        Basic Image Analysis ohne AI (Fallback)
        
        Extrahiert Metadaten und grundlegende Informationen
        """
        from PIL import Image
        import io
        
        # Bild dekodieren
        image_data = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(image_data))
        
        # Metadaten extrahieren
        width, height = img.size
        format_name = img.format or 'Unknown'
        mode = img.mode
        
        # Einfache Analyse
        analysis_parts = [
            f"Image dimensions: {width}x{height}",
            f"Format: {format_name}",
            f"Color mode: {mode}"
        ]
        
        # EXIF-Daten (falls vorhanden)
        try:
            exif = img.getexif()
            if exif:
                analysis_parts.append("EXIF data available")
        except:
            pass
        
        # Task-spezifische Ergänzung
        if task == 'ocr':
            analysis_parts.append("[OCR requires vision model - not available]")
        elif task == 'objects':
            analysis_parts.append("[Object detection requires vision model - not available]")
        
        return {
            'success': True,
            'analysis': '\n'.join(analysis_parts),
            'task': task,
            'model': 'basic_metadata',
            'width': width,
            'height': height,
            'format': format_name,
            'is_fallback': True
        }


# Standalone Test
if __name__ == '__main__':
    import asyncio
    
    async def test():
        print("=" * 70)
        print("AI IMAGE GENERATOR - TEST")
        print("=" * 70)
        
        # Test mit verschiedenen Generatoren
        generators = ['swarmui', 'stable_diffusion', 'dalle']
        
        for gen_type in generators:
            print(f"\n🎨 Test: {gen_type}")
            generator = AIImageGenerator(generator_type=gen_type)
            
            # Health-Check
            health = await generator.health_check()
            print(f"   Available: {health['available']}")
            
            if not health['available']:
                print(f"   → Skipping (not available)")
                continue
            
            # Bild generieren
            result = await generator.generate_image(
                "Photorealistic wind turbine farm at sunset, beautiful landscape",
                {
                    'width': 512,
                    'height': 512,
                    'steps': 20
                }
            )
            
            if result['success']:
                print(f"   ✅ Image generated: {result['image_path']}")
                print(f"      Size: {result['width']}x{result['height']}")
                print(f"      Placeholder: {result.get('is_placeholder', False)}")
            else:
                print(f"   ❌ Error: {result.get('error')}")
        
        print("\n" + "=" * 70)
        print("✅ Tests completed")
        print("=" * 70)
    
    asyncio.run(test())
