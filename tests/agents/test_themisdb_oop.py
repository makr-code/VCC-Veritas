"""
Unit Tests for ThemisDB Agent Framework (OOP Version)
=====================================================

Tests für die OOP-basierte Implementierung mit:
- SOLID Principles
- Design Patterns
- Type Safety
- Adapter-Austauschbarkeit

Author: VERITAS Backend Team
Date: 2025-12-03
Version: 2.0
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from backend.agents.themisdb import (
    # Base
    QueryType,
    QueryComplexity,
    QueryContext,
    QueryPlan,
    QueryResult,
    RAGDocument,
    
    # Implementations
    VectorSearchTemplate,
    HybridQueryTemplate,
    AQLQueryPlanner,
    RAGDocumentTransformer,
    StandardQueryStrategy,
    InMemoryCache,
    
    # Adapters
    DatabaseType,
    DatabaseConfig,
    SearchOptions,
    DocumentResult,
    IDatabaseAdapter,
    ThemisDBAdapter,
    UDS3Adapter,
    DatabaseAdapterFactory,
    
    # Main Agent
    ThemisDBRAGAgent,
    create_rag_agent,
)


# ============================================================================
# Base Classes Tests
# ============================================================================

class TestQueryContext:
    """Test QueryContext value object"""
    
    def test_immutability(self):
        """Test that QueryContext is immutable"""
        context = QueryContext(user_query="test")
        
        # Should be immutable (frozen dataclass)
        with pytest.raises(AttributeError):
            context.user_query = "modified"
    
    def test_with_metadata(self):
        """Test builder pattern for metadata"""
        context = QueryContext(user_query="test")
        new_context = context.with_metadata(top_k=10, threshold=0.8)
        
        assert new_context.metadata["top_k"] == 10
        assert new_context.metadata["threshold"] == 0.8
        # Original unchanged
        assert "top_k" not in context.metadata


class TestQueryPlan:
    """Test QueryPlan command object"""
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        plan = QueryPlan(
            query_type=QueryType.VECTOR_SEARCH,
            aql_query="FOR doc IN documents RETURN doc",
            bind_vars={"limit": 10}
        )
        
        key = plan.cache_key
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hash length
    
    def test_cache_key_consistency(self):
        """Test that same plan generates same key"""
        plan1 = QueryPlan(
            query_type=QueryType.VECTOR_SEARCH,
            aql_query="SELECT * FROM docs",
            bind_vars={"limit": 10}
        )
        plan2 = QueryPlan(
            query_type=QueryType.VECTOR_SEARCH,
            aql_query="SELECT * FROM docs",
            bind_vars={"limit": 10}
        )
        
        assert plan1.cache_key == plan2.cache_key


# ============================================================================
# Template Tests
# ============================================================================

class TestQueryTemplates:
    """Test query templates"""
    
    def test_vector_search_template(self):
        """Test vector search template"""
        template = VectorSearchTemplate()
        context = QueryContext(
            user_query="test",
            metadata={"top_k": 5, "collection": "documents"}
        )
        
        query = template.build_query(context)
        bind_vars = template.extract_bind_vars(context)
        
        assert "COSINE_SIMILARITY" in query
        assert bind_vars["@collection"] == "documents"
        assert bind_vars["limit"] == 5
    
    def test_hybrid_template(self):
        """Test hybrid query template"""
        template = HybridQueryTemplate()
        context = QueryContext(
            user_query="test",
            metadata={"top_k": 10, "context_depth": 2}
        )
        
        query = template.build_query(context)
        bind_vars = template.extract_bind_vars(context)
        
        assert "vector_results" in query
        assert "graph_results" in query
        assert bind_vars["graph_depth"] == 2
    
    def test_query_optimization(self):
        """Test query optimization"""
        template = VectorSearchTemplate()
        
        # Low complexity → cache hint
        context_low = QueryContext(
            user_query="test",
            complexity=QueryComplexity.LOW
        )
        query_low = template.optimize_query("SELECT", context_low)
        assert "/* +cache */" in query_low
        
        # High complexity → profile hint
        context_high = QueryContext(
            user_query="test",
            complexity=QueryComplexity.HIGH
        )
        query_high = template.optimize_query("SELECT", context_high)
        assert "/* +profile */" in query_high


# ============================================================================
# Planner Tests
# ============================================================================

class TestAQLQueryPlanner:
    """Test AQL query planner"""
    
    def test_detect_vector_search(self):
        """Test detection of vector search query"""
        planner = AQLQueryPlanner()
        context = QueryContext(
            user_query="test",
            capabilities=frozenset(["vector_search"])
        )
        
        plan = planner.plan(context)
        assert plan.query_type == QueryType.VECTOR_SEARCH
    
    def test_detect_hybrid_query(self):
        """Test detection of hybrid query"""
        planner = AQLQueryPlanner()
        context = QueryContext(
            user_query="test",
            capabilities=frozenset(["vector_search", "graph_traversal"])
        )
        
        plan = planner.plan(context)
        assert plan.query_type == QueryType.HYBRID
    
    def test_cost_estimation(self):
        """Test query cost estimation"""
        planner = AQLQueryPlanner()
        context = QueryContext(
            user_query="test",
            capabilities=frozenset(["vector_search"])
        )
        
        plan = planner.plan(context)
        assert plan.estimated_cost > 0


# ============================================================================
# Transformer Tests
# ============================================================================

class TestRAGDocumentTransformer:
    """Test result transformer"""
    
    def test_transform_simple_results(self):
        """Test transformation of simple results"""
        transformer = RAGDocumentTransformer()
        raw_results = [
            {
                "doc_id": "doc1",
                "content": "Test content",
                "score": 0.95,
                "metadata": {"year": 2023}
            }
        ]
        
        documents = transformer.transform(raw_results)
        
        assert len(documents) == 1
        assert isinstance(documents[0], RAGDocument)
        assert documents[0].doc_id == "doc1"
        assert documents[0].score == 0.95
    
    def test_transform_nested_results(self):
        """Test transformation of nested results"""
        transformer = RAGDocumentTransformer()
        raw_results = [
            {
                "doc": {
                    "_key": "doc1",
                    "content": "Test",
                    "metadata": {}
                },
                "score": 0.88
            }
        ]
        
        documents = transformer.transform(raw_results)
        
        assert len(documents) == 1
        assert documents[0].doc_id == "doc1"


# ============================================================================
# Cache Tests
# ============================================================================

class TestInMemoryCache:
    """Test in-memory cache"""
    
    def test_set_and_get(self):
        """Test basic cache operations"""
        cache = InMemoryCache()
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_get_nonexistent(self):
        """Test getting non-existent key"""
        cache = InMemoryCache()
        assert cache.get("nonexistent") is None
    
    def test_delete(self):
        """Test cache deletion"""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_clear(self):
        """Test cache clearing"""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None


# ============================================================================
# Adapter Tests
# ============================================================================

class TestDatabaseConfig:
    """Test database configuration"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = DatabaseConfig(db_type=DatabaseType.THEMIS)
        
        assert config.db_type == DatabaseType.THEMIS
        assert config.host == "localhost"
        assert config.port == 8765
        assert config.use_ssl is False
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = DatabaseConfig(
            db_type=DatabaseType.UDS3,
            host="themis.internal",
            port=9000,
            use_ssl=True,
            api_token="test-token"
        )
        
        assert config.host == "themis.internal"
        assert config.port == 9000
        assert config.use_ssl is True
        assert config.api_token == "test-token"


class TestThemisDBAdapter:
    """Test ThemisDB adapter"""
    
    @pytest.mark.asyncio
    async def test_adapter_creation(self):
        """Test ThemisDB adapter creation"""
        config = DatabaseConfig(db_type=DatabaseType.THEMIS)
        adapter = ThemisDBAdapter(config)
        
        assert adapter.get_backend_type() == DatabaseType.THEMIS
        assert adapter.supports_feature("vector_search")
        assert adapter.supports_feature("graph_traversal")
    
    def test_wrong_config_type(self):
        """Test adapter with wrong config type"""
        config = DatabaseConfig(db_type=DatabaseType.UDS3)
        
        with pytest.raises(ValueError):
            ThemisDBAdapter(config)


class TestUDS3Adapter:
    """Test UDS3 adapter"""
    
    @pytest.mark.asyncio
    async def test_adapter_creation(self):
        """Test UDS3 adapter creation"""
        config = DatabaseConfig(db_type=DatabaseType.UDS3)
        adapter = UDS3Adapter(config)
        
        assert adapter.get_backend_type() == DatabaseType.UDS3
        assert adapter.supports_feature("vector_search")
    
    def test_wrong_config_type(self):
        """Test adapter with wrong config type"""
        config = DatabaseConfig(db_type=DatabaseType.THEMIS)
        
        with pytest.raises(ValueError):
            UDS3Adapter(config)


# ============================================================================
# RAG Agent Tests
# ============================================================================

class TestThemisDBRAGAgent:
    """Test main RAG agent"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create mock adapter"""
        adapter = MagicMock(spec=IDatabaseAdapter)
        adapter.get_backend_type.return_value = DatabaseType.THEMIS
        adapter.supports_feature.return_value = True
        adapter.get_stats.return_value = {
            "total_queries": 0,
            "successful_queries": 0
        }
        return adapter
    
    def test_agent_initialization(self, mock_adapter):
        """Test agent initialization"""
        agent = ThemisDBRAGAgent(adapter=mock_adapter)
        
        assert agent is not None
        backend_info = agent.get_backend_info()
        assert backend_info["type"] == "themisdb"
    
    @pytest.mark.asyncio
    async def test_retrieve(self, mock_adapter):
        """Test document retrieval"""
        # Setup mock
        mock_adapter.vector_search = AsyncMock(return_value=[
            DocumentResult(
                doc_id="doc1",
                content="Test content",
                score=0.95,
                metadata={},
                source="themisdb"
            )
        ])
        mock_adapter.execute_aql = AsyncMock(return_value=[
            {
                "doc_id": "doc1",
                "content": "Test content",
                "score": 0.95,
                "metadata": {}
            }
        ])
        
        agent = ThemisDBRAGAgent(adapter=mock_adapter)
        
        results = await agent.retrieve(
            query="test query",
            top_k=5
        )
        
        assert len(results) > 0
        assert isinstance(results[0], RAGDocument)
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_adapter):
        """Test health check"""
        mock_adapter.health_check = AsyncMock(return_value={
            "status": "healthy",
            "available": True,
            "latency_ms": 10.0
        })
        
        agent = ThemisDBRAGAgent(adapter=mock_adapter)
        health = await agent.health_check()
        
        assert health["agent_status"] == "healthy"
        assert health["backend_available"] is True
    
    def test_get_stats(self, mock_adapter):
        """Test statistics retrieval"""
        agent = ThemisDBRAGAgent(adapter=mock_adapter)
        stats = agent.get_stats()
        
        assert "total_queries" in stats
        assert "backend" in stats
        assert stats["backend"] == "themisdb"
    
    def test_cache_clearing(self, mock_adapter):
        """Test cache clearing"""
        agent = ThemisDBRAGAgent(adapter=mock_adapter)
        
        # Should not raise
        agent.clear_cache()


# ============================================================================
# Factory Tests
# ============================================================================

class TestDatabaseAdapterFactory:
    """Test adapter factory"""
    
    def test_get_available_types(self):
        """Test getting available adapter types"""
        types = DatabaseAdapterFactory.get_available_types()
        
        assert DatabaseType.THEMIS in types
        assert DatabaseType.UDS3 in types


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for full workflow"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_mock(self):
        """Test end-to-end workflow with mocks"""
        # Mock adapter
        mock_adapter = MagicMock(spec=IDatabaseAdapter)
        mock_adapter.get_backend_type.return_value = DatabaseType.THEMIS
        mock_adapter.supports_feature.return_value = True
        mock_adapter.execute_aql = AsyncMock(return_value=[
            {
                "doc_id": "doc1",
                "content": "BGB §123 content",
                "score": 0.92,
                "metadata": {"year": 2023}
            }
        ])
        mock_adapter.get_stats.return_value = {"total_queries": 0}
        mock_adapter.health_check = AsyncMock(return_value={
            "status": "healthy",
            "available": True
        })
        
        # Create agent
        agent = ThemisDBRAGAgent(adapter=mock_adapter)
        
        # Retrieve
        results = await agent.retrieve(
            query="BGB Vertragsrecht",
            top_k=5,
            domain="verwaltungsrecht"
        )
        
        # Verify
        assert len(results) > 0
        assert results[0].doc_id == "doc1"
        assert results[0].score == 0.92
        
        # Check stats
        stats = agent.get_stats()
        assert stats["total_queries"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
