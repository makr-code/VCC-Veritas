# Deployment Guide

**Version:** 1.0
**Status:** ✅ Production Ready
**Zielgruppe:** DevOps, Sysadmin, Operations

---

## 🎯 Übersicht

Dieser Guide zeigt, wie VERITAS in Production bereitgestellt wird.

### Deployment-Optionen

1. **Docker** - Schnellste Option (recommended)
2. **Docker Compose** - Mit allen Services
3. **Kubernetes** - Enterprise-Deployment
4. **Bare Metal** - Manuelle Installation

---

## 🚀 Option 1: Docker (Recommended)

### Schritt 1: Docker Image bauen
```bash
docker build -t veritas:latest .
```

### Schritt 2: Container starten
```bash
docker run -d \
  --name veritas \
  -p 5000:5000 \
  -e VERITAS_LOG_LEVEL=INFO \
  -e DATABASE_URL=postgresql://user:pass@db:5432/veritas \
  veritas:latest
```

### Schritt 3: Health Check
```bash
curl http://localhost:5000/api/system/health
```

---

## 🐳 Option 2: Docker Compose

### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    image: veritas:latest
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/veritas
      - CHROMADB_URL=http://chromadb:8000
      - NEO4J_URL=bolt://neo4j:7687
    depends_on:
      - postgres
      - chromadb
      - neo4j

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=secret
    volumes:
      - postgres_data:/var/lib/postgresql/data

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"

  neo4j:
    image: neo4j:5
    environment:
      - NEO4J_AUTH=neo4j/password
    ports:
      - "7687:7687"

volumes:
  postgres_data:
```

### Starten
```bash
docker-compose up -d
```

---

## ☸️ Option 3: Kubernetes

### Deployment erstellen
```bash
kubectl apply -f k8s/deployment.yaml
```

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: veritas-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: veritas-backend
  template:
    metadata:
      labels:
        app: veritas-backend
    spec:
      containers:
      - name: backend
        image: veritas:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: veritas-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /api/system/health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 10
```

### Service erstellen
```bash
kubectl apply -f k8s/service.yaml
```

---

## ⚙️ Konfiguration

### Umgebungsvariablen

```bash
# Logging
export VERITAS_LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR

# API Server
export VERITAS_API_HOST=0.0.0.0            # Bind address
export VERITAS_API_PORT=5000               # Port
export VERITAS_API_RELOAD=false            # Auto-reload

# Database
export DATABASE_URL=postgresql://user:pass@localhost/veritas

# Search Engines
export CHROMADB_URL=http://localhost:8000
export NEO4J_URL=bolt://neo4j:7687
export NEO4J_AUTH=neo4j:password

# LLM
export OLLAMA_BASE_URL=http://localhost:11434
export LLM_MODEL=neural-chat               # oder andere Modelle

# Features
export ENABLE_STREAMING=true
export ENABLE_RAG=true
export ENABLE_AGENTS=true
```

### Config File (veritas.yaml)
```yaml
api:
  host: 0.0.0.0
  port: 5000
  reload: false

logging:
  level: INFO
  format: json

database:
  url: postgresql://localhost/veritas
  pool_size: 20

search:
  chromadb:
    url: http://localhost:8000
  neo4j:
    url: bolt://localhost:7687
```

---

## 🔍 Health Checks & Monitoring

### Liveness Check
```bash
curl http://localhost:5000/api/system/health
```

### Readiness Check
```bash
curl http://localhost:5000/api/system/capabilities
```

### Prometheus Metriken
```bash
curl http://localhost:5000/metrics
```

---

## 📊 Production Checklist

- [ ] SSL/TLS Certificate installiert
- [ ] Database Backup konfiguriert
- [ ] Logging zentralisiert (ELK Stack, etc.)
- [ ] Monitoring aufgesetzt (Prometheus, Grafana)
- [ ] Load Balancer konfiguriert
- [ ] Autoscaling aktiviert
- [ ] Secrets Management (Vault, etc.)
- [ ] Disaster Recovery Plan

---

## 🚨 Troubleshooting

### Backend startet nicht
```bash
# Logs ansehen
docker logs veritas
```

### Database Connection Error
```bash
# Connection testen
psql postgresql://user:pass@localhost/veritas
```

### Performance Probleme
→ Siehe [Monitoring](MONITORING.md)

---

## 📚 Weiterführende Guides

- **[Docker Setup](DOCKER.md)** - Docker im Detail
- **[Kubernetes](KUBERNETES.md)** - K8S Setup
- **[Konfiguration](CONFIGURATION.md)** - Alle Config-Options
- **[Monitoring](MONITORING.md)** - Observability

---

**Bereit?** → [Docker Setup](DOCKER.md) oder [Kubernetes](KUBERNETES.md)
