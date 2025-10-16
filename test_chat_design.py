#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS: Test-Script für neues Chat-Design
Demonstriert alle implementierten Features
"""

import tkinter as tk
from datetime import datetime
from frontend.ui.veritas_ui_chat_formatter import ChatDisplayFormatter, setup_chat_tags

def create_test_window():
    """Erstellt Test-Fenster mit Chat-Display"""
    root = tk.Tk()
    root.title("VERITAS Chat-Design Test")
    root.geometry("800x600")
    
    # Chat-Text-Widget
    chat_text = tk.Text(
        root,
        wrap=tk.WORD,
        font=('Segoe UI', 10),
        bg='#ffffff',
        relief=tk.FLAT,
        padx=10,
        pady=10
    )
    chat_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Tags konfigurieren
    setup_chat_tags(chat_text)
    
    # Formatter initialisieren
    formatter = ChatDisplayFormatter(
        text_widget=chat_text,
        parent_window=root,
        markdown_renderer=None,  # Für Test ohne Markdown
        source_link_handler=None
    )
    
    return root, formatter

def test_user_message_simple(formatter):
    """Test 1: Einfache User-Message ohne Anhang"""
    print("✅ Test 1: Einfache User-Message")
    formatter.text_widget.config(state='normal')
    
    formatter._render_user_message(
        content="Hallo VERITAS! Wie geht es dir?",
        timestamp_short="Heute 14:20",
        timestamp_full="Mittwoch, 9. Oktober 2025, 14:20:15",
        attachments=[]
    )
    
    formatter.text_widget.config(state='disabled')

def test_user_message_with_attachments(formatter):
    """Test 2: User-Message mit Datei-Anhängen"""
    print("✅ Test 2: User-Message mit Anhängen")
    formatter.text_widget.config(state='normal')
    
    formatter._render_user_message(
        content="Analysiere bitte diese Dokumente und erstelle eine Zusammenfassung.",
        timestamp_short="Heute 14:22",
        timestamp_full="Mittwoch, 9. Oktober 2025, 14:22:30",
        attachments=[
            {'name': 'jahresbericht_2024.pdf', 'size': 2457600, 'path': 'C:\\Dokumente\\jahresbericht_2024.pdf'},
            {'name': 'analysen.docx', 'size': 358400, 'path': 'C:\\Dokumente\\analysen.docx'}
        ]
    )
    
    formatter.text_widget.config(state='disabled')

def test_assistant_message_structured(formatter):
    """Test 3: Strukturierte Assistant-Message"""
    print("✅ Test 3: Strukturierte Assistant-Message")
    formatter.text_widget.config(state='normal')
    
    content = """Hier ist die Zusammenfassung der analysierten Dokumente:

**Haupterkenntnisse:**
- Umsatz stieg um 15% gegenüber Vorjahr
- Neue Märkte in Asien erschlossen
- Digitalisierungsprojekte erfolgreich abgeschlossen

**Empfehlungen:**
1. Weitere Investitionen in KI-Technologie
2. Ausbau der internationalen Präsenz
3. Nachhaltigkeit als Kernstrategie

Die detaillierten Analysen finden Sie in den Quelldokumenten."""

    metadata = {
        'confidence': 92,
        'duration': 2.3,
        'sources_count': 5,
        'agents_count': 3
    }
    
    formatter._render_assistant_message_structured(
        content=content,
        timestamp_short="Heute 14:23",
        timestamp_full="Mittwoch, 9. Oktober 2025, 14:23:15",
        metadata=metadata,
        message_id="test_msg_1"
    )
    
    formatter.text_widget.config(state='disabled')

def test_placeholder_animation(formatter):
    """Test 4: Platzhalter mit Animation"""
    print("✅ Test 4: Platzhalter-Animation")
    
    formatter.insert_processing_placeholder("test_placeholder_1")
    
    # Simuliere Antwort nach 3 Sekunden
    def replace_after_delay():
        print("   → Ersetze Platzhalter mit Antwort")
        formatter.replace_placeholder_with_response(
            message_id="test_placeholder_1",
            content="Die Analyse ist abgeschlossen. Alle Dokumente wurden erfolgreich verarbeitet.",
            metadata={
                'confidence': 88,
                'duration': 3.2,
                'sources_count': 2,
                'agents_count': 1
            }
        )
    
    formatter.parent_window.after(3000, replace_after_delay)

def test_low_confidence_message(formatter):
    """Test 5: Message mit niedriger Confidence"""
    print("✅ Test 5: Niedrige Confidence")
    formatter.text_widget.config(state='normal')
    
    formatter._render_assistant_message_structured(
        content="Ich bin mir nicht sicher, aber möglicherweise bezieht sich Ihre Frage auf...",
        timestamp_short="Heute 14:25",
        metadata={
            'confidence': 45,
            'duration': 1.1,
            'sources_count': 1,
            'agents_count': 1
        },
        message_id="test_msg_low_conf"
    )
    
    formatter.text_widget.config(state='disabled')

def test_multiple_messages(formatter):
    """Test 6: Mehrere Messages hintereinander"""
    print("✅ Test 6: Performance-Test mit mehreren Messages")
    formatter.text_widget.config(state='normal')
    
    for i in range(5):
        # User-Message
        formatter._render_user_message(
            content=f"Frage {i+1}: Wie funktioniert Feature X?",
            timestamp_short=f"Heute 14:{30+i}",
            attachments=[]
        )
        
        # Assistant-Message
        formatter._render_assistant_message_structured(
            content=f"Antwort {i+1}: Feature X funktioniert durch...",
            timestamp_short=f"Heute 14:{30+i}",
            metadata={
                'confidence': 85 + (i % 10),
                'duration': 1.5 + (i * 0.3),
                'sources_count': 2 + (i % 3),
                'agents_count': 1 + (i % 2)
            },
            message_id=f"test_msg_{i}"
        )
    
    formatter.text_widget.config(state='disabled')

def run_all_tests():
    """Führt alle Tests aus"""
    print("\n" + "="*60)
    print("🧪 VERITAS Chat-Design Test Suite")
    print("="*60 + "\n")
    
    root, formatter = create_test_window()
    
    # Tests ausführen
    test_user_message_simple(formatter)
    test_user_message_with_attachments(formatter)
    test_assistant_message_structured(formatter)
    test_low_confidence_message(formatter)
    test_multiple_messages(formatter)
    
    print("\n⏳ Warte 2 Sekunden, dann starte Platzhalter-Test...")
    root.after(2000, lambda: test_placeholder_animation(formatter))
    
    print("\n" + "="*60)
    print("✅ Alle Tests gestartet!")
    print("💡 Teste folgende Features:")
    print("   - Rechtsbündige User-Bubbles mit Anhängen")
    print("   - Strukturierte Assistant-Messages mit Metriken")
    print("   - Feedback-Widget (👍👎💬)")
    print("   - Platzhalter-Animation (nach 2s)")
    print("   - Confidence-Badges (🟢🟡🔴)")
    print("="*60 + "\n")
    
    root.mainloop()

if __name__ == "__main__":
    run_all_tests()
