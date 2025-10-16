#!/usr/bin/env python3
"""
VERITAS Database Agent (SQLite Read-Only)
==========================================

Read-Only SQL-Zugriff auf SQLite-Datenbanken mit umfassenden Sicherheits-Features.

Features:
- Read-Only SQL-Queries (SELECT, PRAGMA, EXPLAIN)
- SQL-Injection Prevention
- Write-Operations blockiert (INSERT/UPDATE/DELETE)
- Query-Timeout & Result-Limits
- Connection Pooling
- Audit-Logging

Author: VERITAS Agent System
Date: 10. Oktober 2025
Version: 1.0.0
"""

import sqlite3
import re
import logging
import asyncio
import time
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class DatabaseType(Enum):
    """Unterstützte Datenbank-Typen"""
    SQLITE = "sqlite"
    # Phase 2: PostgreSQL, MySQL, MSSQL


class SQLOperation(Enum):
    """SQL-Operationen"""
    SELECT = "select"
    PRAGMA = "pragma"
    EXPLAIN = "explain"
    BLOCKED = "blocked"  # Write operations


class QueryStatus(Enum):
    """Query Execution Status"""
    SUCCESS = "success"
    BLOCKED = "blocked"
    FAILED = "failed"
    TIMEOUT = "timeout"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class DatabaseQueryRequest:
    """Database Query Request"""
    query_id: str
    sql_query: str
    database_path: str
    
    # Optional Parameters
    database_type: DatabaseType = DatabaseType.SQLITE
    max_results: int = 1000
    timeout_seconds: int = 30
    include_schema: bool = False
    
    # Metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'query_id': self.query_id,
            'sql_query': self.sql_query,
            'database_path': self.database_path,
            'database_type': self.database_type.value,
            'max_results': self.max_results,
            'timeout_seconds': self.timeout_seconds,
            'include_schema': self.include_schema,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'metadata': self.metadata
        }


@dataclass
class DatabaseQueryResponse:
    """Database Query Response"""
    query_id: str
    success: bool
    status: QueryStatus
    
    # Results
    results: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    column_types: List[str] = field(default_factory=list)
    
    # Metadata
    row_count: int = 0
    total_rows: int = 0  # Before LIMIT
    query_time_ms: int = 0
    
    # Schema (optional)
    table_schema: Optional[Dict[str, Any]] = None
    
    # Error Handling
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    # Security
    blocked_reason: Optional[str] = None
    sql_operation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'query_id': self.query_id,
            'success': self.success,
            'status': self.status.value,
            'results': self.results,
            'columns': self.columns,
            'column_types': self.column_types,
            'row_count': self.row_count,
            'total_rows': self.total_rows,
            'query_time_ms': self.query_time_ms,
            'table_schema': self.table_schema,
            'error_message': self.error_message,
            'error_type': self.error_type,
            'warnings': self.warnings,
            'blocked_reason': self.blocked_reason,
            'sql_operation': self.sql_operation
        }


@dataclass
class DatabaseConfig:
    """Database Agent Konfiguration"""
    
    # Query Limits
    max_results: int = 1000
    default_timeout_seconds: int = 30
    max_query_length: int = 10000  # Characters
    
    # Security
    read_only_mode: bool = True
    enable_write_operations: bool = False  # Should always be False
    
    # Connection Pool
    max_connections: int = 10
    connection_timeout_seconds: int = 60
    
    # Performance
    enable_query_cache: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    max_cache_size: int = 100
    
    # Logging
    log_all_queries: bool = True
    log_blocked_queries: bool = True
    log_slow_queries_ms: int = 1000  # 1 second
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return asdict(self)


# =============================================================================
# SQL VALIDATOR (Security)
# =============================================================================

class SQLValidator:
    """
    Validiert SQL-Queries auf Sicherheit
    
    Features:
    - Keyword-Blacklisting (Write Operations)
    - SQL-Injection Prevention
    - Comment-Stripping
    - Query-Sanitization
    """
    
    # Blockierte Keywords (Write Operations)
    BLOCKED_KEYWORDS = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'TRUNCATE', 'REPLACE', 'MERGE', 'GRANT', 'REVOKE',
        'BEGIN', 'COMMIT', 'ROLLBACK', 'EXEC', 'EXECUTE',
        'ATTACH', 'DETACH'  # SQLite-specific
    ]
    
    # Erlaubte Keywords (Read Operations)
    ALLOWED_KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT',
        'INNER', 'OUTER', 'ON', 'GROUP', 'HAVING',
        'ORDER', 'LIMIT', 'OFFSET', 'AS', 'DISTINCT',
        'UNION', 'INTERSECT', 'EXCEPT', 'WITH',
        'EXPLAIN', 'PRAGMA', 'ANALYZE'
    ]
    
    # Gefährliche Patterns
    DANGEROUS_PATTERNS = [
        r';\s*DROP',           # ; DROP TABLE
        r';\s*DELETE',         # ; DELETE FROM
        r';\s*UPDATE',         # ; UPDATE SET
        r';\s*INSERT',         # ; INSERT INTO
        r'--\s*$',             # SQL Comment
        r'/\*.*?\*/',          # Multi-line Comment
        r'xp_cmdshell',        # SQL Server Command Execution
        r'exec\s*\(',          # Exec function
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SQLValidator")
    
    def validate_query(self, sql_query: str) -> Tuple[bool, Optional[str], SQLOperation]:
        """
        Validiert SQL-Query
        
        Args:
            sql_query: SQL-Query String
            
        Returns:
            Tuple[valid, error_message, operation]
        """
        # 1. Sanitize Query
        sanitized = self.sanitize_query(sql_query)
        
        # 2. Detect Operation
        operation = self.detect_operation(sanitized)
        
        # 3. Check if Blocked
        if operation == SQLOperation.BLOCKED:
            return False, "⚠️ Write operations are not allowed (Read-Only Mode)", operation
        
        # 4. Check Dangerous Patterns
        is_safe, danger_msg = self.check_dangerous_patterns(sanitized)
        if not is_safe:
            return False, danger_msg, SQLOperation.BLOCKED
        
        # 5. Validate Query Length
        if len(sanitized) > 10000:
            return False, "Query too long (max 10000 characters)", SQLOperation.BLOCKED
        
        return True, None, operation
    
    def detect_operation(self, sql_query: str) -> SQLOperation:
        """
        Erkennt SQL-Operation Type
        
        Args:
            sql_query: Sanitized SQL-Query
            
        Returns:
            SQLOperation
        """
        query_upper = sql_query.strip().upper()
        
        # Check für blockierte Keywords
        for keyword in self.BLOCKED_KEYWORDS:
            if re.search(rf'\b{keyword}\b', query_upper):
                self.logger.warning(f"🚫 Blocked SQL operation detected: {keyword}")
                return SQLOperation.BLOCKED
        
        # Check für erlaubte Operations
        # WITH (CTE) kann vor SELECT stehen
        if query_upper.startswith('WITH'):
            # WITH ... SELECT ist erlaubt (Common Table Expression)
            if 'SELECT' in query_upper:
                return SQLOperation.SELECT
            else:
                self.logger.warning(f"🚫 WITH clause without SELECT detected")
                return SQLOperation.BLOCKED
        
        if query_upper.startswith('SELECT'):
            return SQLOperation.SELECT
        elif query_upper.startswith('EXPLAIN'):
            return SQLOperation.EXPLAIN
        elif query_upper.startswith('PRAGMA'):
            return SQLOperation.PRAGMA
        else:
            # Unknown operation → block für Sicherheit
            self.logger.warning(f"🚫 Unknown SQL operation: {query_upper[:50]}")
            return SQLOperation.BLOCKED
    
    def sanitize_query(self, sql_query: str) -> str:
        """
        Sanitiert SQL-Query
        
        - Entfernt SQL-Kommentare (-- und /* */)
        - Normalisiert Whitespace
        - Trimmt Query
        
        Args:
            sql_query: Raw SQL-Query
            
        Returns:
            Sanitized SQL-Query
        """
        # Entferne Kommentare (-- am Zeilenende)
        query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
        
        # Entferne Multi-line Kommentare (/* ... */)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Normalisiere Whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    def check_dangerous_patterns(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        Prüft auf gefährliche SQL-Patterns
        
        Args:
            sql_query: Sanitized SQL-Query
            
        Returns:
            Tuple[is_safe, error_message]
        """
        query_upper = sql_query.upper()
        
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                self.logger.warning(f"🚫 Dangerous SQL pattern detected: {pattern}")
                return False, f"Dangerous SQL pattern detected: {pattern}"
        
        return True, None


# =============================================================================
# DATABASE AGENT
# =============================================================================

class DatabaseAgent:
    """
    VERITAS Database Agent
    
    Read-Only SQL-Zugriff auf SQLite-Datenbanken
    
    Features:
    - SELECT, PRAGMA, EXPLAIN Queries
    - SQL-Injection Prevention
    - Query-Timeout & Result-Limits
    - Connection Pooling
    - Query-Caching (optional)
    """
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.logger = logging.getLogger(f"{__name__}.DatabaseAgent")
        
        # SQL Validator
        self.sql_validator = SQLValidator()
        
        # Connection Pool
        self.connection_pool: Dict[str, sqlite3.Connection] = {}
        self.connection_lock = asyncio.Lock()
        
        # Query Cache
        self.query_cache: Dict[str, Tuple[DatabaseQueryResponse, float]] = {}
        self.cache_lock = asyncio.Lock()
        
        # Statistics
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'blocked_queries': 0,
            'failed_queries': 0,
            'cache_hits': 0,
            'avg_query_time_ms': 0.0,
            'total_query_time_ms': 0,
            'slow_queries': 0
        }
        
        self.logger.info("✅ Database Agent initialized (Read-Only Mode)")
    
    async def execute_query(
        self, 
        request: DatabaseQueryRequest
    ) -> DatabaseQueryResponse:
        """
        Führt SQL-Query aus (Read-Only)
        
        Process:
        1. Validate SQL (nur SELECT/PRAGMA/EXPLAIN)
        2. Check Cache (optional)
        3. Open Read-Only Connection
        4. Execute Query mit Timeout
        5. Parse Results
        6. Close Connection
        7. Return DatabaseQueryResponse
        
        Args:
            request: DatabaseQueryRequest
            
        Returns:
            DatabaseQueryResponse
        """
        start_time = time.time()
        self.stats['total_queries'] += 1
        
        # 1. Validate SQL
        is_valid, error_msg, operation = self.sql_validator.validate_query(request.sql_query)
        
        if not is_valid:
            self.stats['blocked_queries'] += 1
            
            if self.config.log_blocked_queries:
                self.logger.warning(
                    f"🚫 Blocked Query: {request.sql_query[:100]} | Reason: {error_msg}"
                )
            
            return DatabaseQueryResponse(
                query_id=request.query_id,
                success=False,
                status=QueryStatus.BLOCKED,
                error_message=error_msg,
                blocked_reason=error_msg,
                sql_operation=operation.value
            )
        
        # 2. Check Cache
        if self.config.enable_query_cache:
            cached_response = await self._get_cached_response(request)
            if cached_response:
                self.stats['cache_hits'] += 1
                self.logger.debug(f"💾 Cache hit for query: {request.query_id}")
                return cached_response
        
        # 3. Execute Query
        try:
            response = await self._execute_sqlite_query(request, operation)
            
            # Update Stats
            query_time_ms = response.query_time_ms
            self.stats['total_query_time_ms'] += query_time_ms
            self.stats['avg_query_time_ms'] = (
                self.stats['total_query_time_ms'] / self.stats['total_queries']
            )
            
            if response.success:
                self.stats['successful_queries'] += 1
                
                # Cache Response
                if self.config.enable_query_cache:
                    await self._cache_response(request, response)
            else:
                self.stats['failed_queries'] += 1
            
            # Log Slow Queries
            if query_time_ms > self.config.log_slow_queries_ms:
                self.stats['slow_queries'] += 1
                self.logger.warning(
                    f"🐌 Slow query detected: {query_time_ms}ms | "
                    f"Query: {request.sql_query[:100]}"
                )
            
            # Log All Queries (optional)
            if self.config.log_all_queries:
                self.logger.info(
                    f"📊 Query executed: {request.query_id} | "
                    f"Time: {query_time_ms}ms | Rows: {response.row_count}"
                )
            
            return response
            
        except Exception as e:
            self.stats['failed_queries'] += 1
            self.logger.error(f"❌ Query execution failed: {e}", exc_info=True)
            
            return DatabaseQueryResponse(
                query_id=request.query_id,
                success=False,
                status=QueryStatus.FAILED,
                error_message=f"Query execution failed: {str(e)}",
                error_type=type(e).__name__,
                sql_operation=operation.value
            )
    
    async def _execute_sqlite_query(
        self,
        request: DatabaseQueryRequest,
        operation: SQLOperation
    ) -> DatabaseQueryResponse:
        """
        Führt SQLite-Query aus
        
        Args:
            request: DatabaseQueryRequest
            operation: SQL Operation Type
            
        Returns:
            DatabaseQueryResponse
        """
        conn = None
        start_time = time.time()
        
        try:
            # 1. Open Read-Only Connection
            conn = self._get_readonly_connection(request.database_path)
            cursor = conn.cursor()
            
            # 2. Set Timeout
            cursor.execute(f"PRAGMA busy_timeout = {request.timeout_seconds * 1000}")
            
            # 3. Execute Query
            cursor.execute(request.sql_query)
            
            # 4. Fetch Results
            results = cursor.fetchall()
            query_time_ms = int((time.time() - start_time) * 1000)
            
            # 5. Extract Columns
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # 6. Extract Column Types (SQLite)
            column_types = []
            if cursor.description:
                for desc in cursor.description:
                    # SQLite gibt type_code zurück (oder None)
                    col_type = "TEXT"  # Default
                    if desc[1] is not None:
                        col_type = self._map_sqlite_type(desc[1])
                    column_types.append(col_type)
            
            # 7. Convert Results to Dicts
            result_dicts = [dict(zip(columns, row)) for row in results]
            
            # 8. Apply max_results Limit
            total_rows = len(result_dicts)
            limited_results = result_dicts[:request.max_results]
            
            # 9. Get Schema (optional)
            table_schema = None
            if request.include_schema and operation == SQLOperation.SELECT:
                table_schema = self._get_table_schema(conn, request.sql_query)
            
            # 10. Build Response
            return DatabaseQueryResponse(
                query_id=request.query_id,
                success=True,
                status=QueryStatus.SUCCESS,
                results=limited_results,
                columns=columns,
                column_types=column_types,
                row_count=len(limited_results),
                total_rows=total_rows,
                query_time_ms=query_time_ms,
                table_schema=table_schema,
                sql_operation=operation.value
            )
            
        except sqlite3.OperationalError as e:
            # Timeout oder Lock
            if "timeout" in str(e).lower():
                return DatabaseQueryResponse(
                    query_id=request.query_id,
                    success=False,
                    status=QueryStatus.TIMEOUT,
                    error_message=f"Query timeout after {request.timeout_seconds}s",
                    error_type="TimeoutError",
                    sql_operation=operation.value
                )
            else:
                raise
        
        finally:
            # Close Connection
            if conn:
                conn.close()
    
    def _get_readonly_connection(self, db_path: str) -> sqlite3.Connection:
        """
        Öffnet Read-Only SQLite Connection
        
        Args:
            db_path: Path zur SQLite-Datei
            
        Returns:
            sqlite3.Connection (Read-Only)
        """
        # SQLite Read-Only URI Mode
        # Siehe: https://www.sqlite.org/uri.html
        readonly_uri = f"file:{db_path}?mode=ro"
        
        try:
            conn = sqlite3.connect(readonly_uri, uri=True)
            
            # Enable Read-Only Pragma (zusätzliche Sicherheit)
            conn.execute("PRAGMA query_only = ON")
            
            return conn
            
        except sqlite3.OperationalError as e:
            if "readonly" in str(e).lower() or "unable to open" in str(e).lower():
                raise FileNotFoundError(f"Database file not found or not readable: {db_path}")
            else:
                raise
    
    def _map_sqlite_type(self, type_code: Any) -> str:
        """
        Mappt SQLite Type-Code zu String
        
        SQLite Types: NULL, INTEGER, REAL, TEXT, BLOB
        """
        if type_code is None:
            return "NULL"
        elif isinstance(type_code, int):
            return "INTEGER"
        elif isinstance(type_code, float):
            return "REAL"
        elif isinstance(type_code, str):
            return "TEXT"
        elif isinstance(type_code, bytes):
            return "BLOB"
        else:
            return "TEXT"  # Default
    
    def _get_table_schema(self, conn: sqlite3.Connection, sql_query: str) -> Dict[str, Any]:
        """
        Extrahiert Tabellen-Schema aus Query
        
        Args:
            conn: SQLite Connection
            sql_query: SQL-Query (SELECT)
            
        Returns:
            Schema-Dictionary
        """
        try:
            # Parse Table Name aus Query (simple regex)
            match = re.search(r'FROM\s+(\w+)', sql_query, re.IGNORECASE)
            if not match:
                return {}
            
            table_name = match.group(1)
            
            # PRAGMA table_info
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema_rows = cursor.fetchall()
            
            # Parse Schema
            schema = {
                'table_name': table_name,
                'columns': []
            }
            
            for row in schema_rows:
                # row: (cid, name, type, notnull, dflt_value, pk)
                schema['columns'].append({
                    'name': row[1],
                    'type': row[2],
                    'not_null': bool(row[3]),
                    'default_value': row[4],
                    'primary_key': bool(row[5])
                })
            
            return schema
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not extract table schema: {e}")
            return {}
    
    async def _get_cached_response(
        self, 
        request: DatabaseQueryRequest
    ) -> Optional[DatabaseQueryResponse]:
        """
        Holt gecachte Response (falls vorhanden und gültig)
        
        Args:
            request: DatabaseQueryRequest
            
        Returns:
            Cached DatabaseQueryResponse oder None
        """
        cache_key = self._generate_cache_key(request)
        
        async with self.cache_lock:
            if cache_key in self.query_cache:
                cached_response, cached_time = self.query_cache[cache_key]
                
                # Check TTL
                age = time.time() - cached_time
                if age < self.config.cache_ttl_seconds:
                    return cached_response
                else:
                    # Expired → remove
                    del self.query_cache[cache_key]
        
        return None
    
    async def _cache_response(
        self,
        request: DatabaseQueryRequest,
        response: DatabaseQueryResponse
    ):
        """
        Cached Response
        
        Args:
            request: DatabaseQueryRequest
            response: DatabaseQueryResponse
        """
        cache_key = self._generate_cache_key(request)
        
        async with self.cache_lock:
            # Check Cache Size
            if len(self.query_cache) >= self.config.max_cache_size:
                # Remove oldest entry (FIFO)
                oldest_key = next(iter(self.query_cache))
                del self.query_cache[oldest_key]
            
            # Add to Cache
            self.query_cache[cache_key] = (response, time.time())
    
    def _generate_cache_key(self, request: DatabaseQueryRequest) -> str:
        """
        Generiert Cache-Key aus Request
        
        Args:
            request: DatabaseQueryRequest
            
        Returns:
            Cache-Key (SHA256 Hash)
        """
        # Combine query + db_path
        key_data = f"{request.sql_query}|{request.database_path}|{request.max_results}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Returns Agent Status & Statistics
        
        Returns:
            Status Dictionary
        """
        return {
            'agent_name': 'DatabaseAgent',
            'version': '1.0.0',
            'database_type': 'SQLite',
            'read_only_mode': self.config.read_only_mode,
            'stats': self.stats,
            'config': self.config.to_dict(),
            'cache_size': len(self.query_cache),
            'connection_pool_size': len(self.connection_pool)
        }
    
    def clear_cache(self):
        """Löscht Query-Cache"""
        self.query_cache.clear()
        self.logger.info("🗑️ Query cache cleared")


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_database_agent(config: DatabaseConfig = None) -> DatabaseAgent:
    """
    Factory für Database Agent
    
    Args:
        config: DatabaseConfig (optional)
        
    Returns:
        DatabaseAgent-Instanz
    """
    return DatabaseAgent(config)


# =============================================================================
# MAIN FOR TESTING
# =============================================================================

async def main():
    """Test des Database Agent"""
    
    print("🗄️  VERITAS Database Agent - Test Suite")
    print("=" * 60)
    
    # Create Test Database
    test_db_path = "test_agent.db"
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Create Test Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert Test Data
    cursor.executemany(
        "INSERT INTO users (username, email, status) VALUES (?, ?, ?)",
        [
            ("alice", "alice@test.com", "active"),
            ("bob", "bob@test.com", "inactive"),
            ("charlie", "charlie@test.com", "active"),
            ("dave", "dave@test.com", "active"),
            ("eve", "eve@test.com", "inactive")
        ]
    )
    conn.commit()
    conn.close()
    
    # Create Agent
    config = DatabaseConfig(
        max_results=10,
        enable_query_cache=True,
        log_all_queries=True
    )
    agent = create_database_agent(config)
    
    # Test Queries
    test_queries = [
        {
            'sql': 'SELECT * FROM users',
            'description': 'Select all users',
            'should_succeed': True
        },
        {
            'sql': 'SELECT * FROM users WHERE status = "active"',
            'description': 'Select active users',
            'should_succeed': True
        },
        {
            'sql': 'SELECT COUNT(*) as count FROM users GROUP BY status',
            'description': 'Aggregate query',
            'should_succeed': True
        },
        {
            'sql': 'PRAGMA table_info(users)',
            'description': 'Get table schema',
            'should_succeed': True
        },
        {
            'sql': 'INSERT INTO users (username) VALUES ("hacker")',
            'description': 'INSERT (should be blocked)',
            'should_succeed': False
        },
        {
            'sql': 'UPDATE users SET status = "admin"',
            'description': 'UPDATE (should be blocked)',
            'should_succeed': False
        },
        {
            'sql': 'DELETE FROM users WHERE id = 1',
            'description': 'DELETE (should be blocked)',
            'should_succeed': False
        },
        {
            'sql': 'DROP TABLE users',
            'description': 'DROP TABLE (should be blocked)',
            'should_succeed': False
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n📋 Test {i}: {test['description']}")
        print(f"   SQL: {test['sql']}")
        
        request = DatabaseQueryRequest(
            query_id=f"test_{i:03d}",
            sql_query=test['sql'],
            database_path=test_db_path,
            include_schema=(i == 4)  # Schema nur bei Test 4
        )
        
        response = await agent.execute_query(request)
        
        # Check Result
        if test['should_succeed']:
            if response.success:
                print(f"   ✅ SUCCESS: {response.row_count} rows returned")
                if response.results:
                    print(f"   📊 Sample: {response.results[0]}")
                if response.table_schema:
                    print(f"   📐 Schema: {len(response.table_schema.get('columns', []))} columns")
            else:
                print(f"   ❌ FAILED: {response.error_message}")
        else:
            if not response.success:
                print(f"   ✅ CORRECTLY BLOCKED: {response.blocked_reason}")
            else:
                print(f"   ❌ SHOULD HAVE BEEN BLOCKED!")
    
    # Agent Status
    print(f"\n📊 Agent Status:")
    status = agent.get_status()
    print(f"   Total Queries: {status['stats']['total_queries']}")
    print(f"   Successful: {status['stats']['successful_queries']}")
    print(f"   Blocked: {status['stats']['blocked_queries']}")
    print(f"   Failed: {status['stats']['failed_queries']}")
    print(f"   Avg Query Time: {status['stats']['avg_query_time_ms']:.1f}ms")
    print(f"   Cache Hits: {status['stats']['cache_hits']}")
    
    # Cleanup
    import os
    os.remove(test_db_path)
    
    print("\n✅ Database Agent test completed!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    asyncio.run(main())
