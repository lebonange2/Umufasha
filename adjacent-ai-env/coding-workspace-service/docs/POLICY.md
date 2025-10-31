# CWS Policy Configuration

Security policy configuration for Coding Workspace Service.

## Policy File

Create `.cws-policy.json` in your workspace root:

```json
{
  "allowedPaths": ["**/*"],
  "deniedPaths": [".git/**", "node_modules/**"],
  "maxFileSize": 10485760,
  "maxEditSize": 1048576,
  "allowedCommands": ["npm", "python3", "make"],
  "envAllowlist": ["PATH", "HOME"],
  "confirmationRequired": ["delete", "applyPatch", "task.run"]
}
```

## Policy Options

### allowedPaths
Glob patterns for allowed paths. Default: `["**/*"]`

### deniedPaths
Glob patterns for denied paths. Default: `[]`

### maxFileSize
Maximum file size in bytes. Default: `10485760` (10MB)

### maxEditSize
Maximum edit size in bytes. Default: `1048576` (1MB)

### allowedCommands
List of allowed command names. Default: `[]` (no commands allowed)

### envAllowlist
List of allowed environment variables. Default: `[]` (all environment variables allowed)

### confirmationRequired
List of operations requiring confirmation. Default: `["delete", "applyPatch", "task.run"]`

## Security Notes

- All paths are normalized and validated against workspace root
- Path traversal attempts are blocked
- Destructive operations require confirmation by default
- Commands are allowlist-only (deny by default)

