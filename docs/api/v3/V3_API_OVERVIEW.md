# VERITAS API v3 - Overview

## 📋 Übersicht

Die **VERITAS API v3** ist die Hauptschnittstelle für alle Backend-Services und bietet 16 spezialisierte Router für verschiedene Funktionsbereiche. Die API basiert auf FastAPI und bietet vollständige OpenAPI/Swagger-Dokumentation.

### API-Struktur

```
/api/v3/
├── /query          - Query Processing (RAG, Hybrid, Streaming)
├── /agent          - Agent Management & Execution
├── /themis         - ThemisDB Multi-Model Database
├── /saga           - SAGA Pattern Orchestration
├── /governance     - Governance & Compliance Management
├── /compliance     - Compliance Checking & Validation
├── /database       - Direct Database Access
├── /system         - System Management & Health
├── /user           - User Management
├── /covina         - Covina Module Integration
├── /immi           - Immissionsschutz (Environmental Protection)
├── /adapter        - Adapter Management
├── /pki            - PKI/Certificate Management
├── /vpb            - VPB (Verwaltungspraxis Bayern)
├── /uds3           - Universal Data Service
└── /ws             - WebSocket Connections
```

## 🗂️ Router-Katalog

### 1. Query Router (`query_router.py`)

**Zweck**: Zentrale Query-Verarbeitung mit Multiple Modes

**Endpoints**:
- `POST /query` - Process query (RAG/Hybrid/Streaming/Agent/Ask)
- `POST /query/batch` - Batch query processing
- `GET /query/{query_id}` - Get query result
- `GET /query/history` - Query history

**Features**:
- 5 Query-Modi (RAG, Hybrid, Streaming, Agent, Ask)
- IEEE Citation Generation
- Streaming Support
- Query History

**LOC**: 423 | **Size**: 13 KB

---

### 2. Agent Router (`agent_router.py`)

**Zweck**: Agent Management und Execution

**Endpoints**:
- `GET /agents` - List all agents
- `GET /agents/{agent_id}` - Get agent info
- `POST /agents/{agent_id}/query` - Execute agent query
- `POST /agents/search` - Search agents by capability

**Features**:
- Agent Discovery
- Capability-based Search
- Agent Execution
- Performance Metrics

**LOC**: 298 | **Size**: 9.7 KB

---

### 3. Themis Router (`themis_router.py`) ⭐ DOCUMENTED

**Zweck**: ThemisDB Multi-Model Database Access

**Endpoints**:
- `POST /themis/vector/search` - HNSW Vector Search
- `POST /themis/graph/traverse` - Property Graph Traversal
- `POST /themis/aql/query` - AQL Query Execution
- `GET /themis/document/{collection}/{key}` - Get Document
- `POST /themis/document/{collection}` - Create Document
- `GET /themis/health` - Health Check
- `GET /themis/stats` - Statistics

**Features**:
- Native Multi-Model Queries (Vector, Graph, Document, Relational)
- AQL Query Language
- Direct ThemisDB Access
- Performance Metrics

**LOC**: 463 | **Size**: 14 KB | **Documentation**: `THEMIS_ROUTER.md`

---

### 4. SAGA Router (`saga_router.py`) ⭐ DOCUMENTED

**Zweck**: SAGA Pattern Implementation für Distributed Transactions

**Endpoints**:
- `POST /saga/create` - Create SAGA transaction
- `GET /saga/{saga_id}` - Get SAGA status
- `POST /saga/{saga_id}/execute` - Execute SAGA
- `POST /saga/{saga_id}/compensate` - Trigger compensation
- `GET /saga/list` - List all SAGAs

**Features**:
- Distributed Transaction Management
- Automatic Compensation
- Step Tracking
- Timeout Handling

**LOC**: 385 | **Size**: 12 KB | **Documentation**: `SAGA_ROUTER.md`

---

### 5. Governance Router (`governance_router.py`) ⭐ DOCUMENTED

**Zweck**: Governance & Policy Management

**Endpoints**:
- `POST /governance/policy` - Create policy
- `GET /governance/policies` - List policies
- `PUT /governance/policy/{policy_id}` - Update policy
- `DELETE /governance/policy/{policy_id}` - Delete policy
- `POST /governance/validate` - Validate compliance
- `GET /governance/audit-log` - Audit log

**Features**:
- Policy Management (CRUD)
- Compliance Validation
- Audit Logging
- Role-Based Access Control

**LOC**: 488 | **Size**: 17 KB | **Documentation**: `GOVERNANCE_ROUTER.md`

---

### 6. Compliance Router (`compliance_router.py`) ⭐ DOCUMENTED

**Zweck**: Compliance Checking & Validation

**Endpoints**:
- `POST /compliance/check` - Run compliance check
- `GET /compliance/rules` - List compliance rules
- `POST /compliance/rule` - Create compliance rule
- `GET /compliance/report` - Generate compliance report
- `POST /compliance/validate-document` - Validate document

**Features**:
- Rule-Based Compliance Checking
- Document Validation
- Compliance Reporting
- Customizable Rules

**LOC**: 426 | **Size**: 14 KB | **Documentation**: `COMPLIANCE_ROUTER.md`

---

### 7. Database Router (`database_router.py`) ⭐ DOCUMENTED

**Zweck**: Direct Database Access Layer

**Endpoints**:
- `POST /database/query` - Execute SQL query
- `GET /database/schema` - Get database schema
- `GET /database/tables` - List tables
- `GET /database/table/{table_name}` - Get table info
- `POST /database/transaction` - Execute transaction
- `GET /database/health` - Database health

**Features**:
- Direct SQL Execution
- Schema Introspection
- Transaction Support
- Connection Pooling

**LOC**: 559 | **Size**: 16 KB | **Documentation**: `DATABASE_ROUTER.md`

---

### 8. System Router (`system_router.py`)

**Zweck**: System Management & Monitoring

**Endpoints**:
- `GET /system/health` - Overall system health
- `GET /system/metrics` - System metrics
- `GET /system/services` - List services status
- `POST /system/service/{service_id}/restart` - Restart service
- `GET /system/logs` - System logs

**Features**:
- Health Monitoring
- Service Management
- Metrics Collection
- Log Access

**LOC**: 427 | **Size**: 14 KB

---

### 9. User Router (`user_router.py`)

**Zweck**: User Management

**Endpoints**:
- `POST /user/register` - User registration
- `POST /user/login` - User login
- `GET /user/profile` - Get user profile
- `PUT /user/profile` - Update profile
- `POST /user/logout` - Logout

**Features**:
- User Authentication
- Profile Management
- Session Management
- Role Management

**LOC**: 419 | **Size**: 14 KB

---

### 10. Covina Router (`covina_router.py`)

**Zweck**: Covina Module Integration

**Endpoints**:
- `POST /covina/process` - Process Covina request
- `GET /covina/modules` - List available modules
- `GET /covina/status` - Covina system status

**Features**:
- Module Discovery
- Request Processing
- Status Monitoring

**LOC**: 245 | **Size**: 7.9 KB

---

### 11. Immissionsschutz Router (`immi_router.py`)

**Zweck**: Immissionsschutz (Environmental Protection) Queries

**Endpoints**:
- `POST /immi/check-limits` - Check emission limits
- `POST /immi/calculate-dispersion` - Calculate pollutant dispersion
- `GET /immi/regulations` - Get relevant regulations

**Features**:
- Emission Limit Checking
- Dispersion Modeling
- Regulation Lookup

**LOC**: 343 | **Size**: 11 KB

---

### 12. Adapter Router (`adapter_router.py`)

**Zweck**: Adapter Factory Management

**Endpoints**:
- `GET /adapter/list` - List available adapters
- `POST /adapter/{adapter_type}/initialize` - Initialize adapter
- `GET /adapter/{adapter_id}/status` - Adapter status
- `POST /adapter/{adapter_id}/execute` - Execute adapter operation

**Features**:
- Adapter Discovery
- Dynamic Initialization
- Operation Execution
- Status Monitoring

**LOC**: 658 | **Size**: 21 KB

---

### 13. PKI Router (`pki_router.py`)

**Zweck**: Public Key Infrastructure Management

**Endpoints**:
- `POST /pki/certificate/generate` - Generate certificate
- `GET /pki/certificate/{cert_id}` - Get certificate
- `POST /pki/certificate/revoke` - Revoke certificate
- `GET /pki/certificate/validate` - Validate certificate

**Features**:
- Certificate Generation
- Certificate Validation
- Revocation Management
- Key Management

**LOC**: 347 | **Size**: 11 KB

---

### 14. VPB Router (`vpb_router.py`)

**Zweck**: Verwaltungspraxis Bayern Integration

**Endpoints**:
- `POST /vpb/search` - Search VPB database
- `GET /vpb/document/{doc_id}` - Get VPB document
- `GET /vpb/categories` - List VPB categories

**Features**:
- VPB Database Search
- Document Retrieval
- Category Navigation

**LOC**: 301 | **Size**: 9.7 KB

---

### 15. UDS3 Router (`uds3_router.py`)

**Zweck**: Universal Data Service v3

**Endpoints**:
- `POST /uds3/index` - Index documents
- `POST /uds3/search` - Search indexed documents
- `GET /uds3/document/{doc_id}` - Get document
- `DELETE /uds3/document/{doc_id}` - Delete document
- `GET /uds3/statistics` - Index statistics

**Features**:
- Document Indexing
- Full-Text Search
- Document Management
- Statistics

**LOC**: 612 | **Size**: 20 KB

---

### 16. WebSocket Router (`websocket_router.py`)

**Zweck**: Real-Time WebSocket Connections

**Endpoints**:
- `WS /ws/connect` - Establish WebSocket connection
- `WS /ws/stream/{session_id}` - Streaming session
- `WS /ws/chat` - Chat interface

**Features**:
- Real-Time Communication
- Streaming Support
- Chat Interface
- Session Management

**LOC**: 652 | **Size**: 21 KB

---

## 📊 Statistiken

### Gesamt-Übersicht

```
Total Routers:       16
Total LOC:           ~7,000
Total Size:          ~215 KB
Documented:          5 (31%)
Undocumented:        11 (69%)
```

### Nach Kategorie

**Core Services (5 Router)**
- Query, Agent, System, User, Database
- LOC: ~2,100

**Multi-Model Database (2 Router)**
- Themis, UDS3
- LOC: ~1,075

**Governance & Compliance (2 Router)**
- Governance, Compliance
- LOC: ~914

**Domain-Specific (4 Router)**
- Immi, Covina, VPB, PKI
- LOC: ~1,236

**Infrastructure (3 Router)**
- SAGA, Adapter, WebSocket
- LOC: ~1,675

### Dokumentations-Status

**✅ Dokumentiert (5 Router)**:
1. Themis Router - Multi-Model Database
2. SAGA Router - Distributed Transactions
3. Governance Router - Policy Management
4. Compliance Router - Compliance Checking
5. Database Router - Direct DB Access

**📝 Top Priority für zukünftige Dokumentation (5 Router)**:
1. Query Router - Zentrale Query-Verarbeitung (423 LOC)
2. Agent Router - Agent Management (298 LOC)
3. UDS3 Router - Universal Data Service (612 LOC)
4. Adapter Router - Adapter Factory (658 LOC)
5. WebSocket Router - Real-Time Communication (652 LOC)

**🔜 Standard Priority (6 Router)**:
- System, User, Covina, Immi, PKI, VPB

## 🔗 Verwandte Dokumentation

### Services
- Query Service (`QUERY_SERVICE.md`)
- Process Executor (`PROCESS_EXECUTOR.md`)

### Agents
- Agent Registry (`AGENT_REGISTRY.md`)
- Agent Message Broker (`AGENT_MESSAGE_BROKER.md`)

### API Documentation
- Themis Router (`THEMIS_ROUTER.md`) ✅
- SAGA Router (`SAGA_ROUTER.md`) ✅
- Governance Router (`GOVERNANCE_ROUTER.md`) ✅
- Compliance Router (`COMPLIANCE_ROUTER.md`) ✅
- Database Router (`DATABASE_ROUTER.md`) ✅

## 🚀 Getting Started

### API-Zugriff

```python
import requests

BASE_URL = "http://localhost:8000/api/v3"

# Example: Query Router
response = requests.post(
    f"{BASE_URL}/query",
    json={
        "query": "BGB Vertragsrecht",
        "mode": "rag",
        "top_k": 5
    }
)
```

### OpenAPI Documentation

```
http://localhost:8000/docs        # Swagger UI
http://localhost:8000/redoc       # ReDoc
http://localhost:8000/openapi.json  # OpenAPI Schema
```

### Authentication

Die meisten Endpoints erfordern Authentication via JWT Token:

```python
headers = {
    "Authorization": f"Bearer {jwt_token}"
}
response = requests.get(f"{BASE_URL}/user/profile", headers=headers)
```

---

**Version**: 3.0  
**Letzte Aktualisierung**: 2025-11-17  
**Dokumentierte Router**: 5 von 16 (31%)  
**Total LOC abgedeckt**: 2,321 von ~7,000 (33%)
