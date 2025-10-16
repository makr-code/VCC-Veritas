"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "veritas_ui_statusbar"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...Pt1juA=="  # Gekuerzt fuer Sicherheit
module_organization_key = "59c32c658f6ca1292b90dee26f655bee2adec032d18aa486221e07c8836c8e29"
module_file_key = "8f43cd76b630056009df95235d56a7b88a1ae5d8e55706cda96e77165c65ea0b"
module_version = "1.0"
module_protection_level = 1
# === END PROTECTION KEYS ===
import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)


class ChatStatusBar(tk.Frame):
    """Einfache Statusleiste für Single-Chat-Windows."""
    
    def __init__(self, parent, app_version="3.1.0", **kwargs):
        """
        Initialisiert die StatusBar.
        
        Args:
            parent: Parent-Widget
            app_version: Aktuelle App-Version
        """
        super().__init__(parent, height=20, relief="sunken", bd=1, **kwargs)
        self.app_version = app_version
        self.pack_propagate(False)
        
        self._create_widgets()
        self.update_status("Bereit", "info")
        
    def _create_widgets(self):
        """Erstellt alle Statusbar-Widgets."""
        # Status-Text (ohne Icons, dezent)
        self.status_label = tk.Label(self, text="Bereit", 
                                    bd=0, relief="flat", anchor=tk.W,
                                    padx=10, pady=1)
        self.status_label.pack(side="left", fill="both", expand=True)
        
        # Rechter Bereich - Version (sehr dezent)
        right_frame = tk.Frame(self, bd=0)
        right_frame.pack(side="right", fill="y")
        
        # Version-Info (sehr klein und dezent)
        self.version_label = tk.Label(right_frame, text=f"v{self.app_version}", 
                                     bd=0, relief="flat", anchor=tk.E,
                                     padx=10, pady=2)
        self.version_label.pack(side="right")
        
    def update_status(self, message, status_type="info", show_version=False):
        
        # Label aktualisieren (nur Text, keine Icons)
        self.status_label.config(text=message)
        
        # Version anzeigen/verstecken
        if hasattr(self, 'version_label'):
            if show_version:
                self.version_label.pack(side="right")
            else:
                self.version_label.pack_forget()
            
        # UI aktualisieren
        self.update_idletasks()
        
        # Logging
        log_level = {
            "info": logging.INFO,
            "working": logging.INFO, 
            "error": logging.ERROR,
            "success": logging.INFO,
            "warning": logging.WARNING
        }.get(status_type, logging.INFO)
        
        logger.log(log_level, f"Status: {message}")
        
    def set_progress(self, message, progress=None):
        """
        Zeigt einen Fortschritt an (ohne Icons).
        
        Args:
            message: Fortschritts-Nachricht
            progress: Fortschritt in Prozent (optional)
        """
        if progress is not None:
            status_text = f"{message} ({progress}%)"
        else:
            status_text = f"{message}..."
            
        self.status_label.config(text=status_text, fg="blue")
        self.update_idletasks()
        
    def clear_status(self):
        """Setzt den Status auf Bereit zurück."""
        self.update_status("Bereit", "info")
        
    def show_temporary_message(self, message, status_type="info", duration=3000):
        """
        Zeigt eine temporäre Nachricht an.
        
        Args:
            message: Nachricht
            status_type: Status-Typ
            duration: Anzeigedauer in Millisekunden
        """
        # Aktuellen Status speichern
        current_text = self.status_label.cget("text")
        
        # Temporäre Nachricht anzeigen
        self.update_status(message, status_type)
        
        # Nach Ablauf der Zeit zurücksetzen
        def restore_status():
            self.status_label.config(text=current_text)
            
        self.after(duration, restore_status)
        
    def set_version(self, version):
        """
        Aktualisiert die Versionsnummer.
        
        Args:
            version: Neue Versionsnummer
        """
        self.app_version = version
        if hasattr(self, 'version_label'):
            self.version_label.config(text=f"v{version}")
        
    def get_current_status(self):
        """
        Gibt den aktuellen Status-Text zurück.
        
        Returns:
            str: Aktueller Status-Text (ohne Icon)
        """
        current_text = self.status_label.cget("text")
        # Da wir keine Icons mehr verwenden, geben wir den ganzen Text zurück
        return current_text
