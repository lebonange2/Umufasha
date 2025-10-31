# MCP Server Examples

## Command Examples

### Build and Install

```bash
cd /home/uwisiyose/ASSISTANT/mcp
pip install -e .
```

### Run Stdio Mode

```bash
python -m mcp.server --transport stdio
```

### Run WebSocket Mode

```bash
python -m mcp.server --transport websocket --host localhost --port 8080 --path /mcp
```

### Test with Hello Client

```bash
python mcp/examples/hello-client.py | python -m mcp.server --transport stdio
```

## Request/Response Examples

### Initialize

**Request:**
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
```

**Response:**
```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{"listChanged":false},"resources":{"subscribe":false,"listChanged":false},"prompts":{"listChanged":false}},"serverInfo":{"name":"assistant-mcp-server","version":"1.0.0"}}}
```

### List Tools

**Request:**
```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

**Response:**
```json
{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"getUser","description":"Get user details by ID","inputSchema":{"type":"object","properties":{"user_id":{"type":"string","description":"User ID"}},"required":["user_id"]}},{"name":"listEvents","description":"List calendar events with optional filters","inputSchema":{"type":"object","properties":{"user_id":{"type":"string","description":"Optional user ID filter"},"days_back":{"type":"integer","description":"Days to look back (default: 2)","default":2,"minimum":0,"maximum":30},"days_forward":{"type":"integer","description":"Days to look forward (default: 30)","default":30,"minimum":1,"maximum":90}}}]}}
```

### Call Tool

**Request:**
```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"listEvents","arguments":{"days_back":2,"days_forward":30}}}
```

**Response:**
```json
{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"{\n  \"events\": [],\n  \"count\": 0\n}"}],"isError":false}}
```

### List Resources

**Request:**
```json
{"jsonrpc":"2.0","id":4,"method":"resources/list","params":{}}
```

**Response:**
```json
{"jsonrpc":"2.0","id":4,"result":{"resources":[{"uri":"resources://users/{user_id}","name":"User Profile","description":"User profile data by user ID","mimeType":"application/json"},{"uri":"resources://events/{event_id}","name":"Calendar Event","description":"Calendar event data by event ID","mimeType":"application/json"}]}}
```

### Read Resource

**Request:**
```json
{"jsonrpc":"2.0","id":5,"method":"resources/read","params":{"uri":"resources://users/user-123"}}
```

**Response:**
```json
{"jsonrpc":"2.0","id":5,"result":{"contents":[{"uri":"resources://users/user-123","mimeType":"application/json","text":"{\n  \"id\": \"user-123\",\n  \"name\": \"John Doe\",\n  \"email\": \"john@example.com\"\n}","hash":"sha256:abc123..."}]}}
```

## Demo Transcript

```
Client → Server: Initialize
Server → Client: Capabilities + Server Info

Client → Server: Initialized (notification)
Server: Ready to accept requests

Client → Server: tools/list
Server → Client: [5 tools listed]

Client → Server: tools/call {name: "listEvents", arguments: {...}}
Server → Client: {events: [...], count: 5}

Client → Server: resources/list
Server → Client: [3 resources listed]

Client → Server: resources/read {uri: "resources://users/user-123"}
Server → Client: {contents: [{...}]}

Client → Server: prompts/list
Server → Client: [3 prompts listed]

Client → Server: prompts/get {name: "notificationPolicy", arguments: {...}}
Server → Client: {messages: [{role: "system", content: "..."}, ...]}
```

## Performance Examples

### Load Test

```bash
# Run load test
ab -n 1000 -c 32 http://localhost:8080/mcp
```

### Benchmark

```bash
# Run benchmark
python -m mcp.benchmarks.load_test --requests 1000 --concurrency 32
```

## Integration Examples

### Python Client

```python
import asyncio
from mcp.examples.hello_client import SimpleMCPClient

async def main():
    client = SimpleMCPClient()
    await client.initialize()
    tools = await client.list_tools()
    print(f"Available tools: {len(tools['tools'])}")

asyncio.run(main())
```

### HTTP Client (WebSocket mode)

```bash
# Use websocat or similar
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | websocat ws://localhost:8080/mcp
```

