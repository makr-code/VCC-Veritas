# 🔬 Dialektische Synthese & Peer-Review - Implementierungsplan

**Version:** 1.0.0  
**Datum:** 16. Oktober 2025  
**Status:** 🔄 In Arbeit  
**Priorität:** 🔥 Hoch (Wissenschaftliche Methode vervollständigen)

---

## 🎯 Ziel

Erweitere VERITAS um zwei wissenschaftliche Methoden:

1. **Dialektische Synthese** (Thesis-Antithesis-Synthesis)
   - Extrahiere Kern-Aussagen aus Agent-Results
   - Identifiziere Widersprüche zwischen Perspektiven
   - Löse Widersprüche auf höherer Abstraktionsebene auf

2. **Peer-Review Validation** (Multi-LLM Consensus)
   - 3 verschiedene LLMs bewerten Final Response unabhängig
   - Berechne Consensus (0-1)
   - Approve/Conditional/Reject basierend auf Übereinstimmung

---

## 📋 Implementierungs-Reihenfolge

### Phase 1: Datenmodelle & Services (2-3h)
- [ ] 1.1 Dialektische Datenmodelle erstellen
- [ ] 1.2 Peer-Review Datenmodelle erstellen
- [ ] 1.3 DialecticalSynthesisService implementieren
- [ ] 1.4 PeerReviewValidationService implementieren

### Phase 2: LLM-Prompts (1-2h)
- [ ] 2.1 Thesis Extraction Prompt
- [ ] 2.2 Contradiction Detection Prompt
- [ ] 2.3 Dialectical Synthesis Prompt
- [ ] 2.4 Peer-Review Prompt

### Phase 3: Pipeline-Integration (2h)
- [ ] 3.1 Dialektische Synthese nach Agent-Execution
- [ ] 3.2 Peer-Review nach Synthese
- [ ] 3.3 Feature-Flag VERITAS_SCIENTIFIC_MODE
- [ ] 3.4 Progress-Events für neue Stages

### Phase 4: Testing & Dokumentation (1-2h)
- [ ] 4.1 Unit-Tests für Services
- [ ] 4.2 Integration-Tests mit Mock-Agents
- [ ] 4.3 Performance-Messung
- [ ] 4.4 API-Dokumentation

**Geschätzte Gesamtzeit:** 6-9 Stunden

---

## 📂 Dateistruktur

```
backend/
├── models/
│   ├── dialectical_synthesis.py    # NEU: Thesis, Contradiction, DialecticalSynthesis
│   └── peer_review.py              # NEU: Review, ReviewConflict, PeerReviewResult
├── services/
│   ├── dialectical_synthesis_service.py  # NEU: Dialektische Synthese
│   └── peer_review_service.py            # NEU: Multi-LLM Peer-Review
├── prompts/
│   ├── thesis_extraction_prompt.txt      # NEU
│   ├── contradiction_detection_prompt.txt # NEU
│   ├── dialectical_synthesis_prompt.txt   # NEU
│   └── peer_review_prompt.txt            # NEU
└── api/
    └── veritas_api_backend.py       # MODIFY: Integration in _process_streaming_query()

config/
└── config.py                        # MODIFY: Feature-Flags

tests/
├── test_dialectical_synthesis.py   # NEU
└── test_peer_review.py             # NEU

docs/
├── DIALEKTISCHE_SYNTHESE_PEER_REVIEW.md  # Dieses Dokument
└── WISSENSCHAFTLICHES_PIPELINE_KONZEPT_STATUS.md  # UPDATED
```

---

## 🔧 Detaillierte Implementation

### 1.1 Dialektische Datenmodelle

**Datei:** `backend/models/dialectical_synthesis.py`

```python
"""
Datenmodelle für Dialektische Synthese (Thesis-Antithesis-Synthesis)
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class ContradictionType(Enum):
    """Art des Widerspruchs"""
    LEGAL = "legal"              # Unterschiedliche Rechtsauslegung
    FACTUAL = "factual"          # Unterschiedliche Fakten
    TEMPORAL = "temporal"        # Unterschiedliche Zeiträume
    REGIONAL = "regional"        # Unterschiedliche Regionen/Zuständigkeiten
    METHODOLOGICAL = "methodological"  # Unterschiedliche Ansätze

class ContradictionSeverity(Enum):
    """Schwere des Widerspruchs"""
    CRITICAL = "critical"        # Fundamentaler Widerspruch
    MODERATE = "moderate"        # Teilweise inkonsistent
    MINOR = "minor"              # Nur unterschiedliche Nuancen

class ResolutionStrategy(Enum):
    """Strategie zur Widerspruchs-Auflösung"""
    CONTEXTUALIZATION = "contextualization"  # Beide richtig in unterschiedlichen Kontexten
    HIERARCHIZATION = "hierarchization"      # Eine Quelle ist autoritativer
    SYNTHESIS = "synthesis"                  # Beide enthalten Teilwahrheiten
    TEMPORAL_ORDERING = "temporal_ordering"  # Zeitliche Abfolge löst auf
    REGIONAL_DIFFERENTIATION = "regional"    # Regional unterschiedliche Regeln

@dataclass
class Thesis:
    """
    Kern-Aussage aus Agent-Result
    
    Eine These ist eine extrahierte Behauptung/Position eines Agents
    mit Belegen und Konfidenz.
    """
    agent_source: str                    # Welcher Agent (z.B. "VerwaltungsrechtAgent")
    claim: str                           # Die Kern-Behauptung
    evidence: List[str]                  # Belege/Zitate
    confidence: float                    # Agent-Konfidenz (0-1)
    legal_basis: Optional[List[str]]     # Rechtsgrundlagen (z.B. ["§10 BauGB", "Art. 59 BayBO"])
    context: Optional[str]               # Kontext der Aussage
    
    def __str__(self) -> str:
        return f"[{self.agent_source}] {self.claim} (Konfidenz: {self.confidence:.2f})"

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
    description: str                     # Was widerspricht sich?
    potential_resolutions: List[str]     # Mögliche Auflösungen
    
    def __str__(self) -> str:
        return (f"WIDERSPRUCH ({self.severity.value}): "
                f"{self.thesis_a.agent_source} vs {self.thesis_b.agent_source} - "
                f"{self.description}")

@dataclass
class DialecticalSynthesis:
    """
    Ergebnis der dialektischen Synthese
    
    Die Synthese auf höherer Ebene, die Widersprüche auflöst
    und eine kohärente Gesamt-Aussage bildet.
    """
    theses: List[Thesis]                      # Alle extrahierten Thesen
    contradictions: List[Contradiction]        # Identifizierte Widersprüche
    synthesis_text: str                        # Aufgelöste kohärente Antwort
    resolution_strategies: List[ResolutionStrategy]  # Verwendete Auflösungs-Strategien
    unresolved_conflicts: List[Contradiction]  # Konflikte die nicht aufgelöst werden konnten
    confidence: float                          # Gesamt-Konfidenz der Synthese (0-1)
    reasoning: str                             # LLM Begründung der Synthese
    metadata: dict                             # Zusätzliche Metadaten
    
    def is_complete(self) -> bool:
        """Prüft ob alle Widersprüche aufgelöst wurden"""
        return len(self.unresolved_conflicts) == 0
    
    def get_summary(self) -> str:
        """Kurze Zusammenfassung der Synthese"""
        return (f"Dialektische Synthese: {len(self.theses)} Thesen, "
                f"{len(self.contradictions)} Widersprüche, "
                f"{len(self.unresolved_conflicts)} unaufgelöst, "
                f"Konfidenz: {self.confidence:.2f}")
```

---

### 1.2 Peer-Review Datenmodelle

**Datei:** `backend/models/peer_review.py`

```python
"""
Datenmodelle für Multi-LLM Peer-Review Validation
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class ReviewRecommendation(Enum):
    """Reviewer-Empfehlung"""
    APPROVE = "approve"          # Antwort ist gut
    REVISE = "revise"            # Überarbeitung nötig
    REJECT = "reject"            # Antwort nicht akzeptabel

class ApprovalStatus(Enum):
    """Gesamt-Status nach Peer-Review"""
    APPROVED = "approved"        # >= 2/3 Zustimmung
    CONDITIONAL = "conditional"  # Mehrheit, aber mit Vorbehalten
    REJECTED = "rejected"        # < 2/3 Zustimmung

@dataclass
class ReviewCriteria:
    """Bewertungs-Kriterien für Peer-Review"""
    name: str
    weight: float               # Gewichtung (sum = 1.0)
    description: str
    score: float                # 0-10
    comments: str               # Begründung

@dataclass
class Review:
    """
    Einzelnes LLM-Review
    
    Ein unabhängiges Review eines LLM-Modells mit detaillierten
    Bewertungen und Empfehlung.
    """
    reviewer_model: str                     # LLM-Modell (z.B. "llama3.1:8b")
    reviewer_description: str               # Beschreibung des Reviewers
    overall_score: float                    # Gesamt-Score (0-10)
    criteria_scores: Dict[str, ReviewCriteria]  # Detaillierte Kriterien
    strengths: List[str]                    # Was ist gut?
    weaknesses: List[str]                   # Was fehlt/ist falsch?
    recommendation: ReviewRecommendation    # Empfehlung
    detailed_comments: str                  # Ausführliche Begründung
    review_timestamp: str                   # Zeitstempel
    
    def get_weighted_score(self) -> float:
        """Berechnet gewichteten Gesamt-Score aus Kriterien"""
        total = 0.0
        for criterion in self.criteria_scores.values():
            total += criterion.score * criterion.weight
        return total
    
    def __str__(self) -> str:
        return (f"Review von {self.reviewer_model}: {self.overall_score:.1f}/10 "
                f"({self.recommendation.value})")

@dataclass
class ReviewConflict:
    """
    Uneinigkeit zwischen Reviewern
    
    Identifiziert wo Reviewer stark unterschiedliche Bewertungen haben.
    """
    criterion: str                  # Bei welchem Kriterium?
    reviewer_a: str
    score_a: float
    comments_a: str
    reviewer_b: str
    score_b: float
    comments_b: str
    difference: float               # Absolute Differenz
    
    def is_significant(self, threshold: float = 3.0) -> bool:
        """Prüft ob Differenz signifikant ist (>= threshold)"""
        return abs(self.difference) >= threshold
    
    def __str__(self) -> str:
        return (f"Konflikt bei '{self.criterion}': "
                f"{self.reviewer_a} ({self.score_a:.1f}) vs "
                f"{self.reviewer_b} ({self.score_b:.1f}) "
                f"[Δ={self.difference:.1f}]")

@dataclass
class PeerReviewResult:
    """
    Gesamt-Ergebnis des Multi-LLM Peer-Reviews
    
    Aggregiert alle Reviews, berechnet Consensus und gibt
    finales Urteil ab.
    """
    reviews: List[Review]                       # Alle Einzelreviews
    consensus_score: float                      # 0-1 (Übereinstimmung der Reviewer)
    average_score: float                        # Durchschnitt aller Scores (0-10)
    approval_status: ApprovalStatus             # Finaler Status
    conflicts: List[ReviewConflict]             # Signifikante Uneinigkeiten
    final_verdict: str                          # Zusammenfassende Bewertung
    confidence: float                           # Konfidenz des Reviews (0-1)
    recommendations: List[str]                  # Verbesserungsvorschläge
    metadata: dict                              # Zusätzliche Metadaten
    
    def get_approval_rate(self) -> float:
        """Berechnet Anteil der Approve-Empfehlungen"""
        approvals = sum(1 for r in self.reviews if r.recommendation == ReviewRecommendation.APPROVE)
        return approvals / len(self.reviews) if self.reviews else 0.0
    
    def get_summary(self) -> str:
        """Kurze Zusammenfassung"""
        approval_rate = self.get_approval_rate()
        return (f"Peer-Review: {len(self.reviews)} Reviewer, "
                f"Consensus: {self.consensus_score:.2f}, "
                f"Avg Score: {self.average_score:.1f}/10, "
                f"Approval: {approval_rate:.0%} ({self.approval_status.value})")


# Standard-Kriterien für Reviews
DEFAULT_REVIEW_CRITERIA = {
    'factual_accuracy': {
        'weight': 0.30,
        'description': 'Faktentreue: Stimmen alle Fakten? Gibt es falsche Aussagen?'
    },
    'completeness': {
        'weight': 0.25,
        'description': 'Vollständigkeit: Wurde die Frage vollständig beantwortet?'
    },
    'legal_compliance': {
        'weight': 0.20,
        'description': 'Rechtskonformität: Sind Rechtsgrundlagen korrekt zitiert?'
    },
    'coherence': {
        'weight': 0.15,
        'description': 'Kohärenz: Ist die Antwort logisch kohärent ohne Widersprüche?'
    },
    'source_coverage': {
        'weight': 0.10,
        'description': 'Quellenabdeckung: Wurden alle relevanten Quellen berücksichtigt?'
    }
}
```

---

## 📝 LLM-Prompts

### Thesis Extraction Prompt

**Datei:** `backend/prompts/thesis_extraction_prompt.txt`

```
Du bist ein wissenschaftlicher Analyst mit Expertise in der Extraktion von Kern-Aussagen aus komplexen Texten.

AUFGABE:
Extrahiere die Kern-Behauptungen (Thesen) aus folgenden Agent-Analysen. Jede These sollte eine klar formulierte Aussage mit Belegen sein.

AGENT-RESULTS:
{agent_results}

ANWEISUNGEN:
1. Identifiziere für jeden Agent die 1-3 wichtigsten Aussagen
2. Formuliere jede These als präzise, eigenständige Behauptung
3. Liste alle Belege/Zitate auf die die These stützen
4. Extrahiere Rechtsgrundlagen (Gesetze, Paragraphen, Verordnungen)
5. Bewerte die Stärke der These basierend auf Belegen (0-1)

FORMAT:
Gib JSON zurück mit folgendem Schema:

{
  "theses": [
    {
      "agent_source": "Name des Agents",
      "claim": "Die Kern-Behauptung in einem Satz",
      "evidence": ["Beleg 1", "Beleg 2", "..."],
      "confidence": 0.85,
      "legal_basis": ["§10 BauGB", "Art. 59 BayBO"],
      "context": "Kontext der Aussage (optional)"
    }
  ]
}

BEISPIEL:
Agent: VerwaltungsrechtAgent
Text: "Nach §10 BauGB ist für den Neubau eine Baugenehmigung erforderlich. Diese muss bei der zuständigen Bauaufsichtsbehörde beantragt werden..."

These:
{
  "agent_source": "VerwaltungsrechtAgent",
  "claim": "Für Neubauten ist eine Baugenehmigung nach §10 BauGB erforderlich",
  "evidence": [
    "§10 BauGB regelt Genehmigungspflicht",
    "Zuständigkeit liegt bei Bauaufsichtsbehörde"
  ],
  "confidence": 0.95,
  "legal_basis": ["§10 BauGB"],
  "context": "Genehmigungspflicht für Neubauvorhaben"
}

WICHTIG:
- Nur faktische Aussagen extrahieren, keine Spekulationen
- Bei widersprüchlichen Aussagen beide Thesen extrahieren
- Confidence basiert auf Stärke der Belege, nicht subjektiver Meinung
- Legal basis nur wenn explizit genannt

AGENT-RESULTS ZUM ANALYSIEREN:
{agent_results}

Gib NUR das JSON zurück, keine zusätzlichen Erklärungen.
```

---

### Contradiction Detection Prompt

**Datei:** `backend/prompts/contradiction_detection_prompt.txt`

```
Du bist ein kritischer Wissenschaftler mit Expertise in der Identifikation von logischen Widersprüchen und Inkonsistenzen.

AUFGABE:
Analysiere folgende Thesen auf Widersprüche, Inkonsistenzen und unvereinbare Aussagen.

THESEN:
{theses}

ANWEISUNGEN:
1. Vergleiche alle Thesen paarweise miteinander
2. Identifiziere direkte Widersprüche (A sagt X, B sagt ¬X)
3. Identifiziere Inkonsistenzen (A und B passen logisch nicht zusammen)
4. Identifiziere Mehrdeutigkeiten (A und B könnten beide stimmen, je nach Interpretation)
5. Kategorisiere jeden Widerspruch nach Typ und Schwere

WIDERSPRUCHS-TYPEN:
- legal: Unterschiedliche Rechtsauslegung
- factual: Unterschiedliche Fakten/Zahlen
- temporal: Unterschiedliche Zeiträume/Fristen
- regional: Unterschiedliche Regionen/Zuständigkeiten
- methodological: Unterschiedliche Ansätze/Methoden

SCHWEREGRADE:
- critical: Fundamentaler Widerspruch, der aufgelöst werden MUSS
- moderate: Teilweise inkonsistent, sollte geklärt werden
- minor: Nur unterschiedliche Nuancen, nicht problematisch

FORMAT:
Gib JSON zurück:

{
  "contradictions": [
    {
      "thesis_a_index": 0,
      "thesis_b_index": 1,
      "contradiction_type": "legal",
      "severity": "critical",
      "description": "Ausführliche Beschreibung des Widerspruchs",
      "potential_resolutions": [
        "Mögliche Auflösung 1",
        "Mögliche Auflösung 2"
      ]
    }
  ]
}

BEISPIEL:
These A: "Nach BayBO ist eine Baugenehmigung erforderlich"
These B: "Im vereinfachten Verfahren ist keine Baugenehmigung nötig"

Widerspruch:
{
  "thesis_a_index": 0,
  "thesis_b_index": 1,
  "contradiction_type": "legal",
  "severity": "moderate",
  "description": "Unterschiedliche Aussagen zur Genehmigungspflicht. These A gilt generell, These B gilt nur für vereinfachtes Verfahren nach Art. 59 BayBO.",
  "potential_resolutions": [
    "Kontextualisierung: Beide Thesen sind richtig in unterschiedlichen Verfahren",
    "Hierarchisierung: Art. 59 BayBO ist Spezialregelung zu allgemeiner Genehmigungspflicht"
  ]
}

WICHTIG:
- Nur echte Widersprüche identifizieren, nicht bloße unterschiedliche Perspektiven
- Bei regional unterschiedlichen Regeln: Typ "regional", nicht "legal"
- Bei zeitlichen Änderungen: Typ "temporal"
- Potential resolutions sollten konkret und umsetzbar sein

THESEN ZUM ANALYSIEREN:
{theses}

Gib NUR das JSON zurück.
```

---

(Fortsetzung in nächstem Teil...)

**DIESES DOKUMENT WIRD IN PHASE 1 WEITER AUSGEARBEITET**

---

## 🎯 Nächste Schritte

1. **Jetzt:** Dialektische Datenmodelle implementieren (`backend/models/dialectical_synthesis.py`)
2. **Dann:** Peer-Review Datenmodelle (`backend/models/peer_review.py`)
3. **Danach:** Services implementieren
4. **Zuletzt:** Pipeline-Integration

---

**Status:** 📝 Konzept & Modelle dokumentiert  
**Nächster Milestone:** Datenmodelle implementieren  
**Geschätzte Zeit bis Completion:** 6-9 Stunden
