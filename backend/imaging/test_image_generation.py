"""
Image Generation Module Tests

Tests for:
- Image Engine core functionality
- Prompt optimization
- Request validation
- Generation pipeline
- Agent integration

Author: VERITAS Test Suite
Date: 2025-12-04
"""

import asyncio
from datetime import datetime
from typing import Any, Dict

import pytest

# Import image generation modules
from backend.imaging.image_engine import (
    GeneratedImage,
    GenerationConfig,
    ImageEnhancer,
    ImageGenerationEngine,
    ImageManager,
    ImageModel,
    ImageTask,
    SchedulerType,
    get_image_manager,
)
from backend.imaging.integration import ImageGenerationAgent, ImageRequest, PromptOptimizer, get_image_generation_agent

# =========================================================================
# Engine Tests
# =========================================================================


class TestImageGenerationEngine:
    """Test ImageGenerationEngine"""

    @pytest.fixture
    def engine(self):
        return ImageGenerationEngine()

    def test_engine_initialization(self, engine):
        """Test engine initializes correctly"""
        assert engine is not None
        assert engine.swarmui_endpoint == "http://localhost:7865"
        assert len(engine.job_queue) == 0

    @pytest.mark.asyncio
    async def test_generate_image_basic(self, engine):
        """Test basic image generation"""
        config = GenerationConfig(prompt="a beautiful sunset", model=ImageModel.SDXL, width=512, height=512)

        image = await engine.generate(config)

        assert image is not None
        assert image.image_id is not None
        assert image.prompt == "a beautiful sunset"
        assert image.status == "completed"
        assert image.processing_time_ms is not None

    @pytest.mark.asyncio
    async def test_generate_with_custom_params(self, engine):
        """Test generation with custom parameters"""
        config = GenerationConfig(
            prompt="cyberpunk city",
            model=ImageModel.SD_TURBO,
            task=ImageTask.TEXT_TO_IMAGE,
            width=768,
            height=768,
            steps=30,
            guidance_scale=8.5,
            num_images=2,
            quality="ultra",
        )

        image = await engine.generate(config)

        assert image.width == 768
        assert image.height == 768
        assert image.steps == 30
        assert image.guidance_scale == 8.5

    def test_build_payload(self, engine):
        """Test SwarmUI payload construction"""
        config = GenerationConfig(prompt="test prompt", negative_prompt="low quality", width=512, height=512, steps=20)

        payload = engine._build_payload(config)

        assert payload["prompt"] == "test prompt"
        assert payload["negative_prompt"] == "low quality"
        assert payload["width"] == 512
        assert payload["height"] == 512
        assert payload["steps"] == 20

    def test_get_job_status(self, engine):
        """Test job status retrieval"""
        config = GenerationConfig(prompt="test")

        # Create a mock image
        image = GeneratedImage(
            image_id="test123",
            prompt="test",
            model="sdxl",
            task="text2img",
            width=512,
            height=512,
            steps=20,
            guidance_scale=7.5,
            seed=42,
            timestamp=datetime.now(),
            status="completed",
        )

        engine.job_queue["test123"] = image

        result = engine.get_job_status("test123")
        assert result is not None
        assert result.image_id == "test123"

    def test_list_jobs(self, engine):
        """Test job listing"""
        # Add mock jobs
        for i in range(3):
            image = GeneratedImage(
                image_id=f"test{i}",
                prompt=f"test{i}",
                model="sdxl",
                task="text2img",
                width=512,
                height=512,
                steps=20,
                guidance_scale=7.5,
                seed=i,
                timestamp=datetime.now(),
                status="completed" if i < 2 else "processing",
            )
            engine.job_queue[f"test{i}"] = image

        all_jobs = engine.list_jobs()
        assert len(all_jobs) == 3

        completed = engine.list_jobs(status="completed")
        assert len(completed) == 2

    def test_engine_info(self, engine):
        """Test engine info retrieval"""
        info = engine.get_info()

        assert "endpoint" in info
        assert "total_jobs" in info
        assert "completed" in info
        assert "processing" in info
        assert "failed" in info
        assert "supported_models" in info
        assert "supported_tasks" in info
        assert len(info["supported_models"]) > 0


# =========================================================================
# Enhancer Tests
# =========================================================================


class TestImageEnhancer:
    """Test ImageEnhancer"""

    @pytest.fixture
    def enhancer(self):
        return ImageEnhancer()

    @pytest.mark.asyncio
    async def test_upscale(self, enhancer):
        """Test image upscaling"""
        image_data = b"fake_image_data"
        result = await enhancer.upscale(image_data, scale_factor=2)

        assert result is not None
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_denoise(self, enhancer):
        """Test image denoising"""
        image_data = b"fake_image_data"
        result = await enhancer.denoise(image_data, strength=0.7)

        assert result is not None
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_enhance_colors(self, enhancer):
        """Test color enhancement"""
        image_data = b"fake_image_data"
        result = await enhancer.enhance_colors(image_data)

        assert result is not None
        assert isinstance(result, bytes)


# =========================================================================
# Image Manager Tests
# =========================================================================


class TestImageManager:
    """Test ImageManager"""

    @pytest.fixture
    def manager(self):
        return ImageManager()

    def test_manager_initialization(self, manager):
        """Test manager initializes correctly"""
        assert manager is not None
        assert manager.generator is not None
        assert manager.enhancer is not None

    @pytest.mark.asyncio
    async def test_generate_image_simple(self, manager):
        """Test simple image generation"""
        image = await manager.generate_image("a cat sitting on a table")

        assert image is not None
        assert image.image_id is not None
        assert image.status == "completed"

    def test_get_generation(self, manager):
        """Test retrieving generation"""
        config = GenerationConfig(prompt="test")

        # Add mock image
        image = GeneratedImage(
            image_id="test123",
            prompt="test",
            model="sdxl",
            task="text2img",
            width=512,
            height=512,
            steps=20,
            guidance_scale=7.5,
            seed=42,
            timestamp=datetime.now(),
            status="completed",
        )

        manager.generations["test123"] = image

        result = manager.get_generation("test123")
        assert result is not None
        assert result.image_id == "test123"

    def test_list_generations(self, manager):
        """Test listing generations"""
        # Add mock images
        for i in range(3):
            image = GeneratedImage(
                image_id=f"test{i}",
                prompt=f"test{i}",
                model="sdxl" if i % 2 == 0 else "sd_15",
                task="text2img",
                width=512,
                height=512,
                steps=20,
                guidance_scale=7.5,
                seed=i,
                timestamp=datetime.now(),
                status="completed",
            )
            manager.generations[f"test{i}"] = image

        all_gens = manager.list_generations()
        assert len(all_gens) == 3

        sdxl_gens = manager.list_generations(model="sdxl")
        assert len(sdxl_gens) == 2

    def test_manager_info(self, manager):
        """Test manager info"""
        info = manager.get_info()

        assert "generator" in info
        assert "total_generations" in info
        assert "successful" in info
        assert "failed" in info


# =========================================================================
# Request Validation Tests
# =========================================================================


class TestImageRequest:
    """Test ImageRequest validation"""

    def test_request_creation(self):
        """Test request creation"""
        req = ImageRequest(prompt="beautiful landscape", model="sdxl", width=768, height=768)

        assert req.prompt == "beautiful landscape"
        assert req.model == "sdxl"
        assert req.width == 768

    def test_request_validation_valid(self):
        """Test valid request validation"""
        req = ImageRequest(prompt="a valid prompt with enough characters", width=512, height=512, steps=20, guidance=7.5)

        is_valid, error = req.validate()
        assert is_valid is True
        assert error is None

    def test_request_validation_short_prompt(self):
        """Test validation fails for short prompt"""
        req = ImageRequest(prompt="ab")  # Too short

        is_valid, error = req.validate()
        assert is_valid is False
        assert "too short" in error.lower()

    def test_request_validation_invalid_dimensions(self):
        """Test validation fails for invalid dimensions"""
        req = ImageRequest(prompt="valid prompt", width=100)  # Too small

        is_valid, error = req.validate()
        assert is_valid is False
        assert "256" in error or "2048" in error

    def test_request_validation_invalid_steps(self):
        """Test validation fails for invalid steps"""
        req = ImageRequest(prompt="valid prompt", steps=200)  # Too many

        is_valid, error = req.validate()
        assert is_valid is False

    def test_request_validation_invalid_guidance(self):
        """Test validation fails for invalid guidance"""
        req = ImageRequest(prompt="valid prompt", guidance=25)  # Too high

        is_valid, error = req.validate()
        assert is_valid is False

    def test_request_to_config(self):
        """Test request to config conversion"""
        req = ImageRequest(prompt="test prompt", model="sdxl", task="text2img", width=768, height=768, steps=25)

        config = req.to_config()

        assert config.prompt == "test prompt"
        assert config.width == 768
        assert config.steps == 25


# =========================================================================
# Prompt Optimization Tests
# =========================================================================


class TestPromptOptimizer:
    """Test PromptOptimizer"""

    def test_optimize_basic(self):
        """Test basic prompt optimization"""
        original = "a cat"
        optimized = PromptOptimizer.optimize(original)

        assert original in optimized
        assert len(optimized) > len(original)
        assert "quality" in optimized.lower() or "detailed" in optimized.lower()

    def test_optimize_with_high_quality(self):
        """Test optimization with high quality setting"""
        optimized = PromptOptimizer.optimize("a dog", quality="high")

        assert "high quality" in optimized.lower() or "detailed" in optimized.lower()

    def test_optimize_with_ultra_quality(self):
        """Test optimization with ultra quality setting"""
        optimized = PromptOptimizer.optimize("a landscape", quality="ultra")

        assert "masterpiece" in optimized.lower() or "8k" in optimized.lower()

    def test_optimize_length_limit(self):
        """Test optimization respects length limit"""
        long_prompt = "a " + ("very " * 200) + "long prompt"
        optimized = PromptOptimizer.optimize(long_prompt)

        assert len(optimized) <= 500

    def test_get_negative_prompt_default(self):
        """Test default negative prompt"""
        negative = PromptOptimizer.get_negative_prompt()

        assert "low quality" in negative.lower() or "blurry" in negative.lower()

    def test_get_negative_prompt_realistic(self):
        """Test realistic negative prompt"""
        negative = PromptOptimizer.get_negative_prompt(style="realistic")

        assert "cartoon" in negative.lower() or "sketch" in negative.lower()


# =========================================================================
# Agent Tests
# =========================================================================


class TestImageGenerationAgent:
    """Test ImageGenerationAgent"""

    @pytest.fixture
    def agent(self):
        return ImageGenerationAgent()

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent is not None
        assert agent.image_manager is not None
        assert agent.optimizer is not None

    @pytest.mark.asyncio
    async def test_process_valid_request(self, agent):
        """Test processing valid request"""
        request_data = {
            "prompt": "a beautiful painting of mountains",
            "model": "sdxl",
            "width": 512,
            "height": 512,
            "steps": 20,
        }

        result = await agent.process_request(request_data)

        assert result["status"] in ["success", "completed", "processing"]
        assert "image_id" in result

    @pytest.mark.asyncio
    async def test_process_invalid_request(self, agent):
        """Test processing invalid request"""
        request_data = {"prompt": "ab"}  # Too short

        result = await agent.process_request(request_data)

        assert result["status"] == "error"
        assert "Invalid" in result["message"]

    def test_get_generation(self, agent):
        """Test getting generation details"""
        # Add mock generation
        image = GeneratedImage(
            image_id="test123",
            prompt="test",
            model="sdxl",
            task="text2img",
            width=512,
            height=512,
            steps=20,
            guidance_scale=7.5,
            seed=42,
            timestamp=datetime.now(),
            status="completed",
        )

        agent.image_manager.generations["test123"] = image

        result = agent.get_generation("test123")

        assert result["status"] in ["success", "completed"]
        assert result["image_id"] == "test123"

    def test_list_generations(self, agent):
        """Test listing generations"""
        # Add mock generations
        for i in range(3):
            image = GeneratedImage(
                image_id=f"test{i}",
                prompt=f"test{i}",
                model="sdxl",
                task="text2img",
                width=512,
                height=512,
                steps=20,
                guidance_scale=7.5,
                seed=i,
                timestamp=datetime.now(),
                status="completed",
            )
            agent.image_manager.generations[f"test{i}"] = image

        result = agent.list_generations(limit=2)

        assert result["status"] == "success"
        assert "recent" in result
        assert len(result["recent"]) <= 2

    def test_get_stats(self, agent):
        """Test getting statistics"""
        result = agent.get_stats()

        assert result["status"] == "success"
        assert "stats" in result
        assert "total_requests" in result["stats"]
        assert "models_supported" in result["stats"]


# =========================================================================
# Singleton Tests
# =========================================================================


class TestSingletons:
    """Test singleton instances"""

    def test_image_manager_singleton(self):
        """Test image manager singleton"""
        manager1 = get_image_manager()
        manager2 = get_image_manager()

        assert manager1 is manager2

    def test_image_agent_singleton(self):
        """Test image agent singleton"""
        agent1 = get_image_generation_agent()
        agent2 = get_image_generation_agent()

        assert agent1 is agent2


# =========================================================================
# Integration Tests
# =========================================================================


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_end_to_end_generation(self):
        """Test end-to-end image generation"""
        agent = get_image_generation_agent()

        request_data = {
            "prompt": "a serene forest with a river",
            "model": "sdxl",
            "width": 512,
            "height": 512,
            "quality": "high",
        }

        result = await agent.process_request(request_data)

        assert result["status"] in ["success", "completed", "processing"]
        assert "image_id" in result
        assert "processing_time_ms" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
