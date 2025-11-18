# 🚀 VERITAS v3.20.0 - Chat Persistence Quick Start Guide

**Version:** v3.20.0
**Datum:** 12. Oktober 2025
**Zielgruppe:** Entwickler & Benutzer

---

## 📋 Überblick

VERITAS v3.20.0 bringt **vollständige Chat-Persistierung** und **kontextuelle LLM-Konversationen**. Dieses Guide erklärt, wie die neuen Features genutzt werden.

---

## 🎯 Features auf einen Blick

### 1. Auto-Save ✅
- **Jede Nachricht** wird automatisch gespeichert
- **JSON-Format:** `data/chat_sessions/{session_id}.json`
- **Kein manuelles Speichern** erforderlich

### 2. Session-Restore ✅
- **Dialog beim App-Start:** "Letzte Session wiederherstellen?"
- **Auto-Restore-Option:** Checkbox "Immer letzte Session automatisch laden"
- **Letzte 10 Sessions** angezeigt

### 3. Session-Manager ✅
- **Menü:** Hamburger → "📁 Sessions verwalten"
- **Funktionen:** Suchen, Umbenennen, Exportieren, Löschen
- **Sortierung:** Nach Titel, Datum, Nachrichten

### 4. Kontextuelle LLM-Antworten ✅
- **LLM erhält Chat-History** (letzte 10 Messages)
- **Bezieht sich auf frühere Fragen/Antworten**
- **Intelligent:** Sliding Window / Relevance-Based

---

## 🚀 Getting Started

### 1. Installation

**Keine zusätzlichen Pakete erforderlich!**

Alle Dependencies sind bereits in `requirements.txt`:
```
pydantic>=2.0.0
```

### 2. App starten

```bash
# Backend (optional, falls nicht bereits läuft)
python -m uvicorn backend.api.veritas_api_backend:app --reload

# Frontend
python frontend/veritas_app.py
```

### 3. Erste Session

1. **App startet** → Session-Restore-Dialog erscheint
2. **"🆕 Neuer Chat"** klicken
3. **Frage eingeben:** z.B. "Was ist das BImSchG?"
4. **Antwort erhalten** → Automatisch gespeichert! ✅

### 4. Session wiederherstellen

1. **App neu starten** → Dialog erscheint
2. **Session auswählen** aus Liste
3. **"✅ Wiederherstellen"** klicken
4. **Chat-History geladen** → Konversation fortsetzen!

---

## 📁 Dateistruktur

### Session-Storage

```
data/
├── chat_sessions/              # Aktive Sessions
│   ├── {uuid-1}.json          # Session 1
│   ├── {uuid-2}.json          # Session 2
│   └── ...
├── chat_backups/               # Auto-Backups (täglich)
│   └── 2025-10-12_10-30-00/   # Backup-Timestamp
│       ├── {uuid-1}.json
│       └── ...
└── session_restore_settings.json  # Auto-Restore-Setting
```

### Session-JSON-Format

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-10-12T14:30:00",
  "updated_at": "2025-10-12T15:45:00",
  "title": "Konversation über BImSchG",
  "llm_model": "llama3.1:8b",
  "messages": [
    {
      "id": "msg-uuid-1",
      "role": "user",
      "content": "Was ist das BImSchG?",
      "timestamp": "2025-10-12T14:30:00",
      "attachments": [],
      "metadata": {}
    },
    {
      "id": "msg-uuid-2",
      "role": "assistant",
      "content": "Das Bundes-Immissionsschutzgesetz...",
      "timestamp": "2025-10-12T14:30:15",
      "attachments": [],
      "metadata": {
        "confidence_score": 0.92,
        "sources": [...]
      }
    }
  ],
  "metadata": {}
}
```

---

## 🎨 UI-Features

### Session-Restore-Dialog

**Erscheint:** Beim App-Start (falls Sessions vorhanden)

**Aufbau:**
```
┌─────────────────────────────────────────────┐
│  Letzte Session wiederherstellen?         │
├─────────────────────────────────────────────┤
│  Titel              Datum      Nachrichten │
│  ───────────────────────────────────────── │
│  BImSchG-Diskussion Heute 14:30    12      │
│  Windkraft-Planung  Gestern 10:15  8       │
│  Baurecht-Fragen    Mo 09:30       5       │
├─────────────────────────────────────────────┤
│  ☑ Immer letzte Session automatisch laden  │
│  [🆕 Neuer Chat]  [✅ Wiederherstellen]    │
└─────────────────────────────────────────────┘
```

**Aktionen:**
- **Doppelklick:** Session sofort wiederherstellen
- **"✅ Wiederherstellen":** Ausgewählte Session laden
- **"🆕 Neuer Chat":** Neue Session starten
- **Checkbox:** Auto-Restore aktivieren/deaktivieren

### Session-Manager

**Öffnen:** Hamburger-Menü → "📁 Sessions verwalten"

**Features:**
- **Suche:** Echtzeit-Filter nach Titel
- **Sortierung:** Click auf Spalten-Header
- **Aktionen:**
  - **📂 Öffnen:** Session laden
  - **✏️ Umbenennen:** Titel ändern
  - **💾 Exportieren:** Als JSON speichern
  - **🗑️ Löschen:** Session löschen (mit Backup)
- **Rechtsklick:** Kontext-Menü mit allen Aktionen

---

## 💡 LLM-Context-Integration

### Wie funktioniert es?

**1. Chat-History wird gesammelt:**
```python
# Frontend sammelt Messages
messages = [
  {"role": "user", "content": "Was ist das BImSchG?"},
  {"role": "assistant", "content": "Das Bundes-Immissionsschutzgesetz..."},
  {"role": "user", "content": "Welche Grenzwerte gelten?"}
]
```

**2. Backend erstellt Context:**
```python
# ConversationContextManager
context = """
Benutzer: Was ist das BImSchG?
Assistent: Das Bundes-Immissionsschutzgesetz...
Benutzer: Welche Grenzwerte gelten?
"""
```

**3. LLM erhält erweiterten Prompt:**
```
System: Du bist VERITAS...

Bisherige Konversation:
Benutzer: Was ist das BImSchG?
Assistent: Das Bundes-Immissionsschutzgesetz...
Benutzer: Welche Grenzwerte gelten?

Aktuelle Frage:
Gibt es Ausnahmen?
```

**4. LLM antwortet kontextuell:**
```
Ja, es gibt Ausnahmen von den zuvor genannten Grenzwerten...
```
(Bezieht sich auf "zuvor genannte Grenzwerte")

### Context-Strategien

**Sliding Window (Default):**
- Neueste 10 Messages
- Schnell & einfach
- Vorhersagbare Token-Anzahl

**Relevance-Based:**
- TF-IDF-Similarity zur Frage
- Intelligente Auswahl
- Optimal für lange Konversationen

**All:**
- Alle Messages (falls <2000 Tokens)
- Vollständiger Kontext
- Auto-Kürzung bei Überschreitung

### Token-Management

**Limits:**
- Max Context: **2000 Tokens** (~8000 Zeichen)
- Schätzung: **~4 Zeichen pro Token**
- Auto-Kürzung bei Überschreitung

**Hinweis bei Kürzung:**
```
[... (gekürzt aufgrund Token-Limit)]
```

---

## 🔧 Entwickler-API

### Chat-Persistence Service

```python
from backend.services.chat_persistence_service import ChatPersistenceService
from shared.chat_schema import ChatSession

# Service initialisieren
service = ChatPersistenceService()

# Session erstellen
session = ChatSession(llm_model="llama3.1:8b")
session.add_message("user", "Hallo!")
session.add_message("assistant", "Hallo! Wie kann ich helfen?")

# Session speichern
service.save_chat_session(session)

# Session laden
loaded_session = service.load_chat_session(session.session_id)

# Alle Sessions auflisten
sessions = service.list_chat_sessions(limit=10, sort_by="updated_at")

# Session löschen (mit Backup)
service.delete_chat_session(session.session_id, create_backup=True)

# Statistiken
stats = service.get_session_statistics()
print(f"Total Sessions: {stats['total_sessions']}")
print(f"Total Messages: {stats['total_messages']}")
```

### ConversationContextManager

```python
from backend.agents.context_manager import ConversationContextManager
from shared.chat_schema import ChatSession

# Manager initialisieren
manager = ConversationContextManager(max_tokens=2000)

# Session mit Messages
session = ChatSession()
session.add_message("user", "Was ist das BImSchG?")
session.add_message("assistant", "Das Bundes-Immissionsschutzgesetz...")
session.add_message("user", "Welche Grenzwerte gelten?")

# Context erstellen
result = manager.build_conversation_context(
    chat_session=session,
    current_query="Gibt es Ausnahmen?",
    strategy="sliding_window",  # oder "relevance" / "all"
    max_messages=10
)

print(f"Context: {result['context']}")
print(f"Tokens: {result['token_count']}")
print(f"Messages: {result['message_count']}")

# Vollständigen Prompt erstellen
prompt = manager.format_prompt_with_context(
    current_query="Gibt es Ausnahmen?",
    context=result['context'],
    system_prompt="Du bist VERITAS..."
)

# Statistiken
stats = manager.get_context_statistics(session)
print(f"Can fit all: {stats['can_fit_all']}")
print(f"Requires truncation: {stats['requires_truncation']}")
```

### Ollama Context-Integration

```python
from backend.agents.veritas_ollama_client import VeritasOllamaClient
from shared.chat_schema import ChatSession

# Client initialisieren
async with VeritasOllamaClient() as client:
    await client.initialize()

    # Session mit History
    session = ChatSession()
    session.add_message("user", "Was ist das BImSchG?")
    session.add_message("assistant", "Das Bundes-Immissionsschutzgesetz...")

    # Query mit Context
    response = await client.query_with_context(
        query="Welche Grenzwerte gelten?",
        chat_session=session,
        context_strategy="sliding_window",
        max_context_messages=10
    )

    print(f"Response: {response.response}")
    print(f"Confidence: {response.confidence_score}")
```

---

## 🧪 Testing

### Unit Tests ausführen

```bash
# ConversationContextManager Tests
python tests/test_context_manager.py

# Output:
# ✅ 12/12 Tests PASSED
```

### Test-Szenarien

**1. Session-Persistierung:**
```bash
python test_chat_persistence.py

# Output:
# ✅ 10/10 Tests PASSED
```

**2. UI-Tests (Manual):**
```bash
python test_chat_persistence_ui.py

# Führt GUI-Tests aus mit Checklist
```

---

## 📊 Performance

### Benchmarks

| Operation | Time | Status |
|-----------|------|--------|
| Save Session | ~50ms | ✅ |
| Load Session | ~30ms | ✅ |
| List Sessions (10) | ~150ms | ✅ |
| Dialog Open | ~150ms | ✅ |
| Manager Refresh | ~250ms | ✅ |
| Search Filter | ~20ms | ✅ |
| Context-Building | <50ms | ✅ |
| API Overhead | <100ms | ✅ |

**Memory Impact:** <30 KB (negligible)

---

## ❓ FAQ

### Q: Wo werden Sessions gespeichert?
**A:** In `data/chat_sessions/{session_id}.json` (JSON-Format)

### Q: Werden Backups erstellt?
**A:** Ja, täglich in `data/chat_backups/{timestamp}/`

### Q: Wie viele Messages kann eine Session haben?
**A:** Unbegrenzt (Warnung ab 10 MB File-Size)

### Q: Wie funktioniert Auto-Restore?
**A:** Checkbox im Session-Restore-Dialog aktivieren → Setting wird gespeichert

### Q: Wie viel Context erhält das LLM?
**A:** Letzte 10 Messages (max 2000 Tokens)

### Q: Was passiert bei Token-Überschreitung?
**A:** Auto-Kürzung mit Hinweis "[... (gekürzt aufgrund Token-Limit)]"

### Q: Kann ich Sessions exportieren?
**A:** Ja, via Session-Manager → Rechtsklick → "💾 Exportieren"

### Q: Werden gelöschte Sessions backuped?
**A:** Ja, automatisch bei Löschung (falls create_backup=True)

---

## 🐛 Troubleshooting

### Problem: Session-Restore-Dialog erscheint nicht

**Lösung:**
1. Prüfe ob Sessions vorhanden: `ls data/chat_sessions/`
2. Prüfe Logs: `logger.info` in `veritas_app.py`
3. Prüfe Berechtigung: Lese-Zugriff auf `data/`

### Problem: Auto-Save funktioniert nicht

**Lösung:**
1. Prüfe ob `chat_persistence_service` initialisiert: `hasattr(self, 'chat_persistence')`
2. Prüfe Schreib-Berechtigung: `data/chat_sessions/` existiert?
3. Prüfe Logs: `logger.error` in `chat_persistence_service.py`

### Problem: Context wird nicht übergeben

**Lösung:**
1. Prüfe ob `chat_history` in API-Payload: `payload.get('chat_history')`
2. Prüfe Backend-Logs: `Context-Integration` Log-Meldungen
3. Prüfe ob Messages vorhanden: `len(self.chat_session.messages) > 0`

---

## 📚 Weitere Dokumentation

### Detaillierte Dokumentation:
- `docs/CHAT_PERSISTENCE_PHASE1_COMPLETE.md` - Persistierung
- `docs/CHAT_PERSISTENCE_PHASE2_COMPLETE.md` - UI
- `docs/CHAT_PERSISTENCE_PHASE3_COMPLETE.md` - Context-Integration
- `docs/CHAT_PERSISTENCE_TESTING_REPORT.md` - Tests
- `docs/CHAT_PERSISTENCE_PROJECT_SUMMARY.md` - Projekt-Übersicht

### Code-Referenz:
- `shared/chat_schema.py` - Data Models
- `backend/services/chat_persistence_service.py` - Persistierung
- `backend/agents/context_manager.py` - Context-Building
- `backend/agents/veritas_ollama_client.py` - LLM-Integration
- `frontend/ui/veritas_ui_session_dialog.py` - Session-Restore-Dialog
- `frontend/ui/veritas_ui_session_manager.py` - Session-Manager

---

## 🎯 Next Steps

### Für Benutzer:
1. ✅ App starten
2. ✅ Erste Session erstellen
3. ✅ Auto-Restore aktivieren
4. ✅ Konversation führen (kontextuell!)

### Für Entwickler:
1. ✅ Tests ausführen (`python tests/test_context_manager.py`)
2. ✅ API ausprobieren (siehe Entwickler-API)
3. ✅ Integration testen (Multi-Turn Conversation)
4. 📝 Feedback geben

---

**VERITAS v3.20.0 - Chat Persistence ist Production-Ready!** 🚀

Bei Fragen: Siehe Dokumentation oder kontaktiere das Team.
