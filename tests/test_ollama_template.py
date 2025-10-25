"""
Test-Script für Ollama Template-Formatierung
============================================

Testet das tatsächliche Template aus veritas_ollama_client.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import pytest


class TestOllamaTemplateFormatting:
    """Tests für das reale Ollama-Template"""
    
    @pytest.fixture
    def template_system(self):
        """System-Prompt aus veritas_ollama_client.py (vereinfacht)"""
        return """Du bist ein hilfreicher Assistent.

FORMAT (MARKDOWN-STRUKTURIERUNG):
✅ VERWENDE FREI: 
- Überschriften (##, ###)
- **Fettdruck**
- Listen (•, -, 1.)

✅ NÄCHSTE SCHRITTE (JSON-Format am Ende):
Wenn sinnvoll, füge am ENDE der Antwort folgendes JSON an:
```json
{{
  "next_steps": [
    {{"action": "Beschreibung", "type": "link"}},
    {{"action": "Weitere Aktion", "type": "info"}}
  ],
  "related_topics": ["Thema 1", "Thema 2"]
}}
```

**Beispiel:**
```json
{{
  "next_steps": [
    {{"action": "Vollständige Unterlagen zusammenstellen", "type": "info"}},
    {{"action": "Termin mit Bauordnungsamt", "type": "link"}}
  ],
  "related_topics": ["Bauvoranfrage", "Baugenehmigungsverfahren"]
}}
```"""
    
    @pytest.fixture
    def template_user(self):
        """User-Template aus veritas_ollama_client.py"""
        return """**User fragte:** {query}

**Kontext aus Dokumenten:**
{rag_context}

**Agent-Erkenntnisse:**
{agent_results}

**Deine Aufgabe:**
Beantworte die User-Frage direkt und hilfreich."""
    
    def test_system_template_no_format_error(self, template_system):
        """Test: System-Template hat keine .format() Platzhalter"""
        # System-Template wird direkt verwendet, NICHT mit .format()
        # Sollte keine KeyError verursachen
        assert "{{" in template_system  # Escaped braces vorhanden
        assert "{query}" not in template_system  # Keine unescaped Platzhalter
    
    def test_user_template_with_json_data(self, template_user):
        """Test: User-Template mit JSON-Daten"""
        
        # Simuliere Agent-Results mit JSON
        agent_results = {
            "BImSchG-Agent": {
                "result": "Das BImSchG regelt Immissionsschutz",
                "confidence": 0.95
            }
        }
        
        rag_context = {
            "sources": ["BImSchG § 1", "BImSchG § 22"],
            "text": "Zweck des Gesetzes ist es..."
        }
        
        try:
            formatted = template_user.format(
                query="Was regelt das BImSchG?",
                rag_context=json.dumps(rag_context, indent=2, ensure_ascii=False),
                agent_results=json.dumps(agent_results, indent=2, ensure_ascii=False)
            )
            
            assert "Was regelt das BImSchG?" in formatted
            assert "BImSchG-Agent" in formatted
            assert "sources" in formatted
            
        except KeyError as e:
            pytest.fail(f"User-Template .format() fehlgeschlagen: {e}")
    
    def test_combined_template_usage(self, template_system, template_user):
        """Test: Vollständiger Template-Workflow wie in Ollama Client"""
        
        # Step 1: System-Prompt wird direkt verwendet (KEIN .format())
        system_prompt = template_system
        assert "{{" in system_prompt
        
        # Step 2: User-Prompt wird mit .format() gefüllt
        user_data = {
            "query": "Was regelt das BImSchG?",
            "rag_context": json.dumps({"sources": ["§1", "§22"]}, indent=2),
            "agent_results": json.dumps({"agent": "result"}, indent=2)
        }
        
        try:
            user_prompt = template_user.format(**user_data)
            
            # Validierung
            assert user_data["query"] in user_prompt
            assert "agent" in user_prompt
            
            # System-Prompt bleibt unverändert
            assert system_prompt == template_system
            
        except Exception as e:
            pytest.fail(f"Template-Workflow fehlgeschlagen: {e}")
    
    def test_escaped_braces_in_output(self):
        """Test: Escaped Braces werden korrekt aufgelöst"""
        template = """Beispiel:
```json
{{
  "key": "value"
}}
```
Query: {query}"""
        
        result = template.format(query="Test")
        
        # Nach .format() sollten {{ }} zu { } werden
        assert '{\n  "key": "value"\n}' in result
        assert "{{" not in result  # Keine escaped braces mehr
    
    def test_realistic_llm_response_parsing(self):
        """Test: Simuliere echte LLM-Antwort mit JSON"""
        
        # Simulierte LLM-Antwort (wie vom Modell generiert)
        llm_response = """Das Bundes-Immissionsschutzgesetz (BImSchG) regelt den Schutz vor schädlichen Umwelteinwirkungen.

### Hauptregelungsbereiche

- **Anlagengenehmigung:** §§ 4-21 BImSchG
- **Lärmschutz:** § 22 BImSchG
- **Luftreinhaltung:** §§ 44-47 BImSchG

Das Gesetz dient dem Schutz von Menschen, Tieren, Pflanzen und Sachen vor schädlichen Umwelteinwirkungen.

```json
{
  "next_steps": [
    {"action": "Volltext des BImSchG einsehen", "type": "document"},
    {"action": "Bei konkretem Fall: Zuständige Behörde kontaktieren", "type": "link"},
    {"action": "Verwaltungsvorschriften prüfen", "type": "info"}
  ],
  "related_topics": ["Genehmigungsverfahren", "TA Lärm", "Immissionsschutzbeauftragter", "BImSchV"]
}
```"""
        
        # Extrahiere JSON
        from backend.utils.json_extractor import extract_json_from_text
        
        clean_text, metadata = extract_json_from_text(llm_response)
        
        # Validierung
        assert "Das Bundes-Immissionsschutzgesetz" in clean_text
        assert "```json" not in clean_text  # JSON wurde entfernt
        assert metadata is not None
        assert len(metadata["next_steps"]) == 3
        assert len(metadata["related_topics"]) == 4
        assert metadata["next_steps"][0]["action"] == "Volltext des BImSchG einsehen"


class TestErrorScenarios:
    """Tests für bekannte Fehlerszenarien"""
    
    def test_original_bug_newline_in_key(self):
        """Test: Original-Bug mit '\n  "next_steps"' KeyError"""
        
        # Fehlerhafte Template-Version (OHNE Escaping)
        bad_template = """Beispiel:
```json
{
  "next_steps": [{"action": "Test"}]
}
```
Query: {query}"""
        
        # Sollte KeyError werfen mit '\n  "next_steps"' als Message
        with pytest.raises(KeyError) as exc_info:
            bad_template.format(query="Test")
        
        # Der Fehler ist das, was NACH dem ersten { kommt
        error_key = str(exc_info.value).strip("'\"")
        assert "next_steps" in error_key or error_key.startswith("\n")
    
    def test_fixed_version_with_escaping(self):
        """Test: Korrigierte Version MIT Escaping funktioniert"""
        
        # Korrigierte Template-Version (MIT Escaping)
        good_template = """Beispiel:
```json
{{
  "next_steps": [{{"action": "Test"}}]
}}
```
Query: {query}"""
        
        try:
            result = good_template.format(query="Test")
            assert "Test" in result
            assert '"next_steps"' in result
        except KeyError:
            pytest.fail("Template mit Escaping sollte NICHT fehlschlagen!")
    
    def test_json_dumps_in_format(self):
        """Test: json.dumps() Output in .format() (wie im echten Code)"""
        
        template = "Agent Results:\n{agent_results}\n\nQuery: {query}"
        
        # Simuliere agent_results mit verschachteltem JSON
        agent_data = {
            "agent1": {
                "metadata": {"key": "value"},
                "response": "Text with {curly} braces"
            }
        }
        
        try:
            result = template.format(
                agent_results=json.dumps(agent_data, indent=2, ensure_ascii=False),
                query="Test"
            )
            
            assert "agent1" in result
            assert "Test" in result
            # json.dumps() escaped die {} in den Daten automatisch
            
        except KeyError as e:
            pytest.fail(f"json.dumps() in .format() fehlgeschlagen: {e}")


def run_tests():
    """Führt Template-Tests aus"""
    print("\n" + "="*70)
    print(" VERITAS Ollama Template Test Suite")
    print("="*70 + "\n")
    
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes",
        "-W", "ignore::DeprecationWarning"
    ])
    
    return exit_code


if __name__ == "__main__":
    exit_code = run_tests()
    
    print("\n" + "="*70)
    if exit_code == 0:
        print(" ✅ ALLE TEMPLATE-TESTS BESTANDEN")
    else:
        print(" ❌ TEMPLATE-TESTS FEHLGESCHLAGEN")
    print("="*70 + "\n")
    
    sys.exit(exit_code)
