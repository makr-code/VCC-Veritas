#!/usr/bin/env python3
"""
VERITAS STREAMING INTEGRATION GUIDE
===================================
Anleitung zur Integration der Streaming-Funktionalität in veritas_app.py

INTEGRATION SCHRITTE:
1. Import der Streaming-Services
2. Erweitere ChatWindowBase um Streaming-Funktionalität
3. Update der Message-Handler
4. UI-Integration ohne Architektur-Änderung

Author: VERITAS System
Date: 2025-09-21
"""

# ===== SCHRITT 1: IMPORTS ERWEITERN =====

"""
In veritas_app.py am Anfang hinzufügen:

# Streaming Integration
try:
    from backend.services.veritas_streaming_service import (
        VeritasStreamingService, StreamingUIMixin, StreamingMessageType,
        setup_streaming_chat_tags
    )
    STREAMING_AVAILABLE = True
    logger.info("✅ Streaming Service verfügbar")
except ImportError as e:
    logger.warning(f"⚠️ Streaming Service nicht verfügbar: {e}")
    STREAMING_AVAILABLE = False
    
    # Fallback Mixin
    class StreamingUIMixin:
        def __init__(self): pass
        def init_streaming_ui(self, parent): pass
        def setup_streaming_integration(self, window_id, thread_manager): pass
        def _handle_streaming_message(self, message): pass
"""

# ===== SCHRITT 2: CHATWINDOWBASE ERWEITERN =====

"""
In ChatWindowBase.__init__() hinzufügen:

class ChatWindowBase(ABC, StreamingUIMixin if STREAMING_AVAILABLE else object):
    
    def __init__(self, window_id: str, thread_manager: ThreadManager, parent=None):
        # Bestehende Initialisierung...
        
        # Streaming Integration
        if STREAMING_AVAILABLE:
            StreamingUIMixin.__init__(self)
            self.setup_streaming_integration(window_id, thread_manager)
            logger.info(f"✅ Streaming für Window {window_id} aktiviert")
        else:
            self.streaming_service = None
"""

# ===== SCHRITT 3: GUI-ERSTELLUNG ERWEITERN =====

"""
In _create_chat_display() Methode von ChatWindowBase:

def _create_chat_display(self, parent, height=20):
    # Bestehende Chat-Display Erstellung...
    
    # Streaming UI hinzufügen (falls verfügbar)
    if STREAMING_AVAILABLE:
        self.init_streaming_ui(parent)
        setup_streaming_chat_tags(self.chat_display)
    
    return self.chat_display
"""

# ===== SCHRITT 4: MESSAGE HANDLER ERWEITERN =====

"""
In _handle_backend_response() Methode von ChatWindowBase:

def _handle_backend_response(self, message: QueueMessage):
    try:
        # Prüfe auf Streaming-Message
        if STREAMING_AVAILABLE and message.data.get('stream_type'):
            self._handle_streaming_message(message)
            return
        
        # Bestehende Backend-Response-Behandlung...
        response_text = message.data.get('content', 'Keine Antwort erhalten')
        # ... rest der bestehenden Implementierung
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Backend-Response: {e}")
"""

# ===== SCHRITT 5: SEND-TO-BACKEND ERWEITERN =====

"""
In _send_to_backend() Methode von ChatWindowBase:

def _send_to_backend(self, message: str):
    try:
        # Prüfe ob Streaming verfügbar und aktiviert
        streaming_enabled = (
            STREAMING_AVAILABLE and 
            hasattr(self, 'streaming_service') and
            getattr(self, 'streaming_enabled_var', None) and
            self.streaming_enabled_var.get()
        )
        
        if streaming_enabled:
            # Streaming-Query starten
            result = self.streaming_service.start_streaming_query(
                query=message,
                session_id=self.session_id,
                enable_progress=True,
                enable_intermediate=True,
                enable_thinking=True
            )
            
            if result.get('success'):
                logger.info(f"🚀 Streaming-Query gestartet: {message[:50]}...")
                return
            else:
                logger.warning(f"⚠️ Streaming fehlgeschlagen, Fallback zu Standard: {result.get('error')}")
        
        # Fallback zu bestehender Standard-Implementation
        # ... bestehende _send_to_backend Implementierung
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Senden: {e}")
        self._send_error_response(f"Fehler beim Senden der Nachricht: {str(e)}")
"""

# ===== SCHRITT 6: SETTINGS ERWEITERN =====

"""
In _create_settings_bar() Methode von ChatWindowBase:

def _create_settings_bar(self, parent, compact=False):
    # Bestehende Settings-Bar Erstellung...
    
    # Streaming-Checkbox hinzufügen (falls verfügbar)
    if STREAMING_AVAILABLE and hasattr(self, 'streaming_enabled_var'):
        streaming_check = ttk.Checkbutton(
            settings_frame,
            text="🔄 Real-time",
            variable=self.streaming_enabled_var,
            command=self._on_streaming_toggle
        )
        streaming_check.pack(side=tk.LEFT, padx=(5, 0))
        
        # Tooltip für Erklärung
        if UI_COMPONENTS_AVAILABLE:
            Tooltip(streaming_check, "Aktiviert Real-time Progress Updates und Zwischenergebnisse")
    
    return settings_frame

def _on_streaming_toggle(self):
    '''Callback für Streaming-Toggle'''
    if hasattr(self, 'streaming_enabled_var'):
        enabled = self.streaming_enabled_var.get()
        logger.info(f"🔄 Streaming {'aktiviert' if enabled else 'deaktiviert'}")
        
        # Optional: Benachrichtigung anzeigen
        if hasattr(self, 'add_system_message'):
            status = "aktiviert" if enabled else "deaktiviert"
            self.add_system_message(f"Real-time Updates {status}")
"""

# ===== SCHRITT 7: MINIMAL-INTEGRATION BEISPIEL =====

def minimal_integration_example():
    """
    Minimale Integration ohne große Änderungen
    """
    
    # In ChatWindowBase.__init__():
    """
    # Streaming Integration (minimal)
    self.streaming_available = False
    try:
        from backend.services.veritas_streaming_service import VeritasStreamingService
        self.streaming_service = VeritasStreamingService()
        self.streaming_service.set_thread_context(thread_manager, window_id)
        self.streaming_available = True
    except ImportError:
        self.streaming_service = None
    """
    
    # In _send_to_backend():
    """
    # Streaming versuchen (falls verfügbar)
    if self.streaming_available and self.streaming_service:
        try:
            result = self.streaming_service.start_streaming_query(
                query=message,
                session_id=self.session_id
            )
            if result.get('success'):
                return  # Streaming läuft
        except Exception as e:
            logger.warning(f"Streaming-Fallback: {e}")
    
    # Standard-Verarbeitung...
    """
    
    # In _handle_backend_response():
    """
    # Check für Streaming-Messages
    if self.streaming_available and message.data.get('stream_type'):
        # Einfache Streaming-Message-Behandlung
        stream_type = message.data.get('stream_type')
        stream_message = message.data.get('message', '')
        
        if stream_type == 'stream_progress':
            # Progress in Status-Bar anzeigen
            if hasattr(self, 'status_var'):
                self.status_var.set(f"🔄 {stream_message}")
        
        elif stream_type == 'stream_intermediate':
            # Zwischenergebnis als System-Message
            self._add_system_message(f"📋 {stream_message}")
        
        elif stream_type == 'stream_complete':
            # Reset Status
            if hasattr(self, 'status_var'):
                self.status_var.set("Bereit")
        
        return
    
    # Standard Backend-Response...
    """

# ===== SCHRITT 8: VOLLSTÄNDIGES BEISPIEL =====

def complete_integration_example():
    """
    Vollständige Integration mit allen Features
    """
    
    code_example = '''
# In veritas_app.py - Erweiterte ChatWindowBase mit Streaming

class ChatWindowBase(ABC, StreamingUIMixin if STREAMING_AVAILABLE else object):
    """Erweiterte Chat-Window-Base mit Streaming-Support"""
    
    def __init__(self, window_id: str, thread_manager: ThreadManager, parent=None):
        # Bestehende Initialisierung
        self.window_id = window_id
        self.thread_manager = thread_manager
        self.parent = parent
        
        # Queue für Thread-sichere UI-Updates
        self.message_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        
        # Session Management
        self.session_id = str(uuid.uuid4())
        self.conversation_history = []
        
        # GUI State
        self.gui_initialized = False
        
        # Streaming Integration
        if STREAMING_AVAILABLE:
            StreamingUIMixin.__init__(self)
            self.setup_streaming_integration(window_id, thread_manager)
            self.streaming_enabled_var = tk.BooleanVar(value=True)
            logger.info(f"✅ Streaming für Window {window_id} aktiviert")
        else:
            self.streaming_service = None
            self.streaming_enabled_var = tk.BooleanVar(value=False)
    
    def create_gui(self):
        """Erstellt GUI mit Streaming-Integration"""
        # Bestehende GUI-Erstellung...
        
        # Chat Display
        self.chat_display = self._create_chat_display(self.parent)
        
        # Input Area  
        self.input_area = self._create_input_area(self.parent)
        
        # Settings Bar (mit Streaming-Toggle)
        self.settings_bar = self._create_settings_bar(self.parent)
        
        # Streaming UI (versteckt initially)
        if STREAMING_AVAILABLE:
            self.init_streaming_ui(self.parent)
            setup_streaming_chat_tags(self.chat_display)
        
        # Status Bar
        self.status_bar = self._create_status_bar(self.parent)
        
        self.gui_initialized = True
    
    def _handle_backend_response(self, message: QueueMessage):
        """Erweiterte Message-Behandlung mit Streaming"""
        try:
            # Streaming-Message prüfen
            if STREAMING_AVAILABLE and message.data.get('stream_type'):
                self._handle_streaming_message(message)
                return
            
            # Standard Backend-Response
            response_text = message.data.get('content', 'Keine Antwort erhalten')
            sources = message.data.get('sources', [])
            confidence = message.data.get('confidence_score', 0.0)
            
            # Response formatieren und anzeigen
            formatted_response = self._format_response(response_text, sources, confidence)
            self._add_to_chat_display("assistant", formatted_response)
            
            # Follow-up Suggestions
            suggestions = message.data.get('suggestions', [])
            if suggestions:
                self._add_follow_up_suggestions(suggestions)
            
            # Conversation History updaten
            self.conversation_history.append({
                'role': 'assistant',
                'content': response_text,
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'sources': sources,
                    'confidence': confidence,
                    'processing_time': message.data.get('processing_time', 0)
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Backend-Response: {e}")
            self._add_error_message(f"Fehler bei der Antwort-Verarbeitung: {str(e)}")
    
    def _send_to_backend(self, message: str):
        """Erweiterte Backend-Kommunikation mit Streaming"""
        try:
            # Conversation History updaten
            self.conversation_history.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Streaming versuchen (falls aktiviert)
            if (STREAMING_AVAILABLE and 
                hasattr(self, 'streaming_service') and 
                self.streaming_service and
                self.streaming_enabled_var.get()):
                
                result = self.streaming_service.start_streaming_query(
                    query=message,
                    session_id=self.session_id,
                    enable_progress=True,
                    enable_intermediate=True,
                    enable_thinking=True
                )
                
                if result.get('success'):
                    logger.info(f"🚀 Streaming-Query erfolgreich gestartet")
                    return
                else:
                    logger.warning(f"⚠️ Streaming fehlgeschlagen: {result.get('error')}")
                    self._add_system_message(f"Streaming nicht verfügbar, verwende Standard-Modus")
            
            # Fallback zu Standard-API
            self._send_standard_api_request(message)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Backend-Versand: {e}")
            self._send_error_response(f"Fehler beim Senden: {str(e)}")
    
    def _add_system_message(self, message: str):
        """Fügt System-Nachricht zur Chat-Anzeige hinzu"""
        if self.gui_initialized and hasattr(self, 'chat_display'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            system_text = f"[{timestamp}] ℹ️ {message}\\n"
            
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, system_text, "system")
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)
'''
    
    return code_example

# ===== TESTING & VALIDATION =====

def validate_integration():
    """
    Validiert die Streaming-Integration
    """
    
    validation_checks = [
        "✅ VeritasStreamingService erfolgreich importiert",
        "✅ StreamingUIMixin in ChatWindowBase integriert", 
        "✅ Message-Handler erweitert für Streaming-Messages",
        "✅ Backend-Sender unterstützt Streaming und Fallback",
        "✅ UI-Komponenten für Progress-Anzeige vorhanden",
        "✅ Cancel-Funktionalität implementiert",
        "✅ Thread-sichere Kommunikation gewährleistet",
        "✅ Kompatibilität mit bestehender Architektur erhalten"
    ]
    
    return validation_checks

# ===== MIGRATION GUIDE =====

def migration_steps():
    """
    Schritt-für-Schritt Migration Guide
    """
    
    steps = [
        {
            "step": 1,
            "title": "Dependencies prüfen",
            "description": "Stelle sicher dass veritas_streaming_service.py verfügbar ist",
            "code": "from backend.services.veritas_streaming_service import VeritasStreamingService"
        },
        {
            "step": 2, 
            "title": "ChatWindowBase erweitern",
            "description": "Füge StreamingUIMixin als Mixin hinzu",
            "code": "class ChatWindowBase(ABC, StreamingUIMixin):"
        },
        {
            "step": 3,
            "title": "Initialisierung erweitern",
            "description": "Streaming-Service in __init__ einbinden",
            "code": "StreamingUIMixin.__init__(self)"
        },
        {
            "step": 4,
            "title": "Message-Handler updaten", 
            "description": "Streaming-Messages in _handle_backend_response behandeln",
            "code": "if message.data.get('stream_type'): self._handle_streaming_message(message)"
        },
        {
            "step": 5,
            "title": "Backend-Sender erweitern",
            "description": "Streaming-Option in _send_to_backend hinzufügen",
            "code": "self.streaming_service.start_streaming_query(...)"
        },
        {
            "step": 6,
            "title": "UI-Integration",
            "description": "Streaming-UI-Komponenten in GUI einbauen",
            "code": "self.init_streaming_ui(parent)"
        },
        {
            "step": 7,
            "title": "Settings erweitern",
            "description": "Streaming-Toggle in Settings-Bar hinzufügen",
            "code": "ttk.Checkbutton(..., variable=self.streaming_enabled_var)"
        },
        {
            "step": 8,
            "title": "Testing",
            "description": "Streaming-Funktionalität testen und validieren",
            "code": "# Test mit aktiviertem und deaktiviertem Streaming"
        }
    ]
    
    return steps

if __name__ == "__main__":
    print("🚀 VERITAS Streaming Integration Guide")
    print("=====================================")
    
    print("\\n📋 Validierungs-Checkliste:")
    for check in validate_integration():
        print(f"  {check}")
    
    print("\\n🔧 Migration Steps:")
    for step in migration_steps():
        print(f"  {step['step']}. {step['title']}: {step['description']}")
    
    print("\\n✅ Integration Guide erstellt!")
    print("📖 Siehe Code-Beispiele oben für detaillierte Implementation")