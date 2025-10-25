# 📊 API v3 - Endpoint Übersicht

**Datum:** 17. Oktober 2025  
**Version:** 3.0  
**Status:** Proposal

---

## 🎯 Neue Endpoints (v3)

### Core Operations (3 Module)

#### 1. Query (`/api/v3/query/`) - 3 Endpoints
- `POST /api/v3/query/standard` - Standard Query
- `POST /api/v3/query/stream` - Streaming Query (SSE)
- `POST /api/v3/query/intelligent` - Multi-Agent Pipeline

#### 2. Agent (`/api/v3/agent/`) - 4 Endpoints
- `GET /api/v3/agent/list` - Liste aller Agents
- `GET /api/v3/agent/:agent_id/info` - Agent Details
- `POST /api/v3/agent/:agent_id/execute` - Agent direkt ausführen
- `GET /api/v3/agent/capabilities` - Agent Capabilities

#### 3. System (`/api/v3/system/`) - 5 Endpoints
- `GET /api/v3/system/health` - Health Check
- `GET /api/v3/system/capabilities` - System Capabilities
- `GET /api/v3/system/modes` - Verfügbare Modi
- `GET /api/v3/system/models` - LLM Models
- `GET /api/v3/system/metrics` - System Metrics

---

### Domain Modules (6 Module)

#### 4. VPB (`/api/v3/vpb/`) - 3 Endpoints
- `POST /api/v3/vpb/query` - VPB-Query
- `GET /api/v3/vpb/documents` - VPB-Dokumente
- `POST /api/v3/vpb/analysis` - Verwaltungsprozess-Analyse

#### 5. COVINA (`/api/v3/covina/`) - 3 Endpoints
- `POST /api/v3/covina/query` - COVINA-Query
- `GET /api/v3/covina/statistics` - COVID-Statistiken
- `GET /api/v3/covina/reports` - COVINA-Reports

#### 6. PKI (`/api/v3/pki/`) - 3 Endpoints
- `POST /api/v3/pki/query` - PKI-Query
- `GET /api/v3/pki/certificates` - Zertifikate
- `POST /api/v3/pki/validation` - Zertifikat-Validierung

#### 7. IMMI (`/api/v3/immi/`) - 3 Endpoints
- `POST /api/v3/immi/query` - Immissionsschutz-Query
- `GET /api/v3/immi/regulations` - BImSchG Vorschriften
- `GET /api/v3/immi/geodata` - WKA Geodaten

#### 8. SAGA (`/api/v3/saga/`) - 6 Endpoints ✨ NEU
- `POST /api/v3/saga/orchestrate` - SAGA Orchestration starten
- `GET /api/v3/saga/:saga_id/status` - SAGA Status
- `POST /api/v3/saga/:saga_id/compensate` - Compensation/Rollback
- `GET /api/v3/saga/:saga_id/history` - SAGA Audit-Log
- `GET /api/v3/saga/list` - Alle SAGAs
- `POST /api/v3/saga/transaction` - Distributed Transaction

#### 9. Compliance (`/api/v3/compliance/`) - 6 Endpoints ✨ NEU
- `POST /api/v3/compliance/check` - Compliance-Prüfung
- `GET /api/v3/compliance/rules` - Compliance-Regeln
- `GET /api/v3/compliance/reports` - Compliance-Reports
- `POST /api/v3/compliance/audit` - Audit-Trail
- `GET /api/v3/compliance/violations` - Verstöße
- `POST /api/v3/compliance/remediate` - Remediation

---

### Enterprise Features (3 Module)

#### 10. Governance (`/api/v3/governance/`) - 6 Endpoints ✨ NEU
- `GET /api/v3/governance/policies` - Data Governance Policies
- `POST /api/v3/governance/validate` - Policy-Validierung
- `GET /api/v3/governance/lineage` - Data Lineage
- `GET /api/v3/governance/catalog` - Data Catalog
- `POST /api/v3/governance/access` - Access Control
- `GET /api/v3/governance/retention` - Data Retention

#### 11. UDS3 (`/api/v3/uds3/`) - 5 Endpoints
- `GET/POST /api/v3/uds3/documents` - Dokumente
- `POST /api/v3/uds3/query` - UDS3 Query
- `POST /api/v3/uds3/vector/search` - Vector Search
- `POST /api/v3/uds3/graph/query` - Graph Query
- `POST /api/v3/uds3/relational/query` - SQL Query

#### 12. User (`/api/v3/user/`) - 4 Endpoints
- `GET/PUT /api/v3/user/profile` - User Profile
- `GET/PUT /api/v3/user/preferences` - User Preferences
- `GET /api/v3/user/history` - Query History
- `POST /api/v3/user/feedback` - User Feedback

---

## 📊 Statistik

### Gesamt

| Kategorie | Module | Endpoints |
|-----------|--------|-----------|
| **Core Operations** | 3 | 12 |
| **Domain Modules** | 6 | 24 |
| **Enterprise Features** | 3 | 15 |
| **TOTAL** | **12** | **51** |

### Neu in v3

| Modul | Endpoints | Status |
|-------|-----------|--------|
| **SAGA** | 6 | ✨ NEU |
| **Compliance** | 6 | ✨ NEU |
| **Governance** | 6 | ✨ NEU |
| **TOTAL** | **18** | **35% der API** |

---

## 🎯 Use Cases

### SAGA Orchestration
```python
# Distributed Transaction mit Compensation
saga = await client.saga_orchestrate(
    saga_name="document_processing",
    steps=[
        {"step_id": "retrieve", "service": "uds3", ...},
        {"step_id": "process", "service": "intelligent_pipeline", ...},
        {"step_id": "store", "service": "uds3", ...}
    ]
)

# Bei Fehler: Automatisches Rollback
if saga['status'] == 'failed':
    await client.saga_compensate(saga['saga_id'])
```

### Compliance Check
```python
# Compliance-Prüfung für Dokument
result = await client.compliance_check(
    entity_type="document",
    entity_id="doc_123",
    rules=["GDPR", "DSGVO", "BImSchG"]
)

if result['status'] == 'non_compliant':
    violations = await client.compliance_violations(status="open")
    for v in violations:
        await client.compliance_remediate(v['violation_id'], ...)
```

### Data Governance
```python
# Data Lineage & Catalog
lineage = await client.governance_lineage(
    entity_id="doc_123",
    depth=5,
    direction="both"
)

# Policy-Validierung
validation = await client.governance_validate(
    policy_id="pol_data_retention",
    entity_id="doc_123"
)

# Access Control
await client.governance_access_grant(
    resource_id="doc_123",
    user_id="user_456",
    access_level="read"
)
```

---

## 🔄 Migration Path

### Von v2 zu v3

| v2 Endpoint | v3 Endpoint | Breaking Changes |
|-------------|-------------|------------------|
| `/v2/query` | `/api/v3/query/standard` | Response-Format |
| `/v2/query/stream` | `/api/v3/query/stream` | SSE-Events |
| `/ask` (Legacy) | `/api/v3/query/standard` | Deprecated |
| `/health` | `/api/v3/system/health` | Response-Struktur |
| `/capabilities` | `/api/v3/system/capabilities` | - |
| `/modes` | `/api/v3/system/modes` | - |

**Neu ohne v2-Äquivalent:**
- SAGA (`/api/v3/saga/*`)
- Compliance (`/api/v3/compliance/*`)
- Governance (`/api/v3/governance/*`)

---

## 📋 Implementation Checklist

### Phase 1: Core (Woche 1)
- [ ] `/api/v3/query/*` - Query Operations
- [ ] `/api/v3/agent/*` - Agent Management
- [ ] `/api/v3/system/*` - System Endpoints

### Phase 2: Domains (Woche 2)
- [ ] `/api/v3/vpb/*` - VPB Module
- [ ] `/api/v3/covina/*` - COVINA Module
- [ ] `/api/v3/pki/*` - PKI Module
- [ ] `/api/v3/immi/*` - IMMI Module

### Phase 3: Enterprise (Woche 2-3)
- [ ] `/api/v3/saga/*` - SAGA Orchestration ✨
- [ ] `/api/v3/compliance/*` - Compliance System ✨
- [ ] `/api/v3/governance/*` - Data Governance ✨

### Phase 4: Infrastructure (Woche 3)
- [ ] `/api/v3/uds3/*` - Database Operations
- [ ] `/api/v3/user/*` - User Management

### Phase 5: Testing & Deployment (Woche 4)
- [ ] Unit Tests (>80% Coverage)
- [ ] Integration Tests
- [ ] Performance Tests
- [ ] Security Audit
- [ ] Documentation (OpenAPI/Swagger)
- [ ] Migration Guide
- [ ] Frontend Integration

---

## 🚀 Benefits

### For Developers
- ✅ Self-documenting API structure
- ✅ Consistent naming conventions
- ✅ RESTful patterns
- ✅ Versioned API (breaking changes possible)

### For Business
- ✅ Enterprise-grade features (SAGA, Compliance, Governance)
- ✅ Regulatory compliance built-in (GDPR, DSGVO)
- ✅ Audit-trails for all operations
- ✅ Data lineage & governance

### For Operations
- ✅ Clear separation of concerns
- ✅ Modular architecture
- ✅ Easy monitoring & debugging
- ✅ Scalable design

---

**Erstellt:** 17. Oktober 2025, 21:50 Uhr  
**Version:** 1.0  
**Status:** ✅ Ready for Implementation
