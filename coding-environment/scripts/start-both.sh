#!/bin/bash
# Start both MCP Server and CWS

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting AI Coding Environment Services...${NC}\n"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ASSISTANT_DIR="$(dirname "$SCRIPT_DIR")"
CWS_DIR="$ASSISTANT_DIR/adjacent-ai-env/coding-workspace-service"

# Start MCP Server
echo -e "${GREEN}Starting MCP Server...${NC}"
cd "$ASSISTANT_DIR"
python3 -m mcp.server --transport websocket --host localhost --port 8080 > /tmp/mcp.log 2>&1 &
MCP_PID=$!
echo "  MCP Server started (PID: $MCP_PID)"
echo "  Log: /tmp/mcp.log"

# Wait a moment
sleep 2

# Start CWS
echo -e "${GREEN}Starting CWS...${NC}"
cd "$CWS_DIR"
python3 -m cws.main --transport websocket --host localhost --port 9090 > /tmp/cws.log 2>&1 &
CWS_PID=$!
echo "  CWS started (PID: $CWS_PID)"
echo "  Log: /tmp/cws.log"

# Wait a moment
sleep 2

echo -e "\n${GREEN}Both services running!${NC}\n"
echo "MCP Server: http://localhost:8080/mcp (PID: $MCP_PID)"
echo "CWS: http://localhost:9090 (PID: $CWS_PID)"
echo ""
echo "Logs:"
echo "  MCP: tail -f /tmp/mcp.log"
echo "  CWS: tail -f /tmp/cws.log"
echo ""
echo "To stop:"
echo "  kill $MCP_PID $CWS_PID"
echo ""
echo "Or save PIDs:"
echo "echo $MCP_PID > /tmp/mcp.pid"
echo "echo $CWS_PID > /tmp/cws.pid"

# Save PIDs
echo $MCP_PID > /tmp/mcp.pid
echo $CWS_PID > /tmp/cws.pid

# Wait for interrupt
trap "echo -e '\n${BLUE}Stopping services...${NC}'; kill $MCP_PID $CWS_PID 2>/dev/null; rm -f /tmp/mcp.pid /tmp/cws.pid; exit" INT TERM

echo "Press Ctrl+C to stop both services"
wait

