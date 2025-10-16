"""
VERITAS Session Restore Dialog
==============================

Dialog zum Wiederherstellen der letzten Chat-Session beim Start.

Features:
- Liste der letzten 10 Sessions
- Vorschau: Titel, Datum, Nachrichtenanzahl
- Buttons: Wiederherstellen, Neu starten
- Settings: "Immer letzte Session laden" (Auto-Restore)

Version: v3.20.0
Author: VERITAS Team
Date: 12. Oktober 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class SessionRestoreDialog:
    """Dialog zum Wiederherstellen von Chat-Sessions"""
    
    def __init__(self, parent, chat_persistence_service):
        """
        Initialisiert Session-Restore-Dialog
        
        Args:
            parent: Parent-Window (Tkinter)
            chat_persistence_service: ChatPersistenceService-Instanz
        """
        self.parent = parent
        self.service = chat_persistence_service
        self.result = None  # Session-ID oder None
        self.auto_restore_enabled = False
        
        # Lade Settings
        self._load_settings()
        
        # Dialog erstellen
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("💬 Session wiederherstellen")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        
        # Modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Zentriere Dialog
        self._center_dialog()
        
        # UI erstellen
        self._create_ui()
        
        # Lade Sessions
        self._load_sessions()
        
        logger.info("Session-Restore-Dialog geöffnet")
    
    def _load_settings(self):
        """Lädt Dialog-Settings aus Datei"""
        try:
            settings_file = os.path.join("data", "session_restore_settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.auto_restore_enabled = settings.get('auto_restore', False)
        except Exception as e:
            logger.warning(f"Konnte Settings nicht laden: {e}")
            self.auto_restore_enabled = False
    
    def _save_settings(self):
        """Speichert Dialog-Settings"""
        try:
            settings_file = os.path.join("data", "session_restore_settings.json")
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            
            settings = {
                'auto_restore': self.auto_restore_enabled
            }
            
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            logger.warning(f"Konnte Settings nicht speichern: {e}")
    
    def _center_dialog(self):
        """Zentriert Dialog auf Bildschirm"""
        self.dialog.update_idletasks()
        
        # Berechne Position
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_ui(self):
        """Erstellt Dialog-UI"""
        # Header
        header_frame = tk.Frame(self.dialog, bg='#2E86AB', height=60)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(
            header_frame,
            text="💬 Letzte Session wiederherstellen?",
            font=('Segoe UI', 14, 'bold'),
            bg='#2E86AB',
            fg='white'
        )
        header_label.pack(pady=15)
        
        # Info-Text
        info_frame = tk.Frame(self.dialog, bg='#F8F9FA')
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        info_label = tk.Label(
            info_frame,
            text="Wählen Sie eine Session zum Wiederherstellen oder starten Sie einen neuen Chat.",
            font=('Segoe UI', 9),
            bg='#F8F9FA',
            fg='#343A40',
            wraplength=550,
            justify=tk.LEFT
        )
        info_label.pack(pady=5)
        
        # Sessions-Liste
        list_frame = tk.Frame(self.dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview (Tabelle)
        columns = ('title', 'date', 'messages', 'model')
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            selectmode='browse',
            yscrollcommand=scrollbar.set
        )
        
        # Spalten konfigurieren
        self.tree.heading('title', text='Titel')
        self.tree.heading('date', text='Datum')
        self.tree.heading('messages', text='Nachrichten')
        self.tree.heading('model', text='Modell')
        
        self.tree.column('title', width=250)
        self.tree.column('date', width=150)
        self.tree.column('messages', width=100)
        self.tree.column('model', width=100)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Double-Click zum Wiederherstellen
        self.tree.bind('<Double-1>', lambda e: self._restore_selected())
        
        # Settings-Frame
        settings_frame = tk.Frame(self.dialog, bg='#F8F9FA')
        settings_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.auto_restore_var = tk.BooleanVar(value=self.auto_restore_enabled)
        auto_restore_check = ttk.Checkbutton(
            settings_frame,
            text="Immer letzte Session automatisch laden",
            variable=self.auto_restore_var,
            command=self._toggle_auto_restore
        )
        auto_restore_check.pack(anchor=tk.W)
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg='#F8F9FA', height=60)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)
        button_frame.pack_propagate(False)
        
        # Neu starten Button
        new_button = tk.Button(
            button_frame,
            text="🆕 Neuer Chat",
            font=('Segoe UI', 10),
            bg='#6C757D',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            padx=20,
            pady=8,
            command=self._start_new
        )
        new_button.pack(side=tk.LEFT, padx=5)
        
        # Wiederherstellen Button
        restore_button = tk.Button(
            button_frame,
            text="✅ Wiederherstellen",
            font=('Segoe UI', 10, 'bold'),
            bg='#28A745',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            padx=20,
            pady=8,
            command=self._restore_selected
        )
        restore_button.pack(side=tk.RIGHT, padx=5)
        
        # Hover-Effekte
        def on_enter_new(e):
            new_button.config(bg='#5A6268')
        def on_leave_new(e):
            new_button.config(bg='#6C757D')
        
        def on_enter_restore(e):
            restore_button.config(bg='#218838')
        def on_leave_restore(e):
            restore_button.config(bg='#28A745')
        
        new_button.bind('<Enter>', on_enter_new)
        new_button.bind('<Leave>', on_leave_new)
        restore_button.bind('<Enter>', on_enter_restore)
        restore_button.bind('<Leave>', on_leave_restore)
    
    def _load_sessions(self):
        """Lädt Sessions und füllt Tabelle"""
        try:
            # Lade letzte 10 Sessions
            sessions = self.service.list_chat_sessions(limit=10, sort_by='updated_at', reverse=True)
            
            if not sessions:
                # Keine Sessions vorhanden
                self.tree.insert('', tk.END, values=(
                    'Keine Sessions gefunden',
                    '',
                    '',
                    ''
                ))
                return
            
            # Fülle Tabelle
            for session in sessions:
                # Formatiere Datum
                updated_at = datetime.fromisoformat(session['updated_at'])
                date_str = self._format_date(updated_at)
                
                # Kürze Titel
                title = session['title']
                if len(title) > 40:
                    title = title[:37] + '...'
                
                # Füge Zeile hinzu
                item_id = self.tree.insert('', tk.END, values=(
                    title,
                    date_str,
                    f"{session['message_count']} msg",
                    session['llm_model']
                ))
                
                # Speichere Session-ID als Tag
                self.tree.item(item_id, tags=(session['session_id'],))
            
            # Wähle erste Session aus
            first_item = self.tree.get_children()[0]
            self.tree.selection_set(first_item)
            self.tree.focus(first_item)
            
            logger.info(f"{len(sessions)} Sessions in Dialog geladen")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Sessions: {e}")
            messagebox.showerror("Fehler", f"Sessions konnten nicht geladen werden:\n{e}")
    
    def _format_date(self, dt: datetime) -> str:
        """Formatiert Datum relativ"""
        now = datetime.now()
        delta = now - dt
        
        if delta.days == 0:
            # Heute
            return f"Heute {dt.strftime('%H:%M')}"
        elif delta.days == 1:
            # Gestern
            return f"Gestern {dt.strftime('%H:%M')}"
        elif delta.days < 7:
            # Diese Woche
            weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
            return f"{weekdays[dt.weekday()]} {dt.strftime('%H:%M')}"
        else:
            # Älter
            return dt.strftime('%d.%m.%Y')
    
    def _toggle_auto_restore(self):
        """Toggle Auto-Restore Setting"""
        self.auto_restore_enabled = self.auto_restore_var.get()
        self._save_settings()
        logger.info(f"Auto-Restore: {'aktiviert' if self.auto_restore_enabled else 'deaktiviert'}")
    
    def _restore_selected(self):
        """Stellt ausgewählte Session wieder her"""
        selection = self.tree.selection()
        
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie eine Session aus.")
            return
        
        # Hole Session-ID aus Tags
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        
        if not tags or tags[0] == '':
            # Keine Sessions vorhanden
            self._start_new()
            return
        
        session_id = tags[0]
        
        # Setze Result
        self.result = session_id
        
        logger.info(f"Session wird wiederhergestellt: {session_id[:8]}...")
        
        # Schließe Dialog
        self.dialog.destroy()
    
    def _start_new(self):
        """Startet neuen Chat"""
        self.result = None
        logger.info("Neuer Chat wird gestartet")
        self.dialog.destroy()
    
    def show(self) -> Optional[str]:
        """
        Zeigt Dialog und wartet auf Auswahl
        
        Returns:
            Session-ID zum Wiederherstellen oder None für neuen Chat
        """
        # Warte auf Dialog-Schließung
        self.dialog.wait_window()
        
        return self.result


def show_session_restore_dialog(parent, chat_persistence_service) -> Optional[str]:
    """
    Zeigt Session-Restore-Dialog
    
    Args:
        parent: Parent-Window
        chat_persistence_service: ChatPersistenceService-Instanz
        
    Returns:
        Session-ID zum Wiederherstellen oder None für neuen Chat
    """
    dialog = SessionRestoreDialog(parent, chat_persistence_service)
    return dialog.show()


# Example Usage
if __name__ == "__main__":
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    from backend.services.chat_persistence_service import ChatPersistenceService
    
    # Create test window
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    # Initialize service
    service = ChatPersistenceService()
    
    # Show dialog
    result = show_session_restore_dialog(root, service)
    
    if result:
        print(f"✅ Session wird wiederhergestellt: {result[:8]}...")
    else:
        print("🆕 Neuer Chat wird gestartet")
    
    root.destroy()
