"""
ThemisDB Agent Framework - Concrete Implementations
===================================================

Konkrete Implementierungen der abstrakten Basis-Klassen
nach OOP Best-Practices und SOLID Principles.

Author: VERITAS Backend Team
Date: 2025-12-03
Version: 2.0 (OOP Refactoring)
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .base import (
    CacheProvider,
    CacheStrategy,
    EmbeddingProvider,
    QueryComplexity,
    QueryContext,
    QueryExecutor,
    QueryPlan,
    QueryPlanner,
    QueryResult,
    QueryStrategy,
    QueryTemplate,
    QueryType,
    RAGDocument,
    ResultTransformer,
    TransformationError,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Concrete Query Templates
# ============================================================================

class VectorSearchTemplate(QueryTemplate):
    """
    Template for vector search queries.
    
    Single Responsibility: Handle vector search query generation
    """
    
    def build_query(self, context: QueryContext) -> str:
        """Build vector search AQL query"""
        return """
            FOR doc IN @@collection
              LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
              FILTER similarity >= @threshold
              SORT similarity DESC
              LIMIT @limit
              RETURN {
                doc_id: doc._key,
                content: doc.content,
                score: similarity,
                metadata: doc.metadata,
                source: "vector_search"
              }
        """
    
    def extract_bind_vars(self, context: QueryContext) -> Dict[str, Any]:
        """Extract bind variables for vector search"""
        return {
            "@collection": context.metadata.get("collection", "documents"),
            "threshold": context.metadata.get("threshold", 0.7),
            "limit": context.metadata.get("top_k", 10)
        }


class HybridQueryTemplate(QueryTemplate):
    """
    Template for hybrid (vector + graph) queries.
    
    Single Responsibility: Handle hybrid query generation
    """
    
    def build_query(self, context: QueryContext) -> str:
        """Build hybrid AQL query"""
        return """
            // Step 1: Vector Search
            LET vector_results = (
              FOR doc IN @@collection
                LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
                FILTER similarity >= @vector_threshold
                SORT similarity DESC
                LIMIT @vector_limit
                RETURN {doc: doc, score: similarity, source: "vector"}
            )
            
            // Step 2: Graph Traversal
            LET graph_results = (
              FOR v IN vector_results
                FOR vertex, edge IN 1..@graph_depth OUTBOUND v.doc._id
                  @edge_collection
                  OPTIONS {uniqueVertices: "path"}
                  RETURN {doc: vertex, edge: edge, source: "graph"}
            )
            
            // Step 3: Merge & Re-rank
            LET merged = UNION_DISTINCT(vector_results, graph_results)
            
            FOR result IN merged
              SORT result.score DESC
              LIMIT @final_limit
              RETURN result
        """
    
    def extract_bind_vars(self, context: QueryContext) -> Dict[str, Any]:
        """Extract bind variables for hybrid query"""
        top_k = context.metadata.get("top_k", 10)
        return {
            "@collection": context.metadata.get("collection", "documents"),
            "@edge_collection": context.metadata.get("edge_collection", "citations"),
            "vector_threshold": context.metadata.get("threshold", 0.7),
            "vector_limit": top_k * 2,  # Over-retrieve for re-ranking
            "graph_depth": context.metadata.get("context_depth", 2),
            "final_limit": top_k
        }


class ContextEnrichedTemplate(QueryTemplate):
    """
    Template for context-enriched RAG queries.
    
    Single Responsibility: Handle context-enriched query generation
    """
    
    def build_query(self, context: QueryContext) -> str:
        """Build context-enriched AQL query"""
        return """
            FOR doc IN @@collection
              LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
              FILTER similarity >= @threshold
              SORT similarity DESC
              LIMIT @limit
              
              // Context Enrichment: Related Documents
              LET related = (
                FOR v IN 1..2 OUTBOUND doc._id
                  citations
                  RETURN {
                    title: v.title,
                    summary: v.summary,
                    type: v.type
                  }
              )
              
              // Context Enrichment: Parent Category
              LET parent = (
                FOR v IN 1..1 INBOUND doc._id
                  hierarchy
                  RETURN {
                    title: v.title,
                    category: v.category
                  }
              )
              
              RETURN {
                doc_id: doc._key,
                title: doc.title,
                content: doc.content,
                score: similarity,
                metadata: doc.metadata,
                rag_context: {
                  related_documents: related,
                  parent_category: parent[0]
                }
              }
        """
    
    def extract_bind_vars(self, context: QueryContext) -> Dict[str, Any]:
        """Extract bind variables for context-enriched query"""
        return {
            "@collection": context.metadata.get("collection", "documents"),
            "threshold": context.metadata.get("threshold", 0.7),
            "limit": context.metadata.get("top_k", 10)
        }


# ============================================================================
# Template Factory (Factory Pattern)
# ============================================================================

class QueryTemplateFactory:
    """
    Factory for creating query templates.
    
    Design Pattern: Factory Pattern
    Principle: Open/Closed - Easy to add new templates
    """
    
    _templates: Dict[QueryType, type[QueryTemplate]] = {
        QueryType.VECTOR_SEARCH: VectorSearchTemplate,
        QueryType.HYBRID: HybridQueryTemplate,
        QueryType.CONTEXT_ENRICHED: ContextEnrichedTemplate,
    }
    
    @classmethod
    def create(cls, query_type: QueryType) -> QueryTemplate:
        """Create template for given query type"""
        template_class = cls._templates.get(query_type)
        if not template_class:
            raise ValueError(f"No template for query type: {query_type}")
        return template_class()
    
    @classmethod
    def register_template(
        cls,
        query_type: QueryType,
        template_class: type[QueryTemplate]
    ) -> None:
        """Register new template (Open/Closed Principle)"""
        cls._templates[query_type] = template_class


# ============================================================================
# Concrete Query Planner
# ============================================================================

class AQLQueryPlanner(QueryPlanner):
    """
    Concrete implementation of query planner.
    
    Single Responsibility: Plan AQL queries based on context
    """
    
    def __init__(self):
        self._template_factory = QueryTemplateFactory()
    
    def plan(self, context: QueryContext) -> QueryPlan:
        """
        Create execution plan from context.
        
        Strategy:
        1. Detect query type from capabilities
        2. Select appropriate template
        3. Build query and extract bind vars
        4. Optimize and estimate cost
        """
        # 1. Detect query type
        query_type = self._detect_query_type(context)
        
        # 2. Get template
        template = self._template_factory.create(query_type)
        
        # 3. Build query
        aql_query = template.build_query(context)
        bind_vars = template.extract_bind_vars(context)
        
        # 4. Optimize
        aql_query = template.optimize_query(aql_query, context)
        
        # 5. Estimate cost
        estimated_cost = template.estimate_cost(aql_query, bind_vars)
        
        # 6. Determine cache strategy
        cache_strategy = self._determine_cache_strategy(estimated_cost, context)
        
        return QueryPlan(
            query_type=query_type,
            aql_query=aql_query,
            bind_vars=bind_vars,
            estimated_cost=estimated_cost,
            cache_strategy=cache_strategy
        )
    
    def supports_query_type(self, query_type: QueryType) -> bool:
        """Check if this planner supports the query type"""
        return query_type in QueryTemplateFactory._templates
    
    def _detect_query_type(self, context: QueryContext) -> QueryType:
        """Detect appropriate query type from context"""
        capabilities = set(context.capabilities)
        
        # Context enrichment
        if "context_enrichment" in capabilities:
            return QueryType.CONTEXT_ENRICHED
        
        # Hybrid query
        if "vector_search" in capabilities and "graph_traversal" in capabilities:
            return QueryType.HYBRID
        
        # Simple vector search
        if "vector_search" in capabilities:
            return QueryType.VECTOR_SEARCH
        
        # Graph traversal
        if "graph_traversal" in capabilities:
            return QueryType.GRAPH_TRAVERSAL
        
        # Default to vector search
        return QueryType.VECTOR_SEARCH
    
    def _determine_cache_strategy(
        self,
        estimated_cost: float,
        context: QueryContext
    ) -> CacheStrategy:
        """Determine optimal cache strategy"""
        # No cache for high-cost queries (they change frequently)
        if estimated_cost > 200:
            return CacheStrategy.NONE
        
        # LRU for medium-cost queries
        if estimated_cost > 50:
            return CacheStrategy.LRU
        
        # Time-based for low-cost queries
        return CacheStrategy.TIME_BASED


# ============================================================================
# Concrete Result Transformer
# ============================================================================

class RAGDocumentTransformer(ResultTransformer[RAGDocument]):
    """
    Transformer for RAG documents.
    
    Single Responsibility: Transform raw results to RAGDocument objects
    """
    
    def transform(self, raw_results: List[Dict[str, Any]]) -> List[RAGDocument]:
        """Transform raw AQL results to RAGDocument objects"""
        documents = []
        
        for result in raw_results:
            try:
                # Handle different result structures
                if "doc" in result:
                    doc = result["doc"]
                    score = result.get("score", 0.0)
                else:
                    doc = result
                    score = result.get("score", 0.0)
                
                rag_doc = RAGDocument(
                    doc_id=result.get("doc_id", doc.get("_key", "")),
                    content=result.get("content", doc.get("content", "")),
                    score=score,
                    metadata=result.get("metadata", doc.get("metadata", {})),
                    context=result.get("rag_context", {}),
                    source=result.get("source", "themisdb")
                )
                documents.append(rag_doc)
                
            except Exception as e:
                logger.error(f"Failed to transform result: {e}")
                raise TransformationError(f"Transformation failed: {e}")
        
        return documents


# ============================================================================
# Concrete Query Strategy
# ============================================================================

class StandardQueryStrategy(QueryStrategy):
    """
    Standard query execution strategy.
    
    Single Responsibility: Execute queries with caching and error handling
    """
    
    async def execute(
        self,
        plan: QueryPlan,
        context: QueryContext
    ) -> QueryResult[RAGDocument]:
        """Execute query with caching and error handling"""
        start_time = time.time()
        
        # 1. Check cache
        if plan.cache_strategy != CacheStrategy.NONE:
            cached = self._get_cached(plan.cache_key)
            if cached:
                logger.info(f"🎯 Cache hit for query: {context.user_query[:50]}")
                return cached
        
        # 2. Add query vector to bind vars if needed
        if "query_vector" not in plan.bind_vars:
            plan.bind_vars["query_vector"] = await self._get_embedding(
                context.user_query
            )
        
        # 3. Execute query
        raw_results = await self._executor.execute_aql(
            query=plan.aql_query,
            bind_vars=plan.bind_vars
        )
        
        # 4. Transform results
        transformer = RAGDocumentTransformer()
        documents = transformer.transform(raw_results)
        
        # 5. Create result
        query_time_ms = (time.time() - start_time) * 1000
        result = QueryResult(
            data=documents,
            metadata={"query_type": plan.query_type.value},
            query_time_ms=query_time_ms,
            source="themisdb"
        )
        
        # 6. Cache result
        if plan.cache_strategy != CacheStrategy.NONE:
            ttl = 300 if plan.cache_strategy == CacheStrategy.TIME_BASED else None
            self._set_cached(plan.cache_key, result, ttl)
        
        logger.info(
            f"✅ Query executed: {len(documents)} results in {query_time_ms:.1f}ms "
            f"(type: {plan.query_type.value})"
        )
        
        return result


# ============================================================================
# Simple In-Memory Cache Implementation
# ============================================================================

class InMemoryCache:
    """
    Simple in-memory cache implementation.
    
    Design Pattern: Singleton (optional)
    Implements: CacheProvider Protocol
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        return self._cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value (TTL not implemented in simple version)"""
        self._cache[key] = value
    
    def delete(self, key: str) -> None:
        """Delete cached value"""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached values"""
        self._cache.clear()
