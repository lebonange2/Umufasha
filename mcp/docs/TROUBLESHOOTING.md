# MCP Server Troubleshooting Guide

## Common Issues

### Server Won't Start

**Problem**: Server fails to start or crashes immediately.

**Possible Causes**:
1. Missing dependencies
2. Database connection error
3. Port already in use (WebSocket mode)
4. Invalid configuration

**Solutions**:
```bash
# Check dependencies
pip install -e .

# Check database connection
python -c "from app.database import engine; print('DB OK')"

# Check port availability
lsof -i :8080

# Run with verbose logging
MCP_LOG_LEVEL=DEBUG python -m mcp.server --transport stdio
```

### ModuleNotFoundError: No module named 'app'

**Problem**: Web application can't find the `app` module when starting.

**Cause**: PYTHONPATH not set correctly.

**Solution**: The `startWebApplication` tool automatically sets PYTHONPATH. Make sure you're running from the ASSISTANT directory:

```bash
# Should be in ASSISTANT directory
cd /home/uwisiyose/ASSISTANT
python3 -m mcp.server --transport stdio
```

### Connection Refused (WebSocket Mode)

**Problem**: Client cannot connect to WebSocket server.

**Possible Causes**:
1. Server not running
2. Firewall blocking port
3. Wrong host/port/path
4. Authentication failure

**Solutions**:
```bash
# Verify server is running
ps aux | grep mcp.server

# Check firewall
sudo iptables -L | grep 8080

# Test connection
curl http://localhost:8080/health

# Check logs
tail -f /var/log/mcp/server.log
```

### Invalid Request Errors

**Problem**: Server returns "Invalid Request" errors.

**Possible Causes**:
1. Malformed JSON
2. Missing required fields
3. Invalid jsonrpc version
4. Wrong message format

**Solutions**:
```bash
# Validate JSON
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m json.tool

# Check message format
# Must be: {"jsonrpc":"2.0","id":...,"method":"...","params":...}

# Enable debug logging
MCP_LOG_LEVEL=DEBUG python -m mcp.server
```

### Tool Execution Errors

**Problem**: Tools return execution errors.

**Possible Causes**:
1. Invalid parameters
2. Database connection error
3. Missing required data
4. Timeout
5. Module import errors

**Solutions**:
```bash
# Validate tool parameters
# Check tool schema: python -m mcp.server --list-tools

# Test database connection
python -c "from app.database import get_db; async def test(): async for db in get_db(): print('OK')"

# Check logs for specific error
grep "TOOL_EXECUTION_FAILED" /var/log/mcp/server.log

# Increase timeout
MCP_DEFAULT_TIMEOUT=60.0 python -m mcp.server
```

### Web Application Start Fails

**Problem**: `startWebApplication` tool fails with "ModuleNotFoundError: No module named 'app'".

**Cause**: PYTHONPATH not correctly set when starting subprocess.

**Solution**: 
- The tool now automatically sets PYTHONPATH to the project root
- Make sure the MCP server is run from the ASSISTANT directory
- Verify the project structure: `/home/uwisiyose/ASSISTANT/app/` should exist

### Stdio Transport Errors

**Problem**: `NotImplementedError` when disconnecting stdio transport.

**Cause**: Some stream implementations don't support `wait_closed()`.

**Solution**: Fixed in code - now gracefully handles missing `wait_closed()`.

### Rate Limiting Issues

**Problem**: Requests are rate limited.

**Possible Causes**:
1. Too many requests
2. Burst limit exceeded
3. Concurrency limit reached

**Solutions**:
```bash
# Check rate limit settings
MCP_RATE_LIMIT_REQUESTS_PER_MINUTE=200 python -m mcp.server

# Increase concurrency
MCP_MAX_CONCURRENT=64 python -m mcp.server

# Review rate limit logs
grep "rate_limit" /var/log/mcp/server.log
```

### Resource Not Found

**Problem**: Resources return "not found" errors.

**Possible Causes**:
1. Invalid resource URI
2. Resource doesn't exist
3. Path pattern mismatch
4. Access denied

**Solutions**:
```bash
# List available resources
curl -X POST http://localhost:8080/mcp -d '{"jsonrpc":"2.0","id":1,"method":"resources/list","params":{}}'

# Verify resource URI format
# Must match pattern: resources://{type}/{id}

# Check resource exists in database
python -c "from app.models import User; from app.database import AsyncSessionLocal; ..."
```

### Authentication Failures

**Problem**: Authentication fails in production mode.

**Possible Causes**:
1. Missing token file
2. Invalid token
3. Token file permissions
4. Token format error

**Solutions**:
```bash
# Check token file exists
ls -la /etc/mcp/tokens.txt

# Verify token format
# Format: client-id:token-secret
cat /etc/mcp/tokens.txt

# Check permissions
chmod 600 /etc/mcp/tokens.txt

# Test authentication
curl -H "Authorization: Bearer client-1:token-secret" http://localhost:8080/mcp
```

## Debugging Tips

### Enable Debug Logging

```bash
export MCP_LOG_LEVEL=DEBUG
python -m mcp.server --transport stdio
```

### Test with Hello Client

```bash
python mcp/examples/hello-client.py | python -m mcp.server --transport stdio
```

### Monitor Requests

```bash
# Log all requests/responses
MCP_LOG_REQUESTS=true python -m mcp.server

# Log to file
python -m mcp.server --transport stdio 2>&1 | tee server.log
```

### Validate Messages

```bash
# Validate JSON-RPC message
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m json.tool

# Test with jq
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | jq '.'
```

## Performance Issues

### Slow Response Times

**Diagnosis**:
```bash
# Enable request timing
MCP_LOG_TIMING=true python -m mcp.server

# Profile with cProfile
python -m cProfile -o profile.stats -m mcp.server
```

**Solutions**:
- Increase timeout
- Optimize database queries
- Add caching
- Scale horizontally

### High Memory Usage

**Diagnosis**:
```bash
# Monitor memory
ps aux | grep mcp.server

# Profile memory
python -m memory_profiler mcp/server.py
```

**Solutions**:
- Reduce max concurrent requests
- Enable request queue limits
- Optimize resource reads
- Add garbage collection tuning

## Getting Help

1. **Check Logs**: Review server logs for errors
2. **Enable Debug Mode**: Set `MCP_LOG_LEVEL=DEBUG`
3. **Test with Examples**: Run hello-client example
4. **Validate Configuration**: Check all environment variables
5. **Review Documentation**: See MESSAGE_CATALOG.md and DESIGN_NOTES.md

## Reporting Issues

When reporting issues, include:
- Server version
- Transport type (stdio/websocket)
- Error messages from logs
- Configuration (sanitized)
- Steps to reproduce
- Expected vs actual behavior
