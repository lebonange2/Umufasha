# MCP Server Design Notes

## Architecture Overview

This document maps the existing ASSISTANT application features to the Model Context Protocol (MCP) server surface. The MCP server exposes application capabilities as tools, resources, and prompts following the MCP specification.

## Module-to-MCP Mapping

### Tools (Parameterized Operations)

| Current Module | MCP Tool | Description |
|---------------|----------|-------------|
| `app/routes/users.py` | `tools.createUser` | Create a new user account |
| `app/routes/users.py` | `tools.updateUser` | Update user preferences |
| `app/routes/events.py` | `tools.listEvents` | List calendar events with filters |
| `app/routes/events.py` | `tools.getEvent` | Get event details by ID |
| `app/routes/calendar.py` | `tools.syncCalendar` | Sync Google Calendar events |
| `app/routes/notifications.py` | `tools.planNotifications` | Plan notifications for events using LLM policy |
| `app/routes/notifications.py` | `tools.cancelNotification` | Cancel a scheduled notification |
| `app/llm/policy.py` | `tools.analyzeEvent` | Analyze event and generate notification plan |
| `app/scheduling/planner.py` | `tools.scheduleNotification` | Schedule a notification for delivery |

### Resources (Readable Data Streams)

| Current Module | MCP Resource | Description |
|---------------|--------------|-------------|
| `app/models.py::User` | `resources://users/{user_id}` | User profile data |
| `app/models.py::Event` | `resources://events/{event_id}` | Event details |
| `app/models.py::Notification` | `resources://notifications/{notification_id}` | Notification status and payload |
| `app/models.py::Event` | `resources://users/{user_id}/events` | List of user's events |
| `app/models.py::Notification` | `resources://users/{user_id}/notifications` | List of user's notifications |
| `app/models.py::AuditLog` | `resources://audit/{log_id}` | Audit log entry |
| Database | `resources://events?start={iso}&end={iso}` | Events in time range |

### Prompts (Templated Instructions)

| Current Module | MCP Prompt | Description |
|---------------|------------|-------------|
| `prompts/policy.md` | `prompts/notificationPolicy` | LLM prompt template for notification planning |
| `prompts/email_style.md` | `prompts/emailTemplate` | Email notification template |
| `prompts/tts_style.md` | `prompts/ttsScript` | TTS script template for phone calls |

## Protocol Implementation

### Message Format

MCP uses JSON-RPC 2.0 for message framing:
- **Request**: `{"jsonrpc": "2.0", "id": "...", "method": "...", "params": {...}}`
- **Response**: `{"jsonrpc": "2.0", "id": "...", "result": {...}}`
- **Error**: `{"jsonrpc": "2.0", "id": "...", "error": {"code": ..., "message": "...", "data": {...}}}`

### Transport Layers

1. **Stdio Transport**: Newline-delimited JSON (NDJSON) over stdin/stdout
2. **WebSocket Transport**: JSON-RPC messages over WebSocket frames

### Lifecycle

1. **Initialize**: Client sends `initialize` with capabilities
2. **Capability Negotiation**: Server responds with supported capabilities
3. **Ready**: Client sends `initialized` notification
4. **Operation**: Tools, resources, prompts available
5. **Shutdown**: Graceful cleanup on exit signal

### Concurrency Model

- Async/await for non-blocking I/O
- Bounded queue for request processing (max 32 in-flight)
- Cooperative cancellation via request IDs
- Timeout handling (default 30s per request)

## Security Architecture

### Sandboxing
- No shell execution by default
- Path allowlists for file operations
- Size limits on request payloads (1MB default)

### Authentication
- **Local Dev**: No auth (stdio mode)
- **Production**: File-based token or mTLS (WebSocket mode)
- UNIX domain socket ACLs for local connections

### Rate Limiting
- Token bucket per method (default 100 req/min)
- Global concurrency limit (32 concurrent requests)
- Exponential backoff for retries

## Observability

### Logging
- Structured JSON logs (one per line)
- Request ID correlation
- Log levels: DEBUG, INFO, WARN, ERROR

### Metrics
- Request count per method
- Latency histograms (p50, p95, p99)
- Error rates
- Prometheus-compatible exposition

### Tracing
- Minimal span tree: request → router → handler
- Span IDs for correlation

## Extension Points

1. **Custom Tools**: Register new tools via capability registration
2. **Resource Providers**: Implement resource handlers for new data sources
3. **Prompt Templates**: Add prompt templates via configuration
4. **Middleware**: Add custom middleware (auth, rate-limiting, logging)

## Trade-offs

### Chosen Approaches
- **Pure Python**: No TypeScript to match existing codebase
- **JSON Schema Validation**: Runtime validation over compile-time (flexibility)
- **Async/Await**: Better for I/O-bound operations (DB, HTTP)
- **In-process Metrics**: Simplicity over external metric services

### Alternatives Considered
- **TypeScript**: More type safety but adds language diversity
- **External Metric Service**: Better scalability but adds dependency
- **Binary Protocol**: Better performance but less debuggable

## Performance Targets

- **Trivial Tools**: p95 < 50ms (e.g., `tools.getEvent`)
- **Typical Tools**: p95 < 250ms (e.g., `tools.planNotifications`)
- **Throughput**: ≥ 200 req/s on localhost
- **Concurrency**: Support 32 concurrent requests

## Testing Strategy

1. **Unit Tests**: Message validation, router, transports, error paths
2. **Golden Tests**: Protocol conformance fixtures
3. **E2E Tests**: Full server lifecycle with mock client
4. **Load Tests**: Concurrency 1/8/32, verify throughput/latency
5. **Integration Tests**: Real database operations

## Deployment Modes

1. **Stdio Mode**: Daemon via systemd, pipes stdin/stdout
2. **WebSocket Mode**: HTTP server with WebSocket upgrade, K8s deployment
3. **Embedded Mode**: Library import for programmatic use

