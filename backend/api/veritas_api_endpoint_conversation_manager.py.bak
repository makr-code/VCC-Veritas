#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys.
Modification will be detected and may result in license violations.
"""


import sqlite3

from flask import Flask, jsonify

app = Flask(__name__)

import json
import logging
import sqlite3
import uuid
from datetime import datetime

from config import DATABASE_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s [%(module)s] - %(message)s")


def init_conversation_db():
    """
    Initialisiert die SQLite-Datenbank und erstellt die notwendigen Tabellen,
    falls sie noch nicht existieren.
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Tabelle für Konversationen (Sessions)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                last_active_time TEXT NOT NULL,
                user_id TEXT NOT NULL -- Um Konversationen Usern zuzuordnen
            )
        """
        )

        # Tabelle für einzelne Gesprächsrunden (Turns)
        # Enthält Fragen, Antworten, verwendete Chunks und Feedback
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_turns (
                turn_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                turn_number INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                retrieved_chunk_ids TEXT, -- JSON-Array der verwendeten Chunk-IDs
                feedback TEXT, -- 'positive', 'negative', NULL
                feedback_timestamp TEXT,
                user_id TEXT NOT NULL, -- user_id vom Turn für direkte Zuordnung
                FOREIGN KEY (session_id) REFERENCES conversations (session_id)
            )
        """
        )

        conn.commit()
        logging.info(f"Datenbank '{DATABASE_FILE}' und Tabellen erfolgreich initialisiert.")
    except sqlite3.Error as e:
        logging.error(f"Fehler beim Initialisieren der Datenbank: {e}")
    finally:
        if conn:
            conn.close()


def _ensure_db_initialized():
    """
    Stellt sicher, dass die Datenbank und Tabellen existieren.
    Wird automatisch bei der ersten Nutzung aufgerufen.
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Prüfe, ob conversations Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations';")
        if not cursor.fetchone():
            # Tabellen existieren nicht, initialisiere sie
            conn.close()
            init_conversation_db()
            logging.info("Datenbank automatisch initialisiert")
        else:
            conn.close()
    except sqlite3.Error as e:
        logging.error(f"Fehler bei automatischer Datenbankinitialisierung: {e}")


def create_new_conversation(user_id: str) -> str:
    """
    Erstellt eine neue Konversation (Session) und gibt die Session-ID zurück.
    """
    # Automatische Datenbankinitialisierung sicherstellen
    _ensure_db_initialized()

    conn = None
    try:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (session_id, start_time, last_active_time, user_id) VALUES (?, ?, ?, ?)",
            (session_id, now, now, user_id),
        )
        conn.commit()
        logging.info(f"Neue Konversation gestartet: {session_id} für User {user_id}")
        return session_id
    except sqlite3.Error as e:
        logging.error(f"Fehler beim Erstellen einer neuen Konversation: {e}")
        return None
    finally:
        if conn:
            conn.close()


def add_turn_to_conversation(session_id: str, question: str, answer: str, retrieved_chunk_ids: list, user_id: str) -> str:
    """
    Fügt eine Frage-Antwort-Runde zu einer bestehenden Konversation hinzu.
    """
    conn = None
    turn_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Ermittle die Turn-Nummer
        cursor.execute("SELECT COUNT(*) FROM conversation_turns WHERE session_id = ?", (session_id,))
        turn_number = cursor.fetchone()[0] + 1

        cursor.execute(
            """INSERT INTO conversation_turns (turn_id, session_id, turn_number, question, answer, timestamp, retrieved_chunk_ids, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (turn_id, session_id, turn_number, question, answer, now, json.dumps(retrieved_chunk_ids), user_id),
        )
        # Aktualisiere die 'last_active_time' der Konversation
        cursor.execute("UPDATE conversations SET last_active_time = ? WHERE session_id = ?", (now, session_id))
        conn.commit()
        logging.info(f"Turn {turn_number} für Session {session_id} hinzugefügt.")
        return turn_id
    except sqlite3.Error as e:
        logging.error(f"Fehler beim Hinzufügen einer Konversationsrunde: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_conversation_history(session_id: str, limit: int = 5) -> list:
    """
    Ruft den Verlauf der letzten 'limit' Frage-Antwort-Runden für eine Session ab.
    Format für LLM: [("human", "frage"), ("ai", "antwort"), ...]
    """
    conn = None
    history = []
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT question, answer FROM conversation_turns WHERE session_id = ? ORDER BY turn_number DESC LIMIT ?",
            (session_id, limit),
        )
        # Ergebnisse in umgekehrter Reihenfolge holen, da DESC LIMIT die neuesten zuerst liefert
        # aber die Historie für das LLM in chronologischer Reihenfolge sein sollte
        raw_history = cursor.fetchall()
        for q, a in reversed(raw_history):
            history.append(("human", q))
            history.append(("ai", a))
        logging.debug(f"Konversationshistorie für Session {session_id} abgerufen (letzte {len(history)/2} Runden).")
    except sqlite3.Error as e:
        logging.error(f"Fehler beim Abrufen der Konversationshistorie: {e}")
    finally:
        if conn:
            conn.close()
    return history


def get_all_conversations():
    """
    Ruft eine Liste aller Konversationen mit ihren IDs und einem Titel ab.
    Der Titel ist die erste Frage in der Konversation.
    """
    # Automatische Datenbankinitialisierung sicherstellen
    _ensure_db_initialized()

    conn = None
    conversations = []
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        # Verwenden Sie eine Unterabfrage, um die erste Frage als Titel zu erhalten
        # Verwenden Sie COALESCE, um Konversationen ohne Runden zu behandeln
        query = """
            SELECT
                c.session_id,
                c.start_time,
                COALESCE(
                    (SELECT question FROM conversation_turns ct
                     WHERE ct.session_id = c.session_id
                     ORDER BY ct.turn_number ASC LIMIT 1),
                    'Neue Konversation'
                ) as title
            FROM conversations c
            ORDER BY c.last_active_time DESC
        """
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            conversations.append(
                {
                    "session_id": row[0],
                    "start_time": row[1],
                    "title": row[2][:50] + "..." if len(row[2]) > 50 else row[2],  # Titel kürzen
                }
            )
        logging.info(f"{len(conversations)} Konversationen abgerufen.")
    except sqlite3.Error as e:
        logging.error(f"Fehler beim Abrufen aller Konversationen: {e}")
    finally:
        if conn:
            conn.close()

    return conversations


def update_feedback(turn_id: str, feedback_type: str):
    """
    Aktualisiert das Feedback für einen spezifischen Konversations-Turn.
    feedback_type kann 'positive' oder 'negative' sein.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "UPDATE conversation_turns SET feedback = ?, feedback_timestamp = ? WHERE turn_id = ?",
            (feedback_type, now, turn_id),
        )
        conn.commit()
        logging.info(f"Feedback '{feedback_type}' für Turn {turn_id} gespeichert.")
    except sqlite3.Error as e:
        logging.error(f"Fehler beim Speichern von Feedback für Turn {turn_id}: {e}")
    finally:
        if conn:
            conn.close()


def get_turn_details(turn_id: str) -> dict:
    """
    Holt alle Details zu einem spezifischen Turn (Frage-Antwort-Runde).
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT turn_id, session_id, turn_number, question, answer, timestamp, retrieved_chunk_ids, feedback, feedback_timestamp, user_id FROM conversation_turns WHERE turn_id = ?",
            (turn_id,),
        )
        row = cursor.fetchone()
        if row:
            # retrieved_chunk_ids als Liste dekodieren
            try:
                chunk_ids = json.loads(row[6]) if row[6] else []
            except Exception:
                chunk_ids = []
            return {
                "turn_id": row[0],
                "session_id": row[1],
                "turn_number": row[2],
                "question": row[3],
                "answer": row[4],
                "timestamp": row[5],
                "retrieved_chunk_ids": chunk_ids,
                "feedback": row[7],
                "feedback_timestamp": row[8],
                "user_id": row[9],
            }
        else:
            return {"error": "Turn nicht gefunden"}
    except sqlite3.Error as e:
        return {"error": f"DB-Fehler: {e}"}
    finally:
        if conn:
            conn.close()


# --- Testfunktionen ---
if __name__ == "__main__":
    print("Starte Selbsttest für conversation_db_manager.py...")
    test_results = {}
    # 1. Datenbank initialisieren
    init_conversation_db()

    test_user_id = "test_user_alpha_007"

    # 2. Neue Konversation erstellen
    test_session_id = create_new_conversation(test_user_id)
    test_results["session_id"] = test_session_id
    if test_session_id:
        print(f"\nNeue Session erstellt: {test_session_id}")

        # 3. Runden zur Konversation hinzufügen
        print("\nFüge Runden zur Konversation hinzu...")
        turn1_id = add_turn_to_conversation(
            session_id=test_session_id,
            question="Was ist die DSGVO?",
            answer="Die DSGVO ist eine Verordnung der Europäischen Union...",
            retrieved_chunk_ids=["chunk_a1", "chunk_a2"],
            user_id=test_user_id,
        )
        print(f"Runde 1 hinzugefügt mit Turn ID: {turn1_id}")
        test_results["turn1_id"] = turn1_id

        turn2_id = add_turn_to_conversation(
            session_id=test_session_id,
            question="Wer ist der Verantwortliche?",
            answer="Der Verantwortliche ist die natürliche oder juristische Person...",
            retrieved_chunk_ids=["chunk_b1"],
            user_id=test_user_id,
        )
        print(f"Runde 2 hinzugefügt mit Turn ID: {turn2_id}")
        test_results["turn2_id"] = turn2_id

        # 4. Konversationshistorie abrufen
        print("\nKonversationshistorie:")
        history = get_conversation_history(test_session_id)
        for role, text in history:
            print(f"[{role}]: {text}")
        test_results["history"] = history

        # 5. Feedback für eine Runde aktualisieren
        if turn1_id:
            print(f"\nSende positives Feedback für Turn {turn1_id} (Runde 1).")
            update_feedback(turn1_id, "positive")

        if turn2_id:
            print(f"\nSende negatives Feedback für Turn {turn2_id} (Runde 2).")
            update_feedback(turn2_id, "negative")

        # 6. Details eines Turns abrufen (um Feedback zu überprüfen)
        print(f"\nDetails von Turn {turn1_id}:")
        details1 = get_turn_details(turn1_id)
        print(json.dumps(details1, indent=2))
        test_results["details1"] = details1

        print(f"\nDetails von Turn {turn2_id}:")
        details2 = get_turn_details(turn2_id)
        print(json.dumps(details2, indent=2))
        test_results["details2"] = details2

        # 7. Test: Abruf aller Konversationen
        print("\nAlle Konversationen:")
        all_convs = get_all_conversations()
        print(json.dumps(all_convs, indent=2))
        test_results["all_conversations"] = all_convs

    print("\nSelbsttest beendet.")

"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys.
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "api_endpoint_conversation_dw_manager"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...NzRkYzhl"  # Gekuerzt fuer Sicherheit
module_organization_key = "6f5304c29594443086e1ace0011c094614b612c22aa16af9f1a63f02a0c9bf5c"
module_file_key = "ec67089e88361627841e8b62c6e445f5fd53532983f90cdfa00a9fe29dbbf1eb"
module_version = "1.0"
module_protection_level = 3
# === END PROTECTION KEYS ===
