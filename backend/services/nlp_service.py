#!/usr/bin/env python3
"""
NLP Service for VERITAS Phase 1
================================
Natural Language Processing service for query analysis.

Features:
- Entity extraction (regex-based)
- Intent detection (keyword-based)
- Parameter extraction
- Question type classification

Author: VERITAS Phase 1
Date: 2025-10-14
"""

import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.models.nlp_models import Entity, EntityType, Intent, IntentType, NLPAnalysisResult, QueryParameters, QuestionType

logger = logging.getLogger(__name__)


class NLPService:
    """
    NLP Service for query analysis.

    Uses regex-based entity extraction and keyword-based intent detection.
    No external dependencies (spaCy optional for future).

    Example:
        >>> nlp = NLPService()
        >>> result = nlp.analyze("Bauantrag für Einfamilienhaus in Stuttgart")
        >>> print(result.intent.intent_type)  # PROCEDURE_QUERY
        >>> print(result.entities[0].text)    # Stuttgart
    """

    def __init__(self):
        """Initialize NLP Service with keyword patterns"""

        # Intent detection patterns
        self.intent_patterns = {
            IntentType.FACT_RETRIEVAL: [
                r"\b(was ist|was sind|wer ist|wer sind)\b",
                r"\b(hauptsitz|adresse|standort|sitz)\b",
                r"\b(definition|bedeutet|erkläre|erklären)\b",
            ],
            IntentType.PROCEDURE_QUERY: [
                r"\b(wie beantrage|antrag|anmeldung|genehmigung)\b",
                r"\b(verfahren|prozess|ablauf|schritte)\b",
                r"\b(bauantrag|baugenehmigung|bauvoranfrage)\b",
                r"\b(welche unterlagen|welche dokumente)\b",
            ],
            IntentType.COMPARISON: [
                r"\b(unterschied|vergleich|vergleichen)\b",
                r"\b(vs\.|versus|oder)\b",
                r"\b(besser|schlechter|günstiger)\b",
            ],
            IntentType.TIMELINE: [
                r"\b(geschichte|entwicklung|zeitstrahl)\b",
                r"\b(seit wann|bis wann|zeitraum)\b",
                r"\b(chronologie|verlauf)\b",
            ],
            IntentType.CALCULATION: [
                r"\b(wie viel|kosten|preis|gebühr)\b",
                r"\b(berechne|rechne|kalkulation)\b",
                r"\b(€|euro|eur)\b",
            ],
            IntentType.LOCATION_QUERY: [
                r"\b(wo finde|wo ist|wo befindet)\b",
                r"\b(adresse|anfahrt|lage)\b",
                r"\b(öffnungszeiten|sprechzeiten)\b",
            ],
            IntentType.CONTACT_QUERY: [
                r"\b(kontakt|telefon|email|e - mail)\b",
                r"\b(ansprechpartner|zuständig)\b",
                r"\b(hotline|service)\b",
            ],
        }

        # Entity patterns
        self.entity_patterns = {
            # German cities (common ones)
            EntityType.LOCATION: [
                r"\b(Stuttgart|München|Berlin|Hamburg|Köln|Frankfurt|Düsseldorf|Dortmund|Essen|Leipzig|Bremen|Dresden|Hannover|Nürnberg|Duisburg|Bochum|Wuppertal|Bielefeld|Bonn|Münster|Karlsruhe|Mannheim|Augsburg|Wiesbaden|Mönchengladbach|Gelsenkirchen|Aachen|Braunschweig|Kiel|Chemnitz|Halle|Magdeburg|Freiburg|Krefeld|Mainz|Lübeck|Erfurt|Oberhausen|Rostock|Kassel|Hagen|Potsdam|Saarbrücken|Hamm|Ludwigshafen|Oldenburg|Osnabrück|Leverkusen|Heidelberg|Solingen|Herne|Neuss|Regensburg|Paderborn|Ingolstadt|Würzburg|Fürth|Wolfsburg|Ulm|Heilbronn|Pforzheim|Göttingen|Bottrop|Reutlingen|Koblenz|Bremerhaven|Bergisch Gladbach|Jena|Remscheid|Erlangen|Moers|Siegen|Hildesheim|Salzgitter)\b",
                r"\b(in|nach|von|aus)\s + ([A-ZÄÖÜ][a - zäöüß]+)\b",  # Generic city pattern
            ],
            # Organizations
            EntityType.ORGANIZATION: [
                r"\b(BMW|Daimler|Volkswagen|Siemens|Bosch|BASF|Bayer|Deutsche Bank|Allianz)\b",
                r"\b(Rathaus|Bürgerbüro|Landratsamt|Finanzamt|Arbeitsamt|Jobcenter|Bauamt|Ordnungsamt|Standesamt)\b",
                r"\b(GmbH|AG|UG|e\.V\.|KG|OHG)\b",
            ],
            # Documents
            EntityType.DOCUMENT: [
                r"\b(Bauantrag|Baugenehmigung|Bauvoranfrage|Personalausweis|Reisepass|Führerschein|Geburtsurkunde|Heiratsurkunde|Sterbeurkunde|Meldebescheinigung|Aufenthaltsgenehmigung|Visum|Zulassung|Abmeldung|Anmeldung)\b",
                r"\b(Formular|Antrag|Bescheinigung|Nachweis|Urkunde|Dokument)\b",
            ],
            # Procedures
            EntityType.PROCEDURE: [
                r"\b(Anmeldung|Abmeldung|Ummeldung|Beantragung|Genehmigung|Zulassung|Registrierung|Prüfung|Beschaffung)\b",
            ],
            # Laws
            EntityType.LAW: [
                r"\b(DSGVO|BGB|StGB|StVO|HGB|GG|AO|SGB|BauGB|BauO|GewO)\b",
                r"\b(Artikel\s + \d+|Art\.\s * \d+|§\s * \d+|Paragraph\s + \d+)\b",
            ],
            # Amounts
            EntityType.AMOUNT: [
                r"\b(\d + (?:[.,]\d+)?)\s * (?:€|EUR|Euro)\b",
                r"\b(\d + (?:[.,]\d+)?)\s * (?:km|m|cm|kg|g|Liter|l)\b",
            ],
            # Dates
            EntityType.DATE: [
                r"\b(\d{1,2}\.\d{1,2}\.\d{2,4})\b",  # 01.01.2025
                r"\b(heute|morgen|gestern|übermorgen)\b",
                r"\b(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}\b",
            ],
        }

        # Question type patterns
        self.question_patterns = {
            QuestionType.WHAT: r"^\s * (was|welche|welcher|welches)\b",
            QuestionType.WHO: r"^\s * wer\b",
            QuestionType.WHERE: r"^\s * wo\b",
            QuestionType.WHEN: r"^\s * wann\b",
            QuestionType.HOW: r"^\s * wie\b",
            QuestionType.WHY: r"^\s * (warum|wieso|weshalb)\b",
            QuestionType.WHICH: r"^\s * welche[rs]?\b",
            QuestionType.HOW_MUCH: r"^\s * wie\s+(viel|viele|oft)\b",
        }

        logger.info("✅ NLPService initialized")

    def analyze(self, query: str) -> NLPAnalysisResult:
        """
        Complete NLP analysis of query.

        Args:
            query: User query string

        Returns:
            NLPAnalysisResult with all extracted information
        """
        logger.info(f"🔍 Analyzing query: {query}")

        # Extract components
        entities = self.extract_entities(query)
        intent = self.detect_intent(query, entities)
        parameters = self.extract_parameters(query, entities)
        question_type = self.classify_question_type(query)
        tokens = self._tokenize(query)

        result = NLPAnalysisResult(
            query=query,
            intent=intent,
            entities=entities,
            parameters=parameters,
            question_type=question_type,
            language="de",
            tokens=tokens,
        )

        logger.info(f"✅ Analysis complete: Intent={intent.intent_type.value}, Entities={len(entities)}")
        return result

    def extract_entities(self, query: str) -> List[Entity]:
        """
        Extract named entities from query using regex patterns.

        Args:
            query: User query string

        Returns:
            List of extracted entities
        """
        entities = []
        query_lower = query.lower()

        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    text = match.group(0).strip()
                    # Skip very short matches or common words
                    if len(text) < 2:
                        continue

                    entity = Entity(
                        text=text,
                        entity_type=entity_type,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.8,  # Regex-based, medium confidence
                    )
                    entities.append(entity)

        # Remove duplicates (keep highest confidence)
        unique_entities = {}
        for entity in entities:
            key = (entity.text.lower(), entity.entity_type)
            if key not in unique_entities or entity.confidence > unique_entities[key].confidence:
                unique_entities[key] = entity

        return list(unique_entities.values())

    def detect_intent(self, query: str, entities: List[Entity] = None) -> Intent:
        """
        Detect query intent using keyword matching.

        Args:
            query: User query string
            entities: Optional pre-extracted entities for context

        Returns:
            Intent with type and confidence
        """
        query_lower = query.lower()
        intent_scores: Dict[IntentType, Tuple[float, List[str]]] = {}

        # Score each intent type
        for intent_type, patterns in self.intent_patterns.items():
            matched_keywords = []
            score = 0.0

            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    score += 1.0
                    matched_keywords.append(match.group(0))

            if score > 0:
                # Normalize score
                confidence = min(score / len(patterns), 1.0)
                intent_scores[intent_type] = (confidence, matched_keywords)

        # Select best intent
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1][0])
            return Intent(intent_type=best_intent[0], confidence=best_intent[1][0], keywords=best_intent[1][1])
        else:
            # Default: FACT_RETRIEVAL for questions, UNKNOWN for others
            if any(q in query_lower for q in ["was", "wer", "wo", "wann", "wie", "warum"]):
                return Intent(intent_type=IntentType.FACT_RETRIEVAL, confidence=0.5, keywords=[])
            else:
                return Intent(intent_type=IntentType.UNKNOWN, confidence=0.3, keywords=[])

    def extract_parameters(self, query: str, entities: List[Entity] = None) -> QueryParameters:
        """
        Extract structured parameters from query.

        Args:
            query: User query string
            entities: Optional pre-extracted entities

        Returns:
            QueryParameters with extracted values
        """
        if entities is None:
            entities = self.extract_entities(query)

        params = QueryParameters()

        # Extract by entity type
        for entity in entities:
            if entity.entity_type == EntityType.LOCATION and not params.location:
                params.location = entity.text
            elif entity.entity_type == EntityType.ORGANIZATION and not params.organization:
                params.organization = entity.text
            elif entity.entity_type == EntityType.DOCUMENT and not params.document_type:
                params.document_type = entity.text
            elif entity.entity_type == EntityType.PROCEDURE and not params.procedure_type:
                params.procedure_type = entity.text
            elif entity.entity_type == EntityType.DATE and not params.date:
                params.date = entity.text
            elif entity.entity_type == EntityType.AMOUNT and not params.amount:
                params.amount = entity.text
            else:
                # Store in custom dict
                key = f"{entity.entity_type.value}_{len(params.custom)}"
                params.custom[key] = entity.text

        return params

    def classify_question_type(self, query: str) -> QuestionType:
        """
        Classify question type from query.

        Args:
            query: User query string

        Returns:
            QuestionType enum value
        """
        query_lower = query.lower().strip()

        for q_type, pattern in self.question_patterns.items():
            if re.match(pattern, query_lower):
                return q_type

        # Default: STATEMENT (not a question)
        return QuestionType.STATEMENT

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization (split by whitespace and punctuation).

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        # Split by whitespace and punctuation
        tokens = re.findall(r"\b\w+\b", text, re.UNICODE)
        return tokens


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    nlp = NLPService()

    # Test queries
    test_queries = [
        "Was ist der Hauptsitz von BMW?",
        "Bauantrag für Einfamilienhaus in Stuttgart",
        "Wie viel kostet ein Bauantrag?",
        "Unterschied zwischen GmbH und AG",
        "Kontakt Bauamt München",
        "Wo finde ich das Bürgerbüro?",
    ]

    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"Query: {query}")
        print("=" * 60)
        result = nlp.analyze(query)
        print(result)
