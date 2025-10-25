#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS UI Module: IEEE Citation System
Version 3.16.0 - Wissenschaftliches Zitieren nach IEEE-Standard

IEEE Citation Standard:
- Inline Citations: [1], [2], [3] im laufenden Text
- References Section: Formatierte Quellenangaben am Ende
- Format je nach Source-Type (Journal, Book, Web, etc.)

Beispiel:
    Text: "Die Studie zeigt signifikante Ergebnisse [1], [2]."
    References:
        [1] J. Smith, "Deep Learning in NLP," IEEE Trans. Pattern Anal., 
            vol. 42, no. 3, pp. 567-589, Mar. 2020.
        [2] "VERITAS Documentation," https://veritas.example.com, 
            accessed Oct. 17, 2025.
"""

import tkinter as tk
from typing import Dict, Any, List, Optional, Tuple, Callable
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# === FARBSCHEMA FÜR CITATIONS ===

CITATION_COLORS = {
    'citation_text': '#0066CC',         # Blue (klickbar)
    'citation_hover': '#004499',        # Darker Blue
    'citation_bg': '#E3F2FD',           # Light Blue (Highlight)
    'reference_number': '#F44336',      # Red für [1], [2]
    'reference_text': '#424242',        # Dark Grey
}


# === IEEE CITATION RENDERER ===

class IEEECitationRenderer:
    """
    Rendert Inline-Citations nach IEEE-Standard im Assistant-Text
    
    Features:
    - Automatische Erkennung von Citation-Markern im Text
    - Klickbare Citations [1], [2] mit Hover-Preview
    - Scroll-to-Reference bei Click
    - Tooltip mit Source-Details
    
    Citation-Format im Text:
    - Backend liefert: "Text mit Quelle {cite:1} und {cite:2}"
    - Renderer wandelt um: "Text mit Quelle [1] und [2]"
    - [1], [2] sind klickbar und scrollen zu Quellenverzeichnis
    """
    
    def __init__(
        self,
        text_widget: tk.Text,
        sources: List[Dict[str, Any]],
        scroll_to_reference_callback: Optional[Callable] = None,
        markdown_renderer: Optional[Any] = None
    ):
        """
        Args:
            text_widget: Tkinter Text Widget für Rendering
            sources: Liste von Source-Dicts (mit file, confidence, etc.)
            scroll_to_reference_callback: Callback(citation_number) zum Scrollen
            markdown_renderer: ✨ Optional MarkdownRenderer für Markdown-Formatierung
        """
        self.text_widget = text_widget
        self.sources = sources
        self.scroll_to_reference_callback = scroll_to_reference_callback
        self.markdown_renderer = markdown_renderer
        
        # Source-ID zu Citation-Number Mapping
        self.source_to_number = self._build_source_mapping()
    
    def _build_source_mapping(self) -> Dict[str, int]:
        """Erstellt Mapping von Source-ID zu Citation-Number"""
        mapping = {}
        for idx, source in enumerate(self.sources, start=1):
            source_id = source.get('id', f"source_{idx}")
            mapping[source_id] = idx
        return mapping
    
    def render_text_with_citations(self, text: str, tag: str = 'assistant_text') -> None:
        """
        Rendert Text mit eingebetteten Citations (MIT MARKDOWN-SUPPORT)
        
        Input-Format (vom Backend):
            Variante 1: "Deep Learning zeigt Erfolge {cite:src_1} in NLP {cite:src_2}."
            Variante 2: "## Direkte Antwort\n\nDeep Learning zeigt Erfolge [1] in NLP [2]."
        
        Output-Format (im UI):
            - Markdown wird korrekt gerendert (H2, Bold, etc.)
            - [1], [2] sind klickbare Citations mit Tooltip
        
        Args:
            text: Text mit {cite:source_id} oder [N] Markern (kann Markdown enthalten)
            tag: Tag für Text-Styling (Standard: 'assistant_text')
        """
        
        # Sicherheitscheck: Text darf nicht None sein
        if text is None:
            logger.warning("⚠️ render_text_with_citations erhielt None als Text")
            return
        
        # ✨ STRATEGIE: 
        # 1. Wenn Markdown-Renderer vorhanden → Markdown rendern mit Citation-Callback
        # 2. Wenn kein Markdown-Renderer → Fallback zu Plain-Text mit Citations
        
        if self.markdown_renderer:
            # === MARKDOWN-MODUS: Rendere Markdown, dann füge Citations ein ===
            # Pattern für Citations: [N]
            citation_pattern = r'\[(\d+)\]'
            
            # 🔍 DEBUG: Zeige Original-Text
            logger.debug(f"🔍 Original Text (erste 200 Zeichen): {text[:200]}")
            
            # Schritt 1: Ersetze Citations temporär durch Platzhalter
            # (damit Markdown sie nicht als Links interpretiert)
            citation_matches = []
            def replace_citation(match):
                citation_num = int(match.group(1))
                # Speichere Match für später
                placeholder_id = len(citation_matches)
                citation_matches.append((citation_num, match.group(0)))
                # Platzhalter: Eindeutiger String der nicht im Markdown-Text vorkommt
                return f"<<<CITE{placeholder_id}>>>"
            
            text_with_placeholders = re.sub(citation_pattern, replace_citation, text)
            
            # 🔍 DEBUG: Zeige Text mit Platzhaltern
            logger.debug(f"🔍 Mit Platzhaltern (erste 200 Zeichen): {text_with_placeholders[:200]}")
            logger.debug(f"🔍 Gefundene Citations: {len(citation_matches)}")
            
            # Schritt 2: Rendere Markdown (mit Platzhaltern)
            self.markdown_renderer.render_markdown(text_with_placeholders, tag)
            
            # Schritt 3: Ersetze Platzhalter durch klickbare Citations
            # Durchsuche Text-Widget nach Platzhaltern
            logger.debug(f"🔍 Ersetze {len(citation_matches)} Platzhalter durch Citations...")
            
            for i, (citation_num, original_text) in enumerate(citation_matches):
                placeholder = f"<<<CITE{i}>>>"
                
                # Finde Platzhalter im Text-Widget
                start_pos = '1.0'
                placeholder_count = 0
                while True:
                    start_pos = self.text_widget.search(placeholder, start_pos, tk.END)
                    if not start_pos:
                        break
                    
                    placeholder_count += 1
                    
                    # Berechne End-Position
                    end_pos = f"{start_pos}+{len(placeholder)}c"
                    
                    # Lösche Platzhalter
                    self.text_widget.delete(start_pos, end_pos)
                    
                    # Füge klickbare Citation ein
                    # Prüfe, ob Citation-Number gültig ist
                    if 1 <= citation_num <= len(self.sources):
                        # Speichere aktuelle Position
                        current_mark = self.text_widget.index(start_pos)
                        
                        # Füge Citation ein
                        citation_text = f'[{citation_num}]'
                        tag_name = f'citation_{citation_num}'
                        self.text_widget.insert(start_pos, citation_text, tag_name)
                        
                        # Konfiguriere Citation-Tag (nur einmal)
                        self._configure_citation_tag(tag_name, citation_num)
                    else:
                        # Ungültige Citation
                        self.text_widget.insert(start_pos, original_text)
                        logger.warning(f"⚠️ Ungültige Citation: {original_text}")
                    
                    # Nächste Position
                    start_pos = f"{start_pos}+1c"
                
                logger.debug(f"  ✓ Platzhalter {i} (Citation [{citation_num}]): {placeholder_count}x gefunden und ersetzt")
            
            logger.debug(f"✅ Markdown + {len(citation_matches)} Citations gerendert")
        
        else:
            # === PLAIN-TEXT FALLBACK (wie bisher) ===
            # Prüfe, ob Text {cite:...} oder [N] Format verwendet
            if '{cite:' in text:
                # Pattern für Citations: {cite:source_id}
                citation_pattern = r'\{cite:([^\}]+)\}'
                
                # Split Text in Chunks und Citations
                parts = re.split(citation_pattern, text)
                
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        # Regular Text (ohne Citation)
                        if part is not None:
                            self.text_widget.insert('end', part, tag)
                    else:
                        # Citation-Marker (source_id)
                        source_id = part
                        citation_num = self.source_to_number.get(source_id, 0)
                        
                        if citation_num > 0:
                            self._insert_citation(citation_num)
                        else:
                            # Fallback: Unbekannte Source
                            self.text_widget.insert('end', f'[?]')
                            logger.warning(f"Unbekannte Citation-Source: {source_id}")
            else:
                # ✨ Format: Backend liefert direkt [1], [2], [3] im Text
                citation_pattern = r'\[(\d+)\]'
                
                # Finde alle Citation-Positionen
                last_end = 0
                for match in re.finditer(citation_pattern, text):
                    # Text vor der Citation
                    before_text = text[last_end:match.start()]
                    if before_text:
                        self.text_widget.insert('end', before_text, tag)
                    
                    # Citation-Number
                    citation_num = int(match.group(1))
                    
                    # Prüfe, ob Citation-Number gültig ist
                    if 1 <= citation_num <= len(self.sources):
                        self._insert_citation(citation_num)
                    else:
                        # Ungültige Citation-Number: Als normaler Text anzeigen
                        self.text_widget.insert('end', match.group(0), tag)
                        logger.warning(f"⚠️ Ungültige Citation-Number: {citation_num} (max: {len(self.sources)})")
                    
                    last_end = match.end()
                
                # Rest des Textes (nach letzter Citation)
                if last_end < len(text):
                    remaining_text = text[last_end:]
                    if remaining_text:
                        self.text_widget.insert('end', remaining_text, tag)
    
    def _configure_citation_tag(self, tag_name: str, citation_num: int):
        """
        Konfiguriert ein Citation-Tag (nur einmal pro Tag)
        
        Args:
            tag_name: Name des Tags (z.B. 'citation_1')
            citation_num: Citation-Number (1, 2, 3, ...)
        """
        
        # Tags werden immer neu konfiguriert (kein Caching nötig, Tkinter ist schnell genug)
        
        # Styling für Citation
        self.text_widget.tag_config(
            tag_name,
            foreground=CITATION_COLORS['citation_text'],
            font=('Segoe UI', 10, 'bold'),
            underline=False  # Kein Underline (ist ja keine URL)
        )
        
        # Click-Handler: Scrolle zu Quellenverzeichnis
        self.text_widget.tag_bind(
            tag_name,
            '<Button-1>',
            lambda e, num=citation_num: self._on_citation_click(num)
        )
        
        # Hover-Effekt
        self.text_widget.tag_bind(
            tag_name,
            '<Enter>',
            lambda e, tag=tag_name: self._on_citation_hover_enter(tag)
        )
        
        self.text_widget.tag_bind(
            tag_name,
            '<Leave>',
            lambda e, tag=tag_name: self._on_citation_hover_leave(tag)
        )
        
        # Cursor ändern bei Hover
        self.text_widget.tag_bind(
            tag_name,
            '<Enter>',
            lambda e: self.text_widget.config(cursor='hand2')
        )
        self.text_widget.tag_bind(
            tag_name,
            '<Leave>',
            lambda e: self.text_widget.config(cursor='')
        )
        
        # Tooltip mit Source-Details
        self._add_citation_tooltip(tag_name, citation_num)
    
    def _insert_citation(self, citation_num: int):
        """
        Fügt einzelne Citation [N] ein mit Styling und Interaktivität
        
        Args:
            citation_num: Citation-Number (1, 2, 3, ...)
        """
        
        # Citation-Text
        citation_text = f'[{citation_num}]'
        
        # Eindeutiger Tag für diese Citation
        tag_name = f'citation_{citation_num}'
        
        # Insert mit Tag
        start_pos = self.text_widget.index('end-1c')
        self.text_widget.insert('end', citation_text, tag_name)
        end_pos = self.text_widget.index('end-1c')
        
        # Konfiguriere Tag
        self._configure_citation_tag(tag_name, citation_num)
    
    def _on_citation_click(self, citation_num: int):
        """Behandelt Click auf Citation → Scrolle zu Quellenverzeichnis"""
        logger.info(f"Citation [{citation_num}] geklickt")
        
        if self.scroll_to_reference_callback:
            try:
                self.scroll_to_reference_callback(citation_num)
            except Exception as e:
                logger.error(f"Scroll-to-Reference Fehler: {e}")
    
    def _on_citation_hover_enter(self, tag_name: str):
        """Hover-Enter: Färbe Citation dunkler"""
        self.text_widget.tag_config(
            tag_name,
            foreground=CITATION_COLORS['citation_hover'],
            background=CITATION_COLORS['citation_bg']
        )
    
    def _on_citation_hover_leave(self, tag_name: str):
        """Hover-Leave: Zurück zu Normal-Farbe"""
        self.text_widget.tag_config(
            tag_name,
            foreground=CITATION_COLORS['citation_text'],
            background=''
        )
    
    def _add_citation_tooltip(self, tag_name: str, citation_num: int):
        """
        Fügt Tooltip mit Source-Details hinzu (mit IEEE-Metadata)
        
        Args:
            tag_name: Tkinter Tag-Name
            citation_num: Citation-Number
        """
        
        # Hole Source für diese Citation
        if citation_num <= len(self.sources):
            source = self.sources[citation_num - 1]
            
            # Build Tooltip-Text mit vollständigen IEEE-Feldern
            tooltip_lines = []
            
            # ✨ IEEE Citation (formatiert)
            if 'ieee_citation' in source:
                tooltip_lines.append(f"📖 {source['ieee_citation']}")
                tooltip_lines.append("")
            else:
                # Fallback: Title
                if 'title' in source:
                    tooltip_lines.append(f"📄 {source['title']}")
            
            # ✨ Authors (mit et al. Unterstützung)
            if 'authors' in source:
                tooltip_lines.append(f"👥 Authors: {source['authors']}")
            
            # ✨ Date/Year
            if 'date' in source:
                tooltip_lines.append(f"📅 Date: {source['date']}")
            elif 'year' in source:
                tooltip_lines.append(f"📅 Year: {source['year']}")
            
            # ✨ Original Source
            if 'original_source' in source:
                tooltip_lines.append(f"📚 Source: {source['original_source']}")
            
            # ✨ Scores (5 verschiedene Metriken)
            scores = []
            if 'similarity_score' in source:
                scores.append(f"Similarity: {source['similarity_score']:.2%}")
            if 'rerank_score' in source:
                scores.append(f"Rerank: {source['rerank_score']:.2%}")
            if 'quality_score' in source:
                scores.append(f"Quality: {source['quality_score']:.2%}")
            if 'confidence' in source:
                conf = source['confidence']
                if isinstance(conf, (int, float)):
                    scores.append(f"Confidence: {conf:.2%}")
            
            if scores:
                tooltip_lines.append("")
                tooltip_lines.append(f"📊 Scores: {' | '.join(scores)}")
            
            # ✨ Impact & Relevance
            classification = []
            if 'impact' in source:
                tooltip_lines.append(f"💎 Impact: {source['impact']}")
            if 'relevance' in source:
                tooltip_lines.append(f"🎯 Relevance: {source['relevance']}")
            
            # ✨ Legal-Specific Metadata
            if 'rechtsgebiet' in source:
                tooltip_lines.append(f"⚖️ Rechtsgebiet: {source['rechtsgebiet']}")
            if 'behoerde' in source:
                tooltip_lines.append(f"🏛️ Behörde: {source['behoerde']}")
            
            # Page/Section
            if 'page' in source:
                tooltip_lines.append(f"📄 Page: {source['page']}")
            if 'section' in source:
                tooltip_lines.append(f"📑 Section: {source['section']}")
            
            # ✨ Ingestion Date
            if 'ingestion_date' in source:
                tooltip_lines.append(f"📥 Ingested: {source['ingestion_date']}")
            
            # DOI/URL
            if 'doi' in source:
                tooltip_lines.append(f"🔗 DOI: {source['doi']}")
            elif 'url' in source:
                url = source['url']
                if len(url) > 60:
                    url = url[:57] + '...'
                tooltip_lines.append(f"🌐 URL: {url}")
            elif 'file' in source:
                tooltip_lines.append(f"📁 File: {source['file']}")
            
            # Snippet (falls vorhanden)
            if 'snippet' in source:
                snippet = source['snippet']
                if len(snippet) > 150:
                    snippet = snippet[:147] + '...'
                tooltip_lines.append(f"\n💬 \"{snippet}\"")
            
            tooltip_text = '\n'.join(tooltip_lines)
            
            # Erstelle Tooltip (einfache Implementierung)
            # TODO: Verwende SourceTooltip aus veritas_ui_components.py
            # Für jetzt: Simple Balloon-Tooltip
            
            # Note: Tkinter hat kein natives Tooltip-System
            # Workaround: Erstelle eigenes Tooltip-Window bei Hover
            # (Bereits durch Hover-Effekt implementiert)
            
            logger.debug(f"Tooltip für [{citation_num}]: {tooltip_text[:100]}...")


# === IEEE REFERENCE FORMATTER ===

class IEEEReferenceFormatter:
    """
    Formatiert Quellenverzeichnis nach IEEE-Standard
    
    IEEE Format je nach Source-Type:
    
    Journal:
        [1] J. Smith and A. Doe, "Article title," IEEE Trans. Pattern Anal., 
            vol. 42, no. 3, pp. 567-589, Mar. 2020.
    
    Book:
        [2] A. Author, Book Title, 2nd ed. Publisher City, State: Publisher, 2019.
    
    Web:
        [3] "Page Title," Website Name. URL (accessed Date).
    
    PDF/Document:
        [4] Author, "Document Title," Organization, Year, pp. Pages.
    
    Database Entry:
        [5] "Entry Title," Database Name, ID: 12345, accessed Oct. 17, 2025.
    """
    
    def __init__(self, sources: List[Dict[str, Any]]):
        """
        Args:
            sources: Liste von Source-Dicts mit Metadaten
        """
        self.sources = sources
    
    def format_all_references(self) -> List[str]:
        """
        Formatiert alle Sources als IEEE-References
        
        Returns:
            Liste von formatierten Reference-Strings
        """
        references = []
        
        for idx, source in enumerate(self.sources, start=1):
            ref = self.format_single_reference(idx, source)
            references.append(ref)
        
        return references
    
    def format_single_reference(self, number: int, source: Dict[str, Any]) -> str:
        """
        Formatiert einzelne Source nach IEEE-Standard (mit vollständigen Metadata-Feldern)
        
        Args:
            number: Reference-Number ([1], [2], ...)
            source: Source-Dict mit Metadaten (inkl. IEEE-Felder vom Backend)
        
        Returns:
            Formatierter Reference-String
        """
        
        # ✨ Nutze vorgefertigten ieee_citation String vom Backend (falls vorhanden)
        if 'ieee_citation' in source:
            # Backend liefert bereits vollständig formatierte Citation
            return source['ieee_citation']
        
        # Fallback: Eigene Formatierung basierend auf Source-Type
        # (für Abwärtskompatibilität mit alten API-Responses)
        
        # Erkenne Source-Type
        source_type = self._detect_source_type(source)
        
        # Format je nach Type
        if source_type == 'pdf':
            return self._format_pdf(number, source)
        elif source_type == 'web':
            return self._format_web(number, source)
        elif source_type == 'database':
            return self._format_database(number, source)
        elif source_type == 'book':
            return self._format_book(number, source)
        else:
            # Fallback: Generic Format mit neuen Feldern
            return self._format_generic_enhanced(number, source)
    
    def _detect_source_type(self, source: Dict[str, Any]) -> str:
        """Erkennt Source-Type aus Metadaten"""
        
        if 'url' in source:
            return 'web'
        elif 'file' in source:
            filename = source['file'].lower()
            if filename.endswith('.pdf'):
                return 'pdf'
            elif filename.endswith(('.doc', '.docx')):
                return 'document'
            elif filename.endswith(('.txt', '.md')):
                return 'text'
        elif 'database' in source or 'db' in source:
            return 'database'
        elif 'isbn' in source or 'publisher' in source:
            return 'book'
        
        return 'generic'
    
    def _format_pdf(self, number: int, source: Dict[str, Any]) -> str:
        """Formatiert PDF nach IEEE-Standard (mit Enhanced Metadata)"""
        
        parts = [f'[{number}]']
        
        # ✨ Authors (bevorzugt das neue authors-Feld)
        if 'authors' in source:
            parts.append(f"{source['authors']},")
        elif 'author' in source:
            parts.append(f"{source['author']},")
        
        # Title
        if 'title' in source:
            parts.append(f'"{source["title"]},"')
        elif 'file' in source:
            # Fallback: Filename als Title
            filename = source['file'].split('/')[-1].replace('.pdf', '')
            parts.append(f'"{filename},"')
        
        # ✨ Original Source (neue Feld)
        if 'original_source' in source:
            parts.append(f"{source['original_source']},")
        # Organization/Publisher (Legacy)
        elif 'organization' in source:
            parts.append(f"{source['organization']},")
        
        # ✨ Year (bevorzugt das neue year-Feld)
        if 'year' in source:
            parts.append(f"{source['year']},")
        
        # Pages
        if 'page' in source:
            parts.append(f"pp. {source['page']}.")
        elif 'pages' in source:
            parts.append(f"pp. {source['pages']}.")
        
        # ✨ DOI (neues Feld)
        if 'doi' in source:
            parts.append(f"DOI: {source['doi']}.")
        
        # ✨ Quality Indicators
        quality_parts = []
        if 'impact' in source:
            quality_parts.append(f"Impact: {source['impact']}")
        if 'relevance' in source:
            quality_parts.append(f"Relevance: {source['relevance']}")
        if 'score' in source:
            quality_parts.append(f"Score: {source['score']:.2f}")
        
        if quality_parts:
            parts.append(f"[{', '.join(quality_parts)}]")
        
        return ' '.join(parts)
    
    def _format_web(self, number: int, source: Dict[str, Any]) -> str:
        """Formatiert Web-URL nach IEEE-Standard (mit Enhanced Metadata)"""
        
        parts = [f'[{number}]']
        
        # ✨ Authors (falls bei Web-Quellen vorhanden)
        if 'authors' in source:
            parts.append(f"{source['authors']},")
        
        # Title (falls vorhanden)
        if 'title' in source:
            parts.append(f'"{source["title"]},"')
        
        # ✨ Original Source (bevorzugt)
        if 'original_source' in source:
            parts.append(f"{source['original_source']}.")
        # Website Name (Legacy)
        elif 'website' in source:
            parts.append(f"{source['website']}.")
        
        # URL
        if 'url' in source:
            url = source['url']
            # Kürze sehr lange URLs
            if len(url) > 80:
                url = url[:77] + '...'
            parts.append(url)
        
        # ✨ Ingestion Date (bevorzugt)
        if 'ingestion_date' in source:
            parts.append(f"(Retrieved: {source['ingestion_date']}).")
        # Access Date (Legacy)
        elif 'access_date' in source:
            parts.append(f"(accessed {source['access_date']}).")
        else:
            # Fallback: Aktuelles Datum
            access_date = datetime.now().strftime('%b. %d, %Y')
            parts.append(f"(accessed {access_date}).")
        
        # ✨ Quality Indicators
        quality_parts = []
        if 'relevance' in source:
            quality_parts.append(f"Relevance: {source['relevance']}")
        if 'score' in source:
            quality_parts.append(f"Score: {source['score']:.2f}")
        
        if quality_parts:
            parts.append(f"[{', '.join(quality_parts)}]")
        
        return ' '.join(parts)
    
    def _format_database(self, number: int, source: Dict[str, Any]) -> str:
        """Formatiert Database-Entry nach IEEE-Standard (mit Enhanced Metadata)"""
        
        parts = [f'[{number}]']
        
        # ✨ Authors (falls vorhanden)
        if 'authors' in source:
            parts.append(f"{source['authors']},")
        
        # Entry Title
        if 'title' in source:
            parts.append(f'"{source["title"]},"')
        elif 'entry_id' in source:
            parts.append(f'"Entry {source["entry_id"]},"')
        
        # Database Name
        if 'database' in source:
            parts.append(f"{source['database']},")
        elif 'db' in source:
            parts.append(f"{source['db']},")
        
        # ID
        if 'id' in source:
            parts.append(f"ID: {source['id']},")
        
        # ✨ Ingestion Date (bevorzugt)
        if 'ingestion_date' in source:
            parts.append(f"Retrieved: {source['ingestion_date']}.")
        # Access Date (Legacy)
        elif 'access_date' in source:
            parts.append(f"accessed {source['access_date']}.")
        else:
            access_date = datetime.now().strftime('%b. %d, %Y')
            parts.append(f"accessed {access_date}.")
        
        # ✨ Legal Metadata (speziell für Database-Entries)
        legal_parts = []
        if 'rechtsgebiet' in source:
            legal_parts.append(f"Rechtsgebiet: {source['rechtsgebiet']}")
        if 'behoerde' in source:
            legal_parts.append(f"Behörde: {source['behoerde']}")
        
        if legal_parts:
            parts.append(f"[{'; '.join(legal_parts)}]")
        
        # ✨ Quality Indicators
        quality_parts = []
        if 'impact' in source:
            quality_parts.append(f"Impact: {source['impact']}")
        if 'relevance' in source:
            quality_parts.append(f"Relevance: {source['relevance']}")
        
        if quality_parts:
            parts.append(f"[{', '.join(quality_parts)}]")
        
        return ' '.join(parts)
    
    def _format_book(self, number: int, source: Dict[str, Any]) -> str:
        """Formatiert Buch nach IEEE-Standard (mit Enhanced Metadata)"""
        
        parts = [f'[{number}]']
        
        # ✨ Authors (bevorzugt das neue authors-Feld mit et al.)
        if 'authors' in source:
            parts.append(f"{source['authors']},")
        # Author (Legacy)
        elif 'author' in source:
            parts.append(f"{source['author']},")
        
        # Title
        if 'title' in source:
            parts.append(f"{source['title']},")
        
        # Edition (optional)
        if 'edition' in source:
            parts.append(f"{source['edition']} ed.")
        
        # ✨ Original Source (kann Publisher ersetzen)
        if 'original_source' in source:
            parts.append(f"{source['original_source']},")
        # Publisher (Legacy)
        elif 'publisher' in source:
            parts.append(f"{source['publisher']},")
        
        # Year
        if 'year' in source:
            parts.append(f"{source['year']}.")
        
        # ✨ DOI (falls vorhanden)
        if 'doi' in source:
            parts.append(f"DOI: {source['doi']}.")
        
        # ✨ Quality Indicators
        quality_parts = []
        if 'impact' in source:
            quality_parts.append(f"Impact: {source['impact']}")
        if 'relevance' in source:
            quality_parts.append(f"Relevance: {source['relevance']}")
        
        if quality_parts:
            parts.append(f"[{', '.join(quality_parts)}]")
        
        return ' '.join(parts)
    
    def _format_generic(self, number: int, source: Dict[str, Any]) -> str:
        """Fallback: Generisches Format für unbekannte Types (Legacy)"""
        
        parts = [f'[{number}]']
        
        # File oder URL
        if 'file' in source:
            parts.append(f"{source['file']}")
        elif 'url' in source:
            parts.append(f"{source['url']}")
        
        # Confidence (als Quality-Indicator)
        if 'confidence' in source:
            conf = source['confidence']
            if isinstance(conf, (int, float)):
                parts.append(f"(Confidence: {conf:.0%})")
        
        return ' '.join(parts) + '.'
    
    def _format_generic_enhanced(self, number: int, source: Dict[str, Any]) -> str:
        """
        ✨ Enhanced Generic Format mit vollständigen IEEE-Feldern
        
        Verwendet neue Backend-Felder:
        - authors (mit et al.)
        - title
        - original_source
        - year/date
        - scores (similarity, rerank, quality, confidence)
        - impact, relevance
        - rechtsgebiet, behoerde (Legal)
        - doi, url, page, section
        """
        
        parts = [f'[{number}]']
        
        # ✨ Authors (mit et al. Unterstützung)
        if 'authors' in source:
            parts.append(f"{source['authors']},")
        
        # ✨ Title (in Anführungszeichen für IEEE-Konformität)
        if 'title' in source:
            parts.append(f'"{source["title"]},"')
        
        # ✨ Original Source / Publication
        if 'original_source' in source:
            parts.append(f"{source['original_source']},")
        elif 'website' in source:
            parts.append(f"{source['website']},")
        
        # ✨ Year (aus year oder date extrahiert)
        if 'year' in source:
            parts.append(f"{source['year']},")
        elif 'date' in source:
            # Versuche Jahr aus Datum zu extrahieren
            date_str = source['date']
            year_match = re.search(r'\b(19|20)\d{2}\b', str(date_str))
            if year_match:
                parts.append(f"{year_match.group()},")
        
        # Page/Section
        if 'page' in source:
            parts.append(f"pp. {source['page']},")
        elif 'section' in source:
            parts.append(f"sec. {source['section']},")
        
        # ✨ DOI (IEEE-Standard)
        if 'doi' in source:
            parts.append(f"DOI: {source['doi']},")
        
        # ✨ URL (als Fallback wenn kein DOI)
        elif 'url' in source:
            url = source['url']
            if len(url) > 60:
                url = url[:57] + '...'
            parts.append(f"{url},")
        
        # ✨ Ingestion/Access Date
        if 'ingestion_date' in source:
            parts.append(f"Retrieved: {source['ingestion_date']},")
        elif 'access_date' in source:
            parts.append(f"accessed {source['access_date']},")
        
        # ✨ Quality Indicators: Scores + Impact + Relevance
        quality_parts = []
        
        # Best Score (bevorzugt)
        if 'score' in source:
            quality_parts.append(f"Score: {source['score']:.2f}")
        elif 'rerank_score' in source:
            quality_parts.append(f"Score: {source['rerank_score']:.2f}")
        elif 'similarity_score' in source:
            quality_parts.append(f"Score: {source['similarity_score']:.2f}")
        
        # Impact
        if 'impact' in source:
            quality_parts.append(f"Impact: {source['impact']}")
        
        # Relevance
        if 'relevance' in source:
            quality_parts.append(f"Relevance: {source['relevance']}")
        
        if quality_parts:
            parts.append(f"[{', '.join(quality_parts)}]")
        
        # ✨ Legal Metadata (optional, in Klammern)
        legal_parts = []
        if 'rechtsgebiet' in source:
            legal_parts.append(f"Rechtsgebiet: {source['rechtsgebiet']}")
        if 'behoerde' in source:
            legal_parts.append(f"Behörde: {source['behoerde']}")
        
        if legal_parts:
            parts.append(f"({'; '.join(legal_parts)})")
        
        return ' '.join(parts) + '.'


# === INTEGRATION MIT METADATA WRAPPER ===

def add_ieee_references_section(
    text_widget: tk.Text,
    sources: List[Dict[str, Any]],
    collapsible: bool = True
) -> Optional[str]:
    """
    Fügt IEEE-Quellenverzeichnis als Section hinzu
    
    Args:
        text_widget: Tkinter Text Widget
        sources: Liste von Source-Dicts
        collapsible: Ob Section collapsible sein soll
    
    Returns:
        Start-Index der References-Section (für Scroll-to-Reference)
    """
    
    if not sources:
        return None
    
    # Formatiere alle References
    formatter = IEEEReferenceFormatter(sources)
    references = formatter.format_all_references()
    
    # Header
    header_start = text_widget.index('end-1c')
    text_widget.insert('end', '\n📚 References (IEEE Standard)\n', 'references_header')
    text_widget.tag_config(
        'references_header',
        font=('Segoe UI', 10, 'bold'),
        foreground='#424242',
        spacing1=10,
        spacing3=5
    )
    
    # References
    for ref in references:
        text_widget.insert('end', f'{ref}\n', 'reference_item')
    
    # Styling für Reference-Items
    text_widget.tag_config(
        'reference_item',
        font=('Segoe UI', 9),
        foreground=CITATION_COLORS['reference_text'],
        lmargin1=20,  # Indent
        lmargin2=40,  # Hanging indent
        spacing1=3
    )
    
    # Highlight für [N] in References
    # Pattern: [1], [2], [3], ...
    for i, ref in enumerate(references, start=1):
        # Finde Position von [N] in Reference
        ref_number = f'[{i}]'
        # Tag für Number-Highlight
        # (Komplexer: Würde Tag-Ranges im Text-Widget benötigen)
        # Für jetzt: Einfaches Styling
    
    logger.info(f"IEEE References-Section hinzugefügt: {len(references)} Quellen")
    
    return header_start


# === EXPORT ===

__all__ = [
    'IEEECitationRenderer',
    'IEEEReferenceFormatter',
    'add_ieee_references_section',
    'CITATION_COLORS'
]
