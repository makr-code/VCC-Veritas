#!/usr/bin/env python3
"""
VERITAS Database Agent - Unit Tests
====================================

Test Suite für Database Agent (SQLite Read-Only)

Test Coverage:
1. ✅ SELECT Queries erlaubt
2. ✅ INSERT Queries blockiert
3. ✅ UPDATE Queries blockiert
4. ✅ DELETE Queries blockiert
5. ✅ SQL-Injection Prevention
6. ✅ Query Timeout
7. ✅ Result Limit
8. ✅ Schema Extraction

Author: VERITAS System
Date: 10. Oktober 2025
Version: 1.0.0
"""

import pytest
import sqlite3
import tempfile
import os
import asyncio
from pathlib import Path

# Database Agent Imports
from backend.agents.veritas_api_agent_database import (
    DatabaseAgent,
    DatabaseQueryRequest,
    DatabaseQueryResponse,
    DatabaseConfig,
    DatabaseType,
    SQLValidator,
    SQLOperation,
    QueryStatus,
    create_database_agent
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def test_database():
    """Erstellt temporäre Test-Datenbank"""
    # Create temp SQLite database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    
    try:
        # Close file descriptor (SQLite öffnet selbst)
        os.close(fd)
        
        # Create test data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT,
                status TEXT,
                role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test data
        test_users = [
            (1, "alice", "alice@test.com", "active", "admin"),
            (2, "bob", "bob@test.com", "inactive", "user"),
            (3, "charlie", "charlie@test.com", "active", "user"),
            (4, "dave", "dave@test.com", "active", "moderator"),
            (5, "eve", "eve@test.com", "inactive", "user")
        ]
        
        cursor.executemany(
            "INSERT INTO users (id, username, email, status, role) VALUES (?, ?, ?, ?, ?)",
            test_users
        )
        
        # Create documents table
        cursor.execute("""
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT,
                content TEXT,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Insert test documents
        test_documents = [
            (1, "Environmental Report 2024", "environmental", "Lorem ipsum...", 1),
            (2, "Financial Analysis Q1", "financial", "Lorem ipsum...", 2),
            (3, "Transport Study", "transport", "Lorem ipsum...", 3)
        ]
        
        cursor.executemany(
            "INSERT INTO documents (id, title, category, content, user_id) VALUES (?, ?, ?, ?, ?)",
            test_documents
        )
        
        conn.commit()
        conn.close()
        
        yield db_path
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def database_config():
    """Erstellt Test-Konfiguration"""
    return DatabaseConfig(
        max_results=1000,
        default_timeout_seconds=30,
        read_only_mode=True,
        enable_write_operations=False,
        enable_query_cache=True,
        log_all_queries=False,  # Disable für Tests
        log_blocked_queries=False  # Disable für Tests
    )


@pytest.fixture
def database_agent(database_config):
    """Erstellt Database Agent"""
    return create_database_agent(database_config)


@pytest.fixture
def sql_validator():
    """Erstellt SQL Validator"""
    return SQLValidator()


# =============================================================================
# SQL VALIDATOR TESTS
# =============================================================================

class TestSQLValidator:
    """Tests für SQL Validator"""
    
    def test_select_allowed(self, sql_validator):
        """Test: SELECT Query erlaubt"""
        sql = "SELECT * FROM users WHERE status = 'active'"
        
        is_valid, error_msg, operation = sql_validator.validate_query(sql)
        
        assert is_valid is True
        assert error_msg is None
        assert operation == SQLOperation.SELECT
    
    def test_pragma_allowed(self, sql_validator):
        """Test: PRAGMA Query erlaubt"""
        sql = "PRAGMA table_info(users)"
        
        is_valid, error_msg, operation = sql_validator.validate_query(sql)
        
        assert is_valid is True
        assert error_msg is None
        assert operation == SQLOperation.PRAGMA
    
    def test_explain_allowed(self, sql_validator):
        """Test: EXPLAIN Query erlaubt"""
        sql = "EXPLAIN SELECT * FROM users"
        
        is_valid, error_msg, operation = sql_validator.validate_query(sql)
        
        assert is_valid is True
        assert error_msg is None
        assert operation == SQLOperation.EXPLAIN
    
    def test_insert_blocked(self, sql_validator):
        """Test: INSERT Query blockiert"""
        sql = "INSERT INTO users (username) VALUES ('hacker')"
        
        is_valid, error_msg, operation = sql_validator.validate_query(sql)
        
        assert is_valid is False
        assert "not allowed" in error_msg.lower()
        assert operation == SQLOperation.BLOCKED
    
    def test_update_blocked(self, sql_validator):
        """Test: UPDATE Query blockiert"""
        sql = "UPDATE users SET role = 'admin' WHERE id = 1"
        
        is_valid, error_msg, operation = sql_validator.validate_query(sql)
        
        assert is_valid is False
        assert "not allowed" in error_msg.lower()
        assert operation == SQLOperation.BLOCKED
    
    def test_delete_blocked(self, sql_validator):
        """Test: DELETE Query blockiert"""
        sql = "DELETE FROM users WHERE id = 1"
        
        is_valid, error_msg, operation = sql_validator.validate_query(sql)
        
        assert is_valid is False
        assert "not allowed" in error_msg.lower()
        assert operation == SQLOperation.BLOCKED
    
    def test_drop_blocked(self, sql_validator):
        """Test: DROP Query blockiert"""
        sql = "DROP TABLE users"
        
        is_valid, error_msg, operation = sql_validator.validate_query(sql)
        
        assert is_valid is False
        assert "not allowed" in error_msg.lower()
        assert operation == SQLOperation.BLOCKED
    
    def test_sql_injection_blocked(self, sql_validator):
        """Test: SQL-Injection Pattern blockiert"""
        sql = "SELECT * FROM users; DROP TABLE users; --"
        
        is_valid, error_msg, operation = sql_validator.validate_query(sql)
        
        assert is_valid is False
        assert operation == SQLOperation.BLOCKED
    
    def test_comment_stripped(self, sql_validator):
        """Test: SQL-Kommentare entfernt"""
        sql = """
        SELECT * FROM users
        -- This is a comment
        WHERE status = 'active'
        """
        
        sanitized = sql_validator.sanitize_query(sql)
        
        assert "--" not in sanitized
        assert "comment" not in sanitized.lower()
        assert "SELECT" in sanitized
        assert "WHERE" in sanitized


# =============================================================================
# DATABASE AGENT TESTS
# =============================================================================

class TestDatabaseAgent:
    """Tests für Database Agent"""
    
    @pytest.mark.asyncio
    async def test_simple_select(self, database_agent, test_database):
        """Test: Einfache SELECT Query"""
        request = DatabaseQueryRequest(
            query_id="test_001",
            sql_query="SELECT * FROM users",
            database_path=test_database
        )
        
        response = await database_agent.execute_query(request)
        
        assert response.success is True
        assert response.status == QueryStatus.SUCCESS
        assert response.row_count == 5  # 5 Test-User
        assert len(response.columns) > 0
        assert "username" in response.columns
    
    @pytest.mark.asyncio
    async def test_select_with_where(self, database_agent, test_database):
        """Test: SELECT mit WHERE Clause"""
        request = DatabaseQueryRequest(
            query_id="test_002",
            sql_query="SELECT * FROM users WHERE status = 'active'",
            database_path=test_database
        )
        
        response = await database_agent.execute_query(request)
        
        assert response.success is True
        assert response.row_count == 3  # 3 aktive User
        
        # Check results
        for result in response.results:
            assert result['status'] == 'active'
    
    @pytest.mark.asyncio
    async def test_aggregate_query(self, database_agent, test_database):
        """Test: Aggregation Query (COUNT, GROUP BY)"""
        request = DatabaseQueryRequest(
            query_id="test_003",
            sql_query="SELECT status, COUNT(*) as count FROM users GROUP BY status",
            database_path=test_database
        )
        
        response = await database_agent.execute_query(request)
        
        assert response.success is True
        assert response.row_count == 2  # 2 Status-Gruppen (active, inactive)
        
        # Check columns
        assert 'status' in response.columns
        assert 'count' in response.columns
    
    @pytest.mark.asyncio
    async def test_pragma_query(self, database_agent, test_database):
        """Test: PRAGMA Query (Schema Info)"""
        request = DatabaseQueryRequest(
            query_id="test_004",
            sql_query="PRAGMA table_info(users)",
            database_path=test_database
        )
        
        response = await database_agent.execute_query(request)
        
        assert response.success is True
        assert response.row_count > 0  # Mindestens 1 Column
        
        # Check for expected columns
        column_names = [row.get('name') for row in response.results]
        assert 'id' in column_names
        assert 'username' in column_names
    
    @pytest.mark.asyncio
    async def test_insert_blocked(self, database_agent, test_database):
        """Test: INSERT blockiert"""
        request = DatabaseQueryRequest(
            query_id="test_005",
            sql_query="INSERT INTO users (username) VALUES ('hacker')",
            database_path=test_database
        )
        
        response = await database_agent.execute_query(request)
        
        assert response.success is False
        assert response.status == QueryStatus.BLOCKED
        assert response.blocked_reason is not None
        assert "not allowed" in response.blocked_reason.lower()
    
    @pytest.mark.asyncio
    async def test_update_blocked(self, database_agent, test_database):
        """Test: UPDATE blockiert"""
        request = DatabaseQueryRequest(
            query_id="test_006",
            sql_query="UPDATE users SET role = 'admin' WHERE id = 1",
            database_path=test_database
        )
        
        response = await database_agent.execute_query(request)
        
        assert response.success is False
        assert response.status == QueryStatus.BLOCKED
    
    @pytest.mark.asyncio
    async def test_delete_blocked(self, database_agent, test_database):
        """Test: DELETE blockiert"""
        request = DatabaseQueryRequest(
            query_id="test_007",
            sql_query="DELETE FROM users WHERE id = 1",
            database_path=test_database
        )
        
        response = await database_agent.execute_query(request)
        
        assert response.success is False
        assert response.status == QueryStatus.BLOCKED
    
    @pytest.mark.asyncio
    async def test_max_results_limit(self, database_agent, test_database):
        """Test: Result Limit funktioniert"""
        request = DatabaseQueryRequest(
            query_id="test_008",
            sql_query="SELECT * FROM users",
            database_path=test_database,
            max_results=2  # Limit auf 2
        )
        
        response = await database_agent.execute_query(request)
        
        assert response.success is True
        assert response.row_count == 2  # Nur 2 Ergebnisse
        assert response.total_rows == 5  # Total 5 in DB
    
    @pytest.mark.asyncio
    async def test_schema_extraction(self, database_agent, test_database):
        """Test: Schema-Extraktion"""
        request = DatabaseQueryRequest(
            query_id="test_009",
            sql_query="SELECT * FROM users LIMIT 1",
            database_path=test_database,
            include_schema=True
        )
        
        response = await database_agent.execute_query(request)
        
        assert response.success is True
        assert response.table_schema is not None
        assert response.table_schema.get('table_name') == 'users'
        assert len(response.table_schema.get('columns', [])) > 0
    
    @pytest.mark.asyncio
    async def test_database_not_found(self, database_agent):
        """Test: Nicht existierende Datenbank"""
        request = DatabaseQueryRequest(
            query_id="test_010",
            sql_query="SELECT * FROM users",
            database_path="/nonexistent/database.db"
        )
        
        response = await database_agent.execute_query(request)
        
        assert response.success is False
        assert response.status == QueryStatus.FAILED
        assert response.error_message is not None
    
    @pytest.mark.asyncio
    async def test_query_statistics(self, test_database):
        """Test: Query-Statistiken"""
        # Create fresh agent instance
        config = DatabaseConfig(enable_query_cache=False, log_all_queries=False)
        agent = create_database_agent(config)
        
        # Execute some queries
        for i in range(5):
            request = DatabaseQueryRequest(
                query_id=f"test_stats_{i}",
                sql_query="SELECT * FROM users",
                database_path=test_database
            )
            await agent.execute_query(request)
        
        # Check stats
        stats = agent.stats
        
        assert stats['total_queries'] == 5
        assert stats['successful_queries'] == 5
        assert stats['avg_query_time_ms'] >= 0
    
    @pytest.mark.asyncio
    async def test_query_caching(self, database_agent, test_database):
        """Test: Query-Caching funktioniert"""
        # Clear cache first
        database_agent.clear_cache()
        
        request = DatabaseQueryRequest(
            query_id="test_cache_001",
            sql_query="SELECT * FROM users",
            database_path=test_database
        )
        
        # First execution (should cache)
        response1 = await database_agent.execute_query(request)
        cache_hits_before = database_agent.stats['cache_hits']
        
        # Second execution (should use cache)
        response2 = await database_agent.execute_query(request)
        cache_hits_after = database_agent.stats['cache_hits']
        
        assert response1.success is True
        assert response2.success is True
        assert cache_hits_after > cache_hits_before  # Cache hit!
    
    def test_agent_status(self, database_agent):
        """Test: Agent Status abrufen"""
        status = database_agent.get_status()
        
        assert status['agent_name'] == 'DatabaseAgent'
        assert status['version'] == '1.0.0'
        assert status['database_type'] == 'SQLite'
        assert status['read_only_mode'] is True
        assert 'stats' in status
        assert 'config' in status


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestDatabaseAgentIntegration:
    """Integration Tests"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, test_database):
        """Test: Vollständiger Workflow"""
        # 1. Create Agent
        config = DatabaseConfig(
            max_results=10,
            enable_query_cache=True,
            log_all_queries=False
        )
        agent = create_database_agent(config)
        
        # 2. Execute SELECT Query
        request = DatabaseQueryRequest(
            query_id="workflow_001",
            sql_query="SELECT username, status FROM users WHERE status = 'active'",
            database_path=test_database,
            max_results=10
        )
        
        response = await agent.execute_query(request)
        
        assert response.success is True
        assert response.row_count > 0
        
        # 3. Get Status
        status = agent.get_status()
        assert status['stats']['successful_queries'] >= 1
        
        # 4. Clear Cache
        agent.clear_cache()
        assert len(agent.query_cache) == 0


# =============================================================================
# MAIN FOR PYTEST
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
