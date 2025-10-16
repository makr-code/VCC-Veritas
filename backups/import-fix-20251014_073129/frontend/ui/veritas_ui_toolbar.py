"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "veritas_ui_toolbar"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...ZWfdbw=="  # Gekuerzt fuer Sicherheit
module_organization_key = "a1691258098bec4f2a57cc74dafcc5b070161ad1ee73c5c1a19270ae346e1074"
module_file_key = "bd359bc774b0f32b00f254237be7f69002466501aba4e72bc37d696c21769ce8"
module_version = "1.0"
module_protection_level = 1
# === END PROTECTION KEYS ===
import tkinter as tk
from tkinter import ttk, Menu, messagebox, filedialog
import logging
import os
import json
import threading
import requests
from frontend.ui.veritas_ui_components import Tooltip
from frontend.themes.veritas_forest_theme import apply_forest_styles_to_window, get_forest_style_for_widget

logger = logging.getLogger(__name__)


class ChatToolbar(ttk.Frame):
    def _create_user_chat_list(self, parent):
        """Erstellt eine Listbox mit den eigenen Chats und platziert sie im UI."""
        self.user_chat_list_frame = ttk.LabelFrame(parent, text="Meine Chats")
        self.user_chat_list_frame.pack(side="left", fill="y", padx=5, pady=5)
        self.user_chat_listbox = tk.Listbox(self.user_chat_list_frame, height=8)
        self.user_chat_listbox.pack(fill="both", expand=True)
        self.user_chat_listbox.bind('<Double-Button-1>', self._on_user_chat_select)
        self._update_user_chat_list()
        self._start_user_chat_list_updater()

    def _update_user_chat_list(self):
        """Lädt die eigenen Chats per API und aktualisiert die Listbox."""
        try:
            import requests
            from config import API_BASE_URL
            user_id = self.current_user.get("user_id") or self.current_user.get("email")
            response = requests.get(f"{API_BASE_URL}/recent_conversations", timeout=3)
            if response.status_code == 200:
                data = response.json()
                conversations = data.get("recent_conversations", [])
                user_chats = [c for c in conversations if c.get("user_id") == user_id]
                self.user_chat_listbox.delete(0, tk.END)
                for chat in user_chats:
                    title = chat.get("title") or f"Chat {chat.get('session_id')}"
                    self.user_chat_listbox.insert(tk.END, f"{title} | {chat.get('session_id')}")
            else:
                self.user_chat_listbox.delete(0, tk.END)
                self.user_chat_listbox.insert(tk.END, "Fehler beim Laden der Chats")
        except Exception as e:
            self.user_chat_listbox.delete(0, tk.END)
            self.user_chat_listbox.insert(tk.END, f"Fehler: {e}")

    def _start_user_chat_list_updater(self):
        """Startet einen Thread, der die Chatliste regelmäßig aktualisiert."""
        import threading
        def updater():
            while True:
                self.after(0, self._update_user_chat_list)
                import time; time.sleep(30)
        t = threading.Thread(target=updater, daemon=True)
        t.start()

    def _on_user_chat_select(self, event):
        """Öffnet den ausgewählten Chat zum Fortführen."""
        selection = self.user_chat_listbox.curselection()
        if selection:
            value = self.user_chat_listbox.get(selection[0])
            # Session-ID extrahieren
            if '|' in value:
                chat_id = value.split('|')[-1].strip()
                self._open_and_continue_chat(chat_id)
    """Moderne Toolbar für Single-Chat-Windows."""
    
    def __init__(self, parent, chat_window, show_user_profile=True, **kwargs):
        """
        Initialisiert die Toolbar.
        
        Args:
            parent: Parent-Widget
            chat_window: Referenz zum Chat-Fenster
            show_user_profile: Zeigt Benutzeridentifikation an
        """
        super().__init__(parent, **kwargs)
        self.chat_window = chat_window
        self.show_user_profile = show_user_profile
        
        # Benutzer-Info
        self.current_user = self._load_user_info()
        
        self._create_widgets()
        
        # Forest-Styles anwenden nach Widget-Erstellung
        self.after(100, lambda: self._apply_forest_theme())
        
    def get_app_instance(self):
        """Holt die globale App-Instanz."""
        try:
            from frontend.veritas_app import get_veritas_app
            return get_veritas_app()
        except ImportError:
            return None
        
    def _create_widgets(self):
        """Erstellt alle Toolbar-Widgets."""
    # Linker Bereich - Hauptaktionen und Chatliste
        left_frame = ttk.Frame(self)
        left_frame.pack(side="left", fill="y")
        # Hamburger-Menu Button (für alle Chat-Fenster verfügbar)
        self._create_hamburger_button(left_frame)
        separator0 = ttk.Separator(left_frame, orient="vertical")
        separator0.pack(side="left", fill="y", padx=(2, 5))
        # Zweiter Separator
        separator2 = ttk.Separator(left_frame, orient="vertical")
        separator2.pack(side="left", fill="y", padx=(2, 5))
        # Eigene Chats als Dropdown-Auswahl auf der Toolbar
        self._create_user_chat_dropdown(left_frame)
        self._create_chat_actions(left_frame)

        # Rechter Bereich - API-Status, Suche und Benutzer
        right_frame = ttk.Frame(self)
        right_frame.pack(side="right", fill="y")
        self.right_toolbar_frame = right_frame  # Für MainChatWindow Status-Label

        # API-Status Button (rechts)
        self._create_api_status_button(right_frame)

        # Suchfeld
        ttk.Label(right_frame, text="🔍").pack(side="left", padx=(0, 2))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(right_frame, textvariable=self.search_var, width=15)
        self.search_entry.pack(side="left", padx=(0, 5))
        self.search_entry.bind("<Return>", self._search_in_chat)

        # Benutzeridentifikation
        if self.show_user_profile:
            self._create_user_profile_section(right_frame)
    def _create_user_chat_dropdown(self, parent):
        """Erstellt eine Dropdown-Auswahlliste für eigene Chats auf der Toolbar."""
        self.user_chat_var = tk.StringVar()
        self.user_chat_dropdown = ttk.Combobox(parent, textvariable=self.user_chat_var, state="readonly", width=32)
        self.user_chat_dropdown.pack(side="left", padx=(2, 5))
        self.user_chat_dropdown.bind("<<ComboboxSelected>>", self._on_user_chat_dropdown_select)
        self._update_user_chat_dropdown()

    def _update_user_chat_dropdown(self):
        """Lädt die eigenen Chats per API und aktualisiert die Dropdown-Auswahl."""
        try:
            import requests
            from config import API_BASE_URL
            user_id = self.current_user.get("user_id") or self.current_user.get("email")
            response = requests.get(f"{API_BASE_URL}/recent_conversations", timeout=3)
            if response.status_code == 200:
                data = response.json()
                conversations = data.get("recent_conversations", [])
                user_chats = [c for c in conversations if c.get("user_id") == user_id]
                values = [f"{chat.get('title') or 'Chat'} | {chat.get('session_id')}" for chat in user_chats]
                self.user_chat_dropdown['values'] = values
                if values:
                    self.user_chat_dropdown.current(0)
            else:
                self.user_chat_dropdown['values'] = ["Fehler beim Laden der Chats"]
        except Exception as e:
            self.user_chat_dropdown['values'] = [f"Fehler: {e}"]

    def _on_user_chat_dropdown_select(self, event):
        value = self.user_chat_var.get()
        if '|' in value:
            chat_id = value.split('|')[-1].strip()
            self._open_and_continue_chat(chat_id)

        # Rechter Bereich - API-Status, Suche und Benutzer
        right_frame = ttk.Frame(self)
        right_frame.pack(side="right", fill="y")
        self.right_toolbar_frame = right_frame  # Für MainChatWindow Status-Label

        # API-Status Button (rechts)
        self._create_api_status_button(right_frame)

        # Suchfeld
        ttk.Label(right_frame, text="🔍").pack(side="left", padx=(0, 2))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(right_frame, textvariable=self.search_var, width=15)
        self.search_entry.pack(side="left", padx=(0, 5))
        self.search_entry.bind("<Return>", self._search_in_chat)

        # Benutzeridentifikation
        if self.show_user_profile:
            self._create_user_profile_section(right_frame)
    
    def _create_hamburger_button(self, parent):
        """Erstellt den Hamburger-Button (nur für Hauptfenster)."""
        hamburger_btn = ttk.Button(parent, text="☰", 
                                 command=self._show_hamburger_menu, width=3)
        hamburger_btn.pack(side="left", padx=(0, 2))
        self.hamburger_btn = hamburger_btn
        
    def _show_hamburger_menu(self):
        """Zeigt das Hamburger-Menü."""
        menu = Menu(self, tearoff=0)
        menu.add_command(label="Neuer Chat", command=self._create_new_chat)
        menu.add_command(label="Chat öffnen", command=self._open_chat)
        menu.add_separator()

        # --- Eigene Chats als Submenü ---
        try:
            import requests
            from config import API_BASE_URL
            user_id = self.current_user.get("user_id") or self.current_user.get("email")
            response = requests.get(f"{API_BASE_URL}/recent_conversations", timeout=3)
            if response.status_code == 200:
                data = response.json()
                conversations = data.get("recent_conversations", [])
                user_chats = [c for c in conversations if c.get("user_id") == user_id]
                submenu = Menu(menu, tearoff=0)
                if user_chats:
                    for chat in user_chats:
                        title = chat.get("title") or f"Chat {chat.get('session_id')}"
                        submenu.add_command(
                            label=title,
                            command=lambda chat_id=chat.get("session_id"): self._open_and_continue_chat(chat_id)
                        )
                else:
                    submenu.add_command(label="Keine eigenen Chats gefunden", state="disabled")
                menu.add_cascade(label="🗂️ Meine Chats", menu=submenu)
            else:
                menu.add_command(label="Fehler beim Laden der Chats", state="disabled")
        except Exception as e:
            menu.add_command(label=f"Fehler: {e}", state="disabled")

        menu.add_command(label="Einstellungen", command=self._show_settings)
        menu.add_command(label="Info", command=self._show_info)
        menu.add_command(label="Beenden", command=self._quit_app)

        # Menu anzeigen
        try:
            x = self.hamburger_btn.winfo_rootx()
            y = self.hamburger_btn.winfo_rooty() + self.hamburger_btn.winfo_height()
            menu.post(x, y)
        except:
            pass

    def _open_and_continue_chat(self, chat_id):
        """Öffnet ein neues Chatfenster und lädt die Konversation zum Fortführen."""
        try:
            app = self.get_app_instance()
            if app and hasattr(app, 'open_chat_by_id'):
                app.open_chat_by_id(chat_id)
            else:
                messagebox.showinfo("Chat öffnen", f"Chat {chat_id} öffnen (Logik noch ergänzen)")
        except Exception as e:
            messagebox.showerror("Fehler", f"Chat konnte nicht geöffnet werden: {e}")

        # Verfügbare offene Chats anzeigen (wie bisher)
        app = self.get_app_instance()
        if app and app.chat_windows:
            other_chats = [w for w in app.chat_windows.values() 
                          if w != self.chat_window and hasattr(w, 'winfo_exists') and w.winfo_exists()]
            if other_chats:
                menu.add_command(label="📋 Verfügbare Chats:", state="disabled")
                for chat_window in other_chats[:5]:
                    chat_name = getattr(chat_window, 'chat_title', chat_window.chat_id)
                    menu.add_command(label=f"   → {chat_name}",
                                   command=lambda w=chat_window: self._switch_to_chat(w))
                menu.add_separator()

    def _open_recent_chat(self, chat_id):
        """Öffnet einen der letzten gespeicherten Chats anhand der Chat-ID."""
        try:
            # Hier kann die Logik ergänzt werden, um den Chat per Chat-ID zu öffnen
            # z.B. über die App-Instanz oder einen API-Call
            app = self.get_app_instance()
            if app and hasattr(app, 'open_chat_by_id'):
                app.open_chat_by_id(chat_id)
            else:
                messagebox.showinfo("Chat öffnen", f"Chat {chat_id} öffnen (Logik noch ergänzen)")
        except Exception as e:
            messagebox.showerror("Fehler", f"Chat konnte nicht geöffnet werden: {e}")
    
    def _create_user_profile_section(self, parent_frame):
        """Erstellt die Benutzer-Profil-Sektion in der Toolbar als Split-Button."""
        # Separator
        separator = ttk.Separator(parent_frame, orient="vertical")
        separator.pack(side="left", fill="y", padx=5)
        
        # Benutzer-Frame für Split-Button
        user_frame = ttk.Frame(parent_frame)
        user_frame.pack(side="left", padx=(5, 0))
        
        # Hauptbutton (Profil bearbeiten)
        user_text = f"{self.current_user['avatar']} {self.current_user['name']}"
        self.user_main_btn = ttk.Button(user_frame, text=user_text, 
                                       command=self._edit_user_profile, width=10)
        self.user_main_btn.pack(side="left")
        
        # Dropdown-Button
        self.user_dropdown_btn = ttk.Button(user_frame, text="▼", 
                                           command=self._show_user_menu, width=2)
        self.user_dropdown_btn.pack(side="left", padx=(1, 0))
    
    def _create_chat_actions(self, parent):
        """Erstellt Chat-Aktions-Buttons in der Toolbar."""
        # Chat exportieren
        export_btn = ttk.Button(parent, text="📋", width=3, 
                               command=self._export_chat)
        export_btn.pack(side="left", padx=(0, 2))
        Tooltip(export_btn, "Chat als Textdatei exportieren")
        
        # Chat löschen
        clear_btn = ttk.Button(parent, text="🗑️", width=3, 
                              command=self._clear_chat)
        clear_btn.pack(side="left", padx=(0, 2))
        Tooltip(clear_btn, "Chat-Verlauf löschen")
        
        # Detaillierte Quellen
        sources_btn = ttk.Button(parent, text="📚", width=3, 
                                command=self._show_detailed_sources)
        sources_btn.pack(side="left", padx=(0, 5))
        Tooltip(sources_btn, "Detaillierte Quelleninformationen der letzten Antwort")
        
        # Separator nach Chat-Aktionen
        separator1 = ttk.Separator(parent, orient="vertical")
        separator1.pack(side="left", fill="y", padx=(2, 5))
    
    def _create_api_status_button(self, parent):
        """Erstellt den API-Status-Button."""
        # API-Status Button mit Forest-Style
        accent_style = get_forest_style_for_widget('important_button')
        if accent_style:
            self.api_status_btn = ttk.Button(parent, text="🔴", width=3, 
                                            style=accent_style,
                                            command=self._check_api_status)
        else:
            self.api_status_btn = ttk.Button(parent, text="🔴", width=3, 
                                            command=self._check_api_status)
        
        self.api_status_btn.pack(side="left", padx=(5, 5))
        Tooltip(self.api_status_btn, "API-Status prüfen")
        
        # Initial API-Status prüfen
        self._check_api_status_async()
    
    def _apply_forest_theme(self):
        """Wendet Forest-Theme auf die Toolbar an."""
        try:
            apply_forest_styles_to_window(self)
            logger.debug("Forest-Styles auf Toolbar angewandt")
        except Exception as e:
            logger.error(f"Fehler beim Anwenden der Forest-Styles auf Toolbar: {e}")
    
    def _create_tooltip(self, widget, text):
        """Erstellt ein Tooltip für ein Widget - Deprecated, verwende Tooltip-Klasse."""
        # Diese Methode ist deprecated, verwende stattdessen die Tooltip-Klasse
        Tooltip(widget, text)
    
    def _load_user_info(self):
        """Lädt Benutzerinformationen."""
        try:
            user_file = os.path.join("data", "user_profile.json")
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Standard-Benutzer
                return {
                    "name": "Benutzer",
                    "email": "benutzer@veritas.local",
                    "avatar": "👤",
                    "theme": "dark"
                }
        except Exception as e:
            logger.error(f"Fehler beim Laden der Benutzerinfo: {e}")
            return {
                "name": "Benutzer",
                "email": "benutzer@veritas.local", 
                "avatar": "👤",
                "theme": "dark"
            }
    
    def _save_user_info(self):
        """Speichert Benutzerinformationen."""
        try:
            user_file = os.path.join("data", "user_profile.json")
            os.makedirs(os.path.dirname(user_file), exist_ok=True)
            
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_user, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Benutzerinfo: {e}")
    
    def _show_user_menu(self):
        """Zeigt das Benutzer-Profil-Menü ohne 'Über Veritas'."""
        menu = Menu(self, tearoff=0)
        
        # Benutzer-Info
        menu.add_command(label=f"👤 {self.current_user['name']}", 
                        state="disabled")
        menu.add_command(label=f"📧 {self.current_user['email']}", 
                        state="disabled")
        menu.add_separator()
        
        # Profil bearbeiten
        menu.add_command(label="✏️ Profil bearbeiten", 
                        command=self._edit_user_profile)
        
        # Einstellungen
        menu.add_command(label="⚙️ Einstellungen", 
                        command=self._show_settings)
        
        # Menü anzeigen
        try:
            x = self.user_dropdown_btn.winfo_rootx()
            y = self.user_dropdown_btn.winfo_rooty() + self.user_dropdown_btn.winfo_height()
            menu.post(x, y)
        except:
            pass
    
    # Event-Handler
    def _create_new_chat(self):
        """Erstellt einen neuen Chat."""
        try:
            app = self.get_app_instance()
            if app:
                app._create_new_chat_window()
                logger.info("Neuer Chat über Toolbar erstellt")
            elif hasattr(self.chat_window, '_create_new_chat'):
                self.chat_window._create_new_chat()
                logger.info("Neuer Chat über Chat-Fenster erstellt")
            else:
                logger.warning("Keine App-Instanz oder Chat-Fenster für neuen Chat verfügbar")
                messagebox.showwarning("Info", "Neuer Chat kann nicht erstellt werden.\nStellen Sie sicher, dass die Anwendung korrekt gestartet wurde.")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen eines neuen Chats: {e}")
    
    def _open_chat(self):
        """Öffnet einen existierenden Chat."""
        try:
            app = self.get_app_instance()
            if app:
                app._open_chat_dialog()
            elif hasattr(self.chat_window, '_open_chat'):
                self.chat_window._open_chat()
        except Exception as e:
            logger.error(f"Fehler beim Öffnen eines Chats: {e}")
    
    def _save_chat(self):
        """Speichert den aktuellen Chat."""
        if hasattr(self.chat_window, 'save_chat'):
            self.chat_window.save_chat()
    
    def _export_chat(self):
        """Exportiert den Chat als Textdatei."""
        if hasattr(self.chat_window, '_export_chat'):
            self.chat_window._export_chat()
    
    def _clear_chat(self):
        """Löscht den Chat-Verlauf."""
        if hasattr(self.chat_window, '_clear_chat'):
            self.chat_window._clear_chat()
    
    def _show_detailed_sources(self):
        """Zeigt detaillierte Quelleninformationen."""
        if hasattr(self.chat_window, '_show_detailed_sources'):
            self.chat_window._show_detailed_sources()
    
    def _check_api_status(self):
        """Prüft den API-Status manuell."""
        self._check_api_status_async()
    
    def _check_api_status_async(self):
        """Prüft den API-Status asynchron."""
        import threading
        import requests
        
        def check_status():
            try:
                from config import API_BASE_URL
                response = requests.get(f"{API_BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    # Verwende try-except für Thread-Safety
                    try:
                        self.after(0, lambda: self._update_api_status(True))
                    except RuntimeError:
                        # Main thread ist nicht im main loop - ignorieren
                        pass
                else:
                    try:
                        self.after(0, lambda: self._update_api_status(False))
                    except RuntimeError:
                        # Main thread ist nicht im main loop - ignorieren
                        pass
            except:
                try:
                    self.after(0, lambda: self._update_api_status(False))
                except RuntimeError:
                    # Main thread ist nicht im main loop - ignorieren
                    pass
        
        threading.Thread(target=check_status, daemon=True).start()
    
    def _update_api_status(self, is_online):
        """Aktualisiert den API-Status-Button."""
        if hasattr(self, 'api_status_btn'):
            if is_online:
                self.api_status_btn.config(text="🟢")
                tooltip_text = "API ist erreichbar"
            else:
                self.api_status_btn.config(text="🔴")
                tooltip_text = "API ist nicht erreichbar"
            
            # Tooltip mit der Tooltip-Klasse aktualisieren
            # Entferne alte Bindings falls vorhanden
            try:
                self.api_status_btn.unbind("<Enter>")
                self.api_status_btn.unbind("<Leave>")
            except:
                pass
            
            # Neues Tooltip setzen
            Tooltip(self.api_status_btn, tooltip_text)
    
    def _switch_to_chat(self, target_window):
        """Wechselt zu einem anderen Chat-Fenster."""
        try:
            if target_window and hasattr(target_window, 'winfo_exists') and target_window.winfo_exists():
                target_window.lift()
                target_window.focus_force()
        except Exception as e:
            logger.error(f"Fehler beim Wechseln zum Chat-Fenster: {e}")
    
    def _search_in_chat(self, event=None):
        """Sucht im aktuellen Chat."""
        search_term = self.search_var.get().strip()
        if not search_term or not hasattr(self.chat_window, '_search_in_chat'):
            return
        self.chat_window._search_in_chat(search_term)
    
    def _edit_user_profile(self):
        """Öffnet Dialog zum Bearbeiten des Benutzerprofils."""
        try:
            if hasattr(self.chat_window, '_edit_user_profile'):
                self.chat_window._edit_user_profile()
            else:
                messagebox.showinfo("Profil", "Profil-Bearbeitung noch nicht implementiert")
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Profil-Dialogs: {e}")
    
    def _show_settings(self):
        """Zeigt Einstellungen."""
        messagebox.showinfo("Einstellungen", 
                          "Einstellungen-Dialog ist noch nicht implementiert.")
    
    def _show_info(self):
        """Zeigt Programm-Informationen."""
        messagebox.showinfo("Info", 
                          "Veritas Chat v3.1.0\n\n"
                          "RAG-basiertes Chat-System mit\n"
                          "Multi-Datenbank Support")
    
    def _quit_app(self):
        """Beendet die Anwendung."""
        if hasattr(self.chat_window, 'veritas_app'):
            # Hauptfenster-Schließ-Logik
            self.chat_window._on_main_close()
        else:
            # Normales Chat-Fenster schließen
            self.chat_window._on_close()
    
    def update_user_display(self):
        """Aktualisiert die Benutzer-Anzeige."""
        if hasattr(self, 'user_btn'):
            user_text = f"{self.current_user['avatar']} {self.current_user['name']}"
            self.user_btn.config(text=user_text)
    
    def set_status(self, message, message_type="info"):
        """Setzt den Status mit Theme-passender Farbe."""
        if hasattr(self, 'status_label'):
            # Theme-basierte Farben verwenden
            style_map = {
                "info": "Info.TLabel",
                "success": "Success.TLabel", 
                "warning": "Warning.TLabel",
                "error": "Error.TLabel"
            }
            style = style_map.get(message_type, "TLabel")
            self.status_label.config(text=message, style=style)
