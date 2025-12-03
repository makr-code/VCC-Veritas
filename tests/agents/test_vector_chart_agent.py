#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Vector Chart Agent

Tests all chart types, templates, export formats, and error handling.
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.vector_chart_agent import VectorChartAgent


class TestVectorChartAgent:
    """Test suite for VectorChartAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create VectorChartAgent instance"""
        return VectorChartAgent()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent is not None
        assert hasattr(agent, 'chart_templates')
        assert len(agent.chart_templates) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_templates(self, agent):
        """Test template listing"""
        templates = agent.list_templates()
        
        assert isinstance(templates, list)
        assert len(templates) == 4
        
        # Verify template structure
        for template in templates:
            assert 'name' in template
            assert 'type' in template
            assert 'title' in template
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_bar_chart_generation(self, agent):
        """Test bar chart generation"""
        result = await agent.generate_chart(
            "Create a bar chart",
            template='bimschg_overview'
        )
        
        assert result['success'] is True
        assert result['chart_type'] == 'bar'
        assert 'title' in result
        assert 'data' in result
        assert 'exports' in result
        
        # Verify exports
        exports = result['exports']
        assert 'png' in exports
        assert 'svg' in exports
        assert 'pdf' in exports
        
        # Verify PNG base64
        assert 'image_base64' in result
        assert result['image_base64'].startswith('data:image/png;base64,')
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_pie_chart_generation(self, agent):
        """Test pie chart generation"""
        result = await agent.generate_chart(
            "Show pie chart",
            template='wka_leistung'
        )
        
        assert result['success'] is True
        assert result['chart_type'] == 'pie'
        assert len(result['data']['values']) == 4
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_line_chart_generation(self, agent):
        """Test line chart generation"""
        result = await agent.generate_chart(
            "Line chart",
            template='zeitreihe_genehmigungen'
        )
        
        assert result['success'] is True
        assert result['chart_type'] == 'line'
        assert len(result['data']['x']) > 0
        assert len(result['data']['y']) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_scatter_chart_generation(self, agent):
        """Test scatter chart generation"""
        result = await agent.generate_chart(
            "Scatter plot",
            template='emissionen_analyse'
        )
        
        assert result['success'] is True
        assert result['chart_type'] == 'scatter'
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_fallback_without_llm(self, agent):
        """Test fallback mechanism when LLM is not available"""
        result = await agent.generate_chart(
            "Create any chart"
        )
        
        assert result['success'] is True
        assert result['chart_type'] in ['bar', 'pie', 'line', 'scatter']
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_template(self, agent):
        """Test handling of invalid template"""
        result = await agent.generate_chart(
            "Create chart",
            template='nonexistent_template'
        )
        
        # Should fall back to default template
        assert result['success'] is True
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_export_formats(self, agent):
        """Test all export formats are created"""
        result = await agent.generate_chart(
            "Bar chart",
            template='bimschg_overview'
        )
        
        exports = result['exports']
        
        # Verify all formats exist
        for format_type in ['png', 'svg', 'pdf']:
            assert format_type in exports
            file_path = Path(exports[format_type])
            assert file_path.exists()
            assert file_path.stat().st_size > 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_concurrent_generation(self, agent):
        """Test concurrent chart generation"""
        tasks = [
            agent.generate_chart("Bar chart", template='bimschg_overview'),
            agent.generate_chart("Pie chart", template='wka_leistung'),
            agent.generate_chart("Line chart", template='zeitreihe_genehmigungen')
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert result['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
