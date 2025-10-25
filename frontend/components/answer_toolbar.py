"""
Answer Toolbar - Kompakte Toolbar unter Antworten für VERITAS
==============================================================

Material Design Toolbar mit Feedback, Transfer, und Metadata-Dropdowns.

Features:
- Feedback-Buttons (👍 👎)
- Transfer-Actions (Kopieren, Wiederholen)
- Metadata-Dropdowns (Meta, Quellen, Vorschläge, Raw)
- Kompaktes Design (10pt, 28px Höhe)
- Unaufdringliches Styling (#757575)

Part of the VERITAS frontend components.

Author: VERITAS Development Team
Created: 2025-10-18
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class AnswerToolbar:
    """
    Kompakte Toolbar unter Assistant-Antworten.
    
    Layout:
    [👍 👎] | [📋 Kopieren] [🔄 Wiederholen] | [▼ Meta] [▼ Quellen] [▼ Vorschläge] [▼ Raw]
    
    Design Pattern: Component Pattern with Callbacks
    """
    
    def __init__(
        self,
        parent: tk.Text,
        message_data: Dict[str, Any],
        on_feedback: Optional[Callable[[str, str], None]] = None,
        on_copy: Optional[Callable[[str], None]] = None,
        on_repeat: Optional[Callable[[str], None]] = None,
        on_show_raw: Optional[Callable[[str], None]] = None,
        bg_color: str = "#F9F9F9",
        fg_color: str = "#757575",
        hover_color: str = "#2196F3",
        root_window: Optional[tk.Tk] = None
    ):
        """
        Initialize the AnswerToolbar.
        
        Args:
            parent: Parent Text widget to insert toolbar into
            message_data: Message data dict with content, metadata, sources, etc.
            on_feedback: Callback(message_id, feedback_type) for feedback
            on_copy: Callback(text) for copy action
            on_repeat: Callback(query) for repeat query
            on_show_raw: Callback(raw_response) for raw response dialog
            bg_color: Background color (Material Design Grey 50)
            fg_color: Foreground color (Material Design Grey 600)
            hover_color: Hover color (Material Design Blue 500)
            root_window: Root Tk window (for Toplevel dialogs)
        """
        self.parent = parent
        self.message_data = message_data
        self.on_feedback = on_feedback
        self.on_copy = on_copy
        self.on_repeat = on_repeat
        self.on_show_raw = on_show_raw
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = hover_color
        
        # ✨ v3.18.0: Get root window for Toplevel dialogs
        self.root_window = root_window or self._get_root_window()
        
        # Extract data
        self.message_id = message_data.get('id', 'unknown')
        self.content = message_data.get('content', '')
        self.metadata = message_data.get('metadata', {})
        self.sources = message_data.get('sources', [])
        self.suggestions = message_data.get('suggestions', [])
        self.raw_response = message_data.get('raw_response', '')
        self.original_query = message_data.get('original_query', '')
        
        # State
        self.toolbar_frame: Optional[tk.Frame] = None
        self.metadata_window: Optional[tk.Toplevel] = None
        self.sources_window: Optional[tk.Toplevel] = None
        self.suggestions_window: Optional[tk.Toplevel] = None
        
        logger.debug(f"✅ AnswerToolbar initialisiert für Message {self.message_id}")
    
    def _get_root_window(self) -> tk.Tk:
        """
        ✨ v3.18.0: Get root Tk window from parent widget
        
        Returns:
            Root Tk window
        """
        try:
            widget = self.parent
            while widget:
                if isinstance(widget, tk.Tk):
                    return widget
                widget = widget.master
            # Fallback: Get from nametowidget
            return self.parent.nametowidget('.')
        except Exception as e:
            logger.error(f"Fehler beim Ermitteln des Root-Windows: {e}")
            # Last resort: Return parent
            return self.parent
    
    def render(self):
        """Render toolbar in parent text widget"""
        try:
            # Create frame
            self.toolbar_frame = tk.Frame(
                self.parent,
                bg=self.bg_color,
                height=28,
                relief=tk.FLAT,
                bd=0
            )
            
            # Embed frame in text widget
            self.parent.window_create(tk.END, window=self.toolbar_frame)
            self.parent.insert(tk.END, "\n")
            
            # === SECTION 1: Feedback ===
            self._create_feedback_section()
            
            # Separator
            self._create_separator()
            
            # === SECTION 2: Transfer Actions ===
            self._create_transfer_section()
            
            # Separator
            self._create_separator()
            
            # === SECTION 3: Metadata Dropdowns ===
            self._create_metadata_section()
            
            logger.debug(f"✅ Toolbar gerendert für Message {self.message_id}")
            
        except Exception as e:
            logger.error(f"Fehler beim Rendern der Toolbar: {e}")
    
    def _create_feedback_section(self):
        """Create feedback buttons (👍 👎)"""
        # 👍 Button
        btn_like = tk.Button(
            self.toolbar_frame,
            text="👍",
            command=lambda: self._handle_feedback('positive'),
            relief=tk.FLAT,
            bd=0,
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 10),
            cursor="hand2",
            padx=5,
            pady=2
        )
        btn_like.pack(side=tk.LEFT, padx=2)
        btn_like.bind("<Enter>", lambda e: btn_like.config(fg=self.hover_color))
        btn_like.bind("<Leave>", lambda e: btn_like.config(fg=self.fg_color))
        
        # 👎 Button
        btn_dislike = tk.Button(
            self.toolbar_frame,
            text="👎",
            command=lambda: self._handle_feedback('negative'),
            relief=tk.FLAT,
            bd=0,
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 10),
            cursor="hand2",
            padx=5,
            pady=2
        )
        btn_dislike.pack(side=tk.LEFT, padx=2)
        btn_dislike.bind("<Enter>", lambda e: btn_dislike.config(fg=self.hover_color))
        btn_dislike.bind("<Leave>", lambda e: btn_dislike.config(fg=self.fg_color))
    
    def _create_transfer_section(self):
        """Create transfer action buttons (Kopieren, Wiederholen)"""
        # 📋 Kopieren
        btn_copy = tk.Button(
            self.toolbar_frame,
            text="📋 Kopieren",
            command=self._handle_copy,
            relief=tk.FLAT,
            bd=0,
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 10),
            cursor="hand2",
            padx=5,
            pady=2
        )
        btn_copy.pack(side=tk.LEFT, padx=2)
        btn_copy.bind("<Enter>", lambda e: btn_copy.config(fg=self.hover_color))
        btn_copy.bind("<Leave>", lambda e: btn_copy.config(fg=self.fg_color))
        
        # 🔄 Wiederholen
        btn_repeat = tk.Button(
            self.toolbar_frame,
            text="🔄 Wiederholen",
            command=self._handle_repeat,
            relief=tk.FLAT,
            bd=0,
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 10),
            cursor="hand2",
            padx=5,
            pady=2
        )
        btn_repeat.pack(side=tk.LEFT, padx=2)
        btn_repeat.bind("<Enter>", lambda e: btn_repeat.config(fg=self.hover_color))
        btn_repeat.bind("<Leave>", lambda e: btn_repeat.config(fg=self.fg_color))
    
    def _create_metadata_section(self):
        """Create metadata dropdown buttons"""
        # ▼ Meta
        btn_meta = tk.Button(
            self.toolbar_frame,
            text="▼ Meta",
            command=self._show_metadata,
            relief=tk.FLAT,
            bd=0,
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 10),
            cursor="hand2",
            padx=5,
            pady=2
        )
        btn_meta.pack(side=tk.LEFT, padx=2)
        btn_meta.bind("<Enter>", lambda e: btn_meta.config(fg=self.hover_color))
        btn_meta.bind("<Leave>", lambda e: btn_meta.config(fg=self.fg_color))
        
        # ▼ Quellen
        sources_count = len(self.sources)
        btn_sources = tk.Button(
            self.toolbar_frame,
            text=f"▼ Quellen ({sources_count})",
            command=self._show_sources,
            relief=tk.FLAT,
            bd=0,
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 10),
            cursor="hand2",
            padx=5,
            pady=2
        )
        btn_sources.pack(side=tk.LEFT, padx=2)
        btn_sources.bind("<Enter>", lambda e: btn_sources.config(fg=self.hover_color))
        btn_sources.bind("<Leave>", lambda e: btn_sources.config(fg=self.fg_color))
        
        # ▼ Vorschläge
        suggestions_count = len(self.suggestions)
        btn_suggestions = tk.Button(
            self.toolbar_frame,
            text=f"▼ Vorschläge ({suggestions_count})",
            command=self._show_suggestions,
            relief=tk.FLAT,
            bd=0,
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 10),
            cursor="hand2",
            padx=5,
            pady=2
        )
        btn_suggestions.pack(side=tk.LEFT, padx=2)
        btn_suggestions.bind("<Enter>", lambda e: btn_suggestions.config(fg=self.hover_color))
        btn_suggestions.bind("<Leave>", lambda e: btn_suggestions.config(fg=self.fg_color))
        
        # ▼ Raw
        btn_raw = tk.Button(
            self.toolbar_frame,
            text="▼ Raw",
            command=self._show_raw,
            relief=tk.FLAT,
            bd=0,
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 10),
            cursor="hand2",
            padx=5,
            pady=2
        )
        btn_raw.pack(side=tk.LEFT, padx=2)
        btn_raw.bind("<Enter>", lambda e: btn_raw.config(fg=self.hover_color))
        btn_raw.bind("<Leave>", lambda e: btn_raw.config(fg=self.fg_color))
    
    def _create_separator(self):
        """Create vertical separator"""
        separator = tk.Label(
            self.toolbar_frame,
            text="|",
            bg=self.bg_color,
            fg="#E0E0E0",
            font=("Segoe UI", 10)
        )
        separator.pack(side=tk.LEFT, padx=5)
    
    # === EVENT HANDLERS ===
    
    def _handle_feedback(self, feedback_type: str):
        """Handle feedback button click"""
        try:
            if self.on_feedback:
                self.on_feedback(self.message_id, feedback_type)
            logger.info(f"👍 Feedback: {feedback_type} für Message {self.message_id}")
        except Exception as e:
            logger.error(f"Fehler beim Feedback: {e}")
    
    def _handle_copy(self):
        """Handle copy button click"""
        try:
            # Copy to clipboard
            self.parent.clipboard_clear()
            self.parent.clipboard_append(self.content)
            self.parent.update()
            
            if self.on_copy:
                self.on_copy(self.content)
            
            logger.info(f"📋 In Zwischenablage kopiert: {len(self.content)} Zeichen")
            messagebox.showinfo("Kopiert", "Antwort in Zwischenablage kopiert!")
            
        except Exception as e:
            logger.error(f"Fehler beim Kopieren: {e}")
            messagebox.showerror("Fehler", f"Kopieren fehlgeschlagen: {e}")
    
    def _handle_repeat(self):
        """Handle repeat button click"""
        try:
            if self.on_repeat:
                self.on_repeat(self.original_query)
            logger.info(f"🔄 Wiederholen: {self.original_query}")
        except Exception as e:
            logger.error(f"Fehler beim Wiederholen: {e}")
    
    def _show_metadata(self):
        """Show metadata in popup window"""
        try:
            if self.metadata_window and self.metadata_window.winfo_exists():
                self.metadata_window.lift()
                return
            
            # ✨ v3.18.0: Use root_window for Toplevel
            self.metadata_window = tk.Toplevel(self.root_window)
            self.metadata_window.title("📊 Metadaten")
            self.metadata_window.geometry("500x400")
            
            # Text widget
            text = tk.Text(
                self.metadata_window,
                wrap=tk.WORD,
                font=("Consolas", 10),
                bg="#FAFAFA",
                fg="#212121"
            )
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Format metadata
            import json
            formatted = json.dumps(self.metadata, indent=2, ensure_ascii=False)
            text.insert("1.0", formatted)
            text.config(state=tk.DISABLED)
            
            logger.debug(f"📊 Metadata-Fenster geöffnet")
            
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen der Metadaten: {e}")
            messagebox.showerror("Fehler", f"Metadaten-Anzeige fehlgeschlagen:\n{e}")
    
    def _show_sources(self):
        """Show sources in popup window (mit vollständigen IEEE-Metadaten)"""
        try:
            if self.sources_window and self.sources_window.winfo_exists():
                self.sources_window.lift()
                return
            
            # ✨ v3.18.0: Use root_window for Toplevel
            self.sources_window = tk.Toplevel(self.root_window)
            self.sources_window.title(f"📚 Quellen ({len(self.sources)})")
            self.sources_window.geometry("700x600")
            
            # Scrollable text widget
            text = tk.Text(
                self.sources_window,
                wrap=tk.WORD,
                font=("Segoe UI", 10),
                bg="#FAFAFA",
                fg="#212121"
            )
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Format sources
            if not self.sources:
                text.insert("1.0", "Keine Quellen verfügbar.")
            else:
                for i, source in enumerate(self.sources, 1):
                    # ✨ IEEE Citation (falls vom Backend geliefert)
                    if 'ieee_citation' in source:
                        text.insert(tk.END, f"{source['ieee_citation']}\n\n", "ieee")
                    else:
                        # Fallback: Manuelle Formatierung
                        text.insert(tk.END, f"[{i}] ", "bold")
                        
                        # ✨ Authors (mit et al.)
                        if 'authors' in source:
                            text.insert(tk.END, f"{source['authors']}, ", "authors")
                        
                        # Title
                        title = source.get('title', 'Unbekannter Titel')
                        text.insert(tk.END, f'"{title}"\n', "title")
                        
                        # ✨ Original Source
                        if 'original_source' in source:
                            text.insert(tk.END, f"📚 {source['original_source']}\n", "normal")
                        
                        # ✨ Date/Year
                        if 'date' in source:
                            text.insert(tk.END, f"📅 {source['date']}", "normal")
                        elif 'year' in source:
                            text.insert(tk.END, f"📅 {source['year']}", "normal")
                        
                        # ✨ Scores (5 Metriken)
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
                        if 'score' in source:
                            scores.append(f"Best: {source['score']:.2%}")
                        
                        if scores:
                            text.insert(tk.END, "\n📊 " + " | ".join(scores), "scores")
                        
                        # ✨ Impact & Relevance
                        classification = []
                        if 'impact' in source:
                            classification.append(f"💎 Impact: {source['impact']}")
                        if 'relevance' in source:
                            classification.append(f"🎯 Relevance: {source['relevance']}")
                        
                        if classification:
                            text.insert(tk.END, "\n" + " | ".join(classification), "classification")
                        
                        # ✨ Legal Metadata
                        legal = []
                        if 'rechtsgebiet' in source:
                            legal.append(f"⚖️ Rechtsgebiet: {source['rechtsgebiet']}")
                        if 'behoerde' in source:
                            legal.append(f"🏛️ Behörde: {source['behoerde']}")
                        
                        if legal:
                            text.insert(tk.END, "\n" + " | ".join(legal), "legal")
                        
                        # Additional Details (Page, DOI, etc.)
                        details = []
                        if 'page' in source:
                            details.append(f"📄 Seite: {source['page']}")
                        if 'section' in source:
                            details.append(f"📑 Abschnitt: {source['section']}")
                        if 'doi' in source:
                            details.append(f"🔗 DOI: {source['doi']}")
                        if 'url' in source:
                            url = source['url']
                            if len(url) > 60:
                                url = url[:57] + '...'
                            details.append(f"🌐 URL: {url}")
                        elif 'file' in source:
                            details.append(f"📁 Datei: {source['file']}")
                        
                        if details:
                            text.insert(tk.END, "\n" + " | ".join(details), "details")
                        
                        # ✨ Ingestion Date
                        if 'ingestion_date' in source:
                            text.insert(tk.END, f"\n📥 Ingested: {source['ingestion_date']}", "ingestion")
                        
                        text.insert(tk.END, "\n\n")
            
            # Configure tags
            text.tag_config("bold", font=("Segoe UI", 10, "bold"))
            text.tag_config("ieee", font=("Segoe UI", 10), foreground="#1976D2")
            text.tag_config("title", font=("Segoe UI", 11, "bold"), foreground="#1976D2")
            text.tag_config("authors", font=("Segoe UI", 10, "italic"), foreground="#424242")
            text.tag_config("normal", font=("Segoe UI", 9), foreground="#616161")
            text.tag_config("scores", font=("Segoe UI", 9), foreground="#4CAF50")
            text.tag_config("classification", font=("Segoe UI", 9, "bold"), foreground="#FF9800")
            text.tag_config("legal", font=("Segoe UI", 9), foreground="#9C27B0")
            text.tag_config("details", font=("Segoe UI", 9), foreground="#757575")
            text.tag_config("ingestion", font=("Segoe UI", 8, "italic"), foreground="#9E9E9E")
            
            text.config(state=tk.DISABLED)
            
            logger.debug(f"📚 Quellen-Fenster geöffnet: {len(self.sources)} Quellen")
            
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen der Quellen: {e}")
            messagebox.showerror("Fehler", f"Quellen-Anzeige fehlgeschlagen:\n{e}")
    
    def _show_suggestions(self):
        """Show suggestions in popup window"""
        try:
            if self.suggestions_window and self.suggestions_window.winfo_exists():
                self.suggestions_window.lift()
                return
            
            # ✨ v3.18.0: Use root_window for Toplevel
            self.suggestions_window = tk.Toplevel(self.root_window)
            self.suggestions_window.title(f"💡 Vorschläge ({len(self.suggestions)})")
            self.suggestions_window.geometry("500x400")
            
            # Text widget
            text = tk.Text(
                self.suggestions_window,
                wrap=tk.WORD,
                font=("Segoe UI", 10),
                bg="#FAFAFA",
                fg="#212121"
            )
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Format suggestions
            if not self.suggestions:
                text.insert("1.0", "Keine Vorschläge verfügbar.")
            else:
                for i, suggestion in enumerate(self.suggestions, 1):
                    text.insert(tk.END, f"{i}. {suggestion}\n\n")
            
            text.config(state=tk.DISABLED)
            
            logger.debug(f"💡 Vorschläge-Fenster geöffnet: {len(self.suggestions)} Vorschläge")
            
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen der Vorschläge: {e}")
            messagebox.showerror("Fehler", f"Vorschläge-Anzeige fehlgeschlagen:\n{e}")
    
    def _show_raw(self):
        """Show raw response in dialog"""
        try:
            if self.on_show_raw:
                raw_text = self.raw_response or self.content
                self.on_show_raw(raw_text)
            else:
                # Fallback: Show in popup
                # ✨ v3.18.0: Use root_window for Toplevel
                raw_window = tk.Toplevel(self.root_window)
                raw_window.title("🔍 Raw Response")
                raw_window.geometry("700x600")
                
                text = tk.Text(
                    raw_window,
                    wrap=tk.WORD,
                    font=("Consolas", 10),
                    bg="#263238",
                    fg="#ECEFF1"
                )
                text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                raw_text = self.raw_response or self.content
                text.insert("1.0", raw_text)
                text.config(state=tk.DISABLED)
            
            logger.debug(f"🔍 Raw-Response-Fenster geöffnet")
            
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen der Raw-Response: {e}")
            messagebox.showerror("Fehler", f"Raw-Response-Anzeige fehlgeschlagen:\n{e}")


def create_answer_toolbar(
    parent: tk.Text,
    message_data: Dict[str, Any],
    on_feedback: Optional[Callable[[str, str], None]] = None,
    on_copy: Optional[Callable[[str], None]] = None,
    on_repeat: Optional[Callable[[str], None]] = None,
    on_show_raw: Optional[Callable[[str], None]] = None
) -> AnswerToolbar:
    """
    Factory function to create an AnswerToolbar.
    
    Args:
        parent: Parent Text widget
        message_data: Message data dict
        on_feedback: Callback(message_id, feedback_type)
        on_copy: Callback(text)
        on_repeat: Callback(query)
        on_show_raw: Callback(raw_response)
    
    Returns:
        Configured AnswerToolbar instance
    
    Example:
        >>> toolbar = create_answer_toolbar(
        ...     parent=chat_text,
        ...     message_data=message,
        ...     on_feedback=self.handle_feedback,
        ...     on_copy=self.handle_copy,
        ...     on_repeat=self.handle_repeat
        ... )
        >>> toolbar.render()
    """
    return AnswerToolbar(
        parent=parent,
        message_data=message_data,
        on_feedback=on_feedback,
        on_copy=on_copy,
        on_repeat=on_repeat,
        on_show_raw=on_show_raw
    )
