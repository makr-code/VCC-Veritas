#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Frontend Component: Error Handler
Zentrale Fehlerbehandlung mit Retry-Logik und User-Feedback

Features:
- Error-Display mit visuellen Feedback
- Retry-Button für fehlgeschlagene Queries
- Typ-spezifische Fehlerbehandlung
- Queue-basierte Error-Messages
- Vollständige GUI-Integration

Version: 1.0.0
"""

import logging
import tkinter as tk
from typing import Dict, Callable, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Kategorien von Fehlern"""
    TIMEOUT = 'timeout'
    CONNECTION = 'connection'
    REQUEST = 'request'
    API_ERROR = 'api_error'
    CLIENT_ERROR = 'client_error'
    UNKNOWN = 'unknown'


@dataclass
class ErrorData:
    """Strukturierte Error-Daten"""
    message: str
    error_type: ErrorType
    original_query: str
    timestamp: str
    retryable: bool = True
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        """Konvertiert zu Dict für Queue-Messages"""
        return {
            'role': 'error',
            'content': self.message,
            'timestamp': self.timestamp,
            'original_query': self.original_query,
            'error_type': self.error_type.value,
            'retryable': self.retryable,
            'details': self.details or {}
        }


class ErrorHandler:
    """
    Zentrale Fehlerbehandlung für Chat-Windows
    
    Features:
    - display_error_with_retry(): Zeigt Fehler mit Retry-Button
    - render_error_box(): Rendert Error-Widget in Chat
    - retry_query(): Führt fehlgeschlagene Query erneut aus
    - dismiss_error(): Schließt Error-Widget
    
    Example:
        error_handler = ErrorHandler(
            chat_text=self.chat_text,
            window=self.window,
            retry_callback=self.send_chat_message,
            status_callback=lambda msg: self.status_var.set(msg)
        )
        
        error_handler.display_error_with_retry(
            error_message="Timeout",
            original_query="Was ist Python?",
            error_type=ErrorType.TIMEOUT
        )
    """
    
    def __init__(
        self,
        chat_text: tk.Text,
        window: tk.Tk,
        retry_callback: Callable[[str], None],
        status_callback: Optional[Callable[[str], None]] = None,
        error_queue_callback: Optional[Callable[[Dict], None]] = None
    ):
        """
        Initialisiert ErrorHandler
        
        Args:
            chat_text: Tkinter Text-Widget für Chat-Display
            window: Tkinter Window für after() Scheduling
            retry_callback: Callback für Retry (z.B. send_chat_message)
            status_callback: Optional Callback für Status-Updates
            error_queue_callback: Optional Callback für Queue-basierte Errors
        """
        self.chat_text = chat_text
        self.window = window
        self.retry_callback = retry_callback
        self.status_callback = status_callback
        self.error_queue_callback = error_queue_callback
        
        # Error-Historie
        self.error_history: list[ErrorData] = []
        
        logger.info("✅ ErrorHandler initialisiert")
    
    # === PUBLIC API ===
    
    def display_error_with_retry(
        self,
        error_message: str,
        original_query: str,
        error_type: ErrorType = ErrorType.UNKNOWN
    ):
        """
        Zeigt Fehler mit Retry-Button an
        
        Args:
            error_message: Fehlermeldung für User
            original_query: Ursprüngliche Query (für Retry)
            error_type: Art des Fehlers
        """
        try:
            # Create ErrorData
            error_data = ErrorData(
                message=error_message,
                error_type=error_type,
                original_query=original_query,
                timestamp=datetime.now().isoformat(),
                retryable=True
            )
            
            # Add to history
            self.error_history.append(error_data)
            
            # Queue-basierte Error-Message (optional)
            if self.error_queue_callback:
                self.error_queue_callback(error_data.to_dict())
            
            # Render in UI-Thread
            if self.window:
                self.window.after(0, lambda: self.render_error_box(error_data))
            
            logger.info(f"❌ Error angezeigt: {error_type.value}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anzeigen der Error-Message: {e}", exc_info=True)
    
    def render_error_box(self, error_data: ErrorData):
        """
        Rendert Error-Widget in Chat-Text
        
        Args:
            error_data: Error-Daten zum Rendern
        """
        try:
            if not self.chat_text:
                return
            
            self.chat_text.config(state='normal')
            
            # === ERROR-BOX FRAME ===
            error_frame = tk.Frame(
                self.chat_text,
                bg='#FFEBEE',  # Material Design Red 50
                relief=tk.SOLID,
                borderwidth=2,
                padx=15,
                pady=10
            )
            
            # Error-Icon
            error_icon = tk.Label(
                error_frame,
                text=self._get_error_icon(error_data.error_type),
                font=('Segoe UI', 16),
                bg='#FFEBEE',
                fg='#C62828'  # Material Design Red 800
            )
            error_icon.pack(side=tk.TOP, pady=(0, 5))
            
            # Error-Message
            error_text = tk.Label(
                error_frame,
                text=error_data.message,
                font=('Segoe UI', 10),
                bg='#FFEBEE',
                fg='#333333',
                wraplength=400,
                justify=tk.LEFT
            )
            error_text.pack(side=tk.TOP, pady=(0, 10))
            
            # === BUTTON-CONTAINER ===
            button_frame = tk.Frame(error_frame, bg='#FFEBEE')
            button_frame.pack(side=tk.TOP, fill=tk.X)
            
            # Retry-Button (nur wenn retryable)
            if error_data.retryable:
                retry_btn = tk.Button(
                    button_frame,
                    text="🔄 Erneut versuchen",
                    font=('Segoe UI', 9, 'bold'),
                    bg='#F57C00',  # Material Design Orange 700
                    fg='white',
                    activebackground='#E65100',  # Orange 900
                    activeforeground='white',
                    cursor='hand2',
                    relief=tk.RAISED,
                    borderwidth=1,
                    padx=15,
                    pady=5,
                    command=lambda: self._on_retry_clicked(error_data, error_frame)
                )
                retry_btn.pack(side=tk.LEFT, padx=(0, 5))
                
                # Hover-Effekt
                retry_btn.bind('<Enter>', lambda e: retry_btn.config(bg='#E65100'))
                retry_btn.bind('<Leave>', lambda e: retry_btn.config(bg='#F57C00'))
            
            # Dismiss-Button
            dismiss_btn = tk.Button(
                button_frame,
                text="✕ Schließen",
                font=('Segoe UI', 9),
                bg='#BDBDBD',  # Material Design Grey 400
                fg='#333333',
                activebackground='#9E9E9E',  # Grey 500
                cursor='hand2',
                relief=tk.RAISED,
                borderwidth=1,
                padx=15,
                pady=5,
                command=lambda: self.dismiss_error(error_frame)
            )
            dismiss_btn.pack(side=tk.LEFT)
            
            # Hover-Effekt
            dismiss_btn.bind('<Enter>', lambda e: dismiss_btn.config(bg='#9E9E9E'))
            dismiss_btn.bind('<Leave>', lambda e: dismiss_btn.config(bg='#BDBDBD'))
            
            # === INSERT IN CHAT ===
            self.chat_text.window_create(tk.END, window=error_frame)
            self.chat_text.insert(tk.END, "\n\n")
            
            self.chat_text.config(state='disabled')
            self.chat_text.see(tk.END)
            
            logger.debug("✅ Error-Widget gerendert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Rendern der Error-Box: {e}", exc_info=True)
    
    def retry_query(self, error_data: ErrorData):
        """
        Führt fehlgeschlagene Query erneut aus
        
        Args:
            error_data: Error-Daten mit original_query
        """
        try:
            if not error_data.original_query:
                logger.warning("⚠️ Keine original_query für Retry")
                return
            
            logger.info(f"🔄 Retry Query: {error_data.original_query[:50]}...")
            
            # Status-Update
            if self.status_callback:
                self.status_callback("🔄 Erneuter Versuch...")
            
            # Execute Retry
            self.retry_callback(error_data.original_query)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Retry: {e}", exc_info=True)
    
    def dismiss_error(self, error_frame: tk.Frame):
        """
        Schließt Error-Widget
        
        Args:
            error_frame: Frame-Widget zum Entfernen
        """
        try:
            error_frame.destroy()
            logger.debug("✅ Error-Widget geschlossen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Schließen: {e}")
    
    def get_error_history(self) -> list[ErrorData]:
        """Gibt Error-Historie zurück"""
        return self.error_history.copy()
    
    def clear_error_history(self):
        """Löscht Error-Historie"""
        self.error_history.clear()
        logger.info("🗑️ Error-Historie gelöscht")
    
    # === PRIVATE HELPERS ===
    
    def _on_retry_clicked(self, error_data: ErrorData, error_frame: tk.Frame):
        """Handler für Retry-Button-Click"""
        # Close error box
        self.dismiss_error(error_frame)
        
        # Execute retry
        self.retry_query(error_data)
    
    def _get_error_icon(self, error_type: ErrorType) -> str:
        """
        Gibt passendes Icon für Error-Type zurück
        
        Args:
            error_type: Typ des Fehlers
            
        Returns:
            Unicode-Icon
        """
        icons = {
            ErrorType.TIMEOUT: "⏱️",
            ErrorType.CONNECTION: "🔌",
            ErrorType.REQUEST: "📡",
            ErrorType.API_ERROR: "⚠️",
            ErrorType.CLIENT_ERROR: "🔧",
            ErrorType.UNKNOWN: "❌"
        }
        return icons.get(error_type, "❌")
    
    def __repr__(self) -> str:
        return f"ErrorHandler(errors={len(self.error_history)})"


# === CONVENIENCE FUNCTIONS ===

def create_error_handler(
    chat_text: tk.Text,
    window: tk.Tk,
    retry_callback: Callable[[str], None],
    **kwargs
) -> ErrorHandler:
    """
    Factory-Funktion für ErrorHandler
    
    Args:
        chat_text: Chat-Text-Widget
        window: Tkinter Window
        retry_callback: Retry-Callback
        **kwargs: Weitere ErrorHandler-Parameter
        
    Returns:
        Initialisierter ErrorHandler
    """
    return ErrorHandler(
        chat_text=chat_text,
        window=window,
        retry_callback=retry_callback,
        **kwargs
    )
