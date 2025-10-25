#!/usr/bin/env python3
"""
Token Budget Calculator - Dynamisches Budget-Management
========================================================
Berechnet optimale Token-Budgets basierend auf:
- Query-Komplexität
- RAG-Chunk-Count
- Multi-Source-Diversität
- Agent-Count
- User-Intent
- Confidence-Score

Author: VERITAS System
Date: 2025-10-17
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class UserIntent(str, Enum):
    """User-Intent-Typen mit Token-Gewichtungen"""
    QUICK_ANSWER = "quick_answer"  # Fakt, kurz → 0.5x
    EXPLANATION = "explanation"    # Erklärung → 1.0x
    ANALYSIS = "analysis"          # Analyse → 1.5x
    RESEARCH = "research"          # Recherche → 2.0x


@dataclass
class TokenBudgetConfig:
    """Konfiguration für Token-Budget-Berechnung"""
    base_tokens: int = 600  # Erhöht von 500 wegen Verwaltungsrecht-Komplexität
    min_tokens: int = 250  # Erhöht von 200
    max_tokens: int = 4000  # Erhöht von 3000 für komplexe Verwaltungsrecht-Fälle
    chunk_token_factor: int = 50
    max_chunk_bonus: int = 1000
    agent_scaling_factor: float = 0.15
    confidence_low_threshold: float = 0.5
    confidence_high_threshold: float = 0.8
    confidence_low_boost: float = 1.2
    confidence_high_reduction: float = 0.9


@dataclass
class BudgetFactors:
    """Faktoren für Budget-Berechnung"""
    query_complexity: float  # 1-10
    chunk_count: int
    source_diversity: float  # 1.0-1.4
    agent_count: int
    intent_weight: float  # 0.5-2.0
    confidence: Optional[float] = None
    user_preference: float = 1.0  # 0.5-2.0 (User-Slider)


class QueryComplexityAnalyzer:
    """Analysiert Query-Komplexität und berechnet Score (1-10)"""
    
    # Fragewort-Komplexität
    QUESTION_WORDS = {
        # Einfach (Score 1-3)
        "was": 2,
        "wer": 2,
        "wo": 2,
        "wann": 2,
        "welche": 2,
        "welcher": 2,
        "welches": 2,
        
        # Mittel (Score 4-6)
        "wie": 5,
        "wieviel": 5,
        "wie viel": 5,
        "wie viele": 5,
        "wodurch": 5,
        
        # Komplex (Score 7-8)
        "warum": 7,
        "weshalb": 7,
        "wieso": 7,
        "inwiefern": 7,
        
        # Sehr komplex (Score 9-10)
        "analysiere": 9,
        "vergleiche": 9,
        "bewerte": 9,
        "erläutere": 8,
        "erkläre": 7,
        "untersuche": 9,
    }
    
    # Domänen-Keywords mit Gewichtung (höhere Werte = mehr Komplexität)
    DOMAIN_KEYWORDS = {
        # Verwaltungsrecht (SEHR KOMPLEX - +1.5-2.0 pro Keyword)
        "verwaltungsrecht": 1.5,
        "verwaltungsverfahren": 1.5,
        "verwaltungsakt": 1.5,
        "verwaltungsgerichtsordnung": 2.0,  # NEU: VwGO sehr komplex
        "bescheid": 1.2,
        "anfechtung": 1.2,
        "widerspruch": 1.2,
        "widerspruchsverfahren": 1.5,  # NEU: Verfahren komplexer
        "ermessen": 2.0,  # ERHÖHT: Fachbegriff sehr komplex
        "ermessensspielraum": 2.0,  # ERHÖHT
        "beurteilungsspielraum": 2.0,  # NEU: Ähnlich wie Ermessen
        "verhältnismäßigkeit": 2.0,  # ERHÖHT: Fachbegriff sehr komplex
        "verhältnismäßigkeitsprinzip": 2.0,  # NEU: Vollständiger Fachbegriff
        "abwägung": 2.0,  # ERHÖHT: Fachbegriff sehr komplex
        
        # Baurecht (KOMPLEX - +1.0-1.2 pro Keyword)
        "baurecht": 1.0,
        "baugenehmigung": 1.0,
        "bauvorhaben": 1.0,
        "bauantrag": 0.8,
        "bebauungsplan": 1.5,  # ERHÖHT: Sehr komplex
        "flächennutzungsplan": 1.2,
        "bauordnung": 1.0,
        "baurechtlich": 1.0,
        
        # Umweltrecht (KOMPLEX - +0.8-1.2 pro Keyword)
        "umweltrecht": 1.0,
        "uvp": 1.2,
        "umweltverträglichkeitsprüfung": 1.2,
        "naturschutz": 1.0,
        "artenschutz": 1.2,
        "emissionsschutz": 1.0,
        "immissionsschutz": 1.0,
        "lärmschutz": 0.8,
        "lärmschutzverordnung": 1.2,  # NEU: Verordnung komplex
        "lärmgrenzwerte": 1.0,  # NEU: Grenzwerte komplex
        "grenzwerte": 1.0,  # NEU: Allgemein Grenzwerte
        "umweltauflagen": 1.0,
        
        # Verkehrsrecht (MITTEL - +0.8-1.0 pro Keyword)
        "verkehrsrecht": 1.0,
        "bußgeldbescheid": 1.0,  # NEU
        "fahrerlaubnis": 0.8,
        "fahrerlaubnisentziehung": 1.2,  # NEU: Entziehung komplex
        
        # Allgemein Rechtlich (MITTEL - +0.8-1.0 pro Keyword)
        "rechtlich": 0.8,
        "gesetz": 0.8,
        "verordnung": 1.0,  # ERHÖHT: Verordnungen sind komplex
        "vorschrift": 0.8,
        "regelung": 0.8,
        "norm": 0.8,
        "richtlinie": 0.8,
        "genehmigung": 0.8,
        "voraussetzungen": 0.9,  # NEU: Frage nach Voraussetzungen ist komplex
        
        # Finanziell/Förderung (MITTEL - +0.6 pro Keyword)
        "finanziell": 0.6,
        "förderung": 0.6,
        "investition": 0.6,
        "kosten": 0.5,
        "wirtschaftlichkeit": 0.7,
        
        # Sozial/Beteiligung (NIEDRIG - +0.5 pro Keyword)
        "sozial": 0.5,
        "beteiligung": 0.6,
        "öffentlichkeitsbeteiligung": 0.7,
        "akzeptanz": 0.5,
        "kommunikation": 0.4,
        
        # Technisch (NIEDRIG - +0.4 pro Keyword)
        "technisch": 0.4,
        "engineering": 0.4,
        "konstruktion": 0.4,
        "planung": 0.5,
    }
    
    @classmethod
    def analyze(cls, query: str) -> float:
        """
        Analysiert Query und gibt Komplexitäts-Score zurück (1-10)
        
        Args:
            query: Die Anfrage
            
        Returns:
            float: Komplexitäts-Score zwischen 1.0 und 10.0
        """
        query_lower = query.lower()
        score = 3.0  # Basis-Score
        
        # 1. Fragewort-Analyse
        for word, word_score in cls.QUESTION_WORDS.items():
            if word in query_lower:
                score = max(score, word_score)
                break
        
        # 2. Anzahl Teilfragen (?, ;)
        question_marks = query.count("?")
        semicolons = query.count(";")
        subquestions = question_marks + (semicolons // 2)
        score += min(subquestions * 0.5, 2.0)
        
        # 3. Domänen-Keywords (mit Gewichtung)
        domain_score = 0.0
        for keyword, weight in cls.DOMAIN_KEYWORDS.items():
            if keyword in query_lower:
                domain_score += weight
        score += min(domain_score, 3.0)  # Max +3.0 für Domänen
        
        # 4. Satzlänge (längere Queries = komplexer)
        if len(query) > 200:
            score += 1.5
        elif len(query) > 100:
            score += 1.0
        elif len(query) > 50:
            score += 0.5
        
        # 5. Listenstruktur (1), 2), etc.)
        list_items = len(re.findall(r'\d+\)', query))
        if list_items > 0:
            score += min(list_items * 0.3, 1.5)
        
        # Score begrenzen auf 1-10
        return max(1.0, min(score, 10.0))


class TokenBudgetCalculator:
    """Berechnet dynamisches Token-Budget basierend auf verschiedenen Faktoren"""
    
    def __init__(self, config: Optional[TokenBudgetConfig] = None):
        """
        Initialisiert Calculator
        
        Args:
            config: Optionale Konfiguration (nutzt Defaults wenn None)
        """
        self.config = config or TokenBudgetConfig()
        self.complexity_analyzer = QueryComplexityAnalyzer()
    
    def calculate_budget(
        self,
        query: str,
        chunk_count: int,
        source_types: List[str],
        agent_count: int,
        intent: UserIntent = UserIntent.EXPLANATION,
        confidence: Optional[float] = None,
        user_preference: float = 1.0
    ) -> Tuple[int, Dict[str, float]]:
        """
        Berechnet optimales Token-Budget
        
        Args:
            query: Die Anfrage
            chunk_count: Anzahl RAG-Chunks
            source_types: Liste der Datenquellen (z.B. ["vector", "graph"])
            agent_count: Anzahl verwendeter Agenten
            intent: User-Intent
            confidence: Optionaler Confidence-Score (post-hoc)
            user_preference: User-Slider (0.5-2.0)
            
        Returns:
            Tuple[int, Dict]: (berechnetes Budget, Breakdown der Faktoren)
        """
        # 1. Query-Komplexität analysieren
        complexity_score = self.complexity_analyzer.analyze(query)
        complexity_factor = complexity_score / 10.0
        
        # 2. Source-Diversität berechnen
        source_diversity = self._calculate_source_diversity(source_types)
        
        # 3. Intent-Weight
        intent_weights = {
            UserIntent.QUICK_ANSWER: 0.5,
            UserIntent.EXPLANATION: 1.0,
            UserIntent.ANALYSIS: 1.5,
            UserIntent.RESEARCH: 2.0
        }
        intent_weight = intent_weights.get(intent, 1.0)
        
        # 4. Faktoren zusammenstellen
        factors = BudgetFactors(
            query_complexity=complexity_score,
            chunk_count=chunk_count,
            source_diversity=source_diversity,
            agent_count=agent_count,
            intent_weight=intent_weight,
            confidence=confidence,
            user_preference=user_preference
        )
        
        # 5. Budget berechnen
        budget = self._compute_budget(factors)
        
        # 6. Breakdown für Analytics erstellen
        breakdown = self._create_breakdown(factors, budget)
        
        return budget, breakdown
    
    def _calculate_source_diversity(self, source_types: List[str]) -> float:
        """
        Berechnet Source-Diversität-Multiplikator
        
        Args:
            source_types: Liste der Datenquellen
            
        Returns:
            float: Multiplikator (1.0-1.4)
        """
        unique_sources = set(source_types)
        
        if len(unique_sources) == 0:
            return 1.0
        elif len(unique_sources) == 1:
            return 1.0
        elif len(unique_sources) == 2:
            return 1.15
        elif len(unique_sources) == 3:
            return 1.30
        else:
            # 4+ Quellen
            return 1.40
    
    def _compute_budget(self, factors: BudgetFactors) -> int:
        """
        Berechnet finales Budget aus allen Faktoren
        
        Args:
            factors: Budget-Faktoren
            
        Returns:
            int: Berechnetes Token-Budget
        """
        # Basis-Budget
        budget = float(self.config.base_tokens)
        
        # Komplexitäts-Multiplikator
        complexity_factor = factors.query_complexity / 10.0
        budget *= complexity_factor
        
        # Chunk-Bonus
        chunk_bonus = min(
            factors.chunk_count * self.config.chunk_token_factor,
            self.config.max_chunk_bonus
        )
        budget += chunk_bonus
        
        # Source-Diversität
        budget *= factors.source_diversity
        
        # Agent-Scaling
        agent_factor = 1.0 + (factors.agent_count * self.config.agent_scaling_factor)
        budget *= agent_factor
        
        # Intent-Weight
        budget *= factors.intent_weight
        
        # User-Preference
        budget *= factors.user_preference
        
        # Confidence-Adjustment (post-hoc, falls vorhanden)
        if factors.confidence is not None:
            if factors.confidence < self.config.confidence_low_threshold:
                budget *= self.config.confidence_low_boost
            elif factors.confidence > self.config.confidence_high_threshold:
                budget *= self.config.confidence_high_reduction
        
        # Min/Max Caps anwenden
        budget = max(self.config.min_tokens, min(int(budget), self.config.max_tokens))
        
        return budget
    
    def _create_breakdown(self, factors: BudgetFactors, final_budget: int) -> Dict[str, float]:
        """
        Erstellt detailliertes Breakdown für Analytics
        
        Args:
            factors: Budget-Faktoren
            final_budget: Finales Budget
            
        Returns:
            Dict: Breakdown-Informationen
        """
        return {
            "final_budget": final_budget,
            "base_tokens": self.config.base_tokens,
            "complexity_score": factors.query_complexity,
            "complexity_factor": factors.query_complexity / 10.0,
            "chunk_count": factors.chunk_count,
            "chunk_bonus": min(
                factors.chunk_count * self.config.chunk_token_factor,
                self.config.max_chunk_bonus
            ),
            "source_diversity": factors.source_diversity,
            "agent_count": factors.agent_count,
            "agent_factor": 1.0 + (factors.agent_count * self.config.agent_scaling_factor),
            "intent_weight": factors.intent_weight,
            "user_preference": factors.user_preference,
            "confidence": factors.confidence,
            "confidence_adjustment": self._get_confidence_adjustment(factors.confidence)
        }
    
    def _get_confidence_adjustment(self, confidence: Optional[float]) -> float:
        """Gibt Confidence-Adjustment zurück"""
        if confidence is None:
            return 1.0
        elif confidence < self.config.confidence_low_threshold:
            return self.config.confidence_low_boost
        elif confidence > self.config.confidence_high_threshold:
            return self.config.confidence_high_reduction
        else:
            return 1.0


# Convenience-Funktion
def calculate_token_budget(
    query: str,
    chunk_count: int = 0,
    source_types: List[str] = None,
    agent_count: int = 0,
    intent: str = "explanation",
    confidence: Optional[float] = None,
    user_preference: float = 1.0,
    config: Optional[TokenBudgetConfig] = None
) -> Tuple[int, Dict[str, float]]:
    """
    Convenience-Funktion für Token-Budget-Berechnung
    
    Returns:
        Tuple[int, Dict]: (Budget, Breakdown)
    """
    calculator = TokenBudgetCalculator(config)
    
    # Intent String zu Enum konvertieren
    intent_enum = UserIntent(intent) if isinstance(intent, str) else intent
    
    return calculator.calculate_budget(
        query=query,
        chunk_count=chunk_count,
        source_types=source_types or [],
        agent_count=agent_count,
        intent=intent_enum,
        confidence=confidence,
        user_preference=user_preference
    )


# Test-Funktion
if __name__ == "__main__":
    # Test-Szenarien
    test_cases = [
        {
            "query": "Was ist eine Baugenehmigung?",
            "chunk_count": 2,
            "source_types": ["vector"],
            "agent_count": 0,
            "intent": "quick_answer"
        },
        {
            "query": "Welche Umweltauflagen gelten für Windkraftanlagen in Naturschutzgebieten?",
            "chunk_count": 8,
            "source_types": ["vector", "relational"],
            "agent_count": 3,
            "intent": "explanation"
        },
        {
            "query": """
            Analysiere bitte folgende Aspekte für ein 5 MW Windkraftprojekt:
            1) Rechtliche Genehmigungsanforderungen
            2) Umweltrechtliche Auflagen
            3) Finanzielle Aspekte
            4) Soziale Auswirkungen
            """,
            "chunk_count": 15,
            "source_types": ["vector", "graph", "relational"],
            "agent_count": 7,
            "intent": "research"
        },
        {
            "query": """
            Welche verwaltungsrechtlichen Voraussetzungen müssen für einen Bescheid 
            zur Baugenehmigung einer Windkraftanlage erfüllt sein? Dabei ist insbesondere 
            die Abwägung zwischen Ermessensspielraum der Behörde und Verhältnismäßigkeitsgrundsatz 
            zu beachten. Welche Rechtsbehelfe stehen bei Anfechtung des Verwaltungsakts zur Verfügung?
            """,
            "chunk_count": 12,
            "source_types": ["vector", "graph", "relational"],
            "agent_count": 5,
            "intent": "research"
        }
    ]
    
    calculator = TokenBudgetCalculator()
    
    print("=" * 80)
    print("TOKEN BUDGET CALCULATOR - Test-Szenarien")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"Szenario {i}:")
        print(f"{'─' * 80}")
        print(f"Query: {test['query'][:80]}...")
        
        budget, breakdown = calculator.calculate_budget(
            query=test['query'],
            chunk_count=test['chunk_count'],
            source_types=test['source_types'],
            agent_count=test['agent_count'],
            intent=UserIntent(test['intent'])
        )
        
        print(f"\n📊 Berechnetes Budget: {budget} tokens")
        print(f"\n🔍 Breakdown:")
        print(f"  • Basis: {breakdown['base_tokens']} tokens")
        print(f"  • Komplexität: {breakdown['complexity_score']:.1f}/10 (Faktor: {breakdown['complexity_factor']:.2f}x)")
        print(f"  • Chunks: {breakdown['chunk_count']} (+{breakdown['chunk_bonus']} tokens)")
        print(f"  • Quellen: {len(test['source_types'])} (Diversität: {breakdown['source_diversity']:.2f}x)")
        print(f"  • Agenten: {breakdown['agent_count']} (Faktor: {breakdown['agent_factor']:.2f}x)")
        print(f"  • Intent: {test['intent']} (Gewicht: {breakdown['intent_weight']:.1f}x)")
    
    print(f"\n{'=' * 80}\n")
