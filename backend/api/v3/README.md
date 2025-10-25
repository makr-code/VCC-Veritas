# VERITAS API v3 - Enterprise REST API

**Version:** 3.0.0  
**Status:** Implementation (Phase 1 Complete)  
**Release Date:** 17. Oktober 2025

Enterprise-grade REST API mit modularer Struktur, konsistenten Conventions und umfassenden Features.

---

## 🚀 Quick Start

### Backend starten

```powershell
cd C:\VCC\veritas
python -m uvicorn backend.api.veritas_api_backend:app --host 0.0.0.0 --port 5000
```

### API Info abrufen

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/v3/
```

### OpenAPI Docs

Browser: `http://localhost:5000/docs`

---

## 📊 API Struktur

### Endpoint Groups (12 Module)

```
/api/v3/
├── query/          # Query Operations (3 endpoints)
├── agent/          # Agent Management (4 endpoints)
├── system/         # System Info (5 endpoints)
├── vpb/            # VPB Module (planned)
├── covina/         # COVINA Module (planned)
├── pki/            # PKI Module (planned)
├── immi/           # Immissionsschutz (planned)
├── saga/           # SAGA Orchestration (planned)
├── compliance/     # Compliance Checks (planned)
├── governance/     # Data Governance (planned)
├── uds3/           # Database Operations (planned)
└── user/           # User Management (planned)
```

---

## 📚 Endpoints (Phase 1)

### Query Operations

#### Standard Query
```http
POST /api/v3/query/standard
Content-Type: application/json

{
  "query": "Was sind die BImSchG Anforderungen für Windkraftanlagen?",
  "mode": "veritas",
  "model": "llama3.2",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response:**
```json
{
  "content": "Generated response...",
  "metadata": {
    "model": "llama3.2",
    "mode": "veritas",
    "duration": 2.45,
    "sources_count": 5,
    "sources_metadata": [...]
  },
  "session_id": "session_20251017_220500",
  "timestamp": "2025-10-17T22:05:00"
}
```

#### Streaming Query
```http
POST /api/v3/query/stream
Content-Type: application/json

{
  "query": "...",
  "mode": "veritas"
}
```

**Response (SSE):**
```
data: {"type": "token", "content": "Das "}
data: {"type": "token", "content": "BImSchG "}
data: {"type": "metadata", "data": {...}}
data: {"type": "done", "session_id": "..."}
```

#### Intelligent Query
```http
POST /api/v3/query/intelligent
Content-Type: application/json

{
  "query": "...",
  "mode": "veritas"
}
```

**Response:** Standard Response + `metadata.agents_involved`, `metadata.complexity`

---

### Agent Management

#### List Agents
```http
GET /api/v3/agent/list
```

**Response:**
```json
[
  {
    "agent_id": "environmental_agent",
    "name": "Environmental Agent",
    "description": "Spezialist für Umweltrecht und BImSchG",
    "capabilities": ["environmental_law", "emissions"],
    "status": "active",
    "version": "1.0.0"
  },
  ...
]
```

#### Get Agent Info
```http
GET /api/v3/agent/environmental_agent/info
```

#### Execute Agent
```http
POST /api/v3/agent/environmental_agent/execute
Content-Type: application/json

{
  "agent_id": "environmental_agent",
  "task": "Analysiere BImSchG §5 Anforderungen",
  "parameters": {"focus": "wind_turbines"},
  "timeout": 60
}
```

**Response:**
```json
{
  "agent_id": "environmental_agent",
  "result": {
    "task": "...",
    "output": "...",
    "parameters": {...}
  },
  "status": "completed",
  "duration": 3.42,
  "timestamp": "2025-10-17T22:05:00"
}
```

#### Get Agent Capabilities
```http
GET /api/v3/agent/capabilities
```

---

### System Information

#### Health Check
```http
GET /api/v3/system/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-17T22:05:00",
  "services": {
    "uds3": true,
    "intelligent_pipeline": true,
    "ollama": true,
    "streaming": true
  },
  "uptime": 1234.56
}
```

**Status Levels:**
- `healthy` - Alle Services verfügbar
- `degraded` - Einige Services unavailable
- `unhealthy` - Critical Services unavailable

#### System Capabilities
```http
GET /api/v3/system/capabilities
```

**Response:**
```json
{
  "version": "3.0.0",
  "endpoints": [...],
  "features": {
    "streaming_available": true,
    "intelligent_pipeline_available": true,
    "uds3_available": true,
    "ollama_available": true,
    "rag_available": true
  },
  "models": ["llama3.2:latest", "llama3.1:8b", ...],
  "agents": ["environmental_agent", ...]
}
```

#### Available Modes
```http
GET /api/v3/system/modes
```

**Response:**
```json
{
  "success": true,
  "data": {
    "modes": {
      "veritas": {
        "display_name": "Standard RAG",
        "endpoints": ["/api/v3/query/standard"],
        "status": "implemented"
      },
      ...
    }
  }
}
```

#### Available Models
```http
GET /api/v3/system/models
```

#### System Metrics
```http
GET /api/v3/system/metrics
```

**Response:**
```json
{
  "requests_total": 1542,
  "requests_per_second": 12.34,
  "average_latency": 245.67,
  "error_rate": 0.0012,
  "uptime": 86400.0,
  "timestamp": "2025-10-17T22:05:00"
}
```

---

## 🔧 Request/Response Patterns

### Standard Success Response
```json
{
  "success": true,
  "message": "...",
  "data": {...},
  "timestamp": "2025-10-17T22:05:00"
}
```

### Standard Error Response
```json
{
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "details": {...},
  "timestamp": "2025-10-17T22:05:00"
}
```

### HTTP Status Codes
- `200 OK` - Success
- `400 Bad Request` - Invalid request
- `404 Not Found` - Resource not found
- `408 Request Timeout` - Operation timeout
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service unavailable

---

## 📦 Pydantic Models

### Import Models
```python
from backend.api.v3.models import (
    # Query
    QueryRequest, QueryResponse, QueryMetadata, SourceMetadata,
    # Agent
    AgentInfo, AgentExecuteRequest, AgentExecuteResponse,
    # System
    SystemHealth, SystemCapabilities, SystemMetrics,
    # Base
    StatusEnum, ErrorResponse, SuccessResponse
)
```

### Example Usage
```python
from backend.api.v3.models import QueryRequest

query_req = QueryRequest(
    query="Test Query",
    mode="veritas",
    model="llama3.2",
    temperature=0.7,
    max_tokens=2000
)

# Validation erfolgt automatisch
print(query_req.model)  # "llama3.2"
print(query_req.dict())  # {"query": "...", "mode": "...", ...}
```

---

## 🧪 Testing

### Integration Test
```powershell
python backend\api\v3\test_integration.py
```

### Live Endpoint Tests
```powershell
# API Info
Invoke-RestMethod http://127.0.0.1:5000/api/v3/ | ConvertTo-Json -Depth 3

# System Health
Invoke-RestMethod http://127.0.0.1:5000/api/v3/system/health | ConvertTo-Json

# Agent List
Invoke-RestMethod http://127.0.0.1:5000/api/v3/agent/list | ConvertTo-Json -Depth 3

# System Modes
Invoke-RestMethod http://127.0.0.1:5000/api/v3/system/modes | ConvertTo-Json -Depth 4
```

---

## 📁 File Structure

```
backend/api/v3/
├── __init__.py              # Base Router, Version Info
├── models.py                # Pydantic Models (25 models)
├── query_router.py          # Query Operations (3 endpoints)
├── agent_router.py          # Agent Management (4 endpoints)
├── system_router.py         # System Info (5 endpoints)
└── test_integration.py      # Integration Tests
```

---

## 🚧 Roadmap

### Phase 1 (Complete) ✅
- [x] Backend Struktur
- [x] Pydantic Models
- [x] Query Router
- [x] Agent Router
- [x] System Router
- [x] Integration in Backend
- [x] Tests

### Phase 2 (Woche 2)
- [ ] VPB Router
- [ ] COVINA Router
- [ ] PKI Router
- [ ] IMMI Router

### Phase 3 (Woche 2-3)
- [ ] SAGA Router
- [ ] Compliance Router
- [ ] Governance Router

### Phase 4 (Woche 3)
- [ ] UDS3 Router
- [ ] User Router

### Phase 5 (Woche 4)
- [ ] Unit Tests (>80%)
- [ ] Integration Tests
- [ ] Performance Tests
- [ ] OpenAPI/Swagger Docs
- [ ] Migration Guide
- [ ] Frontend Integration

---

## 📖 Documentation

- **API Consolidation Proposal:** `docs/API_CONSOLIDATION_PROPOSAL.md`
- **Endpoint Overview:** `docs/API_V3_ENDPOINT_OVERVIEW.md`
- **Phase 1 Complete:** `docs/API_V3_PHASE1_COMPLETE.md`
- **OpenAPI Docs:** `http://localhost:5000/docs` (live)

---

## 🤝 Contributing

### Adding New Endpoints

1. **Create Router:**
   ```python
   # backend/api/v3/my_router.py
   from fastapi import APIRouter
   
   my_router = APIRouter(prefix="/my_module", tags=["My Module"])
   
   @my_router.get("/")
   async def get_my_data():
       return {"data": "..."}
   ```

2. **Add Models (if needed):**
   ```python
   # backend/api/v3/models.py
   class MyRequest(BaseModel):
       field: str = Field(..., description="...")
   ```

3. **Integrate Router:**
   ```python
   # backend/api/veritas_api_backend.py
   from backend.api.v3.my_router import my_router
   app.include_router(my_router, prefix="/api/v3")
   ```

4. **Test:**
   ```powershell
   Invoke-RestMethod http://127.0.0.1:5000/api/v3/my_module/
   ```

---

## 📞 Support

- **Issues:** GitHub Issues
- **Docs:** `docs/API_*.md`
- **Logs:** `data/backend_debug.log`, `logs/backend_uvicorn.log`

---

**Version:** 3.0.0 | **Status:** Phase 1 Complete ✅ | **Date:** 17. Oktober 2025
