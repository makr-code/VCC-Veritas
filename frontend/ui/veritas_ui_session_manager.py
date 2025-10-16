"""
VERITAS Session Manager UI
==========================

Vollständige Session-Verwaltungs-UI mit allen Funktionen.

Features:
- Tabelle mit allen Sessions (Titel, Datum, Messages, Größe)
- Aktionen: Öffnen, Umbenennen, Löschen, Exportieren
- Suche/Filter nach Titel, Datum
- Sortierung nach allen Spalten
- Session-Statistiken

Version: v3.20.0
Author: VERITAS Team
Date: 12. Oktober 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import json
import os
import shutil

logger = logging.getLogger(__name__)


class SessionManagerWindow:
    """Session-Manager-Fenster"""
    
    def __init__(self, parent, chat_persistence_service, on_session_opened: Optional[Callable] = None):
        """
        Initialisiert Session-Manager
        
        Args:
            parent: Parent-Window (Tkinter)
            chat_persistence_service: ChatPersistenceService-Instanz
            on_session_opened: Callback wenn Session geöffnet wird (session_id)
        """
        self.parent = parent
        self.service = chat_persistence_service
        self.on_session_opened = on_session_opened
        
        # Window erstellen
        self.window = tk.Toplevel(parent)
        self.window.title("📁 Session-Verwaltung")
        self.window.geometry("900x600")
        
        # Modal
        self.window.transient(parent)
        
        # Zentriere Window
        self._center_window()
        
        # UI erstellen
        self._create_ui()
        
        # Lade Sessions
        self.refresh_sessions()
        
        logger.info("Session-Manager geöffnet")
    
    def _center_window(self):
        """Zentriert Window auf Bildschirm"""
        self.window.update_idletasks()
        
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_ui(self):
        """Erstellt UI"""
        # Header
        header_frame = tk.Frame(self.window, bg='#2E86AB', height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(
            header_frame,
            text="📁 Session-Verwaltung",
            font=('Segoe UI', 16, 'bold'),
            bg='#2E86AB',
            fg='white'
        )
        header_label.pack(pady=10)
        
        # Statistiken
        self.stats_label = tk.Label(
            header_frame,
            text="",
            font=('Segoe UI', 9),
            bg='#2E86AB',
            fg='white'
        )
        self.stats_label.pack()
        
        # Toolbar
        toolbar_frame = tk.Frame(self.window, bg='#F8F9FA', height=50)
        toolbar_frame.pack(fill=tk.X, padx=10, pady=5)
        toolbar_frame.pack_propagate(False)
        
        # Suche
        search_label = tk.Label(toolbar_frame, text="🔍 Suche:", bg='#F8F9FA', font=('Segoe UI', 9))
        search_label.pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.refresh_sessions())
        
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Refresh-Button
        refresh_btn = tk.Button(
            toolbar_frame,
            text="🔄 Aktualisieren",
            font=('Segoe UI', 9),
            bg='#28A745',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self.refresh_sessions
        )
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # Sessions-Tabelle
        table_frame = tk.Frame(self.window)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        columns = ('title', 'date', 'updated', 'messages', 'model', 'size')
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            selectmode='browse',
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        # Spalten konfigurieren
        self.tree.heading('title', text='Titel', command=lambda: self._sort_by('title'))
        self.tree.heading('date', text='Erstellt', command=lambda: self._sort_by('created_at'))
        self.tree.heading('updated', text='Aktualisiert', command=lambda: self._sort_by('updated_at'))
        self.tree.heading('messages', text='Nachrichten', command=lambda: self._sort_by('message_count'))
        self.tree.heading('model', text='Modell', command=lambda: self._sort_by('llm_model'))
        self.tree.heading('size', text='Größe', command=lambda: self._sort_by('size'))
        
        self.tree.column('title', width=300)
        self.tree.column('date', width=120)
        self.tree.column('updated', width=120)
        self.tree.column('messages', width=100)
        self.tree.column('model', width=120)
        self.tree.column('size', width=80)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        
        # Rechtsklick-Menü
        self._create_context_menu()
        
        # Double-Click zum Öffnen
        self.tree.bind('<Double-1>', lambda e: self._open_session())
        
        # Actions-Frame
        actions_frame = tk.Frame(self.window, bg='#F8F9FA', height=60)
        actions_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        actions_frame.pack_propagate(False)
        
        # Buttons
        open_btn = tk.Button(
            actions_frame,
            text="📂 Öffnen",
            font=('Segoe UI', 10),
            bg='#28A745',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            padx=15,
            pady=8,
            command=self._open_session
        )
        open_btn.pack(side=tk.LEFT, padx=5)
        
        rename_btn = tk.Button(
            actions_frame,
            text="✏️ Umbenennen",
            font=('Segoe UI', 10),
            bg='#F18F01',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            padx=15,
            pady=8,
            command=self._rename_session
        )
        rename_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = tk.Button(
            actions_frame,
            text="💾 Exportieren",
            font=('Segoe UI', 10),
            bg='#2E86AB',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            padx=15,
            pady=8,
            command=self._export_session
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(
            actions_frame,
            text="🗑️ Löschen",
            font=('Segoe UI', 10),
            bg='#C73E1D',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            padx=15,
            pady=8,
            command=self._delete_session
        )
        delete_btn.pack(side=tk.RIGHT, padx=5)
        
        close_btn = tk.Button(
            actions_frame,
            text="❌ Schließen",
            font=('Segoe UI', 10),
            bg='#6C757D',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            padx=15,
            pady=8,
            command=self.window.destroy
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Sortierung
        self.sort_column = 'updated_at'
        self.sort_reverse = True
    
    def _create_context_menu(self):
        """Erstellt Rechtsklick-Menü"""
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="📂 Öffnen", command=self._open_session)
        self.context_menu.add_command(label="✏️ Umbenennen", command=self._rename_session)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="💾 Exportieren", command=self._export_session)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Löschen", command=self._delete_session)
        
        self.tree.bind('<Button-3>', self._show_context_menu)
    
    def _show_context_menu(self, event):
        """Zeigt Rechtsklick-Menü"""
        # Wähle Item unter Cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def refresh_sessions(self):
        """Lädt und zeigt Sessions"""
        try:
            # Lösche alte Einträge
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Lade Sessions
            all_sessions = self.service.list_chat_sessions(
                sort_by=self.sort_column,
                reverse=self.sort_reverse
            )
            
            # Filter nach Suchbegriff
            search_term = self.search_var.get().lower()
            if search_term:
                all_sessions = [
                    s for s in all_sessions
                    if search_term in s['title'].lower()
                ]
            
            # Füge Sessions hinzu
            for session in all_sessions:
                # Formatiere Daten
                created = datetime.fromisoformat(session['created_at']).strftime('%d.%m.%Y %H:%M')
                updated = datetime.fromisoformat(session['updated_at']).strftime('%d.%m.%Y %H:%M')
                
                # File-Size
                session_file = os.path.join(self.service.sessions_dir, f"{session['session_id']}.json")
                if os.path.exists(session_file):
                    size_bytes = os.path.getsize(session_file)
                    size_str = self._format_size(size_bytes)
                else:
                    size_str = "N/A"
                
                # Kürze Titel
                title = session['title']
                if len(title) > 50:
                    title = title[:47] + '...'
                
                # Füge Zeile hinzu
                item_id = self.tree.insert('', tk.END, values=(
                    title,
                    created,
                    updated,
                    session['message_count'],
                    session['llm_model'],
                    size_str
                ))
                
                # Speichere Session-ID als Tag
                self.tree.item(item_id, tags=(session['session_id'],))
            
            # Update Statistiken
            stats = self.service.get_session_statistics()
            self.stats_label.config(
                text=f"📊 {stats.get('total_sessions', 0)} Sessions | "
                     f"{stats.get('total_messages', 0)} Nachrichten | "
                     f"⌀ {stats.get('avg_messages_per_session', 0):.1f} Nachrichten/Session"
            )
            
            logger.info(f"{len(all_sessions)} Sessions angezeigt (Suche: '{search_term}')")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Sessions: {e}")
            messagebox.showerror("Fehler", f"Sessions konnten nicht geladen werden:\n{e}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Formatiert Dateigröße"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / 1024 / 1024:.1f} MB"
    
    def _sort_by(self, column: str):
        """Sortiert Tabelle nach Spalte"""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = True
        
        self.refresh_sessions()
    
    def _get_selected_session_id(self) -> Optional[str]:
        """Gibt ausgewählte Session-ID zurück"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie eine Session aus.")
            return None
        
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        return tags[0] if tags else None
    
    def _open_session(self):
        """Öffnet ausgewählte Session"""
        session_id = self._get_selected_session_id()
        if not session_id:
            return
        
        try:
            # Callback aufrufen
            if self.on_session_opened:
                self.on_session_opened(session_id)
            
            # Fenster schließen
            self.window.destroy()
            
            logger.info(f"Session geöffnet: {session_id[:8]}...")
            
        except Exception as e:
            logger.error(f"Fehler beim Öffnen der Session: {e}")
            messagebox.showerror("Fehler", f"Session konnte nicht geöffnet werden:\n{e}")
    
    def _rename_session(self):
        """Benennt Session um"""
        session_id = self._get_selected_session_id()
        if not session_id:
            return
        
        try:
            # Lade Session
            session = self.service.load_chat_session(session_id)
            if not session:
                messagebox.showerror("Fehler", "Session konnte nicht geladen werden.")
                return
            
            # Dialog für neuen Titel
            new_title = tk.simpledialog.askstring(
                "Umbenennen",
                "Neuer Titel:",
                initialvalue=session.title,
                parent=self.window
            )
            
            if new_title and new_title != session.title:
                # Update Titel
                session.title = new_title
                
                # Speichern
                self.service.save_chat_session(session)
                
                # Refresh
                self.refresh_sessions()
                
                logger.info(f"Session umbenannt: {session_id[:8]}... → {new_title}")
            
        except Exception as e:
            logger.error(f"Fehler beim Umbenennen: {e}")
            messagebox.showerror("Fehler", f"Umbenennen fehlgeschlagen:\n{e}")
    
    def _export_session(self):
        """Exportiert Session als JSON"""
        session_id = self._get_selected_session_id()
        if not session_id:
            return
        
        try:
            # Lade Session
            session = self.service.load_chat_session(session_id)
            if not session:
                messagebox.showerror("Fehler", "Session konnte nicht geladen werden.")
                return
            
            # Dateidialog
            filename = filedialog.asksaveasfilename(
                parent=self.window,
                title="Session exportieren",
                defaultextension=".json",
                filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")],
                initialfile=f"{session.title[:30]}.json"
            )
            
            if filename:
                # Exportiere als JSON
                session_data = session.to_dict()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Erfolg", f"Session exportiert nach:\n{filename}")
                logger.info(f"Session exportiert: {session_id[:8]}... → {filename}")
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren: {e}")
            messagebox.showerror("Fehler", f"Export fehlgeschlagen:\n{e}")
    
    def _delete_session(self):
        """Löscht Session"""
        session_id = self._get_selected_session_id()
        if not session_id:
            return
        
        try:
            # Lade Session für Titel
            session = self.service.load_chat_session(session_id)
            title = session.title if session else session_id[:8]
            
            # Bestätigung
            confirm = messagebox.askyesno(
                "Löschen bestätigen",
                f"Session wirklich löschen?\n\n{title}\n\n"
                "Ein Backup wird automatisch erstellt.",
                parent=self.window
            )
            
            if confirm:
                # Löschen (mit Backup)
                success = self.service.delete_chat_session(session_id, create_backup=True)
                
                if success:
                    messagebox.showinfo("Erfolg", f"Session gelöscht:\n{title}")
                    
                    # Refresh
                    self.refresh_sessions()
                    
                    logger.info(f"Session gelöscht: {session_id[:8]}...")
                else:
                    messagebox.showerror("Fehler", "Session konnte nicht gelöscht werden.")
            
        except Exception as e:
            logger.error(f"Fehler beim Löschen: {e}")
            messagebox.showerror("Fehler", f"Löschen fehlgeschlagen:\n{e}")


def show_session_manager(parent, chat_persistence_service, on_session_opened: Optional[Callable] = None):
    """
    Zeigt Session-Manager-Fenster
    
    Args:
        parent: Parent-Window
        chat_persistence_service: ChatPersistenceService-Instanz
        on_session_opened: Callback wenn Session geöffnet wird
    """
    SessionManagerWindow(parent, chat_persistence_service, on_session_opened)


# Example Usage
if __name__ == "__main__":
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    from backend.services.chat_persistence_service import ChatPersistenceService
    
    # Create main window
    root = tk.Tk()
    root.title("VERITAS Test")
    root.geometry("400x300")
    
    # Initialize service
    service = ChatPersistenceService()
    
    # Button zum Öffnen
    def open_manager():
        show_session_manager(root, service, on_session_opened=lambda sid: print(f"Session geöffnet: {sid[:8]}..."))
    
    btn = tk.Button(root, text="📁 Session-Manager öffnen", command=open_manager, padx=20, pady=10)
    btn.pack(expand=True)
    
    root.mainloop()
