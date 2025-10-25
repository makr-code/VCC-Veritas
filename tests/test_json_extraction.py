"""
Test-Script für JSON-Extraktion aus LLM-Antworten
==================================================

Testet:
1. JSON-Extraktion mit verschiedenen Formaten
2. Template-Escaping (.format() mit JSON-Beispielen)
3. dirtyjson Robustheit
4. Edge Cases (Whitespace, Newlines, etc.)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import pytest
from backend.utils.json_extractor import (
    extract_json_from_text,
    extract_next_steps,
    extract_related_topics,
    format_next_steps_as_markdown
)


class TestJSONExtraction:
    """Tests für JSON-Extraktion aus LLM-Antworten"""
    
    def test_json_in_code_block(self):
        """Test: JSON in Markdown Code-Block"""
        text = """Das BImSchG regelt den Immissionsschutz.

```json
{
  "next_steps": [
    {"action": "Gesetz prüfen", "type": "document"}
  ],
  "related_topics": ["Umweltschutz", "Lärmschutz"]
}
```"""
        
        clean_text, metadata = extract_json_from_text(text)
        
        assert clean_text.strip() == "Das BImSchG regelt den Immissionsschutz."
        assert metadata is not None
        assert "next_steps" in metadata
        assert len(metadata["next_steps"]) == 1
        assert metadata["next_steps"][0]["action"] == "Gesetz prüfen"
        assert "related_topics" in metadata
        assert len(metadata["related_topics"]) == 2
    
    def test_json_at_end(self):
        """Test: JSON ohne Code-Block am Ende"""
        text = """Das BImSchG regelt den Immissionsschutz.

{"next_steps": [{"action": "Test", "type": "info"}], "related_topics": ["A", "B"]}"""
        
        clean_text, metadata = extract_json_from_text(text)
        
        assert clean_text.strip() == "Das BImSchG regelt den Immissionsschutz."
        assert metadata is not None
        assert "next_steps" in metadata
    
    def test_no_json(self):
        """Test: Text ohne JSON"""
        text = "Das BImSchG regelt den Immissionsschutz in Deutschland."
        
        clean_text, metadata = extract_json_from_text(text)
        
        assert clean_text == text
        assert metadata is None
    
    def test_malformed_json_with_dirtyjson(self):
        """Test: Fehlerhaftes JSON (trailing commas) mit dirtyjson"""
        text = """Antwort zum BImSchG.

```json
{
  "next_steps": [
    {"action": "Test", "type": "info"},
  ],
  "related_topics": ["A", "B",]
}
```"""
        
        clean_text, metadata = extract_json_from_text(text)
        
        # dirtyjson sollte trailing commas akzeptieren
        assert metadata is not None
        assert "next_steps" in metadata
    
    def test_json_with_newlines_in_values(self):
        """Test: JSON mit Newlines in String-Werten"""
        text = """Hier die Antwort.

```json
{
  "next_steps": [
    {"action": "Schritt 1:\nPrüfen", "type": "info"}
  ],
  "related_topics": ["Thema"]
}
```"""
        
        clean_text, metadata = extract_json_from_text(text)
        
        assert metadata is not None
        assert "\n" in metadata["next_steps"][0]["action"]
    
    def test_multiple_json_blocks(self):
        """Test: Mehrere JSON-Blöcke (letzter wird genommen)"""
        text = """Zwischenergebnis:
```json
{"test": "ignore"}
```

Finale Antwort:
```json
{
  "next_steps": [{"action": "Final", "type": "info"}],
  "related_topics": ["Final"]
}
```"""
        
        clean_text, metadata = extract_json_from_text(text)
        
        assert metadata is not None
        assert metadata["next_steps"][0]["action"] == "Final"
    
    def test_extract_next_steps(self):
        """Test: next_steps Extraktion"""
        json_data = {
            "next_steps": [
                {"action": "Action 1", "type": "link"},
                {"action": "Action 2", "type": "info"}
            ],
            "other": "data"
        }
        
        steps = extract_next_steps(json_data)
        
        assert steps is not None
        assert len(steps) == 2
        assert steps[0]["action"] == "Action 1"
    
    def test_extract_related_topics(self):
        """Test: related_topics Extraktion"""
        json_data = {
            "related_topics": ["Topic A", "Topic B", "Topic C"],
            "other": "data"
        }
        
        topics = extract_related_topics(json_data)
        
        assert topics is not None
        assert len(topics) == 3
        assert "Topic A" in topics
    
    def test_format_next_steps_markdown(self):
        """Test: Markdown-Formatierung von next_steps"""
        steps = [
            {"action": "Prüfen Sie das Gesetz", "type": "document"},
            {"action": "Beratung vereinbaren", "type": "link"},
            {"action": "Weitere Infos", "type": "info"}
        ]
        
        markdown = format_next_steps_as_markdown(steps)
        
        assert "📄" in markdown  # document icon
        assert "🔗" in markdown  # link icon
        assert "ℹ️" in markdown  # info icon
        assert "Prüfen Sie das Gesetz" in markdown


class TestTemplateEscaping:
    """Tests für Python .format() Template-Escaping"""
    
    def test_template_with_json_example(self):
        """Test: Template mit JSON-Beispiel ({{ }} escaping)"""
        # Template wie in veritas_ollama_client.py
        template = """Antwort mit JSON am Ende:

```json
{{
  "next_steps": [
    {{"action": "Test", "type": "link"}}
  ],
  "related_topics": ["Topic"]
}}
```

Query: {query}"""
        
        # Sollte NICHT fehlschlagen mit KeyError
        try:
            result = template.format(query="Was ist BImSchG?")
            assert "Was ist BImSchG?" in result
            assert '{"action": "Test"' in result  # Escaping wurde aufgelöst
        except KeyError as e:
            pytest.fail(f"Template-Escaping fehlgeschlagen: {e}")
    
    def test_template_without_escaping_fails(self):
        """Test: Template OHNE Escaping schlägt fehl"""
        template = """Beispiel:
```json
{
  "next_steps": [{"action": "Test"}]
}
```
Query: {query}"""
        
        # Sollte KeyError werfen wegen unescaped {
        with pytest.raises(KeyError):
            template.format(query="Test")
    
    def test_complex_template_escaping(self):
        """Test: Komplexes Template mit mehreren JSON-Beispielen"""
        template = """
**Beispiel 1:**
```json
{{
  "next_steps": [{{"action": "A", "type": "link"}}],
  "related_topics": ["X", "Y"]
}}
```

**Beispiel 2:**
```json
{{
  "next_steps": [{{"action": "B", "type": "info"}}]
}}
```

**Query:** {query}
**Context:** {context}
"""
        
        try:
            result = template.format(
                query="Test-Query",
                context="Test-Context"
            )
            assert "Test-Query" in result
            assert "Test-Context" in result
            assert '"action": "A"' in result
            assert '"action": "B"' in result
        except KeyError as e:
            pytest.fail(f"Multi-JSON Template-Escaping fehlgeschlagen: {e}")


class TestEdgeCases:
    """Tests für Edge Cases und Fehlerbehandlung"""
    
    def test_empty_string(self):
        """Test: Leerer String"""
        clean_text, metadata = extract_json_from_text("")
        assert clean_text == ""
        assert metadata is None
    
    def test_only_json(self):
        """Test: Nur JSON ohne Text"""
        text = '{"next_steps": [], "related_topics": []}'
        clean_text, metadata = extract_json_from_text(text)
        
        assert clean_text.strip() == ""
        assert metadata is not None
    
    def test_invalid_json_structure(self):
        """Test: JSON mit falscher Struktur"""
        text = """Antwort.
```json
{"wrong": "structure", "no_next_steps": true}
```"""
        
        clean_text, metadata = extract_json_from_text(text)
        
        # JSON wird extrahiert, aber next_steps/related_topics fehlen
        assert metadata is not None
        assert extract_next_steps(metadata) is None
        assert extract_related_topics(metadata) is None
    
    def test_nested_json_in_text(self):
        """Test: JSON-ähnlicher Text (nicht extrahiert)"""
        text = 'Die Struktur {"key": "value"} ist ein Beispiel.'
        clean_text, metadata = extract_json_from_text(text)
        
        # Kurze JSON-Snippets im Fließtext sollten ignoriert werden
        assert metadata is None or "next_steps" not in metadata
    
    def test_unicode_in_json(self):
        """Test: Unicode-Zeichen in JSON"""
        text = """Antwort mit Umlauten.

```json
{
  "next_steps": [
    {"action": "Prüfen Sie § 22 BImSchG", "type": "document"}
  ],
  "related_topics": ["Lärmschutz", "Umweltschutz", "Genehmigungsverfahren"]
}
```"""
        
        clean_text, metadata = extract_json_from_text(text)
        
        assert metadata is not None
        assert "§" in metadata["next_steps"][0]["action"]
        assert "Lärmschutz" in metadata["related_topics"]


def run_all_tests():
    """Führt alle Tests aus und gibt Report aus"""
    print("\n" + "="*70)
    print(" VERITAS JSON-Extraktion Test Suite")
    print("="*70 + "\n")
    
    # Run pytest programmatically
    exit_code = pytest.main([
        __file__,
        "-v",  # verbose
        "--tb=short",  # short traceback
        "--color=yes",  # colored output
        "-W", "ignore::DeprecationWarning"  # ignore deprecation warnings
    ])
    
    return exit_code


if __name__ == "__main__":
    exit_code = run_all_tests()
    
    print("\n" + "="*70)
    if exit_code == 0:
        print(" ✅ ALLE TESTS BESTANDEN")
    else:
        print(" ❌ TESTS FEHLGESCHLAGEN")
    print("="*70 + "\n")
    
    sys.exit(exit_code)
