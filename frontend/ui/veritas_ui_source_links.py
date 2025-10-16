#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS UI Module: Source Link Handler
Verantwortlich für klickbare Quellen-Links und Vorschau-Dialogs
"""

import tkinter as tk
from tkinter import scrolledtext, ttk
import os
import sys
import webbrowser
import logging
import requests
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# API Base URL für Backend-Requests
try:
    from config import Config
    API_BASE_URL = Config().API_BASE_URL
except ImportError:
    API_BASE_URL = "http://127.0.0.1:5000"


class SourceLinkHandler:
    """
    Handler für klickbare Quellen-Links in VERITAS Chat
    Unterstützt: URLs, lokale Dateien, Datenbank-Quellen
    """
    
    def __init__(self, parent_window: tk.Tk = None, status_var: tk.StringVar = None):
        """
        Initialisiert den Source Link Handler
        
        Args:
            parent_window: Hauptfenster für Dialogs
            status_var: StringVar für Status-Feedback
        """
        self.parent_window = parent_window
        self.status_var = status_var
    
    def open_source_link(self, link: str) -> None:
        """
        Öffnet einen Quellen-Link (URL, Datei oder DB-Quelle)
        
        Args:
            link: URL, Dateipfad oder Quellen-ID
        """
        try:
            # === URL ===
            if link.startswith(('http://', 'https://', 'www.')):
                self._open_url(link)
            
            # === LOKALE DATEI ===
            elif os.path.exists(link):
                self._open_file(link)
            
            # === DATENBANK-QUELLE ===
            else:
                self.show_source_preview(link)
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen des Links: {e}")
            self._set_status(f"❌ Fehler: {str(e)[:50]}...")
    
    def _open_url(self, url: str) -> None:
        """Öffnet URL im Standard-Browser"""
        # Stelle sicher dass URL mit http/https beginnt
        full_url = url if url.startswith('http') else f'http://{url}'
        
        webbrowser.open(full_url)
        logger.info(f"🔗 URL geöffnet: {full_url}")
        
        # Visuelles Feedback
        self._set_status(f"🔗 Link geöffnet: {url[:50]}...", timeout=3000)
    
    def _open_file(self, filepath: str) -> None:
        """Öffnet lokale Datei mit Standard-Programm"""
        if sys.platform == 'win32':
            os.startfile(filepath)
        elif sys.platform == 'darwin':
            os.system(f'open "{filepath}"')
        else:
            os.system(f'xdg-open "{filepath}"')
        
        logger.info(f"📄 Datei geöffnet: {filepath}")
        
        # Visuelles Feedback
        basename = os.path.basename(filepath)
        self._set_status(f"📄 Datei geöffnet: {basename}", timeout=3000)
    
    def _set_status(self, message: str, timeout: int = None) -> None:
        """Setzt Status-Nachricht mit optionalem Timeout"""
        if not self.status_var:
            return
        
        original_status = self.status_var.get()
        self.status_var.set(message)
        
        # Nach Timeout zurücksetzen
        if timeout and self.parent_window:
            self.parent_window.after(timeout, lambda: self.status_var.set(original_status))
    
    def show_source_preview(self, source_name: str) -> None:
        """
        Zeigt Vorschau-Dialog für Datenbank-Quelle
        
        Args:
            source_name: Name/ID der Quelle
        """
        try:
            # Dialog erstellen
            dialog = tk.Toplevel(self.parent_window if self.parent_window else None)
            dialog.title(f"📄 Quelle: {source_name[:50]}")
            dialog.geometry("600x400")
            dialog.resizable(True, True)
            
            if self.parent_window:
                dialog.transient(self.parent_window)
                dialog.grab_set()
            
            # Header
            header_frame = ttk.Frame(dialog)
            header_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(
                header_frame, 
                text="📄 Quellen-Information", 
                font=('Segoe UI', 12, 'bold')
            ).pack(anchor=tk.W)
            
            ttk.Label(
                header_frame, 
                text=source_name, 
                font=('Segoe UI', 9), 
                foreground='#666'
            ).pack(anchor=tk.W)
            
            # Info-Text
            info_text = scrolledtext.ScrolledText(
                dialog,
                wrap=tk.WORD,
                font=('Segoe UI', 10),
                bg='#f9f9f9',
                fg='#333'
            )
            info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
            
            # Quellen-Details
            info_content = self._get_source_info(source_name)
            info_text.insert('1.0', info_content)
            info_text.config(state=tk.DISABLED)
            
            # Schließen-Button
            ttk.Button(
                dialog, 
                text="Schließen", 
                command=dialog.destroy
            ).pack(pady=(0, 10))
            
            # Zentriere Dialog
            self._center_dialog(dialog, 600, 400)
            
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen der Quellen-Vorschau: {e}")
    
    def _get_source_info(self, source_name: str) -> str:
        """Erstellt Info-Text für Quellen-Vorschau"""
        return f"""Quelle: {source_name}

Diese Quelle ist im VERITAS-System gespeichert.

Mögliche Aktionen:
• Fragen Sie nach dem vollständigen Dokument
• Verwenden Sie die Dokumenten-ID in weiteren Anfragen
• Kontaktieren Sie den Administrator für Zugriff

Hinweis: Die Datei konnte nicht lokal gefunden werden.
Sie ist vermutlich in der Datenbank gespeichert.

Weitere Informationen könnten über das Backend abgerufen werden."""
    
    def _center_dialog(self, dialog: tk.Toplevel, width: int, height: int) -> None:
        """Zentriert Dialog auf dem Bildschirm"""
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_hover_tooltip(
        self, 
        widget: tk.Widget, 
        source_name: str,
        preview_text: str = None,
        metadata: Dict[str, Any] = None
    ) -> 'SourceTooltip':
        """
        Erstellt Hover-Tooltip für Widget mit Rich Preview
        
        Args:
            widget: Widget für Tooltip
            source_name: Name der Quelle
            preview_text: Vorschau-Text (optional, wird automatisch geladen)
            metadata: Metadaten (confidence, page, type, etc.)
            
        Returns:
            SourceTooltip-Instanz
        """
        return SourceTooltip(
            widget=widget,
            source_name=source_name,
            preview_text=preview_text,
            metadata=metadata,
            fetch_snippet=True  # Automatisch Snippet vom Backend laden
        )


class SourceTooltip:
    """
    Tooltip für Quellen-Vorschau bei Hover
    Zeigt Snippet, Metadaten und Relevanz-Score
    """
    
    def __init__(
        self, 
        widget: tk.Widget, 
        source_name: str, 
        preview_text: str = None,
        metadata: Dict[str, Any] = None,
        fetch_snippet: bool = True
    ):
        """
        Initialisiert Source-Tooltip mit Rich Preview
        
        Args:
            widget: Widget für Tooltip
            source_name: Name der Quelle
            preview_text: Vorschau-Text (optional, wird aus Backend geladen wenn nicht vorhanden)
            metadata: Metadaten (confidence, page, etc.)
            fetch_snippet: Snippet vom Backend laden wenn preview_text fehlt
        """
        self.widget = widget
        self.source_name = source_name
        self.preview_text = preview_text
        self.metadata = metadata or {}
        self.tooltip_window = None
        self.fetch_snippet = fetch_snippet
        
        # Lade Snippet falls nötig
        if not self.preview_text and self.fetch_snippet:
            self._load_snippet_async()
        
        # Bindings
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)
    
    def _load_snippet_async(self) -> None:
        """Lädt Snippet vom Backend (asynchron)"""
        import threading
        
        def fetch():
            try:
                snippet = self._fetch_source_snippet(self.source_name)
                if snippet:
                    self.preview_text = snippet
            except Exception as e:
                logger.debug(f"Snippet-Fetch fehlgeschlagen: {e}")
        
        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()
    
    def _fetch_source_snippet(self, source_id: str) -> Optional[str]:
        """
        Holt Textausschnitt für Quelle vom Backend
        
        Args:
            source_id: ID oder Name der Quelle
            
        Returns:
            Snippet-Text oder None
        """
        try:
            # Versuche Snippet vom Backend zu holen
            response = requests.post(
                f"{API_BASE_URL}/database/get_snippet",
                json={"source_id": source_id, "max_length": 300},
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                snippet = data.get('snippet', '')
                
                # Update Metadaten wenn vorhanden
                if 'metadata' in data:
                    self.metadata.update(data['metadata'])
                
                return snippet
            else:
                logger.debug(f"Backend-Snippet-Fetch fehlgeschlagen: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.debug("Snippet-Request Timeout")
            return None
        except Exception as e:
            logger.debug(f"Fehler beim Snippet-Fetch: {e}")
            return None
    
    def show_tooltip(self, event=None) -> None:
        """Zeigt Rich Tooltip mit Snippet und Metadaten"""
        if self.tooltip_window:
            return
        
        # Fallback wenn kein Preview-Text
        if not self.preview_text:
            self.preview_text = "Vorschau wird geladen..."
        
        # Position berechnen (mit Offset für bessere Sichtbarkeit)
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        
        # Tooltip-Fenster erstellen
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Rahmen mit Schatten-Effekt
        frame = tk.Frame(
            tw, 
            background="#2c3e50", 
            borderwidth=2, 
            relief="solid",
            padx=1,
            pady=1
        )
        frame.pack()
        
        # Inner Frame für Content
        inner_frame = tk.Frame(frame, background="#34495e")
        inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # === HEADER ===
        header_label = tk.Label(
            inner_frame,
            text=f"📄 {self._truncate(self.source_name, 50)}",
            font=('Segoe UI', 9, 'bold'),
            background="#2c3e50",
            foreground="#ecf0f1",
            padx=10,
            pady=6
        )
        header_label.pack(fill=tk.X)
        
        # === METADATEN ===
        if self.metadata:
            meta_frame = tk.Frame(inner_frame, background="#34495e")
            meta_frame.pack(fill=tk.X, padx=8, pady=(4, 2))
            
            # Confidence Score
            if 'confidence' in self.metadata:
                confidence = self.metadata['confidence']
                color = self._get_confidence_color(confidence)
                conf_label = tk.Label(
                    meta_frame,
                    text=f"⭐ {confidence:.0%}",
                    font=('Segoe UI', 8, 'bold'),
                    background="#34495e",
                    foreground=color,
                    padx=4
                )
                conf_label.pack(side=tk.LEFT)
            
            # Seiten-Nummer
            if 'page' in self.metadata:
                page_label = tk.Label(
                    meta_frame,
                    text=f"📑 S. {self.metadata['page']}",
                    font=('Segoe UI', 8),
                    background="#34495e",
                    foreground="#95a5a6",
                    padx=4
                )
                page_label.pack(side=tk.LEFT)
            
            # Dokumenttyp
            if 'type' in self.metadata:
                type_label = tk.Label(
                    meta_frame,
                    text=f"📋 {self.metadata['type']}",
                    font=('Segoe UI', 8),
                    background="#34495e",
                    foreground="#95a5a6",
                    padx=4
                )
                type_label.pack(side=tk.LEFT)
        
        # === SEPARATOR ===
        separator = tk.Frame(inner_frame, height=1, background="#7f8c8d")
        separator.pack(fill=tk.X, padx=8, pady=4)
        
        # === VORSCHAU-TEXT ===
        preview = self._truncate(self.preview_text, 250)
        text_label = tk.Label(
            inner_frame,
            text=preview,
            font=('Segoe UI', 9),
            background="#34495e",
            foreground="#ecf0f1",
            justify=tk.LEFT,
            wraplength=350,
            padx=10,
            pady=8
        )
        text_label.pack(fill=tk.BOTH, expand=True)
        
        # === FOOTER (Klick-Hinweis) ===
        footer_label = tk.Label(
            inner_frame,
            text="💡 Klicken für Details",
            font=('Segoe UI', 7, 'italic'),
            background="#2c3e50",
            foreground="#95a5a6",
            padx=10,
            pady=4
        )
        footer_label.pack(fill=tk.X)
    
    def _truncate(self, text: str, max_length: int) -> str:
        """Kürzt Text intelligent (an Wortgrenzen)"""
        if len(text) <= max_length:
            return text
        
        # Suche letzte Wortgrenze vor max_length
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.7:  # Mindestens 70% des Texts
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."
    
    def _get_confidence_color(self, confidence: float) -> str:
        """Gibt Farbe basierend auf Confidence-Score zurück"""
        if confidence >= 0.8:
            return "#27ae60"  # Grün
        elif confidence >= 0.6:
            return "#f39c12"  # Orange
        else:
            return "#e74c3c"  # Rot
    
    def hide_tooltip(self, event=None) -> None:
        """Versteckt Tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


# Convenience-Funktionen
def create_clickable_source_link(
    text_widget: tk.Text,
    link_text: str,
    link_url: str,
    handler: SourceLinkHandler,
    tag_prefix: str = "source_link"
) -> str:
    """
    Erstellt einen klickbaren Quellen-Link im Text Widget
    
    Args:
        text_widget: Tkinter Text Widget
        link_text: Anzuzeigender Text
        link_url: URL/Pfad beim Klick
        handler: SourceLinkHandler-Instanz
        tag_prefix: Präfix für Tag-Namen
        
    Returns:
        Tag-Name des erstellten Links
    """
    # Erstelle unique Tag
    link_tag = f"{tag_prefix}_{hash(link_url)}"
    
    # Füge Text ein
    start = text_widget.index(tk.END)
    text_widget.insert(tk.END, link_text, "clickable_link")
    end = text_widget.index(tk.END)
    
    # Füge Tag hinzu
    text_widget.tag_add(link_tag, start, end)
    
    # Click-Handler
    text_widget.tag_bind(
        link_tag, 
        "<Button-1>", 
        lambda e: handler.open_source_link(link_url)
    )
    
    # Cursor-Style über Events
    text_widget.tag_bind(link_tag, "<Enter>", lambda e: text_widget.config(cursor="hand2"))
    text_widget.tag_bind(link_tag, "<Leave>", lambda e: text_widget.config(cursor=""))
    
    return link_tag
