# VERITAS Microservices Architecture

**Version:** 4.0.0
**Datum:** 19. Oktober 2025
**Prinzip:** Klare Trennung der Verantwortlichkeiten (Separation of Concerns)

---

## 🎯 Architektur-Übersicht

VERITAS folgt einer **strikten Microservices-Architektur** mit klarer Verantwortlichkeitstrennung:

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: APPLICATION LAYER (VERITAS)                        │
│ ─────────────────────────────────────────────────────────── │
│ • Query Processing                                           │
│ • Agent Orchestration (15 Agents)                           │
│ • User Interface                                             │
│ • Business Logic                                             │
│                                                              │
│ Verantwortlichkeit:                                          │
│ → Gibt NUR an, WELCHE Backends benötigt werden              │
│ → KEINE Credentials                                          │
│ → KEINE Connection-Details                                   │
│ → KEINE Database-Konfiguration                               │
└──────────────────┬──────────────────────────────────────────┘
                   │ {"vector": {"enabled": True},
                   │  "graph": {"enabled": True}, ...}
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: DATA MICROSERVICE (UDS3)                           │
│ ─────────────────────────────────────────────────────────── │
│ • Polyglot Persistence Management                            │
│ • Backend Orchestration                                      │
│ • RAG Pipeline                                               │
│ • LLM Integration (Ollama)                                   │
│                                                              │
│ Verantwortlichkeit:                                          │
│ → Verwaltet WELCHE Backends verfügbar sind                  │
│ → Koordiniert Backend-Operationen                            │
│ → Stellt einheitliche API bereit                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: CONNECTION POOL MANAGER                            │
│ ─────────────────────────────────────────────────────────── │
│ • database_manager.py                                        │
│ • Lädt zentrale Config (uds3/database/config.py)            │
│ • Merged Config mit Request                                  │
│ • Erstellt Backend-Instanzen                                 │
│                                                              │
│ Verantwortlichkeit:                                          │
│ → Lädt ECHTE Credentials aus zentraler Config               │
│ → Verwaltet Backend-Factories                                │
│ → Autostart-Logik                                            │
└──────────────────┬──────────────────────────────────────────┘
                   │ {host, port, username, password, ...}
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: DATABASE APIS                                       │
│ ─────────────────────────────────────────────────────────── │
│ • database_api_neo4j.py      → Graph DB                     │
│ • database_api_chromadb.py   → Vector DB                    │
│ • database_api_postgresql.py → Relational DB                │
│ • database_api_couchdb.py    → Document DB                  │
│                                                              │
│ Verantwortlichkeit:                                          │
│ → Verwalten Connection Pools                                 │
│ → Implementieren DB-spezifische Logik                        │
│ → Nutzen Credentials aus Config                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: DATABASES (Remote Instances)                       │
│ ─────────────────────────────────────────────────────────── │
│ • Neo4j:       192.168.178.94:7687                          │
│ • PostgreSQL:  192.168.178.94:5432                          │
│ • ChromaDB:    192.168.178.94:8000                          │
│ • CouchDB:     192.168.178.94:32769                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Zentrale Konfiguration

### **Standort:** `uds3/database/config.py`

**Diese Datei ist die EINZIGE Quelle für Database-Credentials!**

```python
# uds3/database/config.py

class DatabaseManager:
    """Manager für Database-Konfigurationen"""

    def _load_default_config(self):
        """Lade Standard-Konfiguration mit ECHTEN Credentials"""

        self.databases = [
            # Vector Database - ChromaDB (Remote)
            DatabaseConnection(
                db_type=DatabaseType.VECTOR,
                backend=DatabaseBackend.CHROMADB,
                host=os.getenv('CHROMA_CLIENT_HOST', '192.168.178.94'),
                port=int(os.getenv('CHROMA_CLIENT_PORT', 8000)),
                settings={
                    'mode': 'persistent',
                    'similarity_threshold': 0.3
                }
            ),

            # Graph Database - Neo4j (Remote)
            DatabaseConnection(
                db_type=DatabaseType.GRAPH,
                backend=DatabaseBackend.NEO4J,
                host=os.getenv('NEO4J_HOST', '192.168.178.94'),
                port=int(os.getenv('NEO4J_PORT', 7687)),
                username=os.getenv('NEO4J_USERNAME', 'neo4j'),
                password=os.getenv('NEO4J_PASSWORD', 'v3f3b1d7'),
                database=os.getenv('NEO4J_DATABASE', 'neo4j'),
                settings={
                    'uri': os.getenv('NEO4J_URI', 'neo4j://192.168.178.94:7687')
                }
            ),

            # Relational Database - PostgreSQL (Remote)
            DatabaseConnection(
                db_type=DatabaseType.RELATIONAL,
                backend=DatabaseBackend.POSTGRESQL,
                host=os.getenv('POSTGRES_HOST', '192.168.178.94'),
                port=int(os.getenv('POSTGRES_PORT', 5432)),
                username=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
                database=os.getenv('POSTGRES_DB', 'vcc_relational_prod')
            ),

            # Document Database - CouchDB (Remote)
            DatabaseConnection(
                db_type=DatabaseType.FILE,
                backend=DatabaseBackend.COUCHDB,
                host=os.getenv('COUCHDB_HOST', '192.168.178.94'),
                port=int(os.getenv('COUCHDB_PORT', 32769)),
                username=os.getenv('COUCHDB_USER', 'admin'),
                password=os.getenv('COUCHDB_PASSWORD', 'admin')
            )
        ]
```

---

## 🔄 Request Flow

### **1. VERITAS startet Backend**

```python
# backend/app.py

# VERITAS gibt NUR an, WELCHE Backends es nutzen will
backend_config = {
    "vector": {"enabled": True},      # ChromaDB gewünscht
    "graph": {"enabled": True},       # Neo4j gewünscht
    "relational": {"enabled": True},  # PostgreSQL gewünscht
    "file": {"enabled": True}         # CouchDB gewünscht
}

# UDS3 wird mit minimaler Config initialisiert
app.state.uds3 = UDS3PolyglotManager(
    backend_config=backend_config,  # NUR enabled-Flags!
    enable_rag=True
)
```

**❌ FALSCH:**
```python
# VERITAS sollte KEINE Credentials angeben!
backend_config = {
    "graph": {
        "enabled": True,
        "host": "192.168.178.94",      # ❌ Gehört in config.py
        "port": 7687,                  # ❌ Gehört in config.py
        "username": "neo4j",           # ❌ Gehört in config.py
        "password": "v3f3b1d7"         # ❌ Gehört in config.py
    }
}
```

---

### **2. UDS3 initialisiert DatabaseManager**

```python
# uds3/core/polyglot_manager.py

def __init__(self, backend_config, enable_rag=True):
    # DatabaseManager bekommt nur die enabled-Flags
    self.db_manager = DatabaseManager(backend_config, autostart=True)
```

---

### **3. DatabaseManager lädt zentrale Config**

```python
# uds3/database/database_manager.py

class DatabaseManager:
    def __init__(self, backend_dict, strict_mode=False, autostart=False):
        # ============================================================================
        # ZENTRALE KONFIGURATION LADEN
        # ============================================================================
        # Die zentrale config.py enthält die ECHTEN DB-Credentials
        self.db_config = DBConfigManager()
        self.logger.info("📋 Zentrale Database-Konfiguration geladen")

        # Merge: VERITAS sagt "enabled", Config liefert Credentials
        backend_dict = self._merge_config_with_request(backend_dict)

    def _merge_config_with_request(self, backend_dict: Dict) -> Dict:
        """
        Merge Request (welche Backends aktiviert) mit zentraler Config (echte Credentials).

        Input:  {"vector": {"enabled": True}, "graph": {"enabled": True}}
        Config: {host: "192.168.178.94", port: 7687, username: "neo4j", ...}
        Output: {"vector": {"enabled": True, "host": "...", "port": ..., ...}}
        """
        merged = {}

        for db_conn in self.db_config.databases:
            db_type_str = db_conn.db_type.value  # 'vector', 'graph', ...

            # Prüfe ob VERITAS diesen Backend-Typ angefordert hat
            requested = backend_dict.get(db_type_str, {})
            if isinstance(requested, dict) and requested.get('enabled', False):
                # VERITAS will diesen Backend - nutze zentrale Config
                merged[db_type_str] = db_conn.to_dict()
                self.logger.info(
                    f"✅ {db_type_str.upper()}: {db_conn.backend.value} "
                    f"@ {db_conn.host}:{db_conn.port}"
                )

        return merged
```

**Log-Output:**
```
📋 Zentrale Database-Konfiguration geladen
✅ VECTOR: chromadb @ 192.168.178.94:8000
✅ GRAPH: neo4j @ 192.168.178.94:7687
✅ RELATIONAL: postgresql @ 192.168.178.94:5432
✅ FILE: couchdb @ 192.168.178.94:32769
```

---

### **4. Backend-Instanzen werden erstellt**

```python
# uds3/database/database_manager.py

# Vector Backend
vector_conf = backend_dict.get('vector')
if vector_conf and vector_conf.get('enabled'):
    from uds3.database.database_api_chromadb import ChromaVectorBackend
    conf = {k: v for k, v in vector_conf.items() if k != 'enabled'}
    # conf enthält jetzt: {host: "192.168.178.94", port: 8000, ...}
    self._backend_factories['vector'] = (ChromaVectorBackend, conf)

# Graph Backend
graph_conf = backend_dict.get('graph')
if graph_conf and graph_conf.get('enabled'):
    from uds3.database.database_api_neo4j import Neo4jGraphBackend
    conf = {k: v for k, v in graph_conf.items() if k != 'enabled'}
    # conf enthält jetzt: {host: "192.168.178.94", port: 7687,
    #                      username: "neo4j", password: "v3f3b1d7", ...}
    self._backend_factories['graph'] = (Neo4jGraphBackend, conf)
```

---

### **5. Database APIs nutzen Credentials**

```python
# uds3/database/database_api_neo4j.py

class Neo4jGraphBackend(GraphDatabaseBackend):
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        cfg = config or {}
        settings = cfg.get('settings') or {}

        # Config enthält jetzt die ECHTEN Credentials aus config.py
        self.uri = cfg.get('uri') or settings.get('uri') or 'neo4j://localhost:7687'
        self.user = cfg.get('user') or cfg.get('username') or 'neo4j'
        self.password = cfg.get('password') or ''
        self.database_name = cfg.get('database') or settings.get('db_name')

    def connect(self) -> bool:
        """Connect mit echten Credentials"""
        self._driver = GraphDatabase.driver(
            self.uri,  # neo4j://192.168.178.94:7687
            auth=basic_auth(self.user, self.password)  # neo4j / v3f3b1d7
        )
```

---

## ✅ Korrekte Implementierung

### **DO: VERITAS (Application Layer)**

```python
# backend/app.py

# ✅ Minimale Config - nur enabled-Flags
backend_config = {
    "vector": {"enabled": True},
    "graph": {"enabled": True},
    "relational": {"enabled": True},
    "file": {"enabled": True}
}

app.state.uds3 = UDS3PolyglotManager(
    backend_config=backend_config,
    enable_rag=True
)
```

### **DO: UDS3 (Data Microservice)**

```python
# uds3/core/polyglot_manager.py

# ✅ Gibt Config weiter an DatabaseManager
self.db_manager = DatabaseManager(backend_config, autostart=True)
```

### **DO: Database Manager (Connection Pool)**

```python
# uds3/database/database_manager.py

# ✅ Lädt zentrale Config
from .config import DatabaseManager as DBConfigManager

def __init__(self, backend_dict, ...):
    # ✅ Zentrale Config laden
    self.db_config = DBConfigManager()

    # ✅ Merge mit Request
    backend_dict = self._merge_config_with_request(backend_dict)
```

### **DO: Database Config (Credentials)**

```python
# uds3/database/config.py

# ✅ EINZIGE Quelle für Credentials
DatabaseConnection(
    db_type=DatabaseType.GRAPH,
    backend=DatabaseBackend.NEO4J,
    host='192.168.178.94',
    port=7687,
    username='neo4j',
    password='v3f3b1d7'
)
```

---

## ❌ Falsche Implementierung (Anti-Patterns)

### **DON'T: Credentials in VERITAS**

```python
# ❌ FALSCH - VERITAS sollte KEINE Credentials haben
backend_config = {
    "graph": {
        "enabled": True,
        "uri": "neo4j://192.168.178.94:7687",  # ❌
        "username": "neo4j",                   # ❌
        "password": "v3f3b1d7"                 # ❌
    }
}
```

### **DON'T: Hardcoded Fallbacks in Database APIs**

```python
# ❌ FALSCH - Fallbacks verhindern zentrale Config
class Neo4jGraphBackend:
    def __init__(self, config):
        # ❌ Hardcoded localhost statt config.py
        self.uri = config.get('uri') or 'neo4j://localhost:7687'
        self.user = config.get('username') or 'neo4j'  # ❌ Hardcoded
        self.password = config.get('password') or ''   # ❌ Leer!
```

### **DON'T: Ignorieren der zentralen Config**

```python
# ❌ FALSCH - DatabaseManager ignoriert config.py
class DatabaseManager:
    def __init__(self, backend_dict):
        # ❌ Keine zentrale Config geladen
        # ❌ Nutzt nur backend_dict von VERITAS
        vector_conf = backend_dict.get('vector')
        # ❌ Keine Credentials verfügbar!
```

---

## 🔒 Sicherheits-Prinzipien

### **1. Single Source of Truth**
- **Nur** `uds3/database/config.py` enthält Credentials
- Environment-Variablen als Override-Möglichkeit
- Keine Duplikation von Credentials

### **2. Separation of Concerns**
- **VERITAS:** Was brauche ich? (enabled: true/false)
- **UDS3:** Wie orchestriere ich? (Polyglot Persistence)
- **Database Manager:** Wo sind die Credentials? (config.py)
- **Database APIs:** Wie verbinde ich? (Connection Pools)

### **3. Fail Fast / No Fallback**
- Wenn Config fehlt → **Sofort Fehler**
- Keine silent failures mit localhost-Fallbacks
- Klare Fehlermeldungen mit Lösung

```python
# ✅ Korrekt: Expliziter Fehler
if not config.get('uri'):
    raise ConfigurationError(
        "Neo4j URI nicht konfiguriert! "
        "Bitte in uds3/database/config.py setzen."
    )

# ❌ Falsch: Silent Fallback
uri = config.get('uri') or 'neo4j://localhost:7687'  # ❌
```

---

## 📊 Debugging & Monitoring

### **Config-Check beim Start**

```python
# Beim Backend-Start wird die Config geloggt
📋 Zentrale Database-Konfiguration geladen
✅ VECTOR: chromadb @ 192.168.178.94:8000
✅ GRAPH: neo4j @ 192.168.178.94:7687
✅ RELATIONAL: postgresql @ 192.168.178.94:5432
✅ FILE: couchdb @ 192.168.178.94:32769
```

### **Connection-Status prüfen**

```bash
# Health Check zeigt aktive Connections
curl http://localhost:5000/api/system/health

{
  "status": "healthy",
  "uds3_backends": {
    "vector": {"backend": "ChromaDB", "status": "active", "host": "192.168.178.94"},
    "graph": {"backend": "Neo4j", "status": "active", "host": "192.168.178.94"},
    "relational": {"backend": "PostgreSQL", "status": "active", "host": "192.168.178.94"},
    "file": {"backend": "CouchDB", "status": "active", "host": "192.168.178.94"}
  }
}
```

---

## 🔧 Environment Variables

### **Priority: ENV > config.py**

Environment-Variablen **überschreiben** die Default-Werte in `config.py`:

```bash
# PowerShell
$env:NEO4J_HOST = "192.168.178.95"        # Override Host
$env:NEO4J_PORT = "7688"                  # Override Port
$env:NEO4J_USERNAME = "admin"             # Override Username
$env:NEO4J_PASSWORD = "new_password"      # Override Password

# Bash
export NEO4J_HOST=192.168.178.95
export NEO4J_PORT=7688
```

**Alle unterstützten ENV-Variablen:**

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `CHROMA_CLIENT_HOST` | `192.168.178.94` | ChromaDB Host |
| `CHROMA_CLIENT_PORT` | `8000` | ChromaDB Port |
| `NEO4J_HOST` | `192.168.178.94` | Neo4j Host |
| `NEO4J_PORT` | `7687` | Neo4j Port |
| `NEO4J_USERNAME` | `neo4j` | Neo4j Username |
| `NEO4J_PASSWORD` | `v3f3b1d7` | Neo4j Password |
| `NEO4J_DATABASE` | `neo4j` | Neo4j Database |
| `POSTGRES_HOST` | `192.168.178.94` | PostgreSQL Host |
| `POSTGRES_PORT` | `5432` | PostgreSQL Port |
| `POSTGRES_USER` | `postgres` | PostgreSQL Username |
| `POSTGRES_PASSWORD` | `postgres` | PostgreSQL Password |
| `POSTGRES_DB` | `vcc_relational_prod` | PostgreSQL Database |
| `COUCHDB_HOST` | `192.168.178.94` | CouchDB Host |
| `COUCHDB_PORT` | `32769` | CouchDB Port |
| `COUCHDB_USER` | `admin` | CouchDB Username |
| `COUCHDB_PASSWORD` | `admin` | CouchDB Password |

---

## 🚀 Best Practices

### **1. Neue Database hinzufügen**

```python
# 1. In uds3/database/config.py hinzufügen
DatabaseConnection(
    db_type=DatabaseType.VECTOR,  # oder GRAPH, RELATIONAL, FILE, KEY_VALUE
    backend=DatabaseBackend.NEW_DB,
    host=os.getenv('NEW_DB_HOST', '192.168.178.94'),
    port=int(os.getenv('NEW_DB_PORT', 9999)),
    username=os.getenv('NEW_DB_USER', 'admin'),
    password=os.getenv('NEW_DB_PASSWORD', 'password')
)

# 2. In VERITAS aktivieren (backend/app.py)
backend_config = {
    "vector": {"enabled": True},  # NEW_DB ist vector-type
    ...
}

# 3. Database API implementieren (uds3/database/database_api_new_db.py)
class NewDBBackend(VectorDatabaseBackend):
    def __init__(self, config):
        # Config enthält automatisch Credentials aus config.py
        self.host = config.get('host')
        self.port = config.get('port')
        self.username = config.get('username')
        self.password = config.get('password')
```

### **2. Config-Änderungen testen**

```python
# Test-Script für Config
from uds3.database.config import DatabaseManager as DBConfig

config = DBConfig()
for db in config.databases:
    if db.enabled:
        print(f"{db.db_type.value}: {db.backend.value} @ {db.host}:{db.port}")
        print(f"  User: {db.username}")
        print(f"  Connection String: {db.get_connection_string()}")
```

### **3. Logging aktivieren**

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Zeigt Config-Merge-Prozess
# DatabaseManager loggt:
# - Welche Backends VERITAS anfordert
# - Welche Credentials aus config.py kommen
# - Welche Backend-Instanzen erstellt werden
```

---

## 📝 Migration von alter zu neuer Architektur

### **Alt (Falsch):**
```python
# backend/app.py
backend_config = {
    "graph": {
        "enabled": True,
        "uri": "neo4j://192.168.178.94:7687",  # ❌ Credentials in VERITAS
        "username": "neo4j",
        "password": "v3f3b1d7"
    }
}
```

### **Neu (Korrekt):**

**1. Credentials nach config.py verschieben:**
```python
# uds3/database/config.py
DatabaseConnection(
    db_type=DatabaseType.GRAPH,
    backend=DatabaseBackend.NEO4J,
    host='192.168.178.94',
    port=7687,
    username='neo4j',
    password='v3f3b1d7'
)
```

**2. VERITAS auf minimal Config ändern:**
```python
# backend/app.py
backend_config = {
    "graph": {"enabled": True}  # ✅ Nur enabled-Flag
}
```

**3. DatabaseManager anpassen:**
```python
# uds3/database/database_manager.py
from .config import DatabaseManager as DBConfigManager

def __init__(self, backend_dict, ...):
    self.db_config = DBConfigManager()  # ✅ Config laden
    backend_dict = self._merge_config_with_request(backend_dict)  # ✅ Merge
```

---

## 🎓 Zusammenfassung

### **Kernprinzipien:**

1. **VERITAS** gibt nur an, **WELCHE** Backends benötigt werden
2. **UDS3** orchestriert die Backends
3. **Database Manager** lädt **zentrale Config** aus `uds3/database/config.py`
4. **Database APIs** nutzen die Credentials für Connection Pools
5. **config.py** ist die **EINZIGE Quelle** für Credentials

### **Vorteile:**

- ✅ **Security:** Credentials an einem Ort
- ✅ **Maintainability:** Änderungen nur in config.py
- ✅ **Separation:** Klare Verantwortlichkeiten
- ✅ **Testability:** Einfaches Mocking durch ENV-Variablen
- ✅ **Scalability:** Neue Backends einfach hinzufügen

### **No Fallback Policy:**

- ❌ Keine silent failures
- ❌ Keine localhost-Fallbacks
- ✅ Fail Fast mit klaren Fehlermeldungen
- ✅ Explizite Konfiguration erforderlich

---

**Dokumentiert:** 19. Oktober 2025
**Version:** 4.0.0
**Status:** Production Ready ✅
