# MANUELLE FRONTEND TEST-ANLEITUNG
# Conversation History Integration im echten Frontend testen

## Vorbereitung

1. **Backend sicherstellen**:
   ```powershell
   .\backend.bat status
   # Falls nicht läuft:
   .\backend.bat start
   ```

2. **Frontend starten**:
   ```powershell
   python start_frontend.py
   ```

## Test-Szenario

### Schritt 1: Erste Frage stellen

**Eingabe in Frontend**:
```
Wie funktioniert das Baugenehmigungsverfahren in München?
```

**Erwartung**:
- ✅ Streaming-Antwort wird angezeigt
- ✅ 4 Stage Reflections (falls aktiviert)
- ✅ Finale Antwort erscheint im Chat
- ❌ KEIN Gesprächskontext-Abschnitt (da erste Nachricht)

### Schritt 2: Follow-up Frage stellen

**Eingabe in Frontend**:
```
Welche Unterlagen benötige ich dafür?
```

**Erwartung**:
- ✅ Streaming-Antwort wird angezeigt
- ✅ 4 Stage Reflections (falls aktiviert)
- ✅ **Gesprächskontext** Abschnitt sollte erscheinen:

```markdown
**Antwort auf Ihre Frage**: Welche Unterlagen benötige ich dafür?

**Gesprächskontext**:
- Sie: Wie funktioniert das Baugenehmigungsverfahren in München?...
- Assistent: Das Baugenehmigungsverfahren in München umfasst...

**Zusammenfassung der Analyse**:
...
```

## Was zu prüfen ist

### ✅ Erfolgsfall

Die Antwort enthält:
1. ✅ `**Gesprächskontext**:` Überschrift
2. ✅ Mindestens 1 vorherige Nachricht von "Sie:"
3. ✅ Mindestens 1 vorherige Nachricht von "Assistent:"
4. ✅ Gesprächskontext erscheint VOR der Zusammenfassung

### ❌ Fehlerfall

Die Antwort:
- ❌ Enthält KEINEN `**Gesprächskontext**:` Abschnitt
- ❌ Beginnt direkt mit `**Zusammenfassung der Analyse**:`
- ❌ Keine Bezugnahme auf vorherige Nachrichten

## Debugging

Falls Gesprächskontext fehlt, prüfe:

### 1. Backend Logs
```powershell
# Prüfe ob conversation_history ankommt
Get-Job | Receive-Job -Keep | Select-String "conversation_history"

# Erwartete Logs:
# INFO:...📚 _synthesize_final_response: conversation_history = True
# INFO:...📚 conversation_history length = 2
# INFO:...✅ Conversation context created: 234 chars
```

### 2. Frontend Logs
```powershell
# Im Frontend-Fenster sollte erscheinen:
# INFO: 📚 Sende 2 Nachrichten als Kontext
```

### 3. Chat Messages Array
Im Frontend-Code prüfen ob `chat_messages` korrekt gefüllt ist:
- Nach erster Frage: `len(chat_messages) = 2` (user + assistant)
- Nach zweiter Frage: `len(chat_messages) = 4` (2x user + 2x assistant)

## Test-Checkliste

- [ ] Backend läuft auf Port 5000
- [ ] Frontend öffnet sich ohne Fehler
- [ ] Erste Frage: Antwort wird angezeigt
- [ ] Erste Frage: KEIN Gesprächskontext (korrekt)
- [ ] Zweite Frage: Antwort wird angezeigt
- [ ] **Zweite Frage: Gesprächskontext wird angezeigt** ← KRITISCH
- [ ] Kontext enthält vorherige User-Nachricht
- [ ] Kontext enthält vorherige Assistant-Nachricht
- [ ] Kontext erscheint an richtiger Stelle (nach "Antwort auf Ihre Frage")

## Erwartetes Format im Frontend

```markdown
**Antwort auf Ihre Frage**: Welche Unterlagen benötige ich dafür?

**Gesprächskontext**:
- Sie: Wie funktioniert das Baugenehmigungsverfahren in München?...
- Assistent: Das Baugenehmigungsverfahren in München umfasst mehrere Schritte: 1. Ba...

**Zusammenfassung der Analyse** (General, Standard):

🟢 **Geo Context**: Geografischer Kontext und lokale Bestimmungen identifiziert

🟡 **Document Retrieval**: Relevante Dokumente gefunden

...
```

## Weitere Test-Szenarien

### Test 3: Längere Konversation

1. Frage 1: "Was ist eine Baugenehmigung?"
2. Frage 2: "Wie lange dauert das?"  ← sollte Kontext zeigen
3. Frage 3: "Was kostet das?"  ← sollte letzte 3 Nachrichten zeigen
4. Frage 4: "Gibt es Ausnahmen?"  ← sollte letzte 3 Nachrichten zeigen

**Erwartung**: Ab Frage 2 immer Gesprächskontext, max. letzte 3 Nachrichten

### Test 4: Neue Session

1. Schließe Frontend
2. Starte Frontend neu
3. Stelle Frage

**Erwartung**: Kein Gesprächskontext (neue Session, leerer chat_messages)

## Wenn es nicht funktioniert

### Schnelltest im Python-Script

```python
import requests

conversation_history = [
    {"role": "user", "content": "Erste Frage"},
    {"role": "assistant", "content": "Erste Antwort"}
]

response = requests.post(
    "http://127.0.0.1:5000/v2/query/stream",
    json={
        "query": "Zweite Frage",
        "session_id": "test_manual",
        "enable_streaming": False,  # Synchron für einfacheren Test
        "conversation_history": conversation_history
    }
)

print(response.json())
# Prüfe ob "**Gesprächskontext**" im response_text enthalten ist
```

### Backend Neustart mit Logging

```powershell
# Stoppe Backend
.\scripts\stop_services.ps1

# Setze Log-Level auf DEBUG (optional)
$env:LOG_LEVEL="DEBUG"

# Starte Backend
.\scripts\start_services.ps1 -BackendOnly

# Prüfe Logs
Get-Job | Receive-Job -Keep
```

## Support

Falls der Test fehlschlägt, notiere:
1. Welcher Schritt ist fehlgeschlagen?
2. Was steht in den Backend-Logs?
3. Was steht in den Frontend-Logs?
4. Screenshot der Antwort im Frontend
5. Inhalt von `chat_messages` Array (über Logger)
