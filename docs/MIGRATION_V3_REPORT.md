# VERITAS API v3 - Migration Report

**Date**: 18. October 2025 10:36:50  
**Status**: ✅ Migration Complete

---

## Migration Summary

### Legacy API Deactivation

**Deactivated Endpoints**: 19

#### Legacy Endpoints Removed:
1. `@app.get("/")`
2. `@app.get("/health")`
3. `@app.get("/capabilities")`
4. `@app.post("/v2/intelligent/query")`
5. `@app.get("/v2/intelligent/status")`
6. `@app.post("/v2/query/stream")`
7. `@app.get("/progress/{session_id}")`
8. `@app.post("/v2/query")`
9. `@app.post("/cancel/{session_id}")`
10. `@app.get("/progress/status/{session_id}")`
11. `@app.post("/ask", response_model=VeritasRAGResponse)`
12. `@app.post("/uds3/documents", response_model=UDS3SecureDocumentResponse)`
13. `@app.post("/uds3/query", response_model=UDS3QueryResponse)`
14. `@app.get("/uds3/status")`
15. `@app.post("/session/start", response_model=StartSessionResponse)`
16. `@app.get("/modes")`
17. `@app.get("/agents/types")`
18. `@app.post("/v2/hybrid/search")`
19. `@app.get("/get_models")`


---

### API v3 Activation

**New API Structure**: `/api/v3/*`

#### Active Routers (12):

**Phase 1 - Core (3 Router, 13 Endpoints)**:
- Query Router: 7 endpoints
- Agent Router: 4 endpoints  
- System Router: 5 endpoints

**Phase 2 - Domain (4 Router, 12 Endpoints)**:
- VPB Router: 3 endpoints
- COVINA Router: 3 endpoints
- PKI Router: 3 endpoints
- IMMI Router: 3 endpoints

**Phase 3 - Enterprise (3 Router, 18 Endpoints)**:
- SAGA Router: 6 endpoints
- Compliance Router: 6 endpoints
- Governance Router: 6 endpoints

**Phase 4 - UDS3 & User (2 Router, 15 Endpoints)**:
- UDS3 Router: 8 endpoints
- User Router: 7 endpoints

---

## Migration Steps

1. ✅ Backup erstellt (`veritas_api_backend_pre_v3_migration_*.py`)
2. ✅ Legacy-Endpoints deaktiviert
3. ✅ API v3 Router aktiviert
4. ✅ Backend neu gestartet
5. ⏳ Frontend-Migration pending

---

## Frontend Migration Guide

### Endpoint Mapping (Legacy → v3)

#### Core Queries:
```
OLD: POST /ask
NEW: POST /api/v3/query

OLD: POST /v2/query
NEW: POST /api/v3/query/execute

OLD: POST /v2/intelligent/query
NEW: POST /api/v3/query/execute (mode=veritas)
```

#### Domain Queries:
```
OLD: POST /vpb/query (if existed)
NEW: POST /api/v3/vpb/query

OLD: POST /covina/query (if existed)
NEW: POST /api/v3/covina/query
```

#### System:
```
OLD: GET /health
NEW: GET /api/v3/system/health

OLD: GET /capabilities
NEW: GET /api/v3/system/capabilities
```

#### UDS3:
```
OLD: POST /uds3/query
NEW: POST /api/v3/uds3/query

OLD: GET /uds3/status
NEW: GET /api/v3/uds3/stats
```

---

## Code Changes Required

### 1. Update API Base URL

```javascript
// OLD
const API_BASE = 'http://localhost:5000'

// NEW
const API_BASE = 'http://localhost:5000/api/v3'
```

### 2. Update Query Function

```javascript
// OLD
async function query(text) {{
    const response = await fetch('/ask', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ query: text }})
    }})
    return response.json()
}}

// NEW
async function query(text) {{
    const response = await fetch('/api/v3/query', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
            query_text: text,
            mode: 'veritas',
            session_id: null
        }})
    }})
    return response.json()
}}
```

### 3. Update Response Handling

```javascript
// OLD Response Structure
{{
    "response": "...",
    "sources": [...],
    "confidence": 0.95
}}

// NEW Response Structure
{{
    "content": "...",
    "sources": [...],
    "confidence": 0.95,
    "query_id": "query_abc123",
    "metadata": {{...}}
}}
```

---

## Testing Checklist

- [ ] Backend startet ohne Fehler
- [ ] `/api/v3/` Root-Endpoint erreichbar
- [ ] `/api/v3/query` funktioniert
- [ ] `/api/v3/system/health` funktioniert
- [ ] Domain-Endpoints (VPB, COVINA, etc.) funktionieren
- [ ] Frontend verbindet sich mit API v3
- [ ] Query-Funktionalität im Frontend funktioniert
- [ ] User Management funktioniert
- [ ] Preferences funktionieren

---

## Rollback Plan

Falls Probleme auftreten:

```powershell
# 1. Stop Backend
# Ctrl+C in Terminal

# 2. Restore Backup
cp backend/api/veritas_api_backend_pre_v3_migration_*.py backend/api/veritas_api_backend.py

# 3. Restart Backend
python start_backend.py
```

---

## Next Steps

1. ✅ Backend Migration complete
2. ⏳ Frontend Migration (update all API calls)
3. ⏳ Test complete workflow
4. ⏳ Deploy to production

---

**Migration Team**: VERITAS API v3  
**Status**: ✅ Backend Migration Complete  
**Date**: {datetime.now().strftime("%d. %B %Y")}
