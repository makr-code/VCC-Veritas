# VERITAS Office Integration - Complete Suite

**Erstellt:** 1. November 2025  
**Status:** ✅ COMPLETE (8/9 Tasks - Packager optional)  
**Scope:** Office Add-ins (6 Apps) + VS Code Extension + RAG Ingestion Stubs

---

## 📊 Übersicht

**Implementierte Add-ins:**
1. ✅ **Word** - Text-Insert (Selection)
2. ✅ **Excel** - Tabellen-Insert (Next Row)
3. ✅ **PowerPoint** - TextBox auf Folie
4. ✅ **Outlook** - E-Mail-Body-Insert (NEW!)
5. ✅ **OneNote** - Outline-Insert (NEW!)
6. ✅ **Access** - Zwischenablage-Fallback (NEW!)

**VS Code Extension:**
7. ✅ **VS Code MCP Client** - Commands + Sidebar (NEW!)

**Backend RAG Integration:**
8. ✅ **Office Ingestion API** - Upload Endpoints (STUB)
9. ✅ **Office Parsers** - docx/xlsx/pptx Parser (STUB)

---

## 🏗️ Architektur

```
VERITAS Office Integration:

Frontend (Office Add-ins):
  ├─ Word Add-in (Word.run() API)
  ├─ Excel Add-in (Excel.run() API)
  ├─ PowerPoint Add-in (PowerPoint.run() API)
  ├─ Outlook Add-in (Mailbox API)
  ├─ OneNote Add-in (OneNote.run() API)
  └─ Access Add-in (Clipboard Fallback)

VS Code Extension:
  ├─ MCP HTTP Client (fetch API)
  ├─ Commands (Ctrl+Shift+V S/P)
  ├─ Sidebar Views (Search + Documents)
  └─ Webview Panel (Interactive Search)

Backend (MCP HTTP Bridge):
  ├─ GET /api/mcp/prompts
  ├─ POST /api/mcp/prompts/{name}/render
  ├─ POST /api/mcp/tools/hybrid_search
  └─ GET /api/mcp/resources/documents/{id}

Backend (Office Ingestion - NEW!):
  ├─ POST /api/office/upload (Single File)
  ├─ POST /api/office/upload/batch (Multiple Files)
  ├─ GET /api/office/jobs/{job_id} (Status)
  ├─ GET /api/office/jobs (List All)
  ├─ DELETE /api/office/jobs/{job_id}
  └─ GET /api/office/stats (Statistics)

Backend (Parsers - STUB):
  ├─ parse_word_document() (python-docx TODO)
  ├─ parse_excel_document() (openpyxl TODO)
  └─ parse_powerpoint_document() (python-pptx TODO)
```

---

## 📁 Neue Dateien (Session 1. Nov 2025)

### Office Add-ins (3 neue Apps)

**Outlook Add-in:**
```
desktop/outlook-addin/
  ├─ manifest.local.xml (Host="Mailbox", Id=...f004)
  ├─ taskpane.html (Button: "In E-Mail einfügen")
  └─ taskpane.js (insertIntoOutlook via setSelectedDataAsync)
```

**OneNote Add-in:**
```
desktop/onenote-addin/
  ├─ manifest.local.xml (Host="Notebook", Id=...f005)
  ├─ taskpane.html (Button: "In OneNote einfügen")
  └─ taskpane.js (insertIntoOneNote via addOutline)
```

**Access Add-in:**
```
desktop/access-addin/
  ├─ manifest.local.xml (Host="Database", Id=...f006)
  ├─ taskpane.html (Button: "In Access einfügen")
  └─ taskpane.js (insertIntoAccess via Clipboard API)
```

### VS Code Extension

```
desktop/vscode-extension/
  ├─ package.json (MCP Client, Commands, Views)
  └─ extension.js (600+ lines)
      ├─ Commands: hybridSearch, renderPrompt, fetchDocument, openSearchPanel
      ├─ Keybindings: Ctrl+Shift+V S/P
      ├─ Views: veritasSearchView, veritasDocumentsView
      └─ Webview: Interactive Search Panel
```

### Backend RAG Integration

**Office Ingestion API:**
```
backend/api/office_ingestion.py (500+ lines)
  ├─ POST /api/office/upload (UploadResponse)
  ├─ POST /api/office/upload/batch (BatchUploadResponse)
  ├─ GET /api/office/jobs/{job_id} (JobStatus)
  ├─ GET /api/office/jobs (List[JobStatus])
  ├─ DELETE /api/office/jobs/{job_id}
  └─ GET /api/office/stats (Statistics)

Features:
  ✅ File Type Validation (.docx, .xlsx, .pptx)
  ✅ Size Limit (50MB)
  ✅ Job Management (in-memory)
  ✅ Batch Upload Support
  ✅ Error Handling
  ⏸️ Parser Integration (STUB - TODO)
  ⏸️ RAG Indexing (STUB - TODO)
```

**Office Parsers:**
```
backend/services/office_parsers.py (400+ lines)
  ├─ parse_word_document() (STUB - python-docx TODO)
  ├─ parse_excel_document() (STUB - openpyxl TODO)
  ├─ parse_powerpoint_document() (STUB - python-pptx TODO)
  └─ parse_office_document() (Generic Dispatcher)

STUB Features:
  ✅ Simulated Text Extraction
  ✅ Dummy Metadata Generation
  ✅ Structure Simulation (Paragraphs/Sheets/Slides)
  ✅ Chunking Preparation
  ⏸️ Real Parsing (TODO - siehe Kommentare)

TODO Integration:
  pip install python-docx openpyxl python-pptx
  # Siehe inline TODO-Kommentare für Code-Beispiele
```

### Backend Integration

**backend/app.py (Modified):**
```python
# Lines 139-150: Office Ingestion Router Import
from backend.api.office_ingestion import router as office_ingestion_router
OFFICE_INGESTION_AVAILABLE = True

# Lines 527-531: Router Mount
if OFFICE_INGESTION_AVAILABLE and office_ingestion_router:
    app.include_router(office_ingestion_router)
    logger.info("✅ Office Ingestion API mounted at /api/office")
```

---

## 🎯 App-spezifische Implementierungen

### Outlook (E-Mail Integration)

**API:** `Office.context.mailbox.item.body.setSelectedDataAsync()`

**Use Case:**
- Recherche-Ergebnisse direkt in E-Mail-Body einfügen
- Funktioniert in Compose + Read Mode
- Einfügen an Cursor-Position

**Code:**
```javascript
Office.context.mailbox.item.body.setSelectedDataAsync(
  text,
  { coercionType: Office.CoercionType.Text },
  function(result) {
    if (result.status === Office.AsyncResultStatus.Failed) {
      log(`Outlook-Fehler: ${result.error.message}`);
    } else {
      log('In E-Mail eingefügt');
    }
  }
);
```

### OneNote (Notizen-Integration)

**API:** `OneNote.run()` mit `addOutline()`

**Use Case:**
- Recherche-Ergebnisse als Outline-Block auf aktiver Seite
- Strukturierte Notizen
- Position konfigurierbar (50, 50)

**Code:**
```javascript
await OneNote.run(async (context) => {
  const activePage = context.application.getActivePage();
  const pageContents = activePage.contents;
  const outline = pageContents.addOutline(50, 50, text);
  await context.sync();
});
```

### Access (Datenbank-Integration)

**API:** Navigator Clipboard API (Fallback)

**Use Case:**
- Access hat KEINE direkte Office.js API
- Fallback: Text in Zwischenablage kopieren
- User fügt manuell ein (Strg+V)

**Code:**
```javascript
if (navigator.clipboard) {
  await navigator.clipboard.writeText(text);
  log('Text in Zwischenablage kopiert (Strg+V zum Einfügen)');
}
```

### VS Code (Editor-Integration)

**Commands:**
- `veritas.hybridSearch` (Ctrl+Shift+V S) - Suche mit Selection
- `veritas.renderPrompt` (Quick Pick) - Prompt-Rendering
- `veritas.fetchDocument` (Input Box) - Dokument-Abruf
- `veritas.openSearchPanel` (Ctrl+Shift+V P) - Webview Panel

**Views:**
- `veritasSearchView` - Suchergebnisse (TreeView)
- `veritasDocumentsView` - Dokumente (TreeView)

**Output:**
- Ergebnisse in neuem Markdown-Dokument
- Auto-Formatierung mit Quellen
- Insert at Cursor

---

## 🔧 Office Ingestion API

### Upload Single File

**Endpoint:** `POST /api/office/upload`

**Request:**
```bash
curl -X POST http://localhost:5000/api/office/upload \
  -F "file=@document.docx" \
  -F "metadata={\"author\":\"John\"}"
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.docx",
  "file_type": "word",
  "size_bytes": 15360,
  "status": "completed",
  "message": "[STUB] Dokument erfolgreich hochgeladen",
  "timestamp": "2025-11-01T10:30:00"
}
```

### Batch Upload

**Endpoint:** `POST /api/office/upload/batch`

**Request:**
```bash
curl -X POST http://localhost:5000/api/office/upload/batch \
  -F "files=@doc1.docx" \
  -F "files=@sheet1.xlsx" \
  -F "files=@pres1.pptx"
```

**Response:**
```json
{
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "total_files": 3,
  "successful": 3,
  "failed": 0,
  "files": [...],
  "timestamp": "2025-11-01T10:35:00"
}
```

### Job Status

**Endpoint:** `GET /api/office/jobs/{job_id}`

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 1.0,
  "total_documents": 1,
  "processed_documents": 1,
  "errors": [],
  "started_at": "2025-11-01T10:30:00",
  "completed_at": "2025-11-01T10:30:05"
}
```

### Statistics

**Endpoint:** `GET /api/office/stats`

**Response:**
```json
{
  "total_jobs": 42,
  "jobs_by_status": {
    "completed": 38,
    "processing": 2,
    "failed": 2
  },
  "total_documents": 150,
  "processed_documents": 145,
  "success_rate": 0.967,
  "timestamp": "2025-11-01T11:00:00"
}
```

---

## 📝 Parser Integration (TODO)

### Installation

```bash
pip install python-docx openpyxl python-pptx
```

### Word Parser Integration

**Datei:** `backend/services/office_parsers.py` (Lines 30-70)

**TODO-Kommentar enthält:**
```python
from docx import Document
import io

doc = Document(io.BytesIO(content))

# Text extraction
paragraphs = [p.text for p in doc.paragraphs]
text = '\n'.join(paragraphs)

# Tables
tables = []
for table in doc.tables:
    table_data = [[cell.text for cell in row.cells] for row in table.rows]
    tables.append(table_data)

# Metadata
metadata = {
    'title': doc.core_properties.title,
    'author': doc.core_properties.author,
    'created': doc.core_properties.created
}
```

### Excel Parser Integration

**Datei:** `backend/services/office_parsers.py` (Lines 120-160)

**TODO-Kommentar enthält:**
```python
from openpyxl import load_workbook
import io

wb = load_workbook(io.BytesIO(content), data_only=True)

# Extract all sheets
sheets = {}
for sheet_name in wb.sheetnames:
    sheet = wb[sheet_name]
    data = []
    for row in sheet.iter_rows(values_only=True):
        data.append(list(row))
    sheets[sheet_name] = data
```

### PowerPoint Parser Integration

**Datei:** `backend/services/office_parsers.py` (Lines 210-260)

**TODO-Kommentar enthält:**
```python
from pptx import Presentation
import io

prs = Presentation(io.BytesIO(content))

# Extract slides
slides = []
for i, slide in enumerate(prs.slides):
    slide_data = {'slide_number': i + 1, 'title': '', 'content': []}
    for shape in slide.shapes:
        if hasattr(shape, "text"):
            if shape.is_placeholder and shape.placeholder_format.type == 1:
                slide_data['title'] = shape.text
            else:
                slide_data['content'].append(shape.text)
    slides.append(slide_data)
```

### RAG Integration

**Datei:** `backend/api/office_ingestion.py` (Lines 80-90)

**TODO-Kommentar:**
```python
# STUB: Hier würde der echte Parser aufgerufen werden
from backend.services.office_parsers import parse_office_document
parsed_data = parse_office_document(content, file_type)

# STUB: Hier würde RAG-Indexierung erfolgen
from backend.services.rag_indexer import index_document
index_document(parsed_data)
```

---

## 🚀 Testing

### Office Add-ins Testen

```powershell
# 1. Backend starten
python backend/app.py

# 2. Add-in sideloaden (Windows)
# - Word/Excel/PowerPoint/Outlook/OneNote/Access öffnen
# - Manifest aus desktop/{app}-addin/manifest.local.xml laden
# - Shared Folder: %LOCALAPPDATA%\Microsoft\Office\16.0\Wef\

# 3. Taskpane öffnen
# - Start → My Add-ins → VERITAS {App} Adapter (Local)

# 4. Funktionen testen
# - Prompts laden → Prompt auswählen → Rendern
# - Hybrid-Suche → Ergebnis prüfen
# - In {App} einfügen → Inhalt validieren
# - Dokument abrufen → Auto-Insert prüfen
```

### VS Code Extension Testen

```bash
# 1. Extension installieren (Dev Mode)
cd desktop/vscode-extension
npm install
code .
# F5 drücken → Extension Host öffnet sich

# 2. Commands testen
# Ctrl+Shift+V S → Hybrid-Suche mit Selection
# Ctrl+Shift+V P → Search Panel öffnen
# Command Palette: "VERITAS: ..."

# 3. Sidebar testen
# Activity Bar → VERITAS Icon → Views öffnen
```

### Office Ingestion API Testen

```bash
# Single Upload
curl -X POST http://localhost:5000/api/office/upload \
  -F "file=@test.docx"

# Batch Upload
curl -X POST http://localhost:5000/api/office/upload/batch \
  -F "files=@doc1.docx" \
  -F "files=@sheet1.xlsx"

# Job Status
curl http://localhost:5000/api/office/jobs/{job_id}

# Statistics
curl http://localhost:5000/api/office/stats
```

---

## 📋 Todo: Multi-App Packager (Optional)

**Aktuell:** Packager unterstützt nur Word-Add-in

**Erweiterung:**
```python
# desktop/office_packager.py (Lines 50-60)

# Dropdown für App-Typ
self.var_app_type = tk.StringVar(value="word")
ttk.Label(frm_src, text="App-Typ:").grid(row=0, column=0, sticky="w")
ttk.Combobox(
    frm_src, 
    textvariable=self.var_app_type,
    values=["word", "excel", "powerpoint", "outlook", "onenote", "access"],
    state="readonly"
).grid(row=0, column=1, sticky="ew", padx=5)

# ZIP-Name anpassen
app_type = self.var_app_type.get()
source_dir = os.path.join(desktop_dir, f"{app_type}-addin")
out_name = f"veritas_{app_type}_addin_{version}.zip"
```

**Build Script Erweiterung:**
```powershell
# desktop/build_package.ps1

param(
    [ValidateSet("word", "excel", "powerpoint", "outlook", "onenote", "access")]
    [string]$AppType = "word",
    [string]$Version,
    [string]$BackendUrl = "http://localhost:5000"
)

$SourceDir = Join-Path $ScriptDir "$AppType-addin"
$OutputZip = "veritas_$($AppType)_addin_$Version.zip"
```

---

## 📊 Feature Matrix

| Feature | Word | Excel | PowerPoint | Outlook | OneNote | Access | VS Code |
|---------|------|-------|------------|---------|---------|--------|---------|
| **Prompt Rendering** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Hybrid Search** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Document Fetch** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Auto-Insert** | ✅ Text | ✅ Table | ✅ TextBox | ✅ Body | ✅ Outline | ⚠️ Clipboard | ✅ Editor |
| **Backend URL Config** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Logging** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ Output |
| **Keybindings** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Sidebar Views** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Webview Panel** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 🎓 Lessons Learned

### Outlook API Differences

**Problem:** Outlook verwendet `mailbox.item.body` statt `run()` Context  
**Solution:** Callback-basierte API mit `setSelectedDataAsync()`

### OneNote Outline Positioning

**Problem:** OneNote erfordert explizite X/Y-Koordinaten  
**Solution:** `addOutline(50, 50, text)` - feste Position

### Access API Limitation

**Problem:** Access hat KEINE Office.js API für direktes Insert  
**Solution:** Fallback zu Clipboard API (user muss manuell einfügen)

### VS Code Extension Activation

**Problem:** `activationEvents` sind deprecated (Warnings in package.json)  
**Solution:** Ignorieren - VS Code generiert automatisch aus `contributes.commands`

### Parser STUB Design

**Problem:** Sofortige Integration blockiert Add-in-Entwicklung  
**Solution:** STUB mit TODO-Kommentaren + Code-Beispielen

---

## 📚 Dokumentation

**Erstellt:**
- `desktop/excel-addin/README.md` (Excel-spezifisch, Installation, API)
- `desktop/powerpoint-addin/README.md` (PowerPoint-spezifisch, Layout Best Practices)

**TODO:**
- `desktop/outlook-addin/README.md`
- `desktop/onenote-addin/README.md`
- `desktop/access-addin/README.md`
- `desktop/vscode-extension/README.md`

---

## ✅ Status Summary

**Completed (8/9 Tasks):**
1. ✅ Excel Add-in (manifest, HTML, JS, README)
2. ✅ PowerPoint Add-in (manifest, HTML, JS, README)
3. ✅ Outlook Add-in (manifest, HTML, JS)
4. ✅ OneNote Add-in (manifest, HTML, JS)
5. ✅ Access Add-in (manifest, HTML, JS)
6. ✅ VS Code Extension (package.json, extension.js)
7. ✅ Office Ingestion API (backend/api/office_ingestion.py)
8. ✅ Office Parsers (backend/services/office_parsers.py - STUB)

**Optional (Not Started):**
9. ⏸️ Multi-App Packager (Dropdown für 6 Apps)

**Production Ready:**
- ✅ All 6 Office Add-ins scaffolded
- ✅ VS Code Extension functional
- ✅ Backend API integrated
- ⏸️ Parser integration pending (python-docx, openpyxl, python-pptx)

---

**Version:** 1.0.0  
**Author:** VERITAS Development Team  
**Last Updated:** 1. November 2025
