#!/usr/bin/env python3
"""
VERITAS FRONTEND STREAMING INTEGRATION
====================================
Integration-Beispiel für veritas_app.py mit Real-time Progress Updates

Features:
- SSE (Server-Sent Events) Client für Progress Updates
- Real-time UI Updates während Agent-Processing
- Zwischenergebnisse anzeigen
- LLM Deep-thinking Visualisierung

Author: VERITAS System
Date: 2025-09-21
"""

import json
import queue
import re
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Callable, Dict, Optional

import requests

# SSE Client für Progress Updates
import sseclient  # pip install sseclient-py


class VeritasStreamingClient:
    """
    Streaming Client für Veritas API Integration

    VERWENDUNG in veritas_app.py:
    - Real-time Progress Updates
    - Intermediate Results Display
    - LLM Thinking Visualization
    """

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session_id = None
        self.active_stream = None
        self.progress_callbacks = []
        self.cancelled_sessions = set()  # Track cancelled sessions

    def start_streaming_query(self, query: str, progress_callback: Callable = None) -> Dict[str, Any]:
        """
        Startet Streaming-Query und Progress-Updates

        Args:
            query: Benutzer-Query
            progress_callback: Callback für Progress-Updates

        Returns:
            Stream-Info mit session_id und stream_url
        """

        # Registriere Callback
        if progress_callback:
            self.progress_callbacks.append(progress_callback)

        # Starte Streaming-Query
        response = requests.post(
            f"{self.base_url}/v2/query/stream",
            json={"query": query, "enable_streaming": True, "enable_intermediate_results": True, "enable_llm_thinking": True},
        )

        if response.status_code == 200:
            stream_info = response.json()
            self.session_id = stream_info["session_id"]

            # Starte Progress-Stream in separatem Thread
            self._start_progress_stream(stream_info["session_id"])

            return stream_info
        else:
            raise Exception(f"Streaming-Query fehlgeschlagen: {response.status_code}")

    def _start_progress_stream(self, session_id: str):
        """Startet SSE Progress-Stream"""

        def stream_worker():
            try:
                stream_url = f"{self.base_url}/progress/{session_id}"

                # SSE Client erstellen
                response = requests.get(stream_url, stream=True, headers={"Accept": "text/event-stream"})
                client = sseclient.SSEClient(response)

                for event in client.events():
                    # Prüfe ob Session abgebrochen wurde
                    if session_id in self.cancelled_sessions:
                        # Sende Cancel-Nachricht an Callbacks
                        for callback in self.progress_callbacks:
                            callback(
                                {
                                    "type": "cancelled",
                                    "message": "Stream wurde vom Benutzer abgebrochen",
                                    "stage": "cancelled",
                                    "session_id": session_id,
                                }
                            )
                        break

                    if event.data:
                        try:
                            progress_data = json.loads(event.data)

                            # Progress-Callbacks aufrufen
                            for callback in self.progress_callbacks:
                                callback(progress_data)

                            # Stream beenden bei Completion oder Error
                            if progress_data.get("stage") in ["completed", "error", "cancelled"]:
                                break

                        except json.JSONDecodeError:
                            continue

            except Exception as e:
                # Error an Callbacks weitergeben
                for callback in self.progress_callbacks:
                    callback({"type": "error", "message": f"Stream-Fehler: {str(e)}", "stage": "error"})

        # Stream-Thread starten
        stream_thread = threading.Thread(target=stream_worker, daemon=True)
        stream_thread.start()

    def cancel_streaming_session(self, session_id: str = None) -> Dict[str, Any]:
        """
        Bricht eine aktive Streaming-Session ab

        Args:
            session_id: Session-ID zum Abbrechen (oder aktuelle Session)

        Returns:
            Abbruch-Status
        """
        session_id = session_id or self.session_id

        if not session_id:
            return {"success": False, "error": "Keine aktive Session"}

        try:
            # Markiere Session als abgebrochen (für lokale Stream-Behandlung)
            self.cancelled_sessions.add(session_id)

            # Sende Cancel-Request an Backend
            response = requests.post(f"{self.base_url}/cancel/{session_id}", json={"reason": "user_cancelled"}, timeout=5)

            if response.status_code == 200:
                cancel_data = response.json()
                return {
                    "success": True,
                    "message": cancel_data.get("message", "Session erfolgreich abgebrochen"),
                    "session_id": session_id,
                }
            elif response.status_code == 404:
                return {
                    "success": True,  # Session existiert nicht mehr (bereits beendet)
                    "message": "Session war bereits beendet",
                    "session_id": session_id,
                }
            else:
                return {"success": False, "error": f"Backend-Fehler: {response.status_code}", "session_id": session_id}

        except requests.RequestException as e:
            # Auch bei Netzwerkfehlern als "erfolgreich" betrachten,
            # da die lokale Behandlung (cancelled_sessions) trotzdem funktioniert
            return {
                "success": True,
                "message": f"Lokaler Abbruch erfolgreich (Backend nicht erreichbar: {str(e)})",
                "session_id": session_id,
            }
        except Exception as e:
            return {"success": False, "error": f"Unerwarteter Fehler: {str(e)}", "session_id": session_id}

    def get_session_progress(self, session_id: str = None) -> Dict[str, Any]:
        """Holt aktuellen Progress-Status"""
        session_id = session_id or self.session_id

        if not session_id:
            return {}

        response = requests.get(f"{self.base_url}/progress/status/{session_id}")

        if response.status_code == 200:
            return response.json()
        else:
            return {}


class VeritasStreamingWidget:
    """
    Tkinter Widget für Streaming Progress Display
    Kann in veritas_app.py integriert werden
    """

    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.streaming_client = VeritasStreamingClient()

        # Progress Queue für Thread-sichere Updates
        self.progress_queue = queue.Queue()

        self._create_widgets()
        self._start_progress_processor()

    def _create_widgets(self):
        """Erstellt UI-Komponenten für Streaming"""

        # Main Streaming Frame
        self.streaming_frame = ttk.LabelFrame(self.parent, text="🔄 Real-time Processing", padding=10)
        self.streaming_frame.pack(fill=tk.X, padx=5, pady=5)

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.streaming_frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        # Current Stage Label
        self.stage_var = tk.StringVar(value="Bereit für Anfragen...")
        self.stage_label = ttk.Label(self.streaming_frame, textvariable=self.stage_var, font=("Arial", 9))
        self.stage_label.pack(anchor=tk.W)

        # Agent Status Frame
        self.agent_frame = ttk.LabelFrame(self.streaming_frame, text="Agent Status", padding=5)
        self.agent_frame.pack(fill=tk.X, pady=(5, 0))

        # Agent Status Labels (werden dynamisch erstellt)
        self.agent_labels = {}

        # Intermediate Results Area
        self.results_frame = ttk.LabelFrame(self.parent, text="💡 Zwischenergebnisse", padding=10)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.results_text = scrolledtext.ScrolledText(self.results_frame, height=8, wrap=tk.WORD, font=("Arial", 9))
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # LLM Thinking Area
        self.thinking_frame = ttk.LabelFrame(self.parent, text="🧠 LLM Deep-Thinking", padding=10)
        self.thinking_frame.pack(fill=tk.X, padx=5, pady=5)

        self.thinking_text = scrolledtext.ScrolledText(
            self.thinking_frame, height=4, wrap=tk.WORD, font=("Arial", 9, "italic")
        )
        self.thinking_text.pack(fill=tk.X)

        # Control Buttons
        self.control_frame = ttk.Frame(self.parent)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)

        self.streaming_enabled_var = tk.BooleanVar(value=True)
        self.streaming_check = ttk.Checkbutton(
            self.control_frame, text="Real-time Updates aktivieren", variable=self.streaming_enabled_var
        )
        self.streaming_check.pack(side=tk.LEFT)

        # Cancel Button
        self.cancel_button = ttk.Button(
            self.control_frame, text="❌ Abbrechen", command=self._cancel_streaming, state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=(10, 0))

        # Hide frames initially
        self.streaming_frame.pack_forget()
        self.results_frame.pack_forget()
        self.thinking_frame.pack_forget()

        # Streaming state
        self.current_session_id = None
        self.streaming_active = False

    def start_streaming_query(self, query: str) -> None:
        """Startet Streaming-Query mit UI-Updates"""

        if not self.streaming_enabled_var.get():
            return

        # Show streaming frames
        self.streaming_frame.pack(fill=tk.X, padx=5, pady=5)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.thinking_frame.pack(fill=tk.X, padx=5, pady=5)

        # Clear previous content
        self.results_text.delete(1.0, tk.END)
        self.thinking_text.delete(1.0, tk.END)
        self._clear_agent_status()

        # Reset progress
        self.progress_var.set(0)
        self.stage_var.set("🚀 Starte Verarbeitung...")

        # Enable cancel button
        self.cancel_button.config(state=tk.NORMAL)
        self.streaming_active = True

        # Start streaming
        try:
            stream_info = self.streaming_client.start_streaming_query(query, self._on_progress_update)

            # Store session ID for cancellation
            self.current_session_id = stream_info.get("session_id")

            # Info message
            self._add_result(
                f"📡 Streaming gestartet für Session: {stream_info['session_id']}\n"
                f"⏱️ Geschätzte Zeit: {stream_info.get('estimated_time', 'unbekannt')}\n"
                f"❌ Klicken Sie 'Abbrechen' um zu stoppen\n\n",
                "info",
            )

        except Exception as e:
            self.stage_var.set(f"❌ Fehler: {str(e)}")
            self._stop_streaming()
            messagebox.showerror("Streaming Fehler", f"Streaming konnte nicht gestartet werden:\n{str(e)}")

    def _cancel_streaming(self):
        """Bricht aktives Streaming ab"""
        if not self.streaming_active or not self.current_session_id:
            return

        try:
            # Versuche Session zu beenden
            cancel_response = self.streaming_client.cancel_streaming_session(self.current_session_id)

            if cancel_response.get("success", False):
                self.stage_var.set("🛑 Verarbeitung abgebrochen")
                self._add_result(f"🛑 Streaming-Session {self.current_session_id} wurde erfolgreich abgebrochen.\n\n", "info")
            else:
                self.stage_var.set("⚠️ Abbruch möglicherweise nicht erfolgreich")
                self._add_result(f"⚠️ Abbruch-Request gesendet, aber Backend-Bestätigung fehlt.\n\n", "warning")

        except Exception as e:
            self.stage_var.set(f"❌ Abbruch-Fehler: {str(e)}")
            self._add_result(
                f"❌ Fehler beim Abbrechen: {str(e)}\n" f"Die Verarbeitung läuft möglicherweise weiter.\n\n", "error"
            )

        finally:
            # UI-State zurücksetzen
            self._stop_streaming()

    def _stop_streaming(self):
        """Stoppt Streaming und setzt UI-State zurück"""
        self.streaming_active = False
        self.current_session_id = None
        self.cancel_button.config(state=tk.DISABLED)

    def _on_progress_update(self, progress_data: Dict[str, Any]):
        """Callback für Progress-Updates (wird in separatem Thread aufgerufen)"""

        # Thread-sicher über Queue
        self.progress_queue.put(progress_data)

    def _start_progress_processor(self):
        """Startet Progress-Processor für UI-Updates"""

        def process_progress():
            try:
                while True:
                    # Warte auf Progress-Update
                    progress_data = self.progress_queue.get(timeout=0.1)

                    # UI-Update im Main-Thread
                    self.parent.after(0, self._update_ui, progress_data)

            except queue.Empty:
                # Timeout - einfach weiter versuchen
                pass
            except Exception as e:
                print(f"Progress Processor Fehler: {e}")

            # Rekursiv weitermachen
            self.parent.after(100, process_progress)

        # Starte Processor
        process_progress()

    def _update_ui(self, progress_data: Dict[str, Any]):
        """Updated UI basierend auf Progress-Data"""

        update_type = progress_data.get("type", "")
        stage = progress_data.get("stage", "")
        message = progress_data.get("message", "")
        progress = progress_data.get("progress", 0)

        # Progress Bar Update
        if progress > 0:
            self.progress_var.set(progress)

        # Stage Update
        if message:
            self.stage_var.set(message)

        # Type-spezifische Updates
        if update_type == "agent_start":
            self._update_agent_status(progress_data.get("agent_type"), "🔄", "Startet...")

        elif update_type == "agent_complete":
            agent_type = progress_data.get("agent_type")
            result = progress_data.get("details", {})
            confidence = result.get("confidence", 0)

            status_icon = "✅" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
            self._update_agent_status(agent_type, status_icon, f"Abgeschlossen ({confidence:.0%})")

        elif update_type == "intermediate_result":
            details = progress_data.get("details", {})
            result_content = details.get("content", "Zwischenergebnis verfügbar")
            confidence = details.get("confidence", 0)

            self._add_result(
                f"[{datetime.now().strftime('%H:%M:%S')}] {result_content}\n" f"Confidence: {confidence:.0%}\n\n",
                "intermediate",
            )

        elif update_type == "llm_thinking":
            thinking_step = progress_data.get("llm_thinking", "")

            self._add_thinking(f"[{datetime.now().strftime('%H:%M:%S')}] {thinking_step}\n")

        elif update_type == "stage_complete" and stage == "completed":
            self.stage_var.set("✅ Verarbeitung abgeschlossen!")
            self.progress_var.set(100)
            self._stop_streaming()

            # Completion message
            self._add_result(f"🎉 Verarbeitung erfolgreich abgeschlossen!\n" f"Finale Antwort ist verfügbar.\n\n", "success")

        elif update_type == "error":
            self.stage_var.set(f"❌ Fehler: {message}")
            self._stop_streaming()
            self._add_result(f"❌ Fehler: {message}\n\n", "error")

        elif update_type == "cancelled":
            self.stage_var.set("🛑 Verarbeitung abgebrochen")
            self._stop_streaming()
            self._add_result(f"🛑 Verarbeitung wurde abgebrochen: {message}\n\n", "warning")

    def _update_agent_status(self, agent_type: str, icon: str, status: str):
        """Updated Agent-Status in UI"""

        if agent_type not in self.agent_labels:
            # Erstelle neues Agent-Label
            agent_frame = ttk.Frame(self.agent_frame)
            agent_frame.pack(fill=tk.X, pady=1)

            name_label = ttk.Label(agent_frame, text=f"{agent_type.replace('_', ' ').title()}:", width=15)
            name_label.pack(side=tk.LEFT)

            status_label = ttk.Label(agent_frame, text=f"{icon} {status}")
            status_label.pack(side=tk.LEFT, padx=(5, 0))

            self.agent_labels[agent_type] = {"frame": agent_frame, "status_label": status_label}
        else:
            # Update existierendes Label
            self.agent_labels[agent_type]["status_label"].config(text=f"{icon} {status}")

    def _clear_agent_status(self):
        """Leert Agent-Status Display"""
        for agent_type, labels in self.agent_labels.items():
            labels["frame"].destroy()
        self.agent_labels.clear()

    def _add_result(self, text: str, result_type: str = "normal"):
        """Fügt Ergebnis zu Results-Area hinzu"""

        # Color coding
        colors = {"info": "blue", "intermediate": "darkgreen", "success": "green", "error": "red", "normal": "black"}

        color = colors.get(result_type, "black")

        # Insert text with color
        self.results_text.insert(tk.END, text)

        # Scroll to end
        self.results_text.see(tk.END)

    def _add_thinking(self, text: str):
        """Fügt LLM-Thinking zu Thinking-Area hinzu"""

        self.thinking_text.insert(tk.END, text)
        self.thinking_text.see(tk.END)

    def is_streaming_enabled(self) -> bool:
        """Prüft ob Streaming aktiviert ist"""
        return self.streaming_enabled_var.get()


# ===== INTEGRATION BEISPIEL =====


class VeritasStreamingDemo:
    """Demo-Anwendung für Streaming Integration"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Veritas Streaming Demo")
        self.root.geometry("800x700")

        self._create_ui()

    def _create_ui(self):
        """Erstellt Demo-UI"""

        # Query Input
        input_frame = ttk.LabelFrame(self.root, text="Query Input", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        self.query_var = tk.StringVar(value="Wie kann ich eine Baugenehmigung beantragen und welche Kosten entstehen?")

        query_entry = ttk.Entry(input_frame, textvariable=self.query_var, font=("Arial", 10))
        query_entry.pack(fill=tk.X, pady=(0, 5))

        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X)

        submit_btn = ttk.Button(button_frame, text="🚀 Streaming Query", command=self._submit_query)
        submit_btn.pack(side=tk.LEFT)

        clear_btn = ttk.Button(button_frame, text="🗑️ Clear", command=self._clear_all)
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))

        # Status Label
        self.status_var = tk.StringVar(value="Bereit für Anfragen")
        status_label = ttk.Label(button_frame, textvariable=self.status_var, font=("Arial", 9))
        status_label.pack(side=tk.RIGHT)

        # Streaming Widget
        self.streaming_widget = VeritasStreamingWidget(self.root)

        # Final Response Area
        response_frame = ttk.LabelFrame(self.root, text="📄 Finale Antwort", padding=10)
        response_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.response_text = scrolledtext.ScrolledText(response_frame, height=8, wrap=tk.WORD)
        self.response_text.pack(fill=tk.BOTH, expand=True)

    def _submit_query(self):
        """Sendet Query mit Streaming"""

        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("Warnung", "Bitte geben Sie eine Query ein.")
            return

        # Clear previous response
        self.response_text.delete(1.0, tk.END)

        if self.streaming_widget.is_streaming_enabled():
            # Streaming Query
            self.status_var.set("⏳ Streaming läuft...")
            self.streaming_widget.start_streaming_query(query)

            # Simuliere finale Antwort nach Completion (in echter Implementation würde das automatisch kommen)
            self.root.after(8000, self._simulate_final_response)
        else:
            # Standard non-streaming Query
            self.status_var.set("⏳ Verarbeitung...")
            self._send_standard_query(query)

    def _simulate_final_response(self):
        """Simuliert finale Antwort (Placeholder)"""

        # Nur wenn Streaming noch aktiv ist
        if not self.streaming_widget.streaming_active:
            return

        self.status_var.set("✅ Abgeschlossen")

        final_response = """
**Finale Antwort zur Baugenehmigung:**

Basierend auf der umfassenden Analyse durch unsere Agenten können wir Ihnen folgende Informationen zur Baugenehmigung geben:

**Verfahren:**
1. Voranfrage bei der Bauaufsichtsbehörde (optional, aber empfohlen)
2. Einreichung der vollständigen Bauantragsunterlagen
3. Prüfung durch die Behörde (4-12 Wochen)
4. Erteilung der Baugenehmigung

**Erforderliche Unterlagen:**
• Bauzeichnungen (Lageplan, Grundrisse, Schnitte, Ansichten)
• Statische Berechnungen
• Entwässerungsnachweis
• Energieausweis
• Bei Bedarf: Gutachten (Schall, Boden, etc.)

**Kosten:**
• Verwaltungsgebühren: 0,5-1,5% der Bausumme
• Architekt/Ingenieur: 10-15% der Bausumme
• Gutachten: 500-2.000€ je nach Art

**Bearbeitungszeit:**
• Einfache Vorhaben: 4-6 Wochen
• Komplexe Vorhaben: 8-12 Wochen
• Bei Einwendungen: Verlängerung möglich

Diese Informationen wurden durch 6 spezialisierte Agenten zusammengestellt und haben eine durchschnittliche Vertrauenswürdigkeit von 89%.
        """

        self.response_text.insert(tk.END, final_response.strip())

    def _send_standard_query(self, query: str):
        """Sendet Standard non-streaming Query"""

        try:
            response = requests.post("http://localhost:5000/v2/query", json={"query": query, "enable_streaming": False})

            if response.status_code == 200:
                result = response.json()
                self.response_text.insert(tk.END, result.get("response_text", "Keine Antwort erhalten"))
                self.status_var.set("✅ Abgeschlossen")
            else:
                self.response_text.insert(tk.END, f"Fehler: {response.status_code}")
                self.status_var.set("❌ Fehler")

        except Exception as e:
            self.response_text.insert(tk.END, f"Verbindungsfehler: {str(e)}")
            self.status_var.set("❌ Verbindungsfehler")

    def _clear_all(self):
        """Leert alle Anzeigebereiche"""

        self.response_text.delete(1.0, tk.END)
        self.streaming_widget.results_text.delete(1.0, tk.END)
        self.streaming_widget.thinking_text.delete(1.0, tk.END)
        self.status_var.set("Bereit für Anfragen")

    def run(self):
        """Startet Demo-Anwendung"""
        self.root.mainloop()


# ===== INTEGRATION GUIDE =====


def integration_guide():
    """
    INTEGRATION GUIDE für veritas_app.py

    1. DEPENDENCIES INSTALLIEREN:
       pip install sseclient-py requests

    2. STREAMING WIDGET INTEGRATION:

       # In veritas_app.py:
       from frontend.streaming.veritas_frontend_streaming import VeritasStreamingWidget

       # Im __init__ der Chat-App:
       self.streaming_widget = VeritasStreamingWidget(self.main_frame)

       # Beim Senden einer Query:
       if use_streaming:
           self.streaming_widget.start_streaming_query(user_query)
       else:
           # Standard-Query wie bisher
           pass

    3. BACKEND-URL KONFIGURATION:

       # In veritas_frontend_streaming.py ändern:
       self.base_url = "http://localhost:5000"  # Deine Backend-URL

    4. UI-INTEGRATION:

       Das VeritasStreamingWidget kann direkt in bestehende Tkinter-UIs
       integriert werden. Es erstellt automatisch die erforderlichen
       Frames für Progress, Zwischenergebnisse und LLM-Thinking.

    5. KONFIGURATION:

       - Real-time Updates können per Checkbox aktiviert/deaktiviert werden
       - Zwischenergebnisse werden automatisch angezeigt
       - LLM Deep-thinking wird in separatem Bereich visualisiert
       - Progress-Bar zeigt Fortschritt der Verarbeitung
    """
    print(integration_guide.__doc__)


if __name__ == "__main__":
    # Starte Demo-Anwendung
    demo = VeritasStreamingDemo()
    demo.run()
