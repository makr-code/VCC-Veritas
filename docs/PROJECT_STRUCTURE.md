# VERITAS Projekt-Struktur Dokumentation

## 📁 Neue Organisierte Verzeichnisstruktur

### 🎨 Frontend (`frontend/`)
Alle clientseitigen Komponenten und Benutzeroberflächen

```
frontend/
├── veritas_app.py                    # Hauptapplikation
├── veritas_main_app.py               # Main App Entry Point
├── ui/                               # UI-Komponenten
│   ├── veritas_ui_components.py      # UI-Hilfselemente & Tooltips
│   ├── veritas_ui_feedback_system.py # Feedback System UI
│   ├── veritas_ui_statusbar.py       # Status Bar Komponenten
│   └── veritas_ui_toolbar.py         # Toolbar Komponenten
├── streaming/                        # Streaming-Integration
│   └── veritas_frontend_streaming.py # Frontend Streaming Integration
└── themes/                          # UI-Themes
    └── veritas_forest_theme.py      # Forest Theme
```

### ⚙️ Backend (`backend/`)
Server-seitige Logik, APIs und Services

```
backend/
├── api/                                          # API Layer
│   ├── veritas_api_backend.py                   # Main API Backend
│   ├── veritas_api_backend_fixed.py             # Fixed API Backend
│   ├── veritas_api_backend_streaming.py         # Streaming API Backend
│   ├── veritas_api_core.py                      # API Core
│   ├── veritas_api_endpoint.py                  # Endpoint Management
│   ├── veritas_api_endpoint_conversation_manager.py # Conversation Management
│   ├── veritas_api_chunk_quality_endpoints.py   # Chunk Quality Endpoints
│   ├── veritas_api_quality_endpoints.py         # Quality Endpoints
│   ├── veritas_api_manager.py                   # API Manager
│   ├── veritas_api_manager_enhanced.py          # Enhanced API Manager
│   ├── veritas_api_integration_manager.py       # Integration Manager
│   ├── veritas_api_worker_integration.py        # Worker Integration
│   ├── veritas_api_reranking.py                 # Reranking API
│   ├── veritas_api_module.py                    # API Module
│   └── veritas_api_native.py                    # Native API
├── agents/                                      # Agent System
│   ├── veritas_agent_system_design.py          # Agent System Design
│   ├── veritas_api_agent_construction.py       # Agent Construction
│   ├── veritas_api_agent_core_components.py    # Agent Core Components
│   ├── veritas_api_agent_orchestrator.py       # Agent Orchestrator
│   ├── veritas_api_agent_environmental.py      # Environmental Agent
│   ├── veritas_api_agent_financial.py          # Financial Agent
│   ├── veritas_api_agent_registry.py           # Agent Registry
│   ├── veritas_api_agent_pipeline_manager.py   # Pipeline Manager
│   ├── veritas_api_agent_social.py             # Social Agent
│   └── veritas_api_agent_traffic.py            # Traffic Agent
└── services/                                   # Backend Services
    └── veritas_streaming_service.py            # Streaming Service
```

### 🔄 Shared (`shared/`)
Gemeinsame Komponenten und Utilities

```
shared/
├── core/                                    # Core Engine
│   └── veritas_core.py                     # Kern-Engine ohne GUI
├── utilities/                              # Utility Functions
│   ├── veritas_utility_text_to_speech.py  # Text-to-Speech Utility
│   ├── veritas_production_manager.py      # Production Management
│   └── veritas_installation_builder.py    # Installation Builder
└── pipelines/                             # Processing Pipelines
    ├── veritas_export_pipeline_final.py   # Export Pipeline
    ├── veritas_pipeline_summary.py        # Pipeline Summary
    ├── veritas_standard_pipeline_orchestrator.py # Pipeline Orchestrator
    ├── veritas_streaming_progress.py      # Streaming Progress
    └── veritas_relations_almanach.py      # Relations Almanach
```

### 🗄️ Database (`database/`)
Datenbank-Abstraktionsschicht (bestehend)

```
database/
├── __init__.py
├── database_api_*.py        # Verschiedene Datenbank-APIs
├── database_manager.py      # Datenbank Manager
└── adapter_governance.py    # Governance Adapter
```

### 🏗️ UDS3 (`uds3/`)
UDS3 System Module (bestehend)

```
uds3/
├── __init__.py
├── uds3_core.py            # UDS3 Core
├── uds3_api_backend.py     # UDS3 API Backend  
└── uds3_*.py              # Weitere UDS3 Module
```

### ⚙️ Configuration (`config/`)
Konfigurationsdateien

```
config/
└── config.py              # Hauptkonfiguration
```

### 🧪 Tests (`tests/`)
Test-Dateien und Test-Suites

```
tests/
├── veritas_api_backend_test.py     # API Backend Tests
└── veritas_app_streaming_test.py   # App Streaming Tests
```

### 📚 Documentation (`docs/`)
Dokumentation und Entwicklungsrichtlinien

```
docs/
├── veritas_kge_development_roadmap.py     # Development Roadmap
├── veritas_streaming_integration_guide.py # Integration Guide
├── VERITAS_API_BACKEND_DOCUMENTATION.md  # API Dokumentation
└── VERITAS_STREAMING_WITH_AGENTS.md      # Streaming & Agents Doku
```

### 💾 Data (`data/`)
Daten, Logs und Runtime-Dateien

```
data/
├── veritas_backend.sqlite     # SQLite Datenbank
└── veritas_auto_server.log   # Server Logs
```

## 🔧 Vorteile der neuen Struktur

### ✅ **Klare Trennung der Verantwortlichkeiten**
- **Frontend**: Alle UI und Client-Logik
- **Backend**: Server, API, Agents und Services
- **Shared**: Gemeinsame Utilities und Core-Funktionen

### ✅ **Bessere Wartbarkeit**
- Logische Gruppierung verwandter Dateien
- Einfachere Navigation und Code-Suche
- Klare Import-Pfade

### ✅ **Skalierbarkeit**
- Neue Features können leicht in die richtige Kategorie eingeordnet werden
- Team-Entwicklung wird durch klare Zuständigkeiten unterstützt
- Microservice-Architektur wird vorbereitet

### ✅ **Development Experience**
- Schnellerer Entwicklungszyklus durch bessere Organisation
- Weniger Merge-Konflikte durch getrennte Bereiche
- Einfachere Deployment-Strategien möglich

## � Wichtige Dokumentation (Stand: 12. Oktober 2025)

### v7.0 Supervisor Integration

**Dokumentation:**
- `SUPERVISOR_INTEGRATION_EXECUTIVE_SUMMARY.md` - Executive Summary (Quick Overview)
- `SUPERVISOR_INTEGRATION_COMPLETE.md` - Vollständige Implementation (800+ LOC)
- `SUPERVISOR_INTEGRATION_VALIDATION.md` - Validation Report (600+ LOC)
- `SUPERVISOR_INTEGRATION_QUICK_REFERENCE.md` - Quick Reference Card

**Status:** ✅ Implementation Complete (820 LOC in 4.5h)

**Key Features:**
- JSON-Driven Supervisor Layer (3 new phases: 1.5, 1.6, 6.5)
- Custom Executors (supervisor, agent_coordinator, llm)
- Dynamic Input Mapping (path-based context resolution)
- Intelligent Agent Selection (Construction, Weather, Financial)
- 9 phases total (6 scientific + 3 supervisor)

**Config:** `config/scientific_methods/default_method.json` (version 2.0.0)

**Orchestrator:** `backend/orchestration/unified_orchestrator_v7.py` (+450 LOC)

**Tests:**
- `tests/test_supervisor_config_validation.py` - Fast validation (✅ PASSED)
- `tests/test_unified_orchestrator_v7_real.py` - E2E test (⏸️ PENDING)

### v7.0 Phase Reports

**Phase Documentation:**
- `IMPLEMENTATION_GAP_ANALYSIS_TODO.md` - Implementation Plan
- `phase_4_3_orchestration_plan.md` - Phase 4.3 Plan
- `STATUS_REPORT.md` - Current Status

## �🚀 Import-Pfad Updates

Nach der Reorganisation müssen Import-Pfade in den Dateien aktualisiert werden:

```python
# Alte Imports:
from veritas_core import VeritasCore

# Neue Imports:
from shared.core.veritas_core import VeritasCore
```

## 📝 Backup

Ein vollständiges Backup wurde erstellt in:
`backup_20250928_114052/`

Alle ursprünglichen Dateien sind dort zur Sicherheit gespeichert.

---
*Erstellt am: 28. September 2025*  
*Letzte Aktualisierung: 12. Oktober 2025 (Supervisor Integration)*  
*VERITAS Projekt-Reorganisation v1.0*