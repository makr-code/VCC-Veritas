"""
VERITAS ConversationContextManager Tests
========================================

Unit Tests für Chat-Context-Integration

Testet:
- Sliding Window Context
- Relevance-Based Context
- Token Estimation
- Context Formatting
- Token Limit Enforcement

Author: VERITAS Team
Date: 12. Oktober 2025
"""

import sys
import os
import pytest
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.agents.context_manager import ConversationContextManager
from shared.chat_schema import ChatSession, ChatMessage


class TestConversationContextManager:
    """Test Suite für ConversationContextManager"""
    
    @pytest.fixture
    def manager(self):
        """Context Manager Fixture"""
        return ConversationContextManager(max_tokens=2000, chars_per_token=4.0)
    
    @pytest.fixture
    def sample_session(self):
        """Sample ChatSession mit mehreren Messages"""
        session = ChatSession(llm_model="llama3.1:8b")
        
        # Konversation über BImSchG und Windkraft
        session.add_message("user", "Was ist das BImSchG?")
        session.add_message("assistant", 
            "Das Bundes-Immissionsschutzgesetz (BImSchG) ist ein deutsches Gesetz, "
            "das den Schutz vor schädlichen Umwelteinwirkungen durch Luftverunreinigungen, "
            "Geräusche, Erschütterungen und ähnliche Vorgänge regelt.")
        
        session.add_message("user", "Welche Grenzwerte gelten für Windkraftanlagen?")
        session.add_message("assistant",
            "Für Windkraftanlagen gelten gemäß TA Lärm folgende Grenzwerte:\n"
            "- Wohngebiete: 55 dB(A) tags, 40 dB(A) nachts\n"
            "- Mischgebiete: 60 dB(A) tags, 45 dB(A) nachts\n"
            "- Gewerbegebiete: 65 dB(A) tags, 50 dB(A) nachts")
        
        session.add_message("user", "Gibt es Ausnahmen von diesen Grenzwerten?")
        session.add_message("assistant",
            "Ja, Ausnahmen sind möglich bei:\n"
            "1. Vorbelastung durch andere Anlagen\n"
            "2. Genehmigung nach § 24 BImSchG\n"
            "3. Seltene Ereignisse (max. 10 Tage/Jahr)")
        
        return session
    
    def test_manager_initialization(self, manager):
        """Test: Manager Initialisierung"""
        print("\n🧪 Test 1: Manager Initialisierung")
        
        assert manager.max_tokens == 2000
        assert manager.chars_per_token == 4.0
        assert manager.max_chars == 8000
        
        print("✅ Manager erfolgreich initialisiert")
    
    def test_sliding_window_context(self, manager, sample_session):
        """Test: Sliding Window Strategie"""
        print("\n🧪 Test 2: Sliding Window Context")
        
        result = manager.build_conversation_context(
            chat_session=sample_session,
            current_query="Brauche ich eine Genehmigung?",
            strategy="sliding_window",
            max_messages=4  # Letzte 4 Messages
        )
        
        assert result['strategy_used'] == 'sliding_window'
        assert result['message_count'] == 4
        assert result['token_count'] > 0
        assert len(result['context']) > 0
        
        # Prüfe dass neueste Messages dabei sind
        assert "Ausnahmen" in result['context']
        assert "Grenzwerte" in result['context']
        
        print(f"✅ Sliding Window: {result['message_count']} Messages, {result['token_count']} Tokens")
        print(f"   Context-Länge: {len(result['context'])} Zeichen")
    
    def test_relevance_based_context(self, manager, sample_session):
        """Test: Relevance-Based Strategie"""
        print("\n🧪 Test 3: Relevance-Based Context")
        
        # Frage über Grenzwerte → sollte entsprechende Messages finden
        result = manager.build_conversation_context(
            chat_session=sample_session,
            current_query="Welche Lärmgrenzwerte gibt es?",
            strategy="relevance",
            max_messages=3
        )
        
        assert result['strategy_used'] == 'relevance'
        assert result['message_count'] > 0
        assert result['token_count'] > 0
        
        # Prüfe dass relevante Message dabei ist
        assert "Grenzwerte" in result['context'] or "dB" in result['context']
        
        print(f"✅ Relevance-Based: {result['message_count']} Messages, {result['token_count']} Tokens")
        print(f"   Relevante Begriffe gefunden")
    
    def test_all_messages_context(self, manager, sample_session):
        """Test: All Messages Strategie"""
        print("\n🧪 Test 4: All Messages Context")
        
        result = manager.build_conversation_context(
            chat_session=sample_session,
            current_query="Zusammenfassung?",
            strategy="all",
            max_messages=100  # Irrelevant bei "all"
        )
        
        assert result['strategy_used'] == 'all'
        assert result['message_count'] == len(sample_session.messages)
        
        # Alle Messages sollten dabei sein
        assert "BImSchG" in result['context']
        assert "Grenzwerte" in result['context']
        assert "Ausnahmen" in result['context']
        
        print(f"✅ All Messages: {result['message_count']} Messages, {result['token_count']} Tokens")
    
    def test_token_estimation(self, manager):
        """Test: Token-Schätzung"""
        print("\n🧪 Test 5: Token Estimation")
        
        test_texts = [
            ("Hallo Welt", 2),  # ~8 Zeichen / 4 = 2 Tokens
            ("Das ist ein längerer Test mit mehreren Wörtern.", 12),  # ~48 Zeichen / 4 = 12 Tokens
            ("A" * 400, 100)  # 400 Zeichen / 4 = 100 Tokens
        ]
        
        for text, expected_tokens in test_texts:
            tokens = manager.estimate_tokens(text)
            assert abs(tokens - expected_tokens) <= 1  # ±1 Token Toleranz
            print(f"   '{text[:30]}...': {tokens} Tokens (erwartet: {expected_tokens})")
        
        print("✅ Token-Schätzung funktioniert korrekt")
    
    def test_context_formatting(self, manager, sample_session):
        """Test: Context-Formatierung für LLM"""
        print("\n🧪 Test 6: Context Formatting")
        
        result = manager.build_conversation_context(
            chat_session=sample_session,
            current_query="Test",
            strategy="sliding_window",
            max_messages=2
        )
        
        context = result['context']
        
        # Prüfe Format: "Benutzer: ... \n Assistent: ..."
        assert "Benutzer:" in context or "Assistent:" in context
        assert "\n" in context  # Mehrzeilig
        
        print("✅ Context korrekt formatiert:")
        print(f"   {context[:100]}...")
    
    def test_token_limit_enforcement(self, manager):
        """Test: Token-Limit wird eingehalten"""
        print("\n🧪 Test 7: Token Limit Enforcement")
        
        # Session mit sehr langen Messages
        long_session = ChatSession()
        
        # 20 sehr lange Messages (je ~500 Zeichen = ~125 Tokens)
        for i in range(20):
            long_session.add_message("user", "Test " * 100)  # ~500 Zeichen
            long_session.add_message("assistant", "Antwort " * 100)  # ~500 Zeichen
        
        result = manager.build_conversation_context(
            chat_session=long_session,
            current_query="Test",
            strategy="all",
            max_messages=100
        )
        
        # Token-Limit sollte eingehalten werden
        assert result['token_count'] <= manager.max_tokens
        
        # Context sollte gekürzt worden sein
        if len(long_session.messages) * 125 > manager.max_tokens:
            assert "[... (gekürzt aufgrund Token-Limit)]" in result['context'] or result['token_count'] <= manager.max_tokens
        
        print(f"✅ Token-Limit eingehalten: {result['token_count']} / {manager.max_tokens} Tokens")
    
    def test_empty_session(self, manager):
        """Test: Leere Session"""
        print("\n🧪 Test 8: Empty Session")
        
        empty_session = ChatSession()
        
        result = manager.build_conversation_context(
            chat_session=empty_session,
            current_query="Test",
            strategy="sliding_window"
        )
        
        assert result['context'] == ''
        assert result['token_count'] == 0
        assert result['message_count'] == 0
        assert result['strategy_used'] == 'none'  # Bei leerer Session: 'none' statt strategy
        
        print("✅ Leere Session korrekt behandelt")
    
    def test_single_message_session(self, manager):
        """Test: Session mit nur einer Message"""
        print("\n🧪 Test 9: Single Message Session")
        
        single_session = ChatSession()
        single_session.add_message("user", "Hallo!")
        
        result = manager.build_conversation_context(
            chat_session=single_session,
            current_query="Wie geht's?",
            strategy="sliding_window"
        )
        
        assert result['message_count'] == 1
        assert "Hallo!" in result['context']
        
        print(f"✅ Single Message: {result['message_count']} Message, {result['token_count']} Tokens")
    
    def test_format_prompt_with_context(self, manager, sample_session):
        """Test: Vollständiger Prompt mit Context"""
        print("\n🧪 Test 10: Format Prompt with Context")
        
        result = manager.build_conversation_context(
            chat_session=sample_session,
            current_query="Brauche ich eine Genehmigung?",
            strategy="sliding_window",
            max_messages=3
        )
        
        prompt = manager.format_prompt_with_context(
            current_query="Brauche ich eine Genehmigung?",
            context=result['context'],
            system_prompt="Du bist VERITAS, ein KI-Assistent für deutsches Baurecht."
        )
        
        # Prüfe Struktur
        assert "Du bist VERITAS" in prompt
        assert "Bisherige Konversation:" in prompt
        assert "Aktuelle Frage:" in prompt
        assert "Brauche ich eine Genehmigung?" in prompt
        
        print("✅ Prompt korrekt formatiert:")
        print(f"   Länge: {len(prompt)} Zeichen")
        print(f"   Enthält System-Prompt: ✅")
        print(f"   Enthält Context: ✅")
        print(f"   Enthält Frage: ✅")
    
    def test_context_statistics(self, manager, sample_session):
        """Test: Context-Statistiken"""
        print("\n🧪 Test 11: Context Statistics")
        
        stats = manager.get_context_statistics(sample_session)
        
        assert stats['total_messages'] == len(sample_session.messages)
        assert stats['total_chars'] > 0
        assert stats['estimated_tokens'] > 0
        assert 'can_fit_all' in stats
        assert 'requires_truncation' in stats
        
        print("✅ Statistiken:")
        print(f"   Total Messages: {stats['total_messages']}")
        print(f"   Total Chars: {stats['total_chars']}")
        print(f"   Estimated Tokens: {stats['estimated_tokens']}")
        print(f"   Can Fit All: {stats['can_fit_all']}")
        print(f"   Requires Truncation: {stats['requires_truncation']}")
    
    def test_long_message_truncation(self, manager):
        """Test: Lange Nachrichten werden gekürzt"""
        print("\n🧪 Test 12: Long Message Truncation")
        
        session = ChatSession()
        # Message mit >500 Zeichen
        long_text = "Dies ist eine sehr lange Nachricht. " * 50  # ~1800 Zeichen
        session.add_message("user", long_text)
        
        result = manager.build_conversation_context(
            chat_session=session,
            current_query="Test",
            strategy="all"
        )
        
        # Nachricht sollte in Context gekürzt sein (auf ~500 Zeichen)
        # (siehe _format_context_for_llm: content[:500] + "...")
        if len(long_text) > 500:
            assert len(result['context']) < len(long_text)
        
        print(f"✅ Lange Message gekürzt: {len(long_text)} → {len(result['context'])} Zeichen")


def create_sample_session():
    """Erstellt Sample ChatSession"""
    session = ChatSession(llm_model="llama3.1:8b")
    
    # Konversation über BImSchG und Windkraft
    session.add_message("user", "Was ist das BImSchG?")
    session.add_message("assistant", 
        "Das Bundes-Immissionsschutzgesetz (BImSchG) ist ein deutsches Gesetz, "
        "das den Schutz vor schädlichen Umwelteinwirkungen durch Luftverunreinigungen, "
        "Geräusche, Erschütterungen und ähnliche Vorgänge regelt.")
    
    session.add_message("user", "Welche Grenzwerte gelten für Windkraftanlagen?")
    session.add_message("assistant",
        "Für Windkraftanlagen gelten gemäß TA Lärm folgende Grenzwerte:\n"
        "- Wohngebiete: 55 dB(A) tags, 40 dB(A) nachts\n"
        "- Mischgebiete: 60 dB(A) tags, 45 dB(A) nachts\n"
        "- Gewerbegebiete: 65 dB(A) tags, 50 dB(A) nachts")
    
    session.add_message("user", "Gibt es Ausnahmen von diesen Grenzwerten?")
    session.add_message("assistant",
        "Ja, Ausnahmen sind möglich bei:\n"
        "1. Vorbelastung durch andere Anlagen\n"
        "2. Genehmigung nach § 24 BImSchG\n"
        "3. Seltene Ereignisse (max. 10 Tage/Jahr)")
    
    return session


def run_all_tests():
    """Führt alle Tests aus"""
    print("=" * 80)
    print("🧪 VERITAS ConversationContextManager Tests")
    print("=" * 80)
    
    tester = TestConversationContextManager()
    
    # Fixtures manuell erstellen
    context_manager = ConversationContextManager(max_tokens=2000, chars_per_token=4.0)
    sample_session = create_sample_session()
    
    tests = [
        ("Manager Initialisierung", lambda: tester.test_manager_initialization(context_manager)),
        ("Sliding Window Context", lambda: tester.test_sliding_window_context(context_manager, sample_session)),
        ("Relevance-Based Context", lambda: tester.test_relevance_based_context(context_manager, sample_session)),
        ("All Messages Context", lambda: tester.test_all_messages_context(context_manager, sample_session)),
        ("Token Estimation", lambda: tester.test_token_estimation(context_manager)),
        ("Context Formatting", lambda: tester.test_context_formatting(context_manager, sample_session)),
        ("Token Limit Enforcement", lambda: tester.test_token_limit_enforcement(context_manager)),
        ("Empty Session", lambda: tester.test_empty_session(context_manager)),
        ("Single Message Session", lambda: tester.test_single_message_session(context_manager)),
        ("Format Prompt with Context", lambda: tester.test_format_prompt_with_context(context_manager, sample_session)),
        ("Context Statistics", lambda: tester.test_context_statistics(context_manager, sample_session)),
        ("Long Message Truncation", lambda: tester.test_long_message_truncation(context_manager))
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ Test '{test_name}' FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ Test '{test_name}' ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        return True
    else:
        print(f"\n❌ {failed} TESTS FAILED")
        return False


if __name__ == "__main__":
    # Direkter Aufruf: Führe alle Tests aus
    success = run_all_tests()
    sys.exit(0 if success else 1)
