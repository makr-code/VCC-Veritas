"""
ThemisDB Adapter - Direct Multi-Model Database Integration
Replaces UDS3 Polyglot for single-backend scenarios with better performance.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


@dataclass
class ThemisDBConfig:
    """ThemisDB Connection Configuration"""
    host: str = "localhost"
    port: int = 8765
    use_ssl: bool = False
    api_token: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> "ThemisDBConfig":
        """Load configuration from environment variables"""
        return cls(
            host=os.getenv("THEMIS_HOST", "localhost"),
            port=int(os.getenv("THEMIS_PORT", "8765")),
            use_ssl=os.getenv("THEMIS_USE_SSL", "false").lower() == "true",
            api_token=os.getenv("THEMIS_API_TOKEN"),
            timeout=int(os.getenv("THEMIS_TIMEOUT", "30")),
            max_retries=int(os.getenv("THEMIS_MAX_RETRIES", "3"))
        )


class ThemisDBAdapter:
    """
    Direct Adapter for ThemisDB Multi-Model Database.
    
    Replaces UDS3 PolyglotManager for single-backend scenarios.
    Compatible with existing UDS3VectorSearchAdapter interface.
    
    Features:
    ---------
    - Vector Search (HNSW Index)
    - Graph Traversal (Property Graph Model)
    - AQL Query Execution (Themis Query Language)
    - Document CRUD (JSON Blob Storage)
    - ACID Transactions (MVCC via RocksDB)
    
    Usage:
    ------
    ```python
    from backend.adapters import ThemisDBAdapter, ThemisDBConfig
    
    config = ThemisDBConfig.from_env()
    adapter = ThemisDBAdapter(config)
    
    # Compatible with UDS3VectorSearchAdapter interface
    results = await adapter.vector_search("BGB Vertragsrecht", top_k=5)
    ```
    """
    
    def __init__(self, config: Optional[ThemisDBConfig] = None):
        """
        Initialize ThemisDB Adapter
        
        Args:
            config: ThemisDB configuration (defaults to env-based config)
        """
        self.config = config or ThemisDBConfig.from_env()
        self.base_url = (
            f"{'https' if self.config.use_ssl else 'http'}://"
            f"{self.config.host}:{self.config.port}"
        )
        
        # Initialize HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.config.timeout,
            headers=self._build_headers(),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=50
            )
        )
        
        self._stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'empty_results': 0,
            'total_latency_ms': 0.0
        }
        
        logger.info(
            f"✅ ThemisDBAdapter initialized - {self.base_url} "
            f"(timeout={self.config.timeout}s, retries={self.config.max_retries})"
        )
    
    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for requests"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Veritas-ThemisDB-Adapter/1.0"
        }
        
        if self.config.api_token:
            headers["Authorization"] = f"Bearer {self.config.api_token}"
        
        return headers
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException))
    )
    async def health_check(self) -> Dict[str, Any]:
        """
        Health check for ThemisDB server
        
        Returns:
            Health status dict with server info
            
        Raises:
            httpx.HTTPError: If health check fails
        """
        try:
            response = await self.client.get("/api/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"❌ ThemisDB health check failed: {e}")
            raise
    
    async def vector_search(
        self,
        query: str,
        top_k: int = 5,
        collection: str = "documents",
        threshold: float = 0.0,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Vector Similarity Search via ThemisDB HNSW Index.
        
        Compatible with UDS3VectorSearchAdapter.vector_search() interface.
        
        Args:
            query: Search query string (will be embedded by embedding service)
            top_k: Number of top results to return
            collection: Collection name in ThemisDB
            threshold: Minimum similarity score (0.0 = no filtering)
            **kwargs: Additional parameters (metric, ef_search, etc.)
            
        Returns:
            List of documents with 'doc_id', 'content', 'score', 'metadata'
        """
        import time
        start_time = time.time()
        
        self._stats['total_queries'] += 1
        
        try:
            # Generate embedding (delegated to Veritas embedding service)
            query_vector = await self._embed(query)
            
            # Call ThemisDB vector search API
            response = await self.client.post(
                "/api/vector/search",
                json={
                    "collection": collection,
                    "query_vector": query_vector,
                    "top_k": top_k,
                    "min_score": threshold,
                    **kwargs
                }
            )
            response.raise_for_status()
            
            # Transform ThemisDB response to standard format
            results_data = response.json()
            documents = self._transform_vector_results(results_data.get("results", []))
            
            # Update stats
            latency_ms = (time.time() - start_time) * 1000
            self._stats['total_latency_ms'] += latency_ms
            
            if documents:
                self._stats['successful_queries'] += 1
                logger.debug(
                    f"✅ ThemisDB Vector Search: {len(documents)} docs, "
                    f"{latency_ms:.1f}ms, query: {query[:50]}"
                )
            else:
                self._stats['empty_results'] += 1
                logger.debug(
                    f"ℹ️ ThemisDB Vector Search: 0 results, {latency_ms:.1f}ms"
                )
            
            return documents
            
        except httpx.HTTPError as e:
            self._stats['failed_queries'] += 1
            logger.error(f"❌ ThemisDB vector_search failed: {e}")
            raise
        except Exception as e:
            self._stats['failed_queries'] += 1
            logger.error(f"❌ ThemisDB vector_search error: {e}")
            raise
    
    def _transform_vector_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """
        Transform ThemisDB vector search results to standard format.
        
        ThemisDB Format:
            [{"id": "doc123", "document": {...}, "score": 0.95}, ...]
        
        Standard Format:
            [{"doc_id": "doc123", "content": "...", "score": 0.95, "metadata": {}}, ...]
        """
        transformed = []
        
        for result in results:
            doc = result.get("document", {})
            transformed.append({
                "doc_id": result.get("id", ""),
                "content": doc.get("content", ""),
                "score": result.get("score", 0.0),
                "metadata": doc.get("metadata", {})
            })
        
        return transformed
    
    async def graph_traverse(
        self,
        start_vertex: str,
        edge_collection: str,
        direction: str = "outbound",
        min_depth: int = 1,
        max_depth: int = 3,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Graph Traversal via ThemisDB Property Graph Engine.
        
        Args:
            start_vertex: Starting vertex ID (e.g., "documents/doc123")
            edge_collection: Edge collection name (e.g., "citations")
            direction: Traversal direction ("outbound", "inbound", "any")
            min_depth: Minimum traversal depth
            max_depth: Maximum traversal depth
            **kwargs: Additional filters
            
        Returns:
            List of traversal results with vertices and edges
        """
        try:
            response = await self.client.post(
                "/api/graph/traverse",
                json={
                    "start_vertex": start_vertex,
                    "edge_collection": edge_collection,
                    "direction": direction,
                    "min_depth": min_depth,
                    "max_depth": max_depth,
                    **kwargs
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("paths", [])
            
        except httpx.HTTPError as e:
            logger.error(f"❌ ThemisDB graph_traverse failed: {e}")
            raise
    
    async def execute_aql(
        self,
        query: str,
        bind_vars: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute AQL Query (ThemisDB's Query Language, similar to ArangoDB AQL).
        
        Args:
            query: AQL query string
            bind_vars: Query bind variables (e.g., {"@collection": "docs", "limit": 10})
            
        Returns:
            Query result as list of documents
            
        Example:
            ```python
            result = await adapter.execute_aql(
                "FOR doc IN documents FILTER doc.year >= @year RETURN doc",
                bind_vars={"year": 2020}
            )
            ```
        """
        try:
            response = await self.client.post(
                "/api/aql/query",
                json={
                    "query": query,
                    "bindVars": bind_vars or {}
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("result", [])
            
        except httpx.HTTPError as e:
            logger.error(f"❌ ThemisDB execute_aql failed: {e}")
            raise
    
    async def get_document(
        self,
        collection: str,
        key: str
    ) -> Dict[str, Any]:
        """
        Retrieve single document by key.
        
        Args:
            collection: Collection name
            key: Document key/ID
            
        Returns:
            Document as dict
        """
        try:
            response = await self.client.get(f"/api/document/{collection}/{key}")
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"❌ ThemisDB get_document failed: {e}")
            raise
    
    async def insert_document(
        self,
        collection: str,
        document: Dict[str, Any],
        key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Insert document into collection.
        
        Args:
            collection: Collection name
            document: Document data
            key: Optional document key (auto-generated if not provided)
            
        Returns:
            Inserted document with metadata
        """
        try:
            payload = {"document": document}
            if key:
                payload["key"] = key
            
            response = await self.client.post(
                f"/api/document/{collection}",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"❌ ThemisDB insert_document failed: {e}")
            raise
    
    async def _embed(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Delegates to Veritas embedding service - ThemisDB only stores vectors.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        # Import here to avoid circular dependencies
        try:
            from backend.services.embedding_service import get_embedding_service
            embedding_service = get_embedding_service()
            return await embedding_service.embed_text(text)
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            # Fallback to mock embedding for testing
            logger.warning("⚠️ Using mock embedding (768-dim zeros)")
            return [0.0] * 768
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get adapter statistics.
        
        Returns:
            Statistics dict with query counts and latencies
        """
        return {
            **self._stats,
            'avg_latency_ms': (
                self._stats['total_latency_ms'] / self._stats['total_queries']
                if self._stats['total_queries'] > 0 else 0.0
            ),
            'success_rate': (
                self._stats['successful_queries'] / self._stats['total_queries']
                if self._stats['total_queries'] > 0 else 0.0
            )
        }
    
    async def close(self):
        """Cleanup HTTP client resources"""
        await self.client.aclose()
        logger.info("✅ ThemisDBAdapter closed")
