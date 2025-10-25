#!/usr/bin/env python3
"""
Intent Classifier - Hybrid NLP + LLM Ansatz
============================================
Klassifiziert User-Intent für optimale Token-Budgets:
- QUICK_ANSWER: Fakten, kurze Antworten
- EXPLANATION: Erklärungen, "Wie funktioniert..."
- ANALYSIS: Vergleiche, Bewertungen
- RESEARCH: Tiefgehende Recherche, Multi-Aspekt-Analysen

Verwendet:
1. Rule-Based NLP (schnell, keine API-Calls)
2. LLM-basierte Klassifikation (präzise, bei Unsicherheit)

Author: VERITAS System
Date: 2025-10-17
"""

import re
from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class UserIntent(str, Enum):
    """User-Intent-Typen"""
    QUICK_ANSWER = "quick_answer"    # 0.5x Token-Weight
    EXPLANATION = "explanation"       # 1.0x Token-Weight
    ANALYSIS = "analysis"             # 1.5x Token-Weight
    RESEARCH = "research"             # 2.0x Token-Weight


@dataclass
class IntentPrediction:
    """Ergebnis der Intent-Klassifikation"""
    intent: UserIntent
    confidence: float  # 0.0 - 1.0
    method: str  # "rule_based", "llm", "hybrid"
    reasoning: str  # Begründung für Debugging


class RuleBasedIntentClassifier:
    """Schneller NLP-basierter Klassifikator ohne LLM"""
    
    # Pattern für QUICK_ANSWER (einfache Fragen)
    QUICK_PATTERNS = [
        r"^was ist (ein|eine|der|die|das)\s",
        r"^wer (ist|war)\s",
        r"^wo (ist|liegt|befindet)\s",
        r"^wann (ist|war|findet)\s",
        r"^welche[rs]?\s\w+\s(ist|sind|gibt)\s",
        r"^gibt es\s",
        r"^hat\s.{0,30}\s(ein|eine)\s",
        r"^definiere\s",
        r"^nenne\s",
        r"^liste\s",  # NEU: "Liste alle X auf"
        r"welche\s(behörde|behörden|stelle)\s",  # NEU: Zuständigkeitsfragen
    ]
    
    # Pattern für EXPLANATION (Erklärungen)
    EXPLANATION_PATTERNS = [
        r"wie\s(funktioniert|läuft|arbeitet|wird)",
        r"erkläre\s",
        r"erläutere\s",
        r"beschreibe\s",
        r"was bedeutet\s",  # NEU: Stärkere Gewichtung
        r"bedeutet\s.*\?",  # NEU: "Was bedeutet X?" am Ende
        r"was ist der unterschied zwischen",  # NEU: Unterschiedsfragen
        r"unterschied zwischen\s.*\?",  # NEU
        r"warum\s(ist|wird|muss|sollte)",
        r"weshalb\s",
        r"welche\s(schritte|voraussetzungen|bedingungen)",
        r"wie\s(kann|könnte|sollte)\s",
        r"welche\s(unterlagen|dokumente)\s",  # NEU: Dokumenten-Fragen
        r"wie\s(beantrage|gehe.*vor)\s",  # NEU: Prozessfragen
    ]
    
    # Pattern für ANALYSIS (Analysen, Vergleiche)
    ANALYSIS_PATTERNS = [
        r"(analysiere|untersuche|prüfe|bewerte)\s",
        r"vergleiche\s",
        r"unterschied zwischen\s",
        r"vor-?\s?und\s?nachteile",
        r"pros?\s?(and|und)\s?cons?",
        r"welche\s(aspekte|faktoren|auswirkungen)",
        r"inwiefern\s",
        r"evaluiere\s",
    ]
    
    # Pattern für RESEARCH (Komplexe Recherchen)
    RESEARCH_PATTERNS = [
        r"recherchiere\s",
        r"umfassende\s(analyse|untersuchung|darstellung)",
        r"alle\s(aspekte|dimensionen|bereiche)",
        r"folgende\s+aspekte",  # "analysiere folgende Aspekte"
        r"\d+\)\s+\w+.*\d+\)\s+\w+.*\d+\)",  # Listen mit 3+ Punkten
        r"sowohl.*als auch.*außerdem",
        r"rechtliche.*und.*finanzielle.*und",  # Mehrere Domänen
        r"detaillierte\s(übersicht|analyse)",
        r"mehrere\s(aspekte|bereiche|dimensionen)",
    ]
    
    # Keywords für Intent-Scoring
    DOMAIN_KEYWORDS = {
        "verwaltungsrecht", "baurecht", "umweltrecht", "genehmigung",
        "rechtlich", "gesetz", "verordnung", "vorschrift"
    }
    
    @classmethod
    def classify(cls, query: str) -> IntentPrediction:
        """
        Klassifiziert Intent basierend auf Regeln
        
        Args:
            query: User-Anfrage
            
        Returns:
            IntentPrediction mit Intent, Confidence, Methode
        """
        query_lower = query.lower().strip()
        
        # Score für jeden Intent
        scores = {
            UserIntent.QUICK_ANSWER: 0.0,
            UserIntent.EXPLANATION: 0.0,
            UserIntent.ANALYSIS: 0.0,
            UserIntent.RESEARCH: 0.0
        }
        
        # 1. Pattern-Matching
        for pattern in cls.QUICK_PATTERNS:
            if re.search(pattern, query_lower):
                scores[UserIntent.QUICK_ANSWER] += 2.0
                
        for pattern in cls.EXPLANATION_PATTERNS:
            if re.search(pattern, query_lower):
                scores[UserIntent.EXPLANATION] += 2.0
                
        for pattern in cls.ANALYSIS_PATTERNS:
            if re.search(pattern, query_lower):
                scores[UserIntent.ANALYSIS] += 2.0
                
        for pattern in cls.RESEARCH_PATTERNS:
            if re.search(pattern, query_lower):
                scores[UserIntent.RESEARCH] += 3.0  # Höhere Priorität für RESEARCH
        
        # 2. Längen-Heuristik
        query_length = len(query)
        if query_length < 50:
            scores[UserIntent.QUICK_ANSWER] += 1.0
        elif query_length > 200:
            scores[UserIntent.RESEARCH] += 1.5
        elif query_length > 100:
            scores[UserIntent.ANALYSIS] += 1.0
        
        # 3. Anzahl Fragezeichen/Semikolons (Teilfragen)
        subquestions = query.count("?") + query.count(";") // 2
        if subquestions >= 3:
            scores[UserIntent.RESEARCH] += 2.0
        elif subquestions >= 2:
            scores[UserIntent.ANALYSIS] += 1.0
        
        # 4. Domänen-Komplexität
        domain_count = sum(1 for kw in cls.DOMAIN_KEYWORDS if kw in query_lower)
        if domain_count >= 3:
            scores[UserIntent.RESEARCH] += 1.5
        elif domain_count >= 2:
            scores[UserIntent.ANALYSIS] += 1.0
        
        # 5. Listen-Struktur (1), 2), etc.)
        list_items = len(re.findall(r'\d+\)', query))
        if list_items >= 3:
            scores[UserIntent.RESEARCH] += 2.0
        
        # Intent mit höchstem Score wählen
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        
        # Confidence berechnen (0.0 - 1.0)
        total_score = sum(scores.values())
        confidence = best_score / max(total_score, 1.0) if total_score > 0 else 0.3
        
        # Reasoning für Debugging
        reasoning = f"Pattern-Score: {best_score:.1f}, Total: {total_score:.1f}"
        if best_score == 0:
            # Fallback bei keinem Match
            best_intent = UserIntent.EXPLANATION
            confidence = 0.3
            reasoning = "Kein Pattern-Match, Fallback zu EXPLANATION"
        
        return IntentPrediction(
            intent=best_intent,
            confidence=min(confidence, 1.0),
            method="rule_based",
            reasoning=reasoning
        )


class LLMIntentClassifier:
    """LLM-basierter Klassifikator für komplexe Fälle"""
    
    @staticmethod
    async def classify_async(
        query: str,
        ollama_service,
        model: str = "phi3"
    ) -> IntentPrediction:
        """
        Fragt LLM nach Intent-Klassifikation
        
        Args:
            query: User-Anfrage
            ollama_service: Ollama-Service-Instanz
            model: LLM-Modell (default: phi3)
            
        Returns:
            IntentPrediction mit Intent, Confidence, Methode
        """
        prompt = f"""Du bist ein Intent-Klassifikator. Klassifiziere die folgende Anfrage in eine der 4 Kategorien:

1. QUICK_ANSWER: Einfache Fakten-Fragen ("Was ist X?", "Wer ist Y?")
2. EXPLANATION: Erklärungen ("Wie funktioniert X?", "Warum passiert Y?")
3. ANALYSIS: Analysen, Vergleiche, Bewertungen ("Vergleiche X und Y", "Analysiere Aspekt Z")
4. RESEARCH: Umfassende Recherchen, Multi-Aspekt-Analysen (mehrere Teilfragen, komplexe Domänen)

Anfrage: "{query}"

Antworte NUR mit einem JSON-Objekt in folgendem Format:
{{"intent": "QUICK_ANSWER|EXPLANATION|ANALYSIS|RESEARCH", "confidence": 0.0-1.0, "reasoning": "kurze Begründung"}}"""

        try:
            response = await ollama_service.generate(
                model=model,
                prompt=prompt,
                temperature=0.1,  # Niedrig für konsistente Klassifikation
                max_tokens=150
            )
            
            # JSON parsen
            import json
            result_text = response.get("response", "").strip()
            
            # Versuche JSON zu extrahieren (auch wenn in Markdown-Block)
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                intent_str = result.get("intent", "EXPLANATION").upper()
                intent = UserIntent[intent_str] if intent_str in UserIntent.__members__ else UserIntent.EXPLANATION
                
                return IntentPrediction(
                    intent=intent,
                    confidence=float(result.get("confidence", 0.7)),
                    method="llm",
                    reasoning=result.get("reasoning", "LLM-basierte Klassifikation")
                )
            else:
                raise ValueError("Kein JSON in LLM-Response gefunden")
                
        except Exception as e:
            # Fallback bei LLM-Fehler
            return IntentPrediction(
                intent=UserIntent.EXPLANATION,
                confidence=0.5,
                method="llm_fallback",
                reasoning=f"LLM-Fehler: {str(e)}"
            )
    
    @staticmethod
    def classify_sync(query: str, ollama_service, model: str = "phi3") -> IntentPrediction:
        """Synchrone Wrapper-Funktion für LLM-Klassifikation"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            LLMIntentClassifier.classify_async(query, ollama_service, model)
        )


class HybridIntentClassifier:
    """
    Kombiniert Rule-Based und LLM-Klassifikation
    
    Strategie:
    1. Rule-Based Klassifikation (schnell)
    2. Bei niedriger Confidence (<0.7): LLM-Klassifikation
    3. Gewichtete Kombination beider Ergebnisse
    """
    
    def __init__(self, llm_threshold: float = 0.7):
        """
        Args:
            llm_threshold: Confidence-Schwelle für LLM-Fallback
        """
        self.llm_threshold = llm_threshold
        self.rule_classifier = RuleBasedIntentClassifier()
    
    async def classify_async(
        self,
        query: str,
        ollama_service = None,
        model: str = "phi3"
    ) -> IntentPrediction:
        """
        Hybride Klassifikation (async)
        
        Args:
            query: User-Anfrage
            ollama_service: Optional - Ollama-Service für LLM-Fallback
            model: LLM-Modell
            
        Returns:
            IntentPrediction mit Intent, Confidence, Methode
        """
        # 1. Rule-Based Klassifikation
        rule_prediction = self.rule_classifier.classify(query)
        
        # 2. Wenn Confidence hoch genug: direkt zurückgeben
        if rule_prediction.confidence >= self.llm_threshold or ollama_service is None:
            return rule_prediction
        
        # 3. LLM-Klassifikation bei niedriger Confidence
        llm_prediction = await LLMIntentClassifier.classify_async(
            query, ollama_service, model
        )
        
        # 4. Hybrid-Entscheidung: LLM gewinnt bei höherer Confidence
        if llm_prediction.confidence > rule_prediction.confidence:
            llm_prediction.method = "hybrid_llm"
            llm_prediction.reasoning = (
                f"LLM ({llm_prediction.confidence:.2f}) > "
                f"Rules ({rule_prediction.confidence:.2f}): {llm_prediction.reasoning}"
            )
            return llm_prediction
        else:
            rule_prediction.method = "hybrid_rules"
            rule_prediction.reasoning = (
                f"Rules ({rule_prediction.confidence:.2f}) >= "
                f"LLM ({llm_prediction.confidence:.2f}): {rule_prediction.reasoning}"
            )
            return rule_prediction
    
    def classify_sync(
        self,
        query: str,
        ollama_service = None,
        model: str = "phi3"
    ) -> IntentPrediction:
        """Synchrone Wrapper-Funktion"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.classify_async(query, ollama_service, model)
        )


# Convenience-Funktionen
def classify_intent_fast(query: str) -> IntentPrediction:
    """Schnelle Rule-Based Klassifikation (kein LLM)"""
    return RuleBasedIntentClassifier.classify(query)


async def classify_intent_llm(
    query: str,
    ollama_service,
    model: str = "phi3"
) -> IntentPrediction:
    """LLM-basierte Klassifikation (async)"""
    return await LLMIntentClassifier.classify_async(query, ollama_service, model)


async def classify_intent_hybrid(
    query: str,
    ollama_service = None,
    model: str = "phi3",
    llm_threshold: float = 0.7
) -> IntentPrediction:
    """Hybride Klassifikation (async)"""
    classifier = HybridIntentClassifier(llm_threshold)
    return await classifier.classify_async(query, ollama_service, model)


# Test-Funktion
if __name__ == "__main__":
    # Test-Queries
    test_queries = [
        "Was ist eine Baugenehmigung?",
        "Wie funktioniert das Genehmigungsverfahren für Windkraftanlagen?",
        "Vergleiche die Umweltauflagen für Onshore- und Offshore-Windparks.",
        """Analysiere bitte folgende Aspekte:
        1) Rechtliche Rahmenbedingungen
        2) Umweltrechtliche Auflagen
        3) Finanzielle Förderung
        4) Soziale Akzeptanz""",
        "Welche verwaltungsrechtlichen Voraussetzungen gelten für die Anfechtung eines Bescheids?",
        "Erkläre den Unterschied zwischen Ermessen und gebundener Entscheidung.",
        "Wann tritt ein Verwaltungsakt in Kraft?",
    ]
    
    classifier = RuleBasedIntentClassifier()
    
    print("=" * 80)
    print("INTENT CLASSIFIER - Rule-Based Tests")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─' * 80}")
        print(f"Query {i}: {query[:70]}...")
        
        prediction = classifier.classify(query)
        
        print(f"\n🎯 Intent: {prediction.intent.value.upper()}")
        print(f"📊 Confidence: {prediction.confidence:.2%}")
        print(f"🔍 Method: {prediction.method}")
        print(f"💡 Reasoning: {prediction.reasoning}")
    
    print(f"\n{'=' * 80}\n")
