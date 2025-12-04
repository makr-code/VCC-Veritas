# 🔄 API Endpoint Konsolidierung - Vorschlag

**Datum:** 17. Oktober 2025, 21:35 Uhr
**Status:** 📋 Planung
**Ziel:** Einheitliche, strukturierte API-Endpoints für Frontend/Backend

---

## 🎯 Problem

### Aktueller Zustand (IST)

**Backend bietet:**
```
/v2/query                    # Standard Query
/v2/query/stream             # Streaming Query
/v2/intelligent/query        # Intelligent Pipeline
/ask                         # Legacy RAG
/uds3/documents              # UDS3 Dokumente
/uds3/query                  # UDS3 Query
/health                      # Health Check
/capabilities                # System Capabilities
/modes                       # Verfügbare Modi
/api/feedback/*              # Feedback API
/api/immi/*                  # IMMI-spezifisch
```

**Probleme:**
- ❌ Inkonsistente Namensgebung (`/v2/query` vs `/ask`)
- ❌ Unklare Versionierung (nur teilweise `v2`)
- ❌ Fehlende Struktur (Module nicht gruppiert)
- ❌ Legacy-Endpoints vermischt mit modernen

---

## ✨ Lösung: Strukturierte API v3

### Neue Endpoint-Struktur

```
/api/v3/
├── query/                   # Query-Operations
│   ├── standard             # POST - Standard Query (non-streaming)
│   ├── stream               # POST - Streaming Query
│   ├── intelligent          # POST - Intelligent Multi-Agent Pipeline
│   └── agent/:agent_name    # POST - Direkte Agent-Query
│
├── agent/                   # Agent-Management
│   ├── list                 # GET - Liste aller Agents
│   ├── :agent_id/info       # GET - Agent-Details
│   ├── :agent_id/execute    # POST - Agent direkt ausführen
│   └── capabilities         # GET - Agent-Capabilities
│
├── vpb/                     # VPB-spezifische Endpoints
│   ├── query                # POST - VPB-Query
│   ├── documents            # GET - VPB-Dokumente
│   └── analysis             # POST - VPB-Analyse
│
├── covina/                  # COVINA-spezifische Endpoints
│   ├── query                # POST - COVINA-Query
│   ├── statistics           # GET - COVINA-Statistiken
│   └── reports              # GET - COVINA-Reports
│
├── pki/                     # PKI-spezifische Endpoints
│   ├── query                # POST - PKI-Query
│   ├── certificates         # GET - Zertifikate
│   └── validation           # POST - Zertifikat-Validierung
│
├── immi/                    # Immissionsschutz-Endpoints
│   ├── query                # POST - IMMI-Query
│   ├── regulations          # GET - BImSchG Vorschriften
│   └── geodata              # GET - WKA Geodaten
│
├── saga/                    # SAGA Orchestration & Transactions
│   ├── orchestrate          # POST - SAGA Orchestration starten
│   ├── :saga_id/status      # GET - SAGA Status abfragen
│   ├── :saga_id/compensate  # POST - Compensation ausführen
│   ├── :saga_id/history     # GET - SAGA History/Audit-Log
│   ├── list                 # GET - Alle SAGAs auflisten
│   └── transaction          # POST - Distributed Transaction
│
├── compliance/              # Compliance & Regulatory
│   ├── check                # POST - Compliance-Prüfung
│   ├── rules                # GET - Compliance-Regeln
│   ├── reports              # GET - Compliance-Reports
│   ├── audit                # POST - Audit-Trail erstellen
│   ├── violations           # GET - Verstöße auflisten
│   └── remediate            # POST - Remediation-Maßnahmen
│
├── governance/              # Data Governance & Policy
│   ├── policies             # GET - Data Governance Policies
│   ├── validate             # POST - Policy-Validierung
│   ├── lineage              # GET - Data Lineage
│   ├── catalog              # GET - Data Catalog
│   ├── access               # POST - Access Control Management
│   └── retention            # GET - Data Retention Policies
│
├── uds3/                    # UDS3 Database Operations
│   ├── documents            # GET/POST - Dokumente
│   ├── query                # POST - UDS3 Query
│   ├── vector/search        # POST - Vector Search
│   ├── graph/query          # POST - Graph Query
│   └── relational/query     # POST - SQL Query
│
├── user/                    # User-Management
│   ├── profile              # GET/PUT - User Profile
│   ├── preferences          # GET/PUT - User Preferences
│   ├── history              # GET - Query History
│   └── feedback             # POST - User Feedback
│
├── feedback/                # Feedback-System
│   ├── submit               # POST - Feedback senden
│   ├── list                 # GET - Feedback-Liste (Admin)
│   └── statistics           # GET - Feedback-Statistiken
│
└── system/                  # System-Endpoints
    ├── health               # GET - Health Check
    ├── capabilities         # GET - System Capabilities
    ├── modes                # GET - Verfügbare Modi
    ├── models               # GET - LLM Models
    └── metrics              # GET - System Metrics
```

---

## 📊 Detaillierte Endpoint-Spezifikation

### 1. Query Operations (`/api/v3/query/`)

#### `POST /api/v3/query/standard`
**Standard Query ohne Streaming**

**Request:**
```json
{
  "query": "Was ist Immissionsschutz?",
  "mode": "veritas",
  "options": {
    "model": "llama3.2:latest",
    "temperature": 0.7,
    "max_tokens": 1500,
    "top_k": 5,
    "use_rag": true,
    "use_agents": false
  },
  "session_id": "session_20251017_123456"
}
```

**Response:**
```json
{
  "status": "success",
  "query_id": "q_abc123",
  "response": {
    "content": "Immissionsschutz ist...",
    "citations": [
      {"id": "src_1", "text": "{cite:src_1}"}
    ]
  },
  "metadata": {
    "model": "llama3.2:latest",
    "duration": 2.5,
    "complexity": "medium",
    "sources_count": 3
  },
  "sources": [
    {
      "id": "src_1",
      "file": "BImSchG.pdf",
      "page": 5,
      "confidence": 0.87,
      "excerpt": "..."
    }
  ],
  "timestamp": "2025-10-17T21:35:00Z"
}
```

---

#### `POST /api/v3/query/stream`
**Streaming Query mit Server-Sent Events**

**Request:** (gleich wie `/standard`)

**Response:** (SSE Stream)
```
event: progress
data: {"status": "retrieving_context", "progress": 0.2}

event: progress
data: {"status": "generating_response", "progress": 0.5}

event: chunk
data: {"content": "Immissionsschutz ", "chunk_id": 1}

event: chunk
data: {"content": "ist ein wichtiger ", "chunk_id": 2}

event: metadata
data: {"sources_count": 3, "complexity": "medium"}

event: sources
data: [{"id": "src_1", "file": "BImSchG.pdf", ...}]

event: done
data: {"status": "completed", "duration": 2.5}
```

---

#### `POST /api/v3/query/intelligent`
**Intelligent Multi-Agent Pipeline**

**Request:**
```json
{
  "query": "Analyse der Luftqualität in Berlin",
  "options": {
    "enable_agents": true,
    "agent_selection": "auto",  // or ["EnvironmentalAgent", "ImmissionsschutzAgent"]
    "parallel_execution": true,
    "confidence_threshold": 0.7
  }
}
```

**Response:**
```json
{
  "status": "success",
  "response": {
    "content": "...",
    "agent_contributions": [
      {
        "agent": "EnvironmentalAgent",
        "confidence": 0.89,
        "processing_time": 1.2,
        "content": "..."
      }
    ]
  },
  "follow_up_suggestions": ["...", "..."],
  "llm_commentary": "Die Analyse zeigt..."
}
```

---

### 2. Agent Operations (`/api/v3/agent/`)

#### `GET /api/v3/agent/list`
**Liste aller verfügbaren Agents**

**Response:**
```json
{
  "agents": [
    {
      "id": "environmental_agent",
      "name": "EnvironmentalAgent",
      "domain": "environmental",
      "status": "active",
      "capabilities": ["luftqualität", "lärm", "abfall"],
      "requires_db": false,
      "requires_api": false
    }
  ],
  "total_count": 14,
  "by_domain": {
    "environmental": 6,
    "legal": 2,
    "technical": 1
  }
}
```

---

#### `POST /api/v3/agent/:agent_id/execute`
**Agent direkt ausführen**

**Request:**
```json
{
  "query": "Luftqualität in Berlin",
  "context": {...},
  "options": {...}
}
```

---

### 3. Module-spezifische Endpoints

#### VPB (`/api/v3/vpb/`)
```
POST /api/v3/vpb/query           # VPB-Query
GET  /api/v3/vpb/documents       # VPB-Dokumente
POST /api/v3/vpb/analysis        # Verwaltungsprozess-Analyse
```

#### COVINA (`/api/v3/covina/`)
```
POST /api/v3/covina/query        # COVINA-Query
GET  /api/v3/covina/statistics   # COVID-Statistiken
GET  /api/v3/covina/reports      # COVINA-Reports
```

#### PKI (`/api/v3/pki/`)
```
POST /api/v3/pki/query           # PKI-Query
GET  /api/v3/pki/certificates    # Zertifikate
POST /api/v3/pki/validation      # Validierung
```

#### IMMI (`/api/v3/immi/`)
```
POST /api/v3/immi/query          # Immissionsschutz-Query
GET  /api/v3/immi/regulations    # BImSchG Vorschriften
GET  /api/v3/immi/geodata        # WKA Geodaten
```

---

#### SAGA (`/api/v3/saga/`)
```
POST /api/v3/saga/orchestrate    # SAGA Orchestration starten
GET  /api/v3/saga/:saga_id/status # SAGA Status abfragen
POST /api/v3/saga/:saga_id/compensate # Compensation ausführen
GET  /api/v3/saga/list           # Alle SAGAs auflisten
POST /api/v3/saga/transaction    # Distributed Transaction
GET  /api/v3/saga/:saga_id/history # SAGA History/Audit-Log
```

---

#### Compliance (`/api/v3/compliance/`)
```
POST /api/v3/compliance/check    # Compliance-Prüfung
GET  /api/v3/compliance/rules    # Compliance-Regeln
GET  /api/v3/compliance/reports  # Compliance-Reports
POST /api/v3/compliance/audit    # Audit-Trail erstellen
GET  /api/v3/compliance/violations # Verstöße auflisten
POST /api/v3/compliance/remediate # Remediation-Maßnahmen
```

---

#### Governance (`/api/v3/governance/`)
```
GET  /api/v3/governance/policies # Data Governance Policies
POST /api/v3/governance/validate # Policy-Validierung
GET  /api/v3/governance/lineage  # Data Lineage
GET  /api/v3/governance/catalog  # Data Catalog
POST /api/v3/governance/access   # Access Control Management
GET  /api/v3/governance/retention # Data Retention Policies
```

---

---

#### SAGA (`/api/v3/saga/`)

##### `POST /api/v3/saga/orchestrate`
**SAGA Orchestration starten**

**Request:**
```json
{
  "saga_name": "document_processing_saga",
  "steps": [
    {
      "step_id": "retrieve_document",
      "service": "uds3",
      "action": "fetch_document",
      "parameters": {"doc_id": "doc_123"},
      "compensation": "rollback_retrieval"
    },
    {
      "step_id": "process_document",
      "service": "intelligent_pipeline",
      "action": "analyze_document",
      "parameters": {"doc_id": "doc_123"},
      "compensation": "undo_processing"
    },
    {
      "step_id": "store_results",
      "service": "uds3",
      "action": "store_analysis",
      "parameters": {"results": "..."},
      "compensation": "delete_results"
    }
  ],
  "timeout_seconds": 300,
  "isolation_level": "read_committed"
}
```

**Response:**
```json
{
  "saga_id": "saga_abc123",
  "status": "running",
  "started_at": "2025-10-17T21:40:00Z",
  "steps_completed": 0,
  "steps_total": 3,
  "estimated_completion": "2025-10-17T21:45:00Z"
}
```

---

##### `GET /api/v3/saga/:saga_id/status`
**SAGA Status abfragen**

**Response:**
```json
{
  "saga_id": "saga_abc123",
  "status": "completed",  // running, completed, failed, compensating, compensated
  "progress": 1.0,
  "steps": [
    {
      "step_id": "retrieve_document",
      "status": "completed",
      "duration": 0.5,
      "completed_at": "2025-10-17T21:40:01Z"
    },
    {
      "step_id": "process_document",
      "status": "completed",
      "duration": 2.3,
      "completed_at": "2025-10-17T21:40:03Z"
    },
    {
      "step_id": "store_results",
      "status": "completed",
      "duration": 0.2,
      "completed_at": "2025-10-17T21:40:04Z"
    }
  ],
  "total_duration": 3.0,
  "completed_at": "2025-10-17T21:40:04Z"
}
```

---

##### `POST /api/v3/saga/:saga_id/compensate`
**Compensation ausführen (Rollback)**

**Response:**
```json
{
  "saga_id": "saga_abc123",
  "compensation_status": "success",
  "compensated_steps": [
    {"step_id": "store_results", "status": "rolled_back"},
    {"step_id": "process_document", "status": "rolled_back"},
    {"step_id": "retrieve_document", "status": "rolled_back"}
  ],
  "compensation_duration": 1.5
}
```

---

##### `GET /api/v3/saga/:saga_id/history`
**SAGA History/Audit-Log**

**Response:**
```json
{
  "saga_id": "saga_abc123",
  "events": [
    {
      "timestamp": "2025-10-17T21:40:00Z",
      "event": "saga_started",
      "details": {"saga_name": "document_processing_saga"}
    },
    {
      "timestamp": "2025-10-17T21:40:01Z",
      "event": "step_completed",
      "step_id": "retrieve_document",
      "result": "success"
    },
    {
      "timestamp": "2025-10-17T21:40:04Z",
      "event": "saga_completed",
      "total_duration": 3.0
    }
  ],
  "audit_trail": [
    {"user": "system", "action": "saga_created", "timestamp": "..."},
    {"user": "admin", "action": "saga_monitored", "timestamp": "..."}
  ]
}
```

---

#### Compliance (`/api/v3/compliance/`)

##### `POST /api/v3/compliance/check`
**Compliance-Prüfung durchführen**

**Request:**
```json
{
  "entity_type": "document",
  "entity_id": "doc_123",
  "rules": ["GDPR", "DSGVO", "BImSchG_compliance"],
  "check_mode": "full"  // or "quick"
}
```

**Response:**
```json
{
  "compliance_check_id": "check_xyz789",
  "entity_id": "doc_123",
  "status": "compliant",  // compliant, non_compliant, partial
  "overall_score": 0.95,
  "checks": [
    {
      "rule": "GDPR",
      "status": "compliant",
      "score": 1.0,
      "details": "Alle GDPR-Anforderungen erfüllt"
    },
    {
      "rule": "DSGVO",
      "status": "compliant",
      "score": 0.98,
      "details": "DSGVO-Anforderungen erfüllt, kleine Warnung bei Datenlöschung"
    },
    {
      "rule": "BImSchG_compliance",
      "status": "compliant",
      "score": 0.87,
      "details": "BImSchG-Grenzwerte eingehalten"
    }
  ],
  "violations": [],
  "warnings": [
    {
      "rule": "DSGVO",
      "severity": "low",
      "message": "Datenlöschungsfrist könnte präziser sein"
    }
  ],
  "timestamp": "2025-10-17T21:40:00Z"
}
```

---

##### `GET /api/v3/compliance/rules`
**Compliance-Regeln auflisten**

**Response:**
```json
{
  "rules": [
    {
      "rule_id": "GDPR",
      "name": "General Data Protection Regulation",
      "category": "data_protection",
      "status": "active",
      "version": "2.0",
      "last_updated": "2024-01-01",
      "checks": [
        "data_minimization",
        "purpose_limitation",
        "right_to_erasure",
        "consent_management"
      ]
    },
    {
      "rule_id": "BImSchG_compliance",
      "name": "Bundesimmissionsschutzgesetz Compliance",
      "category": "environmental",
      "status": "active",
      "version": "3.1",
      "last_updated": "2025-06-01",
      "checks": [
        "emission_limits",
        "noise_protection",
        "air_quality_standards"
      ]
    }
  ],
  "total_count": 12,
  "categories": ["data_protection", "environmental", "legal", "security"]
}
```

---

##### `GET /api/v3/compliance/violations`
**Compliance-Verstöße auflisten**

**Response:**
```json
{
  "violations": [
    {
      "violation_id": "viol_001",
      "entity_type": "document",
      "entity_id": "doc_456",
      "rule": "GDPR",
      "severity": "high",
      "description": "Personenbezogene Daten ohne Einwilligung gespeichert",
      "detected_at": "2025-10-17T20:00:00Z",
      "status": "open",  // open, remediated, acknowledged
      "remediation_deadline": "2025-10-24T23:59:59Z"
    }
  ],
  "summary": {
    "total": 3,
    "by_severity": {"critical": 0, "high": 1, "medium": 1, "low": 1},
    "by_status": {"open": 2, "remediated": 1}
  }
}
```

---

##### `POST /api/v3/compliance/remediate`
**Remediation-Maßnahmen durchführen**

**Request:**
```json
{
  "violation_id": "viol_001",
  "action": "delete_personal_data",
  "parameters": {
    "entities": ["user_email", "user_phone"],
    "anonymize": true
  },
  "justification": "GDPR Right to Erasure",
  "performed_by": "admin_user"
}
```

**Response:**
```json
{
  "remediation_id": "rem_abc123",
  "status": "completed",
  "actions_taken": [
    {"action": "anonymized_field", "field": "user_email"},
    {"action": "anonymized_field", "field": "user_phone"}
  ],
  "violation_status": "remediated",
  "audit_log_entry": "audit_log_xyz789",
  "timestamp": "2025-10-17T21:45:00Z"
}
```

---

#### Governance (`/api/v3/governance/`)

##### `GET /api/v3/governance/policies`
**Data Governance Policies abrufen**

**Response:**
```json
{
  "policies": [
    {
      "policy_id": "pol_data_retention",
      "name": "Data Retention Policy",
      "category": "retention",
      "status": "active",
      "rules": [
        {
          "data_type": "user_logs",
          "retention_period_days": 90,
          "action_after": "archive"
        },
        {
          "data_type": "query_history",
          "retention_period_days": 365,
          "action_after": "delete"
        }
      ],
      "version": "1.2",
      "effective_from": "2025-01-01"
    },
    {
      "policy_id": "pol_access_control",
      "name": "Access Control Policy",
      "category": "security",
      "status": "active",
      "rules": [
        {
          "resource": "sensitive_documents",
          "access_level": "role_based",
          "allowed_roles": ["admin", "compliance_officer"]
        }
      ]
    }
  ],
  "total_count": 8
}
```

---

##### `POST /api/v3/governance/validate`
**Policy-Validierung durchführen**

**Request:**
```json
{
  "policy_id": "pol_data_retention",
  "entity_type": "document",
  "entity_id": "doc_789",
  "check_compliance": true
}
```

**Response:**
```json
{
  "validation_id": "val_xyz456",
  "policy_id": "pol_data_retention",
  "entity_id": "doc_789",
  "status": "compliant",
  "details": [
    {
      "rule": "retention_period",
      "status": "compliant",
      "current_age_days": 45,
      "max_age_days": 90
    }
  ],
  "actions_required": [],
  "next_review_date": "2025-11-01"
}
```

---

##### `GET /api/v3/governance/lineage`
**Data Lineage abrufen**

**Request Parameters:**
- `entity_id` - ID der Entität
- `depth` - Lineage-Tiefe (1-10)
- `direction` - "upstream" oder "downstream" oder "both"

**Response:**
```json
{
  "entity_id": "doc_123",
  "lineage": {
    "upstream": [
      {
        "entity_id": "source_raw_data_001",
        "entity_type": "raw_file",
        "transformation": "extract",
        "timestamp": "2025-10-17T10:00:00Z"
      }
    ],
    "downstream": [
      {
        "entity_id": "analysis_report_456",
        "entity_type": "report",
        "transformation": "aggregate",
        "timestamp": "2025-10-17T11:00:00Z"
      },
      {
        "entity_id": "dashboard_viz_789",
        "entity_type": "visualization",
        "transformation": "visualize",
        "timestamp": "2025-10-17T12:00:00Z"
      }
    ]
  },
  "graph": {
    "nodes": [...],
    "edges": [...]
  }
}
```

---

##### `GET /api/v3/governance/catalog`
**Data Catalog abrufen**

**Response:**
```json
{
  "catalog": [
    {
      "asset_id": "asset_doc_collection",
      "name": "Document Collection",
      "type": "dataset",
      "owner": "admin",
      "description": "Collection of legal documents",
      "tags": ["legal", "BImSchG", "GDPR"],
      "metadata": {
        "row_count": 15420,
        "size_bytes": 1024000000,
        "last_updated": "2025-10-17T21:00:00Z"
      },
      "schema": [
        {"field": "doc_id", "type": "string", "pii": false},
        {"field": "content", "type": "text", "pii": false},
        {"field": "author", "type": "string", "pii": true}
      ],
      "access_level": "restricted",
      "compliance_tags": ["GDPR", "DSGVO"]
    }
  ],
  "total_count": 42,
  "facets": {
    "by_type": {"dataset": 30, "report": 8, "model": 4},
    "by_compliance": {"GDPR": 25, "DSGVO": 25, "BImSchG": 10}
  }
}
```

---

##### `POST /api/v3/governance/access`
**Access Control Management**

**Request:**
```json
{
  "action": "grant_access",
  "resource_id": "doc_123",
  "user_id": "user_456",
  "access_level": "read",
  "expiration": "2025-12-31T23:59:59Z",
  "justification": "Required for compliance audit"
}
```

**Response:**
```json
{
  "access_grant_id": "grant_xyz789",
  "status": "granted",
  "resource_id": "doc_123",
  "user_id": "user_456",
  "access_level": "read",
  "granted_at": "2025-10-17T21:50:00Z",
  "expires_at": "2025-12-31T23:59:59Z",
  "audit_log_entry": "audit_log_abc123"
}
```

---

### 4. UDS3 Operations (`/api/v3/uds3/`)

#### `POST /api/v3/uds3/vector/search`
**Vector Database Search**

**Request:**
```json
{
  "query": "Immissionsschutz",
  "top_k": 10,
  "filters": {
    "document_type": "law",
    "year": {"gte": 2020}
  }
}
```

---

#### `POST /api/v3/uds3/graph/query`
**Graph Database Query**

**Request:**
```json
{
  "cypher": "MATCH (n:Law)-[:RELATES_TO]->(m) RETURN n, m LIMIT 10"
}
```

---

#### `POST /api/v3/uds3/relational/query`
**SQL Query**

**Request:**
```json
{
  "sql": "SELECT * FROM documents WHERE type = 'law' LIMIT 10"
}
```

---

### 5. User Management (`/api/v3/user/`)

#### `GET /api/v3/user/profile`
**User Profile**

**Response:**
```json
{
  "user_id": "user_123",
  "name": "Max Mustermann",
  "email": "max@example.com",
  "role": "user",
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

#### `GET /api/v3/user/history`
**Query History**

**Response:**
```json
{
  "queries": [
    {
      "query_id": "q_abc123",
      "query": "Was ist Immissionsschutz?",
      "timestamp": "2025-10-17T21:00:00Z",
      "mode": "veritas",
      "duration": 2.5
    }
  ],
  "total_count": 42,
  "page": 1
}
```

---

#### `POST /api/v3/user/feedback`
**User Feedback senden**

**Request:**
```json
{
  "query_id": "q_abc123",
  "rating": "positive",
  "comment": "Sehr hilfreich!",
  "metadata": {...}
}
```

---

### 6. System Endpoints (`/api/v3/system/`)

#### `GET /api/v3/system/health`
**Health Check**

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-17T21:35:00Z",
  "components": {
    "ollama": "ok",
    "uds3": "ok",
    "intelligent_pipeline": "ok"
  },
  "uptime_seconds": 12345
}
```

---

#### `GET /api/v3/system/capabilities`
**System Capabilities** (wie aktuell, aber strukturierter)

---

#### `GET /api/v3/system/modes`
**Verfügbare Modi**

**Response:**
```json
{
  "modes": {
    "veritas": {
      "display_name": "Standard RAG",
      "description": "...",
      "endpoint": "/api/v3/query/standard",
      "streaming_endpoint": "/api/v3/query/stream",
      "status": "active"
    }
  }
}
```

---

## 🔄 Migration Plan

### Phase 1: Parallel Betrieb (2 Wochen)
- ✅ **Neue API v3 implementieren**
- ✅ **Legacy-Endpoints beibehalten** (`/ask`, `/v2/query`)
- ✅ **Deprecation Warnings** in Responses
- ✅ **Dokumentation updaten**

### Phase 2: Frontend-Migration (1 Woche)
- ✅ **Frontend auf v3 umstellen**
- ✅ **Fallback auf Legacy** falls v3 nicht verfügbar
- ✅ **Testing mit beiden APIs**

### Phase 3: Legacy-Removal (1 Woche)
- ✅ **Legacy-Endpoints entfernen**
- ✅ **Nur noch v3 aktiv**
- ✅ **Monitoring & Bugfixing**

---

## 📋 Frontend-Anpassungen

### Neue Service-Klasse

```python
# frontend/services/veritas_api_client.py

class VeritasAPIClient:
    """Unified API Client für VERITAS v3"""

    def __init__(self, base_url="http://localhost:5000/api/v3"):
        self.base_url = base_url

    # Query Operations
    async def query_standard(self, query: str, options: dict = None):
        """Standard Query (non-streaming)"""
        endpoint = f"{self.base_url}/query/standard"
        return await self._post(endpoint, {"query": query, "options": options})

    async def query_stream(self, query: str, options: dict = None):
        """Streaming Query (SSE)"""
        endpoint = f"{self.base_url}/query/stream"
        async for chunk in self._stream(endpoint, {"query": query, "options": options}):
            yield chunk

    async def query_intelligent(self, query: str, agent_options: dict = None):
        """Intelligent Multi-Agent Query"""
        endpoint = f"{self.base_url}/query/intelligent"
        return await self._post(endpoint, {"query": query, "options": agent_options})

    # Agent Operations
    async def list_agents(self):
        """Liste aller Agents"""
        endpoint = f"{self.base_url}/agent/list"
        return await self._get(endpoint)

    async def execute_agent(self, agent_id: str, query: str):
        """Agent direkt ausführen"""
        endpoint = f"{self.base_url}/agent/{agent_id}/execute"
        return await self._post(endpoint, {"query": query})

    # Module-spezifische Queries
    async def vpb_query(self, query: str):
        endpoint = f"{self.base_url}/vpb/query"
        return await self._post(endpoint, {"query": query})

    async def covina_query(self, query: str):
        endpoint = f"{self.base_url}/covina/query"
        return await self._post(endpoint, {"query": query})

    async def pki_query(self, query: str):
        endpoint = f"{self.base_url}/pki/query"
        return await self._post(endpoint, {"query": query})

    async def immi_query(self, query: str):
        endpoint = f"{self.base_url}/immi/query"
        return await self._post(endpoint, {"query": query})

    # SAGA Operations
    async def saga_orchestrate(self, saga_name: str, steps: list):
        endpoint = f"{self.base_url}/saga/orchestrate"
        return await self._post(endpoint, {"saga_name": saga_name, "steps": steps})

    async def saga_status(self, saga_id: str):
        endpoint = f"{self.base_url}/saga/{saga_id}/status"
        return await self._get(endpoint)

    async def saga_compensate(self, saga_id: str):
        endpoint = f"{self.base_url}/saga/{saga_id}/compensate"
        return await self._post(endpoint, {})

    async def saga_history(self, saga_id: str):
        endpoint = f"{self.base_url}/saga/{saga_id}/history"
        return await self._get(endpoint)

    # Compliance Operations
    async def compliance_check(self, entity_type: str, entity_id: str, rules: list):
        endpoint = f"{self.base_url}/compliance/check"
        return await self._post(endpoint, {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "rules": rules
        })

    async def compliance_rules(self):
        endpoint = f"{self.base_url}/compliance/rules"
        return await self._get(endpoint)

    async def compliance_violations(self, status: str = None):
        endpoint = f"{self.base_url}/compliance/violations"
        params = {"status": status} if status else {}
        return await self._get(endpoint, params=params)

    async def compliance_remediate(self, violation_id: str, action: str, parameters: dict):
        endpoint = f"{self.base_url}/compliance/remediate"
        return await self._post(endpoint, {
            "violation_id": violation_id,
            "action": action,
            "parameters": parameters
        })

    # Governance Operations
    async def governance_policies(self):
        endpoint = f"{self.base_url}/governance/policies"
        return await self._get(endpoint)

    async def governance_validate(self, policy_id: str, entity_id: str):
        endpoint = f"{self.base_url}/governance/validate"
        return await self._post(endpoint, {
            "policy_id": policy_id,
            "entity_id": entity_id
        })

    async def governance_lineage(self, entity_id: str, depth: int = 3, direction: str = "both"):
        endpoint = f"{self.base_url}/governance/lineage"
        params = {"entity_id": entity_id, "depth": depth, "direction": direction}
        return await self._get(endpoint, params=params)

    async def governance_catalog(self, filters: dict = None):
        endpoint = f"{self.base_url}/governance/catalog"
        return await self._get(endpoint, params=filters)

    async def governance_access_grant(self, resource_id: str, user_id: str, access_level: str):
        endpoint = f"{self.base_url}/governance/access"
        return await self._post(endpoint, {
            "action": "grant_access",
            "resource_id": resource_id,
            "user_id": user_id,
            "access_level": access_level
        })

    # UDS3 Operations
    async def uds3_vector_search(self, query: str, top_k: int = 10):
        endpoint = f"{self.base_url}/uds3/vector/search"
        return await self._post(endpoint, {"query": query, "top_k": top_k})

    # User Operations
    async def submit_feedback(self, query_id: str, rating: str, comment: str = None):
        endpoint = f"{self.base_url}/user/feedback"
        return await self._post(endpoint, {
            "query_id": query_id,
            "rating": rating,
            "comment": comment
        })

    async def get_history(self, page: int = 1, limit: int = 20):
        endpoint = f"{self.base_url}/user/history"
        return await self._get(endpoint, params={"page": page, "limit": limit})

    # System Operations
    async def health_check(self):
        endpoint = f"{self.base_url}/system/health"
        return await self._get(endpoint)

    async def get_capabilities(self):
        endpoint = f"{self.base_url}/system/capabilities"
        return await self._get(endpoint)

    async def get_modes(self):
        endpoint = f"{self.base_url}/system/modes"
        return await self._get(endpoint)
```

---

## 🎯 Vorteile der Konsolidierung

### 1. **Klarheit & Struktur**
- ✅ Konsistente Namensgebung
- ✅ Logische Gruppierung nach Funktion
- ✅ Klare Versionierung (v3)

### 2. **Erweiterbarkeit**
- ✅ Einfaches Hinzufügen neuer Module (`/api/v3/new_module/`)
- ✅ Klare Trennung von Concerns
- ✅ Standardisierte Response-Formate

### 3. **Developer Experience**
- ✅ Selbsterklärende URLs
- ✅ RESTful Patterns
- ✅ Einfache API-Discovery

### 4. **Wartbarkeit**
- ✅ Zentrale API-Verwaltung
- ✅ Versionierung ermöglicht Breaking Changes
- ✅ Legacy-Endpoints können sauber entfernt werden

### 5. **Testing**
- ✅ Strukturierte Test-Suites pro Modul
- ✅ Einfaches Mocking für Frontend-Tests
- ✅ Klare API-Contracts

---

## 📝 Nächste Schritte

### 1. **Backend-Implementierung** (Priority: HIGH)
```python
# backend/api/v3/__init__.py
# backend/api/v3/query_router.py
# backend/api/v3/agent_router.py
# backend/api/v3/vpb_router.py
# backend/api/v3/covina_router.py
# backend/api/v3/pki_router.py
# backend/api/v3/immi_router.py
# backend/api/v3/saga_router.py          # ✨ NEU
# backend/api/v3/compliance_router.py    # ✨ NEU
# backend/api/v3/governance_router.py    # ✨ NEU
# backend/api/v3/uds3_router.py
# backend/api/v3/user_router.py
# backend/api/v3/system_router.py
```

### 2. **Frontend-Anpassung** (Priority: MEDIUM)
```python
# frontend/services/veritas_api_client.py
# frontend/services/api_config.py
```

### 3. **Dokumentation** (Priority: HIGH)
- OpenAPI/Swagger Spec für v3
- Migration Guide für Entwickler
- API-Referenz für Frontend-Team

### 4. **Testing** (Priority: HIGH)
- Unit-Tests für alle v3 Endpoints
- Integration-Tests Frontend ↔ Backend
- Performance-Tests (v2 vs v3)

---

## 🚀 Timeline

| Woche | Task | Status |
|-------|------|--------|
| W1 | Backend v3 Core (Query, System) | ⏳ TODO |
| W1 | Backend v3 Agents | ⏳ TODO |
| W2 | Backend v3 Module (VPB, COVINA, PKI, IMMI) | ⏳ TODO |
| W2 | Backend v3 UDS3 | ⏳ TODO |
| W3 | Frontend API Client | ⏳ TODO |
| W3 | Frontend Integration | ⏳ TODO |
| W4 | Testing & Bugfixing | ⏳ TODO |
| W4 | Legacy-Removal | ⏳ TODO |

---

**Erstellt:** 17. Oktober 2025, 21:35 Uhr
**Status:** 📋 Proposal - Awaiting Approval
**Version:** 1.0
