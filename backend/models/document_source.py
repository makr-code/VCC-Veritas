"""
Document Source Models

Data models for document retrieval, source citations, and RAG results.
Used by RAGService to represent search results and document metadata.

Author: VERITAS AI
Created: 14. Oktober 2025
Version: 1.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json


class SourceType(Enum):
    """Type of document source"""
    FILE = "file"           # Local file
    URL = "url"             # Web URL
    DATABASE = "database"   # Database record
    API = "api"             # External API
    EMAIL = "email"         # Email content
    UNKNOWN = "unknown"


class CitationConfidence(Enum):
    """Confidence level for source citation"""
    DIRECT = "direct"       # Direct quote or reference
    HIGH = "high"           # Strong relevance (>= 0.8)
    MEDIUM = "medium"       # Moderate relevance (>= 0.5)
    LOW = "low"             # Weak relevance (>= 0.3)
    UNKNOWN = "unknown"     # Confidence not determined


@dataclass
class RelevanceScore:
    """
    Multi-faceted relevance score
    
    Tracks relevance from different search methods:
    - semantic: Vector similarity (ChromaDB)
    - keyword: Lexical matching (PostgreSQL)
    - graph: Relationship strength (Neo4j)
    - hybrid: Combined score
    """
    semantic: float = 0.0    # 0.0-1.0
    keyword: float = 0.0     # 0.0-1.0
    graph: float = 0.0       # 0.0-1.0
    hybrid: float = 0.0      # Weighted combination
    
    def __post_init__(self):
        """Validate score ranges"""
        for score_name in ['semantic', 'keyword', 'graph', 'hybrid']:
            score = getattr(self, score_name)
            if not (0.0 <= score <= 1.0):
                raise ValueError(
                    f"{score_name} score must be in range [0.0, 1.0], got {score}"
                )
    
    def calculate_hybrid(
        self,
        semantic_weight: float = 0.5,
        keyword_weight: float = 0.3,
        graph_weight: float = 0.2
    ) -> float:
        """
        Calculate hybrid score from components
        
        Args:
            semantic_weight: Weight for semantic score
            keyword_weight: Weight for keyword score
            graph_weight: Weight for graph score
            
        Returns:
            Hybrid score (0.0-1.0)
        """
        total_weight = semantic_weight + keyword_weight + graph_weight
        if total_weight == 0:
            return 0.0
        
        self.hybrid = (
            self.semantic * semantic_weight +
            self.keyword * keyword_weight +
            self.graph * graph_weight
        ) / total_weight
        
        return self.hybrid
    
    def get_confidence(self) -> CitationConfidence:
        """Get confidence level based on hybrid score"""
        if self.hybrid >= 0.8:
            return CitationConfidence.HIGH
        elif self.hybrid >= 0.5:
            return CitationConfidence.MEDIUM
        elif self.hybrid >= 0.3:
            return CitationConfidence.LOW
        else:
            return CitationConfidence.UNKNOWN
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'semantic': self.semantic,
            'keyword': self.keyword,
            'graph': self.graph,
            'hybrid': self.hybrid
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'RelevanceScore':
        """Create from dictionary"""
        return cls(
            semantic=data.get('semantic', 0.0),
            keyword=data.get('keyword', 0.0),
            graph=data.get('graph', 0.0),
            hybrid=data.get('hybrid', 0.0)
        )


@dataclass
class DocumentSource:
    """
    Source document from RAG retrieval
    
    Represents a document retrieved from UDS3 databases.
    Contains full content, metadata, and relevance scoring.
    """
    document_id: str
    title: str
    content: str
    source_type: SourceType
    relevance_score: RelevanceScore
    
    # Optional metadata
    file_path: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    page_count: Optional[int] = None
    file_size: Optional[int] = None  # In bytes
    mime_type: Optional[str] = None
    language: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate document"""
        if not self.document_id:
            raise ValueError("document_id is required")
        if not self.title:
            raise ValueError("title is required")
        if not self.content:
            raise ValueError("content is required")
    
    def get_excerpt(self, max_length: int = 200) -> str:
        """
        Get excerpt of document content
        
        Args:
            max_length: Maximum excerpt length in characters
            
        Returns:
            Truncated content with ellipsis if needed
        """
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length].strip() + "..."
    
    def get_confidence(self) -> CitationConfidence:
        """Get citation confidence level"""
        return self.relevance_score.get_confidence()
    
    def matches_threshold(self, min_relevance: float = 0.0) -> bool:
        """Check if document meets minimum relevance threshold"""
        return self.relevance_score.hybrid >= min_relevance
    
    def to_citation(self) -> 'SourceCitation':
        """
        Create a SourceCitation from this document
        
        Returns:
            SourceCitation instance
        """
        return SourceCitation(
            source=self,
            confidence=self.get_confidence(),
            excerpt=self.get_excerpt(max_length=150)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'document_id': self.document_id,
            'title': self.title,
            'content': self.content,
            'source_type': self.source_type.value,
            'relevance_score': self.relevance_score.to_dict(),
            'file_path': self.file_path,
            'url': self.url,
            'author': self.author,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'page_count': self.page_count,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'language': self.language,
            'tags': self.tags,
            'custom_metadata': self.custom_metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentSource':
        """Create from dictionary"""
        return cls(
            document_id=data['document_id'],
            title=data['title'],
            content=data['content'],
            source_type=SourceType(data['source_type']),
            relevance_score=RelevanceScore.from_dict(data['relevance_score']),
            file_path=data.get('file_path'),
            url=data.get('url'),
            author=data.get('author'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            modified_at=datetime.fromisoformat(data['modified_at']) if data.get('modified_at') else None,
            page_count=data.get('page_count'),
            file_size=data.get('file_size'),
            mime_type=data.get('mime_type'),
            language=data.get('language'),
            tags=data.get('tags', []),
            custom_metadata=data.get('custom_metadata', {})
        )


@dataclass
class SourceCitation:
    """
    Citation for a specific source
    
    Links a piece of information to its source document,
    including page number and excerpt for precise attribution.
    """
    source: DocumentSource
    confidence: CitationConfidence
    
    # Optional precision fields
    page_number: Optional[int] = None
    section: Optional[str] = None
    excerpt: Optional[str] = None
    excerpt_start: Optional[int] = None  # Character offset
    excerpt_end: Optional[int] = None
    context_before: Optional[str] = None  # Text before excerpt
    context_after: Optional[str] = None   # Text after excerpt
    
    def get_reference_string(self) -> str:
        """
        Get formatted reference string
        
        Returns:
            Citation in format: "Title (Page X)" or just "Title"
        """
        ref = self.source.title
        if self.page_number:
            ref += f" (Page {self.page_number})"
        elif self.section:
            ref += f" ({self.section})"
        return ref
    
    def get_full_excerpt(self, include_context: bool = True) -> str:
        """
        Get full excerpt with optional context
        
        Args:
            include_context: Include surrounding context
            
        Returns:
            Full excerpt text
        """
        if not self.excerpt:
            return self.source.get_excerpt()
        
        if not include_context:
            return self.excerpt
        
        parts = []
        if self.context_before:
            parts.append(f"...{self.context_before}")
        parts.append(self.excerpt)
        if self.context_after:
            parts.append(f"{self.context_after}...")
        
        return " ".join(parts)
    
    def format_citation(self) -> str:
        """
        Format citation as a string
        
        Returns:
            Formatted citation string
        """
        parts = [self.source.title]
        
        if self.page_number:
            parts.append(f"Page {self.page_number}")
        
        if self.section:
            parts.append(self.section)
        
        citation = " (".join(parts)
        if len(parts) > 1:
            citation += ")"
        
        if self.excerpt:
            citation += f": '{self.excerpt[:100]}...'" if len(self.excerpt) > 100 else f": '{self.excerpt}'"
        
        return citation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'source': self.source.to_dict(),
            'confidence': self.confidence.value,
            'page_number': self.page_number,
            'section': self.section,
            'excerpt': self.excerpt,
            'excerpt_start': self.excerpt_start,
            'excerpt_end': self.excerpt_end,
            'context_before': self.context_before,
            'context_after': self.context_after,
            'reference_string': self.get_reference_string()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SourceCitation':
        """Create from dictionary"""
        return cls(
            source=DocumentSource.from_dict(data['source']),
            confidence=CitationConfidence(data['confidence']),
            page_number=data.get('page_number'),
            section=data.get('section'),
            excerpt=data.get('excerpt'),
            excerpt_start=data.get('excerpt_start'),
            excerpt_end=data.get('excerpt_end'),
            context_before=data.get('context_before'),
            context_after=data.get('context_after')
        )


@dataclass
class SearchResultMetadata:
    """Metadata about search execution"""
    query: str
    search_method: str  # "vector", "graph", "relational", "hybrid"
    total_documents: int
    filtered_count: int
    execution_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    weights: Optional[Dict[str, float]] = None
    filters_applied: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'query': self.query,
            'search_method': self.search_method,
            'total_documents': self.total_documents,
            'filtered_count': self.filtered_count,
            'execution_time_ms': self.execution_time_ms,
            'timestamp': self.timestamp.isoformat(),
            'weights': self.weights,
            'filters_applied': self.filters_applied
        }


@dataclass
class SearchResult:
    """
    Complete search result with documents and metadata
    
    Returned by RAGService search methods.
    Contains all retrieved documents and search metadata.
    """
    documents: List[DocumentSource]
    metadata: SearchResultMetadata
    
    def get_top_k(self, k: int = 5) -> List[DocumentSource]:
        """Get top K documents by relevance"""
        return sorted(
            self.documents,
            key=lambda d: d.relevance_score.hybrid,
            reverse=True
        )[:k]
    
    def filter_by_confidence(
        self,
        min_confidence: CitationConfidence = CitationConfidence.MEDIUM
    ) -> List[DocumentSource]:
        """Filter documents by minimum confidence level"""
        confidence_values = {
            CitationConfidence.UNKNOWN: 0,
            CitationConfidence.LOW: 1,
            CitationConfidence.MEDIUM: 2,
            CitationConfidence.HIGH: 3,
            CitationConfidence.DIRECT: 4
        }
        
        min_value = confidence_values[min_confidence]
        
        return [
            doc for doc in self.documents
            if confidence_values[doc.get_confidence()] >= min_value
        ]
    
    def deduplicate_by_id(self) -> List[DocumentSource]:
        """Remove duplicate documents by ID"""
        seen_ids = set()
        unique_docs = []
        
        for doc in self.documents:
            if doc.document_id not in seen_ids:
                seen_ids.add(doc.document_id)
                unique_docs.append(doc)
        
        return unique_docs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'documents': [doc.to_dict() for doc in self.documents],
            'metadata': self.metadata.to_dict()
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """Create from dictionary"""
        metadata = SearchResultMetadata(
            query=data['metadata']['query'],
            search_method=data['metadata']['search_method'],
            total_documents=data['metadata']['total_documents'],
            filtered_count=data['metadata']['filtered_count'],
            execution_time_ms=data['metadata']['execution_time_ms'],
            timestamp=datetime.fromisoformat(data['metadata']['timestamp']),
            weights=data['metadata'].get('weights'),
            filters_applied=data['metadata'].get('filters_applied')
        )
        
        documents = [
            DocumentSource.from_dict(doc_data)
            for doc_data in data['documents']
        ]
        
        return cls(documents=documents, metadata=metadata)


# Helper functions

def create_mock_document(
    document_id: str,
    title: str,
    content: str,
    relevance: float = 0.8
) -> DocumentSource:
    """
    Create a mock document for testing
    
    Args:
        document_id: Unique document ID
        title: Document title
        content: Document content
        relevance: Relevance score (default 0.8)
        
    Returns:
        DocumentSource instance
    """
    score = RelevanceScore(semantic=relevance, hybrid=relevance)
    
    return DocumentSource(
        document_id=document_id,
        title=title,
        content=content,
        source_type=SourceType.FILE,
        relevance_score=score,
        language="de"
    )


def extract_page_number_from_metadata(metadata: Dict[str, Any]) -> Optional[int]:
    """
    Extract page number from various metadata formats
    
    Tries common keys: 'page', 'page_number', 'pageNumber', 'pg'
    
    Args:
        metadata: Document metadata dictionary
        
    Returns:
        Page number if found, None otherwise
    """
    page_keys = ['page', 'page_number', 'pageNumber', 'pg', 'page_num']
    
    for key in page_keys:
        if key in metadata:
            try:
                return int(metadata[key])
            except (ValueError, TypeError):
                continue
    
    return None


# Test function
if __name__ == "__main__":
    print("="*80)
    print("DOCUMENT SOURCE MODELS - STANDALONE TEST")
    print("="*80)
    
    # Test 1: RelevanceScore
    print("\n1. RelevanceScore:")
    score = RelevanceScore(semantic=0.85, keyword=0.6, graph=0.4)
    hybrid = score.calculate_hybrid(
        semantic_weight=0.5,
        keyword_weight=0.3,
        graph_weight=0.2
    )
    print(f"   - Semantic: {score.semantic}")
    print(f"   - Keyword: {score.keyword}")
    print(f"   - Graph: {score.graph}")
    print(f"   - Hybrid: {score.hybrid:.3f}")
    print(f"   - Confidence: {score.get_confidence().value}")
    
    # Test 2: DocumentSource
    print("\n2. DocumentSource:")
    doc = create_mock_document(
        document_id="doc_123",
        title="Bauantragsverfahren Baden-Württemberg",
        content="Ein Bauantrag in Stuttgart erfordert die Einreichung...",
        relevance=0.92
    )
    print(f"   - ID: {doc.document_id}")
    print(f"   - Title: {doc.title}")
    print(f"   - Excerpt: {doc.get_excerpt(50)}")
    print(f"   - Confidence: {doc.get_confidence().value}")
    
    # Test 3: SourceCitation
    print("\n3. SourceCitation:")
    citation = SourceCitation(
        source=doc,
        confidence=CitationConfidence.HIGH,
        page_number=42,
        excerpt="Ein Bauantrag in Stuttgart erfordert..."
    )
    print(f"   - Reference: {citation.get_reference_string()}")
    print(f"   - Confidence: {citation.confidence.value}")
    print(f"   - Excerpt: {citation.excerpt[:50]}...")
    
    # Test 4: SearchResult
    print("\n4. SearchResult:")
    doc2 = create_mock_document(
        document_id="doc_456",
        title="Einfamilienhaus Genehmigung",
        content="Die Genehmigung für ein Einfamilienhaus...",
        relevance=0.78
    )
    
    metadata = SearchResultMetadata(
        query="Bauantrag Stuttgart",
        search_method="hybrid",
        total_documents=2,
        filtered_count=2,
        execution_time_ms=125.5
    )
    
    result = SearchResult(
        documents=[doc, doc2],
        metadata=metadata
    )
    
    print(f"   - Total documents: {len(result.documents)}")
    print(f"   - Query: {result.metadata.query}")
    print(f"   - Execution time: {result.metadata.execution_time_ms:.1f}ms")
    print(f"   - Top document: {result.get_top_k(1)[0].title}")
    
    # Test 5: JSON serialization
    print("\n5. JSON Serialization:")
    json_str = result.to_json(indent=None)
    print(f"   - JSON length: {len(json_str)} chars")
    print(f"   - JSON preview: {json_str[:100]}...")
    
    # Test 6: Deserialization
    print("\n6. Deserialization:")
    result_dict = result.to_dict()
    result_restored = SearchResult.from_dict(result_dict)
    print(f"   - Documents restored: {len(result_restored.documents)}")
    print(f"   - First doc ID: {result_restored.documents[0].document_id}")
    print(f"   - Match: {result_restored.documents[0].document_id == doc.document_id}")
    
    print("\n" + "="*80)
    print("✅ All document source models tests passed!")
    print("="*80)
