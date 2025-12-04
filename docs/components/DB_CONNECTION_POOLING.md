# Database Connection Pooling in VERITAS

Date: 22. Oktober 2025
Status: Developer pool module available; production recommends pgBouncer

---

## Summary

To reduce connection overhead and improve throughput, VERITAS provides:

- A lightweight client-side connection pool based on psycopg2's ThreadedConnectionPool
  - Module: `backend/database/connection_pool.py`
  - API: `PostgresPool.instance().get_conn()/put_conn()` and `get_cursor()`
- Production-ready guidance to use pgBouncer (server-side pooling)

---

## Client-side Pool (Python)

Use in code:

```python
from backend.database.connection_pool import get_cursor

with get_cursor() as cur:
    cur.execute("SELECT 1")
    print(cur.fetchone())
```

Configuration (via .env):

```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=veritas
POSTGRES_USER=postgres
# Password is resolved via SecretsManager (DPAPI/Azure/ENV)
PG_POOL_MIN=1
PG_POOL_MAX=10
```

Smoke test:

```powershell
python tools\test_pg_pool.py
```

---

## Server-side Pool (pgBouncer) [Recommended]

For production, run pgBouncer near PostgreSQL and point VERITAS to pgBouncer (default port 6432):

```
POSTGRES_HOST=<pgbouncer-host>
POSTGRES_PORT=6432
```

Benefits:
- Lower connection churn across all services
- Transaction or session pooling modes
- Centralized control and monitoring

---

## Notes

- The UDS3 `PostgreSQLRelationalBackend` can benefit from pgBouncer automatically when its host/port point to pgBouncer.
- The setup script `backend/agents/framework/setup_database.py` connects directly for database creation, which is expected (it may need superuser access and the `postgres` maintenance DB).
- Secrets are provided by the SecretsManager; ensure `ENABLE_SECURE_SECRETS=true` and run the migration tool to avoid plaintext.

---

## Docker Quickstart (Windows)

We ship a ready-to-run compose setup under `tools/pgbouncer/`.

1) Create local env:

```powershell
cd C:\VCC\veritas\tools\pgbouncer
Copy-Item .env.pgbouncer.example .env.pgbouncer
# Edit .env.pgbouncer and set POSTGRES_PASSWORD, host, db, user
```

2) Start pgBouncer:

```powershell
docker compose up -d
```

3) Point VERITAS to pgBouncer and test:

```powershell
cd C:\VCC\veritas
$env:POSTGRES_PORT=6432
python tools\test_pg_pool.py
```

If you see `OK: Pool operational.`, routing via pgBouncer is working.
