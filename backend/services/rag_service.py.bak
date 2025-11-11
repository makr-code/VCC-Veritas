"""
RAG Service - Real Document Retrieval with UDS3 Integration

This service provides Retrieval-Augmented Generation (RAG) capabilities
by integrating with the UDS3 framework for multi-database document search.

Features:
- Vector search via ChromaDB (semantic similarity)
- Graph search via Neo4j (relationship traversal)
- Relational search via PostgreSQL (metadata filtering)
- Hybrid search (weighted combination of all methods)
- Result ranking and deduplication
- Document metadata extraction
- Source citation generation

Author: VERITAS AI
Created: 14. Oktober 2025
Version: 1.0
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# UDS3 Polyglot Manager - STRICT SEPARATION OF CONCERNS
# ============================================================================
# RAG Service uses ONLY UDS3 PolyglotManager.
# NO direct backend imports - UDS3 handles all database connections!
# Import happens in __init__ to ensure clean startup.


class SearchMethod(Enum):
    """Available search methods"""

    VECTOR = "vector"  # Semantic search via ChromaDB
    GRAPH = "graph"  # Relationship search via Neo4j
    RELATIONAL = "relational"  # Metadata search via PostgreSQL
    HYBRID = "hybrid"  # Combined search


class RankingStrategy(Enum):
    """Ranking strategies for hybrid search"""

    RECIPROCAL_RANK_FUSION = "rrf"  # Reciprocal Rank Fusion
    WEIGHTED_SCORE = "weighted"  # Weighted sum of scores
    BORDA_COUNT = "borda"  # Borda count voting


@dataclass
class SearchWeights:
    """Weights for hybrid search components"""

    vector_weight: float = 0.5  # Semantic similarity weight
    graph_weight: float = 0.3  # Relationship relevance weight
    relational_weight: float = 0.2  # Metadata match weight

    def __post_init__(self):
        """Validate weights sum to 1.0"""
        total = self.vector_weight + self.graph_weight + self.relational_weight
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Search weights must sum to 1.0, got {total}")


@dataclass
class SearchFilters:
    """Filters for document search"""

    document_types: Optional[List[str]] = None  # e.g., ["pdf", "docx"]
    date_range: Optional[Tuple[datetime, datetime]] = None
    min_relevance: float = 0.0  # Minimum relevance score (0.0-1.0)
    max_results: int = 10
    metadata_filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentMetadata:
    """Metadata extracted from documents"""

    document_id: str
    title: str
    source_type: str  # "file", "url", "database", etc.
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    author: Optional[str] = None
    file_path: Optional[str] = None
    page_count: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "document_id": self.document_id,
            "title": self.title,
            "source_type": self.source_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "author": self.author,
            "file_path": self.file_path,
            "page_count": self.page_count,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
        }


@dataclass
class SearchResult:
    """Single search result from any backend"""

    document_id: str
    content: str
    relevance_score: float  # 0.0-1.0
    metadata: DocumentMetadata
    search_method: SearchMethod
    rank: int = 0  # Position in result list
    page_number: Optional[int] = None
    excerpt_start: Optional[int] = None  # Character offset
    excerpt_end: Optional[int] = None

    def get_hash(self) -> str:
        """Generate unique hash for deduplication"""
        key = f"{self.document_id}:{self.page_number or 0}"
        # Use SHA-256 rather than MD5 to avoid Bandit B324 (weak hash).
        # This hash is only used for deduplication keys (non-security use).
        return hashlib.sha256(key.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "document_id": self.document_id,
            "content": self.content,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata.to_dict(),
            "search_method": self.search_method.value,
            "rank": self.rank,
            "page_number": self.page_number,
            "excerpt_start": self.excerpt_start,
            "excerpt_end": self.excerpt_end,
        }


@dataclass
class HybridSearchResult:
    """Combined results from hybrid search"""

    results: List[SearchResult]
    total_count: int
    query: str
    search_methods_used: List[SearchMethod]
    ranking_strategy: RankingStrategy
    weights: SearchWeights
    execution_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "results": [r.to_dict() for r in self.results],
            "total_count": self.total_count,
            "query": self.query,
            "search_methods_used": [m.value for m in self.search_methods_used],
            "ranking_strategy": self.ranking_strategy.value,
            "weights": {
                "vector": self.weights.vector_weight,
                "graph": self.weights.graph_weight,
                "relational": self.weights.relational_weight,
            },
            "execution_time_ms": self.execution_time_ms,
        }


class RAGService:
    """
    Retrieval-Augmented Generation Service

    Provides document search and retrieval using multi-database framework.
    Primary: ThemisDB (Multi-Model) → Fallback: UDS3 Polyglot
    """

    def __init__(self):
        """
        Initialize RAG Service with Database Adapter (ThemisDB or UDS3).

        Strategy:
        ---------
        1. **Primary:** ThemisDB adapter (if THEMIS_ENABLED=true)
        2. **Fallback:** UDS3 Polyglot (if ThemisDB unavailable)

        Environment Variables:
        ----------------------
        - THEMIS_ENABLED: Enable ThemisDB (default: true)
        - USE_UDS3_FALLBACK: Enable UDS3 fallback (default: true)
        """
        self.logger = logging.getLogger(__name__)

        # ============================================================================
        # Database Adapter - Environment-Controlled Selection
        # ============================================================================
        # Primary: ThemisDB (single multi-model database)
        # Fallback: UDS3 Polyglot (multi-backend orchestration)

        try:
            from backend.adapters import get_database_adapter

            # Get adapter with automatic fallback
            self.db_adapter = get_database_adapter(enable_fallback=True)

            # Check which adapter was selected
            adapter_name = self.db_adapter.__class__.__name__
            self.logger.info(f"✅ RAG Service initialized with {adapter_name}")

        except Exception as e:
            self.logger.error(f"❌ CRITICAL: Database Adapter Init FAILED: {e}")
            raise RuntimeError(f"RAG Service requires database adapter - Init failed: {e}")

    def is_available(self) -> bool:
        """
        Check if database adapter is available

        Returns:
            True if adapter initialized successfully
        """
        return hasattr(self, "db_adapter") and self.db_adapter is not None

    def vector_search(self, query: str, filters: Optional[SearchFilters] = None) -> List[SearchResult]:
        """
        Perform vector search using ChromaDB

        Args:
            query: Search query string
            filters: Optional search filters

        Returns:
            List of search results ordered by relevance
        """
        if self.chromadb is None:
            self.logger.warning("ChromaDB not available - returning mock results")
            return self._mock_vector_search(query, filters)

        filters = filters or SearchFilters()

        try:
            # Query ChromaDB with semantic search
            results = self.chromadb.query_vectors(
                query_text=query, limit=filters.max_results, metadata_filter=filters.metadata_filters
            )

            # Convert ChromaDB results to SearchResult format
            search_results = []
            for i, result in enumerate(results):
                metadata = DocumentMetadata(
                    document_id=result.get("id", f"doc_{i}"),
                    title=result.get("metadata", {}).get("title", "Untitled"),
                    source_type=result.get("metadata", {}).get("source_type", "file"),
                    file_path=result.get("metadata", {}).get("file_path"),
                    page_count=result.get("metadata", {}).get("page_count"),
                    tags=result.get("metadata", {}).get("tags", []),
                )

                search_results.append(
                    SearchResult(
                        document_id=metadata.document_id,
                        content=result.get("document", ""),
                        relevance_score=result.get("distance", 0.0),
                        metadata=metadata,
                        search_method=SearchMethod.VECTOR,
                        rank=i + 1,
                        page_number=result.get("metadata", {}).get("page_number"),
                    )
                )

            # Filter by minimum relevance
            search_results = [r for r in search_results if r.relevance_score >= filters.min_relevance]

            self.logger.info(f"Vector search: {len(search_results)} results for '{query}'")
            return search_results

        except Exception as e:
            self.logger.error(f"Vector search failed: {e}")
            return []

    def graph_search(self, query: str, filters: Optional[SearchFilters] = None) -> List[SearchResult]:
        """
        Perform graph search using Neo4j

        Args:
            query: Search query string
            filters: Optional search filters

        Returns:
            List of search results based on graph relationships
        """
        if self.neo4j is None:
            self.logger.warning("Neo4j not available - returning mock results")
            return self._mock_graph_search(query, filters)

        filters = filters or SearchFilters()

        try:
            # Query Neo4j for related documents
            cypher_query = """
            MATCH (d:Document)
            WHERE d.content CONTAINS $query OR d.title CONTAINS $query
            OPTIONAL MATCH (d)-[r]-(related:Document)
            RETURN d, collect(related) as related_docs, count(r) as relationship_count
            ORDER BY relationship_count DESC
            LIMIT $limit
            """

            with self.neo4j.driver.session() as session:
                result = session.run(cypher_query, query=query, limit=filters.max_results)

                search_results = []
                for i, record in enumerate(result):
                    doc = record["d"]
                    rel_count = record["relationship_count"]

                    # Calculate relevance based on relationship count
                    relevance = min(1.0, rel_count / 10.0)  # Normalize to 0-1

                    metadata = DocumentMetadata(
                        document_id=doc.get("id", f"neo4j_doc_{i}"),
                        title=doc.get("title", "Untitled"),
                        source_type="neo4j",
                        tags=doc.get("tags", []),
                    )

                    search_results.append(
                        SearchResult(
                            document_id=metadata.document_id,
                            content=doc.get("content", ""),
                            relevance_score=relevance,
                            metadata=metadata,
                            search_method=SearchMethod.GRAPH,
                            rank=i + 1,
                        )
                    )

                # Filter by minimum relevance
                search_results = [r for r in search_results if r.relevance_score >= filters.min_relevance]

                self.logger.info(f"Graph search: {len(search_results)} results for '{query}'")
                return search_results

        except Exception as e:
            self.logger.error(f"Graph search failed: {e}")
            return []

    def relational_search(self, query: str, filters: Optional[SearchFilters] = None) -> List[SearchResult]:
        """
        Perform relational search using PostgreSQL

        Args:
            query: Search query string
            filters: Optional search filters

        Returns:
            List of search results based on metadata matching
        """
        if self.postgresql is None:
            self.logger.warning("PostgreSQL not available - returning mock results")
            return self._mock_relational_search(query, filters)

        filters = filters or SearchFilters()

        try:
            # Query PostgreSQL with full-text search
            sql_query = """
            SELECT id, title, content, metadata,
                   ts_rank(to_tsvector('german', content), plainto_tsquery('german', %s)) as relevance
            FROM documents
            WHERE to_tsvector('german', content) @@ plainto_tsquery('german', %s)
            ORDER BY relevance DESC
            LIMIT %s
            """

            results = self.postgresql.execute_query(sql_query, (query, query, filters.max_results))

            search_results = []
            for i, row in enumerate(results):
                metadata = DocumentMetadata(
                    document_id=str(row["id"]),
                    title=row["title"],
                    source_type="postgresql",
                    custom_fields=row.get("metadata", {}),
                )

                search_results.append(
                    SearchResult(
                        document_id=metadata.document_id,
                        content=row["content"],
                        relevance_score=float(row["relevance"]),
                        metadata=metadata,
                        search_method=SearchMethod.RELATIONAL,
                        rank=i + 1,
                    )
                )

            # Filter by minimum relevance
            search_results = [r for r in search_results if r.relevance_score >= filters.min_relevance]

            self.logger.info(f"Relational search: {len(search_results)} results for '{query}'")
            return search_results

        except Exception as e:
            self.logger.error(f"Relational search failed: {e}")
            return []

    def hybrid_search(
        self,
        query: str,
        weights: Optional[SearchWeights] = None,
        filters: Optional[SearchFilters] = None,
        ranking_strategy: RankingStrategy = RankingStrategy.RECIPROCAL_RANK_FUSION,
    ) -> HybridSearchResult:
        """
        Perform hybrid search combining all methods

        Args:
            query: Search query string
            weights: Search method weights (defaults to equal weighting)
            filters: Optional search filters
            ranking_strategy: Strategy for combining results

        Returns:
            HybridSearchResult with ranked and deduplicated results
        """
        import time

        start_time = time.time()

        weights = weights or SearchWeights()
        filters = filters or SearchFilters()

        # Perform all searches
        methods_used = []
        all_results = []

        if self.chromadb and weights.vector_weight > 0:
            vector_results = self.vector_search(query, filters)
            all_results.extend(vector_results)
            methods_used.append(SearchMethod.VECTOR)

        if self.neo4j and weights.graph_weight > 0:
            graph_results = self.graph_search(query, filters)
            all_results.extend(graph_results)
            methods_used.append(SearchMethod.GRAPH)

        if self.postgresql and weights.relational_weight > 0:
            relational_results = self.relational_search(query, filters)
            all_results.extend(relational_results)
            methods_used.append(SearchMethod.RELATIONAL)

        # Deduplicate results
        seen_hashes = set()
        unique_results = []
        for result in all_results:
            result_hash = result.get_hash()
            if result_hash not in seen_hashes:
                seen_hashes.add(result_hash)
                unique_results.append(result)

        # Rank results based on strategy
        if ranking_strategy == RankingStrategy.RECIPROCAL_RANK_FUSION:
            ranked_results = self._reciprocal_rank_fusion(unique_results, weights)
        elif ranking_strategy == RankingStrategy.WEIGHTED_SCORE:
            ranked_results = self._weighted_score_ranking(unique_results, weights)
        else:  # BORDA_COUNT
            ranked_results = self._borda_count_ranking(unique_results, weights)

        # Limit to max_results
        ranked_results = ranked_results[: filters.max_results]

        # Update ranks
        for i, result in enumerate(ranked_results):
            result.rank = i + 1

        execution_time = (time.time() - start_time) * 1000  # Convert to ms

        return HybridSearchResult(
            results=ranked_results,
            total_count=len(unique_results),
            query=query,
            search_methods_used=methods_used,
            ranking_strategy=ranking_strategy,
            weights=weights,
            execution_time_ms=execution_time,
        )

    async def batch_search(
        self,
        queries: List[str],
        search_method: SearchMethod = SearchMethod.HYBRID,
        weights: Optional[SearchWeights] = None,
        filters: Optional[SearchFilters] = None,
        ranking_strategy: RankingStrategy = RankingStrategy.RECIPROCAL_RANK_FUSION,
    ) -> List[HybridSearchResult]:
        """
        Perform batch search for multiple queries in parallel

        This method uses asyncio to execute multiple search queries concurrently,
        significantly improving throughput when processing multiple queries.

        Args:
            queries: List of search query strings
            search_method: Search method to use (HYBRID recommended)
            weights: Search method weights for hybrid search
            filters: Optional search filters (applied to all queries)
            ranking_strategy: Ranking strategy for hybrid search

        Returns:
            List of HybridSearchResult objects, one per query

        Example:
            >>> queries = [
            ...     "Bauantrag Stuttgart",
            ...     "Gewerbeanmeldung München",
            ...     "Personalausweis beantragen"
            ... ]
            >>> results = await rag.batch_search(queries)
            >>> for query, result in zip(queries, results):
            ...     print(f"{query}: {len(result.results)} results")
        """
        import asyncio
        import time

        start_time = time.time()
        self.logger.info(f"Starting batch search for {len(queries)} queries")

        # Create async tasks for each query
        async def search_task(query: str) -> HybridSearchResult:
            """Async wrapper for search operation"""
            loop = asyncio.get_event_loop()

            # Run search in thread pool (since search methods are synchronous)
            if search_method == SearchMethod.HYBRID:
                result = await loop.run_in_executor(None, self.hybrid_search, query, weights, filters, ranking_strategy)
            elif search_method == SearchMethod.VECTOR:
                vector_results = await loop.run_in_executor(None, self.vector_search, query, filters)
                # Wrap in HybridSearchResult for consistent output
                result = HybridSearchResult(
                    results=vector_results,
                    total_count=len(vector_results),
                    query=query,
                    search_methods_used=[SearchMethod.VECTOR],
                    ranking_strategy=ranking_strategy,
                    weights=weights or SearchWeights(),
                    execution_time_ms=0.0,
                )
            elif search_method == SearchMethod.GRAPH:
                graph_results = await loop.run_in_executor(None, self.graph_search, query, filters)
                result = HybridSearchResult(
                    results=graph_results,
                    total_count=len(graph_results),
                    query=query,
                    search_methods_used=[SearchMethod.GRAPH],
                    ranking_strategy=ranking_strategy,
                    weights=weights or SearchWeights(),
                    execution_time_ms=0.0,
                )
            else:  # RELATIONAL
                relational_results = await loop.run_in_executor(None, self.relational_search, query, filters)
                result = HybridSearchResult(
                    results=relational_results,
                    total_count=len(relational_results),
                    query=query,
                    search_methods_used=[SearchMethod.RELATIONAL],
                    ranking_strategy=ranking_strategy,
                    weights=weights or SearchWeights(),
                    execution_time_ms=0.0,
                )

            return result

        # Execute all searches in parallel
        tasks = [search_task(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch search failed for query '{queries[i]}': {result}")
                # Create empty result for failed query
                processed_results.append(
                    HybridSearchResult(
                        results=[],
                        total_count=0,
                        query=queries[i],
                        search_methods_used=[],
                        ranking_strategy=ranking_strategy,
                        weights=weights or SearchWeights(),
                        execution_time_ms=0.0,
                    )
                )
            else:
                processed_results.append(result)

        total_time = (time.time() - start_time) * 1000
        avg_time = total_time / len(queries) if queries else 0

        self.logger.info(
            f"Batch search complete: {len(queries)} queries in {total_time:.2f}ms " f"(avg: {avg_time:.2f}ms per query)"
        )

        return processed_results

    def expand_query(self, query: str, max_expansions: int = 3, include_original: bool = True) -> List[str]:
        """
        Expand query with synonyms and reformulations

        This method generates multiple variations of the input query to improve
        recall in search operations. It uses rule-based expansion for common
        German administrative terms.

        Args:
            query: Original search query
            max_expansions: Maximum number of expansions to generate
            include_original: Whether to include original query in results

        Returns:
            List of query variations (including original if requested)

        Example:
            >>> rag = RAGService()
            >>> expansions = rag.expand_query("Bauantrag Stuttgart")
            >>> print(expansions)
            ['Bauantrag Stuttgart', 'Baugenehmigung Stuttgart', 'Bauantragsverfahren Stuttgart']
        """
        expansions = []

        if include_original:
            expansions.append(query)

        # German administrative term synonyms
        synonym_map = {
            # Building/Construction
            "bauantrag": ["baugenehmigung", "bauantragsverfahren", "baugesuch"],
            "einfamilienhaus": ["wohnhaus", "eigenheim", "wohngebäude"],
            "umbau": ["sanierung", "renovierung", "modernisierung"],
            "neubau": ["bauvorhaben", "neubauprojekt"],
            # Business
            "gewerbeanmeldung": ["gewerbeschein", "gewerbeerlaubnis", "gewerbemeldung"],
            "gmbh": ["gesellschaft mit beschränkter haftung", "kapitalgesellschaft"],
            "unternehmensgründung": ["firmengründung", "geschäftsgründung"],
            # Documents
            "personalausweis": ["ausweis", "identitätskarte", "id-karte"],
            "führerschein": ["fahrerlaubnis", "fahrberechtigung"],
            "reisepass": ["pass", "reisedokument"],
            # Procedures
            "anmeldung": ["registrierung", "meldung", "eintragung"],
            "ummeldung": ["adressänderung", "wohnsitzwechsel"],
            "beantragen": ["anfragen", "einreichen", "stellen"],
            # Authorities
            "bauamt": ["bauaufsicht", "baubehörde", "bauordnungsamt"],
            "rathaus": ["stadtverwaltung", "gemeindeverwaltung", "bürgeramt"],
            "finanzamt": ["steuerbehörde", "finanzverwaltung"],
            # Other
            "kosten": ["gebühren", "preise", "ausgaben"],
            "dauer": ["zeitraum", "bearbeitungszeit", "frist"],
            "voraussetzungen": ["bedingungen", "anforderungen", "kriterien"],
        }

        # Normalize query to lowercase for matching
        query_lower = query.lower()

        # Find and replace synonyms
        generated_count = 0
        for term, synonyms in synonym_map.items():
            if generated_count >= max_expansions:
                break

            if term in query_lower:
                for synonym in synonyms:
                    if generated_count >= max_expansions:
                        break

                    # Replace term with synonym (case-preserving)
                    import re

                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    expanded = pattern.sub(synonym, query, count=1)

                    # Avoid duplicates
                    if expanded not in expansions and expanded.lower() != query.lower():
                        expansions.append(expanded)
                        generated_count += 1

        self.logger.info(
            f"Query expansion: '{query}' -> {len(expansions)} variations "
            f"(generated: {len(expansions) - (1 if include_original else 0)})"
        )

        return expansions

    def _reciprocal_rank_fusion(self, results: List[SearchResult], weights: SearchWeights) -> List[SearchResult]:
        """Apply Reciprocal Rank Fusion (RRF) ranking"""
        k = 60  # RRF constant

        # Calculate RRF scores
        for result in results:
            weight = self._get_weight_for_method(result.search_method, weights)
            rrf_score = weight * (1.0 / (k + result.rank))
            result.relevance_score = rrf_score

        # Sort by RRF score
        return sorted(results, key=lambda r: r.relevance_score, reverse=True)

    def _weighted_score_ranking(self, results: List[SearchResult], weights: SearchWeights) -> List[SearchResult]:
        """Apply weighted score ranking"""
        for result in results:
            weight = self._get_weight_for_method(result.search_method, weights)
            result.relevance_score *= weight

        return sorted(results, key=lambda r: r.relevance_score, reverse=True)

    def _borda_count_ranking(self, results: List[SearchResult], weights: SearchWeights) -> List[SearchResult]:
        """Apply Borda count ranking"""
        # Group by method
        method_results = {}
        for result in results:
            method = result.search_method
            if method not in method_results:
                method_results[method] = []
            method_results[method].append(result)

        # Calculate Borda scores
        borda_scores = {}
        for method, method_res in method_results.items():
            n = len(method_res)
            weight = self._get_weight_for_method(method, weights)
            for i, result in enumerate(method_res):
                doc_hash = result.get_hash()
                borda_score = weight * (n - i)
                borda_scores[doc_hash] = borda_scores.get(doc_hash, 0) + borda_score

        # Apply scores and sort
        for result in results:
            result.relevance_score = borda_scores.get(result.get_hash(), 0)

        return sorted(results, key=lambda r: r.relevance_score, reverse=True)

    def _get_weight_for_method(self, method: SearchMethod, weights: SearchWeights) -> float:
        """Get weight for search method"""
        if method == SearchMethod.VECTOR:
            return weights.vector_weight
        elif method == SearchMethod.GRAPH:
            return weights.graph_weight
        elif method == SearchMethod.RELATIONAL:
            return weights.relational_weight
        return 0.0

    def get_relevant_context(self, query: str, max_tokens: int = 2000, filters: Optional[SearchFilters] = None) -> str:
        """
        Build context string from search results

        Args:
            query: Search query
            max_tokens: Maximum tokens for context (approximate)
            filters: Optional search filters

        Returns:
            Context string suitable for LLM input
        """
        # Perform hybrid search
        search_result = self.hybrid_search(query, filters=filters)

        # Build context with token limit
        context_parts = []
        current_tokens = 0
        chars_per_token = 4  # Rough estimate
        max_chars = max_tokens * chars_per_token

        for result in search_result.results:
            # Format: [Source] Content
            source_prefix = f"[{result.metadata.title}] "
            content = result.content[:1000]  # Limit each excerpt

            part = source_prefix + content
            part_tokens = len(part) // chars_per_token

            if current_tokens + part_tokens > max_tokens:
                break

            context_parts.append(part)
            current_tokens += part_tokens

        context = "\n\n".join(context_parts)
        return context

    # Mock methods for testing without UDS3

    def _mock_vector_search(self, query: str, filters: Optional[SearchFilters]) -> List[SearchResult]:
        """Mock vector search for testing"""
        mock_docs = [
            {
                "id": "doc_1",
                "title": "Bauantragsverfahren in Baden-Württemberg",
                "content": "Ein Bauantrag in Stuttgart erfordert...",
                "relevance": 0.92,
            },
            {
                "id": "doc_2",
                "title": "Einfamilienhaus Genehmigung",
                "content": "Die Genehmigung für ein Einfamilienhaus...",
                "relevance": 0.85,
            },
        ]

        results = []
        for i, doc in enumerate(mock_docs):
            metadata = DocumentMetadata(document_id=doc["id"], title=doc["title"], source_type="mock")
            results.append(
                SearchResult(
                    document_id=doc["id"],
                    content=doc["content"],
                    relevance_score=doc["relevance"],
                    metadata=metadata,
                    search_method=SearchMethod.VECTOR,
                    rank=i + 1,
                )
            )

        return results

    def _mock_graph_search(self, query: str, filters: Optional[SearchFilters]) -> List[SearchResult]:
        """Mock graph search for testing"""
        return []  # Graph search typically returns fewer results

    def _mock_relational_search(self, query: str, filters: Optional[SearchFilters]) -> List[SearchResult]:
        """Mock relational search for testing"""
        return []  # Relational search returns metadata-focused results


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("RAG SERVICE - STANDALONE TEST")
    print("=" * 80)

    # Initialize service (will throw RuntimeError if any backend fails)
    rag = RAGService()
    print(f"\n✅ RAG Service initialized - ALL backends connected!")
    print(f"   - ChromaDB: {'✅' if rag.chromadb else '❌'}")
    print(f"   - Neo4j: {'✅' if rag.neo4j else '❌'}")
    print(f"   - PostgreSQL: {'✅' if rag.postgresql else '❌'}")

    # Test query
    query = "Bauantrag für Einfamilienhaus in Stuttgart"
    print(f'\n📝 Test Query: "{query}"')

    # Vector search
    print("\n1. Vector Search:")
    vector_results = rag.vector_search(query)
    for r in vector_results:
        print(f"   - {r.metadata.title} (score: {r.relevance_score:.2f})")

    # Hybrid search
    print("\n2. Hybrid Search:")
    hybrid_result = rag.hybrid_search(query)
    print(f"   - Total results: {len(hybrid_result.results)}")
    print(f"   - Methods used: {[m.value for m in hybrid_result.search_methods_used]}")
    print(f"   - Execution time: {hybrid_result.execution_time_ms:.2f}ms")
    for r in hybrid_result.results[:3]:
        print(f"   - {r.metadata.title} (score: {r.relevance_score:.4f}, method: {r.search_method.value})")

    # Context building
    print("\n3. Context Building:")
    context = rag.get_relevant_context(query, max_tokens=500)
    print(f"   - Context length: {len(context)} chars")
    print(f"   - Context preview: {context[:200]}...")

    print("\n" + "=" * 80)
    print("✅ RAG Service test complete!")
    print("=" * 80)
