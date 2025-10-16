# Database Agent - Quick Start Guide

**Version:** 1.0.0  
**Date:** 10. Oktober 2025  
**Status:** Production Ready ✅

---

## 📚 Overview

The VERITAS Database Agent provides **read-only SQL access** to SQLite databases with comprehensive security features.

**Key Features:**
- ✅ Read-only SQL queries (SELECT, PRAGMA, EXPLAIN)
- 🔒 Write operations blocked (INSERT/UPDATE/DELETE)
- 🛡️ SQL-Injection prevention
- ⚡ Query caching (optional)
- 📊 Statistics & monitoring
- 🔌 REST API endpoints

---

## 🚀 Quick Start

### 1. Import the Agent

```python
from backend.agents.veritas_api_agent_database import (
    create_database_agent,
    DatabaseQueryRequest,
    DatabaseConfig
)
```

### 2. Create Agent Instance

```python
# Use defaults
agent = create_database_agent()

# Or custom config
config = DatabaseConfig(
    max_results=500,
    default_timeout_seconds=15,
    enable_query_cache=True
)
agent = create_database_agent(config)
```

### 3. Execute Query

```python
# Create request
request = DatabaseQueryRequest(
    query_id="query_001",
    sql_query="SELECT * FROM users WHERE status = 'active' LIMIT 10",
    database_path="/path/to/database.db",
    max_results=10,
    timeout_seconds=30
)

# Execute (async)
response = await agent.execute_query(request)

# Check results
if response.success:
    print(f"Found {response.row_count} rows")
    for row in response.results:
        print(row)
else:
    print(f"Error: {response.error_message}")
```

---

## 📖 Examples

### Example 1: Simple SELECT

```python
request = DatabaseQueryRequest(
    query_id="ex1",
    sql_query="SELECT id, username, email FROM users",
    database_path="./data/app.db"
)

response = await agent.execute_query(request)

# Access results
for user in response.results:
    print(f"{user['id']}: {user['username']} ({user['email']})")
```

### Example 2: Aggregate Query

```python
request = DatabaseQueryRequest(
    query_id="ex2",
    sql_query="""
        SELECT category, COUNT(*) as count 
        FROM documents 
        GROUP BY category 
        ORDER BY count DESC
    """,
    database_path="./data/documents.db"
)

response = await agent.execute_query(request)

for row in response.results:
    print(f"{row['category']}: {row['count']} documents")
```

### Example 3: Get Table Schema

```python
request = DatabaseQueryRequest(
    query_id="ex3",
    sql_query="PRAGMA table_info(users)",
    database_path="./data/app.db"
)

response = await agent.execute_query(request)

print("Table Columns:")
for col in response.results:
    print(f"  {col['name']} ({col['type']})")
```

### Example 4: Include Schema in Response

```python
request = DatabaseQueryRequest(
    query_id="ex4",
    sql_query="SELECT * FROM users LIMIT 1",
    database_path="./data/app.db",
    include_schema=True  # Get schema metadata
)

response = await agent.execute_query(request)

# Access schema
schema = response.table_schema
print(f"Table: {schema['table_name']}")
for col in schema['columns']:
    print(f"  {col['name']}: {col['type']} (PK: {col['primary_key']})")
```

### Example 5: Blocked Query (Security)

```python
request = DatabaseQueryRequest(
    query_id="ex5",
    sql_query="DELETE FROM users WHERE id = 1",  # Blocked!
    database_path="./data/app.db"
)

response = await agent.execute_query(request)

# response.success = False
# response.status = QueryStatus.BLOCKED
# response.blocked_reason = "⚠️ Write operations are not allowed (Read-Only Mode)"
```

---

## 🔌 REST API Usage

### Start Backend

First, ensure the Database Agent endpoints are registered in your FastAPI app:

```python
from backend.api.database_endpoints import get_database_router

app = FastAPI()
app.include_router(get_database_router())
```

### API Examples

#### 1. Execute Query

```bash
curl -X POST http://localhost:5000/api/database/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql_query": "SELECT * FROM users WHERE status = '\''active'\'' LIMIT 10",
    "database_path": "/data/app.db",
    "max_results": 10,
    "timeout_seconds": 30
  }'
```

**Response:**
```json
{
  "query_id": "db_query_abc123",
  "success": true,
  "status": "success",
  "results": [
    {
      "id": 1,
      "username": "alice",
      "email": "alice@example.com",
      "status": "active"
    }
  ],
  "columns": ["id", "username", "email", "status"],
  "column_types": ["INTEGER", "TEXT", "TEXT", "TEXT"],
  "row_count": 1,
  "total_rows": 1,
  "query_time_ms": 5
}
```

#### 2. Validate Query (No Execution)

```bash
curl -X POST http://localhost:5000/api/database/validate \
  -H "Content-Type: application/json" \
  -d '{
    "sql_query": "SELECT id, name FROM users"
  }'
```

**Response:**
```json
{
  "valid": true,
  "sql_operation": "select",
  "error_message": null,
  "warnings": []
}
```

#### 3. Get Agent Status

```bash
curl http://localhost:5000/api/database/status
```

**Response:**
```json
{
  "agent_name": "DatabaseAgent",
  "version": "1.0.0",
  "database_type": "SQLite",
  "read_only_mode": true,
  "available": true,
  "stats": {
    "total_queries": 42,
    "successful_queries": 38,
    "blocked_queries": 4,
    "failed_queries": 0,
    "avg_query_time_ms": 12.5,
    "cache_hits": 15
  },
  "config": {
    "max_results": 1000,
    "default_timeout_seconds": 30,
    "enable_query_cache": true
  },
  "cache_size": 15
}
```

#### 4. Get Table Schema

```bash
curl -X POST "http://localhost:5000/api/database/schema/users?database_path=/data/app.db"
```

**Response:**
```json
{
  "table_name": "users",
  "columns": [
    {
      "name": "id",
      "type": "INTEGER",
      "not_null": true,
      "default_value": null,
      "primary_key": true
    },
    {
      "name": "username",
      "type": "TEXT",
      "not_null": true,
      "default_value": null,
      "primary_key": false
    }
  ]
}
```

#### 5. Clear Cache

```bash
curl -X DELETE http://localhost:5000/api/database/cache
```

**Response:**
```json
{
  "success": true,
  "message": "Query cache cleared",
  "previous_cache_size": 15
}
```

---

## 🛡️ Security Guide

### Allowed Operations

✅ **SELECT** - Data retrieval
```sql
SELECT * FROM table;
SELECT column1, column2 FROM table WHERE condition;
SELECT COUNT(*) FROM table GROUP BY category;
```

✅ **PRAGMA** - Database/table metadata (read-only)
```sql
PRAGMA table_info(table_name);
PRAGMA database_list;
PRAGMA foreign_key_list(table_name);
```

✅ **EXPLAIN** - Query execution plan
```sql
EXPLAIN QUERY PLAN SELECT * FROM table;
```

### Blocked Operations

🔴 **INSERT** - Data insertion
```sql
INSERT INTO users (username) VALUES ('alice');  -- BLOCKED
```

🔴 **UPDATE** - Data modification
```sql
UPDATE users SET status = 'admin';  -- BLOCKED
```

🔴 **DELETE** - Data deletion
```sql
DELETE FROM users WHERE id = 1;  -- BLOCKED
```

🔴 **DROP/CREATE/ALTER** - Schema changes
```sql
DROP TABLE users;  -- BLOCKED
CREATE TABLE new_table (...);  -- BLOCKED
ALTER TABLE users ADD COLUMN ...;  -- BLOCKED
```

### SQL-Injection Prevention

The agent **automatically blocks** dangerous patterns:

```python
# Blocked: Multi-statement attack
"SELECT * FROM users; DROP TABLE users; --"

# Blocked: Command execution
"SELECT * FROM users WHERE id = 1; EXEC xp_cmdshell(...)"

# Allowed: Safe parametrization (future feature)
"SELECT * FROM users WHERE id = ?"
```

**Security Layers:**
1. Keyword blacklisting (15+ keywords)
2. Pattern detection (8+ dangerous patterns)
3. Comment stripping (`--`, `/* */`)
4. SQLite read-only mode (`mode=ro`)
5. PRAGMA enforcement (`query_only = ON`)

---

## ⚙️ Configuration

### DatabaseConfig Options

```python
config = DatabaseConfig(
    # Query Limits
    max_results=1000,                 # Max rows returned (1-10000)
    default_timeout_seconds=30,       # Query timeout (1-300s)
    max_query_length=10000,           # Max SQL chars
    
    # Security
    read_only_mode=True,              # Always True (enforced)
    enable_write_operations=False,    # Always False (enforced)
    
    # Connection Pool (future)
    max_connections=10,
    connection_timeout_seconds=60,
    
    # Performance
    enable_query_cache=True,          # Enable result caching
    cache_ttl_seconds=300,            # Cache TTL (5min default)
    max_cache_size=100,               # Max cached queries
    
    # Logging
    log_all_queries=True,             # Log all queries
    log_blocked_queries=True,         # Log blocked attempts
    log_slow_queries_ms=1000          # Slow query threshold (1s)
)
```

### Environment Variables

```bash
# Future: Database connection settings
export DB_AGENT_MAX_RESULTS=500
export DB_AGENT_TIMEOUT=15
export DB_AGENT_CACHE_ENABLED=true
```

---

## 📊 Monitoring

### Get Agent Statistics

```python
status = agent.get_status()

print(f"Total Queries: {status['stats']['total_queries']}")
print(f"Successful: {status['stats']['successful_queries']}")
print(f"Blocked: {status['stats']['blocked_queries']}")
print(f"Avg Time: {status['stats']['avg_query_time_ms']}ms")
print(f"Cache Hits: {status['stats']['cache_hits']}")
```

### Track Query Performance

```python
response = await agent.execute_query(request)

print(f"Query Time: {response.query_time_ms}ms")
print(f"Rows Returned: {response.row_count}")
print(f"Total Rows: {response.total_rows}")
```

### Clear Cache Manually

```python
agent.clear_cache()
```

---

## 🧪 Testing

### Run Unit Tests

```bash
# All tests
python -m pytest tests/test_database_agent.py -v

# Specific test
python -m pytest tests/test_database_agent.py::TestDatabaseAgent::test_simple_select -v

# With coverage
python -m pytest tests/test_database_agent.py --cov=backend.agents.veritas_api_agent_database
```

### Standalone Test Suite

```bash
python backend/agents/veritas_api_agent_database.py
```

**Expected Output:**
```
🗄️  VERITAS Database Agent - Test Suite
============================================================
✅ Test 1: Select all users (5 rows)
✅ Test 2: Select active users (3 rows)
✅ Test 3: Aggregate query (2 groups)
✅ Test 4: Get table schema (5 columns)
✅ Test 5: INSERT blocked ✅
✅ Test 6: UPDATE blocked ✅
✅ Test 7: DELETE blocked ✅
✅ Test 8: DROP TABLE blocked ✅

📊 Agent Status:
   Total Queries: 8
   Successful: 4
   Blocked: 4
   Failed: 0
```

---

## 🔧 Troubleshooting

### Issue: "Database file not found"

**Error:**
```
FileNotFoundError: Database file not found or not readable: /path/to/db.db
```

**Solution:**
- Verify file exists: `ls -la /path/to/db.db`
- Check file permissions: `chmod 644 /path/to/db.db`
- Use absolute path (not relative)

### Issue: Query timeout

**Error:**
```
QueryStatus.TIMEOUT: Query timeout after 30s
```

**Solution:**
- Increase timeout: `timeout_seconds=60`
- Optimize query (add indexes)
- Check database locks

### Issue: "Database locked"

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
- Close other connections to DB
- Use WAL mode: `PRAGMA journal_mode=WAL;`
- Increase timeout: `PRAGMA busy_timeout = 5000;`

### Issue: Cache not working

**Problem:** Cache hits = 0

**Solution:**
- Enable cache: `config.enable_query_cache = True`
- Verify cache key (same query + db_path)
- Check TTL: `config.cache_ttl_seconds = 300`

---

## 📚 Additional Resources

- **Implementation Report:** `docs/DATABASE_AGENT_IMPLEMENTATION_REPORT.md`
- **TODO List:** `TODO_AGENT_DATABASE.md`
- **API Documentation:** `backend/api/database_endpoints.py`
- **Unit Tests:** `tests/test_database_agent.py`

---

## 🤝 Support

**Questions?** Check:
1. This Quick Start Guide
2. Implementation Report (detailed docs)
3. Unit tests (usage examples)
4. Inline code documentation

**Issues?** Create GitHub Issue with:
- Database Agent version (1.0.0)
- SQL query (sanitized)
- Error message
- Expected vs actual behavior

---

**Author:** VERITAS Agent System  
**Version:** 1.0.0  
**Date:** 10. Oktober 2025  
**Status:** Production Ready ✅
