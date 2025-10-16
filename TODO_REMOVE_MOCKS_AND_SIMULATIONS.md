# TODO: Mockups und Simulationen Entfernen

**Datum:** 13. Oktober 2025  
**Status:** 🔴 OPEN - Kritische Code Quality Aufgabe  
**Priorität:** HIGH  
**Geschätzte Zeit:** 12-20 Stunden

---

## 📋 Executive Summary

Umfassende Analyse und Entfernung von **Mockups, Simulationen, Fallback-Modi und Test-Daten** aus dem Production Code. Identifizierung von Code-Bereichen, die für Production-Deployment durch echte Implementierungen ersetzt werden müssen.

**Kategorien:**
1. ✅ **Test Mocks** - OK für Tests (behalten)
2. 🟡 **Development Fallbacks** - Production-Ready machen
3. 🔴 **Fake Implementations** - Durch echte ersetzen
4. ⚠️ **Stub Services** - Implementieren oder entfernen

---

## 🎯 Ziele

### Kurzfristig (Phase 1: 4-6h)
- [ ] **ChromaDB Fallback-Modus entfernen** (KRITISCH - BEREITS BEGONNEN)
- [ ] **PKI Mock-Implementierung** durch echte ersetzen
- [ ] **Database Agent Mocks** identifizieren und ersetzen
- [ ] **API Endpoint Stubs** vervollständigen

### Mittelfristig (Phase 2: 6-8h)
- [ ] **UDS3 Fallback-Docs** zu echten ChromaDB-Daten migrieren
- [ ] **Agent Framework Mockups** zu Production überführen
- [ ] **LLM Parameter Fallbacks** optimieren
- [ ] **Test-Data Generation** in Seeds umwandeln

### Langfristig (Phase 3: 4-6h)
- [ ] **Code Review** aller `mock`, `fake`, `stub` Referenzen
- [ ] **Documentation Update** (Mock → Production Notes)
- [ ] **Integration Tests** ohne Mocks schreiben
- [ ] **Production Readiness Checklist** abarbeiten

---

## 🔍 Kategorisierung nach Fundstellen

### 1. ✅ ChromaDB Fallback-Modus (IN PROGRESS)

**Status:** 🟡 TEILWEISE BEHOBEN (12.10.2025, 22:00 Uhr)

**Betroffene Dateien:**
- `uds3/database/database_api_chromadb_remote.py` - ✅ **NO FALLBACK MODE** implementiert
- `docs/CHROMADB_NO_FALLBACK_IMPLEMENTATION.md` - ✅ Dokumentation erstellt (2,000+ Zeilen)

**Was wurde gemacht:**
- ✅ `_fallback_mode` Variable komplett entfernt
- ✅ `connect()` wirft RuntimeError bei Verbindungsfehlern
- ✅ `is_available()` gibt False zurück (kein RuntimeError)
- ✅ Alle Methoden: Keine Fallback-Checks mehr
- ✅ Test Suite erstellt: `tests/test_chromadb_hard_fail.py`

**Verbleibende Aufgaben:**
- [ ] **Backend Integration:** Fehlerbehandlung für ChromaDB-Ausfälle
  - Graceful Degradation auf Graph-Only Search
  - User-Notification bei Vector Search Unavailable
  - Monitoring/Alerting für ChromaDB Connection Errors
  
- [ ] **Production Monitoring:**
  - ChromaDB Health Checks (heartbeat every 30s)
  - Auto-Restart bei Connection Loss
  - Fallback zu Neo4j-Only bei ChromaDB Down

**Dateien mit Fallback-Referenzen:**
```
TODO.md:632    - ⚠️ ChromaDB: Fallback docs (Remote API issue - known problem)
TODO.md:678    - ⚠️ **ChromaDB:** Fallback docs (Remote API issue)
TODO.md:805      ✅ ChromaDB: Active (fallback mode)
```

**Aufgabe:**
```markdown
- [ ] TODO.md aktualisieren: Fallback-Modus Referenzen entfernen
- [ ] Backend Error Handling: Graceful Degradation implementieren
- [ ] Production Guide: ChromaDB Monitoring-Setup dokumentieren
```

---

### 2. 🔴 PKI Mock-Implementierung (KRITISCH)

**Status:** 🔴 NICHT IMPLEMENTIERT (Nur Mockups vorhanden)

**Betroffene Dateien:**
```
TODO_PKI_INTEGRATION.md:20    3. **Mock-Implementierung** für Entwicklung/Tests
TODO_PKI_INTEGRATION.md:36    │   ├── cert_manager.py          # Certificate management (mock)
TODO_PKI_INTEGRATION.md:37    │   ├── ca_service.py            # CA service interface (mock)
TODO_PKI_INTEGRATION.md:38    │   ├── crypto_utils.py          # Cryptographic utilities (mock)
TODO_PKI_INTEGRATION.md:80    PKI_MOCK_MODE = os.getenv("PKI_MOCK_MODE", "true").lower() == "true"
```

**Mock-Komponenten:**

#### 2.1 Certificate Manager (Mock)
**Datei:** `backend/pki/cert_manager.py`

**Mock-Funktionen:**
```python
class CertificateManager:
    """Mock Certificate Manager"""
    
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self._mock_certs: Dict[str, Dict[str, Any]] = {}
    
    def create_certificate(self, subject: str, validity_days: int = 365):
        """Erstellt ein neues Zertifikat (Mock)"""
        # TODO: Echte Implementierung mit cryptography library
        pass
    
    def revoke_certificate(self, cert_id: str):
        """Widerruft ein Zertifikat (Mock)"""
        # TODO: CRL Management
        pass
    
    def get_certificate_info(self, cert_id: str):
        """Ruft Zertifikat-Details ab (Mock)"""
        # TODO: X.509 Parsing
        pass
```

**Aufgaben:**
- [ ] **Phase 1 (4h):** Mock-Klasse implementieren (In-Memory Storage)
- [ ] **Phase 2 (8h):** Echte cryptography-basierte Implementierung
  - X.509 Certificate Generation
  - CSR Handling
  - Certificate Chain Validation
  - CRL Management
- [ ] **Phase 3 (4h):** CA Integration (e.g., Let's Encrypt, Internal CA)
- [ ] **Tests:** Unit Tests für alle Certificate Operations

#### 2.2 CA Service (Mock)
**Datei:** `backend/pki/ca_service.py`

**Mock-Funktionen:**
```python
class CAService:
    """Mock Certificate Authority Service"""
    
    def initialize_ca(self):
        """Initialisiert die CA (Mock)"""
        pass
    
    def sign_csr(self, csr_data: str):
        """Signiert einen CSR (Mock)"""
        pass
    
    def get_ca_certificate(self):
        """Ruft CA-Zertifikat ab (Mock)"""
        pass
```

**Aufgaben:**
- [ ] **Phase 1 (3h):** Mock-CA mit In-Memory Keys
- [ ] **Phase 2 (10h):** Echte CA-Implementierung
  - Root CA Setup
  - Intermediate CA Handling
  - Certificate Signing Logic
  - OCSP Responder
- [ ] **Phase 3 (6h):** CA Service Integration
  - HSM Support (Hardware Security Module)
  - Automated Certificate Renewal
  - Policy Engine

#### 2.3 Crypto Utils (Mock)
**Datei:** `backend/pki/crypto_utils.py`

**Mock-Funktionen:**
```python
def generate_keypair(key_size: int = 2048):
    """Generiert RSA-Schlüsselpaar (Mock)"""
    return ("mock_private_key", "mock_public_key")

def encrypt_data(data: str, public_key: str):
    """Verschlüsselt Daten (Mock)"""
    return f"encrypted_{data}"

def sign_data(data: str, private_key: str):
    """Signiert Daten (Mock)"""
    return f"signature_of_{data}"
```

**Aufgaben:**
- [ ] **Phase 1 (2h):** Mock-Implementierung mit Plausible Data
- [ ] **Phase 2 (4h):** Echte cryptography-Implementierung
  - RSA Key Generation (2048/4096 bit)
  - AES Encryption (GCM mode)
  - Digital Signatures (PKCS#1, PSS)
  - Hash Functions (SHA-256, SHA-384, SHA-512)
- [ ] **Phase 3 (2h):** Performance Optimization
  - Key Caching
  - Hardware Acceleration (OpenSSL)

**Geschätzte Zeit PKI-Migration:** 40-50 Stunden

---

### 3. 🟡 Agent Framework Mockups

**Status:** 🟡 MOCKUP EXISTIERT (Integration ausstehend)

**Betroffene Dateien:**
```
VERITAS_AGENT_FRAMEWORK_INTEGRATION_TODO.md:4    **Source:** `codespaces-blank/` Mockup Implementation
VERITAS_AGENT_FRAMEWORK_INTEGRATION_TODO.md:14   ### Key Features des Mockup-Systems:
VERITAS_AGENT_FRAMEWORK_INTEGRATION_TODO.md:80   **Verdict:** 🔴 **Significant architectural gap** - Mockup is **2-3 generations ahead**!
```

**Mockup-Komponenten:**

#### 3.1 Multi-Agent Framework (Mockup)
**Location:** `codespaces-blank/` directory

**Gap-Analyse:**
```markdown
| Component | Current Implementation | Mockup Equivalent | Gap |
|-----------|------------------------|-------------------|-----|
| Agent Registry | ❌ None | ✅ Central Registry | 🔴 HIGH |
| Agent Communication | 🟡 Direct Calls | ✅ Message Bus | 🔴 HIGH |
| Agent Orchestration | 🟡 Manual | ✅ Supervisor Pattern | 🟡 MEDIUM |
| Agent State Management | ❌ Stateless | ✅ State Machine | 🔴 HIGH |
| Agent Pipeline | 🟡 Sequential | ✅ DAG-based | 🟡 MEDIUM |
```

**Aufgaben:**
- [ ] **Gap Analysis (4h):** Detaillierter Vergleich Veritas vs. Mockup
  - Feature-Matrix erstellen
  - Code-Metriken vergleichen
  - Architecture Diagrams
  
- [ ] **Integration Strategy (8h):**
  - Agent Registry implementieren (zentrales Register)
  - Message Bus einführen (Agent-to-Agent Communication)
  - Supervisor Pattern (Orchestration Layer)
  - State Machine (Agent Lifecycle Management)
  
- [ ] **Migration Plan (12h):**
  - Environmental Agent → Mockup-Pattern
  - Financial Agent → Mockup-Pattern
  - Social Agent → Mockup-Pattern
  - Traffic Agent → Mockup-Pattern
  
- [ ] **Testing (8h):**
  - Integration Tests für Agent Communication
  - Performance Tests (Message Bus Latency)
  - Stress Tests (100+ concurrent agents)

**Verweise:**
```
VERITAS_AGENT_FRAMEWORK_INTEGRATION_TODO.md:154   - Mappe auf Mockup-Agenten
VERITAS_AGENT_FRAMEWORK_INTEGRATION_TODO.md:1187  - **Mockup:** `c:/VCC/veritas/codespaces-blank/`
```

**Geschätzte Zeit Agent-Migration:** 32-40 Stunden

---

### 4. 🟡 Database Agent Mocks

**Status:** 🟡 TEILWEISE IMPLEMENTIERT (Test Mocks vorhanden)

**Betroffene Dateien:**
```
tests/test_uds3_search_api.py:41    class MockVectorBackend:
tests/test_uds3_search_api.py:69    class MockGraphBackend:
tests/test_uds3_search_api.py:101   class MockRelationalBackend:
tests/test_uds3_search_api.py:116   class MockUnifiedStrategy:
```

**Analyse:**
- ✅ **Test Mocks:** OK für Unit Tests (behalten)
- ⚠️ **Production Code:** Keine Mocks gefunden (gut!)
- 🟡 **Integration Tests:** Sollten echte Databases nutzen

**Aufgaben:**
- [ ] **Integration Test Suite (4h):**
  - Echte PostgreSQL-Tests (mit Test-DB)
  - Echte Neo4j-Tests (mit Test-Graph)
  - Echte ChromaDB-Tests (mit Test-Collection)
  
- [ ] **Test Data Management (3h):**
  - Database Seeds erstellen (SQL, Cypher, JSON)
  - Test Data Isolation (separate Test-Schemas)
  - Teardown/Cleanup Automation
  
- [ ] **CI/CD Integration (3h):**
  - Docker Compose für Test-Databases
  - Test Database Initialization Scripts
  - Parallel Test Execution

**Verweise:**
```
TODO_AGENT_DATABASE.md:397    # tests/agents/test_database_agent.py
TODO_AGENT_DATABASE.md:567    ├── test_database_agent.py (NEU - 400 LOC)
```

**Geschätzte Zeit Database Tests:** 10-12 Stunden

---

### 5. 🟡 LLM Parameter Fallbacks

**Status:** 🟡 DEVELOPMENT FALLBACKS (Production-Ready machen)

**Betroffene Dateien:**
```
TODO_LLM_PARAMETER_EXTENSIONS.md:224    return 2.0, 6.0  # Fallback
tests/test_rag_quality_v3_19_0.py:92    print("📌 Verwende Fallback-Modelle")
```

**Analyse:**

#### 5.1 Temperature/Top-P Fallbacks
**Code:**
```python
def get_temperature_range(model_name: str) -> Tuple[float, float]:
    """Get recommended temperature range for model"""
    if "llama" in model_name.lower():
        return 0.7, 1.2
    elif "mistral" in model_name.lower():
        return 0.5, 1.0
    else:
        return 2.0, 6.0  # Fallback ← PROBLEM: Zu hoch!
```

**Problem:**
- Fallback-Werte (2.0-6.0) sind unrealistisch hoch
- Sollte conservative defaults sein (0.7-1.0)

**Aufgaben:**
- [ ] **Fallback-Werte korrigieren (1h):**
  ```python
  # BEFORE
  return 2.0, 6.0  # Fallback
  
  # AFTER
  return 0.7, 1.0  # Conservative fallback for unknown models
  ```

- [ ] **Model Registry erstellen (3h):**
  - Comprehensive Model Database (temperature, top-p, context_length)
  - Model Capabilities Mapping
  - Auto-Detection für neue Models
  
- [ ] **Tests aktualisieren (2h):**
  - Fallback-Werte validieren
  - Model-Specific Tests

#### 5.2 RAG Quality Test Fallbacks
**Code:**
```python
# tests/test_rag_quality_v3_19_0.py:92
print("📌 Verwende Fallback-Modelle")
```

**Analyse:**
- Test nutzt Fallback-Modelle wenn Primär-Modelle nicht verfügbar
- OK für Development, aber Production sollte definierte Models haben

**Aufgaben:**
- [ ] **Production Model Config (2h):**
  - Definiere Production-Models (llama3.1:8b, etc.)
  - Environment-basierte Model Selection
  - Health Checks für Model Availability
  
- [ ] **Test Configuration (2h):**
  - Separate Test-Models Config
  - Mock-LLM für Unit Tests
  - Real-LLM für Integration Tests

**Geschätzte Zeit LLM Fallbacks:** 10-12 Stunden

---

### 6. 🟡 Test Data & Sample Data

**Status:** 🟡 OK FÜR TESTS (Seeds für Production erstellen)

**Betroffene Dateien:**
```
test_office_export.py:21     # Sample Data
test_comprehensive_sql.py:32  # Setup test data
test_chat_persistence_ui.py:29  test_data = [...]
```

**Analyse:**
- ✅ **Test Files:** Sample/Test Data ist OK
- 🟡 **Production Seeds:** Fehlen noch

**Aufgaben:**

#### 6.1 Production Database Seeds (6h)
- [ ] **PostgreSQL Seeds:**
  - `seeds/postgresql/01_schema.sql` - Database Schema
  - `seeds/postgresql/02_initial_data.sql` - Initial Production Data
  - `seeds/postgresql/03_test_data.sql` - Test Data (optional)
  
- [ ] **Neo4j Seeds:**
  - `seeds/neo4j/01_constraints.cypher` - Graph Constraints
  - `seeds/neo4j/02_initial_nodes.cypher` - Initial Graph Data
  - `seeds/neo4j/03_relationships.cypher` - Graph Relationships
  
- [ ] **ChromaDB Seeds:**
  - `seeds/chromadb/01_collections.json` - Collection Definitions
  - `seeds/chromadb/02_embeddings.json` - Initial Embeddings (optional)

#### 6.2 Seed Management System (4h)
- [ ] **Seed Runner Script:**
  ```python
  # scripts/run_seeds.py
  import argparse
  
  def run_seeds(env: str = "development"):
      """Run database seeds for specified environment"""
      if env == "production":
          # Load production seeds
          pass
      elif env == "test":
          # Load test seeds
          pass
  ```

- [ ] **Environment-based Seeds:**
  - Development: Sample Data (100 docs)
  - Test: Test Data (50 docs, known results)
  - Production: Minimal Initial Data (0-10 docs)

**Geschätzte Zeit Seeds:** 10-12 Stunden

---

### 7. 🟡 API Endpoint Stubs

**Status:** 🟡 TEILWEISE IMPLEMENTIERT

**Betroffene Dateien:**
```
TODO_PKI_INTEGRATION.md:432    # Endpoints (Mock-Implementation)
TODO_PKI_INTEGRATION.md:467    - [ ] Mock-Endpoints implementieren
```

**Fehlende Endpoints:**

#### 7.1 PKI Endpoints (Stubs)
```python
# backend/api/pki_endpoints.py (STUB)

@router.post("/pki/certificates")
async def create_certificate(subject: str):
    """Create new certificate (STUB)"""
    # TODO: Implement using CertificateManager
    return {"status": "not_implemented"}

@router.delete("/pki/certificates/{cert_id}")
async def revoke_certificate(cert_id: str):
    """Revoke certificate (STUB)"""
    # TODO: Implement CRL management
    return {"status": "not_implemented"}
```

**Aufgaben:**
- [ ] **PKI Endpoints implementieren (8h):**
  - POST /pki/certificates - Create Certificate
  - GET /pki/certificates/{id} - Get Certificate Info
  - DELETE /pki/certificates/{id} - Revoke Certificate
  - GET /pki/ca/certificate - Get CA Certificate
  - GET /pki/crl - Get Certificate Revocation List
  
- [ ] **OpenAPI Documentation (2h):**
  - Swagger/OpenAPI Schemas
  - Example Requests/Responses
  - Authentication Requirements

#### 7.2 Map Integration Endpoints (Planned)
```
TODO_MAP_INTEGRATION.md:379    placeholder="Ort, Betriebsstätte..."
```

**Aufgaben:**
- [ ] **Map Endpoints implementieren (6h):**
  - GET /maps/geocode - Geocoding Service
  - GET /maps/tiles/{z}/{x}/{y} - Tile Service
  - POST /maps/markers - Add Map Markers
  
- [ ] **Offline Fallback (4h):**
  - Local Tile Cache
  - Graceful Degradation bei API Failure

**Geschätzte Zeit API Endpoints:** 20-24 Stunden

---

## 📊 Priorisierung nach Impact

### 🔥 KRITISCH (Sofort angehen)

1. **ChromaDB Fallback-Modus** (4h verbleibend)
   - ✅ Code: FIXED (No Fallback Mode)
   - ⏳ Backend Integration: TODO
   - ⏳ Production Monitoring: TODO
   - **Impact:** 🔥 HIGH - Betrifft Vector Search
   - **Risk:** 🔥 HIGH - Production Crashes ohne Error Handling

2. **PKI Mock → Production** (40-50h)
   - ⏳ Certificate Manager: TODO
   - ⏳ CA Service: TODO
   - ⏳ Crypto Utils: TODO
   - **Impact:** 🔥 HIGH - Security Feature
   - **Risk:** 🔥 CRITICAL - Mock = No Security

3. **LLM Parameter Fallbacks** (10-12h)
   - ⏳ Temperature Defaults korrigieren
   - ⏳ Model Registry erstellen
   - **Impact:** 🔥 MEDIUM - Betrifft LLM Quality
   - **Risk:** 🟡 MEDIUM - Fallback-Werte zu hoch

### 🟡 WICHTIG (Mittelfristig)

4. **Agent Framework Integration** (32-40h)
   - ⏳ Gap Analysis
   - ⏳ Integration Strategy
   - ⏳ Migration Plan
   - **Impact:** 🟡 HIGH - Architecture Improvement
   - **Risk:** 🟢 LOW - Mockup funktioniert

5. **Database Seeds & Test Data** (10-12h)
   - ⏳ PostgreSQL Seeds
   - ⏳ Neo4j Seeds
   - ⏳ Seed Runner
   - **Impact:** 🟡 MEDIUM - Development Experience
   - **Risk:** 🟢 LOW - Kein Production Impact

6. **API Endpoint Stubs** (20-24h)
   - ⏳ PKI Endpoints
   - ⏳ Map Endpoints
   - **Impact:** 🟡 MEDIUM - Feature Completeness
   - **Risk:** 🟡 MEDIUM - Stubs = Not Functional

### 🟢 NIEDRIG (Langfristig)

7. **Database Agent Integration Tests** (10-12h)
   - ⏳ Echte PostgreSQL Tests
   - ⏳ Echte Neo4j Tests
   - ⏳ CI/CD Integration
   - **Impact:** 🟢 MEDIUM - Test Coverage
   - **Risk:** 🟢 LOW - Test Mocks funktionieren

8. **Documentation Updates** (4-6h)
   - ⏳ Mock → Production Notes
   - ⏳ Architecture Diagrams
   - **Impact:** 🟢 LOW - Documentation Quality
   - **Risk:** 🟢 NONE

---

## 🗓️ Zeitplan

### Phase 1: Kritische Fixes (2-3 Tage, 18-24h)

**Woche 1:**
- [ ] ChromaDB Backend Integration (4h)
- [ ] PKI Mock-Implementierung Phase 1 (Mock-Klassen) (12h)
- [ ] LLM Parameter Fallbacks korrigieren (10h)

**Deliverables:**
- ✅ ChromaDB Production-Ready (mit Error Handling)
- ✅ PKI Mock-Klassen lauffähig (In-Memory)
- ✅ LLM Conservative Defaults

### Phase 2: Wichtige Features (1-2 Wochen, 60-80h)

**Woche 2-3:**
- [ ] PKI Echte Implementierung (30h)
- [ ] Agent Framework Integration (32h)
- [ ] API Endpoint Stubs implementieren (20h)

**Deliverables:**
- ✅ PKI Production-Ready (cryptography-basiert)
- ✅ Agent Framework Migration Complete
- ✅ PKI & Map Endpoints funktionsfähig

### Phase 3: Test & Documentation (1 Woche, 20-30h)

**Woche 4:**
- [ ] Database Seeds & Test Data (10h)
- [ ] Integration Tests ohne Mocks (10h)
- [ ] Documentation Updates (6h)

**Deliverables:**
- ✅ Production Database Seeds
- ✅ Comprehensive Integration Tests
- ✅ Updated Documentation

---

## ✅ Success Criteria

### Code Quality
- [ ] Keine `mock_mode` Flags in Production Code
- [ ] Keine `fallback` Logic für kritische Features
- [ ] Alle `TODO: Implement` Comments entfernt
- [ ] Alle Stubs durch echte Implementierung ersetzt

### Testing
- [ ] 100% Integration Test Coverage (ohne Mocks)
- [ ] Production Database Seeds vorhanden
- [ ] CI/CD Pipeline nutzt echte Test-DBs
- [ ] Load Tests mit Production-ähnlichen Daten

### Documentation
- [ ] Alle Mock-Referenzen dokumentiert
- [ ] Migration Guides erstellt (Mock → Production)
- [ ] Production Deployment Guide aktualisiert
- [ ] Known Limitations dokumentiert

### Production Readiness
- [ ] PKI: Echte Certificate Management
- [ ] ChromaDB: Production Error Handling
- [ ] LLM: Conservative Parameter Defaults
- [ ] Agents: Production-Grade Communication

---

## 📚 Referenzen

### Dokumentation
- `docs/CHROMADB_NO_FALLBACK_IMPLEMENTATION.md` - ChromaDB Hard Fail Mode
- `docs/CHROMADB_V2_COMPLETE_SUMMARY.md` - ChromaDB v2 API Implementation
- `TODO_PKI_INTEGRATION.md` - PKI Integration Plan
- `VERITAS_AGENT_FRAMEWORK_INTEGRATION_TODO.md` - Agent Framework Migration

### Code
- `uds3/database/database_api_chromadb_remote.py` - ChromaDB Client (NO FALLBACK)
- `tests/test_chromadb_hard_fail.py` - ChromaDB Hard Fail Tests
- `backend/pki/` - PKI Mock Implementation (TODO)
- `codespaces-blank/` - Agent Framework Mockup

### Tests
- `tests/test_uds3_search_api.py` - UDS3 Search API Tests (mit Mocks)
- `tests/test_chromadb_v2_api.py` - ChromaDB v2 API Tests
- `tests/test_pki/` - PKI Tests (TODO)

---

## 🚨 Warnings & Risks

### ⚠️ Critical Risks

1. **PKI Mock in Production:**
   - **Risk:** Keine echte Verschlüsselung/Signierung
   - **Impact:** CRITICAL - Security Breach möglich
   - **Mitigation:** PKI Phase 1 (Mock) schnellstmöglich durch Phase 2 (Real) ersetzen

2. **ChromaDB Fallback ohne Error Handling:**
   - **Risk:** Backend Crashes bei ChromaDB Ausfall
   - **Impact:** HIGH - Service Unavailable
   - **Mitigation:** Graceful Degradation zu Graph-Only Search implementieren

3. **LLM Parameter Fallbacks zu hoch:**
   - **Risk:** Unvorhersehbare LLM Outputs
   - **Impact:** MEDIUM - Quality Issues
   - **Mitigation:** Conservative Defaults (0.7-1.0) setzen

### 🟡 Medium Risks

4. **Agent Framework Mockup-Gap:**
   - **Risk:** Architecture 2-3 Generationen hinter Mockup
   - **Impact:** MEDIUM - Technical Debt
   - **Mitigation:** Schrittweise Migration (32h geplant)

5. **Test Mocks statt echte Databases:**
   - **Risk:** Tests validieren nicht Production Behavior
   - **Impact:** MEDIUM - False Confidence
   - **Mitigation:** Integration Tests mit echten DBs

### 🟢 Low Risks

6. **API Endpoint Stubs:**
   - **Risk:** Features nicht verfügbar
   - **Impact:** LOW - Users wissen dass Features fehlen
   - **Mitigation:** Clear Error Messages ("Not Implemented")

---

## 📞 Next Steps

### Sofort (Diese Woche)

1. **ChromaDB Backend Integration (4h)**
   ```python
   # backend/api/search_endpoints.py
   try:
       results = await chromadb.search_similar(query)
   except RuntimeError as e:
       # Graceful Degradation: Fallback to Graph-Only Search
       logger.warning(f"ChromaDB unavailable: {e}, falling back to Neo4j")
       results = await neo4j.search_similar(query)
   ```

2. **LLM Parameter Fix (1h)**
   ```python
   # backend/services/llm_service.py
   def get_temperature_range(model_name: str):
       # ...
       else:
           return 0.7, 1.0  # FIXED: Conservative fallback
   ```

3. **PKI Mock Phase 1 Start (4h)**
   ```bash
   mkdir -p backend/pki
   touch backend/pki/__init__.py
   touch backend/pki/cert_manager.py
   touch backend/pki/ca_service.py
   touch backend/pki/crypto_utils.py
   ```

### Nächste Woche (Phase 1 Complete)

4. **PKI Mock-Klassen implementieren (12h)**
5. **LLM Model Registry erstellen (4h)**
6. **Database Seeds erstellen (6h)**

---

**Erstellt:** 13. Oktober 2025  
**Autor:** Code Quality Team  
**Review:** Pending  
**Status:** 🔴 OPEN - HIGH PRIORITY

**Total Geschätzte Zeit:** 160-200 Stunden (4-5 Wochen)  
**Empfehlung:** Staffelung in 3 Phasen (kritisch → wichtig → nice-to-have)
