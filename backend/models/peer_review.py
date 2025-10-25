"""
Datenmodelle für Multi-LLM Peer-Review Validation

Peer-Review ist der Gold-Standard wissenschaftlicher Qualitätssicherung:
- Mehrere unabhängige Experten bewerten eine Arbeit
- Konsens erhöht Vertrauenswürdigkeit
- Bias einzelner Reviewer wird minimiert

Anwendung in VERITAS:
- Peers = Verschiedene LLM-Modelle (llama3.1, mixtral, gemma3)
- Review = Validierung der Final Response
- Consensus = Mindestens 2/3 Zustimmung erforderlich
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime, timezone


class ReviewRecommendation(Enum):
    """Reviewer-Empfehlung nach Bewertung"""
    APPROVE = "approve"          # Antwort ist gut, keine Änderungen nötig
    REVISE = "revise"            # Überarbeitung empfohlen
    REJECT = "reject"            # Antwort nicht akzeptabel


class ApprovalStatus(Enum):
    """Gesamt-Status nach Peer-Review"""
    APPROVED = "approved"        # >= 2/3 Zustimmung (oder konfigurierter Threshold)
    CONDITIONAL = "conditional"  # Mehrheit positiv, aber mit Vorbehalten
    REJECTED = "rejected"        # < 2/3 Zustimmung


@dataclass
class ReviewCriteria:
    """Einzelnes Bewertungs-Kriterium für Peer-Review"""
    name: str                   # Name des Kriteriums (z.B. "factual_accuracy")
    weight: float               # Gewichtung (sum aller criteria = 1.0)
    description: str            # Beschreibung was bewertet wird
    score: float                # Score 0-10
    comments: str               # Begründung für Score
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'weight': self.weight,
            'description': self.description,
            'score': self.score,
            'comments': self.comments
        }


@dataclass
class Review:
    """
    Einzelnes LLM-Review
    
    Ein unabhängiges Review eines LLM-Modells mit detaillierten
    Bewertungen nach definierten Kriterien und finaler Empfehlung.
    """
    reviewer_model: str                     # LLM-Modell (z.B. "llama3.1:8b")
    reviewer_description: str               # Beschreibung des Reviewers
    overall_score: float                    # Gesamt-Score (0-10)
    criteria_scores: Dict[str, ReviewCriteria]  # Detaillierte Kriterien
    strengths: List[str]                    # Was ist gut?
    weaknesses: List[str]                   # Was fehlt/ist falsch?
    recommendation: ReviewRecommendation    # Empfehlung
    detailed_comments: str                  # Ausführliche Begründung
    review_timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_weighted_score(self) -> float:
        """Berechnet gewichteten Gesamt-Score aus Kriterien"""
        total = 0.0
        for criterion in self.criteria_scores.values():
            total += criterion.score * criterion.weight
        return total
    
    def __str__(self) -> str:
        return (f"Review von {self.reviewer_model}: {self.overall_score:.1f}/10 "
                f"({self.recommendation.value})")
    
    def to_dict(self) -> dict:
        """Serialisiert Review für JSON"""
        return {
            'reviewer_model': self.reviewer_model,
            'reviewer_description': self.reviewer_description,
            'overall_score': self.overall_score,
            'weighted_score': self.get_weighted_score(),
            'criteria_scores': {k: v.to_dict() for k, v in self.criteria_scores.items()},
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'recommendation': self.recommendation.value,
            'detailed_comments': self.detailed_comments,
            'review_timestamp': self.review_timestamp,
            'metadata': self.metadata
        }


@dataclass
class ReviewConflict:
    """
    Uneinigkeit zwischen Reviewern
    
    Identifiziert wo Reviewer stark unterschiedliche Bewertungen haben.
    Wichtig für Conflict Resolution und Transparenz.
    """
    criterion: str                  # Bei welchem Kriterium?
    reviewer_a: str                 # Erster Reviewer
    score_a: float                  # Score von Reviewer A
    comments_a: str                 # Begründung A
    reviewer_b: str                 # Zweiter Reviewer
    score_b: float                  # Score von Reviewer B
    comments_b: str                 # Begründung B
    difference: float               # Absolute Differenz
    
    def is_significant(self, threshold: float = 3.0) -> bool:
        """
        Prüft ob Differenz signifikant ist
        
        Args:
            threshold: Ab welcher Differenz gilt es als signifikant (default: 3.0 Punkte)
        """
        return abs(self.difference) >= threshold
    
    def __str__(self) -> str:
        return (f"Konflikt bei '{self.criterion}': "
                f"{self.reviewer_a} ({self.score_a:.1f}) vs "
                f"{self.reviewer_b} ({self.score_b:.1f}) "
                f"[Δ={abs(self.difference):.1f}]")
    
    def to_dict(self) -> dict:
        return {
            'criterion': self.criterion,
            'reviewer_a': self.reviewer_a,
            'score_a': self.score_a,
            'comments_a': self.comments_a,
            'reviewer_b': self.reviewer_b,
            'score_b': self.score_b,
            'comments_b': self.comments_b,
            'difference': abs(self.difference),
            'is_significant': self.is_significant()
        }


@dataclass
class PeerReviewResult:
    """
    Gesamt-Ergebnis des Multi-LLM Peer-Reviews
    
    Aggregiert alle Reviews, berechnet Consensus und gibt
    finales Urteil ab basierend auf definierten Schwellwerten.
    """
    reviews: List[Review]                       # Alle Einzelreviews
    consensus_score: float                      # 0-1 (Übereinstimmung der Reviewer)
    average_score: float                        # Durchschnitt aller Scores (0-10)
    approval_status: ApprovalStatus             # Finaler Status
    conflicts: List[ReviewConflict]             # Signifikante Uneinigkeiten
    final_verdict: str                          # Zusammenfassende Bewertung
    confidence: float                           # Konfidenz des Reviews (0-1)
    recommendations: List[str]                  # Verbesserungsvorschläge
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_approval_rate(self) -> float:
        """Berechnet Anteil der Approve-Empfehlungen (0-1)"""
        if not self.reviews:
            return 0.0
        approvals = sum(1 for r in self.reviews if r.recommendation == ReviewRecommendation.APPROVE)
        return approvals / len(self.reviews)
    
    def get_rejection_rate(self) -> float:
        """Berechnet Anteil der Reject-Empfehlungen (0-1)"""
        if not self.reviews:
            return 0.0
        rejections = sum(1 for r in self.reviews if r.recommendation == ReviewRecommendation.REJECT)
        return rejections / len(self.reviews)
    
    def get_significant_conflicts(self, threshold: float = 3.0) -> List[ReviewConflict]:
        """Gibt nur signifikante Konflikte zurück"""
        return [c for c in self.conflicts if c.is_significant(threshold)]
    
    def get_summary(self) -> str:
        """Kurze Zusammenfassung"""
        approval_rate = self.get_approval_rate()
        return (f"Peer-Review: {len(self.reviews)} Reviewer, "
                f"Consensus: {self.consensus_score:.2f}, "
                f"Avg Score: {self.average_score:.1f}/10, "
                f"Approval: {approval_rate:.0%} ({self.approval_status.value})")
    
    def to_dict(self) -> dict:
        """Serialisiert PeerReviewResult für JSON"""
        return {
            'reviews': [r.to_dict() for r in self.reviews],
            'consensus_score': self.consensus_score,
            'average_score': self.average_score,
            'approval_status': self.approval_status.value,
            'conflicts': [c.to_dict() for c in self.conflicts],
            'significant_conflicts_count': len(self.get_significant_conflicts()),
            'final_verdict': self.final_verdict,
            'confidence': self.confidence,
            'recommendations': self.recommendations,
            'approval_rate': self.get_approval_rate(),
            'rejection_rate': self.get_rejection_rate(),
            'summary': self.get_summary(),
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


# Standard-Kriterien für Reviews
DEFAULT_REVIEW_CRITERIA = {
    'factual_accuracy': {
        'weight': 0.30,
        'description': 'Faktentreue: Stimmen alle Fakten? Gibt es falsche oder irreführende Aussagen?'
    },
    'completeness': {
        'weight': 0.25,
        'description': 'Vollständigkeit: Wurde die Frage vollständig beantwortet? Fehlen wichtige Aspekte?'
    },
    'legal_compliance': {
        'weight': 0.20,
        'description': 'Rechtskonformität: Sind Rechtsgrundlagen korrekt zitiert? Stimmen Paragraphen und Fristen?'
    },
    'coherence': {
        'weight': 0.15,
        'description': 'Kohärenz: Ist die Antwort logisch kohärent ohne innere Widersprüche?'
    },
    'source_coverage': {
        'weight': 0.10,
        'description': 'Quellenabdeckung: Wurden alle relevanten Quellen und Perspektiven berücksichtigt?'
    }
}

# Alternative Kriterien-Sets für unterschiedliche Domänen
LEGAL_DOMAIN_CRITERIA = {
    'legal_accuracy': {
        'weight': 0.40,
        'description': 'Rechtliche Korrektheit: Korrekte Zitierung von Gesetzen, Verordnungen, Rechtsprechung'
    },
    'completeness': {
        'weight': 0.25,
        'description': 'Vollständigkeit: Alle relevanten Rechtsnormen berücksichtigt'
    },
    'applicability': {
        'weight': 0.20,
        'description': 'Anwendbarkeit: Ist die Antwort auf den konkreten Fall anwendbar?'
    },
    'clarity': {
        'weight': 0.15,
        'description': 'Klarheit: Verständliche Formulierung für Nicht-Juristen'
    }
}

TECHNICAL_DOMAIN_CRITERIA = {
    'technical_accuracy': {
        'weight': 0.35,
        'description': 'Technische Korrektheit: Fachlich richtige Aussagen'
    },
    'practical_applicability': {
        'weight': 0.30,
        'description': 'Praktische Anwendbarkeit: Umsetzbare Empfehlungen'
    },
    'safety_compliance': {
        'weight': 0.20,
        'description': 'Sicherheit: Einhaltung von Sicherheitsstandards'
    },
    'completeness': {
        'weight': 0.15,
        'description': 'Vollständigkeit: Alle relevanten Aspekte abgedeckt'
    }
}


# Helper-Funktionen

def calculate_consensus_score(reviews: List[Review]) -> float:
    """
    Berechnet Consensus-Score basierend auf Score-Varianz
    
    Je näher die Scores beieinander liegen, desto höher der Consensus.
    Returns: 0-1 (0 = keine Einigkeit, 1 = perfekte Einigkeit)
    """
    if not reviews or len(reviews) < 2:
        return 1.0  # Ein Review = perfekter Consensus mit sich selbst
    
    scores = [r.overall_score for r in reviews]
    mean_score = sum(scores) / len(scores)
    
    # Berechne Standardabweichung
    variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
    std_dev = variance ** 0.5
    
    # Normalisiere auf 0-1 (10 Punkte Differenz = 0 Consensus)
    consensus = max(0.0, 1.0 - (std_dev / 10.0))
    return consensus


def determine_approval_status(reviews: List[Review], min_consensus: float = 0.67) -> ApprovalStatus:
    """
    Bestimmt Approval-Status basierend auf Reviews
    
    Args:
        reviews: Liste von Reviews
        min_consensus: Mindest-Zustimmungsrate für Approval (default: 2/3)
    
    Returns:
        ApprovalStatus (APPROVED, CONDITIONAL, REJECTED)
    """
    if not reviews:
        return ApprovalStatus.REJECTED
    
    approval_rate = sum(1 for r in reviews if r.recommendation == ReviewRecommendation.APPROVE) / len(reviews)
    rejection_rate = sum(1 for r in reviews if r.recommendation == ReviewRecommendation.REJECT) / len(reviews)
    
    # Mehrheit lehnt ab
    if rejection_rate > 0.5:
        return ApprovalStatus.REJECTED
    
    # Ausreichend Zustimmung
    if approval_rate >= min_consensus:
        return ApprovalStatus.APPROVED
    
    # Mehrheit positiv aber unter Threshold
    if approval_rate > rejection_rate:
        return ApprovalStatus.CONDITIONAL
    
    # Keine klare Mehrheit
    return ApprovalStatus.CONDITIONAL


def identify_conflicts(reviews: List[Review], threshold: float = 3.0) -> List[ReviewConflict]:
    """
    Identifiziert signifikante Konflikte zwischen Reviewern
    
    Args:
        reviews: Liste von Reviews
        threshold: Ab welcher Score-Differenz gilt es als Konflikt
    
    Returns:
        Liste von ReviewConflict-Objekten
    """
    conflicts = []
    
    # Vergleiche alle Review-Paare
    for i in range(len(reviews)):
        for j in range(i + 1, len(reviews)):
            review_a = reviews[i]
            review_b = reviews[j]
            
            # Prüfe jeden Kriteriums-Score
            for criterion_name in review_a.criteria_scores.keys():
                if criterion_name not in review_b.criteria_scores:
                    continue
                
                score_a = review_a.criteria_scores[criterion_name].score
                score_b = review_b.criteria_scores[criterion_name].score
                diff = score_a - score_b
                
                if abs(diff) >= threshold:
                    conflict = ReviewConflict(
                        criterion=criterion_name,
                        reviewer_a=review_a.reviewer_model,
                        score_a=score_a,
                        comments_a=review_a.criteria_scores[criterion_name].comments,
                        reviewer_b=review_b.reviewer_model,
                        score_b=score_b,
                        comments_b=review_b.criteria_scores[criterion_name].comments,
                        difference=diff
                    )
                    conflicts.append(conflict)
    
    return conflicts
