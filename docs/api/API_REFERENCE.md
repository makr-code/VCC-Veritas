# API-Referenz

**Version:** 3.25.0
**Status:** ✅ Production Ready
**OpenAPI:** http://localhost:5000/docs

---

## 📋 Übersicht

VERITAS bietet eine **REST API** mit folgenden Haupt-Endpoints:

| Kategorie | Zweck | Base-Path |
|-----------|--------|-----------|
| **Query API** | Queries durchführen | `/api/query` |
| **Chat API** | Chat-Kommunikation | `/api/chat` |
| **Office API** | Word Add-In Integration | `/api/office` |
| **System API** | Health & Status | `/api/system` |
| **Admin API** | Administration | `/api/admin` |

---

## 🔍 Query API

### POST /api/query

Führe eine Recherche-Query durch.

**Request:**
```json
{
  "query": "Was wird in §15 BImSchG geregelt?",
  "mode": "ask",
  "session_id": "session-123",
  "context": {
    "domain": "environmental_law",
    "max_results": 5
  }
}
```

**Response:**
```json
{
  "status": "success",
  "query_id": "query-abc-123",
  "answer": "§15 BImSchG regelt...",
  "sources": [
    {
      "id": "doc-123",
      "title": "BImSchG §15",
      "snippet": "...",
      "relevance_score": 0.95,
      "url": "..."
    }
  ],
  "metadata": {
    "response_time_ms": 2450,
    "search_strategy": "hybrid",
    "document_count": 4
  }
}
```

**Parameter:**
- `query` (string, required) - Suchanfrage
- `mode` (string) - "ask", "search", "chat"
- `session_id` (string) - Session-Identifier
- `context` (object) - Zusätzlicher Kontext

---

## 💬 Chat API

### POST /api/chat

Starte oder setze Chat-Konversation fort.

**Request:**
```json
{
  "message": "Erkläre mir §15 BImSchG",
  "session_id": "session-123",
  "mode": "stream"
}
```

**Response (Streaming):**
```
data: {"type": "message", "content": "§15 regelt..."}
data: {"type": "source", "content": {"title": "BImSchG §15"}}
data: {"type": "complete"}
```

---

## 🏛️ Office API

### POST /api/office/query

Speziell für Word Add-In optimiert.

**Request:**
```json
{
  "query": "Was wird in §15 BImSchG geregelt?",
  "format": "inline",
  "include_sources": true
}
```

**Response:**
```json
{
  "content": "§15 regelt...",
  "sources": [
    {
      "title": "BImSchG §15",
      "page": 34,
      "section": "1"
    }
  ]
}
```

---

## 🏥 System API

### GET /api/system/health

System Health-Check.

**Response:**
```json
{
  "status": "healthy",
  "version": "3.25.0",
  "components": {
    "database": "connected",
    "search": "ready",
    "llm": "ready",
    "cache": "ready"
  },
  "uptime_seconds": 86400
}
```

### GET /api/system/capabilities

Verfügbare Funktionen abrufen.

**Response:**
```json
{
  "search_engines": ["vector", "keyword", "graph"],
  "languages": ["de", "en"],
  "features": {
    "streaming": true,
    "hypothesis_generation": true,
    "batch_search": true
  }
}
```

---

## 🔐 Authentifizierung

### JWT Token

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/query \
  -d '{"query": "..."}'
```

### Token Generation

```bash
# Bekomme einen Test-Token (für Development)
curl http://localhost:5000/api/auth/token \
  -d '{"username": "dev", "password": "dev"}'
```

---

## ⚠️ Error Handling

### Error Response
```json
{
  "status": "error",
  "code": "SEARCH_FAILED",
  "message": "ChromaDB connection failed",
  "details": {
    "error_type": "ConnectionError",
    "retry_after": 5
  }
}
```

### Common Errors

| Code | Status | Beschreibung |
|------|--------|-------------|
| `INVALID_QUERY` | 400 | Query ist ungültig |
| `SEARCH_FAILED` | 503 | Search Engine nicht verfügbar |
| `LLM_ERROR` | 503 | LLM nicht erreichbar |
| `UNAUTHORIZED` | 401 | Auth Token ungültig |
| `RATE_LIMITED` | 429 | Zu viele Requests |

---

## 📊 Pagination

```json
{
  "results": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 45,
    "has_next": true
  }
}
```

---

## 🔗 Rate Limiting

- **Default:** 100 Requests/Minute pro Token
- **Header:** `X-RateLimit-Remaining: 95`
- **Retry:** `Retry-After: 60` Sekunden

---

## 📚 Weiterführende Links

- **[OpenAPI Spec](http://localhost:5000/docs)** - Interaktive API-Dokumentation
- **[Endpoints](ENDPOINTS.md)** - Alle Endpoints im Detail
- **[Authentifizierung](AUTHENTICATION.md)** - Auth im Detail
- **[v3 API Docs](v3/OVERVIEW.md)** - API v3 Spezifika

---

**Möchtest du einen spezifischen Endpoint?** → Siehe [Endpoints](ENDPOINTS.md)
