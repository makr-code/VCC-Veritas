"""
ThemisDB Agent Framework - Base Classes & Interfaces
=====================================================

OOP-basiertes Design nach Best-Practices:
- SOLID Principles
- Abstract Base Classes für Erweiterbarkeit
- Protocol-based Interfaces
- Dependency Injection
- Type Safety mit Generics

Author: VERITAS Backend Team
Date: 2025-12-03
Version: 2.0 (OOP Refactoring)
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar

# Type Variables for Generics
T = TypeVar("T")
QueryResultT = TypeVar("QueryResultT")


# ============================================================================
# Enums
# ============================================================================

class QueryType(Enum):
    """Supported query types"""
    VECTOR_SEARCH = "vector_search"
    GRAPH_TRAVERSAL = "graph_traversal"
    DOCUMENT_FILTER = "document_filter"
    HYBRID = "hybrid"
    AGGREGATION = "aggregation"
    CONTEXT_ENRICHED = "context_enriched"


class QueryComplexity(Enum):
    """Query complexity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CacheStrategy(Enum):
    """Cache strategies"""
    NONE = "none"
    TIME_BASED = "time_based"
    LRU = "lru"
    QUERY_BASED = "query_based"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass(frozen=True)
class QueryContext:
    """
    Immutable query context containing all information needed for query planning.
    
    Design Pattern: Value Object
    Principle: Immutability for thread safety
    """
    user_query: str
    query_intent: str = "information_retrieval"
    complexity: QueryComplexity = QueryComplexity.MEDIUM
    domain: str = "general"
    capabilities: frozenset = field(default_factory=frozenset)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def with_metadata(self, **kwargs) -> QueryContext:
        """Returns new instance with updated metadata (Builder pattern)"""
        return QueryContext(
            user_query=self.user_query,
            query_intent=self.query_intent,
            complexity=self.complexity,
            domain=self.domain,
            capabilities=self.capabilities,
            metadata={**self.metadata, **kwargs}
        )


@dataclass
class QueryPlan:
    """
    Query execution plan with all necessary information.
    
    Design Pattern: Command Pattern
    Principle: Encapsulation of execution strategy
    """
    query_type: QueryType
    aql_query: str
    bind_vars: Dict[str, Any]
    estimated_cost: float = 0.0
    cache_strategy: CacheStrategy = CacheStrategy.TIME_BASED
    timeout_seconds: int = 30
    retry_count: int = 0
    
    @property
    def cache_key(self) -> str:
        """Generate cache key from query plan"""
        import hashlib
        query_str = f"{self.aql_query}:{sorted(self.bind_vars.items())}"
        return hashlib.md5(query_str.encode()).hexdigest()


@dataclass
class QueryResult(Generic[T]):
    """
    Generic query result container.
    
    Design Pattern: Generic Container
    Principle: Type Safety with Generics
    """
    data: List[T]
    metadata: Dict[str, Any] = field(default_factory=dict)
    query_time_ms: float = 0.0
    source: str = "themisdb"
    
    @property
    def count(self) -> int:
        """Number of results"""
        return len(self.data)
    
    def is_empty(self) -> bool:
        """Check if result is empty"""
        return len(self.data) == 0


@dataclass
class RAGDocument:
    """
    RAG-optimized document representation.
    
    Design Pattern: Data Transfer Object (DTO)
    Principle: Clear data structure for RAG pipeline
    """
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    source: str = "themisdb"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
            "context": self.context,
            "source": self.source
        }


# ============================================================================
# Protocols (Interface Segregation Principle)
# ============================================================================

class EmbeddingProvider(Protocol):
    """Protocol for embedding generation"""
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        ...


class CacheProvider(Protocol):
    """Protocol for cache operations"""
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        ...
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value with optional TTL"""
        ...
    
    def delete(self, key: str) -> None:
        """Delete cached value"""
        ...
    
    def clear(self) -> None:
        """Clear all cached values"""
        ...


class QueryExecutor(Protocol):
    """Protocol for query execution"""
    
    async def execute_aql(
        self,
        query: str,
        bind_vars: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute AQL query"""
        ...


# ============================================================================
# Abstract Base Classes
# ============================================================================

class QueryTemplate(abc.ABC):
    """
    Abstract base class for query templates.
    
    Design Pattern: Template Method Pattern
    Principle: Define algorithm structure, let subclasses implement steps
    """
    
    @abc.abstractmethod
    def build_query(self, context: QueryContext) -> str:
        """Build AQL query from context"""
        pass
    
    @abc.abstractmethod
    def extract_bind_vars(self, context: QueryContext) -> Dict[str, Any]:
        """Extract bind variables from context"""
        pass
    
    def optimize_query(self, query: str, context: QueryContext) -> str:
        """
        Optimize query (can be overridden by subclasses).
        
        Template Method: Provides default optimization, subclasses can override
        """
        # Add cache hint for low complexity
        if context.complexity == QueryComplexity.LOW:
            query = f"/* +cache */\n{query}"
        
        # Add profiling for high complexity
        if context.complexity == QueryComplexity.HIGH:
            query = f"/* +profile */\n{query}"
        
        return query.strip()
    
    def estimate_cost(self, query: str, bind_vars: Dict[str, Any]) -> float:
        """
        Estimate query cost (can be overridden).
        
        Template Method: Provides default estimation
        """
        cost = 10.0  # Base cost
        
        # Vector search cost
        if "COSINE_SIMILARITY" in query:
            cost += 20.0
        
        # Graph traversal cost
        if "OUTBOUND" in query or "INBOUND" in query:
            depth = bind_vars.get("graph_depth", 1)
            cost += 50.0 * depth
        
        # Result limit factor
        limit = bind_vars.get("limit", 10)
        cost += limit * 0.5
        
        return cost


class QueryPlanner(abc.ABC):
    """
    Abstract base class for query planning.
    
    Design Pattern: Strategy Pattern
    Principle: Different planning strategies for different query types
    """
    
    @abc.abstractmethod
    def plan(self, context: QueryContext) -> QueryPlan:
        """Create execution plan from context"""
        pass
    
    @abc.abstractmethod
    def supports_query_type(self, query_type: QueryType) -> bool:
        """Check if planner supports given query type"""
        pass


class ResultTransformer(abc.ABC, Generic[T]):
    """
    Abstract base class for result transformation.
    
    Design Pattern: Chain of Responsibility
    Principle: Separation of transformation concerns
    """
    
    @abc.abstractmethod
    def transform(self, raw_results: List[Dict[str, Any]]) -> List[T]:
        """Transform raw results to typed objects"""
        pass
    
    def can_transform(self, raw_results: List[Dict[str, Any]]) -> bool:
        """Check if transformer can handle these results"""
        return True  # Default: can handle any results


class QueryStrategy(abc.ABC):
    """
    Abstract base class for query execution strategies.
    
    Design Pattern: Strategy Pattern
    Principle: Encapsulate query execution algorithms
    """
    
    def __init__(
        self,
        executor: QueryExecutor,
        embedding_provider: EmbeddingProvider,
        cache_provider: Optional[CacheProvider] = None
    ):
        """
        Initialize strategy with dependencies.
        
        Principle: Dependency Injection
        """
        self._executor = executor
        self._embedding_provider = embedding_provider
        self._cache_provider = cache_provider
    
    @abc.abstractmethod
    async def execute(
        self,
        plan: QueryPlan,
        context: QueryContext
    ) -> QueryResult[RAGDocument]:
        """Execute query according to plan"""
        pass
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Helper to get embedding"""
        return await self._embedding_provider.embed_text(text)
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Helper to get cached value"""
        if self._cache_provider:
            return self._cache_provider.get(key)
        return None
    
    def _set_cached(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Helper to set cached value"""
        if self._cache_provider:
            self._cache_provider.set(key, value, ttl)


# ============================================================================
# Exceptions
# ============================================================================

class ThemisDBAgentError(Exception):
    """Base exception for ThemisDB agent errors"""
    pass


class QueryPlanningError(ThemisDBAgentError):
    """Error during query planning"""
    pass


class QueryExecutionError(ThemisDBAgentError):
    """Error during query execution"""
    pass


class TransformationError(ThemisDBAgentError):
    """Error during result transformation"""
    pass


class ValidationError(ThemisDBAgentError):
    """Error during validation"""
    pass
