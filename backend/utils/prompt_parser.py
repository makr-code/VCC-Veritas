"""
Enhanced Prompt Parser with Control Characters
==============================================

Parser für User-Prompts mit Steuerzeichen zur direkten Endpoint-/Agent-Auswahl.

Unterstützte Steuerzeichen:
- @ - Agent/Endpoint direkt ansprechen (@powerpoint, @excel, @outlook, @onenote)
- # - Template-Kategorie angeben (#flowchart, #swot, #meeting_notes)
- / - Slash-Commands (/generate, /list, /help)
- ! - Priorität/Dringlichkeit (!high, !urgent)
- $ - Output-Format ($pdf, $xlsx, $html)
- + - Tags/Kategorien hinzufügen (+confidential, +draft)

Beispiele:
- "@powerpoint #flowchart Erstelle einen Genehmigungsprozess"
- "@excel $xlsx Verkaufszahlen Q4 2024"
- "@outlook !urgent E-Mail an Team über Meeting-Änderung"
- "/list @onenote #meeting_notes"

Author: VERITAS System
Date: 2025-12-13
Version: 1.0
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ControlCharacter(str, Enum):
    """Supported control characters"""
    AGENT = "@"           # @powerpoint, @excel, @outlook, @onenote
    TEMPLATE = "#"        # #flowchart, #swot, #meeting_notes
    COMMAND = "/"         # /generate, /list, /help
    PRIORITY = "!"        # !high, !urgent, !low
    FORMAT = "$"          # $pdf, $xlsx, $html, $json
    TAG = "+"             # +confidential, +draft, +important


class AgentType(str, Enum):
    """Available agent types"""
    POWERPOINT = "powerpoint"
    PPT = "ppt"
    PRESENTATION = "presentation"
    EXCEL = "excel"
    TABLE = "table"
    TABLES = "tables"
    OUTLOOK = "outlook"
    EMAIL = "email"
    MAIL = "mail"
    ONENOTE = "onenote"
    NOTE = "note"
    NOTES = "notes"
    WORD = "word"
    DOC = "doc"
    IMAGE = "image"
    CHART = "chart"


class CommandType(str, Enum):
    """Slash commands"""
    GENERATE = "generate"
    CREATE = "create"
    LIST = "list"
    HELP = "help"
    STATUS = "status"
    TEMPLATES = "templates"
    EXPORT = "export"
    PREVIEW = "preview"


class PriorityLevel(str, Enum):
    """Priority levels"""
    HIGH = "high"
    URGENT = "urgent"
    MEDIUM = "medium"
    NORMAL = "normal"
    LOW = "low"


class OutputFormat(str, Enum):
    """Output formats"""
    PPTX = "pptx"
    PDF = "pdf"
    XLSX = "xlsx"
    CSV = "csv"
    DOCX = "docx"
    HTML = "html"
    JSON = "json"
    XML = "xml"
    MSG = "msg"
    EML = "eml"
    ICS = "ics"


@dataclass
class ParsedPrompt:
    """Result of prompt parsing"""
    # Original and cleaned text
    original_text: str
    clean_text: str  # Text without control characters
    
    # Parsed elements
    agent: Optional[str] = None
    templates: List[str] = field(default_factory=list)
    command: Optional[str] = None
    priority: Optional[str] = None
    output_format: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Routing information
    endpoint: Optional[str] = None
    agent_type: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "original_text": self.original_text,
            "clean_text": self.clean_text,
            "agent": self.agent,
            "templates": self.templates,
            "command": self.command,
            "priority": self.priority,
            "output_format": self.output_format,
            "tags": self.tags,
            "endpoint": self.endpoint,
            "agent_type": self.agent_type,
            "metadata": self.metadata
        }


class PromptParser:
    """
    Enhanced prompt parser with control character support.
    
    Features:
    - Control character extraction (@, #, /, !, $, +)
    - Agent/endpoint routing
    - Template selection
    - Command parsing
    - Priority and format hints
    - Tag extraction
    """
    
    # Agent to endpoint mapping
    AGENT_ENDPOINT_MAP = {
        "powerpoint": "/api/office/presentations/generate",
        "ppt": "/api/office/presentations/generate",
        "presentation": "/api/office/presentations/generate",
        "excel": "/api/office/tables/generate",
        "table": "/api/office/tables/generate",
        "tables": "/api/office/tables/generate",
        "outlook": "/api/office/outlook/compose",
        "email": "/api/office/outlook/compose",
        "mail": "/api/office/outlook/compose",
        "onenote": "/api/office/onenote/create",
        "note": "/api/office/onenote/create",
        "notes": "/api/office/onenote/create",
        "word": "/api/office/word/generate",  # Future
        "doc": "/api/office/word/generate",   # Future
        "image": "/api/office/images/generate", # Future
        "chart": "/api/office/charts/generate"  # Future
    }
    
    # Template synonyms
    TEMPLATE_SYNONYMS = {
        # PowerPoint templates
        "flow": "flowchart",
        "prozess": "process",
        "workflow": "process",
        "org": "hierarchy",
        "organigramm": "hierarchy",
        "kreis": "cycle",
        "zyklus": "cycle",
        "liste": "list",
        "aufzählung": "list",
        
        # Excel templates
        "daten": "data_table",
        "vergleich": "comparison",
        "zusammenfassung": "summary",
        "zeitplan": "schedule",
        
        # Outlook templates
        "kalender": "calendar_event",
        "termin": "calendar_event",
        "aufgabe": "task_management",
        "kontakt": "contact_management",
        
        # OneNote templates
        "meeting": "meeting_notes",
        "besprechung": "meeting_notes",
        "projekt": "project_notes",
        "checklist": "checklist",
        "todo": "checklist"
    }
    
    def __init__(self):
        """Initialize prompt parser"""
        self.patterns = self._compile_patterns()
        logger.info("✅ Prompt Parser initialized")
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for control characters"""
        return {
            "agent": re.compile(r'@(\w+)'),
            "template": re.compile(r'#(\w+)'),
            "command": re.compile(r'/(\w+)'),
            "priority": re.compile(r'!(\w+)'),
            "format": re.compile(r'\$(\w+)'),
            "tag": re.compile(r'\+(\w+)')
        }
    
    def parse(self, text: str) -> ParsedPrompt:
        """
        Parse user prompt and extract control characters.
        
        Args:
            text: User input text
            
        Returns:
            ParsedPrompt with extracted elements
        """
        if not text or not text.strip():
            return ParsedPrompt(original_text="", clean_text="")
        
        original_text = text.strip()
        parsed = ParsedPrompt(original_text=original_text, clean_text="")
        
        # Extract all control character elements
        parsed.agent = self._extract_agent(text)
        parsed.templates = self._extract_templates(text)
        parsed.command = self._extract_command(text)
        parsed.priority = self._extract_priority(text)
        parsed.output_format = self._extract_format(text)
        parsed.tags = self._extract_tags(text)
        
        # Remove control characters to get clean text
        parsed.clean_text = self._remove_control_characters(text)
        
        # Determine endpoint and agent type
        if parsed.agent:
            parsed.endpoint = self.AGENT_ENDPOINT_MAP.get(parsed.agent.lower())
            parsed.agent_type = self._normalize_agent_type(parsed.agent)
        
        # Add metadata
        parsed.metadata = self._build_metadata(parsed)
        
        logger.debug(f"Parsed prompt: agent={parsed.agent}, templates={parsed.templates}, command={parsed.command}")
        
        return parsed
    
    def _extract_agent(self, text: str) -> Optional[str]:
        """Extract agent from @mentions"""
        matches = self.patterns["agent"].findall(text)
        return matches[0].lower() if matches else None
    
    def _extract_templates(self, text: str) -> List[str]:
        """Extract templates from #hashtags"""
        matches = self.patterns["template"].findall(text)
        templates = []
        for match in matches:
            template = match.lower()
            # Check for synonyms
            template = self.TEMPLATE_SYNONYMS.get(template, template)
            templates.append(template)
        return templates
    
    def _extract_command(self, text: str) -> Optional[str]:
        """Extract command from /slash"""
        matches = self.patterns["command"].findall(text)
        return matches[0].lower() if matches else None
    
    def _extract_priority(self, text: str) -> Optional[str]:
        """Extract priority from !exclamation"""
        matches = self.patterns["priority"].findall(text)
        return matches[0].lower() if matches else None
    
    def _extract_format(self, text: str) -> Optional[str]:
        """Extract format from $dollar"""
        matches = self.patterns["format"].findall(text)
        return matches[0].lower() if matches else None
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract tags from +plus"""
        matches = self.patterns["tag"].findall(text)
        return [m.lower() for m in matches]
    
    def _remove_control_characters(self, text: str) -> str:
        """Remove all control characters and clean text"""
        clean = text
        
        # Remove all control character patterns
        for pattern in self.patterns.values():
            clean = pattern.sub('', clean)
        
        # Clean up extra whitespace
        clean = ' '.join(clean.split())
        
        return clean.strip()
    
    def _normalize_agent_type(self, agent: str) -> str:
        """Normalize agent type to canonical form"""
        agent_lower = agent.lower()
        
        if agent_lower in ["powerpoint", "ppt", "presentation"]:
            return "presentation"
        elif agent_lower in ["excel", "table", "tables"]:
            return "table"
        elif agent_lower in ["outlook", "email", "mail"]:
            return "outlook"
        elif agent_lower in ["onenote", "note", "notes"]:
            return "onenote"
        elif agent_lower in ["word", "doc"]:
            return "word"
        elif agent_lower == "image":
            return "image"
        elif agent_lower == "chart":
            return "chart"
        
        return agent_lower
    
    def _build_metadata(self, parsed: ParsedPrompt) -> Dict[str, Any]:
        """Build metadata from parsed elements"""
        metadata = {}
        
        if parsed.priority:
            metadata["priority"] = parsed.priority
        
        if parsed.output_format:
            metadata["output_format"] = parsed.output_format
        
        if parsed.tags:
            metadata["tags"] = parsed.tags
        
        if parsed.command:
            metadata["command"] = parsed.command
        
        return metadata
    
    def suggest_endpoint(self, text: str) -> Optional[str]:
        """
        Suggest endpoint based on prompt content.
        
        Args:
            text: User prompt
            
        Returns:
            Suggested endpoint path or None
        """
        parsed = self.parse(text)
        return parsed.endpoint
    
    def get_routing_info(self, text: str) -> Dict[str, Any]:
        """
        Get routing information for orchestrator.
        
        Args:
            text: User prompt
            
        Returns:
            Dictionary with routing information
        """
        parsed = self.parse(text)
        
        return {
            "agent_type": parsed.agent_type,
            "endpoint": parsed.endpoint,
            "templates": parsed.templates,
            "priority": parsed.priority or "normal",
            "output_format": parsed.output_format,
            "clean_query": parsed.clean_text,
            "metadata": parsed.metadata
        }


# Singleton instance
_parser_instance = None


def get_prompt_parser() -> PromptParser:
    """Get singleton instance of PromptParser"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = PromptParser()
    return _parser_instance


# Convenience functions
def parse_prompt(text: str) -> ParsedPrompt:
    """Parse prompt text (convenience function)"""
    parser = get_prompt_parser()
    return parser.parse(text)


def get_routing_info(text: str) -> Dict[str, Any]:
    """Get routing info from prompt (convenience function)"""
    parser = get_prompt_parser()
    return parser.get_routing_info(text)
