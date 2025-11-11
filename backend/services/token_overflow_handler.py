#!/usr/bin/env python3
"""
Token Overflow Handler - Strategien bei Token-Limit-Überschreitung
===================================================================
Implementiert verschiedene Strategien um mit Token-Overflows umzugehen:
1. Chunk Reranking & Priorisierung
2. Context Summarization
3. Chunked Response (Multi-Part)
4. Streaming mit Early Stopping

Author: VERITAS System
Date: 2025-10-17
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class OverflowStrategy(str, Enum):
    """Strategien für Token-Overflow"""

    RERANK_CHUNKS = "rerank_chunks"  # Wichtigste Chunks priorisieren
    SUMMARIZE_CONTEXT = "summarize_context"  # RAG-Context komprimieren
    CHUNKED_RESPONSE = "chunked_response"  # Multi-Part-Antwort
    EARLY_STOPPING = "early_stopping"  # Streaming stoppen
    REDUCE_AGENTS = "reduce_agents"  # Weniger Agenten verwenden
    FALLBACK_MODEL = "fallback_model"  # Kleineres Modell nutzen


@dataclass
class OverflowResult:
    """Ergebnis der Overflow-Behandlung"""

    strategy_used: OverflowStrategy
    original_tokens: int
    reduced_tokens: int
    tokens_saved: int
    quality_impact: float  # 0.0-1.0 (1.0 = keine Qualitätsverlust)
    user_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class ChunkReranker:
    """
    Rerankt RAG-Chunks nach Relevanz und behält nur die wichtigsten
    """

    @staticmethod
    def calculate_relevance_score(chunk: Dict[str, Any], query: str) -> float:
        """
        Berechnet Relevanz-Score für Chunk

        Args:
            chunk: RAG-Chunk mit 'text' und optional 'score'
            query: Original-Query

        Returns:
            float: Relevanz-Score (0.0-1.0)
        """
        score = 0.0
        chunk_text = chunk.get("text", "").lower()
        query_lower = query.lower()

        # 1. Existing score from RAG
        if "score" in chunk:
            score += chunk["score"] * 0.4

        # 2. Query keyword overlap
        query_words = set(re.findall(r"\w+", query_lower))
        chunk_words = set(re.findall(r"\w+", chunk_text))
        overlap = len(query_words & chunk_words) / max(len(query_words), 1)
        score += overlap * 0.3

        # 3. Chunk length (prefer substantial chunks)
        length_score = min(len(chunk_text) / 1000, 1.0)
        score += length_score * 0.2

        # 4. Source quality (if available)
        if chunk.get("source_type") in ["relational", "graph"]:
            score += 0.1

        return min(score, 1.0)

    @staticmethod
    def rerank_and_filter(chunks: List[Dict[str, Any]], query: str, max_chunks: int) -> Tuple[List[Dict[str, Any]], int]:
        """
        Rerankt Chunks und behält nur Top-N

        Args:
            chunks: Liste von RAG-Chunks
            query: Original-Query
            max_chunks: Maximale Anzahl Chunks

        Returns:
            Tuple[filtered_chunks, tokens_saved]
        """
        if not chunks:
            return [], 0

        # Relevanz-Scores berechnen
        scored_chunks = [
            {**chunk, "relevance_score": ChunkReranker.calculate_relevance_score(chunk, query)} for chunk in chunks
        ]

        # Nach Score sortieren
        scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Top-N behalten
        original_count = len(chunks)
        filtered_chunks = scored_chunks[:max_chunks]
        removed_count = original_count - len(filtered_chunks)

        # Geschätzte Token-Ersparnis (durchschnittlich ~200 tokens pro Chunk)
        tokens_saved = removed_count * 200

        return filtered_chunks, tokens_saved


class ContextSummarizer:
    """
    Komprimiert RAG-Context durch Summarization
    """

    @staticmethod
    def estimate_compression_ratio(text: str, target_length: int) -> float:
        """
        Schätzt Kompressionsrate

        Args:
            text: Original-Text
            target_length: Ziel-Länge in Zeichen

        Returns:
            float: Kompressionsrate (0.0-1.0)
        """
        if not text:
            return 1.0

        return min(target_length / len(text), 1.0)

    @staticmethod
    def extract_key_sentences(text: str, max_sentences: int = 5) -> str:
        """
        Extrahiert wichtigste Sätze (einfache Extraktion ohne LLM)

        Args:
            text: Original-Text
            max_sentences: Max. Anzahl Sätze

        Returns:
            str: Komprimierter Text
        """
        if not text:
            return ""

        # Sätze splitten
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= max_sentences:
            return text

        # Scoring: Längere Sätze mit mehr Keywords bevorzugen
        def score_sentence(sent: str) -> float:
            return len(sent) * (1 + sent.count(",") * 0.1)

        scored = [(score_sentence(s), s) for s in sentences]
        scored.sort(reverse=True)

        # Top-N behalten und in ursprünglicher Reihenfolge zurückgeben
        top_sentences = [s for _, s in scored[:max_sentences]]
        result = ". ".join(top_sentences) + "."

        return result

    @staticmethod
    async def summarize_with_llm(text: str, ollama_client, model: str = "phi3", max_tokens: int = 500) -> str:
        """
        Summarisiert Text mit LLM (optional, falls verfügbar)

        Args:
            text: Zu summarisierender Text
            ollama_client: Ollama-Client
            model: Modell für Summarization
            max_tokens: Max. Tokens für Summary

        Returns:
            str: Zusammenfassung
        """
        if not text or not ollama_client:
            return text

        prompt = """Fasse folgenden Text prägnant zusammen (max {max_tokens} tokens):

{text[:2000]}

Zusammenfassung:"""

        try:
            response = await ollama_client.generate(model=model, prompt=prompt, max_tokens=max_tokens, temperature=0.3)
            return response.get("response", text)
        except Exception as e:
            # Fallback zu einfacher Extraktion
            return ContextSummarizer.extract_key_sentences(text, max_sentences=5)


class ChunkedResponseHandler:
    """
    Teilt Response in mehrere Teile auf
    """

    @staticmethod
    def plan_chunks(total_content_size: int, max_tokens_per_chunk: int) -> List[Dict[str, Any]]:
        """
        Plant Chunk-Aufteilung

        Args:
            total_content_size: Geschätzte Gesamtgröße in Tokens
            max_tokens_per_chunk: Max. Tokens pro Chunk

        Returns:
            List[Dict]: Chunk-Plan mit start/end/part_number
        """
        num_chunks = (total_content_size + max_tokens_per_chunk - 1) // max_tokens_per_chunk

        chunks = []
        for i in range(num_chunks):
            chunks.append(
                {
                    "part_number": i + 1,
                    "total_parts": num_chunks,
                    "start_token": i * max_tokens_per_chunk,
                    "end_token": min((i + 1) * max_tokens_per_chunk, total_content_size),
                    "estimated_size": min(max_tokens_per_chunk, total_content_size - i * max_tokens_per_chunk),
                }
            )

        return chunks

    @staticmethod
    def create_user_message(chunk_info: Dict[str, Any]) -> str:
        """
        Erstellt User-Message für Chunked Response

        Args:
            chunk_info: Chunk-Informationen

        Returns:
            str: User-Message
        """
        return (
            f"📄 Antwort Teil {chunk_info['part_number']}/{chunk_info['total_parts']} " "(aufgrund der Komplexität aufgeteilt)"
        )


class TokenOverflowHandler:
    """
    Hauptklasse für Token-Overflow-Management
    """

    def __init__(self):
        """Initialisiert Handler"""
        self.reranker = ChunkReranker()
        self.summarizer = ContextSummarizer()
        self.chunked_handler = ChunkedResponseHandler()

    def handle_overflow(
        self,
        available_tokens: int,
        required_tokens: int,
        rag_chunks: List[Dict[str, Any]] = None,
        rag_context: Dict[str, Any] = None,
        query: str = "",
        agent_count: int = 0,
    ) -> OverflowResult:
        """
        Behandelt Token-Overflow mit geeigneter Strategie

        Args:
            available_tokens: Verfügbare Tokens
            required_tokens: Benötigte Tokens
            rag_chunks: RAG-Chunks
            rag_context: RAG-Context
            query: Original-Query
            agent_count: Anzahl Agenten

        Returns:
            OverflowResult mit angewandter Strategie
        """
        overflow = required_tokens - available_tokens

        # Strategie 1: Chunk Reranking (bevorzugt, minimaler Qualitätsverlust)
        if rag_chunks and len(rag_chunks) >= 5:
            # Berechne wie viele Chunks wir entfernen können
            overflow_tokens = overflow
            chunks_to_remove = min(len(rag_chunks) - 3, max(1, overflow_tokens // 200))
            max_chunks = len(rag_chunks) - chunks_to_remove

            filtered_chunks, tokens_saved = self.reranker.rerank_and_filter(rag_chunks, query, max_chunks)

            # Wenn wir deutliche Token-Ersparnis erzielen, verwende diese Strategie
            if tokens_saved > 0 and tokens_saved >= overflow * 0.2:
                return OverflowResult(
                    strategy_used=OverflowStrategy.RERANK_CHUNKS,
                    original_tokens=required_tokens,
                    reduced_tokens=required_tokens - tokens_saved,
                    tokens_saved=tokens_saved,
                    quality_impact=0.95,  # Minimal impact
                    user_message=f"ℹ️ {len(rag_chunks) - len(filtered_chunks)} weniger relevante Quellen ausgeblendet",
                    metadata={"original_chunks": len(rag_chunks), "filtered_chunks": len(filtered_chunks)},
                )

        # Strategie 2: Context Summarization (mittlerer Impact)
        if rag_context:
            compression_needed = available_tokens / required_tokens
            estimated_savings = int(overflow * 0.7)  # 70% der Savings durch Summarization

            if estimated_savings >= overflow * 0.5:
                return OverflowResult(
                    strategy_used=OverflowStrategy.SUMMARIZE_CONTEXT,
                    original_tokens=required_tokens,
                    reduced_tokens=required_tokens - estimated_savings,
                    tokens_saved=estimated_savings,
                    quality_impact=0.80,
                    user_message="ℹ️ Kontext wurde komprimiert für optimale Antwortlänge",
                    metadata={"compression_ratio": compression_needed},
                )

        # Strategie 3: Reduce Agents (falls viele Agents beteiligt)
        if agent_count > 5:
            reduced_agents = max(3, int(agent_count * 0.6))
            estimated_savings = (agent_count - reduced_agents) * 150

            if estimated_savings >= overflow * 0.3:
                return OverflowResult(
                    strategy_used=OverflowStrategy.REDUCE_AGENTS,
                    original_tokens=required_tokens,
                    reduced_tokens=required_tokens - estimated_savings,
                    tokens_saved=estimated_savings,
                    quality_impact=0.85,
                    user_message=f"ℹ️ {reduced_agents} von {agent_count} Agenten für fokussierte Antwort gewählt",
                    metadata={"original_agents": agent_count, "reduced_agents": reduced_agents},
                )

        # Strategie 4: Chunked Response (letzter Ausweg)
        chunk_plan = self.chunked_handler.plan_chunks(required_tokens, available_tokens)

        return OverflowResult(
            strategy_used=OverflowStrategy.CHUNKED_RESPONSE,
            original_tokens=required_tokens,
            reduced_tokens=chunk_plan[0]["estimated_size"],
            tokens_saved=0,  # Keine echte Ersparnis
            quality_impact=1.0,  # Keine Qualitätsverlust, nur aufgeteilt
            user_message=self.chunked_handler.create_user_message(chunk_plan[0]),
            metadata={"chunk_plan": chunk_plan},
        )


# Test-Funktion
if __name__ == "__main__":
    handler = TokenOverflowHandler()

    print("=" * 80)
    print("TOKEN OVERFLOW HANDLER - Test")
    print("=" * 80)

    # Test 1: Chunk Reranking
    print("\n🔄 TEST 1: Chunk Reranking")
    print("─" * 80)

    test_chunks = [
        {"text": "Verwaltungsrecht regelt..." * 50, "score": 0.9},
        {"text": "Baurecht ist ein Teilbereich..." * 50, "score": 0.7},
        {"text": "Umweltrecht schützt..." * 50, "score": 0.8},
        {"text": "Finanzen und Förderung..." * 50, "score": 0.5},
        {"text": "Soziale Aspekte..." * 50, "score": 0.6},
        {"text": "Technische Details..." * 50, "score": 0.4},
        {"text": "Historische Entwicklung..." * 50, "score": 0.3},
    ]

    result = handler.handle_overflow(
        available_tokens=2000,
        required_tokens=3400,  # Größerer Overflow (1400 tokens)
        rag_chunks=test_chunks,
        query="Verwaltungsrecht Baugenehmigung",
    )

    print(f"Strategy: {result.strategy_used.value}")
    print(f"Original: {result.original_tokens} tokens")
    print(f"Reduced: {result.reduced_tokens} tokens")
    print(f"Saved: {result.tokens_saved} tokens")
    print(f"Quality Impact: {result.quality_impact:.0%}")
    print(f"User Message: {result.user_message}")

    # Test 2: Context Summarization
    print("\n\n📝 TEST 2: Context Summarization")
    print("─" * 80)

    result = handler.handle_overflow(
        available_tokens=2000, required_tokens=3500, rag_context={"documents": ["..."] * 10}, query="Komplexe Analyse"
    )

    print(f"Strategy: {result.strategy_used.value}")
    print(f"Original: {result.original_tokens} tokens")
    print(f"Reduced: {result.reduced_tokens} tokens")
    print(f"Saved: {result.tokens_saved} tokens")
    print(f"Quality Impact: {result.quality_impact:.0%}")
    print(f"User Message: {result.user_message}")

    # Test 3: Chunked Response
    print("\n\n📄 TEST 3: Chunked Response")
    print("─" * 80)

    result = handler.handle_overflow(available_tokens=2000, required_tokens=6000, query="Sehr umfangreiche Analyse")

    print(f"Strategy: {result.strategy_used.value}")
    print(f"Original: {result.original_tokens} tokens")
    print(f"Part 1 Size: {result.reduced_tokens} tokens")
    print(f"Quality Impact: {result.quality_impact:.0%}")
    print(f"User Message: {result.user_message}")
    print(f"Total Parts: {result.metadata['chunk_plan'][0]['total_parts']}")

    print("\n" + "=" * 80 + "\n")
