# MCP Server Deployment Guide

## Quick Start

### Stdio Mode (Development)

```bash
# Install
cd mcp
pip install -e .

# Run
python -m mcp.server --transport stdio
```

### WebSocket Mode

```bash
# Run WebSocket server
python -m mcp.server --transport websocket --host localhost --port 8080
```

## Docker Deployment

### Build Image

```bash
cd mcp/ops
docker build -f Dockerfile -t assistant-mcp-server:1.0.0 ../..
```

### Run with Docker Compose

```bash
cd mcp/ops
docker-compose up -d
```

### Run Standalone Container

```bash
docker run -d \
  --name assistant-mcp-server \
  -p 8080:8080 \
  -e MCP_TRANSPORT=websocket \
  -e DATABASE_URL=postgresql://user:pass@db:5432/assistant \
  assistant-mcp-server:1.0.0
```

## systemd Deployment

### Install Service

```bash
# Copy service file
sudo cp mcp/ops/systemd.service /etc/systemd/system/assistant-mcp.service

# Edit service file (adjust paths and environment)
sudo nano /etc/systemd/system/assistant-mcp.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable assistant-mcp

# Start service
sudo systemctl start assistant-mcp

# Check status
sudo systemctl status assistant-mcp

# View logs
sudo journalctl -u assistant-mcp -f
```

### Service Configuration

Edit `/etc/systemd/system/assistant-mcp.service`:

```ini
[Service]
Environment="MCP_TRANSPORT=stdio"
Environment="DATABASE_URL=postgresql://user:pass@localhost/assistant"
Environment="MCP_LOG_LEVEL=INFO"
Environment="MCP_MAX_CONCURRENT=32"
```

## Kubernetes Deployment

### Apply Configuration

```bash
# Apply deployment
kubectl apply -f mcp/ops/k8s-deployment.yaml

# Check deployment
kubectl get deployment assistant-mcp-server

# Check pods
kubectl get pods -l app=assistant-mcp-server

# Check service
kubectl get service assistant-mcp-server

# View logs
kubectl logs -l app=assistant-mcp-server -f
```

### Configuration

Edit `k8s-deployment.yaml`:

- **Replicas**: Adjust `spec.replicas` for scaling
- **Resources**: Adjust `resources.requests` and `resources.limits`
- **Environment**: Update `env` variables
- **Secrets**: Configure `secretKeyRef` for sensitive data

## Environment Variables

### Required

- `DATABASE_URL`: PostgreSQL connection string

### Optional

- `MCP_TRANSPORT`: Transport type ("stdio" or "websocket")
- `MCP_HOST`: WebSocket bind host (default: "localhost")
- `MCP_PORT`: WebSocket bind port (default: 8080)
- `MCP_PATH`: WebSocket path (default: "/mcp")
- `MCP_MAX_CONCURRENT`: Maximum concurrent requests (default: 32)
- `MCP_DEFAULT_TIMEOUT`: Default timeout in seconds (default: 30.0)
- `MCP_LOG_LEVEL`: Log level ("DEBUG", "INFO", "WARN", "ERROR")
- `MCP_AUTH_REQUIRED`: Enable authentication (default: "false")
- `MCP_AUTH_TOKEN_FILE`: Path to token file

## Production Checklist

- [ ] Authentication enabled (`MCP_AUTH_REQUIRED=true`)
- [ ] Token file configured (`MCP_AUTH_TOKEN_FILE`)
- [ ] Rate limiting enabled
- [ ] Resource guards enabled
- [ ] Logging configured
- [ ] Secrets redaction enabled
- [ ] Firewall rules configured
- [ ] Process isolation (non-root user)
- [ ] Resource limits set
- [ ] Monitoring configured
- [ ] Backup strategy defined
- [ ] Disaster recovery plan documented

## Scaling

### Horizontal Scaling

**Kubernetes:**
```bash
kubectl scale deployment assistant-mcp-server --replicas=5
```

**Docker Compose:**
```yaml
services:
  mcp-server:
    deploy:
      replicas: 3
```

### Vertical Scaling

Adjust resource limits in deployment config:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Monitoring

### Health Checks

**HTTP (WebSocket mode):**
```bash
curl http://localhost:8080/health
```

**Logs:**
```bash
# Docker
docker logs assistant-mcp-server -f

# systemd
sudo journalctl -u assistant-mcp -f

# Kubernetes
kubectl logs -l app=assistant-mcp-server -f
```

### Metrics

Future: Prometheus-compatible metrics endpoint at `/metrics`

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.

## Security

See [security/](security/) for:
- Threat model
- Hardening guide
- Security checklist

