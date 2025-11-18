#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Integration Example: Neue Chat-Bubbles + Best Practices

Zeigt wie die neuen UI-Komponenten in veritas_app.py integriert werden.
Dieses File ist ein BEISPIEL - nicht zum direkten Ausführen gedacht!

Stattdessen: Code-Snippets in veritas_app.py übernehmen.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional

from frontend.ui.veritas_ui_chat_bubbles import (
    COLORS,
    AssistantFullWidthLayout,
    MetadataCompactWrapper,
    TkinterBestPractices,
    UserMessageBubble,
)

# Bestehende Module
from frontend.ui.veritas_ui_markdown import MarkdownRenderer
from frontend.ui.veritas_ui_source_links import SourceLinkHandler

# === IMPORTS DER NEUEN MODULE ===



logger = logging.getLogger(__name__)


# === BEISPIEL-INTEGRATION IN VERITAS APP ===


class VeritasAppModern:
    """
    Beispiel wie VeritasApp mit neuen UI-Komponenten aussehen könnte

    HINWEIS: Dies ist ein BEISPIEL für Integrations-Muster.
    Der echte Code in veritas_app.py hat mehr Komplexität.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("VERITAS Chat - Modern UI")
        self.root.geometry("900x700")

        # === UI SETUP ===
        self._setup_ui()

        # === NEUE UI-HANDLER INITIALISIEREN ===
        self._setup_modern_ui_handlers()

        # === BEST-PRACTICE OPTIMIERUNGEN ===
        self._apply_best_practices()

    def _setup_ui(self):
        """Erstellt grundlegendes UI-Layout"""

        # Haupt-Container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Chat-Display (scrollbar)
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(chat_frame)
        scrollbar.pack(side="right", fill="y")

        self.chat_text = tk.Text(
            chat_frame,
            wrap="word",
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 10),
            relief="flat",
            bg="#FFFFFF",
            padx=10,
            pady=10,
            state="disabled",  # Read-only, außer beim Einfügen
        )
        self.chat_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.chat_text.yview)

        # Input-Bereich
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill="x", pady=(10, 0))

        self.input_field = tk.Text(input_frame, height=3, wrap="word", font=("Segoe UI", 10), relief="solid", borderwidth=1)
        self.input_field.pack(side="left", fill="both", expand=True)

        send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_button.pack(side="right", padx=(10, 0))

    def _setup_modern_ui_handlers(self):
        """
        ✨ NEU: Initialisiert moderne UI-Handler

        Diese Handler kümmern sich um Rendering von:
        - User-Bubbles
        - Assistant Full-Width Layout
        - Kompakte Metadaten
        """

        # Markdown-Renderer (bestehend, wird wiederverwendet)
        self.markdown_renderer = MarkdownRenderer(text_widget=self.chat_text, parent_window=self.root)

        # Source-Link-Handler (bestehend)
        self.source_link_handler = SourceLinkHandler(text_widget=self.chat_text)

        # ✨ NEU: Metadaten-Handler (kompakt, collapsible)
        self.metadata_handler = MetadataCompactWrapper(
            text_widget=self.chat_text,
            feedback_callback=self.on_feedback_received,
            initially_collapsed=True,  # Default: zugeklappt
        )

        # ✨ NEU: Assistant-Layout-Handler (full-width)
        self.assistant_layout = AssistantFullWidthLayout(
            text_widget=self.chat_text, markdown_renderer=self.markdown_renderer, metadata_handler=self.metadata_handler
        )

        logger.info("✅ Moderne UI-Handler initialisiert")

    def _apply_best_practices(self):
        """
        ✨ NEU: Wendet Tkinter Best-Practice Optimierungen an

        Features:
        1. Smooth Scrolling
        2. Performance-Optimierung
        3. Keyboard Shortcuts
        4. Auto-Scroll Smart Detection
        """

        # 1. Smooth Scrolling aktivieren
        TkinterBestPractices.enable_smooth_scrolling(self.chat_text)
        logger.info("✅ Smooth Scrolling aktiviert")

        # 2. Text-Widget für Performance optimieren
        TkinterBestPractices.optimize_text_widget(self.chat_text)
        logger.info("✅ Text-Widget optimiert")

        # 3. Keyboard Shortcuts registrieren
        shortcuts = {
            "<Control-k>": self.clear_chat,
            "<Control-s>": self.save_chat,
            "<Control-l>": self.load_chat,
            "<Escape>": lambda: self.input_field.focus_set(),
            "<Control-Return>": self.send_message,  # Alternative zu Button
        }
        TkinterBestPractices.add_keyboard_shortcuts(self.root, shortcuts)
        logger.info(f"✅ {len(shortcuts)} Keyboard-Shortcuts registriert")

        # 4. Auto-Scroll mit Smart Detection
        self.auto_scroll_handler = TkinterBestPractices.add_auto_scroll_to_bottom(self.chat_text)
        logger.info("✅ Auto-Scroll Smart Detection aktiviert")

    # === MESSAGE-RENDERING (NEU) ===

    def display_user_message(self, message: str, timestamp: Optional[str] = None):
        """
        ✨ NEU: Rendert User-Message als moderne Bubble (rechts)

        Args:
            message: User-Query-Text
            timestamp: ISO-Timestamp oder None
        """

        # Text-Widget für Schreiben freigeben
        self.chat_text.config(state="normal")

        try:
            # ✨ Verwende neue UserMessageBubble-Klasse
            bubble = UserMessageBubble(
                text_widget=self.chat_text, message=message, timestamp=timestamp, max_width_percent=0.7  # 70% Breite
            )
            bubble.render()

            # Auto-Scroll (nur wenn User am Ende war)
            self.auto_scroll_handler()

            logger.debug(f"User-Bubble gerendert: {len(message)} Zeichen")

        except Exception as e:
            logger.error(f"Fehler beim Rendern User-Bubble: {e}")
            # Fallback: Plain-Text
            self.chat_text.insert("end", f"User: {message}\n\n")

        finally:
            # Text-Widget wieder read-only
            self.chat_text.config(state="disabled")

    def display_assistant_message(
        self, content: str, metadata: Optional[Dict[str, Any]] = None, sources: Optional[List[Dict]] = None
    ):
        """
        ✨ NEU: Rendert Assistant-Message als Full-Width Layout

        Args:
            content: Markdown-formatierter Antwort-Text
            metadata: Dict mit complexity, duration, model, tokens, etc.
            sources: Liste von Source-Dicts mit file, confidence, page, etc.
        """

        # Text-Widget für Schreiben freigeben
        self.chat_text.config(state="normal")

        try:
            # ✨ Verwende neue AssistantFullWidthLayout-Klasse
            self.assistant_layout.render_assistant_message(content=content, metadata=metadata, sources=sources)

            # Auto-Scroll (nur wenn User am Ende war)
            self.auto_scroll_handler()

            logger.debug(f"Assistant Full-Width gerendert: {len(content)} Zeichen")

        except Exception as e:
            logger.error(f"Fehler beim Rendern Assistant-Layout: {e}")
            # Fallback: Plain-Text
            self.chat_text.insert("end", f"Assistant: {content}\n\n")

        finally:
            # Text-Widget wieder read-only
            self.chat_text.config(state="disabled")

    def display_system_message(self, message: str, message_type: str = "info"):
        """
        Zeigt System-Nachrichten (Verbindung, Fehler, etc.)

        Args:
            message: System-Message-Text
            message_type: 'info', 'success', 'error', 'warning'
        """

        # Farben je nach Type
        colors = {
            "info": "#2196F3",  # Blue
            "success": "#4CAF50",  # Green
            "error": "#F44336",  # Red
            "warning": "#FF9800",  # Orange
        }

        self.chat_text.config(state="normal")

        try:
            # Zentrierte System-Message
            self.chat_text.insert("end", f"\n{message}\n\n", "system")

            # Tag für Styling
            self.chat_text.tag_config(
                "system", foreground=colors.get(message_type, "#616161"), font=("Segoe UI", 9, "italic"), justify="center"
            )

            self.auto_scroll_handler()

        finally:
            self.chat_text.config(state="disabled")

    # === FEEDBACK-HANDLER ===

    def on_feedback_received(self, rating: str):
        """
        ✨ NEU: Behandelt Feedback von Metadaten-Wrapper

        Args:
            rating: 'positive' (👍) oder 'negative' (👎)
        """

        logger.info(f"✅ User-Feedback erhalten: {rating}")

        # TODO: An Backend senden
        # POST /feedback
        # {
        #     "message_id": "msg_123",
        #     "rating": "positive",
        #     "timestamp": "2025-10-17T20:30:00"
        # }

        # Visual Feedback für User (optional)
        self.display_system_message("Danke für dein Feedback! 🙏", message_type="success")

    # === MESSAGE-SENDING ===

    def send_message(self):
        """Sendet User-Message an Backend"""

        # Text aus Input-Field holen
        message = self.input_field.get("1.0", "end-1c").strip()

        if not message:
            return

        # Input-Field leeren
        self.input_field.delete("1.0", "end")

        # User-Bubble anzeigen
        from datetime import datetime

        timestamp = datetime.now().isoformat()
        self.display_user_message(message, timestamp)

        # Loading-Indicator (optional)
        self.display_system_message("⋯ Thinking...", message_type="info")

        # Simuliere Backend-Call (in echtem Code: Threading!)
        self.root.after(1000, lambda: self._simulate_backend_response(message))

    def _simulate_backend_response(self, query: str):
        """Simuliert Backend-Antwort (Beispiel)"""

        # ✨ Simulierte Antwort MIT IEEE-Citations
        assistant_content = f"""
## Antwort auf: "{query}"

Das ist eine **Beispiel-Antwort** mit Markdown-Formatierung und wissenschaftlichen Citations.

### Aktuelle Forschung

Deep Learning zeigt signifikante Erfolge {{cite:src_1}} in der Verarbeitung
natürlicher Sprache. Transformer-Architekturen {{cite:src_2}} haben die
Genauigkeit um 15% verbessert.

### Code-Beispiel:
```python
def hello_world():
    print("Hello from VERITAS!")
```

### Weitere Details

Die VERITAS-Dokumentation {{cite:src_3}} bietet umfassende Informationen
zu allen Features.

### Liste:
- Punkt 1: RAG-Pipeline {{cite:src_1}}
- Punkt 2: Token-Management
- Punkt 3: IEEE-Citations {{cite:src_2}}, {{cite:src_3}}

Weitere Informationen findest du in den Quellen unten (IEEE-Standard).
"""

        # ✨ Simulierte Metadaten
        metadata = {
            "complexity": "Medium",
            "duration": 1.234,
            "model": "llama3.2:latest",
            "tokens": {"total": 500, "prompt": 100, "completion": 400},
        }

        # ✨ Simulierte Sources MIT IEEE-Metadaten
        sources = [
            {
                "id": "src_1",
                "file": "deep_learning_nlp.pdf",
                "page": 42,
                "confidence": 0.87,
                "author": "J. Smith",
                "title": "Deep Learning Advances in NLP",
                "year": 2020,
                "snippet": "Significant improvements in natural language processing...",
            },
            {
                "id": "src_2",
                "file": "attention_is_all_you_need.pdf",
                "pages": "5998-6008",
                "confidence": 0.92,
                "author": "A. Vaswani et al.",
                "title": "Attention is All You Need",
                "year": 2017,
                "snippet": "Transformer architecture revolutionized sequence modeling...",
            },
            {
                "id": "src_3",
                "url": "https://veritas.example.com/docs",
                "confidence": 0.85,
                "title": "VERITAS Documentation",
                "website": "VERITAS Project",
                "access_date": "Oct. 17, 2025",
                "snippet": "Comprehensive documentation for all VERITAS features...",
            },
        ]

        # Entferne Loading-Indicator (letzte Zeile)
        # (In echtem Code: Message-ID tracking)

        # ✨ Zeige Assistant-Antwort MIT IEEE-Citations
        self.display_assistant_message(content=assistant_content, metadata=metadata, sources=sources)

    # === UTILITY-FUNKTIONEN ===

    def clear_chat(self):
        """Löscht Chat-History"""
        self.chat_text.config(state="normal")
        self.chat_text.delete("1.0", "end")
        self.chat_text.config(state="disabled")
        logger.info("Chat gelöscht")

    def save_chat(self):
        """Speichert Chat (Placeholder)"""
        logger.info("Chat speichern - TODO: Implementierung")
        # TODO: JSON-Export

    def load_chat(self):
        """Lädt Chat (Placeholder)"""
        logger.info("Chat laden - TODO: Implementierung")
        # TODO: JSON-Import


# === MAIN (nur für Testing) ===

if __name__ == "__main__":
    """
    Dieses Beispiel zeigt die Integration.
    Für echte Verwendung: Code in veritas_app.py integrieren!
    """

    # Logging Setup
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Tkinter App erstellen
    root = tk.Tk()
    app = VeritasAppModern(root)

    # Test-Messages einfügen
    root.after(500, lambda: app.display_user_message("Hallo VERITAS! Was ist der Sinn des Lebens?", "2025-10-17T20:30:00"))

    root.after(2000, lambda: app._simulate_backend_response("Hallo VERITAS! Was ist der Sinn des Lebens?"))

    # App starten
    root.mainloop()


# === INTEGRATION-CHECKLISTE ===
"""
✅ Checkliste für Integration in veritas_app.py:

1. [ ] Import neue Module aus veritas_ui_chat_bubbles.py
      from frontend.ui.veritas_ui_chat_bubbles import ...

2. [ ] _setup_modern_ui_handlers() in __init__ aufrufen
      self.metadata_handler = MetadataCompactWrapper(...)
      self.assistant_layout = AssistantFullWidthLayout(...)

3. [ ] _apply_best_practices() in __init__ aufrufen
      TkinterBestPractices.enable_smooth_scrolling(...)
      TkinterBestPractices.optimize_text_widget(...)

4. [ ] display_user_message() anpassen
      Verwende UserMessageBubble statt Plain-Text

5. [ ] display_assistant_message() anpassen
      Verwende AssistantFullWidthLayout statt altes Format

6. [ ] on_feedback_received() Callback implementieren
      POST /feedback an Backend

7. [ ] Keyboard-Shortcuts registrieren
      TkinterBestPractices.add_keyboard_shortcuts(...)

8. [ ] Testing durchführen
      - User-Bubbles rendern korrekt
      - Assistant Full-Width funktioniert
      - Metadaten collapsible
      - Feedback-Buttons funktionieren
      - Smooth Scrolling aktiviert
      - Shortcuts funktionieren

9. [ ] Performance-Testing
      - Chat mit 100+ Messages
      - Lange Texte (>5000 Zeichen)
      - Viele Sources (>20)

10. [ ] Dokumentation aktualisieren
       - README.md
       - Version History in veritas_app.py
       - Screenshots

Done! 🎉
"""
