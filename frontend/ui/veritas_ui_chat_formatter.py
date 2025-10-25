#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS UI Module: Chat Display Formatter
Verantwortlich für formatierte Chat-Darstellung mit RAG-Sections
"""

import tkinter as tk
import re
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import logging
import os
import platform

# ✨ Logger initialisieren (MUSS VOR allen Imports kommen!)
logger = logging.getLogger(__name__)

# ✨ Zentrale Konfiguration
try:
    from frontend.config.frontend_config import BACKEND_URL
except ImportError:
    BACKEND_URL = "http://localhost:5000/api/v3"  # API v3 Base URL

# ✨ NEW v3.16.0: Feedback API Client
try:
    from frontend.services.feedback_api_client import FeedbackAPIClientSync
    FEEDBACK_API_AVAILABLE = True
except ImportError:
    FEEDBACK_API_AVAILABLE = False
    logger.warning("⚠️ Feedback API Client nicht verfügbar")

# ✨ Icon-System importieren
try:
    from .veritas_ui_icons import VeritasIcons, get_source_icon, format_with_icon
    ICONS_AVAILABLE = True
except ImportError:
    ICONS_AVAILABLE = False
    # Fallback: Keine Icons
    class VeritasIcons:
        @staticmethod
        def get(cat, name, fallback='•'):
            return fallback

# ✨ v3.16.0: Modern Chat Bubbles & IEEE Citations
try:
    from .veritas_ui_chat_bubbles import (
        UserMessageBubble,
        AssistantFullWidthLayout,
        MetadataCompactWrapper,
        TkinterBestPractices
    )
    CHAT_BUBBLES_AVAILABLE = True
    logger.info("✅ Modern Chat Bubbles & Best Practices geladen")
except ImportError:
    CHAT_BUBBLES_AVAILABLE = False
    logger.warning("⚠️ Modern Chat Bubbles nicht verfügbar - verwende Legacy-Darstellung")

# ✨ Feature #1: Collapsible Sections importieren
try:
    from .veritas_ui_components import CollapsibleSection
    COLLAPSIBLE_AVAILABLE = True
except ImportError:
    COLLAPSIBLE_AVAILABLE = False
    logger.warning("⚠️ CollapsibleSection nicht verfügbar - Fallback auf alte Darstellung")


# ✨ Feature #14: Relative Timestamp-Formatierung
def format_relative_timestamp(timestamp_str: str) -> tuple[str, str]:
    """
    Formatiert Timestamp relativ zu jetzt (Feature #14)
    
    Args:
        timestamp_str: ISO-Format Timestamp (z.B. "2025-10-09T14:23:45.123456")
    
    Returns:
        Tuple (short_display, full_tooltip)
        - short_display: "Heute 14:23", "Gestern 10:15", "Mo 09:30"
        - full_tooltip: "Montag, 9. Oktober 2025, 14:23:45"
    """
    try:
        # Parse Timestamp (unterstützt ISO-Format mit/ohne Mikrosekunden)
        if '.' in timestamp_str:
            # Format mit Mikrosekunden: "2025-10-09T14:23:45.123456"
            dt = datetime.fromisoformat(timestamp_str)
        else:
            # Format ohne Mikrosekunden: "2025-10-09T14:23:45"
            dt = datetime.fromisoformat(timestamp_str)
        
        now = datetime.now()
        diff = now - dt
        
        # Zeitformat für Uhrzeit
        time_str = dt.strftime("%H:%M")
        
        # Relative Tage
        if diff.days == 0 and dt.date() == now.date():
            # Heute
            short = f"Heute {time_str}"
        elif diff.days == 1 or (diff.days == 0 and dt.date() < now.date()):
            # Gestern
            short = f"Gestern {time_str}"
        elif diff.days < 7:
            # Diese Woche: Wochentag
            weekday_names = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
            weekday = weekday_names[dt.weekday()]
            short = f"{weekday} {time_str}"
        else:
            # Älter: Datum
            short = dt.strftime("%d.%m. %H:%M")
        
        # Full Tooltip
        weekday_full_names = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
        month_names = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 
                      'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
        
        weekday_full = weekday_full_names[dt.weekday()]
        month_full = month_names[dt.month - 1]
        full = f"{weekday_full}, {dt.day}. {month_full} {dt.year}, {dt.strftime('%H:%M:%S')}"
        
        return (short, full)
        
    except Exception as e:
        logger.debug(f"Fehler beim Timestamp-Parsing: {e}")
        # Fallback: Original-String
        return (timestamp_str, timestamp_str)


def get_date_group_label(timestamp_str: str) -> str:
    """
    Bestimmt die Datums-Gruppe für Message Grouping (Feature #6)
    
    Args:
        timestamp_str: ISO-Format Timestamp
    
    Returns:
        Label für Datums-Trenner: "Heute", "Gestern", "Diese Woche", "Letzte Woche", 
        oder formatiertes Datum (z.B. "15. Oktober 2025")
    """
    try:
        # Parse Timestamp
        if '.' in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str)
        else:
            dt = datetime.fromisoformat(timestamp_str)
        
        now = datetime.now()
        diff = now - dt
        
        # Datums-Gruppe bestimmen
        if diff.days == 0 and dt.date() == now.date():
            return "Heute"
        elif diff.days == 1 or (diff.days == 0 and dt.date() < now.date()):
            return "Gestern"
        elif diff.days < 7:
            return "Diese Woche"
        elif diff.days < 14:
            return "Letzte Woche"
        elif diff.days < 30:
            return "Letzter Monat"
        else:
            # Älter: Formatiertes Datum
            month_names = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 
                          'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
            month = month_names[dt.month - 1]
            return f"{dt.day}. {month} {dt.year}"
        
    except Exception as e:
        logger.debug(f"Fehler beim Date-Group-Parsing: {e}")
        return None


class ChatDisplayFormatter:
    """
    Formatiert Chat-Nachrichten mit RAG-spezifischen Sections
    Unterstützt: Metadaten, Quellen, Agents, Vorschläge, Collapsible Details
    """
    
    def __init__(
        self, 
        text_widget: tk.Text,
        parent_window: tk.Tk = None,
        markdown_renderer = None,
        source_link_handler = None,
        backend_url: str = None,
        suggestion_click_callback = None,  # ✨ v3.19.0: Callback für klickbare Vorschläge
        enable_modern_ui: bool = True  # ✨ v3.16.0: Modern Chat Bubbles aktivieren
    ):
        """
        Initialisiert den Chat Display Formatter
        
        Args:
            text_widget: Tkinter Text Widget
            parent_window: Hauptfenster für Animations
            markdown_renderer: MarkdownRenderer-Instanz (optional)
            source_link_handler: SourceLinkHandler-Instanz (optional)
            backend_url: Backend-URL für API-Calls (default: aus Config)
            suggestion_click_callback: ✨ v3.19.0 - Callback(suggestion_text) für klickbare Vorschläge
            enable_modern_ui: ✨ v3.16.0 - Aktiviere moderne Chat-Bubbles & IEEE-Citations
        """
        self.text_widget = text_widget
        self.parent_window = parent_window
        self.markdown_renderer = markdown_renderer
        self.source_link_handler = source_link_handler
        self.suggestion_click_callback = suggestion_click_callback  # ✨ v3.19.0
        self.enable_modern_ui = enable_modern_ui and CHAT_BUBBLES_AVAILABLE  # ✨ v3.16.0
        
        # ✨ Feature #1: Message-ID Counter für eindeutige Section-IDs
        self._message_counter = 0
        
        # ✨ v3.16.0: Modern UI Components initialisieren
        self._init_modern_ui_components()
        
        # ✨ NEW v3.16.0: Feedback State Management & API Client
        self._feedback_states = {}  # {message_id: {'rating': int, 'submitted': bool}}
        
        # ✨ v3.18.0: Answer Toolbar aktivieren
        self._answer_toolbar_enabled = True
        
        # Backend URL (aus Parameter oder Config)
        self._backend_url = backend_url or BACKEND_URL
        
        if FEEDBACK_API_AVAILABLE:
            self.feedback_api = FeedbackAPIClientSync(base_url=self._backend_url)
            logger.info(f"✅ Feedback API Client initialisiert: {self._backend_url}")
        else:
            self.feedback_api = None
    
    def _init_modern_ui_components(self):
        """
        ✨ v3.16.0: Initialisiert moderne UI-Komponenten
        
        Features:
        - MetadataCompactWrapper (für IEEE-Quellenverzeichnis)
        - AssistantFullWidthLayout (für vollbreite Assistant-Antworten)
        - Tkinter Best Practices (Smooth Scrolling, Performance)
        """
        if not self.enable_modern_ui:
            logger.info("Modern UI deaktiviert - verwende Legacy-Darstellung")
            self.metadata_handler = None
            self.assistant_layout = None
            return
        
        try:
            # Metadata-Handler (kompakte Metadaten-Zeile)
            self.metadata_handler = MetadataCompactWrapper(
                text_widget=self.text_widget,
                feedback_callback=self._on_feedback_received,
                initially_collapsed=True  # Default: zugeklappt
            )
            
            # Assistant-Layout-Handler (vollbreite mit IEEE-Citations)
            self.assistant_layout = AssistantFullWidthLayout(
                text_widget=self.text_widget,
                markdown_renderer=self.markdown_renderer,
                metadata_handler=self.metadata_handler,
                enable_ieee_citations=True  # ✨ IEEE-Citations aktiviert
            )
            
            # Best-Practice Optimierungen anwenden
            TkinterBestPractices.optimize_text_widget(self.text_widget)
            TkinterBestPractices.enable_smooth_scrolling(self.text_widget)
            
            logger.info("✅ Modern UI Components initialisiert (Bubbles, IEEE-Citations, Best-Practices)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Initialisieren Modern UI: {e}")
            self.enable_modern_ui = False
            self.metadata_handler = None
            self.assistant_layout = None
    
    def _on_feedback_received(self, rating: str):
        """
        ✨ v3.16.0: Behandelt Feedback von Modern UI Components
        
        Args:
            rating: 'positive' (👍) oder 'negative' (👎)
        """
        logger.info(f"✅ User-Feedback erhalten: {rating}")
        
        # TODO: An Backend senden
        # POST /feedback mit {message_id, rating, timestamp}
        
        # Visuelles Feedback (optional)
        if hasattr(self, 'parent_window'):
            # Kurz "Danke!" anzeigen (könnte auch Statusbar sein)
            pass
            logger.warning("⚠️ Feedback API nicht verfügbar - Fallback zu lokalem State")
    
    def update_chat_display(self, chat_messages: List[Dict]) -> None:
        """
        Aktualisiert vollständige Chat-Anzeige
        
        Args:
            chat_messages: Liste von Chat-Nachrichten
        """
        logger.info(f"🖼️ update_chat_display: {len(chat_messages)} Messages")
        
        if not self.parent_window or not hasattr(self.parent_window, 'winfo_exists') or not self.parent_window.winfo_exists():
            logger.warning(f"⚠️ Window existiert nicht")
            return
        
        self.text_widget.config(state='normal')
        self.text_widget.delete('1.0', tk.END)
        
        # ✨ Feature #1: Reset Message Counter
        self._message_counter = 0
        
        # ✨ Feature #6: Message Grouping - Track last date group
        last_date_group = None
        
        for idx, msg in enumerate(chat_messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            tag = msg.get('tag', role)
            
            # ✨ Feature #14: Formatiere Timestamp relativ
            if timestamp:
                timestamp_short, timestamp_full = format_relative_timestamp(timestamp)
            else:
                timestamp_short, timestamp_full = ('', '')
            
            # ✨ Feature #6: Datums-Trenner einfügen wenn sich Gruppe ändert
            if timestamp:
                current_date_group = get_date_group_label(timestamp)
                if current_date_group and current_date_group != last_date_group:
                    self._render_date_separator(current_date_group)
                    last_date_group = current_date_group
            
            logger.debug(f"  Message {idx+1}/{len(chat_messages)}: role={role}, len={len(content)}")
            
            # === SYSTEM MESSAGE ===
            if role == 'system':
                if timestamp_short:
                    self.text_widget.insert(tk.END, f"[{timestamp_short}] ", "timestamp")
                self.text_widget.insert(tk.END, f"{content}\n\n", "system")
            
            # === USER MESSAGE ===
            elif role == 'user':
                # ✨ NEW: Sprechblasen-Design für User-Messages
                attachments = msg.get('attachments', [])
                self._render_user_message(
                    content=content,
                    timestamp_short=timestamp_short,
                    timestamp_full=timestamp_full,
                    attachments=attachments
                )
            
            # === ASSISTANT MESSAGE ===
            elif role == 'assistant':
                # ✨ NEW: Strukturiertes Rendering
                self._message_counter += 1
                msg_id = f"msg_{self._message_counter}"
                
                # Hole Metadaten aus Message (falls vorhanden)
                metadata = msg.get('metadata', None)
                
                # Strukturierte Darstellung
                self._render_assistant_message_structured(
                    content=content,
                    timestamp_short=timestamp_short,
                    timestamp_full=timestamp_full,
                    metadata=metadata,
                    message_id=msg_id
                )
            
            # === ERROR MESSAGE ===
            elif role == 'error':
                if timestamp_short:
                    self.text_widget.insert(tk.END, f"[{timestamp_short}] ", "timestamp")
                self.text_widget.insert(tk.END, "Fehler:\n", "system")
                self.text_widget.insert(tk.END, f"{content}\n\n", "system")
        
        self.text_widget.config(state='disabled')
        self.text_widget.see(tk.END)
        logger.info(f"✅ Chat-Display aktualisiert")
    
    def _render_date_separator(self, date_label: str) -> None:
        """
        ✨ Feature #6: Rendert einen Datums-Trenner zwischen Message-Gruppen
        
        Args:
            date_label: Label für den Trenner (z.B. "Heute", "Gestern", "Diese Woche")
        """
        try:
            # Abstand vor Trenner
            self.text_widget.insert(tk.END, "\n")
            
            # Zentrierter Trenner mit Linie und Label
            # Format: ━━━━━ Heute ━━━━━
            separator_width = 60  # Gesamtbreite in Zeichen
            label_with_spaces = f" {date_label} "
            label_len = len(label_with_spaces)
            line_len = (separator_width - label_len) // 2
            
            # Linke Linie
            left_line = "─" * line_len
            # Rechte Linie (eventuell +1 wenn ungerade)
            right_line = "─" * (separator_width - label_len - line_len)
            
            separator_text = f"{left_line}{label_with_spaces}{right_line}"
            
            # Separator einfügen mit speziellem Tag
            start_pos = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, separator_text, "date_separator")
            end_pos = self.text_widget.index(tk.END)
            
            # Tag konfigurieren (falls noch nicht geschehen)
            try:
                self.text_widget.tag_configure(
                    "date_separator",
                    foreground="#9E9E9E",  # Grau
                    font=("Segoe UI", 9, "bold"),
                    justify=tk.CENTER,
                    spacing1=10,  # Abstand oben
                    spacing3=10   # Abstand unten
                )
            except:
                pass  # Tag bereits konfiguriert
            
            # Newline nach Separator
            self.text_widget.insert(tk.END, "\n\n")
            
            logger.debug(f"📅 Datums-Trenner eingefügt: {date_label}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Rendern des Datums-Trenners: {e}")
    
    def _render_user_message(
        self, 
        content: str, 
        timestamp_short: str = '', 
        timestamp_full: str = '',
        attachments: List[Dict] = None
    ) -> None:
        """
        ✨ v3.16.0: Rendert User-Message als moderne rechtsbündige Bubble
        
        Args:
            content: Nachrichtentext
            timestamp_short: Kurzer Timestamp (z.B. "Heute 14:23")
            timestamp_full: Voller Timestamp für Tooltip
            attachments: Liste von Datei-Anhängen [{'name': 'file.pdf', 'size': 1234567, 'path': '...'}]
        """
        
        # ✨ v3.16.0: Modern UI mit Bubbles
        if self.enable_modern_ui and CHAT_BUBBLES_AVAILABLE:
            try:
                # Verwende UserMessageBubble für moderne Darstellung
                bubble = UserMessageBubble(
                    text_widget=self.text_widget,
                    message=content,
                    timestamp=timestamp_full if timestamp_full else None,
                    max_width_percent=0.7  # 70% Breite
                )
                bubble.render()
                
                # Anhänge separat anzeigen (falls vorhanden)
                if attachments and len(attachments) > 0:
                    for attachment in attachments:
                        name = attachment.get('name', 'unbekannt')
                        size = attachment.get('size', 0)
                        
                        # Formatiere Größe
                        if size > 1024 * 1024:
                            size_str = f"{size / (1024 * 1024):.1f} MB"
                        elif size > 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        else:
                            size_str = f"{size} B"
                        
                        self.text_widget.insert(tk.END, f"  📎 {name} ({size_str})\n", "user_attachment")
                
                logger.debug(f"✅ User-Bubble gerendert (attachments={len(attachments) if attachments else 0})")
                return
                
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Rendern User-Bubble: {e} - Fallback auf Legacy")
                # Fallback unten
        
        # === LEGACY FALLBACK ===
        # Metadata-Zeile (oberhalb Bubble)
        metadata_parts = []
        
        # Datei-Anhänge
        if attachments and len(attachments) > 0:
            for attachment in attachments:
                name = attachment.get('name', 'unbekannt')
                size = attachment.get('size', 0)
                
                # Formatiere Größe (Bytes → KB/MB)
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                elif size > 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size} B"
                
                metadata_parts.append(f"📎 {name} ({size_str})")
        
        # Timestamp
        if timestamp_short:
            metadata_parts.append(f"🕐 {timestamp_short}")
        
        # Metadata-Zeile einfügen (wenn vorhanden)
        if metadata_parts:
            metadata_text = "  |  ".join(metadata_parts)
            self.text_widget.insert(tk.END, metadata_text + "\n", "user_metadata")
        
        # === USER-BUBBLE (rechtsbündig mit Hintergrund) ===
        bubble_start = self.text_widget.index(tk.END)
        self.text_widget.insert(tk.END, content, "user_bubble")
        bubble_end = self.text_widget.index(tk.END)
        
        # Unique Tag für diese Message (für Hover-Effekte, falls gewünscht)
        self._message_counter += 1
        bubble_tag = f"user_msg_{self._message_counter}"
        self.text_widget.tag_add(bubble_tag, bubble_start, bubble_end)
        
        # Separator nach Message
        self.text_widget.insert(tk.END, "\n\n", "message_separator")
        
        logger.debug(f"✅ User-Message (Legacy) gerendert (attachments={len(attachments) if attachments else 0})")
    
    def _insert_attachment_list(self, attachments: List[Dict]) -> None:
        """
        ✨ NEW: Fügt klickbare Datei-Anhänge ein
        
        Args:
            attachments: Liste von {'name': str, 'size': int, 'path': str}
        """
        if not attachments:
            return
        
        for i, attachment in enumerate(attachments):
            name = attachment.get('name', 'unbekannt')
            size = attachment.get('size', 0)
            path = attachment.get('path', '')
            
            # Formatiere Größe
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            
            # Icon + Name (klickbar)
            link_start = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, f"📎 {name}", "attachment_link")
            link_end = self.text_widget.index(tk.END)
            
            # Größe (nicht klickbar)
            self.text_widget.insert(tk.END, f" ({size_str})", "user_metadata")
            
            # Separator
            if i < len(attachments) - 1:
                self.text_widget.insert(tk.END, "  |  ", "user_metadata")
            
            # Click-Handler: Öffne Datei
            if path:
                attachment_tag = f"attachment_{self._message_counter}_{i}"
                self.text_widget.tag_add(attachment_tag, link_start, link_end)
                
                def create_open_handler(file_path):
                    def handler(event):
                        try:
                            import os
                            import platform
                            
                            if platform.system() == 'Windows':
                                os.startfile(file_path)
                            elif platform.system() == 'Darwin':  # macOS
                                os.system(f'open "{file_path}"')
                            else:  # Linux
                                os.system(f'xdg-open "{file_path}"')
                            
                            logger.info(f"📂 Datei geöffnet: {file_path}")
                        except Exception as e:
                            logger.error(f"❌ Fehler beim Öffnen: {e}")
                    return handler
                
                self.text_widget.tag_bind(attachment_tag, "<Button-1>", create_open_handler(path))
                
                # Cursor-Effekt
                self.text_widget.tag_bind(attachment_tag, "<Enter>", lambda e: self.text_widget.config(cursor="hand2"))
                self.text_widget.tag_bind(attachment_tag, "<Leave>", lambda e: self.text_widget.config(cursor=""))
    
    def _render_assistant_message_structured(
        self,
        content: str,
        timestamp_short: str = '',
        timestamp_full: str = '',
        metadata: Dict = None,
        message_id: str = None
    ) -> None:
        """
        ✨ v3.16.0: Rendert Assistant-Message mit modernem Layout
        
        Modern Layout (v3.16.0):
        - Vollbreite Markdown-Rendering (keine Bubble)
        - IEEE-Citations im Text [1], [2], [3]
        - Kompakte Metadaten-Zeile (collapsible)
        - IEEE-Quellenverzeichnis in Metadaten
        
        Legacy Layout (Fallback):
        - Strukturiertes Layout mit Sections
        - Metriken-Badge
        - Feedback-Widget
        - Collapsible Sections
        
        Args:
            content: Antwort-Content (mit {cite:source_id} Markern für IEEE)
            timestamp_short: Kurzer Timestamp
            timestamp_full: Voller Timestamp
            metadata: Metadaten {complexity, duration, model, sources_metadata, suggestions, ...}
            message_id: Message-ID für Sections
        """
        
        # 🔍 DEBUG: Prüfe Modern UI Status (INFO-Level für bessere Sichtbarkeit)
        logger.info(f"🔍 _format_assistant_message() aufgerufen")
        logger.info(f"  - enable_modern_ui: {self.enable_modern_ui}")
        logger.info(f"  - assistant_layout: {self.assistant_layout}")
        logger.info(f"  - Bedingung erfüllt: {self.enable_modern_ui and self.assistant_layout}")
        
        # ✨ v3.16.0: Modern UI mit IEEE-Citations
        if self.enable_modern_ui and self.assistant_layout:
            # 🔍 DEBUG: Kein Fallback - Hard Fail für besseres Debugging
            logger.info(f"✅ Modern UI Pfad wird verwendet!")
            
            # Header (Timestamp + Icon)
            if timestamp_short:
                self.text_widget.insert(tk.END, f"[{timestamp_short}] ", "timestamp")
            self.text_widget.insert(tk.END, "🤖 VERITAS:\n", "assistant")
            
            # Extrahiere Sources für IEEE-Formatierung
            sources = metadata.get('sources_metadata', []) if metadata else []
            
            # 🔍 CRITICAL DEBUG: Was ist wirklich in sources_metadata?
            logger.info(f"🔍 RAW metadata['sources_metadata']: {metadata.get('sources_metadata', 'NOT FOUND')[:500] if metadata else 'NO METADATA'}")
            
            logger.info(f"🔍 DEBUG - Rendering Modern Layout:")
            logger.info(f"  - content type: {type(content)}, length: {len(content) if content else 'None'}")
            logger.info(f"  - content preview: {content[:200] if content else 'None'}")
            logger.info(f"  - metadata type: {type(metadata)}")
            logger.info(f"  - metadata keys: {list(metadata.keys()) if metadata else 'None'}")
            logger.info(f"  - sources count: {len(sources)}")
            if sources:
                logger.info(f"  - first source keys: {list(sources[0].keys())}")
                logger.info(f"  - first source title: {sources[0].get('title', 'NO TITLE')}")
                logger.info(f"  - Has 'ieee_citation'?: {'ieee_citation' in sources[0]}")
                logger.info(f"  - Has 'authors'?: {'authors' in sources[0]}")
                logger.info(f"  - Has 'impact'?: {'impact' in sources[0]}")
            logger.info(f"  - enable_citations: True")
            logger.info(f"  - enable_modern_ui: {self.enable_modern_ui}")
            logger.info(f"  - assistant_layout exists: {self.assistant_layout is not None}")
            
            # Verwende AssistantFullWidthLayout für modernen Render
            self.assistant_layout.render_assistant_message(
                content=content,
                metadata=metadata,
                sources=sources,
                enable_citations=True  # IEEE-Citations aktiviert
            )
            
            # ✨ v3.18.0: Answer Toolbar unter Antwort einfügen
            self._insert_answer_toolbar(content, metadata, message_id)
            
            logger.debug(f"✅ Modern Assistant-Message gerendert (IEEE-Citations, {len(sources)} Sources)")
            return
        
        # === LEGACY FALLBACK ===
        # Header (Timestamp + VERITAS)
        if timestamp_short:
            self.text_widget.insert(tk.END, f"[{timestamp_short}] ", "timestamp")
        self.text_widget.insert(tk.END, "🤖 VERITAS:\n", "assistant")
        
        # Parse Content in Sections (wenn Markdown-Renderer verfügbar)
        if self.markdown_renderer:
            sections = self.markdown_renderer.parse_rag_response(content)
        else:
            sections = {'main_answer': content}
        
        # === 1) HAUPTANTWORT ===
        if sections.get('main_answer'):
            # Rendere mit Markdown
            if self.markdown_renderer:
                self.markdown_renderer.render_markdown(sections['main_answer'], "assistant_bubble")
            else:
                self.text_widget.insert(tk.END, sections['main_answer'], "assistant_bubble")
            
            self.text_widget.insert(tk.END, "\n")
        
        # === 2) METRIKEN-BADGE (kompakt) ===
        if metadata:
            self._insert_metrics_compact(metadata)
        elif sections.get('metadata'):
            self._insert_metrics_compact(sections['metadata'])
        
        # === 3) FEEDBACK-WIDGET ===
        if message_id:
            self._insert_feedback_widget(message_id)
        
        # === 4) QUELLEN (Collapsible) ===
        # ✨ v3.19.0: Prüfe auf sources_metadata (IEEE-Format) in metadata
        sources_metadata = metadata.get('sources_metadata', []) if metadata else []
        
        if COLLAPSIBLE_AVAILABLE and message_id and sources_metadata:
            # ✨ NEW: IEEE-konforme Quellen mit Metadaten
            self._insert_sources_collapsible(sources_metadata, message_id, use_ieee_format=True)
        elif COLLAPSIBLE_AVAILABLE and message_id and sections.get('sources'):
            # Legacy: Quellen aus Content-Parsing
            self._insert_sources_collapsible(sections['sources'], message_id, use_ieee_format=False)
        elif sections.get('sources'):
            # Fallback: Normale Darstellung
            self._insert_sources(sections['sources'])
        
        # === 5) AGENTS (Collapsible) ===
        if COLLAPSIBLE_AVAILABLE and message_id and sections.get('agents'):
            self._insert_agents_collapsible(sections['agents'], message_id)
        elif sections.get('agents'):
            # Fallback: Normale Darstellung
            self._insert_agents(sections['agents'])
        
        # === 6) VORSCHLÄGE (Collapsible) ===
        # ✨ v3.19.0: Prüfe auf suggestions in metadata (vom Backend)
        suggestions = metadata.get('suggestions', []) if metadata else []
        
        if COLLAPSIBLE_AVAILABLE and message_id and suggestions:
            # ✨ NEW: Vorschläge aus Backend-Response (klickbare Links)
            self._insert_suggestions_collapsible(suggestions, message_id)
        elif COLLAPSIBLE_AVAILABLE and message_id and sections.get('suggestions'):
            # Legacy: Vorschläge aus Content-Parsing
            self._insert_suggestions_collapsible(sections['suggestions'], message_id)
        elif sections.get('suggestions'):
            # Fallback: Normale Darstellung
            self._insert_suggestions(sections['suggestions'])
        
        # === 7) RAW RESPONSE (Collapsible, DEBUG) ===
        if COLLAPSIBLE_AVAILABLE and message_id and metadata:
            self._insert_raw_response_collapsible(content, metadata, message_id)
        
        # Separator nach Message
        self.text_widget.insert(tk.END, "\n", "message_separator")
        
        logger.debug(f"✅ Strukturierte Assistant-Message (Legacy) gerendert (msg_id={message_id})")
    
    def insert_processing_placeholder(self, message_id: str) -> None:
        """
        ✨ NEW: Fügt animierten Platzhalter während Query-Verarbeitung ein
        
        Args:
            message_id: Eindeutige Message-ID für späteren Ersatz
        """
        # Timestamp-Zeile
        timestamp_short, _ = format_relative_timestamp(datetime.now().isoformat())
        self.text_widget.config(state='normal')
        self.text_widget.insert(tk.END, f"[{timestamp_short}] ", "timestamp")
        self.text_widget.insert(tk.END, "🤖 VERITAS:\n", "assistant")
        
        # Platzhalter mit Marks für späteren Ersatz
        placeholder_start_mark = f"placeholder_start_{message_id}"
        placeholder_end_mark = f"placeholder_end_{message_id}"
        
        # Start-Mark setzen
        self.text_widget.mark_set(placeholder_start_mark, tk.END)
        self.text_widget.mark_gravity(placeholder_start_mark, tk.LEFT)  # Bleibt links von eingefügtem Text
        
        # Platzhalter-Text
        self.text_widget.insert(tk.END, "⏳ Verarbeite Anfrage", "processing_placeholder")
        self.text_widget.insert(tk.END, "...", f"processing_dots_{message_id}")
        self.text_widget.insert(tk.END, "\n\n", "message_separator")
        
        # End-Mark setzen
        self.text_widget.mark_set(placeholder_end_mark, tk.END)
        self.text_widget.mark_gravity(placeholder_end_mark, tk.RIGHT)  # Bleibt rechts von eingefügtem Text
        
        self.text_widget.config(state='disabled')
        self.text_widget.see(tk.END)
        
        # Starte Pulsier-Animation
        self._start_placeholder_animation(message_id)
        
        logger.debug(f"✅ Platzhalter eingefügt für {message_id}")
    
    def _start_placeholder_animation(self, message_id: str) -> None:
        """
        Startet pulsierende Animation für Platzhalter-Punkte
        
        Args:
            message_id: Message-ID des Platzhalters
        """
        dots_tag = f"processing_dots_{message_id}"
        animation_states = [".", "..", "..."]
        current_state = [0]  # Mutable für Closure
        animation_active = [True]  # Flag für Stopp
        
        # Speichere Animation-Flag für späteren Stopp
        if not hasattr(self, '_placeholder_animations'):
            self._placeholder_animations = {}
        self._placeholder_animations[message_id] = animation_active
        
        def animate():
            if not animation_active[0]:
                return  # Animation wurde gestoppt
            
            # Finde alle Text-Bereiche mit diesem Tag
            try:
                ranges = self.text_widget.tag_ranges(dots_tag)
                if not ranges or len(ranges) < 2:
                    return  # Tag nicht mehr vorhanden
                
                # Aktualisiere Text
                self.text_widget.config(state='normal')
                self.text_widget.delete(ranges[0], ranges[1])
                self.text_widget.insert(ranges[0], animation_states[current_state[0]], dots_tag)
                self.text_widget.config(state='disabled')
                
                # Nächster State
                current_state[0] = (current_state[0] + 1) % len(animation_states)
                
                # Nächster Frame (500ms)
                if self.parent_window and hasattr(self.parent_window, 'after'):
                    self.parent_window.after(500, animate)
                    
            except tk.TclError:
                # Widget wurde zerstört
                animation_active[0] = False
        
        # Starte Animation
        if self.parent_window and hasattr(self.parent_window, 'after'):
            self.parent_window.after(500, animate)
    
    def replace_placeholder_with_response(
        self, 
        message_id: str, 
        content: str, 
        metadata: Dict = None
    ) -> None:
        """
        ✨ NEW: Ersetzt Platzhalter durch echte Antwort
        
        Args:
            message_id: Message-ID des Platzhalters
            content: Antwort-Content
            metadata: Metadaten (confidence, sources, etc.)
        """
        placeholder_start_mark = f"placeholder_start_{message_id}"
        placeholder_end_mark = f"placeholder_end_{message_id}"
        
        # Stoppe Animation
        if hasattr(self, '_placeholder_animations') and message_id in self._placeholder_animations:
            self._placeholder_animations[message_id][0] = False  # Stopp-Flag setzen
        
        try:
            # Finde Marks
            start_index = self.text_widget.index(placeholder_start_mark)
            end_index = self.text_widget.index(placeholder_end_mark)
            
            # Lösche Platzhalter
            self.text_widget.config(state='normal')
            self.text_widget.delete(start_index, end_index)
            
            # ✨ Füge strukturierte Antwort ein (STATT insert_formatted_content)
            self.text_widget.mark_set(tk.INSERT, start_index)  # Cursor an Start-Position
            
            # Parse Content in Sections
            if self.markdown_renderer:
                sections = self.markdown_renderer.parse_rag_response(content)
            else:
                sections = {'main_answer': content}
            
            # Rendere strukturiert (OHNE Timestamp + Header - bereits vorhanden)
            # === HAUPTANTWORT ===
            if sections.get('main_answer'):
                if self.markdown_renderer:
                    self.markdown_renderer.render_markdown(sections['main_answer'], "assistant_bubble")
                else:
                    self.text_widget.insert(tk.END, sections['main_answer'], "assistant_bubble")
                self.text_widget.insert(tk.END, "\n")
            
            # === METRIKEN ===
            if metadata:
                self._insert_metrics_compact(metadata)
            elif sections.get('metadata'):
                self._insert_metrics_compact(sections['metadata'])
            
            # === FEEDBACK ===
            self._insert_feedback_widget(message_id)
            
            # === QUELLEN ===
            if COLLAPSIBLE_AVAILABLE and sections.get('sources'):
                self._insert_sources_collapsible(sections['sources'], message_id)
            elif sections.get('sources'):
                self._insert_sources(sections['sources'])
            
            # === VORSCHLÄGE ===
            if COLLAPSIBLE_AVAILABLE and sections.get('suggestions'):
                self._insert_suggestions_collapsible(sections['suggestions'], message_id)
            elif sections.get('suggestions'):
                self._insert_suggestions(sections['suggestions'])
            
            self.text_widget.insert(tk.END, "\n", "message_separator")
            
            self.text_widget.config(state='disabled')
            self.text_widget.see(tk.END)
            
            # Cleanup Marks
            self.text_widget.mark_unset(placeholder_start_mark)
            self.text_widget.mark_unset(placeholder_end_mark)
            
            logger.info(f"✅ Platzhalter ersetzt für {message_id}")
            
        except tk.TclError as e:
            logger.error(f"❌ Fehler beim Ersetzen des Platzhalters: {e}")

    
    def insert_formatted_content(self, content: str, default_tag: str, message_id: str = None) -> None:
        """
        Fügt formatierte RAG-Antwort mit Sections ein
        
        Args:
            content: Roher Antwort-Text
            default_tag: Standard-Tag für Text
            message_id: Eindeutige Message-ID für Collapsible Sections (Feature #1)
        """
        # Parse Content in Sections
        if self.markdown_renderer:
            sections = self.markdown_renderer.parse_rag_response(content)
        else:
            sections = {'main_answer': content}
        
        # === HAUPTANTWORT ===
        if sections.get('main_answer'):
            self.text_widget.insert(tk.END, "📝 ", "header")
            self.text_widget.insert(tk.END, "Antwort:\n", "header")
            
            # Rendere mit Markdown wenn verfügbar
            if self.markdown_renderer:
                self.markdown_renderer.render_markdown(sections['main_answer'], "assistant_main")
            else:
                self.text_widget.insert(tk.END, sections['main_answer'], "assistant_main")
            
            self.text_widget.insert(tk.END, "\n")
        
        # === METADATEN ===
        if sections.get('metadata'):
            self._insert_metadata(sections['metadata'], message_id=message_id)
        
        # ✨ Feature #1: Collapsible Sections statt Details-Toggle
        if COLLAPSIBLE_AVAILABLE and message_id:
            # === QUELLEN (Collapsible) ===
            if sections.get('sources'):
                self._insert_sources_collapsible(sections['sources'], message_id)
            
            # === AGENTS (Collapsible) ===
            if sections.get('agents'):
                self._insert_agents_collapsible(sections['agents'], message_id)
            
            # === VORSCHLÄGE (Collapsible) ===
            if sections.get('suggestions'):
                self._insert_suggestions_collapsible(sections['suggestions'], message_id)
        else:
            # Fallback: Alte Details-Toggle-Methode
            if sections.get('sources') or sections.get('agents') or sections.get('suggestions'):
                self._insert_collapsible_details(sections)
    
    def _insert_metadata(self, metadata: Dict, message_id: str = None) -> None:
        """Fügt Metadaten-Zeile mit dynamischen Icons ein"""
        # ✨ Dynamische Icons
        conf_icon = VeritasIcons.metadata('confidence') if ICONS_AVAILABLE else '🎯'
        sources_icon = VeritasIcons.source('sources') if ICONS_AVAILABLE else '📚'
        agents_icon = VeritasIcons.agent('agents') if ICONS_AVAILABLE else '🤖'
        duration_icon = VeritasIcons.metadata('duration') if ICONS_AVAILABLE else '⚡'
        
        # ✨ Feature #12: Confidence-Score Visualisierung mit farbigen Badges
        if metadata.get('confidence'):
            conf_value = metadata['confidence']
            
            # Bestimme Badge-Style basierend auf Score
            if conf_value >= 80:
                badge_tag = "confidence_badge_high"
                badge_text = f" {conf_value}% HOCH "
            elif conf_value >= 60:
                badge_tag = "confidence_badge_med"
                badge_text = f" {conf_value}% MITTEL "
            else:
                badge_tag = "confidence_badge_low"
                badge_text = f" {conf_value}% NIEDRIG "
            
            # Icon + Badge
            self.text_widget.insert(tk.END, f"{conf_icon} ", "metadata")
            self.text_widget.insert(tk.END, badge_text, badge_tag)
            self.text_widget.insert(tk.END, "  ", "metadata")
        
        # Quellen-Anzahl
        if metadata.get('sources_count'):
            self.text_widget.insert(tk.END, f"{sources_icon} {metadata['sources_count']} Quellen", "metadata")
            self.text_widget.insert(tk.END, "  ", "metadata")
        
        # Agents-Anzahl
        if metadata.get('agents_count'):
            self.text_widget.insert(tk.END, f"{agents_icon} {metadata['agents_count']} Agents", "metadata")
            self.text_widget.insert(tk.END, "  ", "metadata")
        
        # Dauer
        if metadata.get('duration'):
            self.text_widget.insert(tk.END, f"{duration_icon} {metadata['duration']}s", "metadata")
        
        self.text_widget.insert(tk.END, "\n\n", "metadata")
    
    def _insert_metrics_compact(self, metadata: Dict) -> None:
        """
        ✨ NEW: Fügt kompakte Metriken-Badge ein (Inline horizontal)
        
        Format: '🎯 85% | ⏱️ 2.3s | 📚 5 Quellen | 🤖 3 Agents'
        
        Args:
            metadata: Dict mit {confidence, duration, sources_count, agents_count}
        """
        if not metadata:
            return
        
        metrics_parts = []
        
        # Confidence mit farbigem Badge
        if metadata.get('confidence'):
            conf_value = metadata['confidence']
            
            # Bestimme Badge-Style und Icon
            if conf_value >= 80:
                badge_tag = "confidence_badge_high"
                icon = "🟢"  # Grüner Kreis
            elif conf_value >= 60:
                badge_tag = "confidence_badge_med"
                icon = "🟡"  # Gelber Kreis
            else:
                badge_tag = "confidence_badge_low"
                icon = "🔴"  # Roter Kreis
            
            # Badge als Inline-Text (nicht separater Tag)
            metrics_parts.append(f"{icon} {conf_value}%")
        
        # Dauer
        if metadata.get('duration'):
            duration = metadata['duration']
            metrics_parts.append(f"⏱️ {duration:.1f}s" if isinstance(duration, float) else f"⏱️ {duration}s")
        
        # Quellen-Anzahl
        if metadata.get('sources_count'):
            metrics_parts.append(f"📚 {metadata['sources_count']} Quellen")
        
        # Agents-Anzahl
        if metadata.get('agents_count'):
            metrics_parts.append(f"🤖 {metadata['agents_count']} Agents")
        
        # Zusammenfügen mit Pipe-Separator
        if metrics_parts:
            metrics_text = " | ".join(metrics_parts)
            self.text_widget.insert(tk.END, metrics_text + "\n\n", "metrics_compact")
            logger.debug(f"✅ Metriken-Badge eingefügt: {metrics_text}")
    
    def _create_feedback_widget(self, message_id: str) -> tk.Frame:
        """
        ✨ NEW: Erstellt Feedback-Widget als eingebetteten Frame
        
        Args:
            message_id: Eindeutige Message-ID
            
        Returns:
            tk.Frame mit Feedback-Buttons
        """
        import tkinter.ttk as ttk
        
        # Haupt-Frame
        feedback_frame = tk.Frame(
            self.text_widget,
            bg='#F5F5F5',
            relief='flat',
            padx=5,
            pady=5
        )
        
        # Label
        label = tk.Label(
            feedback_frame,
            text="War diese Antwort hilfreich?",
            font=('Segoe UI', 8),
            bg='#F5F5F5',
            fg='#666'
        )
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Thumbs Up Button
        thumbs_up_btn = tk.Button(
            feedback_frame,
            text="👍",
            font=('Segoe UI', 12),
            bg='#F5F5F5',
            relief='flat',
            borderwidth=0,
            cursor='hand2',
            command=lambda: self._on_feedback_thumbs_up(message_id, feedback_frame)
        )
        thumbs_up_btn.pack(side=tk.LEFT, padx=2)
        
        # Thumbs Down Button
        thumbs_down_btn = tk.Button(
            feedback_frame,
            text="👎",
            font=('Segoe UI', 12),
            bg='#F5F5F5',
            relief='flat',
            borderwidth=0,
            cursor='hand2',
            command=lambda: self._on_feedback_thumbs_down(message_id, feedback_frame)
        )
        thumbs_down_btn.pack(side=tk.LEFT, padx=2)
        
        # Kommentar-Button (optional)
        comment_btn = tk.Button(
            feedback_frame,
            text="💬",
            font=('Segoe UI', 12),
            bg='#F5F5F5',
            relief='flat',
            borderwidth=0,
            cursor='hand2',
            command=lambda: self._on_feedback_comment(message_id)
        )
        comment_btn.pack(side=tk.LEFT, padx=2)
        
        return feedback_frame
    
    def _on_feedback_thumbs_up(self, message_id: str, widget: tk.Frame) -> None:
        """
        Callback: Thumbs Up geklickt
        
        Args:
            message_id: Message-ID
            widget: Feedback-Widget Frame
        """
        # State speichern
        self._feedback_states[message_id] = {
            'rating': 1,  # 1 = Positiv
            'submitted': True,
            'timestamp': datetime.now().isoformat()
        }
        
        # Visual Feedback: Widget durch "Danke" ersetzen
        for child in widget.winfo_children():
            child.destroy()
        
        thank_you_label = tk.Label(
            widget,
            text="✓ Danke für Ihr Feedback! 👍",
            font=('Segoe UI', 9, 'bold'),
            bg='#F5F5F5',
            fg='#27ae60'
        )
        thank_you_label.pack(pady=5)
        
        logger.info(f"✅ Positives Feedback für {message_id}")
        
        # ✨ NEW v3.16.0: Backend-Call POST /feedback/submit
        self._submit_feedback_to_backend(message_id, rating=1, category='helpful')
    
    def _on_feedback_thumbs_down(self, message_id: str, widget: tk.Frame) -> None:
        """
        Callback: Thumbs Down geklickt
        
        Args:
            message_id: Message-ID
            widget: Feedback-Widget Frame
        """
        # State speichern
        self._feedback_states[message_id] = {
            'rating': -1,  # -1 = Negativ
            'submitted': True,
            'timestamp': datetime.now().isoformat()
        }
        
        # Visual Feedback
        for child in widget.winfo_children():
            child.destroy()
        
        thank_you_label = tk.Label(
            widget,
            text="✓ Danke für Ihr Feedback! Wir werden uns verbessern. 👎",
            font=('Segoe UI', 9, 'bold'),
            bg='#F5F5F5',
            fg='#e67e22'
        )
        thank_you_label.pack(pady=5)
        
        logger.info(f"⚠️ Negatives Feedback für {message_id}")
        
        # ✨ NEW v3.16.0: Backend-Call POST /feedback/submit
        self._submit_feedback_to_backend(message_id, rating=-1, category='incorrect')
    
    def _on_feedback_comment(self, message_id: str) -> None:
        """
        Callback: Kommentar-Button geklickt
        
        Args:
            message_id: Message-ID
        """
        logger.info(f"💬 Kommentar-Dialog für {message_id}")
        
        # Öffne Kommentar-Dialog
        try:
            from tkinter import simpledialog
            comment = simpledialog.askstring(
                "Feedback-Kommentar",
                "Möchten Sie einen Kommentar hinzufügen?",
                parent=self.parent_window
            )
            
            if comment:
                self._feedback_states[message_id] = {
                    'rating': 0,  # 0 = Neutral mit Kommentar
                    'comment': comment,
                    'submitted': True,
                    'timestamp': datetime.now().isoformat()
                }
                logger.info(f"💬 Kommentar für {message_id}: {comment[:50]}...")
                
                # ✨ NEW v3.16.0: Backend-Call POST /feedback/submit
                self._submit_feedback_to_backend(message_id, rating=0, comment=comment, category='other')
        except Exception as e:
            logger.error(f"❌ Fehler beim Kommentar-Dialog: {e}")
    
    def _submit_feedback_to_backend(
        self, 
        message_id: str, 
        rating: int,
        category: Optional[str] = None,
        comment: Optional[str] = None
    ) -> None:
        """
        ✨ NEW v3.16.0: Sendet Feedback an Backend API
        
        Args:
            message_id: Message-ID
            rating: Rating (1=👍, -1=👎, 0=💬)
            category: Kategorie (helpful, incorrect, unclear, other)
            comment: Optionaler Kommentar
        """
        if not self.feedback_api:
            logger.warning(f"⚠️ Feedback API nicht verfügbar - nur lokale Speicherung für {message_id}")
            return
        
        try:
            # Non-blocking: Führe API-Call in separatem Thread aus
            import threading
            
            def submit_async():
                try:
                    response = self.feedback_api.submit_feedback(
                        message_id=message_id,
                        rating=rating,
                        category=category,
                        comment=comment,
                        user_id="anonymous"
                    )
                    
                    if response.get('success'):
                        logger.info(f"✅ Feedback erfolgreich an Backend gesendet: {message_id} (ID: {response.get('feedback_id')})")
                    else:
                        logger.error(f"❌ Fehler beim Senden von Feedback: {response.get('error')}")
                
                except Exception as e:
                    logger.error(f"❌ Exception beim Senden von Feedback: {e}")
            
            # Starte Thread
            thread = threading.Thread(target=submit_async, daemon=True)
            thread.start()
            logger.debug(f"✅ Feedback-Thread gestartet für {message_id}")
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Starten des Feedback-Threads: {e}")
    
    def _insert_feedback_widget(self, message_id: str) -> None:
        """
        ✨ NEW: Fügt Feedback-Widget als eingebetteten Frame ein
        
        Args:
            message_id: Eindeutige Message-ID
        """
        # Prüfe, ob bereits Feedback gegeben wurde
        if message_id in self._feedback_states and self._feedback_states[message_id].get('submitted'):
            logger.debug(f"⏭️ Feedback bereits gegeben für {message_id}")
            return
        
        # Erstelle Widget
        feedback_widget = self._create_feedback_widget(message_id)
        
        # Füge als embedded window ein
        try:
            self.text_widget.window_create(tk.END, window=feedback_widget)
            self.text_widget.insert(tk.END, "\n\n", "message_separator")
            logger.debug(f"✅ Feedback-Widget eingefügt für {message_id}")
        except tk.TclError as e:
            logger.error(f"❌ Fehler beim Einfügen des Feedback-Widgets: {e}")
    
    def _insert_answer_toolbar(self, content: str, metadata: Dict, message_id: str) -> None:
        """
        ✨ v3.18.0: Fügt kompakte Answer Toolbar unter Assistant-Antwort ein
        
        Layout: [👍 👎] | [📋 Kopieren] [🔄 Wiederholen] | [▼ Meta] [▼ Quellen] [▼ Vorschläge] [▼ Raw]
        
        Args:
            content: Antwort-Text
            metadata: Metadaten (sources, suggestions, etc.)
            message_id: Message-ID
        """
        # Prüfe Feature-Flag
        if not hasattr(self, '_answer_toolbar_enabled') or not self._answer_toolbar_enabled:
            logger.debug("⏭️ AnswerToolbar deaktiviert")
            return
        
        try:
            # Import AnswerToolbar (lazy)
            from frontend.components.answer_toolbar import create_answer_toolbar
            
            # Message-Daten vorbereiten
            message_data = {
                'id': message_id,
                'content': content,
                'metadata': metadata if metadata else {},
                'sources': metadata.get('sources_metadata', []) if metadata else [],
                'suggestions': metadata.get('suggestions', []) if metadata else [],
                'raw_response': content,
                'original_query': ''  # TODO: Extract from context if needed
            }
            
            # Toolbar erstellen mit Callbacks
            toolbar = create_answer_toolbar(
                parent=self.text_widget,
                message_data=message_data,
                on_feedback=lambda feedback_type: self._handle_toolbar_feedback(message_id, feedback_type),
                on_copy=lambda text: self._handle_toolbar_copy(text),
                on_repeat=lambda query: self._handle_toolbar_repeat(query),
                on_show_raw=lambda raw: self._handle_toolbar_raw(raw)
            )
            
            # Toolbar rendern (als embedded frame)
            toolbar.render()
            
            logger.debug(f"✅ AnswerToolbar gerendert für {message_id}")
            
        except ImportError as e:
            logger.warning(f"⚠️ AnswerToolbar nicht verfügbar: {e}")
        except Exception as e:
            logger.error(f"❌ Fehler beim Rendern der AnswerToolbar: {e}")
    
    def _handle_toolbar_feedback(self, message_id: str, feedback_type: str) -> None:
        """
        ✨ v3.18.0: Callback für Toolbar-Feedback (👍 👎)
        
        Args:
            message_id: Message-ID
            feedback_type: 'positive' oder 'negative'
        """
        try:
            logger.info(f"📊 Toolbar-Feedback: {feedback_type} für {message_id}")
            
            # Feedback in State speichern
            if not hasattr(self, '_feedback_states'):
                self._feedback_states = {}
            
            self._feedback_states[message_id] = {
                'type': feedback_type,
                'submitted': True,
                'timestamp': time.time()
            }
            
            # TODO: Backend-Endpoint für Feedback aufrufen
            logger.debug(f"✅ Feedback gespeichert: {feedback_type}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Feedbacks: {e}")
    
    def _handle_toolbar_copy(self, text: str) -> None:
        """
        ✨ v3.18.0: Callback für Toolbar-Copy (📋 Kopieren)
        
        Args:
            text: Text zum Kopieren
        """
        try:
            logger.info(f"📋 Antwort in Zwischenablage kopiert ({len(text)} Zeichen)")
            # Clipboard-Handling erfolgt bereits in AnswerToolbar
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Kopieren: {e}")
    
    def _handle_toolbar_repeat(self, query: str) -> None:
        """
        ✨ v3.18.0: Callback für Toolbar-Repeat (🔄 Wiederholen)
        
        Args:
            query: Query zum Wiederholen
        """
        try:
            logger.info(f"🔄 Query wiederholen: {query}")
            
            # Verwende suggestion_click_callback (falls gesetzt)
            if hasattr(self, 'suggestion_click_callback') and self.suggestion_click_callback:
                self.suggestion_click_callback(query)
                logger.debug("✅ Query weitergeleitet an suggestion_click_callback")
            else:
                logger.warning("⚠️ suggestion_click_callback nicht gesetzt - Wiederholen nicht möglich")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Wiederholen: {e}")
    
    def _handle_toolbar_raw(self, raw_response: str) -> None:
        """
        ✨ v3.18.0: Callback für Toolbar-Raw (Raw-Response anzeigen)
        
        Args:
            raw_response: Raw Response Text
        """
        try:
            logger.info(f"🔍 Raw-Response anzeigen ({len(raw_response)} Zeichen)")
            
            # Verwende DialogManager (falls verfügbar)
            if hasattr(self, 'dialog_manager') and self.dialog_manager:
                self.dialog_manager.show_info(
                    title="Raw Response",
                    message=raw_response
                )
                logger.debug("✅ Raw-Response in Dialog angezeigt")
            else:
                logger.warning("⚠️ DialogManager nicht verfügbar")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anzeigen der Raw-Response: {e}")
    
    def _insert_collapsible_details(self, sections: Dict) -> None:
        """Fügt ausklappbare Details-Section ein"""
        # Details-Header (klickbar)
        self.text_widget.insert(tk.END, "▶️ ", "clickable")
        details_header_start = self.text_widget.index(tk.END)
        self.text_widget.insert(tk.END, "Details anzeigen", "clickable")
        details_header_end = self.text_widget.index(tk.END)
        self.text_widget.insert(tk.END, " (Quellen, Agents, Vorschläge)\n", "collapsed")
        
        # Details-Inhalt (initial versteckt)
        details_content_start = self.text_widget.index(tk.END)
        
        # === QUELLEN ===
        if sections.get('sources'):
            self._insert_sources(sections['sources'])
        
        # === AGENTS ===
        if sections.get('agents'):
            self._insert_agents(sections['agents'])
        
        # === VORSCHLÄGE ===
        if sections.get('suggestions'):
            self._insert_suggestions(sections['suggestions'])
        
        details_content_end = self.text_widget.index(tk.END)
        
        # Details verstecken und Toggle-Handler binden
        self._setup_collapsible_toggle(
            details_header_start, 
            details_header_end, 
            details_content_start, 
            details_content_end
        )
    
    def _insert_sources(self, sources: List[str]) -> None:
        """Fügt Quellen-Liste mit dynamischen Icons und Hover-Tooltips ein"""
        # ✨ Dynamisches Icon-System
        sources_icon = VeritasIcons.source('sources') if ICONS_AVAILABLE else '📚'
        self.text_widget.insert(tk.END, f"\n{sources_icon} ", "header")
        self.text_widget.insert(tk.END, "Verwendete Quellen:\n", "header")
        
        for i, source in enumerate(sources, 1):
            # Extrahiere Metadaten aus source-String (falls vorhanden)
            # Format: "Title [confidence: 0.85] [page: 5] [type: pdf]"
            metadata = self._extract_source_metadata(source)
            
            # ✨ Dynamisches Source-Icon basierend auf Typ
            source_icon = get_source_icon(source) if ICONS_AVAILABLE else '📄'
            
            # Regex-Patterns
            url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
            file_pattern = r'([A-Za-z]:\\[\\\w\s\.-]+|/[\w/\.-]+|[\w\.-]+\.(?:pdf|docx?|txt|md|html?))'
            
            urls = re.findall(url_pattern, source)
            files = re.findall(file_pattern, source)
            
            if urls or files:
                # Source hat Links - klickbar machen MIT Hover-Tooltip
                parts = re.split(f'({url_pattern}|{file_pattern})', source)
                # ✨ Source-Icon vor Nummer
                self.text_widget.insert(tk.END, f"  {source_icon} {i}. ", "source")
                
                for part in parts:
                    if not part:
                        continue
                    
                    if re.match(url_pattern, part) or re.match(file_pattern, part):
                        # Klickbarer Link
                        link_start = self.text_widget.index(tk.END)
                        self.text_widget.insert(tk.END, part, ("clickable_link", "source"))
                        link_end = self.text_widget.index(tk.END)
                        
                        # Unique Tag
                        link_tag = f"link_{i}_{hash(part)}"
                        self.text_widget.tag_add(link_tag, link_start, link_end)
                        
                        # Click-Handler wenn SourceLinkHandler verfügbar
                        if self.source_link_handler:
                            # ✨ NEU: Scroll-to-Source Animation vor dem Öffnen
                            def create_click_handler(idx, url):
                                def handler(e):
                                    self.scroll_to_source(idx)
                                    # Verzögerung damit Scroll-Animation abläuft
                                    self.parent_window.after(
                                        550,  # 500ms Scroll + 50ms Buffer
                                        lambda: self.source_link_handler.open_source_link(url)
                                    )
                                return handler
                            
                            self.text_widget.tag_bind(
                                link_tag, 
                                "<Button-1>", 
                                create_click_handler(i, part)
                            )
                            
                            # === NEU: Hover-Tooltip hinzufügen ===
                            self._add_source_hover_tooltip(link_tag, part, metadata)
                        
                        # Cursor über Events
                        self.text_widget.tag_bind(link_tag, "<Enter>", lambda e: self.text_widget.config(cursor="hand2"))
                        self.text_widget.tag_bind(link_tag, "<Leave>", lambda e: self.text_widget.config(cursor=""))
                    else:
                        # Normaler Text
                        self.text_widget.insert(tk.END, part, "source")
                
                self.text_widget.insert(tk.END, "\n")
            else:
                # Keine Links - normale Darstellung MIT Hover-Tooltip
                link_start = self.text_widget.index(tk.END)
                # ✨ Source-Icon vor Nummer
                self.text_widget.insert(tk.END, f"  {source_icon} {i}. {source}\n", "source")
                link_end = self.text_widget.index(tk.END)
                
                # Unique Tag für DB-Quelle
                db_source_tag = f"db_source_{i}_{hash(source)}"
                self.text_widget.tag_add(db_source_tag, link_start, link_end)
                
                # === NEU: Hover-Tooltip für DB-Quellen ===
                if self.source_link_handler:
                    self._add_source_hover_tooltip(db_source_tag, source, metadata)
    
    def _extract_source_metadata(self, source: str) -> Dict[str, Any]:
        """
        Extrahiert Metadaten aus Source-String
        
        Format: "Title [confidence: 0.85] [page: 5] [type: pdf]"
        
        Returns:
            Dict mit Metadaten (confidence, page, type, etc.)
        """
        metadata = {}
        
        # Confidence extrahieren
        conf_match = re.search(r'\[confidence:\s*([\d.]+)\]', source, re.IGNORECASE)
        if conf_match:
            try:
                metadata['confidence'] = float(conf_match.group(1))
            except ValueError:
                pass
        
        # Page extrahieren
        page_match = re.search(r'\[page:\s*(\d+)\]', source, re.IGNORECASE)
        if page_match:
            try:
                metadata['page'] = int(page_match.group(1))
            except ValueError:
                pass
        
        # Type extrahieren
        type_match = re.search(r'\[type:\s*(\w+)\]', source, re.IGNORECASE)
        if type_match:
            metadata['type'] = type_match.group(1)
        
        return metadata
    
    def _add_source_hover_tooltip(
        self, 
        tag_name: str, 
        source_name: str, 
        metadata: Dict[str, Any]
    ) -> None:
        """
        Fügt Hover-Tooltip zu einem Quellen-Tag hinzu
        
        Args:
            tag_name: Name des Text-Tags
            source_name: Name/URL der Quelle
            metadata: Metadaten (confidence, page, type)
        """
        # Entferne Metadaten-Annotations aus Anzeigenamen
        clean_name = re.sub(r'\[.*?\]', '', source_name).strip()
        
        # Erstelle Dummy-Widget für Tooltip-Binding
        # Wir verwenden den Text-Widget selbst mit Tag-spezifischen Bindings
        def show_tooltip(event):
            if self.source_link_handler:
                # Erstelle Tooltip direkt am Cursor
                tooltip = self.source_link_handler.create_hover_tooltip(
                    widget=self.text_widget,
                    source_name=clean_name,
                    preview_text=None,  # Wird vom Backend geladen
                    metadata=metadata
                )
                # Tooltip wird automatisch bei <Leave> versteckt
        
        # Bind an Tag statt Widget
        try:
            self.text_widget.tag_bind(tag_name, "<Enter>", show_tooltip)
        except Exception as e:
            logger.debug(f"Konnte Hover-Tooltip nicht binden: {e}")
    
    def scroll_to_source(self, source_index: int) -> None:
        """
        Animiert Scroll zur Quellen-Zeile mit Easing-Funktion
        
        Args:
            source_index: Index der Quelle (1-basiert)
        """
        try:
            # Finde Quellen-Sektion im Text-Widget
            search_pattern = f"{source_index}."
            start_pos = "1.0"
            
            # Suche nach "1. ", "2. ", etc. in der Quellen-Liste
            pos = self.text_widget.search(search_pattern, start_pos, stopindex=tk.END)
            
            if not pos:
                logger.warning(f"⚠️ Quelle #{source_index} nicht gefunden")
                return
            
            # Aktuelle und Ziel-Position ermitteln
            current_yview = self.text_widget.yview()[0]  # Aktueller Scroll (0.0-1.0)
            target_line = int(pos.split('.')[0])
            total_lines = int(self.text_widget.index(tk.END).split('.')[0])
            target_yview = max(0.0, min(1.0, (target_line - 3) / total_lines))  # 3 Zeilen Padding
            
            # Kein Scroll nötig wenn bereits sichtbar
            if abs(current_yview - target_yview) < 0.05:
                self.highlight_line(pos)
                return
            
            # Smooth Scroll Animation mit Easing
            duration = 500  # 500ms
            frames = 30
            frame_time = duration / frames
            
            def ease_in_out_cubic(t: float) -> float:
                """Cubic Easing Funktion für natürliche Bewegung"""
                if t < 0.5:
                    return 4 * t * t * t
                else:
                    p = 2 * t - 2
                    return 0.5 * p * p * p + 1
            
            def animate_frame(frame: int):
                """Einzelner Animations-Frame"""
                if frame > frames:
                    # Animation beendet → Highlight aktivieren
                    self.highlight_line(pos)
                    return
                
                # Progress berechnen (0.0 → 1.0)
                progress = ease_in_out_cubic(frame / frames)
                
                # Interpolierte Position
                interpolated_yview = current_yview + (target_yview - current_yview) * progress
                
                # Scroll setzen
                self.text_widget.yview_moveto(interpolated_yview)
                
                # Nächster Frame
                self.parent_window.after(int(frame_time), lambda: animate_frame(frame + 1))
            
            # Animation starten
            animate_frame(1)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Scroll-to-Source: {e}")
    
    def highlight_line(self, line_index: str) -> None:
        """
        Flash-Highlight der Ziel-Zeile mit Fade-out-Animation
        
        Args:
            line_index: Tkinter-Index der Zeile (z.B. "5.0")
        """
        try:
            # Zeilen-Bereich ermitteln
            line_start = f"{line_index.split('.')[0]}.0"
            line_end = f"{int(line_index.split('.')[0]) + 1}.0"
            
            # Highlight-Tag hinzufügen
            highlight_tag = f"highlight_{line_index}"
            self.text_widget.tag_add(highlight_tag, line_start, line_end)
            self.text_widget.tag_configure(highlight_tag, background="#fff3cd")  # Gelb
            
            # Fade-out-Animation (2 Sekunden)
            def fade_step(step: int, total_steps: int = 20):
                """Fade-out Schritt"""
                if step > total_steps:
                    # Animation beendet → Tag entfernen
                    self.text_widget.tag_remove(highlight_tag, "1.0", tk.END)
                    return
                
                # Alpha-Wert berechnen (1.0 → 0.0)
                alpha = 1.0 - (step / total_steps)
                
                # Farbe interpolieren (Gelb → Weiß)
                r = int(255)
                g = int(243 + (255 - 243) * (1 - alpha))
                b = int(205 + (255 - 205) * (1 - alpha))
                color = f"#{r:02x}{g:02x}{b:02x}"
                
                # Tag-Farbe aktualisieren
                self.text_widget.tag_configure(highlight_tag, background=color)
                
                # Nächster Schritt (100ms Intervall)
                self.parent_window.after(100, lambda: fade_step(step + 1, total_steps))
            
            # Fade-out starten
            fade_step(1)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Highlight: {e}")
    
    def _insert_agents(self, agents: Dict[str, str]) -> None:
        """Fügt Agent-Analysen mit dynamischen Icons ein"""
        # ✨ Dynamisches Icon
        agents_icon = VeritasIcons.agent('agents') if ICONS_AVAILABLE else '🤖'
        self.text_widget.insert(tk.END, f"\n{agents_icon} ", "header")
        self.text_widget.insert(tk.END, "Agent-Analysen:\n", "header")
        
        for agent_name, agent_result in agents.items():
            self.text_widget.insert(tk.END, f"  • {agent_name}: ", "agent")
            self.text_widget.insert(tk.END, f"{agent_result}\n", "assistant")
    
    def _insert_suggestions(self, suggestions: List[str]) -> None:
        """Fügt Vorschläge mit dynamischen Icons ein"""
        # ✨ Dynamisches Icon
        suggestion_icon = VeritasIcons.get('special', 'suggestion') if ICONS_AVAILABLE else '💡'
        self.text_widget.insert(tk.END, f"\n{suggestion_icon} ", "header")
        self.text_widget.insert(tk.END, "Weitere Schritte:\n", "header")
        
        for suggestion in suggestions:
            self.text_widget.insert(tk.END, f"  • {suggestion}\n", "source")
    
    # ✨ Feature #1: Neue Collapsible-Section-Methoden
    
    def _insert_sources_collapsible(self, sources: List, message_id: str, use_ieee_format: bool = False) -> None:
        """
        Fügt Quellen-Liste als Collapsible Section ein
        
        Args:
            sources: Liste von Quellen (Strings oder SourceMetadata-Dicts)
            message_id: Message-ID für eindeutige Section-ID
            use_ieee_format: ✨ v3.19.0 - Nutze IEEE-Format mit SourceMetadata-Dicts
        """
        if not sources:
            return
        
        # ✨ Dynamisches Icon
        sources_icon = VeritasIcons.source('sources') if ICONS_AVAILABLE else '📚'
        
        # Collapsible Section erstellen (initial collapsed)
        section = CollapsibleSection(
            text_widget=self.text_widget,
            section_id=f"sources_{message_id}",
            title=f"{sources_icon} Quellen ({len(sources)})",
            initially_collapsed=True,  # Quellen standardmäßig eingeklappt
            parent_window=self.parent_window,
            animate=True
        )
        
        # Header einfügen
        section.insert_header()
        
        # Content-Callback: Rendere Quellen (IEEE oder Legacy)
        def render_sources():
            if use_ieee_format:
                # ✨ v3.19.0: IEEE-Format mit SourceMetadata
                for i, source_meta in enumerate(sources, 1):
                    self._insert_single_source_ieee(i, source_meta)
            else:
                # Legacy: String-basierte Quellen
                for i, source in enumerate(sources, 1):
                    self._insert_single_source(i, source)
        
        # Content einfügen
        section.insert_content(render_sources)
        
        self.text_widget.insert(tk.END, "\n")
    
    def _insert_agents_collapsible(self, agents: Dict[str, str], message_id: str) -> None:
        """
        Fügt Agent-Analysen als Collapsible Section ein
        
        Args:
            agents: Dict von Agent-Name → Result
            message_id: Message-ID für eindeutige Section-ID
        """
        if not agents:
            return
        
        # ✨ Dynamisches Icon
        agents_icon = VeritasIcons.agent('agents') if ICONS_AVAILABLE else '🤖'
        
        # Collapsible Section erstellen (initial collapsed)
        section = CollapsibleSection(
            text_widget=self.text_widget,
            section_id=f"agents_{message_id}",
            title=f"{agents_icon} Agent-Analysen ({len(agents)})",
            initially_collapsed=True,  # Agents standardmäßig eingeklappt
            parent_window=self.parent_window,
            animate=True
        )
        
        # Header einfügen
        section.insert_header()
        
        # Content-Callback
        def render_agents():
            for agent_name, agent_result in agents.items():
                self.text_widget.insert(tk.END, f"  • {agent_name}: ", "agent")
                self.text_widget.insert(tk.END, f"{agent_result}\n", "assistant")
        
        # Content einfügen
        section.insert_content(render_agents)
        
        self.text_widget.insert(tk.END, "\n")
    
    def _insert_suggestions_collapsible(self, suggestions: List[str], message_id: str) -> None:
        """
        ✨ v3.19.0: Fügt Vorschläge als klickbare Links ein (Collapsible Section)
        
        Args:
            suggestions: Liste von Vorschlägen/Follow-up-Fragen
            message_id: Message-ID für eindeutige Section-ID
        
        Verhalten:
            - Rendert jeden Vorschlag als klickbaren Link mit 🔗 Icon
            - Click → Sendet Vorschlag als neue Query ans Backend
            - Hover → Underline + Cursor Change + Background-Highlight
        """
        if not suggestions:
            return
        
        # ✨ Dynamisches Icon
        suggestion_icon = VeritasIcons.get('special', 'suggestion') if ICONS_AVAILABLE else '💡'
        
        # Collapsible Section erstellen (initial expanded)
        section = CollapsibleSection(
            text_widget=self.text_widget,
            section_id=f"suggestions_{message_id}",
            title=f"{suggestion_icon} Weitere Schritte ({len(suggestions)})",
            initially_collapsed=False,  # Vorschläge standardmäßig sichtbar
            parent_window=self.parent_window,
            animate=True
        )
        
        # Header einfügen
        section.insert_header()
        
        # Content-Callback: Rendere Vorschläge als klickbare Links
        def render_suggestions():
            for i, suggestion in enumerate(suggestions, 1):
                self._insert_suggestion_link(i, suggestion)
        
        # Content einfügen
        section.insert_content(render_suggestions)
        
        self.text_widget.insert(tk.END, "\n")
    
    def _insert_suggestion_link(self, index: int, suggestion: str) -> None:
        """
        ✨ v3.19.0: Fügt einen Vorschlag als klickbaren Link ein
        
        Args:
            index: Vorschlag-Nummer (1-basiert)
            suggestion: Vorschlagstext (z.B. "Welche Kosten fallen an?")
        
        Layout:
            🔗 1. Welche Kosten fallen für eine Baugenehmigung an?
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
               (klickbar, Hover: Underline + Background)
        
        Click-Verhalten:
            - Ruft suggestion_click_callback auf (falls gesetzt)
            - Callback erhält suggestion-Text als Parameter
            - Callback sollte Query-Input füllen und senden
        """
        # Icon vor Suggestion
        link_icon = '🔗' if not ICONS_AVAILABLE else VeritasIcons.get('special', 'link', '🔗')
        
        # Prefix einfügen (nicht klickbar)
        self.text_widget.insert(tk.END, f"  {link_icon} {index}. ", "suggestion_prefix")
        
        # Suggestion-Text einfügen (KLICKBAR)
        suggestion_start = self.text_widget.index(tk.END)
        self.text_widget.insert(tk.END, suggestion, "suggestion_link")
        suggestion_end = self.text_widget.index(tk.END)
        
        # Unique Tag für Click-Handling
        suggestion_tag = f"suggestion_click_{index}_{hash(suggestion)}"
        self.text_widget.tag_add(suggestion_tag, suggestion_start, suggestion_end)
        
        # === CLICK-HANDLER ===
        if hasattr(self, 'suggestion_click_callback') and self.suggestion_click_callback:
            def create_click_handler(text):
                def handler(e):
                    logger.info(f"[SUGGESTION-CLICK] User clicked: {text[:50]}...")
                    self.suggestion_click_callback(text)
                return handler
            
            self.text_widget.tag_bind(
                suggestion_tag,
                "<Button-1>",
                create_click_handler(suggestion)
            )
        else:
            logger.warning("[SUGGESTION] suggestion_click_callback nicht gesetzt - Links nicht funktional!")
        
        # === HOVER-EFFECTS ===
        def on_enter(event):
            self.text_widget.tag_config(suggestion_tag, underline=1, background='#E8F4F8')
            self.text_widget.config(cursor="hand2")
        
        def on_leave(event):
            self.text_widget.tag_config(suggestion_tag, underline=0, background='')
            self.text_widget.config(cursor="")
        
        self.text_widget.tag_bind(suggestion_tag, "<Enter>", on_enter)
        self.text_widget.tag_bind(suggestion_tag, "<Leave>", on_leave)
        
        # Zeilenumbruch
        self.text_widget.insert(tk.END, "\n")
        
        logger.debug(f"[SUGGESTION] Inserted clickable link #{index}: {suggestion[:50]}...")
    
    def _insert_raw_response_collapsible(self, content: str, metadata: Dict, message_id: str) -> None:
        """
        ✨ NEW: Fügt Raw-Response als Collapsible Section ein (für Debugging)
        
        Args:
            content: Original-Content (ungefiltert)
            metadata: Metadaten mit LLM-Details
            message_id: Message-ID für eindeutige Section-ID
        """
        if not content:
            return
        
        # ✨ Debug-Icon
        debug_icon = '🔍'
        
        # Collapsible Section erstellen (initial collapsed - nur für Power-User)
        section = CollapsibleSection(
            text_widget=self.text_widget,
            section_id=f"raw_response_{message_id}",
            title=f"{debug_icon} Raw-Antwort (Debug)",
            initially_collapsed=True,  # Standardmäßig eingeklappt
            parent_window=self.parent_window,
            animate=True
        )
        
        # Header einfügen
        section.insert_header()
        
        # Content-Callback
        def render_raw_response():
            # === LLM-PARAMETER ===
            if metadata:
                model = metadata.get('model', 'unknown')
                temperature = metadata.get('temperature', 'N/A')
                max_tokens = metadata.get('max_tokens', 'N/A')
                top_p = metadata.get('top_p', 'N/A')
                duration = metadata.get('duration', 'N/A')
                
                self.text_widget.insert(tk.END, "  📊 LLM-Parameter:\n", "raw_header")
                self.text_widget.insert(tk.END, f"    • Modell: {model}\n", "raw_param")
                self.text_widget.insert(tk.END, f"    • Temperature: {temperature}\n", "raw_param")
                self.text_widget.insert(tk.END, f"    • Max Tokens: {max_tokens}\n", "raw_param")
                self.text_widget.insert(tk.END, f"    • Top-p: {top_p}\n", "raw_param")
                if duration != 'N/A':
                    self.text_widget.insert(tk.END, f"    • Antwortzeit: {duration:.2f}s\n", "raw_param")
                self.text_widget.insert(tk.END, "\n", "raw_param")
            
            # === RAW CONTENT ===
            self.text_widget.insert(tk.END, "  📝 Ungefilterte LLM-Antwort:\n", "raw_header")
            self.text_widget.insert(tk.END, "  " + "─" * 70 + "\n", "raw_separator")
            
            # Content mit Einrückung
            for line in content.split('\n'):
                self.text_widget.insert(tk.END, f"  {line}\n", "raw_content")
            
            self.text_widget.insert(tk.END, "  " + "─" * 70 + "\n", "raw_separator")
            
            # === PROBLEME ERKENNEN ===
            probleme = []
            if "Antwort auf die Frage" in content:
                probleme.append("⚠️ Generische Meta-Phrase erkannt: 'Antwort auf die Frage'")
            if "Basierend auf" in content and content.startswith("Basierend auf"):
                probleme.append("⚠️ Generische Meta-Phrase erkannt: 'Basierend auf'")
            if "Hier ist" in content and content.startswith("Hier ist"):
                probleme.append("⚠️ Generische Meta-Phrase erkannt: 'Hier ist'")
            if len(content) < 50:
                probleme.append("⚠️ Sehr kurze Antwort (< 50 Zeichen)")
            
            if probleme:
                self.text_widget.insert(tk.END, "\n  ⚠️ Erkannte Probleme:\n", "raw_warning")
                for problem in probleme:
                    self.text_widget.insert(tk.END, f"    • {problem}\n", "raw_warning")
                self.text_widget.insert(tk.END, "\n  💡 Tipp: Prüfe Dual-Prompt System im Backend\n", "raw_tip")
        
        # Content einfügen
        section.insert_content(render_raw_response)
        
        self.text_widget.insert(tk.END, "\n")
    
    def _insert_single_source(self, index: int, source: str) -> None:
        """
        Fügt eine einzelne Quelle ein (Helper für _insert_sources_collapsible)
        
        Args:
            index: Quellen-Nummer (1-basiert)
            source: Quellen-String
        """
        # Extrahiere Metadaten
        metadata = self._extract_source_metadata(source)
        
        # ✨ Dynamisches Source-Icon basierend auf Typ
        source_icon = get_source_icon(source) if ICONS_AVAILABLE else '📄'
        
        # Regex-Patterns
        url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
        file_pattern = r'([A-Za-z]:\\[\\\w\s\.-]+|/[\w/\.-]+|[\w\.-]+\.(?:pdf|docx?|txt|md|html?))'
        
        urls = re.findall(url_pattern, source)
        files = re.findall(file_pattern, source)
        
        if urls or files:
            # Source hat Links - klickbar machen MIT Hover-Tooltip
            parts = re.split(f'({url_pattern}|{file_pattern})', source)
            # ✨ Source-Icon vor Nummer
            self.text_widget.insert(tk.END, f"  {source_icon} {index}. ", "source")
            
            for part in parts:
                if not part:
                    continue
                
                if re.match(url_pattern, part) or re.match(file_pattern, part):
                    # Klickbarer Link
                    link_start = self.text_widget.index(tk.END)
                    self.text_widget.insert(tk.END, part, ("clickable_link", "source"))
                    link_end = self.text_widget.index(tk.END)
                    
                    # Unique Tag
                    link_tag = f"link_{index}_{hash(part)}"
                    self.text_widget.tag_add(link_tag, link_start, link_end)
                    
                    # Click-Handler wenn SourceLinkHandler verfügbar
                    if self.source_link_handler:
                        # ✨ Scroll-to-Source Animation
                        def create_click_handler(idx, url):
                            def handler(e):
                                self.scroll_to_source(idx)
                                # Verzögerung damit Scroll-Animation abläuft
                                self.parent_window.after(
                                    550,  # 500ms Scroll + 50ms Buffer
                                    lambda: self.source_link_handler.open_source_link(url)
                                )
                            return handler
                        
                        self.text_widget.tag_bind(
                            link_tag, 
                            "<Button-1>", 
                            create_click_handler(index, part)
                        )
                        
                        # Hover-Tooltip hinzufügen
                        self._add_source_hover_tooltip(link_tag, part, metadata)
                    
                    # Cursor über Events
                    self.text_widget.tag_bind(link_tag, "<Enter>", lambda e: self.text_widget.config(cursor="hand2"))
                    self.text_widget.tag_bind(link_tag, "<Leave>", lambda e: self.text_widget.config(cursor=""))
                else:
                    # Normaler Text
                    self.text_widget.insert(tk.END, part, "source")
            
            self.text_widget.insert(tk.END, "\n")
        else:
            # Keine Links - normale Darstellung MIT Hover-Tooltip
            link_start = self.text_widget.index(tk.END)
            # ✨ Source-Icon vor Nummer
            self.text_widget.insert(tk.END, f"  {source_icon} {index}. {source}\n", "source")
            link_end = self.text_widget.index(tk.END)
            
            # Unique Tag für DB-Quelle
            db_source_tag = f"db_source_{index}_{hash(source)}"
            self.text_widget.tag_add(db_source_tag, link_start, link_end)
            
            # Hover-Tooltip für DB-Quellen
            if self.source_link_handler:
                self._add_source_hover_tooltip(db_source_tag, source, metadata)
    
    def _insert_single_source_ieee(self, index: int, source_meta: Dict[str, Any]) -> None:
        """
        ✨ v3.19.0: Fügt eine Quelle im IEEE-Format ein
        
        IEEE-Format: [N] Author, "Title", Type, Year, [Online]. Available: URL
        
        Args:
            index: Quellen-Nummer (1-basiert, entspricht Citation-ID)
            source_meta: SourceMetadata-Dict {id, title, type, author, year, url, 
                         source_file, page, confidence, content_preview}
        
        Beispiel:
            [1] Landesregierung BW, "Landesbauordnung Baden-Württemberg (LBO BW)", 
                Gesetz, 2023, [Online]. Verfügbar: LBO_BW_2023.pdf (Confidence: 87%)
        """
        # Extrahiere Metadaten
        cite_id = source_meta.get('id', index)
        title = source_meta.get('title', 'Unbekanntes Dokument')
        doc_type = source_meta.get('type', 'Dokument')
        author = source_meta.get('author')
        year = source_meta.get('year')
        url = source_meta.get('url')
        source_file = source_meta.get('source_file')
        page = source_meta.get('page')
        confidence = source_meta.get('confidence')
        content_preview = source_meta.get('content_preview', '')
        
        # ✨ Dynamisches Icon basierend auf Typ
        if doc_type.lower() in ['gesetz', 'law']:
            source_icon = '⚖️'
        elif doc_type.lower() in ['verordnung', 'regulation']:
            source_icon = '📜'
        elif doc_type.lower() in ['urteil', 'judgment']:
            source_icon = '🔨'
        elif doc_type.lower() in ['kommentar', 'commentary']:
            source_icon = '💬'
        else:
            source_icon = VeritasIcons.source('sources') if ICONS_AVAILABLE else '📄'
        
        # === IEEE-Formatierung ===
        ieee_parts = []
        
        # [N] Author (optional)
        ieee_parts.append(f"[{cite_id}]")
        if author:
            ieee_parts.append(author)
        
        # "Title"
        ieee_parts.append(f'"{title}"')
        
        # Type (Gesetz, Verordnung, etc.)
        ieee_parts.append(doc_type)
        
        # Year (optional)
        if year:
            ieee_parts.append(year)
        
        # [Online]. Available: URL/File
        online_part = "[Online]."
        if url:
            online_part += f" Verfügbar: {url}"
        elif source_file:
            online_part += f" Verfügbar: {source_file}"
            if page:
                online_part += f", S. {page}"
        ieee_parts.append(online_part)
        
        # Confidence Score (optional, am Ende)
        if confidence is not None and confidence > 0:
            ieee_parts.append(f"(Confidence: {confidence:.0%})")
        
        # === Zusammensetzen ===
        ieee_formatted = f"  {source_icon} {', '.join(ieee_parts)}"
        
        # === Tag für Citation-Scrolling ===
        # WICHTIG: Dieser Tag wird von _scroll_to_source() gesucht!
        source_entry_tag = f"source_entry_{cite_id}"
        
        # === Einfügen mit Tag ===
        source_start = self.text_widget.index(tk.END)
        self.text_widget.insert(tk.END, ieee_formatted, "source")
        source_end = self.text_widget.index(tk.END)
        
        # Füge source_entry Tag hinzu (für Citation-Klicks)
        self.text_widget.tag_add(source_entry_tag, source_start, source_end)
        
        # === Klickbar machen (wenn URL/File vorhanden) ===
        if url or source_file:
            # Unique Click-Tag
            click_tag = f"source_click_{cite_id}"
            self.text_widget.tag_add(click_tag, source_start, source_end)
            
            # Click-Handler
            if self.source_link_handler:
                target = url if url else source_file
                
                def create_click_handler(target_path):
                    def handler(e):
                        self.source_link_handler.open_source_link(target_path)
                    return handler
                
                self.text_widget.tag_bind(click_tag, "<Button-1>", create_click_handler(target))
                
                # Hover-Effects
                self.text_widget.tag_bind(click_tag, "<Enter>", lambda e: self.text_widget.config(cursor="hand2"))
                self.text_widget.tag_bind(click_tag, "<Leave>", lambda e: self.text_widget.config(cursor=""))
                
                # ✨ Hover-Tooltip mit Content-Preview
                if content_preview:
                    self._add_ieee_source_tooltip(click_tag, source_meta)
        
        self.text_widget.insert(tk.END, "\n")
        
        logger.debug(f"[IEEE-SOURCE] Inserted [{cite_id}] {title} ({doc_type})")
    
    def _add_ieee_source_tooltip(self, tag: str, source_meta: Dict[str, Any]) -> None:
        """
        ✨ v3.19.0: Fügt Hover-Tooltip für IEEE-Quelle hinzu
        
        Args:
            tag: Text-Widget Tag
            source_meta: SourceMetadata-Dict
        """
        title = source_meta.get('title', 'Unbekannt')
        content_preview = source_meta.get('content_preview', '')
        confidence = source_meta.get('confidence')
        
        # Tooltip-Text zusammenstellen
        tooltip_lines = [f"📖 {title}"]
        
        if confidence is not None:
            tooltip_lines.append(f"🎯 Confidence: {confidence:.0%}")
        
        if content_preview:
            # Begrenze Vorschau auf 200 Zeichen
            preview = content_preview[:200]
            if len(content_preview) > 200:
                preview += "..."
            tooltip_lines.append(f"\n💬 Vorschau:\n{preview}")
        
        tooltip_text = "\n".join(tooltip_lines)
        
        # Tooltip Event-Handler
        tooltip_window = None
        
        def show_tooltip(event):
            nonlocal tooltip_window
            if tooltip_window:
                return
            
            x = event.x_root + 10
            y = event.y_root + 10
            
            tooltip_window = tk.Toplevel(self.parent_window)
            tooltip_window.wm_overrideredirect(True)
            tooltip_window.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(
                tooltip_window,
                text=tooltip_text,
                background="#FFFFCC",
                relief=tk.SOLID,
                borderwidth=1,
                font=('Segoe UI', 9),
                justify=tk.LEFT,
                padx=5,
                pady=5
            )
            label.pack()
        
        def hide_tooltip(event):
            nonlocal tooltip_window
            if tooltip_window:
                tooltip_window.destroy()
                tooltip_window = None
        
        self.text_widget.tag_bind(tag, "<Enter>", show_tooltip)
        self.text_widget.tag_bind(tag, "<Leave>", hide_tooltip)
    
    def _setup_collapsible_toggle(
        self, 
        header_start: str, 
        header_end: str, 
        content_start: str, 
        content_end: str
    ) -> None:
        """
        Richtet Toggle-Handler für ausklappbare Details ein
        
        Args:
            header_start: Start-Index des Headers
            header_end: End-Index des Headers
            content_start: Start-Index des Contents
            content_end: End-Index des Contents
        """
        # Initial verstecken
        self.text_widget.tag_add("hidden_details", content_start, content_end)
        self.text_widget.tag_configure("hidden_details", elide=True)
        
        # Animation-State
        animation_in_progress = {'value': False}
        
        # Toggle-Handler
        def toggle_details(event=None):
            if animation_in_progress['value']:
                return
            
            is_hidden = self.text_widget.tag_cget("hidden_details", "elide") == "1"
            
            if is_hidden:
                self._expand_details(header_start, header_end, content_start, content_end, animation_in_progress)
            else:
                self._collapse_details(header_start, header_end, animation_in_progress)
        
        # Bind Click-Event
        self.text_widget.tag_bind("clickable", "<Button-1>", toggle_details)
        # Cursor über Events
        self.text_widget.tag_bind("clickable", "<Enter>", lambda e: self.text_widget.config(cursor="hand2"))
        self.text_widget.tag_bind("clickable", "<Leave>", lambda e: self.text_widget.config(cursor=""))
    
    def _expand_details(
        self, 
        header_start: str, 
        header_end: str, 
        content_start: str, 
        content_end: str, 
        animation_state: Dict
    ) -> None:
        """Animierte Expansion der Details"""
        animation_state['value'] = True
        
        # Update Header sofort
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(header_start, header_end)
        self.text_widget.insert(header_start, "Details verbergen", "clickable")
        arrow_pos = f"{header_start} - 3c"
        self.text_widget.delete(arrow_pos, f"{arrow_pos} + 2c")
        self.text_widget.insert(arrow_pos, "▼️ ", "clickable")
        self.text_widget.config(state=tk.DISABLED)
        
        # Animierte Einblendung
        content_lines = self.text_widget.get(content_start, content_end).split('\n')
        total_lines = len(content_lines)
        
        def reveal_line(line_index=0):
            if line_index < total_lines:
                progress = (line_index + 1) / total_lines
                
                if progress >= 0.3:
                    self.text_widget.tag_configure("hidden_details", elide=False)
                    animation_state['value'] = False
                    
                    # Scroll zu Details
                    if self.parent_window:
                        self.parent_window.after(100, lambda: self.text_widget.see(content_end))
                else:
                    if self.parent_window:
                        self.parent_window.after(20, lambda: reveal_line(line_index + 1))
            else:
                self.text_widget.tag_configure("hidden_details", elide=False)
                animation_state['value'] = False
        
        # Starte Animation
        if self.parent_window:
            self.parent_window.after(50, reveal_line)
        else:
            self.text_widget.tag_configure("hidden_details", elide=False)
            animation_state['value'] = False
    
    def _collapse_details(self, header_start: str, header_end: str, animation_state: Dict) -> None:
        """Animierte Collapse der Details"""
        animation_state['value'] = True
        
        # Update Header sofort
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(header_start, header_end)
        self.text_widget.insert(header_start, "Details anzeigen", "clickable")
        arrow_pos = f"{header_start} - 3c"
        self.text_widget.delete(arrow_pos, f"{arrow_pos} + 2c")
        self.text_widget.insert(arrow_pos, "▶️ ", "clickable")
        self.text_widget.config(state=tk.DISABLED)
        
        # Animierte Ausblendung
        def collapse_step(step=0):
            if step < 3:
                if self.parent_window:
                    self.parent_window.after(30, lambda: collapse_step(step + 1))
            else:
                self.text_widget.tag_configure("hidden_details", elide=True)
                animation_state['value'] = False
        
        # Starte Animation
        if self.parent_window:
            self.parent_window.after(20, collapse_step)
        else:
            self.text_widget.tag_configure("hidden_details", elide=True)
            animation_state['value'] = False
    
    # ✨ v3.16.0: Typing Indicator für Assistant-Antworten
    
    def show_typing_indicator(self) -> str:
        """
        Zeigt animierten Typing Indicator während Assistant antwortet
        
        Returns:
            Mark-ID für späteren Zugriff zum Entfernen
        """
        self.text_widget.config(state='normal')
        
        # Füge Typing Indicator hinzu
        mark_id = f"typing_{int(datetime.now().timestamp() * 1000)}"
        self.text_widget.mark_set(mark_id, tk.END)
        
        self.text_widget.insert(tk.END, "💭 VERITAS denkt nach", "typing_indicator")
        self.text_widget.insert(tk.END, ".", "typing_indicator")
        
        self.text_widget.config(state='disabled')
        self.text_widget.see(tk.END)
        
        # Starte Animation
        self._animate_typing_indicator(mark_id, dots=1)
        
        logger.debug(f"Typing indicator gestartet: {mark_id}")
        return mark_id
    
    def hide_typing_indicator(self, mark_id: str):
        """
        Entfernt Typing Indicator
        
        Args:
            mark_id: Mark-ID vom show_typing_indicator() Return
        """
        try:
            if not mark_id:
                return
            
            self.text_widget.config(state='normal')
            
            # Hole Position der Mark
            try:
                mark_pos = self.text_widget.index(mark_id)
                # Lösche bis Ende der Zeile
                self.text_widget.delete(mark_pos, f"{mark_pos} lineend")
                self.text_widget.delete(mark_pos, f"{mark_pos} +1c")  # Newline
                self.text_widget.mark_unset(mark_id)
                logger.debug(f"Typing indicator entfernt: {mark_id}")
            except tk.TclError:
                # Mark existiert nicht mehr
                pass
            
            self.text_widget.config(state='disabled')
            
        except Exception as e:
            logger.debug(f"Fehler beim Entfernen des Typing Indicators: {e}")
    
    def _animate_typing_indicator(self, mark_id: str, dots: int = 1):
        """
        Animiert Typing Indicator (1-3 Punkte oszillierend)
        
        Args:
            mark_id: Mark-ID des Indicators
            dots: Aktuelle Anzahl Punkte (1-3)
        """
        try:
            # Prüfe ob Mark noch existiert
            if mark_id not in self.text_widget.mark_names():
                return
            
            mark_pos = self.text_widget.index(mark_id)
            
            # Update Punkte
            self.text_widget.config(state='normal')
            # Lösche alte Punkte
            self.text_widget.delete(f"{mark_pos} lineend -4c", f"{mark_pos} lineend")
            # Füge neue Punkte ein
            new_dots = "." * dots
            self.text_widget.insert(f"{mark_pos} lineend", new_dots, "typing_indicator")
            self.text_widget.config(state='disabled')
            
            # Nächster Schritt
            next_dots = (dots % 3) + 1
            
            # Wiederhole nach 500ms
            if self.parent_window:
                self.parent_window.after(500, lambda: self._animate_typing_indicator(mark_id, next_dots))
                
        except Exception as e:
            logger.debug(f"Fehler bei Typing-Indicator-Animation: {e}")
    
    # ✨ v3.16.0: Copy-Button für Messages
    
    def add_copy_button_to_message(self, message_start: str, message_end: str, content: str, message_id: str = None):
        """
        Fügt dezenten Copy-Button rechts oben an einer Message hinzu
        
        Args:
            message_start: Start-Index der Message (z.B. "5.0")
            message_end: End-Index der Message (z.B. "8.0")
            content: Message-Content zum Kopieren
            message_id: Optionale Message-ID für Tracking
        """
        try:
            # Erstelle einzigartigen Tag für diese Message
            msg_tag = f"msg_copy_{message_id or int(datetime.now().timestamp() * 1000)}"
            
            # Füge Tag zur Message hinzu
            self.text_widget.tag_add(msg_tag, message_start, message_end)
            
            # Erstelle Copy-Button als eingebettetes Label
            copy_btn = tk.Label(
                self.text_widget,
                text="📋",
                font=('Segoe UI', 10),
                cursor='hand2',
                bg=self.text_widget.cget('bg'),
                fg='#9E9E9E',  # Grau (dezent)
                padx=3,
                pady=1
            )
            
            # Click-Handler
            def on_copy(event=None):
                try:
                    import pyperclip
                    pyperclip.copy(content)
                    # Visual Feedback
                    copy_btn.configure(text="✓", fg='#4CAF50')  # Grünes Checkmark
                    if self.parent_window:
                        self.parent_window.after(1500, lambda: copy_btn.configure(text="📋", fg='#9E9E9E'))
                    logger.debug(f"Message kopiert (ID: {message_id})")
                except ImportError:
                    # Fallback ohne pyperclip
                    self.text_widget.clipboard_clear()
                    self.text_widget.clipboard_append(content)
                    copy_btn.configure(text="✓", fg='#4CAF50')
                    if self.parent_window:
                        self.parent_window.after(1500, lambda: copy_btn.configure(text="📋", fg='#9E9E9E'))
                except Exception as e:
                    logger.error(f"Fehler beim Kopieren: {e}")
                    copy_btn.configure(text="❌", fg='#F44336')
            
            copy_btn.bind('<Button-1>', on_copy)
            
            # Hover-Effekt
            def on_enter(e):
                copy_btn.configure(fg='#0066CC')  # Blau bei Hover
            def on_leave(e):
                if copy_btn.cget('text') == "📋":
                    copy_btn.configure(fg='#9E9E9E')
            
            copy_btn.bind('<Enter>', on_enter)
            copy_btn.bind('<Leave>', on_leave)
            
            # Füge Button rechts oben in die Message ein
            self.text_widget.window_create(message_start, window=copy_btn, align='right')
            
            logger.debug(f"Copy-Button hinzugefügt für Message: {message_id}")
            
        except Exception as e:
            logger.debug(f"Fehler beim Hinzufügen des Copy-Buttons: {e}")


# Convenience-Funktionen
def setup_chat_tags(text_widget: tk.Text) -> None:
    """
    Konfiguriert Standard-Tags für Chat-Display
    
    Args:
        text_widget: Tkinter Text Widget
    """
    # Timestamp
    text_widget.tag_configure("timestamp", 
                             font=('Segoe UI', 8), 
                             foreground='#999')
    
    # User
    text_widget.tag_configure("user", 
                             font=('Segoe UI', 10), 
                             foreground='#2980b9')
    
    # Assistant
    text_widget.tag_configure("assistant", 
                             font=('Segoe UI', 10), 
                             foreground='#27ae60')
    text_widget.tag_configure("assistant_main", 
                             font=('Segoe UI', 10), 
                             foreground='#000')
    
    # System
    text_widget.tag_configure("system", 
                             font=('Segoe UI', 9, 'italic'), 
                             foreground='#95a5a6')
    
    # Header
    text_widget.tag_configure("header", 
                             font=('Segoe UI', 10, 'bold'), 
                             foreground='#34495e')
    
    # Metadata
    text_widget.tag_configure("metadata", 
                             font=('Segoe UI', 9), 
                             foreground='#7f8c8d')
    
    # Confidence
    text_widget.tag_configure("confidence_high", 
                             font=('Segoe UI', 9, 'bold'), 
                             foreground='#27ae60')
    text_widget.tag_configure("confidence_med", 
                             font=('Segoe UI', 9), 
                             foreground='#f39c12')
    text_widget.tag_configure("confidence_low", 
                             font=('Segoe UI', 9), 
                             foreground='#e74c3c')
    
    # ✨ Feature #12: Confidence-Badges mit Background-Colors
    text_widget.tag_configure("confidence_badge_high", 
                             font=('Segoe UI', 8, 'bold'), 
                             foreground='#ffffff',
                             background='#27ae60')  # Grün
    text_widget.tag_configure("confidence_badge_med", 
                             font=('Segoe UI', 8, 'bold'), 
                             foreground='#ffffff',
                             background='#f39c12')  # Orange
    text_widget.tag_configure("confidence_badge_low", 
                             font=('Segoe UI', 8, 'bold'), 
                             foreground='#ffffff',
                             background='#e74c3c')  # Rot
    
    # Source
    text_widget.tag_configure("source", 
                             font=('Segoe UI', 9), 
                             foreground='#555')
    
    # Agent
    text_widget.tag_configure("agent", 
                             font=('Segoe UI', 9, 'bold'), 
                             foreground='#8e44ad')
    
    # Clickable
    text_widget.tag_configure("clickable", 
                             font=('Segoe UI', 10, 'bold'), 
                             foreground='#3498db')
    text_widget.tag_configure("clickable_link", 
                             font=('Segoe UI', 9), 
                             foreground='#3498db', 
                             underline=True)
    
    # Collapsed
    text_widget.tag_configure("collapsed", 
                             font=('Segoe UI', 9), 
                             foreground='#95a5a6')
    
    # ✨ NEW: Sprechblasen-Design (Tag-basiert, KEIN Canvas)
    # User-Message Bubble (rechtsbündig)
    text_widget.tag_configure("user_bubble", 
                             background='#E3F2FD',       # Hellblau
                             relief='solid', 
                             borderwidth=1,
                             lmargin1=150,               # Rechtsbündig (linker Margin)
                             lmargin2=150,               # Einzug für mehrzeiligen Text
                             rmargin=10,                 # Rechter Rand
                             spacing1=8,                 # Padding oben
                             spacing3=8,                 # Padding unten
                             font=('Segoe UI', 10))
    
    # User-Metadata (Attachments + Timestamp oberhalb Bubble)
    text_widget.tag_configure("user_metadata", 
                             font=('Segoe UI', 8), 
                             foreground='#666',
                             lmargin1=150,               # Rechtsbündig wie Bubble
                             spacing3=2)                 # Kleiner Abstand zur Bubble
    
    # Assistant-Message Bubble (linksbündig)
    text_widget.tag_configure("assistant_bubble", 
                             background='#F5F5F5',       # Hellgrau
                             relief='flat',              # Kein Rahmen für Assistant
                             lmargin1=10,                # Linksbündig
                             lmargin2=10,
                             rmargin=150,                # Rechter Margin (Platz für User-Bubbles)
                             spacing1=8,
                             spacing3=8,
                             font=('Segoe UI', 10))
    
    # Message-Separator
    text_widget.tag_configure("message_separator", 
                             spacing1=10,                # Abstand zwischen Messages
                             spacing3=10)
    
    # Attachment-Link (klickbar)
    text_widget.tag_configure("attachment_link", 
                             font=('Segoe UI', 8), 
                             foreground='#0066CC', 
                             underline=True)
    
    # Metriken-Compact (Inline horizontal)
    text_widget.tag_configure("metrics_compact", 
                             font=('Segoe UI', 8), 
                             foreground='#666',
                             spacing1=2,
                             spacing3=5)
    
    # Processing-Placeholder (pulsierend)
    text_widget.tag_configure("processing_placeholder", 
                             font=('Segoe UI', 10, 'italic'), 
                             foreground='#999')
    
    # === RAW RESPONSE TAGS (Debug-View) ===
    text_widget.tag_configure("raw_header", 
                             font=('Segoe UI', 9, 'bold'), 
                             foreground='#555')
    
    text_widget.tag_configure("raw_param", 
                             font=('Courier New', 8), 
                             foreground='#666',
                             lmargin1=20)
    
    text_widget.tag_configure("raw_content", 
                             font=('Courier New', 8), 
                             foreground='#333',
                             background='#FAFAFA',
                             lmargin1=20,
                             wrap='word')
    
    text_widget.tag_configure("raw_separator", 
                             font=('Courier New', 8), 
                             foreground='#CCC')
    
    # ✨ v3.19.0: Suggestion-Link Tags (klickbare Follow-up-Fragen)
    text_widget.tag_configure("suggestion_prefix",
                             font=('Segoe UI', 9),
                             foreground='#666')
    
    text_widget.tag_configure("suggestion_link",
                             font=('Segoe UI', 9, 'bold'),
                             foreground='#0066CC',  # Blau (Link-Farbe)
                             spacing1=2,
                             spacing3=2)
    
    text_widget.tag_configure("raw_warning", 
                             font=('Segoe UI', 8), 
                             foreground='#FF6600',
                             lmargin1=20)
    
    text_widget.tag_configure("raw_tip", 
                             font=('Segoe UI', 8, 'italic'), 
                             foreground='#0066CC',
                             lmargin1=20)
    
    # ✨ v3.16.0: Typing Indicator Tag
    text_widget.tag_configure("typing_indicator",
                             font=('Segoe UI', 10),
                             foreground='#9E9E9E',
                             spacing1=5,
                             spacing3=5)
    
    logger.info("✅ Chat-Tags konfiguriert (inkl. Sprechblasen-Design + Raw-Response)")
