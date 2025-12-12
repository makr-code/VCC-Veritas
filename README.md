# VERITAS - VCC Agentenbasiertes AI-Chat-System

## Version 3.19.0 ✅ PRODUCTION READY

**VERITAS** ist ein hochmodernes, **agentenbasiertes AI-Chat-System** mit intelligenter Multi-Agent-Orchestrierung. Das System kombiniert spezialisierte Domain-Agents, natürliche Sprachverarbeitung und RAG (Retrieval-Augmented Generation), um präzise, kontextbezogene Antworten auf komplexe Fragen zu liefern.

### 🤖 Multi-Agent-Architektur

VERITAS nutzt über **40 spezialisierte Agenten** in 10 Domänen, die durch einen intelligenten Orchestrator koordiniert werden:
- **Environmental Agents**: Umweltschutz, Naturschutz, Boden-/Gewässerschutz, Emissionsmonitoring
- **Construction Agents**: Baugenehmigungen, Baurecht, Compliance
- **Weather Agents**: DWD-Integration, BrightSky, Wettervorhersagen
- **Chemical Agents**: Chemikalien-Datenbanken, Stoffinformationen
- **Social/Legal Agents**: Verwaltungsrecht, Rechtrecherche, Verwaltungsprozesse
- **Immissionsschutz Agents**: BImSchG-Compliance, Genehmigungsverfahren
- **Standards Agents**: DIN, VDI, ISO-Normen
- **Traffic Agents**: Verkehrsrecht, Verkehrsplanung
- **Financial Agents**: Finanzielle Bewertungen, Kostenanalysen
- **Database/Wikipedia Agents**: Allgemeine Recherche und Datenbankzugriffe

**🎉 Production Deployment Complete (11. Oktober 2025)**

---

## 🚀 Quick Start (2 Minuten)

### 1. Backend starten
```powershell
python start_backend.py
```

### 2. Frontend starten (neues Terminal)
```powershell
python start_frontend.py
```

### 3. Health Check
```powershell
curl http://localhost:5000/api/feedback/health
```

**📖 Vollständige Anleitung:** [`QUICK_START.md`](QUICK_START.md)
**📋 Production Checklist:** [`PRODUCTION_CHECKLIST.md`](PRODUCTION_CHECKLIST.md)

---

## 🌟 Hauptfunktionen

### 🤖 Intelligent Agent Orchestration
- **40+ Spezialisierte Agenten**: Domain-spezifische Experten für verschiedene Fachbereiche
- **Agent Orchestrator**: Intelligente Koordination mehrerer Agenten für komplexe Anfragen
- **BaseAgent Framework**: Einheitliche Architektur mit Schema-basierter Planausführung
- **Agent Registry**: Automatische Agent-Discovery basierend auf Capabilities
- **Quality Gates**: Monitoring, Retry-Handling und Qualitätssicherung
- **Parallel Processing**: Bis zu 3x Speedup durch parallele Agent-Ausführung
- **Cost-Benefit-Optimierung**: Ressourcen-optimierte Agent-Auswahl

### 🎯 Flexible LLM-Integration
- **Multi-Provider-Support**: Ollama oder vLLM
- **Automatischer Fallback**: Nahtloser Wechsel bei Ausfall
- **Provider-agnostisch**: Gleiche API für alle Provider
- **Performance-optimiert**: vLLM für Produktion (+200% Durchsatz)
- **Einfacher Wechsel**: Via Umgebungsvariable `LLM_PROVIDER`

### 💬 Agentenbasierter Chat (Chat Design v2.0)
- **Multi-Agent-Pipeline**: Intelligente Routing-Entscheidungen basierend auf Query-Analyse
- **Agent-Koordination**: Orchestrator wählt optimale Agenten für die Anfrage
- **Sprechblasen-Design**: User (rechts) vs Assistant (links)
- **Strukturierte Antworten**: 6 Sections (Antwort, Details, Quellen, Rechtliche Hinweise, Nächste Schritte, Verwandte Themen)
- **Dual-Prompt System**: Natural language responses (keine generischen Floskeln)
- **UDS3 Hybrid Search**: Neo4j Graph Search (1,930 Dokumente) + Vector + Keyword
- **Streaming-Antworten**: Echtzeit-Fortschrittsupdates während der Verarbeitung
- **Raw Response Debug**: Collapsible debug view für LLM-Responses
- **Agent-Feedback**: Transparente Anzeige welche Agenten an der Antwort beteiligt waren

### 🎛️ LLM Parameter UI Extensions
- **4 Presets**: Präzise, Standard, Ausführlich, Kreativ (1-Klick)
- **Token Counter**: Echtzeit-Längen-Schätzung (💬/📝/⚠️)
- **Antwortzeit-Prädiktion**: Modell-basierte Schätzung (⚡/⏱️/🐌)
- **Parameter-Tuning**: Temperature (0.1-1.0), Tokens (100-2000), Top-p (0.1-1.0)

### 👍👎 Feedback-System
- **3-Button Widget**: 👍 Hilfreich, 👎 Nicht hilfreich, 💬 Kommentar
- **Backend-Integration**: SQLite-Persistierung + FastAPI (4 Endpoints)
- **Analytics**: Positive Ratio, Average Rating, Top Categories
- **Non-blocking UI**: Threaded submissions

### 📊 Office-Integration (Word/Excel Export)
- **Word-Export (.docx)**: Formatierte Chat-Historie mit Quellen, Markdown → Word Conversion
- **Excel-Export (.xlsx)**: 3 Sheets (Messages, Statistiken, Quellen)
- **Export-Dialog**: Zeitraum-Filter, Optionen (Metadata, Sources), Custom Filename

### 🖱️ Drag & Drop Integration
- **32 Dateiformate**: PDF, DOCX, TXT, MD, JSON, XML, CSV, XLSX, PNG, JPG, etc.
- **SHA256 Deduplication**: Automatische Duplikat-Erkennung
- **Size Validation**: Max 50 MB pro Datei, max 10 Dateien gleichzeitig
- **Visual Feedback**: Grüne Border bei Hover, Error Messages

### 🔌 Backend-API-Kommunikation
- **HTTP/HTTPS**: Sichere REST-API-Verbindung
- **FastAPI Backend**: Hochperformante asynchrone Verarbeitung (14 Endpoints)
- **Universal JSON Payloads**: Standardisierte Datenstrukturen
- **Session Management**: Persistente Benutzersitzungen

### 📊 Datenverarbeitung
- **UDS3 Integration** (Backend): Multi-Datenbank-Strategie
- **Neo4j**: Graph-Datenbank für Relationen
- **Vector Search**: Semantische Ähnlichkeitssuche
- **Quality Metrics**: Bewertung der Antwortqualität

---

## 🏗️ Architektur

### Multi-Agent-System Übersicht

```
┌────────────────────────────────────────────────────────────────┐
│                    VERITAS Multi-Agent System                  │
└────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Tkinter GUI)                   │
│  • Tkinter GUI (Python 3.13)    • HTTP/HTTPS API-Client        │
│  • Mehrfenster-Management       • Keine Datenbankzugriffe      │
│  • Plattformunabhängig           • Chat & Streaming UI         │
└─────────────────────────────────────────────────────────────────┘
                                │ HTTP/HTTPS
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI Server)                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Agent Orchestrator (Query Router)             │  │
│  │  • Query Analysis & Intent Detection                     │  │
│  │  • Agent Selection (Cost-Benefit-Optimierung)           │  │
│  │  • Pipeline Coordination                                 │  │
│  │  • Parallel/Sequential Execution                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Agent Registry & Framework                  │  │
│  │  • 40+ Spezialisierte Domain Agents                      │  │
│  │  • BaseAgent Framework (Schema-based)                    │  │
│  │  • Quality Gates & Monitoring                            │  │
│  │  • Retry Handler & Error Recovery                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                     │
│           ┌───────────────┴───────────────┐                    │
│           ▼                               ▼                    │
│  ┌─────────────────┐            ┌─────────────────┐           │
│  │  Domain Agents  │            │  LLM Integration│           │
│  │  10 Kategorien: │            │  • Ollama       │           │
│  │  • Environmental│            │  • vLLM         │           │
│  │  • Construction │            │  • Auto-Fallback│           │
│  │  • Weather      │            └─────────────────┘           │
│  │  • Chemical     │                     │                     │
│  │  • Social/Legal │                     ▼                     │
│  │  • Immission    │            ┌─────────────────┐           │
│  │  • Standards    │            │   UDS3 Multi-DB │           │
│  │  • Traffic      │            │  • Neo4j Graph  │           │
│  │  • Financial    │            │  • ChromaDB     │           │
│  │  • Database/Wiki│            │  • PostgreSQL   │           │
│  └─────────────────┘            │  • Hybrid Search│           │
│                                 └─────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend-Backend Architektur
```
┌─────────────────────────────────┐
│   Tkinter GUI (Python 3.13)     │
│  - Mehrfenster-Management       │
│  - HTTP/HTTPS API-Client        │
│  - Keine Datenbankzugriffe      │
│  - Plattformunabhängig          │
└─────────────────────────────────┘
            ↕ HTTP/HTTPS
┌─────────────────────────────────┐
│   FastAPI Backend (Server)      │
│  - REST API Endpoints           │
│  - Multi-Agent Orchestration    │
│  - Ollama/vLLM LLM Integration  │
│  - UDS3 Multi-DB                │
│  - Streaming Services           │
└─────────────────────────────────┘
```

### Komponenten

#### **Frontend** (`frontend/`)
- `veritas_app.py`: Haupt-GUI-Anwendung (Tkinter)
- `ui/`: UI-Komponenten und Widgets
- `services/`: Streaming und Backend-Kommunikation

#### **Backend** (`backend/`)
- `api/`: FastAPI REST-Endpunkte
- `agents/`: Intelligente Multi-Agent-Pipeline
  - `framework/`: BaseAgent, QualityGate, StateMachine, Monitoring
  - `orchestrator/`: Agent Orchestrator, Pipeline Manager
  - `registry/`: Agent Registry, Capability Management
  - `domain/`: 40+ Domain-spezifische Agenten (10 Kategorien)
  - `specialized/`: Spezialisierte Utility-Agenten
- `services/`: Business-Logik und Datenverarbeitung

#### **Shared** (`shared/`)
- `core/`: Kernfunktionalität (Threading, Sessions)
- `pipelines/`: Datenverarbeitungs-Pipelines
- `universal_json_payload.py`: Standardisierte Payloads

#### **UDS3** (`uds3/`)
- Multi-Datenbank-Distribution-System
- Adaptierte Strategien für verschiedene Datentypen
- Security- und Quality-Management

---

## 🚀 Schnellstart

### Voraussetzungen
- Python 3.13+
- LLM Provider (wähle einen):
  - **Ollama** (empfohlen für Entwicklung) - [Installation](https://ollama.ai)
  - **vLLM** (empfohlen für Produktion) - [Quick Start](docs/VLLM_QUICK_START.md)
- Optional: Neo4j (für Graph-Datenbank)

### Installation

1. **Repository klonen**:
   ```bash
   git clone <repository-url>
   cd veritas
   ```

2. **Dependencies installieren**:
   ```bash
   pip install -r requirements.txt
   ```

3. **LLM Provider starten** (separates Terminal):
   
   **Option A: Ollama** (Standard)
   ```bash
   ollama serve
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```
   
   **Option B: vLLM** (High-Performance)
   ```bash
   pip install vllm
   python -m vllm.entrypoints.openai.api_server \
     --model meta-llama/Meta-Llama-3-8B-Instruct
   ```
   
   Siehe [vLLM Quick Start](docs/VLLM_QUICK_START.md) für Details.

4. **Konfiguration** (optional):
   ```bash
   # Für Ollama (Standard)
   export LLM_PROVIDER=ollama
   
   # Für vLLM
   export LLM_PROVIDER=vllm
   export VLLM_API_URL=http://localhost:8000
   ```

### Anwendung starten

#### Backend starten:
```bash
python start_backend.py
```
Backend läuft auf: `http://localhost:5000`

**Neue Endpoints (v3.20.0):**
- `/api/checklist/generate` - Generiert Checklisten basierend auf ThemisDB-Daten und Vorschriften
- `/api/checklist/generate/stream` - **SSE-Streaming** für Echtzeit-Fortschritt (NEU!)
- `/api/checklist/generate/zip` - Generiert Checkliste als ZIP mit eingebetteten Dateien
- `/api/checklist/upload` - **Datei-Upload zur Laufzeit** (NEU!)
- `/api/checklist/export/{session_id}` - Exportiert vorhandene Checkliste als ZIP
- `/api/checklist/health` - Checklist-Service Health Check
- `/api/checklist/types` - Verfügbare Checklisten-Typen
- `/api/checklist/capabilities` - Checklist-Agent Capabilities

#### Frontend starten:
```bash
python start_frontend.py
```

---

## 📖 Verwendung

### 1. Agentenbasierte Frage-Modi
- **Multi-Agent RAG**: Komplexe Fragen werden automatisch an mehrere spezialisierte Agenten geroutet
- **Single-Agent Queries**: Einfache Fragen werden direkt von einem passenden Agenten bearbeitet
- **Agent Orchestration**: Der Orchestrator wählt basierend auf Query-Analyse die optimalen Agenten
- **Domain-Spezifisch**: Spezialisierte Modi für Umwelt, Bau, Recht, Wetter, Chemie, etc.

**Beispiele:**
- "Was sind die Umweltauflagen für ein Bauvorhaben?" → Environmental + Construction Agents
- "Wie ist das Wetter morgen in Berlin?" → Weather Agent
- "Welche BImSchG-Vorschriften gelten für Windkraftanlagen?" → Immissionsschutz + Standards Agents

### 2. LLM-Modelle wählen
- Klicken Sie auf das Dropdown-Menü
- Wählen Sie ein verfügbares Modell (z.B. `llama3:latest`)
- Temperatur und Max-Tokens anpassen

### 3. Frage stellen
- Geben Sie Ihre Frage in das Eingabefeld ein
- Drücken Sie `Enter` oder klicken Sie auf "Senden"
- Der Agent Orchestrator analysiert die Anfrage und wählt die passenden Agenten
- Warten Sie auf die Streaming-Antwort mit Echtzeit-Fortschritt

### 4. Agent-Feedback verstehen
- Im Chat sehen Sie, welche Agenten an der Antwort beteiligt waren
- Quality Metrics zeigen die Zuverlässigkeit der Agenten
- Debug-View zeigt den kompletten Agent-Pipeline-Prozess

### 5. Chat-Management
- **💾 Speichern**: Chat als JSON-Datei speichern
- **📂 Laden**: Gespeicherten Chat wiederherstellen
- **🗑️ Löschen**: Chat-Verlauf zurücksetzen
- **➕ Neuer Chat**: Zusätzliches Fenster öffnen

### 6. Checklisten-Generierung (Agent-basiert)
VERITAS nutzt spezialisierte Agents zur automatischen Checklisten-Erstellung:

**Via Chat (Automatische Agent-Erkennung):**
- "Erstelle eine Checkliste für Bauantrag" → Construction Agent
- "Checkliste für Umweltgenehmigung" → Environmental Agent
- "Was muss ich beachten bei Bauvoranfrage" → Construction + Legal Agents

**Via API:**
```bash
curl -X POST http://localhost:5000/api/checklist/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Bauantrag für Einfamilienhaus",
    "checklist_type": "construction",
    "include_regulations": true,
    "include_themisdb": true
  }'
```

**Features:**
- Agent-basierte Checklisten-Generierung mit Domain-Experten
- Basierend auf ThemisDB-Dokumenten und geltenden Vorschriften
- Automatische Intent-Erkennung und Agent-Selektion
- JSON-Format für Argus2 Android App Integration
- **ZIP-Export mit eingebetteten Dateien**
- **SSE (Server-Sent Events) für Echtzeit-Fortschritt** (NEU!)
- **MCP (Model Context Protocol) Support** (NEU!)
- **Datei-Upload zur Laufzeit** (NEU!)
- 10 vordefinierte Checklist-Typen (Construction, Compliance, Environmental, etc.)

**SSE Streaming (Echtzeit-Fortschritt):**
Mit Server-Sent Events können Sie den Generierungsprozess in Echtzeit verfolgen:

```javascript
// JavaScript/Frontend
const source = new EventSource('/api/checklist/generate/stream?topic=Bauantrag&checklist_type=construction');

source.addEventListener('progress', (e) => {
  const data = JSON.parse(e.data);
  console.log(`${data.percentage}%: ${data.message}`);
});

source.addEventListener('result', (e) => {
  const checklist = JSON.parse(e.data);
  console.log('Checkliste generiert:', checklist);
});

source.addEventListener('complete', (e) => {
  console.log('Fertig!');
  source.close();
});
```

**Datei-Upload zur Laufzeit:**
Während der Checklisten-Generierung können Dateien hochgeladen werden:

```bash
# 1. Session erstellen und Dateien hochladen
curl -X POST http://localhost:5000/api/checklist/upload \
  -F "session_id=checklist_abc12345" \
  -F "files=@grundriss.png" \
  -F "files=@lageplan.pdf"

# 2. Checkliste mit hochgeladenen Dateien generieren
curl -X POST http://localhost:5000/api/checklist/generate/zip \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "checklist_abc12345",
    "topic": "Bauantrag",
    "checklist_type": "construction"
  }' --output checklist.zip
```

**ZIP-Format Support:**
VERITAS unterstützt jetzt einen konsolidierten ZIP-Export, der zusätzliche Dateien
(png, pdf, docx, xlsx, md, mp3, mpeg, etc.) enthalten kann, die sowohl in der JSON-Frage
(embedded markdown) als auch im JSON-Response (markdown) verlinkt sind.

```bash
# ZIP mit eingebetteten Dateien generieren
curl -X POST http://localhost:5000/api/checklist/generate/zip \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Bauantrag",
    "checklist_type": "construction",
    "embedded_markdown": "![Grundriss](grundriss.png)\n[Lageplan](lageplan.pdf)",
    "attachments": ["grundriss.png", "lageplan.pdf"]
  }' \
  --output checklist.zip

# Zuvor generierte Checkliste als ZIP exportieren
curl http://localhost:5000/api/checklist/export/checklist_abc12345 --output checklist.zip
```

**ZIP-Inhalte:**
- `checklist.json` - Generierte Checkliste mit Markdown-Links
- `metadata.json` - Session-Informationen und Metadaten
- `README.md` - Dokumentation
- `attachments/` - Eingebettete Dateien (Bilder, PDFs, Dokumente, Audio, Video)

### 7. README anzeigen
- Klicken Sie auf **📘 VERITAS** in der Toolbar (rechts oben)
- Die README wird im Chat-Fenster angezeigt

---

## ⚙️ Konfiguration

### Backend (`config/config.py`)
```python
API_BASE_URL = "http://localhost:5000"
OLLAMA_BASE_URL = "http://localhost:11434"

# Agent System Configuration
AGENT_ORCHESTRATOR_ENABLED = True
MAX_PARALLEL_AGENTS = 3
AGENT_TIMEOUT_SECONDS = 30
```

### Agent Configuration (`backend/agents/`)
- Agent Registry: Automatische Registrierung aller BaseAgent-Implementierungen
- Quality Policy: Konfigurierbare Schwellwerte für Agent-Qualität
- Cost-Benefit-Optimierung: YAML-basierte Ressourcen-Kosten (`themisdb/config/resource_costs.yaml`)

### Frontend
- Automatische Backend-Erkennung
- Session-Persistenz
- Automatisches Speichern von Chats
- Agent-Feedback-Anzeige

---

## 🛠️ Entwicklung

### Projektstruktur
```
veritas/
├── frontend/                    # GUI-Anwendung (Tkinter)
│   ├── veritas_app.py          # Haupt-GUI
│   ├── ui/                     # UI-Komponenten
│   └── services/               # Backend-Kommunikation
├── backend/                     # FastAPI REST API & Agent System
│   ├── api/                    # REST Endpoints
│   ├── agents/                 # Multi-Agent System ⭐
│   │   ├── framework/          # BaseAgent, QualityGate, StateMachine
│   │   ├── orchestrator/       # Agent Orchestration & Pipeline
│   │   ├── registry/           # Agent Registry & Discovery
│   │   ├── domain/             # 40+ Domain-spezifische Agenten
│   │   │   ├── environmental/  # Umwelt-Agenten
│   │   │   ├── construction/   # Bau-Agenten
│   │   │   ├── weather/        # Wetter-Agenten
│   │   │   ├── chemical/       # Chemie-Agenten
│   │   │   ├── social/         # Verwaltung/Recht-Agenten
│   │   │   ├── immissionsschutz/ # BImSchG-Agenten
│   │   │   ├── standards/      # DIN, VDI, ISO-Normen
│   │   │   ├── traffic/        # Verkehrs-Agenten
│   │   │   ├── financial/      # Finanz-Agenten
│   │   │   ├── database/       # Datenbank-Agenten
│   │   │   └── wikipedia/      # Wikipedia-Agenten
│   │   ├── specialized/        # Spezialisierte Agenten
│   │   └── themisdb/           # ThemisDB-Integration
│   ├── services/               # Business-Logik
│   └── app.py                  # Hauptanwendung
├── shared/                      # Gemeinsame Komponenten
│   ├── core/                   # Kernfunktionalität
│   └── pipelines/              # Datenverarbeitungs-Pipelines
├── uds3/                        # Multi-DB System (Neo4j, ChromaDB, PostgreSQL)
├── config/                      # Konfiguration
├── docs/                        # Dokumentation
│   ├── CONSOLIDATED_AGENT_SYSTEM_DOCUMENTATION.md
│   ├── AGENT_SYSTEM_QUICK_REFERENCE.md
│   └── ...
└── tests/                       # Unit-Tests & Integration-Tests
    ├── agents/                 # Agent-Tests
    └── ...
```

### Tests ausführen
```bash
# Alle Tests
pytest tests/

# Nur Agent-Tests
pytest tests/agents/

# Spezifische Agent-Tests
python backend/agents/test_orchestration_integration.py
python backend/agents/test_agent_testserver_integration.py
```

### Backend-Tests
```bash
# UDS3 Integration
python test_uds3_integration.py

# Agent Framework
python backend/agents/framework/test_retry_integration.py
python backend/agents/test_monitoring_integration.py
```

---

## 🔧 Troubleshooting

### Frontend startet nicht
- Prüfen Sie, ob Python 3.13+ installiert ist
- Installieren Sie tkinter: `pip install tk`
- Überprüfen Sie die Logs in `veritas_app.log`

### Backend nicht erreichbar
- Stellen Sie sicher, dass das Backend läuft: `http://localhost:5000`
- Prüfen Sie Firewall-Einstellungen
- Überprüfen Sie `veritas_backend.log`

### Keine LLM-Modelle verfügbar
- Starten Sie Ollama: `ollama serve`
- Laden Sie Modelle herunter: `ollama pull llama3`
- Überprüfen Sie: `ollama list`

### Agenten funktionieren nicht
- Überprüfen Sie die Agent Registry: `http://localhost:5000/api/agents/registry`
- Prüfen Sie Agent-Logs in `data/agent_framework.db`
- Stellen Sie sicher, dass alle Agents korrekt registriert sind
- Überprüfen Sie Quality Gates und Retry-Handler

### UDS3-Fehler (nur Backend)
- UDS3 ist optional und nur im Backend erforderlich
- Frontend funktioniert ohne UDS3
- Backend kann im Fallback-Modus laufen

---

## 📚 Dokumentation

- **API-Dokumentation**: `http://localhost:5000/docs` (wenn Backend läuft)
- **Agent-System Dokumentation**: 
  - `docs/CONSOLIDATED_AGENT_SYSTEM_DOCUMENTATION.md` - Vollständige Agent-Architektur
  - `docs/AGENT_SYSTEM_QUICK_REFERENCE.md` - Schnellreferenz
  - `docs/DOMAIN_AGENTS_DETAILED.md` - Domain-Agent Details
  - `docs/BASEAGENT_QUICK_REFERENCE.md` - BaseAgent Framework
- **Projekt-Dokumentation**: `docs/`
- **UDS3-Dokumentation**: `uds3/README.md`
- **Status-Reports**: `docs/STATUS_REPORT.md`

---

## 🔒 Sicherheit

- **Keine Passwörter in Code**: Umgebungsvariablen verwenden
- **HTTPS-Support**: Für Produktions-Deployments
- **Session-Tokens**: Sichere API-Authentifizierung
- **Input-Validierung**: Pydantic-Modelle für alle Requests

---

## 🤝 Mitwirken

Contributions sind willkommen! Bitte:
1. Fork das Repository
2. Erstelle einen Feature-Branch
3. Committe deine Änderungen
4. Push zum Branch
5. Öffne einen Pull Request

### Neue Agenten entwickeln
Wenn Sie einen neuen Domain-Agent erstellen möchten:
1. Verwenden Sie `BaseAgent` als Basis-Klasse
2. Implementieren Sie `get_agent_type()`, `get_capabilities()` und `execute_step()`
3. Registrieren Sie den Agent in der Agent Registry
4. Fügen Sie Tests hinzu
5. Dokumentieren Sie die Agent-Capabilities

Siehe `docs/BASEAGENT_QUICK_REFERENCE.md` für Details.

---

## 📝 Lizenz

[Lizenzinformationen hier einfügen]

---

## 👥 Team

**VERITAS Development Team**
- Frontend: Tkinter GUI, Multi-Window-Management
- Backend: FastAPI, Multi-Agent Orchestration
- Agent System: 40+ Domain-spezifische Agenten
- UDS3: Multi-Database Distribution System
- Integration: LLM-Provider, Streaming, Quality Gates

---

## 📧 Kontakt

Für Fragen und Support:
- Issues: [GitHub Issues]
- Dokumentation: `docs/`
- Logs: `veritas_app.log`, `veritas_backend.log`

---

**Version**: 3.5.0
**Letztes Update**: 5. Oktober 2025
**Status**: Produktionsreif ✅
