#!/usr/bin/env python3
"""
Integration Tests for All API Endpoints

Tests the REST API endpoints for all 4 agents.
"""

import pytest
import asyncio
import httpx
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestChartAPIEndpoints:
    """Integration tests for Chart API"""
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:5000"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_chart_generation_endpoint(self, base_url):
        """Test POST /api/charts/generate"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/charts/generate",
                json={
                    "prompt": "Create a bar chart",
                    "template": "bimschg_overview"
                },
                timeout=30.0
            )
            
            # If backend is running
            if response.status_code == 200:
                data = response.json()
                assert 'chart_type' in data
                assert 'title' in data
                assert 'exports' in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_templates_endpoint(self, base_url):
        """Test GET /api/charts/templates"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/api/charts/templates",
                timeout=10.0
            )
            
            if response.status_code == 200:
                templates = response.json()
                assert isinstance(templates, list)
                assert len(templates) > 0


class TestPresentationAPIEndpoints:
    """Integration tests for Presentation API"""
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:5000"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_presentation_generation_endpoint(self, base_url):
        """Test POST /api/presentations/generate"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/presentations/generate",
                json={
                    "prompt": "Create a 2-slide presentation",
                    "num_slides": 2
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'success' in data
                assert 'slides' in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_vdl_validation_endpoint(self, base_url):
        """Test POST /api/presentations/validate_vdl"""
        async with httpx.AsyncClient() as client:
            vdl = {
                "slides": [
                    {
                        "layout": "title_slide",
                        "elements": []
                    }
                ]
            }
            
            response = await client.post(
                f"{base_url}/api/presentations/validate_vdl",
                json={"vdl": vdl},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'valid' in data


class TestGeoAPIEndpoints:
    """Integration tests for Geo API"""
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:5000"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_geo_query_endpoint(self, base_url):
        """Test POST /api/geo/query"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/geo/query",
                json={
                    "source": "bimschg",
                    "limit": 10
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'type' in data
                assert data['type'] == 'FeatureCollection'
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_geo_map_endpoint(self, base_url):
        """Test POST /api/geo/map"""
        async with httpx.AsyncClient() as client:
            geo_data = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [13.0, 52.5]
                        },
                        "properties": {"name": "Test"}
                    }
                ]
            }
            
            response = await client.post(
                f"{base_url}/api/geo/map",
                json={
                    "geo_data": geo_data,
                    "title": "Test Map"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'success' in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_coordinate_transform_endpoint(self, base_url):
        """Test POST /api/geo/transform"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/geo/transform",
                json={
                    "ostwert": 400000,
                    "nordwert": 5800000
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'lat' in data
                assert 'lon' in data


class TestImageAPIEndpoints:
    """Integration tests for Image API"""
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:5000"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_image_generation_endpoint(self, base_url):
        """Test POST /api/images/generate"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/images/generate",
                json={
                    "prompt": "A wind turbine",
                    "generator": "swarmui"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'success' in data
                assert 'image_path' in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_image_analyze_endpoint(self, base_url):
        """Test POST /api/images/analyze"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/images/analyze",
                json={
                    "image_path": "/tmp/test.jpg",
                    "task": "caption"
                },
                timeout=30.0
            )
            
            # May fail if image doesn't exist, but should return valid response structure
            if response.status_code in [200, 400]:
                data = response.json()
                assert isinstance(data, dict)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_capabilities_endpoint(self, base_url):
        """Test GET /api/images/capabilities"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/api/images/capabilities",
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'generators' in data
                assert 'analysis_models' in data
                assert 'tasks' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
