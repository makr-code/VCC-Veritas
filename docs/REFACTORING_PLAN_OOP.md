# VERITAS OOP Refactoring Plan

**Datum**: 2025-12-03
**Ziel**: Refaktorierung der Backend-Struktur nach OOP Best Practices
**Status**: 🔄 In Bearbeitung

---

## 🎯 Zielsetzung

Reorganisation des VERITAS Backends in eine klare, wartbare OOP-Struktur:

```
backend/
├── core/              # Kern-Funktionalität (Business Logic)
├── agents/            # Agent-System (spezialisierte Agenten)
├── adapters/          # Externe Integrationen (UDS3, ThemisDB, APIs)
├── helpers/           # Utility-Funktionen, Tools
├── models/            # Data Models, Schemas
├── services/          # Service Layer (Orchestration, Processing)
├── api/               # REST API Endpoints
└── database/          # Datenbank-Layer
```

---

## 📋 Aktuelle Probleme

1. ✅ **52 Backup-Dateien** (.bak, .bak1, .bak2, _old) - Müssen gelöscht werden
2. ✅ **Unstrukturierte agents/** - Viele Test-Dateien, keine klare Struktur
3. ✅ **Redundante Dokumentation** - Veraltete/duplizierte Docs
4. ✅ **Keine klare Trennung** - Core/Helpers/Adapters vermischt

---

## 🏗️ Neue Struktur

### 1. **core/** - Kern-Business-Logic

**Inhalt**:
- `orchestration/` - UnifiedOrchestratorV7, OrchestrationController
- `pipeline/` - IntelligentPipeline, PipelineFactory
- `retrieval/` - RAG, Hybrid Search, Query Expansion
- `llm/` - LLM Client Abstractions (Ollama, VLLM)
- `embeddings/` - Embedding Providers
- `reranking/` - Reranking Service

**Dateien (aus backend/agents/):**
- `veritas_intelligent_pipeline.py` → `core/pipeline/intelligent_pipeline.py`
- `veritas_pipeline_factory.py` → `core/pipeline/factory.py`
- `veritas_hybrid_retrieval.py` → `core/retrieval/hybrid.py`
- `veritas_query_expansion.py` → `core/retrieval/query_expansion.py`
- `veritas_reciprocal_rank_fusion.py` → `core/retrieval/rrf.py`
- `veritas_reranking_service.py` → `core/reranking/service.py`
- `veritas_ollama_client.py` → `core/llm/ollama_client.py`
- `veritas_vllm_client.py` → `core/llm/vllm_client.py`
- `veritas_llm_factory.py` → `core/llm/factory.py`

**Dateien (aus backend/orchestration/):**
- `unified_orchestrator_v7.py` → `core/orchestration/unified_orchestrator_v7.py`

---

### 2. **agents/** - Agent-System (Spezialisierte Agenten)

**Struktur**:
```
agents/
├── framework/                    # Agent Framework (bereits gut strukturiert)
│   ├── base_agent.py
│   ├── orchestration_controller.py
│   ├── consolidated_cost_framework.py
│   └── ...
├── themisdb/                     # ThemisDB RAG Agent (bereits gut strukturiert)
│   ├── base.py
│   ├── adapters.py
│   ├── implementations.py
│   ├── rag_agent.py
│   ├── execution_plan_analysis.py
│   └── agent_framework_integration.py
├── domain/                       # Domain-spezifische Agenten
│   ├── construction/
│   │   └── construction_agent.py
│   ├── environmental/
│   │   └── environmental_agent.py
│   ├── financial/
│   │   └── financial_agent.py
│   ├── weather/
│   │   ├── dwd_weather_agent.py
│   │   └── brightsky_weather_agent.py
│   ├── chemical/
│   │   └── chemical_data_agent.py
│   ├── standards/
│   │   └── technical_standards_agent.py
│   ├── wikipedia/
│   │   └── wikipedia_agent.py
│   ├── social/
│   │   └── social_agent.py
│   └── traffic/
│       └── traffic_agent.py
├── registry/                     # Agent Registry System
│   ├── agent_registry.py
│   └── registry_adapter.py
├── orchestrator/                 # Agent Orchestrator
│   ├── agent_orchestrator.py
│   └── pipeline_manager.py
├── supervisor/                   # Supervisor Agent
│   ├── supervisor_agent.py
│   └── supervisor_extensions.py
└── specialized/                  # Spezialisierte Agenten (Immissionsschutz, etc.)
    ├── immissionsschutz/
    │   ├── orchestrator.py
    │   └── testserver_extension.py
    └── database/
        └── testserver_extension.py
```

**Dateien zu verschieben**:
- `veritas_api_agent_*.py` → `agents/domain/*/`
- `agent_registry.py` → `agents/registry/`
- `veritas_api_agent_orchestrator.py` → `agents/orchestrator/`
- `veritas_supervisor_agent.py` → `agents/supervisor/`

**Dateien zu löschen** (Backups):
- `*.bak`, `*.bak1`, `*.bak2`
- `veritas_uds3_hybrid_agent_old.py.bak`

---

### 3. **adapters/** - Externe Integrationen

**Struktur**:
```
adapters/
├── uds3/                         # UDS3 Integration (bereits vorhanden)
│   ├── uds3_adapter.py
│   ├── uds3_hybrid_agent.py
│   └── uds3_hybrid_agent_v2.py
├── themisdb/                     # ThemisDB Adapter (bereits in agents/themisdb/)
│   └── (Symlink zu agents/themisdb/)
├── environmental/                # Environmental APIs
│   └── environmental_adapter.py
└── external_apis/                # Andere externe APIs
    └── ...
```

**Dateien zu verschieben**:
- `backend/adapters/` → Bleiben, sind bereits gut strukturiert
- `veritas_uds3_adapter.py` → `adapters/uds3/` (von agents/)
- `environmental_agent_adapter.py` → `adapters/environmental/`

---

### 4. **helpers/** - Utility-Funktionen

**Struktur**:
```
helpers/
├── context/                      # Context Management
│   └── context_manager.py
├── prompts/                      # Prompt Engineering
│   └── enhanced_prompts.py
├── formatting/                   # Formatierung
│   ├── citation_formatter.py
│   ├── rich_media_schema.py
│   └── sparse_retrieval.py
├── messaging/                    # Message Broker
│   ├── message_broker.py
│   └── message_broker_enhanced.py
└── generation/                   # Code/Template Generation
    └── agent_generator.py
```

**Dateien zu verschieben**:
- `context_manager.py` → `helpers/context/`
- `veritas_enhanced_prompts.py` → `helpers/prompts/`
- `veritas_json_citation_formatter.py` → `helpers/formatting/`
- `veritas_rich_media_schema.py` → `helpers/formatting/`
- `veritas_sparse_retrieval.py` → `helpers/formatting/`
- `agent_message_broker.py` → `helpers/messaging/`
- `agent_generator.py` → `helpers/generation/`

---

### 5. **services/** - Service Layer

**Struktur**:
```
services/
├── rag/                          # RAG Services
│   └── rag_context_service.py
└── ...
```

**Dateien zu verschieben**:
- `rag_context_service.py` → `services/rag/`

---

### 6. **models/** - Data Models (bereits vorhanden)

**Bereits gut strukturiert** - Keine Änderungen nötig

---

### 7. **api/** - REST API (bereits vorhanden)

**Bereits gut strukturiert** - Keine Änderungen nötig

---

### 8. **database/** - Datenbank-Layer (bereits vorhanden)

**Bereits gut strukturiert** - Keine Änderungen nötig

---

## 🗑️ Zu löschende Dateien

### Backup-Dateien in backend/agents/:
- `agent_generator.py.bak1`
- `agent_message_broker.py.bak1`
- `agent_registry.py.bak1`
- `database_agent_testserver_extension.py.bak1`
- `environmental_agent_adapter.py.bak1`
- `test_agent_testserver_integration.py.bak1`
- `test_dual_prompt_system.py.bak1`
- `test_integration_e2e.py.bak1`
- `test_monitoring_integration.py.bak1`
- `test_orchestration_integration.py.bak1`
- `test_quality_gate_integration.py.bak1`
- `test_streaming_integration.py.bak1`
- `test_technical_standards_agent_standalone.py.bak1`
- `test_template_standalone.py.bak1`
- `veritas_agent_system_design.py.bak1`
- `veritas_agent_template.py.bak`
- `veritas_agent_template.py.bak1`
- `veritas_api_agent_core_components.py.bak`
- `veritas_api_agent_core_components.py.bak1`
- `veritas_api_agent_environmental.py.bak`
- `veritas_api_agent_environmental.py.bak1`
- `veritas_api_agent_immissionschutz.py.bak2`
- `veritas_api_agent_registry.py.bak`
- `veritas_api_agent_registry.py.bak1`
- `veritas_uds3_hybrid_agent_old.py.bak`

**Gesamt**: ~26 Backup-Dateien in agents/

### Test-Dateien (zu verschieben nach tests/):
- Alle `test_*.py` Dateien aus `backend/agents/` → `tests/agents/`

---

## 📚 Dokumentation - Konsolidierung

### Zu löschen (veraltet/redundant):
1. Alle `archive/deprecated-features/` Docs (bereits archiviert)
2. Mehrfach-Versionen:
   - `QUICK_START*.md` → Nur `QUICK_START.md` behalten
   - `PHASE_*_*.md` → Konsolidieren in `DEPLOYMENT_HISTORY.md`
   - Multiple `API_V3_PHASE*.md` → Nur `API_V3_COMPLETE.md` behalten
3. Session-Reports (alt):
   - `SESSION_SUMMARY*.md`
   - `TEST_SESSION_REPORT*.md`

### Zu konsolidieren:
1. **Agent Docs**:
   - `AGENT_FRAMEWORK_QUICKSTART.md` (behalten)
   - `AGENT_INTEGRATION_ANALYSIS.md` (behalten)
   - `AGENT_SYSTEM_ANALYSIS_REPORT.md` (behalten)
   - Neue: `AGENT_FRAMEWORK_OOP_GUIDE.md` (erstellen)

2. **ThemisDB Docs**:
   - `THEMISDB_AQL_AGENT_STRATEGIE.md` (behalten)
   - `THEMISDB_OOP_IMPLEMENTATION_SUMMARY.md` (behalten)
   - `CONSOLIDATED_AGENT_SYSTEM_DOCUMENTATION.md` (behalten)

3. **Execution Plan Docs**:
   - `POLYGLOT_EXECUTION_PLAN_ANALYSIS.md` (behalten)
   - `POLYGLOT_EXECUTION_PLAN_IMPLEMENTATION.md` (behalten)
   - `POLYGLOT_SYSTEM_ARCHITECTURE.md` (behalten)

---

## 🔄 Migration Plan

### Phase 1: Backup-Dateien löschen ✅
```bash
# Löschen aller .bak, .bak1, .bak2 Dateien
find backend/agents -name "*.bak*" -delete
```

### Phase 2: Core-Struktur erstellen
1. Erstelle `backend/core/` Verzeichnisse
2. Verschiebe Orchestration/Pipeline/LLM Dateien
3. Update Imports

### Phase 3: Agents reorganisieren
1. Erstelle `backend/agents/domain/` Struktur
2. Verschiebe Domain-Agenten
3. Update Imports

### Phase 4: Adapters konsolidieren
1. Erstelle `backend/adapters/` Struktur
2. Verschiebe Adapter-Dateien
3. Update Imports

### Phase 5: Helpers erstellen
1. Erstelle `backend/helpers/` Struktur
2. Verschiebe Utility-Dateien
3. Update Imports

### Phase 6: Tests verschieben
1. Verschiebe Test-Dateien nach `tests/`
2. Update Test-Imports

### Phase 7: Dokumentation konsolidieren
1. Lösche veraltete Docs
2. Erstelle neue OOP-Guides
3. Update README

---

## ✅ Erfolgskriterien

1. ✅ Klare OOP-Struktur (core, agents, adapters, helpers)
2. ✅ Keine Backup-Dateien mehr
3. ✅ Alle Imports funktionieren
4. ✅ Tests laufen erfolgreich
5. ✅ Dokumentation aktualisiert
6. ✅ Bessere Wartbarkeit

---

## 📝 Nächste Schritte

1. Review dieser Plan mit Team
2. Phase 1 ausführen (Backup-Dateien löschen)
3. Phase 2-6 schrittweise ausführen
4. Nach jeder Phase: Tests laufen lassen
5. Finale Dokumentation

