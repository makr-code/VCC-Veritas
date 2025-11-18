# VERITAS Office Integration - Quick Reference

**Version:** 1.0.0 | **Date:** 1. November 2025

---

## 📦 Was wurde implementiert?

### Office Add-ins (6 Stück)
- ✅ **Word** - Text an Cursor-Position
- ✅ **Excel** - Daten als Zeilen in Tabelle
- ✅ **PowerPoint** - TextBox auf Folie
- ✅ **Outlook** - Text in E-Mail-Body (NEW!)
- ✅ **OneNote** - Outline auf Seite (NEW!)
- ✅ **Access** - Zwischenablage-Fallback (NEW!)

### Desktop Integration
- ✅ **VS Code Extension** - MCP Client mit Commands + Sidebar (NEW!)

### Backend RAG
- ✅ **Office Ingestion API** - Upload von .docx/.xlsx/.pptx (STUB)
- ✅ **Office Parsers** - Text-Extraktion (STUB - TODO: echte Parser)

---

## 🚀 Quick Start

### 1. Backend starten
```powershell
cd c:\VCC\veritas
python backend/app.py
```

**Verfügbare Endpoints:**
- `http://localhost:5000/api/mcp/prompts` (MCP HTTP Bridge)
- `http://localhost:5000/api/office/upload` (Office Ingestion)
- `http://localhost:5000/docs` (FastAPI Swagger)

### 2. Office Add-in sideloaden

**Windows:**
```powershell
# Shared Folder erstellen
New-Item -Path "$env:LOCALAPPDATA\Microsoft\Office\16.0\Wef\" -ItemType Directory -Force

# Manifest kopieren (Beispiel: Word)
Copy-Item "desktop\word-addin\manifest.local.xml" "$env:LOCALAPPDATA\Microsoft\Office\16.0\Wef\"
```

**In Office App:**
- Word/Excel/PowerPoint/Outlook öffnen
- Start → My Add-ins → Shared Folder → VERITAS Adapter auswählen
- Taskpane öffnet sich rechts

### 3. VS Code Extension installieren

```bash
cd desktop/vscode-extension
npm install
code .
# F5 drücken → Extension Host startet
```

**Commands (Ctrl+Shift+P):**
- `VERITAS: Hybrid-Suche ausführen` (Shortcut: Ctrl+Shift+V S)
- `VERITAS: Prompt rendern`
- `VERITAS: Dokument abrufen`
- `VERITAS: Suchpanel öffnen` (Shortcut: Ctrl+Shift+V P)

---

## 📂 Dateistruktur

```
desktop/
├─ word-addin/          ✅ Existing (Phase 1-5)
├─ excel-addin/         ✅ NEW (manifest, HTML, JS, README)
├─ powerpoint-addin/    ✅ NEW (manifest, HTML, JS, README)
├─ outlook-addin/       ✅ NEW (manifest, HTML, JS)
├─ onenote-addin/       ✅ NEW (manifest, HTML, JS)
├─ access-addin/        ✅ NEW (manifest, HTML, JS)
├─ vscode-extension/    ✅ NEW (package.json, extension.js)
├─ office_installer.py  ✅ Existing
├─ office_packager.py   ✅ Existing (TODO: Multi-App Dropdown)
└─ build_package.ps1    ✅ Existing (TODO: -AppType Parameter)

backend/
├─ api/
│  ├─ mcp_http_endpoints.py    ✅ Existing
│  └─ office_ingestion.py      ✅ NEW (500+ lines, 6 endpoints)
├─ services/
│  └─ office_parsers.py        ✅ NEW (400+ lines, STUB)
└─ app.py                      ✅ Modified (Router Integration)
```

---

## 🔧 Office Ingestion API

### Upload Single File
```bash
curl -X POST http://localhost:5000/api/office/upload \
  -F "file=@document.docx"
```

### Batch Upload
```bash
curl -X POST http://localhost:5000/api/office/upload/batch \
  -F "files=@doc1.docx" \
  -F "files=@sheet1.xlsx" \
  -F "files=@pres1.pptx"
```

### Job Status
```bash
curl http://localhost:5000/api/office/jobs/{job_id}
```

### Statistics
```bash
curl http://localhost:5000/api/office/stats
```

**Status:** STUB - Parser-Integration pending!

---

## 📝 Parser Integration (TODO)

### Installation
```bash
pip install python-docx openpyxl python-pptx
```

### Code-Änderungen

**1. Parser aktivieren:**
```python
# backend/services/office_parsers.py
# Entferne STUB-Kommentare
# Implementiere TODO-Kommentare (siehe inline Code-Beispiele)
```

**2. RAG Integration:**
```python
# backend/api/office_ingestion.py (Lines 80-90)
from backend.services.office_parsers import parse_office_document
parsed_data = parse_office_document(content, file_type)

from backend.services.rag_indexer import index_document
index_document(parsed_data)
```

**Dateien mit TODO-Kommentaren:**
- `backend/services/office_parsers.py` (3 Funktionen, ~100 lines TODO)
- `backend/api/office_ingestion.py` (2 Stellen, ~10 lines TODO)

---

## 🎯 App-spezifische Insert-Funktionen

| App | API | Insert-Methode | Besonderheit |
|-----|-----|----------------|--------------|
| **Word** | `Word.run()` | `insertText()` | Selection Replace |
| **Excel** | `Excel.run()` | `values = data` | Next Free Row |
| **PowerPoint** | `PowerPoint.run()` | `addTextBox()` | Shape Creation |
| **Outlook** | `mailbox.item.body` | `setSelectedDataAsync()` | Callback-based |
| **OneNote** | `OneNote.run()` | `addOutline()` | X/Y Position |
| **Access** | Clipboard API | `writeText()` | Manual Paste |
| **VS Code** | Editor API | `insert()` | Cursor Position |

---

## 🔍 Testing Checkliste

### Office Add-ins
- [ ] Backend läuft (`http://localhost:5000/health`)
- [ ] Manifest sideloaded (Shared Folder)
- [ ] Taskpane öffnet sich (Start → My Add-ins)
- [ ] Prompts laden erfolgreich
- [ ] Hybrid-Suche funktioniert
- [ ] Insert-Funktion arbeitet korrekt
- [ ] Dokument-Abruf mit Auto-Insert

### VS Code Extension
- [ ] Extension installiert (npm install)
- [ ] F5 → Extension Host startet
- [ ] Commands im Command Palette sichtbar
- [ ] Keybindings funktionieren (Ctrl+Shift+V S/P)
- [ ] Sidebar Views erscheinen
- [ ] Webview Panel öffnet sich

### Office Ingestion API
- [ ] Upload-Endpoint erreichbar
- [ ] File Type Validation funktioniert
- [ ] Job Status abrufbar
- [ ] Statistics-Endpoint liefert Daten
- [ ] (Optional) Parser integriert und funktioniert

---

## 🐛 Troubleshooting

### Add-in wird nicht angezeigt
**Lösung:**
```powershell
# Cache löschen
Remove-Item "$env:LOCALAPPDATA\Microsoft\Office\16.0\Wef\*" -Recurse -Force
# Office App neustarten
```

### CORS-Fehler
**Lösung:** Backend CORS-Middleware prüfen
```python
# backend/app.py
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### Taskpane lädt nicht (404)
**Lösung:** Static Files Mount prüfen
```python
# backend/app.py (Lines 525-530)
app.mount("/office", StaticFiles(directory="desktop/word-addin"), name="office")
```

### VS Code Extension nicht aktiv
**Lösung:**
```bash
# Entwickler-Tools öffnen (Extension Host)
Help → Toggle Developer Tools
# Console → Fehler prüfen
```

### Office Upload 400 Error
**Ursache:** Unsupported File Type
**Lösung:** Nur .docx, .xlsx, .pptx hochladen

---

## 📊 Feature Comparison

| Feature | Word | Excel | PPT | Outlook | OneNote | Access | VS Code |
|---------|------|-------|-----|---------|---------|--------|---------|
| Prompts | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Search | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Fetch | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Insert | Text | Table | Box | Body | Outline | Clip | Editor |
| README | ✅ | ✅ | ✅ | ⏸️ | ⏸️ | ⏸️ | ⏸️ |

---

## 📚 Dokumentation

**Vollständige Dokumentation:**
- `docs/OFFICE_INTEGRATION_COMPLETE.md` (2000+ Zeilen)

**App-spezifische READMEs:**
- `desktop/word-addin/README.md`
- `desktop/excel-addin/README.md`
- `desktop/powerpoint-addin/README.md`
- `desktop/outlook-addin/README.md` (TODO)
- `desktop/onenote-addin/README.md` (TODO)
- `desktop/access-addin/README.md` (TODO)
- `desktop/vscode-extension/README.md` (TODO)

**Admin Tools:**
- `desktop/README.md` (Installer + Packager)
- `desktop/BUILD_EXAMPLES.md` (PowerShell Script Beispiele)

---

## ✅ Next Steps

### Sofort verfügbar:
1. Backend starten + Add-ins testen ✅
2. VS Code Extension testen (F5) ✅
3. Office Ingestion API testen (curl) ✅

### Integration (Optional):
1. Parser-Libraries installieren:
   ```bash
   pip install python-docx openpyxl python-pptx
   ```
2. STUB-Kommentare in `office_parsers.py` ersetzen
3. RAG-Integration in `office_ingestion.py` aktivieren
4. Tests mit echten Office-Dateien

### Erweiterungen (Optional):
1. Multi-App Packager (Dropdown für 6 Apps)
2. Build Script Parameter `-AppType`
3. READMEs für Outlook/OneNote/Access/VS Code
4. CI/CD Integration (GitHub Actions)

---

**Status:** 8/9 Tasks Complete ✅
**Ready for:** Testing + Parser Integration
**Contact:** VERITAS Development Team
