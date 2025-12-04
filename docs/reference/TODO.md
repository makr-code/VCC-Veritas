# VERITAS Entwicklungs-ToDo Liste 🚀

**Datum:** 28. September 2025
**Status:** Nach Projekt-Reorganisation
**Ziel:** Funktionale Wiederherstellung und Weiterentwicklung

---

## 🎯 **SOFORTIGE MASSNAHMEN (Kritisch)**

### ⚠️ **Phase 1: Import-Pfade reparieren**
**Status:** 🔴 Kritisch - Blockiert alle anderen Entwicklungen

#### Frontend Import-Fixes
- [ ] **`frontend/veritas_app.py`** *(3965 Zeilen - Hauptapplikation)*
  - `from veritas_core` → `from shared.core.veritas_core`
  - `from veritas_ui_components` → `from frontend.ui.veritas_ui_components`
  - `from veritas_ui_feedback_system` → `from frontend.ui.veritas_ui_feedback_system`
  - `from veritas_streaming_service` → `from backend.services.veritas_streaming_service`
  - **Externe Abhängigkeiten:** `uds3_*` und `database` bleiben unverändert

- [ ] **`frontend/ui/veritas_ui_feedback_system.py`**
  - `from veritas_ui_components` → `from frontend.ui.veritas_ui_components`

- [ ] **`frontend/ui/veritas_ui_toolbar.py`**
  - `from veritas_ui_components` → `from frontend.ui.veritas_ui_components`
  - `from veritas_forest_theme` → `from frontend.themes.veritas_forest_theme`
  - `from veritas_app` → `from frontend.veritas_app`

- [ ] **`frontend/streaming/veritas_frontend_streaming.py`** *(748 Zeilen)*
  - Interne Imports überprüfen und korrigieren

#### Backend Import-Fixes
- [ ] **`backend/api/veritas_api_backend.py`** *(817 Zeilen - Haupt-API)*
  - `from veritas_streaming_progress` → `from shared.pipelines.veritas_streaming_progress`

- [ ] **`backend/services/veritas_streaming_service.py`**
  - `from veritas_core` → `from shared.core.veritas_core`
  - `from veritas_streaming_progress` → `from shared.pipelines.veritas_streaming_progress`

- [ ] **`backend/api/veritas_api_backend_fixed.py`**
  - `from veritas_api_agent_*` → `from backend.agents.veritas_api_agent_*`

- [ ] **`backend/agents/veritas_api_agent_core_components.py`**
  - `from veritas_api_agent_registry` → `from backend.agents.veritas_api_agent_registry`
  - `from veritas_api_agent_pipeline_manager` → `from backend.agents.veritas_api_agent_pipeline_manager`
  - **Externe:** `database_api` und `uds3_core` bleiben unverändert

- [ ] **`backend/agents/veritas_api_agent_orchestrator.py`**
  - Agent-interne Imports korrigieren
  - **Externe:** `database_api` und `uds3_core` bleiben unverändert

#### Shared Import-Fixes
- [ ] **`shared/core/veritas_core.py`** *(773 Zeilen - Kern-Engine)*
  - Interne Dependencies überprüfen

---

## 🏗️ **Phase 2: Funktionale Wiederherstellung**

### **Frontend-Funktionalität** 🎨
**Priorität:** 🔴 Hoch

- [ ] **GUI-Komponenten testen**
  - [ ] `frontend/veritas_app.py` - Hauptapplikation starten
  - [ ] `frontend/ui/` - UI-Komponenten (Toolbar, StatusBar, Feedback)
  - [ ] `frontend/themes/veritas_forest_theme.py` - Theme-System
  - [ ] `frontend/streaming/` - Streaming-Integration

- [ ] **Frontend-Backend-Kommunikation**
  - [ ] API-Endpoints testen (`http://localhost:5000`)
  - [ ] Streaming-Verbindungen (SSE/WebSocket)
  - [ ] Session-Management

### **Backend-Funktionalität** ⚙️
**Priorität:** 🔴 Hoch

- [ ] **API-Services starten**
  - [ ] `backend/api/veritas_api_backend.py` - Haupt-API (Port 5000)
  - [ ] `backend/api/veritas_api_backend_streaming.py` - Streaming-API
  - [ ] FastAPI-Dokumentation (`/docs`) verfügbar machen

- [ ] **Agent-System**
  - [ ] `backend/agents/veritas_api_agent_orchestrator.py` - Agent-Koordination
  - [ ] Agent-Registry und Pipeline-Manager
  - [ ] Spezialisierte Agents (Environmental, Financial, Social, Traffic)

- [ ] **Services**
  - [ ] `backend/services/veritas_streaming_service.py` - Streaming-Service
  - [ ] Progress-Management und Real-time Updates

### **Core-System** 🔄
**Priorität:** 🔴 Hoch

- [ ] **Shared-Module**
  - [ ] `shared/core/veritas_core.py` - Kern-Engine ohne GUI
  - [ ] Thread-Management und Queue-System
  - [ ] Session-Management

- [ ] **Pipeline-System**
  - [ ] `shared/pipelines/` - Export, Standard, Streaming Pipelines
  - [ ] Progress-Tracking und Monitoring

---

## 🔗 **Phase 3: Externe Integrationen**
**Markiert als extern - Bestehende Funktionalität beibehalten**

### **UDS3-System** 🏛️ *(Extern)*
```
uds3/ (26 Module)
├── uds3_core.py                    # ✅ Kern-Funktionalität
├── uds3_security.py               # ✅ Sicherheits-Management
├── uds3_quality.py                # ✅ Qualitäts-Management
├── uds3_api_backend.py            # ✅ UDS3-API
└── ...weitere 22 Module
```
**Maßnahmen:**
- [ ] Import-Pfade für UDS3 NICHT ändern
- [ ] Bestehende `from uds3_*` Imports beibehalten
- [ ] UDS3 als externe Bibliothek behandeln

### **Database-Layer** 🗄️ *(Extern)*
```
database/ (21 APIs + Manager)
├── database_api.py                # ✅ Multi-Database-API
├── database_manager.py            # ✅ Database-Manager
├── database_api_*.py              # ✅ 15+ Datenbank-Adapter
└── adapter_governance.py          # ✅ Governance
```
**Maßnahmen:**
- [ ] Import-Pfade für Database NICHT ändern
- [ ] Bestehende `from database_*` Imports beibehalten
- [ ] Database als externe Bibliothek behandeln

---

## 🚀 **Phase 4: Multi-Agent-Pipeline mit Ollama LLM Integration**
**Priorität:** 🔴 Hoch - Intelligente Query-Verarbeitung

### **4.1 Multi-Agent Pipeline Architektur** 🎯
- [x] **Pipeline-Architektur analysieren** *(abgeschlossen)*
  - [x] AgentOrchestrator, AgentPipelineManager, AgentCoordinator analysiert
  - [x] Pipeline-Schemas (basic/standard/advanced) verstanden
  - [x] RAG-Integration-Punkte identifiziert
  - [x] 5 spezialisierte Agents verfügbar (Environmental, Financial, Social, Traffic, Technical Standards)

### **4.2 Ollama LLM Client Integration** 🤖
- [x] **Native Ollama Client entwickeln**
  - [x] Client für localhost:11434 implementieren
  - [x] Modell-Management (llama3.1:8b, llama3.1:8b-instruct, codellama:7b)
  - [x] Prompt-Templates für verschiedene Domänen
  - [x] Response-Generation-Pipeline erstellen
  - [x] Error-Handling und Retry-Logic (inkl. Offline-Fallback)

### **4.3 RAG-Agent-Pipeline-Orchestrierung** 🔄
- [ ] **Query-Pipeline erweitern**
  - [x] RAG-Ergebnisse (Vector, Graph, Relational) in Pipeline integrieren
  - [x] JSON-Schema-basierte Agent-Selektion basierend auf RAG-Kontext
  - [x] Dynamische Pipeline-Generierung implementieren ✅
  - [x] Agent-Prioritäts-System basierend auf Relevanz-Scores
  - [x] Manuelle Tests für RAG-Fallback & Prioritätsausführung (`tests/manual/test_rag_service_fallback.py`, `tests/manual/test_pipeline_execution_plan.py`)

### **4.4 Threading & Queue-Management** ⚡
- [x] **Parallel Agent-Execution optimieren**
  - [x] Thread-Pool für bis zu 5 parallele Agent-Threads (async Queue + `ThreadPoolExecutor` in `veritas_intelligent_pipeline.py`)
  - [x] Queue-basierte Task-Verteilung zwischen AgentPipelineManager und AgentCoordinator *(Pipeline-AgentQueue initialisiert; Tasks werden nach Priorität/Stage abgearbeitet)*
  - [x] Background-Processing für Long-Running-Agents (Timeout-Handling & Monitoring `timed_out_agents`)
  - [x] Thread-Safety für Agent-Ergebnis-Sammlung (RLock-geschützte Aggregation)

### **4.5 Agent-Ergebnis-Aggregation mit LLM** 🧠
- [x] **Multi-Agent-Synthesis entwickeln**
  - [x] Agent-Ergebnisse sammeln und normalisieren (`_normalize_agent_results`, Aggregations-Summary)
  - [x] Ollama LLM für kohärente Antwort-Generierung (Prompt erweitert um Aggregationsdaten)
  - [x] Confidence-Scoring basierend auf Agent-Konsensus (Blended Confidence, `agent_consensus`)
  - [x] Follow-up-Suggestions-Generation (dynamisch nach Key-Points & Confidence)
  - [x] Quellen-Referenzen und Metadaten-Integration (deduplizierte `source_references`, Combined Sources)
Okay
### **4.6 Pipeline-Monitoring & Metrics** 📊
- [ ] **Real-time Pipeline-Status**
  - [ ] Agent-Performance-Tracking (Response-Zeit, Erfolgsrate)
  - [ ] Query-Complexity-Metriken und Trend-Analyse
  - [ ] Pipeline-Visualization Dashboard
  - [ ] Debug-Informationen und Error-Logging

### **4.7 FastAPI Integration und Testing** 🔗
- [ ] **End-to-End Integration**
  - [ ] Multi-Agent-Pipeline in veritas_api_backend_fixed.py integrieren
  - [ ] `/v2/agents/pipeline` Endpoint implementieren
  - [ ] End-to-End Testing: Query → RAG → Agents → LLM → Response
  - [ ] Performance-Tests mit verschiedenen Query-Komplexitäten

---

## 🚀 **Phase 5: Code-Qualität & Advanced Features**

### **5.1 Code-Qualität & Testing** 🧪
- [ ] **Unit-Tests erweitern**
  - [ ] `tests/veritas_api_backend_test.py` - Backend-API Tests
  - [ ] `tests/veritas_app_streaming_test.py` - Streaming-Tests
  - [ ] Neue Tests für Frontend-Komponenten
  - [ ] Integration-Tests für Frontend-Backend-Kommunikation

- [ ] **Code-Review & Refactoring**
  - [ ] Import-Pfade optimieren
  - [ ] Unused Imports entfernen
  - [ ] Code-Duplikationen beseitigen

### **4.2 Architektur-Verbesserungen** 🏛️
- [ ] **Microservice-Vorbereitung**
  - [ ] Service-Discovery implementieren
  - [ ] API-Gateway für Service-Routing
  - [ ] Container-Ready machen (Docker)

- [ ] **Performance-Optimierung**
  - [ ] Async/Await-Patterns erweitern
  - [ ] Caching-Strategien implementieren
  - [ ] Database-Query-Optimierung

### **4.3 Neue Features** ⭐
- [ ] **Enhanced UI-Features**
  - [ ] Dark/Light Theme Toggle
  - [ ] Responsive Design
  - [ ] Keyboard-Shortcuts
  - [ ] Context-Menus

- [ ] **Advanced Agent-Capabilities**
  - [ ] Multi-Agent Collaboration
  - [ ] Agent Learning & Adaptation
  - [ ] External API Integrations

- [ ] **Monitoring & Analytics**
  - [ ] Performance Monitoring
  - [ ] User Analytics
  - [ ] Error Tracking & Reporting

### **4.4 Documentation & DevOps** 📚
- [ ] **Dokumentation**
  - [ ] API-Dokumentation aktualisieren
  - [ ] User-Guide erstellen
  - [ ] Developer-Setup-Guide
  - [ ] Architecture-Dokumentation

- [ ] **DevOps & CI/CD**
  - [ ] GitHub Actions/GitLab CI
  - [ ] Automated Testing
  - [ ] Deployment-Pipelines
  - [ ] Environment-Management

---

## 📊 **Prioritäten-Matrix**

### **Kritisch (Sofort)** 🔴
1. Import-Pfade reparieren (Blockiert alles andere)
2. Frontend-App zum Laufen bringen
3. Backend-API zum Laufen bringen
4. Basis-Funktionalität wiederherstellen

### **Hoch (Diese Woche)** 🟠
1. **Multi-Agent-Pipeline mit Ollama LLM** (Phase 4)
   - Ollama Client Integration
   - RAG-Agent-Pipeline-Orchestrierung
   - Threading & Queue-Management
2. Agent-System funktionsfähig machen
3. Streaming-Funktionalität testen
4. UI-Komponenten vollständig integrieren

### **Mittel (Nächste Woche)** 🟡
1. Agent-Ergebnis-Aggregation mit LLM
2. Pipeline-Monitoring & Metrics
3. FastAPI Integration und Testing
4. Code-Qualität verbessern
5. Performance optimieren

### **Niedrig (Langfristig)** 🟢
1. Microservice-Architektur
2. Advanced Analytics
3. Container-Deployment
4. CI/CD-Pipeline

---

## 🔧 **Entwickler-Aktionen**

### **Sofort starten:**
```bash
# 1. Multi-Agent-Pipeline entwickeln (Phase 4)
cd y:\veritas\backend\agents
# Ollama Client implementieren
# RAG-Pipeline erweitern
# Threading optimieren

# 2. Import-Pfade-Fix-Skript erstellen und ausführen
# 3. Frontend testen:
cd y:\veritas\frontend
python veritas_app.py

# 4. Backend testen:
cd y:\veritas\backend\api
python veritas_api_backend.py

# 5. Health-Check:
curl http://localhost:5000/health
```

### **Externe Dependencies beibehalten:**
- ✅ **UDS3:** `from uds3_*` Imports NICHT ändern
- ✅ **Database:** `from database_*` Imports NICHT ändern
- ⚠️ **Shared:** Alle internen `veritas_*` Imports anpassen

---

## 📈 **Erfolgs-Metriken**

### **Phase 1 Ziele:**
- [ ] 0 Import-Errors bei `python -m py_compile`
- [ ] Frontend startet ohne Crashes
- [ ] Backend-API antwortet auf `/health`
- [ ] Basic UI-Interaktion funktioniert

### **Phase 4 Ziele (Multi-Agent-Pipeline):**
- [ ] Ollama Client läuft auf localhost:11434
- [ ] RAG-basierte Agent-Selektion funktioniert
- [ ] Parallel Agent-Execution mit Thread-Pool
- [ ] LLM-basierte Response-Synthesis arbeitet
- [ ] Pipeline-Monitoring zeigt Real-time Metriken

### **Phase 5 Ziele:**
- [ ] Vollständige Frontend-Backend-Kommunikation
- [ ] Agent-System reagiert auf Queries
- [ ] Streaming-Features funktionieren
- [ ] User kann complex Multi-Agent-Queries ausführen

### **Langfristige Ziele:**
- [ ] <100ms API-Response-Time
- [ ] >95% Test-Coverage
- [ ] Multi-Agent-Pipeline <5s Response-Time
- [ ] Ollama LLM Integration >90% Erfolgsrate
- [ ] Container-Ready Architecture
- [ ] Microservice-Kompatibilität

---

**💡 Tipp:** Beginnen Sie mit Phase 4 - Multi-Agent-Pipeline! Die intelligente RAG-basierte Agent-Orchestrierung mit Ollama LLM Integration ist der nächste große Entwicklungssprung für VERITAS.

**🎯 Fokus:** Multi-Agent-Pipeline → RAG Integration → Ollama LLM → Threading → Monitoring → Testing

---

*Erstellt am: 28. September 2025*
*VERITAS ToDo v1.0 - Post-Reorganisation*
