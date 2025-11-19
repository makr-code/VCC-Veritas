"""
VQB Frontend - Document Model

Data model for documents with relationship support.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from .base_model import Observable


class DocumentType(Enum):
    """Document type enumeration"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    JSON = "json"
    XML = "xml"
    OTHER = "other"


class RelationshipType(Enum):
    """Relationship type enumeration"""
    GRAPH = "graph"          # Neo4j graph relationships
    VECTOR = "vector"        # Semantic similarity
    RELATIONAL = "relational"  # Foreign key relationships
    FILE = "file"            # File system links


@dataclass
class Relationship:
    """
    Relationship between documents or processes
    
    Attributes:
        source_id: Source entity ID
        target_id: Target entity ID
        rel_type: Type of relationship
        weight: Relationship strength (0.0 to 1.0)
        metadata: Additional relationship data
    """
    source_id: str
    target_id: str
    rel_type: RelationshipType
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "rel_type": self.rel_type.value,
            "weight": self.weight,
            "metadata": self.metadata,
        }


@dataclass
class Document:
    """
    Data model for a document
    
    Attributes:
        id: Unique document identifier
        title: Document title
        doc_type: Document type
        content_preview: Preview of content (first N chars)
        authority: Issuing authority
        year: Publication year
        reference: Reference number/code
        relevance_score: Relevance score (0.0 to 1.0)
        file_path: Path to file (if applicable)
        metadata: Additional metadata
        relationships: List of relationships to other entities
    """
    id: str
    title: str
    doc_type: DocumentType = DocumentType.OTHER
    content_preview: str = ""
    authority: Optional[str] = None
    year: Optional[int] = None
    reference: Optional[str] = None
    relevance_score: float = 0.0
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    relationships: List[Relationship] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "doc_type": self.doc_type.value,
            "content_preview": self.content_preview,
            "authority": self.authority,
            "year": self.year,
            "reference": self.reference,
            "relevance_score": self.relevance_score,
            "file_path": self.file_path,
            "metadata": self.metadata,
            "relationships": [r.to_dict() for r in self.relationships],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create Document from dictionary"""
        relationships = [
            Relationship(
                source_id=r["source_id"],
                target_id=r["target_id"],
                rel_type=RelationshipType(r["rel_type"]),
                weight=r.get("weight", 1.0),
                metadata=r.get("metadata", {})
            )
            for r in data.get("relationships", [])
        ]
        
        return cls(
            id=data["id"],
            title=data["title"],
            doc_type=DocumentType(data.get("doc_type", "other")),
            content_preview=data.get("content_preview", ""),
            authority=data.get("authority"),
            year=data.get("year"),
            reference=data.get("reference"),
            relevance_score=data.get("relevance_score", 0.0),
            file_path=data.get("file_path"),
            metadata=data.get("metadata", {}),
            relationships=relationships,
        )


class DocumentModel(Observable):
    """
    Model for managing documents with Observable support
    
    Provides CRUD operations and relationship management.
    """
    
    def __init__(self):
        """Initialize document model"""
        super().__init__()
        self._documents: Dict[str, Document] = {}
    
    def add_document(self, document: Document):
        """
        Add a new document
        
        Args:
            document: Document to add
        """
        self._documents[document.id] = document
        self.notify(event="document_added", document=document)
    
    def update_document(self, doc_id: str, **kwargs):
        """
        Update document fields
        
        Args:
            doc_id: ID of document to update
            **kwargs: Fields to update
        """
        if doc_id in self._documents:
            document = self._documents[doc_id]
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            
            self.notify(event="document_updated", doc_id=doc_id, document=document)
    
    def remove_document(self, doc_id: str):
        """
        Remove a document
        
        Args:
            doc_id: ID of document to remove
        """
        if doc_id in self._documents:
            document = self._documents.pop(doc_id)
            self.notify(event="document_removed", doc_id=doc_id, document=document)
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Get document by ID
        
        Args:
            doc_id: Document ID
        
        Returns:
            Document if found, None otherwise
        """
        return self._documents.get(doc_id)
    
    def get_all_documents(self) -> List[Document]:
        """
        Get all documents
        
        Returns:
            List of all documents
        """
        return list(self._documents.values())
    
    def get_documents_by_type(self, doc_type: DocumentType) -> List[Document]:
        """
        Get documents filtered by type
        
        Args:
            doc_type: Document type to filter by
        
        Returns:
            List of documents with given type
        """
        return [d for d in self._documents.values() if d.doc_type == doc_type]
    
    def get_related_documents(self, entity_id: str, rel_type: Optional[RelationshipType] = None) -> List[Document]:
        """
        Get documents related to an entity
        
        Args:
            entity_id: ID of entity (process or document)
            rel_type: Optional relationship type filter
        
        Returns:
            List of related documents
        """
        related = []
        for doc in self._documents.values():
            for rel in doc.relationships:
                if rel.source_id == entity_id or rel.target_id == entity_id:
                    if rel_type is None or rel.rel_type == rel_type:
                        related.append(doc)
                        break
        return related
    
    def clear(self):
        """Remove all documents"""
        self._documents.clear()
        self.notify(event="documents_cleared")
    
    def load_documents(self, documents: List[Document]):
        """
        Load multiple documents at once
        
        Args:
            documents: List of documents to load
        """
        self.clear()
        for document in documents:
            self._documents[document.id] = document
        self.notify(event="documents_loaded", count=len(documents))
    
    def get_count(self) -> int:
        """Get total document count"""
        return len(self._documents)
