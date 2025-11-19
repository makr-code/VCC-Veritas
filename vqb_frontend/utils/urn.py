"""
VCC-URN - Uniform Resource Names for VCC-Veritas

Implements the VCC-URN schema for unique identification across all VCC subsystems.
"""

import re
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class URNNamespace(Enum):
    """VCC-URN Namespaces"""
    VPB = "vpb"           # Verwaltungspraxis der Bundesbehörden
    LEGAL = "legal"       # Rechtliche Entitäten
    DOC = "doc"           # Dokumente
    CHUNK = "chunk"       # Text-Chunks
    GRAPH = "graph"       # Graph-Entitäten
    PROC = "proc"         # Prozesse
    ORG = "org"           # Organisationen
    FED = "fed"           # Föderale Ebenen
    SESSION = "session"   # User Sessions
    QUERY = "query"       # Queries


@dataclass
class URN:
    """
    VCC Uniform Resource Name
    
    Represents a unique identifier following the VCC-URN schema:
    urn:vcc:{namespace}:{type}:{identifier}[:{subidentifier}]*
    
    Attributes:
        namespace: Namespace (vpb, legal, doc, etc.)
        type: Entity type
        identifier: Primary identifier
        subidentifiers: Hierarchical sub-identifiers [(type, id), ...]
    
    Examples:
        >>> urn = URN(URNNamespace.VPB, "process", "baugenehmigung-2024-001")
        >>> str(urn)
        'urn:vcc:vpb:process:baugenehmigung-2024-001'
        
        >>> urn2 = URN.from_string("urn:vcc:chunk:bimschg:doc-001:42")
        >>> urn2.namespace
        <URNNamespace.CHUNK: 'chunk'>
    """
    namespace: URNNamespace
    type: str
    identifier: str
    subidentifiers: List[Tuple[str, str]] = field(default_factory=list)
    
    def __str__(self) -> str:
        """Convert to URN string"""
        urn_parts = [
            "urn",
            "vcc",
            self.namespace.value,
            self.type,
            self.identifier
        ]
        
        # Add subidentifiers
        for sub_type, sub_id in self.subidentifiers:
            urn_parts.extend([sub_type, sub_id])
        
        return ":".join(urn_parts)
    
    def __repr__(self) -> str:
        return f"URN('{str(self)}')"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, URN):
            return False
        return str(self) == str(other)
    
    def __hash__(self) -> int:
        return hash(str(self))
    
    @classmethod
    def from_string(cls, urn_string: str) -> "URN":
        """
        Parse URN from string
        
        Args:
            urn_string: URN string (e.g., "urn:vcc:vpb:process:proc-001")
        
        Returns:
            URN object
        
        Raises:
            ValueError: If URN format is invalid
        """
        if not urn_string.startswith("urn:vcc:"):
            raise ValueError(f"Invalid VCC-URN: {urn_string}")
        
        parts = urn_string.split(":")
        
        if len(parts) < 5:
            raise ValueError(f"URN too short: {urn_string}")
        
        # Parse fixed parts
        namespace_str = parts[2]
        entity_type = parts[3]
        identifier = parts[4]
        
        # Validate namespace
        try:
            namespace = URNNamespace(namespace_str)
        except ValueError:
            raise ValueError(f"Unknown namespace: {namespace_str}")
        
        # Parse subidentifiers
        subidentifiers = []
        if len(parts) > 5:
            # Remaining parts are subidentifier pairs
            sub_parts = parts[5:]
            if len(sub_parts) % 2 != 0:
                raise ValueError(f"Odd number of subidentifier parts: {urn_string}")
            
            for i in range(0, len(sub_parts), 2):
                sub_type = sub_parts[i]
                sub_id = sub_parts[i + 1]
                subidentifiers.append((sub_type, sub_id))
        
        return cls(
            namespace=namespace,
            type=entity_type,
            identifier=identifier,
            subidentifiers=subidentifiers
        )
    
    def add_subidentifier(self, sub_type: str, sub_id: str) -> "URN":
        """
        Add a subidentifier (returns new URN)
        
        Args:
            sub_type: Subidentifier type
            sub_id: Subidentifier value
        
        Returns:
            New URN with added subidentifier
        """
        new_subs = self.subidentifiers.copy()
        new_subs.append((sub_type, sub_id))
        
        return URN(
            namespace=self.namespace,
            type=self.type,
            identifier=self.identifier,
            subidentifiers=new_subs
        )
    
    def get_subidentifier(self, sub_type: str) -> Optional[str]:
        """
        Get subidentifier value by type
        
        Args:
            sub_type: Subidentifier type to find
        
        Returns:
            Subidentifier value or None
        """
        for stype, sid in self.subidentifiers:
            if stype == sub_type:
                return sid
        return None
    
    def has_subidentifier(self, sub_type: str) -> bool:
        """Check if URN has subidentifier of given type"""
        return self.get_subidentifier(sub_type) is not None
    
    def get_hash(self, length: int = 8) -> str:
        """
        Get hash of URN
        
        Args:
            length: Hash length (default 8 characters)
        
        Returns:
            Hex hash string
        """
        hash_obj = hashlib.sha256(str(self).encode())
        return hash_obj.hexdigest()[:length]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "urn": str(self),
            "namespace": self.namespace.value,
            "type": self.type,
            "identifier": self.identifier,
            "subidentifiers": {stype: sid for stype, sid in self.subidentifiers}
        }


# ============================================================================
# URN Factory Functions
# ============================================================================

def create_vpb_process_urn(process_id: str) -> URN:
    """
    Create URN for VPB process
    
    Args:
        process_id: Process identifier
    
    Returns:
        URN for process
    
    Example:
        >>> urn = create_vpb_process_urn("baugenehmigung-2024-001")
        >>> str(urn)
        'urn:vcc:vpb:process:baugenehmigung-2024-001'
    """
    return URN(
        namespace=URNNamespace.VPB,
        type="process",
        identifier=process_id
    )


def create_vpb_process_step_urn(process_id: str, step_id: str) -> URN:
    """
    Create URN for VPB process step
    
    Args:
        process_id: Process identifier
        step_id: Step identifier
    
    Returns:
        URN for process step
    """
    return URN(
        namespace=URNNamespace.VPB,
        type="process",
        identifier=process_id,
        subidentifiers=[("step", step_id)]
    )


def create_chunk_urn(source: str, doc_id: str, chunk_number: int) -> URN:
    """
    Create URN for legal chunk
    
    Args:
        source: Source legal code (e.g., "bimschg", "vwvfg")
        doc_id: Document identifier
        chunk_number: Chunk number within document
    
    Returns:
        URN for chunk
    
    Example:
        >>> urn = create_chunk_urn("bimschg", "bimschg-2024-001", 42)
        >>> str(urn)
        'urn:vcc:chunk:bimschg:bimschg-2024-001:42'
    """
    return URN(
        namespace=URNNamespace.CHUNK,
        type=source,
        identifier=f"{doc_id}:{chunk_number}"
    )


def create_legal_domain_urn(domain_code: str, subdomain_code: Optional[str] = None) -> URN:
    """
    Create URN for legal domain
    
    Args:
        domain_code: Legal domain code
        subdomain_code: Optional subdomain code
    
    Returns:
        URN for legal domain
    """
    urn = URN(
        namespace=URNNamespace.LEGAL,
        type="domain",
        identifier=domain_code
    )
    
    if subdomain_code:
        urn = urn.add_subidentifier("subdomain", subdomain_code)
    
    return urn


def create_legal_norm_urn(norm_abbr: str, year: int, 
                         paragraph: Optional[str] = None,
                         absatz: Optional[int] = None) -> URN:
    """
    Create URN for legal norm
    
    Args:
        norm_abbr: Norm abbreviation (e.g., "bimschg", "vwvfg")
        year: Year of validity
        paragraph: Optional paragraph number
        absatz: Optional subsection number
    
    Returns:
        URN for legal norm
    """
    urn = URN(
        namespace=URNNamespace.LEGAL,
        type="norm",
        identifier=norm_abbr,
        subidentifiers=[("year", str(year))]
    )
    
    if paragraph:
        urn = urn.add_subidentifier("para", paragraph)
    
    if absatz:
        urn = urn.add_subidentifier("abs", str(absatz))
    
    return urn


def create_federal_urn(level: str, jurisdiction: str) -> URN:
    """
    Create URN for federal level
    
    Args:
        level: Federal level ("bund", "land", "kommune")
        jurisdiction: Jurisdiction identifier
    
    Returns:
        URN for federal level
    """
    return URN(
        namespace=URNNamespace.FED,
        type=level,
        identifier=jurisdiction
    )


def create_authority_urn(org_id: str) -> URN:
    """
    Create URN for authority
    
    Args:
        org_id: Organization identifier
    
    Returns:
        URN for authority
    """
    return URN(
        namespace=URNNamespace.ORG,
        type="authority",
        identifier=org_id
    )


def create_document_urn(doc_type: str, doc_id: str, 
                       version: Optional[str] = None) -> URN:
    """
    Create URN for document
    
    Args:
        doc_type: Document type (pdf, docx, etc.)
        doc_id: Document identifier
        version: Optional version identifier
    
    Returns:
        URN for document
    """
    urn = URN(
        namespace=URNNamespace.DOC,
        type=doc_type,
        identifier=doc_id
    )
    
    if version:
        urn = urn.add_subidentifier("version", version)
    
    return urn


def create_session_urn(user_id: str, timestamp: str, session_id: str) -> URN:
    """
    Create URN for session
    
    Args:
        user_id: User identifier
        timestamp: ISO 8601 timestamp
        session_id: Session identifier
    
    Returns:
        URN for session
    """
    return URN(
        namespace=URNNamespace.SESSION,
        type=user_id,
        identifier=f"{timestamp}:{session_id}"
    )


def create_query_urn(session_id: str, query_number: int) -> URN:
    """
    Create URN for query
    
    Args:
        session_id: Session identifier
        query_number: Query number within session
    
    Returns:
        URN for query
    """
    return URN(
        namespace=URNNamespace.QUERY,
        type=session_id,
        identifier=f"{query_number:03d}"
    )


def create_graph_relationship_urn(rel_type: str, source_urn: URN, target_urn: URN) -> URN:
    """
    Create URN for graph relationship
    
    Args:
        rel_type: Relationship type (kebab-case)
        source_urn: Source entity URN
        target_urn: Target entity URN
    
    Returns:
        URN for relationship
    """
    source_hash = source_urn.get_hash()
    target_hash = target_urn.get_hash()
    
    return URN(
        namespace=URNNamespace.GRAPH,
        type="rel",
        identifier=f"{rel_type}:{source_hash}:{target_hash}"
    )
