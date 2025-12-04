# VERITAS v3.19.0 - Quick Start Guide 🚀

**Status:** ✅ PRODUCTION READY
**Last Updated:** 11. Oktober 2025

---

## 🎯 Schnellstart (2 Minuten)

### 1. Backend starten
```powershell
cd C:\VCC\veritas
python start_backend.py
```

**Erwartete Ausgabe:**
```
⚙️ Starte VERITAS Backend API...
🌐 API wird verfügbar unter: http://localhost:5000
INFO: Uvicorn running on http://0.0.0.0:5000
```

### 2. Frontend starten (neues Terminal)
```powershell
cd C:\VCC\veritas
python start_frontend.py
```

**Erwartete Ausgabe:**
```
🚀 Starte VERITAS Frontend...
[Tkinter GUI öffnet sich]
```

### 3. Erste Query testen
1. Im GUI-Fenster: Text eingeben
2. Beispiel: **"Was ist das BImSchG?"**
3. Button "Senden" klicken
4. Warten (5-10 Sekunden)
5. Antwort erscheint mit:
   - 📝 Strukturierte Antwort
   - 📊 Quellen (aus Neo4j: 1930 Dokumente)
   - ⏱️ Antwortzeit & Metriken
   - 👍👎💬 Feedback-Buttons

---

## 🔧 System-Status prüfen

### Health Check (Backend)
```powershell
curl http://localhost:5000/api/feedback/health
```

**Erwartete Antwort:**
```json
{
  "status": "healthy",
  "database": "connected",
  "today_feedback": 0
}
```

### API Endpoints (14 verfügbar)
```powershell
curl http://localhost:5000/
```

**Wichtigste Endpoints:**
- `/v2/query` - Chat Query (Standard)
- `/v2/query/stream` - Streaming Chat
- `/uds3/query` - UDS3 Hybrid Search
- `/api/feedback/submit` - Feedback senden
- `/api/feedback/stats` - Statistiken

---

## 📊 Features im GUI

### Chat-Interface
- ✅ **Sprechblasen-Design** - User (rechts) vs Assistant (links)
- ✅ **Strukturierte Antworten** - 6 Sections (Antwort, Details, Quellen, etc.)
- ✅ **Metriken-Badges** - Confidence, Duration, Sources

### LLM Parameter Controls
- ✅ **4 Presets** - Präzise, Standard, Ausführlich, Kreativ
- ✅ **Token Counter** - Echtzeit-Längen-Schätzung (💬/📝/⚠️)
- ✅ **Antwortzeit-Prädiktion** - Modell-basierte Schätzung (⚡/⏱️/🐌)
- ✅ **Parameter-Tuning** - Temperature (0.1-1.0), Tokens (100-2000), Top-p (0.1-1.0)

### Feedback System
- ✅ **3-Button Widget** - 👍 Hilfreich, 👎 Nicht hilfreich, 💬 Kommentar
- ✅ **Backend-Integration** - SQLite-Persistierung
- ✅ **Analytics** - Positive Ratio, Average Rating, Top Categories

### Export-Funktionen
- ✅ **Word-Export (.docx)** - Formatierte Chat-Historie mit Quellen
- ✅ **Excel-Export (.xlsx)** - 3 Sheets (Messages, Statistiken, Quellen)
- ✅ **Export-Dialog** - Zeitraum-Filter, Optionen (Metadata, Sources)

### File Upload
- ✅ **Drag & Drop** - 32 Dateiformate (PDF, DOCX, TXT, etc.)
- ✅ **SHA256 Deduplication** - Automatische Duplikat-Erkennung
- ✅ **Size Validation** - Max 50 MB pro Datei

---

## 🎓 Beispiel-Workflows

### Workflow 1: Einfache Frage
1. GUI öffnen
2. Eingabe: **"Welche Grenzwerte gelten für Lärm?"**
3. Senden
4. Antwort lesen
5. Feedback geben (👍)

### Workflow 2: Dokument hochladen + Fragen
1. PDF per Drag & Drop in Chat ziehen
2. Warten (Upload läuft)
3. Frage: **"Was steht in diesem Dokument über Emissionen?"**
4. Senden
5. Antwort mit Quellen aus neuem Dokument

### Workflow 3: Export erstellen
1. Mehrere Fragen stellen (3-5 Queries)
2. Menü: **File → Export**
3. Format wählen: **DOCX** oder **XLSX**
4. Zeitraum: **All** oder **Last 7 days**
5. Optionen: **✓ Include Metadata**, **✓ Include Sources**
6. Export starten
7. Datei öffnen (Word/Excel)

### Workflow 4: LLM Parameter anpassen
1. Komplexe Frage vorbereiten
2. Preset wählen: **"Ausführlich"** (Temp=0.6, Tokens=1000)
3. Token Counter prüfen: **~750 Wörter** (📝 Mittel)
4. Antwortzeit-Schätzung: **~8-12s** (⏱️ Mittel)
5. Senden
6. Lange, detaillierte Antwort erhalten

---

## 🔍 Debug & Troubleshooting

### Backend läuft nicht?
```powershell
# Prozesse prüfen
netstat -ano | findstr ":5000"

# Port belegt? Prozess beenden
taskkill /PID <PID> /F

# Backend neu starten
python start_backend.py
```

### Frontend zeigt keine Antworten?
1. **Backend läuft?** → Health Check durchführen
2. **Ollama läuft?** → `ollama list` in Terminal
3. **Neo4j aktiv?** → Logs prüfen
4. **Firewall blockiert?** → Port 5000 freigeben

### Lange Antwortzeiten (>20s)?
- **Neo4j Indexierung** → Erste Query dauert länger (Cold Start)
- **LLM warmup** → Erste Ollama-Anfrage dauert 10-15s
- **Netzwerk-Latenz** → UDS3-Backends auf Remote-Server (192.168.178.94)

### Keine Quellen in Antwort?
- **Neo4j leer?** → `scripts/check_uds3_status.py` ausführen
- **Graph Search disabled?** → Logs prüfen (warnings)
- **Query zu spezifisch?** → Breitere Suchbegriffe verwenden

---

## 📁 Verzeichnis-Struktur

```
C:\VCC\veritas\
├── backend/
│   ├── api/
│   │   ├── veritas_api_backend.py      # Main Backend (Port 5000)
│   │   └── feedback_routes.py          # Feedback API (4 Endpoints)
│   ├── agents/
│   │   └── veritas_uds3_hybrid_agent.py # UDS3 Agent (299 LOC)
│   └── services/
├── frontend/
│   ├── veritas_app.py                  # Main GUI (Tkinter)
│   ├── ui/
│   │   ├── veritas_ui_chat_formatter.py # Chat Design v2.0
│   │   ├── veritas_ui_export_dialog.py  # Export Dialog
│   │   └── veritas_ui_drag_drop.py      # Drag & Drop Handler
│   └── services/
│       ├── office_export.py             # Word/Excel Export
│       └── feedback_api_client.py       # Feedback API Client
├── docs/
│   ├── PRODUCTION_DEPLOYMENT_COMPLETE.md # Deployment Report
│   ├── UDS3_SEARCH_API_PRODUCTION_GUIDE.md # UDS3 Guide
│   └── TESTING.md                       # Test Guide
├── scripts/
│   ├── check_uds3_status.py            # Backend Status Check
│   └── test_uds3_search_api_integration.py # Integration Tests
├── start_backend.py                     # Backend Launcher
├── start_frontend.py                    # Frontend Launcher
└── QUICK_START.md                       # This file
```

---

## 🎯 Nächste Schritte

### Sofort (Production Use)
- ✅ Backend läuft auf Port 5000
- ✅ Frontend läuft (Tkinter GUI)
- ✅ Alle Features aktiv
- ✅ Bereit für echte Queries!

### Optional (Performance)
- [ ] **ChromaDB Fix** (2-4h) - Remote API Issue beheben
- [ ] **PostgreSQL API** (2-3h) - execute_sql() hinzufügen
- [ ] **Caching** (1-2h) - Query-Enrichment cachen
- [ ] **A/B Testing** (2-3h) - llama3 vs llama3.1

### Optional (Features)
- [ ] **SupervisorAgent** (3-4h) - Zentraler UDS3 Zugriff
- [ ] **File Watcher** (4-6h) - Auto-Indexing
- [ ] **Batch CLI** (6-8h) - Automation Tool

---

## 📞 Support

**Dokumentation:**
- Deployment: `docs/PRODUCTION_DEPLOYMENT_COMPLETE.md`
- UDS3 Guide: `docs/UDS3_SEARCH_API_PRODUCTION_GUIDE.md`
- Testing: `docs/TESTING.md`
- Feedback: `docs/FEEDBACK_SYSTEM.md`
- Export: `docs/OFFICE_EXPORT.md`

**Logs:**
- Backend: Terminal mit `python start_backend.py`
- Frontend: Terminal mit `python start_frontend.py`
- UDS3: `data/veritas_auto_server.log`

**Status Check:**
```powershell
# Backend Health
curl http://localhost:5000/api/feedback/health

# UDS3 Backends
python scripts/check_uds3_status.py

# Ollama Models
ollama list
```

---

## 🎉 Erfolg!

**VERITAS v3.19.0 läuft jetzt!** 🚀

Du hast erfolgreich deployed:
- ✅ Backend (14 API Endpoints)
- ✅ Frontend (8 Major Features)
- ✅ UDS3 Integration (Neo4j: 1930 Dokumente)
- ✅ Feedback System (SQLite + Analytics)
- ✅ Export (Word/Excel)
- ✅ Drag & Drop (32 Formate)

**Viel Erfolg bei der Nutzung!** 🎯

---

**Version:** v3.19.0
**Status:** ✅ PRODUCTION READY
**Date:** 11. Oktober 2025
