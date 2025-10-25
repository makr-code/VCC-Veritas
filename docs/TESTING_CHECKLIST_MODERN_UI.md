# 🧪 VERITAS Modern UI - Testing Checklist

**Datum:** 17. Oktober 2025, 21:56 Uhr  
**Version:** 3.16.0  
**Tester:** _________________  
**Status:** ⏳ In Bearbeitung

---

## ✅ System-Status

- ✅ **Backend:** Läuft auf `http://127.0.0.1:5000` (PID: 31488)
- ✅ **Frontend:** GUI geöffnet (Tkinter)
- ✅ **Health Check:** OK (Streaming, Pipeline, UDS3, Ollama verfügbar)

---

## 📋 Test-Kategorien

### 1. 🎨 User-Message Bubbles

**Ziel:** User-Nachrichten werden als rechts-ausgerichtete Bubbles dargestellt

| Test | Erwartung | Status | Notizen |
|------|-----------|--------|---------|
| Kurze Message (< 50 Zeichen) | Kompakte Bubble, rechts-ausgerichtet | ☐ | |
| Mittellange Message (50-200 Zeichen) | Bubble max 70% Breite | ☐ | |
| Lange Message (> 500 Zeichen) | Multi-line, Wordwrap funktioniert | ☐ | |
| Timestamp angezeigt | Timestamp unterhalb Bubble sichtbar | ☐ | |
| Bubble-Design | Abgerundete Ecken, heller Hintergrund | ☐ | |

**Testfall 1 - Kurze Message:**
```
Query: "Was ist VERITAS?"
```

**Testfall 2 - Lange Message:**
```
Query: "Erkläre mir ausführlich, wie das VERITAS-System funktioniert, welche Komponenten es hat und wie die Agenten zusammenarbeiten. Bitte mit allen technischen Details."
```

---

### 2. 📄 Assistant Full-Width Layout

**Ziel:** Assistant-Antworten nutzen volle Breite, professionelles Markdown-Rendering

| Test | Erwartung | Status | Notizen |
|------|-----------|--------|---------|
| Vollbreite-Rendering | Text nutzt komplette Breite | ☐ | |
| Markdown-Formatierung | **Bold**, *Italic*, `Code` funktioniert | ☐ | |
| Code-Blöcke | Syntax-Highlighting, Copy-Button | ☐ | |
| Listen | Bullet-Points, nummerierte Listen korrekt | ☐ | |
| Überschriften | H1, H2, H3 unterscheidbar | ☐ | |

**Testfall 3 - Markdown-Test:**
```
Query: "Zeige mir ein Python-Code-Beispiel mit Kommentaren und erkläre es mit Listen."
```

---

### 3. 🔬 IEEE-Citations (Inline)

**Ziel:** Inline-Zitate als klickbare [1], [2], [3] im Text

| Test | Erwartung | Status | Notizen |
|------|-----------|--------|---------|
| Citation-Marker erscheinen | [1], [2], [3] im Text sichtbar | ☐ | Backend muss {cite:src_1} liefern! |
| Nummerierung korrekt | Aufsteigende Zahlen, eindeutig | ☐ | |
| Klickbar | Click → Scroll zu Quellenverzeichnis | ☐ | |
| Hover-Tooltip | Tooltip zeigt Source-Details | ☐ | |
| Mehrfach-Citations | {cite:src_1} mehrmals → [1] mehrmals | ☐ | |

**⚠️ Backend-Requirement:**
Backend muss in Response `{cite:source_id}` Marker liefern:
```json
{
  "content": "Text mit Citation {cite:src_1} und {cite:src_2}.",
  "metadata": {
    "sources_metadata": [
      {
        "id": "src_1",
        "file": "document.pdf",
        "page": 42,
        "author": "J. Smith",
        "title": "Document Title",
        "year": 2020
      }
    ]
  }
}
```

**Testfall 4 - Citations:**
```
Query: "Nenne Quellen für Informationen über KI-Systeme"
```

---

### 4. 📚 IEEE-Quellenverzeichnis

**Ziel:** Formatiertes Quellenverzeichnis nach IEEE-Standard in Metadaten

| Test | Erwartung | Status | Notizen |
|------|-----------|--------|---------|
| Quellenverzeichnis sichtbar | In expandiertem Metadata-Wrapper | ☐ | |
| IEEE-Formatierung korrekt | [1] Autor, "Titel", Jahr, pp. Seiten | ☐ | |
| PDF-Sources | Format: [1] J. Smith, "Title", 2020, pp. 42 | ☐ | |
| Web-Sources | Format: [2] "Article Title", URL, Accessed: ... | ☐ | |
| DB-Sources | Format: [3] "DB Entry", Database: ..., ID: ... | ☐ | |
| Book-Sources | Format: [4] J. Doe, Book Title, Publisher, 2021 | ☐ | |

**Testfall 5 - Quellenverzeichnis:**
```
Query: "Suche Informationen aus verschiedenen Quellen"
→ Metadata expandieren
→ Quellenverzeichnis prüfen
```

---

### 5. 📦 Kompakte Metadaten-Wrapper

**Ziel:** Metadaten collapsed by default, expandierbar per Click

| Test | Erwartung | Status | Notizen |
|------|-----------|--------|---------|
| Initial collapsed | Zeigt 1-Zeilen-Summary mit "▶" | ☐ | |
| Expand funktioniert | Click → Zeigt alle Details mit "▼" | ☐ | |
| Collapse funktioniert | Click → Zurück zu 1-Zeilen-Summary | ☐ | |
| Complexity angezeigt | "Complexity: Medium" sichtbar | ☐ | |
| Duration angezeigt | "Duration: 1.5s" sichtbar | ☐ | |
| Model angezeigt | "Model: llama3.2" sichtbar | ☐ | |
| Sources-Count | "3 Sources" (collapsed), Liste (expanded) | ☐ | |

**Testfall 6 - Metadata Toggle:**
```
1. Query senden
2. Auf "▶ Metadata (Complexity: ..., 3 Sources)" klicken
3. Expandiert → Details prüfen
4. Auf "▼ Metadata" klicken
5. Collapsed → Summary prüfen
```

---

### 6. 👍👎 Feedback-Integration

**Ziel:** Feedback-Buttons in Metadaten-Zeile, kompakt und klickbar

| Test | Erwartung | Status | Notizen |
|------|-----------|--------|---------|
| Buttons sichtbar | 👍👎 rechts in Metadaten-Zeile | ☐ | |
| Hover-Effekt | Buttons ändern Farbe bei Hover | ☐ | |
| Thumbs-Up klickbar | Click → Feedback "positive" gesendet | ☐ | |
| Thumbs-Down klickbar | Click → Feedback "negative" gesendet | ☐ | |
| Visual Feedback | Button-Farbe ändert sich nach Click | ☐ | |
| Backend-Call | Console: "Feedback positive/negative sent" | ☐ | |

**Testfall 7 - Feedback:**
```
1. Query senden
2. Auf 👍 klicken → Prüfe Console-Log
3. Neue Query senden
4. Auf 👎 klicken → Prüfe Console-Log
```

---

### 7. 🎯 Smooth Scrolling & Performance

**Ziel:** Flüssiges Scrolling, keine Lags, optimierte Performance

| Test | Erwartung | Status | Notizen |
|------|-----------|--------|---------|
| Smooth Scrolling | Mousewheel → Smooth 1-line Scroll | ☐ | |
| Auto-Scroll bei neuer Message | Scrollt automatisch nach unten | ☐ | |
| Kein Auto-Scroll beim Lesen | Wenn hochgescrollt → bleibt Position | ☐ | |
| Performance 10 Messages | Chat mit 10 Messages lädt schnell | ☐ | |
| Performance 50 Messages | Chat mit 50 Messages keine Lags | ☐ | |
| Performance 100+ Messages | Chat mit 100+ Messages stabil | ☐ | |

**Testfall 8 - Performance:**
```
1. Sende 10 Queries nacheinander
2. Prüfe: Rendering-Geschwindigkeit
3. Scroll hoch und runter → Smooth?
4. Sende weitere 40 Queries (→ 50 total)
5. Prüfe: Immer noch responsive?
```

---

### 8. ⌨️ Keyboard Shortcuts

**Ziel:** Keyboard Shortcuts funktionieren

| Test | Erwartung | Status | Notizen |
|------|-----------|--------|---------|
| Strg+Enter | Sendet Message | ☐ | |
| Esc | Löscht Input-Feld | ☐ | |
| Strg+C (in Text-Widget) | Kopiert markierten Text | ☐ | |
| Strg+A (in Input) | Markiert gesamten Input | ☐ | |

**Testfall 9 - Keyboard:**
```
1. Tippe Query
2. Drücke Strg+Enter → Sendet?
3. Tippe neue Query
4. Drücke Esc → Input gelöscht?
```

---

### 9. 🔍 Edge-Cases

**Ziel:** System verhält sich auch bei ungewöhnlichen Inputs korrekt

| Test | Erwartung | Status | Notizen |
|------|-----------|--------|---------|
| Sehr lange User-Message (>1000 Zeichen) | Bubble mit Wordwrap, keine Overflow | ☐ | |
| Sehr lange Assistant-Response (>10.000 Zeichen) | Rendering performant, kein Freeze | ☐ | |
| Response ohne Metadaten | Funktioniert ohne Crash | ☐ | |
| Response ohne Sources | Keine Sources, aber Metadata angezeigt | ☐ | |
| Unbekannte Citation {cite:unknown} | Zeigt [?] oder ignoriert | ☐ | |
| 20+ Sources | Quellenverzeichnis scrollbar | ☐ | |
| Window Resize | Layout bricht nicht | ☐ | |
| Backend offline | Fehlermeldung, kein Crash | ☐ | |

**Testfall 10 - Extreme Message:**
```
Query: [1000+ Zeichen langer Text]
→ Prüfe Bubble-Rendering
```

**Testfall 11 - Backend Disconnect:**
```
1. Backend stoppen: .\scripts\stop_services.ps1 -BackendOnly
2. Query senden
3. Prüfe: Fehlermeldung erscheint?
4. Backend neu starten: .\scripts\start_services.ps1 -BackendOnly
```

---

### 10. 🔄 Legacy-Fallback

**Ziel:** Bei Fehler fällt System auf Legacy-Darstellung zurück

| Test | Erwartung | Status | Notizen |
|------|-----------|--------|---------|
| CHAT_BUBBLES_AVAILABLE = False | Legacy-Rendering wird verwendet | ☐ | Manuell testen |
| enable_modern_ui = False | Legacy-Rendering wird verwendet | ☐ | Manuell testen |
| Exception in modern render | Automatischer Fallback auf Legacy | ☐ | |
| Legacy-Darstellung funktional | Alle Features weiterhin nutzbar | ☐ | |

**Testfall 12 - Fallback:**
```python
# In veritas_ui_chat_formatter.py temporär ändern:
CHAT_BUBBLES_AVAILABLE = False

# Oder:
enable_modern_ui = False

→ App neu starten
→ Prüfe: Legacy-Darstellung erscheint?
```

---

## 📊 Test-Ergebnisse Summary

### Gesamtstatus

| Kategorie | Tests | Bestanden | Fehlgeschlagen | Übersprungen |
|-----------|-------|-----------|----------------|--------------|
| User-Message Bubbles | 5 | ☐ | ☐ | ☐ |
| Assistant Full-Width | 5 | ☐ | ☐ | ☐ |
| IEEE-Citations | 5 | ☐ | ☐ | ☐ |
| IEEE-Quellenverzeichnis | 6 | ☐ | ☐ | ☐ |
| Metadaten-Wrapper | 7 | ☐ | ☐ | ☐ |
| Feedback-Integration | 6 | ☐ | ☐ | ☐ |
| Smooth Scrolling | 6 | ☐ | ☐ | ☐ |
| Keyboard Shortcuts | 4 | ☐ | ☐ | ☐ |
| Edge-Cases | 8 | ☐ | ☐ | ☐ |
| Legacy-Fallback | 4 | ☐ | ☐ | ☐ |
| **TOTAL** | **56** | **☐** | **☐** | **☐** |

---

## 🐛 Gefundene Bugs

### Bug #1
- **Kategorie:** _____________________
- **Beschreibung:** _____________________
- **Reproduktion:** _____________________
- **Schweregrad:** ☐ Critical ☐ High ☐ Medium ☐ Low
- **Status:** ☐ Open ☐ In Progress ☐ Fixed

### Bug #2
- **Kategorie:** _____________________
- **Beschreibung:** _____________________
- **Reproduktion:** _____________________
- **Schweregrad:** ☐ Critical ☐ High ☐ Medium ☐ Low
- **Status:** ☐ Open ☐ In Progress ☐ Fixed

*(Weitere Bugs auf separatem Blatt)*

---

## 💡 Verbesserungsvorschläge

1. _____________________________________________________
2. _____________________________________________________
3. _____________________________________________________
4. _____________________________________________________
5. _____________________________________________________

---

## ✅ Abnahme

- [ ] Alle Critical/High-Bugs gefixt
- [ ] Mindestens 90% Tests bestanden
- [ ] Performance akzeptabel (< 2s für 50 Messages)
- [ ] Keine Crashes/Freezes beobachtet
- [ ] UX-Feedback positiv

**Tester Unterschrift:** _____________________  
**Datum:** _____________________

**Lead Developer Freigabe:** _____________________  
**Datum:** _____________________

---

## 📋 Quick-Start für Testing

### 1. Services starten
```powershell
cd c:\VCC\veritas
.\scripts\start_services.ps1
```

### 2. Test-Queries (Beispiele)

**Basis-Test:**
```
Was ist VERITAS?
```

**Markdown-Test:**
```
Zeige mir ein Python-Code-Beispiel mit Listen und Erklärungen
```

**Performance-Test:**
```
# 50x die gleiche Query senden:
Erkläre kurz: Was ist KI?
```

**Edge-Case-Test:**
```
[1000+ Zeichen Text mit vielen Sonderzeichen @#$%^&*()...]
```

### 3. Logs prüfen
```powershell
# Backend-Logs
Get-Content C:\VCC\veritas\logs\backend_uvicorn.log -Tail 20 -Wait

# Frontend-Logs (in GUI Console)
# Oder: Get-Job | Receive-Job -Keep
```

### 4. Services stoppen
```powershell
.\scripts\stop_services.ps1
```

---

**Happy Testing! 🚀**
