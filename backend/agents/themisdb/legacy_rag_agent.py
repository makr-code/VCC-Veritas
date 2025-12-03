"""
ThemisDB AQL RAG Agent
======================

Agent für RAG-optimiertes Retrieval mit ThemisDB AQL Query Engineering.

Features:
- Multi-Modal Query Execution (Vector + Graph + Document)
- AQL Prompt Engineering für optimale RAG-Performance
- Intelligent Query Planning & Caching
- Context Enrichment via Graph Traversal
- Fallback-Strategien

Author: VERITAS Backend Team
Date: 2025-12-03
Version: 1.0
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AQLQueryType(Enum):
    """ThemisDB AQL Query Types"""
    VECTOR_SEARCH = "vector_search"
    GRAPH_TRAVERSAL = "graph_traversal"
    DOCUMENT_FILTER = "document_filter"
    HYBRID_QUERY = "hybrid_query"
    AGGREGATION = "aggregation"
    CONTEXT_ENRICHED = "context_enriched"


@dataclass
class AQLPromptContext:
    """Context for AQL Prompt Engineering"""
    user_query: str
    query_intent: str = "information_retrieval"
    query_complexity: str = "medium"
    domain: str = "general"
    required_capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AQLQueryPlan:
    """Execution plan for AQL query"""
    query_type: AQLQueryType
    aql_query: str
    bind_vars: Dict[str, Any]
    estimated_cost: float = 0.0
    use_cache: bool = True
    timeout_seconds: int = 30


class ThemisDBPromptEngineer:
    """
    AQL Prompt Engineering for RAG Optimization
    
    Konvertiert natürliche Sprache zu optimierten AQL-Queries
    basierend auf Query-Intent und Domain-Kontext.
    """
    
    def __init__(self):
        self.templates = self._load_aql_templates()
        self.domain_mappings = self._load_domain_mappings()
        logger.info("✅ ThemisDBPromptEngineer initialisiert")
    
    def engineer_aql_query(
        self,
        context: AQLPromptContext
    ) -> AQLQueryPlan:
        """
        Generiert optimierten AQL Query Plan aus Prompt Context.
        
        Strategie:
        1. Intent Detection (Vector/Graph/Document/Hybrid)
        2. Template Selection basierend auf Domain
        3. Parameter Binding aus Kontext
        4. Query Optimization (Indizes, Limits, Caching)
        5. Cost Estimation
        
        Args:
            context: AQLPromptContext mit Query-Details
            
        Returns:
            AQLQueryPlan mit optimiertem Query
        """
        # 1. Detect query type
        query_type = self._detect_query_type(context)
        
        # 2. Select template
        template_key = f"{query_type.value}_{context.domain}"
        template = self.templates.get(
            template_key,
            self.templates[query_type.value]
        )
        
        # 3. Extract parameters
        bind_vars = self._extract_bind_vars(context)
        
        # 4. Build AQL query
        aql_query = template
        
        # 5. Optimize query
        aql_query = self._optimize_query(aql_query, context)
        
        # 6. Estimate cost
        cost = self._estimate_cost(aql_query, bind_vars)
        
        return AQLQueryPlan(
            query_type=query_type,
            aql_query=aql_query,
            bind_vars=bind_vars,
            estimated_cost=cost,
            use_cache=cost < 100  # Cache low-cost queries
        )
    
    def _detect_query_type(self, context: AQLPromptContext) -> AQLQueryType:
        """Erkennt Query-Typ aus Intent und Capabilities"""
        capabilities = set(context.required_capabilities)
        
        # Context enrichment wenn explizit angefordert
        if "context_enrichment" in capabilities:
            return AQLQueryType.CONTEXT_ENRICHED
        
        # Hybrid wenn Vector + Graph
        if "vector_search" in capabilities and "graph_traversal" in capabilities:
            return AQLQueryType.HYBRID_QUERY
        
        # Vector Search als häufigster Fall
        if "vector_search" in capabilities:
            return AQLQueryType.VECTOR_SEARCH
        
        # Graph Traversal
        if "graph_traversal" in capabilities:
            return AQLQueryType.GRAPH_TRAVERSAL
        
        # Aggregation wenn im Intent
        if "aggregation" in context.query_intent.lower():
            return AQLQueryType.AGGREGATION
        
        # Default: Document Filter
        return AQLQueryType.DOCUMENT_FILTER
    
    def _extract_bind_vars(self, context: AQLPromptContext) -> Dict[str, Any]:
        """Extrahiert Bind Variables aus Context"""
        bind_vars = {
            "@collection": "documents",
            "threshold": 0.7,
            "limit": 10
        }
        
        # Domain-spezifische Anpassungen
        if context.domain == "verwaltungsrecht":
            bind_vars["@collection"] = "verwaltungsgesetze"
            bind_vars["threshold"] = 0.65  # Niedrigere Threshold für Rechtsdokumente
        elif context.domain == "technical_standards":
            bind_vars["@collection"] = "technische_normen"
            bind_vars["threshold"] = 0.75  # Höhere Threshold für präzise Standards
        
        # Metadata aus Context
        bind_vars.update(context.metadata)
        
        return bind_vars
    
    def _optimize_query(self, aql_query: str, context: AQLPromptContext) -> str:
        """Optimiert AQL Query für Performance"""
        # Add cache hint für low-complexity queries
        if context.query_complexity == "low":
            aql_query = f"/* +cache */\n{aql_query}"
        
        # Add profiling für high-complexity queries
        if context.query_complexity == "high":
            aql_query = f"/* +profile */\n{aql_query}"
        
        return aql_query.strip()
    
    def _estimate_cost(self, aql_query: str, bind_vars: Dict[str, Any]) -> float:
        """Schätzt Query-Kosten (simplified)"""
        cost = 10.0  # Base cost
        
        # Vector search: +20
        if "COSINE_SIMILARITY" in aql_query:
            cost += 20
        
        # Graph traversal: +50 per depth level
        if "GRAPH" in aql_query or "OUTBOUND" in aql_query:
            depth = bind_vars.get("graph_depth", 1)
            cost += 50 * depth
        
        # Collection size factor
        limit = bind_vars.get("limit", 10)
        cost += limit * 0.5
        
        return cost
    
    def _load_aql_templates(self) -> Dict[str, str]:
        """Lädt AQL Query Templates"""
        return {
            "vector_search": """
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
            """,
            
            "hybrid_query": """
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
                      RETURN {doc: vertex, edge: edge, source: "graph"}
                )
                
                // Step 3: Merge & Re-rank
                LET merged = UNION_DISTINCT(vector_results, graph_results)
                
                FOR result IN merged
                  SORT result.score DESC
                  LIMIT @final_limit
                  RETURN result
            """,
            
            "context_enriched": """
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
                        summary: v.summary
                      }
                  )
                  
                  RETURN {
                    doc_id: doc._key,
                    content: doc.content,
                    score: similarity,
                    metadata: doc.metadata,
                    rag_context: {
                      related_documents: related
                    }
                  }
            """
        }
    
    def _load_domain_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Lädt Domain-spezifische Mappings"""
        return {
            "verwaltungsrecht": {
                "collection": "verwaltungsgesetze",
                "threshold": 0.65,
                "fields": ["gesetzestext", "kommentar", "fundstelle"]
            },
            "technical_standards": {
                "collection": "technische_normen",
                "threshold": 0.75,
                "fields": ["standard_number", "title", "content"]
            },
            "general": {
                "collection": "documents",
                "threshold": 0.7,
                "fields": ["content", "title"]
            }
        }


class ThemisDBRAGAgent:
    """
    ThemisDB RAG Agent mit AQL-basiertem Retrieval
    
    Capabilities:
    - Multi-Model Query Execution (Vector + Graph + Document)
    - AQL Prompt Engineering für optimale RAG-Performance
    - Intelligent Query Planning & Caching
    - Context Enrichment via Graph Traversal
    """
    
    def __init__(self, themisdb_adapter, config: Optional[Dict] = None):
        """
        Initialisiert ThemisDB RAG Agent
        
        Args:
            themisdb_adapter: ThemisDBAdapter Instance
            config: Optionale Konfiguration
        """
        self.adapter = themisdb_adapter
        self.config = config or {}
        self.prompt_engineer = ThemisDBPromptEngineer()
        self.query_cache = {}
        self._stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_latency_ms": 0.0
        }
        
        logger.info("✅ ThemisDBRAGAgent initialisiert")
    
    async def retrieve_with_rag(
        self,
        query: str,
        top_k: int = 5,
        context_depth: int = 2,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        RAG-optimiertes Retrieval mit AQL Query Engineering.
        
        Pipeline:
        1. Prompt Engineering (Query → AQL)
        2. Query Execution (ThemisDB)
        3. Context Enrichment (Optional)
        4. Result Re-ranking (Optional)
        5. RAG-Format Transformation
        
        Args:
            query: User-Query in natürlicher Sprache
            top_k: Anzahl Top-Dokumente
            context_depth: Graph-Traversal-Tiefe für Context
            **kwargs: Zusätzliche Parameter (domain, filters, etc.)
            
        Returns:
            RAG-optimierte Dokumente mit Context
        """
        start_time = time.time()
        self._stats["total_queries"] += 1
        
        # 1. Build prompt context
        prompt_context = AQLPromptContext(
            user_query=query,
            query_intent=kwargs.get("intent", "information_retrieval"),
            query_complexity=kwargs.get("complexity", "medium"),
            domain=kwargs.get("domain", "general"),
            required_capabilities=kwargs.get("capabilities", ["vector_search"]),
            metadata={
                "top_k": top_k,
                "context_depth": context_depth,
                **kwargs.get("filters", {})
            }
        )
        
        # 2. Engineer AQL query
        query_plan = self.prompt_engineer.engineer_aql_query(prompt_context)
        
        # 3. Check cache
        cache_key = self._get_cache_key(query_plan)
        if query_plan.use_cache and cache_key in self.query_cache:
            logger.info(f"🎯 Cache hit for query: {query[:50]}")
            self._stats["cache_hits"] += 1
            return self.query_cache[cache_key]
        
        self._stats["cache_misses"] += 1
        
        # 4. Execute AQL query
        try:
            # Get embedding if needed
            if "query_vector" not in query_plan.bind_vars:
                query_plan.bind_vars["query_vector"] = await self._get_embedding(query)
            
            # Execute query
            results = await self.adapter.execute_aql(
                query=query_plan.aql_query,
                bind_vars=query_plan.bind_vars
            )
            
            # 5. Transform to RAG format
            rag_results = self._transform_to_rag_format(results)
            
            # 6. Cache results
            if query_plan.use_cache:
                self.query_cache[cache_key] = rag_results
            
            # Update stats
            latency_ms = (time.time() - start_time) * 1000
            self._update_latency_stats(latency_ms)
            
            logger.info(
                f"✅ RAG Query completed: {len(rag_results)} results in {latency_ms:.1f}ms "
                f"(type: {query_plan.query_type.value})"
            )
            
            return rag_results
            
        except Exception as e:
            logger.error(f"❌ RAG Query failed: {e}")
            # Fallback: Simple vector search
            return await self._fallback_vector_search(query, top_k)
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Generiert Embedding für Text"""
        # Use adapter's embedding method
        return await self.adapter._embed(text)
    
    async def _fallback_vector_search(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Fallback zu simpler Vector Search"""
        logger.info("⚠️ Falling back to simple vector search")
        
        try:
            results = await self.adapter.vector_search(
                query=query,
                top_k=top_k,
                collection="documents"
            )
            return results
        except Exception as e:
            logger.error(f"❌ Fallback vector search failed: {e}")
            return []
    
    def _transform_to_rag_format(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Transformiert AQL-Ergebnisse zu RAG-Format"""
        rag_results = []
        
        for result in results:
            # Handle different result structures
            if "doc" in result:
                doc = result["doc"]
                score = result.get("score", 0.0)
            else:
                doc = result
                score = result.get("score", 0.0)
            
            rag_doc = {
                "doc_id": result.get("doc_id", doc.get("_key", "")),
                "content": result.get("content", doc.get("content", "")),
                "score": score,
                "metadata": result.get("metadata", doc.get("metadata", {})),
                "context": result.get("rag_context", {}),
                "source": result.get("source", "themisdb_aql")
            }
            rag_results.append(rag_doc)
        
        return rag_results
    
    def _get_cache_key(self, query_plan: AQLQueryPlan) -> str:
        """Generiert Cache-Key für Query"""
        # Create hash from query + bind vars
        query_str = f"{query_plan.aql_query}:{str(sorted(query_plan.bind_vars.items()))}"
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def _update_latency_stats(self, latency_ms: float):
        """Aktualisiert Latenz-Statistiken"""
        total = self._stats["total_queries"]
        current_avg = self._stats["avg_latency_ms"]
        
        # Rolling average
        self._stats["avg_latency_ms"] = (
            (current_avg * (total - 1) + latency_ms) / total
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Agent-Statistiken zurück"""
        return {
            **self._stats,
            "cache_hit_rate": (
                self._stats["cache_hits"] / self._stats["total_queries"]
                if self._stats["total_queries"] > 0 else 0.0
            )
        }
    
    def clear_cache(self):
        """Leert Query Cache"""
        self.query_cache.clear()
        logger.info("🗑️ Query cache cleared")


# Factory function for easy initialization
def create_themisdb_rag_agent(
    themisdb_adapter,
    config: Optional[Dict] = None
) -> ThemisDBRAGAgent:
    """
    Factory function to create ThemisDB RAG Agent
    
    Args:
        themisdb_adapter: ThemisDBAdapter instance
        config: Optional configuration
        
    Returns:
        ThemisDBRAGAgent instance
    """
    return ThemisDBRAGAgent(themisdb_adapter, config)


if __name__ == "__main__":
    # Example usage
    import asyncio
    from backend.adapters.themisdb_adapter import ThemisDBAdapter, ThemisDBConfig
    
    async def main():
        # Initialize adapter
        config = ThemisDBConfig()
        adapter = ThemisDBAdapter(config)
        
        # Create RAG agent
        rag_agent = create_themisdb_rag_agent(adapter)
        
        # Example query
        results = await rag_agent.retrieve_with_rag(
            query="BGB Vertragsrecht Minderjährige",
            top_k=5,
            domain="verwaltungsrecht",
            capabilities=["vector_search", "context_enrichment"]
        )
        
        print(f"Retrieved {len(results)} documents:")
        for doc in results:
            print(f"- {doc['doc_id']}: {doc['score']:.3f}")
        
        # Stats
        print(f"\nAgent Stats: {rag_agent.get_stats()}")
        
        # Cleanup
        await adapter.close()
    
    asyncio.run(main())
