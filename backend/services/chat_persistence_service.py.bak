"""
VERITAS Chat Persistence Service
================================

Service für Speicherung und Verwaltung von Chat-Sessions.

Features:
- Auto-Save nach jeder Nachricht
- JSON-basierte Persistierung
- Automatische Backups
- Session-Verwaltung (Liste, Laden, Löschen)

Version: v3.20.0
Author: VERITAS Team
Date: 12. Oktober 2025
"""

import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from shared.chat_schema import ChatSession

logger = logging.getLogger(__name__)


class ChatPersistenceService:
    """Service für Chat-Session-Persistierung"""

    def __init__(
        self,
        sessions_dir: str = "data/chat_sessions",
        backups_dir: str = "data/chat_backups",
        max_file_size_mb: int = 10,
        auto_backup_days: int = 1,
    ):
        """
        Initialisiert Chat Persistence Service

        Args:
            sessions_dir: Verzeichnis für Chat-Sessions
            backups_dir: Verzeichnis für Backups
            max_file_size_mb: Maximale Dateigröße (Warnung)
            auto_backup_days: Backup-Intervall in Tagen
        """
        self.sessions_dir = Path(sessions_dir)
        self.backups_dir = Path(backups_dir)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.auto_backup_days = auto_backup_days

        # Erstelle Verzeichnisse falls nicht vorhanden
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"✅ ChatPersistenceService initialisiert")
        logger.info(f"   Sessions: {self.sessions_dir}")
        logger.info(f"   Backups: {self.backups_dir}")

    def save_chat_session(self, session: ChatSession) -> bool:
        """
        Speichert Chat-Session als JSON-Datei

        Args:
            session: ChatSession-Objekt

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            session_file = self.sessions_dir / f"{session.session_id}.json"

            # Update timestamp
            session.updated_at = datetime.now()

            # Konvertiere zu dict
            session_data = session.to_dict()

            # Speichere als JSON (pretty-printed)
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            # File-Size Check
            file_size = session_file.stat().st_size
            if file_size > self.max_file_size_bytes:
                logger.warning(f"⚠️  Session-Datei sehr groß: {file_size / 1024 / 1024:.2f} MB")

            logger.debug(f"💾 Chat-Session gespeichert: {session.session_id} ({session.title})")
            return True

        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Session: {e}", exc_info=True)
            return False

    def load_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Lädt Chat-Session aus JSON-Datei

        Args:
            session_id: Eindeutige Session-ID

        Returns:
            ChatSession-Objekt oder None bei Fehler
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"

            if not session_file.exists():
                logger.warning(f"⚠️  Session-Datei nicht gefunden: {session_id}")
                return None

            # Lade JSON
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Konvertiere zu ChatSession
            session = ChatSession.from_dict(session_data)

            logger.debug(f"📂 Chat-Session geladen: {session_id} ({session.title})")
            return session

        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Session: {e}", exc_info=True)
            return None

    def list_chat_sessions(
        self, limit: Optional[int] = None, sort_by: str = "updated_at", reverse: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Listet alle Chat-Sessions auf

        Args:
            limit: Maximale Anzahl (None = alle)
            sort_by: Sortier-Feld ('created_at', 'updated_at', 'title')
            reverse: Absteigende Sortierung (neueste zuerst)

        Returns:
            Liste von Session-Metadaten
        """
        try:
            session_files = list(self.sessions_dir.glob("*.json"))
            sessions_info = []

            for session_file in session_files:
                try:
                    # Lade nur Metadaten (nicht alle Messages)
                    with open(session_file, "r", encoding="utf-8") as f:
                        session_data = json.load(f)

                    sessions_info.append(
                        {
                            "session_id": session_data["session_id"],
                            "title": session_data["title"],
                            "created_at": session_data["created_at"],
                            "updated_at": session_data["updated_at"],
                            "message_count": len(session_data.get("messages", [])),
                            "llm_model": session_data.get("llm_model", "unknown"),
                            "file_path": str(session_file),
                        }
                    )
                except Exception as e:
                    logger.warning(f"⚠️  Konnte Session nicht lesen: {session_file} - {e}")
                    continue

            # Sortiere
            if sort_by in ["created_at", "updated_at"]:
                sessions_info.sort(key=lambda x: datetime.fromisoformat(x[sort_by]), reverse=reverse)
            elif sort_by == "title":
                sessions_info.sort(key=lambda x: x["title"].lower(), reverse=reverse)

            # Limitiere
            if limit:
                sessions_info = sessions_info[:limit]

            logger.debug(f"📋 {len(sessions_info)} Chat-Sessions gefunden")
            return sessions_info

        except Exception as e:
            logger.error(f"❌ Fehler beim Listen der Sessions: {e}", exc_info=True)
            return []

    def delete_chat_session(self, session_id: str, create_backup: bool = True) -> bool:
        """
        Löscht Chat-Session

        Args:
            session_id: Eindeutige Session-ID
            create_backup: Backup vor Löschung erstellen

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"

            if not session_file.exists():
                logger.warning(f"⚠️  Session-Datei nicht gefunden: {session_id}")
                return False

            # Optional: Backup erstellen
            if create_backup:
                self.create_backup(session_id)

            # Lösche Datei
            session_file.unlink()

            logger.info(f"🗑️  Chat-Session gelöscht: {session_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen der Session: {e}", exc_info=True)
            return False

    def create_backup(self, session_id: Optional[str] = None) -> bool:
        """
        Erstellt Backup von Session(s)

        Args:
            session_id: Spezifische Session (None = alle Sessions)

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = self.backups_dir / timestamp
            backup_subdir.mkdir(parents=True, exist_ok=True)

            if session_id:
                # Backup einer Session
                session_file = self.sessions_dir / f"{session_id}.json"
                if session_file.exists():
                    backup_file = backup_subdir / session_file.name
                    shutil.copy2(session_file, backup_file)
                    logger.info(f"💾 Backup erstellt: {session_id}")
                else:
                    logger.warning(f"⚠️  Session nicht gefunden: {session_id}")
                    return False
            else:
                # Backup aller Sessions
                session_files = list(self.sessions_dir.glob("*.json"))
                for session_file in session_files:
                    backup_file = backup_subdir / session_file.name
                    shutil.copy2(session_file, backup_file)

                logger.info(f"💾 Backup aller Sessions erstellt: {len(session_files)} Dateien")

            return True

        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Backups: {e}", exc_info=True)
            return False

    def auto_backup_if_needed(self) -> bool:
        """
        Erstellt automatisches Backup falls notwendig (basierend auf letztem Backup)

        Returns:
            True wenn Backup erstellt wurde, False sonst
        """
        try:
            # Finde letztes Backup
            backup_dirs = sorted(self.backups_dir.glob("*"), reverse=True)

            if not backup_dirs:
                # Kein Backup vorhanden -> Erstelle erstes
                logger.info("📦 Erstes Auto-Backup wird erstellt...")
                return self.create_backup()

            # Prüfe Alter des letzten Backups
            last_backup_dir = backup_dirs[0]
            last_backup_time = datetime.strptime(last_backup_dir.name, "%Y%m%d_%H%M%S")

            days_since_backup = (datetime.now() - last_backup_time).days

            if days_since_backup >= self.auto_backup_days:
                logger.info(f"📦 Auto-Backup wird erstellt (letztes Backup: {days_since_backup} Tage alt)...")
                return self.create_backup()

            return False

        except Exception as e:
            logger.error(f"❌ Fehler beim Auto-Backup: {e}", exc_info=True)
            return False

    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über alle Sessions zurück

        Returns:
            Dict mit Statistiken
        """
        try:
            sessions = self.list_chat_sessions()

            if not sessions:
                return {
                    "total_sessions": 0,
                    "total_messages": 0,
                    "avg_messages_per_session": 0,
                    "oldest_session": None,
                    "newest_session": None,
                }

            total_messages = sum(s["message_count"] for s in sessions)
            avg_messages = total_messages / len(sessions)

            oldest_session = min(sessions, key=lambda x: datetime.fromisoformat(x["created_at"]))
            newest_session = max(sessions, key=lambda x: datetime.fromisoformat(x["created_at"]))

            return {
                "total_sessions": len(sessions),
                "total_messages": total_messages,
                "avg_messages_per_session": avg_messages,
                "oldest_session": {
                    "session_id": oldest_session["session_id"],
                    "title": oldest_session["title"],
                    "created_at": oldest_session["created_at"],
                },
                "newest_session": {
                    "session_id": newest_session["session_id"],
                    "title": newest_session["title"],
                    "created_at": newest_session["created_at"],
                },
            }

        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Statistiken: {e}", exc_info=True)
            return {}


# Example Usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)

    # Initialize service
    service = ChatPersistenceService()

    # Create sample session
    from shared.chat_schema import ChatSession

    session = ChatSession()
    session.add_message("user", "Was ist das BImSchG?")
    session.add_message("assistant", "Das Bundes-Immissionsschutzgesetz...", metadata={"confidence": 0.887})

    # Save session
    service.save_chat_session(session)

    # List sessions
    sessions = service.list_chat_sessions(limit=10)
    print(f"\n📋 Sessions: {len(sessions)}")
    for s in sessions:
        print(f"  - {s['title']} ({s['message_count']} Nachrichten)")

    # Load session
    loaded = service.load_chat_session(session.session_id)
    print(f"\n📂 Geladen: {loaded.title}")

    # Statistics
    stats = service.get_session_statistics()
    print(f"\n📊 Statistiken:")
    print(f"  Total Sessions: {stats['total_sessions']}")
    print(f"  Total Messages: {stats['total_messages']}")
    print(f"  Avg Messages/Session: {stats['avg_messages_per_session']:.1f}")

    # Backup
    service.create_backup()
