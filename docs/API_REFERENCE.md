# VERITAS API Reference

**Version:** 1.0.0  
**Last Updated:** 2025-10-08  
**Base URL:** `https://api.veritas.example.com`

---

## Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [Agent Execution Endpoints](#agent-execution-endpoints)
3. [RAG (Retrieval-Augmented Generation)](#rag-endpoints)
4. [Quality Management](#quality-management-endpoints)
5. [Monitoring & Health](#monitoring--health-endpoints)
6. [Worker Management](#worker-management-endpoints)
7. [System Administration](#system-administration-endpoints)
8. [Common Response Codes](#common-response-codes)
9. [Error Handling](#error-handling)

---

## Authentication Endpoints

All authentication endpoints require HTTPS and return JWT tokens or API keys.

### POST /auth/login

Authenticate user and receive JWT tokens.

**Request:**
```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your-password"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "username": "user@example.com",
    "role": "user",
    "permissions": ["read", "write", "agents:execute"]
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

### POST /auth/refresh

Refresh access token using refresh token.

**Request:**
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired refresh token
- `400 Bad Request`: Missing refresh token

---

### POST /auth/logout

Logout and invalidate tokens.

**Request:**
```http
POST /auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out",
  "timestamp": "2025-10-08T14:30:00Z"
}
```

---

### GET /auth/me

Get current user information.

**Request:**
```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "id": "user_123",
  "username": "user@example.com",
  "email": "user@example.com",
  "role": "user",
  "permissions": ["read", "write", "agents:execute"],
  "created_at": "2025-01-01T00:00:00Z",
  "last_login": "2025-10-08T14:30:00Z"
}
```

---

### POST /auth/api-keys

Create new API key.

**Request:**
```http
POST /auth/api-keys
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Production Server",
  "description": "API key for production backend",
  "permissions": ["read", "write", "agents:execute"],
  "expires_in_days": 365
}
```

**Response (201 Created):**
```json
{
  "api_key": "vrt_live_abc123xyz789...",
  "key_id": "key_001",
  "name": "Production Server",
  "permissions": ["read", "write", "agents:execute"],
  "created_at": "2025-10-08T14:30:00Z",
  "expires_at": "2026-10-08T14:30:00Z"
}
```

⚠️ **Warning:** API key is only shown once!

---

### GET /auth/api-keys

List all API keys for current user.

**Request:**
```http
GET /auth/api-keys
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "api_keys": [
    {
      "key_id": "key_001",
      "name": "Production Server",
      "permissions": ["read", "write", "agents:execute"],
      "created_at": "2025-10-08T14:30:00Z",
      "expires_at": "2026-10-08T14:30:00Z",
      "last_used": "2025-10-08T15:45:00Z"
    }
  ],
  "total": 1
}
```

---

### DELETE /auth/api-keys/{key_id}

Revoke API key.

**Request:**
```http
DELETE /auth/api-keys/key_001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "message": "API key revoked successfully",
  "key_id": "key_001"
}
```

---

## Agent Execution Endpoints

Execute and manage multi-agent orchestration plans.

### POST /agents/execute

Execute agent orchestration plan.

**Request:**
```http
POST /agents/execute
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "plan_id": "plan_001",
  "agents": ["financial", "environmental", "social"],
  "query": "Analyze sustainability impact of renewable energy",
  "context": {
    "company": "Green Energy Corp",
    "year": 2025
  },
  "streaming": false,
  "quality_gates": {
    "min_score": 0.7,
    "require_review": false
  }
}
```

**Parameters:**
- `plan_id` (string, required): Unique plan identifier
- `agents` (array, required): List of agent types to execute
- `query` (string, required): User query or task description
- `context` (object, optional): Additional context
- `streaming` (boolean, optional): Enable WebSocket streaming (default: false)
- `quality_gates` (object, optional): Quality gate configuration

**Response (202 Accepted):**
```json
{
  "plan_id": "plan_001",
  "status": "pending",
  "agents": ["financial", "environmental", "social"],
  "created_at": "2025-10-08T14:30:00Z",
  "estimated_duration": 15.0,
  "websocket_url": "wss://api.veritas.example.com/api/v1/streaming/ws/client_123?plan_id=plan_001"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Insufficient permissions
- `422 Unprocessable Entity`: Validation error

---

### GET /agents/status/{plan_id}

Get execution status of plan.

**Request:**
```http
GET /agents/status/plan_001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "plan_id": "plan_001",
  "status": "running",
  "progress": 0.65,
  "agents": [
    {
      "agent_id": "fin_001",
      "agent_type": "financial",
      "status": "completed",
      "quality_score": 0.89
    },
    {
      "agent_id": "env_001",
      "agent_type": "environmental",
      "status": "running",
      "progress": 0.45
    },
    {
      "agent_id": "soc_001",
      "agent_type": "social",
      "status": "pending"
    }
  ],
  "created_at": "2025-10-08T14:30:00Z",
  "updated_at": "2025-10-08T14:30:10Z"
}
```

**Status Values:**
- `pending`: Not started
- `running`: Currently executing
- `completed`: Successfully completed
- `failed`: Execution failed
- `cancelled`: Manually cancelled

---

### GET /agents/result/{plan_id}

Get execution result.

**Request:**
```http
GET /agents/result/plan_001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "plan_id": "plan_001",
  "status": "completed",
  "result": {
    "summary": "Comprehensive sustainability analysis",
    "findings": {
      "financial": {"roi": 0.15, "risk": "moderate"},
      "environmental": {"carbon_reduction": 45000, "score": 0.92},
      "social": {"jobs_created": 150, "impact": 0.88}
    },
    "recommendations": [
      "Prioritize solar investments",
      "Engage local communities early"
    ]
  },
  "quality_score": 0.86,
  "execution_time": 12.45,
  "created_at": "2025-10-08T14:30:00Z",
  "completed_at": "2025-10-08T14:30:12Z"
}
```

**Error Responses:**
- `404 Not Found`: Plan not found
- `409 Conflict`: Plan not yet completed

---

### DELETE /agents/cancel/{plan_id}

Cancel running execution.

**Request:**
```http
DELETE /agents/cancel/plan_001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "plan_id": "plan_001",
  "status": "cancelled",
  "message": "Execution cancelled successfully"
}
```

---

### GET /agents/list

List all agent executions.

**Request:**
```http
GET /agents/list?status=completed&limit=10&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**
- `status` (string, optional): Filter by status (pending, running, completed, failed, cancelled)
- `limit` (integer, optional): Number of results (default: 20, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response (200 OK):**
```json
{
  "executions": [
    {
      "plan_id": "plan_001",
      "status": "completed",
      "quality_score": 0.86,
      "created_at": "2025-10-08T14:30:00Z",
      "completed_at": "2025-10-08T14:30:12Z"
    }
  ],
  "total": 45,
  "limit": 10,
  "offset": 0
}
```

---

## RAG Endpoints

Retrieval-Augmented Generation for context-aware queries.

### POST /rag/ask

Query RAG system with context retrieval.

**Request:**
```http
POST /rag/ask
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "question": "What are the key sustainability metrics?",
  "context": {
    "domain": "environmental",
    "timeframe": "2025"
  },
  "top_k": 5,
  "rerank": true,
  "include_sources": true
}
```

**Parameters:**
- `question` (string, required): User question
- `context` (object, optional): Additional context
- `top_k` (integer, optional): Number of chunks to retrieve (default: 5)
- `rerank` (boolean, optional): Apply reranking (default: true)
- `include_sources` (boolean, optional): Include source documents (default: true)

**Response (200 OK):**
```json
{
  "answer": "Key sustainability metrics include carbon emissions, water usage, waste reduction, and renewable energy adoption...",
  "sources": [
    {
      "chunk_id": "chunk_001",
      "text": "Carbon emissions are measured in...",
      "score": 0.92,
      "source": "sustainability_guide.pdf",
      "page": 12
    }
  ],
  "confidence": 0.89,
  "processing_time": 1.23
}
```

---

### POST /rag/embed

Generate embeddings for text.

**Request:**
```http
POST /rag/embed
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "texts": [
    "Sustainability metrics",
    "Carbon emissions tracking"
  ],
  "model": "nomic-embed-text"
}
```

**Response (200 OK):**
```json
{
  "embeddings": [
    [0.123, -0.456, 0.789, ...],
    [0.234, -0.567, 0.890, ...]
  ],
  "dimension": 768,
  "model": "nomic-embed-text"
}
```

---

### POST /rag/search

Search documents without answer generation.

**Request:**
```http
POST /rag/search
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "query": "carbon emissions",
  "top_k": 10,
  "filters": {
    "source": "sustainability_guide.pdf",
    "min_score": 0.7
  }
}
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "chunk_id": "chunk_001",
      "text": "Carbon emissions are measured...",
      "score": 0.92,
      "metadata": {
        "source": "sustainability_guide.pdf",
        "page": 12
      }
    }
  ],
  "total": 10
}
```

---

## Quality Management Endpoints

Manage and monitor quality scores and gates.

### POST /quality/score

Calculate quality score for content.

**Request:**
```http
POST /quality/score
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "content": "This is the content to score...",
  "context": "Expected context or reference",
  "metrics": ["relevance", "coherence", "completeness", "accuracy"]
}
```

**Response (200 OK):**
```json
{
  "overall_score": 0.85,
  "metrics": {
    "relevance": 0.92,
    "coherence": 0.88,
    "completeness": 0.79,
    "accuracy": 0.81
  },
  "passed": true,
  "threshold": 0.6
}
```

---

### POST /quality/gate

Evaluate content against quality gate.

**Request:**
```http
POST /quality/gate
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "plan_id": "plan_001",
  "step_id": "step_financial",
  "result": "Financial analysis shows...",
  "threshold": 0.7,
  "require_review": false
}
```

**Response (200 OK):**
```json
{
  "passed": true,
  "score": 0.85,
  "threshold": 0.7,
  "review_required": false,
  "decision": "approved",
  "timestamp": "2025-10-08T14:30:00Z"
}
```

**Decision Values:**
- `approved`: Quality gate passed
- `rejected`: Quality gate failed
- `review_required`: Manual review needed

---

### GET /quality/metrics

Get quality metrics summary.

**Request:**
```http
GET /quality/metrics?timeframe=7d
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**
- `timeframe` (string, optional): Time period (1h, 24h, 7d, 30d) (default: 24h)

**Response (200 OK):**
```json
{
  "timeframe": "7d",
  "average_score": 0.82,
  "total_evaluations": 1543,
  "passed": 1387,
  "failed": 156,
  "pass_rate": 0.899,
  "metrics_breakdown": {
    "relevance": 0.88,
    "coherence": 0.84,
    "completeness": 0.79,
    "accuracy": 0.78
  }
}
```

---

## Monitoring & Health Endpoints

System health checks and metrics.

### GET /health

Basic health check.

**Request:**
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-08T14:30:00Z"
}
```

**Status Values:**
- `healthy`: All systems operational
- `degraded`: Some issues detected
- `unhealthy`: Critical issues

---

### GET /health/detailed

Detailed health check with component status.

**Request:**
```http
GET /health/detailed
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-08T14:30:00Z",
  "checks": {
    "database": true,
    "redis": true,
    "ollama": true,
    "agents": true,
    "workers": true
  },
  "metrics": {
    "uptime_seconds": 86400,
    "request_count": 15420,
    "error_rate": 0.002,
    "avg_response_time": 0.156
  }
}
```

---

### GET /metrics

Prometheus metrics export.

**Request:**
```http
GET /metrics
```

**Response (200 OK):**
```
# HELP veritas_requests_total Total number of requests
# TYPE veritas_requests_total counter
veritas_requests_total{method="POST",endpoint="/agents/execute",status="200"} 1543

# HELP veritas_request_duration_seconds Request duration in seconds
# TYPE veritas_request_duration_seconds histogram
veritas_request_duration_seconds_bucket{le="0.1"} 1234
veritas_request_duration_seconds_bucket{le="0.5"} 1450
veritas_request_duration_seconds_bucket{le="1.0"} 1520
veritas_request_duration_seconds_sum 234.56
veritas_request_duration_seconds_count 1543

# HELP veritas_agent_executions_total Total agent executions
# TYPE veritas_agent_executions_total counter
veritas_agent_executions_total{agent_type="financial",status="completed"} 543
```

---

### GET /status

System status and information.

**Request:**
```http
GET /status
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "api_version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 86400,
  "agents": {
    "total": 7,
    "active": 3,
    "available": ["financial", "environmental", "social", "traffic", "construction"]
  },
  "database": {
    "type": "postgresql",
    "connected": true,
    "pool_size": 20,
    "active_connections": 5
  },
  "cache": {
    "type": "redis",
    "connected": true,
    "memory_usage": "256MB"
  }
}
```

---

## Worker Management Endpoints

Manage background workers and tasks.

### GET /workers/available

List available workers.

**Request:**
```http
GET /workers/available
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "workers": [
    {
      "worker_type": "kge_worker",
      "name": "Knowledge Graph Extraction",
      "available": true,
      "capabilities": ["entity_extraction", "relation_extraction"]
    },
    {
      "worker_type": "keyword_worker",
      "name": "Keyword Extraction",
      "available": true,
      "capabilities": ["keyword_extraction", "phrase_extraction"]
    }
  ],
  "total": 2
}
```

---

### GET /workers/status

Get workers status.

**Request:**
```http
GET /workers/status
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "workers": [
    {
      "worker_type": "kge_worker",
      "status": "active",
      "active_tasks": 3,
      "total_processed": 1543
    }
  ],
  "timestamp": "2025-10-08T14:30:00Z"
}
```

---

### GET /workers/health/{worker_type}

Check worker health.

**Request:**
```http
GET /workers/health/kge_worker
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "worker_type": "kge_worker",
  "status": "healthy",
  "last_check": "2025-10-08T14:30:00Z",
  "response_time_ms": 15.3
}
```

---

## System Administration Endpoints

Administrative endpoints (admin role required).

### GET /admin/users

List all users.

**Request:**
```http
GET /admin/users?limit=20&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": "user_123",
      "username": "user@example.com",
      "role": "user",
      "created_at": "2025-01-01T00:00:00Z",
      "last_login": "2025-10-08T14:30:00Z"
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

---

### POST /admin/users

Create new user.

**Request:**
```http
POST /admin/users
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "username": "newuser@example.com",
  "password": "secure-password",
  "email": "newuser@example.com",
  "role": "user"
}
```

**Response (201 Created):**
```json
{
  "id": "user_456",
  "username": "newuser@example.com",
  "email": "newuser@example.com",
  "role": "user",
  "created_at": "2025-10-08T14:30:00Z"
}
```

---

### PATCH /admin/users/{user_id}/role

Update user role.

**Request:**
```http
PATCH /admin/users/user_123/role
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "role": "manager"
}
```

**Response (200 OK):**
```json
{
  "id": "user_123",
  "role": "manager",
  "updated_at": "2025-10-08T14:30:00Z"
}
```

---

## Common Response Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| `200 OK` | Success | Request successful |
| `201 Created` | Resource created | POST requests creating new resources |
| `202 Accepted` | Async processing started | Long-running operations initiated |
| `204 No Content` | Success, no content | DELETE requests |
| `400 Bad Request` | Invalid request | Malformed JSON, missing required fields |
| `401 Unauthorized` | Authentication failed | Missing or invalid token |
| `403 Forbidden` | Insufficient permissions | Valid token but lacking required permissions |
| `404 Not Found` | Resource not found | Requested resource doesn't exist |
| `409 Conflict` | Resource conflict | Resource already exists or is in conflicting state |
| `422 Unprocessable Entity` | Validation error | Request valid but semantically incorrect |
| `429 Too Many Requests` | Rate limit exceeded | Too many requests from client |
| `500 Internal Server Error` | Server error | Unexpected server-side error |
| `503 Service Unavailable` | Service temporarily unavailable | Maintenance or overload |

---

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Specific field with error",
      "reason": "Detailed reason"
    },
    "timestamp": "2025-10-08T14:30:00Z",
    "request_id": "req_abc123xyz"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_FAILED` | 401 | Invalid credentials or token |
| `AUTHORIZATION_DENIED` | 403 | Insufficient permissions |
| `VALIDATION_ERROR` | 400, 422 | Invalid request parameters |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource doesn't exist |
| `RESOURCE_CONFLICT` | 409 | Resource conflict |
| `INTERNAL_ERROR` | 500 | Server-side error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `TOKEN_EXPIRED` | 401 | JWT token expired |
| `INVALID_TOKEN` | 401 | Malformed or invalid token |
| `QUALITY_GATE_FAILED` | 422 | Quality score below threshold |
| `AGENT_EXECUTION_FAILED` | 500 | Agent execution error |

### Rate Limit Headers

All responses include rate limit information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1728396000
```

---

**Last Updated:** 2025-10-08  
**Version:** 1.0.0  
**License:** MIT
