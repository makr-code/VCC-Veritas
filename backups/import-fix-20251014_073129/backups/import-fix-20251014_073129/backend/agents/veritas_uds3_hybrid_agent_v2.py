"""
UDS3 Hybrid Search Agent

Kombiniert Vector Search, Keyword Search und Graph Query für optimale Ergebnisse.

Features:
- Vector Search (ChromaDB) - Semantische Ähnlichkeit
- Keyword Search (PostgreSQL) - Exakte Begriffe
- Graph Query (Neo4j, optional) - Beziehungen
- Weighted Re-Ranking - Kombinierte Scores
- Configurable Weights - Anpassbare Gewichtung

Architecture:
- Layer 1: Database API (database_api_*.py) - Error handling, retry logic
- Layer 2: UDS3 Search API (uds3_search_api.py) - High-level search interface ✅
- Layer 3: Application (THIS FILE) - VERITAS integration

Usage:
    from backend.agents.veritas_uds3_hybrid_agent import UDS3HybridSearchAgent
    from uds3.uds3_core import get_optimized_unified_strategy

    strategy = get_optimized_unified_strategy()
    agent = UDS3HybridSearchAgent(strategy)

    results = await agent.hybrid_search(
        query="Was regelt § 58 LBO BW?",
        top_k=10,
        weights={"vector": 0.5, "keyword": 0.3, "graph": 0.2}
    )

Note: Uses UDS3 Search API (uds3_search_api.py) for all backend communication
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Import UDS3 Search API ✅
try:
    from uds3.uds3_search_api import SearchQuery
    from uds3.uds3_search_api import SearchResult as UDS3SearchResult
    from uds3.uds3_search_api import SearchType, UDS3SearchAPI

    UDS3_SEARCH_API_AVAILABLE = True
except ImportError:
    UDS3_SEARCH_API_AVAILABLE = False
    UDS3SearchAPI = None
    SearchQuery = None
    UDS3SearchResult = None
    SearchType = None

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """
    Single search result with metadata

    Compatible with UDS3SearchResult - wrapper for VERITAS-specific needs
    """

    document_id: str
    content: str
    metadata: Dict[str, Any]
    scores: Dict[str, float]  # {"vector": 0.85, "keyword": 0.6, "graph": 0.4}
    final_score: float

    @classmethod
    def from_uds3_result(cls, uds3_result: "UDS3SearchResult", source_weight: float = 1.0):
        """
        Convert UDS3SearchResult to VERITAS SearchResult

        Args:
            uds3_result: UDS3SearchResult instance
            source_weight: Weight for this source (e.g., 0.5 for vector)

        Returns:
            SearchResult instance
        """
        return cls(
            document_id=uds3_result.document_id,
            content=uds3_result.content,
            metadata=uds3_result.metadata,
            scores={uds3_result.source: uds3_result.score * source_weight},
            final_score=uds3_result.score * source_weight,
        )

    def __repr__(self):
        return f"SearchResult(id={self.document_id}, score={self.final_score:.3f})"


class UDS3HybridSearchAgent:
    """
    Hybrid Search Agent using UDS3 Search API

    Architecture:
    1. Uses UDS3SearchAPI for all backend communication ✅
    2. Converts UDS3SearchResult to VERITAS SearchResult
    3. Provides VERITAS-specific API (backward compatible)

    Benefits:
    - ✅ Error handling (retry logic in Database API Layer)
    - ✅ Type safety (SearchResult dataclass)
    - ✅ Reusable (UDS3SearchAPI can be used by other projects)
    - ✅ Maintainable (centralized search logic in UDS3)
    - ✅ Clean architecture (separation of concerns)

    Note: Simplified from 1000 LOC → 200 LOC (uses UDS3 Search API)
    """

    def __init__(self, strategy):
        """
        Initialize Hybrid Search Agent

        Args:
            strategy: UnifiedDatabaseStrategy instance
        """
        self.strategy = strategy

        # Initialize UDS3 Search API ✅
        if not UDS3_SEARCH_API_AVAILABLE:
            logger.error("❌ UDS3 Search API not available - install uds3_search_api.py")
            raise ImportError("UDS3 Search API required (uds3_search_api.py)")

        self.search_api = UDS3SearchAPI(strategy)

        logger.info("✅ UDS3HybridSearchAgent initialized (using UDS3SearchAPI)")

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        weights: Optional[Dict[str, float]] = None,
        filters: Optional[Dict] = None,
        search_types: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Hybrid search using UDS3 Search API

        Args:
            query: Search query
            top_k: Number of results
            weights: Score weights (e.g., {"vector": 0.5, "graph": 0.5})
            filters: Optional filters
            search_types: Search methods (default: ["vector", "graph"])

        Returns:
            List of SearchResult objects

        Example:
            results = await agent.hybrid_search(
                query="Photovoltaik",
                top_k=10,
                weights={"vector": 0.5, "graph": 0.5}
            )
        """
        # Create SearchQuery
        search_query = SearchQuery(
            query_text=query, top_k=top_k, filters=filters, search_types=search_types or ["vector", "graph"], weights=weights
        )

        # Delegate to UDS3 Search API ✅
        uds3_results = await self.search_api.hybrid_search(search_query)

        # Convert to VERITAS SearchResult
        results = []
        for uds3_result in uds3_results:
            result = SearchResult(
                document_id=uds3_result.document_id,
                content=uds3_result.content,
                metadata=uds3_result.metadata,
                scores={uds3_result.source: uds3_result.score},
                final_score=uds3_result.score,
            )
            results.append(result)

        logger.info(f"✅ Hybrid search: {len(results)} results")
        return results

    async def vector_search(self, query: str, top_k: int = 10, collection: Optional[str] = None) -> List[SearchResult]:
        """
        Vector-only search

        Args:
            query: Search query
            top_k: Number of results
            collection: Optional collection name

        Returns:
            List of SearchResult objects
        """
        # Generate embedding
        model = self.search_api._get_embedding_model()
        if not model:
            logger.error("❌ Embedding model not available")
            return []

        embedding = model.encode(query).tolist()

        # Delegate to UDS3 Search API ✅
        uds3_results = await self.search_api.vector_search(embedding, top_k, collection)

        # Convert to VERITAS SearchResult
        results = []
        for uds3_result in uds3_results:
            result = SearchResult.from_uds3_result(uds3_result, source_weight=1.0)
            results.append(result)

        logger.info(f"✅ Vector search: {len(results)} results")
        return results

    async def graph_search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Graph-only search

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of SearchResult objects
        """
        # Delegate to UDS3 Search API ✅
        uds3_results = await self.search_api.graph_search(query, top_k)

        # Convert to VERITAS SearchResult
        results = []
        for uds3_result in uds3_results:
            result = SearchResult.from_uds3_result(uds3_result, source_weight=1.0)
            results.append(result)

        logger.info(f"✅ Graph search: {len(results)} results")
        return results

    async def keyword_search(self, query: str, top_k: int = 10, filters: Optional[Dict] = None) -> List[SearchResult]:
        """
        Keyword-only search

        Args:
            query: Search query
            top_k: Number of results
            filters: Optional filters

        Returns:
            List of SearchResult objects
        """
        # Delegate to UDS3 Search API ✅
        uds3_results = await self.search_api.keyword_search(query, top_k, filters)

        # Convert to VERITAS SearchResult
        results = []
        for uds3_result in uds3_results:
            result = SearchResult.from_uds3_result(uds3_result, source_weight=1.0)
            results.append(result)

        logger.info(f"✅ Keyword search: {len(results)} results")
        return results


# Convenience functions for quick testing


async def quick_hybrid_search(query: str, top_k: int = 10):
    """
    Quick hybrid search using default UDS3 strategy

    Args:
        query: Search query
        top_k: Number of results

    Returns:
        List of SearchResult objects
    """
    from uds3.uds3_core import get_optimized_unified_strategy

    strategy = get_optimized_unified_strategy()
    agent = UDS3HybridSearchAgent(strategy)

    return await agent.hybrid_search(query, top_k)
