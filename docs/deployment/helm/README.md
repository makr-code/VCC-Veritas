# VERITAS Helm Chart

Production-ready Helm chart for deploying VERITAS Framework to Kubernetes.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- PV provisioner support in the underlying infrastructure
- Cert-manager (optional, for automatic TLS certificate management)

## Installing the Chart

### Production

```bash
# Add repository (if published)
helm repo add veritas https://charts.veritas.example.com
helm repo update

# Install with production values
helm install veritas veritas/veritas \
  --namespace veritas-production \
  --create-namespace \
  --values values.yaml \
  --set secrets.database.password=YOUR_DB_PASSWORD \
  --set secrets.redis.password=YOUR_REDIS_PASSWORD \
  --set secrets.jwt.secretKey=YOUR_JWT_SECRET \
  --set ingress.hosts[0].host=api.veritas.example.com
```

### Staging

```bash
helm install veritas veritas/veritas \
  --namespace veritas-staging \
  --create-namespace \
  --values values-staging.yaml \
  --set ingress.hosts[0].host=staging.api.veritas.example.com
```

### Local Development

```bash
# Install from local chart
helm install veritas ./helm/veritas \
  --namespace veritas-dev \
  --create-namespace \
  --values helm/veritas/values-dev.yaml
```

## Upgrading the Chart

```bash
# Production
helm upgrade veritas veritas/veritas \
  --namespace veritas-production \
  --values values.yaml \
  --reuse-values

# Staging
helm upgrade veritas veritas/veritas \
  --namespace veritas-staging \
  --values values-staging.yaml \
  --reuse-values
```

## Uninstalling the Chart

```bash
# Production
helm uninstall veritas --namespace veritas-production

# Staging
helm uninstall veritas --namespace veritas-staging
```

## Configuration

The following table lists the configurable parameters and their default values.

### Global Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.environment` | Environment name | `production` |
| `global.imageRegistry` | Container registry | `""` |
| `global.imagePullSecrets` | Image pull secrets | `[]` |

### API Service

| Parameter | Description | Default |
|-----------|-------------|---------|
| `api.enabled` | Enable API service | `true` |
| `api.replicaCount` | Number of replicas | `3` |
| `api.image.repository` | Image repository | `veritas/api` |
| `api.image.tag` | Image tag | `latest` |
| `api.image.pullPolicy` | Image pull policy | `Always` |
| `api.resources.requests.cpu` | CPU request | `500m` |
| `api.resources.requests.memory` | Memory request | `512Mi` |
| `api.resources.limits.cpu` | CPU limit | `2000m` |
| `api.resources.limits.memory` | Memory limit | `2Gi` |
| `api.autoscaling.enabled` | Enable HPA | `true` |
| `api.autoscaling.minReplicas` | Minimum replicas | `3` |
| `api.autoscaling.maxReplicas` | Maximum replicas | `10` |

### Worker Service

| Parameter | Description | Default |
|-----------|-------------|---------|
| `worker.enabled` | Enable worker service | `true` |
| `worker.replicaCount` | Number of replicas | `2` |
| `worker.image.repository` | Image repository | `veritas/worker` |
| `worker.image.tag` | Image tag | `latest` |
| `worker.resources.requests.cpu` | CPU request | `1000m` |
| `worker.resources.requests.memory` | Memory request | `1Gi` |

### Ingress

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class | `nginx` |
| `ingress.hosts[0].host` | Hostname | `api.veritas.example.com` |
| `ingress.tls[0].secretName` | TLS secret | `veritas-tls-cert` |

### Persistence

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable persistence | `true` |
| `persistence.uploads.size` | Upload storage size | `50Gi` |
| `persistence.data.size` | Data storage size | `100Gi` |

### Secrets

**IMPORTANT**: Change all default secret values in production!

| Parameter | Description | Default |
|-----------|-------------|---------|
| `secrets.database.password` | Database password | `CHANGE_ME_IN_PRODUCTION` |
| `secrets.redis.password` | Redis password | `CHANGE_ME_IN_PRODUCTION` |
| `secrets.jwt.secretKey` | JWT secret key | `CHANGE_ME...` |
| `secrets.apiKeys.admin` | Admin API key | `CHANGE_ME_IN_PRODUCTION` |
| `secrets.encryption.key` | Encryption key | `CHANGE_ME...` |

## Examples

### Custom Resource Limits

```bash
helm install veritas ./helm/veritas \
  --set api.resources.limits.cpu=4000m \
  --set api.resources.limits.memory=4Gi \
  --set worker.resources.limits.cpu=8000m
```

### Custom Scaling

```bash
helm install veritas ./helm/veritas \
  --set api.autoscaling.minReplicas=5 \
  --set api.autoscaling.maxReplicas=20 \
  --set api.autoscaling.targetCPUUtilizationPercentage=60
```

### Disable Worker

```bash
helm install veritas ./helm/veritas \
  --set worker.enabled=false
```

## Monitoring

The chart exposes Prometheus metrics on `/api/v1/metrics`. Annotations are automatically added for Prometheus scraping.

```yaml
prometheus.io/scrape: "true"
prometheus.io/port: "8000"
prometheus.io/path: "/api/v1/metrics"
```

## Security

- Pods run as non-root user (UID 1000)
- Read-only root filesystem where possible
- All capabilities dropped
- Resource limits enforced
- Network policies recommended

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n veritas-production
kubectl describe pod <pod-name> -n veritas-production
kubectl logs <pod-name> -n veritas-production
```

### Check Ingress

```bash
kubectl get ingress -n veritas-production
kubectl describe ingress veritas -n veritas-production
```

### Check HPA

```bash
kubectl get hpa -n veritas-production
kubectl describe hpa veritas-api-hpa -n veritas-production
```

### Check Secrets

```bash
kubectl get secrets -n veritas-production
kubectl describe secret veritas-secrets -n veritas-production
```

## Support

For issues and questions:
- GitHub: https://github.com/veritas/veritas
- Email: veritas@example.com
