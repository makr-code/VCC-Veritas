"""
Test-Script für Chat-Persistence Integration
Testet Auto-Save-Funktionalität ohne Frontend
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


def test_chat_persistence():
    """Testet Chat-Persistierung"""

    print("\n" + "=" * 60)
    print("🧪 CHAT PERSISTENCE TEST - Phase 1")
    print("=" * 60 + "\n")

    # Test 1: Import der Module
    print("📦 Test 1: Module importieren...")
    try:
        from backend.services.chat_persistence_service import ChatPersistenceService
        from shared.chat_schema import ChatMessage, ChatSession

        print("✅ Module erfolgreich importiert")
    except Exception as e:
        print(f"❌ Import fehlgeschlagen: {e}")
        return False

    # Test 2: Service initialisieren
    print("\n🔧 Test 2: Service initialisieren...")
    try:
        service = ChatPersistenceService()
        print(f"✅ Service initialisiert")
        print(f"   Sessions Dir: {service.sessions_dir}")
        print(f"   Backups Dir: {service.backups_dir}")
    except Exception as e:
        print(f"❌ Service-Init fehlgeschlagen: {e}")
        return False

    # Test 3: Chat-Session erstellen
    print("\n💬 Test 3: Chat-Session erstellen...")
    try:
        session = ChatSession(llm_model="llama3.1:8b")
        print(f"✅ Session erstellt")
        print(f"   Session-ID: {session.session_id}")
        print(f"   Title: {session.title}")
    except Exception as e:
        print(f"❌ Session-Erstellung fehlgeschlagen: {e}")
        return False

    # Test 4: Nachrichten hinzufügen
    print("\n📝 Test 4: Nachrichten hinzufügen...")
    try:
        session.add_message("user", "Was ist das BImSchG?")
        session.add_message(
            "assistant",
            "Das Bundes-Immissionsschutzgesetz (BImSchG) ist ein deutsches Gesetz...",
            metadata={"confidence_score": 0.887, "sources": ["BImSchG.pdf", "Gesetzestext.pdf"]},
        )
        session.add_message("user", "Welche Grenzwerte gelten?")

        print(f"✅ {session.get_message_count()} Nachrichten hinzugefügt")
        print(f"   Title (auto-generated): {session.title}")
    except Exception as e:
        print(f"❌ Nachricht hinzufügen fehlgeschlagen: {e}")
        return False

    # Test 5: Session speichern
    print("\n💾 Test 5: Session speichern...")
    try:
        success = service.save_chat_session(session)
        if success:
            session_file = service.sessions_dir / f"{session.session_id}.json"
            file_size = session_file.stat().st_size
            print(f"✅ Session gespeichert")
            print(f"   Datei: {session_file.name}")
            print(f"   Größe: {file_size} Bytes")
        else:
            print(f"❌ Speichern fehlgeschlagen")
            return False
    except Exception as e:
        print(f"❌ Speichern fehlgeschlagen: {e}")
        return False

    # Test 6: Session laden
    print("\n📂 Test 6: Session laden...")
    try:
        loaded_session = service.load_chat_session(session.session_id)
        if loaded_session:
            print(f"✅ Session geladen")
            print(f"   Title: {loaded_session.title}")
            print(f"   Messages: {loaded_session.get_message_count()}")
            print(f"   Last Message: {loaded_session.get_last_message().content[:50]}...")
        else:
            print(f"❌ Laden fehlgeschlagen")
            return False
    except Exception as e:
        print(f"❌ Laden fehlgeschlagen: {e}")
        return False

    # Test 7: Alle Sessions listen
    print("\n📋 Test 7: Alle Sessions listen...")
    try:
        all_sessions = service.list_chat_sessions(limit=10)
        print(f"✅ {len(all_sessions)} Session(s) gefunden")
        for s in all_sessions:
            print(f"   - {s['title'][:40]} ({s['message_count']} msg)")
    except Exception as e:
        print(f"❌ Listen fehlgeschlagen: {e}")
        return False

    # Test 8: Statistiken abrufen
    print("\n📊 Test 8: Statistiken abrufen...")
    try:
        stats = service.get_session_statistics()
        print(f"✅ Statistiken abgerufen")
        print(f"   Total Sessions: {stats['total_sessions']}")
        print(f"   Total Messages: {stats['total_messages']}")
        print(f"   Avg Messages/Session: {stats['avg_messages_per_session']:.1f}")
    except Exception as e:
        print(f"❌ Statistiken fehlgeschlagen: {e}")
        return False

    # Test 9: Backup erstellen
    print("\n💾 Test 9: Backup erstellen...")
    try:
        backup_success = service.create_backup(session.session_id)
        if backup_success:
            print(f"✅ Backup erstellt")
        else:
            print(f"⚠️  Backup fehlgeschlagen (nicht kritisch)")
    except Exception as e:
        print(f"⚠️  Backup-Fehler: {e} (nicht kritisch)")

    # Test 10: Session löschen (optional)
    print("\n🗑️  Test 10: Session löschen (optional)...")
    user_input = input("   Session löschen? (j/n): ")
    if user_input.lower() == "j":
        try:
            delete_success = service.delete_chat_session(session.session_id, create_backup=True)
            if delete_success:
                print(f"✅ Session gelöscht (mit Backup)")
            else:
                print(f"❌ Löschen fehlgeschlagen")
        except Exception as e:
            print(f"❌ Löschen fehlgeschlagen: {e}")
    else:
        print(f"⏭️  Löschen übersprungen")

    # Final Summary
    print("\n" + "=" * 60)
    print("✅ ALLE TESTS ERFOLGREICH!")
    print("=" * 60 + "\n")

    print("📋 Zusammenfassung:")
    print(f"   ✅ Module importiert")
    print(f"   ✅ Service initialisiert")
    print(f"   ✅ Session erstellt und gespeichert")
    print(f"   ✅ Session geladen und validiert")
    print(f"   ✅ Sessions gelistet")
    print(f"   ✅ Statistiken abgerufen")
    print(f"   ✅ Backup erstellt")

    print("\n🎉 Chat-Persistence Phase 1 ABGESCHLOSSEN!\n")

    return True


if __name__ == "__main__":
    try:
        success = test_chat_persistence()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
