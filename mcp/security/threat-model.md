# MCP Server Threat Model

## Overview

This document identifies potential security threats and mitigation strategies for the MCP server.

## Threat Categories

### 1. Unauthorized Access

**Threat**: Unauthorized clients accessing the server.

**Mitigation**:
- File-based token authentication for WebSocket mode
- UNIX domain socket ACLs for local connections
- Rate limiting to prevent brute force attacks

**Risk Level**: Medium (Production), Low (Local Dev)

### 2. Denial of Service

**Threat**: Malicious clients flooding the server with requests.

**Mitigation**:
- Token bucket rate limiting per method
- Global concurrency limit (32 concurrent requests)
- Request timeout (30s default)
- Bounded request queue (100 items max)

**Risk Level**: Medium

### 3. Injection Attacks

**Threat**: Malformed JSON or SQL injection via tool parameters.

**Mitigation**:
- JSON Schema validation for all tool inputs
- Parameterized database queries (SQLAlchemy ORM)
- Path allowlists for file operations
- Input sanitization in prompt rendering

**Risk Level**: Low (with validation), High (without)

### 4. Resource Exhaustion

**Threat**: Clients reading large resources or triggering expensive operations.

**Mitigation**:
- Size limits on request payloads (1MB default)
- Time limits on operations (30s default)
- Pagination and range requests for resources
- Cancellation support for long-running operations

**Risk Level**: Medium

### 5. Information Disclosure

**Threat**: Sensitive data exposed in logs or error messages.

**Mitigation**:
- Secrets redaction middleware
- Structured logging with log levels
- No secrets in error messages
- Audit logging for sensitive operations

**Risk Level**: Medium

### 6. Command Injection

**Threat**: Shell command execution via tool parameters.

**Mitigation**:
- No shell execution by default
- Sandboxing for any external execution (future)
- Capability flags for dangerous operations
- Input validation and escaping

**Risk Level**: Low (current), High (if shell exec added)

## Security Controls

### Authentication

**Local Development**:
- No authentication (stdio mode)
- Trust local environment

**Production**:
- File-based token (WebSocket mode)
- mTLS option (future)
- UNIX domain socket ACLs

### Authorization

- Capability-based access control
- Method-level rate limiting
- Resource path allowlists

### Input Validation

- JSON Schema validation for all inputs
- Type checking and coercion
- Path sanitization
- Size limits

### Rate Limiting

- Token bucket per method (100 req/min default)
- Global concurrency limit (32 concurrent)
- Request timeout (30s default)

### Logging and Monitoring

- Structured JSON logs
- Request ID correlation
- Error tracking
- Performance metrics

## Security Checklist

- [x] Input validation (JSON Schema)
- [x] Rate limiting (token bucket)
- [x] Timeout handling
- [x] Concurrency limits
- [x] Secrets redaction
- [x] Structured logging
- [x] Error sanitization
- [ ] Shell execution disabled (default)
- [ ] Path allowlists (resources)
- [ ] Authentication (production mode)
- [ ] mTLS support (future)
- [ ] Audit logging (comprehensive)

## Recommendations

1. **Enable authentication in production**: Use file-based tokens or mTLS
2. **Monitor rate limits**: Adjust based on load patterns
3. **Review logs regularly**: Detect anomalies and attacks
4. **Update dependencies**: Keep security patches current
5. **Regular audits**: Review threat model and controls

