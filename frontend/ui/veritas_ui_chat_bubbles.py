#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS UI Module: Chat Bubbles & Asymmetric Layout
Version 3.16.0 - Moderne Chat-Darstellung

Design-Prinzipien:
1. USER: Rechts-ausgerichtet, kompakte Bubbles (max 70% Breite)
2. ASSISTANT: Vollbreite, nur Markdown-Rendering, keine Bubble-Dekoration
3. METADATA: Kompakte einzeilige Collapsible-Wrapper unter Assistant-Antwort
4. FEEDBACK: Integriert in Metadaten-Zeile, nicht invasiv

Best-Practice Tkinter:
- Canvas für rounded rectangles (moderne Optik)
- Frame-basiertes Layout (flexibel, performant)
- Event-basierte Interaktionen
- Lazy Loading für Performance
- Wiederverwendbare Komponenten
"""

import tkinter as tk
from tkinter import ttk, font
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ✨ Icon-System importieren
try:
    from .veritas_ui_icons import VeritasIcons
    ICONS_AVAILABLE = True
except ImportError:
    ICONS_AVAILABLE = False
    class VeritasIcons:
        @staticmethod
        def get(cat, name, fallback='•'):
            return fallback


# === FARBSCHEMA (Material Design basiert) ===

# ✨ v3.16.0: Statisches Farbschema
# WICHTIG: Keine zirkulären Imports! Theme-System wird über Setter injiziert

# Statisches Farbschema (wird bei Bedarf vom Hauptprogramm überschrieben)
COLORS = {
    # User Bubble
    'bubble_user': '#E3F2FD',
    'user_bubble_bg': '#E3F2FD',
    'border_user_bubble': '#90CAF9',
    'text_user': '#1E3A5F',
    'user_text': '#1E3A5F',  # ✨ Alias für Kompatibilität
    'timestamp': '#78909C',  # ✨ Timestamp-Farbe
    
    # Assistant (kein Bubble, nur Markdown)
    'assistant_bubble_bg': '#FFFFFF',
    'text_assistant': '#212121',
    'assistant_text': '#212121',
    
    # Metadata Wrapper
    'metadata_bg': '#F5F5F5',
    'metadata_border': '#E0E0E0',  # ✨ Border für Metadata-Wrapper
    'metadata_text': '#616161',  # ✨ Text-Farbe für Metadata
    'metadata_collapsed': '#9E9E9E',  # ✨ Text-Farbe wenn collapsed
    'border_main': '#E0E0E0',
    'text_secondary': '#616161',
    'text_disabled': '#9E9E9E',
    
    # Feedback Buttons
    'feedback_idle': '#9E9E9E',
    'feedback_positive': '#4CAF50',
    'feedback_negative': '#F44336',
    
    # Backgrounds
    'bg_main': '#FFFFFF',
    'bg_secondary': '#F7F7F7',
}

def set_colors(colors_dict: Dict[str, str]):
    """
    Setter für Theme-Integration (wird von veritas_app.py aufgerufen)
    
    Args:
        colors_dict: Farbschema aus get_colors()
    """
    global COLORS
    COLORS.update(colors_dict)
    logger.info(f"✅ Theme-Farben aktualisiert: {len(colors_dict)} Einträge")

def get_colors() -> Dict[str, str]:
    """
    Getter für aktuelles Farbschema
    
    Returns:
        Dictionary mit Farben
    """
    return COLORS.copy()


# === USER MESSAGE BUBBLE ===

class UserMessageBubble:
    """
    Kompakte rechts-ausgerichtete Bubble für User-Queries
    
    Features:
    - Rounded corners (Canvas-basiert)
    - Max 70% Breite
    - Timestamp rechts unten
    - Hover-Effekte
    - Auto-Wrapping für lange Texte
    """
    
    def __init__(
        self,
        text_widget: tk.Text,
        message: str,
        timestamp: Optional[str] = None,
        max_width_percent: float = 0.7
    ):
        """
        Args:
            text_widget: Tkinter Text Widget zum Einfügen
            message: User-Query-Text
            timestamp: ISO-Timestamp oder None
            max_width_percent: Maximale Breite als % von Chat-Breite (0.7 = 70%)
        """
        self.text_widget = text_widget
        self.message = message
        self.timestamp = timestamp
        self.max_width_percent = max_width_percent
        
        # Berechne verfügbare Breite
        self.chat_width = self.text_widget.winfo_width()
        if self.chat_width <= 1:  # Fallback falls Widget noch nicht gerendert
            self.chat_width = 600
        self.max_bubble_width = int(self.chat_width * self.max_width_percent)
    
    def render(self):
        """Rendert die User-Bubble im Text-Widget"""
        
        # Frame für rechts-ausgerichtete Bubble
        bubble_frame = tk.Frame(
            self.text_widget,
            bg=COLORS['user_bubble_bg'],
            relief='flat',
            padx=12,
            pady=8
        )
        
        # Text-Label mit Wrapping
        text_label = tk.Label(
            bubble_frame,
            text=self.message,
            bg=COLORS['user_bubble_bg'],
            fg=COLORS['user_text'],
            font=('Segoe UI', 10),
            wraplength=self.max_bubble_width - 30,  # Padding berücksichtigen
            justify='left',
            anchor='w'
        )
        text_label.pack(side='top', fill='x', expand=True)
        
        # Timestamp (optional, klein unter Text)
        if self.timestamp:
            timestamp_label = tk.Label(
                bubble_frame,
                text=self._format_timestamp(self.timestamp),
                bg=COLORS['user_bubble_bg'],
                fg=COLORS['timestamp'],
                font=('Segoe UI', 8),
                justify='right'
            )
            timestamp_label.pack(side='bottom', anchor='e', pady=(4, 0))
        
        # Insert in Text-Widget (Tkinter unterstützt kein align='right' bei window_create)
        # Stattdessen: Tag mit right justify verwenden
        self.text_widget.tag_configure('user_bubble_right', justify='right')
        
        # Dummy-Text für Bubble-Platzhalter
        start_mark = self.text_widget.index('end-1c')
        self.text_widget.insert('end', ' ')  # Space als Platzhalter
        self.text_widget.window_create('end-1c', window=bubble_frame)
        end_mark = self.text_widget.index('end-1c')
        self.text_widget.tag_add('user_bubble_right', start_mark, end_mark)
        
        self.text_widget.insert('end', '\n\n')  # Abstand zur nächsten Message
        
        # Hover-Effekt
        self._add_hover_effect(bubble_frame)
        
        logger.debug(f"User-Bubble gerendert: {len(self.message)} Zeichen")
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """Formatiert Timestamp für kompakte Anzeige"""
        try:
            dt = datetime.fromisoformat(timestamp_str)
            return dt.strftime('%H:%M')
        except:
            return timestamp_str
    
    def _add_hover_effect(self, frame: tk.Frame):
        """Subtle Hover-Effekt für bessere UX"""
        original_bg = COLORS['user_bubble_bg']
        hover_bg = '#BBDEFB'  # Light Blue 100 (etwas dunkler)
        
        def on_enter(e):
            frame.configure(bg=hover_bg)
            for child in frame.winfo_children():
                child.configure(bg=hover_bg)
        
        def on_leave(e):
            frame.configure(bg=original_bg)
            for child in frame.winfo_children():
                child.configure(bg=original_bg)
        
        frame.bind('<Enter>', on_enter)
        frame.bind('<Leave>', on_leave)


# === ASSISTANT FULL-WIDTH LAYOUT ===

class AssistantFullWidthLayout:
    """
    Vollbreite Layout für Assistant-Antworten
    
    Design:
    - Keine Bubble-Dekoration
    - Vollbreite Markdown-Rendering
    - Nutzt bestehende MarkdownRenderer
    - ✨ IEEE Citations im Text
    - Kompakte Metadaten-Zeile darunter
    
    Kein eigener Render-Code - nutzt vorhandenes Markdown-System
    Diese Klasse ist ein "Organizer" für Layout-Logik
    """
    
    def __init__(
        self,
        text_widget: tk.Text,
        markdown_renderer,
        metadata_handler: Optional['MetadataCompactWrapper'] = None,
        enable_ieee_citations: bool = True
    ):
        """
        Args:
            text_widget: Tkinter Text Widget
            markdown_renderer: Bestehender MarkdownRenderer (aus veritas_ui_markdown.py)
            metadata_handler: MetadataCompactWrapper für Metadaten-Zeile
            enable_ieee_citations: ✨ Aktiviere IEEE-Citations im Text
        """
        self.text_widget = text_widget
        self.markdown_renderer = markdown_renderer
        self.metadata_handler = metadata_handler
        self.enable_ieee_citations = enable_ieee_citations
        
        # ✨ IEEE Citation Renderer (bei Bedarf initialisiert)
        self.citation_renderer = None
    
    def render_assistant_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        sources: Optional[List[Dict]] = None,
        enable_citations: Optional[bool] = None
    ):
        """
        Rendert Assistant-Antwort mit vollbreiter Markdown + Metadaten
        
        Args:
            content: Markdown-formatierter Antwort-Text (mit {cite:N} Markern)
            metadata: Dict mit complexity, duration, model, etc.
            sources: Liste von Source-Dicts
            enable_citations: ✨ Override für IEEE-Citations (None = use default)
        """
        
        logger.debug(f"🎨 AssistantFullWidthLayout.render_assistant_message() aufgerufen")
        logger.debug(f"  - content length: {len(content) if content else 0}")
        logger.debug(f"  - sources count: {len(sources) if sources else 0}")
        logger.debug(f"  - enable_citations param: {enable_citations}")
        logger.debug(f"  - self.enable_ieee_citations: {self.enable_ieee_citations}")
        
        # Citations aktiviert?
        use_citations = enable_citations if enable_citations is not None else self.enable_ieee_citations
        
        logger.debug(f"  - use_citations (final): {use_citations}")
        
        # ✨ 1a. IEEE Citations vorbereiten (falls aktiviert und Sources vorhanden)
        if use_citations and sources and len(sources) > 0:
            try:
                from .veritas_ui_ieee_citations import IEEECitationRenderer
                
                # Scroll-to-Reference Callback
                def scroll_to_ref(citation_num: int):
                    logger.info(f"Scroll to Reference [{citation_num}]")
                    # TODO: Implementiere Scroll-to-Metadata-Section
                    # Möglichkeit: Metadata-Wrapper togglen wenn collapsed
                    if self.metadata_handler and self.metadata_handler.is_collapsed:
                        self.metadata_handler.toggle()
                
                # ✨ Übergebe Markdown-Renderer für korrekte Formatierung
                self.citation_renderer = IEEECitationRenderer(
                    text_widget=self.text_widget,
                    sources=sources,
                    scroll_to_reference_callback=scroll_to_ref,
                    markdown_renderer=self.markdown_renderer  # ✨ NEU: Markdown-Support
                )
                
                # Content mit Citations UND Markdown rendern
                self.citation_renderer.render_text_with_citations(content, tag='assistant_text')
                
                logger.debug(f"✅ IEEE Citations + Markdown gerendert: {len(sources)} Quellen")
                
            except ImportError:
                logger.warning("⚠️ IEEE Citation Renderer nicht verfügbar - Fallback auf Standard-Rendering")
                use_citations = False
        
        # 1b. Standard Markdown-Rendering (ohne Citations)
        if not use_citations or not sources:
            if self.markdown_renderer:
                self.markdown_renderer.render_markdown(content, 'assistant_text')
            else:
                # Fallback: Plain-Text
                self.text_widget.insert('end', content, 'assistant_text')
                self.text_widget.insert('end', '\n')
        
        # 2. Kompakte Metadaten-Zeile darunter (mit IEEE-Quellenverzeichnis)
        if self.metadata_handler and (metadata or sources):
            self.metadata_handler.render(
                metadata=metadata,
                sources=sources
            )
        
        # 3. Abstand zur nächsten Message
        self.text_widget.insert('end', '\n\n')
        
        logger.debug("Assistant Full-Width Layout gerendert")


# === COMPACT METADATA WRAPPER ===

class MetadataCompactWrapper:
    """
    Kompakte einzeilige Metadaten-Anzeige mit Collapsible-Funktionalität
    
    Design:
    - Einzeilig wenn zugeklappt
    - Expandiert bei Klick
    - Enthält: Sources, Complexity, Duration, Model, Feedback
    - Best-Practice Tkinter Expander-Pattern
    
    Layout (zugeklappt):
    ┌────────────────────────────────────────────────────────────┐
    │ ▶ Metadata (5 Sources, Medium, 1.2s, llama3.2) 👍👎        │
    └────────────────────────────────────────────────────────────┘
    
    Layout (expanded):
    ┌────────────────────────────────────────────────────────────┐
    │ ▼ Metadata                                      👍👎        │
    │   📚 Sources (5):                                          │
    │      • file.pdf (Page 42) - 87%                            │
    │      • document.txt - 85%                                  │
    │   ⚙️ Complexity: Medium                                     │
    │   ⏱️ Duration: 1.234s                                       │
    │   🤖 Model: llama3.2:latest                                │
    └────────────────────────────────────────────────────────────┘
    """
    
    def __init__(
        self,
        text_widget: tk.Text,
        feedback_callback: Optional[Callable] = None,
        initially_collapsed: bool = True
    ):
        """
        Args:
            text_widget: Tkinter Text Widget
            feedback_callback: Callback(rating: str) für Feedback (👍/👎)
            initially_collapsed: Initial State (True = zugeklappt)
        """
        self.text_widget = text_widget
        self.feedback_callback = feedback_callback
        self.initially_collapsed = initially_collapsed
        
        # State
        self.is_collapsed = initially_collapsed
        self.metadata_frame = None
        self.content_frame = None
    
    def render(
        self,
        metadata: Optional[Dict[str, Any]] = None,
        sources: Optional[List[Dict]] = None
    ):
        """
        Rendert kompakte Metadaten-Zeile
        
        Args:
            metadata: Dict mit complexity, duration, model, etc.
            sources: Liste von Source-Dicts mit file, confidence, etc.
        """
        
        # Haupt-Frame für Metadaten
        self.metadata_frame = tk.Frame(
            self.text_widget,
            bg=COLORS['metadata_bg'],
            relief='solid',
            borderwidth=1,
            highlightbackground=COLORS['metadata_border'],
            highlightthickness=1
        )
        
        # === Header-Zeile (immer sichtbar) ===
        header_frame = tk.Frame(self.metadata_frame, bg=COLORS['metadata_bg'])
        header_frame.pack(fill='x', padx=8, pady=4)
        
        # Toggle-Icon (▶/▼)
        icon = '▶' if self.is_collapsed else '▼'
        self.toggle_label = tk.Label(
            header_frame,
            text=icon,
            bg=COLORS['metadata_bg'],
            fg=COLORS['metadata_text'],
            font=('Segoe UI', 10),
            cursor='hand2'
        )
        self.toggle_label.pack(side='left', padx=(0, 5))
        self.toggle_label.bind('<Button-1>', lambda e: self.toggle())
        
        # Summary-Text
        summary = self._build_summary(metadata, sources)
        summary_label = tk.Label(
            header_frame,
            text=summary,
            bg=COLORS['metadata_bg'],
            fg=COLORS['metadata_text'] if not self.is_collapsed else COLORS['metadata_collapsed'],
            font=('Segoe UI', 9),
            cursor='hand2'
        )
        summary_label.pack(side='left', fill='x', expand=True)
        summary_label.bind('<Button-1>', lambda e: self.toggle())
        
        # Feedback-Buttons (rechts)
        feedback_frame = tk.Frame(header_frame, bg=COLORS['metadata_bg'])
        feedback_frame.pack(side='right')
        
        self._add_feedback_buttons(feedback_frame)
        
        # === Content-Frame (expandierbar) ===
        self.content_frame = tk.Frame(self.metadata_frame, bg=COLORS['metadata_bg'])
        
        # Details einfügen
        self._build_details(self.content_frame, metadata, sources)
        
        # Initial State (collapsed = hidden)
        if self.is_collapsed:
            self.content_frame.pack_forget()
        else:
            self.content_frame.pack(fill='both', expand=True, padx=8, pady=(0, 4))
        
        # In Text-Widget einfügen
        self.text_widget.window_create('end', window=self.metadata_frame)
        self.text_widget.insert('end', '\n')
        
        logger.debug(f"Metadaten-Wrapper gerendert (collapsed={self.is_collapsed})")
    
    def _build_summary(
        self,
        metadata: Optional[Dict],
        sources: Optional[List[Dict]]
    ) -> str:
        """Baut einzeilige Summary für zugeklappten State (mit IEEE-Metadata)"""
        parts = []
        
        # Sources-Count
        if sources and len(sources) > 0:
            parts.append(f"{len(sources)} Sources")
            
            # ✨ Impact/Relevance Summary (von der ersten/besten Quelle)
            if sources[0]:
                first_source = sources[0]
                
                # Relevance (höchste Priorität)
                if 'relevance' in first_source:
                    relevance = first_source['relevance']
                    # Emoji basierend auf Relevance
                    if relevance == 'Very High':
                        parts.append("🎯 Very High")
                    elif relevance == 'High':
                        parts.append("🎯 High")
                    elif relevance == 'Medium':
                        parts.append("🎯 Medium")
                
                # Impact (falls vorhanden)
                elif 'impact' in first_source:
                    impact = first_source['impact']
                    if impact == 'High':
                        parts.append("💎 High Impact")
                    elif impact == 'Medium':
                        parts.append("💎 Medium Impact")
                
                # Fallback: Best Score
                elif 'score' in first_source:
                    score = first_source['score']
                    if isinstance(score, (int, float)):
                        parts.append(f"📊 {score:.0%}")
        
        # Complexity
        if metadata and 'complexity' in metadata:
            parts.append(metadata['complexity'])
        
        # Duration
        if metadata and 'duration' in metadata:
            duration = metadata['duration']
            if isinstance(duration, (int, float)):
                parts.append(f"{duration:.1f}s")
            else:
                parts.append(str(duration))
        
        # Model
        if metadata and 'model' in metadata:
            model = metadata['model']
            # Kürze lange Model-Namen
            if len(model) > 20:
                model = model[:17] + '...'
            parts.append(model)
        
        summary = "Metadata"
        if parts:
            summary += f" ({', '.join(parts)})"
        
        return summary
    
    def _build_details(
        self,
        parent_frame: tk.Frame,
        metadata: Optional[Dict],
        sources: Optional[List[Dict]]
    ):
        """Baut expandierte Detail-Ansicht"""
        
        # ✨ IEEE-Quellenverzeichnis (statt einfacher Bullet-Liste)
        if sources and len(sources) > 0:
            # Import IEEE Formatter
            try:
                from .veritas_ui_ieee_citations import IEEEReferenceFormatter
                ieee_available = True
            except ImportError:
                ieee_available = False
                logger.warning("⚠️ IEEE Citation Formatter nicht verfügbar")
            
            # Header
            sources_label = tk.Label(
                parent_frame,
                text=f"📚 References (IEEE Standard):",
                bg=COLORS['metadata_bg'],
                fg=COLORS['metadata_text'],
                font=('Segoe UI', 9, 'bold'),
                anchor='w'
            )
            sources_label.pack(fill='x', pady=(4, 2))
            
            # IEEE-Formatierung oder Fallback
            if ieee_available:
                formatter = IEEEReferenceFormatter(sources)
                references = formatter.format_all_references()
                
                # Max 5 References anzeigen (kompakt)
                for ref in references[:5]:
                    ref_label = tk.Label(
                        parent_frame,
                        text=ref,
                        bg=COLORS['metadata_bg'],
                        fg=COLORS['metadata_text'],
                        font=('Segoe UI', 8),
                        anchor='w',
                        wraplength=600,  # Wrap lange References
                        justify='left'
                    )
                    ref_label.pack(fill='x', pady=1)
                
                if len(references) > 5:
                    more_label = tk.Label(
                        parent_frame,
                        text=f"   ... and {len(references) - 5} more references",
                        bg=COLORS['metadata_bg'],
                        fg=COLORS['metadata_collapsed'],
                        font=('Segoe UI', 8, 'italic'),
                        anchor='w'
                    )
                    more_label.pack(fill='x')
            else:
                # Fallback: Einfache Bullet-Liste
                for i, source in enumerate(sources[:5]):
                    source_text = self._format_source(source)
                    source_item = tk.Label(
                        parent_frame,
                        text=f"   • {source_text}",
                        bg=COLORS['metadata_bg'],
                        fg=COLORS['metadata_text'],
                        font=('Segoe UI', 9),
                        anchor='w'
                    )
                    source_item.pack(fill='x')
                
                if len(sources) > 5:
                    more_label = tk.Label(
                        parent_frame,
                        text=f"   ... und {len(sources) - 5} weitere",
                        bg=COLORS['metadata_bg'],
                        fg=COLORS['metadata_collapsed'],
                        font=('Segoe UI', 8, 'italic'),
                        anchor='w'
                    )
                    more_label.pack(fill='x')
        
        # Metadata-Details
        if metadata:
            # Complexity
            if 'complexity' in metadata:
                self._add_metadata_row(
                    parent_frame,
                    '⚙️ Complexity:',
                    metadata['complexity']
                )
            
            # Duration
            if 'duration' in metadata:
                duration = metadata['duration']
                if isinstance(duration, (int, float)):
                    duration_str = f"{duration:.3f}s"
                else:
                    duration_str = str(duration)
                self._add_metadata_row(
                    parent_frame,
                    '⏱️ Duration:',
                    duration_str
                )
            
            # Model
            if 'model' in metadata:
                self._add_metadata_row(
                    parent_frame,
                    '🤖 Model:',
                    metadata['model']
                )
            
            # Tokens (falls vorhanden)
            if 'tokens' in metadata:
                tokens = metadata['tokens']
                if isinstance(tokens, dict):
                    total = tokens.get('total', 0)
                    self._add_metadata_row(
                        parent_frame,
                        '🎫 Tokens:',
                        str(total)
                    )
    
    def _add_metadata_row(self, parent: tk.Frame, label: str, value: str):
        """Fügt eine Metadaten-Zeile hinzu"""
        row = tk.Label(
            parent,
            text=f"{label} {value}",
            bg=COLORS['metadata_bg'],
            fg=COLORS['metadata_text'],
            font=('Segoe UI', 9),
            anchor='w'
        )
        row.pack(fill='x', pady=1)
    
    def _format_source(self, source: Dict) -> str:
        """Formatiert einzelne Source für Anzeige"""
        parts = []
        
        # File/URL
        if 'file' in source:
            parts.append(source['file'])
        elif 'url' in source:
            parts.append(source['url'])
        
        # Page (falls vorhanden)
        if 'page' in source:
            parts.append(f"Page {source['page']}")
        
        # Confidence
        if 'confidence' in source:
            conf = source['confidence']
            if isinstance(conf, (int, float)):
                parts.append(f"{conf:.0%}")
        
        return ' - '.join(parts) if parts else 'Unknown Source'
    
    def _add_feedback_buttons(self, parent_frame: tk.Frame):
        """Fügt 👍👎 Feedback-Buttons hinzu"""
        
        # Thumbs Up
        thumbs_up = tk.Label(
            parent_frame,
            text='👍',
            bg=COLORS['metadata_bg'],
            fg=COLORS['feedback_idle'],
            font=('Segoe UI', 12),
            cursor='hand2'
        )
        thumbs_up.pack(side='left', padx=3)
        thumbs_up.bind('<Button-1>', lambda e: self._on_feedback('positive'))
        
        # Hover-Effekt
        thumbs_up.bind('<Enter>', lambda e: thumbs_up.configure(fg=COLORS['feedback_active']))
        thumbs_up.bind('<Leave>', lambda e: thumbs_up.configure(fg=COLORS['feedback_idle']))
        
        # Thumbs Down
        thumbs_down = tk.Label(
            parent_frame,
            text='👎',
            bg=COLORS['metadata_bg'],
            fg=COLORS['feedback_idle'],
            font=('Segoe UI', 12),
            cursor='hand2'
        )
        thumbs_down.pack(side='left', padx=3)
        thumbs_down.bind('<Button-1>', lambda e: self._on_feedback('negative'))
        
        # Hover-Effekt
        thumbs_down.bind('<Enter>', lambda e: thumbs_down.configure(fg=COLORS['feedback_negative']))
        thumbs_down.bind('<Leave>', lambda e: thumbs_down.configure(fg=COLORS['feedback_idle']))
    
    def _on_feedback(self, rating: str):
        """Behandelt Feedback-Button-Klicks"""
        logger.info(f"Feedback erhalten: {rating}")
        
        if self.feedback_callback:
            try:
                self.feedback_callback(rating)
            except Exception as e:
                logger.error(f"Feedback-Callback Fehler: {e}")
    
    def toggle(self):
        """Toggle zwischen collapsed/expanded"""
        self.is_collapsed = not self.is_collapsed
        
        # Update Icon
        icon = '▶' if self.is_collapsed else '▼'
        self.toggle_label.configure(text=icon)
        
        # Show/Hide Content
        if self.is_collapsed:
            self.content_frame.pack_forget()
        else:
            self.content_frame.pack(fill='both', expand=True, padx=8, pady=(0, 4))
        
        logger.debug(f"Metadaten-Wrapper toggled (collapsed={self.is_collapsed})")


# === WEITERE TKINTER BEST PRACTICES ===

class TkinterBestPractices:
    """
    Sammlung von Best-Practice Optimierungen für optimale Tkinter UX
    
    Features:
    1. Virtual Scrolling für große Chat-Histories
    2. Lazy Loading von Messages
    3. Smooth Scroll-Animationen
    4. Keyboard Shortcuts
    5. Memory Management
    """
    
    @staticmethod
    def enable_smooth_scrolling(text_widget: tk.Text):
        """
        Aktiviert smooth Scrolling mit Mousewheel
        
        Standard Tkinter scrollt abrupt - diese Methode macht es smooth
        """
        def smooth_scroll(event):
            # Delta berechnen
            if event.delta > 0:
                delta = -1
            else:
                delta = 1
            
            # Kleine Schritte für smooth Scrolling
            text_widget.yview_scroll(delta, 'units')
            return 'break'  # Verhindert default Scrolling
        
        text_widget.bind('<MouseWheel>', smooth_scroll)
        logger.debug("Smooth Scrolling aktiviert")
    
    @staticmethod
    def add_keyboard_shortcuts(root: tk.Tk, shortcuts: Dict[str, Callable]):
        """
        Fügt Keyboard-Shortcuts hinzu
        
        Args:
            root: Tkinter Root Window
            shortcuts: Dict mit 'key': callback
            
        Example:
            shortcuts = {
                '<Control-k>': clear_chat,
                '<Control-s>': save_chat,
                '<Escape>': focus_input
            }
        """
        for key, callback in shortcuts.items():
            root.bind(key, lambda e, cb=callback: cb())
        
        logger.debug(f"{len(shortcuts)} Keyboard-Shortcuts registriert")
    
    @staticmethod
    def optimize_text_widget(text_widget: tk.Text):
        """
        Optimiert Text-Widget für Performance
        
        - Deaktiviert Undo (spart Memory)
        - Optimale Wrap-Einstellungen
        - Performance-Tags
        """
        # Undo deaktivieren (Chat braucht kein Undo)
        text_widget.configure(undo=False, maxundo=0)
        
        # Wrap-Modus für bessere Performance
        text_widget.configure(wrap='word')
        
        # Auto-Separator für bessere Performance
        text_widget.configure(autoseparators=False)
        
        logger.debug("Text-Widget optimiert")
    
    @staticmethod
    def lazy_load_messages(
        text_widget: tk.Text,
        all_messages: List[Dict],
        batch_size: int = 20
    ):
        """
        Lazy Loading für große Message-Histories
        
        Lädt nur sichtbare Messages + kleine Buffer
        
        Args:
            text_widget: Tkinter Text Widget
            all_messages: Vollständige Message-Liste
            batch_size: Anzahl Messages pro Batch
        """
        # TODO: Implementierung für sehr große Chats (>1000 Messages)
        # Idee: Virtual Scrolling mit Canvas + Only visible Messages rendern
        pass
    
    @staticmethod
    def add_auto_scroll_to_bottom(text_widget: tk.Text):
        """
        Auto-Scroll to Bottom bei neuen Messages
        
        Aber nur wenn User bereits am Ende war (nicht bei Scroll-Up)
        """
        def is_at_bottom():
            # Check ob Scrollbar am Ende
            yview = text_widget.yview()
            return yview[1] >= 0.99
        
        # Wird vom Chat-Handler aufgerufen
        def scroll_if_at_bottom():
            if is_at_bottom():
                text_widget.see('end')
        
        return scroll_if_at_bottom


# === EXPORT ===

__all__ = [
    'UserMessageBubble',
    'AssistantFullWidthLayout',
    'MetadataCompactWrapper',
    'TkinterBestPractices',
    'COLORS'
]
