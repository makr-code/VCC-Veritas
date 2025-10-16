#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS UI Module: Markdown Renderer
Verantwortlich für Markdown-Rendering in Tkinter Text Widgets
"""

import tkinter as tk
import re
from typing import Dict, Any, Optional
import logging

# Syntax-Highlighting Import
try:
    from frontend.ui.veritas_ui_syntax import SyntaxHighlighter
    SYNTAX_AVAILABLE = True
except ImportError:
    SYNTAX_AVAILABLE = False

# ✨ NEU: Icon-System Import
try:
    from frontend.ui.veritas_ui_icons import VeritasIcons
    ICONS_AVAILABLE = True
except ImportError:
    ICONS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MarkdownRenderer:
    """
    Markdown-Renderer für VERITAS Chat-Antworten
    Unterstützt: Headings, Listen, Blockquotes, Bold, Italic, Code, Links
    ✨ Feature #6: Copy-Button für Code-Blöcke
    ✨ Feature #3: Syntax-Highlighting mit Pygments
    ✨ Feature #10: Custom Icons für Listen und Headings
    """
    
    def __init__(self, text_widget: tk.Text):
        """
        Initialisiert den Markdown-Renderer
        
        Args:
            text_widget: Tkinter Text Widget für Rendering
        """
        self.text_widget = text_widget
        self.link_handlers = {}  # Speichert Link-Handler für Cleanup
        self.copy_buttons = []  # Speichert Copy-Button-Referenzen
        
        # ✨ NEU: Syntax-Highlighter initialisieren
        self.syntax_highlighter = None
        if SYNTAX_AVAILABLE:
            try:
                self.syntax_highlighter = SyntaxHighlighter(text_widget)
                logger.info("✅ Syntax-Highlighting aktiviert")
            except Exception as e:
                logger.warning(f"⚠️ Syntax-Highlighting konnte nicht initialisiert werden: {e}")
        
    def render_markdown(self, text: str, base_tag: str = "assistant") -> None:
        """
        Rendert Markdown-Formatierung in Tkinter Text Widget
        ✨ NEU: Unterstützt Code-Blöcke mit Syntax-Highlighting (```language)
        
        Args:
            text: Markdown-Text
            base_tag: Basis-Tag für normalen Text
        """
        if not text:
            return
        
        # ✨ NEU: Code-Blöcke extrahieren (```python ... ```)
        code_block_pattern = r'```(\w+)?\n(.*?)```'
        
        # Splitte Text bei Code-Blöcken
        parts = re.split(code_block_pattern, text, flags=re.DOTALL)
        
        # Vor-Verarbeitung: Zeilen für Tabellen-Detection
        lines = text.split('\n')
        
        i = 0
        while i < len(parts):
            part = parts[i]
            
            # Prüfe ob dies ein Code-Block ist (nach Split: language, code, text)
            if i + 2 < len(parts) and parts[i + 1]:  # Language marker vorhanden
                language = parts[i].strip() if i < len(parts) else None
                code_language = parts[i + 1].strip() if i + 1 < len(parts) else None
                code_content = parts[i + 2] if i + 2 < len(parts) else ""
                
                # Wenn part leer ist und nächste beiden Teile Code-Block sind
                if not part and code_language and code_content:
                    # Render Code-Block mit Syntax-Highlighting
                    self.render_code_block(code_content, language=code_language)
                    i += 3
                    continue
            
            # Normaler Text - zeilenweise verarbeiten
            lines = part.split('\n')
            
            line_idx = 0
            while line_idx < len(lines):
                line = lines[line_idx]
                
                # === TABELLEN ===
                # ✨ Feature #2: Erkenne Tabellen (| Header | Header |)
                if line.strip().startswith('|') and '|' in line.strip()[1:]:
                    # Prüfe ob nächste Zeile Separator ist (|---|---|)
                    if line_idx + 1 < len(lines):
                        next_line = lines[line_idx + 1].strip()
                        if re.match(r'^\|[\s\-:|]+\|$', next_line):
                            # Tabelle erkannt - Parse und Render
                            table_data, end_idx = self._parse_table(lines, line_idx)
                            self._render_table(table_data)
                            line_idx = end_idx + 1
                            continue
                
                # === ÜBERSCHRIFTEN ===
                if self._render_heading(line):
                    line_idx += 1
                    continue
                
                # === LISTEN ===
                if self._render_list(line, base_tag):
                    line_idx += 1
                    continue
                
                # === BLOCKQUOTES ===
                if self._render_blockquote(line):
                    line_idx += 1
                    continue
                
                # === NORMALE ZEILE MIT INLINE-FORMATTING ===
                self.render_inline_markdown(line, base_tag)
                self.text_widget.insert(tk.END, '\n')
                line_idx += 1
            
            i += 1
    
    def _render_heading(self, line: str) -> bool:
        """Rendert Überschriften (# H1, ## H2, ### H3)"""
        # ### Heading 3
        if line.startswith('### '):
            content = line[4:].strip()
            self.text_widget.insert(tk.END, content + '\n', "md_heading3")
            return True
        
        # ## Heading 2
        elif line.startswith('## ') and not line.startswith('###'):
            content = line[3:].strip()
            self.text_widget.insert(tk.END, content + '\n', "md_heading2")
            return True
        
        # # Heading 1
        elif line.startswith('# ') and not line.startswith('##'):
            content = line[2:].strip()
            self.text_widget.insert(tk.END, content + '\n', "md_heading1")
            return True
        
        return False
    
    def _render_list(self, line: str, base_tag: str) -> bool:
        """
        Rendert Listen mit optionalen Custom Icons, Indentation und Nested-Support
        
        ✨ Feature #4: Liste-Formatierung
        - Auto-Indentation basierend auf Leading Spaces
        - Nested Lists (mehrere Ebenen)
        - Nummerierte Listen (1., 2., 3.)
        - Alphabetische Listen (a., b., c.)
        - Römische Ziffern (i., ii., iii.)
        
        Args:
            line: Zeile mit Listen-Syntax
            base_tag: Basis-Tag für Text
            
        Returns:
            True wenn als Liste gerendert, False sonst
        """
        # ✨ Dynamisches Bullet-Icon
        bullet_icon = VeritasIcons.get('special', 'bullet') if ICONS_AVAILABLE else '•'
        
        # Berechne Indentation-Level (2 Spaces = 1 Level)
        indent_level = (len(line) - len(line.lstrip(' '))) // 2
        indent_spaces = "  " * indent_level  # 2 Spaces pro Level
        
        stripped = line.strip()
        
        # === BULLET LISTS ===
        # - List item oder * List item oder • List item
        if stripped.startswith(('- ', '* ', '• ')):
            content = stripped[2:].strip()
            self.text_widget.insert(tk.END, f"{indent_spaces}{bullet_icon} ", "md_list_item")
            self.render_inline_markdown(content, base_tag)
            self.text_widget.insert(tk.END, '\n')
            return True
        
        # === NUMMERIERTE LISTEN ===
        # 1. Item, 2. Item, 99. Item, ...
        match = re.match(r'^(\d+)\.\s(.+)', stripped)
        if match:
            num, content = match.groups()
            self.text_widget.insert(tk.END, f"{indent_spaces}{num}. ", "md_list_item")
            self.render_inline_markdown(content, base_tag)
            self.text_widget.insert(tk.END, '\n')
            return True
        
        # === ALPHABETISCHE LISTEN (Kleinbuchstaben) ===
        # a. Item, b. Item, c. Item, ...
        match = re.match(r'^([a-z])\.\s(.+)', stripped)
        if match:
            letter, content = match.groups()
            self.text_widget.insert(tk.END, f"{indent_spaces}{letter}. ", "md_list_item")
            self.render_inline_markdown(content, base_tag)
            self.text_widget.insert(tk.END, '\n')
            return True
        
        # === ALPHABETISCHE LISTEN (Großbuchstaben) ===
        # A. Item, B. Item, C. Item, ...
        match = re.match(r'^([A-Z])\.\s(.+)', stripped)
        if match:
            letter, content = match.groups()
            self.text_widget.insert(tk.END, f"{indent_spaces}{letter}. ", "md_list_item")
            self.render_inline_markdown(content, base_tag)
            self.text_widget.insert(tk.END, '\n')
            return True
        
        # === RÖMISCHE ZIFFERN (Kleinbuchstaben) ===
        # i. Item, ii. Item, iii. Item, iv. Item, v. Item, ...
        match = re.match(r'^(i{1,3}|iv|v|vi{1,3}|ix|x)\.\s(.+)', stripped)
        if match:
            roman, content = match.groups()
            self.text_widget.insert(tk.END, f"{indent_spaces}{roman}. ", "md_list_item")
            self.render_inline_markdown(content, base_tag)
            self.text_widget.insert(tk.END, '\n')
            return True
        
        # === RÖMISCHE ZIFFERN (Großbuchstaben) ===
        # I. Item, II. Item, III. Item, IV. Item, V. Item, ...
        match = re.match(r'^(I{1,3}|IV|V|VI{1,3}|IX|X)\.\s(.+)', stripped)
        if match:
            roman, content = match.groups()
            self.text_widget.insert(tk.END, f"{indent_spaces}{roman}. ", "md_list_item")
            self.render_inline_markdown(content, base_tag)
            self.text_widget.insert(tk.END, '\n')
            return True
        
        return False
    
    def _render_blockquote(self, line: str) -> bool:
        """Rendert Blockquotes (> Text)"""
        if line.strip().startswith('> '):
            content = line.strip()[2:]
            self.text_widget.insert(tk.END, f"❝ {content}\n", "md_quote")
            return True
        return False
    
    def _parse_table(self, lines: list, start_index: int) -> tuple[list, int]:
        """
        ✨ Feature #2: Parst Markdown-Tabelle
        
        Erkennt:
        | Header 1 | Header 2 | Header 3 |
        |----------|----------|----------|
        | Cell 1   | Cell 2   | Cell 3   |
        
        Args:
            lines: Alle Zeilen des Texts
            start_index: Index der ersten Tabellen-Zeile
        
        Returns:
            (table_data, end_index) - 2D-Array mit Zellinhalten und End-Index
        """
        table_rows = []
        current_index = start_index
        
        while current_index < len(lines):
            line = lines[current_index].strip()
            
            # Tabellen-Ende: Leere Zeile oder keine Pipes mehr
            if not line or not line.startswith('|'):
                break
            
            # Separator-Zeile überspringen (|---|---|)
            if re.match(r'^\|[\s\-:|]+\|$', line):
                current_index += 1
                continue
            
            # Parse Zeile in Zellen
            # Entferne führende/trailing Pipes und splitte
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            table_rows.append(cells)
            
            current_index += 1
        
        return table_rows, current_index - 1
    
    def _render_table(self, table_data: list) -> None:
        """
        ✨ Feature #2: Rendert geparste Tabelle
        
        Args:
            table_data: 2D-Array mit Tabelleninhalt
                        [0] = Header-Zeile
                        [1:] = Data-Zeilen
        """
        if not table_data or len(table_data) < 2:
            return
        
        # Berechne Spalten-Breiten
        num_cols = len(table_data[0])
        col_widths = [0] * num_cols
        
        for row in table_data:
            for i, cell in enumerate(row):
                if i < num_cols:
                    col_widths[i] = max(col_widths[i], len(cell))
        
        # === HEADER RENDERN ===
        header = table_data[0]
        self.text_widget.insert(tk.END, "┌", "table_border")
        for i, width in enumerate(col_widths):
            self.text_widget.insert(tk.END, "─" * (width + 2), "table_border")
            if i < len(col_widths) - 1:
                self.text_widget.insert(tk.END, "┬", "table_border")
        self.text_widget.insert(tk.END, "┐\n", "table_border")
        
        # Header-Zeile
        self.text_widget.insert(tk.END, "│ ", "table_border")
        for i, cell in enumerate(header):
            padded_cell = cell.ljust(col_widths[i])
            self.text_widget.insert(tk.END, padded_cell, "table_header")
            self.text_widget.insert(tk.END, " │ ", "table_border")
        self.text_widget.insert(tk.END, "\n", "table_border")
        
        # Separator
        self.text_widget.insert(tk.END, "├", "table_border")
        for i, width in enumerate(col_widths):
            self.text_widget.insert(tk.END, "─" * (width + 2), "table_border")
            if i < len(col_widths) - 1:
                self.text_widget.insert(tk.END, "┼", "table_border")
        self.text_widget.insert(tk.END, "┤\n", "table_border")
        
        # === DATA ROWS RENDERN ===
        for row_idx, row in enumerate(table_data[1:], 1):
            # Alternierende Row-Tags für optionale Farben
            row_tag = "table_cell" if row_idx % 2 == 0 else "table_cell_alt"
            
            self.text_widget.insert(tk.END, "│ ", "table_border")
            for i, cell in enumerate(row):
                if i < num_cols:
                    padded_cell = cell.ljust(col_widths[i])
                    self.text_widget.insert(tk.END, padded_cell, row_tag)
                    self.text_widget.insert(tk.END, " │ ", "table_border")
            self.text_widget.insert(tk.END, "\n")
        
        # Bottom Border
        self.text_widget.insert(tk.END, "└", "table_border")
        for i, width in enumerate(col_widths):
            self.text_widget.insert(tk.END, "─" * (width + 2), "table_border")
            if i < len(col_widths) - 1:
                self.text_widget.insert(tk.END, "┴", "table_border")
        self.text_widget.insert(tk.END, "┘\n\n", "table_border")
    
    def render_inline_markdown(self, text: str, base_tag: str = "assistant") -> None:
        """
        Rendert Inline-Markdown (bold, italic, code, links, ✨ IEEE-Zitationen)
        
        Args:
            text: Text mit Inline-Markdown
            base_tag: Basis-Tag für normalen Text
        """
        if not text:
            return
        
        # ✨ SCHRITT 1: Parse IEEE-Zitationen ZUERST (vor anderen Markdown-Elementen)
        text = self._parse_ieee_citations(text)
        
        # Regex-Patterns für Markdown-Elemente
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        bold_pattern = r'\*\*([^\*]+)\*\*|__([^_]+)__'
        italic_pattern = r'(?<!\*)\*([^\*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)'
        code_pattern = r'`([^`]+)`'
        # ✨ Citation-Marker-Pattern (von _parse_ieee_citations erstellt)
        citation_pattern = r'<CITE id=(\d+)>'
        
        # Kombiniertes Pattern (✨ inkl. Citation-Marker)
        combined_pattern = f'({citation_pattern}|{link_pattern}|{bold_pattern}|{italic_pattern}|{code_pattern})'
        
        # Splitte Text bei Markdown-Markern
        parts = re.split(combined_pattern, text)
        
        i = 0
        while i < len(parts):
            part = parts[i]
            
            if not part:
                i += 1
                continue
            
            # === LINKS ===
            if self._render_link(part, i, parts):
                i += 1
                continue
            
            # === ✨ IEEE-ZITATIONEN ===
            if self._render_citation(part):
                i += 1
                continue
            
            # === BOLD ===
            if self._render_bold(part, base_tag):
                i += 1
                continue
            
            # === ITALIC ===
            if self._render_italic(part, base_tag):
                i += 1
                continue
            
            # === CODE ===
            if self._render_code(part):
                i += 1
                continue
            
            # === NORMALER TEXT ===
            self.text_widget.insert(tk.END, part, base_tag)
            i += 1
    
    def _render_link(self, part: str, index: int, parts: list) -> bool:
        """Rendert Markdown-Links [Text](URL)"""
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        link_match = re.match(link_pattern, part)
        
        if link_match:
            link_text = link_match.group(1)
            link_url = link_match.group(2)
            
            # Füge Link als klickbar ein
            link_start = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, link_text, "clickable_link")
            link_end = self.text_widget.index(tk.END)
            
            # Unique Tag für diesen Link
            link_tag = f"md_link_{hash(link_url)}"
            self.text_widget.tag_add(link_tag, link_start, link_end)
            
            # Speichere Link-Handler
            self.link_handlers[link_tag] = link_url
            
            # Click-Handler wird extern gesetzt (via set_link_callback)
            # Cursor-Effekt über Events statt tag_configure
            self.text_widget.tag_configure(link_tag, foreground="#0066CC", underline=True)
            self.text_widget.tag_bind(link_tag, "<Enter>", lambda e: self.text_widget.config(cursor="hand2"))
            self.text_widget.tag_bind(link_tag, "<Leave>", lambda e: self.text_widget.config(cursor=""))
            
            return True
        return False
    
    def _render_bold(self, part: str, base_tag: str) -> bool:
        """Rendert Bold-Text (**text** oder __text__)"""
        bold_pattern = r'\*\*([^\*]+)\*\*|__([^_]+)__'
        bold_match = re.match(bold_pattern, part)
        
        if bold_match:
            bold_text = bold_match.group(1) or bold_match.group(2)
            self.text_widget.insert(tk.END, bold_text, ("md_bold", base_tag))
            return True
        return False
    
    def _render_italic(self, part: str, base_tag: str) -> bool:
        """Rendert Italic-Text (*text* oder _text_)"""
        italic_pattern = r'(?<!\*)\*([^\*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)'
        italic_match = re.match(italic_pattern, part)
        
        if italic_match:
            italic_text = italic_match.group(1) or italic_match.group(2)
            self.text_widget.insert(tk.END, italic_text, ("md_italic", base_tag))
            return True
        return False
    
    def _render_code(self, part: str, add_copy_button: bool = True, language: Optional[str] = None) -> bool:
        """
        Rendert Inline-Code (`code`) mit optionalem Copy-Button und Syntax-Highlighting
        
        Args:
            part: Text-Teil zum Rendern
            add_copy_button: Copy-Button hinzufügen (default: True)
            language: Programmiersprache für Syntax-Highlighting (optional)
        """
        code_pattern = r'`([^`]+)`'
        code_match = re.match(code_pattern, part)
        
        if code_match:
            code_text = code_match.group(1)
            
            # Code-Text einfügen (mit oder ohne Syntax-Highlighting)
            code_start = self.text_widget.index(tk.END)
            
            # ✨ NEU: Syntax-Highlighting für inline code
            if self.syntax_highlighter and language:
                self.syntax_highlighter.highlight_code(code_text, language=language, insert_position=tk.END)
            else:
                self.text_widget.insert(tk.END, code_text, "md_code")
            
            code_end = self.text_widget.index(tk.END)
            
            # ✨ Copy-Button hinzufügen
            if add_copy_button and len(code_text.strip()) > 3:  # Nur für längere Code-Snippets
                self._add_copy_button(code_text, code_start)
            
            return True
        return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ✨ IEEE-ZITATIONEN (v3.19.0 - Sprint 1.3)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _parse_ieee_citations(self, text: str) -> str:
        """
        Parst IEEE-Zitationen [1], [2] und ersetzt mit <CITE id=N> Markern
        
        WICHTIG: Wird VOR render_inline_markdown() aufgerufen, damit [1] nicht
        mit Link-Pattern [text](url) kollidiert.
        
        Args:
            text: Text mit IEEE-Zitationen (z.B. "§ 58 LBO BW[1] regelt...")
        
        Returns:
            Text mit Citation-Markern (z.B. "§ 58 LBO BW<CITE id=1> regelt...")
        
        Beispiel:
            Input:  "Nach § 58[1] ist Baugenehmigung erforderlich[2]."
            Output: "Nach § 58<CITE id=1> ist Baugenehmigung erforderlich<CITE id=2>."
        """
        citation_pattern = r'\[(\d+)\]'
        
        def replace_citation(match):
            cite_id = match.group(1)
            return f'<CITE id={cite_id}>'
        
        return re.sub(citation_pattern, replace_citation, text)
    
    def _render_citation(self, part: str) -> bool:
        """
        Rendert <CITE id=N> Marker als hochgestellte, anklickbare Zahl
        
        Args:
            part: Text-Teil (muss <CITE id=N> Pattern matchen)
        
        Returns:
            True wenn Citation gerendert wurde, sonst False
        
        Verhalten:
            - Rendert als blaue, unterstrichene Zahl (z.B. [1])
            - Cursor: Hand-Cursor bei Hover
            - Click: Scrollt zur entsprechenden Quelle
            - Font-Offset: +4px für Superscript-Effekt
        """
        citation_pattern = r'<CITE id=(\d+)>'
        citation_match = re.match(citation_pattern, part)
        
        if citation_match:
            cite_id = citation_match.group(1)
            
            # Zitations-Nummer einfügen mit Superscript-Styling
            cite_start = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, f"[{cite_id}]", "citation_superscript")
            cite_end = self.text_widget.index(tk.END)
            
            # Einzigartige Tag für Click-Handling (pro Zitation)
            cite_tag = f"citation_link_{cite_id}"
            self.text_widget.tag_add(cite_tag, cite_start, cite_end)
            
            # Click-Handler: Scrolle zur Quelle
            self.text_widget.tag_bind(
                cite_tag, 
                "<Button-1>", 
                lambda e, cid=cite_id: self._scroll_to_source(cid)
            )
            
            # Hover-Effects: Hand-Cursor + Tooltip
            self.text_widget.tag_bind(
                cite_tag, 
                "<Enter>", 
                lambda e: self.text_widget.config(cursor="hand2")
            )
            self.text_widget.tag_bind(
                cite_tag, 
                "<Leave>", 
                lambda e: self.text_widget.config(cursor="")
            )
            
            # Farbe + Underline (wird bei Tag-Konfiguration gesetzt)
            # (siehe __init__ für tag_configure "citation_superscript")
            
            return True
        return False
    
    def _scroll_to_source(self, source_num: str) -> None:
        """
        Scrollt zur Quellenangabe und hebt sie kurz hervor
        
        Args:
            source_num: ID der Quelle (z.B. "1", "2")
        
        Verhalten:
            1. Suche nach Tag "source_entry_{source_num}"
            2. Scrolle zur ersten Position des Tags
            3. Hebe Quelle 2 Sekunden gelb hervor (#FFFFCC)
            4. Entferne Highlight nach 2s
        
        Fallback:
            - Falls Tag nicht gefunden: Logging-Warnung, keine Aktion
        """
        source_tag = f"source_entry_{source_num}"
        
        try:
            # Finde alle Bereiche mit diesem Tag
            ranges = self.text_widget.tag_ranges(source_tag)
            
            if not ranges:
                # Tag nicht gefunden (z.B. Quellen noch nicht gerendert)
                logging.warning(f"[CITATION-SCROLL] Quelle [{source_num}] nicht gefunden (Tag: {source_tag})")
                return
            
            # Scrolle zur ersten Position des Tags
            first_position = ranges[0]
            self.text_widget.see(first_position)
            
            # Highlight-Animation (2 Sekunden gelb)
            self.text_widget.tag_config(source_tag, background='#FFFFCC')
            
            # Nach 2s: Entferne Highlight
            self.text_widget.after(
                2000,  # 2000ms = 2s
                lambda: self.text_widget.tag_config(source_tag, background='')
            )
            
            logging.info(f"[CITATION-SCROLL] Scrolled to source [{source_num}]")
            
        except Exception as e:
            logging.error(f"[CITATION-SCROLL] Fehler beim Scrollen zu Quelle [{source_num}]: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Ende IEEE-Zitationen
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _add_copy_button(self, code_text: str, position: str) -> None:
        """
        Fügt Copy-Button neben Code-Block ein
        
        Args:
            code_text: Zu kopierender Code
            position: Position im Text-Widget
        """
        try:
            # Erstelle Button-Widget
            copy_btn = tk.Label(
                self.text_widget,
                text="📋",
                font=('Segoe UI', 8),
                foreground="#666",
                padx=2,
                pady=0
            )
            copy_btn.config(cursor="hand2")  # Cursor separat setzen
            
            # Hover-Effekt
            def on_enter(e):
                copy_btn.config(foreground="#0066CC")
            def on_leave(e):
                copy_btn.config(foreground="#666")
            
            copy_btn.bind("<Enter>", on_enter)
            copy_btn.bind("<Leave>", on_leave)
            
            # Click-Handler mit Visual Feedback
            def on_click(e):
                self._copy_to_clipboard(code_text, copy_btn)
            
            copy_btn.bind("<Button-1>", on_click)
            
            # Button in Text-Widget einbetten
            self.text_widget.window_create(position, window=copy_btn)
            self.text_widget.insert(tk.END, " ")  # Leerzeichen nach Button
            
            # Speichere Referenz
            self.copy_buttons.append(copy_btn)
            
        except Exception as e:
            logger.debug(f"Fehler beim Hinzufügen des Copy-Buttons: {e}")
    
    def _copy_to_clipboard(self, text: str, button: tk.Label) -> None:
        """
        Kopiert Text in Zwischenablage mit Visual Feedback
        
        Args:
            text: Zu kopierender Text
            button: Button-Widget für Feedback
        """
        try:
            # In Zwischenablage kopieren
            self.text_widget.clipboard_clear()
            self.text_widget.clipboard_append(text)
            
            # Visual Feedback: ✓ Checkmark
            original_text = button.cget("text")
            original_fg = button.cget("foreground")
            
            button.config(text="✓", foreground="#27ae60")
            
            # Nach 1.5 Sekunden zurücksetzen
            def reset_button():
                try:
                    if button.winfo_exists():
                        button.config(text=original_text, foreground=original_fg)
                except:
                    pass
            
            if hasattr(self.text_widget, 'after'):
                self.text_widget.after(1500, reset_button)
            
            logger.debug(f"Code in Zwischenablage kopiert: {text[:30]}...")
            
        except Exception as e:
            logger.error(f"Fehler beim Kopieren in Zwischenablage: {e}")
            # Fehler-Feedback
            button.config(text="✗", foreground="#e74c3c")
            if hasattr(self.text_widget, 'after'):
                self.text_widget.after(1500, lambda: button.config(text="📋", foreground="#666"))
    
    def set_link_callback(self, callback):
        """
        Setzt Callback-Funktion für Link-Klicks
        
        Args:
            callback: Funktion die URL als Parameter erhält
        """
        for link_tag, link_url in self.link_handlers.items():
            self.text_widget.tag_bind(
                link_tag, 
                "<Button-1>", 
                lambda e, url=link_url: callback(url)
            )
    
    @staticmethod
    def parse_rag_response(content: str) -> Dict[str, Any]:
        """
        Parsed RAG-Antwort in strukturierte Abschnitte
        
        Args:
            content: Rohe RAG-Antwort
            
        Returns:
            Dict mit Sections: main_answer, sources, agents, suggestions, metadata
        """
        sections = {
            'main_answer': '',
            'sources': [],
            'agents': {},
            'suggestions': [],
            'metadata': {}
        }
        
        lines = content.split('\n')
        current_section = None
        main_answer_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # === METADATA EXTRACTION ===
            MarkdownRenderer._extract_metadata(line, sections['metadata'])
            
            # === SECTION DETECTION ===
            new_section = MarkdownRenderer._detect_section(stripped)
            if new_section:
                current_section = new_section
                continue
            
            # === CONTENT EXTRACTION ===
            if current_section == 'main':
                if stripped and not stripped.startswith('*') and not stripped.startswith('Aufgrund'):
                    clean_line = stripped.replace('**', '').replace('*', '')
                    if clean_line:
                        main_answer_lines.append(clean_line)
            
            elif current_section == 'sources':
                if stripped.startswith(('*', '•')):
                    source = stripped.lstrip('*•').strip()
                    if source and source not in ['Standard-Quellen']:
                        sections['sources'].append(source)
            
            elif current_section == 'suggestions':
                if stripped.startswith(('*', '•')):
                    suggestion = stripped.lstrip('*•').strip()
                    if suggestion:
                        sections['suggestions'].append(suggestion)
            
            elif current_section == 'agents':
                match = re.search(r'Die\s+(\w+)-Analyse\s+hat\s+(.+)', stripped)
                if match:
                    agent_name = match.group(1)
                    agent_result = match.group(2)
                    sections['agents'][agent_name] = agent_result
        
        # Hauptantwort zusammensetzen
        if main_answer_lines:
            sections['main_answer'] = ' '.join(main_answer_lines)
        else:
            # Fallback: Erste sinnvolle Zeile
            for line in lines[:10]:
                if line.strip() and not line.strip().startswith(('Antwort auf', 'Aufgrund', '🎯', '📚', '🤖', '⚡')):
                    clean = line.strip().replace('**', '').replace('*', '')
                    if len(clean) > 20:
                        sections['main_answer'] = clean
                        break
        
        return sections
    
    @staticmethod
    def _extract_metadata(line: str, metadata: Dict) -> None:
        """Extrahiert Metadaten aus einer Zeile"""
        # Confidence: 88.7%
        if '🎯' in line or 'Confidence:' in line:
            match = re.search(r'(\d+\.?\d*)%', line)
            if match:
                metadata['confidence'] = float(match.group(1))
        
        # 📚 8 Quellen
        if '📚' in line and 'Quellen' in line:
            match = re.search(r'(\d+)\s+Quellen', line)
            if match:
                metadata['sources_count'] = int(match.group(1))
        
        # 🤖 6 Agents
        if '🤖' in line and ('Agents' in line or 'Agenten' in line):
            match = re.search(r'(\d+)\s+(Agents|Agenten)', line)
            if match:
                metadata['agents_count'] = int(match.group(1))
        
        # ⚡ 23.34s
        if '⚡' in line:
            match = re.search(r'(\d+\.?\d*)\s*s', line)
            if match:
                metadata['duration'] = match.group(1)
    
    @staticmethod
    def _detect_section(line: str) -> Optional[str]:
        """Erkennt Section-Header"""
        if 'Hauptergebnisse:' in line or 'Die Hauptfrage' in line:
            return 'main'
        elif 'Quellen:' in line or 'Die folgenden Quellen' in line:
            return 'sources'
        elif 'Nächste Schritte:' in line or 'Vorschläge:' in line or '🔍 **Vorschläge:**' in line:
            return 'suggestions'
        elif 'Zusätzliche Erkenntnisse:' in line:
            return 'agents'
        return None
    
    def render_code_block(self, code: str, language: Optional[str] = None, add_copy_button: bool = True) -> None:
        """
        ✨ NEU: Rendert mehrzeiligen Code-Block mit Syntax-Highlighting
        
        Unterstützt Code-Fences:
        ```python
        def hello():
            print("Hello World")
        ```
        
        Args:
            code: Code-Text
            language: Programmiersprache (z.B. "python", "javascript")
            add_copy_button: Copy-Button hinzufügen
        """
        if not code:
            return
        
        # Markiere Start-Position für Background
        start_pos = self.text_widget.index(tk.END)
        
        # Syntax-Highlighting anwenden falls verfügbar
        if self.syntax_highlighter:
            self.syntax_highlighter.highlight_multiline_block(
                code,
                language=language,
                insert_position=tk.END,
                add_background=True
            )
        else:
            # Fallback: Einfaches Code-Rendering
            self.text_widget.insert(tk.END, code, "md_code")
        
        # Copy-Button hinzufügen
        if add_copy_button:
            self._add_copy_button(code, start_pos)
        
        # Leerzeile nach Code-Block
        self.text_widget.insert(tk.END, '\n')


# Convenience-Funktion für einfache Verwendung
def setup_markdown_tags(text_widget: tk.Text) -> None:
    """
    Konfiguriert Markdown-Tags für ein Text Widget
    
    Args:
        text_widget: Tkinter Text Widget
    """
    # Bold
    text_widget.tag_configure("md_bold", font=('Segoe UI', 10, 'bold'))
    
    # Italic
    text_widget.tag_configure("md_italic", font=('Segoe UI', 10, 'italic'))
    
    # Code
    text_widget.tag_configure("md_code", 
                             font=('Consolas', 9), 
                             background="#f0f0f0", 
                             foreground="#c7254e")
    
    # Headings
    text_widget.tag_configure("md_heading1", 
                             font=('Segoe UI', 14, 'bold'), 
                             foreground="#2c3e50")
    text_widget.tag_configure("md_heading2", 
                             font=('Segoe UI', 12, 'bold'), 
                             foreground="#34495e")
    text_widget.tag_configure("md_heading3", 
                             font=('Segoe UI', 11, 'bold'), 
                             foreground="#7f8c8d")
    
    # List Items
    text_widget.tag_configure("md_list_item", foreground="#555555")
    
    # Blockquotes
    text_widget.tag_configure("md_quote", 
                             font=('Segoe UI', 10, 'italic'), 
                             foreground="#7f8c8d",
                             lmargin1=20, 
                             lmargin2=20)
    
    # ✨ Feature #2: Tabellen-Tags
    text_widget.tag_configure("table_header", 
                             font=('Courier New', 9, 'bold'),
                             foreground="#2c3e50")
    
    text_widget.tag_configure("table_cell", 
                             font=('Courier New', 9),
                             foreground="#34495e")
    
    text_widget.tag_configure("table_cell_alt", 
                             font=('Courier New', 9),
                             foreground="#34495e",
                             background="#f9f9f9")
    
    text_widget.tag_configure("table_border", 
                             font=('Courier New', 9),
                             foreground="#95a5a6")
    
    # ✨ v3.19.0: IEEE-Zitationen Superscript-Styling
    text_widget.tag_configure("citation_superscript",
                             font=('Segoe UI', 7),  # Kleinere Schrift
                             offset=4,  # Superscript-Effekt (4px nach oben)
                             foreground='#0066CC',  # Blau (Link-Farbe)
                             underline=1)  # Unterstrichen
    
    logger.info("✅ Markdown-Tags konfiguriert")
