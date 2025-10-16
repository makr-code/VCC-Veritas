#!/usr/bin/env python3
"""
VERITAS STREAMING SERVICE
========================
Modulare Streaming-Integration für bestehende veritas_app.py Architektur

Features:
- Clean Integration in ChatWindowBase
- Thread-sichere Kommunikation mit ThreadManager
- UI-getrennte Backend-Services
- Cancel-Funktionalität
- Progress-Updates über bestehende Queue-System

Author: VERITAS System
Date: 2025-09-21
"""

import asyncio
import logging
import threading
import time
import json
import requests
import queue
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum

# Import bestehende VERITAS Core Komponenten
try:
    from shared.core.veritas_core import (
        MessageType, QueueMessage, ChatMessage, StatusMessage, BackendResponse,
        ThreadManager
    )
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False

# Import Streaming Progress System
try:
    from shared.pipelines.veritas_streaming_progress import (
        ProgressStage, ProgressType, VeritasProgressManager
    )
    STREAMING_PROGRESS_AVAILABLE = True
except ImportError:
    STREAMING_PROGRESS_AVAILABLE = False

logger = logging.getLogger(__name__)

# ===== STREAMING MESSAGE TYPES =====

class StreamingMessageType(Enum):
    """Erweiterte Message-Typen für Streaming"""
    STREAM_START = "stream_start"
    STREAM_PROGRESS = "stream_progress"
    STREAM_INTERMEDIATE = "stream_intermediate"
    STREAM_THINKING = "stream_thinking"
    STREAM_REFLECTION = "stream_reflection"  # NEU: Stage Reflection
    STREAM_COMPLETE = "stream_complete"
    STREAM_CANCELLED = "stream_cancelled"
    STREAM_ERROR = "stream_error"

@dataclass
class StreamingMessage(QueueMessage):
    """Streaming-spezifische Nachrichten für Queue-System"""
    def __init__(self, sender_id: str, stream_type: StreamingMessageType, **kwargs):
        super().__init__(
            msg_type=MessageType.BACKEND_RESPONSE,  # Kompatibel mit bestehendem System
            sender_id=sender_id,
            timestamp=datetime.now().timestamp(),
            data={
                'stream_type': stream_type.value,
                'session_id': kwargs.get('session_id'),
                'stage': kwargs.get('stage'),
                'progress': kwargs.get('progress', 0),
                'message': kwargs.get('message', ''),
                'details': kwargs.get('details', {}),
                'agent_type': kwargs.get('agent_type'),
                'intermediate_result': kwargs.get('intermediate_result'),
                'thinking_step': kwargs.get('thinking_step'),
                'can_cancel': kwargs.get('can_cancel', True),
                **kwargs
            }
        )

# ===== STREAMING BACKEND SERVICE =====

class VeritasStreamingService:
    """
    Backend-Service für Streaming-Integration
    
    INTEGRATION in ChatWindowBase:
    - Ersetzt/erweitert _send_to_backend() Methode
    - Nutzt bestehende ThreadManager Queue-Kommunikation
    - Thread-sichere Progress-Updates
    - Kompatibel mit bestehender Session-Verwaltung
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.cancelled_sessions: set = set()
        self._lock = threading.Lock()
        
        # Integration mit ThreadManager
        self.thread_manager: Optional[ThreadManager] = None
        self.window_id: Optional[str] = None
        
        logger.info("✅ VeritasStreamingService initialisiert")
    
    def set_thread_context(self, thread_manager: ThreadManager, window_id: str):
        """Setzt Thread-Kontext für Queue-Kommunikation"""
        self.thread_manager = thread_manager
        self.window_id = window_id
        logger.info(f"🔗 Streaming Service an Window {window_id} gebunden")
    
    def start_streaming_query(
        self, 
        query: str, 
        session_id: str,
        enable_progress: bool = True,
        enable_intermediate: bool = True,
        enable_thinking: bool = True,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Startet Streaming-Query und gibt Stream-Info zurück
        
        Args:
            query: Benutzer-Query
            session_id: Session-ID für Kontext
            enable_progress: Progress-Updates aktivieren
            enable_intermediate: Zwischenergebnisse aktivieren
            enable_thinking: LLM-Thinking aktivieren
            conversation_history: Chat-Verlauf für Kontext (Liste von {'role': 'user|assistant', 'content': '...'})
            
        Returns:
            Stream-Informationen oder Error
        """
        try:
            # 🆕 Prepare request payload mit conversation_history
            payload = {
                "query": query,
                "session_id": session_id,
                "enable_streaming": enable_progress,
                "enable_intermediate_results": enable_intermediate,
                "enable_llm_thinking": enable_thinking
            }
            
            # Füge conversation_history hinzu wenn vorhanden
            if conversation_history:
                payload["conversation_history"] = conversation_history
            
            # API-Request senden
            response = requests.post(
                f"{self.base_url}/v2/query/stream",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                stream_info = response.json()
                stream_session_id = stream_info["session_id"]
                
                # Stream-Info speichern
                with self._lock:
                    self.active_streams[stream_session_id] = {
                        'query': query,
                        'veritas_session_id': session_id,
                        'start_time': time.time(),
                        'status': 'active'
                    }
                
                # Progress-Stream in separatem Thread starten
                self._start_progress_monitoring(stream_session_id)
                
                # Start-Nachricht an UI senden
                self._send_streaming_message(
                    stream_type=StreamingMessageType.STREAM_START,
                    session_id=session_id,
                    message=f"🚀 Streaming gestartet für: {query[:50]}...",
                    details={
                        'stream_session_id': stream_session_id,
                        'estimated_time': stream_info.get('estimated_time', 'unbekannt'),
                        'stream_url': stream_info.get('stream_url')
                    }
                )
                
                return {
                    'success': True,
                    'stream_session_id': stream_session_id,
                    'stream_info': stream_info
                }
            else:
                error_msg = f"Streaming-Start fehlgeschlagen: {response.status_code}"
                self._send_streaming_message(
                    stream_type=StreamingMessageType.STREAM_ERROR,
                    session_id=session_id,
                    message=error_msg
                )
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            error_msg = f"Streaming-Fehler: {str(e)}"
            logger.error(error_msg)
            
            self._send_streaming_message(
                stream_type=StreamingMessageType.STREAM_ERROR,
                session_id=session_id,
                message=error_msg
            )
            return {'success': False, 'error': error_msg}
    
    def _start_progress_monitoring(self, stream_session_id: str):
        """Startet Progress-Monitoring in separatem Thread"""
        
        def monitor_progress():
            try:
                # SSE-Stream verbinden
                stream_url = f"{self.base_url}/progress/{stream_session_id}"
                
                response = requests.get(
                    stream_url, 
                    stream=True, 
                    headers={'Accept': 'text/event-stream'},
                    timeout=60
                )
                
                # Stream-Events verarbeiten
                for line in response.iter_lines(decode_unicode=True):
                    # Prüfe auf Cancellation
                    if stream_session_id in self.cancelled_sessions:
                        logger.info(f"🛑 Stream {stream_session_id} wurde abgebrochen")
                        break
                    
                    if line.startswith('data: '):
                        try:
                            event_data = json.loads(line[6:])  # Entferne 'data: '
                            self._handle_progress_event(stream_session_id, event_data)
                        except json.JSONDecodeError:
                            continue
                
            except Exception as e:
                logger.error(f"❌ Progress-Monitor Fehler für {stream_session_id}: {e}")
                self._handle_stream_error(stream_session_id, str(e))
            
            finally:
                # Stream cleanup
                with self._lock:
                    self.active_streams.pop(stream_session_id, None)
                    self.cancelled_sessions.discard(stream_session_id)
        
        # Thread starten
        monitor_thread = threading.Thread(
            target=monitor_progress, 
            name=f"StreamMonitor-{stream_session_id}",
            daemon=True
        )
        monitor_thread.start()
    
    def _handle_progress_event(self, stream_session_id: str, event_data: Dict[str, Any]):
        """Verarbeitet Progress-Events und sendet an UI"""
        
        # Stream-Info holen
        stream_info = self.active_streams.get(stream_session_id)
        if not stream_info:
            return
        
        veritas_session_id = stream_info['veritas_session_id']
        event_type = event_data.get('type', '')
        stage = event_data.get('stage', '')
        
        # Event-spezifische Behandlung
        if event_type == 'stage_update':
            self._send_streaming_message(
                stream_type=StreamingMessageType.STREAM_PROGRESS,
                session_id=veritas_session_id,
                stage=stage,
                progress=event_data.get('progress', 0),
                message=event_data.get('message', ''),
                details=event_data.get('details', {})
            )
        
        elif event_type == 'intermediate_result':
            self._send_streaming_message(
                stream_type=StreamingMessageType.STREAM_INTERMEDIATE,
                session_id=veritas_session_id,
                message=event_data.get('message', ''),
                intermediate_result=event_data.get('details', {}),
                agent_type=event_data.get('agent_type')
            )
        
        elif event_type == 'llm_thinking':
            self._send_streaming_message(
                stream_type=StreamingMessageType.STREAM_THINKING,
                session_id=veritas_session_id,
                message=event_data.get('message', ''),
                thinking_step=event_data.get('llm_thinking', ''),
                details=event_data.get('details', {})
            )
        
        elif event_type == 'stage_reflection':
            # NEU: Stage-Reflection Event
            reflection_data = event_data.get('details', {})
            self._send_streaming_message(
                stream_type=StreamingMessageType.STREAM_REFLECTION,
                session_id=veritas_session_id,
                message=event_data.get('message', ''),
                reflection_data=reflection_data,
                details=reflection_data
            )
        
        elif event_type == 'stage_complete' and stage == 'completed':
            # Finale Antwort verarbeiten
            # FIX: details IST bereits final_result, kein verschachteltes .get() nötig
            final_result = event_data.get('details', {})
            
            self._send_streaming_message(
                stream_type=StreamingMessageType.STREAM_COMPLETE,
                session_id=veritas_session_id,
                message="✅ Verarbeitung abgeschlossen",
                final_result=final_result,  # Füge final_result hinzu für UI
                details=final_result
            )
            
            # Finale Antwort als Standard-Backend-Response senden
            self._send_final_response(veritas_session_id, final_result)
        
        elif event_type == 'error':
            self._handle_stream_error(stream_session_id, event_data.get('message', 'Unbekannter Fehler'))

    def _send_final_response(self, session_id: str, final_result: Dict[str, Any]):
        """Sendet finale Antwort als Standard-BackendResponse"""
        
        if not self.thread_manager or not self.window_id:
            return
        
        # DEBUG: Log final_result structure
        logger.info(f"📤 _send_final_response called with final_result keys: {final_result.keys() if final_result else 'EMPTY'}")
        if final_result:
            logger.info(f"📤 response_text present: {'response_text' in final_result}")
            logger.info(f"📤 response_text value: {final_result.get('response_text', 'MISSING')[:100]}...")
        
        # Konvertiere zu Standard-BackendResponse für Kompatibilität
        response_text = final_result.get('response_text', '')
        if not response_text:
            # Fallback-Strategie
            response_text = final_result.get('answer', '')
        if not response_text:
            response_text = 'Streaming-Antwort erhalten (keine response_text gefunden)'
            logger.warning(f"⚠️ Keine response_text in final_result! Keys: {final_result.keys() if final_result else 'EMPTY'}")
        
        backend_response = BackendResponse(
            sender_id="streaming_service",
            content=response_text,
            session_id=session_id,
            sources=final_result.get('sources', []),
            confidence_score=final_result.get('confidence_score', 0.8),
            suggestions=final_result.get('follow_up_suggestions', []),
            processing_time=final_result.get('processing_metadata', {}).get('processing_time', 0),
            quality_metrics=final_result.get('processing_metadata', {}),
            agent_results=final_result.get('agent_results', {}),
            worker_results=final_result.get('agent_results', {})  # Alias für Kompatibilität
        )
        
        # An UI senden über bestehende Queue
        self.thread_manager.send_message(self.window_id, backend_response)
    
    def _handle_stream_error(self, stream_session_id: str, error_message: str):
        """Behandelt Stream-Fehler"""
        
        stream_info = self.active_streams.get(stream_session_id)
        if not stream_info:
            return
        
        veritas_session_id = stream_info['veritas_session_id']
        
        self._send_streaming_message(
            stream_type=StreamingMessageType.STREAM_ERROR,
            session_id=veritas_session_id,
            message=f"❌ Stream-Fehler: {error_message}",
            can_cancel=False
        )
        
        # Fallback: Standard-Error-Response senden
        if self.thread_manager and self.window_id:
            error_response = BackendResponse(
                sender_id="streaming_service",
                content=f"Entschuldigung, bei der Streaming-Verarbeitung ist ein Fehler aufgetreten: {error_message}",
                session_id=veritas_session_id,
                error_info={'streaming_error': error_message}
            )
            self.thread_manager.send_message(self.window_id, error_response)
    
    def cancel_stream(self, stream_session_id: str) -> Dict[str, Any]:
        """
        Bricht aktiven Stream ab
        
        Args:
            stream_session_id: ID des zu abbrechenden Streams
            
        Returns:
            Cancellation-Status
        """
        try:
            # Lokale Cancellation markieren
            self.cancelled_sessions.add(stream_session_id)
            
            # Backend-Cancellation-Request
            response = requests.post(
                f"{self.base_url}/cancel/{stream_session_id}",
                json={'reason': 'user_cancelled'},
                timeout=5
            )
            
            # Stream-Info holen für Session-ID
            stream_info = self.active_streams.get(stream_session_id)
            if stream_info:
                veritas_session_id = stream_info['veritas_session_id']
                
                self._send_streaming_message(
                    stream_type=StreamingMessageType.STREAM_CANCELLED,
                    session_id=veritas_session_id,
                    message="🛑 Verarbeitung wurde abgebrochen",
                    can_cancel=False
                )
            
            if response.status_code == 200:
                cancel_data = response.json()
                return {
                    'success': True,
                    'message': cancel_data.get('message', 'Stream erfolgreich abgebrochen')
                }
            else:
                return {
                    'success': True,  # Lokale Cancellation funktioniert trotzdem
                    'message': f'Lokaler Abbruch erfolgreich (Backend: {response.status_code})'
                }
                
        except Exception as e:
            logger.error(f"Cancel-Fehler: {e}")
            return {
                'success': True,  # Lokale Cancellation
                'message': f'Lokaler Abbruch erfolgreich (Netzwerk-Fehler: {str(e)})'
            }
    
    def _send_streaming_message(self, stream_type: StreamingMessageType, **kwargs):
        """Sendet Streaming-Message an UI über ThreadManager"""
        
        if not self.thread_manager or not self.window_id:
            return
        
        streaming_msg = StreamingMessage(
            sender_id="streaming_service",
            stream_type=stream_type,
            **kwargs
        )
        
        self.thread_manager.send_message(self.window_id, streaming_msg)
    
    def get_active_streams(self) -> Dict[str, Dict[str, Any]]:
        """Gibt aktive Streams zurück"""
        with self._lock:
            return dict(self.active_streams)
    
    def is_streaming_available(self) -> bool:
        """Prüft ob Streaming verfügbar ist"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=3)
            return response.status_code == 200 and response.json().get('streaming_available', False)
        except:
            return False

# ===== STREAMING UI INTEGRATION MIXIN =====

class StreamingUIMixin:
    """
    Mixin-Klasse für UI-Integration in ChatWindowBase
    
    VERWENDUNG:
    - Als Mixin in bestehende ChatWindow-Klassen einbauen
    - Erweitert bestehende UI um Progress-Komponenten
    - Thread-sichere UI-Updates
    """
    
    def __init__(self):
        # Streaming-spezifische UI-State
        self.streaming_active = False
        self.current_stream_session = None
        self.progress_widgets = {}
        
        # Streaming Service
        self.streaming_service = VeritasStreamingService()
        
        # Import tkinter für UI
        import tkinter as tk
        self.tk = tk
        
    def init_streaming_ui(self, parent_frame):
        """Initialisiert Streaming-UI-Komponenten"""
        
        # Streaming Status Frame (standardmäßig versteckt)
        import tkinter as tk
        from tkinter import ttk
        
        self.streaming_frame = ttk.LabelFrame(
            parent_frame, 
            text="🔄 Real-time Processing", 
            padding=5
        )
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.streaming_frame,
            variable=self.progress_var,
            maximum=100,
            length=300
        )
        self.progress_bar.pack(fill=tk.X, pady=2)
        
        # Status Label
        self.stream_status_var = tk.StringVar(value="Bereit für Streaming...")
        self.stream_status_label = ttk.Label(
            self.streaming_frame,
            textvariable=self.stream_status_var,
            font=('Arial', 8)
        )
        self.stream_status_label.pack(anchor=tk.W)
        
        # Cancel Button
        self.cancel_button = ttk.Button(
            self.streaming_frame,
            text="❌ Abbrechen",
            command=self._cancel_current_stream,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Streaming Checkbox (in Settings-Bereich)
        self.streaming_enabled_var = tk.BooleanVar(value=True)
        
        # Initial verstecken
        self.streaming_frame.pack_forget()
    
    def setup_streaming_integration(self, window_id: str, thread_manager):
        """Setzt Streaming-Integration auf"""
        self.streaming_service.set_thread_context(thread_manager, window_id)
    
    def _handle_streaming_message(self, message: QueueMessage):
        """Behandelt Streaming-spezifische Messages"""
        
        if message.data.get('stream_type'):
            stream_type = message.data['stream_type']
            
            if stream_type == StreamingMessageType.STREAM_START.value:
                self._show_streaming_ui()
                self.stream_status_var.set(message.data.get('message', ''))
                self.cancel_button.config(state=self.tk.NORMAL)
                self.streaming_active = True
                self.current_stream_session = message.data.get('details', {}).get('stream_session_id')
                
            elif stream_type == StreamingMessageType.STREAM_PROGRESS.value:
                progress = message.data.get('progress', 0)
                self.progress_var.set(progress)
                self.stream_status_var.set(message.data.get('message', ''))
                
            elif stream_type == StreamingMessageType.STREAM_INTERMEDIATE.value:
                # Zwischenergebnis in Chat anzeigen
                intermediate = message.data.get('intermediate_result', {})
                agent_type = message.data.get('agent_type', 'Agent')
                
                self._add_intermediate_result(agent_type, intermediate)
                
            elif stream_type == StreamingMessageType.STREAM_THINKING.value:
                # LLM-Thinking anzeigen
                thinking_step = message.data.get('thinking_step', '')
                self._add_thinking_step(thinking_step)
            
            elif stream_type == StreamingMessageType.STREAM_REFLECTION.value:
                # NEU: Stage-Reflection anzeigen
                reflection_data = message.data.get('reflection_data', {})
                self._add_stage_reflection(reflection_data)
                
            elif stream_type in [
                StreamingMessageType.STREAM_COMPLETE.value,
                StreamingMessageType.STREAM_CANCELLED.value,
                StreamingMessageType.STREAM_ERROR.value
            ]:
                self._hide_streaming_ui()
                self.cancel_button.config(state=self.tk.DISABLED)
                self.streaming_active = False
                self.current_stream_session = None
                
                # Bei STREAM_COMPLETE: Finale Response als Backend-Response behandeln
                if stream_type == StreamingMessageType.STREAM_COMPLETE.value:
                    final_result = message.data.get('final_result', {})
                    if final_result and hasattr(self, '_handle_backend_response'):
                        # Extrahiere Antwort-Text: 'response_text' vom Backend, 'answer' als Fallback
                        answer_text = final_result.get('response_text') or final_result.get('answer', '')
                        
                        # DEBUG: Log was wir haben
                        logger.info(f"📩 STREAM_COMPLETE: answer_text length={len(answer_text) if answer_text else 0}")
                        logger.info(f"📩 STREAM_COMPLETE: final_result keys={list(final_result.keys())}")
                        
                        # Konvertiere Stream-Result zu Backend-Response-Format
                        backend_response_msg = QueueMessage(
                            sender_id="streaming_service",
                            msg_type=MessageType.BACKEND_RESPONSE,
                            data={
                                'content': answer_text,  # FIX: 'content' statt 'answer' - erwartet von _handle_backend_response
                                'sources': final_result.get('sources', []),
                                'metadata': final_result.get('metadata', {}),
                                'session_id': message.data.get('session_id'),
                                'confidence_score': final_result.get('confidence_score', 0.0),
                                'worker_results': final_result.get('agent_results', {})
                            },
                            timestamp=message.timestamp
                        )
                        # Rufe die vorhandene Backend-Response-Handler auf
                        self._handle_backend_response(backend_response_msg)
    
    def _show_streaming_ui(self):
        """Zeigt Streaming-UI"""
        self.streaming_frame.pack(fill=self.tk.X, pady=(0, 5))
        self.progress_var.set(0)
    
    def _hide_streaming_ui(self):
        """Versteckt Streaming-UI"""
        self.streaming_frame.pack_forget()
    
    def _cancel_current_stream(self):
        """Bricht aktuellen Stream ab"""
        if self.current_stream_session:
            result = self.streaming_service.cancel_stream(self.current_stream_session)
            if result.get('success'):
                self.stream_status_var.set("🛑 Abbruch läuft...")
            else:
                self.stream_status_var.set(f"❌ Abbruch-Fehler: {result.get('message', '')}")
    
    def _add_intermediate_result(self, agent_type: str, result_data: Dict[str, Any]):
        """Fügt Zwischenergebnis zur Chat-Anzeige hinzu"""
        # Implementierung abhängig von bestehender Chat-Display-Struktur
        if hasattr(self, 'chat_display'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            intermediate_text = f"[{timestamp}] 🔄 {agent_type}: {result_data.get('content', 'Verarbeitung...')}\n"
            
            # Als System-Message einfügen
            self.chat_display.config(state=self.tk.NORMAL)
            self.chat_display.insert(self.tk.END, intermediate_text, "system")
            self.chat_display.config(state=self.tk.DISABLED)
            self.chat_display.see(self.tk.END)
    
    def _add_thinking_step(self, thinking_step: str):
        """Fügt LLM-Thinking-Schritt hinzu"""
        if hasattr(self, 'chat_display'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            thinking_text = f"[{timestamp}] 🧠 {thinking_step}\n"
            
            self.chat_display.config(state=self.tk.NORMAL)
            self.chat_display.insert(self.tk.END, thinking_text, "thinking")
            self.chat_display.config(state=self.tk.DISABLED)
            self.chat_display.see(self.tk.END)
    
    def _add_stage_reflection(self, reflection_data: Dict[str, Any]):
        """
        Zeigt Stage-Reflection in erweitertem Format an
        
        Args:
            reflection_data: Dict mit stage, completion_percent, gaps, etc.
        """
        if not hasattr(self, 'chat_display'):
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        stage = reflection_data.get('stage', 'unknown')
        completion = reflection_data.get('completion_percent', 0)
        status = reflection_data.get('fulfillment_status', 'unknown')
        confidence = reflection_data.get('confidence', 0)
        
        # Status-Emoji
        status_emoji = {
            "incomplete": "🔴",
            "partial": "🟡",
            "complete": "🟢"
        }.get(status, "⚪")
        
        # Haupt-Reflection-Text
        reflection_header = f"\n[{timestamp}] {status_emoji} Stage Reflection: {stage.upper()}\n"
        reflection_header += f"Erfüllung: {completion:.0f}% | Status: {status} | Konfidenz: {confidence:.2f}\n"
        
        # Gesammelte Informationen
        gathered = reflection_data.get('gathered_info', [])
        if gathered:
            reflection_header += f"\n✅ Gesammelt:\n"
            for info in gathered[:3]:  # Max 3 für Übersichtlichkeit
                reflection_header += f"  • {info}\n"
        
        # Identifizierte Lücken
        gaps = reflection_data.get('identified_gaps', [])
        if gaps:
            reflection_header += f"\n⚠️ Lücken:\n"
            for gap in gaps[:3]:
                reflection_header += f"  • {gap}\n"
        
        # Nächste Schritte
        actions = reflection_data.get('next_actions', [])
        if actions:
            reflection_header += f"\n🔜 Nächste Schritte:\n"
            for action in actions[:2]:
                reflection_header += f"  • {action}\n"
        
        # LLM-Reasoning (optional, gekürzt)
        reasoning = reflection_data.get('llm_reasoning', '')
        if reasoning and len(reasoning) > 50:
            reflection_header += f"\n💭 LLM: {reasoning[:150]}...\n"
        elif reasoning:
            reflection_header += f"\n💭 LLM: {reasoning}\n"
        
        reflection_header += "\n" + "─" * 60 + "\n"
        
        # In Chat einfügen
        self.chat_display.config(state=self.tk.NORMAL)
        self.chat_display.insert(self.tk.END, reflection_header, "reflection")
        self.chat_display.config(state=self.tk.DISABLED)
        self.chat_display.see(self.tk.END)

# ===== CHAT TAGS FÜR STREAMING =====

def setup_streaming_chat_tags(chat_display):
    """Richtet Chat-Tags für Streaming-Inhalte ein"""
    
    chat_display.tag_config("system", foreground="#666666", font=('Arial', 8, 'italic'))
    chat_display.tag_config("thinking", foreground="#0066CC", font=('Arial', 8, 'italic'))
    chat_display.tag_config("intermediate", foreground="#006600", font=('Arial', 8))
    chat_display.tag_config("progress", foreground="#FF6600", font=('Arial', 8, 'bold'))
    chat_display.tag_config("reflection", foreground="#9900CC", font=('Arial', 9), 
                          background="#F8F0FF", spacing1=4, spacing3=4)

# ===== UTILITY FUNCTIONS =====

def is_streaming_enabled_for_session(session_id: str) -> bool:
    """Prüft ob Streaming für Session aktiviert ist"""
    # Implementierung abhängig von Session-Management
    return True

def get_streaming_preferences() -> Dict[str, bool]:
    """Holt Streaming-Präferenzen aus Konfiguration"""
    return {
        'enable_progress': True,
        'enable_intermediate': True,
        'enable_thinking': True,
        'auto_show_ui': True
    }

# ===== MODULE EXPORTS =====

__all__ = [
    'VeritasStreamingService',
    'StreamingUIMixin', 
    'StreamingMessageType',
    'StreamingMessage',
    'setup_streaming_chat_tags',
    'is_streaming_enabled_for_session',
    'get_streaming_preferences'
]

if __name__ == "__main__":
    # Test Streaming Service
    print("🚀 VERITAS Streaming Service - Test")
    
    service = VeritasStreamingService()
    print(f"✅ Service erstellt - Streaming verfügbar: {service.is_streaming_available()}")