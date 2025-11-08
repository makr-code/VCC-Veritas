"""
Unit Tests for ThemisDB Adapter and Adapter Factory
"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from backend.adapters.themisdb_adapter import ThemisDBAdapter, ThemisDBConfig
from backend.adapters.adapter_factory import (
    get_database_adapter,
    DatabaseAdapterType,
    is_themisdb_available,
    is_uds3_available
)


class TestThemisDBConfig:
    """Test ThemisDBConfig dataclass and environment loading"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ThemisDBConfig()
        
        assert config.host == "localhost"
        assert config.port == 8765
        assert config.use_ssl is False
        assert config.api_token is None
        assert config.timeout == 30
        assert config.max_retries == 3
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = ThemisDBConfig(
            host="themis.internal",
            port=9000,
            use_ssl=True,
            api_token="test-token-123",
            timeout=60,
            max_retries=5
        )
        
        assert config.host == "themis.internal"
        assert config.port == 9000
        assert config.use_ssl is True
        assert config.api_token == "test-token-123"
        assert config.timeout == 60
        assert config.max_retries == 5
    
    @patch.dict('os.environ', {
        'THEMIS_HOST': 'themis.prod',
        'THEMIS_PORT': '8080',
        'THEMIS_USE_SSL': 'true',
        'THEMIS_API_TOKEN': 'prod-token',
        'THEMIS_TIMEOUT': '45',
        'THEMIS_MAX_RETRIES': '10'
    })
    def test_from_env(self):
        """Test loading configuration from environment variables"""
        config = ThemisDBConfig.from_env()
        
        assert config.host == "themis.prod"
        assert config.port == 8080
        assert config.use_ssl is True
        assert config.api_token == "prod-token"
        assert config.timeout == 45
        assert config.max_retries == 10


class TestThemisDBAdapter:
    """Test ThemisDBAdapter functionality"""
    
    @pytest.fixture
    def adapter(self):
        """Fixture for ThemisDBAdapter instance"""
        config = ThemisDBConfig(host="localhost", port=8765)
        return ThemisDBAdapter(config)
    
    def test_initialization(self, adapter):
        """Test adapter initialization"""
        assert adapter.config.host == "localhost"
        assert adapter.config.port == 8765
        assert adapter.base_url == "http://localhost:8765"
        assert adapter._stats['total_queries'] == 0
    
    def test_build_headers_no_token(self, adapter):
        """Test header building without API token"""
        headers = adapter._build_headers()
        
        assert headers['Content-Type'] == 'application/json'
        assert headers['User-Agent'] == 'Veritas-ThemisDB-Adapter/1.0'
        assert 'Authorization' not in headers
    
    def test_build_headers_with_token(self):
        """Test header building with API token"""
        config = ThemisDBConfig(api_token="test-token")
        adapter = ThemisDBAdapter(config)
        headers = adapter._build_headers()
        
        assert headers['Authorization'] == 'Bearer test-token'
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, adapter):
        """Test successful health check"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "healthy", "version": "1.0.0"}
        
        with patch.object(adapter.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            health = await adapter.health_check()
            
            assert health['status'] == 'healthy'
            assert health['version'] == '1.0.0'
            mock_get.assert_called_once_with('/api/health')
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, adapter):
        """Test health check failure"""
        with patch.object(adapter.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")
            
            with pytest.raises(httpx.ConnectError):
                await adapter.health_check()
    
    @pytest.mark.asyncio
    async def test_vector_search_success(self, adapter):
        """Test successful vector search"""
        # Mock embedding service
        mock_embedding = [0.1] * 768
        
        with patch.object(adapter, '_embed', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = mock_embedding
            
            # Mock HTTP response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "results": [
                    {
                        "id": "doc1",
                        "document": {
                            "content": "BGB §1 content",
                            "metadata": {"year": 2020}
                        },
                        "score": 0.95
                    },
                    {
                        "id": "doc2",
                        "document": {
                            "content": "BGB §2 content",
                            "metadata": {"year": 2021}
                        },
                        "score": 0.87
                    }
                ]
            }
            
            with patch.object(adapter.client, 'post', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response
                
                results = await adapter.vector_search(
                    query="BGB Vertragsrecht",
                    top_k=2
                )
                
                assert len(results) == 2
                assert results[0]['doc_id'] == 'doc1'
                assert results[0]['content'] == 'BGB §1 content'
                assert results[0]['score'] == 0.95
                assert results[0]['metadata']['year'] == 2020
                
                # Check stats
                assert adapter._stats['total_queries'] == 1
                assert adapter._stats['successful_queries'] == 1
    
    @pytest.mark.asyncio
    async def test_vector_search_empty_results(self, adapter):
        """Test vector search with no results"""
        with patch.object(adapter, '_embed', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 768
            
            mock_response = MagicMock()
            mock_response.json.return_value = {"results": []}
            
            with patch.object(adapter.client, 'post', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response
                
                results = await adapter.vector_search(query="unknown query")
                
                assert len(results) == 0
                assert adapter._stats['empty_results'] == 1
    
    @pytest.mark.asyncio
    async def test_graph_traverse(self, adapter):
        """Test graph traversal"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "paths": [
                {"vertices": ["doc1", "doc2"], "edges": ["cites"]},
                {"vertices": ["doc1", "doc3"], "edges": ["cites"]}
            ]
        }
        
        with patch.object(adapter.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            results = await adapter.graph_traverse(
                start_vertex="documents/doc1",
                edge_collection="citations",
                direction="outbound",
                max_depth=2
            )
            
            assert len(results) == 2
            assert results[0]['vertices'] == ['doc1', 'doc2']
    
    @pytest.mark.asyncio
    async def test_execute_aql(self, adapter):
        """Test AQL query execution"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {"_key": "doc1", "title": "Document 1"},
                {"_key": "doc2", "title": "Document 2"}
            ]
        }
        
        with patch.object(adapter.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            results = await adapter.execute_aql(
                query="FOR doc IN documents FILTER doc.year >= @year RETURN doc",
                bind_vars={"year": 2020}
            )
            
            assert len(results) == 2
            assert results[0]['_key'] == 'doc1'
    
    def test_get_stats(self, adapter):
        """Test statistics retrieval"""
        adapter._stats['total_queries'] = 10
        adapter._stats['successful_queries'] = 8
        adapter._stats['total_latency_ms'] = 1000.0
        
        stats = adapter.get_stats()
        
        assert stats['total_queries'] == 10
        assert stats['successful_queries'] == 8
        assert stats['avg_latency_ms'] == 100.0
        assert stats['success_rate'] == 0.8


class TestAdapterFactory:
    """Test adapter factory functionality"""
    
    @patch.dict('os.environ', {
        'THEMIS_ENABLED': 'true',
        'THEMIS_HOST': 'localhost',
        'USE_UDS3_FALLBACK': 'true'
    })
    @patch('backend.adapters.adapter_factory._init_themisdb_adapter')
    def test_get_adapter_themis_primary(self, mock_init_themis):
        """Test getting ThemisDB adapter as primary"""
        mock_adapter = MagicMock()
        mock_adapter.__class__.__name__ = 'ThemisDBAdapter'
        mock_init_themis.return_value = mock_adapter
        
        adapter = get_database_adapter()
        
        assert adapter is mock_adapter
        mock_init_themis.assert_called_once()
    
    @patch.dict('os.environ', {
        'THEMIS_ENABLED': 'false',
        'USE_UDS3_FALLBACK': 'true'
    })
    @patch('backend.adapters.adapter_factory._init_uds3_adapter')
    def test_get_adapter_uds3_primary(self, mock_init_uds3):
        """Test getting UDS3 adapter as primary"""
        mock_adapter = MagicMock()
        mock_adapter.__class__.__name__ = 'UDS3VectorSearchAdapter'
        mock_init_uds3.return_value = mock_adapter
        
        adapter = get_database_adapter()
        
        assert adapter is mock_adapter
        mock_init_uds3.assert_called_once()
    
    @patch.dict('os.environ', {
        'THEMIS_ENABLED': 'true',
        'USE_UDS3_FALLBACK': 'true'
    })
    @patch('backend.adapters.adapter_factory._init_themisdb_adapter')
    @patch('backend.adapters.adapter_factory._init_uds3_adapter')
    def test_get_adapter_fallback_to_uds3(self, mock_init_uds3, mock_init_themis):
        """Test fallback from ThemisDB to UDS3"""
        mock_init_themis.side_effect = Exception("ThemisDB unavailable")
        
        mock_uds3_adapter = MagicMock()
        mock_uds3_adapter.__class__.__name__ = 'UDS3VectorSearchAdapter'
        mock_init_uds3.return_value = mock_uds3_adapter
        
        adapter = get_database_adapter()
        
        assert adapter is mock_uds3_adapter
        mock_init_themis.assert_called_once()
        mock_init_uds3.assert_called_once()
    
    @patch.dict('os.environ', {
        'THEMIS_ENABLED': 'true',
        'USE_UDS3_FALLBACK': 'false'
    })
    @patch('backend.adapters.adapter_factory._init_themisdb_adapter')
    def test_get_adapter_no_fallback(self, mock_init_themis):
        """Test no fallback when disabled"""
        mock_init_themis.side_effect = Exception("ThemisDB unavailable")
        
        with pytest.raises(RuntimeError, match="ThemisDB adapter failed and fallback disabled"):
            get_database_adapter()
    
    def test_force_adapter_type(self):
        """Test forcing specific adapter type"""
        with patch('backend.adapters.adapter_factory._init_themisdb_adapter') as mock_themis:
            mock_adapter = MagicMock()
            mock_themis.return_value = mock_adapter
            
            adapter = get_database_adapter(
                adapter_type=DatabaseAdapterType.THEMIS,
                enable_fallback=False
            )
            
            assert adapter is mock_adapter
            mock_themis.assert_called_once()


class TestAdapterIntegration:
    """Integration tests for adapter usage in RAGService"""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'THEMIS_ENABLED': 'true'})
    async def test_rag_service_with_themis(self):
        """Test RAGService initialization with ThemisDB adapter"""
        with patch('backend.adapters.adapter_factory._init_themisdb_adapter') as mock_init:
            mock_adapter = MagicMock()
            mock_adapter.__class__.__name__ = 'ThemisDBAdapter'
            mock_adapter.vector_search = AsyncMock(return_value=[
                {
                    'doc_id': 'doc1',
                    'content': 'Test content',
                    'score': 0.95,
                    'metadata': {}
                }
            ])
            mock_init.return_value = mock_adapter
            
            # Import after patching
            from backend.services.rag_service import RAGService
            
            rag = RAGService()
            assert rag.is_available()
            assert rag.db_adapter is mock_adapter


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
