#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS UI Module: Dialog Manager
Verantwortlich für verschiedene Dialog-Fenster (Chats, Settings, Info, README)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import glob
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DialogManager:
    """
    Manager für VERITAS Dialog-Fenster
    Beinhaltet: Chat-Verwaltung, Einstellungen, Info, README
    """
    
    def __init__(
        self, 
        parent_window: tk.Tk,
        chat_messages: List[Dict] = None,
        status_var: tk.StringVar = None,
        update_chat_callback = None
    ):
        """
        Initialisiert den Dialog Manager
        
        Args:
            parent_window: Hauptfenster
            chat_messages: Aktuelle Chat-Nachrichten (optional)
            status_var: StringVar für Status-Updates (optional)
            update_chat_callback: Callback zum Update des Chat-Displays (optional)
        """
        self.parent_window = parent_window
        self.chat_messages = chat_messages or []
        self.status_var = status_var
        self.update_chat_callback = update_chat_callback
        
        # Chats-Ordner
        self.chats_dir = os.path.join(os.getcwd(), "chats")
        if not os.path.exists(self.chats_dir):
            os.makedirs(self.chats_dir)
    
    # === CHAT-VERWALTUNG ===
    
    def save_chat(self, messages: List[Dict] = None) -> None:
        """
        Speichert den aktuellen Chat
        
        Args:
            messages: Chat-Nachrichten zum Speichern (optional, nutzt self.chat_messages als Fallback)
        """
        save_messages = messages or self.chat_messages
        
        if not save_messages:
            messagebox.showinfo("Info", "Kein Chat zum Speichern vorhanden")
            return
        
        # Dateiname-Vorschlag aus erstem User-Text
        suggested_name = self._get_suggested_filename(save_messages)
        
        filename = filedialog.asksaveasfilename(
            initialdir=self.chats_dir,
            initialfile=f"{suggested_name}.json",
            defaultextension=".json",
            filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(save_messages, f, ensure_ascii=False, indent=2)
                
                basename = os.path.basename(filename)
                self._set_status(f"Chat gespeichert: {basename}")
                messagebox.showinfo("Erfolg", f"Chat gespeichert: {basename}")
                logger.info(f"Chat gespeichert: {filename}")
                
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")
                logger.error(f"Fehler beim Speichern: {e}")
    
    def load_chat(self) -> Optional[List[Dict]]:
        """
        Lädt einen Chat aus einer Datei
        
        Returns:
            Geladene Chat-Nachrichten oder None
        """
        filename = filedialog.askopenfilename(
            initialdir=self.chats_dir,
            filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    loaded_messages = json.load(f)
                
                self.chat_messages = loaded_messages
                
                basename = os.path.basename(filename)
                self._set_status(f"Chat geladen: {basename}")
                messagebox.showinfo("Erfolg", f"Chat geladen: {basename}")
                
                # Update Display wenn Callback vorhanden
                if self.update_chat_callback:
                    self.update_chat_callback()
                
                return loaded_messages
                
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden: {e}")
                logger.error(f"Fehler beim Laden: {e}")
                return None
    
    def show_all_chats_dialog(self) -> None:
        """Zeigt Dialog mit allen verfügbaren Chats"""
        recent_chats = self._get_recent_chats()
        
        if not recent_chats:
            messagebox.showinfo("Info", "Keine Chat-Dateien gefunden")
            return
        
        # Dialog erstellen
        dialog = tk.Toplevel(self.parent_window)
        dialog.title("📋 Alle verfügbaren Chats")
        dialog.geometry("600x400")
        dialog.resizable(True, True)
        dialog.transient(self.parent_window)
        dialog.grab_set()
        
        # Header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(
            header_frame, 
            text=f"📋 {len(recent_chats)} Chat(s) gefunden", 
            font=('Segoe UI', 12, 'bold')
        ).pack(side=tk.LEFT)
        
        # Liste mit Scrollbar
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        chat_listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set,
            font=('Segoe UI', 9)
        )
        chat_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=chat_listbox.yview)
        
        # Populiere Liste
        for chat_info in recent_chats:
            name = chat_info['name']
            path = chat_info['path']
            mtime = datetime.fromtimestamp(chat_info['mtime']).strftime("%d.%m.%Y %H:%M")
            filename = os.path.basename(path)
            
            display_text = f"{name} ({filename}) - {mtime}"
            chat_listbox.insert(tk.END, display_text)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def load_selected():
            selection = chat_listbox.curselection()
            if selection:
                selected_chat = recent_chats[selection[0]]
                dialog.destroy()
                self._load_recent_chat(selected_chat['path'])
        
        def on_double_click(event):
            load_selected()
        
        chat_listbox.bind('<Double-Button-1>', on_double_click)
        
        ttk.Button(button_frame, text="📂 Laden", command=load_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="❌ Schließen", command=dialog.destroy).pack(side=tk.LEFT)
        
        # Zentriere Dialog
        self._center_dialog(dialog, 600, 400)
    
    def _load_recent_chat(self, file_path: str) -> None:
        """Lädt einen Chat aus der Recent-Liste"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_messages = json.load(f)
            
            self.chat_messages = loaded_messages
            
            basename = os.path.basename(file_path)
            self._set_status(f"Chat geladen: {basename}")
            logger.info(f"Recent chat geladen: {basename}")
            
            # Update Display
            if self.update_chat_callback:
                self.update_chat_callback()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden: {e}")
            logger.error(f"Fehler beim Laden von {file_path}: {e}")
    
    def _get_recent_chats(self) -> List[Dict]:
        """
        Ermittelt die letzten Chat-Dateien
        
        Returns:
            Liste mit Chat-Infos (name, path, mtime)
        """
        try:
            # Suche in typischen Speicherorten
            search_paths = [
                os.path.expanduser("~/Documents/*.json"),
                os.path.expanduser("~/Desktop/*.json"),
                os.path.join(os.getcwd(), "*.json"),
                os.path.join(self.chats_dir, "*.json"),
            ]
            
            chat_files = []
            for pattern in search_paths:
                chat_files.extend(glob.glob(pattern))
            
            # Entferne Duplikate
            unique_files = list(set(chat_files))
            recent_chats = []
            
            for file_path in unique_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Validiere Chat-Datei
                    if self._is_valid_chat_file(data):
                        chat_name = self._extract_chat_name(data, file_path)
                        
                        recent_chats.append({
                            'name': chat_name,
                            'path': file_path,
                            'mtime': os.path.getmtime(file_path)
                        })
                except:
                    continue
            
            # Sortiere nach Änderungszeit
            recent_chats.sort(key=lambda x: x['mtime'], reverse=True)
            return recent_chats
            
        except Exception as e:
            logger.error(f"Fehler beim Ermitteln der letzten Chats: {e}")
            return []
    
    def _is_valid_chat_file(self, data: any) -> bool:
        """Prüft ob Datei eine gültige Chat-Datei ist"""
        if not isinstance(data, list) or len(data) == 0:
            return False
        
        first_item = data[0]
        return isinstance(first_item, dict) and 'role' in first_item and 'content' in first_item
    
    def _extract_chat_name(self, data: List[Dict], file_path: str) -> str:
        """Extrahiert aussagekräftigen Namen aus Chat-Daten"""
        # Versuche ersten User-Text zu finden
        for msg in data:
            if msg.get('role') == 'user':
                content = msg.get('content', '').strip()
                if content:
                    return content[:50] + ("..." if len(content) > 50 else "")
        
        # Fallback: Dateiname
        return Path(file_path).stem
    
    def _get_suggested_filename(self, messages: List[Dict]) -> str:
        """Erstellt Dateinamen-Vorschlag aus Messages"""
        for msg in messages:
            if msg.get('role') == 'user':
                content = msg.get('content', '').strip()
                if content:
                    import re
                    clean_name = re.sub(r'[<>:"/\\|?*]', '', content[:30])
                    return clean_name.replace(' ', '_')
        
        return "chat"
    
    # === INFO-DIALOGE ===
    
    def show_settings(self) -> None:
        """Zeigt Einstellungen-Dialog"""
        messagebox.showinfo(
            "Einstellungen", 
            "Einstellungen werden in einem zukünftigen Update verfügbar sein"
        )
    
    def show_info(self, version: str = "3.5.0") -> None:
        """
        Zeigt Info-Dialog
        
        Args:
            version: VERITAS Version
        """
        info_text = f"""VERITAS Chat v{version}
        
Moderne Chat-Anwendung mit:
• Multi-Window-Unterstützung
• RAG-Integration
• HTTP/HTTPS Backend-API
• Feedback-System
• Markdown-Rendering

© 2025 VERITAS Team"""
        
        messagebox.showinfo("Info", info_text)
    
    def show_readme(self) -> None:
        """Zeigt README.md im Chat-Fenster"""
        try:
            readme_path = self._find_readme()
            
            if readme_path and os.path.exists(readme_path):
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
            else:
                readme_content = self._get_default_readme()
            
            # Kürze auf 2000 Zeichen
            if len(readme_content) > 2000:
                readme_content = readme_content[:2000] + "\n\n... (README gekürzt)"
            
            # Füge zu Chat-Messages hinzu
            readme_message = {
                'role': 'system',
                'content': f'📘 VERITAS README\n{"=" * 50}\n\n{readme_content}',
                'timestamp': datetime.now().isoformat()
            }
            
            self.chat_messages.append(readme_message)
            
            # Update Display
            if self.update_chat_callback:
                self.update_chat_callback()
            
            logger.info("README im Chat angezeigt")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der README: {e}")
            error_message = {
                'role': 'system',
                'content': f'❌ Fehler beim Laden der README: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            self.chat_messages.append(error_message)
            
            if self.update_chat_callback:
                self.update_chat_callback()
    
    def _find_readme(self) -> Optional[str]:
        """Findet README.md Datei"""
        # Projekt-Root
        readme_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'README.md'
        )
        
        if os.path.exists(readme_path):
            return readme_path
        
        # Fallback-Pfade
        possible_paths = [
            'README.md',
            '../README.md',
            '../../README.md',
            os.path.join(os.getcwd(), 'README.md'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _get_default_readme(self) -> str:
        """Gibt Default-README zurück wenn keine Datei gefunden"""
        return """# VERITAS - Verwaltungs-Informations-System

## Übersicht
VERITAS ist ein modernes Chat-basiertes Informationssystem für die öffentliche Verwaltung.

## Features
- 🤖 **Intelligent Chat**: RAG-basierte Antworten mit LLM-Integration
- 🪟 **Multi-Window**: Mehrere Chat-Fenster gleichzeitig öffnen
- 🔌 **Backend-API**: HTTP/HTTPS-basierte Kommunikation
- 📊 **Streaming**: Echtzeit-Fortschrittsupdates
- 💾 **Persistenz**: Chats speichern und laden
- 📝 **Markdown**: Rich-Text Formatierung in Antworten

## Architektur
- **Frontend**: Tkinter GUI (Python)
- **Backend**: FastAPI REST API
- **LLM**: Ollama Integration
- **Datenbank**: PostgreSQL + Neo4j + ChromaDB

## Verwendung
1. Stellen Sie sicher, dass das Backend läuft
2. Wählen Sie einen Frage-Modus
3. Geben Sie Ihre Frage ein
4. Erhalten Sie KI-gestützte Antworten

## Kontakt
Für weitere Informationen siehe Projekt-Dokumentation."""
    
    # === HELPER METHODS ===
    
    def _set_status(self, message: str, timeout: int = None) -> None:
        """Setzt Status-Nachricht mit optionalem Timeout"""
        if not self.status_var:
            return
        
        original_status = self.status_var.get()
        self.status_var.set(message)
        
        if timeout and self.parent_window:
            self.parent_window.after(timeout, lambda: self.status_var.set(original_status))
    
    def _center_dialog(self, dialog: tk.Toplevel, width: int, height: int) -> None:
        """Zentriert Dialog auf dem Bildschirm"""
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
