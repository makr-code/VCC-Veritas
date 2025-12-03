#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Presentation Canvas Agent

Tests VDL generation, rendering, export formats, and element types.
"""

import pytest
import asyncio
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.presentation_canvas_agent import PresentationCanvasAgent


class TestPresentationCanvasAgent:
    """Test suite for PresentationCanvasAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create PresentationCanvasAgent instance"""
        return PresentationCanvasAgent()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent is not None
        assert hasattr(agent, 'width')
        assert hasattr(agent, 'height')
        assert agent.width == 960
        assert agent.height == 720
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_vdl_creation(self, agent):
        """Test VDL creation"""
        vdl = agent.create_vdl(
            "Create a presentation about wind energy",
            num_slides=2
        )
        
        assert 'slides' in vdl
        assert len(vdl['slides']) == 2
        
        # Verify first slide is title slide
        first_slide = vdl['slides'][0]
        assert first_slide['layout'] == 'title_slide'
        assert 'elements' in first_slide
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_vdl_validation(self, agent):
        """Test VDL validation"""
        valid_vdl = {
            "slides": [
                {
                    "layout": "title_slide",
                    "elements": [
                        {
                            "type": "text",
                            "content": "Test",
                            "position": {"x": 100, "y": 100},
                            "properties": {"font_size": 32}
                        }
                    ]
                }
            ]
        }
        
        is_valid, errors = agent.validate_vdl(valid_vdl)
        assert is_valid is True
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_vdl(self, agent):
        """Test invalid VDL detection"""
        invalid_vdl = {
            "slides": []  # No slides
        }
        
        is_valid, errors = agent.validate_vdl(invalid_vdl)
        assert is_valid is False
        assert len(errors) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_presentation_generation(self, agent):
        """Test complete presentation generation"""
        result = await agent.generate_presentation(
            "Create a 2-slide presentation about environmental permits"
        )
        
        assert result['success'] is True
        assert 'vdl' in result
        assert 'slides' in result
        assert len(result['slides']) == 2
        
        # Verify each slide has an image
        for slide in result['slides']:
            assert 'image_base64' in slide
            assert slide['image_base64'].startswith('data:image/png;base64,')
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_text_element_rendering(self, agent):
        """Test text element rendering"""
        vdl = {
            "slides": [
                {
                    "layout": "content",
                    "elements": [
                        {
                            "type": "text",
                            "content": "Test Title",
                            "position": {"x": 480, "y": 100},
                            "properties": {
                                "font_size": 44,
                                "color": "#000000",
                                "align": "center"
                            }
                        }
                    ]
                }
            ]
        }
        
        result = await agent.generate_from_vdl(vdl)
        
        assert result['success'] is True
        assert len(result['slides']) == 1
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_shape_element_rendering(self, agent):
        """Test shape element rendering"""
        vdl = {
            "slides": [
                {
                    "layout": "content",
                    "elements": [
                        {
                            "type": "shape",
                            "shape": "rectangle",
                            "position": {"x": 100, "y": 100},
                            "size": {"width": 200, "height": 100},
                            "properties": {
                                "fill_color": "#3498db",
                                "border_color": "#2c3e50",
                                "border_width": 2
                            }
                        }
                    ]
                }
            ]
        }
        
        result = await agent.generate_from_vdl(vdl)
        assert result['success'] is True
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_powerpoint_export(self, agent):
        """Test PowerPoint export"""
        result = await agent.generate_presentation(
            "Create a simple 1-slide presentation"
        )
        
        assert 'exports' in result
        assert 'pptx' in result['exports']
        
        pptx_path = Path(result['exports']['pptx'])
        assert pptx_path.exists()
        assert pptx_path.suffix == '.pptx'
        assert pptx_path.stat().st_size > 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_multiple_layouts(self, agent):
        """Test different slide layouts"""
        layouts = ['title_slide', 'content', 'two_column', 'chart', 'image', 'blank']
        
        for layout in layouts:
            vdl = {
                "slides": [
                    {
                        "layout": layout,
                        "elements": []
                    }
                ]
            }
            
            result = await agent.generate_from_vdl(vdl)
            assert result['success'] is True
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_ai_image_placeholder(self, agent):
        """Test AI image placeholder rendering"""
        vdl = {
            "slides": [
                {
                    "layout": "image",
                    "elements": [
                        {
                            "type": "image",
                            "ai_prompt": "Wind turbine at sunset",
                            "position": {"x": 100, "y": 100},
                            "properties": {
                                "ai_generator": "swarmui",
                                "width": 400,
                                "height": 300
                            }
                        }
                    ]
                }
            ]
        }
        
        result = await agent.generate_from_vdl(vdl)
        assert result['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
