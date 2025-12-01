#!/bin/bash
# Alternative: Start server with ngrok tunnel
# This creates a public URL you can access from anywhere

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "ngrok is not installed."
    echo ""
    echo "To install ngrok:"
    echo "  1. Download from: https://ngrok.com/download"
    echo "  2. Extract and add to PATH"
    echo "  3. Or use: curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc && echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list && sudo apt update && sudo apt install ngrok"
    echo ""
    echo "Alternatively, use SSH tunnel method (see RUNPOD_PORT_SETUP.md)"
    exit 1
fi

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}"

echo "Starting FastAPI server with ngrok tunnel..."
echo ""

# Start server in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &
SERVER_PID=$!

echo "Server started (PID: $SERVER_PID)"
echo "Waiting for server to be ready..."
sleep 3

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "Error: Server failed to start. Check /tmp/fastapi.log"
    exit 1
fi

echo "Starting ngrok tunnel..."
echo ""
echo "Your public URL will be displayed below:"
echo ""

# Start ngrok
ngrok http 8000

# Cleanup on exit
trap "kill $SERVER_PID 2>/dev/null; pkill ngrok 2>/dev/null" EXIT

