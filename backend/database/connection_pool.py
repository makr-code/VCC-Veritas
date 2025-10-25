"""
PostgreSQL Connection Pool for VERITAS

Provides a global ThreadedConnectionPool configured via environment variables
and SecretsManager. Use get_conn()/put_conn() or context manager get_cursor().
"""
from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Optional

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

# Try to import SecretsManager helpers lazily
try:
    from backend.security.secrets import get_database_password
except Exception:  # pragma: no cover
    get_database_password = None  # type: ignore


class PostgresPool:
    _instance_lock = threading.Lock()
    _instance: Optional["PostgresPool"] = None

    def __init__(self) -> None:
        self._pool: Optional[ThreadedConnectionPool] = None
        self._minconn = int(os.getenv("PG_POOL_MIN", "1"))
        self._maxconn = int(os.getenv("PG_POOL_MAX", "10"))
        self._init_pool()

    def _build_dsn(self) -> str:
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        dbname = os.getenv("POSTGRES_DATABASE", os.getenv("POSTGRES_DB", "veritas"))
        user = os.getenv("POSTGRES_USER", "postgres")
        # Prefer encrypted secret
        password = None
        if get_database_password is not None:
            try:
                password = get_database_password("POSTGRES")
            except Exception:
                password = None
        password = password or os.getenv("POSTGRES_PASSWORD", "postgres")
        return f"host={host} port={port} dbname={dbname} user={user} password={password}"

    def _init_pool(self) -> None:
        dsn = self._build_dsn()
        self._pool = ThreadedConnectionPool(self._minconn, self._maxconn, dsn=dsn)

    @classmethod
    def instance(cls) -> "PostgresPool":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = PostgresPool()
        return cls._instance

    def get_conn(self):
        if self._pool is None:
            self._init_pool()
        assert self._pool is not None
        return self._pool.getconn()

    def put_conn(self, conn) -> None:
        if self._pool is None:
            return
        self._pool.putconn(conn)

    def closeall(self) -> None:
        if self._pool is not None:
            self._pool.closeall()


@contextmanager
def get_cursor(autocommit: bool = True):
    """Context manager yielding a cursor from the pool.

    Usage:
        with get_cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()
    """
    pool = PostgresPool.instance()
    conn = pool.get_conn()
    try:
        conn.autocommit = autocommit
        cur = conn.cursor()
        try:
            yield cur
        finally:
            cur.close()
    finally:
        pool.put_conn(conn)
