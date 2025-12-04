# VERITAS Consolidated Architecture - Current Development State
**Status:** ✅ Production Ready (API v3 - 14 Routers, 58+ Endpoints)  
**Last Updated:** 4. Dezember 2025  
**Version:** 4.0.0  
**API Version:** v3.0.0 (18. Oktober 2025)

---

## 📊 Executive Summary

**VERITAS** is a comprehensive legal information and research system featuring:
- **Frontend:** Tkinter-based GUI with streaming support
- **Backend:** FastAPI with modular v3 API architecture (14 routers, 58+ endpoints)
- **Data Integration:** UDS3 v2.0 + Themis + PostgreSQL + ChromaDB + Neo4j
- **Architecture:** Multi-agent intelligent pipeline with RAG, VPB, and domain-specific adapters

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        VERITAS ECOSYSTEM                           │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────┐         ┌─────────────────────────┐ │
│  │   FRONTEND (Tkinter)    │         │  EXTERNAL APIs/DATA     │ │
│  │  veritas_app.py (1400L) │◄────────┤  • EU LEX              │ │
│  │                         │         │  • Google Search       │ │
│  │  Features:              │         │  • IMMI Geodata        │ │
│  │  • Chat Interface       │         │  • BImSchV Database    │ │
│  │  • Query Modes          │         │  • WKA Database        │ │
│  │  • Streaming Display    │         │  • PostgreSQL (custom) │ │
│  │  • Export/Print         │         │                        │ │
│  └────────────┬────────────┘         └────────────┬────────────┘ │
│               │ HTTP/WebSocket                    │                │
│               ▼                                    ▼                │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │          BACKEND (FastAPI) - backend/app.py               │  │
│  │  Port: 5000 | Version: 4.0.0 | Status: Production       │  │
│  │                                                           │  │
│  │  Middleware:                                            │  │
│  │  • CORS (Frontend/External)                            │  │
│  │  • Rate Limiting                                       │  │
│  │  • Request Logging & Tracing                           │  │
│  │  • Error Handling (Custom HTTPExceptions)              │  │
│  └─────────────────────────────────────────────────────────┘  │
│               │                                                  │
│               ├─ API v3 Router Layer (14 Domain Routers)       │
│               │                                                  │
│  ┌────────────▼──────────────────────────────────────────────┐  │
│  │         API v3 ROUTER LAYER (backend/api/v3/)            │  │
│  │  ✅ PRODUCTION READY - All Routers Implemented          │  │
│  │                                                          │  │
│  │  🔷 CORE OPERATIONS                                    │  │
│  │    • query_router.py      (Query Processing)          │  │
│  │    • agent_router.py      (Agent Management)          │  │
│  │    • system_router.py     (System Info & Health)      │  │
│  │                                                        │  │
│  │  🔷 DOMAIN-SPECIFIC ROUTERS                          │  │
│  │    • vpb_router.py        (VPB Integration)          │  │
│  │    • covina_router.py     (COVINA Queries)          │  │
│  │    • immi_router.py       (IMMI Geodata)            │  │
│  │    • pki_router.py        (PKI Operations)          │  │
│  │    • database_router.py   (Database Access)         │  │
│  │    • uds3_router.py       (UDS3 Queries)            │  │
│  │                                                        │  │
│  │  🔷 ENTERPRISE FEATURES                              │  │
│  │    • themis_router.py     (ThemisDB Integration)    │  │
│  │    • compliance_router.py (Compliance & Audit)      │  │
│  │    • governance_router.py (Governance & Config)     │  │
│  │    • adapter_router.py    (Custom Adapters)        │  │
│  │    • user_router.py       (User Management)         │  │
│  │    • saga_router.py       (SAGA Patterns)          │  │
│  │    • websocket_router.py  (Real-time Streaming)    │  │
│  │                                                        │  │
│  │  📊 Total: 14 Routers | 58+ Endpoints | 5000+ LOC  │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │                                               │
│               ├─ Service Layer                              │
│               │                                               │
│  ┌────────────▼──────────────────────────────────────────────┐  │
│  │       CORE SERVICES (backend/services/)                 │  │
│  │                                                          │  │
│  │  ✓ QueryService              Query orchestration      │  │
│  │  ✓ AgentService              Agent lifecycle mgmt     │  │
│  │  ✓ RAGPipeline               Retrieval-Augmented Gen  │  │
│  │  ✓ IntelligentPipeline       Multi-agent orchestr.   │  │
│  │  ✓ StreamingService          Streaming responses     │  │
│  │  ✓ ExportService             Multi-format export    │  │
│  │  ✓ SearchService             Full-text & semantic   │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │                                              │
│               ├─ Database Layer                             │
│               │                                              │
│  ┌────────────▼──────────────────────────────────────────────┐  │
│  │    DATA INTEGRATION (backend/database/, uds3/)          │  │
│  │                                                          │  │
│  │  🗂️ UDS3 v2.0 (Unified Database Strategy)             │  │
│  │     • UDS3Core: Intelligent DB routing                │  │
│  │     • database_api_*.py: Driver implementations      │  │
│  │     • Strategy patterns per data type                │  │
│  │                                                        │  │
│  │  🗄️ SUPPORTED DATABASES                              │  │
│  │     ✓ PostgreSQL (Default primary DB)               │  │
│  │     ✓ ChromaDB (Vector search)                      │  │
│  │     ✓ Neo4j (Graph queries)                         │  │
│  │     ✓ Elasticsearch (Full-text)                     │  │
│  │     ✓ SQLite (Fallback/testing)                     │  │
│  │     ✓ Themis (Specialized queries)                  │  │
│  │                                                        │  │
│  │  📦 EMBEDDED DATASETS                                │  │
│  │     • BImSchG (DBF files)                            │  │
│  │     • WKA (DBF files)                                │  │
│  │     • Custom SQL fixtures                            │  │
│  └──────────────────────────────────────────────────────┘  │
│               │                                              │
└───────────────┼──────────────────────────────────────────────┘
                │
                ├── 🌐 EXTERNAL INTEGRATIONS
                │   • Google Search API
                │   • EU-Lex Database
                │   • Custom REST APIs
                │
                └── 🎯 DEPLOYMENT
                    • Docker (Dockerfile.production)
                    • Kubernetes (helm/ configs)
                    • Environment-based config

```

---

## 📡 API v3 Endpoint Reference

### 🔷 **QUERY ROUTER** (`query_router.py`) - 5 Endpoints
```
POST /api/v3/query              # Unified query (all modes)
POST /api/v3/query/ask          # Simple Q&A
POST /api/v3/query/rag          # RAG-powered query
POST /api/v3/query/hybrid       # Hybrid search (semantic + keyword)
POST /api/v3/query/stream       # Streaming query response
```
**Response:** Structured response with sources, confidence, citations (IEEE format)

### 🔷 **AGENT ROUTER** (`agent_router.py`) - 4 Endpoints
```
GET  /api/v3/agents/list        # List available agents
GET  /api/v3/agents/{id}/status # Agent status
GET  /api/v3/agents/capabilities # Capabilities matrix
POST /api/v3/agents/{id}/execute # Execute custom agent
```

### 🔷 **SYSTEM ROUTER** (`system_router.py`) - 5 Endpoints
```
GET  /api/v3/system/health       # Health status
GET  /api/v3/system/info         # System information
GET  /api/v3/system/status       # Full status report
GET  /api/v3/system/metrics      # Performance metrics
POST /api/v3/system/config       # Configuration updates
```

### 🔷 **VPB ROUTER** (`vpb_router.py`) - 3 Endpoints
```
POST /api/v3/vpb/analyze        # Analyze VPB data
GET  /api/v3/vpb/models         # List VPB models
POST /api/v3/vpb/predict        # Make predictions
```

### 🔷 **COVINA ROUTER** (`covina_router.py`) - 4 Endpoints
```
POST /api/v3/covina/query       # COVINA domain query
GET  /api/v3/covina/sources     # Available sources
POST /api/v3/covina/validate    # Validate queries
GET  /api/v3/covina/status      # COVINA status
```

### 🔷 **IMMI ROUTER** (`immi_router.py`) - 3 Endpoints
```
GET  /api/v3/immi/markers/bimschg  # BImSchG markers
GET  /api/v3/immi/markers/wka      # WKA markers
POST /api/v3/immi/search           # Spatial search
```

### 🔷 **PKI ROUTER** (`pki_router.py`) - 4 Endpoints
```
POST /api/v3/pki/verify         # Verify signatures
POST /api/v3/pki/encrypt        # Encrypt data
POST /api/v3/pki/decrypt        # Decrypt data
GET  /api/v3/pki/certs          # List certificates
```

### 🔷 **DATABASE ROUTER** (`database_router.py`) - 5 Endpoints
```
GET  /api/v3/database/status    # DB connection status
GET  /api/v3/database/stats     # Database statistics
POST /api/v3/database/query     # Execute custom query
GET  /api/v3/database/schema    # Database schema
POST /api/v3/database/migrate   # Run migrations
```

### 🔷 **UDS3 ROUTER** (`uds3_router.py`) - 4 Endpoints
```
POST /api/v3/uds3/query         # Unified database query
GET  /api/v3/uds3/sources       # Available data sources
POST /api/v3/uds3/optimize      # Optimize query routing
GET  /api/v3/uds3/status        # UDS3 health status
```

### 🔷 **THEMIS ROUTER** (`themis_router.py`) - 5 Endpoints
```
POST /api/v3/themis/query       # ThemisDB query
GET  /api/v3/themis/status      # Themis status
GET  /api/v3/themis/schema      # Themis schema
POST /api/v3/themis/compile     # Compile AQL queries
GET  /api/v3/themis/benchmarks  # Performance data
```

### 🔷 **COMPLIANCE ROUTER** (`compliance_router.py`) - 4 Endpoints
```
GET  /api/v3/compliance/rules   # Compliance rules
POST /api/v3/compliance/check   # Check compliance
GET  /api/v3/compliance/audit   # Audit trail
POST /api/v3/compliance/report  # Generate report
```

### 🔷 **GOVERNANCE ROUTER** (`governance_router.py`) - 3 Endpoints
```
GET  /api/v3/governance/config  # Config management
POST /api/v3/governance/policy  # Policy updates
GET  /api/v3/governance/audit   # Governance audit
```

### 🔷 **ADAPTER ROUTER** (`adapter_router.py`) - 4 Endpoints
```
GET  /api/v3/adapters/list      # List adapters
POST /api/v3/adapters/register  # Register new adapter
POST /api/v3/adapters/{id}/test # Test adapter
DELETE /api/v3/adapters/{id}    # Remove adapter
```

### 🔷 **USER ROUTER** (`user_router.py`) - 4 Endpoints
```
POST /api/v3/users/login        # User authentication
GET  /api/v3/users/profile      # User profile
POST /api/v3/users/preferences  # Update preferences
POST /api/v3/users/logout       # User logout
```

### 🔷 **SAGA ROUTER** (`saga_router.py`) - 3 Endpoints
```
POST /api/v3/saga/execute       # Execute SAGA pattern
GET  /api/v3/saga/{id}/status   # Check SAGA status
POST /api/v3/saga/{id}/rollback # Rollback SAGA
```

### 🔷 **WEBSOCKET ROUTER** (`websocket_router.py`) - 1+ Endpoints
```
WS   /api/v3/ws/streaming       # Real-time streaming
WS   /api/v3/ws/notifications  # System notifications
```

**Total: 14 Routers × ~4 endpoints = 58+ Endpoints**

---

## 🧠 Multi-Agent Intelligent Pipeline

### Architecture
```
User Query
    ↓
[Query Router] Analyzes intent + mode (RAG/VPB/Semantic)
    ↓
[Agent Orchestrator] Selects appropriate agents
    ├─ RAG Agent (Retrieval-Augmented Generation)
    ├─ VPB Agent (Verwaltungsrecht Processing)
    ├─ Domain Agent (Legal domain specialization)
    ├─ Integration Agent (External data sources)
    └─ Search Agent (Full-text + semantic search)
    ↓
[Service Layer] Executes business logic
    ├─ RAGPipeline: Chunk retrieval + ranking + generation
    ├─ SearchService: Multi-database query coordination
    ├─ ExportService: Format conversion (PDF, DOCX, JSON)
    └─ StreamingService: Real-time response delivery
    ↓
[Data Layer] Accesses integrated data
    ├─ UDS3 Router: Intelligent DB selection
    ├─ PostgreSQL: Primary relational data
    ├─ ChromaDB: Vector similarity search
    ├─ Neo4j: Graph relationships
    └─ Themis: Advanced queries
    ↓
Response → Frontend (Streaming or Batch)
```

---

## 📦 Frontend Architecture

### Components
```
frontend/
├── veritas_app.py               # Main GUI (1400 LOC)
│   ├── Chat interface
│   ├── Query modes selector
│   ├── Export/Print functionality
│   └── Settings management
│
├── services/
│   └── backend_api_client.py    # Backend communication
│       ├── Query execution
│       ├── Streaming handling
│       ├── Error retry logic
│       └── Session management
│
└── ui/
    ├── veritas_ui_components.py # UI widgets
    ├── veritas_ui_map_widget.py # Map display (IMMI)
    └── veritas_ui_icons.py      # Icon resources
```

### Query Modes
1. **RAG Mode** - Retrieval-Augmented Generation
2. **VPB Mode** - Verwaltungsrecht Procedure
3. **Semantic Mode** - Semantic similarity search
4. **Keyword Mode** - Full-text search
5. **Hybrid Mode** - Combined search

---

## 🗄️ Data Integration (UDS3 v2.0)

### Unified Database Strategy
```
┌─────────────────────────────────────────┐
│  UDS3 Core (uds3/uds3_core.py)         │
│  • Query routing logic                 │
│  • Database selection strategy         │
│  • Fallback handling                   │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌────────┐┌────────┐┌─────────┐
│ Primary│ Vector │ Graph   │
│  SQL   │ Search │ Storage │
│        │        │         │
│PostgreS│ChromaDB│ Neo4j   │
└────────┘└────────┴─────────┘
```

### Database-Specific Adapters
- **PostgreSQL** (Primary): CRUD operations, transactions, full-text search
- **ChromaDB** (Vector): Embedding similarity, semantic search
- **Neo4j** (Graph): Relationship queries, path finding
- **Elasticsearch** (Full-text): Advanced text search
- **ThemisDB**: Specialized domain queries

### Strategy Patterns
Each data type routes to optimal database:
- Legal documents → PostgreSQL (structured) + ChromaDB (semantic)
- Relationships → Neo4j (graph)
- Full-text → Elasticsearch
- Spatial data → Specialized handlers

---

## 🚀 Deployment Options

### Development
```bash
# Local development
python -m backend.app
# Runs on http://localhost:5000
```

### Docker
```bash
docker build -f Dockerfile.production -t veritas:latest .
docker run -p 5000:8000 veritas:latest
```

### Kubernetes (Helm)
```bash
helm install veritas ./helm
# Configurable via values.yaml
```

### Environment Configuration
- `config/config.py` - Core configuration
- `config/hybrid_search_config.py` - Search configuration
- `config/phase5_config.py` - Deployment-specific
- `.env` - Runtime variables
- `config/prometheus.yml` - Monitoring

---

## 🔧 Configuration & Management

### Core Config (`config/config.py`)
```python
DATABASE_URL = "postgresql://..."
CHROMADB_URL = "http://..."
NEO4J_URL = "neo4j://..."
LLM_MODEL = "gpt-4o"
RAG_CHUNK_SIZE = 1000
STREAMING_ENABLED = True
CORS_ORIGINS = ["http://localhost:3000"]
```

### Services Health Checks
```
GET /api/v3/system/health
→ {"postgres": "connected", "chromadb": "connected", 
   "neo4j": "connected", "status": "healthy"}
```

---

## 📊 Monitoring & Observability

### Metrics Available
- Query latency (p50, p95, p99)
- Agent execution time
- Database query performance
- Cache hit rates
- Error rates by endpoint
- Stream throughput

### Logging
- Structured logging in JSON format
- Request tracing with trace IDs
- Performance logging
- Error context capture

### Prometheus Integration
- Metrics exposed at `/metrics`
- Grafana dashboards available
- Custom alerting rules

---

## 🔐 Security Architecture

### Authentication & Authorization
- **User Router** (`user_router.py`) - Login/logout
- JWT token-based session management
- Role-based access control (RBAC)
- API key authentication for external integrations

### Data Protection
- **PKI Router** (`pki_router.py`) - Encryption/signing
- SSL/TLS for transport
- Data encryption at rest
- Audit logging for compliance

### Request Security
- Rate limiting per endpoint
- CORS policy enforcement
- Input validation (Pydantic models)
- SQL injection prevention

---

## 🧪 Testing Strategy

### Unit Tests
- `tests/test_integration.py` - API integration tests
- `tests/test_domain_routers.py` - Domain router tests
- `tests/test_enterprise_routers.py` - Enterprise feature tests
- `tests/test_phase4_routers.py` - New router tests

### Test Coverage
- Router endpoint tests
- Service layer tests
- Data layer tests
- Integration tests with real databases (CI/CD)

---

## 📈 Performance Characteristics

### Typical Response Times
- Simple queries: 200-500ms
- RAG queries: 1-3s
- Complex domain queries: 3-5s
- Streaming start: 100ms

### Scalability
- **Horizontal:** Docker/Kubernetes scaling
- **Vertical:** Multi-worker configuration
- **Caching:** Redis layer (optional)
- **Load balancing:** Nginx/HAProxy

---

## 🔄 Version History

### Current
- **API v3** (18. Oktober 2025) - PRODUCTION
  - 14 routers, 58+ endpoints
  - UDS3 v2.0 integration complete
  - All domain adapters implemented
  - Streaming & WebSocket support

### Previous
- **API v2** (Deprecated) - Legacy support only
- **API v1** (Archived) - Not recommended

---

## 📝 Development Roadmap

### Q1 2026
- [ ] API v4 migration planning
- [ ] ThemisDB advanced features
- [ ] Performance optimization
- [ ] Enhanced monitoring

### Q2 2026
- [ ] GraphQL support
- [ ] Real-time collaboration
- [ ] Advanced caching strategies
- [ ] Multi-tenant support

---

## 🤝 Contributing

### Adding New Router
1. Create `backend/api/v3/new_router.py`
2. Define Pydantic models in `models.py`
3. Implement endpoints
4. Add tests in `tests/`
5. Update this documentation
6. Submit PR

### Documentation
All changes must include:
- Updated `docs/architecture/CONSOLIDATED_ARCHITECTURE_v4.md`
- Updated endpoint documentation
- API examples
- Tests

---

## 📞 Support & Resources

- **API Docs:** `/docs` (Swagger UI on running instance)
- **Architecture Guide:** `docs/architecture/`
- **API Reference:** `docs/api/API_REFERENCE.md`
- **Integration Guides:** `docs/integration/`
- **Development:** `docs/development/`

---

**Last Verified:** 4. Dezember 2025  
**Documentation Status:** ✅ Current & Accurate  
**Source Code Status:** ✅ Production Ready
