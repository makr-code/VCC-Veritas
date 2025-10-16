#!/usr/bin/env python3
"""
NLP Data Models for VERITAS
============================
Data classes for NLP analysis results.

Author: VERITAS Phase 1
Date: 2025-10-14
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class IntentType(Enum):
    """Query intent types"""
    FACT_RETRIEVAL = "fact_retrieval"           # "Was ist der Hauptsitz von BMW?"
    PROCEDURE_QUERY = "procedure_query"         # "Wie beantrage ich einen Bauantrag?"
    COMPARISON = "comparison"                   # "Unterschied zwischen GmbH und AG?"
    TIMELINE = "timeline"                       # "Geschichte der EU"
    CALCULATION = "calculation"                 # "Wie viel kostet ein Bauantrag?"
    DEFINITION = "definition"                   # "Was bedeutet DSGVO?"
    LOCATION_QUERY = "location_query"           # "Wo finde ich das Bürgerbüro?"
    CONTACT_QUERY = "contact_query"             # "Kontakt Bauamt München"
    UNKNOWN = "unknown"                         # Fallback


class EntityType(Enum):
    """Entity types for named entity recognition"""
    LOCATION = "location"           # Stuttgart, München, Deutschland
    ORGANIZATION = "organization"   # BMW, Rathaus, Landratsamt
    PERSON = "person"              # Max Mustermann
    DATE = "date"                  # 01.01.2025, morgen
    AMOUNT = "amount"              # 500 Euro, 10 km
    DOCUMENT = "document"          # Bauantrag, Personalausweis
    PROCEDURE = "procedure"        # Anmeldung, Genehmigung
    LAW = "law"                    # DSGVO, BGB, StVO
    OTHER = "other"                # Fallback


@dataclass
class Entity:
    """Extracted entity from query"""
    text: str                      # Original text
    entity_type: EntityType        # Type of entity
    start_pos: int = 0            # Start position in query
    end_pos: int = 0              # End position in query
    confidence: float = 1.0       # Confidence score (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional info
    
    def __str__(self) -> str:
        return f"{self.entity_type.value}::{self.text}"


@dataclass
class Intent:
    """Detected query intent"""
    intent_type: IntentType        # Type of intent
    confidence: float              # Confidence score (0-1)
    keywords: List[str] = field(default_factory=list)  # Matched keywords
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional info
    
    def __str__(self) -> str:
        return f"{self.intent_type.value} ({self.confidence:.2%})"


@dataclass
class QueryParameters:
    """Extracted parameters from query"""
    location: Optional[str] = None         # Extracted location
    organization: Optional[str] = None     # Extracted organization
    document_type: Optional[str] = None    # Extracted document type
    procedure_type: Optional[str] = None   # Extracted procedure
    date: Optional[str] = None             # Extracted date
    amount: Optional[str] = None           # Extracted amount
    custom: Dict[str, Any] = field(default_factory=dict)  # Custom parameters
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        return {
            k: v for k, v in {
                'location': self.location,
                'organization': self.organization,
                'document_type': self.document_type,
                'procedure_type': self.procedure_type,
                'date': self.date,
                'amount': self.amount,
                **self.custom
            }.items() if v is not None
        }


class QuestionType(Enum):
    """Question type classification"""
    WHAT = "what"           # Was ist...
    WHO = "who"             # Wer ist...
    WHERE = "where"         # Wo ist/finde ich...
    WHEN = "when"           # Wann...
    HOW = "how"             # Wie...
    WHY = "why"             # Warum...
    WHICH = "which"         # Welche...
    HOW_MUCH = "how_much"   # Wie viel...
    STATEMENT = "statement" # No question word
    

@dataclass
class NLPAnalysisResult:
    """Complete NLP analysis result"""
    query: str                                  # Original query
    intent: Intent                              # Detected intent
    entities: List[Entity]                      # Extracted entities
    parameters: QueryParameters                 # Extracted parameters
    question_type: QuestionType                 # Question classification
    language: str = "de"                        # Detected language
    tokens: List[str] = field(default_factory=list)  # Tokenized query
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional info
    
    def __str__(self) -> str:
        return (
            f"NLPAnalysisResult(\n"
            f"  Query: {self.query}\n"
            f"  Intent: {self.intent}\n"
            f"  Entities: {[str(e) for e in self.entities]}\n"
            f"  Parameters: {self.parameters.to_dict()}\n"
            f"  Question Type: {self.question_type.value}\n"
            f")"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'query': self.query,
            'intent': {
                'type': self.intent.intent_type.value,
                'confidence': self.intent.confidence,
                'keywords': self.intent.keywords
            },
            'entities': [
                {
                    'text': e.text,
                    'type': e.entity_type.value,
                    'confidence': e.confidence
                } for e in self.entities
            ],
            'parameters': self.parameters.to_dict(),
            'question_type': self.question_type.value,
            'language': self.language,
            'tokens': self.tokens
        }


# Example usage for documentation
if __name__ == "__main__":
    # Example 1: Fact retrieval query
    result = NLPAnalysisResult(
        query="Was ist der Hauptsitz von BMW?",
        intent=Intent(
            intent_type=IntentType.FACT_RETRIEVAL,
            confidence=0.95,
            keywords=["Was", "ist", "Hauptsitz"]
        ),
        entities=[
            Entity(text="BMW", entity_type=EntityType.ORGANIZATION, confidence=0.98)
        ],
        parameters=QueryParameters(organization="BMW"),
        question_type=QuestionType.WHAT,
        tokens=["Was", "ist", "der", "Hauptsitz", "von", "BMW"]
    )
    
    print(result)
    print("\nJSON:", result.to_dict())
