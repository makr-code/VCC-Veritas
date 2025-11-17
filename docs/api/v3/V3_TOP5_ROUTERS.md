# V3 API Router Documentation - Top 5 Routers

## Executive Summary

This document provides detailed documentation for the 5 priority V3 API routers totaling 2,321 LOC:

1. **Themis Router** (463 LOC) - Multi-Model Database Access
2. **SAGA Router** (385 LOC) - Distributed Transaction Management
3. **Governance Router** (488 LOC) - Policy & Compliance Management
4. **Compliance Router** (426 LOC) - Compliance Checking & Validation
5. **Database Router** (559 LOC) - Direct Database Access Layer

---

## 1. Themis Router (`themis_router.py`)

### 📋 Übersicht

ThemisDB Router bietet direkten Multi-Model Datenbankzugriff auf die ThemisDB, die Vector, Graph, Document und Relational Queries unterstützt.

### Endpoints (7 Total)

#### `POST /themis/vector/search`
**HNSW Vector Search**

```python
{
  "query": "BGB Vertragsrecht Minderjährige",
  "top_k": 5,
  "collection": "legal_documents",
  "threshold": 0.7,
  "metric": "cosine"
}
```

#### `POST /themis/graph/traverse`
**Property Graph Traversal**

```python
{
  "start_vertex": "documents/doc123",
  "edge_collection": "citations",
  "direction": "outbound",
  "min_depth": 1,
  "max_depth": 3
}
```

#### `POST /themis/aql/query`
**AQL Query Execution**

```python
{
  "query": "FOR doc IN legal_documents FILTER doc.category == @category RETURN doc",
  "bind_vars": {"category": "Verwaltungsrecht"}
}
```

#### `GET /themis/document/{collection}/{key}`
**Get Document by Key**

#### `POST /themis/document/{collection}`
**Create Document**

#### `GET /themis/health`
**Health Check**

#### `GET /themis/stats`
**ThemisDB Statistics**

### Features
- Native multi-model queries
- HNSW vector search (300k+ vectors/sec)
- AQL query language support
- Direct ThemisDB access (bypasses adapter factory)
- Performance metrics tracking

---

## 2. SAGA Router (`saga_router.py`)

### 📋 Übersicht

SAGA Pattern Implementation für verteilte Transaktionen mit automatischer Kompensation bei Fehlern.

### Endpoints (5 Total)

#### `POST /saga/create`
**Create SAGA Transaction**

```python
{
  "saga_type": "document_processing",
  "steps": [
    {"service": "validate", "params": {...}},
    {"service": "transform", "params": {...}},
    {"service": "index", "params": {...}}
  ],
  "timeout_seconds": 300
}
```

#### `GET /saga/{saga_id}`
**Get SAGA Status**

Returns: Current status, completed steps, failed steps, compensation status

#### `POST /saga/{saga_id}/execute`
**Execute SAGA Steps**

Executes all steps sequentially with rollback on failure

#### `POST /saga/{saga_id}/compensate`
**Trigger Manual Compensation**

Forces compensation of completed steps

#### `GET /saga/list`
**List All SAGAs**

Filter by status, type, date range

### Features
- Automatic compensation on failure
- Step-by-step execution tracking
- Timeout handling
- Idempotent operations
- Compensation history

---

## 3. Governance Router (`governance_router.py`)

### 📋 Übersicht

Policy Management und Governance Framework für Compliance-Regeln, Audit-Logging und Role-Based Access Control.

### Endpoints (6 Total)

#### `POST /governance/policy`
**Create Policy**

```python
{
  "policy_name": "data_retention",
  "policy_type": "data_governance",
  "rules": [
    {
      "condition": "document.age_days > 365",
      "action": "archive"
    }
  ],
  "enforcement_level": "mandatory"
}
```

#### `GET /governance/policies`
**List All Policies**

Filter by type, status, enforcement level

#### `PUT /governance/policy/{policy_id}`
**Update Policy**

#### `DELETE /governance/policy/{policy_id}`
**Delete Policy**

#### `POST /governance/validate`
**Validate Compliance**

```python
{
  "entity_type": "document",
  "entity_id": "doc_12345",
  "policies": ["data_retention", "access_control"]
}
```

Returns: Compliance status, violations, recommendations

#### `GET /governance/audit-log`
**Audit Log**

Filter by entity, action, date range, user

### Features
- Policy CRUD operations
- Rule-based enforcement
- Compliance validation
- Comprehensive audit logging
- RBAC integration
- Policy versioning

---

## 4. Compliance Router (`compliance_router.py`)

### 📋 Übersicht

Compliance Checking & Validation Engine mit konfigurierbaren Regeln und automatischen Reports.

### Endpoints (5 Total)

#### `POST /compliance/check`
**Run Compliance Check**

```python
{
  "check_type": "gdpr_compliance",
  "target": {
    "type": "document_collection",
    "id": "legal_documents"
  },
  "rules": ["data_minimization", "consent_verification"]
}
```

Returns: Pass/Fail status, violations, severity, remediation steps

#### `GET /compliance/rules`
**List Compliance Rules**

Filter by category, severity, applicability

#### `POST /compliance/rule`
**Create Compliance Rule**

```python
{
  "rule_name": "gdpr_consent",
  "category": "data_protection",
  "severity": "critical",
  "check_function": "verify_consent_present",
  "remediation": "Add consent documentation"
}
```

#### `GET /compliance/report`
**Generate Compliance Report**

Comprehensive report with:
- Overall compliance score
- Violations by severity
- Trends over time
- Remediation recommendations

#### `POST /compliance/validate-document`
**Validate Document**

Quick validation for single document

### Features
- Customizable compliance rules
- Severity-based prioritization
- Automated reporting
- Remediation tracking
- Historical trend analysis
- Multi-standard support (GDPR, ISO, custom)

---

## 5. Database Router (`database_router.py`)

### 📋 Übersicht

Direct Database Access Layer mit SQL-Ausführung, Schema-Introspection und Transaction Support.

### Endpoints (6 Total)

#### `POST /database/query`
**Execute SQL Query**

```python
{
  "query": "SELECT * FROM documents WHERE category = ? LIMIT 10",
  "params": ["Verwaltungsrecht"],
  "read_only": true
}
```

Security: Read-only mode, parameter sanitization, query timeout

#### `GET /database/schema`
**Get Database Schema**

Returns full schema including tables, columns, indexes, relationships

#### `GET /database/tables`
**List All Tables**

With row counts, sizes, last modified timestamps

#### `GET /database/table/{table_name}`
**Get Table Info**

Detailed table information:
- Column definitions
- Indexes
- Constraints
- Relationships
- Statistics

#### `POST /database/transaction`
**Execute Transaction**

```python
{
  "operations": [
    {"query": "INSERT INTO ...", "params": [...]},
    {"query": "UPDATE ...", "params": [...]}
  ],
  "isolation_level": "READ_COMMITTED"
}
```

Atomic execution with rollback on error

#### `GET /database/health`
**Database Health Check**

Connection pool status, active connections, query performance

### Features
- Direct SQL execution with safety checks
- Full schema introspection
- ACID transaction support
- Connection pooling
- Query performance tracking
- Read-only mode enforcement
- Parameter sanitization
- Query timeout protection

---

## 📊 Performance Characteristics

### Themis Router
- **Vector Search**: 100-300ms (300k vectors/sec)
- **Graph Traversal**: 50-500ms (depending on depth)
- **AQL Queries**: 10-200ms
- **Document Operations**: 5-20ms

### SAGA Router
- **SAGA Creation**: 10-50ms
- **Step Execution**: Varies by service (100ms-10s per step)
- **Compensation**: 50-500ms per step
- **Status Check**: <10ms

### Governance Router
- **Policy Validation**: 20-100ms
- **Audit Log Query**: 50-200ms (depending on filter)
- **Policy CRUD**: 10-50ms

### Compliance Router
- **Compliance Check**: 100ms-5s (depending on rules)
- **Rule Evaluation**: 10-50ms per rule
- **Report Generation**: 1-10s

### Database Router
- **Simple Query**: 10-100ms
- **Complex Query**: 100ms-5s
- **Schema Introspection**: 50-200ms
- **Transaction**: Varies by operations

---

## 🔧 Configuration & Dependencies

### Themis Router
```python
# Required
THEMIS_DB_URL = "http://themisdb:8529"
THEMIS_DB_NAME = "veritas"
THEMIS_USERNAME = "root"
THEMIS_PASSWORD = "..."

# Optional
THEMIS_TIMEOUT = 30  # seconds
THEMIS_MAX_RESULTS = 1000
```

### SAGA Router
```python
# Required
SAGA_STORAGE = "database"  # or "redis"
SAGA_TIMEOUT_DEFAULT = 300  # seconds

# Optional
SAGA_MAX_RETRIES = 3
SAGA_RETRY_DELAY = 5  # seconds
```

### Governance Router
```python
# Required
GOVERNANCE_DB = "postgresql://..."
AUDIT_LOG_ENABLED = True

# Optional
POLICY_CACHE_TTL = 300  # seconds
AUDIT_LOG_RETENTION_DAYS = 365
```

### Compliance Router
```python
# Required
COMPLIANCE_RULES_PATH = "/config/compliance_rules.json"

# Optional
COMPLIANCE_CHECK_TIMEOUT = 60  # seconds
REPORT_GENERATION_ASYNC = True
```

### Database Router
```python
# Required
DB_CONNECTION_STRING = "postgresql://..."
DB_POOL_SIZE = 20

# Optional
DB_READ_ONLY_MODE = False  # Force read-only
DB_QUERY_TIMEOUT = 30  # seconds
DB_MAX_RESULTS = 10000
```

---

## 🧪 Testing Examples

### Themis Router Test
```python
def test_vector_search():
    response = client.post("/api/v3/themis/vector/search", json={
        "query": "Verwaltungsrecht",
        "top_k": 5,
        "collection": "test_docs"
    })
    assert response.status_code == 200
    assert len(response.json()["results"]) <= 5
```

### SAGA Router Test
```python
def test_saga_execution():
    # Create SAGA
    create_resp = client.post("/api/v3/saga/create", json={
        "saga_type": "test",
        "steps": [{"service": "step1"}, {"service": "step2"}]
    })
    saga_id = create_resp.json()["saga_id"]
    
    # Execute
    exec_resp = client.post(f"/api/v3/saga/{saga_id}/execute")
    assert exec_resp.status_code == 200
```

### Governance Router Test
```python
def test_policy_crud():
    # Create
    policy = client.post("/api/v3/governance/policy", json={
        "policy_name": "test_policy",
        "rules": [{"condition": "true", "action": "allow"}]
    })
    policy_id = policy.json()["policy_id"]
    
    # Validate
    validate_resp = client.post("/api/v3/governance/validate", json={
        "entity_id": "test",
        "policies": ["test_policy"]
    })
    assert validate_resp.json()["compliant"] == True
```

---

## 🔗 Integration Patterns

### Pattern 1: Query → Themis → Response
```python
# User query → Vector search → Results
query = "BGB Vertragsrecht"
vector_results = themis.vector_search(query, top_k=10)
return format_response(vector_results)
```

### Pattern 2: Multi-Step SAGA
```python
# Document processing pipeline with rollback
saga = create_saga([
    ("validate_document", doc_id),
    ("extract_entities", doc_id),
    ("index_document", doc_id),
    ("notify_users", doc_id)
])
execute_saga(saga)  # Auto-compensation on failure
```

### Pattern 3: Governance-Driven Access
```python
# Check policy before data access
if not governance.validate(user, document, ["access_policy"]):
    raise HTTPException(403, "Policy violation")
return database.query(document_query)
```

### Pattern 4: Compliance Reporting
```python
# Regular compliance check
report = compliance.check("monthly_audit", {
    "collections": ["documents", "users"],
    "rules": ["gdpr", "data_retention"]
})
if report.violations:
    alert_admin(report)
```

---

**Documentation Coverage**: 2,321 LOC (5 Routers)  
**Version**: 3.0  
**Last Updated**: 2025-11-17  
**Status**: Phase 2 (Option B) Complete
