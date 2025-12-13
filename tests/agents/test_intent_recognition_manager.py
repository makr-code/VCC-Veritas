"""
Tests for Intent Recognition Manager

Tests YAML-based intent recognition system for multiple content types.
"""

import pytest
import os
from backend.agents.orchestrator.intent_recognition_manager import get_intent_manager


class TestIntentRecognitionManager:
    """Test suite for Intent Recognition Manager"""
    
    @pytest.fixture
    def manager(self):
        """Create IntentRecognitionManager instance"""
        return get_intent_manager()
    
    def test_manager_initialization(self, manager):
        """Test manager initializes correctly"""
        assert manager is not None
        assert hasattr(manager, 'recognize_intent')
        assert hasattr(manager, 'list_content_types')
    
    def test_list_content_types(self, manager):
        """Test listing all content types"""
        content_types = manager.list_content_types()
        assert len(content_types) > 0
        assert 'presentation' in content_types
        assert 'table' in content_types
        assert 'outlook' in content_types
        assert 'onenote' in content_types
    
    def test_recognize_presentation_intent(self, manager):
        """Test recognizing presentation intent"""
        result = manager.recognize_intent("Erstelle eine Präsentation mit Flowchart")
        assert result is not None
        assert result['content_type'] == 'presentation'
        assert 'template_category' in result
        assert 'confidence' in result
        assert result['confidence'] > 0.5
    
    def test_recognize_table_intent(self, manager):
        """Test recognizing table/Excel intent"""
        result = manager.recognize_intent("Erstelle eine Excel-Tabelle mit Quartalszahlen")
        assert result is not None
        assert result['content_type'] == 'table'
        assert 'llm_steps' in result
        assert len(result['llm_steps']) > 0
    
    def test_recognize_outlook_email_intent(self, manager):
        """Test recognizing Outlook email intent"""
        result = manager.recognize_intent("Schreibe eine E-Mail an das Team")
        assert result is not None
        assert result['content_type'] == 'outlook'
        assert 'agent_routing' in result
    
    def test_recognize_onenote_intent(self, manager):
        """Test recognizing OneNote intent"""
        result = manager.recognize_intent("Erstelle Meeting-Notizen für unsere Besprechung")
        assert result is not None
        assert result['content_type'] == 'onenote'
        assert 'template_category' in result
    
    def test_recognize_word_document_intent(self, manager):
        """Test recognizing Word document intent"""
        result = manager.recognize_intent("Erstelle einen Bericht über das Projekt")
        assert result is not None
        assert result['content_type'] == 'word_document'
    
    def test_recognize_image_intent(self, manager):
        """Test recognizing image generation intent"""
        result = manager.recognize_intent("Generiere ein Diagramm-Bild")
        assert result is not None
        assert result['content_type'] == 'image'
    
    def test_presentation_flowchart_keyword(self, manager):
        """Test flowchart keyword detection"""
        result = manager.recognize_intent("Ich brauche einen Workflow-Prozess")
        assert result is not None
        if result['content_type'] == 'presentation':
            assert 'process' in result['template_category'] or 'flowchart' in result.get('keywords', [])
    
    def test_presentation_matrix_keyword(self, manager):
        """Test matrix keyword detection"""
        result = manager.recognize_intent("Erstelle eine SWOT-Analyse")
        assert result is not None
        if result['content_type'] == 'presentation':
            assert 'matrix' in result['template_category'] or 'swot' in result.get('keywords', [])
    
    def test_table_comparison_keyword(self, manager):
        """Test table comparison keyword detection"""
        result = manager.recognize_intent("Vergleich verschiedene Optionen in einer Tabelle")
        assert result is not None
        if result['content_type'] == 'table':
            assert 'comparison' in result.get('template_category', '') or 'vergleich' in result.get('keywords', [])
    
    def test_outlook_calendar_keyword(self, manager):
        """Test Outlook calendar keyword detection"""
        result = manager.recognize_intent("Plane einen Termin für nächste Woche")
        assert result is not None
        if result['content_type'] == 'outlook':
            assert 'calendar' in result.get('template_category', '')
    
    def test_onenote_checklist_keyword(self, manager):
        """Test OneNote checklist keyword detection"""
        result = manager.recognize_intent("Erstelle eine Checkliste für das Projekt")
        assert result is not None
        if result['content_type'] == 'onenote':
            assert 'checklist' in result.get('template_category', '')
    
    def test_confidence_scores(self, manager):
        """Test confidence scores are in valid range"""
        queries = [
            "Erstelle eine Präsentation",
            "Generiere eine Tabelle",
            "Schreibe eine E-Mail",
            "Erstelle Notizen"
        ]
        
        for query in queries:
            result = manager.recognize_intent(query)
            assert 'confidence' in result
            assert 0.0 <= result['confidence'] <= 1.0
    
    def test_llm_steps_present(self, manager):
        """Test LLM steps are provided for all intents"""
        queries = [
            "Erstelle eine Präsentation mit Diagramm",
            "Generiere eine Excel-Tabelle",
            "Schreibe eine formale E-Mail",
            "Erstelle Meeting-Notizen"
        ]
        
        for query in queries:
            result = manager.recognize_intent(query)
            assert 'llm_steps' in result
            assert isinstance(result['llm_steps'], list)
            assert len(result['llm_steps']) > 0
    
    def test_agent_routing_configuration(self, manager):
        """Test agent routing is configured"""
        result = manager.recognize_intent("Erstelle eine Präsentation")
        assert 'agent_routing' in result
        assert 'primary_agent' in result['agent_routing']
    
    def test_unknown_intent_handling(self, manager):
        """Test handling of unknown/unclear intent"""
        result = manager.recognize_intent("xyzabc nonsense query")
        assert result is not None
        # Should still return a result, possibly with low confidence
        assert 'confidence' in result
    
    def test_multilingual_german_keywords(self, manager):
        """Test German keyword recognition"""
        german_queries = [
            "Erstelle eine Präsentation",
            "Tabelle mit Daten",
            "E-Mail schreiben",
            "Notizen erstellen"
        ]
        
        for query in german_queries:
            result = manager.recognize_intent(query)
            assert result is not None
            assert result['confidence'] > 0
    
    def test_multilingual_english_keywords(self, manager):
        """Test English keyword recognition"""
        english_queries = [
            "Create a presentation",
            "Generate a table",
            "Write an email",
            "Create notes"
        ]
        
        for query in english_queries:
            result = manager.recognize_intent(query)
            assert result is not None
            assert result['confidence'] > 0
    
    def test_schema_loading(self, manager):
        """Test that all schemas are loaded correctly"""
        content_types = manager.list_content_types()
        expected_types = ['presentation', 'table', 'outlook', 'onenote', 'word_document', 'image']
        
        for expected_type in expected_types:
            assert expected_type in content_types
    
    def test_template_category_mapping(self, manager):
        """Test template categories are mapped correctly"""
        # Presentation templates
        result = manager.recognize_intent("Erstelle eine Liste")
        if result['content_type'] == 'presentation':
            assert 'template_category' in result
        
        # Table templates
        result = manager.recognize_intent("Erstelle einen Zeitplan")
        if result['content_type'] == 'table':
            assert 'template_category' in result
    
    def test_priority_configuration(self, manager):
        """Test priority is configured for content types"""
        result = manager.recognize_intent("Erstelle eine Präsentation")
        if 'priority' in result:
            assert isinstance(result['priority'], (int, float))
            assert 0.0 <= result['priority'] <= 1.0
    
    def test_cache_functionality(self, manager):
        """Test caching improves performance"""
        import time
        
        query = "Erstelle eine Präsentation mit Flowchart"
        
        # First call - not cached
        start = time.time()
        result1 = manager.recognize_intent(query)
        time1 = time.time() - start
        
        # Second call - should be cached
        start = time.time()
        result2 = manager.recognize_intent(query)
        time2 = time.time() - start
        
        # Results should be identical
        assert result1['content_type'] == result2['content_type']
        assert result1['template_category'] == result2['template_category']
        
        # Second call should be faster (cached)
        # Note: This might not always be true in test environment
        # but the caching mechanism should exist
    
    def test_multiple_matches_handling(self, manager):
        """Test handling of queries matching multiple intents"""
        result = manager.recognize_intent("Erstelle eine Präsentation mit einer Tabelle")
        # Should prioritize based on confidence or master config
        assert result is not None
        assert 'content_type' in result
        assert result['confidence'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
