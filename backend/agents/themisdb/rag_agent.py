"""
ThemisDB RAG Agent - Main Implementation (OOP Best-Practice)
===========================================================

Hauptklasse die sowohl ThemisDB als auch UDS3 Adapter nutzen kann.

Design Patterns:
- Dependency Injection
- Strategy Pattern
- Adapter Pattern
- Factory Pattern

SOLID Principles:
- Single Responsibility
- Open/Closed
- Liskov Substitution
- Interface Segregation
- Dependency Inversion

Author: VERITAS Backend Team
Date: 2025-12-03
Version: 2.0 (OOP Refactoring)
"""

import logging
from typing import Any, Dict, List, Optional

from .adapters import (
    DatabaseConfig,
    DatabaseType,
    DocumentResult,
    IDatabaseAdapter,
    SearchOptions,
    DatabaseAdapterFactory,
    AdapterSelector,
)
from .base import (
    QueryContext,
    QueryComplexity,
    QueryPlan,
    QueryResult,
    RAGDocument,
    QueryPlanner,
    QueryStrategy,
    EmbeddingProvider,
    CacheProvider,
)
from .implementations import (
    AQLQueryPlanner,
    StandardQueryStrategy,
    InMemoryCache,
    RAGDocumentTransformer,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Main RAG Agent
# ============================================================================

class ThemisDBRAGAgent:
    """
    RAG Agent with pluggable database adapters.
    
    Design Pattern: Facade Pattern
    Principle: Dependency Inversion - Depends on IDatabaseAdapter interface
    
    Features:
    - Works with both ThemisDB and UDS3 adapters
    - Automatic adapter selection and fallback
    - Query planning and optimization
    - Caching and performance tracking
    """
    
    def __init__(
        self,
        adapter: IDatabaseAdapter,
        planner: Optional[QueryPlanner] = None,
        strategy: Optional[QueryStrategy] = None,
        cache: Optional[CacheProvider] = None
    ):
        """
        Initialize RAG Agent with dependencies.
        
        Principle: Dependency Injection
        
        Args:
            adapter: Database adapter (ThemisDB or UDS3)
            planner: Query planner (default: AQLQueryPlanner)
            strategy: Query execution strategy (default: StandardQueryStrategy)
            cache: Cache provider (default: InMemoryCache)
        """
        self._adapter = adapter
        self._planner = planner or AQLQueryPlanner()
        self._cache = cache or InMemoryCache()
        
        # Strategy needs adapter as executor
        if strategy is None:
            # Create embedding provider adapter
            embedding_provider = self._create_embedding_provider()
            self._strategy = StandardQueryStrategy(
                executor=adapter,
                embedding_provider=embedding_provider,
                cache_provider=self._cache
            )
        else:
            self._strategy = strategy
        
        self._stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "cache_hits": 0,
            "avg_latency_ms": 0.0
        }
        
        logger.info(
            f"✅ ThemisDBRAGAgent initialized with {adapter.get_backend_type().value} adapter"
        )
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        domain: str = "general",
        **kwargs
    ) -> List[RAGDocument]:
        """
        Retrieve documents for RAG pipeline.
        
        Main API method - Works with both ThemisDB and UDS3.
        
        Args:
            query: User query text
            top_k: Number of documents to retrieve
            domain: Domain for query optimization
            **kwargs: Additional options (threshold, context_depth, etc.)
            
        Returns:
            List of RAG-optimized documents
        """
        import time
        start_time = time.time()
        self._stats["total_queries"] += 1
        
        try:
            # 1. Build query context
            context = self._build_context(query, domain, top_k, **kwargs)
            
            # 2. Plan query
            plan = self._planner.plan(context)
            
            logger.info(
                f"📋 Query plan: {plan.query_type.value}, "
                f"cost: {plan.estimated_cost:.1f}, "
                f"backend: {self._adapter.get_backend_type().value}"
            )
            
            # 3. Execute query
            result = await self._strategy.execute(plan, context)
            
            # 4. Update stats
            self._stats["successful_queries"] += 1
            latency_ms = (time.time() - start_time) * 1000
            self._update_latency(latency_ms)
            
            logger.info(
                f"✅ Retrieved {result.count} documents in {latency_ms:.1f}ms "
                f"(backend: {self._adapter.get_backend_type().value})"
            )
            
            return result.data
            
        except Exception as e:
            self._stats["failed_queries"] += 1
            logger.error(f"❌ Retrieval failed: {e}")
            
            # Try fallback if available
            if kwargs.get("enable_fallback", True):
                return await self._fallback_retrieve(query, top_k)
            raise
    
    async def retrieve_with_context(
        self,
        query: str,
        top_k: int = 5,
        context_depth: int = 2,
        **kwargs
    ) -> List[RAGDocument]:
        """
        Retrieve documents with graph-based context enrichment.
        
        Args:
            query: User query text
            top_k: Number of documents to retrieve
            context_depth: Graph traversal depth for context
            **kwargs: Additional options
            
        Returns:
            List of RAG documents with enriched context
        """
        # Check if adapter supports graph traversal
        if not self._adapter.supports_feature("graph_traversal"):
            logger.warning(
                f"⚠️ {self._adapter.get_backend_type().value} doesn't support "
                f"graph traversal, falling back to simple retrieval"
            )
            return await self.retrieve(query, top_k, **kwargs)
        
        # Add context enrichment capability
        kwargs["capabilities"] = kwargs.get("capabilities", [])
        kwargs["capabilities"].append("context_enrichment")
        kwargs["context_depth"] = context_depth
        
        return await self.retrieve(query, top_k, **kwargs)
    
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        **kwargs
    ) -> List[RAGDocument]:
        """
        Perform hybrid search (vector + graph).
        
        Args:
            query: User query text
            top_k: Number of documents to retrieve
            **kwargs: Additional options
            
        Returns:
            List of RAG documents from hybrid search
        """
        # Check if adapter supports hybrid search
        if not self._adapter.supports_feature("graph_traversal"):
            logger.warning(
                f"⚠️ {self._adapter.get_backend_type().value} doesn't support "
                f"hybrid search, falling back to vector search"
            )
            return await self.retrieve(query, top_k, **kwargs)
        
        # Add hybrid capabilities
        kwargs["capabilities"] = ["vector_search", "graph_traversal"]
        
        return await self.retrieve(query, top_k, **kwargs)
    
    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about current backend.
        
        Returns:
            Backend information dict
        """
        return {
            "type": self._adapter.get_backend_type().value,
            "connected": True,
            "features": self._get_supported_features(),
            "stats": self._adapter.get_stats()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG agent statistics"""
        return {
            **self._stats,
            "backend": self._adapter.get_backend_type().value,
            "cache_hit_rate": (
                self._stats["cache_hits"] / self._stats["total_queries"]
                if self._stats["total_queries"] > 0 else 0.0
            )
        }
    
    def clear_cache(self) -> None:
        """Clear query cache"""
        self._cache.clear()
        logger.info("🗑️ Cache cleared")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of RAG agent and backend.
        
        Returns:
            Health status dict
        """
        backend_health = await self._adapter.health_check()
        
        return {
            "agent_status": "healthy",
            "backend_status": backend_health["status"],
            "backend_type": self._adapter.get_backend_type().value,
            "backend_available": backend_health["available"],
            "backend_latency_ms": backend_health.get("latency_ms", 0.0)
        }
    
    # Private methods
    
    def _build_context(
        self,
        query: str,
        domain: str,
        top_k: int,
        **kwargs
    ) -> QueryContext:
        """Build query context from parameters"""
        capabilities = kwargs.get("capabilities", ["vector_search"])
        if isinstance(capabilities, list):
            capabilities = frozenset(capabilities)
        
        return QueryContext(
            user_query=query,
            query_intent=kwargs.get("intent", "information_retrieval"),
            complexity=QueryComplexity(kwargs.get("complexity", "medium")),
            domain=domain,
            capabilities=capabilities,
            metadata={
                "top_k": top_k,
                "threshold": kwargs.get("threshold", 0.7),
                "context_depth": kwargs.get("context_depth", 0),
                "collection": kwargs.get("collection", "documents"),
                **kwargs.get("filters", {})
            }
        )
    
    async def _fallback_retrieve(
        self,
        query: str,
        top_k: int
    ) -> List[RAGDocument]:
        """Fallback to simple vector search"""
        logger.info("⚠️ Falling back to simple vector search")
        
        try:
            options = SearchOptions(
                top_k=top_k,
                threshold=0.7,
                collection="documents"
            )
            
            results = await self._adapter.vector_search(query, options)
            
            # Convert to RAGDocument
            transformer = RAGDocumentTransformer()
            rag_docs = []
            for result in results:
                rag_docs.append(RAGDocument(
                    doc_id=result.doc_id,
                    content=result.content,
                    score=result.score,
                    metadata=result.metadata,
                    source=result.source
                ))
            
            return rag_docs
            
        except Exception as e:
            logger.error(f"❌ Fallback retrieval failed: {e}")
            return []
    
    def _get_supported_features(self) -> List[str]:
        """Get list of supported features"""
        features = [
            "vector_search", "graph_traversal", "full_text_search",
            "hybrid_search", "context_enrichment"
        ]
        return [f for f in features if self._adapter.supports_feature(f)]
    
    def _update_latency(self, latency_ms: float):
        """Update average latency statistics"""
        total = self._stats["total_queries"]
        current_avg = self._stats["avg_latency_ms"]
        self._stats["avg_latency_ms"] = (
            (current_avg * (total - 1) + latency_ms) / total
        )
    
    def _create_embedding_provider(self) -> EmbeddingProvider:
        """Create embedding provider from adapter"""
        # Wrapper to make adapter conform to EmbeddingProvider protocol
        class AdapterEmbeddingProvider:
            def __init__(self, adapter):
                self.adapter = adapter
            
            async def embed_text(self, text: str) -> List[float]:
                # Delegate to adapter's embedding method
                if hasattr(self.adapter, '_get_embedding'):
                    return await self.adapter._get_embedding(text)
                # Fallback to mock embedding
                return [0.0] * 768
        
        return AdapterEmbeddingProvider(self._adapter)


# ============================================================================
# Factory Functions
# ============================================================================

async def create_rag_agent(
    adapter_type: Optional[DatabaseType] = None,
    config: Optional[DatabaseConfig] = None,
    enable_fallback: bool = True
) -> ThemisDBRAGAgent:
    """
    Factory function to create RAG agent.
    
    Design Pattern: Factory Method
    
    Args:
        adapter_type: Preferred database type (None = auto-select)
        config: Database configuration (None = from environment)
        enable_fallback: Enable automatic fallback to alternative adapter
        
    Returns:
        Initialized ThemisDBRAGAgent
        
    Example:
        # Auto-select best adapter
        agent = await create_rag_agent()
        
        # Force ThemisDB
        agent = await create_rag_agent(adapter_type=DatabaseType.THEMIS)
        
        # Force UDS3
        agent = await create_rag_agent(adapter_type=DatabaseType.UDS3)
    """
    if config:
        # Use provided config
        adapter = await DatabaseAdapterFactory.create(config)
    else:
        # Auto-select adapter
        adapter = await AdapterSelector.select_best_adapter(
            preferred_type=adapter_type,
            fallback=enable_fallback
        )
    
    return ThemisDBRAGAgent(adapter)


async def create_themisdb_agent() -> ThemisDBRAGAgent:
    """Create RAG agent with ThemisDB adapter"""
    return await create_rag_agent(adapter_type=DatabaseType.THEMIS, enable_fallback=False)


async def create_uds3_agent() -> ThemisDBRAGAgent:
    """Create RAG agent with UDS3 adapter"""
    return await create_rag_agent(adapter_type=DatabaseType.UDS3, enable_fallback=False)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Example 1: Auto-select adapter (ThemisDB with UDS3 fallback)
        agent = await create_rag_agent()
        
        print(f"Backend: {agent.get_backend_info()}")
        
        # Example 2: Retrieve documents
        results = await agent.retrieve(
            query="BGB Vertragsrecht Minderjährige",
            top_k=5,
            domain="verwaltungsrecht"
        )
        
        print(f"\nRetrieved {len(results)} documents:")
        for doc in results[:3]:
            print(f"- {doc.doc_id}: {doc.score:.3f}")
        
        # Example 3: Hybrid search
        results = await agent.hybrid_search(
            query="Immissionsschutz TA Luft",
            top_k=10
        )
        
        print(f"\nHybrid search: {len(results)} documents")
        
        # Example 4: Context-enriched retrieval
        results = await agent.retrieve_with_context(
            query="DIN EN Normen Brandschutz",
            top_k=5,
            context_depth=2
        )
        
        print(f"\nContext-enriched: {len(results)} documents")
        
        # Stats
        print(f"\nAgent Stats: {agent.get_stats()}")
        print(f"Backend Info: {agent.get_backend_info()}")
        
        # Health check
        health = await agent.health_check()
        print(f"\nHealth: {health}")
    
    asyncio.run(main())
