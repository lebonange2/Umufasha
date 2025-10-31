# CWS Troubleshooting Guide

## Common Issues

### CWS Won't Start

**Problem**: CWS fails to start or crashes immediately.

**Solutions**:
```bash
# Check dependencies
pip install -e .

# Check Python version
python3 --version  # Should be 3.10+

# Run with verbose logging
python3 -m cws.main --transport stdio --workspace-root .
```

### Path Traversal Errors

**Problem**: "Path traversal detected" errors.

**Cause**: Attempting to access files outside workspace root.

**Solution**: Ensure all paths are relative to workspace root.

### Policy Violations

**Problem**: "Policy violation" or "Operation denied" errors.

**Solutions**:
1. Check `.cws-policy.json` in workspace root
2. Verify path is in `allowedPaths`
3. Verify command is in `allowedCommands`
4. Add `"confirmed": true` for operations requiring confirmation

### File Too Large

**Problem**: "File too large" errors.

**Solution**: Increase `maxFileSize` or `maxEditSize` in `.cws-policy.json`.

## Debugging

### Enable Debug Logging

```bash
export CWS_LOG_LEVEL=DEBUG
python3 -m cws.main --transport stdio
```

### Test Connection

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"capabilities","params":{}}' | \
python3 -m cws.main --transport stdio
```

## Getting Help

See documentation:
- [QUICKSTART.md](QUICKSTART.md)
- [MESSAGE_CATALOG.md](MESSAGE_CATALOG.md)
- [POLICY.md](POLICY.md)

