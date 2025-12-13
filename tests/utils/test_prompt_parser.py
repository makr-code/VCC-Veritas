"""
Tests for Enhanced Prompt Parser
================================

Tests für den Prompt-Parser mit Steuerzeichen-Unterstützung.

Author: VERITAS System
Date: 2025-12-13
"""

import pytest
from backend.utils.prompt_parser import (
    PromptParser,
    ParsedPrompt,
    get_prompt_parser,
    parse_prompt,
    get_routing_info,
    ControlCharacter,
    AgentType,
    CommandType
)


class TestPromptParser:
    """Test cases for PromptParser"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.parser = PromptParser()
    
    def test_simple_text_no_controls(self):
        """Test parsing simple text without control characters"""
        result = self.parser.parse("Erstelle eine Präsentation über Naturschutz")
        
        assert result.original_text == "Erstelle eine Präsentation über Naturschutz"
        assert result.clean_text == "Erstelle eine Präsentation über Naturschutz"
        assert result.agent is None
        assert len(result.templates) == 0
        assert result.command is None
    
    def test_agent_mention(self):
        """Test @agent mention parsing"""
        result = self.parser.parse("@powerpoint Erstelle eine Präsentation")
        
        assert result.agent == "powerpoint"
        assert result.agent_type == "presentation"
        assert result.endpoint == "/api/office/presentations/generate"
        assert result.clean_text == "Erstelle eine Präsentation"
    
    def test_template_hashtag(self):
        """Test #template hashtag parsing"""
        result = self.parser.parse("Erstelle #flowchart für Genehmigungsprozess")
        
        assert "flowchart" in result.templates
        assert result.clean_text == "Erstelle für Genehmigungsprozess"
    
    def test_multiple_templates(self):
        """Test multiple #templates"""
        result = self.parser.parse("#flowchart #process Erstelle Diagramm")
        
        assert "flowchart" in result.templates
        assert "process" in result.templates
        assert len(result.templates) == 2
    
    def test_command_parsing(self):
        """Test /command parsing"""
        result = self.parser.parse("/list alle Templates")
        
        assert result.command == "list"
        assert result.clean_text == "alle Templates"
    
    def test_priority_parsing(self):
        """Test !priority parsing"""
        result = self.parser.parse("!urgent E-Mail senden")
        
        assert result.priority == "urgent"
        assert result.clean_text == "E-Mail senden"
    
    def test_format_parsing(self):
        """Test $format parsing"""
        result = self.parser.parse("Export als $pdf bitte")
        
        assert result.output_format == "pdf"
        assert result.clean_text == "Export als bitte"
    
    def test_tags_parsing(self):
        """Test +tags parsing"""
        result = self.parser.parse("Dokument +confidential +draft erstellen")
        
        assert "confidential" in result.tags
        assert "draft" in result.tags
        assert len(result.tags) == 2
    
    def test_combined_controls(self):
        """Test combination of multiple control characters"""
        result = self.parser.parse("@powerpoint #flowchart $pdf !urgent +draft Genehmigungsprozess")
        
        assert result.agent == "powerpoint"
        assert "flowchart" in result.templates
        assert result.output_format == "pdf"
        assert result.priority == "urgent"
        assert "draft" in result.tags
        assert result.clean_text == "Genehmigungsprozess"
    
    def test_routing_info(self):
        """Test routing information extraction"""
        text = "@powerpoint #flowchart $pdf Prozess erstellen"
        routing = self.parser.get_routing_info(text)
        
        assert routing["agent_type"] == "presentation"
        assert routing["endpoint"] == "/api/office/presentations/generate"
        assert "flowchart" in routing["templates"]
        assert routing["output_format"] == "pdf"
        assert "Prozess erstellen" in routing["clean_query"]
    
    def test_to_dict(self):
        """Test ParsedPrompt to_dict conversion"""
        result = self.parser.parse("@powerpoint #flowchart Test")
        data = result.to_dict()
        
        assert isinstance(data, dict)
        assert data["agent"] == "powerpoint"
        assert "flowchart" in data["templates"]
        assert "endpoint" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
