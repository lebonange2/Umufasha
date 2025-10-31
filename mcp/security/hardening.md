# MCP Server Hardening Guide

## Configuration

### Production Settings

```python
# Environment variables
MCP_TRANSPORT=websocket
MCP_HOST=0.0.0.0  # Bind to all interfaces (use firewall to restrict)
MCP_PORT=8080
MCP_PATH=/mcp
MCP_MAX_CONCURRENT=32
MCP_DEFAULT_TIMEOUT=30.0

# Security settings
MCP_AUTH_REQUIRED=true
MCP_AUTH_TOKEN_FILE=/etc/mcp/tokens.txt
MCP_RATE_LIMIT_ENABLED=true
MCP_RATE_LIMIT_REQUESTS_PER_MINUTE=100
MCP_RATE_LIMIT_BURST=10
MCP_LOG_LEVEL=INFO
MCP_SECRETS_REDACTION=true
```

### Rate Limiting

Configure rate limits per method:

```python
# Default rate limits
RATE_LIMITS = {
    "tools/call": {"rate": 60.0, "capacity": 10},  # 60 req/min, burst 10
    "resources/read": {"rate": 120.0, "capacity": 20},
    "prompts/get": {"rate": 30.0, "capacity": 5}
}
```

### Resource Guards

Configure resource access controls:

```python
# Path allowlists
RESOURCE_ALLOWLIST = [
    "resources://users/*",
    "resources://events/*",
    "resources://notifications/*"
]

# Size limits
MAX_RESOURCE_SIZE = 1024 * 1024  # 1MB
MAX_REQUEST_SIZE = 1024 * 1024   # 1MB
```

## Authentication

### File-Based Tokens

1. Create token file:
```bash
echo "client-1:token-secret-123" >> /etc/mcp/tokens.txt
chmod 600 /etc/mcp/tokens.txt
```

2. Configure server:
```bash
export MCP_AUTH_TOKEN_FILE=/etc/mcp/tokens.txt
export MCP_AUTH_REQUIRED=true
```

### UNIX Domain Socket ACLs

For local connections:

```bash
# Set socket permissions
chmod 600 /tmp/mcp.sock
chown mcp:mcp /tmp/mcp.sock
```

## Logging

### Structured Logging

Logs are JSON-formatted:

```json
{
  "timestamp": "2024-01-15T09:00:00Z",
  "level": "INFO",
  "request_id": "req-123",
  "method": "tools/call",
  "duration_ms": 45.2,
  "status": "success"
}
```

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARN**: Warning conditions
- **ERROR**: Error conditions

### Secrets Redaction

Secrets are automatically redacted from logs:

```python
# Before redaction
{"api_key": "sk-1234567890abcdef"}

# After redaction
{"api_key": "***REDACTED***"}
```

## Monitoring

### Metrics

Prometheus-compatible metrics endpoint (future):

```
# Request count
mcp_requests_total{method="tools/call"} 1234

# Request duration
mcp_request_duration_seconds{method="tools/call",quantile="0.95"} 0.045

# Errors
mcp_errors_total{method="tools/call",error_code="-32602"} 5
```

### Health Checks

Health check endpoint (WebSocket mode):

```
GET /health
Response: {"status": "healthy", "version": "1.0.0"}
```

## Firewall Configuration

### WebSocket Mode

```bash
# Allow only localhost (for local clients)
iptables -A INPUT -p tcp --dport 8080 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j DROP

# Or allow specific IP range
iptables -A INPUT -p tcp --dport 8080 -s 10.0.0.0/24 -j ACCEPT
```

### Stdio Mode

No network exposure (uses pipes).

## Process Isolation

### User/Group

Run server as non-root user:

```bash
useradd -r -s /bin/false mcp
chown -R mcp:mcp /var/lib/mcp
```

### Resource Limits

Set resource limits:

```bash
# systemd service file
[Service]
User=mcp
Group=mcp
LimitNOFILE=1024
LimitNPROC=256
```

## Dependency Security

### SBOM

Generate Software Bill of Materials:

```bash
pip install cyclonedx-bom
cyclonedx-py -r requirements.txt -o SBOM.json
```

### Vulnerability Scanning

Regular vulnerability scans:

```bash
pip install safety
safety check -r requirements.txt
```

## Incident Response

### Detection

Monitor for:
- Unusual request patterns
- High error rates
- Resource exhaustion
- Authentication failures

### Response

1. **Rate Limit Violation**: Log and block client
2. **Authentication Failure**: Log and alert
3. **Resource Exhaustion**: Scale resources or reject requests
4. **Security Breach**: Immediate shutdown and investigation

## Security Checklist

- [ ] Authentication enabled (production)
- [ ] Rate limiting configured
- [ ] Resource guards enabled
- [ ] Logging configured
- [ ] Secrets redaction enabled
- [ ] Firewall rules configured
- [ ] Process isolation (non-root user)
- [ ] Resource limits set
- [ ] Dependency scanning enabled
- [ ] Monitoring configured
- [ ] Incident response plan documented

