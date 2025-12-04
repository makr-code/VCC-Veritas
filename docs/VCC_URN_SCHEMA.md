# VCC-URN Schema - Uniform Resource Names für VCC-Veritas

## Version 1.0
**Datum**: 19. November 2025  
**Status**: Konzept & Spezifikation

---

## 1. Überblick

Das **VCC-URN Schema** definiert ein einheitliches Identifikationssystem für alle Entitäten im VCC-Veritas Ökosystem. URNs ermöglichen eindeutige, persistente und hierarchische Referenzierung über alle Teilsysteme hinweg (VPB, UDS3, Neo4j, PostgreSQL, ChromaDB, Files).

### 1.1 Grundprinzipien

- **Eindeutigkeit**: Jede URN identifiziert genau eine Entität
- **Persistenz**: URNs bleiben über Zeit und Systeme hinweg konstant
- **Hierarchie**: URNs reflektieren organisatorische Strukturen
- **Interoperabilität**: URNs funktionieren über alle VCC-Teilsysteme
- **Maschinenlesbarkeit**: Strukturierte Parsbarkeit für automatische Verarbeitung

---

## 2. VCC-URN Syntax

### 2.1 Grundstruktur

```
urn:vcc:{namespace}:{type}:{identifier}[:{subidentifier}]*
```

**Komponenten**:
- `urn` - URN Scheme Identifier (RFC 8141)
- `vcc` - Namespace Identifier (VCC-Veritas)
- `{namespace}` - Teilsystem-Namespace
- `{type}` - Entitätstyp
- `{identifier}` - Eindeutiger Identifier
- `{subidentifier}` - Optional: Hierarchische Unter-Identifier

### 2.2 Namespaces

```
urn:vcc:vpb:*       - VPB (Verwaltungspraxis der Bundesbehörden)
urn:vcc:legal:*     - Rechtliche Entitäten (Normen, Chunks, etc.)
urn:vcc:doc:*       - Dokumente
urn:vcc:chunk:*     - Text-Chunks
urn:vcc:graph:*     - Graph-Entitäten (Neo4j)
urn:vcc:proc:*      - Prozesse
urn:vcc:org:*       - Organisationen (Behörden)
urn:vcc:fed:*       - Föderale Ebenen
urn:vcc:session:*   - User Sessions
urn:vcc:query:*     - Queries/Anfragen
```

---

## 3. Detaillierte URN-Strukturen

### 3.1 VPB Prozesse

```
urn:vcc:vpb:process:{process-id}
urn:vcc:vpb:process:{process-id}:step:{step-id}
urn:vcc:vpb:process:{process-id}:milestone:{milestone-id}

Beispiele:
urn:vcc:vpb:process:baugenehmigung-2024-001
urn:vcc:vpb:process:baugenehmigung-2024-001:step:antragsprüfung
urn:vcc:vpb:process:baugenehmigung-2024-001:milestone:bescheiderteilung
```

**Komponenten**:
- `process-id`: Eindeutige Prozess-ID (z.B. `{typ}-{jahr}-{laufnummer}`)
- `step-id`: Prozessschritt-ID
- `milestone-id`: Meilenstein-ID

### 3.2 Rechtliche Chunks

```
urn:vcc:chunk:{source}:{doc-id}:{chunk-number}
urn:vcc:chunk:{source}:{doc-id}:{chunk-number}:para:{paragraph}

Beispiele:
urn:vcc:chunk:bimschg:bimschg-2024-001:42
urn:vcc:chunk:bimschg:bimschg-2024-001:42:para:5
urn:vcc:chunk:vwvfg:vwvfg-1976-001:128:para:28
```

**Komponenten**:
- `source`: Rechtsquelle (z.B. `bimschg`, `vwvfg`, `bgb`)
- `doc-id`: Dokument-ID
- `chunk-number`: Fortlaufende Chunk-Nummer
- `paragraph`: Optionaler Paragraph-Verweis

### 3.3 Rechtsbereiche

```
urn:vcc:legal:domain:{domain-code}
urn:vcc:legal:domain:{domain-code}:subdomain:{subdomain-code}

Beispiele:
urn:vcc:legal:domain:baurecht
urn:vcc:legal:domain:umweltrecht:subdomain:immissionsschutz
urn:vcc:legal:domain:verwaltungsrecht:subdomain:verfahrensrecht
```

**Komponenten**:
- `domain-code`: Rechtsbereichs-Code
- `subdomain-code`: Unter-Rechtsbereich

### 3.4 Rechtsnormen

```
urn:vcc:legal:norm:{norm-abbr}:{year}
urn:vcc:legal:norm:{norm-abbr}:{year}:para:{paragraph}
urn:vcc:legal:norm:{norm-abbr}:{year}:para:{paragraph}:abs:{absatz}

Beispiele:
urn:vcc:legal:norm:bimschg:2024
urn:vcc:legal:norm:vwvfg:1976:para:28
urn:vcc:legal:norm:bgb:2002:para:110:abs:1
```

**Komponenten**:
- `norm-abbr`: Normabkürzung (z.B. `bimschg`, `vwvfg`)
- `year`: Gültigkeitsjahr
- `paragraph`: Paragraph-Nummer
- `absatz`: Absatz-Nummer

### 3.5 Föderale Ebenen

```
urn:vcc:fed:{level}:{jurisdiction}

Beispiele:
urn:vcc:fed:bund:de
urn:vcc:fed:land:brandenburg
urn:vcc:fed:land:berlin
urn:vcc:fed:kommune:potsdam
```

**Komponenten**:
- `level`: Föderale Ebene (`bund`, `land`, `kommune`)
- `jurisdiction`: Zuständigkeitsbereich

### 3.6 Behörden

```
urn:vcc:org:authority:{org-id}

Beispiele:
urn:vcc:org:authority:bmu
urn:vcc:org:authority:mluk-bb
urn:vcc:org:authority:stadt-potsdam
```

**Komponenten**:
- `org-id`: Organisations-ID

### 3.7 Dokumente

```
urn:vcc:doc:{doc-type}:{doc-id}
urn:vcc:doc:{doc-type}:{doc-id}:version:{version}

Beispiele:
urn:vcc:doc:pdf:bimschg-volltext-2024
urn:vcc:doc:docx:antrag-baugenehmigung-001:version:2
```

**Komponenten**:
- `doc-type`: Dokumenttyp (pdf, docx, xml, etc.)
- `doc-id`: Dokument-ID
- `version`: Optionale Versionsnummer

### 3.8 Graph-Beziehungen

```
urn:vcc:graph:rel:{rel-type}:{source-urn-hash}:{target-urn-hash}

Beispiele:
urn:vcc:graph:rel:belongs-to:a3f2c8d1:b9e4f7a2
urn:vcc:graph:rel:governed-by:c7d9e2f1:d8f3a5b4
```

**Komponenten**:
- `rel-type`: Beziehungstyp (kebab-case)
- `source-urn-hash`: Hash der Quell-URN (8 Zeichen)
- `target-urn-hash`: Hash der Ziel-URN (8 Zeichen)

### 3.9 Sessions

```
urn:vcc:session:{user-id}:{timestamp}:{session-id}

Beispiele:
urn:vcc:session:user001:20251119T122345:a7f3e9d2
```

**Komponenten**:
- `user-id`: Benutzer-ID
- `timestamp`: ISO 8601 Timestamp
- `session-id`: Eindeutige Session-ID

### 3.10 Queries

```
urn:vcc:query:{session-id}:{query-number}

Beispiele:
urn:vcc:query:a7f3e9d2:001
urn:vcc:query:a7f3e9d2:042
```

**Komponenten**:
- `session-id`: Zugehörige Session
- `query-number`: Fortlaufende Query-Nummer

---

## 4. Python-Implementierung

### 4.1 URN Basis-Klasse

```python
"""
VCC-URN - Uniform Resource Names für VCC-Veritas
"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class URNNamespace(Enum):
    """VCC-URN Namespaces"""
    VPB = "vpb"
    LEGAL = "legal"
    DOC = "doc"
    CHUNK = "chunk"
    GRAPH = "graph"
    PROC = "proc"
    ORG = "org"
    FED = "fed"
    SESSION = "session"
    QUERY = "query"


@dataclass
class URN:
    """
    VCC Uniform Resource Name
    
    Attributes:
        namespace: Namespace (vpb, legal, doc, etc.)
        type: Entity type
        identifier: Primary identifier
        subidentifiers: Hierarchical sub-identifiers
    """
    namespace: URNNamespace
    type: str
    identifier: str
    subidentifiers: List[tuple[str, str]] = None  # [(type, id), ...]
    
    def __post_init__(self):
        if self.subidentifiers is None:
            self.subidentifiers = []
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "urn": str(self),
            "namespace": self.namespace.value,
            "type": self.type,
            "identifier": self.identifier,
            "subidentifiers": {stype: sid for stype, sid in self.subidentifiers}
        }
```

### 4.2 URN Factory Functions

```python
"""URN Factory Functions"""


def create_vpb_process_urn(process_id: str) -> URN:
    """Create URN for VPB process"""
    return URN(
        namespace=URNNamespace.VPB,
        type="process",
        identifier=process_id
    )


def create_vpb_process_step_urn(process_id: str, step_id: str) -> URN:
    """Create URN for VPB process step"""
    return URN(
        namespace=URNNamespace.VPB,
        type="process",
        identifier=process_id,
        subidentifiers=[("step", step_id)]
    )


def create_chunk_urn(source: str, doc_id: str, chunk_number: int) -> URN:
    """Create URN for legal chunk"""
    return URN(
        namespace=URNNamespace.CHUNK,
        type=source,
        identifier=f"{doc_id}:{chunk_number}"
    )


def create_legal_domain_urn(domain_code: str, subdomain_code: Optional[str] = None) -> URN:
    """Create URN for legal domain"""
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
    """Create URN for legal norm"""
    urn = URN(
        namespace=URNNamespace.LEGAL,
        type="norm",
        identifier=f"{norm_abbr}:{year}"
    )
    
    if paragraph:
        urn = urn.add_subidentifier("para", paragraph)
    
    if absatz:
        urn = urn.add_subidentifier("abs", str(absatz))
    
    return urn


def create_federal_urn(level: str, jurisdiction: str) -> URN:
    """Create URN for federal level"""
    return URN(
        namespace=URNNamespace.FED,
        type=level,
        identifier=jurisdiction
    )


def create_authority_urn(org_id: str) -> URN:
    """Create URN for authority"""
    return URN(
        namespace=URNNamespace.ORG,
        type="authority",
        identifier=org_id
    )


def create_document_urn(doc_type: str, doc_id: str, 
                       version: Optional[str] = None) -> URN:
    """Create URN for document"""
    urn = URN(
        namespace=URNNamespace.DOC,
        type=doc_type,
        identifier=doc_id
    )
    
    if version:
        urn = urn.add_subidentifier("version", version)
    
    return urn


def create_session_urn(user_id: str, timestamp: str, session_id: str) -> URN:
    """Create URN for session"""
    return URN(
        namespace=URNNamespace.SESSION,
        type=user_id,
        identifier=f"{timestamp}:{session_id}"
    )


def create_query_urn(session_id: str, query_number: int) -> URN:
    """Create URN for query"""
    return URN(
        namespace=URNNamespace.QUERY,
        type=session_id,
        identifier=f"{query_number:03d}"
    )
```

### 4.3 URN Resolver

```python
"""URN Resolver - Resolve URNs to actual entities"""

from typing import Optional, Any
from abc import ABC, abstractmethod


class URNResolver(ABC):
    """Abstract URN resolver"""
    
    @abstractmethod
    async def resolve(self, urn: URN) -> Optional[Any]:
        """
        Resolve URN to entity
        
        Args:
            urn: URN to resolve
        
        Returns:
            Resolved entity or None
        """
        pass


class VPBProcessResolver(URNResolver):
    """Resolver for VPB process URNs"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    async def resolve(self, urn: URN) -> Optional[Any]:
        """Resolve VPB process URN"""
        if urn.namespace != URNNamespace.VPB:
            return None
        
        if urn.type == "process":
            # Fetch process from API
            process_id = urn.identifier
            response = await self.api_client.get(f"/api/v3/vpb/process/{process_id}")
            return response.json()
        
        return None


class ChunkResolver(URNResolver):
    """Resolver for chunk URNs"""
    
    def __init__(self, neo4j_client):
        self.neo4j = neo4j_client
    
    async def resolve(self, urn: URN) -> Optional[Any]:
        """Resolve chunk URN"""
        if urn.namespace != URNNamespace.CHUNK:
            return None
        
        # Parse identifier
        parts = urn.identifier.split(":")
        if len(parts) != 2:
            return None
        
        doc_id, chunk_number = parts
        source = urn.type
        
        # Query Neo4j
        query = """
        MATCH (c:Chunk {source: $source, doc_id: $doc_id, chunk_number: $chunk_number})
        RETURN c
        """
        result = await self.neo4j.run(query, 
                                     source=source, 
                                     doc_id=doc_id,
                                     chunk_number=int(chunk_number))
        
        return result.single() if result else None


class CompositeURNResolver(URNResolver):
    """Composite resolver that delegates to specific resolvers"""
    
    def __init__(self):
        self.resolvers: Dict[URNNamespace, URNResolver] = {}
    
    def register(self, namespace: URNNamespace, resolver: URNResolver):
        """Register resolver for namespace"""
        self.resolvers[namespace] = resolver
    
    async def resolve(self, urn: URN) -> Optional[Any]:
        """Resolve using appropriate resolver"""
        resolver = self.resolvers.get(urn.namespace)
        if resolver:
            return await resolver.resolve(urn)
        return None
```

---

## 5. Integration in VQB

### 5.1 Erweiterte Modelle mit URN

```python
"""VQB Models mit URN-Support"""

from vqb_frontend.urn import URN, create_vpb_process_urn, create_chunk_urn

@dataclass
class Process:
    """Process mit URN"""
    id: str
    title: str
    # ... other fields
    
    @property
    def urn(self) -> URN:
        """Get process URN"""
        return create_vpb_process_urn(self.id)
    
    @classmethod
    def from_urn(cls, urn: URN, **kwargs) -> "Process":
        """Create process from URN"""
        if urn.namespace != URNNamespace.VPB or urn.type != "process":
            raise ValueError(f"Invalid process URN: {urn}")
        
        return cls(id=urn.identifier, **kwargs)


@dataclass
class Chunk:
    """Chunk mit URN"""
    source: str
    doc_id: str
    chunk_number: int
    content: str
    # ... other fields
    
    @property
    def urn(self) -> URN:
        """Get chunk URN"""
        return create_chunk_urn(self.source, self.doc_id, self.chunk_number)
    
    @classmethod
    def from_urn(cls, urn: URN, **kwargs) -> "Chunk":
        """Create chunk from URN"""
        if urn.namespace != URNNamespace.CHUNK:
            raise ValueError(f"Invalid chunk URN: {urn}")
        
        parts = urn.identifier.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid chunk URN identifier: {urn.identifier}")
        
        doc_id, chunk_number = parts
        
        return cls(
            source=urn.type,
            doc_id=doc_id,
            chunk_number=int(chunk_number),
            **kwargs
        )
```

### 5.2 URN-basierte Navigation

```python
class URNNavigator:
    """Navigate application using URNs"""
    
    def __init__(self, app, resolver):
        self.app = app
        self.resolver = resolver
    
    async def navigate_to_urn(self, urn: URN):
        """
        Navigate to entity identified by URN
        
        Args:
            urn: Target URN
        """
        # Resolve URN
        entity = await self.resolver.resolve(urn)
        
        if entity is None:
            self.app.show_error(f"Could not resolve URN: {urn}")
            return
        
        # Navigate based on namespace
        if urn.namespace == URNNamespace.VPB:
            self._navigate_to_process(entity)
        elif urn.namespace == URNNamespace.CHUNK:
            self._navigate_to_chunk(entity)
        # ... more namespaces
    
    def _navigate_to_process(self, process):
        """Navigate to process in timeline"""
        # Scroll timeline to process
        # Highlight process
        # Open process details
        pass
    
    def _navigate_to_chunk(self, chunk):
        """Navigate to chunk in graph view"""
        # Switch to graph view
        # Center on chunk node
        # Open chunk inspector
        pass
```

---

## 6. Vorteile des VCC-URN Systems

1. **Eindeutige Identifikation**: Jede Entität über alle Systeme hinweg eindeutig referenzierbar
2. **Verlinkung**: Deep-Links zu spezifischen Entitäten (z.B. in Dokumentation, Exports)
3. **Provenance**: URN enthält Herkunftsinformation (Namespace, Typ)
4. **Versionierung**: Durch Subidentifier (z.B. `:version:2`)
5. **Interoperabilität**: Standardisierte Referenzen zwischen VCC-Teilsystemen
6. **Debugging**: URNs in Logs ermöglichen präzises Nachverfolgen
7. **API-Design**: RESTful Endpoints mit URN-Parametern
8. **Caching**: URN als Cache-Key
9. **Berechtigungen**: URN-basierte Access Control

---

## 7. Verwendungsbeispiele

### 7.1 Im VQB Frontend

```python
# Process anzeigen via URN
urn = URN.from_string("urn:vcc:vpb:process:baugenehmigung-2024-001")
await navigator.navigate_to_urn(urn)

# Chunk im Graph anzeigen
chunk_urn = URN.from_string("urn:vcc:chunk:bimschg:bimschg-2024-001:42")
await navigator.navigate_to_urn(chunk_urn)

# Rechtsbereich filtern
domain_urn = create_legal_domain_urn("umweltrecht", "immissionsschutz")
filter_panel.apply_domain_filter(domain_urn)
```

### 7.2 In Backend APIs

```python
@router.get("/api/v3/entity/{urn:path}")
async def get_entity_by_urn(urn: str):
    """Generic endpoint - resolve any URN"""
    urn_obj = URN.from_string(urn)
    entity = await resolver.resolve(urn_obj)
    return entity

# Usage:
# GET /api/v3/entity/urn:vcc:vpb:process:proc-001
# GET /api/v3/entity/urn:vcc:chunk:bimschg:doc-001:42
```

### 7.3 In Neo4j Queries

```cypher
// Chunk mit URN erstellen
CREATE (c:Chunk {
  urn: "urn:vcc:chunk:bimschg:bimschg-2024-001:42",
  content: "...",
  source: "bimschg",
  doc_id: "bimschg-2024-001",
  chunk_number: 42
})

// Query via URN
MATCH (c:Chunk {urn: "urn:vcc:chunk:bimschg:bimschg-2024-001:42"})
RETURN c
```

---

## 8. Migration & Adoption

### Phase 1: URN-Generierung
- URNs für existierende Entitäten generieren
- URN-Felder in Datenbanken hinzufügen

### Phase 2: Dual-Mode
- Beide Systeme parallel (Legacy IDs + URNs)
- Mapping zwischen Legacy IDs und URNs

### Phase 3: URN-First
- APIs bevorzugen URNs
- Legacy IDs optional

### Phase 4: URN-Only
- Vollständige Migration auf URNs
- Legacy IDs deprecated

---

**Version**: 1.0  
**Status**: Spezifikation & Referenz-Implementierung  
**Nächste Schritte**: Integration in VQB Frontend und Backend APIs
