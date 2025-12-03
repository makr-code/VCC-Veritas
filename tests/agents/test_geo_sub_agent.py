#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Geo Sub-Agent

Tests coordinate transformation, geo data retrieval, map generation.
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.geo_sub_agent import GeoSubAgent, CoordinateTransformer


class TestCoordinateTransformer:
    """Test suite for CoordinateTransformer"""
    
    @pytest.fixture
    def transformer(self):
        """Create CoordinateTransformer instance"""
        return CoordinateTransformer()
    
    @pytest.mark.unit
    def test_transformer_initialization(self, transformer):
        """Test transformer initializes correctly"""
        assert transformer is not None
        assert hasattr(transformer, 'utm_to_wgs84')
        assert hasattr(transformer, 'wgs84_to_utm')
    
    @pytest.mark.unit
    def test_utm_to_wgs84_conversion(self, transformer):
        """Test UTM to WGS84 coordinate conversion"""
        # Potsdam coordinates in ETRS89 UTM Zone 33N
        ostwert = 385000
        nordwert = 5820000
        
        lat, lon = transformer.utm33n_to_wgs84(ostwert, nordwert)
        
        # Potsdam is approximately at 52.4°N, 13.0°E
        assert 52.0 < lat < 53.0
        assert 12.5 < lon < 13.5
    
    @pytest.mark.unit
    def test_wgs84_to_utm_conversion(self, transformer):
        """Test WGS84 to UTM coordinate conversion"""
        # Potsdam coordinates in WGS84
        lat = 52.4
        lon = 13.0
        
        ostwert, nordwert = transformer.wgs84_to_utm33n(lat, lon)
        
        # Should be in Brandenburg region
        assert 350000 < ostwert < 450000
        assert 5750000 < nordwert < 5900000
    
    @pytest.mark.unit
    def test_round_trip_conversion(self, transformer):
        """Test round-trip coordinate conversion"""
        original_ostwert = 400000
        original_nordwert = 5800000
        
        # UTM -> WGS84 -> UTM
        lat, lon = transformer.utm33n_to_wgs84(original_ostwert, original_nordwert)
        ostwert, nordwert = transformer.wgs84_to_utm33n(lat, lon)
        
        # Should be very close (within 1 meter)
        assert abs(ostwert - original_ostwert) < 1
        assert abs(nordwert - original_nordwert) < 1
    
    @pytest.mark.unit
    def test_brandenburg_validation(self, transformer):
        """Test Brandenburg bounding box validation"""
        # Valid Brandenburg coordinate
        assert transformer.is_in_brandenburg(52.5, 13.5) is True
        
        # Invalid (outside Brandenburg)
        assert transformer.is_in_brandenburg(48.0, 11.0) is False  # Munich


class TestGeoSubAgent:
    """Test suite for GeoSubAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create GeoSubAgent instance"""
        return GeoSubAgent()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent is not None
        assert hasattr(agent, 'transformer')
        assert isinstance(agent.transformer, CoordinateTransformer)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_bimschg_data(self, agent):
        """Test BImSchG data retrieval"""
        query = {'source': 'bimschg', 'limit': 5}
        
        geo_data = await agent.get_geo_data(query)
        
        assert 'type' in geo_data
        assert geo_data['type'] == 'FeatureCollection'
        assert 'features' in geo_data
        assert len(geo_data['features']) <= 5
        
        # Verify feature structure
        if len(geo_data['features']) > 0:
            feature = geo_data['features'][0]
            assert 'type' in feature
            assert feature['type'] == 'Feature'
            assert 'geometry' in feature
            assert 'properties' in feature
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_wka_data(self, agent):
        """Test WKA data retrieval"""
        query = {'source': 'wka', 'limit': 5}
        
        geo_data = await agent.get_geo_data(query)
        
        assert geo_data['type'] == 'FeatureCollection'
        assert len(geo_data['features']) <= 5
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_category_filter(self, agent):
        """Test category filtering"""
        query = {
            'source': 'bimschg',
            'filters': {'category': '1.1'},
            'limit': 10
        }
        
        geo_data = await agent.get_geo_data(query)
        
        # All features should match category
        for feature in geo_data['features']:
            assert feature['properties'].get('category') == '1.1'
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_bbox_filter(self, agent):
        """Test bounding box filtering"""
        query = {
            'source': 'bimschg',
            'bbox': [52.0, 13.0, 53.0, 14.0],  # Part of Brandenburg
            'limit': 10
        }
        
        geo_data = await agent.get_geo_data(query)
        
        # All features should be within bbox
        for feature in geo_data['features']:
            coords = feature['geometry']['coordinates']
            lon, lat = coords[0], coords[1]
            assert 52.0 <= lat <= 53.0
            assert 13.0 <= lon <= 14.0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_map_generation(self, agent):
        """Test map image generation"""
        # Get some geo data
        query = {'source': 'bimschg', 'limit': 10}
        geo_data = await agent.get_geo_data(query)
        
        # Generate map
        options = {
            'title': 'Test Map',
            'width': 800,
            'height': 600,
            'style': 'markers'
        }
        
        result = await agent.generate_map(geo_data, options)
        
        assert result['success'] is True
        assert 'image_path' in result
        assert 'image_base64' in result
        assert 'geojson' in result
        
        # Verify image file exists
        image_path = Path(result['image_path'])
        assert image_path.exists()
        assert image_path.suffix == '.png'
        assert image_path.stat().st_size > 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_map_with_custom_markers(self, agent):
        """Test map generation with custom marker styles"""
        query = {'source': 'wka', 'limit': 5}
        geo_data = await agent.get_geo_data(query)
        
        options = {
            'title': 'WKA Anlagen',
            'marker_color': 'green',
            'marker_size': 100
        }
        
        result = await agent.generate_map(geo_data, options)
        assert result['success'] is True
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_brandenburg_bounds(self, agent):
        """Test Brandenburg bounding box retrieval"""
        bounds = agent.get_brandenburg_bounds()
        
        assert 'min_lat' in bounds
        assert 'max_lat' in bounds
        assert 'min_lon' in bounds
        assert 'max_lon' in bounds
        
        # Verify reasonable values for Brandenburg
        assert 51.0 < bounds['min_lat'] < 52.0
        assert 53.0 < bounds['max_lat'] < 54.0
        assert 11.0 < bounds['min_lon'] < 12.0
        assert 14.0 < bounds['max_lon'] < 15.0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_empty_features(self, agent):
        """Test handling of empty feature set"""
        geo_data = {
            'type': 'FeatureCollection',
            'features': []
        }
        
        result = await agent.generate_map(geo_data, {'title': 'Empty Map'})
        
        # Should still succeed but with a blank map
        assert result['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
