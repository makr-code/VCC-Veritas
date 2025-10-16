#!/usr/bin/env python3
"""
VERITAS APP STREAMING INTEGRATION TEST
=====================================
Minimale Integration der Streaming-Funktionalität in veritas_app.py
ohne Architektur-Änderung

ANWENDUNG:
1. Diese Datei zeigt wie das Streaming-System in veritas_app.py integriert wird
2. Nur 3 kleine Änderungen in bestehender ChatWindowBase nötig
3. Vollständig optional - funktioniert mit/ohne Streaming

Author: VERITAS System  
Date: 2025-09-21
"""

import sys
import os
import threading
import tkinter as tk

# === MINIMAL INTEGRATION BEISPIEL ===

# ===== 1. IMPORTS ERWEITERN (in veritas_app.py oben hinzufügen) =====

# Streaming Integration (OPTIONAL)
try:
    from backend.services.veritas_streaming_service import (
        VeritasStreamingService, StreamingUIMixin, StreamingMessageType,
        setup_streaming_chat_tags
    )
    STREAMING_AVAILABLE = True
    print("✅ Streaming Service verfügbar")
except ImportError as e:
    print(f"⚠️ Streaming Service nicht verfügbar: {e}")
    STREAMING_AVAILABLE = False
    
    # Fallback Mixin (leere Implementierung)
    class StreamingUIMixin:
        def __init__(self): pass
        def init_streaming_ui(self, parent): pass
        def setup_streaming_integration(self, window_id, thread_manager): pass
        def _handle_streaming_message(self, message): pass
        def start_streaming_query(self, query, session_id): pass

# ===== 2. CHATWINDOWBASE MODIFIKATION =====

class ChatWindowBaseStreaming:
    """
    Beispiel für erweiterte ChatWindowBase mit optionalem Streaming
    
    ÄNDERUNGEN:
    1. Erbe von StreamingUIMixin (wenn verfügbar)
    2. Rufe self.setup_streaming_integration() in __init__ auf
    3. Erweitere _handle_message() um Streaming-Nachrichten
    """
    
    def __init__(self, window_id, thread_manager, parent=None):
        # === BESTEHENDE INITIALISIERUNG (unverändert) ===
        self.window_id = window_id
        self.thread_manager = thread_manager
        self.parent = parent
        self.chat_messages = []
        
        # Session-ID für API-Kommunikation
        from datetime import datetime
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{window_id}"
        self.selected_llm = "llama3.1:8b"
        
        # Thread-spezifische Queue
        self.queue = thread_manager.create_thread_queue(window_id)
        self.message_queue = self.queue
        
        # GUI-Komponenten
        self.window = None
        self.chat_text = None
        self.input_text = None
        self.status_var = None
        
        # === STREAMING INTEGRATION (nur 1 Zeile!) ===
        if STREAMING_AVAILABLE:
            self.setup_streaming_integration(window_id, thread_manager)
        
        print(f"✅ ChatWindowBase {window_id} initialisiert (Streaming: {STREAMING_AVAILABLE})")
    
    def create_gui(self):
        """Erstellt GUI mit optionaler Streaming-UI"""
        import tkinter as tk
        from tkinter import ttk, scrolledtext
        
        # === BESTEHENDE GUI-ERSTELLUNG ===
        self.window = tk.Toplevel() if self.parent else tk.Tk()
        self.window.title(f"VERITAS Chat - {self.window_id}")
        self.window.geometry("800x600")
        
        # Hauptframe
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Chat-Display
        self.chat_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            height=20,
            state=tk.DISABLED
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # === STREAMING-UI INTEGRATION (optional) ===
        if STREAMING_AVAILABLE and hasattr(self, 'init_streaming_ui'):
            try:
                self.init_streaming_ui(main_frame)
                print(f"✅ Streaming-UI für {self.window_id} initialisiert")
            except Exception as e:
                print(f"⚠️ Streaming-UI-Fehler: {e}")
        
        # Input-Frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Text-Input
        self.input_text = tk.Text(input_frame, height=3, wrap=tk.WORD)
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Send-Button
        send_button = ttk.Button(
            input_frame,
            text="Senden",
            command=self._send_message
        )
        send_button.pack(side=tk.RIGHT)
        
        # === STREAMING CHAT TAGS (optional) ===
        if STREAMING_AVAILABLE:
            try:
                setup_streaming_chat_tags(self.chat_text)
                print(f"✅ Streaming Chat-Tags für {self.window_id} eingerichtet")
            except Exception as e:
                print(f"⚠️ Chat-Tags-Fehler: {e}")
        
        # Basis-Tags für normalen Chat
        self.chat_text.tag_config("user", foreground="#0066CC", font=('Arial', 10, 'bold'))
        self.chat_text.tag_config("assistant", foreground="#006600", font=('Arial', 10))
        self.chat_text.tag_config("system", foreground="#666666", font=('Arial', 8, 'italic'))
    
    def _handle_message(self, message):
        """Erweiterte Message-Handler mit Streaming-Support"""
        
        # === BESTEHENDE MESSAGE-BEHANDLUNG ===
        if hasattr(message, 'msg_type'):
            msg_type = message.msg_type
            
            if msg_type == "CHAT_MESSAGE":
                self._display_chat_message(message)
            elif msg_type == "STATUS_MESSAGE":
                self._update_status(message.data.get('status', ''))
            elif msg_type == "BACKEND_RESPONSE":
                self._handle_backend_response(message)
                
                # === STREAMING MESSAGE BEHANDLUNG (nur 1 Zeile!) ===
                if STREAMING_AVAILABLE and hasattr(self, '_handle_streaming_message'):
                    try:
                        self._handle_streaming_message(message)
                    except Exception as e:
                        print(f"⚠️ Streaming-Message-Fehler: {e}")
        
        print(f"✅ Message verarbeitet in {self.window_id}: {type(message)}")
    
    def _send_message(self):
        """Sendet Nachricht mit optionalem Streaming"""
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            return
        
        # Input leeren
        self.input_text.delete("1.0", tk.END)
        
        # User-Nachricht anzeigen
        self._display_chat_message_simple("user", text)
        
        # === STREAMING OPTION PRÜFEN ===
        use_streaming = STREAMING_AVAILABLE and hasattr(self, 'start_streaming_query')
        
        if use_streaming:
            try:
                # Streaming-Query starten
                result = self.start_streaming_query(text, self.session_id)
                if result.get('success'):
                    print(f"✅ Streaming gestartet für: {text[:50]}...")
                    return
                else:
                    print(f"⚠️ Streaming fehlgeschlagen: {result.get('error')}")
            except Exception as e:
                print(f"⚠️ Streaming-Fehler: {e}")
        
        # === FALLBACK: NORMALE API-ANFRAGE ===
        self._send_normal_query(text)
    
    def _send_normal_query(self, text):
        """Standard-API-Anfrage ohne Streaming"""
        import requests
        import threading
        
        def api_request():
            try:
                response = requests.post(
                    "http://127.0.0.1:5000/api/query",
                    json={
                        'query': text,
                        'session_id': self.session_id,
                        'llm_model': self.selected_llm
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self._display_chat_message_simple("assistant", data.get('answer', 'Keine Antwort'))
                else:
                    self._display_chat_message_simple("system", f"API-Fehler: {response.status_code}")
                    
            except Exception as e:
                self._display_chat_message_simple("system", f"Fehler: {str(e)}")
        
        # API-Request in separatem Thread
        thread = threading.Thread(target=api_request, daemon=True)
        thread.start()
    
    def _display_chat_message_simple(self, role, content):
        """Einfache Chat-Nachricht-Anzeige"""
        if not self.chat_text:
            return
            
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"{role.upper()}: {content}\n\n")
        self.chat_text.tag_add(role, f"end-{len(content)+4}c", f"end-4c")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)
    
    def _display_chat_message(self, message):
        """Kompatible Chat-Message-Anzeige"""
        data = message.data if hasattr(message, 'data') else {}
        role = data.get('role', 'system')
        content = data.get('content', str(message))
        self._display_chat_message_simple(role, content)
    
    def _handle_backend_response(self, message):
        """Backend-Response verarbeiten"""
        data = message.data if hasattr(message, 'data') else {}
        content = data.get('content', data.get('answer', str(message)))
        self._display_chat_message_simple("assistant", content)
    
    def _update_status(self, status):
        """Status-Update"""
        if hasattr(self, 'status_var') and self.status_var:
            self.status_var.set(status)
        print(f"Status {self.window_id}: {status}")

# ===== STREAMING MIXIN INTEGRATION =====

# Mix StreamingUIMixin dynamisch ein
if STREAMING_AVAILABLE:
    class ChatWindowBaseStreaming(ChatWindowBaseStreaming, StreamingUIMixin):
        def __init__(self, window_id, thread_manager, parent=None):
            # Streaming-UI initialisieren
            StreamingUIMixin.__init__(self)
            # Basis-Chat-Window initialisieren
            super().__init__(window_id, thread_manager, parent)

# ===== TEST ANWENDUNG =====

def test_streaming_integration():
    """Testet die Streaming-Integration"""
    
    print("🚀 VERITAS Streaming Integration Test")
    print("=" * 50)
    
    # Mock Thread-Manager für Test
    class MockThreadManager:
        def __init__(self):
            self.shutdown_event = threading.Event()
            self.queues = {}
        
        def create_thread_queue(self, window_id):
            import queue
            self.queues[window_id] = queue.Queue()
            return self.queues[window_id]
        
        def register_thread(self, window_id, thread):
            pass
    
    # Test mit Mock-Manager
    thread_manager = MockThreadManager()
    
    try:
        # Chat-Window erstellen
        chat_window = ChatWindowBaseStreaming("test_window", thread_manager)
        
        print(f"✅ Chat-Window erstellt: {chat_window.window_id}")
        print(f"✅ Streaming verfügbar: {STREAMING_AVAILABLE}")
        
        if STREAMING_AVAILABLE:
            print(f"✅ Streaming-Service: {hasattr(chat_window, 'streaming_service')}")
            print(f"✅ Streaming-UI: {hasattr(chat_window, 'init_streaming_ui')}")
        
        # GUI erstellen
        chat_window.create_gui()
        print("✅ GUI erstellt")
        
        # Test-Message
        class TestMessage:
            def __init__(self):
                self.msg_type = "CHAT_MESSAGE"
                self.data = {'role': 'user', 'content': 'Test-Nachricht'}
        
        chat_window._handle_message(TestMessage())
        print("✅ Message-Handler funktioniert")
        
        return True
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test durchführen
    success = test_streaming_integration()
    
    if success:
        print("\n🎉 STREAMING INTEGRATION ERFOLGREICH!")
        print("\nNächste Schritte:")
        print("1. Kopiere die Änderungen in deine veritas_app.py")
        print("2. Erweitere ChatWindowBase um StreamingUIMixin")
        print("3. Starte Backend-Server mit veritas_api_backend.py")
        print("4. Teste Streaming-Funktionalität")
    else:
        print("\n❌ Test fehlgeschlagen - prüfe Abhängigkeiten")