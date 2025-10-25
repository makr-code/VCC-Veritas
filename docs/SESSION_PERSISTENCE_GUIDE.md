# VERITAS Session Persistence Guide

## 📋 Übersicht

Die Session Persistence-Funktion ermöglicht das Speichern und Laden kompletter Chat-Sessions in JSON-Format. Dies erlaubt es, Konversationen zwischen verschiedenen Sitzungen zu bewahren und später fortzusetzen.

## 🎯 Features

### 1. **Manuelles Speichern** (Ctrl+S oder 💾 Button)
- Öffnet Datei-Dialog zur Auswahl des Speicherorts
- Speichert als `.json`-Datei
- Enthält:
  - Session-Metadaten (ID, Zeitstempel, Modell)
  - Alle Chat-Messages (User + Assistant)
  - LLM-Einstellungen (Temperature, Max Tokens, Top-p)

### 2. **Manuelles Laden** (Ctrl+O oder 📂 Button)
- Öffnet Datei-Dialog zur Auswahl der Session-Datei
- Zeigt Bestätigungs-Dialog mit Session-Infos
- Lädt Messages und Einstellungen
- Aktualisiert Chat-Display automatisch

### 3. **Auto-Save beim Schließen**
- Automatisches Speichern beim Fenster-Schließen
- Speichert in `data/sessions/` Verzeichnis
- Dateiname: `auto_save_{window_id}_{timestamp}.json`
- Behält nur die letzten 5 Auto-Saves pro Fenster

## 🎹 Keyboard Shortcuts

| Shortcut | Aktion | Beschreibung |
|----------|--------|--------------|
| `Ctrl+S` | Session speichern | Öffnet Speichern-Dialog |
| `Ctrl+O` | Session laden | Öffnet Laden-Dialog |

## 📁 Session-Datei Format

```json
{
  "metadata": {
    "session_id": "session_20251018_143025_main",
    "window_id": "main",
    "created_at": "2025-10-18T14:30:25.123456",
    "message_count": 12,
    "llm_model": "llama3.1:8b",
    "settings": {
      "temperature": 0.7,
      "max_tokens": 1500,
      "top_p": 0.9
    }
  },
  "messages": [
    {
      "role": "user",
      "content": "Was ist VERITAS?",
      "timestamp": "2025-10-18T14:30:30.123456"
    },
    {
      "role": "assistant",
      "content": "VERITAS ist ein RAG-basiertes System...",
      "timestamp": "2025-10-18T14:30:35.789012",
      "metadata": {
        "sources": [...],
        "confidence": 0.95
      }
    }
  ],
  "version": "1.0"
}
```

## 🔧 Verwendung im Code

### Session Speichern

```python
# Manuell mit Dialog
window.save_session()

# Mit spezifischem Pfad
window.save_session(filepath="c:/path/to/session.json")
```

### Session Laden

```python
# Manuell mit Dialog
window.load_session()

# Mit spezifischem Pfad
window.load_session(filepath="c:/path/to/session.json")
```

### Auto-Save

```python
# Automatisches Speichern in data/sessions/
window.auto_save_session()
```

## 📂 Speicherorte

### Manuelle Saves
- Beliebiger Speicherort (User-Auswahl)
- Standard-Dateiname: `veritas_session_YYYYMMDD_HHMMSS.json`

### Auto-Saves
- Verzeichnis: `data/sessions/`
- Dateiname: `auto_save_{window_id}_{timestamp}.json`
- Retention: Letzte 5 Dateien pro Fenster

## 🎨 UI-Integration

### Toolbar-Buttons
- **💾 Speichern** - Links in der Toolbar
- **📂 Laden** - Neben Speichern-Button
- Visual Separator zwischen Session- und Chat-Controls

### Status-Feedback
- ✅ **"💾 Session gespeichert!"** nach erfolgreichem Speichern
- ✅ **"📂 Session geladen: X Messages"** nach erfolgreichem Laden
- ❌ **"❌ Session-Speichern fehlgeschlagen"** bei Fehler

### Bestätigungs-Dialog beim Laden
```
Session laden?

📅 Erstellt: 2025-10-18T14:30:25
💬 Nachrichten: 12
🤖 Modell: llama3.1:8b

⚠️ Aktuelle Chat-History wird ersetzt!

[Ja] [Nein]
```

## ⚙️ Technische Details

### Session-Metadaten
- `session_id`: Eindeutige Session-Identifikation
- `window_id`: Fenster-Identifikation (main/child)
- `created_at`: ISO-Format Timestamp
- `message_count`: Anzahl gespeicherter Messages
- `llm_model`: Verwendetes LLM-Modell
- `settings`: LLM-Parameter (temp, tokens, top-p)

### Message-Format
- `role`: "user" oder "assistant"
- `content`: Nachrichteninhalt
- `timestamp`: ISO-Format Timestamp
- `metadata`: Optional (sources, confidence, etc.)

### Error Handling
- Try-Catch-Blöcke für alle File-Operations
- User-friendly Error-Messages
- Logging aller Aktionen

## 🔄 Workflow-Beispiel

### Typischer Workflow

1. **User startet neue Session**
   - Stellt mehrere Fragen
   - Erhält Antworten mit RAG-Quellen

2. **User speichert Session** (Ctrl+S)
   - Wählt Speicherort
   - Datei wird als JSON gespeichert

3. **User schließt VERITAS**
   - Auto-Save wird ausgeführt
   - Letzte 5 Auto-Saves bleiben erhalten

4. **User startet VERITAS neu**
   - Lädt Session (Ctrl+O)
   - Chat-History wird wiederhergestellt
   - Settings werden übernommen

5. **User setzt Konversation fort**
   - Neue Messages werden hinzugefügt
   - Kontext bleibt erhalten

## 🚀 Best Practices

### Für User
1. Speichere wichtige Sessions manuell (Ctrl+S)
2. Nutze aussagekräftige Dateinamen
3. Organisiere Sessions in Ordnern (z.B. nach Thema)
4. Auto-Saves dienen als Backup, nicht als primärer Speicher

### Für Entwickler
1. Validiere JSON-Format beim Laden
2. Handle File-Not-Found und Permissions-Errors
3. Biete User-Feedback bei allen Aktionen
4. Cleanup alte Auto-Saves regelmäßig

## 🐛 Troubleshooting

### Session kann nicht geladen werden
- **Problem**: Ungültiges JSON-Format
- **Lösung**: Überprüfe Datei-Integrität, verwende JSON-Validator

### Auto-Save funktioniert nicht
- **Problem**: Keine Schreibrechte in `data/sessions/`
- **Lösung**: Überprüfe Verzeichnis-Permissions

### Settings werden nicht wiederhergestellt
- **Problem**: Alte Session-Version ohne Settings
- **Lösung**: Nur Messages werden geladen, Settings bleiben Standard

## 📊 Statistiken

### Storage
- ~1-5 KB pro Message (durchschnittlich)
- ~10-50 KB pro Session (10-50 Messages)
- Auto-Save-Limit: 5 × Session-Size pro Fenster

### Performance
- Speichern: <100ms (typisch)
- Laden: <200ms (typisch)
- Kein Performance-Impact im normalen Betrieb

## 🔮 Geplante Erweiterungen

- [ ] Session-Tags und Kategorien
- [ ] Session-Suche und Filterung
- [ ] Cloud-Sync für Sessions
- [ ] Session-Merge-Funktion
- [ ] Export zu anderen Formaten (Markdown, PDF)

## 📚 Siehe auch

- [TODO_CHAT_UI_UX.md](TODO_CHAT_UI_UX.md) - Vollständige Feature-Liste
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Projekt-Architektur
- [VERITAS_API_BACKEND_DOCUMENTATION.md](VERITAS_API_BACKEND_DOCUMENTATION.md) - Backend-API

---

**Version**: 1.0  
**Datum**: 18. Oktober 2025  
**Status**: ✅ Implementiert und Getestet
