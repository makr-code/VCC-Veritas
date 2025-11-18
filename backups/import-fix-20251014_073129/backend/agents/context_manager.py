"""
VERITAS Conversation Context Manager
====================================

Verwaltet Chat-History für LLM-Context-Integration.

Features:
- Sliding Window: Neueste N Nachrichten
- Relevance-Based: TF-IDF-Similarity zur aktuellen Frage
- Token Estimation: ~4 Zeichen pro Token
- Max 2000 Tokens für LLM-Context

Version: v3.20.0
Author: VERITAS Team
Date: 12. Oktober 2025
"""

import logging
import math
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConversationContextManager:
    """Verwaltet Konversations-Kontext für LLM"""

    def __init__(self, max_tokens: int = 2000, chars_per_token: float = 4.0):
        """
        Initialisiert Context Manager

        Args:
            max_tokens: Maximale Anzahl Tokens für Context
            chars_per_token: Durchschnittliche Zeichen pro Token
        """
        self.max_tokens = max_tokens
        self.chars_per_token = chars_per_token
        self.max_chars = int(max_tokens * chars_per_token)

        logger.info(f"✅ ConversationContextManager initialisiert (max {max_tokens} tokens)")

    def build_conversation_context(
        self, chat_session, current_query: str, strategy: str = "sliding_window", max_messages: int = 10
    ) -> Dict[str, Any]:
        """
        Erstellt Konversations-Kontext für LLM

        Args:
            chat_session: ChatSession-Objekt
            current_query: Aktuelle User-Frage
            strategy: Strategie ("sliding_window", "relevance", "all")
            max_messages: Max. Anzahl Messages (bei sliding_window)

        Returns:
            Dict mit context, token_count, message_count, strategy_used
        """
        try:
            if not chat_session or not hasattr(chat_session, "messages"):
                return {"context": "", "token_count": 0, "message_count": 0, "strategy_used": "none"}

            messages = chat_session.messages

            if not messages:
                return {"context": "", "token_count": 0, "message_count": 0, "strategy_used": "none"}

            # Wähle Strategie
            if strategy == "sliding_window":
                selected_messages = self._sliding_window_context(messages, max_messages)
            elif strategy == "relevance":
                selected_messages = self._relevance_based_context(messages, current_query, max_messages)
            elif strategy == "all":
                selected_messages = messages
            else:
                logger.warning(f"Unbekannte Strategie: {strategy}, verwende sliding_window")
                selected_messages = self._sliding_window_context(messages, max_messages)

            # Formatiere für LLM
            context = self._format_context_for_llm(selected_messages)

            # Kürze falls zu lang
            if len(context) > self.max_chars:
                context = self._truncate_context(context)

            # Token-Schätzung
            token_count = self.estimate_tokens(context)

            result = {
                "context": context,
                "token_count": token_count,
                "message_count": len(selected_messages),
                "strategy_used": strategy,
            }

            logger.info(f"Context erstellt: {len(selected_messages)} msgs, {token_count} tokens, Strategie: {strategy}")

            return result

        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Kontexts: {e}")
            return {"context": "", "token_count": 0, "message_count": 0, "strategy_used": "error"}

    def _sliding_window_context(self, messages: List, max_messages: int) -> List:
        """
        Sliding Window: Neueste N Nachrichten

        Args:
            messages: Liste aller ChatMessage-Objekte
            max_messages: Max. Anzahl

        Returns:
            Liste der neuesten Messages
        """
        # Nimm die letzten N Nachrichten
        return messages[-max_messages:] if len(messages) > max_messages else messages

    def _relevance_based_context(self, messages: List, current_query: str, max_messages: int) -> List:
        """
        Relevance-Based: TF-IDF-Ähnlichkeit zur aktuellen Frage

        Args:
            messages: Liste aller ChatMessage-Objekte
            current_query: Aktuelle Frage
            max_messages: Max. Anzahl

        Returns:
            Liste der relevantesten Messages
        """
        try:
            # Berechne TF-IDF-Scores für alle Messages
            scored_messages = []

            query_tokens = self._tokenize(current_query.lower())

            for msg in messages:
                if msg.role == "user":  # Nur User-Messages berücksichtigen
                    content_tokens = self._tokenize(msg.content.lower())

                    # Berechne Overlap-Score (einfache TF-IDF-Näherung)
                    score = self._calculate_overlap_score(query_tokens, content_tokens)

                    scored_messages.append((score, msg))

            # Sortiere nach Score (höchster zuerst)
            scored_messages.sort(key=lambda x: x[0], reverse=True)

            # Nimm Top-N
            top_messages = [msg for score, msg in scored_messages[:max_messages]]

            # Sortiere chronologisch
            top_messages.sort(key=lambda x: x.timestamp)

            # Füge auch die zugehörigen Assistant-Antworten hinzu
            result = []
            for msg in messages:
                if msg in top_messages:
                    result.append(msg)
                    # Füge nächste Assistant-Message hinzu falls vorhanden
                    msg_idx = messages.index(msg)
                    if msg_idx + 1 < len(messages) and messages[msg_idx + 1].role == "assistant":
                        result.append(messages[msg_idx + 1])

            return result[: max_messages * 2]  # User + Assistant Pairs

        except Exception as e:
            logger.error(f"Fehler bei Relevance-Based Context: {e}")
            # Fallback zu Sliding Window
            return self._sliding_window_context(messages, max_messages)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenisiert Text in Wörter"""
        # Einfache Tokenisierung: Lowercase + nur Buchstaben/Zahlen
        return re.findall(r"\w+", text.lower())

    def _calculate_overlap_score(self, tokens1: List[str], tokens2: List[str]) -> float:
        """
        Berechnet Overlap-Score zwischen zwei Token-Listen

        Args:
            tokens1: Erste Token-Liste (Query)
            tokens2: Zweite Token-Liste (Message)

        Returns:
            Score (0.0 - 1.0)
        """
        if not tokens1 or not tokens2:
            return 0.0

        # Counter für Häufigkeiten
        counter1 = Counter(tokens1)
        counter2 = Counter(tokens2)

        # Gemeinsame Tokens
        common_tokens = set(counter1.keys()) & set(counter2.keys())

        if not common_tokens:
            return 0.0

        # TF-IDF-ähnlicher Score
        score = sum(min(counter1[token], counter2[token]) for token in common_tokens)

        # Normalisierung
        max_score = math.sqrt(len(tokens1) * len(tokens2))

        return score / max_score if max_score > 0 else 0.0

    def _format_context_for_llm(self, messages: List) -> str:
        """
        Formatiert Messages für LLM-Prompt

        Args:
            messages: Liste von ChatMessage-Objekten

        Returns:
            Formatierter Context-String
        """
        if not messages:
            return ""

        context_lines = []

        for msg in messages:
            # Rolle formatieren
            role = "Benutzer" if msg.role == "user" else "Assistent"

            # Kürze lange Inhalte
            content = msg.content
            if len(content) > 500:
                content = content[:497] + "..."

            # Formatiere als Dialog
            context_lines.append(f"{role}: {content}")

        return "\n".join(context_lines)

    def _truncate_context(self, context: str) -> str:
        """
        Kürzt Context auf max_chars

        Args:
            context: Vollständiger Context

        Returns:
            Gekürzter Context
        """
        if len(context) <= self.max_chars:
            return context

        # Kürze und füge Hinweis hinzu
        truncated = context[: self.max_chars - 50]

        # Finde letzten Satz-Ende
        last_period = truncated.rfind(".")
        if last_period > 0:
            truncated = truncated[: last_period + 1]

        truncated += "\n[... (gekürzt aufgrund Token-Limit)]"

        logger.warning(f"Context gekürzt: {len(context)} → {len(truncated)} Zeichen")

        return truncated

    def estimate_tokens(self, text: str) -> int:
        """
        Schätzt Token-Anzahl für Text

        Args:
            text: Zu schätzender Text

        Returns:
            Geschätzte Token-Anzahl
        """
        return int(len(text) / self.chars_per_token)

    def format_prompt_with_context(self, current_query: str, context: str, system_prompt: Optional[str] = None) -> str:
        """
        Formatiert vollständigen Prompt mit Context

        Args:
            current_query: Aktuelle Frage
            context: Konversations-Context
            system_prompt: Optional System-Prompt

        Returns:
            Vollständiger Prompt für LLM
        """
        parts = []

        # System-Prompt
        if system_prompt:
            parts.append(system_prompt)

        # Context
        if context:
            parts.append("Bisherige Konversation:")
            parts.append(context)
            parts.append("")  # Leerzeile

        # Aktuelle Frage
        parts.append("Aktuelle Frage:")
        parts.append(current_query)

        return "\n".join(parts)

    def get_context_statistics(self, chat_session) -> Dict[str, Any]:
        """
        Gibt Statistiken über Session-Context zurück

        Args:
            chat_session: ChatSession-Objekt

        Returns:
            Dict mit Statistiken
        """
        try:
            if not chat_session or not hasattr(chat_session, "messages"):
                return {"total_messages": 0, "total_chars": 0, "estimated_tokens": 0, "can_fit_all": True}

            messages = chat_session.messages
            total_chars = sum(len(msg.content) for msg in messages)
            estimated_tokens = self.estimate_tokens(self._format_context_for_llm(messages))

            return {
                "total_messages": len(messages),
                "total_chars": total_chars,
                "estimated_tokens": estimated_tokens,
                "can_fit_all": estimated_tokens <= self.max_tokens,
                "requires_truncation": estimated_tokens > self.max_tokens,
            }

        except Exception as e:
            logger.error(f"Fehler bei Context-Statistiken: {e}")
            return {}


# Example Usage
if __name__ == "__main__":
    import os
    import sys

    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)

    from shared.chat_schema import ChatSession

    # Create test session
    session = ChatSession(llm_model="llama3.1:8b")
    session.add_message("user", "Was ist das BImSchG?")
    session.add_message("assistant", "Das Bundes-Immissionsschutzgesetz regelt...", metadata={"confidence": 0.887})
    session.add_message("user", "Welche Grenzwerte gelten?")
    session.add_message("assistant", "Für Windkraftanlagen gelten folgende Grenzwerte...", metadata={"confidence": 0.92})
    session.add_message("user", "Gibt es Ausnahmen?")

    # Initialize manager
    manager = ConversationContextManager(max_tokens=2000)

    # Test 1: Sliding Window
    print("\n📊 Test 1: Sliding Window Context")
    result = manager.build_conversation_context(session, "Gibt es Ausnahmen?", strategy="sliding_window", max_messages=3)
    print(f"Messages: {result['message_count']}")
    print(f"Tokens: {result['token_count']}")
    print(f"Strategy: {result['strategy_used']}")
    print(f"\nContext:\n{result['context'][:200]}...")

    # Test 2: Relevance-Based
    print("\n📊 Test 2: Relevance-Based Context")
    result = manager.build_conversation_context(
        session, "Welche Vorschriften gibt es für Windkraftanlagen?", strategy="relevance", max_messages=3
    )
    print(f"Messages: {result['message_count']}")
    print(f"Tokens: {result['token_count']}")
    print(f"Strategy: {result['strategy_used']}")

    # Test 3: Statistics
    print("\n📊 Test 3: Context Statistics")
    stats = manager.get_context_statistics(session)
    print(f"Total Messages: {stats['total_messages']}")
    print(f"Estimated Tokens: {stats['estimated_tokens']}")
    print(f"Can Fit All: {stats['can_fit_all']}")

    # Test 4: Format Prompt
    print("\n📊 Test 4: Format Prompt with Context")
    prompt = manager.format_prompt_with_context(
        "Gibt es Ausnahmen?", result["context"], system_prompt="Du bist VERITAS, ein KI-Assistent für deutsches Baurecht."
    )
    print(f"Prompt Length: {len(prompt)} chars")
    print(f"Estimated Tokens: {manager.estimate_tokens(prompt)}")
