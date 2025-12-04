# pgBouncer for VERITAS (Docker Quickstart)

This folder provides a ready-to-run pgBouncer configuration using Docker on Windows.

## Prerequisites

- Docker Desktop installed and running
- A reachable PostgreSQL instance (local or remote)

## Setup

1) Create your local env file from the template:

```powershell
cd C:\VCC\veritas\tools\pgbouncer
Copy-Item .env.pgbouncer.example .env.pgbouncer
# Edit .env.pgbouncer to set POSTGRES_PASSWORD and other values
```

2) Start Postgres + pgBouncer:

```powershell
docker compose up -d
```

This brings up a local Postgres and pgBouncer. pgBouncer listens on localhost:6432 and forwards to the Postgres service.

If you prefer to use an external Postgres, edit `.env.pgbouncer` and set `POSTGRES_HOST=host.docker.internal` and correct port/user/password.

3) Point VERITAS to pgBouncer by setting:

```
POSTGRES_HOST=localhost
POSTGRES_PORT=6432
```

Now all client connections go through pgBouncer.

## Verify

- Use the included pool smoke test:

```powershell
cd C:\VCC\veritas
$env:POSTGRES_PORT=6432
python tools\test_pg_pool.py
```

You should see:
```
OK: Pool operational.
```

## Tuning

- PGBOUNCER_POOL_MODE: transaction (recommended) or session
- PGBOUNCER_DEFAULT_POOL_SIZE: backend connections per database/user
- PGBOUNCER_MAX_CLIENT_CONN: max incoming client connections

Adjust these in `.env.pgbouncer` and run `docker compose up -d` again.

## Troubleshooting

- Connection refused on 6432: Ensure Docker is running and `docker ps` shows `veritas-pgbouncer` healthy.
- Auth failed: Check `POSTGRES_USER/POSTGRES_PASSWORD` match your PostgreSQL.
- Target Postgres down: Confirm `POSTGRES_HOST` and `POSTGRES_PORT` are reachable from the container. On Windows host use `host.docker.internal`.
