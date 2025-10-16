# VERITAS Framework - Docker & Kubernetes Deployment Guide

Complete guide for deploying VERITAS to production using Docker and Kubernetes.

## Table of Contents

1. [Overview](#overview)
2. [Docker Images](#docker-images)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Helm Chart](#helm-chart)
5. [Production Deployment](#production-deployment)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Overview

VERITAS provides production-ready deployment configurations for:
- **Docker**: Multi-stage optimized images
- **Kubernetes**: Native manifests for staging and production
- **Helm**: Templated charts for easy deployment
- **Nginx**: Reverse proxy with SSL termination

### Architecture

```
┌─────────────┐
│   Ingress   │ (TLS, Rate Limiting)
│   (Nginx)   │
└──────┬──────┘
       │
┌──────▼──────────────────┐
│   Kubernetes Cluster    │
│  ┌──────────────────┐   │
│  │ API Pods (3-10)  │   │ (Auto-scaling)
│  └────────┬─────────┘   │
│  ┌────────▼─────────┐   │
│  │ Worker Pods (2-8)│   │ (Background tasks)
│  └──────────────────┘   │
│  ┌──────────────────┐   │
│  │  PostgreSQL      │   │
│  │  Redis           │   │
│  │  Prometheus      │   │
│  └──────────────────┘   │
└─────────────────────────┘
```

---

## Docker Images

### Available Images

1. **veritas/api** - FastAPI application server
2. **veritas/worker** - Celery background workers
3. **veritas/nginx** - Reverse proxy with SSL

### Building Images

#### Using Build Script

```bash
# Build all images with version tag
VERSION=1.0.0 ./scripts/build-docker.sh

# Build with custom registry
DOCKER_REGISTRY=registry.example.com VERSION=1.0.0 ./scripts/build-docker.sh
```

#### Manual Build

```bash
# API image
docker build -t veritas/api:latest -f Dockerfile.production .

# Worker image
docker build -t veritas/worker:latest -f Dockerfile.worker .

# Nginx image
docker build -t veritas/nginx:latest -f Dockerfile.nginx .
```

### Image Details

#### API Image (`Dockerfile.production`)

- **Base**: `python:3.11-slim`
- **Build**: Multi-stage (builder + runtime)
- **Size**: ~350MB
- **Features**:
  - Non-root user (UID 1000)
  - Virtual environment
  - Health checks
  - Minimal dependencies

**Security Features:**
- ✅ Non-root user
- ✅ Read-only root filesystem (where possible)
- ✅ No unnecessary packages
- ✅ Health checks
- ✅ Resource limits

#### Worker Image (`Dockerfile.worker`)

- **Base**: `python:3.11-slim`
- **Size**: ~360MB
- **Features**:
  - Celery worker with Redis backend
  - Non-root user (UID 1001)
  - Automatic task retries
  - Health monitoring

#### Nginx Image (`Dockerfile.nginx`)

- **Base**: `nginx:1.25-alpine`
- **Size**: ~25MB
- **Features**:
  - SSL/TLS termination
  - WebSocket support
  - Rate limiting
  - Compression (gzip)

### Testing Images Locally

```bash
# Run API container
docker run -d -p 8000:8000 \
  -e VERITAS_ENV=production \
  -e DB_HOST=localhost \
  -e REDIS_HOST=localhost \
  veritas/api:latest

# Health check
curl http://localhost:8000/api/v1/health

# Run worker
docker run -d \
  -e VERITAS_ENV=production \
  -e REDIS_HOST=localhost \
  veritas/worker:latest
```

### Pushing Images to Registry

```bash
# Tag images
docker tag veritas/api:latest registry.example.com/veritas/api:1.0.0
docker tag veritas/worker:latest registry.example.com/veritas/worker:1.0.0
docker tag veritas/nginx:latest registry.example.com/veritas/nginx:1.0.0

# Push images
docker push registry.example.com/veritas/api:1.0.0
docker push registry.example.com/veritas/worker:1.0.0
docker push registry.example.com/veritas/nginx:1.0.0
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes 1.24+
- kubectl configured
- Persistent volume provisioner
- Cert-manager (optional, for TLS)

### Quick Start

#### 1. Create Namespace

```bash
kubectl create namespace veritas-production
```

#### 2. Create Secrets

```bash
# Create secret from file
kubectl create secret generic veritas-secrets \
  --from-literal=DB_PASSWORD=your_db_password \
  --from-literal=REDIS_PASSWORD=your_redis_password \
  --from-literal=JWT_SECRET_KEY=your_jwt_secret \
  -n veritas-production
```

#### 3. Apply Manifests

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/deployment-api.yaml
kubectl apply -f k8s/deployment-worker.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

#### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n veritas-production

# Check services
kubectl get svc -n veritas-production

# Check ingress
kubectl get ingress -n veritas-production

# View logs
kubectl logs -f deployment/veritas-api -n veritas-production
```

### Kubernetes Resources

#### Deployments

**API Deployment** (`k8s/deployment-api.yaml`):
- **Replicas**: 3 (production), 1 (staging)
- **Strategy**: RollingUpdate (maxSurge: 1, maxUnavailable: 0)
- **Resources**: 
  - Requests: 500m CPU, 512Mi RAM
  - Limits: 2000m CPU, 2Gi RAM
- **Probes**: 
  - Liveness: HTTP GET `/api/v1/health` (30s delay, 10s interval)
  - Readiness: HTTP GET `/api/v1/health` (10s delay, 5s interval)

**Worker Deployment** (`k8s/deployment-worker.yaml`):
- **Replicas**: 2 (production), 1 (staging)
- **Resources**:
  - Requests: 1000m CPU, 1Gi RAM
  - Limits: 4000m CPU, 4Gi RAM

#### Services

**API Service** (`k8s/service.yaml`):
- Type: ClusterIP
- Port: 8000
- Session Affinity: ClientIP (3h timeout for WebSocket)

#### Ingress

**Ingress** (`k8s/ingress.yaml`):
- Class: nginx
- TLS: cert-manager automatic certificates
- Rate limiting: 100 req/s
- WebSocket support
- Security headers

#### Horizontal Pod Autoscaler

**API HPA** (`k8s/hpa.yaml`):
- Min: 3 replicas
- Max: 10 replicas
- Target: 70% CPU, 80% Memory
- Scale down: 50% / 60s (min), 2 pods / 60s
- Scale up: 100% / 30s (max), 4 pods / 30s

**Worker HPA**:
- Min: 2 replicas
- Max: 8 replicas
- Target: 75% CPU, 85% Memory

#### Persistent Storage

**PVC** (`k8s/pvc.yaml`):
- **Uploads**: 50Gi (ReadWriteMany)
- **Data**: 100Gi (ReadWriteMany)
- **PostgreSQL**: 100Gi (ReadWriteOnce)
- **Redis**: 10Gi (ReadWriteOnce)

---

## Helm Chart

### Installation

#### Production

```bash
helm install veritas ./helm/veritas \
  --namespace veritas-production \
  --create-namespace \
  --values helm/veritas/values.yaml \
  --set secrets.database.password=STRONG_PASSWORD \
  --set secrets.redis.password=STRONG_PASSWORD \
  --set secrets.jwt.secretKey=STRONG_SECRET \
  --set ingress.hosts[0].host=api.veritas.example.com
```

#### Staging

```bash
helm install veritas ./helm/veritas \
  --namespace veritas-staging \
  --create-namespace \
  --values helm/veritas/values-staging.yaml
```

### Upgrading

```bash
helm upgrade veritas ./helm/veritas \
  --namespace veritas-production \
  --reuse-values \
  --wait \
  --timeout 10m
```

### Rollback

```bash
# List releases
helm history veritas -n veritas-production

# Rollback to previous version
helm rollback veritas -n veritas-production

# Rollback to specific revision
helm rollback veritas 3 -n veritas-production
```

### Uninstalling

```bash
helm uninstall veritas -n veritas-production
```

### Chart Configuration

Key configuration values in `values.yaml`:

```yaml
api:
  replicaCount: 3
  image:
    repository: veritas/api
    tag: latest
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 2000m
      memory: 2Gi

worker:
  replicaCount: 2
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 8

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: api.veritas.example.com

persistence:
  uploads:
    size: 50Gi
  data:
    size: 100Gi
```

---

## Production Deployment

### Step-by-Step Production Deployment

#### 1. Prepare Environment

```bash
# Set variables
export ENVIRONMENT=production
export NAMESPACE=veritas-production
export DOMAIN=api.veritas.example.com
export DB_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)
export JWT_SECRET=$(openssl rand -base64 64)
export ENCRYPTION_KEY=$(openssl rand -base64 32)
```

#### 2. Create Namespace

```bash
kubectl create namespace ${NAMESPACE}
kubectl label namespace ${NAMESPACE} environment=production
```

#### 3. Setup Secrets

```bash
# Create secrets
kubectl create secret generic veritas-secrets \
  --from-literal=DB_HOST=postgres.${NAMESPACE}.svc.cluster.local \
  --from-literal=DB_PASSWORD=${DB_PASSWORD} \
  --from-literal=REDIS_HOST=redis.${NAMESPACE}.svc.cluster.local \
  --from-literal=REDIS_PASSWORD=${REDIS_PASSWORD} \
  --from-literal=JWT_SECRET_KEY=${JWT_SECRET} \
  --from-literal=ENCRYPTION_KEY=${ENCRYPTION_KEY} \
  -n ${NAMESPACE}

# Verify secret (don't show values)
kubectl get secret veritas-secrets -n ${NAMESPACE}
```

#### 4. Deploy Database & Redis

```bash
# Deploy PostgreSQL (using Bitnami Helm chart)
helm install postgres bitnami/postgresql \
  --namespace ${NAMESPACE} \
  --set auth.password=${DB_PASSWORD} \
  --set primary.persistence.size=100Gi

# Deploy Redis
helm install redis bitnami/redis \
  --namespace ${NAMESPACE} \
  --set auth.password=${REDIS_PASSWORD} \
  --set master.persistence.size=10Gi
```

#### 5. Deploy VERITAS

```bash
# Using deployment script
./scripts/deploy-k8s.sh production

# Or using Helm directly
helm install veritas ./helm/veritas \
  --namespace ${NAMESPACE} \
  --values helm/veritas/values.yaml \
  --wait \
  --timeout 10m
```

#### 6. Configure TLS

```bash
# Install cert-manager (if not already installed)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Certificate will be auto-created by ingress
```

#### 7. Verify Deployment

```bash
# Check all resources
kubectl get all -n ${NAMESPACE}

# Check pods are running
kubectl get pods -n ${NAMESPACE} -w

# Check ingress
kubectl get ingress -n ${NAMESPACE}

# Test health endpoint
curl https://${DOMAIN}/api/v1/health
```

#### 8. Setup Monitoring

```bash
# Deploy Prometheus (if not already installed)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# Configure ServiceMonitor for VERITAS
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: veritas-api
  namespace: ${NAMESPACE}
spec:
  selector:
    matchLabels:
      app: veritas
      component: api
  endpoints:
  - port: http
    path: /api/v1/metrics
EOF
```

### Production Checklist

- [ ] Strong passwords/secrets generated
- [ ] TLS certificates configured
- [ ] Database backups scheduled
- [ ] Monitoring configured
- [ ] Log aggregation setup
- [ ] Resource limits set
- [ ] HPA configured
- [ ] Network policies applied
- [ ] RBAC configured
- [ ] Ingress rate limiting active
- [ ] Health checks passing
- [ ] Persistent storage provisioned

---

## Monitoring & Maintenance

### Monitoring

#### Prometheus Metrics

```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Access at http://localhost:9090
```

**Key Metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `agent_execution_duration_seconds` - Agent execution time
- `quality_score` - Quality check scores
- `worker_tasks_total` - Worker task count

#### Logs

```bash
# View API logs
kubectl logs -f deployment/veritas-api -n veritas-production

# View worker logs
kubectl logs -f deployment/veritas-worker -n veritas-production

# View all logs with label
kubectl logs -f -l app=veritas -n veritas-production --all-containers

# Tail last 100 lines
kubectl logs --tail=100 deployment/veritas-api -n veritas-production
```

### Maintenance

#### Scaling

```bash
# Manual scale API
kubectl scale deployment veritas-api --replicas=5 -n veritas-production

# Manual scale workers
kubectl scale deployment veritas-worker --replicas=4 -n veritas-production
```

#### Updates

```bash
# Update image
kubectl set image deployment/veritas-api api=veritas/api:1.1.0 -n veritas-production

# Watch rollout
kubectl rollout status deployment/veritas-api -n veritas-production

# Rollback if needed
kubectl rollout undo deployment/veritas-api -n veritas-production
```

#### Database Backup

```bash
# Manual backup
kubectl exec -it postgres-postgresql-0 -n veritas-production -- \
  pg_dump -U veritas_user veritas_production > backup-$(date +%Y%m%d).sql

# Restore from backup
kubectl exec -i postgres-postgresql-0 -n veritas-production -- \
  psql -U veritas_user veritas_production < backup-20250108.sql
```

---

## Troubleshooting

### Common Issues

#### Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n veritas-production

# Check events
kubectl get events -n veritas-production --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n veritas-production
```

**Common Causes:**
- Image pull errors → Check image registry credentials
- OOMKilled → Increase memory limits
- CrashLoopBackOff → Check application logs
- Pending → Check PVC/node resources

#### Service Not Accessible

```bash
# Check service
kubectl describe svc veritas-api -n veritas-production

# Check endpoints
kubectl get endpoints veritas-api -n veritas-production

# Test from within cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://veritas-api.veritas-production.svc.cluster.local:8000/api/v1/health
```

#### Ingress Issues

```bash
# Check ingress
kubectl describe ingress veritas -n veritas-production

# Check certificate
kubectl get certificate -n veritas-production

# Check cert-manager logs
kubectl logs -f -n cert-manager deployment/cert-manager
```

#### Database Connection Issues

```bash
# Test database connectivity
kubectl run -it --rm psql-test --image=postgres:15 --restart=Never -- \
  psql -h postgres-postgresql.veritas-production.svc.cluster.local -U veritas_user -d veritas_production

# Check database pod
kubectl logs -f postgres-postgresql-0 -n veritas-production
```

### Performance Tuning

#### API Performance

```yaml
# Increase resources
resources:
  requests:
    cpu: 1000m
    memory: 1Gi
  limits:
    cpu: 4000m
    memory: 4Gi

# Increase replicas
replicas: 5
```

#### Worker Performance

```yaml
# Increase concurrency
env:
  - name: WORKER_CONCURRENCY
    value: "8"
  
# Add more workers
replicas: 4
```

#### Database Performance

```yaml
# Increase connection pool
env:
  - name: DB_POOL_SIZE
    value: "40"
  - name: DB_MAX_OVERFLOW
    value: "20"
```

### Debug Commands

```bash
# Get all resources
kubectl get all -n veritas-production

# Get resource usage
kubectl top pods -n veritas-production
kubectl top nodes

# Execute shell in pod
kubectl exec -it <pod-name> -n veritas-production -- /bin/bash

# Port forward for debugging
kubectl port-forward deployment/veritas-api 8000:8000 -n veritas-production

# View HPA status
kubectl get hpa -n veritas-production
kubectl describe hpa veritas-api-hpa -n veritas-production

# Check PVC status
kubectl get pvc -n veritas-production
kubectl describe pvc veritas-uploads-pvc -n veritas-production
```

---

## Best Practices

### Security

1. **Always use secrets for sensitive data**
   ```bash
   kubectl create secret generic ... --from-literal=...
   ```

2. **Enable RBAC and network policies**
3. **Use non-root containers**
4. **Enable Pod Security Standards**
5. **Regular security updates**

### High Availability

1. **Multiple replicas** (min 3 for API)
2. **Pod anti-affinity** (spread across nodes)
3. **HPA for auto-scaling**
4. **Database replication**
5. **Regular backups**

### Performance

1. **Resource limits** properly configured
2. **Horizontal scaling** for load
3. **Connection pooling** for database
4. **Caching** with Redis
5. **CDN** for static assets

### Monitoring

1. **Prometheus metrics** enabled
2. **Grafana dashboards** configured
3. **Log aggregation** (ELK/Loki)
4. **Alerting** setup
5. **Health checks** active

---

## Support

For issues and questions:
- **GitHub**: https://github.com/veritas/veritas
- **Email**: veritas@example.com
- **Documentation**: https://docs.veritas.example.com
