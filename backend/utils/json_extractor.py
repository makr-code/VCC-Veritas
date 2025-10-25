"""
VERITAS JSON Extractor
======================

Robustes Extrahieren von JSON aus LLM-Antworten mit:
- Regex-basierte Lokalisierung
- dirty-json für fehlertolerantes Parsing
- Fallback-Strategien

Compliance-konform: Strukturierte Metadaten in JSON
"""

import re
import json
import logging
from typing import Dict, Any, Optional, Tuple

try:
    import dirtyjson
    DIRTY_JSON_AVAILABLE = True
except ImportError:
    DIRTY_JSON_AVAILABLE = False

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Extrahiert JSON aus Text und liefert beides separat
    
    Args:
        text: Vollständiger Text (ggf. mit eingebettetem JSON)
        
    Returns:
        Tuple[str, Optional[Dict]]: (Reiner Text, Extrahierte JSON-Daten)
        
    Examples:
        >>> text = "Das ist eine Antwort.\\n```json\\n{\"key\": \"value\"}\\n```"
        >>> clean_text, json_data = extract_json_from_text(text)
        >>> clean_text
        "Das ist eine Antwort."
        >>> json_data
        {"key": "value"}
    """
    
    # Pattern 1: JSON in Code-Block (```json ... ```)
    json_block_pattern = r'```json\s*(.*?)\s*```'
    match = re.search(json_block_pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        json_str = match.group(1).strip()
        clean_text = text[:match.start()].strip() + text[match.end():].strip()
        clean_text = clean_text.strip()
        
        # Parse JSON
        parsed = _parse_json_robust(json_str)
        if parsed:
            logger.debug("✅ JSON aus Code-Block extrahiert")
            return clean_text, parsed
    
    # Pattern 2: JSON ohne Code-Block (rohe JSON-Objekte)
    # Suche nach {...} am Ende des Texts
    json_raw_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*$'
    match = re.search(json_raw_pattern, text, re.DOTALL)
    
    if match:
        json_str = match.group(0).strip()
        clean_text = text[:match.start()].strip()
        
        parsed = _parse_json_robust(json_str)
        if parsed:
            logger.debug("✅ JSON am Textende extrahiert")
            return clean_text, parsed
    
    # Pattern 3: Mehrere JSON-Objekte (nimm letztes)
    all_json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = list(re.finditer(all_json_pattern, text, re.DOTALL))
    
    if matches:
        last_match = matches[-1]
        json_str = last_match.group(0).strip()
        clean_text = text[:last_match.start()].strip()
        
        parsed = _parse_json_robust(json_str)
        if parsed:
            logger.debug("✅ Letztes JSON-Objekt extrahiert")
            return clean_text, parsed
    
    # Kein JSON gefunden
    logger.debug("ℹ️ Kein JSON im Text gefunden")
    return text, None


def _parse_json_robust(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Parst JSON mit Fallback-Strategien
    
    1. Standard json.loads()
    2. dirty-json (wenn verfügbar)
    3. Manuelle Reparatur-Versuche
    
    Args:
        json_str: JSON-String
        
    Returns:
        Optional[Dict]: Geparste Daten oder None
    """
    
    # Versuch 1: Standard JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.debug(f"Standard JSON parsing fehlgeschlagen: {e}")
    
    # Versuch 2: dirtyjson
    if DIRTY_JSON_AVAILABLE:
        try:
            parsed = dirtyjson.loads(json_str)
            logger.debug("✅ dirtyjson erfolgreich")
            return parsed
        except Exception as e:
            logger.debug(f"dirtyjson fehlgeschlagen: {e}")
    
    # Versuch 3: Manuelle Reparatur
    try:
        # Entferne trailing commas
        repaired = re.sub(r',\s*}', '}', json_str)
        repaired = re.sub(r',\s*]', ']', repaired)
        
        # Entferne leading/trailing whitespace in Werten
        repaired = repaired.strip()
        
        return json.loads(repaired)
    except json.JSONDecodeError as e:
        logger.warning(f"❌ JSON-Parsing fehlgeschlagen (auch nach Repair): {e}")
        logger.debug(f"Fehlerhafter JSON: {json_str[:200]}...")
        return None


def extract_next_steps(json_data: Optional[Dict[str, Any]]) -> Optional[list]:
    """
    Extrahiert 'next_steps' aus JSON-Daten
    
    Args:
        json_data: Extrahierte JSON-Daten
        
    Returns:
        Optional[list]: Liste von Next Steps oder None
    """
    if not json_data:
        return None
    
    return json_data.get("next_steps") or json_data.get("nächste_schritte")


def extract_related_topics(json_data: Optional[Dict[str, Any]]) -> Optional[list]:
    """
    Extrahiert 'related_topics' aus JSON-Daten
    
    Args:
        json_data: Extrahierte JSON-Daten
        
    Returns:
        Optional[list]: Liste von Related Topics oder None
    """
    if not json_data:
        return None
    
    return json_data.get("related_topics") or json_data.get("verwandte_themen")


def format_next_steps_as_markdown(next_steps: list) -> str:
    """
    Formatiert Next Steps als Markdown-Liste
    
    Args:
        next_steps: Liste von Step-Dictionaries
        
    Returns:
        str: Formatierte Markdown-Liste
        
    Example:
        >>> steps = [
        ...     {"action": "Unterlagen zusammenstellen", "type": "info"},
        ...     {"action": "Termin vereinbaren", "type": "link"}
        ... ]
        >>> print(format_next_steps_as_markdown(steps))
        **Nächste Schritte:**
        • Unterlagen zusammenstellen
        • Termin vereinbaren 🔗
    """
    if not next_steps:
        return ""
    
    lines = ["**Nächste Schritte:**"]
    
    for step in next_steps:
        if isinstance(step, dict):
            action = step.get("action", "")
            step_type = step.get("type", "")
            
            # Icon basierend auf Type
            icon = ""
            if step_type == "link":
                icon = " 🔗"
            elif step_type == "document":
                icon = " 📄"
            
            lines.append(f"• {action}{icon}")
        elif isinstance(step, str):
            lines.append(f"• {step}")
    
    return "\n".join(lines)
