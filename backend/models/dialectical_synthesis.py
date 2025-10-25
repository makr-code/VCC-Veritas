"""
Datenmodelle für Dialektische Synthese (Thesis-Antithesis-Synthesis)

Die dialektische Methode nach Hegel:
1. THESIS - Eine Ausgangsbehauptung/Position
2. ANTITHESIS - Der Widerspruch/Gegensatz zur These
3. SYNTHESIS - Die Auflösung des Widerspruchs auf höherer Ebene

Anwendung in VERITAS:
- Thesen = Agent-Results (verschiedene Experten-Perspektiven)
- Antithesen = Widersprüche zwischen Agent-Aussagen
- Synthese = LLM-gestützte Auflösung → kohärente Antwort
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, timezone


class ContradictionType(Enum):
    """Art des Widerspruchs zwischen Thesen"""
    LEGAL = "legal"                      # Unterschiedliche Rechtsauslegung
    FACTUAL = "factual"                  # Unterschiedliche Fakten
    TEMPORAL = "temporal"                # Unterschiedliche Zeiträume
    REGIONAL = "regional"                # Unterschiedliche Regionen/Zuständigkeiten
    METHODOLOGICAL = "methodological"    # Unterschiedliche Ansätze
    INTERPRETATION = "interpretation"    # Unterschiedliche Interpretationen


class ContradictionSeverity(Enum):
    """Schwere des Widerspruchs"""
    CRITICAL = "critical"      # Fundamentaler Widerspruch, MUSS aufgelöst werden
    MODERATE = "moderate"      # Teilweise inkonsistent, sollte geklärt werden
    MINOR = "minor"            # Nur unterschiedliche Nuancen, nicht problematisch


class ResolutionStrategy(Enum):
    """Strategie zur Widerspruchs-Auflösung"""
    CONTEXTUALIZATION = "contextualization"          # Beide richtig in unterschiedlichen Kontexten
    HIERARCHIZATION = "hierarchization"              # Eine Quelle ist autoritativer
    SYNTHESIS = "synthesis"                          # Beide enthalten Teilwahrheiten → höhere Ebene
    TEMPORAL_ORDERING = "temporal_ordering"          # Zeitliche Abfolge löst Widerspruch auf
    REGIONAL_DIFFERENTIATION = "regional"            # Regional unterschiedliche Regeln
    COMPLEMENTARY_PERSPECTIVES = "complementary"     # Unterschiedliche aber ergänzende Perspektiven


@dataclass
class Thesis:
    """
    Kern-Aussage aus Agent-Result
    
    Eine These ist eine extrahierte Behauptung/Position eines Agents
    mit Belegen und Konfidenz.
    """
    agent_source: str                        # Welcher Agent (z.B. "VerwaltungsrechtAgent")
    claim: str                               # Die Kern-Behauptung
    evidence: List[str]                      # Belege/Zitate
    confidence: float                        # Agent-Konfidenz (0-1)
    legal_basis: Optional[List[str]] = None  # Rechtsgrundlagen (z.B. ["§10 BauGB"])
    context: Optional[str] = None            # Kontext der Aussage
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        legal = f" [{', '.join(self.legal_basis)}]" if self.legal_basis else ""
        return f"[{self.agent_source}] {self.claim}{legal} (Konfidenz: {self.confidence:.2f})"
    
    def to_dict(self) -> dict:
        """Serialisiert Thesis für JSON"""
        return {
            'agent_source': self.agent_source,
            'claim': self.claim,
            'evidence': self.evidence,
            'confidence': self.confidence,
            'legal_basis': self.legal_basis,
            'context': self.context,
            'metadata': self.metadata
        }


@dataclass
class Contradiction:
    """
    Identifizierter Widerspruch zwischen zwei Thesen
    
    Eine Antithese im dialektischen Sinne - zwei Aussagen die
    sich widersprechen oder inkonsistent sind.
    """
    thesis_a: Thesis
    thesis_b: Thesis
    contradiction_type: ContradictionType
    severity: ContradictionSeverity
    description: str                         # Was widerspricht sich?
    potential_resolutions: List[str]         # Mögliche Auflösungen
    resolution_applied: Optional[ResolutionStrategy] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return (f"WIDERSPRUCH ({self.severity.value}, {self.contradiction_type.value}): "
                f"{self.thesis_a.agent_source} vs {self.thesis_b.agent_source} - "
                f"{self.description}")
    
    def to_dict(self) -> dict:
        """Serialisiert Contradiction für JSON"""
        return {
            'thesis_a': self.thesis_a.to_dict(),
            'thesis_b': self.thesis_b.to_dict(),
            'contradiction_type': self.contradiction_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'potential_resolutions': self.potential_resolutions,
            'resolution_applied': self.resolution_applied.value if self.resolution_applied else None,
            'metadata': self.metadata
        }


@dataclass
class DialecticalSynthesis:
    """
    Ergebnis der dialektischen Synthese
    
    Die Synthese auf höherer Ebene, die Widersprüche auflöst
    und eine kohärente Gesamt-Aussage bildet.
    
    Philosophischer Hintergrund:
    - These + Antithese = Synthese (Hegel)
    - Die Synthese hebt den Widerspruch auf (Aufhebung)
    - Neue Qualität entsteht auf höherer Abstraktionsebene
    """
    theses: List[Thesis]                      # Alle extrahierten Thesen
    contradictions: List[Contradiction]       # Identifizierte Widersprüche
    synthesis_text: str                       # Aufgelöste kohärente Antwort
    resolution_strategies: List[ResolutionStrategy]  # Verwendete Auflösungs-Strategien
    unresolved_conflicts: List[Contradiction] # Konflikte die nicht aufgelöst werden konnten
    confidence: float                         # Gesamt-Konfidenz der Synthese (0-1)
    reasoning: str                            # LLM Begründung der Synthese
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_complete(self) -> bool:
        """Prüft ob alle Widersprüche aufgelöst wurden"""
        return len(self.unresolved_conflicts) == 0
    
    def get_summary(self) -> str:
        """Kurze Zusammenfassung der Synthese"""
        resolved = len(self.contradictions) - len(self.unresolved_conflicts)
        return (f"Dialektische Synthese: {len(self.theses)} Thesen, "
                f"{len(self.contradictions)} Widersprüche ({resolved} aufgelöst), "
                f"Konfidenz: {self.confidence:.2f}")
    
    def get_critical_unresolved(self) -> List[Contradiction]:
        """Gibt kritische unaufgelöste Widersprüche zurück"""
        return [c for c in self.unresolved_conflicts 
                if c.severity == ContradictionSeverity.CRITICAL]
    
    def to_dict(self) -> dict:
        """Serialisiert DialecticalSynthesis für JSON"""
        return {
            'theses': [t.to_dict() for t in self.theses],
            'contradictions': [c.to_dict() for c in self.contradictions],
            'synthesis_text': self.synthesis_text,
            'resolution_strategies': [s.value for s in self.resolution_strategies],
            'unresolved_conflicts': [c.to_dict() for c in self.unresolved_conflicts],
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp,
            'summary': self.get_summary(),
            'is_complete': self.is_complete(),
            'critical_unresolved_count': len(self.get_critical_unresolved()),
            'metadata': self.metadata
        }


# Helper-Funktionen

def create_thesis_from_dict(data: dict) -> Thesis:
    """Erstellt Thesis aus Dictionary (z.B. von LLM-Response)"""
    return Thesis(
        agent_source=data['agent_source'],
        claim=data['claim'],
        evidence=data.get('evidence', []),
        confidence=data.get('confidence', 0.5),
        legal_basis=data.get('legal_basis'),
        context=data.get('context'),
        metadata=data.get('metadata', {})
    )


def create_contradiction_from_dict(data: dict, theses: List[Thesis]) -> Contradiction:
    """Erstellt Contradiction aus Dictionary"""
    thesis_a_idx = data.get('thesis_a_index', 0)
    thesis_b_idx = data.get('thesis_b_index', 1)
    
    return Contradiction(
        thesis_a=theses[thesis_a_idx] if thesis_a_idx < len(theses) else theses[0],
        thesis_b=theses[thesis_b_idx] if thesis_b_idx < len(theses) else theses[-1],
        contradiction_type=ContradictionType(data['contradiction_type']),
        severity=ContradictionSeverity(data['severity']),
        description=data['description'],
        potential_resolutions=data.get('potential_resolutions', []),
        metadata=data.get('metadata', {})
    )
