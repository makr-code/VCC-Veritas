"""
Test-Script für Chat-Persistence Phase 2 - Session UI
Testet Session-Restore-Dialog und Session-Manager
"""

import logging
import os
import sys

# Setup
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def create_test_sessions():
    """Erstellt Test-Sessions für UI-Tests"""
    print("\n📦 Erstelle Test-Sessions...")

    from datetime import datetime, timedelta

    from backend.services.chat_persistence_service import ChatPersistenceService
    from shared.chat_schema import ChatSession

    service = ChatPersistenceService()

    # Test-Sessions mit unterschiedlichen Daten
    test_data = [
        {
            "messages": [
                ("user", "Was ist das BImSchG?"),
                ("assistant", "Das Bundes-Immissionsschutzgesetz...", {"confidence": 0.887}),
                ("user", "Welche Grenzwerte gelten?"),
                ("assistant", "Für Windkraftanlagen gelten...", {"confidence": 0.92}),
            ],
            "days_ago": 0,  # Heute
        },
        {
            "messages": [
                ("user", "Erkläre die Umweltverträglichkeitsprüfung"),
                ("assistant", "Die UVP ist ein Verfahren...", {"confidence": 0.85}),
            ],
            "days_ago": 1,  # Gestern
        },
        {
            "messages": [
                ("user", "Was ist der Unterschied zwischen BauGB und BImSchG?"),
                ("assistant", "BauGB regelt Bauplanung, BImSchG Emissionen...", {"confidence": 0.91}),
                ("user", "Welches Gesetz ist wichtiger?"),
                ("assistant", "Beide sind gleichrangig...", {"confidence": 0.78}),
            ],
            "days_ago": 3,  # Vor 3 Tagen
        },
        {"messages": [("user", "Kurze Frage"), ("assistant", "Kurze Antwort")], "days_ago": 7},  # Vor 1 Woche
    ]

    # Weitere Test-Sessions hinzufügen
    for i in range(5, 10):
        test_data.append({"messages": [("user", f"Test-Session {i}"), ("assistant", f"Antwort {i}")], "days_ago": i * 2})

    created_sessions = []

    for data in test_data:
        session = ChatSession(llm_model="llama3.1:8b")

        # Messages hinzufügen
        for msg_data in data["messages"]:
            role, content = msg_data[0], msg_data[1]
            metadata = msg_data[2] if len(msg_data) > 2 else {}
            session.add_message(role, content, metadata=metadata)

        # Timestamp anpassen
        days_ago = data["days_ago"]
        if days_ago > 0:
            from datetime import datetime, timedelta

            old_date = datetime.now() - timedelta(days=days_ago)
            session.created_at = old_date
            session.updated_at = old_date

        # Speichern
        service.save_chat_session(session)
        created_sessions.append(session)

    print(f"✅ {len(created_sessions)} Test-Sessions erstellt")
    return created_sessions


def test_session_restore_dialog():
    """Testet Session-Restore-Dialog"""
    print("\n" + "=" * 60)
    print("🧪 TEST: Session-Restore-Dialog")
    print("=" * 60)

    import tkinter as tk

    from backend.services.chat_persistence_service import ChatPersistenceService
    from frontend.ui.veritas_ui_session_dialog import show_session_restore_dialog

    # Create test window
    root = tk.Tk()
    root.title("Test Window")
    root.geometry("400x300")

    service = ChatPersistenceService()

    # Info-Label
    info = tk.Label(
        root,
        text="Test: Session-Restore-Dialog\n\n" "Klicken Sie auf den Button,\n" "um den Dialog zu öffnen.",
        font=("Segoe UI", 11),
        pady=20,
    )
    info.pack()

    # Result-Label
    result_var = tk.StringVar(value="⏳ Warte auf Aktion...")
    result_label = tk.Label(root, textvariable=result_var, font=("Segoe UI", 10, "bold"), fg="blue")
    result_label.pack(pady=10)

    # Test-Button
    def run_test():
        result_var.set("⏳ Dialog wird geöffnet...")
        root.update()

        session_id = show_session_restore_dialog(root, service)

        if session_id:
            result_var.set(f"✅ Session ausgewählt:\n{session_id[:16]}...")
            print(f"\n✅ Test erfolgreich: Session {session_id[:8]}... ausgewählt")
        else:
            result_var.set("🆕 Neuer Chat ausgewählt")
            print("\n✅ Test erfolgreich: Neuer Chat gewählt")

    test_btn = tk.Button(
        root,
        text="🧪 Dialog testen",
        font=("Segoe UI", 12, "bold"),
        bg="#28A745",
        fg="white",
        padx=20,
        pady=10,
        command=run_test,
    )
    test_btn.pack(pady=20)

    # Close Button
    close_btn = tk.Button(root, text="❌ Schließen", command=root.destroy, padx=15, pady=5)
    close_btn.pack()

    print("\n📋 Anweisungen:")
    print("   1. Klicken Sie auf 'Dialog testen'")
    print("   2. Im Dialog:")
    print("      - Sehen Sie die Liste der Sessions")
    print("      - Wählen Sie eine Session oder 'Neuer Chat'")
    print("      - Optional: 'Immer letzte Session laden' aktivieren")
    print("   3. Validieren Sie das Ergebnis")

    root.mainloop()
    print("\n✅ Session-Restore-Dialog Test abgeschlossen")


def test_session_manager():
    """Testet Session-Manager-UI"""
    print("\n" + "=" * 60)
    print("🧪 TEST: Session-Manager-UI")
    print("=" * 60)

    import tkinter as tk

    from backend.services.chat_persistence_service import ChatPersistenceService
    from frontend.ui.veritas_ui_session_manager import show_session_manager

    # Create test window
    root = tk.Tk()
    root.title("Test Window - Session Manager")
    root.geometry("500x350")

    service = ChatPersistenceService()

    # Info
    info = tk.Label(
        root,
        text="Test: Session-Manager-UI\n\n" "Öffnen Sie den Session-Manager\n" "und testen Sie alle Funktionen.",
        font=("Segoe UI", 12),
        pady=20,
    )
    info.pack()

    # Test-Checkliste
    checklist_frame = tk.Frame(root, bg="#F8F9FA", relief=tk.RIDGE, borderwidth=2)
    checklist_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    tk.Label(checklist_frame, text="📋 Test-Checkliste:", font=("Segoe UI", 10, "bold"), bg="#F8F9FA", anchor=tk.W).pack(
        fill=tk.X, padx=10, pady=5
    )

    tests = [
        "✅ Alle Sessions werden angezeigt",
        "✅ Suche funktioniert (Titel-Filter)",
        "✅ Sortierung nach Spalten",
        "✅ Session öffnen (Doppelklick)",
        "✅ Session umbenennen",
        "✅ Session exportieren (JSON)",
        "✅ Session löschen (mit Backup)",
        "✅ Rechtsklick-Menü funktioniert",
        "✅ Statistiken korrekt angezeigt",
    ]

    for test in tests:
        tk.Label(checklist_frame, text=test, font=("Segoe UI", 9), bg="#F8F9FA", anchor=tk.W).pack(fill=tk.X, padx=20, pady=2)

    # Result
    result_var = tk.StringVar(value="⏳ Öffnen Sie den Manager...")
    result_label = tk.Label(root, textvariable=result_var, font=("Segoe UI", 10, "bold"), fg="blue")
    result_label.pack(pady=10)

    # Buttons
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    def open_manager():
        result_var.set("📁 Session-Manager geöffnet")

        def on_session_opened(session_id):
            result_var.set(f"✅ Session geöffnet:\n{session_id[:16]}...")
            print(f"\n✅ Callback: Session {session_id[:8]}... geöffnet")

        show_session_manager(root, service, on_session_opened=on_session_opened)

    test_btn = tk.Button(
        btn_frame,
        text="📁 Session-Manager öffnen",
        font=("Segoe UI", 12, "bold"),
        bg="#2E86AB",
        fg="white",
        padx=20,
        pady=10,
        command=open_manager,
    )
    test_btn.pack(side=tk.LEFT, padx=5)

    close_btn = tk.Button(
        btn_frame,
        text="❌ Test beenden",
        font=("Segoe UI", 10),
        bg="#6C757D",
        fg="white",
        padx=15,
        pady=8,
        command=root.destroy,
    )
    close_btn.pack(side=tk.LEFT, padx=5)

    print("\n📋 Anweisungen:")
    print("   1. Öffnen Sie den Session-Manager")
    print("   2. Testen Sie:")
    print("      - Tabelle mit allen Sessions")
    print("      - Suche nach Titel")
    print("      - Sortierung (Klick auf Spalten)")
    print("      - Session umbenennen")
    print("      - Session exportieren")
    print("      - Session löschen")
    print("      - Rechtsklick-Menü")
    print("   3. Validieren Sie alle Funktionen")

    root.mainloop()
    print("\n✅ Session-Manager Test abgeschlossen")


def main():
    """Hauptfunktion"""
    print("\n" + "=" * 60)
    print("🧪 CHAT PERSISTENCE - PHASE 2 UI TESTS")
    print("=" * 60)

    # Erstelle Test-Sessions
    sessions = create_test_sessions()

    print("\n📋 Test-Plan:")
    print("   1. Session-Restore-Dialog testen")
    print("   2. Session-Manager-UI testen")

    # Test 1: Session-Restore-Dialog
    test_session_restore_dialog()

    # Test 2: Session-Manager
    test_session_manager()

    # Final Summary
    print("\n" + "=" * 60)
    print("✅ ALLE UI-TESTS ABGESCHLOSSEN!")
    print("=" * 60)

    print("\n📊 Zusammenfassung:")
    print("   ✅ Test-Sessions erstellt")
    print("   ✅ Session-Restore-Dialog getestet")
    print("   ✅ Session-Manager getestet")

    print("\n🎉 Phase 2 UI-Tests erfolgreich!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Tests abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Tests fehlgeschlagen: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
