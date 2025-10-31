#!/bin/bash
# Quick script to check if web application is running

echo "=== Web Application Status ==="

# Check if process is running
if pgrep -f "uvicorn app.main" > /dev/null; then
    PID=$(pgrep -f "uvicorn app.main" | head -1)
    echo "✓ Process running (PID: $PID)"
else
    echo "✗ Process not running"
fi

# Check if port 8000 is in use
if lsof -i :8000 > /dev/null 2>&1; then
    PORT_PID=$(lsof -ti :8000 | head -1)
    echo "✓ Port 8000 in use (PID: $PORT_PID)"
else
    echo "✗ Port 8000 not in use"
fi

# Check health endpoint
echo ""
echo "=== Health Check ==="
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Health endpoint responding"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
else
    echo "✗ Health endpoint not responding"
fi

echo ""
echo "=== URLs ==="
echo "  Main: http://localhost:8000"
echo "  Admin: http://localhost:8000/admin"
echo "  API Docs: http://localhost:8000/docs"
echo "  Health: http://localhost:8000/health"

