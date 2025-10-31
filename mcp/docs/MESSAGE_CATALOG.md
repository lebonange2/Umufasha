# MCP Message Catalog

This document describes all MCP protocol methods, their schemas, example requests/responses, and error codes.

## Protocol Version

- **Protocol Version**: `2024-11-05`
- **JSON-RPC Version**: `2.0`

## Initialization

### `initialize`

Initializes the MCP connection and negotiates capabilities.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "client-name",
      "version": "1.0.0"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {"listChanged": false},
      "resources": {"subscribe": false, "listChanged": false},
      "prompts": {"listChanged": false}
    },
    "serverInfo": {
      "name": "assistant-mcp-server",
      "version": "1.0.0"
    }
  }
}
```

**Error Codes:**
- `-32600`: Invalid Request
- `-32602`: Invalid Params

### `initialized`

Notification sent by client after receiving `initialize` response.

**Notification:**
```json
{
  "jsonrpc": "2.0",
  "method": "initialized"
}
```

## Tools

### `tools/list`

Lists all available tools.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "getUser",
        "description": "Get user details by ID",
        "inputSchema": {
          "type": "object",
          "properties": {
            "user_id": {
              "type": "string",
              "description": "User ID"
            }
          },
          "required": ["user_id"]
        }
      }
    ]
  }
}
```

**Error Codes:**
- `-32600`: Invalid Request
- `-32603`: Internal Error

### `tools/call`

Calls a tool with arguments.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "getUser",
    "arguments": {
      "user_id": "user-123"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"id\": \"user-123\",\n  \"name\": \"John Doe\",\n  \"email\": \"john@example.com\"\n}"
      }
    ],
    "isError": false
  }
}
```

**Error Codes:**
- `-32600`: Invalid Request
- `-32601`: Method Not Found (tool doesn't exist)
- `-32602`: Invalid Params (validation error)
- `-32003`: Tool Execution Failed
- `-32004`: Timeout
- `-32005`: Cancelled

**Available Tools:**

1. **getUser**: Get user details by ID
   - Parameters: `user_id` (string, required)
   - Returns: User object with id, name, email, preferences

2. **getEvent**: Get event details by ID
   - Parameters: `event_id` (string, required)
   - Returns: Event object with full details

3. **listEvents**: List calendar events with filters
   - Parameters: `user_id` (string, optional), `days_back` (integer, default: 2), `days_forward` (integer, default: 30)
   - Returns: Array of events with metadata

4. **listNotifications**: List notifications with filters
   - Parameters: `user_id` (string, optional), `status` (string, optional), `days_forward` (integer, default: 7)
   - Returns: Array of notifications

5. **planNotifications**: Plan notifications for user events using LLM policy
   - Parameters: `user_id` (string, required), `event_id` (string, optional), `force_replan` (boolean, default: false)
   - Returns: Planning result with counts and timing

## Resources

### `resources/list`

Lists all available resources.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "resources": [
      {
        "uri": "resources://users/{user_id}",
        "name": "User Profile",
        "description": "User profile data by user ID",
        "mimeType": "application/json"
      }
    ]
  }
}
```

### `resources/read`

Reads a resource by URI.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "resources/read",
  "params": {
    "uri": "resources://users/user-123",
    "offset": 0,
    "limit": 1024
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "contents": [
      {
        "uri": "resources://users/user-123",
        "mimeType": "application/json",
        "text": "{\n  \"id\": \"user-123\",\n  \"name\": \"John Doe\"\n}",
        "hash": "sha256:abc123..."
      }
    ]
  }
}
```

**Error Codes:**
- `-32600`: Invalid Request
- `-32002`: Resource Not Found
- `-32602`: Invalid Params

**Available Resources:**

1. **resources://users/{user_id}**: User profile data
2. **resources://events/{event_id}**: Event details
3. **resources://users/{user_id}/events**: List of user's events

## Prompts

### `prompts/list`

Lists all available prompts.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "prompts/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "prompts": [
      {
        "name": "notificationPolicy",
        "description": "LLM prompt template for notification planning",
        "arguments": [
          {
            "name": "event_data",
            "description": "Event data (JSON string)",
            "required": true
          }
        ]
      }
    ]
  }
}
```

### `prompts/get`

Gets a rendered prompt with arguments.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "prompts/get",
  "params": {
    "name": "notificationPolicy",
    "arguments": {
      "event_data": "{\"title\": \"Meeting\", \"start_ts\": \"2024-01-15T09:00:00Z\"}",
      "user_preferences": "{\"channel_pref\": \"email\"}"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "messages": [
      {
        "role": "system",
        "content": "You are a scheduling policy agent..."
      },
      {
        "role": "user",
        "content": "Event Data:\n{...}\n\nUser Preferences:\n{...}"
      }
    ],
    "description": "LLM prompt template for notification planning"
  }
}
```

**Error Codes:**
- `-32600`: Invalid Request
- `-32601`: Method Not Found (prompt doesn't exist)
- `-32602`: Invalid Params (missing required arguments)

**Available Prompts:**

1. **notificationPolicy**: LLM prompt for notification planning decisions
2. **emailTemplate**: Email notification template generator
3. **ttsScript**: TTS script template for phone calls

## Error Codes

### JSON-RPC 2.0 Standard Errors

- `-32700`: Parse Error
- `-32600`: Invalid Request
- `-32601`: Method Not Found
- `-32602`: Invalid Params
- `-32603`: Internal Error

### MCP-Specific Errors

- `-32001`: Capability Not Supported
- `-32002`: Resource Not Found
- `-32003`: Tool Execution Failed
- `-32004`: Timeout
- `-32005`: Cancelled
- `-32000`: Server Error (generic)

## Error Response Format

```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "path": ["user_id"],
      "validator": "required",
      "validator_value": null
    }
  }
}
```

