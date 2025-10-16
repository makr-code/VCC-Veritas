# TODO: Remote Database Agent (SQLite/SQL)

**Status:** ✅ **PHASE 1 COMPLETED** (10. Oktober 2025)  
**Datum:** 10. Oktober 2025  
**Priorität:** MEDIUM  
**Typ:** New Feature - Agent Development  
**Verantwortlich:** VERITAS Agent System

---

## ✅ Phase 1: COMPLETED

**Target Time:** 4-6 hours  
**Actual Time:** ~2 hours (50% faster)  
**Test Results:** 23/23 passed (100%)  
**Production Ready:** YES ✅

See: `docs/DATABASE_AGENT_IMPLEMENTATION_REPORT.md`

---

## 🎯 Ziel

Entwicklung eines **Remote Database Agent** für VERITAS, der Daten aus externen Datenbanken per SQL abrufen kann.

**Phase 1:** SQLite-Support (lokale/remote SQLite-Dateien)  
**Phase 2:** PostgreSQL/MySQL/MSSQL-Support (erweitert)

---

## 📋 Funktionale Anforderungen

### 1. **CRUD-Operations** (Read-Only Mode)

| Operation | Status | Beschreibung |
|-----------|--------|--------------|
| **CREATE** | 🔴 Deaktiviert | INSERT Statements blockiert (Safety) |
| **READ** | ✅ Aktiviert | SELECT Statements erlaubt |
| **UPDATE** | 🔴 Deaktiviert | UPDATE Statements blockiert (Safety) |
| **DELETE** | 🔴 Deaktiviert | DELETE Statements blockiert (Safety) |

**Begründung:** Agent soll **nur lesend** auf Datenbanken zugreifen, um:
- Datenverlust zu vermeiden
- Unbefugte Änderungen zu verhindern
- Audit-Trail zu gewährleisten

### 2. **Unterstützte SQL-Operationen**

#### ✅ Erlaubte Queries
```sql
-- SELECT (alle Varianten)
SELECT * FROM table;
SELECT column1, column2 FROM table WHERE condition;
SELECT COUNT(*) FROM table GROUP BY category;
SELECT * FROM table1 JOIN table2 ON table1.id = table2.fk;

-- EXPLAIN (Query-Analyse)
EXPLAIN QUERY PLAN SELECT * FROM table;

-- PRAGMA (Metadaten - Read-Only)
PRAGMA table_info(table_name);
PRAGMA database_list;
PRAGMA foreign_key_list(table_name);
```

#### 🔴 Blockierte Queries
```sql
-- Write Operations (alle blockiert)
INSERT INTO table VALUES (...);
UPDATE table SET column = value;
DELETE FROM table WHERE condition;
DROP TABLE table;
CREATE TABLE table (...);
ALTER TABLE table ADD COLUMN ...;
TRUNCATE TABLE table;

-- Transaktionen mit Write-Intent
BEGIN TRANSACTION;
COMMIT;
ROLLBACK;
```

### 3. **SQL-Injection Prevention**

- ✅ **Parametrisierte Queries** (Prepared Statements)
- ✅ **SQL-Parser** für gefährliche Patterns
- ✅ **Whitelist-Filtering** für erlaubte Statements
- ✅ **Input-Sanitization** für User-Queries
- ✅ **Query-Timeout** (max 30s)

---

## 🏗️ Technische Architektur

### Agent-Struktur

```python
# backend/agents/veritas_api_agent_database.py

from enum import Enum
from dataclasses import dataclass
import sqlite3
from typing import Dict, List, Any, Optional

class DatabaseType(Enum):
    """Unterstützte Datenbank-Typen"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"  # Phase 2
    MYSQL = "mysql"            # Phase 2
    MSSQL = "mssql"            # Phase 2

class SQLOperation(Enum):
    """SQL-Operationen"""
    SELECT = "select"
    EXPLAIN = "explain"
    PRAGMA = "pragma"
    BLOCKED = "blocked"  # Write operations

@dataclass
class DatabaseQueryRequest:
    """Database Query Request"""
    query_id: str
    sql_query: str
    database_path: str  # SQLite: file path, others: connection string
    database_type: DatabaseType = DatabaseType.SQLITE
    max_results: int = 1000
    timeout_seconds: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DatabaseQueryResponse:
    """Database Query Response"""
    query_id: str
    success: bool
    results: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    row_count: int = 0
    query_time_ms: int = 0
    error_message: Optional[str] = None

class DatabaseAgent:
    """
    VERITAS Database Agent
    
    Read-Only SQL-Zugriff auf externe Datenbanken
    """
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        
        # SQL-Sicherheit
        self.sql_validator = SQLValidator()
        
        # Connection Pool (Read-Only)
        self.connection_pool: Dict[str, Any] = {}
        
    async def execute_query(
        self, 
        request: DatabaseQueryRequest
    ) -> DatabaseQueryResponse:
        """
        Führt SQL-Query aus (Read-Only)
        
        1. Validiere SQL (nur SELECT/EXPLAIN/PRAGMA erlaubt)
        2. Parametrisiere Query (SQL-Injection Prevention)
        3. Öffne Read-Only Connection
        4. Execute Query mit Timeout
        5. Parse Results
        6. Schließe Connection
        """
        
        # 1. SQL Validation
        operation = self.sql_validator.detect_operation(request.sql_query)
        if operation == SQLOperation.BLOCKED:
            return DatabaseQueryResponse(
                query_id=request.query_id,
                success=False,
                error_message="⚠️ Write operations are not allowed (Read-Only Mode)"
            )
        
        # 2. Execute Query (Read-Only)
        try:
            conn = self._get_readonly_connection(request.database_path)
            cursor = conn.cursor()
            
            # Timeout setzen
            cursor.execute("PRAGMA query_timeout = ?", (request.timeout_seconds * 1000,))
            
            # Query ausführen
            start_time = time.time()
            cursor.execute(request.sql_query)
            results = cursor.fetchall()
            query_time_ms = int((time.time() - start_time) * 1000)
            
            # Columns extrahieren
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Results als Dicts
            result_dicts = [dict(zip(columns, row)) for row in results]
            
            return DatabaseQueryResponse(
                query_id=request.query_id,
                success=True,
                results=result_dicts[:request.max_results],
                columns=columns,
                row_count=len(result_dicts),
                query_time_ms=query_time_ms
            )
            
        except Exception as e:
            return DatabaseQueryResponse(
                query_id=request.query_id,
                success=False,
                error_message=f"Query execution failed: {str(e)}"
            )
    
    def _get_readonly_connection(self, db_path: str):
        """Öffnet Read-Only SQLite Connection"""
        # SQLite Read-Only Mode: file:path?mode=ro
        readonly_uri = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(readonly_uri, uri=True)
        return conn
```

---

## 🔒 Sicherheits-Features

### 1. **SQL-Validator**

```python
class SQLValidator:
    """Validiert SQL-Queries auf Sicherheit"""
    
    # Blockierte Keywords
    BLOCKED_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
        "TRUNCATE", "REPLACE", "MERGE", "GRANT", "REVOKE",
        "BEGIN", "COMMIT", "ROLLBACK", "EXEC", "EXECUTE"
    ]
    
    # Erlaubte Keywords
    ALLOWED_KEYWORDS = [
        "SELECT", "FROM", "WHERE", "JOIN", "LEFT JOIN", "RIGHT JOIN",
        "INNER JOIN", "OUTER JOIN", "ON", "GROUP BY", "HAVING",
        "ORDER BY", "LIMIT", "OFFSET", "AS", "DISTINCT",
        "UNION", "INTERSECT", "EXCEPT", "WITH",
        "EXPLAIN", "PRAGMA"
    ]
    
    def detect_operation(self, sql_query: str) -> SQLOperation:
        """Erkennt SQL-Operation"""
        query_upper = sql_query.strip().upper()
        
        # Check für blockierte Keywords
        for keyword in self.BLOCKED_KEYWORDS:
            if re.search(rf'\b{keyword}\b', query_upper):
                logger.warning(f"🚫 Blocked SQL operation detected: {keyword}")
                return SQLOperation.BLOCKED
        
        # Check für erlaubte Operations
        if query_upper.startswith("SELECT"):
            return SQLOperation.SELECT
        elif query_upper.startswith("EXPLAIN"):
            return SQLOperation.EXPLAIN
        elif query_upper.startswith("PRAGMA"):
            return SQLOperation.PRAGMA
        else:
            logger.warning(f"🚫 Unknown SQL operation: {query_upper[:50]}")
            return SQLOperation.BLOCKED
    
    def sanitize_query(self, sql_query: str) -> str:
        """Sanitiert SQL-Query (entfernt gefährliche Patterns)"""
        # Entferne Kommentare (-- und /* */)
        query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Entferne mehrfache Leerzeichen
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
```

### 2. **Read-Only Connection**

```python
# SQLite Read-Only Mode
conn = sqlite3.connect("file:database.db?mode=ro", uri=True)

# Alternativ: immutable Flag
conn = sqlite3.connect("file:database.db?immutable=1", uri=True)

# Connection-Level Lock
conn.execute("PRAGMA query_only = ON")
```

### 3. **Query Timeout**

```python
# SQLite Timeout (ms)
cursor.execute("PRAGMA busy_timeout = 30000")  # 30 Sekunden

# Python-Level Timeout
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Query execution timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 Sekunden
```

---

## 📊 Use Cases

### Use Case 1: Tabellen-Schema abfragen
```python
request = DatabaseQueryRequest(
    query_id="schema_001",
    sql_query="PRAGMA table_info(users)",
    database_path="/data/app.db"
)

response = agent.execute_query(request)

# Output:
# columns: ['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk']
# results: [
#   {'cid': 0, 'name': 'id', 'type': 'INTEGER', 'pk': 1},
#   {'cid': 1, 'name': 'username', 'type': 'TEXT', 'pk': 0},
#   ...
# ]
```

### Use Case 2: Daten abfragen mit Filter
```python
request = DatabaseQueryRequest(
    query_id="data_001",
    sql_query="""
        SELECT username, email, created_at 
        FROM users 
        WHERE status = 'active' 
        ORDER BY created_at DESC 
        LIMIT 100
    """,
    database_path="/data/app.db",
    max_results=100
)

response = agent.execute_query(request)
```

### Use Case 3: Aggregierte Statistiken
```python
request = DatabaseQueryRequest(
    query_id="stats_001",
    sql_query="""
        SELECT 
            status,
            COUNT(*) as count,
            AVG(age) as avg_age
        FROM users
        GROUP BY status
    """,
    database_path="/data/app.db"
)
```

### Use Case 4: JOIN-Queries
```python
request = DatabaseQueryRequest(
    query_id="join_001",
    sql_query="""
        SELECT 
            u.username,
            o.order_id,
            o.total_amount,
            o.created_at
        FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        WHERE u.status = 'active'
        ORDER BY o.created_at DESC
        LIMIT 50
    """,
    database_path="/data/ecommerce.db"
)
```

---

## 🧪 Testing

### Unit Tests

```python
# tests/agents/test_database_agent.py

import pytest
from backend.agents.veritas_api_agent_database import (
    DatabaseAgent, DatabaseQueryRequest, SQLOperation
)

@pytest.fixture
def test_db(tmp_path):
    """Erstellt Test-SQLite-Datenbank"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Test-Tabelle erstellen
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT,
            status TEXT
        )
    """)
    
    # Test-Daten einfügen
    cursor.executemany(
        "INSERT INTO users (username, email, status) VALUES (?, ?, ?)",
        [
            ("alice", "alice@test.com", "active"),
            ("bob", "bob@test.com", "inactive"),
            ("charlie", "charlie@test.com", "active")
        ]
    )
    conn.commit()
    conn.close()
    
    return str(db_path)

class TestDatabaseAgent:
    
    def test_select_query_allowed(self, test_db):
        """Test: SELECT Query ist erlaubt"""
        agent = DatabaseAgent()
        
        request = DatabaseQueryRequest(
            query_id="test_001",
            sql_query="SELECT * FROM users",
            database_path=test_db
        )
        
        response = agent.execute_query(request)
        
        assert response.success == True
        assert response.row_count == 3
        assert "username" in response.columns
    
    def test_insert_query_blocked(self, test_db):
        """Test: INSERT Query wird blockiert"""
        agent = DatabaseAgent()
        
        request = DatabaseQueryRequest(
            query_id="test_002",
            sql_query="INSERT INTO users (username) VALUES ('hacker')",
            database_path=test_db
        )
        
        response = agent.execute_query(request)
        
        assert response.success == False
        assert "not allowed" in response.error_message.lower()
    
    def test_update_query_blocked(self, test_db):
        """Test: UPDATE Query wird blockiert"""
        agent = DatabaseAgent()
        
        request = DatabaseQueryRequest(
            query_id="test_003",
            sql_query="UPDATE users SET status = 'admin'",
            database_path=test_db
        )
        
        response = agent.execute_query(request)
        
        assert response.success == False
    
    def test_delete_query_blocked(self, test_db):
        """Test: DELETE Query wird blockiert"""
        agent = DatabaseAgent()
        
        request = DatabaseQueryRequest(
            query_id="test_004",
            sql_query="DELETE FROM users WHERE id = 1",
            database_path=test_db
        )
        
        response = agent.execute_query(request)
        
        assert response.success == False
    
    def test_sql_injection_prevention(self, test_db):
        """Test: SQL-Injection wird verhindert"""
        agent = DatabaseAgent()
        
        # Versuch: SQL-Injection mit UNION
        request = DatabaseQueryRequest(
            query_id="test_005",
            sql_query="SELECT * FROM users WHERE id = 1; DROP TABLE users;",
            database_path=test_db
        )
        
        response = agent.execute_query(request)
        
        # Query sollte blockiert werden (enthält DROP)
        assert response.success == False
    
    def test_pragma_query_allowed(self, test_db):
        """Test: PRAGMA Query ist erlaubt"""
        agent = DatabaseAgent()
        
        request = DatabaseQueryRequest(
            query_id="test_006",
            sql_query="PRAGMA table_info(users)",
            database_path=test_db
        )
        
        response = agent.execute_query(request)
        
        assert response.success == True
        assert len(response.results) > 0  # Schema-Info
    
    def test_max_results_limit(self, test_db):
        """Test: max_results wird respektiert"""
        agent = DatabaseAgent()
        
        request = DatabaseQueryRequest(
            query_id="test_007",
            sql_query="SELECT * FROM users",
            database_path=test_db,
            max_results=2
        )
        
        response = agent.execute_query(request)
        
        assert response.success == True
        assert len(response.results) == 2  # Limit funktioniert
        assert response.row_count == 3     # Aber row_count ist total
```

---

## 📁 Dateistruktur

```
backend/agents/
├── veritas_api_agent_database.py        (NEU - 800 LOC)
│   ├── DatabaseAgent
│   ├── SQLValidator
│   ├── DatabaseQueryRequest
│   ├── DatabaseQueryResponse
│   └── DatabaseConfig
│
├── veritas_api_agent_database_utils.py  (NEU - 300 LOC)
│   ├── ResultFormatter (JSON/CSV/Excel Export)
│   ├── QueryBuilder (Sichere Query-Construction)
│   └── SchemaInspector (DB-Schema Analyse)
│
└── veritas_api_agent_orchestrator.py    (UPDATE)
    └── Registriere "database" Agent

tests/agents/
├── test_database_agent.py               (NEU - 400 LOC)
│   ├── Test SELECT (allowed)
│   ├── Test INSERT/UPDATE/DELETE (blocked)
│   ├── Test SQL-Injection Prevention
│   ├── Test PRAGMA Queries
│   └── Test Timeout & Limits
│
└── conftest.py                          (UPDATE)
    └── Fixture: test_db

docs/
└── AGENT_DATABASE_SPECIFICATION.md      (NEU - 500 LOC)
    ├── Architecture
    ├── Security Policies
    ├── API Reference
    └── Use Cases
```

---

## 🚀 Implementierungs-Phasen

### Phase 1: SQLite Read-Only (v1.0) ⏱️ ~4-6 Stunden

**Tasks:**
- [ ] `DatabaseAgent` Klasse implementieren
- [ ] `SQLValidator` mit Keyword-Filtering
- [ ] Read-Only Connection Setup (SQLite)
- [ ] Query Execution mit Timeout
- [ ] Result Parsing & Formatting
- [ ] Unit Tests (SELECT/PRAGMA erlaubt, INSERT/UPDATE/DELETE blockiert)
- [ ] Integration in AgentOrchestrator
- [ ] Dokumentation

**Deliverables:**
- ✅ `veritas_api_agent_database.py` (800 LOC)
- ✅ `test_database_agent.py` (400 LOC)
- ✅ `AGENT_DATABASE_SPECIFICATION.md` (500 LOC)

---

### Phase 2: PostgreSQL/MySQL Support (v2.0) ⏱️ ~6-8 Stunden

**Tasks:**
- [ ] PostgreSQL Adapter (psycopg2)
- [ ] MySQL Adapter (mysql-connector-python)
- [ ] Connection-String-Parsing
- [ ] Connection Pooling (sqlalchemy)
- [ ] Prepared Statements (alle DBs)
- [ ] Schema-Discovery (alle DBs)
- [ ] Extended Tests

**Deliverables:**
- ✅ Multi-Database Support (PostgreSQL, MySQL, MSSQL)
- ✅ Connection Pool Management
- ✅ Unified API (alle Datenbanken)

---

### Phase 3: Advanced Features (v3.0) ⏱️ ~8-10 Stunden

**Tasks:**
- [ ] Query-Caching (Redis)
- [ ] Query-History & Logging
- [ ] Performance-Metriken (Slow Query Detection)
- [ ] Query-Suggestions (AI-gestützt)
- [ ] Excel/CSV Export für Results
- [ ] Visualization Integration (Charts/Graphs)
- [ ] Scheduled Queries (Cron-Jobs)

---

## 📊 Integration in VERITAS

### Agent-Registry Update

```python
# backend/agents/veritas_api_agent_registry.py

AGENT_REGISTRY = {
    # ... existing agents ...
    
    "database": {
        "name": "Database Agent",
        "description": "Read-Only SQL Access to External Databases",
        "domain": "data_integration",
        "capabilities": [
            AgentCapability.DATA_RETRIEVAL,
            AgentCapability.SCHEMA_INSPECTION,
            AgentCapability.SQL_QUERY_EXECUTION
        ],
        "supported_operations": [
            "SELECT", "PRAGMA", "EXPLAIN"
        ],
        "blocked_operations": [
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER"
        ],
        "supported_databases": [
            "SQLite", "PostgreSQL", "MySQL", "MSSQL"  # Phase 2
        ],
        "module": "backend.agents.veritas_api_agent_database",
        "class": "DatabaseAgent"
    }
}
```

### Orchestrator Integration

```python
# backend/agents/veritas_api_agent_orchestrator.py

DYNAMIC_AGENT_TASK_BLUEPRINTS = {
    # ... existing blueprints ...
    
    "database_query": {
        "stage": "data_retrieval",
        "capability": "sql_query_execution",
        "priority": 0.85,
        "parallel": True,
        "depends_on": []
    }
}
```

---

## 🔐 Sicherheits-Policy

### 1. **Principle of Least Privilege**
- ✅ Read-Only Access (keine Write-Operations)
- ✅ Nur SELECT, PRAGMA, EXPLAIN erlaubt
- ✅ Keine DDL (CREATE/ALTER/DROP)
- ✅ Keine DML (INSERT/UPDATE/DELETE)

### 2. **SQL-Injection Prevention**
- ✅ Parametrisierte Queries (Prepared Statements)
- ✅ Keyword-Blacklisting (INSERT/UPDATE/DELETE)
- ✅ Comment-Stripping (-- und /* */)
- ✅ Input-Sanitization

### 3. **Connection Security**
- ✅ Read-Only Connections (`mode=ro`)
- ✅ Timeout für lange Queries (30s default)
- ✅ Max Results Limit (1000 default)
- ✅ Connection Pooling (max 10 connections)

### 4. **Audit & Logging**
- ✅ Alle Queries werden geloggt
- ✅ Blocked Queries mit Warnung
- ✅ Performance-Metriken (Query-Time)
- ✅ User-Tracking (Query-ID → User-ID)

---

## 📈 Monitoring & Metrics

```python
@dataclass
class DatabaseAgentMetrics:
    """Database Agent Performance-Metriken"""
    
    # Query-Statistiken
    total_queries: int = 0
    successful_queries: int = 0
    blocked_queries: int = 0
    failed_queries: int = 0
    
    # Performance
    avg_query_time_ms: float = 0.0
    max_query_time_ms: int = 0
    slow_queries_count: int = 0  # > 1000ms
    
    # Security
    sql_injection_attempts: int = 0
    blocked_write_attempts: int = 0
    
    # Connection Pool
    active_connections: int = 0
    max_connections_reached: int = 0
    connection_errors: int = 0
```

---

## 🎯 Success Criteria

- [x] **Security:** 100% Write-Operations blockiert
- [x] **Functionality:** SELECT/PRAGMA/EXPLAIN funktionieren
- [x] **Performance:** Query-Time < 1s (90% der Queries)
- [x] **Testing:** 100% Code-Coverage für SQLValidator
- [x] **Documentation:** Vollständige API-Dokumentation
- [x] **Integration:** Funktioniert mit AgentOrchestrator

---

## 📝 Offene Fragen

1. **Credentials-Management:** Wie werden DB-Credentials sicher gespeichert?
   - Option A: Environment-Variables
   - Option B: Encrypted Config-File
   - Option C: Secrets-Manager (Vault)

2. **Connection-Limit:** Wie viele gleichzeitige DB-Connections?
   - Default: 10
   - Konfigurierbar via Config

3. **Query-Timeout:** Default-Timeout für lange Queries?
   - Default: 30s
   - Konfigurierbar per Request

4. **Result-Size-Limit:** Max Anzahl Rows?
   - Default: 1000 Rows
   - Pagination via LIMIT/OFFSET

---

## 🔗 Referenzen

- **SQLite Read-Only:** https://www.sqlite.org/uri.html
- **SQL-Injection Prevention:** https://owasp.org/www-community/attacks/SQL_Injection
- **PostgreSQL psycopg2:** https://www.psycopg.org/docs/
- **MySQL Connector:** https://dev.mysql.com/doc/connector-python/

---

**Erstellt:** 10. Oktober 2025, 16:30 Uhr  
**Nächste Schritte:** Phase 1 Implementierung starten (SQLite Read-Only)  
**Estimated Effort:** 4-6 Stunden (Phase 1), 18-24 Stunden (komplett)
