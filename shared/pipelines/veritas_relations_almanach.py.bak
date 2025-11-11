#!/usr/bin/env python3
"""
VERITAS KNOWLEDGE GRAPH RELATIONS ALMANACH
==========================================
Umfassender Katalog aller möglichen und sinnvollen Relations für das VERITAS Knowledge Graph System
Basis für Knowledge Graph Embedding (KGE), Retrofitting und Graph Neural Networks (GNN)
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class RelationType(Enum):
    """Kategorien von Relationship-Typen"""

    STRUCTURAL = "structural"  # Dokumentstruktur
    LEGAL = "legal"  # Rechtliche Beziehungen
    SEMANTIC = "semantic"  # Inhaltliche Beziehungen
    TEMPORAL = "temporal"  # Zeitliche Beziehungen
    PROCEDURAL = "procedural"  # Verfahrensbezogene Beziehungen
    ADMINISTRATIVE = "administrative"  # Verwaltungsbezogene Beziehungen
    TECHNICAL = "technical"  # Technische Beziehungen
    QUALITY = "quality"  # Qualitätsbezogene Beziehungen


class GraphLevel(Enum):
    """Graph-Ebenen für Relationships"""

    DOCUMENT = "document"  # Document-zu-Document
    CHUNK = "chunk"  # Chunk-zu-Chunk
    HYBRID = "hybrid"  # Document-zu-Chunk oder gemischt
    ENTITY = "entity"  # Entity-zu-Entity
    CONCEPT = "concept"  # Concept-zu-Concept


@dataclass
class RelationDefinition:
    """Definition einer Knowledge Graph Relation"""

    name: str
    type: RelationType
    level: GraphLevel
    description: str
    source_node_types: List[str]
    target_node_types: List[str]
    properties: Dict[str, str]
    inverse_relation: Optional[str] = None
    transitivity: bool = False
    symmetry: bool = False
    reflexivity: bool = False
    weight_range: Tuple[float, float] = (0.0, 1.0)
    uds3_compliance: bool = True
    kge_importance: str = "medium"  # low, medium, high, critical


class VERITASRelationAlmanach:
    """Almanach aller VERITAS Knowledge Graph Relations"""

    def __init__(self):
        self.relations = self._define_all_relations()

    def _define_all_relations(self) -> Dict[str, RelationDefinition]:
        """Definiert alle Relations für das VERITAS Knowledge Graph"""

        relations = {}

        # =================================================================
        # 1. STRUKTURELLE RELATIONS (Document/Chunk Hierarchie)
        # =================================================================

        relations["PART_OF"] = RelationDefinition(
            name="PART_OF",
            type=RelationType.STRUCTURAL,
            level=GraphLevel.HYBRID,
            description="Chunk gehört zu Document",
            source_node_types=["DocumentChunk"],
            target_node_types=["Document"],
            properties={"chunk_index": "int", "chunk_position": "float", "chunk_size": "int"},
            inverse_relation="CONTAINS_CHUNK",
            kge_importance="critical",
        )

        relations["CONTAINS_CHUNK"] = RelationDefinition(
            name="CONTAINS_CHUNK",
            type=RelationType.STRUCTURAL,
            level=GraphLevel.HYBRID,
            description="Document enthält Chunk",
            source_node_types=["Document"],
            target_node_types=["DocumentChunk"],
            properties={"total_chunks": "int", "chunk_order": "list"},
            inverse_relation="PART_OF",
            kge_importance="critical",
        )

        relations["NEXT_CHUNK"] = RelationDefinition(
            name="NEXT_CHUNK",
            type=RelationType.STRUCTURAL,
            level=GraphLevel.CHUNK,
            description="Sequenzieller nächster Chunk",
            source_node_types=["DocumentChunk"],
            target_node_types=["DocumentChunk"],
            properties={"sequence_gap": "int", "content_overlap": "float"},
            inverse_relation="PREVIOUS_CHUNK",
            transitivity=True,
            kge_importance="high",
        )

        relations["PREVIOUS_CHUNK"] = RelationDefinition(
            name="PREVIOUS_CHUNK",
            type=RelationType.STRUCTURAL,
            level=GraphLevel.CHUNK,
            description="Sequenzieller vorheriger Chunk",
            source_node_types=["DocumentChunk"],
            target_node_types=["DocumentChunk"],
            properties={"sequence_gap": "int", "content_overlap": "float"},
            inverse_relation="NEXT_CHUNK",
            transitivity=True,
            kge_importance="high",
        )

        relations["SIBLING_CHUNK"] = RelationDefinition(
            name="SIBLING_CHUNK",
            type=RelationType.STRUCTURAL,
            level=GraphLevel.CHUNK,
            description="Chunks desselben Documents",
            source_node_types=["DocumentChunk"],
            target_node_types=["DocumentChunk"],
            properties={"distance": "int", "same_section": "bool"},
            symmetry=True,
            kge_importance="medium",
        )

        # =================================================================
        # 2. RECHTLICHE RELATIONS (Legal References)
        # =================================================================

        relations["UDS3_LEGAL_REFERENCE"] = RelationDefinition(
            name="UDS3_LEGAL_REFERENCE",
            type=RelationType.LEGAL,
            level=GraphLevel.HYBRID,
            description="UDS3-konforme rechtliche Referenz",
            source_node_types=["Document", "DocumentChunk"],
            target_node_types=["LegalReference", "Document"],
            properties={
                "reference_type": "str",
                "paragraph": "str",
                "confidence": "float",
                "context": "str",
                "uds3_category": "str",
            },
            kge_importance="critical",
        )

        relations["CITES"] = RelationDefinition(
            name="CITES",
            type=RelationType.LEGAL,
            level=GraphLevel.DOCUMENT,
            description="Dokument zitiert rechtliche Quelle",
            source_node_types=["Document"],
            target_node_types=["LegalReference", "Document"],
            properties={"citation_context": "str", "citation_strength": "float", "citation_type": "str"},
            inverse_relation="CITED_BY",
            kge_importance="high",
        )

        relations["CITED_BY"] = RelationDefinition(
            name="CITED_BY",
            type=RelationType.LEGAL,
            level=GraphLevel.DOCUMENT,
            description="Rechtliche Quelle wird zitiert von",
            source_node_types=["LegalReference", "Document"],
            target_node_types=["Document"],
            properties={"citation_frequency": "int", "citation_relevance": "float"},
            inverse_relation="CITES",
            kge_importance="high",
        )

        relations["LEGAL_BASIS"] = RelationDefinition(
            name="LEGAL_BASIS",
            type=RelationType.LEGAL,
            level=GraphLevel.DOCUMENT,
            description="Dokument basiert auf Rechtsgrundlage",
            source_node_types=["Document"],
            target_node_types=["LegalReference"],
            properties={
                "basis_type": "str",  # hauptrechtsgrundlage, zusatzgrundlage
                "relevance_score": "float",
                "application_context": "str",
            },
            kge_importance="critical",
        )

        relations["SUPERSEDES"] = RelationDefinition(
            name="SUPERSEDES",
            type=RelationType.LEGAL,
            level=GraphLevel.DOCUMENT,
            description="Dokument ersetzt vorheriges",
            source_node_types=["Document", "LegalReference"],
            target_node_types=["Document", "LegalReference"],
            properties={"superseded_date": "datetime", "transition_period": "duration", "partial_supersession": "bool"},
            inverse_relation="SUPERSEDED_BY",
            kge_importance="high",
        )

        relations["AMENDS"] = RelationDefinition(
            name="AMENDS",
            type=RelationType.LEGAL,
            level=GraphLevel.DOCUMENT,
            description="Dokument ändert bestehendes Dokument",
            source_node_types=["Document"],
            target_node_types=["Document", "LegalReference"],
            properties={"amendment_type": "str", "amended_sections": "list", "effective_date": "datetime"},
            inverse_relation="AMENDED_BY",
            kge_importance="high",
        )

        # =================================================================
        # 3. SEMANTISCHE RELATIONS (Inhaltliche Beziehungen)
        # =================================================================

        relations["UDS3_SEMANTIC_REFERENCE"] = RelationDefinition(
            name="UDS3_SEMANTIC_REFERENCE",
            type=RelationType.SEMANTIC,
            level=GraphLevel.HYBRID,
            description="UDS3-konforme semantische Beziehung",
            source_node_types=["Document", "DocumentChunk"],
            target_node_types=["Document", "DocumentChunk", "Concept"],
            properties={
                "semantic_type": "str",
                "similarity_score": "float",
                "topic_overlap": "float",
                "context_similarity": "float",
            },
            symmetry=True,
            kge_importance="high",
        )

        relations["SIMILAR_TO"] = RelationDefinition(
            name="SIMILAR_TO",
            type=RelationType.SEMANTIC,
            level=GraphLevel.HYBRID,
            description="Inhaltlich ähnlich",
            source_node_types=["Document", "DocumentChunk"],
            target_node_types=["Document", "DocumentChunk"],
            properties={
                "similarity_score": "float",
                "similarity_type": "str",  # content, topic, structure
                "common_entities": "list",
            },
            symmetry=True,
            kge_importance="high",
        )

        relations["RELATES_TO"] = RelationDefinition(
            name="RELATES_TO",
            type=RelationType.SEMANTIC,
            level=GraphLevel.HYBRID,
            description="Allgemeine inhaltliche Beziehung",
            source_node_types=["Document", "DocumentChunk", "Concept"],
            target_node_types=["Document", "DocumentChunk", "Concept"],
            properties={"relation_strength": "float", "relation_type": "str", "context": "str"},
            symmetry=True,
            kge_importance="medium",
        )

        relations["CONTRADICTS"] = RelationDefinition(
            name="CONTRADICTS",
            type=RelationType.SEMANTIC,
            level=GraphLevel.HYBRID,
            description="Widersprüchlicher Inhalt",
            source_node_types=["Document", "DocumentChunk"],
            target_node_types=["Document", "DocumentChunk"],
            properties={"contradiction_type": "str", "severity": "float", "resolution_needed": "bool"},
            symmetry=True,
            kge_importance="high",
        )

        relations["ELABORATES"] = RelationDefinition(
            name="ELABORATES",
            type=RelationType.SEMANTIC,
            level=GraphLevel.HYBRID,
            description="Erläutert oder vertieft Inhalt",
            source_node_types=["Document", "DocumentChunk"],
            target_node_types=["Document", "DocumentChunk"],
            properties={"elaboration_type": "str", "detail_level": "int", "completeness": "float"},
            inverse_relation="ELABORATED_BY",
            kge_importance="medium",
        )

        # =================================================================
        # 4. TEMPORALE RELATIONS (Zeitliche Beziehungen)
        # =================================================================

        relations["PRECEDES"] = RelationDefinition(
            name="PRECEDES",
            type=RelationType.TEMPORAL,
            level=GraphLevel.DOCUMENT,
            description="Zeitlich vorhergehend",
            source_node_types=["Document", "ProcessStep"],
            target_node_types=["Document", "ProcessStep"],
            properties={"time_gap": "duration", "causal_relation": "bool", "sequence_type": "str"},
            inverse_relation="FOLLOWS",
            transitivity=True,
            kge_importance="medium",
        )

        relations["FOLLOWS"] = RelationDefinition(
            name="FOLLOWS",
            type=RelationType.TEMPORAL,
            level=GraphLevel.DOCUMENT,
            description="Zeitlich nachfolgend",
            source_node_types=["Document", "ProcessStep"],
            target_node_types=["Document", "ProcessStep"],
            properties={"time_gap": "duration", "causal_relation": "bool", "sequence_type": "str"},
            inverse_relation="PRECEDES",
            transitivity=True,
            kge_importance="medium",
        )

        relations["SIMULTANEOUS"] = RelationDefinition(
            name="SIMULTANEOUS",
            type=RelationType.TEMPORAL,
            level=GraphLevel.DOCUMENT,
            description="Zeitgleich entstanden/gültig",
            source_node_types=["Document"],
            target_node_types=["Document"],
            properties={"time_overlap": "float", "synchronicity_type": "str"},
            symmetry=True,
            kge_importance="low",
        )

        # =================================================================
        # 5. PROZESSUALE RELATIONS (Verfahrensbezogen)
        # =================================================================

        relations["TRIGGERS"] = RelationDefinition(
            name="TRIGGERS",
            type=RelationType.PROCEDURAL,
            level=GraphLevel.DOCUMENT,
            description="Löst Verfahren/Prozess aus",
            source_node_types=["Document", "Event"],
            target_node_types=["Process", "Document"],
            properties={"trigger_condition": "str", "automatic": "bool", "delay": "duration"},
            inverse_relation="TRIGGERED_BY",
            kge_importance="high",
        )

        relations["REQUIRES"] = RelationDefinition(
            name="REQUIRES",
            type=RelationType.PROCEDURAL,
            level=GraphLevel.DOCUMENT,
            description="Benötigt als Voraussetzung",
            source_node_types=["Document", "Process"],
            target_node_types=["Document", "Requirement"],
            properties={"requirement_type": "str", "mandatory": "bool", "fulfillment_criteria": "str"},
            inverse_relation="REQUIRED_BY",
            kge_importance="high",
        )

        relations["ENABLES"] = RelationDefinition(
            name="ENABLES",
            type=RelationType.PROCEDURAL,
            level=GraphLevel.DOCUMENT,
            description="Ermöglicht/berechtigt zu",
            source_node_types=["Document", "Authority"],
            target_node_types=["Action", "Process"],
            properties={"authorization_scope": "str", "conditions": "list", "validity_period": "duration"},
            inverse_relation="ENABLED_BY",
            kge_importance="medium",
        )

        # =================================================================
        # 6. ADMINISTRATIVE RELATIONS (Verwaltungsbezogen)
        # =================================================================

        relations["ISSUED_BY"] = RelationDefinition(
            name="ISSUED_BY",
            type=RelationType.ADMINISTRATIVE,
            level=GraphLevel.DOCUMENT,
            description="Ausgestellt/erlassen von",
            source_node_types=["Document"],
            target_node_types=["Authority", "Person", "Organization"],
            properties={"issue_date": "datetime", "authority_level": "str", "signature": "str"},
            inverse_relation="ISSUES",
            kge_importance="high",
        )

        relations["APPLIES_TO"] = RelationDefinition(
            name="APPLIES_TO",
            type=RelationType.ADMINISTRATIVE,
            level=GraphLevel.DOCUMENT,
            description="Gilt für/betrifft",
            source_node_types=["Document", "Regulation"],
            target_node_types=["Person", "Organization", "Location", "Process"],
            properties={"application_scope": "str", "exceptions": "list", "effective_period": "str"},
            inverse_relation="SUBJECT_TO",
            kge_importance="high",
        )

        relations["REFERENCES"] = RelationDefinition(
            name="REFERENCES",
            type=RelationType.ADMINISTRATIVE,
            level=GraphLevel.HYBRID,
            description="Verweist auf/referenziert",
            source_node_types=["Document", "DocumentChunk"],
            target_node_types=["Document", "LegalReference", "Case"],
            properties={"reference_type": "str", "context": "str", "relevance": "float"},
            inverse_relation="REFERENCED_BY",
            kge_importance="medium",
        )

        # =================================================================
        # 7. TECHNISCHE RELATIONS (System/Verarbeitung)
        # =================================================================

        relations["PROCESSED_BY"] = RelationDefinition(
            name="PROCESSED_BY",
            type=RelationType.TECHNICAL,
            level=GraphLevel.HYBRID,
            description="Verarbeitet durch System/Worker",
            source_node_types=["Document", "DocumentChunk"],
            target_node_types=["Worker", "System", "Algorithm"],
            properties={
                "processing_timestamp": "datetime",
                "processing_version": "str",
                "processing_quality": "float",
                "processing_duration": "duration",
            },
            inverse_relation="PROCESSES",
            kge_importance="low",
        )

        relations["GENERATED_FROM"] = RelationDefinition(
            name="GENERATED_FROM",
            type=RelationType.TECHNICAL,
            level=GraphLevel.HYBRID,
            description="Generiert aus Quelldaten",
            source_node_types=["Document", "DocumentChunk", "Embedding"],
            target_node_types=["Document", "RawData"],
            properties={"generation_method": "str", "transformation_type": "str", "confidence": "float"},
            inverse_relation="GENERATES",
            kge_importance="low",
        )

        relations["VECTORIZED_AS"] = RelationDefinition(
            name="VECTORIZED_AS",
            type=RelationType.TECHNICAL,
            level=GraphLevel.HYBRID,
            description="Repräsentiert als Vektor/Embedding",
            source_node_types=["Document", "DocumentChunk"],
            target_node_types=["Embedding", "Vector"],
            properties={"embedding_model": "str", "vector_dimension": "int", "embedding_quality": "float"},
            inverse_relation="REPRESENTS",
            kge_importance="medium",
        )

        # =================================================================
        # 8. QUALITÄTS-RELATIONS (Quality Management)
        # =================================================================

        relations["VALIDATES"] = RelationDefinition(
            name="VALIDATES",
            type=RelationType.QUALITY,
            level=GraphLevel.HYBRID,
            description="Validiert Qualität/Korrektheit",
            source_node_types=["QualityCheck", "Validator"],
            target_node_types=["Document", "DocumentChunk", "Relationship"],
            properties={"validation_score": "float", "validation_criteria": "list", "validation_timestamp": "datetime"},
            inverse_relation="VALIDATED_BY",
            kge_importance="medium",
        )

        relations["CONFLICTS_WITH"] = RelationDefinition(
            name="CONFLICTS_WITH",
            type=RelationType.QUALITY,
            level=GraphLevel.HYBRID,
            description="Konflikt/Inkonsistenz mit",
            source_node_types=["Document", "DocumentChunk", "Relationship"],
            target_node_types=["Document", "DocumentChunk", "Relationship"],
            properties={"conflict_type": "str", "severity": "float", "resolution_strategy": "str"},
            symmetry=True,
            kge_importance="high",
        )

        relations["CONFIRMS"] = RelationDefinition(
            name="CONFIRMS",
            type=RelationType.QUALITY,
            level=GraphLevel.HYBRID,
            description="Bestätigt/unterstützt",
            source_node_types=["Document", "DocumentChunk"],
            target_node_types=["Document", "DocumentChunk", "Fact"],
            properties={"confirmation_strength": "float", "evidence_type": "str", "confidence": "float"},
            inverse_relation="CONFIRMED_BY",
            kge_importance="medium",
        )

        # =================================================================
        # 9. ENTITY-RELATIONS (Named Entity Relations)
        # =================================================================

        relations["MENTIONS"] = RelationDefinition(
            name="MENTIONS",
            type=RelationType.SEMANTIC,
            level=GraphLevel.ENTITY,
            description="Erwähnt Named Entity",
            source_node_types=["Document", "DocumentChunk"],
            target_node_types=["Person", "Organization", "Location", "Date", "Law"],
            properties={"mention_context": "str", "mention_frequency": "int", "mention_sentiment": "float"},
            inverse_relation="MENTIONED_IN",
            kge_importance="high",
        )

        relations["INVOLVES"] = RelationDefinition(
            name="INVOLVES",
            type=RelationType.PROCEDURAL,
            level=GraphLevel.ENTITY,
            description="Beteiligt Entity in Prozess",
            source_node_types=["Process", "Case", "Document"],
            target_node_types=["Person", "Organization", "Authority"],
            properties={"role": "str", "involvement_type": "str", "responsibility_level": "float"},
            inverse_relation="INVOLVED_IN",
            kge_importance="high",
        )

        relations["LOCATED_IN"] = RelationDefinition(
            name="LOCATED_IN",
            type=RelationType.SEMANTIC,
            level=GraphLevel.ENTITY,
            description="Geografisch verortet in",
            source_node_types=["Event", "Organization", "Process"],
            target_node_types=["Location", "Jurisdiction"],
            properties={"coordinates": "tuple", "administrative_level": "str", "jurisdiction_type": "str"},
            inverse_relation="CONTAINS_LOCATION",
            kge_importance="medium",
        )

        # =================================================================
        # 10. ADVANCED SEMANTIC RELATIONS (für KGE/Retrofitting)
        # =================================================================

        relations["CONCEPTUALLY_RELATED"] = RelationDefinition(
            name="CONCEPTUALLY_RELATED",
            type=RelationType.SEMANTIC,
            level=GraphLevel.CONCEPT,
            description="Konzeptuell verwandt (für KGE)",
            source_node_types=["Concept", "Topic"],
            target_node_types=["Concept", "Topic"],
            properties={"conceptual_distance": "float", "relation_strength": "float", "semantic_field": "str"},
            symmetry=True,
            kge_importance="critical",
        )

        relations["ENTAILS"] = RelationDefinition(
            name="ENTAILS",
            type=RelationType.SEMANTIC,
            level=GraphLevel.CONCEPT,
            description="Logisch impliziert",
            source_node_types=["Concept", "Statement"],
            target_node_types=["Concept", "Statement"],
            properties={"logical_strength": "float", "entailment_type": "str"},
            inverse_relation="ENTAILED_BY",
            transitivity=True,
            kge_importance="high",
        )

        relations["HYPERNYM_OF"] = RelationDefinition(
            name="HYPERNYM_OF",
            type=RelationType.SEMANTIC,
            level=GraphLevel.CONCEPT,
            description="Übergeordneter Begriff",
            source_node_types=["Concept"],
            target_node_types=["Concept"],
            properties={"abstraction_level": "int", "taxonomic_distance": "float"},
            inverse_relation="HYPONYM_OF",
            transitivity=True,
            kge_importance="high",
        )

        relations["HYPONYM_OF"] = RelationDefinition(
            name="HYPONYM_OF",
            type=RelationType.SEMANTIC,
            level=GraphLevel.CONCEPT,
            description="Untergeordneter Begriff",
            source_node_types=["Concept"],
            target_node_types=["Concept"],
            properties={"specificity_level": "int", "taxonomic_distance": "float"},
            inverse_relation="HYPERNYM_OF",
            transitivity=True,
            kge_importance="high",
        )

        return relations

    def get_relations_by_type(self, relation_type: RelationType) -> Dict[str, RelationDefinition]:
        """Filtert Relations nach Typ"""
        return {name: rel for name, rel in self.relations.items() if rel.type == relation_type}

    def get_relations_by_level(self, level: GraphLevel) -> Dict[str, RelationDefinition]:
        """Filtert Relations nach Graph-Level"""
        return {name: rel for name, rel in self.relations.items() if rel.level == level}

    def get_kge_critical_relations(self) -> Dict[str, RelationDefinition]:
        """Relations kritisch für Knowledge Graph Embeddings"""
        return {name: rel for name, rel in self.relations.items() if rel.kge_importance in ["critical", "high"]}

    def get_uds3_compliant_relations(self) -> Dict[str, RelationDefinition]:
        """UDS3-konforme Relations"""
        return {name: rel for name, rel in self.relations.items() if rel.uds3_compliance}

    def export_almanach(self, format: str = "json") -> str:
        """Exportiert Almanach in verschiedenen Formaten"""
        if format == "json":
            return self._export_json()
        elif format == "cypher":
            return self._export_cypher()
        elif format == "rdf":
            return self._export_rdf()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_json(self) -> str:
        """Exportiert als JSON für maschinelle Verarbeitung"""
        export_data = {}
        for name, rel in self.relations.items():
            export_data[name] = {
                "type": rel.type.value,
                "level": rel.level.value,
                "description": rel.description,
                "source_node_types": rel.source_node_types,
                "target_node_types": rel.target_node_types,
                "properties": rel.properties,
                "inverse_relation": rel.inverse_relation,
                "transitivity": rel.transitivity,
                "symmetry": rel.symmetry,
                "reflexivity": rel.reflexivity,
                "weight_range": rel.weight_range,
                "uds3_compliance": rel.uds3_compliance,
                "kge_importance": rel.kge_importance,
            }
        return json.dumps(export_data, indent=2, ensure_ascii=False)

    def _export_cypher(self) -> str:
        """Exportiert als Neo4j Cypher-Statements"""
        cypher_statements = []
        cypher_statements.append("// VERITAS Knowledge Graph Relations Schema")
        cypher_statements.append("// Auto-generated from Relations Almanach")
        cypher_statements.append("")

        for name, rel in self.relations.items():
            cypher_statements.append(f"// {name}: {rel.description}")
            cypher_statements.append(f"// Type: {rel.type.value}, Level: {rel.level.value}")
            cypher_statements.append(f"// KGE Importance: {rel.kge_importance}")

            # Beispiel-Statement
            source_type = rel.source_node_types[0] if rel.source_node_types else "Node"
            target_type = rel.target_node_types[0] if rel.target_node_types else "Node"

            cypher_statements.append(f"// MATCH (a:{source_type})-[r:{name}]->(b:{target_type})")
            cypher_statements.append("")

        return "\n".join(cypher_statements)

    def _export_rdf(self) -> str:
        """Exportiert als RDF/Turtle für Semantic Web"""
        # Vereinfachte RDF-Ausgabe
        rdf_lines = []
        rdf_lines.append("@prefix veritas: <http://veritas.tech/ontology/> .")
        rdf_lines.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
        rdf_lines.append("")

        for name, rel in self.relations.items():
            rdf_lines.append(f"veritas:{name} a rdfs:Property ;")
            rdf_lines.append(f'    rdfs:label "{name}" ;')
            rdf_lines.append(f'    rdfs:comment "{rel.description}" ;')
            rdf_lines.append(f'    veritas:relationType "{rel.type.value}" ;')
            rdf_lines.append(f'    veritas:kgeImportance "{rel.kge_importance}" .')
            rdf_lines.append("")

        return "\n".join(rdf_lines)

    def generate_kge_training_schema(self) -> Dict:
        """Generiert Schema für Knowledge Graph Embedding Training"""
        kge_schema = {
            "relation_types": {},
            "node_types": set(),
            "critical_relations": [],
            "embedding_dimensions": {},
            "training_priorities": {},
        }

        for name, rel in self.relations.items():
            # Sammle alle Node-Typen
            kge_schema["node_types"].update(rel.source_node_types)
            kge_schema["node_types"].update(rel.target_node_types)

            # Relation-Schema
            kge_schema["relation_types"][name] = {
                "domain": rel.source_node_types,
                "range": rel.target_node_types,
                "properties": list(rel.properties.keys()),
                "inverse": rel.inverse_relation,
                "transitive": rel.transitivity,
                "symmetric": rel.symmetry,
            }

            # Kritische Relations für Training
            if rel.kge_importance in ["critical", "high"]:
                kge_schema["critical_relations"].append(name)

            # Training-Prioritäten
            priority_map = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
            kge_schema["training_priorities"][name] = priority_map.get(rel.kge_importance, 0.5)

        kge_schema["node_types"] = list(kge_schema["node_types"])
        return kge_schema

    def print_almanach_summary(self):
        """Druckt Zusammenfassung des Almanachs"""
        print("🔗 VERITAS KNOWLEDGE GRAPH RELATIONS ALMANACH")
        print("=" * 60)

        # Statistiken nach Typ
        type_counts = {}
        for rel in self.relations.values():
            type_counts[rel.type.value] = type_counts.get(rel.type.value, 0) + 1

        print(f"\n📊 RELATIONS NACH TYP:")
        for rel_type, count in sorted(type_counts.items()):
            print(f"  {rel_type:15}: {count:3} Relations")

        # Statistiken nach Level
        level_counts = {}
        for rel in self.relations.values():
            level_counts[rel.level.value] = level_counts.get(rel.level.value, 0) + 1

        print(f"\n📊 RELATIONS NACH LEVEL:")
        for level, count in sorted(level_counts.items()):
            print(f"  {level:10}: {count:3} Relations")

        # KGE-kritische Relations
        kge_counts = {}
        for rel in self.relations.values():
            kge_counts[rel.kge_importance] = kge_counts.get(rel.kge_importance, 0) + 1

        print(f"\n📊 KGE-WICHTIGKEIT:")
        for importance, count in sorted(kge_counts.items()):
            print(f"  {importance:8}: {count:3} Relations")

        # Besondere Eigenschaften
        transitiv = sum(1 for rel in self.relations.values() if rel.transitivity)
        symmetrisch = sum(1 for rel in self.relations.values() if rel.symmetry)
        uds3 = sum(1 for rel in self.relations.values() if rel.uds3_compliance)

        print(f"\n📊 EIGENSCHAFTEN:")
        print(f"  Transitiv   : {transitiv:3} Relations")
        print(f"  Symmetrisch : {symmetrisch:3} Relations")
        print(f"  UDS3-konform: {uds3:3} Relations")

        print(f"\n📊 GESAMT: {len(self.relations)} Relations definiert")


def main():
    """Hauptfunktion - erstellt und präsentiert den Almanach"""
    almanach = VERITASRelationAlmanach()

    # Zusammenfassung anzeigen
    almanach.print_almanach_summary()

    # Exportiere verschiedene Formate
    print(f"\n💾 EXPORT-DATEIEN ERSTELLEN...")

    # JSON Export
    with open("veritas_relations_almanach.json", "w", encoding="utf-8") as f:
        f.write(almanach.export_almanach("json"))
    print(f"  ✅ JSON: veritas_relations_almanach.json")

    # Cypher Export
    with open("veritas_relations_schema.cypher", "w", encoding="utf-8") as f:
        f.write(almanach.export_almanach("cypher"))
    print(f"  ✅ Cypher: veritas_relations_schema.cypher")

    # RDF Export
    with open("veritas_relations_ontology.ttl", "w", encoding="utf-8") as f:
        f.write(almanach.export_almanach("rdf"))
    print(f"  ✅ RDF/Turtle: veritas_relations_ontology.ttl")

    # KGE Training Schema
    kge_schema = almanach.generate_kge_training_schema()
    with open("veritas_kge_training_schema.json", "w", encoding="utf-8") as f:
        json.dump(kge_schema, f, indent=2, ensure_ascii=False)
    print(f"  ✅ KGE Schema: veritas_kge_training_schema.json")

    print(f"\n🎯 VERWENDUNG FÜR WEITERENTWICKLUNG:")
    print(f"  📊 Knowledge Graph Embeddings (KGE): veritas_kge_training_schema.json")
    print(f"  🔧 Neo4j Schema: veritas_relations_schema.cypher")
    print(f"  🌐 Semantic Web: veritas_relations_ontology.ttl")
    print(f"  🤖 Machine Learning: veritas_relations_almanach.json")


if __name__ == "__main__":
    main()
