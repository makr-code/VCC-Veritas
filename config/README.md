# Configuration - Settings & Environment

## Overview

The `config/` directory contains all configuration files for VERITAS, including environment settings, database configuration, API configuration, and deployment parameters.

## File Structure

```
config/
├── database.yml              # Database configuration
├── api.yml                   # API endpoints and settings
├── llm.yml                   # LLM and Ollama settings
├── rag.yml                   # RAG pipeline configuration
├── cache.yml                 # Caching configuration
├── auth.yml                  # Authentication settings
├── logging.yml               # Logging configuration
├── docker-compose.yml        # Docker services
├── environment.example       # Example .env file
├── kubernetes/               # Kubernetes configs
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
└── README.md                 # This file
```

## Configuration Files

### database.yml
**Purpose:** Database connection and settings

```yaml
database:
  host: localhost
  port: 5432
  name: veritas_db
  user: ${DB_USER}
  password: ${DB_PASSWORD}
  ssl: true
  pool:
    min: 5
    max: 20
    timeout: 30
  backup:
    enabled: true
    schedule: "0 2 * * *"  # 2 AM daily
```

**Environment Variables:**
- `DB_HOST` - Database hostname
- `DB_PORT` - Database port
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `DB_SSL` - Enable SSL (true/false)

### api.yml
**Purpose:** API endpoints and configuration

```yaml
api:
  host: 0.0.0.0
  port: 8000
  base_path: /api/v1

  # CORS settings
  cors:
    origins:
      - http://localhost:3000
      - https://veritas.example.com
    methods: [GET, POST, PUT, DELETE]
    credentials: true

  # Rate limiting
  rate_limit:
    enabled: true
    requests_per_minute: 60
    burst_size: 10

  # Timeouts
  timeout:
    read: 30
    write: 30
    idle: 60
```

**Environment Variables:**
- `API_HOST` - API server host
- `API_PORT` - API server port
- `API_BASE_PATH` - Base API path
- `API_CORS_ORIGINS` - CORS origins (comma-separated)

### llm.yml
**Purpose:** LLM and Ollama configuration

```yaml
llm:
  provider: ollama
  model: neural-9b-german

  # Ollama settings
  ollama:
    host: localhost
    port: 11434
    timeout: 120
    retry_attempts: 3

  # Model parameters
  parameters:
    temperature: 0.7
    top_p: 0.95
    top_k: 40
    num_predict: 2048

  # Performance
  performance:
    batch_size: 4
    num_threads: 8
    cache_enabled: true
```

**Environment Variables:**
- `LLM_PROVIDER` - LLM provider (ollama, openai, etc.)
- `LLM_MODEL` - Model name
- `OLLAMA_HOST` - Ollama server host
- `OLLAMA_PORT` - Ollama server port
- `LLM_TEMPERATURE` - Model temperature
- `LLM_MAX_TOKENS` - Maximum tokens

### rag.yml
**Purpose:** RAG pipeline configuration

```yaml
rag:
  enabled: true

  # Retrieval settings
  retrieval:
    vector_db: pinecone
    chunk_size: 512
    chunk_overlap: 50
    top_k: 5

  # Vector database
  vector_db:
    pinecone:
      api_key: ${PINECONE_API_KEY}
      environment: us-west1
      index: veritas-prod

  # Embedding model
  embeddings:
    model: multilingual-e5-large
    dimension: 1024

  # Reranking
  reranking:
    enabled: true
    model: cross-encoder-mmarco-mMiniLMv2-L12-H384-v41
```

**Environment Variables:**
- `RAG_ENABLED` - Enable RAG (true/false)
- `VECTOR_DB_TYPE` - Vector database type
- `PINECONE_API_KEY` - Pinecone API key
- `PINECONE_ENVIRONMENT` - Pinecone environment
- `EMBEDDING_MODEL` - Embedding model name

### cache.yml
**Purpose:** Caching configuration

```yaml
cache:
  # Redis cache
  redis:
    host: localhost
    port: 6379
    db: 0
    password: ${REDIS_PASSWORD}
    timeout: 5

  # Cache policies
  policies:
    query_results:
      ttl: 3600        # 1 hour
      max_size: 1000
      enabled: true

    embedding_cache:
      ttl: 86400       # 24 hours
      max_size: 100000
      enabled: true

    semantic_cache:
      ttl: 7200        # 2 hours
      threshold: 0.95
      enabled: true
```

**Environment Variables:**
- `REDIS_HOST` - Redis host
- `REDIS_PORT` - Redis port
- `REDIS_PASSWORD` - Redis password
- `CACHE_TTL` - Default TTL in seconds

### auth.yml
**Purpose:** Authentication settings

```yaml
auth:
  jwt:
    secret: ${JWT_SECRET}
    algorithm: HS256
    expiration: 3600  # 1 hour

  oauth:
    enabled: false
    providers:
      google:
        client_id: ${GOOGLE_CLIENT_ID}
        client_secret: ${GOOGLE_CLIENT_SECRET}

  # API keys
  api_keys:
    enabled: true
    rotation_days: 90

  # RBAC
  rbac:
    enabled: true
    default_role: user
```

**Environment Variables:**
- `JWT_SECRET` - JWT signing secret
- `JWT_EXPIRATION` - Token expiration in seconds
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret

### logging.yml
**Purpose:** Logging configuration

```yaml
logging:
  level: INFO
  format: json

  # Console output
  console:
    enabled: true
    level: INFO

  # File output
  file:
    enabled: true
    path: logs/veritas.log
    max_size_mb: 100
    max_backups: 10
    compress: true

  # External services
  external:
    sentry:
      enabled: true
      dsn: ${SENTRY_DSN}
      traces_sample_rate: 0.1
```

**Environment Variables:**
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARN, ERROR)
- `LOG_FORMAT` - Log format (json, text)
- `SENTRY_DSN` - Sentry error tracking DSN

### docker-compose.yml
**Purpose:** Docker services for development and production

```yaml
version: '3.8'

services:
  api:
    image: veritas:latest
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=postgres
      - REDIS_HOST=redis
      - OLLAMA_HOST=ollama:11434
    depends_on:
      - postgres
      - redis
      - ollama

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama

volumes:
  postgres_data:
  ollama_data:
```

**Usage:**
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f api

# Restart specific service
docker-compose restart redis
```

## Environment Configuration

### .env File
**Location:** `.env` (gitignored, create from `environment.example`)

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=veritas_db
DB_USER=veritas
DB_PASSWORD=secure_password

# API
API_HOST=0.0.0.0
API_PORT=8000

# LLM
LLM_PROVIDER=ollama
LLM_MODEL=neural-9b-german
OLLAMA_HOST=localhost
OLLAMA_PORT=11434

# RAG
RAG_ENABLED=true
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=your_api_key

# Cache
REDIS_HOST=localhost
REDIS_PORT=6379

# Auth
JWT_SECRET=your_jwt_secret

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://...
```

### Loading Environment Variables

**Python:**
```python
from dotenv import load_dotenv
import os

load_dotenv()
db_host = os.getenv('DB_HOST', 'localhost')
```

**Node.js:**
```javascript
require('dotenv').config();
const dbHost = process.env.DB_HOST || 'localhost';
```

**PowerShell:**
```powershell
Get-Content .env | ForEach-Object {
    $name, $value = $_ -split '='
    Set-Item -Path Env:$name -Value $value
}
```

## Configuration by Environment

### Development

```bash
# .env.development
LOG_LEVEL=DEBUG
API_CORS_ORIGINS=http://localhost:3000
CACHE_ENABLED=false
```

### Staging

```bash
# .env.staging
LOG_LEVEL=INFO
API_CORS_ORIGINS=https://staging.veritas.example.com
CACHE_ENABLED=true
```

### Production

```bash
# .env.production
LOG_LEVEL=WARN
API_CORS_ORIGINS=https://veritas.example.com
CACHE_ENABLED=true
LLM_TEMPERATURE=0.5
```

## Configuration Management

### Loading Configuration

**Priority (highest to lowest):**
1. Command-line arguments
2. Environment variables
3. `.env` file
4. YAML configuration files
5. Built-in defaults

### Validation

All configuration is validated on startup:
```bash
python -m veritas.config --validate
```

**Validation checks:**
- Required fields present
- Type correctness
- Range validation
- Connectivity checks
- Permission verification

### Hot Reload

Some configuration can be reloaded without restart:
```bash
# Reload logging configuration
curl -X POST http://localhost:8000/api/v1/admin/config/reload/logging

# Reload cache configuration
curl -X POST http://localhost:8000/api/v1/admin/config/reload/cache
```

## Security Best Practices

### Secrets Management

✅ **DO:**
- Store secrets in `.env` (gitignored)
- Use environment variables in production
- Rotate secrets regularly
- Use strong passwords

❌ **DON'T:**
- Commit `.env` to repository
- Hardcode secrets in code
- Share `.env` files
- Use default passwords

### Configuration Files

✅ **DO:**
- Version control `.yaml` files (no secrets)
- Use example files (`.example`)
- Document all options
- Use restrictive file permissions

❌ **DON'T:**
- Store passwords in YAML
- Commit sensitive data
- Use world-readable configs
- Leave defaults unchanged

### Encryption

```bash
# Encrypt sensitive configuration
openssl enc -aes-256-cbc -in config/auth.yml -out config/auth.yml.enc

# Decrypt on startup
openssl enc -d -aes-256-cbc -in config/auth.yml.enc -out config/auth.yml
```

## Troubleshooting

### Configuration Not Loading

```bash
# Check configuration syntax
python -m veritas.config --validate

# Print effective configuration
python -m veritas.config --print

# Check environment variables
env | grep VERITAS
```

### Connection Failures

```bash
# Test database connection
psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME}

# Test Redis connection
redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} ping

# Test Ollama connection
curl http://${OLLAMA_HOST}:${OLLAMA_PORT}/api/tags
```

### Performance Issues

```bash
# Check cache configuration
curl http://localhost:8000/api/v1/admin/config/cache

# Check thread count
curl http://localhost:8000/api/v1/admin/config/performance

# Review logging level (too verbose?)
grep LOG_LEVEL .env
```

## Configuration Reference

| Variable | Type | Default | Required |
|----------|------|---------|----------|
| DB_HOST | string | localhost | Yes |
| DB_PORT | int | 5432 | No |
| DB_NAME | string | veritas_db | Yes |
| DB_USER | string | - | Yes |
| DB_PASSWORD | string | - | Yes |
| API_PORT | int | 8000 | No |
| LLM_MODEL | string | neural-9b | No |
| OLLAMA_HOST | string | localhost | No |
| REDIS_HOST | string | localhost | No |
| JWT_SECRET | string | - | Yes |
| LOG_LEVEL | enum | INFO | No |

## Related Documentation

- See `DEVELOPMENT.md` for development setup
- See `.env.example` for example configuration
- See `docker-compose.yml` for Docker setup
- See backend README for specific service configs

---

**Last Updated:** December 4, 2025
**Status:** Production Ready ✅
**Configuration Files:** 10+
**Environments:** Development, Staging, Production
