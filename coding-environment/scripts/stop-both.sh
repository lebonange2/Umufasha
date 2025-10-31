#!/bin/bash
# Stop both MCP Server and CWS

set -e

# Colors
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}Stopping AI Coding Environment Services...${NC}\n"

# Stop MCP Server
if [ -f /tmp/mcp.pid ]; then
    MCP_PID=$(cat /tmp/mcp.pid)
    if ps -p $MCP_PID > /dev/null 2>&1; then
        kill $MCP_PID
        echo "Stopped MCP Server (PID: $MCP_PID)"
    else
        echo "MCP Server not running"
    fi
    rm -f /tmp/mcp.pid
else
    # Try to find and kill by port
    MCP_PID=$(lsof -ti :8080 2>/dev/null || true)
    if [ ! -z "$MCP_PID" ]; then
        kill $MCP_PID
        echo "Stopped MCP Server (found on port 8080)"
    else
        echo "MCP Server not running"
    fi
fi

# Stop CWS
if [ -f /tmp/cws.pid ]; then
    CWS_PID=$(cat /tmp/cws.pid)
    if ps -p $CWS_PID > /dev/null 2>&1; then
        kill $CWS_PID
        echo "Stopped CWS (PID: $CWS_PID)"
    else
        echo "CWS not running"
    fi
    rm -f /tmp/cws.pid
else
    # Try to find and kill by port
    CWS_PID=$(lsof -ti :9090 2>/dev/null || true)
    if [ ! -z "$CWS_PID" ]; then
        kill $CWS_PID
        echo "Stopped CWS (found on port 9090)"
    else
        echo "CWS not running"
    fi
fi

echo ""
echo "Done!"

