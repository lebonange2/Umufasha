# How to Add a User via MCP Server

## Quick Example

### Basic User Creation (Required Fields Only)

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"John Doe","email":"john@example.com"}}}' | \
python3 -m mcp.server --transport stdio
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\n  \"id\": \"user-12345\",\n  \"name\": \"John Doe\",\n  \"email\": \"john@example.com\",\n  \"message\": \"User created successfully\"\n}"
    }]
  }
}
```

### Complete User Creation (All Fields)

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"Jane Smith","email":"jane@example.com","phone_e164":"+1234567890","timezone":"America/New_York","channel_pref":"both"}}}' | \
python3 -m mcp.server --transport stdio
```

## Required Fields

- **`name`**: User's full name (string)
- **`email`**: User's email address (string)

## Optional Fields

- **`phone_e164`**: Phone number in E.164 format (string)
  - Example: `"+1234567890"`
  - Format: `+[country code][number]`

- **`timezone`**: User's timezone (string)
  - Default: `"UTC"`
  - Examples: `"America/New_York"`, `"Europe/London"`, `"Asia/Tokyo"`

- **`channel_pref`**: Preferred notification channel (string)
  - Options: `"email"`, `"call"`, or `"both"`
  - Default: `"email"`

## Step-by-Step Instructions

### 1. Prepare Your Request

Create a JSON request with:
- JSON-RPC 2.0 format
- Method: `"tools/call"`
- Tool name: `"createUser"`
- Arguments with user data

### 2. Send via Stdio

```bash
# Format the request
REQUEST='{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"Alice Johnson","email":"alice@example.com","phone_e164":"+15551234567","channel_pref":"both"}}}'

# Send it
echo "$REQUEST" | python3 -m mcp.server --transport stdio
```

### 3. Parse the Response

The response will include:
- `id`: The newly created user ID
- `name`: User's name
- `email`: User's email
- `message`: Success message

## Examples

### Example 1: Simple User

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"Bob Wilson","email":"bob@example.com"}}}' | \
python3 -m mcp.server --transport stdio
```

### Example 2: User with Phone Number

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"Carol Brown","email":"carol@example.com","phone_e164":"+15559876543","channel_pref":"call"}}}' | \
python3 -m mcp.server --transport stdio
```

### Example 3: User with All Fields

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"createUser","arguments":{"name":"David Lee","email":"david@example.com","phone_e164":"+15551112222","timezone":"America/Los_Angeles","channel_pref":"both"}}}' | \
python3 -m mcp.server --transport stdio
```

## Using Python Script

### Interactive Script

```python
#!/usr/bin/env python3
"""Add user via MCP."""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.core.protocol.messages import JSONRPCRequest, serialize_message, parse_message

async def add_user(name, email, phone=None, timezone="UTC", channel_pref="email"):
    """Add a user via MCP."""
    request = JSONRPCRequest(
        id=1,
        method="tools/call",
        params={
            "name": "createUser",
            "arguments": {
                "name": name,
                "email": email,
                **({"phone_e164": phone} if phone else {}),
                "timezone": timezone,
                "channel_pref": channel_pref
            }
        }
    )
    
    # Serialize and print (would normally send to MCP server)
    print(serialize_message(request))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 add_user.py <name> <email> [phone] [timezone] [channel_pref]")
        sys.exit(1)
    
    name = sys.argv[1]
    email = sys.argv[2]
    phone = sys.argv[3] if len(sys.argv) > 3 else None
    timezone = sys.argv[4] if len(sys.argv) > 4 else "UTC"
    channel_pref = sys.argv[5] if len(sys.argv) > 5 else "email"
    
    asyncio.run(add_user(name, email, phone, timezone, channel_pref))
```

## Error Handling

### Email Already Exists

If a user with the email already exists:

```json
{
  "error": "User with this email already exists"
}
```

### Missing Required Fields

If required fields are missing:

```json
{
  "error": "Missing required fields: email"
}
```

### Invalid Email Format

The server validates email format. Invalid emails will be rejected.

## Verify User Was Created

After creating a user, verify it exists:

```bash
# Get user by ID (from the creation response)
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"getUser","arguments":{"user_id":"user-12345"}}}' | \
python3 -m mcp.server --transport stdio

# Or check dashboard stats
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"getDashboardStats","arguments":{}}}' | \
python3 -m mcp.server --transport stdio
```

## Using WebSocket Mode

If MCP server is running in WebSocket mode:

```python
import asyncio
import websockets
import json

async def add_user_websocket():
    uri = "ws://localhost:8080/mcp"
    async with websockets.connect(uri) as websocket:
        # Initialize
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "client", "version": "1.0.0"}
            }
        }))
        
        # Create user
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "createUser",
                "arguments": {
                    "name": "Test User",
                    "email": "test@example.com"
                }
            }
        }))
        
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(add_user_websocket())
```

## Quick Reference

**Minimum Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "createUser",
    "arguments": {
      "name": "User Name",
      "email": "user@example.com"
    }
  }
}
```

**Full Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "createUser",
    "arguments": {
      "name": "User Name",
      "email": "user@example.com",
      "phone_e164": "+1234567890",
      "timezone": "America/New_York",
      "channel_pref": "both"
    }
  }
}
```

## Tips

1. **Email must be unique** - Each email can only be registered once
2. **Phone format** - Use E.164 format: `+[country][number]` (e.g., `+15551234567`)
3. **Timezone** - Use IANA timezone names (e.g., `America/New_York`)
4. **Channel preference** - Choose: `"email"`, `"call"`, or `"both"`
5. **Save the user ID** - The response includes the user ID, save it for future operations

