"""
Tests for ExcelTableAgent

Tests table generation, Excel/Word/PowerPoint embedding,
and template management functionality.
"""

import pytest
import os
import tempfile
from pathlib import Path
import pandas as pd
from backend.agents.excel_table_agent import ExcelTableAgent
from backend.agents.table_template_manager import get_table_template_manager


class TestExcelTableAgent:
    """Test suite for ExcelTableAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create ExcelTableAgent instance"""
        return ExcelTableAgent()
    
    @pytest.fixture
    def template_manager(self):
        """Create TableTemplateManager instance"""
        return get_table_template_manager()
    
    @pytest.fixture
    def sample_data(self):
        """Sample table data for testing"""
        return {
            'headers': ['Product', 'Q1', 'Q2', 'Q3', 'Q4'],
            'rows': [
                ['Widget A', 100, 120, 115, 130],
                ['Widget B', 85, 90, 95, 100],
                ['Widget C', 200, 210, 205, 220]
            ]
        }
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent is not None
        assert hasattr(agent, 'template_manager')
        assert hasattr(agent, 'generate_table')
    
    def test_template_manager_initialization(self, template_manager):
        """Test template manager initializes correctly"""
        assert template_manager is not None
        templates = template_manager.list_templates()
        assert len(templates) > 0
        assert any(t['name'] == 'data_table' for t in templates)
    
    def test_read_data_table_template(self, template_manager):
        """Test reading data_table template"""
        template = template_manager.read_template('data_table')
        assert template is not None
        assert template['name'] == 'data_table'
        assert 'variations' in template
        assert len(template['variations']) > 0
    
    def test_read_comparison_template(self, template_manager):
        """Test reading comparison template"""
        template = template_manager.read_template('comparison')
        assert template is not None
        assert template['name'] == 'comparison'
        assert 'llm_example' in template
    
    def test_read_summary_template(self, template_manager):
        """Test reading summary template"""
        template = template_manager.read_template('summary')
        assert template is not None
        assert template['name'] == 'summary'
    
    def test_read_schedule_template(self, template_manager):
        """Test reading schedule template"""
        template = template_manager.read_template('schedule')
        assert template is not None
        assert template['name'] == 'schedule'
    
    @pytest.mark.asyncio
    async def test_generate_excel_table(self, agent, sample_data):
        """Test generating Excel file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_output.xlsx')
            
            result = await agent.generate_table({
                'template': 'data_table',
                'variation': 'simple_data_table',
                'data': sample_data,
                'output_format': 'excel',
                'output_path': output_path
            })
            
            assert result['status'] == 'success'
            assert os.path.exists(output_path)
            assert result['format'] == 'excel'
    
    @pytest.mark.asyncio
    async def test_generate_csv_table(self, agent, sample_data):
        """Test generating CSV file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_output.csv')
            
            result = await agent.generate_table({
                'template': 'data_table',
                'variation': 'simple_data_table',
                'data': sample_data,
                'output_format': 'csv',
                'output_path': output_path
            })
            
            assert result['status'] == 'success'
            assert os.path.exists(output_path)
            assert result['format'] == 'csv'
    
    @pytest.mark.asyncio
    async def test_generate_formatted_table(self, agent, sample_data):
        """Test generating formatted Excel table"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_formatted.xlsx')
            
            result = await agent.generate_table({
                'template': 'data_table',
                'variation': 'formatted_data_table',
                'data': sample_data,
                'output_format': 'excel',
                'output_path': output_path,
                'styling': {
                    'header_color': '#4472C4',
                    'alternate_rows': True
                }
            })
            
            assert result['status'] == 'success'
            assert os.path.exists(output_path)
    
    def test_create_dataframe_from_data(self, agent, sample_data):
        """Test DataFrame creation from data"""
        df = agent._create_dataframe(sample_data)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3  # 3 rows
        assert len(df.columns) == 5  # 5 columns
        assert df.columns[0] == 'Product'
    
    def test_template_search_by_category(self, template_manager):
        """Test searching templates by category"""
        templates = template_manager.search_templates(category='data_table')
        assert len(templates) > 0
        assert all(t['name'] == 'data_table' for t in templates)
    
    def test_export_import_templates(self, template_manager):
        """Test template export/import functionality"""
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = os.path.join(tmpdir, 'templates_export.json')
            
            # Export templates
            result = template_manager.export_templates(export_path)
            assert result['status'] == 'success'
            assert os.path.exists(export_path)
            
            # Import templates
            result = template_manager.import_templates(export_path)
            assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_comparison_template_generation(self, agent):
        """Test generating comparison table"""
        comparison_data = {
            'headers': ['Feature', 'Option A', 'Option B', 'Option C'],
            'rows': [
                ['Price', '$99', '$149', '$199'],
                ['Storage', '128GB', '256GB', '512GB'],
                ['RAM', '8GB', '16GB', '32GB']
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'comparison.xlsx')
            
            result = await agent.generate_table({
                'template': 'comparison',
                'variation': 'feature_comparison',
                'data': comparison_data,
                'output_format': 'excel',
                'output_path': output_path
            })
            
            assert result['status'] == 'success'
            assert os.path.exists(output_path)
    
    @pytest.mark.asyncio
    async def test_summary_template_generation(self, agent):
        """Test generating summary table with totals"""
        summary_data = {
            'headers': ['Category', 'Q1', 'Q2', 'Q3', 'Q4', 'Total'],
            'rows': [
                ['Revenue', 1000, 1100, 1050, 1200, 4350],
                ['Expenses', 800, 850, 900, 950, 3500],
                ['Profit', 200, 250, 150, 250, 850]
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'summary.xlsx')
            
            result = await agent.generate_table({
                'template': 'summary',
                'variation': 'quarterly_summary',
                'data': summary_data,
                'output_format': 'excel',
                'output_path': output_path
            })
            
            assert result['status'] == 'success'
    
    def test_template_validation(self, template_manager):
        """Test template validation"""
        template = template_manager.read_template('data_table')
        assert 'name' in template
        assert 'category' in template
        assert 'variations' in template
        assert 'llm_example' in template
        assert isinstance(template['variations'], list)
    
    @pytest.mark.asyncio
    async def test_invalid_template_handling(self, agent, sample_data):
        """Test handling of invalid template"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test.xlsx')
            
            result = await agent.generate_table({
                'template': 'nonexistent_template',
                'data': sample_data,
                'output_format': 'excel',
                'output_path': output_path
            })
            
            # Should handle gracefully
            assert 'status' in result
    
    def test_all_templates_readable(self, template_manager):
        """Test that all templates can be read"""
        templates = template_manager.list_templates()
        for template_info in templates:
            template = template_manager.read_template(template_info['name'])
            assert template is not None
            assert 'variations' in template
            assert len(template['variations']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
