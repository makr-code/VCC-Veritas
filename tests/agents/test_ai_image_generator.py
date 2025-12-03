#!/usr/bin/env python3
"""
Comprehensive Unit Tests for AI Image Generator

Tests image generation, image analysis, SwarmUI integration, and dual-use functionality.
"""

import pytest
import asyncio
from pathlib import Path
import sys
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.ai_image_generator import AIImageGenerator


class TestAIImageGenerator:
    """Test suite for AIImageGenerator"""
    
    @pytest.fixture
    def agent(self):
        """Create AIImageGenerator instance"""
        return AIImageGenerator(generator_type='swarmui')
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent is not None
        assert agent.generator_type == 'swarmui'
        assert hasattr(agent, 'swarmui_url')
        assert hasattr(agent, 'sd_webui_url')
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_supported_generators(self, agent):
        """Test all supported generators"""
        generators = ['swarmui', 'stable_diffusion', 'comfyui', 'dalle']
        
        for gen in generators:
            test_agent = AIImageGenerator(generator_type=gen)
            assert test_agent.generator_type == gen
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_image_generation_fallback(self, agent):
        """Test image generation with fallback to placeholder"""
        # Without actual SwarmUI running, should fall back to placeholder
        result = await agent.generate_image(
            "A photorealistic wind turbine at sunset"
        )
        
        assert result['success'] is True
        assert 'image_path' in result
        assert 'image_base64' in result
        
        # Verify placeholder was created
        image_path = Path(result['image_path'])
        assert image_path.exists()
        assert image_path.suffix == '.png'
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_image_generation_with_parameters(self, agent):
        """Test image generation with custom parameters"""
        result = await agent.generate_image(
            "Solar panels",
            width=1024,
            height=768,
            steps=30,
            cfg_scale=7.5
        )
        
        assert result['success'] is True
        assert result['width'] == 1024
        assert result['height'] == 768
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_analyze_image_placeholder(self, agent):
        """Test image analysis with fallback"""
        # Create a test image
        result_gen = await agent.generate_image("Test image")
        image_path = result_gen['image_path']
        
        # Analyze it (will fall back to basic metadata)
        result = await agent.analyze_image(
            image_path=image_path,
            task='caption'
        )
        
        assert result['success'] is True
        assert 'analysis' in result
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_analyze_image_ocr_task(self, agent):
        """Test OCR analysis task"""
        # Create test image
        result_gen = await agent.generate_image("Test")
        image_path = result_gen['image_path']
        
        result = await agent.analyze_image(
            image_path=image_path,
            task='ocr'
        )
        
        assert result['success'] is True
        assert result['task'] == 'ocr'
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_analyze_image_vqa_task(self, agent):
        """Test VQA (Visual Question Answering) task"""
        result_gen = await agent.generate_image("Wind turbine")
        image_path = result_gen['image_path']
        
        result = await agent.analyze_image(
            image_path=image_path,
            task='vqa',
            question='What is in this image?'
        )
        
        assert result['success'] is True
        assert result['task'] == 'vqa'
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_analyze_image_objects_task(self, agent):
        """Test object detection task"""
        result_gen = await agent.generate_image("Test")
        image_path = result_gen['image_path']
        
        result = await agent.analyze_image(
            image_path=image_path,
            task='objects'
        )
        
        assert result['success'] is True
        assert result['task'] == 'objects'
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_batch_image_generation(self, agent):
        """Test batch image generation"""
        prompts = [
            "Wind turbine",
            "Solar panel",
            "Hydroelectric dam"
        ]
        
        results = await agent.batch_generate(prompts)
        
        assert len(results) == 3
        for result in results:
            assert result['success'] is True
            assert 'image_path' in result
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_batch_image_analysis(self, agent):
        """Test batch image analysis"""
        # Generate some test images
        prompts = ["Test 1", "Test 2"]
        gen_results = await agent.batch_generate(prompts)
        
        image_paths = [r['image_path'] for r in gen_results]
        
        # Analyze them
        results = await agent.batch_analyze(
            image_paths=image_paths,
            task='caption'
        )
        
        assert len(results) == 2
        for result in results:
            assert result['success'] is True
            assert result['task'] == 'caption'
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_capabilities(self, agent):
        """Test capabilities listing"""
        capabilities = agent.get_capabilities()
        
        assert 'generators' in capabilities
        assert 'analysis_models' in capabilities
        assert 'tasks' in capabilities
        
        assert 'swarmui' in capabilities['generators']
        assert 'ocr' in capabilities['tasks']
        assert 'caption' in capabilities['tasks']
        assert 'vqa' in capabilities['tasks']
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_task(self, agent):
        """Test handling of invalid analysis task"""
        result_gen = await agent.generate_image("Test")
        image_path = result_gen['image_path']
        
        result = await agent.analyze_image(
            image_path=image_path,
            task='invalid_task'
        )
        
        # Should fall back to caption
        assert result['success'] is True
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_nonexistent_image(self, agent):
        """Test handling of nonexistent image file"""
        result = await agent.analyze_image(
            image_path='/nonexistent/image.jpg',
            task='caption'
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_cross_platform_file_naming(self, agent):
        """Test UUID-based file naming for cross-platform compatibility"""
        result = await agent.generate_image("Test")
        
        image_path = Path(result['image_path'])
        filename = image_path.name
        
        # Should contain UUID pattern
        assert 'swarmui_' in filename or 'placeholder_' in filename
        assert filename.endswith('.png')
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_different_generators(self):
        """Test all generator types"""
        generators = ['swarmui', 'stable_diffusion', 'comfyui', 'dalle']
        
        for gen_type in generators:
            agent = AIImageGenerator(generator_type=gen_type)
            result = await agent.generate_image("Test image")
            
            assert result['success'] is True
            assert result['generator'] == gen_type


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
