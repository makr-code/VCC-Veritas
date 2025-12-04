# Docker - Container Images & Orchestration

## Overview

The `docker/` directory contains Docker-related files for containerization and orchestration of VERITAS components.

## File Structure

```
docker/
├── Dockerfile                    # Main application image
├── Dockerfile.production        # Production-optimized image
├── Dockerfile.nginx             # Nginx reverse proxy
├── Dockerfile.worker            # Worker service image
├── docker-compose.yml           # Local development setup
├── docker-compose.production.yml # Production setup
├── entrypoint.sh               # Container startup script
├── healthcheck.sh              # Health check script
├── nginx.conf                  # Nginx configuration
├── Makefile                    # Docker build automation
└── README.md                   # This file
```

## Docker Images

### Main Application Image

**File:** `Dockerfile`

**Purpose:** Development and testing image

**Build:**
```bash
docker build -t veritas:latest .
```

**Usage:**
```bash
docker run -p 8000:8000 \
  -e DB_HOST=postgres \
  -e OLLAMA_HOST=ollama:11434 \
  veritas:latest
```

**Features:**
- Python 3.11 base
- All dependencies included
- Development tools
- Hot reload support

### Production Image

**File:** `Dockerfile.production`

**Purpose:** Optimized production image

**Build:**
```bash
docker build -f Dockerfile.production -t veritas:prod .
```

**Optimizations:**
- Multi-stage build
- Minimal base image (slim)
- No development dependencies
- Optimized layer caching
- Reduced image size (~2GB → 800MB)

### Nginx Reverse Proxy

**File:** `Dockerfile.nginx`

**Purpose:** Reverse proxy and static file serving

**Build:**
```bash
docker build -f Dockerfile.nginx -t veritas-nginx:latest .
```

**Features:**
- SSL/TLS termination
- Static file serving
- Gzip compression
- Rate limiting
- Request logging

### Worker Service

**File:** `Dockerfile.worker`

**Purpose:** Background task processing

**Build:**
```bash
docker build -f Dockerfile.worker -t veritas-worker:latest .
```

**Functions:**
- Async task processing
- RAG index updates
- Embedding generation
- Report generation
- Scheduled jobs

## Docker Compose

### Development Setup

**File:** `docker-compose.yml`

Complete development environment with all services:

```yaml
services:
  api:           # Main API server
  postgres:      # Primary database
  redis:         # Cache and session store
  ollama:        # LLM backend
  nginx:         # Web server
  adminer:       # Database UI
  mailhog:       # Email testing
```

**Start:**
```bash
docker-compose up -d
```

**Services available:**
- API: http://localhost:8000
- Web: http://localhost
- Database UI: http://localhost:8080
- Mail: http://localhost:1025

### Production Setup

**File:** `docker-compose.production.yml`

Production-optimized deployment:
- Health checks
- Resource limits
- Restart policies
- Volume persistence
- Network isolation

**Deploy:**
```bash
docker-compose -f docker-compose.production.yml up -d
```

## Startup Scripts

### Entrypoint

**File:** `entrypoint.sh`

Runs on container startup:
1. Wait for database to be ready
2. Run database migrations
3. Create required indexes
4. Initialize cache
5. Start application

```bash
#!/bin/bash
set -e

echo "Waiting for database..."
while ! pg_isready -h $DB_HOST -p $DB_PORT; do
  sleep 1
done

echo "Running migrations..."
python -m alembic upgrade head

echo "Starting application..."
exec "$@"
```

### Health Check

**File:** `healthcheck.sh`

Periodic health verification:
```bash
#!/bin/bash
curl -f http://localhost:8000/api/v1/health || exit 1
```

**Configuration in docker-compose.yml:**
```yaml
healthcheck:
  test: ["CMD", "bash", "healthcheck.sh"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## Nginx Configuration

**File:** `nginx.conf`

Reverse proxy and web server setup:

```nginx
upstream api {
  server api:8000;
}

server {
  listen 80;
  server_name _;

  location /api/ {
    proxy_pass http://api;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
  }
}
```

**Features:**
- API proxying
- Static file serving
- Compression
- Caching headers
- SSL configuration

## Building Images

### Using Make

```bash
# Build all images
make build

# Build specific image
make build-api
make build-nginx
make build-worker

# Build production images
make build-prod

# Push to registry
make push

# Clean
make clean
```

### Manual Build

```bash
# Development
docker build -t veritas:latest .

# Production
docker build -f Dockerfile.production -t veritas:1.0.0 .

# With buildkit
docker buildx build --platform linux/amd64,linux/arm64 -t veritas:latest .
```

## Running Containers

### Single Container

```bash
docker run -d \
  --name veritas-api \
  -p 8000:8000 \
  -e DB_HOST=postgres \
  -e OLLAMA_HOST=ollama:11434 \
  -e JWT_SECRET=your_secret \
  veritas:latest
```

### Docker Compose

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f api

# Run command in container
docker-compose exec api bash
```

### Kubernetes

```bash
# Apply manifest
kubectl apply -f kubernetes/

# Check status
kubectl get pods

# View logs
kubectl logs deployment/veritas-api

# Port forward
kubectl port-forward svc/veritas-api 8000:8000
```

## Environment Variables

### Required

```bash
DB_HOST=postgres
DB_PORT=5432
DB_NAME=veritas_db
DB_USER=veritas
DB_PASSWORD=secure_password
JWT_SECRET=your_jwt_secret
```

### Optional

```bash
API_PORT=8000
API_CORS_ORIGINS=http://localhost:3000
LLM_MODEL=neural-9b-german
OLLAMA_HOST=ollama:11434
REDIS_HOST=redis
LOG_LEVEL=INFO
```

### Set at Runtime

```bash
# In docker-compose.yml
environment:
  - DB_HOST=postgres
  - DB_PASSWORD=${DB_PASSWORD}  # From .env

# Or from .env file
env_file:
  - .env
```

## Volume Management

### Persistent Data

```yaml
volumes:
  postgres_data:      # Database
  ollama_data:        # Model cache
  redis_data:         # Cache store
  logs_volume:        # Application logs
```

### Bind Mounts

```bash
docker run -v $(pwd)/logs:/app/logs veritas:latest
```

### Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U veritas veritas_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U veritas veritas_db < backup.sql
```

## Networking

### Docker Network

```bash
# Create custom network
docker network create veritas-net

# Connect container
docker network connect veritas-net container_name

# View network
docker network inspect veritas-net
```

### Port Mapping

```yaml
ports:
  - "8000:8000"      # API
  - "80:80"          # HTTP
  - "443:443"        # HTTPS
  - "5432:5432"      # PostgreSQL
```

## Security

### Best Practices

1. **Use read-only root filesystem**
   ```yaml
   read_only: true
   tmpfs:
     - /tmp
   ```

2. **Run as non-root user**
   ```dockerfile
   USER app
   ```

3. **Limit resources**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

4. **Use secrets management**
   ```yaml
   secrets:
     - jwt_secret
   ```

### Image Scanning

```bash
# Scan for vulnerabilities
docker scan veritas:latest

# Using Trivy
trivy image veritas:latest
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs container_name

# Run interactively
docker run -it veritas:latest bash

# Check entrypoint
docker inspect container_name | grep Cmd
```

### Connection Issues

```bash
# Test network
docker network inspect docker_default

# Check DNS
docker run busybox nslookup postgres

# Verify ports
docker port container_name
```

### Performance

```bash
# Monitor resources
docker stats

# View process
docker top container_name

# Analyze image layers
docker history veritas:latest
```

## Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove dangling images
docker image prune

# Remove volumes
docker volume prune

# Full cleanup
docker system prune -a
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build & Push Docker Image

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Build image
        run: docker build -t veritas:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo ${{ secrets.REGISTRY_PASSWORD }} | docker login -u ${{ secrets.REGISTRY_USER }} --password-stdin
          docker push veritas:${{ github.sha }}
```

## Documentation & Guides

- See `docker-compose.yml` for compose configuration
- See `Dockerfile*` for build scripts
- See `config/README.md` for configuration
- See `DEPLOY.md` for deployment guide

---

**Last Updated:** December 4, 2025
**Status:** Production Ready ✅
**Docker Images:** 4
**Compose Services:** 8
**Min Size:** 500 MB (production)
