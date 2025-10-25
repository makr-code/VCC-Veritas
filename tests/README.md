# VERITAS Test Suite

## Übersicht

Diese Test Suite validiert die JSON-Extraktion und Template-Formatierung im VERITAS-System.

## Test-Module

### 1. `test_json_extraction.py`
Testet die Extraktion von JSON-Metadaten aus LLM-Antworten:
- ✅ JSON in Markdown Code-Blocks (````json...```)
- ✅ JSON am Ende des Texts
- ✅ Fehlerhafte JSON-Syntax (dirtyjson Robustheit)
- ✅ Mehrere JSON-Blöcke (letzter wird genommen)
- ✅ Unicode-Zeichen (Umlaute, Sonderzeichen)
- ✅ Edge Cases (leere Strings, nur JSON, etc.)

### 2. `test_ollama_template.py`
Testet die Python `.format()` Template-Formatierung:
- ✅ Template mit JSON-Beispielen (Escaping: `{{ }}`)
- ✅ Fehlerhafte Templates ohne Escaping (sollten fehlschlagen)
- ✅ Komplexe Templates mit mehreren JSON-Blöcken
- ✅ Realistischer LLM-Response-Workflow
- ✅ Original-Bug-Szenario (`'\n  "next_steps"'` KeyError)

## Schnellstart

### Alle Tests ausführen
```powershell
python tests/run_all_tests.py
```

### Nur JSON-Extraktion
```powershell
python tests/run_all_tests.py --json
```

### Nur Template-Tests
```powershell
python tests/run_all_tests.py --template
```

### Mit Coverage
```powershell
python tests/run_all_tests.py --coverage
```

### Verbose Output
```powershell
python tests/run_all_tests.py -vv
```

### Spezifische Tests
```powershell
python tests/run_all_tests.py -k "test_template_escaping"
```

## Einzelne Test-Dateien

### test_json_extraction.py direkt
```powershell
python tests/test_json_extraction.py
```

### test_ollama_template.py direkt
```powershell
python tests/test_ollama_template.py
```

## Test-Kategorien

### JSON-Extraktion Tests
- **Klasse**: `TestJSONExtraction`
- **Zweck**: Validiert `backend/utils/json_extractor.py`
- **Wichtigste Tests**:
  - `test_json_in_code_block` - Markdown Code-Blocks
  - `test_malformed_json_with_dirtyjson` - Robustheit
  - `test_multiple_json_blocks` - Multi-JSON Handling

### Template-Escaping Tests
- **Klasse**: `TestOllamaTemplateFormatting`
- **Zweck**: Validiert `.format()` in `veritas_ollama_client.py`
- **Wichtigste Tests**:
  - `test_user_template_with_json_data` - Realer Workflow
  - `test_escaped_braces_in_output` - Brace-Escaping
  - `test_realistic_llm_response_parsing` - End-to-End

### Error-Szenario Tests
- **Klasse**: `TestErrorScenarios`
- **Zweck**: Validiert Fehlerbehandlung
- **Wichtigste Tests**:
  - `test_original_bug_newline_in_key` - Original-Bug reproduzieren
  - `test_fixed_version_with_escaping` - Fix validieren

## Bekannte Issues (behoben)

### ❌ Original-Bug: `'\n  "next_steps"'` KeyError

**Problem:**
```python
template = """Beispiel:
```json
{
  "next_steps": [...]
}
```"""

template.format(query="Test")  # ❌ KeyError: '\n  "next_steps"'
```

**Ursache:**  
Python `.format()` interpretiert `{` als Platzhalter-Start. Der Fehlertext ist **das was nach dem `{` kommt**.

**Lösung:**
```python
template = """Beispiel:
```json
{{
  "next_steps": [...]
}}
```"""

template.format(query="Test")  # ✅ Funktioniert!
```

**Validierung:**  
Test `test_original_bug_newline_in_key` reproduziert den Bug.  
Test `test_fixed_version_with_escaping` validiert den Fix.

## Dependencies

```bash
pip install pytest pytest-cov dirtyjson
```

## CI/CD Integration

Tests können in CI/CD-Pipelines integriert werden:

```yaml
# .github/workflows/tests.yml
- name: Run Tests
  run: python tests/run_all_tests.py --coverage
```

## Coverage Report

Nach `--coverage` Run:
```
Coverage Report: htmlcov/index.html
```

Im Browser öffnen:
```powershell
Start-Process htmlcov/index.html
```

## Test-Entwicklung

### Neuen Test hinzufügen

```python
# In test_json_extraction.py oder test_ollama_template.py

def test_new_feature(self):
    """Test: Beschreibung der neuen Funktion"""
    # Arrange
    input_data = "..."
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected_output
```

### Test ausführen
```powershell
python tests/run_all_tests.py -k "test_new_feature"
```

## Debugging

### Test-Fehler untersuchen
```powershell
# Mit Traceback
python tests/run_all_tests.py -vv

# Einzelner Test
pytest tests/test_json_extraction.py::TestJSONExtraction::test_json_in_code_block -vv

# Mit Debugger
pytest --pdb tests/test_json_extraction.py
```

### Backend-Logs bei Test-Fehlern
```powershell
Get-Content .\logs\backend_uvicorn.err.log -Tail 50
```

## Best Practices

1. **Immer Tests vor Code-Änderungen ausführen** (Baseline)
2. **Nach jeder Änderung Tests ausführen** (Regression)
3. **Neue Features: Erst Test schreiben** (TDD)
4. **Coverage > 80% anstreben**
5. **Edge Cases explizit testen** (leere Inputs, Unicode, etc.)

## Kontakt

Bei Fragen oder Problemen:
- Logs prüfen: `logs/backend_uvicorn.err.log`
- Issues: GitHub Issues
- Docs: `docs/VERITAS_API_BACKEND_DOCUMENTATION.md`
