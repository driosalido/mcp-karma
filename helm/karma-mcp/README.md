# Karma MCP Helm Chart

Helm chart for deploying the Karma MCP Server in Kubernetes environments.

## Prerequisites

- Kubernetes 1.16+
- Helm 3.0+
- Access to a Karma Alert Dashboard instance

## Installation

### Add the chart repository (if published)

```bash
# If published to a Helm repository
helm repo add karma-mcp https://driosalido.github.io/mcp-karma
helm repo update
```

### Install from local chart

```bash
# Clone the repository
git clone https://github.com/driosalido/mcp-karma.git
cd mcp-karma

# Install the chart
helm install karma-mcp ./helm/karma-mcp
```

### Install with custom values

```bash
helm install karma-mcp ./helm/karma-mcp \
  --set config.karmaUrl="http://your-karma-instance:8080" \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host="karma-mcp.yourdomain.com"
```

## Configuration

The following table lists the configurable parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Container image repository | `driosalido/karma-mcp` |
| `image.tag` | Container image tag | `""` (uses appVersion) |
| `config.karmaUrl` | Karma server URL | `http://karma:8080` |
| `config.logLevel` | Log level (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `service.type` | Kubernetes service type | `ClusterIP` |
| `service.port` | Service port | `8080` |
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class name | `""` |
| `ingress.hosts[0].host` | Hostname for ingress | `karma-mcp.local` |
| `resources.requests.cpu` | CPU requests | `100m` |
| `resources.requests.memory` | Memory requests | `128Mi` |
| `resources.limits.cpu` | CPU limits | `500m` |
| `resources.limits.memory` | Memory limits | `512Mi` |
| `autoscaling.enabled` | Enable horizontal pod autoscaler | `false` |
| `persistence.enabled` | Enable persistent storage | `false` |

## Examples

### Basic deployment

```bash
helm install karma-mcp ./helm/karma-mcp \
  --set config.karmaUrl="http://karma.monitoring.svc.cluster.local:8080"
```

### With ingress and TLS

```bash
helm install karma-mcp ./helm/karma-mcp \
  --set config.karmaUrl="http://karma.monitoring.svc.cluster.local:8080" \
  --set ingress.enabled=true \
  --set ingress.className="nginx" \
  --set ingress.hosts[0].host="karma-mcp.example.com" \
  --set ingress.tls[0].secretName="karma-mcp-tls" \
  --set ingress.tls[0].hosts[0]="karma-mcp.example.com"
```

### With autoscaling

```bash
helm install karma-mcp ./helm/karma-mcp \
  --set config.karmaUrl="http://karma.monitoring.svc.cluster.local:8080" \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=2 \
  --set autoscaling.maxReplicas=10 \
  --set autoscaling.targetCPUUtilizationPercentage=70
```

### Custom values file

Create a `values-prod.yaml`:

```yaml
replicaCount: 2

config:
  karmaUrl: "http://karma.monitoring.svc.cluster.local:8080"
  logLevel: "WARNING"

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
  hosts:
    - host: karma-mcp.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: karma-mcp-tls
      hosts:
        - karma-mcp.example.com

resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilizationPercentage: 70
```

Install with:

```bash
helm install karma-mcp ./helm/karma-mcp -f values-prod.yaml
```

## Uninstall

```bash
helm uninstall karma-mcp
```

## Health Checks

The chart includes liveness and readiness probes that check Karma connectivity. The health checks can be configured:

```yaml
healthCheck:
  enabled: true
  initialDelaySeconds: 30
  periodSeconds: 30
  timeoutSeconds: 10
  failureThreshold: 3
```

## Security

The chart follows security best practices:

- Runs as non-root user (UID 1000)
- Uses read-only root filesystem
- Drops all capabilities
- Includes resource limits
- Supports network policies (manual configuration)

## Troubleshooting

### Pod fails to start

Check the logs:

```bash
kubectl logs -l app.kubernetes.io/name=karma-mcp
```

### Health checks failing

Verify Karma connectivity:

```bash
kubectl exec deployment/karma-mcp -- python -c "
import sys; sys.path.append('/app/src')
from karma_mcp.server import check_karma
import asyncio
print(asyncio.run(check_karma()))
"
```

### Ingress not working

Check ingress configuration:

```bash
kubectl describe ingress karma-mcp
kubectl get ingress karma-mcp -o yaml
```