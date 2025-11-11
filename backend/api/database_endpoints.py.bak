#!/usr/bin/env python3
"""
VERITAS Database API Endpoints
================================

REST API Endpoints für Database Agent (SQLite Read-Only)

Features:
- POST /api/database/query - Execute SQL Query
- GET /api/database/status - Database Agent Status
- GET /api/database/schema/{table} - Get Table Schema
- POST /api/database/validate - Validate SQL Query

Author: VERITAS System
Date: 10. Oktober 2025
Version: 1.0.0
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query
from pydantic import BaseModel, Field, validator

# Database Agent Integration
try:
    from backend.agents.veritas_api_agent_database import (
        DatabaseAgent,
        DatabaseConfig,
        DatabaseQueryRequest,
        DatabaseQueryResponse,
        DatabaseType,
        create_database_agent,
    )

    DATABASE_AGENT_AVAILABLE = True
except ImportError:
    DATABASE_AGENT_AVAILABLE = False
    logging.warning("⚠️ Database Agent nicht verfügbar")

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/database", tags=["database"])

# Global Database Agent Instance
_database_agent: Optional[DatabaseAgent] = None


# =============================================================================
# PYDANTIC MODELS
# =============================================================================


class DatabaseQueryRequestModel(BaseModel):
    """Request Model für Database Query"""

    sql_query: str = Field(..., description="SQL Query (SELECT, PRAGMA, EXPLAIN only)", min_length=1, max_length=10000)
    database_path: str = Field(..., description="Absolute path to SQLite database file")

    # Optional Parameters
    max_results: int = Field(default=1000, description="Maximum number of results to return", ge=1, le=10000)
    timeout_seconds: int = Field(default=30, description="Query timeout in seconds", ge=1, le=300)
    include_schema: bool = Field(default=False, description="Include table schema in response")

    # Metadata
    user_id: Optional[str] = Field(default=None, description="User ID for audit logging")
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking")

    @validator("sql_query")
    def validate_sql_query(cls, v):
        """Validiert SQL-Query Format"""
        if not v or not v.strip():
            raise ValueError("SQL query cannot be empty")

        # Basic validation: Must start with SELECT/PRAGMA/EXPLAIN
        query_upper = v.strip().upper()
        allowed_starts = ["SELECT", "PRAGMA", "EXPLAIN"]

        if not any(query_upper.startswith(keyword) for keyword in allowed_starts):
            raise ValueError(f"SQL query must start with one of: {', '.join(allowed_starts)}")

        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "sql_query": "SELECT * FROM documents WHERE category = 'environmental' LIMIT 10",
                "database_path": "/path/to/database.db",
                "max_results": 100,
                "timeout_seconds": 30,
                "include_schema": False,
                "user_id": "user_123",
                "session_id": "session_456",
            }
        }


class SQLValidationRequestModel(BaseModel):
    """Request Model für SQL Validation"""

    sql_query: str = Field(..., description="SQL Query to validate", min_length=1, max_length=10000)

    class Config:
        schema_extra = {"example": {"sql_query": "SELECT id, name FROM users WHERE status = 'active'"}}


class DatabaseQueryResponseModel(BaseModel):
    """Response Model für Database Query"""

    query_id: str
    success: bool
    status: str

    # Results
    results: list = Field(default_factory=list)
    columns: list = Field(default_factory=list)
    column_types: list = Field(default_factory=list)

    # Metadata
    row_count: int = 0
    total_rows: int = 0
    query_time_ms: int = 0

    # Schema (optional)
    table_schema: Optional[dict] = None

    # Error Handling
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    warnings: list = Field(default_factory=list)

    # Security
    blocked_reason: Optional[str] = None
    sql_operation: Optional[str] = None


class SQLValidationResponseModel(BaseModel):
    """Response Model für SQL Validation"""

    valid: bool
    sql_operation: str
    error_message: Optional[str] = None
    warnings: list = Field(default_factory=list)


class DatabaseStatusResponseModel(BaseModel):
    """Response Model für Database Agent Status"""

    agent_name: str
    version: str
    database_type: str
    read_only_mode: bool
    available: bool
    stats: dict
    config: dict
    cache_size: int = 0
    connection_pool_size: int = 0


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_database_agent() -> DatabaseAgent:
    """
    Holt oder erstellt Database Agent Singleton

    Returns:
        DatabaseAgent-Instanz

    Raises:
        HTTPException: Wenn Database Agent nicht verfügbar
    """
    global _database_agent

    if not DATABASE_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database Agent is not available (module not loaded)")

    if _database_agent is None:
        try:
            config = DatabaseConfig(
                max_results=1000,
                default_timeout_seconds=30,
                read_only_mode=True,
                enable_write_operations=False,  # Must always be False
                enable_query_cache=True,
                log_all_queries=True,
                log_blocked_queries=True,
            )
            _database_agent = create_database_agent(config)
            logger.info("✅ Database Agent initialized via API")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Database Agent: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to initialize Database Agent: {str(e)}")

    return _database_agent


# =============================================================================
# API ENDPOINTS
# =============================================================================


@router.post("/query", response_model=DatabaseQueryResponseModel)
async def execute_database_query(request: DatabaseQueryRequestModel = Body(...)) -> Dict[str, Any]:
    """
    **Executes SQL Query on Database (Read-Only)**

    Allowed Operations:
    - SELECT: Query data
    - PRAGMA: Get database/table info
    - EXPLAIN: Query execution plan

    Blocked Operations (Security):
    - INSERT, UPDATE, DELETE (Write operations)
    - DROP, CREATE, ALTER (Schema changes)
    - ATTACH, DETACH (Database management)

    **Example:**
    ```json
    {
        "sql_query": "SELECT * FROM users WHERE status = 'active' LIMIT 10",
        "database_path": "/data/app.db",
        "max_results": 100,
        "timeout_seconds": 30
    }
    ```

    **Response:**
    - `success`: Query executed successfully
    - `results`: Array of result rows (as dictionaries)
    - `columns`: Column names
    - `row_count`: Number of rows returned
    - `query_time_ms`: Execution time in milliseconds
    """
    try:
        agent = get_database_agent()

        # Generate Query ID
        query_id = f"db_query_{uuid.uuid4().hex[:8]}"

        # Create DatabaseQueryRequest
        db_request = DatabaseQueryRequest(
            query_id=query_id,
            sql_query=request.sql_query,
            database_path=request.database_path,
            database_type=DatabaseType.SQLITE,
            max_results=request.max_results,
            timeout_seconds=request.timeout_seconds,
            include_schema=request.include_schema,
            user_id=request.user_id,
            session_id=request.session_id,
        )

        # Execute Query
        response = await agent.execute_query(db_request)

        # Convert to Response Model
        return response.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database query execution failed: {str(e)}")


@router.post("/validate", response_model=SQLValidationResponseModel)
async def validate_sql_query(request: SQLValidationRequestModel = Body(...)) -> Dict[str, Any]:
    """
    **Validates SQL Query (without execution)**

    Checks:
    - SQL syntax (basic validation)
    - Allowed operations (SELECT, PRAGMA, EXPLAIN)
    - Blocked keywords (INSERT, UPDATE, DELETE, DROP, etc.)
    - Dangerous SQL patterns (SQL Injection)

    **Example:**
    ```json
    {
        "sql_query": "SELECT id, name FROM users WHERE id = 123"
    }
    ```

    **Response:**
    - `valid`: SQL query is valid and allowed
    - `sql_operation`: Detected operation (select/pragma/explain/blocked)
    - `error_message`: Validation error (if invalid)
    """
    try:
        agent = get_database_agent()

        # Validate Query
        is_valid, error_msg, operation = agent.sql_validator.validate_query(request.sql_query)

        return {"valid": is_valid, "sql_operation": operation.value, "error_message": error_msg, "warnings": []}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ SQL validation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SQL validation failed: {str(e)}")


@router.get("/status", response_model=DatabaseStatusResponseModel)
async def get_database_status() -> Dict[str, Any]:
    """
    **Returns Database Agent Status**

    Provides:
    - Agent availability
    - Configuration
    - Statistics (queries executed, blocked, etc.)
    - Cache status
    - Performance metrics

    **Example Response:**
    ```json
    {
        "agent_name": "DatabaseAgent",
        "version": "1.0.0",
        "database_type": "SQLite",
        "read_only_mode": true,
        "available": true,
        "stats": {
            "total_queries": 150,
            "successful_queries": 145,
            "blocked_queries": 5,
            "avg_query_time_ms": 12.5
        }
    }
    ```
    """
    try:
        if not DATABASE_AGENT_AVAILABLE:
            return {
                "agent_name": "DatabaseAgent",
                "version": "1.0.0",
                "database_type": "SQLite",
                "read_only_mode": True,
                "available": False,
                "stats": {},
                "config": {},
                "cache_size": 0,
                "connection_pool_size": 0,
            }

        agent = get_database_agent()
        status = agent.get_status()
        status["available"] = True

        return status

    except Exception as e:
        logger.error(f"❌ Failed to get database status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get database status: {str(e)}")


@router.post("/schema/{table_name}")
async def get_table_schema(
    table_name: str = Path(..., description="Table name to get schema for"),
    database_path: str = Query(..., description="Path to SQLite database file"),
) -> Dict[str, Any]:
    """
    **Returns Table Schema**

    Uses PRAGMA table_info to retrieve:
    - Column names
    - Column types
    - NOT NULL constraints
    - Default values
    - Primary keys

    **Example:**
    ```
    POST /api/database/schema/users?database_path=/data/app.db
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
            }
        ]
    }
    ```
    """
    try:
        agent = get_database_agent()

        # Generate Query ID
        query_id = f"schema_{uuid.uuid4().hex[:8]}"

        # PRAGMA table_info Query
        sql_query = f"PRAGMA table_info({table_name})"

        db_request = DatabaseQueryRequest(
            query_id=query_id,
            sql_query=sql_query,
            database_path=database_path,
            database_type=DatabaseType.SQLITE,
            max_results=1000,
            timeout_seconds=10,
        )

        response = await agent.execute_query(db_request)

        if not response.success:
            raise HTTPException(status_code=400, detail=f"Failed to get table schema: {response.error_message}")

        # Parse Schema
        schema = {"table_name": table_name, "columns": []}

        for row in response.results:
            schema["columns"].append(
                {
                    "name": row.get("name"),
                    "type": row.get("type"),
                    "not_null": bool(row.get("notnull")),
                    "default_value": row.get("dflt_value"),
                    "primary_key": bool(row.get("pk")),
                }
            )

        return schema

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get table schema: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get table schema: {str(e)}")


@router.delete("/cache")
async def clear_query_cache() -> Dict[str, Any]:
    """
    **Clears Query Cache**

    Removes all cached query results.
    Useful for testing or when database content has changed.

    **Response:**
    ```json
    {
        "success": true,
        "message": "Query cache cleared",
        "previous_cache_size": 42
    }
    ```
    """
    try:
        agent = get_database_agent()

        # Get cache size before clearing
        previous_size = len(agent.query_cache)

        # Clear cache
        agent.clear_cache()

        return {"success": True, "message": "Query cache cleared", "previous_cache_size": previous_size}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


# =============================================================================
# ROUTER REGISTRATION
# =============================================================================


def get_database_router() -> APIRouter:
    """
    Returns Database API Router

    Returns:
        FastAPI APIRouter
    """
    return router


# =============================================================================
# MAIN FOR TESTING
# =============================================================================

if __name__ == "__main__":
    print("🗄️  Database API Endpoints")
    print("=" * 60)
    print("\nAvailable Endpoints:")
    print("  POST   /api/database/query         - Execute SQL Query")
    print("  POST   /api/database/validate      - Validate SQL Query")
    print("  GET    /api/database/status        - Agent Status")
    print("  POST   /api/database/schema/{table} - Get Table Schema")
    print("  DELETE /api/database/cache         - Clear Cache")
    print("\nDatabase Agent Available:", DATABASE_AGENT_AVAILABLE)
