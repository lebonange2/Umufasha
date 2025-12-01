#!/bin/bash
# Start server script for RunPod or remote access
# This ensures the server binds to all interfaces (0.0.0.0)

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Add current directory to Python path
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}"

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Starting FastAPI server on 0.0.0.0:8000"
echo "Access the application at:"
echo "  - Local: http://localhost:8000"
echo "  - Network: http://<your-ip>:8000"
echo "  - RunPod: Use RunPod's port forwarding URL"
echo ""
echo "Mindmapper: http://<server-url>/brainstorm/mindmapper"
echo ""

# Start server bound to all interfaces
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info

