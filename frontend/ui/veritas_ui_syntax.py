#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Syntax-Highlighting Module
Provides syntax highlighting for code blocks using Pygments
Integrates with Tkinter Text widgets via custom tags
"""

import tkinter as tk
from typing import Dict, List, Optional, Tuple
import re
import logging

try:
    from pygments import lex
    from pygments.lexers import (
        get_lexer_by_name, 
        guess_lexer,
        PythonLexer,
        JavascriptLexer,
        JsonLexer,
        SqlLexer,
        BashLexer,
        TextLexer
    )
    from pygments.token import Token
    from pygments.util import ClassNotFound
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class SyntaxHighlighter:
    """
    Syntax-Highlighting für Code-Blöcke mit Pygments
    
    Features:
    - Automatische Sprach-Erkennung aus Markdown Code-Fence (```python)
    - Pygments Token → Tkinter Tag Konvertierung
    - Fallback auf Textlexer wenn Sprache unbekannt
    - Unterstützte Sprachen: Python, JavaScript, SQL, JSON, Bash, u.v.m.
    
    Usage:
        highlighter = SyntaxHighlighter(text_widget)
        highlighter.highlight_code(code_text, language="python")
    """
    
    # Standard-Farbschema (VS Code Dark+ Theme inspiriert)
    COLOR_SCHEME = {
        Token.Keyword: '#569cd6',           # Blau (if, def, class)
        Token.Keyword.Namespace: '#569cd6', # import, from
        Token.Name.Builtin: '#4ec9b0',      # Türkis (print, len)
        Token.Name.Function: '#dcdcaa',     # Gelb (function names)
        Token.Name.Class: '#4ec9b0',        # Türkis (class names)
        Token.String: '#ce9178',            # Orange (strings)
        Token.String.Doc: '#6a9955',        # Grün (docstrings)
        Token.Number: '#b5cea8',            # Hellgrün (numbers)
        Token.Comment: '#6a9955',           # Grün (comments)
        Token.Comment.Single: '#6a9955',
        Token.Comment.Multiline: '#6a9955',
        Token.Operator: '#d4d4d4',          # Weiß (=, +, -)
        Token.Punctuation: '#d4d4d4',       # Weiß ((), [], {})
        Token.Name: '#d4d4d4',              # Weiß (variables)
        Token.Name.Decorator: '#dcdcaa',    # Gelb (@decorator)
        Token.Literal: '#ce9178',           # Orange (literals)
    }
    
    # Sprach-Aliase für bessere Erkennung
    LANGUAGE_ALIASES = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'sh': 'bash',
        'shell': 'bash',
        'md': 'markdown',
        'yml': 'yaml',
        'txt': 'text',
    }
    
    def __init__(self, text_widget: tk.Text):
        """
        Initialisiert den Syntax-Highlighter
        
        Args:
            text_widget: Tkinter Text-Widget für Tag-Konfiguration
        """
        self.text_widget = text_widget
        
        if not PYGMENTS_AVAILABLE:
            logger.warning("⚠️ Pygments nicht verfügbar - Syntax-Highlighting deaktiviert")
            return
        
        # Text-Tags für Syntax-Highlighting konfigurieren
        self._configure_syntax_tags()
        
        logger.info("✅ SyntaxHighlighter initialisiert (Pygments verfügbar)")
    
    def _configure_syntax_tags(self):
        """Konfiguriert Tkinter Text-Tags für Syntax-Highlighting"""
        for token_type, color in self.COLOR_SCHEME.items():
            tag_name = self._token_to_tag(token_type)
            
            # Font-Stil basierend auf Token-Typ
            font_style = ('Consolas', 9)
            
            # Spezielle Stile für bestimmte Token
            if token_type in (Token.Keyword, Token.Keyword.Namespace):
                font_style = ('Consolas', 9, 'bold')
            elif token_type in (Token.Comment, Token.Comment.Single, Token.Comment.Multiline):
                font_style = ('Consolas', 9, 'italic')
            
            self.text_widget.tag_configure(
                tag_name,
                foreground=color,
                font=font_style
            )
    
    def _token_to_tag(self, token_type) -> str:
        """
        Konvertiert Pygments Token-Typ zu Tkinter Tag-Namen
        
        Args:
            token_type: Pygments Token (z.B. Token.Keyword)
        
        Returns:
            Tag-Name als String (z.B. "syntax_keyword")
        """
        # Entferne "Token." Prefix und ersetze Punkte mit Underscores
        token_str = str(token_type).replace('Token.', '').replace('.', '_').lower()
        return f"syntax_{token_str}"
    
    def detect_language(self, code: str, hint: Optional[str] = None) -> str:
        """
        Erkennt Programmiersprache aus Code-Text
        
        Args:
            code: Code-Text zum Analysieren
            hint: Optional language hint (z.B. "python" aus ```python)
        
        Returns:
            Erkannte Sprache als String (lowercase)
        """
        if not PYGMENTS_AVAILABLE:
            return 'text'
        
        # 1. Priorität: Expliziter Hint
        if hint:
            normalized_hint = hint.lower().strip()
            # Aliase auflösen
            language = self.LANGUAGE_ALIASES.get(normalized_hint, normalized_hint)
            
            try:
                # Verifiziere dass Lexer existiert
                get_lexer_by_name(language)
                return language
            except ClassNotFound:
                logger.debug(f"Lexer für '{language}' nicht gefunden - verwende Guess")
        
        # 2. Fallback: Guess aus Code-Inhalt
        try:
            lexer = guess_lexer(code)
            return lexer.name.lower()
        except:
            return 'text'
    
    def highlight_code(
        self, 
        code: str, 
        language: Optional[str] = None,
        insert_position: str = tk.END
    ) -> List[Tuple[str, str]]:
        """
        Highlightet Code-Text und fügt ihn mit Tags in Text-Widget ein
        
        Args:
            code: Code-Text zum Highlighten
            language: Programmiersprache (optional, wird auto-detected)
            insert_position: Position im Text-Widget (default: tk.END)
        
        Returns:
            Liste von (text, tag) Tuples für Testing/Debugging
        """
        if not PYGMENTS_AVAILABLE:
            # Fallback: Insert ohne Highlighting
            self.text_widget.insert(insert_position, code, "md_code")
            return [(code, "md_code")]
        
        # Sprache erkennen
        detected_language = self.detect_language(code, hint=language)
        
        try:
            lexer = get_lexer_by_name(detected_language)
        except ClassNotFound:
            lexer = TextLexer()
        
        # Pygments Tokenization
        tokens = list(lex(code, lexer))
        
        # Insert mit Tags
        result = []
        for token_type, token_text in tokens:
            tag_name = self._token_to_tag(token_type)
            
            # Füge Text mit Syntax-Tag ein
            self.text_widget.insert(insert_position, token_text, tag_name)
            result.append((token_text, tag_name))
            
            # Update insert_position für nächsten Token
            if insert_position != tk.END:
                insert_position = self.text_widget.index(f"{insert_position}+{len(token_text)}c")
        
        return result
    
    def highlight_multiline_block(
        self,
        code: str,
        language: Optional[str] = None,
        insert_position: str = tk.END,
        add_background: bool = True
    ) -> str:
        """
        Highlightet mehrzeiligen Code-Block (```python ... ```)
        
        Args:
            code: Code-Block-Text
            language: Sprache aus Code-Fence (```python)
            insert_position: Position im Text-Widget
            add_background: Grauer Hintergrund für Code-Block
        
        Returns:
            End-Position nach dem Code-Block
        """
        if not PYGMENTS_AVAILABLE:
            self.text_widget.insert(insert_position, code, "md_code")
            return self.text_widget.index(insert_position)
        
        # Markiere Start-Position
        start_pos = insert_position if insert_position != tk.END else self.text_widget.index(tk.END)
        
        # Syntax-Highlighting anwenden
        self.highlight_code(code, language=language, insert_position=insert_position)
        
        # End-Position ermitteln
        end_pos = self.text_widget.index(tk.END)
        
        # Optional: Grauer Hintergrund für gesamten Block
        if add_background:
            block_tag = f"code_block_{id(code)}"
            self.text_widget.tag_configure(
                block_tag,
                background="#f5f5f5",
                lmargin1=10,
                lmargin2=10,
                rmargin=10
            )
            self.text_widget.tag_add(block_tag, start_pos, end_pos)
        
        return end_pos


def setup_syntax_highlighting_tags(text_widget: tk.Text):
    """
    Hilfsfunktion: Konfiguriert alle Syntax-Highlighting-Tags
    
    Args:
        text_widget: Tkinter Text-Widget
    """
    highlighter = SyntaxHighlighter(text_widget)
    # Tags werden automatisch in __init__ konfiguriert
    return highlighter


# Beispiel-Code für Testing
if __name__ == "__main__":
    # Test-GUI erstellen
    root = tk.Tk()
    root.title("Syntax-Highlighting Test")
    
    text_widget = tk.Text(root, wrap=tk.WORD, font=('Consolas', 10), bg='#1e1e1e', fg='#d4d4d4')
    text_widget.pack(fill=tk.BOTH, expand=True)
    
    highlighter = SyntaxHighlighter(text_widget)
    
    # Test-Code
    python_code = '''def hello_world():
    """Prints Hello World"""
    print("Hello, World!")
    return 42
'''
    
    highlighter.highlight_code(python_code, language='python')
    
    root.mainloop()
