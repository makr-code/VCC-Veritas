# VERITAS Backend Refactoring - Migration Checklist

**Version:** 4.0.0  
**Date:** 19. Oktober 2025  
**Status:** Phase 1 Complete ✅

---

## ✅ Phase 1: Neue Struktur erstellen (COMPLETE)

### Models
- [x] `backend/models/__init__.py` - Model Exports
- [x] `backend/models/enums.py` - Shared Enumerations (95 Zeilen)
- [x] `backend/models/request.py` - Request Models (180 Zeilen)
- [x] `backend/models/response.py` - UnifiedResponse + IEEE Citations (250 Zeilen)

### Services
- [x] `backend/services/query_service.py` - QueryService (350 Zeilen)
  - [x] `process_query()` - Main Entry Point
  - [x] `_normalize_sources()` - IEEE Normalization
  - [x] `_process_rag()` - RAG Processing
  - [x] `_process_hybrid()` - Hybrid Search
  - [x] `_process_streaming()` - Streaming
  - [x] `_process_agent()` - Agent Processing
  - [x] `_process_ask()` - Simple Ask
  - [x] `_generate_mock_response()` - Mock Fallback

### API (Flach - kein v3/)
- [x] `backend/api/__init__.py` - Router Export
- [x] `backend/api/query_router.py` - Query Endpoints (200 Zeilen)
  - [x] `POST /query` - Unified Query
  - [x] `POST /query/ask` - Simple Ask
  - [x] `POST /query/rag` - RAG Query
  - [x] `POST /query/hybrid` - Hybrid Search
  - [x] `POST /query/stream` - Streaming Query
- [x] `backend/api/agent_router.py` - Agent Endpoints (80 Zeilen)
  - [x] `GET /agent/list`
  - [x] `GET /agent/capabilities`
  - [x] `GET /agent/status/{id}`
- [x] `backend/api/system_router.py` - System Endpoints (140 Zeilen)
  - [x] `GET /system/health`
  - [x] `GET /system/info`
  - [x] `GET /system/capabilities`
  - [x] `GET /system/modes`

### Backend Core
- [x] `backend/app.py` - Konsolidiertes Backend (385 Zeilen)
  - [x] Logging Setup
  - [x] UDS3 v2.0.0 Integration
  - [x] Intelligent Pipeline Integration
  - [x] Streaming Integration
  - [x] QueryService Initialization
  - [x] FastAPI App mit Lifespan
  - [x] CORS Middleware
  - [x] API Router Mounting
  - [x] Root Endpoints
  - [x] Error Handlers

### Start Scripts
- [x] `start_backend.py` - Updated für `backend.app:app`

### Dokumentation
- [x] `docs/BACKEND_REFACTORING.md` - Migration Guide
- [x] `docs/QUICK_START.md` - Quick Start Guide
- [x] `docs/STRUCTURE_OVERVIEW.md` - Struktur-Übersicht
- [x] `docs/MIGRATION_CHECKLIST.md` - Diese Datei

### Code Quality
- [x] Syntax Check - Alle Dateien fehlerfrei
- [x] Import Paths - Korrekt
- [x] Type Hints - Wo sinnvoll vorhanden
- [x] Docstrings - Vorhanden

---

## ⏳ Phase 2: Testing (TODO)

### Backend Start
- [ ] Backend startet ohne Fehler
  ```powershell
  python start_backend.py
  # Oder: python backend/app.py
  ```
- [ ] Logs zeigen:
  - [ ] ✅ Startup successful
  - [ ] ✅ UDS3 initialized (oder Demo Mode)
  - [ ] ✅ Pipeline initialized (oder Demo Mode)
  - [ ] ✅ QueryService initialized
  - [ ] ✅ API mounted at /api
- [ ] Keine Exceptions beim Start

### Endpoint Tests

#### System Endpoints
- [ ] `GET /` - Root Endpoint
  ```bash
  curl http://localhost:5000/
  ```
  - [ ] Returns system info
  - [ ] Shows version 4.0.0
  - [ ] Lists features

- [ ] `GET /health` - Quick Health Check
  ```bash
  curl http://localhost:5000/health
  ```
  - [ ] Returns "healthy"
  - [ ] Shows component status

- [ ] `GET /api/system/health` - System Health
  ```bash
  curl http://localhost:5000/api/system/health
  ```
  - [ ] Returns detailed health
  - [ ] Shows UDS3/Pipeline/Streaming status

- [ ] `GET /api/system/info` - System Info
  ```bash
  curl http://localhost:5000/api/system/info
  ```
  - [ ] Returns API info
  - [ ] Shows version, modules, features

- [ ] `GET /api/system/capabilities` - Capabilities
  - [ ] Lists query modes
  - [ ] Lists features
  - [ ] Lists endpoints

- [ ] `GET /api/system/modes` - Available Modes
  - [ ] Shows mode descriptions
  - [ ] Lists mode features

#### Query Endpoints

- [ ] `POST /api/query` - Unified Query (RAG Mode)
  ```bash
  curl -X POST http://localhost:5000/api/query \
    -H "Content-Type: application/json" \
    -d '{"query": "Was regelt das BImSchG?", "mode": "rag", "model": "llama3.2"}'
  ```
  - [ ] Returns UnifiedResponse
  - [ ] Content contains Markdown
  - [ ] Sources have numeric IDs (1, 2, 3)
  - [ ] Sources have IEEE fields
  - [ ] Metadata shows mode="rag"

- [ ] `POST /api/query/rag` - RAG Query
  - [ ] Same as above

- [ ] `POST /api/query/ask` - Simple Ask
  ```bash
  curl -X POST http://localhost:5000/api/query/ask \
    -H "Content-Type: application/json" \
    -d '{"query": "Erkläre mir das BImSchG", "model": "llama3.2"}'
  ```
  - [ ] Returns UnifiedResponse
  - [ ] Metadata shows mode="ask"
  - [ ] Sources may be empty (ok for ask mode)

- [ ] `POST /api/query/hybrid` - Hybrid Search
  - [ ] Returns UnifiedResponse
  - [ ] Metadata shows mode="hybrid"
  - [ ] Metadata shows search_method

- [ ] `POST /api/query/stream` - Streaming
  - [ ] Returns UnifiedResponse (TODO: SSE)
  - [ ] Metadata shows mode="streaming"

#### Agent Endpoints

- [ ] `GET /api/agent/list` - Agent List
  - [ ] Returns list of agents

- [ ] `GET /api/agent/capabilities` - Capabilities
  - [ ] Returns capability list

- [ ] `GET /api/agent/status/{id}` - Agent Status
  - [ ] Returns agent status

### Response Validation

#### UnifiedResponse Structure
- [ ] `content` field present (string)
- [ ] `sources` field present (list)
- [ ] `metadata` field present (object)
- [ ] `session_id` field present (string)
- [ ] `timestamp` field present (ISO datetime)

#### IEEE Citations (Sources)
- [ ] Source `id` is numeric string ("1", "2", "3" NOT "src_1")
- [ ] Source `title` present
- [ ] Source `type` present
- [ ] Optional IEEE fields work:
  - [ ] `authors`
  - [ ] `ieee_citation`
  - [ ] `year`
  - [ ] `publisher`
  - [ ] `similarity_score`
  - [ ] `rerank_score`
  - [ ] `impact`
  - [ ] `relevance`
  - [ ] `rechtsgebiet`

#### Metadata Validation
- [ ] `model` field present
- [ ] `mode` field present and correct
- [ ] `duration` field present (number)
- [ ] `sources_count` matches len(sources)
- [ ] Optional fields work:
  - [ ] `agents_involved`
  - [ ] `complexity`
  - [ ] `domain`
  - [ ] `search_method`

### Mock Fallback
- [ ] Works when UDS3 not available
- [ ] Works when Pipeline not available
- [ ] Returns valid UnifiedResponse
- [ ] Mock sources have IEEE fields
- [ ] Mock sources have numeric IDs

---

## ⏳ Phase 3: Frontend Integration (TODO)

### Frontend Anpassung
- [ ] Update API Base URL zu `/api/query`
- [ ] Parse UnifiedResponse statt alte Formate
- [ ] Display IEEE Citations (35+ Felder)
- [ ] Show Citation tooltips mit allen Feldern
- [ ] Render Markdown content
- [ ] Parse [1], [2], [3] Citations
- [ ] Show metadata (model, duration, agents)

### UI Tests
- [ ] Query eingeben
- [ ] Response wird angezeigt
- [ ] Citations [1], [2], [3] sind klickbar
- [ ] Citation-Details zeigen:
  - [ ] IEEE Citation
  - [ ] Authors
  - [ ] Year, Publisher
  - [ ] Scores (similarity, rerank, quality)
  - [ ] Impact, Relevance
  - [ ] Rechtsgebiet
- [ ] Metadata wird angezeigt

---

## ⏳ Phase 4: Cleanup (TODO)

### Alte Dateien
- [ ] Backup erstellen:
  ```powershell
  $backup = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
  New-Item -ItemType Directory -Path $backup
  ```
- [ ] Alte Backend-Dateien verschieben:
  ```powershell
  Move-Item backend/api/veritas_api_backend.py $backup/
  Move-Item backend/api/veritas_api_backend_v3.py $backup/
  Move-Item backend/api/veritas_api_backend_streaming.py $backup/
  Move-Item backend/api/veritas_api_backend_fixed.py $backup/
  Move-Item backend/api/veritas_api_backend_pre_v3_*.py $backup/
  ```
- [ ] v3 Ordner verschieben (optional):
  ```powershell
  Move-Item backend/api/v3 $backup/api_v3
  ```

### Agent-Dateien umbenennen (optional)
- [ ] `veritas_api_agent_orchestrator.py` → `orchestrator.py`
- [ ] `veritas_api_agent_registry.py` → `registry.py`
- [ ] `veritas_intelligent_pipeline.py` → `pipeline.py`
- [ ] `veritas_api_agent_environmental.py` → `environmental.py`
- [ ] Imports anpassen in allen Dateien

### Services-Ordner ausbauen
- [ ] `backend/services/rag_service.py` - RAG Business Logic
- [ ] `backend/services/hybrid_search.py` - Hybrid Search Logic
- [ ] `backend/services/streaming_service.py` - Streaming Logic
- [ ] `backend/services/agent_service.py` - Agent Coordination

---

## ⏳ Phase 5: Production (TODO)

### Configuration
- [ ] Environment Variables dokumentieren
- [ ] Production CORS Origins konfigurieren
- [ ] Logging Level für Production
- [ ] Secret Management (API Keys)

### Database
- [ ] ChromaDB mit Dokumenten füllen
- [ ] UDS3 v2.0.0 konfigurieren
- [ ] Embeddings-Model konfigurieren
- [ ] Vector Index optimieren

### Monitoring
- [ ] Error Tracking einrichten
- [ ] Performance Metrics
- [ ] Health Check Monitoring
- [ ] Log Aggregation

### Deployment
- [ ] Docker Container
- [ ] docker-compose.yml
- [ ] Deployment Guide
- [ ] CI/CD Pipeline

---

## 📊 Progress Tracking

### Overall Progress
```
Phase 1: ████████████████████ 100% ✅ COMPLETE
Phase 2: ░░░░░░░░░░░░░░░░░░░░   0% ⏳ TODO
Phase 3: ░░░░░░░░░░░░░░░░░░░░   0% ⏳ TODO
Phase 4: ░░░░░░░░░░░░░░░░░░░░   0% ⏳ TODO
Phase 5: ░░░░░░░░░░░░░░░░░░░░   0% ⏳ TODO
```

### File Count
- ✅ Created: 13 neue Dateien
- ✅ Updated: 2 Dateien
- ⏳ To Remove: 5+ alte Backend-Dateien

### Line Count
- ✅ New Code: ~1500 Zeilen
- ✅ Models: ~525 Zeilen
- ✅ Services: ~350 Zeilen
- ✅ API: ~420 Zeilen
- ✅ Backend: ~385 Zeilen

---

## 🎯 Acceptance Criteria

- [x] Ein Backend statt 5
- [x] Ein Response-Model statt 4
- [x] Flache API-Struktur (kein v3/)
- [x] IEEE Citations (35+ Felder)
- [x] Keine Syntax-Errors
- [ ] Backend startet ohne Fehler
- [ ] Alle Endpoints funktionieren
- [ ] Frontend Integration erfolgreich
- [ ] Tests erfolgreich

---

## 🚀 Next Steps

**Jetzt sofort:**
1. Backend starten:
   ```powershell
   python start_backend.py
   ```

2. Health Check:
   ```powershell
   curl http://localhost:5000/api/system/health
   ```

3. Test Query:
   ```powershell
   curl -X POST http://localhost:5000/api/query \
     -H "Content-Type: application/json" \
     -d '{"query": "Was regelt das BImSchG?", "mode": "rag"}'
   ```

**Dokumentation:**
- `docs/QUICK_START.md` - Schnellstart-Anleitung
- `docs/STRUCTURE_OVERVIEW.md` - Struktur-Übersicht
- `docs/BACKEND_REFACTORING.md` - Migration Guide

---

**Status:** ✅ **Phase 1 Complete - Ready for Testing!**
