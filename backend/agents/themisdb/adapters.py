"""
Database Adapter Interface & Implementations
===========================================

Gemeinsame Schnittstelle für verschiedene Database-Backends:
- ThemisDB (Multi-Model Database)
- UDS3 (Polyglot Database Manager)

Design Pattern: Adapter Pattern
Principle: Dependency Inversion - Code gegen Interface, nicht gegen konkrete Implementierung

Author: VERITAS Backend Team
Date: 2025-12-03
Version: 2.0 (OOP Refactoring)
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

# ============================================================================
# Enums & Data Classes
# ============================================================================

class DatabaseType(Enum):
    """Supported database backend types"""
    THEMIS = "themisdb"
    UDS3 = "uds3_polyglot"


@dataclass
class DatabaseConfig:
    """
    Generic database configuration.
    
    Design Pattern: Configuration Object
    """
    db_type: DatabaseType
    host: str = "localhost"
    port: int = 8765
    use_ssl: bool = False
    api_token: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    custom_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_settings is None:
            self.custom_settings = {}


@dataclass
class SearchOptions:
    """
    Generic search options for both adapters.
    
    Principle: Common interface for different backends
    """
    top_k: int = 5
    threshold: float = 0.7
    collection: str = "documents"
    filters: Optional[Dict[str, Any]] = None
    context_depth: int = 0  # Graph traversal depth
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}


@dataclass
class DocumentResult:
    """
    Standardized document result format.
    
    Design Pattern: Data Transfer Object (DTO)
    Principle: Uniform result format across adapters
    """
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    source: str  # "themisdb" or "uds3"
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
            "source": self.source,
            "context": self.context or {}
        }


# ============================================================================
# Abstract Database Adapter (Interface)
# ============================================================================

class IDatabaseAdapter(abc.ABC):
    """
    Abstract interface for database adapters.
    
    Design Pattern: Adapter Pattern
    Principle: Interface Segregation - Clients depend on this interface
    
    Both ThemisDB and UDS3 adapters MUST implement this interface.
    """
    
    @abc.abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to database.
        
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abc.abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check database health.
        
        Returns:
            Health status dict with:
            - status: "healthy" | "degraded" | "unhealthy"
            - available: bool
            - version: Optional[str]
            - latency_ms: float
        """
        pass
    
    @abc.abstractmethod
    async def vector_search(
        self,
        query: str,
        options: SearchOptions
    ) -> List[DocumentResult]:
        """
        Perform vector similarity search.
        
        Args:
            query: Search query text
            options: Search options (top_k, threshold, etc.)
            
        Returns:
            List of document results sorted by relevance
        """
        pass
    
    @abc.abstractmethod
    async def graph_traverse(
        self,
        start_vertex: str,
        edge_collection: str,
        direction: str = "outbound",
        min_depth: int = 1,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Perform graph traversal.
        
        Args:
            start_vertex: Starting vertex ID
            edge_collection: Edge collection name
            direction: Traversal direction ("outbound", "inbound", "any")
            min_depth: Minimum traversal depth
            max_depth: Maximum traversal depth
            
        Returns:
            List of graph paths
        """
        pass
    
    @abc.abstractmethod
    async def execute_query(
        self,
        query: str,
        bind_vars: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute native query (AQL for ThemisDB, custom for UDS3).
        
        Args:
            query: Query string in native format
            bind_vars: Query parameters
            
        Returns:
            Raw query results
        """
        pass
    
    @abc.abstractmethod
    def get_backend_type(self) -> DatabaseType:
        """Get the backend database type"""
        pass
    
    @abc.abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get adapter statistics.
        
        Returns:
            Statistics dict with metrics like:
            - total_queries
            - successful_queries
            - failed_queries
            - avg_latency_ms
        """
        pass
    
    @abc.abstractmethod
    def supports_feature(self, feature: str) -> bool:
        """
        Check if adapter supports specific feature.
        
        Args:
            feature: Feature name (e.g., "graph_traversal", "full_text_search")
            
        Returns:
            True if feature is supported
        """
        pass


# ============================================================================
# ThemisDB Adapter Implementation
# ============================================================================

class ThemisDBAdapter(IDatabaseAdapter):
    """
    ThemisDB adapter implementation.
    
    Design Pattern: Adapter Pattern
    Principle: Adapts ThemisDB API to common interface
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize ThemisDB adapter.
        
        Args:
            config: Database configuration
            
        Raises:
            ValueError: If config.db_type is not THEMIS
        """
        if config.db_type != DatabaseType.THEMIS:
            raise ValueError(f"Expected THEMIS, got {config.db_type}")
        
        self._config = config
        self._client = None  # httpx.AsyncClient
        self._stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_latency_ms": 0.0
        }
        self._connected = False
    
    async def connect(self) -> None:
        """Establish connection to ThemisDB"""
        import httpx
        
        base_url = (
            f"{'https' if self._config.use_ssl else 'http'}://"
            f"{self._config.host}:{self._config.port}"
        )
        
        headers = {"Content-Type": "application/json"}
        if self._config.api_token:
            headers["Authorization"] = f"Bearer {self._config.api_token}"
        
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=self._config.timeout
        )
        
        # Test connection
        await self.health_check()
        self._connected = True
    
    async def disconnect(self) -> None:
        """Close ThemisDB connection"""
        if self._client:
            await self._client.aclose()
            self._connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check ThemisDB health"""
        import time
        start = time.time()
        
        try:
            response = await self._client.get("/api/health")
            response.raise_for_status()
            data = response.json()
            latency_ms = (time.time() - start) * 1000
            
            return {
                "status": "healthy",
                "available": True,
                "version": data.get("version"),
                "latency_ms": latency_ms
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "available": False,
                "error": str(e),
                "latency_ms": (time.time() - start) * 1000
            }
    
    async def vector_search(
        self,
        query: str,
        options: SearchOptions
    ) -> List[DocumentResult]:
        """Perform vector search via ThemisDB"""
        import time
        start = time.time()
        
        self._stats["total_queries"] += 1
        
        try:
            # Generate embedding
            query_vector = await self._get_embedding(query)
            
            # Execute search
            response = await self._client.post(
                "/api/vector/search",
                json={
                    "collection": options.collection,
                    "query_vector": query_vector,
                    "top_k": options.top_k,
                    "min_score": options.threshold,
                    **options.filters
                }
            )
            response.raise_for_status()
            
            # Transform results
            data = response.json()
            results = self._transform_vector_results(data.get("results", []))
            
            self._stats["successful_queries"] += 1
            self._update_latency(time.time() - start)
            
            return results
            
        except Exception as e:
            self._stats["failed_queries"] += 1
            raise
    
    async def graph_traverse(
        self,
        start_vertex: str,
        edge_collection: str,
        direction: str = "outbound",
        min_depth: int = 1,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """Perform graph traversal via ThemisDB"""
        response = await self._client.post(
            "/api/graph/traverse",
            json={
                "start_vertex": start_vertex,
                "edge_collection": edge_collection,
                "direction": direction,
                "min_depth": min_depth,
                "max_depth": max_depth
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("paths", [])
    
    async def execute_query(
        self,
        query: str,
        bind_vars: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute AQL query"""
        response = await self._client.post(
            "/api/aql/query",
            json={
                "query": query,
                "bindVars": bind_vars or {}
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("result", [])
    
    def get_backend_type(self) -> DatabaseType:
        """Get backend type"""
        return DatabaseType.THEMIS
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics"""
        return {
            **self._stats,
            "backend": "themisdb",
            "connected": self._connected
        }
    
    def supports_feature(self, feature: str) -> bool:
        """Check feature support"""
        supported = {
            "vector_search", "graph_traversal", "aql_query",
            "document_crud", "transactions"
        }
        return feature in supported
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text (placeholder)"""
        # TODO: Integrate with embedding service
        return [0.0] * 768
    
    def _transform_vector_results(
        self,
        results: List[Dict]
    ) -> List[DocumentResult]:
        """Transform ThemisDB results to standard format"""
        documents = []
        for result in results:
            doc = result.get("document", {})
            documents.append(DocumentResult(
                doc_id=result.get("id", ""),
                content=doc.get("content", ""),
                score=result.get("score", 0.0),
                metadata=doc.get("metadata", {}),
                source="themisdb",
                context=None
            ))
        return documents
    
    def _update_latency(self, duration: float):
        """Update average latency"""
        total = self._stats["total_queries"]
        current_avg = self._stats["avg_latency_ms"]
        new_latency = duration * 1000
        self._stats["avg_latency_ms"] = (
            (current_avg * (total - 1) + new_latency) / total
        )


# ============================================================================
# UDS3 Adapter Implementation
# ============================================================================

class UDS3Adapter(IDatabaseAdapter):
    """
    UDS3 Polyglot adapter implementation.
    
    Design Pattern: Adapter Pattern
    Principle: Adapts UDS3 API to common interface
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize UDS3 adapter.
        
        Args:
            config: Database configuration
            
        Raises:
            ValueError: If config.db_type is not UDS3
        """
        if config.db_type != DatabaseType.UDS3:
            raise ValueError(f"Expected UDS3, got {config.db_type}")
        
        self._config = config
        self._uds3_manager = None
        self._stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_latency_ms": 0.0
        }
        self._connected = False
    
    async def connect(self) -> None:
        """Initialize UDS3 Polyglot Manager"""
        from uds3.core.polyglot_manager import UDS3PolyglotManager
        
        # Load backend config from custom_settings
        backend_config = self._config.custom_settings.get("backend_config", {
            "relational": {"enabled": True},
            "vector": {"enabled": True},
            "graph": {"enabled": True},
            "file": {"enabled": True}
        })
        
        self._uds3_manager = UDS3PolyglotManager(
            backend_config=backend_config,
            enable_rag=False  # RAG handled at agent level
        )
        
        self._connected = True
    
    async def disconnect(self) -> None:
        """Cleanup UDS3 resources"""
        if self._uds3_manager:
            # UDS3 cleanup if needed
            self._connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check UDS3 health"""
        import time
        start = time.time()
        
        try:
            # UDS3 health check (placeholder - adapt to actual UDS3 API)
            status = "healthy" if self._connected else "unhealthy"
            
            return {
                "status": status,
                "available": self._connected,
                "version": "2.0.0",
                "latency_ms": (time.time() - start) * 1000
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "available": False,
                "error": str(e),
                "latency_ms": (time.time() - start) * 1000
            }
    
    async def vector_search(
        self,
        query: str,
        options: SearchOptions
    ) -> List[DocumentResult]:
        """Perform vector search via UDS3"""
        import time
        start = time.time()
        
        self._stats["total_queries"] += 1
        
        try:
            # UDS3 vector search
            results = await self._uds3_manager.query_across_databases(
                query_text=query,
                vector_params={
                    "top_k": options.top_k,
                    "threshold": options.threshold,
                    "collection": options.collection
                },
                graph_params=None,
                relational_params=None
            )
            
            # Transform UDS3 results
            documents = self._transform_uds3_results(results)
            
            self._stats["successful_queries"] += 1
            self._update_latency(time.time() - start)
            
            return documents
            
        except Exception as e:
            self._stats["failed_queries"] += 1
            raise
    
    async def graph_traverse(
        self,
        start_vertex: str,
        edge_collection: str,
        direction: str = "outbound",
        min_depth: int = 1,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """Perform graph traversal via UDS3"""
        # UDS3 graph traversal
        results = await self._uds3_manager.query_across_databases(
            query_text="",
            vector_params=None,
            graph_params={
                "start_vertex": start_vertex,
                "edge_collection": edge_collection,
                "direction": direction,
                "min_depth": min_depth,
                "max_depth": max_depth
            },
            relational_params=None
        )
        
        return results.get("graph_results", [])
    
    async def execute_query(
        self,
        query: str,
        bind_vars: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute UDS3 query (not native AQL)"""
        # UDS3 doesn't support AQL directly
        raise NotImplementedError(
            "UDS3 doesn't support native AQL queries. "
            "Use vector_search or graph_traverse instead."
        )
    
    def get_backend_type(self) -> DatabaseType:
        """Get backend type"""
        return DatabaseType.UDS3
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics"""
        return {
            **self._stats,
            "backend": "uds3_polyglot",
            "connected": self._connected
        }
    
    def supports_feature(self, feature: str) -> bool:
        """Check feature support"""
        supported = {
            "vector_search", "graph_traversal", "hybrid_search",
            "multi_database"
        }
        return feature in supported
    
    def _transform_uds3_results(
        self,
        results: Dict[str, Any]
    ) -> List[DocumentResult]:
        """Transform UDS3 results to standard format"""
        documents = []
        
        # UDS3 result format varies - adapt as needed
        vector_results = results.get("vector_results", [])
        
        for result in vector_results:
            documents.append(DocumentResult(
                doc_id=result.get("doc_id", ""),
                content=result.get("content", ""),
                score=result.get("score", 0.0),
                metadata=result.get("metadata", {}),
                source="uds3",
                context=result.get("context")
            ))
        
        return documents
    
    def _update_latency(self, duration: float):
        """Update average latency"""
        total = self._stats["total_queries"]
        current_avg = self._stats["avg_latency_ms"]
        new_latency = duration * 1000
        self._stats["avg_latency_ms"] = (
            (current_avg * (total - 1) + new_latency) / total
        )


# ============================================================================
# Adapter Factory (Factory Pattern)
# ============================================================================

class DatabaseAdapterFactory:
    """
    Factory for creating database adapters.
    
    Design Pattern: Factory Pattern + Strategy Pattern
    Principle: Open/Closed - Easy to add new adapters
    """
    
    _adapters: Dict[DatabaseType, type[IDatabaseAdapter]] = {
        DatabaseType.THEMIS: ThemisDBAdapter,
        DatabaseType.UDS3: UDS3Adapter,
    }
    
    @classmethod
    async def create(cls, config: DatabaseConfig) -> IDatabaseAdapter:
        """
        Create and initialize adapter.
        
        Args:
            config: Database configuration
            
        Returns:
            Initialized database adapter
            
        Raises:
            ValueError: If database type not supported
        """
        adapter_class = cls._adapters.get(config.db_type)
        if not adapter_class:
            raise ValueError(f"Unsupported database type: {config.db_type}")
        
        adapter = adapter_class(config)
        await adapter.connect()
        return adapter
    
    @classmethod
    def register_adapter(
        cls,
        db_type: DatabaseType,
        adapter_class: type[IDatabaseAdapter]
    ) -> None:
        """
        Register new adapter type.
        
        Principle: Open/Closed - Extend without modification
        """
        cls._adapters[db_type] = adapter_class
    
    @classmethod
    def get_available_types(cls) -> List[DatabaseType]:
        """Get list of available database types"""
        return list(cls._adapters.keys())


# ============================================================================
# Adapter Selection Strategy
# ============================================================================

class AdapterSelector:
    """
    Strategy for selecting appropriate adapter.
    
    Design Pattern: Strategy Pattern
    Principle: Encapsulate adapter selection logic
    """
    
    @staticmethod
    async def select_best_adapter(
        preferred_type: Optional[DatabaseType] = None,
        fallback: bool = True
    ) -> IDatabaseAdapter:
        """
        Select best available adapter.
        
        Strategy:
        1. Try preferred type if specified
        2. Try ThemisDB (primary)
        3. Fallback to UDS3 if enabled
        
        Args:
            preferred_type: Preferred database type
            fallback: Enable fallback to alternative
            
        Returns:
            Initialized adapter
            
        Raises:
            RuntimeError: If no adapter available
        """
        import logging
        import os
        
        logger = logging.getLogger(__name__)
        
        # 1. Try preferred type
        if preferred_type:
            try:
                config = cls._get_config_for_type(preferred_type)
                adapter = await DatabaseAdapterFactory.create(config)
                logger.info(f"✅ Using {preferred_type.value} adapter (preferred)")
                return adapter
            except Exception as e:
                logger.warning(f"⚠️ Preferred adapter {preferred_type.value} failed: {e}")
                if not fallback:
                    raise
        
        # 2. Try ThemisDB (primary)
        if os.getenv("THEMIS_ENABLED", "true").lower() == "true":
            try:
                config = cls._get_config_for_type(DatabaseType.THEMIS)
                adapter = await DatabaseAdapterFactory.create(config)
                logger.info("✅ Using ThemisDB adapter (primary)")
                return adapter
            except Exception as e:
                logger.warning(f"⚠️ ThemisDB adapter failed: {e}")
        
        # 3. Fallback to UDS3
        if fallback and os.getenv("USE_UDS3_FALLBACK", "true").lower() == "true":
            try:
                config = cls._get_config_for_type(DatabaseType.UDS3)
                adapter = await DatabaseAdapterFactory.create(config)
                logger.info("✅ Using UDS3 adapter (fallback)")
                return adapter
            except Exception as e:
                logger.error(f"❌ UDS3 adapter failed: {e}")
        
        raise RuntimeError("No database adapter available")
    
    @staticmethod
    def _get_config_for_type(db_type: DatabaseType) -> DatabaseConfig:
        """Get configuration for database type"""
        import os
        
        if db_type == DatabaseType.THEMIS:
            return DatabaseConfig(
                db_type=DatabaseType.THEMIS,
                host=os.getenv("THEMIS_HOST", "localhost"),
                port=int(os.getenv("THEMIS_PORT", "8765")),
                use_ssl=os.getenv("THEMIS_USE_SSL", "false").lower() == "true",
                api_token=os.getenv("THEMIS_API_TOKEN"),
                timeout=int(os.getenv("THEMIS_TIMEOUT", "30"))
            )
        elif db_type == DatabaseType.UDS3:
            return DatabaseConfig(
                db_type=DatabaseType.UDS3,
                custom_settings={
                    "backend_config": {
                        "relational": {"enabled": True},
                        "vector": {"enabled": True},
                        "graph": {"enabled": True},
                        "file": {"enabled": True}
                    }
                }
            )
        else:
            raise ValueError(f"Unknown database type: {db_type}")
