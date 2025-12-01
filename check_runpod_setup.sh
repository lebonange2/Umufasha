#!/bin/bash
# Diagnostic script for RunPod setup

echo "=== RunPod Diagnostic Script ==="
echo ""

echo "1. Checking if FastAPI app is running..."
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "   ✓ FastAPI app is running"
    PID=$(pgrep -f "uvicorn.*app.main:app" | head -1)
    echo "   PID: $PID"
else
    echo "   ✗ FastAPI app is NOT running"
fi
echo ""

echo "2. Checking port 8000..."
if netstat -tuln 2>/dev/null | grep -q ":8000 "; then
    echo "   ✓ Port 8000 is listening"
    netstat -tuln 2>/dev/null | grep ":8000 "
elif ss -tuln 2>/dev/null | grep -q ":8000 "; then
    echo "   ✓ Port 8000 is listening"
    ss -tuln 2>/dev/null | grep ":8000 "
else
    echo "   ✗ Port 8000 is NOT listening"
fi
echo ""

echo "3. Testing local connection..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✓ App responds to HTTP requests"
    echo "   Response: $(curl -s http://localhost:8000/health)"
else
    echo "   ✗ App does NOT respond to HTTP requests"
fi
echo ""

echo "4. Checking port 8888 (Jupyter)..."
if netstat -tuln 2>/dev/null | grep -q ":8888 "; then
    echo "   ✓ Port 8888 (Jupyter) is listening"
elif ss -tuln 2>/dev/null | grep -q ":8888 "; then
    echo "   ✓ Port 8888 (Jupyter) is listening"
else
    echo "   - Port 8888 is not listening"
fi
echo ""

echo "5. Checking RunPod environment..."
if [ -n "$RUNPOD_POD_ID" ]; then
    echo "   ✓ RunPod environment detected"
    echo "   POD ID: $RUNPOD_POD_ID"
else
    echo "   - No RUNPOD_POD_ID found"
fi
echo ""

echo "6. Checking network interfaces..."
echo "   Hostname: $(hostname)"
echo "   IP addresses:"
ip addr show 2>/dev/null | grep "inet " | awk '{print "     " $2}' || ifconfig 2>/dev/null | grep "inet " | awk '{print "     " $2}'
echo ""

echo "7. Checking for RunPod-specific files..."
if [ -d "/workspace/.runpod" ]; then
    echo "   ✓ Found /workspace/.runpod directory"
    ls -la /workspace/.runpod/ 2>/dev/null | head -5
else
    echo "   - No /workspace/.runpod directory found"
fi
echo ""

echo "=== Recommendations ==="
echo ""
if ! pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "→ Start your app: ./start_server.sh"
    echo ""
fi

if ! netstat -tuln 2>/dev/null | grep -q ":8000 " && ! ss -tuln 2>/dev/null | grep -q ":8000 "; then
    echo "→ Port 8000 is not listening. Make sure the app is running."
    echo ""
fi

echo "→ To access from browser:"
echo "  1. Use SSH tunnel: ssh -L 8000:localhost:8000 root@<runpod-host> -N"
echo "  2. Then open: http://localhost:8000/brainstorm/mindmapper"
echo ""
echo "→ Or configure port 8000 in RunPod UI under Ports/Network settings"

