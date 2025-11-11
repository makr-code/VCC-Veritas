#!/usr/bin/env python3
"""
VERITAS QUERY EXPANSION SERVICE
================================

LLM-basierte Query-Expansion für verbesserte Retrieval-Recall.
Generiert semantische Varianten einer Suchanfrage via Ollama.

Query Expansion Strategien:
---------------------------
1. **Synonym Expansion**: "nachhaltig" → "umweltfreundlich", "ökologisch", "grün"
2. **Context Expansion**: "Haus bauen" → "Wie baue ich ein Haus nach DIN-Normen?"
3. **Multi-Perspective**: Rechtlich, Technisch, Prozessual

Vorteile:
---------
- Höhere Recall-Rate (mehr relevante Dokumente gefunden)
- Robustheit gegen Query-Formulierung
- Bessere Abdeckung von Synonymen & Paraphrasen

Beispiel:
--------
Original: "Wie baue ich ein barrierefreies Haus?"

Expanded:
- "Welche DIN-Normen gelten für barrierefreies Bauen?"
- "Anforderungen an behindertengerechte Wohngebäude"
- "Barrierefreiheit Neubau § 39 BauO NRW"

Author: VERITAS System
Date: 2025-10-06
Version: 1.0
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Ollama Import
try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("⚠️ httpx nicht verfügbar - Query Expansion arbeitet ohne Ollama")


class ExpansionStrategy(Enum):
    """Query Expansion Strategien."""

    SYNONYM = "synonym"  # Synonyme & ähnliche Begriffe
    CONTEXT = "context"  # Kontextuelle Umformulierung
    MULTI_PERSPECTIVE = "multi_perspective"  # Verschiedene Perspektiven
    TECHNICAL = "technical"  # Technische/Fachliche Formulierung
    SIMPLE = "simple"  # Vereinfachte Formulierung


@dataclass
class QueryExpansionConfig:
    """Konfiguration für Query Expansion."""

    # LLM-Parameter
    model: str = "phi3:latest"  # Ollama Model (Best: phi3:latest 1654ms, llama3.2:latest 1185ms)
    temperature: float = 0.7  # Kreativität (0.0-1.0)
    max_tokens: int = 256  # Max Tokens pro Expansion

    # Expansion-Parameter
    num_expansions: int = 2  # Anzahl generierte Varianten
    strategies: List[ExpansionStrategy] = field(default_factory=lambda: [ExpansionStrategy.SYNONYM, ExpansionStrategy.CONTEXT])

    # Ollama-Verbindung
    ollama_base_url: str = "http://localhost:11434"
    timeout: float = 10.0  # Timeout in Sekunden

    # Caching
    enable_cache: bool = True
    cache_ttl: int = 3600  # Cache TTL in Sekunden

    # Fallback
    fallback_to_original: bool = True  # Original-Query als Fallback


@dataclass
class ExpandedQuery:
    """Eine expandierte Query-Variante."""

    text: str
    strategy: ExpansionStrategy
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class QueryExpander:
    """
    LLM-basierte Query-Expansion via Ollama.

    Funktionsweise:
    --------------
    1. Original-Query analysieren
    2. LLM-Prompt für Expansion-Strategie erstellen
    3. Ollama API aufrufen
    4. Varianten extrahieren & validieren
    5. Duplikate entfernen

    Performance:
    -----------
    - LLM-Latenz: ~500-2000ms (abhängig von Model-Größe)
    - Cache-Hit: ~1ms
    - Fallback (ohne Ollama): ~0ms (original query)

    Beispiel:
    --------
    expander = QueryExpander()
    results = await expander.expand(
        "Wie baue ich ein barrierefreies Haus?",
        num_expansions=2
    )
    # results = [
    #   ExpandedQuery(text="Welche DIN-Normen gelten für barrierefreies Bauen?", ...),
    #   ExpandedQuery(text="Anforderungen behindertengerechtes Wohnen", ...)
    # ]
    """

    def __init__(self, config: Optional[QueryExpansionConfig] = None):
        """Initialisiert Query Expander.

        Args:
            config: Expansion-Konfiguration (optional)
        """
        self.config = config or QueryExpansionConfig()
        self._cache: Dict[str, List[ExpandedQuery]] = {}
        self._ollama_available = HTTPX_AVAILABLE

        if not self._ollama_available:
            logger.warning("⚠️ Query Expansion läuft ohne Ollama (httpx fehlt) - " "Fallback auf Original-Query")

    async def expand(
        self, query: str, num_expansions: Optional[int] = None, strategies: Optional[List[ExpansionStrategy]] = None
    ) -> List[ExpandedQuery]:
        """
        Expandiert Query in semantische Varianten.

        Args:
            query: Original-Suchanfrage
            num_expansions: Anzahl Varianten (default: config.num_expansions)
            strategies: Expansion-Strategien (default: config.strategies)

        Returns:
            Liste von ExpandedQuery-Objekten (inkl. Original)
        """
        num_expansions = num_expansions or self.config.num_expansions
        strategies = strategies or self.config.strategies

        # Cache-Check
        cache_key = self._get_cache_key(query, num_expansions, strategies)
        if self.config.enable_cache and cache_key in self._cache:
            logger.debug(f"💾 Query Expansion Cache-Hit: '{query[:50]}...'")
            return self._cache[cache_key]

        start_time = time.time()

        # Original-Query immer inkludieren
        expanded_queries = [
            ExpandedQuery(
                text=query, strategy=ExpansionStrategy.SYNONYM, confidence=1.0, metadata={"source": "original"}  # Placeholder
            )
        ]

        # LLM-Expansion nur wenn Ollama verfügbar
        if self._ollama_available:
            try:
                # Für jede Strategie Varianten generieren
                for strategy in strategies[:num_expansions]:
                    variant = await self._expand_with_strategy(query, strategy)
                    if variant and variant.text.strip() and variant.text != query:
                        # Duplikat-Check
                        if not any(eq.text.lower() == variant.text.lower() for eq in expanded_queries):
                            expanded_queries.append(variant)

                    # Limit erreicht?
                    if len(expanded_queries) >= num_expansions + 1:  # +1 für Original
                        break

            except Exception as e:
                logger.warning(f"⚠️ Query Expansion fehlgeschlagen: {e}")
                if not self.config.fallback_to_original:
                    raise

        # Cache speichern
        if self.config.enable_cache:
            self._cache[cache_key] = expanded_queries

        duration = (time.time() - start_time) * 1000
        logger.info(f"🔍 Query Expansion: '{query[:50]}...' → {len(expanded_queries)} Varianten ({duration:.0f}ms)")

        return expanded_queries

    async def _expand_with_strategy(self, query: str, strategy: ExpansionStrategy) -> Optional[ExpandedQuery]:
        """Generiert Query-Variante mit spezifischer Strategie."""

        # Prompt basierend auf Strategie
        prompt = self._build_prompt(query, strategy)

        # Ollama API aufrufen
        try:
            variant_text = await self._call_ollama(prompt)

            return ExpandedQuery(
                text=variant_text,
                strategy=strategy,
                confidence=0.85,  # LLM-generiert
                metadata={"source": "ollama", "model": self.config.model},
            )

        except Exception as e:
            logger.warning(f"⚠️ Ollama-Call fehlgeschlagen für {strategy.value}: {e}")
            return None

    def _build_prompt(self, query: str, strategy: ExpansionStrategy) -> str:
        """Erstellt Prompt für Query Expansion."""

        base_instruction = (
            "Du bist ein Experte für Baurecht, Umweltrecht und technische Normen. "
            "Deine Aufgabe ist es, Suchanfragen umzuformulieren.\n\n"
        )

        if strategy == ExpansionStrategy.SYNONYM:
            instruction = (
                "Formuliere die folgende Suchanfrage mit SYNONYMEN und ähnlichen Begriffen um. "
                "Behalte die gleiche Bedeutung bei, verwende aber andere Wörter.\n\n"
                f"Original: {query}\n"
                "Umformulierung mit Synonymen:"
            )

        elif strategy == ExpansionStrategy.CONTEXT:
            instruction = (
                "Formuliere die folgende Suchanfrage KONTEXTUELL um. "
                "Füge relevante rechtliche oder technische Details hinzu.\n\n"
                f"Original: {query}\n"
                "Kontextuelle Umformulierung:"
            )

        elif strategy == ExpansionStrategy.MULTI_PERSPECTIVE:
            instruction = (
                "Formuliere die folgende Suchanfrage aus einer ANDEREN PERSPEKTIVE um "
                "(z.B. rechtlich, technisch, oder prozessual).\n\n"
                f"Original: {query}\n"
                "Alternative Perspektive:"
            )

        elif strategy == ExpansionStrategy.TECHNICAL:
            instruction = (
                "Formuliere die folgende Suchanfrage TECHNISCH/FACHLICH um. "
                "Verwende Fachbegriffe, Normen, Paragraphen falls relevant.\n\n"
                f"Original: {query}\n"
                "Technische Formulierung:"
            )

        elif strategy == ExpansionStrategy.SIMPLE:
            instruction = (
                "Formuliere die folgende Suchanfrage EINFACHER und allgemeinverständlicher um.\n\n"
                f"Original: {query}\n"
                "Einfache Formulierung:"
            )

        else:
            instruction = f"Original: {query}\nUmformulierung:"

        return base_instruction + instruction

    async def _call_ollama(self, prompt: str) -> str:
        """Ruft Ollama API auf und extrahiert Response."""

        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx nicht verfügbar - kann Ollama nicht aufrufen")

        url = f"{self.config.ollama_base_url}/api/generate"

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
                "stop": ["\n\n", "Original:", "Umformulierung:"],
            },
        }

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            variant = result.get("response", "").strip()

            # Cleanup: Entferne Anführungszeichen, Präfixe, etc.
            variant = self._cleanup_variant(variant)

            return variant

    def _cleanup_variant(self, text: str) -> str:
        """Bereinigt LLM-Output."""

        # Entferne Anführungszeichen
        text = text.strip("\"'")

        # Entferne häufige Präfixe
        prefixes = [
            "Umformulierung:",
            "Variante:",
            "Alternative:",
            "Synonym:",
            "Technisch:",
            "Einfach:",
        ]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix) :].strip()

        # Entferne Zeilenumbrüche
        text = text.replace("\n", " ").strip()

        # Nur erste Zeile wenn mehrere
        if "." in text:
            sentences = text.split(".")
            # Nehme ersten vollständigen Satz
            text = sentences[0].strip() + "."

        return text

    def _get_cache_key(self, query: str, num_expansions: int, strategies: List[ExpansionStrategy]) -> str:
        """Erstellt Cache-Key."""
        strategy_str = "_".join(s.value for s in strategies)
        return f"{query}_{num_expansions}_{strategy_str}"

    def get_stats(self) -> Dict[str, Any]:
        """Gibt Expansion-Statistiken zurück."""
        return {
            "ollama_available": self._ollama_available,
            "cache_size": len(self._cache),
            "config": {
                "model": self.config.model,
                "num_expansions": self.config.num_expansions,
                "temperature": self.config.temperature,
                "strategies": [s.value for s in self.config.strategies],
            },
        }

    def clear_cache(self) -> None:
        """Leert Query-Cache."""
        self._cache.clear()
        logger.info("🗑️ Query Expansion Cache geleert")


# Singleton-Pattern
_query_expander_instance: Optional[QueryExpander] = None


def get_query_expander(config: Optional[QueryExpansionConfig] = None) -> QueryExpander:
    """Gibt Singleton Query Expander zurück."""
    global _query_expander_instance

    if _query_expander_instance is None:
        _query_expander_instance = QueryExpander(config)

    return _query_expander_instance


# Multi-Query Generator für verschiedene Perspektiven
class MultiQueryGenerator:
    """
    Generiert Queries aus verschiedenen Perspektiven.

    Perspektiven:
    ------------
    - Rechtlich: Paragraphen, Gesetze, Vorschriften
    - Technisch: Normen, Standards, Spezifikationen
    - Prozessual: Abläufe, Verfahren, Genehmigungen

    Beispiel:
    --------
    Original: "Wie baue ich ein Haus?"

    Rechtlich: "Welche baurechtlichen Vorschriften gelten für Wohngebäude?"
    Technisch: "Welche DIN-Normen sind beim Hausbau zu beachten?"
    Prozessual: "Welche Genehmigungsverfahren durchlaufe ich beim Hausbau?"
    """

    def __init__(self, query_expander: Optional[QueryExpander] = None):
        """Initialisiert Multi-Query Generator.

        Args:
            query_expander: Query Expander Instanz (optional)
        """
        self.expander = query_expander or get_query_expander()

    async def generate_multi_perspective(self, query: str, perspectives: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Generiert Queries aus verschiedenen Perspektiven.

        Args:
            query: Original-Suchanfrage
            perspectives: Liste von Perspektiven (default: rechtlich, technisch, prozessual)

        Returns:
            Dict mit Perspektive → Query Mapping
        """
        perspectives = perspectives or ["rechtlich", "technisch", "prozessual"]

        multi_queries = {}

        for perspective in perspectives:
            # Custom-Prompt für Perspektive
            prompt = (
                "Du bist Experte für Baurecht und technische Normen. "
                f"Formuliere die folgende Suchanfrage aus {perspective.upper()}ER Sicht um:\n\n"
                f"Original: {query}\n"
                f"{perspective.capitalize()}e Formulierung:"
            )

            try:
                variant = await self.expander._call_ollama(prompt)
                multi_queries[perspective] = variant
            except Exception as e:
                logger.warning(f"⚠️ Multi-Query Generation für '{perspective}' fehlgeschlagen: {e}")
                multi_queries[perspective] = query  # Fallback

        return multi_queries
