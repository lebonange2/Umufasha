# MCP Server Installation

## Basic Installation

```bash
cd /home/uwisiyose/ASSISTANT/mcp
pip install -e .
```

## Optional Dependencies

### Application Management Features

For full application management capabilities (start/stop web application), install optional dependencies:

```bash
pip install -e ".[app-management]"
```

Or install psutil directly:
```bash
pip install psutil
```

**Note**: The server will still work without `psutil`, but some process management features will use fallback methods (lsof/netstat commands).

## Development Installation

For development with testing tools:

```bash
pip install -e ".[dev]"
```

This includes:
- pytest (testing)
- black (code formatting)
- flake8 (linting)
- mypy (type checking)

## Full Installation

For all features:

```bash
pip install -e ".[app-management,dev]"
```

## Verifying Installation

```bash
# Check if MCP server can be imported
python3 -c "from mcp import server; print('✓ MCP server installed')"

# Check if optional features are available
python3 -c "
try:
    import psutil
    print('✓ psutil available (app management features enabled)')
except ImportError:
    print('⚠ psutil not installed (app management uses fallback methods)')
"

# Run the server
python3 -m mcp.server --help
```

## Troubleshooting

### ModuleNotFoundError

If you get `ModuleNotFoundError`, make sure you're in the correct directory:

```bash
# Should be in ASSISTANT directory, not mcp subdirectory
cd /home/uwisiyose/ASSISTANT
pip install -e ./mcp
```

### psutil Installation Issues

If psutil fails to install:

```bash
# On Ubuntu/Debian
sudo apt-get install python3-dev
pip install psutil

# Or use system package
sudo apt-get install python3-psutil
```

### Port Already in Use

If port 8080 is already in use:

```bash
# Check what's using it
lsof -i :8080

# Kill it
lsof -ti:8080 | xargs kill -9
```

## Dependencies

### Required Dependencies
- `jsonschema>=4.0.0` - JSON Schema validation
- `structlog>=24.0.0` - Structured logging
- `websockets>=12.0` - WebSocket support
- `sqlalchemy>=2.0.0` - Database ORM
- `asyncpg>=0.29.0` - PostgreSQL async driver
- `httpx>=0.26.0` - HTTP client

### Optional Dependencies
- `psutil>=5.9.0` - Process management (for app management features)

### Development Dependencies
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `black>=23.12.0` - Code formatter
- `flake8>=7.0.0` - Linter
- `mypy>=1.8.0` - Type checker

## License Compliance

All dependencies are open-source:
- **MIT**: jsonschema, sqlalchemy, websockets
- **Apache-2.0**: structlog, asyncpg
- **BSD**: httpx, psutil

See `SBOM.json` for complete Software Bill of Materials.

