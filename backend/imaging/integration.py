"""
VERITAS Image Generation Integration

Integration module for connecting Image Generation Engine with VERITAS Agent system.

Features:
- ImageAgent for request handling
- Integration with existing agents
- Prompt optimization
- Quality assurance
- Output formatting

Author: VERITAS Integration Engine
Date: 2025-12-04
Version: 1.0
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.imaging.image_engine import (
    GeneratedImage,
    GenerationConfig,
    ImageManager,
    ImageModel,
    ImageTask,
    get_image_manager,
)

logger = logging.getLogger(__name__)


# =========================================================================
# Image Request Handler
# =========================================================================


class ImageRequest:
    """Structured image generation request"""

    def __init__(
        self,
        prompt: str,
        model: str = "sdxl",
        task: str = "text2img",
        width: int = 768,
        height: int = 768,
        steps: int = 20,
        guidance: float = 7.5,
        quality: str = "high",
        num_images: int = 1,
    ):
        self.prompt = prompt
        self.model = model
        self.task = task
        self.width = width
        self.height = height
        self.steps = steps
        self.guidance = guidance
        self.quality = quality
        self.num_images = num_images
        self.created_at = datetime.now()

    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate request"""
        if not self.prompt or len(self.prompt.strip()) < 3:
            return False, "Prompt too short (min 3 characters)"

        if self.width < 256 or self.width > 2048:
            return False, "Width must be 256-2048"

        if self.height < 256 or self.height > 2048:
            return False, "Height must be 256-2048"

        if self.steps < 1 or self.steps > 100:
            return False, "Steps must be 1-100"

        if self.guidance < 0 or self.guidance > 20:
            return False, "Guidance must be 0-20"

        return True, None

    def to_config(self) -> GenerationConfig:
        """Convert to engine configuration"""
        return GenerationConfig(
            prompt=self.prompt,
            model=ImageModel[self.model.upper()] if self.model.upper() in ImageModel.__members__ else ImageModel.SDXL,
            task=ImageTask[self.task.upper()] if self.task.upper() in ImageTask.__members__ else ImageTask.TEXT_TO_IMAGE,
            width=self.width,
            height=self.height,
            steps=self.steps,
            guidance_scale=self.guidance,
            num_images=self.num_images,
            quality=self.quality,
        )


# =========================================================================
# Prompt Optimization
# =========================================================================


class PromptOptimizer:
    """
    Optimize prompts for better generation quality

    - Add quality keywords
    - Style enhancement
    - Structure improvement
    - Length optimization
    """

    QUALITY_BOOSTS = {
        "high": "professional, high quality, detailed, sharp focus",
        "ultra": "masterpiece, best quality, ultra detailed, 8k, cinematography",
        "artistic": "artistic, stylized, illustration, concept art",
        "photorealistic": "photorealistic, professional photo, 50mm, f/2.8, studio lighting",
    }

    @staticmethod
    def optimize(prompt: str, quality: str = "high") -> str:
        """Optimize prompt for generation"""
        base = prompt.strip()

        # Add quality keywords
        quality_boost = PromptOptimizer.QUALITY_BOOSTS.get(quality, PromptOptimizer.QUALITY_BOOSTS["high"])

        # Build optimized prompt
        optimized = f"{base}, {quality_boost}"

        # Limit length
        if len(optimized) > 500:
            optimized = optimized[:500]

        logger.debug(f"📝 Optimized prompt: {optimized[:100]}...")
        return optimized

    @staticmethod
    def get_negative_prompt(style: str = "default") -> str:
        """Get negative prompt for quality"""
        negative_prompts = {
            "default": "low quality, blurry, distorted, ugly, bad anatomy",
            "realistic": "cartoon, sketch, drawing, painting",
            "artistic": "photorealistic, photo, realistic",
        }
        return negative_prompts.get(style, negative_prompts["default"])


# =========================================================================
# Image Generation Agent Integration
# =========================================================================


class ImageGenerationAgent:
    """
    VERITAS Image Generation Agent

    Provides:
    - Image generation via natural language
    - Request validation
    - Quality assurance
    - Response formatting
    """

    def __init__(self):
        """Initialize agent"""
        self.image_manager = get_image_manager()
        self.optimizer = PromptOptimizer()
        self.request_history: List[ImageRequest] = []

        logger.info("🎨 ImageGenerationAgent initialized")

    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process image generation request

        Args:
            request_data: Request parameters

        Returns:
            Response with image metadata
        """
        try:
            # Parse request
            req = ImageRequest(
                prompt=request_data.get("prompt", ""),
                model=request_data.get("model", "sdxl"),
                task=request_data.get("task", "text2img"),
                width=request_data.get("width", 768),
                height=request_data.get("height", 768),
                steps=request_data.get("steps", 20),
                guidance=request_data.get("guidance", 7.5),
                quality=request_data.get("quality", "high"),
                num_images=request_data.get("num_images", 1),
            )

            # Validate
            is_valid, error = req.validate()
            if not is_valid:
                return {"status": "error", "message": f"Invalid request: {error}", "code": 400}

            # Optimize prompt
            optimized_prompt = self.optimizer.optimize(req.prompt, req.quality)

            # Create config with optimized prompt
            config = req.to_config()
            config.prompt = optimized_prompt
            config.negative_prompt = self.optimizer.get_negative_prompt()

            # Generate
            logger.info(f"🚀 Starting image generation: {config.prompt[:50]}...")
            image = await self.image_manager.generate_image(
                prompt=config.prompt,
                model=config.model,
                width=config.width,
                height=config.height,
                steps=config.steps,
                guidance_scale=config.guidance_scale,
                quality=config.quality,
            )

            self.request_history.append(req)

            # Return response
            return {
                "status": "success" if image.status == "completed" else image.status,
                "image_id": image.image_id,
                "model": image.model,
                "task": image.task,
                "dimensions": f"{image.width}x{image.height}",
                "steps": image.steps,
                "processing_time_ms": image.processing_time_ms,
                "timestamp": image.timestamp.isoformat(),
                "error": image.error,
            }

        except Exception as e:
            logger.error(f"❌ Request processing failed: {e}")
            return {"status": "error", "message": str(e), "code": 500}

    async def batch_generate(self, prompts: List[str], **kwargs) -> Dict[str, Any]:
        """Generate multiple images"""
        configs = [GenerationConfig(prompt=prompt, **kwargs) for prompt in prompts]

        images = await self.image_manager.generator.batch_generate(configs)

        return {
            "status": "success",
            "total": len(images),
            "completed": len([img for img in images if img.status == "completed"]),
            "images": [
                {"id": img.image_id, "status": img.status, "processing_time_ms": img.processing_time_ms} for img in images
            ],
        }

    def get_generation(self, image_id: str) -> Dict[str, Any]:
        """Get generation details"""
        image = self.image_manager.get_generation(image_id)

        if not image:
            return {"status": "error", "message": "Image not found"}

        return {
            "status": "success",
            "image_id": image.image_id,
            "prompt": image.prompt,
            "model": image.model,
            "dimensions": f"{image.width}x{image.height}",
            "status": image.status,
            "processing_time_ms": image.processing_time_ms,
            "timestamp": image.timestamp.isoformat(),
        }

    def list_generations(self, limit: int = 10) -> Dict[str, Any]:
        """List recent generations"""
        generations = self.image_manager.list_generations()

        return {
            "status": "success",
            "total": len(generations),
            "recent": [
                {
                    "id": g.image_id,
                    "prompt": g.prompt[:60] + "..." if len(g.prompt) > 60 else g.prompt,
                    "model": g.model,
                    "status": g.status,
                    "timestamp": g.timestamp.isoformat(),
                }
                for g in generations[-limit:]
            ],
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics"""
        info = self.image_manager.get_info()

        return {
            "status": "success",
            "stats": {
                "total_requests": len(self.request_history),
                "total_generations": info["total_generations"],
                "successful": info["successful"],
                "failed": info["failed"],
                "models_supported": len(info["generator"]["supported_models"]),
                "models": info["generator"]["supported_models"],
            },
        }


# =========================================================================
# Singleton Instance
# =========================================================================

_image_agent = None


def get_image_generation_agent() -> ImageGenerationAgent:
    """Get or create image generation agent singleton"""
    global _image_agent
    if _image_agent is None:
        _image_agent = ImageGenerationAgent()
    return _image_agent


# =========================================================================
# API Integration
# =========================================================================


async def handle_image_generation_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle image generation API request"""
    agent = get_image_generation_agent()
    return await agent.process_request(request_data)


def handle_image_query(prompt: str, **kwargs) -> Dict[str, Any]:
    """Handle simple image generation query"""

    async def _run():
        agent = get_image_generation_agent()
        return await agent.process_request({"prompt": prompt, **kwargs})

    # Run async function
    try:
        import asyncio

        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context
            task = asyncio.create_task(_run())
            return {"status": "processing", "task_id": str(id(task))}
        else:
            return asyncio.run(_run())
    except RuntimeError:
        return asyncio.run(_run())
